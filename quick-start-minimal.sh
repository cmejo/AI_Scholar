#!/bin/bash
# AI Scholar Minimal Quick Start Script
# Starts only essential services to get the application running

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
                                                       
  Minimal Quick Start for scholar.cmejo.com
EOF
echo -e "${NC}"

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    error "docker-compose.prod.yml not found. Please run this script from the project root directory."
fi

if [ ! -f ".env" ]; then
    error ".env file not found. Please ensure the .env file is present."
fi

log "Starting AI Scholar minimal deployment (core services only)..."

# Create missing directories
log "Creating missing directories and files..."
mkdir -p public data/{postgres,redis,chroma,ollama} logs uploads backups ssl config monitoring

# Fix permissions on data directories
log "Setting proper permissions on data directories..."
sudo chown -R $USER:$USER data/ logs/ uploads/ backups/ 2>/dev/null || true
chmod -R 755 data/ logs/ uploads/ backups/ 2>/dev/null || true

# Create vite.svg if it doesn't exist
if [ ! -f "public/vite.svg" ]; then
    cat > public/vite.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" aria-hidden="true" role="img" class="iconify iconify--logos" width="31.88" height="32" preserveAspectRatio="xMidYMid meet" viewBox="0 0 256 257"><defs><linearGradient id="IconifyId1813088fe1fbc01fb466" x1="-.828%" x2="57.636%" y1="7.652%" y2="78.411%"><stop offset="0%" stop-color="#41D1FF"></stop><stop offset="100%" stop-color="#BD34FE"></stop></linearGradient><linearGradient id="IconifyId1813088fe1fbc01fb467" x1="43.376%" x2="50.316%" y1="2.242%" y2="89.03%"><stop offset="0%" stop-color="#FFEA83"></stop><stop offset="8.333%" stop-color="#FFDD35"></stop><stop offset="100%" stop-color="#FFA800"></stop></linearGradient></defs><path fill="url(#IconifyId1813088fe1fbc01fb466)" d="M255.153 37.938L134.897 252.976c-2.483 4.44-8.862 4.466-11.382.048L.875 37.958c-2.746-4.814 1.371-10.646 6.827-9.67l120.385 21.517a6.537 6.537 0 0 0 2.322-.004l117.867-21.483c5.438-.991 9.574 4.796 6.877 9.62Z"></path><path fill="url(#IconifyId1813088fe1fbc01fb467)" d="M185.432.063L96.44 17.501a3.268 3.268 0 0 0-2.634 3.014l-5.474 92.456a3.268 3.268 0 0 0 3.997 3.378l24.777-5.718c2.318-.535 4.413 1.507 3.936 3.838l-7.361 36.047c-.495 2.426 1.782 4.5 4.151 3.78l15.304-4.649c2.372-.72 4.652 1.36 4.15 3.788l-11.698 56.621c-.732 3.542 3.979 5.473 5.943 2.437l1.313-2.028l72.516-144.72c1.215-2.423-.88-5.186-3.54-4.672l-25.505 4.922c-2.396.462-4.435-1.77-3.759-4.114l16.646-57.705c.677-2.35-1.37-4.583-3.769-4.113Z"></path></svg>
EOF
fi

# Create favicon.ico if it doesn't exist
touch public/favicon.ico 2>/dev/null || true

# Check Docker
if ! command -v docker &> /dev/null; then
    error "Docker not found. Please install Docker first."
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose not found. Please install Docker Compose first."
fi

# Check for port conflicts and stop conflicting services
log "Checking for port conflicts..."
ports_to_check=(3006 8001 5433 6380)

