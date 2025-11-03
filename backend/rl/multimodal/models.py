"""
Data models for multi-modal learning system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from datetime import datetime


class VisualElementType(Enum):
    """Types of visual elements that can be detected."""
    CHART = "chart"
    DIAGRAM = "diagram"
    EQUATION = "equation"
    FIGURE = "figure"
    TABLE = "table"
    GRAPH = "graph"
    FLOWCHART = "flowchart"
    SCREENSHOT = "screenshot"
    UNKNOWN = "unknown"


@dataclass
class BoundingBox:
    """Bounding box coordinates for visual elements."""
    x: float
    y: float
    width: float
    height: float
    
    def __post_init__(self):
        """Validate bounding box coordinates."""
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Width and height must be positive")
        if self.x < 0 or self.y < 0:
            raise ValueError("Coordinates must be non-negative")
    
    def area(self) -> float:
        """Calculate the area of the bounding box."""
        return self.width * self.height
    
    def center(self) -> Tuple[float, float]:
        """Get the center point of the bounding box."""
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    def intersects(self, other: 'BoundingBox') -> bool:
        """Check if this bounding box intersects with another."""
        return not (
            self.x + self.width < other.x or
            other.x + other.width < self.x or
            self.y + self.height < other.y or
            other.y + other.height < self.y
        )


@dataclass
class ElementRelationship:
    """Relationship between visual elements."""
    source_element_id: str
    target_element_id: str
    relationship_type: str  # "contains", "references", "follows", "precedes"
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate relationship data."""
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        if not self.relationship_type:
            raise ValueError("Relationship type cannot be empty")


@dataclass
class VisualElement:
    """Represents a visual element detected in a document."""
    element_id: str
    element_type: VisualElementType
    bounding_box: BoundingBox
    confidence: float
    extracted_data: Optional[Dict[str, Any]] = None
    relationships: List[ElementRelationship] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate visual element data."""
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        if not self.element_id:
            raise ValueError("Element ID cannot be empty")
    
    def add_relationship(self, relationship: ElementRelationship) -> None:
        """Add a relationship to this element."""
        if relationship.source_element_id != self.element_id:
            raise ValueError("Relationship source must match element ID")
        self.relationships.append(relationship)
    
    def get_relationships_by_type(self, relationship_type: str) -> List[ElementRelationship]:
        """Get relationships of a specific type."""
        return [r for r in self.relationships if r.relationship_type == relationship_type]
    
    def is_valid(self) -> bool:
        """Check if the visual element is valid."""
        try:
            return (
                0 <= self.confidence <= 1 and
                self.element_id and
                self.bounding_box.area() > 0
            )
        except Exception:
            return False


@dataclass
class CrossModalRelationship:
    """Relationship between text and visual content."""
    text_span: Tuple[int, int]  # Start and end positions in text
    visual_element_id: str
    relationship_type: str  # "describes", "references", "explains", "summarizes"
    confidence: float
    semantic_similarity: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate cross-modal relationship data."""
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        if not 0 <= self.semantic_similarity <= 1:
            raise ValueError("Semantic similarity must be between 0 and 1")
        if self.text_span[0] < 0 or self.text_span[1] < self.text_span[0]:
            raise ValueError("Invalid text span")


@dataclass
class TextFeatures:
    """Text features for multi-modal integration."""
    embeddings: np.ndarray
    tokens: List[str]
    semantic_features: Dict[str, float]
    linguistic_features: Dict[str, float]
    domain_features: Dict[str, float]
    
    def __post_init__(self):
        """Validate text features."""
        if self.embeddings.size == 0:
            raise ValueError("Embeddings cannot be empty")
        if not self.tokens:
            raise ValueError("Tokens cannot be empty")


@dataclass
class VisualFeatures:
    """Visual features extracted from images."""
    visual_embeddings: np.ndarray
    color_features: Dict[str, float]
    texture_features: Dict[str, float]
    shape_features: Dict[str, float]
    spatial_features: Dict[str, float]
    content_features: Dict[str, Any]
    
    def __post_init__(self):
        """Validate visual features."""
        if self.visual_embeddings.size == 0:
            raise ValueError("Visual embeddings cannot be empty")


@dataclass
class MultiModalFeatures:
    """Integrated features from text and visual content."""
    text_features: TextFeatures
    visual_features: List[VisualFeatures]
    cross_modal_relationships: List[CrossModalRelationship]
    integrated_embedding: np.ndarray
    confidence_scores: Dict[str, float]
    fusion_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate multi-modal features."""
        if self.integrated_embedding.size == 0:
            raise ValueError("Integrated embedding cannot be empty")
        if not self.visual_features:
            raise ValueError("Visual features cannot be empty")
        
        # Validate confidence scores
        for key, score in self.confidence_scores.items():
            if not 0 <= score <= 1:
                raise ValueError(f"Confidence score for {key} must be between 0 and 1")
    
    def get_overall_confidence(self) -> float:
        """Calculate overall confidence score."""
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores.values()) / len(self.confidence_scores)
    
    def is_high_quality(self, threshold: float = 0.7) -> bool:
        """Check if features meet quality threshold."""
        return self.get_overall_confidence() >= threshold


@dataclass
class DocumentContent:
    """Content of a document for multi-modal processing."""
    document_id: str
    text_content: str
    raw_text: str
    structured_content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate document content."""
        if not self.document_id:
            raise ValueError("Document ID cannot be empty")
        if not self.text_content and not self.raw_text:
            raise ValueError("Document must have some text content")


