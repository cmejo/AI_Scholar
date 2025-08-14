#!/bin/bash
# Fix backend container gunicorn issue

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

echo -e "${BLUE}=== Backend Fix Script ===${NC}"
echo

# Stop existing backend container
log "Stopping existing backend container..."
docker stop ai-scholar-backend 2>/dev/null || true
docker rm ai-scholar-backend 2>/dev/null || true

# Remove backend image to force rebuild
log "Removing old backend image..."
docker rmi ai-scholar-backend:latest 2>/dev/null || true

# Rebuild backend image
log "Rebuilding backend image with gunicorn..."
docker build -f Dockerfile.backend -t ai-scholar-backend:latest .

# Test the backend image
log "Testing backend image..."
docker run --rm -d --name test-backend \
    -p 8002:8000 \
    -e DATABASE_URL="sqlite:///./test.db" \
    -e REDIS_URL="redis://localhost:6379/0" \
    -e SECRET_KEY="test-secret-key" \
    -e JWT_SECRET="test-jwt-secret" \
    ai-scholar-backend:latest

sleep 10

if docker ps | grep -q test-backend; then
    log "Testing backend health endpoint..."
    if curl -f http://localhost:8002/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is working!${NC}"
    else
        warn "Backend started but health check failed"
        echo "Backend logs:"
        docker logs test-backend --tail 20
    fi
    
    docker stop test-backend
else
    error "Backend container failed to start"
    echo "Backend logs:"
    docker logs test-backend --tail 30 2>/dev/null || echo "No logs available"
    docker rm test-backend 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ Backend image rebuilt successfully!${NC}"
echo
echo -e "${BLUE}Now you can run your deployment script again:${NC}"
echo "./quick-start-minimal.sh"