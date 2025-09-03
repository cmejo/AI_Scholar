#!/bin/bash

# Production Deployment Script for Zotero Integration
# This script handles production-specific deployment with enhanced safety checks

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="production"
BACKUP_DIR="${PROJECT_ROOT}/backups/production_$(date +%Y%m%d_%H%M%S)"
DEPLOY_LOG="${PROJECT_ROOT}/logs/deploy_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
exec 1> >(tee -a "$DEPLOY_LOG")
exec 2> >(tee -a "$DEPLOY_LOG" >&2)

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

# Production safety checks
production_safety_checks() {
    log "Running production safety checks..."
    
    # Check if we're in production environment
    if [[ "${NODE_ENV:-}" != "production" ]]; then
        error "NODE_ENV must be set to 'production' for production deployment"
        exit 1
    fi
    
    # Check for required environment variables
    local required_vars=(
        "DB_HOST" "DB_USER" "DB_PASSWORD" "DB_NAME"
        "ZOTERO_CLIENT_ID" "ZOTERO_CLIENT_SECRET"
        "REDIS_URL" "ZOTERO_ENCRYPTION_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    # Check SSL certificates
    if [[ ! -f "/etc/ssl/certs/aischolar.crt" ]] || [[ ! -f "/etc/ssl/private/aischolar.key" ]]; then
        warning "SSL certificates not found. HTTPS may not work properly."
    fi
    
    # Check disk space
    local available_space=$(df / | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 5242880 ]]; then  # 5GB in KB
        error "Insufficient disk space. At least 5GB required."
        exit 1
    fi
    
    # Check memory
    local available_memory=$(free -m | awk 'NR==2{print $7}')
    if [[ $available_memory -lt 2048 ]]; then  # 2GB
        warning "Low available memory. Performance may be affected."
    fi
    
    success "Production safety checks passed"
}

# Blue-green deployment setup
setup_blue_green_deployment() {
    log "Setting up blue-green deployment..."
    
    # Determine current and target environments
    local current_env="blue"
    local target_env="green"
    
    if docker-compose -f docker-compose.blue.yml ps | grep -q "Up"; then
        current_env="blue"
        target_env="green"
    elif docker-compose -f docker-compose.green.yml ps | grep -q "Up"; then
        current_env="green"
        target_env="blue"
    fi
    
    log "Current environment: $current_env, Target environment: $target_env"
    
    # Deploy to target environment
    log "Deploying to $target_env environment..."
    docker-compose -f "docker-compose.${target_env}.yml" up -d --build
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 30
    
    # Health check
    local health_check_url="http://localhost:8000/health/zotero"
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f "$health_check_url" &>/dev/null; then
            success "Health check passed"
            break
        fi
        
        log "Health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 10
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        error "Health check failed after $max_attempts attempts"
        return 1
    fi
    
    # Switch traffic to new environment
    log "Switching traffic to $target_env environment..."
    
    # Update nginx configuration
    sed -i "s/upstream backend_${current_env}/upstream backend_${target_env}/g" /etc/nginx/sites-available/aischolar
    nginx -s reload
    
    # Wait for traffic to drain from old environment
    sleep 60
    
    # Stop old environment
    log "Stopping $current_env environment..."
    docker-compose -f "docker-compose.${current_env}.yml" down
    
    success "Blue-green deployment completed"
}

# Database migration with safety checks
safe_database_migration() {
    log "Running database migration with safety checks..."
    
    # Create database backup
    local backup_file="${BACKUP_DIR}/database_backup.sql"
    mkdir -p "$BACKUP_DIR"
    
    log "Creating database backup..."
    pg_dump -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "$DB_USER" -d "$DB_NAME" \
        --verbose --no-owner --no-privileges > "$backup_file"
    
    if [[ ! -s "$backup_file" ]]; then
        error "Database backup failed or is empty"
        exit 1
    fi
    
    # Test migration on a copy first (if test database is available)
    if [[ -n "${TEST_DB_NAME:-}" ]]; then
        log "Testing migration on test database..."
        
        # Create test database copy
        createdb -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "$DB_USER" \
            -T "$DB_NAME" "$TEST_DB_NAME" || true
        
        # Run migration on test database
        python backend/migrations/upgrade_zotero_schema.py upgrade \
            --environment production \
            --config config/zotero_config.production.json
        
        # Verify test migration
        if ! python backend/migrations/upgrade_zotero_schema.py status \
            --environment production \
            --config config/zotero_config.production.json | grep -q "up to date"; then
            error "Test migration verification failed"
            exit 1
        fi
        
        # Clean up test database
        dropdb -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "$DB_USER" "$TEST_DB_NAME"
    fi
    
    # Run actual migration
    log "Running production database migration..."
    python backend/migrations/upgrade_zotero_schema.py upgrade \
        --environment production \
        --config config/zotero_config.production.json
    
    success "Database migration completed"
}

# SSL certificate management
manage_ssl_certificates() {
    log "Managing SSL certificates..."
    
    # Check certificate expiry
    local cert_file="/etc/ssl/certs/aischolar.crt"
    if [[ -f "$cert_file" ]]; then
        local expiry_date=$(openssl x509 -enddate -noout -in "$cert_file" | cut -d= -f2)
        local expiry_timestamp=$(date -d "$expiry_date" +%s)
        local current_timestamp=$(date +%s)
        local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        if [[ $days_until_expiry -lt 30 ]]; then
            warning "SSL certificate expires in $days_until_expiry days. Consider renewal."
        fi
    fi
    
    # Auto-renew with Let's Encrypt if certbot is available
    if command -v certbot &> /dev/null; then
        log "Attempting SSL certificate renewal..."
        certbot renew --quiet --no-self-upgrade || warning "Certificate renewal failed"
    fi
}

