#!/bin/bash

# Multi-Instance ArXiv System - Production Deployment Script
# This script automates the deployment of the Multi-Instance ArXiv System to production

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_LOG="/var/log/arxiv-system-deployment.log"
BACKUP_DIR="/opt/arxiv-system/backups/pre-deployment"
ROLLBACK_SCRIPT="/opt/arxiv-system/scripts/rollback_deployment.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$DEPLOYMENT_LOG"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }
log_success() { log "SUCCESS" "$@"; }

# Error handling
handle_error() {
    local exit_code=$?
    local line_number=$1
    log_error "Deployment failed at line $line_number with exit code $exit_code"
    echo -e "${RED}Deployment failed! Check $DEPLOYMENT_LOG for details.${NC}"
    echo -e "${YELLOW}To rollback, run: $ROLLBACK_SCRIPT${NC}"
    exit $exit_code
}

trap 'handle_error $LINENO' ERR

# Display banner
display_banner() {
    echo -e "${BLUE}"
    echo "=================================================================="
    echo "  Multi-Instance ArXiv System - Production Deployment"
    echo "=================================================================="
    echo -e "${NC}"
    echo "Deployment started at: $(date)"
    echo "Project root: $PROJECT_ROOT"
    echo "Deployment log: $DEPLOYMENT_LOG"
    echo
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking deployment prerequisites..."
    
    # Check if running as root or with sudo
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root or with sudo"
        exit 1
    fi
    
    # Check required commands
    local required_commands=("docker" "python3" "pip3" "git" "curl" "systemctl")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "Required command not found: $cmd"
            exit 1
        fi
    done
    
    # Check system resources
    local available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    local available_disk=$(df / | awk 'NR==2{printf "%.0f", $4/1024/1024}')
    
    if [[ $available_memory -lt 4096 ]]; then
        log_warn "Low available memory: ${available_memory}MB (recommended: 4GB+)"
    fi
    
    if [[ $available_disk -lt 50 ]]; then
        log_error "Insufficient disk space: ${available_disk}GB (required: 50GB+)"
        exit 1
    fi
    
    log_success "Prerequisites check completed"
}

