"""
Tests for Zotero Group Library Service
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from services.zotero.zotero_group_library_service import ZoteroGroupLibraryService
from models.zotero_models import (
    ZoteroLibrary, ZoteroGroupMember, ZoteroGroupSyncSettings,
    ZoteroGroupPermissionTemplate, ZoteroGroupActivityLog,
    ZoteroGroupAccessControl, ZoteroConnection
)


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def group_library_service(mock_db):
    """Create ZoteroGroupLibraryService instance with mocked dependencies"""
    with patch('services.zotero.zotero_group_library_service.get_db') as mock_get_db:
        mock_get_db.return_value = mock_db
        service = ZoteroGroupLibraryService(mock_db)
        service.zotero_client = Mock()
        return service


@pytest.fixture
def sample_group_data():
    """Sample group data from Zotero API"""
    return {
        'id': 12345,
        'data': {
            'name': 'Research Group',
            'description': 'A collaborative research group',
            'url': 'https://www.zotero.org/groups/12345',
            'type': 'PublicOpen',
            'numMembers': 5,
            'libraryReading': {'read': True, 'write': True},
            'members': [
                {
                    'userID': 67890,
                    'role': 'owner',
                    'permissions': {'admin': True, 'manage_members': True}
                },
                {
                    'userID': 67891,
                    'role': 'member',
                    'permissions': {'read': True, 'write': True}
                }
            ]
        }
    }


@pytest.fixture
def sample_library():
    """Sample ZoteroLibrary instance"""
    return ZoteroLibrary(
        id='lib-123',
        connection_id='conn-123',
        zotero_library_id='12345',
        library_type='group',
        library_name='Research Group',
        group_description='A collaborative research group',
        is_public=True,
        member_count=5
    )


@pytest.fixture
def sample_group_member():
    """Sample ZoteroGroupMember instance"""
    return ZoteroGroupMember(
        id='member-123',
        library_id='lib-123',
        user_id='user-123',
        zotero_user_id='67890',
        member_role='owner',
        permissions={'admin': True, 'manage_members': True},
        is_active=True
    )


class TestZoteroGroupLibraryService:
    """Test cases for ZoteroGroupLibraryService"""
    
    @pytest.mark.asyncio
    async def test_import_group_libraries_success(self, group_library_service, mock_db, sample_group_data):
        """Test successful import of group libraries"""
        # Mock Zotero API response
        group_library_service.zotero_client.get_user_groups = AsyncMock(
            return_value=[sample_group_data]
        )
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Mock library creation
        mock_library = Mock()
        mock_library.id = 'lib-123'
        mock_db.add = Mock()
        
        result = await group_library_service.import_group_libraries('conn-123', 'user-123')
        
        assert result['imported_count'] == 1
        assert len(result['errors']) == 0
        group_library_service.zotero_client.get_user_groups.assert_called_once_with('conn-123')
    
    @pytest.mark.asyncio
    async def test_import_group_libraries_with_errors(self, group_library_service, mock_db):
        """Test import with some failures"""
        # Mock Zotero API response with invalid data
        invalid_group_data = {'id': 'invalid', 'data': {}}
        group_library_service.zotero_client.get_user_groups = AsyncMock(
            return_value=[invalid_group_data]
        )
        
        result = await group_library_service.import_group_libraries('conn-123', 'user-123')
        
        assert result['imported_count'] == 0
        assert len(result['errors']) == 1
        assert result['errors'][0]['group_id'] == 'invalid'
    
    @pytest.mark.asyncio
    async def test_get_user_group_libraries(self, group_library_service, mock_db, sample_library, sample_group_member):
        """Test getting user's group libraries"""
        # Mock database queries
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sample_library]
        
        # Mock member and sync settings queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_group_member,  # Member query
            Mock(sync_enabled=True)  # Sync settings query
        ]
        
        result = await group_library_service.get_user_group_libraries('user-123')
        
        assert len(result) == 1
        assert result[0]['id'] == 'lib-123'
        assert result[0]['name'] == 'Research Group'
        assert result[0]['user_role'] == 'owner'
    
    @pytest.mark.asyncio
    async def test_get_group_members_success(self, group_library_service, mock_db, sample_group_member):
        """Test getting group members with proper permissions"""
        # Mock permission check
        group_library_service._check_permission = AsyncMock(return_value=True)
        
        # Mock database query
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_group_member]
        
        result = await group_library_service.get_group_members('lib-123', 'user-123')
        
        assert len(result) == 1
        assert result[0]['id'] == 'member-123'
        assert result[0]['role'] == 'owner'
        group_library_service._check_permission.assert_called_once_with('lib-123', 'user-123', 'read')
    
    @pytest.mark.asyncio
    async def test_get_group_members_permission_denied(self, group_library_service, mock_db):
        """Test getting group members without proper permissions"""
        # Mock permission check to return False
        group_library_service._check_permission = AsyncMock(return_value=False)
        
        with pytest.raises(PermissionError, match="User does not have permission to view group members"):
            await group_library_service.get_group_members('lib-123', 'user-123')
    
    @pytest.mark.asyncio
    async def test_update_member_permissions_success(self, group_library_service, mock_db, sample_group_member):
        """Test successful member permission update"""
        # Mock permission check
        group_library_service._check_permission = AsyncMock(return_value=True)
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.return_value = sample_group_member
        mock_db.commit = Mock()
        
        # Mock activity logging
        group_library_service._log_group_activity = AsyncMock()
        
        result = await group_library_service.update_member_permissions(
            'lib-123', 'member-123', 'admin', {'admin': True}, 'user-123'
        )
        
        assert result['member_id'] == 'member-123'
        assert result['new_role'] == 'admin'
        assert sample_group_member.member_role == 'admin'
        group_library_service._log_group_activity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_member_permissions_no_permission(self, group_library_service, mock_db):
        """Test member permission update without proper permissions"""
        # Mock permission check to return False
        group_library_service._check_permission = AsyncMock(return_value=False)
        
        with pytest.raises(PermissionError, match="User does not have permission to manage group members"):
            await group_library_service.update_member_permissions(
                'lib-123', 'member-123', 'admin', {'admin': True}, 'user-123'
            )
    
    @pytest.mark.asyncio
    async def test_update_member_permissions_member_not_found(self, group_library_service, mock_db):
        """Test member permission update with non-existent member"""
        # Mock permission check
        group_library_service._check_permission = AsyncMock(return_value=True)
        
        # Mock database query to return None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Group member not found"):
            await group_library_service.update_member_permissions(
                'lib-123', 'member-123', 'admin', {'admin': True}, 'user-123'
            )
    
    @pytest.mark.asyncio
    async def test_get_group_sync_settings_existing(self, group_library_service, mock_db):
        """Test getting existing sync settings"""
        mock_settings = Mock()
        mock_settings.sync_enabled = True
        mock_settings.sync_frequency_minutes = 60
        mock_settings.sync_collections = True
        mock_settings.sync_items = True
        mock_settings.sync_attachments = False
        mock_settings.sync_annotations = True
        mock_settings.auto_resolve_conflicts = True
        mock_settings.conflict_resolution_strategy = 'zotero_wins'
        mock_settings.last_sync_at = None
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_settings
        
        result = await group_library_service.get_group_sync_settings('lib-123', 'user-123')
        
        assert result['sync_enabled'] is True
        assert result['sync_frequency_minutes'] == 60
        assert result['conflict_resolution_strategy'] == 'zotero_wins'
    
    @pytest.mark.asyncio
    async def test_get_group_sync_settings_create_default(self, group_library_service, mock_db):
        """Test creating default sync settings when none exist"""
        # First call returns None, second call returns created settings
        mock_settings = Mock()
        mock_settings.sync_enabled = True
        mock_settings.sync_frequency_minutes = 60
        mock_settings.sync_collections = True
        mock_settings.sync_items = True
        mock_settings.sync_attachments = False
        mock_settings.sync_annotations = True
        mock_settings.auto_resolve_conflicts = True
        mock_settings.conflict_resolution_strategy = 'zotero_wins'
        mock_settings.last_sync_at = None
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [None, mock_settings]
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        result = await group_library_service.get_group_sync_settings('lib-123', 'user-123')
        
        assert result['sync_enabled'] is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_group_sync_settings(self, group_library_service, mock_db):
        """Test updating sync settings"""
        mock_settings = Mock()
        mock_settings.sync_enabled = True
        mock_settings.sync_frequency_minutes = 60
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_settings
        mock_db.commit = Mock()
        
        # Mock the get_group_sync_settings call
        group_library_service.get_group_sync_settings = AsyncMock(
            return_value={'sync_enabled': False, 'sync_frequency_minutes': 120}
        )
        
        settings_data = {'sync_enabled': False, 'sync_frequency_minutes': 120}
        result = await group_library_service.update_group_sync_settings('lib-123', 'user-123', settings_data)
        
        assert result['sync_enabled'] is False
        assert result['sync_frequency_minutes'] == 120
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_group_activity_log(self, group_library_service, mock_db):
        """Test getting group activity log"""
        # Mock permission check
        group_library_service._check_permission = AsyncMock(return_value=True)
        
        # Mock activity log
        mock_activity = Mock()
        mock_activity.id = 'activity-123'
        mock_activity.user_id = 'user-123'
        mock_activity.activity_type = 'member_added'
        mock_activity.target_type = 'member'
        mock_activity.target_id = 'member-123'
        mock_activity.activity_description = 'Added new member'
        mock_activity.created_at = datetime.utcnow()
        
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = [mock_activity]
        
        result = await group_library_service.get_group_activity_log('lib-123', 'user-123', 50, 0)
        
        assert len(result) == 1
        assert result[0]['id'] == 'activity-123'
        assert result[0]['activity_type'] == 'member_added'
    
    @pytest.mark.asyncio
    async def test_check_permission_owner(self, group_library_service, mock_db):
        """Test permission check for owner role"""
        mock_member = Mock()
        mock_member.member_role = 'owner'
        mock_member.permissions = {}
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_member
        
        result = await group_library_service._check_permission('lib-123', 'user-123', 'manage_settings')
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_permission_member_read(self, group_library_service, mock_db):
        """Test permission check for member role with read permission"""
        mock_member = Mock()
        mock_member.member_role = 'member'
        mock_member.permissions = {}
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_member
        
        result = await group_library_service._check_permission('lib-123', 'user-123', 'read')
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_permission_member_admin_denied(self, group_library_service, mock_db):
        """Test permission check for member role without admin permission"""
        mock_member = Mock()
        mock_member.member_role = 'member'
        mock_member.permissions = {}
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_member
        
        result = await group_library_service._check_permission('lib-123', 'user-123', 'admin')
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_permission_no_member(self, group_library_service, mock_db):
        """Test permission check for non-member"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await group_library_service._check_permission('lib-123', 'user-123', 'read')
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_permission_templates(self, group_library_service, mock_db):
        """Test getting permission templates"""
        mock_template = Mock()
        mock_template.id = 'template-123'
        mock_template.template_name = 'Owner'
        mock_template.template_description = 'Full control'
        mock_template.permissions = {'admin': True}
        mock_template.is_default = False
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_template]
        
        result = await group_library_service.get_permission_templates()
        
        assert len(result) == 1
        assert result[0]['name'] == 'Owner'
        assert result[0]['permissions']['admin'] is True
    
    @pytest.mark.asyncio
    async def test_sync_group_library_success(self, group_library_service, mock_db):
        """Test successful group library sync"""
        # Mock permission check
        group_library_service._check_permission = AsyncMock(return_value=True)
        
        # Mock sync settings
        group_library_service.get_group_sync_settings = AsyncMock(
            return_value={'sync_enabled': True}
        )
        
        result = await group_library_service.sync_group_library('lib-123', 'user-123')
        
        assert result['sync_initiated'] is True
        assert result['library_id'] == 'lib-123'
        assert result['sync_type'] == 'manual_group_sync'
    
    @pytest.mark.asyncio
    async def test_sync_group_library_no_permission(self, group_library_service, mock_db):
        """Test group library sync without permission"""
        # Mock permission check to return False
        group_library_service._check_permission = AsyncMock(return_value=False)
        
        with pytest.raises(PermissionError, match="User does not have permission to sync this group library"):
            await group_library_service.sync_group_library('lib-123', 'user-123')
    
    @pytest.mark.asyncio
    async def test_sync_group_library_sync_disabled(self, group_library_service, mock_db):
        """Test group library sync when sync is disabled"""
        # Mock permission check
        group_library_service._check_permission = AsyncMock(return_value=True)
        
        # Mock sync settings with sync disabled
        group_library_service.get_group_sync_settings = AsyncMock(
            return_value={'sync_enabled': False}
        )
        
        with pytest.raises(ValueError, match="Sync is disabled for this group library"):
            await group_library_service.sync_group_library('lib-123', 'user-123')
    
    @pytest.mark.asyncio
    async def test_log_group_activity(self, group_library_service, mock_db):
        """Test logging group activity"""
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        await group_library_service._log_group_activity(
            'lib-123', 'user-123', 'member_added', 'member', 'member-123',
            'Added new member', {'old': 'data'}, {'new': 'data'}
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verify the activity log object was created with correct data
        call_args = mock_db.add.call_args[0][0]
        assert call_args.library_id == 'lib-123'
        assert call_args.user_id == 'user-123'
        assert call_args.activity_type == 'member_added'