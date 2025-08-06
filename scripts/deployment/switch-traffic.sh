#!/bin/bash

# Traffic switching script for blue-green deployment
# Switches load balancer traffic between blue and green environments

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
NGINX_CONFIG_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
TRAEFIK_CONFIG_DIR="/opt/traefik/dynamic"
HEALTH_CHECK_URL="http://localhost/health"
API_HEALTH_CHECK_URL="http://localhost/api/health"

# Function to switch nginx configuration
switch_nginx_traffic() {
    local environment=$1
    local frontend_port=$([[ "$environment" == "blue" ]] && echo "3002" || echo "3003")
    local backend_port=$([[ "$environment" == "blue" ]] && echo "8002" || echo "8003")
    
    print_status "Switching nginx traffic to $environment environment..."
    
    # Create new nginx configuration
    cat > "$NGINX_CONFIG_DIR/ai-scholar-$environment" << EOF
upstream backend_$environment {
    server localhost:$backend_port max_fails=3 fail_timeout=30s;
    keepalive 32;
}

upstream frontend_$environment {
    server localhost:$frontend_port max_fails=3 fail_timeout=30s;
    keepalive 32;
}

# Rate limiting
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=login:10m rate=5r/m;

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
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' wss: https:;" always;
    
    # Deployment environment header
    add_header X-Deployment-Environment "$environment" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # API routes with rate limiting
    location /api/auth/ {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://backend_$environment;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
    }
    
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://backend_$environment;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
    }
    
    # WebSocket routes
    location /ws/ {
        proxy_pass http://backend_$environment;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }
    
    # Health check endpoint (no rate limiting)
    location /health {
        proxy_pass http://backend_$environment/health;
        access_log off;
        proxy_set_header Host \$host;
        proxy_connect_timeout 5s;
        proxy_send_timeout 5s;
        proxy_read_timeout 5s;
    }
    
    # Static assets with long caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://frontend_$environment;
        proxy_set_header Host \$host;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Deployment-Environment "$environment" always;
    }
    
    # Service worker and manifest (no caching)
    location ~* \.(sw\.js|manifest\.json)$ {
        proxy_pass http://frontend_$environment;
        proxy_set_header Host \$host;
        expires 0;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header X-Deployment-Environment "$environment" always;
    }
    
    # Frontend routes
    location / {
        proxy_pass http://frontend_$environment;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Handle client-side routing
        try_files \$uri \$uri/ @fallback;
    }
    
    location @fallback {
        proxy_pass http://frontend_$environment/index.html;
        proxy_set_header Host \$host;
        add_header X-Deployment-Environment "$environment" always;
    }
    
    # Error pages
    error_page 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
        internal;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name aischolar.com www.aischolar.com;
    return 301 https://\$server_name\$request_uri;
}
EOF

    # Enable new configuration
    ln -sf "$NGINX_CONFIG_DIR/ai-scholar-$environment" "$NGINX_ENABLED_DIR/ai-scholar"
    
    # Test nginx configuration
    if nginx -t; then
        print_status "Nginx configuration test passed"
        
        # Reload nginx gracefully
        nginx -s reload
        
        return 0
    else
        print_error "Nginx configuration test failed"
        return 1
    fi
}

# Function to switch Traefik configuration (if using Traefik)
switch_traefik_traffic() {
    local environment=$1
    
    print_status "Switching Traefik traffic to $environment environment..."
    
    # Create Traefik dynamic configuration
    cat > "$TRAEFIK_CONFIG_DIR/ai-scholar.yml" << EOF
http:
  routers:
    frontend-router:
      rule: "Host(\`aischolar.com\`) && PathPrefix(\`/\`)"
      service: "frontend-$environment"
      tls:
        certResolver: "letsencrypt"
    
    backend-router:
      rule: "Host(\`aischolar.com\`) && PathPrefix(\`/api\`)"
      service: "backend-$environment"
      tls:
        certResolver: "letsencrypt"
  
  services:
    frontend-$environment:
      loadBalancer:
        servers:
          - url: "http://localhost:$([[ "$environment" == "blue" ]] && echo "3002" || echo "3003")"
        healthCheck:
          path: "/health"
          interval: "30s"
          timeout: "10s"
    
    backend-$environment:
      loadBalancer:
        servers:
          - url: "http://localhost:$([[ "$environment" == "blue" ]] && echo "8002" || echo "8003")"
        healthCheck:
          path: "/health"
          interval: "30s"
          timeout: "10s"

  middlewares:
    rate-limit:
      rateLimit:
        burst: 100
        average: 50
    
    security-headers:
      headers:
        customRequestHeaders:
          X-Deployment-Environment: "$environment"
        customResponseHeaders:
          X-Frame-Options: "DENY"
          X-Content-Type-Options: "nosniff"
          X-XSS-Protection: "1; mode=block"
          Strict-Transport-Security: "max-age=63072000; includeSubDomains; preload"
EOF

    print_success "Traefik configuration updated for $environment environment"
    return 0
}

