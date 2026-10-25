import re

# Penanda bagian -> label baku. Urutan tidak penting.
SECTION_LABELS = {
    "tanggung jawab": "Tanggung Jawab",
    "tugas": "Tanggung Jawab",
    "deskripsi pekerjaan": "Tanggung Jawab",
    "job description": "Tanggung Jawab",
    "responsibilities": "Tanggung Jawab",
    "kualifikasi": "Kualifikasi",
    "persyaratan": "Kualifikasi",
    "syarat": "Kualifikasi",
    "requirements": "Kualifikasi",
    "qualifications": "Kualifikasi",
    "nilai tambah": "Nilai Tambah",
    "benefit": "Benefit",
    "keuntungan": "Benefit",
}

_MARKER_RE = re.compile(
    r"(?<![A-Za-z])(" + "|".join(sorted(map(re.escape, SECTION_LABELS), key=len, reverse=True)) + r")\s*[:.]\s",
    re.IGNORECASE,
)
_SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(])")

# Batas aman untuk model dengan max_seq_length 128 token (+- 450 karakter Indonesia).
MAX_CHARS = 450


def split_sections(deskripsi: str) -> list[tuple[str, str]]:
    """Pecah deskripsi jadi [(label, isi)] berdasarkan penanda bagian."""
    deskripsi = deskripsi.strip()
    titik = []  # (posisi_mulai, posisi_isi, label)
    for m in _MARKER_RE.finditer(deskripsi):
        sebelum = deskripsi[: m.start()].rstrip()
        # penanda sah hanya jika di awal teks atau di awal kalimat
        if sebelum and sebelum[-1] not in ".!?:)":
            continue
        titik.append((m.start(), m.end(), SECTION_LABELS[m.group(1).lower()]))

    if not titik:
        return [("Deskripsi", deskripsi)] if deskripsi else []

    hasil = []
    if titik[0][0] > 0 and deskripsi[: titik[0][0]].strip():
        hasil.append(("Deskripsi", deskripsi[: titik[0][0]].strip()))
    for i, (_, mulai_isi, label) in enumerate(titik):
        akhir = titik[i + 1][0] if i + 1 < len(titik) else len(deskripsi)
        isi = deskripsi[mulai_isi:akhir].strip()
        if isi:
            hasil.append((label, isi))
    return hasil


def _split_long(isi: str, max_chars: int, overlap: int = 1) -> list[str]:
    """Potong isi panjang di batas kalimat, dengan tumpang tindih `overlap` kalimat."""
    kalimat = [k.strip() for k in _SENT_RE.split(isi) if k.strip()]
    # kalimat tunggal yang kepanjangan dipotong paksa per kata
    pecah = []
    for k in kalimat:
        while len(k) > max_chars:
            potong = k.rfind(" ", 0, max_chars)
            potong = potong if potong > 0 else max_chars
            pecah.append(k[:potong].strip())
            k = k[potong:].strip()
        if k:
            pecah.append(k)

    potongan, saat_ini = [], []
    for k in pecah:
        if saat_ini and len(" ".join(saat_ini + [k])) > max_chars:
            potongan.append(" ".join(saat_ini))
            saat_ini = saat_ini[-overlap:] if overlap else []
            # kalau sisa overlap + kalimat baru masih kepanjangan, buang overlap
            if len(" ".join(saat_ini + [k])) > max_chars:
                saat_ini = []
        saat_ini.append(k)
    if saat_ini:
        potongan.append(" ".join(saat_ini))
    return potongan


def chunk_job(posisi: str, perusahaan: str, lokasi: str, tipe_kerja: str,
              deskripsi: str, max_chars: int = MAX_CHARS) -> list[dict]:
    """
    Kembalikan list chunk: {"text": ..., "bagian": ...}.
    Setiap chunk diawali identitas lowongan supaya tetap bermakna sendirian.
    """
    chunks = []
    for label, isi in split_sections(deskripsi):
        header = f"{posisi}, {perusahaan}, {lokasi}, {tipe_kerja}. {label}: "
        sisa = max(max_chars - len(header), 150)
        for bagian in _split_long(isi, sisa):
            chunks.append({"text": header + bagian, "bagian": label})
    return chunks