#!/bin/bash

# Production deployment script for AI Scholar RAG
# Deploys the complete system to production environment

set -e

echo "🚀 Deploying AI Scholar RAG to production..."

# Check if we're in production mode
if [ "$NODE_ENV" != "production" ]; then
    echo "⚠️ Warning: NODE_ENV is not set to production"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Build production images
echo "🏗️ Building production images..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Stop existing services
echo "🛑 Stopping existing services..."
docker-compose down

# Start production services
echo "🚀 Starting production services..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose exec backend python -c "
from core.database import init_db
import asyncio
asyncio.run(init_db())
"

# Pull Ollama models
echo "🤖 Ensuring Ollama models are available..."
docker-compose exec ollama ollama pull mistral
docker-compose exec ollama ollama pull nomic-embed-text

# Health checks
echo "🔍 Running health checks..."

services=("backend:8000" "frontend:3000" "streamlit:8501" "ollama:11434")
for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if curl -f "http://localhost:$port/" > /dev/null 2>&1; then
        echo "✅ $name is healthy"
    else
        echo "❌ $name health check failed"
        exit 1
    fi
done

# Setup SSL certificates (if needed)
if [ -d "ssl" ]  && [ "$(ls -A ssl)" ]; then
    echo "🔒 SSL certificates found, enabling HTTPS..."
    # SSL setup would go here
fi

echo ""
echo "🎉 Production deployment complete!"
echo ""
echo "📱 Production URLs:"
echo "   Frontend:     https://your-domain.com"
echo "   Streamlit:    https://streamlit.your-domain.com"
echo "   API:          https://api.your-domain.com"
echo ""
echo "📊 Monitoring:"
echo "   Logs:         docker-compose logs -f"
echo "   Status:       docker-compose ps"
echo "   Resources:    docker stats"