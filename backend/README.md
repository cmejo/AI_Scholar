# AI Scholar RAG Backend

Advanced RAG (Retrieval Augmented Generation) backend with multi-modal document processing, knowledge graphs, and enterprise features.

## Features

- **Multi-Modal Document Processing**: PDF, text, and image processing with OCR
- **Vector Search**: Semantic search using ChromaDB and Ollama embeddings
- **Knowledge Graphs**: Entity extraction and relationship mapping
- **Chain of Thought**: Step-by-step reasoning for complex queries
- **Citation-Aware Responses**: Precise source linking and citations
- **Document Comparison**: Side-by-side analysis of multiple documents
- **User Authentication**: JWT-based authentication system
- **Analytics**: Comprehensive usage analytics and insights

## Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Install spaCy model:**
```bash
python -m spacy download en_core_web_sm
```

3. **Install Ollama:**
```bash
# On macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull mistral
ollama pull nomic-embed-text
```

4. **Setup environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database:**
```bash
python -c "from core.database import init_db; import asyncio; asyncio.run(init_db())"
```

## Running the Application

1. **Start Ollama service:**
```bash
ollama serve
```

2. **Start the backend:**
```bash
python app.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

### Key Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/documents/upload` - Upload and process documents
- `POST /api/chat/message` - Send chat message with RAG
- `POST /api/documents/compare` - Compare multiple documents
- `GET /api/knowledge-graph/{document_id}` - Get knowledge graph
- `GET /api/search/semantic` - Semantic search

## Configuration

### Environment Variables

- `OLLAMA_URL`: Ollama service URL (default: http://localhost:11434)
- `OLLAMA_MODEL`: LLM model name (default: mistral)
- `EMBEDDING_MODEL`: Embedding model (default: nomic-embed-text)
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT secret key
- `CHROMA_PERSIST_DIR`: ChromaDB storage directory

### Supported File Types

- **PDF**: Text extraction, table detection, OCR for images
- **Text**: Plain text processing and chunking
- **Images**: OCR text extraction and object detection

## Architecture

```
backend/
├── app.py                 # FastAPI application
├── core/
│   ├── config.py         # Configuration settings
│   └── database.py       # Database models and setup
├── services/
│   ├── document_processor.py  # Document processing
│   ├── vector_store.py        # Vector database operations
│   ├── rag_service.py         # RAG response generation
│   ├── auth_service.py        # Authentication
│   ├── knowledge_graph.py     # Knowledge graph operations
│   ├── text_processor.py      # Text processing utilities
│   └── image_processor.py     # Image processing and OCR
└── models/
    └── schemas.py        # Pydantic models
```

## Integration with Frontend

The backend is designed to work seamlessly with the React frontend. Key integration points:

1. **Authentication**: JWT tokens for secure API access
2. **File Upload**: Multi-part form data for document uploads
3. **Real-time Chat**: RESTful API for chat interactions
4. **Analytics**: Dashboard data endpoints
5. **Knowledge Graph**: JSON data for graph visualization

## Development

### Adding New Features

1. **New API Endpoint**: Add to `app.py` with proper authentication
2. **New Service**: Create in `services/` directory
3. **Database Changes**: Update models in `core/database.py`
4. **New Schemas**: Add to `models/schemas.py`

### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## Production Deployment

1. **Use PostgreSQL** instead of SQLite:
```bash
pip install psycopg2-binary
# Update DATABASE_URL in .env
```

2. **Use Redis** for caching:
```bash
pip install redis
```

3. **Setup reverse proxy** (nginx/Apache)

4. **Use environment variables** for all secrets

5. **Setup monitoring** and logging

## Troubleshooting

### Common Issues

1. **Ollama Connection Error**: Ensure Ollama is running on the correct port
2. **spaCy Model Missing**: Run `python -m spacy download en_core_web_sm`
3. **ChromaDB Permission Error**: Check write permissions for `CHROMA_PERSIST_DIR`
4. **Large File Upload**: Adjust `MAX_FILE_SIZE` in configuration

### Logs

Check application logs for detailed error information:
```bash
tail -f app.log
```

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for public methods
4. Write tests for new features
5. Update documentation

## License

MIT License - see LICENSE file for details.