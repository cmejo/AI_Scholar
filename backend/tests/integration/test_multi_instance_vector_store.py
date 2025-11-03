"""
Integration tests for multi-instance vector store operations.
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
    from multi_instance_arxiv_system.vector_store.multi_instance_vector_store_service import MultiInstanceVectorStoreService
    from multi_instance_arxiv_system.core.instance_config import InstanceConfig
    from multi_instance_arxiv_system.models.paper_models import ArxivPaper, JournalPaper
    from multi_instance_arxiv_system.processors.ai_scholar_processor import AIScholarProcessor
    from multi_instance_arxiv_system.processors.quant_scholar_processor import QuantScholarProcessor
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class TestMultiInstanceVectorStoreIntegration:
    """Integration tests for multi-instance vector store operations."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def vector_store_service(self):
        """Create MultiInstanceVectorStoreService instance."""
        return MultiInstanceVectorStoreService()
    
    @pytest.fixture
    def ai_scholar_config(self, temp_dir):
        """Create AI Scholar configuration."""
        return InstanceConfig(
            instance_name="ai_scholar",
            storage_path=str(temp_dir / "ai_scholar"),
            vector_store_collection="ai_scholar_papers",
            arxiv_categories=["cs.AI", "cs.LG", "cs.CV"]
        )
    
    @pytest.fixture
    def quant_scholar_config(self, temp_dir):
        """Create Quant Scholar configuration."""
        return InstanceConfig(
            instance_name="quant_scholar",
            storage_path=str(temp_dir / "quant_scholar"),
            vector_store_collection="quant_scholar_papers",
            arxiv_categories=["q-fin.*", "stat.AP"]
        )
    
    @pytest.fixture
    def sample_ai_documents(self):
        """Create sample AI Scholar documents."""
        return [
            {
                'content': 'This paper presents a novel deep learning architecture for computer vision tasks. The proposed method achieves state-of-the-art results on ImageNet classification.',
                'metadata': {
                    'paper_id': 'ai_2023_001',
                    'title': 'Novel Deep Learning Architecture for Computer Vision',
                    'authors': ['Alice AI', 'Bob Vision'],
                    'categories': ['cs.CV', 'cs.LG'],
                    'instance_name': 'ai_scholar',
                    'source_type': 'arxiv',
                    'published_date': '2023-05-15',
                    'abstract': 'Novel deep learning approach for computer vision applications.'
                }
            },
            {
                'content': 'We introduce a new natural language processing model based on transformer architecture. Our approach shows significant improvements in language understanding tasks.',
                'metadata': {
                    'paper_id': 'ai_2023_002',
                    'title': 'Advanced NLP with Transformers',
                    'authors': ['Carol NLP', 'David Language'],
                    'categories': ['cs.CL', 'cs.AI'],
                    'instance_name': 'ai_scholar',
                    'source_type': 'arxiv',
                    'published_date': '2023-05-16',
                    'abstract': 'Advanced natural language processing using transformer models.'
                }
            }
        ]
    
    @pytest.fixture
    def sample_quant_documents(self):
        """Create sample Quant Scholar documents."""
        return [
            {
                'content': 'This paper analyzes portfolio optimization strategies using machine learning techniques. We demonstrate improved risk-adjusted returns through our methodology.',
                'metadata': {
                    'paper_id': 'quant_2023_001',
                    'title': 'ML-Based Portfolio Optimization',
                    'authors': ['Eve Finance', 'Frank Quant'],
                    'categories': ['q-fin.PM', 'stat.ML'],
                    'instance_name': 'quant_scholar',
                    'source_type': 'arxiv',
                    'published_date': '2023-05-15',
                    'abstract': 'Machine learning approaches to portfolio optimization.'
                }
            },
            {
                'content': 'We present statistical methods for risk management in financial markets. Our R package implements advanced econometric models for risk assessment.',
                'metadata': {
                    'paper_id': 'quant_2023_002',
                    'title': 'Statistical Risk Management Methods',
                    'authors': ['Grace Stats', 'Henry Risk'],
                    'journal_name': 'Journal of Statistical Software',
                    'volume': '95',
                    'issue': '3',
                    'instance_name': 'quant_scholar',
                    'source_type': 'journal',
                    'published_date': '2023-05-17',
                    'abstract': 'Statistical methods for financial risk management.'
                }
            }
        ]
    
    @pytest.mark.asyncio
    async def test_instance_separation_in_vector_store(self, vector_store_service, sample_ai_documents, sample_quant_documents):
        """Test that instances are properly separated in vector store."""
        
        # Mock ChromaDB client operations
        with patch.object(vector_store_service, 'chroma_client') as mock_client:
            
            # Mock collection operations
            mock_ai_collection = Mock()
            mock_quant_collection = Mock()
            
            mock_client.get_or_create_collection.side_effect = lambda name, **kwargs: {
                'ai_scholar_papers': mock_ai_collection,
                'quant_scholar_papers': mock_quant_collection
            }[name]
            
            # Add AI Scholar documents
            result_ai = await vector_store_service.add_documents(
                documents=sample_ai_documents,
                collection_name='ai_scholar_papers'
            )
            
            assert result_ai == True
            mock_ai_collection.add.assert_called_once()
            
            # Add Quant Scholar documents
            result_quant = await vector_store_service.add_documents(
                documents=sample_quant_documents,
                collection_name='quant_scholar_papers'
            )
            
            assert result_quant == True
            mock_quant_collection.add.assert_called_once()
            
            # Verify documents were added to separate collections
            ai_call_args = mock_ai_collection.add.call_args
            quant_call_args = mock_quant_collection.add.call_args
            
            # Check AI Scholar documents
            ai_ids = ai_call_args[1]['ids']
            ai_metadatas = ai_call_args[1]['metadatas']
            
            assert len(ai_ids) == 2
            assert all(meta['instance_name'] == 'ai_scholar' for meta in ai_metadatas)
            
            # Check Quant Scholar documents
            quant_ids = quant_call_args[1]['ids']
            quant_metadatas = quant_call_args[1]['metadatas']
            
            assert len(quant_ids) == 2
            assert all(meta['instance_name'] == 'quant_scholar' for meta in quant_metadatas)
    
    @pytest.mark.asyncio
    async def test_cross_instance_search_isolation(self, vector_store_service, sample_ai_documents, sample_quant_documents):
        """Test that searches are properly isolated between instances."""
        
        with patch.object(vector_store_service, 'chroma_client') as mock_client:
            
            # Mock collection operations
            mock_ai_collection = Mock()
            mock_quant_collection = Mock()
            
            mock_client.get_collection.side_effect = lambda name: {
                'ai_scholar_papers': mock_ai_collection,
                'quant_scholar_papers': mock_quant_collection
            }[name]
            
            # Mock search results for AI Scholar
            mock_ai_collection.query.return_value = {
                'ids': [['ai_2023_001']],
                'distances': [[0.15]],
                'metadatas': [[sample_ai_documents[0]['metadata']]],
                'documents': [[sample_ai_documents[0]['content']]]
            }
            
            # Mock search results for Quant Scholar
            mock_quant_collection.query.return_value = {
                'ids': [['quant_2023_001']],
                'distances': [[0.12]],
                'metadatas': [[sample_quant_documents[0]['metadata']]],
                'documents': [[sample_quant_documents[0]['content']]]
            }
            
            # Search AI Scholar collection
            ai_results = await vector_store_service.search_documents(
                query="deep learning computer vision",
                collection_name='ai_scholar_papers',
                limit=5
            )
            
            assert len(ai_results) == 1
            assert ai_results[0]['document']['metadata']['instance_name'] == 'ai_scholar'
            assert 'computer vision' in ai_results[0]['document']['content'].lower()
            
            # Search Quant Scholar collection
            quant_results = await vector_store_service.search_documents(
                query="portfolio optimization finance",
                collection_name='quant_scholar_papers',
                limit=5
            )
            
            assert len(quant_results) == 1
            assert quant_results[0]['document']['metadata']['instance_name'] == 'quant_scholar'
            assert 'portfolio optimization' in quant_results[0]['document']['content'].lower()
            
            # Verify separate collections were queried
            mock_ai_collection.query.assert_called_once()
            mock_quant_collection.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_unified_search_across_instances(self, vector_store_service, sample_ai_documents, sample_quant_documents):
        """Test unified search across multiple instances."""
        
        with patch.object(vector_store_service, 'chroma_client') as mock_client:
            
            # Mock collection operations
            mock_ai_collection = Mock()
            mock_quant_collection = Mock()
            
            mock_client.list_collections.return_value = [
                Mock(name='ai_scholar_papers'),
                Mock(name='quant_scholar_papers')
            ]
            
            mock_client.get_collection.side_effect = lambda name: {
                'ai_scholar_papers': mock_ai_collection,
                'quant_scholar_papers': mock_quant_collection
            }[name]
            
            # Mock search results
            mock_ai_collection.query.return_value = {
                'ids': [['ai_2023_001']],
                'distances': [[0.20]],
                'metadatas': [[sample_ai_documents[0]['metadata']]],
                'documents': [[sample_ai_documents[0]['content']]]
            }
            
            mock_quant_collection.query.return_value = {
                'ids': [['quant_2023_001']],
                'distances': [[0.15]],
                'metadatas': [[sample_quant_documents[0]['metadata']]],
                'documents': [[sample_quant_documents[0]['content']]]
            }
            
            # Perform unified search
            unified_results = await vector_store_service.search_all_instances(
                query="machine learning optimization",
                limit=10
            )
            
            assert len(unified_results) == 2
            
            # Results should be sorted by relevance (distance)
            assert unified_results[0]['score'] >= unified_results[1]['score']
            
            # Should contain results from both instances
            instance_names = [result['document']['metadata']['instance_name'] for result in unified_results]
            assert 'ai_scholar' in instance_names
            assert 'quant_scholar' in instance_names
            
            # Verify both collections were searched
            mock_ai_collection.query.assert_called_once()
            mock_quant_collection.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_instance_specific_metadata_schemas(self, vector_store_service):
        """Test instance-specific metadata schemas."""
        
        # AI Scholar document with ArXiv-specific metadata
        ai_doc = {
            'content': 'AI research content',
            'metadata': {
                'paper_id': 'ai_2023_001',
                'title': 'AI Paper',
                'authors': ['AI Author'],
                'categories': ['cs.AI'],
                'instance_name': 'ai_scholar',
                'source_type': 'arxiv',
                'arxiv_id': '2023.12345',
                'submission_date': '2023-05-15',
                'last_updated': '2023-05-16'
            }
        }
        
        # Quant Scholar document with journal-specific metadata
        quant_doc = {
            'content': 'Quantitative finance research content',
            'metadata': {
                'paper_id': 'quant_2023_001',
                'title': 'Quant Paper',
                'authors': ['Quant Author'],
                'instance_name': 'quant_scholar',
                'source_type': 'journal',
                'journal_name': 'Journal of Statistical Software',
                'volume': '95',
                'issue': '2',
                'doi': '10.18637/jss.v095.i02',
                'publication_year': '2023'
            }
        }
        
        with patch.object(vector_store_service, 'chroma_client') as mock_client:
            
            mock_ai_collection = Mock()
            mock_quant_collection = Mock()
            
            mock_client.get_or_create_collection.side_effect = lambda name, **kwargs: {
                'ai_scholar_papers': mock_ai_collection,
                'quant_scholar_papers': mock_quant_collection
            }[name]
            
            # Add documents with different metadata schemas
            await vector_store_service.add_documents([ai_doc], 'ai_scholar_papers')
            await vector_store_service.add_documents([quant_doc], 'quant_scholar_papers')
            
            # Verify AI Scholar metadata
            ai_call_args = mock_ai_collection.add.call_args[1]
            ai_metadata = ai_call_args['metadatas'][0]
            
            assert ai_metadata['source_type'] == 'arxiv'
            assert 'arxiv_id' in ai_metadata
            assert 'submission_date' in ai_metadata
            
            # Verify Quant Scholar metadata
            quant_call_args = mock_quant_collection.add.call_args[1]
            quant_metadata = quant_call_args['metadatas'][0]
            
            assert quant_metadata['source_type'] == 'journal'
            assert 'journal_name' in quant_metadata
            assert 'volume' in quant_metadata
            assert 'doi' in quant_metadata
    
    @pytest.mark.asyncio
    async def test_vector_store_collection_management(self, vector_store_service):
        """Test vector store collection management operations."""
        
        with patch.object(vector_store_service, 'chroma_client') as mock_client:
            
            # Mock collection operations
            mock_collection = Mock()
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_client.list_collections.return_value = [
                Mock(name='ai_scholar_papers'),
                Mock(name='quant_scholar_papers')
            ]
            
            # Test collection creation
            collection = await vector_store_service.get_or_create_collection('test_collection')
            assert collection == mock_collection
            mock_client.get_or_create_collection.assert_called_with(
                name='test_collection',
                embedding_function=vector_store_service.embedding_function
            )
            
            # Test listing collections
            collections = await vector_store_service.list_collections()
            assert len(collections) == 2
            assert 'ai_scholar_papers' in collections
            assert 'quant_scholar_papers' in collections
            
            # Test collection statistics
            mock_collection.count.return_value = 150
            stats = await vector_store_service.get_collection_stats('ai_scholar_papers')
            
            assert stats['collection_name'] == 'ai_scholar_papers'
            assert stats['document_count'] == 150
    
    @pytest.mark.asyncio
    async def test_document_update_and_deletion(self, vector_store_service):
        """Test document update and deletion operations."""
        
        with patch.object(vector_store_service, 'chroma_client') as mock_client:
            
            mock_collection = Mock()
            mock_client.get_collection.return_value = mock_collection
            
            # Test document update
            updated_doc = {
                'content': 'Updated content for the paper',
                'metadata': {
                    'paper_id': 'ai_2023_001',
                    'title': 'Updated AI Paper Title',
                    'instance_name': 'ai_scholar',
                    'last_updated': datetime.now().isoformat()
                }
            }
            
            result = await vector_store_service.update_document(
                document_id='ai_2023_001',
                updated_document=updated_doc,
                collection_name='ai_scholar_papers'
            )
            
            assert result == True
            mock_collection.update.assert_called_once()
            
            # Test document deletion
            delete_result = await vector_store_service.delete_document(
                document_id='ai_2023_001',
                collection_name='ai_scholar_papers'
            )
            
            assert delete_result == True
            mock_collection.delete.assert_called_once_with(ids=['ai_2023_001'])
    
    @pytest.mark.asyncio
    async def test_batch_operations(self, vector_store_service, sample_ai_documents):
        """Test batch operations for large document sets."""
        
        # Create large document set
        large_document_set = []
        for i in range(100):
            doc = {
                'content': f'This is document {i} content with various AI and ML topics.',
                'metadata': {
                    'paper_id': f'ai_2023_{i:03d}',
                    'title': f'AI Paper {i}',
                    'authors': [f'Author {i}'],
                    'instance_name': 'ai_scholar',
                    'batch_id': f'batch_{i // 10}'
                }
            }
            large_document_set.append(doc)
        
        with patch.object(vector_store_service, 'chroma_client') as mock_client:
            
            mock_collection = Mock()
            mock_client.get_or_create_collection.return_value = mock_collection
            
            # Test batch addition with automatic batching
            result = await vector_store_service.add_documents_batch(
                documents=large_document_set,
                collection_name='ai_scholar_papers',
                batch_size=25
            )
            
            assert result == True
            
            # Should be called 4 times (100 docs / 25 batch size)
            assert mock_collection.add.call_count == 4
            
            # Verify batch sizes
            call_args_list = mock_collection.add.call_args_list
            for i, call_args in enumerate(call_args_list):
                batch_size = len(call_args[1]['ids'])
                assert batch_size == 25  # All batches should be size 25
    
    @pytest.mark.asyncio
    async def test_vector_store_backup_and_recovery(self, vector_store_service):
        """Test vector store backup and recovery operations."""
        
        with patch.object(vector_store_service, 'chroma_client') as mock_client:
            
            mock_collection = Mock()
            mock_client.get_collection.return_value = mock_collection
            
            # Mock collection data for backup
            mock_collection.get.return_value = {
                'ids': ['doc1', 'doc2'],
                'documents': ['Content 1', 'Content 2'],
                'metadatas': [
                    {'paper_id': 'doc1', 'instance_name': 'ai_scholar'},
                    {'paper_id': 'doc2', 'instance_name': 'ai_scholar'}
                ]
            }
            
            # Test backup creation
            backup_data = await vector_store_service.create_collection_backup('ai_scholar_papers')
            
            assert 'collection_name' in backup_data
            assert 'documents' in backup_data
            assert 'timestamp' in backup_data
            assert len(backup_data['documents']) == 2
            
            # Test backup restoration
            restore_result = await vector_store_service.restore_collection_from_backup(
                backup_data, 'ai_scholar_papers_restored'
            )
            
            assert restore_result == True
            mock_client.get_or_create_collection.assert_called_with(
                name='ai_scholar_papers_restored',
                embedding_function=vector_store_service.embedding_function
            )


