#!/usr/bin/env python3
"""
Database initialization script for enhanced RAG features
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import Base, engine, init_db
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_enhanced_tables():
    """Create all enhanced database tables"""
    try:
        logger.info("Creating enhanced database tables...")
        
        # Create all tables defined in the Base metadata
        Base.metadata.create_all(bind=engine)
        
        logger.info("Enhanced database tables created successfully!")
        
        # Print table information
        logger.info("Created tables:")
        for table_name in Base.metadata.tables.keys():
            logger.info(f"  - {table_name}")
            
    except Exception as e:
        logger.error(f"Error creating enhanced database tables: {e}")
        raise

async def main():
    """Main initialization function"""
    logger.info("Initializing enhanced RAG database...")
    
    try:
        await create_enhanced_tables()
        logger.info("Database initialization completed successfully!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())