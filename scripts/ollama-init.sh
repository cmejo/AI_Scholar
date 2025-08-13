#!/bin/bash
# Ollama initialization script for AI Scholar

set -e

echo "Starting Ollama initialization..."

# Wait for Ollama service to be ready
echo "Waiting for Ollama service to start..."
while ! curl -f http://localhost:11434/api/tags >/dev/null 2>&1; do
    echo "Waiting for Ollama to be ready..."
    sleep 5
done

echo "Ollama service is ready!"

# Pull required models
echo "Pulling required models..."

# Pull embedding model for RAG
echo "Pulling nomic-embed-text model..."
ollama pull nomic-embed-text

# Pull main chat model
echo "Pulling mistral model..."
ollama pull mistral

# Pull code generation model
echo "Pulling codellama model..."
ollama pull codellama:7b

# Pull additional models based on environment variables
if [ ! -z "$OLLAMA_ADDITIONAL_MODELS" ]; then
    IFS=',' read -ra MODELS <<< "$OLLAMA_ADDITIONAL_MODELS"
    for model in "${MODELS[@]}"; do
        echo "Pulling additional model: $model"
        ollama pull "$model"
    done
fi

echo "Model initialization completed!"

# List all available models
echo "Available models:"
ollama list

echo "Ollama initialization finished successfully!"