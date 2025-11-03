"""
Unit tests for multi-modal data models.
"""

import pytest
import numpy as np
from datetime import datetime
from typing import Dict, List

from backend.rl.multimodal.models import (
    VisualElement,
    VisualElementType,
    BoundingBox,
    ElementRelationship,
    CrossModalRelationship,
    TextFeatures,
    VisualFeatures,
    MultiModalFeatures,
    DocumentContent,
    ResearchContext,
    UserInteraction,
    MultiModalContext,
    QuantitativeData,
    StructuralRelationships
)


class TestBoundingBox:
    """Test cases for BoundingBox class."""
    
    def test_valid_bounding_box_creation(self):
        """Test creating a valid bounding box."""
        bbox = BoundingBox(x=10.0, y=20.0, width=100.0, height=50.0)
        assert bbox.x == 10.0
        assert bbox.y == 20.0
        assert bbox.width == 100.0
        assert bbox.height == 50.0
    
    def test_bounding_box_area_calculation(self):
        """Test area calculation."""
        bbox = BoundingBox(x=0.0, y=0.0, width=10.0, height=5.0)
        assert bbox.area() == 50.0
    
    def test_bounding_box_center_calculation(self):
        """Test center point calculation."""
        bbox = BoundingBox(x=10.0, y=20.0, width=100.0, height=50.0)
        center = bbox.center()
        assert center == (60.0, 45.0)
    
    def test_bounding_box_intersection(self):
        """Test intersection detection."""
        bbox1 = BoundingBox(x=0.0, y=0.0, width=10.0, height=10.0)
        bbox2 = BoundingBox(x=5.0, y=5.0, width=10.0, height=10.0)
        bbox3 = BoundingBox(x=20.0, y=20.0, width=10.0, height=10.0)
        
        assert bbox1.intersects(bbox2)
        assert bbox2.intersects(bbox1)
        assert not bbox1.intersects(bbox3)
        assert not bbox3.intersects(bbox1)
    
    def test_invalid_bounding_box_negative_dimensions(self):
        """Test validation of negative dimensions."""
        with pytest.raises(ValueError, match="Width and height must be positive"):
            BoundingBox(x=0.0, y=0.0, width=-10.0, height=10.0)
        
        with pytest.raises(ValueError, match="Width and height must be positive"):
            BoundingBox(x=0.0, y=0.0, width=10.0, height=-10.0)
    
    def test_invalid_bounding_box_negative_coordinates(self):
        """Test validation of negative coordinates."""
        with pytest.raises(ValueError, match="Coordinates must be non-negative"):
            BoundingBox(x=-10.0, y=0.0, width=10.0, height=10.0)
        
        with pytest.raises(ValueError, match="Coordinates must be non-negative"):
            BoundingBox(x=0.0, y=-10.0, width=10.0, height=10.0)


class TestElementRelationship:
    """Test cases for ElementRelationship class."""
    
    def test_valid_relationship_creation(self):
        """Test creating a valid element relationship."""
        rel = ElementRelationship(
            source_element_id="elem1",
            target_element_id="elem2",
            relationship_type="contains",
            confidence=0.8
        )
        assert rel.source_element_id == "elem1"
        assert rel.target_element_id == "elem2"
        assert rel.relationship_type == "contains"
        assert rel.confidence == 0.8
    
    def test_invalid_confidence_values(self):
        """Test validation of confidence values."""
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            ElementRelationship(
                source_element_id="elem1",
                target_element_id="elem2",
                relationship_type="contains",
                confidence=1.5
            )
        
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            ElementRelationship(
                source_element_id="elem1",
                target_element_id="elem2",
                relationship_type="contains",
                confidence=-0.1
            )
    
    def test_empty_relationship_type(self):
        """Test validation of empty relationship type."""
        with pytest.raises(ValueError, match="Relationship type cannot be empty"):
            ElementRelationship(
                source_element_id="elem1",
                target_element_id="elem2",
                relationship_type="",
                confidence=0.8
            )


