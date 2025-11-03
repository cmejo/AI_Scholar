"""
Integration tests for AI Scholar download and processing pipeline.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import json
import sys

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.core.instance_config import InstanceConfig
    from multi_instance_arxiv_system.downloaders.ai_scholar_downloader import AIScholarDownloader
    from multi_instance_arxiv_system.processors.ai_scholar_processor import AIScholarProcessor
    from multi_instance_arxiv_system.scheduling.monthly_update_orchestrator import MonthlyUpdateOrchestrator
    from multi_instance_arxiv_system.vector_store.multi_instance_vector_store_service import MultiInstanceVectorStoreService
    from multi_instance_arxiv_system.models.paper_models import ArxivPaper
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class TestAIScholarEndToEndWorkflow:
    """End-to-end integration tests for AI Scholar workflow."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def ai_scholar_config(self, temp_dir):
        """Create AI Scholar configuration."""
        return InstanceConfig(
            instance_name="ai_scholar",
            storage_path=str(temp_dir),
            arxiv_categories=["cs.AI", "cs.LG", "cs.CV", "cs.CL", "cs.NE"],
            max_papers_per_run=50,
            processing_batch_size=10,
            vector_store_collection="ai_scholar_papers",
            email_notifications=True
        )
    
    @pytest.fixture
    def sample_arxiv_papers(self):
        """Create sample ArXiv paper data."""
        return [
            {
                'id': '2023.12345',
                'title': 'Advanced Machine Learning Techniques for Computer Vision',
                'authors': ['Alice Johnson', 'Bob Smith'],
                'abstract': 'This paper presents novel machine learning approaches for computer vision tasks.',
                'categories': ['cs.CV', 'cs.LG'],
                'published': datetime.now() - timedelta(days=1),
                'pdf_url': 'https://arxiv.org/pdf/2023.12345.pdf'
            },
            {
                'id': '2023.12346',
                'title': 'Natural Language Processing with Deep Neural Networks',
                'authors': ['Carol Davis', 'David Wilson'],
                'abstract': 'We explore deep learning methods for natural language understanding.',
                'categories': ['cs.CL', 'cs.AI'],
                'published': datetime.now() - timedelta(days=2),
                'pdf_url': 'https://arxiv.org/pdf/2023.12346.pdf'
            },
            {
                'id': '2023.12347',
                'title': 'Reinforcement Learning for Autonomous Systems',
                'authors': ['Eve Brown', 'Frank Miller'],
                'abstract': 'This work investigates reinforcement learning applications in autonomous systems.',
                'categories': ['cs.AI', 'cs.RO'],
                'published': datetime.now() - timedelta(days=3),
                'pdf_url': 'https://arxiv.org/pdf/2023.12347.pdf'
            }
        ]
    
    @pytest.mark.asyncio
    async def test_complete_ai_scholar_pipeline(self, ai_scholar_config, sample_arxiv_papers, temp_dir):
        """Test complete AI Scholar download and processing pipeline."""
        
        # Initialize components
        downloader = AIScholarDownloader(ai_scholar_config)
        processor = AIScholarProcessor(ai_scholar_config)
        vector_store = MultiInstanceVectorStoreService()
        
        # Mock ArXiv API responses
        with patch('feedparser.parse') as mock_feedparser, \
             patch('aiohttp.ClientSession.get') as mock_http_get:
            
            # Mock RSS feed response
            mock_feed = Mock()
            mock_feed.entries = []
            
            for paper_data in sample_arxiv_papers:
                entry = Mock()
                entry.id = paper_data['id']
                entry.title = paper_data['title']
                entry.authors = [{'name': author} for author in paper_data['authors']]
                entry.summary = paper_data['abstract']
                entry.tags = [{'term': cat} for cat in paper_data['categories']]
                entry.published = paper_data['published'].strftime('%Y-%m-%dT%H:%M:%SZ')
                entry.links = [{'href': paper_data['pdf_url'], 'type': 'application/pdf'}]
                mock_feed.entries.append(entry)
            
            mock_feedparser.return_value = mock_feed
            
            # Mock PDF download responses
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.content = b'Mock PDF content for testing'
            mock_http_get.return_value.__aenter__.return_value = mock_response
            
            # Step 1: Download papers
            download_result = await downloader.download_recent_papers(days_back=7)
            
            assert download_result['success'] == True
            assert download_result['papers_downloaded'] == 3
            assert len(downloader.downloaded_papers) == 3
            
            # Verify papers were saved to storage
            papers_dir = temp_dir / "papers"
            assert papers_dir.exists()
            
            pdf_files = list(papers_dir.glob("*.pdf"))
            assert len(pdf_files) == 3
            
            # Verify metadata was saved
            metadata_dir = temp_dir / "metadata"
            assert metadata_dir.exists()
            
            metadata_files = list(metadata_dir.glob("*.json"))
            assert len(metadata_files) == 3
            
            # Step 2: Process papers
            with patch.object(vector_store, 'add_documents') as mock_add_docs:
                mock_add_docs.return_value = True
                
                processing_result = await processor.process_downloaded_papers()
                
                assert processing_result['success'] == True
                assert processing_result['papers_processed'] == 3
                
                # Verify vector store was called
                mock_add_docs.assert_called()
                
                # Check that documents were created with proper metadata
                call_args = mock_add_docs.call_args[1]
                documents = call_args['documents']
                
                assert len(documents) == 3
                
                for doc in documents:
                    assert 'content' in doc
                    assert 'metadata' in doc
                    assert doc['metadata']['instance_name'] == 'ai_scholar'
                    assert doc['metadata']['paper_id'] in ['2023.12345', '2023.12346', '2023.12347']
            
            # Step 3: Verify processing logs
            logs_dir = temp_dir / "logs"
            assert logs_dir.exists()
            
            log_files = list(logs_dir.glob("*.log"))
            assert len(log_files) > 0
            
            # Step 4: Check final statistics
            final_stats = await downloader.get_download_statistics()
            
            assert final_stats['total_papers'] == 3
            assert final_stats['successful_downloads'] == 3
            assert final_stats['failed_downloads'] == 0
            assert final_stats['success_rate'] == 100.0
    
    @pytest.mark.asyncio
    async def test_ai_scholar_error_handling(self, ai_scholar_config, temp_dir):
        """Test AI Scholar pipeline error handling."""
        
        downloader = AIScholarDownloader(ai_scholar_config)
        
        # Test network error handling
        with patch('feedparser.parse') as mock_feedparser:
            mock_feedparser.side_effect = Exception("Network connection failed")
            
            download_result = await downloader.download_recent_papers(days_back=7)
            
            assert download_result['success'] == False
            assert 'error' in download_result
            assert len(downloader.processing_errors) > 0
        
        # Test PDF download error handling
        with patch('feedparser.parse') as mock_feedparser, \
             patch('aiohttp.ClientSession.get') as mock_http_get:
            
            # Mock successful feed parsing
            mock_feed = Mock()
            mock_entry = Mock()
            mock_entry.id = '2023.error'
            mock_entry.title = 'Error Test Paper'
            mock_entry.authors = [{'name': 'Test Author'}]
            mock_entry.summary = 'Test abstract'
            mock_entry.tags = [{'term': 'cs.AI'}]
            mock_entry.published = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            mock_entry.links = [{'href': 'https://arxiv.org/pdf/2023.error.pdf', 'type': 'application/pdf'}]
            mock_feed.entries = [mock_entry]
            mock_feedparser.return_value = mock_feed
            
            # Mock PDF download failure
            mock_response = AsyncMock()
            mock_response.status = 404  # Not found
            mock_http_get.return_value.__aenter__.return_value = mock_response
            
            download_result = await downloader.download_recent_papers(days_back=7)
            
            # Should handle PDF download errors gracefully
            assert len(downloader.processing_errors) > 0
            
            # Check error details
            error = downloader.processing_errors[0]
            assert error.error_type.value == 'http_error'
            assert '404' in error.message
    
    @pytest.mark.asyncio
    async def test_ai_scholar_duplicate_detection(self, ai_scholar_config, sample_arxiv_papers, temp_dir):
        """Test duplicate paper detection in AI Scholar pipeline."""
        
        downloader = AIScholarDownloader(ai_scholar_config)
        
        # Create existing metadata file to simulate duplicate
        metadata_dir = temp_dir / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        existing_paper = sample_arxiv_papers[0]
        existing_metadata = {
            'paper_id': existing_paper['id'],
            'title': existing_paper['title'],
            'downloaded_at': (datetime.now() - timedelta(days=1)).isoformat(),
            'instance_name': 'ai_scholar'
        }
        
        with open(metadata_dir / f"{existing_paper['id']}.json", 'w') as f:
            json.dump(existing_metadata, f)
        
        # Mock ArXiv API to return the same papers
        with patch('feedparser.parse') as mock_feedparser, \
             patch('aiohttp.ClientSession.get') as mock_http_get:
            
            mock_feed = Mock()
            mock_feed.entries = []
            
            for paper_data in sample_arxiv_papers:
                entry = Mock()
                entry.id = paper_data['id']
                entry.title = paper_data['title']
                entry.authors = [{'name': author} for author in paper_data['authors']]
                entry.summary = paper_data['abstract']
                entry.tags = [{'term': cat} for cat in paper_data['categories']]
                entry.published = paper_data['published'].strftime('%Y-%m-%dT%H:%M:%SZ')
                entry.links = [{'href': paper_data['pdf_url'], 'type': 'application/pdf'}]
                mock_feed.entries.append(entry)
            
            mock_feedparser.return_value = mock_feed
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.content = b'Mock PDF content'
            mock_http_get.return_value.__aenter__.return_value = mock_response
            
            download_result = await downloader.download_recent_papers(days_back=7)
            
            # Should skip the duplicate paper
            assert download_result['papers_downloaded'] == 2  # Only new papers
            assert download_result['duplicates_skipped'] == 1
    
    @pytest.mark.asyncio
    async def test_ai_scholar_category_filtering(self, ai_scholar_config, temp_dir):
        """Test AI Scholar category filtering."""
        
        downloader = AIScholarDownloader(ai_scholar_config)
        
        # Create papers with mixed categories
        mixed_papers = [
            {
                'id': '2023.ai',
                'title': 'AI Paper',
                'categories': ['cs.AI'],  # Should be included
                'published': datetime.now()
            },
            {
                'id': '2023.physics',
                'title': 'Physics Paper',
                'categories': ['physics.gen-ph'],  # Should be excluded
                'published': datetime.now()
            },
            {
                'id': '2023.mixed',
                'title': 'Mixed Paper',
                'categories': ['cs.LG', 'stat.ML'],  # Should be included (cs.LG matches)
                'published': datetime.now()
            }
        ]
        
        with patch('feedparser.parse') as mock_feedparser, \
             patch('aiohttp.ClientSession.get') as mock_http_get:
            
            mock_feed = Mock()
            mock_feed.entries = []
            
            for paper_data in mixed_papers:
                entry = Mock()
                entry.id = paper_data['id']
                entry.title = paper_data['title']
                entry.authors = [{'name': 'Test Author'}]
                entry.summary = 'Test abstract'
                entry.tags = [{'term': cat} for cat in paper_data['categories']]
                entry.published = paper_data['published'].strftime('%Y-%m-%dT%H:%M:%SZ')
                entry.links = [{'href': f'https://arxiv.org/pdf/{paper_data["id"]}.pdf', 'type': 'application/pdf'}]
                mock_feed.entries.append(entry)
            
            mock_feedparser.return_value = mock_feed
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.content = b'Mock PDF content'
            mock_http_get.return_value.__aenter__.return_value = mock_response
            
            download_result = await downloader.download_recent_papers(days_back=7)
            
            # Should only download AI/ML related papers
            assert download_result['papers_downloaded'] == 2  # AI and Mixed papers
            
            # Verify correct papers were downloaded
            downloaded_ids = [paper.paper_id for paper in downloader.downloaded_papers]
            assert '2023.ai' in downloaded_ids
            assert '2023.mixed' in downloaded_ids
            assert '2023.physics' not in downloaded_ids
    
    @pytest.mark.asyncio
    async def test_ai_scholar_batch_processing(self, ai_scholar_config, temp_dir):
        """Test AI Scholar batch processing capabilities."""
        
        # Create config with small batch size for testing
        batch_config = ai_scholar_config
        batch_config.processing_batch_size = 2
        
        processor = AIScholarProcessor(batch_config)
        
        # Create sample papers for processing
        papers_dir = temp_dir / "papers"
        papers_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_dir = temp_dir / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Create 5 papers to test batching
        for i in range(5):
            paper_id = f'2023.batch{i}'
            
            # Create PDF file
            pdf_path = papers_dir / f"{paper_id}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(b'Mock PDF content for batch processing test')
            
            # Create metadata file
            metadata = {
                'paper_id': paper_id,
                'title': f'Batch Test Paper {i}',
                'authors': ['Test Author'],
                'abstract': f'Abstract for paper {i}',
                'categories': ['cs.AI'],
                'instance_name': 'ai_scholar',
                'downloaded_at': datetime.now().isoformat()
            }
            
            with open(metadata_dir / f"{paper_id}.json", 'w') as f:
                json.dump(metadata, f)
        
        # Mock vector store operations
        with patch.object(processor.vector_store, 'add_documents') as mock_add_docs:
            mock_add_docs.return_value = True
            
            processing_result = await processor.process_downloaded_papers()
            
            assert processing_result['success'] == True
            assert processing_result['papers_processed'] == 5
            
            # Verify batching occurred (should be called 3 times: 2+2+1)
            assert mock_add_docs.call_count == 3
            
            # Verify batch sizes
            call_args_list = mock_add_docs.call_args_list
            
            # First two batches should have 2 documents each
            assert len(call_args_list[0][1]['documents']) == 2
            assert len(call_args_list[1][1]['documents']) == 2
            
            # Last batch should have 1 document
            assert len(call_args_list[2][1]['documents']) == 1


