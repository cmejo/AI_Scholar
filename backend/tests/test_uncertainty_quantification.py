"""
Unit tests for uncertainty quantification system
Tests confidence scoring based on source quality and consensus
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from services.reasoning_engine import UncertaintyQuantifier, ReasoningEngine
from models.schemas import ReasoningResult, UncertaintyScore

class TestUncertaintyQuantifier:
    """Test cases for the UncertaintyQuantifier class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.quantifier = UncertaintyQuantifier()
    
    def test_assess_source_quality_high_quality(self):
        """Test source quality assessment with high-quality sources"""
        sources = [
            {
                "content": "This is a comprehensive analysis with detailed explanations and multiple supporting examples.",
                "relevance": 0.9
            },
            {
                "content": "Another detailed source with substantial content and high relevance.",
                "relevance": 0.85
            }
        ]
        
        quality_score = self.quantifier._assess_source_quality(sources)
        
        assert quality_score > 0.6, "High-quality sources should have quality score > 0.6"
        assert quality_score <= 1.0, "Quality score should not exceed 1.0"
    
    def test_assess_source_quality_low_quality(self):
        """Test source quality assessment with low-quality sources"""
        sources = [
            {
                "content": "Short text.",
                "relevance": 0.3
            },
            {
                "content": "Brief.",
                "relevance": 0.2
            }
        ]
        
        quality_score = self.quantifier._assess_source_quality(sources)
        
        assert quality_score < 0.5, "Low-quality sources should have quality score < 0.5"
        assert quality_score >= 0.0, "Quality score should not be negative"
    
    def test_assess_source_quality_empty_sources(self):
        """Test source quality assessment with no sources"""
        sources = []
        
        quality_score = self.quantifier._assess_source_quality(sources)
        
        assert quality_score == 0.0, "Empty sources should return quality score of 0.0"
    
    def test_assess_source_consensus_single_source(self):
        """Test source consensus with single source"""
        sources = [
            {
                "content": "Single source content about the topic",
                "relevance": 0.8
            }
        ]
        response = "Response about the topic"
        
        consensus_score = self.quantifier._assess_source_consensus(sources, response)
        
        assert consensus_score == 0.8, "Single source should return moderate consensus score"
    
    def test_assess_source_consensus_multiple_sources(self):
        """Test source consensus with multiple sources"""
        sources = [
            {
                "content": "Information about climate change effects on temperature",
                "relevance": 0.9
            },
            {
                "content": "Data on climate change temperature impacts",
                "relevance": 0.85
            }
        ]
        response = "Climate change affects global temperatures"
        
        consensus_score = self.quantifier._assess_source_consensus(sources, response)
        
        assert 0.0 <= consensus_score <= 1.0, "Consensus score should be between 0 and 1"
    
    @pytest.mark.asyncio
    async def test_assess_language_confidence_confident_text(self):
        """Test language confidence assessment with confident language"""
        confident_text = "This is definitely true and clearly established by proven research."
        
        confidence_score = await self.quantifier._assess_language_confidence(confident_text)
        
        assert confidence_score > 0.5, "Confident language should have confidence score > 0.5"
        assert confidence_score <= 1.0, "Confidence score should not exceed 1.0"
    
    @pytest.mark.asyncio
    async def test_assess_language_confidence_uncertain_text(self):
        """Test language confidence assessment with uncertain language"""
        uncertain_text = "This might be true, but it's unclear and possibly uncertain."
        
        confidence_score = await self.quantifier._assess_language_confidence(uncertain_text)
        
        assert confidence_score < 0.5, "Uncertain language should have confidence score < 0.5"
        assert confidence_score >= 0.0, "Confidence score should not be negative"
    
    def test_assess_reasoning_confidence_strong_reasoning(self):
        """Test reasoning confidence assessment with strong reasoning"""
        reasoning_results = [
            ReasoningResult(
                reasoning_type="causal",
                confidence=0.9,
                explanation="Strong reasoning",
                supporting_evidence=["Evidence 1"],
                metadata={}
            ),
            ReasoningResult(
                reasoning_type="analogical",
                confidence=0.85,
                explanation="Good analogical support",
                supporting_evidence=["Evidence 2"],
                metadata={}
            )
        ]
        
        reasoning_confidence = self.quantifier._assess_reasoning_confidence(reasoning_results)
        
        assert reasoning_confidence > 0.8, "Strong reasoning should have high confidence"
        assert reasoning_confidence <= 1.0, "Reasoning confidence should not exceed 1.0"
    
    def test_assess_reasoning_confidence_weak_reasoning(self):
        """Test reasoning confidence assessment with weak reasoning"""
        reasoning_results = [
            ReasoningResult(
                reasoning_type="causal",
                confidence=0.3,
                explanation="Weak reasoning",
                supporting_evidence=["Weak evidence"],
                metadata={}
            )
        ]
        
        reasoning_confidence = self.quantifier._assess_reasoning_confidence(reasoning_results)
        
        assert reasoning_confidence < 0.5, "Weak reasoning should have low confidence"
        assert reasoning_confidence >= 0.0, "Reasoning confidence should not be negative"
    
    def test_assess_reasoning_confidence_no_reasoning(self):
        """Test reasoning confidence assessment with no reasoning"""
        reasoning_results = []
        
        reasoning_confidence = self.quantifier._assess_reasoning_confidence(reasoning_results)
        
        assert reasoning_confidence == 0.5, "No reasoning should return neutral confidence of 0.5"
    
    @pytest.mark.asyncio
    async def test_quantify_uncertainty_high_confidence_scenario(self):
        """Test uncertainty quantification for high confidence scenario"""
        response = "The Earth orbits the Sun in an elliptical path."
        sources = [
            {
                "content": "Comprehensive astronomical data confirms Earth's elliptical orbit around the Sun.",
                "relevance": 0.95
            },
            {
                "content": "Multiple observations verify Earth's orbital mechanics and elliptical trajectory.",
                "relevance": 0.90
            }
        ]
        reasoning_results = [
            ReasoningResult(
                reasoning_type="causal",
                confidence=0.92,
                explanation="Strong causal relationship",
                supporting_evidence=["Astronomical observations"],
                metadata={}
            )
        ]
        
        uncertainty_score = await self.quantifier.quantify_uncertainty(
            response, sources, reasoning_results
        )
        
        assert isinstance(uncertainty_score, UncertaintyScore)
        assert 0.0 <= uncertainty_score.confidence <= 1.0
        assert 0.0 <= uncertainty_score.reliability_score <= 1.0
        assert 0.0 <= uncertainty_score.source_quality <= 1.0
        assert isinstance(uncertainty_score.uncertainty_factors, list)
    
    @pytest.mark.asyncio
    async def test_quantify_uncertainty_low_confidence_scenario(self):
        """Test uncertainty quantification for low confidence scenario"""
        response = "The exact number of alien civilizations is unclear and highly speculative."
        sources = [
            {
                "content": "Brief speculation about alien life.",
                "relevance": 0.3
            }
        ]
        reasoning_results = [
            ReasoningResult(
                reasoning_type="analogical",
                confidence=0.2,
                explanation="Weak analogical support",
                supporting_evidence=["Speculative evidence"],
                metadata={}
            )
        ]
        
        uncertainty_score = await self.quantifier.quantify_uncertainty(
            response, sources, reasoning_results
        )
        
        assert isinstance(uncertainty_score, UncertaintyScore)
        assert uncertainty_score.confidence < 0.5, "Low confidence scenario should have confidence < 0.5"
        assert len(uncertainty_score.uncertainty_factors) > 0, "Should identify uncertainty factors"
    
    @pytest.mark.asyncio
    async def test_quantify_uncertainty_no_sources(self):
        """Test uncertainty quantification with no sources"""
        response = "This is a response without any sources."
        sources = []
        
        uncertainty_score = await self.quantifier.quantify_uncertainty(response, sources)
        
        assert isinstance(uncertainty_score, UncertaintyScore)
        assert uncertainty_score.source_quality == 0.0, "No sources should result in zero source quality"
        assert "Low source quality" in uncertainty_score.uncertainty_factors

