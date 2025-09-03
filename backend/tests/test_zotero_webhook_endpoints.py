"""
Tests for Zotero webhook API endpoints
"""
import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from api.zotero_webhook_endpoints import router


@pytest.fixture
def app():
    """Create FastAPI test app"""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock current user"""
    return {"id": "user-123", "email": "test@example.com"}


@pytest.fixture
def mock_webhook_service():
    """Mock webhook service"""
    return Mock()


class TestZoteroWebhookEndpoints:
    """Test cases for Zotero webhook endpoints"""
    
    @patch('api.zotero_webhook_endpoints.get_current_user')
    @patch('api.zotero_webhook_endpoints.get_db')
    @patch('api.zotero_webhook_endpoints.ZoteroWebhookService')
    def test_register_webhook_endpoint_success(self, mock_service_class, mock_db, mock_auth, client, mock_current_user):
        """Test successful webhook endpoint registration"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.register_webhook_endpoint.return_value = {
            "endpoint_id": "webhook-123",
            "webhook_url": "https://example.com/webhook",
            "webhook_secret": "secret-123",
            "status": "active"
        }
        
        # Execute
        response = client.post("/api/zotero/webhooks/endpoints", json={
            "connection_id": "conn-123",
            "webhook_url": "https://example.com/webhook"
        })
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "endpoint_id" in data["data"]
        mock_service.register_webhook_endpoint.assert_called_once_with(
            user_id="user-123",
            connection_id="conn-123",
            webhook_url="https://example.com/webhook",
            webhook_secret=None
        )
    
    @patch('api.zotero_webhook_endpoints.get_current_user')
    @patch('api.zotero_webhook_endpoints.get_db')
    @patch('api.zotero_webhook_endpoints.ZoteroWebhookService')
    def test_register_webhook_endpoint_with_secret(self, mock_service_class, mock_db, mock_auth, client, mock_current_user):
        """Test webhook endpoint registration with custom secret"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.register_webhook_endpoint.return_value = {
            "endpoint_id": "webhook-123",
            "webhook_url": "https://example.com/webhook",
            "webhook_secret": "custom-secret",
            "status": "active"
        }
        
        # Execute
        response = client.post("/api/zotero/webhooks/endpoints", json={
            "connection_id": "conn-123",
            "webhook_url": "https://example.com/webhook",
            "webhook_secret": "custom-secret"
        })
        
        # Verify
        assert response.status_code == 200
        mock_service.register_webhook_endpoint.assert_called_once_with(
            user_id="user-123",
            connection_id="conn-123",
            webhook_url="https://example.com/webhook",
            webhook_secret="custom-secret"
        )
    
    @patch('api.zotero_webhook_endpoints.get_current_user')
    @patch('api.zotero_webhook_endpoints.get_db')
    @patch('api.zotero_webhook_endpoints.ZoteroWebhookService')
    def test_get_webhook_endpoints_success(self, mock_service_class, mock_db, mock_auth, client, mock_current_user):
        """Test successful retrieval of webhook endpoints"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_webhook_endpoints.return_value = [
            {
                "id": "webhook-123",
                "connection_id": "conn-123",
                "webhook_url": "https://example.com/webhook",
                "status": "active",
                "error_count": 0,
                "created_at": "2024-01-01T00:00:00"
            }
        ]
        
        # Execute
        response = client.get("/api/zotero/webhooks/endpoints")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]["endpoints"]) == 1
        assert data["data"]["total_count"] == 1
        mock_service.get_webhook_endpoints.assert_called_once_with("user-123")
    
    @patch('api.zotero_webhook_endpoints.get_current_user')
    @patch('api.zotero_webhook_endpoints.get_db')
    @patch('api.zotero_webhook_endpoints.ZoteroWebhookService')
    def test_update_webhook_endpoint_status_success(self, mock_service_class, mock_db, mock_auth, client, mock_current_user):
        """Test successful webhook endpoint status update"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.update_webhook_endpoint_status.return_value = None
        
        # Execute
        response = client.put("/api/zotero/webhooks/endpoints/webhook-123/status", json={
            "status": "inactive",
            "error_message": "Connection timeout"
        })
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        mock_service.update_webhook_endpoint_status.assert_called_once_with(
            endpoint_id="webhook-123",
            status="inactive",
            error_message="Connection timeout"
        )
    
    @patch('api.zotero_webhook_endpoints.get_current_user')
    @patch('api.zotero_webhook_endpoints.get_db')
    @patch('api.zotero_webhook_endpoints.ZoteroWebhookService')
    def test_update_webhook_endpoint_status_not_found(self, mock_service_class, mock_db, mock_auth, client, mock_current_user):
        """Test webhook endpoint status update with non-existent endpoint"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.update_webhook_endpoint_status.side_effect = ValueError("Webhook endpoint not found")
        
        # Execute
        response = client.put("/api/zotero/webhooks/endpoints/nonexistent/status", json={
            "status": "inactive"
        })
        
        # Verify
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @patch('api.zotero_webhook_endpoints.get_current_user')
    @patch('api.zotero_webhook_endpoints.get_db')
    @patch('api.zotero_webhook_endpoints.ZoteroWebhookService')
    def test_delete_webhook_endpoint_success(self, mock_service_class, mock_db, mock_auth, client, mock_current_user):
        """Test successful webhook endpoint deletion"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.delete_webhook_endpoint.return_value = True
        
        # Execute
        response = client.delete("/api/zotero/webhooks/endpoints/webhook-123")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        mock_service.delete_webhook_endpoint.assert_called_once_with(
            endpoint_id="webhook-123",
            user_id="user-123"
        )
    
    @patch('api.zotero_webhook_endpoints.get_current_user')
    @patch('api.zotero_webhook_endpoints.get_db')
    @patch('api.zotero_webhook_endpoints.ZoteroWebhookService')
    def test_delete_webhook_endpoint_not_found(self, mock_service_class, mock_db, mock_auth, client, mock_current_user):
        """Test webhook endpoint deletion with non-existent endpoint"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.delete_webhook_endpoint.return_value = False
        
        # Execute
        response = client.delete("/api/zotero/webhooks/endpoints/nonexistent")
        
        # Verify
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @patch('api.zotero_webhook_endpoints.get_db')
    @patch('api.zotero_webhook_endpoints.ZoteroWebhookService')
    def test_process_webhook_event_success(self, mock_service_class, mock_db, client):
        """Test successful webhook event processing"""
        # Setup
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.process_webhook_event.return_value = {
            "event_id": "event-123",
            "status": "accepted",
            "processing_status": "pending"
        }
        
        # Execute
        response = client.post("/api/zotero/webhooks/endpoints/webhook-123/events", json={
            "event_type": "library_update",
            "event_data": {"library_id": "123", "items": ["item1", "item2"]}
        })
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "event_id" in data["data"]
        mock_service.process_webhook_event.assert_called_once()
    
    @patch('api.zotero_webhook_endpoints.get_db')
    @patch('api.zotero_webhook_endpoints.ZoteroWebhookService')
    def test_process_webhook_event_invalid_signature(self, mock_service_class, mock_db, client):
        """Test webhook event processing with invalid signature"""
        # Setup
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.process_webhook_event.side_effect = ValueError("Invalid webhook signature")
        
        # Execute
        response = client.post(
            "/api/zotero/webhooks/endpoints/webhook-123/events",
            json={
                "event_type": "library_update",
                "event_data": {"library_id": "123"}
            },
            headers={"X-Zotero-Signature": "sha256=invalid"}
        )
        
        # Verify
        assert response.status_code == 400
        assert "Invalid webhook signature" in response.json()["detail"]
    
    @patch('api.zotero_webhook_endpoints.get_current_user')
    @patch('api.zotero_webhook_endpoints.get_db')
    @patch('api.zotero_webhook_endpoints.ZoteroWebhookService')
    def test_get_webhook_events_success(self, mock_service_class, mock_db, mock_auth, client, mock_current_user):
        """Test successful retrieval of webhook events"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_webhook_endpoints.return_value = [{"id": "webhook-123"}]
        mock_service.get_webhook_events.return_value = {
            "events": [
                {
                    "id": "event-123",
                    "event_type": "library_update",
                    "processing_status": "completed",
                    "created_at": "2024-01-01T00:00:00"
                }
            ],
            "total_count": 1,
            "limit": 50,
            "offset": 0
        }
        
        # Execute
        response = client.get("/api/zotero/webhooks/endpoints/webhook-123/events")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]["events"]) == 1
        assert data["data"]["total_count"] == 1
    
    @patch('api.zotero_webhook_endpoints.get_current_user')
    @patch('api.zotero_webhook_endpoints.get_db')
    @patch('api.zotero_webhook_endpoints.ZoteroWebhookService')
    def test_get_webhook_events_unauthorized(self, mock_service_class, mock_db, mock_auth, client, mock_current_user):
        """Test webhook events retrieval for unauthorized endpoint"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_webhook_endpoints.return_value = []  # User doesn't own this endpoint
        
        # Execute
        response = client.get("/api/zotero/webhooks/endpoints/webhook-123/events")
        
        # Verify
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @patch('api.zotero_webhook_endpoints.get_current_user')
    @patch('api.zotero_webhook_endpoints.get_db')
    @patch('api.zotero_webhook_endpoints.ZoteroWebhookService')
    def test_retry_failed_webhook_events_success(self, mock_service_class, mock_db, mock_auth, client, mock_current_user):
        """Test successful retry of failed webhook events"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_webhook_endpoints.return_value = [{"id": "webhook-123"}]
        mock_service.retry_failed_webhook_events.return_value = {
            "retried_count": 3,
            "status": "success"
        }
        
        # Execute
        response = client.post("/api/zotero/webhooks/endpoints/webhook-123/events/retry")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Retried 3 failed webhook events" in data["message"]
        mock_service.retry_failed_webhook_events.assert_called_once_with("webhook-123")
    
    @patch('api.zotero_webhook_endpoints.get_current_user')
    @patch('api.zotero_webhook_endpoints.get_db')
    @patch('api.zotero_webhook_endpoints.ZoteroWebhookService')
    def test_check_webhook_endpoint_health_healthy(self, mock_service_class, mock_db, mock_auth, client, mock_current_user):
        """Test webhook endpoint health check - healthy status"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_webhook_endpoints.return_value = [
            {
                "id": "webhook-123",
                "error_count": 0,
                "last_ping_at": "2024-01-01T00:00:00",
                "last_error_at": None
            }
        ]
        mock_service.get_webhook_events.return_value = {
            "events": [
                {"processing_status": "completed"},
                {"processing_status": "completed"}
            ],
            "total_count": 2
        }
        
        # Execute
        response = client.get("/api/zotero/webhooks/endpoints/webhook-123/health")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["health_status"] == "healthy"
        assert data["data"]["success_rate"] == 100.0
        assert data["data"]["total_events"] == 2
        assert data["data"]["failed_events"] == 0
    
    @patch('api.zotero_webhook_endpoints.get_current_user')
    @patch('api.zotero_webhook_endpoints.get_db')
    @patch('api.zotero_webhook_endpoints.ZoteroWebhookService')
    def test_check_webhook_endpoint_health_degraded(self, mock_service_class, mock_db, mock_auth, client, mock_current_user):
        """Test webhook endpoint health check - degraded status"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_webhook_endpoints.return_value = [
            {
                "id": "webhook-123",
                "error_count": 3,
                "last_ping_at": "2024-01-01T00:00:00",
                "last_error_at": "2024-01-01T01:00:00"
            }
        ]
        mock_service.get_webhook_events.return_value = {
            "events": [
                {"processing_status": "completed"},
                {"processing_status": "failed"},
                {"processing_status": "failed"}
            ],
            "total_count": 3
        }
        
        # Execute
        response = client.get("/api/zotero/webhooks/endpoints/webhook-123/health")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["health_status"] == "degraded"
        assert data["data"]["success_rate"] == pytest.approx(33.33, rel=1e-2)
        assert data["data"]["failed_events"] == 2
    
    @patch('api.zotero_webhook_endpoints.get_current_user')
    @patch('api.zotero_webhook_endpoints.get_db')
    @patch('api.zotero_webhook_endpoints.ZoteroWebhookService')
    def test_check_webhook_endpoint_health_unhealthy(self, mock_service_class, mock_db, mock_auth, client, mock_current_user):
        """Test webhook endpoint health check - unhealthy status"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_webhook_endpoints.return_value = [
            {
                "id": "webhook-123",
                "error_count": 10,
                "last_ping_at": "2024-01-01T00:00:00",
                "last_error_at": "2024-01-01T01:00:00"
            }
        ]
        mock_service.get_webhook_events.return_value = {
            "events": [],
            "total_count": 0
        }
        
        # Execute
        response = client.get("/api/zotero/webhooks/endpoints/webhook-123/health")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["health_status"] == "unhealthy"
        assert data["data"]["error_count"] == 10