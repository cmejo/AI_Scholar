#!/bin/bash

# Comprehensive Health Check Script for Zotero Integration
# Performs deep health checks on all Zotero integration components

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-production}"
CHECK_TYPE="${2:-all}"  # all, basic, deep, external

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Health check results
HEALTH_RESULTS=()
FAILED_CHECKS=0
TOTAL_CHECKS=0

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

# Record health check result
record_check() {
    local check_name="$1"
    local status="$2"
    local message="$3"
    local duration="${4:-0}"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [[ "$status" == "PASS" ]]; then
        success "✓ $check_name: $message (${duration}ms)"
    elif [[ "$status" == "WARN" ]]; then
        warning "⚠ $check_name: $message (${duration}ms)"
    else
        error "✗ $check_name: $message (${duration}ms)"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
    
    HEALTH_RESULTS+=("$check_name|$status|$message|$duration")
}

# Load environment configuration
load_environment() {
    local env_file="${PROJECT_ROOT}/.env.${ENVIRONMENT}"
    
    if [[ -f "$env_file" ]]; then
        source "$env_file"
    fi
    
    # Load deployment-specific configuration
    local deploy_env_file="${PROJECT_ROOT}/config/deployment/${ENVIRONMENT}.env"
    if [[ -f "$deploy_env_file" ]]; then
        source "$deploy_env_file"
    fi
}

# Check database connectivity and health
check_database() {
    log "Checking database health..."
    
    local start_time=$(date +%s%3N)
    
    # Basic connectivity
    if pg_isready -h "${DB_HOST}" -p "${DB_PORT:-5432}" -U "${DB_USER}" &> /dev/null; then
        local end_time=$(date +%s%3N)
        local duration=$((end_time - start_time))
        record_check "Database Connectivity" "PASS" "Database is reachable" "$duration"
    else
        local end_time=$(date +%s%3N)
        local duration=$((end_time - start_time))
        record_check "Database Connectivity" "FAIL" "Cannot reach database" "$duration"
        return 1
    fi
    
    # Authentication test
    start_time=$(date +%s%3N)
    if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT:-5432}" -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT 1;" &> /dev/null; then
        end_time=$(date +%s%3N)
        duration=$((end_time - start_time))
        record_check "Database Authentication" "PASS" "Authentication successful" "$duration"
    else
        end_time=$(date +%s%3N)
        duration=$((end_time - start_time))
        record_check "Database Authentication" "FAIL" "Authentication failed" "$duration"
        return 1
    fi
    
    # Schema validation
    start_time=$(date +%s%3N)
    local table_count=$(PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT:-5432}" -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'zotero';" 2>/dev/null | xargs)
    
    if [[ "$table_count" -ge 5 ]]; then
        end_time=$(date +%s%3N)
        duration=$((end_time - start_time))
        record_check "Database Schema" "PASS" "Zotero schema has $table_count tables" "$duration"
    else
        end_time=$(date +%s%3N)
        duration=$((end_time - start_time))
        record_check "Database Schema" "FAIL" "Zotero schema incomplete ($table_count tables)" "$duration"
    fi
    
    # Connection pool health
    start_time=$(date +%s%3N)
    local active_connections=$(PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT:-5432}" -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" 2>/dev/null | xargs)
    
    if [[ "$active_connections" -lt 50 ]]; then
        end_time=$(date +%s%3N)
        duration=$((end_time - start_time))
        record_check "Database Connections" "PASS" "$active_connections active connections" "$duration"
    else
        end_time=$(date +%s%3N)
        duration=$((end_time - start_time))
        record_check "Database Connections" "WARN" "High connection count: $active_connections" "$duration"
    fi
}

