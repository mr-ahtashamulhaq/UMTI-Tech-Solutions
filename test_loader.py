from src.ingestion.document_loader import load_all_documents
from src.ingestion.chunker import chunk_documents
from src.ingestion.embedder import store_chunks_in_chroma

documents = load_all_documents("data")
chunks = chunk_documents(documents)

print(f"Total chunks: {len(chunks)}")

store_chunks_in_chroma(chunks)