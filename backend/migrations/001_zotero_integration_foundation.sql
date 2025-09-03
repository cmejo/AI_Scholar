-- Zotero Integration Foundation Database Migration
-- This migration creates the core tables needed for Zotero integration

-- Create zotero schema for organization
CREATE SCHEMA IF NOT EXISTS zotero;

-- Set search path to include zotero schema
SET search_path TO ai_scholar, zotero, public;

-- Create zotero_connections table for storing user Zotero API credentials
CREATE TABLE IF NOT EXISTS zotero.zotero_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES ai_scholar.users(id) ON DELETE CASCADE,
    zotero_user_id VARCHAR(50) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    api_key VARCHAR(255),
    connection_type VARCHAR(20) DEFAULT 'oauth' CHECK (connection_type IN ('oauth', 'api_key')),
    connection_status VARCHAR(20) DEFAULT 'active' CHECK (connection_status IN ('active', 'expired', 'revoked', 'error')),
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    connection_metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(user_id, zotero_user_id)
);

-- Create zotero_libraries table for storing library information
CREATE TABLE IF NOT EXISTS zotero.zotero_libraries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID NOT NULL REFERENCES zotero.zotero_connections(id) ON DELETE CASCADE,
    zotero_library_id VARCHAR(50) NOT NULL,
    library_type VARCHAR(20) NOT NULL CHECK (library_type IN ('user', 'group')),
    library_name VARCHAR(255) NOT NULL,
    library_version INTEGER DEFAULT 0,
    owner_id VARCHAR(50),
    group_id VARCHAR(50),
    permissions JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    library_metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(connection_id, zotero_library_id)
);

-- Create zotero_collections table for storing collection hierarchy
CREATE TABLE IF NOT EXISTS zotero.zotero_collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    library_id UUID NOT NULL REFERENCES zotero.zotero_libraries(id) ON DELETE CASCADE,
    zotero_collection_key VARCHAR(50) NOT NULL,
    parent_collection_id UUID REFERENCES zotero.zotero_collections(id) ON DELETE CASCADE,
    collection_name VARCHAR(255) NOT NULL,
    collection_version INTEGER DEFAULT 0,
    collection_path TEXT, -- Hierarchical path for efficient queries
    item_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    collection_metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(library_id, zotero_collection_key)
);

-- Create zotero_items table for storing reference items
CREATE TABLE IF NOT EXISTS zotero.zotero_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    library_id UUID NOT NULL REFERENCES zotero.zotero_libraries(id) ON DELETE CASCADE,
    zotero_item_key VARCHAR(50) NOT NULL,
    parent_item_id UUID REFERENCES zotero.zotero_items(id) ON DELETE CASCADE,
    item_type VARCHAR(50) NOT NULL,
    item_version INTEGER DEFAULT 0,
    title TEXT,
    creators JSONB DEFAULT '[]'::jsonb, -- Authors, editors, etc.
    publication_title VARCHAR(500),
    publication_year INTEGER,
    publisher VARCHAR(255),
    doi VARCHAR(255),
    isbn VARCHAR(50),
    issn VARCHAR(50),
    url TEXT,
    abstract_note TEXT,
    date_added TIMESTAMP WITH TIME ZONE,
    date_modified TIMESTAMP WITH TIME ZONE,
    extra_fields JSONB DEFAULT '{}'::jsonb, -- Additional Zotero fields
    tags JSONB DEFAULT '[]'::jsonb,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    item_metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(library_id, zotero_item_key)
);

-- Create zotero_item_collections table for many-to-many relationship
CREATE TABLE IF NOT EXISTS zotero.zotero_item_collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES zotero.zotero_items(id) ON DELETE CASCADE,
    collection_id UUID NOT NULL REFERENCES zotero.zotero_collections(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(item_id, collection_id)
);

-- Create zotero_attachments table for PDF and file attachments
CREATE TABLE IF NOT EXISTS zotero.zotero_attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES zotero.zotero_items(id) ON DELETE CASCADE,
    zotero_attachment_key VARCHAR(50) NOT NULL,
    attachment_type VARCHAR(50) NOT NULL, -- 'imported_file', 'imported_url', 'linked_file', 'linked_url'
    title VARCHAR(255),
    filename VARCHAR(255),
    content_type VARCHAR(100),
    file_size BIGINT,
    file_path TEXT, -- Local storage path
    zotero_url TEXT, -- Zotero storage URL
    md5_hash VARCHAR(32),
    sync_status VARCHAR(20) DEFAULT 'pending' CHECK (sync_status IN ('pending', 'synced', 'error', 'not_available')),
    last_accessed TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    attachment_metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(item_id, zotero_attachment_key)
);

