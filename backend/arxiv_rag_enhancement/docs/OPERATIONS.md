# arXiv RAG Enhancement System - Operations Runbook

This document provides operational procedures for running and maintaining the arXiv RAG Enhancement System in production.

## 🚀 Deployment Procedures

### Initial Deployment

1. **Pre-deployment Checklist**
   ```bash
   # Verify system requirements
   python --version  # Should be 3.8+
   df -h /datapool/aischolar/  # Check disk space (50GB+ recommended)
   free -h  # Check memory (4GB+ recommended)
   
   # Verify ChromaDB is running
   curl http://localhost:8082/api/v1/heartbeat
   ```

2. **Run Setup Script**
   ```bash
   cd backend
   python setup_arxiv_rag_enhancement.py
   ```

3. **Verify Installation**
   ```bash
   # Test all three scripts
   python process_local_arxiv_dataset.py --help
   python download_bulk_arxiv_papers.py --help
   python run_monthly_update.py --help
   ```

4. **Configure System**
   ```bash
   # Edit configuration file
   nano /datapool/aischolar/arxiv-dataset-2024/config/arxiv_rag_config.yaml
   
   # Set up environment variables
   cp /datapool/aischolar/arxiv-dataset-2024/config/.env.template .env
   nano .env
   ```

### Production Deployment

1. **Create Service User**
   ```bash
   sudo useradd -r -s /bin/bash arxiv-rag
   sudo mkdir -p /home/arxiv-rag
   sudo chown arxiv-rag:arxiv-rag /home/arxiv-rag
   ```

2. **Set Permissions**
   ```bash
   sudo chown -R arxiv-rag:arxiv-rag /datapool/aischolar/arxiv-dataset-2024/
   sudo chmod -R 755 /datapool/aischolar/arxiv-dataset-2024/
   ```

3. **Install as Service** (Optional)
   ```bash
   # Create systemd service for monthly updater
   sudo tee /etc/systemd/system/arxiv-monthly-updater.service > /dev/null <<EOF
   [Unit]
   Description=arXiv Monthly Updater
   After=network.target
   
   [Service]
   Type=oneshot
   User=arxiv-rag
   WorkingDirectory=/path/to/backend
   ExecStart=/usr/bin/python run_monthly_update.py
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   sudo systemctl daemon-reload
   sudo systemctl enable arxiv-monthly-updater.service
   ```

## 📊 Monitoring Procedures

### Daily Monitoring

1. **Check System Health**
   ```bash
   # Run status check
   /datapool/aischolar/arxiv-dataset-2024/scripts/check_status.sh
   
   # Check disk usage
   df -h /datapool/aischolar/
   
   # Check recent logs
   tail -f /datapool/aischolar/arxiv-dataset-2024/processed/error_logs/*.log
   ```

2. **Verify ChromaDB Connection**
   ```bash
   python -c "
   import chromadb
   client = chromadb.HttpClient(host='localhost', port=8082)
   client.heartbeat()
   print('ChromaDB OK')
   "
   ```

3. **Check Processing Status**
   ```bash
   # Check for active processing
   ps aux | grep -E "(process_local|download_bulk|run_monthly)"
   
   # Check state files
   ls -la /datapool/aischolar/arxiv-dataset-2024/processed/state_files/
   ```

### Weekly Monitoring

1. **Review Error Logs**
   ```bash
   # Check error rates
   grep -c "ERROR" /datapool/aischolar/arxiv-dataset-2024/processed/error_logs/*.log
   
   # Review recent errors
   grep "ERROR" /datapool/aischolar/arxiv-dataset-2024/processed/error_logs/*.log | tail -20
   ```

2. **Storage Analysis**
   ```bash
   # Analyze storage usage
   du -sh /datapool/aischolar/arxiv-dataset-2024/*
   
   # Count processed papers
   find /datapool/aischolar/arxiv-dataset-2024/pdfs -name "*.pdf" | wc -l
   ```

3. **Performance Review**
   ```bash
   # Check processing rates from logs
   grep "processing rate" /datapool/aischolar/arxiv-dataset-2024/processed/error_logs/*.log
   
   # Review monthly reports
   ls -la /datapool/aischolar/arxiv-dataset-2024/processed/reports/
   ```

### Monthly Monitoring

