#!/usr/bin/env python3
"""
Test script to verify the updated citation service works with the core citation engine
"""
import sys
import os
from datetime import datetime
from unittest.mock import Mock

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock the database and logging dependencies
class MockLogger:
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

class MockSession:
    def query(self, *args): return self
    def filter(self, *args): return self
    def all(self): return []
    def first(self): return None

# Mock the imports that cause issues
sys.modules['core.logging_config'] = Mock()
sys.modules['core.logging_config'].get_logger = Mock(return_value=MockLogger())
sys.modules['core.database'] = Mock()
sys.modules['models.zotero_models'] = Mock()
sys.modules['models.zotero_schemas'] = Mock()

# Now import our citation service
from services.zotero.zotero_citation_service import ZoteroCitationService, CitationStyleError, CitationValidationError

# Mock ZoteroItem class
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

async def test_citation_service():
    """Test the updated citation service"""
    print("Testing Updated Citation Service...")
    print("=" * 50)
    
    # Create mock database session
    mock_db = MockSession()
    
    # Create citation service
    citation_service = ZoteroCitationService(mock_db)
    
    # Create test item
    test_item = MockZoteroItem(
        title="Machine Learning in Academic Research",
        creators=[
            {"creator_type": "author", "first_name": "Sarah", "last_name": "Johnson"},
            {"creator_type": "author", "first_name": "Michael", "last_name": "Chen"}
        ],
        publication_title="Journal of Computer Science",
        publication_year=2023,
        doi="10.1000/jcs.2023.123"
    )
    
    # Test APA citation formatting
    print("Testing APA citation formatting...")
    apa_citation = await citation_service._format_citation(test_item, "apa", "text", "en-US")
    print(f"APA Citation: {apa_citation}")
    
    assert "Johnson, S. & Chen, M." in apa_citation
    assert "(2023)" in apa_citation
    assert "Machine Learning in Academic Research" in apa_citation
    assert "Journal of Computer Science" in apa_citation
    assert "https://doi.org/10.1000/jcs.2023.123" in apa_citation
    print("✓ APA citation test passed")
    
    # Test MLA citation formatting
    print("\nTesting MLA citation formatting...")
    mla_citation = await citation_service._format_citation(test_item, "mla", "text", "en-US")
    print(f"MLA Citation: {mla_citation}")
    
    assert "Johnson, Sarah and Chen, Michael" in mla_citation
    assert '"Machine Learning in Academic Research"' in mla_citation
    assert "Journal of Computer Science" in mla_citation
    assert "2023" in mla_citation
    print("✓ MLA citation test passed")
    
    # Test Chicago citation formatting
    print("\nTesting Chicago citation formatting...")
    chicago_citation = await citation_service._format_citation(test_item, "chicago", "text", "en-US")
    print(f"Chicago Citation: {chicago_citation}")
    
    assert "Johnson, Sarah and Chen, Michael" in chicago_citation
    assert "2023" in chicago_citation
    assert '"Machine Learning in Academic Research"' in chicago_citation
    assert "Journal of Computer Science" in chicago_citation
    print("✓ Chicago citation test passed")
    
    # Test IEEE citation formatting
    print("\nTesting IEEE citation formatting...")
    ieee_citation = await citation_service._format_citation(test_item, "ieee", "text", "en-US")
    print(f"IEEE Citation: {ieee_citation}")
    
    assert "S. Johnson, M. Chen" in ieee_citation
    assert '"Machine Learning in Academic Research"' in ieee_citation
    assert "Journal of Computer Science" in ieee_citation
    assert "2023" in ieee_citation
    print("✓ IEEE citation test passed")
    
    # Test bibliography entry formatting
    print("\nTesting bibliography entry formatting...")
    bib_entry = await citation_service._format_bibliography_entry(test_item, "apa", "text")
    print(f"Bibliography Entry: {bib_entry}")
    
    assert "Johnson, S. & Chen, M." in bib_entry
    assert "(2023)" in bib_entry
    print("✓ Bibliography entry test passed")
    
    # Test citation validation
    print("\nTesting citation validation...")
    validation = await citation_service.validate_citation_data(test_item)
    print(f"Validation Result: {validation}")
    
    assert validation['is_valid'] == True
    assert validation['item_type'] == "article"
    assert len(validation['missing_fields']) == 0
    print("✓ Citation validation test passed")
    
    # Test HTML formatting
    print("\nTesting HTML formatting...")
    book_item = MockZoteroItem(
        title="Advanced Citation Formatting",
        creators=[
            {"creator_type": "author", "first_name": "Robert", "last_name": "Williams"}
        ],
        publisher="Academic Press",
        publication_year=2022,
        item_type="book"
    )
    
    html_citation = await citation_service._format_citation(book_item, "apa", "html", "en-US")
    print(f"HTML Citation: {html_citation}")
    
    assert "Williams, R." in html_citation
    assert "(2022)" in html_citation
    assert "<em>Advanced Citation Formatting</em>" in html_citation
    assert "Academic Press" in html_citation
    print("✓ HTML formatting test passed")
    
    # Test error handling
    print("\nTesting error handling...")
    try:
        await citation_service._format_citation(test_item, "invalid_style", "text", "en-US")
        assert False, "Should have raised an error"
    except CitationStyleError as e:
        print(f"Expected error caught: {str(e)}")
        print("✓ Error handling test passed")
    
    print("\n" + "=" * 50)
    print("✅ All citation service tests passed!")
    print("The updated citation service is working correctly with the core citation engine.")
    
    return True

async def main():
    """Main test function"""
    try:
        success = await test_citation_service()
        return success
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1)