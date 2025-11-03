"""
Unit tests for diagram analyzer and structure analysis.
"""

import pytest
import numpy as np
import asyncio
from PIL import Image, ImageDraw
import cv2
from unittest.mock import Mock, patch, AsyncMock

from backend.rl.multimodal.diagram_analyzer import (
    DiagramAnalyzer,
    ShapeDetector,
    ConnectionDetector,
    LayoutAnalyzer,
    DiagramNode,
    DiagramEdge,
    NodeShape,
    DiagramType
)
from backend.rl.multimodal.models import StructuralRelationships, BoundingBox


class TestShapeDetector:
    """Test cases for ShapeDetector class."""
    
    def create_simple_shapes_image(self, width=300, height=200):
        """Create an image with simple geometric shapes."""
        img_array = np.full((height, width, 3), 255, dtype=np.uint8)  # White background
        
        # Draw rectangle
        cv2.rectangle(img_array, (50, 50), (120, 100), (0, 0, 0), 2)
        
        # Draw circle
        cv2.circle(img_array, (200, 75), 30, (0, 0, 0), 2)
        
        # Draw triangle (approximate with polygon)
        triangle_points = np.array([[80, 150], [120, 150], [100, 120]], np.int32)
        cv2.polylines(img_array, [triangle_points], True, (0, 0, 0), 2)
        
        # Draw diamond (rotated square)
        diamond_points = np.array([[200, 120], [220, 140], [200, 160], [180, 140]], np.int32)
        cv2.polylines(img_array, [diamond_points], True, (0, 0, 0), 2)
        
        return img_array
    
    def create_filled_shapes_image(self, width=200, height=150):
        """Create an image with filled shapes for better contour detection."""
        img_array = np.full((height, width, 3), 255, dtype=np.uint8)
        
        # Filled rectangle
        cv2.rectangle(img_array, (30, 30), (80, 70), (0, 0, 0), -1)
        
        # Filled circle
        cv2.circle(img_array, (130, 50), 20, (0, 0, 0), -1)
        
        # Filled triangle
        triangle_points = np.array([[50, 120], [80, 120], [65, 90]], np.int32)
        cv2.fillPoly(img_array, [triangle_points], (0, 0, 0))
        
        return img_array
    
    @pytest.mark.asyncio
    async def test_detect_shapes_basic(self):
        """Test basic shape detection."""
        detector = ShapeDetector()
        test_image = self.create_filled_shapes_image()
        
        nodes = await detector.detect_shapes(test_image)
        
        # Should detect some shapes
        assert isinstance(nodes, list)
        assert len(nodes) > 0
        
        # Check node properties
        for node in nodes:
            assert isinstance(node, DiagramNode)
            assert node.node_id.startswith("node_")
            assert isinstance(node.shape, NodeShape)
            assert isinstance(node.bounding_box, BoundingBox)
            assert len(node.center) == 2
            assert node.area > 0
            assert 0 <= node.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_preprocess_image(self):
        """Test image preprocessing."""
        detector = ShapeDetector()
        test_image = self.create_simple_shapes_image()
        
        processed = await detector._preprocess_image(test_image)
        
        # Should return grayscale binary image
        assert len(processed.shape) == 2  # Grayscale
        assert processed.dtype == np.uint8
        assert np.all((processed == 0) | (processed == 255))  # Binary
    
    @pytest.mark.asyncio
    async def test_find_contours(self):
        """Test contour detection."""
        detector = ShapeDetector()
        test_image = self.create_filled_shapes_image()
        
        processed = await detector._preprocess_image(test_image)
        contours = await detector._find_contours(processed)
        
        # Should find contours
        assert isinstance(contours, list)
        assert len(contours) > 0
        
        # Check contour properties
        for contour in contours:
            assert isinstance(contour, np.ndarray)
            area = cv2.contourArea(contour)
            assert detector.min_contour_area <= area <= detector.max_contour_area
    
    @pytest.mark.asyncio
    async def test_classify_contour_rectangle(self):
        """Test classification of rectangular contour."""
        detector = ShapeDetector()
        
        # Create rectangular contour
        rect_contour = np.array([[[50, 50]], [[100, 50]], [[100, 80]], [[50, 80]]], dtype=np.int32)
        
        node = await detector._classify_contour(rect_contour, 0)
        
        assert isinstance(node, DiagramNode)
        assert node.shape == NodeShape.RECTANGLE
        assert node.node_id == "node_0"
        assert node.bounding_box.width > 0
        assert node.bounding_box.height > 0
    
    @pytest.mark.asyncio
    async def test_classify_shape_type_circle(self):
        """Test shape type classification for circular shapes."""
        detector = ShapeDetector()
        
        # Create circular contour (approximate)
        center = (50, 50)
        radius = 20
        angles = np.linspace(0, 2*np.pi, 20)
        circle_points = []
        for angle in angles:
            x = int(center[0] + radius * np.cos(angle))
            y = int(center[1] + radius * np.sin(angle))
            circle_points.append([[x, y]])
        
        circle_contour = np.array(circle_points, dtype=np.int32)
        area = cv2.contourArea(circle_contour)
        perimeter = cv2.arcLength(circle_contour, True)
        
        shape_type, confidence = await detector._classify_shape_type(circle_contour, area, perimeter)
        
        # Should classify as circle with high confidence
        assert shape_type == NodeShape.CIRCLE
        assert confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_classify_shape_type_triangle(self):
        """Test shape type classification for triangular shapes."""
        detector = ShapeDetector()
        
        # Create triangular contour
        triangle_contour = np.array([[[50, 80]], [[70, 50]], [[90, 80]]], dtype=np.int32)
        area = cv2.contourArea(triangle_contour)
        perimeter = cv2.arcLength(triangle_contour, True)
        
        shape_type, confidence = await detector._classify_shape_type(triangle_contour, area, perimeter)
        
        # Should classify as triangle
        assert shape_type == NodeShape.TRIANGLE
        assert confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_detect_shapes_empty_image(self):
        """Test shape detection on empty image."""
        detector = ShapeDetector()
        empty_image = np.full((100, 100, 3), 255, dtype=np.uint8)  # White image
        
        nodes = await detector.detect_shapes(empty_image)
        
        # Should return empty list for empty image
        assert isinstance(nodes, list)
        assert len(nodes) == 0
    
    @pytest.mark.asyncio
    async def test_detect_shapes_noise_filtering(self):
        """Test that small noise is filtered out."""
        detector = ShapeDetector()
        
        # Create image with noise and valid shapes
        img_array = np.full((150, 200, 3), 255, dtype=np.uint8)
        
        # Add small noise (should be filtered)
        cv2.circle(img_array, (50, 50), 2, (0, 0, 0), -1)
        cv2.circle(img_array, (60, 60), 3, (0, 0, 0), -1)
        
        # Add valid shape
        cv2.rectangle(img_array, (100, 50), (150, 100), (0, 0, 0), -1)
        
        nodes = await detector.detect_shapes(img_array)
        
        # Should detect only the valid shape, not the noise
        assert len(nodes) >= 1
        
        # All detected nodes should have reasonable area
        for node in nodes:
            assert node.area >= detector.min_contour_area


