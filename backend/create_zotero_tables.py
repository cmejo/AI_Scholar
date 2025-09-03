#!/usr/bin/env python3
"""
Simple script to create Zotero tables using raw SQL
"""
import sqlite3
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = "ai_scholar.db"

def create_zotero_tables():
    """Create Zotero tables in SQLite database"""
    
    # SQL for creating Zotero tables (SQLite compatible)
    zotero_sql = """
    -- Create zotero_connections table
    CREATE TABLE IF NOT EXISTS zotero_connections (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        zotero_user_id TEXT NOT NULL,
        access_token TEXT NOT NULL,
        refresh_token TEXT,
        token_expires_at DATETIME,
        api_key TEXT,
        connection_type TEXT DEFAULT 'oauth' CHECK (connection_type IN ('oauth', 'api_key')),
        connection_status TEXT DEFAULT 'active' CHECK (connection_status IN ('active', 'expired', 'revoked', 'error')),
        last_sync_at DATETIME,
        sync_enabled BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        connection_metadata TEXT DEFAULT '{}',
        UNIQUE(user_id, zotero_user_id)
    );

    -- Create zotero_libraries table
    CREATE TABLE IF NOT EXISTS zotero_libraries (
        id TEXT PRIMARY KEY,
        connection_id TEXT NOT NULL REFERENCES zotero_connections(id) ON DELETE CASCADE,
        zotero_library_id TEXT NOT NULL,
        library_type TEXT NOT NULL CHECK (library_type IN ('user', 'group')),
        library_name TEXT NOT NULL,
        library_version INTEGER DEFAULT 0,
        owner_id TEXT,
        group_id TEXT,
        permissions TEXT DEFAULT '{}',
        is_active BOOLEAN DEFAULT 1,
        last_sync_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        library_metadata TEXT DEFAULT '{}',
        UNIQUE(connection_id, zotero_library_id)
    );

    -- Create zotero_collections table
    CREATE TABLE IF NOT EXISTS zotero_collections (
        id TEXT PRIMARY KEY,
        library_id TEXT NOT NULL REFERENCES zotero_libraries(id) ON DELETE CASCADE,
        zotero_collection_key TEXT NOT NULL,
        parent_collection_id TEXT REFERENCES zotero_collections(id) ON DELETE CASCADE,
        collection_name TEXT NOT NULL,
        collection_version INTEGER DEFAULT 0,
        collection_path TEXT,
        item_count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        collection_metadata TEXT DEFAULT '{}',
        UNIQUE(library_id, zotero_collection_key)
    );

    -- Create zotero_items table
    CREATE TABLE IF NOT EXISTS zotero_items (
        id TEXT PRIMARY KEY,
        library_id TEXT NOT NULL REFERENCES zotero_libraries(id) ON DELETE CASCADE,
        zotero_item_key TEXT NOT NULL,
        parent_item_id TEXT REFERENCES zotero_items(id) ON DELETE CASCADE,
        item_type TEXT NOT NULL,
        item_version INTEGER DEFAULT 0,
        title TEXT,
        creators TEXT DEFAULT '[]',
        publication_title TEXT,
        publication_year INTEGER,
        publisher TEXT,
        doi TEXT,
        isbn TEXT,
        issn TEXT,
        url TEXT,
        abstract_note TEXT,
        date_added DATETIME,
        date_modified DATETIME,
        extra_fields TEXT DEFAULT '{}',
        tags TEXT DEFAULT '[]',
        is_deleted BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        item_metadata TEXT DEFAULT '{}',
        UNIQUE(library_id, zotero_item_key)
    );

    -- Create zotero_item_collections table
    CREATE TABLE IF NOT EXISTS zotero_item_collections (
        id TEXT PRIMARY KEY,
        item_id TEXT NOT NULL REFERENCES zotero_items(id) ON DELETE CASCADE,
        collection_id TEXT NOT NULL REFERENCES zotero_collections(id) ON DELETE CASCADE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(item_id, collection_id)
    );

    -- Create zotero_attachments table
    CREATE TABLE IF NOT EXISTS zotero_attachments (
        id TEXT PRIMARY KEY,
        item_id TEXT NOT NULL REFERENCES zotero_items(id) ON DELETE CASCADE,
        zotero_attachment_key TEXT NOT NULL,
        attachment_type TEXT NOT NULL,
        title TEXT,
        filename TEXT,
        content_type TEXT,
        file_size INTEGER,
        file_path TEXT,
        zotero_url TEXT,
        md5_hash TEXT,
        sync_status TEXT DEFAULT 'pending' CHECK (sync_status IN ('pending', 'synced', 'error', 'not_available')),
        last_accessed DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        attachment_metadata TEXT DEFAULT '{}',
        UNIQUE(item_id, zotero_attachment_key)
    );

    -- Create zotero_annotations table
    CREATE TABLE IF NOT EXISTS zotero_annotations (
        id TEXT PRIMARY KEY,
        attachment_id TEXT NOT NULL REFERENCES zotero_attachments(id) ON DELETE CASCADE,
        zotero_annotation_key TEXT NOT NULL,
        annotation_type TEXT NOT NULL CHECK (annotation_type IN ('highlight', 'note', 'image')),
        annotation_text TEXT,
        annotation_comment TEXT,
        page_number INTEGER,
        position_data TEXT,
        color TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        annotation_metadata TEXT DEFAULT '{}',
        UNIQUE(attachment_id, zotero_annotation_key)
    );

    -- Create zotero_sync_log table
    CREATE TABLE IF NOT EXISTS zotero_sync_log (
        id TEXT PRIMARY KEY,
        connection_id TEXT NOT NULL REFERENCES zotero_connections(id) ON DELETE CASCADE,
        sync_type TEXT NOT NULL CHECK (sync_type IN ('full', 'incremental', 'manual')),
        sync_status TEXT NOT NULL CHECK (sync_status IN ('started', 'in_progress', 'completed', 'failed', 'cancelled')),
        items_processed INTEGER DEFAULT 0,
        items_added INTEGER DEFAULT 0,
        items_updated INTEGER DEFAULT 0,
        items_deleted INTEGER DEFAULT 0,
        errors_count INTEGER DEFAULT 0,
        error_details TEXT DEFAULT '[]',
        started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME,
        sync_metadata TEXT DEFAULT '{}'
    );

    -- Create zotero_citation_styles table
    CREATE TABLE IF NOT EXISTS zotero_citation_styles (
        id TEXT PRIMARY KEY,
        style_name TEXT NOT NULL UNIQUE,
        style_title TEXT NOT NULL,
        style_category TEXT,
        csl_content TEXT NOT NULL,
        is_default BOOLEAN DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Create zotero_user_preferences table
    CREATE TABLE IF NOT EXISTS zotero_user_preferences (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        default_citation_style_id TEXT REFERENCES zotero_citation_styles(id),
        auto_sync_enabled BOOLEAN DEFAULT 1,
        sync_frequency_minutes INTEGER DEFAULT 60,
        sync_attachments BOOLEAN DEFAULT 1,
        sync_annotations BOOLEAN DEFAULT 1,
        max_attachment_size_mb INTEGER DEFAULT 50,
        preferred_export_format TEXT DEFAULT 'bibtex',
        ai_analysis_enabled BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        preferences_metadata TEXT DEFAULT '{}',
        UNIQUE(user_id)
    );

    -- Create indexes
    CREATE INDEX IF NOT EXISTS idx_zotero_connections_user_id ON zotero_connections(user_id);
    CREATE INDEX IF NOT EXISTS idx_zotero_connections_status ON zotero_connections(connection_status);
    CREATE INDEX IF NOT EXISTS idx_zotero_libraries_connection_id ON zotero_libraries(connection_id);
    CREATE INDEX IF NOT EXISTS idx_zotero_collections_library_id ON zotero_collections(library_id);
    CREATE INDEX IF NOT EXISTS idx_zotero_items_library_id ON zotero_items(library_id);
    CREATE INDEX IF NOT EXISTS idx_zotero_items_type ON zotero_items(item_type);
    CREATE INDEX IF NOT EXISTS idx_zotero_items_title ON zotero_items(title);
    CREATE INDEX IF NOT EXISTS idx_zotero_items_year ON zotero_items(publication_year);
    CREATE INDEX IF NOT EXISTS idx_zotero_items_doi ON zotero_items(doi);
    CREATE INDEX IF NOT EXISTS idx_zotero_attachments_item_id ON zotero_attachments(item_id);
    CREATE INDEX IF NOT EXISTS idx_zotero_annotations_attachment_id ON zotero_annotations(attachment_id);
    CREATE INDEX IF NOT EXISTS idx_zotero_sync_log_connection_id ON zotero_sync_log(connection_id);
    CREATE INDEX IF NOT EXISTS idx_zotero_user_preferences_user_id ON zotero_user_preferences(user_id);

    -- Insert default citation styles
    INSERT OR IGNORE INTO zotero_citation_styles (id, style_name, style_title, style_category, csl_content, is_default) VALUES
    ('apa-style', 'apa', 'American Psychological Association 7th edition', 'author-date', 
     '<?xml version="1.0" encoding="utf-8"?><style xmlns="http://purl.org/net/xbiblio/csl" class="in-text" version="1.0"><info><title>American Psychological Association 7th edition</title><id>http://www.zotero.org/styles/apa</id></info></style>', 1),
    ('mla-style', 'mla', 'Modern Language Association 9th edition', 'author', 
     '<?xml version="1.0" encoding="utf-8"?><style xmlns="http://purl.org/net/xbiblio/csl" class="in-text" version="1.0"><info><title>Modern Language Association 9th edition</title><id>http://www.zotero.org/styles/mla</id></info></style>', 0),
    ('chicago-style', 'chicago-author-date', 'Chicago Manual of Style 17th edition (author-date)', 'author-date', 
     '<?xml version="1.0" encoding="utf-8"?><style xmlns="http://purl.org/net/xbiblio/csl" class="in-text" version="1.0"><info><title>Chicago Manual of Style 17th edition (author-date)</title><id>http://www.zotero.org/styles/chicago-author-date</id></info></style>', 0);
    """
    
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Execute SQL
        cursor.executescript(zotero_sql)
        
        # Commit changes
        conn.commit()
        
        logger.info("Zotero tables created successfully!")
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'zotero_%'")
        tables = cursor.fetchall()
        
        logger.info(f"Created {len(tables)} Zotero tables:")
        for table in tables:
            logger.info(f"  - {table[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error creating Zotero tables: {e}")
        return False


def main():
    """Main function"""
    logger.info("Creating Zotero integration tables...")
    
    if create_zotero_tables():
        logger.info("Zotero database setup completed successfully!")
        return True
    else:
        logger.error("Zotero database setup failed!")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)