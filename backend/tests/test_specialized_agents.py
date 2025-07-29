"""
Comprehensive tests for specialized AI agents (FactChecking, Summarization, Research)
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from services.reasoning_engine import (
    FactCheckingAgent, 
    SummarizationAgent, 
    ResearchAgent, 
    AgentCoordinator,
    ReasoningEngine
)
from models.schemas import ReasoningResult

class TestFactCheckingAgent:
    """Test suite for FactCheckingAgent"""
    
    @pytest.fixture
    def fact_checking_agent(self):
        return FactCheckingAgent()
    
    @pytest.fixture
    def sample_context(self):
        return """
        The Earth is approximately 4.5 billion years old. It orbits the Sun at an average distance 
        of 93 million miles. Water covers about 71% of Earth's surface. The human population 
        reached 8 billion in 2022. Climate change is caused primarily by greenhouse gas emissions 
        from human activities.
        """
    
    @pytest.fixture
    def sample_claims(self):
        return [
            "The Earth is 4.5 billion years old",
            "Water covers 71% of Earth's surface",
            "The human population is 10 billion",
            "The Sun orbits the Earth"
        ]
    
    @pytest.mark.asyncio
    async def test_fact_checking_with_claims(self, fact_checking_agent, sample_context, sample_claims):
        """Test fact-checking with provided claims"""
        with patch.object(fact_checking_agent, '_call_llm') as mock_llm:
            mock_llm.return_value = """
CLAIM: The Earth is 4.5 billion years old
STATUS: VERIFIED
EVIDENCE: The context states "The Earth is approximately 4.5 billion years old"
CONFIDENCE: 0.9
EXPLANATION: Direct match with provided information

CLAIM: Water covers 71% of Earth's surface
STATUS: VERIFIED
EVIDENCE: The context states "Water covers about 71% of Earth's surface"
CONFIDENCE: 0.9
EXPLANATION: Direct match with provided information

CLAIM: The human population is 10 billion
STATUS: CONTRADICTED
EVIDENCE: The context states "The human population reached 8 billion in 2022"
CONFIDENCE: 0.8
EXPLANATION: The claim contradicts the provided information

CLAIM: The Sun orbits the Earth
STATUS: UNVERIFIED
EVIDENCE: No information about orbital mechanics in the context
CONFIDENCE: 0.3
EXPLANATION: No relevant information found in context
"""
            
            result = await fact_checking_agent.reason(
                query="Verify these claims about Earth",
                context=sample_context,
                claims=sample_claims
            )
            
            assert isinstance(result, ReasoningResult)
            assert result.reasoning_type == "fact_checking"
            assert 0.0 <= result.confidence <= 1.0
            assert len(result.supporting_evidence) > 0
            
            # Check metadata
            metadata = result.metadata
            assert 'fact_check_results' in metadata
            assert 'claims_analyzed' in metadata
            assert 'verified_claims' in metadata
            assert 'contradicted_claims' in metadata
            
            fact_check_results = metadata['fact_check_results']
            assert len(fact_check_results) == 4
            
            # Verify specific results
            verified_count = metadata['verified_claims']
            contradicted_count = metadata['contradicted_claims']
            assert verified_count == 2
            assert contradicted_count == 1
    
    @pytest.mark.asyncio
    async def test_fact_checking_without_claims(self, fact_checking_agent, sample_context):
        """Test fact-checking with automatic claim extraction"""
        with patch.object(fact_checking_agent, '_call_llm') as mock_llm:
            # Mock claim extraction
            mock_llm.side_effect = [
                """
CLAIM: The Earth is 4.5 billion years old
CLAIM: Water covers 71% of Earth's surface
CLAIM: Human population reached 8 billion in 2022
""",
                """
CLAIM: The Earth is 4.5 billion years old
STATUS: VERIFIED
EVIDENCE: Direct statement in context
CONFIDENCE: 0.9
EXPLANATION: Matches provided information

CLAIM: Water covers 71% of Earth's surface
STATUS: VERIFIED
EVIDENCE: Direct statement in context
CONFIDENCE: 0.9
EXPLANATION: Matches provided information

