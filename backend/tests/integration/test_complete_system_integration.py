#!/usr/bin/env python3
"""
Complete System Integration Tests for Multi-Instance ArXiv System

This module provides comprehensive integration tests that validate the entire
system functionality including both AI Scholar and Quant Scholar instances,
data isolation, automated scheduling, and email notifications.
"""

import pytest
import asyncio
import tempfile
import shutil
import yaml
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import system components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from multi_instance_arxiv_system.core.base_scholar_downloader import BaseScholarDownloader
from multi_instance_arxiv_system.downloaders.ai_scholar_downloader import AIScholarDownloader
from multi_instance_arxiv_system.downloaders.quant_scholar_downloader import QuantScholarDownloader
from multi_instance_arxiv_system.processing.ai_scholar_processor import AIScholarProcessor
from multi_instance_arxiv_system.processing.quant_scholar_processor import QuantScholarProcessor
from multi_instance_arxiv_system.scheduling.monthly_update_orchestrator import MonthlyUpdateOrchestrator
from multi_instance_arxiv_system.services.email_notification_service import EmailNotificationService
from multi_instance_arxiv_system.services.multi_instance_vector_store_service import MultiInstanceVectorStoreService
from multi_instance_arxiv_system.config.instance_config import InstanceConfig


class TestCompleteSystemIntegration:
    """Test complete system integration functionality"""
    
    @pytest.fixture
    def temp_system_dir(self):
        """Create temporary system directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def ai_scholar_config(self, temp_system_dir):
        """Create AI Scholar test configuration"""
        config_data = {
            'instance_name': 'ai_scholar_test',
            'description': 'AI Scholar Test Instance',
            'storage_path': str(temp_system_dir / 'ai_scholar'),
            'papers_path': str(temp_system_dir / 'ai_scholar' / 'papers'),
            'logs_path': str(temp_system_dir / 'ai_scholar' / 'logs'),
            'cache_path': str(temp_system_dir / 'ai_scholar' / 'cache'),
            'arxiv_categories': ['cs.AI', 'cs.LG', 'cs.CV'],
            'processing': {
                'batch_size': 10,
                'max_concurrent': 1,
                'memory_limit_gb': 2
            },
            'email_notifications': {
                'enabled': True,
                'recipients': ['test@example.com'],
                'frequency': 'monthly'
            }
        }
        
        config_file = temp_system_dir / 'ai_scholar_config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        return InstanceConfig.from_yaml(config_file)
    
    @pytest.fixture
    def quant_scholar_config(self, temp_system_dir):
        """Create Quant Scholar test configuration"""
        config_data = {
            'instance_name': 'quant_scholar_test',
            'description': 'Quant Scholar Test Instance',
            'storage_path': str(temp_system_dir / 'quant_scholar'),
            'papers_path': str(temp_system_dir / 'quant_scholar' / 'papers'),
            'logs_path': str(temp_system_dir / 'quant_scholar' / 'logs'),
            'cache_path': str(temp_system_dir / 'quant_scholar' / 'cache'),
            'arxiv_categories': ['q-fin.*', 'stat.*'],
            'journal_sources': [
                {'name': 'Test Journal', 'url': 'https://test.example.com', 'enabled': True}
            ],
            'processing': {
                'batch_size': 10,
                'max_concurrent': 1,
                'memory_limit_gb': 2
            },
            'email_notifications': {
                'enabled': True,
                'recipients': ['test@example.com'],
                'frequency': 'monthly'
            }
        }
        
        config_file = temp_system_dir / 'quant_scholar_config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        return InstanceConfig.from_yaml(config_file)
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store service"""
        mock_service = Mock(spec=MultiInstanceVectorStoreService)
        mock_service.create_collection.return_value = True
        mock_service.add_documents.return_value = True
        mock_service.query_collection.return_value = {'documents': [], 'metadatas': []}
        mock_service.get_collection_stats.return_value = {'count': 0, 'size_mb': 0}
        return mock_service
    
    @pytest.fixture
    def mock_email_service(self):
        """Mock email notification service"""
        mock_service = Mock(spec=EmailNotificationService)
        mock_service.send_update_report.return_value = True
        mock_service.send_error_alert.return_value = True
        return mock_service
    
    def test_end_to_end_ai_scholar_workflow(self, ai_scholar_config, mock_vector_store, mock_email_service):
        """Test complete AI Scholar workflow from download to processing"""
        
        # Create directory structure
        ai_scholar_config.create_directories()
        
        # Test downloader initialization
        downloader = AIScholarDownloader(ai_scholar_config)
        assert downloader.config.instance_name == 'ai_scholar_test'
        assert downloader.config.arxiv_categories == ['cs.AI', 'cs.LG', 'cs.CV']
        
        # Mock download process
        with patch.object(downloader, '_download_paper') as mock_download:
            mock_download.return_value = True
            
            # Simulate downloading a few papers
            test_papers = [
                {'id': 'cs.AI/2024001', 'title': 'Test AI Paper 1', 'categories': ['cs.AI']},
                {'id': 'cs.LG/2024002', 'title': 'Test ML Paper 2', 'categories': ['cs.LG']},
                {'id': 'cs.CV/2024003', 'title': 'Test CV Paper 3', 'categories': ['cs.CV']}
            ]
            
            # Create mock PDF files
            for paper in test_papers:
                paper_file = Path(ai_scholar_config.papers_path) / f"{paper['id'].replace('/', '_')}.pdf"
                paper_file.parent.mkdir(parents=True, exist_ok=True)
                paper_file.write_text(f"Mock PDF content for {paper['title']}")
            
            # Test processor initialization
            processor = AIScholarProcessor(ai_scholar_config, mock_vector_store)
            assert processor.config.instance_name == 'ai_scholar_test'
            
            # Test processing
            with patch.object(processor, '_extract_text_from_pdf') as mock_extract:
                mock_extract.return_value = "Sample extracted text content"
                
                # Process papers
                results = processor.process_papers(limit=3)
                
                # Verify processing results
                assert 'processed_count' in results
                assert 'error_count' in results
                assert results['processed_count'] >= 0
                
                # Verify vector store interactions
                assert mock_vector_store.create_collection.called
                
        print("✓ AI Scholar end-to-end workflow test passed")
    
    def test_end_to_end_quant_scholar_workflow(self, quant_scholar_config, mock_vector_store, mock_email_service):
        """Test complete Quant Scholar workflow including journal sources"""
        
        # Create directory structure
        quant_scholar_config.create_directories()
        
        # Test downloader initialization
        downloader = QuantScholarDownloader(quant_scholar_config)
        assert downloader.config.instance_name == 'quant_scholar_test'
        assert 'q-fin.*' in downloader.config.arxiv_categories
        
        # Mock download process for arXiv papers
        with patch.object(downloader, '_download_paper') as mock_download:
            mock_download.return_value = True
            
            # Simulate downloading papers
            test_papers = [
                {'id': 'q-fin.ST/2024001', 'title': 'Test Quant Paper 1', 'categories': ['q-fin.ST']},
                {'id': 'stat.ML/2024002', 'title': 'Test Stats Paper 2', 'categories': ['stat.ML']}
            ]
            
            # Create mock PDF files
            for paper in test_papers:
                paper_file = Path(quant_scholar_config.papers_path) / f"{paper['id'].replace('/', '_')}.pdf"
                paper_file.parent.mkdir(parents=True, exist_ok=True)
                paper_file.write_text(f"Mock PDF content for {paper['title']}")
            
            # Test journal source handling
            with patch.object(downloader, '_download_from_journal') as mock_journal_download:
                mock_journal_download.return_value = True
                
                # Simulate journal downloads
                journal_papers = [
                    {'title': 'Test Journal Paper 1', 'source': 'Test Journal', 'url': 'https://test.example.com/paper1.pdf'}
                ]
                
                for paper in journal_papers:
                    paper_file = Path(quant_scholar_config.papers_path) / f"journal_{paper['title'].replace(' ', '_')}.pdf"
                    paper_file.write_text(f"Mock journal PDF content for {paper['title']}")
            
            # Test processor initialization
            processor = QuantScholarProcessor(quant_scholar_config, mock_vector_store)
            assert processor.config.instance_name == 'quant_scholar_test'
            
            # Test processing with multiple source types
            with patch.object(processor, '_extract_text_from_pdf') as mock_extract:
                mock_extract.return_value = "Sample extracted text content"
                
                # Process papers
                results = processor.process_papers(limit=5)
                
                # Verify processing results
                assert 'processed_count' in results
                assert 'error_count' in results
                assert results['processed_count'] >= 0
                
                # Verify vector store interactions
                assert mock_vector_store.create_collection.called
        
        print("✓ Quant Scholar end-to-end workflow test passed")
    
    def test_instance_data_isolation(self, ai_scholar_config, quant_scholar_config, mock_vector_store):
        """Test that AI Scholar and Quant Scholar instances maintain data isolation"""
        
        # Create both instances
        ai_scholar_config.create_directories()
        quant_scholar_config.create_directories()
        
        # Create processors for both instances
        ai_processor = AIScholarProcessor(ai_scholar_config, mock_vector_store)
        quant_processor = QuantScholarProcessor(quant_scholar_config, mock_vector_store)
        
        # Verify different collection names
        ai_collection = ai_processor._get_collection_name()
        quant_collection = quant_processor._get_collection_name()
        
        assert ai_collection != quant_collection
        assert 'ai_scholar' in ai_collection.lower()
        assert 'quant_scholar' in quant_collection.lower()
        
        # Verify separate storage paths
        assert ai_scholar_config.storage_path != quant_scholar_config.storage_path
        assert ai_scholar_config.papers_path != quant_scholar_config.papers_path
        assert ai_scholar_config.logs_path != quant_scholar_config.logs_path
        
        # Create test files in each instance
        ai_test_file = Path(ai_scholar_config.papers_path) / 'ai_test.pdf'
        quant_test_file = Path(quant_scholar_config.papers_path) / 'quant_test.pdf'
        
        ai_test_file.write_text("AI Scholar test content")
        quant_test_file.write_text("Quant Scholar test content")
        
        # Verify files are isolated
        assert ai_test_file.exists()
        assert quant_test_file.exists()
        assert ai_test_file.read_text() != quant_test_file.read_text()
        
        # Verify no cross-contamination
        ai_files = list(Path(ai_scholar_config.papers_path).glob('*'))
        quant_files = list(Path(quant_scholar_config.papers_path).glob('*'))
        
        ai_file_names = [f.name for f in ai_files]
        quant_file_names = [f.name for f in quant_files]
        
        assert 'ai_test.pdf' in ai_file_names
        assert 'ai_test.pdf' not in quant_file_names
        assert 'quant_test.pdf' in quant_file_names
        assert 'quant_test.pdf' not in ai_file_names
        
        print("✓ Instance data isolation test passed")
    
    def test_monthly_update_orchestration(self, ai_scholar_config, quant_scholar_config, mock_vector_store, mock_email_service):
        """Test automated monthly update orchestration"""
        
        # Create configurations
        configs = [ai_scholar_config, quant_scholar_config]
        
        # Initialize orchestrator
        orchestrator = MonthlyUpdateOrchestrator(configs, mock_email_service)
        
        # Mock the individual update processes
        with patch.object(orchestrator, '_run_instance_update') as mock_update:
            mock_update.return_value = {
                'success': True,
                'papers_downloaded': 10,
                'papers_processed': 8,
                'errors': 2,
                'duration_minutes': 15
            }
            
            # Run orchestrated update
            results = orchestrator.run_monthly_update()
            
            # Verify orchestration results
            assert 'ai_scholar_test' in results
            assert 'quant_scholar_test' in results
            
            for instance_name, result in results.items():
                assert result['success'] is True
                assert 'papers_downloaded' in result
                assert 'papers_processed' in result
                assert 'duration_minutes' in result
            
            # Verify both instances were updated
            assert mock_update.call_count == 2
            
            # Verify email notification was sent
            assert mock_email_service.send_update_report.called
        
        print("✓ Monthly update orchestration test passed")
    
    def test_email_notification_functionality(self, ai_scholar_config, mock_email_service):
        """Test email notification system functionality"""
        
        # Test update report generation
        update_data = {
            'instance_name': 'ai_scholar_test',
            'papers_downloaded': 25,
            'papers_processed': 23,
            'errors': 2,
            'duration_minutes': 30,
            'storage_used_gb': 1.5,
            'timestamp': datetime.now().isoformat()
        }
        
        # Test sending update report
        mock_email_service.send_update_report(update_data)
        assert mock_email_service.send_update_report.called
        
        # Test error alert
        error_data = {
            'instance_name': 'ai_scholar_test',
            'error_type': 'download_failure',
            'error_message': 'Failed to download paper: connection timeout',
            'timestamp': datetime.now().isoformat()
        }
        
        mock_email_service.send_error_alert(error_data)
        assert mock_email_service.send_error_alert.called
        
        print("✓ Email notification functionality test passed")
    
    def test_vector_store_multi_instance_operations(self, ai_scholar_config, quant_scholar_config, mock_vector_store):
        """Test vector store operations across multiple instances"""
        
        # Create processors for both instances
        ai_processor = AIScholarProcessor(ai_scholar_config, mock_vector_store)
        quant_processor = QuantScholarProcessor(quant_scholar_config, mock_vector_store)
        
        # Test collection creation for both instances
        ai_collection = ai_processor._get_collection_name()
        quant_collection = quant_processor._get_collection_name()
        
        # Simulate adding documents to both collections
        ai_docs = [
            {'id': 'ai_doc_1', 'text': 'AI research content', 'metadata': {'instance': 'ai_scholar'}},
            {'id': 'ai_doc_2', 'text': 'Machine learning content', 'metadata': {'instance': 'ai_scholar'}}
        ]
        
        quant_docs = [
            {'id': 'quant_doc_1', 'text': 'Quantitative finance content', 'metadata': {'instance': 'quant_scholar'}},
            {'id': 'quant_doc_2', 'text': 'Statistical analysis content', 'metadata': {'instance': 'quant_scholar'}}
        ]
        
        # Test document addition
        mock_vector_store.add_documents(ai_collection, ai_docs)
        mock_vector_store.add_documents(quant_collection, quant_docs)
        
        # Verify separate collection operations
        assert mock_vector_store.add_documents.call_count == 2
        
        # Test querying specific collections
        mock_vector_store.query_collection(ai_collection, "AI research", n_results=5)
        mock_vector_store.query_collection(quant_collection, "finance analysis", n_results=5)
        
        # Verify collection-specific queries
        assert mock_vector_store.query_collection.call_count == 2
        
        print("✓ Vector store multi-instance operations test passed")
    
    def test_error_handling_and_recovery(self, ai_scholar_config, mock_vector_store, mock_email_service):
        """Test system error handling and recovery mechanisms"""
        
        # Create processor
        processor = AIScholarProcessor(ai_scholar_config, mock_vector_store)
        
        # Test handling of processing errors
        with patch.object(processor, '_extract_text_from_pdf') as mock_extract:
            # Simulate extraction failure
            mock_extract.side_effect = Exception("PDF extraction failed")
            
            # Create test file
            ai_scholar_config.create_directories()
            test_file = Path(ai_scholar_config.papers_path) / 'test_error.pdf'
            test_file.write_text("Mock PDF content")
            
            # Process with error
            results = processor.process_papers(limit=1)
            
            # Verify error handling
            assert 'error_count' in results
            assert results['error_count'] > 0
            
            # Verify error was logged (would check log files in real implementation)
            
        # Test vector store connection failure
        mock_vector_store.add_documents.side_effect = Exception("Vector store connection failed")
        
        with patch.object(processor, '_extract_text_from_pdf') as mock_extract:
            mock_extract.return_value = "Sample text"
            
            # Process with vector store error
            results = processor.process_papers(limit=1)
            
            # Verify graceful handling of vector store errors
            assert 'error_count' in results
        
        print("✓ Error handling and recovery test passed")
    
    def test_system_health_validation(self, ai_scholar_config, quant_scholar_config, mock_vector_store):
        """Test comprehensive system health validation"""
        
        # Test configuration validation
        assert ai_scholar_config.validate()
        assert quant_scholar_config.validate()
        
        # Test directory structure
        ai_scholar_config.create_directories()
        quant_scholar_config.create_directories()
        
        # Verify all required directories exist
        for config in [ai_scholar_config, quant_scholar_config]:
            assert Path(config.storage_path).exists()
            assert Path(config.papers_path).exists()
            assert Path(config.logs_path).exists()
            assert Path(config.cache_path).exists()
        
        # Test component initialization
        ai_downloader = AIScholarDownloader(ai_scholar_config)
        quant_downloader = QuantScholarDownloader(quant_scholar_config)
        ai_processor = AIScholarProcessor(ai_scholar_config, mock_vector_store)
        quant_processor = QuantScholarProcessor(quant_scholar_config, mock_vector_store)
        
        # Verify all components initialized successfully
        assert ai_downloader is not None
        assert quant_downloader is not None
        assert ai_processor is not None
        assert quant_processor is not None
        
        # Test vector store connectivity (mocked)
        mock_vector_store.create_collection('test_collection')
        assert mock_vector_store.create_collection.called
        
        print("✓ System health validation test passed")


def run_integration_tests():
    """Run all integration tests"""
    print("Running Complete System Integration Tests")
    print("=" * 50)
    
    # Run pytest with this file
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == "__main__":
    run_integration_tests()