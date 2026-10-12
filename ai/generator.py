import os
import google.generativeai as genai
from dotenv import load_dotenv
from retriever import retrieve_relevant_jobs

# Memuat variabel lingkungan dari file .env (GEMINI_API_KEY)
load_dotenv()

# Konfigurasi kunci API Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_response(user_query: str):
    # 1. Tarik 3 loker teratas dari ChromaDB
    konteks_loker = retrieve_relevant_jobs(user_query)
    
    # 2. Gunakan model standar yang stabil
    model = genai.GenerativeModel('gemini-3.6-flash')
    
    # 3. Racik Hybrid Prompt yang ringkas dan to the point
    prompt = f"""Kamu adalah Konsultan Karir AI yang sangat ringkas, to the point, dan berbasis data.
    
    ATURAN FORMAT JAWABAN:
    Wajib langsung tampilkan hasil dengan struktur berikut tanpa basa-basi:
    
    🎯 **REKOMENDASI LOKER TERKAIT:**
    (Analisis cepat apakah ada loker di bawah yang cocok dengan skill user. Jika ada, sebutkan nama posisi dan perusahaannya. Jika tidak ada yang cocok secara persis, katakan "Belum ada loker yang sesuai di database").
    
    💡 **SARAN & LANGKAH TAKTIS:**
    (Berikan 2-3 poin solusi singkat terkait keahlian atau keluhan user, tanpa paragraf sambutan yang panjang).
    
    [Data Loker dari Database]:
    {konteks_loker}
    
    Pertanyaan User:
    "{user_query}"
    """
    
    # 4. Kirim prompt dengan stream=True
    response = model.generate_content(prompt, stream=True)
    
    # Cetak langsung kata per kata secara real-time di sini
    for chunk in response:
        print(chunk.text, end="", flush=True)

# --- Blok untuk Testing File Secara Langsung ---
if __name__ == "__main__":
    print("=== Konsultan Karir AI (Ketik 'keluar' untuk berhenti) ===")
    
    while True:
        # Meminta input langsung dari user
        test_query = input("\nKeluhan atau Pertanyaanmu: ")
        
        if test_query.lower() == 'keluar':
            print("Sesi konsultasi dihentikan. Semoga sukses!")
            break
            
        print("\nBot Karir:\n")
        generate_response(test_query)
        print("\n" + "-" * 50)