#!/bin/bash

# Automated Incident Response Script for AI Scholar Advanced RAG
# Handles incident detection, escalation, and automated remediation

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
INCIDENT_LOG_DIR="/opt/ai-scholar/logs/incidents"
HEALTH_CHECK_SCRIPT="/opt/ai-scholar/scripts/deployment/health-check.sh"
ROLLBACK_SCRIPT="/opt/ai-scholar/scripts/deployment/rollback.sh"
API_ENDPOINT="${API_ENDPOINT:-http://localhost:8000}"
INCIDENT_RESPONSE_LOG="$INCIDENT_LOG_DIR/incident-response-$(date +%Y%m%d-%H%M%S).log"

# Create incident log directory
mkdir -p "$INCIDENT_LOG_DIR"

# Logging function
log_incident() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$INCIDENT_RESPONSE_LOG"
    echo "$1"
}

# Incident severity levels
declare -A SEVERITY_LEVELS=(
    ["critical"]=1
    ["high"]=2
    ["medium"]=3
    ["low"]=4
)

# Notification functions
send_incident_notification() {
    local incident_type=$1
    local severity=$2
    local message=$3
    local action_taken=$4
    
    log_incident "Sending incident notification: $incident_type ($severity)"
    
    # Slack notification
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local color
        case "$severity" in
            "critical") color="#8b0000" ;;
            "high") color="#ff0000" ;;
            "medium") color="#ff9500" ;;
            "low") color="#36a64f" ;;
            *) color="#ff9500" ;;
        esac
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"🚨 Incident Alert: $incident_type\",
                    \"text\": \"$message\",
                    \"fields\": [
                        {\"title\": \"Severity\", \"value\": \"$severity\", \"short\": true},
                        {\"title\": \"Action Taken\", \"value\": \"$action_taken\", \"short\": true},
                        {\"title\": \"Timestamp\", \"value\": \"$(date)\", \"short\": true},
                        {\"title\": \"Environment\", \"value\": \"${ENVIRONMENT:-production}\", \"short\": true}
                    ]
                }]
            }" \
            "${SLACK_WEBHOOK_URL}" > /dev/null 2>&1 || true
    fi
    
    # PagerDuty for critical incidents
    if [ "$severity" = "critical" ] && [ -n "${PAGERDUTY_INTEGRATION_KEY:-}" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"routing_key\": \"${PAGERDUTY_INTEGRATION_KEY}\",
                \"event_action\": \"trigger\",
                \"payload\": {
                    \"summary\": \"$incident_type: $message\",
                    \"source\": \"ai-scholar-incident-response\",
                    \"severity\": \"$severity\",
                    \"custom_details\": {
                        \"action_taken\": \"$action_taken\",
                        \"timestamp\": \"$(date)\",
                        \"environment\": \"${ENVIRONMENT:-production}\"
                    }
                }
            }" \
            "https://events.pagerduty.com/v2/enqueue" > /dev/null 2>&1 || true
    fi
}

# Health check and incident detection
detect_incidents() {
    log_incident "Starting incident detection..."
    
    local incidents_detected=0
    
    # Run comprehensive health check
    if ! "$HEALTH_CHECK_SCRIPT" comprehensive > /dev/null 2>&1; then
        log_incident "Health check failed - investigating..."
        
        # Check specific components
        check_system_resources
        check_service_health
        check_database_health
        check_integration_health
        
        incidents_detected=1
    fi
    
    # Check error rates
    check_error_rates
    
    # Check performance metrics
    check_performance_degradation
    
    return $incidents_detected
}

# System resource monitoring
check_system_resources() {
    log_incident "Checking system resources..."
    
    # Check CPU usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    if (( $(echo "$cpu_usage > 90" | bc -l) )); then
        handle_high_cpu_usage "$cpu_usage"
    fi
    
    # Check memory usage
    memory_usage=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
    if (( $(echo "$memory_usage > 90" | bc -l) )); then
        handle_high_memory_usage "$memory_usage"
    fi
    
    # Check disk usage
    disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 95 ]; then
        handle_high_disk_usage "$disk_usage"
    fi
}

# Service health monitoring
check_service_health() {
    log_incident "Checking service health..."
    
    # Check if critical services are running
    local critical_services=("postgres" "redis" "chromadb")
    
    for service in "${critical_services[@]}"; do
        if ! docker-compose ps "$service" | grep -q "Up"; then
            handle_service_down "$service"
        fi
    done
    
    # Check application containers
    if ! docker-compose ps backend | grep -q "Up"; then
        handle_application_down "backend"
    fi
    
    if ! docker-compose ps frontend | grep -q "Up"; then
        handle_application_down "frontend"
    fi
}

