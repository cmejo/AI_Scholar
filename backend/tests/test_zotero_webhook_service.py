"""
Tests for Zotero webhook service
"""
import pytest
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from models.zotero_models import (
    ZoteroConnection, ZoteroWebhookEndpoint, ZoteroWebhookEvent,
    ZoteroSyncJob, ZoteroSyncStatus, ZoteroSyncAuditLog
)
from services.zotero.zotero_webhook_service import ZoteroWebhookService


class TestZoteroWebhookService:
    """Test cases for ZoteroWebhookService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def webhook_service(self, mock_db):
        """Create webhook service instance"""
        return ZoteroWebhookService(mock_db)
    
    @pytest.fixture
    def sample_connection(self):
        """Sample Zotero connection"""
        return ZoteroConnection(
            id="conn-123",
            user_id="user-123",
            zotero_user_id="zotero-123",
            access_token="token-123",
            connection_status="active"
        )
    
    @pytest.fixture
    def sample_webhook_endpoint(self):
        """Sample webhook endpoint"""
        return ZoteroWebhookEndpoint(
            id="webhook-123",
            user_id="user-123",
            connection_id="conn-123",
            webhook_url="https://example.com/webhook",
            webhook_secret="secret-123",
            webhook_status="active"
        )
    
    def test_register_webhook_endpoint_new(self, webhook_service, mock_db):
        """Test registering a new webhook endpoint"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.commit.return_value = None
        
        # Execute
        result = webhook_service.register_webhook_endpoint(
            user_id="user-123",
            connection_id="conn-123",
            webhook_url="https://example.com/webhook"
        )
        
        # Verify
        assert "endpoint_id" in result
        assert result["webhook_url"] == "https://example.com/webhook"
        assert result["status"] == "active"
        assert "webhook_secret" in result
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
    
    def test_register_webhook_endpoint_existing(self, webhook_service, mock_db, sample_webhook_endpoint):
        """Test updating an existing webhook endpoint"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_webhook_endpoint
        mock_db.commit.return_value = None
        
        # Execute
        result = webhook_service.register_webhook_endpoint(
            user_id="user-123",
            connection_id="conn-123",
            webhook_url="https://example.com/webhook",
            webhook_secret="new-secret"
        )
        
        # Verify
        assert result["endpoint_id"] == sample_webhook_endpoint.id
        assert sample_webhook_endpoint.webhook_secret == "new-secret"
        assert sample_webhook_endpoint.webhook_status == "active"
        mock_db.commit.assert_called()
    
    def test_validate_webhook_signature_valid(self, webhook_service):
        """Test webhook signature validation with valid signature"""
        # Setup
        payload = b'{"test": "data"}'
        secret = "test-secret"
        signature = "sha256=" + hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Execute
        result = webhook_service.validate_webhook_signature(payload, signature, secret)
        
        # Verify
        assert result is True
    
    def test_validate_webhook_signature_invalid(self, webhook_service):
        """Test webhook signature validation with invalid signature"""
        # Setup
        payload = b'{"test": "data"}'
        secret = "test-secret"
        signature = "sha256=invalid-signature"
        
        # Execute
        result = webhook_service.validate_webhook_signature(payload, signature, secret)
        
        # Verify
        assert result is False
    
    def test_process_webhook_event_success(self, webhook_service, mock_db, sample_webhook_endpoint):
        """Test successful webhook event processing"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_webhook_endpoint
        mock_db.commit.return_value = None
        
        event_data = {"library_id": "123", "items": ["item1", "item2"]}
        
        with patch.object(webhook_service, '_queue_sync_job_for_event') as mock_queue:
            # Execute
            result = webhook_service.process_webhook_event(
                endpoint_id="webhook-123",
                event_type="library_update",
                event_data=event_data
            )
        
        # Verify
        assert "event_id" in result
        assert result["status"] == "accepted"
        assert result["processing_status"] == "pending"
        mock_db.add.assert_called_once()
        mock_queue.assert_called_once()
    
    def test_process_webhook_event_invalid_signature(self, webhook_service, mock_db, sample_webhook_endpoint):
        """Test webhook event processing with invalid signature"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_webhook_endpoint
        
        event_data = {"library_id": "123"}
        payload = b'{"test": "data"}'
        signature = "sha256=invalid-signature"
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Invalid webhook signature"):
            webhook_service.process_webhook_event(
                endpoint_id="webhook-123",
                event_type="library_update",
                event_data=event_data,
                signature=signature,
                raw_payload=payload
            )
    
    def test_process_webhook_event_endpoint_not_found(self, webhook_service, mock_db):
        """Test webhook event processing with non-existent endpoint"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Webhook endpoint not found"):
            webhook_service.process_webhook_event(
                endpoint_id="nonexistent",
                event_type="library_update",
                event_data={}
            )
    
    def test_queue_sync_job_for_event_new_job(self, webhook_service, mock_db):
        """Test queuing new sync job for webhook event"""
        # Setup
        webhook_event = Mock()
        webhook_event.id = "event-123"
        webhook_event.event_type = "library_update"
        webhook_event.event_data = {"library_id": "123"}
        webhook_event.endpoint = Mock()
        webhook_event.endpoint.connection_id = "conn-123"
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.commit.return_value = None
        
        # Execute
        webhook_service._queue_sync_job_for_event(webhook_event)
        
        # Verify
        mock_db.add.assert_called_once()
        assert webhook_event.processing_status == "processing"
        mock_db.commit.assert_called()
    
    def test_queue_sync_job_for_event_existing_job(self, webhook_service, mock_db):
        """Test queuing sync job when existing job exists"""
        # Setup
        webhook_event = Mock()
        webhook_event.id = "event-123"
        webhook_event.event_type = "library_update"
        webhook_event.event_data = {"library_id": "123"}
        webhook_event.endpoint = Mock()
        webhook_event.endpoint.connection_id = "conn-123"
        
        existing_job = Mock()
        existing_job.job_metadata = {}
        mock_db.query.return_value.filter.return_value.first.return_value = existing_job
        mock_db.commit.return_value = None
        
        # Execute
        webhook_service._queue_sync_job_for_event(webhook_event)
        
        # Verify
        assert "webhook_events" in existing_job.job_metadata
        assert webhook_event.id in existing_job.job_metadata["webhook_events"]
        assert webhook_event.processing_status == "processing"
    
    def test_determine_sync_type(self, webhook_service):
        """Test sync type determination based on event type"""
        # Test library update
        result = webhook_service._determine_sync_type("library_update", {})
        assert result == "incremental_sync"
        
        # Test item update
        result = webhook_service._determine_sync_type("item_update", {})
        assert result == "webhook_triggered"
        
        # Test unknown event
        result = webhook_service._determine_sync_type("unknown_event", {})
        assert result == "incremental_sync"
    
    def test_get_webhook_endpoints(self, webhook_service, mock_db, sample_webhook_endpoint):
        """Test getting webhook endpoints for user"""
        # Setup
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_webhook_endpoint]
        
        # Execute
        result = webhook_service.get_webhook_endpoints("user-123")
        
        # Verify
        assert len(result) == 1
        assert result[0]["id"] == sample_webhook_endpoint.id
        assert result[0]["webhook_url"] == sample_webhook_endpoint.webhook_url
        assert result[0]["status"] == sample_webhook_endpoint.webhook_status
    
    def test_update_webhook_endpoint_status(self, webhook_service, mock_db, sample_webhook_endpoint):
        """Test updating webhook endpoint status"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_webhook_endpoint
        mock_db.commit.return_value = None
        
        # Execute
        webhook_service.update_webhook_endpoint_status(
            endpoint_id="webhook-123",
            status="error",
            error_message="Connection failed"
        )
        
        # Verify
        assert sample_webhook_endpoint.webhook_status == "error"
        assert sample_webhook_endpoint.error_count == 1
        assert sample_webhook_endpoint.last_error_at is not None
        mock_db.commit.assert_called_once()
    
    def test_update_webhook_endpoint_status_not_found(self, webhook_service, mock_db):
        """Test updating non-existent webhook endpoint status"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Webhook endpoint not found"):
            webhook_service.update_webhook_endpoint_status(
                endpoint_id="nonexistent",
                status="error"
            )
    
    def test_delete_webhook_endpoint_success(self, webhook_service, mock_db, sample_webhook_endpoint):
        """Test successful webhook endpoint deletion"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_webhook_endpoint
        mock_db.commit.return_value = None
        
        # Execute
        result = webhook_service.delete_webhook_endpoint("webhook-123", "user-123")
        
        # Verify
        assert result is True
        mock_db.delete.assert_called_once_with(sample_webhook_endpoint)
        mock_db.commit.assert_called()
    
    def test_delete_webhook_endpoint_not_found(self, webhook_service, mock_db):
        """Test deleting non-existent webhook endpoint"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = webhook_service.delete_webhook_endpoint("nonexistent", "user-123")
        
        # Verify
        assert result is False
    
    def test_get_webhook_events(self, webhook_service, mock_db):
        """Test getting webhook events for endpoint"""
        # Setup
        sample_events = [
            Mock(
                id="event-1",
                event_type="library_update",
                event_data={"test": "data"},
                processing_status="completed",
                retry_count=0,
                error_message=None,
                created_at=datetime.utcnow(),
                processed_at=datetime.utcnow()
            )
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_events
        
        mock_db.query.return_value = mock_query
        
        # Execute
        result = webhook_service.get_webhook_events("webhook-123")
        
        # Verify
        assert result["total_count"] == 1
        assert len(result["events"]) == 1
        assert result["events"][0]["id"] == "event-1"
        assert result["events"][0]["event_type"] == "library_update"
    
    def test_retry_failed_webhook_events(self, webhook_service, mock_db):
        """Test retrying failed webhook events"""
        # Setup
        failed_event = Mock()
        failed_event.processing_status = "failed"
        failed_event.retry_count = 1
        failed_event.max_retries = 3
        
        mock_db.query.return_value.filter.return_value.all.return_value = [failed_event]
        mock_db.commit.return_value = None
        
        with patch.object(webhook_service, '_queue_sync_job_for_event') as mock_queue:
            # Execute
            result = webhook_service.retry_failed_webhook_events("webhook-123")
        
        # Verify
        assert result["retried_count"] == 1
        assert failed_event.processing_status == "retrying"
        assert failed_event.retry_count == 2
        assert failed_event.next_retry_at is not None
        mock_queue.assert_called_once()
    
    def test_generate_webhook_secret(self, webhook_service):
        """Test webhook secret generation"""
        secret = webhook_service._generate_webhook_secret()
        
        assert isinstance(secret, str)
        assert len(secret) > 20  # Should be reasonably long
    
    def test_log_audit_event(self, webhook_service, mock_db):
        """Test audit event logging"""
        # Setup
        mock_db.commit.return_value = None
        
        # Execute
        webhook_service._log_audit_event(
            connection_id="conn-123",
            action="webhook_registered",
            target_type="webhook",
            target_id="webhook-123",
            user_id="user-123"
        )
        
        # Verify
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()