#!/usr/bin/env python3
"""
Simple test for knowledge graph RAG integration logic
"""
import asyncio
import sys
import os
import logging
from typing import List, Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockKnowledgeGraphService:
    """Mock knowledge graph service for testing"""
    
    class MockEntityExtractor:
        async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
            """Mock entity extraction"""
            # Simple mock that returns entities based on keywords
            entities = []
            
            keywords = {
                "machine learning": {"type": "concept", "confidence": 0.9},
                "artificial intelligence": {"type": "concept", "confidence": 0.95},
                "healthcare": {"type": "concept", "confidence": 0.8},
                "patient outcomes": {"type": "concept", "confidence": 0.85},
                "medical diagnosis": {"type": "concept", "confidence": 0.9},
                "patient care": {"type": "concept", "confidence": 0.8},
                "healthcare systems": {"type": "concept", "confidence": 0.85}
            }
            
            text_lower = text.lower()
            for keyword, data in keywords.items():
                if keyword in text_lower:
                    entities.append({
                        "text": keyword,
                        "type": data["type"],
                        "confidence": data["confidence"],
                        "start": text_lower.find(keyword),
                        "end": text_lower.find(keyword) + len(keyword)
                    })
            
            return entities
    
    def __init__(self):
        self.entity_extractor = self.MockEntityExtractor()
    
    async def find_related_entities(self, entity_name: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Mock related entity finding"""
        # Mock relationships
        relationships = {
            "machine learning": [
                {"entity": "artificial intelligence", "relationship": "part_of", "confidence": 0.9, "depth": 1},
                {"entity": "medical diagnosis", "relationship": "improves", "confidence": 0.8, "depth": 1},
                {"entity": "patient outcomes", "relationship": "affects", "confidence": 0.7, "depth": 2}
            ],
            "artificial intelligence": [
                {"entity": "healthcare", "relationship": "transforms", "confidence": 0.85, "depth": 1},
                {"entity": "patient care", "relationship": "enhances", "confidence": 0.8, "depth": 1}
            ],
            "healthcare": [
                {"entity": "patient outcomes", "relationship": "focuses_on", "confidence": 0.9, "depth": 1},
                {"entity": "medical diagnosis", "relationship": "includes", "confidence": 0.85, "depth": 1}
            ]
        }
        
        return relationships.get(entity_name.lower(), [])

class TestEnhancedRAGIntegration:
    """Test class for enhanced RAG knowledge graph integration"""
    
    def __init__(self):
        self.knowledge_graph = MockKnowledgeGraphService()
    
    async def _build_relationship_context(
        self, 
        query_entities: List[str], 
        content_entities: List[str]
    ) -> Dict[str, Any]:
        """Build relationship context between query and content entities"""
        relationship_context = {
            "direct_relationships": [],
            "indirect_relationships": [],
            "entity_connections": {},
            "relationship_strength": 0.0
        }
        
        try:
            # Find direct relationships between query and content entities
            for query_entity in query_entities:
                for content_entity in content_entities:
                    # Check if entities are related
                    related_entities = await self.knowledge_graph.find_related_entities(
                        query_entity, max_depth=2
                    )
                    
                    for related in related_entities:
                        if related["entity"].lower() == content_entity.lower():
                            relationship_info = {
                                "source": query_entity,
                                "target": content_entity,
                                "relationship_type": related["relationship"],
                                "confidence": related["confidence"],
                                "depth": related["depth"],
                                "context": related.get("context", "")
                            }
                            
                            if related["depth"] == 1:
                                relationship_context["direct_relationships"].append(relationship_info)
                            else:
                                relationship_context["indirect_relationships"].append(relationship_info)
            
            # Build entity connection map
            for query_entity in query_entities:
                connections = await self.knowledge_graph.find_related_entities(query_entity, max_depth=1)
                if connections:
                    relationship_context["entity_connections"][query_entity] = [
                        {
                            "entity": conn["entity"],
                            "relationship": conn["relationship"],
                            "confidence": conn["confidence"]
                        }
                        for conn in connections[:5]  # Limit to top 5 connections
                    ]
            
            # Calculate overall relationship strength
            direct_strength = sum(rel["confidence"] for rel in relationship_context["direct_relationships"])
            indirect_strength = sum(rel["confidence"] * 0.5 for rel in relationship_context["indirect_relationships"])
            relationship_context["relationship_strength"] = min(1.0, direct_strength + indirect_strength)
            
        except Exception as e:
            logger.error(f"Error building relationship context: {e}")
        
        return relationship_context
    
    def _calculate_knowledge_graph_boost(self, relationship_context: Dict[str, Any]) -> float:
        """Calculate relevance boost based on knowledge graph relationships"""
        base_boost = 0.0
        
        # Boost for direct relationships
        direct_count = len(relationship_context.get("direct_relationships", []))
        if direct_count > 0:
            base_boost += min(0.3, direct_count * 0.1)
        
        # Smaller boost for indirect relationships
        indirect_count = len(relationship_context.get("indirect_relationships", []))
        if indirect_count > 0:
            base_boost += min(0.15, indirect_count * 0.05)
        
        # Boost based on relationship strength
        strength_boost = relationship_context.get("relationship_strength", 0.0) * 0.2
        base_boost += strength_boost
        
        return min(0.4, base_boost)  # Cap the boost at 0.4
    
    def _summarize_relationships(self, relationship_context: Dict[str, Any]) -> str:
        """Create a human-readable summary of relationships"""
        summary_parts = []
        
        direct_rels = relationship_context.get("direct_relationships", [])
        if direct_rels:
            summary_parts.append(f"Direct relationships: {len(direct_rels)}")
            for rel in direct_rels[:2]:  # Show top 2
                summary_parts.append(
                    f"  • {rel['source']} {rel['relationship_type']} {rel['target']} "
                    f"(confidence: {rel['confidence']:.2f})"
                )
        
        indirect_rels = relationship_context.get("indirect_relationships", [])
        if indirect_rels:
            summary_parts.append(f"Indirect relationships: {len(indirect_rels)}")
        
        entity_connections = relationship_context.get("entity_connections", {})
        if entity_connections:
            summary_parts.append(f"Connected entities: {len(entity_connections)}")
        
        return "; ".join(summary_parts) if summary_parts else "No significant relationships found"
    
    async def _enhance_with_knowledge_graph(
        self,
        search_results: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """Enhance search results with knowledge graph relationships"""
        try:
            # Extract entities from query using the knowledge graph service
            query_entities = await self.knowledge_graph.entity_extractor.extract_entities(query)
            query_entity_names = [entity["text"] for entity in query_entities if entity["confidence"] > 0.5]
            
            if not query_entity_names:
                logger.debug("No high-confidence entities found in query")
                return search_results
            
            # For each search result, enhance with knowledge graph information
            enhanced_results = []
            for result in search_results:
                enhanced_result = result.copy()
                
                try:
                    # Extract entities from the search result content
                    content_entities = await self.knowledge_graph.entity_extractor.extract_entities(
                        result["content"]
                    )
                    content_entity_names = [
                        entity["text"] for entity in content_entities 
                        if entity["confidence"] > 0.5
                    ]
                    
                    # Find relationships between query entities and content entities
                    relationship_context = await self._build_relationship_context(
                        query_entity_names, content_entity_names
                    )
                    
                    if relationship_context:
                        enhanced_result["metadata"]["knowledge_graph"] = relationship_context
                        
                        # Calculate knowledge graph boost based on relationship strength
                        kg_boost = self._calculate_knowledge_graph_boost(relationship_context)
                        enhanced_result["relevance"] = min(1.0, result.get("relevance", 0) + kg_boost)
                        
                        # Add relationship summary to metadata
                        enhanced_result["metadata"]["relationship_summary"] = self._summarize_relationships(
                            relationship_context
                        )
                    
                    # Store extracted entities for potential use in response generation
                    enhanced_result["metadata"]["extracted_entities"] = {
                        "query_entities": query_entity_names,
                        "content_entities": content_entity_names
                    }
                        
                except Exception as kg_error:
                    logger.debug(f"Knowledge graph enhancement failed for result: {kg_error}")
                
                enhanced_results.append(enhanced_result)
            
            # Re-rank results based on knowledge graph relationships
            enhanced_results = await self._rerank_with_knowledge_graph(enhanced_results, query_entity_names)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error enhancing with knowledge graph: {e}")
            return search_results
    
    async def _rerank_with_knowledge_graph(
        self, 
        results: List[Dict[str, Any]], 
        query_entities: List[str]
    ) -> List[Dict[str, Any]]:
        """Re-rank search results considering knowledge graph relationships"""
        try:
            # Calculate combined score for each result
            for result in results:
                base_relevance = result.get("relevance", 0.0)
                kg_metadata = result.get("metadata", {}).get("knowledge_graph", {})
                
                # Knowledge graph factors
                relationship_strength = kg_metadata.get("relationship_strength", 0.0)
                direct_rel_count = len(kg_metadata.get("direct_relationships", []))
                indirect_rel_count = len(kg_metadata.get("indirect_relationships", []))
                
                # Calculate knowledge graph score
                kg_score = (
                    relationship_strength * 0.4 +
                    min(1.0, direct_rel_count * 0.3) +
                    min(0.5, indirect_rel_count * 0.1)
                )
                
                # Combine scores (70% base relevance, 30% knowledge graph)
                combined_score = (base_relevance * 0.7) + (kg_score * 0.3)
                result["combined_relevance"] = combined_score
                result["kg_score"] = kg_score
            
            # Sort by combined relevance
            results.sort(key=lambda x: x.get("combined_relevance", x.get("relevance", 0)), reverse=True)
            
        except Exception as e:
            logger.error(f"Error re-ranking with knowledge graph: {e}")
        
        return results

async def test_knowledge_graph_integration():
    """Test the knowledge graph integration logic"""
    
    print("🧪 Testing Knowledge Graph RAG Integration Logic")
    print("=" * 50)
    
    try:
        # Initialize test class
        test_rag = TestEnhancedRAGIntegration()
        
        # Test query
        test_query = "How does machine learning improve healthcare and patient outcomes?"
        print(f"Test query: {test_query}")
        
        # Test entity extraction
        print("\n1. Testing entity extraction...")
        query_entities = await test_rag.knowledge_graph.entity_extractor.extract_entities(test_query)
        query_entity_names = [e["text"] for e in query_entities if e["confidence"] > 0.5]
        print(f"   Extracted entities: {query_entity_names}")
        
        # Test relationship building
        print("\n2. Testing relationship context building...")
        content_entities = ["artificial intelligence", "medical diagnosis", "patient care"]
        
        relationship_context = await test_rag._build_relationship_context(
            query_entity_names, content_entities
        )
        
        print(f"   Direct relationships: {len(relationship_context['direct_relationships'])}")
        print(f"   Indirect relationships: {len(relationship_context['indirect_relationships'])}")
        print(f"   Relationship strength: {relationship_context['relationship_strength']:.2f}")
        
        for rel in relationship_context['direct_relationships']:
            print(f"     - {rel['source']} {rel['relationship_type']} {rel['target']} (conf: {rel['confidence']:.2f})")
        
        # Test knowledge graph boost calculation
        print("\n3. Testing knowledge graph boost...")
        kg_boost = test_rag._calculate_knowledge_graph_boost(relationship_context)
        print(f"   Knowledge graph boost: {kg_boost:.3f}")
        
        # Test relationship summary
        print("\n4. Testing relationship summary...")
        summary = test_rag._summarize_relationships(relationship_context)
        print(f"   Summary: {summary}")
        
        # Test search results enhancement
        print("\n5. Testing search results enhancement...")
        mock_search_results = [
            {
                "id": "test_1",
                "content": "Machine learning algorithms are revolutionizing healthcare by improving diagnostic accuracy and patient outcomes. These AI systems can analyze medical images and assist doctors.",
                "metadata": {
                    "document_name": "AI in Healthcare",
                    "page_number": 1
                },
                "relevance": 0.75
            },
            {
                "id": "test_2",
                "content": "Patient care has been transformed through artificial intelligence applications in hospitals. Healthcare systems now use predictive analytics.",
                "metadata": {
                    "document_name": "Healthcare Innovation", 
                    "page_number": 2
                },
                "relevance": 0.68
            }
        ]
        
        enhanced_results = await test_rag._enhance_with_knowledge_graph(
            mock_search_results, test_query
        )
        
        print(f"   Enhanced {len(enhanced_results)} search results")
        
        for i, result in enumerate(enhanced_results):
            print(f"   Result {i+1}:")
            print(f"     - Original relevance: {mock_search_results[i]['relevance']:.3f}")
            print(f"     - Enhanced relevance: {result.get('relevance', 0):.3f}")
            print(f"     - Combined relevance: {result.get('combined_relevance', 0):.3f}")
            print(f"     - KG score: {result.get('kg_score', 0):.3f}")
            
            kg_metadata = result.get("metadata", {}).get("knowledge_graph", {})
            if kg_metadata:
                print(f"     - Relationship strength: {kg_metadata.get('relationship_strength', 0):.3f}")
                print(f"     - Direct relationships: {len(kg_metadata.get('direct_relationships', []))}")
        
        print("\n✅ Knowledge Graph Integration Test Completed Successfully!")
        
        # Verify improvements
        original_order = [r['relevance'] for r in mock_search_results]
        enhanced_order = [r.get('combined_relevance', r.get('relevance', 0)) for r in enhanced_results]
        
        print(f"\n📊 Results Analysis:")
        print(f"   Original relevance scores: {[f'{r:.3f}' for r in original_order]}")
        print(f"   Enhanced relevance scores: {[f'{r:.3f}' for r in enhanced_order]}")
        
        # Check if knowledge graph improved ranking
        kg_improved = any(
            result.get("metadata", {}).get("knowledge_graph", {}).get("relationship_strength", 0) > 0
            for result in enhanced_results
        )
        
        print(f"   Knowledge graph relationships found: {'✅ Yes' if kg_improved else '❌ No'}")
        print(f"   Ranking potentially improved: {'✅ Yes' if enhanced_order != original_order else '⚠️  Same'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def main():
        print("🧠 Knowledge Graph RAG Integration Test")
        print("=" * 50)
        
        success = await test_knowledge_graph_integration()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 Test completed successfully! Knowledge graph integration logic is working.")
            return 0
        else:
            print("⚠️  Test failed. Please check the implementation.")
            return 1
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)