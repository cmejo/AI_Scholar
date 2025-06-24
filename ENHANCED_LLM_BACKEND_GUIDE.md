# AI Scholar Chatbot - Enhanced LLM Backend Guide

## Overview

This enhanced backend provides a comprehensive open-source LLM integration for the AI Scholar chatbot project, featuring:

- **Ollama Integration**: Local LLM hosting and management
- **HuggingFace Integration**: Model discovery and download
- **RAG (Retrieval-Augmented Generation)**: Document-based question answering
- **Streaming Responses**: Real-time chat with streaming
- **Model Management**: Dynamic model switching and optimization
- **Fine-tuning Support**: Custom model training capabilities
- **Embeddings Service**: Vector search and semantic similarity
- **System Monitoring**: Performance tracking and health checks

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  Flask Backend  │    │     Ollama      │
│                 │◄──►│                 │◄──►│   (Local LLMs)  │
│  - Chat UI      │    │  - API Routes   │    │  - Model Mgmt   │
│  - Auth         │    │  - WebSocket    │    │  - Inference    │
│  - Settings     │    │  - Services     │    │  - Streaming    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   Database      │
                    │  - Users        │
                    │  - Sessions     │
                    │  - Messages     │
                    └─────────────────┘
```

## Quick Start

### 1. Automated Setup

```bash
# Run the setup script
python setup_enhanced_llm_backend.py

# Or manually:
chmod +x setup_enhanced_llm_backend.py
./setup_enhanced_llm_backend.py
```

### 2. Manual Setup

```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Start Ollama service
ollama serve

# 3. Pull a model
ollama pull llama2:7b-chat

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Set up environment
cp .env.example .env
# Edit .env with your settings

# 6. Initialize database
python manage_db.py init

# 7. Start the backend
python app.py
```

### 3. Start the Application

```bash
# Unix/Linux/macOS
./start.sh

# Windows
start.bat

# Manual
python app.py
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user
- `POST /api/auth/refresh` - Refresh token

### Chat
- `POST /api/chat` - Send chat message
- `POST /api/chat/stream` - Streaming chat
- `GET /api/chat/sessions` - Get chat sessions
- `POST /api/chat/sessions` - Create new session
- `GET /api/chat/sessions/{id}` - Get session messages
- `PUT /api/chat/sessions/{id}/model` - Switch model
- `PUT /api/chat/sessions/{id}/parameters` - Update parameters

### Models
- `GET /api/models` - List available models
- `GET /api/models/{name}` - Get model info
- `POST /api/models/pull` - Pull/download model
- `DELETE /api/models/{name}` - Delete model
- `GET /api/models/recommendations` - Get model recommendations

### HuggingFace Integration
- `GET /api/huggingface/search` - Search HF models
- `GET /api/huggingface/recommended` - Get recommended models
- `POST /api/huggingface/download` - Download HF model

### RAG (Retrieval-Augmented Generation)
- `POST /api/rag/ingest` - Upload document
- `POST /api/rag/ingest-text` - Add text content
- `POST /api/rag/search` - Search documents
- `POST /api/rag/chat` - RAG-enhanced chat
- `GET /api/rag/stats` - RAG statistics

### Embeddings
- `GET /api/embeddings/models` - List embedding models
- `POST /api/embeddings/generate` - Generate embeddings
- `POST /api/embeddings/collections` - Create collection
- `POST /api/embeddings/collections/{name}/search` - Search collection

### Fine-tuning
- `GET /api/fine-tuning/datasets` - List datasets
- `POST /api/fine-tuning/datasets` - Create dataset
- `POST /api/fine-tuning/start` - Start fine-tuning job
- `GET /api/fine-tuning/jobs` - List jobs

### System Monitoring
- `GET /api/health` - Health check
- `GET /api/system/status` - System status
- `GET /api/system/performance` - Performance metrics

## Configuration

### Environment Variables

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=llama2:7b-chat

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chatbot_db
DB_USER=chatbot_user
DB_PASSWORD=chatbot_password

# Security
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=jwt-secret-key
JWT_EXPIRES_HOURS=24

# Optional integrations
HUGGINGFACE_HUB_TOKEN=your_hf_token
OPENAI_API_KEY=your_openai_key
```

### Model Recommendations

#### Lightweight Models (1-3GB)
- `tinyllama:1.1b` - Very fast, basic capabilities
- `phi:2.7b` - Good balance of size and performance
- `gemma:2b` - Google's efficient model

#### General Purpose (4-8GB)
- `llama2:7b-chat` - Meta's conversational model
- `mistral:7b-instruct` - Excellent instruction following
- `neural-chat:7b` - Intel's optimized chat model

#### Code Assistance (4-8GB)
- `codellama:7b-instruct` - Code generation and explanation
- `deepseek-coder:6.7b` - Advanced coding capabilities

#### Advanced Models (8GB+)
- `llama2:13b-chat` - Better reasoning and knowledge
- `codellama:13b-instruct` - Advanced code assistance

## Services Overview

### 1. Ollama Service (`services/ollama_service.py`)

Handles local LLM management:

```python
from services.ollama_service import ollama_service

# List available models
models = ollama_service.list_models()

# Generate response
for response in ollama_service.chat(
    model="llama2:7b-chat",
    messages=[{"role": "user", "content": "Hello!"}],
    stream=True
):
    print(response.content)
```

### 2. Chat Service (`services/chat_service.py`)

Manages conversations with context:

```python
from services.chat_service import chat_service

