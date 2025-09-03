"""
Tests for Zotero Team Collaboration Service
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from services.zotero.zotero_team_collaboration_service import ZoteroTeamCollaborationService
from models.zotero_models import (
    ZoteroTeamWorkspace, ZoteroTeamWorkspaceMember, ZoteroTeamWorkspaceCollection,
    ZoteroModificationTracking, ZoteroCollaborativeEditingSession,
    ZoteroCollaborationConflict, ZoteroSharedReferenceCollection
)


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def team_collaboration_service(mock_db):
    """Create ZoteroTeamCollaborationService instance with mocked dependencies"""
    with patch('services.zotero.zotero_team_collaboration_service.get_db') as mock_get_db:
        mock_get_db.return_value = mock_db
        return ZoteroTeamCollaborationService(mock_db)


@pytest.fixture
def sample_workspace():
    """Sample ZoteroTeamWorkspace instance"""
    return ZoteroTeamWorkspace(
        id='workspace-123',
        name='Research Team',
        description='A collaborative research workspace',
        owner_user_id='user-123',
        workspace_type='research_team',
        is_active=True
    )


@pytest.fixture
def sample_workspace_member():
    """Sample ZoteroTeamWorkspaceMember instance"""
    return ZoteroTeamWorkspaceMember(
        id='member-123',
        workspace_id='workspace-123',
        user_id='user-123',
        role='owner',
        permissions={'admin': True, 'manage_members': True},
        is_active=True,
        invitation_status='active'
    )


@pytest.fixture
def sample_collection():
    """Sample ZoteroSharedReferenceCollection instance"""
    return ZoteroSharedReferenceCollection(
        id='collection-123',
        name='Research Papers',
        description='Collection of research papers',
        owner_user_id='user-123'
    )


class TestZoteroTeamCollaborationService:
    """Test cases for ZoteroTeamCollaborationService"""
    
    @pytest.mark.asyncio
    async def test_create_team_workspace(self, team_collaboration_service, mock_db):
        """Test creating a team workspace"""
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Mock the workspace and member objects
        mock_workspace = Mock()
        mock_workspace.id = 'workspace-123'
        mock_workspace.created_at = datetime.utcnow()
        
        mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 'workspace-123')
        
        # Mock initialization methods
        team_collaboration_service._initialize_workspace_settings = AsyncMock()
        team_collaboration_service._log_collaboration_history = AsyncMock()
        
        result = await team_collaboration_service.create_team_workspace(
            'Research Team', 'user-123', 'A collaborative workspace', 'research_team'
        )
        
        assert result['workspace_id'] == 'workspace-123'
        assert result['name'] == 'Research Team'
        assert result['workspace_type'] == 'research_team'
        
        # Should add workspace and owner member
        assert mock_db.add.call_count == 2
        mock_db.commit.assert_called()
        team_collaboration_service._initialize_workspace_settings.assert_called_once()
        team_collaboration_service._log_collaboration_history.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_workspaces(self, team_collaboration_service, mock_db, sample_workspace, sample_workspace_member):
        """Test getting user's workspaces"""
        # Mock membership
        mock_membership = Mock()
        mock_membership.workspace_id = 'workspace-123'
        mock_membership.role = 'owner'
        mock_membership.permissions = {'admin': True}
        mock_membership.last_activity = datetime.utcnow()
        
        # Mock database queries
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_membership]
        
        # Mock workspace and count queries
        mock_db.query.return_value.filter.return_value.first.return_value = sample_workspace
        mock_db.query.return_value.filter.return_value.count.side_effect = [3, 5]  # member_count, collection_count
        
        result = await team_collaboration_service.get_user_workspaces('user-123')
        
        assert len(result) == 1
        assert result[0]['workspace_id'] == 'workspace-123'
        assert result[0]['name'] == 'Research Team'
        assert result[0]['user_role'] == 'owner'
        assert result[0]['member_count'] == 3
        assert result[0]['collection_count'] == 5
    
    @pytest.mark.asyncio
    async def test_add_workspace_member_success(self, team_collaboration_service, mock_db, sample_workspace, sample_workspace_member):
        """Test successfully adding a workspace member"""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_workspace,  # Workspace exists
            sample_workspace_member,  # Inviter has permission
            None  # No existing member
        ]
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        mock_new_member = Mock()
        mock_new_member.id = 'member-456'
        mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 'member-456')
        
        # Mock activity logging and notification creation
        team_collaboration_service._log_collaboration_history = AsyncMock()
        team_collaboration_service._create_workspace_notification = AsyncMock()
        
        result = await team_collaboration_service.add_workspace_member(
            'workspace-123', 'user-456', 'user-123', 'member', {'read': True}
        )
        
        assert result['member_id'] == 'member-456'
        assert result['user_id'] == 'user-456'
        assert result['role'] == 'member'
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
        team_collaboration_service._log_collaboration_history.assert_called_once()
        team_collaboration_service._create_workspace_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_workspace_member_no_permission(self, team_collaboration_service, mock_db, sample_workspace):
        """Test adding workspace member without permission"""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_workspace,  # Workspace exists
            None  # Inviter has no permission
        ]
        
        with pytest.raises(PermissionError, match="User does not have permission to add members"):
            await team_collaboration_service.add_workspace_member(
                'workspace-123', 'user-456', 'user-789', 'member'
            )
    
    @pytest.mark.asyncio
    async def test_add_workspace_member_already_exists(self, team_collaboration_service, mock_db, sample_workspace, sample_workspace_member):
        """Test adding a user who is already a member"""
        # Mock existing active member
        existing_member = Mock()
        existing_member.is_active = True
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_workspace,  # Workspace exists
            sample_workspace_member,  # Inviter has permission
            existing_member  # User is already a member
        ]
        
        with pytest.raises(ValueError, match="User is already a member of this workspace"):
            await team_collaboration_service.add_workspace_member(
                'workspace-123', 'user-456', 'user-123', 'member'
            )
    
    @pytest.mark.asyncio
    async def test_add_collection_to_workspace_success(self, team_collaboration_service, mock_db, sample_workspace_member, sample_collection):
        """Test successfully adding a collection to workspace"""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_workspace_member,  # User has permission
            sample_collection,  # Collection exists
            None  # Collection not already in workspace
        ]
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        mock_workspace_collection = Mock()
        mock_workspace_collection.id = 'workspace-collection-123'
        mock_workspace_collection.added_at = datetime.utcnow()
        mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 'workspace-collection-123')
        
        # Mock activity logging
        team_collaboration_service._log_collaboration_history = AsyncMock()
        
        result = await team_collaboration_service.add_collection_to_workspace(
            'workspace-123', 'collection-123', 'user-123', 'shared', True
        )
        
        assert result['workspace_collection_id'] == 'workspace-collection-123'
        assert result['collection_id'] == 'collection-123'
        assert result['collection_role'] == 'shared'
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
        team_collaboration_service._log_collaboration_history.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_collection_to_workspace_no_permission(self, team_collaboration_service, mock_db):
        """Test adding collection without permission"""
        # Mock member with insufficient permissions
        mock_member = Mock()
        mock_member.role = 'viewer'
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_member
        
        with pytest.raises(PermissionError, match="User does not have permission to add collections"):
            await team_collaboration_service.add_collection_to_workspace(
                'workspace-123', 'collection-123', 'user-456', 'shared'
            )
    
    @pytest.mark.asyncio
    async def test_track_modification_no_conflict(self, team_collaboration_service, mock_db):
        """Test tracking a modification without conflicts"""
        # Mock latest modification query
        mock_latest_mod = Mock()
        mock_latest_mod.version_number = 5
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_latest_mod
        
        # Mock conflict detection
        team_collaboration_service._detect_modification_conflict = AsyncMock(return_value=False)
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        mock_modification = Mock()
        mock_modification.id = 'modification-123'
        mock_modification.created_at = datetime.utcnow()
        mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 'modification-123')
        
        # Mock activity logging
        team_collaboration_service._log_collaboration_history = AsyncMock()
        
        result = await team_collaboration_service.track_modification(
            'reference', 'ref-123', 'user-123', 'update',
            {'title': 'new title'}, {'title': 'old title'}, {'title': 'new title'},
            'workspace-123', None, 'Updated reference title'
        )
        
        assert result['modification_id'] == 'modification-123'
        assert result['version_number'] == 6
        assert result['is_conflict'] is False
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
        team_collaboration_service._log_collaboration_history.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_track_modification_with_conflict(self, team_collaboration_service, mock_db):
        """Test tracking a modification that causes a conflict"""
        # Mock latest modification query
        mock_latest_mod = Mock()
        mock_latest_mod.version_number = 3
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_latest_mod
        
        # Mock conflict detection
        team_collaboration_service._detect_modification_conflict = AsyncMock(return_value=True)
        team_collaboration_service._create_collaboration_conflict = AsyncMock()
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        mock_modification = Mock()
        mock_modification.id = 'modification-123'
        mock_modification.created_at = datetime.utcnow()
        mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 'modification-123')
        
        # Mock activity logging
        team_collaboration_service._log_collaboration_history = AsyncMock()
        
        result = await team_collaboration_service.track_modification(
            'reference', 'ref-123', 'user-123', 'update',
            {'title': 'new title'}, {'title': 'old title'}, {'title': 'new title'},
            'workspace-123'
        )
        
        assert result['is_conflict'] is True
        team_collaboration_service._create_collaboration_conflict.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_modification_history(self, team_collaboration_service, mock_db):
        """Test getting modification history"""
        # Mock modification
        mock_modification = Mock()
        mock_modification.id = 'modification-123'
        mock_modification.user_id = 'user-123'
        mock_modification.modification_type = 'update'
        mock_modification.field_changes = {'title': 'new title'}
        mock_modification.old_values = {'title': 'old title'}
        mock_modification.new_values = {'title': 'new title'}
        mock_modification.change_summary = 'Updated title'
        mock_modification.version_number = 1
        mock_modification.is_conflict = False
        mock_modification.conflict_resolution = None
        mock_modification.created_at = datetime.utcnow()
        
        # Mock database queries
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = [mock_modification]
        
        result = await team_collaboration_service.get_modification_history('reference', 'ref-123', 10, 0)
        
        assert len(result) == 1
        assert result[0]['modification_id'] == 'modification-123'
        assert result[0]['modification_type'] == 'update'
        assert result[0]['is_conflict'] is False
    
    @pytest.mark.asyncio
    async def test_create_editing_session_new(self, team_collaboration_service, mock_db):
        """Test creating a new editing session"""
        # Mock no existing session
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        mock_session = Mock()
        mock_session.id = 'session-123'
        mock_session.session_token = 'token-123'
        mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 'session-123')
        
        # Mock token generation
        team_collaboration_service._generate_session_token = Mock(return_value='token-123')
        
        result = await team_collaboration_service.create_editing_session(
            'reference', 'ref-123', 'user-123', 'workspace-123'
        )
        
        assert result['session_id'] == 'session-123'
        assert result['session_token'] == 'token-123'
        assert result['active_users'] == ['user-123']
        assert result['lock_status'] == 'unlocked'
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_create_editing_session_join_existing(self, team_collaboration_service, mock_db):
        """Test joining an existing editing session"""
        # Mock existing session
        mock_existing_session = Mock()
        mock_existing_session.id = 'session-123'
        mock_existing_session.session_token = 'token-123'
        mock_existing_session.active_users = ['user-456']
        mock_existing_session.lock_status = 'unlocked'
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_session
        mock_db.commit = Mock()
        
        result = await team_collaboration_service.create_editing_session(
            'reference', 'ref-123', 'user-123', 'workspace-123'
        )
        
        assert result['session_id'] == 'session-123'
        assert result['active_users'] == ['user-456', 'user-123']
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_resolve_conflict_success(self, team_collaboration_service, mock_db, sample_workspace_member):
        """Test successfully resolving a conflict"""
        # Mock conflict
        mock_conflict = Mock()
        mock_conflict.id = 'conflict-123'
        mock_conflict.workspace_id = 'workspace-123'
        mock_conflict.target_type = 'reference'
        mock_conflict.target_id = 'ref-123'
        mock_conflict.resolution_strategy = None
        mock_conflict.resolution_status = 'pending'
        mock_conflict.resolved_by = None
        mock_conflict.resolved_at = None
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_conflict,  # Conflict exists
            sample_workspace_member  # User has permission
        ]
        mock_db.commit = Mock()
        
        # Mock update query
        mock_update_query = Mock()
        mock_db.query.return_value.filter.return_value.update = Mock()
        
        # Mock activity logging
        team_collaboration_service._log_collaboration_history = AsyncMock()
        
        result = await team_collaboration_service.resolve_conflict(
            'conflict-123', 'user-123', 'manual', 'Resolved manually'
        )
        
        assert result['conflict_id'] == 'conflict-123'
        assert result['resolution_strategy'] == 'manual'
        assert result['resolved_by'] == 'user-123'
        
        assert mock_conflict.resolution_strategy == 'manual'
        assert mock_conflict.resolution_status == 'resolved'
        assert mock_conflict.resolved_by == 'user-123'
        assert mock_conflict.resolution_notes == 'Resolved manually'
        
        mock_db.commit.assert_called()
        team_collaboration_service._log_collaboration_history.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_resolve_conflict_not_found(self, team_collaboration_service, mock_db):
        """Test resolving non-existent conflict"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Conflict not found"):
            await team_collaboration_service.resolve_conflict(
                'conflict-123', 'user-123', 'manual'
            )
    
    @pytest.mark.asyncio
    async def test_resolve_conflict_no_permission(self, team_collaboration_service, mock_db):
        """Test resolving conflict without permission"""
        # Mock conflict
        mock_conflict = Mock()
        mock_conflict.workspace_id = 'workspace-123'
        
        # Mock member with insufficient permissions
        mock_member = Mock()
        mock_member.role = 'member'
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_conflict,  # Conflict exists
            mock_member  # User has insufficient permission
        ]
        
        with pytest.raises(PermissionError, match="User does not have permission to resolve conflicts"):
            await team_collaboration_service.resolve_conflict(
                'conflict-123', 'user-456', 'manual'
            )
    
    @pytest.mark.asyncio
    async def test_get_workspace_conflicts(self, team_collaboration_service, mock_db, sample_workspace_member):
        """Test getting workspace conflicts"""
        # Mock conflict
        mock_conflict = Mock()
        mock_conflict.id = 'conflict-123'
        mock_conflict.target_type = 'reference'
        mock_conflict.target_id = 'ref-123'
        mock_conflict.conflict_type = 'concurrent_edit'
        mock_conflict.conflicting_users = ['user-123', 'user-456']
        mock_conflict.conflict_data = {'details': 'conflict details'}
        mock_conflict.resolution_strategy = 'manual'
        mock_conflict.resolution_status = 'pending'
        mock_conflict.resolved_by = None
        mock_conflict.resolved_at = None
        mock_conflict.resolution_notes = None
        mock_conflict.created_at = datetime.utcnow()
        
        # Mock database queries
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = sample_workspace_member  # User has access
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_conflict]
        
        result = await team_collaboration_service.get_workspace_conflicts('workspace-123', 'user-123')
        
        assert len(result) == 1
        assert result[0]['conflict_id'] == 'conflict-123'
        assert result[0]['conflict_type'] == 'concurrent_edit'
        assert result[0]['resolution_status'] == 'pending'
    
    @pytest.mark.asyncio
    async def test_get_collaboration_history(self, team_collaboration_service, mock_db, sample_workspace_member):
        """Test getting collaboration history"""
        # Mock history entry
        mock_history = Mock()
        mock_history.id = 'history-123'
        mock_history.user_id = 'user-123'
        mock_history.action_type = 'create_workspace'
        mock_history.target_type = 'workspace'
        mock_history.target_id = 'workspace-123'
        mock_history.action_description = 'Created workspace'
        mock_history.action_data = {'workspace_type': 'research_team'}
        mock_history.impact_level = 'medium'
        mock_history.created_at = datetime.utcnow()
        
        # Mock database queries
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = sample_workspace_member  # User has access
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = [mock_history]
        
        result = await team_collaboration_service.get_collaboration_history('workspace-123', 'user-123', 10, 0)
        
        assert len(result) == 1
        assert result[0]['history_id'] == 'history-123'
        assert result[0]['action_type'] == 'create_workspace'
        assert result[0]['impact_level'] == 'medium'
    
    def test_generate_session_token(self, team_collaboration_service):
        """Test session token generation"""
        token = team_collaboration_service._generate_session_token()
        
        assert len(token) == 32
        assert token.isalnum()
        
        # Test custom length
        token_custom = team_collaboration_service._generate_session_token(16)
        assert len(token_custom) == 16
    
    @pytest.mark.asyncio
    async def test_detect_modification_conflict_no_conflict(self, team_collaboration_service, mock_db):
        """Test conflict detection with no conflicts"""
        # Mock no recent modifications
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = await team_collaboration_service._detect_modification_conflict(
            'reference', 'ref-123', 'user-123', 'update', {'title': 'new title'}
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_detect_modification_conflict_with_conflict(self, team_collaboration_service, mock_db):
        """Test conflict detection with overlapping changes"""
        # Mock recent modification with overlapping field
        mock_recent_mod = Mock()
        mock_recent_mod.field_changes = {'title': 'different title'}
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_recent_mod]
        
        result = await team_collaboration_service._detect_modification_conflict(
            'reference', 'ref-123', 'user-123', 'update', {'title': 'new title'}
        )
        
        assert result is True