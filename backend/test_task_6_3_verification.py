"""
Task 6.3 Verification: Citation Generation System

This script verifies the implementation of the citation generation system including:
- CitationGenerator for multiple citation formats
- Automatic bibliography generation
- Integration with RAG responses
- Citation accuracy and format compliance
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.citation_service import (
    CitationGenerator, 
    RAGCitationIntegrator,
    CitationMetadata, 
    Citation,
    CitationFormat, 
    DocumentType
)
from services.enhanced_rag_service import enhanced_rag_service

def print_test_header(test_name):
    """Print formatted test header"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")

def print_test_result(test_name, passed, details=""):
    """Print test result"""
    status = "✓ PASSED" if passed else "✗ FAILED"
    print(f"{status}: {test_name}")
    if details:
        print(f"  Details: {details}")

async def test_citation_generator_basic():
    """Test basic citation generation functionality"""
    print_test_header("Citation Generator Basic Functionality")
    
    generator = CitationGenerator()
    
    # Test metadata creation
    metadata = CitationMetadata(
        title="Advanced Machine Learning Techniques",
        authors=["Dr. John Smith", "Dr. Jane Doe"],
        publication_date=datetime(2023, 5, 15),
        journal="AI Research Journal",
        volume="10",
        issue="2",
        pages="45-67",
        doi="10.1000/ai.2023.123"
    )
    
    # Test APA citation
    apa_citation = generator.generate_citation(metadata, CitationFormat.APA)
    apa_expected_elements = ["Smith, J.", "Doe, J.", "(2023)", "Advanced Machine Learning Techniques", 
                            "*AI Research Journal*", "10(2)", "45-67", "https://doi.org/10.1000/ai.2023.123"]
    
    apa_passed = all(element in apa_citation.text for element in apa_expected_elements)
    print_test_result("APA Citation Generation", apa_passed, 
                     f"Generated: {apa_citation.text[:100]}...")
    
    # Test MLA citation
    mla_citation = generator.generate_citation(metadata, CitationFormat.MLA)
    mla_expected_elements = ["Smith, John", '"Advanced Machine Learning Techniques"', 
                            "*AI Research Journal*", "vol. 10", "no. 2", "2023"]
    
    mla_passed = all(element in mla_citation.text for element in mla_expected_elements)
    print_test_result("MLA Citation Generation", mla_passed,
                     f"Generated: {mla_citation.text[:100]}...")
    
    # Test short form generation
    short_form_passed = apa_citation.short_form == "(Smith, 2023)"
    print_test_result("Short Form Generation", short_form_passed,
                     f"Generated: {apa_citation.short_form}")
    
    return apa_passed and mla_passed and short_form_passed

async def test_multiple_citation_formats():
    """Test all supported citation formats"""
    print_test_header("Multiple Citation Formats")
    
    generator = CitationGenerator()
    
    metadata = CitationMetadata(
        title="Data Science Fundamentals",
        authors=["Alice Johnson"],
        publication_date=datetime(2022, 8, 1),
        publisher="Tech Books",
        document_type=DocumentType.BOOK
    )
    
    formats = [CitationFormat.APA, CitationFormat.MLA, CitationFormat.CHICAGO, 
               CitationFormat.IEEE, CitationFormat.HARVARD]
    
    all_passed = True
    
    for format in formats:
        citation = generator.generate_citation(metadata, format)
        
        # Basic validation - should contain title and author
        format_passed = (
            "Data Science Fundamentals" in citation.text and
            "Johnson" in citation.text and
            citation.format == format and
            len(citation.text) > 20
        )
        
        print_test_result(f"{format.value.upper()} Format", format_passed,
                         f"Length: {len(citation.text)} chars")
        
        all_passed = all_passed and format_passed
    
    return all_passed

async def test_bibliography_generation():
    """Test bibliography generation"""
    print_test_header("Bibliography Generation")
    
    generator = CitationGenerator()
    
    # Create multiple citations
    citations = []
    sources = [
        ("Zebra Research Methods", ["Dr. Zoe Wilson"], datetime(2023, 1, 1)),
        ("Alpha Data Analysis", ["Dr. Alice Brown"], datetime(2022, 6, 15)),
        ("Beta Machine Learning", ["Dr. Bob Smith", "Dr. Carol Jones"], datetime(2023, 3, 10))
    ]
    
    for title, authors, date in sources:
        metadata = CitationMetadata(title=title, authors=authors, publication_date=date)
        citation = generator.generate_citation(metadata, CitationFormat.APA)
        citations.append(citation)
    
    bibliography = generator.generate_bibliography(citations, CitationFormat.APA)
    
    # Test bibliography structure
    bib_lines = bibliography.split('\n')
    content_lines = [line for line in bib_lines if line.strip() and line != "References"]
    
    # Should be sorted alphabetically
    alphabetical_passed = (
        "Brown, A." in content_lines[0] and  # Alice first
        "Smith, B." in content_lines[1] and  # Bob second  
        "Wilson, Z." in content_lines[2]     # Zoe last
    )
    
    header_passed = "References" in bibliography
    
    print_test_result("Bibliography Header", header_passed)
    print_test_result("Alphabetical Sorting", alphabetical_passed)
    print_test_result("Bibliography Generation", header_passed and alphabetical_passed,
                     f"Generated {len(content_lines)} entries")
    
    return header_passed and alphabetical_passed

