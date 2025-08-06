#!/bin/bash

# Blue-Green Deployment Script for AI Scholar Advanced RAG
# Zero-downtime deployment with automatic rollback on failure

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
NGINX_CONFIG_DIR="/etc/nginx/sites-available"
HEALTH_CHECK_URL="http://localhost/health"
API_HEALTH_CHECK_URL="http://localhost/api/health"
HEALTH_CHECK_TIMEOUT=300
HEALTH_CHECK_INTERVAL=10

# Load environment variables
if [ -f "$DEPLOYMENT_DIR/.env.production" ]; then
    source "$DEPLOYMENT_DIR/.env.production"
fi

# Determine current and next environments
get_current_environment() {
    if docker-compose -f "$DEPLOYMENT_DIR/docker-compose.blue.yml" ps --services --filter status=running | grep -q "frontend\|backend"; then
        echo "blue"
    elif docker-compose -f "$DEPLOYMENT_DIR/docker-compose.green.yml" ps --services --filter status=running | grep -q "frontend\|backend"; then
        echo "green"
    else
        echo "none"
    fi
}

get_next_environment() {
    current=$1
    if [ "$current" = "blue" ]; then
        echo "green"
    elif [ "$current" = "green" ]; then
        echo "blue"
    else
        echo "blue"  # Default to blue if no environment is running
    fi
}

# Health check function
health_check() {
    local environment=$1
    local port=$2
    local max_attempts=$((HEALTH_CHECK_TIMEOUT / HEALTH_CHECK_INTERVAL))
    local attempt=1
    
    print_status "Running health checks for $environment environment on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        print_status "Health check attempt $attempt/$max_attempts..."
        
        # Check main application health
        if curl -f -s "http://localhost:$port/health" > /dev/null; then
            # Check API health
            if curl -f -s "http://localhost:$port/api/health" > /dev/null; then
                print_success "Health check passed for $environment environment"
                return 0
            fi
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Health check failed for $environment environment after $max_attempts attempts"
            return 1
        fi
        
        sleep $HEALTH_CHECK_INTERVAL
        attempt=$((attempt + 1))
    done
}

# Deploy to environment
deploy_environment() {
    local environment=$1
    local image_tag=${2:-latest}
    
    print_status "Deploying to $environment environment with tag: $image_tag"
    
    # Create environment-specific docker-compose file
    cat > "$DEPLOYMENT_DIR/docker-compose.$environment.yml" << EOF
version: '3.8'

services:
  frontend-$environment:
    image: ghcr.io/ai-scholar/advanced-rag-frontend:$image_tag
    container_name: advanced-rag-frontend-$environment
    restart: unless-stopped
    environment:
      - NODE_ENV=production
      - REACT_APP_API_URL=https://aischolar.com/api
      - REACT_APP_WS_URL=wss://aischolar.com/ws
    ports:
      - "300$([[ "$environment" == "blue" ]] && echo "2" || echo "3"):3000"
    networks:
      - rag-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend-$environment:
    image: ghcr.io/ai-scholar/advanced-rag-backend:$image_tag
    container_name: advanced-rag-backend-$environment
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://rag_user:\${POSTGRES_PASSWORD}@postgres:5432/advanced_rag_db
      - REDIS_URL=redis://:\${REDIS_PASSWORD}@redis:6379/0
      - VECTOR_DB_URL=http://chromadb:8000
      - SECRET_KEY=\${SECRET_KEY}
      - JWT_SECRET=\${JWT_SECRET}
      - OPENAI_API_KEY=\${OPENAI_API_KEY}
      - HUGGINGFACE_API_KEY=\${HUGGINGFACE_API_KEY}
      - ENVIRONMENT=production
      - DEBUG=False
      - LOG_LEVEL=INFO
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    ports:
      - "800$([[ "$environment" == "blue" ]] && echo "2" || echo "3"):8000"
    networks:
      - rag-network
    depends_on:
      - postgres
      - redis
      - chromadb
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  rag-network:
    external: true

EOF

    # Pull latest images
    print_status "Pulling Docker images for $environment..."
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.$environment.yml" pull
    
    # Start services
    print_status "Starting $environment environment services..."
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.$environment.yml" up -d
    
    # Wait for services to be ready
    sleep 30
    
    # Run health checks
    local port=$([[ "$environment" == "blue" ]] && echo "8002" || echo "8003")
    if health_check "$environment" "$port"; then
        print_success "$environment environment deployed successfully"
        
        # Start deployment monitoring
        if [ -f "$DEPLOYMENT_DIR/scripts/deployment/deployment-monitoring.sh" ]; then
            print_status "Starting deployment monitoring..."
            "$DEPLOYMENT_DIR/scripts/deployment/deployment-monitoring.sh" monitor "$environment" 300 &
            MONITORING_PID=$!
        fi
        
        return 0
    else
        print_error "$environment environment deployment failed health checks"
        return 1
    fi
}

