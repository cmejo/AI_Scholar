#!/usr/bin/env python3
"""
Test semantic search service initialization
"""
import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_semantic_search_initialization():
    """Test semantic search service initialization"""
    try:
        logger.info("Testing semantic search service initialization...")
        
        # Import service manager
        from core.service_manager import service_manager
        
        # Test semantic search service initialization
        logger.info("Initializing semantic search service...")
        success = await service_manager.initialize_semantic_search_service()
        
        if success:
            logger.info("✓ Semantic search service initialized successfully")
            
            # Test service health
            health = await service_manager.check_service_health("semantic_search")
            logger.info(f"Service health: {health.status.value}")
            
            # Get service instance
            service = service_manager.get_service("semantic_search")
            if service:
                logger.info("✓ Service instance retrieved successfully")
                
                # Test service methods
                status = service.get_status()
                logger.info(f"Service status: {status}")
                
                # Test health check
                health_result = await service.health_check()
                logger.info(f"Health check result: {health_result}")
                
            else:
                logger.error("✗ Failed to retrieve service instance")
                return False
        else:
            logger.error("✗ Semantic search service initialization failed")
            return False
        
        # Test service manager summary
        summary = service_manager.get_initialization_summary()
        logger.info(f"Initialization summary: {summary}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during semantic search service test: {e}", exc_info=True)
        return False

async def main():
    """Main test function"""
    logger.info("Starting semantic search service initialization test")
    
    success = await test_semantic_search_initialization()
    
    if success:
        logger.info("✓ All tests passed")
        return 0
    else:
        logger.error("✗ Tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)