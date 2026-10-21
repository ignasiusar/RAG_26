FROM python:3.10-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HOME=/app/.hf_cache

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*


RUN pip install torch --index-url https://download.pytorch.org/whl/cpu \
    --extra-index-url https://pypi.org/simple


RUN pip install --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

COPY . .
EXPOSE 8000
CMD ["uvicorn", "generator:app", "--host", "0.0.0.0", "--port", "8000"]
