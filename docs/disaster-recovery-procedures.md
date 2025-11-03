# Multi-Instance ArXiv System - Disaster Recovery Procedures

## Overview

This document provides comprehensive disaster recovery procedures for the Multi-Instance ArXiv System. It covers various disaster scenarios, recovery strategies, and step-by-step procedures to restore system functionality with minimal data loss and downtime.

## Disaster Recovery Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Primary Site  │    │   Backup Site   │    │  Cloud Backup   │
│                 │    │   (Optional)    │    │                 │
│ • Live System   │───▶│ • Standby       │───▶│ • Long-term     │
│ • Real-time     │    │ • Sync'd Data   │    │ • Archive       │
│ • Operations    │    │ • Quick Switch  │    │ • Compliance    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Recovery      │
                    │   Orchestration │
                    │                 │
                    └─────────────────┘
```

## Disaster Scenarios and Response

### Scenario 1: Complete System Failure

**Symptoms:**
- System completely unresponsive
- All services down
- Hardware failure or corruption

**Recovery Priority:** CRITICAL (RTO: 4 hours, RPO: 1 hour)

**Recovery Procedure:**

1. **Immediate Assessment**
   ```bash
   # Run emergency assessment
   /opt/arxiv-system/scripts/emergency_assessment.sh
   
   # Check system status
   systemctl status chromadb arxiv-system-monitor
   docker ps -a
   ```

2. **Activate Disaster Recovery**
   ```bash
   # Switch to disaster recovery mode
   /opt/arxiv-system/scripts/activate_disaster_recovery.sh --scenario=complete_failure
   ```

3. **System Restoration**
   ```bash
   # Restore from latest full backup
   /opt/arxiv-system/scripts/restore_full_system.sh /opt/arxiv-system/backups/full_system_latest
   
   # Verify restoration
   /opt/arxiv-system/scripts/system_health_check.py
   ```

### Scenario 2: Database Corruption

**Symptoms:**
- ChromaDB not responding
- Data integrity errors
- Collection access failures

**Recovery Priority:** HIGH (RTO: 2 hours, RPO: 30 minutes)

**Recovery Procedure:**

1. **Stop All Services**
   ```bash
   systemctl stop arxiv-system-monitor chromadb
   docker stop chromadb
   ```

2. **Assess Corruption**
   ```bash
   # Check ChromaDB logs
   docker logs chromadb
   
   # Verify data integrity
   /opt/arxiv-system/scripts/verify_chromadb_integrity.sh
   ```

3. **Restore Database**
   ```bash
   # Restore from latest backup
   /opt/arxiv-system/scripts/restore_chromadb.sh /opt/arxiv-system/backups/chromadb/latest
   
   # Restart services
   systemctl start chromadb arxiv-system-monitor
   ```

### Scenario 3: Storage System Failure

**Symptoms:**
- Disk I/O errors
- File system corruption
- Storage device failure

**Recovery Priority:** HIGH (RTO: 3 hours, RPO: 1 hour)

**Recovery Procedure:**

1. **Emergency Data Preservation**
   ```bash
   # Create emergency backup of accessible data
   /opt/arxiv-system/scripts/emergency_backup.sh --target=/mnt/emergency_storage
   ```

2. **Storage Recovery**
   ```bash
   # Check file system integrity
   fsck /dev/sda1
   
   # Mount recovery storage
   mount /dev/sdb1 /mnt/recovery
   
   # Restore data
   /opt/arxiv-system/scripts/restore_from_storage_backup.sh /mnt/recovery
   ```

### Scenario 4: Network Infrastructure Failure

**Symptoms:**
- No internet connectivity
- DNS resolution failures
- Network timeouts

**Recovery Priority:** MEDIUM (RTO: 1 hour, RPO: N/A)

**Recovery Procedure:**

1. **Network Diagnostics**
   ```bash
   # Check network connectivity
   ping 8.8.8.8
   nslookup arxiv.org
   
   # Check network interfaces
   ip addr show
   ip route show
   ```

2. **Activate Offline Mode**
   ```bash
   # Switch to offline processing mode
   /opt/arxiv-system/scripts/activate_offline_mode.sh
   
   # Process existing papers only
   /opt/arxiv-system/scripts/process_local_papers.sh
   ```

### Scenario 5: Security Breach

**Symptoms:**
- Unauthorized access detected
- Suspicious system activity
- Data integrity concerns

**Recovery Priority:** CRITICAL (RTO: 1 hour, RPO: 0)

**Recovery Procedure:**

1. **Immediate Isolation**
   ```bash
   # Isolate system from network
   iptables -P INPUT DROP
   iptables -P OUTPUT DROP
   
   # Stop all external services
   systemctl stop arxiv-system-monitor
   ```

2. **Security Assessment**
   ```bash
   # Run security audit
   /opt/arxiv-system/scripts/security_audit.sh --emergency
   
   # Check for unauthorized changes
   /opt/arxiv-system/scripts/integrity_check.sh
   ```

3. **Clean Recovery**
   ```bash
   # Restore from known-good backup
   /opt/arxiv-system/scripts/secure_restore.sh --verify-integrity
   
   # Update all credentials
   /opt/arxiv-system/scripts/rotate_credentials.sh
   ```

## Recovery Scripts and Automation

### Emergency Assessment Script

```bash
cat > /opt/arxiv-system/scripts/emergency_assessment.sh << 'EOF'
#!/bin/bash

