# AI Scholar RAG Integration Guide

This guide provides step-by-step instructions for integrating this RAG chatbot with your existing AI_Scholar Python codebase.

## 🔄 Integration Overview

The frontend React application is designed to work seamlessly with your existing Python backend. Here's how to set up the complete integration:

## 1. Backend API Setup

### Required API Endpoints

Create these endpoints in your Python backend (Flask/FastAPI):

```python
# app.py - Main Flask application
from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
from your_existing_modules import DocumentProcessor, RAGSystem

app = Flask(__name__)
CORS(app)

# Initialize your existing systems
doc_processor = DocumentProcessor()
rag_system = RAGSystem(model_name="mistral")

@app.route('/api/documents/upload', methods=['POST'])
def upload_document():
    """Upload and process a document"""
    try:
        file = request.files['file']
        
        # Use your existing document processing logic
        result = doc_processor.process_document(file)
        
        return jsonify({
            "id": result.id,
            "name": file.filename,
            "status": "processed",
            "chunks": result.chunk_count,
            "embeddings": result.embedding_count
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/message', methods=['POST'])
def chat_message():
    """Process chat message with RAG"""
    try:
        data = request.json
        query = data['message']
        conversation_id = data.get('conversation_id')
        
        # Use your existing RAG system
        response = rag_system.generate_response(query)
        
        return jsonify({
            "response": response.text,
            "sources": [
                {
                    "document": source.document_name,
                    "page": source.page_number,
                    "relevance": source.relevance_score
                }
                for source in response.sources
            ],
            "model": "mistral",
            "processing_time": response.processing_time
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Get all processed documents"""
    try:
        documents = doc_processor.get_all_documents()
        return jsonify({
            "documents": [
                {
                    "id": doc.id,
                    "name": doc.name,
                    "size": doc.size,
                    "status": doc.status,
                    "chunks": doc.chunk_count,
                    "uploadedAt": doc.created_at.isoformat()
                }
                for doc in documents
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Delete a document"""
    try:
        doc_processor.delete_document(document_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)
```

## 2. Ollama Integration

### Setup Ollama Service

```python
# ollama_service.py
import requests
import json
from typing import List, Dict

class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "mistral"  # or your preferred model
    
    def generate_response(self, prompt: str, context: str = "") -> Dict:
        """Generate response using Ollama"""
        full_prompt = self._build_rag_prompt(prompt, context)
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": full_prompt,
                "stream": False
            }
        )
        
        return response.json()
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        response = requests.post(
            f"{self.base_url}/api/embeddings",
            json={
                "model": self.model,
                "prompt": text
            }
        )
        
        return response.json()["embedding"]
    
    def _build_rag_prompt(self, query: str, context: str) -> str:
        """Build RAG prompt with context"""
        return f"""
Context: {context}

Question: {query}

Based on the provided context, please answer the question. 
If the context doesn't contain enough information, please say so.

Answer:"""
```

## 3. Vector Store Integration

### Enhanced Vector Store with Chroma

```python
# vector_store.py
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
import uuid

class ChromaVectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        self.collection = self.client.get_or_create_collection("ai_scholar_docs")
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to vector store"""
        ids = [str(uuid.uuid4()) for _ in documents]
        texts = [doc["content"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        embeddings = [doc["embedding"] for doc in documents]
        
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings
        )
    
    def search(self, query_embedding: List[float], n_results: int = 5) -> Dict:
        """Search for similar documents"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results
    
    def delete_documents(self, document_id: str) -> None:
        """Delete documents by document_id"""
        self.collection.delete(
            where={"document_id": document_id}
        )
```

## 4. Complete RAG System

### Integrated RAG Implementation

```python
# rag_system.py
from typing import List, Dict, Any
import time
from dataclasses import dataclass

@dataclass
class RAGResponse:
    text: str
    sources: List[Dict[str, Any]]
    processing_time: float
    model: str

class RAGSystem:
    def __init__(self, model_name: str = "mistral"):
        self.ollama_service = OllamaService()
        self.vector_store = ChromaVectorStore()
        self.model_name = model_name
    
    def generate_response(self, query: str) -> RAGResponse:
        """Generate RAG response"""
        start_time = time.time()
        
        # Generate query embedding
        query_embedding = self.ollama_service.generate_embedding(query)
        
        # Search for relevant documents
        search_results = self.vector_store.search(query_embedding, n_results=5)
        
        # Build context from search results
        context = self._build_context(search_results)
        
        # Generate response using Ollama
        response = self.ollama_service.generate_response(query, context)
        
        # Format sources
        sources = self._format_sources(search_results)
        
        processing_time = time.time() - start_time
        
        return RAGResponse(
            text=response["response"],
            sources=sources,
            processing_time=processing_time,
            model=self.model_name
        )
    
    def _build_context(self, search_results: Dict) -> str:
        """Build context from search results"""
        context_parts = []
        for doc, metadata in zip(search_results["documents"][0], search_results["metadatas"][0]):
            context_parts.append(f"Document: {metadata['document_name']}\nContent: {doc}\n")
        return "\n".join(context_parts)
    
    def _format_sources(self, search_results: Dict) -> List[Dict[str, Any]]:
        """Format sources for response"""
        sources = []
        for metadata, distance in zip(search_results["metadatas"][0], search_results["distances"][0]):
            sources.append({
                "document_name": metadata["document_name"],
                "page_number": metadata.get("page", 1),
                "relevance_score": 1 - distance  # Convert distance to relevance
            })
        return sources
```

