"""
RAG Pipeline — Retrieval-Augmented Generation
----------------------------------------------
Flow:
  1. User uploads a file (PDF / DOCX / TXT)
  2. Read the file text
  3. Split into chunks  (RecursiveCharacterTextSplitter)
  4. Create embeddings  (HuggingFace sentence-transformers — free, no API key)
  5. Store in FAISS vector store (in-memory)
  6. User asks a question
  7. Retrieve top-4 similar chunks from FAISS (similarity search)
  8. Build prompt: context chunks + question
  9. Send to Groq LLM (llama-3.3-70b-versatile)
  10. Return the answer
"""

import os
import io

# On Railway/Vercel serverless, set the HuggingFace cache dir to /tmp
# (the model downloads ~90MB on first start — needs a writable directory)
os.environ.setdefault("HF_HOME", "/tmp/huggingface")

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate

from pypdf import PdfReader
from docx import Document
from dotenv import load_dotenv

load_dotenv()


# HuggingFace runs locally — no API key needed.
# Downloads ~90MB model on first run, then cached in /tmp/huggingface.
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")



llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)

# We tell the LLM: answer ONLY from the context, not from your training data.
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


def build_vector_store(filename: str, file_bytes: bytes) -> tuple:
    """
    Takes a file, extracts text, splits into chunks,
    embeds them, and stores in FAISS.
    Returns the FAISS vector_store + stats (chunk count, character count).
    """
    text = read_file_text(filename, file_bytes)

    if not text.strip():
        raise ValueError("Could not extract any text from the file.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    chunks = splitter.create_documents([text])

    vector_store = FAISS.from_documents(chunks, embeddings)

    return vector_store, len(chunks), len(text)

def ask_question(vector_store, question: str) -> tuple:
    """
    Takes the FAISS vector store and a question.
    Retrieves top-4 relevant chunks, builds a prompt, calls Groq LLM.
    Returns the answer and the retrieved source chunks.
    """
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4})

    retrieved_docs = retriever.invoke(question)

    context_text = "\n\n".join(doc.page_content for doc in retrieved_docs)

    final_prompt = prompt.invoke({"context": context_text, "question": question})

    answer = llm.invoke(final_prompt)
    sources = [doc.page_content[:200] + "..." for doc in retrieved_docs]

    return answer.content, sources
