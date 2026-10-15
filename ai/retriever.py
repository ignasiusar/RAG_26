import os
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

@lru_cache(maxsize=1)
def _get_model():
    return SentenceTransformer(MODEL_NAME)

@lru_cache(maxsize=1)
def _get_collection():
    client = chromadb.PersistentClient(path=DB_PATH)
    return client.get_collection(name=COLLECTION_NAME)

def retrieve_relevant_jobs(pertanyaan_user:str, jumlah_hasil: int = 3)-> list[dict]:
    try:
        vektor = _get_model().encode(pertanyaan_user).tolist()
        hasil = _get_collection().query(
            query_embeddings=[vektor],
            n_results=jumlah_hasil,
        )
    except Exception:
        logger.exception("Retrieve Gagal")
        return[]

    jobs = []
    for meta,doc, dist in zip(
        hasil["metadatas"][0], hasil["documents"][0], hasil["distances"][0]
    ):
        if MAX_DISTANCE is not None and dist > MAX_DISTANCE:
            continue
        jobs.append({
            "posisi":meta["posisi"],
            "perusahaan":meta["perusahaan"],
            "lokasi":meta["lokasi"],
            "url":meta["url"],
            "dokumen":doc[:MAX_DOC_CHARS],
            "distance":round(dist,4),
        })

    return jobs