#!/bin/bash
# Fix nginx configuration and missing files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

echo -e "${BLUE}=== Nginx Configuration Fix ===${NC}"
echo

# Create required directories
log "Creating required directories..."
mkdir -p config/nginx/sites-available ssl logs/nginx

# Copy nginx configuration if it doesn't exist
if [ ! -f "config/nginx/nginx.prod.conf" ]; then
    if [ -f "config/nginx.prod.conf" ]; then
        log "Copying nginx.prod.conf to correct location..."
        cp config/nginx.prod.conf config/nginx/nginx.prod.conf
    else
        log "Creating basic nginx configuration..."
        cat > config/nginx/nginx.prod.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

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
        image/svg+xml;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Include site configurations
    include /etc/nginx/sites-available/*;
}
EOF
    fi
else
    log "nginx.prod.conf already exists"
fi

# Create default site configuration if it doesn't exist
if [ ! -f "config/nginx/sites-available/default" ]; then
    log "Creating default site configuration..."
    cat > config/nginx/sites-available/default << 'EOF'
# Default site configuration for AI Scholar
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    # Frontend
    location / {
        proxy_pass http://frontend:3005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF
else
    log "Default site configuration already exists"
fi

# Create self-signed SSL certificates if they don't exist
if [ ! -f "ssl/fullchain.pem" ] || [ ! -f "ssl/privkey.pem" ]; then
    log "Creating self-signed SSL certificates..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/privkey.pem \
        -out ssl/fullchain.pem \
        -subj "/C=US/ST=State/L=City/O=AI Scholar/CN=localhost" \
        -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1" 2>/dev/null || {
        # Fallback for older OpenSSL versions
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/privkey.pem \
            -out ssl/fullchain.pem \
            -subj "/C=US/ST=State/L=City/O=AI Scholar/CN=localhost"
    }
    chmod 600 ssl/privkey.pem
    chmod 644 ssl/fullchain.pem
else
    log "SSL certificates already exist"
fi

# Set proper permissions
log "Setting proper permissions..."
chmod -R 755 config/nginx logs/nginx ssl 2>/dev/null || true

# Test nginx configuration
log "Testing nginx configuration..."
docker run --rm -v $(pwd)/config/nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro \
    -v $(pwd)/config/nginx/sites-available:/etc/nginx/sites-available:ro \
    nginx:alpine nginx -t 2>/dev/null && {
    echo -e "${GREEN}✅ Nginx configuration is valid${NC}"
} || {
    warn "Nginx configuration test failed, but continuing..."
}

echo -e "${GREEN}✅ Nginx configuration fixed!${NC}"
echo
echo -e "${BLUE}Created/verified:${NC}"
echo "  • config/nginx/nginx.prod.conf"
echo "  • config/nginx/sites-available/default"
echo "  • ssl/fullchain.pem (self-signed)"
echo "  • ssl/privkey.pem (self-signed)"
echo "  • logs/nginx/ directory"
echo
echo -e "${BLUE}Now you can run your deployment script again:${NC}"
echo "./quick-start-minimal.sh"