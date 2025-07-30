#!/bin/bash

# Advanced RAG Research Ecosystem - Update Script
# Safe update procedure with rollback capability

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
BACKUP_DIR="./backups"
UPDATE_LOG="./logs/update_$(date +%Y%m%d_%H%M%S).log"
ROLLBACK_POINT=""

# Create update log
mkdir -p ./logs
exec 1> >(tee -a "$UPDATE_LOG")
exec 2> >(tee -a "$UPDATE_LOG" >&2)

# Cleanup function
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "Update failed. Check log: $UPDATE_LOG"
        if [ -n "$ROLLBACK_POINT" ]; then
            print_status "Rollback point available: $ROLLBACK_POINT"
            read -p "Do you want to rollback? (y/n): " rollback_choice
            if [[ $rollback_choice == [yY] ]]; then
                rollback_deployment
            fi
        fi
    fi
}

trap cleanup EXIT

# Pre-update checks
pre_update_checks() {
    print_status "Running pre-update checks..."
    
    # Check if services are running
    if ! docker-compose ps | grep -q "Up"; then
        print_error "Some services are not running. Please start services first."
        exit 1
    fi
    
    # Check disk space
    disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        print_error "Insufficient disk space: $disk_usage% used"
        exit 1
    fi
    
    # Check if git repository is clean
    if [ -n "$(git status --porcelain)" ]; then
        print_warning "Git repository has uncommitted changes"
        read -p "Continue anyway? (y/n): " continue_choice
        if [[ $continue_choice != [yY] ]]; then
            exit 1
        fi
    fi
    
    # Test current deployment health
    if ! ./scripts/health-check.sh > /dev/null 2>&1; then
        print_warning "Current deployment has health issues"
        read -p "Continue with update? (y/n): " continue_choice
        if [[ $continue_choice != [yY] ]]; then
            exit 1
        fi
    fi
    
    print_success "Pre-update checks passed"
}

# Create rollback point
create_rollback_point() {
    print_status "Creating rollback point..."
    
    ROLLBACK_POINT="rollback_$(date +%Y%m%d_%H%M%S)"
    
    # Backup current state
    ./scripts/backup.sh > /dev/null 2>&1
    
    # Save current git commit
    git rev-parse HEAD > "$BACKUP_DIR/$ROLLBACK_POINT.commit"
    
    # Save current docker-compose state
    docker-compose config > "$BACKUP_DIR/$ROLLBACK_POINT.compose.yml"
    
    # Save current environment
    cp .env "$BACKUP_DIR/$ROLLBACK_POINT.env"
    
    print_success "Rollback point created: $ROLLBACK_POINT"
}

# Update application code
update_code() {
    print_status "Updating application code..."
    
    # Fetch latest changes
    git fetch origin
    
    # Get current and target commits
    current_commit=$(git rev-parse HEAD)
    target_commit=$(git rev-parse origin/main)
    
    if [ "$current_commit" = "$target_commit" ]; then
        print_success "Code is already up to date"
        return 0
    fi
    
    print_status "Updating from $current_commit to $target_commit"
    
    # Pull latest changes
    git pull origin main
    
    print_success "Code updated successfully"
}

# Update Docker images
update_images() {
    print_status "Updating Docker images..."
    
    # Pull latest base images
    docker-compose pull
    
    # Rebuild custom images
    docker-compose build --no-cache --pull
    
    print_success "Docker images updated"
}

# Update dependencies
update_dependencies() {
    print_status "Checking for dependency updates..."
    
    # Check if requirements.txt changed
    if git diff HEAD~1 HEAD --name-only | grep -q "requirements.txt"; then
        print_status "Python dependencies updated, rebuilding backend..."
        docker-compose build --no-cache backend
    fi
    
    # Check if package.json changed
    if git diff HEAD~1 HEAD --name-only | grep -q "frontend/package.json"; then
        print_status "Node.js dependencies updated, rebuilding frontend..."
        docker-compose build --no-cache frontend
    fi
    
    print_success "Dependencies checked and updated"
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Check if there are new migrations
    if docker-compose exec -T backend alembic current | grep -q "head"; then
        print_success "Database is already up to date"
    else
        # Run migrations
        docker-compose exec -T backend alembic upgrade head
        print_success "Database migrations completed"
    fi
}

# Rolling update deployment
rolling_update() {
    print_status "Performing rolling update..."
    
    # Update services one by one to minimize downtime
    services=("backend" "frontend" "nginx")
    
    for service in "${services[@]}"; do
        print_status "Updating $service..."
        
        # Start new container
        docker-compose up -d --no-deps --scale "$service=2" "$service"
        
        # Wait for new container to be healthy
        sleep 30
        
        # Remove old container
        docker-compose up -d --no-deps --scale "$service=1" "$service"
        
        # Verify service health
        if ! ./scripts/health-check.sh "$service" > /dev/null 2>&1; then
            print_error "Health check failed for $service"
            return 1
        fi
        
        print_success "$service updated successfully"
    done
}

# Standard update deployment
standard_update() {
    print_status "Performing standard update..."
    
    # Stop services
    docker-compose down
    
    # Start updated services
    docker-compose up -d
    
    # Wait for services to be ready
    sleep 60
    
    print_success "Services updated and restarted"
}

# Post-update verification
post_update_verification() {
    print_status "Running post-update verification..."
    
    # Wait for services to stabilize
    sleep 30
    
    # Run comprehensive health check
    if ./scripts/health-check.sh; then
        print_success "Post-update health check passed"
    else
        print_error "Post-update health check failed"
        return 1
    fi
    
    # Test critical functionality
    if curl -f -s "http://localhost:8000/health" > /dev/null; then
        print_success "Backend API is responding"
    else
        print_error "Backend API is not responding"
        return 1
    fi
    
    if curl -f -s "http://localhost:3000/health" > /dev/null; then
        print_success "Frontend is responding"
    else
        print_error "Frontend is not responding"
        return 1
    fi
    
    print_success "Post-update verification completed"
}

