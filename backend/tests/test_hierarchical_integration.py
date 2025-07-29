"""
Tests for hierarchical chunking integration with document processor and vector store
"""
import pytest
import asyncio
import tempfile
import os
import json
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base, Document, DocumentChunk, DocumentChunkEnhanced
from services.document_processor import DocumentProcessor
from services.vector_store import VectorStoreService
from services.hierarchical_chunking import ChunkingStrategy


class TestHierarchicalIntegration:
    """Test hierarchical chunking integration"""
    
    @pytest.fixture
    def setup_test_db(self):
        """Setup test database"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return TestSessionLocal
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        with patch('services.document_processor.settings') as mock_settings:
            mock_settings.UPLOAD_DIR = tempfile.mkdtemp()
            mock_settings.CHUNK_SIZE = 512
            mock_settings.CHUNK_OVERLAP = 50
            yield mock_settings
    
    @pytest.fixture
    def document_processor(self, mock_settings):
        """Create document processor instance"""
        return DocumentProcessor()
    
    @pytest.fixture
    def vector_store(self):
        """Create vector store instance"""
        with patch('services.vector_store.settings') as mock_settings:
            mock_settings.OLLAMA_URL = "http://localhost:11434"
            mock_settings.EMBEDDING_MODEL = "nomic-embed-text"
            mock_settings.CHROMA_PERSIST_DIR = tempfile.mkdtemp()
            
            store = VectorStoreService()
            # Mock the ChromaDB collection
            store.collection = Mock()
            store.collection.add = Mock()
            store.collection.query = Mock()
            store.collection.get = Mock()
            store.collection.count = Mock(return_value=0)
            
            return store
    
    @pytest.fixture
    def sample_text(self):
        """Sample text for testing"""
        return """
        Introduction to Machine Learning
        
        Machine learning is a subset of artificial intelligence that focuses on algorithms 
        that can learn from data. It has three main types: supervised learning, 
        unsupervised learning, and reinforcement learning.
        
        Supervised Learning
        
        Supervised learning uses labeled data to train models. Common algorithms include 
        linear regression, decision trees, and neural networks. The goal is to predict 
        outcomes for new, unseen data.
        
        Applications of supervised learning include image classification, spam detection, 
        and medical diagnosis. These applications require large datasets with known outcomes.
        
        Unsupervised Learning
        
        Unsupervised learning finds patterns in data without labeled examples. Clustering 
        and dimensionality reduction are common techniques. K-means clustering and 
        principal component analysis are popular algorithms.
        
        Reinforcement Learning
        
        Reinforcement learning learns through interaction with an environment. Agents 
        receive rewards or penalties for actions. This approach is used in game playing, 
        robotics, and autonomous systems.
        """
    
    @pytest.mark.asyncio
    async def test_hierarchical_chunking_integration(self, document_processor, setup_test_db, sample_text):
        """Test that document processor creates hierarchical chunks correctly"""
        
        # Mock database session
        with patch('services.document_processor.get_db') as mock_get_db:
            db_session = setup_test_db()
            mock_get_db.return_value = iter([db_session])
            
            # Create a temporary text file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(sample_text)
                temp_file_path = f.name
            
            try:
                # Process the text file
                result = await document_processor._process_text(
                    temp_file_path, 
                    "test_doc_id", 
                    db_session
                )
                
                # Verify results
                assert result['chunks_count'] > 0
                assert result['embeddings_count'] > 0
                assert 'hierarchical_levels' in result['details']
                assert result['details']['hierarchical_levels'] > 1
                
                # Check that enhanced chunks were created
                enhanced_chunks = db_session.query(DocumentChunkEnhanced).filter(
                    DocumentChunkEnhanced.document_id == "test_doc_id"
                ).all()
                
                assert len(enhanced_chunks) > 0
                
                # Verify hierarchical structure
                levels = set(chunk.chunk_level for chunk in enhanced_chunks)
                assert len(levels) > 1  # Should have multiple levels
                assert 0 in levels  # Should have base level
                
                # Check parent-child relationships
                parent_chunks = [chunk for chunk in enhanced_chunks if chunk.parent_chunk_id is not None]
                assert len(parent_chunks) > 0
                
                # Verify chunk metadata
                for chunk in enhanced_chunks:
                    assert chunk.content is not None
                    assert chunk.chunk_index is not None
                    assert chunk.chunk_level is not None
                    assert chunk.sentence_boundaries is not None
                    
                    # Parse sentence boundaries
                    boundaries = json.loads(chunk.sentence_boundaries) if chunk.sentence_boundaries else []
                    assert isinstance(boundaries, list)
                
            finally:
                os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_vector_store_hierarchical_integration(self, vector_store, setup_test_db):
        """Test vector store integration with hierarchical chunks"""
        
        # Create mock enhanced chunks
        mock_chunks = [
            Mock(
                id="chunk_1",
                document_id="test_doc",
                content="This is a test chunk at level 0",
                chunk_level=0,
                chunk_index=0,
                parent_chunk_id=None,
                overlap_start=None,
                overlap_end=None,
                sentence_boundaries='[0, 1]',
                chunk_metadata={'strategy': 'hierarchical'}
            ),
            Mock(
                id="chunk_2",
                document_id="test_doc",
                content="This is a parent chunk at level 1 containing multiple sentences",
                chunk_level=1,
                chunk_index=0,
                parent_chunk_id=None,
                overlap_start=None,
                overlap_end=50,
                sentence_boundaries='[0, 1, 2]',
                chunk_metadata={'strategy': 'hierarchical', 'child_chunks': ['chunk_1']}
            )
        ]
        
        # Mock embedding generation
        vector_store.generate_embedding = AsyncMock(return_value=[0.1] * 384)
        
        # Mock database query
        with patch('services.vector_store.get_db') as mock_get_db:
            db_session = Mock()
            db_session.query.return_value.filter.return_value.all.return_value = mock_chunks
            mock_get_db.return_value = iter([db_session])
            
            # Test adding hierarchical chunks
            document_data = {"id": "test_doc", "name": "test_document.txt"}
            await vector_store.add_document(document_data)
            
            # Verify that add was called with correct structure
            vector_store.collection.add.assert_called_once()
            call_args = vector_store.collection.add.call_args
            
            # Check IDs include level information
            ids = call_args[1]['ids']
            assert any('_L0_' in id for id in ids)
            assert any('_L1_' in id for id in ids)
            
            # Check metadata includes hierarchical information
            metadatas = call_args[1]['metadatas']
            for metadata in metadatas:
                assert 'chunk_type' in metadata
                assert metadata['chunk_type'] == 'hierarchical'
                assert 'chunk_level' in metadata
                assert 'has_overlap' in metadata
                assert 'sentence_count' in metadata
    
    @pytest.mark.asyncio
    async def test_hierarchical_search(self, vector_store):
        """Test hierarchical search functionality"""
        
        # Mock search results
        mock_search_results = {
            "ids": [["test_doc_L0_0", "test_doc_L1_0"]],
            "documents": [["Level 0 content", "Level 1 content"]],
            "metadatas": [[
                {
                    "document_id": "test_doc",
                    "chunk_level": 0,
                    "chunk_type": "hierarchical",
                    "has_overlap": False,
                    "content_length": 100
                },
                {
                    "document_id": "test_doc", 
                    "chunk_level": 1,
                    "chunk_type": "hierarchical",
                    "has_overlap": True,
                    "content_length": 200
                }
            ]],
            "distances": [[0.2, 0.3]]
        }
        
        vector_store.collection.query.return_value = mock_search_results
        vector_store.collection.get.return_value = {"ids": [], "documents": [], "metadatas": []}
        vector_store.generate_embedding = AsyncMock(return_value=[0.1] * 384)
        
        # Test hierarchical search
        results = await vector_store.hierarchical_search(
            query="test query",
            user_id="test_user",
            limit=5,
            include_context=True
        )
        
        # Verify results structure
        assert len(results) == 2
        for result in results:
            assert 'id' in result
            assert 'content' in result
            assert 'metadata' in result
            assert 'relevance' in result
            assert 'hierarchical_context' in result
            
            # Check hierarchical context
            context = result['hierarchical_context']
            assert 'level' in context
            assert 'has_overlap' in context
            assert 'related_chunks' in context
    
    @pytest.mark.asyncio
    async def test_chunk_hierarchy_retrieval(self, document_processor, setup_test_db):
        """Test chunk hierarchy retrieval methods"""
        
        with patch('services.document_processor.get_db') as mock_get_db:
            db_session = setup_test_db()
            mock_get_db.return_value = iter([db_session])
            
            # Create test document
            document = Document(
                id="test_doc",
                user_id="test_user",
                name="test.txt",
                file_path="/tmp/test.txt",
                content_type="text/plain",
                size=1000,
                status="completed"
            )
            db_session.add(document)
            
            # Create test enhanced chunks
            chunks = [
                DocumentChunkEnhanced(
                    id="chunk_1",
                    document_id="test_doc",
                    content="Level 0 chunk 1",
                    chunk_level=0,
                    chunk_index=0,
                    sentence_boundaries='[0, 1]',
                    chunk_metadata={'test': True}
                ),
                DocumentChunkEnhanced(
                    id="chunk_2", 
                    document_id="test_doc",
                    content="Level 0 chunk 2",
                    chunk_level=0,
                    chunk_index=1,
                    parent_chunk_id="chunk_3",
                    sentence_boundaries='[2, 3]',
                    chunk_metadata={'test': True}
                ),
                DocumentChunkEnhanced(
                    id="chunk_3",
                    document_id="test_doc", 
                    content="Level 1 parent chunk",
                    chunk_level=1,
                    chunk_index=0,
                    overlap_end=100,
                    sentence_boundaries='[0, 1, 2, 3]',
                    chunk_metadata={'child_chunks': ['chunk_1', 'chunk_2']}
                )
            ]
            
            for chunk in chunks:
                db_session.add(chunk)
            db_session.commit()
            
            # Test get_chunk_hierarchy
            hierarchy = await document_processor.get_chunk_hierarchy("test_doc", "test_user")
            
            assert hierarchy['document_id'] == "test_doc"
            assert 'levels' in hierarchy
            assert 0 in hierarchy['levels']
            assert 1 in hierarchy['levels']
            assert len(hierarchy['levels'][0]) == 2  # Two level 0 chunks
            assert len(hierarchy['levels'][1]) == 1  # One level 1 chunk
            
            # Test get_contextual_chunks
            contextual = await document_processor.get_contextual_chunks("chunk_2", "test_user")
            
            # Should include parent, target, and siblings
            chunk_relationships = [chunk['relationship'] for chunk in contextual]
            assert 'target' in chunk_relationships
            assert 'parent' in chunk_relationships
            assert 'sibling' in chunk_relationships
            
            # Test get_chunk_relationships
            relationships = await document_processor.get_chunk_relationships("chunk_2", "test_user")
            
            assert relationships['chunk_id'] == "chunk_2"
            assert relationships['chunk_level'] == 0
            assert relationships['parent_chunk_id'] == "chunk_3"
            assert 'overlap_info' in relationships
    
    @pytest.mark.asyncio
    async def test_backward_compatibility(self, document_processor, vector_store, setup_test_db):
        """Test that the system maintains backward compatibility with legacy chunks"""
        
        with patch('services.document_processor.get_db') as mock_get_db:
            db_session = setup_test_db()
            mock_get_db.return_value = iter([db_session])
            
            # Create legacy chunks (no enhanced chunks)
            legacy_chunks = [
                Mock(
                    id="legacy_1",
                    document_id="legacy_doc",
                    content="Legacy chunk content",
                    chunk_index=0,
                    page_number=1,
                    chunk_metadata=None
                )
            ]
            
            # Mock database queries to return legacy chunks only
            db_session.query.return_value.filter.return_value.all.side_effect = [
                [],  # No enhanced chunks
                legacy_chunks  # Legacy chunks
            ]
            
            vector_store.generate_embedding = AsyncMock(return_value=[0.1] * 384)
            
            # Test that vector store handles legacy chunks
            document_data = {"id": "legacy_doc", "name": "legacy.txt"}
            await vector_store.add_document(document_data)
            
            # Verify legacy chunks were processed
            vector_store.collection.add.assert_called_once()
            call_args = vector_store.collection.add.call_args
            
            metadatas = call_args[1]['metadatas']
            assert metadatas[0]['chunk_type'] == 'legacy'
    
    def test_chunking_strategy_integration(self, document_processor):
        """Test that different chunking strategies are properly integrated"""
        
        # Test that hierarchical chunker is initialized
        assert document_processor.hierarchical_chunker is not None
        
        # Test that chunking strategies are available
        strategies = [
            ChunkingStrategy.HIERARCHICAL,
            ChunkingStrategy.SENTENCE_AWARE,
            ChunkingStrategy.ADAPTIVE,
            ChunkingStrategy.FIXED_SIZE
        ]
        
        for strategy in strategies:
            # Should not raise an exception
            chunks = document_processor.hierarchical_chunker.chunk_document(
                "Test text for chunking strategy validation.",
                strategy=strategy
            )
            assert isinstance(chunks, list)


if __name__ == "__main__":
    pytest.main([__file__])