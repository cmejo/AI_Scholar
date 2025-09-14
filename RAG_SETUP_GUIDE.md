# AI Scholar RAG System Setup Guide

This guide will help you set up and run the complete RAG (Retrieval-Augmented Generation) system for querying your scientific literature using Ollama and open-source LLMs.

## 🚀 Quick Start

### 1. Prerequisites

Make sure you have the following installed:
- Docker and Docker Compose
- Python 3.8+
- Node.js 16+
- Your arXiv dataset at `/home/cmejo/arxiv-dataset/pdf`

### 2. Start the Services

```bash
# Start all services (ChromaDB, Ollama, etc.)
docker-compose up -d

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../
npm install
```

### 3. Initialize the RAG System

```bash
# Test the system components
cd backend
python test_rag_system.py

# Process your arXiv dataset (start with a small batch)
python process_arxiv_dataset.py
```

### 4. Start the Application

```bash
# Start the backend
cd backend
python app.py

# In another terminal, start the frontend
npm run dev
```

## 📋 Detailed Setup

### Backend Services

#### 1. ChromaDB (Vector Database)
- **Purpose**: Stores document embeddings for semantic search
- **Port**: 8000
- **Status**: Check at `http://localhost:8000/api/v1/heartbeat`

#### 2. Ollama (LLM Service)
- **Purpose**: Provides open-source LLMs for text generation
- **Port**: 11434
- **Models**: llama2, mistral, codellama, etc.

#### 3. FastAPI Backend
- **Purpose**: Main API server with RAG endpoints
- **Port**: 8000 (backend)
- **Key endpoints**:
  - `POST /api/rag/query` - Scientific queries
  - `POST /api/rag/process-arxiv-dataset` - Process your dataset
  - `GET /api/rag/corpus/stats` - Collection statistics

### Frontend Interface

#### 1. Scientific RAG Component
- **Location**: Available in the sidebar as "Scientific RAG"
- **Features**:
  - Query your scientific literature
  - View corpus statistics
  - Process new documents
  - Browse sources and citations

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# ChromaDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Ollama Configuration
OLLAMA_HOST=localhost
OLLAMA_PORT=11434

# Dataset Configuration
ARXIV_DATASET_PATH=/home/cmejo/arxiv-dataset/pdf

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Ollama Models

Install recommended models:

```bash
# Pull models (run after Ollama is started)
docker exec ollama ollama pull llama2
docker exec ollama ollama pull mistral
docker exec ollama ollama pull codellama
```

## 📊 Usage Examples

### 1. Query Your Literature

```bash
# Example API call
curl -X POST "http://localhost:8000/api/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest developments in transformer architectures?",
    "model": "llama2",
    "max_sources": 10
  }'
```

### 2. Process Documents

```bash
# Process your entire arXiv dataset
curl -X POST "http://localhost:8000/api/rag/process-arxiv-dataset" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Get Corpus Statistics

```bash
# Check your document collection
curl "http://localhost:8000/api/rag/corpus/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🧪 Testing

### 1. Component Tests

```bash
cd backend

# Test PDF processing
python -c "
from services.scientific_pdf_processor import scientific_pdf_processor
import glob
pdfs = glob.glob('/home/cmejo/arxiv-dataset/pdf/*.pdf')
if pdfs:
    result = scientific_pdf_processor.extract_comprehensive_content(pdfs[0])
    print(f'Processed: {result[\"metadata\"].get(\"title\", \"Unknown\")}')
"

# Test vector store
python -c "
import asyncio
from services.vector_store_service import vector_store_service
async def test():
    await vector_store_service.initialize()
    health = await vector_store_service.health_check()
    print(f'Vector store status: {health.get(\"status\")}')
asyncio.run(test())
"
```

### 2. End-to-End Test

```bash
# Run the complete test suite
python test_rag_system.py
```

## 🔍 Monitoring

### 1. Service Health

Check service status:
- ChromaDB: `http://localhost:8000/api/v1/heartbeat`
- Ollama: `http://localhost:11434/api/version`
- Backend: `http://localhost:8000/health`

### 2. Logs

Monitor logs:
```bash
# Docker services
docker-compose logs -f

# Backend logs
cd backend && python app.py

# Processing logs
tail -f backend/logs/processing.log
```

## 🚨 Troubleshooting

### Common Issues

#### 1. ChromaDB Connection Failed
```bash
# Check if ChromaDB is running
docker ps | grep chromadb

# Restart ChromaDB
docker-compose restart chromadb
```

#### 2. Ollama Models Not Available
```bash
# Check available models
docker exec ollama ollama list

# Pull missing models
docker exec ollama ollama pull llama2
```

#### 3. PDF Processing Errors
```bash
# Check PDF file permissions
ls -la /home/cmejo/arxiv-dataset/pdf/

# Test with a single PDF
python -c "
from pathlib import Path
pdfs = list(Path('/home/cmejo/arxiv-dataset/pdf').glob('*.pdf'))
print(f'Found {len(pdfs)} PDF files')
if pdfs:
    print(f'First PDF: {pdfs[0]}')
"
```

#### 4. Memory Issues
```bash
# Monitor memory usage
docker stats

# Reduce batch size in processing
# Edit process_arxiv_dataset.py and reduce batch_size parameter
```

## 📈 Performance Optimization

### 1. Batch Processing
- Start with small batches (10-50 PDFs)
- Monitor memory usage
- Adjust batch size based on system performance

### 2. Embedding Model Selection
- `all-MiniLM-L6-v2`: Fast, good quality (default)
- `all-mpnet-base-v2`: Higher quality, slower
- `multi-qa-MiniLM-L6-cos-v1`: Optimized for Q&A

### 3. Hardware Recommendations
- **RAM**: 16GB+ recommended for large datasets
- **Storage**: SSD recommended for vector database
- **CPU**: Multi-core for parallel processing

## 🎯 Next Steps

1. **Start Small**: Process 10-100 PDFs first to test the system
2. **Monitor Performance**: Watch memory and processing times
3. **Scale Gradually**: Increase batch sizes as system proves stable
4. **Customize**: Adjust embedding models and chunk sizes for your use case
5. **Integrate**: Connect with your existing research workflows

## 📚 API Documentation

Once the backend is running, visit:
- **API Docs**: `http://localhost:8000/docs`
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`

## 🤝 Support

If you encounter issues:
1. Check the logs for error messages
2. Verify all services are running
3. Test with a small subset of documents first
4. Monitor system resources (RAM, CPU, disk space)

The RAG system is designed to be robust and scalable, but start small and scale up as you become familiar with the system's behavior on your specific dataset and hardware.