#!/bin/bash

# Rollback script for AI Scholar Advanced RAG
# Quickly reverts to previous deployment in case of issues

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
DEPLOYMENT_DIR="/opt/ai-scholar"
ROLLBACK_STATE_FILE="$DEPLOYMENT_DIR/.rollback_state"
HEALTH_CHECK_URL="http://localhost/health"
API_HEALTH_CHECK_URL="http://localhost/api/health"

# Function to get current active environment
get_current_environment() {
    if docker-compose -f "$DEPLOYMENT_DIR/docker-compose.blue.yml" ps --services --filter status=running | grep -q "frontend\|backend"; then
        echo "blue"
    elif docker-compose -f "$DEPLOYMENT_DIR/docker-compose.green.yml" ps --services --filter status=running | grep -q "frontend\|backend"; then
        echo "green"
    else
        echo "unknown"
    fi
}

# Function to get previous environment from state file
get_previous_environment() {
    if [ -f "$ROLLBACK_STATE_FILE" ]; then
        grep "previous_environment=" "$ROLLBACK_STATE_FILE" | cut -d'=' -f2
    else
        echo "unknown"
    fi
}

# Function to save rollback state
save_rollback_state() {
    local current_env=$1
    local previous_env=$2
    local deployment_time=$3
    
    cat > "$ROLLBACK_STATE_FILE" << EOF
current_environment=$current_env
previous_environment=$previous_env
deployment_time=$deployment_time
rollback_available=true
EOF
}

# Function to perform emergency rollback
emergency_rollback() {
    local target_environment=$1
    
    print_warning "🚨 EMERGENCY ROLLBACK INITIATED 🚨"
    print_status "Rolling back to $target_environment environment..."
    
    # Start previous environment immediately
    print_status "Starting $target_environment environment services..."
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.$target_environment.yml" up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Switch traffic immediately
    if "$DEPLOYMENT_DIR/scripts/deployment/switch-traffic.sh" "$target_environment"; then
        print_success "Traffic switched to $target_environment environment"
    else
        print_error "Failed to switch traffic during emergency rollback"
        return 1
    fi
    
    # Verify rollback
    if verify_rollback "$target_environment"; then
        print_success "Emergency rollback completed successfully"
        
        # Update rollback state
        save_rollback_state "$target_environment" "unknown" "$(date)"
        
        return 0
    else
        print_error "Emergency rollback verification failed"
        return 1
    fi
}

# Function to perform graceful rollback
graceful_rollback() {
    local current_env=$1
    local target_env=$2
    
    print_status "Performing graceful rollback from $current_env to $target_env..."
    
    # Check if target environment is available
    if ! docker-compose -f "$DEPLOYMENT_DIR/docker-compose.$target_env.yml" ps --services | grep -q "frontend\|backend"; then
        print_status "Target environment not running, starting services..."
        docker-compose -f "$DEPLOYMENT_DIR/docker-compose.$target_env.yml" up -d
        
        # Wait for services to be ready
        sleep 60
    fi
    
    # Health check target environment
    local target_port=$([[ "$target_env" == "blue" ]] && echo "8002" || echo "8003")
    if ! curl -f -s "http://localhost:$target_port/health" > /dev/null; then
        print_error "Target environment health check failed"
        return 1
    fi
    
    # Create database backup before rollback
    print_status "Creating pre-rollback database backup..."
    if ! "$DEPLOYMENT_DIR/scripts/deployment/database-migration.sh" backup; then
        print_warning "Database backup failed, continuing with rollback..."
    fi
    
    # Switch traffic gradually (canary rollback)
    print_status "Switching traffic gradually to $target_env environment..."
    
    # Start with 10% traffic
    "$DEPLOYMENT_DIR/scripts/deployment/switch-traffic.sh" "$target_env" nginx canary 10
    sleep 30
    
    # Increase to 50% traffic
    "$DEPLOYMENT_DIR/scripts/deployment/switch-traffic.sh" "$target_env" nginx canary 50
    sleep 30
    
    # Complete the switch
    "$DEPLOYMENT_DIR/scripts/deployment/switch-traffic.sh" "$target_env" nginx
    
    # Verify rollback
    if verify_rollback "$target_env"; then
        print_success "Graceful rollback completed successfully"
        
        # Stop failed environment
        print_status "Stopping failed $current_env environment..."
        docker-compose -f "$DEPLOYMENT_DIR/docker-compose.$current_env.yml" down
        
        # Update rollback state
        save_rollback_state "$target_env" "$current_env" "$(date)"
        
        return 0
    else
        print_error "Graceful rollback verification failed"
        return 1
    fi
}

# Function to verify rollback success
verify_rollback() {
    local environment=$1
    local max_attempts=10
    local attempt=1
    
    print_status "Verifying rollback to $environment environment..."
    
    while [ $attempt -le $max_attempts ]; do
        print_status "Verification attempt $attempt/$max_attempts..."
        
        # Check main health endpoint
        if curl -f -s "$HEALTH_CHECK_URL" > /dev/null; then
            # Check API health endpoint
            if curl -f -s "$API_HEALTH_CHECK_URL" > /dev/null; then
                # Verify deployment environment header
                deployment_env=$(curl -s -I "$HEALTH_CHECK_URL" | grep -i "x-deployment-environment" | cut -d' ' -f2 | tr -d '\r\n')
                
                if [ "$deployment_env" = "$environment" ]; then
                    print_success "Rollback verification successful - serving from $environment environment"
                    return 0
                fi
            fi
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Rollback verification failed after $max_attempts attempts"
            return 1
        fi
        
        sleep 10
        attempt=$((attempt + 1))
    done
}

