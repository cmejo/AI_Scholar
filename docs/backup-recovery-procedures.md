# Multi-Instance ArXiv System - Backup and Recovery Procedures

## Overview

This document provides comprehensive backup and recovery procedures for the Multi-Instance ArXiv System. It covers data protection strategies, backup automation, disaster recovery, and system restoration procedures.

## Backup Strategy

### Data Classification

The system contains several types of data with different backup requirements:

1. **Critical Data** (Daily backups, 30-day retention)
   - ChromaDB vector database
   - System configuration files
   - Instance configuration files
   - Processing state and metadata

2. **Important Data** (Weekly backups, 12-week retention)
   - Downloaded PDF papers
   - Processing logs
   - Email templates and reports

3. **Recoverable Data** (Monthly backups, 6-month retention)
   - Cache files
   - Temporary processing files
   - System logs

### Backup Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Local Backup  │    │  Remote Backup  │    │  Cloud Backup   │
│   (Daily)       │    │  (Weekly)       │    │  (Monthly)      │
│                 │    │                 │    │                 │
│ • ChromaDB      │───▶│ • Full System   │───▶│ • Archive       │
│ • Configs       │    │ • Papers        │    │ • Long-term     │
│ • Metadata      │    │ • Logs          │    │ • Disaster      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Backup Implementation

### 1. ChromaDB Backup

Create ChromaDB backup script:

```bash
cat > /opt/arxiv-system/scripts/backup_chromadb.sh << 'EOF'
#!/bin/bash

# ChromaDB Backup Script
# Creates a backup of the ChromaDB vector database

BACKUP_DIR="/opt/arxiv-system/backups/chromadb"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="chromadb_backup_${TIMESTAMP}.tar.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Log backup start
echo "$(date): Starting ChromaDB backup" >> /opt/arxiv-system/logs/backup.log

# Stop ChromaDB temporarily for consistent backup
echo "Stopping ChromaDB for backup..."
docker stop chromadb

# Create backup
echo "Creating backup: $BACKUP_FILE"
docker run --rm \
  -v chromadb_data:/source:ro \
  -v "$BACKUP_DIR":/backup \
  ubuntu tar czf "/backup/$BACKUP_FILE" -C /source .

# Restart ChromaDB
echo "Restarting ChromaDB..."
docker start chromadb

# Wait for ChromaDB to be ready
sleep 10
until curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; do
  echo "Waiting for ChromaDB to start..."
  sleep 5
done

# Verify backup
if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
  BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
  echo "$(date): ChromaDB backup completed successfully - Size: $BACKUP_SIZE" >> /opt/arxiv-system/logs/backup.log
  echo "Backup completed: $BACKUP_DIR/$BACKUP_FILE ($BACKUP_SIZE)"
else
  echo "$(date): ChromaDB backup failed" >> /opt/arxiv-system/logs/backup.log
  echo "ERROR: Backup failed"
  exit 1
fi

# Cleanup old backups (keep last 30 days)
find "$BACKUP_DIR" -name "chromadb_backup_*.tar.gz" -mtime +30 -delete

echo "ChromaDB backup process completed"
EOF

chmod +x /opt/arxiv-system/scripts/backup_chromadb.sh
```

### 2. Configuration Backup

Create configuration backup script:

```bash
cat > /opt/arxiv-system/scripts/backup_configs.sh << 'EOF'
#!/bin/bash

# Configuration Backup Script
# Backs up all system and instance configurations

BACKUP_DIR="/opt/arxiv-system/backups/configs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="configs_backup_${TIMESTAMP}.tar.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Log backup start
echo "$(date): Starting configuration backup" >> /opt/arxiv-system/logs/backup.log

# Create temporary directory for backup
TEMP_DIR=$(mktemp -d)
CONFIG_BACKUP_DIR="$TEMP_DIR/arxiv_system_configs"
mkdir -p "$CONFIG_BACKUP_DIR"

# Copy configuration files
echo "Backing up configuration files..."

# System configurations
cp -r /opt/arxiv-system/config "$CONFIG_BACKUP_DIR/"
cp /opt/arxiv-system/.env "$CONFIG_BACKUP_DIR/" 2>/dev/null || true

# Monitoring configurations
cp -r /opt/arxiv-system/monitoring/config "$CONFIG_BACKUP_DIR/monitoring_config" 2>/dev/null || true

# Cron configurations
crontab -l > "$CONFIG_BACKUP_DIR/crontab.txt" 2>/dev/null || true

# System service files
mkdir -p "$CONFIG_BACKUP_DIR/systemd"
cp /etc/systemd/system/chromadb.service "$CONFIG_BACKUP_DIR/systemd/" 2>/dev/null || true

# Logrotate configuration
cp /etc/logrotate.d/arxiv-system "$CONFIG_BACKUP_DIR/logrotate.conf" 2>/dev/null || true

# Create backup archive
cd "$TEMP_DIR"
tar czf "$BACKUP_DIR/$BACKUP_FILE" arxiv_system_configs/

# Cleanup temporary directory
rm -rf "$TEMP_DIR"

# Verify backup
if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
  BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
  echo "$(date): Configuration backup completed successfully - Size: $BACKUP_SIZE" >> /opt/arxiv-system/logs/backup.log
  echo "Configuration backup completed: $BACKUP_DIR/$BACKUP_FILE ($BACKUP_SIZE)"
else
  echo "$(date): Configuration backup failed" >> /opt/arxiv-system/logs/backup.log
  echo "ERROR: Configuration backup failed"
  exit 1
fi

# Cleanup old backups (keep last 30 days)
find "$BACKUP_DIR" -name "configs_backup_*.tar.gz" -mtime +30 -delete

echo "Configuration backup process completed"
EOF

chmod +x /opt/arxiv-system/scripts/backup_configs.sh
```

