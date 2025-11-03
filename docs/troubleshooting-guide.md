# Multi-Instance ArXiv System - Troubleshooting Guide

## Overview

This guide provides solutions to common issues encountered when running the Multi-Instance ArXiv System. Issues are organized by category with step-by-step resolution procedures.

## Quick Diagnostic Commands

Before diving into specific issues, run these commands to get system status:

```bash
# System health check
python -m backend.multi_instance_arxiv_system.scripts.system_health_check --verbose

# Storage analysis
python -m backend.multi_instance_arxiv_system.scripts.storage_manager analyze

# Monitor system status
python -m backend.multi_instance_arxiv_system.scripts.multi_instance_monitor

# Check logs
tail -f logs/system.log
```

## Installation and Setup Issues

### 1. Python Import Errors

**Symptoms:**
```
ImportError: No module named 'multi_instance_arxiv_system'
ModuleNotFoundError: No module named 'chromadb'
```

**Solutions:**

1. **Verify Virtual Environment:**
   ```bash
   # Check if virtual environment is activated
   which python
   # Should show path to venv/bin/python
   
   # Activate if not active
   source venv/bin/activate
   ```

2. **Reinstall Dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

3. **Check Python Path:**
   ```bash
   python -c "import sys; print('\n'.join(sys.path))"
   # Ensure project directory is in path
   ```

4. **Install in Development Mode:**
   ```bash
   pip install -e .
   ```

### 2. ChromaDB Connection Issues

**Symptoms:**
```
ConnectionError: Could not connect to ChromaDB at localhost:8000
requests.exceptions.ConnectionError
```

**Solutions:**

1. **Check ChromaDB Status:**
   ```bash
   # Check if ChromaDB container is running
   docker ps | grep chromadb
   
   # Check ChromaDB health
   curl http://localhost:8000/api/v1/heartbeat
   ```

2. **Start ChromaDB:**
   ```bash
   # Start ChromaDB container
   docker run -d --name chromadb -p 8000:8000 chromadb/chroma:latest
   
   # Or restart existing container
   docker restart chromadb
   ```

3. **Check Port Conflicts:**
   ```bash
   # Check what's using port 8000
   sudo netstat -tulpn | grep 8000
   
   # Use different port if needed
   docker run -d --name chromadb -p 8001:8000 chromadb/chroma:latest
   # Update CHROMA_PORT in .env file
   ```

4. **Check Docker Installation:**
   ```bash
   docker --version
   docker info
   
   # If Docker not running
   sudo systemctl start docker
   ```

