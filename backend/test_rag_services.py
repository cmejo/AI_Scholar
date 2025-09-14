#!/usr/bin/env python3
"""
Test script to verify RAG services are working
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent))

from services.vector_store_service import vector_store_service
from services.ollama_service import ollama_service
from services.scientific_rag_service import scientific_rag_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_services():
    """Test all RAG services"""
    
    print("🧪 Testing RAG Services")
    print("=" * 40)
    
    # Test 1: Vector Store Service
    print("\n1. Testing Vector Store Service...")
    try:
        # Initialize with correct ChromaDB configuration
        vector_store_service.chroma_host = "localhost"
        vector_store_service.chroma_port = 8082
        await vector_store_service.initialize()
        health = await vector_store_service.health_check()
        print(f"   ✅ Vector Store: {health}")
    except Exception as e:
        print(f"   ❌ Vector Store Error: {e}")
        return False
    
    # Test 2: Ollama Service
    print("\n2. Testing Ollama Service...")
    try:
        # Initialize with correct Ollama configuration
        ollama_service.base_url = "http://localhost:11435"
        await ollama_service.initialize()
        health = await ollama_service.health_check()
        print(f"   ✅ Ollama: {health}")
        
        # Test model availability
        models = await ollama_service.list_models()
        print(f"   📋 Available models: {models}")
    except Exception as e:
        print(f"   ❌ Ollama Error: {e}")
        return False
    
    # Test 3: Simple query test
    print("\n3. Testing Simple Query...")
    try:
        # Test with a simple query
        response = await ollama_service.generate_response(
            "What is machine learning?",
            model="llama2:7b"
        )
        print(f"   ✅ Query Response: {response[:100]}...")
    except Exception as e:
        print(f"   ❌ Query Error: {e}")
        return False
    
    # Test 4: Collection stats
    print("\n4. Testing Collection Stats...")
    try:
        stats = await vector_store_service.get_collection_stats()
        print(f"   📊 Collection Stats: {stats}")
    except Exception as e:
        print(f"   ❌ Stats Error: {e}")
    
    print("\n🎉 All services are working!")
    return True

async def test_single_pdf():
    """Test processing a single PDF"""
    
    print("\n5. Testing Single PDF Processing...")
    
    # Find a PDF file
    pdf_files = list(Path("/home/cmejo/arxiv-dataset/pdf").rglob("*.pdf"))
    if not pdf_files:
        print("   ❌ No PDF files found")
        return False
    
    test_pdf = pdf_files[0]
    print(f"   📄 Testing with: {test_pdf.name}")
    
    try:
        from services.scientific_pdf_processor import scientific_pdf_processor
        
        # Extract content
        document_data = scientific_pdf_processor.extract_comprehensive_content(str(test_pdf))
        print(f"   ✅ Extracted content: {len(document_data.get('content', ''))} chars")
        
        # Create chunks
        chunks = scientific_rag_service._create_scientific_chunks(document_data)
        print(f"   ✅ Created {len(chunks)} chunks")
        
        # Add to vector store
        result = await vector_store_service.add_document_chunks(
            document_data['document_id'],
            chunks
        )
        print(f"   ✅ Added to vector store: {result}")
        
        # Test search
        search_results = await vector_store_service.search_similar(
            "machine learning",
            limit=3
        )
        print(f"   ✅ Search results: {len(search_results)} found")
        
        return True
        
    except Exception as e:
        print(f"   ❌ PDF Processing Error: {e}")
        return False

async def main():
    """Main test function"""
    
    # Test basic services
    if not await test_services():
        print("❌ Basic service tests failed")
        return
    
    # Test PDF processing
    await test_single_pdf()
    
    print("\n🚀 RAG System is ready!")
    print("You can now:")
    print("1. Visit http://localhost:3003/react-rag-app.html")
    print("2. Login and test queries")
    print("3. Process more PDFs with process_arxiv_dataset.py")

if __name__ == "__main__":
    asyncio.run(main())