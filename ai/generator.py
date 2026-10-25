import os
import sqlite3
import mysql.connector
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from retriever import retrieve_relevant_jobs, _get_model, _get_collection

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))



app = FastAPI(title="API AI Konsultan Karir")

    
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Mengizinkan UI dari port berapapun (termasuk 5173) untuk masuk
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def warmup():
    _get_model()
    try:
        _get_collection()
    except Exception:
        from data_ingest import process_and_store_data
        process_and_store_data()
        _get_collection.cache_clear()
        _get_collection()

DB_CONNECTION = os.getenv("DB_CONNECTION", "sqlite").lower()
SQLITE_PATH = os.getenv("SQLITE_PATH", "chat_history.db")
os.makedirs(os.path.dirname(SQLITE_PATH) or ".", exist_ok=True)

def init_db():
    if DB_CONNECTION == "mysql":
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "rag_karir")
        )
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages(
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(255), 
                role VARCHAR(255),
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

def muat_history(session_id: str):
    history = []
    if DB_CONNECTION == "mysql":
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "rag_karir")
        )
        cursor = conn.cursor()
        cursor.execute('SELECT role, content FROM messages WHERE session_id = %s ORDER BY id ASC', (session_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC', (session_id,))
        rows = cursor.fetchall()
        conn.close()

    for role, content in rows:
        history.append({
            "role": role,
            "parts": [content]
        })
    return history

def simpan_pesan(session_id: str, role: str, content: str):
    if DB_CONNECTION == "mysql":
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "rag_karir")
        )
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (session_id, role, content) VALUES (%s, %s, %s)', (session_id, role, content))
        conn.commit()
        cursor.close()
        conn.close()
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)', (session_id, role, content))
        conn.commit()
        conn.close()


init_db()

instruksi_sistem = """Kamu adalah Mentor Karir AI yang suportif, hangat, namun tetap praktis dan to-the-point. 
User yang datang padamu seringkali sedang bingung, jadi gunakan nada bicara yang empatik selayaknya teman diskusi.

ATURAN JAWABAN:
1. FILTER SAPAAN: Jika user HANYA menyapa, abaikan data loker. Cukup sapa balik.
2. INGATAN: Ingat selalu konteks pembicaraan sebelumnya (seperti jurusan, masalah, atau minat user). Jangan menanyakan ulang apa yang sudah diceritakan.
3. REKOMENDASI LOKER: Jika user meminta saran konkrit atau mencari kerja, cek [Data Loker]. Tawarkan dengan antusias. Jika tidak relevan, jujur saja.
4. DILARANG MENGARANG: Rekomendasikan HANYA loker yang ada di [Data Loker].
   Jangan membuat posisi, perusahaan, atau link yang tidak tertulis di sana.
5: GAJI: Soal gaji, hanya sebut angka yang tertulis di baris "Gaji:". Jangan menebak atau menggeneralisasi
6. JANGAN MEMBUAT LINK: Jangan membuat link baru. Hanya gunakan link yang ada di [Data Loker].
[Data Loker] adalah kumpulan lowongan kerja yang relevan dengan pertanyaan user.
7. JUJUR SOAL CAKUPAN: Jika user menyebut bidang (mis. psikologi/HR) yang tidak ada di [Data Loker], katakan terus terang bahwa database belum punya loker bidang itu. Bedakan jelas antara FAKTA dari data dan SARAN UMUM dari kamu.
8. LOKASI & GAJI: Jika loker berada jauh dari lokasi yang user sebut, atau gajinya di bawah target user, sebutkan itu.

"""

model = genai.GenerativeModel("gemini-3.6-flash", system_instruction=instruksi_sistem)
rewriter = genai.GenerativeModel("gemini-3.6-flash")

def tulis_ulang_query(pesan: str) -> str:
    prompt = (
        "Ubah pesan user berikut jadi query pencarian lowongan kerja yang pendek "
        "(maksimal 15 kata): posisi, skill, lokasi, gaji. Buang basa-basi dan candaan. "
        "Tulis nama lokasi dengan ejaan baku (mis. 'Jawa Barat'). "
        "Keluarkan hanya query, tanpa penjelasan.\n\nPesan: " + pesan
    )
    try:
        hasil = rewriter.generate_content(prompt).text.strip()
        return hasil or pesan
    except Exception:
        logger.exception("Rewrite gagal, pakai pesan asli")
        return pesan
    
class ChatRequest(BaseModel):
    user_session_id: str
    message: str

import logging
logger = logging.getLogger(__name__)

MAX_HISTORY = 20

def format_konteks(jobs: list[dict]) -> str:
    if not jobs:
        return "Tidak ada data loker yang relevan."
    return "\n\n".join(
        f"[Loker {i+1}]: {j['posisi']} - {j['perusahaan']} ({j['lokasi']})\n"
        f"Gaji: {j['gaji'] or 'tidak dicantumkan'}\n"
        f"{j['dokumen']}\nLink: {j['url']}"
        for i, j in enumerate(jobs)
    )

def build_prompt(konteks: str, user_message: str) -> str:
    return ( 
        f"[Data Loker dari Database]:\n{konteks}\n\n"
        f"Ucapan/Pertanyaan User: \"{user_message}\"\n"
        "(Berikan balasan natural sesuai ucapan user di atas)"
    )

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    history = muat_history(request.user_session_id) [-MAX_HISTORY:]

    if history and history[0]["role"]== "model":
        history = history[1:]

    query = tulis_ulang_query(request.message)
    logger.info("Query pencarian: %s", query)
    job = retrieve_relevant_jobs(request.message)
    konteks = format_konteks(job)

    try:
        chat = model.start_chat(history=history)
        response = chat.send_message(build_prompt(konteks,request.message))
        bot_reply = response.text
    except Exception:
        logger.exception("LLM Gagal Merespons")
        raise HTTPException(status_code=502, detail="Terjadi kesalahan saat memproses permintaan.")

    simpan_pesan(request.user_session_id, "user", request.message)
    simpan_pesan(request.user_session_id, "model", bot_reply)
    sumber = [j for j in job if j["url"] in bot_reply]
    return {"status": "success", "reply": bot_reply, "sources": [{k: j[k] for k in ("posisi", "perusahaan", "lokasi", "url")} for j in sumber]} 


@app.get("/health")
def health():
    return {"status": "ok"}           