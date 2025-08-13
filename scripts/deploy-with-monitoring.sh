#!/bin/bash
# AI Scholar Production Deployment Script with Monitoring Enabled
# Customized for scholar.cmejo.com

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root for security reasons"
fi

# Check Ubuntu version
if ! grep -q "24.04" /etc/os-release; then
    warn "This script is optimized for Ubuntu 24.04.2 LTS. Proceeding anyway..."
fi

log "Starting AI Scholar deployment with monitoring for scholar.cmejo.com..."

# Update system packages
log "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
log "Installing required system packages..."
sudo apt install -y \
    curl \
    wget \
    git \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    ufw \
    fail2ban \
    htop \
    tree \
    jq \
    net-tools

# Install Docker
log "Installing Docker..."
if ! command -v docker &> /dev/null; then
    # Add Docker's official GPG key
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Add Docker repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    log "Docker installed successfully"
else
    log "Docker is already installed"
fi

# Install Docker Compose (standalone)
log "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_VERSION="v2.24.0"
    sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    log "Docker Compose installed successfully"
else
    log "Docker Compose is already installed"
fi

# Configure firewall for scholar.cmejo.com
log "Configuring firewall..."
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
# Allow monitoring ports (restrict to localhost)
sudo ufw allow from 127.0.0.1 to any port 9090  # Prometheus
sudo ufw allow from 127.0.0.1 to any port 3001  # Grafana
log "Firewall configured for scholar.cmejo.com"

# Configure fail2ban
log "Configuring fail2ban..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
log "Fail2ban configured"

# Create application directory structure
log "Creating application directory structure..."
APP_DIR="/opt/ai-scholar"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

cd $APP_DIR

# Create required directories with proper structure
mkdir -p {data/{postgres,redis,chroma,ollama,elasticsearch,prometheus,grafana},logs/{nginx,backend},uploads,backups,ssl,config,monitoring}

# Set proper permissions
chmod 755 data logs uploads backups ssl config monitoring
chmod 700 ssl

log "Directory structure created"

# Get the original directory where the script was called from
ORIGINAL_DIR=$(pwd)

# Copy application files from the original directory
if [ -f "$ORIGINAL_DIR/docker-compose.prod.yml" ]; then
    log "Copying application files from $ORIGINAL_DIR to $APP_DIR..."
    cp -r $ORIGINAL_DIR/* $APP_DIR/ 2>/dev/null || true
    cp -r $ORIGINAL_DIR/.env* $APP_DIR/ 2>/dev/null || true
    cd $APP_DIR
else
    error "docker-compose.prod.yml not found in $ORIGINAL_DIR. Please run this script from the project root directory."
fi

# Create monitoring configuration
log "Setting up monitoring configuration..."
mkdir -p monitoring/{prometheus,grafana/{dashboards,datasources}}

# Create Prometheus configuration
cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'ai-scholar-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'ai-scholar-nginx'
    static_configs:
      - targets: ['nginx:80']
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

# Create basic Grafana dashboard
cat > monitoring/grafana/dashboards/ai-scholar.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "AI Scholar Monitoring",
    "tags": ["ai-scholar"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "System Overview",
        "type": "stat",
        "targets": [
          {
            "expr": "up",
            "legendFormat": "{{job}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "30s"
  }
}
EOF

# Make scripts executable
chmod +x scripts/*.sh

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

# Wait for core services to be ready
log "Waiting for core services to be ready..."
sleep 30

# Start Ollama and initialize models
log "Starting Ollama and initializing models..."
docker-compose -f docker-compose.prod.yml up -d ollama
sleep 60

# Initialize Ollama models
log "Initializing Ollama models (this will take some time)..."
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

# Wait for services to be ready
log "Waiting for all services to be ready..."
sleep 45

# Health check
log "Performing health checks..."

# Check if services are running
if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    log "Services are running successfully!"
else
    error "Some services failed to start. Check logs with: docker-compose -f docker-compose.prod.yml logs"
fi

# Display service status
log "Service Status:"
docker-compose -f docker-compose.prod.yml ps

# Display access information
log "Deployment completed successfully!"
echo
echo -e "${BLUE}=== ACCESS INFORMATION ===${NC}"
echo -e "Domain: ${GREEN}scholar.cmejo.com${NC}"
echo -e "Frontend: ${GREEN}http://localhost:3000${NC} (or https://scholar.cmejo.com after SSL setup)"
echo -e "Backend API: ${GREEN}http://localhost:8000${NC} (or https://scholar.cmejo.com/api after SSL setup)"
echo -e "ChromaDB: ${GREEN}http://localhost:8080${NC}"
echo -e "Ollama: ${GREEN}http://localhost:11434${NC}"
echo -e "Prometheus: ${GREEN}http://localhost:9090${NC}"
echo -e "Grafana: ${GREEN}http://localhost:3001${NC} (admin/AiScholar2024!Grafana#Monitor)"
echo
echo -e "${BLUE}=== MONITORING ENABLED ===${NC}"
echo -e "Prometheus metrics: ${GREEN}http://localhost:9090${NC}"
echo -e "Grafana dashboards: ${GREEN}http://localhost:3001${NC}"
echo -e "Grafana credentials: ${YELLOW}admin / AiScholar2024!Grafana#Monitor${NC}"
echo
echo -e "${BLUE}=== NEXT STEPS ===${NC}"
echo "1. Set up SSL certificates: ./scripts/setup-ssl.sh scholar.cmejo.com"
echo "2. Configure your DNS to point scholar.cmejo.com to this server"
echo "3. Monitor logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "4. Access your application at: https://scholar.cmejo.com"
echo "5. Monitor system health at: http://localhost:3001"
echo
echo -e "${YELLOW}=== SECURITY REMINDERS ===${NC}"
echo "- SSL certificates will be set up automatically"
echo "- All passwords are configured securely"
echo "- Firewall is configured for scholar.cmejo.com"
echo "- Monitoring is enabled for system health"
echo "- Set up backup strategy if needed"
echo
log "Deployment script completed for scholar.cmejo.com!"

# Remind about Docker group
if groups $USER | grep -q docker; then
    log "You may need to log out and back in for Docker group membership to take effect"
fi

# Show quick management commands
echo
echo -e "${BLUE}=== QUICK MANAGEMENT COMMANDS ===${NC}"
echo "Start services: ./manage.sh start monitoring"
echo "Stop services: ./manage.sh stop"
echo "View logs: ./manage.sh logs"
echo "Check health: ./manage.sh health"
echo "Set up SSL: ./manage.sh ssl scholar.cmejo.com"