CLAIM: Human population reached 8 billion in 2022
STATUS: VERIFIED
EVIDENCE: Direct statement in context
CONFIDENCE: 0.9
EXPLANATION: Matches provided information
"""
            ]
            
            result = await fact_checking_agent.reason(
                query="What are the key facts about Earth?",
                context=sample_context
            )
            
            assert isinstance(result, ReasoningResult)
            assert result.reasoning_type == "fact_checking"
            assert result.confidence > 0.8  # High confidence for verified claims
            
            # Should have called LLM twice (extraction + verification)
            assert mock_llm.call_count == 2
    
    def test_parse_fact_check_response(self, fact_checking_agent):
        """Test parsing of fact-check response"""
        response = """
CLAIM: Test claim 1
STATUS: VERIFIED
EVIDENCE: Supporting evidence
CONFIDENCE: 0.8
EXPLANATION: Test explanation

CLAIM: Test claim 2
STATUS: CONTRADICTED
EVIDENCE: Contradicting evidence
CONFIDENCE: 0.7
EXPLANATION: Another explanation
"""
        
        results = fact_checking_agent._parse_fact_check_response(response, ["Test claim 1", "Test claim 2"])
        
        assert len(results) == 2
        assert results[0]['claim'] == "Test claim 1"
        assert results[0]['status'] == "VERIFIED"
        assert results[0]['confidence'] == 0.8
        assert results[1]['status'] == "CONTRADICTED"

class TestSummarizationAgent:
    """Test suite for SummarizationAgent"""
    
    @pytest.fixture
    def summarization_agent(self):
        return SummarizationAgent()
    
    @pytest.fixture
    def sample_long_context(self):
        return """
        Artificial Intelligence (AI) has evolved significantly over the past decades. Starting from 
        simple rule-based systems in the 1950s, AI has progressed through various paradigms including 
        expert systems, machine learning, and now deep learning. Modern AI systems can perform complex 
        tasks such as natural language processing, computer vision, and decision making. The field has 
        seen remarkable breakthroughs with the development of neural networks, particularly deep neural 
        networks that can learn hierarchical representations of data. Recent advances in transformer 
        architectures have revolutionized natural language processing, leading to powerful language 
        models that can generate human-like text, translate languages, and answer questions. However, 
        AI also faces challenges including bias, interpretability, and ethical concerns. The future 
        of AI promises even more sophisticated systems that could potentially achieve artificial 
        general intelligence, though this remains a subject of ongoing research and debate.
        """
    
    @pytest.mark.asyncio
    async def test_comprehensive_summarization(self, summarization_agent, sample_long_context):
        """Test comprehensive summarization"""
        with patch.object(summarization_agent, '_call_llm') as mock_llm:
            mock_llm.return_value = """
MAIN SUMMARY:
AI has evolved from simple rule-based systems to sophisticated deep learning models. Modern AI excels 
at natural language processing and computer vision through neural networks and transformer architectures. 
Despite remarkable progress, challenges remain in bias, interpretability, and ethics.

KEY INSIGHTS:
- AI progression: rule-based → expert systems → machine learning → deep learning
- Transformers revolutionized natural language processing
- Current challenges: bias, interpretability, ethics
- Future goal: artificial general intelligence

RELEVANCE ASSESSMENT:
The content provides a comprehensive overview of AI evolution, current capabilities, and future challenges, 
directly addressing the query about AI development.

Completeness: 0.8
Accuracy: 0.9
Relevance: 0.9
"""
            
            result = await summarization_agent.reason(
                query="Summarize the evolution and current state of AI",
                context=sample_long_context,
                summary_type="comprehensive",
                max_length=200
            )
            
            assert isinstance(result, ReasoningResult)
            assert result.reasoning_type == "summarization"
            assert 0.0 <= result.confidence <= 1.0
            
            # Check metadata
            metadata = result.metadata
            assert metadata['summary_type'] == "comprehensive"
            assert metadata['max_length'] == 200
            assert 'key_insights' in metadata
            assert 'confidence_metrics' in metadata
            assert 'word_count' in metadata
            
            # Verify confidence metrics were parsed
            confidence_metrics = metadata['confidence_metrics']
            assert 'completeness' in confidence_metrics
            assert 'accuracy' in confidence_metrics
            assert 'relevance' in confidence_metrics
    
    @pytest.mark.asyncio
    async def test_focused_summarization(self, summarization_agent, sample_long_context):
        """Test summarization with focus areas"""
        with patch.object(summarization_agent, '_call_llm') as mock_llm:
            mock_llm.return_value = """
