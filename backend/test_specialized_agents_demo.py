#!/usr/bin/env python3
"""
Demonstration script for specialized AI agents (FactChecking, Summarization, Research)
This script shows the capabilities of each agent with real examples.
"""
import asyncio
import json
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.reasoning_engine import ReasoningEngine, AgentCoordinator
from core.config import settings

async def demo_fact_checking_agent():
    """Demonstrate the FactCheckingAgent capabilities"""
    print("=" * 60)
    print("FACT-CHECKING AGENT DEMONSTRATION")
    print("=" * 60)
    
    reasoning_engine = ReasoningEngine()
    
    # Sample context with factual information
    context = """
    The Great Wall of China is approximately 13,000 miles long and was built over many centuries. 
    It was primarily constructed during the Ming Dynasty (1368-1644). The wall was built to protect 
    Chinese states from invasions by nomadic groups from the north. Contrary to popular belief, 
    the Great Wall is not visible from space with the naked eye. The wall is made primarily of 
    brick, tamped earth, wood, and stone. It took over 1 million workers to build, including 
    soldiers, peasants, and prisoners. The wall has watchtowers, garrison stations, and smoke 
    signals for communication.
    """
    
    # Test claims to verify
    claims = [
        "The Great Wall of China is 13,000 miles long",
        "The Great Wall was built during the Ming Dynasty",
        "The Great Wall is visible from space with the naked eye",
        "The Great Wall was built to protect against northern invasions",
        "The Great Wall is made entirely of stone"
    ]
    
    print("Context:", context[:200] + "...")
    print("\nClaims to verify:")
    for i, claim in enumerate(claims, 1):
        print(f"{i}. {claim}")
    
    try:
        result = await reasoning_engine.fact_check(
            query="Verify these claims about the Great Wall of China",
            context=context,
            claims=claims
        )
        
        print(f"\nFact-Checking Results:")
        print(f"Overall Confidence: {result.confidence:.2f}")
        print(f"Processing Time: {result.metadata.get('processing_time', 0):.2f}s")
        
        fact_results = result.metadata.get('fact_check_results', [])
        print(f"\nDetailed Results:")
        for i, fact_result in enumerate(fact_results, 1):
            print(f"\n{i}. Claim: {fact_result.get('claim', 'Unknown')}")
            print(f"   Status: {fact_result.get('status', 'Unknown')}")
            print(f"   Confidence: {fact_result.get('confidence', 0):.2f}")
            print(f"   Evidence: {fact_result.get('evidence', 'No evidence')}")
        
        print(f"\nSummary:")
        print(f"- Claims analyzed: {result.metadata.get('claims_analyzed', 0)}")
        print(f"- Verified claims: {result.metadata.get('verified_claims', 0)}")
        print(f"- Contradicted claims: {result.metadata.get('contradicted_claims', 0)}")
        
    except Exception as e:
        print(f"Error in fact-checking: {str(e)}")

