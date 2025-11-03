# AI Scholar Monthly Cronjob Setup Guide

This guide helps you set up automated monthly updates for AI Scholar that will download, process, and store all papers from the previous month.

## Quick Setup (Recommended)

Run the automated setup script:

```bash
cd backend
chmod +x setup_monthly_cronjob.sh
./setup_monthly_cronjob.sh
```

This script will:
- Create a wrapper script for better error handling
- Set up logging
- Configure the cronjob interactively
- Test the setup

## Manual Setup

### 1. Choose Your Schedule

**Option A: 1st of every month at 2:00 AM**
```bash
0 2 1 * * /path/to/your/project/backend/run_monthly_update.sh
```

**Option B: 2nd of every month at 3:00 AM (Recommended)**
```bash
0 3 2 * * /path/to/your/project/backend/run_monthly_update.sh
```

### 2. Create the Wrapper Script

Create `backend/run_monthly_update.sh`:

```bash
#!/bin/bash
set -e

# Configuration - UPDATE THESE PATHS
PROJECT_ROOT="/path/to/your/AI_Scholar-v2"
PYTHON_PATH="/usr/bin/python3"
LOG_FILE="/path/to/your/AI_Scholar-v2/logs/ai_scholar_monthly_cron.log"

# Create logs directory
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log with timestamp
log_with_timestamp() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Start logging
log_with_timestamp "=== AI Scholar Monthly Update Started ==="

# Change to project directory
cd "$PROJECT_ROOT"

# Run the monthly update
log_with_timestamp "Starting monthly update process..."
if "$PYTHON_PATH" backend/ai_scholar_monthly_update.py --email --cleanup --max-papers 0 >> "$LOG_FILE" 2>&1; then
    log_with_timestamp "Monthly update completed successfully"
    exit 0
else
    log_with_timestamp "Monthly update failed with exit code $?"
    exit 1
fi
```

### 3. Make Script Executable

```bash
chmod +x backend/run_monthly_update.sh
```

### 4. Add to Crontab

```bash
# Edit crontab
crontab -e

# Add one of these lines:
# Run on 2nd of every month at 3:00 AM (recommended)
0 3 2 * * /path/to/your/project/backend/run_monthly_update.sh

# Or run on 1st of every month at 2:00 AM
0 2 1 * * /path/to/your/project/backend/run_monthly_update.sh
```

## What the Monthly Update Does

The monthly update script will:

1. **Download papers** from the previous month for AI Scholar categories:
   - cond-mat, gr-qc, hep-ph, hep-th, math, math-ph, physics, q-alg, quant-ph

2. **Process papers** into your vector database:
   - Extract text and metadata
   - Generate embeddings
   - Store in ChromaDB

3. **Send email reports** (if configured):
   - Processing statistics
   - Error summaries
   - Storage usage

4. **Cleanup old files** (if enabled):
   - Remove temporary files
   - Archive old data

## Configuration Options

### Command Line Options

```bash
# Basic monthly update
python backend/ai_scholar_monthly_update.py

# Process specific month
python backend/ai_scholar_monthly_update.py --month 2024-10

# With email and cleanup
python backend/ai_scholar_monthly_update.py --email --cleanup

# Unlimited papers (recommended for monthly updates)
python backend/ai_scholar_monthly_update.py --max-papers 0
```

### Config File

The script uses `backend/multi_instance_arxiv_system/configs/ai_scholar.yaml` for configuration.

## Monitoring

### View Cronjob Status

```bash
# List current cronjobs
crontab -l

# View recent cron logs (system-wide)
sudo tail -f /var/log/cron

# View AI Scholar specific logs
tail -f logs/ai_scholar_monthly_cron.log
```

### Test the Setup

```bash
# Test the wrapper script manually
./backend/run_monthly_update.sh

# Test with limited papers
python backend/ai_scholar_monthly_update.py --max-papers 10 --verbose
```

## Troubleshooting

### Common Issues

1. **Python not found**
   - Update `PYTHON_PATH` in the wrapper script
   - Use `which python3` to find the correct path

2. **Config file not found**
   - Ensure `backend/multi_instance_arxiv_system/configs/ai_scholar.yaml` exists
   - Check file permissions

3. **ChromaDB not running**
   - Ensure ChromaDB is running on localhost:8082
   - Start it before the cronjob runs

4. **Permission denied**
   - Make sure the wrapper script is executable: `chmod +x run_monthly_update.sh`
   - Check directory permissions

### Email Notifications

To enable email notifications, configure SMTP settings in your config file:

```yaml
notifications:
  enabled: true
  recipients:
    - "your-email@example.com"
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  smtp_username: "your-username"
  smtp_password: "your-app-password"
```

## Security Considerations

1. **File Permissions**: Ensure log files and scripts have appropriate permissions
2. **Email Credentials**: Store email credentials securely
3. **Resource Limits**: Monitor disk space and memory usage
4. **Network Access**: Ensure the system can access arXiv and other sources

## Example Cron Schedule Formats

```bash
# Every 1st of month at 2:00 AM
0 2 1 * *

# Every 2nd of month at 3:00 AM  
0 3 2 * *

# Every Sunday at 1:00 AM (weekly)
0 1 * * 0

# Every day at 4:00 AM (daily)
0 4 * * *
```

## Next Steps

After setting up the cronjob:

1. **Monitor the first run** to ensure it works correctly
2. **Check logs regularly** for any issues
3. **Set up email notifications** for automated reporting
4. **Configure storage monitoring** to prevent disk space issues
5. **Consider setting up similar cronjobs** for Quant Scholar if needed

The system will now automatically keep your AI Scholar database up-to-date with the latest research papers!