MAIN SUMMARY:
Focusing on challenges: AI faces significant issues with bias in training data and algorithms, 
lack of interpretability in deep learning models, and ethical concerns about privacy and job displacement.

KEY INSIGHTS:
- Bias stems from training data and algorithmic design
- Deep learning models are often "black boxes"
- Ethical concerns include privacy and employment impact

RELEVANCE ASSESSMENT:
Highly relevant to the focus on AI challenges and limitations.

Completeness: 0.7
Accuracy: 0.9
Relevance: 1.0
"""
            
            result = await summarization_agent.reason(
                query="What are the main challenges in AI?",
                context=sample_long_context,
                summary_type="focused",
                focus_areas=["challenges", "limitations"]
            )
            
            assert result.reasoning_type == "summarization"
            assert result.metadata['focus_areas'] == ["challenges", "limitations"]
    
    def test_parse_summarization_response(self, summarization_agent):
        """Test parsing of summarization response"""
        response = """
MAIN SUMMARY:
This is the main summary content with key points and important details.

KEY INSIGHTS:
- First key insight
- Second key insight
- Third key insight

RELEVANCE ASSESSMENT:
The content is highly relevant to the query and addresses all main points.

CONFIDENCE METRICS:
Completeness: 0.8
Accuracy: 0.9
Relevance: 0.85
"""
        
        result = summarization_agent._parse_summarization_response(response)
        
        assert 'main_summary' in result
        assert 'key_insights' in result
        assert 'relevance_assessment' in result
        assert 'confidence_metrics' in result
        
        assert len(result['key_insights']) == 3
        assert result['confidence_metrics']['completeness'] == 0.8
        assert result['confidence_metrics']['accuracy'] == 0.9
        assert result['confidence_metrics']['relevance'] == 0.85

class TestResearchAgent:
    """Test suite for ResearchAgent"""
    
    @pytest.fixture
    def research_agent(self):
        return ResearchAgent()
    
    @pytest.fixture
    def sample_research_context(self):
        return """
        Quantum computing represents a paradigm shift in computational technology. Unlike classical 
        computers that use bits (0 or 1), quantum computers use quantum bits (qubits) that can exist 
        in superposition states. This allows quantum computers to perform certain calculations 
        exponentially faster than classical computers. Key applications include cryptography, 
        optimization, and simulation of quantum systems. Major companies like IBM, Google, and 
        Microsoft are investing heavily in quantum computing research. However, current quantum 
        computers are still in early stages, facing challenges like quantum decoherence and error rates.
        """
    
    @pytest.mark.asyncio
    async def test_comprehensive_research(self, research_agent, sample_research_context):
        """Test comprehensive research analysis"""
        with patch.object(research_agent, '_call_llm') as mock_llm:
            mock_llm.return_value = """
BACKGROUND ANALYSIS:
Quantum computing emerged from quantum mechanics principles developed in the early 20th century. 
The concept was first proposed by Richard Feynman in 1982 as a way to simulate quantum systems efficiently.

CURRENT STATE ASSESSMENT:
Current quantum computers are in the NISQ (Noisy Intermediate-Scale Quantum) era, with limited 
qubits and high error rates. Companies like IBM and Google have achieved quantum supremacy in 
specific tasks but practical applications remain limited.

KEY RELATIONSHIPS AND CONNECTIONS:
Quantum computing connects quantum physics, computer science, and mathematics. It has implications 
for cryptography (breaking current encryption), optimization (solving complex problems), and 
scientific simulation (drug discovery, materials science).

IMPLICATIONS AND SIGNIFICANCE:
Quantum computing could revolutionize fields requiring massive computational power. It threatens 
current cryptographic systems but also enables new secure communication methods through quantum cryptography.

KNOWLEDGE GAPS AND LIMITATIONS:
Major gaps include scalability challenges, error correction methods, and practical algorithm development. 
Current systems require extreme cooling and isolation.

