# Cara pakai

1. Buat project:  npx create-next-app@latest temukerja --typescript --tailwind --app --src-dir --import-alias "@/*"
2. Hapus isi folder `src/` bawaan, lalu salin semua isi folder `src/` ini ke dalamnya
   (app/globals.css bawaan dibiarkan, jangan ditimpa).
3. npm run dev  -> buka http://localhost:3000
4. Untuk menyambung ke RAG Python: buat `.env.local` berisi
   RAG_API_URL=http://localhost:8000/chat
