# RAG Chatbot

A simple **Retrieval-Augmented Generation (RAG)** chatbot.  
Upload a document → Ask questions → Get answers grounded in your document.

---

## What is RAG?

RAG stands for **Retrieval-Augmented Generation**. It solves the problem of LLMs not knowing about *your* private documents.

Instead of relying on the LLM's training data, RAG:
1. **Splits** your document into small chunks
2. **Embeds** each chunk as a vector (a list of numbers representing meaning)
3. **Stores** all vectors in a vector store (FAISS)
4. When you ask a question, **finds the most similar chunks** using cosine similarity
5. **Sends** those chunks + your question to the LLM as context
6. The LLM **answers based only on the retrieved context** — not from memory

This means the LLM can only answer from your document, not hallucinate from training data.

---

## RAG Flow (step by step)

```
User uploads a file
       │
       ▼
Read text from file (PDF / DOCX / TXT)
       │
       ▼
Split into chunks (RecursiveCharacterTextSplitter)
  chunk_size=1000, chunk_overlap=200
       │
       ▼
Embed each chunk (HuggingFace: sentence-transformers/all-MiniLM-L6-v2)
  → converts text to a 384-dimensional vector
  → free, runs locally, no API key needed
       │
       ▼
Store vectors in FAISS (in-memory vector store)
       │
       ▼
User asks a question
       │
       ▼
Embed the question (same embedding model)
       │
       ▼
Similarity search in FAISS → top 4 most relevant chunks
       │
       ▼
Build prompt: context (4 chunks) + question
       │
       ▼
Send to Groq LLM (llama-3.3-70b-versatile)
       │
       ▼
Return answer to user
```

---

## Tech Stack

| Component | Library | Why |
|---|---|---|
| Text splitting | `langchain-text-splitters` | `RecursiveCharacterTextSplitter` splits smartly by paragraphs/sentences |
| Embeddings | `langchain-huggingface` + `sentence-transformers` | Free, local, no API key needed |
| Vector store | `faiss-cpu` via `langchain-community` | Fast in-memory similarity search |
| LLM | `langchain-groq` (llama-3.3-70b-versatile) | Fast, free tier available |
| API | `FastAPI` | Simple Python REST API |
| Frontend | Vanilla HTML/CSS/JS | No framework needed |
| Deployment | Vercel | Frontend + Python serverless |

---

## Project Structure

```
├── api/
│   └── index.py         ← Entire RAG backend (one flat file)
├── frontend/
│   └── index.html       ← Upload + chat UI
├── requirements.txt     ← Python dependencies
├── vercel.json          ← Vercel routing config
├── .env                 ← API keys (not committed)
└── README.md
```

---

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env

# Start the server
uvicorn api.index:app --reload

# Open the UI
# Go to: http://localhost:8000
# (index.html talks to /api which is localhost:8000/api)
```

---

## Environment Variables

| Variable | Required | Where to get it |
|---|---|---|
| `GROQ_API_KEY` | Yes | [console.groq.com](https://console.groq.com) |

On Vercel, add `GROQ_API_KEY` in **Project Settings → Environment Variables**.

---

## Key Concepts for Interviews

**Why chunking?**  
LLMs have a context window limit. A 100-page PDF won't fit in one prompt. We split it into 1000-character chunks so only the *relevant* pieces are sent.

**Why overlap?**  
`chunk_overlap=200` means adjacent chunks share 200 characters. This prevents important context from being cut off at a chunk boundary.

**What is an embedding?**  
A vector (array of numbers) that represents the *meaning* of text. Similar meanings → similar vectors. `all-MiniLM-L6-v2` produces 384-dimensional vectors.

**What is FAISS?**  
Facebook AI Similarity Search — an in-memory database optimized for finding nearest vectors. When you ask a question, it finds the 4 chunks whose vectors are closest to the question's vector.

**Why only answer from context?**  
The prompt explicitly says: *"Answer ONLY from the provided document context. If the context is insufficient, just say you don't know."* This prevents hallucination.
