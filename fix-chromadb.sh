#!/bin/bash
# ChromaDB specific troubleshooting and fix script

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
}

echo -e "${BLUE}=== ChromaDB Fix Script ===${NC}"
echo

# Clean up any existing ChromaDB containers
log "Cleaning up existing ChromaDB containers..."
docker stop test-chromadb ai-scholar-chromadb ai-scholar-chromadb-simple 2>/dev/null || true
docker rm test-chromadb ai-scholar-chromadb ai-scholar-chromadb-simple 2>/dev/null || true

# Remove and recreate data directory
log "Resetting ChromaDB data directory..."
sudo rm -rf data/chroma 2>/dev/null || rm -rf data/chroma 2>/dev/null || true
mkdir -p data/chroma
chmod 777 data/chroma

# Check if port is really available
log "Checking port 8081..."
if lsof -Pi :8081 -sTCP:LISTEN -t >/dev/null 2>&1; then
    error "Port 8081 is still in use!"
    lsof -Pi :8081 -sTCP:LISTEN
    exit 1
else
    log "Port 8081 is available"
fi

# Try different ChromaDB versions and configurations
versions=("0.4.18" "0.4.15" "0.4.22" "latest")

for version in "${versions[@]}"; do
    log "Trying ChromaDB version: $version"
    
    # Start ChromaDB with very basic configuration
    docker run -d --name test-chromadb-$version \
        -p 8081:8000 \
        --user root \
        -v $(pwd)/data/chroma:/chroma/chroma \
        -e CHROMA_SERVER_HOST=0.0.0.0 \
        -e CHROMA_SERVER_HTTP_PORT=8000 \
        -e ANONYMIZED_TELEMETRY=False \
        -e ALLOW_RESET=True \
        -e CHROMA_SERVER_CORS_ALLOW_ORIGINS='["*"]' \
        chromadb/chroma:$version
    
    # Wait for startup
    log "Waiting for ChromaDB $version to start..."
    sleep 20
    
    # Check if container is running
    if ! docker ps | grep -q test-chromadb-$version; then
        warn "Container test-chromadb-$version stopped. Checking logs..."
        echo "=== LOGS FOR VERSION $version ==="
        docker logs test-chromadb-$version 2>&1 || echo "No logs available"
        echo "=================================="
        docker rm test-chromadb-$version 2>/dev/null || true
        continue
    fi
    
    # Test health endpoint
    log "Testing health endpoint for version $version..."
    if curl -f http://localhost:8081/api/v1/heartbeat >/dev/null 2>&1; then
        echo -e "${GREEN}✅ ChromaDB $version is working!${NC}"
        
        # Test basic functionality
        log "Testing basic ChromaDB functionality..."
        if curl -X POST http://localhost:8081/api/v1/collections \
            -H "Content-Type: application/json" \
            -d '{"name": "test_collection"}' >/dev/null 2>&1; then
            echo -e "${GREEN}✅ ChromaDB can create collections${NC}"
            
            # Clean up test
            curl -X DELETE http://localhost:8081/api/v1/collections/test_collection >/dev/null 2>&1 || true
        fi
        
        # Show successful configuration
        echo -e "${BLUE}=== WORKING CONFIGURATION ===${NC}"
        echo "Version: chromadb/chroma:$version"
        echo "Port: 8081:8000"
        echo "Volume: $(pwd)/data/chroma:/chroma/chroma"
        echo "User: root"
        echo "Environment:"
        echo "  CHROMA_SERVER_HOST=0.0.0.0"
        echo "  CHROMA_SERVER_HTTP_PORT=8000"
        echo "  ANONYMIZED_TELEMETRY=False"
        echo "  ALLOW_RESET=True"
        echo "  CHROMA_SERVER_CORS_ALLOW_ORIGINS=[\"*\"]"
        
        # Stop test container
        docker stop test-chromadb-$version
        docker rm test-chromadb-$version
        
        # Create working docker-compose override
        log "Creating working ChromaDB configuration..."
        cat > docker-compose.chromadb-fix.yml << EOF
services:
  chromadb:
    image: chromadb/chroma:$version
    container_name: ai-scholar-chromadb-fixed
    restart: unless-stopped
    user: root
    ports:
      - "8081:8000"
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
      - CHROMA_SERVER_HTTP_PORT=8000
      - ANONYMIZED_TELEMETRY=False
      - ALLOW_RESET=True
      - CHROMA_SERVER_CORS_ALLOW_ORIGINS=["*"]
    volumes:
      - ./data/chroma:/chroma/chroma
    networks:
      - ai-scholar-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/api/v1/heartbeat || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 45s
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 256M

