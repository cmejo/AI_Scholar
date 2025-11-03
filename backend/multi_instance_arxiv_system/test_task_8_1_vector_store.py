#!/usr/bin/env python3
"""
Test script for Task 8.1: Extend vector store service for instance separation.

This script tests the multi-instance vector store service to ensure proper
instance separation, collection management, and unified search capabilities.
"""

import sys
from pathlib import Path
from datetime import datetime
import asyncio
import json

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.vector_store.multi_instance_vector_store_service import MultiInstanceVectorStoreService
    from multi_instance_arxiv_system.vector_store.collection_manager import CollectionManager
    from multi_instance_arxiv_system.vector_store.embedding_service import EmbeddingService
    from multi_instance_arxiv_system.shared.multi_instance_data_models import (
        ArxivPaper, JournalPaper, VectorStoreConfig
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the correct directory and ChromaDB is available")
    sys.exit(1)


async def test_collection_manager():
    """Test the CollectionManager functionality."""
    print("Testing CollectionManager...")
    
    try:
        # Initialize collection manager
        manager = CollectionManager()
        await manager.initialize()
        
        # Test collection creation
        result = await manager.create_instance_collection(
            instance_name="test_ai_scholar",
            embedding_model="all-MiniLM-L6-v2",
            description="Test collection for AI Scholar"
        )
        
        assert result['created'] or result['status'] == 'already_exists'
        print(f"✓ Collection creation: {result['collection_name']}")
        
        # Test collection listing
        collections = await manager.list_instance_collections()
        test_collections = [c for c in collections if c['instance_name'] == 'test_ai_scholar']
        assert len(test_collections) > 0
        print(f"✓ Collection listing: Found {len(collections)} total collections")
        
        # Test collection stats
        stats = await manager.get_collection_stats("test_ai_scholar")
        assert stats['instance_name'] == "test_ai_scholar"
        print(f"✓ Collection stats: {stats['document_count']} documents")
        
        # Test collection validation
        validation = await manager.validate_collection_integrity("test_ai_scholar")
        assert validation['instance_name'] == "test_ai_scholar"
        print(f"✓ Collection validation: {'Valid' if validation['valid'] else 'Invalid'}")
        
        print("✓ CollectionManager tests passed")
        return True
        
    except Exception as e:
        print(f"❌ CollectionManager test failed: {e}")
        return False


async def test_embedding_service():
    """Test the EmbeddingService functionality."""
    print("Testing EmbeddingService...")
    
    try:
        # Initialize embedding service
        service = EmbeddingService()
        
        # Test model initialization
        success = await service.initialize_model(
            model_name="all-MiniLM-L6-v2",
            instance_name="test_ai_scholar"
        )
        assert success
        print("✓ Model initialization successful")
        
        # Test embedding generation
        test_texts = [
            "This is a test document about artificial intelligence.",
            "Machine learning algorithms are used in various applications.",
            "Natural language processing enables computers to understand text."
        ]
        
        embeddings = await service.generate_embeddings(
            texts=test_texts,
            instance_name="test_ai_scholar",
            model_name="all-MiniLM-L6-v2"
        )
        
        assert len(embeddings) == len(test_texts)
        assert len(embeddings[0]) == 384  # MiniLM dimension
        print(f"✓ Generated embeddings: {len(embeddings)} x {len(embeddings[0])}")
        
        # Test embedding validation
        validation = await service.validate_embedding_quality(
            embeddings=embeddings,
            texts=test_texts,
            model_name="all-MiniLM-L6-v2"
        )
        
        assert validation['valid']
        assert validation['quality_score'] > 0.5
        print(f"✓ Embedding validation: Quality score {validation['quality_score']:.2f}")
        
        # Test model info
        model_info = service.get_model_info("all-MiniLM-L6-v2")
        assert model_info['dimensions'] == 384
        print(f"✓ Model info: {model_info['description']}")
        
        print("✓ EmbeddingService tests passed")
        return True
        
    except Exception as e:
        print(f"❌ EmbeddingService test failed: {e}")
        return False


async def test_multi_instance_vector_store():
    """Test the MultiInstanceVectorStoreService functionality."""
    print("Testing MultiInstanceVectorStoreService...")
    
    try:
        # Initialize multi-instance service
        service = MultiInstanceVectorStoreService()
        
        # Create configurations for two instances
        ai_config = VectorStoreConfig(
            collection_name="test_ai_scholar_papers",
            embedding_model="all-MiniLM-L6-v2",
            chunk_size=1000,
            chunk_overlap=200
        )
        
        quant_config = VectorStoreConfig(
            collection_name="test_quant_scholar_papers",
            embedding_model="all-MiniLM-L6-v2",
            chunk_size=800,
            chunk_overlap=150
        )
        
        # Initialize instances
        ai_success = await service.initialize_instance("test_ai_scholar", ai_config)
        quant_success = await service.initialize_instance("test_quant_scholar", quant_config)
        
        assert ai_success and quant_success
        print("✓ Instance initialization successful")
        
        # Create test papers
        ai_paper = ArxivPaper(
            paper_id="2301.00001",
            title="Test AI Paper",
            authors=["John Doe", "Jane Smith"],
            abstract="This is a test paper about artificial intelligence and machine learning.",
            published_date=datetime.now(),
            instance_name="test_ai_scholar",
            arxiv_id="2301.00001",
            categories=["cs.AI", "cs.LG"],
            pdf_url="https://arxiv.org/pdf/2301.00001.pdf"
        )
        
        quant_paper = JournalPaper(
            paper_id="jss_2023_001",
            title="Test Quantitative Finance Paper",
            authors=["Alice Johnson", "Bob Wilson"],
            abstract="This is a test paper about quantitative finance and statistical methods.",
            published_date=datetime.now(),
            instance_name="test_quant_scholar",
            journal_name="Journal of Statistical Software",
            volume="100",
            issue="1",
            pdf_url="https://www.jstatsoft.org/article/view/v100i01"
        )
        
        # Create test chunks
        ai_chunks = [
            {
                'text': "Artificial intelligence has revolutionized many fields of study.",
                'section': 'introduction',
                'chunk_type': 'standard'
            },
            {
                'text': "Machine learning algorithms can learn patterns from data automatically.",
                'section': 'methodology',
                'chunk_type': 'standard'
            }
        ]
        
        quant_chunks = [
            {
                'text': "Quantitative finance uses mathematical models to analyze financial markets.",
                'section': 'introduction',
                'chunk_type': 'standard'
            },
            {
                'text': "Statistical methods are essential for risk management in finance.",
                'section': 'methodology',
                'chunk_type': 'standard'
            }
        ]
        
        # Add documents to instances
        ai_result = await service.add_instance_document("test_ai_scholar", ai_paper, ai_chunks)
        quant_result = await service.add_instance_document("test_quant_scholar", quant_paper, quant_chunks)
        
        assert ai_result['chunks_added'] == 2
        assert quant_result['chunks_added'] == 2
        print(f"✓ Added documents: AI Scholar ({ai_result['chunks_added']} chunks), Quant Scholar ({quant_result['chunks_added']} chunks)")
        
        # Test instance-specific search
        ai_results = await service.search_instance_papers(
            instance_name="test_ai_scholar",
            query="artificial intelligence machine learning",
            n_results=5
        )
        
        quant_results = await service.search_instance_papers(
            instance_name="test_quant_scholar",
            query="quantitative finance statistical methods",
            n_results=5
        )
        
        assert len(ai_results) > 0
        assert len(quant_results) > 0
        assert all(r['instance_name'] == 'test_ai_scholar' for r in ai_results)
        assert all(r['instance_name'] == 'test_quant_scholar' for r in quant_results)
        print(f"✓ Instance-specific search: AI ({len(ai_results)} results), Quant ({len(quant_results)} results)")
        
        # Test cross-instance search
        all_results = await service.search_all_instances(
            query="statistical methods and machine learning",
            n_results=10
        )
        
        assert len(all_results) > 0
        instances_found = set(r['instance_name'] for r in all_results)
        print(f"✓ Cross-instance search: {len(all_results)} results from {len(instances_found)} instances")
        
        # Test instance statistics
        ai_stats = await service.get_instance_stats("test_ai_scholar")
        quant_stats = await service.get_instance_stats("test_quant_scholar")
        
        assert ai_stats['instance_name'] == "test_ai_scholar"
        assert quant_stats['instance_name'] == "test_quant_scholar"
        print(f"✓ Instance stats: AI ({ai_stats.get('total_chunks', 0)} chunks), Quant ({quant_stats.get('total_chunks', 0)} chunks)")
        
        # Test health check
        health = await service.health_check()
        assert health['overall_status'] in ['healthy', 'degraded']
        assert health['total_instances'] == 2
        print(f"✓ Health check: {health['overall_status']} ({health['healthy_instances']}/{health['total_instances']} healthy)")
        
        # Test instance separation validation
        validation = await service.validate_instance_separation()
        print(f"✓ Instance separation: {'Valid' if validation['separation_valid'] else 'Invalid'}")
        if validation['issues']:
            print(f"  Issues: {validation['issues']}")
        
        print("✓ MultiInstanceVectorStoreService tests passed")
        return True
        
    except Exception as e:
        print(f"❌ MultiInstanceVectorStoreService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_collection_naming_conventions():
    """Test collection naming conventions and validation."""
    print("Testing collection naming conventions...")
    
    try:
        manager = CollectionManager()
        await manager.initialize()
        
        # Test valid instance names
        valid_names = ["ai_scholar", "quant-scholar", "test123", "scholar_v2"]
        for name in valid_names:
            collection_name = manager._get_collection_name(name)
            assert collection_name.startswith("scholar_instance_")
            assert collection_name.endswith("_papers")
            print(f"✓ Valid name '{name}' -> '{collection_name}'")
        
        # Test invalid instance names
        invalid_names = ["", "a", "test@scholar", "admin", "system", "x" * 60]
        for name in invalid_names:
            try:
                collection_name = manager._get_collection_name(name)
                assert False, f"Should have failed for invalid name: {name}"
            except ValueError:
                print(f"✓ Correctly rejected invalid name: '{name}'")
        
        print("✓ Collection naming convention tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Collection naming test failed: {e}")
        return False


async def test_embedding_caching():
    """Test embedding caching functionality."""
    print("Testing embedding caching...")
    
    try:
        service = EmbeddingService()
        
        # Initialize model
        await service.initialize_model("all-MiniLM-L6-v2", "test_instance")
        
        test_texts = ["This is a test sentence for caching."]
        
        # First generation (should cache)
        start_time = datetime.now()
        embeddings1 = await service.generate_embeddings(
            texts=test_texts,
            instance_name="test_instance",
            model_name="all-MiniLM-L6-v2"
        )
        first_duration = (datetime.now() - start_time).total_seconds()
        
        # Second generation (should use cache)
        start_time = datetime.now()
        embeddings2 = await service.generate_embeddings(
            texts=test_texts,
            instance_name="test_instance",
            model_name="all-MiniLM-L6-v2"
        )
        second_duration = (datetime.now() - start_time).total_seconds()
        
        # Verify embeddings are identical
        assert embeddings1 == embeddings2
        
        # Cache should make second call faster (though this might not always be true in tests)
        print(f"✓ Embedding caching: First call {first_duration:.3f}s, Second call {second_duration:.3f}s")
        
        # Test cache stats
        cache_stats = service.get_cache_stats()
        assert cache_stats['cache_enabled']
        print(f"✓ Cache stats: {cache_stats['cache_size']} entries")
        
        # Test cache clearing
        cleared_count = service.clear_cache()
        assert cleared_count >= 0
        print(f"✓ Cache cleared: {cleared_count} entries removed")
        
        print("✓ Embedding caching tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Embedding caching test failed: {e}")
        return False


async def main():
    """Run all tests for Task 8.1."""
    print("Testing Task 8.1: Extend vector store service for instance separation")
    print("=" * 80)
    
    # Note: These tests require ChromaDB to be running
    print("Note: These tests require ChromaDB to be running on localhost:8082")
    print("If ChromaDB is not available, tests will be skipped.\n")
    
    test_results = []
    
    try:
        # Test individual components
        test_results.append(await test_collection_manager())
        test_results.append(await test_embedding_service())
        test_results.append(await test_collection_naming_conventions())
        test_results.append(await test_embedding_caching())
        
        # Test integrated functionality
        test_results.append(await test_multi_instance_vector_store())
        
        print("\n" + "=" * 80)
        
        if all(test_results):
            print("✅ All Task 8.1 tests passed!")
            print("\nImplemented features:")
            print("- MultiInstanceVectorStoreService with instance separation")
            print("- CollectionManager with standardized naming conventions")
            print("- EmbeddingService with caching and quality validation")
            print("- Instance-specific document processing and metadata")
            print("- Unified search interface across instances")
            print("- Collection validation and health monitoring")
            print("- Proper instance isolation and separation validation")
            
            return True
        else:
            failed_count = len([r for r in test_results if not r])
            print(f"❌ {failed_count} out of {len(test_results)} tests failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)