async def demo_summarization_agent():
    """Demonstrate the SummarizationAgent capabilities"""
    print("\n" + "=" * 60)
    print("SUMMARIZATION AGENT DEMONSTRATION")
    print("=" * 60)
    
    reasoning_engine = ReasoningEngine()
    
    # Long context about artificial intelligence
    context = """
    Artificial Intelligence (AI) has undergone remarkable evolution since its inception in the 1950s. 
    The field began with simple rule-based systems and symbolic reasoning, where programmers explicitly 
    coded knowledge and decision-making rules. Early AI systems like expert systems in the 1970s and 
    1980s showed promise in specific domains like medical diagnosis and financial analysis, but they 
    were limited by their inability to learn and adapt.
    
    The 1990s and 2000s marked a significant shift toward machine learning approaches. Instead of 
    hand-coding rules, researchers developed algorithms that could learn patterns from data. This 
    period saw the rise of neural networks, support vector machines, and ensemble methods. However, 
    these approaches were still limited by the need for feature engineering and relatively shallow 
    learning capabilities.
    
    The breakthrough came with deep learning in the 2010s. Deep neural networks with multiple layers 
    could automatically learn hierarchical representations of data, eliminating much of the need for 
    manual feature engineering. This led to dramatic improvements in computer vision, natural language 
    processing, and speech recognition. Convolutional Neural Networks (CNNs) revolutionized image 
    recognition, while Recurrent Neural Networks (RNNs) and later Transformers transformed natural 
    language processing.
    
    The introduction of the Transformer architecture in 2017 marked another pivotal moment. Transformers, 
    with their attention mechanisms, enabled the development of large language models like GPT, BERT, 
    and their successors. These models demonstrated unprecedented capabilities in text generation, 
    translation, summarization, and question-answering. The scale of these models grew exponentially, 
    from millions to billions and now trillions of parameters.
    
    Today's AI systems exhibit capabilities that seemed impossible just a decade ago. They can engage 
    in human-like conversations, generate creative content, write code, solve complex mathematical 
    problems, and even assist in scientific research. However, these advances also bring challenges. 
    Issues of bias, fairness, interpretability, and safety have become paramount concerns. The energy 
    consumption of training large models raises environmental questions, while the potential for misuse 
    in generating misinformation or deepfakes poses societal risks.
    
    Looking forward, the field is exploring several promising directions. Multimodal AI systems that 
    can process text, images, audio, and video simultaneously are becoming more sophisticated. 
    Few-shot and zero-shot learning approaches aim to make AI systems more efficient and adaptable. 
    Neuromorphic computing and quantum computing may provide new computational paradigms for AI. 
    The ultimate goal for many researchers remains Artificial General Intelligence (AGI) - systems 
    that can match or exceed human cognitive abilities across all domains.
    """
    
    print("Original text length:", len(context.split()), "words")
    print("Context preview:", context[:300] + "...")
    
    # Test different summarization types
    summarization_tests = [
        {
            "type": "comprehensive",
            "max_length": 200,
            "focus_areas": [],
            "description": "Comprehensive summary (200 words)"
        },
        {
            "type": "brief",
            "max_length": 100,
            "focus_areas": [],
            "description": "Brief summary (100 words)"
        },
        {
            "type": "focused",
            "max_length": 150,
            "focus_areas": ["challenges", "future"],
            "description": "Focused on challenges and future (150 words)"
        }
    ]
    
    for test in summarization_tests:
        print(f"\n{'-' * 40}")
        print(f"Test: {test['description']}")
        print(f"{'-' * 40}")
        
        try:
            result = await reasoning_engine.summarize(
                query="Summarize the evolution and current state of AI",
                context=context,
                summary_type=test["type"],
                max_length=test["max_length"],
                focus_areas=test["focus_areas"]
            )
            
            print(f"Summary Confidence: {result.confidence:.2f}")
            print(f"Processing Time: {result.metadata.get('processing_time', 0):.2f}s")
            print(f"Generated Word Count: {result.metadata.get('word_count', 0)}")
            
            # Extract main summary from metadata
            main_summary = result.metadata.get('main_summary', 'No summary available')
            print(f"\nSummary:")
            print(main_summary)
            
            # Show key insights
            key_insights = result.metadata.get('key_insights', [])
            if key_insights:
                print(f"\nKey Insights:")
                for insight in key_insights[:3]:  # Show top 3 insights
                    print(f"• {insight}")
            
            # Show confidence metrics
            confidence_metrics = result.metadata.get('confidence_metrics', {})
            if confidence_metrics:
                print(f"\nConfidence Metrics:")
                for metric, value in confidence_metrics.items():
                    print(f"• {metric.title()}: {value:.2f}")
                    
        except Exception as e:
            print(f"Error in summarization: {str(e)}")