class TestReasoningEngine:
    """Test cases for the ReasoningEngine class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.reasoning_engine = ReasoningEngine()
    
    def test_should_apply_reasoning_complex_query(self):
        """Test reasoning application decision for complex queries"""
        complex_queries = [
            "Why does climate change cause extreme weather?",
            "How does exercise affect mental health?",
            "What are the consequences of deforestation?",
            "Compare the effects of renewable vs fossil fuels"
        ]
        
        for query in complex_queries:
            should_reason = self.reasoning_engine.should_apply_reasoning(query)
            assert should_reason, f"Complex query should trigger reasoning: {query}"
    
    def test_should_apply_reasoning_simple_query(self):
        """Test reasoning application decision for simple queries"""
        simple_queries = [
            "What is the capital of France?",
            "Define photosynthesis",
            "List the planets in our solar system"
        ]
        
        for query in simple_queries:
            should_reason = self.reasoning_engine.should_apply_reasoning(query)
            # Simple queries may or may not trigger reasoning depending on threshold
            assert isinstance(should_reason, bool), f"Should return boolean for query: {query}"
    
    @pytest.mark.asyncio
    async def test_quantify_uncertainty_integration(self):
        """Test uncertainty quantification integration in reasoning engine"""
        response = "Test response for uncertainty quantification"
        sources = [
            {
                "content": "Test source content",
                "relevance": 0.7
            }
        ]
        
        uncertainty_score = await self.reasoning_engine.quantify_uncertainty(
            response, sources
        )
        
        assert isinstance(uncertainty_score, UncertaintyScore)
        assert hasattr(uncertainty_score, 'confidence')
        assert hasattr(uncertainty_score, 'uncertainty_factors')
        assert hasattr(uncertainty_score, 'reliability_score')
        assert hasattr(uncertainty_score, 'source_quality')

class TestUncertaintyScoreModel:
    """Test cases for the UncertaintyScore model"""
    
    def test_uncertainty_score_creation(self):
        """Test UncertaintyScore model creation"""
        uncertainty_score = UncertaintyScore(
            confidence=0.75,
            uncertainty_factors=["Some uncertainty"],
            reliability_score=0.8,
            source_quality=0.85
        )
        
        assert uncertainty_score.confidence == 0.75
        assert uncertainty_score.uncertainty_factors == ["Some uncertainty"]
        assert uncertainty_score.reliability_score == 0.8
        assert uncertainty_score.source_quality == 0.85
    
    def test_uncertainty_score_validation(self):
        """Test UncertaintyScore model validation"""
        # Test with valid data
        valid_score = UncertaintyScore(
            confidence=0.5,
            uncertainty_factors=[],
            reliability_score=0.6,
            source_quality=0.7
        )
        
        assert isinstance(valid_score, UncertaintyScore)
        
        # Test with invalid data types should raise validation error
        with pytest.raises(Exception):
            UncertaintyScore(
                confidence="invalid",  # Should be float
                uncertainty_factors=[],
                reliability_score=0.6,
                source_quality=0.7
            )

if __name__ == "__main__":
    pytest.main([__file__])