# Emergency System Assessment Script

echo "EMERGENCY SYSTEM ASSESSMENT - $(date)"
echo "======================================"

# System status
echo "System Status:"
echo "  Uptime: $(uptime)"
echo "  Load: $(cat /proc/loadavg)"
echo "  Memory: $(free -h | grep Mem)"
echo "  Disk: $(df -h / | tail -1)"

# Service status
echo -e "\nService Status:"
for service in chromadb arxiv-system-monitor; do
    status=$(systemctl is-active $service 2>/dev/null || echo "unknown")
    echo "  $service: $status"
done

# Docker status
echo -e "\nDocker Status:"
if command -v docker &> /dev/null; then
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "  Docker not available"
fi

# Network connectivity
echo -e "\nNetwork Status:"
ping -c 1 8.8.8.8 &>/dev/null && echo "  Internet: OK" || echo "  Internet: FAILED"
curl -s http://localhost:8000/api/v1/heartbeat &>/dev/null && echo "  ChromaDB: OK" || echo "  ChromaDB: FAILED"

# Critical files
echo -e "\nCritical Files:"
for file in /opt/arxiv-system/.env /opt/arxiv-system/config/ai_scholar.yaml; do
    if [[ -f "$file" ]]; then
        echo "  $file: EXISTS"
    else
        echo "  $file: MISSING"
    fi
done

# Recent errors
echo -e "\nRecent Errors (last 10):"
find /opt/arxiv-system/logs -name "*.log" -mmin -60 -exec grep -i error {} \; | tail -10

echo -e "\nAssessment completed at $(date)"
EOF

chmod +x /opt/arxiv-system/scripts/emergency_assessment.sh
```

### Disaster Recovery Activation Script

```bash
cat > /opt/arxiv-system/scripts/activate_disaster_recovery.sh << 'EOF'
#!/bin/bash

# Disaster Recovery Activation Script

SCENARIO="$1"
DR_LOG="/opt/arxiv-system/logs/disaster_recovery.log"

log() {
    echo "$(date): $*" | tee -a "$DR_LOG"
}

