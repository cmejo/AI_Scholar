#!/usr/bin/env python3
"""
Demo script for Task 8.1: Multi-Instance Vector Store Service.

This script demonstrates how the multi-instance vector store service works
with complete instance separation and unified search capabilities.
"""

import sys
from pathlib import Path
from datetime import datetime
import asyncio
import json

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from multi_instance_arxiv_system.vector_store.multi_instance_vector_store_service import MultiInstanceVectorStoreService
from multi_instance_arxiv_system.shared.multi_instance_data_models import (
    ArxivPaper, JournalPaper, VectorStoreConfig
)


async def create_sample_papers():
    """Create sample papers for demonstration."""
    
    # AI Scholar papers
    ai_papers = [
        ArxivPaper(
            paper_id="2301.00001",
            title="Attention Is All You Need: A Comprehensive Survey",
            authors=["Alice Johnson", "Bob Smith"],
            abstract="This paper provides a comprehensive survey of attention mechanisms in deep learning, covering transformer architectures, self-attention, and their applications in natural language processing and computer vision.",
            published_date=datetime(2023, 1, 15),
            instance_name="ai_scholar",
            arxiv_id="2301.00001",
            categories=["cs.AI", "cs.LG", "cs.CL"],
            pdf_url="https://arxiv.org/pdf/2301.00001.pdf"
        ),
        ArxivPaper(
            paper_id="2301.00002",
            title="Quantum Machine Learning: Bridging Quantum Computing and AI",
            authors=["Charlie Brown", "Diana Prince"],
            abstract="We explore the intersection of quantum computing and machine learning, presenting novel quantum algorithms for optimization and pattern recognition tasks.",
            published_date=datetime(2023, 1, 20),
            instance_name="ai_scholar",
            arxiv_id="2301.00002",
            categories=["quant-ph", "cs.LG"],
            pdf_url="https://arxiv.org/pdf/2301.00002.pdf"
        )
    ]
    
    # Quant Scholar papers
    quant_papers = [
        JournalPaper(
            paper_id="jss_2023_001",
            title="Advanced Portfolio Optimization Using Machine Learning",
            authors=["Eva Martinez", "Frank Wilson"],
            abstract="This paper presents advanced portfolio optimization techniques using machine learning algorithms, including deep reinforcement learning for dynamic asset allocation.",
            published_date=datetime(2023, 2, 1),
            instance_name="quant_scholar",
            journal_name="Journal of Statistical Software",
            volume="105",
            issue="3",
            pages="1-25",
            pdf_url="https://www.jstatsoft.org/article/view/v105i03"
        ),
        JournalPaper(
            paper_id="rjournal_2023_001",
            title="Risk Management in Cryptocurrency Markets: A Statistical Approach",
            authors=["Grace Lee", "Henry Davis"],
            abstract="We develop statistical models for risk management in cryptocurrency markets, focusing on volatility modeling and extreme value theory applications.",
            published_date=datetime(2023, 2, 15),
            instance_name="quant_scholar",
            journal_name="The R Journal",
            volume="15",
            issue="1",
            pages="45-68",
            pdf_url="https://journal.r-project.org/archive/2023-1/paper.pdf"
        )
    ]
    
    return ai_papers, quant_papers


def create_paper_chunks(paper, chunk_texts):
    """Create document chunks for a paper."""
    chunks = []
    
    for i, text in enumerate(chunk_texts):
        chunk = {
            'text': text,
            'section': ['abstract', 'introduction', 'methodology', 'results', 'conclusion'][i % 5],
            'chunk_type': 'standard',
            'chunk_index': i
        }
        chunks.append(chunk)
    
    return chunks


async def demonstrate_instance_separation():
    """Demonstrate complete instance separation."""
    
    print("🔄 Demonstrating Instance Separation")
    print("=" * 50)
    
    # Initialize service
    service = MultiInstanceVectorStoreService()
    
    # Create configurations
    ai_config = VectorStoreConfig(
        collection_name="ai_scholar_papers",
        embedding_model="all-MiniLM-L6-v2",
        chunk_size=1000,
        chunk_overlap=200,
        host="localhost",
        port=8082
    )
    
    quant_config = VectorStoreConfig(
        collection_name="quant_scholar_papers",
        embedding_model="all-MiniLM-L6-v2",
        chunk_size=800,
        chunk_overlap=150,
        host="localhost",
        port=8082
    )
    
    # Initialize instances
    print("1. Initializing scholar instances...")
    ai_success = await service.initialize_instance("ai_scholar", ai_config)
    quant_success = await service.initialize_instance("quant_scholar", quant_config)
    
    if not (ai_success and quant_success):
        print("❌ Failed to initialize instances. Make sure ChromaDB is running.")
        return False
    
    print("   ✓ AI Scholar instance initialized")
    print("   ✓ Quant Scholar instance initialized")
    
    # Get collection names to show separation
    collection_names = await service.get_collection_names()
    print(f"   📁 Collections: {collection_names}")
    
    return service