-- Create zotero_annotations table for PDF annotations
CREATE TABLE IF NOT EXISTS zotero.zotero_annotations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    attachment_id UUID NOT NULL REFERENCES zotero.zotero_attachments(id) ON DELETE CASCADE,
    zotero_annotation_key VARCHAR(50) NOT NULL,
    annotation_type VARCHAR(20) NOT NULL CHECK (annotation_type IN ('highlight', 'note', 'image')),
    annotation_text TEXT,
    annotation_comment TEXT,
    page_number INTEGER,
    position_data JSONB, -- Position coordinates and dimensions
    color VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    annotation_metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(attachment_id, zotero_annotation_key)
);

-- Create zotero_sync_log table for tracking synchronization
CREATE TABLE IF NOT EXISTS zotero.zotero_sync_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID NOT NULL REFERENCES zotero.zotero_connections(id) ON DELETE CASCADE,
    sync_type VARCHAR(20) NOT NULL CHECK (sync_type IN ('full', 'incremental', 'manual')),
    sync_status VARCHAR(20) NOT NULL CHECK (sync_status IN ('started', 'in_progress', 'completed', 'failed', 'cancelled')),
    items_processed INTEGER DEFAULT 0,
    items_added INTEGER DEFAULT 0,
    items_updated INTEGER DEFAULT 0,
    items_deleted INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    error_details JSONB DEFAULT '[]'::jsonb,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    sync_metadata JSONB DEFAULT '{}'::jsonb
);

-- Create zotero_citation_styles table for citation formatting
CREATE TABLE IF NOT EXISTS zotero.zotero_citation_styles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    style_name VARCHAR(100) NOT NULL UNIQUE,
    style_title VARCHAR(255) NOT NULL,
    style_category VARCHAR(50), -- 'author-date', 'numeric', 'note'
    csl_content TEXT NOT NULL, -- Citation Style Language XML content
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create zotero_user_preferences table for user-specific settings
CREATE TABLE IF NOT EXISTS zotero.zotero_user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES ai_scholar.users(id) ON DELETE CASCADE,
    default_citation_style_id UUID REFERENCES zotero.zotero_citation_styles(id),
    auto_sync_enabled BOOLEAN DEFAULT TRUE,
    sync_frequency_minutes INTEGER DEFAULT 60,
    sync_attachments BOOLEAN DEFAULT TRUE,
    sync_annotations BOOLEAN DEFAULT TRUE,
    max_attachment_size_mb INTEGER DEFAULT 50,
    preferred_export_format VARCHAR(20) DEFAULT 'bibtex',
    ai_analysis_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    preferences_metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(user_id)
);

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_zotero_connections_user_id ON zotero.zotero_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_zotero_connections_status ON zotero.zotero_connections(connection_status);
CREATE INDEX IF NOT EXISTS idx_zotero_connections_last_sync ON zotero.zotero_connections(last_sync_at);

CREATE INDEX IF NOT EXISTS idx_zotero_libraries_connection_id ON zotero.zotero_libraries(connection_id);
CREATE INDEX IF NOT EXISTS idx_zotero_libraries_type ON zotero.zotero_libraries(library_type);
CREATE INDEX IF NOT EXISTS idx_zotero_libraries_active ON zotero.zotero_libraries(is_active);

CREATE INDEX IF NOT EXISTS idx_zotero_collections_library_id ON zotero.zotero_collections(library_id);
CREATE INDEX IF NOT EXISTS idx_zotero_collections_parent ON zotero.zotero_collections(parent_collection_id);
CREATE INDEX IF NOT EXISTS idx_zotero_collections_path ON zotero.zotero_collections(collection_path);

CREATE INDEX IF NOT EXISTS idx_zotero_items_library_id ON zotero.zotero_items(library_id);
CREATE INDEX IF NOT EXISTS idx_zotero_items_type ON zotero.zotero_items(item_type);
CREATE INDEX IF NOT EXISTS idx_zotero_items_title ON zotero.zotero_items USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_zotero_items_creators ON zotero.zotero_items USING gin(creators);
CREATE INDEX IF NOT EXISTS idx_zotero_items_tags ON zotero.zotero_items USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_zotero_items_year ON zotero.zotero_items(publication_year);
CREATE INDEX IF NOT EXISTS idx_zotero_items_doi ON zotero.zotero_items(doi);
CREATE INDEX IF NOT EXISTS idx_zotero_items_deleted ON zotero.zotero_items(is_deleted);

CREATE INDEX IF NOT EXISTS idx_zotero_item_collections_item ON zotero.zotero_item_collections(item_id);
CREATE INDEX IF NOT EXISTS idx_zotero_item_collections_collection ON zotero.zotero_item_collections(collection_id);

