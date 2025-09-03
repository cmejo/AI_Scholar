#!/bin/bash

# Deployment Configuration Validation Script
# Validates all deployment configurations and prerequisites

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-production}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Validation results
VALIDATION_ERRORS=0
VALIDATION_WARNINGS=0

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
}

# Validate environment files
validate_environment_files() {
    log "Validating environment configuration files..."
    
    local env_files=(
        ".env.${ENVIRONMENT}"
        "config/deployment/${ENVIRONMENT}.env"
        "config/zotero_config.${ENVIRONMENT}.json"
    )
    
    for env_file in "${env_files[@]}"; do
        local file_path="${PROJECT_ROOT}/${env_file}"
        
        if [[ -f "$file_path" ]]; then
            success "✓ Found: $env_file"
            
            # Check file permissions
            local perms=$(stat -c "%a" "$file_path" 2>/dev/null || stat -f "%A" "$file_path" 2>/dev/null)
            if [[ "$perms" -le 600 ]]; then
                success "✓ Secure permissions: $env_file ($perms)"
            else
                warning "⚠ Insecure permissions: $env_file ($perms) - should be 600"
            fi
        else
            error "✗ Missing: $env_file"
        fi
    done
}

# Validate required environment variables
validate_environment_variables() {
    log "Validating required environment variables..."
    
    # Load environment
    local env_file="${PROJECT_ROOT}/.env.${ENVIRONMENT}"
    if [[ -f "$env_file" ]]; then
        source "$env_file"
    fi
    
    local deploy_env_file="${PROJECT_ROOT}/config/deployment/${ENVIRONMENT}.env"
    if [[ -f "$deploy_env_file" ]]; then
        source "$deploy_env_file"
    fi
    
    # Required variables by category
    local database_vars=(
        "DB_HOST" "DB_PORT" "DB_NAME" "DB_USER" "DB_PASSWORD"
    )
    
    local redis_vars=(
        "REDIS_URL"
    )
    
    local zotero_vars=(
        "ZOTERO_CLIENT_ID" "ZOTERO_CLIENT_SECRET" "ZOTERO_REDIRECT_URI"
        "ZOTERO_ENCRYPTION_KEY" "ZOTERO_WEBHOOK_SECRET"
    )
    
    local security_vars=(
        "SECRET_KEY" "JWT_SECRET"
    )
    
    # Validate database variables
    log "Checking database configuration..."
    for var in "${database_vars[@]}"; do
        if [[ -n "${!var:-}" ]]; then
            success "✓ $var is set"
        else
            error "✗ $var is not set"
        fi
    done
    
    # Validate Redis variables
    log "Checking Redis configuration..."
    for var in "${redis_vars[@]}"; do
        if [[ -n "${!var:-}" ]]; then
            success "✓ $var is set"
        else
            error "✗ $var is not set"
        fi
    done
    
    # Validate Zotero variables
    log "Checking Zotero configuration..."
    for var in "${zotero_vars[@]}"; do
        if [[ -n "${!var:-}" ]]; then
            success "✓ $var is set"
            
            # Validate key lengths
            case "$var" in
                "ZOTERO_ENCRYPTION_KEY")
                    if [[ ${#!var} -ge 32 ]]; then
                        success "✓ $var has adequate length"
                    else
                        error "✗ $var is too short (minimum 32 characters)"
                    fi
                    ;;
                "ZOTERO_WEBHOOK_SECRET")
                    if [[ ${#!var} -ge 16 ]]; then
                        success "✓ $var has adequate length"
                    else
                        warning "⚠ $var is short (recommended 16+ characters)"
                    fi
                    ;;
            esac
        else
            error "✗ $var is not set"
        fi
    done
    
    # Validate security variables
    log "Checking security configuration..."
    for var in "${security_vars[@]}"; do
        if [[ -n "${!var:-}" ]]; then
            success "✓ $var is set"
            
            if [[ ${#!var} -ge 32 ]]; then
                success "✓ $var has adequate length"
            else
                warning "⚠ $var is short (recommended 32+ characters)"
            fi
        else
            error "✗ $var is not set"
        fi
    done
}

# Validate Docker configuration
validate_docker_config() {
    log "Validating Docker configuration..."
    
    local docker_files=(
        "docker-compose.yml"
        "docker-compose.${ENVIRONMENT}.yml"
        "Dockerfile.backend"
        "Dockerfile.frontend"
    )
    
    for docker_file in "${docker_files[@]}"; do
        local file_path="${PROJECT_ROOT}/${docker_file}"
        
        if [[ -f "$file_path" ]]; then
            success "✓ Found: $docker_file"
            
            # Validate Docker Compose syntax
            if [[ "$docker_file" == docker-compose*.yml ]]; then
                if docker-compose -f "$file_path" config &> /dev/null; then
                    success "✓ Valid syntax: $docker_file"
                else
                    error "✗ Invalid syntax: $docker_file"
                fi
            fi
        else
            if [[ "$docker_file" == "docker-compose.${ENVIRONMENT}.yml" ]]; then
                warning "⚠ Missing: $docker_file (environment-specific)"
            else
                error "✗ Missing: $docker_file"
            fi
        fi
    done
    
    # Check if Docker is available
    if command -v docker &> /dev/null; then
        success "✓ Docker is available"
        
        # Check Docker daemon
        if docker info &> /dev/null; then
            success "✓ Docker daemon is running"
        else
            error "✗ Docker daemon is not running"
        fi
    else
        error "✗ Docker is not installed"
    fi
    
    # Check if Docker Compose is available
    if command -v docker-compose &> /dev/null; then
        success "✓ Docker Compose is available"
    else
        error "✗ Docker Compose is not installed"
    fi
}

# Validate database migration files
validate_migration_files() {
    log "Validating database migration files..."
    
    local migration_dir="${PROJECT_ROOT}/backend/migrations"
    
    if [[ -d "$migration_dir" ]]; then
        success "✓ Migration directory exists"
        
        local migration_files=(
            "001_zotero_integration_foundation.sql"
            "002_zotero_auth_tables.sql"
            "003_zotero_sync_tables.sql"
            "004_zotero_reference_tables.sql"
            "005_citation_management_tables.sql"
            "006_zotero_export_sharing_tables.sql"
            "007_zotero_annotation_sync_tables.sql"
            "upgrade_zotero_schema.py"
        )
        
        for migration_file in "${migration_files[@]}"; do
            local file_path="${migration_dir}/${migration_file}"
            
            if [[ -f "$file_path" ]]; then
                success "✓ Found: $migration_file"
                
                # Validate SQL syntax for .sql files
                if [[ "$migration_file" == *.sql ]]; then
                    if grep -q "CREATE\|ALTER\|INSERT" "$file_path"; then
                        success "✓ Contains SQL statements: $migration_file"
                    else
                        warning "⚠ No SQL statements found: $migration_file"
                    fi
                fi
            else
                error "✗ Missing: $migration_file"
            fi
        done
    else
        error "✗ Migration directory not found: $migration_dir"
    fi
}

# Validate monitoring configuration
validate_monitoring_config() {
    log "Validating monitoring configuration..."
    
    local monitoring_files=(
        "monitoring/prometheus.yml"
        "monitoring/zotero_monitoring.yml"
        "monitoring/alertmanager.yml"
        "monitoring/grafana/dashboards/zotero-dashboard.json"
    )
    
    for monitoring_file in "${monitoring_files[@]}"; do
        local file_path="${PROJECT_ROOT}/${monitoring_file}"
        
        if [[ -f "$file_path" ]]; then
            success "✓ Found: $monitoring_file"
            
            # Validate YAML syntax
            if [[ "$monitoring_file" == *.yml ]] || [[ "$monitoring_file" == *.yaml ]]; then
                if python3 -c "import yaml; yaml.safe_load(open('$file_path'))" &> /dev/null; then
                    success "✓ Valid YAML: $monitoring_file"
                else
                    error "✗ Invalid YAML: $monitoring_file"
                fi
            fi
            
            # Validate JSON syntax
            if [[ "$monitoring_file" == *.json ]]; then
                if python3 -c "import json; json.load(open('$file_path'))" &> /dev/null; then
                    success "✓ Valid JSON: $monitoring_file"
                else
                    error "✗ Invalid JSON: $monitoring_file"
                fi
            fi
        else
            warning "⚠ Missing: $monitoring_file"
        fi
    done
}

# Validate SSL certificates (production only)
validate_ssl_certificates() {
    if [[ "$ENVIRONMENT" != "production" ]]; then
        return 0
    fi
    
    log "Validating SSL certificates..."
    
    local cert_file="${SSL_CERT_PATH:-/etc/ssl/certs/aischolar.crt}"
    local key_file="${SSL_KEY_PATH:-/etc/ssl/private/aischolar.key}"
    
    if [[ -f "$cert_file" ]]; then
        success "✓ Certificate file exists: $cert_file"
        
        # Check certificate validity
        local expiry_date=$(openssl x509 -enddate -noout -in "$cert_file" 2>/dev/null | cut -d= -f2)
        if [[ -n "$expiry_date" ]]; then
            local expiry_timestamp=$(date -d "$expiry_date" +%s 2>/dev/null || echo 0)
            local current_timestamp=$(date +%s)
            local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
            
            if [[ $days_until_expiry -gt 30 ]]; then
                success "✓ Certificate valid for $days_until_expiry days"
            elif [[ $days_until_expiry -gt 7 ]]; then
                warning "⚠ Certificate expires in $days_until_expiry days"
            else
                error "✗ Certificate expires in $days_until_expiry days"
            fi
        else
            error "✗ Cannot read certificate expiry date"
        fi
    else
        error "✗ Certificate file not found: $cert_file"
    fi
    
    if [[ -f "$key_file" ]]; then
        success "✓ Private key file exists: $key_file"
        
        # Check key permissions
        local perms=$(stat -c "%a" "$key_file" 2>/dev/null || stat -f "%A" "$key_file" 2>/dev/null)
        if [[ "$perms" -eq 600 ]]; then
            success "✓ Secure key permissions: $key_file"
        else
            error "✗ Insecure key permissions: $key_file ($perms) - should be 600"
        fi
    else
        error "✗ Private key file not found: $key_file"
    fi
}

# Validate deployment scripts
validate_deployment_scripts() {
    log "Validating deployment scripts..."
    
    local scripts=(
        "scripts/deploy-zotero-integration.sh"
        "scripts/deploy-zotero-production.sh"
        "scripts/database-migration.sh"
        "scripts/health-check.sh"
    )
    
    for script in "${scripts[@]}"; do
        local script_path="${PROJECT_ROOT}/${script}"
        
        if [[ -f "$script_path" ]]; then
            success "✓ Found: $script"
            
            # Check if executable
            if [[ -x "$script_path" ]]; then
                success "✓ Executable: $script"
            else
                warning "⚠ Not executable: $script"
            fi
            
            # Basic syntax check
            if bash -n "$script_path" &> /dev/null; then
                success "✓ Valid syntax: $script"
            else
                error "✗ Invalid syntax: $script"
            fi
        else
            error "✗ Missing: $script"
        fi
    done
}

# Validate system requirements
validate_system_requirements() {
    log "Validating system requirements..."
    
    # Check required commands
    local required_commands=(
        "python3" "pip3" "node" "npm"
        "psql" "pg_dump" "pg_restore"
        "redis-cli" "curl" "git"
    )
    
    for cmd in "${required_commands[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            success "✓ Command available: $cmd"
        else
            error "✗ Command not found: $cmd"
        fi
    done
    
    # Check Python packages
    local python_packages=(
        "psycopg2" "redis" "requests" "fastapi"
    )
    
    for package in "${python_packages[@]}"; do
        if python3 -c "import $package" &> /dev/null; then
            success "✓ Python package available: $package"
        else
            error "✗ Python package not found: $package"
        fi
    done
    
    # Check system resources
    local available_memory=$(free -m | awk 'NR==2{print $7}')
    if [[ $available_memory -gt 2048 ]]; then
        success "✓ Adequate memory: ${available_memory}MB available"
    elif [[ $available_memory -gt 1024 ]]; then
        warning "⚠ Low memory: ${available_memory}MB available"
    else
        error "✗ Insufficient memory: ${available_memory}MB available"
    fi
    
    local available_space=$(df "${PROJECT_ROOT}" | awk 'NR==2 {print $4}')
    local available_gb=$((available_space / 1024 / 1024))
    if [[ $available_gb -gt 10 ]]; then
        success "✓ Adequate disk space: ${available_gb}GB available"
    elif [[ $available_gb -gt 5 ]]; then
        warning "⚠ Low disk space: ${available_gb}GB available"
    else
        error "✗ Insufficient disk space: ${available_gb}GB available"
    fi
}

# Generate validation report
generate_validation_report() {
    log "Generating validation report..."
    
    local report_file="${PROJECT_ROOT}/logs/deployment_validation_$(date +%Y%m%d_%H%M%S).json"
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    mkdir -p "$(dirname "$report_file")"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$timestamp",
    "environment": "$ENVIRONMENT",
    "validation_summary": {
        "errors": $VALIDATION_ERRORS,
        "warnings": $VALIDATION_WARNINGS,
        "status": "$([ $VALIDATION_ERRORS -eq 0 ] && echo "PASS" || echo "FAIL")"
    },
    "git_info": {
        "commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
        "branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
        "dirty": $([ -n "$(git status --porcelain 2>/dev/null)" ] && echo "true" || echo "false")
    }
}
EOF
    
    log "Validation report saved to: $report_file"
}

# Main validation function
main() {
    log "Starting deployment configuration validation for environment: $ENVIRONMENT"
    
    validate_environment_files
    validate_environment_variables
    validate_docker_config
    validate_migration_files
    validate_monitoring_config
    validate_ssl_certificates
    validate_deployment_scripts
    validate_system_requirements
    
    generate_validation_report
    
    # Summary
    echo
    log "Validation Summary:"
    log "Errors: $VALIDATION_ERRORS"
    log "Warnings: $VALIDATION_WARNINGS"
    
    if [[ $VALIDATION_ERRORS -eq 0 ]]; then
        success "✓ All validations passed! Deployment configuration is ready."
        exit 0
    else
        error "✗ $VALIDATION_ERRORS validation errors found. Please fix before deployment."
        exit 1
    fi
}

# Script usage
usage() {
    echo "Usage: $0 [environment]"
    echo "  environment: production, staging, development (default: production)"
    echo ""
    echo "Examples:"
    echo "  $0 production"
    echo "  $0 staging"
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