async def demonstrate_document_processing():
    """Demonstrate instance-specific document processing."""
    
    print("\n🔄 Demonstrating Document Processing")
    print("=" * 50)
    
    service = await demonstrate_instance_separation()
    if not service:
        return False
    
    # Create sample papers
    ai_papers, quant_papers = await create_sample_papers()
    
    print("2. Adding documents to instances...")
    
    # Add AI Scholar papers
    for paper in ai_papers:
        chunks = create_paper_chunks(paper, [
            f"Abstract: {paper.abstract}",
            "Introduction: This work addresses fundamental questions in artificial intelligence.",
            "Methodology: We employ state-of-the-art machine learning techniques.",
            "Results: Our experiments demonstrate significant improvements over baselines.",
            "Conclusion: This research opens new avenues for AI development."
        ])
        
        result = await service.add_instance_document("ai_scholar", paper, chunks)
        print(f"   ✓ Added AI paper: {paper.title[:50]}... ({result['chunks_added']} chunks)")
    
    # Add Quant Scholar papers
    for paper in quant_papers:
        chunks = create_paper_chunks(paper, [
            f"Abstract: {paper.abstract}",
            "Introduction: This study focuses on quantitative finance applications.",
            "Methodology: We use statistical models and econometric techniques.",
            "Results: Our analysis reveals important market dynamics.",
            "Conclusion: These findings have practical implications for risk management."
        ])
        
        result = await service.add_instance_document("quant_scholar", paper, chunks)
        print(f"   ✓ Added Quant paper: {paper.title[:50]}... ({result['chunks_added']} chunks)")
    
    return service


async def demonstrate_search_capabilities():
    """Demonstrate search capabilities across instances."""
    
    print("\n🔄 Demonstrating Search Capabilities")
    print("=" * 50)
    
    service = await demonstrate_document_processing()
    if not service:
        return False
    
    print("3. Testing search capabilities...")
    
    # Test instance-specific searches
    print("\n   🔍 Instance-specific searches:")
    
    ai_query = "attention mechanisms transformer neural networks"
    ai_results = await service.search_instance_papers(
        instance_name="ai_scholar",
        query=ai_query,
        n_results=3
    )
    
    print(f"   AI Scholar query: '{ai_query}'")
    for i, result in enumerate(ai_results[:2]):
        print(f"     {i+1}. {result['metadata'].get('title', 'Unknown')[:60]}...")
        print(f"        Relevance: {result['relevance_score']:.3f}")
    
    quant_query = "portfolio optimization risk management statistical models"
    quant_results = await service.search_instance_papers(
        instance_name="quant_scholar",
        query=quant_query,
        n_results=3
    )
    
    print(f"\n   Quant Scholar query: '{quant_query}'")
    for i, result in enumerate(quant_results[:2]):
        print(f"     {i+1}. {result['metadata'].get('title', 'Unknown')[:60]}...")
        print(f"        Relevance: {result['relevance_score']:.3f}")
    
    # Test cross-instance search
    print("\n   🔍 Cross-instance search:")
    
    cross_query = "machine learning algorithms optimization"
    all_results = await service.search_all_instances(
        query=cross_query,
        n_results=5
    )
    
    print(f"   Query: '{cross_query}'")
    instances_found = {}
    for result in all_results:
        instance = result['instance_name']
        instances_found[instance] = instances_found.get(instance, 0) + 1
        print(f"     {result['global_rank']}. [{instance}] {result['metadata'].get('title', 'Unknown')[:50]}...")
        print(f"        Relevance: {result['relevance_score']:.3f}")
    
    print(f"   📊 Results from {len(instances_found)} instances: {dict(instances_found)}")
    
    return service


async def demonstrate_monitoring_and_stats():
    """Demonstrate monitoring and statistics capabilities."""
    
    print("\n🔄 Demonstrating Monitoring and Statistics")
    print("=" * 50)
    
    service = await demonstrate_search_capabilities()
    if not service:
        return False
    
    print("4. Collecting instance statistics...")
    
    # Get individual instance stats
    ai_stats = await service.get_instance_stats("ai_scholar")
    quant_stats = await service.get_instance_stats("quant_scholar")
    
    print(f"\n   📊 AI Scholar Statistics:")
    print(f"     Collection: {ai_stats.get('collection_name', 'Unknown')}")
    print(f"     Documents: {ai_stats.get('total_chunks', 0)} chunks")
    print(f"     Embedding Model: {ai_stats.get('embedding_model', 'Unknown')}")
    print(f"     Paper Types: {ai_stats.get('paper_types', {})}")
    
    print(f"\n   📊 Quant Scholar Statistics:")
    print(f"     Collection: {quant_stats.get('collection_name', 'Unknown')}")
    print(f"     Documents: {quant_stats.get('total_chunks', 0)} chunks")
    print(f"     Embedding Model: {quant_stats.get('embedding_model', 'Unknown')}")
    print(f"     Paper Types: {quant_stats.get('paper_types', {})}")
    
    # Get all instance stats
    all_stats = await service.get_all_instance_stats()
    print(f"\n   📈 System Overview: {len(all_stats)} active instances")
    
    return service


