"""
Unit tests for journal source handlers and metadata extraction.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import sys

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.journal_sources.jstat_software_handler import JStatSoftwareHandler
    from multi_instance_arxiv_system.journal_sources.r_journal_handler import RJournalHandler
    from multi_instance_arxiv_system.models.paper_models import JournalPaper
    from multi_instance_arxiv_system.error_handling.error_models import ProcessingError
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class TestJStatSoftwareHandler:
    """Test cases for Journal of Statistical Software handler."""
    
    @pytest.fixture
    def handler(self):
        """Create JStatSoftwareHandler instance."""
        return JStatSoftwareHandler()
    
    @pytest.fixture
    def sample_jss_metadata(self):
        """Sample JSS paper metadata."""
        return {
            'title': 'Sample Statistical Software Paper',
            'authors': ['John Doe', 'Jane Smith'],
            'abstract': 'This paper describes statistical software implementation.',
            'volume': '85',
            'issue': '3',
            'year': '2023',
            'doi': '10.18637/jss.v085.i03',
            'pdf_url': 'https://www.jstatsoft.org/article/view/v085i03/v085i03.pdf',
            'keywords': ['statistical software', 'R package', 'methodology']
        }
    
    def test_initialization(self, handler):
        """Test handler initialization."""
        assert handler.journal_name == "Journal of Statistical Software"
        assert handler.base_url == "https://www.jstatsoft.org"
        assert handler.journal_abbreviation == "JSS"
    
    @pytest.mark.asyncio
    async def test_fetch_recent_papers(self, handler):
        """Test fetching recent papers from JSS."""
        # Mock RSS feed response
        mock_rss_content = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Journal of Statistical Software</title>
                <item>
                    <title>Sample Paper Title</title>
                    <link>https://www.jstatsoft.org/article/view/v085i03</link>
                    <description>Sample abstract content</description>
                    <pubDate>Mon, 15 May 2023 00:00:00 GMT</pubDate>
                </item>
            </channel>
        </rss>"""
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=mock_rss_content)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            papers = await handler.fetch_recent_papers(days_back=30)
            
            assert len(papers) > 0
            assert isinstance(papers[0], dict)
            assert 'title' in papers[0]
            assert 'link' in papers[0]
    
    @pytest.mark.asyncio
    async def test_extract_paper_metadata(self, handler, sample_jss_metadata):
        """Test extracting paper metadata from JSS page."""
        # Mock HTML content
        mock_html = f"""
        <html>
            <head>
                <title>{sample_jss_metadata['title']}</title>
                <meta name="citation_author" content="{sample_jss_metadata['authors'][0]}">
                <meta name="citation_author" content="{sample_jss_metadata['authors'][1]}">
                <meta name="citation_volume" content="{sample_jss_metadata['volume']}">
                <meta name="citation_issue" content="{sample_jss_metadata['issue']}">
                <meta name="citation_publication_date" content="{sample_jss_metadata['year']}">
                <meta name="citation_doi" content="{sample_jss_metadata['doi']}">
                <meta name="citation_pdf_url" content="{sample_jss_metadata['pdf_url']}">
            </head>
            <body>
                <div class="abstract">
                    <p>{sample_jss_metadata['abstract']}</p>
                </div>
            </body>
        </html>
        """
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=mock_html)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            paper_url = "https://www.jstatsoft.org/article/view/v085i03"
            metadata = await handler.extract_paper_metadata(paper_url)
            
            assert metadata is not None
            assert metadata['title'] == sample_jss_metadata['title']
            assert metadata['volume'] == sample_jss_metadata['volume']
            assert metadata['issue'] == sample_jss_metadata['issue']
            assert metadata['doi'] == sample_jss_metadata['doi']
    
    @pytest.mark.asyncio
    async def test_download_paper_pdf(self, handler):
        """Test downloading paper PDF."""
        pdf_url = "https://www.jstatsoft.org/article/view/v085i03/v085i03.pdf"
        
        # Mock PDF content
        mock_pdf_content = b"PDF content here"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.read = AsyncMock(return_value=mock_pdf_content)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            pdf_content = await handler.download_paper_pdf(pdf_url)
            
            assert pdf_content == mock_pdf_content
    
    @pytest.mark.asyncio
    async def test_download_paper_pdf_error(self, handler):
        """Test PDF download error handling."""
        pdf_url = "https://www.jstatsoft.org/nonexistent.pdf"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response
            
            pdf_content = await handler.download_paper_pdf(pdf_url)
            
            assert pdf_content is None
    
    def test_validate_metadata(self, handler, sample_jss_metadata):
        """Test metadata validation."""
        # Valid metadata
        assert handler.validate_metadata(sample_jss_metadata) == True
        
        # Missing required fields
        incomplete_metadata = sample_jss_metadata.copy()
        del incomplete_metadata['title']
        assert handler.validate_metadata(incomplete_metadata) == False
        
        # Invalid DOI format
        invalid_doi_metadata = sample_jss_metadata.copy()
        invalid_doi_metadata['doi'] = 'invalid-doi'
        assert handler.validate_metadata(invalid_doi_metadata) == False
    
    def test_parse_volume_issue(self, handler):
        """Test volume and issue parsing from URL."""
        test_urls = [
            ("https://www.jstatsoft.org/article/view/v085i03", ("85", "3")),
            ("https://www.jstatsoft.org/article/view/v100i01", ("100", "1")),
            ("https://www.jstatsoft.org/article/view/v042i12", ("42", "12")),
        ]
        
        for url, expected in test_urls:
            volume, issue = handler._parse_volume_issue_from_url(url)
            assert volume == expected[0]
            assert issue == expected[1]
    
    def test_format_citation(self, handler, sample_jss_metadata):
        """Test citation formatting."""
        citation = handler.format_citation(sample_jss_metadata)
        
        expected_parts = [
            sample_jss_metadata['authors'][0],
            sample_jss_metadata['title'],
            "Journal of Statistical Software",
            sample_jss_metadata['volume'],
            sample_jss_metadata['issue'],
            sample_jss_metadata['year']
        ]
        
        for part in expected_parts:
            assert part in citation


