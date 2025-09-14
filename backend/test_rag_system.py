#!/usr/bin/env python3
"""
Test script for the Scientific RAG system
Tests PDF processing, vector storage, and query functionality
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent))

from services.scientific_pdf_processor import scientific_pdf_processor
from services.vector_store_service import vector_store_service
from services.ollama_service import ollama_service
from services.scientific_rag_service import scientific_rag_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rag_system():
    """Test the complete RAG system"""
    
    print("🚀 Testing AI Scholar RAG System")
    print("=" * 50)
    
    # Test 1: Initialize services
    print("\n1. Initializing services...")
    try:
        # Initialize vector store
        await vector_store_service.initialize()
        print("✅ Vector store initialized")
        
        # Initialize Ollama service
        await ollama_service.initialize()
        print("✅ Ollama service initialized")
        
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False
    
    # Test 2: Health checks
    print("\n2. Running health checks...")
    try:
        vector_health = await vector_store_service.health_check()
        ollama_health = await ollama_service.health_check()
        
        print(f"Vector store status: {vector_health.get('status', 'unknown')}")
        print(f"Ollama status: {ollama_health.get('status', 'unknown')}")
        
        if vector_health.get('status') != 'healthy':
            print("⚠️  Vector store not healthy - check ChromaDB connection")
        
        if ollama_health.get('status') != 'healthy':
            print("⚠️  Ollama not healthy - check Ollama service")
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test 3: Check arXiv dataset
    print("\n3. Checking arXiv dataset...")
    arxiv_path = Path("/home/cmejo/arxiv-dataset/pdf")
    
    if arxiv_path.exists():
        pdf_files = list(arxiv_path.glob("*.pdf"))
        print(f"✅ Found {len(pdf_files)} PDF files in arXiv dataset")
        
        if pdf_files:
            # Test processing a single PDF
            print(f"\n4. Testing PDF processing with: {pdf_files[0].name}")
            try:
                document_data = scientific_pdf_processor.extract_comprehensive_content(str(pdf_files[0]))
                print(f"✅ PDF processed successfully")
                print(f"   - Title: {document_data['metadata'].get('title', 'Unknown')[:100]}...")
                print(f"   - Sections found: {len(document_data['sections'])}")
                print(f"   - Word count: {document_data['statistics']['word_count']}")
                print(f"   - Quality: {document_data['extraction_quality']['assessment']}")
                
                # Test chunk creation
                chunks = scientific_rag_service._create_scientific_chunks(document_data)
                print(f"   - Chunks created: {len(chunks)}")
                
                # Test adding to vector store
                result = await vector_store_service.add_document_chunks(
                    document_data['document_id'],
                    chunks
                )
                print(f"✅ Added {result['chunks_added']} chunks to vector store")
                
            except Exception as e:
                print(f"❌ PDF processing failed: {e}")
                
    else:
        print(f"❌ arXiv dataset not found at {arxiv_path}")
        print("   Please ensure the dataset is available or update the path")
    
    # Test 5: Test semantic search
    print("\n5. Testing semantic search...")
    try:
        # Get collection stats
        stats = await vector_store_service.get_collection_stats()
        print(f"   - Total chunks in collection: {stats.get('total_chunks', 0)}")
        print(f"   - Total documents: {stats.get('document_count', 0)}")
        
        if stats.get('total_chunks', 0) > 0:
            # Test search
            search_results = await vector_store_service.semantic_search(
                "machine learning neural networks",
                n_results=5
            )
            print(f"✅ Search returned {len(search_results)} results")
            
            for i, result in enumerate(search_results[:3]):
                print(f"   Result {i+1}: {result.get('document', '')[:100]}...")
                print(f"   Relevance: {result.get('relevance_score', 0):.3f}")
        else:
            print("⚠️  No documents in collection for search testing")
            
    except Exception as e:
        print(f"❌ Semantic search test failed: {e}")
    
    # Test 6: Test RAG query (if Ollama is available)
    print("\n6. Testing RAG query...")
    try:
        if ollama_service.client and stats.get('total_chunks', 0) > 0:
            query_result = await scientific_rag_service.process_scientific_query(
                "What are the main applications of machine learning?",
                max_sources=3
            )
            
            if not query_result.get('error'):
                print("✅ RAG query successful")
                print(f"   - Query type: {query_result.get('query_type', 'unknown')}")
                print(f"   - Sources used: {query_result.get('context_chunks_used', 0)}")
                print(f"   - Processing time: {query_result.get('processing_time', 0):.2f}s")
                print(f"   - Response preview: {query_result.get('response', '')[:200]}...")
            else:
                print(f"❌ RAG query failed: {query_result.get('response', 'Unknown error')}")
        else:
            print("⚠️  Skipping RAG query test (Ollama not available or no documents)")
            
    except Exception as e:
        print(f"❌ RAG query test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 RAG system test completed!")
    print("\nNext steps:")
    print("1. Start the FastAPI server: python app.py")
    print("2. Process your arXiv dataset: POST /api/rag/process-arxiv-dataset")
    print("3. Query your documents: POST /api/rag/query")
    
    return True

async def test_simple_pdf_processing():
    """Test PDF processing with a simple example"""
    print("\n🔬 Testing simple PDF processing...")
    
    # Create a simple test to verify PDF processing works
    arxiv_path = Path("/home/cmejo/arxiv-dataset/pdf")
    
    if not arxiv_path.exists():
        print(f"❌ arXiv dataset not found at {arxiv_path}")
        return False
    
    pdf_files = list(arxiv_path.glob("*.pdf"))
    if not pdf_files:
        print("❌ No PDF files found")
        return False
    
    # Test with first PDF
    test_pdf = pdf_files[0]
    print(f"Testing with: {test_pdf.name}")
    
    try:
        document_data = scientific_pdf_processor.extract_comprehensive_content(str(test_pdf))
        
        print("✅ PDF processing successful!")
        print(f"Document ID: {document_data['document_id']}")
        print(f"Title: {document_data['metadata'].get('title', 'Unknown')}")
        print(f"Authors: {document_data['metadata'].get('authors', [])}")
        print(f"Sections: {list(document_data['sections'].keys())}")
        print(f"Word count: {document_data['statistics']['word_count']}")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("AI Scholar RAG System Test")
    print("=" * 30)
    
    # First test simple PDF processing
    asyncio.run(test_simple_pdf_processing())
    
    # Then test full system
    asyncio.run(test_rag_system())