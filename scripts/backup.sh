#!/bin/bash

# Advanced RAG Research Ecosystem - Backup Script
# Automated backup for database, files, and configuration

set -e

# Configuration
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Load environment variables
if [ -f ".env.production" ]; then
    source .env.production
else
    print_error "Environment file not found"
    exit 1
fi

# Database backup
backup_database() {
    print_status "Backing up PostgreSQL database..."
    
    docker-compose exec -T postgres pg_dump \
        -U rag_user \
        -d advanced_rag_db \
        --no-password \
        --verbose \
        --clean \
        --if-exists \
        --create > "$BACKUP_DIR/database_$DATE.sql"
    
    # Compress the backup
    gzip "$BACKUP_DIR/database_$DATE.sql"
    
    print_success "Database backup completed: database_$DATE.sql.gz"
}

# Redis backup
backup_redis() {
    print_status "Backing up Redis data..."
    
    # Create Redis backup
    docker-compose exec -T redis redis-cli --rdb - > "$BACKUP_DIR/redis_$DATE.rdb"
    
    # Compress the backup
    gzip "$BACKUP_DIR/redis_$DATE.rdb"
    
    print_success "Redis backup completed: redis_$DATE.rdb.gz"
}

# File uploads backup
backup_files() {
    print_status "Backing up uploaded files..."
    
    if [ -d "uploads" ]; then
        tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" uploads/
        print_success "Files backup completed: uploads_$DATE.tar.gz"
    else
        print_warning "No uploads directory found"
    fi
}

# Configuration backup
backup_config() {
    print_status "Backing up configuration..."
    
    # Create config backup directory
    mkdir -p "$BACKUP_DIR/config_$DATE"
    
    # Copy important configuration files
    cp .env.production "$BACKUP_DIR/config_$DATE/"
    cp docker-compose.yml "$BACKUP_DIR/config_$DATE/"
    cp -r nginx/ "$BACKUP_DIR/config_$DATE/" 2>/dev/null || true
    cp -r monitoring/ "$BACKUP_DIR/config_$DATE/" 2>/dev/null || true
    
    # Compress configuration backup
    tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" -C "$BACKUP_DIR" "config_$DATE"
    rm -rf "$BACKUP_DIR/config_$DATE"
    
    print_success "Configuration backup completed: config_$DATE.tar.gz"
}

# Vector database backup
backup_vector_db() {
    print_status "Backing up vector database..."
    
    # ChromaDB backup
    if docker-compose ps chromadb | grep -q "Up"; then
        docker-compose exec -T chromadb tar -czf - /chroma > "$BACKUP_DIR/chromadb_$DATE.tar.gz"
        print_success "Vector database backup completed: chromadb_$DATE.tar.gz"
    else
        print_warning "ChromaDB service not running, skipping backup"
    fi
}

# Clean old backups
cleanup_old_backups() {
    print_status "Cleaning up old backups (older than $RETENTION_DAYS days)..."
    
    find "$BACKUP_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.sql" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.rdb" -mtime +$RETENTION_DAYS -delete
    
    print_success "Old backups cleaned up"
}

# Upload to cloud storage (if configured)
upload_to_cloud() {
    if [ -n "$S3_BACKUP_BUCKET" ] && [ -n "$AWS_ACCESS_KEY_ID" ]; then
        print_status "Uploading backups to S3..."
        
        # Upload recent backups to S3
        aws s3 sync "$BACKUP_DIR" "s3://$S3_BACKUP_BUCKET/backups/" \
            --exclude "*" \
            --include "*$DATE*" \
            --storage-class STANDARD_IA
        
        print_success "Backups uploaded to S3"
    else
        print_warning "S3 backup not configured, skipping cloud upload"
    fi
}

# Verify backups
verify_backups() {
    print_status "Verifying backups..."
    
    # Check if backup files exist and are not empty
    backups=(
        "database_$DATE.sql.gz"
        "redis_$DATE.rdb.gz"
        "uploads_$DATE.tar.gz"
        "config_$DATE.tar.gz"
        "chromadb_$DATE.tar.gz"
    )
    
    for backup in "${backups[@]}"; do
        if [ -f "$BACKUP_DIR/$backup" ] && [ -s "$BACKUP_DIR/$backup" ]; then
            size=$(du -h "$BACKUP_DIR/$backup" | cut -f1)
            print_success "$backup verified (size: $size)"
        else
            print_warning "$backup not found or empty"
        fi
    done
}