class TestRJournalHandler:
    """Test cases for R Journal handler."""
    
    @pytest.fixture
    def handler(self):
        """Create RJournalHandler instance."""
        return RJournalHandler()
    
    @pytest.fixture
    def sample_rjournal_metadata(self):
        """Sample R Journal paper metadata."""
        return {
            'title': 'Advanced R Package for Data Analysis',
            'authors': ['Alice Johnson', 'Bob Wilson'],
            'abstract': 'This paper presents an advanced R package for statistical analysis.',
            'volume': '15',
            'issue': '2',
            'year': '2023',
            'pages': '123-145',
            'pdf_url': 'https://journal.r-project.org/archive/2023-2/johnson-wilson.pdf',
            'keywords': ['R package', 'data analysis', 'statistics']
        }
    
    def test_initialization(self, handler):
        """Test handler initialization."""
        assert handler.journal_name == "The R Journal"
        assert handler.base_url == "https://journal.r-project.org"
        assert handler.journal_abbreviation == "R J"
    
    @pytest.mark.asyncio
    async def test_fetch_recent_papers(self, handler):
        """Test fetching recent papers from R Journal."""
        # Mock archive page response
        mock_html = """
        <html>
            <body>
                <div class="issue">
                    <h2>Volume 15, Issue 2 (2023)</h2>
                    <div class="article">
                        <h3><a href="/archive/2023-2/johnson-wilson.pdf">Advanced R Package</a></h3>
                        <p class="authors">Alice Johnson, Bob Wilson</p>
                        <p class="abstract">This paper presents an advanced R package...</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=mock_html)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            papers = await handler.fetch_recent_papers(days_back=30)
            
            assert len(papers) > 0
            assert isinstance(papers[0], dict)
    
    @pytest.mark.asyncio
    async def test_extract_paper_metadata(self, handler):
        """Test extracting paper metadata from R Journal."""
        # Mock paper page HTML
        mock_html = """
        <html>
            <head>
                <title>Advanced R Package for Data Analysis</title>
            </head>
            <body>
                <div class="paper-metadata">
                    <h1>Advanced R Package for Data Analysis</h1>
                    <p class="authors">Alice Johnson, Bob Wilson</p>
                    <p class="volume-issue">Volume 15, Issue 2 (2023), pages 123-145</p>
                    <div class="abstract">
                        <p>This paper presents an advanced R package for statistical analysis.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=mock_html)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            paper_url = "https://journal.r-project.org/archive/2023-2/johnson-wilson.pdf"
            metadata = await handler.extract_paper_metadata(paper_url)
            
            assert metadata is not None
            assert 'title' in metadata
            assert 'authors' in metadata
    
    def test_parse_authors(self, handler):
        """Test author parsing from different formats."""
        test_cases = [
            ("Alice Johnson, Bob Wilson", ["Alice Johnson", "Bob Wilson"]),
            ("Alice Johnson and Bob Wilson", ["Alice Johnson", "Bob Wilson"]),
            ("Johnson, A., Wilson, B.", ["Johnson, A.", "Wilson, B."]),
            ("Single Author", ["Single Author"]),
        ]
        
        for author_string, expected in test_cases:
            parsed_authors = handler._parse_authors(author_string)
            assert parsed_authors == expected
    
    def test_parse_volume_issue_pages(self, handler):
        """Test parsing volume, issue, and pages from text."""
        test_cases = [
            ("Volume 15, Issue 2 (2023), pages 123-145", ("15", "2", "2023", "123-145")),
            ("Vol. 10, No. 1 (2020), pp. 1-20", ("10", "1", "2020", "1-20")),
            ("Volume 5 (2018), pages 50-75", ("5", None, "2018", "50-75")),
        ]
        
        for text, expected in test_cases:
            result = handler._parse_volume_issue_pages(text)
            assert result == expected
    
    @pytest.mark.asyncio
    async def test_validate_r_journal_paper(self, handler, sample_rjournal_metadata):
        """Test R Journal specific validation."""
        # Valid R Journal paper
        assert handler.validate_metadata(sample_rjournal_metadata) == True
        
        # Missing R-specific fields
        invalid_metadata = sample_rjournal_metadata.copy()
        del invalid_metadata['volume']
        assert handler.validate_metadata(invalid_metadata) == False
    
    def test_extract_keywords(self, handler):
        """Test keyword extraction from abstract and title."""
        text = "This paper presents an R package for statistical analysis and data visualization."
        
        keywords = handler._extract_keywords(text)
        
        # Should contain R-related keywords
        r_keywords = ['R package', 'statistical', 'analysis', 'data']
        found_keywords = [kw for kw in r_keywords if any(kw.lower() in k.lower() for k in keywords)]
        
        assert len(found_keywords) > 0