async def demo_research_agent():
    """Demonstrate the ResearchAgent capabilities"""
    print("\n" + "=" * 60)
    print("RESEARCH AGENT DEMONSTRATION")
    print("=" * 60)
    
    reasoning_engine = ReasoningEngine()
    
    # Context about climate change
    context = """
    Climate change refers to long-term shifts in global temperatures and weather patterns. While 
    climate variations are natural, scientific evidence shows that human activities have been the 
    primary driver of climate change since the 1800s. The burning of fossil fuels like coal, oil, 
    and gas generates greenhouse gas emissions that trap heat in Earth's atmosphere.
    
    The primary greenhouse gases include carbon dioxide (CO2), methane (CH4), nitrous oxide (N2O), 
    and fluorinated gases. CO2 concentrations have increased by over 40% since pre-industrial times, 
    primarily due to fossil fuel combustion and deforestation. Current atmospheric CO2 levels are 
    the highest in over 3 million years.
    
    The effects of climate change are already visible worldwide. Global average temperatures have 
    risen by approximately 1.1°C since the late 1800s. This warming has led to melting ice sheets 
    and glaciers, rising sea levels, more frequent extreme weather events, shifts in precipitation 
    patterns, and ecosystem disruptions. Arctic sea ice is declining at a rate of 13% per decade.
    
    Climate models project continued warming throughout the 21st century, with the magnitude depending 
    on future greenhouse gas emissions. Under high emission scenarios, global temperatures could rise 
    by 3-5°C by 2100, leading to catastrophic impacts including widespread coastal flooding, severe 
    droughts, food security threats, and mass species extinctions.
    
    Mitigation efforts focus on reducing greenhouse gas emissions through renewable energy adoption, 
    energy efficiency improvements, sustainable transportation, and carbon capture technologies. 
    Adaptation strategies involve preparing for unavoidable climate impacts through infrastructure 
    improvements, ecosystem restoration, and community resilience building.
    
    International cooperation is essential, as demonstrated by agreements like the Paris Climate 
    Accord, which aims to limit global warming to well below 2°C above pre-industrial levels. 
    However, current national commitments are insufficient to meet these targets, requiring more 
    ambitious action from governments, businesses, and individuals worldwide.
    """
    
    print("Research context length:", len(context.split()), "words")
    print("Context preview:", context[:300] + "...")
    
    # Test different research approaches
    research_tests = [
        {
            "depth": "comprehensive",
            "areas": ["background", "current_state", "implications"],
            "description": "Comprehensive analysis covering all areas"
        },
        {
            "depth": "focused",
            "areas": ["implications", "solutions"],
            "description": "Focused analysis on implications and solutions"
        },
        {
            "depth": "deep",
            "areas": ["current_state", "future_trends"],
            "description": "Deep dive into current state and future trends"
        }
    ]
    
    for test in research_tests:
        print(f"\n{'-' * 50}")
        print(f"Research Test: {test['description']}")
        print(f"{'-' * 50}")
        
        try:
            result = await reasoning_engine.research(
                query="Analyze the current state and implications of climate change",
                context=context,
                research_depth=test["depth"],
                research_areas=test["areas"]
            )
            
            print(f"Research Confidence: {result.confidence:.2f}")
            print(f"Processing Time: {result.metadata.get('processing_time', 0):.2f}s")
            print(f"Research Depth: {result.metadata.get('research_depth')}")
            print(f"Focus Areas: {', '.join(result.metadata.get('research_areas', []))}")
            
            # Show research sections
            sections = [
                ("Background Analysis", "background_analysis"),
                ("Current State", "current_state"),
                ("Key Relationships", "key_relationships"),
                ("Implications", "implications"),
                ("Knowledge Gaps", "knowledge_gaps")
            ]
            
            for section_name, section_key in sections:
                section_content = result.metadata.get(section_key, '')
                if section_content:
                    print(f"\n{section_name}:")
                    # Show first 200 characters of each section
                    preview = section_content[:200] + "..." if len(section_content) > 200 else section_content
                    print(f"  {preview}")
            
            # Show confidence metrics
            confidence_metrics = result.metadata.get('research_confidence', {})
            if confidence_metrics:
                print(f"\nResearch Confidence Metrics:")
                for metric, value in confidence_metrics.items():
                    print(f"• {metric.replace('_', ' ').title()}: {value:.2f}")
                    
        except Exception as e:
            print(f"Error in research: {str(e)}")

