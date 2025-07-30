#!/bin/bash

# Advanced RAG Research Ecosystem - Deployment Script
# This script automates the deployment process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env.production"
BACKUP_DIR="./backups"
LOG_DIR="./logs"

# Function to print colored output
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

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if environment file exists
    if [ ! -f "$ENV_FILE" ]; then
        print_error "Environment file $ENV_FILE not found. Please create it from .env.example"
        exit 1
    fi
    
    # Check if required directories exist
    mkdir -p "$BACKUP_DIR" "$LOG_DIR" "uploads" "nginx/ssl"
    
    print_success "Prerequisites check passed"
}

# Function to validate environment configuration
validate_environment() {
    print_status "Validating environment configuration..."
    
    # Check for required environment variables
    source "$ENV_FILE"
    
    required_vars=(
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "SECRET_KEY"
        "JWT_SECRET"
        "OPENAI_API_KEY"
        "DOMAIN"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            print_error "Required environment variable $var is not set in $ENV_FILE"
            exit 1
        fi
    done
    
    # Check if secrets are not default values
    if [[ "$SECRET_KEY" == *"your_"* ]] || [[ "$JWT_SECRET" == *"your_"* ]]; then
        print_error "Please replace default secret values in $ENV_FILE"
        exit 1
    fi
    
    print_success "Environment validation passed"
}

# Function to setup SSL certificates
setup_ssl() {
    print_status "Setting up SSL certificates..."
    
    if [ ! -f "nginx/ssl/fullchain.pem" ] || [ ! -f "nginx/ssl/privkey.pem" ]; then
        print_warning "SSL certificates not found. You'll need to set them up manually."
        print_status "For Let's Encrypt certificates, run:"
        echo "sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
        echo "Then copy the certificates to nginx/ssl/ directory"
        
        read -p "Do you want to continue without SSL? (y/n): " continue_without_ssl
        if [[ $continue_without_ssl != [yY] ]]; then
            print_error "SSL setup required. Exiting."
            exit 1
        fi
    else
        print_success "SSL certificates found"
    fi
}

# Function to build and start services
deploy_services() {
    print_status "Building and starting services..."
    
    # Pull latest images
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull
    
    # Build custom images
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache
    
    # Start core services first
    print_status "Starting database services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d postgres redis chromadb
    
    # Wait for databases to be ready
    print_status "Waiting for databases to be ready..."
    sleep 30
    
    # Run database migrations
    print_status "Running database migrations..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T backend alembic upgrade head
    
    # Start application services
    print_status "Starting application services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d backend frontend nginx
    
    # Start optional services
    print_status "Starting monitoring services..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" --profile monitoring up -d
    
    print_success "Services deployed successfully"
}

# Function to verify deployment
verify_deployment() {
    print_status "Verifying deployment..."
    
    # Check if services are running
    services=("postgres" "redis" "chromadb" "backend" "frontend" "nginx")
    
    for service in "${services[@]}"; do
        if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps "$service" | grep -q "Up"; then
            print_success "$service is running"
        else
            print_error "$service is not running"
            docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs "$service"
            exit 1
        fi
    done
    
    # Test health endpoints
    print_status "Testing health endpoints..."
    
    # Wait for services to be fully ready
    sleep 30
    
    # Test backend health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend health check passed"
    else
        print_warning "Backend health check failed - service may still be starting"
    fi
    
    # Test frontend
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend health check passed"
    else
        print_warning "Frontend health check failed - service may still be starting"
    fi
    
    print_success "Deployment verification completed"
}

# Function to show deployment summary
show_summary() {
    print_success "🎉 Deployment completed successfully!"
    echo ""
    echo "📋 Deployment Summary:"
    echo "======================"
    echo "• Application URL: https://$DOMAIN"
    echo "• API Documentation: https://$DOMAIN/api/docs"
    echo "• Monitoring (if enabled): http://localhost:8080/grafana"
    echo ""
    echo "📊 Service Status:"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    echo ""
    echo "📝 Next Steps:"
    echo "1. Test the application functionality"
    echo "2. Set up monitoring alerts"
    echo "3. Configure backup schedules"
    echo "4. Review security settings"
    echo "5. Set up domain DNS if not done already"
    echo ""
    echo "🔧 Useful Commands:"
    echo "• View logs: docker-compose logs -f [service_name]"
    echo "• Restart service: docker-compose restart [service_name]"
    echo "• Update deployment: ./scripts/update.sh"
    echo "• Backup data: ./scripts/backup.sh"
    echo ""
}

# Function to handle cleanup on failure
cleanup_on_failure() {
    print_error "Deployment failed. Cleaning up..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    exit 1
}

# Main deployment function
main() {
    echo ""
    echo "🚀 Advanced RAG Research Ecosystem - Deployment"
    echo "==============================================="
    echo ""
    
    # Set trap for cleanup on failure
    trap cleanup_on_failure ERR
    
    # Run deployment steps
    check_prerequisites
    validate_environment
    setup_ssl
    deploy_services
    verify_deployment
    show_summary
    
    print_success "Deployment completed successfully! 🎉"
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "update")
        print_status "Updating deployment..."
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
        print_success "Update completed"
        ;;
    "stop")
        print_status "Stopping services..."
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
        print_success "Services stopped"
        ;;
    "restart")
        print_status "Restarting services..."
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart
        print_success "Services restarted"
        ;;
    "logs")
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f "${2:-}"
        ;;
    "status")
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
        ;;
    *)
        echo "Usage: $0 {deploy|update|stop|restart|logs|status}"
        echo ""
        echo "Commands:"
        echo "  deploy  - Full deployment (default)"
        echo "  update  - Update existing deployment"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  logs    - View logs (optionally specify service name)"
        echo "  status  - Show service status"
        exit 1
        ;;
esac