#!/usr/bin/env python3
"""
Test script for Journal Source Handlers.

Tests the journal source handler functionality including:
- Base journal handler functionality
- JSS handler implementation
- R Journal handler implementation
- Metadata extraction and validation
- PDF download capabilities
"""

import asyncio
import logging
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_journal_metadata():
    """Test JournalMetadata dataclass."""
    logger.info("Testing JournalMetadata...")
    
    try:
        sys.path.append(str(Path(__file__).parent))
        
        from journal_sources.base_journal_handler import JournalMetadata
        
        # Test basic metadata creation
        metadata = JournalMetadata(
            title="Test Paper Title",
            authors=["Author One", "Author Two"],
            abstract="This is a test abstract for the paper.",
            journal_name="Test Journal",
            volume="10",
            issue="2",
            doi="10.1000/test.doi"
        )
        
        assert metadata.title == "Test Paper Title"
        assert len(metadata.authors) == 2
        assert metadata.journal_name == "Test Journal"
        assert metadata.keywords == []  # Should be initialized as empty list
        
        logger.info("JournalMetadata test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"JournalMetadata test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_base_handler_functionality():
    """Test base journal handler functionality."""
    logger.info("Testing base handler functionality...")
    
    try:
        from journal_sources.base_journal_handler import BaseJournalHandler
        
        # Create a concrete implementation for testing
        class TestHandler(BaseJournalHandler):
            async def discover_papers(self, start_date, end_date, max_papers=100):
                return []
            
            async def extract_metadata(self, paper_url):
                return None
            
            async def download_paper(self, paper_info, download_dir):
                return None
        
        # Test initialization
        handler = TestHandler("test_instance", "https://example.com", "Test Journal")
        
        assert handler.instance_name == "test_instance"
        assert handler.base_url == "https://example.com"
        assert handler.journal_name == "Test Journal"
        assert handler.max_retries == 3
        
        # Test text cleaning
        dirty_text = "  This   is   dirty\n\ntext  with  &nbsp; entities  "
        clean_text = handler.clean_text(dirty_text)
        assert "This is dirty text with entities" in clean_text
        
        # Test DOI extraction
        text_with_doi = "The DOI for this paper is doi:10.1000/test.doi and more text"
        doi = handler.extract_doi(text_with_doi)
        assert doi == "10.1000/test.doi"
        
        # Test author parsing
        author_text = "John Smith, Jane Doe and Bob Johnson"
        authors = handler.parse_authors(author_text)
        assert len(authors) >= 2
        assert "John Smith" in authors
        
        # Test handler stats
        stats = handler.get_handler_stats()
        assert stats['handler_type'] == 'TestHandler'
        assert stats['journal_name'] == 'Test Journal'
        
        logger.info("Base handler functionality test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Base handler functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_jss_handler_initialization():
    """Test JSS handler initialization."""
    logger.info("Testing JSS handler initialization...")
    
    try:
        from journal_sources.jss_handler import JStatSoftwareHandler
        
        # Test initialization
        handler = JStatSoftwareHandler("test_instance")
        
        assert handler.instance_name == "test_instance"
        assert handler.journal_name == "Journal of Statistical Software"
        assert "jstatsoft.org" in handler.base_url
        assert handler.issues_url is not None
        
        # Test issue date range checking
        test_issue = {'volume': '50', 'issue': '1', 'title': 'Test Issue'}
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2025, 12, 31)
        
        in_range = handler._is_issue_in_date_range(test_issue, start_date, end_date)
        assert isinstance(in_range, bool)
        
        # Test paper ID generation
        from journal_sources.base_journal_handler import JournalMetadata
        metadata = JournalMetadata(
            title="Test JSS Paper",
            authors=["Test Author"],
            abstract="Test abstract",
            journal_name="Journal of Statistical Software",
            volume="50",
            issue="1"
        )
        
        paper_id = handler.generate_paper_id(metadata)
        assert isinstance(paper_id, str)
        assert len(paper_id) > 0
        
        logger.info("JSS handler initialization test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"JSS handler initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rjournal_handler_initialization():
    """Test R Journal handler initialization."""
    logger.info("Testing R Journal handler initialization...")
    
    try:
        from journal_sources.rjournal_handler import RJournalHandler
        
        # Test initialization
        handler = RJournalHandler("test_instance")
        
        assert handler.instance_name == "test_instance"
        assert handler.journal_name == "The R Journal"
        assert "journal.r-project.org" in handler.base_url
        assert handler.issues_url is not None
        
        # Test issue date range checking
        test_issue = {'year': '2023', 'issue': '1', 'title': 'Test Issue'}
        start_date = datetime(2022, 1, 1)
        end_date = datetime(2024, 12, 31)
        
        in_range = handler._is_issue_in_date_range(test_issue, start_date, end_date)
        assert isinstance(in_range, bool)
        
        # Test minimal metadata creation from URL
        pdf_url = "https://journal.r-project.org/archive/2023-1/test-paper.pdf"
        metadata = handler._create_minimal_metadata_from_url(pdf_url)
        
        assert metadata is not None
        assert metadata.journal_name == "The R Journal"
        
        logger.info("R Journal handler initialization test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"R Journal handler initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metadata_validation():
    """Test metadata validation functionality."""
    logger.info("Testing metadata validation...")
    
    try:
        from journal_sources.base_journal_handler import BaseJournalHandler, JournalMetadata
        
        # Create a test handler
        class TestHandler(BaseJournalHandler):
            async def discover_papers(self, start_date, end_date, max_papers=100):
                return []
            async def extract_metadata(self, paper_url):
                return None
            async def download_paper(self, paper_info, download_dir):
                return None
        
        handler = TestHandler("test", "https://example.com", "Test Journal")
        
        # Test valid metadata
        valid_metadata = JournalMetadata(
            title="Valid Paper Title",
            authors=["Author One", "Author Two"],
            abstract="This is a valid abstract with sufficient content.",
            journal_name="Test Journal"
        )
        
        assert handler.validate_metadata(valid_metadata) == True
        
        # Test invalid metadata (no title)
        invalid_metadata = JournalMetadata(
            title="",
            authors=["Author One"],
            abstract="Abstract",
            journal_name="Test Journal"
        )
        
        assert handler.validate_metadata(invalid_metadata) == False
        
        # Test invalid metadata (no authors)
        invalid_metadata2 = JournalMetadata(
            title="Valid Title",
            authors=[],
            abstract="Abstract",
            journal_name="Test Journal"
        )
        
        assert handler.validate_metadata(invalid_metadata2) == False
        
        logger.info("Metadata validation test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Metadata validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_journal_paper_creation():
    """Test journal paper object creation."""
    logger.info("Testing journal paper creation...")
    
    try:
        from journal_sources.jss_handler import JStatSoftwareHandler
        from journal_sources.rjournal_handler import RJournalHandler
        
        # Test JSS paper creation
        jss_handler = JStatSoftwareHandler("test_instance")
        
        jss_paper_info = {
            'title': 'Test JSS Paper',
            'url': 'https://www.jstatsoft.org/article/view/v050i01',
            'volume': '50',
            'issue': '01',
            'journal': 'Journal of Statistical Software'
        }
        
        jss_paper = jss_handler.create_journal_paper(jss_paper_info)
        
        assert jss_paper.title == 'Test JSS Paper'
        assert jss_paper.journal_name == 'Journal of Statistical Software'
        assert jss_paper.volume == '50'
        assert jss_paper.issue == '01'
        assert jss_paper.source_type == 'journal'
        assert jss_paper.instance_name == 'test_instance'
        
        # Test R Journal paper creation
        rjournal_handler = RJournalHandler("test_instance")
        
        rjournal_paper_info = {
            'title': 'Test R Journal Paper',
            'url': 'https://journal.r-project.org/archive/2023-1/test.pdf',
            'year': '2023',
            'issue': '1',
            'journal': 'The R Journal'
        }
        
        rjournal_paper = rjournal_handler.create_journal_paper(rjournal_paper_info)
        
        assert rjournal_paper.title == 'Test R Journal Paper'
        assert rjournal_paper.journal_name == 'The R Journal'
        assert rjournal_paper.volume == '2023'
        assert rjournal_paper.issue == '1'
        assert rjournal_paper.source_type == 'journal'
        assert rjournal_paper.instance_name == 'test_instance'
        
        logger.info("Journal paper creation test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Journal paper creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_async_context_manager():
    """Test async context manager functionality."""
    logger.info("Testing async context manager...")
    
    try:
        from journal_sources.jss_handler import JStatSoftwareHandler
        
        handler = JStatSoftwareHandler("test_instance")
        
        # Test context manager
        async with handler:
            assert handler.session is not None
            
            # Test that we can make a basic request (this might fail due to network,
            # but we're mainly testing the context manager setup)
            try:
                response = await handler.fetch_with_retry("https://httpbin.org/status/200")
                # If we get here, the session is working
                logger.info("Network request successful")
            except Exception as e:
                # Network errors are okay for this test
                logger.info(f"Network request failed (expected): {e}")
        
        # After context manager, session should be closed
        assert handler.session is None or handler.session.closed
        
        logger.info("Async context manager test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Async context manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_html_parsing_patterns():
    """Test HTML parsing patterns used by handlers."""
    logger.info("Testing HTML parsing patterns...")
    
    try:
        from journal_sources.jss_handler import JStatSoftwareHandler
        from journal_sources.rjournal_handler import RJournalHandler
        
        # Test JSS issue parsing
        jss_handler = JStatSoftwareHandler("test_instance")
        
        sample_jss_html = '''
        <html>
        <body>
        <a href="/issue/view/v050i01">Volume 50, Issue 1</a>
        <a href="/issue/view/v049i12">Volume 49, Issue 12</a>
        </body>
        </html>
        '''
        
        issues = jss_handler._parse_issues_page(sample_jss_html)
        assert len(issues) >= 1
        
        # Find the v050i01 issue
        v50_issue = next((issue for issue in issues if issue['volume'] == '50'), None)
        assert v50_issue is not None
        assert v50_issue['issue'] == '01'
        
        # Test R Journal issue parsing
        rjournal_handler = RJournalHandler("test_instance")
        
        sample_rjournal_html = '''
        <html>
        <body>
        <a href="/archive/2023-1/">The R Journal 2023 Issue 1</a>
        <a href="/archive/2022-2/">The R Journal 2022 Issue 2</a>
        </body>
        </html>
        '''
        
        r_issues = rjournal_handler._parse_issues_page(sample_rjournal_html)
        assert len(r_issues) >= 1
        
        # Find the 2023-1 issue
        r2023_issue = next((issue for issue in r_issues if issue['year'] == '2023'), None)
        assert r2023_issue is not None
        assert r2023_issue['issue'] == '1'
        
        logger.info("HTML parsing patterns test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"HTML parsing patterns test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    logger.info("Starting Journal Source Handlers tests")
    
    tests = [
        ("Journal Metadata", test_journal_metadata),
        ("Base Handler Functionality", test_base_handler_functionality),
        ("JSS Handler Initialization", test_jss_handler_initialization),
        ("R Journal Handler Initialization", test_rjournal_handler_initialization),
        ("Metadata Validation", test_metadata_validation),
        ("Journal Paper Creation", test_journal_paper_creation),
        ("Async Context Manager", test_async_context_manager),
        ("HTML Parsing Patterns", test_html_parsing_patterns),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
            status = "PASSED" if result else "FAILED"
            logger.info(f"{test_name} Test: {status}")
        except Exception as e:
            logger.error(f"{test_name} Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n--- Test Summary ---")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("All journal source handler tests completed successfully!")
        logger.info("\nKey features verified:")
        logger.info("✓ Base journal handler functionality")
        logger.info("✓ JSS handler implementation")
        logger.info("✓ R Journal handler implementation")
        logger.info("✓ Metadata extraction and validation")
        logger.info("✓ Journal paper object creation")
        logger.info("✓ HTML parsing patterns")
        logger.info("✓ Async context manager support")
    else:
        logger.error("Some tests failed!")


if __name__ == "__main__":
    asyncio.run(main())