### 3. Data Backup

Create data backup script:

```bash
cat > /opt/arxiv-system/scripts/backup_data.sh << 'EOF'
#!/bin/bash

# Data Backup Script
# Backs up papers, logs, and processing state

BACKUP_DIR="/opt/arxiv-system/backups/data"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
INSTANCE="$1"

if [ -z "$INSTANCE" ]; then
  echo "Usage: $0 <instance_name>"
  echo "Available instances: ai_scholar, quant_scholar, all"
  exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Function to backup single instance
backup_instance() {
  local instance_name="$1"
  local instance_dir="/opt/arxiv-system/data/$instance_name"
  
  if [ ! -d "$instance_dir" ]; then
    echo "Instance directory not found: $instance_dir"
    return 1
  fi
  
  local backup_file="data_${instance_name}_${TIMESTAMP}.tar.gz"
  
  echo "Backing up $instance_name data..."
  echo "$(date): Starting $instance_name data backup" >> /opt/arxiv-system/logs/backup.log
  
  # Create backup with compression and progress
  tar czf "$BACKUP_DIR/$backup_file" \
    -C "/opt/arxiv-system/data" \
    --exclude="cache/*" \
    --exclude="*.tmp" \
    "$instance_name"
  
  if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/$backup_file" | cut -f1)
    echo "$(date): $instance_name data backup completed - Size: $BACKUP_SIZE" >> /opt/arxiv-system/logs/backup.log
    echo "$instance_name backup completed: $BACKUP_DIR/$backup_file ($BACKUP_SIZE)"
  else
    echo "$(date): $instance_name data backup failed" >> /opt/arxiv-system/logs/backup.log
    echo "ERROR: $instance_name backup failed"
    return 1
  fi
}

# Backup based on parameter
case "$INSTANCE" in
  "ai_scholar"|"quant_scholar")
    backup_instance "$INSTANCE"
    ;;
  "all")
    backup_instance "ai_scholar"
    backup_instance "quant_scholar"
    ;;
  *)
    echo "Invalid instance: $INSTANCE"
    echo "Available instances: ai_scholar, quant_scholar, all"
    exit 1
    ;;
esac

# Cleanup old backups (keep last 12 weeks for data backups)
find "$BACKUP_DIR" -name "data_*.tar.gz" -mtime +84 -delete

echo "Data backup process completed"
EOF

chmod +x /opt/arxiv-system/scripts/backup_data.sh
```

### 4. Full System Backup

Create comprehensive backup script:

