#!/usr/bin/env python3
"""
Final RAG system test
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent))

async def test_rag_system():
    """Test the complete RAG system"""
    
    print("🚀 AI Scholar RAG System - Final Test")
    print("=" * 50)
    
    # Test 1: Vector Store Service
    print("\n1. Testing Vector Store Service...")
    try:
        from services.vector_store_service import VectorStoreService
        
        # Create instance with correct config
        vector_store = VectorStoreService(chroma_host="localhost", chroma_port=8082)
        await vector_store.initialize()
        
        health = await vector_store.health_check()
        print(f"   ✅ Vector Store: {health['status']}")
        print(f"   📊 Documents: {health['total_documents']}")
        
    except Exception as e:
        print(f"   ❌ Vector Store Error: {e}")
        return False
    
    # Test 2: Ollama Service
    print("\n2. Testing Ollama Service...")
    try:
        from services.ollama_service import OllamaService
        
        # Create instance with correct config
        ollama = OllamaService(base_url="http://localhost:11435")
        await ollama.initialize()
        
        health = await ollama.health_check()
        print(f"   ✅ Ollama: {health['status']}")
        print(f"   🤖 Models: {health['models_available']}")
        
    except Exception as e:
        print(f"   ❌ Ollama Error: {e}")
        return False
    
    # Test 3: Simple search (if we have documents)
    if health['total_documents'] > 0:
        print("\n3. Testing Document Search...")
        try:
            # Simple query test using ChromaDB directly
            results = vector_store.collection.query(
                query_texts=["machine learning"],
                n_results=3
            )
            
            if results['documents'] and len(results['documents'][0]) > 0:
                print(f"   ✅ Found {len(results['documents'][0])} results")
                for i, doc in enumerate(results['documents'][0][:2]):
                    print(f"   {i+1}. {doc[:100]}...")
            else:
                print("   ℹ️ No results found (collection may be empty)")
                
        except Exception as e:
            print(f"   ❌ Search Error: {e}")
    
    print("\n🎉 RAG System Test Complete!")
    print("\nNext Steps:")
    print("1. Visit http://localhost:3003/react-rag-app.html")
    print("2. Click the red 'Login' button")
    print("3. Test queries in the RAG interface")
    print("4. Process more PDFs with: python backend/process_arxiv_dataset.py")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_rag_system())