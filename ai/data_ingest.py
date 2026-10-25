import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb

from data_cleaning import get_clean_data
from chunker import chunk_job

DB_PATH = os.getenv("CHROMA_PATH", "./db_loker")
COLLECTION_NAME = "kumpulan_loker"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CSV_PATH = "id-jobstreet-com-2026-10-05-2.csv"


def process_and_store_data():
    print("1. Membaca & membersihkan data...")
    df = get_clean_data(CSV_PATH)

    print("2. Menyiapkan chunk & metadata...")
    ids, documents, metadatas = [], [], []
    for _, row in df.iterrows():
        chunks = chunk_job(row["Posisi"], row["Perusahaan"], row["Lokasi"],
                           row["Tipe_Kerja"], row["Deskripsi_lengkap"])
        for n, ch in enumerate(chunks):
            ids.append(f"job_{row['Job_ID']}_{n}")
            documents.append(ch["text"])
            metadatas.append({
                "job_id": str(row["Job_ID"]),
                "bagian": ch["bagian"],
                "posisi": str(row["Posisi"]),
                "perusahaan": str(row["Perusahaan"]),
                "lokasi": str(row["Lokasi"]),
                "tipe_kerja": str(row["Tipe_Kerja"]),
                "industri": str(row["Industri"]),
                "gaji": str(row["Gaji"]) if pd.notna(row["Gaji"]) else "",
                "url": str(row["URL"]),
            })
    print(f"   {len(df)} loker -> {len(ids)} chunk")
    assert len(ids) >= len(df), "Jumlah chunk lebih kecil dari jumlah loker: cek indentasi loop"

    print("3. Embedding (lokal)...")
    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(documents, batch_size=16, show_progress_bar=True).tolist()

    print("4. Menyimpan ke ChromaDB...")
    client = chromadb.PersistentClient(path=DB_PATH)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    collection.upsert(ids=ids, documents=documents,
                      embeddings=embeddings, metadatas=metadatas)

    print(f"Selesai. Total data: {collection.count()}")


if __name__ == "__main__":
    process_and_store_data()