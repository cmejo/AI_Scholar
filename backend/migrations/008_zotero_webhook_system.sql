-- Migration: Add Zotero webhook handling system tables
-- Description: Creates tables for webhook handling, background sync processing, and sync monitoring

-- Create webhook endpoints table
CREATE TABLE IF NOT EXISTS zotero.zotero_webhook_endpoints (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR NOT NULL,
    connection_id VARCHAR NOT NULL REFERENCES zotero.zotero_connections(id) ON DELETE CASCADE,
    webhook_url VARCHAR(500) NOT NULL,
    webhook_secret VARCHAR(255) NOT NULL,
    webhook_status VARCHAR(20) DEFAULT 'active', -- 'active', 'inactive', 'error'
    last_ping_at TIMESTAMP,
    last_error_at TIMESTAMP,
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    webhook_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create webhook events table
CREATE TABLE IF NOT EXISTS zotero.zotero_webhook_events (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    endpoint_id VARCHAR NOT NULL REFERENCES zotero.zotero_webhook_endpoints(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- 'library_update', 'item_update', 'collection_update', 'attachment_update'
    event_data JSONB NOT NULL,
    processing_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed', 'retrying'
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMP,
    processed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    event_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create background sync jobs table
CREATE TABLE IF NOT EXISTS zotero.zotero_sync_jobs (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    connection_id VARCHAR NOT NULL REFERENCES zotero.zotero_connections(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL, -- 'full_sync', 'incremental_sync', 'webhook_triggered', 'manual_sync'
    job_status VARCHAR(20) DEFAULT 'queued', -- 'queued', 'running', 'completed', 'failed', 'cancelled'
    priority INTEGER DEFAULT 5, -- 1-10, lower is higher priority
    scheduled_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    progress_percentage INTEGER DEFAULT 0,
    items_to_process INTEGER DEFAULT 0,
    items_processed INTEGER DEFAULT 0,
    items_added INTEGER DEFAULT 0,
    items_updated INTEGER DEFAULT 0,
    items_deleted INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    error_details JSONB DEFAULT '[]'::jsonb,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMP,
    job_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create sync conflict resolution table
CREATE TABLE IF NOT EXISTS zotero.zotero_sync_conflicts (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    sync_job_id VARCHAR NOT NULL REFERENCES zotero.zotero_sync_jobs(id) ON DELETE CASCADE,
    item_id VARCHAR REFERENCES zotero.zotero_items(id) ON DELETE CASCADE,
    collection_id VARCHAR REFERENCES zotero.zotero_collections(id) ON DELETE CASCADE,
    conflict_type VARCHAR(50) NOT NULL, -- 'version_mismatch', 'deleted_locally', 'deleted_remotely', 'data_inconsistency'
    local_version INTEGER,
    remote_version INTEGER,
    local_data JSONB,
    remote_data JSONB,
    resolution_strategy VARCHAR(50) DEFAULT 'zotero_wins', -- 'zotero_wins', 'local_wins', 'merge', 'manual'
    resolution_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'resolved', 'failed', 'manual_required'
    resolved_at TIMESTAMP,
    resolved_by VARCHAR, -- user_id who resolved manually
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    conflict_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create sync status monitoring table
CREATE TABLE IF NOT EXISTS zotero.zotero_sync_status (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    connection_id VARCHAR NOT NULL REFERENCES zotero.zotero_connections(id) ON DELETE CASCADE,
    status_type VARCHAR(50) NOT NULL, -- 'sync_progress', 'error_report', 'completion_notification'
    status VARCHAR(20) NOT NULL, -- 'in_progress', 'completed', 'error', 'warning'
    title VARCHAR(255) NOT NULL,
    message TEXT,
    progress_percentage INTEGER DEFAULT 0,
    details JSONB DEFAULT '{}'::jsonb,
    is_read BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create sync audit log table
CREATE TABLE IF NOT EXISTS zotero.zotero_sync_audit_log (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    connection_id VARCHAR NOT NULL REFERENCES zotero.zotero_connections(id) ON DELETE CASCADE,
    sync_job_id VARCHAR REFERENCES zotero.zotero_sync_jobs(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL, -- 'sync_started', 'sync_completed', 'item_added', 'item_updated', 'item_deleted', 'error_occurred'
    target_type VARCHAR(50), -- 'library', 'collection', 'item', 'attachment'
    target_id VARCHAR,
    old_data JSONB,
    new_data JSONB,
    user_id VARCHAR, -- References users.id
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    audit_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_webhook_endpoints_connection_id ON zotero.zotero_webhook_endpoints(connection_id);
CREATE INDEX IF NOT EXISTS idx_webhook_endpoints_status ON zotero.zotero_webhook_endpoints(webhook_status);

CREATE INDEX IF NOT EXISTS idx_webhook_events_endpoint_id ON zotero.zotero_webhook_events(endpoint_id);
CREATE INDEX IF NOT EXISTS idx_webhook_events_status ON zotero.zotero_webhook_events(processing_status);
CREATE INDEX IF NOT EXISTS idx_webhook_events_created_at ON zotero.zotero_webhook_events(created_at);
CREATE INDEX IF NOT EXISTS idx_webhook_events_next_retry ON zotero.zotero_webhook_events(next_retry_at) WHERE next_retry_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sync_jobs_connection_id ON zotero.zotero_sync_jobs(connection_id);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_status ON zotero.zotero_sync_jobs(job_status);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_scheduled_at ON zotero.zotero_sync_jobs(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_priority ON zotero.zotero_sync_jobs(priority);

CREATE INDEX IF NOT EXISTS idx_sync_conflicts_job_id ON zotero.zotero_sync_conflicts(sync_job_id);
CREATE INDEX IF NOT EXISTS idx_sync_conflicts_status ON zotero.zotero_sync_conflicts(resolution_status);

CREATE INDEX IF NOT EXISTS idx_sync_status_connection_id ON zotero.zotero_sync_status(connection_id);
CREATE INDEX IF NOT EXISTS idx_sync_status_type ON zotero.zotero_sync_status(status_type);
CREATE INDEX IF NOT EXISTS idx_sync_status_read ON zotero.zotero_sync_status(is_read);

CREATE INDEX IF NOT EXISTS idx_sync_audit_connection_id ON zotero.zotero_sync_audit_log(connection_id);
CREATE INDEX IF NOT EXISTS idx_sync_audit_job_id ON zotero.zotero_sync_audit_log(sync_job_id);
CREATE INDEX IF NOT EXISTS idx_sync_audit_created_at ON zotero.zotero_sync_audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_sync_audit_action ON zotero.zotero_sync_audit_log(action);

-- Add updated_at trigger for webhook endpoints
CREATE OR REPLACE FUNCTION update_zotero_webhook_endpoints_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_zotero_webhook_endpoints_updated_at
    BEFORE UPDATE ON zotero.zotero_webhook_endpoints
    FOR EACH ROW
    EXECUTE FUNCTION update_zotero_webhook_endpoints_updated_at();

-- Add updated_at trigger for sync status
CREATE OR REPLACE FUNCTION update_zotero_sync_status_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_zotero_sync_status_updated_at
    BEFORE UPDATE ON zotero.zotero_sync_status
    FOR EACH ROW
    EXECUTE FUNCTION update_zotero_sync_status_updated_at();