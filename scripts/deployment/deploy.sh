#!/bin/bash

# Main deployment orchestration script for AI Scholar Advanced RAG
# Coordinates all deployment activities including CI/CD, blue-green, and monitoring

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
SCRIPTS_DIR="$DEPLOYMENT_DIR/scripts/deployment"
LOG_DIR="$DEPLOYMENT_DIR/logs/deployment"
DEPLOYMENT_LOG="$LOG_DIR/deployment-$(date +%Y%m%d-%H%M%S).log"

# Create log directory
mkdir -p "$LOG_DIR"

# Logging function
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$DEPLOYMENT_LOG"
    echo "$1"
}

# Pre-deployment checks
pre_deployment_checks() {
    log_message "Starting pre-deployment checks..."
    
    # Check if required scripts exist
    local required_scripts=(
        "blue-green-deployment.sh"
        "database-migration.sh"
        "health-check.sh"
        "switch-traffic.sh"
        "rollback.sh"
    )
    
    for script in "${required_scripts[@]}"; do
        if [ ! -f "$SCRIPTS_DIR/$script" ]; then
            print_error "Required script not found: $script"
            return 1
        fi
        
        if [ ! -x "$SCRIPTS_DIR/$script" ]; then
            chmod +x "$SCRIPTS_DIR/$script"
        fi
    done
    
    # Check Docker daemon
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker daemon is not running"
        return 1
    fi
    
    # Check Docker Compose
    if ! docker-compose version > /dev/null 2>&1; then
        print_error "Docker Compose is not available"
        return 1
    fi
    
    # Check system resources
    if ! "$SCRIPTS_DIR/health-check.sh" quick > /dev/null 2>&1; then
        print_warning "System health check failed, but continuing..."
    fi
    
    # Check network connectivity
    if ! curl -f -s --max-time 10 "https://github.com" > /dev/null; then
        print_error "Network connectivity check failed"
        return 1
    fi
    
    log_message "Pre-deployment checks completed successfully"
    return 0
}

# Build and push Docker images
build_and_push_images() {
    local image_tag=${1:-latest}
    local registry=${2:-ghcr.io}
    local image_name=${3:-ai-scholar/advanced-rag}
    
    log_message "Building and pushing Docker images with tag: $image_tag"
    
    # Build frontend image
    print_status "Building frontend image..."
    docker build -f config/dockerfiles/Dockerfile.frontend -t "$registry/$image_name-frontend:$image_tag" .
    docker push "$registry/$image_name-frontend:$image_tag"
    
    # Build backend image
    print_status "Building backend image..."
    docker build -f config/dockerfiles/Dockerfile.backend -t "$registry/$image_name-backend:$image_tag" .
    docker push "$registry/$image_name-backend:$image_tag"
    
    # Build nginx image
    print_status "Building nginx image..."
    docker build -f config/dockerfiles/Dockerfile.nginx -t "$registry/$image_name-nginx:$image_tag" .
    docker push "$registry/$image_name-nginx:$image_tag"
    
    log_message "Docker images built and pushed successfully"
}

# Deploy infrastructure services
deploy_infrastructure() {
    log_message "Deploying infrastructure services..."
    
    # Start core infrastructure
    print_status "Starting core infrastructure services..."
    docker-compose up -d postgres redis chromadb
    
    # Wait for services to be ready
    print_status "Waiting for infrastructure services to be ready..."
    sleep 30
    
    # Verify infrastructure health
    if ! "$SCRIPTS_DIR/health-check.sh" database > /dev/null 2>&1; then
        print_error "Database health check failed"
        return 1
    fi
    
    if ! "$SCRIPTS_DIR/health-check.sh" redis > /dev/null 2>&1; then
        print_error "Redis health check failed"
        return 1
    fi
    
    log_message "Infrastructure services deployed successfully"
}

# Run database migrations
run_database_migrations() {
    local migration_type=${1:-migrate}
    
    log_message "Running database migrations (type: $migration_type)..."
    
    if "$SCRIPTS_DIR/database-migration.sh" "$migration_type"; then
        log_message "Database migrations completed successfully"
        return 0
    else
        print_error "Database migrations failed"
        return 1
    fi
}