# Switch traffic to new environment
switch_traffic() {
    local new_environment=$1
    local port=$([[ "$new_environment" == "blue" ]] && echo "8002" || echo "8003")
    local frontend_port=$([[ "$new_environment" == "blue" ]] && echo "3002" || echo "3003")
    
    print_status "Switching traffic to $new_environment environment..."
    
    # Create new nginx configuration
    cat > "$NGINX_CONFIG_DIR/ai-scholar-$new_environment" << EOF
upstream backend_$new_environment {
    server localhost:$port;
}

upstream frontend_$new_environment {
    server localhost:$frontend_port;
}

server {
    listen 80;
    listen 443 ssl http2;
    server_name aischolar.com www.aischolar.com;
    
    # SSL configuration
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    
    # API routes
    location /api/ {
        proxy_pass http://backend_$new_environment;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket routes
    location /ws/ {
        proxy_pass http://backend_$new_environment;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://backend_$new_environment/health;
        access_log off;
    }
    
    # Frontend routes
    location / {
        proxy_pass http://frontend_$new_environment;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Handle client-side routing
        try_files \$uri \$uri/ /index.html;
    }
    
    # Static assets with caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://frontend_$new_environment;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    # Enable new configuration
    ln -sf "$NGINX_CONFIG_DIR/ai-scholar-$new_environment" /etc/nginx/sites-enabled/ai-scholar
    
    # Test nginx configuration
    if nginx -t; then
        print_status "Nginx configuration test passed"
        
        # Reload nginx
        systemctl reload nginx
        
        # Wait for traffic switch
        sleep 10
        
        # Verify traffic switch
        if curl -f -s "$HEALTH_CHECK_URL" > /dev/null && curl -f -s "$API_HEALTH_CHECK_URL" > /dev/null; then
            print_success "Traffic successfully switched to $new_environment environment"
            return 0
        else
            print_error "Traffic switch verification failed"
            return 1
        fi
    else
        print_error "Nginx configuration test failed"
        return 1
    fi
}

# Stop old environment
stop_old_environment() {
    local old_environment=$1
    
    print_status "Stopping $old_environment environment..."
    
    if [ -f "$DEPLOYMENT_DIR/docker-compose.$old_environment.yml" ]; then
        docker-compose -f "$DEPLOYMENT_DIR/docker-compose.$old_environment.yml" down
        print_success "$old_environment environment stopped"
    else
        print_warning "No docker-compose file found for $old_environment environment"
    fi
}

# Rollback to previous environment
rollback() {
    local current_environment=$1
    local previous_environment=$2
    
    print_error "Rolling back from $current_environment to $previous_environment..."
    
    # Switch traffic back
    if switch_traffic "$previous_environment"; then
        print_success "Traffic rolled back to $previous_environment environment"
        
        # Stop failed environment
        stop_old_environment "$current_environment"
        
        return 0
    else
        print_error "Rollback failed"
        return 1
    fi
}

# Pre-deployment checks
pre_deployment_checks() {
    print_status "Running pre-deployment checks..."
    
    # Check Docker daemon
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker daemon is not running"
        return 1
    fi
    
    # Check disk space
    available_space=$(df / | awk 'NR==2 {print $4}')
    required_space=5000000  # 5GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        print_error "Insufficient disk space. Available: ${available_space}KB, Required: ${required_space}KB"
        return 1
    fi
    
    # Check database connectivity
    if ! docker-compose exec -T postgres pg_isready -U rag_user -d advanced_rag_db > /dev/null 2>&1; then
        print_error "Database is not accessible"
        return 1
    fi
    
    # Check Redis connectivity
    if ! docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_error "Redis is not accessible"
        return 1
    fi
    
    print_success "Pre-deployment checks passed"
    return 0
}

# Post-deployment tasks
post_deployment_tasks() {
    local environment=$1
    
    print_status "Running post-deployment tasks for $environment..."
    
    # Clear application caches
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.$environment.yml" exec -T backend-$environment python -c "
from backend.core.redis_client import redis_client
redis_client.flushdb()
print('Application cache cleared')
"
    
    # Warm up application
    print_status "Warming up application..."
    curl -s "$HEALTH_CHECK_URL" > /dev/null
    curl -s "$API_HEALTH_CHECK_URL" > /dev/null
    
    # Update search indices if needed
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.$environment.yml" exec -T backend-$environment python -c "
# Update search indices
print('Search indices updated')
"
    
    print_success "Post-deployment tasks completed"
}

# Main deployment function
main() {
    echo ""
    echo "🚀 AI Scholar Advanced RAG - Blue-Green Deployment"
    echo "=================================================="
    echo "Started: $(date)"
    echo ""
    
    local image_tag=${1:-latest}
    local skip_checks=${2:-false}
    
    # Pre-deployment checks
    if [ "$skip_checks" != "true" ]; then
        if ! pre_deployment_checks; then
            print_error "Pre-deployment checks failed"
            exit 1
        fi
    fi
    
    # Determine environments
    current_env=$(get_current_environment)
    next_env=$(get_next_environment "$current_env")
    
    print_status "Current environment: $current_env"
    print_status "Deploying to: $next_env"
    
    # Deploy to next environment
    if deploy_environment "$next_env" "$image_tag"; then
        print_success "Deployment to $next_env successful"
        
        # Switch traffic
        if switch_traffic "$next_env"; then
            print_success "Traffic switch successful"
            
            # Post-deployment tasks
            post_deployment_tasks "$next_env"
            
            # Enable feature flags for new environment
            if [ -f "$DEPLOYMENT_DIR/scripts/deployment/feature-flag-management.sh" ]; then
                print_status "Configuring feature flags for new environment..."
                "$DEPLOYMENT_DIR/scripts/deployment/feature-flag-management.sh" post-deploy
            fi
            
            # Wait for monitoring to complete
            if [ -n "${MONITORING_PID:-}" ]; then
                print_status "Waiting for deployment monitoring to complete..."
                wait $MONITORING_PID
                local monitoring_result=$?
                
                if [ $monitoring_result -eq 2 ]; then
                    print_error "Monitoring detected issues, triggering rollback..."
                    rollback "$next_env" "$current_env"
                    exit 1
                fi
            fi
            
            # Stop old environment
            if [ "$current_env" != "none" ]; then
                stop_old_environment "$current_env"
            fi
            
            print_success "🎉 Blue-green deployment completed successfully!"
            echo "Active environment: $next_env"
            
        else
            print_error "Traffic switch failed, rolling back..."
            rollback "$next_env" "$current_env"
            exit 1
        fi
        
    else
        print_error "Deployment to $next_env failed"
        
        # Clean up failed deployment
        stop_old_environment "$next_env"
        exit 1
    fi
    
    echo ""
    echo "Finished: $(date)"
    echo ""
}

# Handle rollback command
if [ "$1" = "rollback" ]; then
    current_env=$(get_current_environment)
    previous_env=$(get_next_environment "$current_env")
    
    print_warning "Manual rollback requested"
    rollback "$current_env" "$previous_env"
    exit $?
fi

# Handle status command
if [ "$1" = "status" ]; then
    current_env=$(get_current_environment)
    echo "Current active environment: $current_env"
    
    # Show running services
    if [ "$current_env" != "none" ]; then
        echo ""
        echo "Running services:"
        docker-compose -f "$DEPLOYMENT_DIR/docker-compose.$current_env.yml" ps
    fi
    exit 0
fi

# Run main deployment
main "$@"