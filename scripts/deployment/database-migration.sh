#!/bin/bash

# Database Migration Script for AI Scholar Advanced RAG
# Handles schema updates and data migrations for new features

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
DB_CONTAINER="advanced-rag-postgres"
DB_NAME="advanced_rag_db"
DB_USER="rag_user"
BACKUP_DIR="./backups/migrations"
MIGRATION_DIR="./backend/migrations"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Pre-migration backup
create_backup() {
    print_status "Creating pre-migration backup..."
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_file="$BACKUP_DIR/pre_migration_${timestamp}.sql"
    
    docker-compose exec -T "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" > "$backup_file"
    
    if [ $? -eq 0 ]; then
        print_success "Backup created: $backup_file"
        echo "$backup_file" > "$BACKUP_DIR/latest_backup.txt"
    else
        print_error "Failed to create backup"
        exit 1
    fi
}

# Check database connection
check_database() {
    print_status "Checking database connection..."
    
    if docker-compose exec -T "$DB_CONTAINER" pg_isready -U "$DB_USER" -d "$DB_NAME"; then
        print_success "Database connection successful"
    else
        print_error "Database connection failed"
        exit 1
    fi
}

# Run schema migrations
run_schema_migrations() {
    print_status "Running schema migrations..."
    
    # Mobile accessibility features
    print_status "Adding mobile accessibility tables..."
    docker-compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << 'EOF'
-- Mobile sessions and sync
CREATE TABLE IF NOT EXISTS mobile_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    device_info JSONB NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    offline_cache JSONB DEFAULT '{}',
    sync_status VARCHAR(50) DEFAULT 'pending',
    last_sync TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Accessibility preferences
CREATE TABLE IF NOT EXISTS accessibility_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    screen_reader_enabled BOOLEAN DEFAULT FALSE,
    high_contrast_mode BOOLEAN DEFAULT FALSE,
    font_size_multiplier DECIMAL(3,2) DEFAULT 1.0,
    keyboard_navigation_only BOOLEAN DEFAULT FALSE,
    voice_feedback_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- PWA installations
CREATE TABLE IF NOT EXISTS pwa_installations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    device_type VARCHAR(50) NOT NULL,
    installation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    push_subscription JSONB,
    is_active BOOLEAN DEFAULT TRUE
);

-- Mobile app versions
CREATE TABLE IF NOT EXISTS mobile_app_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(20) NOT NULL, -- 'pwa', 'android', 'ios'
    version VARCHAR(50) NOT NULL,
    build_number INTEGER,
    release_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    minimum_supported_version VARCHAR(50),
    features JSONB DEFAULT '{}',
    rollout_percentage INTEGER DEFAULT 100,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Mobile feature flags
CREATE TABLE IF NOT EXISTS mobile_feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_name VARCHAR(100) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    is_enabled BOOLEAN DEFAULT FALSE,
    rollout_percentage INTEGER DEFAULT 0,
    target_versions JSONB DEFAULT '[]',
    conditions JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(flag_name, platform)
);
EOF

    # Voice interface features
    print_status "Adding voice interface tables..."
    docker-compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << 'EOF'
-- Voice sessions
CREATE TABLE IF NOT EXISTS voice_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    voice_profile JSONB DEFAULT '{}',
    conversation_context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Voice commands
CREATE TABLE IF NOT EXISTS voice_commands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES voice_sessions(id) ON DELETE CASCADE,
    command_text TEXT NOT NULL,
    intent VARCHAR(100),
    entities JSONB DEFAULT '[]',
    confidence_score DECIMAL(5,4),
    execution_result JSONB,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Voice preferences
CREATE TABLE IF NOT EXISTS voice_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    preferred_language VARCHAR(10) DEFAULT 'en',
    voice_speed DECIMAL(3,2) DEFAULT 1.0,
    voice_pitch DECIMAL(3,2) DEFAULT 1.0,
    noise_cancellation BOOLEAN DEFAULT TRUE,
    wake_word_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
EOF

    # External integrations
    print_status "Adding external integration tables..."
    docker-compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << 'EOF'
-- External integrations
CREATE TABLE IF NOT EXISTS external_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    integration_type VARCHAR(50) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    credentials JSONB NOT NULL, -- Encrypted
    sync_settings JSONB DEFAULT '{}',
    last_sync TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, integration_type, service_name)
);

-- Integration sync logs
CREATE TABLE IF NOT EXISTS integration_sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_id UUID REFERENCES external_integrations(id) ON DELETE CASCADE,
    sync_type VARCHAR(50) NOT NULL,
    items_synced INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    sync_duration_ms INTEGER,
    error_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bibliographic data
