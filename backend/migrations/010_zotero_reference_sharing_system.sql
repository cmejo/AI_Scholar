-- Migration: Add Zotero reference sharing system
-- Description: Creates tables for reference sharing between AI Scholar users, shared collections, and collaborative features

-- Create user reference shares table
CREATE TABLE IF NOT EXISTS zotero.zotero_user_reference_shares (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    reference_id VARCHAR NOT NULL REFERENCES zotero.zotero_items(id) ON DELETE CASCADE,
    owner_user_id VARCHAR NOT NULL, -- References users.id
    shared_with_user_id VARCHAR NOT NULL, -- References users.id
    permission_level VARCHAR(20) DEFAULT 'read', -- 'read', 'comment', 'edit'
    share_message TEXT,
    share_context JSONB DEFAULT '{}'::jsonb, -- Additional context about the share
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP, -- Optional expiration
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    share_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create shared reference collections table (research projects)
CREATE TABLE IF NOT EXISTS zotero.zotero_shared_reference_collections (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_user_id VARCHAR NOT NULL, -- References users.id
    collection_type VARCHAR(50) DEFAULT 'research_project', -- 'research_project', 'bibliography', 'reading_list', 'course_materials'
    is_public BOOLEAN DEFAULT FALSE,
    access_code VARCHAR(20), -- Optional access code for sharing
    visibility VARCHAR(20) DEFAULT 'private', -- 'private', 'shared', 'public'
    collaboration_settings JSONB DEFAULT '{}'::jsonb, -- Settings for collaboration
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    collection_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create collection collaborators table
CREATE TABLE IF NOT EXISTS zotero.zotero_collection_collaborators (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    collection_id VARCHAR NOT NULL REFERENCES zotero.zotero_shared_reference_collections(id) ON DELETE CASCADE,
    user_id VARCHAR NOT NULL, -- References users.id
    permission_level VARCHAR(20) DEFAULT 'read', -- 'read', 'comment', 'edit', 'admin'
    role VARCHAR(50) DEFAULT 'collaborator', -- 'owner', 'admin', 'editor', 'collaborator', 'viewer'
    invited_by VARCHAR NOT NULL, -- References users.id
    invitation_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'accepted', 'declined', 'removed'
    invitation_message TEXT,
    joined_at TIMESTAMP,
    last_activity TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    collaborator_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create collection references table (many-to-many)
CREATE TABLE IF NOT EXISTS zotero.zotero_shared_collection_references (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    collection_id VARCHAR NOT NULL REFERENCES zotero.zotero_shared_reference_collections(id) ON DELETE CASCADE,
    reference_id VARCHAR NOT NULL REFERENCES zotero.zotero_items(id) ON DELETE CASCADE,
    added_by VARCHAR NOT NULL, -- References users.id
    added_at TIMESTAMP DEFAULT NOW(),
    notes TEXT, -- Optional notes about why this reference was added
    tags JSONB DEFAULT '[]'::jsonb, -- User-defined tags for organization within collection
    sort_order INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT FALSE, -- Mark important references
    reference_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create reference discussions table
CREATE TABLE IF NOT EXISTS zotero.zotero_reference_discussions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    reference_id VARCHAR NOT NULL REFERENCES zotero.zotero_items(id) ON DELETE CASCADE,
    collection_id VARCHAR REFERENCES zotero.zotero_shared_reference_collections(id) ON DELETE CASCADE, -- Optional: discussion within a collection context
    user_id VARCHAR NOT NULL, -- References users.id
    discussion_type VARCHAR(20) DEFAULT 'comment', -- 'comment', 'question', 'suggestion', 'review'
    content TEXT NOT NULL,
    parent_discussion_id VARCHAR REFERENCES zotero.zotero_reference_discussions(id) ON DELETE CASCADE, -- For threaded discussions
    is_resolved BOOLEAN DEFAULT FALSE, -- For questions/suggestions
    resolved_by VARCHAR, -- References users.id
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    discussion_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create reference annotations sharing table
CREATE TABLE IF NOT EXISTS zotero.zotero_shared_reference_annotations (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    reference_id VARCHAR NOT NULL REFERENCES zotero.zotero_items(id) ON DELETE CASCADE,
    annotation_id VARCHAR REFERENCES zotero.zotero_annotations(id) ON DELETE CASCADE, -- Optional: link to existing annotation
    user_id VARCHAR NOT NULL, -- References users.id
    annotation_type VARCHAR(20) NOT NULL, -- 'highlight', 'note', 'bookmark', 'tag'
    content TEXT,
    position_data JSONB, -- Position in document (page, coordinates, etc.)
    color VARCHAR(20),
    is_public BOOLEAN DEFAULT FALSE, -- Whether annotation is visible to all collaborators
    shared_with_users JSONB DEFAULT '[]'::jsonb, -- Specific users who can see this annotation
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    annotation_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create sharing activity log table
CREATE TABLE IF NOT EXISTS zotero.zotero_sharing_activity_log (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR NOT NULL, -- References users.id
    activity_type VARCHAR(50) NOT NULL, -- 'share_reference', 'create_collection', 'add_collaborator', 'add_reference', 'comment', etc.
    target_type VARCHAR(50) NOT NULL, -- 'reference', 'collection', 'discussion', 'annotation'
    target_id VARCHAR NOT NULL, -- ID of the target object
    target_user_id VARCHAR, -- References users.id (for activities involving other users)
    collection_id VARCHAR REFERENCES zotero.zotero_shared_reference_collections(id) ON DELETE SET NULL, -- Optional collection context
    activity_description TEXT,
    activity_data JSONB DEFAULT '{}'::jsonb, -- Additional activity details
    created_at TIMESTAMP DEFAULT NOW(),
    ip_address VARCHAR(45), -- For security auditing
    user_agent TEXT -- For security auditing
);

-- Create reference sharing invitations table
CREATE TABLE IF NOT EXISTS zotero.zotero_reference_sharing_invitations (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    invitation_type VARCHAR(20) NOT NULL, -- 'reference_share', 'collection_invite'
    target_id VARCHAR NOT NULL, -- ID of reference or collection being shared
    invited_by VARCHAR NOT NULL, -- References users.id
    invited_user_email VARCHAR(255), -- Email of invited user (may not be registered yet)
    invited_user_id VARCHAR, -- References users.id (if user is registered)
    permission_level VARCHAR(20) DEFAULT 'read',
    invitation_message TEXT,
    invitation_token VARCHAR(255) UNIQUE NOT NULL, -- Unique token for invitation link
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'accepted', 'declined', 'expired', 'cancelled'
    expires_at TIMESTAMP NOT NULL,
    accepted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    invitation_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create reference sharing notifications table
CREATE TABLE IF NOT EXISTS zotero.zotero_sharing_notifications (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR NOT NULL, -- References users.id (recipient)
    notification_type VARCHAR(50) NOT NULL, -- 'reference_shared', 'collection_invite', 'new_comment', 'mention', etc.
    title VARCHAR(255) NOT NULL,
    message TEXT,
    target_type VARCHAR(50), -- 'reference', 'collection', 'discussion'
    target_id VARCHAR,
    sender_user_id VARCHAR, -- References users.id (sender)
    is_read BOOLEAN DEFAULT FALSE,
    is_dismissed BOOLEAN DEFAULT FALSE,
    action_url VARCHAR(500), -- URL to take action on the notification
    created_at TIMESTAMP DEFAULT NOW(),
    read_at TIMESTAMP,
    notification_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_reference_shares_owner ON zotero.zotero_user_reference_shares(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_user_reference_shares_shared_with ON zotero.zotero_user_reference_shares(shared_with_user_id);
CREATE INDEX IF NOT EXISTS idx_user_reference_shares_reference ON zotero.zotero_user_reference_shares(reference_id);
CREATE INDEX IF NOT EXISTS idx_user_reference_shares_active ON zotero.zotero_user_reference_shares(is_active);

CREATE INDEX IF NOT EXISTS idx_shared_collections_owner ON zotero.zotero_shared_reference_collections(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_shared_collections_type ON zotero.zotero_shared_reference_collections(collection_type);
CREATE INDEX IF NOT EXISTS idx_shared_collections_public ON zotero.zotero_shared_reference_collections(is_public);
CREATE INDEX IF NOT EXISTS idx_shared_collections_access_code ON zotero.zotero_shared_reference_collections(access_code) WHERE access_code IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_collection_collaborators_collection ON zotero.zotero_collection_collaborators(collection_id);
CREATE INDEX IF NOT EXISTS idx_collection_collaborators_user ON zotero.zotero_collection_collaborators(user_id);
CREATE INDEX IF NOT EXISTS idx_collection_collaborators_status ON zotero.zotero_collection_collaborators(invitation_status);

CREATE INDEX IF NOT EXISTS idx_shared_collection_references_collection ON zotero.zotero_shared_collection_references(collection_id);
CREATE INDEX IF NOT EXISTS idx_shared_collection_references_reference ON zotero.zotero_shared_collection_references(reference_id);
CREATE INDEX IF NOT EXISTS idx_shared_collection_references_added_by ON zotero.zotero_shared_collection_references(added_by);

CREATE INDEX IF NOT EXISTS idx_reference_discussions_reference ON zotero.zotero_reference_discussions(reference_id);
CREATE INDEX IF NOT EXISTS idx_reference_discussions_collection ON zotero.zotero_reference_discussions(collection_id);
CREATE INDEX IF NOT EXISTS idx_reference_discussions_user ON zotero.zotero_reference_discussions(user_id);
CREATE INDEX IF NOT EXISTS idx_reference_discussions_parent ON zotero.zotero_reference_discussions(parent_discussion_id);

CREATE INDEX IF NOT EXISTS idx_shared_annotations_reference ON zotero.zotero_shared_reference_annotations(reference_id);
CREATE INDEX IF NOT EXISTS idx_shared_annotations_user ON zotero.zotero_shared_reference_annotations(user_id);
CREATE INDEX IF NOT EXISTS idx_shared_annotations_public ON zotero.zotero_shared_reference_annotations(is_public);

CREATE INDEX IF NOT EXISTS idx_sharing_activity_user ON zotero.zotero_sharing_activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_sharing_activity_type ON zotero.zotero_sharing_activity_log(activity_type);
CREATE INDEX IF NOT EXISTS idx_sharing_activity_target ON zotero.zotero_sharing_activity_log(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_sharing_activity_created ON zotero.zotero_sharing_activity_log(created_at);

CREATE INDEX IF NOT EXISTS idx_sharing_invitations_token ON zotero.zotero_reference_sharing_invitations(invitation_token);
CREATE INDEX IF NOT EXISTS idx_sharing_invitations_email ON zotero.zotero_reference_sharing_invitations(invited_user_email);
CREATE INDEX IF NOT EXISTS idx_sharing_invitations_user ON zotero.zotero_reference_sharing_invitations(invited_user_id);
CREATE INDEX IF NOT EXISTS idx_sharing_invitations_status ON zotero.zotero_reference_sharing_invitations(status);

CREATE INDEX IF NOT EXISTS idx_sharing_notifications_user ON zotero.zotero_sharing_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_sharing_notifications_read ON zotero.zotero_sharing_notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_sharing_notifications_type ON zotero.zotero_sharing_notifications(notification_type);

-- Add updated_at triggers
CREATE OR REPLACE FUNCTION update_zotero_user_reference_shares_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_zotero_user_reference_shares_updated_at
    BEFORE UPDATE ON zotero.zotero_user_reference_shares
    FOR EACH ROW
    EXECUTE FUNCTION update_zotero_user_reference_shares_updated_at();

CREATE OR REPLACE FUNCTION update_zotero_shared_reference_collections_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_zotero_shared_reference_collections_updated_at
    BEFORE UPDATE ON zotero.zotero_shared_reference_collections
    FOR EACH ROW
    EXECUTE FUNCTION update_zotero_shared_reference_collections_updated_at();

CREATE OR REPLACE FUNCTION update_zotero_collection_collaborators_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_zotero_collection_collaborators_updated_at
    BEFORE UPDATE ON zotero.zotero_collection_collaborators
    FOR EACH ROW
    EXECUTE FUNCTION update_zotero_collection_collaborators_updated_at();

CREATE OR REPLACE FUNCTION update_zotero_reference_discussions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_zotero_reference_discussions_updated_at
    BEFORE UPDATE ON zotero.zotero_reference_discussions
    FOR EACH ROW
    EXECUTE FUNCTION update_zotero_reference_discussions_updated_at();

CREATE OR REPLACE FUNCTION update_zotero_shared_reference_annotations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_zotero_shared_reference_annotations_updated_at
    BEFORE UPDATE ON zotero.zotero_shared_reference_annotations
    FOR EACH ROW
    EXECUTE FUNCTION update_zotero_shared_reference_annotations_updated_at();

-- Add constraints
ALTER TABLE zotero.zotero_user_reference_shares 
ADD CONSTRAINT unique_user_reference_share 
UNIQUE (reference_id, owner_user_id, shared_with_user_id);

ALTER TABLE zotero.zotero_collection_collaborators 
ADD CONSTRAINT unique_collection_collaborator 
UNIQUE (collection_id, user_id);

ALTER TABLE zotero.zotero_shared_collection_references 
ADD CONSTRAINT unique_collection_reference 
UNIQUE (collection_id, reference_id);