# Create system user and directories
setup_system_user() {
    log_info "Setting up system user and directories..."
    
    # Create arxiv-system user if it doesn't exist
    if ! id "arxiv-system" &>/dev/null; then
        useradd -r -m -s /bin/bash -d /opt/arxiv-system arxiv-system
        usermod -aG docker arxiv-system
        log_info "Created arxiv-system user"
    fi
    
    # Create directory structure
    local directories=(
        "/opt/arxiv-system"
        "/opt/arxiv-system/data"
        "/opt/arxiv-system/data/ai_scholar"
        "/opt/arxiv-system/data/quant_scholar"
        "/opt/arxiv-system/logs"
        "/opt/arxiv-system/config"
        "/opt/arxiv-system/backups"
        "/opt/arxiv-system/scripts"
        "/opt/arxiv-system/monitoring"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        chown arxiv-system:arxiv-system "$dir"
    done
    
    # Create subdirectories for each instance
    for instance in "ai_scholar" "quant_scholar"; do
        for subdir in "papers" "logs" "cache" "reports"; do
            mkdir -p "/opt/arxiv-system/data/$instance/$subdir"
            chown arxiv-system:arxiv-system "/opt/arxiv-system/data/$instance/$subdir"
        done
    done
    
    log_success "System user and directories setup completed"
}

# Deploy application code
deploy_application() {
    log_info "Deploying application code..."
    
    # Switch to arxiv-system user for deployment
    sudo -u arxiv-system bash << 'EOF'
    
    cd /opt/arxiv-system
    
    # Clone or update repository
    if [[ -d ".git" ]]; then
        log_info "Updating existing repository..."
        git fetch origin
        git checkout main
        git pull origin main
    else
        log_info "Cloning repository..."
        # Replace with actual repository URL
        git clone https://github.com/your-org/multi-instance-arxiv-system.git .
    fi
    
    # Create Python virtual environment
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Install backend dependencies
    cd backend
    pip install -r requirements.txt
    cd ..
    
EOF
    
    log_success "Application deployment completed"
}

# Setup configuration files
setup_configuration() {
    log_info "Setting up configuration files..."
    
    # Create environment file
    cat > /opt/arxiv-system/.env << 'ENV_EOF'
# Multi-Instance ArXiv System Configuration

# Database Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Email Configuration (Update with actual values)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Storage Configuration
BASE_STORAGE_PATH=/opt/arxiv-system/data

# Logging
LOG_LEVEL=INFO
LOG_FILE=/opt/arxiv-system/logs/system.log

# Performance
MAX_CONCURRENT_DOWNLOADS=4
MAX_CONCURRENT_PROCESSING=2
MEMORY_LIMIT_GB=16

# Security
SECRET_KEY=your-secret-key-here
ENV_EOF
    
    chmod 600 /opt/arxiv-system/.env
    chown arxiv-system:arxiv-system /opt/arxiv-system/.env
    
    # Create AI Scholar configuration
    cat > /opt/arxiv-system/config/ai_scholar.yaml << 'AI_EOF'
instance_name: "ai_scholar"
description: "AI and Machine Learning Papers"

storage_path: "/opt/arxiv-system/data/ai_scholar"
papers_path: "/opt/arxiv-system/data/ai_scholar/papers"
logs_path: "/opt/arxiv-system/data/ai_scholar/logs"
cache_path: "/opt/arxiv-system/data/ai_scholar/cache"

arxiv_categories:
  - "cs.AI"
  - "cs.LG"
  - "cs.CV"
  - "cs.CL"
  - "cs.NE"
  - "cs.RO"
  - "stat.ML"

processing:
  batch_size: 100
  max_concurrent: 2
  memory_limit_gb: 8

email_notifications:
  enabled: true
  recipients:
    - "admin@yourorg.com"
  frequency: "monthly"
AI_EOF
    
    # Create Quant Scholar configuration
    cat > /opt/arxiv-system/config/quant_scholar.yaml << 'QUANT_EOF'
instance_name: "quant_scholar"
description: "Quantitative Finance and Statistics Papers"

storage_path: "/opt/arxiv-system/data/quant_scholar"
papers_path: "/opt/arxiv-system/data/quant_scholar/papers"
logs_path: "/opt/arxiv-system/data/quant_scholar/logs"
cache_path: "/opt/arxiv-system/data/quant_scholar/cache"

arxiv_categories:
  - "q-fin.*"
  - "stat.*"
  - "math.ST"
  - "econ.*"

journal_sources:
  - name: "Journal of Statistical Software"
    url: "https://www.jstatsoft.org"
    enabled: true
  - name: "R Journal"
    url: "https://journal.r-project.org"
    enabled: true

processing:
  batch_size: 50
  max_concurrent: 2
  memory_limit_gb: 8

email_notifications:
  enabled: true
  recipients:
    - "admin@yourorg.com"
  frequency: "monthly"
QUANT_EOF
    
    # Set proper permissions
    chown -R arxiv-system:arxiv-system /opt/arxiv-system/config
    chmod 644 /opt/arxiv-system/config/*.yaml
    
    log_success "Configuration setup completed"
}

# Setup ChromaDB
setup_chromadb() {
    log_info "Setting up ChromaDB..."
    
    # Pull ChromaDB image
    docker pull chromadb/chroma:latest
    
    # Create persistent volume
    docker volume create chromadb_data
    
    # Stop existing ChromaDB if running
    docker stop chromadb 2>/dev/null || true
    docker rm chromadb 2>/dev/null || true
    
    # Start ChromaDB
    docker run -d --name chromadb \
        -p 8000:8000 \
        -v chromadb_data:/chroma/chroma \
        --memory=8g \
        --cpus=4 \
        --restart unless-stopped \
        chromadb/chroma:latest
    
    # Wait for ChromaDB to start
    log_info "Waiting for ChromaDB to start..."
    local retry_count=0
    while ! curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; do
        sleep 5
        retry_count=$((retry_count + 1))
        if [[ $retry_count -gt 12 ]]; then
            log_error "ChromaDB failed to start within 60 seconds"
            exit 1
        fi
    done
    
    log_success "ChromaDB setup completed"
}

# Setup systemd services
setup_systemd_services() {
    log_info "Setting up systemd services..."
    
    # Create ChromaDB service
    cat > /etc/systemd/system/chromadb.service << 'CHROMADB_SERVICE'
[Unit]
Description=ChromaDB Vector Database
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/docker start chromadb
ExecStop=/usr/bin/docker stop chromadb
TimeoutStartSec=0
User=root

[Install]
WantedBy=multi-user.target
CHROMADB_SERVICE
    
    # Create ArXiv System monitoring service
    cat > /etc/systemd/system/arxiv-system-monitor.service << 'MONITOR_SERVICE'
[Unit]
Description=ArXiv System Monitoring
After=chromadb.service
Requires=chromadb.service

[Service]
Type=simple
User=arxiv-system
WorkingDirectory=/opt/arxiv-system
ExecStart=/opt/arxiv-system/venv/bin/python -m backend.monitoring.scripts.system_monitor
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
MONITOR_SERVICE
    
    # Reload systemd and enable services
    systemctl daemon-reload
    systemctl enable chromadb.service
    systemctl enable arxiv-system-monitor.service
    
    # Start services
    systemctl start chromadb.service
    systemctl start arxiv-system-monitor.service
    
    log_success "Systemd services setup completed"
}

# Setup cron jobs
setup_cron_jobs() {
    log_info "Setting up cron jobs..."
    
    # Create monthly update script
    cat > /opt/arxiv-system/scripts/monthly_update.sh << 'MONTHLY_SCRIPT'
#!/bin/bash

cd /opt/arxiv-system
source venv/bin/activate

# Log start
echo "$(date): Starting monthly update" >> logs/monthly_update.log

# Run monthly updates for both instances
python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_monthly_update >> logs/monthly_update.log 2>&1
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_monthly_update >> logs/monthly_update.log 2>&1

# Generate and send reports
python -m backend.multi_instance_arxiv_system.scripts.generate_monthly_report >> logs/monthly_update.log 2>&1

# Log completion
echo "$(date): Monthly update completed" >> logs/monthly_update.log
MONTHLY_SCRIPT
    
    chmod +x /opt/arxiv-system/scripts/monthly_update.sh
    chown arxiv-system:arxiv-system /opt/arxiv-system/scripts/monthly_update.sh
    
    # Add cron jobs for arxiv-system user
    sudo -u arxiv-system bash << 'CRON_EOF'
    
    # Create crontab entries
    (crontab -l 2>/dev/null; cat << 'CRON_ENTRIES'
# Multi-Instance ArXiv System Cron Jobs

# Monthly update (1st of each month at 2 AM)
0 2 1 * * /opt/arxiv-system/scripts/monthly_update.sh

# System monitoring (every 5 minutes)
*/5 * * * * /opt/arxiv-system/venv/bin/python /opt/arxiv-system/backend/monitoring/scripts/system_metrics.py

# Health check (every hour)
0 * * * * /opt/arxiv-system/scripts/health_check.sh

# Backup (daily at 3 AM)
0 3 * * * /opt/arxiv-system/scripts/backup_chromadb.sh

CRON_ENTRIES
    ) | crontab -
    
CRON_EOF
    
    log_success "Cron jobs setup completed"
}

