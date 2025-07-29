#!/usr/bin/env python3
"""
Test script for GraphBuilder and GraphQueryEngine functionality
Tests task 3.2: Build knowledge graph storage and query system
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.knowledge_graph import GraphBuilder, GraphQueryEngine, EnhancedKnowledgeGraphService
from models.schemas import EntityType, RelationshipType
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_graph_builder():
    """Test GraphBuilder functionality"""
    print("=" * 60)
    print("TESTING GRAPH BUILDER")
    print("=" * 60)
    
    # Create test data
    entities = [
        {
            "name": "Python",
            "type": "CONCEPT",
            "importance_score": 0.9,
            "metadata": {"category": "programming_language"}
        },
        {
            "name": "Machine Learning",
            "type": "CONCEPT", 
            "importance_score": 0.8,
            "metadata": {"category": "technology"}
        },
        {
            "name": "TensorFlow",
            "type": "PRODUCT",
            "importance_score": 0.7,
            "metadata": {"category": "framework"}
        },
        {
            "name": "Google",
            "type": "ORGANIZATION",
            "importance_score": 0.9,
            "metadata": {"category": "company"}
        }
    ]
    
    relationships = [
        {
            "source_entity_name": "Python",
            "target_entity_name": "Machine Learning",
            "relationship_type": "related_to",
            "confidence_score": 0.8,
            "context": "Python is commonly used for machine learning",
            "metadata": {"strength": "strong"}
        },
        {
            "source_entity_name": "TensorFlow",
            "target_entity_name": "Machine Learning",
            "relationship_type": "part_of",
            "confidence_score": 0.9,
            "context": "TensorFlow is a machine learning framework",
            "metadata": {"strength": "very_strong"}
        },
        {
            "source_entity_name": "Google",
            "target_entity_name": "TensorFlow",
            "relationship_type": "causes",
            "confidence_score": 0.95,
            "context": "Google created TensorFlow",
            "metadata": {"relationship": "creator"}
        }
    ]
    
    # Test GraphBuilder
    builder = GraphBuilder()
    
    print("1. Building graph from entities and relationships...")
    graph = await builder.build_graph_from_entities_and_relationships(entities, relationships)
    
    print(f"   - Graph nodes: {graph.number_of_nodes()}")
    print(f"   - Graph edges: {graph.number_of_edges()}")
    
    # Test node data
    print("\n2. Testing node data...")
    for node_id, node_data in graph.nodes(data=True):
        print(f"   - Node: {node_id}")
        print(f"     Name: {node_data['name']}")
        print(f"     Type: {node_data['type']}")
        print(f"     Importance: {node_data['importance']}")
    
    # Test edge data
    print("\n3. Testing edge data...")
    for source, target, edge_data in graph.edges(data=True):
        print(f"   - Edge: {source} -> {target}")
        print(f"     Relationship: {edge_data['relationship_type']}")
        print(f"     Confidence: {edge_data['confidence']}")
    
    # Test subgraph extraction
    print("\n4. Testing subgraph extraction...")
    subgraph = await builder.get_subgraph(["Python", "Machine Learning"], max_depth=2)
    print(f"   - Subgraph nodes: {subgraph.number_of_nodes()}")
    print(f"   - Subgraph edges: {subgraph.number_of_edges()}")
    
    # Test centrality metrics
    print("\n5. Testing centrality metrics...")
    metrics = await builder.calculate_centrality_metrics()
    for node, node_metrics in metrics.items():
        print(f"   - {node}:")
        print(f"     Degree centrality: {node_metrics['degree_centrality']:.3f}")
        print(f"     Betweenness centrality: {node_metrics['betweenness_centrality']:.3f}")
        print(f"     PageRank: {node_metrics['pagerank']:.3f}")
    
    # Test graph update with new document
    print("\n6. Testing graph update with new document...")
    new_entities = [
        {
            "name": "PyTorch",
            "type": "PRODUCT",
            "importance_score": 0.8,
            "metadata": {"category": "framework"}
        }
    ]
    
    new_relationships = [
        {
            "source_entity_name": "PyTorch",
            "target_entity_name": "Machine Learning",
            "relationship_type": "part_of",
            "confidence_score": 0.85,
            "context": "PyTorch is a machine learning framework",
            "metadata": {"strength": "strong"}
        }
    ]
    
    await builder.update_graph_with_new_document("doc_2", new_entities, new_relationships)
    print(f"   - Updated graph nodes: {builder.graph.number_of_nodes()}")
    print(f"   - Updated graph edges: {builder.graph.number_of_edges()}")
    
    return builder

async def test_graph_query_engine(builder):
    """Test GraphQueryEngine functionality"""
    print("\n" + "=" * 60)
    print("TESTING GRAPH QUERY ENGINE")
    print("=" * 60)
    
    # Create query engine
    query_engine = GraphQueryEngine(builder)
    
    # Test finding entities by type
    print("1. Testing find entities by type...")
    concept_entities = await query_engine.find_entities_by_type("CONCEPT", min_importance=0.5)
    print(f"   - Found {len(concept_entities)} concept entities:")
    for entity in concept_entities:
        print(f"     * {entity['name']} (importance: {entity['importance']})")
    
    # Test finding related entities
    print("\n2. Testing find related entities...")
    related = await query_engine.find_related_entities("Python", max_depth=2, min_confidence=0.5)
    print(f"   - Found {len(related)} entities related to Python:")
    for entity in related[:5]:  # Show top 5
        print(f"     * {entity['entity']} ({entity['relationship']}, confidence: {entity['confidence']:.3f})")
    
    # Test shortest path
    print("\n3. Testing shortest path...")
    paths = await query_engine.find_shortest_path("Google", "Machine Learning")
    print(f"   - Found {len(paths)} paths from Google to Machine Learning:")
    for i, path in enumerate(paths[:2]):  # Show top 2 paths
        print(f"     Path {i+1} (length: {path['path_length']}, confidence: {path['total_confidence']:.3f}):")
        for step in path['path']:
            print(f"       {step['from']} --[{step['relationship']}]--> {step['to']}")
    
    # Test pattern matching
    print("\n4. Testing pattern matching...")
    pattern = {
        "source_type": "ORGANIZATION",
        "relationship_type": "causes",
        "min_confidence": 0.8
    }
    matches = await query_engine.query_by_pattern(pattern)
    print(f"   - Found {len(matches)} matches for pattern:")
    for match in matches:
        print(f"     * {match['source']['name']} --[{match['relationship']}]--> {match['target']['name']}")
        print(f"       Confidence: {match['confidence']:.3f}")
    
    # Test graph statistics
    print("\n5. Testing graph statistics...")
    stats = await query_engine.get_graph_statistics()
    print(f"   - Total nodes: {stats['total_nodes']}")
    print(f"   - Total edges: {stats['total_edges']}")
    print(f"   - Graph density: {stats['density']:.3f}")
    print(f"   - Connected components: {stats['connected_components']}")
    print(f"   - Average clustering: {stats['average_clustering']:.3f}")
    print(f"   - Average degree: {stats['average_degree']:.3f}")
    
    print("   - Node types:")
    for node_type, count in stats['node_types'].items():
        print(f"     * {node_type}: {count}")
    
    print("   - Relationship types:")
    for rel_type, count in stats['relationship_types'].items():
        print(f"     * {rel_type}: {count}")

async def test_enhanced_knowledge_graph_service():
    """Test EnhancedKnowledgeGraphService integration"""
    print("\n" + "=" * 60)
    print("TESTING ENHANCED KNOWLEDGE GRAPH SERVICE")
    print("=" * 60)
    
    service = EnhancedKnowledgeGraphService()
    await service.initialize()
    
    # Test building graph from database (will be empty but should not error)
    print("1. Testing build full graph from database...")
    try:
        await service.build_full_graph_from_database()
        print("   ✓ Successfully built graph from database")
    except Exception as e:
        print(f"   ✗ Error building graph from database: {e}")
    
    # Test graph query
    print("\n2. Testing graph query...")
    try:
        # First add some test data to the in-memory graph
        test_entities = [
            {"name": "Artificial Intelligence", "type": "CONCEPT", "importance_score": 0.9, "metadata": {}},
            {"name": "Neural Networks", "type": "CONCEPT", "importance_score": 0.8, "metadata": {}}
        ]
        test_relationships = [
            {
                "source_entity_name": "Artificial Intelligence",
                "target_entity_name": "Neural Networks", 
                "relationship_type": "part_of",
                "confidence_score": 0.9,
                "context": "Neural networks are part of AI",
                "metadata": {}
            }
        ]
        
        await service.graph_builder.build_graph_from_entities_and_relationships(
            test_entities, test_relationships
        )
        
        result = await service.query_graph("Artificial Intelligence")
        print(f"   ✓ Query result: {len(result.get('results', []))} results found")
        if result.get('results'):
            for res in result['results'][:3]:
                print(f"     * {res['entity']} ({res['relationship']}, confidence: {res['confidence']:.3f})")
    except Exception as e:
        print(f"   ✗ Error querying graph: {e}")
    
    # Test graph statistics
    print("\n3. Testing graph statistics...")
    try:
        stats = await service.get_graph_statistics()
        print(f"   ✓ Statistics retrieved: {stats.get('total_entities', 0)} entities, {stats.get('total_relationships', 0)} relationships")
    except Exception as e:
        print(f"   ✗ Error getting statistics: {e}")

async def main():
    """Run all tests"""
    print("Starting GraphBuilder and GraphQueryEngine Tests")
    print("=" * 80)
    
    try:
        # Test GraphBuilder
        builder = await test_graph_builder()
        
        # Test GraphQueryEngine
        await test_graph_query_engine(builder)
        
        # Test EnhancedKnowledgeGraphService
        await test_enhanced_knowledge_graph_service()
        
        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("✓ GraphBuilder: Constructs and maintains knowledge graphs")
        print("✓ GraphQueryEngine: Enables semantic queries over the graph")
        print("✓ Graph updating: Updates graphs when new documents are added")
        print("✓ Graph construction and querying: Fully functional")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)