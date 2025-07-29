#!/usr/bin/env python3
"""
Integration test for hierarchical chunking with document processor and vector store
"""
import asyncio
import tempfile
import os
import json
import logging
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our services
from core.database import Base, Document, DocumentChunk, DocumentChunkEnhanced
from services.document_processor import DocumentProcessor
from services.vector_store import VectorStoreService
from services.hierarchical_chunking import ChunkingStrategy

class HierarchicalIntegrationDemo:
    """Demo class for testing hierarchical chunking integration"""
    
    def __init__(self):
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Setup test database and mock services"""
        # Create in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(self.engine)
        self.TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create temp directory for uploads
        self.temp_dir = tempfile.mkdtemp()
        
        logger.info(f"Test environment setup complete. Temp dir: {self.temp_dir}")
    
    async def test_document_processing_integration(self):
        """Test complete document processing with hierarchical chunking"""
        logger.info("=== Testing Document Processing Integration ===")
        
        # Mock settings
        with patch('services.document_processor.settings') as mock_settings:
            mock_settings.UPLOAD_DIR = self.temp_dir
            mock_settings.CHUNK_SIZE = 512
            mock_settings.CHUNK_OVERLAP = 50
            
            # Mock database session
            with patch('services.document_processor.get_db') as mock_get_db:
                db_session = self.TestSessionLocal()
                mock_get_db.return_value = iter([db_session])
                
                # Create document processor
                processor = DocumentProcessor()
                
                # Create sample text content
                sample_text = """
                Introduction to Artificial Intelligence
                
                Artificial Intelligence (AI) is a branch of computer science that aims to create 
                intelligent machines that work and react like humans. AI has become increasingly 
                important in modern technology and business applications.
                
                Machine Learning Fundamentals
                
                Machine learning is a subset of AI that provides systems the ability to automatically 
                learn and improve from experience without being explicitly programmed. It focuses on 
                the development of computer programs that can access data and use it to learn for themselves.
                
                Types of Machine Learning
                
                There are three main types of machine learning: supervised learning, unsupervised learning, 
                and reinforcement learning. Each type has its own characteristics and applications.
                
                Supervised Learning
                
                Supervised learning uses labeled training data to learn a mapping function from input 
                variables to output variables. Common algorithms include linear regression, decision trees, 
                and support vector machines.
                
                Applications include image classification, spam detection, and medical diagnosis. These 
                applications require large datasets with known correct answers.
                
                Unsupervised Learning
                
                Unsupervised learning finds hidden patterns in data without labeled examples. Common 
                techniques include clustering, association rules, and dimensionality reduction.
                
                Reinforcement Learning
                
                Reinforcement learning learns optimal actions through trial and error interactions with 
                an environment. The agent receives rewards or penalties for actions taken.
                """
                
                # Create temporary text file
                text_file_path = os.path.join(self.temp_dir, "ai_guide.txt")
                with open(text_file_path, 'w', encoding='utf-8') as f:
                    f.write(sample_text)
                
                try:
                    # Process the text file
                    result = await processor._process_text(text_file_path, "test_doc_123", db_session)
                    
                    logger.info(f"Processing result: {json.dumps(result, indent=2)}")
                    
                    # Verify results
                    assert result['chunks_count'] > 0, "Should create chunks"
                    assert result['embeddings_count'] > 0, "Should create embeddings"
                    assert 'hierarchical_levels' in result['details'], "Should have hierarchical levels"
                    assert result['details']['hierarchical_levels'] > 1, "Should have multiple levels"
                    
                    # Check database for enhanced chunks
                    enhanced_chunks = db_session.query(DocumentChunkEnhanced).filter(
                        DocumentChunkEnhanced.document_id == "test_doc_123"
                    ).all()
                    
                    logger.info(f"Created {len(enhanced_chunks)} enhanced chunks")
                    
                    # Verify hierarchical structure
                    levels = set(chunk.chunk_level for chunk in enhanced_chunks)
                    logger.info(f"Hierarchical levels found: {sorted(levels)}")
                    
                    # Display chunk information
                    for i, chunk in enumerate(enhanced_chunks[:5]):  # Show first 5 chunks
                        logger.info(f"Chunk {i+1}:")
                        logger.info(f"  Level: {chunk.chunk_level}")
                        logger.info(f"  Index: {chunk.chunk_index}")
                        logger.info(f"  Parent: {chunk.parent_chunk_id}")
                        logger.info(f"  Content preview: {chunk.content[:100]}...")
                        logger.info(f"  Overlap start: {chunk.overlap_start}")
                        logger.info(f"  Overlap end: {chunk.overlap_end}")
                        logger.info(f"  Sentence boundaries: {chunk.sentence_boundaries}")
                        logger.info("---")
                    
                    # Test hierarchy retrieval methods
                    await self.test_hierarchy_retrieval_methods(processor, db_session)
                    
                    logger.info("✅ Document processing integration test passed!")
                    return True
                    
                except Exception as e:
                    logger.error(f"❌ Document processing integration test failed: {str(e)}")
                    return False
                finally:
                    if os.path.exists(text_file_path):
                        os.unlink(text_file_path)
    
    async def test_hierarchy_retrieval_methods(self, processor, db_session):
        """Test chunk hierarchy retrieval methods"""
        logger.info("=== Testing Hierarchy Retrieval Methods ===")
        
        # Create test document in database
        document = Document(
            id="test_doc_123",
            user_id="test_user",
            name="ai_guide.txt",
            file_path="/tmp/ai_guide.txt",
            content_type="text/plain",
            size=1000,
            status="completed"
        )
        db_session.add(document)
        db_session.commit()
        
        # Mock get_db for the processor methods
        with patch('services.document_processor.get_db') as mock_get_db:
            mock_get_db.return_value = iter([db_session])
            
            try:
                # Test get_chunk_hierarchy
                hierarchy = await processor.get_chunk_hierarchy("test_doc_123", "test_user")
                logger.info(f"Hierarchy structure: {json.dumps(hierarchy, indent=2, default=str)}")
                
                assert hierarchy['document_id'] == "test_doc_123"
                assert 'levels' in hierarchy
                assert 'relationships' in hierarchy
                
                # Test get_contextual_chunks (if we have chunks)
                enhanced_chunks = db_session.query(DocumentChunkEnhanced).filter(
                    DocumentChunkEnhanced.document_id == "test_doc_123"
                ).all()
                
                if enhanced_chunks:
                    first_chunk_id = enhanced_chunks[0].id
                    contextual = await processor.get_contextual_chunks(first_chunk_id, "test_user")
                    logger.info(f"Contextual chunks for {first_chunk_id}: {len(contextual)} chunks")
                    
                    # Test get_chunk_relationships
                    relationships = await processor.get_chunk_relationships(first_chunk_id, "test_user")
                    logger.info(f"Chunk relationships: {json.dumps(relationships, indent=2, default=str)}")
                
                # Test chunking statistics
                stats = await processor.get_chunking_statistics("test_doc_123", "test_user")
                logger.info(f"Chunking statistics: {json.dumps(stats, indent=2, default=str)}")
                
                logger.info("✅ Hierarchy retrieval methods test passed!")
                
            except Exception as e:
                logger.error(f"❌ Hierarchy retrieval methods test failed: {str(e)}")
                raise e
    
    async def test_vector_store_integration(self):
        """Test vector store integration with hierarchical chunks"""
        logger.info("=== Testing Vector Store Integration ===")
        
        try:
            # Mock vector store
            with patch('services.vector_store.settings') as mock_settings:
                mock_settings.OLLAMA_URL = "http://localhost:11434"
                mock_settings.EMBEDDING_MODEL = "nomic-embed-text"
                mock_settings.CHROMA_PERSIST_DIR = self.temp_dir
                
                vector_store = VectorStoreService()
                
                # Mock ChromaDB collection
                vector_store.collection = Mock()
                vector_store.collection.add = Mock()
                vector_store.collection.query = Mock()
                vector_store.collection.get = Mock()
                vector_store.collection.count = Mock(return_value=0)
                
                # Mock embedding generation
                vector_store.generate_embedding = AsyncMock(return_value=[0.1] * 384)
                
                # Create mock enhanced chunks
                mock_chunks = [
                    Mock(
                        id="chunk_1",
                        document_id="test_doc",
                        content="This is a test chunk at level 0 with some content for testing.",
                        chunk_level=0,
                        chunk_index=0,
                        parent_chunk_id=None,
                        overlap_start=None,
                        overlap_end=None,
                        sentence_boundaries='[0, 1]',
                        chunk_metadata={'strategy': 'hierarchical', 'document_type': 'text'}
                    ),
                    Mock(
                        id="chunk_2",
                        document_id="test_doc",
                        content="This is a parent chunk at level 1 containing multiple sentences and more comprehensive content.",
                        chunk_level=1,
                        chunk_index=0,
                        parent_chunk_id=None,
                        overlap_start=None,
                        overlap_end=50,
                        sentence_boundaries='[0, 1, 2]',
                        chunk_metadata={'strategy': 'hierarchical', 'document_type': 'text', 'child_chunks': ['chunk_1']}
                    )
                ]
                
                # Mock database query
                with patch('services.vector_store.get_db') as mock_get_db:
                    db_session = Mock()
                    db_session.query.return_value.filter.return_value.all.return_value = mock_chunks
                    mock_get_db.return_value = iter([db_session])
                    
                    # Test adding hierarchical chunks
                    document_data = {"id": "test_doc", "name": "test_document.txt"}
                    await vector_store.add_document(document_data)
                    
                    # Verify that add was called
                    vector_store.collection.add.assert_called_once()
                    call_args = vector_store.collection.add.call_args
                    
                    # Check the structure of what was added
                    ids = call_args[1]['ids']
                    embeddings = call_args[1]['embeddings']
                    documents = call_args[1]['documents']
                    metadatas = call_args[1]['metadatas']
                    
                    logger.info(f"Added {len(ids)} chunks to vector store")
                    logger.info(f"Chunk IDs: {ids}")
                    
                    # Verify hierarchical structure in vector store
                    for i, metadata in enumerate(metadatas):
                        logger.info(f"Chunk {i+1} metadata: {json.dumps(metadata, indent=2)}")
                        assert metadata['chunk_type'] == 'hierarchical'
                        assert 'chunk_level' in metadata
                        assert 'has_overlap' in metadata
                    
                    # Test hierarchical search
                    await self.test_hierarchical_search(vector_store)
                    
                    logger.info("✅ Vector store integration test passed!")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Vector store integration test failed: {str(e)}")
            return False
    
    async def test_hierarchical_search(self, vector_store):
        """Test hierarchical search functionality"""
        logger.info("=== Testing Hierarchical Search ===")
        
        # Mock search results
        mock_search_results = {
            "ids": [["test_doc_L0_0", "test_doc_L1_0"]],
            "documents": [["Level 0 content for testing", "Level 1 content with more comprehensive information"]],
            "metadatas": [[
                {
                    "document_id": "test_doc",
                    "chunk_level": 0,
                    "chunk_type": "hierarchical",
                    "has_overlap": False,
                    "content_length": 100,
                    "document_name": "test_document.txt"
                },
                {
                    "document_id": "test_doc", 
                    "chunk_level": 1,
                    "chunk_type": "hierarchical",
                    "has_overlap": True,
                    "content_length": 200,
                    "document_name": "test_document.txt"
                }
            ]],
            "distances": [[0.2, 0.3]]
        }
        
        vector_store.collection.query.return_value = mock_search_results
        vector_store.collection.get.return_value = {"ids": [], "documents": [], "metadatas": []}
        
        # Test hierarchical search
        results = await vector_store.hierarchical_search(
            query="test query about artificial intelligence",
            user_id="test_user",
            limit=5,
            include_context=True
        )
        
        logger.info(f"Hierarchical search returned {len(results)} results")
        
        for i, result in enumerate(results):
            logger.info(f"Result {i+1}:")
            logger.info(f"  ID: {result['id']}")
            logger.info(f"  Content: {result['content'][:100]}...")
            logger.info(f"  Relevance: {result['relevance']:.3f}")
            logger.info(f"  Level: {result['metadata']['chunk_level']}")
            logger.info(f"  Has overlap: {result['metadata']['has_overlap']}")
            logger.info(f"  Context available: {'hierarchical_context' in result}")
            logger.info("---")
        
        assert len(results) > 0, "Should return search results"
        for result in results:
            assert 'hierarchical_context' in result, "Should include hierarchical context"
            assert 'metadata' in result, "Should include metadata"
            assert result['metadata']['chunk_type'] == 'hierarchical', "Should be hierarchical chunks"
        
        logger.info("✅ Hierarchical search test passed!")
    
    async def test_complete_workflow(self):
        """Test the complete workflow from document upload to search"""
        logger.info("=== Testing Complete Workflow ===")
        
        try:
            # Step 1: Document processing
            doc_success = await self.test_document_processing_integration()
            if not doc_success:
                return False
            
            # Step 2: Vector store integration
            vector_success = await self.test_vector_store_integration()
            if not vector_success:
                return False
            
            logger.info("✅ Complete workflow test passed!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Complete workflow test failed: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up test environment"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info("Test environment cleaned up")
        except Exception as e:
            logger.warning(f"Cleanup warning: {str(e)}")

async def main():
    """Run the integration demo"""
    logger.info("🚀 Starting Hierarchical Chunking Integration Demo")
    
    demo = HierarchicalIntegrationDemo()
    
    try:
        success = await demo.test_complete_workflow()
        
        if success:
            logger.info("🎉 All integration tests passed successfully!")
            logger.info("✅ Task 2.3 - Hierarchical chunking integration is working correctly")
        else:
            logger.error("❌ Some integration tests failed")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Demo failed with exception: {str(e)}")
        return 1
    finally:
        demo.cleanup()
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))