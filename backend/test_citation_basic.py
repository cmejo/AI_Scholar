"""
Basic test script for citation service functionality
"""
import asyncio
from datetime import datetime
from unittest.mock import Mock

# Mock the database dependencies
class MockDB:
    def query(self, *args):
        return self
    
    def filter(self, *args):
        return self
    
    def all(self):
        return []

# Mock ZoteroItem
class MockZoteroItem:
    def __init__(self):
        self.id = "item-1"
        self.library_id = "lib-1"
        self.zotero_item_key = "ABC123"
        self.item_type = "article"
        self.title = "Sample Article Title"
        self.creators = [
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
        ]
        self.publication_title = "Journal of Testing"
        self.publication_year = 2023
        self.publisher = "Test Publisher"
        self.doi = "10.1000/test.doi"
        self.url = "https://example.com/article"
        self.abstract_note = "This is a test article abstract."
        self.is_deleted = False
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

async def test_citation_formatting():
    """Test basic citation formatting functionality"""
    print("Testing citation formatting...")
    
    # Import the service (this will test if imports work)
    try:
        import sys
        sys.path.append('.')
        from services.zotero.zotero_citation_service import ZoteroCitationService
        print("✓ Citation service imported successfully")
    except Exception as e:
        print(f"✗ Failed to import citation service: {e}")
        return False
    
    # Create service instance
    mock_db = MockDB()
    service = ZoteroCitationService(mock_db)
    print("✓ Citation service instance created")
    
    # Test supported styles
    styles = await service.get_supported_styles()
    print(f"✓ Supported styles: {list(styles.keys())}")
    
    # Test supported formats
    formats = await service.get_supported_formats()
    print(f"✓ Supported formats: {formats}")
    
    # Test APA author formatting
    creators = [
        {"creator_type": "author", "first_name": "John", "last_name": "Doe"},
        {"creator_type": "author", "first_name": "Jane", "last_name": "Smith"}
    ]
    apa_authors = service._format_apa_authors(creators)
    print(f"✓ APA authors: {apa_authors}")
    assert apa_authors == "Doe, J. & Smith, J."
    
    # Test MLA author formatting
    mla_authors = service._format_mla_authors(creators)
    print(f"✓ MLA authors: {mla_authors}")
    assert mla_authors == "Doe, John and Smith, Jane"
    
    # Test IEEE author formatting
    ieee_authors = service._format_ieee_authors(creators)
    print(f"✓ IEEE authors: {ieee_authors}")
    assert ieee_authors == "J. Doe, J. Smith"
    
    # Test title formatting
    title_html = service._format_title_italic("Test Title", "html")
    print(f"✓ HTML title: {title_html}")
    assert title_html == "<em>Test Title</em>"
    
    title_rtf = service._format_title_italic("Test Title", "rtf")
    print(f"✓ RTF title: {title_rtf}")
    assert title_rtf == "\\i Test Title\\i0"
    
    # Test citation formatting with mock item
    mock_item = MockZoteroItem()
    
    apa_citation = await service._format_apa_citation(mock_item, "text")
    print(f"✓ APA citation: {apa_citation}")
    assert "Doe, J. & Smith, J." in apa_citation
    assert "(2023)" in apa_citation
    
    mla_citation = await service._format_mla_citation(mock_item, "text")
    print(f"✓ MLA citation: {mla_citation}")
    assert "Doe, John and Smith, Jane" in mla_citation
    
    chicago_citation = await service._format_chicago_citation(mock_item, "text")
    print(f"✓ Chicago citation: {chicago_citation}")
    assert "Doe, J. & Smith, J." in chicago_citation
    
    ieee_citation = await service._format_ieee_citation(mock_item, "text")
    print(f"✓ IEEE citation: {ieee_citation}")
    assert "J. Doe, J. Smith" in ieee_citation
    
    # Test validation
    validation_result = await service.validate_citation_data(mock_item)
    print(f"✓ Validation result: {validation_result}")
    assert validation_result['is_valid'] == True
    
    # Test required fields
    required_fields = service._get_required_fields_by_type("article")
    print(f"✓ Required fields for article: {required_fields}")
    assert "title" in required_fields
    assert "creators" in required_fields
    
    # Test field value checking
    has_title = service._has_field_value(mock_item, "title")
    print(f"✓ Has title: {has_title}")
    assert has_title == True
    
    print("\n🎉 All citation formatting tests passed!")
    return True

async def test_bibliography_functionality():
    """Test bibliography functionality"""
    print("\nTesting bibliography functionality...")
    
    try:
        import sys
        sys.path.append('.')
        from services.zotero.zotero_citation_service import ZoteroCitationService
    except Exception as e:
        print(f"✗ Failed to import citation service: {e}")
        return False
    
    mock_db = MockDB()
    service = ZoteroCitationService(mock_db)
    
    # Test bibliography entry combination
    entries = ["Entry 1", "Entry 2", "Entry 3"]
    
    text_bib = await service._combine_bibliography_entries(entries, "text", "apa")
    print(f"✓ Text bibliography: {text_bib}")
    assert text_bib == "Entry 1\n\nEntry 2\n\nEntry 3"
    
    html_bib = await service._combine_bibliography_entries(entries, "html", "apa")
    print(f"✓ HTML bibliography contains div: {'<div class=\"bibliography\">' in html_bib}")
    assert '<div class="bibliography">' in html_bib
    
    rtf_bib = await service._combine_bibliography_entries(entries, "rtf", "apa")
    print(f"✓ RTF bibliography: {rtf_bib}")
    assert "\\par\n" in rtf_bib
    
    # Test sorting
    mock_items = [MockZoteroItem(), MockZoteroItem()]
    mock_items[0].creators = [{"creator_type": "author", "last_name": "Smith"}]
    mock_items[1].creators = [{"creator_type": "author", "last_name": "Doe"}]
    
    sorted_items = await service._sort_items_for_bibliography(mock_items, "author")
    print(f"✓ Sorted by author: {[service._get_sort_key_author(item) for item in sorted_items]}")
    
    print("🎉 All bibliography tests passed!")
    return True

if __name__ == "__main__":
    async def main():
        success1 = await test_citation_formatting()
        success2 = await test_bibliography_functionality()
        
        if success1 and success2:
            print("\n✅ All tests completed successfully!")
        else:
            print("\n❌ Some tests failed!")
    
    asyncio.run(main())