RESEARCH CONFIDENCE:
Completeness of analysis: 0.8
Reliability of sources: 0.7
Depth of coverage: 0.9
"""
            
            result = await research_agent.reason(
                query="Analyze the current state and future of quantum computing",
                context=sample_research_context,
                research_depth="comprehensive"
            )
            
            assert isinstance(result, ReasoningResult)
            assert result.reasoning_type == "research"
            assert 0.0 <= result.confidence <= 1.0
            
            # Check metadata
            metadata = result.metadata
            assert metadata['research_depth'] == "comprehensive"
            assert 'background_analysis' in metadata
            assert 'current_state' in metadata
            assert 'implications' in metadata
            assert 'research_confidence' in metadata
            
            # Verify confidence metrics
            confidence_metrics = metadata['research_confidence']
            assert 'completeness_of_analysis' in confidence_metrics
            assert 'reliability_of_sources' in confidence_metrics
            assert 'depth_of_coverage' in confidence_metrics
    
    @pytest.mark.asyncio
    async def test_focused_research(self, research_agent, sample_research_context):
        """Test research with specific focus areas"""
        with patch.object(research_agent, '_call_llm') as mock_llm:
            mock_llm.return_value = """
BACKGROUND ANALYSIS:
Limited background analysis focusing on technical foundations.

CURRENT STATE ASSESSMENT:
Current quantum computers face significant technical challenges including decoherence and error rates.

KEY RELATIONSHIPS AND CONNECTIONS:
Strong connections to cryptography and security implications.

IMPLICATIONS AND SIGNIFICANCE:
Major implications for cybersecurity and encryption methods.

KNOWLEDGE GAPS AND LIMITATIONS:
Significant gaps in practical implementation and scalability.

