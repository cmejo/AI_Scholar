"""
Tests for Zotero library import functionality
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
def mock_library_data():
    """Mock library data from Zotero API"""
    return [
        {
            "id": "12345",
            "type": "user",
            "name": "Personal Library",
            "owner": "12345"
        },
        {
            "id": "67890",
            "type": "group",
            "name": "Research Group",
            "owner": "11111",
            "group_type": "PublicOpen",
            "description": "Research collaboration group"
        }
    ]


@pytest.fixture
def mock_collections_data():
    """Mock collections data from Zotero API"""
    return [
        {
            "key": "ABCD1234",
            "version": 1,
            "data": {
                "name": "Research Papers",
                "parentCollection": None
            }
        },
        {
            "key": "EFGH5678",
            "version": 1,
            "data": {
                "name": "Methodology",
                "parentCollection": "ABCD1234"
            }
        }
    ]


@pytest.fixture
def mock_items_data():
    """Mock items data from Zotero API"""
    return [
        {
            "key": "ITEM1234",
            "version": 1,
            "data": {
                "itemType": "journalArticle",
                "title": "Test Article",
                "creators": [
                    {
                        "creatorType": "author",
                        "firstName": "John",
                        "lastName": "Doe"
                    }
                ],
                "publicationTitle": "Test Journal",
                "date": "2023-01-01",
                "DOI": "10.1000/test.doi",
                "abstractNote": "This is a test article",
                "tags": [{"tag": "test"}, {"tag": "research"}],
                "collections": ["ABCD1234"],
                "dateAdded": "2023-01-01T10:00:00Z",
                "dateModified": "2023-01-01T10:00:00Z"
            }
        },
        {
            "key": "ITEM5678",
            "version": 1,
            "data": {
                "itemType": "book",
                "title": "Test Book",
                "creators": [
                    {
                        "creatorType": "author",
                        "firstName": "Jane",
                        "lastName": "Smith"
                    }
                ],
                "publisher": "Test Publisher",
                "date": "2022",
                "ISBN": "978-0-123456-78-9",
                "tags": [{"tag": "book"}, {"tag": "reference"}],
                "collections": [],
                "dateAdded": "2023-01-02T10:00:00Z",
                "dateModified": "2023-01-02T10:00:00Z"
            }
        }
    ]


@pytest.fixture
def sync_service():
    """Create sync service instance"""
    return ZoteroLibrarySyncService()


class TestZoteroSyncProgress:
    """Test ZoteroSyncProgress class"""
    
    def test_sync_progress_initialization(self):
        """Test sync progress initialization"""
        sync_id = "test-sync-123"
        sync_type = SyncType.FULL
        
        progress = ZoteroSyncProgress(sync_id, sync_type)
        
        assert progress.sync_id == sync_id
        assert progress.sync_type == sync_type
        assert progress.status == SyncStatus.STARTED
        assert progress.items_processed == 0
        assert progress.items_added == 0
        assert progress.items_updated == 0
        assert progress.errors_count == 0
        assert isinstance(progress.started_at, datetime)
        assert progress.completed_at is None
    
    def test_update_progress(self):
        """Test progress update functionality"""
        progress = ZoteroSyncProgress("test-sync", SyncType.FULL)
        
        progress.update_progress(
            items_processed=10,
            items_added=5,
            items_updated=3,
            current_library="Test Library"
        )
        
        assert progress.items_processed == 10
        assert progress.items_added == 5
        assert progress.items_updated == 3
        assert progress.current_library == "Test Library"
    
    def test_add_error(self):
        """Test error tracking"""
        progress = ZoteroSyncProgress("test-sync", SyncType.FULL)
        progress.current_library = "Test Library"
        progress.current_operation = "importing_items"
        
        progress.add_error("Test error", {"detail": "error details"})
        
        assert progress.errors_count == 1
        assert len(progress.error_details) == 1
        
        error = progress.error_details[0]
        assert error["error"] == "Test error"
        assert error["library"] == "Test Library"
        assert error["operation"] == "importing_items"
        assert error["details"]["detail"] == "error details"
        assert "timestamp" in error
    
    def test_complete(self):
        """Test completion functionality"""
        progress = ZoteroSyncProgress("test-sync", SyncType.FULL)
        
        progress.complete(SyncStatus.COMPLETED)
        
        assert progress.status == SyncStatus.COMPLETED
        assert isinstance(progress.completed_at, datetime)
    
    def test_get_progress_dict(self):
        """Test progress dictionary generation"""
        progress = ZoteroSyncProgress("test-sync", SyncType.FULL)
        progress.update_progress(items_processed=5, items_added=3)
        progress.add_error("Test error")
        
        progress_dict = progress.get_progress_dict()
        
        assert progress_dict["sync_id"] == "test-sync"
        assert progress_dict["sync_type"] == "full"
        assert progress_dict["status"] == "started"
        assert progress_dict["progress"]["items_processed"] == 5
        assert progress_dict["progress"]["items_added"] == 3
        assert progress_dict["errors"]["count"] == 1
        assert len(progress_dict["errors"]["details"]) == 1


class TestZoteroLibrarySyncService:
    """Test ZoteroLibrarySyncService class"""
    
    @pytest.mark.asyncio
    async def test_import_library_connection_not_found(self, sync_service):
        """Test import with non-existent connection"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            progress = await sync_service.import_library("non-existent-connection")
            
            assert progress.status == SyncStatus.FAILED
            assert progress.errors_count > 0
            assert "not found" in progress.error_details[0]["error"]
    
    @pytest.mark.asyncio
    async def test_import_library_inactive_connection(self, sync_service, mock_connection):
        """Test import with inactive connection"""
        mock_connection.connection_status = "expired"
        
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            progress = await sync_service.import_library("test-connection")
            
            assert progress.status == SyncStatus.FAILED
            assert progress.errors_count > 0
            assert "not active" in progress.error_details[0]["error"]
    
    @pytest.mark.asyncio
    async def test_import_library_success(
        self, 
        sync_service, 
        mock_connection, 
        mock_library_data,
        mock_collections_data,
        mock_items_data
    ):
        """Test successful library import"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db, \
             patch.object(sync_service.client, '__aenter__') as mock_client_enter:
            
            # Setup database mock
            mock_db = AsyncMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.flush = MagicMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Setup API client mock
            mock_api_client = AsyncMock()
            mock_api_client.get_libraries.return_value = mock_library_data
            mock_api_client.get_collections.return_value = mock_collections_data
            mock_api_client.get_items.return_value = mock_items_data
            mock_client_enter.return_value = mock_api_client
            
            # Mock library and collection creation
            mock_library = MagicMock()
            mock_library.id = "test-library-id"
            mock_library.library_name = "Personal Library"
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_connection,  # Connection query
                None,  # Library query (new library)
                None, None,  # Collection queries (new collections)
                None, None   # Item queries (new items)
            ]
            
            progress = await sync_service.import_library("test-connection")
            
            assert progress.status == SyncStatus.COMPLETED
            assert progress.libraries_processed == 2  # Personal + Group library
            assert progress.collections_processed == 2
            assert progress.items_processed == 2
            assert progress.items_added == 2
            assert progress.errors_count == 0
    
    @pytest.mark.asyncio
    async def test_import_library_with_api_error(self, sync_service, mock_connection):
        """Test import with API error"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db, \
             patch.object(sync_service.client, '__aenter__') as mock_client_enter:
            
            # Setup database mock
            mock_db = AsyncMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Setup API client to raise error
            mock_api_client = AsyncMock()
            mock_api_client.get_libraries.side_effect = Exception("API Error")
            mock_client_enter.return_value = mock_api_client
            
            progress = await sync_service.import_library("test-connection")
            
            assert progress.status == SyncStatus.FAILED
            assert progress.errors_count > 0
            assert "API Error" in progress.error_details[0]["error"]
    
    def test_transform_item_data(self, sync_service):
        """Test item data transformation"""
        zotero_data = {
            "itemType": "journalArticle",
            "title": "Test Article",
            "creators": [
                {
                    "creatorType": "author",
                    "firstName": "John",
                    "lastName": "Doe"
                }
            ],
            "publicationTitle": "Test Journal",
            "date": "2023-01-01",
            "DOI": "10.1000/test.doi",
            "publisher": "Test Publisher",
            "abstractNote": "Test abstract",
            "dateAdded": "2023-01-01T10:00:00Z",
            "dateModified": "2023-01-01T10:00:00Z",
            "tags": [{"tag": "test"}, {"tag": "research"}],
            "extra": "Extra field"
        }
        
        transformed = sync_service._transform_item_data(zotero_data)
        
        assert transformed["item_type"] == "journalArticle"
        assert transformed["title"] == "Test Article"
        assert len(transformed["creators"]) == 1
        assert transformed["creators"][0]["creator_type"] == "author"
        assert transformed["creators"][0]["first_name"] == "John"
        assert transformed["creators"][0]["last_name"] == "Doe"
        assert transformed["publication_title"] == "Test Journal"
        assert transformed["publication_year"] == 2023
        assert transformed["doi"] == "10.1000/test.doi"
        assert transformed["publisher"] == "Test Publisher"
        assert transformed["abstract_note"] == "Test abstract"
        assert transformed["tags"] == ["test", "research"]
        assert "extra" in transformed["extra_fields"]
        assert isinstance(transformed["date_added"], datetime)
        assert isinstance(transformed["date_modified"], datetime)
    
    def test_transform_item_data_with_organization_creator(self, sync_service):
        """Test item data transformation with organization creator"""
        zotero_data = {
            "itemType": "report",
            "title": "Test Report",
            "creators": [
                {
                    "creatorType": "author",
                    "name": "Test Organization"
                }
            ]
        }
        
        transformed = sync_service._transform_item_data(zotero_data)
        
        assert len(transformed["creators"]) == 1
        assert transformed["creators"][0]["creator_type"] == "author"
        assert transformed["creators"][0]["name"] == "Test Organization"
        assert transformed["creators"][0]["first_name"] is None
        assert transformed["creators"][0]["last_name"] is None
    
    def test_transform_item_data_year_extraction(self, sync_service):
        """Test year extraction from various date formats"""
        test_cases = [
            ("2023", 2023),
            ("2023-01-01", 2023),
            ("January 2023", 2023),
            ("2023/01/01", 2023),
            ("1999-12-31", 1999),
            ("2000", 2000),
            ("no year here", None),
            ("", None),
            (None, None)
        ]
        
        for date_input, expected_year in test_cases:
            zotero_data = {
                "itemType": "article",
                "title": "Test",
                "date": date_input
            }
            
            transformed = sync_service._transform_item_data(zotero_data)
            assert transformed["publication_year"] == expected_year
    
    def test_parse_zotero_date(self, sync_service):
        """Test Zotero date parsing"""
        # Valid ISO date
        date_str = "2023-01-01T10:00:00Z"
        parsed = sync_service._parse_zotero_date(date_str)
        assert isinstance(parsed, datetime)
        assert parsed.year == 2023
        assert parsed.month == 1
        assert parsed.day == 1
        
        # Invalid date
        invalid_date = "not a date"
        parsed = sync_service._parse_zotero_date(invalid_date)
        assert parsed is None
        
        # None input
        parsed = sync_service._parse_zotero_date(None)
        assert parsed is None
    
    def test_get_sync_progress(self, sync_service):
        """Test sync progress retrieval"""
        # No active sync
        progress = sync_service.get_sync_progress("non-existent")
        assert progress is None
        
        # Add active sync
        sync_progress = ZoteroSyncProgress("test-sync", SyncType.FULL)
        sync_service._active_syncs["test-sync"] = sync_progress
        
        progress = sync_service.get_sync_progress("test-sync")
        assert progress is not None
        assert progress["sync_id"] == "test-sync"
    
    def test_get_active_syncs(self, sync_service):
        """Test active syncs retrieval"""
        # No active syncs
        active = sync_service.get_active_syncs()
        assert len(active) == 0
        
        # Add active syncs
        sync1 = ZoteroSyncProgress("sync-1", SyncType.FULL)
        sync2 = ZoteroSyncProgress("sync-2", SyncType.INCREMENTAL)
        sync_service._active_syncs["sync-1"] = sync1
        sync_service._active_syncs["sync-2"] = sync2
        
        active = sync_service.get_active_syncs()
        assert len(active) == 2
        assert any(s["sync_id"] == "sync-1" for s in active)
        assert any(s["sync_id"] == "sync-2" for s in active)
    
    @pytest.mark.asyncio
    async def test_cancel_sync(self, sync_service):
        """Test sync cancellation"""
        # Non-existent sync
        success = await sync_service.cancel_sync("non-existent")
        assert success is False
        
        # Existing sync
        sync_progress = ZoteroSyncProgress("test-sync", SyncType.FULL)
        sync_service._active_syncs["test-sync"] = sync_progress
        
        success = await sync_service.cancel_sync("test-sync")
        assert success is True
        assert sync_progress.status == SyncStatus.CANCELLED
        assert "test-sync" not in sync_service._active_syncs


