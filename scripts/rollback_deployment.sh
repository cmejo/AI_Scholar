#!/bin/bash

# Multi-Instance ArXiv System - Deployment Rollback Script
# This script provides comprehensive rollback capabilities for failed deployments

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ROLLBACK_LOG="/var/log/arxiv-system-rollback.log"
BACKUP_DIR="/opt/arxiv-system/backups/pre-deployment"
EMERGENCY_BACKUP_DIR="/opt/arxiv-system/backups/emergency"

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
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$ROLLBACK_LOG"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }
log_success() { log "SUCCESS" "$@"; }

# Error handling
handle_error() {
    local exit_code=$?
    local line_number=$1
    log_error "Rollback failed at line $line_number with exit code $exit_code"
    echo -e "${RED}Rollback failed! Manual intervention required.${NC}"
    echo -e "${YELLOW}Check $ROLLBACK_LOG for details.${NC}"
    exit $exit_code
}

trap 'handle_error $LINENO' ERR

# Display banner
display_banner() {
    echo -e "${YELLOW}"
    echo "=================================================================="
    echo "  Multi-Instance ArXiv System - Deployment Rollback"
    echo "=================================================================="
    echo -e "${NC}"
    echo "Rollback started at: $(date)"
    echo "Rollback log: $ROLLBACK_LOG"
    echo
}

# Check rollback prerequisites
check_rollback_prerequisites() {
    log_info "Checking rollback prerequisites..."
    
    # Check if running as root or with sudo
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root or with sudo"
        exit 1
    fi
    
    # Check if backup directory exists
    if [[ ! -d "$BACKUP_DIR" ]]; then
        log_warn "Pre-deployment backup directory not found: $BACKUP_DIR"
        log_warn "Will attempt emergency procedures"
    fi
    
    log_success "Rollback prerequisites check completed"
}

