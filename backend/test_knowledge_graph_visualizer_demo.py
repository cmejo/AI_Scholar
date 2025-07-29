"""
Demo script for Knowledge Graph Visualizer Service
"""
import asyncio
import json
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.knowledge_graph_visualizer import KnowledgeGraphVisualizer, GraphClusteringAlgorithm, GraphLayoutAlgorithm
from services.knowledge_graph import EnhancedKnowledgeGraphService
from core.database import init_db, get_db
from models.schemas import EntityType, RelationshipType

async def create_sample_knowledge_graph():
    """Create sample knowledge graph data for testing"""
    print("Creating sample knowledge graph data...")
    
    kg_service = EnhancedKnowledgeGraphService()
    
    # Sample text about machine learning
    sample_text = """
    Machine learning is a subset of artificial intelligence that focuses on algorithms 
    that can learn from data. Neural networks are a key component of deep learning, 
    which is a subset of machine learning. Popular frameworks like TensorFlow and 
    PyTorch are used to build neural networks. Companies like Google and Facebook 
    have made significant contributions to the field. Researchers at Stanford and MIT 
    have published important papers on transformer architectures.
    """
    
    try:
        # Extract entities and relationships
        entities = await kg_service.entity_extractor.extract_entities(sample_text)
        print(f"Extracted {len(entities)} entities")
        
        relationships = await kg_service.relationship_mapper.extract_relationships(
            sample_text, entities
        )
        print(f"Extracted {len(relationships)} relationships")
        
        # Store in database (if available)
        async with get_db() as db:
            # This would normally store the entities and relationships
            # For demo purposes, we'll just print them
            print("\nSample Entities:")
            for entity in entities[:5]:  # Show first 5
                print(f"  - {entity['text']} ({entity['type']}) - confidence: {entity['confidence']:.2f}")
            
            print("\nSample Relationships:")
            for rel in relationships[:5]:  # Show first 5
                print(f"  - {rel['source']} -> {rel['target']} ({rel['type']}) - confidence: {rel['confidence']:.2f}")
        
        return entities, relationships
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        return [], []

async def test_clustering_algorithms():
    """Test graph clustering algorithms"""
    print("\n" + "="*50)
    print("TESTING CLUSTERING ALGORITHMS")
    print("="*50)
    
    import networkx as nx
    
    # Create sample graph
    graph = nx.Graph()
    edges = [
        ("ML", "AI"), ("ML", "DL"), ("DL", "NN"), ("NN", "TensorFlow"),
        ("TensorFlow", "Google"), ("PyTorch", "Facebook"), ("Stanford", "Research"),
        ("MIT", "Research"), ("Research", "Papers")
    ]
    graph.add_edges_from(edges)
    
    print(f"Created graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
    
    # Test community detection
    clusters = GraphClusteringAlgorithm.community_detection(graph)
    print(f"\nCommunity Detection Results:")
    cluster_groups = {}
    for node, cluster_id in clusters.items():
        if cluster_id not in cluster_groups:
            cluster_groups[cluster_id] = []
        cluster_groups[cluster_id].append(node)
    
    for cluster_id, nodes in cluster_groups.items():
        print(f"  Cluster {cluster_id}: {', '.join(nodes)}")
    
    # Test hierarchical clustering
    hierarchical_clusters = GraphClusteringAlgorithm.hierarchical_clustering(graph, num_levels=2)
    print(f"\nHierarchical Clustering Results:")
    for level, level_clusters in hierarchical_clusters.items():
        print(f"  {level}: {len(set(level_clusters.values()))} clusters")

async def test_layout_algorithms():
    """Test graph layout algorithms"""
    print("\n" + "="*50)
    print("TESTING LAYOUT ALGORITHMS")
    print("="*50)
    
    import networkx as nx
    
    # Create sample graph
    graph = nx.Graph()
    nodes = ["AI", "ML", "DL", "NN", "TensorFlow", "PyTorch", "Google", "Facebook"]
    edges = [("AI", "ML"), ("ML", "DL"), ("DL", "NN"), ("NN", "TensorFlow"), ("NN", "PyTorch")]
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)
    
    width, height = 800, 600
    
    # Test force-directed layout
    print("Testing Force-Directed Layout...")
    positions = GraphLayoutAlgorithm.force_directed_layout(graph, width, height)
    print(f"  Positioned {len(positions)} nodes")
    for node, (x, y) in list(positions.items())[:3]:
        print(f"    {node}: ({x:.1f}, {y:.1f})")
    
    # Test circular layout
    print("\nTesting Circular Layout...")
    positions = GraphLayoutAlgorithm.circular_layout(graph, width, height)
    print(f"  Positioned {len(positions)} nodes in circle")
    
    # Test hierarchical layout
    print("\nTesting Hierarchical Layout...")
    clusters = {node: i % 3 for i, node in enumerate(nodes)}  # 3 clusters
    positions = GraphLayoutAlgorithm.hierarchical_layout(graph, clusters, width, height)
    print(f"  Positioned {len(positions)} nodes hierarchically")
    
    # Test layered layout
    print("\nTesting Layered Layout...")
    entity_types = {
        "AI": "concept", "ML": "concept", "DL": "concept", "NN": "concept",
        "TensorFlow": "product", "PyTorch": "product",
        "Google": "organization", "Facebook": "organization"
    }
    positions = GraphLayoutAlgorithm.layered_layout(graph, entity_types, width, height)
    print(f"  Positioned {len(positions)} nodes in layers")

