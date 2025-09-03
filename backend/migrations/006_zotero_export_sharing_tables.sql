-- Migration: Add Zotero export and sharing tables
-- Task 8.3: Build export and sharing capabilities

-- Create shared references table
CREATE TABLE IF NOT EXISTS zotero.zotero_shared_references (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    reference_id VARCHAR NOT NULL REFERENCES zotero.zotero_items(id) ON DELETE CASCADE,
    owner_user_id VARCHAR NOT NULL,
    shared_with_user_id VARCHAR NOT NULL,
    permission_level VARCHAR(20) DEFAULT 'read' CHECK (permission_level IN ('read', 'comment', 'edit')),
    message TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create shared collections table
CREATE TABLE IF NOT EXISTS zotero.zotero_shared_collections (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_user_id VARCHAR NOT NULL,
    collection_type VARCHAR(50) DEFAULT 'research_project' CHECK (collection_type IN ('research_project', 'bibliography', 'reading_list')),
    is_public BOOLEAN DEFAULT false,
    access_code VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create collection collaborators table
CREATE TABLE IF NOT EXISTS zotero.zotero_collection_collaborators (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    collection_id VARCHAR NOT NULL REFERENCES zotero.zotero_shared_collections(id) ON DELETE CASCADE,
    user_id VARCHAR NOT NULL,
    permission_level VARCHAR(20) DEFAULT 'read' CHECK (permission_level IN ('read', 'comment', 'edit', 'admin')),
    invited_by VARCHAR NOT NULL,
    invitation_status VARCHAR(20) DEFAULT 'pending' CHECK (invitation_status IN ('pending', 'accepted', 'declined')),
    joined_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create conversation exports table
CREATE TABLE IF NOT EXISTS zotero.zotero_conversation_exports (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR NOT NULL,
    conversation_id VARCHAR NOT NULL,
    export_format VARCHAR(20) DEFAULT 'json' CHECK (export_format IN ('json', 'pdf', 'docx', 'html')),
    citation_style VARCHAR(50) DEFAULT 'apa',
    export_data JSONB NOT NULL,
    file_path TEXT,
    download_count INTEGER DEFAULT 0,
    last_downloaded TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create collection references junction table
CREATE TABLE IF NOT EXISTS zotero.zotero_collection_references (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    collection_id VARCHAR NOT NULL REFERENCES zotero.zotero_shared_collections(id) ON DELETE CASCADE,
    reference_id VARCHAR NOT NULL REFERENCES zotero.zotero_items(id) ON DELETE CASCADE,
    added_by VARCHAR NOT NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(collection_id, reference_id)
);

-- Create sharing activity audit table
CREATE TABLE IF NOT EXISTS zotero.zotero_sharing_activity (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id VARCHAR NOT NULL,
    target_user_id VARCHAR,
    activity_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_shared_references_owner ON zotero.zotero_shared_references(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_shared_references_shared_with ON zotero.zotero_shared_references(shared_with_user_id);
CREATE INDEX IF NOT EXISTS idx_shared_references_reference ON zotero.zotero_shared_references(reference_id);
CREATE INDEX IF NOT EXISTS idx_shared_references_active ON zotero.zotero_shared_references(is_active) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_shared_collections_owner ON zotero.zotero_shared_collections(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_shared_collections_type ON zotero.zotero_shared_collections(collection_type);
CREATE INDEX IF NOT EXISTS idx_shared_collections_public ON zotero.zotero_shared_collections(is_public) WHERE is_public = true;
CREATE INDEX IF NOT EXISTS idx_shared_collections_access_code ON zotero.zotero_shared_collections(access_code) WHERE access_code IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_collection_collaborators_collection ON zotero.zotero_collection_collaborators(collection_id);
CREATE INDEX IF NOT EXISTS idx_collection_collaborators_user ON zotero.zotero_collection_collaborators(user_id);
CREATE INDEX IF NOT EXISTS idx_collection_collaborators_status ON zotero.zotero_collection_collaborators(invitation_status);

CREATE INDEX IF NOT EXISTS idx_conversation_exports_user ON zotero.zotero_conversation_exports(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_exports_conversation ON zotero.zotero_conversation_exports(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversation_exports_created ON zotero.zotero_conversation_exports(created_at);

CREATE INDEX IF NOT EXISTS idx_collection_references_collection ON zotero.zotero_collection_references(collection_id);
CREATE INDEX IF NOT EXISTS idx_collection_references_reference ON zotero.zotero_collection_references(reference_id);
CREATE INDEX IF NOT EXISTS idx_collection_references_added_by ON zotero.zotero_collection_references(added_by);

CREATE INDEX IF NOT EXISTS idx_sharing_activity_user ON zotero.zotero_sharing_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_sharing_activity_type ON zotero.zotero_sharing_activity(activity_type);
CREATE INDEX IF NOT EXISTS idx_sharing_activity_target ON zotero.zotero_sharing_activity(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_sharing_activity_created ON zotero.zotero_sharing_activity(created_at);

-- Add triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_zotero_shared_references_updated_at 
    BEFORE UPDATE ON zotero.zotero_shared_references 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_zotero_shared_collections_updated_at 
    BEFORE UPDATE ON zotero.zotero_shared_collections 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_zotero_collection_collaborators_updated_at 
    BEFORE UPDATE ON zotero.zotero_collection_collaborators 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();