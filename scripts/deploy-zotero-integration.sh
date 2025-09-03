#!/bin/bash

# Zotero Integration Deployment Script
# This script handles the deployment of Zotero integration features

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-production}"
BACKUP_DIR="${PROJECT_ROOT}/backups/$(date +%Y%m%d_%H%M%S)"

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
    log "Checking deployment prerequisites..."
    
    # Check if required commands exist
    local required_commands=("docker" "docker-compose" "psql" "redis-cli")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error "Required command '$cmd' not found. Please install it first."
            exit 1
        fi
    done
    
    # Check if environment file exists
    if [[ ! -f "${PROJECT_ROOT}/.env.${ENVIRONMENT}" ]]; then
        error "Environment file .env.${ENVIRONMENT} not found"
        exit 1
    fi
    
    # Check if database is accessible
    source "${PROJECT_ROOT}/.env.${ENVIRONMENT}"
    if ! pg_isready -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER}" &> /dev/null; then
        error "Database is not accessible. Please check your database configuration."
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Create backup
create_backup() {
    log "Creating backup before deployment..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    source "${PROJECT_ROOT}/.env.${ENVIRONMENT}"
    pg_dump -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER}" -d "${DB_NAME}" \
        > "${BACKUP_DIR}/database_backup.sql"
    
    # Backup configuration files
    cp "${PROJECT_ROOT}/.env.${ENVIRONMENT}" "${BACKUP_DIR}/"
    cp -r "${PROJECT_ROOT}/config" "${BACKUP_DIR}/" 2>/dev/null || true
    
    # Backup current application state
    if [[ -d "${PROJECT_ROOT}/backend/zotero_attachments" ]]; then
        cp -r "${PROJECT_ROOT}/backend/zotero_attachments" "${BACKUP_DIR}/"
    fi
    
    success "Backup created at ${BACKUP_DIR}"
}

# Run database migrations
run_migrations() {
    log "Running Zotero integration database migrations..."
    
    cd "$PROJECT_ROOT"
    
    # Check if migrations directory exists
    if [[ ! -d "backend/migrations" ]]; then
        error "Migrations directory not found"
        exit 1
    fi
    
    # Run Zotero-specific migrations
    local zotero_migrations=(
        "001_zotero_integration_foundation.sql"
        "002_zotero_auth_tables.sql"
        "003_zotero_sync_tables.sql"
        "004_zotero_reference_tables.sql"
        "005_citation_management_tables.sql"
        "006_zotero_export_sharing_tables.sql"
        "007_zotero_annotation_sync_tables.sql"
    )
    
    source ".env.${ENVIRONMENT}"
    
    for migration in "${zotero_migrations[@]}"; do
        migration_file="backend/migrations/${migration}"
        if [[ -f "$migration_file" ]]; then
            log "Running migration: $migration"
            psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER}" -d "${DB_NAME}" \
                -f "$migration_file"
        else
            warning "Migration file not found: $migration"
        fi
    done
    
    success "Database migrations completed"
}

# Deploy backend services
deploy_backend() {
    log "Deploying Zotero integration backend services..."
    
    cd "$PROJECT_ROOT"
    
    # Install/update Python dependencies
    if [[ -f "backend/requirements.txt" ]]; then
        log "Installing Python dependencies..."
        pip install -r backend/requirements.txt
    fi
    
    # Create necessary directories
    mkdir -p backend/zotero_attachments
    mkdir -p backend/logs
    mkdir -p backend/temp
    
    # Set proper permissions
    chmod 755 backend/zotero_attachments
    chmod 755 backend/logs
    chmod 755 backend/temp
    
    # Copy configuration files
    if [[ -f "config/zotero_config.${ENVIRONMENT}.json" ]]; then
        cp "config/zotero_config.${ENVIRONMENT}.json" "backend/config/zotero_config.json"
    fi
    
    success "Backend deployment completed"
}

