"""
Diagram structure analysis for multi-modal learning system.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
import numpy as np
from PIL import Image, ImageDraw
import cv2
from dataclasses import dataclass
from enum import Enum
import networkx as nx

from .models import StructuralRelationships, BoundingBox

logger = logging.getLogger(__name__)


class DiagramType(Enum):
    """Types of diagrams that can be analyzed."""
    FLOWCHART = "flowchart"
    ORGANIZATIONAL_CHART = "org_chart"
    NETWORK_DIAGRAM = "network"
    PROCESS_DIAGRAM = "process"
    MIND_MAP = "mind_map"
    TREE_DIAGRAM = "tree"
    CIRCUIT_DIAGRAM = "circuit"
    UNKNOWN = "unknown"


class NodeShape(Enum):
    """Types of node shapes in diagrams."""
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    DIAMOND = "diamond"
    ELLIPSE = "ellipse"
    TRIANGLE = "triangle"
    HEXAGON = "hexagon"
    UNKNOWN = "unknown"


@dataclass
class DiagramNode:
    """Represents a node in a diagram."""
    node_id: str
    shape: NodeShape
    bounding_box: BoundingBox
    center: Tuple[float, float]
    area: float
    text_content: Optional[str] = None
    confidence: float = 1.0
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class DiagramEdge:
    """Represents an edge/connection in a diagram."""
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: str  # "directed", "undirected", "bidirectional"
    path_points: List[Tuple[float, float]]
    confidence: float = 1.0
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class ShapeDetector:
    """Detects and classifies shapes in diagram images."""
    
    def __init__(self):
        self.min_contour_area = 100
        self.max_contour_area = 50000
    
    async def detect_shapes(self, image: np.ndarray) -> List[DiagramNode]:
        """Detect shapes in the diagram image."""
        nodes = []
        
        # Preprocess image
        processed_image = await self._preprocess_image(image)
        
        # Find contours
        contours = await self._find_contours(processed_image)
        
        # Classify each contour as a shape
        for i, contour in enumerate(contours):
            node = await self._classify_contour(contour, i)
            if node:
                nodes.append(node)
        
        return nodes
    
    async def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for shape detection."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Morphological operations to clean up
        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        return cleaned
    
    async def _find_contours(self, processed_image: np.ndarray) -> List[np.ndarray]:
        """Find contours in the processed image."""
        contours, _ = cv2.findContours(
            processed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter contours by area
        filtered_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if self.min_contour_area <= area <= self.max_contour_area:
                filtered_contours.append(contour)
        
        return filtered_contours
    
    async def _classify_contour(self, contour: np.ndarray, node_id: int) -> Optional[DiagramNode]:
        """Classify a contour as a specific shape type."""
        # Calculate contour properties
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if area < self.min_contour_area:
            return None
        
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)
        bounding_box = BoundingBox(x=float(x), y=float(y), width=float(w), height=float(h))
        
        # Calculate center
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]
        else:
            cx, cy = x + w/2, y + h/2
        
        center = (float(cx), float(cy))
        
        # Classify shape
        shape_type, confidence = await self._classify_shape_type(contour, area, perimeter)
        
        return DiagramNode(
            node_id=f"node_{node_id}",
            shape=shape_type,
            bounding_box=bounding_box,
            center=center,
            area=float(area),
            confidence=confidence,
            properties={
                "perimeter": float(perimeter),
                "aspect_ratio": float(w / h) if h > 0 else 1.0,
                "extent": float(area / (w * h)) if w * h > 0 else 0.0,
                "solidity": float(area / cv2.contourArea(cv2.convexHull(contour)))
            }
        )
    
    async def _classify_shape_type(self, contour: np.ndarray, area: float, perimeter: float) -> Tuple[NodeShape, float]:
        """Classify the shape type of a contour."""
        # Approximate contour to polygon
        epsilon = 0.02 * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)
        vertices = len(approx)
        
        # Calculate circularity
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        
        # Get bounding rectangle properties
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / h if h > 0 else 1.0
        
        # Classification logic
        if circularity > 0.7:
            return NodeShape.CIRCLE, 0.9
        
        elif vertices == 3:
            return NodeShape.TRIANGLE, 0.8
        
        elif vertices == 4:
            # Check if it's square-like or rectangular
            if 0.8 <= aspect_ratio <= 1.2:
                # Could be square or diamond
                # Check orientation to distinguish diamond
                rect = cv2.minAreaRect(contour)
                angle = rect[2]
                if abs(angle) > 30 and abs(angle) < 60:
                    return NodeShape.DIAMOND, 0.7
                else:
                    return NodeShape.RECTANGLE, 0.8
            else:
                return NodeShape.RECTANGLE, 0.8
        
        elif vertices >= 5 and vertices <= 8:
            if circularity > 0.5:
                if vertices == 6:
                    return NodeShape.HEXAGON, 0.7
                else:
                    return NodeShape.ELLIPSE, 0.6
            else:
                return NodeShape.RECTANGLE, 0.5  # Irregular rectangle
        
        else:
            # Many vertices or irregular shape
            if circularity > 0.4:
                return NodeShape.ELLIPSE, 0.5
            else:
                return NodeShape.UNKNOWN, 0.3


class ConnectionDetector:
    """Detects connections/edges between nodes in diagrams."""
    
    def __init__(self):
        self.line_detection_threshold = 50
        self.min_line_length = 20
        self.max_line_gap = 10
    
    async def detect_connections(self, image: np.ndarray, nodes: List[DiagramNode]) -> List[DiagramEdge]:
        """Detect connections between nodes."""
        edges = []
        
        # Preprocess image for line detection
        processed_image = await self._preprocess_for_lines(image)
        
        # Detect lines
        lines = await self._detect_lines(processed_image)
        
        # Filter lines that connect nodes
        connecting_lines = await self._filter_connecting_lines(lines, nodes)
        
        # Create edges from connecting lines
        for i, line_info in enumerate(connecting_lines):
            edge = await self._create_edge_from_line(line_info, i)
            if edge:
                edges.append(edge)
        
        return edges
    
    async def _preprocess_for_lines(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for line detection."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
        
        return edges
    
    async def _detect_lines(self, edge_image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect lines using Hough transform."""
        lines = cv2.HoughLinesP(
            edge_image,
            rho=1,
            theta=np.pi/180,
            threshold=self.line_detection_threshold,
            minLineLength=self.min_line_length,
            maxLineGap=self.max_line_gap
        )
        
        if lines is None:
            return []
        
        # Convert to list of tuples
        line_list = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            line_list.append((x1, y1, x2, y2))
        
        return line_list
    
    async def _filter_connecting_lines(self, lines: List[Tuple[int, int, int, int]], nodes: List[DiagramNode]) -> List[Dict[str, Any]]:
        """Filter lines that actually connect nodes."""
        connecting_lines = []
        
        for line in lines:
            x1, y1, x2, y2 = line
            
            # Find nodes that this line connects
            source_node = await self._find_nearest_node((x1, y1), nodes)
            target_node = await self._find_nearest_node((x2, y2), nodes)
            
            if source_node and target_node and source_node != target_node:
                # Check if line actually connects the nodes (not just near them)
                if await self._line_connects_nodes(line, source_node, target_node):
                    connecting_lines.append({
                        "line": line,
                        "source_node": source_node,
                        "target_node": target_node,
                        "path_points": [(x1, y1), (x2, y2)]
                    })
        
        return connecting_lines
    
    async def _find_nearest_node(self, point: Tuple[int, int], nodes: List[DiagramNode], max_distance: float = 50.0) -> Optional[DiagramNode]:
        """Find the nearest node to a given point."""
        x, y = point
        nearest_node = None
        min_distance = float('inf')
        
        for node in nodes:
            # Calculate distance to node center
            dx = x - node.center[0]
            dy = y - node.center[1]
            distance = np.sqrt(dx*dx + dy*dy)
            
            # Check if point is within node bounds or nearby
            bbox = node.bounding_box
            if (bbox.x <= x <= bbox.x + bbox.width and 
                bbox.y <= y <= bbox.y + bbox.height):
                # Point is inside node
                return node
            elif distance < max_distance and distance < min_distance:
                min_distance = distance
                nearest_node = node
        
        return nearest_node
    
    async def _line_connects_nodes(self, line: Tuple[int, int, int, int], source_node: DiagramNode, target_node: DiagramNode) -> bool:
        """Check if a line actually connects two nodes."""
        x1, y1, x2, y2 = line
        
        # Check if line endpoints are near the node boundaries
        source_bbox = source_node.bounding_box
        target_bbox = target_node.bounding_box
        
        # Calculate distances from line endpoints to node boundaries
        source_distance = min(
            abs(x1 - source_bbox.x),  # Left edge
            abs(x1 - (source_bbox.x + source_bbox.width)),  # Right edge
            abs(y1 - source_bbox.y),  # Top edge
            abs(y1 - (source_bbox.y + source_bbox.height))  # Bottom edge
        )
        
        target_distance = min(
            abs(x2 - target_bbox.x),
            abs(x2 - (target_bbox.x + target_bbox.width)),
            abs(y2 - target_bbox.y),
            abs(y2 - (target_bbox.y + target_bbox.height))
        )
        
        # Line connects nodes if endpoints are close to node boundaries
        return source_distance < 20 and target_distance < 20
    
    async def _create_edge_from_line(self, line_info: Dict[str, Any], edge_id: int) -> Optional[DiagramEdge]:
        """Create a DiagramEdge from line information."""
        source_node = line_info["source_node"]
        target_node = line_info["target_node"]
        path_points = line_info["path_points"]
        
        # Determine edge type (simplified - assume directed for now)
        edge_type = "directed"
        
        # Check for arrowheads to determine direction (simplified)
        # In a more sophisticated implementation, this would analyze the line endpoints
        
        return DiagramEdge(
            edge_id=f"edge_{edge_id}",
            source_node_id=source_node.node_id,
            target_node_id=target_node.node_id,
            edge_type=edge_type,
            path_points=path_points,
            confidence=0.7,
            properties={
                "length": np.sqrt((path_points[1][0] - path_points[0][0])**2 + 
                                (path_points[1][1] - path_points[0][1])**2)
            }
        )


