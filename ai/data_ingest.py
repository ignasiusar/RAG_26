import os
import pandas as pd
import chromadb
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

client_hf = InferenceClient(
    api_key=os.getenv("HF_TOKEN"),
)

def process_and_store_data(csv_url: str):

    chroma_client = chromadb.PersistentClient(path="./db_loker")
    collection = chroma_client.get_or_create_collection(name="kumpulan_loker")

    print("Mengambil data dari Google Sheets...")
    df = pd.read_csv(csv_url)

    df = df.dropna(subset=['title'])

    print("Daftar kolom yang terbaca oleh sistem:", df.columns.tolist())
    ids, documents, metadatas, embeddings = [], [], [], []

    for index, row in df.iterrows():
        job_id = str(row['job_id'])
        
        # Chunking: Menggabungkan kolom relevan
        teks_loker = f"Posisi: {row['title']}. Perusahaan: {row['company']}. Tipe: {row['job_type']}. Lokasi: {row['location']}. Skill: {row['required_skill']}. Deskripsi: {row['description']}"
        
        print(f"Embedding ID: {job_id} - {row['title']}...")
        
        # Proses vektorisasi
        hasil_vektor = client_hf.feature_extraction(
            teks_loker,
            model="sentence-transformers/all-MiniLM-L6-v2",
        )
        
        vektor_flat = hasil_vektor[0] if isinstance(hasil_vektor[0], list) else hasil_vektor
        
        ids.append(job_id)
        documents.append(teks_loker)
        embeddings.append(vektor_flat)
        metadatas.append({
            "title": str(row['title']),
            "company": str(row['company']),
            "location": str(row['location'])
        })

    print("Melakukan upsert ke ChromaDB...")
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )
    print("Sinkronisasi data selesai dan berhasil!")

if __name__ == "__main__":
    URL_SHEET = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQovj1zaxMh_XQkBarUT549S9__qm83mYFu5whCsqjKFjObhk8e9n4Ywm9T9rYazQsuIm-BPdUlHr49/pub?gid=669667940&single=true&output=csv"
    process_and_store_data(URL_SHEET)