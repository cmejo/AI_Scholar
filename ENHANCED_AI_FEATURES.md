# Enhanced AI Scholar Features

This document describes the newly implemented advanced AI capabilities that transform AI Scholar from a basic chatbot into a sophisticated AI assistant with specialized knowledge and multi-model support.

## 🚀 New Features Overview

### 1. Retrieval-Augmented Generation (RAG) for Specialized Knowledge

**What it is**: RAG allows AI Scholar to access and cite information from a private knowledge base, making it an expert on specific topics rather than relying solely on pre-trained knowledge.

**Key Benefits**:
- **Reduced Hallucinations**: Answers are grounded in your actual documents
- **Source Citations**: Every RAG response includes source references
- **Domain Expertise**: Becomes an expert on your specific content
- **Up-to-date Information**: Knowledge base can be updated with latest information

**Supported Document Formats**:
- PDF files (.pdf)
- Microsoft Word documents (.docx, .doc)
- Text files (.txt)
- Markdown files (.md)
- HTML files (.html, .htm)
- Direct text input

### 2. Multi-Model and Multi-Persona Support

**What it is**: Users can switch between different AI models on-the-fly, each optimized for different tasks and use cases.

**Model Categories**:
- **General Chat**: Best for everyday conversations (llama2, mistral)
- **Code Assistance**: Specialized for programming tasks (codellama, deepseek-coder)
- **Creative Writing**: Optimized for creative tasks (llama2-13b, neural-chat)
- **Lightweight**: Fast responses for simple queries (tinyllama, phi, gemma)

**Smart Recommendations**: The system automatically suggests the best model based on:
- Use case category
- Available system resources
- Model performance history

## 🛠️ Technical Implementation

### Backend Architecture

#### RAG Service (`services/rag_service.py`)
- **Vector Database**: ChromaDB for efficient similarity search
- **Embeddings**: SentenceTransformers for text vectorization
- **Document Processing**: Multi-format document parsing
- **Text Chunking**: Intelligent text splitting with overlap
- **Fallback Support**: In-memory storage when ChromaDB unavailable

#### Model Manager (`services/model_manager.py`)
- **Usage Tracking**: Monitors model performance and usage
- **Resource Management**: Considers system resources for recommendations
- **Health Monitoring**: Tracks model success rates and response times
- **Optimization**: Suggests optimal parameters per model and use case

#### Enhanced Chat Service (`services/chat_service.py`)
- **Context Management**: Maintains conversation context with model awareness
- **Parameter Optimization**: Dynamic parameter adjustment per model
- **Streaming Support**: Real-time response streaming
- **Session Persistence**: Model and RAG settings persist across sessions

### Frontend Components

#### ModelSelector Component
- **Category-based Selection**: Models organized by use case
- **RAG Toggle**: Easy enable/disable of knowledge base
- **Visual Indicators**: Shows current model and RAG status
- **Responsive Design**: Works on desktop and mobile

#### RAG Manager Component
- **Document Upload**: Drag-and-drop file upload
- **Text Input**: Direct text content addition
- **Statistics Dashboard**: Shows knowledge base metrics
- **Document Management**: Clear and refresh capabilities

#### Enhanced Message Component
- **Model Information**: Shows which model generated each response
- **RAG Indicators**: Visual indicators for knowledge-enhanced responses
- **Source Citations**: Expandable source references
- **Confidence Scores**: Shows RAG confidence levels

## 📊 API Enhancements

### Enhanced Chat Endpoints

#### POST `/api/chat`
```json
{
  "message": "Your question here",
  "model": "llama2:7b-chat",
  "use_rag": true,
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 2048
  }
}
```

**Response includes**:
- Model used
- RAG status
- Source citations (if RAG enabled)
- Confidence score
- Response metadata

#### POST `/api/chat/stream`
Real-time streaming version with same parameters.

### RAG Management Endpoints

