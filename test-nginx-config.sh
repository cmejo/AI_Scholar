#!/bin/bash
# Comprehensive Nginx Configuration Testing Script
# Tests configuration, connectivity, SSL, and performance

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
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

fail() {
    echo -e "${RED}❌ $1${NC}"
}

# Configuration
DOMAIN=${1:-localhost}
NGINX_CONF_DIR="/etc/nginx"

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    NGINX_CONF_DIR="/usr/local/etc/nginx"
fi

echo -e "${BLUE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║                  Nginx Configuration Test                    ║
║                     for AI Scholar                           ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

info "Testing domain: $DOMAIN"
info "Nginx config dir: $NGINX_CONF_DIR"

# Test 1: Nginx Configuration Syntax
log "Testing nginx configuration syntax..."
if nginx -t 2>/dev/null; then
    success "Nginx configuration syntax is valid"
else
    fail "Nginx configuration syntax test failed"
    nginx -t
    exit 1
fi

# Test 2: Check if Nginx is running
log "Checking if nginx is running..."
if pgrep nginx > /dev/null; then
    success "Nginx is running"
    NGINX_PID=$(pgrep nginx | head -1)
    info "Nginx master process PID: $NGINX_PID"
else
    fail "Nginx is not running"
    info "Start nginx with: sudo systemctl start nginx (Linux) or nginx (macOS)"
    exit 1
fi

# Test 3: Check listening ports
log "Checking nginx listening ports..."
if command -v netstat &> /dev/null; then
    LISTENING_PORTS=$(netstat -tlnp 2>/dev/null | grep nginx || netstat -tln 2>/dev/null | grep -E ':(80|443|8080|8443)')
    if [[ -n "$LISTENING_PORTS" ]]; then
        success "Nginx is listening on ports:"
        echo "$LISTENING_PORTS" | while read line; do
            echo "  $line"
        done
    else
        warn "No nginx listening ports detected"
    fi
elif command -v ss &> /dev/null; then
    LISTENING_PORTS=$(ss -tlnp | grep nginx)
    if [[ -n "$LISTENING_PORTS" ]]; then
        success "Nginx is listening on ports:"
        echo "$LISTENING_PORTS" | while read line; do
            echo "  $line"
        done
    else
        warn "No nginx listening ports detected"
    fi
else
    warn "Cannot check listening ports (netstat/ss not available)"
fi

# Test 4: Basic HTTP connectivity
log "Testing HTTP connectivity..."
HTTP_PORTS=(80 8080)
for port in "${HTTP_PORTS[@]}"; do
    if curl -s -o /dev/null -w "%{http_code}" "http://$DOMAIN:$port/health" 2>/dev/null | grep -q "200\|301\|302"; then
        success "HTTP port $port is responding"
    else
        warn "HTTP port $port is not responding or not configured"
    fi
done

# Test 5: HTTPS connectivity
log "Testing HTTPS connectivity..."
HTTPS_PORTS=(443 8443)
for port in "${HTTPS_PORTS[@]}"; do
    if curl -k -s -o /dev/null -w "%{http_code}" "https://$DOMAIN:$port/health" 2>/dev/null | grep -q "200"; then
        success "HTTPS port $port is responding"
    else
        warn "HTTPS port $port is not responding or not configured"
    fi
done

# Test 6: SSL Certificate validation
log "Testing SSL certificate..."
if [[ -f "$NGINX_CONF_DIR/ssl/fullchain.pem" ]]; then
    if openssl x509 -in "$NGINX_CONF_DIR/ssl/fullchain.pem" -noout -checkend 86400 2>/dev/null; then
        success "SSL certificate is valid and not expiring within 24 hours"
        
        # Show certificate details
        CERT_SUBJECT=$(openssl x509 -in "$NGINX_CONF_DIR/ssl/fullchain.pem" -noout -subject 2>/dev/null | sed 's/subject=//')
        CERT_EXPIRES=$(openssl x509 -in "$NGINX_CONF_DIR/ssl/fullchain.pem" -noout -enddate 2>/dev/null | sed 's/notAfter=//')
        info "Certificate subject: $CERT_SUBJECT"
        info "Certificate expires: $CERT_EXPIRES"
    else
        warn "SSL certificate is invalid or expiring soon"
    fi
else
    warn "SSL certificate not found at $NGINX_CONF_DIR/ssl/fullchain.pem"
fi

# Test 7: Upstream service connectivity
log "Testing upstream services..."
UPSTREAMS=(
    "Backend:http://127.0.0.1:8001/health"
    "Frontend:http://127.0.0.1:3006/health"
    "ChromaDB:http://127.0.0.1:8081/api/v1/heartbeat"
    "Ollama:http://127.0.0.1:11435/api/tags"
)

for upstream in "${UPSTREAMS[@]}"; do
    IFS=':' read -r name url <<< "$upstream"
    if curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null | grep -q "200"; then
        success "$name service is responding"
    else
        warn "$name service is not responding at $url"
    fi
done

# Test 8: Proxy functionality
log "Testing proxy functionality..."
if curl -k -s "https://$DOMAIN/health" 2>/dev/null | grep -q "healthy"; then
    success "Nginx proxy is working (health endpoint)"
