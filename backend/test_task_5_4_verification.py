#!/usr/bin/env python3
"""
Test script for Task 5.4: Integrate reasoning engine with RAG workflow
Tests the integration of reasoning capabilities into the RAG service.
"""
import asyncio
import sys
import os
import logging
from typing import Dict, Any, List

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.enhanced_rag_service import EnhancedRAGService
from services.reasoning_engine import ReasoningEngine
from models.schemas import ReasoningResult, UncertaintyScore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReasoningIntegrationTester:
    """Test class for reasoning engine integration with RAG workflow"""
    
    def __init__(self):
        self.rag_service = EnhancedRAGService()
        self.reasoning_engine = ReasoningEngine()
        self.test_results = []
    
    async def run_all_tests(self):
        """Run all reasoning integration tests"""
        logger.info("Starting Task 5.4 Reasoning Integration Tests")
        logger.info("=" * 60)
        
        tests = [
            ("Selective Reasoning Application", self.test_selective_reasoning),
            ("Query Complexity Detection", self.test_query_complexity_detection),
            ("Reasoning Type Determination", self.test_reasoning_type_determination),
            ("Specialized Agent Selection", self.test_specialized_agent_selection),
            ("Reasoning Intensity Levels", self.test_reasoning_intensity_levels),
            ("Response Enhancement", self.test_response_enhancement),
            ("End-to-End Integration", self.test_end_to_end_integration),
            ("Error Handling", self.test_error_handling)
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
        
        # Print summary
        self.print_test_summary()
    
    async def test_selective_reasoning(self) -> bool:
        """Test selective reasoning application based on query complexity"""
        logger.info("Testing selective reasoning application...")
        
        # Test cases with different complexity levels
        test_cases = [
            {
                "query": "What is Python?",
                "expected_reasoning": False,
                "description": "Simple query should not trigger reasoning"
            },
            {
                "query": "Why does machine learning require large datasets and how does this impact model performance?",
                "expected_reasoning": True,
                "description": "Complex causal query should trigger reasoning"
            },
            {
                "query": "Compare neural networks to the human brain and explain the similarities",
                "expected_reasoning": True,
                "description": "Analogical query should trigger reasoning"
            }
        ]
        
        for case in test_cases:
            # Test reasoning decision
            should_apply = self.rag_service.reasoning_engine.should_apply_reasoning(case["query"])
            
            if should_apply != case["expected_reasoning"]:
                logger.error(f"Reasoning decision mismatch for: {case['query']}")
                logger.error(f"Expected: {case['expected_reasoning']}, Got: {should_apply}")
                return False
            
            logger.info(f"✓ {case['description']}: {should_apply}")
        
        return True
    
    async def test_query_complexity_detection(self) -> bool:
        """Test query complexity detection mechanisms"""
        logger.info("Testing query complexity detection...")
        
        complexity_tests = [
            ("Simple question", "What is AI?", False),
            ("Causal question", "Why do neural networks work better with more data?", True),
            ("Analogical question", "How is machine learning like human learning?", True),
            ("Multi-part question", "What is deep learning? How does it differ from traditional ML? Why is it effective?", True),
            ("Research question", "Analyze the impact of transformer architectures on NLP", True)
        ]
        
        for description, query, expected_complex in complexity_tests:
            is_complex = self.rag_service.reasoning_engine.should_apply_reasoning(query, 0.05)
            
            if is_complex != expected_complex:
                logger.error(f"Complexity detection failed for: {description}")
                return False
            
            logger.info(f"✓ {description}: {'Complex' if is_complex else 'Simple'}")
        
        return True
    
    async def test_reasoning_type_determination(self) -> bool:
        """Test determination of appropriate reasoning types"""
        logger.info("Testing reasoning type determination...")
        
        type_tests = [
            {
                "query": "Why does overfitting occur in machine learning?",
                "response": "Overfitting happens because the model learns noise",
                "expected_types": ["causal"]
            },
            {
                "query": "How is a neural network similar to the human brain?",
                "response": "Both process information through interconnected nodes",
                "expected_types": ["analogical"]
            },
            {
                "query": "Why are transformers better than RNNs and how are they similar to attention mechanisms?",
                "response": "Transformers use self-attention which is like focusing on relevant parts",
                "expected_types": ["causal", "analogical"]
            }
        ]
        
        for case in type_tests:
            reasoning_types = self.rag_service._determine_reasoning_types(
                case["query"], case["response"]
            )
            
            for expected_type in case["expected_types"]:
                if expected_type not in reasoning_types:
                    logger.error(f"Missing reasoning type {expected_type} for query: {case['query']}")
                    return False
            
            logger.info(f"✓ Query reasoning types: {reasoning_types}")
        
        return True
    
    async def test_specialized_agent_selection(self) -> bool:
        """Test selection of appropriate specialized agents"""
        logger.info("Testing specialized agent selection...")
        
        agent_tests = [
            {
                "query": "Verify if this claim is true: Deep learning requires GPUs",
                "response": "Research shows that GPUs significantly accelerate training",
                "context": "Studies indicate GPU acceleration improves performance",
                "expected_agents": ["fact_checking"]
            },
            {
                "query": "Summarize the main points about machine learning",
                "response": "ML involves training models on data to make predictions",
                "context": "Machine learning is a subset of AI that uses algorithms...",
                "expected_agents": ["summarization"]
            },
            {
                "query": "Research the current state of natural language processing",
                "response": "NLP has advanced significantly with transformer models",
                "context": "Natural language processing encompasses various techniques...",
                "expected_agents": ["research"]
            }
        ]
        
        for case in agent_tests:
            agents = self.rag_service._determine_specialized_agents(
                case["query"], case["response"], case["context"]
            )
            
            for expected_agent in case["expected_agents"]:
                if expected_agent not in agents:
                    logger.error(f"Missing agent {expected_agent} for query: {case['query']}")
                    return False
            
            logger.info(f"✓ Selected agents: {agents}")
        
        return True
    
    async def test_reasoning_intensity_levels(self) -> bool:
        """Test different reasoning intensity levels"""
        logger.info("Testing reasoning intensity levels...")
        
        intensity_tests = [
            {
                "query": "What is ML?",
                "preference": "adaptive",
                "expected_intensity": "basic"
            },
            {
                "query": "Explain how neural networks work",
                "preference": "adaptive", 
                "expected_intensity": "moderate"
            },
            {
                "query": "Analyze in detail the comprehensive impact of deep learning on AI",
                "preference": "adaptive",
                "expected_intensity": "comprehensive"
            },
            {
                "query": "Simple question",
                "preference": "always",
                "expected_intensity": "comprehensive"
            }
        ]
        
        for case in intensity_tests:
            intensity = self.rag_service._determine_reasoning_intensity(
                case["query"], case["preference"]
            )
            
            if intensity != case["expected_intensity"]:
                logger.error(f"Intensity mismatch for: {case['query']}")
                logger.error(f"Expected: {case['expected_intensity']}, Got: {intensity}")
                return False
            
            logger.info(f"✓ Query intensity: {intensity}")
        
        return True
    
    async def test_response_enhancement(self) -> bool:
        """Test response enhancement with reasoning insights"""
        logger.info("Testing response enhancement...")
        
        # Create mock reasoning results
        mock_reasoning_results = [
            ReasoningResult(
                reasoning_type="causal",
                confidence=0.8,
                explanation="Causal analysis performed",
                supporting_evidence=["Evidence 1"],
                metadata={
                    "causal_relations": [
                        {"cause": "Large datasets", "effect": "Better model performance"}
                    ]
                }
            ),
            ReasoningResult(
                reasoning_type="fact_checking",
                confidence=0.9,
                explanation="Fact checking performed",
                supporting_evidence=["Evidence 2"],
                metadata={
                    "fact_check_results": [
                        {"status": "VERIFIED", "claim": "Test claim"}
                    ]
                }
            )
        ]
        
        original_response = "Machine learning models perform better with more data."
        enhanced_response = await self.rag_service._enhance_response_with_reasoning(
            original_response, mock_reasoning_results
        )
        
        # Check if reasoning insights were added
        if "Causal Analysis" not in enhanced_response:
            logger.error("Causal analysis not added to response")
            return False
        
        if "Fact Verification" not in enhanced_response:
            logger.error("Fact verification not added to response")
            return False
        
        logger.info("✓ Response enhanced with reasoning insights")
        logger.info(f"Enhanced response length: {len(enhanced_response)} chars")
        
        return True
    
    async def test_end_to_end_integration(self) -> bool:
        """Test end-to-end reasoning integration"""
        logger.info("Testing end-to-end reasoning integration...")
        
        try:
            # Test with a complex query that should trigger reasoning
            test_query = "Why do transformer models perform better than RNNs in NLP tasks?"
            test_context = """
            Transformer models use self-attention mechanisms that allow them to process 
            sequences in parallel, unlike RNNs which process sequentially. This parallel 
            processing leads to faster training and better capture of long-range dependencies.
            Research shows that transformers achieve state-of-the-art results on many NLP benchmarks.
            """
            
            # Apply selective reasoning
            personalized_context = {
                "user_preferences": {
                    "reasoning_level": {"value": "adaptive"}
                }
            }
            
            reasoning_results = await self.rag_service._apply_selective_reasoning(
                test_query, test_context, "Test response", personalized_context
            )
            
            if not reasoning_results:
                logger.error("No reasoning results generated for complex query")
                return False
            
            # Check if appropriate reasoning types were applied
            reasoning_types = [r.reasoning_type for r in reasoning_results]
            logger.info(f"Applied reasoning types: {reasoning_types}")
            
            # Verify reasoning results have proper structure
            for result in reasoning_results:
                if not hasattr(result, 'reasoning_type') or not hasattr(result, 'confidence'):
                    logger.error("Invalid reasoning result structure")
                    return False
                
                if result.confidence < 0 or result.confidence > 1:
                    logger.error(f"Invalid confidence score: {result.confidence}")
                    return False
            
            logger.info(f"✓ Generated {len(reasoning_results)} reasoning results")
            
            return True
            
        except Exception as e:
            logger.error(f"End-to-end test failed: {str(e)}")
            return False
    
    async def test_error_handling(self) -> bool:
        """Test error handling in reasoning integration"""
        logger.info("Testing error handling...")
        
        try:
            # Test with invalid inputs
            empty_results = await self.rag_service._apply_selective_reasoning(
                "", "", "", {}
            )
            
            # Should handle gracefully and return empty list
            if empty_results is None:
                logger.error("Should return empty list for invalid inputs")
                return False
            
            # Test response enhancement with invalid reasoning results
            enhanced = await self.rag_service._enhance_response_with_reasoning(
                "Test response", []
            )
            
            if enhanced != "Test response":
                logger.error("Should return original response when no reasoning results")
                return False
            
            logger.info("✓ Error handling works correctly")
            return True
            
        except Exception as e:
            logger.error(f"Error handling test failed: {str(e)}")
            return False
    
    def print_test_summary(self):
        """Print test results summary"""
        logger.info("\n" + "=" * 60)
        logger.info("TASK 5.4 REASONING INTEGRATION TEST SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(1 for _, result in self.test_results if result == "PASSED")
        total = len(self.test_results)
        
        for test_name, result in self.test_results:
            status_symbol = "✓" if result == "PASSED" else "✗"
            logger.info(f"{status_symbol} {test_name}: {result}")
        
        logger.info("-" * 60)
        logger.info(f"TOTAL: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED! Reasoning integration is working correctly.")
        else:
            logger.warning(f"⚠️  {total - passed} tests failed. Please review the implementation.")
        
        logger.info("=" * 60)

async def main():
    """Main test execution"""
    tester = ReasoningIntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())