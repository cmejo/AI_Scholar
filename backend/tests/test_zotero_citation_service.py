"""
Unit tests for Zotero Citation Service

Tests citation generation, bibliography creation, and validation functionality.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from services.zotero.zotero_citation_service import (
    ZoteroCitationService, CitationStyleError, CitationValidationError
)
from models.zotero_models import ZoteroItem, ZoteroCitationStyle, ZoteroUserPreferences
from models.zotero_schemas import CitationRequest, BibliographyRequest


class TestZoteroCitationService:
    """Test cases for ZoteroCitationService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def citation_service(self, mock_db):
        """Citation service instance with mocked database"""
        return ZoteroCitationService(mock_db)
    
    @pytest.fixture
    def sample_item(self):
        """Sample Zotero item for testing"""
        return ZoteroItem(
            id="item-1",
            library_id="lib-1",
            zotero_item_key="ABC123",
            item_type="article",
            title="Sample Article Title",
            creators=[
                {
                    "creator_type": "author",
                    "first_name": "John",
                    "last_name": "Doe"
                },
                {
                    "creator_type": "author",
                    "first_name": "Jane",
                    "last_name": "Smith"
                }
            ],
            publication_title="Journal of Testing",
            publication_year=2023,
            publisher="Test Publisher",
            doi="10.1000/test.doi",
            url="https://example.com/article",
            abstract_note="This is a test article abstract.",
            is_deleted=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.fixture
    def sample_book_item(self):
        """Sample book item for testing"""
        return ZoteroItem(
            id="item-2",
            library_id="lib-1",
            zotero_item_key="DEF456",
            item_type="book",
            title="Sample Book Title",
            creators=[
                {
                    "creator_type": "author",
                    "first_name": "Alice",
                    "last_name": "Johnson"
                }
            ],
            publication_year=2022,
            publisher="Academic Press",
            isbn="978-0123456789",
            is_deleted=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_generate_citations_success(self, citation_service, mock_db, sample_item):
        """Test successful citation generation"""
        # Mock database query
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_item]
        
        # Mock private methods
        citation_service._get_items_by_ids = AsyncMock(return_value=[sample_item])
        citation_service._get_user_preferences = AsyncMock(return_value=None)
        
        result = await citation_service.generate_citations(
            item_ids=["item-1"],
            citation_style="apa",
            format_type="text"
        )
        
        assert result.citations
        assert len(result.citations) == 1
        assert result.style_used == "apa"
        assert result.format == "text"
        assert result.processing_time > 0
        assert "Doe, J." in result.citations[0]
        assert "Smith, J." in result.citations[0]
        assert "2023" in result.citations[0]
    
    @pytest.mark.asyncio
    async def test_generate_citations_invalid_style(self, citation_service):
        """Test citation generation with invalid style"""
        with pytest.raises(CitationValidationError, match="Unsupported citation style"):
            await citation_service.generate_citations(
                item_ids=["item-1"],
                citation_style="invalid_style",
                format_type="text"
            )
    
    @pytest.mark.asyncio
    async def test_generate_citations_invalid_format(self, citation_service):
        """Test citation generation with invalid format"""
        with pytest.raises(CitationValidationError, match="Unsupported format"):
            await citation_service.generate_citations(
                item_ids=["item-1"],
                citation_style="apa",
                format_type="invalid_format"
            )
    
    @pytest.mark.asyncio
    async def test_generate_citations_no_items(self, citation_service):
        """Test citation generation with empty item list"""
        with pytest.raises(CitationValidationError, match="No item IDs provided"):
            await citation_service.generate_citations(
                item_ids=[],
                citation_style="apa",
                format_type="text"
            )
    
    @pytest.mark.asyncio
    async def test_generate_citations_too_many_items(self, citation_service):
        """Test citation generation with too many items"""
        item_ids = [f"item-{i}" for i in range(101)]
        
        with pytest.raises(CitationValidationError, match="Too many items requested"):
            await citation_service.generate_citations(
                item_ids=item_ids,
                citation_style="apa",
                format_type="text"
            )
    
    @pytest.mark.asyncio
    async def test_generate_bibliography_success(self, citation_service, sample_item, sample_book_item):
        """Test successful bibliography generation"""
        items = [sample_item, sample_book_item]
        
        citation_service._get_items_by_ids = AsyncMock(return_value=items)
        citation_service._get_user_preferences = AsyncMock(return_value=None)
        citation_service._sort_items_for_bibliography = AsyncMock(return_value=items)
        
        result = await citation_service.generate_bibliography(
            item_ids=["item-1", "item-2"],
            citation_style="apa",
            format_type="text",
            sort_by="author"
        )
        
        assert result.bibliography
        assert result.item_count == 2
        assert result.style_used == "apa"
        assert result.format == "text"
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_format_citation_apa_article(self, citation_service, sample_item):
        """Test APA citation formatting for article using core engine"""
        citation = await citation_service._format_citation(sample_item, "apa", "text", "en-US")
        
        assert "Doe, J. & Smith, J." in citation
        assert "(2023)" in citation
        assert "Sample Article Title" in citation
        assert "Journal of Testing" in citation
        assert "https://doi.org/10.1000/test.doi" in citation
    
    @pytest.mark.asyncio
    async def test_format_citation_apa_book(self, citation_service, sample_book_item):
        """Test APA citation formatting for book using core engine"""
        citation = await citation_service._format_citation(sample_book_item, "apa", "text", "en-US")
        
        assert "Johnson, A." in citation
        assert "(2022)" in citation
        assert "Sample Book Title" in citation
        assert "Academic Press" in citation
    
    @pytest.mark.asyncio
    async def test_format_citation_mla(self, citation_service, sample_item):
        """Test MLA citation formatting using core engine"""
        citation = await citation_service._format_citation(sample_item, "mla", "text", "en-US")
        
        assert "Doe, John and Smith, Jane" in citation
        assert '"Sample Article Title"' in citation
        assert "Journal of Testing" in citation
        assert "2023" in citation
    
    @pytest.mark.asyncio
    async def test_format_citation_chicago(self, citation_service, sample_item):
        """Test Chicago citation formatting using core engine"""
        citation = await citation_service._format_citation(sample_item, "chicago", "text", "en-US")
        
        assert "Doe, John and Smith, Jane" in citation
        assert "2023" in citation
        assert '"Sample Article Title"' in citation
        assert "Journal of Testing" in citation
        assert "doi:10.1000/test.doi" in citation
    
    @pytest.mark.asyncio
    async def test_format_citation_ieee(self, citation_service, sample_item):
        """Test IEEE citation formatting using core engine"""
        citation = await citation_service._format_citation(sample_item, "ieee", "text", "en-US")
        
        assert "J. Doe, J. Smith" in citation
        assert '"Sample Article Title"' in citation
        assert "Journal of Testing" in citation
        assert "2023" in citation
    
    # Legacy formatting method tests removed - now using CoreCitationEngine
    
    @pytest.mark.asyncio
    async def test_validate_citation_data_valid(self, citation_service, sample_item):
        """Test citation data validation for valid item"""
        result = await citation_service.validate_citation_data(sample_item)
        
        assert result['is_valid'] == True
        assert result['item_type'] == "article"
        assert len(result['missing_fields']) == 0
    
    @pytest.mark.asyncio
    async def test_validate_citation_data_missing_fields(self, citation_service):
        """Test citation data validation with missing fields"""
        item = ZoteroItem(
            id="item-1",
            item_type="article",
            title=None,  # Missing required field
            creators=[],  # Missing required field
            publication_title=None,  # Missing required field
            publication_year=None,  # Missing required field
            is_deleted=False
        )
        
        result = await citation_service.validate_citation_data(item)
        
        assert result['is_valid'] == False
        assert 'title' in result['missing_fields']
        assert 'creators' in result['missing_fields']
        assert 'publication_title' in result['missing_fields']
        assert 'publication_year' in result['missing_fields']
    
    @pytest.mark.asyncio
    async def test_validate_citation_data_warnings(self, citation_service):
        """Test citation data validation with warnings"""
        item = ZoteroItem(
            id="item-1",
            item_type="article",
            title="Test Title",
            creators=[{"creator_type": "author"}],  # Missing name info
            publication_title="Test Journal",
            publication_year=3000,  # Invalid year
            is_deleted=False
        )
        
        result = await citation_service.validate_citation_data(item)
        
        assert len(result['warnings']) > 0
        assert any('Creator missing name' in warning for warning in result['warnings'])
        assert any('Publication year seems invalid' in warning for warning in result['warnings'])
    
    @pytest.mark.asyncio
    async def test_sort_items_by_author(self, citation_service, sample_item, sample_book_item):
        """Test sorting items by author"""
        items = [sample_book_item, sample_item]  # Johnson, Doe
        
        sorted_items = await citation_service._sort_items_for_bibliography(items, "author")
        
        # Should be sorted: Doe, Johnson
        assert sorted_items[0].id == sample_item.id
        assert sorted_items[1].id == sample_book_item.id
    
    @pytest.mark.asyncio
    async def test_sort_items_by_title(self, citation_service, sample_item, sample_book_item):
        """Test sorting items by title"""
        items = [sample_item, sample_book_item]  # "Sample Article", "Sample Book"
        
        sorted_items = await citation_service._sort_items_for_bibliography(items, "title")
        
        # Should be sorted alphabetically by title
        assert sorted_items[0].id == sample_item.id  # "Sample Article" comes first
        assert sorted_items[1].id == sample_book_item.id  # "Sample Book" comes second
    
    @pytest.mark.asyncio
    async def test_sort_items_by_year(self, citation_service, sample_item, sample_book_item):
        """Test sorting items by year"""
        items = [sample_book_item, sample_item]  # 2022, 2023
        
        sorted_items = await citation_service._sort_items_for_bibliography(items, "year")
        
        # Should be sorted by year descending (newest first)
        assert sorted_items[0].id == sample_item.id  # 2023
        assert sorted_items[1].id == sample_book_item.id  # 2022
    
    def test_get_sort_key_author_with_authors(self, citation_service, sample_item):
        """Test getting sort key for item with authors"""
        result = citation_service._get_sort_key_author(sample_item)
        assert result == "doe"
    
    def test_get_sort_key_author_no_authors(self, citation_service):
        """Test getting sort key for item without authors"""
        item = ZoteroItem(id="item-1", creators=[], is_deleted=False)
        result = citation_service._get_sort_key_author(item)
        assert result == "zzz"
    
    def test_get_sort_key_author_organization(self, citation_service):
        """Test getting sort key for organization author"""
        item = ZoteroItem(
            id="item-1",
            creators=[{"creator_type": "author", "name": "World Health Organization"}],
            is_deleted=False
        )
        result = citation_service._get_sort_key_author(item)
        assert result == "world health organization"
    
    @pytest.mark.asyncio
    async def test_combine_bibliography_entries_text(self, citation_service):
        """Test combining bibliography entries in text format"""
        entries = ["Entry 1", "Entry 2", "Entry 3"]
        result = await citation_service._combine_bibliography_entries(entries, "text", "apa")
        
        assert result == "Entry 1\n\nEntry 2\n\nEntry 3"
    
    @pytest.mark.asyncio
    async def test_combine_bibliography_entries_html(self, citation_service):
        """Test combining bibliography entries in HTML format"""
        entries = ["Entry 1", "Entry 2"]
        result = await citation_service._combine_bibliography_entries(entries, "html", "apa")
        
        assert '<div class="bibliography">' in result
        assert '<p class="bibliography-entry">Entry 1</p>' in result
        assert '<p class="bibliography-entry">Entry 2</p>' in result
        assert '</div>' in result
    
    @pytest.mark.asyncio
    async def test_combine_bibliography_entries_rtf(self, citation_service):
        """Test combining bibliography entries in RTF format"""
        entries = ["Entry 1", "Entry 2"]
        result = await citation_service._combine_bibliography_entries(entries, "rtf", "apa")
        
        assert result == "Entry 1\\par\nEntry 2"
    
    # Legacy validation method tests removed - now using CoreCitationEngine
    
    @pytest.mark.asyncio
    async def test_get_supported_styles(self, citation_service):
        """Test getting supported citation styles"""
        styles = await citation_service.get_supported_styles()
        
        assert "apa" in styles
        assert "mla" in styles
        assert "chicago" in styles
        assert "ieee" in styles
        assert len(styles) >= 4
    
    @pytest.mark.asyncio
    async def test_get_supported_formats(self, citation_service):
        """Test getting supported output formats"""
        formats = await citation_service.get_supported_formats()
        
        assert "text" in formats
        assert "html" in formats
        assert "rtf" in formats
        assert len(formats) == 3