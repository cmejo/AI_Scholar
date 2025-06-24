# AI Scholar Chatbot - Enhanced Backend Setup Checklist

## ✅ Pre-Setup Checklist

Before running the setup, ensure you have:

- [ ] **Python 3.8+** installed (`python3 --version`)
- [ ] **pip** package manager available
- [ ] **At least 8GB RAM** (for running 7B models)
- [ ] **10GB+ free disk space** (for models)
- [ ] **Internet connection** (for downloading models)

## 🚀 Setup Steps

### Option 1: Automated Setup (Recommended)
```bash
# 1. Run the automated setup script
python3 setup_enhanced_llm_backend.py

# 2. Follow the prompts to:
#    - Install Ollama
#    - Set up Python environment
#    - Download recommended models
#    - Configure environment

# 3. Validate the setup
python3 validate_enhanced_setup.py

# 4. Test the backend
python3 test_enhanced_backend.py
```

### Option 2: Manual Setup
```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Start Ollama service
ollama serve

# 3. Pull a model (in another terminal)
ollama pull llama2:7b-chat

# 4. Install Python dependencies
pip3 install -r requirements.txt

# 5. Set up environment
cp .env.example .env
# Edit .env with your settings

# 6. Initialize database (if using PostgreSQL)
python3 manage_db.py init

# 7. Start the backend
python3 app.py
```

## 🧪 Validation Steps

### 1. Check Services
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Verify backend is running
curl http://localhost:5000/api/health

# Run comprehensive tests
python3 test_enhanced_backend.py
```

### 2. Test Basic Functionality
- [ ] Health check returns "healthy" status
- [ ] At least one model is available
- [ ] User registration works
- [ ] Chat endpoint responds
- [ ] WebSocket connection works

### 3. Test Advanced Features
- [ ] Model switching works
- [ ] RAG document ingestion works
- [ ] HuggingFace search works
- [ ] System monitoring works

## 🎯 Frontend Integration

### React Frontend Setup
```bash
# In the frontend directory
cd frontend
npm install
npm start
```

### Verify Integration
- [ ] Frontend connects to backend
- [ ] Chat interface works
- [ ] Authentication flows work
- [ ] Real-time features work

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Ollama Issues
```bash
# If Ollama won't start
pkill ollama
ollama serve

# If models are missing
ollama list
ollama pull llama2:7b-chat
```

#### Python Issues
```bash
# If dependencies are missing
pip3 install -r requirements.txt

# If virtual environment issues
python3 -m venv venv
source venv/bin/activate  # Unix/Linux/macOS
# or
venv\Scripts\activate.bat  # Windows
pip install -r requirements.txt
```

#### Database Issues
```bash
# If database connection fails
python3 manage_db.py status
python3 manage_db.py init

# For development, you can use SQLite
# Set in .env: DATABASE_URL=sqlite:///chatbot.db
```

#### Port Conflicts
```bash
# Check if ports are in use
lsof -i :5000  # Backend port
lsof -i :11434 # Ollama port
lsof -i :3000  # Frontend port

# Kill processes if needed
kill -9 <PID>
```

## 📊 Performance Optimization

### Model Selection by System
- **4GB RAM**: `tinyllama:1.1b`
- **8GB RAM**: `llama2:7b-chat` or `mistral:7b-instruct`
- **16GB+ RAM**: `llama2:13b-chat` or `codellama:13b-instruct`

### System Monitoring
```bash
# Check system resources
curl http://localhost:5000/api/system/status

# Monitor model performance
curl http://localhost:5000/api/system/performance
```

## 🎉 Success Criteria

Your setup is successful when:

- [ ] ✅ All services start without errors
- [ ] ✅ Health check returns "healthy"
- [ ] ✅ You can chat with the AI
- [ ] ✅ Frontend connects and works
- [ ] ✅ Advanced features are accessible

## 📚 Next Steps

Once setup is complete:

1. **Explore the API**: Check out all endpoints in the [API Guide](ENHANCED_LLM_BACKEND_GUIDE.md#api-endpoints)
2. **Try Advanced Features**: Upload documents for RAG, switch models, monitor performance
3. **Customize**: Modify system prompts, adjust model parameters, add new models
4. **Deploy**: Use Docker or cloud deployment for production

## 📞 Getting Help

If you encounter issues:

1. **Check the logs**: Look at console output for error messages
2. **Run validation**: `python3 validate_enhanced_setup.py`
3. **Check documentation**: [ENHANCED_LLM_BACKEND_GUIDE.md](ENHANCED_LLM_BACKEND_GUIDE.md)
4. **Review troubleshooting**: [Troubleshooting section](ENHANCED_LLM_BACKEND_GUIDE.md#troubleshooting)

---

**Ready to build amazing AI applications with open source models? Let's get started! 🚀**