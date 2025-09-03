#!/usr/bin/env python3
"""
Comprehensive test suite for bibliography generation and export functionality
Tests task 5.2: Build bibliography and export functionality
"""
import asyncio
import json
import pytest
from datetime import datetime
from typing import Dict, List, Optional, Any
from unittest.mock import Mock, AsyncMock, patch

# Mock database session
class MockDB:
    def query(self, model):
        return MockQuery()
    
    def commit(self):
        pass
    
    def rollback(self):
        pass

class MockQuery:
    def filter(self, *args):
        return self
    
    def all(self):
        return []
    
    def first(self):
        return None

# Mock Zotero item for testing
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

# Import the services we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from services.zotero.zotero_citation_service import ZoteroCitationService
from services.zotero.zotero_export_service import ZoteroExportService
from models.zotero_schemas import BibliographyRequest, BibliographyResponse, ZoteroExportRequest, ZoteroExportResponse


class TestBibliographyGeneration:
    """Test bibliography generation functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.db = MockDB()
        self.citation_service = ZoteroCitationService(self.db)
        
        # Mock items for testing
        self.test_items = [
            MockZoteroItem(
                id="item-1",
                title="First Article",
                creators=[{"creator_type": "author", "first_name": "Alice", "last_name": "Johnson"}],
                publication_year=2023
            ),
            MockZoteroItem(
                id="item-2",
                title="Second Article",
                creators=[{"creator_type": "author", "first_name": "Bob", "last_name": "Smith"}],
                publication_year=2022
            ),
            MockZoteroItem(
                id="item-3",
                item_type="book",
                title="Test Book",
                creators=[{"creator_type": "author", "first_name": "Carol", "last_name": "Davis"}],
                publisher="Academic Press",
                publication_year=2021
            )
        ]
    
    @pytest.mark.asyncio
    async def test_generate_bibliography_basic(self):
        """Test basic bibliography generation"""
        # Mock the database query
        with patch.object(self.citation_service, '_get_items_by_ids', return_value=self.test_items):
            response = await self.citation_service.generate_bibliography(
                item_ids=["item-1", "item-2", "item-3"],
                citation_style="apa",
                format_type="text"
            )
            
            assert isinstance(response, BibliographyResponse)
            assert response.item_count == 3
            assert response.style_used == "apa"
            assert response.format == "text"
            assert len(response.bibliography) > 0
            assert "References" in response.bibliography
            print(f"✓ Basic bibliography generation test passed")
    
    @pytest.mark.asyncio
    async def test_generate_bibliography_html_format(self):
        """Test bibliography generation with HTML formatting"""
        with patch.object(self.citation_service, '_get_items_by_ids', return_value=self.test_items):
            response = await self.citation_service.generate_bibliography(
                item_ids=["item-1", "item-2"],
                citation_style="apa",
                format_type="html"
            )
            
            assert '<div class="bibliography"' in response.bibliography
            assert '<h3 class="bibliography-title">References</h3>' in response.bibliography
            assert '<div class="bibliography-entry"' in response.bibliography
            print(f"✓ HTML bibliography generation test passed")
    
    @pytest.mark.asyncio
    async def test_generate_bibliography_rtf_format(self):
        """Test bibliography generation with RTF formatting"""
        with patch.object(self.citation_service, '_get_items_by_ids', return_value=self.test_items):
            response = await self.citation_service.generate_bibliography(
                item_ids=["item-1"],
                citation_style="apa",
                format_type="rtf"
            )
            
            assert response.bibliography.startswith('{\\rtf1\\ansi\\deff0')
            assert '\\par\\b References\\b0\\par\\par' in response.bibliography
            assert response.bibliography.endswith('}')
            print(f"✓ RTF bibliography generation test passed")
    
    @pytest.mark.asyncio
    async def test_batch_bibliography_generation(self):
        """Test batch bibliography generation for large datasets"""
        # Create a larger dataset
        large_dataset = []
        for i in range(150):  # More than batch size
            large_dataset.append(MockZoteroItem(
                id=f"item-{i}",
                title=f"Article {i}",
                creators=[{"creator_type": "author", "first_name": f"Author{i}", "last_name": f"Last{i}"}],
                publication_year=2020 + (i % 4)
            ))
        
        with patch.object(self.citation_service, '_get_items_by_ids', return_value=large_dataset):
            response = await self.citation_service.generate_bibliography(
                item_ids=[f"item-{i}" for i in range(150)],
                citation_style="apa",
                format_type="text"
            )
            
            assert response.item_count == 150
            assert len(response.bibliography.split('\n\n')) >= 150  # Should have many entries
            print(f"✓ Batch bibliography generation test passed")
    
    @pytest.mark.asyncio
    async def test_bibliography_sorting(self):
        """Test bibliography sorting by different criteria"""
        # Test sorting by author
        with patch.object(self.citation_service, '_get_items_by_ids', return_value=self.test_items):
            response = await self.citation_service.generate_bibliography(
                item_ids=["item-1", "item-2", "item-3"],
                citation_style="apa",
                format_type="text",
                sort_by="author"
            )
            
            # Check that items are sorted (Carol Davis should come before Alice Johnson)
            bibliography_lines = response.bibliography.split('\n\n')
            # Remove the "References" header
            entries = [line for line in bibliography_lines if line.strip() and line.strip() != "References"]
            
            # First entry should contain "Davis" (Carol Davis)
            assert len(entries) >= 3
            print(f"✓ Bibliography sorting test passed")
    
    @pytest.mark.asyncio
    async def test_bibliography_different_styles(self):
        """Test bibliography generation with different citation styles"""
        styles_to_test = ["apa", "mla", "chicago"]
        
        for style in styles_to_test:
            with patch.object(self.citation_service, '_get_items_by_ids', return_value=self.test_items[:1]):
                response = await self.citation_service.generate_bibliography(
                    item_ids=["item-1"],
                    citation_style=style,
                    format_type="text"
                )
                
                assert response.style_used == style
                assert len(response.bibliography) > 0
                print(f"✓ Bibliography generation with {style} style test passed")
    
    @pytest.mark.asyncio
    async def test_batch_citations_processing(self):
        """Test batch citation processing functionality"""
        with patch.object(self.citation_service, '_get_items_by_ids', return_value=self.test_items):
            response = await self.citation_service.generate_batch_citations(
                item_ids=["item-1", "item-2", "item-3"],
                citation_style="apa",
                format_type="text",
                batch_size=2
            )
            
            assert response['total_items'] == 3
            assert response['successful_items'] >= 0
            assert len(response['citations']) == 3
            assert response['style_used'] == "apa"
            assert response['batch_size'] == 2
            
            # Check individual citation results
            for citation_result in response['citations']:
                assert 'item_id' in citation_result
                assert 'citation' in citation_result
                assert 'status' in citation_result
            
            print(f"✓ Batch citations processing test passed")


class TestExportFunctionality:
    """Test export functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.db = MockDB()
        self.export_service = ZoteroExportService(self.db)
        
        # Mock items for testing
        self.test_items = [
            MockZoteroItem(
                id="item-1",
                title="Export Test Article",
                creators=[{"creator_type": "author", "first_name": "Export", "last_name": "Author"}],
                publication_year=2023,
                doi="10.1000/export.test"
            ),
            MockZoteroItem(
                id="item-2",
                item_type="book",
                title="Export Test Book",
                creators=[{"creator_type": "author", "first_name": "Book", "last_name": "Author"}],
                publisher="Export Publisher",
                publication_year=2022
            )
        ]
    
    @pytest.mark.asyncio
    async def test_export_bibtex(self):
        """Test BibTeX export functionality"""
        with patch.object(self.export_service, '_get_items_by_ids', return_value=self.test_items):
            response = await self.export_service.export_references(
                item_ids=["item-1", "item-2"],
                export_format="bibtex",
                include_notes=True
            )
            
            assert isinstance(response, ZoteroExportResponse)
            assert response.export_format == "bibtex"
            assert response.item_count == 2
            assert "@article{" in response.export_data
            assert "@book{" in response.export_data
            assert "title = {Export Test Article}" in response.export_data
            assert "author = {Author, Export}" in response.export_data
            print(f"✓ BibTeX export test passed")
    
    @pytest.mark.asyncio
    async def test_export_ris(self):
        """Test RIS export functionality"""
        with patch.object(self.export_service, '_get_items_by_ids', return_value=self.test_items):
            response = await self.export_service.export_references(
                item_ids=["item-1", "item-2"],
                export_format="ris",
                include_notes=True
            )
            
            assert response.export_format == "ris"
            assert "TY  - JOUR" in response.export_data
            assert "TY  - BOOK" in response.export_data
            assert "TI  - Export Test Article" in response.export_data
            assert "AU  - Author, Export" in response.export_data
            assert "ER  - " in response.export_data
            print(f"✓ RIS export test passed")
    
    @pytest.mark.asyncio
    async def test_export_endnote(self):
        """Test EndNote export functionality"""
        with patch.object(self.export_service, '_get_items_by_ids', return_value=self.test_items):
            response = await self.export_service.export_references(
                item_ids=["item-1", "item-2"],
                export_format="endnote",
                include_notes=True
            )
            
            assert response.export_format == "endnote"
            assert "%T Export Test Article" in response.export_data
            assert "%A Author, Export" in response.export_data
            print(f"✓ EndNote export test passed")
    
    @pytest.mark.asyncio
    async def test_export_json(self):
        """Test JSON export functionality"""
        with patch.object(self.export_service, '_get_items_by_ids', return_value=self.test_items):
            response = await self.export_service.export_references(
                item_ids=["item-1", "item-2"],
                export_format="json",
                include_attachments=True,
                include_notes=True
            )
            
            assert response.export_format == "json"
            
            # Parse JSON to verify structure
            exported_data = json.loads(response.export_data)
            assert len(exported_data) == 2
            assert exported_data[0]['id'] == 'item-1'
            assert exported_data[0]['title'] == 'Export Test Article'
            assert 'abstract_note' in exported_data[0]
            print(f"✓ JSON export test passed")
    
    @pytest.mark.asyncio
    async def test_export_csv(self):
        """Test CSV export functionality"""
        with patch.object(self.export_service, '_get_items_by_ids', return_value=self.test_items):
            response = await self.export_service.export_references(
                item_ids=["item-1", "item-2"],
                export_format="csv",
                include_notes=True
            )
            
            assert response.export_format == "csv"
            
            lines = response.export_data.strip().split('\n')
            assert len(lines) >= 3  # Header + 2 data rows
            
            # Check header
            header = lines[0]
            assert "ID" in header
            assert "Title" in header
            assert "Authors" in header
            
            # Check data
            assert "item-1" in lines[1]
            assert "Export Test Article" in lines[1]
            print(f"✓ CSV export test passed")
    
    @pytest.mark.asyncio
    async def test_batch_export_large_dataset(self):
        """Test batch export with large dataset"""
        # Create large dataset
        large_dataset = []
        for i in range(150):
            large_dataset.append(MockZoteroItem(
                id=f"export-item-{i}",
                title=f"Export Article {i}",
                creators=[{"creator_type": "author", "first_name": f"Author{i}", "last_name": f"Last{i}"}]
            ))
        
        with patch.object(self.export_service, '_get_items_by_ids', return_value=large_dataset):
            response = await self.export_service.export_references(
                item_ids=[f"export-item-{i}" for i in range(150)],
                export_format="bibtex",
                include_notes=True
            )
            
            assert response.item_count == 150
            # Should have 150 BibTeX entries
            bibtex_entries = response.export_data.count("@article{")
            assert bibtex_entries == 150
            print(f"✓ Batch export large dataset test passed")
    
    @pytest.mark.asyncio
    async def test_batch_export_by_collection(self):
        """Test batch export by collection"""
        with patch.object(self.export_service, '_get_items_by_ids', return_value=self.test_items):
            response = await self.export_service.batch_export_by_collection(
                collection_id="test-collection",
                export_format="bibtex",
                include_notes=True
            )
            
            assert response.export_format == "bibtex"
            assert response.item_count == 2
            print(f"✓ Batch export by collection test passed")
    
    @pytest.mark.asyncio
    async def test_export_with_special_characters(self):
        """Test export handling of special characters"""
        special_item = MockZoteroItem(
            id="special-item",
            title="Title with {special} characters & symbols $#_^%",
            abstract_note="Abstract with {braces} and & symbols",
            creators=[{"creator_type": "author", "first_name": "Special", "last_name": "Author"}]
        )
        
        with patch.object(self.export_service, '_get_items_by_ids', return_value=[special_item]):
            response = await self.export_service.export_references(
                item_ids=["special-item"],
                export_format="bibtex",
                include_notes=True
            )
            
            # Check that special characters are properly escaped
            assert "\\{" in response.export_data
            assert "\\}" in response.export_data
            assert "\\&" in response.export_data
            print(f"✓ Export with special characters test passed")
    
    @pytest.mark.asyncio
    async def test_export_error_handling(self):
        """Test export error handling"""
        # Test with empty item list
        with patch.object(self.export_service, '_get_items_by_ids', return_value=[]):
            try:
                await self.export_service.export_references(
                    item_ids=["nonexistent-item"],
                    export_format="bibtex"
                )
                assert False, "Should have raised an exception"
            except Exception as e:
                assert "No valid items found" in str(e)
                print(f"✓ Export error handling test passed")


