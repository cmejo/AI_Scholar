"""
Citation Service Demo

Demonstrates the citation generation capabilities including:
- Multiple citation formats
- Bibliography generation
- RAG integration
- Metadata extraction
"""

import asyncio
from datetime import datetime
from services.citation_service import (
    CitationGenerator, 
    RAGCitationIntegrator,
    CitationMetadata, 
    CitationFormat, 
    DocumentType
)

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_subsection(title):
    """Print a formatted subsection header"""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")

async def demo_basic_citation_generation():
    """Demo basic citation generation in different formats"""
    print_section("BASIC CITATION GENERATION")
    
    generator = CitationGenerator()
    
    # Sample metadata for a journal article
    journal_metadata = CitationMetadata(
        title="Advanced Machine Learning Techniques for Natural Language Processing",
        authors=["Dr. John Smith", "Prof. Jane Doe", "Dr. Robert Johnson"],
        publication_date=datetime(2023, 5, 15),
        journal="Journal of Artificial Intelligence Research",
        volume="45",
        issue="3",
        pages="123-145",
        doi="10.1000/182",
        document_type=DocumentType.JOURNAL_ARTICLE
    )
    
    # Generate citations in different formats
    formats = [CitationFormat.APA, CitationFormat.MLA, CitationFormat.CHICAGO, 
               CitationFormat.IEEE, CitationFormat.HARVARD]
    
    for format in formats:
        print_subsection(f"{format.value.upper()} Format")
        citation = generator.generate_citation(journal_metadata, format)
        print(f"Full Citation: {citation.text}")
        print(f"Short Form: {citation.short_form}")
    
    return generator

async def demo_different_document_types():
    """Demo citations for different document types"""
    print_section("DIFFERENT DOCUMENT TYPES")
    
    generator = CitationGenerator()
    
    # Book
    print_subsection("Book Citation")
    book_metadata = CitationMetadata(
        title="Introduction to Data Science: A Comprehensive Guide",
        authors=["Dr. Alice Johnson"],
        publication_date=datetime(2022, 8, 1),
        publisher="Tech Books Publishing",
        location="San Francisco",
        isbn="978-0123456789",
        document_type=DocumentType.BOOK
    )
    
    book_citation = generator.generate_citation(book_metadata, CitationFormat.APA)
    print(f"APA: {book_citation.text}")
    
    # Web page
    print_subsection("Web Page Citation")
    web_metadata = CitationMetadata(
        title="Understanding Neural Networks: A Beginner's Guide",
        authors=["Tech Writer"],
        url="https://example.com/neural-networks-guide",
        access_date=datetime(2023, 12, 1),
        document_type=DocumentType.WEB_PAGE
    )
    
    web_citation = generator.generate_citation(web_metadata, CitationFormat.MLA)
    print(f"MLA: {web_citation.text}")
    
    # Conference paper
    print_subsection("Conference Paper Citation")
    conf_metadata = CitationMetadata(
        title="Real-time Object Detection Using Deep Learning",
        authors=["Dr. Bob Wilson", "Dr. Carol Brown"],
        publication_date=datetime(2023, 9, 15),
        conference="International Conference on Computer Vision",
        pages="456-463",
        location="Boston, MA",
        document_type=DocumentType.CONFERENCE_PAPER
    )
    
    conf_citation = generator.generate_citation(conf_metadata, CitationFormat.IEEE)
    print(f"IEEE: {conf_citation.text}")
    
    # Thesis
    print_subsection("Thesis Citation")
    thesis_metadata = CitationMetadata(
        title="Machine Learning Applications in Healthcare: A Comprehensive Analysis",
        authors=["Graduate Student"],
        publication_date=datetime(2023, 6, 1),
        publisher="University of Technology",
        location="Boston",
        document_type=DocumentType.THESIS
    )
    
    thesis_citation = generator.generate_citation(thesis_metadata, CitationFormat.CHICAGO)
    print(f"Chicago: {thesis_citation.text}")

