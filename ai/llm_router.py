"""
LLM router: coba provider berurutan, pindah otomatis bila kuota habis / error / timeout.

Kenapa ingatan percakapan aman saat pindah provider:
  riwayat chat disimpan di DB kita sendiri (tabel messages) dan dikirim ulang di
  SETIAP request. Provider LLM tidak menyimpan apa pun, jadi provider baru cukup
  menerima riwayat yang sama. Format riwayat di sini netral:
      {"role": "user" | "model", "content": "..."}
  dan diterjemahkan ke format masing-masing provider.

Konfigurasi lewat .env (hanya provider yang punya API key yang dipakai):
  LLM_PROVIDERS=gemini,openrouter,groq        # urutan prioritas
  GEMINI_API_KEY=...   GEMINI_MODEL=gemini-3.6-flash,gemini-3.5-flash   # boleh lebih dari satu
  OPENROUTER_API_KEY=...  OPENROUTER_MODEL=<id model, mis. yang berakhiran :free>
  OPENROUTER_FALLBACK_MODELS=<id1>,<id2>      # opsional, fallback internal OpenRouter
  GROQ_API_KEY=...        GROQ_MODEL=<id model dari console Groq>
  OLLAMA_URL=http://host.docker.internal:11434/v1  OLLAMA_MODEL=<model lokal>   # opsional
"""
import logging
import os
import re
import time

logger = logging.getLogger(__name__)


class AllProvidersFailed(Exception):
    """Semua provider gagal atau sedang cooldown."""


# --------------------------------------------------------------------------- #
# Cooldown: berapa lama sebuah provider diistirahatkan setelah gagal
# --------------------------------------------------------------------------- #
_RE_RETRY = re.compile(r"retry in\s+(?:(\d+)h)?(?:(\d+)m)?(?:([\d.]+)s)?", re.IGNORECASE)


def _status(e: Exception):
    return getattr(e, "status_code", None) or getattr(getattr(e, "response", None), "status_code", None)


def hitung_cooldown(e: Exception) -> int:
    pesan = str(e)
    nama = type(e).__name__
    status = _status(e)

    # Gemini menyebut sendiri kapan boleh coba lagi, mis. "Please retry in 12h20m29.0s"
    m = _RE_RETRY.search(pesan)
    if m and any(m.groups()):
        h, mnt, s = (float(x) if x else 0.0 for x in m.groups())
        return int(min(h * 3600 + mnt * 60 + s, 24 * 3600)) + 5

    if nama == "ResourceExhausted" or status == 429:
        kecil = pesan.lower()
        return 3600 if any(k in kecil for k in ("per day", "daily", "quota")) else 60
    if status in (401, 403, 404) or nama in ("PermissionDenied", "Unauthenticated", "NotFound"):
        return 3600  # kunci/model salah: jangan dicoba terus, tapi catat keras
    return 30        # timeout, 5xx, koneksi putus


# --------------------------------------------------------------------------- #
# Provider
# --------------------------------------------------------------------------- #
class Provider:
    name = "base"

    def generate(self, system: str, history: list[dict], prompt: str, timeout: float) -> str:
        raise NotImplementedError


class GeminiProvider(Provider):
    def __init__(self, model: str, api_key: str):
        self.model = model
        self.name = f"gemini:{model}"
        self.api_key = api_key

    def generate(self, system, history, prompt, timeout):
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        m = genai.GenerativeModel(self.model, system_instruction=system)
        chat = m.start_chat(history=[{"role": h["role"], "parts": [h["content"]]} for h in history])
        return chat.send_message(prompt, request_options={"timeout": timeout}).text