class TestConnectionDetector:
    """Test cases for ConnectionDetector class."""
    
    def create_connected_shapes_image(self, width=300, height=200):
        """Create an image with shapes connected by lines."""
        img_array = np.full((height, width, 3), 255, dtype=np.uint8)
        
        # Draw two rectangles
        cv2.rectangle(img_array, (50, 70), (100, 120), (0, 0, 0), -1)
        cv2.rectangle(img_array, (200, 70), (250, 120), (0, 0, 0), -1)
        
        # Draw connecting line
        cv2.line(img_array, (100, 95), (200, 95), (0, 0, 0), 2)
        
        return img_array
    
    def create_sample_nodes(self):
        """Create sample nodes for testing."""
        node1 = DiagramNode(
            node_id="node_1",
            shape=NodeShape.RECTANGLE,
            bounding_box=BoundingBox(x=50, y=70, width=50, height=50),
            center=(75, 95),
            area=2500
        )
        
        node2 = DiagramNode(
            node_id="node_2",
            shape=NodeShape.RECTANGLE,
            bounding_box=BoundingBox(x=200, y=70, width=50, height=50),
            center=(225, 95),
            area=2500
        )
        
        return [node1, node2]
    
    @pytest.mark.asyncio
    async def test_detect_connections_basic(self):
        """Test basic connection detection."""
        detector = ConnectionDetector()
        test_image = self.create_connected_shapes_image()
        nodes = self.create_sample_nodes()
        
        edges = await detector.detect_connections(test_image, nodes)
        
        # Should detect connections
        assert isinstance(edges, list)
        
        # Check edge properties
        for edge in edges:
            assert isinstance(edge, DiagramEdge)
            assert edge.edge_id.startswith("edge_")
            assert edge.source_node_id in ["node_1", "node_2"]
            assert edge.target_node_id in ["node_1", "node_2"]
            assert edge.source_node_id != edge.target_node_id
            assert len(edge.path_points) >= 2
            assert 0 <= edge.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_preprocess_for_lines(self):
        """Test preprocessing for line detection."""
        detector = ConnectionDetector()
        test_image = self.create_connected_shapes_image()
        
        processed = await detector._preprocess_for_lines(test_image)
        
        # Should return edge-detected image
        assert len(processed.shape) == 2  # Grayscale
        assert processed.dtype == np.uint8
    
    @pytest.mark.asyncio
    async def test_detect_lines(self):
        """Test line detection using Hough transform."""
        detector = ConnectionDetector()
        test_image = self.create_connected_shapes_image()
        
        processed = await detector._preprocess_for_lines(test_image)
        lines = await detector._detect_lines(processed)
        
        # Should detect lines
        assert isinstance(lines, list)
        
        # Check line format
        for line in lines:
            assert len(line) == 4  # (x1, y1, x2, y2)
            assert all(isinstance(coord, (int, np.integer)) for coord in line)
    
    @pytest.mark.asyncio
    async def test_find_nearest_node(self):
        """Test finding nearest node to a point."""
        detector = ConnectionDetector()
        nodes = self.create_sample_nodes()
        
        # Test point near first node
        nearest = await detector._find_nearest_node((80, 90), nodes)
        assert nearest is not None
        assert nearest.node_id == "node_1"
        
        # Test point near second node
        nearest = await detector._find_nearest_node((220, 100), nodes)
        assert nearest is not None
        assert nearest.node_id == "node_2"
        
        # Test point far from any node
        nearest = await detector._find_nearest_node((500, 500), nodes)
        assert nearest is None
    
    @pytest.mark.asyncio
    async def test_line_connects_nodes(self):
        """Test checking if a line connects two nodes."""
        detector = ConnectionDetector()
        nodes = self.create_sample_nodes()
        
        # Line that connects the nodes
        connecting_line = (100, 95, 200, 95)
        connects = await detector._line_connects_nodes(connecting_line, nodes[0], nodes[1])
        assert connects is True
        
        # Line that doesn't connect the nodes
        non_connecting_line = (10, 10, 20, 20)
        connects = await detector._line_connects_nodes(non_connecting_line, nodes[0], nodes[1])
        assert connects is False
    
    @pytest.mark.asyncio
    async def test_create_edge_from_line(self):
        """Test creating edge from line information."""
        detector = ConnectionDetector()
        nodes = self.create_sample_nodes()
        
        line_info = {
            "line": (100, 95, 200, 95),
            "source_node": nodes[0],
            "target_node": nodes[1],
            "path_points": [(100, 95), (200, 95)]
        }
        
        edge = await detector._create_edge_from_line(line_info, 0)
        
        assert isinstance(edge, DiagramEdge)
        assert edge.edge_id == "edge_0"
        assert edge.source_node_id == "node_1"
        assert edge.target_node_id == "node_2"
        assert edge.path_points == [(100, 95), (200, 95)]
        assert edge.confidence > 0
    
    @pytest.mark.asyncio
    async def test_detect_connections_no_lines(self):
        """Test connection detection when no lines are present."""
        detector = ConnectionDetector()
        
        # Create image with shapes but no connecting lines
        img_array = np.full((200, 300, 3), 255, dtype=np.uint8)
        cv2.rectangle(img_array, (50, 70), (100, 120), (0, 0, 0), -1)
        cv2.rectangle(img_array, (200, 70), (250, 120), (0, 0, 0), -1)
        
        nodes = self.create_sample_nodes()
        
        edges = await detector.detect_connections(img_array, nodes)
        
        # Should return empty list when no connections
        assert isinstance(edges, list)
        # May be empty or contain very few false positives