class TestVisualElement:
    """Test cases for VisualElement class."""
    
    def test_valid_visual_element_creation(self):
        """Test creating a valid visual element."""
        bbox = BoundingBox(x=10.0, y=20.0, width=100.0, height=50.0)
        element = VisualElement(
            element_id="elem1",
            element_type=VisualElementType.CHART,
            bounding_box=bbox,
            confidence=0.9
        )
        assert element.element_id == "elem1"
        assert element.element_type == VisualElementType.CHART
        assert element.confidence == 0.9
        assert element.is_valid()
    
    def test_add_relationship(self):
        """Test adding relationships to visual element."""
        bbox = BoundingBox(x=10.0, y=20.0, width=100.0, height=50.0)
        element = VisualElement(
            element_id="elem1",
            element_type=VisualElementType.CHART,
            bounding_box=bbox,
            confidence=0.9
        )
        
        rel = ElementRelationship(
            source_element_id="elem1",
            target_element_id="elem2",
            relationship_type="references",
            confidence=0.7
        )
        
        element.add_relationship(rel)
        assert len(element.relationships) == 1
        assert element.relationships[0] == rel
    
    def test_get_relationships_by_type(self):
        """Test filtering relationships by type."""
        bbox = BoundingBox(x=10.0, y=20.0, width=100.0, height=50.0)
        element = VisualElement(
            element_id="elem1",
            element_type=VisualElementType.CHART,
            bounding_box=bbox,
            confidence=0.9
        )
        
        rel1 = ElementRelationship("elem1", "elem2", "contains", 0.8)
        rel2 = ElementRelationship("elem1", "elem3", "references", 0.7)
        rel3 = ElementRelationship("elem1", "elem4", "contains", 0.9)
        
        element.add_relationship(rel1)
        element.add_relationship(rel2)
        element.add_relationship(rel3)
        
        contains_rels = element.get_relationships_by_type("contains")
        assert len(contains_rels) == 2
        assert all(r.relationship_type == "contains" for r in contains_rels)
    
    def test_invalid_confidence_values(self):
        """Test validation of confidence values."""
        bbox = BoundingBox(x=10.0, y=20.0, width=100.0, height=50.0)
        
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            VisualElement(
                element_id="elem1",
                element_type=VisualElementType.CHART,
                bounding_box=bbox,
                confidence=1.5
            )
    
    def test_empty_element_id(self):
        """Test validation of empty element ID."""
        bbox = BoundingBox(x=10.0, y=20.0, width=100.0, height=50.0)
        
        with pytest.raises(ValueError, match="Element ID cannot be empty"):
            VisualElement(
                element_id="",
                element_type=VisualElementType.CHART,
                bounding_box=bbox,
                confidence=0.9
            )
    
    def test_invalid_relationship_source(self):
        """Test validation of relationship source ID."""
        bbox = BoundingBox(x=10.0, y=20.0, width=100.0, height=50.0)
        element = VisualElement(
            element_id="elem1",
            element_type=VisualElementType.CHART,
            bounding_box=bbox,
            confidence=0.9
        )
        
        rel = ElementRelationship(
            source_element_id="elem2",  # Wrong source ID
            target_element_id="elem3",
            relationship_type="references",
            confidence=0.7
        )
        
        with pytest.raises(ValueError, match="Relationship source must match element ID"):
            element.add_relationship(rel)


class TestCrossModalRelationship:
    """Test cases for CrossModalRelationship class."""
    
    def test_valid_cross_modal_relationship(self):
        """Test creating a valid cross-modal relationship."""
        rel = CrossModalRelationship(
            text_span=(10, 50),
            visual_element_id="elem1",
            relationship_type="describes",
            confidence=0.8,
            semantic_similarity=0.7
        )
        assert rel.text_span == (10, 50)
        assert rel.visual_element_id == "elem1"
        assert rel.relationship_type == "describes"
        assert rel.confidence == 0.8
        assert rel.semantic_similarity == 0.7
    
    def test_invalid_confidence_values(self):
        """Test validation of confidence values."""
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            CrossModalRelationship(
                text_span=(10, 50),
                visual_element_id="elem1",
                relationship_type="describes",
                confidence=1.5,
                semantic_similarity=0.7
            )
    
    def test_invalid_semantic_similarity(self):
        """Test validation of semantic similarity values."""
        with pytest.raises(ValueError, match="Semantic similarity must be between 0 and 1"):
            CrossModalRelationship(
                text_span=(10, 50),
                visual_element_id="elem1",
                relationship_type="describes",
                confidence=0.8,
                semantic_similarity=1.5
            )
    
    def test_invalid_text_span(self):
        """Test validation of text span."""
        with pytest.raises(ValueError, match="Invalid text span"):
            CrossModalRelationship(
                text_span=(-5, 50),
                visual_element_id="elem1",
                relationship_type="describes",
                confidence=0.8,
                semantic_similarity=0.7
            )
        
        with pytest.raises(ValueError, match="Invalid text span"):
            CrossModalRelationship(
                text_span=(50, 10),  # End before start
                visual_element_id="elem1",
                relationship_type="describes",
                confidence=0.8,
                semantic_similarity=0.7
            )


