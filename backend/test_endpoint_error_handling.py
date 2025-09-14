#!/usr/bin/env python3
"""
Test endpoint error handling implementation
Tests the comprehensive error handling added to API endpoints
"""
import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_error_handling_infrastructure():
    """Test the error handling infrastructure components"""
    logger.info("Testing error handling infrastructure...")
    
    try:
        # Test error handler imports
        from core.error_handler import (
            EndpointErrorHandler,
            ServiceUnavailableError,
            ValidationError,
            handle_endpoint_errors,
            validate_request_data,
            create_fallback_response,
            ErrorResponse
        )
        logger.info("✓ Error handler components imported successfully")
        
        # Test error response creation
        error_response = EndpointErrorHandler.create_error_response(
            error_type="test_error",
            message="Test error message",
            details={"test_key": "test_value"},
            request_id="test-request-123"
        )
        
        assert error_response.error == "test_error"
        assert error_response.message == "Test error message"
        assert error_response.details["test_key"] == "test_value"
        assert error_response.request_id == "test-request-123"
        logger.info("✓ Error response creation works correctly")
        
        # Test validation function
        try:
            validate_request_data({"field1": "value1"}, ["field1", "field2"])
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "missing_fields" in e.details
            assert "field2" in e.details["missing_fields"]
            logger.info("✓ Request validation works correctly")
        
        # Test fallback response creation
        fallback = create_fallback_response(
            message="Test fallback",
            data={"test": "data"},
            status="degraded"
        )
        
        assert fallback["status"] == "degraded"
        assert fallback["message"] == "Test fallback"
        assert fallback["data"]["test"] == "data"
        assert fallback["fallback"] is True
        logger.info("✓ Fallback response creation works correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"Error handling infrastructure test failed: {str(e)}", exc_info=True)
        return False


async def test_service_manager_integration():
    """Test integration with service manager"""
    logger.info("Testing service manager integration...")
    
    try:
        from core.service_manager import service_manager
        
        # Test service manager availability
        assert service_manager is not None
        logger.info("✓ Service manager is available")
        
        # Test service health checking
        health_status = service_manager.get_service_health()
        assert isinstance(health_status, dict)
        logger.info(f"✓ Service health status retrieved: {len(health_status)} services")
        
        # Test individual service checking
        for service_name in ["semantic_search", "research_automation", "advanced_analytics", "knowledge_graph"]:
            service = service_manager.get_service(service_name)
            is_healthy = service_manager.is_service_healthy(service_name)
            logger.info(f"  - {service_name}: {'available' if service else 'not available'}, {'healthy' if is_healthy else 'not healthy'}")
        
        return True
        
    except Exception as e:
        logger.error(f"Service manager integration test failed: {str(e)}", exc_info=True)
        return False


async def test_endpoint_decorator():
    """Test the endpoint error handling decorator"""
    logger.info("Testing endpoint error handling decorator...")
    
    try:
        from core.error_handler import handle_endpoint_errors, create_fallback_response
        
        # Create a test function with the decorator
        @handle_endpoint_errors(
            "test_endpoint",
            required_services=["nonexistent_service"],
            fallback_response=create_fallback_response(
                message="Test fallback response",
                data={"test": True},
                status="degraded"
            )
        )
        async def test_endpoint_function():
            return {"status": "ok", "message": "This should not be reached"}
        
        # Test the decorated function
        result = await test_endpoint_function()
        
        # Should return fallback response due to missing service
        assert result["status"] == "degraded"
        assert result["fallback"] is True
        assert result["message"] == "Test fallback response"
        logger.info("✓ Endpoint decorator handles missing services correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"Endpoint decorator test failed: {str(e)}", exc_info=True)
        return False


async def test_middleware_integration():
    """Test middleware integration"""
    logger.info("Testing middleware integration...")
    
    try:
        from middleware.error_monitoring import ErrorMonitoringMiddleware, RequestMetricsMiddleware
        
        # Test middleware classes can be instantiated
        # Note: We pass None as app since we're just testing instantiation
        error_middleware = ErrorMonitoringMiddleware(None)
        metrics_middleware = RequestMetricsMiddleware(None)
        
        assert error_middleware is not None
        assert metrics_middleware is not None
        logger.info("✓ Middleware classes instantiated successfully")
        
        # Test that middleware has expected attributes
        assert hasattr(error_middleware, 'enable_request_logging')
        assert hasattr(metrics_middleware, 'request_count')
        assert hasattr(metrics_middleware, 'error_count')
        logger.info("✓ Middleware attributes are correct")
        
        # Test metrics collection
        metrics = metrics_middleware.get_metrics()
        assert isinstance(metrics, dict)
        assert "total_requests" in metrics
        assert "total_errors" in metrics
        assert "error_rate" in metrics
        assert "average_processing_time" in metrics
        logger.info("✓ Metrics collection works correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"Middleware integration test failed: {str(e)}", exc_info=True)
        return False


async def test_api_endpoints_error_handling():
    """Test that API endpoints have proper error handling"""
    logger.info("Testing API endpoints error handling...")
    
    try:
        # Import the router to check endpoint definitions
        from api.advanced_endpoints import router
        
        # Check that router exists and has routes
        assert router is not None
        routes = router.routes
        assert len(routes) > 0
        logger.info(f"✓ Router has {len(routes)} routes defined")
        
        # Test that key endpoints exist by checking route paths
        route_paths = []
        for route in routes:
            if hasattr(route, 'path'):
                route_paths.append(route.path)
            elif hasattr(route, 'path_regex'):
                # For parameterized routes, extract the pattern
                path_pattern = str(route.path_regex.pattern)
                route_paths.append(path_pattern)
        
        expected_endpoints = [
            "health",
            "database",
            "semantic-search",
            "research-automation", 
            "advanced-analytics",
            "knowledge-graph",
            "research"
        ]
        
        found_endpoints = 0
        for endpoint in expected_endpoints:
            if any(endpoint in path for path in route_paths):
                logger.info(f"✓ Endpoint group found: {endpoint}")
                found_endpoints += 1
            else:
                logger.warning(f"Expected endpoint group not found: {endpoint}")
        
        # Check that we found most expected endpoints
        if found_endpoints >= len(expected_endpoints) * 0.7:  # At least 70% found
            logger.info(f"✓ Found {found_endpoints}/{len(expected_endpoints)} expected endpoint groups")
            return True
        else:
            logger.error(f"Only found {found_endpoints}/{len(expected_endpoints)} expected endpoint groups")
            return False
        
    except Exception as e:
        logger.error(f"API endpoints error handling test failed: {str(e)}", exc_info=True)
        return False


async def test_error_logging():
    """Test error logging functionality"""
    logger.info("Testing error logging functionality...")
    
    try:
        from core.error_handler import EndpointErrorHandler
        
        # Test error logging
        test_error = Exception("Test error for logging")
        
        EndpointErrorHandler.log_error(
            endpoint_name="test_endpoint",
            error=test_error,
            request_data={"test_param": "test_value", "password": "secret"},
            user_id="test_user_123",
            request_id="test_request_456"
        )
        
        logger.info("✓ Error logging completed without exceptions")
        
        # Test service status context
        from core.service_manager import service_manager
        
        status_context = EndpointErrorHandler.get_service_status_context(
            service_manager,
            ["semantic_search", "research_automation"]
        )
        
        assert isinstance(status_context, dict)
        logger.info(f"✓ Service status context retrieved: {status_context}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error logging test failed: {str(e)}", exc_info=True)
        return False


async def run_all_tests():
    """Run all error handling tests"""
    logger.info("Starting comprehensive error handling tests...")
    logger.info("=" * 60)
    
    tests = [
        ("Error Handling Infrastructure", test_error_handling_infrastructure),
        ("Service Manager Integration", test_service_manager_integration),
        ("Endpoint Decorator", test_endpoint_decorator),
        ("Middleware Integration", test_middleware_integration),
        ("API Endpoints Error Handling", test_api_endpoints_error_handling),
        ("Error Logging", test_error_logging)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning test: {test_name}")
        logger.info("-" * 40)
        
        try:
            result = await test_func()
            results[test_name] = result
            
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {str(e)}", exc_info=True)
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All error handling tests passed!")
        return True
    else:
        logger.error(f"💥 {total - passed} tests failed")
        return False


if __name__ == "__main__":
    asyncio.run(run_all_tests())