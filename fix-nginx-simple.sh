#!/bin/bash
# Simple nginx fix - rebuild without volume mount conflicts

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

echo -e "${BLUE}=== Simple Nginx Fix ===${NC}"
echo

# Create logs directory
log "Creating logs directory..."
mkdir -p logs/nginx

# Stop existing nginx container
log "Stopping existing nginx container..."
docker stop ai-scholar-nginx 2>/dev/null || true
docker rm ai-scholar-nginx 2>/dev/null || true

# Remove nginx image to force rebuild
log "Removing old nginx image..."
docker rmi ai-scholar-nginx:latest 2>/dev/null || true

# Rebuild nginx image
log "Rebuilding nginx image..."
docker build -f Dockerfile.nginx -t ai-scholar-nginx:latest .

# Test the nginx image
log "Testing nginx image..."
docker run --rm -d --name test-nginx \
    -p 8003:80 \
    ai-scholar-nginx:latest

sleep 5

if docker ps | grep -q test-nginx; then
    log "Testing nginx health..."
    if curl -f http://localhost:8003/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Nginx is working!${NC}"
    else
        warn "Nginx started but health check failed (this is normal without backend/frontend)"
    fi
    
    docker stop test-nginx
else
    error "Nginx container failed to start"
    echo "Nginx logs:"
    docker logs test-nginx --tail 30 2>/dev/null || echo "No logs available"
    docker rm test-nginx 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ Nginx image rebuilt successfully!${NC}"
echo
echo -e "${BLUE}The nginx container now uses its built-in configuration.${NC}"
echo "No external volume mounts needed for configuration files."
echo
echo -e "${BLUE}Now you can run your deployment script again:${NC}"
echo "./quick-start-minimal.sh"