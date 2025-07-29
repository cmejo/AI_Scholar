#!/bin/bash

# Development script for AI Scholar RAG
# Starts services in development mode with hot reloading

set -e

echo "🔧 Starting AI Scholar RAG in development mode..."

# Start core services (database, ollama)
echo "🚀 Starting core services..."
docker-compose up -d postgres ollama redis chromadb

# Wait for services
echo "⏳ Waiting for core services..."
sleep 5

# Start backend in development mode
echo "🐍 Starting backend..."
cd backend
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend in development mode
echo "⚛️ Starting frontend..."
npm run dev &
FRONTEND_PID=$!

# Start Streamlit in development mode
echo "📊 Starting Streamlit..."
cd streamlit_app
streamlit run app.py --server.port=8501 &
STREAMLIT_PID=$!
cd ..

echo ""
echo "🎉 Development environment started!"
echo ""
echo "📱 Access your applications:"
echo "   React Frontend:  http://localhost:5173"
echo "   Streamlit UI:    http://localhost:8501"
echo "   Backend API: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    kill $STREAMLIT_PID 2>/dev/null || true
    docker-compose stop
    echo "✅ All services stopped"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Wait for user to stop
wait