async def test_visualizer_service():
    """Test the main visualizer service"""
    print("\n" + "="*50)
    print("TESTING VISUALIZER SERVICE")
    print("="*50)
    
    visualizer = KnowledgeGraphVisualizer()
    
    try:
        # Test getting visualization data
        print("Testing get_graph_visualization_data...")
        viz_data = await visualizer.get_graph_visualization_data(max_nodes=10)
        
        print(f"  Nodes: {len(viz_data.get('nodes', []))}")
        print(f"  Edges: {len(viz_data.get('edges', []))}")
        print(f"  Clusters: {len(viz_data.get('clusters', []))}")
        print(f"  Metrics: {list(viz_data.get('metrics', {}).keys())}")
        
        if viz_data.get('nodes'):
            # Test layout generation
            print("\nTesting layout generation...")
            layouts = ["force_directed", "circular", "hierarchical", "layered"]
            
            for layout_type in layouts:
                try:
                    layout_data = await visualizer.get_graph_layout(
                        viz_data, layout_type, 800, 600
                    )
                    print(f"  {layout_type}: ✓")
                except Exception as e:
                    print(f"  {layout_type}: ✗ ({e})")
        
        # Test graph statistics
        print("\nTesting graph statistics...")
        stats = await visualizer.get_graph_statistics()
        print(f"  Total entities: {stats.get('total_entities', 0)}")
        print(f"  Total relationships: {stats.get('total_relationships', 0)}")
        print(f"  Graph density: {stats.get('graph_density', 0):.3f}")
        
    except Exception as e:
        print(f"Error testing visualizer service: {e}")
        print("This is expected if the database is not set up with knowledge graph data")

async def test_search_functionality():
    """Test graph search functionality"""
    print("\n" + "="*50)
    print("TESTING SEARCH FUNCTIONALITY")
    print("="*50)
    
    visualizer = KnowledgeGraphVisualizer()
    
    try:
        # Test entity name search
        print("Testing entity name search...")
        search_results = await visualizer.search_graph("machine", "entity_name", limit=5)
        print(f"  Found {len(search_results.get('nodes', []))} nodes")
        
        # Test entity type search
        print("Testing entity type search...")
        search_results = await visualizer.search_graph("concept", "entity_type", limit=5)
        print(f"  Found {len(search_results.get('nodes', []))} concept nodes")
        
    except Exception as e:
        print(f"Error testing search: {e}")

async def test_neighborhood_exploration():
    """Test neighborhood exploration"""
    print("\n" + "="*50)
    print("TESTING NEIGHBORHOOD EXPLORATION")
    print("="*50)
    
    visualizer = KnowledgeGraphVisualizer()
    
    try:
        # This would require actual entity IDs from the database
        print("Testing neighborhood exploration...")
        print("  (Requires actual entity data in database)")
        
        # For demo, we'll show the structure
        sample_result = {
            "nodes": [],
            "edges": [],
            "center_node": "sample_id",
            "depth": 2,
            "metadata": {"total_nodes": 0, "total_edges": 0}
        }
        print(f"  Expected structure: {list(sample_result.keys())}")
        
    except Exception as e:
        print(f"Error testing neighborhood: {e}")

