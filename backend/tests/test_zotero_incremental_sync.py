"""
Tests for Zotero incremental synchronization functionality
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session

from services.zotero.zotero_sync_service import ZoteroLibrarySyncService, ZoteroSyncProgress
from models.zotero_models import (
    ZoteroConnection, ZoteroLibrary, ZoteroCollection, ZoteroItem,
    ZoteroItemCollection, ZoteroSyncLog
)
from models.zotero_schemas import SyncType, SyncStatus


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = MagicMock(spec=Session)
    session.query.return_value.filter.return_value.first.return_value = None
    session.add = MagicMock()
    session.commit = MagicMock()
    session.flush = MagicMock()
    return session


@pytest.fixture
def mock_connection():
    """Mock Zotero connection"""
    connection = MagicMock(spec=ZoteroConnection)
    connection.id = "test-connection-id"
    connection.user_id = "test-user-id"
    connection.zotero_user_id = "12345"
    connection.access_token = "test-access-token"
    connection.connection_status = "active"
    return connection


@pytest.fixture
def mock_library():
    """Mock Zotero library"""
    library = MagicMock(spec=ZoteroLibrary)
    library.id = "test-library-id"
    library.zotero_library_id = "12345"
    library.library_type = "user"
    library.library_name = "Test Library"
    library.library_version = 100  # Current version
    library.is_active = True
    return library


@pytest.fixture
def mock_existing_item():
    """Mock existing Zotero item"""
    item = MagicMock(spec=ZoteroItem)
    item.id = "existing-item-id"
    item.zotero_item_key = "ITEM1234"
    item.item_version = 50  # Older version
    item.title = "Old Title"
    item.is_deleted = False
    return item


@pytest.fixture
def sync_service():
    """Create sync service instance"""
    return ZoteroLibrarySyncService()


class TestIncrementalSync:
    """Test incremental synchronization functionality"""
    
    @pytest.mark.asyncio
    async def test_incremental_sync_no_changes(self, sync_service, mock_connection, mock_library):
        """Test incremental sync when no changes are needed"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db, \
             patch.object(sync_service.client, '__aenter__') as mock_client_enter:
            
            # Setup database mock
            mock_db = AsyncMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_library]
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Setup API client - library is up to date
            mock_api_client = AsyncMock()
            mock_api_client.get_library_version.return_value = mock_library.library_version  # Same version
            mock_client_enter.return_value = mock_api_client
            
            progress = await sync_service.incremental_sync("test-connection")
            
            assert progress.status == SyncStatus.COMPLETED
            assert progress.libraries_processed == 1
            assert progress.items_processed == 0  # No items to process
            assert progress.errors_count == 0
    
    @pytest.mark.asyncio
    async def test_incremental_sync_with_updates(self, sync_service, mock_connection, mock_library, mock_existing_item):
        """Test incremental sync with item updates"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db, \
             patch.object(sync_service.client, '__aenter__') as mock_client_enter:
            
            # Setup database mock
            mock_db = AsyncMock()
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_connection,  # Connection query
                mock_existing_item  # Item query
            ]
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_library]
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Setup API client with newer version and modified items
            mock_api_client = AsyncMock()
            mock_api_client.get_library_version.return_value = mock_library.library_version + 10  # Newer version
            mock_api_client.get_collections.return_value = []  # No collections
            mock_api_client.get_items.return_value = [
                {
                    "key": "ITEM1234",
                    "version": 60,  # Newer than existing item
                    "data": {
                        "itemType": "journalArticle",
                        "title": "Updated Title",
                        "creators": [],
                        "tags": [],
                        "collections": [],
                        "dateAdded": "2023-01-01T10:00:00Z",
                        "dateModified": "2023-01-01T10:00:00Z"
                    }
                }
            ]
            mock_client_enter.return_value = mock_api_client
            
            progress = await sync_service.incremental_sync("test-connection")
            
            assert progress.status == SyncStatus.COMPLETED
            assert progress.libraries_processed == 1
            assert progress.items_processed == 1
            assert progress.items_updated == 1
            assert progress.items_added == 0
            assert progress.errors_count == 0
            
            # Verify item was updated
            assert mock_existing_item.title == "Updated Title"
            assert mock_existing_item.item_version == 60
    
    @pytest.mark.asyncio
    async def test_incremental_sync_with_new_items(self, sync_service, mock_connection, mock_library):
        """Test incremental sync with new items"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db, \
             patch.object(sync_service.client, '__aenter__') as mock_client_enter:
            
            # Setup database mock
            mock_db = AsyncMock()
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_connection,  # Connection query
                None  # Item query (new item)
            ]
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_library]
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Setup API client
            mock_api_client = AsyncMock()
            mock_api_client.get_library_version.return_value = mock_library.library_version + 5
            mock_api_client.get_collections.return_value = []
            mock_api_client.get_items.return_value = [
                {
                    "key": "NEWITEM123",
                    "version": 105,
                    "data": {
                        "itemType": "book",
                        "title": "New Book",
                        "creators": [
                            {
                                "creatorType": "author",
                                "firstName": "New",
                                "lastName": "Author"
                            }
                        ],
                        "tags": [{"tag": "new"}],
                        "collections": [],
                        "dateAdded": "2023-01-01T10:00:00Z",
                        "dateModified": "2023-01-01T10:00:00Z"
                    }
                }
            ]
            mock_client_enter.return_value = mock_api_client
            
            progress = await sync_service.incremental_sync("test-connection")
            
            assert progress.status == SyncStatus.COMPLETED
            assert progress.items_processed == 1
            assert progress.items_added == 1
            assert progress.items_updated == 0
            assert progress.errors_count == 0
    
    @pytest.mark.asyncio
    async def test_incremental_sync_with_deleted_items(self, sync_service, mock_connection, mock_library, mock_existing_item):
        """Test incremental sync with deleted items"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db, \
             patch.object(sync_service.client, '__aenter__') as mock_client_enter:
            
            # Setup database mock
            mock_db = AsyncMock()
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_connection,  # Connection query
                mock_existing_item  # Item query
            ]
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_library]
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Setup API client with deleted item
            mock_api_client = AsyncMock()
            mock_api_client.get_library_version.return_value = mock_library.library_version + 5
            mock_api_client.get_collections.return_value = []
            mock_api_client.get_items.return_value = [
                {
                    "key": "ITEM1234",
                    "version": 60,
                    "data": {
                        "itemType": "journalArticle",
                        "title": "Deleted Item",
                        "deleted": True,  # Item is deleted
                        "creators": [],
                        "tags": [],
                        "collections": [],
                        "dateAdded": "2023-01-01T10:00:00Z",
                        "dateModified": "2023-01-01T10:00:00Z"
                    }
                }
            ]
            mock_client_enter.return_value = mock_api_client
            
            progress = await sync_service.incremental_sync("test-connection")
            
            assert progress.status == SyncStatus.COMPLETED
            assert progress.items_processed == 1
            assert progress.items_deleted == 1
            assert progress.items_updated == 0
            assert progress.errors_count == 0
            
            # Verify item was marked as deleted
            assert mock_existing_item.is_deleted == True
            assert mock_existing_item.item_version == 60
    
    @pytest.mark.asyncio
    async def test_incremental_sync_with_collections(self, sync_service, mock_connection, mock_library):
        """Test incremental sync with collection updates"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db, \
             patch.object(sync_service.client, '__aenter__') as mock_client_enter:
            
            # Setup database mock
            mock_db = AsyncMock()
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_connection,  # Connection query
                None  # Collection query (new collection)
            ]
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_library]
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Setup API client
            mock_api_client = AsyncMock()
            mock_api_client.get_library_version.return_value = mock_library.library_version + 5
            mock_api_client.get_collections.return_value = [
                {
                    "key": "COLL1234",
                    "version": 105,
                    "data": {
                        "name": "New Collection",
                        "parentCollection": None
                    }
                }
            ]
            mock_api_client.get_items.return_value = []
            mock_client_enter.return_value = mock_api_client
            
            progress = await sync_service.incremental_sync("test-connection")
            
            assert progress.status == SyncStatus.COMPLETED
            assert progress.collections_processed == 1
            assert progress.errors_count == 0


