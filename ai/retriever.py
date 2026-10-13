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
    konteks_gabungan = ""
    if hasil['documents'] and len(hasil['documents'][0]) > 0:
        for i in range(len(hasil['ids'][0])):
            metadata = hasil['metadatas'][0][i]
            dokumen = hasil['documents'][0][i]
            
            # HAPUS semua print() di sini!
            # print(f"\n{i+1}. Posisi     : {metadata['posisi']}") ... dll
            
            konteks_gabungan += f"[Loker {i+1}]:\n{dokumen}\nLink: {metadata['url']}\n\n"
            
        return konteks_gabungan
    else:
        return "Tidak ada lowongan yang ditemukan."