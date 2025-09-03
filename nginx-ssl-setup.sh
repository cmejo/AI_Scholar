#!/bin/bash
# SSL Certificate Setup for Nginx
# Supports both self-signed (development) and Let's Encrypt (production)

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

# Default values
MODE="development"
DOMAIN="localhost"
EMAIL=""
NGINX_CONF_DIR="/etc/nginx"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --production)
            MODE="production"
            shift
            ;;
        --dev|--development)
            MODE="development"
            shift
            ;;
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --email)
            EMAIL="$2"
            shift 2
            ;;
        --nginx-dir)
            NGINX_CONF_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --production          Use Let's Encrypt for production SSL"
            echo "  --dev, --development  Use self-signed certificate (default)"
            echo "  --domain DOMAIN       Domain name (default: localhost)"
            echo "  --email EMAIL         Email for Let's Encrypt registration"
            echo "  --nginx-dir DIR       Nginx configuration directory"
            echo "  -h, --help           Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Detect OS and adjust paths
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    NGINX_CONF_DIR="/usr/local/etc/nginx"
elif [[ -f /etc/debian_version ]]; then
    OS="debian"
elif [[ -f /etc/redhat-release ]]; then
    OS="redhat"
else
    OS="unknown"
fi

echo -e "${BLUE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║                    SSL Certificate Setup                     ║
║                     for AI Scholar Nginx                     ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

info "Mode: $MODE"
info "Domain: $DOMAIN"
info "OS: $OS"
info "Nginx config dir: $NGINX_CONF_DIR"

# Check if running as root (except on macOS)
if [[ "$OS" != "macos" && $EUID -ne 0 ]]; then
    error "This script must be run as root (use sudo)"
fi

# Create SSL directory
log "Creating SSL directory..."
mkdir -p "$NGINX_CONF_DIR/ssl"

if [[ "$MODE" == "production" ]]; then
    # Production SSL with Let's Encrypt
    log "Setting up Let's Encrypt SSL certificate..."
    
    if [[ "$DOMAIN" == "localhost" ]]; then
        error "Cannot use Let's Encrypt with localhost. Please specify a real domain with --domain"
    fi
    
    if [[ -z "$EMAIL" ]]; then
        error "Email is required for Let's Encrypt. Use --email your@email.com"
    fi
    
    # Install certbot if not present
    if ! command -v certbot &> /dev/null; then
        log "Installing certbot..."
        case $OS in
            "debian")
                apt update && apt install -y certbot python3-certbot-nginx
                ;;
            "redhat")
                yum install -y certbot python3-certbot-nginx || dnf install -y certbot python3-certbot-nginx
                ;;
            "macos")
                if command -v brew &> /dev/null; then
                    brew install certbot
                else
                    error "Please install Homebrew first: https://brew.sh"
                fi
                ;;
            *)
                error "Unsupported OS for automatic certbot installation"
                ;;
        esac
    fi
    
    # Stop nginx temporarily for standalone authentication
    log "Stopping nginx temporarily..."
    if [[ "$OS" == "macos" ]]; then
        nginx -s stop 2>/dev/null || true
    else
        systemctl stop nginx 2>/dev/null || true
    fi
    
    # Get certificate using standalone mode
    log "Obtaining Let's Encrypt certificate..."
    certbot certonly \
        --standalone \
        --non-interactive \
        --agree-tos \
        --email "$EMAIL" \
        -d "$DOMAIN"
    
    # Copy certificates to nginx directory
    log "Copying certificates to nginx directory..."
    cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$NGINX_CONF_DIR/ssl/"
    cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$NGINX_CONF_DIR/ssl/"
    
    # Set up automatic renewal
    log "Setting up automatic certificate renewal..."
    
    # Create renewal script
    cat > "/usr/local/bin/renew-ai-scholar-ssl.sh" << EOF
#!/bin/bash
# AI Scholar SSL Certificate Renewal Script

# Stop nginx
systemctl stop nginx

# Renew certificate
certbot renew --standalone --quiet

