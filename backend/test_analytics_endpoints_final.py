"""
Final test script for analytics endpoints
Tests analytics endpoint functionality with correct service_manager patching
"""
import sys
import os
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

try:
    from fastapi.testclient import TestClient
    from app import app
    
    def test_analytics_endpoints():
        """Test analytics endpoints functionality"""
        client = TestClient(app)
        base_url = "/api/advanced"
        test_user_id = "test-user-123"
        
        print("Testing Analytics Endpoints...")
        print("=" * 50)
        
        # Test 1: Analytics report endpoint - service unavailable
        print("Test 1: Analytics report endpoint - service unavailable")
        with patch('core.service_manager.get_service', return_value=None):
            response = client.get(f"{base_url}/analytics/report/{test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "unavailable" and data["user_id"] == test_user_id:
                    print("✓ PASS: Service unavailable handled correctly")
                else:
                    print("✗ FAIL: Unexpected response format")
                    print(f"Response: {data}")
            else:
                print(f"✗ FAIL: Expected 200, got {response.status_code}")
        
        # Test 2: Analytics report endpoint - invalid timeframe
        print("\nTest 2: Analytics report endpoint - invalid timeframe")
        mock_service = Mock()
        with patch('core.service_manager.get_service', return_value=mock_service):
            response = client.get(f"{base_url}/analytics/report/{test_user_id}?timeframe=invalid")
            
            if response.status_code == 400:
                data = response.json()
                if "Invalid timeframe" in data["detail"]:
                    print("✓ PASS: Invalid timeframe handled correctly")
                else:
                    print("✗ FAIL: Unexpected error message")
                    print(f"Response: {data}")
            else:
                print(f"✗ FAIL: Expected 400, got {response.status_code}")
        
        # Test 3: Test all analytics endpoints are accessible
        print("\nTest 3: Testing all analytics endpoints accessibility")
        endpoints = [
            f"/analytics/report/{test_user_id}",
            f"/analytics/usage/{test_user_id}",
            f"/analytics/content/{test_user_id}",
            f"/analytics/relationships/{test_user_id}",
            f"/analytics/knowledge-patterns/{test_user_id}",
            f"/analytics/knowledge-map/{test_user_id}",
            f"/analytics/metrics/{test_user_id}"
        ]
        
        accessible_count = 0
        for endpoint in endpoints:
            try:
                with patch('core.service_manager.get_service', return_value=None):
                    response = client.get(f"{base_url}{endpoint}")
                    
                    if response.status_code in [200, 400, 422]:  # Valid HTTP responses
                        accessible_count += 1
                        print(f"  ✓ {endpoint} - accessible")
                    else:
                        print(f"  ✗ {endpoint} - unexpected status {response.status_code}")
                        
            except Exception as e:
                print(f"  ✗ {endpoint} - exception: {str(e)}")
        
        if accessible_count == len(endpoints):
            print("✓ PASS: All analytics endpoints are accessible")
        else:
            print(f"✗ FAIL: Only {accessible_count}/{len(endpoints)} endpoints accessible")
        
        # Test 4: Parameter validation tests
        print("\nTest 4: Parameter validation tests")
        validation_tests = [
            (f"/analytics/relationships/{test_user_id}?min_similarity=1.5", "min_similarity must be between 0.0 and 1.0"),
            (f"/analytics/relationships/{test_user_id}?max_relationships=2000", "max_relationships must be between 1 and 1000"),
            (f"/analytics/knowledge-patterns/{test_user_id}?min_frequency=0", "min_frequency must be at least 1"),
            (f"/analytics/knowledge-patterns/{test_user_id}?confidence_threshold=1.5", "confidence_threshold must be between 0.0 and 1.0"),
            (f"/analytics/knowledge-map/{test_user_id}?layout_algorithm=invalid", "Invalid layout_algorithm"),
            (f"/analytics/knowledge-map/{test_user_id}?max_nodes=5", "max_nodes must be between 10 and 500"),
            (f"/analytics/metrics/{test_user_id}?metric_types=invalid,unknown", "Invalid metric types")
        ]
        
        validation_pass_count = 0
        for endpoint, expected_error in validation_tests:
            try:
                mock_service = Mock()
                with patch('core.service_manager.get_service', return_value=mock_service):
                    response = client.get(f"{base_url}{endpoint}")
                    
                    if response.status_code == 400:
                        data = response.json()
                        if expected_error in data["detail"]:
                            validation_pass_count += 1
                            print(f"  ✓ Validation: {expected_error}")
                        else:
                            print(f"  ✗ Validation: Expected '{expected_error}', got '{data['detail']}'")
                    else:
                        print(f"  ✗ Validation: Expected 400, got {response.status_code}")
                        
            except Exception as e:
                print(f"  ✗ Validation exception: {str(e)}")
        
        if validation_pass_count == len(validation_tests):
            print("✓ PASS: All parameter validations work correctly")
        else:
            print(f"✗ FAIL: Only {validation_pass_count}/{len(validation_tests)} validations passed")
        
        # Test 5: Service health check integration
        print("\nTest 5: Service health check integration")
        mock_service = Mock()
        mock_health = Mock()
        mock_health.status.value = "unhealthy"
        mock_health.error_message = "Service connection failed"
        
        with patch('core.service_manager.get_service', return_value=mock_service), \
             patch('core.service_manager.check_service_health', return_value=mock_health):
            
            response = client.get(f"{base_url}/analytics/report/{test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "degraded" and "Service connection failed" in data["error"]:
                    print("✓ PASS: Service health check integration works")
                else:
                    print("✗ FAIL: Unexpected health check response")
                    print(f"Response: {data}")
            else:
                print(f"✗ FAIL: Expected 200, got {response.status_code}")
        
        print("\n" + "=" * 50)
        print("Analytics endpoints testing completed!")
        
    def test_endpoint_documentation():
        """Test that endpoints are properly documented"""
        client = TestClient(app)
        
        print("\nTesting Endpoint Documentation...")
        print("=" * 50)
        
        # Test that OpenAPI docs are accessible
        try:
            response = client.get("/docs")
            if response.status_code == 200:
                print("✓ PASS: OpenAPI documentation accessible at /docs")
            else:
                print(f"✗ FAIL: OpenAPI docs returned {response.status_code}")
        except Exception as e:
            print(f"✗ FAIL: OpenAPI docs exception: {str(e)}")
        
        # Test that OpenAPI JSON is accessible
        try:
            response = client.get("/openapi.json")
            if response.status_code == 200:
                openapi_data = response.json()
                
                # Check if analytics endpoints are documented
                paths = openapi_data.get("paths", {})
                analytics_paths = [path for path in paths.keys() if "/analytics/" in path]
                
                if len(analytics_paths) >= 7:  # We expect at least 7 analytics endpoints
                    print(f"✓ PASS: {len(analytics_paths)} analytics endpoints documented in OpenAPI")
                else:
                    print(f"✗ FAIL: Only {len(analytics_paths)} analytics endpoints found in OpenAPI")
                    print(f"Found paths: {analytics_paths}")
            else:
                print(f"✗ FAIL: OpenAPI JSON returned {response.status_code}")
        except Exception as e:
            print(f"✗ FAIL: OpenAPI JSON exception: {str(e)}")
        
        print("=" * 50)
        print("Endpoint documentation testing completed!")
    
    if __name__ == "__main__":
        try:
            test_analytics_endpoints()
            test_endpoint_documentation()
            print("\n🎉 All analytics endpoint tests completed!")
        except Exception as e:
            print(f"\n❌ Test execution failed: {str(e)}")
            import traceback
            traceback.print_exc()

except ImportError as e:
    print(f"Import error: {e}")
    print("FastAPI not available. Running basic structure validation...")
    
    # Basic functionality test without FastAPI
    def basic_test():
        print("Testing basic analytics endpoint structure...")
        
        # Test that we can import the endpoints module
        try:
            from api.advanced_endpoints import router
            print("✓ PASS: Analytics endpoints module imports successfully")
            
            # Test that the router has routes
            if hasattr(router, 'routes') and len(router.routes) > 0:
                print(f"✓ PASS: Router has {len(router.routes)} routes")
                
                # Count analytics routes
                analytics_routes = 0
                for route in router.routes:
                    if hasattr(route, 'path') and '/analytics/' in route.path:
                        analytics_routes += 1
                
                if analytics_routes >= 7:
                    print(f"✓ PASS: Found {analytics_routes} analytics routes")
                else:
                    print(f"✗ FAIL: Only found {analytics_routes} analytics routes")
            else:
                print("✗ FAIL: Router has no routes")
                
        except Exception as e:
            print(f"✗ FAIL: Cannot import analytics endpoints: {e}")
            return
        
        print("Basic analytics endpoint structure test completed!")
    
    basic_test()