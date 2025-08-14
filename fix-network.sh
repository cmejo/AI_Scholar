#!/bin/bash
# Quick fix for the network issue

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

log "Cleaning up any existing network..."
docker network rm ai-scholar-network 2>/dev/null || true

log "Creating ai-scholar-network..."
docker network create ai-scholar-network --driver bridge --subnet 172.25.0.0/16

log "Verifying network exists..."
if docker network ls | grep -q ai-scholar-network; then
    log "✅ Network created successfully"
    docker network inspect ai-scholar-network --format '{{.Name}}: {{.Driver}} ({{range .IPAM.Config}}{{.Subnet}}{{end}})'
else
    error "❌ Failed to create network"
fi

log "Network is ready for deployment!"