```bash
cat > /opt/arxiv-system/scripts/backup_full_system.sh << 'EOF'
#!/bin/bash

# Full System Backup Script
# Performs complete system backup

BACKUP_ROOT="/opt/arxiv-system/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FULL_BACKUP_DIR="$BACKUP_ROOT/full_system_$TIMESTAMP"

# Create backup directory
mkdir -p "$FULL_BACKUP_DIR"

echo "Starting full system backup: $TIMESTAMP"
echo "$(date): Starting full system backup" >> /opt/arxiv-system/logs/backup.log

# 1. Backup ChromaDB
echo "1/4: Backing up ChromaDB..."
/opt/arxiv-system/scripts/backup_chromadb.sh
if [ $? -eq 0 ]; then
  # Move ChromaDB backup to full backup directory
  LATEST_CHROMADB=$(ls -t /opt/arxiv-system/backups/chromadb/chromadb_backup_*.tar.gz | head -1)
  cp "$LATEST_CHROMADB" "$FULL_BACKUP_DIR/"
  echo "ChromaDB backup included in full backup"
else
  echo "ERROR: ChromaDB backup failed"
  exit 1
fi

# 2. Backup configurations
echo "2/4: Backing up configurations..."
/opt/arxiv-system/scripts/backup_configs.sh
if [ $? -eq 0 ]; then
  # Move config backup to full backup directory
  LATEST_CONFIG=$(ls -t /opt/arxiv-system/backups/configs/configs_backup_*.tar.gz | head -1)
  cp "$LATEST_CONFIG" "$FULL_BACKUP_DIR/"
  echo "Configuration backup included in full backup"
else
  echo "ERROR: Configuration backup failed"
  exit 1
fi

# 3. Backup all instance data
echo "3/4: Backing up instance data..."
/opt/arxiv-system/scripts/backup_data.sh all
if [ $? -eq 0 ]; then
  # Move data backups to full backup directory
  LATEST_AI_DATA=$(ls -t /opt/arxiv-system/backups/data/data_ai_scholar_*.tar.gz | head -1)
  LATEST_QUANT_DATA=$(ls -t /opt/arxiv-system/backups/data/data_quant_scholar_*.tar.gz | head -1)
  cp "$LATEST_AI_DATA" "$FULL_BACKUP_DIR/" 2>/dev/null || true
  cp "$LATEST_QUANT_DATA" "$FULL_BACKUP_DIR/" 2>/dev/null || true
  echo "Instance data backups included in full backup"
else
  echo "ERROR: Instance data backup failed"
  exit 1
fi

# 4. Create system information snapshot
echo "4/4: Creating system information snapshot..."
cat > "$FULL_BACKUP_DIR/system_info.txt" << EOF
Full System Backup Information
==============================
Backup Date: $(date)
System: $(uname -a)
Python Version: $(python3 --version)
Docker Version: $(docker --version)
Disk Usage: $(df -h /opt/arxiv-system)
Memory: $(free -h)

Installed Packages:
$(pip list)

Docker Containers:
$(docker ps -a)

Cron Jobs:
$(crontab -l)
EOF

# Create backup manifest
echo "Creating backup manifest..."
cat > "$FULL_BACKUP_DIR/MANIFEST.txt" << EOF
Multi-Instance ArXiv System - Full Backup Manifest
==================================================
Backup Timestamp: $TIMESTAMP
Backup Location: $FULL_BACKUP_DIR

Contents:
$(ls -la "$FULL_BACKUP_DIR")

Backup Sizes:
$(du -h "$FULL_BACKUP_DIR"/* | sort -hr)

Total Backup Size: $(du -sh "$FULL_BACKUP_DIR" | cut -f1)

Restoration Instructions:
1. Extract ChromaDB backup to Docker volume
2. Restore configuration files to /opt/arxiv-system/
3. Extract instance data to /opt/arxiv-system/data/
4. Restart services and verify functionality

For detailed restoration procedures, see:
/opt/arxiv-system/docs/backup-recovery-procedures.md
EOF

# Calculate total backup size
TOTAL_SIZE=$(du -sh "$FULL_BACKUP_DIR" | cut -f1)

echo "$(date): Full system backup completed - Size: $TOTAL_SIZE" >> /opt/arxiv-system/logs/backup.log
echo "Full system backup completed: $FULL_BACKUP_DIR ($TOTAL_SIZE)"

# Cleanup old full backups (keep last 4 full backups)
ls -dt /opt/arxiv-system/backups/full_system_* | tail -n +5 | xargs rm -rf

echo "Full system backup process completed successfully"
EOF

chmod +x /opt/arxiv-system/scripts/backup_full_system.sh
```

## Recovery Procedures

### 1. ChromaDB Recovery

Create ChromaDB recovery script:

