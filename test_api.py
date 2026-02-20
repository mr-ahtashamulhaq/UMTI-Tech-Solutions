"""
Test script for RAG Voice Assistant API
Tests all three endpoints: /health, /query, and /ingest
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health check endpoint"""
    print("\n" + "="*60)
    print("Testing GET /health")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200


def test_query(question):
    """Test query endpoint"""
    print("\n" + "="*60)
    print("Testing POST /query")
    print("="*60)
    print(f"Question: {question}")
    
    response = requests.post(
        f"{BASE_URL}/query",
        json={"question": question}
    )
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nAnswer:\n{data['answer']}")
        print(f"\nSources:")
        for i, source in enumerate(data['sources'], 1):
            print(f"  {i}. {source}")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200


def test_ingest():
    """Test ingest endpoint"""
    print("\n" + "="*60)
    print("Testing POST /ingest")
    print("="*60)
    print("Note: This will reload all documents from data/ folder")
    
    response = requests.post(f"{BASE_URL}/ingest")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data['status']}")
        print(f"Message: {data['message']}")
        print(f"Total Chunks: {data['total_chunks']}")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200


if __name__ == "__main__":
    print("RAG Voice Assistant API - Test Suite")
    print("Make sure the server is running on http://localhost:8000")
    
    # Test health endpoint
    test_health()
    
    # Test query endpoint
    test_query("How to use Unicorn Studio?")
    
    # Uncomment to test ingest (takes longer)
    # test_ingest()
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)
