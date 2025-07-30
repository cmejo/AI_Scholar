#!/bin/bash

# Advanced RAG Research Ecosystem - Health Check Script
# Comprehensive health monitoring for all services

set -e

# Configuration
DOMAIN=${DOMAIN:-"localhost"}
BACKEND_URL="http://backend:8000"
FRONTEND_URL="http://frontend:3000"
POSTGRES_HOST=${POSTGRES_HOST:-"postgres"}
REDIS_HOST=${REDIS_HOST:-"redis"}
CHROMADB_URL="http://chromadb:8000"

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

# Health check functions
check_backend() {
    print_status "Checking backend service..."
    
    if curl -f -s "$BACKEND_URL/health" > /dev/null; then
        print_success "Backend is healthy"
        return 0
    else
        print_error "Backend health check failed"
        return 1
    fi
}

check_frontend() {
    print_status "Checking frontend service..."
    
    if curl -f -s "$FRONTEND_URL/health" > /dev/null; then
        print_success "Frontend is healthy"
        return 0
    else
        print_error "Frontend health check failed"
        return 1
    fi
}

check_postgres() {
    print_status "Checking PostgreSQL database..."
    
    if docker-compose exec -T postgres pg_isready -h localhost -U rag_user > /dev/null 2>&1; then
        print_success "PostgreSQL is healthy"
        return 0
    else
        print_error "PostgreSQL health check failed"
        return 1
    fi
}

check_redis() {
    print_status "Checking Redis cache..."
    
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is healthy"
        return 0
    else
        print_error "Redis health check failed"
        return 1
    fi
}

check_chromadb() {
    print_status "Checking ChromaDB vector database..."
    
    if curl -f -s "$CHROMADB_URL/api/v1/heartbeat" > /dev/null; then
        print_success "ChromaDB is healthy"
        return 0
    else
        print_error "ChromaDB health check failed"
        return 1
    fi
}

check_nginx() {
    print_status "Checking Nginx reverse proxy..."
    
    if docker-compose exec -T nginx nginx -t > /dev/null 2>&1; then
        print_success "Nginx configuration is valid"
        return 0
    else
        print_error "Nginx configuration check failed"
        return 1
    fi
}

check_disk_space() {
    print_status "Checking disk space..."
    
    usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -lt 80 ]; then
        print_success "Disk space is healthy ($usage% used)"
        return 0
    elif [ "$usage" -lt 90 ]; then
        print_warning "Disk space is getting low ($usage% used)"
        return 0
    else
        print_error "Disk space is critically low ($usage% used)"
        return 1
    fi
}

check_memory() {
    print_status "Checking memory usage..."
    
    usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ "$usage" -lt 80 ]; then
        print_success "Memory usage is healthy ($usage% used)"
        return 0
    elif [ "$usage" -lt 90 ]; then
        print_warning "Memory usage is high ($usage% used)"
        return 0
    else
        print_error "Memory usage is critically high ($usage% used)"
        return 1
    fi
}

check_docker_containers() {
    print_status "Checking Docker containers..."
    
    failed_containers=$(docker-compose ps --services --filter "status=exited")
    
    if [ -z "$failed_containers" ]; then
        print_success "All Docker containers are running"
        return 0
    else
        print_error "Some containers have failed: $failed_containers"
        return 1
    fi
}