# Function to rollback database changes
rollback_database() {
    local backup_file=$1
    
    if [ -n "$backup_file" ] && [ -f "$backup_file" ]; then
        print_status "Rolling back database changes..."
        
        # Stop all services temporarily
        docker-compose -f "$DEPLOYMENT_DIR/docker-compose.blue.yml" down || true
        docker-compose -f "$DEPLOYMENT_DIR/docker-compose.green.yml" down || true
        
        # Start only database
        docker-compose up -d postgres
        sleep 10
        
        # Restore database
        docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db < "$backup_file"
        
        print_success "Database rollback completed"
    else
        print_warning "No database backup specified or file not found"
    fi
}

# Function to show rollback status
show_rollback_status() {
    echo ""
    echo "📊 Rollback Status"
    echo "=================="
    
    if [ -f "$ROLLBACK_STATE_FILE" ]; then
        echo "Rollback state file found:"
        cat "$ROLLBACK_STATE_FILE"
        echo ""
    else
        echo "No rollback state file found"
        echo ""
    fi
    
    echo "Current environment status:"
    echo "Blue environment:"
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.blue.yml" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "  Not running"
    
    echo ""
    echo "Green environment:"
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.green.yml" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "  Not running"
    
    echo ""
    echo "Active environment: $(get_current_environment)"
    echo "Previous environment: $(get_previous_environment)"
}

# Function to cleanup rollback artifacts
cleanup_rollback() {
    print_status "Cleaning up rollback artifacts..."
    
    # Remove rollback state file
    rm -f "$ROLLBACK_STATE_FILE"
    
    # Clean up old containers
    docker container prune -f
    
    # Clean up old images
    docker image prune -f
    
    print_success "Rollback cleanup completed"
}

# Main function
main() {
    local command=${1:-auto}
    local target_environment=${2:-}
    local database_backup=${3:-}
    
    echo ""
    echo "🔄 AI Scholar Advanced RAG - Rollback System"
    echo "============================================"
    echo "Command: $command"
    echo "Started: $(date)"
    echo ""
    
    case "$command" in
        "auto")
            # Automatic rollback - determine target environment
            current_env=$(get_current_environment)
            previous_env=$(get_previous_environment)
            
            if [ "$current_env" = "unknown" ]; then
                print_error "Cannot determine current environment"
                exit 1
            fi
            
            if [ "$previous_env" = "unknown" ]; then
                # No previous environment known, switch to opposite
                target_env=$([[ "$current_env" == "blue" ]] && echo "green" || echo "blue")
                print_warning "No previous environment recorded, rolling back to $target_env"
            else
                target_env="$previous_env"
            fi
            
            print_status "Auto-rollback: $current_env -> $target_env"
            graceful_rollback "$current_env" "$target_env"
            ;;
            
        "emergency")
            # Emergency rollback - immediate switch
            if [ -z "$target_environment" ]; then
                current_env=$(get_current_environment)
                target_environment=$([[ "$current_env" == "blue" ]] && echo "green" || echo "blue")
            fi
            
            emergency_rollback "$target_environment"
            ;;
            
        "graceful")
            # Graceful rollback with specified target
            if [ -z "$target_environment" ]; then
                print_error "Target environment required for graceful rollback"
                exit 1
            fi
            
            current_env=$(get_current_environment)
            graceful_rollback "$current_env" "$target_environment"
            ;;
            
        "database")
            # Database-only rollback
            if [ -z "$database_backup" ]; then
                print_error "Database backup file required"
                exit 1
            fi
            
            rollback_database "$database_backup"
            ;;
            
        "status")
            # Show rollback status
            show_rollback_status
            exit 0
            ;;
            
        "cleanup")
            # Cleanup rollback artifacts
            cleanup_rollback
            exit 0
            ;;
            
        *)
            echo "Usage: $0 {auto|emergency|graceful|database|status|cleanup} [target_environment] [database_backup]"
            echo ""
            echo "Commands:"
            echo "  auto      - Automatic rollback to previous environment"
            echo "  emergency - Immediate rollback (specify target environment)"
            echo "  graceful  - Gradual rollback with health checks"
            echo "  database  - Rollback database only (specify backup file)"
            echo "  status    - Show current rollback status"
            echo "  cleanup   - Clean up rollback artifacts"
            echo ""
            echo "Examples:"
            echo "  $0 auto                                    # Auto rollback"
            echo "  $0 emergency blue                          # Emergency rollback to blue"
            echo "  $0 graceful green                          # Graceful rollback to green"
            echo "  $0 database /backups/pre_deploy.sql       # Database rollback"
            exit 1
            ;;
    esac
    
    echo ""
    echo "Finished: $(date)"
    echo ""
}

# Handle errors and perform emergency rollback
trap 'print_error "Rollback script failed at line $LINENO"' ERR

# Run main function
main "$@"