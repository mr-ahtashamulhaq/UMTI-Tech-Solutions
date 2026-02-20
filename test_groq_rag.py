from src.rag.pipeline import rag_query

if __name__ == "__main__":
    query = "What is RAG?"
    print(f"Query: {query}\n")
    
    try:
        answer, sources = rag_query(query)
        print("=" * 50)
        print("ANSWER:")
        print("=" * 50)
        print(answer)
        print("\n" + "=" * 50)
        print("SOURCES:")
        print("=" * 50)
        for i, source in enumerate(sources, 1):
            print(f"\nSource {i}:")
            print(f"  File: {source.get('source', 'N/A')}")
            print(f"  Chunk: {source.get('chunk_id', 'N/A')}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