class TestConflictDetection:
    """Test conflict detection functionality"""
    
    @pytest.mark.asyncio
    async def test_detect_no_conflicts(self, sync_service, mock_connection, mock_library):
        """Test conflict detection when no conflicts exist"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db, \
             patch.object(sync_service.client, '__aenter__') as mock_client_enter:
            
            # Setup database mock
            mock_db = AsyncMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_library]
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Setup API client - no version difference
            mock_api_client = AsyncMock()
            mock_api_client.get_library_version.return_value = mock_library.library_version
            mock_client_enter.return_value = mock_api_client
            
            conflicts = await sync_service.detect_sync_conflicts("test-connection")
            
            assert conflicts["has_conflicts"] == False
            assert conflicts["total_conflicts"] == 0
            assert len(conflicts["libraries"]) == 0
    
    @pytest.mark.asyncio
    async def test_detect_version_conflicts(self, sync_service, mock_connection, mock_library):
        """Test conflict detection with version mismatches"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db, \
             patch.object(sync_service.client, '__aenter__') as mock_client_enter:
            
            # Setup database mock
            mock_db = AsyncMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_library]
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Setup API client with newer version and modified items
            mock_api_client = AsyncMock()
            mock_api_client.get_library_version.return_value = mock_library.library_version + 10
            mock_api_client.get_items.return_value = [
                {
                    "key": "ITEM1",
                    "version": 110,
                    "data": {
                        "title": "Modified Item",
                        "deleted": False
                    }
                },
                {
                    "key": "ITEM2",
                    "version": 111,
                    "data": {
                        "title": "Deleted Item",
                        "deleted": True
                    }
                }
            ]
            mock_client_enter.return_value = mock_api_client
            
            conflicts = await sync_service.detect_sync_conflicts("test-connection")
            
            assert conflicts["has_conflicts"] == True
            assert conflicts["total_conflicts"] == 3  # 1 version + 2 items
            assert conflicts["conflict_types"]["version_mismatch"] == 1
            assert conflicts["conflict_types"]["modified_items"] == 1
            assert conflicts["conflict_types"]["deleted_items"] == 1
            assert len(conflicts["libraries"]) == 1
            
            library_conflicts = conflicts["libraries"][0]
            assert library_conflicts["library_name"] == mock_library.library_name
            assert library_conflicts["conflict_count"] == 3
            assert len(library_conflicts["conflicts"]) == 3
    
    @pytest.mark.asyncio
    async def test_resolve_conflicts_zotero_wins(self, sync_service, mock_connection):
        """Test conflict resolution with Zotero wins strategy"""
        with patch.object(sync_service, 'incremental_sync') as mock_incremental_sync:
            # Mock incremental sync result
            mock_progress = MagicMock()
            mock_progress.get_progress_dict.return_value = {
                "sync_id": "test-sync",
                "status": "completed",
                "items_updated": 5
            }
            mock_incremental_sync.return_value = mock_progress
            
            result = await sync_service.resolve_sync_conflicts(
                "test-connection",
                "zotero_wins"
            )
            
            assert result["strategy"] == "zotero_wins"
            assert result["resolved"] == True
            assert "sync_result" in result
            mock_incremental_sync.assert_called_once_with("test-connection", None)
    
    @pytest.mark.asyncio
    async def test_resolve_conflicts_unsupported_strategy(self, sync_service):
        """Test conflict resolution with unsupported strategy"""
        result = await sync_service.resolve_sync_conflicts(
            "test-connection",
            "local_wins"
        )
        
        assert result["strategy"] == "local_wins"
        assert result["resolved"] == False
        assert "not yet implemented" in result["message"]


