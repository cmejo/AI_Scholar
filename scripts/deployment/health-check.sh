#!/bin/bash

# Comprehensive health check script for AI Scholar Advanced RAG
# Monitors all services and provides detailed health status

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

# Configuration
HEALTH_CHECK_TIMEOUT=30
DEPLOYMENT_DIR="/opt/ai-scholar"

# Health check functions
check_database() {
    print_status "Checking database health..."
    
    if docker-compose exec -T postgres pg_isready -U rag_user -d advanced_rag_db > /dev/null 2>&1; then
        # Check database connectivity and basic query
        if docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -c "SELECT 1;" > /dev/null 2>&1; then
            # Check database size and connections
            db_info=$(docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -t -c "
                SELECT 
                    pg_size_pretty(pg_database_size('advanced_rag_db')) as db_size,
                    (SELECT count(*) FROM pg_stat_activity WHERE datname = 'advanced_rag_db') as connections;
            ")
            print_success "Database: Healthy - $db_info"
            return 0
        fi
    fi
    
    print_error "Database: Unhealthy"
    return 1
}

check_redis() {
    print_status "Checking Redis health..."
    
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        # Check Redis memory usage
        memory_info=$(docker-compose exec -T redis redis-cli info memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
        print_success "Redis: Healthy - Memory used: $memory_info"
        return 0
    fi
    
    print_error "Redis: Unhealthy"
    return 1
}

check_chromadb() {
    print_status "Checking ChromaDB health..."
    
    if curl -f -s --max-time $HEALTH_CHECK_TIMEOUT "http://localhost:8080/api/v1/heartbeat" > /dev/null; then
        # Check ChromaDB collections
        collections=$(curl -s "http://localhost:8080/api/v1/collections" | jq -r '.length // 0' 2>/dev/null || echo "0")
        print_success "ChromaDB: Healthy - Collections: $collections"
        return 0
    fi
    
    print_error "ChromaDB: Unhealthy"
    return 1
}

check_backend() {
    local environment=${1:-}
    local port=${2:-8000}
    
    print_status "Checking backend health (${environment:-default})..."
    
    # Basic health check
    if curl -f -s --max-time $HEALTH_CHECK_TIMEOUT "http://localhost:$port/health" > /dev/null; then
        # Detailed health check
        health_data=$(curl -s --max-time $HEALTH_CHECK_TIMEOUT "http://localhost:$port/health" | jq -r '.' 2>/dev/null || echo "{}")
        
        # Check API endpoints
        if curl -f -s --max-time $HEALTH_CHECK_TIMEOUT "http://localhost:$port/api/health" > /dev/null; then
            print_success "Backend${environment:+ ($environment)}: Healthy"
            return 0
        fi
    fi
    
    print_error "Backend${environment:+ ($environment)}: Unhealthy"
    return 1
}

check_frontend() {
    local environment=${1:-}
    local port=${2:-3000}
    
    print_status "Checking frontend health (${environment:-default})..."
    
    if curl -f -s --max-time $HEALTH_CHECK_TIMEOUT "http://localhost:$port/health" > /dev/null; then
        # Check if main page loads
        if curl -f -s --max-time $HEALTH_CHECK_TIMEOUT "http://localhost:$port/" > /dev/null; then
            print_success "Frontend${environment:+ ($environment)}: Healthy"
            return 0
        fi
    fi
    
    print_error "Frontend${environment:+ ($environment)}: Unhealthy"
    return 1
}

check_nginx() {
    print_status "Checking Nginx health..."
    
    # Check if nginx is running
    if docker-compose ps nginx | grep -q "Up"; then
        # Check nginx configuration
        if docker-compose exec -T nginx nginx -t > /dev/null 2>&1; then
            # Check if nginx responds
            if curl -f -s --max-time $HEALTH_CHECK_TIMEOUT "http://localhost/health" > /dev/null; then
                print_success "Nginx: Healthy"
                return 0
            fi
        fi
    fi
    
    print_error "Nginx: Unhealthy"
    return 1
}

check_ssl_certificates() {
    print_status "Checking SSL certificates..."
    
    cert_file="/etc/nginx/ssl/fullchain.pem"
    
    if docker-compose exec -T nginx test -f "$cert_file"; then
        # Check certificate expiration
        expiry_date=$(docker-compose exec -T nginx openssl x509 -in "$cert_file" -noout -enddate | cut -d= -f2)
        expiry_timestamp=$(date -d "$expiry_date" +%s 2>/dev/null || echo "0")
        current_timestamp=$(date +%s)
        days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        if [ $days_until_expiry -gt 30 ]; then
            print_success "SSL Certificate: Valid (expires in $days_until_expiry days)"
            return 0
        elif [ $days_until_expiry -gt 0 ]; then
            print_warning "SSL Certificate: Expires soon ($days_until_expiry days)"
            return 0
        fi
    fi
    
    print_error "SSL Certificate: Invalid or expired"
    return 1
}

check_disk_space() {
    print_status "Checking disk space..."
    
    # Check available disk space
    available_space=$(df / | awk 'NR==2 {print $4}')
    available_gb=$((available_space / 1024 / 1024))
    
    if [ $available_gb -gt 5 ]; then
        print_success "Disk Space: Sufficient (${available_gb}GB available)"
        return 0
    elif [ $available_gb -gt 1 ]; then
        print_warning "Disk Space: Low (${available_gb}GB available)"
        return 0
    fi
    
    print_error "Disk Space: Critical (${available_gb}GB available)"
    return 1
}

check_memory_usage() {
    print_status "Checking memory usage..."
    
    # Check system memory
    memory_info=$(free -h | awk 'NR==2{printf "Used: %s/%s (%.1f%%)", $3, $2, $3/$2*100}')
    memory_percent=$(free | awk 'NR==2{printf "%.1f", $3/$2*100}')
    
    if (( $(echo "$memory_percent < 80" | bc -l) )); then
        print_success "Memory Usage: Normal ($memory_info)"
        return 0
    elif (( $(echo "$memory_percent < 90" | bc -l) )); then
        print_warning "Memory Usage: High ($memory_info)"
        return 0
    fi
    
    print_error "Memory Usage: Critical ($memory_info)"
    return 1
}

check_docker_health() {
    print_status "Checking Docker container health..."
    
    # Check all containers
    unhealthy_containers=$(docker ps --filter "health=unhealthy" --format "{{.Names}}" | wc -l)
    
    if [ $unhealthy_containers -eq 0 ]; then
        running_containers=$(docker ps --format "{{.Names}}" | wc -l)
        print_success "Docker Containers: All healthy ($running_containers running)"
        return 0
    fi
    
    print_error "Docker Containers: $unhealthy_containers unhealthy containers found"
    docker ps --filter "health=unhealthy" --format "table {{.Names}}\t{{.Status}}"
    return 1
}

check_blue_green_environments() {
    print_status "Checking blue-green deployment environments..."
    
    blue_status="down"
    green_status="down"
    
    # Check blue environment
    if docker-compose -f "$DEPLOYMENT_DIR/docker-compose.blue.yml" ps --services --filter status=running | grep -q "frontend\|backend"; then
        if check_backend "blue" 8002 && check_frontend "blue" 3002; then
            blue_status="healthy"
        else
            blue_status="unhealthy"
        fi
    fi
    
    # Check green environment
    if docker-compose -f "$DEPLOYMENT_DIR/docker-compose.green.yml" ps --services --filter status=running | grep -q "frontend\|backend"; then
        if check_backend "green" 8003 && check_frontend "green" 3003; then
            green_status="healthy"
        else
            green_status="unhealthy"
        fi
    fi
    
    print_status "Blue environment: $blue_status"
    print_status "Green environment: $green_status"
    
    if [ "$blue_status" = "healthy" ] || [ "$green_status" = "healthy" ]; then
        return 0
    fi
    
    return 1
}

# Comprehensive health check
comprehensive_health_check() {
    local failed_checks=0
    local total_checks=0
    
    echo ""
    echo "🏥 AI Scholar Advanced RAG - Health Check"
    echo "========================================"
    echo "Started: $(date)"
    echo ""
    
    # Core infrastructure checks
    echo "📊 Core Infrastructure"
    echo "---------------------"
    
    ((total_checks++))
    if ! check_database; then ((failed_checks++)); fi
    
    ((total_checks++))
    if ! check_redis; then ((failed_checks++)); fi
    
    ((total_checks++))
    if ! check_chromadb; then ((failed_checks++)); fi
    
    echo ""
    
    # Application checks
    echo "🚀 Application Services"
    echo "----------------------"
    
    ((total_checks++))
    if ! check_nginx; then ((failed_checks++)); fi
    
    # Check blue-green environments
    ((total_checks++))
    if ! check_blue_green_environments; then ((failed_checks++)); fi
    
    echo ""
    
    # System resource checks
    echo "💻 System Resources"
    echo "------------------"
    
    ((total_checks++))
    if ! check_disk_space; then ((failed_checks++)); fi
    
    ((total_checks++))
    if ! check_memory_usage; then ((failed_checks++)); fi
    
    ((total_checks++))
    if ! check_docker_health; then ((failed_checks++)); fi
    
    echo ""
    
    # Security checks
    echo "🔒 Security"
    echo "----------"
    
    ((total_checks++))
    if ! check_ssl_certificates; then ((failed_checks++)); fi
    
    echo ""
    
    # Summary
    echo "📋 Health Check Summary"
    echo "======================"
    echo "Total checks: $total_checks"
    echo "Passed: $((total_checks - failed_checks))"
    echo "Failed: $failed_checks"
    
    if [ $failed_checks -eq 0 ]; then
        print_success "🎉 All health checks passed!"
        echo "System Status: HEALTHY"
        return 0
    elif [ $failed_checks -le 2 ]; then
        print_warning "⚠️  Some health checks failed"
        echo "System Status: DEGRADED"
        return 1
    else
        print_error "🚨 Multiple health checks failed"
        echo "System Status: UNHEALTHY"
        return 2
    fi
}

# Quick health check
quick_health_check() {
    echo "🔍 Quick Health Check"
    echo "===================="
    
    # Check only critical services
    if check_database && check_redis && check_nginx; then
        print_success "✅ Critical services are healthy"
        return 0
    else
        print_error "❌ Critical services have issues"
        return 1
    fi
}

# Monitoring endpoint health check
monitoring_health_check() {
    print_status "Checking monitoring endpoints..."
    
    # Check Prometheus
    if curl -f -s --max-time $HEALTH_CHECK_TIMEOUT "http://localhost:9090/-/healthy" > /dev/null; then
        print_success "Prometheus: Healthy"
    else
        print_warning "Prometheus: Unavailable"
    fi
    
    # Check Grafana
    if curl -f -s --max-time $HEALTH_CHECK_TIMEOUT "http://localhost:3001/api/health" > /dev/null; then
        print_success "Grafana: Healthy"
    else
        print_warning "Grafana: Unavailable"
    fi
}

# Main function
main() {
    local check_type=${1:-comprehensive}
    
    case "$check_type" in
        "comprehensive"|"full")
            comprehensive_health_check
            ;;
        "quick"|"basic")
            quick_health_check
            ;;
        "monitoring")
            monitoring_health_check
            ;;
        "database")
            check_database
            ;;
        "redis")
            check_redis
            ;;
        "backend")
            check_backend
            ;;
        "frontend")
            check_frontend
            ;;
        "nginx")
            check_nginx
            ;;
        "blue-green")
            check_blue_green_environments
            ;;
        *)
            echo "Usage: $0 {comprehensive|quick|monitoring|database|redis|backend|frontend|nginx|blue-green}"
            echo ""
            echo "Health Check Types:"
            echo "  comprehensive - Full system health check (default)"
            echo "  quick         - Quick check of critical services"
            echo "  monitoring    - Check monitoring services"
            echo "  database      - Check database only"
            echo "  redis         - Check Redis only"
            echo "  backend       - Check backend API only"
            echo "  frontend      - Check frontend only"
            echo "  nginx         - Check Nginx only"
            echo "  blue-green    - Check blue-green environments"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"