class TestProcessorVectorStoreIntegration:
    """Integration tests for processor and vector store interaction."""
    
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
            storage_path=str(temp_dir / "ai_scholar"),
            vector_store_collection="ai_scholar_papers",
            processing_batch_size=5
        )
    
    @pytest.mark.asyncio
    async def test_ai_scholar_processor_vector_store_integration(self, ai_scholar_config, temp_dir):
        """Test AI Scholar processor integration with vector store."""
        
        processor = AIScholarProcessor(ai_scholar_config)
        
        # Create sample papers in storage
        papers_dir = temp_dir / "ai_scholar" / "papers"
        papers_dir.mkdir(parents=True)
        
        metadata_dir = temp_dir / "ai_scholar" / "metadata"
        metadata_dir.mkdir(parents=True)
        
        # Create sample papers
        for i in range(3):
            paper_id = f'ai_2023_{i:03d}'
            
            # Create PDF file
            pdf_path = papers_dir / f"{paper_id}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(b'Mock PDF content for AI paper')
            
            # Create metadata file
            metadata = {
                'paper_id': paper_id,
                'title': f'AI Paper {i}',
                'authors': [f'AI Author {i}'],
                'abstract': f'Abstract for AI paper {i}',
                'categories': ['cs.AI'],
                'instance_name': 'ai_scholar',
                'downloaded_at': datetime.now().isoformat()
            }
            
            with open(metadata_dir / f"{paper_id}.json", 'w') as f:
                json.dump(metadata, f)
        
        # Mock vector store and PDF processing
        with patch.object(processor.vector_store, 'add_documents') as mock_add_docs, \
             patch.object(processor.pdf_processor, 'extract_text') as mock_extract_text:
            
            # Mock PDF text extraction
            mock_extract_text.side_effect = [
                f'Extracted text from AI paper {i} about artificial intelligence and machine learning'
                for i in range(3)
            ]
            
            mock_add_docs.return_value = True
            
            # Process papers
            result = await processor.process_downloaded_papers()
            
            assert result['success'] == True
            assert result['papers_processed'] == 3
            
            # Verify vector store integration
            mock_add_docs.assert_called_once()
            
            call_args = mock_add_docs.call_args[1]
            documents = call_args['documents']
            collection_name = call_args['collection_name']
            
            assert collection_name == 'ai_scholar_papers'
            assert len(documents) == 3
            
            # Verify document structure
            for i, doc in enumerate(documents):
                assert 'content' in doc
                assert 'metadata' in doc
                assert doc['metadata']['instance_name'] == 'ai_scholar'
                assert doc['metadata']['paper_id'] == f'ai_2023_{i:03d}'
                assert 'artificial intelligence' in doc['content'].lower()
    
    @pytest.mark.asyncio
    async def test_quant_scholar_processor_vector_store_integration(self, temp_dir):
        """Test Quant Scholar processor integration with vector store."""
        
        quant_config = InstanceConfig(
            instance_name="quant_scholar",
            storage_path=str(temp_dir / "quant_scholar"),
            vector_store_collection="quant_scholar_papers",
            processing_batch_size=3
        )
        
        processor = QuantScholarProcessor(quant_config)
        
        # Create sample papers in storage (mixed ArXiv and journal)
        papers_dir = temp_dir / "quant_scholar" / "papers"
        papers_dir.mkdir(parents=True)
        
        metadata_dir = temp_dir / "quant_scholar" / "metadata"
        metadata_dir.mkdir(parents=True)
        
        # ArXiv paper
        arxiv_metadata = {
            'paper_id': 'quant_arxiv_001',
            'title': 'Portfolio Optimization with ML',
            'authors': ['Quant Author'],
            'abstract': 'Machine learning for portfolio optimization',
            'categories': ['q-fin.PM'],
            'source_type': 'arxiv',
            'instance_name': 'quant_scholar',
            'downloaded_at': datetime.now().isoformat()
        }
        
        with open(papers_dir / "quant_arxiv_001.pdf", 'wb') as f:
            f.write(b'ArXiv PDF content about portfolio optimization')
        
        with open(metadata_dir / "quant_arxiv_001.json", 'w') as f:
            json.dump(arxiv_metadata, f)
        
        # Journal paper
        journal_metadata = {
            'paper_id': 'jss_v095_i01',
            'title': 'Statistical Software for Finance',
            'authors': ['Stats Author'],
            'abstract': 'R package for financial analysis',
            'journal_name': 'Journal of Statistical Software',
            'volume': '95',
            'issue': '1',
            'source_type': 'journal',
            'instance_name': 'quant_scholar',
            'downloaded_at': datetime.now().isoformat()
        }
        
        with open(papers_dir / "jss_v095_i01.pdf", 'wb') as f:
            f.write(b'Journal PDF content about statistical software')
        
        with open(metadata_dir / "jss_v095_i01.json", 'w') as f:
            json.dump(journal_metadata, f)
        
        # Mock vector store and PDF processing
        with patch.object(processor.vector_store, 'add_documents') as mock_add_docs, \
             patch.object(processor.pdf_processor, 'extract_text') as mock_extract_text:
            
            # Mock PDF text extraction
            mock_extract_text.side_effect = [
                'Extracted text about portfolio optimization and machine learning in finance',
                'Extracted text about statistical software and R packages for financial analysis'
            ]
            
            mock_add_docs.return_value = True
            
            # Process papers
            result = await processor.process_downloaded_papers()
            
            assert result['success'] == True
            assert result['papers_processed'] == 2
            assert result['arxiv_papers_processed'] == 1
            assert result['journal_papers_processed'] == 1
            
            # Verify vector store integration
            mock_add_docs.assert_called_once()
            
            call_args = mock_add_docs.call_args[1]
            documents = call_args['documents']
            collection_name = call_args['collection_name']
            
            assert collection_name == 'quant_scholar_papers'
            assert len(documents) == 2
            
            # Verify mixed document types
            arxiv_docs = [doc for doc in documents if doc['metadata'].get('source_type') == 'arxiv']
            journal_docs = [doc for doc in documents if doc['metadata'].get('source_type') == 'journal']
            
            assert len(arxiv_docs) == 1
            assert len(journal_docs) == 1
            
            # Verify content and metadata
            for doc in documents:
                assert doc['metadata']['instance_name'] == 'quant_scholar'
                assert 'financial' in doc['content'].lower() or 'finance' in doc['content'].lower()
    
    @pytest.mark.asyncio
    async def test_concurrent_processing_vector_store_operations(self, temp_dir):
        """Test concurrent processing operations with vector store."""
        
        # Create configurations for both instances
        ai_config = InstanceConfig(
            instance_name="ai_scholar",
            storage_path=str(temp_dir / "ai_scholar"),
            vector_store_collection="ai_scholar_papers"
        )
        
        quant_config = InstanceConfig(
            instance_name="quant_scholar",
            storage_path=str(temp_dir / "quant_scholar"),
            vector_store_collection="quant_scholar_papers"
        )
        
        # Create processors
        ai_processor = AIScholarProcessor(ai_config)
        quant_processor = QuantScholarProcessor(quant_config)
        
        # Create sample data for both instances
        for config, processor_name in [(ai_config, 'ai'), (quant_config, 'quant')]:
            papers_dir = Path(config.storage_path) / "papers"
            papers_dir.mkdir(parents=True)
            
            metadata_dir = Path(config.storage_path) / "metadata"
            metadata_dir.mkdir(parents=True)
            
            # Create sample paper
            paper_id = f'{processor_name}_2023_001'
            
            with open(papers_dir / f"{paper_id}.pdf", 'wb') as f:
                f.write(f'PDF content for {processor_name} paper'.encode())
            
            metadata = {
                'paper_id': paper_id,
                'title': f'{processor_name.upper()} Paper',
                'authors': [f'{processor_name.upper()} Author'],
                'instance_name': config.instance_name,
                'downloaded_at': datetime.now().isoformat()
            }
            
            with open(metadata_dir / f"{paper_id}.json", 'w') as f:
                json.dump(metadata, f)
        
        # Mock vector store operations for both processors
        with patch.object(ai_processor.vector_store, 'add_documents') as mock_ai_add, \
             patch.object(quant_processor.vector_store, 'add_documents') as mock_quant_add, \
             patch.object(ai_processor.pdf_processor, 'extract_text') as mock_ai_extract, \
             patch.object(quant_processor.pdf_processor, 'extract_text') as mock_quant_extract:
            
            # Mock text extraction
            mock_ai_extract.return_value = 'AI paper content about artificial intelligence'
            mock_quant_extract.return_value = 'Quant paper content about quantitative finance'
            
            mock_ai_add.return_value = True
            mock_quant_add.return_value = True
            
            # Process both instances concurrently
            ai_task = asyncio.create_task(ai_processor.process_downloaded_papers())
            quant_task = asyncio.create_task(quant_processor.process_downloaded_papers())
            
            ai_result, quant_result = await asyncio.gather(ai_task, quant_task)
            
            # Verify both processed successfully
            assert ai_result['success'] == True
            assert quant_result['success'] == True
            
            # Verify separate vector store operations
            mock_ai_add.assert_called_once()
            mock_quant_add.assert_called_once()
            
            # Verify correct collections were used
            ai_call_args = mock_ai_add.call_args[1]
            quant_call_args = mock_quant_add.call_args[1]
            
            assert ai_call_args['collection_name'] == 'ai_scholar_papers'
            assert quant_call_args['collection_name'] == 'quant_scholar_papers'
            
            # Verify instance separation in metadata
            ai_docs = ai_call_args['documents']
            quant_docs = quant_call_args['documents']
            
            assert ai_docs[0]['metadata']['instance_name'] == 'ai_scholar'
            assert quant_docs[0]['metadata']['instance_name'] == 'quant_scholar'