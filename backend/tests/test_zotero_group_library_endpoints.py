"""
Tests for Zotero Group Library API Endpoints
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

from api.zotero_group_library_endpoints import router
from services.zotero.zotero_group_library_service import ZoteroGroupLibraryService


@pytest.fixture
def mock_service():
    """Mock ZoteroGroupLibraryService"""
    return Mock(spec=ZoteroGroupLibraryService)


@pytest.fixture
def mock_current_user():
    """Mock current user"""
    return {"id": "user-123", "email": "test@example.com"}


@pytest.fixture
def sample_group_library():
    """Sample group library data"""
    return {
        'id': 'lib-123',
        'zotero_library_id': '12345',
        'name': 'Research Group',
        'description': 'A collaborative research group',
        'is_public': True,
        'member_count': 5,
        'user_role': 'owner',
        'user_permissions': {'admin': True, 'manage_members': True},
        'sync_enabled': True,
        'last_sync_at': None,
        'created_at': '2024-01-01T00:00:00Z'
    }


@pytest.fixture
def sample_group_member():
    """Sample group member data"""
    return {
        'id': 'member-123',
        'user_id': 'user-456',
        'zotero_user_id': '67890',
        'role': 'member',
        'permissions': {'read': True, 'write': True},
        'join_date': '2024-01-01T00:00:00Z',
        'last_activity': None,
        'invitation_status': 'active'
    }


class TestZoteroGroupLibraryEndpoints:
    """Test cases for Zotero Group Library API endpoints"""
    
    @patch('api.zotero_group_library_endpoints.ZoteroGroupLibraryService')
    @patch('api.zotero_group_library_endpoints.get_current_user')
    @patch('api.zotero_group_library_endpoints.get_db')
    def test_import_group_libraries_success(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test successful group libraries import"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.import_group_libraries = AsyncMock(return_value={
            'imported_count': 2,
            'libraries': ['lib-123', 'lib-456'],
            'errors': []
        })
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post("/api/zotero/groups/import?connection_id=conn-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['imported_count'] == 2
        mock_service.import_group_libraries.assert_called_once_with('conn-123', 'user-123')
    
    @patch('api.zotero_group_library_endpoints.ZoteroGroupLibraryService')
    @patch('api.zotero_group_library_endpoints.get_current_user')
    @patch('api.zotero_group_library_endpoints.get_db')
    def test_import_group_libraries_error(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test group libraries import with error"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.import_group_libraries = AsyncMock(side_effect=Exception("Import failed"))
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post("/api/zotero/groups/import?connection_id=conn-123")
        
        assert response.status_code == 500
        assert "Import failed" in response.json()['detail']
    
    @patch('api.zotero_group_library_endpoints.ZoteroGroupLibraryService')
    @patch('api.zotero_group_library_endpoints.get_current_user')
    @patch('api.zotero_group_library_endpoints.get_db')
    def test_get_user_group_libraries(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user, sample_group_library):
        """Test getting user's group libraries"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.get_user_group_libraries = AsyncMock(return_value=[sample_group_library])
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.get("/api/zotero/groups/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['id'] == 'lib-123'
        assert data[0]['name'] == 'Research Group'
        mock_service.get_user_group_libraries.assert_called_once_with('user-123')
    
    @patch('api.zotero_group_library_endpoints.ZoteroGroupLibraryService')
    @patch('api.zotero_group_library_endpoints.get_current_user')
    @patch('api.zotero_group_library_endpoints.get_db')
    def test_get_group_members_success(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user, sample_group_member):
        """Test getting group members successfully"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.get_group_members = AsyncMock(return_value=[sample_group_member])
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.get("/api/zotero/groups/lib-123/members")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['id'] == 'member-123'
        assert data[0]['role'] == 'member'
        mock_service.get_group_members.assert_called_once_with('lib-123', 'user-123')
    
    @patch('api.zotero_group_library_endpoints.ZoteroGroupLibraryService')
    @patch('api.zotero_group_library_endpoints.get_current_user')
    @patch('api.zotero_group_library_endpoints.get_db')
    def test_get_group_members_permission_denied(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test getting group members without permission"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.get_group_members = AsyncMock(side_effect=PermissionError("Access denied"))
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.get("/api/zotero/groups/lib-123/members")
        
        assert response.status_code == 403
        assert "Access denied" in response.json()['detail']
    
    @patch('api.zotero_group_library_endpoints.ZoteroGroupLibraryService')
    @patch('api.zotero_group_library_endpoints.get_current_user')
    @patch('api.zotero_group_library_endpoints.get_db')
    def test_update_member_permissions_success(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test successful member permission update"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.update_member_permissions = AsyncMock(return_value={
            'member_id': 'member-123',
            'new_role': 'admin',
            'new_permissions': {'admin': True},
            'updated_at': datetime.utcnow()
        })
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        request_data = {
            'role': 'admin',
            'permissions': {'admin': True}
        }
        
        response = client.put("/api/zotero/groups/lib-123/members/member-123/permissions", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['new_role'] == 'admin'
        mock_service.update_member_permissions.assert_called_once_with(
            'lib-123', 'member-123', 'admin', {'admin': True}, 'user-123'
        )
    
    @patch('api.zotero_group_library_endpoints.ZoteroGroupLibraryService')
    @patch('api.zotero_group_library_endpoints.get_current_user')
    @patch('api.zotero_group_library_endpoints.get_db')
    def test_update_member_permissions_not_found(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test member permission update with non-existent member"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.update_member_permissions = AsyncMock(side_effect=ValueError("Member not found"))
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        request_data = {
            'role': 'admin',
            'permissions': {'admin': True}
        }
        
        response = client.put("/api/zotero/groups/lib-123/members/member-123/permissions", json=request_data)
        
        assert response.status_code == 404
        assert "Member not found" in response.json()['detail']
    
    @patch('api.zotero_group_library_endpoints.ZoteroGroupLibraryService')
    @patch('api.zotero_group_library_endpoints.get_current_user')
    @patch('api.zotero_group_library_endpoints.get_db')
    def test_get_group_sync_settings(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test getting group sync settings"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.get_group_sync_settings = AsyncMock(return_value={
            'sync_enabled': True,
            'sync_frequency_minutes': 60,
            'sync_collections': True,
            'sync_items': True,
            'sync_attachments': False,
            'sync_annotations': True,
            'auto_resolve_conflicts': True,
            'conflict_resolution_strategy': 'zotero_wins',
            'last_sync_at': None
        })
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.get("/api/zotero/groups/lib-123/sync-settings")
        
        assert response.status_code == 200
        data = response.json()
        assert data['sync_enabled'] is True
        assert data['sync_frequency_minutes'] == 60
        mock_service.get_group_sync_settings.assert_called_once_with('lib-123', 'user-123')
    
    @patch('api.zotero_group_library_endpoints.ZoteroGroupLibraryService')
    @patch('api.zotero_group_library_endpoints.get_current_user')
    @patch('api.zotero_group_library_endpoints.get_db')
    def test_update_group_sync_settings(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test updating group sync settings"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.update_group_sync_settings = AsyncMock(return_value={
            'sync_enabled': False,
            'sync_frequency_minutes': 120,
            'sync_collections': True,
            'sync_items': True,
            'sync_attachments': False,
            'sync_annotations': True,
            'auto_resolve_conflicts': True,
            'conflict_resolution_strategy': 'zotero_wins',
            'last_sync_at': None
        })
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        request_data = {
            'sync_enabled': False,
            'sync_frequency_minutes': 120
        }
        
        response = client.put("/api/zotero/groups/lib-123/sync-settings", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['sync_enabled'] is False
        assert data['sync_frequency_minutes'] == 120
        mock_service.update_group_sync_settings.assert_called_once_with(
            'lib-123', 'user-123', {'sync_enabled': False, 'sync_frequency_minutes': 120}
        )
    
    @patch('api.zotero_group_library_endpoints.ZoteroGroupLibraryService')
    @patch('api.zotero_group_library_endpoints.get_current_user')
    @patch('api.zotero_group_library_endpoints.get_db')
    def test_get_group_activity_log(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test getting group activity log"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.get_group_activity_log = AsyncMock(return_value=[
            {
                'id': 'activity-123',
                'user_id': 'user-123',
                'activity_type': 'member_added',
                'target_type': 'member',
                'target_id': 'member-123',
                'description': 'Added new member',
                'created_at': '2024-01-01T00:00:00Z'
            }
        ])
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.get("/api/zotero/groups/lib-123/activity?limit=50&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['id'] == 'activity-123'
        assert data[0]['activity_type'] == 'member_added'
        mock_service.get_group_activity_log.assert_called_once_with('lib-123', 'user-123', 50, 0)
    
    @patch('api.zotero_group_library_endpoints.ZoteroGroupLibraryService')
    @patch('api.zotero_group_library_endpoints.get_current_user')
    @patch('api.zotero_group_library_endpoints.get_db')
    def test_get_permission_templates(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test getting permission templates"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.get_permission_templates = AsyncMock(return_value=[
            {
                'id': 'template-123',
                'name': 'Owner',
                'description': 'Full control over group library',
                'permissions': {'admin': True, 'manage_members': True},
                'is_default': False
            }
        ])
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.get("/api/zotero/groups/permission-templates")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['name'] == 'Owner'
        assert data[0]['permissions']['admin'] is True
        mock_service.get_permission_templates.assert_called_once()
    
    @patch('api.zotero_group_library_endpoints.ZoteroGroupLibraryService')
    @patch('api.zotero_group_library_endpoints.get_current_user')
    @patch('api.zotero_group_library_endpoints.get_db')
    def test_sync_group_library_success(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test successful group library sync"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.sync_group_library = AsyncMock(return_value={
            'sync_initiated': True,
            'library_id': 'lib-123',
            'sync_type': 'manual_group_sync',
            'message': 'Group library sync initiated'
        })
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post("/api/zotero/groups/lib-123/sync")
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['sync_initiated'] is True
        mock_service.sync_group_library.assert_called_once_with('lib-123', 'user-123')
    
    @patch('api.zotero_group_library_endpoints.ZoteroGroupLibraryService')
    @patch('api.zotero_group_library_endpoints.get_current_user')
    @patch('api.zotero_group_library_endpoints.get_db')
    def test_sync_group_library_permission_denied(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test group library sync without permission"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.sync_group_library = AsyncMock(side_effect=PermissionError("Access denied"))
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post("/api/zotero/groups/lib-123/sync")
        
        assert response.status_code == 403
        assert "Access denied" in response.json()['detail']
    
    @patch('api.zotero_group_library_endpoints.ZoteroGroupLibraryService')
    @patch('api.zotero_group_library_endpoints.get_current_user')
    @patch('api.zotero_group_library_endpoints.get_db')
    def test_sync_group_library_sync_disabled(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test group library sync when disabled"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service.sync_group_library = AsyncMock(side_effect=ValueError("Sync is disabled"))
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post("/api/zotero/groups/lib-123/sync")
        
        assert response.status_code == 400
        assert "Sync is disabled" in response.json()['detail']
    
    @patch('api.zotero_group_library_endpoints.ZoteroGroupLibraryService')
    @patch('api.zotero_group_library_endpoints.get_current_user')
    @patch('api.zotero_group_library_endpoints.get_db')
    def test_check_user_permissions(self, mock_get_db, mock_get_current_user, mock_service_class, mock_current_user):
        """Test checking user permissions"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_service = Mock()
        mock_service._check_permission = AsyncMock(return_value=True)
        mock_service_class.return_value = mock_service
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.get("/api/zotero/groups/lib-123/permissions/check?permission=read")
        
        assert response.status_code == 200
        data = response.json()
        assert data['user_id'] == 'user-123'
        assert data['library_id'] == 'lib-123'
        assert data['permission'] == 'read'
        assert data['has_permission'] is True
        mock_service._check_permission.assert_called_once_with('lib-123', 'user-123', 'read')