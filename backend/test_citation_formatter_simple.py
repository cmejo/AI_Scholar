#!/usr/bin/env python3
"""
Simple test script for citation formatter functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from services.zotero.citation_formatter import (
    CoreCitationEngine, CitationStyleParser, CitationFormatterFactory,
    APAFormatter, MLAFormatter, ChicagoFormatter, IEEEFormatter,
    CitationStyle, OutputFormat, FormattedText, CitationData,
    CitationFormattingError, CitationValidationError
)

# Mock ZoteroItem class for testing
class MockZoteroItem:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'test-item')
        self.library_id = kwargs.get('library_id', 'test-lib')
        self.zotero_item_key = kwargs.get('zotero_item_key', 'TEST123')
        self.item_type = kwargs.get('item_type', 'article')
        self.title = kwargs.get('title', 'Test Article Title')
        self.creators = kwargs.get('creators', [])
        self.publication_title = kwargs.get('publication_title', 'Test Journal')
        self.publication_year = kwargs.get('publication_year', 2023)
        self.publisher = kwargs.get('publisher', 'Test Publisher')
        self.doi = kwargs.get('doi', '10.1000/test.doi')
        self.url = kwargs.get('url', 'https://example.com/article')
        self.abstract_note = kwargs.get('abstract_note', 'Test abstract')
        self.is_deleted = kwargs.get('is_deleted', False)
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())

def test_formatted_text():
    """Test FormattedText functionality"""
    print("Testing FormattedText...")
    
    # Test plain text
    text = FormattedText("Sample Text")
    assert text.to_format(OutputFormat.TEXT) == "Sample Text"
    assert text.to_format(OutputFormat.HTML) == "Sample Text"
    assert text.to_format(OutputFormat.RTF) == "Sample Text"
    
    # Test italic text
    text = FormattedText("Sample Text", is_italic=True)
    assert text.to_format(OutputFormat.TEXT) == "Sample Text"
    assert text.to_format(OutputFormat.HTML) == "<em>Sample Text</em>"
    assert text.to_format(OutputFormat.RTF) == "\\i Sample Text\\i0"
    
    print("✓ FormattedText tests passed")

def test_citation_style_parser():
    """Test CitationStyleParser functionality"""
    print("Testing CitationStyleParser...")
    
    parser = CitationStyleParser()
    
    # Create test item
    item = MockZoteroItem(
        title="Test Article",
        creators=[
            {"creator_type": "author", "first_name": "John", "last_name": "Doe"},
            {"creator_type": "author", "first_name": "Jane", "last_name": "Smith"}
        ],
        publication_title="Test Journal",
        publication_year=2023,
        doi="10.1000/test.doi"
    )
    
    # Test parsing
    citation_data = parser.parse_zotero_item(item)
    assert citation_data.title == "Test Article"
    assert citation_data.publication_title == "Test Journal"
    assert citation_data.publication_year == 2023
    assert citation_data.doi == "10.1000/test.doi"
    assert len(citation_data.authors) == 2
    
    # Test validation
    validation = parser.validate_citation_data(citation_data)
    assert validation['is_valid'] == True
    assert validation['item_type'] == "article"
    
    print("✓ CitationStyleParser tests passed")

def test_apa_formatter():
    """Test APA formatter"""
    print("Testing APA formatter...")
    
    formatter = APAFormatter()
    
    # Create test data
    citation_data = CitationData(
        title="Test Article Title",
        authors=[
            {'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False},
            {'type': 'author', 'first_name': 'Jane', 'last_name': 'Smith', 'is_organization': False}
        ],
        publication_title="Test Journal",
        publication_year=2023,
        doi="10.1000/test.doi",
        item_type="article"
    )
    
    # Test citation formatting
    citation = formatter.format_citation(citation_data, OutputFormat.TEXT)
    assert "Doe, J. & Smith, J." in citation
    assert "(2023)" in citation
    assert "Test Article Title" in citation
    assert "Test Journal" in citation
    assert "https://doi.org/10.1000/test.doi" in citation
    assert citation.endswith('.')
    
    print("✓ APA formatter tests passed")

def test_mla_formatter():
    """Test MLA formatter"""
    print("Testing MLA formatter...")
    
    formatter = MLAFormatter()
    
    # Create test data
    citation_data = CitationData(
        title="Test Article Title",
        authors=[
            {'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False},
            {'type': 'author', 'first_name': 'Jane', 'last_name': 'Smith', 'is_organization': False}
        ],
        publication_title="Test Journal",
        publication_year=2023,
        url="https://example.com/article",
        item_type="article"
    )
    
    # Test citation formatting
    citation = formatter.format_citation(citation_data, OutputFormat.TEXT)
    assert "Doe, John and Smith, Jane" in citation
    assert '"Test Article Title"' in citation
    assert "Test Journal" in citation
    assert "2023" in citation
    assert "Web." in citation
    
    print("✓ MLA formatter tests passed")

def test_chicago_formatter():
    """Test Chicago formatter"""
    print("Testing Chicago formatter...")
    
    formatter = ChicagoFormatter()
    
    # Create test data
    citation_data = CitationData(
        title="Test Article Title",
        authors=[
            {'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False}
        ],
        publication_title="Test Journal",
        publication_year=2023,
        doi="10.1000/test.doi",
        item_type="article"
    )
    
    # Test citation formatting
    citation = formatter.format_citation(citation_data, OutputFormat.TEXT)
    assert "Doe, John" in citation
    assert "2023" in citation
    assert '"Test Article Title"' in citation
    assert "Test Journal" in citation
    assert "doi:10.1000/test.doi" in citation
    
    print("✓ Chicago formatter tests passed")

def test_ieee_formatter():
    """Test IEEE formatter"""
    print("Testing IEEE formatter...")
    
    formatter = IEEEFormatter()
    
    # Create test data
    citation_data = CitationData(
        title="Test Article Title",
        authors=[
            {'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False},
            {'type': 'author', 'first_name': 'Jane', 'last_name': 'Smith', 'is_organization': False}
        ],
        publication_title="Test Journal",
        publication_year=2023,
        item_type="article"
    )
    
    # Test citation formatting
    citation = formatter.format_citation(citation_data, OutputFormat.TEXT)
    assert "J. Doe, J. Smith" in citation
    assert '"Test Article Title"' in citation
    assert "Test Journal" in citation
    assert "2023" in citation
    
    print("✓ IEEE formatter tests passed")

def test_citation_formatter_factory():
    """Test CitationFormatterFactory"""
    print("Testing CitationFormatterFactory...")
    
    # Test creating formatters
    apa_formatter = CitationFormatterFactory.create_formatter(CitationStyle.APA)
    assert isinstance(apa_formatter, APAFormatter)
    
    mla_formatter = CitationFormatterFactory.create_formatter(CitationStyle.MLA)
    assert isinstance(mla_formatter, MLAFormatter)
    
    chicago_formatter = CitationFormatterFactory.create_formatter(CitationStyle.CHICAGO)
    assert isinstance(chicago_formatter, ChicagoFormatter)
    
    ieee_formatter = CitationFormatterFactory.create_formatter(CitationStyle.IEEE)
    assert isinstance(ieee_formatter, IEEEFormatter)
    
    # Test supported styles
    styles = CitationFormatterFactory.get_supported_styles()
    assert CitationStyle.APA in styles
    assert CitationStyle.MLA in styles
    assert CitationStyle.CHICAGO in styles
    assert CitationStyle.IEEE in styles
    
    print("✓ CitationFormatterFactory tests passed")

def test_core_citation_engine():
    """Test CoreCitationEngine"""
    print("Testing CoreCitationEngine...")
    
    engine = CoreCitationEngine()
    
    # Create test item
    item = MockZoteroItem(
        title="Test Article",
        creators=[
            {"creator_type": "author", "first_name": "John", "last_name": "Doe"}
        ],
        publication_title="Test Journal",
        publication_year=2023,
        doi="10.1000/test.doi"
    )
    
    # Test APA citation
    citation = engine.format_citation(item, CitationStyle.APA, OutputFormat.TEXT)
    assert "Doe, J." in citation
    assert "(2023)" in citation
    assert "Test Article" in citation
    assert "Test Journal" in citation
    assert "https://doi.org/10.1000/test.doi" in citation
    
    # Test MLA citation
    citation = engine.format_citation(item, CitationStyle.MLA, OutputFormat.TEXT)
    assert "Doe, John" in citation
    assert '"Test Article"' in citation
    assert "Test Journal" in citation
    assert "2023" in citation
    
    # Test bibliography entry
    entry = engine.format_bibliography_entry(item, CitationStyle.APA, OutputFormat.TEXT)
    assert "Doe, J." in entry
    assert "(2023)" in entry
    
    # Test validation
    validation = engine.validate_item_for_citation(item)
    assert validation['is_valid'] == True
    
    # Test supported styles and formats
    styles = engine.get_supported_styles()
    assert "apa" in styles
    assert "mla" in styles
    assert "chicago" in styles
    assert "ieee" in styles
    
    formats = engine.get_supported_formats()
    assert "text" in formats
    assert "html" in formats
    assert "rtf" in formats
    
    print("✓ CoreCitationEngine tests passed")

def test_html_formatting():
    """Test HTML output formatting"""
    print("Testing HTML formatting...")
    
    engine = CoreCitationEngine()
    
    # Create book item to test italic formatting
    item = MockZoteroItem(
        title="Test Book Title",
        creators=[
            {"creator_type": "author", "first_name": "John", "last_name": "Doe"}
        ],
        publisher="Test Publisher",
        publication_year=2022,
        item_type="book"
    )
    
    # Test HTML formatting
    citation = engine.format_citation(item, CitationStyle.APA, OutputFormat.HTML)
    assert "<em>Test Book Title</em>" in citation
    
    print("✓ HTML formatting tests passed")

def test_validation_edge_cases():
    """Test validation edge cases"""
    print("Testing validation edge cases...")
    
    parser = CitationStyleParser()
    
    # Test missing required fields
    citation_data = CitationData(
        title=None,  # Missing
        authors=[],  # Missing
        publication_title=None,  # Missing for article
        publication_year=None,  # Missing for article
        item_type="article"
    )
    
    validation = parser.validate_citation_data(citation_data)
    assert validation['is_valid'] == False
    assert 'title' in validation['missing_fields']
    assert 'authors' in validation['missing_fields']
    assert 'publication_title' in validation['missing_fields']
    assert 'publication_year' in validation['missing_fields']
    
    # Test warnings
    citation_data = CitationData(
        title="Test Title",
        authors=[{'type': 'author', 'is_organization': False}],  # Missing name
        publication_title="Test Journal",
        publication_year=3000,  # Invalid year
        item_type="article"
    )
    
    validation = parser.validate_citation_data(citation_data)
    assert len(validation['warnings']) > 0
    
    print("✓ Validation edge cases tests passed")

def run_all_tests():
    """Run all tests"""
    print("Running Citation Formatter Tests...")
    print("=" * 50)
    
    try:
        test_formatted_text()
        test_citation_style_parser()
        test_apa_formatter()
        test_mla_formatter()
        test_chicago_formatter()
        test_ieee_formatter()
        test_citation_formatter_factory()
        test_core_citation_engine()
        test_html_formatting()
        test_validation_edge_cases()
        
        print("=" * 50)
        print("✅ All tests passed successfully!")
        print("Citation formatting engine is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)