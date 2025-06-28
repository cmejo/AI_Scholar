#!/bin/bash

# AI Chatbot Advanced Enterprise Edition Startup Script
# This script starts the advanced enterprise version with sophisticated sharing and custom analytics

set -e

echo "🚀 Starting AI Chatbot Advanced Enterprise Edition"
echo "=================================================="

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

# Install additional advanced enterprise dependencies
echo "📥 Installing advanced enterprise dependencies..."
pip install python-socketio[client] prometheus-client redis

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

# Initialize database with advanced features
echo "💾 Initializing database with advanced features..."
python -c "
from app_enterprise import app, db
from models import User, CustomDashboard, SessionInvitation, SessionActivityLog
import os

with app.app_context():
    # Create all tables including new advanced features
    db.create_all()
    print('✅ Database initialized with advanced features')
    
    # Check if admin user exists, create if not
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
        print('✅ Default admin user created with advanced privileges')
        print(f'   Username: {admin.username}')
        print(f'   Email: {admin.email}')
        print('   Password: Check ADMIN_PASSWORD in .env file')
    else:
        print(f'✅ Admin user exists: {admin_user.username}')
    
    # Create sample dashboard for admin
    sample_dashboard = CustomDashboard.query.filter_by(name='System Overview Dashboard').first()
    if not sample_dashboard and admin_user:
        sample_dashboard = CustomDashboard(
            user_id=admin_user.id,
            name='System Overview Dashboard',
            description='Default system monitoring dashboard',
            layout={'cols': 12, 'rows': 8},
            widgets=[
                {
                    'id': 'widget_1',
                    'name': 'User Activity',
                    'type': 'chart',
                    'data_source': 'user_activity',
                    'config': {'chart_type': 'line', 'days': 30},
                    'position': {'x': 0, 'y': 0, 'w': 6, 'h': 4}
                },
                {
                    'id': 'widget_2',
                    'name': 'System Health',
                    'type': 'status',
                    'data_source': 'system_health',
                    'config': {'refresh_interval': 30},
                    'position': {'x': 6, 'y': 0, 'w': 6, 'h': 4}
                },
                {
                    'id': 'widget_3',
                    'name': 'Message Volume',
                    'type': 'chart',
                    'data_source': 'message_analytics',
                    'config': {'chart_type': 'bar', 'days': 7},
                    'position': {'x': 0, 'y': 4, 'w': 12, 'h': 4}
                }
            ],
            is_default=True,
            is_public=False
        )
        db.session.add(sample_dashboard)
        db.session.commit()
        print('✅ Sample dashboard created')
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

# Check if Redis is available (optional for caching)
echo "🔄 Checking Redis service (optional)..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis is running (analytics caching enabled)"
    else
        echo "⚠️  Redis is not running (analytics caching disabled)"
    fi
else
    echo "ℹ️  Redis not installed (analytics caching disabled)"
fi

# Start the advanced enterprise application
echo ""
echo "🌟 Starting Advanced Enterprise AI Chatbot..."
echo "   Backend: http://localhost:5000"
echo "   Enhanced Admin Dashboard: http://localhost:3000/admin"
echo "   Health Check: http://localhost:5000/api/health"
echo ""
echo "Advanced Features enabled:"
echo "   ✅ Real-time collaboration via WebSockets"
echo "   ✅ Advanced session sharing with permissions"
echo "   ✅ Invitation-based collaboration system"
echo "   ✅ Activity logging and audit trails"
echo "   ✅ Custom analytics dashboards"
echo "   ✅ Drag-and-drop dashboard builder"
echo "   ✅ Multi-source widget data integration"
echo "   ✅ Dashboard export functionality"
echo "   ✅ Enhanced admin user management"
echo "   ✅ Collaboration analytics and insights"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================================="

# Run the advanced enterprise application
python app_enterprise.py