from src.rag.pipeline import rag_query

query = "What is RAG and how does SEEBot use it?"
answer, sources = rag_query(query)

print(f"Question: {query}\n")
print(f"Answer: {answer}\n")
print("Sources:")
for s in sources:
    print(f"  - {s['filename']} (chunk {s['chunk_index']})")