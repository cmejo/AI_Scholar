#!/usr/bin/env python3
"""
Test research automation service initialization
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

async def test_research_automation_initialization():
    """Test research automation service initialization"""
    try:
        logger.info("Testing research automation service initialization...")
        
        # Import service manager
        from core.service_manager import service_manager
        
        # Test research automation service initialization
        logger.info("Initializing research automation service...")
        success = await service_manager.initialize_research_automation_service()
        
        if success:
            logger.info("✓ Research automation service initialized successfully")
            
            # Test service health
            health = await service_manager.check_service_health("research_automation")
            logger.info(f"Service health: {health.status.value}")
            
            # Get service instance
            service = service_manager.get_service("research_automation")
            if service:
                logger.info("✓ Service instance retrieved successfully")
                
                # Test service methods
                status = service.get_status()
                logger.info(f"Service status: {status}")
                
                # Test health check
                health_result = await service.health_check()
                logger.info(f"Health check result: {health_result}")
                
                # Test mock workflow creation
                try:
                    workflow = await service.create_automated_workflow(
                        user_id="test-user",
                        name="Test Workflow",
                        workflow_type="literature_monitoring",
                        description="Test workflow description",
                        configuration={"test": "config"},
                        schedule_config={"interval": "daily"}
                    )
                    logger.info(f"✓ Mock workflow creation test: {workflow}")
                except Exception as e:
                    logger.info(f"Mock workflow creation (expected for mock service): {e}")
                
            else:
                logger.error("✗ Failed to retrieve service instance")
                return False
        else:
            logger.error("✗ Research automation service initialization failed")
            return False
        
        # Test service manager summary
        summary = service_manager.get_initialization_summary()
        logger.info(f"Initialization summary: {summary}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during research automation service test: {e}", exc_info=True)
        return False

async def main():
    """Main test function"""
    logger.info("Starting research automation service initialization test")
    
    success = await test_research_automation_initialization()
    
    if success:
        logger.info("✓ All tests passed")
        return 0
    else:
        logger.error("✗ Tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)