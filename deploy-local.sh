#!/bin/bash
# AI Scholar Local Deployment Script
# Runs deployment from current directory without copying files

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

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    error "docker-compose.prod.yml not found. Please run this script from the project root directory."
fi

if [ ! -f ".env" ]; then
    error ".env file not found. Please ensure the .env file is present."
fi

log "Starting AI Scholar local deployment for scholar.cmejo.com..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root for security reasons"
fi

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    log "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    log "Docker installed. You may need to log out and back in."
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    log "Installing Docker Compose..."
    DOCKER_COMPOSE_VERSION="v2.24.0"
    sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Create required directories
log "Creating required directories..."
mkdir -p data/{postgres,redis,chroma,ollama,elasticsearch,prometheus,grafana}
mkdir -p logs/{nginx,backend}
mkdir -p uploads backups ssl config monitoring

# Set permissions safely (only if we can)
log "Setting directory permissions..."
chmod 755 data logs uploads config monitoring 2>/dev/null || warn "Could not set permissions on some directories (this is usually fine)"
chmod 755 backups 2>/dev/null || warn "Could not set permissions on backups directory (this is usually fine)"
chmod 700 ssl 2>/dev/null || warn "Could not set permissions on ssl directory (this is usually fine)"

# Configure firewall
log "Configuring firewall..."
sudo ufw --force enable 2>/dev/null || true
sudo ufw default deny incoming 2>/dev/null || true
sudo ufw default allow outgoing 2>/dev/null || true
sudo ufw allow ssh 2>/dev/null || true
sudo ufw allow 80/tcp 2>/dev/null || true
sudo ufw allow 443/tcp 2>/dev/null || true

# Create monitoring configuration
log "Setting up monitoring configuration..."
mkdir -p monitoring/{prometheus,grafana/{dashboards,datasources}}

# Create Prometheus configuration
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

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 30s
EOF

# Create Grafana datasource configuration
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

# Pull Docker images
log "Pulling Docker images..."
docker-compose -f docker-compose.prod.yml pull

# Build custom images
log "Building custom Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Create Docker networks
log "Creating Docker networks..."
docker network create ai-scholar-network 2>/dev/null || true

# Start core services first
log "Starting core services..."
docker-compose -f docker-compose.prod.yml up -d postgres redis chromadb

# Wait for core services
log "Waiting for core services to be ready..."
sleep 30

# Start Ollama
log "Starting Ollama..."
docker-compose -f docker-compose.prod.yml up -d ollama
sleep 60

# Initialize Ollama models
log "Initializing Ollama models (this may take several minutes)..."
docker-compose -f docker-compose.prod.yml exec ollama bash -c "
    echo 'Waiting for Ollama to be ready...'
    while ! curl -f http://localhost:11434/api/tags >/dev/null 2>&1; do
        sleep 5
    done
    echo 'Pulling models...'
    ollama pull mistral
    ollama pull nomic-embed-text
    ollama pull codellama:7b
    echo 'Models initialized successfully!'
" || warn "Ollama initialization may need manual completion"

# Start application services
log "Starting application services..."
docker-compose -f docker-compose.prod.yml up -d backend frontend nginx

# Start monitoring services
log "Starting monitoring services..."
docker-compose -f docker-compose.prod.yml --profile monitoring up -d

# Wait for all services
log "Waiting for all services to be ready..."
sleep 45

# Health check
log "Performing health checks..."
services_status=0

# Check if services are running
if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    log "✅ Services are running successfully!"
else
    error "❌ Some services failed to start. Check logs with: docker-compose -f docker-compose.prod.yml logs"
fi

# Test endpoints
endpoints=(
    "http://localhost:8000/health:Backend API"
    "http://localhost:3005/health:Frontend"
    "http://localhost:8080/api/v1/heartbeat:ChromaDB"
    "http://localhost:11434/api/tags:Ollama"
    "http://localhost:9090/-/healthy:Prometheus"
    "http://localhost:3001/api/health:Grafana"
)

log "Testing service endpoints..."
for endpoint in "${endpoints[@]}"; do
    IFS=':' read -r url name <<< "$endpoint"
    if curl -f "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $name is responding${NC}"
    else
        echo -e "${YELLOW}⚠️  $name is not responding (may still be starting)${NC}"
    fi
done

# Display service status
log "Current Service Status:"
docker-compose -f docker-compose.prod.yml ps

# Display access information
echo
echo -e "${BLUE}🎉 AI SCHOLAR DEPLOYMENT COMPLETED! 🎉${NC}"
echo
echo -e "${GREEN}=== ACCESS INFORMATION ===${NC}"
echo -e "🌐 Domain: ${BLUE}scholar.cmejo.com${NC}"
echo -e "🚀 Frontend: ${BLUE}http://localhost:3005${NC}"
echo -e "🔧 Backend API: ${BLUE}http://localhost:8000${NC}"
echo -e "📊 Grafana: ${BLUE}http://localhost:3001${NC} (admin/AiScholar2024!Grafana#Monitor)"
echo -e "📈 Prometheus: ${BLUE}http://localhost:9090${NC}"
echo -e "🤖 Ollama: ${BLUE}http://localhost:11434${NC}"
echo -e "🔍 ChromaDB: ${BLUE}http://localhost:8080${NC}"
echo
echo -e "${YELLOW}=== NEXT STEPS ===${NC}"
echo "1. Set up SSL: ${BLUE}./manage.sh ssl scholar.cmejo.com${NC}"
echo "2. Point DNS for scholar.cmejo.com to this server"
echo "3. Access your app: ${BLUE}https://scholar.cmejo.com${NC}"
echo "4. Monitor logs: ${BLUE}./manage.sh logs${NC}"
echo
echo -e "${GREEN}=== MANAGEMENT COMMANDS ===${NC}"
echo "./manage.sh status    # Check service status"
echo "./manage.sh logs      # View logs"
echo "./manage.sh health    # Health check"
echo "./manage.sh restart   # Restart services"
echo "./manage.sh stop      # Stop all services"
echo
log "🚀 Deployment completed successfully!"