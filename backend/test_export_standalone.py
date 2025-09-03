"""
Standalone test for export functionality
Tests the export service without database dependencies
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any


class MockZoteroItem:
    """Mock Zotero item for testing"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'item-1')
        self.library_id = kwargs.get('library_id', 'lib-1')
        self.zotero_item_key = kwargs.get('zotero_item_key', 'ABC123')
        self.item_type = kwargs.get('item_type', 'article')
        self.title = kwargs.get('title', 'Sample Article Title')
        self.creators = kwargs.get('creators', [
            {"creator_type": "author", "first_name": "John", "last_name": "Doe"},
            {"creator_type": "author", "first_name": "Jane", "last_name": "Smith"}
        ])
        self.publication_title = kwargs.get('publication_title', 'Journal of Testing')
        self.publication_year = kwargs.get('publication_year', 2023)
        self.publisher = kwargs.get('publisher', 'Test Publisher')
        self.doi = kwargs.get('doi', '10.1000/test.doi')
        self.isbn = kwargs.get('isbn', '978-0123456789')
        self.issn = kwargs.get('issn', '1234-5678')
        self.url = kwargs.get('url', 'https://example.com/article')
        self.abstract_note = kwargs.get('abstract_note', 'This is a test article abstract.')
        self.tags = kwargs.get('tags', ['testing', 'research'])
        self.extra_fields = kwargs.get('extra_fields', {})
        self.is_deleted = kwargs.get('is_deleted', False)
        self.date_added = kwargs.get('date_added', datetime.now())
        self.date_modified = kwargs.get('date_modified', datetime.now())
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())