# Database health monitoring
check_database_health() {
    log_incident "Checking database health..."
    
    # Check database connectivity
    if ! docker-compose exec -T postgres pg_isready -U rag_user -d advanced_rag_db > /dev/null 2>&1; then
        handle_database_connectivity_issue
    fi
    
    # Check database connections
    connection_count=$(docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'advanced_rag_db';" | tr -d ' ')
    
    if [ "$connection_count" -gt 100 ]; then
        handle_high_database_connections "$connection_count"
    fi
}

# Integration health monitoring
check_integration_health() {
    log_incident "Checking integration health..."
    
    # Check external integrations via API
    if command -v curl &> /dev/null; then
        integration_health=$(curl -s --max-time 10 "$API_ENDPOINT/api/monitoring/integrations/health" | jq -r '.overall_health_percentage // 0' 2>/dev/null || echo "0")
        
        if (( $(echo "$integration_health < 70" | bc -l) )); then
            handle_integration_degradation "$integration_health"
        fi
    fi
}

# Error rate monitoring
check_error_rates() {
    log_incident "Checking error rates..."
    
    # Get error metrics from API
    if command -v curl &> /dev/null; then
        error_data=$(curl -s --max-time 10 "$API_ENDPOINT/api/monitoring/performance?hours=1" 2>/dev/null || echo "{}")
        error_rate=$(echo "$error_data" | jq -r '.error_rate // 0' 2>/dev/null || echo "0")
        
        if (( $(echo "$error_rate > 10" | bc -l) )); then
            handle_high_error_rate "$error_rate"
        fi
    fi
}

# Performance monitoring
check_performance_degradation() {
    log_incident "Checking performance metrics..."
    
    # Get performance metrics from API
    if command -v curl &> /dev/null; then
        perf_data=$(curl -s --max-time 10 "$API_ENDPOINT/api/monitoring/performance?hours=1" 2>/dev/null || echo "{}")
        p95_response_time=$(echo "$perf_data" | jq -r '.response_time_ms.p95 // 0' 2>/dev/null || echo "0")
        
        if (( $(echo "$p95_response_time > 5000" | bc -l) )); then
            handle_performance_degradation "$p95_response_time"
        fi
    fi
}

# Incident handlers
handle_high_cpu_usage() {
    local cpu_usage=$1
    log_incident "CRITICAL: High CPU usage detected: ${cpu_usage}%"
    
    # Identify top CPU processes
    top_processes=$(ps aux --sort=-%cpu | head -10)
    log_incident "Top CPU processes: $top_processes"
    
    # Automated remediation
    log_incident "Attempting automated remediation for high CPU usage..."
    
    # Restart high CPU containers if they're consuming too much
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}" | while read line; do
        if [[ $line == *"%"* ]]; then
            container=$(echo $line | awk '{print $1}')
            cpu_percent=$(echo $line | awk '{print $2}' | sed 's/%//')
            
            if (( $(echo "$cpu_percent > 80" | bc -l) )); then
                log_incident "Restarting high CPU container: $container"
                docker restart "$container" || true
            fi
        fi
    done
    
    send_incident_notification "High CPU Usage" "critical" "CPU usage at ${cpu_usage}%" "Container restart attempted"
}

handle_high_memory_usage() {
    local memory_usage=$1
    log_incident "HIGH: High memory usage detected: ${memory_usage}%"
    
    # Clear system caches
    log_incident "Clearing system caches..."
    sync && echo 3 > /proc/sys/vm/drop_caches || true
    
    # Clear Redis cache if it's consuming too much memory
    docker-compose exec -T redis redis-cli FLUSHDB || true
    
    send_incident_notification "High Memory Usage" "high" "Memory usage at ${memory_usage}%" "Cache clearing attempted"
}

handle_high_disk_usage() {
    local disk_usage=$1
    log_incident "CRITICAL: High disk usage detected: ${disk_usage}%"
    
    # Clean up old logs
    log_incident "Cleaning up old logs..."
    find /opt/ai-scholar/logs -name "*.log" -mtime +7 -delete || true
    
    # Clean up Docker
    log_incident "Cleaning up Docker resources..."
    docker system prune -f || true
    
    # Clean up old backups
    find /opt/ai-scholar/backups -name "*.sql" -mtime +30 -delete || true
    
    send_incident_notification "High Disk Usage" "critical" "Disk usage at ${disk_usage}%" "Cleanup operations performed"
}

