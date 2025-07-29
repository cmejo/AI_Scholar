#!/usr/bin/env python3
"""
Demonstration of the Uncertainty Quantification System
Shows how the system provides confidence scores and uncertainty indicators
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.reasoning_engine import UncertaintyQuantifier, ReasoningEngine
from models.schemas import UncertaintyScore, ReasoningResult

def format_uncertainty_indicator(confidence: float, uncertainty_factors: list) -> str:
    """Format uncertainty indicator for display"""
    if confidence >= 0.8:
        indicator = "🟢 High confidence - Well-supported information"
    elif confidence >= 0.6:
        indicator = "🟡 Medium confidence - Generally reliable with some uncertainty"
    elif confidence >= 0.4:
        indicator = "🟠 Low-medium confidence - Proceed with caution"
    else:
        indicator = "🔴 Low confidence - Highly uncertain information"
    
    if uncertainty_factors:
        factors_text = ", ".join(uncertainty_factors[:3])  # Show first 3 factors
        if len(uncertainty_factors) > 3:
            factors_text += f" (+{len(uncertainty_factors) - 3} more)"
        return f"{indicator}\nNote: {factors_text}"
    
    return indicator

async def demonstrate_uncertainty_quantification():
    """Demonstrate uncertainty quantification with various scenarios"""
    print("🧪 Uncertainty Quantification System Demonstration")
    print("=" * 60)
    
    quantifier = UncertaintyQuantifier()
    
    # Scenario 1: High confidence - Scientific fact with good sources
    print("\n📊 Scenario 1: High Confidence Scientific Fact")
    print("-" * 50)
    
    response1 = "Water boils at 100 degrees Celsius (212 degrees Fahrenheit) at standard atmospheric pressure."
    sources1 = [
        {
            "content": "Comprehensive physics textbook chapter on thermodynamics explaining the boiling point of water at standard atmospheric pressure with detailed experimental data and theoretical background.",
            "relevance": 0.95,
            "document_id": "physics_textbook"
        },
        {
            "content": "Peer-reviewed scientific paper documenting precise measurements of water's boiling point under various atmospheric conditions with extensive methodology and results.",
            "relevance": 0.92,
            "document_id": "scientific_paper"
        }
    ]
    
    reasoning1 = [
        ReasoningResult(
            reasoning_type="causal",
            confidence=0.95,
            explanation="Strong causal relationship between atmospheric pressure and boiling point",
            supporting_evidence=["Thermodynamic principles", "Experimental validation"],
            metadata={"strength": "high"}
        )
    ]
    
    uncertainty1 = await quantifier.quantify_uncertainty(response1, sources1, reasoning1)
    
    print(f"Response: {response1}")
    print(f"Confidence Score: {uncertainty1.confidence:.3f}")
    print(f"Source Quality: {uncertainty1.source_quality:.3f}")
    print(f"Reliability Score: {uncertainty1.reliability_score:.3f}")
    print(f"Uncertainty Factors: {uncertainty1.uncertainty_factors}")
    print(f"Indicator: {format_uncertainty_indicator(uncertainty1.confidence, uncertainty1.uncertainty_factors)}")
    
    # Scenario 2: Medium confidence - Complex topic with some uncertainty
    print("\n📊 Scenario 2: Medium Confidence Complex Topic")
    print("-" * 50)
    
    response2 = "Climate change appears to be contributing to more frequent extreme weather events, though the exact mechanisms are still being studied."
    sources2 = [
        {
            "content": "Research paper discussing correlations between climate change and extreme weather patterns with statistical analysis but acknowledging uncertainties in attribution.",
            "relevance": 0.8,
            "document_id": "climate_research"
        },
        {
            "content": "IPCC report section on extreme weather attribution with moderate confidence levels and discussion of ongoing research needs.",
            "relevance": 0.75,
            "document_id": "ipcc_report"
        }
    ]
    
    reasoning2 = [
        ReasoningResult(
            reasoning_type="causal",
            confidence=0.7,
            explanation="Moderate causal evidence linking climate change to extreme weather",
            supporting_evidence=["Statistical correlations", "Physical mechanisms"],
            metadata={"strength": "moderate"}
        )
    ]
    
    uncertainty2 = await quantifier.quantify_uncertainty(response2, sources2, reasoning2)
    
    print(f"Response: {response2}")
    print(f"Confidence Score: {uncertainty2.confidence:.3f}")
    print(f"Source Quality: {uncertainty2.source_quality:.3f}")
    print(f"Reliability Score: {uncertainty2.reliability_score:.3f}")
    print(f"Uncertainty Factors: {uncertainty2.uncertainty_factors}")
    print(f"Indicator: {format_uncertainty_indicator(uncertainty2.confidence, uncertainty2.uncertainty_factors)}")
    
    # Scenario 3: Low confidence - Speculative topic
    print("\n📊 Scenario 3: Low Confidence Speculative Topic")
    print("-" * 50)
    
    response3 = "It's possible that artificial general intelligence might be achieved within the next 20 years, but this is highly uncertain and depends on numerous unknown factors."
    sources3 = [
        {
            "content": "Blog post speculating about AGI timelines with personal opinions.",
            "relevance": 0.4,
            "document_id": "blog_post"
        },
        {
            "content": "Brief news article mentioning AI expert predictions with conflicting viewpoints.",
            "relevance": 0.3,
            "document_id": "news_article"
        }
    ]
    
    reasoning3 = [
        ReasoningResult(
            reasoning_type="analogical",
            confidence=0.3,
            explanation="Weak analogical reasoning based on historical technology development",
            supporting_evidence=["Historical precedents"],
            metadata={"strength": "weak"}
        )
    ]
    
    uncertainty3 = await quantifier.quantify_uncertainty(response3, sources3, reasoning3)
    
    print(f"Response: {response3}")
    print(f"Confidence Score: {uncertainty3.confidence:.3f}")
    print(f"Source Quality: {uncertainty3.source_quality:.3f}")
    print(f"Reliability Score: {uncertainty3.reliability_score:.3f}")
    print(f"Uncertainty Factors: {uncertainty3.uncertainty_factors}")
    print(f"Indicator: {format_uncertainty_indicator(uncertainty3.confidence, uncertainty3.uncertainty_factors)}")
    
    # Scenario 4: No sources - Pure speculation
    print("\n📊 Scenario 4: No Sources - Pure Speculation")
    print("-" * 50)
    
    response4 = "The stock market will probably go up tomorrow, but it's impossible to predict with certainty."
    sources4 = []
    
    uncertainty4 = await quantifier.quantify_uncertainty(response4, sources4)
    
    print(f"Response: {response4}")
    print(f"Confidence Score: {uncertainty4.confidence:.3f}")
    print(f"Source Quality: {uncertainty4.source_quality:.3f}")
    print(f"Reliability Score: {uncertainty4.reliability_score:.3f}")
    print(f"Uncertainty Factors: {uncertainty4.uncertainty_factors}")
    print(f"Indicator: {format_uncertainty_indicator(uncertainty4.confidence, uncertainty4.uncertainty_factors)}")

async def demonstrate_reasoning_engine_integration():
    """Demonstrate uncertainty quantification through reasoning engine"""
    print("\n\n🔗 Reasoning Engine Integration Demonstration")
    print("=" * 60)
    
    reasoning_engine = ReasoningEngine()
    
    # Test query that should trigger reasoning
    query = "Why does exercise improve mental health?"
    response = "Exercise improves mental health through multiple mechanisms including endorphin release, stress reduction, and improved sleep quality."
    sources = [
        {
            "content": "Comprehensive meta-analysis of exercise and mental health studies showing consistent positive effects across multiple populations and exercise types.",
            "relevance": 0.9,
            "document_id": "meta_analysis"
        },
        {
            "content": "Neuroscience research explaining the biological mechanisms by which exercise affects brain chemistry and mental well-being.",
            "relevance": 0.85,
            "document_id": "neuroscience_study"
        }
    ]
    
    # Apply reasoning first
    reasoning_results = await reasoning_engine.apply_reasoning(
        query=query,
        context=" ".join([s["content"] for s in sources]),
        reasoning_types=["causal", "analogical"]
    )
    
    # Then quantify uncertainty
    uncertainty_score = await reasoning_engine.quantify_uncertainty(
        response=response,
        sources=sources,
        reasoning_results=reasoning_results
    )
    
    print(f"Query: {query}")
    print(f"Response: {response}")
    print(f"\nReasoning Results:")
    for i, result in enumerate(reasoning_results, 1):
        print(f"  {i}. {result.reasoning_type}: confidence {result.confidence:.3f}")
        print(f"     {result.explanation[:100]}...")
    
    print(f"\nUncertainty Analysis:")
    print(f"  Overall Confidence: {uncertainty_score.confidence:.3f}")
    print(f"  Source Quality: {uncertainty_score.source_quality:.3f}")
    print(f"  Reliability Score: {uncertainty_score.reliability_score:.3f}")
    print(f"  Uncertainty Factors: {uncertainty_score.uncertainty_factors}")
    print(f"  Indicator: {format_uncertainty_indicator(uncertainty_score.confidence, uncertainty_score.uncertainty_factors)}")

async def main():
    """Run the uncertainty quantification demonstration"""
    try:
        await demonstrate_uncertainty_quantification()
        await demonstrate_reasoning_engine_integration()
        
        print("\n" + "=" * 60)
        print("✅ Uncertainty Quantification System Demonstration Complete")
        print("=" * 60)
        
        print("\n🎯 Key Features Demonstrated:")
        print("• Multi-factor confidence scoring")
        print("• Source quality assessment")
        print("• Language confidence analysis")
        print("• Reasoning integration")
        print("• Uncertainty factor identification")
        print("• Visual confidence indicators")
        print("• Calibrated confidence scores across scenarios")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demonstration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)