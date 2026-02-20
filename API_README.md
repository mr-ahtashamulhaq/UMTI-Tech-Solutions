# RAG Voice Assistant API

FastAPI backend for the Offline Multimodal RAG Voice Assistant.

## Setup

### Prerequisites
- Python 3.8+
- All dependencies installed: `pip install -r requirements.txt`
- Environment variables configured in `.env`:
  - `GEMINI_API_KEY` - for embeddings
  - `GROQ_API_KEY` - for text generation

### Start the Server

```bash
# Option 1: Using run.py
python run.py

# Option 2: Using uvicorn directly
python -m uvicorn src.api.main:app --port 8000
```

Server will start on: **http://localhost:8000**

## API Endpoints

### 1. Health Check
**GET** `/health`

Check if the API is running.

**Response:**
```json
{
  "status": "ok"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

### 2. Query RAG System
**POST** `/query`

Ask a question and get an AI-generated answer based on your documents.

**Request Body:**
```json
{
  "question": "Your question here"
}
```

**Response:**
```json
{
  "answer": "AI-generated answer based on your documents",
  "sources": [
    {
      "filename": "document.docx",
      "chunk_index": 0
    }
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How to use Unicorn Studio?"}'
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={"question": "How to use Unicorn Studio?"}
)
data = response.json()
print(f"Answer: {data['answer']}")
print(f"Sources: {data['sources']}")
```

---

### 3. Ingest Documents
**POST** `/ingest`

Trigger the full ingestion pipeline to load, chunk, embed, and store documents from the `data/` folder into ChromaDB.

**Response:**
```json
{
  "status": "success",
  "message": "Successfully ingested X documents",
  "total_chunks": 58
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/ingest
```

**Note:** This endpoint:
- Loads all PDF, DOCX, and TXT files from `data/` folder
- Chunks them into smaller pieces
- Generates embeddings using Gemini
- Stores everything in ChromaDB
- **Warning:** This will replace existing data in the database

---

## Interactive API Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- See all endpoints and their schemas
- Test API calls directly from the browser
- View request/response examples

---

## Testing

Run the test suite:
```bash
python test_api.py
```

This will test:
- ✅ Health check endpoint
- ✅ Query endpoint with sample question
- ⚠️ Ingest endpoint (commented out by default - uncomment to test)

---

## Architecture

```
src/
├── api/
│   ├── __init__.py
│   └── main.py          # FastAPI application
├── rag/
│   └── pipeline.py      # RAG query logic
└── ingestion/
    ├── document_loader.py  # Load PDF, DOCX, TXT
    ├── chunker.py         # Split into chunks
    └── embedder.py        # Generate embeddings & store
```

### Technology Stack
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Groq (Llama 3.3 70B)** - Text generation
- **Google Gemini** - Embeddings
- **ChromaDB** - Vector database
- **LangChain** - Text splitting

---

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200` - Success
- `400` - Bad request (e.g., no documents in data folder)
- `404` - Not found (e.g., data folder missing)
- `500` - Internal server error

Error responses include detailed messages:
```json
{
  "detail": "Error message explaining what went wrong"
}
```

---

## Development

### Running with Auto-Reload
For development, use reload mode (watches for file changes):
```bash
python -m uvicorn src.api.main:app --port 8000 --reload
```

### Adding New Endpoints
1. Define Pydantic models for request/response
2. Create endpoint function with `@app.get/post/put/delete`
3. Add proper error handling
4. Update this README

---

## Troubleshooting

### Server won't start
- Check if port 8000 is already in use
- Verify all dependencies are installed
- Check `.env` file has required API keys

### Query returns "I don't have enough information"
- Make sure documents are ingested (call `/ingest` endpoint)
- Verify ChromaDB has data: check `chroma_db/` folder exists
- Try a question related to your document content

### Ingest fails
- Verify `data/` folder exists and contains supported files (.pdf, .docx, .txt)
- Check API keys in `.env` are valid
- Ensure sufficient disk space for ChromaDB

---

## License

[Your License Here]
