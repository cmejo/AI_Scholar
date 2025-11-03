# Multi-Instance ArXiv System - Operational Runbooks

## Overview

This document provides step-by-step operational procedures for maintaining and operating the Multi-Instance ArXiv System. These runbooks are designed for system administrators and operators.

## Daily Operations

### Daily Health Check

**Frequency**: Every day at 6 AM (automated) or on-demand  
**Duration**: 5-10 minutes  
**Prerequisites**: System access, monitoring tools available

#### Procedure

1. **Run Automated Health Check**
   ```bash
   python -m backend.multi_instance_arxiv_system.scripts.system_health_check \
     --verbose --output daily_health_$(date +%Y%m%d).json
   ```

2. **Review Health Report**
   ```bash
   # Check overall system status
   cat daily_health_$(date +%Y%m%d).json | jq '.overall_status'
   
   # Check instance statuses
   cat daily_health_$(date +%Y%m%d).json | jq '.instances'
   
   # Check for alerts
   cat daily_health_$(date +%Y%m%d).json | jq '.alerts'
   ```

3. **Verify Critical Services**
   ```bash
   # Check ChromaDB
   curl -s http://localhost:8000/api/v1/heartbeat || echo "ChromaDB DOWN"
   
   # Check disk space
   df -h | grep -E "(9[0-9]%|100%)" && echo "DISK SPACE WARNING"
   
   # Check system resources
   free -h | grep Mem
   uptime
   ```

4. **Review Recent Logs**
   ```bash
   # Check for errors in last 24 hours
   grep -i error logs/system.log | grep "$(date +%Y-%m-%d)"
   
   # Check for warnings
   grep -i warning logs/system.log | grep "$(date +%Y-%m-%d)"
   ```

#### Expected Results
- Overall status: "healthy" or "degraded"
- All instances showing "healthy" status
- No critical alerts
- Disk usage < 80%
- No critical errors in logs

