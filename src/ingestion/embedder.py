import os
import chromadb
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_embedding(text):
    result = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values

def store_chunks_in_chroma(chunks, collection_name="rag_collection"):
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    try:
        chroma_client.delete_collection(collection_name)
    except:
        pass
    
    collection = chroma_client.create_collection(collection_name)
    
    print("Generating embeddings and storing in Chroma...")
    
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk["text"])
        collection.add(
            ids=[str(i)],
            embeddings=[embedding],
            documents=[chunk["text"]],
            metadatas=[{"filename": chunk["filename"], "chunk_index": chunk["chunk_index"]}]
        )
        print(f"Stored chunk {i+1}/{len(chunks)}")
    
    print("Done. All chunks stored.")
    return collection