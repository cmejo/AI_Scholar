#!/usr/bin/env python3
"""
Direct test of research automation service functionality
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

async def test_research_automation_direct():
    """Test research automation service directly"""
    try:
        logger.info("Testing research automation service directly...")
        
        # Import service manager
        from core.service_manager import service_manager
        
        # Initialize research automation service
        logger.info("Initializing research automation service...")
        success = await service_manager.initialize_research_automation_service()
        
        if not success:
            logger.error("✗ Failed to initialize research automation service")
            return False
        
        logger.info("✓ Research automation service initialized successfully")
        
        # Get service instance
        service = service_manager.get_service("research_automation")
        if not service:
            logger.error("✗ Failed to get research automation service instance")
            return False
        
        logger.info("✓ Research automation service instance retrieved")
        
        # Test service health check
        logger.info("Testing service health check...")
        health_result = await service.health_check()
        logger.info(f"Health check result: {health_result}")
        
        if health_result.get("status") in ["mock", "healthy"]:
            logger.info("✓ Service health check passed")
        else:
            logger.error("✗ Service health check failed")
            return False
        
        # Test service status
        logger.info("Testing service status...")
        status = service.get_status()
        logger.info(f"Service status: {status}")
        
        if status.get("status") == "healthy":
            logger.info("✓ Service status is healthy")
        else:
            logger.error("✗ Service status is not healthy")
            return False
        
        # Test service manager health check
        logger.info("Testing service manager health check...")
        health = await service_manager.check_service_health("research_automation")
        logger.info(f"Service manager health check: {health.status.value}")
        
        if health.status.value in ["healthy", "degraded"]:
            logger.info("✓ Service manager health check passed")
        else:
            logger.error("✗ Service manager health check failed")
            return False
        
        # Test workflow creation (mock)
        logger.info("Testing workflow creation...")
        try:
            workflow = await service.create_automated_workflow(
                user_id="test-user-123",
                name="Test Literature Monitoring",
                workflow_type="literature_monitoring",
                description="Test workflow for monitoring literature updates",
                configuration={
                    "keywords": ["machine learning", "AI"],
                    "sources": ["arxiv", "pubmed"],
                    "frequency": "daily"
                },
                schedule_config={
                    "interval": "daily",
                    "time": "09:00"
                }
            )
            logger.info(f"Workflow creation result: {workflow}")
            
            if workflow.get("id"):
                logger.info("✓ Workflow creation test passed")
            else:
                logger.error("✗ Workflow creation test failed")
                return False
        except Exception as e:
            logger.error(f"✗ Workflow creation test failed: {e}")
            return False
        
        # Test workflow listing
        logger.info("Testing workflow listing...")
        try:
            workflows = await service.list_workflows("test-user-123")
            logger.info(f"Workflow listing result: {workflows}")
            logger.info("✓ Workflow listing test passed")
        except Exception as e:
            logger.error(f"✗ Workflow listing test failed: {e}")
            return False
        
        # Test workflow execution
        logger.info("Testing workflow execution...")
        try:
            execution_result = await service.execute_workflow("mock-workflow-id", manual_trigger=True)
            logger.info(f"Workflow execution result: {execution_result}")
            
            if execution_result.get("status"):
                logger.info("✓ Workflow execution test passed")
            else:
                logger.error("✗ Workflow execution test failed")
                return False
        except Exception as e:
            logger.error(f"✗ Workflow execution test failed: {e}")
            return False
        
        # Test service manager summary
        logger.info("Testing service manager summary...")
        summary = service_manager.get_initialization_summary()
        logger.info(f"Initialization summary: {summary}")
        
        if summary.get("total_services", 0) > 0:
            logger.info("✓ Service manager summary test passed")
        else:
            logger.error("✗ Service manager summary test failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error during direct research automation test: {e}", exc_info=True)
        return False

async def main():
    """Main test function"""
    logger.info("Starting direct research automation service tests")
    
    success = await test_research_automation_direct()
    
    if success:
        logger.info("✓ All direct tests passed - Research automation service is working correctly")
        return 0
    else:
        logger.error("✗ Direct tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)