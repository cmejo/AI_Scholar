# Multi-Instance ArXiv System - Deployment Checklist

## Overview

This checklist ensures a complete and successful deployment of the Multi-Instance ArXiv System to a production environment. Follow each step in order and verify completion before proceeding.

## Pre-Deployment Requirements

### Infrastructure Requirements

- [ ] **Server Specifications Met**
  - [ ] CPU: Minimum 8 cores, recommended 16+ cores
  - [ ] RAM: Minimum 32GB, recommended 64GB+
  - [ ] Storage: Minimum 500GB SSD, recommended 1TB+ NVMe
  - [ ] Network: Stable internet with good bandwidth (100Mbps+)

- [ ] **Operating System Prepared**
  - [ ] Ubuntu 20.04 LTS or newer installed
  - [ ] System fully updated (`sudo apt update && sudo apt upgrade -y`)
  - [ ] Required system packages installed
  - [ ] User account with sudo privileges created

- [ ] **Network Configuration**
  - [ ] Firewall configured (ports 22, 80, 443, 8000 as needed)
  - [ ] DNS resolution working
  - [ ] NTP synchronization enabled
  - [ ] SSL certificates obtained (if using HTTPS)

### Software Dependencies

- [ ] **Python Environment**
  - [ ] Python 3.9+ installed
  - [ ] pip and venv available
  - [ ] Virtual environment created and activated

- [ ] **Docker Installation**
  - [ ] Docker 20.10+ installed
  - [ ] Docker service running and enabled
  - [ ] User added to docker group
  - [ ] Docker Compose installed (if needed)

- [ ] **System Tools**
  - [ ] Git installed
  - [ ] curl and wget available
  - [ ] PDF processing tools installed (poppler-utils, ghostscript)
  - [ ] Text processing tools installed (tesseract-ocr)

### Security Preparation

- [ ] **Access Control**
  - [ ] SSH key-based authentication configured
  - [ ] Password authentication disabled
  - [ ] Fail2ban or similar intrusion prevention installed
  - [ ] Regular security updates scheduled

- [ ] **Secrets Management**
  - [ ] API keys obtained and securely stored
  - [ ] Email credentials configured
  - [ ] Environment variables prepared
  - [ ] Configuration files secured (600 permissions)

## Deployment Steps

### Phase 1: Base System Setup

- [ ] **1.1 System Preparation**
  ```bash
  # Update system
  sudo apt update && sudo apt upgrade -y
  
  # Install essential packages
  sudo apt install -y python3-pip python3-venv git curl wget \
    poppler-utils ghostscript tesseract-ocr build-essential
  
  # Create application user (optional but recommended)
  sudo useradd -m -s /bin/bash arxiv-system
  sudo usermod -aG docker arxiv-system
  ```

- [ ] **1.2 Directory Structure**
  ```bash
  # Create base directories
  sudo mkdir -p /opt/arxiv-system
  sudo chown arxiv-system:arxiv-system /opt/arxiv-system
  
  # Switch to application user
  sudo su - arxiv-system
  cd /opt/arxiv-system
  
  # Create directory structure
  mkdir -p {data,logs,config,backups,reports}
  mkdir -p data/{ai_scholar,quant_scholar}/{papers,logs,cache,reports}
  ```

- [ ] **1.3 Application Code**
  ```bash
  # Clone repository
  git clone https://github.com/your-org/multi-instance-arxiv-system.git .
  
  # Create virtual environment
  python3 -m venv venv
  source venv/bin/activate
  
  # Install dependencies
  pip install --upgrade pip
  pip install -r requirements.txt
  ```

### Phase 2: Database Setup

- [ ] **2.1 ChromaDB Installation**
  ```bash
  # Pull ChromaDB image
  docker pull chromadb/chroma:latest
  
  # Create persistent volume
  docker volume create chromadb_data
  
  # Start ChromaDB
  docker run -d --name chromadb \
    -p 8000:8000 \
    -v chromadb_data:/chroma/chroma \
    --restart unless-stopped \
    chromadb/chroma:latest
  ```

- [ ] **2.2 Database Verification**
  ```bash
  # Wait for startup
  sleep 10
  
  # Test connection
  curl http://localhost:8000/api/v1/heartbeat
  
  # Should return: {"nanosecond heartbeat": <timestamp>}
  ```

