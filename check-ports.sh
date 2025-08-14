#!/bin/bash
# Check what's using common web ports

echo "=== Port Usage Check ==="
echo

ports=(80 443 8080 8443 3006 8001 5433 6380)

for port in "${ports[@]}"; do
    echo "Port $port:"
    if lsof -Pi :$port -sTCP:LISTEN >/dev/null 2>&1; then
        echo "  ❌ IN USE:"
        lsof -Pi :$port -sTCP:LISTEN | head -5
    else
        echo "  ✅ Available"
    fi
    echo
done

echo "=== Common Services to Stop ==="
echo "If port 80 is in use, try:"
echo "  sudo systemctl stop apache2"
echo "  sudo systemctl stop nginx"
echo "  sudo systemctl stop lighttpd"
echo
echo "If port 443 is in use, try:"
echo "  sudo systemctl stop apache2"
echo "  sudo systemctl stop nginx"