class TestLibraryImportIntegration:
    """Integration tests for library import"""
    
    @pytest.mark.asyncio
    async def test_full_import_workflow(
        self,
        sync_service,
        mock_connection,
        mock_library_data,
        mock_collections_data,
        mock_items_data
    ):
        """Test complete import workflow"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db, \
             patch.object(sync_service.client, '__aenter__') as mock_client_enter:
            
            # Setup comprehensive database mock
            mock_db = AsyncMock()
            mock_sync_log = MagicMock()
            
            # Mock query results
            query_results = [
                mock_connection,  # Connection query
                None,  # Library 1 query (new)
                None,  # Library 2 query (new)
                None, None,  # Collection queries (new)
                None, None   # Item queries (new)
            ]
            mock_db.query.return_value.filter.return_value.first.side_effect = query_results
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.flush = MagicMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Setup API client mock with realistic responses
            mock_api_client = AsyncMock()
            mock_api_client.get_libraries.return_value = mock_library_data
            mock_api_client.get_collections.return_value = mock_collections_data
            mock_api_client.get_items.return_value = mock_items_data
            mock_client_enter.return_value = mock_api_client
            
            # Track progress with callback
            progress_updates = []
            
            async def progress_callback(progress_dict):
                progress_updates.append(progress_dict)
            
            # Execute import
            progress = await sync_service.import_library(
                connection_id="test-connection",
                progress_callback=progress_callback
            )
            
            # Verify final results
            assert progress.status == SyncStatus.COMPLETED
            assert progress.libraries_processed == 2
            assert progress.collections_processed == 2
            assert progress.items_processed == 2
            assert progress.items_added == 2
            assert progress.errors_count == 0
            
            # Verify database operations
            assert mock_db.add.called
            assert mock_db.commit.called
            
            # Verify API calls
            mock_api_client.get_libraries.assert_called_once()
            assert mock_api_client.get_collections.call_count == 2  # Once per library
            assert mock_api_client.get_items.call_count >= 2  # At least once per library
    
    @pytest.mark.asyncio
    async def test_import_with_existing_data(self, sync_service, mock_connection):
        """Test import with existing libraries, collections, and items"""
        with patch('services.zotero.zotero_sync_service.get_db') as mock_get_db, \
             patch.object(sync_service.client, '__aenter__') as mock_client_enter:
            
            # Setup database with existing data
            mock_db = AsyncMock()
            
            # Mock existing library
            existing_library = MagicMock()
            existing_library.id = "existing-library-id"
            existing_library.library_name = "Old Name"
            
            # Mock existing collection
            existing_collection = MagicMock()
            existing_collection.id = "existing-collection-id"
            existing_collection.collection_name = "Old Collection Name"
            existing_collection.collection_version = 0
            
            # Mock existing item
            existing_item = MagicMock()
            existing_item.id = "existing-item-id"
            existing_item.title = "Old Title"
            existing_item.item_version = 0
            
            # Setup query results to return existing objects
            query_results = [
                mock_connection,  # Connection query
                existing_library,  # Library query (existing)
                existing_collection,  # Collection query (existing)
                existing_item  # Item query (existing)
            ]
            mock_db.query.return_value.filter.return_value.first.side_effect = query_results
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Setup API client
            mock_api_client = AsyncMock()
            mock_api_client.get_libraries.return_value = [{
                "id": "12345",
                "type": "user",
                "name": "Updated Library Name",
                "owner": "12345"
            }]
            mock_api_client.get_collections.return_value = [{
                "key": "ABCD1234",
                "version": 2,  # Higher version
                "data": {
                    "name": "Updated Collection Name",
                    "parentCollection": None
                }
            }]
            mock_api_client.get_items.return_value = [{
                "key": "ITEM1234",
                "version": 2,  # Higher version
                "data": {
                    "itemType": "journalArticle",
                    "title": "Updated Article Title",
                    "creators": [],
                    "tags": [],
                    "collections": [],
                    "dateAdded": "2023-01-01T10:00:00Z",
                    "dateModified": "2023-01-01T10:00:00Z"
                }
            }]
            mock_client_enter.return_value = mock_api_client
            
            progress = await sync_service.import_library("test-connection")
            
            # Verify updates were made
            assert progress.status == SyncStatus.COMPLETED
            assert progress.items_updated == 1  # Item was updated
            assert existing_library.library_name == "Updated Library Name"
            assert existing_collection.collection_name == "Updated Collection Name"
            assert existing_collection.collection_version == 2


if __name__ == "__main__":
    pytest.main([__file__])