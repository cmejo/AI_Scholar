"""
Tests for Zotero sync monitoring service
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from models.zotero_models import (
    ZoteroSyncStatus, ZoteroSyncAuditLog, ZoteroSyncJob,
    ZoteroConnection, ZoteroWebhookEvent
)
from services.zotero.zotero_sync_monitoring_service import ZoteroSyncMonitoringService


class TestZoteroSyncMonitoringService:
    """Test cases for ZoteroSyncMonitoringService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def monitoring_service(self, mock_db):
        """Create monitoring service instance"""
        return ZoteroSyncMonitoringService(mock_db)
    
    @pytest.fixture
    def sample_sync_status(self):
        """Sample sync status notification"""
        return ZoteroSyncStatus(
            id="status-123",
            connection_id="conn-123",
            status_type="sync_progress",
            status="in_progress",
            title="Sync Started",
            message="Starting synchronization...",
            progress_percentage=25,
            is_read=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    def test_create_sync_notification(self, monitoring_service, mock_db):
        """Test creating a sync notification"""
        # Setup
        mock_db.commit.return_value = None
        
        # Execute
        notification_id = monitoring_service.create_sync_notification(
            connection_id="conn-123",
            status_type="sync_progress",
            status="in_progress",
            title="Sync Started",
            message="Starting synchronization...",
            progress_percentage=25,
            details={"job_id": "job-123"}
        )
        
        # Verify
        assert notification_id is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_get_sync_notifications(self, monitoring_service, mock_db, sample_sync_status):
        """Test getting sync notifications"""
        # Setup
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_sync_status]
        
        mock_db.query.return_value = mock_query
        
        with patch.object(monitoring_service, '_get_unread_count', return_value=1):
            # Execute
            result = monitoring_service.get_sync_notifications("conn-123")
        
        # Verify
        assert result['total_count'] == 1
        assert len(result['notifications']) == 1
        assert result['notifications'][0]['id'] == "status-123"
        assert result['notifications'][0]['status_type'] == "sync_progress"
        assert result['unread_count'] == 1
    
    def test_get_sync_notifications_with_filters(self, monitoring_service, mock_db, sample_sync_status):
        """Test getting sync notifications with filters"""
        # Setup
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_sync_status]
        
        mock_db.query.return_value = mock_query
        
        with patch.object(monitoring_service, '_get_unread_count', return_value=0):
            # Execute
            result = monitoring_service.get_sync_notifications(
                connection_id="conn-123",
                status_type="sync_progress",
                is_read=False,
                limit=10,
                offset=0
            )
        
        # Verify
        assert result['total_count'] == 1
        assert len(result['notifications']) == 1
        # Verify filters were applied (multiple filter calls)
        assert mock_query.filter.call_count >= 3
    
    def test_mark_notification_as_read_success(self, monitoring_service, mock_db, sample_sync_status):
        """Test successfully marking notification as read"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_sync_status
        mock_db.commit.return_value = None
        
        # Execute
        result = monitoring_service.mark_notification_as_read("status-123", "conn-123")
        
        # Verify
        assert result is True
        assert sample_sync_status.is_read is True
        assert sample_sync_status.updated_at is not None
        mock_db.commit.assert_called_once()
    
    def test_mark_notification_as_read_not_found(self, monitoring_service, mock_db):
        """Test marking non-existent notification as read"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = monitoring_service.mark_notification_as_read("nonexistent", "conn-123")
        
        # Verify
        assert result is False
    
    def test_mark_all_notifications_as_read(self, monitoring_service, mock_db):
        """Test marking all notifications as read"""
        # Setup
        mock_db.query.return_value.filter.return_value.update.return_value = 3
        mock_db.commit.return_value = None
        
        # Execute
        result = monitoring_service.mark_all_notifications_as_read("conn-123")
        
        # Verify
        assert result == 3
        mock_db.commit.assert_called_once()
    
    def test_delete_notification_success(self, monitoring_service, mock_db, sample_sync_status):
        """Test successfully deleting notification"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_sync_status
        mock_db.commit.return_value = None
        
        # Execute
        result = monitoring_service.delete_notification("status-123", "conn-123")
        
        # Verify
        assert result is True
        mock_db.delete.assert_called_once_with(sample_sync_status)
        mock_db.commit.assert_called_once()
    
    def test_delete_notification_not_found(self, monitoring_service, mock_db):
        """Test deleting non-existent notification"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = monitoring_service.delete_notification("nonexistent", "conn-123")
        
        # Verify
        assert result is False
    
    def test_cleanup_expired_notifications(self, monitoring_service, mock_db):
        """Test cleaning up expired notifications"""
        # Setup
        mock_db.query.return_value.filter.return_value.delete.return_value = 5
        mock_db.commit.return_value = None
        
        # Execute
        result = monitoring_service.cleanup_expired_notifications()
        
        # Verify
        assert result == 5
        mock_db.commit.assert_called_once()
    
    def test_get_sync_history(self, monitoring_service, mock_db):
        """Test getting sync history"""
        # Setup
        sample_log = Mock()
        sample_log.id = "log-123"
        sample_log.sync_job_id = "job-123"
        sample_log.action = "sync_started"
        sample_log.target_type = "library"
        sample_log.target_id = "lib-123"
        sample_log.user_id = "user-123"
        sample_log.old_data = None
        sample_log.new_data = {"job_type": "incremental_sync"}
        sample_log.created_at = datetime.utcnow()
        sample_log.audit_metadata = {}
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_log]
        
        mock_db.query.return_value = mock_query
        
        # Execute
        result = monitoring_service.get_sync_history("conn-123")
        
        # Verify
        assert result['total_count'] == 1
        assert len(result['history']) == 1
        assert result['history'][0]['id'] == "log-123"
        assert result['history'][0]['action'] == "sync_started"
    
    def test_get_sync_statistics(self, monitoring_service, mock_db):
        """Test getting sync statistics"""
        # Setup
        # Mock job statistics
        job_stat = Mock()
        job_stat.job_status = 'completed'
        job_stat.count = 5
        job_stat.total_items_processed = 100
        job_stat.total_items_added = 20
        job_stat.total_items_updated = 30
        job_stat.total_items_deleted = 5
        job_stat.total_errors = 2
        
        # Mock webhook statistics
        webhook_stat = Mock()
        webhook_stat.processing_status = 'completed'
        webhook_stat.count = 8
        
        # Mock recent jobs
        recent_job = Mock()
        recent_job.started_at = datetime.utcnow() - timedelta(minutes=10)
        recent_job.completed_at = datetime.utcnow()
        
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.side_effect = [
            [job_stat],  # job stats
            [webhook_stat]  # webhook stats
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [recent_job]
        
        # Execute
        result = monitoring_service.get_sync_statistics("conn-123", days=30)
        
        # Verify
        assert result['period_days'] == 30
        assert result['sync_jobs']['total'] == 5
        assert result['sync_jobs']['completed'] == 5
        assert result['sync_jobs']['success_rate'] == 100.0
        assert result['items']['total_processed'] == 100
        assert result['webhook_events']['total'] == 8
        assert result['performance']['recent_jobs_count'] == 1
    
    def test_get_error_summary(self, monitoring_service, mock_db):
        """Test getting error summary"""
        # Setup
        failed_job = Mock()
        failed_job.id = "job-123"
        failed_job.job_type = "incremental_sync"
        failed_job.created_at = datetime.utcnow()
        failed_job.errors_count = 2
        failed_job.retry_count = 1
        failed_job.error_details = [
            {"error": "Network connection timeout", "timestamp": "2024-01-01T00:00:00"},
            {"error": "Authentication failed", "timestamp": "2024-01-01T01:00:00"}
        ]
        
        error_notification = Mock()
        error_notification.id = "notif-123"
        error_notification.title = "Sync Failed"
        error_notification.message = "Network error occurred"
        error_notification.created_at = datetime.utcnow()
        error_notification.details = {"error_code": "NETWORK_ERROR"}
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.side_effect = [
            [failed_job],  # failed jobs
            [error_notification]  # error notifications
        ]
        
        # Execute
        result = monitoring_service.get_error_summary("conn-123", days=7)
        
        # Verify
        assert result['period_days'] == 7
        assert result['total_failed_jobs'] == 1
        assert result['total_error_notifications'] == 1
        assert len(result['failed_jobs']) == 1
        assert len(result['error_notifications']) == 1
        assert 'Network/Connection' in result['error_categories']
        assert 'Authentication' in result['error_categories']
    
    def test_create_progress_notification_new(self, monitoring_service, mock_db):
        """Test creating new progress notification"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.commit.return_value = None
        
        with patch.object(monitoring_service, 'create_sync_notification', return_value="notif-123") as mock_create:
            # Execute
            result = monitoring_service.create_progress_notification(
                connection_id="conn-123",
                job_id="job-123",
                progress_percentage=50,
                items_processed=25,
                total_items=50,
                current_operation="Syncing items"
            )
        
        # Verify
        assert result == "notif-123"
        mock_create.assert_called_once()
    
    def test_create_progress_notification_update_existing(self, monitoring_service, mock_db):
        """Test updating existing progress notification"""
        # Setup
        existing_notification = Mock()
        existing_notification.id = "notif-123"
        existing_notification.details = {}
        
        mock_db.query.return_value.filter.return_value.first.return_value = existing_notification
        mock_db.commit.return_value = None
        
        # Execute
        result = monitoring_service.create_progress_notification(
            connection_id="conn-123",
            job_id="job-123",
            progress_percentage=75,
            items_processed=37,
            total_items=50,
            current_operation="Finalizing sync"
        )
        
        # Verify
        assert result == "notif-123"
        assert existing_notification.progress_percentage == 75
        assert "Finalizing sync" in existing_notification.message
        assert existing_notification.details['items_processed'] == 37
        mock_db.commit.assert_called_once()
    
    def test_get_unread_count(self, monitoring_service, mock_db):
        """Test getting unread notification count"""
        # Setup
        mock_db.query.return_value.filter.return_value.count.return_value = 3
        
        # Execute
        result = monitoring_service._get_unread_count("conn-123")
        
        # Verify
        assert result == 3
    
    def test_categorize_error_network(self, monitoring_service):
        """Test error categorization for network errors"""
        result = monitoring_service._categorize_error("Network connection timeout")
        assert result == "Network/Connection"
        
        result = monitoring_service._categorize_error("Connection refused")
        assert result == "Network/Connection"
    
    def test_categorize_error_authentication(self, monitoring_service):
        """Test error categorization for authentication errors"""
        result = monitoring_service._categorize_error("Authentication failed")
        assert result == "Authentication"
        
        result = monitoring_service._categorize_error("Unauthorized access")
        assert result == "Authentication"
        
        result = monitoring_service._categorize_error("Invalid token")
        assert result == "Authentication"
    
    def test_categorize_error_rate_limiting(self, monitoring_service):
        """Test error categorization for rate limiting errors"""
        result = monitoring_service._categorize_error("Rate limit exceeded")
        assert result == "Rate Limiting"
        
        result = monitoring_service._categorize_error("Too many requests")
        assert result == "Rate Limiting"
    
    def test_categorize_error_permissions(self, monitoring_service):
        """Test error categorization for permission errors"""
        result = monitoring_service._categorize_error("Permission denied")
        assert result == "Permissions"
        
        result = monitoring_service._categorize_error("Forbidden access")
        assert result == "Permissions"
    
    def test_categorize_error_not_found(self, monitoring_service):
        """Test error categorization for not found errors"""
        result = monitoring_service._categorize_error("Resource not found")
        assert result == "Resource Not Found"
        
        result = monitoring_service._categorize_error("404 error")
        assert result == "Resource Not Found"
    
    def test_categorize_error_validation(self, monitoring_service):
        """Test error categorization for validation errors"""
        result = monitoring_service._categorize_error("Invalid data format")
        assert result == "Data Validation"
        
        result = monitoring_service._categorize_error("Validation failed")
        assert result == "Data Validation"
    
    def test_categorize_error_database(self, monitoring_service):
        """Test error categorization for database errors"""
        result = monitoring_service._categorize_error("Database connection failed")
        assert result == "Database"
        
        result = monitoring_service._categorize_error("SQL syntax error")
        assert result == "Database"
    
    def test_categorize_error_conflicts(self, monitoring_service):
        """Test error categorization for sync conflicts"""
        result = monitoring_service._categorize_error("Version conflict detected")
        assert result == "Sync Conflicts"
        
        result = monitoring_service._categorize_error("Conflict resolution required")
        assert result == "Sync Conflicts"
    
    def test_categorize_error_other(self, monitoring_service):
        """Test error categorization for unknown errors"""
        result = monitoring_service._categorize_error("Unknown error occurred")
        assert result == "Other"
        
        result = monitoring_service._categorize_error("Unexpected exception")
        assert result == "Other"
    
    def test_create_error_notification(self, monitoring_service, mock_db):
        """Test creating error notification"""
        mock_db.commit.return_value = None
        
        with patch.object(monitoring_service, 'create_sync_notification', return_value="error-notif-123") as mock_create:
            # Execute
            result = monitoring_service.create_error_notification(
                connection_id="conn-123",
                job_id="job-123",
                error_message="Network timeout occurred",
                error_details={"timeout_seconds": 30},
                retry_count=2
            )
        
        # Verify
        assert result == "error-notif-123"
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args[1]['status_type'] == 'error_report'
        assert call_args[1]['status'] == 'error'
        assert call_args[1]['title'] == 'Sync Error'
        assert call_args[1]['message'] == "Network timeout occurred"
        assert call_args[1]['details']['retry_count'] == 2
        assert call_args[1]['details']['error_category'] == 'Network/Connection'
    
    def test_create_completion_notification(self, monitoring_service, mock_db):
        """Test creating completion notification"""
        mock_db.commit.return_value = None
        
        with patch.object(monitoring_service, 'create_sync_notification', return_value="completion-notif-123") as mock_create:
            # Execute
            result = monitoring_service.create_completion_notification(
                connection_id="conn-123",
                job_id="job-123",
                items_processed=100,
                items_added=20,
                items_updated=15,
                items_deleted=5,
                sync_duration=45.5
            )
        
        # Verify
        assert result == "completion-notif-123"
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args[1]['status_type'] == 'completion_notification'
        assert call_args[1]['status'] == 'completed'
        assert call_args[1]['title'] == 'Sync Completed'
        assert "Processed 100 items" in call_args[1]['message']
        assert "added 20" in call_args[1]['message']
        assert "updated 15" in call_args[1]['message']
        assert "deleted 5" in call_args[1]['message']
        assert call_args[1]['progress_percentage'] == 100
        assert call_args[1]['details']['sync_duration_seconds'] == 45.5
        assert call_args[1]['expires_at'] is not None
    
    def test_create_warning_notification(self, monitoring_service, mock_db):
        """Test creating warning notification"""
        mock_db.commit.return_value = None
        
        with patch.object(monitoring_service, 'create_sync_notification', return_value="warning-notif-123") as mock_create:
            # Execute
            result = monitoring_service.create_warning_notification(
                connection_id="conn-123",
                job_id="job-123",
                warning_message="Some items could not be synced",
                warning_details={"skipped_items": 3}
            )
        
        # Verify
        assert result == "warning-notif-123"
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args[1]['status_type'] == 'warning'
        assert call_args[1]['status'] == 'warning'
        assert call_args[1]['title'] == 'Sync Warning'
        assert call_args[1]['message'] == "Some items could not be synced"
        assert call_args[1]['details']['warning_details']['skipped_items'] == 3
        assert call_args[1]['expires_at'] is not None
    
    def test_log_sync_audit_event(self, monitoring_service, mock_db):
        """Test logging sync audit event"""
        mock_db.commit.return_value = None
        
        # Execute
        result = monitoring_service.log_sync_audit_event(
            connection_id="conn-123",
            sync_job_id="job-123",
            action="item_added",
            target_type="item",
            target_id="item-123",
            old_data=None,
            new_data={"title": "New Paper", "authors": ["John Doe"]},
            user_id="user-123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            metadata={"source": "zotero_api"}
        )
        
        # Verify
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verify the audit log object
        audit_log = mock_db.add.call_args[0][0]
        assert audit_log.connection_id == "conn-123"
        assert audit_log.sync_job_id == "job-123"
        assert audit_log.action == "item_added"
        assert audit_log.target_type == "item"
        assert audit_log.target_id == "item-123"
        assert audit_log.old_data is None
        assert audit_log.new_data == {"title": "New Paper", "authors": ["John Doe"]}
        assert audit_log.user_id == "user-123"
        assert audit_log.ip_address == "192.168.1.1"
        assert audit_log.user_agent == "Mozilla/5.0"
        assert audit_log.audit_metadata == {"source": "zotero_api"}
    
    def test_get_real_time_sync_status(self, monitoring_service, mock_db):
        """Test getting real-time sync status"""
        # Setup active jobs
        active_job = Mock()
        active_job.id = "job-123"
        active_job.job_type = "incremental_sync"
        active_job.job_status = "running"
        active_job.progress_percentage = 75
        active_job.items_processed = 150
        active_job.started_at = datetime.utcnow()
        
        # Setup progress notifications
        progress_notification = Mock()
        progress_notification.id = "notif-123"
        progress_notification.message = "Syncing items - 150/200 items processed"
        progress_notification.progress_percentage = 75
        progress_notification.updated_at = datetime.utcnow()
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.all.return_value = [active_job]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [progress_notification]
        mock_db.query.return_value.filter.return_value.count.return_value = 2
        
        # Execute
        result = monitoring_service.get_real_time_sync_status("conn-123")
        
        # Verify
        assert result['is_syncing'] is True
        assert len(result['active_jobs']) == 1
        assert result['active_jobs'][0]['id'] == "job-123"
        assert result['active_jobs'][0]['job_type'] == "incremental_sync"
        assert result['active_jobs'][0]['status'] == "running"
        assert result['active_jobs'][0]['progress_percentage'] == 75
        assert len(result['progress_notifications']) == 1
        assert result['progress_notifications'][0]['id'] == "notif-123"
        assert result['recent_error_count'] == 2
        assert 'last_updated' in result
    
    def test_get_real_time_sync_status_no_active_jobs(self, monitoring_service, mock_db):
        """Test getting real-time sync status with no active jobs"""
        # Setup empty results
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        # Execute
        result = monitoring_service.get_real_time_sync_status("conn-123")
        
        # Verify
        assert result['is_syncing'] is False
        assert len(result['active_jobs']) == 0
        assert len(result['progress_notifications']) == 0
        assert result['recent_error_count'] == 0
        assert 'last_updated' in result
    
    def test_log_sync_audit_event_error_handling(self, monitoring_service, mock_db):
        """Test error handling in audit event logging"""
        # Setup database error
        mock_db.add.side_effect = Exception("Database error")
        mock_db.rollback.return_value = None
        
        # Execute and verify exception is raised
        with pytest.raises(Exception, match="Database error"):
            monitoring_service.log_sync_audit_event(
                connection_id="conn-123",
                sync_job_id="job-123",
                action="test_action"
            )
        
        # Verify rollback was called
        mock_db.rollback.assert_called_once()
    
    def test_create_completion_notification_minimal_changes(self, monitoring_service, mock_db):
        """Test creating completion notification with minimal changes"""
        mock_db.commit.return_value = None
        
        with patch.object(monitoring_service, 'create_sync_notification', return_value="completion-notif-123") as mock_create:
            # Execute with no changes
            result = monitoring_service.create_completion_notification(
                connection_id="conn-123",
                job_id="job-123",
                items_processed=50,
                items_added=0,
                items_updated=0,
                items_deleted=0,
                sync_duration=10.2
            )
        
        # Verify
        assert result == "completion-notif-123"
        call_args = mock_create.call_args
        # Should only mention processed items, not added/updated/deleted
        assert "Processed 50 items" in call_args[1]['message']
        assert "added" not in call_args[1]['message']
        assert "updated" not in call_args[1]['message']
        assert "deleted" not in call_args[1]['message']