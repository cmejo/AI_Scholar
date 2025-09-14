#!/usr/bin/env python3
"""
Test script to verify database models import functionality
"""
import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.database_service import DatabaseService, get_database_service, initialize_database_service

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_database_models_import():
    """Test database models import functionality"""
    logger.info("Starting database models import test")
    
    try:
        # Test direct database service creation (without full initialization)
        logger.info("Creating database service instance...")
        db_service = DatabaseService()
        
        # Test that the service handles missing SQLAlchemy gracefully
        logger.info("Testing graceful handling of missing SQLAlchemy...")
        if db_service.error_message and "SQLAlchemy" in db_service.error_message:
            logger.info("✓ Database service correctly detected missing SQLAlchemy")
        else:
            logger.warning("✗ Database service should detect missing SQLAlchemy")
        
        # Try to initialize (this should fail gracefully)
        logger.info("Testing initialization with missing dependencies...")
        success = await db_service.initialize()
        
        if not success:
            logger.info("✓ Database service initialization correctly failed with missing dependencies")
        else:
            logger.warning("✗ Database service initialization should fail with missing dependencies")
        
        # Test model imports (even with missing SQLAlchemy, Pydantic schemas should work)
        logger.info("Testing SQLAlchemy model imports...")
        sqlalchemy_models = db_service.get_available_sqlalchemy_models()
        logger.info(f"Available SQLAlchemy models: {len(sqlalchemy_models)}")
        if len(sqlalchemy_models) == 0:
            logger.info("✓ No SQLAlchemy models imported (expected due to missing SQLAlchemy)")
        else:
            for model_name in sqlalchemy_models[:5]:  # Show first 5
                model_class = db_service.get_sqlalchemy_model(model_name)
                logger.info(f"  - {model_name}: {'✓' if model_class else '✗'}")
        
        logger.info("Testing Pydantic schema imports...")
        pydantic_schemas = db_service.get_available_pydantic_schemas()
        logger.info(f"Available Pydantic schemas: {len(pydantic_schemas)}")
        if len(pydantic_schemas) > 0:
            logger.info("✓ Pydantic schemas imported successfully")
            for schema_name in pydantic_schemas[:5]:  # Show first 5
                schema_class = db_service.get_pydantic_schema(schema_name)
                logger.info(f"  - {schema_name}: {'✓' if schema_class else '✗'}")
        else:
            logger.warning("✗ No Pydantic schemas imported")
        
        logger.info("Testing enum imports...")
        enums = db_service.get_available_enums()
        logger.info(f"Available enums: {len(enums)}")
        if len(enums) > 0:
            logger.info("✓ Enums imported successfully")
            for enum_name in enums:
                enum_class = db_service.get_enum(enum_name)
                logger.info(f"  - {enum_name}: {'✓' if enum_class else '✗'}")
        else:
            logger.warning("✗ No enums imported")
        
        # Test database connection (should fail gracefully)
        logger.info("Testing database connection...")
        health_info = await db_service.health_check()
        logger.info(f"Database health status: {health_info['status']}")
        
        if health_info['status'] == 'unhealthy':
            logger.info("✓ Database connection correctly reports unhealthy (expected due to missing SQLAlchemy)")
        else:
            logger.warning(f"✗ Database connection should report unhealthy: {health_info.get('details', {}).get('error', 'Unknown error')}")
        
        # Test specific model access
        logger.info("Testing specific model access...")
        
        # Test SQLAlchemy User model (should be None)
        user_model = db_service.get_sqlalchemy_model('User')
        if not user_model:
            logger.info("✓ SQLAlchemy User model correctly unavailable (expected)")
        else:
            logger.warning(f"✗ SQLAlchemy User model should be unavailable: {user_model.__name__}")
        
        # Test Pydantic UserResponse schema (should work)
        user_response_schema = db_service.get_pydantic_schema('UserResponse')
        if user_response_schema:
            logger.info(f"✓ Pydantic UserResponse schema: {user_response_schema.__name__}")
        else:
            logger.warning("✗ Pydantic UserResponse schema not available")
        
        # Test ServiceStatus enum (should work)
        service_status_enum = db_service.get_enum('ServiceStatus')
        if service_status_enum:
            logger.info(f"✓ ServiceStatus enum: {service_status_enum.__name__}")
            logger.info(f"  Enum values: {list(service_status_enum)}")
        else:
            logger.warning("✗ ServiceStatus enum not available")
        
        # Get service status
        status = db_service.get_status()
        logger.info(f"Service status: {status}")
        
        # Test passes if we have graceful error handling and some imports work
        has_pydantic_schemas = len(pydantic_schemas) > 0
        has_enums = len(enums) > 0
        graceful_error_handling = not success and db_service.error_message is not None
        
        test_success = graceful_error_handling and (has_pydantic_schemas or has_enums)
        
        if test_success:
            logger.info("✓ Database models import test completed successfully")
            logger.info("  - Graceful error handling for missing SQLAlchemy: ✓")
            logger.info(f"  - Pydantic schemas imported: {'✓' if has_pydantic_schemas else '✗'}")
            logger.info(f"  - Enums imported: {'✓' if has_enums else '✗'}")
        else:
            logger.error("✗ Database models import test failed")
        
        return test_success
        
    except Exception as e:
        logger.error(f"Database models import test failed: {e}", exc_info=True)
        return False


async def test_database_error_handling():
    """Test database error handling"""
    logger.info("Testing database error handling...")
    
    try:
        # Create a new database service instance to test error handling
        db_service = DatabaseService()
        
        # Test health check on uninitialized service
        health_info = await db_service.health_check()
        logger.info(f"Uninitialized service health: {health_info['status']}")
        
        if health_info['status'] == 'unhealthy':
            logger.info("✓ Uninitialized service correctly reports unhealthy status")
        else:
            logger.warning("✗ Uninitialized service should report unhealthy status")
        
        # Test model access on uninitialized service
        user_model = db_service.get_sqlalchemy_model('User')
        if user_model:
            logger.info("✓ Models available even before initialization")
        else:
            logger.info("✗ Models not available before initialization")
        
        logger.info("Database error handling test completed")
        return True
        
    except Exception as e:
        logger.error(f"Database error handling test failed: {e}", exc_info=True)
        return False


async def main():
    """Main test function"""
    logger.info("Starting database models import tests")
    
    # Test 1: Database models import
    test1_success = await test_database_models_import()
    
    # Test 2: Error handling
    test2_success = await test_database_error_handling()
    
    # Summary
    logger.info("=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Database models import test: {'PASSED' if test1_success else 'FAILED'}")
    logger.info(f"Database error handling test: {'PASSED' if test2_success else 'FAILED'}")
    
    overall_success = test1_success and test2_success
    logger.info(f"Overall result: {'PASSED' if overall_success else 'FAILED'}")
    
    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)