class TestSyncErrorHandling:
    """Test error handling in sync operations"""
    
    @pytest.mark.asyncio
    async def test_incremental_sync_api_error(self, sync_service, mock_connection, mock_library):
        """Test incremental sync with API error"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db, \
             patch.object(sync_service.client, '__aenter__') as mock_client_enter:
            
            # Setup database mock
            mock_db = AsyncMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_library]
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Setup API client to raise error
            mock_api_client = AsyncMock()
            mock_api_client.get_library_version.side_effect = Exception("API Error")
            mock_client_enter.return_value = mock_api_client
            
            progress = await sync_service.incremental_sync("test-connection")
            
            assert progress.status == SyncStatus.FAILED
            assert progress.errors_count > 0
            assert "API Error" in progress.error_details[0]["error"]
    
    @pytest.mark.asyncio
    async def test_incremental_sync_item_error(self, sync_service, mock_connection, mock_library):
        """Test incremental sync with item processing error"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db, \
             patch.object(sync_service.client, '__aenter__') as mock_client_enter:
            
            # Setup database mock
            mock_db = AsyncMock()
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_connection,  # Connection query
                Exception("Database error")  # Item query error
            ]
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_library]
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Setup API client
            mock_api_client = AsyncMock()
            mock_api_client.get_library_version.return_value = mock_library.library_version + 5
            mock_api_client.get_collections.return_value = []
            mock_api_client.get_items.return_value = [
                {
                    "key": "ITEM1234",
                    "version": 105,
                    "data": {
                        "itemType": "article",
                        "title": "Test Item",
                        "creators": [],
                        "tags": [],
                        "collections": [],
                        "dateAdded": "2023-01-01T10:00:00Z",
                        "dateModified": "2023-01-01T10:00:00Z"
                    }
                }
            ]
            mock_client_enter.return_value = mock_api_client
            
            progress = await sync_service.incremental_sync("test-connection")
            
            # Sync should complete but with errors for individual items
            assert progress.status == SyncStatus.COMPLETED
            assert progress.errors_count > 0
            assert progress.items_processed == 1  # Item was processed despite error


