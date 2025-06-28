#!/usr/bin/env python3
"""
Simple database migration script for minimal app
Adds metadata column to chat_messages table
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """Add metadata column to chat_messages table if it doesn't exist"""
    
    # Database path
    db_path = 'chatbot.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. Creating new database with updated schema.")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if metadata column exists
        cursor.execute("PRAGMA table_info(chat_message)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'metadata' not in columns:
            print("Adding metadata column to chat_message table...")
            cursor.execute("ALTER TABLE chat_message ADD COLUMN metadata TEXT")
            conn.commit()
            print("✓ Metadata column added successfully")
        else:
            print("✓ Metadata column already exists")
        
        # Create visualizations table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS visualizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                visualization_type VARCHAR(50) NOT NULL,
                data TEXT NOT NULL,
                config TEXT,
                title VARCHAR(255),
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES chat_message (id),
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        """)
        conn.commit()
        print("✓ Visualizations table created/verified")
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_visualizations_message_id ON visualizations (message_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_visualizations_user_id ON visualizations (user_id)")
        conn.commit()
        print("✓ Indexes created/verified")
        
        conn.close()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    migrate_database()