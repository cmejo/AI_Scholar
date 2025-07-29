#!/usr/bin/env python3
"""
Initialize database for performance optimization testing.
"""
import asyncio
import logging
from core.database import init_db, Base, engine
from core.database_optimization import initialize_database_optimizations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Initialize database and optimizations."""
    try:
        logger.info("Creating database tables...")
        await init_db()
        
        logger.info("Applying database optimizations...")
        await initialize_database_optimizations()
        
        logger.info("Database initialization completed successfully!")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)