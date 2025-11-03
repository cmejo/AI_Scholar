#!/bin/bash

# AI Scholar Monthly Update Wrapper Script
# Generated on Sat Oct 25 03:37:14 PM UTC 2025

set -e

# Configuration
PROJECT_ROOT="/home/cmejo/AI_Scholar-v2"
PYTHON_PATH="/usr/bin/python3"
AI_SCHOLAR_SCRIPT="/home/cmejo/AI_Scholar-v2/backend/ai_scholar_monthly_update.py"
LOG_FILE="/home/cmejo/AI_Scholar-v2/logs/ai_scholar_monthly_cron.log"

# Function to log with timestamp
log_with_timestamp() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Start logging
log_with_timestamp "=== AI Scholar Monthly Update Started ==="
log_with_timestamp "Working directory: $PROJECT_ROOT"
log_with_timestamp "Python path: $PYTHON_PATH"
log_with_timestamp "Script path: $AI_SCHOLAR_SCRIPT"

# Change to project directory
cd "$PROJECT_ROOT"

# Check if ChromaDB is running (optional)
if command -v curl &> /dev/null; then
    if curl -s http://localhost:8082/api/v1/heartbeat &> /dev/null; then
        log_with_timestamp "ChromaDB is running"
    else
        log_with_timestamp "Warning: ChromaDB may not be running on localhost:8082"
    fi
fi

# Run the monthly update
log_with_timestamp "Starting monthly update process..."
if "$PYTHON_PATH" "$AI_SCHOLAR_SCRIPT" --config backend/multi_instance_arxiv_system/configs/ai_scholar.yaml --email --cleanup --max-papers 0 >> "$LOG_FILE" 2>&1; then
    log_with_timestamp "Monthly update completed successfully"
    exit 0
else
    log_with_timestamp "Monthly update failed with exit code $?"
    exit 1
fi