@dataclass
class ResearchContext:
    """Research context for multi-modal processing."""
    research_domain: str
    research_goals: List[str]
    current_task: Optional[str] = None
    related_documents: List[str] = field(default_factory=list)
    user_expertise_level: float = 0.5
    context_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate research context."""
        if not self.research_domain:
            raise ValueError("Research domain cannot be empty")
        if not 0 <= self.user_expertise_level <= 1:
            raise ValueError("User expertise level must be between 0 and 1")


@dataclass
class UserInteraction:
    """User interaction data for multi-modal learning."""
    interaction_id: str
    user_id: str
    timestamp: datetime
    interaction_type: str  # "click", "hover", "scroll", "zoom", "select"
    target_element_id: Optional[str] = None
    interaction_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate user interaction data."""
        if not self.interaction_id or not self.user_id:
            raise ValueError("Interaction ID and User ID cannot be empty")
        if not self.interaction_type:
            raise ValueError("Interaction type cannot be empty")


@dataclass
class MultiModalContext:
    """Complete context for multi-modal processing."""
    context_id: str
    document_content: DocumentContent
    visual_elements: List[VisualElement]
    user_interaction_history: List[UserInteraction]
    research_context: ResearchContext
    processing_timestamp: datetime = field(default_factory=datetime.now)
    context_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate multi-modal context."""
        if not self.context_id:
            raise ValueError("Context ID cannot be empty")
    
    def get_visual_elements_by_type(self, element_type: VisualElementType) -> List[VisualElement]:
        """Get visual elements of a specific type."""
        return [elem for elem in self.visual_elements if elem.element_type == element_type]
    
    def get_recent_interactions(self, limit: int = 10) -> List[UserInteraction]:
        """Get recent user interactions."""
        sorted_interactions = sorted(
            self.user_interaction_history,
            key=lambda x: x.timestamp,
            reverse=True
        )
        return sorted_interactions[:limit]
    
    def is_valid(self) -> bool:
        """Check if the context is valid."""
        try:
            return (
                self.context_id and
                self.document_content.document_id and
                all(elem.is_valid() for elem in self.visual_elements)
            )
        except Exception:
            return False


@dataclass
class QuantitativeData:
    """Quantitative data extracted from charts and graphs."""
    data_points: List[Dict[str, float]]
    data_series: Dict[str, List[float]]
    axis_labels: Dict[str, List[str]]
    chart_type: str
    units: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate quantitative data."""
        if not self.data_points and not self.data_series:
            raise ValueError("Must have either data points or data series")
        if not self.chart_type:
            raise ValueError("Chart type cannot be empty")
    
    def get_data_range(self, series_name: str) -> Tuple[float, float]:
        """Get the range of values for a data series."""
        if series_name not in self.data_series:
            raise ValueError(f"Series {series_name} not found")
        
        values = self.data_series[series_name]
        return (min(values), max(values))
    
    def get_summary_statistics(self, series_name: str) -> Dict[str, float]:
        """Get summary statistics for a data series."""
        if series_name not in self.data_series:
            raise ValueError(f"Series {series_name} not found")
        
        values = self.data_series[series_name]
        return {
            "mean": np.mean(values),
            "median": np.median(values),
            "std": np.std(values),
            "min": np.min(values),
            "max": np.max(values),
            "count": len(values)
        }


@dataclass
class StructuralRelationships:
    """Structural relationships in diagrams and flowcharts."""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    hierarchy_levels: Dict[str, int]
    flow_direction: str  # "top-down", "left-right", "circular", "mixed"
    relationship_types: Dict[str, str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate structural relationships."""
        if not self.nodes:
            raise ValueError("Must have at least one node")
        if not self.flow_direction:
            raise ValueError("Flow direction cannot be empty")
    
    def get_root_nodes(self) -> List[Dict[str, Any]]:
        """Get nodes that have no incoming edges."""
        incoming_targets = {edge.get("target") for edge in self.edges}
        return [node for node in self.nodes if node.get("id") not in incoming_targets]
    
    def get_leaf_nodes(self) -> List[Dict[str, Any]]:
        """Get nodes that have no outgoing edges."""
        outgoing_sources = {edge.get("source") for edge in self.edges}
        return [node for node in self.nodes if node.get("id") not in outgoing_sources]
    
    def get_node_connections(self, node_id: str) -> Dict[str, List[str]]:
        """Get incoming and outgoing connections for a node."""
        incoming = [edge.get("source") for edge in self.edges if edge.get("target") == node_id]
        outgoing = [edge.get("target") for edge in self.edges if edge.get("source") == node_id]
        
        return {
            "incoming": [conn for conn in incoming if conn is not None],
            "outgoing": [conn for conn in outgoing if conn is not None]
        }