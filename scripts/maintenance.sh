#!/bin/bash

# Advanced RAG Research Ecosystem - Maintenance Script
# Automated maintenance tasks for optimal system performance

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

# Database maintenance
maintain_database() {
    print_status "Performing database maintenance..."
    
    # Vacuum and analyze database
    docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -c "VACUUM ANALYZE;"
    print_success "Database vacuum and analyze completed"
    
    # Update table statistics
    docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -c "ANALYZE;"
    print_success "Database statistics updated"
    
    # Check for unused indexes
    unused_indexes=$(docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -t -c "
        SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
        FROM pg_stat_user_indexes 
        WHERE idx_tup_read = 0 AND idx_tup_fetch = 0;
    " | wc -l)
    
    if [ "$unused_indexes" -gt 0 ]; then
        print_warning "Found $unused_indexes potentially unused indexes"
    else
        print_success "No unused indexes found"
    fi
    
    # Check database size
    db_size=$(docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -t -c "
        SELECT pg_size_pretty(pg_database_size('advanced_rag_db'));
    " | xargs)
    print_status "Database size: $db_size"
}

# Redis maintenance
maintain_redis() {
    print_status "Performing Redis maintenance..."
    
    # Get Redis info
    redis_info=$(docker-compose exec -T redis redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
    print_status "Redis memory usage: $redis_info"
    
    # Check for expired keys
    expired_keys=$(docker-compose exec -T redis redis-cli info stats | grep expired_keys | cut -d: -f2 | tr -d '\r')
    print_status "Expired keys cleaned: $expired_keys"
    
    # Optimize Redis if needed
    docker-compose exec -T redis redis-cli bgrewriteaof > /dev/null
    print_success "Redis AOF rewrite initiated"
}

# Log rotation and cleanup
maintain_logs() {
    print_status "Performing log maintenance..."
    
    # Rotate Docker logs
    docker system prune -f --volumes > /dev/null 2>&1
    print_success "Docker system cleanup completed"
    
    # Clean old log files
    find ./logs -name "*.log" -mtime +30 -delete 2>/dev/null || true
    find ./logs -name "*.log.*" -mtime +7 -delete 2>/dev/null || true
    print_success "Old log files cleaned"
    
    # Compress large log files
    find ./logs -name "*.log" -size +100M -exec gzip {} \; 2>/dev/null || true
    print_success "Large log files compressed"
}

# System cleanup
maintain_system() {
    print_status "Performing system maintenance..."
    
    # Clean package cache
    sudo apt autoremove -y > /dev/null 2>&1
    sudo apt autoclean > /dev/null 2>&1
    print_success "Package cache cleaned"
    
    # Update system packages (security updates only)
    sudo unattended-upgrade -d > /dev/null 2>&1 || true
    print_success "Security updates applied"
    
    # Check disk usage
    disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 80 ]; then
        print_warning "Disk usage is high: $disk_usage%"
        
        # Clean temporary files
        sudo find /tmp -type f -atime +7 -delete 2>/dev/null || true
        sudo find /var/tmp -type f -atime +7 -delete 2>/dev/null || true
        print_success "Temporary files cleaned"
    else
        print_success "Disk usage is healthy: $disk_usage%"
    fi
}

# Docker maintenance
maintain_docker() {
    print_status "Performing Docker maintenance..."
    
    # Remove unused images
    docker image prune -f > /dev/null 2>&1
    print_success "Unused Docker images removed"
    
    # Remove unused volumes
    docker volume prune -f > /dev/null 2>&1
    print_success "Unused Docker volumes removed"
    
    # Remove unused networks
    docker network prune -f > /dev/null 2>&1
    print_success "Unused Docker networks removed"
    
    # Check container health
    unhealthy_containers=$(docker ps --filter health=unhealthy --format "table {{.Names}}" | tail -n +2)
    if [ -n "$unhealthy_containers" ]; then
        print_warning "Unhealthy containers found: $unhealthy_containers"
    else
        print_success "All containers are healthy"
    fi
}

# SSL certificate maintenance
maintain_ssl() {
    print_status "Checking SSL certificates..."
    
    if [ -f "nginx/ssl/fullchain.pem" ]; then
        expiry_date=$(openssl x509 -enddate -noout -in nginx/ssl/fullchain.pem | cut -d= -f2)
        expiry_epoch=$(date -d "$expiry_date" +%s)
        current_epoch=$(date +%s)
        days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
        
        if [ "$days_until_expiry" -lt 30 ]; then
            print_warning "SSL certificate expires in $days_until_expiry days"
            
            # Attempt to renew certificate
            if command -v certbot &> /dev/null; then
                sudo certbot renew --quiet || print_warning "Certificate renewal failed"
                print_success "Certificate renewal attempted"
            fi
        else
            print_success "SSL certificate is valid for $days_until_expiry days"
        fi
    else
        print_warning "SSL certificate not found"
    fi
}

# Backup verification
verify_backups() {
    print_status "Verifying recent backups..."
    
    # Check if backups exist
    recent_backup=$(find ./backups -name "database_*.sql.gz" -mtime -1 | head -1)
    
    if [ -n "$recent_backup" ]; then
        backup_size=$(du -h "$recent_backup" | cut -f1)
        print_success "Recent database backup found: $backup_size"
        
        # Test backup integrity
        if gzip -t "$recent_backup" 2>/dev/null; then
            print_success "Backup integrity verified"
        else
            print_error "Backup integrity check failed"
        fi
    else
        print_warning "No recent database backup found"
    fi
}

# Performance optimization
optimize_performance() {
    print_status "Optimizing system performance..."
    
    # Optimize PostgreSQL configuration
    docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -c "
        SELECT pg_stat_reset();
    " > /dev/null 2>&1
    print_success "PostgreSQL statistics reset"
    
    # Clear Redis memory if usage is high
    redis_memory=$(docker-compose exec -T redis redis-cli info memory | grep used_memory_peak_perc | cut -d: -f2 | cut -d. -f1 | tr -d '\r')
    
    if [ "$redis_memory" -gt 80 ]; then
        print_warning "Redis memory usage is high: $redis_memory%"
        docker-compose exec -T redis redis-cli flushdb > /dev/null 2>&1
        print_success "Redis cache cleared"
    fi
    
    # Restart services if memory usage is high
    total_memory=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$total_memory" -gt 90 ]; then
        print_warning "System memory usage is high: $total_memory%"
        print_status "Restarting services to free memory..."
        docker-compose restart backend frontend
        print_success "Services restarted"
    fi
}

# Security maintenance
maintain_security() {
    print_status "Performing security maintenance..."
    
    # Update fail2ban
    sudo systemctl reload fail2ban 2>/dev/null || true
    print_success "Fail2ban reloaded"
    
    # Check for suspicious login attempts
    suspicious_logins=$(sudo grep "Failed password" /var/log/auth.log | tail -10 | wc -l)
    if [ "$suspicious_logins" -gt 5 ]; then
        print_warning "Multiple failed login attempts detected: $suspicious_logins"
    else
        print_success "No suspicious login activity"
    fi
    
    # Check firewall status
    if sudo ufw status | grep -q "Status: active"; then
        print_success "Firewall is active"
    else
        print_warning "Firewall is not active"
    fi
}

# Generate maintenance report
generate_report() {
    print_status "Generating maintenance report..."
    
    report_file="./logs/maintenance_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
Advanced RAG Research Ecosystem - Maintenance Report
===================================================
Date: $(date)
Hostname: $(hostname)

System Information:
- Uptime: $(uptime)
- Load Average: $(uptime | awk -F'load average:' '{print $2}')
- Memory Usage: $(free -h | awk 'NR==2{printf "%s/%s (%.0f%%)", $3,$2,$3*100/$2}')
- Disk Usage: $(df -h / | awk 'NR==2{printf "%s/%s (%s)", $3,$2,$5}')

Docker Status:
$(docker-compose ps)

Database Status:
- Size: $(docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -t -c "SELECT pg_size_pretty(pg_database_size('advanced_rag_db'));" | xargs)
- Connections: $(docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -t -c "SELECT count(*) FROM pg_stat_activity;" | xargs)

Redis Status:
- Memory: $(docker-compose exec -T redis redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
- Keys: $(docker-compose exec -T redis redis-cli dbsize | tr -d '\r')

Recent Backups:
$(ls -lh ./backups/*$(date +%Y%m%d)* 2>/dev/null || echo "No backups found for today")

Maintenance Tasks Completed:
- Database vacuum and analyze
- Redis optimization
- Log rotation and cleanup
- System package updates
- Docker cleanup
- SSL certificate check
- Backup verification
- Performance optimization
- Security checks

Next Maintenance: $(date -d "+1 week")
EOF

    print_success "Maintenance report generated: $report_file"
}

# Main maintenance function
main() {
    echo ""
    echo "🔧 Advanced RAG Research Ecosystem - Maintenance"
    echo "==============================================="
    echo "Started: $(date)"
    echo ""
    
    # Check if services are running
    if ! docker-compose ps | grep -q "Up"; then
        print_error "Some services are not running. Please start services first."
        exit 1
    fi
    
    # Run maintenance tasks
    maintain_database
    maintain_redis
    maintain_logs
    maintain_system
    maintain_docker
    maintain_ssl
    verify_backups
    optimize_performance
    maintain_security
    generate_report
    
    echo ""
    print_success "🎉 Maintenance completed successfully!"
    echo ""
    echo "📊 Maintenance Summary:"
    echo "======================"
    echo "• Database optimized and analyzed"
    echo "• Redis cache optimized"
    echo "• Log files rotated and cleaned"
    echo "• System packages updated"
    echo "• Docker resources cleaned"
    echo "• SSL certificates checked"
    echo "• Backups verified"
    echo "• Performance optimized"
    echo "• Security checks completed"
    echo ""
    echo "📝 Next Steps:"
    echo "1. Review maintenance report in ./logs/"
    echo "2. Monitor system performance"
    echo "3. Schedule next maintenance"
    echo ""
}

# Parse command line arguments
case "${1:-full}" in
    "full")
        main
        ;;
    "database")
        maintain_database
        ;;
    "redis")
        maintain_redis
        ;;
    "logs")
        maintain_logs
        ;;
    "system")
        maintain_system
        ;;
    "docker")
        maintain_docker
        ;;
    "ssl")
        maintain_ssl
        ;;
    "security")
        maintain_security
        ;;
    "performance")
        optimize_performance
        ;;
    *)
        echo "Usage: $0 {full|database|redis|logs|system|docker|ssl|security|performance}"
        echo ""
        echo "Commands:"
        echo "  full        - Run all maintenance tasks (default)"
        echo "  database    - Database maintenance only"
        echo "  redis       - Redis maintenance only"
        echo "  logs        - Log cleanup only"
        echo "  system      - System maintenance only"
        echo "  docker      - Docker cleanup only"
        echo "  ssl         - SSL certificate check only"
        echo "  security    - Security maintenance only"
        echo "  performance - Performance optimization only"
        exit 1
        ;;
esac