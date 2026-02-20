# How I Built It

## The Problem I Was Solving

Most document Q&A tools are either cloud-locked, expensive at scale, or require you to hand your data to a third party. I wanted to build something that runs locally, answers questions about your own documents accurately, and adds a voice layer on top — so you can speak a question and hear the answer back. No cloud dependency for the data. Fast enough to feel responsive.

---

## Architecture Overview

The system has four components that chain together cleanly.

**Document Ingestion Pipeline**
When you drop a PDF, DOCX, or TXT file into `data/` and hit ingest, the pipeline reads the raw text, splits it into 500-character chunks with 50-character overlap using LangChain's `RecursiveCharacterTextSplitter`, embeds each chunk with the Gemini embedding API, and stores everything in a persistent ChromaDB collection. The overlap prevents context from being lost at chunk boundaries.

**RAG Pipeline**
At query time, the question gets embedded with the same Gemini model, ChromaDB returns the three closest chunks by cosine similarity, and those chunks become the context window passed to Groq's LLaMA 3.3 70B. The prompt explicitly restricts the model to answering from context only — it won't hallucinate beyond the documents. The answer and source metadata come back together.

**Voice Layer**
Voice input goes through Groq's Whisper large-v3 for transcription. The transcribed text feeds directly into the RAG pipeline. The answer text gets converted to an MP3 using gTTS and saved to a temp file. The frontend fetches that file from a dedicated `/voice/audio` endpoint and auto-plays it.

**FastAPI Backend + Frontend**
The backend exposes six endpoints: health check, text query, document ingest, audio transcription, voice query, and audio file serving. CORS is open so the frontend can run as a plain file without a local server. The frontend is a single HTML file — no framework, no build step — with a split-panel layout that switches between text and voice input modes.

---

## Key Technical Decisions

**Groq for the LLM.** Inference is fast — sub-second on most queries. The free tier is generous enough for development and demos. LLaMA 3.3 70B gives strong reasoning without fine-tuning.

**Gemini for embeddings.** `gemini-embedding-001` produces semantically rich vectors. The same model is used at ingest and query time, which matters — embedding asymmetry is a common source of poor retrieval.

**ChromaDB for the vector store.** It runs in-process, persists to disk, and requires zero infrastructure. For a project at this scale there's no reason to spin up a Qdrant or Weaviate instance.

**gTTS for TTS.** No API key, no account, clear audio for response-length text. Adding a paid dependency for a feature that isn't the core of the project would be the wrong trade-off.

**Single-file frontend.** One HTML file means anyone can open it directly in a browser. No Node, no bundler, no `npm install`.

---

## Challenges and How I Solved Them

**Embedding model consistency.** Early on I used different embedding models at ingest and query time by accident. Retrieval was returning irrelevant chunks. The fix was locking both to `gemini-embedding-001` and clearing the Chroma collection on every ingest to prevent stale vectors from polluting results.

**Audio format compatibility with Whisper.** The browser's `MediaRecorder` outputs `audio/webm` by default, but some environments produce `audio/ogg` or `audio/mp4`. Whisper accepts all of them, but the file extension has to match the MIME type or the API rejects it. I solved this by detecting the MIME type and setting the filename extension accordingly before upload.

**CORS blocking the frontend.** Opening `index.html` as a local file means requests come from a `null` origin. Adding `CORSMiddleware` with `allow_origins=["*"]` fixed it without requiring a dev server.

**Port conflicts on restart.** During iterative development, the previous process often held port 8000 for a few seconds after a kill. I built the habit of finding and terminating the owning process by PID before restart.

---

## What I Learned

Retrieval quality is the bottleneck, not generation. A better LLM does not fix bad chunk retrieval. Getting the chunking strategy and embedding model right matters more than which LLM you use downstream.

Latency is dominated by sequential API calls. Embedding the query and then generating the answer are two separate network round-trips. Caching embeddings for repeated queries would cut latency nearly in half for common questions.

Voice UX requires more error handling than text. Microphone permission denial, browser codec differences, and network failures all need separate handling. A single generic error message makes the voice feature feel broken even when the underlying issue is trivial.

Building the evaluation script before finishing the frontend was the right call. Running `evaluate.py` against the live pipeline surfaced retrieval gaps — questions where the answer existed in the document but the wrong chunks were returned — that I could then address by tuning chunk size.