class OpenAICompatProvider(Provider):
    """Untuk semua layanan berformat OpenAI: OpenRouter, Groq, Ollama, dll."""

    def __init__(self, name, base_url, api_key, model, extra_models=None):
        self.name = f"{name}:{model}"
        self.model = model
        self.extra_models = extra_models or []
        self.base_url, self.api_key = base_url, api_key

    def generate(self, system, history, prompt, timeout):
        from openai import OpenAI

        client = OpenAI(base_url=self.base_url, api_key=self.api_key, max_retries=0)  # failover diurus router
        pesan = [{"role": "system", "content": system}]
        for h in history:
            pesan.append({"role": "assistant" if h["role"] in ("model", "assistant") else "user",
                          "content": h["content"]})
        pesan.append({"role": "user", "content": prompt})

        kwargs = {"extra_body": {"models": [self.model] + self.extra_models}} if self.extra_models else {}
        r = client.chat.completions.create(model=self.model, messages=pesan, timeout=timeout, **kwargs)
        return r.choices[0].message.content or ""


# --------------------------------------------------------------------------- #
# Router
# --------------------------------------------------------------------------- #
class LLMRouter:
    def __init__(self, providers: list[Provider], timeout: float = 25.0):
        self.providers = providers
        self.timeout = timeout
        self.cooldown_until: dict[str, float] = {}

    def generate(self, system: str, history: list[dict], prompt: str) -> tuple[str, str]:
        """Return (balasan, nama_provider). Raise AllProvidersFailed bila semua gagal."""
        galat = []
        for p in self.providers:
            sisa = self.cooldown_until.get(p.name, 0) - time.time()
            if sisa > 0:
                galat.append(f"{p.name}: cooldown {int(sisa)}s")
                continue
            try:
                teks = p.generate(system, history, prompt, self.timeout)
                if not (teks or "").strip():
                    raise RuntimeError("balasan kosong")
                if galat:
                    logger.warning("Pindah provider -> %s (sebelumnya: %s)", p.name, "; ".join(galat))
                return teks, p.name
            except Exception as e:
                detik = hitung_cooldown(e)
                self.cooldown_until[p.name] = time.time() + detik
                galat.append(f"{p.name}: {type(e).__name__}")
                logger.warning("Provider %s gagal (%s), cooldown %ss: %.200s", p.name, type(e).__name__, detik, e)
        raise AllProvidersFailed("; ".join(galat) or "tidak ada provider terkonfigurasi")

    def status(self) -> list[dict]:
        sekarang = time.time()
        return [{"provider": p.name,
                 "cooldown_detik": max(0, int(self.cooldown_until.get(p.name, 0) - sekarang))}
                for p in self.providers]


def build_router() -> LLMRouter:
    urutan = [x.strip().lower() for x in os.getenv("LLM_PROVIDERS", "gemini").split(",") if x.strip()]
    providers: list[Provider] = []

    for nama in urutan:
        if nama == "gemini" and os.getenv("GEMINI_API_KEY"):
            for model in os.getenv("GEMINI_MODEL", "gemini-3.6-flash").split(","):
                if model.strip():
                    providers.append(GeminiProvider(model.strip(), os.environ["GEMINI_API_KEY"]))
        elif nama in ("openrouter", "groq", "ollama"):
            cfg = {
                "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", "OPENROUTER_MODEL"),
                "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY", "GROQ_MODEL"),
                "ollama": (os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/v1"), None, "OLLAMA_MODEL"),
            }[nama]
            key = os.getenv(cfg[1], "ollama") if cfg[1] else "ollama"
            model = os.getenv(cfg[2], "").strip()
            if not (key and model):
                logger.warning("Provider %s dilewati: API key atau %s belum diisi", nama, cfg[2])
                continue
            extra = [m.strip() for m in os.getenv("OPENROUTER_FALLBACK_MODELS", "").split(",") if m.strip()] \
                if nama == "openrouter" else []
            providers.append(OpenAICompatProvider(nama, cfg[0], key, model, extra))
        else:
            logger.warning("Provider %r dilewati (tidak dikenal atau API key kosong)", nama)

    if not providers:
        logger.error("Tidak ada provider LLM yang aktif. Periksa LLM_PROVIDERS dan API key di .env")
    logger.info("Urutan provider LLM: %s", [p.name for p in providers])
    return LLMRouter(providers)