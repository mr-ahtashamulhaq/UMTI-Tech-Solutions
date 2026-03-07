---
title: RAG Voice Assistant
emoji: 🎙️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# RAG Voice Assistant

A production-ready **Retrieval-Augmented Generation (RAG)** assistant that answers questions about your documents by text **or** voice  with spoken audio responses.<br>

<a href="https://rag-voice-assistant-three.vercel.app" target="_blank">
  <img src="https://img.shields.io/badge/Live-Demo-000000?style=for-the-badge&logo=vercel&logoColor=3B82F6" alt="Live Demo">
</a>

---

## Architecture Overview

```
User (browser)
   │  text question     ──▶  POST /query
   │  voice recording   ──▶  POST /voice/ask
   │  document ingest   ──▶  POST /ingest
   ▼
FastAPI backend  (src/api/main.py)
   ├── Ingestion pipeline
   │     ├── Document Loader   – reads PDF / DOCX / TXT   (src/ingestion/document_loader.py)
   │     ├── Chunker           – splits text into chunks   (src/ingestion/chunker.py)
   │     └── Embedder          – Gemini embeddings → ChromaDB  (src/ingestion/embedder.py)
   │
   ├── RAG pipeline  (src/rag/pipeline.py)
   │     ├── Retriever  – embeds query, queries ChromaDB
   │     └── Generator  – Groq LLaMA builds grounded answer
   │
   └── Voice pipeline
         ├── ASR  – Groq Whisper transcribes audio  (src/voice/asr.py)
         └── TTS  – gTTS converts answer to mp3     (src/voice/tts.py)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI + Uvicorn |
| LLM | Groq — `llama-3.3-70b-versatile` |
| Embeddings | Google Gemini — `gemini-embedding-001` |
| Vector store | ChromaDB (persistent) |
| ASR | Groq — `whisper-large-v3` |
| TTS | gTTS (Google Text-to-Speech) |
| Text splitting | LangChain `RecursiveCharacterTextSplitter` |
| Document parsing | pypdf, python-docx |
| Frontend | Plain HTML + CSS + JavaScript (single file) |

---

## Setup

### Prerequisites
- Python 3.11+
- A [Groq API key](https://console.groq.com/)
- A [Google AI / Gemini API key](https://aistudio.google.com/app/apikey)

### 1 — Clone
```bash
git clone https://github.com/your-username/rag-voice-assistant.git
cd rag-voice-assistant
```

### 2 — Create virtual environment & install dependencies
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3 — Add API keys
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4 — Add your documents
Drop PDF, DOCX, or TXT files into the `data/` folder.

### 5 — Run the server
```bash
python run.py
```

The API will be available at **http://localhost:8000**  
Interactive docs at **http://localhost:8000/docs**

---

## Running with Docker

```bash
# Build
docker build -t rag-voice-assistant .

# Run (mount data folder and pass API keys)
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your_groq_key \
  -e GEMINI_API_KEY=your_gemini_key \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/chroma_db:/app/chroma_db \
  rag-voice-assistant
```

---

## How to Use

### Ingest documents
1. Place files in `data/`
2. Open the frontend at `frontend/index.html` and click **Reload Documents**, or call:
```bash
curl -X POST http://localhost:8000/ingest
```

### Ask by text
Type a question in the **Ask by Text** box and press Enter or click **Ask**.

Or via API:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic of the documents?"}'
```

### Ask by voice
1. Click **Record** and speak your question
2. Click **Stop** — the audio is transcribed and sent to the RAG pipeline
3. The answer is displayed as text and played back as audio

Or via API:
```bash
curl -X POST http://localhost:8000/voice/ask \
  -F "file=@question.wav"
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Server health check |
| POST | `/query` | Text question → RAG answer |
| POST | `/ingest` | Ingest all files in `data/` |
| POST | `/voice/transcribe` | Audio file → transcribed text |
| POST | `/voice/ask` | Audio file → RAG answer + TTS mp3 |
| GET | `/voice/audio` | Serve generated TTS audio file |

---

## Folder Structure

```
rag-voice-assistant/
├── data/                        # Drop your documents here
├── chroma_db/                   # Persistent vector store (auto-created)
├── frontend/
│   └── index.html               # Single-file dark-themed UI
├── src/
│   ├── api/
│   │   └── main.py              # FastAPI app + all endpoints
│   ├── ingestion/
│   │   ├── document_loader.py   # PDF / DOCX / TXT reader
│   │   ├── chunker.py           # Text splitter
│   │   └── embedder.py          # Gemini embeddings → ChromaDB
│   ├── rag/
│   │   └── pipeline.py          # Retrieve + generate answer
│   └── voice/
│       ├── asr.py               # Groq Whisper transcription
│       └── tts.py               # gTTS text-to-speech
├── run.py                       # Server entry point
├── requirements.txt
├── Dockerfile
└── .env                         # API keys (never commit this)
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.
