#!/usr/bin/env python3
"""
Test script to verify enhanced service initialization error handling
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging to capture detailed error handling logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('service_initialization_error_handling_test.log')
    ]
)

logger = logging.getLogger(__name__)


async def test_service_initialization_error_handling():
    """Test the enhanced service initialization error handling"""
    
    try:
        logger.info("Starting service initialization error handling test")
        
        # Import the service manager
        from core.service_manager import ServiceManager
        
        # Create a new service manager instance for testing
        test_service_manager = ServiceManager()
        
        logger.info("Created test service manager instance")
        
        # Test 1: Test initialization with invalid service name
        logger.info("=== Test 1: Invalid service name ===")
        result1 = await test_service_manager.initialize_service(
            service_name="",  # Invalid empty name
            service_factory=lambda: "test_service",
            dependencies=[]
        )
        logger.info(f"Test 1 result (should be False): {result1}")
        assert result1 == False, "Expected False for invalid service name"
        
        # Test 2: Test initialization with non-callable factory
        logger.info("=== Test 2: Non-callable factory ===")
        result2 = await test_service_manager.initialize_service(
            service_name="test_service_2",
            service_factory="not_callable",  # Invalid non-callable factory
            dependencies=[]
        )
        logger.info(f"Test 2 result (should be False): {result2}")
        assert result2 == False, "Expected False for non-callable factory"
        
        # Test 3: Test initialization with missing dependencies
        logger.info("=== Test 3: Missing dependencies ===")
        result3 = await test_service_manager.initialize_service(
            service_name="test_service_3",
            service_factory=lambda: "test_service",
            dependencies=["non_existent_service"]  # Missing dependency
        )
        logger.info(f"Test 3 result (should be False): {result3}")
        assert result3 == False, "Expected False for missing dependencies"
        
        # Test 4: Test successful initialization
        logger.info("=== Test 4: Successful initialization ===")
        
        class TestService:
            def __init__(self):
                self.status = "healthy"
            
            def get_status(self):
                return {"status": "healthy", "type": "test"}
            
            async def health_check(self):
                return {"status": "healthy", "message": "Test service is running"}
        
        result4 = await test_service_manager.initialize_service(
            service_name="test_service_4",
            service_factory=lambda: TestService(),
            dependencies=[]
        )
        logger.info(f"Test 4 result (should be True): {result4}")
        assert result4 == True, "Expected True for successful initialization"
        
        # Test 5: Test factory that returns None
        logger.info("=== Test 5: Factory returns None ===")
        result5 = await test_service_manager.initialize_service(
            service_name="test_service_5",
            service_factory=lambda: None,  # Factory returns None
            dependencies=[]
        )
        logger.info(f"Test 5 result (should be False): {result5}")
        assert result5 == False, "Expected False for factory returning None"
        
        # Test 6: Test factory that raises exception
        logger.info("=== Test 6: Factory raises exception ===")
        def failing_factory():
            raise RuntimeError("Test factory failure")
        
        result6 = await test_service_manager.initialize_service(
            service_name="test_service_6",
            service_factory=failing_factory,
            dependencies=[],
            max_retries=2,  # Test retry mechanism
            recovery_strategy="retry"
        )
        logger.info(f"Test 6 result (should be False): {result6}")
        assert result6 == False, "Expected False for failing factory"
        
        # Test 7: Test fallback recovery strategy
        logger.info("=== Test 7: Fallback recovery strategy ===")
        result7 = await test_service_manager.initialize_service(
            service_name="semantic_search",  # This should trigger fallback to mock service
            service_factory=failing_factory,
            dependencies=[],
            max_retries=1,
            recovery_strategy="fallback"
        )
        logger.info(f"Test 7 result (should be True due to fallback): {result7}")
        # Note: This might be True if fallback to mock service succeeds
        
        # Test 8: Test service health status tracking
        logger.info("=== Test 8: Service health status tracking ===")
        health_status = test_service_manager.get_service_health()
        logger.info(f"Current service health status: {health_status}")
        
        # Test 9: Test initialization summary
        logger.info("=== Test 9: Initialization summary ===")
        summary = test_service_manager.get_initialization_summary()
        logger.info(f"Initialization summary: {summary}")
        
        # Test 10: Test database service initialization (if available)
        logger.info("=== Test 10: Database service initialization ===")
        try:
            db_result = await test_service_manager.initialize_database_service()
            logger.info(f"Database service initialization result: {db_result}")
        except Exception as e:
            logger.info(f"Database service initialization failed (expected): {e}")
        
        # Test 11: Test semantic search service initialization
        logger.info("=== Test 11: Semantic search service initialization ===")
        try:
            semantic_result = await test_service_manager.initialize_semantic_search_service()
            logger.info(f"Semantic search service initialization result: {semantic_result}")
        except Exception as e:
            logger.info(f"Semantic search service initialization failed: {e}")
        
        logger.info("=== All tests completed successfully ===")
        
        # Print final service status
        final_health = test_service_manager.get_service_health()
        final_summary = test_service_manager.get_initialization_summary()
        
        logger.info("=== Final Status ===")
        logger.info(f"Final service health: {final_health}")
        logger.info(f"Final summary: {final_summary}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False


async def main():
    """Main test function"""
    logger.info("Starting service initialization error handling tests")
    
    success = await test_service_initialization_error_handling()
    
    if success:
        logger.info("All tests passed successfully!")
        return 0
    else:
        logger.error("Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)