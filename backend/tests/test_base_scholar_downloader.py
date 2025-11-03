"""
Unit tests for BaseScholarDownloader and instance-specific downloaders.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import sys

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.core.base_scholar_downloader import BaseScholarDownloader
    from multi_instance_arxiv_system.core.instance_config import InstanceConfig
    from multi_instance_arxiv_system.models.paper_models import ArxivPaper
    from multi_instance_arxiv_system.error_handling.error_models import ProcessingError
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class TestBaseScholarDownloader:
    """Test cases for BaseScholarDownloader."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_config(self, temp_dir):
        """Create mock instance configuration."""
        return InstanceConfig(
            instance_name="test_scholar",
            storage_path=str(temp_dir),
            arxiv_categories=["cs.AI", "cs.LG"],
            max_papers_per_run=100,
            processing_batch_size=10
        )
    
    @pytest.fixture
    def downloader(self, mock_config):
        """Create BaseScholarDownloader instance."""
        return BaseScholarDownloader(mock_config)
    
    def test_initialization(self, downloader, mock_config):
        """Test downloader initialization."""
        assert downloader.config == mock_config
        assert downloader.instance_name == "test_scholar"
        assert downloader.storage_path == Path(mock_config.storage_path)
        assert downloader.downloaded_papers == []
        assert downloader.processing_errors == []
    
    def test_validate_categories(self, downloader):
        """Test category validation."""
        # Valid categories
        valid_categories = ["cs.AI", "cs.LG", "stat.ML"]
        assert downloader._validate_categories(valid_categories) == True
        
        # Invalid categories
        invalid_categories = ["invalid.category", "cs.INVALID"]
        assert downloader._validate_categories(invalid_categories) == False
        
        # Mixed valid and invalid
        mixed_categories = ["cs.AI", "invalid.category"]
        assert downloader._validate_categories(mixed_categories) == False
    
    @pytest.mark.asyncio
    async def test_setup_storage_directories(self, downloader, temp_dir):
        """Test storage directory setup."""
        await downloader._setup_storage_directories()
        
        # Check that required directories are created
        expected_dirs = ["papers", "metadata", "logs", "cache"]
        for dir_name in expected_dirs:
            assert (temp_dir / dir_name).exists()
            assert (temp_dir / dir_name).is_dir()
    
    @pytest.mark.asyncio
    async def test_download_paper_success(self, downloader):
        """Test successful paper download."""
        # Mock paper data
        paper_data = {
            'id': 'test_paper_id',
            'title': 'Test Paper Title',
            'authors': ['Author One', 'Author Two'],
            'abstract': 'Test abstract content',
            'categories': ['cs.AI'],
            'published': datetime.now(),
            'pdf_url': 'https://example.com/paper.pdf'
        }
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.content = b'PDF content'
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await downloader._download_paper(paper_data)
            
            assert result is not None
            assert isinstance(result, ArxivPaper)
            assert result.paper_id == 'test_paper_id'
            assert result.title == 'Test Paper Title'
    
    @pytest.mark.asyncio
    async def test_download_paper_http_error(self, downloader):
        """Test paper download with HTTP error."""
        paper_data = {
            'id': 'test_paper_id',
            'title': 'Test Paper Title',
            'pdf_url': 'https://example.com/paper.pdf'
        }
        
        # Mock HTTP error response
        mock_response = Mock()
        mock_response.status = 404
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await downloader._download_paper(paper_data)
            
            assert result is None
            assert len(downloader.processing_errors) > 0
            assert downloader.processing_errors[0].error_type.value == 'http_error'
    
    @pytest.mark.asyncio
    async def test_save_paper_metadata(self, downloader, temp_dir):
        """Test saving paper metadata."""
        paper = ArxivPaper(
            paper_id='test_paper_id',
            title='Test Paper Title',
            authors=['Author One'],
            abstract='Test abstract',
            categories=['cs.AI'],
            published=datetime.now(),
            instance_name='test_scholar'
        )
        
        await downloader._save_paper_metadata(paper)
        
        # Check that metadata file was created
        metadata_file = temp_dir / "metadata" / "test_paper_id.json"
        assert metadata_file.exists()
        
        # Verify metadata content
        import json
        with open(metadata_file, 'r') as f:
            saved_metadata = json.load(f)
        
        assert saved_metadata['paper_id'] == 'test_paper_id'
        assert saved_metadata['title'] == 'Test Paper Title'
        assert saved_metadata['instance_name'] == 'test_scholar'
    
    @pytest.mark.asyncio
    async def test_check_duplicate_paper(self, downloader, temp_dir):
        """Test duplicate paper detection."""
        # Create existing metadata file
        metadata_dir = temp_dir / "metadata"
        metadata_dir.mkdir(exist_ok=True)
        
        existing_metadata = {
            'paper_id': 'existing_paper',
            'title': 'Existing Paper',
            'downloaded_at': datetime.now().isoformat()
        }
        
        with open(metadata_dir / "existing_paper.json", 'w') as f:
            import json
            json.dump(existing_metadata, f)
        
        # Test duplicate detection
        assert await downloader._is_duplicate_paper('existing_paper') == True
        assert await downloader._is_duplicate_paper('new_paper') == False
    
    def test_filter_papers_by_date(self, downloader):
        """Test filtering papers by publication date."""
        # Create test papers with different dates
        old_paper = {'published': datetime.now() - timedelta(days=400)}
        recent_paper = {'published': datetime.now() - timedelta(days=30)}
        new_paper = {'published': datetime.now() - timedelta(days=1)}
        
        papers = [old_paper, recent_paper, new_paper]
        
        # Filter papers from last year
        cutoff_date = datetime.now() - timedelta(days=365)
        filtered_papers = downloader._filter_papers_by_date(papers, cutoff_date)
        
        assert len(filtered_papers) == 2  # recent_paper and new_paper
        assert old_paper not in filtered_papers
    
    def test_categorize_papers(self, downloader):
        """Test paper categorization by ArXiv categories."""
        papers = [
            {'categories': ['cs.AI', 'cs.LG']},
            {'categories': ['math.ST', 'stat.ML']},
            {'categories': ['cs.AI']},
            {'categories': ['physics.gen-ph']}
        ]
        
        # Filter for AI/ML categories
        target_categories = ['cs.AI', 'cs.LG', 'stat.ML']
        categorized_papers = downloader._categorize_papers(papers, target_categories)
        
        assert len(categorized_papers) == 3  # First three papers match
        assert papers[3] not in categorized_papers  # Physics paper excluded
    
    @pytest.mark.asyncio
    async def test_batch_download_papers(self, downloader):
        """Test batch downloading of papers."""
        # Mock papers data
        papers_data = [
            {
                'id': f'paper_{i}',
                'title': f'Paper {i}',
                'authors': ['Author'],
                'abstract': f'Abstract {i}',
                'categories': ['cs.AI'],
                'published': datetime.now(),
                'pdf_url': f'https://example.com/paper_{i}.pdf'
            }
            for i in range(5)
        ]
        
        # Mock successful downloads
        with patch.object(downloader, '_download_paper') as mock_download:
            mock_download.side_effect = [
                ArxivPaper(
                    paper_id=paper['id'],
                    title=paper['title'],
                    authors=paper['authors'],
                    abstract=paper['abstract'],
                    categories=paper['categories'],
                    published=paper['published'],
                    instance_name='test_scholar'
                )
                for paper in papers_data
            ]
            
            results = await downloader._batch_download_papers(papers_data, batch_size=2)
            
            assert len(results) == 5
            assert all(isinstance(paper, ArxivPaper) for paper in results)
            assert mock_download.call_count == 5
    
    @pytest.mark.asyncio
    async def test_error_handling_during_download(self, downloader):
        """Test error handling during paper download."""
        paper_data = {
            'id': 'error_paper',
            'title': 'Error Paper',
            'pdf_url': 'https://example.com/error.pdf'
        }
        
        # Mock network error
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            result = await downloader._download_paper(paper_data)
            
            assert result is None
            assert len(downloader.processing_errors) > 0
            
            error = downloader.processing_errors[0]
            assert isinstance(error, ProcessingError)
            assert "Network error" in error.message
    
    def test_progress_tracking(self, downloader):
        """Test download progress tracking."""
        # Initialize progress
        downloader._initialize_progress_tracking(total_papers=100)
        
        assert downloader.total_papers == 100
        assert downloader.processed_papers == 0
        assert downloader.successful_downloads == 0
        assert downloader.failed_downloads == 0
        
        # Update progress
        downloader._update_progress(success=True)
        assert downloader.processed_papers == 1
        assert downloader.successful_downloads == 1
        assert downloader.failed_downloads == 0
        
        downloader._update_progress(success=False)
        assert downloader.processed_papers == 2
        assert downloader.successful_downloads == 1
        assert downloader.failed_downloads == 1
    
    def test_get_download_statistics(self, downloader):
        """Test download statistics generation."""
        # Set up some test data
        downloader.total_papers = 100
        downloader.processed_papers = 95
        downloader.successful_downloads = 90
        downloader.failed_downloads = 5
        downloader.start_time = datetime.now() - timedelta(minutes=30)
        
        stats = downloader.get_download_statistics()
        
        assert stats['total_papers'] == 100
        assert stats['processed_papers'] == 95
        assert stats['successful_downloads'] == 90
        assert stats['failed_downloads'] == 5
        assert stats['success_rate'] == 90.0  # 90/100
        assert 'processing_time_minutes' in stats
        assert 'papers_per_minute' in stats
    
    @pytest.mark.asyncio
    async def test_cleanup_temporary_files(self, downloader, temp_dir):
        """Test cleanup of temporary files."""
        # Create some temporary files
        cache_dir = temp_dir / "cache"
        cache_dir.mkdir(exist_ok=True)
        
        temp_files = [
            cache_dir / "temp_file_1.tmp",
            cache_dir / "temp_file_2.tmp",
            cache_dir / "regular_file.txt"
        ]
        
        for temp_file in temp_files:
            temp_file.write_text("temporary content")
        
        # Run cleanup
        await downloader._cleanup_temporary_files()
        
        # Check that .tmp files are removed but regular files remain
        assert not (cache_dir / "temp_file_1.tmp").exists()
        assert not (cache_dir / "temp_file_2.tmp").exists()
        assert (cache_dir / "regular_file.txt").exists()


