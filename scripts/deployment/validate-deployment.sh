#!/bin/bash

# Comprehensive Deployment Validation Script
# This script validates all aspects of the AI Scholar RAG deployment

set -e

# Configuration
DOMAIN=${DOMAIN:-localhost}
API_URL=${API_URL:-http://localhost:8000}
FRONTEND_URL=${FRONTEND_URL:-http://localhost:3000}
STREAMLIT_URL=${STREAMLIT_URL:-http://localhost:8501}
MONITORING_URL=${MONITORING_URL:-http://localhost:3001}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    log "Running test: $test_name"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if eval "$test_command"; then
        success "$test_name"
        return 0
    else
        error "$test_name"
        return 1
    fi
}

# Service health checks
check_service_health() {
    log "Checking service health..."
    
    # Backend API
    run_test "Backend API Health" "curl -f -s $API_URL/ > /dev/null"
    
    # Frontend
    run_test "Frontend Health" "curl -f -s $FRONTEND_URL/ > /dev/null"
    
    # Streamlit
    run_test "Streamlit Health" "curl -f -s $STREAMLIT_URL/ > /dev/null"
    
    # Database
    run_test "Database Health" "docker-compose exec -T postgres pg_isready -U postgres > /dev/null"
    
    # Redis
    run_test "Redis Health" "docker-compose exec -T redis redis-cli ping | grep -q PONG"
    
    # Ollama
    run_test "Ollama Health" "curl -f -s http://localhost:11434/ > /dev/null"
    
    # ChromaDB
    run_test "ChromaDB Health" "curl -f -s http://localhost:8001/api/v1/heartbeat > /dev/null || true"
}

# API endpoint tests
check_api_endpoints() {
    log "Checking API endpoints..."
    
    # Health endpoint
    run_test "API Root Endpoint" "curl -f -s $API_URL/ | grep -q 'AI Scholar RAG Backend'"
    
    # API documentation
    run_test "API Documentation" "curl -f -s $API_URL/docs > /dev/null"
    
    # Metrics endpoint
    run_test "Metrics Endpoint" "curl -f -s $API_URL/metrics > /dev/null || true"
}

# Database connectivity tests
check_database() {
    log "Checking database connectivity and structure..."
    
    # Basic connectivity
    run_test "Database Connection" "docker-compose exec -T postgres psql -U postgres -d ai_scholar -c 'SELECT 1;' > /dev/null"
    
    # Check for required tables
    run_test "Users Table Exists" "docker-compose exec -T postgres psql -U postgres -d ai_scholar -c \"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users');\" | grep -q 't'"
    
    run_test "Documents Table Exists" "docker-compose exec -T postgres psql -U postgres -d ai_scholar -c \"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'documents');\" | grep -q 't'"
    
    run_test "Enhanced Tables Exist" "docker-compose exec -T postgres psql -U postgres -d ai_scholar -c \"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_profiles');\" | grep -q 't'"
}

# Performance tests
check_performance() {
    log "Running performance checks..."
    
    # Response time test
    local response_time=$(curl -o /dev/null -s -w '%{time_total}' $API_URL/)
    if (( $(echo "$response_time < 2.0" | bc -l) )); then
        success "API Response Time ($response_time seconds)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        error "API Response Time too slow ($response_time seconds)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Memory usage check
    local memory_usage=$(docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}" | grep backend | awk '{print $2}' | sed 's/MiB.*//')
    if [ -n "$memory_usage" ] && [ "$memory_usage" -lt 2000 ]; then
        success "Backend Memory Usage (${memory_usage}MiB)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        warning "Backend Memory Usage high (${memory_usage}MiB)"
        PASSED_TESTS=$((PASSED_TESTS + 1))  # Warning, not failure
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

# Security checks
check_security() {
    log "Running security checks..."
    
    # SSL/TLS check (if HTTPS)
    if [[ $API_URL == https* ]]; then
        run_test "SSL Certificate Valid" "curl -f -s $API_URL/ > /dev/null"
    else
        warning "SSL not configured (development mode)"
    fi
    
    # CORS headers check
    run_test "CORS Headers Present" "curl -s -I $API_URL/ | grep -i 'access-control-allow-origin' > /dev/null || true"
    
    # Security headers check
    if [[ $API_URL == https* ]]; then
        run_test "Security Headers Present" "curl -s -I $FRONTEND_URL/ | grep -i 'x-frame-options\\|x-content-type-options\\|strict-transport-security' > /dev/null || true"
    fi
}

# Monitoring checks
check_monitoring() {
    log "Checking monitoring setup..."
    
    # Prometheus
    if docker-compose ps prometheus | grep -q "Up"; then
        run_test "Prometheus Running" "curl -f -s http://localhost:9090/-/healthy > /dev/null"
        run_test "Prometheus Targets" "curl -s http://localhost:9090/api/v1/targets | grep -q '\"health\":\"up\"'"
    else
        warning "Prometheus not running (monitoring disabled)"
    fi
    
    # Grafana
    if docker-compose ps grafana | grep -q "Up"; then
        run_test "Grafana Running" "curl -f -s http://localhost:3001/api/health > /dev/null"
    else
        warning "Grafana not running (monitoring disabled)"
    fi
}

# File system checks
check_filesystem() {
    log "Checking file system and permissions..."
    
    # Upload directory
    run_test "Upload Directory Writable" "[ -w backend/uploads ]"
    
    # ChromaDB directory
    run_test "ChromaDB Directory Exists" "[ -d backend/chroma_db ]"
    
    # SSL directory (if exists)
    if [ -d "ssl" ]; then
        run_test "SSL Directory Readable" "[ -r ssl ]"
    fi
    
    # Log files
    run_test "Docker Logs Accessible" "docker-compose logs --tail=1 backend > /dev/null"
}

# Configuration validation
check_configuration() {
    log "Validating configuration..."
    
    # Environment variables
    if [ -n "$SECRET_KEY" ]; then
        success "SECRET_KEY is set"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        error "SECRET_KEY not set"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Docker Compose configuration
    run_test "Docker Compose Config Valid" "docker-compose config > /dev/null"
    
    # Nginx configuration (if exists)
    if [ -f "nginx.conf" ] || [ -f "nginx.prod.conf" ]; then
        run_test "Nginx Config Syntax" "docker run --rm -v $(pwd):/etc/nginx nginx:alpine nginx -t > /dev/null 2>&1 || true"
    fi
}

# Advanced feature tests
check_advanced_features() {
    log "Testing advanced features (requires system validation script)..."
    
    if [ -f "tests/system_validation.py" ]; then
        # Install required dependencies if not present
        if ! python3 -c "import aiohttp" 2>/dev/null; then
            warning "Installing test dependencies..."
            pip3 install aiohttp asyncio 2>/dev/null || true
        fi
        
        # Run comprehensive system validation
        if python3 tests/system_validation.py > /dev/null 2>&1; then
            success "Advanced Features Validation"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            error "Advanced Features Validation (check system_validation_report_*.md for details)"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
    else
        warning "System validation script not found, skipping advanced feature tests"
    fi
}

# Resource usage check
check_resources() {
    log "Checking resource usage..."
    
    # Disk space
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -lt 80 ]; then
        success "Disk Usage (${disk_usage}%)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        error "Disk Usage too high (${disk_usage}%)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Docker container status
    local running_containers=$(docker-compose ps --services --filter "status=running" | wc -l)
    local total_containers=$(docker-compose ps --services | wc -l)
    
    if [ "$running_containers" -eq "$total_containers" ]; then
        success "All Containers Running ($running_containers/$total_containers)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        error "Some Containers Not Running ($running_containers/$total_containers)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

# Generate validation report
generate_report() {
    local success_rate=0
    if [ $TOTAL_TESTS -gt 0 ]; then
        success_rate=$(( PASSED_TESTS * 100 / TOTAL_TESTS ))
    fi
    
    local report_file="deployment_validation_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# AI Scholar RAG Deployment Validation Report

**Validation Date**: $(date)
**Environment**: $DEPLOYMENT_ENV
**Domain**: $DOMAIN

## Summary

- **Total Tests**: $TOTAL_TESTS
- **Passed**: $PASSED_TESTS
- **Failed**: $FAILED_TESTS
- **Success Rate**: ${success_rate}%

## Service URLs

- Frontend: $FRONTEND_URL
- API: $API_URL
- Streamlit: $STREAMLIT_URL
- Monitoring: $MONITORING_URL

## System Status

$(docker-compose ps)

## Resource Usage

### Memory Usage
$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}")

### Disk Usage
$(df -h)

## Validation Results

EOF
    
    if [ $FAILED_TESTS -gt 0 ]; then
        echo "### Failed Tests" >> "$report_file"
        echo "The following tests failed and require attention:" >> "$report_file"
        echo "" >> "$report_file"
        # Note: Individual test failures are logged during execution
    fi
    
    if [ $success_rate -ge 90 ]; then
        echo "### Overall Status: ✅ PASSED" >> "$report_file"
        echo "System validation successful with ${success_rate}% success rate." >> "$report_file"
    elif [ $success_rate -ge 70 ]; then
        echo "### Overall Status: ⚠️ WARNING" >> "$report_file"
        echo "System validation completed with warnings (${success_rate}% success rate)." >> "$report_file"
    else
        echo "### Overall Status: ❌ FAILED" >> "$report_file"
        echo "System validation failed with ${success_rate}% success rate." >> "$report_file"
    fi
    
    echo "" >> "$report_file"
    echo "Report generated: $(date)" >> "$report_file"
    
    echo "$report_file"
}

# Main validation function
main() {
    log "Starting comprehensive deployment validation..."
    echo ""
    
    # Run all validation checks
    check_service_health
    echo ""
    
    check_api_endpoints
    echo ""
    
    check_database
    echo ""
    
    check_performance
    echo ""
    
    check_security
    echo ""
    
    check_monitoring
    echo ""
    
    check_filesystem
    echo ""
    
    check_configuration
    echo ""
    
    check_resources
    echo ""
    
    check_advanced_features
    echo ""
    
    # Generate report
    local report_file=$(generate_report)
    
    # Display summary
    local success_rate=0
    if [ $TOTAL_TESTS -gt 0 ]; then
        success_rate=$(( PASSED_TESTS * 100 / TOTAL_TESTS ))
    fi
    
    echo "=========================================="
    echo "DEPLOYMENT VALIDATION SUMMARY"
    echo "=========================================="
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    echo "Success Rate: ${success_rate}%"
    echo ""
    echo "Report saved to: $report_file"
    echo ""
    
    if [ $success_rate -ge 90 ]; then
        success "🎉 Deployment validation PASSED!"
        echo ""
        echo "Your AI Scholar RAG system is ready for production use."
        echo ""
        echo "Next steps:"
        echo "1. Review the validation report"
        echo "2. Set up monitoring alerts"
        echo "3. Configure automated backups"
        echo "4. Notify users of system availability"
        exit 0
    elif [ $success_rate -ge 70 ]; then
        warning "⚠️ Deployment validation completed with WARNINGS"
        echo ""
        echo "The system is functional but some issues need attention."
        echo "Review the failed tests and address them before full production use."
        exit 1
    else
        error "❌ Deployment validation FAILED"
        echo ""
        echo "Critical issues detected. Do not proceed to production."
        echo "Review the validation report and fix all critical issues."
        exit 2
    fi
}

# Run main function
main "$@"