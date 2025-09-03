#!/bin/bash
# Quick ChromaDB log checker

echo "=== ChromaDB Container Status ==="
docker ps -a | grep chroma || echo "No ChromaDB containers found"

echo
echo "=== Recent ChromaDB Logs ==="
for container in $(docker ps -a --filter "name=chroma" --format "{{.Names}}"); do
    echo "--- Logs for $container ---"
    docker logs $container --tail 50 2>&1 || echo "No logs available"
    echo
done

echo "=== Quick ChromaDB Test ==="
echo "Testing if we can start a basic ChromaDB container..."

# Clean up
docker stop quick-test-chromadb 2>/dev/null || true
docker rm quick-test-chromadb 2>/dev/null || true

# Start basic ChromaDB
docker run -d --name quick-test-chromadb \
    -p 8082:8000 \
    -e CHROMA_SERVER_HOST=0.0.0.0 \
    chromadb/chroma:0.4.18

sleep 10

if docker ps | grep -q quick-test-chromadb; then
    echo "✅ Basic ChromaDB container started"
    if curl -f http://localhost:8082/api/v1/heartbeat >/dev/null 2>&1; then
        echo "✅ ChromaDB API is responding"
    else
        echo "❌ ChromaDB API not responding"
    fi
else
    echo "❌ ChromaDB container failed to start"
fi

echo "--- Quick test logs ---"
docker logs quick-test-chromadb --tail 20 2>&1 || echo "No logs"

# Cleanup
docker stop quick-test-chromadb 2>/dev/null || true
docker rm quick-test-chromadb 2>/dev/null || true