from google import genai
from dotenv import load_dotenv
import chromadb
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_embedding(text):
    result = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values

def retrieve(query, n_results=3):
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_collection("rag_collection")
    
    query_embedding = get_embedding(query)
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    return results

# Test it
query = "What is RAG?"
results = retrieve(query)

print(f"Query: {query}\n")
for i, doc in enumerate(results['documents'][0]):
    print(f"--- Result {i+1} ---")
    print(doc[:300])
    print()