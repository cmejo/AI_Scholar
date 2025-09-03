#!/bin/bash
# Simple wrapper script for codebase analysis

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}AI Scholar Codebase Analysis${NC}"
echo "=============================="

# Check if comprehensive runner exists
if [[ -f "scripts/run-comprehensive-analysis.sh" ]]; then
    echo -e "${GREEN}Running comprehensive analysis...${NC}"
    ./scripts/run-comprehensive-analysis.sh "$@"
else
    echo "Comprehensive analysis script not found. Running basic analysis..."
    
    # Fallback to basic Python script
    if [[ -f "scripts/codebase-analysis.py" ]]; then
        python3 scripts/codebase-analysis.py "$@"
    else
        echo "Error: No analysis scripts found!"
        exit 1
    fi
fi