- [ ] **2.3 Initialize Collections**
  ```bash
  # Initialize vector store collections
  python -m backend.multi_instance_arxiv_system.scripts.initialize_collections
  
  # Verify collections created
  python -c "
  import chromadb
  client = chromadb.HttpClient(host='localhost', port=8000)
  collections = client.list_collections()
  print([c.name for c in collections])
  "
  ```

### Phase 3: Configuration

- [ ] **3.1 Environment Variables**
  ```bash
  # Create .env file
  cat > .env << EOF
  # Database Configuration
  CHROMA_HOST=localhost
  CHROMA_PORT=8000
  
  # Email Configuration
  SMTP_HOST=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USERNAME=your-email@gmail.com
  SMTP_PASSWORD=your-app-password
  
  # Storage Configuration
  BASE_STORAGE_PATH=/opt/arxiv-system/data
  
  # Logging
  LOG_LEVEL=INFO
  LOG_FILE=/opt/arxiv-system/logs/system.log
  
  # Performance
  MAX_CONCURRENT_DOWNLOADS=4
  MAX_CONCURRENT_PROCESSING=2
  MEMORY_LIMIT_GB=16
  EOF
  
  # Secure environment file
  chmod 600 .env
  ```

- [ ] **3.2 Instance Configurations**
  ```bash
  # Create AI Scholar config
  cat > config/ai_scholar.yaml << EOF
  instance_name: "ai_scholar"
  description: "AI and Machine Learning Papers"
  
  storage_path: "/opt/arxiv-system/data/ai_scholar"
  papers_path: "/opt/arxiv-system/data/ai_scholar/papers"
  logs_path: "/opt/arxiv-system/data/ai_scholar/logs"
  cache_path: "/opt/arxiv-system/data/ai_scholar/cache"
  
  arxiv_categories:
    - "cs.AI"
    - "cs.LG"
    - "cs.CV"
    - "cs.CL"
    - "cs.NE"
    - "cs.RO"
    - "stat.ML"
  
  processing:
    batch_size: 100
    max_concurrent: 2
    memory_limit_gb: 8
  
  email_notifications:
    enabled: true
    recipients:
      - "admin@yourorg.com"
    frequency: "monthly"
  EOF
  
  # Create Quant Scholar config
  cat > config/quant_scholar.yaml << EOF
  instance_name: "quant_scholar"
  description: "Quantitative Finance and Statistics Papers"
  
  storage_path: "/opt/arxiv-system/data/quant_scholar"
  papers_path: "/opt/arxiv-system/data/quant_scholar/papers"
  logs_path: "/opt/arxiv-system/data/quant_scholar/logs"
  cache_path: "/opt/arxiv-system/data/quant_scholar/cache"
  
  arxiv_categories:
    - "q-fin.*"
    - "stat.*"
    - "math.ST"
    - "econ.*"
  
  journal_sources:
    - name: "Journal of Statistical Software"
      url: "https://www.jstatsoft.org"
      enabled: true
    - name: "R Journal"
      url: "https://journal.r-project.org"
      enabled: true
  
  processing:
    batch_size: 50
    max_concurrent: 2
    memory_limit_gb: 8
  
  email_notifications:
    enabled: true
    recipients:
      - "admin@yourorg.com"
    frequency: "monthly"
  EOF
  ```

### Phase 4: Service Setup

- [ ] **4.1 Systemd Service Files**
  ```bash
  # Create systemd service for ChromaDB
  sudo cat > /etc/systemd/system/chromadb.service << EOF
  [Unit]
  Description=ChromaDB Vector Database
  After=docker.service
  Requires=docker.service
  
  [Service]
  Type=oneshot
  RemainAfterExit=yes
  ExecStart=/usr/bin/docker start chromadb
  ExecStop=/usr/bin/docker stop chromadb
  TimeoutStartSec=0
  
  [Install]
  WantedBy=multi-user.target
  EOF
  
  # Enable ChromaDB service
  sudo systemctl enable chromadb.service
  sudo systemctl start chromadb.service
  ```

- [ ] **4.2 Cron Jobs Setup**
  ```bash
  # Create monthly update script
  cat > /opt/arxiv-system/scripts/monthly_update.sh << 'EOF'
  #!/bin/bash
  cd /opt/arxiv-system
  source venv/bin/activate
  
  # Run monthly updates for both instances
  python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_monthly_update
  python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_monthly_update
  
  # Generate and send reports
  python -m backend.multi_instance_arxiv_system.scripts.generate_monthly_report
  EOF
  
  chmod +x /opt/arxiv-system/scripts/monthly_update.sh
  
  # Add to crontab (runs on 1st of each month at 2 AM)
  (crontab -l 2>/dev/null; echo "0 2 1 * * /opt/arxiv-system/scripts/monthly_update.sh") | crontab -
  ```

