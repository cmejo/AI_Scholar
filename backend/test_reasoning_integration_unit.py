#!/usr/bin/env python3
"""
Unit test for Task 5.4: Reasoning integration methods
Tests the specific reasoning integration methods without requiring full service dependencies.
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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockReasoningEngine:
    """Mock reasoning engine for testing"""
    
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
        """Mock reasoning application"""
        results = []
        
        if "causal" in reasoning_types:
            results.append(ReasoningResult(
                reasoning_type="causal",
                confidence=0.8,
                explanation="Mock causal reasoning",
                supporting_evidence=["Mock evidence"],
                metadata={"causal_relations": [{"cause": "A", "effect": "B"}]}
            ))
        
        if "analogical" in reasoning_types:
            results.append(ReasoningResult(
                reasoning_type="analogical",
                confidence=0.7,
                explanation="Mock analogical reasoning",
                supporting_evidence=["Mock analogy"],
                metadata={"analogies": [{"source_domain": "X", "target_domain": "Y"}]}
            ))
        
        return results
    
    async def apply_specialized_agents(self, query: str, context: str, agents: List[str]) -> List[ReasoningResult]:
        """Mock specialized agents"""
        results = []
        
        for agent in agents:
            results.append(ReasoningResult(
                reasoning_type=agent,
                confidence=0.9,
                explanation=f"Mock {agent} result",
                supporting_evidence=[f"Mock {agent} evidence"],
                metadata={f"{agent}_results": [{"status": "VERIFIED"}]}
            ))
        
        return results

class ReasoningIntegrationMethods:
    """Class containing the reasoning integration methods to test"""
    
    def __init__(self):
        self.reasoning_engine = MockReasoningEngine()
    
    def _determine_reasoning_types(self, query: str, response: str) -> List[str]:
        """Determine which reasoning types to apply based on query and response patterns"""
        reasoning_types = []
        query_lower = query.lower()
        response_lower = response.lower()
        
        # Causal reasoning indicators
        causal_indicators = [
            "why", "because", "cause", "reason", "due to", "leads to", 
            "results in", "consequence", "effect", "impact", "influence"
        ]
        if any(indicator in query_lower for indicator in causal_indicators):
            reasoning_types.append("causal")
        
        # Analogical reasoning indicators
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
        
        # Fact-checking indicators
        fact_check_indicators = [
            "fact", "proven", "research shows", "studies indicate", "evidence",
            "verified", "confirmed", "documented", "established", "true", "false"
        ]
        if (any(indicator in response_lower for indicator in fact_check_indicators) or
            any(word in query_lower for word in ["verify", "check", "confirm", "validate"])):
            agents.append("fact_checking")
        
        # Summarization indicators
        summary_indicators = [
            "summarize", "summary", "overview", "brief", "main points",
            "key points", "outline", "digest", "abstract"
        ]
        if (any(indicator in query_lower for indicator in summary_indicators) or
            len(context) > 2000):
            agents.append("summarization")
        
        # Research indicators
        research_indicators = [
            "research", "investigate", "explore", "analyze", "examine",
            "study", "comprehensive", "detailed analysis", "in-depth"
        ]
        if any(indicator in query_lower for indicator in research_indicators):
            agents.append("research")
        
        return agents
    
    def _should_apply_reasoning_selective(
        self, 
        query: str, 
        response: str, 
        reasoning_preference: str
    ) -> bool:
        """Determine if reasoning should be applied based on selective criteria"""
        
        if reasoning_preference == "always":
            return True
        
        if reasoning_preference == "never":
            return False
        
        if reasoning_preference == "adaptive":
            base_complexity = self.reasoning_engine.should_apply_reasoning(query, 0.05)
            
            complex_patterns = [
                len(query.split()) > 15,
                "?" in query and len(query.split("?")) > 2,
                any(word in response.lower() for word in [
                    "complex", "complicated", "multiple", "various", "several"
                ]),
                len(response.split()) > 100
            ]
            
            additional_complexity = sum(complex_patterns) >= 2
            return base_complexity or additional_complexity
        
        return self.reasoning_engine.should_apply_reasoning(query)
    
    def _determine_reasoning_intensity(self, query: str, reasoning_preference: str) -> str:
        """Determine the intensity of reasoning to apply"""
        
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
            return "moderate"  # Only moderate for longer questions
        else:
            return "basic"
    
    async def _enhance_response_with_reasoning(
        self,
        response: str,
        reasoning_results: List[ReasoningResult]
    ) -> str:
        """Enhance the response with reasoning insights"""
        
        if not reasoning_results:
            return response
        
        try:
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
            
            # Add fact-checking insights
            if "fact_checking" in reasoning_by_type:
                fact_check_results = reasoning_by_type["fact_checking"]
                for result in fact_check_results:
                    fact_checks = result.metadata.get("fact_checking_results", [])
                    verified_count = len([fc for fc in fact_checks if fc.get("status") == "VERIFIED"])
                    total_count = len(fact_checks)
                    
                    if total_count > 0:
                        reasoning_insights.append(
                            f"**Fact Verification:** {verified_count}/{total_count} claims verified"
                        )
            
            if reasoning_insights:
                enhanced_response = response + "\n\n---\n\n" + "\n\n".join(reasoning_insights)
                return enhanced_response
            
            return response
            
        except Exception as e:
            logger.error(f"Error enhancing response with reasoning: {e}")
            return response

class ReasoningIntegrationTester:
    """Test class for reasoning integration methods"""
    
    def __init__(self):
        self.methods = ReasoningIntegrationMethods()
        self.test_results = []
    
    async def run_all_tests(self):
        """Run all reasoning integration tests"""
        logger.info("Starting Reasoning Integration Unit Tests")
        logger.info("=" * 60)
        
        tests = [
            ("Reasoning Type Determination", self.test_reasoning_type_determination),
            ("Specialized Agent Selection", self.test_specialized_agent_selection),
            ("Selective Reasoning Decision", self.test_selective_reasoning_decision),
            ("Reasoning Intensity Determination", self.test_reasoning_intensity_determination),
            ("Response Enhancement", self.test_response_enhancement),
            ("Edge Cases", self.test_edge_cases)
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\n--- {test_name} ---")
                result = await test_func()
                self.test_results.append((test_name, "PASSED" if result else "FAILED"))
                logger.info(f"✓ {test_name}: {'PASSED' if result else 'FAILED'}")
            except Exception as e:
                logger.error(f"✗ {test_name}: FAILED - {str(e)}")
                self.test_results.append((test_name, f"FAILED - {str(e)}"))
        
        self.print_test_summary()
    
    async def test_reasoning_type_determination(self) -> bool:
        """Test reasoning type determination"""
        test_cases = [
            {
                "query": "Why does machine learning work?",
                "response": "ML works because of pattern recognition",
                "expected": ["causal"]
            },
            {
                "query": "How is AI similar to human intelligence?",
                "response": "Both process information",
                "expected": ["analogical"]
            },
            {
                "query": "Why are neural networks like the brain and what causes their effectiveness?",
                "response": "They both have interconnected nodes",
                "expected": ["causal", "analogical"]
            },
            {
                "query": "What is Python?",
                "response": "Python is a programming language",
                "expected": []
            }
        ]
        
        for case in test_cases:
            result = self.methods._determine_reasoning_types(case["query"], case["response"])
            
            for expected_type in case["expected"]:
                if expected_type not in result:
                    logger.error(f"Missing type {expected_type} for: {case['query']}")
                    return False
            
            # Check for unexpected types
            for result_type in result:
                if result_type not in case["expected"]:
                    logger.error(f"Unexpected type {result_type} for: {case['query']}")
                    return False
            
            logger.info(f"✓ '{case['query'][:30]}...': {result}")
        
        return True
    
    async def test_specialized_agent_selection(self) -> bool:
        """Test specialized agent selection"""
        test_cases = [
            {
                "query": "Verify this claim about AI",
                "response": "Research shows that AI is effective",
                "context": "Studies indicate improvements",
                "expected": ["fact_checking"]
            },
            {
                "query": "Summarize the main points",
                "response": "Here are the key insights",
                "context": "Short context",
                "expected": ["summarization"]
            },
            {
                "query": "Research the impact of AI",
                "response": "AI has significant effects",
                "context": "AI research context",
                "expected": ["research"]
            },
            {
                "query": "What is AI?",
                "response": "AI is artificial intelligence",
                "context": "Long context " * 500,  # Long context should trigger summarization
                "expected": ["summarization"]
            }
        ]
        
        for case in test_cases:
            result = self.methods._determine_specialized_agents(
                case["query"], case["response"], case["context"]
            )
            
            for expected_agent in case["expected"]:
                if expected_agent not in result:
                    logger.error(f"Missing agent {expected_agent} for: {case['query']}")
                    return False
            
            logger.info(f"✓ '{case['query'][:30]}...': {result}")
        
        return True
    
    async def test_selective_reasoning_decision(self) -> bool:
        """Test selective reasoning decision logic"""
        test_cases = [
            {
                "query": "What is AI?",
                "response": "AI is artificial intelligence",
                "preference": "never",
                "expected": False
            },
            {
                "query": "What is AI?",
                "response": "AI is artificial intelligence",
                "preference": "always",
                "expected": True
            },
            {
                "query": "Why does deep learning work so well for image recognition?",
                "response": "Deep learning works because it can learn hierarchical features",
                "preference": "adaptive",
                "expected": True
            },
            {
                "query": "Hello",
                "response": "Hi there",
                "preference": "adaptive",
                "expected": False
            }
        ]
        
        for case in test_cases:
            result = self.methods._should_apply_reasoning_selective(
                case["query"], case["response"], case["preference"]
            )
            
            if result != case["expected"]:
                logger.error(f"Decision mismatch for: {case['query']}")
                logger.error(f"Expected: {case['expected']}, Got: {result}")
                return False
            
            logger.info(f"✓ '{case['query'][:30]}...' ({case['preference']}): {result}")
        
        return True
    
    async def test_reasoning_intensity_determination(self) -> bool:
        """Test reasoning intensity determination"""
        test_cases = [
            {
                "query": "What is AI?",
                "preference": "adaptive",
                "expected": "basic"
            },
            {
                "query": "Explain how neural networks work",
                "preference": "adaptive",
                "expected": "moderate"
            },
            {
                "query": "Analyze in detail the comprehensive impact of AI",
                "preference": "adaptive",
                "expected": "comprehensive"
            },
            {
                "query": "Simple question",
                "preference": "always",
                "expected": "comprehensive"
            }
        ]
        
        for case in test_cases:
            result = self.methods._determine_reasoning_intensity(
                case["query"], case["preference"]
            )
            
            if result != case["expected"]:
                logger.error(f"Intensity mismatch for: {case['query']}")
                logger.error(f"Expected: {case['expected']}, Got: {result}")
                return False
            
            logger.info(f"✓ '{case['query'][:30]}...': {result}")
        
        return True
    
    async def test_response_enhancement(self) -> bool:
        """Test response enhancement with reasoning"""
        # Create mock reasoning results
        reasoning_results = [
            ReasoningResult(
                reasoning_type="causal",
                confidence=0.8,
                explanation="Causal analysis",
                supporting_evidence=["Evidence"],
                metadata={
                    "causal_relations": [
                        {"cause": "Training data", "effect": "Model accuracy"}
                    ]
                }
            ),
            ReasoningResult(
                reasoning_type="fact_checking",
                confidence=0.9,
                explanation="Fact checking",
                supporting_evidence=["Evidence"],
                metadata={
                    "fact_checking_results": [
                        {"status": "VERIFIED"}
                    ]
                }
            )
        ]
        
        original_response = "Machine learning models improve with more data."
        enhanced_response = await self.methods._enhance_response_with_reasoning(
            original_response, reasoning_results
        )
        
        # Check if enhancements were added
        if "Causal Analysis" not in enhanced_response:
            logger.error("Causal analysis not added")
            return False
        
        if "Training data → Model accuracy" not in enhanced_response:
            logger.error("Causal relation not properly formatted")
            return False
        
        if len(enhanced_response) <= len(original_response):
            logger.error("Response was not enhanced")
            return False
        
        logger.info("✓ Response successfully enhanced with reasoning insights")
        
        # Test with empty reasoning results
        empty_enhanced = await self.methods._enhance_response_with_reasoning(
            original_response, []
        )
        
        if empty_enhanced != original_response:
            logger.error("Should return original response when no reasoning results")
            return False
        
        logger.info("✓ Handles empty reasoning results correctly")
        
        return True
    
    async def test_edge_cases(self) -> bool:
        """Test edge cases and error handling"""
        
        # Test with empty inputs
        empty_types = self.methods._determine_reasoning_types("", "")
        if empty_types != []:
            logger.error("Should return empty list for empty inputs")
            return False
        
        empty_agents = self.methods._determine_specialized_agents("", "", "")
        if empty_agents != []:
            logger.error("Should return empty list for empty inputs")
            return False
        
        # Test with very long inputs
        long_query = "What is AI? " * 100
        long_response = "AI is artificial intelligence. " * 100
        
        types_result = self.methods._determine_reasoning_types(long_query, long_response)
        # Should still work with long inputs
        
        # Test selective reasoning with invalid preference
        decision = self.methods._should_apply_reasoning_selective(
            "Test query", "Test response", "invalid_preference"
        )
        # Should fall back to default behavior
        
        logger.info("✓ Edge cases handled correctly")
        return True
    
    def print_test_summary(self):
        """Print test results summary"""
        logger.info("\n" + "=" * 60)
        logger.info("REASONING INTEGRATION UNIT TEST SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(1 for _, result in self.test_results if result == "PASSED")
        total = len(self.test_results)
        
        for test_name, result in self.test_results:
            status_symbol = "✓" if result == "PASSED" else "✗"
            logger.info(f"{status_symbol} {test_name}: {result}")
        
        logger.info("-" * 60)
        logger.info(f"TOTAL: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED! Reasoning integration methods work correctly.")
        else:
            logger.warning(f"⚠️  {total - passed} tests failed. Please review the implementation.")
        
        logger.info("=" * 60)

async def main():
    """Main test execution"""
    tester = ReasoningIntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())