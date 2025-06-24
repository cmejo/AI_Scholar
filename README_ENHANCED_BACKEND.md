# AI Scholar Chatbot - Enhanced Open Source LLM Backend

## 🚀 Quick Start

### Automated Setup
```bash
python setup_enhanced_llm_backend.py
```

### Manual Setup
```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Start Ollama and pull a model
ollama serve
ollama pull llama2:7b-chat

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Start the backend
python app.py
```

### Start Application
```bash
./start.sh  # Unix/Linux/macOS
start.bat   # Windows
```

## 🧪 Test the Backend
```bash
python test_enhanced_backend.py
```

## 🌟 Features

- **🤖 Local LLM Integration**: Ollama for private, local AI models
- **🔄 Streaming Responses**: Real-time chat with WebSocket support
- **📚 RAG System**: Document-based question answering
- **🔍 Model Management**: Dynamic model switching and monitoring
- **🤗 HuggingFace Integration**: Model discovery and download
- **⚡ Performance Monitoring**: System health and usage analytics
- **🔧 Fine-tuning Support**: Custom model training capabilities
- **🔐 Authentication**: JWT-based user management
- **📊 Embeddings**: Vector search and semantic similarity

## 📡 API Endpoints

### Core Chat
- `POST /api/chat` - Send message
- `POST /api/chat/stream` - Streaming chat
- `GET /api/models/simple` - List available models

### Authentication
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login user

### Advanced Features
- `POST /api/rag/chat` - RAG-enhanced chat
- `GET /api/huggingface/search` - Search HF models
- `GET /api/system/status` - System monitoring

## 🔧 Configuration

Key environment variables:
```bash
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=llama2:7b-chat
DB_HOST=localhost
SECRET_KEY=your-secret-key
```

## 📖 Documentation

- [Complete Guide](ENHANCED_LLM_BACKEND_GUIDE.md) - Comprehensive documentation
- [API Reference](ENHANCED_LLM_BACKEND_GUIDE.md#api-endpoints) - All endpoints
- [Deployment Guide](ENHANCED_LLM_BACKEND_GUIDE.md#deployment) - Production setup

## 🤝 Frontend Integration

This backend is designed to work seamlessly with the existing React frontend:

```javascript
// The frontend chatService will automatically use:
// - WebSocket for real-time chat
// - REST API as fallback
// - Streaming responses
// - Authentication tokens
```

## 🛠️ Troubleshooting

1. **Ollama not responding**: `ollama serve`
2. **No models available**: `ollama pull llama2:7b-chat`
3. **Database issues**: Check `.env` configuration
4. **Port conflicts**: Ensure ports 5000 and 11434 are free

## 📊 Model Recommendations

- **Lightweight**: `tinyllama:1.1b` (1GB)
- **General**: `llama2:7b-chat` (4GB)
- **Code**: `codellama:7b-instruct` (4GB)
- **Advanced**: `llama2:13b-chat` (8GB)

## 🎯 What's Next?

1. Run the setup script
2. Test with `python test_enhanced_backend.py`
3. Start the React frontend
4. Explore the chat interface
5. Try advanced features like RAG and model switching

## 📞 Support

- Check [troubleshooting guide](ENHANCED_LLM_BACKEND_GUIDE.md#troubleshooting)
- Review [API documentation](ENHANCED_LLM_BACKEND_GUIDE.md#api-endpoints)
- Open an issue on GitHub

---

**Ready to chat with open source AI models locally? Let's get started! 🚀**