for port in "${ports_to_check[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        warn "Port $port is in use. Attempting to stop conflicting services..."
        
        # Get PIDs using the port
        pids=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null || true)
        
        # Try to stop Docker containers using these ports
        docker ps --format "table {{.Names}}\t{{.Ports}}" | grep ":$port->" | awk '{print $1}' | xargs -r docker stop 2>/dev/null || true
        
        # For Redis specifically, try to stop system Redis
        if [ "$port" = "6380" ]; then
            log "Stopping Redis services..."
            sudo systemctl stop redis-server 2>/dev/null || true
            sudo systemctl stop redis 2>/dev/null || true
            sudo systemctl disable redis-server 2>/dev/null || true
            sudo systemctl disable redis 2>/dev/null || true
            
            # Kill Redis processes if still running
            if [ -n "$pids" ]; then
                for pid in $pids; do
                    if ps -p $pid > /dev/null 2>&1; then
                        log "Killing Redis process $pid"
                        sudo kill -TERM $pid 2>/dev/null || true
                        sleep 2
                        if ps -p $pid > /dev/null 2>&1; then
                            sudo kill -KILL $pid 2>/dev/null || true
                        fi
                    fi
                done
            fi
        fi
        
        # For PostgreSQL specifically
        if [ "$port" = "5433" ]; then
            log "Stopping PostgreSQL services..."
            sudo systemctl stop postgresql 2>/dev/null || true
            sudo systemctl disable postgresql 2>/dev/null || true
            
            # Kill PostgreSQL processes if still running
            if [ -n "$pids" ]; then
                for pid in $pids; do
                    if ps -p $pid > /dev/null 2>&1; then
                        log "Killing PostgreSQL process $pid"
                        sudo kill -TERM $pid 2>/dev/null || true
                        sleep 2
                        if ps -p $pid > /dev/null 2>&1; then
                            sudo kill -KILL $pid 2>/dev/null || true
                        fi
                    fi
                done
            fi
        fi
        
        # For other ports, try to kill the processes
        if [ "$port" != "6380" ] && [ "$port" != "5433" ] && [ -n "$pids" ]; then
            for pid in $pids; do
                if ps -p $pid > /dev/null 2>&1; then
                    process_name=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
                    log "Killing process $pid ($process_name) using port $port"
                    sudo kill -TERM $pid 2>/dev/null || true
                    sleep 2
                    if ps -p $pid > /dev/null 2>&1; then
                        sudo kill -KILL $pid 2>/dev/null || true
                    fi
                fi
            done
        fi
        
        # Wait a moment for services to stop
        sleep 3
        
        # Check if port is still in use
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            error "Port $port is still in use after cleanup attempts. Please manually stop the service using this port and try again."
        else
            log "Port $port is now available"
        fi
    fi
done

# Create Docker network
log "Creating Docker network..."
docker network create ai-scholar-network 2>/dev/null || log "Network already exists"

# Stop any existing containers and clean up volumes
log "Stopping any existing containers..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

# Force stop any remaining AI Scholar containers
log "Force stopping any remaining AI Scholar containers..."
docker ps -a --filter "name=ai-scholar" --format "{{.Names}}" | xargs -r docker stop 2>/dev/null || true
docker ps -a --filter "name=ai-scholar" --format "{{.Names}}" | xargs -r docker rm 2>/dev/null || true

# Clean up conflicting volumes
log "Cleaning up conflicting volumes..."
docker volume rm ai_scholar_redis_data 2>/dev/null || true
docker volume rm ai_scholar_postgres_data 2>/dev/null || true
docker volume rm ai_scholar_chroma_data 2>/dev/null || true
docker volume rm ai_scholar_ollama_data 2>/dev/null || true

# Prune unused Docker resources
log "Cleaning up unused Docker resources..."
docker system prune -f 2>/dev/null || true

# Build images
log "Building Docker images..."
docker-compose -f docker-compose.prod.yml build

# Start only essential services (skip ChromaDB and Ollama for now)
log "Starting essential services (postgres, redis)..."
DOCKER_BUILDKIT=1 docker-compose -f docker-compose.prod.yml up -d postgres redis

log "Waiting for essential services to be healthy..."
for i in {1..60}; do
    if docker-compose -f docker-compose.prod.yml ps postgres | grep -q "healthy" && \
       docker-compose -f docker-compose.prod.yml ps redis | grep -q "healthy"; then
        log "Essential services are healthy"
        break
    fi
    if [ $i -eq 60 ]; then
        error "Essential services failed to start properly"
    fi
    sleep 2
done

log "Starting application services..."
DOCKER_BUILDKIT=1 docker-compose -f docker-compose.prod.yml up -d backend frontend nginx

# Wait and test
log "Waiting for application services to be ready..."
sleep 30

# Check service status first
log "Checking service status..."
docker-compose -f docker-compose.prod.yml ps

# Test endpoints
log "Testing service endpoints..."
endpoints=(
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

# Success message
echo
echo -e "${GREEN}🎉 MINIMAL DEPLOYMENT COMPLETED! 🎉${NC}"
echo
echo -e "${BLUE}=== ACCESS INFORMATION ===${NC}"
echo -e "🌐 Domain: ${GREEN}scholar.cmejo.com${NC}"
echo -e "🚀 Frontend: ${GREEN}http://localhost:3006${NC}"
echo -e "🔧 Backend: ${GREEN}http://localhost:8001${NC}"
echo
echo -e "${YELLOW}=== NOTES ===${NC}"
echo "• ChromaDB and Ollama were skipped to avoid startup issues"
echo "• You can add them later once the core application is working"
echo "• To add monitoring: ${BLUE}docker-compose -f docker-compose.prod.yml --profile monitoring up -d${NC}"
echo
log "🚀 Minimal deployment completed successfully!"