# Check Redis connectivity and health
check_redis() {
    log "Checking Redis health..."
    
    local start_time=$(date +%s%3N)
    
    # Basic connectivity
    if redis-cli -u "${REDIS_URL}" ping &> /dev/null; then
        local end_time=$(date +%s%3N)
        local duration=$((end_time - start_time))
        record_check "Redis Connectivity" "PASS" "Redis is reachable" "$duration"
    else
        local end_time=$(date +%s%3N)
        local duration=$((end_time - start_time))
        record_check "Redis Connectivity" "FAIL" "Cannot reach Redis" "$duration"
        return 1
    fi
    
    # Memory usage check
    start_time=$(date +%s%3N)
    local memory_info=$(redis-cli -u "${REDIS_URL}" info memory 2>/dev/null | grep used_memory_human | cut -d: -f2 | tr -d '\r')
    
    if [[ -n "$memory_info" ]]; then
        end_time=$(date +%s%3N)
        duration=$((end_time - start_time))
        record_check "Redis Memory" "PASS" "Memory usage: $memory_info" "$duration"
    else
        end_time=$(date +%s%3N)
        duration=$((end_time - start_time))
        record_check "Redis Memory" "WARN" "Cannot retrieve memory info" "$duration"
    fi
    
    # Key count check
    start_time=$(date +%s%3N)
    local key_count=$(redis-cli -u "${REDIS_URL}" dbsize 2>/dev/null)
    
    if [[ -n "$key_count" ]]; then
        end_time=$(date +%s%3N)
        duration=$((end_time - start_time))
        record_check "Redis Keys" "PASS" "$key_count keys in database" "$duration"
    else
        end_time=$(date +%s%3N)
        duration=$((end_time - start_time))
        record_check "Redis Keys" "WARN" "Cannot retrieve key count" "$duration"
    fi
}

