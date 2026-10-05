import os
import google.generativeai as genai
from dotenv import load_dotenv
from retriever import retrieve_relevant_jobs

# Memuat variabel lingkungan dari file .env
load_dotenv()

# Konfigurasi kunci API Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_response(user_query: str):
    # 1. Tarik 3 loker teratas dari ChromaDB lewat retriever.py
    konteks_loker = retrieve_relevant_jobs(user_query)
    
    # 2. Gunakan model standar yang stabil
    model = genai.GenerativeModel('gemini-3.6-flash')
    
    # 3. Racik Hybrid Prompt yang ringkas dan to the point
    prompt = f"""Kamu adalah Mentor Karir AI yang suportif, hangat, namun tetap praktis dan to-the-point. 
    User yang datang padamu seringkali sedang bingung atau lelah, jadi gunakan nada bicara yang empatik selayaknya teman diskusi atau senior yang membantu adik tingkatnya.
    
    ATURAN JAWABAN:
    1. Buka dengan 1-2 kalimat empati atau validasi perasaan user (jangan terlalu panjang).
    2. Berikan saran karir yang realistis dan bisa langsung dieksekusi (Gunakan format poin jika perlu).
    3. Cek [Data Loker dari Database] di bawah. Jika ada yang relevan dengan keahlian user, tawarkan dengan antusias beserta link pendaftarannya. Jika tidak ada, sampaikan dengan halus bahwa saat ini belum ada posisi yang pas, tapi berikan alternatif lain.
    
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