## 5. Environment Configuration

### Environment Variables

Create a `.env` file in your backend directory:

```env
# .env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral
CHROMA_PERSIST_DIR=./chroma_db
FLASK_ENV=development
FLASK_DEBUG=1
CORS_ORIGINS=http://localhost:3000
```

### Configuration Class

```python
# config.py
import os
from dataclasses import dataclass

@dataclass
class Config:
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "mistral")
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    
    # Document processing
    MAX_CHUNK_SIZE: int = int(os.getenv("MAX_CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    
    # Vector search
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "5"))

config = Config()
```

## 6. Frontend Configuration

### Update Frontend Environment

Create/update `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
VITE_OLLAMA_URL=http://localhost:11434
VITE_WS_URL=ws://localhost:8000
```

### Update API Service

```typescript
// src/services/apiService.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  async uploadDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Upload failed');
    }

    return response.json();
  }

  async sendMessage(message: string, conversationId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
    });

    if (!response.ok) {
      throw new Error('Message failed');
    }

    return response.json();
  }

  async getDocuments(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/documents`);
    return response.json();
  }

  async deleteDocument(id: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/documents/${id}`, {
      method: 'DELETE',
    });
    return response.json();
  }
}

export const apiService = new ApiService();
```

## 7. Docker Setup

### Complete Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build: 
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - VITE_API_URL=http://backend:8000

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    depends_on:
      - ollama
    environment:
      - OLLAMA_URL=http://ollama:11434
      - OLLAMA_MODEL=mistral
      - CHROMA_PERSIST_DIR=/app/chroma_db
    volumes:
      - ./backend/chroma_db:/app/chroma_db

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ./ollama_data:/root/.ollama
    command: >
      sh -c "ollama serve &
             sleep 5 &&
             ollama pull mistral &&
             wait"

volumes:
  ollama_data:
```

### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
```

## 8. Testing Integration

### Test Script

```python
# test_integration.py
import pytest
import requests
import json

BASE_URL = "http://localhost:8000"

def test_document_upload():
    """Test document upload endpoint"""
    with open("test_document.pdf", "rb") as f:
        files = {"file": f}
        response = requests.post(f"{BASE_URL}/api/documents/upload", files=files)
    
    assert response.status_code == 200
    assert "id" in response.json()

def test_chat_message():
    """Test chat message endpoint"""
    payload = {
        "message": "What is the main topic of the document?",
        "conversation_id": "test_conversation"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/chat/message", 
        json=payload
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "sources" in data

def test_document_list():
    """Test document listing endpoint"""
    response = requests.get(f"{BASE_URL}/api/documents")
    
    assert response.status_code == 200
    assert "documents" in response.json()

if __name__ == "__main__":
    pytest.main([__file__])
```

## 9. Production Deployment

### Production Checklist

- [ ] Environment variables secured
- [ ] SSL certificates configured
- [ ] Database backups automated
- [ ] Monitoring and logging setup
- [ ] Error tracking implemented
- [ ] Performance monitoring active
- [ ] Security headers configured
- [ ] Rate limiting implemented

### Production Environment Variables

```env
# Production .env
FLASK_ENV=production
FLASK_DEBUG=0
OLLAMA_URL=https://your-ollama-service.com
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://your-redis-service.com
SENTRY_DSN=https://your-sentry-dsn
```

## 🚀 Quick Start Commands

```bash
# Start the complete system
docker-compose up -d

# Initialize Ollama models
docker-compose exec ollama ollama pull mistral

# Install Python dependencies
pip install -r requirements.txt

# Start backend development server
python app.py

# Start frontend development server
cd frontend && npm run dev
```

This integration guide provides everything needed to connect your React frontend with your existing Python AI_Scholar backend. The system is designed to be modular and production-ready with proper error handling, logging, and scalability considerations.