# Check API endpoints
check_api_endpoints() {
    log "Checking API endpoints..."
    
    local base_url="${API_BASE_URL:-http://localhost:8000}"
    local endpoints=(
        "/health"
        "/health/zotero"
        "/health/zotero/database"
        "/health/zotero/sync"
        "/api/zotero/status"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local start_time=$(date +%s%3N)
        local url="${base_url}${endpoint}"
        
        if curl -f -s --max-time 10 "$url" &> /dev/null; then
            local end_time=$(date +%s%3N)
            local duration=$((end_time - start_time))
            record_check "API Endpoint $endpoint" "PASS" "Endpoint responding" "$duration"
        else
            local end_time=$(date +%s%3N)
            local duration=$((end_time - start_time))
            record_check "API Endpoint $endpoint" "FAIL" "Endpoint not responding" "$duration"
        fi
    done
}

# Check external services
check_external_services() {
    log "Checking external services..."
    
    # Zotero API
    local start_time=$(date +%s%3N)
    if curl -f -s --max-time 10 "https://api.zotero.org/users/1/items?limit=1" &> /dev/null; then
        local end_time=$(date +%s%3N)
        local duration=$((end_time - start_time))
        record_check "Zotero API" "PASS" "Zotero API is accessible" "$duration"
    else
        local end_time=$(date +%s%3N)
        local duration=$((end_time - start_time))
        record_check "Zotero API" "FAIL" "Zotero API not accessible" "$duration"
    fi
    
    # OpenAI API (if configured)
    if [[ -n "${OPENAI_API_KEY:-}" ]]; then
        start_time=$(date +%s%3N)
        if curl -f -s --max-time 10 -H "Authorization: Bearer ${OPENAI_API_KEY}" "https://api.openai.com/v1/models" &> /dev/null; then
            end_time=$(date +%s%3N)
            duration=$((end_time - start_time))
            record_check "OpenAI API" "PASS" "OpenAI API is accessible" "$duration"
        else
            end_time=$(date +%s%3N)
            duration=$((end_time - start_time))
            record_check "OpenAI API" "WARN" "OpenAI API not accessible" "$duration"
        fi
    fi
}

# Check file system and storage
check_storage() {
    log "Checking storage and file system..."
    
    # Check attachment directory
    local attachment_dir="${ZOTERO_ATTACHMENT_PATH:-./backend/zotero_attachments}"
    local start_time=$(date +%s%3N)
    
    if [[ -d "$attachment_dir" ]] && [[ -w "$attachment_dir" ]]; then
        local end_time=$(date +%s%3N)
        local duration=$((end_time - start_time))
        local size=$(du -sh "$attachment_dir" 2>/dev/null | cut -f1)
        record_check "Attachment Storage" "PASS" "Directory accessible, size: $size" "$duration"
    else
        local end_time=$(date +%s%3N)
        local duration=$((end_time - start_time))
        record_check "Attachment Storage" "FAIL" "Directory not accessible or writable" "$duration"
    fi
    
    # Check disk space
    start_time=$(date +%s%3N)
    local available_space=$(df "${PROJECT_ROOT}" | awk 'NR==2 {print $4}')
    local available_gb=$((available_space / 1024 / 1024))
    
    if [[ $available_gb -gt 5 ]]; then
        end_time=$(date +%s%3N)
        duration=$((end_time - start_time))
        record_check "Disk Space" "PASS" "${available_gb}GB available" "$duration"
    elif [[ $available_gb -gt 1 ]]; then
        end_time=$(date +%s%3N)
        duration=$((end_time - start_time))
        record_check "Disk Space" "WARN" "Low disk space: ${available_gb}GB available" "$duration"
    else
        end_time=$(date +%s%3N)
        duration=$((end_time - start_time))
        record_check "Disk Space" "FAIL" "Critical disk space: ${available_gb}GB available" "$duration"
    fi
    
    # Check log directory
    start_time=$(date +%s%3N)
    local log_dir="${PROJECT_ROOT}/backend/logs"
    
    if [[ -d "$log_dir" ]] && [[ -w "$log_dir" ]]; then
        end_time=$(date +%s%3N)
        duration=$((end_time - start_time))
        record_check "Log Directory" "PASS" "Log directory accessible" "$duration"
    else
        end_time=$(date +%s%3N)
        duration=$((end_time - start_time))
        record_check "Log Directory" "FAIL" "Log directory not accessible" "$duration"
    fi
}

# Check service processes
check_processes() {
    log "Checking service processes..."
    
    # Check if running in Docker
    if command -v docker &> /dev/null; then
        # Check Docker containers
        local containers=("aischolar-backend" "aischolar-celery" "aischolar-celery-beat")
        
        for container in "${containers[@]}"; do
            local start_time=$(date +%s%3N)
            
            if docker ps --format "table {{.Names}}" | grep -q "$container"; then
                local end_time=$(date +%s%3N)
                local duration=$((end_time - start_time))
                local status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "unknown")
                record_check "Container $container" "PASS" "Running, health: $status" "$duration"
            else
                local end_time=$(date +%s%3N)
                local duration=$((end_time - start_time))
                record_check "Container $container" "FAIL" "Container not running" "$duration"
            fi
        done
    else
        # Check system processes
        local processes=("python.*app.py" "celery.*worker" "celery.*beat")
        
        for process in "${processes[@]}"; do
            local start_time=$(date +%s%3N)
            
            if pgrep -f "$process" &> /dev/null; then
                local end_time=$(date +%s%3N)
                local duration=$((end_time - start_time))
                local pid=$(pgrep -f "$process" | head -1)
                record_check "Process $process" "PASS" "Running (PID: $pid)" "$duration"
            else
                local end_time=$(date +%s%3N)
                local duration=$((end_time - start_time))
                record_check "Process $process" "FAIL" "Process not running" "$duration"
            fi
        done
    fi
}

# Check SSL certificates
check_ssl() {
    log "Checking SSL certificates..."
    
    local cert_file="${SSL_CERT_PATH:-/etc/ssl/certs/aischolar.crt}"
    local start_time=$(date +%s%3N)
    
    if [[ -f "$cert_file" ]]; then
        local expiry_date=$(openssl x509 -enddate -noout -in "$cert_file" 2>/dev/null | cut -d= -f2)
        local expiry_timestamp=$(date -d "$expiry_date" +%s 2>/dev/null || echo 0)
        local current_timestamp=$(date +%s)
        local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        local end_time=$(date +%s%3N)
        local duration=$((end_time - start_time))
        
        if [[ $days_until_expiry -gt 30 ]]; then
            record_check "SSL Certificate" "PASS" "Valid for $days_until_expiry days" "$duration"
        elif [[ $days_until_expiry -gt 7 ]]; then
            record_check "SSL Certificate" "WARN" "Expires in $days_until_expiry days" "$duration"
        else
            record_check "SSL Certificate" "FAIL" "Expires in $days_until_expiry days" "$duration"
        fi
    else
        local end_time=$(date +%s%3N)
        local duration=$((end_time - start_time))
        record_check "SSL Certificate" "WARN" "Certificate file not found" "$duration"
    fi
}

