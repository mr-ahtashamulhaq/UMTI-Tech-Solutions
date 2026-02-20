FROM python:3.11-slim

# System deps needed by chromadb (sqlite3) and audio libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY src/ ./src/
COPY run.py .
COPY frontend/ ./frontend/

# Create data and chroma_db dirs so mounts are optional
RUN mkdir -p data chroma_db

EXPOSE 8000

CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
