"""
Tests for Zotero background sync service
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from models.zotero_models import (
    ZoteroSyncJob, ZoteroConnection, ZoteroLibrary,
    ZoteroSyncConflict, ZoteroSyncStatus, ZoteroSyncAuditLog
)
from services.zotero.zotero_background_sync_service import ZoteroBackgroundSyncService


class TestZoteroBackgroundSyncService:
    """Test cases for ZoteroBackgroundSyncService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sync_service(self, mock_db):
        """Create background sync service instance"""
        service = ZoteroBackgroundSyncService(mock_db)
        service.sync_service = Mock()
        return service
    
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
    def sample_library(self):
        """Sample Zotero library"""
        return ZoteroLibrary(
            id="lib-123",
            connection_id="conn-123",
            zotero_library_id="zotero-lib-123",
            library_type="user",
            library_name="My Library"
        )
    
    @pytest.fixture
    def sample_sync_job(self):
        """Sample sync job"""
        return ZoteroSyncJob(
            id="job-123",
            connection_id="conn-123",
            job_type="incremental_sync",
            job_status="queued",
            priority=5
        )
    
    @pytest.mark.asyncio
    async def test_process_sync_jobs_success(self, sync_service, mock_db, sample_sync_job):
        """Test successful sync job processing"""
        # Setup
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [sample_sync_job]
        mock_db.commit.return_value = None
        
        with patch.object(sync_service, '_process_single_job', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {"status": "success", "job_id": "job-123"}
            
            # Execute
            result = await sync_service.process_sync_jobs()
        
        # Verify
        assert result["processed_jobs"] == 1
        assert result["successful_jobs"] == 1
        assert result["failed_jobs"] == 0
        assert result["status"] == "completed"
        mock_process.assert_called_once_with(sample_sync_job)
    
    @pytest.mark.asyncio
    async def test_process_sync_jobs_no_jobs(self, sync_service, mock_db):
        """Test processing when no jobs are queued"""
        # Setup
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        # Execute
        result = await sync_service.process_sync_jobs()
        
        # Verify
        assert result["processed_jobs"] == 0
        assert result["status"] == "no_jobs_queued"
    
    @pytest.mark.asyncio
    async def test_process_single_job_incremental_sync(self, sync_service, mock_db, sample_sync_job):
        """Test processing single incremental sync job"""
        # Setup
        sample_sync_job.job_type = "incremental_sync"
        mock_db.commit.return_value = None
        
        with patch.object(sync_service, '_process_incremental_sync', new_callable=AsyncMock) as mock_incremental:
            mock_incremental.return_value = {
                'items_processed': 10,
                'items_added': 2,
                'items_updated': 3,
                'items_deleted': 1,
                'errors_count': 0,
                'error_details': []
            }
            
            with patch.object(sync_service, '_create_sync_status') as mock_status:
                with patch.object(sync_service, '_log_audit_event') as mock_audit:
                    # Execute
                    result = await sync_service._process_single_job(sample_sync_job)
        
        # Verify
        assert result["status"] == "success"
        assert sample_sync_job.job_status == "completed"
        assert sample_sync_job.items_processed == 10
        assert sample_sync_job.items_added == 2
        assert sample_sync_job.items_updated == 3
        assert sample_sync_job.items_deleted == 1
        mock_incremental.assert_called_once_with(sample_sync_job)
        mock_status.assert_called()
        mock_audit.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_single_job_failure(self, sync_service, mock_db, sample_sync_job):
        """Test processing single job with failure"""
        # Setup
        sample_sync_job.job_type = "incremental_sync"
        sample_sync_job.retry_count = 0
        sample_sync_job.max_retries = 3
        mock_db.commit.return_value = None
        
        with patch.object(sync_service, '_process_incremental_sync', new_callable=AsyncMock) as mock_incremental:
            mock_incremental.side_effect = Exception("Sync failed")
            
            with patch.object(sync_service, '_create_sync_status') as mock_status:
                with patch.object(sync_service, '_log_audit_event') as mock_audit:
                    # Execute
                    result = await sync_service._process_single_job(sample_sync_job)
        
        # Verify
        assert result["status"] == "error"
        assert sample_sync_job.job_status == "queued"  # Re-queued for retry
        assert sample_sync_job.retry_count == 1
        assert sample_sync_job.next_retry_at is not None
        assert len(sample_sync_job.error_details) == 1
        mock_status.assert_called()
        mock_audit.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_full_sync(self, sync_service, mock_db, sample_sync_job, sample_connection, sample_library):
        """Test full sync processing"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_connection
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_library]
        mock_db.commit.return_value = None
        
        sync_service.sync_service.sync_library = AsyncMock(return_value={
            'items_processed': 5,
            'items_added': 1,
            'items_updated': 2,
            'items_deleted': 0,
            'errors': []
        })
        
        # Execute
        result = await sync_service._process_full_sync(sample_sync_job)
        
        # Verify
        assert result['items_processed'] == 5
        assert result['items_added'] == 1
        assert result['items_updated'] == 2
        assert result['items_deleted'] == 0
        assert result['libraries_synced'] == 1
        sync_service.sync_service.sync_library.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_incremental_sync(self, sync_service, mock_db, sample_sync_job, sample_connection, sample_library):
        """Test incremental sync processing"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_connection
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_library]
        mock_db.commit.return_value = None
        
        sync_service.sync_service.incremental_sync = AsyncMock(return_value={
            'items_processed': 3,
            'items_added': 0,
            'items_updated': 2,
            'items_deleted': 1,
            'errors': []
        })
        
        with patch.object(sync_service, '_detect_and_resolve_conflicts', new_callable=AsyncMock) as mock_conflicts:
            mock_conflicts.return_value = []
            
            # Execute
            result = await sync_service._process_incremental_sync(sample_sync_job)
        
        # Verify
        assert result['items_processed'] == 3
        assert result['items_updated'] == 2
        assert result['items_deleted'] == 1
        assert result['libraries_synced'] == 1
        sync_service.sync_service.incremental_sync.assert_called_once()
        mock_conflicts.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_webhook_triggered_sync(self, sync_service, mock_db, sample_sync_job, sample_library):
        """Test webhook-triggered sync processing"""
        # Setup
        sample_sync_job.job_metadata = {
            'trigger_event_data': {'library_id': 'zotero-lib-123'}
        }
        
        mock_db.query.return_value.filter.return_value.first.return_value = sample_library
        
        sync_service.sync_service.incremental_sync = AsyncMock(return_value={
            'items_processed': 2,
            'items_added': 1,
            'items_updated': 1,
            'items_deleted': 0,
            'errors': []
        })
        
        with patch.object(sync_service, '_detect_and_resolve_conflicts', new_callable=AsyncMock) as mock_conflicts:
            mock_conflicts.return_value = []
            
            # Execute
            result = await sync_service._process_webhook_triggered_sync(sample_sync_job)
        
        # Verify
        assert result['items_processed'] == 2
        assert result['items_added'] == 1
        sync_service.sync_service.incremental_sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_detect_and_resolve_conflicts(self, sync_service, mock_db, sample_sync_job, sample_library):
        """Test conflict detection and resolution"""
        # Setup
        sync_result = {
            'conflicts': [
                {
                    'item_id': 'item-123',
                    'conflict_type': 'version_mismatch',
                    'local_version': 1,
                    'remote_version': 2,
                    'local_data': {'title': 'Old Title'},
                    'remote_data': {'title': 'New Title'}
                }
            ]
        }
        
        mock_conflict = Mock()
        mock_conflict.id = 'conflict-123'
        mock_conflict.conflict_type = 'version_mismatch'
        
        with patch.object(sync_service, '_create_sync_conflict', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_conflict
            
            with patch.object(sync_service, '_resolve_conflict', new_callable=AsyncMock) as mock_resolve:
                mock_resolve.return_value = {'status': 'failed', 'error': 'Resolution failed'}
                
                # Execute
                result = await sync_service._detect_and_resolve_conflicts(sample_sync_job, sample_library, sync_result)
        
        # Verify
        assert len(result) == 1
        assert result[0]['conflict_id'] == 'conflict-123'
        assert result[0]['resolution_status'] == 'failed'
        mock_create.assert_called_once()
        mock_resolve.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_sync_conflict(self, sync_service, mock_db, sample_sync_job):
        """Test sync conflict creation"""
        # Setup
        conflict_data = {
            'item_id': 'item-123',
            'conflict_type': 'version_mismatch',
            'local_version': 1,
            'remote_version': 2,
            'local_data': {'title': 'Old Title'},
            'remote_data': {'title': 'New Title'}
        }
        
        mock_db.commit.return_value = None
        
        # Execute
        result = await sync_service._create_sync_conflict(sample_sync_job, conflict_data)
        
        # Verify
        assert result.sync_job_id == sample_sync_job.id
        assert result.item_id == 'item-123'
        assert result.conflict_type == 'version_mismatch'
        assert result.resolution_strategy == 'zotero_wins'
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_resolve_conflict_zotero_wins(self, sync_service, mock_db):
        """Test conflict resolution with Zotero wins strategy"""
        # Setup
        mock_item = Mock()
        mock_item.title = "Old Title"
        
        mock_conflict = Mock()
        mock_conflict.id = "conflict-123"
        mock_conflict.item_id = "item-123"
        mock_conflict.collection_id = None
        mock_conflict.resolution_strategy = "zotero_wins"
        mock_conflict.remote_version = 2
        mock_conflict.remote_data = {"title": "New Title", "abstract_note": "New Abstract"}
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_item
        mock_db.commit.return_value = None
        
        # Execute
        result = await sync_service._resolve_conflict(mock_conflict)
        
        # Verify
        assert result['status'] == 'resolved'
        assert result['strategy'] == 'zotero_wins'
        assert mock_item.title == "New Title"
        assert mock_item.item_version == 2
        assert mock_conflict.resolution_status == 'resolved'
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_resolve_conflict_manual(self, sync_service, mock_db):
        """Test conflict resolution requiring manual intervention"""
        # Setup
        mock_conflict = Mock()
        mock_conflict.resolution_strategy = "manual"
        mock_db.commit.return_value = None
        
        # Execute
        result = await sync_service._resolve_conflict(mock_conflict)
        
        # Verify
        assert result['status'] == 'manual_required'
        assert mock_conflict.resolution_status == 'manual_required'
        mock_db.commit.assert_called_once()
    
    def test_schedule_sync_job(self, sync_service, mock_db):
        """Test sync job scheduling"""
        # Setup
        mock_db.commit.return_value = None
        
        # Execute
        job_id = sync_service.schedule_sync_job(
            connection_id="conn-123",
            job_type="incremental_sync",
            priority=3,
            job_metadata={"test": "data"}
        )
        
        # Verify
        assert job_id is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_get_sync_jobs(self, sync_service, mock_db):
        """Test getting sync jobs"""
        # Setup
        sample_jobs = [
            Mock(
                id="job-1",
                connection_id="conn-123",
                job_type="incremental_sync",
                job_status="completed",
                priority=5,
                progress_percentage=100,
                items_processed=10,
                items_added=2,
                items_updated=3,
                items_deleted=1,
                errors_count=0,
                retry_count=0,
                scheduled_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                next_retry_at=None
            )
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_jobs
        
        mock_db.query.return_value = mock_query
        
        # Execute
        result = sync_service.get_sync_jobs(connection_id="conn-123")
        
        # Verify
        assert result['total_count'] == 1
        assert len(result['jobs']) == 1
        assert result['jobs'][0]['id'] == "job-1"
        assert result['jobs'][0]['job_type'] == "incremental_sync"
    
    def test_cancel_sync_job_success(self, sync_service, mock_db):
        """Test successful sync job cancellation"""
        # Setup
        mock_job = Mock()
        mock_job.id = "job-123"
        mock_job.job_status = "queued"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job
        mock_db.commit.return_value = None
        
        with patch.object(sync_service, '_log_audit_event') as mock_audit:
            # Execute
            result = sync_service.cancel_sync_job("job-123")
        
        # Verify
        assert result is True
        assert mock_job.job_status == "cancelled"
        assert mock_job.completed_at is not None
        mock_audit.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_cancel_sync_job_not_found(self, sync_service, mock_db):
        """Test cancelling non-existent sync job"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = sync_service.cancel_sync_job("nonexistent")
        
        # Verify
        assert result is False
    
    def test_cancel_sync_job_already_completed(self, sync_service, mock_db):
        """Test cancelling already completed sync job"""
        # Setup
        mock_job = Mock()
        mock_job.job_status = "completed"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job
        
        # Execute
        result = sync_service.cancel_sync_job("job-123")
        
        # Verify
        assert result is False
    
    def test_create_sync_status(self, sync_service, mock_db):
        """Test sync status creation"""
        # Setup
        mock_db.commit.return_value = None
        
        # Execute
        sync_service._create_sync_status(
            connection_id="conn-123",
            status_type="sync_progress",
            status="in_progress",
            title="Sync Started",
            message="Starting synchronization...",
            progress_percentage=25
        )
        
        # Verify
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_log_audit_event(self, sync_service, mock_db):
        """Test audit event logging"""
        # Setup
        mock_db.commit.return_value = None
        
        # Execute
        sync_service._log_audit_event(
            connection_id="conn-123",
            action="sync_started",
            sync_job_id="job-123",
            new_data={"job_type": "incremental_sync"}
        )
        
        # Verify
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()