# Create emergency backup of current state
create_emergency_backup() {
    log_info "Creating emergency backup of current state..."
    
    mkdir -p "$EMERGENCY_BACKUP_DIR"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    
    # Backup current application state
    if [[ -d "/opt/arxiv-system" ]]; then
        cd /opt/arxiv-system
        tar czf "$EMERGENCY_BACKUP_DIR/current_state_${timestamp}.tar.gz" . \
            --exclude=backups \
            --exclude=data/*/papers \
            --exclude=venv \
            2>/dev/null || true
        log_info "Current application state backed up"
    fi
    
    # Backup current ChromaDB state
    if docker ps | grep -q chromadb; then
        docker run --rm \
            -v chromadb_data:/source:ro \
            -v "$EMERGENCY_BACKUP_DIR":/backup \
            ubuntu tar czf "/backup/chromadb_current_${timestamp}.tar.gz" -C /source . \
            2>/dev/null || true
        log_info "Current ChromaDB state backed up"
    fi
    
    log_success "Emergency backup completed"
}

# Stop all services
stop_services() {
    log_info "Stopping all ArXiv system services..."
    
    local services=(
        "arxiv-system-monitor.service"
        "chromadb.service"
    )
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            log_info "Stopping $service..."
            systemctl stop "$service" || log_warn "Failed to stop $service"
        else
            log_info "$service is not running"
        fi
    done
    
    # Stop Docker containers
    if docker ps | grep -q chromadb; then
        log_info "Stopping ChromaDB container..."
        docker stop chromadb || log_warn "Failed to stop ChromaDB container"
    fi
    
    log_success "Services stopped"
}

# Restore application from backup
restore_application() {
    log_info "Restoring application from backup..."
    
    local backup_file="$BACKUP_DIR/application.tar.gz"
    
    if [[ -f "$backup_file" ]]; then
        log_info "Restoring application from: $backup_file"
        
        # Remove current application (except backups)
        cd /opt/arxiv-system
        find . -maxdepth 1 -not -name "backups" -not -name "." -exec rm -rf {} + 2>/dev/null || true
        
        # Restore from backup
        tar xzf "$backup_file" -C /opt/arxiv-system/
        
        # Fix permissions
        chown -R arxiv-system:arxiv-system /opt/arxiv-system
        chmod 600 /opt/arxiv-system/.env 2>/dev/null || true
        
        log_success "Application restored from backup"
    else
        log_warn "Application backup not found: $backup_file"
        log_warn "Skipping application restore"
    fi
}

# Restore ChromaDB from backup
restore_chromadb() {
    log_info "Restoring ChromaDB from backup..."
    
    local backup_file="$BACKUP_DIR/chromadb.tar.gz"
    
    if [[ -f "$backup_file" ]]; then
        log_info "Restoring ChromaDB from: $backup_file"
        
        # Stop ChromaDB if running
        docker stop chromadb 2>/dev/null || true
        
        # Clear existing data
        docker run --rm -v chromadb_data:/data ubuntu rm -rf /data/* 2>/dev/null || true
        
        # Restore from backup
        docker run --rm \
            -v chromadb_data:/data \
            -v "$BACKUP_DIR":/backup:ro \
            ubuntu tar xzf /backup/chromadb.tar.gz -C /data
        
        log_success "ChromaDB restored from backup"
    else
        log_warn "ChromaDB backup not found: $backup_file"
        log_warn "Will attempt to start with empty database"
    fi
}

# Restore system configuration
restore_system_configuration() {
    log_info "Restoring system configuration..."
    
    # Restore systemd services if backup exists
    local systemd_backup="$BACKUP_DIR/systemd_services.tar.gz"
    if [[ -f "$systemd_backup" ]]; then
        cd /etc/systemd/system
        tar xzf "$systemd_backup" 2>/dev/null || true
        systemctl daemon-reload
        log_info "Systemd services restored"
    fi
    
    # Restore cron jobs if backup exists
    local cron_backup="$BACKUP_DIR/crontab_backup.txt"
    if [[ -f "$cron_backup" ]]; then
        sudo -u arxiv-system crontab "$cron_backup" 2>/dev/null || true
        log_info "Cron jobs restored"
    fi
    
    # Restore logrotate configuration
    local logrotate_backup="$BACKUP_DIR/logrotate_arxiv-system"
    if [[ -f "$logrotate_backup" ]]; then
        cp "$logrotate_backup" /etc/logrotate.d/arxiv-system
        log_info "Logrotate configuration restored"
    fi
    
    log_success "System configuration restored"
}

# Start services after rollback
start_services() {
    log_info "Starting services after rollback..."
    
    # Start ChromaDB
    if docker ps -a | grep -q chromadb; then
        log_info "Starting ChromaDB container..."
        docker start chromadb
        
        # Wait for ChromaDB to be ready
        local retry_count=0
        while ! curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; do
            sleep 5
            retry_count=$((retry_count + 1))
            if [[ $retry_count -gt 12 ]]; then
                log_warn "ChromaDB did not start within 60 seconds"
                break
            fi
        done
        
        if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; then
            log_success "ChromaDB is running"
        else
            log_error "ChromaDB failed to start"
        fi
    else
        log_warn "ChromaDB container not found - may need manual setup"
    fi
    
    # Start systemd services
    local services=("chromadb.service" "arxiv-system-monitor.service")
    for service in "${services[@]}"; do
        if systemctl list-unit-files | grep -q "$service"; then
            log_info "Starting $service..."
            systemctl start "$service" || log_warn "Failed to start $service"
            
            if systemctl is-active --quiet "$service"; then
                log_success "$service is running"
            else
                log_warn "$service failed to start"
            fi
        else
            log_warn "$service not found"
        fi
    done
}

# Verify rollback success
verify_rollback() {
    log_info "Verifying rollback success..."
    
    local verification_passed=true
    
    # Check ChromaDB
    if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; then
        log_success "ChromaDB is responding"
    else
        log_error "ChromaDB is not responding"
        verification_passed=false
    fi
    
    # Check critical files
    local critical_files=(
        "/opt/arxiv-system/.env"
        "/opt/arxiv-system/config"
    )
    
    for file in "${critical_files[@]}"; do
        if [[ -e "$file" ]]; then
            log_success "$file exists"
        else
            log_error "$file is missing"
            verification_passed=false
        fi
    done
    
    # Check services
    local services=("chromadb.service")
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            log_success "$service is running"
        else
            log_warn "$service is not running"
        fi
    done
    
    if [[ "$verification_passed" == "true" ]]; then
        log_success "Rollback verification passed"
        return 0
    else
        log_error "Rollback verification failed"
        return 1
    fi
}

# Clean up failed deployment artifacts
cleanup_failed_deployment() {
    log_info "Cleaning up failed deployment artifacts..."
    
    # Remove any temporary files
    rm -rf /tmp/arxiv-system-* 2>/dev/null || true
    
    # Clean up any orphaned Docker containers
    docker container prune -f 2>/dev/null || true
    
    # Clean up any orphaned Docker images
    docker image prune -f 2>/dev/null || true
    
    log_success "Cleanup completed"
}

# Generate rollback report
generate_rollback_report() {
    log_info "Generating rollback report..."
    
    local report_file="/opt/arxiv-system/logs/rollback_report_$(date '+%Y%m%d_%H%M%S').txt"
    
    cat > "$report_file" << EOF
Multi-Instance ArXiv System - Rollback Report
============================================

Rollback Date: $(date)
Rollback Log: $ROLLBACK_LOG

System Status After Rollback:
-----------------------------

ChromaDB Status:
$(curl -s http://localhost:8000/api/v1/heartbeat > /dev/null && echo "✓ Running" || echo "✗ Not responding")

Services Status:
$(systemctl is-active chromadb.service 2>/dev/null && echo "✓ chromadb.service: active" || echo "✗ chromadb.service: inactive")
$(systemctl is-active arxiv-system-monitor.service 2>/dev/null && echo "✓ arxiv-system-monitor.service: active" || echo "✗ arxiv-system-monitor.service: inactive")

File System Status:
$(ls -la /opt/arxiv-system/ 2>/dev/null | head -10)

Disk Usage:
$(df -h /opt/arxiv-system 2>/dev/null || echo "Directory not found")

Memory Usage:
$(free -h)

Recommendations:
---------------
1. Verify all system functionality manually
2. Check application logs for any errors
3. Test core system operations
4. Consider investigating root cause of deployment failure
5. Update deployment procedures based on lessons learned

Emergency Contacts:
------------------
- System Administrator: admin@yourorg.com
- Technical Support: support@yourorg.com
- Emergency Hotline: +1-555-0123

EOF
    
    chown arxiv-system:arxiv-system "$report_file" 2>/dev/null || true
    
    log_success "Rollback report generated: $report_file"
}

# Interactive rollback mode
interactive_rollback() {
    echo -e "${YELLOW}Interactive Rollback Mode${NC}"
    echo "This will guide you through the rollback process step by step."
    echo
    
    read -p "Do you want to create an emergency backup of the current state? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_emergency_backup
    fi
    
    read -p "Do you want to stop all services? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        stop_services
    fi
    
    read -p "Do you want to restore the application from backup? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        restore_application
    fi
    
    read -p "Do you want to restore ChromaDB from backup? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        restore_chromadb
    fi
    
    read -p "Do you want to restore system configuration? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        restore_system_configuration
    fi
    
    read -p "Do you want to start services? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        start_services
    fi
    
    verify_rollback
    generate_rollback_report
}

# Automatic rollback mode
automatic_rollback() {
    log_info "Starting automatic rollback..."
    
    create_emergency_backup
    stop_services
    restore_application
    restore_chromadb
    restore_system_configuration
    start_services
    cleanup_failed_deployment
    
    if verify_rollback; then
        log_success "Automatic rollback completed successfully"
    else
        log_error "Automatic rollback completed with issues"
    fi
    
    generate_rollback_report
}

# Emergency rollback mode (minimal restoration)
emergency_rollback() {
    log_info "Starting emergency rollback..."
    
    # Stop everything
    systemctl stop arxiv-system-monitor.service 2>/dev/null || true
    docker stop chromadb 2>/dev/null || true
    
    # Try to restore minimal functionality
    if [[ -f "$BACKUP_DIR/chromadb.tar.gz" ]]; then
        log_info "Restoring ChromaDB from backup..."
        docker run --rm -v chromadb_data:/data ubuntu rm -rf /data/* 2>/dev/null || true
        docker run --rm \
            -v chromadb_data:/data \
            -v "$BACKUP_DIR":/backup:ro \
            ubuntu tar xzf /backup/chromadb.tar.gz -C /data 2>/dev/null || true
    fi
    
    # Start ChromaDB
    docker start chromadb 2>/dev/null || docker run -d --name chromadb \
        -p 8000:8000 \
        -v chromadb_data:/chroma/chroma \
        --restart unless-stopped \
        chromadb/chroma:latest
    
    log_warn "Emergency rollback completed - system may have limited functionality"
    generate_rollback_report
}

# Show usage information
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -i, --interactive    Interactive rollback mode"
    echo "  -a, --automatic      Automatic rollback mode (default)"
    echo "  -e, --emergency      Emergency rollback mode (minimal restoration)"
    echo "  -h, --help          Show this help message"
    echo
    echo "Examples:"
    echo "  $0                   # Automatic rollback"
    echo "  $0 --interactive     # Interactive rollback with prompts"
    echo "  $0 --emergency       # Emergency rollback (minimal)"
}

# Main rollback function
main() {
    local mode="automatic"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--interactive)
                mode="interactive"
                shift
                ;;
            -a|--automatic)
                mode="automatic"
                shift
                ;;
            -e|--emergency)
                mode="emergency"
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    display_banner
    check_rollback_prerequisites
    
    case $mode in
        interactive)
            interactive_rollback
            ;;
        automatic)
            automatic_rollback
            ;;
        emergency)
            emergency_rollback
            ;;
    esac
    
    echo -e "${GREEN}"
    echo "=================================================================="
    echo "  ROLLBACK COMPLETED"
    echo "=================================================================="
    echo -e "${NC}"
    echo "Rollback mode: $mode"
    echo "Rollback log: $ROLLBACK_LOG"
    echo "Report: /opt/arxiv-system/logs/rollback_report_*.txt"
    echo
    echo "Next steps:"
    echo "1. Verify system functionality manually"
    echo "2. Check application logs for errors"
    echo "3. Investigate root cause of deployment failure"
    echo "4. Update deployment procedures if needed"
    echo
    echo "If issues persist, contact technical support."
}

# Run main function
main "$@"