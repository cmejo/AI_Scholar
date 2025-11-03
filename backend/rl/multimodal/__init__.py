"""
Multi-modal learning components for the RL system.
"""

from .models import (
    VisualElement,
    VisualElementType,
    MultiModalFeatures,
    MultiModalContext,
    BoundingBox,
    ElementRelationship,
    CrossModalRelationship
)

from .visual_processor import VisualContentProcessor
from .feature_integrator import MultiModalFeatureIntegrator
from .learning_model import MultiModalLearningModel

__all__ = [
    'VisualElement',
    'VisualElementType', 
    'MultiModalFeatures',
    'MultiModalContext',
    'BoundingBox',
    'ElementRelationship',
    'CrossModalRelationship',
    'VisualContentProcessor',
    'MultiModalFeatureIntegrator',
    'MultiModalLearningModel'
]