class TestTextFeatures:
    """Test cases for TextFeatures class."""
    
    def test_valid_text_features_creation(self):
        """Test creating valid text features."""
        embeddings = np.random.rand(100)
        tokens = ["hello", "world", "test"]
        semantic_features = {"sentiment": 0.8, "complexity": 0.6}
        linguistic_features = {"pos_tags": 0.7}
        domain_features = {"technical": 0.9}
        
        features = TextFeatures(
            embeddings=embeddings,
            tokens=tokens,
            semantic_features=semantic_features,
            linguistic_features=linguistic_features,
            domain_features=domain_features
        )
        
        assert np.array_equal(features.embeddings, embeddings)
        assert features.tokens == tokens
        assert features.semantic_features == semantic_features
    
    def test_empty_embeddings(self):
        """Test validation of empty embeddings."""
        with pytest.raises(ValueError, match="Embeddings cannot be empty"):
            TextFeatures(
                embeddings=np.array([]),
                tokens=["hello"],
                semantic_features={},
                linguistic_features={},
                domain_features={}
            )
    
    def test_empty_tokens(self):
        """Test validation of empty tokens."""
        with pytest.raises(ValueError, match="Tokens cannot be empty"):
            TextFeatures(
                embeddings=np.random.rand(100),
                tokens=[],
                semantic_features={},
                linguistic_features={},
                domain_features={}
            )


class TestVisualFeatures:
    """Test cases for VisualFeatures class."""
    
    def test_valid_visual_features_creation(self):
        """Test creating valid visual features."""
        embeddings = np.random.rand(256)
        color_features = {"brightness": 0.7, "contrast": 0.8}
        texture_features = {"roughness": 0.6}
        shape_features = {"circularity": 0.9}
        spatial_features = {"density": 0.5}
        content_features = {"has_text": True}
        
        features = VisualFeatures(
            visual_embeddings=embeddings,
            color_features=color_features,
            texture_features=texture_features,
            shape_features=shape_features,
            spatial_features=spatial_features,
            content_features=content_features
        )
        
        assert np.array_equal(features.visual_embeddings, embeddings)
        assert features.color_features == color_features
    
    def test_empty_visual_embeddings(self):
        """Test validation of empty visual embeddings."""
        with pytest.raises(ValueError, match="Visual embeddings cannot be empty"):
            VisualFeatures(
                visual_embeddings=np.array([]),
                color_features={},
                texture_features={},
                shape_features={},
                spatial_features={},
                content_features={}
            )


