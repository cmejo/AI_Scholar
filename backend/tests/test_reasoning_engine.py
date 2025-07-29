"""
Tests for the Reasoning Engine Service
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from services.reasoning_engine import (
    CausalReasoningAgent, 
    AnalogicalReasoningAgent, 
    UncertaintyQuantifier,
    ReasoningEngine,
    ReasoningType,
    CausalRelation,
    Analogy
)
from models.schemas import ReasoningResult, UncertaintyScore

class TestCausalReasoningAgent:
    """Test cases for CausalReasoningAgent"""
    
    @pytest.fixture
    def causal_agent(self):
        return CausalReasoningAgent()
    
    @pytest.fixture
    def mock_llm_response(self):
        return """
CAUSE: Increased carbon emissions
EFFECT: Global temperature rise
MECHANISM: Greenhouse gas effect traps heat in atmosphere
CONFIDENCE: 0.9
EVIDENCE: Multiple climate studies show correlation

CAUSE: Deforestation
EFFECT: Reduced carbon absorption
MECHANISM: Fewer trees means less CO2 converted to oxygen
CONFIDENCE: 0.8
EVIDENCE: Forest coverage data and carbon cycle research
"""
    
    @pytest.mark.asyncio
    async def test_causal_reasoning_basic(self, causal_agent, mock_llm_response):
        """Test basic causal reasoning functionality"""
        with patch.object(causal_agent, '_call_llm', return_value=mock_llm_response):
            result = await causal_agent.reason(
                query="What causes climate change?",
                context="Climate change is caused by various factors including emissions and deforestation."
            )
            
            assert isinstance(result, ReasoningResult)
            assert result.reasoning_type == ReasoningType.CAUSAL.value
            assert result.confidence > 0.0
            assert len(result.metadata['causal_relations']) == 2
            
            # Check first causal relation
            first_relation = result.metadata['causal_relations'][0]
            assert first_relation['cause'] == "Increased carbon emissions"
            assert first_relation['effect'] == "Global temperature rise"
            assert first_relation['confidence'] == 0.9
    
    def test_parse_causal_response(self, causal_agent, mock_llm_response):
        """Test parsing of causal relationships from LLM response"""
        relations = causal_agent._parse_causal_response(mock_llm_response)
        
        assert len(relations) == 2
        
        # Test first relation
        assert relations[0].cause == "Increased carbon emissions"
        assert relations[0].effect == "Global temperature rise"
        assert relations[0].mechanism == "Greenhouse gas effect traps heat in atmosphere"
        assert relations[0].confidence == 0.9
        
        # Test second relation
        assert relations[1].cause == "Deforestation"
        assert relations[1].effect == "Reduced carbon absorption"
        assert relations[1].confidence == 0.8
    
    @pytest.mark.asyncio
    async def test_causal_reasoning_error_handling(self, causal_agent):
        """Test error handling in causal reasoning"""
        with patch.object(causal_agent, '_call_llm', side_effect=Exception("LLM Error")):
            with pytest.raises(Exception):
                await causal_agent.reason("test query", "test context")
    
    @pytest.mark.asyncio
    async def test_causal_reasoning_empty_response(self, causal_agent):
        """Test handling of empty or malformed LLM response"""
        with patch.object(causal_agent, '_call_llm', return_value=""):
            result = await causal_agent.reason("test query", "test context")
            
            assert result.confidence == 0.0
            assert len(result.metadata['causal_relations']) == 0

class TestAnalogicalReasoningAgent:
    """Test cases for AnalogicalReasoningAgent"""
    
    @pytest.fixture
    def analogical_agent(self):
        return AnalogicalReasoningAgent()
    
    @pytest.fixture
    def mock_analogical_response(self):
        return """
SOURCE_DOMAIN: Water flow in rivers
TARGET_DOMAIN: Electric current in circuits
MAPPING: water -> electricity
SIMILARITY_SCORE: 0.8
EXPLANATION: Both involve flow through pathways with resistance

