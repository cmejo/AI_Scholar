#!/usr/bin/env python3
"""
Initialize Zotero integration database schema
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.config import settings
from core.database import engine, Base
from models.zotero_models import *  # Import all Zotero models
import sqlalchemy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration_sql():
    """Run the Zotero migration SQL file"""
    migration_file = backend_dir / "migrations" / "001_zotero_integration_foundation.sql"
    
    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return False
    
    try:
        # Read migration SQL
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        with engine.connect() as connection:
            # Split SQL into individual statements and execute
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement.upper().startswith(('CREATE', 'INSERT', 'ALTER', 'DROP', 'GRANT', 'SET')):
                    try:
                        connection.execute(sqlalchemy.text(statement))
                        connection.commit()
                    except Exception as e:
                        logger.warning(f"Statement execution warning (may be expected): {e}")
                        # Continue with other statements
                        continue
        
        logger.info("Zotero database migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error running migration: {e}")
        return False


def create_tables():
    """Create Zotero tables using SQLAlchemy models"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Zotero database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False


def verify_tables():
    """Verify that Zotero tables were created"""
    try:
        with engine.connect() as connection:
            # Check if zotero schema exists
            result = connection.execute(sqlalchemy.text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = 'zotero'
            """))
            
            if not result.fetchone():
                logger.error("Zotero schema not found")
                return False
            
            # Check if main tables exist
            tables_to_check = [
                'zotero_connections',
                'zotero_libraries', 
                'zotero_collections',
                'zotero_items',
                'zotero_attachments',
                'zotero_citation_styles',
                'zotero_user_preferences'
            ]
            
            for table in tables_to_check:
                result = connection.execute(sqlalchemy.text(f"""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'zotero' AND table_name = '{table}'
                """))
                
                if not result.fetchone():
                    logger.error(f"Table {table} not found in zotero schema")
                    return False
            
            logger.info("All Zotero tables verified successfully")
            return True
            
    except Exception as e:
        logger.error(f"Error verifying tables: {e}")
        return False


def main():
    """Main initialization function"""
    logger.info("Starting Zotero database initialization...")
    
    # Check database connection
    try:
        with engine.connect() as connection:
            connection.execute(sqlalchemy.text("SELECT 1"))
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
    
    # Run migration SQL (for PostgreSQL-specific features)
    if settings.DATABASE_URL.startswith("postgresql"):
        logger.info("Running PostgreSQL migration...")
        if not run_migration_sql():
            logger.error("Migration failed")
            return False
    else:
        logger.info("Using SQLAlchemy table creation for non-PostgreSQL database...")
        if not create_tables():
            logger.error("Table creation failed")
            return False
    
    # Verify tables were created
    if not verify_tables():
        logger.error("Table verification failed")
        return False
    
    logger.info("Zotero database initialization completed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)