else
    warn "Nginx proxy health endpoint not working"
fi

# Test API proxy
if curl -k -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/api/health" 2>/dev/null | grep -q "200\|404"; then
    success "API proxy is configured (got response)"
else
    warn "API proxy may not be working"
fi

# Test 9: Security headers
log "Testing security headers..."
HEADERS_RESPONSE=$(curl -k -s -I "https://$DOMAIN/health" 2>/dev/null)
if [[ -n "$HEADERS_RESPONSE" ]]; then
    SECURITY_HEADERS=(
        "X-Frame-Options"
        "X-Content-Type-Options"
        "X-XSS-Protection"
        "Referrer-Policy"
    )
    
    for header in "${SECURITY_HEADERS[@]}"; do
        if echo "$HEADERS_RESPONSE" | grep -qi "$header"; then
            success "Security header present: $header"
        else
            warn "Security header missing: $header"
        fi
    done
else
    warn "Could not retrieve headers for security test"
fi

# Test 10: Rate limiting (if configured)
log "Testing rate limiting..."
RATE_LIMIT_TEST=true
for i in {1..3}; do
    RESPONSE_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/health" 2>/dev/null)
    if [[ "$RESPONSE_CODE" == "429" ]]; then
        success "Rate limiting is working (got 429 Too Many Requests)"
        RATE_LIMIT_TEST=false
        break
    fi
    sleep 0.1
done

if [[ "$RATE_LIMIT_TEST" == true ]]; then
    info "Rate limiting not triggered (may be configured with higher limits)"
fi

# Test 11: Gzip compression
log "Testing gzip compression..."
GZIP_RESPONSE=$(curl -k -s -H "Accept-Encoding: gzip" -I "https://$DOMAIN/" 2>/dev/null)
if echo "$GZIP_RESPONSE" | grep -qi "content-encoding.*gzip"; then
    success "Gzip compression is enabled"
else
    warn "Gzip compression may not be enabled"
fi

# Test 12: WebSocket support (if applicable)
log "Testing WebSocket support..."
if command -v wscat &> /dev/null; then
    # This is a basic test - in practice you'd need a real WebSocket endpoint
    info "WebSocket testing requires wscat and a WebSocket endpoint"
else
    info "WebSocket testing skipped (wscat not available)"
fi

# Test 13: Log file accessibility
log "Checking nginx log files..."
LOG_FILES=(
    "/var/log/nginx/access.log"
    "/var/log/nginx/error.log"
    "$NGINX_CONF_DIR/../logs/access.log"
    "$NGINX_CONF_DIR/../logs/error.log"
)

for log_file in "${LOG_FILES[@]}"; do
    if [[ -f "$log_file" && -r "$log_file" ]]; then
        success "Log file accessible: $log_file"
        RECENT_ENTRIES=$(tail -5 "$log_file" 2>/dev/null | wc -l)
        info "Recent log entries: $RECENT_ENTRIES"
    fi
done

# Test 14: Configuration file validation
log "Validating configuration files..."
CONFIG_FILES=(
    "$NGINX_CONF_DIR/nginx.conf"
    "$NGINX_CONF_DIR/sites-available/ai-scholar"
    "$NGINX_CONF_DIR/sites-enabled/ai-scholar"
)

for config_file in "${CONFIG_FILES[@]}"; do
    if [[ -f "$config_file" ]]; then
        success "Configuration file exists: $config_file"
    else
        warn "Configuration file missing: $config_file"
    fi
done

# Test 15: Performance test (basic)
log "Running basic performance test..."
if command -v ab &> /dev/null; then
    info "Running Apache Bench test (100 requests, concurrency 10)..."
    AB_RESULT=$(ab -n 100 -c 10 -q "https://$DOMAIN/health" 2>/dev/null | grep "Requests per second" || echo "Test failed")
    if [[ "$AB_RESULT" != "Test failed" ]]; then
        success "Performance test completed: $AB_RESULT"
    else
        warn "Performance test failed"
    fi
else
    info "Performance testing skipped (Apache Bench not available)"
    info "Install with: apt install apache2-utils (Ubuntu) or brew install apache2 (macOS)"
fi

# Summary
echo
echo -e "${BLUE}=== Test Summary ===${NC}"
echo -e "Domain tested: ${GREEN}$DOMAIN${NC}"
echo -e "Nginx config: ${GREEN}$NGINX_CONF_DIR${NC}"
echo -e "Test completed: ${GREEN}$(date)${NC}"

echo
echo -e "${BLUE}=== Recommendations ===${NC}"
echo "1. Check any warnings above and fix configuration issues"
echo "2. Ensure all upstream services are running"
echo "3. Monitor nginx logs for errors: tail -f /var/log/nginx/error.log"
echo "4. Test with real traffic and monitor performance"
echo "5. Set up log rotation and monitoring alerts"

echo
echo -e "${BLUE}=== Useful Commands ===${NC}"
echo "Reload nginx: sudo nginx -s reload"
echo "Test config: sudo nginx -t"
echo "View status: sudo systemctl status nginx"
echo "View logs: sudo tail -f /var/log/nginx/error.log"
echo "Check processes: ps aux | grep nginx"

echo
log "🎉 Nginx configuration test completed!"