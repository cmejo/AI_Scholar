"""
Tests for Zotero Annotation Synchronization API Endpoints

This module contains tests for the REST API endpoints that handle
annotation synchronization, collaboration, and sharing.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

from api.zotero_annotation_sync_endpoints import router
from models.zotero_models import ZoteroAnnotationCollaboration, ZoteroAnnotationShare


@pytest.fixture
def mock_annotation_sync_service():
    """Mock annotation sync service"""
    service = Mock()
    service.sync_annotations_for_attachment = AsyncMock()
    service.create_annotation_collaboration = AsyncMock()
    service.share_annotation = AsyncMock()
    service.get_annotation_collaborations = AsyncMock()
    service.get_annotation_history = AsyncMock()
    service.get_shared_annotations = AsyncMock()
    return service


@pytest.fixture
def mock_current_user():
    """Mock current user"""
    return {"user_id": "user-123", "email": "test@example.com"}


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return Mock()


@pytest.fixture
def sample_sync_response():
    """Sample sync response data"""
    return {
        'attachment_id': 'attachment-123',
        'sync_direction': 'bidirectional',
        'annotations_imported': 2,
        'annotations_exported': 1,
        'annotations_updated': 1,
        'conflicts_detected': 0,
        'errors': []
    }


@pytest.fixture
def sample_collaboration():
    """Sample annotation collaboration"""
    collaboration = Mock(spec=ZoteroAnnotationCollaboration)
    collaboration.id = "collaboration-123"
    collaboration.annotation_id = "annotation-123"
    collaboration.user_id = "user-123"
    collaboration.collaboration_type = "comment"
    collaboration.content = "This is a comment"
    collaboration.parent_collaboration_id = None
    collaboration.is_active = True
    collaboration.created_at = datetime.utcnow()
    collaboration.updated_at = datetime.utcnow()
    collaboration.metadata = {}
    return collaboration


@pytest.fixture
def sample_share():
    """Sample annotation share"""
    share = Mock(spec=ZoteroAnnotationShare)
    share.id = "share-123"
    share.annotation_id = "annotation-123"
    share.owner_user_id = "user-123"
    share.shared_with_user_id = "user-456"
    share.permission_level = "read"
    share.share_message = "Check this out"
    share.is_active = True
    share.created_at = datetime.utcnow()
    share.updated_at = datetime.utcnow()
    share.metadata = {}
    return share


class TestAnnotationSyncEndpoints:
    """Test cases for annotation sync endpoints"""
    
    @patch('api.zotero_annotation_sync_endpoints.ZoteroAnnotationSyncService')
    @patch('api.zotero_annotation_sync_endpoints.get_current_user_with_zotero')
    @patch('api.zotero_annotation_sync_endpoints.get_db')
    def test_sync_annotations_success(
        self, mock_get_db, mock_get_user, mock_service_class,
        mock_annotation_sync_service, mock_current_user, mock_db_session, sample_sync_response
    ):
        """Test successful annotation synchronization"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_get_user.return_value = mock_current_user
        mock_service_class.return_value = mock_annotation_sync_service
        mock_annotation_sync_service.sync_annotations_for_attachment.return_value = sample_sync_response
        
        # Create test client
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Test request
        response = client.post("/api/zotero/annotations/sync", json={
            "attachment_id": "attachment-123",
            "sync_direction": "bidirectional"
        })
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['attachment_id'] == "attachment-123"
        assert data['sync_direction'] == "bidirectional"
        assert data['annotations_imported'] == 2
        assert data['annotations_exported'] == 1
        assert data['annotations_updated'] == 1
        assert data['conflicts_detected'] == 0
        assert len(data['errors']) == 0
        assert 'sync_completed_at' in data
    
    @patch('api.zotero_annotation_sync_endpoints.ZoteroAnnotationSyncService')
    @patch('api.zotero_annotation_sync_endpoints.get_current_user_with_zotero')
    @patch('api.zotero_annotation_sync_endpoints.get_db')
    def test_sync_annotations_invalid_direction(
        self, mock_get_db, mock_get_user, mock_service_class,
        mock_current_user, mock_db_session
    ):
        """Test sync with invalid direction"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_get_user.return_value = mock_current_user
        mock_service_class.return_value = Mock()
        
        # Create test client
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Test request with invalid direction
        response = client.post("/api/zotero/annotations/sync", json={
            "attachment_id": "attachment-123",
            "sync_direction": "invalid_direction"
        })
        
        # Verify error response
        assert response.status_code == 400
        assert "Invalid sync direction" in response.json()['detail']
    
    @patch('api.zotero_annotation_sync_endpoints.ZoteroAnnotationSyncService')
    @patch('api.zotero_annotation_sync_endpoints.get_current_user_with_zotero')
    @patch('api.zotero_annotation_sync_endpoints.get_db')
    def test_sync_annotations_attachment_not_found(
        self, mock_get_db, mock_get_user, mock_service_class,
        mock_annotation_sync_service, mock_current_user, mock_db_session
    ):
        """Test sync with non-existent attachment"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_get_user.return_value = mock_current_user
        mock_service_class.return_value = mock_annotation_sync_service
        mock_annotation_sync_service.sync_annotations_for_attachment.side_effect = ValueError(
            "Attachment attachment-123 not found"
        )
        
        # Create test client
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Test request
        response = client.post("/api/zotero/annotations/sync", json={
            "attachment_id": "attachment-123",
            "sync_direction": "bidirectional"
        })
        
        # Verify error response
        assert response.status_code == 404
        assert "Attachment attachment-123 not found" in response.json()['detail']
    
    @patch('api.zotero_annotation_sync_endpoints.ZoteroAnnotationSyncService')
    @patch('api.zotero_annotation_sync_endpoints.get_current_user_with_zotero')
    @patch('api.zotero_annotation_sync_endpoints.get_db')
    def test_create_annotation_collaboration_success(
        self, mock_get_db, mock_get_user, mock_service_class,
        mock_annotation_sync_service, mock_current_user, mock_db_session, sample_collaboration
    ):
        """Test successful annotation collaboration creation"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_get_user.return_value = mock_current_user
        mock_service_class.return_value = mock_annotation_sync_service
        mock_annotation_sync_service.create_annotation_collaboration.return_value = sample_collaboration
        
        # Create test client
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Test request
        response = client.post("/api/zotero/annotations/collaborate", json={
            "annotation_id": "annotation-123",
            "collaboration_type": "comment",
            "content": "This is a comment"
        })
        
        # Verify response
        assert response.status_code == 200
        # Note: In a real test, we'd need to mock the Pydantic response model
        # For now, we just verify the service was called correctly
        mock_annotation_sync_service.create_annotation_collaboration.assert_called_once_with(
            annotation_id="annotation-123",
            user_id="user-123",
            collaboration_type="comment",
            content="This is a comment",
            parent_collaboration_id=None
        )
    
    @patch('api.zotero_annotation_sync_endpoints.ZoteroAnnotationSyncService')
    @patch('api.zotero_annotation_sync_endpoints.get_current_user_with_zotero')
    @patch('api.zotero_annotation_sync_endpoints.get_db')
    def test_create_annotation_collaboration_invalid_type(
        self, mock_get_db, mock_get_user, mock_service_class,
        mock_current_user, mock_db_session
    ):
        """Test collaboration creation with invalid type"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_get_user.return_value = mock_current_user
        mock_service_class.return_value = Mock()
        
        # Create test client
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Test request with invalid collaboration type
        response = client.post("/api/zotero/annotations/collaborate", json={
            "annotation_id": "annotation-123",
            "collaboration_type": "invalid_type",
            "content": "This is a comment"
        })
        
        # Verify error response
        assert response.status_code == 400
        assert "Invalid collaboration type" in response.json()['detail']
    
    @patch('api.zotero_annotation_sync_endpoints.ZoteroAnnotationSyncService')
    @patch('api.zotero_annotation_sync_endpoints.get_current_user_with_zotero')
    @patch('api.zotero_annotation_sync_endpoints.get_db')
    def test_share_annotation_success(
        self, mock_get_db, mock_get_user, mock_service_class,
        mock_annotation_sync_service, mock_current_user, mock_db_session, sample_share
    ):
        """Test successful annotation sharing"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_get_user.return_value = mock_current_user
        mock_service_class.return_value = mock_annotation_sync_service
        mock_annotation_sync_service.share_annotation.return_value = sample_share
        
        # Create test client
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Test request
        response = client.post("/api/zotero/annotations/share", json={
            "annotation_id": "annotation-123",
            "shared_with_user_id": "user-456",
            "permission_level": "read",
            "share_message": "Check this out"
        })
        
        # Verify response
        assert response.status_code == 200
        mock_annotation_sync_service.share_annotation.assert_called_once_with(
            annotation_id="annotation-123",
            owner_user_id="user-123",
            shared_with_user_id="user-456",
            permission_level="read",
            share_message="Check this out"
        )
    
    @patch('api.zotero_annotation_sync_endpoints.ZoteroAnnotationSyncService')
    @patch('api.zotero_annotation_sync_endpoints.get_current_user_with_zotero')
    @patch('api.zotero_annotation_sync_endpoints.get_db')
    def test_share_annotation_invalid_permission(
        self, mock_get_db, mock_get_user, mock_service_class,
        mock_current_user, mock_db_session
    ):
        """Test sharing with invalid permission level"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_get_user.return_value = mock_current_user
        mock_service_class.return_value = Mock()
        
        # Create test client
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Test request with invalid permission level
        response = client.post("/api/zotero/annotations/share", json={
            "annotation_id": "annotation-123",
            "shared_with_user_id": "user-456",
            "permission_level": "invalid_permission"
        })
        
        # Verify error response
        assert response.status_code == 400
        assert "Invalid permission level" in response.json()['detail']
    
    @patch('api.zotero_annotation_sync_endpoints.ZoteroAnnotationSyncService')
    @patch('api.zotero_annotation_sync_endpoints.get_current_user_with_zotero')
    @patch('api.zotero_annotation_sync_endpoints.get_db')
    def test_get_annotation_collaborations(
        self, mock_get_db, mock_get_user, mock_service_class,
        mock_annotation_sync_service, mock_current_user, mock_db_session, sample_collaboration
    ):
        """Test getting annotation collaborations"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_get_user.return_value = mock_current_user
        mock_service_class.return_value = mock_annotation_sync_service
        mock_annotation_sync_service.get_annotation_collaborations.return_value = [sample_collaboration]
        
        # Create test client
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Test request
        response = client.get("/api/zotero/annotations/collaborations/annotation-123")
        
        # Verify response
        assert response.status_code == 200
        mock_annotation_sync_service.get_annotation_collaborations.assert_called_once_with(
            annotation_id="annotation-123",
            user_id=None
        )
    
    @patch('api.zotero_annotation_sync_endpoints.ZoteroAnnotationSyncService')
    @patch('api.zotero_annotation_sync_endpoints.get_current_user_with_zotero')
    @patch('api.zotero_annotation_sync_endpoints.get_db')
    def test_get_annotation_history(
        self, mock_get_db, mock_get_user, mock_service_class,
        mock_annotation_sync_service, mock_current_user, mock_db_session
    ):
        """Test getting annotation history"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_get_user.return_value = mock_current_user
        mock_service_class.return_value = mock_annotation_sync_service
        mock_annotation_sync_service.get_annotation_history.return_value = []
        
        # Create test client
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Test request
        response = client.get("/api/zotero/annotations/history/annotation-123?limit=25")
        
        # Verify response
        assert response.status_code == 200
        mock_annotation_sync_service.get_annotation_history.assert_called_once_with(
            annotation_id="annotation-123",
            limit=25
        )
    
    @patch('api.zotero_annotation_sync_endpoints.ZoteroAnnotationSyncService')
    @patch('api.zotero_annotation_sync_endpoints.get_current_user_with_zotero')
    @patch('api.zotero_annotation_sync_endpoints.get_db')
    def test_get_shared_annotations(
        self, mock_get_db, mock_get_user, mock_service_class,
        mock_annotation_sync_service, mock_current_user, mock_db_session
    ):
        """Test getting shared annotations"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_get_user.return_value = mock_current_user
        mock_service_class.return_value = mock_annotation_sync_service
        
        # Mock shared annotation data
        mock_annotation = Mock()
        mock_attachment = Mock()
        mock_attachment.title = "Sample PDF"
        mock_item = Mock()
        mock_item.title = "Sample Paper"
        mock_attachment.item = mock_item
        mock_annotation.attachment = mock_attachment
        
        mock_annotation_sync_service.get_shared_annotations.return_value = [{
            'share': sample_share,
            'annotation': mock_annotation,
            'attachment': mock_attachment
        }]
        
        # Create test client
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Test request
        response = client.get("/api/zotero/annotations/shared")
        
        # Verify response
        assert response.status_code == 200
        mock_annotation_sync_service.get_shared_annotations.assert_called_once_with(
            user_id="user-123",
            permission_level=None
        )
    
    @patch('api.zotero_annotation_sync_endpoints.get_current_user_with_zotero')
    @patch('api.zotero_annotation_sync_endpoints.get_db')
    def test_revoke_annotation_share_success(
        self, mock_get_db, mock_get_user, mock_current_user, mock_db_session, sample_share
    ):
        """Test successful annotation share revocation"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_get_user.return_value = mock_current_user
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_share
        mock_db_session.commit = Mock()
        
        # Create test client
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Test request
        response = client.delete("/api/zotero/annotations/share/share-123")
        
        # Verify response
        assert response.status_code == 200
        assert response.json()['message'] == "Annotation share revoked successfully"
        assert sample_share.is_active is False
        mock_db_session.commit.assert_called_once()
    
    @patch('api.zotero_annotation_sync_endpoints.get_current_user_with_zotero')
    @patch('api.zotero_annotation_sync_endpoints.get_db')
    def test_revoke_annotation_share_not_found(
        self, mock_get_db, mock_get_user, mock_current_user, mock_db_session
    ):
        """Test revoking non-existent share"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_get_user.return_value = mock_current_user
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Create test client
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Test request
        response = client.delete("/api/zotero/annotations/share/nonexistent-share")
        
        # Verify error response
        assert response.status_code == 404
        assert "Annotation share not found" in response.json()['detail']
    
    @patch('api.zotero_annotation_sync_endpoints.get_current_user_with_zotero')
    @patch('api.zotero_annotation_sync_endpoints.get_db')
    def test_revoke_annotation_share_forbidden(
        self, mock_get_db, mock_get_user, mock_current_user, mock_db_session
    ):
        """Test revoking share without permission"""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        mock_get_user.return_value = mock_current_user
        
        # Create share owned by different user
        other_user_share = Mock(spec=ZoteroAnnotationShare)
        other_user_share.owner_user_id = "other-user-456"
        mock_db_session.query.return_value.filter.return_value.first.return_value = other_user_share
        
        # Create test client
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Test request
        response = client.delete("/api/zotero/annotations/share/share-123")
        
        # Verify error response
        assert response.status_code == 403
        assert "You can only revoke your own annotation shares" in response.json()['detail']


class TestAnnotationSyncValidation:
    """Test input validation for annotation sync endpoints"""
    
    def test_sync_request_validation(self):
        """Test sync request validation"""
        from api.zotero_annotation_sync_endpoints import AnnotationSyncRequest
        
        # Valid request
        valid_request = AnnotationSyncRequest(
            attachment_id="attachment-123",
            sync_direction="bidirectional"
        )
        assert valid_request.attachment_id == "attachment-123"
        assert valid_request.sync_direction == "bidirectional"
        
        # Test default sync direction
        default_request = AnnotationSyncRequest(attachment_id="attachment-123")
        assert default_request.sync_direction == "bidirectional"
    
    def test_collaboration_request_validation(self):
        """Test collaboration request validation"""
        from api.zotero_annotation_sync_endpoints import AnnotationCollaborationRequest
        
        # Valid request
        valid_request = AnnotationCollaborationRequest(
            annotation_id="annotation-123",
            collaboration_type="comment",
            content="This is a comment"
        )
        assert valid_request.annotation_id == "annotation-123"
        assert valid_request.collaboration_type == "comment"
        assert valid_request.content == "This is a comment"
        assert valid_request.parent_collaboration_id is None
    
    def test_share_request_validation(self):
        """Test share request validation"""
        from api.zotero_annotation_sync_endpoints import AnnotationShareRequest
        
        # Valid request
        valid_request = AnnotationShareRequest(
            annotation_id="annotation-123",
            shared_with_user_id="user-456"
        )
        assert valid_request.annotation_id == "annotation-123"
        assert valid_request.shared_with_user_id == "user-456"
        assert valid_request.permission_level == "read"  # default
        assert valid_request.share_message is None