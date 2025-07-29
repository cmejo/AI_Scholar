#!/usr/bin/env python3
"""
Test script for uncertainty quantification system
Demonstrates confidence scoring based on source quality and consensus
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.reasoning_engine import UncertaintyQuantifier, ReasoningResult, ReasoningType
from models.schemas import UncertaintyScore

async def test_uncertainty_quantification():
    """Test the uncertainty quantification system"""
    print("🧪 Testing Uncertainty Quantification System")
    print("=" * 60)
    
    quantifier = UncertaintyQuantifier()
    
    # Test Case 1: High confidence scenario
    print("\n📊 Test Case 1: High Confidence Scenario")
    print("-" * 40)
    
    high_confidence_response = """
    The Earth orbits the Sun in an elliptical path, completing one orbit approximately every 365.25 days.
    This orbital period is well-established through centuries of astronomical observations and is confirmed
    by multiple independent measurements using various techniques.
    """
    
    high_quality_sources = [
        {
            "content": "The Earth's orbital period around the Sun is 365.25636 days, as measured by precise astronomical observations.",
            "relevance": 0.95,
            "document_id": "astronomy_textbook_1"
        },
        {
            "content": "Astronomical measurements confirm that Earth completes one orbit around the Sun in approximately 365.25 days.",
            "relevance": 0.92,
            "document_id": "nasa_orbital_data"
        },
        {
            "content": "The sidereal year, Earth's orbital period relative to the stars, is 365.25636 solar days.",
            "relevance": 0.90,
            "document_id": "celestial_mechanics"
        }
    ]
    
    # Create mock reasoning results with high confidence
    high_confidence_reasoning = [
        ReasoningResult(
            reasoning_type=ReasoningType.CAUSAL.value,
            confidence=0.92,
            explanation="Strong causal relationship established",
            supporting_evidence=["Multiple astronomical observations", "Consistent measurements"],
            metadata={"processing_time": 0.5}
        )
    ]
    
    uncertainty_score = await quantifier.quantify_uncertainty(
        high_confidence_response, 
        high_quality_sources, 
        high_confidence_reasoning
    )
    
    print(f"Response: {high_confidence_response[:100]}...")
    print(f"Overall Confidence: {uncertainty_score.confidence:.3f}")
    print(f"Reliability Score: {uncertainty_score.reliability_score:.3f}")
    print(f"Source Quality: {uncertainty_score.source_quality:.3f}")
    print(f"Uncertainty Factors: {uncertainty_score.uncertainty_factors}")
    
    # Test Case 2: Low confidence scenario
    print("\n📊 Test Case 2: Low Confidence Scenario")
    print("-" * 40)
    
    low_confidence_response = """
    The exact number of alien civilizations in our galaxy is unclear and highly speculative.
    Some estimates suggest there might be thousands, while others indicate there could be none.
    This remains one of the most uncertain questions in astrobiology.
    """
    
    low_quality_sources = [
        {
            "content": "Speculation about alien life varies widely among researchers.",
            "relevance": 0.4,
            "document_id": "blog_post_1"
        },
        {
            "content": "The Drake equation suggests many variables affect alien civilization estimates.",
            "relevance": 0.6,
            "document_id": "popular_science_article"
        }
    ]
    
    # Create mock reasoning results with low confidence
    low_confidence_reasoning = [
        ReasoningResult(
            reasoning_type=ReasoningType.ANALOGICAL.value,
            confidence=0.3,
            explanation="Weak analogical support",
            supporting_evidence=["Speculative comparisons"],
            metadata={"processing_time": 0.8}
        )
    ]
    
    uncertainty_score = await quantifier.quantify_uncertainty(
        low_confidence_response, 
        low_quality_sources, 
        low_confidence_reasoning
    )
    
    print(f"Response: {low_confidence_response[:100]}...")
    print(f"Overall Confidence: {uncertainty_score.confidence:.3f}")
    print(f"Reliability Score: {uncertainty_score.reliability_score:.3f}")
    print(f"Source Quality: {uncertainty_score.source_quality:.3f}")
    print(f"Uncertainty Factors: {uncertainty_score.uncertainty_factors}")
    
    # Test Case 3: Conflicting sources scenario
    print("\n📊 Test Case 3: Conflicting Sources Scenario")
    print("-" * 40)
    
    conflicting_response = """
    The effectiveness of vitamin C supplements for preventing common colds shows mixed results.
    Some studies indicate benefits while others show no significant effect.
    """
    
    conflicting_sources = [
        {
            "content": "Vitamin C supplements significantly reduce cold duration and severity in controlled studies.",
            "relevance": 0.8,
            "document_id": "medical_study_a"
        },
        {
            "content": "Meta-analysis shows vitamin C supplements have no meaningful effect on cold prevention.",
            "relevance": 0.8,
            "document_id": "medical_study_b"
        },
        {
            "content": "Results on vitamin C effectiveness vary depending on study methodology and population.",
            "relevance": 0.7,
            "document_id": "review_paper"
        }
    ]
    
    uncertainty_score = await quantifier.quantify_uncertainty(
        conflicting_response, 
        conflicting_sources
    )
    
    print(f"Response: {conflicting_response[:100]}...")
    print(f"Overall Confidence: {uncertainty_score.confidence:.3f}")
    print(f"Reliability Score: {uncertainty_score.reliability_score:.3f}")
    print(f"Source Quality: {uncertainty_score.source_quality:.3f}")
    print(f"Uncertainty Factors: {uncertainty_score.uncertainty_factors}")
    
    # Test Case 4: No sources scenario
    print("\n📊 Test Case 4: No Sources Scenario")
    print("-" * 40)
    
    no_sources_response = """
    The weather tomorrow will likely be sunny with temperatures around 75°F.
    """
    
    uncertainty_score = await quantifier.quantify_uncertainty(
        no_sources_response, 
        []
    )
    
    print(f"Response: {no_sources_response}")
    print(f"Overall Confidence: {uncertainty_score.confidence:.3f}")
    print(f"Reliability Score: {uncertainty_score.reliability_score:.3f}")
    print(f"Source Quality: {uncertainty_score.source_quality:.3f}")
    print(f"Uncertainty Factors: {uncertainty_score.uncertainty_factors}")

async def test_individual_assessment_methods():
    """Test individual assessment methods of the uncertainty quantifier"""
    print("\n🔬 Testing Individual Assessment Methods")
    print("=" * 60)
    
    quantifier = UncertaintyQuantifier()
    
    # Test source quality assessment
    print("\n📈 Source Quality Assessment")
    print("-" * 30)
    
    high_quality_sources = [
        {"content": "This is a comprehensive analysis with detailed explanations and multiple supporting examples that demonstrate the concept thoroughly.", "relevance": 0.9},
        {"content": "Another detailed source with substantial content and high relevance to the topic at hand.", "relevance": 0.85}
    ]
    
    low_quality_sources = [
        {"content": "Short text.", "relevance": 0.3},
        {"content": "Brief.", "relevance": 0.2}
    ]
    
    high_quality_score = quantifier._assess_source_quality(high_quality_sources)
    low_quality_score = quantifier._assess_source_quality(low_quality_sources)
    
    print(f"High quality sources score: {high_quality_score:.3f}")
    print(f"Low quality sources score: {low_quality_score:.3f}")
    
    # Test language confidence assessment
    print("\n🗣️ Language Confidence Assessment")
    print("-" * 30)
    
    confident_text = "This is definitely true and clearly established by proven research."
    uncertain_text = "This might be true, but it's unclear and possibly uncertain."
    
    confident_score = await quantifier._assess_language_confidence(confident_text)
    uncertain_score = await quantifier._assess_language_confidence(uncertain_text)
    
    print(f"Confident language score: {confident_score:.3f}")
    print(f"Uncertain language score: {uncertain_score:.3f}")
    
    # Test reasoning confidence assessment
    print("\n🧠 Reasoning Confidence Assessment")
    print("-" * 30)
    
    strong_reasoning = [
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
    
    weak_reasoning = [
        ReasoningResult(
            reasoning_type="causal",
            confidence=0.3,
            explanation="Weak reasoning",
            supporting_evidence=["Weak evidence"],
            metadata={}
        )
    ]
    
    strong_reasoning_score = quantifier._assess_reasoning_confidence(strong_reasoning)
    weak_reasoning_score = quantifier._assess_reasoning_confidence(weak_reasoning)
    no_reasoning_score = quantifier._assess_reasoning_confidence([])
    
    print(f"Strong reasoning score: {strong_reasoning_score:.3f}")
    print(f"Weak reasoning score: {weak_reasoning_score:.3f}")
    print(f"No reasoning score: {no_reasoning_score:.3f}")

async def test_confidence_calibration():
    """Test confidence score calibration across different scenarios"""
    print("\n⚖️ Testing Confidence Score Calibration")
    print("=" * 60)
    
    quantifier = UncertaintyQuantifier()
    
    test_scenarios = [
        {
            "name": "Perfect Scenario",
            "response": "This is definitely correct and clearly established.",
            "sources": [
                {"content": "Comprehensive detailed analysis with extensive supporting evidence and high relevance.", "relevance": 1.0},
                {"content": "Another thorough source with substantial content confirming the same conclusions.", "relevance": 0.95}
            ],
            "reasoning": [
                ReasoningResult(
                    reasoning_type="causal", 
                    confidence=0.95, 
                    explanation="Strong causal analysis", 
                    supporting_evidence=["Strong evidence"], 
                    metadata={}
                )
            ]
        },
        {
            "name": "Good Scenario",
            "response": "This appears to be correct based on available evidence.",
            "sources": [
                {"content": "Good analysis with supporting evidence.", "relevance": 0.8},
                {"content": "Supporting information with reasonable detail.", "relevance": 0.75}
            ],
            "reasoning": [
                ReasoningResult(
                    reasoning_type="analogical", 
                    confidence=0.7, 
                    explanation="Reasonable analogical support", 
                    supporting_evidence=["Good evidence"], 
                    metadata={}
                )
            ]
        },
        {
            "name": "Uncertain Scenario",
            "response": "This might be correct, but it's unclear and possibly uncertain.",
            "sources": [
                {"content": "Limited information available.", "relevance": 0.5},
                {"content": "Brief mention.", "relevance": 0.4}
            ],
            "reasoning": [
                ReasoningResult(
                    reasoning_type="causal", 
                    confidence=0.4, 
                    explanation="Weak reasoning", 
                    supporting_evidence=["Limited evidence"], 
                    metadata={}
                )
            ]
        },
        {
            "name": "Poor Scenario",
            "response": "This is highly speculative and uncertain.",
            "sources": [
                {"content": "Short.", "relevance": 0.2}
            ],
            "reasoning": [
                ReasoningResult(
                    reasoning_type="analogical", 
                    confidence=0.2, 
                    explanation="Very weak support", 
                    supporting_evidence=["Minimal evidence"], 
                    metadata={}
                )
            ]
        }
    ]
    
    for scenario in test_scenarios:
        uncertainty_score = await quantifier.quantify_uncertainty(
            scenario["response"],
            scenario["sources"],
            scenario["reasoning"]
        )
        
        print(f"\n{scenario['name']}:")
        print(f"  Confidence: {uncertainty_score.confidence:.3f}")
        print(f"  Reliability: {uncertainty_score.reliability_score:.3f}")
        print(f"  Source Quality: {uncertainty_score.source_quality:.3f}")
        print(f"  Uncertainty Factors: {len(uncertainty_score.uncertainty_factors)}")

async def main():
    """Run all uncertainty quantification tests"""
    try:
        await test_uncertainty_quantification()
        await test_individual_assessment_methods()
        await test_confidence_calibration()
        
        print("\n✅ All uncertainty quantification tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())