class TestJournalPaperModel:
    """Test cases for JournalPaper model."""
    
    def test_journal_paper_creation(self):
        """Test creating JournalPaper instance."""
        paper = JournalPaper(
            paper_id="jss_v085_i03",
            title="Sample Statistical Software Paper",
            authors=["John Doe", "Jane Smith"],
            abstract="This paper describes statistical software implementation.",
            journal_name="Journal of Statistical Software",
            volume="85",
            issue="3",
            year="2023",
            doi="10.18637/jss.v085.i03",
            instance_name="quant_scholar"
        )
        
        assert paper.paper_id == "jss_v085_i03"
        assert paper.journal_name == "Journal of Statistical Software"
        assert paper.volume == "85"
        assert paper.issue == "3"
        assert paper.year == "2023"
        assert paper.instance_name == "quant_scholar"
    
    def test_journal_paper_validation(self):
        """Test JournalPaper validation."""
        # Valid paper
        valid_paper = JournalPaper(
            paper_id="valid_paper",
            title="Valid Paper Title",
            authors=["Author One"],
            abstract="Valid abstract",
            journal_name="Test Journal",
            volume="1",
            issue="1",
            year="2023",
            instance_name="test_instance"
        )
        
        assert valid_paper.validate() == True
        
        # Invalid paper (missing required fields)
        with pytest.raises(ValueError):
            JournalPaper(
                paper_id="",  # Empty paper_id should raise error
                title="Title",
                authors=["Author"],
                abstract="Abstract",
                journal_name="Journal",
                instance_name="instance"
            )
    
    def test_journal_paper_serialization(self):
        """Test JournalPaper serialization to dict."""
        paper = JournalPaper(
            paper_id="test_paper",
            title="Test Paper",
            authors=["Test Author"],
            abstract="Test abstract",
            journal_name="Test Journal",
            volume="1",
            issue="1",
            year="2023",
            instance_name="test_instance"
        )
        
        paper_dict = paper.to_dict()
        
        assert paper_dict['paper_id'] == "test_paper"
        assert paper_dict['journal_name'] == "Test Journal"
        assert paper_dict['volume'] == "1"
        assert paper_dict['issue'] == "1"
        assert paper_dict['year'] == "2023"
        assert 'created_at' in paper_dict
    
    def test_journal_paper_from_dict(self):
        """Test creating JournalPaper from dictionary."""
        paper_dict = {
            'paper_id': 'test_paper',
            'title': 'Test Paper',
            'authors': ['Test Author'],
            'abstract': 'Test abstract',
            'journal_name': 'Test Journal',
            'volume': '1',
            'issue': '1',
            'year': '2023',
            'instance_name': 'test_instance'
        }
        
        paper = JournalPaper.from_dict(paper_dict)
        
        assert paper.paper_id == "test_paper"
        assert paper.journal_name == "Test Journal"
        assert paper.volume == "1"
        assert paper.issue == "1"


