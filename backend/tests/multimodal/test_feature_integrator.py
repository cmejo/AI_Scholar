"""
Unit tests for multi-modal feature integration system.
"""

import pytest
import numpy as np
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from backend.rl.multimodal.feature_integrator import (
    MultiModalFeatureIntegrator,
    TextProcessor,
    VisualProcessor,
    CrossModalAligner,
    AttentionFusion,
    IntegrationConfig,
    IntegrationStrategy,
    AttentionMechanism
)
from backend.rl.multimodal.models import (
    TextFeatures,
    VisualFeatures,
    MultiModalFeatures,
    CrossModalRelationship,
    VisualElement,
    VisualElementType,
    BoundingBox,
    MultiModalContext,
    DocumentContent,
    ResearchContext
)


class TestIntegrationConfig:
    """Test cases for IntegrationConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = IntegrationConfig()
        
        assert config.strategy == IntegrationStrategy.ATTENTION_FUSION
        assert config.attention_mechanism == AttentionMechanism.CROSS_ATTENTION
        assert config.text_weight == 0.5
        assert config.visual_weight == 0.5
        assert config.embedding_dim == 512
        assert config.num_attention_heads == 8
        assert config.dropout_rate == 0.1
        assert config.temperature == 1.0
        assert config.normalize_features is True
        assert config.use_positional_encoding is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = IntegrationConfig(
            strategy=IntegrationStrategy.CONCATENATION,
            text_weight=0.7,
            visual_weight=0.3,
            embedding_dim=256
        )
        
        assert config.strategy == IntegrationStrategy.CONCATENATION
        assert config.text_weight == 0.7
        assert config.visual_weight == 0.3
        assert config.embedding_dim == 256


class TestTextProcessor:
    """Test cases for TextProcessor class."""
    
    def create_sample_text_features(self):
        """Create sample text features for testing."""
        return TextFeatures(
            embeddings=np.random.rand(100),
            tokens=["hello", "world", "test"],
            semantic_features={"sentiment": 0.8, "complexity": 0.6},
            linguistic_features={"pos_tags": 0.7, "syntax_score": 0.9},
            domain_features={"technical": 0.8, "academic": 0.6}
        )
    
    @pytest.mark.asyncio
    async def test_process_text_features(self):
        """Test text feature processing."""
        config = IntegrationConfig()
        processor = TextProcessor(config)
        text_features = self.create_sample_text_features()
        
        processed = await processor.process_text_features(text_features)
        
        # Check that all expected keys are present
        expected_keys = ['embeddings', 'semantic', 'linguistic', 'domain', 'tokens']
        for key in expected_keys:
            assert key in processed
            assert isinstance(processed[key], np.ndarray)
        
        # Check embeddings are normalized if config requires it
        if config.normalize_features:
            norm = np.linalg.norm(processed['embeddings'])
            assert abs(norm - 1.0) < 1e-6  # Should be unit length
    
    @pytest.mark.asyncio
    async def test_normalize_embeddings(self):
        """Test embedding normalization."""
        config = IntegrationConfig()
        processor = TextProcessor(config)
        
        # Test with non-zero vector
        embeddings = np.array([3.0, 4.0, 0.0])
        normalized = await processor._normalize_embeddings(embeddings)
        
        # Should be unit length
        norm = np.linalg.norm(normalized)
        assert abs(norm - 1.0) < 1e-6
        
        # Test with zero vector
        zero_embeddings = np.zeros(5)
        normalized_zero = await processor._normalize_embeddings(zero_embeddings)
        assert np.array_equal(normalized_zero, zero_embeddings)
    
    @pytest.mark.asyncio
    async def test_vectorize_features(self):
        """Test feature dictionary vectorization."""
        config = IntegrationConfig()
        processor = TextProcessor(config)
        
        features = {"feature1": 0.5, "feature2": 0.8, "feature3": 0.2}
        vector = await processor._vectorize_features(features)
        
        # Should return numpy array
        assert isinstance(vector, np.ndarray)
        assert len(vector) == 10  # Target size
        
        # Test with empty features
        empty_vector = await processor._vectorize_features({})
        assert len(empty_vector) == 10
        assert np.all(empty_vector == 0)
    
    @pytest.mark.asyncio
    async def test_create_token_features(self):
        """Test token feature creation."""
        config = IntegrationConfig()
        processor = TextProcessor(config)
        
        tokens = ["hello", "world", "123", "test!"]
        token_features = await processor._create_token_features(tokens)
        
        # Should return numpy array with expected features
        assert isinstance(token_features, np.ndarray)
        assert len(token_features) == 5  # Number of token features
        
        # Check specific features
        assert token_features[0] == len(tokens)  # num_tokens
        assert token_features[3] == 1.0  # has_numbers (due to "123")
        assert token_features[4] == 1.0  # has_punctuation (due to "test!")
        
        # Test with empty tokens
        empty_features = await processor._create_token_features([])
        assert len(empty_features) == 5
        assert empty_features[0] == 0  # num_tokens should be 0


class TestVisualProcessor:
    """Test cases for VisualProcessor class."""
    
    def create_sample_visual_features(self):
        """Create sample visual features for testing."""
        return VisualFeatures(
            visual_embeddings=np.random.rand(256),
            color_features={"brightness": 0.7, "contrast": 0.8},
            texture_features={"roughness": 0.6, "uniformity": 0.9},
            shape_features={"circularity": 0.5, "aspect_ratio": 1.2},
            spatial_features={"density": 0.4, "symmetry": 0.8},
            content_features={"has_text": True, "complexity": 0.6}
        )
    
    @pytest.mark.asyncio
    async def test_process_visual_features(self):
        """Test visual feature processing."""
        config = IntegrationConfig()
        processor = VisualProcessor(config)
        visual_features_list = [self.create_sample_visual_features()]
        
        processed = await processor.process_visual_features(visual_features_list)
        
        # Check that all expected keys are present
        expected_keys = ['embeddings', 'color', 'texture', 'shape', 'spatial', 'content']
        for key in expected_keys:
            assert key in processed
            assert isinstance(processed[key], np.ndarray)
        
        # Check embeddings dimension
        assert len(processed['embeddings']) == config.embedding_dim
    
    @pytest.mark.asyncio
    async def test_process_empty_visual_features(self):
        """Test processing empty visual features list."""
        config = IntegrationConfig()
        processor = VisualProcessor(config)
        
        processed = await processor.process_visual_features([])
        
        # Should return default empty features
        expected_keys = ['embeddings', 'color', 'texture', 'shape', 'spatial', 'content']
        for key in expected_keys:
            assert key in processed
            assert isinstance(processed[key], np.ndarray)
            assert len(processed[key]) > 0
    
    @pytest.mark.asyncio
    async def test_aggregate_visual_embeddings(self):
        """Test visual embedding aggregation."""
        config = IntegrationConfig()
        processor = VisualProcessor(config)
        
        # Create multiple visual features with different embedding sizes
        visual_features_list = [
            VisualFeatures(
                visual_embeddings=np.random.rand(200),
                color_features={}, texture_features={}, shape_features={},
                spatial_features={}, content_features={}
            ),
            VisualFeatures(
                visual_embeddings=np.random.rand(300),
                color_features={}, texture_features={}, shape_features={},
                spatial_features={}, content_features={}
            )
        ]
        
        aggregated = await processor._aggregate_visual_embeddings(visual_features_list)
        
        # Should return embedding of target dimension
        assert len(aggregated) == config.embedding_dim
        assert isinstance(aggregated, np.ndarray)
    
    @pytest.mark.asyncio
    async def test_aggregate_feature_dicts(self):
        """Test feature dictionary aggregation."""
        config = IntegrationConfig()
        processor = VisualProcessor(config)
        
        feature_dicts = [
            {"feature1": 0.5, "feature2": 0.8},
            {"feature1": 0.7, "feature3": 0.6},
            {"feature2": 0.9, "feature3": 0.4}
        ]
        
        aggregated = await processor._aggregate_feature_dicts(feature_dicts)
        
        # Should return fixed-size vector
        assert isinstance(aggregated, np.ndarray)
        assert len(aggregated) == 10  # Target size
        
        # Test with empty feature dicts
        empty_aggregated = await processor._aggregate_feature_dicts([])
        assert len(empty_aggregated) == 10
        assert np.all(empty_aggregated == 0)
    
    @pytest.mark.asyncio
    async def test_aggregate_content_features(self):
        """Test content feature aggregation."""
        config = IntegrationConfig()
        processor = VisualProcessor(config)
        
        content_features_list = [
            {"has_text": True, "has_lines": False, "complexity": 0.8},
            {"has_text": False, "has_lines": True, "complexity": 0.6},
            {"has_text": True, "has_shapes": True, "complexity": 0.7}
        ]
        
        aggregated = await processor._aggregate_content_features(content_features_list)
        
        # Should return fixed-size vector
        assert isinstance(aggregated, np.ndarray)
        assert len(aggregated) == 5
        
        # Check boolean feature aggregation (should be ratios)
        assert 0 <= aggregated[0] <= 1  # has_text ratio
        assert 0 <= aggregated[1] <= 1  # has_lines ratio


class TestCrossModalAligner:
    """Test cases for CrossModalAligner class."""
    
    def create_sample_visual_elements(self):
        """Create sample visual elements for testing."""
        return [
            VisualElement(
                element_id="elem1",
                element_type=VisualElementType.CHART,
                bounding_box=BoundingBox(x=10, y=20, width=100, height=80),
                confidence=0.9
            ),
            VisualElement(
                element_id="elem2",
                element_type=VisualElementType.DIAGRAM,
                bounding_box=BoundingBox(x=150, y=30, width=120, height=90),
                confidence=0.8
            )
        ]
    
    def create_sample_text_features(self):
        """Create sample text features for testing."""
        return TextFeatures(
            embeddings=np.random.rand(100),
            tokens=["the", "chart", "shows", "data", "trends"],
            semantic_features={"sentiment": 0.5},
            linguistic_features={"complexity": 0.6},
            domain_features={"technical": 0.8}
        )
    
    def create_sample_visual_features_list(self):
        """Create sample visual features list for testing."""
        return [
            VisualFeatures(
                visual_embeddings=np.random.rand(100),
                color_features={}, texture_features={}, shape_features={},
                spatial_features={}, content_features={}
            )
        ]
    
    @pytest.mark.asyncio
    async def test_find_cross_modal_relationships(self):
        """Test cross-modal relationship finding."""
        config = IntegrationConfig()
        aligner = CrossModalAligner(config)
        
        text_content = "The chart shows important data trends and the diagram illustrates the process flow."
        visual_elements = self.create_sample_visual_elements()
        text_features = self.create_sample_text_features()
        visual_features_list = self.create_sample_visual_features_list()
        
        relationships = await aligner.find_cross_modal_relationships(
            text_content, visual_elements, text_features, visual_features_list
        )
        
        # Should find some relationships
        assert isinstance(relationships, list)
        
        # Check relationship properties
        for rel in relationships:
            assert isinstance(rel, CrossModalRelationship)
            assert len(rel.text_span) == 2
            assert rel.text_span[0] >= 0
            assert rel.text_span[1] >= rel.text_span[0]
            assert rel.visual_element_id in ["elem1", "elem2"]
            assert 0 <= rel.confidence <= 1
            assert 0 <= rel.semantic_similarity <= 1
    
    @pytest.mark.asyncio
    async def test_keyword_based_alignment(self):
        """Test keyword-based alignment."""
        config = IntegrationConfig()
        aligner = CrossModalAligner(config)
        
        text_content = "The chart displays data and the diagram shows the process."
        visual_elements = self.create_sample_visual_elements()
        
        relationships = await aligner._keyword_based_alignment(text_content, visual_elements)
        
        # Should find relationships for "chart" and "diagram" keywords
        assert isinstance(relationships, list)
        assert len(relationships) >= 2  # At least one for chart, one for diagram
        
        # Check that relationships reference correct elements
        chart_relationships = [r for r in relationships if r.visual_element_id == "elem1"]
        diagram_relationships = [r for r in relationships if r.visual_element_id == "elem2"]
        
        assert len(chart_relationships) > 0
        assert len(diagram_relationships) > 0
    
    @pytest.mark.asyncio
    async def test_semantic_similarity_alignment(self):
        """Test semantic similarity alignment."""
        config = IntegrationConfig()
        aligner = CrossModalAligner(config)
        
        text_features = self.create_sample_text_features()
        visual_features_list = self.create_sample_visual_features_list()
        visual_elements = self.create_sample_visual_elements()
        
        relationships = await aligner._semantic_similarity_alignment(
            text_features, visual_features_list, visual_elements
        )
        
        # Should return relationships based on semantic similarity
        assert isinstance(relationships, list)
        
        # Check relationship properties
        for rel in relationships:
            assert isinstance(rel, CrossModalRelationship)
            assert rel.relationship_type == "relates_to"
            assert 0 <= rel.semantic_similarity <= 1
    
    @pytest.mark.asyncio
    async def test_positional_alignment(self):
        """Test positional alignment."""
        config = IntegrationConfig()
        aligner = CrossModalAligner(config)
        
        text_content = "The chart above shows data and the diagram below illustrates the process."
        visual_elements = self.create_sample_visual_elements()
        
        relationships = await aligner._positional_alignment(text_content, visual_elements)
        
        # Should find relationships for positional keywords
        assert isinstance(relationships, list)
        
        # Check relationship properties
        for rel in relationships:
            assert isinstance(rel, CrossModalRelationship)
            assert rel.relationship_type == "references"
    
    @pytest.mark.asyncio
    async def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        config = IntegrationConfig()
        aligner = CrossModalAligner(config)
        
        # Test with identical vectors
        vec1 = np.array([1, 2, 3])
        vec2 = np.array([1, 2, 3])
        similarity = await aligner._cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 1e-6
        
        # Test with orthogonal vectors
        vec3 = np.array([1, 0, 0])
        vec4 = np.array([0, 1, 0])
        similarity = await aligner._cosine_similarity(vec3, vec4)
        assert abs(similarity - 0.0) < 1e-6
        
        # Test with zero vectors
        vec5 = np.zeros(3)
        vec6 = np.array([1, 2, 3])
        similarity = await aligner._cosine_similarity(vec5, vec6)
        assert similarity == 0.0


class TestAttentionFusion:
    """Test cases for AttentionFusion class."""
    
    def create_sample_processed_features(self):
        """Create sample processed features for testing."""
        text_features = {
            'embeddings': np.random.rand(100),
            'semantic': np.random.rand(10),
            'linguistic': np.random.rand(10)
        }
        
        visual_features = {
            'embeddings': np.random.rand(100),
            'color': np.random.rand(10),
            'texture': np.random.rand(10)
        }
        
        return text_features, visual_features
    
    @pytest.mark.asyncio
    async def test_apply_attention_fusion(self):
        """Test attention fusion application."""
        config = IntegrationConfig()
        fusion = AttentionFusion(config)
        text_features, visual_features = self.create_sample_processed_features()
        
        result = await fusion.apply_attention_fusion(text_features, visual_features)
        
        # Should return numpy array
        assert isinstance(result, np.ndarray)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_cross_attention_fusion(self):
        """Test cross-attention fusion."""
        config = IntegrationConfig()
        fusion = AttentionFusion(config)
        text_features, visual_features = self.create_sample_processed_features()
        
        result = await fusion._cross_attention_fusion(text_features, visual_features)
        
        # Should return combined features
        assert isinstance(result, np.ndarray)
        assert len(result) >= config.embedding_dim
    
    @pytest.mark.asyncio
    async def test_self_attention_fusion(self):
        """Test self-attention fusion."""
        config = IntegrationConfig()
        fusion = AttentionFusion(config)
        text_features, visual_features = self.create_sample_processed_features()
        
        result = await fusion._self_attention_fusion(text_features, visual_features)
        
        # Should return fused features
        assert isinstance(result, np.ndarray)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_multi_head_attention_fusion(self):
        """Test multi-head attention fusion."""
        config = IntegrationConfig(num_attention_heads=4)
        fusion = AttentionFusion(config)
        text_features, visual_features = self.create_sample_processed_features()
        
        result = await fusion._multi_head_attention_fusion(text_features, visual_features)
        
        # Should return fused features
        assert isinstance(result, np.ndarray)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_calculate_attention_scores(self):
        """Test attention score calculation."""
        config = IntegrationConfig()
        fusion = AttentionFusion(config)
        
        query = np.array([1, 2, 3])
        key = np.array([2, 4, 6])  # Parallel to query
        
        score = await fusion._calculate_attention_scores(query, key)
        
        # Should return similarity score
        assert isinstance(score, float)
        assert score > 0.9  # Should be high for parallel vectors
    
    @pytest.mark.asyncio
    async def test_resize_vector(self):
        """Test vector resizing."""
        config = IntegrationConfig()
        fusion = AttentionFusion(config)
        
        # Test padding
        small_vector = np.array([1, 2, 3])
        resized = await fusion._resize_vector(small_vector, 5)
        assert len(resized) == 5
        assert np.array_equal(resized[:3], small_vector)
        assert np.array_equal(resized[3:], [0, 0])
        
        # Test truncation
        large_vector = np.array([1, 2, 3, 4, 5, 6])
        resized = await fusion._resize_vector(large_vector, 4)
        assert len(resized) == 4
        assert np.array_equal(resized, large_vector[:4])


class TestMultiModalFeatureIntegrator:
    """Test cases for MultiModalFeatureIntegrator class."""
    
    def create_sample_text_features(self):
        """Create sample text features for testing."""
        return TextFeatures(
            embeddings=np.random.rand(100),
            tokens=["hello", "world", "test"],
            semantic_features={"sentiment": 0.8},
            linguistic_features={"complexity": 0.6},
            domain_features={"technical": 0.7}
        )
    
    def create_sample_visual_features_list(self):
        """Create sample visual features list for testing."""
        return [
            VisualFeatures(
                visual_embeddings=np.random.rand(100),
                color_features={"brightness": 0.7},
                texture_features={"roughness": 0.6},
                shape_features={"circularity": 0.8},
                spatial_features={"density": 0.5},
                content_features={"has_text": True}
            )
        ]
    
    def create_sample_multimodal_context(self):
        """Create sample multi-modal context for testing."""
        doc_content = DocumentContent(
            document_id="doc1",
            text_content="This is a test document with charts and diagrams.",
            raw_text="This is a test document with charts and diagrams.",
            structured_content={}
        )
        
        research_context = ResearchContext(
            research_domain="machine_learning",
            research_goals=["understand", "implement"]
        )
        
        visual_elements = [
            VisualElement(
                element_id="elem1",
                element_type=VisualElementType.CHART,
                bounding_box=BoundingBox(x=10, y=20, width=100, height=80),
                confidence=0.9
            )
        ]
        
        return MultiModalContext(
            context_id="ctx1",
            document_content=doc_content,
            visual_elements=visual_elements,
            user_interaction_history=[],
            research_context=research_context
        )
    
    @pytest.mark.asyncio
    async def test_integrate_features(self):
        """Test feature integration."""
        integrator = MultiModalFeatureIntegrator()
        text_features = self.create_sample_text_features()
        visual_features = self.create_sample_visual_features_list()
        
        result = await integrator.integrate_features(text_features, visual_features)
        
        # Should return MultiModalFeatures
        assert isinstance(result, MultiModalFeatures)
        assert result.text_features == text_features
        assert result.visual_features == visual_features
        assert isinstance(result.integrated_embedding, np.ndarray)
        assert len(result.integrated_embedding) > 0
        assert isinstance(result.confidence_scores, dict)
        assert isinstance(result.fusion_metadata, dict)
    
    @pytest.mark.asyncio
    async def test_integrate_features_different_strategies(self):
        """Test integration with different strategies."""
        strategies = [
            IntegrationStrategy.CONCATENATION,
            IntegrationStrategy.ATTENTION_FUSION,
            IntegrationStrategy.WEIGHTED_COMBINATION
        ]
        
        text_features = self.create_sample_text_features()
        visual_features = self.create_sample_visual_features_list()
        
        for strategy in strategies:
            config = IntegrationConfig(strategy=strategy)
            integrator = MultiModalFeatureIntegrator(config)
            
            result = await integrator.integrate_features(text_features, visual_features)
            
            assert isinstance(result, MultiModalFeatures)
            assert result.fusion_metadata["integration_strategy"] == strategy.value
    
    @pytest.mark.asyncio
    async def test_create_cross_modal_embeddings(self):
        """Test cross-modal embedding creation."""
        integrator = MultiModalFeatureIntegrator()
        text_features = self.create_sample_text_features()
        visual_features = self.create_sample_visual_features_list()
        
        # First integrate features
        multimodal_features = await integrator.integrate_features(text_features, visual_features)
        
        # Then create cross-modal embeddings
        cross_modal_embeddings = await integrator.create_cross_modal_embeddings(multimodal_features)
        
        # Should return normalized embeddings
        assert isinstance(cross_modal_embeddings, np.ndarray)
        assert len(cross_modal_embeddings) > 0
        
        # Check normalization if enabled
        if integrator.config.normalize_features:
            norm = np.linalg.norm(cross_modal_embeddings)
            assert abs(norm - 1.0) < 1e-6
    
    @pytest.mark.asyncio
    async def test_find_cross_modal_relationships_with_context(self):
        """Test cross-modal relationship finding with context."""
        integrator = MultiModalFeatureIntegrator()
        context = self.create_sample_multimodal_context()
        
        relationships = await integrator.find_cross_modal_relationships_with_context(context)
        
        # Should return list of relationships
        assert isinstance(relationships, list)
        
        # Check relationship properties
        for rel in relationships:
            assert isinstance(rel, CrossModalRelationship)
    
    @pytest.mark.asyncio
    async def test_concatenation_fusion(self):
        """Test concatenation fusion method."""
        integrator = MultiModalFeatureIntegrator()
        
        text_features = {
            'embeddings': np.array([1, 2, 3]),
            'semantic': np.array([4, 5])
        }
        
        visual_features = {
            'embeddings': np.array([6, 7, 8]),
            'color': np.array([9, 10])
        }
        
        result = await integrator._concatenation_fusion(text_features, visual_features)
        
        # Should concatenate all features
        assert isinstance(result, np.ndarray)
        expected_length = 3 + 2 + 3 + 2  # Sum of all feature lengths
        assert len(result) == expected_length
    
    @pytest.mark.asyncio
    async def test_weighted_combination_fusion(self):
        """Test weighted combination fusion method."""
        config = IntegrationConfig(text_weight=0.7, visual_weight=0.3)
        integrator = MultiModalFeatureIntegrator(config)
        
        text_features = {
            'embeddings': np.array([1, 2, 3]),
            'semantic': np.array([4, 5])
        }
        
        visual_features = {
            'embeddings': np.array([6, 7, 8]),
            'color': np.array([9, 10])
        }
        
        result = await integrator._weighted_combination_fusion(text_features, visual_features)
        
        # Should return weighted combination
        assert isinstance(result, np.ndarray)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_calculate_confidence_scores(self):
        """Test confidence score calculation."""
        integrator = MultiModalFeatureIntegrator()
        text_features = self.create_sample_text_features()
        visual_features = self.create_sample_visual_features_list()
        integrated_embedding = np.random.rand(100)
        
        confidence_scores = await integrator._calculate_confidence_scores(
            text_features, visual_features, integrated_embedding
        )
        
        # Should return confidence scores
        assert isinstance(confidence_scores, dict)
        expected_keys = ['text', 'visual', 'integration', 'overall']
        for key in expected_keys:
            assert key in confidence_scores
            assert 0 <= confidence_scores[key] <= 1
    
    @pytest.mark.asyncio
    async def test_integration_with_empty_visual_features(self):
        """Test integration with empty visual features."""
        integrator = MultiModalFeatureIntegrator()
        text_features = self.create_sample_text_features()
        empty_visual_features = []
        
        result = await integrator.integrate_features(text_features, empty_visual_features)
        
        # Should handle empty visual features gracefully
        assert isinstance(result, MultiModalFeatures)
        assert result.text_features == text_features
        assert result.visual_features == empty_visual_features
        assert isinstance(result.integrated_embedding, np.ndarray)
        assert result.confidence_scores['visual'] == 0.0
    
    @pytest.mark.asyncio
    async def test_integration_error_handling(self):
        """Test error handling in integration."""
        integrator = MultiModalFeatureIntegrator()
        
        # Test with invalid text features (missing required attributes)
        invalid_text_features = Mock()
        invalid_text_features.embeddings = None  # This should cause an error
        
        visual_features = self.create_sample_visual_features_list()
        
        with pytest.raises(Exception):
            await integrator.integrate_features(invalid_text_features, visual_features)


class TestIntegration:
    """Integration tests for multi-modal feature integration."""
    
    def create_comprehensive_features(self):
        """Create comprehensive features for integration testing."""
        text_features = TextFeatures(
            embeddings=np.random.rand(256),
            tokens=["the", "chart", "shows", "important", "data", "trends"],
            semantic_features={
                "sentiment": 0.7,
                "complexity": 0.8,
                "formality": 0.6,
                "objectivity": 0.9
            },
            linguistic_features={
                "pos_diversity": 0.7,
                "syntax_complexity": 0.6,
                "readability": 0.8
            },
            domain_features={
                "technical": 0.8,
                "academic": 0.7,
                "business": 0.4
            }
        )
        
        visual_features = [
            VisualFeatures(
                visual_embeddings=np.random.rand(256),
                color_features={
                    "brightness": 0.7,
                    "contrast": 0.8,
                    "saturation": 0.6,
                    "hue_diversity": 0.5
                },
                texture_features={
                    "roughness": 0.4,
                    "uniformity": 0.8,
                    "directionality": 0.3
                },
                shape_features={
                    "circularity": 0.6,
                    "rectangularity": 0.8,
                    "complexity": 0.5
                },
                spatial_features={
                    "density": 0.6,
                    "symmetry": 0.7,
                    "balance": 0.8
                },
                content_features={
                    "has_text": True,
                    "has_lines": True,
                    "has_shapes": True,
                    "complexity": 0.7
                }
            ),
            VisualFeatures(
                visual_embeddings=np.random.rand(256),
                color_features={"brightness": 0.5, "contrast": 0.6},
                texture_features={"roughness": 0.7, "uniformity": 0.4},
                shape_features={"circularity": 0.3, "rectangularity": 0.9},
                spatial_features={"density": 0.8, "symmetry": 0.5},
                content_features={"has_text": False, "complexity": 0.4}
            )
        ]
        
        return text_features, visual_features
    
    @pytest.mark.asyncio
    async def test_end_to_end_integration(self):
        """Test complete end-to-end feature integration."""
        # Test with different configurations
        configs = [
            IntegrationConfig(strategy=IntegrationStrategy.CONCATENATION),
            IntegrationConfig(strategy=IntegrationStrategy.ATTENTION_FUSION),
            IntegrationConfig(strategy=IntegrationStrategy.WEIGHTED_COMBINATION),
        ]
        
        text_features, visual_features = self.create_comprehensive_features()
        
        for config in configs:
            integrator = MultiModalFeatureIntegrator(config)
            
            # Integrate features
            result = await integrator.integrate_features(text_features, visual_features)
            
            # Verify result quality
            assert isinstance(result, MultiModalFeatures)
            assert result.is_high_quality(threshold=0.5)
            
            # Create cross-modal embeddings
            cross_modal_emb = await integrator.create_cross_modal_embeddings(result)
            assert isinstance(cross_modal_emb, np.ndarray)
            assert len(cross_modal_emb) > 0
    
    @pytest.mark.asyncio
    async def test_integration_consistency(self):
        """Test that integration produces consistent results."""
        integrator = MultiModalFeatureIntegrator()
        text_features, visual_features = self.create_comprehensive_features()
        
        # Run integration multiple times
        results = []
        for _ in range(3):
            result = await integrator.integrate_features(text_features, visual_features)
            results.append(result)
        
        # Results should be identical (deterministic)
        for i in range(1, len(results)):
            assert np.allclose(results[0].integrated_embedding, results[i].integrated_embedding)
            assert results[0].confidence_scores.keys() == results[i].confidence_scores.keys()
    
    @pytest.mark.asyncio
    async def test_integration_with_different_attention_mechanisms(self):
        """Test integration with different attention mechanisms."""
        attention_mechanisms = [
            AttentionMechanism.CROSS_ATTENTION,
            AttentionMechanism.SELF_ATTENTION,
            AttentionMechanism.MULTI_HEAD_ATTENTION,
            AttentionMechanism.SCALED_DOT_PRODUCT
        ]
        
        text_features, visual_features = self.create_comprehensive_features()
        
        for mechanism in attention_mechanisms:
            config = IntegrationConfig(
                strategy=IntegrationStrategy.ATTENTION_FUSION,
                attention_mechanism=mechanism
            )
            integrator = MultiModalFeatureIntegrator(config)
            
            result = await integrator.integrate_features(text_features, visual_features)
            
            assert isinstance(result, MultiModalFeatures)
            assert result.fusion_metadata["attention_mechanism"] == mechanism.value
    
    @pytest.mark.asyncio
    async def test_performance_with_large_features(self):
        """Test performance with large feature vectors."""
        # Create large features
        large_text_features = TextFeatures(
            embeddings=np.random.rand(2048),
            tokens=["word"] * 1000,
            semantic_features={f"feature_{i}": np.random.rand() for i in range(100)},
            linguistic_features={f"ling_{i}": np.random.rand() for i in range(50)},
            domain_features={f"domain_{i}": np.random.rand() for i in range(20)}
        )
        
        large_visual_features = [
            VisualFeatures(
                visual_embeddings=np.random.rand(2048),
                color_features={f"color_{i}": np.random.rand() for i in range(50)},
                texture_features={f"texture_{i}": np.random.rand() for i in range(30)},
                shape_features={f"shape_{i}": np.random.rand() for i in range(20)},
                spatial_features={f"spatial_{i}": np.random.rand() for i in range(25)},
                content_features={f"content_{i}": np.random.rand() > 0.5 for i in range(10)}
            )
        ]
        
        integrator = MultiModalFeatureIntegrator()
        
        # Should complete without timeout or memory issues
        result = await integrator.integrate_features(large_text_features, large_visual_features)
        
        assert isinstance(result, MultiModalFeatures)
        assert len(result.integrated_embedding) > 0