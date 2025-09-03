"""
Tests for Zotero Reference Sharing API Endpoints
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

from api.zotero_reference_sharing_endpoints import router
from services.zotero.zotero_reference_sharing_service import ZoteroReferenceSharingService


@pytest.fixture
def mock_service():
    """Mock ZoteroReferenceSharingService"""
    return Mock(spec=ZoteroReferenceSharingService)


@pytest.fixture
def mock_current_user():
    """Mock current user"""
    return {"id": "user-123", "email": "test@example.com"}


@pytest.fixture
def sample_shared_reference():
    """Sample shared reference data"""
    return {
        'share_id': 'share-123',
        'reference_id': 'ref-123',
        'reference_title': 'Sample Research Paper',
        'reference_authors': [{'firstName': 'John', 'lastName': 'Doe', 'creatorType': 'author'}],
        'reference_year': 2024,
        'owner_user_id': 'user-123',
        'shared_with_user_id': 'user-456',
        'permission_level': 'read',
        'share_message': 'Check this out!',
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z'
    }


@pytest.fixture
def sample_collection():
    """Sample collection data"""
    return {
        'collection_id': 'collection-123',
        'name': 'Research Project',
        'description': 'A collaborative research project',
        'collection_type': 'research_project',
        'owner_user_id': 'user-123',
        'is_public': False,
        'visibility': 'private',
        'user_role': 'owner',
        'user_permission_level': 'admin',
        'reference_count': 5,
        'collaborator_count': 3,
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z'
    }


class TestZoteroReferenceSharingEndpoints:
    """Test cases for Zotero Reference Sharing API endpoints"""
    
    @patch('api.zotero_reference_sharing_endpoints.ZoteroReferenceSharingService')
    @patch('api.zotero_reference_sharing_endpoints.get_current_user')
    @patch('api.zotero_reference_sharing_endpoints.get_db')
    def test_share_reference_success(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test successful reference sharing"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.share_reference_with_user = AsyncMock(return_value={
            'share_id': 'share-123',
            'reference_id': 'ref-123',
            'shared_with_user_id': 'user-456',
            'permission_level': 'read',
            'action': 'created'
        })
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        request_data = {
            'reference_id': 'ref-123',
            'shared_with_user_id': 'user-456',
            'permission_level': 'read',
            'share_message': 'Check this out!'
        }
        
        response = client.post("/api/zotero/sharing/references/share", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['share_id'] == 'share-123'
        mock_service.share_reference_with_user.assert_called_once_with(
            'ref-123', 'user-123', 'user-456', 'read', 'Check this out!', {}
        )
    
    @patch('api.zotero_reference_sharing_endpoints.ZoteroReferenceSharingService')
    @patch('api.zotero_reference_sharing_endpoints.get_current_user')
    @patch('api.zotero_reference_sharing_endpoints.get_db')
    def test_share_reference_not_found(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test sharing non-existent reference"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.share_reference_with_user = AsyncMock(side_effect=ValueError("Reference not found"))
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        request_data = {
            'reference_id': 'ref-123',
            'shared_with_user_id': 'user-456',
            'permission_level': 'read'
        }
        
        response = client.post("/api/zotero/sharing/references/share", json=request_data)
        
        assert response.status_code == 404
        assert "Reference not found" in response.json()['detail']
    
    @patch('api.zotero_reference_sharing_endpoints.ZoteroReferenceSharingService')
    @patch('api.zotero_reference_sharing_endpoints.get_current_user')
    @patch('api.zotero_reference_sharing_endpoints.get_db')
    def test_get_shared_references(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user, sample_shared_reference):
        """Test getting shared references"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.get_shared_references = AsyncMock(return_value=[sample_shared_reference])
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.get("/api/zotero/sharing/references/shared?as_owner=true")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['share_id'] == 'share-123'
        assert data[0]['reference_title'] == 'Sample Research Paper'
        mock_service.get_shared_references.assert_called_once_with('user-123', True)
    
    @patch('api.zotero_reference_sharing_endpoints.ZoteroReferenceSharingService')
    @patch('api.zotero_reference_sharing_endpoints.get_current_user')
    @patch('api.zotero_reference_sharing_endpoints.get_db')
    def test_create_shared_collection(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test creating a shared collection"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.create_shared_collection = AsyncMock(return_value={
            'collection_id': 'collection-123',
            'name': 'Research Project',
            'access_code': None,
            'is_public': False,
            'created_at': datetime.utcnow()
        })
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        request_data = {
            'name': 'Research Project',
            'description': 'A collaborative project',
            'collection_type': 'research_project',
            'is_public': False
        }
        
        response = client.post("/api/zotero/sharing/collections", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['collection_id'] == 'collection-123'
        mock_service.create_shared_collection.assert_called_once_with(
            'Research Project', 'user-123', 'A collaborative project', 'research_project', False, {}
        )
    
    @patch('api.zotero_reference_sharing_endpoints.ZoteroReferenceSharingService')
    @patch('api.zotero_reference_sharing_endpoints.get_current_user')
    @patch('api.zotero_reference_sharing_endpoints.get_db')
    def test_get_user_collections(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user, sample_collection):
        """Test getting user collections"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.get_user_collections = AsyncMock(return_value=[sample_collection])
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.get("/api/zotero/sharing/collections")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['collection_id'] == 'collection-123'
        assert data[0]['name'] == 'Research Project'
        mock_service.get_user_collections.assert_called_once_with('user-123')
    
    @patch('api.zotero_reference_sharing_endpoints.ZoteroReferenceSharingService')
    @patch('api.zotero_reference_sharing_endpoints.get_current_user')
    @patch('api.zotero_reference_sharing_endpoints.get_db')
    def test_add_collaborator_success(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test successfully adding a collaborator"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.add_collaborator_to_collection = AsyncMock(return_value={
            'collaborator_id': 'collaborator-456',
            'collection_id': 'collection-123',
            'user_id': 'user-456',
            'permission_level': 'read',
            'role': 'collaborator',
            'invitation_status': 'pending'
        })
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        request_data = {
            'user_id': 'user-456',
            'permission_level': 'read',
            'role': 'collaborator',
            'invitation_message': 'Welcome!'
        }
        
        response = client.post("/api/zotero/sharing/collections/collection-123/collaborators", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['collaborator_id'] == 'collaborator-456'
        mock_service.add_collaborator_to_collection.assert_called_once_with(
            'collection-123', 'user-456', 'user-123', 'read', 'collaborator', 'Welcome!'
        )
    
    @patch('api.zotero_reference_sharing_endpoints.ZoteroReferenceSharingService')
    @patch('api.zotero_reference_sharing_endpoints.get_current_user')
    @patch('api.zotero_reference_sharing_endpoints.get_db')
    def test_add_collaborator_permission_denied(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test adding collaborator without permission"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.add_collaborator_to_collection = AsyncMock(side_effect=PermissionError("Access denied"))
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        request_data = {
            'user_id': 'user-456',
            'permission_level': 'read'
        }
        
        response = client.post("/api/zotero/sharing/collections/collection-123/collaborators", json=request_data)
        
        assert response.status_code == 403
        assert "Access denied" in response.json()['detail']
    
    @patch('api.zotero_reference_sharing_endpoints.ZoteroReferenceSharingService')
    @patch('api.zotero_reference_sharing_endpoints.get_current_user')
    @patch('api.zotero_reference_sharing_endpoints.get_db')
    def test_add_reference_to_collection(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test adding reference to collection"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.add_reference_to_collection = AsyncMock(return_value={
            'collection_reference_id': 'collection-ref-123',
            'collection_id': 'collection-123',
            'reference_id': 'ref-123',
            'added_by': 'user-123',
            'added_at': datetime.utcnow()
        })
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        request_data = {
            'reference_id': 'ref-123',
            'notes': 'Important paper',
            'tags': ['research'],
            'is_featured': True
        }
        
        response = client.post("/api/zotero/sharing/collections/collection-123/references", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['collection_reference_id'] == 'collection-ref-123'
        mock_service.add_reference_to_collection.assert_called_once_with(
            'collection-123', 'ref-123', 'user-123', 'Important paper', ['research'], True
        )
    
    @patch('api.zotero_reference_sharing_endpoints.ZoteroReferenceSharingService')
    @patch('api.zotero_reference_sharing_endpoints.get_current_user')
    @patch('api.zotero_reference_sharing_endpoints.get_db')
    def test_get_collection_references(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test getting collection references"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.get_collection_references = AsyncMock(return_value=[
            {
                'collection_reference_id': 'collection-ref-123',
                'reference_id': 'ref-123',
                'reference_title': 'Sample Paper',
                'reference_authors': [{'firstName': 'John', 'lastName': 'Doe'}],
                'reference_year': 2024,
                'reference_doi': '10.1000/test',
                'added_by': 'user-123',
                'added_at': '2024-01-01T00:00:00Z',
                'notes': 'Important',
                'tags': ['research'],
                'is_featured': True,
                'sort_order': 1
            }
        ])
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.get("/api/zotero/sharing/collections/collection-123/references?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['collection_reference_id'] == 'collection-ref-123'
        assert data[0]['reference_title'] == 'Sample Paper'
        mock_service.get_collection_references.assert_called_once_with('collection-123', 'user-123', 10, 0)
    
    @patch('api.zotero_reference_sharing_endpoints.ZoteroReferenceSharingService')
    @patch('api.zotero_reference_sharing_endpoints.get_current_user')
    @patch('api.zotero_reference_sharing_endpoints.get_db')
    def test_add_reference_discussion(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test adding reference discussion"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.add_reference_discussion = AsyncMock(return_value={
            'discussion_id': 'discussion-123',
            'reference_id': 'ref-123',
            'user_id': 'user-123',
            'discussion_type': 'comment',
            'content': 'Great paper!',
            'created_at': datetime.utcnow()
        })
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        request_data = {
            'content': 'Great paper!',
            'discussion_type': 'comment',
            'collection_id': 'collection-123'
        }
        
        response = client.post("/api/zotero/sharing/references/ref-123/discussions", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['discussion_id'] == 'discussion-123'
        mock_service.add_reference_discussion.assert_called_once_with(
            'ref-123', 'user-123', 'Great paper!', 'comment', 'collection-123', None
        )
    
    @patch('api.zotero_reference_sharing_endpoints.ZoteroReferenceSharingService')
    @patch('api.zotero_reference_sharing_endpoints.get_current_user')
    @patch('api.zotero_reference_sharing_endpoints.get_db')
    def test_get_reference_discussions(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test getting reference discussions"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.get_reference_discussions = AsyncMock(return_value=[
            {
                'discussion_id': 'discussion-123',
                'reference_id': 'ref-123',
                'collection_id': 'collection-123',
                'user_id': 'user-123',
                'discussion_type': 'comment',
                'content': 'Great paper!',
                'parent_discussion_id': None,
                'is_resolved': False,
                'resolved_by': None,
                'resolved_at': None,
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            }
        ])
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.get("/api/zotero/sharing/references/ref-123/discussions?collection_id=collection-123")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['discussion_id'] == 'discussion-123'
        assert data[0]['content'] == 'Great paper!'
        mock_service.get_reference_discussions.assert_called_once_with('ref-123', 'user-123', 'collection-123')
    
    @patch('api.zotero_reference_sharing_endpoints.ZoteroReferenceSharingService')
    @patch('api.zotero_reference_sharing_endpoints.get_current_user')
    @patch('api.zotero_reference_sharing_endpoints.get_db')
    def test_get_user_notifications(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test getting user notifications"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.get_user_notifications = AsyncMock(return_value=[
            {
                'notification_id': 'notification-123',
                'notification_type': 'reference_shared',
                'title': 'Reference shared',
                'message': 'A reference was shared with you',
                'target_type': 'reference',
                'target_id': 'ref-123',
                'sender_user_id': 'user-456',
                'is_read': False,
                'is_dismissed': False,
                'action_url': '/references/ref-123',
                'created_at': '2024-01-01T00:00:00Z',
                'read_at': None
            }
        ])
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.get("/api/zotero/sharing/notifications?unread_only=true&limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['notification_id'] == 'notification-123'
        assert data[0]['notification_type'] == 'reference_shared'
        mock_service.get_user_notifications.assert_called_once_with('user-123', True, 10, 0)
    
    @patch('api.zotero_reference_sharing_endpoints.ZoteroReferenceSharingService')
    @patch('api.zotero_reference_sharing_endpoints.get_current_user')
    @patch('api.zotero_reference_sharing_endpoints.get_db')
    def test_mark_notification_as_read_success(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test successfully marking notification as read"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.mark_notification_as_read = AsyncMock(return_value=True)
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.put("/api/zotero/sharing/notifications/notification-123/read")
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Notification marked as read'
        mock_service.mark_notification_as_read.assert_called_once_with('notification-123', 'user-123')
    
    @patch('api.zotero_reference_sharing_endpoints.ZoteroReferenceSharingService')
    @patch('api.zotero_reference_sharing_endpoints.get_current_user')
    @patch('api.zotero_reference_sharing_endpoints.get_db')
    def test_mark_notification_as_read_not_found(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test marking non-existent notification as read"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.mark_notification_as_read = AsyncMock(return_value=False)
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.put("/api/zotero/sharing/notifications/notification-123/read")
        
        assert response.status_code == 404
        assert "Notification not found" in response.json()['detail']