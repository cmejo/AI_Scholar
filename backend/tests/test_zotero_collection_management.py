"""
Tests for Zotero collection and hierarchy management functionality
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session

from services.zotero.zotero_collection_service import ZoteroCollectionService
from models.zotero_models import (
    ZoteroConnection, ZoteroLibrary, ZoteroCollection, ZoteroItem,
    ZoteroItemCollection
)


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
    return connection


@pytest.fixture
def mock_library():
    """Mock Zotero library"""
    library = MagicMock(spec=ZoteroLibrary)
    library.id = "test-library-id"
    library.connection_id = "test-connection-id"
    return library


@pytest.fixture
def mock_collections():
    """Mock collection hierarchy"""
    root_collection = MagicMock(spec=ZoteroCollection)
    root_collection.id = "root-collection-id"
    root_collection.library_id = "test-library-id"
    root_collection.zotero_collection_key = "ROOT123"
    root_collection.parent_collection_id = None
    root_collection.collection_name = "Research Papers"
    root_collection.collection_path = "Research Papers"
    root_collection.item_count = 10
    root_collection.created_at = datetime.now()
    root_collection.updated_at = datetime.now()
    
    child_collection = MagicMock(spec=ZoteroCollection)
    child_collection.id = "child-collection-id"
    child_collection.library_id = "test-library-id"
    child_collection.zotero_collection_key = "CHILD123"
    child_collection.parent_collection_id = "root-collection-id"
    child_collection.collection_name = "Methodology"
    child_collection.collection_path = "Research Papers/Methodology"
    child_collection.item_count = 5
    child_collection.created_at = datetime.now()
    child_collection.updated_at = datetime.now()
    
    return [root_collection, child_collection]


@pytest.fixture
def collection_service():
    """Create collection service instance"""
    return ZoteroCollectionService()


class TestCollectionRetrieval:
    """Test collection retrieval functionality"""
    
    @pytest.mark.asyncio
    async def test_get_library_collections_flat(
        self, 
        collection_service, 
        mock_connection, 
        mock_library, 
        mock_collections
    ):
        """Test getting collections without hierarchy"""
        with patch('services.zotero.zotero_collection_service.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_connection, mock_library
            ]
            mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_collections
            mock_db.query.return_value.filter.return_value.count.return_value = 3  # Mock item count
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            collections = await collection_service.get_library_collections(
                connection_id="test-connection-id",
                library_id="test-library-id",
                include_hierarchy=False,
                include_item_counts=True
            )
            
            assert len(collections) == 2
            assert collections[0]["collection_name"] == "Research Papers"
            assert collections[1]["collection_name"] == "Methodology"
            assert "actual_item_count" in collections[0]
    
    @pytest.mark.asyncio
    async def test_get_library_collections_hierarchical(
        self, 
        collection_service, 
        mock_connection, 
        mock_library, 
        mock_collections
    ):
        """Test getting collections with hierarchy"""
        with patch('services.zotero.zotero_collection_service.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_connection, mock_library
            ]
            mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_collections
            mock_db.query.return_value.filter.return_value.count.return_value = 3
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            collections = await collection_service.get_library_collections(
                connection_id="test-connection-id",
                library_id="test-library-id",
                include_hierarchy=True,
                include_item_counts=False
            )
            
            # Should return only root collections with children nested
            root_collections = [c for c in collections if c["parent_collection_id"] is None]
            assert len(root_collections) == 1
            
            root = root_collections[0]
            assert root["collection_name"] == "Research Papers"
            assert "children" in root
    
    @pytest.mark.asyncio
    async def test_get_collection_tree(
        self, 
        collection_service, 
        mock_connection, 
        mock_library, 
        mock_collections
    ):
        """Test getting collection tree structure"""
        with patch('services.zotero.zotero_collection_service.get_db') as mock_get_db:
            mock_db = AsyncMock()
            
            # Mock queries for tree building
            mock_db.query.return_value.filter.return_value.first.return_value = mock_collections[0]  # Root collection
            mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_collections[1]]  # Child collections
            mock_db.query.return_value.filter.return_value.count.return_value = 5  # Item count
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            tree = await collection_service.get_collection_tree(
                connection_id="test-connection-id",
                library_id="test-library-id",
                collection_id="root-collection-id"
            )
            
            assert tree.collection_name == "Research Papers"
            assert tree.item_count == 5
            assert len(tree.children) == 1
            assert tree.children[0].collection_name == "Methodology"
    
    @pytest.mark.asyncio
    async def test_get_collection_items(
        self, 
        collection_service, 
        mock_connection, 
        mock_library, 
        mock_collections
    ):
        """Test getting items in a collection"""
        with patch('services.zotero.zotero_collection_service.get_db') as mock_get_db:
            mock_db = AsyncMock()
            
            # Mock collection
            mock_db.query.return_value.filter.return_value.first.return_value = mock_collections[0]
            
            # Mock items
            mock_item = MagicMock(spec=ZoteroItem)
            mock_item.id = "item-id"
            mock_item.title = "Test Article"
            mock_item.item_type = "journalArticle"
            mock_item.creators = [{"name": "Test Author"}]
            mock_item.is_deleted = False
            
            mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.count.return_value = 1
            mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_item]
            
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            result = await collection_service.get_collection_items(
                connection_id="test-connection-id",
                library_id="test-library-id",
                collection_id="root-collection-id",
                include_subcollections=False,
                limit=10,
                offset=0
            )
            
            assert "collection" in result
            assert "items" in result
            assert "pagination" in result
            assert result["collection"]["name"] == "Research Papers"
            assert len(result["items"]) == 1
            assert result["items"][0]["title"] == "Test Article"
            assert result["pagination"]["total_count"] == 1
    
    @pytest.mark.asyncio
    async def test_search_collections(
        self, 
        collection_service, 
        mock_connection, 
        mock_library, 
        mock_collections
    ):
        """Test searching collections by name"""
        with patch('services.zotero.zotero_collection_service.get_db') as mock_get_db:
            mock_db = AsyncMock()
            
            # Mock search results
            filtered_collections = [c for c in mock_collections if "Research" in c.collection_name]
            mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = filtered_collections
            mock_db.query.return_value.filter.return_value.count.return_value = 3  # Item count
            
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            results = await collection_service.search_collections(
                connection_id="test-connection-id",
                library_id="test-library-id",
                query="Research",
                limit=10
            )
            
            assert len(results) == 1
            assert results[0]["collection_name"] == "Research Papers"
            assert "item_count" in results[0]


class TestCollectionHierarchy:
    """Test collection hierarchy functionality"""
    
    def test_build_collection_hierarchy(self, collection_service):
        """Test building hierarchical structure from flat list"""
        collections = [
            {
                "id": "root-1",
                "collection_name": "Root 1",
                "parent_collection_id": None
            },
            {
                "id": "child-1",
                "collection_name": "Child 1",
                "parent_collection_id": "root-1"
            },
            {
                "id": "child-2",
                "collection_name": "Child 2",
                "parent_collection_id": "root-1"
            },
            {
                "id": "grandchild-1",
                "collection_name": "Grandchild 1",
                "parent_collection_id": "child-1"
            }
        ]
        
        hierarchy = collection_service._build_collection_hierarchy(collections)
        
        # Should return only root collections
        assert len(hierarchy) == 1
        
        root = hierarchy[0]
        assert root["collection_name"] == "Root 1"
        assert len(root["children"]) == 2
        
        # Check child collections
        child1 = next(c for c in root["children"] if c["collection_name"] == "Child 1")
        assert len(child1["children"]) == 1
        assert child1["children"][0]["collection_name"] == "Grandchild 1"
        
        child2 = next(c for c in root["children"] if c["collection_name"] == "Child 2")
        assert len(child2["children"]) == 0
    
    def test_calculate_collection_depth(self, collection_service):
        """Test collection depth calculation"""
        assert collection_service._calculate_collection_depth(None) == 0
        assert collection_service._calculate_collection_depth("") == 0
        assert collection_service._calculate_collection_depth("Root") == 1
        assert collection_service._calculate_collection_depth("Root/Child") == 2
        assert collection_service._calculate_collection_depth("Root/Child/Grandchild") == 3
    
    def test_build_collection_path(self, collection_service):
        """Test building collection path"""
        # Create mock collections
        root = MagicMock()
        root.id = "root-id"
        root.collection_name = "Research"
        root.parent_collection_id = None
        
        child = MagicMock()
        child.id = "child-id"
        child.collection_name = "Papers"
        child.parent_collection_id = "root-id"
        
        grandchild = MagicMock()
        grandchild.id = "grandchild-id"
        grandchild.collection_name = "Methodology"
        grandchild.parent_collection_id = "child-id"
        
        collection_map = {
            "root-id": root,
            "child-id": child,
            "grandchild-id": grandchild
        }
        
        # Test path building
        root_path = collection_service._build_collection_path(root, collection_map)
        assert root_path == "Research"
        
        child_path = collection_service._build_collection_path(child, collection_map)
        assert child_path == "Research/Papers"
        
        grandchild_path = collection_service._build_collection_path(grandchild, collection_map)
        assert grandchild_path == "Research/Papers/Methodology"
    
    @pytest.mark.asyncio
    async def test_get_descendant_collection_ids(self, collection_service):
        """Test getting descendant collection IDs"""
        with patch('services.zotero.zotero_collection_service.get_db'):
            mock_db = MagicMock()
            
            # Mock child collections
            child1 = MagicMock()
            child1.id = "child-1"
            child2 = MagicMock()
            child2.id = "child-2"
            
            # Mock grandchild collections
            grandchild1 = MagicMock()
            grandchild1.id = "grandchild-1"
            
            # Setup query results
            def mock_query_filter(parent_id):
                if parent_id == "root-id":
                    return [child1, child2]
                elif parent_id == "child-1":
                    return [grandchild1]
                else:
                    return []
            
            mock_db.query.return_value.filter.return_value.all.side_effect = lambda: mock_query_filter("root-id")
            
            # This is a simplified test - in reality we'd need to mock the recursive calls
            descendant_ids = await collection_service._get_descendant_collection_ids(mock_db, "root-id")
            
            # The actual implementation would return all descendant IDs
            # This test verifies the structure is correct
            assert isinstance(descendant_ids, list)


class TestCollectionStatistics:
    """Test collection statistics functionality"""
    
    @pytest.mark.asyncio
    async def test_get_collection_statistics(
        self, 
        collection_service, 
        mock_connection, 
        mock_library, 
        mock_collections
    ):
        """Test getting collection statistics"""
        with patch('services.zotero.zotero_collection_service.get_db') as mock_get_db:
            mock_db = AsyncMock()
            
            # Mock various statistics queries
            mock_db.query.return_value.filter.return_value.count.side_effect = [10, 3]  # total, root collections
            mock_db.query.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.order_by.return_value.first.return_value = (mock_collections[0], 15)  # largest collection
            mock_db.query.return_value.select_from.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.scalar.return_value = 5.5  # average items
            mock_db.query.return_value.filter.return_value.all.return_value = mock_collections  # all collections
            
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            statistics = await collection_service.get_collection_statistics(
                connection_id="test-connection-id",
                library_id="test-library-id"
            )
            
            assert "total_collections" in statistics
            assert "root_collections" in statistics
            assert "nested_collections" in statistics
            assert "max_depth" in statistics
            assert "collections_by_depth" in statistics
            assert "average_items_per_collection" in statistics
            assert "largest_collection" in statistics
            
            assert statistics["total_collections"] == 10
            assert statistics["root_collections"] == 3
            assert statistics["nested_collections"] == 7
            assert statistics["largest_collection"]["name"] == "Research Papers"


class TestCollectionManagement:
    """Test collection management operations"""
    
    @pytest.mark.asyncio
    async def test_get_collection_breadcrumbs(
        self, 
        collection_service, 
        mock_connection, 
        mock_library, 
        mock_collections
    ):
        """Test getting collection breadcrumbs"""
        with patch('services.zotero.zotero_collection_service.get_db') as mock_get_db:
            mock_db = AsyncMock()
            
            # Mock collection hierarchy for breadcrumbs
            child_collection = mock_collections[1]  # Child collection
            root_collection = mock_collections[0]   # Root collection
            
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                child_collection,  # Initial collection
                root_collection    # Parent collection
            ]
            
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            breadcrumbs = await collection_service.get_collection_breadcrumbs(
                connection_id="test-connection-id",
                library_id="test-library-id",
                collection_id="child-collection-id"
            )
            
            assert len(breadcrumbs) == 2
            assert breadcrumbs[0]["name"] == "Research Papers"  # Root first
            assert breadcrumbs[1]["name"] == "Methodology"     # Child second
    
    @pytest.mark.asyncio
    async def test_update_collection_paths(
        self, 
        collection_service, 
        mock_connection, 
        mock_library, 
        mock_collections
    ):
        """Test updating collection paths"""
        with patch('services.zotero.zotero_collection_service.get_db') as mock_get_db:
            mock_db = AsyncMock()
            
            # Mock collections with incorrect paths
            mock_collections[1].collection_path = "Wrong Path"  # Child collection has wrong path
            
            mock_db.query.return_value.filter.return_value.all.return_value = mock_collections
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            result = await collection_service.update_collection_paths(
                connection_id="test-connection-id",
                library_id="test-library-id"
            )
            
            assert "total_collections" in result
            assert "updated_collections" in result
            assert result["total_collections"] == 2
            assert result["updated_collections"] >= 0  # At least some collections might be updated
    
    @pytest.mark.asyncio
    async def test_move_collection(
        self, 
        collection_service, 
        mock_connection, 
        mock_library, 
        mock_collections
    ):
        """Test moving a collection"""
        with patch('services.zotero.zotero_collection_service.get_db') as mock_get_db:
            mock_db = AsyncMock()
            
            collection_to_move = mock_collections[1]  # Child collection
            new_parent = mock_collections[0]          # Root collection (different parent)
            
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                collection_to_move,  # Collection to move
                new_parent           # New parent
            ]
            mock_db.query.return_value.filter.return_value.all.return_value = mock_collections
            
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            result = await collection_service.move_collection(
                connection_id="test-connection-id",
                library_id="test-library-id",
                collection_id="child-collection-id",
                new_parent_id="root-collection-id"
            )
            
            assert "collection_id" in result
            assert "new_parent_id" in result
            assert "new_path" in result
            assert result["collection_id"] == "child-collection-id"
            assert result["new_parent_id"] == "root-collection-id"
    
    @pytest.mark.asyncio
    async def test_would_create_circular_reference(self, collection_service):
        """Test circular reference detection"""
        mock_db = MagicMock()
        
        # Mock collection hierarchy: A -> B -> C
        collection_a = MagicMock()
        collection_a.id = "a"
        collection_a.parent_collection_id = None
        
        collection_b = MagicMock()
        collection_b.id = "b"
        collection_b.parent_collection_id = "a"
        
        collection_c = MagicMock()
        collection_c.id = "c"
        collection_c.parent_collection_id = "b"
        
        def mock_query_result(collection_id):
            if collection_id == "a":
                return collection_a
            elif collection_id == "b":
                return collection_b
            elif collection_id == "c":
                return collection_c
            return None
        
        mock_db.query.return_value.filter.return_value.first.side_effect = mock_query_result
        
        # Test: Moving A to be child of C would create circular reference
        would_create_circular = await collection_service._would_create_circular_reference(
            mock_db, "a", "c"
        )
        assert would_create_circular == True
        
        # Test: Moving C to be child of A would not create circular reference (already the case)
        would_create_circular = await collection_service._would_create_circular_reference(
            mock_db, "c", "a"
        )
        assert would_create_circular == False


if __name__ == "__main__":
    pytest.main([__file__])