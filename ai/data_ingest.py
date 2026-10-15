import os
import chromadb
import numpy as np
from huggingface_hub import InferenceClient
from dotenv import load_dotenv


from data_cleaning import get_clean_data

load_dotenv()
client_hf = InferenceClient(api_key=os.getenv("HF_TOKEN"))

def process_and_store_data():
    print("1. Menarik data bersih dari file data_cleaning.py...")

    df_bersih = get_clean_data('id-jobstreet-com-2026-10-05-2.csv')

    print("2. Menyiapkan database ChromaDB...")
    chroma_client = chromadb.PersistentClient(path="./db_loker")

    try:
        chroma_client.delete_collection(name="kumpulan_loker")
    except ValueError:
        pass
    collection = chroma_client.create_collection(name="kumpulan_loker")

    print("3. Mulai proses vektorisasi (Embedding)...")
    ids, documents, metadatas, embeddings = [], [], [], []


    for index, row in df_bersih.iterrows():
        job_id = f"jobstreet_{index}"
        
        teks_loker = f"Posisi: {row['Posisi']}. Perusahaan: {row['Perusahaan']}. Tipe: {row['Tipe_Kerja']}. Lokasi: {row['Lokasi']}. Deskripsi: {row['Deskripsi_lengkap']}"
        
        print(f"Embedding ID: {job_id} - {row['Posisi']}...")
        
        try:
            
            hasil_vektor = client_hf.feature_extraction(
                teks_loker,
                model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            )
            
            
            vektor_flat = np.array(hasil_vektor).flatten().tolist()
            
            ids.append(job_id)
            documents.append(teks_loker)
            embeddings.append(vektor_flat)
            
        
            metadatas.append({
                "posisi": str(row['Posisi']),
                "perusahaan": str(row['Perusahaan']),
                "lokasi": str(row['Lokasi']),
                "url": str(row['URL'])
            })
        except Exception as e:
            print(f"Gagal embedding baris {index}: {e}")

    print("4. Melakukan upsert ke ChromaDB...")
    if ids:
        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        print("Sinkronisasi data selesai dan berhasil! 🚀")
        print(f"Total data di database saat ini: {collection.count()}")
    else:
        print("Gagal: Tidak ada data yang berhasil diproses.")

if __name__ == "__main__":
    process_and_store_data()