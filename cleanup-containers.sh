#!/bin/bash
# Clean up all AI Scholar containers and start fresh

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

echo -e "${BLUE}=== AI Scholar Container Cleanup ===${NC}"
echo

# Stop all docker-compose services
log "Stopping docker-compose services..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
docker-compose -f docker-compose.minimal.yml down 2>/dev/null || true

# Stop all AI Scholar containers
log "Stopping all AI Scholar containers..."
containers=$(docker ps -a --filter "name=ai-scholar" --format "{{.Names}}" 2>/dev/null || true)
if [ -n "$containers" ]; then
    echo "$containers" | xargs -r docker stop 2>/dev/null || true
    echo "$containers" | xargs -r docker rm -f 2>/dev/null || true
    log "Removed containers: $containers"
else
    log "No AI Scholar containers found"
fi

# Stop test containers
log "Cleaning up test containers..."
test_containers="test-chromadb test-ollama quick-test-chromadb test-nginx test-backend"
for container in $test_containers; do
    docker stop $container 2>/dev/null || true
    docker rm $container 2>/dev/null || true
done

# Clean up volumes (optional - uncomment if you want to reset data)
# log "Cleaning up volumes..."
# docker volume rm ai_scholar_postgres_data ai_scholar_redis_data ai_scholar_chroma_data ai_scholar_ollama_data 2>/dev/null || true

# Clean up networks
log "Cleaning up networks..."
docker network rm ai-scholar-network 2>/dev/null || true

# Show current status
log "Current container status:"
docker ps -a --filter "name=ai-scholar" --format "table {{.Names}}\t{{.Status}}" || echo "No AI Scholar containers found"

echo
echo -e "${GREEN}✅ Cleanup completed!${NC}"
echo
echo -e "${BLUE}Now you can run a fresh deployment:${NC}"
echo "  ./quick-start-minimal.sh        # Minimal deployment"
echo "  ./deploy-with-ai-services.sh    # Full deployment with AI services"