```bash
cat > /opt/arxiv-system/scripts/restore_chromadb.sh << 'EOF'
#!/bin/bash

# ChromaDB Recovery Script
# Restores ChromaDB from backup

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
  echo "Usage: $0 <backup_file>"
  echo "Example: $0 /opt/arxiv-system/backups/chromadb/chromadb_backup_20241030_120000.tar.gz"
  exit 1
fi

echo "Starting ChromaDB recovery from: $BACKUP_FILE"
echo "$(date): Starting ChromaDB recovery from $BACKUP_FILE" >> /opt/arxiv-system/logs/recovery.log

# Stop ChromaDB
echo "Stopping ChromaDB..."
docker stop chromadb

# Remove existing data (backup current state first)
echo "Backing up current ChromaDB state..."
CURRENT_BACKUP="/opt/arxiv-system/backups/chromadb/pre_recovery_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
docker run --rm \
  -v chromadb_data:/source:ro \
  -v /opt/arxiv-system/backups/chromadb:/backup \
  ubuntu tar czf "/backup/$(basename $CURRENT_BACKUP)" -C /source . 2>/dev/null || true

# Clear existing data
echo "Clearing existing ChromaDB data..."
docker run --rm -v chromadb_data:/data ubuntu rm -rf /data/*

# Restore from backup
echo "Restoring ChromaDB data..."
docker run --rm \
  -v chromadb_data:/data \
  -v "$(dirname $BACKUP_FILE)":/backup:ro \
  ubuntu tar xzf "/backup/$(basename $BACKUP_FILE)" -C /data

# Start ChromaDB
echo "Starting ChromaDB..."
docker start chromadb

# Wait for ChromaDB to be ready
echo "Waiting for ChromaDB to start..."
sleep 15
RETRY_COUNT=0
until curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; do
  echo "Waiting for ChromaDB to respond..."
  sleep 5
  RETRY_COUNT=$((RETRY_COUNT + 1))
  if [ $RETRY_COUNT -gt 12 ]; then
    echo "ERROR: ChromaDB failed to start after recovery"
    echo "$(date): ChromaDB recovery failed - service not responding" >> /opt/arxiv-system/logs/recovery.log
    exit 1
  fi
done

# Verify recovery
echo "Verifying ChromaDB recovery..."
COLLECTIONS=$(curl -s http://localhost:8000/api/v1/collections | jq length 2>/dev/null || echo "0")
echo "ChromaDB is running with $COLLECTIONS collections"

echo "$(date): ChromaDB recovery completed successfully - $COLLECTIONS collections restored" >> /opt/arxiv-system/logs/recovery.log
echo "ChromaDB recovery completed successfully"
EOF

chmod +x /opt/arxiv-system/scripts/restore_chromadb.sh
```

### 2. Configuration Recovery

Create configuration recovery script:

```bash
cat > /opt/arxiv-system/scripts/restore_configs.sh << 'EOF'
#!/bin/bash

# Configuration Recovery Script
# Restores system configurations from backup

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
  echo "Usage: $0 <config_backup_file>"
  echo "Example: $0 /opt/arxiv-system/backups/configs/configs_backup_20241030_120000.tar.gz"
  exit 1
fi

echo "Starting configuration recovery from: $BACKUP_FILE"
echo "$(date): Starting configuration recovery from $BACKUP_FILE" >> /opt/arxiv-system/logs/recovery.log

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Extract backup
echo "Extracting configuration backup..."
tar xzf "$BACKUP_FILE"

if [ ! -d "arxiv_system_configs" ]; then
  echo "ERROR: Invalid backup file format"
  rm -rf "$TEMP_DIR"
  exit 1
fi

cd arxiv_system_configs

# Backup current configurations
echo "Backing up current configurations..."
CURRENT_BACKUP_DIR="/opt/arxiv-system/backups/configs/pre_recovery_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$CURRENT_BACKUP_DIR"
cp -r /opt/arxiv-system/config "$CURRENT_BACKUP_DIR/" 2>/dev/null || true
cp /opt/arxiv-system/.env "$CURRENT_BACKUP_DIR/" 2>/dev/null || true

# Restore configurations
echo "Restoring system configurations..."

# Main config directory
if [ -d "config" ]; then
  cp -r config/* /opt/arxiv-system/config/
  echo "System configurations restored"
fi

# Environment file
if [ -f ".env" ]; then
  cp .env /opt/arxiv-system/
  chmod 600 /opt/arxiv-system/.env
  echo "Environment configuration restored"
fi

# Monitoring configurations
if [ -d "monitoring_config" ]; then
  mkdir -p /opt/arxiv-system/monitoring/config
  cp -r monitoring_config/* /opt/arxiv-system/monitoring/config/
  echo "Monitoring configurations restored"
fi

# Cron configuration
if [ -f "crontab.txt" ]; then
  echo "Restoring cron jobs..."
  crontab crontab.txt
  echo "Cron jobs restored"
fi

# System service files
if [ -d "systemd" ]; then
  echo "Restoring systemd service files..."
  sudo cp systemd/* /etc/systemd/system/ 2>/dev/null || true
  sudo systemctl daemon-reload
  echo "Systemd services restored"
fi

# Logrotate configuration
if [ -f "logrotate.conf" ]; then
  sudo cp logrotate.conf /etc/logrotate.d/arxiv-system
  echo "Logrotate configuration restored"
fi

# Cleanup
cd /
rm -rf "$TEMP_DIR"

echo "$(date): Configuration recovery completed successfully" >> /opt/arxiv-system/logs/recovery.log
echo "Configuration recovery completed successfully"
echo "Note: You may need to restart services for changes to take effect"
EOF

chmod +x /opt/arxiv-system/scripts/restore_configs.sh
```

