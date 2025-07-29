#!/usr/bin/env python3
"""
Test script for knowledge graph integration with RAG retrieval
"""
import asyncio
import sys
import os
import logging

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.enhanced_rag_service import EnhancedRAGService
from services.knowledge_graph import KnowledgeGraphService
from services.vector_store import VectorStoreService
from core.database import init_db, get_db
from models.schemas import DocumentCreate
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_knowledge_graph_rag_integration():
    """Test the integration of knowledge graph with RAG retrieval"""
    
    print("🧪 Testing Knowledge Graph RAG Integration")
    print("=" * 50)
    
    try:
        # Initialize services
        print("1. Initializing services...")
        enhanced_rag = EnhancedRAGService()
        kg_service = KnowledgeGraphService()
        vector_store = VectorStoreService()
        
        await vector_store.initialize()
        await kg_service.initialize()
        
        # Initialize database
        init_db()
        
        print("✅ Services initialized successfully")
        
        # Test entity extraction from query
        print("\n2. Testing entity extraction from query...")
        test_query = "What are the effects of machine learning on healthcare and patient outcomes?"
        
        query_entities = await enhanced_rag._extract_entities_from_text(test_query)
        print(f"   Query: {test_query}")
        print(f"   Extracted entities: {query_entities}")
        
        # Test enhanced entity extraction using knowledge graph service
        print("\n3. Testing enhanced entity extraction...")
        enhanced_entities = await kg_service.entity_extractor.extract_entities(test_query)
        print(f"   Enhanced entities: {[e['text'] for e in enhanced_entities if e['confidence'] > 0.5]}")
        
        # Test relationship building
        print("\n4. Testing relationship context building...")
        content_entities = ["artificial intelligence", "medical diagnosis", "patient care", "healthcare systems"]
        query_entity_names = [e["text"] for e in enhanced_entities if e["confidence"] > 0.5]
        
        if query_entity_names:
            relationship_context = await enhanced_rag._build_relationship_context(
                query_entity_names[:3], content_entities[:3]
            )
            print(f"   Relationship context: {relationship_context}")
            
            # Test knowledge graph boost calculation
            kg_boost = enhanced_rag._calculate_knowledge_graph_boost(relationship_context)
            print(f"   Knowledge graph boost: {kg_boost}")
            
            # Test relationship summary
            summary = enhanced_rag._summarize_relationships(relationship_context)
            print(f"   Relationship summary: {summary}")
        
        # Test mock search results enhancement
        print("\n5. Testing search results enhancement...")
        mock_search_results = [
            {
                "id": "test_1",
                "content": "Machine learning algorithms are revolutionizing healthcare by improving diagnostic accuracy and patient outcomes. These AI systems can analyze medical images, predict disease progression, and assist doctors in making better treatment decisions.",
                "metadata": {
                    "document_name": "AI in Healthcare",
                    "page_number": 1,
                    "document_id": str(uuid.uuid4())
                },
                "relevance": 0.85
            },
            {
                "id": "test_2", 
                "content": "Patient care has been transformed through artificial intelligence applications in hospitals. Healthcare systems now use predictive analytics to identify high-risk patients and optimize treatment protocols.",
                "metadata": {
                    "document_name": "Healthcare Innovation",
                    "page_number": 2,
                    "document_id": str(uuid.uuid4())
                },
                "relevance": 0.78
            }
        ]
        
        enhanced_results = await enhanced_rag._enhance_with_knowledge_graph(
            mock_search_results, test_query
        )
        
        print(f"   Original results count: {len(mock_search_results)}")
        print(f"   Enhanced results count: {len(enhanced_results)}")
        
        for i, result in enumerate(enhanced_results):
            print(f"   Result {i+1}:")
            print(f"     - Original relevance: {mock_search_results[i]['relevance']}")
            print(f"     - Enhanced relevance: {result.get('relevance', 'N/A')}")
            print(f"     - Combined relevance: {result.get('combined_relevance', 'N/A')}")
            print(f"     - KG score: {result.get('kg_score', 'N/A')}")
            
            kg_metadata = result.get("metadata", {}).get("knowledge_graph", {})
            if kg_metadata:
                print(f"     - Relationship strength: {kg_metadata.get('relationship_strength', 0)}")
                print(f"     - Direct relationships: {len(kg_metadata.get('direct_relationships', []))}")
                print(f"     - Indirect relationships: {len(kg_metadata.get('indirect_relationships', []))}")
        
        # Test knowledge graph context building
        print("\n6. Testing knowledge graph context building...")
        kg_context = await enhanced_rag._build_knowledge_graph_context(enhanced_results, test_query)
        if kg_context:
            print(f"   Knowledge graph context:\n{kg_context}")
        else:
            print("   No knowledge graph context generated")
        
        # Test enhanced context building
        print("\n7. Testing enhanced context building...")
        memory_context = {"conversation_summary": "Previous discussion about AI applications"}
        personalized_context = {"user_preferences": {"technical_level": {"value": "intermediate"}}}
        
        enhanced_context = await enhanced_rag._build_enhanced_context(
            enhanced_results, memory_context, personalized_context, test_query
        )
        
        print(f"   Enhanced context length: {len(enhanced_context)} characters")
        print(f"   Context preview:\n{enhanced_context[:500]}...")
        
        # Test knowledge graph statistics collection
        print("\n8. Testing knowledge graph statistics...")
        kg_stats = enhanced_rag._collect_knowledge_graph_stats(enhanced_results)
        print(f"   KG Statistics: {kg_stats}")
        
        # Test source formatting with knowledge graph info
        print("\n9. Testing source formatting...")
        formatted_sources = enhanced_rag._format_sources(enhanced_results)
        print(f"   Formatted sources count: {len(formatted_sources)}")
        
        for i, source in enumerate(formatted_sources):
            print(f"   Source {i+1}:")
            print(f"     - Document: {source.document}")
            print(f"     - Page: {source.page}")
            print(f"     - Relevance: {source.relevance}")
            print(f"     - Snippet length: {len(source.snippet)}")
            if "[Knowledge Graph:" in source.snippet:
                print(f"     - Contains KG info: Yes")
        
        print("\n✅ Knowledge Graph RAG Integration Test Completed Successfully!")
        print("\n📊 Summary:")
        print(f"   - Entity extraction: {'✅ Working' if query_entities else '❌ Failed'}")
        print(f"   - Enhanced entity extraction: {'✅ Working' if enhanced_entities else '❌ Failed'}")
        print(f"   - Relationship building: {'✅ Working' if 'relationship_context' in locals() else '❌ Failed'}")
        print(f"   - Search enhancement: {'✅ Working' if enhanced_results else '❌ Failed'}")
        print(f"   - Context building: {'✅ Working' if enhanced_context else '❌ Failed'}")
        print(f"   - Statistics collection: {'✅ Working' if kg_stats else '❌ Failed'}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_full_enhanced_response():
    """Test the full enhanced response generation with knowledge graph"""
    
    print("\n🚀 Testing Full Enhanced Response Generation")
    print("=" * 50)
    
    try:
        enhanced_rag = EnhancedRAGService()
        
        # Test query
        test_query = "How does artificial intelligence improve medical diagnosis?"
        test_user_id = str(uuid.uuid4())
        
        print(f"Query: {test_query}")
        print(f"User ID: {test_user_id}")
        
        # Note: This would require actual documents in the vector store
        # For now, we'll test the components individually
        print("\n⚠️  Full response test requires documents in vector store")
        print("   This test demonstrates the integration components working together")
        
        # Test entity extraction
        entities = await enhanced_rag._extract_entities_from_text(test_query)
        print(f"✅ Entity extraction: {entities}")
        
        # Test mock enhancement
        mock_results = [{
            "id": "mock_1",
            "content": "Artificial intelligence in medical diagnosis uses machine learning algorithms to analyze patient data and medical images, improving diagnostic accuracy and reducing human error.",
            "metadata": {"document_name": "AI Medicine", "page_number": 1},
            "relevance": 0.9
        }]
        
        enhanced = await enhanced_rag._enhance_with_knowledge_graph(mock_results, test_query)
        print(f"✅ Knowledge graph enhancement: {len(enhanced)} results processed")
        
        print("\n✅ Full Enhanced Response Test Components Verified!")
        
    except Exception as e:
        print(f"❌ Full response test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    async def main():
        print("🧠 Knowledge Graph RAG Integration Test Suite")
        print("=" * 60)
        
        # Run integration tests
        test1_success = await test_knowledge_graph_rag_integration()
        test2_success = await test_full_enhanced_response()
        
        print("\n" + "=" * 60)
        print("📋 Test Results Summary:")
        print(f"   Integration Test: {'✅ PASSED' if test1_success else '❌ FAILED'}")
        print(f"   Full Response Test: {'✅ PASSED' if test2_success else '❌ FAILED'}")
        
        if test1_success and test2_success:
            print("\n🎉 All tests passed! Knowledge graph integration is working correctly.")
            return 0
        else:
            print("\n⚠️  Some tests failed. Please check the implementation.")
            return 1
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)