# RAG Loker Assistant 🚀

Sebuah sistem *Retrieval-Augmented Generation* (RAG) berbasis *container* untuk pencarian dan rekomendasi lowongan kerja (Loker). Proyek ini memadukan *backend* FastAPI dengan mesin pencarian vektor ChromaDB dan antarmuka React.

## 🛠️ Tech Stack

*   **Backend:** FastAPI, Python 3.10, Uvicorn
*   **AI & ML:** PyTorch (CPU-only), ChromaDB, Sentence-Transformers (`paraphrase-multilingual-MiniLM-L12-v2`)
*   **Frontend:** React + Vite
*   **Infrastruktur:** Docker & Docker Compose

## ✨ Fitur Utama

*   **Pencarian Semantik:** Menggunakan model *embedding* multibahasa untuk pencarian lowongan kerja yang lebih akurat dan relevan.
*   **Optimasi Docker:** Dibangun menggunakan PyTorch versi CPU untuk menekan ukuran *image* dan mempercepat proses *build*.
*   **Persistensi Data:** Menggunakan *volume mapping* Docker untuk menyimpan riwayat obrolan (SQLite) dan data vektor (ChromaDB) agar tidak hilang saat kontainer di-*restart*.
*   **API Ready:** Dokumentasi API otomatis (Swagger UI) yang langsung siap diakses.

## 🚀 Cara Menjalankan (Local Development)

**Prasyarat:** Pastikan Docker dan Docker Compose sudah terpasang di sistem Anda.

1.  **Clone repositori ini:**
    ```bash
    git clone [https://github.com/username/RAG_26.git](https://github.com/username/RAG_26.git)
    cd RAG_26
    ```

2.  **Jalankan dengan Docker Compose:**
    ```bash
    docker-compose up -d --build
    ```

3.  **Akses Aplikasi:**
    *   **Backend API (Swagger UI):** `http://localhost:8000/docs`
    *   **Frontend Web:** `http://localhost:5173`

## 📂 Struktur Direktori

*   `/ai` - Kode sumber *backend* Python (FastAPI, logika RAG, Dockerfile backend).
*   `/view` - Kode sumber *frontend* React/Vite (Dockerfile frontend).
*   `docker-compose.yml` - Konfigurasi orkestrasi kontainer.

## 💡 Catatan Penting
Pada saat pertama kali dijalankan, sistem akan mengunduh model *embedding* dan inisialisasi koleksi `kumpulan_loker` di dalam ChromaDB secara otomatis.