#### POST `/api/rag/ingest`
Upload documents to knowledge base.

#### POST `/api/rag/ingest-text`
Add text content directly.

#### POST `/api/rag/search`
Search knowledge base.

#### POST `/api/rag/chat`
Direct RAG-enhanced chat.

#### GET `/api/rag/stats`
Knowledge base statistics.

### Model Management Endpoints

#### GET `/api/models/simple`
```json
{
  "models": ["llama2", "codellama", "mistral"],
  "categories": {
    "general_chat": ["llama2", "mistral"],
    "code_assistance": ["codellama"]
  },
  "default_model": "llama2",
  "recommendations": {...}
}
```

#### GET `/api/models/recommendations`
Get model recommendations by use case.

## 🎯 Usage Examples

### Basic Multi-Model Chat

```javascript
// Switch to code assistance model
await chatService.sendMessage(
  "Write a Python function to sort a list",
  sessionId,
  token,
  {
    model: "codellama:7b-instruct",
    use_rag: false
  }
);
```

### RAG-Enhanced Query

```javascript
// Ask question with knowledge base
await chatService.sendMessage(
  "What are the key concepts in our AI documentation?",
  sessionId,
  token,
  {
    model: "llama2:7b-chat",
    use_rag: true
  }
);
```

### Document Upload

```javascript
// Upload document to knowledge base
const formData = new FormData();
formData.append('file', pdfFile);

await axios.post('/api/rag/ingest', formData, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'multipart/form-data'
  }
});
```

## 🔧 Configuration

### Environment Variables

```bash
# RAG Configuration
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_MAX_SOURCES=5
RAG_MIN_SIMILARITY=0.3

# Model Configuration
DEFAULT_MODEL=llama2:7b-chat
MODEL_MONITORING=true
```

### RAG Service Configuration

```python
rag_service = RAGService(
    collection_name="ai_scholar_docs",
    embedding_model="all-MiniLM-L6-v2",
    chunk_size=1000,
    chunk_overlap=200
)
```

## 📈 Performance Monitoring

### Model Usage Tracking
- Response times
- Success rates
- Token usage
- Memory consumption

### RAG Metrics
- Document count
- Search performance
- Retrieval accuracy
- Confidence scores

### System Health
- Resource utilization
- Model availability
- Database status
- Error rates

## 🚀 Getting Started

### 1. Install Dependencies

```bash
# Backend dependencies
pip install chromadb sentence-transformers PyPDF2 python-docx beautifulsoup4

# Frontend dependencies (already included)
# ModelSelector and RAG components are ready to use
```

### 2. Initialize RAG System

```bash
# Start the application
python app.py

# Upload your first document via the UI or API
curl -X POST http://localhost:5000/api/rag/ingest-text \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "Your knowledge content here"}'
```

### 3. Test Multi-Model Support

```bash
# Run the test script
python test_enhanced_features.py
```

## 🔍 Troubleshooting

### Common Issues

1. **ChromaDB Installation Issues**
   ```bash
   pip install --upgrade chromadb
   ```

2. **Model Not Available**
   - Check Ollama is running
   - Verify model is pulled: `ollama pull llama2`

3. **RAG Not Working**
   - Check document upload was successful
   - Verify vector database initialization
   - Check similarity threshold settings

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🎉 What's Next

The enhanced AI Scholar now provides:

✅ **Intelligent Model Selection** - Right model for each task
✅ **Knowledge-Grounded Responses** - Answers based on your documents  
✅ **Source Attribution** - Know where answers come from
✅ **Performance Optimization** - Smart resource management
✅ **Extensible Architecture** - Easy to add new models and features

AI Scholar is now a true AI expert that can:
- Answer questions about your specific domain
- Switch between specialized models automatically
- Provide cited, accurate responses
- Learn from your documents
- Optimize performance based on usage patterns

Ready to explore the enhanced capabilities! 🚀
