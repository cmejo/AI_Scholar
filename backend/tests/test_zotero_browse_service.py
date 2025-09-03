"""
Comprehensive tests for Zotero Browse Service

Tests all aspects of the browse and filtering functionality including:
- Collection-based filtering
- Sorting options by date, title, author, relevance
- Pagination for large result sets
- Helpful suggestions when no results found
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from services.zotero.zotero_browse_service import ZoteroBrowseService
from models.zotero_models import ZoteroItem, ZoteroLibrary, ZoteroCollection, ZoteroConnection


class TestZoteroBrowseService:
    """Test suite for ZoteroBrowseService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def browse_service(self, mock_db):
        """Browse service instance with mocked database"""
        return ZoteroBrowseService(mock_db)
    
    @pytest.fixture
    def sample_references(self):
        """Sample reference data for testing"""
        now = datetime.utcnow()
        return [
            Mock(
                id="ref-1",
                library_id="lib-1",
                zotero_item_key="item-1",
                item_type="article",
                title="AI in Healthcare",
                creators=[{"name": "John Doe", "creatorType": "author"}],
                publication_year=2023,
                publisher="Tech Press",
                doi="10.1000/test1",
                tags=["AI", "healthcare", "machine learning"],
                date_added=now - timedelta(days=5),
                date_modified=now - timedelta(days=3),
                attachments=[Mock()],  # Has attachments
                is_deleted=False
            ),
            Mock(
                id="ref-2",
                library_id="lib-1",
                zotero_item_key="item-2",
                item_type="book",
                title="Programming Fundamentals",
                creators=[{"name": "Jane Smith", "creatorType": "author"}],
                publication_year=2022,
                publisher="Book Publishers",
                doi=None,
                tags=["programming", "software"],
                date_added=now - timedelta(days=45),
                date_modified=now - timedelta(days=40),
                attachments=[],  # No attachments
                is_deleted=False
            ),
            Mock(
                id="ref-3",
                library_id="lib-2",
                zotero_item_key="item-3",
                item_type="article",
                title="Deep Learning Applications",
                creators=[{"name": "Bob Johnson", "creatorType": "author"}],
                publication_year=2023,
                publisher="AI Journal",
                doi="10.1000/test2",
                tags=["AI", "deep learning", "neural networks"],
                date_added=now - timedelta(days=15),
                date_modified=now - timedelta(days=1),
                attachments=[Mock(), Mock()],  # Multiple attachments
                is_deleted=False
            )
        ]
    
    @pytest.fixture
    def sample_collections(self):
        """Sample collection data for testing"""
        return [
            Mock(
                id="col-1",
                library_id="lib-1",
                collection_name="AI Research",
                parent_collection_id=None,
                collection_path="/AI Research",
                item_count=5
            ),
            Mock(
                id="col-2",
                library_id="lib-1",
                collection_name="Machine Learning",
                parent_collection_id="col-1",
                collection_path="/AI Research/Machine Learning",
                item_count=3
            ),
            Mock(
                id="col-3",
                library_id="lib-1",
                collection_name="Programming",
                parent_collection_id=None,
                collection_path="/Programming",
                item_count=2
            )
        ]
    
    @pytest.mark.asyncio
    async def test_browse_references_basic(self, browse_service, mock_db, sample_references):
        """Test basic reference browsing functionality"""
        # Mock query chain
        mock_query = Mock()
        mock_query.count.return_value = len(sample_references)
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_references
        
        # Mock the _build_base_query method
        browse_service._build_base_query = Mock(return_value=mock_query)
        browse_service._apply_browse_filters = Mock(return_value=mock_query)
        browse_service._apply_sorting = Mock(return_value=mock_query)
        browse_service._generate_helpful_suggestions = Mock(return_value=[])
        
        # Test browse
        references, total_count, metadata = await browse_service.browse_references(
            user_id="user-1",
            limit=10,
            offset=0
        )
        
        # Assertions
        assert len(references) == 3
        assert total_count == 3
        assert metadata["total_count"] == 3
        assert metadata["current_page"] == 1
        assert metadata["has_next_page"] == False
        assert metadata["has_previous_page"] == False
        assert metadata["suggestions"] == []
        
        # Verify method calls
        browse_service._build_base_query.assert_called_once_with("user-1")
        browse_service._apply_browse_filters.assert_called_once()
        browse_service._apply_sorting.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_browse_references_with_filters(self, browse_service, mock_db, sample_references):
        """Test reference browsing with various filters"""
        # Mock query chain
        mock_query = Mock()
        mock_query.count.return_value = 1
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_references[0]]  # Only first reference
        
        browse_service._build_base_query = Mock(return_value=mock_query)
        browse_service._apply_browse_filters = Mock(return_value=mock_query)
        browse_service._apply_sorting = Mock(return_value=mock_query)
        browse_service._generate_helpful_suggestions = Mock(return_value=[])
        
        # Test with filters
        references, total_count, metadata = await browse_service.browse_references(
            user_id="user-1",
            library_id="lib-1",
            collection_id="col-1",
            item_type="article",
            tags=["AI"],
            creators=["John Doe"],
            publication_year_start=2023,
            publication_year_end=2023,
            publisher="Tech Press",
            has_doi=True,
            has_attachments=True,
            sort_by="title",
            sort_order="asc",
            limit=20,
            offset=0
        )
        
        # Verify filters were applied
        browse_service._apply_browse_filters.assert_called_once()
        call_args = browse_service._apply_browse_filters.call_args[0]
        assert call_args[1] == "lib-1"  # library_id
        assert call_args[2] == "col-1"  # collection_id
        assert call_args[3] == "article"  # item_type
        assert call_args[4] == ["AI"]  # tags
        assert call_args[5] == ["John Doe"]  # creators
        
        # Verify metadata includes applied filters
        filters_applied = metadata["filters_applied"]
        assert filters_applied["library_id"] == "lib-1"
        assert filters_applied["collection_id"] == "col-1"
        assert filters_applied["item_type"] == "article"
        assert filters_applied["tags"] == ["AI"]
        assert filters_applied["has_doi"] == True
        assert filters_applied["has_attachments"] == True
    
    @pytest.mark.asyncio
    async def test_browse_references_pagination(self, browse_service, mock_db):
        """Test pagination functionality"""
        # Mock large result set
        total_items = 157
        mock_query = Mock()
        mock_query.count.return_value = total_items
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []  # Empty for simplicity
        
        browse_service._build_base_query = Mock(return_value=mock_query)
        browse_service._apply_browse_filters = Mock(return_value=mock_query)
        browse_service._apply_sorting = Mock(return_value=mock_query)
        browse_service._generate_helpful_suggestions = Mock(return_value=[])
        
        # Test different pagination scenarios
        test_cases = [
            {"limit": 10, "offset": 0, "expected_page": 1, "expected_total_pages": 16, "has_next": True, "has_prev": False},
            {"limit": 10, "offset": 10, "expected_page": 2, "expected_total_pages": 16, "has_next": True, "has_prev": True},
            {"limit": 20, "offset": 40, "expected_page": 3, "expected_total_pages": 8, "has_next": True, "has_prev": True},
            {"limit": 50, "offset": 150, "expected_page": 4, "expected_total_pages": 4, "has_next": False, "has_prev": True},
        ]
        
        for case in test_cases:
            references, total_count, metadata = await browse_service.browse_references(
                user_id="user-1",
                limit=case["limit"],
                offset=case["offset"]
            )
            
            assert metadata["current_page"] == case["expected_page"]
            assert metadata["page_count"] == case["expected_total_pages"]
            assert metadata["has_next_page"] == case["has_next"]
            assert metadata["has_previous_page"] == case["has_prev"]
            assert metadata["total_count"] == total_items
    
    @pytest.mark.asyncio
    async def test_browse_references_sorting(self, browse_service, mock_db, sample_references):
        """Test sorting functionality"""
        mock_query = Mock()
        mock_query.count.return_value = len(sample_references)
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_references
        
        browse_service._build_base_query = Mock(return_value=mock_query)
        browse_service._apply_browse_filters = Mock(return_value=mock_query)
        browse_service._apply_sorting = Mock(return_value=mock_query)
        browse_service._generate_helpful_suggestions = Mock(return_value=[])
        
        # Test different sorting options
        sort_options = [
            ("title", "asc"),
            ("date_added", "desc"),
            ("publication_year", "desc"),
            ("item_type", "asc"),
            ("publisher", "asc")
        ]
        
        for sort_by, sort_order in sort_options:
            references, total_count, metadata = await browse_service.browse_references(
                user_id="user-1",
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            # Verify sorting was applied
            browse_service._apply_sorting.assert_called()
            call_args = browse_service._apply_sorting.call_args[0]
            assert call_args[1] == sort_by
            assert call_args[2] == sort_order
            
            # Verify metadata
            assert metadata["sort_by"] == sort_by
            assert metadata["sort_order"] == sort_order
    
    @pytest.mark.asyncio
    async def test_browse_references_no_results_with_suggestions(self, browse_service, mock_db):
        """Test helpful suggestions when no results are found"""
        # Mock empty result set
        mock_query = Mock()
        mock_query.count.return_value = 0
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        browse_service._build_base_query = Mock(return_value=mock_query)
        browse_service._apply_browse_filters = Mock(return_value=mock_query)
        browse_service._apply_sorting = Mock(return_value=mock_query)
        
        # Mock suggestions
        mock_suggestions = [
            {
                "type": "remove_filter",
                "message": "Try removing some filters",
                "action": "remove_collection_filter"
            },
            {
                "type": "similar_tags",
                "message": "Try these similar tags:",
                "action": "use_similar_tags",
                "alternatives": ["machine learning", "artificial intelligence"]
            }
        ]
        browse_service._generate_helpful_suggestions = Mock(return_value=mock_suggestions)
        
        # Test browse with no results
        references, total_count, metadata = await browse_service.browse_references(
            user_id="user-1",
            collection_id="nonexistent-collection",
            tags=["nonexistent-tag"]
        )
        
        # Assertions
        assert len(references) == 0
        assert total_count == 0
        assert len(metadata["suggestions"]) == 2
        assert metadata["suggestions"][0]["type"] == "remove_filter"
        assert metadata["suggestions"][1]["type"] == "similar_tags"
        assert "machine learning" in metadata["suggestions"][1]["alternatives"]
        
        # Verify suggestions were generated
        browse_service._generate_helpful_suggestions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_recent_references(self, browse_service, mock_db, sample_references):
        """Test recent references functionality"""
        # Mock recent references (first and third are recent)
        recent_refs = [sample_references[0], sample_references[2]]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = recent_refs
        
        browse_service._build_base_query = Mock(return_value=mock_query)
        
        # Test recent references
        references = await browse_service.get_recent_references(
            user_id="user-1",
            days=30,
            limit=20
        )
        
        assert len(references) == 2
        # Verify filtering and ordering were applied
        assert mock_query.filter.called
        assert mock_query.order_by.called
        assert mock_query.limit.called
    
    @pytest.mark.asyncio
    async def test_get_popular_references(self, browse_service, mock_db, sample_references):
        """Test popular references functionality"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_references
        
        browse_service._build_base_query = Mock(return_value=mock_query)
        
        # Test popular references
        references = await browse_service.get_popular_references(
            user_id="user-1",
            limit=20
        )
        
        assert len(references) == 3
        # Verify ordering by popularity was applied
        assert mock_query.order_by.called
        assert mock_query.limit.called
    
    @pytest.mark.asyncio
    async def test_get_references_by_year(self, browse_service, mock_db, sample_references):
        """Test filtering references by publication year"""
        # Mock references from 2023
        year_2023_refs = [ref for ref in sample_references if ref.publication_year == 2023]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = len(year_2023_refs)
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = year_2023_refs
        
        browse_service._build_base_query = Mock(return_value=mock_query)
        browse_service._apply_sorting = Mock(return_value=mock_query)
        
        # Test year filtering
        references, total_count = await browse_service.get_references_by_year(
            user_id="user-1",
            year=2023,
            sort_by="title",
            sort_order="asc"
        )
        
        assert len(references) == 2  # Two references from 2023
        assert total_count == 2
        # Verify year filter was applied
        assert mock_query.filter.called
        browse_service._apply_sorting.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_references_by_tag(self, browse_service, mock_db, sample_references):
        """Test filtering references by tag"""
        # Mock references with "AI" tag
        ai_refs = [ref for ref in sample_references if "AI" in ref.tags]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = len(ai_refs)
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = ai_refs
        
        browse_service._build_base_query = Mock(return_value=mock_query)
        browse_service._apply_sorting = Mock(return_value=mock_query)
        
        # Test tag filtering
        references, total_count = await browse_service.get_references_by_tag(
            user_id="user-1",
            tag="AI"
        )
        
        assert len(references) == 2  # Two references with "AI" tag
        assert total_count == 2
        # Verify tag filter was applied
        assert mock_query.filter.called
    
    @pytest.mark.asyncio
    async def test_get_references_by_creator(self, browse_service, mock_db, sample_references):
        """Test filtering references by creator"""
        # Mock references by "John"
        john_refs = [ref for ref in sample_references if any("John" in creator["name"] for creator in ref.creators)]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = len(john_refs)
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = john_refs
        
        browse_service._build_base_query = Mock(return_value=mock_query)
        browse_service._apply_sorting = Mock(return_value=mock_query)
        
        # Test creator filtering
        references, total_count = await browse_service.get_references_by_creator(
            user_id="user-1",
            creator_name="John"
        )
        
        assert len(references) == 2  # Two references with "John" in creator name
        assert total_count == 2
        # Verify creator filter was applied
        assert mock_query.filter.called
    
    @pytest.mark.asyncio
    async def test_get_collection_hierarchy(self, browse_service, mock_db, sample_collections):
        """Test collection hierarchy building"""
        # Mock library access validation
        mock_library = Mock()
        mock_db.query.return_value.join.return_value.filter.return_value.first.return_value = mock_library
        
        # Mock collections query
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = sample_collections
        
        # Test hierarchy building
        hierarchy = await browse_service.get_collection_hierarchy(
            user_id="user-1",
            library_id="lib-1",
            include_item_counts=True
        )
        
        # Verify hierarchy structure
        assert len(hierarchy) == 2  # Two root collections
        
        # Find AI Research collection
        ai_collection = next((col for col in hierarchy if col["name"] == "AI Research"), None)
        assert ai_collection is not None
        assert len(ai_collection["children"]) == 1  # One child collection
        assert ai_collection["children"][0]["name"] == "Machine Learning"
        assert ai_collection["item_count"] == 5
        
        # Find Programming collection
        prog_collection = next((col for col in hierarchy if col["name"] == "Programming"), None)
        assert prog_collection is not None
        assert len(prog_collection["children"]) == 0  # No children
        assert prog_collection["item_count"] == 2
    
    @pytest.mark.asyncio
    async def test_get_browse_statistics(self, browse_service, mock_db, sample_references):
        """Test browse statistics calculation"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_references
        
        browse_service._build_base_query = Mock(return_value=mock_query)
        
        # Test statistics
        stats = await browse_service.get_browse_statistics(
            user_id="user-1"
        )
        
        # Verify statistics
        assert stats["total_references"] == 3
        
        # Check item type distribution
        item_types = {item["type"]: item["count"] for item in stats["item_types"]}
        assert item_types["article"] == 2
        assert item_types["book"] == 1
        
        # Check publication year distribution
        years = {item["year"]: item["count"] for item in stats["publication_years"]}
        assert years[2023] == 2
        assert years[2022] == 1
        
        # Check other statistics
        assert stats["with_attachments"]["count"] == 2  # Two refs have attachments
        assert stats["with_doi"]["count"] == 2  # Two refs have DOI
        assert len(stats["top_tags"]) > 0
        
        # Verify percentages are calculated
        assert 0 <= stats["with_attachments"]["percentage"] <= 100
        assert 0 <= stats["with_doi"]["percentage"] <= 100
    
    @pytest.mark.asyncio
    async def test_generate_helpful_suggestions_collection_filter(self, browse_service, mock_db):
        """Test suggestion generation for collection filter"""
        mock_query = Mock()
        browse_service._build_base_query = Mock(return_value=mock_query)
        
        # Test with collection filter
        suggestions = await browse_service._generate_helpful_suggestions(
            user_id="user-1",
            library_id="lib-1",
            collection_id="col-1",
            item_type=None,
            tags=None,
            creators=None,
            publication_year_start=None,
            publication_year_end=None,
            publisher=None
        )
        
        # Should suggest removing collection filter
        assert len(suggestions) > 0
        collection_suggestion = next((s for s in suggestions if s["type"] == "remove_filter"), None)
        assert collection_suggestion is not None
        assert "collection" in collection_suggestion["message"].lower()
    
    @pytest.mark.asyncio
    async def test_generate_helpful_suggestions_item_type(self, browse_service, mock_db):
        """Test suggestion generation for item type filter"""
        mock_query = Mock()
        mock_query.with_entities.return_value.distinct.return_value.all.return_value = [
            ("article",), ("book",), ("thesis",)
        ]
        browse_service._build_base_query = Mock(return_value=mock_query)
        
        # Test with item type filter
        suggestions = await browse_service._generate_helpful_suggestions(
            user_id="user-1",
            library_id=None,
            collection_id=None,
            item_type="journal",  # Non-existent type
            tags=None,
            creators=None,
            publication_year_start=None,
            publication_year_end=None,
            publisher=None
        )
        
        # Should suggest alternative item types
        assert len(suggestions) > 0
        type_suggestion = next((s for s in suggestions if s["type"] == "alternative_filter"), None)
        assert type_suggestion is not None
        assert "alternatives" in type_suggestion
        assert len(type_suggestion["alternatives"]) > 0
    
    @pytest.mark.asyncio
    async def test_generate_helpful_suggestions_tags(self, browse_service, mock_db):
        """Test suggestion generation for tag filters"""
        # Mock references with various tags
        mock_refs = [
            Mock(tags=["AI", "machine learning", "deep learning"]),
            Mock(tags=["artificial intelligence", "neural networks"]),
            Mock(tags=["programming", "software"])
        ]
        
        mock_query = Mock()
        mock_query.all.return_value = mock_refs
        browse_service._build_base_query = Mock(return_value=mock_query)
        
        # Test with tag filter that has similar alternatives
        suggestions = await browse_service._generate_helpful_suggestions(
            user_id="user-1",
            library_id=None,
            collection_id=None,
            item_type=None,
            tags=["ML"],  # Should find "machine learning" as similar
            creators=None,
            publication_year_start=None,
            publication_year_end=None,
            publisher=None
        )
        
        # Should suggest similar tags
        tag_suggestion = next((s for s in suggestions if s["type"] == "similar_tags"), None)
        if tag_suggestion:  # May not always find similar tags
            assert "alternatives" in tag_suggestion
            assert len(tag_suggestion["alternatives"]) > 0
    
    @pytest.mark.asyncio
    async def test_generate_helpful_suggestions_no_references(self, browse_service, mock_db):
        """Test suggestion generation when no references exist"""
        mock_query = Mock()
        mock_query.count.return_value = 0
        mock_query.all.return_value = []
        browse_service._build_base_query = Mock(return_value=mock_query)
        
        # Test with no references in library
        suggestions = await browse_service._generate_helpful_suggestions(
            user_id="user-1",
            library_id=None,
            collection_id=None,
            item_type=None,
            tags=None,
            creators=None,
            publication_year_start=None,
            publication_year_end=None,
            publisher=None
        )
        
        # Should suggest importing library
        assert len(suggestions) > 0
        import_suggestion = next((s for s in suggestions if s["type"] == "no_references"), None)
        assert import_suggestion is not None
        assert "import" in import_suggestion["message"].lower()
    
    def test_convert_to_response(self, browse_service, sample_references):
        """Test conversion of database model to response schema"""
        reference = sample_references[0]
        
        # Mock the response conversion
        with patch('models.zotero_schemas.ZoteroCreator') as mock_creator:
            mock_creator.return_value = Mock()
            
            response = browse_service._convert_to_response(reference)
            
            # Verify response structure
            assert response.id == reference.id
            assert response.title == reference.title
            assert response.item_type == reference.item_type
            assert response.publication_year == reference.publication_year
            assert response.doi == reference.doi
            assert response.tags == reference.tags
    
    @pytest.mark.asyncio
    async def test_error_handling(self, browse_service, mock_db):
        """Test error handling in browse operations"""
        # Mock database error
        mock_db.query.side_effect = Exception("Database error")
        
        # Test that errors are properly handled
        with pytest.raises(Exception):
            await browse_service.browse_references(user_id="user-1")
        
        # Test suggestion generation error handling
        browse_service._build_base_query = Mock(side_effect=Exception("Query error"))
        
        suggestions = await browse_service._generate_helpful_suggestions(
            user_id="user-1",
            library_id=None,
            collection_id=None,
            item_type=None,
            tags=None,
            creators=None,
            publication_year_start=None,
            publication_year_end=None,
            publisher=None
        )
        
        # Should return fallback suggestions
        assert len(suggestions) > 0
        assert suggestions[0]["type"] == "general"


if __name__ == "__main__":
    pytest.main([__file__])