class TestMultiModalFeatures:
    """Test cases for MultiModalFeatures class."""
    
    def create_sample_text_features(self):
        """Create sample text features for testing."""
        return TextFeatures(
            embeddings=np.random.rand(100),
            tokens=["hello", "world"],
            semantic_features={"sentiment": 0.8},
            linguistic_features={"pos": 0.7},
            domain_features={"tech": 0.9}
        )
    
    def create_sample_visual_features(self):
        """Create sample visual features for testing."""
        return VisualFeatures(
            visual_embeddings=np.random.rand(256),
            color_features={"brightness": 0.7},
            texture_features={"roughness": 0.6},
            shape_features={"circularity": 0.9},
            spatial_features={"density": 0.5},
            content_features={"has_text": True}
        )
    
    def test_valid_multimodal_features_creation(self):
        """Test creating valid multi-modal features."""
        text_features = self.create_sample_text_features()
        visual_features = [self.create_sample_visual_features()]
        cross_modal_relationships = []
        integrated_embedding = np.random.rand(512)
        confidence_scores = {"text": 0.8, "visual": 0.9, "integration": 0.7}
        
        features = MultiModalFeatures(
            text_features=text_features,
            visual_features=visual_features,
            cross_modal_relationships=cross_modal_relationships,
            integrated_embedding=integrated_embedding,
            confidence_scores=confidence_scores
        )
        
        assert features.text_features == text_features
        assert features.visual_features == visual_features
        assert features.confidence_scores == confidence_scores
    
    def test_overall_confidence_calculation(self):
        """Test overall confidence score calculation."""
        text_features = self.create_sample_text_features()
        visual_features = [self.create_sample_visual_features()]
        confidence_scores = {"text": 0.8, "visual": 0.6, "integration": 0.9}
        
        features = MultiModalFeatures(
            text_features=text_features,
            visual_features=visual_features,
            cross_modal_relationships=[],
            integrated_embedding=np.random.rand(512),
            confidence_scores=confidence_scores
        )
        
        expected_confidence = (0.8 + 0.6 + 0.9) / 3
        assert abs(features.get_overall_confidence() - expected_confidence) < 1e-6
    
    def test_high_quality_check(self):
        """Test high quality threshold check."""
        text_features = self.create_sample_text_features()
        visual_features = [self.create_sample_visual_features()]
        
        # High quality features
        high_confidence_scores = {"text": 0.9, "visual": 0.8, "integration": 0.85}
        high_quality_features = MultiModalFeatures(
            text_features=text_features,
            visual_features=visual_features,
            cross_modal_relationships=[],
            integrated_embedding=np.random.rand(512),
            confidence_scores=high_confidence_scores
        )
        
        assert high_quality_features.is_high_quality(threshold=0.7)
        
        # Low quality features
        low_confidence_scores = {"text": 0.5, "visual": 0.4, "integration": 0.6}
        low_quality_features = MultiModalFeatures(
            text_features=text_features,
            visual_features=visual_features,
            cross_modal_relationships=[],
            integrated_embedding=np.random.rand(512),
            confidence_scores=low_confidence_scores
        )
        
        assert not low_quality_features.is_high_quality(threshold=0.7)
    
    def test_empty_integrated_embedding(self):
        """Test validation of empty integrated embedding."""
        text_features = self.create_sample_text_features()
        visual_features = [self.create_sample_visual_features()]
        
        with pytest.raises(ValueError, match="Integrated embedding cannot be empty"):
            MultiModalFeatures(
                text_features=text_features,
                visual_features=visual_features,
                cross_modal_relationships=[],
                integrated_embedding=np.array([]),
                confidence_scores={"text": 0.8}
            )
    
    def test_empty_visual_features(self):
        """Test validation of empty visual features."""
        text_features = self.create_sample_text_features()
        
        with pytest.raises(ValueError, match="Visual features cannot be empty"):
            MultiModalFeatures(
                text_features=text_features,
                visual_features=[],
                cross_modal_relationships=[],
                integrated_embedding=np.random.rand(512),
                confidence_scores={"text": 0.8}
            )
    
    def test_invalid_confidence_scores(self):
        """Test validation of confidence scores."""
        text_features = self.create_sample_text_features()
        visual_features = [self.create_sample_visual_features()]
        
        with pytest.raises(ValueError, match="Confidence score for text must be between 0 and 1"):
            MultiModalFeatures(
                text_features=text_features,
                visual_features=visual_features,
                cross_modal_relationships=[],
                integrated_embedding=np.random.rand(512),
                confidence_scores={"text": 1.5}  # Invalid score
            )