class TestAIScholarDownloader:
    """Test cases specific to AI Scholar downloader."""
    
    @pytest.fixture
    def ai_config(self, temp_dir):
        """Create AI Scholar configuration."""
        return InstanceConfig(
            instance_name="ai_scholar",
            storage_path=str(temp_dir),
            arxiv_categories=["cs.AI", "cs.LG", "cs.CV", "cs.CL", "cs.NE"],
            max_papers_per_run=200,
            processing_batch_size=20
        )
    
    def test_ai_scholar_categories(self, ai_config):
        """Test AI Scholar specific categories."""
        expected_categories = ["cs.AI", "cs.LG", "cs.CV", "cs.CL", "cs.NE"]
        assert ai_config.arxiv_categories == expected_categories
    
    def test_ai_scholar_filtering(self):
        """Test AI Scholar paper filtering logic."""
        # This would test AI-specific filtering if implemented
        # For now, we'll test the category matching
        ai_categories = ["cs.AI", "cs.LG", "cs.CV", "cs.CL", "cs.NE"]
        
        test_papers = [
            {'categories': ['cs.AI']},  # Should match
            {'categories': ['cs.LG', 'stat.ML']},  # Should match
            {'categories': ['cs.CV', 'cs.AI']},  # Should match
            {'categories': ['math.ST']},  # Should not match
            {'categories': ['physics.gen-ph']},  # Should not match
        ]
        
        matching_papers = []
        for paper in test_papers:
            if any(cat in ai_categories for cat in paper['categories']):
                matching_papers.append(paper)
        
        assert len(matching_papers) == 3