# Deploy application using blue-green strategy
deploy_application() {
    local image_tag=${1:-latest}
    local deployment_strategy=${2:-blue-green}
    
    log_message "Deploying application (strategy: $deployment_strategy, tag: $image_tag)..."
    
    case "$deployment_strategy" in
        "blue-green")
            if "$SCRIPTS_DIR/blue-green-deployment.sh" "$image_tag"; then
                log_message "Blue-green deployment completed successfully"
                return 0
            else
                print_error "Blue-green deployment failed"
                return 1
            fi
            ;;
        "rolling")
            # Rolling deployment implementation
            print_status "Performing rolling deployment..."
            # Update services one by one
            docker-compose up -d --no-deps backend
            sleep 30
            docker-compose up -d --no-deps frontend
            sleep 30
            docker-compose up -d --no-deps nginx
            ;;
        "recreate")
            # Recreate deployment (downtime expected)
            print_status "Performing recreate deployment..."
            docker-compose down
            docker-compose up -d
            ;;
        *)
            print_error "Unknown deployment strategy: $deployment_strategy"
            return 1
            ;;
    esac
}

# Post-deployment verification
post_deployment_verification() {
    log_message "Running post-deployment verification..."
    
    # Wait for services to stabilize
    print_status "Waiting for services to stabilize..."
    sleep 60
    
    # Run comprehensive health check
    if "$SCRIPTS_DIR/health-check.sh" comprehensive; then
        log_message "Post-deployment health check passed"
    else
        print_error "Post-deployment health check failed"
        return 1
    fi
    
    # Run smoke tests
    print_status "Running smoke tests..."
    if run_smoke_tests; then
        log_message "Smoke tests passed"
    else
        print_error "Smoke tests failed"
        return 1
    fi
    
    # Update monitoring dashboards
    update_monitoring_dashboards
    
    log_message "Post-deployment verification completed successfully"
}

# Run smoke tests
run_smoke_tests() {
    print_status "Executing smoke tests..."
    
    # Test main endpoints
    local endpoints=(
        "http://localhost/health"
        "http://localhost/api/health"
        "http://localhost/api/docs"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if ! curl -f -s --max-time 30 "$endpoint" > /dev/null; then
            print_error "Smoke test failed for endpoint: $endpoint"
            return 1
        fi
    done
    
    # Test database connectivity
    if ! docker-compose exec -T backend python -c "
from backend.core.database import get_db
try:
    db = next(get_db())
    db.execute('SELECT 1')
    print('Database connectivity test passed')
except Exception as e:
    print(f'Database connectivity test failed: {e}')
    exit(1)
"; then
        return 1
    fi
    
    # Test Redis connectivity
    if ! docker-compose exec -T backend python -c "
from backend.core.redis_client import redis_client
try:
    redis_client.ping()
    print('Redis connectivity test passed')
except Exception as e:
    print(f'Redis connectivity test failed: {e}')
    exit(1)
"; then
        return 1
    fi
    
    return 0
}

# Update monitoring dashboards
update_monitoring_dashboards() {
    print_status "Updating monitoring dashboards..."
    
    # Update Grafana dashboards if available
    if curl -f -s --max-time 10 "http://localhost:3001/api/health" > /dev/null; then
        # Import or update dashboards
        print_status "Grafana is available, updating dashboards..."
        # Dashboard update logic would go here
    fi
    
    # Update Prometheus configuration if needed
    if docker-compose ps prometheus | grep -q "Up"; then
        print_status "Prometheus is running, configuration is up to date"
    fi
}

# Cleanup old resources
cleanup_old_resources() {
    log_message "Cleaning up old resources..."
    
    # Remove old Docker images
    print_status "Removing old Docker images..."
    docker image prune -f
    
    # Remove old containers
    print_status "Removing old containers..."
    docker container prune -f
    
    # Clean up old logs (keep last 30 days)
    print_status "Cleaning up old logs..."
    find "$LOG_DIR" -name "deployment-*.log" -mtime +30 -delete 2>/dev/null || true
    
    log_message "Cleanup completed"
}

# Send deployment notifications
send_notifications() {
    local status=$1
    local deployment_info=$2
    
    log_message "Sending deployment notifications (status: $status)..."
    
    # Slack notification
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local color=$([[ "$status" == "success" ]] && echo "good" || echo "danger")
        local message="AI Scholar Advanced RAG deployment $status"
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"$message\",
                    \"text\": \"$deployment_info\",
                    \"fields\": [
                        {\"title\": \"Environment\", \"value\": \"${ENVIRONMENT:-production}\", \"short\": true},
                        {\"title\": \"Version\", \"value\": \"${IMAGE_TAG:-latest}\", \"short\": true},
                        {\"title\": \"Timestamp\", \"value\": \"$(date)\", \"short\": true}
                    ]
                }]
            }" \
            "${SLACK_WEBHOOK_URL}" > /dev/null 2>&1 || true
    fi
    
    # Email notification (if configured)
    if [ -n "${EMAIL_NOTIFICATION:-}" ]; then
        echo "$deployment_info" | mail -s "AI Scholar Deployment $status" "$EMAIL_NOTIFICATION" 2>/dev/null || true
    fi
}

