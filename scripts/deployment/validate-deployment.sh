#!/bin/bash

# Deployment Validation Script for AI Scholar Advanced RAG
# Validates deployment infrastructure and configuration

set -e

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

# Configuration
DEPLOYMENT_DIR="/opt/ai-scholar"
SCRIPTS_DIR="$DEPLOYMENT_DIR/scripts/deployment"
CONFIG_DIR="$DEPLOYMENT_DIR/config"

# Validation results
VALIDATION_ERRORS=0
VALIDATION_WARNINGS=0

# Add validation error
add_error() {
    print_error "$1"
    VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
}

# Add validation warning
add_warning() {
    print_warning "$1"
    VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
}

# Validate required files exist
validate_files() {
    print_status "Validating required files..."
    
    local required_files=(
        "$SCRIPTS_DIR/deploy.sh"
        "$SCRIPTS_DIR/blue-green-deployment.sh"
        "$SCRIPTS_DIR/database-migration.sh"
        "$SCRIPTS_DIR/mobile-app-deployment.sh"
        "$SCRIPTS_DIR/health-check.sh"
        "$SCRIPTS_DIR/rollback.sh"
        "$SCRIPTS_DIR/switch-traffic.sh"
        "$SCRIPTS_DIR/deployment-monitoring.sh"
        "$SCRIPTS_DIR/feature-flag-management.sh"
        "$CONFIG_DIR/deployment-config.yml"
        "$CONFIG_DIR/docker-compose.blue.yml"
        "$CONFIG_DIR/docker-compose.green.yml"
        ".github/workflows/web-deployment.yml"
        ".github/workflows/mobile-deployment.yml"
        "android/fastlane/Fastfile"
        "ios/fastlane/Fastfile"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            add_error "Required file missing: $file"
        else
            print_success "Found: $file"
        fi
    done
}

# Validate script permissions
validate_permissions() {
    print_status "Validating script permissions..."
    
    local scripts=(
        "$SCRIPTS_DIR/deploy.sh"
        "$SCRIPTS_DIR/blue-green-deployment.sh"
        "$SCRIPTS_DIR/database-migration.sh"
        "$SCRIPTS_DIR/mobile-app-deployment.sh"
        "$SCRIPTS_DIR/health-check.sh"
        "$SCRIPTS_DIR/rollback.sh"
        "$SCRIPTS_DIR/switch-traffic.sh"
        "$SCRIPTS_DIR/deployment-monitoring.sh"
        "$SCRIPTS_DIR/feature-flag-management.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ -f "$script" ]; then
            if [ ! -x "$script" ]; then
                add_error "Script not executable: $script"
            else
                print_success "Executable: $script"
            fi
        fi
    done
}

# Validate Docker setup
validate_docker() {
    print_status "Validating Docker setup..."
    
    # Check Docker daemon
    if ! docker info > /dev/null 2>&1; then
        add_error "Docker daemon not running or not accessible"
        return
    fi
    print_success "Docker daemon is running"
    
    # Check Docker Compose
    if ! docker-compose version > /dev/null 2>&1; then
        add_error "Docker Compose not available"
        return
    fi
    print_success "Docker Compose is available"
    
    # Check Docker network
    if ! docker network ls | grep -q "rag-network"; then
        add_warning "Docker network 'rag-network' not found - will be created during deployment"
    else
        print_success "Docker network 'rag-network' exists"
    fi
    
    # Validate Dockerfiles
    local dockerfiles=(
        "config/dockerfiles/Dockerfile.frontend"
        "config/dockerfiles/Dockerfile.backend"
        "config/dockerfiles/Dockerfile.nginx"
    )
    
    for dockerfile in "${dockerfiles[@]}"; do
        if [ ! -f "$dockerfile" ]; then
            add_error "Dockerfile missing: $dockerfile"
        else
            print_success "Found: $dockerfile"
        fi
    done
}

# Validate environment variables
validate_environment() {
    print_status "Validating environment variables..."
    
    local required_vars=(
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "SECRET_KEY"
        "JWT_SECRET"
        "OPENAI_API_KEY"
    )
    
    local optional_vars=(
        "HUGGINGFACE_API_KEY"
        "SLACK_WEBHOOK_URL"
        "API_TOKEN"
        "GOOGLE_PLAY_SERVICE_ACCOUNT"
        "APPLE_ID_USERNAME"
        "APPLE_ID_PASSWORD"
        "AWS_ACCESS_KEY_ID"
        "AWS_SECRET_ACCESS_KEY"
    )
    
    # Check required variables
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            add_error "Required environment variable not set: $var"
        else
            print_success "Environment variable set: $var"
        fi
    done
    
    # Check optional variables
    for var in "${optional_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            add_warning "Optional environment variable not set: $var"
        else
            print_success "Environment variable set: $var"
        fi
    done
}

# Validate database connectivity
validate_database() {
    print_status "Validating database connectivity..."
    
    # Check if database container is running
    if ! docker-compose ps postgres | grep -q "Up"; then
        add_warning "PostgreSQL container not running - will be started during deployment"
        return
    fi
    
    # Test database connection
    if docker-compose exec -T postgres pg_isready -U rag_user -d advanced_rag_db > /dev/null 2>&1; then
        print_success "Database connection successful"
    else
        add_error "Database connection failed"
    fi
    
    # Check database size and health
    local db_size=$(docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db -t -c "
        SELECT pg_size_pretty(pg_database_size('advanced_rag_db'));
    " 2>/dev/null | tr -d ' ' || echo "unknown")
    
    print_status "Database size: $db_size"
}

# Validate Redis connectivity
validate_redis() {
    print_status "Validating Redis connectivity..."
    
    # Check if Redis container is running
    if ! docker-compose ps redis | grep -q "Up"; then
        add_warning "Redis container not running - will be started during deployment"
        return
    fi
    
    # Test Redis connection
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis connection successful"
    else
        add_error "Redis connection failed"
    fi
    
    # Check Redis memory usage
    local redis_memory=$(docker-compose exec -T redis redis-cli info memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r' || echo "unknown")
    print_status "Redis memory usage: $redis_memory"
}

# Validate network connectivity
validate_network() {
    print_status "Validating network connectivity..."
    
    # Test external connectivity
    local test_urls=(
        "https://github.com"
        "https://registry.hub.docker.com"
        "https://api.openai.com"
    )
    
    for url in "${test_urls[@]}"; do
        if curl -f -s --max-time 10 "$url" > /dev/null; then
            print_success "Network connectivity to $url: OK"
        else
            add_warning "Network connectivity to $url: FAILED"
        fi
    done
}

# Validate SSL certificates
validate_ssl() {
    print_status "Validating SSL certificates..."
    
    local cert_files=(
        "/etc/nginx/ssl/fullchain.pem"
        "/etc/nginx/ssl/privkey.pem"
    )
    
    for cert_file in "${cert_files[@]}"; do
        if [ -f "$cert_file" ]; then
            # Check certificate expiration
            local expiry_date=$(openssl x509 -enddate -noout -in "$cert_file" 2>/dev/null | cut -d= -f2 || echo "unknown")
            print_success "SSL certificate found: $cert_file (expires: $expiry_date)"
        else
            add_warning "SSL certificate not found: $cert_file"
        fi
    done
}

# Validate mobile deployment setup
validate_mobile_deployment() {
    print_status "Validating mobile deployment setup..."
    
    # Check Node.js and npm
    if command -v node &> /dev/null; then
        local node_version=$(node --version)
        print_success "Node.js version: $node_version"
    else
        add_error "Node.js not found"
    fi
    
    if command -v npm &> /dev/null; then
        local npm_version=$(npm --version)
        print_success "npm version: $npm_version"
    else
        add_error "npm not found"
    fi
    
    # Check Capacitor CLI
    if command -v cap &> /dev/null; then
        local cap_version=$(cap --version)
        print_success "Capacitor CLI version: $cap_version"
    else
        add_warning "Capacitor CLI not found - will be installed during deployment"
    fi
    
    # Check Android SDK (if available)
    if command -v android &> /dev/null; then
        print_success "Android SDK found"
    else
        add_warning "Android SDK not found - Android builds will not be available"
    fi
    
    # Check Xcode (if on macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v xcodebuild &> /dev/null; then
            local xcode_version=$(xcodebuild -version | head -n1)
            print_success "Xcode found: $xcode_version"
        else
            add_warning "Xcode not found - iOS builds will not be available"
        fi
    fi
    
    # Check Fastlane
    if command -v fastlane &> /dev/null; then
        local fastlane_version=$(fastlane --version | head -n1)
        print_success "Fastlane found: $fastlane_version"
    else
        add_warning "Fastlane not found - will be installed during deployment"
    fi
}

# Validate monitoring setup
validate_monitoring() {
    print_status "Validating monitoring setup..."
    
    # Check if monitoring services are configured
    local monitoring_services=(
        "prometheus"
        "grafana"
        "loki"
    )
    
    for service in "${monitoring_services[@]}"; do
        if docker-compose config --services | grep -q "$service"; then
            print_success "Monitoring service configured: $service"
        else
            add_warning "Monitoring service not configured: $service"
        fi
    done
    
    # Check monitoring endpoints
    local monitoring_endpoints=(
        "http://localhost:9090"  # Prometheus
        "http://localhost:3001"  # Grafana
    )
    
    for endpoint in "${monitoring_endpoints[@]}"; do
        if curl -f -s --max-time 5 "$endpoint" > /dev/null 2>&1; then
            print_success "Monitoring endpoint accessible: $endpoint"
        else
            add_warning "Monitoring endpoint not accessible: $endpoint"
        fi
    done
}

# Validate backup configuration
validate_backup() {
    print_status "Validating backup configuration..."
    
    local backup_dir="./backups"
    
    if [ -d "$backup_dir" ]; then
        print_success "Backup directory exists: $backup_dir"
        
        # Check backup permissions
        if [ -w "$backup_dir" ]; then
            print_success "Backup directory is writable"
        else
            add_error "Backup directory is not writable: $backup_dir"
        fi
    else
        add_warning "Backup directory does not exist: $backup_dir (will be created)"
    fi
    
    # Check available disk space
    local available_space=$(df . | awk 'NR==2 {print $4}')
    local required_space=5000000  # 5GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        add_warning "Low disk space. Available: ${available_space}KB, Recommended: ${required_space}KB"
    else
        print_success "Sufficient disk space available: ${available_space}KB"
    fi
}

# Validate security configuration
validate_security() {
    print_status "Validating security configuration..."
    
    # Check file permissions
    local sensitive_files=(
        ".env"
        ".env.production"
        "config/deployment.env.example"
    )
    
    for file in "${sensitive_files[@]}"; do
        if [ -f "$file" ]; then
            local perms=$(stat -c "%a" "$file" 2>/dev/null || stat -f "%A" "$file" 2>/dev/null || echo "unknown")
            if [ "$perms" = "600" ] || [ "$perms" = "644" ]; then
                print_success "File permissions OK: $file ($perms)"
            else
                add_warning "File permissions may be too permissive: $file ($perms)"
            fi
        fi
    done
    
    # Check for secrets in version control
    if git rev-parse --git-dir > /dev/null 2>&1; then
        local secret_patterns=(
            "password"
            "secret"
            "key"
            "token"
        )
        
        for pattern in "${secret_patterns[@]}"; do
            if git log --all -S"$pattern" --oneline | head -1 | grep -q .; then
                add_warning "Potential secrets found in git history (pattern: $pattern)"
            fi
        done
    fi
}

# Generate validation report
generate_report() {
    local report_file="/tmp/deployment_validation_$(date +%Y%m%d_%H%M%S).json"
    
    print_status "Generating validation report..."
    
    cat > "$report_file" << EOF
{
  "validation": {
    "timestamp": "$(date -Iseconds)",
    "errors": $VALIDATION_ERRORS,
    "warnings": $VALIDATION_WARNINGS,
    "status": "$([ $VALIDATION_ERRORS -eq 0 ] && echo "PASS" || echo "FAIL")"
  },
  "system": {
    "os": "$(uname -s)",
    "architecture": "$(uname -m)",
    "docker_version": "$(docker --version 2>/dev/null || echo "not available")",
    "docker_compose_version": "$(docker-compose --version 2>/dev/null || echo "not available")",
    "node_version": "$(node --version 2>/dev/null || echo "not available")",
    "npm_version": "$(npm --version 2>/dev/null || echo "not available")"
  },
  "recommendations": [
    $([ $VALIDATION_ERRORS -gt 0 ] && echo '"Fix all validation errors before deployment",' || echo '')
    $([ $VALIDATION_WARNINGS -gt 0 ] && echo '"Review and address validation warnings",' || echo '')
    $([ $VALIDATION_ERRORS -eq 0 ] && [ $VALIDATION_WARNINGS -eq 0 ] && echo '"System is ready for deployment"' || echo '')
  ]
}
EOF
    
    print_success "Validation report generated: $report_file"
    echo "$report_file"
}

# Main validation function
main() {
    echo ""
    echo "✅ AI Scholar Advanced RAG - Deployment Validation"
    echo "=================================================="
    echo "Started: $(date)"
    echo ""
    
    # Run all validations
    validate_files
    validate_permissions
    validate_docker
    validate_environment
    validate_database
    validate_redis
    validate_network
    validate_ssl
    validate_mobile_deployment
    validate_monitoring
    validate_backup
    validate_security
    
    echo ""
    echo "=================================================="
    echo "Validation Summary:"
    echo "  Errors: $VALIDATION_ERRORS"
    echo "  Warnings: $VALIDATION_WARNINGS"
    echo ""
    
    # Generate report
    local report_file=$(generate_report)
    
    if [ $VALIDATION_ERRORS -eq 0 ]; then
        print_success "🎉 Deployment validation passed!"
        echo "System is ready for deployment."
        
        if [ $VALIDATION_WARNINGS -gt 0 ]; then
            print_warning "Please review $VALIDATION_WARNINGS warning(s) before proceeding."
        fi
        
        exit 0
    else
        print_error "❌ Deployment validation failed!"
        echo "Please fix $VALIDATION_ERRORS error(s) before deployment."
        echo "Report: $report_file"
        exit 1
    fi
}

# Install required tools if needed
if ! command -v jq &> /dev/null; then
    print_status "Installing jq for JSON processing..."
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y jq
    elif command -v yum &> /dev/null; then
        yum install -y jq
    elif command -v brew &> /dev/null; then
        brew install jq
    fi
fi

# Run main function
main "$@"