RESEARCH CONFIDENCE:
Completeness of analysis: 0.6
Reliability of sources: 0.8
Depth of coverage: 0.7
"""
            
            result = await research_agent.reason(
                query="What are the security implications of quantum computing?",
                context=sample_research_context,
                research_depth="focused",
                research_areas=["implications", "security"]
            )
            
            assert result.reasoning_type == "research"
            assert result.metadata['research_depth'] == "focused"
            assert result.metadata['research_areas'] == ["implications", "security"]

class TestAgentCoordinator:
    """Test suite for AgentCoordinator"""
    
    @pytest.fixture
    def agent_coordinator(self):
        return AgentCoordinator()
    
    @pytest.fixture
    def mock_reasoning_results(self):
        return [
            ReasoningResult(
                reasoning_type="fact_checking",
                confidence=0.8,
                explanation="Fact check results",
                supporting_evidence=["Evidence 1", "Evidence 2"],
                metadata={
                    "fact_check_results": [{"claim": "Test claim", "status": "VERIFIED"}],
                    "claims_analyzed": 1,
                    "verified_claims": 1,
                    "contradicted_claims": 0,
                    "processing_time": 1.5
                }
            ),
            ReasoningResult(
                reasoning_type="summarization",
                confidence=0.9,
                explanation="Summary results",
                supporting_evidence=["Summary content"],
                metadata={
                    "key_insights": ["Insight 1", "Insight 2"],
                    "word_count": 150,
                    "summary_type": "comprehensive",
                    "processing_time": 2.0
                }
            )
        ]
    
    @pytest.mark.asyncio
    async def test_coordinate_agents(self, agent_coordinator):
        """Test agent coordination"""
        with patch.object(agent_coordinator.fact_checking_agent, 'reason') as mock_fact_check, \
             patch.object(agent_coordinator.summarization_agent, 'reason') as mock_summarize:
            
            mock_fact_check.return_value = ReasoningResult(
                reasoning_type="fact_checking",
                confidence=0.8,
                explanation="Fact check",
                supporting_evidence=["Evidence"],
                metadata={}
            )
            
            mock_summarize.return_value = ReasoningResult(
                reasoning_type="summarization",
                confidence=0.9,
                explanation="Summary",
                supporting_evidence=["Summary"],
                metadata={}
            )
            
            results = await agent_coordinator.coordinate_agents(
                query="Test query",
                context="Test context",
                agent_types=["fact_checking", "summarization"]
            )
            
            assert len(results) == 2
            assert results[0].reasoning_type == "fact_checking"
            assert results[1].reasoning_type == "summarization"
            
            mock_fact_check.assert_called_once()
            mock_summarize.assert_called_once()
    
    def test_determine_relevant_agents(self, agent_coordinator):
        """Test automatic agent selection based on query"""
        # Test fact-checking query
        fact_query = "Is this claim true and accurate?"
        agents = agent_coordinator._determine_relevant_agents(fact_query)
        assert "fact_checking" in agents
        
        # Test summarization query
        summary_query = "Please summarize the main points"
        agents = agent_coordinator._determine_relevant_agents(summary_query)
        assert "summarization" in agents
        
        # Test research query
        research_query = "Analyze the implications of this development"
        agents = agent_coordinator._determine_relevant_agents(research_query)
        assert "research" in agents
        
        # Test general query (should default to research)
        general_query = "Tell me about this topic"
        agents = agent_coordinator._determine_relevant_agents(general_query)
        assert "research" in agents
    
    @pytest.mark.asyncio
    async def test_integrate_results(self, agent_coordinator, mock_reasoning_results):
        """Test integration of multiple agent results"""
        integration = await agent_coordinator.integrate_results(mock_reasoning_results)
        
        assert integration['agent_count'] == 2
        assert 0.0 <= integration['overall_confidence'] <= 1.0
        assert len(integration['reasoning_types']) == 2
        assert "fact_checking" in integration['reasoning_types']
        assert "summarization" in integration['reasoning_types']
        
        # Check combined evidence
        assert len(integration['combined_evidence']) >= 2
        
        # Check key insights
        assert len(integration['key_insights']) > 0
        
        # Check metadata summary
        assert 'fact_checking' in integration['metadata_summary']
        assert 'summarization' in integration['metadata_summary']

class TestReasoningEngineIntegration:
    """Integration tests for ReasoningEngine with specialized agents"""
    
    @pytest.fixture
    def reasoning_engine(self):
        return ReasoningEngine()
    
    @pytest.mark.asyncio
    async def test_apply_specialized_agents(self, reasoning_engine):
        """Test applying specialized agents through reasoning engine"""
        with patch.object(reasoning_engine.agent_coordinator, 'coordinate_agents') as mock_coordinate:
            mock_coordinate.return_value = [
                ReasoningResult(
                    reasoning_type="fact_checking",
                    confidence=0.8,
                    explanation="Test",
                    supporting_evidence=["Evidence"],
                    metadata={}
                )
            ]
            
            results = await reasoning_engine.apply_specialized_agents(
                query="Test query",
                context="Test context",
                agent_types=["fact_checking"]
            )
            
            assert len(results) == 1
            assert results[0].reasoning_type == "fact_checking"
            mock_coordinate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fact_check_method(self, reasoning_engine):
        """Test direct fact-checking method"""
        with patch.object(reasoning_engine.agent_coordinator.fact_checking_agent, 'reason') as mock_reason:
            mock_reason.return_value = ReasoningResult(
                reasoning_type="fact_checking",
                confidence=0.8,
                explanation="Fact check result",
                supporting_evidence=["Evidence"],
                metadata={}
            )
            
            result = await reasoning_engine.fact_check(
                query="Test query",
                context="Test context",
                claims=["Test claim"]
            )
            
            assert result.reasoning_type == "fact_checking"
            mock_reason.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_summarize_method(self, reasoning_engine):
        """Test direct summarization method"""
        with patch.object(reasoning_engine.agent_coordinator.summarization_agent, 'reason') as mock_reason:
            mock_reason.return_value = ReasoningResult(
                reasoning_type="summarization",
                confidence=0.9,
                explanation="Summary result",
                supporting_evidence=["Summary"],
                metadata={}
            )
            
            result = await reasoning_engine.summarize(
                query="Test query",
                context="Test context",
                summary_type="brief",
                max_length=100
            )
            
            assert result.reasoning_type == "summarization"
            mock_reason.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_research_method(self, reasoning_engine):
        """Test direct research method"""
        with patch.object(reasoning_engine.agent_coordinator.research_agent, 'reason') as mock_reason:
            mock_reason.return_value = ReasoningResult(
                reasoning_type="research",
                confidence=0.7,
                explanation="Research result",
                supporting_evidence=["Research findings"],
                metadata={}
            )
            
            result = await reasoning_engine.research(
                query="Test query",
                context="Test context",
                research_depth="comprehensive"
            )
            
            assert result.reasoning_type == "research"
            mock_reason.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__])