### 3. Data Recovery

Create data recovery script:

```bash
cat > /opt/arxiv-system/scripts/restore_data.sh << 'EOF'
#!/bin/bash

# Data Recovery Script
# Restores instance data from backup

BACKUP_FILE="$1"
INSTANCE="$2"

if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
  echo "Usage: $0 <data_backup_file> [instance_name]"
  echo "Example: $0 /opt/arxiv-system/backups/data/data_ai_scholar_20241030_120000.tar.gz ai_scholar"
  exit 1
fi

# Extract instance name from filename if not provided
if [ -z "$INSTANCE" ]; then
  INSTANCE=$(basename "$BACKUP_FILE" | sed 's/data_\(.*\)_[0-9]*_[0-9]*.tar.gz/\1/')
fi

if [ -z "$INSTANCE" ]; then
  echo "ERROR: Could not determine instance name"
  echo "Please specify instance name as second parameter"
  exit 1
fi

INSTANCE_DIR="/opt/arxiv-system/data/$INSTANCE"

echo "Starting data recovery for $INSTANCE from: $BACKUP_FILE"
echo "$(date): Starting $INSTANCE data recovery from $BACKUP_FILE" >> /opt/arxiv-system/logs/recovery.log

# Backup current data
if [ -d "$INSTANCE_DIR" ]; then
  echo "Backing up current $INSTANCE data..."
  CURRENT_BACKUP="/opt/arxiv-system/backups/data/pre_recovery_${INSTANCE}_$(date +%Y%m%d_%H%M%S).tar.gz"
  tar czf "$CURRENT_BACKUP" -C "/opt/arxiv-system/data" "$INSTANCE" 2>/dev/null || true
  echo "Current data backed up to: $CURRENT_BACKUP"
fi

# Create instance directory
mkdir -p "/opt/arxiv-system/data"

# Extract backup
echo "Extracting $INSTANCE data..."
tar xzf "$BACKUP_FILE" -C "/opt/arxiv-system/data"

# Verify restoration
if [ -d "$INSTANCE_DIR" ]; then
  PAPER_COUNT=$(find "$INSTANCE_DIR/papers" -name "*.pdf" 2>/dev/null | wc -l)
  TOTAL_SIZE=$(du -sh "$INSTANCE_DIR" | cut -f1)
  
  echo "$(date): $INSTANCE data recovery completed - $PAPER_COUNT papers, $TOTAL_SIZE total" >> /opt/arxiv-system/logs/recovery.log
  echo "$INSTANCE data recovery completed successfully"
  echo "Papers restored: $PAPER_COUNT"
  echo "Total size: $TOTAL_SIZE"
else
  echo "$(date): $INSTANCE data recovery failed - directory not found" >> /opt/arxiv-system/logs/recovery.log
  echo "ERROR: Data recovery failed"
  exit 1
fi
EOF

chmod +x /opt/arxiv-system/scripts/restore_data.sh
```

### 4. Full System Recovery

Create comprehensive recovery script:

```bash
cat > /opt/arxiv-system/scripts/restore_full_system.sh << 'EOF'
#!/bin/bash

# Full System Recovery Script
# Restores complete system from full backup

BACKUP_DIR="$1"

if [ -z "$BACKUP_DIR" ] || [ ! -d "$BACKUP_DIR" ]; then
  echo "Usage: $0 <full_backup_directory>"
  echo "Example: $0 /opt/arxiv-system/backups/full_system_20241030_120000"
  exit 1
fi

if [ ! -f "$BACKUP_DIR/MANIFEST.txt" ]; then
  echo "ERROR: Invalid backup directory - MANIFEST.txt not found"
  exit 1
fi

echo "Starting full system recovery from: $BACKUP_DIR"
echo "$(date): Starting full system recovery from $BACKUP_DIR" >> /opt/arxiv-system/logs/recovery.log

# Display backup information
echo "Backup Information:"
echo "=================="
cat "$BACKUP_DIR/MANIFEST.txt"
echo
read -p "Continue with recovery? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Recovery cancelled"
  exit 0
fi

# 1. Restore ChromaDB
echo "1/4: Restoring ChromaDB..."
CHROMADB_BACKUP=$(find "$BACKUP_DIR" -name "chromadb_backup_*.tar.gz" | head -1)
if [ -n "$CHROMADB_BACKUP" ]; then
  /opt/arxiv-system/scripts/restore_chromadb.sh "$CHROMADB_BACKUP"
  if [ $? -ne 0 ]; then
    echo "ERROR: ChromaDB restoration failed"
    exit 1
  fi
else
  echo "WARNING: No ChromaDB backup found in full backup"
fi

# 2. Restore configurations
echo "2/4: Restoring configurations..."
CONFIG_BACKUP=$(find "$BACKUP_DIR" -name "configs_backup_*.tar.gz" | head -1)
if [ -n "$CONFIG_BACKUP" ]; then
  /opt/arxiv-system/scripts/restore_configs.sh "$CONFIG_BACKUP"
  if [ $? -ne 0 ]; then
    echo "ERROR: Configuration restoration failed"
    exit 1
  fi
else
  echo "WARNING: No configuration backup found in full backup"
fi

# 3. Restore instance data
echo "3/4: Restoring instance data..."
AI_DATA_BACKUP=$(find "$BACKUP_DIR" -name "data_ai_scholar_*.tar.gz" | head -1)
QUANT_DATA_BACKUP=$(find "$BACKUP_DIR" -name "data_quant_scholar_*.tar.gz" | head -1)

if [ -n "$AI_DATA_BACKUP" ]; then
  /opt/arxiv-system/scripts/restore_data.sh "$AI_DATA_BACKUP" ai_scholar
fi

if [ -n "$QUANT_DATA_BACKUP" ]; then
  /opt/arxiv-system/scripts/restore_data.sh "$QUANT_DATA_BACKUP" quant_scholar
fi

# 4. Restart services and verify
echo "4/4: Restarting services and verifying system..."

# Restart ChromaDB
docker restart chromadb
sleep 10

# Verify ChromaDB
echo "Verifying ChromaDB..."
RETRY_COUNT=0
until curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; do
  echo "Waiting for ChromaDB..."
  sleep 5
  RETRY_COUNT=$((RETRY_COUNT + 1))
  if [ $RETRY_COUNT -gt 12 ]; then
    echo "ERROR: ChromaDB not responding after recovery"
    exit 1
  fi
done

# Run system health check
echo "Running system health check..."
/opt/arxiv-system/monitoring/scripts/health_check.sh

echo "$(date): Full system recovery completed successfully" >> /opt/arxiv-system/logs/recovery.log
echo
echo "Full system recovery completed successfully!"
echo "Please verify all functionality before resuming normal operations."
EOF

chmod +x /opt/arxiv-system/scripts/restore_full_system.sh
```

## Disaster Recovery Plan

### Emergency Response Procedures

#### 1. System Failure Response

```bash
# Emergency system assessment script
cat > /opt/arxiv-system/scripts/emergency_assessment.sh << 'EOF'
#!/bin/bash

echo "EMERGENCY SYSTEM ASSESSMENT"
echo "=========================="
echo "Timestamp: $(date)"
echo

# Check critical services
echo "Critical Services Status:"
echo "------------------------"

# ChromaDB
if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; then
  echo "✓ ChromaDB: RUNNING"
else
  echo "✗ ChromaDB: DOWN"
fi

# Docker
if docker ps > /dev/null 2>&1; then
  echo "✓ Docker: RUNNING"
else
  echo "✗ Docker: DOWN"
fi

# Disk space
echo
echo "Storage Status:"
echo "--------------"
df -h /opt/arxiv-system

# System resources
echo
echo "System Resources:"
echo "----------------"
echo "CPU Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"

# Recent errors
echo
echo "Recent Critical Errors:"
echo "----------------------"
find /opt/arxiv-system/logs -name "*.log" -mmin -60 -exec grep -i "critical\|fatal\|error" {} \; | tail -10

echo
echo "Assessment completed. Check output above for issues."
EOF

chmod +x /opt/arxiv-system/scripts/emergency_assessment.sh
```

#### 2. Data Corruption Recovery