1. **Review Monthly Update Reports**
   ```bash
   # Check latest monthly report
   cat /datapool/aischolar/arxiv-dataset-2024/processed/reports/monthly_update_*.json | jq .
   ```

2. **Cleanup Old Data**
   ```bash
   # Run cleanup
   python run_monthly_update.py --cleanup-only
   ```

3. **System Maintenance**
   ```bash
   # Update dependencies
   pip install -r arxiv_rag_enhancement/requirements.txt --upgrade
   
   # Rotate logs
   logrotate /etc/logrotate.d/arxiv-rag
   ```

## 🔧 Maintenance Procedures

### Routine Maintenance

1. **Log Rotation**
   ```bash
   # Create logrotate configuration
   sudo tee /etc/logrotate.d/arxiv-rag > /dev/null <<EOF
   /datapool/aischolar/arxiv-dataset-2024/processed/error_logs/*.log {
       daily
       rotate 30
       compress
       delaycompress
       missingok
       notifempty
       create 644 arxiv-rag arxiv-rag
   }
   EOF
   ```

2. **Database Maintenance**
   ```bash
   # ChromaDB maintenance (if needed)
   # This depends on your ChromaDB setup
   ```

3. **Disk Space Management**
   ```bash
   # Clean up old PDFs (if configured)
   python run_monthly_update.py --cleanup-only
   
   # Manual cleanup of old state files
   find /datapool/aischolar/arxiv-dataset-2024/processed/state_files -name "*.json" -mtime +7 -delete
   ```

### Configuration Updates

1. **Update Configuration**
   ```bash
   # Backup current config
   cp /datapool/aischolar/arxiv-dataset-2024/config/arxiv_rag_config.yaml \
      /datapool/aischolar/arxiv-dataset-2024/config/arxiv_rag_config.yaml.backup
   
   # Edit configuration
   nano /datapool/aischolar/arxiv-dataset-2024/config/arxiv_rag_config.yaml
   
   # Validate configuration
   python -c "
   from arxiv_rag_enhancement.config import ConfigManager
   config = ConfigManager('/datapool/aischolar/arxiv-dataset-2024/config/arxiv_rag_config.yaml')
   errors = config.validate_config()
   if errors:
       print('Configuration errors:', errors)
   else:
       print('Configuration valid')
   "
   ```

2. **Update Categories**
   ```bash
   # Add new arXiv categories to config
   # Edit the categories list in the configuration file
   ```

3. **Update Email Settings**
   ```bash
   # Test email configuration
   python -c "
   import smtplib
   from email.mime.text import MIMEText
   
   # Test SMTP connection
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.starttls()
   # server.login('username', 'password')  # Uncomment to test auth
   print('SMTP connection OK')
   server.quit()
   "
   ```

## 🚨 Incident Response

### Processing Failures

1. **Identify the Issue**
   ```bash
   # Check recent error logs
   tail -100 /datapool/aischolar/arxiv-dataset-2024/processed/error_logs/*.log
   
   # Check system resources
   top
   df -h
   free -h
   ```

2. **Common Issues and Solutions**

   **ChromaDB Connection Failed:**
   ```bash
   # Check ChromaDB status
   curl http://localhost:8082/api/v1/heartbeat
   
   # Restart ChromaDB if needed
   sudo systemctl restart chromadb  # If running as service
   # OR
   chroma run --host localhost --port 8082 &
   ```

   **Out of Disk Space:**
   ```bash
   # Free up space
   python run_monthly_update.py --cleanup-only
   
   # Remove old PDFs if necessary
   find /datapool/aischolar/arxiv-dataset-2024/pdfs -name "*.pdf" -mtime +90 -delete
   ```

   **Memory Issues:**
   ```bash
   # Reduce batch size
   export ARXIV_RAG_BATCH_SIZE=5
   
   # Kill memory-intensive processes
   pkill -f "process_local_arxiv"
   ```

3. **Resume Processing**
   ```bash
   # Resume interrupted processing
   python process_local_arxiv_dataset.py --resume
   python download_bulk_arxiv_papers.py  # Will skip duplicates
   ```

### Data Corruption

1. **Identify Corrupted Data**
   ```bash
   # Check for corrupted PDFs
   find /datapool/aischolar/arxiv-dataset-2024/pdfs -name "*.pdf" -size 0
   
   # Check state file integrity
   python -c "
   import json
   from pathlib import Path
   
   state_dir = Path('/datapool/aischolar/arxiv-dataset-2024/processed/state_files')
   for state_file in state_dir.glob('*.json'):
       try:
           with open(state_file) as f:
               json.load(f)
           print(f'{state_file}: OK')
       except Exception as e:
           print(f'{state_file}: CORRUPTED - {e}')
   "
   ```

