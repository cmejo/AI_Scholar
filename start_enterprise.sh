#!/bin/bash

# AI Chatbot Enterprise Edition Startup Script
# This script starts the enterprise version with real-time collaboration and admin dashboard

set -e

echo "🚀 Starting AI Chatbot Enterprise Edition"
echo "=========================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade requirements
echo "📥 Installing/updating dependencies..."
pip install -r requirements.txt

# Install additional enterprise dependencies
echo "📥 Installing enterprise dependencies..."
pip install python-socketio[client] prometheus-client

# Set up environment variables
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration"
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Initialize database
echo "💾 Initializing database..."
python -c "
from app_enterprise import app, db
with app.app_context():
    db.create_all()
    print('✅ Database initialized')
"

# Check if admin user exists, create if not
echo "👤 Checking admin user..."
python -c "
from app_enterprise import app
from models import db, User
import os

with app.app_context():
    admin_user = User.query.filter_by(is_admin=True).first()
    if not admin_user:
        # Create default admin user
        admin = User(
            username=os.environ.get('ADMIN_USERNAME', 'admin'),
            email=os.environ.get('ADMIN_EMAIL', 'admin@example.com'),
            password=os.environ.get('ADMIN_PASSWORD', 'admin123456')
        )
        admin.is_admin = True
        db.session.add(admin)
        db.session.commit()
        print('✅ Default admin user created')
        print(f'   Username: {admin.username}')
        print(f'   Email: {admin.email}')
        print('   Password: Check ADMIN_PASSWORD in .env file')
    else:
        print(f'✅ Admin user exists: {admin_user.username}')
"

# Check if Ollama is running
echo "🤖 Checking Ollama service..."
OLLAMA_URL=${OLLAMA_BASE_URL:-"http://localhost:11434"}
if curl -s "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
    echo "✅ Ollama is running at $OLLAMA_URL"
    
    # List available models
    echo "📋 Available models:"
    curl -s "$OLLAMA_URL/api/tags" | python -c "
import json, sys
try:
    data = json.load(sys.stdin)
    models = data.get('models', [])
    if models:
        for model in models[:5]:  # Show first 5 models
            print(f'   - {model[\"name\"]}')
        if len(models) > 5:
            print(f'   ... and {len(models) - 5} more')
    else:
        print('   No models found. Run: ollama pull llama2')
except:
    print('   Could not parse model list')
"
else
    echo "⚠️  Ollama is not running at $OLLAMA_URL"
    echo "   Please start Ollama first: ollama serve"
    echo "   Or update OLLAMA_BASE_URL in .env file"
fi

# Start the enterprise application
echo ""
echo "🌟 Starting Enterprise AI Chatbot..."
echo "   Backend: http://localhost:5000"
echo "   Admin Dashboard: http://localhost:3000/admin"
echo "   Health Check: http://localhost:5000/api/health"
echo ""
echo "Features enabled:"
echo "   ✅ Real-time collaboration via WebSockets"
echo "   ✅ Admin dashboard and user analytics"
echo "   ✅ Advanced user management"
echo "   ✅ System monitoring and health checks"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="

# Run the enterprise application
python app_enterprise.py