SOURCE_DOMAIN: Human immune system
TARGET_DOMAIN: Computer security system
MAPPING: antibodies -> antivirus software
SIMILARITY_SCORE: 0.7
EXPLANATION: Both systems detect and neutralize threats
"""
    
    @pytest.mark.asyncio
    async def test_analogical_reasoning_basic(self, analogical_agent, mock_analogical_response):
        """Test basic analogical reasoning functionality"""
        with patch.object(analogical_agent, '_call_llm', return_value=mock_analogical_response):
            result = await analogical_agent.reason(
                query="How does electricity work?",
                context="Electricity flows through circuits like water through pipes."
            )
            
            assert isinstance(result, ReasoningResult)
            assert result.reasoning_type == ReasoningType.ANALOGICAL.value
            assert result.confidence > 0.0
            assert len(result.metadata['analogies']) == 2
            
            # Check first analogy
            first_analogy = result.metadata['analogies'][0]
            assert first_analogy['source_domain'] == "Water flow in rivers"
            assert first_analogy['target_domain'] == "Electric current in circuits"
            assert first_analogy['similarity_score'] == 0.8
    
    def test_parse_analogical_response(self, analogical_agent, mock_analogical_response):
        """Test parsing of analogies from LLM response"""
        analogies = analogical_agent._parse_analogical_response(mock_analogical_response)
        
        assert len(analogies) == 2
        
        # Test first analogy
        assert analogies[0].source_domain == "Water flow in rivers"
        assert analogies[0].target_domain == "Electric current in circuits"
        assert analogies[0].mapping == {"water": "electricity"}
        assert analogies[0].similarity_score == 0.8
        
        # Test second analogy
        assert analogies[1].source_domain == "Human immune system"
        assert analogies[1].target_domain == "Computer security system"
        assert analogies[1].similarity_score == 0.7
    
    @pytest.mark.asyncio
    async def test_analogical_reasoning_complex_mapping(self, analogical_agent):
        """Test handling of complex mapping formats"""
        complex_response = """
