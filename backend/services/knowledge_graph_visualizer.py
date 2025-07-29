"""
Knowledge Graph Visualizer Service for interactive graph display and exploration
"""
import json
import logging
import asyncio
import networkx as nx
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict, Counter
from datetime import datetime
import math

from core.database import get_db, KnowledgeGraphEntity, KnowledgeGraphRelationship
from models.schemas import (
    KnowledgeGraphEntityResponse, KnowledgeGraphRelationshipResponse,
    EntityType, RelationshipType
)
from services.knowledge_graph import EnhancedKnowledgeGraphService

logger = logging.getLogger(__name__)

class GraphClusteringAlgorithm:
    """Graph clustering algorithms for knowledge graph visualization"""
    
    @staticmethod
    def community_detection(graph: nx.Graph, resolution: float = 1.0) -> Dict[str, int]:
        """Detect communities using Louvain algorithm"""
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(graph, resolution=resolution)
            return partition
        except ImportError:
            logger.warning("python-louvain not available, using simple clustering")
            return GraphClusteringAlgorithm._simple_clustering(graph)
    
    @staticmethod
    def _simple_clustering(graph: nx.Graph) -> Dict[str, int]:
        """Simple clustering based on connected components"""
        clusters = {}
        cluster_id = 0
        
        for component in nx.connected_components(graph):
            for node in component:
                clusters[node] = cluster_id
            cluster_id += 1
        
        return clusters
    
    @staticmethod
    def hierarchical_clustering(
        graph: nx.Graph, 
        num_levels: int = 3
    ) -> Dict[str, Dict[str, int]]:
        """Hierarchical clustering at multiple levels"""
        levels = {}
        
        for level in range(num_levels):
            resolution = 0.5 + level * 0.5
            clusters = GraphClusteringAlgorithm.community_detection(graph, resolution)
            levels[f"level_{level}"] = clusters
        
        return levels

class GraphLayoutAlgorithm:
    """Graph layout algorithms for positioning nodes"""
    
    @staticmethod
    def force_directed_layout(
        graph: nx.Graph,
        width: int = 800,
        height: int = 600,
        iterations: int = 50,
        k: Optional[float] = None
    ) -> Dict[str, Tuple[float, float]]:
        """Force-directed layout using spring algorithm"""
        if not graph.nodes():
            return {}
        
        # Use NetworkX spring layout as base
        pos = nx.spring_layout(
            graph, 
            k=k, 
            iterations=iterations,
            scale=min(width, height) * 0.4
        )
        
        # Center and scale positions
        center_x, center_y = width / 2, height / 2
        
        positioned_nodes = {}
        for node, (x, y) in pos.items():
            positioned_nodes[node] = (
                center_x + x,
                center_y + y
            )
        
        return positioned_nodes
    
    @staticmethod
    def hierarchical_layout(
        graph: nx.Graph,
        clusters: Dict[str, int],
        width: int = 800,
        height: int = 600
    ) -> Dict[str, Tuple[float, float]]:
        """Hierarchical layout based on clusters"""
        positions = {}
        cluster_groups = defaultdict(list)
        
        # Group nodes by cluster
        for node, cluster_id in clusters.items():
            cluster_groups[cluster_id].append(node)
        
        num_clusters = len(cluster_groups)
        if num_clusters == 0:
            return positions
        
        # Position clusters in a circle
        cluster_positions = {}
        for i, cluster_id in enumerate(cluster_groups.keys()):
            angle = 2 * math.pi * i / num_clusters
            radius = min(width, height) * 0.3
            cluster_positions[cluster_id] = (
                width / 2 + radius * math.cos(angle),
                height / 2 + radius * math.sin(angle)
            )
        
        # Position nodes within each cluster
        for cluster_id, nodes in cluster_groups.items():
            cluster_x, cluster_y = cluster_positions[cluster_id]
            
            if len(nodes) == 1:
                positions[nodes[0]] = (cluster_x, cluster_y)
            else:
                # Arrange nodes in a small circle around cluster center
                cluster_radius = 50 + len(nodes) * 5
                for i, node in enumerate(nodes):
                    angle = 2 * math.pi * i / len(nodes)
                    positions[node] = (
                        cluster_x + cluster_radius * math.cos(angle),
                        cluster_y + cluster_radius * math.sin(angle)
                    )
        
        return positions
    
    @staticmethod
    def circular_layout(
        graph: nx.Graph,
        width: int = 800,
        height: int = 600
    ) -> Dict[str, Tuple[float, float]]:
        """Circular layout with nodes arranged in a circle"""
        positions = {}
        nodes = list(graph.nodes())
        
        if not nodes:
            return positions
        
        radius = min(width, height) * 0.35
        center_x, center_y = width / 2, height / 2
        
        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / len(nodes)
            positions[node] = (
                center_x + radius * math.cos(angle),
                center_y + radius * math.sin(angle)
            )
        
        return positions
    
    @staticmethod
    def layered_layout(
        graph: nx.Graph,
        entity_types: Dict[str, str],
        width: int = 800,
        height: int = 600
    ) -> Dict[str, Tuple[float, float]]:
        """Layered layout based on entity types"""
        positions = {}
        
        # Group nodes by type
        type_groups = defaultdict(list)
        for node in graph.nodes():
            entity_type = entity_types.get(node, "other")
            type_groups[entity_type].append(node)
        
        # Define layer order
        layer_order = ["person", "organization", "location", "concept", "event", "product", "other"]
        layers = []
        
        for entity_type in layer_order:
            if entity_type in type_groups:
                layers.append(type_groups[entity_type])
        
        # Add any remaining types
        for entity_type, nodes in type_groups.items():
            if entity_type not in layer_order:
                layers.append(nodes)
        
        # Position nodes in layers
        layer_height = height / (len(layers) + 1)
        
        for layer_idx, layer_nodes in enumerate(layers):
            y = layer_height * (layer_idx + 1)
            
            if len(layer_nodes) == 1:
                positions[layer_nodes[0]] = (width / 2, y)
            else:
                node_spacing = width / (len(layer_nodes) + 1)
                for node_idx, node in enumerate(layer_nodes):
                    x = node_spacing * (node_idx + 1)
                    positions[node] = (x, y)
        
        return positions

