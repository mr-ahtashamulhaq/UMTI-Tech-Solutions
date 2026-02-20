import os
import chromadb
from google import genai
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_embedding(text):
    result = gemini_client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values

def retrieve_chunks(query, n_results=3):
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_collection("rag_collection")
    query_embedding = get_embedding(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    return results['documents'][0], results['metadatas'][0]

def generate_answer(query, chunks):
    context = "\n\n".join(chunks)
    prompt = f"""You are a helpful assistant. Answer the question based only on the context provided below.
If the answer is not in the context, say "I don't have enough information to answer that."

Context:
{context}

Question: {query}

Answer:"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

def rag_query(query):
    chunks, metadatas = retrieve_chunks(query)
    answer = generate_answer(query, chunks)
    return answer, metadatas