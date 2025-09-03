"""
Tests for Zotero Reference Sharing Service
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from services.zotero.zotero_reference_sharing_service import ZoteroReferenceSharingService
from models.zotero_models import (
    ZoteroItem, ZoteroUserReferenceShare, ZoteroSharedReferenceCollection,
    ZoteroCollectionCollaborator, ZoteroSharedCollectionReference,
    ZoteroReferenceDiscussion, ZoteroSharingNotification
)


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def reference_sharing_service(mock_db):
    """Create ZoteroReferenceSharingService instance with mocked dependencies"""
    with patch('services.zotero.zotero_reference_sharing_service.get_db') as mock_get_db:
        mock_get_db.return_value = mock_db
        return ZoteroReferenceSharingService(mock_db)


@pytest.fixture
def sample_reference():
    """Sample ZoteroItem instance"""
    return ZoteroItem(
        id='ref-123',
        library_id='lib-123',
        zotero_item_key='ABCD1234',
        item_type='article',
        title='Sample Research Paper',
        creators=[{'firstName': 'John', 'lastName': 'Doe', 'creatorType': 'author'}],
        publication_year=2024
    )


@pytest.fixture
def sample_collection():
    """Sample ZoteroSharedReferenceCollection instance"""
    return ZoteroSharedReferenceCollection(
        id='collection-123',
        name='Research Project',
        description='A collaborative research project',
        owner_user_id='user-123',
        collection_type='research_project',
        is_public=False
    )


@pytest.fixture
def sample_collaborator():
    """Sample ZoteroCollectionCollaborator instance"""
    return ZoteroCollectionCollaborator(
        id='collaborator-123',
        collection_id='collection-123',
        user_id='user-123',
        permission_level='admin',
        role='owner',
        invited_by='user-123',
        invitation_status='accepted'
    )


class TestZoteroReferenceSharingService:
    """Test cases for ZoteroReferenceSharingService"""
    
    @pytest.mark.asyncio
    async def test_share_reference_with_user_new_share(self, reference_sharing_service, mock_db, sample_reference):
        """Test sharing a reference with a new user"""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_reference,  # Reference exists
            None  # No existing share
        ]
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Mock the new share object
        mock_share = Mock()
        mock_share.id = 'share-123'
        mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 'share-123')
        
        # Mock activity logging and notification creation
        reference_sharing_service._log_sharing_activity = AsyncMock()
        reference_sharing_service._create_notification = AsyncMock()
        
        result = await reference_sharing_service.share_reference_with_user(
            'ref-123', 'user-123', 'user-456', 'read', 'Check this out!'
        )
        
        assert result['reference_id'] == 'ref-123'
        assert result['shared_with_user_id'] == 'user-456'
        assert result['permission_level'] == 'read'
        assert result['action'] == 'created'
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
        reference_sharing_service._log_sharing_activity.assert_called_once()
        reference_sharing_service._create_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_share_reference_with_user_update_existing(self, reference_sharing_service, mock_db, sample_reference):
        """Test updating an existing reference share"""
        # Mock existing share
        mock_existing_share = Mock()
        mock_existing_share.id = 'share-123'
        mock_existing_share.permission_level = 'read'
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_reference,  # Reference exists
            mock_existing_share  # Existing share
        ]
        mock_db.commit = Mock()
        
        # Mock activity logging and notification creation
        reference_sharing_service._log_sharing_activity = AsyncMock()
        reference_sharing_service._create_notification = AsyncMock()
        
        result = await reference_sharing_service.share_reference_with_user(
            'ref-123', 'user-123', 'user-456', 'edit', 'Updated permissions'
        )
        
        assert result['action'] == 'updated'
        assert mock_existing_share.permission_level == 'edit'
        assert mock_existing_share.share_message == 'Updated permissions'
        
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_share_reference_with_user_reference_not_found(self, reference_sharing_service, mock_db):
        """Test sharing a non-existent reference"""
        # Mock database query to return None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Reference not found"):
            await reference_sharing_service.share_reference_with_user(
                'ref-123', 'user-123', 'user-456', 'read'
            )
    
    @pytest.mark.asyncio
    async def test_get_shared_references_as_owner(self, reference_sharing_service, mock_db, sample_reference):
        """Test getting references shared by the user"""
        # Mock share
        mock_share = Mock()
        mock_share.id = 'share-123'
        mock_share.reference_id = 'ref-123'
        mock_share.owner_user_id = 'user-123'
        mock_share.shared_with_user_id = 'user-456'
        mock_share.permission_level = 'read'
        mock_share.share_message = 'Check this out!'
        mock_share.created_at = datetime.utcnow()
        mock_share.updated_at = datetime.utcnow()
        
        # Mock database queries
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_share]
        
        # Mock reference query
        mock_db.query.return_value.filter.return_value.first.return_value = sample_reference
        
        result = await reference_sharing_service.get_shared_references('user-123', as_owner=True)
        
        assert len(result) == 1
        assert result[0]['share_id'] == 'share-123'
        assert result[0]['reference_title'] == 'Sample Research Paper'
        assert result[0]['permission_level'] == 'read'
    
    @pytest.mark.asyncio
    async def test_create_shared_collection(self, reference_sharing_service, mock_db):
        """Test creating a shared collection"""
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Mock the collection and collaborator objects
        mock_collection = Mock()
        mock_collection.id = 'collection-123'
        mock_collection.created_at = datetime.utcnow()
        
        mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 'collection-123')
        
        # Mock activity logging
        reference_sharing_service._log_sharing_activity = AsyncMock()
        
        result = await reference_sharing_service.create_shared_collection(
            'Research Project', 'user-123', 'A collaborative project', 'research_project', False
        )
        
        assert result['collection_id'] == 'collection-123'
        assert result['name'] == 'Research Project'
        assert result['is_public'] is False
        assert result['access_code'] is None
        
        # Should add collection and owner collaborator
        assert mock_db.add.call_count == 2
        mock_db.commit.assert_called()
        reference_sharing_service._log_sharing_activity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_shared_collection_public(self, reference_sharing_service, mock_db):
        """Test creating a public shared collection"""
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        mock_collection = Mock()
        mock_collection.id = 'collection-123'
        mock_collection.created_at = datetime.utcnow()
        
        mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 'collection-123')
        
        reference_sharing_service._log_sharing_activity = AsyncMock()
        
        result = await reference_sharing_service.create_shared_collection(
            'Public Research', 'user-123', 'A public project', 'research_project', True
        )
        
        assert result['is_public'] is True
        assert result['access_code'] is not None
        assert len(result['access_code']) == 8
    
    @pytest.mark.asyncio
    async def test_add_collaborator_to_collection_success(self, reference_sharing_service, mock_db, sample_collection, sample_collaborator):
        """Test successfully adding a collaborator to a collection"""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_collection,  # Collection exists
            sample_collaborator,  # Inviter has permission
            None  # No existing collaborator
        ]
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        mock_new_collaborator = Mock()
        mock_new_collaborator.id = 'collaborator-456'
        mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 'collaborator-456')
        
        # Mock activity logging and notification creation
        reference_sharing_service._log_sharing_activity = AsyncMock()
        reference_sharing_service._create_notification = AsyncMock()
        
        result = await reference_sharing_service.add_collaborator_to_collection(
            'collection-123', 'user-456', 'user-123', 'read', 'collaborator', 'Welcome!'
        )
        
        assert result['collaborator_id'] == 'collaborator-456'
        assert result['user_id'] == 'user-456'
        assert result['permission_level'] == 'read'
        assert result['invitation_status'] == 'pending'
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
        reference_sharing_service._log_sharing_activity.assert_called_once()
        reference_sharing_service._create_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_collaborator_collection_not_found(self, reference_sharing_service, mock_db):
        """Test adding collaborator to non-existent collection"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Collection not found"):
            await reference_sharing_service.add_collaborator_to_collection(
                'collection-123', 'user-456', 'user-123', 'read'
            )
    
    @pytest.mark.asyncio
    async def test_add_collaborator_no_permission(self, reference_sharing_service, mock_db, sample_collection):
        """Test adding collaborator without permission"""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_collection,  # Collection exists
            None  # Inviter has no permission
        ]
        
        with pytest.raises(PermissionError, match="User does not have permission to add collaborators"):
            await reference_sharing_service.add_collaborator_to_collection(
                'collection-123', 'user-456', 'user-789', 'read'
            )
    
    @pytest.mark.asyncio
    async def test_add_reference_to_collection_success(self, reference_sharing_service, mock_db, sample_collection, sample_collaborator, sample_reference):
        """Test successfully adding a reference to a collection"""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_collection,  # Collection exists
            sample_collaborator,  # User has permission
            sample_reference,  # Reference exists
            None  # Reference not already in collection
        ]
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        mock_collection_ref = Mock()
        mock_collection_ref.id = 'collection-ref-123'
        mock_collection_ref.added_at = datetime.utcnow()
        mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 'collection-ref-123')
        
        # Mock activity logging
        reference_sharing_service._log_sharing_activity = AsyncMock()
        
        result = await reference_sharing_service.add_reference_to_collection(
            'collection-123', 'ref-123', 'user-123', 'Great paper!', ['important'], True
        )
        
        assert result['collection_reference_id'] == 'collection-ref-123'
        assert result['reference_id'] == 'ref-123'
        assert result['added_by'] == 'user-123'
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
        reference_sharing_service._log_sharing_activity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_reference_to_collection_already_exists(self, reference_sharing_service, mock_db, sample_collection, sample_collaborator, sample_reference):
        """Test adding a reference that's already in the collection"""
        # Mock existing collection reference
        mock_existing_ref = Mock()
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_collection,  # Collection exists
            sample_collaborator,  # User has permission
            sample_reference,  # Reference exists
            mock_existing_ref  # Reference already in collection
        ]
        
        with pytest.raises(ValueError, match="Reference is already in this collection"):
            await reference_sharing_service.add_reference_to_collection(
                'collection-123', 'ref-123', 'user-123'
            )
    
    @pytest.mark.asyncio
    async def test_get_user_collections(self, reference_sharing_service, mock_db, sample_collection):
        """Test getting user's collections"""
        # Mock collaborator
        mock_collaborator = Mock()
        mock_collaborator.collection_id = 'collection-123'
        mock_collaborator.role = 'owner'
        mock_collaborator.permission_level = 'admin'
        
        # Mock database queries
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_collaborator]
        
        # Mock collection and count queries
        mock_db.query.return_value.filter.return_value.first.return_value = sample_collection
        mock_db.query.return_value.filter.return_value.count.side_effect = [5, 3]  # ref_count, collab_count
        
        result = await reference_sharing_service.get_user_collections('user-123')
        
        assert len(result) == 1
        assert result[0]['collection_id'] == 'collection-123'
        assert result[0]['name'] == 'Research Project'
        assert result[0]['user_role'] == 'owner'
        assert result[0]['reference_count'] == 5
        assert result[0]['collaborator_count'] == 3
    
    @pytest.mark.asyncio
    async def test_get_collection_references(self, reference_sharing_service, mock_db, sample_collaborator, sample_reference):
        """Test getting references in a collection"""
        # Mock collection reference
        mock_collection_ref = Mock()
        mock_collection_ref.id = 'collection-ref-123'
        mock_collection_ref.reference_id = 'ref-123'
        mock_collection_ref.added_by = 'user-123'
        mock_collection_ref.added_at = datetime.utcnow()
        mock_collection_ref.notes = 'Important paper'
        mock_collection_ref.tags = ['research']
        mock_collection_ref.is_featured = True
        mock_collection_ref.sort_order = 1
        
        # Mock database queries
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = sample_collaborator  # User has access
        mock_query.join.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = [mock_collection_ref]
        
        # Mock reference query
        mock_db.query.return_value.filter.return_value.first.return_value = sample_reference
        
        result = await reference_sharing_service.get_collection_references('collection-123', 'user-123', 10, 0)
        
        assert len(result) == 1
        assert result[0]['collection_reference_id'] == 'collection-ref-123'
        assert result[0]['reference_title'] == 'Sample Research Paper'
        assert result[0]['is_featured'] is True
    
    @pytest.mark.asyncio
    async def test_get_collection_references_no_access(self, reference_sharing_service, mock_db):
        """Test getting collection references without access"""
        # Mock database query to return None (no access)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(PermissionError, match="User does not have access to this collection"):
            await reference_sharing_service.get_collection_references('collection-123', 'user-456', 10, 0)
    
    @pytest.mark.asyncio
    async def test_add_reference_discussion(self, reference_sharing_service, mock_db, sample_reference, sample_collaborator):
        """Test adding a discussion to a reference"""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_reference,  # Reference exists
            sample_collaborator  # User has access to collection
        ]
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        mock_discussion = Mock()
        mock_discussion.id = 'discussion-123'
        mock_discussion.created_at = datetime.utcnow()
        mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 'discussion-123')
        
        # Mock activity logging
        reference_sharing_service._log_sharing_activity = AsyncMock()
        
        result = await reference_sharing_service.add_reference_discussion(
            'ref-123', 'user-123', 'Great paper!', 'comment', 'collection-123'
        )
        
        assert result['discussion_id'] == 'discussion-123'
        assert result['reference_id'] == 'ref-123'
        assert result['content'] == 'Great paper!'
        assert result['discussion_type'] == 'comment'
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
        reference_sharing_service._log_sharing_activity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_reference_discussion_no_access(self, reference_sharing_service, mock_db, sample_reference):
        """Test adding discussion without collection access"""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_reference,  # Reference exists
            None  # No access to collection
        ]
        
        with pytest.raises(PermissionError, match="User does not have access to this collection"):
            await reference_sharing_service.add_reference_discussion(
                'ref-123', 'user-456', 'Comment', 'comment', 'collection-123'
            )
    
    @pytest.mark.asyncio
    async def test_get_reference_discussions(self, reference_sharing_service, mock_db, sample_collaborator):
        """Test getting discussions for a reference"""
        # Mock discussion
        mock_discussion = Mock()
        mock_discussion.id = 'discussion-123'
        mock_discussion.reference_id = 'ref-123'
        mock_discussion.collection_id = 'collection-123'
        mock_discussion.user_id = 'user-123'
        mock_discussion.discussion_type = 'comment'
        mock_discussion.content = 'Great paper!'
        mock_discussion.parent_discussion_id = None
        mock_discussion.is_resolved = False
        mock_discussion.resolved_by = None
        mock_discussion.resolved_at = None
        mock_discussion.created_at = datetime.utcnow()
        mock_discussion.updated_at = datetime.utcnow()
        
        # Mock database queries
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = sample_collaborator  # User has access
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_discussion]
        
        result = await reference_sharing_service.get_reference_discussions('ref-123', 'user-123', 'collection-123')
        
        assert len(result) == 1
        assert result[0]['discussion_id'] == 'discussion-123'
        assert result[0]['content'] == 'Great paper!'
        assert result[0]['discussion_type'] == 'comment'
    
    @pytest.mark.asyncio
    async def test_get_user_notifications(self, reference_sharing_service, mock_db):
        """Test getting user notifications"""
        # Mock notification
        mock_notification = Mock()
        mock_notification.id = 'notification-123'
        mock_notification.notification_type = 'reference_shared'
        mock_notification.title = 'Reference shared'
        mock_notification.message = 'A reference was shared with you'
        mock_notification.target_type = 'reference'
        mock_notification.target_id = 'ref-123'
        mock_notification.sender_user_id = 'user-456'
        mock_notification.is_read = False
        mock_notification.is_dismissed = False
        mock_notification.action_url = '/references/ref-123'
        mock_notification.created_at = datetime.utcnow()
        mock_notification.read_at = None
        
        # Mock database queries
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = [mock_notification]
        
        result = await reference_sharing_service.get_user_notifications('user-123', False, 10, 0)
        
        assert len(result) == 1
        assert result[0]['notification_id'] == 'notification-123'
        assert result[0]['notification_type'] == 'reference_shared'
        assert result[0]['is_read'] is False
    
    @pytest.mark.asyncio
    async def test_mark_notification_as_read(self, reference_sharing_service, mock_db):
        """Test marking a notification as read"""
        # Mock notification
        mock_notification = Mock()
        mock_notification.is_read = False
        mock_notification.read_at = None
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_notification
        mock_db.commit = Mock()
        
        result = await reference_sharing_service.mark_notification_as_read('notification-123', 'user-123')
        
        assert result is True
        assert mock_notification.is_read is True
        assert mock_notification.read_at is not None
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mark_notification_as_read_not_found(self, reference_sharing_service, mock_db):
        """Test marking non-existent notification as read"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await reference_sharing_service.mark_notification_as_read('notification-123', 'user-123')
        
        assert result is False
    
    def test_generate_access_code(self, reference_sharing_service):
        """Test access code generation"""
        code = reference_sharing_service._generate_access_code()
        
        assert len(code) == 8
        assert code.isalnum()
        assert code.isupper()
        
        # Test custom length
        code_custom = reference_sharing_service._generate_access_code(12)
        assert len(code_custom) == 12
    
    @pytest.mark.asyncio
    async def test_log_sharing_activity(self, reference_sharing_service, mock_db):
        """Test logging sharing activity"""
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        await reference_sharing_service._log_sharing_activity(
            'user-123', 'share_reference', 'reference', 'ref-123',
            target_user_id='user-456', description='Shared reference',
            activity_data={'permission': 'read'}
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verify the activity log object was created with correct data
        call_args = mock_db.add.call_args[0][0]
        assert call_args.user_id == 'user-123'
        assert call_args.activity_type == 'share_reference'
        assert call_args.target_id == 'ref-123'
    
    @pytest.mark.asyncio
    async def test_create_notification(self, reference_sharing_service, mock_db):
        """Test creating a notification"""
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        await reference_sharing_service._create_notification(
            'user-123', 'reference_shared', 'Reference shared',
            'A reference was shared with you', 'reference', 'ref-123', 'user-456'
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verify the notification object was created with correct data
        call_args = mock_db.add.call_args[0][0]
        assert call_args.user_id == 'user-123'
        assert call_args.notification_type == 'reference_shared'
        assert call_args.title == 'Reference shared'