# Copy renewed certificates
if [[ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then
    cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$NGINX_CONF_DIR/ssl/"
    cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$NGINX_CONF_DIR/ssl/"
    
    # Set proper permissions
    chmod 644 "$NGINX_CONF_DIR/ssl/fullchain.pem"
    chmod 600 "$NGINX_CONF_DIR/ssl/privkey.pem"
fi

# Start nginx
systemctl start nginx

# Log renewal
echo "\$(date): SSL certificate renewed for $DOMAIN" >> /var/log/ai-scholar-ssl-renewal.log
EOF
    
    chmod +x "/usr/local/bin/renew-ai-scholar-ssl.sh"
    
    # Add cron job for automatic renewal
    if [[ "$OS" != "macos" ]]; then
        (crontab -l 2>/dev/null; echo "0 3 * * 0 /usr/local/bin/renew-ai-scholar-ssl.sh") | crontab -
        log "Added weekly SSL renewal cron job"
    fi
    
    log "✅ Let's Encrypt SSL certificate installed"
    
else
    # Development SSL with self-signed certificate
    log "Generating self-signed SSL certificate for development..."
    
    # Generate private key
    openssl genrsa -out "$NGINX_CONF_DIR/ssl/privkey.pem" 4096
    
    # Generate certificate signing request
    openssl req -new \
        -key "$NGINX_CONF_DIR/ssl/privkey.pem" \
        -out "$NGINX_CONF_DIR/ssl/cert.csr" \
        -subj "/C=US/ST=Development/L=Local/O=AI Scholar/OU=Development/CN=$DOMAIN"
    
    # Generate self-signed certificate
    openssl x509 -req -days 365 \
        -in "$NGINX_CONF_DIR/ssl/cert.csr" \
        -signkey "$NGINX_CONF_DIR/ssl/privkey.pem" \
        -out "$NGINX_CONF_DIR/ssl/fullchain.pem" \
        -extensions v3_req \
        -extfile <(cat << EOF
[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = *.$DOMAIN
DNS.3 = localhost
DNS.4 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF
)
    
    # Clean up CSR file
    rm "$NGINX_CONF_DIR/ssl/cert.csr"
    
    log "✅ Self-signed SSL certificate generated"
    
    warn "This is a self-signed certificate for development only!"
    warn "Browsers will show security warnings. This is normal for development."
fi

# Set proper permissions
log "Setting SSL file permissions..."
chmod 644 "$NGINX_CONF_DIR/ssl/fullchain.pem"
chmod 600 "$NGINX_CONF_DIR/ssl/privkey.pem"

# Set ownership (skip on macOS as it uses different user management)
if [[ "$OS" != "macos" ]]; then
    if [[ "$OS" == "debian" ]]; then
        chown www-data:www-data "$NGINX_CONF_DIR/ssl/"*
    else
        chown nginx:nginx "$NGINX_CONF_DIR/ssl/"*
    fi
fi

# Verify certificate
log "Verifying SSL certificate..."
if openssl x509 -in "$NGINX_CONF_DIR/ssl/fullchain.pem" -text -noout > /dev/null 2>&1; then
    log "✅ SSL certificate is valid"
    
    # Show certificate details
    info "Certificate details:"
    openssl x509 -in "$NGINX_CONF_DIR/ssl/fullchain.pem" -noout -subject -dates -issuer
else
    error "❌ SSL certificate verification failed"
fi

# Test nginx configuration if nginx is installed
if command -v nginx &> /dev/null; then
    log "Testing nginx configuration..."
    if nginx -t; then
        log "✅ Nginx configuration test passed"
        
        # Restart nginx
        log "Restarting nginx..."
        if [[ "$OS" == "macos" ]]; then
            nginx -s reload 2>/dev/null || nginx
        else
            systemctl restart nginx
        fi
    else
        warn "⚠️ Nginx configuration test failed. Please check your configuration."
    fi
fi

echo
echo -e "${GREEN}🎉 SSL Certificate Setup Complete! 🎉${NC}"
echo
echo -e "${BLUE}=== Certificate Information ===${NC}"
echo -e "Mode: ${GREEN}$MODE${NC}"
echo -e "Domain: ${GREEN}$DOMAIN${NC}"
echo -e "Certificate: ${GREEN}$NGINX_CONF_DIR/ssl/fullchain.pem${NC}"
echo -e "Private key: ${GREEN}$NGINX_CONF_DIR/ssl/privkey.pem${NC}"

if [[ "$MODE" == "production" ]]; then
    echo
    echo -e "${BLUE}=== Let's Encrypt Information ===${NC}"
    echo -e "Certificate location: ${GREEN}/etc/letsencrypt/live/$DOMAIN/${NC}"
    echo -e "Renewal script: ${GREEN}/usr/local/bin/renew-ai-scholar-ssl.sh${NC}"
    echo -e "Renewal cron job: ${GREEN}Weekly on Sunday at 3 AM${NC}"
    echo
    echo -e "${YELLOW}Important:${NC}"
    echo "- Certificates will auto-renew weekly"
    echo "- Check renewal logs: /var/log/ai-scholar-ssl-renewal.log"
    echo "- Test renewal: certbot renew --dry-run"
else
    echo
    echo -e "${BLUE}=== Development Certificate Information ===${NC}"
    echo -e "Valid for: ${GREEN}365 days${NC}"
    echo -e "Subject Alternative Names: ${GREEN}$DOMAIN, *.$DOMAIN, localhost, *.localhost${NC}"
    echo
    echo -e "${YELLOW}Important:${NC}"
    echo "- This is a self-signed certificate for development only"
    echo "- Browsers will show security warnings - this is normal"
    echo "- For production, run: $0 --production --domain yourdomain.com --email your@email.com"
fi

echo
echo -e "${BLUE}=== Testing SSL ===${NC}"
echo "Test your SSL certificate:"
echo "  curl -k https://$DOMAIN/health"
echo "  openssl s_client -connect $DOMAIN:443 -servername $DOMAIN"
echo
echo "Online SSL test (production only):"
echo "  https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"