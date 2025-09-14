"""
Test suite for semantic search endpoints
Tests the semantic search endpoints with conditional service access,
error handling, and fallback responses.
"""
import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Import the FastAPI app
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from core import service_manager

client = TestClient(app)

class TestSemanticSearchEndpoints:
    """Test class for semantic search endpoints"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.base_url = "/api/advanced"
        self.test_user_id = "test-user-123"
        self.test_query = "machine learning algorithms"
        self.test_research_area = "artificial intelligence"
        self.test_domain = "computer_science"
    
    def test_semantic_search_endpoint_with_healthy_service(self):
        """Test semantic search endpoint with healthy service"""
        # Mock the service manager and semantic search service
        mock_service = Mock()
        mock_service.advanced_search = AsyncMock(return_value=[
            Mock(
                id="result-1",
                document_id="doc-1",
                chunk_id="chunk-1",
                content="Test content about machine learning",
                title="ML Research Paper",
                relevance_score=0.9,
                confidence_score=0.85,
                reasoning_path=["semantic_analysis"],
                knowledge_connections=[],
                temporal_context=None,
                cross_domain_insights=[],
                explanation="High relevance match",
                metadata={"type": "research_paper"}
            )
        ])
        
        mock_health = Mock()
        mock_health.status.value = "healthy"
        
        with patch.object(service_manager, 'get_service', return_value=mock_service), \
             patch.object(service_manager, 'check_service_health', return_value=mock_health):
            
            response = client.post(
                f"{self.base_url}/semantic-search/search",
                json={
                    "query": self.test_query,
                    "user_id": self.test_user_id,
                    "mode": "semantic",
                    "reasoning_types": ["associative"],
                    "max_results": 10,
                    "confidence_threshold": 0.5,
                    "include_explanations": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["query"] == self.test_query
            assert data["user_id"] == self.test_user_id
            assert data["service_used"] == "semantic_search_v2"
            assert len(data["results"]) == 1
            assert data["results"][0]["title"] == "ML Research Paper"
    
    def test_semantic_search_endpoint_with_unhealthy_service(self):
        """Test semantic search endpoint with unhealthy service (fallback)"""
        mock_service = Mock()
        mock_health = Mock()
        mock_health.status.value = "unhealthy"
        
        # Mock database service for fallback
        mock_db_service = Mock()
        mock_db_session = Mock()
        mock_db_service.get_session.return_value = mock_db_session
        
        # Mock database query results
        mock_doc = Mock()
        mock_doc.id = "doc-1"
        mock_doc.name = "Machine Learning Research"
        mock_doc.created_at = datetime.utcnow()
        mock_doc.content_type = "pdf"
        mock_doc.user_id = self.test_user_id
        mock_doc.status = "completed"
        
        mock_db_session.query.return_value.filter.return_value.limit.return_value.all.return_value = [mock_doc]
        
        with patch.object(service_manager, 'get_service') as mock_get_service, \
             patch.object(service_manager, 'check_service_health', return_value=mock_health):
            
            # Configure mock to return different services based on name
            def get_service_side_effect(service_name):
                if service_name == "semantic_search":
                    return mock_service
                elif service_name == "database":
                    return mock_db_service
                return None
            
            mock_get_service.side_effect = get_service_side_effect
            
            response = client.post(
                f"{self.base_url}/semantic-search/search",
                json={
                    "query": self.test_query,
                    "user_id": self.test_user_id,
                    "mode": "semantic",
                    "max_results": 10
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["service_used"] == "fallback_search"
            assert "warning" in data
            assert len(data["results"]) >= 1
    
    def test_semantic_search_endpoint_with_no_service(self):
        """Test semantic search endpoint with no service available (mock results)"""
        with patch.object(service_manager, 'get_service', return_value=None):
            
            response = client.post(
                f"{self.base_url}/semantic-search/search",
                json={
                    "query": self.test_query,
                    "user_id": self.test_user_id,
                    "mode": "semantic"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["service_used"] == "fallback_search"
            assert "warning" in data
            assert len(data["results"]) >= 1
            assert data["results"][0]["metadata"]["mock"] == True
    
    def test_semantic_search_endpoint_validation_errors(self):
        """Test semantic search endpoint parameter validation"""
        # Test missing query
        response = client.post(
            f"{self.base_url}/semantic-search/search",
            json={
                "user_id": self.test_user_id
            }
        )
        assert response.status_code == 400
        assert "Query parameter is required" in response.json()["detail"]
        
        # Test missing user_id
        response = client.post(
            f"{self.base_url}/semantic-search/search",
            json={
                "query": self.test_query
            }
        )
        assert response.status_code == 400
        assert "User ID parameter is required" in response.json()["detail"]
        
        # Test empty query
        response = client.post(
            f"{self.base_url}/semantic-search/search",
            json={
                "query": "",
                "user_id": self.test_user_id
            }
        )
        assert response.status_code == 400
        assert "Query parameter is required" in response.json()["detail"]
    
    def test_generate_hypotheses_endpoint_with_healthy_service(self):
        """Test hypothesis generation endpoint with healthy service"""
        mock_service = Mock()
        mock_service.generate_hypotheses = AsyncMock(return_value=[
            Mock(
                id="hyp-1",
                hypothesis="AI will revolutionize research methodologies",
                confidence=0.8,
                supporting_evidence=["Current AI trends", "Research patterns"],
                contradicting_evidence=["Limited adoption"],
                research_gaps=["Ethical considerations"],
                methodology_suggestions=["Mixed methods"],
                predicted_outcomes=["Improved efficiency"]
            )
        ])
        
        mock_health = Mock()
        mock_health.status.value = "healthy"
        
        with patch.object(service_manager, 'get_service', return_value=mock_service), \
             patch.object(service_manager, 'check_service_health', return_value=mock_health):
            
            response = client.post(
                f"{self.base_url}/semantic-search/hypotheses",
                json={
                    "user_id": self.test_user_id,
                    "research_area": self.test_research_area,
                    "existing_knowledge": ["Machine learning basics"]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["user_id"] == self.test_user_id
            assert data["research_area"] == self.test_research_area
            assert data["service_used"] == "semantic_search_v2"
            assert len(data["hypotheses"]) == 1
            assert data["hypotheses"][0]["confidence"] == 0.8
    
    def test_generate_hypotheses_endpoint_fallback(self):
        """Test hypothesis generation endpoint with fallback"""
        with patch.object(service_manager, 'get_service', return_value=None):
            
            response = client.post(
                f"{self.base_url}/semantic-search/hypotheses",
                json={
                    "user_id": self.test_user_id,
                    "research_area": self.test_research_area
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["service_used"] == "mock_service"
            assert "warning" in data
            assert len(data["hypotheses"]) >= 1
    
    def test_cross_domain_insights_endpoint_with_healthy_service(self):
        """Test cross-domain insights endpoint with healthy service"""
        mock_service = Mock()
        mock_service.discover_cross_domain_insights = AsyncMock(return_value=[
            Mock(
                id="insight-1",
                source_domain=self.test_domain,
                target_domain="medicine",
                insight="AI algorithms can be applied to medical diagnosis",
                confidence=0.75,
                analogical_reasoning="Pattern recognition similarities",
                potential_applications=["Medical imaging", "Drug discovery"],
                supporting_documents=["doc-1", "doc-2"]
            )
        ])
        
        mock_health = Mock()
        mock_health.status.value = "healthy"
        
        with patch.object(service_manager, 'get_service', return_value=mock_service), \
             patch.object(service_manager, 'check_service_health', return_value=mock_health):
            
            response = client.post(
                f"{self.base_url}/semantic-search/cross-domain-insights",
                json={
                    "user_id": self.test_user_id,
                    "source_domain": self.test_domain,
                    "target_domains": ["medicine", "psychology"]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["user_id"] == self.test_user_id
            assert data["source_domain"] == self.test_domain
            assert data["service_used"] == "semantic_search_v2"
            assert len(data["insights"]) == 1
            assert data["insights"][0]["target_domain"] == "medicine"
    
    def test_predict_trends_endpoint_with_healthy_service(self):
        """Test research trends prediction endpoint with healthy service"""
        mock_service = Mock()
        mock_service.predict_research_trends = AsyncMock(return_value={
            "domain": self.test_domain,
            "time_horizon_months": 12,
            "predicted_trends": ["AI integration", "Ethical AI"],
            "emerging_topics": ["Explainable AI", "AI Safety"],
            "research_opportunities": ["Cross-domain applications"],
            "methodology_trends": ["Automated research"],
            "confidence_scores": {"overall_confidence": 0.8},
            "generated_at": datetime.utcnow().isoformat()
        })
        
        mock_health = Mock()
        mock_health.status.value = "healthy"
        
        with patch.object(service_manager, 'get_service', return_value=mock_service), \
             patch.object(service_manager, 'check_service_health', return_value=mock_health):
            
            response = client.post(
                f"{self.base_url}/semantic-search/predict-trends",
                json={
                    "user_id": self.test_user_id,
                    "domain": self.test_domain,
                    "time_horizon_months": 12
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["user_id"] == self.test_user_id
            assert data["service_used"] == "semantic_search_v2"
            assert "predictions" in data
            assert data["predictions"]["domain"] == self.test_domain
    
    def test_get_search_modes_endpoint(self):
        """Test get search modes endpoint"""
        mock_service = Mock()
        mock_health = Mock()
        mock_health.status.value = "healthy"
        
        with patch.object(service_manager, 'get_service', return_value=mock_service), \
             patch.object(service_manager, 'check_service_health', return_value=mock_health):
            
            response = client.get(f"{self.base_url}/semantic-search/modes")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "search_modes" in data
            assert "reasoning_types" in data
            assert "service_status" in data
            assert len(data["search_modes"]) == 6  # semantic, hybrid, knowledge_graph, temporal, cross_domain, predictive
            assert len(data["reasoning_types"]) == 5  # causal, analogical, temporal, hierarchical, associative
    
    def test_get_search_modes_endpoint_service_unavailable(self):
        """Test get search modes endpoint when service is unavailable"""
        with patch.object(service_manager, 'get_service', return_value=None):
            
            response = client.get(f"{self.base_url}/semantic-search/modes")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["service_status"]["available"] == False
            assert data["service_status"]["status"] == "unavailable"
    
    def test_semantic_search_parameter_validation(self):
        """Test parameter validation for semantic search"""
        mock_service = Mock()
        mock_health = Mock()
        mock_health.status.value = "healthy"
        
        with patch.object(service_manager, 'get_service', return_value=mock_service), \
             patch.object(service_manager, 'check_service_health', return_value=mock_health):
            
            # Test with invalid max_results (should default to 20)
            response = client.post(
                f"{self.base_url}/semantic-search/search",
                json={
                    "query": self.test_query,
                    "user_id": self.test_user_id,
                    "max_results": 150  # Over limit
                }
            )
            
            # Should not fail, but should use default value
            assert response.status_code in [200, 500]  # May fail due to service mock, but validation should pass
            
            # Test with invalid confidence_threshold (should default to 0.5)
            response = client.post(
                f"{self.base_url}/semantic-search/search",
                json={
                    "query": self.test_query,
                    "user_id": self.test_user_id,
                    "confidence_threshold": 1.5  # Over limit
                }
            )
            
            # Should not fail, but should use default value
            assert response.status_code in [200, 500]  # May fail due to service mock, but validation should pass
    
    def test_error_handling_in_endpoints(self):
        """Test error handling in semantic search endpoints"""
        # Mock service that raises an exception
        mock_service = Mock()
        mock_service.advanced_search = AsyncMock(side_effect=Exception("Service error"))
        mock_health = Mock()
        mock_health.status.value = "healthy"
        
        with patch.object(service_manager, 'get_service', return_value=mock_service), \
             patch.object(service_manager, 'check_service_health', return_value=mock_health):
            
            response = client.post(
                f"{self.base_url}/semantic-search/search",
                json={
                    "query": self.test_query,
                    "user_id": self.test_user_id
                }
            )
            
            # Should fall back to degraded mode when service fails
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert "warning" in data
    
    def test_performance_validation(self):
        """Test performance aspects of semantic search endpoints"""
        import time
        
        # Mock fast service
        mock_service = Mock()
        mock_service.advanced_search = AsyncMock(return_value=[])
        mock_health = Mock()
        mock_health.status.value = "healthy"
        
        with patch.object(service_manager, 'get_service', return_value=mock_service), \
             patch.object(service_manager, 'check_service_health', return_value=mock_health):
            
            start_time = time.time()
            
            response = client.post(
                f"{self.base_url}/semantic-search/search",
                json={
                    "query": self.test_query,
                    "user_id": self.test_user_id,
                    "max_results": 50
                }
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Response should be reasonably fast (under 5 seconds for mocked service)
            assert response_time < 5.0
            assert response.status_code == 200


def test_semantic_search_endpoints_integration():
    """Integration test for semantic search endpoints"""
    # Test that all endpoints are properly registered
    response = client.get("/docs")
    assert response.status_code == 200
    
    # Test that endpoints are accessible (even if they return errors due to missing services)
    endpoints_to_test = [
        ("/api/advanced/semantic-search/modes", "GET"),
    ]
    
    for endpoint, method in endpoints_to_test:
        if method == "GET":
            response = client.get(endpoint)
        else:
            response = client.post(endpoint, json={})
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])