### 3. Permission Errors

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/path/to/data'
OSError: [Errno 13] Permission denied
```

**Solutions:**

1. **Fix Directory Permissions:**
   ```bash
   # Create directories with correct permissions
   mkdir -p data/{ai_scholar,quant_scholar}/{papers,logs,cache,reports}
   chmod -R 755 data/
   chown -R $USER:$USER data/
   ```

2. **Fix Log Permissions:**
   ```bash
   mkdir -p logs
   chmod 755 logs/
   touch logs/system.log
   chmod 644 logs/system.log
   ```

3. **Fix Config Permissions:**
   ```bash
   chmod 644 config/*.yaml
   chmod 600 .env  # Secure environment file
   ```

## Configuration Issues

### 1. Invalid Configuration Files

**Symptoms:**
```
yaml.scanner.ScannerError: mapping values are not allowed here
ValueError: Invalid configuration: missing required field 'instance_name'
```

**Solutions:**

1. **Validate YAML Syntax:**
   ```bash
   # Check YAML syntax
   python -c "
   import yaml
   with open('config/ai_scholar.yaml') as f:
       config = yaml.safe_load(f)
       print('YAML is valid')
   "
   ```

2. **Check Required Fields:**
   ```bash
   # Validate configuration
   python -c "
   from backend.multi_instance_arxiv_system.core.instance_config import InstanceConfigManager
   manager = InstanceConfigManager('config')
   config = manager.load_instance_config('ai_scholar')
   print('Configuration is valid')
   "
   ```

3. **Common YAML Issues:**
   - **Indentation:** Use spaces, not tabs
   - **Quotes:** Use quotes for strings with special characters
   - **Lists:** Ensure proper list formatting with `-`
   - **Colons:** Space after colons in key-value pairs

4. **Example Fix:**
   ```yaml
   # Wrong
   arxiv_categories:
   - cs.AI
   - cs.LG
   
   # Correct
   arxiv_categories:
     - "cs.AI"
     - "cs.LG"
   ```

### 2. Path Configuration Issues

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: '/path/to/storage'
OSError: Storage path is not writable
```

**Solutions:**

1. **Create Missing Directories:**
   ```bash
   # Create all required directories
   python -c "
   import os
   from pathlib import Path
   
   base_paths = ['data/ai_scholar', 'data/quant_scholar']
   subdirs = ['papers', 'logs', 'cache', 'reports']
   
   for base in base_paths:
       for subdir in subdirs:
           Path(base, subdir).mkdir(parents=True, exist_ok=True)
           print(f'Created {base}/{subdir}')
   "
   ```

2. **Check Path Permissions:**
   ```bash
   # Test write permissions
   python -c "
   import tempfile
   from pathlib import Path
   
   test_path = Path('data/ai_scholar')
   try:
       with tempfile.NamedTemporaryFile(dir=test_path, delete=True):
           print(f'{test_path} is writable')
   except Exception as e:
       print(f'Error: {e}')
   "
   ```

3. **Use Absolute Paths:**
   ```yaml
   # In config file, use absolute paths
   storage_path: "/home/user/arxiv-system/data/ai_scholar"
   ```

## Runtime Issues

### 1. Download Failures

**Symptoms:**
```
requests.exceptions.HTTPError: 429 Client Error: Too Many Requests
requests.exceptions.Timeout: Request timed out
ConnectionError: Failed to download paper
```

**Solutions:**

1. **Rate Limiting Issues:**
   ```bash
   # Reduce concurrent downloads
   # In config file:
   processing:
     max_concurrent: 2  # Reduce from default 4
   
   # Add delays between requests
   python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_downloader \
     --delay 2 --limit 50
   ```

2. **Network Timeout Issues:**
   ```bash
   # Increase timeout values
   export REQUEST_TIMEOUT=60
   
   # Use retry with backoff
   python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_downloader \
     --max-retries 5 --retry-delay 30
   ```

3. **Check Network Connectivity:**
   ```bash
   # Test ArXiv connectivity
   curl -I https://arxiv.org/abs/2301.00001
   
   # Test with proxy if needed
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080
   ```

4. **Check ArXiv API Status:**
   ```bash
   # Check ArXiv API
   curl "http://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=1"
   ```

### 2. PDF Processing Errors

**Symptoms:**
```
PyMuPDF error: cannot open document
PDFSyntaxError: EOF marker not found
UnicodeDecodeError: 'utf-8' codec can't decode
```

**Solutions:**

1. **Install PDF Dependencies:**
   ```bash
   # Ubuntu/Debian
   sudo apt install -y poppler-utils ghostscript tesseract-ocr
   
   # macOS
   brew install poppler ghostscript tesseract
   
   # Test installation
   pdfinfo --version
   gs --version
   ```

2. **Handle Corrupted PDFs:**
   ```bash
   # Enable PDF validation
   # In config file:
   processing:
     validate_pdfs: true
     skip_on_error: true
   
   # Test PDF processing
   python -c "
   import fitz
   doc = fitz.open('path/to/test.pdf')
   print(f'PDF has {doc.page_count} pages')
   doc.close()
   "
   ```

3. **Memory Issues with Large PDFs:**
   ```bash
   # Reduce batch size for large PDFs
   # In config file:
   processing:
     batch_size: 20  # Reduce from default 50
     chunk_size: 800  # Reduce from default 1000
   ```

4. **Alternative PDF Libraries:**
   ```bash
   # Install alternative PDF processors
   pip install pdfplumber pypdf2 pdfminer.six
   ```

### 3. Vector Store Issues

**Symptoms:**
```
chromadb.errors.InvalidCollectionException: Collection does not exist
ValueError: Embedding dimension mismatch
RuntimeError: CUDA out of memory
```

**Solutions:**

1. **Collection Issues:**
   ```bash
   # List existing collections
   python -c "
   import chromadb
   client = chromadb.HttpClient(host='localhost', port=8000)
   collections = client.list_collections()
   print([c.name for c in collections])
   "
   
   # Create missing collection
   python -c "
   import chromadb
   client = chromadb.HttpClient(host='localhost', port=8000)
   collection = client.create_collection('ai_scholar_papers')
   print('Collection created')
   "
   ```

2. **Embedding Model Issues:**
   ```bash
   # Test embedding model
   python -c "
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
   embeddings = model.encode(['test sentence'])
   print(f'Embedding dimension: {embeddings.shape[1]}')
   "
   
   # Clear model cache if needed
   rm -rf ~/.cache/torch/sentence_transformers/
   ```

3. **Memory Issues:**
   ```bash
   # Use CPU-only embeddings
   export CUDA_VISIBLE_DEVICES=""
   
   # Reduce batch size
   # In config file:
   processing:
     batch_size: 10
   
   # Use smaller embedding model
   vector_store:
     embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
   ```

4. **ChromaDB Persistence Issues:**
   ```bash
   # Check ChromaDB data directory
   docker exec chromadb ls -la /chroma/chroma
   
   # Backup and reset if needed
   docker stop chromadb
   docker rm chromadb
   docker run -d --name chromadb -p 8000:8000 \
     -v chromadb_data:/chroma/chroma chromadb/chroma:latest
   ```

## Performance Issues

### 1. Slow Processing

**Symptoms:**
- Processing takes much longer than expected
- High CPU/memory usage
- System becomes unresponsive

**Solutions:**

1. **Optimize Concurrency:**
   ```bash
   # Check system resources
   htop
   free -h
   df -h
   
   # Adjust concurrency settings
   # In config file:
   processing:
     max_concurrent: 2  # Reduce if system is overloaded
     batch_size: 25     # Reduce batch size
   ```

2. **Monitor Resource Usage:**
   ```bash
   # Monitor during processing
   python -m backend.multi_instance_arxiv_system.scripts.multi_instance_monitor \
     --continuous 5
   
   # Check memory usage
   python -c "
   import psutil
   print(f'Memory usage: {psutil.virtual_memory().percent}%')
   print(f'CPU usage: {psutil.cpu_percent(interval=1)}%')
   "
   ```

3. **Optimize Embedding Model:**
   ```yaml
   # Use faster embedding model
   vector_store:
     embedding_model: "sentence-transformers/all-MiniLM-L6-v2"  # Fastest
     # embedding_model: "sentence-transformers/all-mpnet-base-v2"  # Better quality but slower
   ```

4. **Enable Caching:**
   ```bash
   # Ensure cache directory exists and is writable
   mkdir -p data/ai_scholar/cache
   chmod 755 data/ai_scholar/cache
   ```

### 2. High Memory Usage

**Symptoms:**
```
MemoryError: Unable to allocate memory
OSError: [Errno 12] Cannot allocate memory
```

**Solutions:**

1. **Reduce Memory Usage:**
   ```yaml
   # In config file
   processing:
     batch_size: 10      # Reduce from default 50
     max_concurrent: 1   # Process one at a time
     chunk_size: 500     # Reduce chunk size
   ```

2. **Monitor Memory:**
   ```bash
   # Add memory monitoring
   python -c "
   import psutil
   import time
   
   while True:
       mem = psutil.virtual_memory()
       print(f'Memory: {mem.percent}% used, {mem.available/1024**3:.1f}GB available')
       time.sleep(5)
   "
   ```

3. **Use Swap Space:**
   ```bash
   # Check swap
   swapon --show
   
   # Add swap if needed (Ubuntu)
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

4. **Process in Smaller Batches:**
   ```bash
   # Process papers in smaller groups
   python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_processor \
     --batch-size 5 --max-papers 100
   ```

## Email and Notification Issues

### 1. Email Sending Failures

**Symptoms:**
```
SMTPAuthenticationError: Username and Password not accepted
SMTPConnectError: Connection refused
```

**Solutions:**

1. **Check SMTP Configuration:**
   ```bash
   # Test SMTP connection
   python -c "
   import smtplib
   import os
   
   smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
   smtp_port = int(os.getenv('SMTP_PORT', '587'))
   
   try:
       server = smtplib.SMTP(smtp_host, smtp_port)
       server.starttls()
       print('SMTP connection successful')
       server.quit()
   except Exception as e:
       print(f'SMTP error: {e}')
   "
   ```

2. **Gmail App Passwords:**
   ```bash
   # For Gmail, use app-specific password
   # 1. Enable 2FA on Gmail account
   # 2. Generate app password: https://myaccount.google.com/apppasswords
   # 3. Use app password in SMTP_PASSWORD
   ```

3. **Test Email Sending:**
   ```bash
   # Test email functionality
   python -c "
   from backend.multi_instance_arxiv_system.reporting.email_notification_service import EmailNotificationService
   
   service = EmailNotificationService()
   success = service.send_test_email('your-email@example.com')
   print(f'Email test: {'Success' if success else 'Failed'}')
   "
   ```

4. **Alternative SMTP Providers:**
   ```bash
   # Outlook/Hotmail
   SMTP_HOST=smtp-mail.outlook.com
   SMTP_PORT=587
   
   # Yahoo
   SMTP_HOST=smtp.mail.yahoo.com
   SMTP_PORT=587
   
   # Custom SMTP
   SMTP_HOST=mail.yourcompany.com
   SMTP_PORT=587
   ```

### 2. Missing Notifications

**Symptoms:**
- No email notifications received
- Notifications not being triggered

**Solutions:**

1. **Check Notification Configuration:**
   ```yaml
   # In config file
   notifications:
     email:
       enabled: true
       recipients:
         - "admin@example.com"
       on_success: true
       on_error: true
   ```

2. **Check Email Logs:**
   ```bash
   # Check email-specific logs
   grep -i "email\|smtp\|notification" logs/system.log
   
   # Check for email errors
   grep -i "error.*email" logs/system.log
   ```

3. **Test Notification Triggers:**
   ```bash
   # Manually trigger notification
   python -c "
   from backend.multi_instance_arxiv_system.reporting.email_notification_service import EmailNotificationService
   
   service = EmailNotificationService()
   service.send_notification(
       subject='Test Notification',
       message='This is a test notification',
       recipients=['your-email@example.com']
   )
   "
   ```

## Storage and Disk Issues

### 1. Disk Space Issues

**Symptoms:**
```
OSError: [Errno 28] No space left on device
IOError: Not enough space on disk
```

**Solutions:**

1. **Check Disk Usage:**
   ```bash
   # Check overall disk usage
   df -h
   
   # Check directory sizes
   du -sh data/*
   du -sh logs/
   
   # Find large files
   find data/ -type f -size +100M -exec ls -lh {} \;
   ```

2. **Clean Up Storage:**
   ```bash
   # Run storage cleanup
   python -m backend.multi_instance_arxiv_system.scripts.storage_manager cleanup \
     --max-age-days 30
   
   # Clean up logs
   find logs/ -name "*.log" -mtime +30 -delete
   
   # Clean up cache
   rm -rf data/*/cache/*
   ```

3. **Compress Old Files:**
   ```bash
   # Compress old log files
   find logs/ -name "*.log" -mtime +7 -exec gzip {} \;
   
   # Run storage optimization
   python -m backend.multi_instance_arxiv_system.scripts.storage_manager optimize
   ```

4. **Monitor Disk Usage:**
   ```bash
   # Set up disk monitoring
   python -m backend.multi_instance_arxiv_system.scripts.storage_manager analyze \
     --output storage_report.json
   ```

### 2. File Permission Issues

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied
OSError: [Errno 1] Operation not permitted
```

**Solutions:**

1. **Fix Permissions Recursively:**
   ```bash
   # Fix data directory permissions
   find data/ -type d -exec chmod 755 {} \;
   find data/ -type f -exec chmod 644 {} \;
   
   # Fix ownership
   chown -R $USER:$USER data/ logs/ reports/
   ```

2. **Check SELinux (if applicable):**
   ```bash
   # Check SELinux status
   sestatus
   
   # If SELinux is enforcing, set appropriate contexts
   sudo setsebool -P httpd_can_network_connect 1
   ```

## Monitoring and Logging Issues

### 1. Missing or Incomplete Logs

**Symptoms:**
- No log files generated
- Logs missing important information
- Log rotation not working

**Solutions:**

1. **Check Log Configuration:**
   ```bash
   # Verify log directory exists
   mkdir -p logs
   chmod 755 logs/
   
   # Check log file permissions
   touch logs/system.log
   chmod 644 logs/system.log
   ```

2. **Test Logging:**
   ```bash
   # Test logging functionality
   python -c "
   import logging
   
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('logs/test.log'),
           logging.StreamHandler()
       ]
   )
   
   logger = logging.getLogger('test')
   logger.info('Test log message')
   print('Check logs/test.log for output')
   "
   ```

3. **Configure Log Rotation:**
   ```bash
   # Set up logrotate
   sudo tee /etc/logrotate.d/arxiv-system << EOF
   /path/to/logs/*.log {
       daily
       rotate 30
       compress
       delaycompress
       missingok
       notifempty
       create 644 $USER $USER
   }
   EOF
   
   # Test logrotate
   sudo logrotate -d /etc/logrotate.d/arxiv-system
   ```

### 2. Monitoring Script Issues

**Symptoms:**
- Health checks failing
- Monitoring scripts not running
- Incorrect system status reports

**Solutions:**

1. **Test Health Check:**
   ```bash
   # Run health check manually
   python -m backend.multi_instance_arxiv_system.scripts.system_health_check \
     --verbose --output health_report.json
   
   # Check specific instance
   python -m backend.multi_instance_arxiv_system.scripts.system_health_check \
     --instance ai_scholar
   ```

2. **Debug Monitor Script:**
   ```bash
   # Run monitor with debug output
   python -m backend.multi_instance_arxiv_system.scripts.multi_instance_monitor \
     --verbose
   
   # Check monitor dependencies
   python -c "
   from backend.multi_instance_arxiv_system.monitoring.storage_monitor import StorageMonitor
   from backend.multi_instance_arxiv_system.monitoring.performance_monitor import PerformanceMonitor
   print('Monitoring modules imported successfully')
   "
   ```

## Cron and Scheduling Issues

### 1. Cron Jobs Not Running

**Symptoms:**
- Scheduled updates not executing
- No cron job output
- Jobs running at wrong times

**Solutions:**

1. **Check Cron Status:**
   ```bash
   # Check if cron service is running
   sudo systemctl status cron
   
   # Start cron if not running
   sudo systemctl start cron
   sudo systemctl enable cron
   ```

2. **Verify Cron Jobs:**
   ```bash
   # List current cron jobs
   crontab -l
   
   # Check cron logs
   sudo tail -f /var/log/cron
   # or
   sudo journalctl -u cron -f
   ```

3. **Test Cron Job Manually:**
   ```bash
   # Run the exact command from crontab
   /path/to/venv/bin/python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_monthly_update
   ```

4. **Fix Common Cron Issues:**
   ```bash
   # Ensure full paths in crontab
   # Wrong:
   # 0 2 1 * * python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_monthly_update
   
   # Correct:
   # 0 2 1 * * /home/user/arxiv-system/venv/bin/python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_monthly_update
   
   # Set environment variables in crontab
   crontab -e
   # Add at top:
   PATH=/usr/local/bin:/usr/bin:/bin
   PYTHONPATH=/home/user/arxiv-system
   ```

### 2. Scheduling Conflicts

**Symptoms:**
- Multiple instances running simultaneously
- Resource conflicts during updates
- Lock file errors

**Solutions:**

1. **Check for Lock Files:**
   ```bash
   # Check for existing lock files
   find /tmp -name "*.lock" -ls
   
   # Remove stale lock files
   find /tmp -name "arxiv_*.lock" -mtime +1 -delete
   ```

2. **Stagger Schedules:**
   ```bash
   # Ensure different instances run at different times
   # AI Scholar: 1st of month at 2 AM
   # Quant Scholar: 15th of month at 3 AM
   
   crontab -e
   # Add:
   0 2 1 * * /path/to/venv/bin/python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_monthly_update
   0 3 15 * * /path/to/venv/bin/python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_monthly_update
   ```

3. **Implement Better Locking:**
   ```bash
   # Use flock for better process locking
   # In crontab:
   0 2 1 * * /usr/bin/flock -n /tmp/ai_scholar.lock /path/to/venv/bin/python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_monthly_update
   ```

## Getting Help

### 1. Collecting Debug Information

When reporting issues, collect this information:

```bash
# System information
uname -a
python --version
docker --version

# System status
python -m backend.multi_instance_arxiv_system.scripts.system_health_check \
  --output debug_health.json

# Storage status
python -m backend.multi_instance_arxiv_system.scripts.storage_manager analyze \
  --output debug_storage.json

# Recent logs
tail -100 logs/system.log > debug_logs.txt

# Configuration (remove sensitive data)
cp config/ai_scholar.yaml debug_config.yaml
# Edit debug_config.yaml to remove sensitive information
```

### 2. Log Analysis

```bash
# Search for errors
grep -i error logs/system.log | tail -20

# Search for warnings
grep -i warning logs/system.log | tail -20

# Search for specific component issues
grep -i "chromadb\|vector\|embedding" logs/system.log | tail -10
grep -i "download\|arxiv\|pdf" logs/system.log | tail -10
grep -i "email\|smtp\|notification" logs/system.log | tail -10
```

### 3. Performance Analysis

```bash
# Check system resources during operation
top -p $(pgrep -f "multi_instance_arxiv")

# Monitor disk I/O
iotop -p $(pgrep -f "multi_instance_arxiv")

# Monitor network usage
nethogs
```

### 4. Contact Information

For additional support:

1. **Check Documentation**: Review all documentation files
2. **Search Issues**: Check existing GitHub issues
3. **Create Issue**: Create detailed issue with debug information
4. **Community Support**: Join community discussions

### 5. Emergency Recovery

If the system is completely broken:

```bash
# Stop all processes
pkill -f "multi_instance_arxiv"

# Stop ChromaDB
docker stop chromadb

# Backup current state
tar -czf backup_$(date +%Y%m%d).tar.gz data/ config/ logs/

# Reset to clean state
rm -rf data/*/cache/*
rm -rf logs/*.log
docker rm chromadb
docker run -d --name chromadb -p 8000:8000 chromadb/chroma:latest

# Restart system
python -m backend.multi_instance_arxiv_system.scripts.system_health_check
```

Remember to always backup your data before making significant changes to the system configuration or attempting major troubleshooting steps.