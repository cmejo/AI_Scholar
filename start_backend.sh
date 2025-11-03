#!/bin/bash

# AI Scholar Backend Startup Script

echo "🚀 Starting AI Scholar Backend..."

# Check if Ollama is running on port 11435
if ! curl -s http://localhost:11435/api/tags > /dev/null; then
    echo "❌ Ollama is not running on port 11435"
    echo "Please start Ollama with:"
    echo "export OLLAMA_HOST=0.0.0.0:11435"
    echo "ollama serve"
    exit 1
fi

echo "✅ Ollama is running on port 11435"

# Check if models are available
MODELS=$(curl -s http://localhost:11435/api/tags | jq -r '.models | length')
if [ "$MODELS" -eq 0 ]; then
    echo "⚠️  No models found. Pulling llama3.1:8b..."
    OLLAMA_HOST=http://localhost:11435 ollama pull llama3.1:8b
fi

echo "✅ Models available: $(curl -s http://localhost:11435/api/tags | jq -r '.models[].name' | tr '\n' ' ')"

# Start the backend
echo "🔧 Starting backend server..."
cd backend
source venv/bin/activate
python simple_app.py

echo "🎉 Backend started on http://localhost:8000"