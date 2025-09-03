-- Migration for Zotero annotation synchronization and collaboration features
-- This migration adds tables for annotation sync tracking and collaboration

-- Add annotation sync tracking table
CREATE TABLE IF NOT EXISTS zotero.zotero_annotation_sync_log (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    annotation_id VARCHAR NOT NULL REFERENCES zotero.zotero_annotations(id) ON DELETE CASCADE,
    sync_type VARCHAR(20) NOT NULL, -- 'import', 'export', 'update', 'delete'
    sync_status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'failed'
    zotero_annotation_version INTEGER,
    local_annotation_version INTEGER,
    sync_direction VARCHAR(20) NOT NULL, -- 'from_zotero', 'to_zotero', 'bidirectional'
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    sync_metadata JSONB DEFAULT '{}'::jsonb
);

-- Add annotation collaboration table
CREATE TABLE IF NOT EXISTS zotero.zotero_annotation_collaborations (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    annotation_id VARCHAR NOT NULL REFERENCES zotero.zotero_annotations(id) ON DELETE CASCADE,
    user_id VARCHAR NOT NULL, -- References users.id
    collaboration_type VARCHAR(20) NOT NULL, -- 'comment', 'reply', 'edit', 'share'
    content TEXT,
    parent_collaboration_id VARCHAR REFERENCES zotero.zotero_annotation_collaborations(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Add annotation sharing table
CREATE TABLE IF NOT EXISTS zotero.zotero_annotation_shares (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    annotation_id VARCHAR NOT NULL REFERENCES zotero.zotero_annotations(id) ON DELETE CASCADE,
    owner_user_id VARCHAR NOT NULL, -- References users.id
    shared_with_user_id VARCHAR NOT NULL, -- References users.id
    permission_level VARCHAR(20) DEFAULT 'read', -- 'read', 'comment', 'edit'
    share_message TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Add annotation change history table
CREATE TABLE IF NOT EXISTS zotero.zotero_annotation_history (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    annotation_id VARCHAR NOT NULL REFERENCES zotero.zotero_annotations(id) ON DELETE CASCADE,
    user_id VARCHAR NOT NULL, -- References users.id
    change_type VARCHAR(20) NOT NULL, -- 'create', 'update', 'delete', 'comment'
    old_content JSONB,
    new_content JSONB,
    change_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_annotation_sync_log_annotation_id ON zotero.zotero_annotation_sync_log(annotation_id);
CREATE INDEX IF NOT EXISTS idx_annotation_sync_log_status ON zotero.zotero_annotation_sync_log(sync_status);
CREATE INDEX IF NOT EXISTS idx_annotation_sync_log_created_at ON zotero.zotero_annotation_sync_log(created_at);

CREATE INDEX IF NOT EXISTS idx_annotation_collaborations_annotation_id ON zotero.zotero_annotation_collaborations(annotation_id);
CREATE INDEX IF NOT EXISTS idx_annotation_collaborations_user_id ON zotero.zotero_annotation_collaborations(user_id);
CREATE INDEX IF NOT EXISTS idx_annotation_collaborations_type ON zotero.zotero_annotation_collaborations(collaboration_type);

CREATE INDEX IF NOT EXISTS idx_annotation_shares_annotation_id ON zotero.zotero_annotation_shares(annotation_id);
CREATE INDEX IF NOT EXISTS idx_annotation_shares_owner ON zotero.zotero_annotation_shares(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_annotation_shares_shared_with ON zotero.zotero_annotation_shares(shared_with_user_id);

CREATE INDEX IF NOT EXISTS idx_annotation_history_annotation_id ON zotero.zotero_annotation_history(annotation_id);
CREATE INDEX IF NOT EXISTS idx_annotation_history_user_id ON zotero.zotero_annotation_history(user_id);
CREATE INDEX IF NOT EXISTS idx_annotation_history_created_at ON zotero.zotero_annotation_history(created_at);

-- Add updated_at trigger for collaboration table
CREATE OR REPLACE FUNCTION update_annotation_collaboration_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_annotation_collaboration_updated_at
    BEFORE UPDATE ON zotero.zotero_annotation_collaborations
    FOR EACH ROW
    EXECUTE FUNCTION update_annotation_collaboration_updated_at();

-- Add updated_at trigger for shares table
CREATE OR REPLACE FUNCTION update_annotation_share_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_annotation_share_updated_at
    BEFORE UPDATE ON zotero.zotero_annotation_shares
    FOR EACH ROW
    EXECUTE FUNCTION update_annotation_share_updated_at();