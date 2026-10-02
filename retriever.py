import os
import chromadb
import numpy as np
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

client_hf = InferenceClient(
    api_key=os.getenv("HF_TOKEN"),
)

def retrieve_relevant_jobs(user_query: str, top_k: int = 3):

    # 1. Menghubungkan ke database lokal ChromaDB
    chroma_client = chromadb.PersistentClient(path="./db_loker")
    collection = chroma_client.get_collection(name="kumpulan_loker")
    
    # 2. Mengubah query user menjadi vektor
    hasil_vektor = client_hf.feature_extraction(
        user_query,
        model="sentence-transformers/all-MiniLM-L6-v2",
    )
    vektor_query = np.array(hasil_vektor).flatten().tolist()
    
    # 3. Melakukan pencarian (Similarity Search) di ChromaDB
    results = collection.query(
        query_embeddings=[vektor_query],
        n_results=top_k
    )
    
    # 4. Mengekstrak dan merapikan hasil pencarian (Konteks)
    konteks_loker = ""
    
    # Memeriksa apakah ada hasil yang ditemukan
    if results['documents'] and len(results['documents'][0]) > 0:
        dokumen_ditemukan = results['documents'][0]
        
        for i, doc in enumerate(dokumen_ditemukan):
            konteks_loker += f"[Loker {i+1}]: {doc}\n"
            
        return konteks_loker
    else:
        return "Tidak ada lowongan yang ditemukan."

# --- Blok untuk Testing File Secara Langsung ---
if __name__ == "__main__":
    print("=== Sistem Pencarian Loker (Ketik 'keluar' untuk berhenti) ===")
    
    while True:
        # Meminta input langsung dari ketikan kamu di terminal
        test_query = input("\nMasukkan keluh kesah atau skill kamu: ")
        
        if test_query.lower() == 'keluar':
            print("Sistem dihentikan.")
            break
            
        print(f"\nMencari loker yang cocok untuk: '{test_query}'...\n")
        
        hasil_pencarian = retrieve_relevant_jobs(test_query)
        print("--- Hasil Konteks Loker yang Ditemukan ---")
        print(hasil_pencarian)