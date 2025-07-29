#!/usr/bin/env python3
"""
Simple integration test for hierarchical chunking functionality
Tests the core integration without external dependencies
"""
import sys
import os
import json
import logging
from unittest.mock import Mock, patch

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_hierarchical_chunking_service():
    """Test the hierarchical chunking service directly"""
    logger.info("=== Testing Hierarchical Chunking Service ===")
    
    try:
        from services.hierarchical_chunking import HierarchicalChunker, ChunkingStrategy
        
        # Create chunker instance with smaller chunk size to force multiple levels
        chunker = HierarchicalChunker(
            base_chunk_size=100,  # Smaller chunk size to force hierarchical levels
            overlap_percentage=0.15,
            max_levels=3
        )
        
        # Sample text for testing - longer text to ensure multiple hierarchical levels
        sample_text = """
        Introduction to Machine Learning and Artificial Intelligence
        
        Machine learning is a subset of artificial intelligence that focuses on algorithms 
        that can learn from data without being explicitly programmed. It has three main 
        types: supervised learning, unsupervised learning, and reinforcement learning.
        Each type serves different purposes and uses different approaches to solve problems.
        
        Supervised Learning Fundamentals
        
        Supervised learning uses labeled data to train models that can make predictions.
        Common algorithms include linear regression for continuous values, decision trees 
        for classification tasks, and neural networks for complex pattern recognition.
        The goal is to predict outcomes for new, unseen data based on patterns learned 
        from training examples. This approach requires large datasets with known correct answers.
        
        Applications of supervised learning are widespread in modern technology.
        Image classification systems can identify objects in photographs with high accuracy.
        Spam detection filters automatically sort unwanted emails from legitimate messages.
        Medical diagnosis systems assist doctors in identifying diseases from symptoms and test results.
        Financial fraud detection systems monitor transactions for suspicious patterns.
        
        Unsupervised Learning Techniques
        
        Unsupervised learning finds hidden patterns in data without labeled examples.
        This approach is particularly useful when you don't know what you're looking for.
        Clustering algorithms group similar data points together to reveal natural categories.
        Dimensionality reduction techniques simplify complex datasets while preserving important information.
        K-means clustering is one of the most popular algorithms for grouping data.
        Principal component analysis helps reduce the number of variables in a dataset.
        
        Association rule learning discovers relationships between different variables.
        Anomaly detection identifies unusual patterns that might indicate problems or opportunities.
        These techniques are essential for exploratory data analysis and pattern discovery.
        
        Reinforcement Learning Systems
        
        Reinforcement learning learns optimal actions through trial and error interactions.
        An agent operates in an environment and receives rewards or penalties for actions taken.
        The goal is to maximize cumulative reward over time through strategic decision making.
        This approach mimics how humans and animals learn through experience and feedback.
        
        Applications include game playing systems that can master complex strategy games.
        Robotics systems learn to navigate and manipulate objects in physical environments.
        Autonomous vehicles use reinforcement learning to make driving decisions.
        Recommendation systems learn user preferences to suggest relevant content.
        Trading algorithms optimize investment strategies based on market feedback.
        
        Deep Learning and Neural Networks
        
        Deep learning is a specialized subset of machine learning using artificial neural networks.
        These networks are inspired by the structure and function of biological neural networks.
        Multiple layers of interconnected nodes process information in increasingly abstract ways.
        Each layer learns to recognize different features and patterns in the input data.
        
        Convolutional neural networks excel at processing visual information like images and videos.
        Recurrent neural networks are designed to handle sequential data like text and speech.
        Transformer architectures have revolutionized natural language processing tasks.
        Generative adversarial networks can create realistic synthetic data and images.
        
        The Future of Machine Learning
        
        Machine learning continues to evolve rapidly with new techniques and applications.
        Quantum machine learning explores the potential of quantum computing for AI tasks.
        Federated learning enables training models across distributed devices while preserving privacy.
        Explainable AI focuses on making machine learning decisions more transparent and interpretable.
        AutoML systems automate the process of building and optimizing machine learning models.
        
        Ethical considerations become increasingly important as AI systems affect more aspects of society.
        Bias detection and mitigation ensure fair treatment across different demographic groups.
        Privacy-preserving techniques protect sensitive information while enabling useful analysis.
        Robustness and safety measures prevent AI systems from causing unintended harm.
        """
        
        # Test hierarchical chunking
        chunks = chunker.chunk_document(sample_text, strategy=ChunkingStrategy.HIERARCHICAL)
        
        logger.info(f"Created {len(chunks)} hierarchical chunks")
        
        # Verify chunk structure
        levels = set(chunk.chunk_level for chunk in chunks)
        logger.info(f"Hierarchical levels: {sorted(levels)}")
        
        # Display chunk information
        for i, chunk in enumerate(chunks[:5]):  # Show first 5 chunks
            logger.info(f"Chunk {i+1}:")
            logger.info(f"  Level: {chunk.chunk_level}")
            logger.info(f"  Index: {chunk.chunk_index}")
            logger.info(f"  Parent: {chunk.parent_chunk_id}")
            logger.info(f"  Content length: {len(chunk.content)}")
            logger.info(f"  Content preview: {chunk.content[:100].strip()}...")
            logger.info(f"  Overlap start: {chunk.overlap_start}")
            logger.info(f"  Overlap end: {chunk.overlap_end}")
            logger.info(f"  Sentence boundaries: {len(chunk.sentence_boundaries)} sentences")
            logger.info(f"  Metadata keys: {list(chunk.metadata.keys())}")
            logger.info("---")
        
        # Test overlap statistics
        overlap_stats = chunker.overlap_manager.get_overlap_statistics()
        logger.info(f"Overlap statistics: {json.dumps(overlap_stats, indent=2)}")
        
        # Verify basic requirements
        assert len(chunks) > 0, "Should create chunks"
        assert len(levels) > 1, "Should have multiple hierarchical levels"
        assert any(chunk.parent_chunk_id is not None for chunk in chunks), "Should have parent-child relationships"
        
        logger.info("✅ Hierarchical chunking service test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Hierarchical chunking service test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_database_models():
    """Test database model integration"""
    logger.info("=== Testing Database Models ===")
    
    try:
        from core.database import DocumentChunkEnhanced, Base
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # Create in-memory database
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        
        # Create test enhanced chunk
        chunk = DocumentChunkEnhanced(
            document_id="test_doc_123",
            content="This is a test chunk with hierarchical information.",
            chunk_level=0,
            chunk_index=0,
            overlap_start=None,
            overlap_end=50,
            sentence_boundaries='[0, 1, 2]',
            chunk_metadata={
                'strategy': 'hierarchical',
                'document_type': 'text',
                'words_count': 10
            }
        )
        
        db.add(chunk)
        db.commit()
        
        # Retrieve and verify
        retrieved = db.query(DocumentChunkEnhanced).filter(
            DocumentChunkEnhanced.document_id == "test_doc_123"
        ).first()
        
        assert retrieved is not None, "Should retrieve chunk"
        assert retrieved.chunk_level == 0, "Should have correct level"
        assert retrieved.overlap_end == 50, "Should have overlap information"
        assert retrieved.chunk_metadata['strategy'] == 'hierarchical', "Should have metadata"
        
        logger.info(f"Successfully created and retrieved enhanced chunk: {retrieved.id}")
        logger.info(f"Chunk metadata: {json.dumps(retrieved.chunk_metadata, indent=2)}")
        
        db.close()
        
        logger.info("✅ Database models test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database models test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_vector_store_structure():
    """Test vector store structure without external dependencies"""
    logger.info("=== Testing Vector Store Structure ===")
    
    try:
        # Import first, then mock
        import services.vector_store
        
        # Mock the external dependencies
        with patch.object(services.vector_store, 'chromadb'), \
             patch.object(services.vector_store, 'requests'), \
             patch.object(services.vector_store, 'settings') as mock_settings:
            
            mock_settings.OLLAMA_URL = "http://localhost:11434"
            mock_settings.EMBEDDING_MODEL = "nomic-embed-text"
            mock_settings.CHROMA_PERSIST_DIR = "/tmp/test"
            
            from services.vector_store import VectorStoreService
            
            # Create vector store instance
            vector_store = VectorStoreService()
            
            # Mock collection
            vector_store.collection = Mock()
            vector_store.collection.add = Mock()
            vector_store.collection.query = Mock()
            vector_store.collection.get = Mock()
            
            # Test that the service has the required methods
            assert hasattr(vector_store, 'add_document'), "Should have add_document method"
            assert hasattr(vector_store, 'hierarchical_search'), "Should have hierarchical_search method"
            assert hasattr(vector_store, 'get_chunk_hierarchy_info'), "Should have get_chunk_hierarchy_info method"
            
            logger.info("Vector store service structure verified")
            
            # Test hierarchical search method signature
            import inspect
            search_sig = inspect.signature(vector_store.hierarchical_search)
            expected_params = ['query', 'user_id', 'limit', 'preferred_level', 'include_context']
            actual_params = list(search_sig.parameters.keys())
            
            for param in expected_params:
                assert param in actual_params, f"Should have {param} parameter"
            
            logger.info("Hierarchical search method signature verified")
            
            logger.info("✅ Vector store structure test passed!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Vector store structure test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_document_processor_structure():
    """Test document processor structure without external dependencies"""
    logger.info("=== Testing Document Processor Structure ===")
    
    try:
        # Import first, then mock
        import services.document_processor
        
        # Mock external dependencies
        with patch.object(services.document_processor, 'aiofiles'), \
             patch.object(services.document_processor, 'PyPDF2'), \
             patch.object(services.document_processor, 'pdfplumber'), \
             patch.object(services.document_processor, 'pytesseract'), \
             patch.object(services.document_processor, 'settings') as mock_settings:
            
            mock_settings.UPLOAD_DIR = "/tmp/test"
            
            from services.document_processor import DocumentProcessor
            
            # Create processor instance
            processor = DocumentProcessor()
            
            # Test that the processor has hierarchical chunker
            assert hasattr(processor, 'hierarchical_chunker'), "Should have hierarchical_chunker"
            assert processor.hierarchical_chunker is not None, "Hierarchical chunker should be initialized"
            
            # Test that required methods exist
            required_methods = [
                'get_chunk_hierarchy',
                'get_contextual_chunks', 
                'get_chunk_relationships',
                'get_chunking_statistics',
                'reprocess_document_with_hierarchical_chunking'
            ]
            
            for method in required_methods:
                assert hasattr(processor, method), f"Should have {method} method"
            
            logger.info("Document processor structure verified")
            
            # Test method signatures
            import inspect
            
            # Test get_chunk_hierarchy signature
            hierarchy_sig = inspect.signature(processor.get_chunk_hierarchy)
            assert 'document_id' in hierarchy_sig.parameters, "Should have document_id parameter"
            assert 'user_id' in hierarchy_sig.parameters, "Should have user_id parameter"
            
            # Test get_contextual_chunks signature
            contextual_sig = inspect.signature(processor.get_contextual_chunks)
            assert 'chunk_id' in contextual_sig.parameters, "Should have chunk_id parameter"
            assert 'user_id' in contextual_sig.parameters, "Should have user_id parameter"
            assert 'context_window' in contextual_sig.parameters, "Should have context_window parameter"
            
            logger.info("Document processor method signatures verified")
            
            logger.info("✅ Document processor structure test passed!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Document processor structure test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    logger.info("🚀 Starting Hierarchical Chunking Integration Tests")
    
    tests = [
        ("Hierarchical Chunking Service", test_hierarchical_chunking_service),
        ("Database Models", test_database_models),
        ("Vector Store Structure", test_vector_store_structure),
        ("Document Processor Structure", test_document_processor_structure)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} PASSED")
            else:
                failed += 1
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            logger.error(f"❌ {test_name} FAILED with exception: {str(e)}")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"TEST SUMMARY")
    logger.info(f"{'='*50}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total:  {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 All integration tests passed!")
        logger.info("✅ Task 2.3 - Hierarchical chunking integration is working correctly")
        return 0
    else:
        logger.error(f"❌ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())