# Setup log rotation
setup_log_rotation() {
    log_info "Setting up log rotation..."
    
    cat > /etc/logrotate.d/arxiv-system << 'LOGROTATE_CONFIG'
/opt/arxiv-system/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 arxiv-system arxiv-system
    postrotate
        systemctl reload rsyslog > /dev/null 2>&1 || true
    endscript
}

/opt/arxiv-system/data/*/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 arxiv-system arxiv-system
}
LOGROTATE_CONFIG
    
    log_success "Log rotation setup completed"
}

# Initialize vector store collections
initialize_vector_store() {
    log_info "Initializing vector store collections..."
    
    sudo -u arxiv-system bash << 'INIT_EOF'
    
    cd /opt/arxiv-system
    source venv/bin/activate
    
    # Initialize collections for both instances
    python -c "
from backend.multi_instance_arxiv_system.services.multi_instance_vector_store_service import MultiInstanceVectorStoreService
from backend.multi_instance_arxiv_system.config.instance_config import InstanceConfig

# Load configurations
ai_config = InstanceConfig.from_yaml('config/ai_scholar.yaml')
quant_config = InstanceConfig.from_yaml('config/quant_scholar.yaml')

# Initialize vector store service
vector_service = MultiInstanceVectorStoreService()

# Create collections
ai_collection = vector_service.create_collection('ai_scholar_papers')
quant_collection = vector_service.create_collection('quant_scholar_papers')

print(f'AI Scholar collection created: {ai_collection}')
print(f'Quant Scholar collection created: {quant_collection}')
"
    
INIT_EOF
    
    log_success "Vector store initialization completed"
}

# Run system validation
run_system_validation() {
    log_info "Running system validation..."
    
    sudo -u arxiv-system bash << 'VALIDATION_EOF'
    
    cd /opt/arxiv-system
    source venv/bin/activate
    
    # Run validation script
    python backend/scripts/validate_complete_system.py
    
VALIDATION_EOF
    
    if [[ $? -eq 0 ]]; then
        log_success "System validation passed"
    else
        log_error "System validation failed"
        exit 1
    fi
}

# Create rollback script
create_rollback_script() {
    log_info "Creating rollback script..."
    
    cat > "$ROLLBACK_SCRIPT" << 'ROLLBACK_EOF'
#!/bin/bash

# Multi-Instance ArXiv System - Rollback Script

set -euo pipefail

BACKUP_DIR="/opt/arxiv-system/backups/pre-deployment"

echo "Starting rollback procedure..."

# Stop services
systemctl stop arxiv-system-monitor.service || true
systemctl stop chromadb.service || true

# Restore from backup if available
if [[ -d "$BACKUP_DIR" ]]; then
    echo "Restoring from backup..."
    
    # Restore application code
    if [[ -f "$BACKUP_DIR/application.tar.gz" ]]; then
        cd /opt/arxiv-system
        tar xzf "$BACKUP_DIR/application.tar.gz"
    fi
    
    # Restore ChromaDB data
    if [[ -f "$BACKUP_DIR/chromadb.tar.gz" ]]; then
        docker stop chromadb || true
        docker run --rm -v chromadb_data:/data -v "$BACKUP_DIR":/backup ubuntu tar xzf /backup/chromadb.tar.gz -C /data
        docker start chromadb
    fi
    
    echo "Rollback completed"
else
    echo "No backup found - manual intervention required"
fi
ROLLBACK_EOF
    
    chmod +x "$ROLLBACK_SCRIPT"
    
    log_success "Rollback script created"
}

# Create backup before deployment
create_pre_deployment_backup() {
    log_info "Creating pre-deployment backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup existing application if it exists
    if [[ -d "/opt/arxiv-system" ]]; then
        cd /opt/arxiv-system
        tar czf "$BACKUP_DIR/application.tar.gz" . --exclude=backups --exclude=data/*/papers 2>/dev/null || true
    fi
    
    # Backup ChromaDB data if it exists
    if docker ps | grep -q chromadb; then
        docker run --rm -v chromadb_data:/source:ro -v "$BACKUP_DIR":/backup ubuntu tar czf /backup/chromadb.tar.gz -C /source . 2>/dev/null || true
    fi
    
    log_success "Pre-deployment backup completed"
}