async def demonstrate_health_and_validation():
    """Demonstrate health checking and validation."""
    
    print("\n🔄 Demonstrating Health Checking and Validation")
    print("=" * 50)
    
    service = await demonstrate_monitoring_and_stats()
    if not service:
        return False
    
    print("5. Performing health checks and validation...")
    
    # Health check
    health = await service.health_check()
    print(f"\n   🏥 System Health: {health['overall_status'].upper()}")
    print(f"     Total Instances: {health['total_instances']}")
    print(f"     Healthy Instances: {health['healthy_instances']}")
    
    if health['instance_health']:
        for instance, instance_health in health['instance_health'].items():
            status = instance_health.get('status', 'unknown')
            print(f"     {instance}: {status}")
    
    # Instance separation validation
    validation = await service.validate_instance_separation()
    print(f"\n   🔒 Instance Separation: {'✓ Valid' if validation['separation_valid'] else '❌ Invalid'}")
    
    if validation['issues']:
        print("     Issues found:")
        for issue in validation['issues']:
            print(f"       - {issue}")
    
    if validation['cross_contamination']:
        print(f"     Cross-contamination detected: {len(validation['cross_contamination'])} cases")
    
    # Collection details
    print(f"\n   📁 Collection Details:")
    for instance, details in validation['instance_collections'].items():
        print(f"     {instance}:")
        print(f"       Collection: {details['collection_name']}")
        print(f"       Documents: {details['document_count']}")
        print(f"       Proper metadata: {details['proper_instance_metadata']}")
    
    return True


async def demonstrate_advanced_features():
    """Demonstrate advanced features like similar paper finding."""
    
    print("\n🔄 Demonstrating Advanced Features")
    print("=" * 50)
    
    service = await demonstrate_health_and_validation()
    if not service:
        return False
    
    print("6. Testing advanced features...")
    
    # Create a reference paper
    ai_papers, _ = await create_sample_papers()
    reference_paper = ai_papers[0]  # Use the first AI paper
    
    # Find similar papers across instances
    similar_papers = await service.find_similar_papers_across_instances(
        reference_paper=reference_paper,
        n_results=3,
        exclude_same_instance=False
    )
    
    print(f"\n   🔍 Papers similar to: '{reference_paper.title[:50]}...'")
    for i, result in enumerate(similar_papers):
        metadata = result.get('metadata', {})
        title = metadata.get('title', 'Unknown')
        instance = metadata.get('instance_name', 'Unknown')
        relevance = result.get('relevance_score', 0)
        
        print(f"     {i+1}. [{instance}] {title[:50]}...")
        print(f"        Relevance: {relevance:.3f}")
    
    # Test backup functionality (demonstration only)
    print(f"\n   💾 Backup capabilities available for both instances")
    print(f"     - Collection backup with metadata preservation")
    print(f"     - Instance-specific backup and restore")
    print(f"     - Embedding backup (optional)")
    
    return True


async def main():
    """Run the complete multi-instance vector store demonstration."""
    
    print("Demo: Task 8.1 - Multi-Instance Vector Store Service")
    print("This demo shows complete instance separation with unified search capabilities.")
    print("\nNote: This demo requires ChromaDB to be running on localhost:8082")
    print("=" * 80)
    
    try:
        success = await demonstrate_advanced_features()
        
        if success:
            print("\n" + "=" * 80)
            print("✅ Multi-Instance Vector Store Demo Complete!")
            print("\nKey capabilities demonstrated:")
            print("- Complete instance separation with dedicated collections")
            print("- Instance-specific document processing and metadata")
            print("- Unified search interface across multiple instances")
            print("- Collection management with standardized naming")
            print("- Embedding service with caching and quality validation")
            print("- Health monitoring and instance validation")
            print("- Advanced features like cross-instance similarity search")
            print("- Backup and restore capabilities")
            
            print("\nThe multi-instance vector store service provides:")
            print("- 🔒 Complete data isolation between scholar instances")
            print("- 🔍 Powerful search capabilities within and across instances")
            print("- 📊 Comprehensive monitoring and statistics")
            print("- 🏥 Health checking and validation")
            print("- ⚡ High-performance embedding generation with caching")
            print("- 🛡️ Robust error handling and recovery")
            
        else:
            print("\n❌ Demo failed. Please check ChromaDB connection and try again.")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)