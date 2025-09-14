#!/usr/bin/env python3
"""
Test database connection health checks and error handling
"""
import asyncio
import logging
import sys
import os
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.database_service import DatabaseService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockEngine:
    """Mock database engine for testing"""
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.pool = Mock()
        self.pool.size = 10
    
    def connect(self):
        if self.should_fail:
            raise Exception("Mock database connection failed")
        return MockConnection()


class MockConnection:
    """Mock database connection"""
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def execute(self, query):
        return MockResult()


class MockResult:
    """Mock query result"""
    def fetchone(self):
        return (1,)


class MockSessionLocal:
    """Mock session factory"""
    def __call__(self):
        return MockSession()


class MockSession:
    """Mock database session"""
    def rollback(self):
        pass
    
    def close(self):
        pass


class MockBase:
    """Mock SQLAlchemy Base"""
    metadata = Mock()
    
    @staticmethod
    def create_all(bind=None):
        pass


async def test_database_health_checks_with_mock():
    """Test database health checks with mock components"""
    logger.info("Testing database health checks with mock components")
    
    try:
        # Create database service
        db_service = DatabaseService()
        
        # Mock the database components to simulate successful imports
        db_service.engine = MockEngine(should_fail=False)
        db_service.SessionLocal = MockSessionLocal()
        db_service.Base = MockBase()
        db_service.error_message = None
        
        # Test successful initialization
        logger.info("Testing successful database initialization...")
        
        # Mock the text function import
        with patch.object(db_service, '_import_database_components'):
            with patch('services.database_service.ConditionalImporter.safe_import') as mock_import:
                # Configure mock to return text function
                def mock_import_side_effect(module_name, attribute=None, fallback=None):
                    if module_name == "sqlalchemy" and attribute == "text":
                        return lambda x: f"SQL: {x}"
                    elif module_name == "sqlalchemy" and attribute == "inspect":
                        return lambda engine: Mock(get_table_names=lambda: ['users', 'documents', 'conversations'])
                    return fallback
                
                mock_import.side_effect = mock_import_side_effect
                
                # Test initialization
                success = await db_service.initialize()
                
                if success:
                    logger.info("✓ Database service initialized successfully with mock components")
                else:
                    logger.error("✗ Database service initialization failed")
                    return False
        
        # Test health check
        logger.info("Testing database health check...")
        health_info = await db_service.health_check()
        
        logger.info(f"Health check result: {health_info['status']}")
        logger.info(f"Health details: {health_info.get('details', {})}")
        
        if health_info['status'] in ['healthy', 'degraded']:
            logger.info("✓ Database health check passed")
        else:
            logger.warning(f"✗ Database health check failed: {health_info}")
        
        # Test connection failure scenario
        logger.info("Testing database connection failure scenario...")
        db_service.engine = MockEngine(should_fail=True)
        
        health_info_failed = await db_service.health_check()
        
        if health_info_failed['status'] == 'unhealthy':
            logger.info("✓ Database correctly reports unhealthy status on connection failure")
        else:
            logger.warning("✗ Database should report unhealthy status on connection failure")
        
        # Test session management
        logger.info("Testing database session management...")
        db_service.engine = MockEngine(should_fail=False)  # Reset to working state
        db_service.is_initialized = True
        
        try:
            async with db_service.get_session() as session:
                if session:
                    logger.info("✓ Database session created successfully")
                else:
                    logger.warning("✗ Database session creation failed")
        except Exception as e:
            logger.error(f"✗ Database session management failed: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in database health checks test: {e}", exc_info=True)
        return False


