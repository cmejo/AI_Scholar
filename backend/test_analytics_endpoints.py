"""
Test suite for analytics endpoints
Tests analytics endpoint functionality with service dependency checks and error handling
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import the application and router
from app import app
from api.advanced_endpoints import router
from core.service_manager import ServiceManager

class TestAnalyticsEndpoints:
    """Test analytics endpoints with service dependency checks"""
    
    def setup_method(self):
        """Set up test client and mock services"""
        self.client = TestClient(app)
        self.base_url = "/api/advanced"
        self.test_user_id = "test-user-123"
    
    def test_analytics_report_endpoint_service_unavailable(self):
        """Test analytics report endpoint when service is unavailable"""
        with patch('core.service_manager.get_service', return_value=None):
            response = self.client.get(f"{self.base_url}/analytics/report/{self.test_user_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unavailable"
            assert data["user_id"] == self.test_user_id
            assert "fallback_data" in data
            assert "Advanced analytics service not initialized" in data["message"]
    
    def test_analytics_report_endpoint_invalid_timeframe(self):
        """Test analytics report endpoint with invalid timeframe"""
        mock_service = Mock()
        
        with patch('core.service_manager.get_service', return_value=mock_service):
            response = self.client.get(
                f"{self.base_url}/analytics/report/{self.test_user_id}?timeframe=invalid"
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "Invalid timeframe" in data["detail"]
    
    def test_analytics_report_endpoint_service_unhealthy(self):
        """Test analytics report endpoint when service is unhealthy"""
        mock_service = Mock()
        mock_health = Mock()
        mock_health.status.value = "unhealthy"
        mock_health.error_message = "Service connection failed"
        
        with patch('core.service_manager.get_service', return_value=mock_service), \
             patch('core.service_manager.check_service_health', return_value=mock_health):
            
            response = self.client.get(f"{self.base_url}/analytics/report/{self.test_user_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["error"] == "Service connection failed"
    
    @patch('core.service_manager.check_service_health')
    @patch('core.service_manager.get_service')
    def test_analytics_report_endpoint_success(self, mock_get_service, mock_check_health):
        """Test successful analytics report generation"""
        # Mock service and health check
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
        
        mock_get_service.return_value = mock_service
        mock_check_health.return_value = mock_health
        
        response = self.client.get(f"{self.base_url}/analytics/report/{self.test_user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["user_id"] == self.test_user_id
        assert "report" in data
        assert data["report"]["id"] == "report-123"
    
    def test_usage_insights_endpoint_service_unavailable(self):
        """Test usage insights endpoint when service is unavailable"""
        with patch('core.service_manager.get_service', return_value=None):
            response = self.client.get(f"{self.base_url}/analytics/usage/{self.test_user_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unavailable"
            assert data["user_id"] == self.test_user_id
            assert "fallback_data" in data
    
    @patch('core.service_manager.check_service_health')
    @patch('core.service_manager.get_service')
    def test_usage_insights_endpoint_success(self, mock_get_service, mock_check_health):
        """Test successful usage insights generation"""
        # Mock service and health check
        mock_service = Mock()
        mock_health = Mock()
        mock_health.status.value = "healthy"
        
        mock_insights = {
            "total_events": 150,
            "event_types": {"search": 50, "upload": 30, "view": 70},
            "daily_activity": {"2024-01-01": 10, "2024-01-02": 15},
            "trends": {"growth_rate": 0.15}
        }
        
        mock_service.generate_usage_insights = AsyncMock(return_value=mock_insights)
        
        mock_get_service.return_value = mock_service
        mock_check_health.return_value = mock_health
        
        response = self.client.get(f"{self.base_url}/analytics/usage/{self.test_user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["insights"]["total_events"] == 150
    
    def test_content_analytics_endpoint_invalid_timeframe(self):
        """Test content analytics endpoint with invalid timeframe"""
        mock_service = Mock()
        
        with patch('core.service_manager.get_service', return_value=mock_service):
            response = self.client.get(
                f"{self.base_url}/analytics/content/{self.test_user_id}?timeframe=invalid"
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "Invalid timeframe" in data["detail"]
    
    @patch('core.service_manager.check_service_health')
    @patch('core.service_manager.get_service')
    def test_content_analytics_endpoint_success(self, mock_get_service, mock_check_health):
        """Test successful content analytics generation"""
        # Mock service and health check
        mock_service = Mock()
        mock_health = Mock()
        mock_health.status.value = "healthy"
        
        mock_analytics = {
            "document_stats": {"total_documents": 25, "total_size_bytes": 1024000},
            "content_analysis": {"total_words": 50000, "vocabulary_size": 5000},
            "quality_metrics": {"processing_success_rate": 0.95}
        }
        
        mock_service.generate_content_analytics = AsyncMock(return_value=mock_analytics)
        
        mock_get_service.return_value = mock_service
        mock_check_health.return_value = mock_health
        
        response = self.client.get(f"{self.base_url}/analytics/content/{self.test_user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["analytics"]["document_stats"]["total_documents"] == 25
    
    def test_document_relationships_endpoint_invalid_similarity(self):
        """Test document relationships endpoint with invalid similarity threshold"""
        mock_service = Mock()
        
        with patch('core.service_manager.get_service', return_value=mock_service):
            response = self.client.get(
                f"{self.base_url}/analytics/relationships/{self.test_user_id}?min_similarity=1.5"
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "min_similarity must be between 0.0 and 1.0" in data["detail"]
    
    def test_document_relationships_endpoint_invalid_max_relationships(self):
        """Test document relationships endpoint with invalid max_relationships"""
        mock_service = Mock()
        
        with patch('core.service_manager.get_service', return_value=mock_service):
            response = self.client.get(
                f"{self.base_url}/analytics/relationships/{self.test_user_id}?max_relationships=2000"
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "max_relationships must be between 1 and 1000" in data["detail"]
    
    @patch('core.service_manager.check_service_health')
    @patch('core.service_manager.get_service')
    def test_document_relationships_endpoint_success(self, mock_get_service, mock_check_health):
        """Test successful document relationships analysis"""
        # Mock service and health check
        mock_service = Mock()
        mock_health = Mock()
        mock_health.status.value = "healthy"
        
        # Mock relationship data
        mock_relationship = Mock()
        mock_relationship.source_doc_id = "doc1"
        mock_relationship.target_doc_id = "doc2"
        mock_relationship.relationship_type = "similar"
        mock_relationship.strength = 0.75
        mock_relationship.shared_concepts = ["AI", "machine learning"]
        mock_relationship.similarity_score = 0.75
        
        mock_service.analyze_document_relationships = AsyncMock(return_value=[mock_relationship])
        
        mock_get_service.return_value = mock_service
        mock_check_health.return_value = mock_health
        
        response = self.client.get(f"{self.base_url}/analytics/relationships/{self.test_user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert len(data["relationships"]) == 1
        assert data["relationships"][0]["source_doc_id"] == "doc1"
    
    def test_knowledge_patterns_endpoint_invalid_frequency(self):
        """Test knowledge patterns endpoint with invalid frequency"""
        mock_service = Mock()
        
        with patch('core.service_manager.get_service', return_value=mock_service):
            response = self.client.get(
                f"{self.base_url}/analytics/knowledge-patterns/{self.test_user_id}?min_frequency=0"
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "min_frequency must be at least 1" in data["detail"]
    
    def test_knowledge_patterns_endpoint_invalid_confidence(self):
        """Test knowledge patterns endpoint with invalid confidence threshold"""
        mock_service = Mock()
        
        with patch('core.service_manager.get_service', return_value=mock_service):
            response = self.client.get(
                f"{self.base_url}/analytics/knowledge-patterns/{self.test_user_id}?confidence_threshold=1.5"
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "confidence_threshold must be between 0.0 and 1.0" in data["detail"]
    
    @patch('core.service_manager.check_service_health')
    @patch('core.service_manager.get_service')
    def test_knowledge_patterns_endpoint_success(self, mock_get_service, mock_check_health):
        """Test successful knowledge patterns discovery"""
        # Mock service and health check
        mock_service = Mock()
        mock_health = Mock()
        mock_health.status.value = "healthy"
        
        # Mock pattern data
        mock_pattern = Mock()
        mock_pattern.pattern_id = "pattern-1"
        mock_pattern.pattern_type = "cooccurrence"
        mock_pattern.entities = ["AI", "machine learning"]
        mock_pattern.relationships = ["related_to"]
        mock_pattern.frequency = 5
        mock_pattern.confidence = 0.8
        mock_pattern.examples = ["Example 1", "Example 2"]
        
        mock_service.discover_knowledge_patterns = AsyncMock(return_value=[mock_pattern])
        
        mock_get_service.return_value = mock_service
        mock_check_health.return_value = mock_health
        
        response = self.client.get(f"{self.base_url}/analytics/knowledge-patterns/{self.test_user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert len(data["patterns"]) == 1
        assert data["patterns"][0]["pattern_id"] == "pattern-1"
    
    def test_knowledge_map_endpoint_invalid_layout(self):
        """Test knowledge map endpoint with invalid layout algorithm"""
        mock_service = Mock()
        
        with patch('core.service_manager.get_service', return_value=mock_service):
            response = self.client.get(
                f"{self.base_url}/analytics/knowledge-map/{self.test_user_id}?layout_algorithm=invalid"
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "Invalid layout_algorithm" in data["detail"]
    
    def test_knowledge_map_endpoint_invalid_max_nodes(self):
        """Test knowledge map endpoint with invalid max_nodes"""
        mock_service = Mock()
        
        with patch('core.service_manager.get_service', return_value=mock_service):
            response = self.client.get(
                f"{self.base_url}/analytics/knowledge-map/{self.test_user_id}?max_nodes=5"
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "max_nodes must be between 10 and 500" in data["detail"]
    
    @patch('core.service_manager.check_service_health')
    @patch('core.service_manager.get_service')
    def test_knowledge_map_endpoint_success(self, mock_get_service, mock_check_health):
        """Test successful knowledge map visualization creation"""
        # Mock service and health check
        mock_service = Mock()
        mock_health = Mock()
        mock_health.status.value = "healthy"
        
        # Mock visualization data
        mock_visualization = Mock()
        mock_visualization.chart_type.value = "network_graph"
        mock_visualization.title = "Knowledge Map"
        mock_visualization.data = {"nodes": [], "edges": []}
        mock_visualization.config = {"layout": "spring"}
        mock_visualization.description = "Test visualization"
        mock_visualization.insights = ["Test insight"]
        
        mock_service.create_knowledge_map_visualization = AsyncMock(return_value=mock_visualization)
        
        mock_get_service.return_value = mock_service
        mock_check_health.return_value = mock_health
        
        response = self.client.get(f"{self.base_url}/analytics/knowledge-map/{self.test_user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["visualization"]["chart_type"] == "network_graph"
    
    def test_analytics_metrics_endpoint_invalid_timeframe(self):
        """Test analytics metrics endpoint with invalid timeframe"""
        mock_service = Mock()
        
        with patch('core.service_manager.get_service', return_value=mock_service):
            response = self.client.get(
                f"{self.base_url}/analytics/metrics/{self.test_user_id}?timeframe=invalid"
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "Invalid timeframe" in data["detail"]
    
    def test_analytics_metrics_endpoint_invalid_metric_types(self):
        """Test analytics metrics endpoint with invalid metric types"""
        mock_service = Mock()
        
        with patch('core.service_manager.get_service', return_value=mock_service):
            response = self.client.get(
                f"{self.base_url}/analytics/metrics/{self.test_user_id}?metric_types=invalid,unknown"
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "Invalid metric types" in data["detail"]
    
    @patch('core.service_manager.check_service_health')
    @patch('core.service_manager.get_service')
    def test_analytics_metrics_endpoint_success(self, mock_get_service, mock_check_health):
        """Test successful analytics metrics retrieval"""
        # Mock service and health check
        mock_service = Mock()
        mock_health = Mock()
        mock_health.status.value = "healthy"
        
        # Mock metric data
        mock_metric = Mock()
        mock_metric.name = "Total Events"
        mock_metric.value = 100
        mock_metric.metric_type.value = "usage"
        mock_metric.description = "Total user events"
        mock_metric.unit = "events"
        mock_metric.trend = 0.15
        mock_metric.benchmark = None
        mock_metric.timestamp = datetime.utcnow()
        
        mock_service._get_usage_metrics = AsyncMock(return_value=[mock_metric])
        mock_service._get_performance_metrics = AsyncMock(return_value=[])
        mock_service._get_content_metrics = AsyncMock(return_value=[])
        mock_service._get_user_behavior_metrics = AsyncMock(return_value=[])
        mock_service._get_knowledge_metrics = AsyncMock(return_value=[])
        
        mock_get_service.return_value = mock_service
        mock_check_health.return_value = mock_health
        
        response = self.client.get(
            f"{self.base_url}/analytics/metrics/{self.test_user_id}?metric_types=usage"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert len(data["metrics"]) == 1
        assert data["metrics"][0]["name"] == "Total Events"
    
    def test_all_analytics_endpoints_error_handling(self):
        """Test error handling for all analytics endpoints"""
        endpoints = [
            f"/analytics/report/{self.test_user_id}",
            f"/analytics/usage/{self.test_user_id}",
            f"/analytics/content/{self.test_user_id}",
            f"/analytics/relationships/{self.test_user_id}",
            f"/analytics/knowledge-patterns/{self.test_user_id}",
            f"/analytics/knowledge-map/{self.test_user_id}",
            f"/analytics/metrics/{self.test_user_id}"
        ]
        
        # Mock service that raises an exception
        mock_service = Mock()
        mock_health = Mock()
        mock_health.status.value = "healthy"
        
        with patch('core.service_manager.get_service', return_value=mock_service), \
             patch('core.service_manager.check_service_health', return_value=mock_health), \
             patch.object(mock_service, 'generate_comprehensive_report', side_effect=Exception("Test error")), \
             patch.object(mock_service, 'generate_usage_insights', side_effect=Exception("Test error")), \
             patch.object(mock_service, 'generate_content_analytics', side_effect=Exception("Test error")), \
             patch.object(mock_service, 'analyze_document_relationships', side_effect=Exception("Test error")), \
             patch.object(mock_service, 'discover_knowledge_patterns', side_effect=Exception("Test error")), \
             patch.object(mock_service, 'create_knowledge_map_visualization', side_effect=Exception("Test error")), \
             patch.object(mock_service, '_get_usage_metrics', side_effect=Exception("Test error")):
            
            for endpoint in endpoints:
                response = self.client.get(f"{self.base_url}{endpoint}")
                
                # All endpoints should return 200 with error status for graceful degradation
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "error"
                assert "Test error" in data["message"]
                assert "error_details" in data

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])