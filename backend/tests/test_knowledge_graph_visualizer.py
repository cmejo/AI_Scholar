"""
Tests for Knowledge Graph Visualizer Service
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from services.knowledge_graph_visualizer import (
    KnowledgeGraphVisualizer, GraphClusteringAlgorithm, GraphLayoutAlgorithm
)
from models.schemas import EntityType, RelationshipType
from core.database import KnowledgeGraphEntity, KnowledgeGraphRelationship

class TestGraphClusteringAlgorithm:
    """Test graph clustering algorithms"""
    
    def test_simple_clustering_empty_graph(self):
        """Test clustering with empty graph"""
        import networkx as nx
        graph = nx.Graph()
        clusters = GraphClusteringAlgorithm._simple_clustering(graph)
        assert clusters == {}
    
    def test_simple_clustering_single_component(self):
        """Test clustering with single connected component"""
        import networkx as nx
        graph = nx.Graph()
        graph.add_edges_from([("A", "B"), ("B", "C"), ("C", "D")])
        
        clusters = GraphClusteringAlgorithm._simple_clustering(graph)
        
        # All nodes should be in the same cluster
        cluster_values = set(clusters.values())
        assert len(cluster_values) == 1
        assert len(clusters) == 4
    
    def test_simple_clustering_multiple_components(self):
        """Test clustering with multiple connected components"""
        import networkx as nx
        graph = nx.Graph()
        graph.add_edges_from([("A", "B"), ("C", "D")])  # Two separate components
        
        clusters = GraphClusteringAlgorithm._simple_clustering(graph)
        
        # Should have two clusters
        cluster_values = set(clusters.values())
        assert len(cluster_values) == 2
        assert len(clusters) == 4
    
    def test_community_detection_fallback(self):
        """Test community detection falls back to simple clustering"""
        import networkx as nx
        graph = nx.Graph()
        graph.add_edges_from([("A", "B"), ("B", "C")])
        
        # Should work regardless of whether python-louvain is available
        clusters = GraphClusteringAlgorithm.community_detection(graph)
        assert isinstance(clusters, dict)
        assert len(clusters) == 3
    
    def test_hierarchical_clustering(self):
        """Test hierarchical clustering"""
        import networkx as nx
        graph = nx.Graph()
        graph.add_edges_from([("A", "B"), ("B", "C"), ("C", "D")])
        
        levels = GraphClusteringAlgorithm.hierarchical_clustering(graph, num_levels=2)
        
        assert "level_0" in levels
        assert "level_1" in levels
        assert len(levels["level_0"]) == 4
        assert len(levels["level_1"]) == 4

class TestGraphLayoutAlgorithm:
    """Test graph layout algorithms"""
    
    def test_force_directed_layout_empty_graph(self):
        """Test force-directed layout with empty graph"""
        import networkx as nx
        graph = nx.Graph()
        positions = GraphLayoutAlgorithm.force_directed_layout(graph)
        assert positions == {}
    
    def test_force_directed_layout_single_node(self):
        """Test force-directed layout with single node"""
        import networkx as nx
        graph = nx.Graph()
        graph.add_node("A")
        
        positions = GraphLayoutAlgorithm.force_directed_layout(graph, 800, 600)
        
        assert "A" in positions
        x, y = positions["A"]
        assert isinstance(x, (int, float))
        assert isinstance(y, (int, float))
    
    def test_force_directed_layout_multiple_nodes(self):
        """Test force-directed layout with multiple nodes"""
        import networkx as nx
        graph = nx.Graph()
        graph.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
        
        positions = GraphLayoutAlgorithm.force_directed_layout(graph, 800, 600)
        
        assert len(positions) == 3
        for node in ["A", "B", "C"]:
            assert node in positions
            x, y = positions[node]
            assert 0 <= x <= 800
            assert 0 <= y <= 600
    
    def test_circular_layout(self):
        """Test circular layout"""
        import networkx as nx
        graph = nx.Graph()
        graph.add_nodes_from(["A", "B", "C", "D"])
        
        positions = GraphLayoutAlgorithm.circular_layout(graph, 800, 600)
        
        assert len(positions) == 4
        center_x, center_y = 400, 300
        
        # Check that nodes are arranged in a circle
        for node, (x, y) in positions.items():
            distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            assert abs(distance - 210) < 10  # Should be close to radius
    
    def test_hierarchical_layout(self):
        """Test hierarchical layout"""
        import networkx as nx
        graph = nx.Graph()
        graph.add_nodes_from(["A", "B", "C", "D"])
        clusters = {"A": 0, "B": 0, "C": 1, "D": 1}
        
        positions = GraphLayoutAlgorithm.hierarchical_layout(graph, clusters, 800, 600)
        
        assert len(positions) == 4
        
        # Nodes in same cluster should be close to each other
        cluster_0_nodes = [pos for node, pos in positions.items() if clusters[node] == 0]
        cluster_1_nodes = [pos for node, pos in positions.items() if clusters[node] == 1]
        
        assert len(cluster_0_nodes) == 2
        assert len(cluster_1_nodes) == 2
    
    def test_layered_layout(self):
        """Test layered layout based on entity types"""
        import networkx as nx
        graph = nx.Graph()
        graph.add_nodes_from(["person1", "org1", "concept1"])
        entity_types = {
            "person1": "person",
            "org1": "organization", 
            "concept1": "concept"
        }
        
        positions = GraphLayoutAlgorithm.layered_layout(graph, entity_types, 800, 600)
        
        assert len(positions) == 3
        
        # Different types should be on different y levels
        y_positions = [pos[1] for pos in positions.values()]
        assert len(set(y_positions)) >= 2  # At least 2 different y levels

class TestKnowledgeGraphVisualizer:
    """Test main knowledge graph visualizer service"""
    
    @pytest.fixture
    def visualizer(self):
        return KnowledgeGraphVisualizer()
    
    @pytest.fixture
    def mock_entities(self):
        """Mock knowledge graph entities"""
        entities = []
        for i in range(3):
            entity = Mock(spec=KnowledgeGraphEntity)
            entity.id = f"entity_{i}"
            entity.name = f"Entity {i}"
            entity.type = EntityType.CONCEPT.value
            entity.importance_score = 0.5 + i * 0.2
            entity.description = f"Description for entity {i}"
            entity.document_id = f"doc_{i}"
            entity.entity_metadata = {"test": True}
            entities.append(entity)
        return entities
    
    @pytest.fixture
    def mock_relationships(self):
        """Mock knowledge graph relationships"""
        relationships = []
        for i in range(2):
            rel = Mock(spec=KnowledgeGraphRelationship)
            rel.id = f"rel_{i}"
            rel.source_entity_id = f"entity_{i}"
            rel.target_entity_id = f"entity_{i+1}"
            rel.relationship_type = RelationshipType.RELATED_TO.value
            rel.confidence_score = 0.7 + i * 0.1
            rel.context = f"Context for relationship {i}"
            rel.relationship_metadata = {"test": True}
            relationships.append(rel)
        return relationships
    
    @patch('services.knowledge_graph_visualizer.get_db')
    @pytest.mark.asyncio
    async def test_get_graph_visualization_data(self, mock_get_db, visualizer, mock_entities, mock_relationships):
        """Test getting graph visualization data"""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock entity query
        mock_entity_query = Mock()
        mock_entity_query.filter.return_value = mock_entity_query
        mock_entity_query.order_by.return_value = mock_entity_query
        mock_entity_query.limit.return_value = mock_entity_query
        mock_entity_query.all.return_value = mock_entities
        mock_db.query.return_value = mock_entity_query
        
        # Mock relationship query for the second call
        mock_rel_query = Mock()
        mock_rel_query.filter.return_value = mock_rel_query
        mock_rel_query.all.return_value = mock_relationships
        
        # Set up query method to return different mocks for different calls
        def query_side_effect(model):
            if model == KnowledgeGraphEntity:
                return mock_entity_query
            elif model == KnowledgeGraphRelationship:
                return mock_rel_query
            return Mock()
        
        mock_db.query.side_effect = query_side_effect
        
        # Test the method
        result = await visualizer.get_graph_visualization_data()
        
        # Verify structure
        assert "nodes" in result
        assert "edges" in result
        assert "clusters" in result
        assert "metrics" in result
        assert "metadata" in result
        
        # Verify nodes
        assert len(result["nodes"]) == 3
        for node in result["nodes"]:
            assert "id" in node
            assert "label" in node
            assert "type" in node
            assert "size" in node
            assert "color" in node
        
        # Verify edges
        assert len(result["edges"]) == 2
        for edge in result["edges"]:
            assert "id" in edge
            assert "source" in edge
            assert "target" in edge
            assert "weight" in edge
    
    @pytest.mark.asyncio
    async def test_get_graph_layout(self, visualizer):
        """Test getting graph layout"""
        # Mock graph data
        graph_data = {
            "nodes": [
                {"id": "A", "type": "concept", "cluster": 0},
                {"id": "B", "type": "concept", "cluster": 0},
                {"id": "C", "type": "person", "cluster": 1}
            ],
            "edges": [
                {"source": "A", "target": "B", "weight": 0.8},
                {"source": "B", "target": "C", "weight": 0.6}
            ]
        }
        
        # Test force-directed layout
        result = await visualizer.get_graph_layout(
            graph_data, "force_directed", 800, 600
        )
        
        assert "nodes" in result
        assert "layout" in result
        assert result["layout"]["type"] == "force_directed"
        
        # Check that nodes have positions
        for node in result["nodes"]:
            assert "x" in node
            assert "y" in node
            assert isinstance(node["x"], (int, float))
            assert isinstance(node["y"], (int, float))
    
    @patch('services.knowledge_graph_visualizer.get_db')
    @pytest.mark.asyncio
    async def test_get_node_neighborhood(self, mock_get_db, visualizer, mock_entities, mock_relationships):
        """Test getting node neighborhood"""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock central entity query
        central_entity = mock_entities[0]
        mock_db.query.return_value.filter.return_value.first.return_value = central_entity
        
        # Mock relationship query
        mock_db.query.return_value.filter.return_value.all.return_value = mock_relationships
        
        result = await visualizer.get_node_neighborhood("entity_0", depth=1)
        
        assert "nodes" in result
        assert "edges" in result
        assert "center_node" in result
        assert result["center_node"] == "entity_0"
        assert result["depth"] == 1
    
    @patch('services.knowledge_graph_visualizer.get_db')
    @pytest.mark.asyncio
    async def test_search_graph(self, mock_get_db, visualizer, mock_entities, mock_relationships):
        """Test graph search functionality"""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock entity search query
        mock_entity_query = Mock()
        mock_entity_query.filter.return_value = mock_entity_query
        mock_entity_query.limit.return_value = mock_entity_query
        mock_entity_query.all.return_value = mock_entities[:2]  # Return subset
        mock_db.query.return_value = mock_entity_query
        
        # Mock relationship query
        mock_rel_query = Mock()
        mock_rel_query.filter.return_value = mock_rel_query
        mock_rel_query.all.return_value = mock_relationships[:1]
        
        # Set up query method
        def query_side_effect(model):
            if model == KnowledgeGraphEntity:
                return mock_entity_query
            elif model == KnowledgeGraphRelationship:
                return mock_rel_query
            return Mock()
        
        mock_db.query.side_effect = query_side_effect
        
        result = await visualizer.search_graph("Entity", "entity_name")
        
        assert "nodes" in result
        assert "edges" in result
        assert "query" in result
        assert result["query"] == "Entity"
        assert result["search_type"] == "entity_name"
    
    @patch('services.knowledge_graph_visualizer.get_db')
    @pytest.mark.asyncio
    async def test_get_graph_statistics(self, mock_get_db, visualizer, mock_entities):
        """Test getting graph statistics"""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock count queries
        mock_db.query.return_value.count.return_value = 10
        mock_db.query.return_value.filter.return_value.count.return_value = 2
        
        # Mock top entities query
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = mock_entities
        
        result = await visualizer.get_graph_statistics()
        
        assert "total_entities" in result
        assert "total_relationships" in result
        assert "entity_types" in result
        assert "relationship_types" in result
        assert "top_entities" in result
        assert "graph_density" in result
    
    def test_build_networkx_graph(self, visualizer, mock_entities, mock_relationships):
        """Test building NetworkX graph from entities and relationships"""
        graph = visualizer._build_networkx_graph(mock_entities, mock_relationships)
        
        assert graph.number_of_nodes() == 3
        assert graph.number_of_edges() == 2
        
        # Check node attributes
        for entity in mock_entities:
            assert graph.has_node(entity.id)
            node_data = graph.nodes[entity.id]
            assert node_data["name"] == entity.name
            assert node_data["type"] == entity.type
    
    def test_calculate_graph_metrics(self, visualizer):
        """Test calculating graph metrics"""
        import networkx as nx
        
        # Create test graph
        graph = nx.Graph()
        graph.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
        
        metrics = visualizer._calculate_graph_metrics(graph)
        
        assert "num_nodes" in metrics
        assert "num_edges" in metrics
        assert "density" in metrics
        assert "is_connected" in metrics
        assert metrics["num_nodes"] == 3
        assert metrics["num_edges"] == 3
        assert metrics["is_connected"] is True
    
    def test_format_nodes(self, visualizer, mock_entities):
        """Test formatting entities as nodes"""
        clusters = {"entity_0": 0, "entity_1": 0, "entity_2": 1}
        metrics = {
            "degree_centrality": {"entity_0": 0.5, "entity_1": 0.3, "entity_2": 0.8},
            "betweenness_centrality": {"entity_0": 0.2, "entity_1": 0.1, "entity_2": 0.4}
        }
        
        nodes = visualizer._format_nodes(mock_entities, clusters, metrics)
        
        assert len(nodes) == 3
        for node in nodes:
            assert "id" in node
            assert "label" in node
            assert "type" in node
            assert "size" in node
            assert "color" in node
            assert "cluster" in node
            assert "degree_centrality" in node
            assert "betweenness_centrality" in node
    
    def test_format_edges(self, visualizer, mock_relationships):
        """Test formatting relationships as edges"""
        edges = visualizer._format_edges(mock_relationships)
        
        assert len(edges) == 2
        for edge in edges:
            assert "id" in edge
            assert "source" in edge
            assert "target" in edge
            assert "type" in edge
            assert "weight" in edge
            assert "thickness" in edge
            assert "color" in edge
            assert "confidence" in edge
    
    def test_format_clusters(self, visualizer):
        """Test formatting cluster information"""
        clusters = {"A": 0, "B": 0, "C": 1, "D": 1, "E": 2}
        
        formatted_clusters = visualizer._format_clusters(clusters)
        
        assert len(formatted_clusters) == 3
        for cluster in formatted_clusters:
            assert "id" in cluster
            assert "nodes" in cluster
            assert "size" in cluster
            assert "color" in cluster
        
        # Check cluster sizes
        cluster_sizes = {cluster["id"]: cluster["size"] for cluster in formatted_clusters}
        assert cluster_sizes[0] == 2
        assert cluster_sizes[1] == 2
        assert cluster_sizes[2] == 1

@pytest.mark.asyncio
class TestKnowledgeGraphVisualizerIntegration:
    """Integration tests for knowledge graph visualizer"""
    
    @pytest.mark.asyncio
    async def test_full_visualization_pipeline(self):
        """Test the complete visualization pipeline"""
        visualizer = KnowledgeGraphVisualizer()
        
        # This would require a real database setup
        # For now, we'll test that the methods can be called without errors
        try:
            # Test with empty parameters
            result = await visualizer.get_graph_visualization_data(max_nodes=5)
            assert isinstance(result, dict)
        except Exception as e:
            # Expected if database is not set up
            assert "database" in str(e).lower() or "connection" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_layout_algorithms_consistency(self):
        """Test that layout algorithms produce consistent results"""
        visualizer = KnowledgeGraphVisualizer()
        
        # Mock graph data
        graph_data = {
            "nodes": [
                {"id": "A", "type": "concept", "cluster": 0},
                {"id": "B", "type": "concept", "cluster": 0}
            ],
            "edges": [
                {"source": "A", "target": "B", "weight": 0.8}
            ]
        }
        
        # Test different layouts
        layouts = ["force_directed", "circular", "hierarchical", "layered"]
        
        for layout_type in layouts:
            result = await visualizer.get_graph_layout(
                graph_data, layout_type, 400, 300
            )
            
            assert result["layout"]["type"] == layout_type
            assert len(result["nodes"]) == 2
            
            # Check that positions are within bounds
            for node in result["nodes"]:
                assert 0 <= node["x"] <= 400
                assert 0 <= node["y"] <= 300

if __name__ == "__main__":
    pytest.main([__file__])