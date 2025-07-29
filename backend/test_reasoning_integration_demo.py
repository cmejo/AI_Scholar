#!/usr/bin/env python3
"""
Demo script for Task 5.4: Reasoning Engine Integration with RAG Workflow
Demonstrates the integrated reasoning capabilities in the RAG service.
"""
import asyncio
import sys
import os
import logging
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.schemas import ReasoningResult, UncertaintyScore

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class MockReasoningEngine:
    """Mock reasoning engine for demonstration"""
    
    def should_apply_reasoning(self, query: str, threshold: float = 0.1) -> bool:
        """Mock reasoning decision based on query complexity"""
        complexity_indicators = [
            'why', 'how', 'cause', 'effect', 'because', 'reason', 'explain',
            'compare', 'similar', 'different', 'like', 'analogy', 'relationship'
        ]
        
        query_lower = query.lower()
        complexity_score = sum(1 for indicator in complexity_indicators if indicator in query_lower)
        query_words = query.split()
        
        if not query_words:
            return False
            
        normalized_complexity = complexity_score / len(query_words)
        return normalized_complexity >= threshold
    
    async def apply_reasoning(self, query: str, context: str, reasoning_types: List[str]) -> List[ReasoningResult]:
        """Mock reasoning application with realistic results"""
        results = []
        
        if "causal" in reasoning_types:
            # Generate causal reasoning based on query content
            if "machine learning" in query.lower() and "data" in query.lower():
                results.append(ReasoningResult(
                    reasoning_type="causal",
                    confidence=0.85,
                    explanation="Identified causal relationship between data quality and model performance",
                    supporting_evidence=["Large datasets provide more examples for pattern recognition"],
                    metadata={
                        "causal_relations": [
                            {"cause": "Large training datasets", "effect": "Better model generalization"},
                            {"cause": "Data quality", "effect": "Model accuracy"}
                        ]
                    }
                ))
            elif "neural network" in query.lower():
                results.append(ReasoningResult(
                    reasoning_type="causal",
                    confidence=0.78,
                    explanation="Analyzed causal mechanisms in neural network learning",
                    supporting_evidence=["Backpropagation enables weight adjustment"],
                    metadata={
                        "causal_relations": [
                            {"cause": "Gradient descent", "effect": "Weight optimization"},
                            {"cause": "Multiple layers", "effect": "Feature hierarchy"}
                        ]
                    }
                ))
        
        if "analogical" in reasoning_types:
            # Generate analogical reasoning
            if "brain" in query.lower() or "human" in query.lower():
                results.append(ReasoningResult(
                    reasoning_type="analogical",
                    confidence=0.72,
                    explanation="Found analogies between artificial and biological neural networks",
                    supporting_evidence=["Both use interconnected processing units"],
                    metadata={
                        "analogies": [
                            {
                                "source_domain": "Biological brain",
                                "target_domain": "Artificial neural network",
                                "similarity_score": 0.75,
                                "explanation": "Both process information through connected nodes"
                            }
                        ]
                    }
                ))
        
        return results
    
    async def apply_specialized_agents(self, query: str, context: str, agents: List[str]) -> List[ReasoningResult]:
        """Mock specialized agents with realistic outputs"""
        results = []
        
        for agent in agents:
            if agent == "fact_checking":
                results.append(ReasoningResult(
                    reasoning_type="fact_checking",
                    confidence=0.88,
                    explanation="Verified factual claims against available sources",
                    supporting_evidence=["Cross-referenced with research literature"],
                    metadata={
                        "fact_check_results": [
                            {"claim": "Deep learning requires large datasets", "status": "VERIFIED", "confidence": 0.9},
                            {"claim": "GPUs accelerate training", "status": "VERIFIED", "confidence": 0.95}
                        ]
                    }
                ))
            
            elif agent == "summarization":
                results.append(ReasoningResult(
                    reasoning_type="summarization",
                    confidence=0.82,
                    explanation="Generated comprehensive summary of key concepts",
                    supporting_evidence=["Extracted main themes and relationships"],
                    metadata={
                        "key_insights": [
                            "Machine learning effectiveness depends on data quality and quantity",
                            "Neural networks learn hierarchical feature representations",
                            "Modern architectures like transformers have revolutionized NLP"
                        ],
                        "summary_type": "comprehensive"
                    }
                ))
            
            elif agent == "research":
                results.append(ReasoningResult(
                    reasoning_type="research",
                    confidence=0.79,
                    explanation="Conducted comprehensive research analysis",
                    supporting_evidence=["Analyzed current trends and developments"],
                    metadata={
                        "research_areas": ["current_state", "recent_advances", "future_directions"],
                        "key_findings": [
                            "Transformer architectures dominate current NLP research",
                            "Self-supervised learning is becoming increasingly important",
                            "Multimodal AI is an emerging frontier"
                        ]
                    }
                ))
        
        return results
    
    async def quantify_uncertainty(self, response: str, sources: List[Dict], reasoning_results: List[ReasoningResult] = None) -> UncertaintyScore:
        """Mock uncertainty quantification"""
        # Simple mock calculation
        base_confidence = 0.75
        
        if reasoning_results:
            reasoning_confidence = sum(r.confidence for r in reasoning_results) / len(reasoning_results)
            base_confidence = (base_confidence + reasoning_confidence) / 2
        
        uncertainty_factors = []
        if base_confidence < 0.8:
            uncertainty_factors.append("Limited source verification")
        if len(sources) < 3:
            uncertainty_factors.append("Few supporting sources")
        
        return UncertaintyScore(
            confidence=base_confidence,
            uncertainty_factors=uncertainty_factors,
            reliability_score=base_confidence * 0.9,
            source_quality=0.8
        )

