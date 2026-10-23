import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb

from data_cleaning import get_clean_data

DB_PATH = os.getenv("CHROMA_PATH", "./db_loker")
COLLECTION_NAME = "kumpulan_loker"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CSV_PATH = "id-jobstreet-com-2026-10-05-2.csv"

def process_and_store_data():
    print("1. Membaca & membersihkan data...")
    df = get_clean_data(CSV_PATH)

    print("2. Menyiapkan teks & metadata...")
    ids, documents, metadatas = [], [], []
    for _, row in df.iterrows():
        ids.append(f"job_{row['Job_ID']}")
        documents.append(
            f"Posisi: {row['Posisi']}. Perusahaan: {row['Perusahaan']}. "
            f"Industri: {row['Industri']}. Tipe: {row['Tipe_Kerja']}. "
            f"Lokasi: {row['Lokasi']}. Deskripsi: {row['Deskripsi_lengkap']}"
        )
        metadatas.append({
            "posisi": str(row["Posisi"]),
            "perusahaan": str(row["Perusahaan"]),
            "lokasi": str(row["Lokasi"]),
            "tipe_kerja": str(row["Tipe_Kerja"]),
            "industri": str(row["Industri"]),
            "gaji": str(row["Gaji"]) if pd.notna(row["Gaji"]) else "",
            "url": str(row["URL"]),
        })

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