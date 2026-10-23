import chromadb

# Cek ke path database lokal
DB_PATH = "./db_loker"
CLIENT = chromadb.PersistentClient(path=DB_PATH)

try:
    collection = CLIENT.get_collection("kumpulan_loker")
    print(f"STATUS: Database ditemukan!")
    print(f"Total data loker di dalam ChromaDB: {collection.count()} baris")
    
    # Ambil sampel 1 data teratas untuk memastikan isinya ada
    sample = collection.peek(limit=1)
    print("\nContoh Metadata Loker Pertama:")
    print(sample['metadatas'][0])
    
except Exception as e:
    print(f"STATUS: Database BERANTAKAN / TIDAK KETEMU!")
    print(f"Error details: {e}")