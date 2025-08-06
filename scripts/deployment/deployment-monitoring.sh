#!/bin/bash

# Deployment Monitoring Script for AI Scholar Advanced RAG
# Monitors deployment health, performance, and rollback triggers

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
MONITORING_INTERVAL=30
MAX_ERROR_RATE=5.0
MAX_RESPONSE_TIME=2000
MIN_SUCCESS_RATE=95.0
ROLLBACK_THRESHOLD=3
DEPLOYMENT_TIMEOUT=1800  # 30 minutes

# Monitoring endpoints
HEALTH_ENDPOINTS=(
    "http://localhost/health"
    "http://localhost/api/health"
    "http://localhost/api/monitoring/health"
)

API_ENDPOINTS=(
    "http://localhost/api/docs"
    "http://localhost/api/auth/health"
    "http://localhost/api/research/health"
    "http://localhost/api/mobile/health"
)

# Metrics collection
collect_metrics() {
    local environment=$1
    local timestamp=$(date +%s)
    
    # Collect response times
    local response_times=()
    local success_count=0
    local total_count=0
    
    for endpoint in "${HEALTH_ENDPOINTS[@]}" "${API_ENDPOINTS[@]}"; do
        total_count=$((total_count + 1))
        
        # Measure response time
        local start_time=$(date +%s%3N)
        if curl -f -s --max-time 10 "$endpoint" > /dev/null 2>&1; then
            local end_time=$(date +%s%3N)
            local response_time=$((end_time - start_time))
            response_times+=($response_time)
            success_count=$((success_count + 1))
        else
            response_times+=(10000)  # Timeout value
        fi
    done
    
    # Calculate metrics
    local avg_response_time=0
    local max_response_time=0
    
    if [ ${#response_times[@]} -gt 0 ]; then
        local sum=0
        for time in "${response_times[@]}"; do
            sum=$((sum + time))
            if [ $time -gt $max_response_time ]; then
                max_response_time=$time
            fi
        done
        avg_response_time=$((sum / ${#response_times[@]}))
    fi
    
    local success_rate=$(echo "scale=2; $success_count * 100 / $total_count" | bc)
    local error_rate=$(echo "scale=2; 100 - $success_rate" | bc)
    
    # Store metrics
    echo "$timestamp,$environment,$success_rate,$error_rate,$avg_response_time,$max_response_time" >> "/tmp/deployment_metrics.csv"
    
    # Return metrics
    echo "$success_rate,$error_rate,$avg_response_time,$max_response_time"
}

# Check deployment health
check_deployment_health() {
    local environment=$1
    local metrics=$(collect_metrics "$environment")
    
    IFS=',' read -r success_rate error_rate avg_response_time max_response_time <<< "$metrics"
    
    print_status "Environment: $environment"
    print_status "Success Rate: ${success_rate}%"
    print_status "Error Rate: ${error_rate}%"
    print_status "Avg Response Time: ${avg_response_time}ms"
    print_status "Max Response Time: ${max_response_time}ms"
    
    # Check thresholds
    local health_issues=0
    
    if (( $(echo "$error_rate > $MAX_ERROR_RATE" | bc -l) )); then
        print_warning "Error rate ($error_rate%) exceeds threshold ($MAX_ERROR_RATE%)"
        health_issues=$((health_issues + 1))
    fi
    
    if (( $(echo "$success_rate < $MIN_SUCCESS_RATE" | bc -l) )); then
        print_warning "Success rate ($success_rate%) below threshold ($MIN_SUCCESS_RATE%)"
        health_issues=$((health_issues + 1))
    fi
    
    if [ $max_response_time -gt $MAX_RESPONSE_TIME ]; then
        print_warning "Max response time (${max_response_time}ms) exceeds threshold (${MAX_RESPONSE_TIME}ms)"
        health_issues=$((health_issues + 1))
    fi
    
    return $health_issues
}

# Monitor database performance
monitor_database() {
    local environment=$1
    
    print_status "Monitoring database performance for $environment..."
    
    # Check database connections
    local db_connections=$(docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -t -c "
        SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
    " | tr -d ' ')
    
    # Check slow queries
    local slow_queries=$(docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -t -c "
        SELECT count(*) FROM pg_stat_statements WHERE mean_time > 1000;
    " | tr -d ' ' || echo "0")
    
    # Check database size
    local db_size=$(docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -t -c "
        SELECT pg_size_pretty(pg_database_size('advanced_rag_db'));
    " | tr -d ' ')
    
    print_status "Active DB Connections: $db_connections"
    print_status "Slow Queries: $slow_queries"
    print_status "Database Size: $db_size"
    
    # Check thresholds
    if [ "$db_connections" -gt 100 ]; then
        print_warning "High number of database connections: $db_connections"
        return 1
    fi
    
    if [ "$slow_queries" -gt 10 ]; then
        print_warning "High number of slow queries: $slow_queries"
        return 1
    fi
    
    return 0
}

# Monitor Redis performance
monitor_redis() {
    local environment=$1
    
    print_status "Monitoring Redis performance for $environment..."
    
    # Get Redis info
    local redis_info=$(docker-compose exec -T redis redis-cli info stats | grep -E "total_commands_processed|total_connections_received|used_memory_human")
    
    print_status "Redis Stats:"
    echo "$redis_info" | while read line; do
        print_status "  $line"
    done
    
    # Check Redis connectivity
    if ! docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_error "Redis connectivity check failed"
        return 1
    fi
    
    return 0
}

# Monitor application logs
monitor_logs() {
    local environment=$1
    local log_file="/app/logs/app.log"
    
    print_status "Monitoring application logs for $environment..."
    
    # Check for error patterns in logs
    local error_count=$(docker-compose logs --tail=100 backend-$environment 2>/dev/null | grep -c "ERROR\|CRITICAL\|Exception" || echo "0")
    local warning_count=$(docker-compose logs --tail=100 backend-$environment 2>/dev/null | grep -c "WARNING" || echo "0")
    
    print_status "Recent Errors: $error_count"
    print_status "Recent Warnings: $warning_count"
    
    # Check for specific error patterns
    if [ "$error_count" -gt 10 ]; then
        print_warning "High error count in logs: $error_count"
        
        # Show recent errors
        print_status "Recent errors:"
        docker-compose logs --tail=10 backend-$environment 2>/dev/null | grep "ERROR\|CRITICAL\|Exception" | tail -5
        
        return 1
    fi
    
    return 0
}

# Check feature flags status
check_feature_flags() {
    local environment=$1
    
    print_status "Checking feature flags for $environment..."
    
    # Get feature flags status
    local flags_response=$(curl -s -H "Authorization: Bearer ${API_TOKEN}" \
        "http://localhost/api/monitoring/features/flags" || echo "{}")
    
    if [ "$flags_response" != "{}" ]; then
        print_status "Feature flags status:"
        echo "$flags_response" | jq -r 'to_entries[] | "  \(.key): \(.value)"' 2>/dev/null || echo "  Unable to parse feature flags"
    else
        print_warning "Unable to retrieve feature flags status"
        return 1
    fi
    
    return 0
}

# Continuous monitoring during deployment
continuous_monitoring() {
    local environment=$1
    local duration=${2:-$DEPLOYMENT_TIMEOUT}
    local start_time=$(date +%s)
    local consecutive_failures=0
    
    print_status "Starting continuous monitoring for $environment (duration: ${duration}s)..."
    
    # Initialize metrics file
    echo "timestamp,environment,success_rate,error_rate,avg_response_time,max_response_time" > "/tmp/deployment_metrics.csv"
    
    while true; do
        local current_time=$(date +%s)
        local elapsed_time=$((current_time - start_time))
        
        if [ $elapsed_time -ge $duration ]; then
            print_success "Monitoring completed successfully"
            break
        fi
        
        print_status "Monitoring check $(date) (elapsed: ${elapsed_time}s)"
        
        # Perform health checks
        local health_issues=0
        
        if ! check_deployment_health "$environment"; then
            health_issues=$((health_issues + $?))
        fi
        
        if ! monitor_database "$environment"; then
            health_issues=$((health_issues + 1))
        fi
        
        if ! monitor_redis "$environment"; then
            health_issues=$((health_issues + 1))
        fi
        
        if ! monitor_logs "$environment"; then
            health_issues=$((health_issues + 1))
        fi
        
        if ! check_feature_flags "$environment"; then
            health_issues=$((health_issues + 1))
        fi
        
        # Check if we should trigger rollback
        if [ $health_issues -gt 0 ]; then
            consecutive_failures=$((consecutive_failures + 1))
            print_warning "Health check issues detected ($consecutive_failures consecutive failures)"
            
            if [ $consecutive_failures -ge $ROLLBACK_THRESHOLD ]; then
                print_error "Rollback threshold reached ($ROLLBACK_THRESHOLD). Triggering rollback..."
                return 2  # Rollback signal
            fi
        else
            consecutive_failures=0
            print_success "All health checks passed"
        fi
        
        sleep $MONITORING_INTERVAL
    done
    
    return 0
}

# Generate monitoring report
generate_report() {
    local environment=$1
    local report_file="/tmp/deployment_report_${environment}_$(date +%Y%m%d_%H%M%S).json"
    
    print_status "Generating monitoring report..."
    
    # Collect final metrics
    local final_metrics=$(collect_metrics "$environment")
    IFS=',' read -r success_rate error_rate avg_response_time max_response_time <<< "$final_metrics"
    
    # Create JSON report
    cat > "$report_file" << EOF
{
  "deployment": {
    "environment": "$environment",
    "timestamp": "$(date -Iseconds)",
    "duration": "$(($(date +%s) - start_time))s"
  },
  "metrics": {
    "success_rate": $success_rate,
    "error_rate": $error_rate,
    "avg_response_time": $avg_response_time,
    "max_response_time": $max_response_time
  },
  "health_checks": {
    "database": "$(monitor_database "$environment" > /dev/null && echo "healthy" || echo "unhealthy")",
    "redis": "$(monitor_redis "$environment" > /dev/null && echo "healthy" || echo "unhealthy")",
    "application": "$(monitor_logs "$environment" > /dev/null && echo "healthy" || echo "unhealthy")"
  },
  "recommendations": [
    $([ $(echo "$success_rate < 98" | bc -l) -eq 1 ] && echo '"Investigate success rate issues",' || echo '')
    $([ $max_response_time -gt 1500 ] && echo '"Optimize response times",' || echo '')
    $([ $(echo "$error_rate > 2" | bc -l) -eq 1 ] && echo '"Reduce error rate"' || echo '')
  ]
}
EOF
    
    print_success "Report generated: $report_file"
    
    # Send report if webhook is configured
    if [ -n "${MONITORING_WEBHOOK_URL:-}" ]; then
        curl -X POST -H "Content-Type: application/json" \
            -d @"$report_file" \
            "$MONITORING_WEBHOOK_URL" > /dev/null 2>&1 || true
    fi
    
    echo "$report_file"
}

# Main monitoring function
main() {
    local command=${1:-monitor}
    local environment=${2:-production}
    local duration=${3:-$DEPLOYMENT_TIMEOUT}
    
    echo ""
    echo "📊 AI Scholar Advanced RAG - Deployment Monitoring"
    echo "=================================================="
    echo "Command: $command"
    echo "Environment: $environment"
    echo "Started: $(date)"
    echo ""
    
    case "$command" in
        "monitor")
            # Continuous monitoring
            local result=$(continuous_monitoring "$environment" "$duration")
            local exit_code=$?
            
            if [ $exit_code -eq 2 ]; then
                print_error "Monitoring triggered rollback"
                exit 2
            elif [ $exit_code -eq 0 ]; then
                generate_report "$environment"
                print_success "🎉 Monitoring completed successfully!"
            else
                print_error "Monitoring failed"
                exit 1
            fi
            ;;
        "check")
            # Single health check
            if check_deployment_health "$environment"; then
                print_success "Health check passed"
            else
                print_error "Health check failed"
                exit 1
            fi
            ;;
        "report")
            # Generate report only
            generate_report "$environment"
            ;;
        *)
            echo "Usage: $0 {monitor|check|report} [environment] [duration]"
            echo ""
            echo "Commands:"
            echo "  monitor  - Continuous monitoring during deployment"
            echo "  check    - Single health check"
            echo "  report   - Generate monitoring report"
            echo ""
            echo "Parameters:"
            echo "  environment - Deployment environment (default: production)"
            echo "  duration    - Monitoring duration in seconds (default: $DEPLOYMENT_TIMEOUT)"
            exit 1
            ;;
    esac
    
    echo ""
    echo "Finished: $(date)"
    echo ""
}

# Install dependencies if needed
if ! command -v bc &> /dev/null; then
    print_status "Installing bc for calculations..."
    apt-get update && apt-get install -y bc
fi

if ! command -v jq &> /dev/null; then
    print_status "Installing jq for JSON processing..."
    apt-get update && apt-get install -y jq
fi

# Run main function
main "$@"