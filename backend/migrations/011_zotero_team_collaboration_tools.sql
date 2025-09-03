-- Migration: Add Zotero team collaboration tools
-- Description: Creates tables for team workspaces, modification tracking, history, and conflict resolution

-- Create team workspaces table
CREATE TABLE IF NOT EXISTS zotero.zotero_team_workspaces (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_user_id VARCHAR NOT NULL, -- References users.id
    workspace_type VARCHAR(50) DEFAULT 'research_team', -- 'research_team', 'course', 'department', 'project'
    settings JSONB DEFAULT '{}'::jsonb, -- Workspace-specific settings
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    workspace_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create team workspace members table
CREATE TABLE IF NOT EXISTS zotero.zotero_team_workspace_members (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    workspace_id VARCHAR NOT NULL REFERENCES zotero.zotero_team_workspaces(id) ON DELETE CASCADE,
    user_id VARCHAR NOT NULL, -- References users.id
    role VARCHAR(50) NOT NULL, -- 'owner', 'admin', 'editor', 'member', 'viewer'
    permissions JSONB DEFAULT '{}'::jsonb, -- Specific permissions
    joined_at TIMESTAMP DEFAULT NOW(),
    last_activity TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    invited_by VARCHAR, -- References users.id
    invitation_status VARCHAR(20) DEFAULT 'active', -- 'pending', 'active', 'declined', 'removed'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    member_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create team workspace collections table (links collections to workspaces)
CREATE TABLE IF NOT EXISTS zotero.zotero_team_workspace_collections (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    workspace_id VARCHAR NOT NULL REFERENCES zotero.zotero_team_workspaces(id) ON DELETE CASCADE,
    collection_id VARCHAR NOT NULL REFERENCES zotero.zotero_shared_reference_collections(id) ON DELETE CASCADE,
    added_by VARCHAR NOT NULL, -- References users.id
    added_at TIMESTAMP DEFAULT NOW(),
    collection_role VARCHAR(50) DEFAULT 'shared', -- 'primary', 'shared', 'reference'
    is_featured BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    workspace_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create modification tracking table
CREATE TABLE IF NOT EXISTS zotero.zotero_modification_tracking (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    target_type VARCHAR(50) NOT NULL, -- 'reference', 'collection', 'annotation', 'discussion'
    target_id VARCHAR NOT NULL, -- ID of the modified object
    workspace_id VARCHAR REFERENCES zotero.zotero_team_workspaces(id) ON DELETE SET NULL,
    collection_id VARCHAR REFERENCES zotero.zotero_shared_reference_collections(id) ON DELETE SET NULL,
    user_id VARCHAR NOT NULL, -- References users.id
    modification_type VARCHAR(50) NOT NULL, -- 'create', 'update', 'delete', 'move', 'share'
    field_changes JSONB DEFAULT '{}'::jsonb, -- Specific field changes
    old_values JSONB DEFAULT '{}'::jsonb, -- Previous values
    new_values JSONB DEFAULT '{}'::jsonb, -- New values
    change_summary TEXT, -- Human-readable summary of changes
    version_number INTEGER DEFAULT 1, -- Version tracking
    is_conflict BOOLEAN DEFAULT FALSE, -- Whether this change caused a conflict
    conflict_resolution VARCHAR(50), -- How conflict was resolved
    created_at TIMESTAMP DEFAULT NOW(),
    modification_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create collaborative editing sessions table
CREATE TABLE IF NOT EXISTS zotero.zotero_collaborative_editing_sessions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    target_type VARCHAR(50) NOT NULL, -- 'reference', 'collection', 'annotation'
    target_id VARCHAR NOT NULL, -- ID of the object being edited
    workspace_id VARCHAR REFERENCES zotero.zotero_team_workspaces(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL, -- Unique session identifier
    active_users JSONB DEFAULT '[]'::jsonb, -- List of currently active users
    lock_status VARCHAR(20) DEFAULT 'unlocked', -- 'unlocked', 'soft_lock', 'hard_lock'
    locked_by VARCHAR, -- References users.id
    locked_at TIMESTAMP,
    lock_expires_at TIMESTAMP,
    session_data JSONB DEFAULT '{}'::jsonb, -- Real-time collaboration data
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    session_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create conflict resolution table
CREATE TABLE IF NOT EXISTS zotero.zotero_collaboration_conflicts (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    target_type VARCHAR(50) NOT NULL, -- 'reference', 'collection', 'annotation'
    target_id VARCHAR NOT NULL, -- ID of the conflicted object
    workspace_id VARCHAR REFERENCES zotero.zotero_team_workspaces(id) ON DELETE CASCADE,
    conflict_type VARCHAR(50) NOT NULL, -- 'concurrent_edit', 'version_mismatch', 'permission_conflict'
    conflicting_users JSONB NOT NULL, -- List of users involved in conflict
    conflict_data JSONB NOT NULL, -- Details of the conflicting changes
    resolution_strategy VARCHAR(50) DEFAULT 'manual', -- 'manual', 'auto_merge', 'latest_wins', 'admin_decides'
    resolution_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'resolved', 'escalated'
    resolved_by VARCHAR, -- References users.id
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    conflict_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create team collaboration history table
CREATE TABLE IF NOT EXISTS zotero.zotero_team_collaboration_history (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    workspace_id VARCHAR NOT NULL REFERENCES zotero.zotero_team_workspaces(id) ON DELETE CASCADE,
    user_id VARCHAR NOT NULL, -- References users.id
    action_type VARCHAR(50) NOT NULL, -- 'join_workspace', 'leave_workspace', 'create_collection', 'edit_reference', etc.
    target_type VARCHAR(50), -- 'workspace', 'collection', 'reference', 'member'
    target_id VARCHAR,
    action_description TEXT,
    action_data JSONB DEFAULT '{}'::jsonb,
    impact_level VARCHAR(20) DEFAULT 'low', -- 'low', 'medium', 'high', 'critical'
    created_at TIMESTAMP DEFAULT NOW(),
    history_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create team workspace settings table
CREATE TABLE IF NOT EXISTS zotero.zotero_team_workspace_settings (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    workspace_id VARCHAR NOT NULL REFERENCES zotero.zotero_team_workspaces(id) ON DELETE CASCADE,
    setting_category VARCHAR(50) NOT NULL, -- 'collaboration', 'permissions', 'notifications', 'sync'
    setting_key VARCHAR(100) NOT NULL,
    setting_value JSONB NOT NULL,
    set_by VARCHAR NOT NULL, -- References users.id
    is_locked BOOLEAN DEFAULT FALSE, -- Whether setting can be changed by non-admins
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    setting_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create team workspace invitations table
CREATE TABLE IF NOT EXISTS zotero.zotero_team_workspace_invitations (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    workspace_id VARCHAR NOT NULL REFERENCES zotero.zotero_team_workspaces(id) ON DELETE CASCADE,
    invited_by VARCHAR NOT NULL, -- References users.id
    invited_user_email VARCHAR(255), -- Email of invited user
    invited_user_id VARCHAR, -- References users.id (if user is registered)
    role VARCHAR(50) NOT NULL,
    permissions JSONB DEFAULT '{}'::jsonb,
    invitation_message TEXT,
    invitation_token VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'accepted', 'declined', 'expired', 'cancelled'
    expires_at TIMESTAMP NOT NULL,
    accepted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    invitation_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create team workspace notifications table
CREATE TABLE IF NOT EXISTS zotero.zotero_team_workspace_notifications (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    workspace_id VARCHAR NOT NULL REFERENCES zotero.zotero_team_workspaces(id) ON DELETE CASCADE,
    user_id VARCHAR NOT NULL, -- References users.id (recipient)
    notification_type VARCHAR(50) NOT NULL, -- 'workspace_invite', 'conflict_detected', 'member_joined', etc.
    title VARCHAR(255) NOT NULL,
    message TEXT,
    priority VARCHAR(20) DEFAULT 'normal', -- 'low', 'normal', 'high', 'urgent'
    target_type VARCHAR(50), -- 'workspace', 'collection', 'reference', 'conflict'
    target_id VARCHAR,
    sender_user_id VARCHAR, -- References users.id (sender)
    is_read BOOLEAN DEFAULT FALSE,
    is_dismissed BOOLEAN DEFAULT FALSE,
    action_required BOOLEAN DEFAULT FALSE, -- Whether user action is required
    action_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    read_at TIMESTAMP,
    notification_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_team_workspaces_owner ON zotero.zotero_team_workspaces(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_team_workspaces_type ON zotero.zotero_team_workspaces(workspace_type);
CREATE INDEX IF NOT EXISTS idx_team_workspaces_active ON zotero.zotero_team_workspaces(is_active);

CREATE INDEX IF NOT EXISTS idx_team_workspace_members_workspace ON zotero.zotero_team_workspace_members(workspace_id);
CREATE INDEX IF NOT EXISTS idx_team_workspace_members_user ON zotero.zotero_team_workspace_members(user_id);
CREATE INDEX IF NOT EXISTS idx_team_workspace_members_role ON zotero.zotero_team_workspace_members(role);
CREATE INDEX IF NOT EXISTS idx_team_workspace_members_active ON zotero.zotero_team_workspace_members(is_active);

CREATE INDEX IF NOT EXISTS idx_team_workspace_collections_workspace ON zotero.zotero_team_workspace_collections(workspace_id);
CREATE INDEX IF NOT EXISTS idx_team_workspace_collections_collection ON zotero.zotero_team_workspace_collections(collection_id);

CREATE INDEX IF NOT EXISTS idx_modification_tracking_target ON zotero.zotero_modification_tracking(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_modification_tracking_workspace ON zotero.zotero_modification_tracking(workspace_id);
CREATE INDEX IF NOT EXISTS idx_modification_tracking_user ON zotero.zotero_modification_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_modification_tracking_created ON zotero.zotero_modification_tracking(created_at);
CREATE INDEX IF NOT EXISTS idx_modification_tracking_conflict ON zotero.zotero_modification_tracking(is_conflict);

CREATE INDEX IF NOT EXISTS idx_collaborative_editing_target ON zotero.zotero_collaborative_editing_sessions(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_collaborative_editing_workspace ON zotero.zotero_collaborative_editing_sessions(workspace_id);
CREATE INDEX IF NOT EXISTS idx_collaborative_editing_token ON zotero.zotero_collaborative_editing_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_collaborative_editing_lock ON zotero.zotero_collaborative_editing_sessions(lock_status);

CREATE INDEX IF NOT EXISTS idx_collaboration_conflicts_target ON zotero.zotero_collaboration_conflicts(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_collaboration_conflicts_workspace ON zotero.zotero_collaboration_conflicts(workspace_id);
CREATE INDEX IF NOT EXISTS idx_collaboration_conflicts_status ON zotero.zotero_collaboration_conflicts(resolution_status);

CREATE INDEX IF NOT EXISTS idx_team_collaboration_history_workspace ON zotero.zotero_team_collaboration_history(workspace_id);
CREATE INDEX IF NOT EXISTS idx_team_collaboration_history_user ON zotero.zotero_team_collaboration_history(user_id);
CREATE INDEX IF NOT EXISTS idx_team_collaboration_history_created ON zotero.zotero_team_collaboration_history(created_at);
CREATE INDEX IF NOT EXISTS idx_team_collaboration_history_impact ON zotero.zotero_team_collaboration_history(impact_level);

CREATE INDEX IF NOT EXISTS idx_team_workspace_settings_workspace ON zotero.zotero_team_workspace_settings(workspace_id);
CREATE INDEX IF NOT EXISTS idx_team_workspace_settings_category ON zotero.zotero_team_workspace_settings(setting_category);

CREATE INDEX IF NOT EXISTS idx_team_workspace_invitations_workspace ON zotero.zotero_team_workspace_invitations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_team_workspace_invitations_token ON zotero.zotero_team_workspace_invitations(invitation_token);
CREATE INDEX IF NOT EXISTS idx_team_workspace_invitations_email ON zotero.zotero_team_workspace_invitations(invited_user_email);
CREATE INDEX IF NOT EXISTS idx_team_workspace_invitations_status ON zotero.zotero_team_workspace_invitations(status);

CREATE INDEX IF NOT EXISTS idx_team_workspace_notifications_workspace ON zotero.zotero_team_workspace_notifications(workspace_id);
CREATE INDEX IF NOT EXISTS idx_team_workspace_notifications_user ON zotero.zotero_team_workspace_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_team_workspace_notifications_read ON zotero.zotero_team_workspace_notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_team_workspace_notifications_priority ON zotero.zotero_team_workspace_notifications(priority);

-- Add updated_at triggers
CREATE OR REPLACE FUNCTION update_zotero_team_workspaces_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_zotero_team_workspaces_updated_at
    BEFORE UPDATE ON zotero.zotero_team_workspaces
    FOR EACH ROW
    EXECUTE FUNCTION update_zotero_team_workspaces_updated_at();

CREATE OR REPLACE FUNCTION update_zotero_team_workspace_members_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_zotero_team_workspace_members_updated_at
    BEFORE UPDATE ON zotero.zotero_team_workspace_members
    FOR EACH ROW
    EXECUTE FUNCTION update_zotero_team_workspace_members_updated_at();

CREATE OR REPLACE FUNCTION update_zotero_collaborative_editing_sessions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_zotero_collaborative_editing_sessions_updated_at
    BEFORE UPDATE ON zotero.zotero_collaborative_editing_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_zotero_collaborative_editing_sessions_updated_at();

CREATE OR REPLACE FUNCTION update_zotero_collaboration_conflicts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_zotero_collaboration_conflicts_updated_at
    BEFORE UPDATE ON zotero.zotero_collaboration_conflicts
    FOR EACH ROW
    EXECUTE FUNCTION update_zotero_collaboration_conflicts_updated_at();

CREATE OR REPLACE FUNCTION update_zotero_team_workspace_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_zotero_team_workspace_settings_updated_at
    BEFORE UPDATE ON zotero.zotero_team_workspace_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_zotero_team_workspace_settings_updated_at();

-- Add constraints
ALTER TABLE zotero.zotero_team_workspace_members 
ADD CONSTRAINT unique_workspace_member 
UNIQUE (workspace_id, user_id);

ALTER TABLE zotero.zotero_team_workspace_collections 
ADD CONSTRAINT unique_workspace_collection 
UNIQUE (workspace_id, collection_id);

ALTER TABLE zotero.zotero_team_workspace_settings 
ADD CONSTRAINT unique_workspace_setting 
UNIQUE (workspace_id, setting_category, setting_key);

-- Add check constraints
ALTER TABLE zotero.zotero_team_workspace_members 
ADD CONSTRAINT check_valid_role 
CHECK (role IN ('owner', 'admin', 'editor', 'member', 'viewer'));

ALTER TABLE zotero.zotero_collaborative_editing_sessions 
ADD CONSTRAINT check_valid_lock_status 
CHECK (lock_status IN ('unlocked', 'soft_lock', 'hard_lock'));

ALTER TABLE zotero.zotero_collaboration_conflicts 
ADD CONSTRAINT check_valid_resolution_status 
CHECK (resolution_status IN ('pending', 'resolved', 'escalated'));

-- Insert default workspace settings templates
INSERT INTO zotero.zotero_team_workspace_settings (id, workspace_id, setting_category, setting_key, setting_value, set_by, is_locked) VALUES
('default-collab-1', 'default', 'collaboration', 'allow_concurrent_editing', 'true', 'system', true),
('default-collab-2', 'default', 'collaboration', 'auto_save_interval', '30', 'system', false),
('default-collab-3', 'default', 'collaboration', 'conflict_resolution_strategy', 'manual', 'system', false),
('default-perm-1', 'default', 'permissions', 'default_member_role', 'member', 'system', false),
('default-perm-2', 'default', 'permissions', 'allow_member_invite', 'false', 'system', false),
('default-notif-1', 'default', 'notifications', 'notify_on_conflicts', 'true', 'system', false),
('default-notif-2', 'default', 'notifications', 'notify_on_member_join', 'true', 'system', false),
('default-sync-1', 'default', 'sync', 'auto_sync_enabled', 'true', 'system', false),
('default-sync-2', 'default', 'sync', 'sync_frequency_minutes', '15', 'system', false)
ON CONFLICT (workspace_id, setting_category, setting_key) DO NOTHING;