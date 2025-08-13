#!/bin/bash
# SSL Certificate Setup Script for AI Scholar

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

# Check if domain is provided
if [ -z "$1" ]; then
    error "Usage: $0 <domain-name> [email]"
fi

DOMAIN=$1
EMAIL=${2:-admin@$DOMAIN}

log "Setting up SSL certificate for domain: $DOMAIN"

# Check if running in the correct directory
if [ ! -f "docker-compose.prod.yml" ]; then
    error "Please run this script from the AI Scholar project directory"
fi

# Update environment file with domain
log "Updating environment configuration..."
sed -i "s/DOMAIN_NAME=.*/DOMAIN_NAME=$DOMAIN/" .env
sed -i "s/SSL_EMAIL=.*/SSL_EMAIL=$EMAIL/" .env
sed -i "s|VITE_API_URL=.*|VITE_API_URL=https://$DOMAIN/api|" .env
sed -i "s|VITE_WS_URL=.*|VITE_WS_URL=wss://$DOMAIN/ws|" .env
sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN|" .env

# Ensure nginx is running
log "Starting nginx service..."
docker-compose -f docker-compose.prod.yml up -d nginx

# Wait for nginx to be ready
sleep 10

# Test domain accessibility
log "Testing domain accessibility..."
if ! curl -f http://$DOMAIN/.well-known/acme-challenge/ >/dev/null 2>&1; then
    warn "Domain $DOMAIN may not be properly configured or accessible"
    warn "Make sure your DNS points to this server and port 80 is open"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Request SSL certificate using Let's Encrypt
log "Requesting SSL certificate from Let's Encrypt..."
docker-compose -f docker-compose.prod.yml --profile ssl run --rm certbot \
    certonly --webroot --webroot-path=/var/www/certbot \
    --email $EMAIL --agree-tos --no-eff-email \
    -d $DOMAIN -d www.$DOMAIN

# Check if certificate was created
if [ ! -f "./ssl/live/$DOMAIN/fullchain.pem" ]; then
    # Copy certificates from certbot container
    log "Copying SSL certificates..."
    docker cp $(docker-compose -f docker-compose.prod.yml --profile ssl ps -q certbot):/etc/letsencrypt/live/$DOMAIN/fullchain.pem ./ssl/
    docker cp $(docker-compose -f docker-compose.prod.yml --profile ssl ps -q certbot):/etc/letsencrypt/live/$DOMAIN/privkey.pem ./ssl/
fi

# Update nginx configuration for SSL
log "Updating nginx configuration for SSL..."
cat > config/nginx/ssl.conf << EOF
# SSL Configuration for $DOMAIN
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    # SSL configuration
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Frontend
    location / {
        proxy_pass http://frontend:3000;
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
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend:8000/;
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
        
        # Timeouts for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # WebSocket endpoint
    location /ws/ {
        proxy_pass http://backend:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket specific timeouts
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # Health check endpoints
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }

    # Static files with caching
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
        proxy_pass http://frontend:3000;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header Vary Accept-Encoding;
    }
}
EOF

# Restart nginx to apply SSL configuration
log "Restarting nginx with SSL configuration..."
docker-compose -f docker-compose.prod.yml restart nginx

# Set up certificate renewal
log "Setting up automatic certificate renewal..."
cat > scripts/renew-ssl.sh << 'EOF'
#!/bin/bash
# SSL Certificate Renewal Script

set -e

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting SSL certificate renewal..."

# Renew certificates
docker-compose -f docker-compose.prod.yml --profile ssl run --rm certbot renew

# Reload nginx if certificates were renewed
if [ $? -eq 0 ]; then
    log "Certificates renewed successfully, reloading nginx..."
    docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
    log "Nginx reloaded successfully"
else
    log "Certificate renewal failed or not needed"
fi

log "SSL certificate renewal completed"
EOF

chmod +x scripts/renew-ssl.sh

# Add cron job for automatic renewal
log "Adding cron job for automatic certificate renewal..."
(crontab -l 2>/dev/null; echo "0 12 * * * /opt/ai-scholar/scripts/renew-ssl.sh >> /opt/ai-scholar/logs/ssl-renewal.log 2>&1") | crontab -

# Test SSL configuration
log "Testing SSL configuration..."
sleep 10

if curl -f https://$DOMAIN/health >/dev/null 2>&1; then
    log "SSL configuration successful!"
    echo
    echo -e "${GREEN}=== SSL SETUP COMPLETED ===${NC}"
    echo -e "Your site is now accessible at: ${GREEN}https://$DOMAIN${NC}"
    echo -e "SSL certificate will auto-renew via cron job"
    echo
    echo -e "${BLUE}=== SSL CERTIFICATE INFO ===${NC}"
    openssl x509 -in ./ssl/fullchain.pem -text -noout | grep -E "(Subject:|Issuer:|Not Before:|Not After:)"
else
    error "SSL configuration failed. Please check the logs and try again."
fi

log "SSL setup completed successfully!"