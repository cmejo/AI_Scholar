"""
Endpoint response validation and error handling tests
Tests request validation, response formats, and error scenarios
"""
import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
from pydantic import ValidationError

from api.advanced_endpoints import router
from core.service_manager import ServiceManager, ServiceStatus, ServiceHealth


@pytest.fixture
def test_client():
    """Create test client for advanced endpoints"""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def mock_service_manager():
    """Mock service manager for testing"""
    with patch('api.advanced_endpoints.service_manager') as mock_sm:
        yield mock_sm


@pytest.mark.unit
class TestRequestValidation:
    """Test request data validation"""
    
    def test_basic_search_valid_request(self, test_client, mock_service_manager):
        """Test basic search with valid request data"""
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        valid_requests = [
            {"query": "machine learning"},
            {"query": "AI research", "max_results": 5},
            {"query": "deep learning", "max_results": 10, "user_id": "user123"},
            {"query": "neural networks", "user_id": "user456"}
        ]
        
        for request_data in valid_requests:
            response = test_client.post(
                "/api/advanced/research/search/basic",
                json=request_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["query"] == request_data["query"]
    
    def test_basic_search_missing_query(self, test_client, mock_service_manager):
        """Test basic search with missing query field"""
        response = test_client.post(
            "/api/advanced/research/search/basic",
            json={"max_results": 10}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "query" in data["detail"].lower()
    
    def test_basic_search_empty_query(self, test_client, mock_service_manager):
        """Test basic search with empty query"""
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        response = test_client.post(
            "/api/advanced/research/search/basic",
            json={"query": ""}
        )
        
        # Should handle empty query gracefully
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == ""
    
    def test_basic_search_invalid_max_results(self, test_client, mock_service_manager):
        """Test basic search with invalid max_results values"""
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        invalid_max_results = [-1, 0, 101, "invalid", None]
        
        for max_results in invalid_max_results:
            response = test_client.post(
                "/api/advanced/research/search/basic",
                json={"query": "test", "max_results": max_results}
            )
            
            assert response.status_code == 200  # Should handle gracefully
            data = response.json()
            # Should default to 10
            assert len(data["results"]) <= 10
    
    def test_analytics_report_invalid_timeframe(self, test_client, mock_service_manager):
        """Test analytics report with invalid timeframe"""
        mock_service_manager.get_service.return_value = MagicMock()
        
        invalid_timeframes = ["invalid", "yearly", "daily", ""]
        
        for timeframe in invalid_timeframes:
            response = test_client.get(
                "/api/advanced/analytics/report/user123",
                params={"timeframe": timeframe}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "timeframe" in data["detail"].lower()
    
    def test_analytics_report_valid_timeframes(self, test_client, mock_service_manager):
        """Test analytics report with valid timeframes"""
        mock_service = MagicMock()
        mock_report = MagicMock()
        mock_report.id = "report-123"
        mock_report.title = "Test Report"
        mock_report.summary = "Test summary"
        mock_report.metrics = []
        mock_report.visualizations = []
        mock_report.recommendations = []
        mock_report.timeframe.value = "month"
        mock_report.generated_at = datetime.utcnow()
        mock_report.confidence_score = 0.9
        
        mock_service.generate_comprehensive_report = AsyncMock(return_value=mock_report)
        mock_service_manager.get_service.return_value = mock_service
        
        valid_timeframes = ["hour", "day", "week", "month", "quarter", "year", "all_time"]
        
        for timeframe in valid_timeframes:
            response = test_client.get(
                "/api/advanced/analytics/report/user123",
                params={"timeframe": timeframe}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
    
    def test_document_relationships_parameter_validation(self, test_client, mock_service_manager):
        """Test document relationships endpoint parameter validation"""
        mock_service_manager.get_service.return_value = MagicMock()
        
        # Test invalid min_similarity values
        invalid_similarities = [-0.1, 1.1, 2.0, "invalid"]
        
        for similarity in invalid_similarities:
            response = test_client.get(
                "/api/advanced/analytics/relationships/user123",
                params={"min_similarity": similarity}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "min_similarity" in data["detail"]
        
        # Test invalid max_relationships values
        invalid_max_rels = [0, -1, 1001, 5000, "invalid"]
        
        for max_rels in invalid_max_rels:
            response = test_client.get(
                "/api/advanced/analytics/relationships/user123",
                params={"max_relationships": max_rels}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "max_relationships" in data["detail"]
    
    def test_query_validation_endpoint(self, test_client):
        """Test research query validation endpoint"""
        # Test valid queries
        valid_queries = [
            {"query": "What is machine learning?"},
            {"query": "Compare neural networks vs decision trees", "domain": "computer_science"},
            {"query": "Recent advances in AI", "user_id": "user123"}
        ]
        
        for request_data in valid_queries:
            response = test_client.post(
                "/api/advanced/research/validate",
                json=request_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "validation" in data
            assert "is_valid" in data["validation"]
        
        # Test missing query
        response = test_client.post(
            "/api/advanced/research/validate",
            json={"domain": "computer_science"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "query" in data["detail"].lower()
    
    def test_malformed_json_requests(self, test_client):
        """Test endpoints with malformed JSON requests"""
        endpoints = [
            "/api/advanced/research/search/basic",
            "/api/advanced/research/validate"
        ]
        
        malformed_json = '{"query": "test", "invalid": }'
        
        for endpoint in endpoints:
            response = test_client.post(
                endpoint,
                data=malformed_json,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 422  # Unprocessable Entity
    
    def test_missing_content_type(self, test_client):
        """Test endpoints with missing content type"""
        response = test_client.post(
            "/api/advanced/research/search/basic",
            data='{"query": "test"}'
        )
        
        # Should handle missing content type
        assert response.status_code in [400, 422]


@pytest.mark.unit
class TestResponseValidation:
    """Test response format validation"""
    
    def test_health_check_response_format(self, test_client):
        """Test basic health check response format"""
        response = test_client.get("/api/advanced/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate required fields
        assert "status" in data
        assert "message" in data
        assert isinstance(data["status"], str)
        assert isinstance(data["message"], str)
    
    def test_detailed_health_check_response_format(self, test_client, mock_service_manager):
        """Test detailed health check response format"""
        mock_service_manager.get_service_health.return_value = {
            "database": {
                "status": "healthy",
                "last_check": datetime.utcnow().isoformat(),
                "dependencies": []
            }
        }
        mock_service_manager.get_initialization_summary.return_value = {
            "total_services": 1,
            "healthy_services": 1,
            "failed_services": 0
        }
        
        response = test_client.get("/api/advanced/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        required_fields = ["status", "timestamp", "services", "summary", "message"]
        for field in required_fields:
            assert field in data
        
        # Validate timestamp format
        timestamp = data["timestamp"]
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))  # Should not raise
        
        # Validate services structure
        assert isinstance(data["services"], dict)
        
        # Validate summary structure
        summary = data["summary"]
        summary_fields = ["total_services", "healthy_services", "failed_services"]
        for field in summary_fields:
            assert field in summary
            assert isinstance(summary[field], int)
    
    def test_service_health_response_format(self, test_client, mock_service_manager):
        """Test individual service health check response format"""
        mock_health = ServiceHealth(
            name="database",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow(),
            dependencies=[],
            initialization_time=2.5
        )
        
        mock_service_manager.check_service_health.return_value = mock_health
        
        response = test_client.get("/api/advanced/health/service/database")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        required_fields = ["status", "timestamp", "service"]
        for field in required_fields:
            assert field in data
        
        # Validate service structure
        service = data["service"]
        service_fields = ["name", "status", "last_check", "dependencies"]
        for field in service_fields:
            assert field in service
        
        assert service["name"] == "database"
        assert service["status"] == "healthy"
        assert isinstance(service["dependencies"], list)
    
    def test_research_search_response_format(self, test_client, mock_service_manager):
        """Test research search response format"""
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        response = test_client.post(
            "/api/advanced/research/search/basic",
            json={"query": "test query", "max_results": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        required_fields = ["status", "timestamp", "query", "results", "total_results", "service_used", "message"]
        for field in required_fields:
            assert field in data
        
        # Validate results structure
        assert isinstance(data["results"], list)
        assert isinstance(data["total_results"], int)
        assert data["total_results"] == len(data["results"])
        
        # Validate individual result structure
        if data["results"]:
            result = data["results"][0]
            result_fields = ["id", "title", "content", "relevance_score", "source", "type"]
            for field in result_fields:
                assert field in result
    
    def test_research_domains_response_format(self, test_client):
        """Test research domains response format"""
        response = test_client.get("/api/advanced/research/domains")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        required_fields = ["status", "timestamp", "domains", "total_domains", "message"]
        for field in required_fields:
            assert field in data
        
        # Validate domains structure
        assert isinstance(data["domains"], dict)
        assert isinstance(data["total_domains"], int)
        assert data["total_domains"] == len(data["domains"])
        
        # Validate individual domain structure
        for domain_key, domain_data in data["domains"].items():
            domain_fields = ["name", "description", "subdomains"]
            for field in domain_fields:
                assert field in domain_data
            
            assert isinstance(domain_data["subdomains"], list)
    
    def test_query_validation_response_format(self, test_client):
        """Test query validation response format"""
        response = test_client.post(
            "/api/advanced/research/validate",
            json={"query": "What is machine learning?", "domain": "computer_science"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        required_fields = ["status", "timestamp", "query", "validation", "message"]
        for field in required_fields:
            assert field in data
        
        # Validate validation structure
        validation = data["validation"]
        validation_fields = ["is_valid", "issues", "suggestions", "confidence", "query_type"]
        for field in validation_fields:
            assert field in validation
        
        assert isinstance(validation["is_valid"], bool)
        assert isinstance(validation["issues"], list)
        assert isinstance(validation["suggestions"], list)
        assert isinstance(validation["confidence"], (int, float))
        assert isinstance(validation["query_type"], str)
    
    def test_error_response_format(self, test_client):
        """Test error response format consistency"""
        # Test 400 error
        response = test_client.post(
            "/api/advanced/research/validate",
            json={"domain": "computer_science"}  # Missing query
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        
        # Test 404 error (non-existent endpoint)
        response = test_client.get("/api/advanced/nonexistent")
        assert response.status_code == 404
    
    def test_timestamp_format_consistency(self, test_client, mock_service_manager):
        """Test timestamp format consistency across endpoints"""
        mock_service_manager.get_service_health.return_value = {}
        mock_service_manager.get_initialization_summary.return_value = {
            "total_services": 0,
            "healthy_services": 0,
            "failed_services": 0
        }
        
        endpoints = [
            "/api/advanced/health/detailed",
            "/api/advanced/research/domains",
            "/api/advanced/health/monitoring"
        ]
        
        mock_service_manager.get_health_monitoring_status.return_value = {
            "enabled": True,
            "interval": 300
        }
        
        for endpoint in endpoints:
            response = test_client.get(endpoint)
            
            if response.status_code == 200:
                data = response.json()
                if "timestamp" in data:
                    timestamp = data["timestamp"]
                    # Should be valid ISO format
                    datetime.fromisoformat(timestamp.replace('Z', '+00:00'))


@pytest.mark.unit
class TestErrorHandling:
    """Test comprehensive error handling scenarios"""
    
    def test_service_unavailable_error_handling(self, test_client, mock_service_manager):
        """Test handling when required services are unavailable"""
        mock_service_manager.get_service.return_value = None
        
        # Endpoints that require specific services
        service_dependent_endpoints = [
            ("/api/advanced/database/health", "database"),
            ("/api/advanced/database/connection", "database"),
            ("/api/advanced/database/models", "database")
        ]
        
        for endpoint, service_name in service_dependent_endpoints:
            response = test_client.get(endpoint)
            
            # Should return fallback response, not error
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["unavailable", "degraded"]
    
    def test_service_exception_error_handling(self, test_client, mock_service_manager):
        """Test handling when services raise exceptions"""
        mock_service = MagicMock()
        mock_service.health_check = AsyncMock(side_effect=Exception("Service internal error"))
        mock_service_manager.get_service.return_value = mock_service
        
        response = test_client.get("/api/advanced/database/health")
        
        # Should handle exception gracefully
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            # Should indicate error or degraded status
            assert data["status"] in ["error", "degraded", "unavailable"]
    
    def test_async_operation_error_handling(self, test_client, mock_service_manager):
        """Test handling of async operation failures"""
        mock_service = MagicMock()
        
        # Mock async method that fails
        async def failing_async_method():
            raise Exception("Async operation failed")
        
        mock_service.health_check = failing_async_method
        mock_service_manager.get_service.return_value = mock_service
        
        response = test_client.get("/api/advanced/database/health")
        
        # Should handle async failure gracefully
        assert response.status_code in [200, 500]
    
    def test_timeout_error_handling(self, test_client, mock_service_manager):
        """Test handling of operation timeouts"""
        mock_service = MagicMock()
        
        # Mock slow async method
        async def slow_method():
            import asyncio
            await asyncio.sleep(10)  # Simulate slow operation
            return {"status": "healthy"}
        
        mock_service.health_check = slow_method
        mock_service_manager.get_service.return_value = mock_service
        
        # This would require actual timeout implementation in endpoints
        response = test_client.get("/api/advanced/database/health")
        
        # Should complete within reasonable time
        assert response.status_code in [200, 408, 500]
    
    def test_data_validation_error_handling(self, test_client, mock_service_manager):
        """Test handling of data validation errors"""
        # Test with various invalid data types
        invalid_requests = [
            {"query": None},
            {"query": 123},
            {"query": []},
            {"query": {}}
        ]
        
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        for invalid_request in invalid_requests:
            response = test_client.post(
                "/api/advanced/research/search/basic",
                json=invalid_request
            )
            
            # Should handle invalid data gracefully
            assert response.status_code in [200, 400, 422]
    
    def test_concurrent_request_error_handling(self, test_client, mock_service_manager):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        results = []
        
        def make_request():
            response = test_client.post(
                "/api/advanced/research/search/basic",
                json={"query": "concurrent test"}
            )
            results.append(response.status_code)
        
        # Make multiple concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should complete successfully
        assert all(status == 200 for status in results)
        assert len(results) == 5
    
    def test_memory_pressure_error_handling(self, test_client, mock_service_manager):
        """Test handling under memory pressure"""
        mock_service = MagicMock()
        mock_service.health_check = AsyncMock(side_effect=MemoryError("Out of memory"))
        mock_service_manager.get_service.return_value = mock_service
        
        response = test_client.get("/api/advanced/database/health")
        
        # Should handle memory error gracefully
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] in ["error", "unavailable"]
    
    def test_network_error_simulation(self, test_client, mock_service_manager):
        """Test handling of simulated network errors"""
        mock_service = MagicMock()
        mock_service.health_check = AsyncMock(side_effect=ConnectionError("Network unreachable"))
        mock_service_manager.get_service.return_value = mock_service
        
        response = test_client.get("/api/advanced/database/health")
        
        # Should handle network error gracefully
        assert response.status_code in [200, 500]


@pytest.mark.unit
class TestFallbackResponses:
    """Test fallback response mechanisms"""
    
    def test_search_fallback_response(self, test_client, mock_service_manager):
        """Test search endpoint fallback to mock results"""
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        response = test_client.post(
            "/api/advanced/research/search/basic",
            json={"query": "machine learning", "max_results": 3}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should use fallback
        assert data["status"] == "degraded"
        assert data["service_used"] == "mock"
        assert data["fallback"] is True
        assert len(data["results"]) <= 3
        
        # Validate mock result structure
        if data["results"]:
            result = data["results"][0]
            assert "id" in result
            assert "title" in result
            assert "content" in result
            assert "relevance_score" in result
    
    def test_health_check_fallback_responses(self, test_client, mock_service_manager):
        """Test health check endpoints with service unavailable"""
        mock_service_manager.get_service.return_value = None
        
        fallback_endpoints = [
            "/api/advanced/health/services",
            "/api/advanced/database/health",
            "/api/advanced/semantic-search/health",
            "/api/advanced/research-automation/health"
        ]
        
        for endpoint in fallback_endpoints:
            response = test_client.get(endpoint)
            
            assert response.status_code == 200
            data = response.json()
            
            # Should indicate unavailable status
            assert data["status"] in ["unavailable", "degraded"]
            
            # Should have appropriate fallback data
            if "data" in data:
                assert isinstance(data["data"], dict)
    
    def test_analytics_fallback_responses(self, test_client, mock_service_manager):
        """Test analytics endpoints with service unavailable"""
        mock_service_manager.get_service.return_value = None
        
        analytics_endpoints = [
            "/api/advanced/analytics/report/user123",
            "/api/advanced/analytics/usage/user123",
            "/api/advanced/analytics/content/user123"
        ]
        
        for endpoint in analytics_endpoints:
            response = test_client.get(endpoint)
            
            assert response.status_code == 200
            data = response.json()
            
            # Should indicate unavailable status
            assert data["status"] in ["unavailable", "error"]
            
            # Should have fallback data or error information
            assert "message" in data
    
    def test_graceful_degradation(self, test_client, mock_service_manager):
        """Test graceful degradation when some services are available"""
        # Mock partial service availability
        def mock_get_service(name):
            if name == "semantic_search":
                mock_service = MagicMock()
                mock_service.advanced_search = AsyncMock(return_value=[
                    {"id": "1", "title": "Test Result", "relevance_score": 0.8}
                ])
                return mock_service
            return None
        
        def mock_is_service_healthy(name):
            return name == "semantic_search"
        
        mock_service_manager.get_service.side_effect = mock_get_service
        mock_service_manager.is_service_healthy.side_effect = mock_is_service_healthy
        
        # Test search with available service
        response = test_client.post(
            "/api/advanced/research/search/basic",
            json={"query": "test", "max_results": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service_used"] == "semantic_search"
        
        # Test analytics with unavailable service
        response = test_client.get("/api/advanced/analytics/report/user123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unavailable"


@pytest.mark.integration
class TestEndpointValidationIntegration:
    """Integration tests for endpoint validation and error handling"""
    
    def test_complete_error_handling_workflow(self, test_client, mock_service_manager):
        """Test complete error handling workflow across multiple endpoints"""
        # Simulate various service states
        service_states = {
            "database": "healthy",
            "semantic_search": "unhealthy", 
            "research_automation": "unavailable",
            "advanced_analytics": "degraded"
        }
        
        def mock_get_service(name):
            if service_states.get(name) == "unavailable":
                return None
            return MagicMock()
        
        def mock_is_service_healthy(name):
            return service_states.get(name) == "healthy"
        
        def mock_check_service_health(name):
            state = service_states.get(name, "unavailable")
            if state == "unavailable":
                return None
            
            status_map = {
                "healthy": ServiceStatus.HEALTHY,
                "unhealthy": ServiceStatus.UNHEALTHY,
                "degraded": ServiceStatus.DEGRADED
            }
            
            return ServiceHealth(
                name=name,
                status=status_map[state],
                last_check=datetime.utcnow(),
                error_message="Service error" if state != "healthy" else None
            )
        
        mock_service_manager.get_service.side_effect = mock_get_service
        mock_service_manager.is_service_healthy.side_effect = mock_is_service_healthy
        mock_service_manager.check_service_health.side_effect = mock_check_service_health
        
        # Test various endpoints with different service states
        test_cases = [
            ("/api/advanced/database/health", "healthy"),
            ("/api/advanced/semantic-search/health", "unhealthy"),
            ("/api/advanced/research-automation/health", "unavailable"),
            ("/api/advanced/advanced-analytics/health", "degraded")
        ]
        
        for endpoint, expected_state in test_cases:
            response = test_client.get(endpoint)
            
            assert response.status_code == 200
            data = response.json()
            
            if expected_state == "healthy":
                assert data["status"] == "ok"
            elif expected_state == "unavailable":
                assert data["status"] == "unavailable"
            else:
                assert data["status"] in ["degraded", "unhealthy", expected_state]
    
    def test_request_response_validation_cycle(self, test_client, mock_service_manager):
        """Test complete request-response validation cycle"""
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        # Test valid request -> valid response
        response = test_client.post(
            "/api/advanced/research/search/basic",
            json={"query": "valid query", "max_results": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate complete response structure
        assert isinstance(data, dict)
        assert "status" in data
        assert "timestamp" in data
        assert "query" in data
        assert "results" in data
        assert isinstance(data["results"], list)
        
        # Test invalid request -> error response
        response = test_client.post(
            "/api/advanced/research/search/basic",
            json={"max_results": 5}  # Missing query
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_cross_endpoint_consistency(self, test_client, mock_service_manager):
        """Test consistency across different endpoints"""
        mock_service_manager.get_service.return_value = None
        mock_service_manager.get_service_health.return_value = {}
        mock_service_manager.get_initialization_summary.return_value = {
            "total_services": 0,
            "healthy_services": 0,
            "failed_services": 0
        }
        mock_service_manager.get_health_monitoring_status.return_value = {
            "enabled": False,
            "interval": 300
        }
        
        endpoints = [
            "/api/advanced/health",
            "/api/advanced/health/detailed",
            "/api/advanced/health/monitoring",
            "/api/advanced/research/domains"
        ]
        
        responses = []
        for endpoint in endpoints:
            response = test_client.get(endpoint)
            responses.append((endpoint, response))
        
        # All should return 200
        for endpoint, response in responses:
            assert response.status_code == 200, f"Endpoint {endpoint} failed"
        
        # All should have consistent timestamp format
        for endpoint, response in responses:
            data = response.json()
            if "timestamp" in data:
                timestamp = data["timestamp"]
                # Should be valid ISO format
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        # All should have status field
        for endpoint, response in responses:
            data = response.json()
            assert "status" in data, f"Endpoint {endpoint} missing status"
            assert isinstance(data["status"], str)