CREATE TABLE IF NOT EXISTS bibliographic_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    integration_id UUID REFERENCES external_integrations(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    authors JSONB DEFAULT '[]',
    journal VARCHAR(255),
    year INTEGER,
    doi VARCHAR(255),
    abstract TEXT,
    keywords JSONB DEFAULT '[]',
    citation_count INTEGER DEFAULT 0,
    external_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
EOF

    # Educational features
    print_status "Adding educational feature tables..."
    docker-compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << 'EOF'
-- Quizzes
CREATE TABLE IF NOT EXISTS quizzes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content_source_id UUID, -- References document or content
    difficulty_level VARCHAR(20) DEFAULT 'medium',
    estimated_time_minutes INTEGER DEFAULT 15,
    learning_objectives JSONB DEFAULT '[]',
    questions JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Quiz attempts
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID REFERENCES quizzes(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    responses JSONB NOT NULL,
    score DECIMAL(5,2),
    time_taken_seconds INTEGER,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Spaced repetition items
CREATE TABLE IF NOT EXISTS spaced_repetition_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content_id UUID NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    difficulty DECIMAL(3,2) DEFAULT 2.5,
    interval_days INTEGER DEFAULT 1,
    repetition_count INTEGER DEFAULT 0,
    ease_factor DECIMAL(3,2) DEFAULT 2.5,
    next_review_date DATE NOT NULL,
    last_reviewed TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Learning progress
CREATE TABLE IF NOT EXISTS learning_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subject_area VARCHAR(100) NOT NULL,
    competency_level DECIMAL(5,2) DEFAULT 0.0,
    time_spent_minutes INTEGER DEFAULT 0,
    items_mastered INTEGER DEFAULT 0,
    items_learning INTEGER DEFAULT 0,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, subject_area)
);
EOF

    # Enterprise and compliance features
    print_status "Adding enterprise feature tables..."
    docker-compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << 'EOF'
-- Institutions
CREATE TABLE IF NOT EXISTS institutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE,
    settings JSONB DEFAULT '{}',
    compliance_policies JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Institutional roles
CREATE TABLE IF NOT EXISTS institutional_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES institutions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_type VARCHAR(50) NOT NULL,
    permissions JSONB DEFAULT '{}',
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(institution_id, user_id)
);

-- Compliance violations
CREATE TABLE IF NOT EXISTS compliance_violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES institutions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    violation_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    description TEXT NOT NULL,
    policy_violated VARCHAR(255),
    resolution_status VARCHAR(50) DEFAULT 'open',
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Resource usage tracking
CREATE TABLE IF NOT EXISTS resource_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES institutions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL,
    usage_amount DECIMAL(10,2) NOT NULL,
    usage_unit VARCHAR(20) NOT NULL,
    cost DECIMAL(10,2),
    usage_date DATE NOT NULL,
    metadata JSONB DEFAULT '{}'
);
EOF

    # Interactive content features
    print_status "Adding interactive content tables..."
    docker-compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << 'EOF'
-- Jupyter notebooks
CREATE TABLE IF NOT EXISTS jupyter_notebooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    notebook_content JSONB NOT NULL,
    kernel_type VARCHAR(50) DEFAULT 'python3',
    execution_status VARCHAR(50) DEFAULT 'idle',
    last_executed TIMESTAMP WITH TIME ZONE,
    version INTEGER DEFAULT 1,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Interactive visualizations
CREATE TABLE IF NOT EXISTS interactive_visualizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    visualization_type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    data_source JSONB,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Code execution sessions
CREATE TABLE IF NOT EXISTS code_execution_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    language VARCHAR(50) NOT NULL,
    environment_config JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);
EOF

    # Opportunity matching features
    print_status "Adding opportunity matching tables..."
    docker-compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << 'EOF'
-- Funding opportunities
CREATE TABLE IF NOT EXISTS funding_opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    agency VARCHAR(255) NOT NULL,
    program VARCHAR(255),
    description TEXT,
    eligibility_criteria JSONB DEFAULT '{}',
    funding_amount_min DECIMAL(12,2),
    funding_amount_max DECIMAL(12,2),
    application_deadline DATE,
    keywords JSONB DEFAULT '[]',
    external_id VARCHAR(255),
    source_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Publication venues
CREATE TABLE IF NOT EXISTS publication_venues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    venue_type VARCHAR(50) NOT NULL, -- journal, conference
    impact_factor DECIMAL(6,3),
    acceptance_rate DECIMAL(5,2),
    subject_areas JSONB DEFAULT '[]',
    submission_guidelines JSONB DEFAULT '{}',
    deadlines JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User opportunity matches
CREATE TABLE IF NOT EXISTS opportunity_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    opportunity_id UUID, -- Can reference funding_opportunities or publication_venues
    opportunity_type VARCHAR(50) NOT NULL,
    relevance_score DECIMAL(5,4) NOT NULL,
    match_reasons JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'suggested',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