networks:
  ai-scholar-network:
    external: true
EOF
        
        echo -e "${GREEN}✅ Created docker-compose.chromadb-fix.yml${NC}"
        echo
        echo -e "${BLUE}To start the fixed ChromaDB:${NC}"
        echo "docker network create ai-scholar-network 2>/dev/null || true"
        echo "docker-compose -f docker-compose.chromadb-fix.yml up -d"
        echo
        echo -e "${BLUE}To test:${NC}"
        echo "curl http://localhost:8081/api/v1/heartbeat"
        
        exit 0
    else
        warn "Health check failed for version $version"
        echo "=== LOGS FOR VERSION $version ==="
        docker logs test-chromadb-$version --tail 30 2>&1 || echo "No logs available"
        echo "=================================="
        docker stop test-chromadb-$version 2>/dev/null || true
        docker rm test-chromadb-$version 2>/dev/null || true
    fi
done

# If all versions failed, try without volume mount
log "All versions failed with volume mount. Trying without persistent storage..."

docker run -d --name test-chromadb-memory \
    -p 8081:8000 \
    --user root \
    -e CHROMA_SERVER_HOST=0.0.0.0 \
    -e CHROMA_SERVER_HTTP_PORT=8000 \
    -e ANONYMIZED_TELEMETRY=False \
    -e ALLOW_RESET=True \
    chromadb/chroma:0.4.18

sleep 15

if curl -f http://localhost:8081/api/v1/heartbeat >/dev/null 2>&1; then
    echo -e "${GREEN}✅ ChromaDB works without persistent storage${NC}"
    echo -e "${YELLOW}⚠️  This means there's a volume/permission issue${NC}"
    
    # Show the issue
    echo -e "${BLUE}=== DIAGNOSIS ===${NC}"
    echo "ChromaDB works without volume mount but fails with it."
    echo "This indicates a file system permission or compatibility issue."
    echo
    echo -e "${BLUE}=== SOLUTIONS ===${NC}"
    echo "1. Use in-memory ChromaDB (no persistence):"
    echo "   - Fast startup, no storage issues"
    echo "   - Data lost on restart"
    echo
    echo "2. Try different volume mount:"
    echo "   - Use Docker volume instead of bind mount"
    echo "   - Use tmpfs for testing"
    echo
    echo "3. Fix file system permissions:"
    echo "   - Check if your file system supports the required permissions"
    echo "   - Try running Docker as root (not recommended for production)"
    
    # Create in-memory version
    cat > docker-compose.chromadb-memory.yml << EOF
services:
  chromadb:
    image: chromadb/chroma:0.4.18
    container_name: ai-scholar-chromadb-memory
    restart: unless-stopped
    user: root
    ports:
      - "8081:8000"
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
      - CHROMA_SERVER_HTTP_PORT=8000
      - ANONYMIZED_TELEMETRY=False
      - ALLOW_RESET=True
      - CHROMA_SERVER_CORS_ALLOW_ORIGINS=["*"]
    networks:
      - ai-scholar-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/api/v1/heartbeat || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

networks:
  ai-scholar-network:
    external: true
EOF
    
    echo -e "${GREEN}✅ Created docker-compose.chromadb-memory.yml (in-memory version)${NC}"
    
    docker stop test-chromadb-memory
    docker rm test-chromadb-memory
else
    echo -e "${RED}❌ ChromaDB failed even without volume mount${NC}"
    echo "=== LOGS ==="
    docker logs test-chromadb-memory --tail 30 2>&1 || echo "No logs available"
    echo "============"
    
    echo -e "${BLUE}=== ADVANCED DEBUGGING ===${NC}"
    echo "ChromaDB is failing to start entirely. Possible causes:"
    echo "1. Docker/container runtime issues"
    echo "2. Network conflicts"
    echo "3. Resource constraints"
    echo "4. Architecture compatibility (ARM vs x86)"
    echo
    echo "Try:"
    echo "docker run --rm chromadb/chroma:0.4.18 --help"
    echo "docker system info"
    
    docker stop test-chromadb-memory 2>/dev/null || true
    docker rm test-chromadb-memory 2>/dev/null || true
fi