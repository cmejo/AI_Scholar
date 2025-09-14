"""
Test database endpoints functionality
"""
import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_database_health_endpoint():
    """Test database health endpoint"""
    print("Testing database health endpoint...")
    
    try:
        # Import the endpoint function directly
        from api.advanced_endpoints import database_health_check
        from core.service_manager import service_manager
        
        # Initialize database service first
        await service_manager.initialize_database_service()
        
        # Call the endpoint
        result = await database_health_check()
        print(f"✅ Database health endpoint result: {result.get('status', 'unknown')}")
        print(f"   Message: {result.get('message', 'No message')}")
        
        if 'database' in result:
            db_info = result['database']
            print(f"   Database status: {db_info.get('status', 'unknown')}")
            print(f"   Database details: {db_info.get('details', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database health endpoint test failed: {e}")
        logger.error(f"Database health endpoint test failed: {e}", exc_info=True)
        return False


async def test_database_connection_endpoint():
    """Test database connection endpoint"""
    print("\nTesting database connection endpoint...")
    
    try:
        # Import the endpoint function directly
        from api.advanced_endpoints import database_connection_test
        from core.service_manager import service_manager
        
        # Initialize database service first
        await service_manager.initialize_database_service()
        
        # Call the endpoint
        result = await database_connection_test()
        print(f"✅ Database connection endpoint result: {result.get('status', 'unknown')}")
        print(f"   Message: {result.get('message', 'No message')}")
        
        if 'service_status' in result:
            service_status = result['service_status']
            print(f"   Service initialized: {service_status.get('initialized', False)}")
            print(f"   Health status: {service_status.get('health_status', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection endpoint test failed: {e}")
        logger.error(f"Database connection endpoint test failed: {e}", exc_info=True)
        return False


async def test_database_models_endpoint():
    """Test database models endpoint"""
    print("\nTesting database models endpoint...")
    
    try:
        # Import the endpoint function directly
        from api.advanced_endpoints import database_models_info
        from core.service_manager import service_manager
        
        # Initialize database service first
        await service_manager.initialize_database_service()
        
        # Call the endpoint
        result = await database_models_info()
        print(f"✅ Database models endpoint result: {result.get('status', 'unknown')}")
        print(f"   Model count: {result.get('model_count', 0)}")
        print(f"   Models: {result.get('models', [])[:5]}...")  # Show first 5
        
        return True
        
    except Exception as e:
        print(f"❌ Database models endpoint test failed: {e}")
        logger.error(f"Database models endpoint test failed: {e}", exc_info=True)
        return False


async def test_database_migration_endpoint():
    """Test database migration check endpoint"""
    print("\nTesting database migration endpoint...")
    
    try:
        # Import the endpoint function directly
        from api.advanced_endpoints import database_migration_check
        from core.service_manager import service_manager
        
        # Initialize database service first
        await service_manager.initialize_database_service()
        
        # Call the endpoint
        result = await database_migration_check()
        print(f"✅ Database migration endpoint result: {result.get('status', 'unknown')}")
        print(f"   Message: {result.get('message', 'No message')}")
        
        if 'tables' in result:
            tables_info = result['tables']
            print(f"   Tables status: {tables_info.get('status', 'unknown')}")
            print(f"   Table count: {tables_info.get('table_count', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database migration endpoint test failed: {e}")
        logger.error(f"Database migration endpoint test failed: {e}", exc_info=True)
        return False


async def test_service_manager_database_health():
    """Test database health through service manager"""
    print("\nTesting database health through service manager...")
    
    try:
        from core.service_manager import service_manager
        
        # Initialize database service
        success = await service_manager.initialize_database_service()
        print(f"✅ Database service initialization: {'successful' if success else 'failed'}")
        
        # Check if service is healthy
        is_healthy = service_manager.is_service_healthy("database")
        print(f"✅ Database service healthy: {is_healthy}")
        
        # Get service health info
        health_info = service_manager.get_service_health("database")
        print(f"✅ Database service health info: {health_info}")
        
        # Perform health check
        if service_manager.get_service("database"):
            health_result = await service_manager.check_service_health("database")
            print(f"✅ Database health check result: {health_result.status.value}")
            if health_result.error_message:
                print(f"   Error: {health_result.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service manager database health test failed: {e}")
        logger.error(f"Service manager database health test failed: {e}", exc_info=True)
        return False


async def main():
    """Run all database endpoint tests"""
    print("=" * 60)
    print("DATABASE ENDPOINTS TESTS")
    print("=" * 60)
    
    tests = [
        ("Database Health Endpoint", test_database_health_endpoint),
        ("Database Connection Endpoint", test_database_connection_endpoint),
        ("Database Models Endpoint", test_database_models_endpoint),
        ("Database Migration Endpoint", test_database_migration_endpoint),
        ("Service Manager Database Health", test_service_manager_database_health),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed - this may be expected if database is not configured")


if __name__ == "__main__":
    asyncio.run(main())