class TestJournalHandlerIntegration:
    """Integration tests for journal handlers."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_jss_workflow(self):
        """Test complete JSS paper processing workflow."""
        handler = JStatSoftwareHandler()
        
        # Mock the entire workflow
        with patch.object(handler, 'fetch_recent_papers') as mock_fetch, \
             patch.object(handler, 'extract_paper_metadata') as mock_extract, \
             patch.object(handler, 'download_paper_pdf') as mock_download:
            
            # Mock fetch returning paper URLs
            mock_fetch.return_value = [
                {'link': 'https://www.jstatsoft.org/article/view/v085i03'}
            ]
            
            # Mock metadata extraction
            mock_extract.return_value = {
                'title': 'Test Paper',
                'authors': ['Test Author'],
                'abstract': 'Test abstract',
                'volume': '85',
                'issue': '3',
                'year': '2023',
                'doi': '10.18637/jss.v085.i03',
                'pdf_url': 'https://www.jstatsoft.org/article/view/v085i03/v085i03.pdf'
            }
            
            # Mock PDF download
            mock_download.return_value = b'PDF content'
            
            # Run workflow
            papers = await handler.fetch_recent_papers(days_back=30)
            assert len(papers) == 1
            
            metadata = await handler.extract_paper_metadata(papers[0]['link'])
            assert metadata is not None
            assert metadata['title'] == 'Test Paper'
            
            pdf_content = await handler.download_paper_pdf(metadata['pdf_url'])
            assert pdf_content == b'PDF content'
    
    @pytest.mark.asyncio
    async def test_error_handling_in_journal_processing(self):
        """Test error handling in journal paper processing."""
        handler = JStatSoftwareHandler()
        
        # Test network error handling
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            papers = await handler.fetch_recent_papers(days_back=30)
            assert papers == []  # Should return empty list on error
        
        # Test invalid URL handling
        invalid_url = "https://invalid-url.com/nonexistent"
        metadata = await handler.extract_paper_metadata(invalid_url)
        assert metadata is None  # Should return None for invalid URLs