EOF

    print_success "Schema migrations completed successfully"
}

# Create indices for performance
create_indices() {
    print_status "Creating database indices..."
    
    docker-compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << 'EOF'
-- Mobile and accessibility indices
CREATE INDEX IF NOT EXISTS idx_mobile_sessions_user_id ON mobile_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_mobile_sessions_sync_status ON mobile_sessions(sync_status);
CREATE INDEX IF NOT EXISTS idx_accessibility_preferences_user_id ON accessibility_preferences(user_id);

-- Voice interface indices
CREATE INDEX IF NOT EXISTS idx_voice_sessions_user_id ON voice_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_commands_session_id ON voice_commands(session_id);
CREATE INDEX IF NOT EXISTS idx_voice_commands_intent ON voice_commands(intent);

-- Integration indices
CREATE INDEX IF NOT EXISTS idx_external_integrations_user_id ON external_integrations(user_id);
CREATE INDEX IF NOT EXISTS idx_external_integrations_type ON external_integrations(integration_type);
CREATE INDEX IF NOT EXISTS idx_integration_sync_logs_integration_id ON integration_sync_logs(integration_id);
CREATE INDEX IF NOT EXISTS idx_bibliographic_data_user_id ON bibliographic_data(user_id);
CREATE INDEX IF NOT EXISTS idx_bibliographic_data_doi ON bibliographic_data(doi);

-- Educational indices
CREATE INDEX IF NOT EXISTS idx_quizzes_user_id ON quizzes(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user_id ON quiz_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_quiz_id ON quiz_attempts(quiz_id);
CREATE INDEX IF NOT EXISTS idx_spaced_repetition_user_id ON spaced_repetition_items(user_id);
CREATE INDEX IF NOT EXISTS idx_spaced_repetition_next_review ON spaced_repetition_items(next_review_date);
CREATE INDEX IF NOT EXISTS idx_learning_progress_user_id ON learning_progress(user_id);

-- Enterprise indices
CREATE INDEX IF NOT EXISTS idx_institutional_roles_institution_id ON institutional_roles(institution_id);
CREATE INDEX IF NOT EXISTS idx_institutional_roles_user_id ON institutional_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_compliance_violations_institution_id ON compliance_violations(institution_id);
CREATE INDEX IF NOT EXISTS idx_compliance_violations_user_id ON compliance_violations(user_id);
CREATE INDEX IF NOT EXISTS idx_resource_usage_institution_id ON resource_usage(institution_id);
CREATE INDEX IF NOT EXISTS idx_resource_usage_date ON resource_usage(usage_date);

-- Interactive content indices
CREATE INDEX IF NOT EXISTS idx_jupyter_notebooks_user_id ON jupyter_notebooks(user_id);
CREATE INDEX IF NOT EXISTS idx_interactive_visualizations_user_id ON interactive_visualizations(user_id);
CREATE INDEX IF NOT EXISTS idx_code_execution_sessions_user_id ON code_execution_sessions(user_id);

-- Opportunity matching indices
CREATE INDEX IF NOT EXISTS idx_funding_opportunities_deadline ON funding_opportunities(application_deadline);
CREATE INDEX IF NOT EXISTS idx_funding_opportunities_active ON funding_opportunities(is_active);
CREATE INDEX IF NOT EXISTS idx_publication_venues_type ON publication_venues(venue_type);
CREATE INDEX IF NOT EXISTS idx_opportunity_matches_user_id ON opportunity_matches(user_id);
CREATE INDEX IF NOT EXISTS idx_opportunity_matches_score ON opportunity_matches(relevance_score);
EOF

    print_success "Database indices created successfully"
}

# Update database statistics
update_statistics() {
    print_status "Updating database statistics..."
    
    docker-compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "ANALYZE;"
    
    print_success "Database statistics updated"
}

# Verify migration
verify_migration() {
    print_status "Verifying migration..."
    
    # Check if all tables exist
    tables_count=$(docker-compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN (
            'mobile_sessions', 'accessibility_preferences', 'pwa_installations',
            'voice_sessions', 'voice_commands', 'voice_preferences',
            'external_integrations', 'integration_sync_logs', 'bibliographic_data',
            'quizzes', 'quiz_attempts', 'spaced_repetition_items', 'learning_progress',
            'institutions', 'institutional_roles', 'compliance_violations', 'resource_usage',
            'jupyter_notebooks', 'interactive_visualizations', 'code_execution_sessions',
            'funding_opportunities', 'publication_venues', 'opportunity_matches'
        );
    " | tr -d ' ')
    
    expected_tables=22
    
    if [ "$tables_count" -eq "$expected_tables" ]; then
        print_success "All $expected_tables tables created successfully"
    else
        print_error "Expected $expected_tables tables, found $tables_count"
        exit 1
    fi
    
    # Test database connection
    if docker-compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null; then
        print_success "Database connection verified"
    else
        print_error "Database connection failed after migration"
        exit 1
    fi
}

# Rollback function
rollback_migration() {
    print_status "Rolling back migration..."
    
    latest_backup=$(cat "$BACKUP_DIR/latest_backup.txt" 2>/dev/null || echo "")
    
    if [ -n "$latest_backup" ] && [ -f "$latest_backup" ]; then
        print_warning "Restoring from backup: $latest_backup"
        
        # Drop current database and recreate
        docker-compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"
        docker-compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d postgres -c "CREATE DATABASE ${DB_NAME};"
        
        # Restore from backup
        docker-compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" < "$latest_backup"
        
        print_success "Database restored from backup"
    else
        print_error "No backup found for rollback"
        exit 1
    fi
}

# Zero-downtime migration function
zero_downtime_migration() {
    print_status "Performing zero-downtime migration..."
    
    # Create shadow tables for new schema
    print_status "Creating shadow tables..."
    docker-compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << 'EOF'
-- Create shadow tables with new schema
CREATE TABLE IF NOT EXISTS mobile_sessions_new (LIKE mobile_sessions INCLUDING ALL);
CREATE TABLE IF NOT EXISTS voice_sessions_new (LIKE voice_sessions INCLUDING ALL);
-- Add other shadow tables as needed
EOF

    # Migrate data in batches
    print_status "Migrating data in batches..."
    docker-compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << 'EOF'
-- Batch migration with minimal locking
INSERT INTO mobile_sessions_new SELECT * FROM mobile_sessions WHERE id NOT IN (SELECT id FROM mobile_sessions_new);
INSERT INTO voice_sessions_new SELECT * FROM voice_sessions WHERE id NOT IN (SELECT id FROM voice_sessions_new);
EOF

    # Atomic table swap
    print_status "Performing atomic table swap..."
    docker-compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << 'EOF'
BEGIN;
ALTER TABLE mobile_sessions RENAME TO mobile_sessions_old;
ALTER TABLE mobile_sessions_new RENAME TO mobile_sessions;
ALTER TABLE voice_sessions RENAME TO voice_sessions_old;
ALTER TABLE voice_sessions_new RENAME TO voice_sessions;
COMMIT;
EOF

    print_success "Zero-downtime migration completed"
}

# Migration validation function
validate_migration() {
    print_status "Validating migration integrity..."
    
    # Check data consistency
    docker-compose exec -T "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << 'EOF'
-- Validate foreign key constraints
SELECT conname, conrelid::regclass, confrelid::regclass 
FROM pg_constraint 
WHERE contype = 'f' AND NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints 
    WHERE constraint_name = conname
);

-- Check for orphaned records
SELECT 'mobile_sessions' as table_name, COUNT(*) as orphaned_count
FROM mobile_sessions m 
WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = m.user_id)
UNION ALL
SELECT 'voice_sessions', COUNT(*)
FROM voice_sessions v 
WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = v.user_id);
EOF

    print_success "Migration validation completed"
}

