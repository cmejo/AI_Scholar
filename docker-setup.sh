#!/bin/bash

# AI Scholar Chatbot - Docker Setup Script
# Sets up the complete dockerized environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    print_status "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Check if Docker daemon is running
check_docker_daemon() {
    print_status "Checking Docker daemon..."
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    print_success "Docker daemon is running"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p data logs uploads ssl
    print_success "Directories created"
}

# Setup environment files
setup_environment() {
    print_status "Setting up environment files..."
    
    if [ ! -f .env.docker ]; then
        cat > .env.docker << EOF
# AI Scholar Chatbot - Docker Environment

# Ollama Configuration
OLLAMA_BASE_URL=http://ollama:11434
DEFAULT_MODEL=llama2:7b-chat

# Database Configuration
POSTGRES_DB=chatbot_db
POSTGRES_USER=chatbot_user
POSTGRES_PASSWORD=chatbot_secure_password_change_this

# Security (CHANGE THESE IN PRODUCTION!)
SECRET_KEY=your-production-secret-key-change-this-to-something-secure
JWT_SECRET_KEY=your-jwt-secret-key-change-this-to-something-secure
JWT_EXPIRES_HOURS=24
JWT_REFRESH_EXPIRES_DAYS=30

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Application Settings
FLASK_ENV=production
FLASK_DEBUG=false
EOF
        print_success "Created .env.docker file"
        print_warning "Please edit .env.docker and change the default passwords and secret keys!"
    else
        print_status ".env.docker already exists"
    fi
}

# Build Docker images
build_images() {
    print_status "Building Docker images..."
    docker-compose -f docker-compose.ollama.yml build
    print_success "Docker images built successfully"
}

# Pull required Docker images
pull_images() {
    print_status "Pulling required Docker images..."
    docker-compose -f docker-compose.ollama.yml pull
    print_success "Docker images pulled successfully"
}

# Start services
start_services() {
    print_status "Starting services..."
    docker-compose -f docker-compose.ollama.yml up -d
    print_success "Services started successfully"
}

# Wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for Ollama
    print_status "Waiting for Ollama to be ready..."
    timeout=300
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:11434/api/tags &> /dev/null; then
            print_success "Ollama is ready"
            break
        fi
        sleep 5
        timeout=$((timeout - 5))
    done
    
    if [ $timeout -le 0 ]; then
        print_error "Ollama failed to start within 5 minutes"
        return 1
    fi
    
    # Wait for backend
    print_status "Waiting for backend to be ready..."
    timeout=120
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:5000/api/health &> /dev/null; then
            print_success "Backend is ready"
            break
        fi
        sleep 5
        timeout=$((timeout - 5))
    done
    
    if [ $timeout -le 0 ]; then
        print_error "Backend failed to start within 2 minutes"
        return 1
    fi
}

# Download models
download_models() {
    print_status "Downloading recommended models..."
    
    # Start model downloader service
    docker-compose -f docker-compose.ollama.yml up model-downloader
    
    print_success "Model download completed"
}

# Show status
show_status() {
    print_status "Checking service status..."
    docker-compose -f docker-compose.ollama.yml ps
    
    echo ""
    print_success "🎉 AI Scholar Chatbot is now running!"
    echo ""
    echo "📋 Service URLs:"
    echo "  🌐 Backend API: http://localhost:5000"
    echo "  🤖 Ollama API: http://localhost:11434"
    echo "  📊 Health Check: http://localhost:5000/api/health"
    echo ""
    echo "🔧 Management Commands:"
    echo "  📊 View logs: docker-compose -f docker-compose.ollama.yml logs -f"
    echo "  🛑 Stop services: docker-compose -f docker-compose.ollama.yml down"
    echo "  🔄 Restart services: docker-compose -f docker-compose.ollama.yml restart"
    echo "  🧹 Clean up: docker-compose -f docker-compose.ollama.yml down -v"
    echo ""
    echo "📚 Available models:"
    curl -s http://localhost:11434/api/tags | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    models = [model['name'] for model in data.get('models', [])]
    for model in models:
        print(f'  🤖 {model}')
except:
    print('  ⏳ Models are still downloading...')
"
}

# Main setup function
main() {
    echo "🚀 AI Scholar Chatbot - Docker Setup"
    echo "===================================="
    
    check_docker
    check_docker_daemon
    create_directories
    setup_environment
    
    # Ask user for setup type
    echo ""
    echo "Choose setup type:"
    echo "1. Full production setup (with Nginx, PostgreSQL, Redis)"
    echo "2. Development setup (minimal, with hot reload)"
    echo "3. Quick test setup (Ollama + Backend only)"
    read -p "Enter choice (1-3): " choice
    
    case $choice in
        1)
            print_status "Setting up full production environment..."
            pull_images
            build_images
            start_services
            wait_for_services
            download_models
            ;;
        2)
            print_status "Setting up development environment..."
            docker-compose -f docker-compose.enhanced-dev.yml up -d
            wait_for_services
            ;;
        3)
            print_status "Setting up quick test environment..."
            docker-compose -f docker-compose.enhanced-dev.yml up -d ollama backend-dev
            wait_for_services
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
    
    show_status
}

# Handle script arguments
case "${1:-}" in
    "start")
        docker-compose -f docker-compose.ollama.yml up -d
        ;;
    "stop")
        docker-compose -f docker-compose.ollama.yml down
        ;;
    "restart")
        docker-compose -f docker-compose.ollama.yml restart
        ;;
    "logs")
        docker-compose -f docker-compose.ollama.yml logs -f
        ;;
    "status")
        docker-compose -f docker-compose.ollama.yml ps
        ;;
    "clean")
        docker-compose -f docker-compose.ollama.yml down -v
        docker system prune -f
        ;;
    "models")
        curl -s http://localhost:11434/api/tags | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = [model['name'] for model in data.get('models', [])]
for model in models:
    print(f'{model}')
"
        ;;
    *)
        main
        ;;
esac