class TestCollectionUpdates:
    """Test collection update functionality"""
    
    @pytest.mark.asyncio
    async def test_update_item_collections(self, sync_service):
        """Test updating item collection associations"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db:
            # Setup database mock
            mock_db = AsyncMock()
            mock_item = MagicMock()
            mock_item.id = "item-id"
            
            # Mock existing collection
            mock_collection = MagicMock()
            mock_collection.id = "collection-id"
            mock_db.query.return_value.filter.return_value.first.return_value = mock_collection
            
            # Mock library
            mock_library = MagicMock()
            mock_library.id = "library-id"
            
            await sync_service._update_item_collections(
                mock_db, mock_item, ["COLL1234"], mock_library
            )
            
            # Verify old associations were deleted
            mock_db.query.return_value.filter.return_value.delete.assert_called_once()
            
            # Verify new association was added
            mock_db.add.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_collection_hierarchy(self, sync_service):
        """Test updating collection parent-child relationships"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db:
            # Setup mock collections
            mock_parent = MagicMock()
            mock_parent.id = "parent-id"
            mock_parent.collection_name = "Parent Collection"
            mock_parent.collection_path = "Parent Collection"
            
            mock_child = MagicMock()
            mock_child.id = "child-id"
            mock_child.collection_name = "Child Collection"
            
            collection_map = {
                "PARENT123": mock_parent,
                "CHILD123": mock_child
            }
            
            collections_data = [
                {
                    "key": "CHILD123",
                    "data": {
                        "name": "Child Collection",
                        "parentCollection": "PARENT123"
                    }
                }
            ]
            
            await sync_service._update_collection_hierarchy(
                mock_get_db, collection_map, collections_data
            )
            
            # Verify child collection was linked to parent
            assert mock_child.parent_collection_id == "parent-id"
            assert mock_child.collection_path == "Parent Collection/Child Collection"


