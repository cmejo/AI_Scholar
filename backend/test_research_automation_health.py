#!/usr/bin/env python3
"""
Test research automation service health endpoints
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

async def test_health_endpoints():
    """Test research automation health endpoints"""
    try:
        logger.info("Testing research automation health endpoints...")
        
        # Import FastAPI test client
        from fastapi.testclient import TestClient
        from app import app
        
        # Create test client
        client = TestClient(app)
        
        # Test research automation health endpoint
        logger.info("Testing /api/advanced/research-automation/health endpoint...")
        response = client.get("/api/advanced/research-automation/health")
        logger.info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✓ Research automation health endpoint working")
            logger.info(f"Service status: {result.get('status')}")
            logger.info(f"Service details: {result.get('service', {}).get('service_details')}")
        else:
            logger.error(f"✗ Health endpoint failed with status {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
        
        # Test detailed health check
        logger.info("Testing /api/advanced/health/detailed endpoint...")
        response = client.get("/api/advanced/health/detailed")
        logger.info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✓ Detailed health endpoint working")
            logger.info(f"Overall status: {result.get('status')}")
            
            # Check if research automation service is in the services list
            services = result.get('services', {})
            if 'research_automation' in services:
                logger.info(f"✓ Research automation service found in detailed health check")
                ra_service = services['research_automation']
                logger.info(f"Research automation status: {ra_service.get('status')}")
            else:
                logger.warning("Research automation service not found in detailed health check")
        else:
            logger.error(f"✗ Detailed health endpoint failed with status {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
        
        # Test services health check
        logger.info("Testing /api/advanced/health/services endpoint...")
        response = client.get("/api/advanced/health/services")
        logger.info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✓ Services health endpoint working")
            
            # Check if research automation service is in the services list
            services = result.get('services', {})
            if 'research_automation' in services:
                logger.info(f"✓ Research automation service found in services health check")
                ra_service = services['research_automation']
                logger.info(f"Research automation status: {ra_service.get('status')}")
            else:
                logger.warning("Research automation service not found in services health check")
        else:
            logger.error(f"✗ Services health endpoint failed with status {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error during health endpoint test: {e}", exc_info=True)
        return False

async def main():
    """Main test function"""
    logger.info("Starting research automation health endpoint tests")
    
    success = await test_health_endpoints()
    
    if success:
        logger.info("✓ All health endpoint tests passed")
        return 0
    else:
        logger.error("✗ Health endpoint tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)