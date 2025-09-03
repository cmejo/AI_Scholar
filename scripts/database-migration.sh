#!/bin/bash

# Database Migration Script for Zotero Integration
# Handles database schema upgrades with safety checks and rollback capabilities

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-production}"
TARGET_VERSION="${2:-latest}"
BACKUP_DIR="${PROJECT_ROOT}/backups/migration_$(date +%Y%m%d_%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Load environment configuration
load_environment() {
    local env_file="${PROJECT_ROOT}/.env.${ENVIRONMENT}"
    
    if [[ ! -f "$env_file" ]]; then
        error "Environment file not found: $env_file"
        exit 1
    fi
    
    source "$env_file"
    
    # Load deployment-specific configuration
    local deploy_env_file="${PROJECT_ROOT}/config/deployment/${ENVIRONMENT}.env"
    if [[ -f "$deploy_env_file" ]]; then
        source "$deploy_env_file"
    fi
    
    log "Loaded configuration for environment: $ENVIRONMENT"
}

# Check database connectivity
check_database_connectivity() {
    log "Checking database connectivity..."
    
    if ! pg_isready -h "${DB_HOST}" -p "${DB_PORT:-5432}" -U "${DB_USER}" &> /dev/null; then
        error "Cannot connect to database at ${DB_HOST}:${DB_PORT:-5432}"
        exit 1
    fi
    
    # Test actual connection with credentials
    if ! PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT:-5432}" -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT 1;" &> /dev/null; then
        error "Database authentication failed"
        exit 1
    fi
    
    success "Database connectivity verified"
}

# Create comprehensive backup
create_backup() {
    log "Creating comprehensive database backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Full database backup
    log "Creating full database backup..."
    PGPASSWORD="${DB_PASSWORD}" pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT:-5432}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --verbose \
        --no-owner \
        --no-privileges \
        --format=custom \
        --file="${BACKUP_DIR}/full_backup.dump"
    
    # Schema-only backup
    log "Creating schema-only backup..."
    PGPASSWORD="${DB_PASSWORD}" pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT:-5432}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --schema-only \
        --verbose \
        --no-owner \
        --no-privileges \
        --file="${BACKUP_DIR}/schema_backup.sql"
    
    # Zotero-specific data backup
    log "Creating Zotero-specific data backup..."
    PGPASSWORD="${DB_PASSWORD}" pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT:-5432}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --data-only \
        --schema=zotero \
        --verbose \
        --no-owner \
        --no-privileges \
        --file="${BACKUP_DIR}/zotero_data_backup.sql"
    
    # Create backup metadata
    cat > "${BACKUP_DIR}/backup_info.json" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "environment": "${ENVIRONMENT}",
    "database_host": "${DB_HOST}",
    "database_name": "${DB_NAME}",
    "backup_type": "pre_migration",
    "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "migration_target": "${TARGET_VERSION}"
}
EOF
    
    # Verify backup integrity
    if [[ ! -s "${BACKUP_DIR}/full_backup.dump" ]]; then
        error "Backup verification failed - backup file is empty or missing"
        exit 1
    fi
    
    success "Backup created successfully at: $BACKUP_DIR"
}

# Check migration prerequisites
check_migration_prerequisites() {
    log "Checking migration prerequisites..."
    
    # Check Python environment
    if ! python3 -c "import psycopg2" &> /dev/null; then
        error "psycopg2 Python package not found. Please install it."
        exit 1
    fi
    
    # Check migration script
    local migration_script="${PROJECT_ROOT}/backend/migrations/upgrade_zotero_schema.py"
    if [[ ! -f "$migration_script" ]]; then
        error "Migration script not found: $migration_script"
        exit 1
    fi
    
    # Check configuration file
    local config_file="${PROJECT_ROOT}/config/zotero_config.${ENVIRONMENT}.json"
    if [[ ! -f "$config_file" ]]; then
        error "Configuration file not found: $config_file"
        exit 1
    fi
    
    # Check disk space (require at least 1GB free)
    local available_space=$(df "${PROJECT_ROOT}" | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 1048576 ]]; then  # 1GB in KB
        error "Insufficient disk space. At least 1GB required for migration."
        exit 1
    fi
    
    success "Migration prerequisites verified"
}

# Run migration with monitoring
run_migration() {
    log "Starting database migration to version: $TARGET_VERSION"
    
    local config_file="${PROJECT_ROOT}/config/zotero_config.${ENVIRONMENT}.json"
    local migration_script="${PROJECT_ROOT}/backend/migrations/upgrade_zotero_schema.py"
    
    # Set up migration monitoring
    local migration_log="${BACKUP_DIR}/migration.log"
    local migration_pid_file="${BACKUP_DIR}/migration.pid"
    
    # Start migration in background with logging
    (
        cd "$PROJECT_ROOT"
        python3 "$migration_script" upgrade \
            --environment "$ENVIRONMENT" \
            --config "$config_file" \
            --target-version "$TARGET_VERSION" 2>&1
    ) | tee "$migration_log" &
    
    local migration_pid=$!
    echo $migration_pid > "$migration_pid_file"
    
    # Monitor migration progress
    local timeout=1800  # 30 minutes timeout
    local elapsed=0
    local check_interval=10
    
    while kill -0 $migration_pid 2>/dev/null; do
        if [[ $elapsed -ge $timeout ]]; then
            error "Migration timeout after ${timeout} seconds"
            kill $migration_pid 2>/dev/null || true
            return 1
        fi
        
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
        
        # Show progress every minute
        if [[ $((elapsed % 60)) -eq 0 ]]; then
            log "Migration in progress... (${elapsed}s elapsed)"
        fi
    done
    
    # Check migration result
    wait $migration_pid
    local migration_result=$?
    
    if [[ $migration_result -eq 0 ]]; then
        success "Migration completed successfully"
        return 0
    else
        error "Migration failed with exit code: $migration_result"
        return 1
    fi
}