```bash
# Data corruption recovery script
cat > /opt/arxiv-system/scripts/recover_corruption.sh << 'EOF'
#!/bin/bash

echo "DATA CORRUPTION RECOVERY PROCEDURE"
echo "================================="

CORRUPTION_TYPE="$1"

case "$CORRUPTION_TYPE" in
  "chromadb")
    echo "Recovering from ChromaDB corruption..."
    
    # Find latest ChromaDB backup
    LATEST_BACKUP=$(ls -t /opt/arxiv-system/backups/chromadb/chromadb_backup_*.tar.gz | head -1)
    
    if [ -n "$LATEST_BACKUP" ]; then
      echo "Found backup: $LATEST_BACKUP"
      /opt/arxiv-system/scripts/restore_chromadb.sh "$LATEST_BACKUP"
    else
      echo "ERROR: No ChromaDB backup found"
      exit 1
    fi
    ;;
    
  "config")
    echo "Recovering from configuration corruption..."
    
    # Find latest config backup
    LATEST_BACKUP=$(ls -t /opt/arxiv-system/backups/configs/configs_backup_*.tar.gz | head -1)
    
    if [ -n "$LATEST_BACKUP" ]; then
      echo "Found backup: $LATEST_BACKUP"
      /opt/arxiv-system/scripts/restore_configs.sh "$LATEST_BACKUP"
    else
      echo "ERROR: No configuration backup found"
      exit 1
    fi
    ;;
    
  "data")
    echo "Recovering from data corruption..."
    echo "Available instance backups:"
    ls -la /opt/arxiv-system/backups/data/
    
    echo "Please run data recovery manually for specific instances:"
    echo "/opt/arxiv-system/scripts/restore_data.sh <backup_file> <instance>"
    ;;
    
  *)
    echo "Usage: $0 <corruption_type>"
    echo "Types: chromadb, config, data"
    exit 1
    ;;
esac
EOF

chmod +x /opt/arxiv-system/scripts/recover_corruption.sh
```

## Automated Backup Scheduling

### Setup Automated Backups

```bash
# Create backup scheduler script
cat > /opt/arxiv-system/scripts/schedule_backups.sh << 'EOF'
#!/bin/bash

echo "Setting up automated backup schedule..."

# Add backup jobs to crontab
(crontab -l 2>/dev/null; cat << 'CRON_JOBS'
# Multi-Instance ArXiv System Backup Schedule

# Daily ChromaDB backup (2 AM)
0 2 * * * /opt/arxiv-system/scripts/backup_chromadb.sh

# Daily configuration backup (2:30 AM)
30 2 * * * /opt/arxiv-system/scripts/backup_configs.sh

# Weekly data backup (Sunday 3 AM)
0 3 * * 0 /opt/arxiv-system/scripts/backup_data.sh all

# Monthly full system backup (1st of month, 4 AM)
0 4 1 * * /opt/arxiv-system/scripts/backup_full_system.sh

CRON_JOBS
) | crontab -

echo "Backup schedule configured:"
echo "- Daily ChromaDB backup: 2:00 AM"
echo "- Daily configuration backup: 2:30 AM"
echo "- Weekly data backup: Sunday 3:00 AM"
echo "- Monthly full backup: 1st of month 4:00 AM"

# Create backup monitoring script
cat > /opt/arxiv-system/scripts/monitor_backups.sh << 'MONITOR_EOF'
#!/bin/bash

# Check if backups are running successfully
BACKUP_LOG="/opt/arxiv-system/logs/backup.log"

if [ ! -f "$BACKUP_LOG" ]; then
  echo "WARNING: Backup log not found"
  exit 1
fi

# Check for recent backup activity (last 25 hours)
RECENT_BACKUPS=$(grep "$(date -d '25 hours ago' '+%Y-%m-%d')" "$BACKUP_LOG" | wc -l)

if [ $RECENT_BACKUPS -eq 0 ]; then
  echo "ALERT: No backup activity in the last 25 hours"
  # Send alert email
  echo "No backup activity detected in the last 25 hours. Please check the backup system." | \
  mail -s "Backup System Alert" admin@yourorg.com
else
  echo "Backup system is active ($RECENT_BACKUPS recent entries)"
fi

# Check for backup failures
RECENT_FAILURES=$(grep -i "failed\|error" "$BACKUP_LOG" | grep "$(date '+%Y-%m-%d')" | wc -l)

if [ $RECENT_FAILURES -gt 0 ]; then
  echo "ALERT: $RECENT_FAILURES backup failures detected today"
  # Send alert email
  grep -i "failed\|error" "$BACKUP_LOG" | grep "$(date '+%Y-%m-%d')" | \
  mail -s "Backup Failure Alert" admin@yourorg.com
fi
MONITOR_EOF

chmod +x /opt/arxiv-system/scripts/monitor_backups.sh

# Add backup monitoring to crontab (check every 6 hours)
(crontab -l 2>/dev/null; echo "0 */6 * * * /opt/arxiv-system/scripts/monitor_backups.sh") | crontab -

echo "Backup monitoring configured"
echo "Setup completed successfully!"
EOF

chmod +x /opt/arxiv-system/scripts/schedule_backups.sh
```