case "$SCENARIO" in
    --scenario=complete_failure)
        log "ACTIVATING: Complete system failure recovery"
        
        # Stop all services
        systemctl stop arxiv-system-monitor chromadb || true
        docker stop chromadb || true
        
        # Create emergency backup
        /opt/arxiv-system/scripts/emergency_backup.sh
        
        # Prepare for full restoration
        log "System prepared for full restoration"
        ;;
        
    --scenario=database_corruption)
        log "ACTIVATING: Database corruption recovery"
        
        # Stop database services
        systemctl stop chromadb || true
        docker stop chromadb || true
        
        # Backup corrupted state for analysis
        docker run --rm -v chromadb_data:/source:ro -v /opt/arxiv-system/backups/corrupted:/backup \
            ubuntu tar czf /backup/corrupted_chromadb_$(date +%Y%m%d_%H%M%S).tar.gz -C /source .
        
        log "Database corruption recovery activated"
        ;;
        
    --scenario=security_breach)
        log "ACTIVATING: Security breach response"
        
        # Immediate isolation
        iptables -P INPUT DROP
        iptables -P OUTPUT DROP
        iptables -A INPUT -i lo -j ACCEPT
        iptables -A OUTPUT -o lo -j ACCEPT
        
        # Stop external services
        systemctl stop arxiv-system-monitor || true
        
        # Log security event
        log "SECURITY: System isolated due to security breach"
        
        # Send alert (if possible)
        echo "SECURITY ALERT: ArXiv system isolated due to breach at $(date)" | \
            mail -s "SECURITY ALERT" admin@yourorg.com || true
        ;;
        
    *)
        echo "Usage: $0 --scenario={complete_failure|database_corruption|security_breach}"
        exit 1
        ;;
esac

log "Disaster recovery activation completed for scenario: $SCENARIO"
EOF

chmod +x /opt/arxiv-system/scripts/activate_disaster_recovery.sh
```

### Emergency Backup Script

```bash
cat > /opt/arxiv-system/scripts/emergency_backup.sh << 'EOF'
#!/bin/bash

# Emergency Backup Script

BACKUP_TARGET="${1:-/opt/arxiv-system/backups/emergency}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Starting emergency backup to: $BACKUP_TARGET"

# Create backup directory
mkdir -p "$BACKUP_TARGET"

# Backup critical configuration
echo "Backing up configuration..."
tar czf "$BACKUP_TARGET/emergency_config_$TIMESTAMP.tar.gz" \
    /opt/arxiv-system/config \
    /opt/arxiv-system/.env \
    2>/dev/null || true

# Backup ChromaDB if accessible
echo "Backing up ChromaDB..."
if docker ps | grep -q chromadb; then
    docker run --rm -v chromadb_data:/source:ro -v "$BACKUP_TARGET":/backup \
        ubuntu tar czf "/backup/emergency_chromadb_$TIMESTAMP.tar.gz" -C /source . \
        2>/dev/null || true
fi

# Backup recent logs
echo "Backing up recent logs..."
find /opt/arxiv-system/logs -name "*.log" -mtime -1 -exec cp {} "$BACKUP_TARGET/" \; 2>/dev/null || true

# Backup system information
echo "Collecting system information..."
cat > "$BACKUP_TARGET/system_info_$TIMESTAMP.txt" << INFO_EOF
Emergency Backup Information
===========================
Timestamp: $(date)
Hostname: $(hostname)
Uptime: $(uptime)
Disk Usage: $(df -h)
Memory: $(free -h)
Processes: $(ps aux | head -20)
Network: $(ip addr show)
Services: $(systemctl list-units --failed)
INFO_EOF

echo "Emergency backup completed: $BACKUP_TARGET"
ls -la "$BACKUP_TARGET"
EOF