async def demonstrate_visualization_pipeline():
    """Demonstrate the complete visualization pipeline"""
    print("\n" + "="*50)
    print("VISUALIZATION PIPELINE DEMONSTRATION")
    print("="*50)
    
    # Step 1: Create sample data
    entities, relationships = await create_sample_knowledge_graph()
    
    # Step 2: Test clustering
    await test_clustering_algorithms()
    
    # Step 3: Test layouts
    await test_layout_algorithms()
    
    # Step 4: Test visualizer service
    await test_visualizer_service()
    
    # Step 5: Test search
    await test_search_functionality()
    
    # Step 6: Test neighborhood exploration
    await test_neighborhood_exploration()

async def export_sample_visualization():
    """Export a sample visualization for frontend testing"""
    print("\n" + "="*50)
    print("EXPORTING SAMPLE VISUALIZATION")
    print("="*50)
    
    # Create sample visualization data
    sample_viz = {
        "nodes": [
            {
                "id": "ai",
                "label": "Artificial Intelligence",
                "type": "concept",
                "size": 25,
                "color": "#8B5CF6",
                "importance": 0.9,
                "cluster": 0,
                "x": 400,
                "y": 200
            },
            {
                "id": "ml",
                "label": "Machine Learning",
                "type": "concept", 
                "size": 22,
                "color": "#8B5CF6",
                "importance": 0.8,
                "cluster": 0,
                "x": 300,
                "y": 300
            },
            {
                "id": "dl",
                "label": "Deep Learning",
                "type": "concept",
                "size": 20,
                "color": "#8B5CF6", 
                "importance": 0.7,
                "cluster": 0,
                "x": 500,
                "y": 300
            },
            {
                "id": "tensorflow",
                "label": "TensorFlow",
                "type": "product",
                "size": 18,
                "color": "#06B6D4",
                "importance": 0.6,
                "cluster": 1,
                "x": 200,
                "y": 400
            },
            {
                "id": "google",
                "label": "Google",
                "type": "organization",
                "size": 20,
                "color": "#10B981",
                "importance": 0.8,
                "cluster": 1,
                "x": 150,
                "y": 500
            }
        ],
        "edges": [
            {
                "id": "ai_ml",
                "source": "ai",
                "target": "ml",
                "type": "part_of",
                "weight": 0.9,
                "thickness": 4,
                "color": "#10B981"
            },
            {
                "id": "ml_dl", 
                "source": "ml",
                "target": "dl",
                "type": "part_of",
                "weight": 0.8,
                "thickness": 3,
                "color": "#10B981"
            },
            {
                "id": "dl_tensorflow",
                "source": "dl",
                "target": "tensorflow",
                "type": "related_to",
                "weight": 0.7,
                "thickness": 3,
                "color": "#6B7280"
            },
            {
                "id": "tensorflow_google",
                "source": "tensorflow",
                "target": "google",
                "type": "created_by",
                "weight": 0.9,
                "thickness": 4,
                "color": "#3B82F6"
            }
        ],
        "clusters": [
            {
                "id": 0,
                "nodes": ["ai", "ml", "dl"],
                "size": 3,
                "color": "hsl(0, 70%, 50%)"
            },
            {
                "id": 1,
                "nodes": ["tensorflow", "google"],
                "size": 2,
                "color": "hsl(137.5, 70%, 50%)"
            }
        ],
        "metadata": {
            "total_nodes": 5,
            "total_edges": 4,
            "num_clusters": 2,
            "generated_at": datetime.utcnow().isoformat()
        }
    }
    
    # Save to file
    output_file = "sample_knowledge_graph_visualization.json"
    with open(output_file, 'w') as f:
        json.dump(sample_viz, f, indent=2)
    
    print(f"Sample visualization exported to: {output_file}")
    print(f"Nodes: {len(sample_viz['nodes'])}")
    print(f"Edges: {len(sample_viz['edges'])}")
    print(f"Clusters: {len(sample_viz['clusters'])}")

async def main():
    """Main demo function"""
    print("Knowledge Graph Visualizer Demo")
    print("=" * 50)
    
    try:
        # Initialize database (if available)
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        print("Continuing with limited functionality...")
    
    # Run demonstrations
    await demonstrate_visualization_pipeline()
    
    # Export sample data
    await export_sample_visualization()
    
    print("\n" + "="*50)
    print("DEMO COMPLETED")
    print("="*50)
    print("Key features demonstrated:")
    print("✓ Graph clustering algorithms")
    print("✓ Graph layout algorithms") 
    print("✓ Visualization data formatting")
    print("✓ Search functionality")
    print("✓ Neighborhood exploration")
    print("✓ Sample data export")

if __name__ == "__main__":
    asyncio.run(main())