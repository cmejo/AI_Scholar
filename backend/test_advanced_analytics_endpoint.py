#!/usr/bin/env python3
"""
Test script for Advanced Analytics Service endpoint
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from core.service_manager import ServiceManager
from api.advanced_endpoints import advanced_analytics_health_check

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_advanced_analytics_endpoint():
    """Test advanced analytics health check endpoint"""
    logger.info("Testing Advanced Analytics Service endpoint...")
    
    # Create and initialize service manager
    service_manager_instance = ServiceManager()
    
    try:
        # Initialize the advanced analytics service
        logger.info("Initializing advanced analytics service...")
        success = await service_manager_instance.initialize_advanced_analytics_service()
        
        if not success:
            logger.error("❌ Service initialization failed")
            return False
        
        # Import the service manager module to set the global instance
        import core.service_manager as sm_module
        sm_module.service_manager = service_manager_instance
        
        # Test the health check endpoint
        logger.info("Testing health check endpoint...")
        result = await advanced_analytics_health_check()
        
        logger.info(f"✅ Health check endpoint result: {result}")
        
        # Verify the response structure
        expected_fields = ["status", "timestamp", "service", "message"]
        for field in expected_fields:
            if field not in result:
                logger.error(f"❌ Missing field in response: {field}")
                return False
        
        # Verify service details
        if "service" in result and isinstance(result["service"], dict):
            service_fields = ["name", "status", "last_check", "dependencies", "service_details"]
            for field in service_fields:
                if field not in result["service"]:
                    logger.error(f"❌ Missing service field: {field}")
                    return False
        
        logger.info("✅ Response structure validation: SUCCESS")
        
        # Test service status
        if result.get("status") in ["ok", "healthy"]:
            logger.info("✅ Service status: HEALTHY")
        else:
            logger.warning(f"⚠️ Service status: {result.get('status')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}", exc_info=True)
        return False

async def main():
    """Main test function"""
    logger.info("Starting Advanced Analytics Service endpoint test...")
    
    success = await test_advanced_analytics_endpoint()
    
    if success:
        logger.info("🎉 All endpoint tests passed!")
        return 0
    else:
        logger.error("💥 Some endpoint tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)