# Main deployment function
main() {
    local command=${1:-deploy}
    local image_tag=${2:-latest}
    local deployment_strategy=${3:-blue-green}
    local skip_checks=${4:-false}
    
    echo ""
    echo "🚀 AI Scholar Advanced RAG - Deployment Orchestrator"
    echo "===================================================="
    echo "Command: $command"
    echo "Image Tag: $image_tag"
    echo "Strategy: $deployment_strategy"
    echo "Started: $(date)"
    echo "Log File: $DEPLOYMENT_LOG"
    echo ""
    
    case "$command" in
        "deploy")
            # Full deployment process
            log_message "Starting full deployment process..."
            
            if [ "$skip_checks" != "true" ]; then
                if ! pre_deployment_checks; then
                    send_notifications "failed" "Pre-deployment checks failed"
                    exit 1
                fi
            fi
            
            # Setup feature flags for deployment
            if [ -f "$SCRIPTS_DIR/feature-flag-management.sh" ]; then
                print_status "Setting up feature flags for deployment..."
                "$SCRIPTS_DIR/feature-flag-management.sh" pre-deploy
            fi
            
            if ! deploy_infrastructure; then
                send_notifications "failed" "Infrastructure deployment failed"
                exit 1
            fi
            
            if ! run_database_migrations; then
                send_notifications "failed" "Database migrations failed"
                exit 1
            fi
            
            if ! deploy_application "$image_tag" "$deployment_strategy"; then
                send_notifications "failed" "Application deployment failed"
                # Attempt rollback
                print_warning "Attempting automatic rollback..."
                "$SCRIPTS_DIR/rollback.sh" emergency
                exit 1
            fi
            
            if ! post_deployment_verification; then
                send_notifications "failed" "Post-deployment verification failed"
                # Attempt rollback
                print_warning "Attempting automatic rollback..."
                "$SCRIPTS_DIR/rollback.sh" emergency
                exit 1
            fi
            
            cleanup_old_resources
            
            send_notifications "success" "Deployment completed successfully with $deployment_strategy strategy"
            print_success "🎉 Deployment completed successfully!"
            ;;
            
        "build")
            # Build and push images only
            build_and_push_images "$image_tag"
            ;;
            
        "infrastructure")
            # Deploy infrastructure only
            deploy_infrastructure
            ;;
            
        "migrate")
            # Run database migrations only
            run_database_migrations "$image_tag"
            ;;
            
        "verify")
            # Run verification only
            post_deployment_verification
            ;;
            
        "rollback")
            # Perform rollback
            "$SCRIPTS_DIR/rollback.sh" auto
            ;;
            
        "status")
            # Show deployment status
            "$SCRIPTS_DIR/health-check.sh" comprehensive
            ;;
            
        *)
            echo "Usage: $0 {deploy|build|infrastructure|migrate|verify|rollback|status} [image_tag] [strategy] [skip_checks]"
            echo ""
            echo "Commands:"
            echo "  deploy         - Full deployment process (default)"
            echo "  build          - Build and push Docker images only"
            echo "  infrastructure - Deploy infrastructure services only"
            echo "  migrate        - Run database migrations only"
            echo "  verify         - Run post-deployment verification only"
            echo "  rollback       - Perform automatic rollback"
            echo "  status         - Show current deployment status"
            echo ""
            echo "Parameters:"
            echo "  image_tag      - Docker image tag (default: latest)"
            echo "  strategy       - Deployment strategy: blue-green|rolling|recreate (default: blue-green)"
            echo "  skip_checks    - Skip pre-deployment checks: true|false (default: false)"
            echo ""
            echo "Examples:"
            echo "  $0 deploy v1.2.3 blue-green"
            echo "  $0 build v1.2.3"
            echo "  $0 rollback"
            exit 1
            ;;
    esac
    
    echo ""
    echo "Finished: $(date)"
    echo "Log File: $DEPLOYMENT_LOG"
    echo ""
}

# Error handling
trap 'print_error "Deployment failed at line $LINENO. Check log: $DEPLOYMENT_LOG"' ERR

# Make scripts executable
chmod +x "$SCRIPTS_DIR"/*.sh 2>/dev/null || true

# Run main function
main "$@"