class KnowledgeGraphVisualizer:
    """Main service for knowledge graph visualization"""
    
    def __init__(self):
        self.kg_service = EnhancedKnowledgeGraphService()
        self.clustering = GraphClusteringAlgorithm()
        self.layout = GraphLayoutAlgorithm()
    
    async def get_graph_visualization_data(
        self,
        user_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None,
        relationship_types: Optional[List[str]] = None,
        max_nodes: int = 100,
        min_confidence: float = 0.3
    ) -> Dict[str, Any]:
        """Get graph data formatted for visualization"""
        
        # Fetch entities and relationships
        entities = await self._get_filtered_entities(
            document_ids, entity_types, max_nodes, min_confidence
        )
        
        relationships = await self._get_filtered_relationships(
            [e.id for e in entities], relationship_types, min_confidence
        )
        
        # Build NetworkX graph
        graph = self._build_networkx_graph(entities, relationships)
        
        # Calculate graph metrics
        metrics = self._calculate_graph_metrics(graph)
        
        # Detect clusters
        clusters = self.clustering.community_detection(graph)
        
        # Format for frontend
        visualization_data = {
            "nodes": self._format_nodes(entities, clusters, metrics),
            "edges": self._format_edges(relationships),
            "clusters": self._format_clusters(clusters),
            "metrics": metrics,
            "metadata": {
                "total_nodes": len(entities),
                "total_edges": len(relationships),
                "num_clusters": len(set(clusters.values())) if clusters else 0,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
        return visualization_data
    
    async def get_graph_layout(
        self,
        graph_data: Dict[str, Any],
        layout_type: str = "force_directed",
        width: int = 800,
        height: int = 600,
        **layout_params
    ) -> Dict[str, Any]:
        """Calculate node positions for a specific layout"""
        
        # Rebuild graph from data
        graph = nx.Graph()
        
        # Add nodes
        for node in graph_data["nodes"]:
            graph.add_node(node["id"])
        
        # Add edges
        for edge in graph_data["edges"]:
            graph.add_edge(edge["source"], edge["target"], weight=edge["weight"])
        
        # Calculate positions based on layout type
        if layout_type == "force_directed":
            positions = self.layout.force_directed_layout(
                graph, width, height, **layout_params
            )
        elif layout_type == "hierarchical":
            clusters = {node["id"]: node["cluster"] for node in graph_data["nodes"]}
            positions = self.layout.hierarchical_layout(
                graph, clusters, width, height
            )
        elif layout_type == "circular":
            positions = self.layout.circular_layout(graph, width, height)
        elif layout_type == "layered":
            entity_types = {node["id"]: node["type"] for node in graph_data["nodes"]}
            positions = self.layout.layered_layout(
                graph, entity_types, width, height
            )
        else:
            # Default to force-directed
            positions = self.layout.force_directed_layout(graph, width, height)
        
        # Update node positions
        positioned_nodes = []
        for node in graph_data["nodes"]:
            node_copy = node.copy()
            if node["id"] in positions:
                node_copy["x"], node_copy["y"] = positions[node["id"]]
            else:
                # Fallback position
                node_copy["x"] = width / 2
                node_copy["y"] = height / 2
            positioned_nodes.append(node_copy)
        
        return {
            **graph_data,
            "nodes": positioned_nodes,
            "layout": {
                "type": layout_type,
                "width": width,
                "height": height,
                "parameters": layout_params
            }
        }
    
    async def get_node_neighborhood(
        self,
        node_id: str,
        depth: int = 2,
        max_neighbors: int = 50
    ) -> Dict[str, Any]:
        """Get neighborhood around a specific node"""
        
        db = next(get_db())
        # Get the central entity
        central_entity = db.query(KnowledgeGraphEntity).filter(
            KnowledgeGraphEntity.id == node_id
        ).first()
        
        if not central_entity:
            return {"nodes": [], "edges": [], "error": "Node not found"}
        
        # Get connected entities up to specified depth
        visited = set()
        current_level = {node_id}
        all_entities = {node_id: central_entity}
        all_relationships = []
        
        for level in range(depth):
            if not current_level or len(all_entities) >= max_neighbors:
                break
            
            next_level = set()
            
            # Get relationships for current level
            level_relationships = db.query(KnowledgeGraphRelationship).filter(
                (KnowledgeGraphRelationship.source_entity_id.in_(current_level)) |
                (KnowledgeGraphRelationship.target_entity_id.in_(current_level))
            ).all()
            
            for rel in level_relationships:
                all_relationships.append(rel)
                
                # Add connected entities
                for entity_id in [rel.source_entity_id, rel.target_entity_id]:
                    if entity_id not in visited and len(all_entities) < max_neighbors:
                        entity = db.query(KnowledgeGraphEntity).filter(
                            KnowledgeGraphEntity.id == entity_id
                        ).first()
                        if entity:
                            all_entities[entity_id] = entity
                            next_level.add(entity_id)
            
            visited.update(current_level)
            current_level = next_level
        
        # Build graph and calculate layout
        entities = list(all_entities.values())
        graph = self._build_networkx_graph(entities, all_relationships)
        clusters = self.clustering.community_detection(graph)
        metrics = self._calculate_graph_metrics(graph)
        
        return {
            "nodes": self._format_nodes(entities, clusters, metrics),
            "edges": self._format_edges(all_relationships),
            "center_node": node_id,
            "depth": depth,
            "metadata": {
                "total_nodes": len(entities),
                "total_edges": len(all_relationships),
                "search_depth": depth
            }
        }
    
    async def search_graph(
        self,
        query: str,
        search_type: str = "entity_name",
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search for nodes in the knowledge graph"""
        
        db = next(get_db())
        entities = []
        
        if search_type == "entity_name":
            entities = db.query(KnowledgeGraphEntity).filter(
                KnowledgeGraphEntity.name.ilike(f"%{query}%")
            ).limit(limit).all()
        
        elif search_type == "entity_type":
            entities = db.query(KnowledgeGraphEntity).filter(
                KnowledgeGraphEntity.type == query
            ).limit(limit).all()
        
        elif search_type == "description":
            entities = db.query(KnowledgeGraphEntity).filter(
                KnowledgeGraphEntity.description.ilike(f"%{query}%")
            ).limit(limit).all()
        
        # Get relationships for found entities
        entity_ids = [e.id for e in entities]
        relationships = db.query(KnowledgeGraphRelationship).filter(
            (KnowledgeGraphRelationship.source_entity_id.in_(entity_ids)) |
            (KnowledgeGraphRelationship.target_entity_id.in_(entity_ids))
        ).all()
        
        # Build visualization data
        if entities:
            graph = self._build_networkx_graph(entities, relationships)
            clusters = self.clustering.community_detection(graph)
            metrics = self._calculate_graph_metrics(graph)
            
            return {
                "nodes": self._format_nodes(entities, clusters, metrics),
                "edges": self._format_edges(relationships),
                "query": query,
                "search_type": search_type,
                "metadata": {
                    "results_count": len(entities),
                    "total_edges": len(relationships)
                }
            }
        
        return {
            "nodes": [],
            "edges": [],
            "query": query,
            "search_type": search_type,
            "metadata": {"results_count": 0}
        }
    
    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get overall graph statistics"""
        
        db = next(get_db())
        # Entity statistics
        total_entities = db.query(KnowledgeGraphEntity).count()
        entity_type_counts = {}
        
        for entity_type in EntityType:
            count = db.query(KnowledgeGraphEntity).filter(
                KnowledgeGraphEntity.type == entity_type.value
            ).count()
            entity_type_counts[entity_type.value] = count
        
        # Relationship statistics
        total_relationships = db.query(KnowledgeGraphRelationship).count()
        relationship_type_counts = {}
        
        for rel_type in RelationshipType:
            count = db.query(KnowledgeGraphRelationship).filter(
                KnowledgeGraphRelationship.relationship_type == rel_type.value
            ).count()
            relationship_type_counts[rel_type.value] = count
        
        # Get top entities by importance
        top_entities = db.query(KnowledgeGraphEntity).order_by(
            KnowledgeGraphEntity.importance_score.desc()
        ).limit(10).all()
        
        return {
            "total_entities": total_entities,
            "total_relationships": total_relationships,
            "entity_types": entity_type_counts,
            "relationship_types": relationship_type_counts,
            "top_entities": [
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.type,
                    "importance_score": e.importance_score
                }
                for e in top_entities
            ],
            "graph_density": total_relationships / (total_entities * (total_entities - 1) / 2) if total_entities > 1 else 0
        }
    
    async def _get_filtered_entities(
        self,
        document_ids: Optional[List[str]],
        entity_types: Optional[List[str]],
        max_nodes: int,
        min_confidence: float
    ) -> List[KnowledgeGraphEntity]:
        """Get filtered entities based on criteria"""
        
        db = next(get_db())
        query = db.query(KnowledgeGraphEntity)
        
        if document_ids:
            query = query.filter(KnowledgeGraphEntity.document_id.in_(document_ids))
        
        if entity_types:
            query = query.filter(KnowledgeGraphEntity.type.in_(entity_types))
        
        # Filter by importance score as proxy for confidence
        query = query.filter(KnowledgeGraphEntity.importance_score >= min_confidence)
        
        # Order by importance and limit
        entities = query.order_by(
            KnowledgeGraphEntity.importance_score.desc()
        ).limit(max_nodes).all()
        
        return entities
    
    async def _get_filtered_relationships(
        self,
        entity_ids: List[str],
        relationship_types: Optional[List[str]],
        min_confidence: float
    ) -> List[KnowledgeGraphRelationship]:
        """Get filtered relationships for given entities"""
        
        db = next(get_db())
        query = db.query(KnowledgeGraphRelationship).filter(
            (KnowledgeGraphRelationship.source_entity_id.in_(entity_ids)) &
            (KnowledgeGraphRelationship.target_entity_id.in_(entity_ids))
        )
        
        if relationship_types:
            query = query.filter(
                KnowledgeGraphRelationship.relationship_type.in_(relationship_types)
            )
        
        # Filter by confidence score
        query = query.filter(
            KnowledgeGraphRelationship.confidence_score >= min_confidence
        )
        
        relationships = query.all()
        return relationships
    
    def _build_networkx_graph(
        self,
        entities: List[KnowledgeGraphEntity],
        relationships: List[KnowledgeGraphRelationship]
    ) -> nx.Graph:
        """Build NetworkX graph from entities and relationships"""
        
        graph = nx.Graph()
        
        # Add nodes
        for entity in entities:
            graph.add_node(
                entity.id,
                name=entity.name,
                type=entity.type,
                importance=entity.importance_score
            )
        
        # Add edges
        for rel in relationships:
            if graph.has_node(rel.source_entity_id) and graph.has_node(rel.target_entity_id):
                graph.add_edge(
                    rel.source_entity_id,
                    rel.target_entity_id,
                    relationship_type=rel.relationship_type,
                    confidence=rel.confidence_score,
                    weight=rel.confidence_score
                )
        
        return graph
    
    def _calculate_graph_metrics(self, graph: nx.Graph) -> Dict[str, Any]:
        """Calculate various graph metrics"""
        
        if not graph.nodes():
            return {}
        
        # Basic metrics
        metrics = {
            "num_nodes": graph.number_of_nodes(),
            "num_edges": graph.number_of_edges(),
            "density": nx.density(graph),
            "is_connected": nx.is_connected(graph)
        }
        
        # Centrality measures
        try:
            degree_centrality = nx.degree_centrality(graph)
            betweenness_centrality = nx.betweenness_centrality(graph)
            closeness_centrality = nx.closeness_centrality(graph)
            
            metrics.update({
                "degree_centrality": degree_centrality,
                "betweenness_centrality": betweenness_centrality,
                "closeness_centrality": closeness_centrality
            })
        except Exception as e:
            logger.warning(f"Failed to calculate centrality measures: {e}")
        
        # Connected components
        if not nx.is_connected(graph):
            components = list(nx.connected_components(graph))
            metrics["connected_components"] = len(components)
            metrics["largest_component_size"] = len(max(components, key=len))
        
        return metrics
    
    def _format_nodes(
        self,
        entities: List[KnowledgeGraphEntity],
        clusters: Dict[str, int],
        metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Format entities as nodes for visualization"""
        
        nodes = []
        degree_centrality = metrics.get("degree_centrality", {})
        betweenness_centrality = metrics.get("betweenness_centrality", {})
        
        # Color mapping for entity types
        type_colors = {
            "person": "#3B82F6",      # Blue
            "organization": "#10B981", # Emerald
            "location": "#F59E0B",     # Amber
            "concept": "#8B5CF6",      # Violet
            "event": "#EF4444",        # Red
            "product": "#06B6D4",      # Cyan
            "other": "#6B7280"         # Gray
        }
        
        for entity in entities:
            # Calculate node size based on importance and centrality
            base_size = 10
            importance_factor = entity.importance_score * 20
            centrality_factor = degree_centrality.get(entity.id, 0) * 15
            node_size = base_size + importance_factor + centrality_factor
            
            nodes.append({
                "id": entity.id,
                "label": entity.name,
                "type": entity.type,
                "size": min(max(node_size, 8), 40),  # Clamp between 8 and 40
                "color": type_colors.get(entity.type, type_colors["other"]),
                "importance": entity.importance_score,
                "cluster": clusters.get(entity.id, 0),
                "degree_centrality": degree_centrality.get(entity.id, 0),
                "betweenness_centrality": betweenness_centrality.get(entity.id, 0),
                "description": entity.description,
                "document_id": entity.document_id,
                "metadata": entity.entity_metadata or {}
            })
        
        return nodes
    
    def _format_edges(
        self,
        relationships: List[KnowledgeGraphRelationship]
    ) -> List[Dict[str, Any]]:
        """Format relationships as edges for visualization"""
        
        edges = []
        
        # Color mapping for relationship types
        type_colors = {
            "related_to": "#6B7280",    # Gray
            "part_of": "#10B981",       # Emerald
            "causes": "#EF4444",        # Red
            "similar_to": "#3B82F6",    # Blue
            "opposite_of": "#F59E0B",   # Amber
            "defined_by": "#8B5CF6",    # Violet
            "example_of": "#06B6D4"     # Cyan
        }
        
        for rel in relationships:
            # Calculate edge thickness based on confidence
            thickness = max(1, rel.confidence_score * 5)
            
            edges.append({
                "id": rel.id,
                "source": rel.source_entity_id,
                "target": rel.target_entity_id,
                "type": rel.relationship_type,
                "weight": rel.confidence_score,
                "thickness": thickness,
                "color": type_colors.get(rel.relationship_type, type_colors["related_to"]),
                "confidence": rel.confidence_score,
                "context": rel.context,
                "metadata": rel.relationship_metadata or {}
            })
        
        return edges
    
    def _format_clusters(self, clusters: Dict[str, int]) -> List[Dict[str, Any]]:
        """Format cluster information"""
        
        cluster_info = defaultdict(list)
        for node_id, cluster_id in clusters.items():
            cluster_info[cluster_id].append(node_id)
        
        formatted_clusters = []
        for cluster_id, node_ids in cluster_info.items():
            formatted_clusters.append({
                "id": cluster_id,
                "nodes": node_ids,
                "size": len(node_ids),
                "color": f"hsl({(cluster_id * 137.5) % 360}, 70%, 50%)"  # Golden ratio colors
            })
        
        return formatted_clusters