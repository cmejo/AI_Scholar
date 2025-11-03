#!/bin/bash

# AI Scholar Monthly Update Cronjob Setup Script
# This script sets up automated monthly updates for AI Scholar

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_PATH="/usr/bin/python3"  # Adjust if needed
LOG_DIR="$PROJECT_ROOT/logs"
CRON_LOG="$LOG_DIR/ai_scholar_monthly_cron.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}AI Scholar Monthly Update Cronjob Setup${NC}"
echo "========================================"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found. Please install Python 3.${NC}"
    exit 1
fi

# Check if the AI Scholar script exists
AI_SCHOLAR_SCRIPT="$SCRIPT_DIR/ai_scholar_monthly_update.py"
if [ ! -f "$AI_SCHOLAR_SCRIPT" ]; then
    echo -e "${RED}Error: AI Scholar monthly update script not found at $AI_SCHOLAR_SCRIPT${NC}"
    exit 1
fi

# Check if config file exists
CONFIG_FILE="$SCRIPT_DIR/multi_instance_arxiv_system/configs/ai_scholar.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}Warning: Config file not found at $CONFIG_FILE${NC}"
    echo "Please ensure the config file exists before running the cronjob."
fi

# Create the cronjob command
CRON_COMMAND="cd $PROJECT_ROOT && $PYTHON_PATH $AI_SCHOLAR_SCRIPT --email --cleanup --max-papers 0 >> $CRON_LOG 2>&1"

# Create a wrapper script for better error handling
WRAPPER_SCRIPT="$SCRIPT_DIR/run_monthly_update.sh"
cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash

# AI Scholar Monthly Update Wrapper Script
# Generated on $(date)

set -e

# Configuration
PROJECT_ROOT="$PROJECT_ROOT"
PYTHON_PATH="$PYTHON_PATH"
AI_SCHOLAR_SCRIPT="$AI_SCHOLAR_SCRIPT"
LOG_FILE="$CRON_LOG"

# Function to log with timestamp
log_with_timestamp() {
    echo "\$(date '+%Y-%m-%d %H:%M:%S') - \$1" >> "\$LOG_FILE"
}

# Start logging
log_with_timestamp "=== AI Scholar Monthly Update Started ==="
log_with_timestamp "Working directory: \$PROJECT_ROOT"
log_with_timestamp "Python path: \$PYTHON_PATH"
log_with_timestamp "Script path: \$AI_SCHOLAR_SCRIPT"

# Change to project directory
cd "\$PROJECT_ROOT"

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
if "\$PYTHON_PATH" "\$AI_SCHOLAR_SCRIPT" --email --cleanup --max-papers 0 >> "\$LOG_FILE" 2>&1; then
    log_with_timestamp "Monthly update completed successfully"
    exit 0
else
    log_with_timestamp "Monthly update failed with exit code \$?"
    exit 1
fi
EOF

# Make wrapper script executable
chmod +x "$WRAPPER_SCRIPT"

echo -e "${GREEN}✓${NC} Created wrapper script: $WRAPPER_SCRIPT"

# Display cronjob options
echo ""
echo -e "${YELLOW}Cronjob Setup Options:${NC}"
echo "======================"
echo ""
echo "1. Run on the 1st of every month at 2:00 AM:"
echo "   0 2 1 * * $WRAPPER_SCRIPT"
echo ""
echo "2. Run on the 1st of every month at 6:00 AM:"
echo "   0 6 1 * * $WRAPPER_SCRIPT"
echo ""
echo "3. Run on the 2nd of every month at 3:00 AM (safer, avoids month-end issues):"
echo "   0 3 2 * * $WRAPPER_SCRIPT"
echo ""

# Function to add cronjob
add_cronjob() {
    local cron_schedule="$1"
    local description="$2"
    
    # Check if cronjob already exists
    if crontab -l 2>/dev/null | grep -q "$WRAPPER_SCRIPT"; then
        echo -e "${YELLOW}Warning: A cronjob for AI Scholar already exists.${NC}"
        echo "Current cronjobs:"
        crontab -l 2>/dev/null | grep "$WRAPPER_SCRIPT" || true
        echo ""
        read -p "Do you want to replace it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Cronjob setup cancelled."
            return 1
        fi
        
        # Remove existing cronjob
        (crontab -l 2>/dev/null | grep -v "$WRAPPER_SCRIPT") | crontab -
        echo -e "${GREEN}✓${NC} Removed existing cronjob"
    fi
    
    # Add new cronjob
    (crontab -l 2>/dev/null; echo "$cron_schedule $WRAPPER_SCRIPT  # $description") | crontab -
    echo -e "${GREEN}✓${NC} Added cronjob: $description"
    echo "   Schedule: $cron_schedule"
    echo "   Command: $WRAPPER_SCRIPT"
}

# Interactive setup
echo -e "${YELLOW}Would you like to set up the cronjob now?${NC}"
echo "1) Yes, run on 1st of month at 2:00 AM"
echo "2) Yes, run on 1st of month at 6:00 AM" 
echo "3) Yes, run on 2nd of month at 3:00 AM (recommended)"
echo "4) No, I'll set it up manually"
echo ""
read -p "Choose an option (1-4): " -n 1 -r
echo ""

case $REPLY in
    1)
        add_cronjob "0 2 1 * *" "AI Scholar Monthly Update - 1st at 2AM"
        ;;
    2)
        add_cronjob "0 6 1 * *" "AI Scholar Monthly Update - 1st at 6AM"
        ;;
    3)
        add_cronjob "0 3 2 * *" "AI Scholar Monthly Update - 2nd at 3AM"
        ;;
    4)
        echo "Manual setup chosen. Use one of the cron schedules shown above."
        ;;
    *)
        echo "Invalid option. Manual setup required."
        ;;
esac

echo ""
echo -e "${GREEN}Setup Complete!${NC}"
echo "==============="
echo ""
echo "Files created:"
echo "  - Wrapper script: $WRAPPER_SCRIPT"
echo "  - Log file will be: $CRON_LOG"
echo ""
echo "To view current cronjobs:"
echo "  crontab -l"
echo ""
echo "To view logs:"
echo "  tail -f $CRON_LOG"
echo ""
echo "To test the script manually:"
echo "  $WRAPPER_SCRIPT"
echo ""
echo "To remove the cronjob:"
echo "  crontab -e  # then delete the line with AI Scholar"
echo ""

# Test the wrapper script
echo -e "${YELLOW}Would you like to test the wrapper script now? (y/N):${NC}"
read -p "" -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Testing wrapper script..."
    echo "This will run a dry-run of the monthly update process."
    echo ""
    # Run with a small limit for testing
    cd "$PROJECT_ROOT"
    if "$PYTHON_PATH" "$AI_SCHOLAR_SCRIPT" --max-papers 5 --verbose; then
        echo -e "${GREEN}✓${NC} Test completed successfully!"
    else
        echo -e "${RED}✗${NC} Test failed. Please check the configuration."
    fi
fi

echo ""
echo -e "${GREEN}All done! Your AI Scholar will now update automatically.${NC}"