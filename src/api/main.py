from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import sys
import tempfile

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.rag.pipeline import rag_query
from src.ingestion.document_loader import load_all_documents
from src.ingestion.chunker import chunk_documents
from src.ingestion.embedder import store_chunks_in_chroma
from src.voice.asr import transcribe_audio
from src.voice.tts import text_to_speech

app = FastAPI(title="RAG Voice Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    status: str


class IngestResponse(BaseModel):
    status: str
    message: str
    total_chunks: int


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Query the RAG system with a question"""
    try:
        answer, metadatas = rag_query(request.question)
        return {
            "answer": answer,
            "sources": metadatas
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.post("/ingest", response_model=IngestResponse)
async def ingest_documents():
    """Trigger full ingestion pipeline"""
    try:
        data_folder = "./data"
        
        if not os.path.exists(data_folder):
            raise HTTPException(status_code=404, detail=f"Data folder not found: {data_folder}")
        
        # Load all documents from data folder
        print(f"Loading documents from {data_folder}...")
        documents = load_all_documents(data_folder)
        
        if not documents:
            raise HTTPException(status_code=400, detail="No documents found in data folder")
        
        # Chunk the documents
        print("Chunking documents...")
        chunks = chunk_documents(documents)
        
        # Store in Chroma with embeddings
        print("Storing chunks in Chroma...")
        store_chunks_in_chroma(chunks)
        
        return {
            "status": "success",
            "message": f"Successfully ingested {len(documents)} documents",
            "total_chunks": len(chunks)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during ingestion: {str(e)}")


@app.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Save uploaded documents to the data/ folder."""
    data_folder = "./data"
    os.makedirs(data_folder, exist_ok=True)

    ALLOWED = {".pdf", ".docx", ".txt"}
    uploaded = []
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{ext}' for '{file.filename}'. Allowed: PDF, DOCX, TXT."
            )
        dest = os.path.join(data_folder, file.filename)
        content = await file.read()
        with open(dest, "wb") as f:
            f.write(content)
        uploaded.append(file.filename)

    return {"uploaded": uploaded}


@app.post("/voice/transcribe")
async def voice_transcribe(file: UploadFile = File(...)):
    """Transcribe an uploaded audio file."""
    try:
        suffix = os.path.splitext(file.filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        try:
            text = transcribe_audio(tmp_path)
        finally:
            os.unlink(tmp_path)
        return {"transcription": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")


@app.post("/voice/ask")
async def voice_ask(file: UploadFile = File(...)):
    """Transcribe audio, run RAG query, and return answer with TTS audio."""
    try:
        suffix = os.path.splitext(file.filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        try:
            question = transcribe_audio(tmp_path)
        finally:
            os.unlink(tmp_path)

        answer, metadatas = rag_query(question)

        audio_output = tempfile.mktemp(suffix=".mp3")
        audio_path = text_to_speech(answer, output_path=audio_output)

        return {"answer": answer, "sources": metadatas, "audio_path": audio_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing voice query: {str(e)}")


@app.get("/voice/audio")
async def get_audio(path: str):
    """Serve a generated TTS audio file by its absolute path."""
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(path, media_type="audio/mpeg", filename=os.path.basename(path))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