class LayoutAnalyzer:
    """Analyzes the layout and hierarchy of diagram elements."""
    
    def __init__(self):
        pass
    
    async def analyze_layout(self, nodes: List[DiagramNode], edges: List[DiagramEdge]) -> Dict[str, Any]:
        """Analyze the layout structure of the diagram."""
        layout_info = {}
        
        # Determine flow direction
        layout_info["flow_direction"] = await self._determine_flow_direction(nodes, edges)
        
        # Calculate hierarchy levels
        layout_info["hierarchy_levels"] = await self._calculate_hierarchy_levels(nodes, edges)
        
        # Detect layout patterns
        layout_info["layout_pattern"] = await self._detect_layout_pattern(nodes)
        
        # Calculate spatial relationships
        layout_info["spatial_relationships"] = await self._analyze_spatial_relationships(nodes)
        
        return layout_info
    
    async def _determine_flow_direction(self, nodes: List[DiagramNode], edges: List[DiagramEdge]) -> str:
        """Determine the primary flow direction of the diagram."""
        if not edges:
            return "unknown"
        
        # Analyze edge directions
        horizontal_flow = 0
        vertical_flow = 0
        
        for edge in edges:
            if len(edge.path_points) >= 2:
                start = edge.path_points[0]
                end = edge.path_points[-1]
                
                dx = abs(end[0] - start[0])
                dy = abs(end[1] - start[1])
                
                if dx > dy:
                    horizontal_flow += 1
                else:
                    vertical_flow += 1
        
        if horizontal_flow > vertical_flow * 1.5:
            return "left-right"
        elif vertical_flow > horizontal_flow * 1.5:
            return "top-down"
        else:
            return "mixed"
    
    async def _calculate_hierarchy_levels(self, nodes: List[DiagramNode], edges: List[DiagramEdge]) -> Dict[str, int]:
        """Calculate hierarchy levels for nodes."""
        hierarchy = {}
        
        if not nodes:
            return hierarchy
        
        # Create a graph
        G = nx.DiGraph()
        
        # Add nodes
        for node in nodes:
            G.add_node(node.node_id)
        
        # Add edges
        for edge in edges:
            if edge.edge_type in ["directed", "bidirectional"]:
                G.add_edge(edge.source_node_id, edge.target_node_id)
        
        # Find root nodes (nodes with no incoming edges)
        root_nodes = [node for node in G.nodes() if G.in_degree(node) == 0]
        
        if not root_nodes:
            # If no clear root, use topological sort or assign level 0 to all
            try:
                topo_order = list(nx.topological_sort(G))
                for i, node_id in enumerate(topo_order):
                    hierarchy[node_id] = i
            except nx.NetworkXError:
                # Graph has cycles, assign levels based on position
                for i, node in enumerate(nodes):
                    hierarchy[node.node_id] = 0
        else:
            # BFS from root nodes to assign levels
            visited = set()
            queue = [(root_id, 0) for root_id in root_nodes]
            
            while queue:
                node_id, level = queue.pop(0)
                
                if node_id not in visited:
                    visited.add(node_id)
                    hierarchy[node_id] = level
                    
                    # Add children to queue
                    for successor in G.successors(node_id):
                        if successor not in visited:
                            queue.append((successor, level + 1))
        
        return hierarchy
    
    async def _detect_layout_pattern(self, nodes: List[DiagramNode]) -> str:
        """Detect the overall layout pattern."""
        if len(nodes) < 2:
            return "single"
        
        # Analyze node positions
        positions = [node.center for node in nodes]
        x_coords = [pos[0] for pos in positions]
        y_coords = [pos[1] for pos in positions]
        
        # Calculate variance in x and y directions
        x_variance = np.var(x_coords) if len(x_coords) > 1 else 0
        y_variance = np.var(y_coords) if len(y_coords) > 1 else 0
        
        # Determine pattern based on coordinate distribution
        if x_variance < y_variance * 0.3:
            return "vertical"
        elif y_variance < x_variance * 0.3:
            return "horizontal"
        elif len(nodes) <= 4:
            return "clustered"
        else:
            # Check for grid-like pattern
            if await self._is_grid_pattern(positions):
                return "grid"
            elif await self._is_circular_pattern(positions):
                return "circular"
            else:
                return "scattered"
    
    async def _is_grid_pattern(self, positions: List[Tuple[float, float]]) -> bool:
        """Check if positions form a grid pattern."""
        if len(positions) < 4:
            return False
        
        # Group positions by similar x and y coordinates
        x_coords = sorted(set(round(pos[0], -1) for pos in positions))
        y_coords = sorted(set(round(pos[1], -1) for pos in positions))
        
        # Check if we have multiple rows and columns
        return len(x_coords) >= 2 and len(y_coords) >= 2
    
    async def _is_circular_pattern(self, positions: List[Tuple[float, float]]) -> bool:
        """Check if positions form a circular pattern."""
        if len(positions) < 4:
            return False
        
        # Calculate center of positions
        center_x = np.mean([pos[0] for pos in positions])
        center_y = np.mean([pos[1] for pos in positions])
        
        # Calculate distances from center
        distances = [np.sqrt((pos[0] - center_x)**2 + (pos[1] - center_y)**2) for pos in positions]
        
        # Check if distances are similar (circular arrangement)
        distance_variance = np.var(distances)
        mean_distance = np.mean(distances)
        
        return distance_variance < (mean_distance * 0.3)**2 if mean_distance > 0 else False
    
    async def _analyze_spatial_relationships(self, nodes: List[DiagramNode]) -> Dict[str, Any]:
        """Analyze spatial relationships between nodes."""
        relationships = {
            "alignment": {},
            "spacing": {},
            "grouping": {}
        }
        
        if len(nodes) < 2:
            return relationships
        
        # Analyze alignment
        horizontal_groups = {}
        vertical_groups = {}
        
        for node in nodes:
            y_key = round(node.center[1], -1)  # Round to nearest 10
            x_key = round(node.center[0], -1)
            
            if y_key not in horizontal_groups:
                horizontal_groups[y_key] = []
            horizontal_groups[y_key].append(node.node_id)
            
            if x_key not in vertical_groups:
                vertical_groups[x_key] = []
            vertical_groups[x_key].append(node.node_id)
        
        # Find significant alignments (groups with multiple nodes)
        relationships["alignment"]["horizontal"] = {
            k: v for k, v in horizontal_groups.items() if len(v) > 1
        }
        relationships["alignment"]["vertical"] = {
            k: v for k, v in vertical_groups.items() if len(v) > 1
        }
        
        # Analyze spacing
        x_positions = sorted([node.center[0] for node in nodes])
        y_positions = sorted([node.center[1] for node in nodes])
        
        if len(x_positions) > 1:
            x_spacings = [x_positions[i+1] - x_positions[i] for i in range(len(x_positions)-1)]
            relationships["spacing"]["horizontal"] = {
                "mean": np.mean(x_spacings),
                "std": np.std(x_spacings),
                "regular": np.std(x_spacings) < np.mean(x_spacings) * 0.3
            }
        
        if len(y_positions) > 1:
            y_spacings = [y_positions[i+1] - y_positions[i] for i in range(len(y_positions)-1)]
            relationships["spacing"]["vertical"] = {
                "mean": np.mean(y_spacings),
                "std": np.std(y_spacings),
                "regular": np.std(y_spacings) < np.mean(y_spacings) * 0.3
            }
        
        return relationships