check_ssl_certificate() {
    if [ "$DOMAIN" != "localhost" ]; then
        print_status "Checking SSL certificate..."
        
        if openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" < /dev/null 2>/dev/null | openssl x509 -noout -dates > /dev/null 2>&1; then
            expiry=$(openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" < /dev/null 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
            expiry_epoch=$(date -d "$expiry" +%s)
            current_epoch=$(date +%s)
            days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
            
            if [ "$days_until_expiry" -gt 30 ]; then
                print_success "SSL certificate is valid (expires in $days_until_expiry days)"
                return 0
            elif [ "$days_until_expiry" -gt 7 ]; then
                print_warning "SSL certificate expires soon (in $days_until_expiry days)"
                return 0
            else
                print_error "SSL certificate expires very soon (in $days_until_expiry days)"
                return 1
            fi
        else
            print_error "SSL certificate check failed"
            return 1
        fi
    else
        print_status "Skipping SSL check for localhost"
        return 0
    fi
}

check_api_endpoints() {
    print_status "Checking critical API endpoints..."
    
    endpoints=(
        "/health"
        "/api/v1/research-memory/health"
        "/api/v1/personalization/health"
        "/api/v1/realtime/health"
    )
    
    failed_endpoints=0
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f -s "$BACKEND_URL$endpoint" > /dev/null; then
            print_success "Endpoint $endpoint is healthy"
        else
            print_error "Endpoint $endpoint failed"
            ((failed_endpoints++))
        fi
    done
    
    if [ "$failed_endpoints" -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

check_database_connections() {
    print_status "Checking database connection pool..."
    
    connections=$(docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" 2>/dev/null | xargs)
    
    if [ "$connections" -lt 50 ]; then
        print_success "Database connections are healthy ($connections active)"
        return 0
    elif [ "$connections" -lt 80 ]; then
        print_warning "Database connections are high ($connections active)"
        return 0
    else
        print_error "Database connections are critically high ($connections active)"
        return 1
    fi
}

# Main health check function
main() {
    echo ""
    echo "🏥 Advanced RAG Research Ecosystem - Health Check"
    echo "================================================"
    echo "Timestamp: $(date)"
    echo ""
    
    failed_checks=0
    total_checks=0
    
    # Run all health checks
    checks=(
        "check_docker_containers"
        "check_backend"
        "check_frontend"
        "check_postgres"
        "check_redis"
        "check_chromadb"
        "check_nginx"
        "check_disk_space"
        "check_memory"
        "check_ssl_certificate"
        "check_api_endpoints"
        "check_database_connections"
    )
    
    for check in "${checks[@]}"; do
        ((total_checks++))
        if ! $check; then
            ((failed_checks++))
        fi
        echo ""
    done
    
    # Summary
    echo "📊 Health Check Summary"
    echo "======================"
    echo "Total checks: $total_checks"
    echo "Passed: $((total_checks - failed_checks))"
    echo "Failed: $failed_checks"
    echo ""
    
    if [ "$failed_checks" -eq 0 ]; then
        print_success "🎉 All health checks passed! System is healthy."
        exit 0
    elif [ "$failed_checks" -lt 3 ]; then
        print_warning "⚠️  Some health checks failed, but system is mostly healthy."
        exit 1
    else
        print_error "❌ Multiple health checks failed. System needs attention."
        exit 2
    fi
}

# Parse command line arguments
case "${1:-all}" in
    "all")
        main
        ;;
    "backend")
        check_backend
        ;;
    "frontend")
        check_frontend
        ;;
    "database")
        check_postgres
        ;;
    "cache")
        check_redis
        ;;
    "vector")
        check_chromadb
        ;;
    "nginx")
        check_nginx
        ;;
    "system")
        check_disk_space
        check_memory
        ;;
    "ssl")
        check_ssl_certificate
        ;;
    *)
        echo "Usage: $0 {all|backend|frontend|database|cache|vector|nginx|system|ssl}"
        echo ""
        echo "Commands:"
        echo "  all       - Run all health checks (default)"
        echo "  backend   - Check backend API service"
        echo "  frontend  - Check frontend service"
        echo "  database  - Check PostgreSQL database"
        echo "  cache     - Check Redis cache"
        echo "  vector    - Check ChromaDB vector database"
        echo "  nginx     - Check Nginx configuration"
        echo "  system    - Check system resources"
        echo "  ssl       - Check SSL certificate"
        exit 1
        ;;
esac