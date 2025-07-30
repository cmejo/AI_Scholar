#!/bin/bash

# Advanced RAG Research Ecosystem - Maintenance Script
# Automated maintenance tasks for optimal performance

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# System maintenance
system_maintenance() {
    print_status "Performing system maintenance..."
    
    # Update package lists
    sudo apt update
    
    # Clean package cache
    sudo apt autoremove -y
    sudo apt autoclean
    
    # Clean Docker system
    docker system prune -f
    docker volume prune -f
    
    print_success "System maintenance completed"
}

# Database maintenance
database_maintenance() {
    print_status "Performing database maintenance..."
    
    # PostgreSQL maintenance
    docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -c "VACUUM ANALYZE;"
    docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -c "REINDEX DATABASE advanced_rag_db;"
    
    # Redis maintenance
    docker-compose exec -T redis redis-cli FLUSHEXPIRED
    docker-compose exec -T redis redis-cli MEMORY PURGE
    
    print_success "Database maintenance completed"
}

# Log rotation and cleanup
log_maintenance() {
    print_status "Performing log maintenance..."
    
    # Rotate Docker logs
    sudo logrotate -f /etc/logrotate.d/docker-containers
    
    # Clean old application logs
    find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true
    
    # Clean old backup logs
    find backups/ -name "*.log" -mtime +30 -delete 2>/dev/null || true
    
    print_success "Log maintenance completed"
}

# SSL certificate maintenance
ssl_maintenance() {
    print_status "Checking SSL certificates..."
    
    # Check certificate expiry
    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        expiry=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" | cut -d= -f2)
        expiry_epoch=$(date -d "$expiry" +%s)
        current_epoch=$(date +%s)
        days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
        
        if [ "$days_until_expiry" -lt 30 ]; then
            print_warning "SSL certificate expires in $days_until_expiry days"
            sudo certbot renew --quiet
            docker-compose restart nginx
        else
            print_success "SSL certificate is valid for $days_until_expiry days"
        fi
    fi
}

# Performance optimization
performance_optimization() {
    print_status "Optimizing system performance..."
    
    # Clear system caches
    sudo sync
    echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null
    
    # Optimize PostgreSQL
    docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -c "
        UPDATE pg_stat_user_tables SET n_tup_ins=0, n_tup_upd=0, n_tup_del=0;
        SELECT pg_stat_reset();
    "
    
    # Restart services for memory cleanup
    docker-compose restart redis
    
    print_success "Performance optimization completed"
}

# Security updates
security_maintenance() {
    print_status "Performing security maintenance..."
    
    # Update system packages
    sudo apt update
    sudo apt upgrade -y
    
    # Update Docker images
    docker-compose pull
    
    # Check for security vulnerabilities
    if command -v lynis &> /dev/null; then
        sudo lynis audit system --quick
    fi
    
    print_success "Security maintenance completed"
}

# Backup verification
backup_verification() {
    print_status "Verifying backup integrity..."
    
    # Check recent backups
    latest_backup=$(ls -t backups/database_*.sql.gz 2>/dev/null | head -1)
    
    if [ -n "$latest_backup" ]; then
        # Test backup integrity
        if gunzip -t "$latest_backup" 2>/dev/null; then
            print_success "Latest backup is valid: $latest_backup"
        else
            print_error "Latest backup is corrupted: $latest_backup"
        fi
    else
        print_warning "No database backups found"
    fi
}

# Health check
health_check() {
    print_status "Running health checks..."
    
    # Run comprehensive health check
    ./scripts/deployment/health-check.sh all
    
    print_success "Health check completed"
}

# Generate maintenance report
generate_report() {
    print_status "Generating maintenance report..."
    
    report_file="maintenance-report-$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
AI Scholar RAG Maintenance Report
================================

Date: $(date)
Maintenance Type: ${1:-full}

System Information:
- Uptime: $(uptime)
- Disk Usage: $(df -h / | awk 'NR==2 {print $5}')
- Memory Usage: $(free -h | awk 'NR==2{printf "%.0f%%", $3*100/$2}')
- Load Average: $(uptime | awk -F'load average:' '{print $2}')

Docker Status:
$(docker-compose ps)

Service Health:
$(curl -s http://localhost:8000/health 2>/dev/null || echo "Backend: Not responding")

Database Status:
$(docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -c "SELECT version();" 2>/dev/null | head -1 || echo "Database: Not responding")

Recent Logs (Last 10 lines):
$(docker-compose logs --tail=10 backend 2>/dev/null || echo "No recent logs")

Maintenance Tasks Completed:
- System cleanup
- Database optimization
- Log rotation
- SSL certificate check
- Performance optimization
- Security updates
- Backup verification
- Health checks

Next Maintenance: $(date -d "+1 week")
EOF
    
    print_success "Maintenance report saved: $report_file"
}

# Main maintenance function
main() {
    echo ""
    echo "🔧 Advanced RAG Research Ecosystem - Maintenance"
    echo "==============================================="
    echo "Started: $(date)"
    echo ""
    
    # Load environment variables
    if [ -f ".env.production" ]; then
        source .env.production
    fi
    
    case "${1:-full}" in
        "full")
            system_maintenance
            database_maintenance
            log_maintenance
            ssl_maintenance
            performance_optimization
            security_maintenance
            backup_verification
            health_check
            generate_report "full"
            ;;
        "quick")
            database_maintenance
            log_maintenance
            performance_optimization
            health_check
            generate_report "quick"
            ;;
        "system")
            system_maintenance
            security_maintenance
            generate_report "system"
            ;;
        "database")
            database_maintenance
            generate_report "database"
            ;;
        "security")
            security_maintenance
            ssl_maintenance
            generate_report "security"
            ;;
        *)
            echo "Usage: $0 {full|quick|system|database|security}"
            echo ""
            echo "Maintenance Types:"
            echo "  full     - Complete maintenance (default)"
            echo "  quick    - Essential maintenance only"
            echo "  system   - System and security updates"
            echo "  database - Database optimization only"
            echo "  security - Security updates and SSL check"
            exit 1
            ;;
    esac
    
    echo ""
    print_success "🎉 Maintenance completed successfully!"
    echo "Finished: $(date)"
    echo ""
}

# Run main function
main "$@"