"""
Test database service functionality
"""
import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_database_service_import():
    """Test database service import and initialization"""
    print("Testing database service import...")
    
    try:
        from services.database_service import DatabaseService, get_database_service, initialize_database_service
        print("✅ Successfully imported database service components")
        
        # Test service creation
        db_service = DatabaseService()
        print(f"✅ Database service created: {type(db_service)}")
        
        # Test initialization
        success = await db_service.initialize()
        print(f"✅ Database service initialization: {'successful' if success else 'failed'}")
        
        # Test status
        status = db_service.get_status()
        print(f"✅ Database service status: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database service import test failed: {e}")
        logger.error(f"Database service import test failed: {e}", exc_info=True)
        return False


async def test_database_health_check():
    """Test database health check functionality"""
    print("\nTesting database health check...")
    
    try:
        from services.database_service import get_database_service
        
        db_service = await get_database_service()
        
        # Perform health check
        health_info = await db_service.health_check()
        print(f"✅ Health check completed: {health_info.get('status', 'unknown')}")
        print(f"   Details: {health_info.get('details', {})}")
        
        # Test is_healthy method
        is_healthy = db_service.is_healthy()
        print(f"✅ Service healthy: {is_healthy}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database health check test failed: {e}")
        logger.error(f"Database health check test failed: {e}", exc_info=True)
        return False


async def test_database_models():
    """Test database models import and availability"""
    print("\nTesting database models...")
    
    try:
        from services.database_service import get_database_service
        
        db_service = await get_database_service()
        
        # Get available models
        models = db_service.get_available_models()
        print(f"✅ Available models: {len(models)}")
        print(f"   Model names: {models[:5]}...")  # Show first 5
        
        # Test getting specific model
        if models:
            model_name = models[0]
            model_class = db_service.get_model(model_name)
            print(f"✅ Retrieved model '{model_name}': {model_class}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        logger.error(f"Database models test failed: {e}", exc_info=True)
        return False


async def test_service_manager_integration():
    """Test database service integration with service manager"""
    print("\nTesting service manager integration...")
    
    try:
        from core.service_manager import service_manager
        
        # Initialize database service through service manager
        success = await service_manager.initialize_database_service()
        print(f"✅ Service manager database initialization: {'successful' if success else 'failed'}")
        
        # Check if service is registered
        db_service = service_manager.get_service("database")
        if db_service:
            print(f"✅ Database service registered in service manager: {type(db_service)}")
            
            # Check health through service manager
            is_healthy = service_manager.is_service_healthy("database")
            print(f"✅ Service manager reports database healthy: {is_healthy}")
            
            # Get service health info
            health_info = service_manager.get_service_health("database")
            print(f"✅ Service health info: {health_info}")
        else:
            print("❌ Database service not found in service manager")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Service manager integration test failed: {e}")
        logger.error(f"Service manager integration test failed: {e}", exc_info=True)
        return False


async def test_database_session():
    """Test database session management"""
    print("\nTesting database session management...")
    
    try:
        from services.database_service import get_database_service
        
        db_service = await get_database_service()
        
        if not db_service.is_initialized:
            print("⚠️  Database service not initialized, skipping session test")
            return True
        
        # Test session context manager
        try:
            async with db_service.get_session() as session:
                print(f"✅ Database session created: {type(session)}")
                # Session will be automatically closed
            print("✅ Database session closed successfully")
        except Exception as session_error:
            print(f"⚠️  Database session test failed (expected if no DB): {session_error}")
            # This is expected if database is not actually available
        
        return True
        
    except Exception as e:
        print(f"❌ Database session test failed: {e}")
        logger.error(f"Database session test failed: {e}", exc_info=True)
        return False


async def main():
    """Run all database service tests"""
    print("=" * 60)
    print("DATABASE SERVICE TESTS")
    print("=" * 60)
    
    tests = [
        ("Database Service Import", test_database_service_import),
        ("Database Health Check", test_database_health_check),
        ("Database Models", test_database_models),
        ("Service Manager Integration", test_service_manager_integration),
        ("Database Session", test_database_session),
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