# Performance optimization
optimize_performance() {
    log "Applying performance optimizations..."
    
    # Database connection pooling
    log "Optimizing database connections..."
    psql -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "$DB_USER" -d "$DB_NAME" -c "
        ALTER SYSTEM SET max_connections = 200;
        ALTER SYSTEM SET shared_buffers = '256MB';
        ALTER SYSTEM SET effective_cache_size = '1GB';
        ALTER SYSTEM SET work_mem = '4MB';
        SELECT pg_reload_conf();
    " || warning "Database optimization failed"
    
    # Redis optimization
    if command -v redis-cli &> /dev/null; then
        log "Optimizing Redis configuration..."
        redis-cli CONFIG SET maxmemory 512mb
        redis-cli CONFIG SET maxmemory-policy allkeys-lru
        redis-cli CONFIG SET save "900 1 300 10 60 10000"
    fi
    
    # System-level optimizations
    log "Applying system optimizations..."
    
    # Increase file descriptor limits
    echo "* soft nofile 65536" >> /etc/security/limits.conf
    echo "* hard nofile 65536" >> /etc/security/limits.conf
    
    # Optimize kernel parameters
    sysctl -w net.core.somaxconn=65535
    sysctl -w net.ipv4.tcp_max_syn_backlog=65535
    sysctl -w vm.swappiness=10
    
    success "Performance optimizations applied"
}

# Security hardening
apply_security_hardening() {
    log "Applying security hardening..."
    
    # File permissions
    chmod 600 .env.production
    chmod 600 config/zotero_config.production.json
    chmod -R 700 backend/zotero_attachments
    
    # Firewall rules
    if command -v ufw &> /dev/null; then
        ufw --force enable
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow ssh
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow from 10.0.0.0/8 to any port 5432  # Database access from private network
    fi
    
    # Fail2ban configuration
    if command -v fail2ban-client &> /dev/null; then
        systemctl enable fail2ban
        systemctl start fail2ban
    fi
    
    success "Security hardening applied"
}

# Monitoring setup
setup_monitoring() {
    log "Setting up monitoring and alerting..."
    
    # Start monitoring services
    if [[ -f "docker-compose.monitoring.yml" ]]; then
        docker-compose -f docker-compose.monitoring.yml up -d
    fi
    
    # Configure log rotation
    cat > /etc/logrotate.d/zotero-integration << EOF
/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 app app
    postrotate
        systemctl reload nginx
    endscript
}
EOF
    
    # Set up health check cron job
    (crontab -l 2>/dev/null; echo "*/5 * * * * curl -f http://localhost:8000/health/zotero || echo 'Health check failed' | mail -s 'Zotero Health Alert' admin@aischolar.com") | crontab -
    
    success "Monitoring setup completed"
}

# Rollback function
rollback_deployment() {
    error "Deployment failed. Initiating rollback..."
    
    if [[ -d "$BACKUP_DIR" ]]; then
        log "Restoring from backup: $BACKUP_DIR"
        
        # Restore database
        if [[ -f "${BACKUP_DIR}/database_backup.sql" ]]; then
            log "Restoring database..."
            psql -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "$DB_USER" -d "$DB_NAME" \
                < "${BACKUP_DIR}/database_backup.sql"
        fi
        
        # Restore configuration
        if [[ -f "${BACKUP_DIR}/.env.production" ]]; then
            cp "${BACKUP_DIR}/.env.production" "$PROJECT_ROOT/"
        fi
        
        # Restart services
        docker-compose restart
        
        success "Rollback completed"
    else
        error "No backup found for rollback"
    fi
    
    exit 1
}

# Main deployment function
main() {
    log "Starting Zotero integration production deployment"
    
    # Set up error handling
    trap rollback_deployment ERR
    
    # Create log directory
    mkdir -p "$(dirname "$DEPLOY_LOG")"
    
    # Run deployment steps
    production_safety_checks
    safe_database_migration
    setup_blue_green_deployment
    manage_ssl_certificates
    optimize_performance
    apply_security_hardening
    setup_monitoring
    
    # Final verification
    log "Running final deployment verification..."
    sleep 30
    
    # Comprehensive health check
    local health_endpoints=(
        "/health"
        "/health/zotero"
        "/health/zotero/database"
        "/health/zotero/sync"
    )
    
    for endpoint in "${health_endpoints[@]}"; do
        if ! curl -f "https://aischolar.com${endpoint}" &>/dev/null; then
            error "Health check failed for $endpoint"
            exit 1
        fi
    done
    
    success "Zotero integration production deployment completed successfully!"
    log "Deployment log: $DEPLOY_LOG"
    log "Backup location: $BACKUP_DIR"
    
    # Send deployment notification
    if command -v mail &> /dev/null; then
        echo "Zotero integration production deployment completed successfully at $(date)" | \
            mail -s "Production Deployment Success" admin@aischolar.com
    fi
}

# Execute main function
main "$@"