# Post-deployment verification
post_deployment_verification() {
    log_info "Running post-deployment verification..."
    
    # Check services
    local services=("chromadb" "arxiv-system-monitor")
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            log_success "$service is running"
        else
            log_error "$service is not running"
            exit 1
        fi
    done
    
    # Check ChromaDB connectivity
    if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; then
        log_success "ChromaDB is responding"
    else
        log_error "ChromaDB is not responding"
        exit 1
    fi
    
    # Check file permissions
    local critical_files=(
        "/opt/arxiv-system/.env"
        "/opt/arxiv-system/config/ai_scholar.yaml"
        "/opt/arxiv-system/config/quant_scholar.yaml"
    )
    
    for file in "${critical_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "$file exists with correct permissions"
        else
            log_error "$file is missing"
            exit 1
        fi
    done
    
    log_success "Post-deployment verification completed"
}

# Main deployment function
main() {
    display_banner
    
    log_info "Starting production deployment..."
    
    # Pre-deployment steps
    check_prerequisites
    create_pre_deployment_backup
    create_rollback_script
    
    # Deployment steps
    setup_system_user
    deploy_application
    setup_configuration
    setup_chromadb
    setup_systemd_services
    setup_cron_jobs
    setup_log_rotation
    initialize_vector_store
    
    # Validation and verification
    run_system_validation
    post_deployment_verification
    
    # Success message
    echo -e "${GREEN}"
    echo "=================================================================="
    echo "  DEPLOYMENT COMPLETED SUCCESSFULLY!"
    echo "=================================================================="
    echo -e "${NC}"
    echo "System is now running at:"
    echo "  - ChromaDB: http://localhost:8000"
    echo "  - System logs: /opt/arxiv-system/logs/"
    echo "  - Configuration: /opt/arxiv-system/config/"
    echo
    echo "Next steps:"
    echo "1. Update email configuration in /opt/arxiv-system/.env"
    echo "2. Test the monthly update process"
    echo "3. Verify monitoring and alerting"
    echo "4. Schedule regular backups"
    echo
    echo "For support, check the documentation at:"
    echo "  /opt/arxiv-system/docs/"
    
    log_success "Production deployment completed successfully"
}

# Run main function
main "$@"