handle_service_down() {
    local service=$1
    log_incident "CRITICAL: Service down detected: $service"
    
    # Attempt to restart the service
    log_incident "Attempting to restart service: $service"
    docker-compose restart "$service" || docker-compose up -d "$service"
    
    # Wait and verify
    sleep 30
    if docker-compose ps "$service" | grep -q "Up"; then
        log_incident "Service $service successfully restarted"
        send_incident_notification "Service Recovery" "medium" "Service $service was down and has been restarted" "Service restart successful"
    else
        log_incident "Failed to restart service: $service"
        send_incident_notification "Service Down" "critical" "Service $service is down and restart failed" "Manual intervention required"
    fi
}

handle_application_down() {
    local app=$1
    log_incident "CRITICAL: Application down detected: $app"
    
    # Check if it's a deployment issue
    if [ -f "/opt/ai-scholar/.deployment_in_progress" ]; then
        log_incident "Deployment in progress, skipping automatic restart"
        return
    fi
    
    # Attempt to restart the application
    log_incident "Attempting to restart application: $app"
    docker-compose restart "$app"
    
    # Wait and verify
    sleep 60
    if docker-compose ps "$app" | grep -q "Up"; then
        log_incident "Application $app successfully restarted"
        send_incident_notification "Application Recovery" "medium" "Application $app was down and has been restarted" "Application restart successful"
    else
        log_incident "Failed to restart application: $app - initiating rollback"
        initiate_emergency_rollback
    fi
}

handle_database_connectivity_issue() {
    log_incident "CRITICAL: Database connectivity issue detected"
    
    # Restart PostgreSQL container
    log_incident "Restarting PostgreSQL container..."
    docker-compose restart postgres
    
    # Wait for database to be ready
    sleep 30
    
    # Verify connectivity
    if docker-compose exec -T postgres pg_isready -U rag_user -d advanced_rag_db > /dev/null 2>&1; then
        log_incident "Database connectivity restored"
        send_incident_notification "Database Recovery" "high" "Database connectivity was lost and has been restored" "Database restart successful"
    else
        log_incident "Database connectivity still failing"
        send_incident_notification "Database Down" "critical" "Database connectivity failed and restart unsuccessful" "Manual intervention required"
    fi
}

handle_high_database_connections() {
    local connection_count=$1
    log_incident "HIGH: High database connection count: $connection_count"
    
    # Kill idle connections
    log_incident "Terminating idle database connections..."
    docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -c "
        SELECT pg_terminate_backend(pid) 
        FROM pg_stat_activity 
        WHERE datname = 'advanced_rag_db' 
        AND state = 'idle' 
        AND state_change < now() - interval '5 minutes';
    " || true
    
    send_incident_notification "High DB Connections" "high" "Database connection count at $connection_count" "Idle connections terminated"
}

handle_integration_degradation() {
    local health_percentage=$1
    log_incident "HIGH: Integration health degraded: ${health_percentage}%"
    
    # This would trigger integration-specific recovery procedures
    log_incident "Integration health degradation detected - monitoring for recovery"
    
    send_incident_notification "Integration Degradation" "high" "Integration health at ${health_percentage}%" "Monitoring for recovery"
}

handle_high_error_rate() {
    local error_rate=$1
    log_incident "HIGH: High error rate detected: ${error_rate}%"
    
    # Check if this is a deployment-related issue
    if [ -f "/opt/ai-scholar/.deployment_in_progress" ]; then
        log_incident "Deployment in progress - monitoring error rate"
        return
    fi
    
    # If error rate is extremely high, consider rollback
    if (( $(echo "$error_rate > 25" | bc -l) )); then
        log_incident "Error rate critically high - considering rollback"
        initiate_emergency_rollback
    fi
    
    send_incident_notification "High Error Rate" "high" "Error rate at ${error_rate}%" "Monitoring and potential rollback"
}

handle_performance_degradation() {
    local response_time=$1
    log_incident "MEDIUM: Performance degradation detected: ${response_time}ms P95"
    
    # Scale up if possible (this would depend on your orchestration setup)
    log_incident "Performance degradation detected - considering scaling"
    
    send_incident_notification "Performance Degradation" "medium" "P95 response time at ${response_time}ms" "Performance monitoring active"
}

# Emergency procedures
initiate_emergency_rollback() {
    log_incident "CRITICAL: Initiating emergency rollback procedure"
    
    # Create rollback marker
    touch "/opt/ai-scholar/.emergency_rollback_in_progress"
    
    # Execute rollback
    if [ -x "$ROLLBACK_SCRIPT" ]; then
        log_incident "Executing emergency rollback..."
        "$ROLLBACK_SCRIPT" emergency
        
        # Wait and verify
        sleep 60
        if "$HEALTH_CHECK_SCRIPT" quick > /dev/null 2>&1; then
            log_incident "Emergency rollback successful"
            send_incident_notification "Emergency Rollback" "critical" "System issues detected - emergency rollback executed" "Rollback successful"
        else
            log_incident "Emergency rollback failed"
            send_incident_notification "Rollback Failed" "critical" "Emergency rollback failed - manual intervention required" "Manual intervention required"
        fi
    else
        log_incident "Rollback script not found or not executable"
        send_incident_notification "Rollback Unavailable" "critical" "Emergency rollback needed but script unavailable" "Manual intervention required"
    fi
    
    # Remove rollback marker
    rm -f "/opt/ai-scholar/.emergency_rollback_in_progress"
}