chmod +x /opt/arxiv-system/scripts/emergency_backup.sh
```

## Recovery Time and Point Objectives

### Service Level Agreements

| **Component** | **RTO (Recovery Time)** | **RPO (Recovery Point)** | **Priority** |
|---------------|-------------------------|--------------------------|--------------|
| ChromaDB | 2 hours | 30 minutes | Critical |
| AI Scholar Instance | 4 hours | 1 hour | High |
| Quant Scholar Instance | 4 hours | 1 hour | High |
| Monitoring System | 1 hour | 15 minutes | Medium |
| Email Notifications | 30 minutes | 5 minutes | Low |

### Recovery Priorities

1. **Critical (P1)**: ChromaDB, Core System Infrastructure
2. **High (P2)**: Scholar Instances, Data Processing
3. **Medium (P3)**: Monitoring, Reporting
4. **Low (P4)**: Email Notifications, Non-essential Features

## Communication Procedures

### Emergency Contacts

```yaml
# Emergency Contact List
primary_contacts:
  - name: "System Administrator"
    email: "admin@yourorg.com"
    phone: "+1-555-0101"
    role: "Primary DR Coordinator"
  
  - name: "Technical Lead"
    email: "tech-lead@yourorg.com"
    phone: "+1-555-0102"
    role: "Technical Recovery"

secondary_contacts:
  - name: "Operations Manager"
    email: "ops@yourorg.com"
    phone: "+1-555-0103"
    role: "Business Continuity"
  
  - name: "Security Officer"
    email: "security@yourorg.com"
    phone: "+1-555-0104"
    role: "Security Incidents"

escalation:
  - level: 1
    timeout: "30 minutes"
    contacts: ["admin@yourorg.com"]
  
  - level: 2
    timeout: "1 hour"
    contacts: ["admin@yourorg.com", "tech-lead@yourorg.com"]
  
  - level: 3
    timeout: "2 hours"
    contacts: ["all_contacts", "management@yourorg.com"]
```

### Communication Templates

#### Initial Incident Notification

```
Subject: [INCIDENT] ArXiv System Disaster - Immediate Action Required

INCIDENT DETAILS:
- System: Multi-Instance ArXiv System
- Severity: [CRITICAL/HIGH/MEDIUM]
- Start Time: [TIMESTAMP]
- Impact: [DESCRIPTION]
- Estimated Users Affected: [NUMBER]

INITIAL ASSESSMENT:
- Root Cause: [PRELIMINARY ASSESSMENT]
- Services Affected: [LIST]
- Data Loss Risk: [YES/NO/UNKNOWN]

IMMEDIATE ACTIONS TAKEN:
- [ACTION 1]
- [ACTION 2]
- [ACTION 3]

RECOVERY PLAN:
- Estimated Recovery Time: [HOURS]
- Recovery Coordinator: [NAME]
- Next Update: [TIMESTAMP]

CONTACT INFORMATION:
- Incident Commander: [NAME] - [PHONE]
- Technical Lead: [NAME] - [PHONE]
```

#### Recovery Progress Update

```
Subject: [UPDATE] ArXiv System Recovery - Progress Report #[NUMBER]

RECOVERY STATUS:
- Current Phase: [PHASE NAME]
- Progress: [PERCENTAGE]%
- Estimated Completion: [TIMESTAMP]

COMPLETED ACTIONS:
- [ACTION 1] - [TIMESTAMP]
- [ACTION 2] - [TIMESTAMP]

IN PROGRESS:
- [ACTION] - ETA: [TIMESTAMP]

NEXT STEPS:
- [STEP 1] - [TIMELINE]
- [STEP 2] - [TIMELINE]

ISSUES/BLOCKERS:
- [ISSUE] - [RESOLUTION PLAN]

SERVICES STATUS:
- ChromaDB: [STATUS]
- AI Scholar: [STATUS]
- Quant Scholar: [STATUS]
- Monitoring: [STATUS]
```

## Testing and Validation

### Disaster Recovery Testing Schedule

| **Test Type** | **Frequency** | **Scope** | **Duration** |
|---------------|---------------|-----------|--------------|
| Backup Verification | Weekly | All backups | 30 minutes |
| Database Recovery | Monthly | ChromaDB restore | 2 hours |
| Full System Recovery | Quarterly | Complete system | 4 hours |
| Security Breach Simulation | Semi-annually | Security procedures | 3 hours |
| Network Failure Test | Annually | Offline mode | 2 hours |

### Recovery Testing Procedures

#### Monthly Database Recovery Test

```bash
#!/bin/bash
# Monthly Database Recovery Test