#### Escalation
- If overall status is "unhealthy": Follow [System Recovery Procedure](#system-recovery-procedure)
- If disk usage > 90%: Follow [Storage Cleanup Procedure](#storage-cleanup-procedure)
- If critical errors found: Follow [Error Investigation Procedure](#error-investigation-procedure)

### Daily Log Review

**Frequency**: Daily  
**Duration**: 10-15 minutes

#### Procedure

1. **Check Log File Sizes**
   ```bash
   # Check log file sizes
   ls -lh logs/
   
   # Alert if any log file > 100MB
   find logs/ -name "*.log" -size +100M -exec ls -lh {} \;
   ```

2. **Review Error Patterns**
   ```bash
   # Count errors by type
   grep -i error logs/system.log | grep "$(date +%Y-%m-%d)" | \
     awk '{print $4}' | sort | uniq -c | sort -nr
   
   # Check for new error patterns
   grep -i error logs/system.log | grep "$(date +%Y-%m-%d)" | \
     tail -10
   ```

3. **Check Processing Statistics**
   ```bash
   # Check papers processed today
   grep "papers processed" logs/system.log | grep "$(date +%Y-%m-%d)"
   
   # Check download statistics
   grep "downloaded" logs/system.log | grep "$(date +%Y-%m-%d)"
   ```

#### Actions
- Rotate logs if any file > 100MB
- Document new error patterns
- Report unusual processing statistics

## Weekly Operations

### Weekly Storage Management

**Frequency**: Every Sunday at 1 AM (automated) or weekly manual review  
**Duration**: 30-45 minutes

#### Procedure

1. **Storage Analysis**
   ```bash
   # Generate storage report
   python -m backend.multi_instance_arxiv_system.scripts.storage_manager analyze \
     --output weekly_storage_$(date +%Y%m%d).json
   
   # Review storage usage
   cat weekly_storage_$(date +%Y%m%d).json | jq '.total_usage'
   
   # Check recommendations
   cat weekly_storage_$(date +%Y%m%d).json | jq '.recommendations'
   ```

2. **Storage Cleanup**
   ```bash
   # Dry run cleanup
   python -m backend.multi_instance_arxiv_system.scripts.storage_manager cleanup \
     --dry-run --max-age-days 30
   
   # Review cleanup plan
   # If acceptable, run actual cleanup
   python -m backend.multi_instance_arxiv_system.scripts.storage_manager cleanup \
     --max-age-days 30
   ```

3. **Storage Optimization**
   ```bash
   # Run storage optimization
   python -m backend.multi_instance_arxiv_system.scripts.storage_manager optimize
   
   # Check optimization results
   du -sh data/*/
   ```

4. **Backup Verification**
   ```bash
   # Check backup status (if backups are configured)
   ls -la backups/
   
   # Verify recent backups
   find backups/ -name "*.tar.gz" -mtime -7 -ls
   ```

#### Expected Results
- Storage usage < 80% of available space
- Successful cleanup of temporary files
- Optimization completed without errors
- Recent backups available

#### Escalation
- If storage usage > 90%: Follow [Emergency Storage Cleanup](#emergency-storage-cleanup)
- If cleanup fails: Follow [Storage Recovery Procedure](#storage-recovery-procedure)

### Weekly Performance Review

**Frequency**: Weekly  
**Duration**: 20-30 minutes

#### Procedure

1. **Performance Metrics Collection**
   ```bash
   # Generate performance report
   python -m backend.multi_instance_arxiv_system.scripts.multi_instance_monitor \
     --output weekly_performance_$(date +%Y%m%d).json
   
   # Review system metrics
   cat weekly_performance_$(date +%Y%m%d).json | jq '.system_metrics'
   ```

2. **Processing Statistics Review**
   ```bash
   # Check processing rates
   grep "processing rate" logs/system.log | grep -E "$(date -d '7 days ago' +%Y-%m-%d)|$(date +%Y-%m-%d)"
   
   # Check error rates
   grep -c "error" logs/system.log | head -7  # Last 7 days
   ```

3. **Resource Utilization Analysis**
   ```bash
   # Check average CPU usage
   sar -u 1 1
   
   # Check memory usage trends
   free -h
   
   # Check disk I/O
   iostat -x 1 1
   ```

#### Actions
- Document performance trends
- Adjust configuration if performance degraded
- Plan capacity upgrades if needed

## Monthly Operations

### Monthly System Update

**Frequency**: First Sunday of each month  
**Duration**: 2-3 hours  
**Prerequisites**: Maintenance window scheduled, backups completed

#### Pre-Update Checklist

1. **System Backup**
   ```bash
   # Create full system backup
   tar -czf backup_pre_update_$(date +%Y%m%d).tar.gz \
     data/ config/ logs/ .env
   
   # Backup ChromaDB data
   docker exec chromadb tar -czf /tmp/chromadb_backup.tar.gz /chroma
   docker cp chromadb:/tmp/chromadb_backup.tar.gz ./chromadb_backup_$(date +%Y%m%d).tar.gz
   ```

2. **Health Check**
   ```bash
   # Verify system is healthy before update
   python -m backend.multi_instance_arxiv_system.scripts.system_health_check
   ```

3. **Stop Scheduled Jobs**
   ```bash
   # Disable cron jobs temporarily
   crontab -l > crontab_backup.txt
   crontab -r
   ```

#### Update Procedure

1. **Update System Packages**
   ```bash
   # Update OS packages
   sudo apt update && sudo apt upgrade -y
   
   # Update Python packages
   source venv/bin/activate
   pip list --outdated
   pip install --upgrade pip
   pip install -r requirements.txt --upgrade
   ```

2. **Update Application Code**
   ```bash
   # Pull latest code (if using git)
   git fetch origin
   git checkout main
   git pull origin main
   
   # Install any new dependencies
   pip install -r requirements.txt
   ```

3. **Database Updates**
   ```bash
   # Update ChromaDB if needed
   docker pull chromadb/chroma:latest
   docker stop chromadb
   docker rm chromadb
   docker run -d --name chromadb -p 8000:8000 \
     -v chromadb_data:/chroma/chroma chromadb/chroma:latest
   ```

4. **Configuration Updates**
   ```bash
   # Review configuration changes
   # Update config files if needed
   # Validate configurations
   python -c "
   from backend.multi_instance_arxiv_system.core.instance_config import InstanceConfigManager
   manager = InstanceConfigManager('config')
   for instance in ['ai_scholar', 'quant_scholar']:
       config = manager.load_instance_config(instance)
       print(f'{instance}: OK')
   "
   ```

#### Post-Update Verification

1. **System Health Check**
   ```bash
   # Verify system is healthy after update
   python -m backend.multi_instance_arxiv_system.scripts.system_health_check --verbose
   ```

2. **Functional Testing**
   ```bash
   # Test AI Scholar functionality
   python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_downloader \
     --dry-run --limit 5
   
   # Test Quant Scholar functionality
   python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader \
     --dry-run --limit 5
   
   # Test processing
   python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_processor \
     --dry-run
   ```

3. **Restore Scheduled Jobs**
   ```bash
   # Restore cron jobs
   crontab crontab_backup.txt
   crontab -l  # Verify
   ```

#### Rollback Procedure (if needed)

1. **Stop Current System**
   ```bash
   pkill -f "multi_instance_arxiv"
   docker stop chromadb
   ```

2. **Restore Backup**
   ```bash
   # Restore application files
   tar -xzf backup_pre_update_$(date +%Y%m%d).tar.gz
   
   # Restore ChromaDB
   docker rm chromadb
   docker run -d --name chromadb -p 8000:8000 chromadb/chroma:latest
   docker cp chromadb_backup_$(date +%Y%m%d).tar.gz chromadb:/tmp/
   docker exec chromadb tar -xzf /tmp/chromadb_backup_$(date +%Y%m%d).tar.gz -C /
   docker restart chromadb
   ```

3. **Verify Rollback**
   ```bash
   python -m backend.multi_instance_arxiv_system.scripts.system_health_check
   ```

### Monthly Performance Optimization

**Frequency**: Monthly  
**Duration**: 1-2 hours

#### Procedure

1. **Performance Analysis**
   ```bash
   # Generate comprehensive performance report
   python -c "
   from backend.multi_instance_arxiv_system.monitoring.performance_monitor import PerformanceMonitor
   monitor = PerformanceMonitor()
   report = monitor.generate_monthly_report()
   print(report)
   " > monthly_performance_$(date +%Y%m%d).txt
   ```

2. **Database Optimization**
   ```bash
   # Optimize ChromaDB collections
   python -c "
   import chromadb
   client = chromadb.HttpClient(host='localhost', port=8000)
   collections = client.list_collections()
   for collection in collections:
       print(f'Collection {collection.name}: {collection.count()} documents')
   "
   
   # Consider collection cleanup if too large
   ```

3. **Configuration Tuning**
   ```bash
   # Review and adjust configuration based on performance data
   # Update batch sizes, concurrency limits, etc.
   ```

4. **System Tuning**
   ```bash
   # Check system limits
   ulimit -a
   
   # Adjust if needed
   # Update /etc/security/limits.conf if necessary
   ```

## Emergency Procedures

### System Recovery Procedure

**Trigger**: System health check shows "unhealthy" status  
**Duration**: 30-60 minutes  
**Severity**: High

#### Immediate Actions

1. **Assess Situation**
   ```bash
   # Check system status
   python -m backend.multi_instance_arxiv_system.scripts.system_health_check \
     --verbose --output emergency_health.json
   
   # Check critical services
   docker ps | grep chromadb
   ps aux | grep python | grep arxiv
   ```

2. **Stop All Processing**
   ```bash
   # Stop all ArXiv system processes
   pkill -f "multi_instance_arxiv"
   
   # Disable cron jobs
   crontab -l > emergency_crontab_backup.txt
   crontab -r
   ```

3. **Check Resources**
   ```bash
   # Check disk space
   df -h
   
   # Check memory
   free -h
   
   # Check system load
   uptime
   ```

#### Recovery Steps

1. **Restart Core Services**
   ```bash
   # Restart ChromaDB
   docker restart chromadb
   
   # Wait for ChromaDB to be ready
   sleep 10
   curl http://localhost:8000/api/v1/heartbeat
   ```

2. **Clear Temporary Files**
   ```bash
   # Clear cache directories
   rm -rf data/*/cache/*
   
   # Clear lock files
   rm -f /tmp/arxiv_*.lock
   
   # Clear temporary downloads
   find data/*/papers/ -name "*.tmp" -delete
   ```

3. **Restart System Components**
   ```bash
   # Test basic functionality
   python -m backend.multi_instance_arxiv_system.scripts.system_health_check
   
   # If healthy, restore cron jobs
   crontab emergency_crontab_backup.txt
   ```

#### Verification

1. **Health Check**
   ```bash
   python -m backend.multi_instance_arxiv_system.scripts.system_health_check --verbose
   ```

2. **Functional Test**
   ```bash
   # Test each instance
   python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_downloader --dry-run --limit 1
   python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader --dry-run --limit 1
   ```

### Emergency Storage Cleanup

**Trigger**: Disk usage > 95%  
**Duration**: 15-30 minutes  
**Severity**: Critical

#### Immediate Actions

1. **Stop All Processing**
   ```bash
   pkill -f "multi_instance_arxiv"
   ```

2. **Emergency Cleanup**
   ```bash
   # Clear cache immediately
   rm -rf data/*/cache/*
   
   # Clear old logs
   find logs/ -name "*.log" -mtime +7 -delete
   
   # Clear temporary files
   find /tmp -name "arxiv_*" -delete
   find data/ -name "*.tmp" -delete
   ```

3. **Compress Large Files**
   ```bash
   # Compress old log files
   find logs/ -name "*.log" -mtime +1 -exec gzip {} \;
   
   # Check space freed
   df -h
   ```

#### Extended Cleanup (if needed)

1. **Archive Old Papers**
   ```bash
   # Find old papers (>90 days)
   find data/*/papers/ -name "*.pdf" -mtime +90 -ls
   
   # Archive to external storage or compress
   # (Manual decision based on business requirements)
   ```

2. **Database Cleanup**
   ```bash
   # Check ChromaDB disk usage
   docker exec chromadb du -sh /chroma
   
   # Consider collection cleanup if necessary
   ```

### Error Investigation Procedure

**Trigger**: Critical errors in logs or system alerts  
**Duration**: 30-60 minutes  
**Severity**: Medium-High

#### Investigation Steps

1. **Collect Error Information**
   ```bash
   # Extract recent errors
   grep -i error logs/system.log | tail -50 > error_investigation_$(date +%Y%m%d_%H%M).txt
   
   # Get error context
   grep -B5 -A5 "ERROR" logs/system.log | tail -100 >> error_investigation_$(date +%Y%m%d_%H%M).txt
   ```

2. **Categorize Errors**
   ```bash
   # Group errors by type
   grep -i error logs/system.log | awk '{print $5}' | sort | uniq -c | sort -nr
   
   # Check error frequency
   grep -i error logs/system.log | grep "$(date +%Y-%m-%d)" | wc -l
   ```

3. **Check System State**
   ```bash
   # Check if errors are ongoing
   tail -f logs/system.log | grep -i error &
   TAIL_PID=$!
   sleep 30
   kill $TAIL_PID
   ```

#### Resolution Actions

1. **Address Common Errors**
   ```bash
   # Network errors: Check connectivity
   curl -I https://arxiv.org/
   
   # PDF errors: Check PDF processing tools
   pdfinfo --version
   
   # Database errors: Check ChromaDB
   curl http://localhost:8000/api/v1/heartbeat
   ```

2. **Apply Fixes**
   ```bash
   # Restart services if needed
   docker restart chromadb
   
   # Clear problematic files
   # (Based on specific error analysis)
   ```

3. **Monitor Resolution**
   ```bash
   # Watch for error recurrence
   tail -f logs/system.log | grep -i error
   ```

## Maintenance Windows

### Scheduled Maintenance

**Frequency**: Monthly (first Sunday, 2-6 AM)  
**Duration**: 4 hours  
**Notification**: 48 hours advance notice

#### Pre-Maintenance

1. **Notification**
   ```bash
   # Send maintenance notification
   python -c "
   from backend.multi_instance_arxiv_system.reporting.email_notification_service import EmailNotificationService
   service = EmailNotificationService()
   service.send_maintenance_notification('Scheduled maintenance window: $(date)')
   "
   ```

2. **Backup**
   ```bash
   # Full system backup
   ./scripts/backup_system.sh
   ```

#### During Maintenance

1. **System Updates**
   - Follow [Monthly System Update](#monthly-system-update) procedure

2. **Performance Optimization**
   - Follow [Monthly Performance Optimization](#monthly-performance-optimization) procedure

3. **Security Updates**
   ```bash
   # Update security patches
   sudo apt update && sudo apt upgrade -y
   
   # Update SSL certificates if needed
   # Rotate API keys if scheduled
   ```

#### Post-Maintenance

1. **Verification**
   ```bash
   # Complete system health check
   python -m backend.multi_instance_arxiv_system.scripts.system_health_check --verbose
   
   # Performance verification
   # Run test downloads and processing
   ```

2. **Notification**
   ```bash
   # Send completion notification
   python -c "
   from backend.multi_instance_arxiv_system.reporting.email_notification_service import EmailNotificationService
   service = EmailNotificationService()
   service.send_maintenance_completion_notification()
   "
   ```

## Monitoring and Alerting

### Alert Response Procedures

#### Critical Alerts

**Response Time**: Immediate (< 15 minutes)

1. **System Down**
   - Follow [System Recovery Procedure](#system-recovery-procedure)
   - Notify stakeholders immediately

2. **Disk Space Critical (>95%)**
   - Follow [Emergency Storage Cleanup](#emergency-storage-cleanup)
   - Escalate if cleanup insufficient

3. **Database Unavailable**
   ```bash
   # Check ChromaDB status
   docker ps | grep chromadb
   docker logs chromadb
   
   # Restart if needed
   docker restart chromadb
   ```

#### Warning Alerts

**Response Time**: Within 2 hours

1. **High Error Rate**
   - Follow [Error Investigation Procedure](#error-investigation-procedure)
   - Monitor for escalation

2. **Performance Degradation**
   - Check system resources
   - Review recent changes
   - Adjust configuration if needed

3. **Storage Warning (>80%)**
   - Schedule storage cleanup
   - Plan capacity expansion

### Escalation Matrix

| Severity | Response Time | Escalation |
|----------|---------------|------------|
| Critical | < 15 minutes | Immediate notification to on-call engineer |
| High | < 1 hour | Notification to system administrator |
| Medium | < 4 hours | Email notification to operations team |
| Low | < 24 hours | Include in daily report |

## Documentation and Reporting

### Daily Reports

Generate and review daily operational reports:

```bash
# Generate daily report
python -m backend.multi_instance_arxiv_system.scripts.generate_daily_report \
  --output daily_report_$(date +%Y%m%d).html
```

### Weekly Reports

Generate weekly summary reports:

```bash
# Generate weekly report
python -m backend.multi_instance_arxiv_system.scripts.generate_weekly_report \
  --output weekly_report_$(date +%Y%m%d).html
```

### Incident Documentation

For each incident:

1. **Create Incident Record**
   - Date/time of incident
   - Symptoms observed
   - Root cause analysis
   - Resolution steps taken
   - Prevention measures

2. **Update Runbooks**
   - Add new procedures if needed
   - Update existing procedures based on lessons learned

3. **Review and Improve**
   - Monthly review of incidents
   - Update monitoring and alerting
   - Improve automation where possible

## Contact Information

### Emergency Contacts

- **Primary On-Call**: [Contact Information]
- **Secondary On-Call**: [Contact Information]
- **System Administrator**: [Contact Information]
- **Database Administrator**: [Contact Information]

### Vendor Contacts

- **Cloud Provider Support**: [Contact Information]
- **ChromaDB Support**: [Contact Information]
- **Email Service Provider**: [Contact Information]

### Internal Escalation

- **Operations Manager**: [Contact Information]
- **Engineering Manager**: [Contact Information]
- **CTO/Technical Director**: [Contact Information]