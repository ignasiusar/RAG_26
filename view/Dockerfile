# Menggunakan base image Node.js versi ringan
FROM node:18-alpine

WORKDIR /app

# Menyalin daftar package NPM
COPY package*.json ./

# Menginstal dependency Frontend
RUN npm install

# Menyalin seluruh kode UI React/Vite
COPY . .

# Menjalankan Vite (Wajib pakai flag --host agar bisa diakses dari browser host Fedora)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
