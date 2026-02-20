"""
FastAPI Server Starter for RAG Voice Assistant
Usage: python run.py
Access API at: http://localhost:7860
Interactive docs: http://localhost:7860/docs
"""
import uvicorn

if __name__ == "__main__":
    print("Starting RAG Voice Assistant API Server...")
    print("API will be available at: http://localhost:7860")
    print("Interactive API docs: http://localhost:7860/docs")
    print("\nEndpoints:")
    print("  GET  /health - Health check")
    print("  POST /query  - Query the RAG system")
    print("  POST /ingest - Ingest documents from data/ folder")
    print("\nPress CTRL+C to stop the server\n")
    
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=7860, reload=False)
