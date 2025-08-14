#!/bin/bash
# Troubleshoot ChromaDB and Ollama startup issues

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

echo -e "${BLUE}=== AI Services Troubleshooter ===${NC}"
echo

# Function to test ChromaDB
test_chromadb() {
    log "Testing ChromaDB..."
    
    # Stop any existing ChromaDB
    docker stop ai-scholar-chromadb ai-scholar-chromadb-simple 2>/dev/null || true
    docker rm ai-scholar-chromadb ai-scholar-chromadb-simple 2>/dev/null || true
    
    # Create data directory
    mkdir -p data/chroma
    chmod 777 data/chroma
    
    # Start simple ChromaDB
    log "Starting ChromaDB with minimal configuration..."
    docker run -d --name test-chromadb \
        -p 8081:8000 \
        -v $(pwd)/data/chroma:/chroma/chroma \
        -e CHROMA_SERVER_HOST=0.0.0.0 \
        -e CHROMA_SERVER_HTTP_PORT=8000 \
        -e ANONYMIZED_TELEMETRY=False \
        -e ALLOW_RESET=True \
        chromadb/chroma:0.4.18
    
    # Wait and test
    sleep 15
    
    if curl -f http://localhost:8081/api/v1/heartbeat >/dev/null 2>&1; then
        echo -e "${GREEN}✅ ChromaDB is working!${NC}"
        docker logs test-chromadb --tail 10
        docker stop test-chromadb
        docker rm test-chromadb
        return 0
    else
        echo -e "${RED}❌ ChromaDB failed${NC}"
        echo "Logs:"
        docker logs test-chromadb --tail 20
        docker stop test-chromadb 2>/dev/null || true
        docker rm test-chromadb 2>/dev/null || true
        return 1
    fi
}

# Function to test Ollama
test_ollama() {
    log "Testing Ollama..."
    
    # Stop any existing Ollama
    docker stop ai-scholar-ollama ai-scholar-ollama-simple 2>/dev/null || true
    docker rm ai-scholar-ollama ai-scholar-ollama-simple 2>/dev/null || true
    
    # Create data directory
    mkdir -p data/ollama
    chmod 777 data/ollama
    
    # Start simple Ollama
    log "Starting Ollama with minimal configuration..."
    docker run -d --name test-ollama \
        -p 11435:11434 \
        -v $(pwd)/data/ollama:/root/.ollama \
        -e OLLAMA_ORIGINS=* \
        -e OLLAMA_HOST=0.0.0.0:11434 \
        ollama/ollama:latest
    
    # Wait longer for Ollama
    log "Waiting for Ollama to initialize (up to 2 minutes)..."
    for i in {1..120}; do
        if curl -f http://localhost:11435/api/tags >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Ollama is working!${NC}"
            docker logs test-ollama --tail 10
            docker stop test-ollama
            docker rm test-ollama
            return 0
        fi
        
        if [ $((i % 30)) -eq 0 ]; then
            log "Still waiting... ($((i/60)) minutes)"
        fi
        
        sleep 1
    done
    
    echo -e "${RED}❌ Ollama failed or timed out${NC}"
    echo "Logs:"
    docker logs test-ollama --tail 30
    docker stop test-ollama 2>/dev/null || true
    docker rm test-ollama 2>/dev/null || true
    return 1
}

# Function to check system resources
check_resources() {
    log "Checking system resources..."
    
    # Memory
    total_mem=$(free -m | awk 'NR==2{printf "%.1f", $2/1024}')
    available_mem=$(free -m | awk 'NR==2{printf "%.1f", $7/1024}')
    echo "Memory: ${available_mem}GB available / ${total_mem}GB total"
    
    if (( $(echo "$available_mem < 4" | bc -l) )); then
        warn "Low available memory. Ollama may fail to start."
    fi
    
    # Disk space
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    echo "Disk space: ${available_space}GB available"
    
    if [ "$available_space" -lt 5 ]; then
        warn "Low disk space. AI services may fail."
    fi
    
    # CPU
    cpu_count=$(nproc)
    echo "CPU cores: $cpu_count"
    
    echo
}

# Function to fix permissions
fix_permissions() {
    log "Fixing permissions..."
    
    mkdir -p data/{chroma,ollama}
    
    # Fix ownership
    sudo chown -R $USER:$USER data/ 2>/dev/null || chown -R $USER:$USER data/
    
    # Set permissive permissions for AI services
    chmod -R 777 data/chroma/ data/ollama/
    
    echo -e "${GREEN}✅ Permissions fixed${NC}"
    echo
}

# Main troubleshooting flow
main() {
    check_resources
    fix_permissions
    
    echo -e "${BLUE}=== Testing ChromaDB ===${NC}"
    if test_chromadb; then
        chromadb_ok=true
    else
        chromadb_ok=false
    fi
    
    echo
    echo -e "${BLUE}=== Testing Ollama ===${NC}"
    if test_ollama; then
        ollama_ok=true
    else
        ollama_ok=false
    fi
    
    echo
    echo -e "${BLUE}=== RESULTS ===${NC}"
    
    if [ "$chromadb_ok" = true ]; then
        echo -e "${GREEN}✅ ChromaDB: Working${NC}"
    else
        echo -e "${RED}❌ ChromaDB: Failed${NC}"
        echo "  Common fixes:"
        echo "  • Check data/chroma permissions: chmod 777 data/chroma"
        echo "  • Try different ChromaDB version: chromadb/chroma:0.4.15"
        echo "  • Check port 8081 availability: lsof -i :8081"
    fi
    
    if [ "$ollama_ok" = true ]; then
        echo -e "${GREEN}✅ Ollama: Working${NC}"
    else
        echo -e "${RED}❌ Ollama: Failed${NC}"
        echo "  Common fixes:"
        echo "  • Increase memory: Ollama needs 4GB+ RAM"
        echo "  • Check data/ollama permissions: chmod 777 data/ollama"
        echo "  • Try CPU-only mode if GPU issues"
        echo "  • Check port 11435 availability: lsof -i :11435"
    fi
    
    echo
    if [ "$chromadb_ok" = true ] && [ "$ollama_ok" = true ]; then
        echo -e "${GREEN}🎉 Both services are working! You can now run the full deployment.${NC}"
        echo "Run: ./deploy-with-ai-services.sh"
    elif [ "$chromadb_ok" = true ] || [ "$ollama_ok" = true ]; then
        echo -e "${YELLOW}⚠️  One service is working. You can deploy with partial AI functionality.${NC}"
        echo "Run: ./deploy-with-ai-services.sh"
    else
        echo -e "${RED}❌ Both services failed. Use minimal deployment instead.${NC}"
        echo "Run: ./quick-start-minimal.sh"
    fi
}

# Run main function
main