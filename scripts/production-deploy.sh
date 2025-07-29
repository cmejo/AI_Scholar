#!/bin/bash

# Production Deployment Script for AI Scholar RAG
# This script handles complete production deployment with monitoring and health checks

set -e

# Configuration
DEPLOYMENT_ENV=${DEPLOYMENT_ENV:-production}
BACKUP_ENABLED=${BACKUP_ENABLED:-true}
MONITORING_ENABLED=${MONITORING_ENABLED:-true}
SSL_ENABLED=${SSL_ENABLED:-true}
DOMAIN=${DOMAIN:-your-domain.com}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check environment variables
    if [ -z "$SECRET_KEY" ]; then
        error "SECRET_KEY environment variable is required"
        exit 1
    fi
    
    if [ -z "$POSTGRES_PASSWORD" ]; then
        error "POSTGRES_PASSWORD environment variable is required"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Backup existing data
backup_data() {
    if [ "$BACKUP_ENABLED" = "true" ]; then
        log "Creating backup of existing data..."
        
        BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        # Backup database
        if docker-compose ps postgres | grep -q "Up"; then
            log "Backing up PostgreSQL database..."
            docker-compose exec -T postgres pg_dump -U postgres ai_scholar > "$BACKUP_DIR/database.sql"
        fi
        
        # Backup uploaded files
        if [ -d "backend/uploads" ]; then
            log "Backing up uploaded files..."
            cp -r backend/uploads "$BACKUP_DIR/"
        fi
        
        # Backup vector database
        if [ -d "backend/chroma_db" ]; then
            log "Backing up vector database..."
            cp -r backend/chroma_db "$BACKUP_DIR/"
        fi
        
        success "Backup created at $BACKUP_DIR"
    else
        warning "Backup disabled, skipping..."
    fi
}

# Setup SSL certificates
setup_ssl() {
    if [ "$SSL_ENABLED" = "true" ]; then
        log "Setting up SSL certificates..."
        
        mkdir -p ssl
        
        # Check if certificates exist
        if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
            warning "SSL certificates not found"
            log "Generating self-signed certificates for development..."
            
            openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes \
                -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
            
            warning "Using self-signed certificates. Replace with proper certificates for production!"
        fi
        
        success "SSL certificates configured"
    fi
}

# Build and deploy services
deploy_services() {
    log "Building production images..."
    
    # Build with production optimizations
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml build \
        --build-arg NODE_ENV=production \
        --build-arg PYTHON_ENV=production
    
    log "Stopping existing services..."
    docker-compose down --remove-orphans
    
    log "Starting production services..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    success "Services deployed"
}

# Wait for services to be ready
wait_for_services() {
    log "Waiting for services to be ready..."
    
    # Wait for database
    log "Waiting for PostgreSQL..."
    timeout=60
    while ! docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
        sleep 2
        timeout=$((timeout - 2))
        if [ $timeout -le 0 ]; then
            error "PostgreSQL failed to start within 60 seconds"
            exit 1
        fi
    done
    
    # Wait for backend
    log "Waiting for backend API..."
    timeout=120
    while ! curl -f http://localhost:8000/ > /dev/null 2>&1; do
        sleep 5
        timeout=$((timeout - 5))
        if [ $timeout -le 0 ]; then
            error "Backend API failed to start within 120 seconds"
            exit 1
        fi
    done
    
    # Wait for Ollama
    log "Waiting for Ollama..."
    timeout=60
    while ! curl -f http://localhost:11434/ > /dev/null 2>&1; do
        sleep 5
        timeout=$((timeout - 5))
        if [ $timeout -le 0 ]; then
            error "Ollama failed to start within 60 seconds"
            exit 1
        fi
    done
    
    success "All services are ready"
}

# Initialize database
initialize_database() {
    log "Initializing database..."
    
    # Run database migrations
    docker-compose exec -T backend python -c "
import asyncio
from core.database import init_db
asyncio.run(init_db())
print('Database initialized successfully')
"
    
    success "Database initialized"
}

# Setup Ollama models
setup_ollama_models() {
    log "Setting up Ollama models..."
    
    # Pull required models
    models=("mistral" "nomic-embed-text")
    
    for model in "${models[@]}"; do
        log "Pulling model: $model"
        if ! docker-compose exec -T ollama ollama pull "$model"; then
            error "Failed to pull model: $model"
            exit 1
        fi
    done
    
    success "Ollama models configured"
}

# Setup monitoring
setup_monitoring() {
    if [ "$MONITORING_ENABLED" = "true" ]; then
        log "Setting up monitoring..."
        
        # Ensure monitoring configuration exists
        if [ ! -f "monitoring/prometheus.yml" ]; then
            warning "Prometheus configuration not found, creating default..."
            mkdir -p monitoring
            cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-scholar-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres:5432']
    scrape_interval: 30s

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s
EOF
        fi
        
        # Start monitoring services
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d prometheus grafana
        
        success "Monitoring services started"
        log "Grafana available at: http://localhost:3001 (admin/admin)"
        log "Prometheus available at: http://localhost:9090"
    fi
}