CREATE INDEX IF NOT EXISTS idx_zotero_attachments_item_id ON zotero.zotero_attachments(item_id);
CREATE INDEX IF NOT EXISTS idx_zotero_attachments_type ON zotero.zotero_attachments(attachment_type);
CREATE INDEX IF NOT EXISTS idx_zotero_attachments_sync_status ON zotero.zotero_attachments(sync_status);
CREATE INDEX IF NOT EXISTS idx_zotero_attachments_content_type ON zotero.zotero_attachments(content_type);

CREATE INDEX IF NOT EXISTS idx_zotero_annotations_attachment_id ON zotero.zotero_annotations(attachment_id);
CREATE INDEX IF NOT EXISTS idx_zotero_annotations_type ON zotero.zotero_annotations(annotation_type);
CREATE INDEX IF NOT EXISTS idx_zotero_annotations_page ON zotero.zotero_annotations(page_number);

CREATE INDEX IF NOT EXISTS idx_zotero_sync_log_connection_id ON zotero.zotero_sync_log(connection_id);
CREATE INDEX IF NOT EXISTS idx_zotero_sync_log_status ON zotero.zotero_sync_log(sync_status);
CREATE INDEX IF NOT EXISTS idx_zotero_sync_log_started_at ON zotero.zotero_sync_log(started_at);

CREATE INDEX IF NOT EXISTS idx_zotero_user_preferences_user_id ON zotero.zotero_user_preferences(user_id);

-- Create updated_at triggers for Zotero tables
CREATE TRIGGER update_zotero_connections_updated_at 
    BEFORE UPDATE ON zotero.zotero_connections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_zotero_libraries_updated_at 
    BEFORE UPDATE ON zotero.zotero_libraries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_zotero_collections_updated_at 
    BEFORE UPDATE ON zotero.zotero_collections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_zotero_items_updated_at 
    BEFORE UPDATE ON zotero.zotero_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_zotero_attachments_updated_at 
    BEFORE UPDATE ON zotero.zotero_attachments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_zotero_annotations_updated_at 
    BEFORE UPDATE ON zotero.zotero_annotations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_zotero_citation_styles_updated_at 
    BEFORE UPDATE ON zotero.zotero_citation_styles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_zotero_user_preferences_updated_at 
    BEFORE UPDATE ON zotero.zotero_user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default citation styles
INSERT INTO zotero.zotero_citation_styles (style_name, style_title, style_category, csl_content, is_default) VALUES
('apa', 'American Psychological Association 7th edition', 'author-date', '<?xml version="1.0" encoding="utf-8"?>
<style xmlns="http://purl.org/net/xbiblio/csl" class="in-text" version="1.0" demote-non-dropping-particle="never">
  <info>
    <title>American Psychological Association 7th edition</title>
    <id>http://www.zotero.org/styles/apa</id>
    <link href="http://www.zotero.org/styles/apa" rel="self"/>
    <category citation-format="author-date"/>
    <category field="psychology"/>
    <category field="generic-base"/>
    <updated>2020-01-20T14:00:00+00:00</updated>
  </info>
  <!-- Simplified CSL content for APA style -->
</style>', TRUE),
('mla', 'Modern Language Association 9th edition', 'author', '<?xml version="1.0" encoding="utf-8"?>
<style xmlns="http://purl.org/net/xbiblio/csl" class="in-text" version="1.0">
  <info>
    <title>Modern Language Association 9th edition</title>
    <id>http://www.zotero.org/styles/mla</id>
    <link href="http://www.zotero.org/styles/mla" rel="self"/>
    <category citation-format="author"/>
    <category field="literature"/>
    <updated>2021-02-01T12:00:00+00:00</updated>
  </info>
  <!-- Simplified CSL content for MLA style -->
</style>', FALSE),
('chicago-author-date', 'Chicago Manual of Style 17th edition (author-date)', 'author-date', '<?xml version="1.0" encoding="utf-8"?>
<style xmlns="http://purl.org/net/xbiblio/csl" class="in-text" version="1.0">
  <info>
    <title>Chicago Manual of Style 17th edition (author-date)</title>
    <id>http://www.zotero.org/styles/chicago-author-date</id>
    <link href="http://www.zotero.org/styles/chicago-author-date" rel="self"/>
    <category citation-format="author-date"/>
    <category field="generic-base"/>
    <updated>2020-09-28T14:00:00+00:00</updated>
  </info>
  <!-- Simplified CSL content for Chicago author-date style -->
</style>', FALSE);

-- Grant permissions on zotero schema
GRANT USAGE ON SCHEMA zotero TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA zotero TO PUBLIC;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA zotero TO PUBLIC;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Zotero integration foundation migration completed successfully!';
END $$;