# Generate backup report
generate_report() {
    print_status "Generating backup report..."
    
    report_file="$BACKUP_DIR/backup_report_$DATE.txt"
    
    cat > "$report_file" << EOF
Advanced RAG Research Ecosystem - Backup Report
===============================================
Date: $(date)
Backup ID: $DATE

Backup Files:
$(ls -lh "$BACKUP_DIR"/*$DATE* 2>/dev/null || echo "No backup files found")

System Information:
- Docker Version: $(docker --version)
- Docker Compose Version: $(docker-compose --version)
- Disk Usage: $(df -h .)

Service Status:
$(docker-compose ps)

Environment:
- Database: PostgreSQL
- Cache: Redis
- Vector DB: ChromaDB
- Backup Location: $BACKUP_DIR
- Retention: $RETENTION_DAYS days

Notes:
- All backups are compressed with gzip
- Configuration files are included
- Vector database backup included if service is running
EOF

    print_success "Backup report generated: $report_file"
}

# Main backup function
main() {
    echo ""
    echo "🔄 Advanced RAG Research Ecosystem - Backup"
    echo "==========================================="
    echo "Backup ID: $DATE"
    echo ""
    
    # Check if services are running
    if ! docker-compose ps | grep -q "Up"; then
        print_warning "Some services may not be running. Backup may be incomplete."
        read -p "Continue anyway? (y/n): " continue_backup
        if [[ $continue_backup != [yY] ]]; then
            print_error "Backup cancelled"
            exit 1
        fi
    fi
    
    # Perform backups
    backup_database
    backup_redis
    backup_files
    backup_config
    backup_vector_db
    
    # Verify and report
    verify_backups
    generate_report
    
    # Cleanup and upload
    cleanup_old_backups
    upload_to_cloud
    
    echo ""
    print_success "🎉 Backup completed successfully!"
    echo ""
    echo "📊 Backup Summary:"
    echo "=================="
    ls -lh "$BACKUP_DIR"/*$DATE* 2>/dev/null || echo "No backup files found"
    echo ""
    echo "📝 Next Steps:"
    echo "1. Verify backup integrity"
    echo "2. Test restore procedure"
    echo "3. Update backup documentation"
    echo ""
}

# Parse command line arguments
case "${1:-backup}" in
    "backup")
        main
        ;;
    "restore")
        if [ -z "$2" ]; then
            print_error "Please specify backup date (YYYYMMDD_HHMMSS)"
            echo "Available backups:"
            ls -1 "$BACKUP_DIR"/database_*.sql.gz 2>/dev/null | sed 's/.*database_\(.*\)\.sql\.gz/\1/' || echo "No backups found"
            exit 1
        fi
        
        RESTORE_DATE="$2"
        print_status "Restoring from backup: $RESTORE_DATE"
        
        # Restore database
        if [ -f "$BACKUP_DIR/database_$RESTORE_DATE.sql.gz" ]; then
            print_status "Restoring database..."
            gunzip -c "$BACKUP_DIR/database_$RESTORE_DATE.sql.gz" | \
                docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db
            print_success "Database restored"
        fi
        
        # Restore files
        if [ -f "$BACKUP_DIR/uploads_$RESTORE_DATE.tar.gz" ]; then
            print_status "Restoring files..."
            tar -xzf "$BACKUP_DIR/uploads_$RESTORE_DATE.tar.gz"
            print_success "Files restored"
        fi
        
        print_success "Restore completed"
        ;;
    "list")
        echo "Available backups:"
        ls -1 "$BACKUP_DIR"/database_*.sql.gz 2>/dev/null | sed 's/.*database_\(.*\)\.sql\.gz/\1/' || echo "No backups found"
        ;;
    "clean")
        print_status "Cleaning old backups..."
        cleanup_old_backups
        ;;
    *)
        echo "Usage: $0 {backup|restore|list|clean}"
        echo ""
        echo "Commands:"
        echo "  backup           - Create full backup (default)"
        echo "  restore <date>   - Restore from backup"
        echo "  list             - List available backups"
        echo "  clean            - Clean old backups"
        exit 1
        ;;
esac