async def test_metadata_extraction():
    """Test metadata extraction from document information"""
    print_test_header("Metadata Extraction")
    
    generator = CitationGenerator()
    
    # Test extraction from document metadata
    document_metadata = {
        "authors": ["Dr. John Smith", "Dr. Jane Doe"],
        "publication_date": "2023-05-15",
        "journal": "Science Journal",
        "volume": "10",
        "issue": "2",
        "pages": "45-67",
        "doi": "10.1000/science.2023.123"
    }
    
    metadata = generator.extract_metadata_from_document(
        document_name="research_paper.pdf",
        document_metadata=document_metadata
    )
    
    metadata_passed = (
        metadata.title == "research_paper.pdf" and
        len(metadata.authors) == 2 and
        metadata.authors[0] == "Dr. John Smith" and
        metadata.publication_date.year == 2023 and
        metadata.journal == "Science Journal" and
        metadata.volume == "10"
    )
    
    print_test_result("Metadata Extraction from Dict", metadata_passed,
                     f"Extracted {len(metadata.authors)} authors, journal: {metadata.journal}")
    
    # Test extraction from content
    sample_content = """
    Research Paper: Machine Learning Applications
    Authors: Dr. Alice Johnson, Dr. Bob Wilson
    Published: March 2023
    
    This paper discusses...
    """
    
    content_metadata = generator.extract_metadata_from_document(
        document_name="ml_applications.pdf",
        content=sample_content
    )
    
    content_passed = (
        len(content_metadata.authors) >= 1 and
        any("Johnson" in author for author in content_metadata.authors)
    )
    
    print_test_result("Metadata Extraction from Content", content_passed,
                     f"Extracted authors: {content_metadata.authors}")
    
    return metadata_passed and content_passed

async def test_rag_citation_integration():
    """Test RAG citation integration"""
    print_test_header("RAG Citation Integration")
    
    generator = CitationGenerator()
    integrator = RAGCitationIntegrator(generator)
    
    # Sample RAG response
    response = """
    Machine learning has revolutionized data analysis [Source 1]. Deep learning techniques 
    have shown particular promise in image recognition [Source 2]. Recent advances in 
    natural language processing have also been significant [Source 1].
    """
    
    # Sample sources
    sources = [
        {
            "document": "ml_overview.pdf",
            "page": 1,
            "relevance": 0.95,
            "snippet": "Machine learning algorithms have transformed...",
            "metadata": {
                "authors": ["Dr. John Smith"],
                "publication_date": "2023-01-15",
                "journal": "AI Journal",
                "volume": "10"
            }
        },
        {
            "document": "deep_learning_guide.pdf", 
            "page": 45,
            "relevance": 0.88,
            "snippet": "Convolutional neural networks...",
            "metadata": {
                "authors": ["Dr. Jane Doe"],
                "publication_date": "2022-08-01",
                "publisher": "Tech Press"
            }
        }
    ]
    
    # Test inline citations
    inline_result = integrator.add_citations_to_response(
        response, sources, CitationFormat.APA, "inline"
    )
    
    inline_passed = (
        "(Smith, 2023)" in inline_result["response"] and
        "(Doe, 2022)" in inline_result["response"] and
        len(inline_result["citations"]) == 2 and
        inline_result["citation_format"] == "apa"
    )
    
    print_test_result("Inline Citation Integration", inline_passed,
                     f"Generated {len(inline_result['citations'])} citations")
    
    # Test footnote citations
    footnote_result = integrator.add_citations_to_response(
        response, sources, CitationFormat.MLA, "footnote"
    )
    
    footnote_passed = (
        "^1^" in footnote_result["response"] and
        "^2^" in footnote_result["response"] and
        "---" in footnote_result["response"]  # Footnote separator
    )
    
    print_test_result("Footnote Citation Integration", footnote_passed)
    
    # Test bibliography generation
    bib_result = integrator.add_citations_to_response(
        response, sources, CitationFormat.CHICAGO, "bibliography"
    )
    
    bib_passed = (
        "Bibliography" in bib_result["bibliography"] and
        len(bib_result["citations"]) == 2
    )
    
    print_test_result("Bibliography Citation Integration", bib_passed)
    
    return inline_passed and footnote_passed and bib_passed