SOURCE_DOMAIN: Solar system
TARGET_DOMAIN: Atomic structure
MAPPING: sun -> nucleus, planets -> electrons
SIMILARITY_SCORE: 0.9
EXPLANATION: Central body with orbiting smaller bodies
"""
        
        with patch.object(analogical_agent, '_call_llm', return_value=complex_response):
            result = await analogical_agent.reason("test query", "test context")
            
            analogies = result.metadata['analogies']
            assert len(analogies) == 1
            # Should handle complex mapping gracefully
            assert 'general' in analogies[0]['mapping'] or len(analogies[0]['mapping']) > 0

class TestUncertaintyQuantifier:
    """Test cases for UncertaintyQuantifier"""
    
    @pytest.fixture
    def uncertainty_quantifier(self):
        return UncertaintyQuantifier()
    
    @pytest.fixture
    def sample_sources(self):
        return [
            {
                'content': 'Climate change is caused by greenhouse gas emissions from human activities.',
                'relevance': 0.9,
                'document': 'Climate Report 2023'
            },
            {
                'content': 'Global warming results from increased carbon dioxide in the atmosphere.',
                'relevance': 0.8,
                'document': 'Environmental Study'
            }
        ]
    
    @pytest.fixture
    def sample_reasoning_results(self):
        return [
            ReasoningResult(
                reasoning_type="causal",
                confidence=0.8,
                explanation="Strong causal evidence",
                supporting_evidence=["Study A", "Study B"]
            ),
            ReasoningResult(
                reasoning_type="analogical",
                confidence=0.7,
                explanation="Good analogical support",
                supporting_evidence=["Example 1"]
            )
        ]
    
    @pytest.mark.asyncio
    async def test_uncertainty_quantification_basic(self, uncertainty_quantifier, sample_sources, sample_reasoning_results):
        """Test basic uncertainty quantification"""
        response = "Climate change is definitely caused by human activities, particularly greenhouse gas emissions."
        
        with patch.object(uncertainty_quantifier, '_assess_language_confidence', return_value=0.8):
            with patch.object(uncertainty_quantifier, '_assess_factual_confidence', return_value=0.9):
                uncertainty_score = await uncertainty_quantifier.quantify_uncertainty(
                    response, sample_sources, sample_reasoning_results
                )
                
                assert isinstance(uncertainty_score, UncertaintyScore)
                assert 0.0 <= uncertainty_score.confidence <= 1.0
                assert 0.0 <= uncertainty_score.reliability_score <= 1.0
                assert 0.0 <= uncertainty_score.source_quality <= 1.0
                assert isinstance(uncertainty_score.uncertainty_factors, list)
    
    def test_assess_source_quality(self, uncertainty_quantifier, sample_sources):
        """Test source quality assessment"""
        quality = uncertainty_quantifier._assess_source_quality(sample_sources)
        
        assert 0.0 <= quality <= 1.0
        assert quality > 0.5  # Should be reasonably high for good sources
    
    def test_assess_source_quality_empty(self, uncertainty_quantifier):
        """Test source quality assessment with no sources"""
        quality = uncertainty_quantifier._assess_source_quality([])
        assert quality == 0.0
    
    def test_assess_source_consensus(self, uncertainty_quantifier, sample_sources):
        """Test source consensus assessment"""
        response = "Climate change is caused by greenhouse gas emissions."
        consensus = uncertainty_quantifier._assess_source_consensus(sample_sources, response)
        
        assert 0.0 <= consensus <= 1.0
    
    def test_assess_reasoning_confidence(self, uncertainty_quantifier, sample_reasoning_results):
        """Test reasoning confidence assessment"""
        confidence = uncertainty_quantifier._assess_reasoning_confidence(sample_reasoning_results)
        
        assert confidence == 0.75  # Average of 0.8 and 0.7
    
    def test_assess_reasoning_confidence_empty(self, uncertainty_quantifier):
        """Test reasoning confidence with no results"""
        confidence = uncertainty_quantifier._assess_reasoning_confidence([])
        assert confidence == 0.5
    
    @pytest.mark.asyncio
    async def test_assess_language_confidence_certain(self, uncertainty_quantifier):
        """Test language confidence with certain language"""
        response = "This is definitely true and clearly established by research."
        confidence = await uncertainty_quantifier._assess_language_confidence(response)
        
        assert confidence > 0.5  # Should be higher for confident language
    
    @pytest.mark.asyncio
    async def test_assess_language_confidence_uncertain(self, uncertainty_quantifier):
        """Test language confidence with uncertain language"""
        response = "This might be true and possibly could happen, but it's unclear."
        confidence = await uncertainty_quantifier._assess_language_confidence(response)
        
        assert confidence < 0.5  # Should be lower for uncertain language

class TestReasoningEngine:
    """Test cases for ReasoningEngine"""
    
    @pytest.fixture
    def reasoning_engine(self):
        return ReasoningEngine()
    
    @pytest.fixture
    def mock_reasoning_results(self):
        return [
            ReasoningResult(
                reasoning_type="causal",
                confidence=0.8,
                explanation="Causal analysis",
                supporting_evidence=["Evidence 1"]
            ),
            ReasoningResult(
                reasoning_type="analogical",
                confidence=0.7,
                explanation="Analogical analysis",
                supporting_evidence=["Evidence 2"]
            )
        ]
    
    @pytest.mark.asyncio
    async def test_apply_reasoning_both_types(self, reasoning_engine, mock_reasoning_results):
        """Test applying both causal and analogical reasoning"""
        with patch.object(reasoning_engine.causal_agent, 'reason', return_value=mock_reasoning_results[0]):
            with patch.object(reasoning_engine.analogical_agent, 'reason', return_value=mock_reasoning_results[1]):
                results = await reasoning_engine.apply_reasoning(
                    query="Why does this happen?",
                    context="Some context about the phenomenon."
                )
                
                assert len(results) == 2
                assert results[0].reasoning_type == "causal"
                assert results[1].reasoning_type == "analogical"
    
    @pytest.mark.asyncio
    async def test_apply_reasoning_selective(self, reasoning_engine, mock_reasoning_results):
        """Test applying only specific reasoning types"""
        with patch.object(reasoning_engine.causal_agent, 'reason', return_value=mock_reasoning_results[0]):
            results = await reasoning_engine.apply_reasoning(
                query="Why does this happen?",
                context="Some context.",
                reasoning_types=["causal"]
            )
                
            assert len(results) == 1
            assert results[0].reasoning_type == "causal"
    
    @pytest.mark.asyncio
    async def test_apply_reasoning_error_handling(self, reasoning_engine):
        """Test error handling in reasoning application"""
        with patch.object(reasoning_engine.causal_agent, 'reason', side_effect=Exception("Error")):
            with patch.object(reasoning_engine.analogical_agent, 'reason', side_effect=Exception("Error")):
                results = await reasoning_engine.apply_reasoning(
                    query="test query",
                    context="test context"
                )
                
                # Should return empty list when all agents fail
                assert len(results) == 0
    
    def test_should_apply_reasoning_complex_query(self, reasoning_engine):
        """Test reasoning application decision for complex queries"""
        complex_query = "Why does this cause that effect and how is it similar to other phenomena?"
        should_apply = reasoning_engine.should_apply_reasoning(complex_query)
        
        assert should_apply is True
    
    def test_should_apply_reasoning_simple_query(self, reasoning_engine):
        """Test reasoning application decision for simple queries"""
        simple_query = "What is the capital of France?"
        should_apply = reasoning_engine.should_apply_reasoning(simple_query)
        
        assert should_apply is False
    
    @pytest.mark.asyncio
    async def test_quantify_uncertainty_integration(self, reasoning_engine):
        """Test uncertainty quantification integration"""
        sample_sources = [{'content': 'test content', 'relevance': 0.8}]
        
        with patch.object(reasoning_engine.uncertainty_quantifier, 'quantify_uncertainty') as mock_quantify:
            mock_quantify.return_value = UncertaintyScore(
                confidence=0.8,
                uncertainty_factors=[],
                reliability_score=0.9,
                source_quality=0.8
            )
            
            uncertainty_score = await reasoning_engine.quantify_uncertainty(
                response="Test response",
                sources=sample_sources
            )
            
            assert isinstance(uncertainty_score, UncertaintyScore)
            mock_quantify.assert_called_once()

# Integration tests
class TestReasoningEngineIntegration:
    """Integration tests for the reasoning engine"""
    
    @pytest.mark.asyncio
    async def test_full_reasoning_pipeline(self):
        """Test the complete reasoning pipeline"""
        reasoning_engine = ReasoningEngine()
        
        query = "What causes economic inflation and how is it similar to other economic phenomena?"
        context = """
        Economic inflation occurs when there is too much money chasing too few goods.
        This can be caused by increased money supply, reduced production, or increased demand.
        Similar to how water pressure increases when you reduce the pipe diameter,
        economic pressure increases when supply is constrained.
        """
        
        # Mock the LLM calls to avoid external dependencies
        mock_causal_response = """
