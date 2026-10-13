import os
import sqlite3
import mysql.connector
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from retriever import retrieve_relevant_jobs

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


app = FastAPI(title="API AI Konsultan Karir")

DB_CONNECTION = os.getenv("DB_CONNECTION", "sqlite").lower()

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
        conn = sqlite3.connect("chat_history.db")
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
        conn = sqlite3.connect("chat_history.db")
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
        conn = sqlite3.connect("chat_history.db")
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)', (session_id, role, content))
        conn.commit()
        conn.close()

# Jalankan pembuatan tabel
init_db()

instruksi_sistem = """Kamu adalah Mentor Karir AI yang suportif, hangat, namun tetap praktis dan to-the-point. 
User yang datang padamu seringkali sedang bingung, jadi gunakan nada bicara yang empatik selayaknya teman diskusi.

ATURAN JAWABAN:
1. FILTER SAPAAN: Jika user HANYA menyapa, abaikan data loker. Cukup sapa balik.
2. INGATAN: Ingat selalu konteks pembicaraan sebelumnya (seperti jurusan, masalah, atau minat user). Jangan menanyakan ulang apa yang sudah diceritakan.
3. REKOMENDASI LOKER: Jika user meminta saran konkrit atau mencari kerja, cek [Data Loker]. Tawarkan dengan antusias. Jika tidak relevan, jujur saja.
"""

model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=instruksi_sistem)


class ChatRequest(BaseModel):
    user_session_id: str
    message: str


@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    user_id = request.user_session_id
    user_message = request.message
    
    
    simpan_pesan(user_id, "user", user_message)
    
    
    history = muat_history(user_id)
    chat_session = model.start_chat(history=history)
    
    
    konteks_loker = retrieve_relevant_jobs(user_message)
    
    
    prompt_harian = f"[Data Loker dari Database]:\n{konteks_loker}\n\nUcapan/Pertanyaan User: \"{user_message}\"\n(Berikan balasan natural sesuai ucapan user di atas)"
    
    
    response = chat_session.send_message(prompt_harian)
    bot_reply = response.text
    
    
    simpan_pesan(user_id, "model", bot_reply)
    
    return {
        "status": "success",
        "user_session_id": user_id,
        "reply": bot_reply
    }