class ReasoningIntegrationDemo:
    """Demo class showing reasoning integration capabilities"""
    
    def __init__(self):
        self.reasoning_engine = MockReasoningEngine()
    
    def _determine_reasoning_types(self, query: str, response: str) -> List[str]:
        """Determine which reasoning types to apply"""
        reasoning_types = []
        query_lower = query.lower()
        
        causal_indicators = [
            "why", "because", "cause", "reason", "due to", "leads to", 
            "results in", "consequence", "effect", "impact", "influence"
        ]
        if any(indicator in query_lower for indicator in causal_indicators):
            reasoning_types.append("causal")
        
        analogical_indicators = [
            "like", "similar", "compare", "analogy", "resembles", "parallel",
            "equivalent", "corresponds", "matches", "relates to"
        ]
        if any(indicator in query_lower for indicator in analogical_indicators):
            reasoning_types.append("analogical")
        
        return reasoning_types
    
    def _determine_specialized_agents(self, query: str, response: str, context: str) -> List[str]:
        """Determine which specialized agents to apply"""
        agents = []
        query_lower = query.lower()
        response_lower = response.lower()
        
        fact_check_indicators = [
            "fact", "proven", "research shows", "studies indicate", "evidence",
            "verified", "confirmed", "documented", "established", "true", "false"
        ]
        if (any(indicator in response_lower for indicator in fact_check_indicators) or
            any(word in query_lower for word in ["verify", "check", "confirm", "validate"])):
            agents.append("fact_checking")
        
        summary_indicators = [
            "summarize", "summary", "overview", "brief", "main points",
            "key points", "outline", "digest", "abstract"
        ]
        if (any(indicator in query_lower for indicator in summary_indicators) or
            len(context) > 2000):
            agents.append("summarization")
        
        research_indicators = [
            "research", "investigate", "explore", "analyze", "examine",
            "study", "comprehensive", "detailed analysis", "in-depth"
        ]
        if any(indicator in query_lower for indicator in research_indicators):
            agents.append("research")
        
        return agents
    
    def _should_apply_reasoning_selective(self, query: str, response: str, reasoning_preference: str) -> bool:
        """Determine if reasoning should be applied"""
        if reasoning_preference == "always":
            return True
        if reasoning_preference == "never":
            return False
        
        if reasoning_preference == "adaptive":
            base_complexity = self.reasoning_engine.should_apply_reasoning(query, 0.02)  # Lower threshold
            
            complex_patterns = [
                len(query.split()) > 10,  # Lower threshold
                "?" in query and len(query.split("?")) > 2,
                any(word in response.lower() for word in [
                    "complex", "complicated", "multiple", "various", "several"
                ]),
                len(response.split()) > 50,  # Lower threshold
                any(word in query.lower() for word in [
                    "analyze", "comprehensive", "detail", "verify", "research"
                ])
            ]
            
            additional_complexity = sum(complex_patterns) >= 1  # Lower threshold
            return base_complexity or additional_complexity
        
        return self.reasoning_engine.should_apply_reasoning(query)
    
    def _determine_reasoning_intensity(self, query: str, reasoning_preference: str) -> str:
        """Determine reasoning intensity"""
        if reasoning_preference == "always":
            return "comprehensive"
        
        high_intensity_indicators = [
            "analyze", "explain in detail", "comprehensive", "thorough",
            "why exactly", "how specifically", "what are all"
        ]
        
        medium_intensity_indicators = [
            "explain", "describe", "compare"
        ]
        
        query_lower = query.lower()
        
        if any(indicator in query_lower for indicator in high_intensity_indicators):
            return "comprehensive"
        elif any(indicator in query_lower for indicator in medium_intensity_indicators):
            return "moderate"
        elif any(word in query_lower for word in ["what", "how", "why"]) and len(query.split()) > 5:
            return "moderate"
        else:
            return "basic"
    
    async def _enhance_response_with_reasoning(self, response: str, reasoning_results: List[ReasoningResult]) -> str:
        """Enhance response with reasoning insights"""
        if not reasoning_results:
            return response
        
        reasoning_by_type = {}
        for result in reasoning_results:
            if result.reasoning_type not in reasoning_by_type:
                reasoning_by_type[result.reasoning_type] = []
            reasoning_by_type[result.reasoning_type].append(result)
        
        reasoning_insights = []
        
        # Add causal reasoning insights
        if "causal" in reasoning_by_type:
            causal_results = reasoning_by_type["causal"]
            high_confidence_causal = [r for r in causal_results if r.confidence > 0.7]
            if high_confidence_causal:
                causal_relations = []
                for result in high_confidence_causal:
                    relations = result.metadata.get("causal_relations", [])
                    for rel in relations[:2]:
                        causal_relations.append(f"{rel['cause']} → {rel['effect']}")
                
                if causal_relations:
                    reasoning_insights.append(
                        f"**Causal Analysis:** {'; '.join(causal_relations)}"
                    )
        
        # Add analogical reasoning insights
        if "analogical" in reasoning_by_type:
            analogical_results = reasoning_by_type["analogical"]
            high_confidence_analogical = [r for r in analogical_results if r.confidence > 0.6]
            if high_confidence_analogical:
                analogies = []
                for result in high_confidence_analogical:
                    analogy_data = result.metadata.get("analogies", [])
                    for analogy in analogy_data[:1]:
                        analogies.append(
                            f"{analogy['source_domain']} ↔ {analogy['target_domain']}"
                        )
                
                if analogies:
                    reasoning_insights.append(
                        f"**Analogical Insights:** {'; '.join(analogies)}"
                    )
        
        # Add fact-checking insights
        if "fact_checking" in reasoning_by_type:
            fact_check_results = reasoning_by_type["fact_checking"]
            for result in fact_check_results:
                fact_checks = result.metadata.get("fact_check_results", [])
                verified_count = len([fc for fc in fact_checks if fc.get("status") == "VERIFIED"])
                total_count = len(fact_checks)
                
                if total_count > 0:
                    reasoning_insights.append(
                        f"**Fact Verification:** {verified_count}/{total_count} claims verified"
                    )
        
        # Add summarization insights
        if "summarization" in reasoning_by_type:
            summary_results = reasoning_by_type["summarization"]
            for result in summary_results:
                key_insights = result.metadata.get("key_insights", [])
                if key_insights:
                    reasoning_insights.append(
                        f"**Key Insights:** {'; '.join(key_insights[:2])}"
                    )
        
        # Add research insights
        if "research" in reasoning_by_type:
            research_results = reasoning_by_type["research"]
            for result in research_results:
                key_findings = result.metadata.get("key_findings", [])
                if key_findings:
                    reasoning_insights.append(
                        f"**Research Findings:** {'; '.join(key_findings[:2])}"
                    )
        
        if reasoning_insights:
            enhanced_response = response + "\n\n---\n\n" + "\n\n".join(reasoning_insights)
            return enhanced_response
        
        return response
    
    async def demonstrate_reasoning_integration(self):
        """Demonstrate the complete reasoning integration workflow"""
        logger.info("🚀 REASONING ENGINE INTEGRATION DEMONSTRATION")
        logger.info("=" * 80)
        
        # Demo scenarios
        scenarios = [
            {
                "name": "Causal Reasoning Query",
                "query": "Why do machine learning models perform better with larger datasets?",
                "response": "Machine learning models perform better with larger datasets because they provide more examples for pattern recognition and reduce overfitting.",
                "context": "Research shows that dataset size is crucial for model performance. Large datasets help models generalize better and learn more robust patterns.",
                "preference": "adaptive"
            },
            {
                "name": "Analogical Reasoning Query", 
                "query": "How are neural networks similar to the human brain?",
                "response": "Neural networks are similar to the human brain in that both use interconnected nodes to process information and learn from experience.",
                "context": "Both artificial neural networks and biological brains consist of interconnected processing units that can adapt and learn.",
                "preference": "adaptive"
            },
            {
                "name": "Fact-Checking Query",
                "query": "Verify the claim that deep learning requires GPUs for training",
                "response": "Research shows that GPUs significantly accelerate deep learning training due to their parallel processing capabilities.",
                "context": "Studies indicate that GPU acceleration can speed up training by 10-100x compared to CPUs for deep learning workloads.",
                "preference": "adaptive"
            },
            {
                "name": "Comprehensive Analysis Query",
                "query": "Analyze in detail the comprehensive impact of transformer architectures on natural language processing",
                "response": "Transformer architectures have revolutionized NLP by enabling better handling of long-range dependencies and parallel processing.",
                "context": "Transformers introduced self-attention mechanisms that have become the foundation for modern NLP models like BERT and GPT.",
                "preference": "adaptive"
            },
            {
                "name": "Simple Query (No Reasoning)",
                "query": "What is Python?",
                "response": "Python is a high-level programming language known for its simplicity and readability.",
                "context": "Python was created by Guido van Rossum and is widely used in web development, data science, and AI.",
                "preference": "adaptive"
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            logger.info(f"\n📋 SCENARIO {i}: {scenario['name']}")
            logger.info("-" * 60)
            
            await self.demonstrate_scenario(scenario)
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ REASONING INTEGRATION DEMONSTRATION COMPLETE")
        logger.info("=" * 80)
    
    async def demonstrate_scenario(self, scenario: Dict[str, Any]):
        """Demonstrate reasoning integration for a specific scenario"""
        query = scenario["query"]
        response = scenario["response"]
        context = scenario["context"]
        preference = scenario["preference"]
        
        logger.info(f"🔍 Query: {query}")
        logger.info(f"📝 Initial Response: {response}")
        
        # Step 1: Check if reasoning should be applied
        should_apply = self._should_apply_reasoning_selective(query, response, preference)
        logger.info(f"🤔 Should Apply Reasoning: {should_apply}")
        
        if not should_apply:
            logger.info("⏭️  Skipping reasoning (query complexity below threshold)")
            return
        
        # Step 2: Determine reasoning intensity
        intensity = self._determine_reasoning_intensity(query, preference)
        logger.info(f"⚡ Reasoning Intensity: {intensity}")
        
        # Step 3: Determine reasoning types
        reasoning_types = self._determine_reasoning_types(query, response)
        logger.info(f"🧠 Reasoning Types: {reasoning_types}")
        
        # Step 4: Determine specialized agents
        specialized_agents = self._determine_specialized_agents(query, response, context)
        logger.info(f"🤖 Specialized Agents: {specialized_agents}")
        
        # Step 5: Apply reasoning
        all_reasoning_results = []
        
        if reasoning_types:
            core_reasoning = await self.reasoning_engine.apply_reasoning(
                query, context, reasoning_types
            )
            all_reasoning_results.extend(core_reasoning)
            logger.info(f"✨ Applied {len(core_reasoning)} core reasoning results")
        
        if specialized_agents:
            if intensity == "comprehensive":
                # Apply all agents
                specialized_results = await self.reasoning_engine.apply_specialized_agents(
                    query, context, specialized_agents
                )
            elif intensity == "moderate":
                # Apply only the first agent
                specialized_results = await self.reasoning_engine.apply_specialized_agents(
                    query, context, specialized_agents[:1]
                )
            else:
                # Basic intensity - no specialized agents
                specialized_results = []
            
            all_reasoning_results.extend(specialized_results)
            logger.info(f"🔬 Applied {len(specialized_results)} specialized agent results")
        
        # Step 6: Calculate uncertainty
        mock_sources = [{"content": context, "relevance": 0.8}]
        uncertainty_score = await self.reasoning_engine.quantify_uncertainty(
            response, mock_sources, all_reasoning_results
        )
        logger.info(f"📊 Uncertainty Score: {uncertainty_score.confidence:.2f}")
        if uncertainty_score.uncertainty_factors:
            logger.info(f"⚠️  Uncertainty Factors: {', '.join(uncertainty_score.uncertainty_factors)}")
        
        # Step 7: Enhance response with reasoning
        enhanced_response = await self._enhance_response_with_reasoning(
            response, all_reasoning_results
        )
        
        if enhanced_response != response:
            logger.info("🎯 Enhanced Response:")
            logger.info(enhanced_response)
        else:
            logger.info("📄 Response unchanged (no reasoning insights to add)")
        
        # Step 8: Summary
        logger.info(f"📈 Summary: Applied {len(all_reasoning_results)} reasoning results with {uncertainty_score.confidence:.1%} confidence")

async def main():
    """Main demonstration execution"""
    demo = ReasoningIntegrationDemo()
    await demo.demonstrate_reasoning_integration()

if __name__ == "__main__":
    asyncio.run(main())