# Verify migration success
verify_migration() {
    log "Verifying migration success..."
    
    local config_file="${PROJECT_ROOT}/config/zotero_config.${ENVIRONMENT}.json"
    local migration_script="${PROJECT_ROOT}/backend/migrations/upgrade_zotero_schema.py"
    
    # Check migration status
    cd "$PROJECT_ROOT"
    local status_output=$(python3 "$migration_script" status \
        --environment "$ENVIRONMENT" \
        --config "$config_file" 2>&1)
    
    if echo "$status_output" | grep -q "up to date"; then
        success "Migration verification passed"
        return 0
    else
        error "Migration verification failed"
        echo "$status_output"
        return 1
    fi
}

# Test database functionality
test_database_functionality() {
    log "Testing database functionality..."
    
    # Test basic Zotero schema access
    local test_queries=(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'zotero';"
        "SELECT version FROM zotero.schema_version ORDER BY applied_at DESC LIMIT 1;"
        "SELECT COUNT(*) FROM zotero.zotero_connections;"
    )
    
    for query in "${test_queries[@]}"; do
        if ! PGPASSWORD="${DB_PASSWORD}" psql \
            -h "${DB_HOST}" \
            -p "${DB_PORT:-5432}" \
            -U "${DB_USER}" \
            -d "${DB_NAME}" \
            -c "$query" &> /dev/null; then
            error "Database functionality test failed: $query"
            return 1
        fi
    done
    
    success "Database functionality tests passed"
}

# Rollback migration
rollback_migration() {
    error "Migration failed. Initiating rollback..."
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        error "Backup directory not found: $BACKUP_DIR"
        exit 1
    fi
    
    local backup_file="${BACKUP_DIR}/full_backup.dump"
    if [[ ! -f "$backup_file" ]]; then
        error "Backup file not found: $backup_file"
        exit 1
    fi
    
    log "Restoring database from backup..."
    
    # Drop and recreate database
    PGPASSWORD="${DB_PASSWORD}" dropdb \
        -h "${DB_HOST}" \
        -p "${DB_PORT:-5432}" \
        -U "${DB_USER}" \
        "${DB_NAME}" || true
    
    PGPASSWORD="${DB_PASSWORD}" createdb \
        -h "${DB_HOST}" \
        -p "${DB_PORT:-5432}" \
        -U "${DB_USER}" \
        "${DB_NAME}"
    
    # Restore from backup
    PGPASSWORD="${DB_PASSWORD}" pg_restore \
        -h "${DB_HOST}" \
        -p "${DB_PORT:-5432}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --verbose \
        --no-owner \
        --no-privileges \
        "$backup_file"
    
    success "Database rollback completed"
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    local backup_parent_dir="${PROJECT_ROOT}/backups"
    if [[ ! -d "$backup_parent_dir" ]]; then
        return 0
    fi
    
    # Keep only last 10 migration backups
    find "$backup_parent_dir" -name "migration_*" -type d -mtime +7 | \
        sort | head -n -10 | xargs rm -rf
    
    success "Old backups cleaned up"
}

# Send notification
send_notification() {
    local status="$1"
    local message="$2"
    
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"Migration ${status}: ${message}\"}" \
            "${SLACK_WEBHOOK_URL}" &> /dev/null || true
    fi
    
    if command -v mail &> /dev/null && [[ -n "${ADMIN_EMAIL:-}" ]]; then
        echo "$message" | mail -s "Database Migration ${status}" "${ADMIN_EMAIL}" || true
    fi
}

# Main migration function
main() {
    log "Starting Zotero database migration for environment: $ENVIRONMENT"
    
    # Set up error handling
    trap 'rollback_migration; send_notification "FAILED" "Migration failed and was rolled back"' ERR
    
    load_environment
    check_database_connectivity
    check_migration_prerequisites
    create_backup
    
    if run_migration && verify_migration && test_database_functionality; then
        success "Migration completed successfully!"
        cleanup_old_backups
        send_notification "SUCCESS" "Migration completed successfully"
    else
        error "Migration failed"
        exit 1
    fi
}

# Script usage
usage() {
    echo "Usage: $0 [environment] [target_version]"
    echo "  environment: production, staging, development (default: production)"
    echo "  target_version: specific version or 'latest' (default: latest)"
    echo ""
    echo "Examples:"
    echo "  $0 production latest"
    echo "  $0 staging 005_citation_management_tables"
    echo "  $0 development"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
    production|staging|development|"")
        main
        ;;
    *)
        error "Invalid environment: $1"
        usage
        exit 1
        ;;
esac