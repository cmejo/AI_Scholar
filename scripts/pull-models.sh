#!/bin/bash

# Script to pull Ollama models for AI Scholar
echo "🚀 Pulling Ollama models for AI Scholar..."

# Set Ollama host
export OLLAMA_HOST=http://localhost:11435

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
while ! curl -s http://localhost:11435/api/tags > /dev/null; do
    echo "Waiting for Ollama service..."
    sleep 5
done

echo "✅ Ollama is ready!"

# Pull models
echo "📥 Pulling llama3.1:8b (default model)..."
ollama pull llama3.1:8b

echo "📥 Pulling llama3.1:70b (large model)..."
ollama pull llama3.1:70b

echo "📥 Pulling qwen2:72b (reasoning model)..."
ollama pull qwen2:72b

echo "📥 Pulling codellama:34b (code model)..."
ollama pull codellama:34b

echo "🎉 All models pulled successfully!"

# List available models
echo "📋 Available models:"
ollama list