#!/bin/bash
# AI Scholar Management Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

COMPOSE_FILE="docker-compose.prod.yml"

show_help() {
    echo -e "${BLUE}AI Scholar Management Script${NC}"
    echo
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  start [profile]     Start services (profiles: monitoring, workers, backup, full)"
    echo "  stop               Stop all services"
    echo "  restart [service]  Restart all services or specific service"
    echo "  status             Show service status"
    echo "  logs [service]     Show logs for all services or specific service"
    echo "  update             Update and restart services"
    echo "  backup             Create manual backup"
    echo "  ssl [domain]       Set up SSL certificate"
    echo "  health             Check service health"
    echo "  clean              Clean up unused Docker resources"
    echo "  deploy             Run full deployment"
    echo
    echo "Examples:"
    echo "  $0 start monitoring    # Start with monitoring"
    echo "  $0 logs backend        # Show backend logs"
    echo "  $0 restart nginx       # Restart nginx"
    echo "  $0 ssl example.com     # Set up SSL for domain"
}

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

check_requirements() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "docker-compose.prod.yml not found. Please run from project directory."
    fi
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please run ./scripts/deploy.sh first."
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please run ./scripts/deploy.sh first."
    fi
}

start_services() {
    local profile=$1
    log "Starting AI Scholar services..."
    
    if [ -n "$profile" ]; then
        log "Using profile: $profile"
        docker-compose -f $COMPOSE_FILE --profile $profile up -d
    else
        # Default to monitoring enabled for scholar.cmejo.com
        log "Starting with monitoring enabled by default"
        docker-compose -f $COMPOSE_FILE --profile monitoring up -d
    fi
    
    log "Services started successfully!"
}

stop_services() {
    log "Stopping AI Scholar services..."
    docker-compose -f $COMPOSE_FILE down
    log "Services stopped successfully!"
}

restart_services() {
    local service=$1
    
    if [ -n "$service" ]; then
        log "Restarting service: $service"
        docker-compose -f $COMPOSE_FILE restart $service
    else
        log "Restarting all services..."
        docker-compose -f $COMPOSE_FILE restart
    fi
    
    log "Restart completed!"
}

show_status() {
    log "Service Status:"
    docker-compose -f $COMPOSE_FILE ps
    echo
    log "Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

show_logs() {
    local service=$1
    
    if [ -n "$service" ]; then
        log "Showing logs for service: $service"
        docker-compose -f $COMPOSE_FILE logs -f --tail=100 $service
    else
        log "Showing logs for all services:"
        docker-compose -f $COMPOSE_FILE logs -f --tail=50
    fi
}

update_services() {
    log "Updating AI Scholar services..."
    
    # Pull latest images
    docker-compose -f $COMPOSE_FILE pull
    
    # Rebuild custom images
    docker-compose -f $COMPOSE_FILE build --no-cache
    
    # Restart services
    docker-compose -f $COMPOSE_FILE up -d
    
    log "Update completed successfully!"
}

create_backup() {
    log "Creating manual backup..."
    
    if docker-compose -f $COMPOSE_FILE ps | grep -q backup; then
        docker-compose -f $COMPOSE_FILE exec backup python3 /backup/backup.py
    else
        warn "Backup service not running. Starting backup service..."
        docker-compose -f $COMPOSE_FILE --profile backup up -d backup
        sleep 10
        docker-compose -f $COMPOSE_FILE exec backup python3 /backup/backup.py
    fi
    
    log "Backup completed!"
}

setup_ssl() {
    local domain=$1
    
    if [ -z "$domain" ]; then
        error "Please provide a domain name: $0 ssl example.com"
    fi
    
    if [ ! -f "scripts/setup-ssl.sh" ]; then
        error "SSL setup script not found"
    fi
    
    log "Setting up SSL for domain: $domain"
    ./scripts/setup-ssl.sh $domain
}

check_health() {
    log "Checking service health..."
    
    # Check if services are running
    if ! docker-compose -f $COMPOSE_FILE ps | grep -q "Up"; then
        error "Some services are not running"
    fi
    
    # Check endpoints
    local endpoints=(
        "http://localhost:8000/health:Backend"
        "http://localhost:3000/health:Frontend"
        "http://localhost:8080/api/v1/heartbeat:ChromaDB"
        "http://localhost:11434/api/tags:Ollama"
    )
    
    for endpoint in "${endpoints[@]}"; do
        IFS=':' read -r url name <<< "$endpoint"
        if curl -f "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ $name is healthy${NC}"
        else
            echo -e "${RED}✗ $name is not responding${NC}"
        fi
    done
    
    log "Health check completed!"
}

clean_docker() {
    log "Cleaning up Docker resources..."
    
    # Remove unused containers, networks, images
    docker system prune -f
    
    # Remove unused volumes (be careful!)
    read -p "Remove unused volumes? This may delete data! (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume prune -f
    fi
    
    log "Docker cleanup completed!"
}

run_deployment() {
    if [ ! -f "scripts/deploy.sh" ]; then
        error "Deployment script not found"
    fi
    
    log "Running full deployment..."
    ./scripts/deploy.sh
}

# Main script logic
case "$1" in
    start)
        check_requirements
        start_services $2
        ;;
    stop)
        check_requirements
        stop_services
        ;;
    restart)
        check_requirements
        restart_services $2
        ;;
    status)
        check_requirements
        show_status
        ;;
    logs)
        check_requirements
        show_logs $2
        ;;
    update)
        check_requirements
        update_services
        ;;
    backup)
        check_requirements
        create_backup
        ;;
    ssl)
        check_requirements
        setup_ssl $2
        ;;
    health)
        check_requirements
        check_health
        ;;
    clean)
        clean_docker
        ;;
    deploy)
        run_deployment
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo
        show_help
        exit 1
        ;;
esac