- [ ] **4.3 Log Rotation**
  ```bash
  # Create logrotate configuration
  sudo cat > /etc/logrotate.d/arxiv-system << EOF
  /opt/arxiv-system/logs/*.log {
      daily
      missingok
      rotate 30
      compress
      delaycompress
      notifempty
      create 644 arxiv-system arxiv-system
      postrotate
          systemctl reload rsyslog > /dev/null 2>&1 || true
      endscript
  }
  EOF
  ```

### Phase 5: Testing and Validation

- [ ] **5.1 System Health Check**
  ```bash
  # Run comprehensive health check
  python -m backend.multi_instance_arxiv_system.scripts.system_health_check
  
  # Expected output: All systems operational
  ```

- [ ] **5.2 Test Downloads**
  ```bash
  # Test AI Scholar download (small batch)
  python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_downloader \
    --test-mode --limit 5
  
  # Test Quant Scholar download (small batch)
  python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader \
    --test-mode --limit 5
  ```

- [ ] **5.3 Test Processing**
  ```bash
  # Test AI Scholar processing
  python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_processor \
    --test-mode
  
  # Test Quant Scholar processing
  python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_processor \
    --test-mode
  ```

- [ ] **5.4 Test Email Notifications**
  ```bash
  # Send test email
  python -c "
  from backend.multi_instance_arxiv_system.services.email_notification_service import EmailNotificationService
  service = EmailNotificationService()
  service.send_test_email('Test deployment notification')
  "
  ```

### Phase 6: Monitoring Setup

- [ ] **6.1 System Monitoring**
  ```bash
  # Install monitoring tools
  sudo apt install -y htop iotop nethogs
  
  # Create monitoring script
  cat > /opt/arxiv-system/scripts/monitor.sh << 'EOF'
  #!/bin/bash
  
  # Check system resources
  echo "=== System Resources ==="
  free -h
  df -h /opt/arxiv-system
  
  # Check ChromaDB
  echo "=== ChromaDB Status ==="
  curl -s http://localhost:8000/api/v1/heartbeat || echo "ChromaDB not responding"
  
  # Check recent logs
  echo "=== Recent Errors ==="
  tail -n 20 /opt/arxiv-system/logs/system.log | grep -i error || echo "No recent errors"
  EOF
  
  chmod +x /opt/arxiv-system/scripts/monitor.sh
  ```

- [ ] **6.2 Alerting Setup**
  ```bash
  # Create alert script for critical issues
  cat > /opt/arxiv-system/scripts/alert.sh << 'EOF'
  #!/bin/bash
  
  # Check disk space (alert if > 90% full)
  DISK_USAGE=$(df /opt/arxiv-system | tail -1 | awk '{print $5}' | sed 's/%//')
  if [ $DISK_USAGE -gt 90 ]; then
      echo "ALERT: Disk usage is ${DISK_USAGE}%" | \
      mail -s "ArXiv System Disk Alert" admin@yourorg.com
  fi
  
  # Check ChromaDB health
  if ! curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; then
      echo "ALERT: ChromaDB is not responding" | \
      mail -s "ArXiv System Database Alert" admin@yourorg.com
  fi
  EOF
  
  chmod +x /opt/arxiv-system/scripts/alert.sh
  
  # Add to crontab (check every hour)
  (crontab -l 2>/dev/null; echo "0 * * * * /opt/arxiv-system/scripts/alert.sh") | crontab -
  ```

## Post-Deployment Verification

### Performance Validation

- [ ] **Resource Usage Check**
  - [ ] CPU usage under normal load < 70%
  - [ ] Memory usage < 80% of available RAM
  - [ ] Disk I/O performance adequate for workload
  - [ ] Network connectivity stable

- [ ] **Processing Performance**
  - [ ] Download speeds meet expectations (>10 papers/minute)
  - [ ] Processing speeds adequate (>5 papers/minute)
  - [ ] Vector store operations responsive (<2s per query)
  - [ ] Email notifications delivered within 5 minutes

