"""
Multi-modal feature integration system for combining text and visual features.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
import numpy as np
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

from .models import (
    MultiModalFeatures,
    TextFeatures,
    VisualFeatures,
    CrossModalRelationship,
    VisualElement,
    MultiModalContext
)

logger = logging.getLogger(__name__)


class IntegrationStrategy(Enum):
    """Different strategies for integrating multi-modal features."""
    CONCATENATION = "concatenation"
    ATTENTION_FUSION = "attention_fusion"
    CROSS_MODAL_ALIGNMENT = "cross_modal_alignment"
    HIERARCHICAL_FUSION = "hierarchical_fusion"
    WEIGHTED_COMBINATION = "weighted_combination"


class AttentionMechanism(Enum):
    """Types of attention mechanisms for feature fusion."""
    SELF_ATTENTION = "self_attention"
    CROSS_ATTENTION = "cross_attention"
    MULTI_HEAD_ATTENTION = "multi_head_attention"
    SCALED_DOT_PRODUCT = "scaled_dot_product"


@dataclass
class IntegrationConfig:
    """Configuration for multi-modal feature integration."""
    strategy: IntegrationStrategy = IntegrationStrategy.ATTENTION_FUSION
    attention_mechanism: AttentionMechanism = AttentionMechanism.CROSS_ATTENTION
    text_weight: float = 0.5
    visual_weight: float = 0.5
    embedding_dim: int = 512
    num_attention_heads: int = 8
    dropout_rate: float = 0.1
    temperature: float = 1.0
    normalize_features: bool = True
    use_positional_encoding: bool = True


class TextProcessor:
    """Processes and prepares text features for integration."""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
    
    async def process_text_features(self, text_features: TextFeatures) -> Dict[str, np.ndarray]:
        """Process text features for integration."""
        processed = {}
        
        # Normalize embeddings if required
        embeddings = text_features.embeddings
        if self.config.normalize_features:
            embeddings = await self._normalize_embeddings(embeddings)
        
        processed['embeddings'] = embeddings
        
        # Process semantic features
        semantic_vector = await self._vectorize_features(text_features.semantic_features)
        processed['semantic'] = semantic_vector
        
        # Process linguistic features
        linguistic_vector = await self._vectorize_features(text_features.linguistic_features)
        processed['linguistic'] = linguistic_vector
        
        # Process domain features
        domain_vector = await self._vectorize_features(text_features.domain_features)
        processed['domain'] = domain_vector
        
        # Create token-level features
        token_features = await self._create_token_features(text_features.tokens)
        processed['tokens'] = token_features
        
        return processed
    
    async def _normalize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """Normalize embeddings to unit length."""
        norm = np.linalg.norm(embeddings)
        if norm > 0:
            return embeddings / norm
        return embeddings
    
    async def _vectorize_features(self, features: Dict[str, float]) -> np.ndarray:
        """Convert feature dictionary to vector."""
        if not features:
            return np.zeros(10)  # Default size for empty features
        
        # Sort keys for consistent ordering
        sorted_keys = sorted(features.keys())
        vector = np.array([features[key] for key in sorted_keys], dtype=np.float32)
        
        # Pad or truncate to fixed size
        target_size = 10
        if len(vector) < target_size:
            vector = np.pad(vector, (0, target_size - len(vector)), 'constant')
        elif len(vector) > target_size:
            vector = vector[:target_size]
        
        return vector
    
    async def _create_token_features(self, tokens: List[str]) -> np.ndarray:
        """Create features from token list."""
        # Simple token-based features
        features = {
            'num_tokens': len(tokens),
            'avg_token_length': np.mean([len(token) for token in tokens]) if tokens else 0,
            'unique_tokens_ratio': len(set(tokens)) / len(tokens) if tokens else 0,
            'has_numbers': any(any(c.isdigit() for c in token) for token in tokens),
            'has_punctuation': any(any(not c.isalnum() for c in token) for token in tokens)
        }
        
        return np.array(list(features.values()), dtype=np.float32)


class VisualProcessor:
    """Processes and prepares visual features for integration."""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
    
    async def process_visual_features(self, visual_features_list: List[VisualFeatures]) -> Dict[str, np.ndarray]:
        """Process visual features for integration."""
        processed = {}
        
        if not visual_features_list:
            # Return empty features
            return {
                'embeddings': np.zeros(self.config.embedding_dim),
                'color': np.zeros(10),
                'texture': np.zeros(10),
                'shape': np.zeros(10),
                'spatial': np.zeros(10),
                'content': np.zeros(5)
            }
        
        # Aggregate multiple visual features
        aggregated_embeddings = await self._aggregate_visual_embeddings(visual_features_list)
        if self.config.normalize_features:
            aggregated_embeddings = await self._normalize_embeddings(aggregated_embeddings)
        
        processed['embeddings'] = aggregated_embeddings
        
        # Aggregate other feature types
        processed['color'] = await self._aggregate_feature_dicts([vf.color_features for vf in visual_features_list])
        processed['texture'] = await self._aggregate_feature_dicts([vf.texture_features for vf in visual_features_list])
        processed['shape'] = await self._aggregate_feature_dicts([vf.shape_features for vf in visual_features_list])
        processed['spatial'] = await self._aggregate_feature_dicts([vf.spatial_features for vf in visual_features_list])
        processed['content'] = await self._aggregate_content_features([vf.content_features for vf in visual_features_list])
        
        return processed
    
    async def _aggregate_visual_embeddings(self, visual_features_list: List[VisualFeatures]) -> np.ndarray:
        """Aggregate visual embeddings from multiple sources."""
        embeddings = [vf.visual_embeddings for vf in visual_features_list]
        
        if not embeddings:
            return np.zeros(self.config.embedding_dim)
        
        # Ensure all embeddings have the same dimension
        target_dim = self.config.embedding_dim
        normalized_embeddings = []
        
        for emb in embeddings:
            if len(emb) < target_dim:
                # Pad with zeros
                padded = np.pad(emb, (0, target_dim - len(emb)), 'constant')
                normalized_embeddings.append(padded)
            elif len(emb) > target_dim:
                # Truncate
                normalized_embeddings.append(emb[:target_dim])
            else:
                normalized_embeddings.append(emb)
        
        # Average the embeddings
        return np.mean(normalized_embeddings, axis=0)
    
    async def _aggregate_feature_dicts(self, feature_dicts: List[Dict[str, float]]) -> np.ndarray:
        """Aggregate feature dictionaries into a single vector."""
        if not feature_dicts or not any(feature_dicts):
            return np.zeros(10)
        
        # Collect all unique keys
        all_keys = set()
        for fd in feature_dicts:
            if fd:
                all_keys.update(fd.keys())
        
        if not all_keys:
            return np.zeros(10)
        
        # Sort keys for consistency
        sorted_keys = sorted(all_keys)
        
        # Aggregate values
        aggregated_values = []
        for key in sorted_keys:
            values = [fd.get(key, 0.0) for fd in feature_dicts if fd]
            aggregated_values.append(np.mean(values) if values else 0.0)
        
        # Convert to fixed-size vector
        vector = np.array(aggregated_values, dtype=np.float32)
        target_size = 10
        
        if len(vector) < target_size:
            vector = np.pad(vector, (0, target_size - len(vector)), 'constant')
        elif len(vector) > target_size:
            vector = vector[:target_size]
        
        return vector
    
    async def _aggregate_content_features(self, content_features_list: List[Dict[str, Any]]) -> np.ndarray:
        """Aggregate content features into a vector."""
        if not content_features_list or not any(content_features_list):
            return np.zeros(5)
        
        # Extract boolean and numeric features
        features = {
            'has_text': 0.0,
            'has_lines': 0.0,
            'has_shapes': 0.0,
            'complexity': 0.0,
            'num_elements': 0.0
        }
        
        valid_features = [cf for cf in content_features_list if cf]
        
        if valid_features:
            # Aggregate boolean features as ratios
            features['has_text'] = sum(cf.get('has_text', False) for cf in valid_features) / len(valid_features)
            features['has_lines'] = sum(cf.get('has_lines', False) for cf in valid_features) / len(valid_features)
            features['has_shapes'] = sum(cf.get('has_shapes', False) for cf in valid_features) / len(valid_features)
            
            # Aggregate numeric features as averages
            complexity_values = [cf.get('complexity', 0.0) for cf in valid_features]
            features['complexity'] = np.mean(complexity_values) if complexity_values else 0.0
            
            features['num_elements'] = len(valid_features)
        
        return np.array(list(features.values()), dtype=np.float32)
    
    async def _normalize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """Normalize embeddings to unit length."""
        norm = np.linalg.norm(embeddings)
        if norm > 0:
            return embeddings / norm
        return embeddings


class CrossModalAligner:
    """Aligns and finds relationships between text and visual features."""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
    
    async def find_cross_modal_relationships(
        self, 
        text_content: str, 
        visual_elements: List[VisualElement],
        text_features: TextFeatures,
        visual_features_list: List[VisualFeatures]
    ) -> List[CrossModalRelationship]:
        """Find relationships between text and visual content."""
        relationships = []
        
        # Simple keyword-based alignment
        relationships.extend(await self._keyword_based_alignment(text_content, visual_elements))
        
        # Semantic similarity alignment
        relationships.extend(await self._semantic_similarity_alignment(
            text_features, visual_features_list, visual_elements
        ))
        
        # Positional alignment (if applicable)
        relationships.extend(await self._positional_alignment(text_content, visual_elements))
        
        return relationships
    
    async def _keyword_based_alignment(self, text_content: str, visual_elements: List[VisualElement]) -> List[CrossModalRelationship]:
        """Find relationships based on keywords in text."""
        relationships = []
        
        # Define visual element keywords
        visual_keywords = {
            'chart': ['chart', 'graph', 'plot', 'data', 'figure'],
            'diagram': ['diagram', 'flowchart', 'process', 'flow', 'structure'],
            'equation': ['equation', 'formula', 'mathematical', 'calculation'],
            'figure': ['figure', 'image', 'picture', 'illustration'],
            'table': ['table', 'data', 'rows', 'columns']
        }
        
        text_lower = text_content.lower()
        
        for element in visual_elements:
            element_type = element.element_type.value
            keywords = visual_keywords.get(element_type, [])
            
            for keyword in keywords:
                # Find keyword positions in text
                start_pos = 0
                while True:
                    pos = text_lower.find(keyword, start_pos)
                    if pos == -1:
                        break
                    
                    # Create relationship
                    relationship = CrossModalRelationship(
                        text_span=(pos, pos + len(keyword)),
                        visual_element_id=element.element_id,
                        relationship_type="describes",
                        confidence=0.6,
                        semantic_similarity=0.7
                    )
                    relationships.append(relationship)
                    
                    start_pos = pos + 1
        
        return relationships
    
    async def _semantic_similarity_alignment(
        self, 
        text_features: TextFeatures, 
        visual_features_list: List[VisualFeatures],
        visual_elements: List[VisualElement]
    ) -> List[CrossModalRelationship]:
        """Find relationships based on semantic similarity."""
        relationships = []
        
        if not visual_features_list or not visual_elements:
            return relationships
        
        # Calculate semantic similarity between text and visual features
        text_embedding = text_features.embeddings
        
        for i, (visual_features, visual_element) in enumerate(zip(visual_features_list, visual_elements)):
            visual_embedding = visual_features.visual_embeddings
            
            # Calculate cosine similarity
            similarity = await self._cosine_similarity(text_embedding, visual_embedding)
            
            if similarity > 0.3:  # Threshold for meaningful similarity
                # Create relationship for entire text (simplified)
                relationship = CrossModalRelationship(
                    text_span=(0, len(' '.join(text_features.tokens))),
                    visual_element_id=visual_element.element_id,
                    relationship_type="relates_to",
                    confidence=min(0.9, similarity + 0.1),
                    semantic_similarity=similarity
                )
                relationships.append(relationship)
        
        return relationships
    
    async def _positional_alignment(self, text_content: str, visual_elements: List[VisualElement]) -> List[CrossModalRelationship]:
        """Find relationships based on positional references in text."""
        relationships = []
        
        # Look for positional references
        position_keywords = {
            'above': ['above', 'top', 'upper'],
            'below': ['below', 'bottom', 'lower'],
            'left': ['left', 'leftward'],
            'right': ['right', 'rightward'],
            'center': ['center', 'middle', 'central']
        }
        
        text_lower = text_content.lower()
        
        for position, keywords in position_keywords.items():
            for keyword in keywords:
                pos = text_lower.find(keyword)
                if pos != -1:
                    # Find the most appropriate visual element based on position
                    # This is simplified - in reality, would need layout analysis
                    if visual_elements:
                        # Just use the first element as an example
                        element = visual_elements[0]
                        
                        relationship = CrossModalRelationship(
                            text_span=(pos, pos + len(keyword)),
                            visual_element_id=element.element_id,
                            relationship_type="references",
                            confidence=0.5,
                            semantic_similarity=0.4
                        )
                        relationships.append(relationship)
        
        return relationships
    
    async def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        # Ensure vectors have the same dimension
        min_dim = min(len(vec1), len(vec2))
        vec1_norm = vec1[:min_dim]
        vec2_norm = vec2[:min_dim]
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1_norm, vec2_norm)
        norm1 = np.linalg.norm(vec1_norm)
        norm2 = np.linalg.norm(vec2_norm)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))


class AttentionFusion:
    """Implements attention-based fusion mechanisms."""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
    
    async def apply_attention_fusion(
        self, 
        text_features: Dict[str, np.ndarray], 
        visual_features: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """Apply attention-based fusion to combine features."""
        
        if self.config.attention_mechanism == AttentionMechanism.CROSS_ATTENTION:
            return await self._cross_attention_fusion(text_features, visual_features)
        elif self.config.attention_mechanism == AttentionMechanism.SELF_ATTENTION:
            return await self._self_attention_fusion(text_features, visual_features)
        elif self.config.attention_mechanism == AttentionMechanism.MULTI_HEAD_ATTENTION:
            return await self._multi_head_attention_fusion(text_features, visual_features)
        else:
            return await self._scaled_dot_product_fusion(text_features, visual_features)
    
    async def _cross_attention_fusion(
        self, 
        text_features: Dict[str, np.ndarray], 
        visual_features: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """Cross-attention fusion between text and visual features."""
        
        # Get main embeddings
        text_emb = text_features.get('embeddings', np.zeros(self.config.embedding_dim))
        visual_emb = visual_features.get('embeddings', np.zeros(self.config.embedding_dim))
        
        # Ensure same dimension
        target_dim = self.config.embedding_dim
        text_emb = await self._resize_vector(text_emb, target_dim)
        visual_emb = await self._resize_vector(visual_emb, target_dim)
        
        # Calculate attention weights
        attention_scores = await self._calculate_attention_scores(text_emb, visual_emb)
        
        # Apply attention to visual features
        attended_visual = attention_scores * visual_emb
        
        # Combine with text features
        combined = self.config.text_weight * text_emb + self.config.visual_weight * attended_visual
        
        # Add other feature types
        other_features = await self._combine_other_features(text_features, visual_features)
        
        # Concatenate all features
        final_features = np.concatenate([combined, other_features])
        
        return final_features
    
    async def _self_attention_fusion(
        self, 
        text_features: Dict[str, np.ndarray], 
        visual_features: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """Self-attention fusion within combined features."""
        
        # Combine all features first
        all_features = []
        
        # Add text features
        for key, features in text_features.items():
            all_features.append(features.flatten())
        
        # Add visual features
        for key, features in visual_features.items():
            all_features.append(features.flatten())
        
        # Create feature matrix
        feature_matrix = np.array(all_features)
        
        # Apply self-attention
        attention_weights = await self._self_attention_weights(feature_matrix)
        
        # Apply weights and combine
        weighted_features = attention_weights @ feature_matrix
        
        # Flatten to single vector
        return weighted_features.flatten()
    
    async def _multi_head_attention_fusion(
        self, 
        text_features: Dict[str, np.ndarray], 
        visual_features: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """Multi-head attention fusion."""
        
        num_heads = self.config.num_attention_heads
        head_results = []
        
        # Apply attention with multiple heads
        for head in range(num_heads):
            # Each head focuses on different aspects
            head_result = await self._single_head_attention(
                text_features, visual_features, head
            )
            head_results.append(head_result)
        
        # Combine head results
        combined_result = np.mean(head_results, axis=0)
        
        return combined_result
    
    async def _scaled_dot_product_fusion(
        self, 
        text_features: Dict[str, np.ndarray], 
        visual_features: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """Scaled dot-product attention fusion."""
        
        text_emb = text_features.get('embeddings', np.zeros(self.config.embedding_dim))
        visual_emb = visual_features.get('embeddings', np.zeros(self.config.embedding_dim))
        
        # Ensure same dimension
        target_dim = self.config.embedding_dim
        text_emb = await self._resize_vector(text_emb, target_dim)
        visual_emb = await self._resize_vector(visual_emb, target_dim)
        
        # Scaled dot-product attention
        scale = np.sqrt(target_dim)
        attention_score = np.dot(text_emb, visual_emb) / scale
        
        # Apply temperature
        attention_score = attention_score / self.config.temperature
        
        # Softmax (simplified for single score)
        attention_weight = 1.0 / (1.0 + np.exp(-attention_score))
        
        # Combine features
        combined = (
            self.config.text_weight * text_emb + 
            self.config.visual_weight * attention_weight * visual_emb
        )
        
        # Add other features
        other_features = await self._combine_other_features(text_features, visual_features)
        
        return np.concatenate([combined, other_features])
    
    async def _calculate_attention_scores(self, query: np.ndarray, key: np.ndarray) -> float:
        """Calculate attention scores between query and key."""
        # Simplified attention score calculation
        dot_product = np.dot(query, key)
        norm_product = np.linalg.norm(query) * np.linalg.norm(key)
        
        if norm_product == 0:
            return 0.0
        
        return dot_product / norm_product
    
    async def _self_attention_weights(self, feature_matrix: np.ndarray) -> np.ndarray:
        """Calculate self-attention weights."""
        # Simplified self-attention
        num_features = feature_matrix.shape[0]
        
        # Calculate pairwise similarities
        similarities = np.zeros((num_features, num_features))
        for i in range(num_features):
            for j in range(num_features):
                similarities[i, j] = await self._calculate_attention_scores(
                    feature_matrix[i], feature_matrix[j]
                )
        
        # Apply softmax to each row
        attention_weights = np.zeros_like(similarities)
        for i in range(num_features):
            exp_scores = np.exp(similarities[i] / self.config.temperature)
            attention_weights[i] = exp_scores / np.sum(exp_scores)
        
        return attention_weights
    
    async def _single_head_attention(
        self, 
        text_features: Dict[str, np.ndarray], 
        visual_features: Dict[str, np.ndarray],
        head_idx: int
    ) -> np.ndarray:
        """Single head attention computation."""
        # Simplified single head - just use cross attention with different weights
        text_emb = text_features.get('embeddings', np.zeros(self.config.embedding_dim))
        visual_emb = visual_features.get('embeddings', np.zeros(self.config.embedding_dim))
        
        # Different weight for each head
        head_weight = (head_idx + 1) / self.config.num_attention_heads
        
        # Apply head-specific transformation (simplified)
        transformed_text = text_emb * head_weight
        transformed_visual = visual_emb * (1 - head_weight)
        
        return transformed_text + transformed_visual
    
    async def _combine_other_features(
        self, 
        text_features: Dict[str, np.ndarray], 
        visual_features: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """Combine non-embedding features."""
        other_features = []
        
        # Text features (excluding embeddings)
        for key, features in text_features.items():
            if key != 'embeddings':
                other_features.append(features.flatten())
        
        # Visual features (excluding embeddings)
        for key, features in visual_features.items():
            if key != 'embeddings':
                other_features.append(features.flatten())
        
        if other_features:
            return np.concatenate(other_features)
        else:
            return np.array([])
    
    async def _resize_vector(self, vector: np.ndarray, target_size: int) -> np.ndarray:
        """Resize vector to target size."""
        if len(vector) < target_size:
            return np.pad(vector, (0, target_size - len(vector)), 'constant')
        elif len(vector) > target_size:
            return vector[:target_size]
        else:
            return vector


class MultiModalFeatureIntegrator:
    """Main class for integrating multi-modal features."""
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        self.config = config or IntegrationConfig()
        self.text_processor = TextProcessor(self.config)
        self.visual_processor = VisualProcessor(self.config)
        self.cross_modal_aligner = CrossModalAligner(self.config)
        self.attention_fusion = AttentionFusion(self.config)
    
    async def integrate_features(
        self, 
        text_features: TextFeatures, 
        visual_features: List[VisualFeatures]
    ) -> MultiModalFeatures:
        """Integrate text and visual features into unified representation."""
        
        try:
            # Process individual feature types
            processed_text = await self.text_processor.process_text_features(text_features)
            processed_visual = await self.visual_processor.process_visual_features(visual_features)
            
            # Apply integration strategy
            if self.config.strategy == IntegrationStrategy.ATTENTION_FUSION:
                integrated_embedding = await self.attention_fusion.apply_attention_fusion(
                    processed_text, processed_visual
                )
            elif self.config.strategy == IntegrationStrategy.CONCATENATION:
                integrated_embedding = await self._concatenation_fusion(processed_text, processed_visual)
            elif self.config.strategy == IntegrationStrategy.WEIGHTED_COMBINATION:
                integrated_embedding = await self._weighted_combination_fusion(processed_text, processed_visual)
            else:
                # Default to concatenation
                integrated_embedding = await self._concatenation_fusion(processed_text, processed_visual)
            
            # Calculate confidence scores
            confidence_scores = await self._calculate_confidence_scores(
                text_features, visual_features, integrated_embedding
            )
            
            # Create cross-modal relationships (empty for now, would need context)
            cross_modal_relationships = []
            
            return MultiModalFeatures(
                text_features=text_features,
                visual_features=visual_features,
                cross_modal_relationships=cross_modal_relationships,
                integrated_embedding=integrated_embedding,
                confidence_scores=confidence_scores,
                fusion_metadata={
                    "integration_strategy": self.config.strategy.value,
                    "attention_mechanism": self.config.attention_mechanism.value,
                    "text_weight": self.config.text_weight,
                    "visual_weight": self.config.visual_weight,
                    "embedding_dimension": len(integrated_embedding),
                    "processing_timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error integrating features: {str(e)}")
            raise
    
    async def create_cross_modal_embeddings(
        self, 
        features: MultiModalFeatures
    ) -> np.ndarray:
        """Create cross-modal embeddings from integrated features."""
        
        # Use the integrated embedding as the cross-modal representation
        cross_modal_embedding = features.integrated_embedding
        
        # Apply additional transformations if needed
        if self.config.normalize_features:
            norm = np.linalg.norm(cross_modal_embedding)
            if norm > 0:
                cross_modal_embedding = cross_modal_embedding / norm
        
        return cross_modal_embedding
    
    async def find_cross_modal_relationships_with_context(
        self, 
        context: MultiModalContext
    ) -> List[CrossModalRelationship]:
        """Find cross-modal relationships using full context."""
        
        text_content = context.document_content.text_content
        visual_elements = context.visual_elements
        
        # Extract features from context (simplified)
        # In practice, these would be extracted from the document
        if hasattr(context, 'text_features') and hasattr(context, 'visual_features'):
            text_features = context.text_features
            visual_features_list = context.visual_features
        else:
            # Create dummy features for demonstration
            text_features = TextFeatures(
                embeddings=np.random.rand(256),
                tokens=text_content.split(),
                semantic_features={},
                linguistic_features={},
                domain_features={}
            )
            visual_features_list = []
        
        return await self.cross_modal_aligner.find_cross_modal_relationships(
            text_content, visual_elements, text_features, visual_features_list
        )
    
    async def _concatenation_fusion(
        self, 
        text_features: Dict[str, np.ndarray], 
        visual_features: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """Simple concatenation fusion."""
        all_features = []
        
        # Add text features
        for features in text_features.values():
            all_features.append(features.flatten())
        
        # Add visual features
        for features in visual_features.values():
            all_features.append(features.flatten())
        
        return np.concatenate(all_features)
    
    async def _weighted_combination_fusion(
        self, 
        text_features: Dict[str, np.ndarray], 
        visual_features: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """Weighted combination fusion."""
        # Get main embeddings
        text_emb = text_features.get('embeddings', np.zeros(self.config.embedding_dim))
        visual_emb = visual_features.get('embeddings', np.zeros(self.config.embedding_dim))
        
        # Ensure same dimension
        target_dim = min(len(text_emb), len(visual_emb), self.config.embedding_dim)
        text_emb = text_emb[:target_dim]
        visual_emb = visual_emb[:target_dim]
        
        # Weighted combination
        combined_emb = (
            self.config.text_weight * text_emb + 
            self.config.visual_weight * visual_emb
        )
        
        # Add other features
        other_features = []
        for key, features in text_features.items():
            if key != 'embeddings':
                other_features.append(features.flatten())
        
        for key, features in visual_features.items():
            if key != 'embeddings':
                other_features.append(features.flatten())
        
        if other_features:
            return np.concatenate([combined_emb] + other_features)
        else:
            return combined_emb
    
    async def _calculate_confidence_scores(
        self, 
        text_features: TextFeatures, 
        visual_features: List[VisualFeatures],
        integrated_embedding: np.ndarray
    ) -> Dict[str, float]:
        """Calculate confidence scores for the integration."""
        
        confidence_scores = {}
        
        # Text confidence based on feature quality
        text_confidence = 0.8  # Base confidence
        if len(text_features.tokens) > 0:
            text_confidence = min(1.0, text_confidence + 0.1)
        if text_features.semantic_features:
            text_confidence = min(1.0, text_confidence + 0.1)
        
        confidence_scores['text'] = text_confidence
        
        # Visual confidence based on number and quality of visual features
        if visual_features:
            visual_confidence = np.mean([0.8 for _ in visual_features])  # Base confidence
            confidence_scores['visual'] = float(visual_confidence)
        else:
            confidence_scores['visual'] = 0.0
        
        # Integration confidence based on embedding quality
        embedding_norm = np.linalg.norm(integrated_embedding)
        integration_confidence = min(1.0, embedding_norm / 10.0)  # Normalize by expected range
        confidence_scores['integration'] = float(integration_confidence)
        
        # Overall confidence
        confidence_scores['overall'] = np.mean(list(confidence_scores.values()))
        
        return confidence_scores