async def demo_bibliography_generation():
    """Demo bibliography generation"""
    print_section("BIBLIOGRAPHY GENERATION")
    
    generator = CitationGenerator()
    
    # Create multiple citations
    citations = []
    
    # Various sources
    sources_data = [
        {
            "title": "Zebra Patterns in Machine Learning",
            "authors": ["Dr. Zoe Wilson"],
            "date": datetime(2023, 1, 1),
            "journal": "Pattern Recognition Journal",
            "volume": "12"
        },
        {
            "title": "Alpha Algorithms for Data Processing",
            "authors": ["Dr. Alice Johnson", "Dr. Bob Smith"],
            "date": datetime(2022, 6, 15),
            "journal": "Computing Research",
            "volume": "8",
            "issue": "2"
        },
        {
            "title": "Beta Testing in Software Development",
            "authors": ["Prof. Carol Brown"],
            "date": datetime(2023, 3, 10),
            "publisher": "Software Press"
        }
    ]
    
    for source in sources_data:
        metadata = CitationMetadata(
            title=source["title"],
            authors=source["authors"],
            publication_date=source["date"],
            journal=source.get("journal"),
            volume=source.get("volume"),
            issue=source.get("issue"),
            publisher=source.get("publisher")
        )
        citation = generator.generate_citation(metadata, CitationFormat.APA)
        citations.append(citation)
    
    print_subsection("APA Bibliography")
    bibliography = generator.generate_bibliography(citations, CitationFormat.APA)
    print(bibliography)
    
    print_subsection("MLA Works Cited")
    mla_citations = [generator.generate_citation(c.metadata, CitationFormat.MLA) for c in citations]
    mla_bibliography = generator.generate_bibliography(mla_citations, CitationFormat.MLA)
    print(mla_bibliography)

async def demo_metadata_extraction():
    """Demo metadata extraction from document content"""
    print_section("METADATA EXTRACTION")
    
    generator = CitationGenerator()
    
    # Sample document content
    sample_content = """
    Research Paper: Advanced Neural Network Architectures
    
    Authors: Dr. John Smith, Prof. Jane Doe, Dr. Robert Johnson
    Published: March 15, 2023
    Journal: AI Research Quarterly
    Volume: 28, Issue: 2
    Pages: 45-67
    DOI: 10.1000/ai.2023.456
    
    Abstract:
    This paper presents novel approaches to neural network design...
    """
    
    print_subsection("Content-Based Extraction")
    print("Sample Content:")
    print(sample_content[:200] + "...")
    
    metadata = generator.extract_metadata_from_document(
        document_name="neural_networks_paper.pdf",
        content=sample_content
    )
    
    print(f"\nExtracted Metadata:")
    print(f"Title: {metadata.title}")
    print(f"Authors: {metadata.authors}")
    print(f"Publication Date: {metadata.publication_date}")
    print(f"Document Type: {metadata.document_type}")
    
    # Generate citation from extracted metadata
    citation = generator.generate_citation(metadata, CitationFormat.APA)
    print(f"\nGenerated Citation: {citation.text}")
    
    # Test with document metadata
    print_subsection("Metadata-Based Extraction")
    document_metadata = {
        "authors": ["Dr. Sarah Wilson", "Dr. Mike Davis"],
        "publication_date": "2023-08-20",
        "journal": "Computer Science Review",
        "volume": "15",
        "issue": "4",
        "pages": "78-92",
        "doi": "10.1000/csr.2023.789"
    }
    
    metadata2 = generator.extract_metadata_from_document(
        document_name="computer_science_review.pdf",
        document_metadata=document_metadata
    )
    
    citation2 = generator.generate_citation(metadata2, CitationFormat.APA)
    print(f"Citation from metadata: {citation2.text}")

async def demo_rag_integration():
    """Demo RAG citation integration"""
    print_section("RAG CITATION INTEGRATION")
    
    generator = CitationGenerator()
    integrator = RAGCitationIntegrator(generator)
    
    # Sample RAG response with source references
    rag_response = """
    Machine learning has revolutionized many fields [Source 1]. Deep learning, in particular, 
    has shown remarkable success in image recognition tasks [Source 2]. Recent advances in 
    transformer architectures have also improved natural language processing capabilities [Source 3].
    
    The combination of these techniques has led to significant breakthroughs in artificial 
    intelligence applications [Source 1][Source 2].
    """
    
    # Sample sources from RAG system
    sources = [
        {
            "document": "machine_learning_overview.pdf",
            "page": 1,
            "relevance": 0.95,
            "snippet": "Machine learning algorithms have transformed...",
            "metadata": {
                "authors": ["Dr. John Smith", "Dr. Jane Doe"],
                "publication_date": "2023-01-15",
                "journal": "AI Research Journal",
                "volume": "10",
                "issue": "1",
                "pages": "1-20",
                "doi": "10.1000/ai.2023.001"
            }
        },
        {
            "document": "deep_learning_handbook.pdf",
            "page": 45,
            "relevance": 0.88,
            "snippet": "Convolutional neural networks have achieved...",
            "metadata": {
                "authors": ["Dr. Alice Johnson"],
                "publication_date": "2022-08-01",
                "publisher": "Tech Books Publishing",
                "document_type": "book"
            }
        },
        {
            "document": "transformer_architectures.pdf",
            "page": 12,
            "relevance": 0.92,
            "snippet": "The attention mechanism in transformers...",
            "metadata": {
                "authors": ["Dr. Bob Wilson", "Dr. Carol Brown", "Dr. David Lee"],
                "publication_date": "2023-06-10",
                "journal": "Neural Networks Review",
                "volume": "25",
                "issue": "3",
                "pages": "234-251"
            }
        }
    ]
    
    # Test different citation styles
    styles = ["inline", "footnote", "bibliography"]
    
    for style in styles:
        print_subsection(f"{style.title()} Citation Style")
        
        result = integrator.add_citations_to_response(
            rag_response,
            sources,
            CitationFormat.APA,
            style
        )
        
        print("Enhanced Response:")
        print(result["response"][:300] + "..." if len(result["response"]) > 300 else result["response"])
        
        print(f"\nCitations ({len(result['citations'])}):")
        for i, citation in enumerate(result["citations"], 1):
            print(f"{i}. {citation['text']}")
        
        if result["bibliography"]:
            print(f"\nBibliography:")
            print(result["bibliography"])
        
        print()

