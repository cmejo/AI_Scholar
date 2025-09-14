"""
Comprehensive tests for advanced API endpoints
Tests endpoint functionality, error handling, and service integration
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

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
class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_basic_health_check(self, test_client):
        """Test basic health check endpoint"""
        response = test_client.get("/api/advanced/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data
    
    def test_detailed_health_check_success(self, test_client, mock_service_manager):
        """Test detailed health check with healthy services"""
        # Mock service manager responses
        mock_service_manager.get_service_health.return_value = {
            "database": {
                "status": "healthy",
                "last_check": datetime.utcnow().isoformat(),
                "dependencies": []
            },
            "semantic_search": {
                "status": "healthy", 
                "last_check": datetime.utcnow().isoformat(),
                "dependencies": ["database"]
            }
        }
        
        mock_service_manager.get_initialization_summary.return_value = {
            "total_services": 2,
            "healthy_services": 2,
            "failed_services": 0,
            "initialization_time": 5.2
        }
        
        response = test_client.get("/api/advanced/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "services" in data
        assert "summary" in data
        assert "timestamp" in data
    
    def test_detailed_health_check_degraded(self, test_client, mock_service_manager):
        """Test detailed health check with some failed services"""
        mock_service_manager.get_service_health.return_value = {
            "database": {
                "status": "healthy",
                "last_check": datetime.utcnow().isoformat(),
                "dependencies": []
            },
            "semantic_search": {
                "status": "unhealthy",
                "last_check": datetime.utcnow().isoformat(),
                "error_message": "Service initialization failed",
                "dependencies": ["database"]
            }
        }
        
        mock_service_manager.get_initialization_summary.return_value = {
            "total_services": 2,
            "healthy_services": 1,
            "failed_services": 1,
            "initialization_time": 3.1
        }
        
        response = test_client.get("/api/advanced/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["semantic_search"]["status"] == "unhealthy"
    
    def test_services_health_check_success(self, test_client, mock_service_manager):
        """Test services health check endpoint"""
        # Mock health check results
        mock_health_results = {
            "database": ServiceHealth(
                name="database",
                status=ServiceStatus.HEALTHY,
                last_check=datetime.utcnow(),
                dependencies=[],
                initialization_time=2.1
            ),
            "semantic_search": ServiceHealth(
                name="semantic_search", 
                status=ServiceStatus.HEALTHY,
                last_check=datetime.utcnow(),
                dependencies=["database"],
                initialization_time=3.5
            )
        }
        
        mock_service_manager.check_all_services_health.return_value = mock_health_results
        
        response = test_client.get("/api/advanced/health/services")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "services" in data
        assert len(data["services"]) == 2
        assert "database" in data["services"]
        assert "semantic_search" in data["services"]
    
    def test_service_health_check_individual(self, test_client, mock_service_manager):
        """Test individual service health check"""
        mock_health = ServiceHealth(
            name="database",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow(),
            dependencies=[],
            initialization_time=2.1
        )
        
        mock_service_manager.check_service_health.return_value = mock_health
        
        response = test_client.get("/api/advanced/health/service/database")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"]["name"] == "database"
        assert data["service"]["status"] == "healthy"
    
    def test_health_monitoring_status(self, test_client, mock_service_manager):
        """Test health monitoring status endpoint"""
        mock_service_manager.get_health_monitoring_status.return_value = {
            "enabled": True,
            "interval": 300,
            "cache_ttl": 60,
            "active": True,
            "last_check": datetime.utcnow().isoformat()
        }
        
        response = test_client.get("/api/advanced/health/monitoring")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["monitoring"]["enabled"] is True
        assert data["monitoring"]["interval"] == 300
    
    def test_configure_health_monitoring(self, test_client, mock_service_manager):
        """Test health monitoring configuration endpoint"""
        mock_service_manager.configure_health_monitoring = MagicMock()
        mock_service_manager.start_health_monitoring = AsyncMock()
        mock_service_manager.get_health_monitoring_status.return_value = {
            "enabled": True,
            "interval": 180,
            "cache_ttl": 30
        }
        
        response = test_client.post(
            "/api/advanced/health/monitoring/configure",
            params={"interval": 180, "cache_ttl": 30, "enabled": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "configuration" in data
        
        # Verify service manager was called
        mock_service_manager.configure_health_monitoring.assert_called_once()


@pytest.mark.unit
class TestDatabaseEndpoints:
    """Test database-related endpoints"""
    
    def test_database_health_check_success(self, test_client, mock_service_manager):
        """Test database health check with healthy service"""
        mock_db_service = MagicMock()
        mock_db_service.health_check = AsyncMock(return_value={
            "status": "healthy",
            "connection": "active",
            "tables": {"users": "ok", "documents": "ok"}
        })
        
        mock_service_manager.get_service.return_value = mock_db_service
        
        response = test_client.get("/api/advanced/database/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "database" in data
        assert data["database"]["status"] == "healthy"
    
    def test_database_health_check_service_unavailable(self, test_client, mock_service_manager):
        """Test database health check when service is unavailable"""
        mock_service_manager.get_service.return_value = None
        
        response = test_client.get("/api/advanced/database/health")
        
        # Should return fallback response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unavailable"
        assert "service_registered" in data["data"]
        assert data["data"]["service_registered"] is False
    
    def test_database_connection_test_success(self, test_client, mock_service_manager):
        """Test database connection test with healthy connection"""
        mock_db_service = MagicMock()
        mock_db_service.is_healthy.return_value = True
        mock_db_service.get_status.return_value = {"connection": "active", "pool_size": 10}
        
        mock_service_manager.get_service.return_value = mock_db_service
        
        response = test_client.get("/api/advanced/database/connection")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "connected"
        assert "service_status" in data
    
    def test_database_connection_test_failed(self, test_client, mock_service_manager):
        """Test database connection test with failed connection"""
        mock_db_service = MagicMock()
        mock_db_service.is_healthy.return_value = False
        mock_db_service.get_status.return_value = {"connection": "failed", "error": "Connection timeout"}
        
        mock_service_manager.get_service.return_value = mock_db_service
        
        response = test_client.get("/api/advanced/database/connection")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "disconnected"
        assert "service_status" in data
    
    def test_database_models_info(self, test_client, mock_service_manager):
        """Test database models information endpoint"""
        mock_db_service = MagicMock()
        mock_db_service.get_available_models.return_value = [
            {"name": "User", "table": "users", "status": "active"},
            {"name": "Document", "table": "documents", "status": "active"},
            {"name": "Citation", "table": "citations", "status": "active"}
        ]
        mock_db_service.get_status.return_value = {"connection": "active"}
        
        mock_service_manager.get_service.return_value = mock_db_service
        
        response = test_client.get("/api/advanced/database/models")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["model_count"] == 3
        assert len(data["models"]) == 3
    
    def test_database_migration_check(self, test_client, mock_service_manager):
        """Test database migration check endpoint"""
        mock_db_service = MagicMock()
        mock_db_service.health_check = AsyncMock(return_value={
            "status": "healthy",
            "details": {
                "tables": {
                    "users": {"exists": True, "columns": 5},
                    "documents": {"exists": True, "columns": 8},
                    "citations": {"exists": True, "columns": 6}
                },
                "connection": "active"
            }
        })
        
        mock_service_manager.get_service.return_value = mock_db_service
        
        response = test_client.get("/api/advanced/database/migration/check")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "tables" in data
        assert "connection" in data


@pytest.mark.unit
class TestServiceHealthEndpoints:
    """Test individual service health endpoints"""
    
    def test_semantic_search_health_success(self, test_client, mock_service_manager):
        """Test semantic search health check with healthy service"""
        mock_service = MagicMock()
        mock_health = ServiceHealth(
            name="semantic_search",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow(),
            dependencies=["database"],
            initialization_time=3.2
        )
        
        mock_service_manager.get_service.return_value = mock_service
        mock_service_manager.check_service_health.return_value = mock_health
        
        response = test_client.get("/api/advanced/semantic-search/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"]["name"] == "semantic_search"
        assert data["service"]["status"] == "healthy"
    
    def test_semantic_search_health_unavailable(self, test_client, mock_service_manager):
        """Test semantic search health check when service is unavailable"""
        mock_service_manager.get_service.return_value = None
        
        response = test_client.get("/api/advanced/semantic-search/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unavailable"
        assert data["details"]["service_registered"] is False
    
    def test_research_automation_health_success(self, test_client, mock_service_manager):
        """Test research automation health check with healthy service"""
        mock_service = MagicMock()
        mock_service.get_status.return_value = {
            "active_workflows": 5,
            "scheduler_running": True,
            "last_execution": datetime.utcnow().isoformat()
        }
        
        mock_health = ServiceHealth(
            name="research_automation",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow(),
            dependencies=["database"],
            initialization_time=2.8
        )
        
        mock_service_manager.get_service.return_value = mock_service
        mock_service_manager.check_service_health.return_value = mock_health
        
        response = test_client.get("/api/advanced/research-automation/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"]["name"] == "research_automation"
        assert data["service"]["service_details"]["active_workflows"] == 5
    
    def test_advanced_analytics_health_success(self, test_client, mock_service_manager):
        """Test advanced analytics health check with healthy service"""
        mock_service = MagicMock()
        mock_service.get_status.return_value = {
            "reports_generated": 150,
            "cache_hit_rate": 0.85,
            "last_report": datetime.utcnow().isoformat()
        }
        
        mock_health = ServiceHealth(
            name="advanced_analytics",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow(),
            dependencies=["database"],
            initialization_time=4.1
        )
        
        mock_service_manager.get_service.return_value = mock_service
        mock_service_manager.check_service_health.return_value = mock_health
        
        response = test_client.get("/api/advanced/advanced-analytics/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"]["service_details"]["reports_generated"] == 150
    
    def test_knowledge_graph_health_success(self, test_client, mock_service_manager):
        """Test knowledge graph health check with healthy service"""
        mock_service = MagicMock()
        mock_service.get_status.return_value = {
            "entities_count": 1250,
            "relationships_count": 3400,
            "last_update": datetime.utcnow().isoformat()
        }
        
        mock_health = ServiceHealth(
            name="knowledge_graph",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow(),
            dependencies=["database"],
            initialization_time=5.7
        )
        
        mock_service_manager.get_service.return_value = mock_service
        mock_service_manager.check_service_health.return_value = mock_health
        
        response = test_client.get("/api/advanced/knowledge-graph/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"]["service_details"]["entities_count"] == 1250


@pytest.mark.unit
class TestResearchEndpoints:
    """Test research-related endpoints"""
    
    def test_research_status_all_healthy(self, test_client, mock_service_manager):
        """Test research status with all services healthy"""
        # Mock healthy services
        services = ["semantic_search", "research_automation", "advanced_analytics", "knowledge_graph"]
        
        def mock_get_service(name):
            return MagicMock() if name in services else None
        
        def mock_check_service_health(name):
            return ServiceHealth(
                name=name,
                status=ServiceStatus.HEALTHY,
                last_check=datetime.utcnow()
            )
        
        mock_service_manager.get_service.side_effect = mock_get_service
        mock_service_manager.check_service_health.side_effect = mock_check_service_health
        
        response = test_client.get("/api/advanced/research/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert len(data["services"]) == 4
        
        for service_name in services:
            assert data["services"][service_name]["status"] == "healthy"
            assert data["services"][service_name]["available"] is True
    
    def test_research_status_some_unavailable(self, test_client, mock_service_manager):
        """Test research status with some services unavailable"""
        available_services = ["semantic_search", "research_automation"]
        unavailable_services = ["advanced_analytics", "knowledge_graph"]
        
        def mock_get_service(name):
            return MagicMock() if name in available_services else None
        
        def mock_check_service_health(name):
            if name in available_services:
                return ServiceHealth(
                    name=name,
                    status=ServiceStatus.HEALTHY,
                    last_check=datetime.utcnow()
                )
            return None
        
        mock_service_manager.get_service.side_effect = mock_get_service
        mock_service_manager.check_service_health.side_effect = mock_check_service_health
        
        response = test_client.get("/api/advanced/research/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        
        for service_name in available_services:
            assert data["services"][service_name]["available"] is True
        
        for service_name in unavailable_services:
            assert data["services"][service_name]["available"] is False
    
    def test_research_capabilities(self, test_client, mock_service_manager):
        """Test research capabilities endpoint"""
        services = ["semantic_search", "research_automation", "advanced_analytics", "knowledge_graph"]
        
        def mock_get_service(name):
            return MagicMock() if name in services else None
        
        def mock_check_service_health(name):
            return ServiceHealth(
                name=name,
                status=ServiceStatus.HEALTHY,
                last_check=datetime.utcnow()
            )
        
        mock_service_manager.get_service.side_effect = mock_get_service
        mock_service_manager.check_service_health.side_effect = mock_check_service_health
        
        response = test_client.get("/api/advanced/research/capabilities")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "capabilities" in data
        
        for service_name in services:
            capability = data["capabilities"][service_name]
            assert capability["available"] is True
            assert capability["status"] == "healthy"
            assert "features" in capability
            assert len(capability["features"]) > 0
    
    def test_basic_research_search_with_service(self, test_client, mock_service_manager):
        """Test basic research search with available semantic search service"""
        mock_service = MagicMock()
        mock_service.advanced_search = AsyncMock(return_value=[
            {
                "id": "result-1",
                "title": "AI Research Paper",
                "content": "Advanced AI research content",
                "relevance_score": 0.95,
                "source": "academic_db"
            },
            {
                "id": "result-2", 
                "title": "Machine Learning Study",
                "content": "ML research findings",
                "relevance_score": 0.87,
                "source": "academic_db"
            }
        ])
        
        mock_service_manager.get_service.return_value = mock_service
        mock_service_manager.is_service_healthy.return_value = True
        
        response = test_client.post(
            "/api/advanced/research/search/basic",
            json={"query": "artificial intelligence", "max_results": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service_used"] == "semantic_search"
        assert len(data["results"]) == 2
        assert data["results"][0]["title"] == "AI Research Paper"
    
    def test_basic_research_search_fallback(self, test_client, mock_service_manager):
        """Test basic research search with fallback to mock results"""
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        response = test_client.post(
            "/api/advanced/research/search/basic",
            json={"query": "machine learning", "max_results": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["service_used"] == "mock"
        assert data["fallback"] is True
        assert len(data["results"]) <= 5
    
    def test_basic_research_search_validation_error(self, test_client, mock_service_manager):
        """Test basic research search with invalid request data"""
        response = test_client.post(
            "/api/advanced/research/search/basic",
            json={"max_results": 10}  # Missing required "query" field
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "query" in data["detail"].lower()
    
    def test_research_domains(self, test_client):
        """Test research domains endpoint"""
        response = test_client.get("/api/advanced/research/domains")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "domains" in data
        assert data["total_domains"] > 0
        
        # Check that expected domains are present
        expected_domains = ["computer_science", "engineering", "medicine", "natural_sciences"]
        for domain in expected_domains:
            assert domain in data["domains"]
            assert "name" in data["domains"][domain]
            assert "description" in data["domains"][domain]
            assert "subdomains" in data["domains"][domain]
    
    def test_validate_research_query_valid(self, test_client):
        """Test research query validation with valid query"""
        response = test_client.post(
            "/api/advanced/research/validate",
            json={
                "query": "What are the latest developments in machine learning?",
                "domain": "computer_science"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["validation"]["is_valid"] is True
        assert data["validation"]["query_type"] == "question"
        assert len(data["validation"]["suggestions"]) > 0
    
    def test_validate_research_query_invalid(self, test_client):
        """Test research query validation with invalid query"""
        response = test_client.post(
            "/api/advanced/research/validate",
            json={"query": "AI"}  # Too short
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["validation"]["is_valid"] is False
        assert "Query too short" in data["validation"]["issues"]
    
    def test_validate_research_query_missing_query(self, test_client):
        """Test research query validation with missing query"""
        response = test_client.post(
            "/api/advanced/research/validate",
            json={"domain": "computer_science"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "query" in data["detail"].lower()


@pytest.mark.unit
class TestAnalyticsEndpoints:
    """Test analytics-related endpoints"""
    
    def test_generate_analytics_report_success(self, test_client, mock_service_manager):
        """Test analytics report generation with available service"""
        mock_service = MagicMock()
        
        # Mock report object
        mock_report = MagicMock()
        mock_report.id = "report-123"
        mock_report.title = "User Analytics Report"
        mock_report.summary = "Comprehensive analytics summary"
        mock_report.metrics = []
        mock_report.visualizations = []
        mock_report.recommendations = ["Increase engagement", "Optimize workflow"]
        mock_report.timeframe.value = "month"
        mock_report.generated_at = datetime.utcnow()
        mock_report.confidence_score = 0.92
        
        mock_service.generate_comprehensive_report = AsyncMock(return_value=mock_report)
        mock_service_manager.get_service.return_value = mock_service
        
        response = test_client.get("/api/advanced/analytics/report/user123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["user_id"] == "user123"
        assert data["report"]["id"] == "report-123"
        assert data["report"]["confidence_score"] == 0.92
    
    def test_generate_analytics_report_service_unavailable(self, test_client, mock_service_manager):
        """Test analytics report generation when service is unavailable"""
        mock_service_manager.get_service.return_value = None
        
        response = test_client.get("/api/advanced/analytics/report/user123")
        
        # Should return fallback response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unavailable"
        assert "basic_metrics" in data["data"]
    
    def test_generate_analytics_report_invalid_timeframe(self, test_client, mock_service_manager):
        """Test analytics report generation with invalid timeframe"""
        mock_service_manager.get_service.return_value = MagicMock()
        
        response = test_client.get(
            "/api/advanced/analytics/report/user123",
            params={"timeframe": "invalid_timeframe"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "timeframe" in data["detail"].lower()
    
    def test_get_usage_insights_success(self, test_client, mock_service_manager):
        """Test usage insights endpoint with available service"""
        mock_service = MagicMock()
        mock_insights = {
            "daily_usage": 4.2,
            "peak_hours": [9, 14, 20],
            "feature_usage": {
                "search": 45,
                "analytics": 12,
                "export": 8
            },
            "trends": {
                "usage_trend": "increasing",
                "engagement_score": 0.78
            }
        }
        
        mock_service.generate_usage_insights = AsyncMock(return_value=mock_insights)
        
        mock_health = ServiceHealth(
            name="advanced_analytics",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow()
        )
        
        mock_service_manager.get_service.return_value = mock_service
        mock_service_manager.check_service_health.return_value = mock_health
        
        response = test_client.get("/api/advanced/analytics/usage/user123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["user_id"] == "user123"
        assert data["insights"]["daily_usage"] == 4.2
    
    def test_get_usage_insights_service_degraded(self, test_client, mock_service_manager):
        """Test usage insights when service is degraded"""
        mock_service = MagicMock()
        mock_health = ServiceHealth(
            name="advanced_analytics",
            status=ServiceStatus.DEGRADED,
            last_check=datetime.utcnow(),
            error_message="Service running with limited functionality"
        )
        
        mock_service_manager.get_service.return_value = mock_service
        mock_service_manager.check_service_health.return_value = mock_health
        
        response = test_client.get("/api/advanced/analytics/usage/user123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["error"] == "Service running with limited functionality"
    
    def test_get_content_analytics_success(self, test_client, mock_service_manager):
        """Test content analytics endpoint"""
        mock_service = MagicMock()
        mock_analytics = {
            "total_documents": 156,
            "document_types": {
                "research_papers": 89,
                "reports": 34,
                "notes": 33
            },
            "topic_distribution": {
                "AI": 0.35,
                "ML": 0.28,
                "Data Science": 0.22,
                "Other": 0.15
            },
            "quality_metrics": {
                "avg_length": 2450,
                "readability_score": 0.72,
                "citation_density": 0.15
            }
        }
        
        mock_service.generate_content_analytics = AsyncMock(return_value=mock_analytics)
        
        mock_health = ServiceHealth(
            name="advanced_analytics",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow()
        )
        
        mock_service_manager.get_service.return_value = mock_service
        mock_service_manager.check_service_health.return_value = mock_health
        
        response = test_client.get("/api/advanced/analytics/content/user123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["analytics"]["total_documents"] == 156
        assert "topic_distribution" in data["analytics"]
    
    def test_analyze_document_relationships_success(self, test_client, mock_service_manager):
        """Test document relationships analysis endpoint"""
        mock_service = MagicMock()
        
        # Mock relationship objects
        mock_relationships = [
            MagicMock(
                source_doc_id="doc1",
                target_doc_id="doc2",
                relationship_type="similar_topic",
                strength=0.85,
                shared_concepts=["AI", "machine learning"],
                similarity_score=0.78
            ),
            MagicMock(
                source_doc_id="doc2",
                target_doc_id="doc3",
                relationship_type="citation",
                strength=0.92,
                shared_concepts=["neural networks"],
                similarity_score=0.65
            )
        ]
        
        mock_service.analyze_document_relationships = AsyncMock(return_value=mock_relationships)
        
        mock_health = ServiceHealth(
            name="advanced_analytics",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow()
        )
        
        mock_service_manager.get_service.return_value = mock_service
        mock_service_manager.check_service_health.return_value = mock_health
        
        response = test_client.get(
            "/api/advanced/analytics/relationships/user123",
            params={"min_similarity": 0.5, "max_relationships": 50}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["total_relationships"] == 2
        assert len(data["relationships"]) == 2
        assert data["relationships"][0]["source_doc_id"] == "doc1"
    
    def test_analyze_document_relationships_invalid_params(self, test_client, mock_service_manager):
        """Test document relationships analysis with invalid parameters"""
        mock_service_manager.get_service.return_value = MagicMock()
        
        # Test invalid min_similarity
        response = test_client.get(
            "/api/advanced/analytics/relationships/user123",
            params={"min_similarity": 1.5}  # > 1.0
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "min_similarity" in data["detail"]
        
        # Test invalid max_relationships
        response = test_client.get(
            "/api/advanced/analytics/relationships/user123",
            params={"max_relationships": 2000}  # > 1000
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "max_relationships" in data["detail"]


@pytest.mark.unit
class TestEndpointErrorHandling:
    """Test endpoint error handling and fallback responses"""
    
    def test_endpoint_with_service_exception(self, test_client, mock_service_manager):
        """Test endpoint behavior when service raises exception"""
        mock_service = MagicMock()
        mock_service.health_check = AsyncMock(side_effect=Exception("Service internal error"))
        
        mock_service_manager.get_service.return_value = mock_service
        
        response = test_client.get("/api/advanced/database/health")
        
        # Should handle exception gracefully
        assert response.status_code in [200, 500]  # Depends on error handling implementation
    
    def test_endpoint_with_timeout(self, test_client, mock_service_manager):
        """Test endpoint behavior with service timeout"""
        mock_service = MagicMock()
        
        async def slow_health_check():
            await asyncio.sleep(10)  # Simulate timeout
            return {"status": "healthy"}
        
        mock_service.health_check = slow_health_check
        mock_service_manager.get_service.return_value = mock_service
        
        # This test would need actual timeout handling in the endpoint
        response = test_client.get("/api/advanced/database/health")
        
        # Should complete within reasonable time
        assert response.status_code in [200, 408, 500]
    
    def test_endpoint_with_malformed_service_response(self, test_client, mock_service_manager):
        """Test endpoint behavior with malformed service response"""
        mock_service = MagicMock()
        mock_service.health_check = AsyncMock(return_value="invalid_response")  # Should be dict
        
        mock_service_manager.get_service.return_value = mock_service
        
        response = test_client.get("/api/advanced/database/health")
        
        # Should handle malformed response gracefully
        assert response.status_code in [200, 500]
    
    def test_endpoint_fallback_responses(self, test_client, mock_service_manager):
        """Test that endpoints return appropriate fallback responses"""
        mock_service_manager.get_service.return_value = None
        
        # Test various endpoints that should have fallback responses
        endpoints_with_fallbacks = [
            "/api/advanced/health/services",
            "/api/advanced/database/health",
            "/api/advanced/semantic-search/health",
            "/api/advanced/research/status"
        ]
        
        for endpoint in endpoints_with_fallbacks:
            response = test_client.get(endpoint)
            
            # Should return 200 with fallback data
            assert response.status_code == 200
            data = response.json()
            
            # Should indicate unavailable status
            assert data.get("status") in ["unavailable", "degraded"]


@pytest.mark.integration
class TestEndpointIntegration:
    """Integration tests for endpoint interactions"""
    
    def test_health_check_workflow(self, test_client, mock_service_manager):
        """Test complete health check workflow"""
        # Setup mock services
        services = {
            "database": MagicMock(),
            "semantic_search": MagicMock(),
            "research_automation": MagicMock()
        }
        
        for name, service in services.items():
            service.health_check = AsyncMock(return_value={"status": "healthy"})
            service.get_status = MagicMock(return_value={"status": "active"})
        
        def mock_get_service(name):
            return services.get(name)
        
        def mock_check_service_health(name):
            if name in services:
                return ServiceHealth(
                    name=name,
                    status=ServiceStatus.HEALTHY,
                    last_check=datetime.utcnow(),
                    dependencies=[]
                )
            return None
        
        mock_service_manager.get_service.side_effect = mock_get_service
        mock_service_manager.check_service_health.side_effect = mock_check_service_health
        mock_service_manager.check_all_services_health.return_value = {
            name: ServiceHealth(name=name, status=ServiceStatus.HEALTHY, last_check=datetime.utcnow())
            for name in services.keys()
        }
        
        # Test basic health check
        response = test_client.get("/api/advanced/health")
        assert response.status_code == 200
        
        # Test detailed health check
        mock_service_manager.get_service_health.return_value = {
            name: {"status": "healthy", "last_check": datetime.utcnow().isoformat(), "dependencies": []}
            for name in services.keys()
        }
        mock_service_manager.get_initialization_summary.return_value = {
            "total_services": len(services),
            "healthy_services": len(services),
            "failed_services": 0
        }
        
        response = test_client.get("/api/advanced/health/detailed")
        assert response.status_code == 200
        
        # Test individual service health checks
        for service_name in services.keys():
            response = test_client.get(f"/api/advanced/health/service/{service_name}")
            assert response.status_code == 200
    
    def test_research_workflow_integration(self, test_client, mock_service_manager):
        """Test complete research workflow integration"""
        # Setup semantic search service
        mock_search_service = MagicMock()
        mock_search_service.advanced_search = AsyncMock(return_value=[
            {"id": "1", "title": "AI Paper", "relevance_score": 0.9}
        ])
        
        def mock_get_service(name):
            if name == "semantic_search":
                return mock_search_service
            return None
        
        def mock_is_service_healthy(name):
            return name == "semantic_search"
        
        def mock_check_service_health(name):
            if name == "semantic_search":
                return ServiceHealth(
                    name=name,
                    status=ServiceStatus.HEALTHY,
                    last_check=datetime.utcnow()
                )
            return ServiceHealth(
                name=name,
                status=ServiceStatus.UNHEALTHY,
                last_check=datetime.utcnow(),
                error_message="Service not available"
            )
        
        mock_service_manager.get_service.side_effect = mock_get_service
        mock_service_manager.is_service_healthy.side_effect = mock_is_service_healthy
        mock_service_manager.check_service_health.side_effect = mock_check_service_health
        
        # Test research status
        response = test_client.get("/api/advanced/research/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"  # Some services unavailable
        
        # Test research capabilities
        response = test_client.get("/api/advanced/research/capabilities")
        assert response.status_code == 200
        
        # Test basic search
        response = test_client.post(
            "/api/advanced/research/search/basic",
            json={"query": "machine learning", "max_results": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["service_used"] == "semantic_search"
        assert len(data["results"]) == 1