## Testing and Validation

### Backup Testing Procedures

```bash
# Create backup testing script
cat > /opt/arxiv-system/scripts/test_backups.sh << 'EOF'
#!/bin/bash

echo "BACKUP SYSTEM TESTING"
echo "===================="

# Test ChromaDB backup
echo "1. Testing ChromaDB backup..."
/opt/arxiv-system/scripts/backup_chromadb.sh
if [ $? -eq 0 ]; then
  echo "✓ ChromaDB backup test passed"
else
  echo "✗ ChromaDB backup test failed"
fi

# Test configuration backup
echo "2. Testing configuration backup..."
/opt/arxiv-system/scripts/backup_configs.sh
if [ $? -eq 0 ]; then
  echo "✓ Configuration backup test passed"
else
  echo "✗ Configuration backup test failed"
fi

# Test data backup (small test)
echo "3. Testing data backup..."
/opt/arxiv-system/scripts/backup_data.sh ai_scholar
if [ $? -eq 0 ]; then
  echo "✓ Data backup test passed"
else
  echo "✗ Data backup test failed"
fi

echo
echo "Backup testing completed"
echo "Check /opt/arxiv-system/logs/backup.log for details"
EOF

chmod +x /opt/arxiv-system/scripts/test_backups.sh
```

## Recovery Testing

### Recovery Validation Procedures

```bash
# Create recovery testing script
cat > /opt/arxiv-system/scripts/test_recovery.sh << 'EOF'
#!/bin/bash

echo "RECOVERY SYSTEM TESTING"
echo "======================"
echo "WARNING: This will test recovery procedures"
echo "Only run this on a test system or during maintenance"
echo

read -p "Continue with recovery testing? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Recovery testing cancelled"
  exit 0
fi

# Find latest backups for testing
CHROMADB_BACKUP=$(ls -t /opt/arxiv-system/backups/chromadb/chromadb_backup_*.tar.gz | head -1)
CONFIG_BACKUP=$(ls -t /opt/arxiv-system/backups/configs/configs_backup_*.tar.gz | head -1)

echo "Testing recovery procedures..."

# Test ChromaDB recovery
if [ -n "$CHROMADB_BACKUP" ]; then
  echo "1. Testing ChromaDB recovery..."
  /opt/arxiv-system/scripts/restore_chromadb.sh "$CHROMADB_BACKUP"
  if [ $? -eq 0 ]; then
    echo "✓ ChromaDB recovery test passed"
  else
    echo "✗ ChromaDB recovery test failed"
  fi
else
  echo "✗ No ChromaDB backup found for testing"
fi

# Test configuration recovery
if [ -n "$CONFIG_BACKUP" ]; then
  echo "2. Testing configuration recovery..."
  /opt/arxiv-system/scripts/restore_configs.sh "$CONFIG_BACKUP"
  if [ $? -eq 0 ]; then
    echo "✓ Configuration recovery test passed"
  else
    echo "✗ Configuration recovery test failed"
  fi
else
  echo "✗ No configuration backup found for testing"
fi

echo
echo "Recovery testing completed"
echo "System should be verified manually after testing"
EOF

chmod +x /opt/arxiv-system/scripts/test_recovery.sh
```

## Maintenance and Best Practices

### Regular Maintenance Tasks

1. **Weekly Tasks**
   - Verify backup completion and integrity
   - Check storage usage and cleanup old backups
   - Test recovery procedures on non-critical data
   - Review backup logs for errors or warnings

2. **Monthly Tasks**
   - Perform full system backup verification
   - Test complete recovery procedure in staging environment
   - Review and update backup retention policies
   - Update disaster recovery documentation

3. **Quarterly Tasks**
   - Conduct disaster recovery drill
   - Review and update recovery procedures
   - Validate backup storage capacity planning
   - Update emergency contact information

### Best Practices

1. **Backup Strategy**
   - Follow 3-2-1 rule: 3 copies, 2 different media, 1 offsite
   - Test backups regularly to ensure they're recoverable
   - Document all backup and recovery procedures
   - Monitor backup completion and alert on failures

2. **Security**
   - Encrypt sensitive backup data
   - Secure backup storage locations
   - Limit access to backup and recovery scripts
   - Regularly audit backup access logs

3. **Documentation**
   - Keep recovery procedures up to date
   - Document all configuration changes
   - Maintain emergency contact information
   - Record lessons learned from recovery events

---

This completes the comprehensive backup and recovery procedures documentation. The system now has robust backup automation, recovery procedures, and disaster recovery planning to ensure data protection and business continuity.