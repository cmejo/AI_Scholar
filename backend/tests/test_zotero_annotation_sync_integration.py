"""
Integration Tests for Zotero Annotation Synchronization

This module contains integration tests that test the complete annotation
synchronization workflow including database operations and API interactions.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base
from models.zotero_models import (
    ZoteroConnection, ZoteroLibrary, ZoteroItem, ZoteroAttachment, ZoteroAnnotation,
    ZoteroAnnotationSyncLog, ZoteroAnnotationCollaboration, ZoteroAnnotationShare,
    ZoteroAnnotationHistory
)
from services.zotero.zotero_annotation_sync_service import ZoteroAnnotationSyncService


@pytest.fixture
def test_db_session():
    """Create test database session"""
    # Create in-memory SQLite database for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def test_connection(test_db_session):
    """Create test Zotero connection"""
    connection = ZoteroConnection(
        id="test-conn-123",
        user_id="test-user-123",
        zotero_user_id="zotero-user-123",
        access_token="test-access-token",
        connection_status="active"
    )
    test_db_session.add(connection)
    test_db_session.commit()
    test_db_session.refresh(connection)
    return connection


@pytest.fixture
def test_library(test_db_session, test_connection):
    """Create test library"""
    library = ZoteroLibrary(
        id="test-lib-123",
        connection_id=test_connection.id,
        zotero_library_id="zotero-lib-123",
        library_type="user",
        library_name="Test Library"
    )
    test_db_session.add(library)
    test_db_session.commit()
    test_db_session.refresh(library)
    return library


@pytest.fixture
def test_item(test_db_session, test_library):
    """Create test item"""
    item = ZoteroItem(
        id="test-item-123",
        library_id=test_library.id,
        zotero_item_key="item-key-123",
        item_type="article",
        title="Test Article"
    )
    test_db_session.add(item)
    test_db_session.commit()
    test_db_session.refresh(item)
    return item


@pytest.fixture
def test_attachment(test_db_session, test_item):
    """Create test attachment"""
    attachment = ZoteroAttachment(
        id="test-attachment-123",
        item_id=test_item.id,
        zotero_attachment_key="attachment-key-123",
        attachment_type="imported_file",
        title="Test PDF",
        filename="test.pdf",
        content_type="application/pdf"
    )
    test_db_session.add(attachment)
    test_db_session.commit()
    test_db_session.refresh(attachment)
    return attachment


@pytest.fixture
def test_annotation(test_db_session, test_attachment):
    """Create test annotation"""
    annotation = ZoteroAnnotation(
        id="test-annotation-123",
        attachment_id=test_attachment.id,
        zotero_annotation_key="annotation-key-123",
        annotation_type="highlight",
        annotation_text="Test highlighted text",
        annotation_comment="Test comment",
        page_number=1,
        position_data={"x": 100, "y": 200},
        color="#ffff00",
        annotation_version=1,
        sync_status="synced"
    )
    test_db_session.add(annotation)
    test_db_session.commit()
    test_db_session.refresh(annotation)
    return annotation


@pytest.fixture
def mock_zotero_client():
    """Mock Zotero client for integration tests"""
    client = Mock()
    client.get_item_annotations = AsyncMock()
    client.create_annotation = AsyncMock()
    client.update_annotation = AsyncMock()
    return client


class TestAnnotationSyncIntegration:
    """Integration tests for annotation synchronization"""
    
    @pytest.mark.asyncio
    async def test_full_sync_workflow_import(
        self, test_db_session, test_attachment, test_connection, mock_zotero_client
    ):
        """Test complete annotation import workflow"""
        # Mock Zotero API response
        zotero_annotations = [
            {
                "key": "new-annotation-key-1",
                "version": 1,
                "data": {
                    "annotationType": "highlight",
                    "annotationText": "New highlighted text 1",
                    "annotationComment": "New comment 1",
                    "annotationPageLabel": "1",
                    "annotationPosition": {"x": 150, "y": 250},
                    "annotationColor": "#ff0000",
                    "dateAdded": "2024-01-15T10:30:00Z",
                    "dateModified": "2024-01-15T10:30:00Z"
                }
            },
            {
                "key": "new-annotation-key-2",
                "version": 1,
                "data": {
                    "annotationType": "note",
                    "annotationText": "",
                    "annotationComment": "This is a note annotation",
                    "annotationPageLabel": "2",
                    "annotationColor": "#00ff00",
                    "dateAdded": "2024-01-15T11:00:00Z",
                    "dateModified": "2024-01-15T11:00:00Z"
                }
            }
        ]
        
        mock_zotero_client.get_item_annotations.return_value = zotero_annotations
        
        # Create service with mocked client
        with patch('services.zotero.zotero_annotation_sync_service.ZoteroClient') as mock_client_class:
            mock_client_class.return_value = mock_zotero_client
            service = ZoteroAnnotationSyncService(test_db_session)
            
            # Perform sync
            result = await service.sync_annotations_for_attachment(
                attachment_id=test_attachment.id,
                user_id=test_connection.user_id,
                sync_direction="from_zotero"
            )
            
            # Verify results
            assert result['annotations_imported'] == 2
            assert result['annotations_updated'] == 0
            assert result['conflicts_detected'] == 0
            assert len(result['errors']) == 0
            
            # Verify annotations were created in database
            annotations = test_db_session.query(ZoteroAnnotation).filter(
                ZoteroAnnotation.attachment_id == test_attachment.id
            ).all()
            
            # Should have original annotation plus 2 new ones
            assert len(annotations) == 3
            
            # Verify new annotations
            new_annotations = [a for a in annotations if a.zotero_annotation_key in ["new-annotation-key-1", "new-annotation-key-2"]]
            assert len(new_annotations) == 2
            
            highlight_annotation = next(a for a in new_annotations if a.annotation_type == "highlight")
            assert highlight_annotation.annotation_text == "New highlighted text 1"
            assert highlight_annotation.annotation_comment == "New comment 1"
            assert highlight_annotation.page_number == "1"
            assert highlight_annotation.color == "#ff0000"
            assert highlight_annotation.sync_status == "synced"
            
            note_annotation = next(a for a in new_annotations if a.annotation_type == "note")
            assert note_annotation.annotation_comment == "This is a note annotation"
            assert note_annotation.page_number == "2"
            assert note_annotation.color == "#00ff00"
    
    @pytest.mark.asyncio
    async def test_full_sync_workflow_export(
        self, test_db_session, test_attachment, test_connection, mock_zotero_client
    ):
        """Test complete annotation export workflow"""
        # Create local annotation that needs to be exported
        local_annotation = ZoteroAnnotation(
            id="local-annotation-123",
            attachment_id=test_attachment.id,
            zotero_annotation_key=None,  # No Zotero key yet
            annotation_type="highlight",
            annotation_text="Local highlighted text",
            annotation_comment="Local comment",
            page_number=3,
            position_data={"x": 200, "y": 300},
            color="#0000ff",
            annotation_version=1,
            sync_status="pending"
        )
        test_db_session.add(local_annotation)
        test_db_session.commit()
        
        # Mock Zotero API response for creation
        mock_zotero_client.create_annotation.return_value = {
            "key": "created-annotation-key-123",
            "version": 1
        }
        
        # Create service with mocked client
        with patch('services.zotero.zotero_annotation_sync_service.ZoteroClient') as mock_client_class:
            mock_client_class.return_value = mock_zotero_client
            service = ZoteroAnnotationSyncService(test_db_session)
            
            # Perform sync
            result = await service.sync_annotations_for_attachment(
                attachment_id=test_attachment.id,
                user_id=test_connection.user_id,
                sync_direction="to_zotero"
            )
            
            # Verify results
            assert result['annotations_exported'] == 1
            assert len(result['errors']) == 0
            
            # Verify annotation was updated with Zotero key
            test_db_session.refresh(local_annotation)
            assert local_annotation.zotero_annotation_key == "created-annotation-key-123"
            assert local_annotation.sync_status == "synced"
            assert local_annotation.last_synced_at is not None
            
            # Verify Zotero client was called correctly
            mock_zotero_client.create_annotation.assert_called_once()
            call_args = mock_zotero_client.create_annotation.call_args
            assert call_args[0][0] == test_connection.zotero_user_id
            assert call_args[0][1] == test_attachment.zotero_attachment_key
            assert call_args[0][3] == test_connection.access_token
            
            # Verify annotation data format
            annotation_data = call_args[0][2]
            assert annotation_data['annotationType'] == "highlight"
            assert annotation_data['annotationText'] == "Local highlighted text"
            assert annotation_data['annotationComment'] == "Local comment"
            assert annotation_data['annotationPageLabel'] == "3"
            assert annotation_data['annotationColor'] == "#0000ff"
    
    @pytest.mark.asyncio
    async def test_annotation_collaboration_workflow(
        self, test_db_session, test_annotation
    ):
        """Test complete annotation collaboration workflow"""
        service = ZoteroAnnotationSyncService(test_db_session)
        
        # Create initial comment
        comment = await service.create_annotation_collaboration(
            annotation_id=test_annotation.id,
            user_id="user-123",
            collaboration_type="comment",
            content="This is an important highlight"
        )
        
        # Verify comment was created
        assert comment.annotation_id == test_annotation.id
        assert comment.user_id == "user-123"
        assert comment.collaboration_type == "comment"
        assert comment.content == "This is an important highlight"
        assert comment.parent_collaboration_id is None
        assert comment.is_active is True
        
        # Create reply to the comment
        reply = await service.create_annotation_collaboration(
            annotation_id=test_annotation.id,
            user_id="user-456",
            collaboration_type="reply",
            content="I agree, this is very relevant",
            parent_collaboration_id=comment.id
        )
        
        # Verify reply was created
        assert reply.annotation_id == test_annotation.id
        assert reply.user_id == "user-456"
        assert reply.collaboration_type == "reply"
        assert reply.content == "I agree, this is very relevant"
        assert reply.parent_collaboration_id == comment.id
        
        # Get all collaborations for the annotation
        collaborations = await service.get_annotation_collaborations(test_annotation.id)
        
        # Verify we have both comment and reply
        assert len(collaborations) == 2
        comment_collab = next(c for c in collaborations if c.collaboration_type == "comment")
        reply_collab = next(c for c in collaborations if c.collaboration_type == "reply")
        
        assert comment_collab.content == "This is an important highlight"
        assert reply_collab.content == "I agree, this is very relevant"
        assert reply_collab.parent_collaboration_id == comment_collab.id
        
        # Verify history was logged
        history = await service.get_annotation_history(test_annotation.id)
        assert len(history) >= 2  # At least 2 history entries for the collaborations
    
    @pytest.mark.asyncio
    async def test_annotation_sharing_workflow(
        self, test_db_session, test_annotation
    ):
        """Test complete annotation sharing workflow"""
        service = ZoteroAnnotationSyncService(test_db_session)
        
        # Share annotation with another user
        share = await service.share_annotation(
            annotation_id=test_annotation.id,
            owner_user_id="user-123",
            shared_with_user_id="user-456",
            permission_level="comment",
            share_message="Please review this annotation"
        )
        
        # Verify share was created
        assert share.annotation_id == test_annotation.id
        assert share.owner_user_id == "user-123"
        assert share.shared_with_user_id == "user-456"
        assert share.permission_level == "comment"
        assert share.share_message == "Please review this annotation"
        assert share.is_active is True
        
        # Get shared annotations for the recipient
        shared_annotations = await service.get_shared_annotations("user-456")
        
        # Verify the annotation appears in shared list
        assert len(shared_annotations) == 1
        shared_item = shared_annotations[0]
        assert shared_item['share'].id == share.id
        assert shared_item['annotation'].id == test_annotation.id
        
        # Update share permission
        updated_share = await service.share_annotation(
            annotation_id=test_annotation.id,
            owner_user_id="user-123",
            shared_with_user_id="user-456",
            permission_level="edit",
            share_message="Updated: you can now edit"
        )
        
        # Verify share was updated (same ID, updated permission)
        assert updated_share.id == share.id
        assert updated_share.permission_level == "edit"
        assert updated_share.share_message == "Updated: you can now edit"
        
        # Verify history was logged
        history = await service.get_annotation_history(test_annotation.id)
        share_history = [h for h in history if h.change_type == "share"]
        assert len(share_history) >= 1
    
    @pytest.mark.asyncio
    async def test_annotation_conflict_resolution(
        self, test_db_session, test_attachment, test_connection, mock_zotero_client
    ):
        """Test annotation conflict detection and resolution"""
        # Create local annotation that was modified recently
        local_annotation = ZoteroAnnotation(
            id="conflict-annotation-123",
            attachment_id=test_attachment.id,
            zotero_annotation_key="conflict-key-123",
            annotation_type="highlight",
            annotation_text="Local modified text",
            annotation_comment="Local modified comment",
            page_number=1,
            color="#ffff00",
            annotation_version=2,
            sync_status="synced",
            last_synced_at=datetime.utcnow() - timedelta(hours=2),
            updated_at=datetime.utcnow() - timedelta(minutes=30)  # Modified recently
        )
        test_db_session.add(local_annotation)
        test_db_session.commit()
        
        # Mock Zotero API response with conflicting changes
        zotero_annotations = [
            {
                "key": "conflict-key-123",
                "version": 3,
                "data": {
                    "annotationType": "highlight",
                    "annotationText": "Zotero modified text",
                    "annotationComment": "Zotero modified comment",
                    "annotationPageLabel": "1",
                    "annotationColor": "#ff0000",
                    "dateAdded": "2024-01-15T10:30:00Z",
                    "dateModified": (datetime.utcnow() - timedelta(minutes=15)).isoformat() + "Z"  # Also modified recently
                }
            }
        ]
        
        mock_zotero_client.get_item_annotations.return_value = zotero_annotations
        
        # Create service with mocked client
        with patch('services.zotero.zotero_annotation_sync_service.ZoteroClient') as mock_client_class:
            mock_client_class.return_value = mock_zotero_client
            service = ZoteroAnnotationSyncService(test_db_session)
            
            # Perform sync
            result = await service.sync_annotations_for_attachment(
                attachment_id=test_attachment.id,
                user_id=test_connection.user_id,
                sync_direction="from_zotero"
            )
            
            # Verify conflict was detected
            assert result['conflicts_detected'] == 1
            assert result['annotations_imported'] == 0
            assert result['annotations_updated'] == 0
            
            # Verify annotation was updated with Zotero version (default resolution strategy)
            test_db_session.refresh(local_annotation)
            assert local_annotation.annotation_text == "Zotero modified text"
            assert local_annotation.annotation_comment == "Zotero modified comment"
            assert local_annotation.color == "#ff0000"
            assert local_annotation.sync_status == "synced"
            
            # Verify conflict was logged in history
            history = await service.get_annotation_history(local_annotation.id)
            conflict_history = [h for h in history if h.change_type == "conflict"]
            assert len(conflict_history) >= 1
            
            conflict_entry = conflict_history[0]
            assert "local_data" in conflict_entry.new_content
            assert "zotero_data" in conflict_entry.new_content
            assert conflict_entry.new_content["resolution_strategy"] == "from_zotero"


class TestAnnotationSyncErrorHandling:
    """Test error handling in annotation synchronization"""
    
    @pytest.mark.asyncio
    async def test_sync_with_api_error(
        self, test_db_session, test_attachment, test_connection, mock_zotero_client
    ):
        """Test handling of Zotero API errors during sync"""
        # Mock API error
        mock_zotero_client.get_item_annotations.side_effect = Exception("API Error")
        
        # Create service with mocked client
        with patch('services.zotero.zotero_annotation_sync_service.ZoteroClient') as mock_client_class:
            mock_client_class.return_value = mock_zotero_client
            service = ZoteroAnnotationSyncService(test_db_session)
            
            # Perform sync should raise exception
            with pytest.raises(Exception, match="API Error"):
                await service.sync_annotations_for_attachment(
                    attachment_id=test_attachment.id,
                    user_id=test_connection.user_id,
                    sync_direction="from_zotero"
                )
    
    @pytest.mark.asyncio
    async def test_partial_sync_failure(
        self, test_db_session, test_attachment, test_connection, mock_zotero_client
    ):
        """Test handling of partial sync failures"""
        # Mock Zotero API response with one valid and one invalid annotation
        zotero_annotations = [
            {
                "key": "valid-annotation-key",
                "version": 1,
                "data": {
                    "annotationType": "highlight",
                    "annotationText": "Valid annotation",
                    "annotationComment": "Valid comment",
                    "annotationPageLabel": "1",
                    "annotationColor": "#ffff00"
                }
            },
            {
                "key": "invalid-annotation-key",
                "version": 1,
                "data": {
                    # Missing required fields to cause processing error
                    "annotationType": "invalid_type"
                }
            }
        ]
        
        mock_zotero_client.get_item_annotations.return_value = zotero_annotations
        
        # Create service with mocked client
        with patch('services.zotero.zotero_annotation_sync_service.ZoteroClient') as mock_client_class:
            mock_client_class.return_value = mock_zotero_client
            service = ZoteroAnnotationSyncService(test_db_session)
            
            # Mock _process_zotero_annotation to fail for invalid annotation
            original_process = service._process_zotero_annotation
            
            async def mock_process(attachment, annotation_data):
                if annotation_data['key'] == 'invalid-annotation-key':
                    raise ValueError("Invalid annotation data")
                return await original_process(attachment, annotation_data)
            
            service._process_zotero_annotation = mock_process
            
            # Perform sync
            result = await service.sync_annotations_for_attachment(
                attachment_id=test_attachment.id,
                user_id=test_connection.user_id,
                sync_direction="from_zotero"
            )
            
            # Verify partial success
            assert result['annotations_imported'] == 1  # Only valid annotation
            assert len(result['errors']) == 1  # One error for invalid annotation
            assert result['errors'][0]['annotation_key'] == 'invalid-annotation-key'
            assert "Invalid annotation data" in result['errors'][0]['error']
            
            # Verify valid annotation was still created
            annotations = test_db_session.query(ZoteroAnnotation).filter(
                ZoteroAnnotation.zotero_annotation_key == "valid-annotation-key"
            ).all()
            assert len(annotations) == 1
            assert annotations[0].annotation_text == "Valid annotation"