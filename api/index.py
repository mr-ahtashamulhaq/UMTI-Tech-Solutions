"""
RAG Chatbot API — Complete flow in one file
-------------------------------------------
Flow (exactly like rag_using_langchain.py):
  1. User uploads a file (PDF / DOCX / TXT)
  2. Read the file text
  3. Split into chunks (RecursiveCharacterTextSplitter)
  4. Create embeddings (HuggingFace sentence-transformers — runs free, locally)
  5. Store in FAISS vector store (in-memory, per session)
  6. User asks a question
  7. Retrieve top-4 similar chunks from FAISS  (similarity search)
  8. Build prompt: context + question
  9. Send to Groq LLM (llama-3.3-70b-versatile)
  10. Return the answer
"""

import os
import io
import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Same libraries from rag_using_langchain.py ---
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate

# --- Document reading ---
from pypdf import PdfReader
from docx import Document

from dotenv import load_dotenv

load_dotenv()

# ── FastAPI app ────────────────────────────────────────────────────────────────

app = FastAPI(title="RAG Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory vector store (one per server instance) ──────────────────────────
# On Vercel serverless, each upload creates a fresh vector store.
vector_store = None


# ── Helper: Read text from uploaded file ──────────────────────────────────────

def read_file_text(filename: str, file_bytes: bytes) -> str:
    """Extract plain text from PDF, DOCX, or TXT files."""
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".txt":
        return file_bytes.decode("utf-8", errors="ignore")

    elif ext == ".pdf":
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    elif ext == ".docx":
        doc = Document(io.BytesIO(file_bytes))
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text

    else:
        raise ValueError(f"Unsupported file type: {ext}. Use PDF, DOCX, or TXT.")


# ── Embeddings model (HuggingFace, free, no API key needed) ───────────────────
# Loaded once when the module starts (cached by HuggingFace automatically).
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# ── Groq LLM ──────────────────────────────────────────────────────────────────
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)

# ── Prompt template (exactly from rag_using_langchain.py) ─────────────────────
prompt = PromptTemplate(
    template="""
You are a helpful assistant.
Answer ONLY from the provided document context.
If the context is insufficient, just say you don't know.

{context}

Question: {question}
""",
    input_variables=["context", "question"],
)


# ── API: Request/Response models ───────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]  # list of relevant chunk previews


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a document → build the in-memory vector store.
    Steps: read text → split into chunks → embed → store in FAISS
    """
    global vector_store

    # 1. Read the file bytes
    file_bytes = await file.read()

    # 2. Extract text
    try:
        text = read_file_text(file.filename, file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from the file.")

    print(f"Loaded file: {file.filename} — {len(text)} characters")

    # 3. Split text into chunks (same params as rag_using_langchain.py)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.create_documents([text])

    print(f"Created {len(chunks)} chunks")

    # 4. Create embeddings and store in FAISS (in-memory)
    vector_store = FAISS.from_documents(chunks, embeddings)

    print("Vector store built successfully")

    return {
        "message": f"File '{file.filename}' uploaded and indexed successfully.",
        "chunks": len(chunks),
        "characters": len(text),
    }


@app.post("/api/query", response_model=QueryResponse)
def query_rag(request: QueryRequest):
    """
    Ask a question → retrieve relevant chunks → generate answer with Groq.
    Steps: embed question → similarity search → build prompt → LLM → answer
    """
    global vector_store

    if vector_store is None:
        raise HTTPException(status_code=400, detail="No document uploaded yet. Please upload a file first.")

    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 5. Make retriever (similarity search, top 4 chunks — same as rag_using_langchain.py)
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4})

    # 6. Retrieve the 4 most relevant chunks
    retrieved_docs = retriever.invoke(question)

    # 7. Concatenate chunks into context string (same as rag_using_langchain.py)
    context_text = "\n\n".join(doc.page_content for doc in retrieved_docs)

    # 8. Build the final prompt
    final_prompt = prompt.invoke({"context": context_text, "question": question})

    # 9. Send to Groq LLM and get answer
    answer = llm.invoke(final_prompt)

    # 10. Return answer + source chunk previews
    sources = [doc.page_content[:200] + "..." for doc in retrieved_docs]

    return QueryResponse(answer=answer.content, sources=sources)
