#!/bin/bash
# Complete Nginx Reverse Proxy Setup for AI Scholar
# Supports both development and production environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Configuration variables
DOMAIN=${1:-localhost}
ENVIRONMENT=${2:-development}
NGINX_USER=${NGINX_USER:-nginx}
NGINX_GROUP=${NGINX_GROUP:-nginx}

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    NGINX_USER="_www"
    NGINX_GROUP="_www"
    NGINX_CONF_DIR="/usr/local/etc/nginx"
    NGINX_LOG_DIR="/usr/local/var/log/nginx"
elif [[ -f /etc/debian_version ]]; then
    OS="debian"
    NGINX_USER="www-data"
    NGINX_GROUP="www-data"
    NGINX_CONF_DIR="/etc/nginx"
    NGINX_LOG_DIR="/var/log/nginx"
elif [[ -f /etc/redhat-release ]]; then
    OS="redhat"
    NGINX_CONF_DIR="/etc/nginx"
    NGINX_LOG_DIR="/var/log/nginx"
else
    OS="unknown"
    NGINX_CONF_DIR="/etc/nginx"
    NGINX_LOG_DIR="/var/log/nginx"
fi

echo -e "${BLUE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║                    AI Scholar Nginx Setup                    ║
║                   Reverse Proxy Configuration                ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

info "Detected OS: $OS"
info "Domain: $DOMAIN"
info "Environment: $ENVIRONMENT"
info "Nginx user: $NGINX_USER"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    error "This script must be run as root (use sudo)"
fi

# Install nginx if not present
log "Checking nginx installation..."
if ! command -v nginx &> /dev/null; then
    log "Installing nginx..."
    case $OS in
        "debian")
            apt update && apt install -y nginx
            ;;
        "redhat")
            yum install -y nginx || dnf install -y nginx
            ;;
        "macos")
            if command -v brew &> /dev/null; then
                brew install nginx
            else
                error "Please install Homebrew first: https://brew.sh"
            fi
            ;;
        *)
            error "Unsupported OS. Please install nginx manually."
            ;;
    esac
else
    log "Nginx is already installed"
fi

# Create necessary directories
log "Creating nginx directories..."
mkdir -p $NGINX_CONF_DIR/sites-available
mkdir -p $NGINX_CONF_DIR/sites-enabled
mkdir -p $NGINX_CONF_DIR/ssl
mkdir -p $NGINX_CONF_DIR/conf.d
mkdir -p $NGINX_LOG_DIR
mkdir -p /var/www/html
mkdir -p /var/www/certbot

# Set proper ownership
chown -R $NGINX_USER:$NGINX_GROUP $NGINX_LOG_DIR
chown -R $NGINX_USER:$NGINX_GROUP /var/www/html

# Backup existing configuration
if [[ -f "$NGINX_CONF_DIR/nginx.conf" ]]; then
    log "Backing up existing nginx.conf..."
    cp "$NGINX_CONF_DIR/nginx.conf" "$NGINX_CONF_DIR/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Create optimized nginx.conf
log "Creating optimized nginx.conf..."
cat > "$NGINX_CONF_DIR/nginx.conf" << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /var/run/nginx.pid;

