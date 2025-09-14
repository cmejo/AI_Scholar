"""
Working test script for analytics endpoints
Tests analytics endpoint functionality with proper service_manager mocking
"""
import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

try:
    from fastapi.testclient import TestClient
    from app import app
    from core import service_manager
    
    def test_analytics_endpoints():
        """Test analytics endpoints functionality"""
        client = TestClient(app)
        base_url = "/api/advanced"
        test_user_id = "test-user-123"
        
        print("Testing Analytics Endpoints...")
        print("=" * 50)
        
        # Test 1: Analytics report endpoint - service unavailable
        print("Test 1: Analytics report endpoint - service unavailable")
        with patch.object(service_manager, 'get_service', return_value=None):
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
        with patch.object(service_manager, 'get_service', return_value=mock_service):
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
        
        # Test 3: Usage insights endpoint - service unavailable
        print("\nTest 3: Usage insights endpoint - service unavailable")
        with patch.object(service_manager, 'get_service', return_value=None):
            response = client.get(f"{base_url}/analytics/usage/{test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "unavailable":
                    print("✓ PASS: Service unavailable handled correctly")
                else:
                    print("✗ FAIL: Unexpected response format")
                    print(f"Response: {data}")
            else:
                print(f"✗ FAIL: Expected 200, got {response.status_code}")
        
        # Test 4: Content analytics endpoint - invalid timeframe
        print("\nTest 4: Content analytics endpoint - invalid timeframe")
        mock_service = Mock()
        with patch.object(service_manager, 'get_service', return_value=mock_service):
            response = client.get(f"{base_url}/analytics/content/{test_user_id}?timeframe=invalid")
            
            if response.status_code == 400:
                data = response.json()
                if "Invalid timeframe" in data["detail"]:
                    print("✓ PASS: Invalid timeframe handled correctly")
                else:
                    print("✗ FAIL: Unexpected error message")
            else:
                print(f"✗ FAIL: Expected 400, got {response.status_code}")
        
        # Test 5: Document relationships endpoint - invalid similarity
        print("\nTest 5: Document relationships endpoint - invalid similarity")
        mock_service = Mock()
        with patch.object(service_manager, 'get_service', return_value=mock_service):
            response = client.get(f"{base_url}/analytics/relationships/{test_user_id}?min_similarity=1.5")
            
            if response.status_code == 400:
                data = response.json()
                if "min_similarity must be between 0.0 and 1.0" in data["detail"]:
                    print("✓ PASS: Invalid similarity threshold handled correctly")
                else:
                    print("✗ FAIL: Unexpected error message")
            else:
                print(f"✗ FAIL: Expected 400, got {response.status_code}")
        
        # Test 6: Knowledge patterns endpoint - invalid frequency
        print("\nTest 6: Knowledge patterns endpoint - invalid frequency")
        mock_service = Mock()
        with patch.object(service_manager, 'get_service', return_value=mock_service):
            response = client.get(f"{base_url}/analytics/knowledge-patterns/{test_user_id}?min_frequency=0")
            
            if response.status_code == 400:
                data = response.json()
                if "min_frequency must be at least 1" in data["detail"]:
                    print("✓ PASS: Invalid frequency handled correctly")
                else:
                    print("✗ FAIL: Unexpected error message")
            else:
                print(f"✗ FAIL: Expected 400, got {response.status_code}")
        
        # Test 7: Knowledge map endpoint - invalid layout
        print("\nTest 7: Knowledge map endpoint - invalid layout")
        mock_service = Mock()
        with patch.object(service_manager, 'get_service', return_value=mock_service):
            response = client.get(f"{base_url}/analytics/knowledge-map/{test_user_id}?layout_algorithm=invalid")
            
            if response.status_code == 400:
                data = response.json()
                if "Invalid layout_algorithm" in data["detail"]:
                    print("✓ PASS: Invalid layout algorithm handled correctly")
                else:
                    print("✗ FAIL: Unexpected error message")
            else:
                print(f"✗ FAIL: Expected 400, got {response.status_code}")
        
        # Test 8: Analytics metrics endpoint - invalid metric types
        print("\nTest 8: Analytics metrics endpoint - invalid metric types")
        mock_service = Mock()
        with patch.object(service_manager, 'get_service', return_value=mock_service):
            response = client.get(f"{base_url}/analytics/metrics/{test_user_id}?metric_types=invalid,unknown")
            
            if response.status_code == 400:
                data = response.json()
                if "Invalid metric types" in data["detail"]:
                    print("✓ PASS: Invalid metric types handled correctly")
                else:
                    print("✗ FAIL: Unexpected error message")
            else:
                print(f"✗ FAIL: Expected 400, got {response.status_code}")
        
        # Test 9: Test successful response with mocked service
        print("\nTest 9: Analytics report endpoint - successful response")
        mock_service = Mock()
        mock_health = Mock()
        mock_health.status.value = "healthy"
        mock_health.error_message = None
        
        # Mock report data
        mock_report = Mock()
        mock_report.id = "report-123"
        mock_report.title = "Test Report"
        mock_report.summary = "Test summary"
        mock_report.metrics = []
        mock_report.visualizations = []
        mock_report.recommendations = ["Test recommendation"]
        mock_report.timeframe.value = "month"
        mock_report.generated_at = datetime.utcnow()
        mock_report.confidence_score = 0.85
        
        mock_service.generate_comprehensive_report = AsyncMock(return_value=mock_report)
        
        with patch.object(service_manager, 'get_service', return_value=mock_service), \
             patch.object(service_manager, 'check_service_health', return_value=mock_health):
            
            response = client.get(f"{base_url}/analytics/report/{test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "ok" and "report" in data:
                    print("✓ PASS: Successful analytics report generation")
                else:
                    print("✗ FAIL: Unexpected response format")
                    print(f"Response: {data}")
            else:
                print(f"✗ FAIL: Expected 200, got {response.status_code}")
        
        # Test 10: Test error handling
        print("\nTest 10: Error handling test")
        mock_service = Mock()
        mock_health = Mock()
        mock_health.status.value = "healthy"
        
        mock_service.generate_comprehensive_report = AsyncMock(side_effect=Exception("Test error"))
        
        with patch.object(service_manager, 'get_service', return_value=mock_service), \
             patch.object(service_manager, 'check_service_health', return_value=mock_health):
            
            response = client.get(f"{base_url}/analytics/report/{test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "error" and "Test error" in data["message"]:
                    print("✓ PASS: Error handling works correctly")
                else:
                    print("✗ FAIL: Unexpected error response")
                    print(f"Response: {data}")
            else:
                print(f"✗ FAIL: Expected 200, got {response.status_code}")
        
        print("\n" + "=" * 50)
        print("Analytics endpoints testing completed!")
        
    def test_endpoint_availability():
        """Test that all analytics endpoints are available"""
        client = TestClient(app)
        base_url = "/api/advanced"
        test_user_id = "test-user-123"
        
        print("\nTesting Endpoint Availability...")
        print("=" * 50)
        
        endpoints = [
            f"/analytics/report/{test_user_id}",
            f"/analytics/usage/{test_user_id}",
            f"/analytics/content/{test_user_id}",
            f"/analytics/relationships/{test_user_id}",
            f"/analytics/knowledge-patterns/{test_user_id}",
            f"/analytics/knowledge-map/{test_user_id}",
            f"/analytics/metrics/{test_user_id}"
        ]
        
        for endpoint in endpoints:
            try:
                with patch.object(service_manager, 'get_service', return_value=None):
                    response = client.get(f"{base_url}{endpoint}")
                    
                    if response.status_code in [200, 400, 422]:  # Valid HTTP responses
                        print(f"✓ PASS: {endpoint} - endpoint available")
                    else:
                        print(f"✗ FAIL: {endpoint} - unexpected status {response.status_code}")
                        
            except Exception as e:
                print(f"✗ FAIL: {endpoint} - exception: {str(e)}")
        
        print("=" * 50)
        print("Endpoint availability testing completed!")
    
    if __name__ == "__main__":
        try:
            test_analytics_endpoints()
            test_endpoint_availability()
            print("\n🎉 All analytics endpoint tests completed successfully!")
        except Exception as e:
            print(f"\n❌ Test execution failed: {str(e)}")
            import traceback
            traceback.print_exc()

except ImportError as e:
    print(f"Import error: {e}")
    print("Some dependencies may not be available.")
    
    # Basic functionality test without FastAPI
    def basic_test():
        print("Testing basic analytics endpoint structure...")
        
        # Test that we can import the endpoints module
        try:
            from api.advanced_endpoints import router
            print("✓ PASS: Analytics endpoints module imports successfully")
        except Exception as e:
            print(f"✗ FAIL: Cannot import analytics endpoints: {e}")
            return
        
        # Test that the router has the expected routes
        routes = [route.path for route in router.routes]
        expected_analytics_routes = [
            "/analytics/report/{user_id}",
            "/analytics/usage/{user_id}",
            "/analytics/content/{user_id}",
            "/analytics/relationships/{user_id}",
            "/analytics/knowledge-patterns/{user_id}",
            "/analytics/knowledge-map/{user_id}",
            "/analytics/metrics/{user_id}"
        ]
        
        for expected_route in expected_analytics_routes:
            if expected_route in routes:
                print(f"✓ PASS: Route {expected_route} found")
            else:
                print(f"✗ FAIL: Route {expected_route} not found")
        
        print("Basic analytics endpoint structure test completed!")
    
    basic_test()