import chromadb
from sentence_transformers import SentenceTransformer

def retrieve_relevant_jobs(pertanyaan_user, jumlah_hasil=3):
    print(f"\nMencari loker untuk curhatan: '{pertanyaan_user}'...")
    
    # 1. Hubungkan ke ChromaDB lokal
    chroma_client = chromadb.PersistentClient(path="./db_loker")
    collection = chroma_client.get_collection(name="kumpulan_loker")
    
    # 2. Muat model embedding lokal yang sama
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    
    # 3. Ubah curhatan user menjadi vektor
    vektor_query = model.encode(pertanyaan_user).tolist()
    
    # 4. Cari kemiripan di ChromaDB
    hasil = collection.query(
        query_embeddings=[vektor_query],
        n_results=jumlah_hasil
    )
    
    # 5. Tampilkan hasilnya
    print("\n" + "="*40)
    print("HASIL REKOMENDASI LOKER TERBAIK:")
    print("="*40)
    
    for i in range(len(hasil['ids'][0])):
        metadata = hasil['metadatas'][0][i]
        jarak = hasil['distances'][0][i] if 'distances' in hasil else "N/A"
        
        print(f"\n{i+1}. Posisi     : {metadata['posisi']}")
        print(   f"   Perusahaan : {metadata['perusahaan']}")
        print(   f"   Lokasi     : {metadata['lokasi']}")
        print(   f"   Link       : {metadata['url']}")
        print(   f"   Skor Jarak : {jarak:.4f} (Semakin kecil semakin mirip)")

if __name__ == "__main__":
    # Contoh curhatan user untuk dites
    curhatan = "Aku punya pengalaman di bidang perbaikan elektronik dan mesin, pengen kerja teknisi di sekitar Bekasi"
    
    cari_loker_cocok(curhatan)