class TestVersionBasedSync:
    """Test version-based synchronization logic"""
    
    @pytest.mark.asyncio
    async def test_sync_single_item_update(self, sync_service, mock_connection, mock_library, mock_existing_item):
        """Test syncing a single updated item"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_item
            
            item_data = {
                "key": "ITEM1234",
                "version": 60,  # Newer than existing
                "data": {
                    "itemType": "journalArticle",
                    "title": "Updated Title",
                    "creators": [],
                    "tags": [],
                    "collections": [],
                    "dateAdded": "2023-01-01T10:00:00Z",
                    "dateModified": "2023-01-01T10:00:00Z"
                }
            }
            
            progress = MagicMock()
            progress.items_updated = 0
            progress.items_added = 0
            progress.items_deleted = 0
            
            await sync_service._sync_single_item(
                mock_db, None, mock_connection, mock_library, item_data, progress
            )
            
            # Verify item was updated
            assert progress.items_updated == 1
            assert mock_existing_item.title == "Updated Title"
            assert mock_existing_item.item_version == 60
    
    @pytest.mark.asyncio
    async def test_sync_single_item_delete(self, sync_service, mock_connection, mock_library, mock_existing_item):
        """Test syncing a deleted item"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_item
            
            item_data = {
                "key": "ITEM1234",
                "version": 60,
                "data": {
                    "deleted": True,
                    "itemType": "journalArticle",
                    "title": "Deleted Item"
                }
            }
            
            progress = MagicMock()
            progress.items_updated = 0
            progress.items_added = 0
            progress.items_deleted = 0
            
            await sync_service._sync_single_item(
                mock_db, None, mock_connection, mock_library, item_data, progress
            )
            
            # Verify item was marked as deleted
            assert progress.items_deleted == 1
            assert mock_existing_item.is_deleted == True
            assert mock_existing_item.item_version == 60
    
    @pytest.mark.asyncio
    async def test_sync_single_item_no_update_needed(self, sync_service, mock_connection, mock_library, mock_existing_item):
        """Test syncing an item that doesn't need updates"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_existing_item.item_version = 60  # Same as remote
            mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_item
            
            item_data = {
                "key": "ITEM1234",
                "version": 60,  # Same version
                "data": {
                    "itemType": "journalArticle",
                    "title": "Same Title",
                    "creators": [],
                    "tags": [],
                    "collections": []
                }
            }
            
            progress = MagicMock()
            progress.items_updated = 0
            progress.items_added = 0
            progress.items_deleted = 0
            
            await sync_service._sync_single_item(
                mock_db, None, mock_connection, mock_library, item_data, progress
            )
            
            # Verify no updates were made
            assert progress.items_updated == 0
            assert progress.items_added == 0
            assert progress.items_deleted == 0


class TestSyncStatusTracking:
    """Test sync status and progress tracking"""
    
    def test_sync_progress_initialization(self):
        """Test sync progress tracker initialization"""
        from services.zotero.zotero_sync_service import ZoteroSyncProgress
        from models.zotero_schemas import SyncType
        
        progress = ZoteroSyncProgress("test-sync-123", SyncType.INCREMENTAL)
        
        assert progress.sync_id == "test-sync-123"
        assert progress.sync_type == SyncType.INCREMENTAL
        assert progress.status == SyncStatus.STARTED
        assert progress.items_processed == 0
        assert progress.items_added == 0
        assert progress.items_updated == 0
        assert progress.items_deleted == 0
        assert progress.errors_count == 0
    
    def test_sync_progress_update(self):
        """Test sync progress updates"""
        from services.zotero.zotero_sync_service import ZoteroSyncProgress
        from models.zotero_schemas import SyncType
        
        progress = ZoteroSyncProgress("test-sync-123", SyncType.INCREMENTAL)
        
        # Update progress
        progress.update_progress(
            items_processed=10,
            items_added=5,
            items_updated=3,
            items_deleted=2
        )
        
        assert progress.items_processed == 10
        assert progress.items_added == 5
        assert progress.items_updated == 3
        assert progress.items_deleted == 2
    
    def test_sync_progress_error_handling(self):
        """Test sync progress error tracking"""
        from services.zotero.zotero_sync_service import ZoteroSyncProgress
        from models.zotero_schemas import SyncType
        
        progress = ZoteroSyncProgress("test-sync-123", SyncType.INCREMENTAL)
        
        # Add errors
        progress.add_error("Test error 1", {"item_key": "ITEM123"})
        progress.add_error("Test error 2")
        
        assert progress.errors_count == 2
        assert len(progress.error_details) == 2
        assert progress.error_details[0]["error"] == "Test error 1"
        assert progress.error_details[0]["details"]["item_key"] == "ITEM123"
    
    def test_sync_progress_completion(self):
        """Test sync progress completion"""
        from services.zotero.zotero_sync_service import ZoteroSyncProgress
        from models.zotero_schemas import SyncType
        
        progress = ZoteroSyncProgress("test-sync-123", SyncType.INCREMENTAL)
        
        # Complete sync
        progress.complete(SyncStatus.COMPLETED)
        
        assert progress.status == SyncStatus.COMPLETED
        assert progress.completed_at is not None
    
    def test_sync_progress_dict_output(self):
        """Test sync progress dictionary output"""
        from services.zotero.zotero_sync_service import ZoteroSyncProgress
        from models.zotero_schemas import SyncType
        
        progress = ZoteroSyncProgress("test-sync-123", SyncType.INCREMENTAL)
        progress.update_progress(items_processed=5, items_added=3)
        progress.add_error("Test error")
        
        progress_dict = progress.get_progress_dict()
        
        assert progress_dict["sync_id"] == "test-sync-123"
        assert progress_dict["sync_type"] == "incremental"
        assert progress_dict["progress"]["items_processed"] == 5
        assert progress_dict["progress"]["items_added"] == 3
        assert progress_dict["errors"]["count"] == 1


if __name__ == "__main__":
    pytest.main([__file__])