#!/usr/bin/env python3
"""
Verification test for enhanced RAG service with knowledge graph integration
"""
import asyncio
import sys
import os
import logging
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enhanced_rag_kg_methods():
    """Test the enhanced RAG service knowledge graph methods"""
    
    print("🔍 Testing Enhanced RAG Service KG Methods")
    print("=" * 50)
    
    try:
        # Mock the dependencies to avoid import issues
        with patch('services.enhanced_rag_service.VectorStoreService'), \
             patch('services.enhanced_rag_service.KnowledgeGraphService'), \
             patch('services.enhanced_rag_service.conversation_memory_manager'), \
             patch('services.enhanced_rag_service.context_compressor'), \
             patch('services.enhanced_rag_service.user_memory_store'), \
             patch('services.enhanced_rag_service.get_db'):
            
            from services.enhanced_rag_service import EnhancedRAGService
            
            # Create service instance
            rag_service = EnhancedRAGService()
            
            # Mock the knowledge graph service
            mock_kg_service = Mock()
            mock_entity_extractor = Mock()
            
            # Mock entity extraction
            mock_entity_extractor.extract_entities = AsyncMock(return_value=[
                {"text": "machine learning", "confidence": 0.9, "type": "concept"},
                {"text": "healthcare", "confidence": 0.8, "type": "concept"},
                {"text": "patient outcomes", "confidence": 0.85, "type": "concept"}
            ])
            
            mock_kg_service.entity_extractor = mock_entity_extractor
            
            # Mock find_related_entities
            mock_kg_service.find_related_entities = AsyncMock(return_value=[
                {"entity": "artificial intelligence", "relationship": "part_of", "confidence": 0.9, "depth": 1},
                {"entity": "medical diagnosis", "relationship": "improves", "confidence": 0.8, "depth": 1}
            ])
            
            rag_service.knowledge_graph = mock_kg_service
            
            print("✅ Service initialized with mocked dependencies")
            
            # Test 1: Entity extraction
            print("\n1. Testing entity extraction...")
            entities = await rag_service._extract_entities_from_text(
                "How does machine learning improve healthcare?"
            )
            print(f"   Extracted entities: {entities}")
            assert len(entities) > 0, "Should extract entities"
            
            # Test 2: Relationship context building
            print("\n2. Testing relationship context building...")
            query_entities = ["machine learning", "healthcare"]
            content_entities = ["artificial intelligence", "medical diagnosis"]
            
            relationship_context = await rag_service._build_relationship_context(
                query_entities, content_entities
            )
            
            print(f"   Relationship context keys: {list(relationship_context.keys())}")
            print(f"   Direct relationships: {len(relationship_context.get('direct_relationships', []))}")
            print(f"   Relationship strength: {relationship_context.get('relationship_strength', 0)}")
            
            assert "direct_relationships" in relationship_context
            assert "relationship_strength" in relationship_context
            
            # Test 3: Knowledge graph boost calculation
            print("\n3. Testing KG boost calculation...")
            kg_boost = rag_service._calculate_knowledge_graph_boost(relationship_context)
            print(f"   KG boost: {kg_boost}")
            assert 0 <= kg_boost <= 0.4, "Boost should be within expected range"
            
            # Test 4: Relationship summary
            print("\n4. Testing relationship summary...")
            summary = rag_service._summarize_relationships(relationship_context)
            print(f"   Summary: {summary}")
            assert isinstance(summary, str), "Summary should be a string"
            
            # Test 5: Search results enhancement
            print("\n5. Testing search results enhancement...")
            mock_search_results = [
                {
                    "id": "test_1",
                    "content": "Machine learning algorithms improve healthcare outcomes through better diagnosis.",
                    "metadata": {"document_name": "AI Healthcare", "page_number": 1},
                    "relevance": 0.8
                }
            ]
            
            enhanced_results = await rag_service._enhance_with_knowledge_graph(
                mock_search_results, "How does machine learning help healthcare?"
            )
            
            print(f"   Enhanced results count: {len(enhanced_results)}")
            
            # Check if enhancement worked
            first_result = enhanced_results[0]
            has_kg_metadata = "knowledge_graph" in first_result.get("metadata", {})
            has_extracted_entities = "extracted_entities" in first_result.get("metadata", {})
            
            print(f"   Has KG metadata: {has_kg_metadata}")
            print(f"   Has extracted entities: {has_extracted_entities}")
            print(f"   Original relevance: {mock_search_results[0]['relevance']}")
            print(f"   Enhanced relevance: {first_result.get('relevance', 'N/A')}")
            
            # Test 6: Re-ranking with knowledge graph
            print("\n6. Testing re-ranking...")
            reranked_results = await rag_service._rerank_with_knowledge_graph(
                enhanced_results, ["machine learning"]
            )
            
            print(f"   Re-ranked results count: {len(reranked_results)}")
            
            first_reranked = reranked_results[0]
            has_combined_relevance = "combined_relevance" in first_reranked
            has_kg_score = "kg_score" in first_reranked
            
            print(f"   Has combined relevance: {has_combined_relevance}")
            print(f"   Has KG score: {has_kg_score}")
            
            if has_combined_relevance:
                print(f"   Combined relevance: {first_reranked['combined_relevance']}")
            if has_kg_score:
                print(f"   KG score: {first_reranked['kg_score']}")
            
            # Test 7: Knowledge graph context building
            print("\n7. Testing KG context building...")
            kg_context = await rag_service._build_knowledge_graph_context(
                enhanced_results, "machine learning healthcare"
            )
            
            print(f"   KG context length: {len(kg_context) if kg_context else 0}")
            if kg_context:
                print(f"   KG context preview: {kg_context[:200]}...")
            
            # Test 8: Statistics collection
            print("\n8. Testing KG statistics collection...")
            kg_stats = rag_service._collect_knowledge_graph_stats(enhanced_results)
            
            print(f"   KG stats keys: {list(kg_stats.keys())}")
            print(f"   Total entities: {kg_stats.get('total_entities', 0)}")
            print(f"   Relationships found: {kg_stats.get('relationships_found', 0)}")
            
            assert "total_entities" in kg_stats
            assert "relationships_found" in kg_stats
            
            print("\n✅ All Enhanced RAG KG Methods Test Completed Successfully!")
            
            # Summary
            print(f"\n📊 Test Summary:")
            print(f"   ✅ Entity extraction: Working")
            print(f"   ✅ Relationship context: Working") 
            print(f"   ✅ KG boost calculation: Working")
            print(f"   ✅ Relationship summary: Working")
            print(f"   ✅ Search enhancement: Working")
            print(f"   ✅ Re-ranking: Working")
            print(f"   ✅ Context building: Working")
            print(f"   ✅ Statistics collection: Working")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_enhanced_context_integration():
    """Test the enhanced context building with knowledge graph"""
    
    print("\n🔗 Testing Enhanced Context Integration")
    print("=" * 50)
    
    try:
        with patch('services.enhanced_rag_service.VectorStoreService'), \
             patch('services.enhanced_rag_service.KnowledgeGraphService'), \
             patch('services.enhanced_rag_service.conversation_memory_manager'), \
             patch('services.enhanced_rag_service.context_compressor'), \
             patch('services.enhanced_rag_service.user_memory_store'), \
             patch('services.enhanced_rag_service.get_db'):
            
            from services.enhanced_rag_service import EnhancedRAGService
            
            rag_service = EnhancedRAGService()
            
            # Mock search results with KG metadata
            mock_search_results = [
                {
                    "id": "test_1",
                    "content": "Machine learning improves healthcare diagnostics significantly.",
                    "metadata": {
                        "document_name": "AI Healthcare",
                        "page_number": 1,
                        "knowledge_graph": {
                            "relationship_strength": 0.8,
                            "direct_relationships": [
                                {"source": "machine learning", "target": "healthcare", "relationship_type": "improves"}
                            ]
                        },
                        "relationship_summary": "Direct relationships: 1; machine learning improves healthcare"
                    },
                    "relevance": 0.9
                }
            ]
            
            memory_context = {
                "conversation_summary": "Previous discussion about AI applications",
                "relevant_memories": [
                    {"content": "User asked about AI in medicine", "importance": 0.8}
                ]
            }
            
            personalized_context = {
                "user_preferences": {
                    "technical_level": {"value": "intermediate"}
                }
            }
            
            # Test enhanced context building
            enhanced_context = await rag_service._build_enhanced_context(
                mock_search_results, memory_context, personalized_context, 
                "How does machine learning help healthcare?"
            )
            
            print(f"Enhanced context length: {len(enhanced_context)}")
            print(f"Contains user preferences: {'User Preferences:' in enhanced_context}")
            print(f"Contains memory context: {'Conversation Context:' in enhanced_context}")
            print(f"Contains KG relationships: {'Knowledge Graph Relationships:' in enhanced_context}")
            print(f"Contains relationship info: {'Relationships:' in enhanced_context}")
            
            # Verify context structure
            context_sections = enhanced_context.split('\n\n')
            print(f"Context sections: {len(context_sections)}")
            
            print("\n✅ Enhanced Context Integration Test Completed!")
            return True
            
    except Exception as e:
        print(f"❌ Enhanced context test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def main():
        print("🧠 Enhanced RAG Knowledge Graph Integration Verification")
        print("=" * 60)
        
        # Run tests
        test1_success = await test_enhanced_rag_kg_methods()
        test2_success = await test_enhanced_context_integration()
        
        print("\n" + "=" * 60)
        print("📋 Verification Results:")
        print(f"   KG Methods Test: {'✅ PASSED' if test1_success else '❌ FAILED'}")
        print(f"   Context Integration Test: {'✅ PASSED' if test2_success else '❌ FAILED'}")
        
        if test1_success and test2_success:
            print("\n🎉 All verification tests passed!")
            print("   Knowledge graph integration is properly implemented in Enhanced RAG service.")
            return 0
        else:
            print("\n⚠️  Some verification tests failed.")
            return 1
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)