# Main migration function
main() {
    echo ""
    echo "🗄️  AI Scholar Advanced RAG - Database Migration"
    echo "================================================"
    echo "Started: $(date)"
    echo ""
    
    case "${1:-migrate}" in
        "migrate")
            check_database
            create_backup
            run_schema_migrations
            create_indices
            update_statistics
            verify_migration
            validate_migration
            print_success "🎉 Database migration completed successfully!"
            ;;
        "zero-downtime")
            check_database
            create_backup
            zero_downtime_migration
            create_indices
            update_statistics
            verify_migration
            validate_migration
            print_success "🎉 Zero-downtime migration completed successfully!"
            ;;
        "rollback")
            rollback_migration
            ;;
        "verify")
            verify_migration
            ;;
        "validate")
            validate_migration
            ;;
        "backup")
            create_backup
            ;;
        *)
            echo "Usage: $0 {migrate|zero-downtime|rollback|verify|validate|backup}"
            echo ""
            echo "Commands:"
            echo "  migrate       - Run database migrations (default)"
            echo "  zero-downtime - Run zero-downtime migration"
            echo "  rollback      - Rollback to previous backup"
            echo "  verify        - Verify migration success"
            echo "  validate      - Validate migration integrity"
            echo "  backup        - Create database backup only"
            exit 1
            ;;
    esac
    
    echo ""
    echo "Finished: $(date)"
    echo ""
}

# Handle errors
trap 'print_error "Migration failed at line $LINENO. Rolling back..."; rollback_migration' ERR

# Run main function
main "$@"