TEST_LOG="/opt/arxiv-system/logs/dr_test_$(date +%Y%m%d).log"

echo "Starting monthly database recovery test..." | tee "$TEST_LOG"

# 1. Create test backup
echo "Creating test backup..." | tee -a "$TEST_LOG"
/opt/arxiv-system/scripts/backup_chromadb.sh

# 2. Stop ChromaDB
echo "Stopping ChromaDB..." | tee -a "$TEST_LOG"
docker stop chromadb

# 3. Clear data
echo "Clearing test data..." | tee -a "$TEST_LOG"
docker run --rm -v chromadb_data:/data ubuntu rm -rf /data/test_*

# 4. Restore from backup
echo "Restoring from backup..." | tee -a "$TEST_LOG"
LATEST_BACKUP=$(ls -t /opt/arxiv-system/backups/chromadb/chromadb_backup_*.tar.gz | head -1)
/opt/arxiv-system/scripts/restore_chromadb.sh "$LATEST_BACKUP"

# 5. Verify restoration
echo "Verifying restoration..." | tee -a "$TEST_LOG"
sleep 10
if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; then
    echo "✓ Database recovery test PASSED" | tee -a "$TEST_LOG"
else
    echo "✗ Database recovery test FAILED" | tee -a "$TEST_LOG"
fi

echo "Test completed at $(date)" | tee -a "$TEST_LOG"
```

## Post-Recovery Procedures

### System Validation Checklist

After any disaster recovery, complete this validation checklist:

- [ ] **System Resources**
  - [ ] CPU usage normal (<80%)
  - [ ] Memory usage normal (<80%)
  - [ ] Disk space adequate (>20% free)
  - [ ] Network connectivity restored

- [ ] **Core Services**
  - [ ] ChromaDB responding
  - [ ] All systemd services running
  - [ ] Docker containers healthy
  - [ ] Cron jobs scheduled

- [ ] **Data Integrity**
  - [ ] Vector collections accessible
  - [ ] Document counts match expectations
  - [ ] No data corruption detected
  - [ ] Backup systems functional

- [ ] **Application Functions**
  - [ ] AI Scholar instance operational
  - [ ] Quant Scholar instance operational
  - [ ] Processing pipelines working
  - [ ] Email notifications sending

- [ ] **Security**
  - [ ] Access controls verified
  - [ ] Credentials rotated (if breach)
  - [ ] Audit logs reviewed
  - [ ] Security monitoring active

### Recovery Documentation

After each disaster recovery event, document:

1. **Incident Timeline**
   - Detection time
   - Response time
   - Recovery completion time
   - Total downtime

2. **Root Cause Analysis**
   - Primary cause
   - Contributing factors
   - Prevention measures

3. **Recovery Effectiveness**
   - RTO/RPO achievement
   - Data loss assessment
   - Process improvements

4. **Lessons Learned**
   - What worked well
   - What needs improvement
   - Updated procedures

## Continuous Improvement

### Regular Reviews

- **Monthly**: Review backup success rates and recovery test results
- **Quarterly**: Update disaster recovery procedures based on system changes
- **Annually**: Conduct comprehensive DR plan review and update

### Metrics and KPIs

- **Recovery Time Actual vs. Target**
- **Data Loss Incidents**
- **Backup Success Rate**
- **Test Success Rate**
- **Mean Time to Recovery (MTTR)**

---

This disaster recovery plan should be reviewed and updated regularly to ensure it remains current with system changes and organizational requirements. All team members should be familiar with these procedures and participate in regular disaster recovery drills.