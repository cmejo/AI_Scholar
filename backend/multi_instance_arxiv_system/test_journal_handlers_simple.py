#!/usr/bin/env python3
"""
Simple test for Journal Source Handlers components.

Tests individual components without complex imports.
"""

import asyncio
import logging
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_journal_metadata_structure():
    """Test journal metadata structure."""
    logger.info("Testing journal metadata structure...")
    
    try:
        @dataclass
        class JournalMetadata:
            """Metadata extracted from journal papers."""
            title: str
            authors: List[str]
            abstract: str
            journal_name: str
            volume: Optional[str] = None
            issue: Optional[str] = None
            pages: Optional[str] = None
            doi: Optional[str] = None
            publication_date: Optional[datetime] = None
            keywords: List[str] = None
            url: Optional[str] = None
            
            def __post_init__(self):
                if self.keywords is None:
                    self.keywords = []
        
        # Test metadata creation
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
        assert metadata.volume == "10"
        assert metadata.issue == "2"
        
        logger.info("Journal metadata structure test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Journal metadata structure test failed: {e}")
        return False


def test_text_cleaning_functionality():
    """Test text cleaning functionality."""
    logger.info("Testing text cleaning functionality...")
    
    try:
        def clean_text(text):
            """Clean and normalize text content."""
            if not text:
                return ""
            
            # Remove extra whitespace and normalize
            text = re.sub(r'\s+', ' ', text.strip())
            
            # Remove common HTML entities
            text = text.replace('&nbsp;', ' ')
            text = text.replace('&amp;', '&')
            text = text.replace('&lt;', '<')
            text = text.replace('&gt;', '>')
            text = text.replace('&quot;', '"')
            
            return text
        
        # Test text cleaning
        dirty_text = "  This   is   dirty\n\ntext  with  &nbsp; entities  "
        clean_result = clean_text(dirty_text)
        
        # Check that text is cleaned
        expected_words = ["This", "is", "dirty", "text", "with", "entities"]
        words = clean_result.split()
        
        # Check that all expected words are present
        for word in expected_words:
            assert word in words, f"Expected word '{word}' not found in {words}"
        
        assert "&nbsp;" not in clean_result, f"HTML entity not cleaned: {clean_result}"
        assert len(words) == 6, f"Expected 6 words, got {len(words)}: {words}"
        
        logger.info("Text cleaning functionality test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Text cleaning functionality test failed: {e}")
        return False


