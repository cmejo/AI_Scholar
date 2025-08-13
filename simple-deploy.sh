#!/bin/bash
# AI Scholar Simple Deployment Script
# Minimal deployment without permission changes

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
                                                       
  Simple Deployment for scholar.cmejo.com
EOF
echo -e "${NC}"

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    error "docker-compose.prod.yml not found. Please run this script from the project root directory."
fi

if [ ! -f ".env" ]; then
    error ".env file not found. Please ensure the .env file is present."
fi

log "Starting AI Scholar simple deployment..."

# Check Docker installation
if ! command -v docker &> /dev/null; then
    log "Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    warn "Docker installed. You may need to log out and back in for group membership to take effect."
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    log "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Create directories without changing permissions
log "Creating required directories..."
mkdir -p data/{postgres,redis,chroma,ollama,elasticsearch,prometheus,grafana}
mkdir -p logs/{nginx,backend}
mkdir -p uploads backups ssl config monitoring/{prometheus,grafana/{dashboards,datasources}}

# Create basic monitoring configuration
log "Setting up monitoring configuration..."

# Prometheus config
cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'ai-scholar-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 30s
EOF

# Grafana datasource config
cat > monitoring/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

# Create Docker network
log "Creating Docker network..."
docker network create ai-scholar-network 2>/dev/null || log "Network already exists"

# Pull images
log "Pulling Docker images..."
docker-compose -f docker-compose.prod.yml pull

# Build custom images
log "Building custom images..."
docker-compose -f docker-compose.prod.yml build

# Start services in stages
log "Starting database services..."
docker-compose -f docker-compose.prod.yml up -d postgres redis chromadb

log "Waiting for databases to be ready..."
sleep 30

log "Starting Ollama..."
docker-compose -f docker-compose.prod.yml up -d ollama

log "Waiting for Ollama to start..."
sleep 60

log "Starting application services..."
docker-compose -f docker-compose.prod.yml up -d backend frontend nginx

log "Starting monitoring services..."
docker-compose -f docker-compose.prod.yml --profile monitoring up -d

log "Waiting for all services to be ready..."
sleep 30

# Initialize Ollama models (optional, can be done later)
log "Initializing Ollama models (this may take a while)..."
docker-compose -f docker-compose.prod.yml exec -T ollama bash -c "
    echo 'Waiting for Ollama to be ready...'
    timeout=300
    while [ \$timeout -gt 0 ] && ! curl -f http://localhost:11434/api/tags >/dev/null 2>&1; do
        sleep 5
        timeout=\$((timeout-5))
    done
    
    if [ \$timeout -le 0 ]; then
        echo 'Timeout waiting for Ollama'
        exit 1
    fi
    
    echo 'Pulling essential models...'
    ollama pull mistral || echo 'Failed to pull mistral'
    ollama pull nomic-embed-text || echo 'Failed to pull nomic-embed-text'
    echo 'Model initialization completed (some models may have failed)'
" || warn "Ollama model initialization had issues - you can initialize models manually later"

# Show status
log "Checking service status..."
docker-compose -f docker-compose.prod.yml ps

# Test endpoints
log "Testing service endpoints..."
endpoints=(
    "http://localhost:8000/health:Backend"
    "http://localhost:3000/health:Frontend"
    "http://localhost:9090/-/healthy:Prometheus"
    "http://localhost:3001/api/health:Grafana"
)

for endpoint in "${endpoints[@]}"; do
    IFS=':' read -r url name <<< "$endpoint"
    if timeout 10 curl -f "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $name is responding${NC}"
    else
        echo -e "${YELLOW}⚠️  $name is not responding yet${NC}"
    fi
done

# Success message
echo
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETED! 🎉${NC}"
echo
echo -e "${BLUE}=== ACCESS INFORMATION ===${NC}"
echo -e "🌐 Domain: ${GREEN}scholar.cmejo.com${NC}"
echo -e "🚀 Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "🔧 Backend: ${GREEN}http://localhost:8000${NC}"
echo -e "📊 Grafana: ${GREEN}http://localhost:3001${NC}"
echo -e "   Username: ${YELLOW}admin${NC}"
echo -e "   Password: ${YELLOW}AiScholar2024!Grafana#Monitor${NC}"
echo -e "📈 Prometheus: ${GREEN}http://localhost:9090${NC}"
echo -e "🤖 Ollama: ${GREEN}http://localhost:11434${NC}"
echo
echo -e "${YELLOW}=== NEXT STEPS ===${NC}"
echo "1. Set up SSL: ${BLUE}./manage.sh ssl scholar.cmejo.com${NC}"
echo "2. Point DNS for scholar.cmejo.com to this server"
echo "3. Initialize more Ollama models if needed:"
echo "   ${BLUE}docker-compose -f docker-compose.prod.yml exec ollama ollama pull codellama:7b${NC}"
echo
echo -e "${GREEN}=== MANAGEMENT COMMANDS ===${NC}"
echo "./manage.sh status    # Check service status"
echo "./manage.sh logs      # View logs"
echo "./manage.sh health    # Health check"
echo "./manage.sh restart   # Restart services"
echo "./manage.sh stop      # Stop all services"
echo
log "🚀 Simple deployment completed successfully!"