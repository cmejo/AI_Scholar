-- Migration: Add citation management tables
-- Description: Add tables for citation history, favorites, and style previews

-- Citation History Table
CREATE TABLE IF NOT EXISTS zotero.zotero_citation_history (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR NOT NULL,
    item_ids JSONB NOT NULL,
    citation_style VARCHAR(50) NOT NULL,
    format_type VARCHAR(20) NOT NULL,
    citations JSONB NOT NULL,
    access_count INTEGER DEFAULT 1,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id VARCHAR(100),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Citation Favorites Table
CREATE TABLE IF NOT EXISTS zotero.zotero_citation_favorites (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR NOT NULL,
    item_id VARCHAR NOT NULL,
    citation_style VARCHAR(50) NOT NULL,
    format_type VARCHAR(20) NOT NULL,
    citation TEXT NOT NULL,
    user_note TEXT,
    tags JSONB DEFAULT '[]'::jsonb,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    FOREIGN KEY (item_id) REFERENCES zotero.zotero_items(id) ON DELETE CASCADE
);

-- Citation Style Previews Cache Table
CREATE TABLE IF NOT EXISTS zotero.zotero_citation_style_previews (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    item_id VARCHAR NOT NULL,
    citation_style VARCHAR(50) NOT NULL,
    format_type VARCHAR(20) NOT NULL,
    citation_preview TEXT NOT NULL,
    cache_expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (item_id) REFERENCES zotero.zotero_items(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_citation_history_user_id ON zotero.zotero_citation_history(user_id);
CREATE INDEX IF NOT EXISTS idx_citation_history_created_at ON zotero.zotero_citation_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_citation_history_style ON zotero.zotero_citation_history(citation_style);

CREATE INDEX IF NOT EXISTS idx_citation_favorites_user_id ON zotero.zotero_citation_favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_citation_favorites_item_id ON zotero.zotero_citation_favorites(item_id);
CREATE INDEX IF NOT EXISTS idx_citation_favorites_last_accessed ON zotero.zotero_citation_favorites(last_accessed DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_citation_favorites_unique ON zotero.zotero_citation_favorites(user_id, item_id, citation_style);

CREATE INDEX IF NOT EXISTS idx_citation_previews_item_style ON zotero.zotero_citation_style_previews(item_id, citation_style);
CREATE INDEX IF NOT EXISTS idx_citation_previews_expires ON zotero.zotero_citation_style_previews(cache_expires_at);

-- Add trigger to update updated_at timestamp for favorites
CREATE OR REPLACE FUNCTION update_citation_favorites_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_citation_favorites_updated_at
    BEFORE UPDATE ON zotero.zotero_citation_favorites
    FOR EACH ROW
    EXECUTE FUNCTION update_citation_favorites_updated_at();

-- Add comments for documentation
COMMENT ON TABLE zotero.zotero_citation_history IS 'Stores user citation generation history for quick access and analytics';
COMMENT ON TABLE zotero.zotero_citation_favorites IS 'Stores user favorite citations with notes and tags';
COMMENT ON TABLE zotero.zotero_citation_style_previews IS 'Caches citation style previews for performance';

COMMENT ON COLUMN zotero.zotero_citation_history.item_ids IS 'JSON array of item IDs that were cited together';
COMMENT ON COLUMN zotero.zotero_citation_history.citations IS 'JSON array of generated citations';
COMMENT ON COLUMN zotero.zotero_citation_history.session_id IS 'Optional session identifier for grouping related citations';

COMMENT ON COLUMN zotero.zotero_citation_favorites.tags IS 'JSON array of user-defined tags for organization';
COMMENT ON COLUMN zotero.zotero_citation_favorites.access_count IS 'Number of times this favorite has been accessed';

COMMENT ON COLUMN zotero.zotero_citation_style_previews.cache_expires_at IS 'When this cached preview expires and should be regenerated';