async def demo_agent_coordination():
    """Demonstrate coordination of multiple agents"""
    print("\n" + "=" * 60)
    print("AGENT COORDINATION DEMONSTRATION")
    print("=" * 60)
    
    coordinator = AgentCoordinator()
    
    # Context that can benefit from multiple agents
    context = """
    Recent studies have shown that regular exercise can significantly improve cognitive function 
    and memory in older adults. A 2023 study published in the Journal of Aging Research found 
    that participants who engaged in 30 minutes of moderate exercise three times per week showed 
    a 25% improvement in memory tests compared to sedentary controls. The study followed 200 
    participants aged 65-80 over 12 months.
    
    Exercise appears to increase the production of brain-derived neurotrophic factor (BDNF), 
    a protein that supports neuron growth and survival. Additionally, physical activity improves 
    blood flow to the brain and reduces inflammation. These mechanisms may help protect against 
    age-related cognitive decline and neurodegenerative diseases like Alzheimer's.
    
    However, some researchers question whether the observed benefits are due to exercise itself 
    or other factors like social interaction and improved sleep quality that often accompany 
    regular physical activity. More research is needed to establish definitive causal relationships.
    """
    
    query = "Analyze the relationship between exercise and cognitive function in older adults"
    
    print("Query:", query)
    print("Context preview:", context[:200] + "...")
    
    try:
        # Coordinate multiple agents
        results = await coordinator.coordinate_agents(
            query=query,
            context=context,
            agent_types=["fact_checking", "summarization", "research"]
        )
        
        print(f"\nCoordinated {len(results)} agents:")
        
        for i, result in enumerate(results, 1):
            print(f"\n{'-' * 30}")
            print(f"Agent {i}: {result.reasoning_type.title()}")
            print(f"{'-' * 30}")
            print(f"Confidence: {result.confidence:.2f}")
            
            if result.reasoning_type == "fact_checking":
                fact_results = result.metadata.get('fact_check_results', [])
                print(f"Claims analyzed: {len(fact_results)}")
                verified = result.metadata.get('verified_claims', 0)
                contradicted = result.metadata.get('contradicted_claims', 0)
                print(f"Verified: {verified}, Contradicted: {contradicted}")
                
            elif result.reasoning_type == "summarization":
                word_count = result.metadata.get('word_count', 0)
                print(f"Summary word count: {word_count}")
                insights = result.metadata.get('key_insights', [])
                print(f"Key insights: {len(insights)}")
                
            elif result.reasoning_type == "research":
                depth = result.metadata.get('research_depth', 'unknown')
                areas = result.metadata.get('research_areas', [])
                print(f"Research depth: {depth}")
                print(f"Research areas: {len(areas)}")
        
        # Integrate results
        print(f"\n{'=' * 40}")
        print("INTEGRATED RESULTS")
        print(f"{'=' * 40}")
        
        integration = await coordinator.integrate_results(results)
        
        print(f"Overall confidence: {integration['overall_confidence']:.2f}")
        print(f"Agents used: {', '.join(integration['reasoning_types'])}")
        print(f"Total evidence pieces: {len(integration['combined_evidence'])}")
        print(f"Key insights: {len(integration['key_insights'])}")
        
        # Show top insights
        if integration['key_insights']:
            print(f"\nTop Insights:")
            for insight in integration['key_insights'][:3]:
                print(f"• {insight}")
        
        # Show metadata summary
        print(f"\nAgent Performance Summary:")
        for agent_type, metadata in integration['metadata_summary'].items():
            print(f"• {agent_type.title()}: {metadata['confidence']:.2f} confidence, "
                  f"{metadata['processing_time']:.2f}s processing time")
                  
    except Exception as e:
        print(f"Error in agent coordination: {str(e)}")

async def main():
    """Run all demonstrations"""
    print("SPECIALIZED AI AGENTS DEMONSTRATION")
    print("This demo showcases the capabilities of FactChecking, Summarization, and Research agents")
    print("Note: This demo requires a running Ollama instance with the configured model")
    
    try:
        # Check if we can connect to Ollama
        import requests
        response = requests.get(f"{settings.OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code != 200:
            print(f"Warning: Cannot connect to Ollama at {settings.OLLAMA_URL}")
            print("Please ensure Ollama is running and the model is available")
            return
    except Exception as e:
        print(f"Warning: Cannot connect to Ollama: {str(e)}")
        print("This demo will show the structure but may not generate real responses")
    
    # Run demonstrations
    await demo_fact_checking_agent()
    await demo_summarization_agent()
    await demo_research_agent()
    await demo_agent_coordination()
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("The specialized agents are now ready for integration into the RAG system!")

if __name__ == "__main__":
    asyncio.run(main())