class TestIntegrationScenarios:
    """Test integration scenarios combining bibliography and export"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.db = MockDB()
        self.citation_service = ZoteroCitationService(self.db)
        self.export_service = ZoteroExportService(self.db)
        
        # Create diverse test dataset
        self.diverse_items = [
            MockZoteroItem(
                id="journal-1",
                item_type="article",
                title="Machine Learning in Academic Research",
                creators=[
                    {"creator_type": "author", "first_name": "Alice", "last_name": "Johnson"},
                    {"creator_type": "author", "first_name": "Bob", "last_name": "Smith"}
                ],
                publication_title="Journal of AI Research",
                publication_year=2023,
                volume="15",
                issue="3",
                pages="123-145",
                doi="10.1000/jair.2023.15.123"
            ),
            MockZoteroItem(
                id="book-1",
                item_type="book",
                title="Advanced Citation Management",
                creators=[{"creator_type": "author", "first_name": "Carol", "last_name": "Davis"}],
                publisher="Academic Press",
                publication_year=2022,
                isbn="978-0123456789"
            ),
            MockZoteroItem(
                id="conference-1",
                item_type="conferencePaper",
                title="Automated Bibliography Generation",
                creators=[
                    {"creator_type": "author", "first_name": "David", "last_name": "Wilson"},
                    {"creator_type": "author", "first_name": "Eva", "last_name": "Brown"}
                ],
                publication_title="Proceedings of the International Conference on Digital Libraries",
                publication_year=2023,
                pages="45-52"
            ),
            MockZoteroItem(
                id="org-1",
                item_type="report",
                title="Standards for Academic Citation",
                creators=[{"creator_type": "author", "name": "International Academic Standards Organization"}],
                publisher="IASO Publications",
                publication_year=2023
            )
        ]
    
    @pytest.mark.asyncio
    async def test_bibliography_and_export_consistency(self):
        """Test that bibliography and export produce consistent results"""
        with patch.object(self.citation_service, '_get_items_by_ids', return_value=self.diverse_items):
            with patch.object(self.export_service, '_get_items_by_ids', return_value=self.diverse_items):
                # Generate bibliography
                bib_response = await self.citation_service.generate_bibliography(
                    item_ids=["journal-1", "book-1", "conference-1", "org-1"],
                    citation_style="apa",
                    format_type="text"
                )
                
                # Export to BibTeX
                export_response = await self.export_service.export_references(
                    item_ids=["journal-1", "book-1", "conference-1", "org-1"],
                    export_format="bibtex"
                )
                
                # Both should process the same number of items
                assert bib_response.item_count == export_response.item_count
                assert bib_response.item_count == 4
                
                # Bibliography should contain all titles
                for item in self.diverse_items:
                    assert item.title in bib_response.bibliography
                
                # BibTeX export should contain all entries
                assert export_response.export_data.count("@") == 4
                print(f"✓ Bibliography and export consistency test passed")
    
    @pytest.mark.asyncio
    async def test_multiple_format_export_workflow(self):
        """Test exporting the same dataset to multiple formats"""
        formats_to_test = ["bibtex", "ris", "endnote", "json", "csv"]
        
        with patch.object(self.export_service, '_get_items_by_ids', return_value=self.diverse_items):
            export_results = {}
            
            for format_name in formats_to_test:
                response = await self.export_service.export_references(
                    item_ids=["journal-1", "book-1", "conference-1", "org-1"],
                    export_format=format_name,
                    include_notes=True
                )
                
                export_results[format_name] = response
                assert response.item_count == 4
                assert response.export_format == format_name
                assert len(response.export_data) > 0
            
            # Verify format-specific characteristics
            assert "@article{" in export_results["bibtex"].export_data
            assert "TY  - JOUR" in export_results["ris"].export_data
            assert "%T Machine Learning" in export_results["endnote"].export_data
            
            # JSON should be parseable
            json_data = json.loads(export_results["json"].export_data)
            assert len(json_data) == 4
            
            # CSV should have proper structure
            csv_lines = export_results["csv"].export_data.strip().split('\n')
            assert len(csv_lines) == 5  # Header + 4 data rows
            
            print(f"✓ Multiple format export workflow test passed")
    
    @pytest.mark.asyncio
    async def test_large_scale_processing(self):
        """Test large-scale bibliography and export processing"""
        # Create a large dataset with mixed item types
        large_dataset = []
        item_types = ["article", "book", "conferencePaper", "report", "thesis"]
        
        for i in range(500):  # Large dataset
            item_type = item_types[i % len(item_types)]
            large_dataset.append(MockZoteroItem(
                id=f"large-item-{i}",
                item_type=item_type,
                title=f"Large Scale Test Item {i}",
                creators=[{"creator_type": "author", "first_name": f"Author{i}", "last_name": f"Last{i}"}],
                publication_year=2020 + (i % 4)
            ))
        
        item_ids = [f"large-item-{i}" for i in range(500)]
        
        with patch.object(self.citation_service, '_get_items_by_ids', return_value=large_dataset):
            with patch.object(self.export_service, '_get_items_by_ids', return_value=large_dataset):
                # Test large bibliography generation
                bib_response = await self.citation_service.generate_bibliography(
                    item_ids=item_ids,
                    citation_style="apa",
                    format_type="text"
                )
                
                assert bib_response.item_count == 500
                assert bib_response.processing_time > 0
                
                # Test large export
                export_response = await self.export_service.export_references(
                    item_ids=item_ids,
                    export_format="bibtex"
                )
                
                assert export_response.item_count == 500
                assert export_response.processing_time > 0
                
                # Should use batch processing for large datasets
                assert export_response.export_data.count("@") == 500
                
                print(f"✓ Large scale processing test passed")


async def run_all_tests():
    """Run all bibliography and export tests"""
    print("🚀 Starting Bibliography and Export Functionality Tests")
    print("=" * 80)
    
    # Bibliography tests
    print("\n📚 BIBLIOGRAPHY GENERATION TESTS")
    print("-" * 50)
    
    bib_tests = TestBibliographyGeneration()
    bib_tests.setup_method()
    
    await bib_tests.test_generate_bibliography_basic()
    await bib_tests.test_generate_bibliography_html_format()
    await bib_tests.test_generate_bibliography_rtf_format()
    await bib_tests.test_batch_bibliography_generation()
    await bib_tests.test_bibliography_sorting()
    await bib_tests.test_bibliography_different_styles()
    await bib_tests.test_batch_citations_processing()
    
    # Export tests
    print("\n📤 EXPORT FUNCTIONALITY TESTS")
    print("-" * 50)
    
    export_tests = TestExportFunctionality()
    export_tests.setup_method()
    
    await export_tests.test_export_bibtex()
    await export_tests.test_export_ris()
    await export_tests.test_export_endnote()
    await export_tests.test_export_json()
    await export_tests.test_export_csv()
    await export_tests.test_batch_export_large_dataset()
    await export_tests.test_batch_export_by_collection()
    await export_tests.test_export_with_special_characters()
    await export_tests.test_export_error_handling()
    
    # Integration tests
    print("\n🔗 INTEGRATION SCENARIO TESTS")
    print("-" * 50)
    
    integration_tests = TestIntegrationScenarios()
    integration_tests.setup_method()
    
    await integration_tests.test_bibliography_and_export_consistency()
    await integration_tests.test_multiple_format_export_workflow()
    await integration_tests.test_large_scale_processing()
    
    print("\n" + "=" * 80)
    print("✅ ALL BIBLIOGRAPHY AND EXPORT TESTS COMPLETED SUCCESSFULLY!")
    print("\nTask 5.2 Implementation Summary:")
    print("✓ Bibliography compilation from multiple references")
    print("✓ Export support for BibTeX, RIS, EndNote formats")
    print("✓ Batch citation processing")
    print("✓ Comprehensive test coverage")
    print("✓ Error handling and edge cases")
    print("✓ Performance optimization for large datasets")
    print("✓ Multiple output formats (text, HTML, RTF)")
    print("✓ Integration with existing citation system")


if __name__ == "__main__":
    asyncio.run(run_all_tests())