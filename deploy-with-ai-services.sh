#!/bin/bash
# AI Scholar Deployment with ChromaDB and Ollama
# Handles common startup issues and provides detailed debugging

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

echo -e "${BLUE}"
cat << 'EOF'
   _____  _____    _____      _           _            
  |  _  ||_   _|  /  ___|    | |         | |           
  | |_| |  | |    \ `--.  ___| |__   ___ | | __ _ _ __ 
  |  _  |  | |     `--. \/ __| '_ \ / _ \| |/ _` | '__|
  | | | | _| |_   /\__/ / (__| | | | (_) | | (_| | |   
  \_| |_/ \___/   \____/ \___|_| |_|\___/|_|\__,_|_|   
                                                       
  AI Scholar with ChromaDB & Ollama
EOF
echo -e "${NC}"

# Check system requirements
log "Checking system requirements..."
total_mem=$(free -m | awk 'NR==2{printf "%.0f", $2/1024}')
if [ "$total_mem" -lt 8 ]; then
    warn "System has ${total_mem}GB RAM. Ollama may need more memory. Consider reducing resource limits."
fi

available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$available_space" -lt 10 ]; then
    warn "Available disk space: ${available_space}GB. Ollama models require significant space."
fi

# Create directories with proper permissions
log "Setting up directories and permissions..."
mkdir -p data/{postgres,redis,chroma,ollama} logs uploads backups ssl config monitoring

# Fix ownership and permissions
sudo chown -R $USER:$USER data/ logs/ uploads/ backups/ 2>/dev/null || true
chmod -R 755 data/ logs/ uploads/ backups/ 2>/dev/null || true

# Ensure ChromaDB directory has correct permissions
if [ -d "data/chroma" ]; then
    chmod -R 777 data/chroma/  # ChromaDB needs write access
fi

# Ensure Ollama directory has correct permissions
if [ -d "data/ollama" ]; then
    chmod -R 777 data/ollama/  # Ollama needs write access
fi

# Clean up any existing containers
log "Cleaning up existing containers..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
docker-compose -f docker-compose.minimal.yml down 2>/dev/null || true

# Force stop and remove all AI Scholar containers
log "Force removing all AI Scholar containers..."
docker ps -a --filter "name=ai-scholar" --format "{{.Names}}" | xargs -r docker stop 2>/dev/null || true
docker ps -a --filter "name=ai-scholar" --format "{{.Names}}" | xargs -r docker rm -f 2>/dev/null || true

# Also clean up any test containers
docker stop test-chromadb test-ollama quick-test-chromadb 2>/dev/null || true
docker rm test-chromadb test-ollama quick-test-chromadb 2>/dev/null || true

# Clean up volumes if they exist and are problematic
log "Cleaning up problematic volumes..."
docker volume rm ai_scholar_chroma_data ai_scholar_ollama_data 2>/dev/null || true

# Start core services first using minimal compose
log "Starting core services (postgres, redis, backend, frontend, nginx)..."
DOCKER_BUILDKIT=1 docker-compose -f docker-compose.minimal.yml up -d

# Wait for core services
log "Waiting for core services to be healthy..."
for i in {1..60}; do
    if docker-compose -f docker-compose.minimal.yml ps postgres | grep -q "healthy" && \
       docker-compose -f docker-compose.minimal.yml ps redis | grep -q "healthy"; then
        log "Core services are healthy"
        break
    fi
    if [ $i -eq 60 ]; then
        error "Core services failed to start"
    fi
    sleep 2
done

# Start ChromaDB with retry logic
log "Starting ChromaDB with retry logic..."
chromadb_attempts=0
max_chromadb_attempts=3

while [ $chromadb_attempts -lt $max_chromadb_attempts ]; do
    chromadb_attempts=$((chromadb_attempts + 1))
    log "ChromaDB attempt $chromadb_attempts/$max_chromadb_attempts"
    
    # Stop any existing ChromaDB container
    docker stop ai-scholar-chromadb test-chromadb 2>/dev/null || true
    docker rm ai-scholar-chromadb test-chromadb 2>/dev/null || true
    
    # Start ChromaDB with version 0.4.15
    docker run -d --name ai-scholar-chromadb \
        --network ai-scholar-network \
        -p 8081:8000 \
        --user root \
        -v $(pwd)/data/chroma:/chroma/chroma \
        -e CHROMA_SERVER_HOST=0.0.0.0 \
        -e CHROMA_SERVER_HTTP_PORT=8000 \
        -e ANONYMIZED_TELEMETRY=False \
        -e ALLOW_RESET=True \
        -e CHROMA_SERVER_CORS_ALLOW_ORIGINS='["*"]' \
        --restart unless-stopped \
        chromadb/chroma:0.4.15
    
    # Wait and check
    sleep 30
    
    if docker ps | grep -q ai-scholar-chromadb && \
       curl -f http://localhost:8081/api/v1/heartbeat >/dev/null 2>&1; then
        log "✅ ChromaDB started successfully"
        break
    else
        warn "ChromaDB attempt $chromadb_attempts failed"
        if [ $chromadb_attempts -eq $max_chromadb_attempts ]; then
            warn "ChromaDB failed after $max_chromadb_attempts attempts. Continuing without it."
            echo "ChromaDB logs:"
            docker logs ai-scholar-chromadb --tail 20 2>/dev/null || echo "No logs available"
        else
            sleep 10
        fi
    fi
done

# Start Ollama with retry logic and timeout
log "Starting Ollama with extended timeout..."
ollama_attempts=0
max_ollama_attempts=2

while [ $ollama_attempts -lt $max_ollama_attempts ]; do
    ollama_attempts=$((ollama_attempts + 1))
    log "Ollama attempt $ollama_attempts/$max_ollama_attempts"
    
    # Stop any existing Ollama container
    docker stop ai-scholar-ollama test-ollama 2>/dev/null || true
    docker rm ai-scholar-ollama test-ollama 2>/dev/null || true
    
    # Start Ollama
    docker run -d --name ai-scholar-ollama \
        --network ai-scholar-network \
        -p 11435:11434 \
        -v $(pwd)/data/ollama:/root/.ollama \
        -e OLLAMA_ORIGINS=* \
        -e OLLAMA_HOST=0.0.0.0:11434 \
        -e OLLAMA_KEEP_ALIVE=5m \
        -e OLLAMA_MAX_LOADED_MODELS=1 \
        --restart unless-stopped \
        ollama/ollama:latest
    
    # Wait with progress indicator
    log "Waiting for Ollama to initialize (this can take 3-5 minutes)..."
    for i in {1..300}; do  # 5 minutes timeout
        if docker ps | grep -q ai-scholar-ollama; then
            if curl -f http://localhost:11435/api/tags >/dev/null 2>&1; then
                log "✅ Ollama started successfully"
                break 2  # Break out of both loops
            fi
        else
            warn "Ollama container stopped unexpectedly"
            break
        fi
        
        # Show progress every 30 seconds
        if [ $((i % 30)) -eq 0 ]; then
            log "Still waiting for Ollama... ($((i/60)) minutes elapsed)"
        fi
        
        sleep 1
    done
    
    warn "Ollama attempt $ollama_attempts failed or timed out"
    if [ $ollama_attempts -eq $max_ollama_attempts ]; then
        warn "Ollama failed after $max_ollama_attempts attempts. Continuing without it."
        echo "Ollama logs:"
        docker logs ai-scholar-ollama --tail 30 2>/dev/null || echo "No logs available"
    else
        sleep 10
    fi
done

# Check which AI services are running
chromadb_running=false
ollama_running=false

if docker ps | grep -q ai-scholar-chromadb && \
   curl -f http://localhost:8081/api/v1/heartbeat >/dev/null 2>&1; then
    chromadb_running=true
fi

if docker ps | grep -q ai-scholar-ollama && \
   curl -f http://localhost:11435/api/tags >/dev/null 2>&1; then
    ollama_running=true
fi

# Application services are already started with minimal compose
log "Core application services are running..."

# Wait for application services
log "Waiting for application services..."
sleep 45

# Check service status
log "Checking service status..."
echo "=== Core Services ==="
docker-compose -f docker-compose.minimal.yml ps
echo
echo "=== AI Services ==="
docker ps --filter "name=ai-scholar-chromadb" --filter "name=ai-scholar-ollama" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Test endpoints
log "Testing service endpoints..."
endpoints=(
    "http://localhost:8080/health:Nginx Proxy"
    "http://localhost:8001/health:Backend"
    "http://localhost:3006/health:Frontend"
)

for endpoint in "${endpoints[@]}"; do
    IFS=':' read -r url name <<< "$endpoint"
    if timeout 10 curl -f "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $name is responding${NC}"
    else
        echo -e "${YELLOW}⚠️  $name is not responding yet${NC}"
    fi
done

# Test AI services
if [ "$chromadb_running" = true ]; then
    echo -e "${GREEN}✅ ChromaDB is running and healthy${NC}"
else
    echo -e "${YELLOW}⚠️  ChromaDB is not available${NC}"
fi

if [ "$ollama_running" = true ]; then
    echo -e "${GREEN}✅ Ollama is running and healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama is not available${NC}"
fi

# Success message
echo
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETED! 🎉${NC}"
echo
echo -e "${BLUE}=== ACCESS INFORMATION ===${NC}"
echo -e "🌐 Main App: ${GREEN}http://localhost:8080${NC} (nginx proxy)"
echo -e "🚀 Frontend: ${GREEN}http://localhost:3006${NC} (direct)"
echo -e "🔧 Backend: ${GREEN}http://localhost:8001${NC} (direct)"

if [ "$chromadb_running" = true ]; then
    echo -e "🔍 ChromaDB: ${GREEN}http://localhost:8081${NC}"
else
    echo -e "🔍 ChromaDB: ${YELLOW}Not available${NC}"
fi

if [ "$ollama_running" = true ]; then
    echo -e "🤖 Ollama: ${GREEN}http://localhost:11435${NC}"
else
    echo -e "🤖 Ollama: ${YELLOW}Not available${NC}"
fi

echo
echo -e "${BLUE}=== AI SERVICES STATUS ===${NC}"
if [ "$chromadb_running" = false ] && [ "$ollama_running" = false ]; then
    echo -e "${YELLOW}⚠️  Both AI services failed to start. The application will work but without:${NC}"
    echo "   • Vector search capabilities (ChromaDB)"
    echo "   • Local LLM inference (Ollama)"
    echo
    echo -e "${BLUE}To retry AI services later:${NC}"
    echo "   docker-compose -f docker-compose.prod.yml up -d chromadb ollama"
elif [ "$chromadb_running" = false ]; then
    echo -e "${YELLOW}⚠️  ChromaDB failed to start. Vector search will not be available.${NC}"
elif [ "$ollama_running" = false ]; then
    echo -e "${YELLOW}⚠️  Ollama failed to start. Local LLM inference will not be available.${NC}"
else
    echo -e "${GREEN}✅ All AI services are running successfully!${NC}"
fi

echo
log "🚀 Deployment completed!"