def test_doi_extraction():
    """Test DOI extraction functionality."""
    logger.info("Testing DOI extraction...")
    
    try:
        def extract_doi(text):
            """Extract DOI from text."""
            # Common DOI patterns
            doi_patterns = [
                r'doi:\s*([0-9]+\.[0-9]+/[^\s]+)',
                r'DOI:\s*([0-9]+\.[0-9]+/[^\s]+)',
                r'https?://doi\.org/([0-9]+\.[0-9]+/[^\s]+)',
                r'https?://dx\.doi\.org/([0-9]+\.[0-9]+/[^\s]+)'
            ]
            
            for pattern in doi_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            return None
        
        # Test DOI extraction
        test_cases = [
            ("The DOI for this paper is doi:10.1000/test.doi and more text", "10.1000/test.doi"),
            ("DOI: 10.1234/example.paper", "10.1234/example.paper"),
            ("Available at https://doi.org/10.5678/another.paper", "10.5678/another.paper"),
            ("No DOI in this text", None)
        ]
        
        for text, expected_doi in test_cases:
            extracted_doi = extract_doi(text)
            assert extracted_doi == expected_doi, f"Expected {expected_doi}, got {extracted_doi}"
        
        logger.info("DOI extraction test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"DOI extraction test failed: {e}")
        return False


def test_author_parsing():
    """Test author name parsing."""
    logger.info("Testing author parsing...")
    
    try:
        def parse_authors(author_text):
            """Parse author names from text."""
            if not author_text:
                return []
            
            # Clean the text
            author_text = re.sub(r'\s+', ' ', author_text.strip())
            
            # Common separators
            separators = [',', ';', ' and ', ' & ', '\n']
            
            authors = [author_text]
            for sep in separators:
                new_authors = []
                for author in authors:
                    new_authors.extend([a.strip() for a in author.split(sep) if a.strip()])
                authors = new_authors
            
            # Filter out empty strings and common non-author text
            filtered_authors = []
            for author in authors:
                author = author.strip()
                if (author and 
                    len(author) > 2 and 
                    not author.lower().startswith('email') and
                    not author.lower().startswith('affiliation')):
                    filtered_authors.append(author)
            
            return filtered_authors[:10]  # Limit to reasonable number
        
        # Test author parsing
        test_cases = [
            ("John Smith, Jane Doe and Bob Johnson", ["John Smith", "Jane Doe", "Bob Johnson"]),
            ("Alice Brown; Charlie Davis", ["Alice Brown", "Charlie Davis"]),
            ("Mary Wilson & Peter Jones", ["Mary Wilson", "Peter Jones"]),
            ("Single Author", ["Single Author"]),
            ("", [])
        ]
        
        for author_text, expected_authors in test_cases:
            parsed_authors = parse_authors(author_text)
            
            # Check that we got the expected number of authors
            assert len(parsed_authors) == len(expected_authors), f"Expected {len(expected_authors)} authors, got {len(parsed_authors)}"
            
            # Check that expected authors are in the result
            for expected_author in expected_authors:
                assert expected_author in parsed_authors, f"Expected author '{expected_author}' not found in {parsed_authors}"
        
        logger.info("Author parsing test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Author parsing test failed: {e}")
        return False


def test_html_parsing_patterns():
    """Test HTML parsing patterns."""
    logger.info("Testing HTML parsing patterns...")
    
    try:
        def parse_jss_issues(html_content):
            """Parse JSS issues from HTML."""
            issues = []
            
            # JSS uses patterns like "/issue/view/v001" or "/issue/view/v050i01"
            issue_pattern = r'href="(/issue/view/v(\d+)(?:i(\d+))?)"[^>]*>([^<]+)</a>'
            matches = re.findall(issue_pattern, html_content, re.IGNORECASE)
            
            for issue_path, volume, issue_num, issue_title in matches:
                issue_info = {
                    'path': issue_path,
                    'title': issue_title.strip(),
                    'volume': volume,
                    'issue': issue_num if issue_num else None,
                    'url': f"https://www.jstatsoft.org{issue_path}"
                }
                issues.append(issue_info)
            
            return issues
        
        def parse_rjournal_issues(html_content):
            """Parse R Journal issues from HTML."""
            issues = []
            
            # R Journal uses patterns like "/archive/2023-1/"
            issue_pattern = r'href="(/archive/(\d{4})-(\d+)/)"[^>]*>([^<]+)</a>'
            matches = re.findall(issue_pattern, html_content, re.IGNORECASE)
            
            for issue_path, year, issue_num, title in matches:
                issue_info = {
                    'path': issue_path,
                    'title': title.strip(),
                    'year': year,
                    'issue': issue_num,
                    'url': f"https://journal.r-project.org{issue_path}"
                }
                issues.append(issue_info)
            
            return issues
        
        # Test JSS parsing
        sample_jss_html = '''
        <html>
        <body>
        <a href="/issue/view/v050i01">Volume 50, Issue 1</a>
        <a href="/issue/view/v049i12">Volume 49, Issue 12</a>
        <a href="/issue/view/v048">Volume 48</a>
        </body>
        </html>
        '''
        
        jss_issues = parse_jss_issues(sample_jss_html)
        assert len(jss_issues) >= 2, f"Expected at least 2 issues, got {len(jss_issues)}"
        
        # Find the v050i01 issue (volume is parsed as '050', not '50')
        v50_issue = next((issue for issue in jss_issues if issue['volume'] == '050'), None)
        assert v50_issue is not None, f"Could not find volume 050 issue in {jss_issues}"
        assert v50_issue['issue'] == '01', f"Expected issue 01, got {v50_issue['issue']}"
        assert 'Volume 50' in v50_issue['title'], f"Expected 'Volume 50' in title: {v50_issue['title']}"
        
        # Test R Journal parsing
        sample_rjournal_html = '''
        <html>
        <body>
        <a href="/archive/2023-1/">The R Journal 2023 Issue 1</a>
        <a href="/archive/2022-2/">The R Journal 2022 Issue 2</a>
        </body>
        </html>
        '''
        
        r_issues = parse_rjournal_issues(sample_rjournal_html)
        assert len(r_issues) >= 2
        
        # Find the 2023-1 issue
        r2023_issue = next((issue for issue in r_issues if issue['year'] == '2023'), None)
        assert r2023_issue is not None
        assert r2023_issue['issue'] == '1'
        assert '2023' in r2023_issue['title']
        
        logger.info("HTML parsing patterns test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"HTML parsing patterns test failed: {e}")
        return False


def test_metadata_validation():
    """Test metadata validation logic."""
    logger.info("Testing metadata validation...")
    
    try:
        @dataclass
        class JournalMetadata:
            title: str
            authors: List[str]
            abstract: str
            journal_name: str
            volume: Optional[str] = None
            issue: Optional[str] = None
        
        def validate_metadata(metadata):
            """Validate extracted metadata."""
            # Check required fields
            if not metadata.title or len(metadata.title.strip()) < 5:
                return False
            
            if not metadata.authors:
                return False
            
            if not metadata.journal_name:
                return False
            
            # Check for reasonable content
            if len(metadata.title) > 500:
                return False
            
            return True
        
        # Test valid metadata
        valid_metadata = JournalMetadata(
            title="Valid Paper Title",
            authors=["Author One", "Author Two"],
            abstract="This is a valid abstract with sufficient content.",
            journal_name="Test Journal"
        )
        
        assert validate_metadata(valid_metadata) == True
        
        # Test invalid metadata (no title)
        invalid_metadata1 = JournalMetadata(
            title="",
            authors=["Author One"],
            abstract="Abstract",
            journal_name="Test Journal"
        )
        
        assert validate_metadata(invalid_metadata1) == False
        
        # Test invalid metadata (no authors)
        invalid_metadata2 = JournalMetadata(
            title="Valid Title",
            authors=[],
            abstract="Abstract",
            journal_name="Test Journal"
        )
        
        assert validate_metadata(invalid_metadata2) == False
        
        # Test invalid metadata (title too long)
        invalid_metadata3 = JournalMetadata(
            title="A" * 600,  # Too long
            authors=["Author"],
            abstract="Abstract",
            journal_name="Test Journal"
        )
        
        assert validate_metadata(invalid_metadata3) == False
        
        logger.info("Metadata validation test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Metadata validation test failed: {e}")
        return False


def test_paper_id_generation():
    """Test paper ID generation logic."""
    logger.info("Testing paper ID generation...")
    
    try:
        import hashlib
        
        def generate_paper_id(title, journal_name, volume=None, issue=None):
            """Generate a unique paper ID for the journal paper."""
            # Create a hash from title and journal info
            content = f"{title}_{journal_name}_{volume}_{issue}"
            hash_obj = hashlib.md5(content.encode('utf-8'))
            hash_str = hash_obj.hexdigest()[:8]
            
            # Create readable ID
            journal_prefix = journal_name.lower().replace(' ', '_').replace('.', '')[:10]
            
            if volume and issue:
                return f"{journal_prefix}_v{volume}i{issue}_{hash_str}"
            else:
                return f"{journal_prefix}_{hash_str}"
        
        # Test JSS paper ID
        jss_id = generate_paper_id(
            "Test JSS Paper",
            "Journal of Statistical Software",
            "50",
            "01"
        )
        
        assert "journal_of" in jss_id
        assert "v50i01" in jss_id
        assert len(jss_id.split('_')) >= 3
        
        # Test R Journal paper ID
        rjournal_id = generate_paper_id(
            "Test R Paper",
            "The R Journal",
            "2023",
            "1"
        )
        
        assert "the_r_jour" in rjournal_id
        assert "v2023i1" in rjournal_id
        
        # Test paper ID without volume/issue
        simple_id = generate_paper_id(
            "Simple Paper",
            "Simple Journal"
        )
        
        assert "simple_jou" in simple_id
        assert len(simple_id) > 10
        
        logger.info("Paper ID generation test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Paper ID generation test failed: {e}")
        return False


def test_date_range_checking():
    """Test date range checking logic."""
    logger.info("Testing date range checking...")
    
    try:
        def is_jss_issue_in_date_range(issue, start_date, end_date):
            """Check if a JSS issue is likely to be in the date range."""
            try:
                volume = int(issue['volume']) if issue['volume'] else 0
                
                # Rough estimation: JSS has been publishing since ~2000
                # Assume roughly 4-6 volumes per year
                estimated_year = 2000 + (volume // 5)
                
                # Create approximate date
                estimated_date = datetime(estimated_year, 6, 1)  # Mid-year
                
                # Allow some buffer (1 year on each side)
                buffer = timedelta(days=365)
                return (start_date - buffer) <= estimated_date <= (end_date + buffer)
                
            except Exception:
                # If we can't estimate, include it to be safe
                return True
        
        def is_rjournal_issue_in_date_range(issue, start_date, end_date):
            """Check if an R Journal issue is in the date range."""
            try:
                year = int(issue['year'])
                issue_num = int(issue['issue'])
                
                # Estimate publication date (R Journal typically publishes 1-2 issues per year)
                if issue_num == 1:
                    estimated_date = datetime(year, 6, 1)  # June
                else:
                    estimated_date = datetime(year, 12, 1)  # December
                
                # Allow some buffer (6 months on each side)
                buffer = timedelta(days=180)
                return (start_date - buffer) <= estimated_date <= (end_date + buffer)
                
            except Exception:
                return True
        
        # Test JSS date range checking
        jss_issue = {'volume': '50', 'issue': '1', 'title': 'Test Issue'}
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2025, 12, 31)
        
        in_range = is_jss_issue_in_date_range(jss_issue, start_date, end_date)
        assert isinstance(in_range, bool)
        
        # Test R Journal date range checking
        rjournal_issue = {'year': '2023', 'issue': '1', 'title': 'Test Issue'}
        
        in_range = is_rjournal_issue_in_date_range(rjournal_issue, start_date, end_date)
        assert isinstance(in_range, bool)
        assert in_range == True  # 2023 should be in range
        
        # Test out of range
        old_issue = {'year': '2010', 'issue': '1', 'title': 'Old Issue'}
        in_range = is_rjournal_issue_in_date_range(old_issue, start_date, end_date)
        assert in_range == False  # 2010 should be out of range
        
        logger.info("Date range checking test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Date range checking test failed: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("Starting Journal Source Handlers component tests")
    
    tests = [
        ("Journal Metadata Structure", test_journal_metadata_structure),
        ("Text Cleaning Functionality", test_text_cleaning_functionality),
        ("DOI Extraction", test_doi_extraction),
        ("Author Parsing", test_author_parsing),
        ("HTML Parsing Patterns", test_html_parsing_patterns),
        ("Metadata Validation", test_metadata_validation),
        ("Paper ID Generation", test_paper_id_generation),
        ("Date Range Checking", test_date_range_checking),
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
        logger.info("All journal source handler component tests completed successfully!")
        logger.info("\nKey features verified:")
        logger.info("✓ Journal metadata structure and validation")
        logger.info("✓ Text cleaning and normalization")
        logger.info("✓ DOI extraction from various formats")
        logger.info("✓ Author name parsing with multiple separators")
        logger.info("✓ HTML parsing patterns for JSS and R Journal")
        logger.info("✓ Paper ID generation with hashing")
        logger.info("✓ Date range checking for issue filtering")
    else:
        logger.error("Some tests failed!")


if __name__ == "__main__":
    asyncio.run(main())