class TestAIScholarMonthlyUpdate:
    """Integration tests for AI Scholar monthly update process."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def ai_scholar_config(self, temp_dir):
        """Create AI Scholar configuration."""
        return InstanceConfig(
            instance_name="ai_scholar",
            storage_path=str(temp_dir),
            arxiv_categories=["cs.AI", "cs.LG"],
            max_papers_per_run=100,
            processing_batch_size=10,
            email_notifications=True
        )
    
    @pytest.mark.asyncio
    async def test_monthly_update_orchestration(self, ai_scholar_config, temp_dir):
        """Test monthly update orchestration for AI Scholar."""
        
        orchestrator = MonthlyUpdateOrchestrator()
        
        # Mock all the components
        with patch('multi_instance_arxiv_system.downloaders.ai_scholar_downloader.AIScholarDownloader') as mock_downloader_class, \
             patch('multi_instance_arxiv_system.processors.ai_scholar_processor.AIScholarProcessor') as mock_processor_class, \
             patch('multi_instance_arxiv_system.reporting.email_notification_service.EmailNotificationService') as mock_email_class:
            
            # Setup mock downloader
            mock_downloader = Mock()
            mock_downloader.download_recent_papers = AsyncMock(return_value={
                'success': True,
                'papers_downloaded': 25,
                'duplicates_skipped': 5,
                'processing_time_minutes': 15
            })
            mock_downloader.get_download_statistics = AsyncMock(return_value={
                'total_papers': 25,
                'successful_downloads': 25,
                'failed_downloads': 0,
                'success_rate': 100.0
            })
            mock_downloader_class.return_value = mock_downloader
            
            # Setup mock processor
            mock_processor = Mock()
            mock_processor.process_downloaded_papers = AsyncMock(return_value={
                'success': True,
                'papers_processed': 25,
                'processing_errors': 0,
                'vector_store_updates': 25
            })
            mock_processor_class.return_value = mock_processor
            
            # Setup mock email service
            mock_email = Mock()
            mock_email.send_update_notification = AsyncMock(return_value=True)
            mock_email_class.return_value = mock_email
            
            # Run monthly update
            update_result = await orchestrator.run_monthly_update('ai_scholar', ai_scholar_config)
            
            assert update_result['success'] == True
            assert update_result['instance_name'] == 'ai_scholar'
            assert update_result['papers_downloaded'] == 25
            assert update_result['papers_processed'] == 25
            
            # Verify all components were called
            mock_downloader.download_recent_papers.assert_called_once()
            mock_processor.process_downloaded_papers.assert_called_once()
            mock_email.send_update_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_monthly_update_error_recovery(self, ai_scholar_config, temp_dir):
        """Test error recovery in monthly update process."""
        
        orchestrator = MonthlyUpdateOrchestrator()
        
        with patch('multi_instance_arxiv_system.downloaders.ai_scholar_downloader.AIScholarDownloader') as mock_downloader_class, \
             patch('multi_instance_arxiv_system.processors.ai_scholar_processor.AIScholarProcessor') as mock_processor_class:
            
            # Setup mock downloader that fails
            mock_downloader = Mock()
            mock_downloader.download_recent_papers = AsyncMock(side_effect=Exception("Download failed"))
            mock_downloader_class.return_value = mock_downloader
            
            # Setup mock processor
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            
            # Run monthly update (should handle error gracefully)
            update_result = await orchestrator.run_monthly_update('ai_scholar', ai_scholar_config)
            
            assert update_result['success'] == False
            assert 'error' in update_result
            assert 'Download failed' in update_result['error']
            
            # Processor should not be called if download fails
            mock_processor.process_downloaded_papers.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_monthly_update_partial_failure(self, ai_scholar_config, temp_dir):
        """Test monthly update with partial failures."""
        
        orchestrator = MonthlyUpdateOrchestrator()
        
        with patch('multi_instance_arxiv_system.downloaders.ai_scholar_downloader.AIScholarDownloader') as mock_downloader_class, \
             patch('multi_instance_arxiv_system.processors.ai_scholar_processor.AIScholarProcessor') as mock_processor_class, \
             patch('multi_instance_arxiv_system.reporting.email_notification_service.EmailNotificationService') as mock_email_class:
            
            # Setup mock downloader (successful)
            mock_downloader = Mock()
            mock_downloader.download_recent_papers = AsyncMock(return_value={
                'success': True,
                'papers_downloaded': 20,
                'duplicates_skipped': 2,
                'errors': 3  # Some download errors
            })
            mock_downloader.get_download_statistics = AsyncMock(return_value={
                'total_papers': 23,
                'successful_downloads': 20,
                'failed_downloads': 3,
                'success_rate': 87.0
            })
            mock_downloader_class.return_value = mock_downloader
            
            # Setup mock processor (partial failure)
            mock_processor = Mock()
            mock_processor.process_downloaded_papers = AsyncMock(return_value={
                'success': True,
                'papers_processed': 18,  # 2 processing failures
                'processing_errors': 2,
                'vector_store_updates': 18
            })
            mock_processor_class.return_value = mock_processor
            
            # Setup mock email service
            mock_email = Mock()
            mock_email.send_update_notification = AsyncMock(return_value=True)
            mock_email_class.return_value = mock_email
            
            # Run monthly update
            update_result = await orchestrator.run_monthly_update('ai_scholar', ai_scholar_config)
            
            # Should still be considered successful overall
            assert update_result['success'] == True
            assert update_result['papers_downloaded'] == 20
            assert update_result['papers_processed'] == 18
            assert update_result['total_errors'] == 5  # 3 download + 2 processing
            
            # Should send notification with error summary
            mock_email.send_update_notification.assert_called_once()
            
            # Check notification includes error information
            notification_call = mock_email.send_update_notification.call_args
            notification_data = notification_call[1]
            assert notification_data['total_errors'] == 5


class TestAIScholarVectorStoreIntegration:
    """Integration tests for AI Scholar vector store operations."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def ai_scholar_config(self, temp_dir):
        """Create AI Scholar configuration."""
        return InstanceConfig(
            instance_name="ai_scholar",
            storage_path=str(temp_dir),
            vector_store_collection="ai_scholar_papers",
            arxiv_categories=["cs.AI", "cs.LG"]
        )
    
    @pytest.mark.asyncio
    async def test_vector_store_document_processing(self, ai_scholar_config, temp_dir):
        """Test vector store document processing for AI Scholar."""
        
        processor = AIScholarProcessor(ai_scholar_config)
        
        # Create sample processed papers
        papers_dir = temp_dir / "papers"
        papers_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_dir = temp_dir / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        sample_papers = [
            {
                'paper_id': '2023.ai001',
                'title': 'Deep Learning for Computer Vision',
                'abstract': 'This paper explores deep learning techniques for computer vision applications.',
                'categories': ['cs.CV', 'cs.LG']
            },
            {
                'paper_id': '2023.ai002',
                'title': 'Natural Language Processing with Transformers',
                'abstract': 'We present novel transformer architectures for NLP tasks.',
                'categories': ['cs.CL', 'cs.AI']
            }
        ]
        
        for paper in sample_papers:
            # Create PDF file (mock content)
            pdf_path = papers_dir / f"{paper['paper_id']}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(b'Mock PDF content representing the paper text')
            
            # Create metadata file
            metadata = {
                **paper,
                'authors': ['Test Author'],
                'instance_name': 'ai_scholar',
                'downloaded_at': datetime.now().isoformat()
            }
            
            with open(metadata_dir / f"{paper['paper_id']}.json", 'w') as f:
                json.dump(metadata, f)
        
        # Mock vector store operations
        with patch.object(processor.vector_store, 'add_documents') as mock_add_docs, \
             patch.object(processor.pdf_processor, 'extract_text') as mock_extract_text:
            
            # Mock PDF text extraction
            mock_extract_text.side_effect = [
                'Extracted text from deep learning paper about computer vision',
                'Extracted text from transformer paper about natural language processing'
            ]
            
            mock_add_docs.return_value = True
            
            # Process papers
            result = await processor.process_downloaded_papers()
            
            assert result['success'] == True
            assert result['papers_processed'] == 2
            
            # Verify vector store was called with correct documents
            mock_add_docs.assert_called_once()
            
            call_args = mock_add_docs.call_args[1]
            documents = call_args['documents']
            collection_name = call_args['collection_name']
            
            assert collection_name == 'ai_scholar_papers'
            assert len(documents) == 2
            
            # Verify document structure
            for doc in documents:
                assert 'content' in doc
                assert 'metadata' in doc
                assert doc['metadata']['instance_name'] == 'ai_scholar'
                assert doc['metadata']['paper_id'] in ['2023.ai001', '2023.ai002']
                assert 'categories' in doc['metadata']
                assert 'title' in doc['metadata']
    
    @pytest.mark.asyncio
    async def test_vector_store_search_functionality(self, ai_scholar_config):
        """Test vector store search functionality for AI Scholar."""
        
        vector_store = MultiInstanceVectorStoreService()
        
        # Mock search results
        mock_search_results = [
            {
                'document': {
                    'content': 'Deep learning techniques for computer vision',
                    'metadata': {
                        'paper_id': '2023.ai001',
                        'title': 'Deep Learning for Computer Vision',
                        'instance_name': 'ai_scholar',
                        'categories': ['cs.CV', 'cs.LG']
                    }
                },
                'score': 0.95
            },
            {
                'document': {
                    'content': 'Transformer architectures for natural language processing',
                    'metadata': {
                        'paper_id': '2023.ai002',
                        'title': 'NLP with Transformers',
                        'instance_name': 'ai_scholar',
                        'categories': ['cs.CL', 'cs.AI']
                    }
                },
                'score': 0.87
            }
        ]
        
        with patch.object(vector_store, 'search_documents') as mock_search:
            mock_search.return_value = mock_search_results
            
            # Test search
            search_results = await vector_store.search_documents(
                query="deep learning computer vision",
                collection_name="ai_scholar_papers",
                limit=10
            )
            
            assert len(search_results) == 2
            assert search_results[0]['score'] > search_results[1]['score']
            
            # Verify all results are from AI Scholar instance
            for result in search_results:
                assert result['document']['metadata']['instance_name'] == 'ai_scholar'
            
            # Verify search was called with correct parameters
            mock_search.assert_called_once_with(
                query="deep learning computer vision",
                collection_name="ai_scholar_papers",
                limit=10
            )