class TestQuantitativeData:
    """Test cases for QuantitativeData class."""
    
    def test_valid_quantitative_data_creation(self):
        """Test creating valid quantitative data."""
        data_points = [{"x": 1.0, "y": 2.0}, {"x": 2.0, "y": 4.0}]
        data_series = {"series1": [1.0, 2.0, 3.0], "series2": [2.0, 4.0, 6.0]}
        axis_labels = {"x": ["A", "B", "C"], "y": ["Low", "Medium", "High"]}
        
        data = QuantitativeData(
            data_points=data_points,
            data_series=data_series,
            axis_labels=axis_labels,
            chart_type="line"
        )
        
        assert data.data_points == data_points
        assert data.data_series == data_series
        assert data.chart_type == "line"
    
    def test_get_data_range(self):
        """Test getting data range for a series."""
        data_series = {"series1": [1.0, 5.0, 3.0, 8.0, 2.0]}
        
        data = QuantitativeData(
            data_points=[],
            data_series=data_series,
            axis_labels={},
            chart_type="bar"
        )
        
        min_val, max_val = data.get_data_range("series1")
        assert min_val == 1.0
        assert max_val == 8.0
    
    def test_get_summary_statistics(self):
        """Test getting summary statistics for a series."""
        data_series = {"series1": [1.0, 2.0, 3.0, 4.0, 5.0]}
        
        data = QuantitativeData(
            data_points=[],
            data_series=data_series,
            axis_labels={},
            chart_type="bar"
        )
        
        stats = data.get_summary_statistics("series1")
        assert stats["mean"] == 3.0
        assert stats["median"] == 3.0
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["count"] == 5
    
    def test_empty_data_validation(self):
        """Test validation of empty data."""
        with pytest.raises(ValueError, match="Must have either data points or data series"):
            QuantitativeData(
                data_points=[],
                data_series={},
                axis_labels={},
                chart_type="bar"
            )
    
    def test_empty_chart_type(self):
        """Test validation of empty chart type."""
        with pytest.raises(ValueError, match="Chart type cannot be empty"):
            QuantitativeData(
                data_points=[{"x": 1, "y": 2}],
                data_series={},
                axis_labels={},
                chart_type=""
            )
    
    def test_nonexistent_series_error(self):
        """Test error handling for nonexistent series."""
        data = QuantitativeData(
            data_points=[],
            data_series={"series1": [1, 2, 3]},
            axis_labels={},
            chart_type="bar"
        )
        
        with pytest.raises(ValueError, match="Series nonexistent not found"):
            data.get_data_range("nonexistent")
        
        with pytest.raises(ValueError, match="Series nonexistent not found"):
            data.get_summary_statistics("nonexistent")


class TestStructuralRelationships:
    """Test cases for StructuralRelationships class."""
    
    def test_valid_structural_relationships_creation(self):
        """Test creating valid structural relationships."""
        nodes = [
            {"id": "node1", "label": "Start"},
            {"id": "node2", "label": "Process"},
            {"id": "node3", "label": "End"}
        ]
        edges = [
            {"source": "node1", "target": "node2", "type": "flow"},
            {"source": "node2", "target": "node3", "type": "flow"}
        ]
        hierarchy_levels = {"node1": 0, "node2": 1, "node3": 2}
        
        relationships = StructuralRelationships(
            nodes=nodes,
            edges=edges,
            hierarchy_levels=hierarchy_levels,
            flow_direction="top-down",
            relationship_types={"flow": "sequential"}
        )
        
        assert relationships.nodes == nodes
        assert relationships.edges == edges
        assert relationships.flow_direction == "top-down"
    
    def test_get_root_nodes(self):
        """Test getting root nodes (no incoming edges)."""
        nodes = [
            {"id": "node1", "label": "Start"},
            {"id": "node2", "label": "Process"},
            {"id": "node3", "label": "End"}
        ]
        edges = [
            {"source": "node1", "target": "node2"},
            {"source": "node2", "target": "node3"}
        ]
        
        relationships = StructuralRelationships(
            nodes=nodes,
            edges=edges,
            hierarchy_levels={},
            flow_direction="top-down",
            relationship_types={}
        )
        
        root_nodes = relationships.get_root_nodes()
        assert len(root_nodes) == 1
        assert root_nodes[0]["id"] == "node1"
    
    def test_get_leaf_nodes(self):
        """Test getting leaf nodes (no outgoing edges)."""
        nodes = [
            {"id": "node1", "label": "Start"},
            {"id": "node2", "label": "Process"},
            {"id": "node3", "label": "End"}
        ]
        edges = [
            {"source": "node1", "target": "node2"},
            {"source": "node2", "target": "node3"}
        ]
        
        relationships = StructuralRelationships(
            nodes=nodes,
            edges=edges,
            hierarchy_levels={},
            flow_direction="top-down",
            relationship_types={}
        )
        
        leaf_nodes = relationships.get_leaf_nodes()
        assert len(leaf_nodes) == 1
        assert leaf_nodes[0]["id"] == "node3"
    
    def test_get_node_connections(self):
        """Test getting node connections."""
        nodes = [
            {"id": "node1"}, {"id": "node2"}, {"id": "node3"}
        ]
        edges = [
            {"source": "node1", "target": "node2"},
            {"source": "node2", "target": "node3"},
            {"source": "node1", "target": "node3"}
        ]
        
        relationships = StructuralRelationships(
            nodes=nodes,
            edges=edges,
            hierarchy_levels={},
            flow_direction="top-down",
            relationship_types={}
        )
        
        # Test node2 connections
        connections = relationships.get_node_connections("node2")
        assert "node1" in connections["incoming"]
        assert "node3" in connections["outgoing"]
        assert len(connections["incoming"]) == 1
        assert len(connections["outgoing"]) == 1
    
    def test_empty_nodes_validation(self):
        """Test validation of empty nodes."""
        with pytest.raises(ValueError, match="Must have at least one node"):
            StructuralRelationships(
                nodes=[],
                edges=[],
                hierarchy_levels={},
                flow_direction="top-down",
                relationship_types={}
            )
    
    def test_empty_flow_direction(self):
        """Test validation of empty flow direction."""
        with pytest.raises(ValueError, match="Flow direction cannot be empty"):
            StructuralRelationships(
                nodes=[{"id": "node1"}],
                edges=[],
                hierarchy_levels={},
                flow_direction="",
                relationship_types={}
            )


