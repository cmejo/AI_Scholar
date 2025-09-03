"""
Tests for Zotero Annotation Synchronization Service

This module contains comprehensive tests for annotation synchronization,
collaboration, and sharing functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from services.zotero.zotero_annotation_sync_service import ZoteroAnnotationSyncService
from models.zotero_models import (
    ZoteroConnection, ZoteroLibrary, ZoteroItem, ZoteroAttachment, ZoteroAnnotation,
    ZoteroAnnotationSyncLog, ZoteroAnnotationCollaboration, ZoteroAnnotationShare,
    ZoteroAnnotationHistory
)


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def mock_zotero_client():
    """Mock Zotero client"""
    client = Mock()
    client.get_item_annotations = AsyncMock()
    client.create_annotation = AsyncMock()
    client.update_annotation = AsyncMock()
    return client


@pytest.fixture
def annotation_sync_service(mock_db_session):
    """Create annotation sync service with mocked dependencies"""
    with patch('services.zotero.zotero_annotation_sync_service.ZoteroClient') as mock_client_class:
        mock_client_class.return_value = Mock()
        service = ZoteroAnnotationSyncService(mock_db_session)
        return service


@pytest.fixture
def sample_zotero_connection():
    """Sample Zotero connection"""
    return ZoteroConnection(
        id="conn-123",
        user_id="user-123",
        zotero_user_id="zotero-user-123",
        access_token="access-token-123",
        connection_status="active"
    )


@pytest.fixture
def sample_attachment():
    """Sample attachment"""
    return ZoteroAttachment(
        id="attachment-123",
        item_id="item-123",
        zotero_attachment_key="attachment-key-123",
        attachment_type="imported_file",
        title="Sample PDF",
        filename="sample.pdf",
        content_type="application/pdf"
    )


@pytest.fixture
def sample_annotation():
    """Sample annotation"""
    return ZoteroAnnotation(
        id="annotation-123",
        attachment_id="attachment-123",
        zotero_annotation_key="annotation-key-123",
        annotation_type="highlight",
        annotation_text="Sample highlighted text",
        annotation_comment="This is important",
        page_number=1,
        position_data={"x": 100, "y": 200, "width": 150, "height": 20},
        color="#ffff00",
        annotation_version=1,
        sync_status="synced"
    )


@pytest.fixture
def sample_zotero_annotation_data():
    """Sample Zotero annotation data from API"""
    return {
        "key": "annotation-key-456",
        "version": 2,
        "data": {
            "annotationType": "highlight",
            "annotationText": "New highlighted text",
            "annotationComment": "Updated comment",
            "annotationPageLabel": "2",
            "annotationPosition": {"x": 150, "y": 250},
            "annotationSortIndex": "00001",
            "annotationColor": "#ff0000",
            "dateAdded": "2024-01-15T10:30:00Z",
            "dateModified": "2024-01-15T11:00:00Z"
        }
    }


class TestZoteroAnnotationSyncService:
    """Test cases for ZoteroAnnotationSyncService"""
    
    @pytest.mark.asyncio
    async def test_sync_annotations_for_attachment_success(
        self, annotation_sync_service, mock_db_session, sample_attachment, sample_zotero_connection
    ):
        """Test successful annotation synchronization"""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_attachment
        annotation_sync_service._get_user_connection = Mock(return_value=sample_zotero_connection)
        annotation_sync_service._import_annotations_from_zotero = AsyncMock(return_value={
            'annotations_imported': 2,
            'annotations_updated': 1,
            'conflicts_detected': 0,
            'errors': []
        })
        annotation_sync_service._export_annotations_to_zotero = AsyncMock(return_value={
            'exported': 1,
            'errors': []
        })
        annotation_sync_service._log_sync_operation = AsyncMock()
        
        # Test sync
        result = await annotation_sync_service.sync_annotations_for_attachment(
            attachment_id="attachment-123",
            user_id="user-123",
            sync_direction="bidirectional"
        )
        
        # Verify results
        assert result['attachment_id'] == "attachment-123"
        assert result['sync_direction'] == "bidirectional"
        assert result['annotations_imported'] == 2
        assert result['annotations_updated'] == 1
        assert result['annotations_exported'] == 1
        assert result['conflicts_detected'] == 0
        assert len(result['errors']) == 0
    
    @pytest.mark.asyncio
    async def test_sync_annotations_attachment_not_found(
        self, annotation_sync_service, mock_db_session
    ):
        """Test sync with non-existent attachment"""
        # Mock database query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Test sync should raise ValueError
        with pytest.raises(ValueError, match="Attachment attachment-123 not found"):
            await annotation_sync_service.sync_annotations_for_attachment(
                attachment_id="attachment-123",
                user_id="user-123"
            )
    
    @pytest.mark.asyncio
    async def test_sync_annotations_no_connection(
        self, annotation_sync_service, mock_db_session, sample_attachment
    ):
        """Test sync with no Zotero connection"""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_attachment
        annotation_sync_service._get_user_connection = Mock(return_value=None)
        
        # Test sync should raise ValueError
        with pytest.raises(ValueError, match="No Zotero connection found for user user-123"):
            await annotation_sync_service.sync_annotations_for_attachment(
                attachment_id="attachment-123",
                user_id="user-123"
            )
    
    @pytest.mark.asyncio
    async def test_import_annotations_from_zotero(
        self, annotation_sync_service, sample_attachment, sample_zotero_connection,
        sample_zotero_annotation_data
    ):
        """Test importing annotations from Zotero"""
        # Mock Zotero client
        annotation_sync_service.zotero_client.get_item_annotations = AsyncMock(
            return_value=[sample_zotero_annotation_data]
        )
        annotation_sync_service._process_zotero_annotation = AsyncMock(
            return_value={'action': 'imported', 'annotation_id': 'new-annotation-123'}
        )
        
        # Test import
        result = await annotation_sync_service._import_annotations_from_zotero(
            sample_attachment, sample_zotero_connection
        )
        
        # Verify results
        assert result['annotations_imported'] == 1
        assert result['annotations_updated'] == 0
        assert result['conflicts_detected'] == 0
        assert len(result['errors']) == 0
    
    @pytest.mark.asyncio
    async def test_process_zotero_annotation_new(
        self, annotation_sync_service, mock_db_session, sample_attachment, sample_zotero_annotation_data
    ):
        """Test processing new annotation from Zotero"""
        # Mock database query to return None (no existing annotation)
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        annotation_sync_service._create_annotation = AsyncMock(
            return_value=Mock(id="new-annotation-123")
        )
        
        # Test processing
        result = await annotation_sync_service._process_zotero_annotation(
            sample_attachment, sample_zotero_annotation_data
        )
        
        # Verify results
        assert result['action'] == 'imported'
        assert result['annotation_id'] == "new-annotation-123"
    
    @pytest.mark.asyncio
    async def test_process_zotero_annotation_update(
        self, annotation_sync_service, mock_db_session, sample_attachment, 
        sample_annotation, sample_zotero_annotation_data
    ):
        """Test processing existing annotation from Zotero"""
        # Mock database query to return existing annotation
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_annotation
        annotation_sync_service._has_annotation_conflict = Mock(return_value=False)
        annotation_sync_service._update_annotation = AsyncMock()
        
        # Test processing
        result = await annotation_sync_service._process_zotero_annotation(
            sample_attachment, sample_zotero_annotation_data
        )
        
        # Verify results
        assert result['action'] == 'updated'
        assert result['annotation_id'] == sample_annotation.id
    
    @pytest.mark.asyncio
    async def test_process_zotero_annotation_conflict(
        self, annotation_sync_service, mock_db_session, sample_attachment,
        sample_annotation, sample_zotero_annotation_data
    ):
        """Test processing annotation with conflict"""
        # Mock database query to return existing annotation
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_annotation
        annotation_sync_service._has_annotation_conflict = Mock(return_value=True)
        annotation_sync_service._handle_annotation_conflict = AsyncMock()
        
        # Test processing
        result = await annotation_sync_service._process_zotero_annotation(
            sample_attachment, sample_zotero_annotation_data
        )
        
        # Verify results
        assert result['action'] == 'conflict'
        assert result['annotation_id'] == sample_annotation.id
    
    @pytest.mark.asyncio
    async def test_create_annotation_collaboration(
        self, annotation_sync_service, mock_db_session
    ):
        """Test creating annotation collaboration"""
        # Mock database operations
        mock_collaboration = Mock()
        mock_collaboration.id = "collaboration-123"
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()
        annotation_sync_service._log_annotation_history = AsyncMock()
        
        with patch('services.zotero.zotero_annotation_sync_service.ZoteroAnnotationCollaboration') as mock_class:
            mock_class.return_value = mock_collaboration
            
            # Test collaboration creation
            result = await annotation_sync_service.create_annotation_collaboration(
                annotation_id="annotation-123",
                user_id="user-123",
                collaboration_type="comment",
                content="This is a comment"
            )
            
            # Verify results
            assert result == mock_collaboration
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            annotation_sync_service._log_annotation_history.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_share_annotation_new(
        self, annotation_sync_service, mock_db_session
    ):
        """Test sharing annotation with new user"""
        # Mock database operations
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        mock_share = Mock()
        mock_share.id = "share-123"
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()
        annotation_sync_service._log_annotation_history = AsyncMock()
        
        with patch('services.zotero.zotero_annotation_sync_service.ZoteroAnnotationShare') as mock_class:
            mock_class.return_value = mock_share
            
            # Test annotation sharing
            result = await annotation_sync_service.share_annotation(
                annotation_id="annotation-123",
                owner_user_id="user-123",
                shared_with_user_id="user-456",
                permission_level="read",
                share_message="Check this out"
            )
            
            # Verify results
            assert result == mock_share
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            annotation_sync_service._log_annotation_history.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_share_annotation_existing(
        self, annotation_sync_service, mock_db_session
    ):
        """Test updating existing annotation share"""
        # Mock existing share
        existing_share = Mock()
        existing_share.permission_level = "read"
        existing_share.share_message = "Old message"
        mock_db_session.query.return_value.filter.return_value.first.return_value = existing_share
        mock_db_session.commit = Mock()
        
        # Test annotation sharing update
        result = await annotation_sync_service.share_annotation(
            annotation_id="annotation-123",
            owner_user_id="user-123",
            shared_with_user_id="user-456",
            permission_level="edit",
            share_message="Updated message"
        )
        
        # Verify results
        assert result == existing_share
        assert existing_share.permission_level == "edit"
        assert existing_share.share_message == "Updated message"
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_annotation_collaborations(
        self, annotation_sync_service, mock_db_session
    ):
        """Test getting annotation collaborations"""
        # Mock database query
        mock_collaborations = [Mock(), Mock()]
        mock_query = mock_db_session.query.return_value
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_collaborations
        
        # Test getting collaborations
        result = await annotation_sync_service.get_annotation_collaborations(
            annotation_id="annotation-123"
        )
        
        # Verify results
        assert result == mock_collaborations
        mock_db_session.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_annotation_history(
        self, annotation_sync_service, mock_db_session
    ):
        """Test getting annotation history"""
        # Mock database query
        mock_history = [Mock(), Mock(), Mock()]
        mock_query = mock_db_session.query.return_value
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_history
        
        # Test getting history
        result = await annotation_sync_service.get_annotation_history(
            annotation_id="annotation-123",
            limit=50
        )
        
        # Verify results
        assert result == mock_history
        mock_db_session.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_shared_annotations(
        self, annotation_sync_service, mock_db_session
    ):
        """Test getting shared annotations"""
        # Mock database queries
        mock_share = Mock()
        mock_share.annotation_id = "annotation-123"
        mock_annotation = Mock()
        mock_attachment = Mock()
        mock_annotation.attachment = mock_attachment
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_share]
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_annotation
        
        # Test getting shared annotations
        result = await annotation_sync_service.get_shared_annotations(
            user_id="user-123"
        )
        
        # Verify results
        assert len(result) == 1
        assert result[0]['share'] == mock_share
        assert result[0]['annotation'] == mock_annotation
        assert result[0]['attachment'] == mock_attachment
    
    def test_extract_annotation_data(self, annotation_sync_service, sample_zotero_annotation_data):
        """Test extracting annotation data from Zotero format"""
        result = annotation_sync_service._extract_annotation_data(sample_zotero_annotation_data)
        
        # Verify extracted data
        assert result['zotero_annotation_key'] == "annotation-key-456"
        assert result['annotation_type'] == "highlight"
        assert result['annotation_text'] == "New highlighted text"
        assert result['annotation_comment'] == "Updated comment"
        assert result['page_number'] == "2"
        assert result['color'] == "#ff0000"
        assert 'position' in result['position_data']
        assert 'version' in result['annotation_metadata']
    
    def test_has_annotation_conflict_true(self, annotation_sync_service, sample_annotation):
        """Test conflict detection when conflict exists"""
        # Set up annotation with recent local modification
        sample_annotation.updated_at = datetime.utcnow() - timedelta(minutes=5)
        sample_annotation.last_synced_at = datetime.utcnow() - timedelta(hours=1)
        
        zotero_data = {
            'annotation_metadata': {
                'dateModified': (datetime.utcnow() - timedelta(minutes=10)).isoformat() + 'Z'
            }
        }
        
        # Test conflict detection
        result = annotation_sync_service._has_annotation_conflict(sample_annotation, zotero_data)
        
        # Should detect conflict
        assert result is True
    
    def test_has_annotation_conflict_false(self, annotation_sync_service, sample_annotation):
        """Test conflict detection when no conflict exists"""
        # Set up annotation with old local modification
        sample_annotation.updated_at = datetime.utcnow() - timedelta(hours=2)
        sample_annotation.last_synced_at = datetime.utcnow() - timedelta(hours=1)
        
        zotero_data = {
            'annotation_metadata': {
                'dateModified': (datetime.utcnow() - timedelta(minutes=10)).isoformat() + 'Z'
            }
        }
        
        # Test conflict detection
        result = annotation_sync_service._has_annotation_conflict(sample_annotation, zotero_data)
        
        # Should not detect conflict
        assert result is False
    
    def test_convert_to_zotero_format(self, annotation_sync_service, sample_annotation):
        """Test converting annotation to Zotero format"""
        result = annotation_sync_service._convert_to_zotero_format(sample_annotation)
        
        # Verify converted data
        assert result['annotationType'] == "highlight"
        assert result['annotationText'] == "Sample highlighted text"
        assert result['annotationComment'] == "This is important"
        assert result['annotationPageLabel'] == "1"
        assert result['annotationColor'] == "#ffff00"
    
    @pytest.mark.asyncio
    async def test_export_annotations_to_zotero(
        self, annotation_sync_service, mock_db_session, sample_attachment, sample_zotero_connection
    ):
        """Test exporting annotations to Zotero"""
        # Mock local annotations
        mock_annotation = Mock()
        mock_annotation.id = "annotation-123"
        mock_annotation.zotero_annotation_key = None
        mock_annotation.sync_status = "pending"
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_annotation]
        
        # Mock Zotero client
        annotation_sync_service.zotero_client.create_annotation = AsyncMock(
            return_value={'key': 'new-annotation-key-123'}
        )
        annotation_sync_service._convert_to_zotero_format = Mock(
            return_value={'annotationType': 'highlight'}
        )
        mock_db_session.commit = Mock()
        
        # Test export
        result = await annotation_sync_service._export_annotations_to_zotero(
            sample_attachment, sample_zotero_connection
        )
        
        # Verify results
        assert result['exported'] == 1
        assert len(result['errors']) == 0
        assert mock_annotation.zotero_annotation_key == 'new-annotation-key-123'
        assert mock_annotation.sync_status == 'synced'


class TestAnnotationSyncIntegration:
    """Integration tests for annotation synchronization"""
    
    @pytest.mark.asyncio
    async def test_full_sync_workflow(self, annotation_sync_service):
        """Test complete annotation sync workflow"""
        # This would be an integration test that tests the full workflow
        # from fetching Zotero annotations to storing them locally
        # and handling conflicts and collaborations
        pass
    
    @pytest.mark.asyncio
    async def test_collaboration_workflow(self, annotation_sync_service):
        """Test annotation collaboration workflow"""
        # This would test creating comments, replies, and managing
        # collaborative annotation features
        pass
    
    @pytest.mark.asyncio
    async def test_sharing_workflow(self, annotation_sync_service):
        """Test annotation sharing workflow"""
        # This would test sharing annotations between users
        # and managing permissions
        pass