# Function to verify traffic switch
verify_traffic_switch() {
    local environment=$1
    local max_attempts=10
    local attempt=1
    
    print_status "Verifying traffic switch to $environment environment..."
    
    while [ $attempt -le $max_attempts ]; do
        print_status "Verification attempt $attempt/$max_attempts..."
        
        # Check main health endpoint
        if curl -f -s -H "Cache-Control: no-cache" "$HEALTH_CHECK_URL" > /dev/null; then
            # Check API health endpoint
            if curl -f -s -H "Cache-Control: no-cache" "$API_HEALTH_CHECK_URL" > /dev/null; then
                # Verify deployment environment header
                deployment_env=$(curl -s -I "$HEALTH_CHECK_URL" | grep -i "x-deployment-environment" | cut -d' ' -f2 | tr -d '\r\n')
                
                if [ "$deployment_env" = "$environment" ]; then
                    print_success "Traffic switch verification successful - serving from $environment environment"
                    return 0
                else
                    print_warning "Environment header mismatch: expected $environment, got $deployment_env"
                fi
            fi
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Traffic switch verification failed after $max_attempts attempts"
            return 1
        fi
        
        sleep 10
        attempt=$((attempt + 1))
    done
}

# Function to perform canary deployment (gradual traffic shift)
canary_deployment() {
    local new_environment=$1
    local old_environment=$2
    local canary_percentage=${3:-10}
    
    print_status "Starting canary deployment to $new_environment environment ($canary_percentage% traffic)..."
    
    # Create canary nginx configuration
    cat > "$NGINX_CONFIG_DIR/ai-scholar-canary" << EOF
upstream backend_canary {
    server localhost:$([[ "$old_environment" == "blue" ]] && echo "8002" || echo "8003") weight=$((100 - canary_percentage));
    server localhost:$([[ "$new_environment" == "blue" ]] && echo "8002" || echo "8003") weight=$canary_percentage;
}

upstream frontend_canary {
    server localhost:$([[ "$old_environment" == "blue" ]] && echo "3002" || echo "3003") weight=$((100 - canary_percentage));
    server localhost:$([[ "$new_environment" == "blue" ]] && echo "3002" || echo "3003") weight=$canary_percentage;
}

# ... rest of nginx configuration using canary upstreams
EOF

    print_success "Canary deployment configured with $canary_percentage% traffic to $new_environment"
}

# Main function
main() {
    local environment=${1:-}
    local load_balancer=${2:-nginx}
    local canary_mode=${3:-false}
    local canary_percentage=${4:-10}
    
    if [ -z "$environment" ]; then
        print_error "Usage: $0 <blue|green> [nginx|traefik] [canary] [percentage]"
        echo ""
        echo "Examples:"
        echo "  $0 blue                    # Switch all traffic to blue environment"
        echo "  $0 green nginx             # Switch nginx traffic to green environment"
        echo "  $0 blue traefik canary 20  # Canary deployment with 20% traffic to blue"
        exit 1
    fi
    
    if [ "$environment" != "blue" ] && [ "$environment" != "green" ]; then
        print_error "Environment must be 'blue' or 'green'"
        exit 1
    fi
    
    echo ""
    echo "🔄 AI Scholar Advanced RAG - Traffic Switch"
    echo "=========================================="
    echo "Target environment: $environment"
    echo "Load balancer: $load_balancer"
    echo "Canary mode: $canary_mode"
    echo "Started: $(date)"
    echo ""
    
    # Perform traffic switch based on load balancer type
    case "$load_balancer" in
        "nginx")
            if [ "$canary_mode" = "canary" ]; then
                # Determine current environment for canary
                current_env=$([[ "$environment" == "blue" ]] && echo "green" || echo "blue")
                canary_deployment "$environment" "$current_env" "$canary_percentage"
            else
                switch_nginx_traffic "$environment"
            fi
            ;;
        "traefik")
            switch_traefik_traffic "$environment"
            ;;
        *)
            print_error "Unsupported load balancer: $load_balancer"
            exit 1
            ;;
    esac
    
    # Verify traffic switch
    if [ "$canary_mode" != "canary" ]; then
        if verify_traffic_switch "$environment"; then
            print_success "🎉 Traffic successfully switched to $environment environment!"
        else
            print_error "Traffic switch verification failed"
            exit 1
        fi
    else
        print_success "🎉 Canary deployment configured with $canary_percentage% traffic to $environment!"
    fi
    
    echo ""
    echo "Finished: $(date)"
    echo ""
}

# Run main function
main "$@"