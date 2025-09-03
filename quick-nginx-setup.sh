#!/bin/bash
# Quick Nginx Reverse Proxy Setup for AI Scholar
# One-command setup for development or production

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
SETUP_MONITORING=true
SETUP_SSL=true

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
        --no-monitoring)
            SETUP_MONITORING=false
            shift
            ;;
        --no-ssl)
            SETUP_SSL=false
            shift
            ;;
        -h|--help)
            echo "Quick Nginx Setup for AI Scholar"
            echo
            echo "Usage: $0 [OPTIONS]"
            echo
            echo "Options:"
            echo "  --production          Production setup with Let's Encrypt"
            echo "  --dev, --development  Development setup (default)"
            echo "  --domain DOMAIN       Domain name (default: localhost)"
            echo "  --email EMAIL         Email for Let's Encrypt (required for production)"
            echo "  --no-monitoring       Skip monitoring setup"
            echo "  --no-ssl             Skip SSL setup"
            echo "  -h, --help           Show this help message"
            echo
            echo "Examples:"
            echo "  $0                                    # Development setup"
            echo "  $0 --production --domain example.com --email admin@example.com"
            echo "  $0 --dev --domain myapp.local"
            exit 0
            ;;
        *)
            error "Unknown option: $1. Use --help for usage information."
            ;;
    esac
done

# Validation
if [[ "$MODE" == "production" ]]; then
    if [[ "$DOMAIN" == "localhost" ]]; then
        error "Production mode requires a real domain. Use --domain yourdomain.com"
    fi
    if [[ -z "$EMAIL" ]]; then
        error "Production mode requires an email. Use --email your@email.com"
    fi
fi

echo -e "${BLUE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║                  Quick Nginx Setup                           ║
║                   for AI Scholar                             ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

info "Mode: $MODE"
info "Domain: $DOMAIN"
if [[ -n "$EMAIL" ]]; then
    info "Email: $EMAIL"
fi
info "Setup monitoring: $SETUP_MONITORING"
info "Setup SSL: $SETUP_SSL"

# Check if scripts exist
REQUIRED_SCRIPTS=(
    "setup-nginx-proxy.sh"
    "nginx-ssl-setup.sh"
    "test-nginx-config.sh"
    "nginx-monitoring-setup.sh"
)

for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [[ ! -f "$script" ]]; then
        error "Required script not found: $script"
    fi
done

# Step 1: Main nginx setup
log "🔧 Setting up nginx reverse proxy..."
if [[ "$MODE" == "production" ]]; then
    sudo ./setup-nginx-proxy.sh "$DOMAIN" production
else
    sudo ./setup-nginx-proxy.sh "$DOMAIN" development
fi

# Step 2: SSL setup
if [[ "$SETUP_SSL" == true ]]; then
    log "🔒 Setting up SSL certificates..."
    if [[ "$MODE" == "production" ]]; then
        sudo ./nginx-ssl-setup.sh --production --domain "$DOMAIN" --email "$EMAIL"
    else
        sudo ./nginx-ssl-setup.sh --dev --domain "$DOMAIN"
    fi
fi

# Step 3: Monitoring setup
if [[ "$SETUP_MONITORING" == true ]]; then
    log "📊 Setting up monitoring and logging..."
    sudo ./nginx-monitoring-setup.sh
fi

# Step 4: Test configuration
log "🧪 Testing nginx configuration..."
./test-nginx-config.sh "$DOMAIN"

# Step 5: Final status check
log "🔍 Checking final status..."
sleep 3

if pgrep nginx > /dev/null; then
    log "✅ Nginx is running successfully"
else
    error "❌ Nginx failed to start"
fi

# Test endpoints
ENDPOINTS=(
    "http://$DOMAIN/health"
    "https://$DOMAIN/health"
)

for endpoint in "${ENDPOINTS[@]}"; do
    if curl -k -s -o /dev/null -w "%{http_code}" "$endpoint" 2>/dev/null | grep -q "200\|301\|302"; then
        log "✅ $endpoint is responding"
    else
        warn "⚠️ $endpoint is not responding"
    fi
done

echo
echo -e "${GREEN}🎉 Nginx Setup Complete! 🎉${NC}"
echo
echo -e "${BLUE}=== Access Information ===${NC}"
if [[ "$DOMAIN" == "localhost" ]]; then
    echo -e "🌐 Main app: ${GREEN}https://localhost${NC}"
    echo -e "🔧 Health check: ${GREEN}https://localhost/health${NC}"
else
    echo -e "🌐 Main app: ${GREEN}https://$DOMAIN${NC}"
    echo -e "🔧 Health check: ${GREEN}https://$DOMAIN/health${NC}"
fi

if [[ "$SETUP_MONITORING" == true ]]; then
    echo -e "📊 Monitoring dashboard: ${GREEN}sudo /opt/nginx-monitoring/scripts/dashboard.sh${NC}"
    echo -e "📈 Status page: ${GREEN}http://127.0.0.1:8888/nginx-status${NC} (localhost only)"
fi

echo
echo -e "${BLUE}=== Next Steps ===${NC}"
echo "1. Start your AI Scholar services:"
echo "   ./deploy-with-ai-services.sh"
echo
echo "2. Verify everything is working:"
echo "   curl -k https://$DOMAIN/health"
echo
echo "3. Check nginx logs:"
echo "   sudo tail -f /var/log/nginx/access.log"
echo "   sudo tail -f /var/log/nginx/error.log"

if [[ "$SETUP_MONITORING" == true ]]; then
    echo
    echo "4. Monitor performance:"
    echo "   sudo /opt/nginx-monitoring/scripts/dashboard.sh"
fi

if [[ "$MODE" == "development" ]]; then
    echo
    echo -e "${YELLOW}Development Notes:${NC}"
    echo "- Using self-signed SSL certificate (browser warnings are normal)"
    echo "- For production, run with --production --domain yourdomain.com --email your@email.com"
fi

if [[ "$MODE" == "production" ]]; then
    echo
    echo -e "${YELLOW}Production Notes:${NC}"
    echo "- SSL certificates will auto-renew weekly"
    echo "- Monitor renewal logs: /var/log/ai-scholar-ssl-renewal.log"
    echo "- Test SSL: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
fi

echo
log "🚀 Setup completed successfully!"