class DiagramAnalyzer:
    """Main diagram analyzer that coordinates all diagram analysis components."""
    
    def __init__(self):
        self.shape_detector = ShapeDetector()
        self.connection_detector = ConnectionDetector()
        self.layout_analyzer = LayoutAnalyzer()
    
    async def analyze_diagram(self, image: Union[np.ndarray, Image.Image]) -> StructuralRelationships:
        """Analyze a diagram image and extract structural relationships."""
        
        # Convert PIL Image to numpy array if needed
        if isinstance(image, Image.Image):
            image_array = np.array(image)
        else:
            image_array = image
        
        try:
            # Detect shapes/nodes
            nodes = await self.shape_detector.detect_shapes(image_array)
            
            # Detect connections/edges
            edges = await self.connection_detector.detect_connections(image_array, nodes)
            
            # Analyze layout
            layout_info = await self.layout_analyzer.analyze_layout(nodes, edges)
            
            # Convert to StructuralRelationships format
            structural_relationships = await self._convert_to_structural_relationships(
                nodes, edges, layout_info, image_array.shape
            )
            
            logger.info(f"Analyzed diagram with {len(nodes)} nodes and {len(edges)} edges")
            return structural_relationships
            
        except Exception as e:
            logger.error(f"Error analyzing diagram: {str(e)}")
            # Return minimal structure
            return StructuralRelationships(
                nodes=[],
                edges=[],
                hierarchy_levels={},
                flow_direction="unknown",
                relationship_types={},
                metadata={
                    "error": str(e),
                    "analysis_failed": True
                }
            )
    
    async def _convert_to_structural_relationships(
        self, 
        nodes: List[DiagramNode], 
        edges: List[DiagramEdge], 
        layout_info: Dict[str, Any],
        image_shape: Tuple[int, ...]
    ) -> StructuralRelationships:
        """Convert detected elements to StructuralRelationships format."""
        
        # Convert nodes to dictionary format
        node_dicts = []
        for node in nodes:
            node_dict = {
                "id": node.node_id,
                "shape": node.shape.value,
                "x": node.center[0],
                "y": node.center[1],
                "width": node.bounding_box.width,
                "height": node.bounding_box.height,
                "area": node.area,
                "confidence": node.confidence
            }
            
            if node.text_content:
                node_dict["label"] = node.text_content
            
            # Add shape-specific properties
            node_dict.update(node.properties)
            
            node_dicts.append(node_dict)
        
        # Convert edges to dictionary format
        edge_dicts = []
        for edge in edges:
            edge_dict = {
                "id": edge.edge_id,
                "source": edge.source_node_id,
                "target": edge.target_node_id,
                "type": edge.edge_type,
                "confidence": edge.confidence,
                "path": edge.path_points
            }
            
            # Add edge-specific properties
            edge_dict.update(edge.properties)
            
            edge_dicts.append(edge_dict)
        
        # Extract hierarchy levels
        hierarchy_levels = layout_info.get("hierarchy_levels", {})
        
        # Extract flow direction
        flow_direction = layout_info.get("flow_direction", "unknown")
        
        # Create relationship types mapping
        relationship_types = {}
        for edge in edges:
            relationship_types[edge.edge_id] = edge.edge_type
        
        return StructuralRelationships(
            nodes=node_dicts,
            edges=edge_dicts,
            hierarchy_levels=hierarchy_levels,
            flow_direction=flow_direction,
            relationship_types=relationship_types,
            metadata={
                "extraction_method": "advanced_diagram_analysis",
                "image_dimensions": image_shape,
                "num_nodes": len(nodes),
                "num_edges": len(edges),
                "layout_pattern": layout_info.get("layout_pattern", "unknown"),
                "spatial_relationships": layout_info.get("spatial_relationships", {}),
                "shape_distribution": {
                    shape.value: len([n for n in nodes if n.shape == shape])
                    for shape in NodeShape
                },
                "average_node_confidence": np.mean([n.confidence for n in nodes]) if nodes else 0.0,
                "average_edge_confidence": np.mean([e.confidence for e in edges]) if edges else 0.0
            }
        )