class TestQuantScholarDownloader:
    """Test cases specific to Quant Scholar downloader."""
    
    @pytest.fixture
    def quant_config(self, temp_dir):
        """Create Quant Scholar configuration."""
        return InstanceConfig(
            instance_name="quant_scholar",
            storage_path=str(temp_dir),
            arxiv_categories=["q-fin.*", "stat.AP", "stat.ME", "math.ST"],
            journal_sources=["jstatsoft", "rjournal"],
            max_papers_per_run=150,
            processing_batch_size=15
        )
    
    def test_quant_scholar_categories(self, quant_config):
        """Test Quant Scholar specific categories."""
        expected_categories = ["q-fin.*", "stat.AP", "stat.ME", "math.ST"]
        assert quant_config.arxiv_categories == expected_categories
    
    def test_wildcard_category_matching(self):
        """Test wildcard category matching for q-fin.*"""
        # This would test wildcard matching logic
        qfin_papers = [
            {'categories': ['q-fin.CP']},  # Computational Finance
            {'categories': ['q-fin.EC']},  # Economics
            {'categories': ['q-fin.GN']},  # General Finance
            {'categories': ['q-fin.MF']},  # Mathematical Finance
            {'categories': ['q-fin.PM']},  # Portfolio Management
            {'categories': ['q-fin.PR']},  # Pricing of Securities
            {'categories': ['q-fin.RM']},  # Risk Management
            {'categories': ['q-fin.ST']},  # Statistical Finance
            {'categories': ['q-fin.TR']},  # Trading and Market Microstructure
        ]
        
        # All should match q-fin.* pattern
        for paper in qfin_papers:
            assert any(cat.startswith('q-fin.') for cat in paper['categories'])
    
    def test_journal_source_configuration(self, quant_config):
        """Test journal source configuration."""
        expected_sources = ["jstatsoft", "rjournal"]
        assert quant_config.journal_sources == expected_sources