# Rollback deployment
rollback_deployment() {
    print_error "Rolling back deployment..."
    
    if [ -z "$ROLLBACK_POINT" ]; then
        print_error "No rollback point available"
        return 1
    fi
    
    # Stop current services
    docker-compose down
    
    # Restore git state
    if [ -f "$BACKUP_DIR/$ROLLBACK_POINT.commit" ]; then
        rollback_commit=$(cat "$BACKUP_DIR/$ROLLBACK_POINT.commit")
        git reset --hard "$rollback_commit"
        print_success "Code rolled back to $rollback_commit"
    fi
    
    # Restore environment
    if [ -f "$BACKUP_DIR/$ROLLBACK_POINT.env" ]; then
        cp "$BACKUP_DIR/$ROLLBACK_POINT.env" .env
        print_success "Environment restored"
    fi
    
    # Restore database
    latest_backup=$(find "$BACKUP_DIR" -name "database_*.sql.gz" | sort | tail -1)
    if [ -n "$latest_backup" ]; then
        print_status "Restoring database from $latest_backup"
        gunzip -c "$latest_backup" | docker-compose exec -T postgres psql -U rag_user -d advanced_rag_db
        print_success "Database restored"
    fi
    
    # Start services
    docker-compose up -d
    
    # Wait and verify
    sleep 60
    if ./scripts/health-check.sh > /dev/null 2>&1; then
        print_success "Rollback completed successfully"
    else
        print_error "Rollback verification failed"
    fi
}

# Cleanup old rollback points
cleanup_rollback_points() {
    print_status "Cleaning up old rollback points..."
    
    # Keep only last 5 rollback points
    find "$BACKUP_DIR" -name "rollback_*" -type f | sort | head -n -15 | xargs rm -f 2>/dev/null || true
    
    print_success "Old rollback points cleaned up"
}

# Generate update report
generate_update_report() {
    print_status "Generating update report..."
    
    report_file="./logs/update_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
Advanced RAG Research Ecosystem - Update Report
===============================================
Date: $(date)
Update Type: ${UPDATE_TYPE:-standard}
Rollback Point: $ROLLBACK_POINT

Git Information:
- Previous Commit: $(cat "$BACKUP_DIR/$ROLLBACK_POINT.commit" 2>/dev/null || echo "Unknown")
- Current Commit: $(git rev-parse HEAD)
- Branch: $(git branch --show-current)

Services Status:
$(docker-compose ps)

Health Check Results:
$(./scripts/health-check.sh 2>&1 || echo "Health check failed")

Update Log:
$(tail -50 "$UPDATE_LOG")

Next Steps:
1. Monitor system performance
2. Verify user functionality
3. Update documentation if needed
4. Schedule next update
EOF

    print_success "Update report generated: $report_file"
}

# Main update function
main() {
    echo ""
    echo "🔄 Advanced RAG Research Ecosystem - Update"
    echo "==========================================="
    echo "Started: $(date)"
    echo ""
    
    # Determine update type
    UPDATE_TYPE="${1:-standard}"
    
    print_status "Update type: $UPDATE_TYPE"
    
    # Run update process
    pre_update_checks
    create_rollback_point
    update_code
    update_images
    update_dependencies
    run_migrations
    
    # Choose deployment strategy
    case "$UPDATE_TYPE" in
        "rolling")
            rolling_update
            ;;
        "standard"|*)
            standard_update
            ;;
    esac
    
    post_update_verification
    cleanup_rollback_points
    generate_update_report
    
    echo ""
    print_success "🎉 Update completed successfully!"
    echo ""
    echo "📊 Update Summary:"
    echo "=================="
    echo "• Code updated from git repository"
    echo "• Docker images rebuilt and updated"
    echo "• Database migrations applied"
    echo "• Services restarted and verified"
    echo "• Health checks passed"
    echo "• Rollback point created: $ROLLBACK_POINT"
    echo ""
    echo "📝 Next Steps:"
    echo "1. Monitor application performance"
    echo "2. Test critical functionality"
    echo "3. Review update report in ./logs/"
    echo "4. Update team documentation"
    echo ""
}

# Parse command line arguments
case "${1:-standard}" in
    "standard")
        main "standard"
        ;;
    "rolling")
        main "rolling"
        ;;
    "rollback")
        if [ -z "$2" ]; then
            print_error "Please specify rollback point"
            echo "Available rollback points:"
            ls -1 "$BACKUP_DIR"/rollback_*.commit 2>/dev/null | sed 's/.*rollback_\(.*\)\.commit/\1/' || echo "No rollback points found"
            exit 1
        fi
        ROLLBACK_POINT="$2"
        rollback_deployment
        ;;
    "check")
        pre_update_checks
        print_success "System is ready for update"
        ;;
    *)
        echo "Usage: $0 {standard|rolling|rollback|check}"
        echo ""
        echo "Commands:"
        echo "  standard  - Standard update with service restart (default)"
        echo "  rolling   - Rolling update with zero downtime"
        echo "  rollback  - Rollback to previous version"
        echo "  check     - Check if system is ready for update"
        echo ""
        echo "Examples:"
        echo "  $0 standard    # Standard update"
        echo "  $0 rolling     # Zero-downtime update"
        echo "  $0 rollback rollback_20240101_120000  # Rollback to specific point"
        exit 1
        ;;
esac