# Load dynamic modules
include /etc/nginx/modules-enabled/*.conf;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    # Basic settings
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    log_format json escape=json '{'
        '"timestamp":"$time_iso8601",'
        '"remote_addr":"$remote_addr",'
        '"method":"$request_method",'
        '"uri":"$request_uri",'
        '"status":$status,'
        '"body_bytes_sent":$body_bytes_sent,'
        '"request_time":$request_time,'
        '"upstream_response_time":"$upstream_response_time",'
        '"user_agent":"$http_user_agent",'
        '"referer":"$http_referer"'
    '}';

    access_log /var/log/nginx/access.log json;

    # Performance settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;
    client_max_body_size 100M;

    # Buffer settings
    client_body_buffer_size 128k;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    output_buffers 1 32k;
    postpone_output 1460;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json
        application/xml
        image/svg+xml
        application/x-font-ttf
        font/opentype;

    # Security headers (global)
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
    limit_req_zone $binary_remote_addr zone=general:10m rate=5r/s;

    # Connection limiting
    limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10m;
    limit_conn conn_limit_per_ip 20;

    # Upstream definitions
    upstream ai_scholar_backend {
        server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    upstream ai_scholar_frontend {
        server 127.0.0.1:3006 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    upstream ai_scholar_chromadb {
        server 127.0.0.1:8081 max_fails=3 fail_timeout=30s;
        keepalive 8;
    }

    upstream ai_scholar_ollama {
        server 127.0.0.1:11435 max_fails=3 fail_timeout=30s;
        keepalive 8;
    }

    # Include site configurations
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
EOF

# Update nginx.conf for detected OS
if [[ "$OS" == "macos" ]]; then
    sed -i '' "s|user nginx;|user $NGINX_USER;|g" "$NGINX_CONF_DIR/nginx.conf"
    sed -i '' "s|/var/log/nginx/|$NGINX_LOG_DIR/|g" "$NGINX_CONF_DIR/nginx.conf"
elif [[ "$OS" == "debian" ]]; then
    sed -i "s|user nginx;|user $NGINX_USER;|g" "$NGINX_CONF_DIR/nginx.conf"
fi

# Create AI Scholar site configuration
log "Creating AI Scholar site configuration..."
cat > "$NGINX_CONF_DIR/sites-available/ai-scholar" << EOF
# AI Scholar Application Configuration
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    # Let's Encrypt challenge location
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
        try_files \$uri =404;
    }

    # Redirect all other HTTP traffic to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN;

    # SSL configuration
    ssl_certificate $NGINX_CONF_DIR/ssl/fullchain.pem;
    ssl_certificate_key $NGINX_CONF_DIR/ssl/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS (optional, uncomment for production)
    # add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Frontend application (main site)
    location / {
        limit_req zone=general burst=10 nodelay;
        
        proxy_pass http://ai_scholar_frontend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Error handling
        proxy_intercept_errors on;
        error_page 502 503 504 /50x.html;
    }

    # Backend API
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://ai_scholar_backend/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        
        # WebSocket support for real-time features
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Extended timeouts for AI processing
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Buffer settings for large responses
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # Authentication endpoints (stricter rate limiting)
    location ~ ^/api/(auth|login|register) {
        limit_req zone=login burst=5 nodelay;
        
        proxy_pass http://ai_scholar_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Shorter timeouts for auth
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # WebSocket endpoint
    location /ws/ {
        proxy_pass http://ai_scholar_backend/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Long timeouts for WebSocket connections
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_connect_timeout 60s;
    }

    # ChromaDB API (if exposing directly)
    location /chromadb/ {
        limit_req zone=api burst=10 nodelay;
        
        proxy_pass http://ai_scholar_chromadb/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS headers for ChromaDB
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        
        if (\$request_method = 'OPTIONS') {
            return 204;
        }
    }

    # Ollama API (if exposing directly)
    location /ollama/ {
        limit_req zone=api burst=5 nodelay;
        
        proxy_pass http://ai_scholar_ollama/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Extended timeouts for LLM processing
        proxy_connect_timeout 60s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    # Static files with aggressive caching
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|webp)\$ {
        proxy_pass http://ai_scholar_frontend;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header Vary Accept-Encoding;
        
        # Optional: serve from local cache if available
        # try_files \$uri @frontend;
    }

    # Health check endpoints
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }

    # Nginx status (for monitoring)
    location /nginx-status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        allow ::1;
        deny all;
    }

    # Error pages
    location = /50x.html {
        root /var/www/html;
        internal;
    }

    # Security.txt
    location /.well-known/security.txt {
        return 200 "Contact: security@$DOMAIN\\nExpires: 2025-12-31T23:59:59.000Z\\n";
        add_header Content-Type text/plain;
    }

    # Deny access to hidden files
    location ~ /\\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

# Create error page
log "Creating error page..."
cat > "/var/www/html/50x.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>AI Scholar - Service Temporarily Unavailable</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        h1 { color: #333; }
        p { color: #666; }
    </style>
</head>
<body>
    <h1>Service Temporarily Unavailable</h1>
    <p>AI Scholar is currently undergoing maintenance. Please try again in a few moments.</p>
</body>
</html>
EOF

# Generate SSL certificate
log "Generating SSL certificate..."
if [[ "$ENVIRONMENT" == "production" && "$DOMAIN" != "localhost" ]]; then
    warn "For production, you should use Let's Encrypt. Run: ./nginx-ssl-setup.sh --production --domain $DOMAIN"
fi

# Generate self-signed certificate for development
openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
    -keyout "$NGINX_CONF_DIR/ssl/privkey.pem" \
    -out "$NGINX_CONF_DIR/ssl/fullchain.pem" \
    -subj "/C=US/ST=State/L=City/O=AI Scholar/CN=$DOMAIN" \
    -addext "subjectAltName=DNS:$DOMAIN,DNS:*.$DOMAIN,IP:127.0.0.1"

# Set proper permissions for SSL files
chmod 600 "$NGINX_CONF_DIR/ssl/privkey.pem"
chmod 644 "$NGINX_CONF_DIR/ssl/fullchain.pem"
chown $NGINX_USER:$NGINX_GROUP "$NGINX_CONF_DIR/ssl/"*

# Enable the site
log "Enabling AI Scholar site..."
if [[ -L "$NGINX_CONF_DIR/sites-enabled/ai-scholar" ]]; then
    rm "$NGINX_CONF_DIR/sites-enabled/ai-scholar"
fi
ln -s "$NGINX_CONF_DIR/sites-available/ai-scholar" "$NGINX_CONF_DIR/sites-enabled/ai-scholar"

# Disable default site if it exists
if [[ -L "$NGINX_CONF_DIR/sites-enabled/default" ]]; then
    log "Disabling default site..."
    rm "$NGINX_CONF_DIR/sites-enabled/default"
fi

# Test nginx configuration
log "Testing nginx configuration..."
if nginx -t; then
    log "✅ Nginx configuration is valid"
else
    error "❌ Nginx configuration test failed"
fi

# Start/restart nginx
log "Starting nginx..."
case $OS in
    "macos")
        if pgrep nginx > /dev/null; then
            nginx -s reload
        else
            nginx
        fi
        ;;
    *)
        systemctl enable nginx
        systemctl restart nginx
        ;;
esac

# Verify nginx is running
sleep 2
if pgrep nginx > /dev/null; then
    log "✅ Nginx is running"
else
    error "❌ Failed to start nginx"
fi

echo
echo -e "${GREEN}🎉 Nginx Reverse Proxy Setup Complete! 🎉${NC}"
echo
echo -e "${BLUE}=== Configuration Summary ===${NC}"
echo -e "Domain: ${GREEN}$DOMAIN${NC}"
echo -e "Environment: ${GREEN}$ENVIRONMENT${NC}"
echo -e "Config file: ${GREEN}$NGINX_CONF_DIR/sites-available/ai-scholar${NC}"
echo -e "SSL certificate: ${GREEN}$NGINX_CONF_DIR/ssl/fullchain.pem${NC}"
echo
echo -e "${BLUE}=== Access URLs ===${NC}"
echo -e "Main app: ${GREEN}https://$DOMAIN${NC}"
echo -e "API: ${GREEN}https://$DOMAIN/api/${NC}"
echo -e "Health check: ${GREEN}https://$DOMAIN/health${NC}"
echo -e "Nginx status: ${GREEN}https://$DOMAIN/nginx-status${NC} (localhost only)"
echo
echo -e "${BLUE}=== Next Steps ===${NC}"
echo "1. Start your AI Scholar services:"
echo "   ./deploy-with-ai-services.sh"
echo
echo "2. Test the configuration:"
echo "   ./test-nginx-config.sh"
echo
echo "3. For production SSL:"
echo "   ./nginx-ssl-setup.sh --production --domain $DOMAIN"
echo
echo -e "${YELLOW}Note: Make sure your AI Scholar services are running on the expected ports:${NC}"
echo "  - Frontend: http://localhost:3006"
echo "  - Backend: http://localhost:8001"
echo "  - ChromaDB: http://localhost:8081"
echo "  - Ollama: http://localhost:11435"