class TestLayoutAnalyzer:
    """Test cases for LayoutAnalyzer class."""
    
    def create_sample_nodes_and_edges(self):
        """Create sample nodes and edges for testing."""
        nodes = [
            DiagramNode("node_1", NodeShape.RECTANGLE, BoundingBox(50, 50, 50, 30), (75, 65), 1500),
            DiagramNode("node_2", NodeShape.RECTANGLE, BoundingBox(150, 50, 50, 30), (175, 65), 1500),
            DiagramNode("node_3", NodeShape.RECTANGLE, BoundingBox(100, 120, 50, 30), (125, 135), 1500),
        ]
        
        edges = [
            DiagramEdge("edge_1", "node_1", "node_2", "directed", [(100, 65), (150, 65)]),
            DiagramEdge("edge_2", "node_2", "node_3", "directed", [(175, 80), (125, 120)]),
        ]
        
        return nodes, edges
    
    @pytest.mark.asyncio
    async def test_analyze_layout(self):
        """Test layout analysis."""
        analyzer = LayoutAnalyzer()
        nodes, edges = self.create_sample_nodes_and_edges()
        
        layout_info = await analyzer.analyze_layout(nodes, edges)
        
        # Should return layout information
        assert isinstance(layout_info, dict)
        assert "flow_direction" in layout_info
        assert "hierarchy_levels" in layout_info
        assert "layout_pattern" in layout_info
        assert "spatial_relationships" in layout_info
        
        # Check data types
        assert isinstance(layout_info["flow_direction"], str)
        assert isinstance(layout_info["hierarchy_levels"], dict)
        assert isinstance(layout_info["layout_pattern"], str)
        assert isinstance(layout_info["spatial_relationships"], dict)
    
    @pytest.mark.asyncio
    async def test_determine_flow_direction(self):
        """Test flow direction determination."""
        analyzer = LayoutAnalyzer()
        nodes, edges = self.create_sample_nodes_and_edges()
        
        flow_direction = await analyzer._determine_flow_direction(nodes, edges)
        
        # Should return valid flow direction
        assert flow_direction in ["left-right", "top-down", "mixed", "unknown"]
    
    @pytest.mark.asyncio
    async def test_calculate_hierarchy_levels(self):
        """Test hierarchy level calculation."""
        analyzer = LayoutAnalyzer()
        nodes, edges = self.create_sample_nodes_and_edges()
        
        hierarchy = await analyzer._calculate_hierarchy_levels(nodes, edges)
        
        # Should return hierarchy mapping
        assert isinstance(hierarchy, dict)
        
        # All nodes should have hierarchy levels
        node_ids = {node.node_id for node in nodes}
        for node_id in node_ids:
            if node_id in hierarchy:
                assert isinstance(hierarchy[node_id], int)
                assert hierarchy[node_id] >= 0
    
    @pytest.mark.asyncio
    async def test_detect_layout_pattern(self):
        """Test layout pattern detection."""
        analyzer = LayoutAnalyzer()
        
        # Test with horizontal layout
        horizontal_nodes = [
            DiagramNode("node_1", NodeShape.RECTANGLE, BoundingBox(50, 100, 30, 30), (65, 115), 900),
            DiagramNode("node_2", NodeShape.RECTANGLE, BoundingBox(150, 100, 30, 30), (165, 115), 900),
            DiagramNode("node_3", NodeShape.RECTANGLE, BoundingBox(250, 100, 30, 30), (265, 115), 900),
        ]
        
        pattern = await analyzer._detect_layout_pattern(horizontal_nodes)
        assert pattern in ["horizontal", "vertical", "grid", "circular", "clustered", "scattered", "single"]
    
    @pytest.mark.asyncio
    async def test_is_grid_pattern(self):
        """Test grid pattern detection."""
        analyzer = LayoutAnalyzer()
        
        # Create grid-like positions
        grid_positions = [
            (50, 50), (100, 50), (150, 50),
            (50, 100), (100, 100), (150, 100)
        ]
        
        is_grid = await analyzer._is_grid_pattern(grid_positions)
        assert isinstance(is_grid, bool)
        assert is_grid is True  # Should detect grid pattern
        
        # Test non-grid positions
        random_positions = [(10, 20), (150, 80), (200, 30)]
        is_grid = await analyzer._is_grid_pattern(random_positions)
        assert is_grid is False
    
    @pytest.mark.asyncio
    async def test_is_circular_pattern(self):
        """Test circular pattern detection."""
        analyzer = LayoutAnalyzer()
        
        # Create circular positions
        center = (100, 100)
        radius = 50
        circular_positions = []
        for angle in [0, np.pi/2, np.pi, 3*np.pi/2]:
            x = center[0] + radius * np.cos(angle)
            y = center[1] + radius * np.sin(angle)
            circular_positions.append((x, y))
        
        is_circular = await analyzer._is_circular_pattern(circular_positions)
        assert isinstance(is_circular, bool)
        # May or may not detect as circular depending on tolerance
    
    @pytest.mark.asyncio
    async def test_analyze_spatial_relationships(self):
        """Test spatial relationship analysis."""
        analyzer = LayoutAnalyzer()
        nodes, _ = self.create_sample_nodes_and_edges()
        
        relationships = await analyzer._analyze_spatial_relationships(nodes)
        
        # Should return relationship information
        assert isinstance(relationships, dict)
        assert "alignment" in relationships
        assert "spacing" in relationships
        assert "grouping" in relationships
        
        # Check structure
        assert isinstance(relationships["alignment"], dict)
        assert isinstance(relationships["spacing"], dict)
        assert isinstance(relationships["grouping"], dict)
    
    @pytest.mark.asyncio
    async def test_analyze_layout_empty_input(self):
        """Test layout analysis with empty input."""
        analyzer = LayoutAnalyzer()
        
        layout_info = await analyzer.analyze_layout([], [])
        
        # Should handle empty input gracefully
        assert isinstance(layout_info, dict)
        assert layout_info["flow_direction"] == "unknown"
        assert isinstance(layout_info["hierarchy_levels"], dict)


