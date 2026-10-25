import os
import re
import logging
from functools import lru_cache

import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("CHROMA_PATH", os.path.join(os.path.dirname(__file__), "db_loker"))
COLLECTION_NAME = "kumpulan_loker"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

MAX_DOC_CHARS = 1500
MAX_DISTANCE = float(os.getenv("MAX_DISTANCE", 0)) or None


GENERIC_WORDS = {"jawa", "kalimantan", "sulawesi", "nusa", "sumatera", "kepulauan", "daerah"}


@lru_cache(maxsize=1)
def _get_model():
    return SentenceTransformer(MODEL_NAME)


@lru_cache(maxsize=1)
def _get_collection():
    client = chromadb.PersistentClient(path=DB_PATH)
    col = client.get_collection(name=COLLECTION_NAME)
    if col.count() == 0:
        raise RuntimeError("Collection kosong")
    return col


def _norm(teks: str) -> str:
    """lowercase, buang teks dalam kurung seperti '(Hibrid)', rapikan spasi."""
    teks = re.sub(r"\(.*?\)", "", teks.lower())
    return re.sub(r"\s+", " ", teks).strip()


def build_location_index(lokasi_list: list[str]) -> dict[str, set[str]]:
    """
    Peta: kata kunci lokasi -> set nilai 'lokasi' persis seperti di metadata.
    'Bekasi, Jawa Barat' menghasilkan kunci 'bekasi', 'jawa barat', 'bekasi, jawa barat'.
    'Jakarta Barat, Jakarta Raya' juga menghasilkan alias 'jakarta'.
    """
    index: dict[str, set[str]] = {}

    def add(key: str, asli: str):
        key = key.strip()
        if len(key) >= 3:
            index.setdefault(key, set()).add(asli)

    for asli in set(lokasi_list):
        norm = _norm(asli)
        add(norm, asli)
        for bagian in norm.split(","):
            bagian = bagian.strip()
            add(bagian, asli)
            kata_pertama = bagian.split(" ")[0]
            if " " in bagian and kata_pertama not in GENERIC_WORDS:
                add(kata_pertama, asli)
    return index


@lru_cache(maxsize=1)
def _get_location_index() -> dict[str, set[str]]:
    data = _get_collection().get(include=["metadatas"])
    return build_location_index([m["lokasi"] for m in data["metadatas"]])


def detect_locations(pertanyaan: str, index: dict[str, set[str]]) -> list[str]:
    """Kembalikan nilai 'lokasi' (persis metadata) yang disebut di pertanyaan."""
    q = " " + re.sub(r"[^\w\s]", " ", pertanyaan.lower()) + " "
    q = re.sub(r"\s+", " ", q)
    hasil: set[str] = set()
    # kunci terpanjang dulu, supaya 'jakarta barat' menang atas 'jakarta'
    for key in sorted(index, key=len, reverse=True):
        key_bersih = re.sub(r"[^\w\s]", " ", key)
        key_bersih = re.sub(r"\s+", " ", key_bersih).strip()
        if f" {key_bersih} " in q:
            hasil |= index[key]
            q = q.replace(f" {key_bersih} ", " ")  # cegah match ganda oleh kunci yang lebih pendek
    return sorted(hasil)


def retrieve_relevant_jobs(pertanyaan_user: str, jumlah_hasil: int = 5) -> list[dict]:
    try:
        vektor = _get_model().encode(pertanyaan_user).tolist()
        col = _get_collection()

        lokasi_cocok = detect_locations(pertanyaan_user, _get_location_index())
        hasil = None
        if lokasi_cocok:
            logger.info("Filter lokasi: %s", lokasi_cocok)
            hasil = col.query(
                query_embeddings=[vektor],
                n_results=jumlah_hasil,
                where={"lokasi": {"$in": lokasi_cocok}},
            )
            if not hasil["ids"][0]:
                hasil = None  

        if hasil is None:
            hasil = col.query(query_embeddings=[vektor], n_results=jumlah_hasil)
    except Exception:
        logger.exception("Retrieve Gagal")
        return []

    jobs = []
    for meta, doc, dist in zip(
        hasil["metadatas"][0], hasil["documents"][0], hasil["distances"][0]
    ):
        if MAX_DISTANCE is not None and dist > MAX_DISTANCE:
            continue
        jobs.append({
            "posisi": meta["posisi"],
            "perusahaan": meta["perusahaan"],
            "lokasi": meta["lokasi"],
            "url": meta["url"],
            "dokumen": doc[:MAX_DOC_CHARS],
            "distance": round(dist, 4),
        })
    return jobs