async def test_citation_caching():
    """Test citation caching functionality"""
    print_test_header("Citation Caching")
    
    generator = CitationGenerator()
    integrator = RAGCitationIntegrator(generator)
    
    sources = [
        {
            "document": "test_document.pdf",
            "metadata": {"authors": ["Test Author"], "publication_date": "2023-01-01"}
        }
    ]
    
    # First call
    result1 = integrator.add_citations_to_response(
        "Test response [Source 1]", sources, CitationFormat.APA
    )
    
    # Second call with same source
    result2 = integrator.add_citations_to_response(
        "Another response [Source 1]", sources, CitationFormat.APA
    )
    
    # Should use cached citation
    cache_passed = result1["citations"][0]["text"] == result2["citations"][0]["text"]
    
    stats = integrator.get_cache_stats()
    stats_passed = stats["cached_citations"] > 0
    
    print_test_result("Citation Caching", cache_passed and stats_passed,
                     f"Cache stats: {stats}")
    
    # Test cache clearing
    integrator.clear_cache()
    cleared_stats = integrator.get_cache_stats()
    clear_passed = cleared_stats["cached_citations"] == 0
    
    print_test_result("Cache Clearing", clear_passed)
    
    return cache_passed and stats_passed and clear_passed

async def test_enhanced_rag_integration():
    """Test integration with enhanced RAG service"""
    print_test_header("Enhanced RAG Service Integration")
    
    try:
        # Test that citation components are properly initialized
        service = enhanced_rag_service
        
        init_passed = (
            hasattr(service, 'citation_generator') and
            hasattr(service, 'citation_integrator') and
            service.citation_generator is not None and
            service.citation_integrator is not None
        )
        
        print_test_result("Citation Service Initialization", init_passed)
        
        # Test citation metadata extraction method
        test_result = {
            "document": "test_paper.pdf",
            "metadata": {
                "authors": ["Test Author"],
                "publication_date": "2023-01-01",
                "journal": "Test Journal"
            }
        }
        
        citation_metadata = service._extract_citation_metadata(test_result)
        
        metadata_passed = (
            citation_metadata["title"] == "test_paper.pdf" and
            citation_metadata["authors"] == ["Test Author"] and
            citation_metadata["publication_date"] == "2023-01-01"
        )
        
        print_test_result("Citation Metadata Extraction", metadata_passed,
                         f"Extracted: {citation_metadata}")
        
        # Test document type determination
        doc_type = service._determine_document_type_from_name("journal_article.pdf")
        type_passed = doc_type == "journal_article"
        
        print_test_result("Document Type Determination", type_passed,
                         f"Determined type: {doc_type}")
        
        return init_passed and metadata_passed and type_passed
        
    except Exception as e:
        print_test_result("Enhanced RAG Integration", False, f"Error: {e}")
        return False

async def test_error_handling():
    """Test error handling in citation generation"""
    print_test_header("Error Handling")
    
    generator = CitationGenerator()
    integrator = RAGCitationIntegrator(generator)
    
    # Test with minimal metadata
    minimal_metadata = CitationMetadata(title="Test Document")
    citation = generator.generate_citation(minimal_metadata, CitationFormat.APA)
    
    minimal_passed = (
        citation.text is not None and
        len(citation.text) > 0 and
        "Test Document" in citation.text
    )
    
    print_test_result("Minimal Metadata Handling", minimal_passed,
                     f"Generated: {citation.text}")
    
    # Test with invalid sources
    invalid_sources = [{"invalid": "data"}]
    result = integrator.add_citations_to_response(
        "Test [Source 1]", invalid_sources, CitationFormat.APA
    )
    
    error_passed = (
        result["response"] == "Test [Source 1]" and  # Original response preserved
        (len(result["citations"]) == 0 or "error" in result)
    )
    
    print_test_result("Invalid Source Handling", error_passed)
    
    return minimal_passed and error_passed

async def run_all_tests():
    """Run all citation system tests"""
    print("CITATION GENERATION SYSTEM VERIFICATION")
    print("=" * 60)
    print("Testing Task 6.3: Create citation generation system")
    print("Requirements: 5.4 - Automatic citation format generation")
    
    tests = [
        ("Basic Citation Generation", test_citation_generator_basic),
        ("Multiple Citation Formats", test_multiple_citation_formats),
        ("Bibliography Generation", test_bibliography_generation),
        ("Metadata Extraction", test_metadata_extraction),
        ("RAG Citation Integration", test_rag_citation_integration),
        ("Citation Caching", test_citation_caching),
        ("Enhanced RAG Integration", test_enhanced_rag_integration),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print_test_result(test_name, False, f"Exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print_test_header("TEST SUMMARY")
    passed_tests = sum(1 for _, result in results if result)
    total_tests = len(results)
    
    for test_name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("Citation generation system is working correctly.")
        print("\nImplemented features:")
        print("✓ Multiple citation formats (APA, MLA, Chicago, IEEE, Harvard)")
        print("✓ Automatic bibliography generation")
        print("✓ RAG response integration")
        print("✓ Citation accuracy and format compliance")
        print("✓ Metadata extraction from documents")
        print("✓ Caching for performance optimization")
        print("✓ Error handling and fallback citations")
        return True
    else:
        print(f"\n❌ {total_tests - passed_tests} tests failed.")
        print("Please review the implementation.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)