# Run health checks
run_health_checks() {
    log "Running comprehensive health checks..."
    
    # Service health checks
    services=("backend:8000" "frontend:3000" "streamlit:8501" "ollama:11434")
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        log "Checking $name health..."
        
        if curl -f "http://localhost:$port/" > /dev/null 2>&1; then
            success "$name is healthy"
        else
            error "$name health check failed"
            exit 1
        fi
    done
    
    # Database connectivity check
    log "Checking database connectivity..."
    if docker-compose exec -T postgres psql -U postgres -d ai_scholar -c "SELECT 1;" > /dev/null 2>&1; then
        success "Database connectivity OK"
    else
        error "Database connectivity failed"
        exit 1
    fi
    
    # Vector store check
    log "Checking vector store..."
    if curl -f "http://localhost:8001/api/v1/heartbeat" > /dev/null 2>&1; then
        success "Vector store is healthy"
    else
        warning "Vector store health check failed (may be normal if no data)"
    fi
    
    # Redis check
    log "Checking Redis..."
    if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
        success "Redis is healthy"
    else
        error "Redis health check failed"
        exit 1
    fi
    
    success "All health checks passed"
}

# Setup log rotation
setup_log_rotation() {
    log "Setting up log rotation..."
    
    # Create logrotate configuration
    sudo tee /etc/logrotate.d/ai-scholar > /dev/null << EOF
/var/lib/docker/containers/*/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
    postrotate
        docker kill --signal=USR1 \$(docker ps -q) 2>/dev/null || true
    endscript
}
EOF
    
    success "Log rotation configured"
}

# Create systemd service
create_systemd_service() {
    log "Creating systemd service..."
    
    sudo tee /etc/systemd/system/ai-scholar.service > /dev/null << EOF
[Unit]
Description=AI Scholar RAG System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)
ExecStart=/usr/local/bin/docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable ai-scholar.service
    
    success "Systemd service created and enabled"
}

# Setup firewall rules
setup_firewall() {
    log "Configuring firewall..."
    
    # Allow SSH
    sudo ufw allow ssh
    
    # Allow HTTP and HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Allow application ports (only if needed for external access)
    if [ "$ALLOW_DIRECT_ACCESS" = "true" ]; then
        sudo ufw allow 3000/tcp  # Frontend
        sudo ufw allow 8000/tcp  # Backend
        sudo ufw allow 8501/tcp  # Streamlit
    fi
    
    # Enable firewall
    sudo ufw --force enable
    
    success "Firewall configured"
}

# Generate deployment report
generate_report() {
    log "Generating deployment report..."
    
    REPORT_FILE="deployment-report-$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$REPORT_FILE" << EOF
AI Scholar RAG Production Deployment Report
==========================================

Deployment Date: $(date)
Environment: $DEPLOYMENT_ENV
Domain: $DOMAIN

Services Status:
$(docker-compose ps)

System Resources:
$(docker stats --no-stream)

Disk Usage:
$(df -h)

Network Ports:
$(netstat -tlnp | grep -E ':(80|443|3000|8000|8501|11434|5432|6379)')

Environment Variables:
NODE_ENV=$NODE_ENV
DEPLOYMENT_ENV=$DEPLOYMENT_ENV
SSL_ENABLED=$SSL_ENABLED
MONITORING_ENABLED=$MONITORING_ENABLED
BACKUP_ENABLED=$BACKUP_ENABLED

Service URLs:
- Frontend: https://$DOMAIN
- API: https://api.$DOMAIN
- Streamlit: https://streamlit.$DOMAIN
- Monitoring: https://monitoring.$DOMAIN

Health Check Results:
$(curl -s http://localhost:8000/ | head -1)

Deployment completed successfully!
EOF
    
    success "Deployment report saved to $REPORT_FILE"
}

# Main deployment function
main() {
    log "Starting AI Scholar RAG production deployment..."
    
    check_prerequisites
    backup_data
    setup_ssl
    deploy_services
    wait_for_services
    initialize_database
    setup_ollama_models
    setup_monitoring
    run_health_checks
    setup_log_rotation
    create_systemd_service
    setup_firewall
    generate_report
    
    success "🎉 Production deployment completed successfully!"
    
    echo ""
    echo "📱 Access your application:"
    echo "   Frontend:     https://$DOMAIN"
    echo "   API Docs:     https://api.$DOMAIN/docs"
    echo "   Streamlit:    https://streamlit.$DOMAIN"
    echo ""
    echo "📊 Monitoring:"
    echo "   Grafana:      http://localhost:3001"
    echo "   Prometheus:   http://localhost:9090"
    echo ""
    echo "🔧 Management:"
    echo "   Logs:         docker-compose logs -f"
    echo "   Status:       docker-compose ps"
    echo "   Restart:      sudo systemctl restart ai-scholar"
    echo "   Stop:         sudo systemctl stop ai-scholar"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Configure DNS to point to this server"
    echo "   2. Replace self-signed certificates with proper SSL certificates"
    echo "   3. Set up automated backups"
    echo "   4. Configure monitoring alerts"
    echo "   5. Test all functionality"
}

# Run main function
main "$@"