async def demo_citation_formats_comparison():
    """Demo comparison of citation formats for the same source"""
    print_section("CITATION FORMATS COMPARISON")
    
    generator = CitationGenerator()
    
    # Sample metadata
    metadata = CitationMetadata(
        title="Artificial Intelligence: A Modern Approach",
        authors=["Stuart Russell", "Peter Norvig"],
        publication_date=datetime(2020, 4, 28),
        publisher="Pearson",
        location="Boston",
        edition="4th",
        isbn="978-0134610993",
        document_type=DocumentType.BOOK
    )
    
    formats = [CitationFormat.APA, CitationFormat.MLA, CitationFormat.CHICAGO, 
               CitationFormat.IEEE, CitationFormat.HARVARD]
    
    print("Same source cited in different formats:")
    print(f"Source: {metadata.title} by {', '.join(metadata.authors)}")
    print()
    
    for format in formats:
        citation = generator.generate_citation(metadata, format)
        print(f"{format.value.upper():8}: {citation.text}")
        print(f"{'':8}  Short: {citation.short_form}")
        print()

async def demo_error_handling():
    """Demo error handling and fallback citations"""
    print_section("ERROR HANDLING & FALLBACK CITATIONS")
    
    generator = CitationGenerator()
    
    print_subsection("Minimal Metadata")
    minimal_metadata = CitationMetadata(title="Unknown Document")
    citation = generator.generate_citation(minimal_metadata, CitationFormat.APA)
    print(f"Minimal citation: {citation.text}")
    print(f"Short form: {citation.short_form}")
    
    print_subsection("Invalid Date Handling")
    invalid_date_metadata = CitationMetadata(
        title="Document with Invalid Date",
        authors=["Test Author"]
    )
    # Test with invalid date in document metadata
    extracted = generator.extract_metadata_from_document(
        "test.pdf",
        document_metadata={"publication_date": "invalid-date"}
    )
    citation = generator.generate_citation(extracted, CitationFormat.APA)
    print(f"Invalid date citation: {citation.text}")
    
    print_subsection("Cache Statistics")
    integrator = RAGCitationIntegrator(generator)
    
    # Add some citations to cache
    sample_sources = [
        {"document": "test1.pdf", "metadata": {"authors": ["Author 1"]}},
        {"document": "test2.pdf", "metadata": {"authors": ["Author 2"]}}
    ]
    
    integrator.add_citations_to_response(
        "Test response [Source 1][Source 2]",
        sample_sources,
        CitationFormat.APA
    )
    
    stats = integrator.get_cache_stats()
    print(f"Cache statistics: {stats}")
    
    integrator.clear_cache()
    stats_after_clear = integrator.get_cache_stats()
    print(f"After clearing cache: {stats_after_clear}")

async def main():
    """Run all citation service demos"""
    print("CITATION SERVICE DEMONSTRATION")
    print("=" * 60)
    print("This demo showcases the comprehensive citation generation capabilities")
    print("including multiple formats, bibliography generation, and RAG integration.")
    
    try:
        await demo_basic_citation_generation()
        await demo_different_document_types()
        await demo_bibliography_generation()
        await demo_metadata_extraction()
        await demo_rag_integration()
        await demo_citation_formats_comparison()
        await demo_error_handling()
        
        print_section("DEMO COMPLETED SUCCESSFULLY")
        print("All citation generation features have been demonstrated.")
        print("The service supports:")
        print("✓ Multiple citation formats (APA, MLA, Chicago, IEEE, Harvard)")
        print("✓ Various document types (books, articles, web pages, etc.)")
        print("✓ Automatic bibliography generation")
        print("✓ Metadata extraction from content and document info")
        print("✓ RAG response integration with inline, footnote, and bibliography styles")
        print("✓ Caching for performance optimization")
        print("✓ Error handling and fallback citations")
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())