# Deploy frontend components
deploy_frontend() {
    log "Deploying Zotero integration frontend components..."
    
    cd "$PROJECT_ROOT"
    
    # Install/update Node.js dependencies
    if [[ -f "package.json" ]]; then
        log "Installing Node.js dependencies..."
        npm ci --production
    fi
    
    # Build frontend assets
    log "Building frontend assets..."
    npm run build
    
    # Copy built assets to appropriate location
    if [[ -d "dist" ]]; then
        mkdir -p "public/zotero"
        cp -r dist/* "public/zotero/"
    fi
    
    success "Frontend deployment completed"
}

# Configure services
configure_services() {
    log "Configuring Zotero integration services..."
    
    cd "$PROJECT_ROOT"
    
    # Configure Redis for caching
    if command -v redis-cli &> /dev/null; then
        log "Configuring Redis caching..."
        redis-cli CONFIG SET maxmemory-policy allkeys-lru
        redis-cli CONFIG SET maxmemory 256mb
    fi
    
    # Configure background job processing
    if [[ -f "config/celery_config.py" ]]; then
        cp "config/celery_config.py" "backend/config/"
    fi
    
    # Set up log rotation
    if [[ -f "config/logrotate.conf" ]]; then
        sudo cp "config/logrotate.conf" "/etc/logrotate.d/zotero-integration"
    fi
    
    success "Service configuration completed"
}

# Start services
start_services() {
    log "Starting Zotero integration services..."
    
    cd "$PROJECT_ROOT"
    
    # Start with docker-compose if available
    if [[ -f "docker-compose.yml" ]]; then
        log "Starting services with Docker Compose..."
        docker-compose -f docker-compose.yml up -d
    else
        # Start services individually
        log "Starting backend services..."
        
        # Start Celery workers for background tasks
        if [[ -f "backend/celery_worker.py" ]]; then
            nohup python backend/celery_worker.py > backend/logs/celery.log 2>&1 &
            echo $! > backend/celery.pid
        fi
        
        # Start main application
        if [[ -f "backend/app.py" ]]; then
            nohup python backend/app.py > backend/logs/app.log 2>&1 &
            echo $! > backend/app.pid
        fi
    fi
    
    success "Services started successfully"
}

# Verify deployment
verify_deployment() {
    log "Verifying Zotero integration deployment..."
    
    # Wait for services to start
    sleep 10
    
    # Check database connectivity
    source "${PROJECT_ROOT}/.env.${ENVIRONMENT}"
    if ! pg_isready -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER}" &> /dev/null; then
        error "Database connectivity check failed"
        return 1
    fi
    
    # Check if Zotero tables exist
    local table_check=$(psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER}" -d "${DB_NAME}" \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'zotero';")
    
    if [[ "$table_check" -lt 5 ]]; then
        error "Zotero database tables not found or incomplete"
        return 1
    fi
    
    # Check API endpoints
    local api_url="${API_BASE_URL:-http://localhost:8000}"
    if command -v curl &> /dev/null; then
        if ! curl -f "${api_url}/health" &> /dev/null; then
            warning "API health check failed - service may still be starting"
        fi
        
        if ! curl -f "${api_url}/api/zotero/status" &> /dev/null; then
            warning "Zotero API endpoints not responding - check service logs"
        fi
    fi
    
    # Check file permissions
    if [[ ! -w "backend/zotero_attachments" ]]; then
        error "Zotero attachments directory is not writable"
        return 1
    fi
    
    success "Deployment verification completed"
}

# Rollback function
rollback() {
    error "Deployment failed. Initiating rollback..."
    
    if [[ -d "$BACKUP_DIR" ]]; then
        log "Restoring from backup: $BACKUP_DIR"
        
        # Restore database
        source "${PROJECT_ROOT}/.env.${ENVIRONMENT}"
        if [[ -f "${BACKUP_DIR}/database_backup.sql" ]]; then
            psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER}" -d "${DB_NAME}" \
                < "${BACKUP_DIR}/database_backup.sql"
        fi
        
        # Restore configuration
        if [[ -f "${BACKUP_DIR}/.env.${ENVIRONMENT}" ]]; then
            cp "${BACKUP_DIR}/.env.${ENVIRONMENT}" "${PROJECT_ROOT}/"
        fi
        
        # Restore attachments
        if [[ -d "${BACKUP_DIR}/zotero_attachments" ]]; then
            rm -rf "${PROJECT_ROOT}/backend/zotero_attachments"
            cp -r "${BACKUP_DIR}/zotero_attachments" "${PROJECT_ROOT}/backend/"
        fi
        
        success "Rollback completed"
    else
        error "No backup found for rollback"
    fi
}

# Main deployment function
main() {
    log "Starting Zotero integration deployment for environment: $ENVIRONMENT"
    
    # Trap errors for rollback
    trap rollback ERR
    
    check_prerequisites
    create_backup
    run_migrations
    deploy_backend
    deploy_frontend
    configure_services
    start_services
    
    if verify_deployment; then
        success "Zotero integration deployment completed successfully!"
        log "Backup location: $BACKUP_DIR"
        log "Deployment logs: backend/logs/"
    else
        error "Deployment verification failed"
        exit 1
    fi
}

# Script usage
usage() {
    echo "Usage: $0 [environment]"
    echo "  environment: production, staging, development (default: production)"
    echo ""
    echo "Examples:"
    echo "  $0 production"
    echo "  $0 staging"
    echo "  $0 development"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
    production|staging|development|"")
        main
        ;;
    *)
        error "Invalid environment: $1"
        usage
        exit 1
        ;;
esac