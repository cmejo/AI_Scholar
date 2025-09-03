"""
Unit tests for Zotero Search Service

Tests advanced search functionality including full-text search,
faceted search, relevance scoring, and similarity search.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from models.zotero_models import ZoteroItem, ZoteroLibrary, ZoteroConnection
from models.zotero_schemas import ZoteroSearchRequest, ZoteroCreator
from services.zotero.zotero_search_service import ZoteroSearchService


class TestZoteroSearchService:
    """Test suite for ZoteroSearchService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def search_service(self, mock_db):
        """Search service instance with mocked database"""
        return ZoteroSearchService(mock_db)
    
    @pytest.fixture
    def sample_search_request(self):
        """Sample search request"""
        return ZoteroSearchRequest(
            query="machine learning",
            library_id=None,
            collection_id=None,
            item_type=None,
            tags=[],
            creators=[],
            publication_year_start=None,
            publication_year_end=None,
            limit=20,
            offset=0,
            sort_by="relevance",
            sort_order="desc"
        )
    
    @pytest.fixture
    def sample_references(self):
        """Sample reference items for testing"""
        return [
            ZoteroItem(
                id="ref-1",
                library_id="lib-123",
                zotero_item_key="item-1",
                item_type="article",
                title="Machine Learning in Healthcare",
                creators=[{
                    "creator_type": "author",
                    "first_name": "John",
                    "last_name": "Doe"
                }],
                publication_title="AI Journal",
                publication_year=2023,
                doi="10.1000/ml.healthcare",
                abstract_note="This paper discusses machine learning applications in healthcare.",
                tags=["machine learning", "healthcare", "AI"],
                is_deleted=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            ZoteroItem(
                id="ref-2",
                library_id="lib-123",
                zotero_item_key="item-2",
                item_type="book",
                title="Deep Learning Fundamentals",
                creators=[{
                    "creator_type": "author",
                    "first_name": "Jane",
                    "last_name": "Smith"
                }],
                publication_title="Tech Publishers",
                publication_year=2022,
                publisher="Tech Publishers",
                tags=["deep learning", "neural networks"],
                is_deleted=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            ZoteroItem(
                id="ref-3",
                library_id="lib-123",
                zotero_item_key="item-3",
                item_type="article",
                title="Natural Language Processing Applications",
                creators=[{
                    "creator_type": "author",
                    "first_name": "Bob",
                    "last_name": "Johnson"
                }],
                publication_title="NLP Conference",
                publication_year=2023,
                tags=["NLP", "text processing"],
                is_deleted=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
    
    # Search Tests
    
    @pytest.mark.asyncio
    async def test_search_references_basic(
        self, search_service, mock_db, sample_search_request, sample_references
    ):
        """Test basic search functionality"""
        # Mock the query chain
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.count.return_value = len(sample_references)
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_references
        
        mock_db.query.return_value = mock_query
        
        result = await search_service.search_references(
            user_id="user-123",
            search_request=sample_search_request
        )
        
        assert result.total_count == 3
        assert len(result.items) == 3
        assert result.query == "machine learning"
        assert result.processing_time > 0
        assert "sort_by" in result.filters_applied
    
    @pytest.mark.asyncio
    async def test_search_with_filters(
        self, search_service, mock_db, sample_references
    ):
        """Test search with various filters"""
        filtered_request = ZoteroSearchRequest(
            query="machine learning",
            item_type="article",
            tags=["AI"],
            publication_year_start=2023,
            publication_year_end=2023,
            limit=10,
            offset=0,
            sort_by="publication_year",
            sort_order="desc"
        )
        
        # Mock the query chain
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_references[0]]  # Only the first one matches
        
        mock_db.query.return_value = mock_query
        
        result = await search_service.search_references(
            user_id="user-123",
            search_request=filtered_request
        )
        
        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.filters_applied["item_type"] == "article"
        assert result.filters_applied["tags"] == ["AI"]
        assert result.filters_applied["publication_year_start"] == 2023
        assert result.filters_applied["publication_year_end"] == 2023
    
    @pytest.mark.asyncio
    async def test_search_empty_query(
        self, search_service, mock_db, sample_references
    ):
        """Test search with empty query"""
        empty_request = ZoteroSearchRequest(
            query="",
            limit=20,
            offset=0,
            sort_by="date_modified",
            sort_order="desc"
        )
        
        # Mock the query chain
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.count.return_value = len(sample_references)
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_references
        
        mock_db.query.return_value = mock_query
        
        result = await search_service.search_references(
            user_id="user-123",
            search_request=empty_request
        )
        
        assert result.total_count == 3
        assert len(result.items) == 3
        assert result.query == ""
    
    # Facets Tests
    
    @pytest.mark.asyncio
    async def test_get_search_facets(
        self, search_service, mock_db, sample_references
    ):
        """Test search facets calculation"""
        # Mock the query chain
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.all.return_value = sample_references
        
        mock_db.query.return_value = mock_query
        
        facets = await search_service.get_search_facets(user_id="user-123")
        
        assert "item_types" in facets
        assert "publication_years" in facets
        assert "creators" in facets
        assert "tags" in facets
        assert "publishers" in facets
        
        # Check item type facets
        item_types = facets["item_types"]
        assert len(item_types) == 2  # article and book
        assert any(facet["value"] == "article" and facet["count"] == 2 for facet in item_types)
        assert any(facet["value"] == "book" and facet["count"] == 1 for facet in item_types)
        
        # Check year facets
        years = facets["publication_years"]
        assert any(facet["value"] == 2023 and facet["count"] == 2 for facet in years)
        assert any(facet["value"] == 2022 and facet["count"] == 1 for facet in years)
    
    @pytest.mark.asyncio
    async def test_get_search_facets_with_filters(
        self, search_service, mock_db, sample_references
    ):
        """Test search facets with library filter"""
        # Mock the query chain
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.all.return_value = sample_references
        
        mock_db.query.return_value = mock_query
        
        facets = await search_service.get_search_facets(
            user_id="user-123",
            library_id="lib-123"
        )
        
        assert "item_types" in facets
        assert "publication_years" in facets
        assert "creators" in facets
        assert "tags" in facets
        assert "publishers" in facets
    
    # Suggestions Tests
    
    @pytest.mark.asyncio
    async def test_suggest_search_terms(
        self, search_service, mock_db, sample_references
    ):
        """Test search term suggestions"""
        # Mock the query chain for different searches
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_references
        
        mock_db.query.return_value = mock_query
        
        suggestions = await search_service.suggest_search_terms(
            user_id="user-123",
            partial_query="machine",
            limit=10
        )
        
        assert isinstance(suggestions, list)
        assert "machine" in " ".join(suggestions).lower() or "Machine" in " ".join(suggestions)
    
    @pytest.mark.asyncio
    async def test_suggest_search_terms_short_query(
        self, search_service, mock_db
    ):
        """Test search suggestions with short query"""
        suggestions = await search_service.suggest_search_terms(
            user_id="user-123",
            partial_query="a",  # Too short
            limit=10
        )
        
        assert suggestions == []
    
    # Similarity Tests
    
    @pytest.mark.asyncio
    async def test_get_similar_references(
        self, search_service, mock_db, sample_references
    ):
        """Test finding similar references"""
        target_ref = sample_references[0]  # Machine Learning in Healthcare
        
        # Mock getting the target reference
        mock_target_query = Mock()
        mock_target_query.join.return_value = mock_target_query
        mock_target_query.filter.return_value = mock_target_query
        mock_target_query.first.return_value = target_ref
        
        # Mock getting similar references
        mock_similar_query = Mock()
        mock_similar_query.join.return_value = mock_similar_query
        mock_similar_query.filter.return_value = mock_similar_query
        mock_similar_query.options.return_value = mock_similar_query
        mock_similar_query.order_by.return_value = mock_similar_query
        mock_similar_query.limit.return_value = mock_similar_query
        mock_similar_query.all.return_value = [sample_references[2]]  # Similar article
        
        mock_db.query.side_effect = [mock_target_query, mock_similar_query]
        
        similar_refs = await search_service.get_similar_references(
            user_id="user-123",
            reference_id="ref-1",
            limit=10
        )
        
        assert isinstance(similar_refs, list)
        assert len(similar_refs) <= 10
    
    @pytest.mark.asyncio
    async def test_get_similar_references_not_found(
        self, search_service, mock_db
    ):
        """Test similarity search when target reference not found"""
        # Mock query to return None
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        mock_db.query.return_value = mock_query
        
        similar_refs = await search_service.get_similar_references(
            user_id="user-123",
            reference_id="nonexistent",
            limit=10
        )
        
        assert similar_refs == []
    
    # Helper Method Tests
    
    def test_calculate_item_type_facets(self, search_service, sample_references):
        """Test item type facet calculation"""
        facets = search_service._calculate_item_type_facets(sample_references)
        
        assert len(facets) == 2
        assert any(facet["value"] == "article" and facet["count"] == 2 for facet in facets)
        assert any(facet["value"] == "book" and facet["count"] == 1 for facet in facets)
        
        # Should be sorted by count (descending)
        assert facets[0]["count"] >= facets[1]["count"]
    
    def test_calculate_year_facets(self, search_service, sample_references):
        """Test publication year facet calculation"""
        facets = search_service._calculate_year_facets(sample_references)
        
        assert len(facets) == 2
        assert any(facet["value"] == 2023 and facet["count"] == 2 for facet in facets)
        assert any(facet["value"] == 2022 and facet["count"] == 1 for facet in facets)
        
        # Should be sorted by year (descending)
        assert facets[0]["value"] >= facets[1]["value"]
    
    def test_calculate_creator_facets(self, search_service, sample_references):
        """Test creator facet calculation"""
        facets = search_service._calculate_creator_facets(sample_references)
        
        assert len(facets) == 3
        creator_names = [facet["value"] for facet in facets]
        assert "John Doe" in creator_names
        assert "Jane Smith" in creator_names
        assert "Bob Johnson" in creator_names
    
    def test_calculate_tag_facets(self, search_service, sample_references):
        """Test tag facet calculation"""
        facets = search_service._calculate_tag_facets(sample_references)
        
        # Should include all unique tags
        tag_values = [facet["value"] for facet in facets]
        assert "machine learning" in tag_values
        assert "healthcare" in tag_values
        assert "AI" in tag_values
        assert "deep learning" in tag_values
        assert "neural networks" in tag_values
        assert "NLP" in tag_values
        assert "text processing" in tag_values
    
    def test_calculate_publisher_facets(self, search_service, sample_references):
        """Test publisher facet calculation"""
        facets = search_service._calculate_publisher_facets(sample_references)
        
        assert len(facets) == 1  # Only one item has a publisher
        assert facets[0]["value"] == "Tech Publishers"
        assert facets[0]["count"] == 1
    
    def test_convert_to_response(self, search_service, sample_references):
        """Test conversion to response format"""
        reference = sample_references[0]
        response = search_service._convert_to_response(reference)
        
        assert response.id == reference.id
        assert response.title == reference.title
        assert response.item_type == reference.item_type
        assert len(response.creators) == 1
        assert response.creators[0].creator_type == "author"
        assert response.creators[0].first_name == "John"
        assert response.creators[0].last_name == "Doe"
        assert response.publication_year == reference.publication_year
        assert response.doi == reference.doi
        assert "machine learning" in response.tags
    
    # Error Handling Tests
    
    @pytest.mark.asyncio
    async def test_search_database_error(
        self, search_service, mock_db, sample_search_request
    ):
        """Test search with database error"""
        # Mock database to raise an error
        mock_db.query.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception, match="Database connection failed"):
            await search_service.search_references(
                user_id="user-123",
                search_request=sample_search_request
            )
    
    @pytest.mark.asyncio
    async def test_facets_database_error(self, search_service, mock_db):
        """Test facets with database error"""
        # Mock database to raise an error
        mock_db.query.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception, match="Database connection failed"):
            await search_service.get_search_facets(user_id="user-123")
    
    # Integration Tests
    
    @pytest.mark.asyncio
    async def test_search_with_pagination(
        self, search_service, mock_db, sample_references
    ):
        """Test search with pagination"""
        paginated_request = ZoteroSearchRequest(
            query="machine learning",
            limit=2,
            offset=1,
            sort_by="title",
            sort_order="asc"
        )
        
        # Mock the query chain
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_references[1:3]  # Skip first, take 2
        
        mock_db.query.return_value = mock_query
        
        result = await search_service.search_references(
            user_id="user-123",
            search_request=paginated_request
        )
        
        assert result.total_count == 3
        assert len(result.items) == 2
        assert result.filters_applied["limit"] == 2
        assert result.filters_applied["offset"] == 1


if __name__ == "__main__":
    pytest.main([__file__])