class TestMultiModalContext:
    """Test cases for MultiModalContext class."""
    
    def create_sample_document_content(self):
        """Create sample document content for testing."""
        return DocumentContent(
            document_id="doc1",
            text_content="Sample text content",
            raw_text="Sample raw text",
            structured_content={"title": "Test Document"}
        )
    
    def create_sample_research_context(self):
        """Create sample research context for testing."""
        return ResearchContext(
            research_domain="machine_learning",
            research_goals=["understand algorithms", "implement models"]
        )
    
    def test_valid_multimodal_context_creation(self):
        """Test creating valid multi-modal context."""
        doc_content = self.create_sample_document_content()
        research_context = self.create_sample_research_context()
        
        context = MultiModalContext(
            context_id="ctx1",
            document_content=doc_content,
            visual_elements=[],
            user_interaction_history=[],
            research_context=research_context
        )
        
        assert context.context_id == "ctx1"
        assert context.document_content == doc_content
        assert context.research_context == research_context
        assert context.is_valid()
    
    def test_get_visual_elements_by_type(self):
        """Test filtering visual elements by type."""
        doc_content = self.create_sample_document_content()
        research_context = self.create_sample_research_context()
        
        bbox = BoundingBox(x=0, y=0, width=100, height=50)
        chart_element = VisualElement("elem1", VisualElementType.CHART, bbox, 0.9)
        diagram_element = VisualElement("elem2", VisualElementType.DIAGRAM, bbox, 0.8)
        
        context = MultiModalContext(
            context_id="ctx1",
            document_content=doc_content,
            visual_elements=[chart_element, diagram_element],
            user_interaction_history=[],
            research_context=research_context
        )
        
        charts = context.get_visual_elements_by_type(VisualElementType.CHART)
        assert len(charts) == 1
        assert charts[0].element_id == "elem1"
    
    def test_get_recent_interactions(self):
        """Test getting recent user interactions."""
        doc_content = self.create_sample_document_content()
        research_context = self.create_sample_research_context()
        
        # Create interactions with different timestamps
        interactions = []
        for i in range(15):
            interaction = UserInteraction(
                interaction_id=f"int{i}",
                user_id="user1",
                timestamp=datetime.now(),
                interaction_type="click"
            )
            interactions.append(interaction)
        
        context = MultiModalContext(
            context_id="ctx1",
            document_content=doc_content,
            visual_elements=[],
            user_interaction_history=interactions,
            research_context=research_context
        )
        
        recent = context.get_recent_interactions(limit=5)
        assert len(recent) == 5
    
    def test_empty_context_id_validation(self):
        """Test validation of empty context ID."""
        doc_content = self.create_sample_document_content()
        research_context = self.create_sample_research_context()
        
        with pytest.raises(ValueError, match="Context ID cannot be empty"):
            MultiModalContext(
                context_id="",
                document_content=doc_content,
                visual_elements=[],
                user_interaction_history=[],
                research_context=research_context
            )