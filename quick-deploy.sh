#!/bin/bash
# Quick Deploy Script for scholar.cmejo.com
# This script sets up everything with your specific configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

echo -e "${BLUE}"
cat << 'EOF'
   _____  _____    _____      _           _            
  |  _  ||_   _|  /  ___|    | |         | |           
  | |_| |  | |    \ `--.  ___| |__   ___ | | __ _ _ __ 
  |  _  |  | |     `--. \/ __| '_ \ / _ \| |/ _` | '__|
  | | | | _| |_   /\__/ / (__| | | | (_) | | (_| | |   
  \_| |_/ \___/   \____/ \___|_| |_|\___/|_|\__,_|_|   
                                                       
  Production Deployment for scholar.cmejo.com
EOF
echo -e "${NC}"

log "Starting AI Scholar deployment for scholar.cmejo.com..."

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    error "Please run this script from the AI Scholar project directory"
fi

# Check if .env file exists and is configured
if [ ! -f ".env" ]; then
    error ".env file not found. Please ensure the .env file is present."
fi

# Verify configuration
log "Verifying configuration for scholar.cmejo.com..."
if ! grep -q "scholar.cmejo.com" .env; then
    error "Configuration not set for scholar.cmejo.com. Please check .env file."
fi

# Run the build and run script
log "Running build and deployment..."
if [ -f "build-and-run.sh" ]; then
    ./build-and-run.sh
else
    # Fallback to simple deploy
    if [ -f "simple-deploy.sh" ]; then
        ./simple-deploy.sh
    else
        error "No deployment script found"
    fi
fi

# Wait for services to be fully ready
log "Waiting for services to be fully ready..."
sleep 60

# Perform comprehensive health check
log "Performing comprehensive health check..."

# Check core services
services=("postgres" "redis" "chromadb" "ollama" "backend" "frontend" "nginx" "prometheus" "grafana")
failed_services=()

for service in "${services[@]}"; do
    if docker-compose -f docker-compose.prod.yml ps | grep -q "$service.*Up"; then
        echo -e "${GREEN}✓ $service is running${NC}"
    else
        echo -e "${RED}✗ $service is not running${NC}"
        failed_services+=("$service")
    fi
done

# Check endpoints
log "Testing service endpoints..."
endpoints=(
    "http://localhost:8000/health:Backend API"
    "http://localhost:3005/health:Frontend"
    "http://localhost:8080/api/v1/heartbeat:ChromaDB"
    "http://localhost:11434/api/tags:Ollama"
    "http://localhost:9090/-/healthy:Prometheus"
    "http://localhost:3001/api/health:Grafana"
)

for endpoint in "${endpoints[@]}"; do
    IFS=':' read -r url name <<< "$endpoint"
    if curl -f "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ $name is responding${NC}"
    else
        echo -e "${YELLOW}⚠ $name is not responding (may still be starting)${NC}"
    fi
done

# Display final status
echo
if [ ${#failed_services[@]} -eq 0 ]; then
    log "🎉 Deployment completed successfully!"
    echo
    echo -e "${GREEN}=== AI SCHOLAR IS READY! ===${NC}"
    echo -e "🌐 Domain: ${BLUE}scholar.cmejo.com${NC}"
    echo -e "🚀 Frontend: ${BLUE}http://localhost:3005${NC}"
    echo -e "🔧 Backend API: ${BLUE}http://localhost:8000${NC}"
    echo -e "📊 Monitoring: ${BLUE}http://localhost:3001${NC}"
    echo -e "🤖 Ollama: ${BLUE}http://localhost:11434${NC}"
    echo
    echo -e "${YELLOW}=== NEXT STEPS ===${NC}"
    echo "1. Set up SSL: ${BLUE}./manage.sh ssl scholar.cmejo.com${NC}"
    echo "2. Point your DNS to this server"
    echo "3. Access your app: ${BLUE}https://scholar.cmejo.com${NC}"
    echo "4. Monitor health: ${BLUE}http://localhost:3001${NC}"
    echo
    echo -e "${GREEN}=== CREDENTIALS ===${NC}"
    echo "Grafana: admin / AiScholar2024!Grafana#Monitor"
    echo
    echo -e "${BLUE}=== MANAGEMENT COMMANDS ===${NC}"
    echo "./manage.sh status    # Check service status"
    echo "./manage.sh logs      # View logs"
    echo "./manage.sh health    # Health check"
    echo "./manage.sh ssl scholar.cmejo.com  # Set up SSL"
else
    warn "Some services failed to start: ${failed_services[*]}"
    echo "Check logs with: docker-compose -f docker-compose.prod.yml logs"
fi

log "Quick deploy completed!"