### Security Validation

- [ ] **Access Control**
  - [ ] SSH access restricted to authorized keys only
  - [ ] Application files have correct permissions
  - [ ] Sensitive configuration files secured (600 permissions)
  - [ ] No unnecessary services running

- [ ] **Data Protection**
  - [ ] Database access restricted to localhost
  - [ ] Log files contain no sensitive information
  - [ ] Backup procedures tested and working
  - [ ] SSL/TLS configured if external access needed

### Operational Validation

- [ ] **Automated Processes**
  - [ ] Cron jobs scheduled and working
  - [ ] Log rotation functioning
  - [ ] Monitoring scripts operational
  - [ ] Alert system tested and working

- [ ] **Documentation**
  - [ ] All configuration files documented
  - [ ] Operational procedures documented
  - [ ] Emergency contacts and procedures defined
  - [ ] Backup and recovery procedures tested

## Troubleshooting Common Issues

### ChromaDB Connection Issues

```bash
# Check if ChromaDB is running
docker ps | grep chromadb

# Check ChromaDB logs
docker logs chromadb

# Restart ChromaDB if needed
docker restart chromadb

# Test connection
curl http://localhost:8000/api/v1/heartbeat
```

### Storage Issues

```bash
# Check disk space
df -h /opt/arxiv-system

# Check large files
find /opt/arxiv-system -type f -size +100M -exec ls -lh {} \;

# Clean up old logs
find /opt/arxiv-system/logs -name "*.log" -mtime +30 -delete

# Clean up cache files
find /opt/arxiv-system/data/*/cache -name "*.tmp" -mtime +7 -delete
```

### Email Notification Issues

```bash
# Test SMTP connection
python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-app-password')
server.quit()
print('SMTP connection successful')
"

# Check email logs
grep -i "email\|smtp" /opt/arxiv-system/logs/system.log
```

### Performance Issues

```bash
# Check system resources
htop
iotop -o
nethogs

# Check ChromaDB performance
curl -s http://localhost:8000/api/v1/collections | jq '.[].count'

# Monitor processing performance
tail -f /opt/arxiv-system/logs/system.log | grep -i "processing\|download"
```

## Maintenance Procedures

### Daily Checks

- [ ] Check system resources (CPU, memory, disk)
- [ ] Verify ChromaDB is running and responsive
- [ ] Check for any error messages in logs
- [ ] Verify automated processes are running

### Weekly Checks

- [ ] Review processing statistics and performance
- [ ] Check storage usage and cleanup if needed
- [ ] Verify backup procedures are working
- [ ] Review and rotate logs if necessary

### Monthly Checks

- [ ] Review monthly update reports
- [ ] Analyze system performance trends
- [ ] Update system packages and dependencies
- [ ] Review and update configuration as needed
- [ ] Test disaster recovery procedures

## Emergency Procedures

### System Recovery

1. **Database Corruption**
   ```bash
   # Stop ChromaDB
   docker stop chromadb
   
   # Restore from backup
   docker run --rm -v chromadb_data:/data -v /path/to/backup:/backup \
     ubuntu tar xzf /backup/chromadb_backup.tar.gz -C /data
   
   # Restart ChromaDB
   docker start chromadb
   ```

2. **Disk Space Emergency**
   ```bash
   # Emergency cleanup
   find /opt/arxiv-system/data/*/cache -type f -delete
   find /opt/arxiv-system/logs -name "*.log" -mtime +7 -delete
   
   # Compress old papers
   find /opt/arxiv-system/data/*/papers -name "*.pdf" -mtime +90 \
     -exec gzip {} \;
   ```

3. **Service Recovery**
   ```bash
   # Restart all services
   sudo systemctl restart chromadb
   
   # Check service status
   sudo systemctl status chromadb
   
   # Restart cron if needed
   sudo systemctl restart cron
   ```

## Contact Information

- **System Administrator**: admin@yourorg.com
- **Technical Support**: support@yourorg.com
- **Emergency Contact**: +1-555-0123

## Deployment Sign-off

- [ ] **Technical Lead Approval**: _________________ Date: _______
- [ ] **Security Review**: _________________ Date: _______
- [ ] **Operations Approval**: _________________ Date: _______
- [ ] **Final Deployment**: _________________ Date: _______

---

**Note**: This checklist should be customized for your specific environment and requirements. Always test procedures in a staging environment before applying to production.
   