# Generate response with context
for response in chat_service.generate_response(
    session_id=1,
    user_id=1,
    message="What is machine learning?",
    model="llama2:7b-chat",
    stream=True
):
    print(response.content)
```

### 3. Model Manager (`services/model_manager.py`)

Monitors and optimizes model performance:

```python
from services.model_manager import model_manager

# Get system status
status = model_manager.get_system_status()

# Get optimal model for use case
optimal = model_manager.get_optimal_model("code_assistance")

# Record usage statistics
model_manager.record_model_usage(
    model_name="llama2:7b-chat",
    response_time=2.5,
    token_count=150,
    success=True
)
```

### 4. RAG Service (`services/rag_service.py`)

Provides document-based question answering:

```python
from services.rag_service import rag_service

# Ingest document
rag_service.ingest_file("document.pdf", {"source": "upload"})

# Search documents
results = rag_service.search_documents("machine learning", max_results=5)

# Generate RAG response
response = rag_service.generate_rag_response(
    "What is machine learning?",
    model="llama2:7b-chat"
)
```

### 5. HuggingFace Service (`services/huggingface_service.py`)

Integrates with HuggingFace Hub:

```python
from services.huggingface_service import hf_service

# Search models
models = hf_service.search_models("llama", "text-generation")

# Download model for Ollama
hf_service.download_model_for_ollama("microsoft/DialoGPT-medium")
```

## Frontend Integration

### Chat Service Integration

The backend is designed to work seamlessly with the existing React frontend:

```javascript
// Frontend chat service usage
import { chatService } from './services/chatService';

// Send message (uses WebSocket or REST API fallback)
const response = await chatService.sendMessage(
  "Hello, how are you?",
  sessionId,
  authToken
);

// Health check
const isHealthy = await chatService.checkHealth();
```

### WebSocket Events

Real-time communication via Socket.IO:

```javascript
// Connect to WebSocket
socket.on('connect', () => {
  console.log('Connected to backend');
});

// Receive chat responses
socket.on('chat_response', (data) => {
  if (data.success) {
    displayMessage(data.response);
  }
});

// Handle typing indicators
socket.on('typing', (data) => {
  showTypingIndicator(data.typing);
});
```

## Advanced Features

### 1. Streaming Responses

Real-time response streaming for better UX:

```python
@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    def generate_stream():
        for response in chat_service.generate_response(..., stream=True):
            yield f"data: {json.dumps(response)}\n\n"
    
    return Response(generate_stream(), mimetype='text/event-stream')
```

### 2. Model Switching

Dynamic model switching per conversation:

```python
# Switch model for a session
success = chat_service.switch_model(session_id, "codellama:7b-instruct")

# Update model parameters
chat_service.update_model_parameters(session_id, {
    "temperature": 0.1,
    "top_p": 0.95
})
```

### 3. System Monitoring

Comprehensive monitoring and analytics:

```python
# Get performance report
report = model_manager.get_model_performance_report()

# Health check
health = model_manager.get_model_health_check()

# Cleanup unused models
removed = model_manager.cleanup_unused_models(days_unused=7)
```

### 4. RAG Integration

Document-based question answering:

```python
# Upload and process documents
POST /api/rag/ingest
Content-Type: multipart/form-data

# Chat with document context
POST /api/rag/chat
{
  "query": "What are the key findings?",
  "model": "llama2:7b-chat",
  "max_sources": 5
}
```

## Deployment

### Development

```bash
# Start all services
python app.py

# Or use the startup script
./start.sh
```

### Production

```bash
# Use Docker Compose
docker-compose -f docker-compose.enhanced.yml up -d

# Or deploy with Gunicorn
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
```

### Environment Setup

```bash
# Production environment variables
export FLASK_ENV=production
export FLASK_DEBUG=False
export SECRET_KEY=your-production-secret
export DATABASE_URL=postgresql://user:pass@host:port/db
```

## Troubleshooting

### Common Issues

1. **Ollama not responding**
   ```bash
   # Check if Ollama is running
   ps aux | grep ollama
   
   # Restart Ollama
   pkill ollama
   ollama serve
   ```

2. **Model not found**
   ```bash
   # List available models
   ollama list
   
   # Pull missing model
   ollama pull llama2:7b-chat
   ```

3. **Database connection issues**
   ```bash
   # Check database status
   python manage_db.py status
   
   # Initialize database
   python manage_db.py init
   ```

4. **Memory issues**
   ```bash
   # Check system resources
   curl http://localhost:5000/api/system/status
   
   # Use smaller models
   ollama pull tinyllama:1.1b
   ```

### Performance Optimization

1. **Model Selection**
   - Use smaller models for faster responses
   - Switch models based on use case
   - Monitor model performance metrics

2. **System Resources**
   - Ensure adequate RAM (8GB+ recommended)
   - Use SSD storage for better I/O
   - Monitor GPU usage if available

3. **Database Optimization**
   - Use PostgreSQL for production
   - Index frequently queried columns
   - Regular database maintenance

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section
- Review the API documentation
- Open an issue on GitHub
- Check Ollama documentation at https://ollama.ai

## Changelog

### v1.0.0 (Current)
- Initial enhanced LLM backend implementation
- Ollama integration with streaming support
- HuggingFace model search and download
- RAG system with document ingestion
- Model management and monitoring
- Fine-tuning capabilities
- Comprehensive API endpoints
- WebSocket support for real-time chat
- System monitoring and health checks