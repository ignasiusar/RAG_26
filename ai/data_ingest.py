import os
import chromadb
import numpy as np
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

# 1. Panggil fungsi pembersih data dari file sebelah
from data_cleaning import get_clean_data

load_dotenv()
client_hf = InferenceClient(api_key=os.getenv("HF_TOKEN"))

def process_and_store_data():
    print("1. Menarik data bersih dari file data_cleaning.py...")
    # Kita panggil dataframe yang sudah di-cleaning
    df_bersih = get_clean_data('id-jobstreet-com-2026-10-05-2.csv')

    print("2. Menyiapkan database ChromaDB...")
    chroma_client = chromadb.PersistentClient(path="./db_loker")
    
    # Kita RESET database lama agar terganti dengan 100 data scraping terbaru
    try:
        chroma_client.delete_collection(name="kumpulan_loker")
    except ValueError:
        pass
    collection = chroma_client.create_collection(name="kumpulan_loker")

    print("3. Mulai proses vektorisasi (Embedding)...")
    ids, documents, metadatas, embeddings = [], [], [], []

    # Looping menggunakan df_bersih (data dari JobStreet)
    for index, row in df_bersih.iterrows():
        job_id = f"jobstreet_{index}"
        
        # Menggunakan nama kolom yang BARU (sesuai data_cleaning.py)
        teks_loker = f"Posisi: {row['Posisi']}. Perusahaan: {row['Perusahaan']}. Tipe: {row['Tipe_Kerja']}. Lokasi: {row['Lokasi']}. Deskripsi: {row['Deskripsi_lengkap']}"
        
        print(f"Embedding ID: {job_id} - {row['Posisi']}...")
        
        try:
            # PENTING: Pakai model MULTILINGUAL agar paham Bahasa Indonesia!
            hasil_vektor = client_hf.feature_extraction(
                teks_loker,
                model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            )
            
            # Meratakan vektor agar bisa masuk ChromaDB
            vektor_flat = np.array(hasil_vektor).flatten().tolist()
            
            ids.append(job_id)
            documents.append(teks_loker)
            embeddings.append(vektor_flat)
            
            # Simpan metadata untuk balasan bot nanti
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
    # Tinggal panggil fungsi utamanya, tidak butuh URL Google Sheet lagi
    process_and_store_data()