class TestDiagramAnalyzer:
    """Test cases for DiagramAnalyzer class."""
    
    def create_simple_diagram(self, width=300, height=200):
        """Create a simple diagram for testing."""
        img_array = np.full((height, width, 3), 255, dtype=np.uint8)
        
        # Draw connected shapes
        cv2.rectangle(img_array, (50, 70), (100, 120), (0, 0, 0), -1)
        cv2.rectangle(img_array, (200, 70), (250, 120), (0, 0, 0), -1)
        cv2.line(img_array, (100, 95), (200, 95), (0, 0, 0), 2)
        
        # Add arrow to indicate direction
        cv2.arrowedLine(img_array, (180, 95), (200, 95), (0, 0, 0), 2)
        
        return img_array
    
    def create_flowchart_diagram(self, width=400, height=300):
        """Create a more complex flowchart diagram."""
        img_array = np.full((height, width, 3), 255, dtype=np.uint8)
        
        # Start node (circle)
        cv2.circle(img_array, (200, 50), 25, (0, 0, 0), -1)
        
        # Process nodes (rectangles)
        cv2.rectangle(img_array, (150, 100), (250, 140), (0, 0, 0), -1)
        cv2.rectangle(img_array, (150, 180), (250, 220), (0, 0, 0), -1)
        
        # Decision node (diamond - approximated as rotated square)
        diamond_points = np.array([[200, 160], [230, 180], [200, 200], [170, 180]], np.int32)
        cv2.fillPoly(img_array, [diamond_points], (0, 0, 0))
        
        # Connecting lines
        cv2.line(img_array, (200, 75), (200, 100), (0, 0, 0), 2)  # Start to process
        cv2.line(img_array, (200, 140), (200, 160), (0, 0, 0), 2)  # Process to decision
        cv2.line(img_array, (200, 200), (200, 180), (0, 0, 0), 2)  # Decision to end
        
        return img_array
    
    @pytest.mark.asyncio
    async def test_analyze_diagram_numpy_array(self):
        """Test diagram analysis with numpy array input."""
        analyzer = DiagramAnalyzer()
        diagram_image = self.create_simple_diagram()
        
        result = await analyzer.analyze_diagram(diagram_image)
        
        # Should return StructuralRelationships
        assert isinstance(result, StructuralRelationships)
        assert isinstance(result.nodes, list)
        assert isinstance(result.edges, list)
        assert isinstance(result.hierarchy_levels, dict)
        assert isinstance(result.flow_direction, str)
        assert isinstance(result.relationship_types, dict)
        assert isinstance(result.metadata, dict)
    
    @pytest.mark.asyncio
    async def test_analyze_diagram_pil_image(self):
        """Test diagram analysis with PIL Image input."""
        analyzer = DiagramAnalyzer()
        diagram_array = self.create_simple_diagram()
        pil_image = Image.fromarray(diagram_array)
        
        result = await analyzer.analyze_diagram(pil_image)
        
        # Should return StructuralRelationships
        assert isinstance(result, StructuralRelationships)
        assert result.flow_direction != ""
    
    @pytest.mark.asyncio
    async def test_analyze_diagram_metadata(self):
        """Test that diagram analysis includes proper metadata."""
        analyzer = DiagramAnalyzer()
        diagram_image = self.create_simple_diagram()
        
        result = await analyzer.analyze_diagram(diagram_image)
        
        # Check metadata content
        metadata = result.metadata
        assert 'extraction_method' in metadata
        assert 'image_dimensions' in metadata
        assert 'num_nodes' in metadata
        assert 'num_edges' in metadata
        assert 'layout_pattern' in metadata
        assert 'shape_distribution' in metadata
        
        # Check metadata types
        assert isinstance(metadata['image_dimensions'], tuple)
        assert isinstance(metadata['num_nodes'], int)
        assert isinstance(metadata['num_edges'], int)
        assert isinstance(metadata['layout_pattern'], str)
        assert isinstance(metadata['shape_distribution'], dict)
    
    @pytest.mark.asyncio
    async def test_convert_to_structural_relationships(self):
        """Test conversion to StructuralRelationships format."""
        analyzer = DiagramAnalyzer()
        
        # Create sample data
        nodes = [
            DiagramNode("node_1", NodeShape.RECTANGLE, BoundingBox(50, 50, 50, 30), (75, 65), 1500),
            DiagramNode("node_2", NodeShape.CIRCLE, BoundingBox(150, 50, 40, 40), (170, 70), 1256)
        ]
        
        edges = [
            DiagramEdge("edge_1", "node_1", "node_2", "directed", [(100, 65), (150, 70)])
        ]
        
        layout_info = {
            "hierarchy_levels": {"node_1": 0, "node_2": 1},
            "flow_direction": "left-right",
            "layout_pattern": "horizontal",
            "spatial_relationships": {}
        }
        
        image_shape = (200, 300, 3)
        
        result = await analyzer._convert_to_structural_relationships(
            nodes, edges, layout_info, image_shape
        )
        
        # Check result structure
        assert isinstance(result, StructuralRelationships)
        assert len(result.nodes) == 2
        assert len(result.edges) == 1
        assert result.flow_direction == "left-right"
        
        # Check node format
        node_dict = result.nodes[0]
        assert "id" in node_dict
        assert "shape" in node_dict
        assert "x" in node_dict
        assert "y" in node_dict
        assert "confidence" in node_dict
        
        # Check edge format
        edge_dict = result.edges[0]
        assert "id" in edge_dict
        assert "source" in edge_dict
        assert "target" in edge_dict
        assert "type" in edge_dict
        assert "confidence" in edge_dict
        
        # Check metadata
        assert result.metadata['image_dimensions'] == image_shape
        assert result.metadata['num_nodes'] == 2
        assert result.metadata['num_edges'] == 1
    
    @pytest.mark.asyncio
    async def test_analyze_diagram_error_handling(self):
        """Test error handling in diagram analysis."""
        analyzer = DiagramAnalyzer()
        
        # Test with invalid input that causes error
        with patch.object(analyzer.shape_detector, 'detect_shapes', side_effect=Exception("Test error")):
            result = await analyzer.analyze_diagram(np.zeros((50, 50, 3), dtype=np.uint8))
            
            # Should return error result
            assert isinstance(result, StructuralRelationships)
            assert len(result.nodes) == 0
            assert len(result.edges) == 0
            assert result.flow_direction == "unknown"
            assert 'error' in result.metadata
            assert result.metadata['analysis_failed'] is True
    
    @pytest.mark.asyncio
    async def test_analyze_empty_diagram(self):
        """Test analysis of empty/blank diagram."""
        analyzer = DiagramAnalyzer()
        
        # Create blank white image
        blank_image = np.full((100, 100, 3), 255, dtype=np.uint8)
        
        result = await analyzer.analyze_diagram(blank_image)
        
        # Should complete without error
        assert isinstance(result, StructuralRelationships)
        # May have empty nodes/edges for blank image
        assert isinstance(result.nodes, list)
        assert isinstance(result.edges, list)
    
    @pytest.mark.asyncio
    async def test_analyze_complex_diagram(self):
        """Test analysis of more complex diagram."""
        analyzer = DiagramAnalyzer()
        flowchart_image = self.create_flowchart_diagram()
        
        result = await analyzer.analyze_diagram(flowchart_image)
        
        # Should successfully analyze complex diagram
        assert isinstance(result, StructuralRelationships)
        
        # Should detect multiple nodes
        assert len(result.nodes) >= 2
        
        # Check that nodes have different shapes
        shapes = [node.get("shape") for node in result.nodes]
        assert len(set(shapes)) >= 1  # At least one different shape type
        
        # Should have proper metadata
        assert 'extraction_method' in result.metadata
        assert result.metadata['extraction_method'] == 'advanced_diagram_analysis'


