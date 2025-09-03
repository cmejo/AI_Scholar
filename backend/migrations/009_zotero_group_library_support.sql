-- Migration: Add Zotero group library support
-- Description: Creates tables and updates for group library management, permissions, and collaboration

-- Add group-specific fields to existing zotero_libraries table
ALTER TABLE zotero.zotero_libraries 
ADD COLUMN IF NOT EXISTS group_permissions JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS group_settings JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS member_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS group_description TEXT,
ADD COLUMN IF NOT EXISTS group_url VARCHAR(500);

-- Create group members table
CREATE TABLE IF NOT EXISTS zotero.zotero_group_members (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    library_id VARCHAR NOT NULL REFERENCES zotero.zotero_libraries(id) ON DELETE CASCADE,
    user_id VARCHAR NOT NULL, -- References users.id
    zotero_user_id VARCHAR(50) NOT NULL,
    member_role VARCHAR(50) NOT NULL, -- 'owner', 'admin', 'member', 'reader'
    permissions JSONB DEFAULT '{}'::jsonb, -- Specific permissions for this member
    join_date TIMESTAMP DEFAULT NOW(),
    last_activity TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    invitation_status VARCHAR(20) DEFAULT 'active', -- 'pending', 'active', 'declined', 'removed'
    invited_by VARCHAR, -- References users.id
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    member_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create group library sync settings table
CREATE TABLE IF NOT EXISTS zotero.zotero_group_sync_settings (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    library_id VARCHAR NOT NULL REFERENCES zotero.zotero_libraries(id) ON DELETE CASCADE,
    user_id VARCHAR NOT NULL, -- References users.id
    sync_enabled BOOLEAN DEFAULT TRUE,
    sync_frequency_minutes INTEGER DEFAULT 60,
    sync_collections BOOLEAN DEFAULT TRUE,
    sync_items BOOLEAN DEFAULT TRUE,
    sync_attachments BOOLEAN DEFAULT FALSE, -- Group attachments might be restricted
    sync_annotations BOOLEAN DEFAULT TRUE,
    auto_resolve_conflicts BOOLEAN DEFAULT TRUE,
    conflict_resolution_strategy VARCHAR(50) DEFAULT 'zotero_wins', -- 'zotero_wins', 'manual'
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    settings_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create group permissions template table
CREATE TABLE IF NOT EXISTS zotero.zotero_group_permission_templates (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    template_name VARCHAR(100) NOT NULL,
    template_description TEXT,
    permissions JSONB NOT NULL, -- Permission definitions
    is_default BOOLEAN DEFAULT FALSE,
    is_system BOOLEAN DEFAULT FALSE, -- System templates cannot be deleted
    created_by VARCHAR, -- References users.id
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create group activity log table
CREATE TABLE IF NOT EXISTS zotero.zotero_group_activity_log (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    library_id VARCHAR NOT NULL REFERENCES zotero.zotero_libraries(id) ON DELETE CASCADE,
    user_id VARCHAR NOT NULL, -- References users.id
    activity_type VARCHAR(50) NOT NULL, -- 'member_added', 'member_removed', 'permission_changed', 'item_added', 'item_updated', 'item_deleted'
    target_type VARCHAR(50), -- 'member', 'item', 'collection', 'permission'
    target_id VARCHAR,
    activity_description TEXT,
    old_data JSONB,
    new_data JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    activity_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create group library access control table
CREATE TABLE IF NOT EXISTS zotero.zotero_group_access_control (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    library_id VARCHAR NOT NULL REFERENCES zotero.zotero_libraries(id) ON DELETE CASCADE,
    user_id VARCHAR NOT NULL, -- References users.id
    access_type VARCHAR(50) NOT NULL, -- 'read', 'write', 'admin', 'owner'
    resource_type VARCHAR(50) NOT NULL, -- 'library', 'collection', 'item', 'attachment'
    resource_id VARCHAR, -- ID of the specific resource (optional for library-level access)
    granted_by VARCHAR, -- References users.id
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP, -- Optional expiration
    is_active BOOLEAN DEFAULT TRUE,
    access_conditions JSONB DEFAULT '{}'::jsonb, -- Additional conditions or restrictions
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create group sync conflicts table (extends general sync conflicts for group-specific handling)
CREATE TABLE IF NOT EXISTS zotero.zotero_group_sync_conflicts (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    library_id VARCHAR NOT NULL REFERENCES zotero.zotero_libraries(id) ON DELETE CASCADE,
    sync_job_id VARCHAR REFERENCES zotero.zotero_sync_jobs(id) ON DELETE CASCADE,
    conflict_type VARCHAR(50) NOT NULL, -- 'permission_conflict', 'member_conflict', 'group_settings_conflict'
    conflicting_user_id VARCHAR, -- References users.id
    conflict_description TEXT,
    local_data JSONB,
    remote_data JSONB,
    resolution_strategy VARCHAR(50) DEFAULT 'admin_decides', -- 'admin_decides', 'owner_decides', 'majority_vote'
    resolution_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'resolved', 'escalated'
    resolved_by VARCHAR, -- References users.id
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    conflict_metadata JSONB DEFAULT '{}'::jsonb
);

-- Insert default permission templates
INSERT INTO zotero.zotero_group_permission_templates (template_name, template_description, permissions, is_default, is_system) VALUES
('Owner', 'Full control over group library', '{"read": true, "write": true, "delete": true, "admin": true, "manage_members": true, "manage_permissions": true, "manage_settings": true}', false, true),
('Admin', 'Administrative access with member management', '{"read": true, "write": true, "delete": true, "admin": true, "manage_members": true, "manage_permissions": true, "manage_settings": false}', false, true),
('Member', 'Read and write access to library content', '{"read": true, "write": true, "delete": false, "admin": false, "manage_members": false, "manage_permissions": false, "manage_settings": false}', true, true),
('Reader', 'Read-only access to library content', '{"read": true, "write": false, "delete": false, "admin": false, "manage_members": false, "manage_permissions": false, "manage_settings": false}', false, true);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_group_members_library_id ON zotero.zotero_group_members(library_id);
CREATE INDEX IF NOT EXISTS idx_group_members_user_id ON zotero.zotero_group_members(user_id);
CREATE INDEX IF NOT EXISTS idx_group_members_role ON zotero.zotero_group_members(member_role);
CREATE INDEX IF NOT EXISTS idx_group_members_active ON zotero.zotero_group_members(is_active);

CREATE INDEX IF NOT EXISTS idx_group_sync_settings_library_id ON zotero.zotero_group_sync_settings(library_id);
CREATE INDEX IF NOT EXISTS idx_group_sync_settings_user_id ON zotero.zotero_group_sync_settings(user_id);

CREATE INDEX IF NOT EXISTS idx_group_activity_library_id ON zotero.zotero_group_activity_log(library_id);
CREATE INDEX IF NOT EXISTS idx_group_activity_user_id ON zotero.zotero_group_activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_group_activity_type ON zotero.zotero_group_activity_log(activity_type);
CREATE INDEX IF NOT EXISTS idx_group_activity_created_at ON zotero.zotero_group_activity_log(created_at);

CREATE INDEX IF NOT EXISTS idx_group_access_library_id ON zotero.zotero_group_access_control(library_id);
CREATE INDEX IF NOT EXISTS idx_group_access_user_id ON zotero.zotero_group_access_control(user_id);
CREATE INDEX IF NOT EXISTS idx_group_access_type ON zotero.zotero_group_access_control(access_type);
CREATE INDEX IF NOT EXISTS idx_group_access_active ON zotero.zotero_group_access_control(is_active);

CREATE INDEX IF NOT EXISTS idx_group_sync_conflicts_library_id ON zotero.zotero_group_sync_conflicts(library_id);
CREATE INDEX IF NOT EXISTS idx_group_sync_conflicts_status ON zotero.zotero_group_sync_conflicts(resolution_status);

-- Add updated_at triggers
CREATE OR REPLACE FUNCTION update_zotero_group_members_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_zotero_group_members_updated_at
    BEFORE UPDATE ON zotero.zotero_group_members
    FOR EACH ROW
    EXECUTE FUNCTION update_zotero_group_members_updated_at();

CREATE OR REPLACE FUNCTION update_zotero_group_sync_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_zotero_group_sync_settings_updated_at
    BEFORE UPDATE ON zotero.zotero_group_sync_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_zotero_group_sync_settings_updated_at();

CREATE OR REPLACE FUNCTION update_zotero_group_access_control_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_zotero_group_access_control_updated_at
    BEFORE UPDATE ON zotero.zotero_group_access_control
    FOR EACH ROW
    EXECUTE FUNCTION update_zotero_group_access_control_updated_at();

-- Add constraint to ensure only one owner per group
CREATE UNIQUE INDEX IF NOT EXISTS idx_group_members_unique_owner 
ON zotero.zotero_group_members(library_id) 
WHERE member_role = 'owner' AND is_active = true;

-- Add constraint to ensure user can only be a member once per group
CREATE UNIQUE INDEX IF NOT EXISTS idx_group_members_unique_user_library 
ON zotero.zotero_group_members(library_id, user_id) 
WHERE is_active = true;