CAUSE: Increased money supply
EFFECT: Higher prices
MECHANISM: More money available for same goods
CONFIDENCE: 0.8
EVIDENCE: Economic theory and historical data
"""
        
        mock_analogical_response = """
SOURCE_DOMAIN: Water pressure in pipes
TARGET_DOMAIN: Economic pressure in markets
MAPPING: water -> money, pipe diameter -> supply
SIMILARITY_SCORE: 0.7
EXPLANATION: Both involve pressure changes due to flow constraints
"""
        
        with patch.object(reasoning_engine.causal_agent, '_call_llm', return_value=mock_causal_response):
            with patch.object(reasoning_engine.analogical_agent, '_call_llm', return_value=mock_analogical_response):
                with patch.object(reasoning_engine.uncertainty_quantifier, '_assess_language_confidence', return_value=0.8):
                    with patch.object(reasoning_engine.uncertainty_quantifier, '_assess_factual_confidence', return_value=0.7):
                        
                        # Apply reasoning
                        reasoning_results = await reasoning_engine.apply_reasoning(query, context)
                        
                        # Quantify uncertainty
                        sources = [{'content': context, 'relevance': 0.9}]
                        uncertainty_score = await reasoning_engine.quantify_uncertainty(
                            "Inflation is caused by increased money supply", sources, reasoning_results
                        )
                        
                        # Verify results
                        assert len(reasoning_results) == 2
                        assert any(r.reasoning_type == "causal" for r in reasoning_results)
                        assert any(r.reasoning_type == "analogical" for r in reasoning_results)
                        assert isinstance(uncertainty_score, UncertaintyScore)
                        assert 0.0 <= uncertainty_score.confidence <= 1.0

if __name__ == "__main__":
    pytest.main([__file__])