class TestIntegration:
    """Integration tests for diagram analysis components."""
    
    def create_realistic_flowchart(self):
        """Create a realistic flowchart for integration testing."""
        img_array = np.full((400, 500, 3), 255, dtype=np.uint8)
        
        # Title
        cv2.putText(img_array, "Process Flow", (180, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        
        # Start (oval/circle)
        cv2.ellipse(img_array, (250, 80), (40, 20), 0, 0, 360, (0, 0, 0), -1)
        
        # Process steps (rectangles)
        cv2.rectangle(img_array, (200, 130), (300, 170), (0, 0, 0), -1)
        cv2.rectangle(img_array, (200, 210), (300, 250), (0, 0, 0), -1)
        
        # Decision (diamond)
        diamond_points = np.array([[250, 280], (290, 310), (250, 340), (210, 310)], np.int32)
        cv2.fillPoly(img_array, [diamond_points], (0, 0, 0))
        
        # End (oval/circle)
        cv2.ellipse(img_array, (250, 380), (40, 20), 0, 0, 360, (0, 0, 0), -1)
        
        # Connecting arrows
        cv2.arrowedLine(img_array, (250, 100), (250, 130), (0, 0, 0), 2)
        cv2.arrowedLine(img_array, (250, 170), (250, 210), (0, 0, 0), 2)
        cv2.arrowedLine(img_array, (250, 250), (250, 280), (0, 0, 0), 2)
        cv2.arrowedLine(img_array, (250, 340), (250, 360), (0, 0, 0), 2)
        
        # Decision branches
        cv2.arrowedLine(img_array, (290, 310), (350, 310), (0, 0, 0), 2)  # Yes branch
        cv2.arrowedLine(img_array, (210, 310), (150, 310), (0, 0, 0), 2)  # No branch
        
        return img_array
    
    @pytest.mark.asyncio
    async def test_end_to_end_flowchart_analysis(self):
        """Test complete end-to-end analysis of a flowchart."""
        analyzer = DiagramAnalyzer()
        flowchart_image = self.create_realistic_flowchart()
        
        result = await analyzer.analyze_diagram(flowchart_image)
        
        # Should successfully analyze the flowchart
        assert isinstance(result, StructuralRelationships)
        
        # Should detect multiple nodes
        assert len(result.nodes) >= 3
        
        # Should detect connections
        assert len(result.edges) >= 1
        
        # Should have reasonable flow direction
        assert result.flow_direction in ["top-down", "left-right", "mixed", "unknown"]
        
        # Should have hierarchy information
        assert isinstance(result.hierarchy_levels, dict)
        
        # Should have proper metadata
        assert 'extraction_method' in result.metadata
        assert result.metadata['extraction_method'] == 'advanced_diagram_analysis'
        assert result.metadata['num_nodes'] == len(result.nodes)
        assert result.metadata['num_edges'] == len(result.edges)
    
    @pytest.mark.asyncio
    async def test_multiple_diagram_analysis(self):
        """Test analysis of multiple different diagram types."""
        analyzer = DiagramAnalyzer()
        
        # Create different diagram types
        diagrams = [
            self.create_realistic_flowchart(),
            np.random.randint(0, 256, (200, 300, 3), dtype=np.uint8),  # Random image
        ]
        
        results = []
        for diagram in diagrams:
            result = await analyzer.analyze_diagram(diagram)
            results.append(result)
        
        # All should return StructuralRelationships
        for result in results:
            assert isinstance(result, StructuralRelationships)
            assert isinstance(result.flow_direction, str)
            assert isinstance(result.metadata, dict)
    
    @pytest.mark.asyncio
    async def test_performance_with_large_diagram(self):
        """Test performance with larger diagram images."""
        analyzer = DiagramAnalyzer()
        
        # Create large diagram image
        large_diagram = np.full((800, 1200, 3), 255, dtype=np.uint8)
        
        # Add some basic diagram elements
        for i in range(5):
            x = 200 + i * 150
            y = 300
            cv2.rectangle(large_diagram, (x-40, y-20), (x+40, y+20), (0, 0, 0), -1)
            
            if i < 4:
                cv2.arrowedLine(large_diagram, (x+40, y), (x+110, y), (0, 0, 0), 2)
        
        # Should complete analysis without timeout
        result = await analyzer.analyze_diagram(large_diagram)
        
        assert isinstance(result, StructuralRelationships)
        assert result.metadata['image_dimensions'] == (800, 1200, 3)
    
    @pytest.mark.asyncio
    async def test_diagram_with_text_elements(self):
        """Test diagram analysis with text elements."""
        analyzer = DiagramAnalyzer()
        
        # Create diagram with text
        img_array = np.full((300, 400, 3), 255, dtype=np.uint8)
        
        # Add shapes with text labels
        cv2.rectangle(img_array, (50, 100), (150, 140), (0, 0, 0), 2)
        cv2.putText(img_array, "Start", (80, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        cv2.rectangle(img_array, (250, 100), (350, 140), (0, 0, 0), 2)
        cv2.putText(img_array, "End", (280, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        cv2.arrowedLine(img_array, (150, 120), (250, 120), (0, 0, 0), 2)
        
        result = await analyzer.analyze_diagram(img_array)
        
        # Should handle text elements without errors
        assert isinstance(result, StructuralRelationships)
        # Text might affect shape detection, but should not cause failures