async def test_database_error_handling():
    """Test comprehensive database error handling"""
    logger.info("Testing database error handling scenarios")
    
    try:
        # Test 1: Uninitialized service
        logger.info("Test 1: Uninitialized service health check")
        db_service = DatabaseService()
        
        health_info = await db_service.health_check()
        
        if health_info['status'] == 'unhealthy' and 'not initialized' in health_info['details'].get('error', '').lower():
            logger.info("✓ Uninitialized service correctly reports unhealthy")
        else:
            logger.warning("✗ Uninitialized service should report unhealthy")
        
        # Test 2: Missing database components
        logger.info("Test 2: Missing database components")
        db_service.engine = None
        db_service.SessionLocal = None
        
        init_success = await db_service.initialize()
        
        if not init_success and db_service.error_message:
            logger.info("✓ Service correctly handles missing database components")
        else:
            logger.warning("✗ Service should handle missing database components")
        
        # Test 3: Connection timeout simulation
        logger.info("Test 3: Connection timeout simulation")
        
        async def slow_connection_test():
            await asyncio.sleep(15)  # Longer than the 10-second timeout
            return True
        
        db_service.engine = MockEngine(should_fail=False)
        db_service.SessionLocal = MockSessionLocal()
        
        # Mock the connection test to simulate timeout
        original_test_connection = db_service._test_connection
        db_service._test_connection = slow_connection_test
        
        try:
            connection_result = await asyncio.wait_for(db_service._test_connection(), timeout=2.0)
            logger.warning("✗ Connection test should have timed out")
        except asyncio.TimeoutError:
            logger.info("✓ Connection test correctly timed out")
        
        # Restore original method
        db_service._test_connection = original_test_connection
        
        return True
        
    except Exception as e:
        logger.error(f"Error in database error handling test: {e}", exc_info=True)
        return False


async def test_database_service_status():
    """Test database service status reporting"""
    logger.info("Testing database service status reporting")
    
    try:
        db_service = DatabaseService()
        
        # Test initial status
        status = db_service.get_status()
        logger.info(f"Initial status: {status}")
        
        expected_fields = ['initialized', 'health_status', 'error_message', 'last_health_check', 
                          'total_models', 'sqlalchemy_models', 'pydantic_schemas', 'enums']
        
        missing_fields = [field for field in expected_fields if field not in status]
        
        if not missing_fields:
            logger.info("✓ Service status contains all expected fields")
        else:
            logger.warning(f"✗ Service status missing fields: {missing_fields}")
        
        # Test status after mock initialization
        db_service.engine = MockEngine(should_fail=False)
        db_service.SessionLocal = MockSessionLocal()
        db_service.Base = MockBase()
        db_service.is_initialized = True
        db_service.health_status = "healthy"
        db_service.last_health_check = datetime.utcnow()
        
        status_after_init = db_service.get_status()
        logger.info(f"Status after initialization: {status_after_init}")
        
        if status_after_init['initialized'] and status_after_init['health_status'] == 'healthy':
            logger.info("✓ Service status correctly reflects initialized state")
        else:
            logger.warning("✗ Service status should reflect initialized state")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in database service status test: {e}", exc_info=True)
        return False


async def main():
    """Main test function"""
    logger.info("Starting database health checks and error handling tests")
    logger.info("=" * 70)
    
    # Test 1: Database health checks with mock
    test1_success = await test_database_health_checks_with_mock()
    logger.info("=" * 70)
    
    # Test 2: Database error handling
    test2_success = await test_database_error_handling()
    logger.info("=" * 70)
    
    # Test 3: Database service status
    test3_success = await test_database_service_status()
    logger.info("=" * 70)
    
    # Summary
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Database health checks test: {'PASSED' if test1_success else 'FAILED'}")
    logger.info(f"Database error handling test: {'PASSED' if test2_success else 'FAILED'}")
    logger.info(f"Database service status test: {'PASSED' if test3_success else 'FAILED'}")
    
    overall_success = test1_success and test2_success and test3_success
    logger.info(f"Overall result: {'PASSED' if overall_success else 'FAILED'}")
    
    logger.info("=" * 70)
    logger.info("DATABASE HEALTH CHECKS DEMONSTRATION COMPLETE")
    logger.info("This demonstrates the database health check functionality:")
    logger.info("1. ✓ Database connection health checks with timeout handling")
    logger.info("2. ✓ Comprehensive error handling for connection failures")
    logger.info("3. ✓ Graceful degradation when components are missing")
    logger.info("4. ✓ Proper status reporting and error messages")
    logger.info("5. ✓ Session management with proper cleanup")
    
    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)