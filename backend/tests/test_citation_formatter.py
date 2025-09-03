"""
Unit tests for Citation Formatter

Tests the core citation formatting engine including style parsers,
formatters, and validation functionality.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock

from services.zotero.citation_formatter import (
    CoreCitationEngine, CitationStyleParser, CitationFormatterFactory,
    APAFormatter, MLAFormatter, ChicagoFormatter, IEEEFormatter,
    CitationStyle, OutputFormat, FormattedText, CitationData,
    CitationFormattingError, CitationValidationError
)
from models.zotero_models import ZoteroItem


class TestFormattedText:
    """Test cases for FormattedText class"""
    
    def test_formatted_text_plain(self):
        """Test plain text formatting"""
        text = FormattedText("Sample Text")
        assert text.to_format(OutputFormat.TEXT) == "Sample Text"
        assert text.to_format(OutputFormat.HTML) == "Sample Text"
        assert text.to_format(OutputFormat.RTF) == "Sample Text"
    
    def test_formatted_text_italic(self):
        """Test italic text formatting"""
        text = FormattedText("Sample Text", is_italic=True)
        assert text.to_format(OutputFormat.TEXT) == "Sample Text"
        assert text.to_format(OutputFormat.HTML) == "<em>Sample Text</em>"
        assert text.to_format(OutputFormat.RTF) == "\\i Sample Text\\i0"
    
    def test_formatted_text_bold(self):
        """Test bold text formatting"""
        text = FormattedText("Sample Text", is_bold=True)
        assert text.to_format(OutputFormat.TEXT) == "Sample Text"
        assert text.to_format(OutputFormat.HTML) == "<strong>Sample Text</strong>"
        assert text.to_format(OutputFormat.RTF) == "\\b Sample Text\\b0"
    
    def test_formatted_text_underlined(self):
        """Test underlined text formatting"""
        text = FormattedText("Sample Text", is_underlined=True)
        assert text.to_format(OutputFormat.TEXT) == "Sample Text"
        assert text.to_format(OutputFormat.HTML) == "<u>Sample Text</u>"
        assert text.to_format(OutputFormat.RTF) == "\\ul Sample Text\\ul0"
    
    def test_formatted_text_combined(self):
        """Test combined text formatting"""
        text = FormattedText("Sample Text", is_italic=True, is_bold=True)
        assert text.to_format(OutputFormat.HTML) == "<strong><em>Sample Text</em></strong>"
        assert text.to_format(OutputFormat.RTF) == "\\b \\i Sample Text\\i0\\b0"


class TestCitationStyleParser:
    """Test cases for CitationStyleParser"""
    
    @pytest.fixture
    def parser(self):
        """Citation style parser instance"""
        return CitationStyleParser()
    
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
    
    def test_parse_zotero_item_success(self, parser, sample_item):
        """Test successful parsing of Zotero item"""
        citation_data = parser.parse_zotero_item(sample_item)
        
        assert citation_data.title == "Sample Article Title"
        assert citation_data.publication_title == "Journal of Testing"
        assert citation_data.publication_year == 2023
        assert citation_data.doi == "10.1000/test.doi"
        assert citation_data.url == "https://example.com/article"
        assert citation_data.item_type == "article"
        assert len(citation_data.authors) == 2
        
        # Check author parsing
        assert citation_data.authors[0]['first_name'] == "John"
        assert citation_data.authors[0]['last_name'] == "Doe"
        assert citation_data.authors[0]['type'] == "author"
        assert citation_data.authors[0]['is_organization'] == False
    
    def test_parse_creators_individual(self, parser):
        """Test parsing individual creators"""
        creators = [
            {"creator_type": "author", "first_name": "John", "last_name": "Doe"},
            {"creator_type": "editor", "first_name": "Jane", "last_name": "Smith"}
        ]
        
        parsed = parser._parse_creators(creators)
        
        assert len(parsed) == 2
        assert parsed[0]['type'] == "author"
        assert parsed[0]['first_name'] == "John"
        assert parsed[0]['last_name'] == "Doe"
        assert parsed[0]['is_organization'] == False
        
        assert parsed[1]['type'] == "editor"
        assert parsed[1]['first_name'] == "Jane"
        assert parsed[1]['last_name'] == "Smith"
        assert parsed[1]['is_organization'] == False
    
    def test_parse_creators_organization(self, parser):
        """Test parsing organizational creators"""
        creators = [
            {"creator_type": "author", "name": "World Health Organization"}
        ]
        
        parsed = parser._parse_creators(creators)
        
        assert len(parsed) == 1
        assert parsed[0]['type'] == "author"
        assert parsed[0]['name'] == "World Health Organization"
        assert parsed[0]['is_organization'] == True
    
    def test_parse_creators_mixed(self, parser):
        """Test parsing mixed individual and organizational creators"""
        creators = [
            {"creator_type": "author", "first_name": "John", "last_name": "Doe"},
            {"creator_type": "author", "name": "World Health Organization"}
        ]
        
        parsed = parser._parse_creators(creators)
        
        assert len(parsed) == 2
        assert parsed[0]['is_organization'] == False
        assert parsed[1]['is_organization'] == True
    
    def test_clean_text_normal(self, parser):
        """Test text cleaning with normal text"""
        result = parser._clean_text("Normal text")
        assert result == "Normal text"
    
    def test_clean_text_whitespace(self, parser):
        """Test text cleaning with extra whitespace"""
        result = parser._clean_text("  Text  with   extra   spaces  ")
        assert result == "Text with extra spaces"
    
    def test_clean_text_html(self, parser):
        """Test text cleaning with HTML tags"""
        result = parser._clean_text("Text with <em>HTML</em> tags")
        assert result == "Text with HTML tags"
    
    def test_clean_text_empty(self, parser):
        """Test text cleaning with empty/None values"""
        assert parser._clean_text(None) is None
        assert parser._clean_text("") is None
        assert parser._clean_text("   ") is None
    
    def test_validate_citation_data_valid(self, parser, sample_item):
        """Test validation of valid citation data"""
        citation_data = parser.parse_zotero_item(sample_item)
        validation = parser.validate_citation_data(citation_data)
        
        assert validation['is_valid'] == True
        assert validation['item_type'] == "article"
        assert len(validation['missing_fields']) == 0
    
    def test_validate_citation_data_missing_fields(self, parser):
        """Test validation with missing required fields"""
        citation_data = CitationData(
            title=None,  # Missing required field
            authors=[],  # Missing required field
            publication_title=None,  # Missing required field for article
            publication_year=None,  # Missing required field for article
            item_type="article"
        )
        
        validation = parser.validate_citation_data(citation_data)
        
        assert validation['is_valid'] == False
        assert 'title' in validation['missing_fields']
        assert 'authors' in validation['missing_fields']
        assert 'publication_title' in validation['missing_fields']
        assert 'publication_year' in validation['missing_fields']
    
    def test_validate_citation_data_warnings(self, parser):
        """Test validation with warnings"""
        citation_data = CitationData(
            title="Test Title",
            authors=[{'type': 'author', 'is_organization': False}],  # Missing name
            publication_title="Test Journal",
            publication_year=3000,  # Invalid year
            item_type="article"
        )
        
        validation = parser.validate_citation_data(citation_data)
        
        assert len(validation['warnings']) > 0
        assert any('Publication year' in warning for warning in validation['warnings'])
    
    def test_has_valid_field_value_string(self, parser):
        """Test field value validation for strings"""
        data = CitationData(title="Valid Title")
        assert parser._has_valid_field_value(data, 'title') == True
        
        data = CitationData(title="")
        assert parser._has_valid_field_value(data, 'title') == False
        
        data = CitationData(title=None)
        assert parser._has_valid_field_value(data, 'title') == False
    
    def test_has_valid_field_value_list(self, parser):
        """Test field value validation for lists"""
        data = CitationData(authors=[{'name': 'Author'}])
        assert parser._has_valid_field_value(data, 'authors') == True
        
        data = CitationData(authors=[])
        assert parser._has_valid_field_value(data, 'authors') == False


class TestAPAFormatter:
    """Test cases for APA formatter"""
    
    @pytest.fixture
    def formatter(self):
        """APA formatter instance"""
        return APAFormatter()
    
    @pytest.fixture
    def article_data(self):
        """Sample article citation data"""
        return CitationData(
            title="Sample Article Title",
            authors=[
                {'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False},
                {'type': 'author', 'first_name': 'Jane', 'last_name': 'Smith', 'is_organization': False}
            ],
            publication_title="Journal of Testing",
            publication_year=2023,
            doi="10.1000/test.doi",
            item_type="article"
        )
    
    @pytest.fixture
    def book_data(self):
        """Sample book citation data"""
        return CitationData(
            title="Sample Book Title",
            authors=[
                {'type': 'author', 'first_name': 'Alice', 'last_name': 'Johnson', 'is_organization': False}
            ],
            publisher="Academic Press",
            publication_year=2022,
            item_type="book"
        )
    
    def test_format_citation_article(self, formatter, article_data):
        """Test APA citation formatting for article"""
        citation = formatter.format_citation(article_data, OutputFormat.TEXT)
        
        assert "Doe, J. & Smith, J." in citation
        assert "(2023)" in citation
        assert "Sample Article Title" in citation
        assert "Journal of Testing" in citation
        assert "https://doi.org/10.1000/test.doi" in citation
        assert citation.endswith('.')
    
    def test_format_citation_book(self, formatter, book_data):
        """Test APA citation formatting for book"""
        citation = formatter.format_citation(book_data, OutputFormat.TEXT)
        
        assert "Johnson, A." in citation
        assert "(2022)" in citation
        assert "Sample Book Title" in citation  # Should be italicized in HTML/RTF
        assert "Academic Press" in citation
        assert citation.endswith('.')
    
    def test_format_citation_html(self, formatter, book_data):
        """Test APA citation formatting with HTML output"""
        citation = formatter.format_citation(book_data, OutputFormat.HTML)
        
        assert "<em>Sample Book Title</em>" in citation
    
    def test_format_author_names_single(self, formatter):
        """Test APA author formatting with single author"""
        authors = [{'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False}]
        result = formatter._format_author_names(authors, False)
        assert result.text == "Doe, J."
    
    def test_format_author_names_two(self, formatter):
        """Test APA author formatting with two authors"""
        authors = [
            {'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False},
            {'type': 'author', 'first_name': 'Jane', 'last_name': 'Smith', 'is_organization': False}
        ]
        result = formatter._format_author_names(authors, False)
        assert result.text == "Doe, J. & Smith, J."
    
    def test_format_author_names_multiple(self, formatter):
        """Test APA author formatting with multiple authors"""
        authors = [
            {'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False},
            {'type': 'author', 'first_name': 'Jane', 'last_name': 'Smith', 'is_organization': False},
            {'type': 'author', 'first_name': 'Bob', 'last_name': 'Johnson', 'is_organization': False}
        ]
        result = formatter._format_author_names(authors, False)
        assert result.text == "Doe, J., Smith, J., & Johnson, B."
    
    def test_format_author_names_organization(self, formatter):
        """Test APA author formatting with organization"""
        authors = [{'type': 'author', 'name': 'World Health Organization', 'is_organization': True}]
        result = formatter._format_author_names(authors, False)
        assert result.text == "World Health Organization"
    
    def test_format_author_names_truncated(self, formatter):
        """Test APA author formatting with truncation"""
        authors = [
            {'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False}
        ]
        result = formatter._format_author_names(authors, True)
        assert result.text == "Doe, J., et al."


class TestMLAFormatter:
    """Test cases for MLA formatter"""
    
    @pytest.fixture
    def formatter(self):
        """MLA formatter instance"""
        return MLAFormatter()
    
    @pytest.fixture
    def article_data(self):
        """Sample article citation data"""
        return CitationData(
            title="Sample Article Title",
            authors=[
                {'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False},
                {'type': 'author', 'first_name': 'Jane', 'last_name': 'Smith', 'is_organization': False}
            ],
            publication_title="Journal of Testing",
            publication_year=2023,
            url="https://example.com/article",
            item_type="article"
        )
    
    def test_format_citation_article(self, formatter, article_data):
        """Test MLA citation formatting for article"""
        citation = formatter.format_citation(article_data, OutputFormat.TEXT)
        
        assert "Doe, John and Smith, Jane" in citation
        assert '"Sample Article Title"' in citation
        assert "Journal of Testing" in citation
        assert "2023" in citation
        assert "Web." in citation
        assert citation.endswith('.')
    
    def test_format_author_names_single(self, formatter):
        """Test MLA author formatting with single author"""
        authors = [{'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False}]
        result = formatter._format_author_names(authors, False)
        assert result.text == "Doe, John"
    
    def test_format_author_names_two(self, formatter):
        """Test MLA author formatting with two authors"""
        authors = [
            {'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False},
            {'type': 'author', 'first_name': 'Jane', 'last_name': 'Smith', 'is_organization': False}
        ]
        result = formatter._format_author_names(authors, False)
        assert result.text == "Doe, John and Smith, Jane"
    
    def test_format_author_names_multiple(self, formatter):
        """Test MLA author formatting with multiple authors"""
        authors = [
            {'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False},
            {'type': 'author', 'first_name': 'Jane', 'last_name': 'Smith', 'is_organization': False},
            {'type': 'author', 'first_name': 'Bob', 'last_name': 'Johnson', 'is_organization': False}
        ]
        result = formatter._format_author_names(authors, False)
        assert result.text == "Doe, John, Smith, Jane, and Johnson, Bob"


class TestChicagoFormatter:
    """Test cases for Chicago formatter"""
    
    @pytest.fixture
    def formatter(self):
        """Chicago formatter instance"""
        return ChicagoFormatter()
    
    @pytest.fixture
    def article_data(self):
        """Sample article citation data"""
        return CitationData(
            title="Sample Article Title",
            authors=[
                {'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False}
            ],
            publication_title="Journal of Testing",
            publication_year=2023,
            doi="10.1000/test.doi",
            item_type="article"
        )
    
    def test_format_citation_article(self, formatter, article_data):
        """Test Chicago citation formatting for article"""
        citation = formatter.format_citation(article_data, OutputFormat.TEXT)
        
        assert "Doe, John" in citation
        assert "2023" in citation
        assert '"Sample Article Title"' in citation
        assert "Journal of Testing" in citation
        assert "doi:10.1000/test.doi" in citation
        assert citation.endswith('.')


class TestIEEEFormatter:
    """Test cases for IEEE formatter"""
    
    @pytest.fixture
    def formatter(self):
        """IEEE formatter instance"""
        return IEEEFormatter()
    
    @pytest.fixture
    def article_data(self):
        """Sample article citation data"""
        return CitationData(
            title="Sample Article Title",
            authors=[
                {'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False},
                {'type': 'author', 'first_name': 'Jane', 'last_name': 'Smith', 'is_organization': False}
            ],
            publication_title="Journal of Testing",
            publication_year=2023,
            item_type="article"
        )
    
    def test_format_citation_article(self, formatter, article_data):
        """Test IEEE citation formatting for article"""
        citation = formatter.format_citation(article_data, OutputFormat.TEXT)
        
        assert "J. Doe, J. Smith" in citation
        assert '"Sample Article Title"' in citation
        assert "Journal of Testing" in citation
        assert "2023" in citation
        assert citation.endswith('.')
    
    def test_format_author_names_ieee(self, formatter):
        """Test IEEE author formatting"""
        authors = [
            {'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False},
            {'type': 'author', 'first_name': 'Jane', 'last_name': 'Smith', 'is_organization': False}
        ]
        result = formatter._format_author_names(authors, False)
        assert result.text == "J. Doe, J. Smith"


class TestCitationFormatterFactory:
    """Test cases for CitationFormatterFactory"""
    
    def test_create_formatter_apa(self):
        """Test creating APA formatter"""
        formatter = CitationFormatterFactory.create_formatter(CitationStyle.APA)
        assert isinstance(formatter, APAFormatter)
        assert formatter.style == CitationStyle.APA
    
    def test_create_formatter_mla(self):
        """Test creating MLA formatter"""
        formatter = CitationFormatterFactory.create_formatter(CitationStyle.MLA)
        assert isinstance(formatter, MLAFormatter)
        assert formatter.style == CitationStyle.MLA
    
    def test_create_formatter_chicago(self):
        """Test creating Chicago formatter"""
        formatter = CitationFormatterFactory.create_formatter(CitationStyle.CHICAGO)
        assert isinstance(formatter, ChicagoFormatter)
        assert formatter.style == CitationStyle.CHICAGO
    
    def test_create_formatter_ieee(self):
        """Test creating IEEE formatter"""
        formatter = CitationFormatterFactory.create_formatter(CitationStyle.IEEE)
        assert isinstance(formatter, IEEEFormatter)
        assert formatter.style == CitationStyle.IEEE
    
    def test_get_supported_styles(self):
        """Test getting supported styles"""
        styles = CitationFormatterFactory.get_supported_styles()
        assert CitationStyle.APA in styles
        assert CitationStyle.MLA in styles
        assert CitationStyle.CHICAGO in styles
        assert CitationStyle.IEEE in styles
        assert len(styles) >= 4


class TestCoreCitationEngine:
    """Test cases for CoreCitationEngine"""
    
    @pytest.fixture
    def engine(self):
        """Core citation engine instance"""
        return CoreCitationEngine()
    
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
                }
            ],
            publication_title="Journal of Testing",
            publication_year=2023,
            doi="10.1000/test.doi",
            is_deleted=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def test_format_citation_apa(self, engine, sample_item):
        """Test citation formatting with APA style"""
        citation = engine.format_citation(sample_item, CitationStyle.APA, OutputFormat.TEXT)
        
        assert "Doe, J." in citation
        assert "(2023)" in citation
        assert "Sample Article Title" in citation
        assert "Journal of Testing" in citation
        assert "https://doi.org/10.1000/test.doi" in citation
        assert citation.endswith('.')
    
    def test_format_citation_mla(self, engine, sample_item):
        """Test citation formatting with MLA style"""
        citation = engine.format_citation(sample_item, CitationStyle.MLA, OutputFormat.TEXT)
        
        assert "Doe, John" in citation
        assert '"Sample Article Title"' in citation
        assert "Journal of Testing" in citation
        assert "2023" in citation
    
    def test_format_citation_html(self, engine, sample_item):
        """Test citation formatting with HTML output"""
        # Create a book item to test italic formatting
        sample_item.item_type = "book"
        citation = engine.format_citation(sample_item, CitationStyle.APA, OutputFormat.HTML)
        
        assert "<em>Sample Article Title</em>" in citation
    
    def test_format_bibliography_entry(self, engine, sample_item):
        """Test bibliography entry formatting"""
        entry = engine.format_bibliography_entry(sample_item, CitationStyle.APA, OutputFormat.TEXT)
        
        assert "Doe, J." in entry
        assert "(2023)" in entry
        assert "Sample Article Title" in entry
        assert entry.endswith('.')
    
    def test_validate_item_for_citation_valid(self, engine, sample_item):
        """Test validation of valid item"""
        validation = engine.validate_item_for_citation(sample_item)
        
        assert validation['is_valid'] == True
        assert validation['item_type'] == "article"
        assert len(validation['missing_fields']) == 0
    
    def test_validate_item_for_citation_invalid(self, engine):
        """Test validation of invalid item"""
        invalid_item = ZoteroItem(
            id="item-1",
            item_type="article",
            title=None,  # Missing required field
            creators=[],  # Missing required field
            publication_title=None,  # Missing required field
            publication_year=None,  # Missing required field
            is_deleted=False
        )
        
        validation = engine.validate_item_for_citation(invalid_item)
        
        assert validation['is_valid'] == False
        assert len(validation['missing_fields']) > 0
    
    def test_get_supported_styles(self, engine):
        """Test getting supported styles"""
        styles = engine.get_supported_styles()
        
        assert "apa" in styles
        assert "mla" in styles
        assert "chicago" in styles
        assert "ieee" in styles
        assert len(styles) >= 4
    
    def test_get_supported_formats(self, engine):
        """Test getting supported formats"""
        formats = engine.get_supported_formats()
        
        assert "text" in formats
        assert "html" in formats
        assert "rtf" in formats
        assert len(formats) == 3
    
    def test_format_citation_error_handling(self, engine):
        """Test error handling in citation formatting"""
        # Create an item that will cause parsing errors
        invalid_item = Mock()
        invalid_item.id = "invalid-item"
        invalid_item.title = None
        invalid_item.creators = "invalid_creators"  # Should be list
        
        with pytest.raises(CitationFormattingError):
            engine.format_citation(invalid_item, CitationStyle.APA, OutputFormat.TEXT)


class TestCitationValidation:
    """Test cases for citation validation"""
    
    @pytest.fixture
    def parser(self):
        """Citation style parser instance"""
        return CitationStyleParser()
    
    def test_validation_article_complete(self, parser):
        """Test validation of complete article"""
        data = CitationData(
            title="Complete Article",
            authors=[{'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False}],
            publication_title="Test Journal",
            publication_year=2023,
            item_type="article"
        )
        
        validation = parser.validate_citation_data(data)
        assert validation['is_valid'] == True
        assert len(validation['missing_fields']) == 0
    
    def test_validation_book_complete(self, parser):
        """Test validation of complete book"""
        data = CitationData(
            title="Complete Book",
            authors=[{'type': 'author', 'first_name': 'Jane', 'last_name': 'Smith', 'is_organization': False}],
            publisher="Test Publisher",
            publication_year=2022,
            item_type="book"
        )
        
        validation = parser.validate_citation_data(data)
        assert validation['is_valid'] == True
        assert len(validation['missing_fields']) == 0
    
    def test_validation_webpage_complete(self, parser):
        """Test validation of complete webpage"""
        data = CitationData(
            title="Web Page Title",
            url="https://example.com",
            item_type="webpage"
        )
        
        validation = parser.validate_citation_data(data)
        assert validation['is_valid'] == True
        assert len(validation['missing_fields']) == 0
    
    def test_validation_missing_title(self, parser):
        """Test validation with missing title"""
        data = CitationData(
            title=None,
            authors=[{'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False}],
            publication_title="Test Journal",
            publication_year=2023,
            item_type="article"
        )
        
        validation = parser.validate_citation_data(data)
        assert validation['is_valid'] == False
        assert 'title' in validation['missing_fields']
    
    def test_validation_missing_authors(self, parser):
        """Test validation with missing authors"""
        data = CitationData(
            title="Test Article",
            authors=[],
            publication_title="Test Journal",
            publication_year=2023,
            item_type="article"
        )
        
        validation = parser.validate_citation_data(data)
        assert validation['is_valid'] == False
        assert 'authors' in validation['missing_fields']
    
    def test_validation_warnings_invalid_year(self, parser):
        """Test validation warnings for invalid year"""
        data = CitationData(
            title="Test Article",
            authors=[{'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False}],
            publication_title="Test Journal",
            publication_year=3000,  # Invalid year
            item_type="article"
        )
        
        validation = parser.validate_citation_data(data)
        assert len(validation['warnings']) > 0
        assert any('Publication year' in warning for warning in validation['warnings'])
    
    def test_validation_warnings_missing_doi(self, parser):
        """Test validation warnings for missing DOI in article"""
        data = CitationData(
            title="Test Article",
            authors=[{'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False}],
            publication_title="Test Journal",
            publication_year=2023,
            doi=None,
            url=None,
            item_type="article"
        )
        
        validation = parser.validate_citation_data(data)
        assert any('missing DOI or URL' in warning for warning in validation['warnings'])