#!/bin/bash

# AI Scholar RAG Setup Script
# This script sets up the complete development environment

set -e

echo "🚀 Setting up AI Scholar RAG System..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p backend/uploads
mkdir -p backend/chroma_db
mkdir -p ssl

# Set permissions
chmod 755 backend/uploads
chmod 755 backend/chroma_db

# Copy environment files
echo "⚙️ Setting up environment files..."
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env from example"
fi

if [ ! -f .env ]; then
    cat > .env << EOF
# Frontend Environment
VITE_API_URL=http://localhost:8000
VITE_OLLAMA_URL=http://localhost:11434

# Streamlit Environment
API_BASE_URL=http://localhost:8000
OLLAMA_URL=http://localhost:11434
EOF
    echo "✅ Created .env file"
fi

# Build and start services
echo "🐳 Building Docker containers..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if Ollama is ready and pull models
echo "🤖 Setting up Ollama models..."
docker-compose exec -T ollama ollama pull mistral || echo "⚠️ Failed to pull mistral model"
docker-compose exec -T ollama ollama pull nomic-embed-text || echo "⚠️ Failed to pull embedding model"

# Check service health
echo "🔍 Checking service health..."

# Check backend
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Backend is running"
else
    echo "❌ Backend is not responding"
fi

# Check frontend
if curl -f http://localhost:3000/ > /dev/null 2>&1; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend is not responding"
fi

# Check Streamlit
if curl -f http://localhost:8501/ > /dev/null 2>&1; then
    echo "✅ Streamlit is running"
else
    echo "❌ Streamlit is not responding"
fi

# Check Ollama
if curl -f http://localhost:11434/ > /dev/null 2>&1; then
    echo "✅ Ollama is running"
else
    echo "❌ Ollama is not responding"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📱 Access your applications:"
echo "   React Frontend:  http://localhost:3000"
echo "   Streamlit UI:    http://localhost:8501"
echo "   Backend API:     http://localhost:8000"
echo "   API Docs:        http://localhost:8000/docs"
echo ""
echo "🔧 Development commands:"
echo "   View logs:       docker-compose logs -f"
echo "   Stop services:   docker-compose down"
echo "   Restart:         docker-compose restart"
echo "   Clean up:        docker-compose down -v"
echo ""
echo "📚 Default login credentials:"
echo "   Email:    admin@example.com"
echo "   Password: admin123"