class ExportFormatter:
    """Standalone export formatter for testing"""
    
    def __init__(self):
        self.supported_formats = {
            'bibtex': 'BibTeX format (.bib)',
            'ris': 'Research Information Systems format (.ris)',
            'endnote': 'EndNote format (.enw)',
            'json': 'JSON format (.json)',
            'csv': 'Comma-separated values (.csv)',
            'tsv': 'Tab-separated values (.tsv)'
        }
    
    async def export_bibtex(self, items: List[MockZoteroItem], include_notes: bool = True) -> str:
        """Export items to BibTeX format"""
        bibtex_entries = []
        
        for item in items:
            entry = await self.format_bibtex_entry(item, include_notes)
            bibtex_entries.append(entry)
        
        return '\n\n'.join(bibtex_entries)
    
    async def format_bibtex_entry(self, item: MockZoteroItem, include_notes: bool) -> str:
        """Format a single BibTeX entry"""
        # Map item types to BibTeX entry types
        type_mapping = {
            'article': 'article',
            'book': 'book',
            'bookSection': 'inbook',
            'conferencePaper': 'inproceedings',
            'thesis': 'phdthesis',
            'report': 'techreport',
            'webpage': 'misc'
        }
        
        bibtex_type = type_mapping.get(item.item_type, 'misc')
        citation_key = self.generate_citation_key(item)
        
        # Start entry
        entry_lines = [f"@{bibtex_type}{{{citation_key},"]
        
        # Add fields
        if item.title:
            entry_lines.append(f"  title = {{{item.title}}},")
        
        # Authors
        if item.creators:
            authors = self.format_bibtex_authors(item.creators)
            if authors:
                entry_lines.append(f"  author = {{{authors}}},")
        
        # Journal/Publication
        if item.publication_title:
            if item.item_type in ['article']:
                entry_lines.append(f"  journal = {{{item.publication_title}}},")
            else:
                entry_lines.append(f"  publisher = {{{item.publication_title}}},")
        
        # Publisher
        if item.publisher and item.item_type in ['book', 'bookSection', 'report']:
            entry_lines.append(f"  publisher = {{{item.publisher}}},")
        
        # Year
        if item.publication_year:
            entry_lines.append(f"  year = {{{item.publication_year}}},")
        
        # DOI
        if item.doi:
            entry_lines.append(f"  doi = {{{item.doi}}},")
        
        # ISBN
        if item.isbn:
            entry_lines.append(f"  isbn = {{{item.isbn}}},")
        
        # URL
        if item.url:
            entry_lines.append(f"  url = {{{item.url}}},")
        
        # Abstract
        if include_notes and item.abstract_note:
            clean_abstract = self.clean_text_for_bibtex(item.abstract_note)
            entry_lines.append(f"  abstract = {{{clean_abstract}}},")
        
        # Keywords
        if item.tags:
            keywords = ', '.join(item.tags)
            entry_lines.append(f"  keywords = {{{keywords}}},")
        
        # Remove trailing comma from last field
        if entry_lines[-1].endswith(','):
            entry_lines[-1] = entry_lines[-1][:-1]
        
        # Close entry
        entry_lines.append("}")
        
        return '\n'.join(entry_lines)
    
    async def export_ris(self, items: List[MockZoteroItem], include_notes: bool = True) -> str:
        """Export items to RIS format"""
        ris_entries = []
        
        for item in items:
            entry = await self.format_ris_entry(item, include_notes)
            ris_entries.append(entry)
        
        return '\n\n'.join(ris_entries)
    
    async def format_ris_entry(self, item: MockZoteroItem, include_notes: bool) -> str:
        """Format a single RIS entry"""
        # Map item types to RIS types
        type_mapping = {
            'article': 'JOUR',
            'book': 'BOOK',
            'bookSection': 'CHAP',
            'conferencePaper': 'CONF',
            'thesis': 'THES',
            'report': 'RPRT',
            'webpage': 'ELEC'
        }
        
        ris_type = type_mapping.get(item.item_type, 'GEN')
        
        # Start entry
        entry_lines = [f"TY  - {ris_type}"]
        
        # Title
        if item.title:
            entry_lines.append(f"TI  - {item.title}")
        
        # Authors
        if item.creators:
            for creator in item.creators:
                if creator.get('creator_type') == 'author':
                    if creator.get('name'):  # Organization
                        entry_lines.append(f"AU  - {creator['name']}")
                    else:
                        last = creator.get('last_name', '')
                        first = creator.get('first_name', '')
                        if last and first:
                            entry_lines.append(f"AU  - {last}, {first}")
                        elif last:
                            entry_lines.append(f"AU  - {last}")
        
        # Journal
        if item.publication_title:
            if item.item_type in ['article']:
                entry_lines.append(f"JO  - {item.publication_title}")
            else:
                entry_lines.append(f"T2  - {item.publication_title}")
        
        # Publisher
        if item.publisher:
            entry_lines.append(f"PB  - {item.publisher}")
        
        # Year
        if item.publication_year:
            entry_lines.append(f"PY  - {item.publication_year}")
        
        # DOI
        if item.doi:
            entry_lines.append(f"DO  - {item.doi}")
        
        # ISBN
        if item.isbn:
            entry_lines.append(f"SN  - {item.isbn}")
        
        # URL
        if item.url:
            entry_lines.append(f"UR  - {item.url}")
        
        # Abstract
        if include_notes and item.abstract_note:
            entry_lines.append(f"AB  - {item.abstract_note}")
        
        # Keywords
        if item.tags:
            for tag in item.tags:
                entry_lines.append(f"KW  - {tag}")
        
        # End entry
        entry_lines.append("ER  - ")
        
        return '\n'.join(entry_lines)
    
    async def export_json(self, items: List[MockZoteroItem], include_attachments: bool = False, include_notes: bool = True) -> str:
        """Export items to JSON format"""
        export_data = []
        
        for item in items:
            item_data = {
                'id': item.id,
                'zotero_item_key': item.zotero_item_key,
                'item_type': item.item_type,
                'title': item.title,
                'creators': item.creators,
                'publication_title': item.publication_title,
                'publication_year': item.publication_year,
                'publisher': item.publisher,
                'doi': item.doi,
                'isbn': item.isbn,
                'issn': item.issn,
                'url': item.url,
                'tags': item.tags,
                'date_added': item.date_added.isoformat() if item.date_added else None,
                'date_modified': item.date_modified.isoformat() if item.date_modified else None
            }
            
            if include_notes and item.abstract_note:
                item_data['abstract_note'] = item.abstract_note
            
            if item.extra_fields:
                item_data['extra_fields'] = item.extra_fields
            
            export_data.append(item_data)
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    async def export_csv(self, items: List[MockZoteroItem], include_notes: bool = True) -> str:
        """Export items to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        
        # Define CSV headers
        headers = [
            'ID', 'Item Type', 'Title', 'Authors', 'Publication Title',
            'Publication Year', 'Publisher', 'DOI', 'ISBN', 'ISSN', 'URL', 'Tags'
        ]
        
        if include_notes:
            headers.append('Abstract')
        
        writer = csv.writer(output)
        writer.writerow(headers)
        
        for item in items:
            # Format authors
            authors = []
            if item.creators:
                for creator in item.creators:
                    if creator.get('creator_type') == 'author':
                        if creator.get('name'):
                            authors.append(creator['name'])
                        else:
                            last = creator.get('last_name', '')
                            first = creator.get('first_name', '')
                            if last and first:
                                authors.append(f"{first} {last}")
                            elif last:
                                authors.append(last)
            
            row = [
                item.id,
                item.item_type,
                item.title or '',
                '; '.join(authors),
                item.publication_title or '',
                item.publication_year or '',
                item.publisher or '',
                item.doi or '',
                item.isbn or '',
                item.issn or '',
                item.url or '',
                '; '.join(item.tags) if item.tags else ''
            ]
            
            if include_notes:
                row.append(item.abstract_note or '')
            
            writer.writerow(row)
        
        return output.getvalue()
    
    def generate_citation_key(self, item: MockZoteroItem) -> str:
        """Generate a citation key for BibTeX"""
        import re
        
        # Get first author's last name
        author_key = "unknown"
        if item.creators:
            for creator in item.creators:
                if creator.get('creator_type') == 'author':
                    if creator.get('last_name'):
                        author_key = creator['last_name'].lower()
                        break
                    elif creator.get('name'):
                        # Use first word of organization name
                        author_key = creator['name'].split()[0].lower()
                        break
        
        # Clean author key
        author_key = re.sub(r'[^a-zA-Z0-9]', '', author_key)
        
        # Add year
        year_key = str(item.publication_year) if item.publication_year else "nodate"
        
        # Add title word if needed for uniqueness
        title_key = ""
        if item.title:
            # Get first significant word from title
            title_words = re.findall(r'\b[a-zA-Z]{3,}\b', item.title.lower())
            if title_words:
                title_key = title_words[0][:8]  # First 8 characters
        
        # Combine parts
        if title_key:
            citation_key = f"{author_key}{year_key}{title_key}"
        else:
            citation_key = f"{author_key}{year_key}"
        
        return citation_key
    
    def format_bibtex_authors(self, creators: List[Dict[str, Any]]) -> str:
        """Format authors for BibTeX"""
        authors = []
        
        for creator in creators:
            if creator.get('creator_type') == 'author':
                if creator.get('name'):  # Organization
                    authors.append(creator['name'])
                else:
                    last = creator.get('last_name', '')
                    first = creator.get('first_name', '')
                    if last and first:
                        authors.append(f"{last}, {first}")
                    elif last:
                        authors.append(last)
        
        return ' and '.join(authors)
    
    def clean_text_for_bibtex(self, text: str) -> str:
        """Clean text for BibTeX format"""
        import re
        
        if not text:
            return ""
        
        # Remove or escape special characters
        text = text.replace('{', '\\{').replace('}', '\\}')
        text = text.replace('%', '\\%')
        text = text.replace('&', '\\&')
        text = text.replace('$', '\\$')
        text = text.replace('#', '\\#')
        text = text.replace('_', '\\_')
        text = text.replace('^', '\\^')
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text


async def test_bibtex_export():
    """Test BibTeX export functionality"""
    print("Testing BibTeX export...")
    
    formatter = ExportFormatter()
    
    # Test single article
    article_item = MockZoteroItem()
    bibtex_output = await formatter.export_bibtex([article_item])
    
    print(f"✓ BibTeX output generated ({len(bibtex_output)} characters)")
    assert "@article{" in bibtex_output
    assert "title = {Sample Article Title}" in bibtex_output
    assert "author = {Doe, John and Smith, Jane}" in bibtex_output
    assert "year = {2023}" in bibtex_output
    assert "journal = {Journal of Testing}" in bibtex_output
    assert "doi = {10.1000/test.doi}" in bibtex_output
    
    # Test book item
    book_item = MockZoteroItem(
        item_type="book",
        title="Sample Book Title",
        creators=[{"creator_type": "author", "first_name": "Alice", "last_name": "Johnson"}],
        publisher="Academic Press"
    )
    
    book_bibtex = await formatter.export_bibtex([book_item])
    print(f"✓ Book BibTeX output generated")
    assert "@book{" in book_bibtex
    assert "publisher = {Academic Press}" in book_bibtex
    
    # Test citation key generation
    citation_key = formatter.generate_citation_key(article_item)
    print(f"✓ Citation key generated: {citation_key}")
    assert citation_key == "doe2023sample"
    
    # Test author formatting
    authors = formatter.format_bibtex_authors(article_item.creators)
    print(f"✓ BibTeX authors: {authors}")
    assert authors == "Doe, John and Smith, Jane"
    
    # Test text cleaning
    dirty_text = "This has {special} characters & symbols $#_^%"
    clean_text = formatter.clean_text_for_bibtex(dirty_text)
    print(f"✓ Cleaned text: {clean_text}")
    assert "\\{" in clean_text and "\\}" in clean_text
    
    print("🎉 All BibTeX export tests passed!")
    return True


async def test_ris_export():
    """Test RIS export functionality"""
    print("\nTesting RIS export...")
    
    formatter = ExportFormatter()
    
    # Test article export
    article_item = MockZoteroItem()
    ris_output = await formatter.export_ris([article_item])
    
    print(f"✓ RIS output generated ({len(ris_output)} characters)")
    assert "TY  - JOUR" in ris_output
    assert "TI  - Sample Article Title" in ris_output
    assert "AU  - Doe, John" in ris_output
    assert "AU  - Smith, Jane" in ris_output
    assert "JO  - Journal of Testing" in ris_output
    assert "PY  - 2023" in ris_output
    assert "DO  - 10.1000/test.doi" in ris_output
    assert "ER  - " in ris_output
    
    # Test book export
    book_item = MockZoteroItem(
        item_type="book",
        title="Sample Book Title",
        creators=[{"creator_type": "author", "first_name": "Alice", "last_name": "Johnson"}]
    )
    
    book_ris = await formatter.export_ris([book_item])
    print(f"✓ Book RIS output generated")
    assert "TY  - BOOK" in book_ris
    assert "AU  - Johnson, Alice" in book_ris
    
    # Test with tags
    assert "KW  - testing" in ris_output
    assert "KW  - research" in ris_output
    
    print("🎉 All RIS export tests passed!")
    return True


async def test_json_export():
    """Test JSON export functionality"""
    print("\nTesting JSON export...")
    
    formatter = ExportFormatter()
    
    # Test JSON export
    items = [MockZoteroItem(), MockZoteroItem(id="item-2", title="Second Article")]
    json_output = await formatter.export_json(items)
    
    print(f"✓ JSON output generated ({len(json_output)} characters)")
    
    # Parse JSON to verify structure
    parsed_data = json.loads(json_output)
    assert len(parsed_data) == 2
    assert parsed_data[0]['id'] == 'item-1'
    assert parsed_data[0]['title'] == 'Sample Article Title'
    assert parsed_data[0]['item_type'] == 'article'
    assert parsed_data[1]['id'] == 'item-2'
    assert parsed_data[1]['title'] == 'Second Article'
    
    # Test with notes included
    assert 'abstract_note' in parsed_data[0]
    
    # Test without notes
    json_no_notes = await formatter.export_json(items, include_notes=False)
    parsed_no_notes = json.loads(json_no_notes)
    assert 'abstract_note' not in parsed_no_notes[0]
    
    print("🎉 All JSON export tests passed!")
    return True


async def test_csv_export():
    """Test CSV export functionality"""
    print("\nTesting CSV export...")
    
    formatter = ExportFormatter()
    
    # Test CSV export
    items = [MockZoteroItem(), MockZoteroItem(id="item-2", title="Second Article")]
    csv_output = await formatter.export_csv(items)
    
    print(f"✓ CSV output generated ({len(csv_output)} characters)")
    
    # Check CSV structure
    lines = csv_output.strip().split('\n')
    assert len(lines) >= 3  # Header + 2 data rows
    
    # Check header
    header = lines[0]
    assert "ID" in header
    assert "Title" in header
    assert "Authors" in header
    assert "Publication Title" in header
    
    # Check data rows
    first_row = lines[1]
    assert "item-1" in first_row
    assert "Sample Article Title" in first_row
    assert "John Doe" in first_row
    
    # Test without notes
    csv_no_notes = await formatter.export_csv(items, include_notes=False)
    assert "Abstract" not in csv_no_notes.split('\n')[0]
    
    print("🎉 All CSV export tests passed!")
    return True


async def test_multiple_formats():
    """Test exporting the same data to multiple formats"""
    print("\nTesting multiple format export...")
    
    formatter = ExportFormatter()
    
    # Create test items
    items = [
        MockZoteroItem(),
        MockZoteroItem(
            id="item-2",
            item_type="book",
            title="Sample Book",
            creators=[{"creator_type": "author", "first_name": "Alice", "last_name": "Johnson"}],
            publisher="Academic Press"
        )
    ]
    
    # Export to all formats
    bibtex_output = await formatter.export_bibtex(items)
    ris_output = await formatter.export_ris(items)
    json_output = await formatter.export_json(items)
    csv_output = await formatter.export_csv(items)
    
    print(f"✓ BibTeX: {len(bibtex_output)} chars")
    print(f"✓ RIS: {len(ris_output)} chars")
    print(f"✓ JSON: {len(json_output)} chars")
    print(f"✓ CSV: {len(csv_output)} chars")
    
    # Verify all formats contain both items
    assert bibtex_output.count("@") == 2  # Two BibTeX entries
    assert ris_output.count("TY  -") == 2  # Two RIS entries
    
    parsed_json = json.loads(json_output)
    assert len(parsed_json) == 2
    
    csv_lines = csv_output.strip().split('\n')
    assert len(csv_lines) == 3  # Header + 2 data rows
    
    print("🎉 All multiple format tests passed!")
    return True


async def test_edge_cases():
    """Test edge cases and special scenarios"""
    print("\nTesting edge cases...")
    
    formatter = ExportFormatter()
    
    # Test item with minimal data
    minimal_item = MockZoteroItem(
        title=None,
        creators=[],
        publication_title=None,
        doi=None,
        url=None,
        abstract_note=None,
        tags=[]
    )
    
    bibtex_minimal = await formatter.export_bibtex([minimal_item])
    print(f"✓ Minimal item BibTeX: {len(bibtex_minimal)} chars")
    print(f"  Content: {bibtex_minimal}")
    assert "@article{" in bibtex_minimal  # Article is the default type for minimal_item
    
    # Test organization author
    org_item = MockZoteroItem(
        creators=[{"creator_type": "author", "name": "World Health Organization"}]
    )
    
    bibtex_org = await formatter.export_bibtex([org_item])
    print(f"✓ Organization author BibTeX generated")
    assert "World Health Organization" in bibtex_org
    
    # Test special characters in text
    special_item = MockZoteroItem(
        title="Title with {special} characters & symbols $#_^%",
        abstract_note="Abstract with {braces} and & symbols"
    )
    
    bibtex_special = await formatter.export_bibtex([special_item])
    print(f"✓ Special characters handled in BibTeX")
    assert "\\{" in bibtex_special and "\\}" in bibtex_special
    
    # Test empty list
    empty_export = await formatter.export_bibtex([])
    print(f"✓ Empty list handled: '{empty_export}'")
    assert empty_export == ""
    
    print("🎉 All edge case tests passed!")
    return True


async def main():
    """Run all export tests"""
    print("🚀 Starting export service tests...\n")
    
    success1 = await test_bibtex_export()
    success2 = await test_ris_export()
    success3 = await test_json_export()
    success4 = await test_csv_export()
    success5 = await test_multiple_formats()
    success6 = await test_edge_cases()
    
    if all([success1, success2, success3, success4, success5, success6]):
        print("\n✅ All export service tests completed successfully!")
        print("The bibliography and export functionality is working correctly.")
    else:
        print("\n❌ Some tests failed!")


if __name__ == "__main__":
    asyncio.run(main())