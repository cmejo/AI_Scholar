#!/bin/bash
# Debug script to identify ChromaDB and Ollama issues

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

echo -e "${BLUE}=== AI Scholar Service Debug Tool ===${NC}"
echo

# Check system resources
log "Checking system resources..."
echo "Memory:"
free -h
echo
echo "Disk space:"
df -h
echo
echo "CPU info:"
nproc
echo

# Check Docker
log "Checking Docker status..."
docker --version
docker-compose --version
docker system df
echo

# Check existing containers
log "Checking existing containers..."
docker ps -a --filter "name=ai-scholar"
echo

# Check volumes
log "Checking Docker volumes..."
docker volume ls | grep ai_scholar || echo "No AI Scholar volumes found"
echo

# Check networks
log "Checking Docker networks..."
docker network ls | grep ai-scholar || echo "No AI Scholar networks found"
echo

# Check data directories
log "Checking data directories..."
ls -la data/ 2>/dev/null || echo "No data directory found"
if [ -d "data" ]; then
    echo "Data directory contents:"
    ls -la data/
    echo
    if [ -d "data/chroma" ]; then
        echo "ChromaDB data:"
        ls -la data/chroma/
        echo
    fi
    if [ -d "data/ollama" ]; then
        echo "Ollama data:"
        ls -la data/ollama/
        echo
    fi
fi

# Test ChromaDB standalone
log "Testing ChromaDB standalone..."
echo "Attempting to start ChromaDB alone..."
docker run --rm -d --name test-chromadb -p 8081:8000 \
    -e CHROMA_SERVER_HOST=0.0.0.0 \
    -e CHROMA_SERVER_HTTP_PORT=8000 \
    -e ANONYMIZED_TELEMETRY=False \
    -e ALLOW_RESET=True \
    chromadb/chroma:0.4.18

sleep 10

if docker ps | grep -q test-chromadb; then
    echo -e "${GREEN}✅ ChromaDB started successfully${NC}"
    
    # Test health endpoint
    if curl -f http://localhost:8081/api/v1/heartbeat 2>/dev/null; then
        echo -e "${GREEN}✅ ChromaDB health check passed${NC}"
    else
        echo -e "${RED}❌ ChromaDB health check failed${NC}"
    fi
    
    # Show logs
    echo "ChromaDB logs:"
    docker logs test-chromadb --tail 20
    
    # Stop test container
    docker stop test-chromadb
else
    echo -e "${RED}❌ ChromaDB failed to start${NC}"
    echo "ChromaDB logs:"
    docker logs test-chromadb --tail 20 2>/dev/null || echo "No logs available"
    docker rm test-chromadb 2>/dev/null || true
fi

echo

# Test Ollama standalone
log "Testing Ollama standalone..."
echo "Attempting to start Ollama alone..."
docker run --rm -d --name test-ollama -p 11435:11434 \
    -e OLLAMA_ORIGINS=* \
    -e OLLAMA_HOST=0.0.0.0:11434 \
    ollama/ollama:latest

sleep 30

if docker ps | grep -q test-ollama; then
    echo -e "${GREEN}✅ Ollama started successfully${NC}"
    
    # Test API endpoint
    if curl -f http://localhost:11435/api/tags 2>/dev/null; then
        echo -e "${GREEN}✅ Ollama API check passed${NC}"
    else
        echo -e "${RED}❌ Ollama API check failed${NC}"
    fi
    
    # Show logs
    echo "Ollama logs:"
    docker logs test-ollama --tail 20
    
    # Stop test container
    docker stop test-ollama
else
    echo -e "${RED}❌ Ollama failed to start${NC}"
    echo "Ollama logs:"
    docker logs test-ollama --tail 20 2>/dev/null || echo "No logs available"
    docker rm test-ollama 2>/dev/null || true
fi

echo

# Check port availability
log "Checking port availability..."
ports=(8081 11435)
for port in "${ports[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Port $port is in use${NC}"
        lsof -Pi :$port -sTCP:LISTEN
    else
        echo -e "${GREEN}✅ Port $port is available${NC}"
    fi
done

echo
log "Debug complete. Check the output above for issues."