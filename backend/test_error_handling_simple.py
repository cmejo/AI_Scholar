#!/usr/bin/env python3
"""
Simple test for error handling implementation
"""
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_middleware():
    """Test middleware imports"""
    try:
        from middleware.error_monitoring import ErrorMonitoringMiddleware, RequestMetricsMiddleware
        print("✓ Middleware imports successful")
        
        # Test instantiation
        error_middleware = ErrorMonitoringMiddleware(None)
        print("✓ ErrorMonitoringMiddleware instantiated")
        
        metrics_middleware = RequestMetricsMiddleware(None)
        print("✓ RequestMetricsMiddleware instantiated")
        
        # Test metrics
        metrics = metrics_middleware.get_metrics()
        print(f"✓ Metrics: {metrics}")
        
        return True
    except Exception as e:
        print(f"❌ Middleware test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test API endpoints"""
    try:
        from api.advanced_endpoints import router
        print(f"✓ Router imported with {len(router.routes)} routes")
        
        # Print some route info
        for i, route in enumerate(router.routes[:5]):  # First 5 routes
            if hasattr(route, 'path'):
                print(f"  Route {i}: {route.path}")
            elif hasattr(route, 'path_regex'):
                print(f"  Route {i}: {route.path_regex.pattern}")
        
        return True
    except Exception as e:
        print(f"❌ API endpoints test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handler():
    """Test error handler"""
    try:
        from core.error_handler import EndpointErrorHandler, handle_endpoint_errors
        print("✓ Error handler imported")
        
        # Test error response creation
        response = EndpointErrorHandler.create_error_response(
            "test_error", "Test message"
        )
        print(f"✓ Error response created: {response.error}")
        
        return True
    except Exception as e:
        print(f"❌ Error handler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Running simple error handling tests...")
    
    tests = [
        ("Error Handler", test_error_handler),
        ("Middleware", test_middleware),
        ("API Endpoints", test_api_endpoints)
    ]
    
    for name, test_func in tests:
        print(f"\n--- Testing {name} ---")
        result = test_func()
        print(f"Result: {'PASSED' if result else 'FAILED'}")