# Generate health report
generate_report() {
    log "Generating health check report..."
    
    local report_file="${PROJECT_ROOT}/logs/health_check_$(date +%Y%m%d_%H%M%S).json"
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    # Create JSON report
    cat > "$report_file" << EOF
{
    "timestamp": "$timestamp",
    "environment": "$ENVIRONMENT",
    "check_type": "$CHECK_TYPE",
    "summary": {
        "total_checks": $TOTAL_CHECKS,
        "passed_checks": $((TOTAL_CHECKS - FAILED_CHECKS)),
        "failed_checks": $FAILED_CHECKS,
        "success_rate": $(echo "scale=2; ($TOTAL_CHECKS - $FAILED_CHECKS) * 100 / $TOTAL_CHECKS" | bc -l 2>/dev/null || echo "0")
    },
    "checks": [
EOF
    
    local first=true
    for result in "${HEALTH_RESULTS[@]}"; do
        IFS='|' read -r name status message duration <<< "$result"
        
        if [[ "$first" == "true" ]]; then
            first=false
        else
            echo "," >> "$report_file"
        fi
        
        cat >> "$report_file" << EOF
        {
            "name": "$name",
            "status": "$status",
            "message": "$message",
            "duration_ms": $duration
        }
EOF
    done
    
    cat >> "$report_file" << EOF
    ]
}
EOF
    
    log "Health check report saved to: $report_file"
}

# Send health check results
send_results() {
    local status="HEALTHY"
    if [[ $FAILED_CHECKS -gt 0 ]]; then
        status="UNHEALTHY"
    fi
    
    # Send to monitoring system
    if command -v curl &> /dev/null && [[ -n "${PROMETHEUS_PUSHGATEWAY_URL:-}" ]]; then
        curl -X POST "${PROMETHEUS_PUSHGATEWAY_URL}/metrics/job/health_check/instance/${HOSTNAME}" \
            --data "health_check_total_checks $TOTAL_CHECKS" \
            --data "health_check_failed_checks $FAILED_CHECKS" &> /dev/null || true
    fi
    
    # Send notification if unhealthy
    if [[ "$status" == "UNHEALTHY" ]] && [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚨 Health Check Failed: $FAILED_CHECKS/$TOTAL_CHECKS checks failed in $ENVIRONMENT\"}" \
            "${SLACK_WEBHOOK_URL}" &> /dev/null || true
    fi
}

# Main health check function
main() {
    log "Starting Zotero integration health check for environment: $ENVIRONMENT"
    log "Check type: $CHECK_TYPE"
    
    load_environment
    
    # Run checks based on type
    case "$CHECK_TYPE" in
        "basic")
            check_database
            check_redis
            check_api_endpoints
            ;;
        "deep")
            check_database
            check_redis
            check_api_endpoints
            check_storage
            check_processes
            check_ssl
            ;;
        "external")
            check_external_services
            ;;
        "all"|*)
            check_database
            check_redis
            check_api_endpoints
            check_external_services
            check_storage
            check_processes
            check_ssl
            ;;
    esac
    
    # Generate report and send results
    generate_report
    send_results
    
    # Summary
    echo
    log "Health Check Summary:"
    log "Total Checks: $TOTAL_CHECKS"
    log "Passed: $((TOTAL_CHECKS - FAILED_CHECKS))"
    log "Failed: $FAILED_CHECKS"
    
    if [[ $FAILED_CHECKS -eq 0 ]]; then
        success "All health checks passed! ✓"
        exit 0
    else
        error "$FAILED_CHECKS health checks failed! ✗"
        exit 1
    fi
}

# Script usage
usage() {
    echo "Usage: $0 [environment] [check_type]"
    echo "  environment: production, staging, development (default: production)"
    echo "  check_type: all, basic, deep, external (default: all)"
    echo ""
    echo "Examples:"
    echo "  $0 production all"
    echo "  $0 staging basic"
    echo "  $0 development external"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
    *)
        main
        ;;
esac