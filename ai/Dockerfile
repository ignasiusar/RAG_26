# Menggunakan base image Python versi ringan
FROM python:3.10-slim

# Menentukan folder kerja di dalam container
WORKDIR /app

# Menyalin file requirements terlebih dahulu untuk efisiensi cache Docker
COPY requirements.txt .

# Menginstal dependency Python tanpa menyimpan cache (agar ringan)
RUN pip install --no-cache-dir -r requirements.txt

# Menyalin seluruh kode AI (termasuk folder db_loker dan .env jika ada)
COPY . .

# Menjalankan server Uvicorn untuk FastAPI
# FORMAT: uvicorn <nama_file_tanpa_py>:<nama_variabel_FastAPI> --host 0.0.0.0 --port 8000
CMD ["uvicorn", "generator:app", "--host", "0.0.0.0", "--port", "8000"]