# Incident escalation
escalate_incident() {
    local incident_type=$1
    local severity=$2
    local message=$3
    
    log_incident "Escalating incident: $incident_type ($severity)"
    
    # Create incident via API
    if command -v curl &> /dev/null; then
        curl -X POST "$API_ENDPOINT/api/error-tracking/incidents" \
            -H "Content-Type: application/json" \
            -d "{
                \"title\": \"$incident_type\",
                \"description\": \"$message\",
                \"severity\": \"$severity\",
                \"category\": \"system\",
                \"affected_features\": [\"system\"]
            }" > /dev/null 2>&1 || true
    fi
    
    # Send escalation notifications
    send_incident_notification "$incident_type" "$severity" "$message" "Incident escalated"
}

# Recovery verification
verify_recovery() {
    log_incident "Verifying system recovery..."
    
    # Run health checks
    if "$HEALTH_CHECK_SCRIPT" comprehensive > /dev/null 2>&1; then
        log_incident "System recovery verified"
        send_incident_notification "System Recovery" "low" "System has recovered from incidents" "Recovery verified"
        return 0
    else
        log_incident "System recovery not complete"
        return 1
    fi
}

# Main incident response function
main() {
    local mode=${1:-monitor}
    
    echo ""
    echo "🚨 AI Scholar Advanced RAG - Incident Response"
    echo "=============================================="
    echo "Mode: $mode"
    echo "Started: $(date)"
    echo "Log File: $INCIDENT_RESPONSE_LOG"
    echo ""
    
    case "$mode" in
        "monitor")
            # Continuous monitoring mode
            log_incident "Starting incident monitoring..."
            
            while true; do
                if detect_incidents; then
                    log_incident "Incidents detected - running response procedures"
                    
                    # Wait for remediation to take effect
                    sleep 300  # 5 minutes
                    
                    # Verify recovery
                    if verify_recovery; then
                        log_incident "Recovery successful"
                    else
                        log_incident "Recovery incomplete - escalating"
                        escalate_incident "System Degradation" "high" "Automated remediation did not fully resolve system issues"
                    fi
                else
                    log_incident "No incidents detected"
                fi
                
                # Wait before next check
                sleep 60  # 1 minute
            done
            ;;
            
        "check")
            # One-time incident check
            log_incident "Running one-time incident check..."
            
            if detect_incidents; then
                log_incident "Incidents detected"
                exit 1
            else
                log_incident "No incidents detected"
                exit 0
            fi
            ;;
            
        "test")
            # Test incident response procedures
            log_incident "Testing incident response procedures..."
            
            # Test notifications
            send_incident_notification "Test Incident" "low" "This is a test of the incident response system" "Test notification"
            
            log_incident "Incident response test completed"
            ;;
            
        "escalate")
            # Manual incident escalation
            local incident_type=${2:-"Manual Escalation"}
            local severity=${3:-"medium"}
            local message=${4:-"Manual incident escalation requested"}
            
            escalate_incident "$incident_type" "$severity" "$message"
            ;;
            
        *)
            echo "Usage: $0 {monitor|check|test|escalate} [incident_type] [severity] [message]"
            echo ""
            echo "Modes:"
            echo "  monitor   - Continuous incident monitoring (default)"
            echo "  check     - One-time incident check"
            echo "  test      - Test incident response procedures"
            echo "  escalate  - Manual incident escalation"
            echo ""
            echo "Examples:"
            echo "  $0 monitor                                    # Start continuous monitoring"
            echo "  $0 check                                      # Check for incidents once"
            echo "  $0 test                                       # Test notifications"
            echo "  $0 escalate \"Database Issue\" high \"DB down\"  # Manual escalation"
            exit 1
            ;;
    esac
    
    echo ""
    echo "Finished: $(date)"
    echo "Log File: $INCIDENT_RESPONSE_LOG"
    echo ""
}

# Error handling
trap 'log_incident "Incident response script failed at line $LINENO"' ERR

# Ensure required tools are available
command -v bc >/dev/null 2>&1 || { echo "bc is required but not installed. Aborting." >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "jq is required but not installed. Aborting." >&2; exit 1; }

# Run main function
main "$@"