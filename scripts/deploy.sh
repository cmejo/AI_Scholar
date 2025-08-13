#!/bin/bash
# AI Scholar Production Deployment Script for Ubuntu 24.04.2 LTS

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

log "Starting AI Scholar deployment on Ubuntu 24.04.2 LTS..."

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
    jq

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

# Configure firewall
log "Configuring firewall..."
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
log "Firewall configured"

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

# Create required directories
mkdir -p {data/{postgres,redis,chroma,ollama,elasticsearch,prometheus,grafana},logs/{nginx,backend},uploads,backups,ssl,config}

# Set proper permissions
chmod 755 data logs uploads backups ssl config
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

# Create environment file if it doesn't exist
if [ ! -f ".env" ]; then
    log "Creating environment file..."
    cp .env.production .env
    warn "Please edit .env file with your actual configuration values"
    warn "Especially update: DOMAIN_NAME, SSL_EMAIL, passwords, and API keys"
fi

# Make scripts executable
chmod +x scripts/*.sh

# Generate secure passwords if not set
log "Checking environment configuration..."
if grep -q "your_secure_.*_password_here" .env; then
    warn "Default passwords detected in .env file"
    warn "Please update all passwords before running in production"
fi

# Pull Docker images
log "Pulling Docker images..."
docker-compose -f docker-compose.prod.yml pull

# Build custom images
log "Building custom Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Create Docker networks
log "Creating Docker networks..."
docker network create ai-scholar-network 2>/dev/null || true

# Initialize Ollama models (this will take some time)
log "Initializing Ollama models..."
docker-compose -f docker-compose.prod.yml up -d ollama
sleep 30
docker-compose -f docker-compose.prod.yml exec ollama /ollama-init.sh || warn "Ollama initialization may need manual completion"

# Start core services
log "Starting core services..."
docker-compose -f docker-compose.prod.yml up -d postgres redis chromadb

# Wait for services to be ready
log "Waiting for services to be ready..."
sleep 30

# Start application services
log "Starting application services..."
docker-compose -f docker-compose.prod.yml up -d backend frontend nginx

# Start monitoring services (optional)
if [ "$1" = "--with-monitoring" ]; then
    log "Starting monitoring services..."
    docker-compose -f docker-compose.prod.yml --profile monitoring up -d
fi

# Start worker services (optional)
if [ "$1" = "--with-workers" ]; then
    log "Starting worker services..."
    docker-compose -f docker-compose.prod.yml --profile workers up -d
fi

# Start backup service (optional)
if [ "$1" = "--with-backup" ]; then
    log "Starting backup service..."
    docker-compose -f docker-compose.prod.yml --profile backup up -d
fi

# Health check
log "Performing health checks..."
sleep 30

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
echo -e "Frontend: ${GREEN}http://localhost:3005${NC} (or https://yourdomain.com after SSL setup)"
echo -e "Backend API: ${GREEN}http://localhost:8000${NC} (or https://yourdomain.com/api after SSL setup)"
echo -e "ChromaDB: ${GREEN}http://localhost:8080${NC}"
echo -e "Ollama: ${GREEN}http://localhost:11434${NC}"
echo
echo -e "${BLUE}=== NEXT STEPS ===${NC}"
echo "1. Update .env file with your actual configuration"
echo "2. Set up SSL certificates: ./scripts/setup-ssl.sh yourdomain.com"
echo "3. Configure your domain DNS to point to this server"
echo "4. Monitor logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "5. Access Grafana (if monitoring enabled): http://localhost:3001"
echo
echo -e "${YELLOW}=== SECURITY REMINDERS ===${NC}"
echo "- Change all default passwords in .env file"
echo "- Set up SSL certificates for production"
echo "- Configure backup strategy"
echo "- Review firewall settings"
echo "- Set up monitoring and alerting"
echo
log "Deployment script completed!"

# Remind about Docker group
if groups $USER | grep -q docker; then
    log "You may need to log out and back in for Docker group membership to take effect"
fi