2. **Recovery Procedures**
   ```bash
   # Remove corrupted files
   find /datapool/aischolar/arxiv-dataset-2024/pdfs -name "*.pdf" -size 0 -delete
   
   # Reset state files if corrupted
   rm /datapool/aischolar/arxiv-dataset-2024/processed/state_files/*.json
   
   # Restart processing
   python process_local_arxiv_dataset.py
   ```

### Service Outages

1. **arXiv API Outage**
   ```bash
   # Check arXiv API status
   curl -I "http://export.arxiv.org/api/query?search_query=cat:cond-mat&max_results=1"
   
   # Wait and retry later
   # The system will automatically retry with exponential backoff
   ```

2. **Network Issues**
   ```bash
   # Check network connectivity
   ping arxiv.org
   ping storage.googleapis.com
   
   # Check DNS resolution
   nslookup arxiv.org
   ```

## 📈 Performance Tuning

### Optimization Guidelines

1. **Batch Size Tuning**
   ```bash
   # Start with default batch size
   ARXIV_RAG_BATCH_SIZE=10
   
   # Increase for powerful systems
   ARXIV_RAG_BATCH_SIZE=20
   
   # Decrease for resource-constrained systems
   ARXIV_RAG_BATCH_SIZE=5
   ```

2. **Concurrent Processing**
   ```bash
   # Adjust concurrent downloads
   # Edit configuration file:
   bulk_downloader:
     max_concurrent_downloads: 10  # Increase for faster downloads
   ```

3. **Memory Optimization**
   ```bash
   # Monitor memory usage
   watch -n 5 'free -h && ps aux --sort=-%mem | head -10'
   
   # Adjust memory limits in configuration
   performance:
     memory_limit_mb: 8192
   ```

### Scaling Considerations

1. **Horizontal Scaling**
   - Run multiple instances with different categories
   - Use different output directories
   - Coordinate via external scheduling

2. **Vertical Scaling**
   - Increase batch sizes
   - Add more concurrent workers
   - Allocate more memory

## 🔐 Security Procedures

### Access Control

1. **File Permissions**
   ```bash
   # Set secure permissions
   chmod 750 /datapool/aischolar/arxiv-dataset-2024/
   chmod 640 /datapool/aischolar/arxiv-dataset-2024/config/*.yaml
   chmod 600 /datapool/aischolar/arxiv-dataset-2024/config/.env
   ```

2. **Service Account**
   ```bash
   # Run as dedicated user
   sudo -u arxiv-rag python process_local_arxiv_dataset.py
   ```

### Audit Procedures

1. **Access Logging**
   ```bash
   # Monitor file access
   sudo auditctl -w /datapool/aischolar/arxiv-dataset-2024/ -p rwxa -k arxiv-rag
   
   # Review audit logs
   sudo ausearch -k arxiv-rag
   ```

2. **Configuration Auditing**
   ```bash
   # Track configuration changes
   git init /datapool/aischolar/arxiv-dataset-2024/config/
   cd /datapool/aischolar/arxiv-dataset-2024/config/
   git add .
   git commit -m "Initial configuration"
   ```

## 📞 Emergency Contacts

### Escalation Procedures

1. **Level 1**: System Administrator
   - Check logs and system resources
   - Attempt basic troubleshooting
   - Restart services if needed

2. **Level 2**: Technical Lead
   - Complex configuration issues
   - Performance optimization
   - Integration problems

3. **Level 3**: Development Team
   - Code-level issues
   - System architecture changes
   - Major incidents

### Emergency Shutdown

```bash
# Emergency stop all processing
pkill -f "process_local_arxiv"
pkill -f "download_bulk_arxiv"
pkill -f "run_monthly_update"

# Stop ChromaDB if needed
sudo systemctl stop chromadb

# Preserve state files for recovery
cp -r /datapool/aischolar/arxiv-dataset-2024/processed/state_files/ \
      /datapool/aischolar/arxiv-dataset-2024/processed/state_files.backup/
```

---

**Remember**: Always test procedures in a development environment before applying to production!