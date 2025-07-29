"""
Tests for Citation Service

Tests citation generation, bibliography creation, and RAG integration
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from services.citation_service import (
    CitationGenerator, 
    RAGCitationIntegrator,
    CitationMetadata, 
    Citation,
    CitationFormat, 
    DocumentType
)

class TestCitationMetadata:
    """Test CitationMetadata class"""
    
    def test_citation_metadata_creation(self):
        """Test basic metadata creation"""
        metadata = CitationMetadata(
            title="Test Document",
            authors=["John Doe", "Jane Smith"],
            publication_date=datetime(2023, 1, 15),
            publisher="Test Publisher"
        )
        
        assert metadata.title == "Test Document"
        assert len(metadata.authors) == 2
        assert metadata.publication_date.year == 2023
        assert metadata.publisher == "Test Publisher"
        assert metadata.document_type == DocumentType.UNKNOWN
    
    def test_citation_metadata_defaults(self):
        """Test metadata with defaults"""
        metadata = CitationMetadata(title="Test")
        
        assert metadata.authors == []
        assert metadata.publication_date is None
        assert metadata.document_type == DocumentType.UNKNOWN
    
    def test_citation_metadata_with_url(self):
        """Test metadata with URL sets access date"""
        metadata = CitationMetadata(
            title="Web Article",
            url="https://example.com/article"
        )
        
        assert metadata.url == "https://example.com/article"
        assert metadata.access_date is not None
        assert isinstance(metadata.access_date, datetime)

class TestCitationGenerator:
    """Test CitationGenerator class"""
    
    @pytest.fixture
    def generator(self):
        return CitationGenerator()
    
    @pytest.fixture
    def sample_metadata(self):
        return CitationMetadata(
            title="Advanced Machine Learning Techniques",
            authors=["John Smith", "Jane Doe", "Bob Johnson"],
            publication_date=datetime(2023, 5, 15),
            journal="Journal of AI Research",
            volume="45",
            issue="3",
            pages="123-145",
            doi="10.1000/182"
        )
    
    def test_apa_citation_journal_article(self, generator, sample_metadata):
        """Test APA format for journal article"""
        citation = generator.generate_citation(sample_metadata, CitationFormat.APA)
        
        assert citation.format == CitationFormat.APA
        assert "Smith, J." in citation.text
        assert "(2023)" in citation.text
        assert "Advanced Machine Learning Techniques" in citation.text
        assert "*Journal of AI Research*" in citation.text
        assert "45(3)" in citation.text
        assert "123-145" in citation.text
        assert "https://doi.org/10.1000/182" in citation.text
        assert citation.short_form == "(Smith, 2023)"
    
    def test_mla_citation_journal_article(self, generator, sample_metadata):
        """Test MLA format for journal article"""
        citation = generator.generate_citation(sample_metadata, CitationFormat.MLA)
        
        assert citation.format == CitationFormat.MLA
        assert "Smith, John" in citation.text
        assert '"Advanced Machine Learning Techniques"' in citation.text
        assert "*Journal of AI Research*" in citation.text
        assert "vol. 45" in citation.text
        assert "no. 3" in citation.text
        assert "2023" in citation.text
        assert citation.short_form == "(Smith)"
    
    def test_chicago_citation_journal_article(self, generator, sample_metadata):
        """Test Chicago format for journal article"""
        citation = generator.generate_citation(sample_metadata, CitationFormat.CHICAGO)
        
        assert citation.format == CitationFormat.CHICAGO
        assert "John Smith" in citation.text
        assert '"Advanced Machine Learning Techniques"' in citation.text
        assert "*Journal of AI Research*" in citation.text
        assert "45, no. 3" in citation.text
        assert "(2023)" in citation.text
        assert ": 123-145" in citation.text
    
    def test_ieee_citation_journal_article(self, generator, sample_metadata):
        """Test IEEE format for journal article"""
        citation = generator.generate_citation(sample_metadata, CitationFormat.IEEE)
        
        assert citation.format == CitationFormat.IEEE
        assert "J. Smith" in citation.text
        assert '"Advanced Machine Learning Techniques,"' in citation.text
        assert "*Journal of AI Research*" in citation.text
        assert "vol. 45" in citation.text
        assert "no. 3" in citation.text
        assert "pp. 123-145" in citation.text
        assert "2023" in citation.text
        assert citation.short_form == "[1]"
    
    def test_harvard_citation_journal_article(self, generator, sample_metadata):
        """Test Harvard format for journal article"""
        citation = generator.generate_citation(sample_metadata, CitationFormat.HARVARD)
        
        assert citation.format == CitationFormat.HARVARD
        assert "John Smith (2023)" in citation.text
        assert "'Advanced Machine Learning Techniques'" in citation.text
        assert "*Journal of AI Research*" in citation.text
        assert "45(3)" in citation.text
        assert "pp. 123-145" in citation.text
    
    def test_book_citation_apa(self, generator):
        """Test APA format for book"""
        metadata = CitationMetadata(
            title="Introduction to Data Science",
            authors=["Alice Johnson"],
            publication_date=datetime(2022, 8, 1),
            publisher="Tech Books Publishing",
            document_type=DocumentType.BOOK
        )
        
        citation = generator.generate_citation(metadata, CitationFormat.APA)
        
        assert "Johnson, A." in citation.text
        assert "(2022)" in citation.text
        assert "*Introduction to Data Science*" in citation.text
        assert "Tech Books Publishing" in citation.text
    
    def test_web_page_citation_mla(self, generator):
        """Test MLA format for web page"""
        metadata = CitationMetadata(
            title="Understanding Neural Networks",
            authors=["Tech Writer"],
            url="https://example.com/neural-networks",
            access_date=datetime(2023, 12, 1),
            document_type=DocumentType.WEB_PAGE
        )
        
        citation = generator.generate_citation(metadata, CitationFormat.MLA)
        
        assert "Writer, Tech" in citation.text
        assert '"Understanding Neural Networks"' in citation.text
        assert "https://example.com/neural-networks" in citation.text
        assert "Accessed 01 Dec 2023" in citation.text
    
    def test_multiple_authors_formatting(self, generator):
        """Test different author count formatting"""
        # Single author
        metadata_single = CitationMetadata(
            title="Single Author Work",
            authors=["John Doe"]
        )
        citation_single = generator.generate_citation(metadata_single, CitationFormat.APA)
        assert "Doe, J." in citation_single.text
        
        # Two authors
        metadata_two = CitationMetadata(
            title="Two Author Work",
            authors=["John Doe", "Jane Smith"]
        )
        citation_two = generator.generate_citation(metadata_two, CitationFormat.APA)
        assert "Doe, J. & Smith, J." in citation_two.text
        
        # Multiple authors
        metadata_multiple = CitationMetadata(
            title="Multiple Author Work",
            authors=["John Doe", "Jane Smith", "Bob Johnson", "Alice Brown"]
        )
        citation_multiple = generator.generate_citation(metadata_multiple, CitationFormat.APA)
        assert "Doe, J., Smith, J., Johnson, B., & Brown, A." in citation_multiple.text
    
    def test_no_date_citation(self, generator):
        """Test citation with no publication date"""
        metadata = CitationMetadata(
            title="Undated Work",
            authors=["Unknown Author"]
        )
        
        citation = generator.generate_citation(metadata, CitationFormat.APA)
        assert "(n.d.)" in citation.text
        assert citation.short_form == "(Unknown, n.d.)"
    
    def test_no_author_citation(self, generator):
        """Test citation with no author"""
        metadata = CitationMetadata(
            title="Anonymous Work",
            publication_date=datetime(2023, 1, 1)
        )
        
        citation = generator.generate_citation(metadata, CitationFormat.APA)
        assert "(2023)" in citation.text
        assert "Anonymous Work" in citation.text
    
    def test_extract_metadata_from_document(self, generator):
        """Test metadata extraction from document info"""
        document_metadata = {
            "authors": ["Dr. John Smith", "Prof. Jane Doe"],
            "publication_date": "2023-05-15",
            "publisher": "Academic Press",
            "journal": "Science Journal",
            "volume": "10",
            "issue": "2",
            "pages": "45-67",
            "doi": "10.1000/123"
        }
        
        metadata = generator.extract_metadata_from_document(
            document_name="Research Paper.pdf",
            document_metadata=document_metadata
        )
        
        assert metadata.title == "Research Paper.pdf"
        assert len(metadata.authors) == 2
        assert metadata.authors[0] == "Dr. John Smith"
        assert metadata.publication_date.year == 2023
        assert metadata.publisher == "Academic Press"
        assert metadata.journal == "Science Journal"
        assert metadata.volume == "10"
        assert metadata.doi == "10.1000/123"
    
    def test_extract_authors_from_content(self, generator):
        """Test author extraction from content"""
        content = """
        Title: Machine Learning Basics
        Author: John Smith, Jane Doe
        Published: 2023
        
        This is the content of the document...
        """
        
        authors = generator._extract_authors_from_content(content)
        assert len(authors) == 2
        assert "John Smith" in authors
        assert "Jane Doe" in authors
    
    def test_extract_date_from_content(self, generator):
        """Test date extraction from content"""
        content = """
        Research Paper
        Published: March 15, 2023
        
        Content here...
        """
        
        date = generator._extract_date_from_content(content)
        assert date is not None
        assert date.year == 2023
    
    def test_determine_document_type(self, generator):
        """Test document type determination"""
        assert generator._determine_document_type("paper.pdf") == DocumentType.PDF
        assert generator._determine_document_type("thesis.docx") == DocumentType.THESIS
        assert generator._determine_document_type("journal_article.pdf") == DocumentType.JOURNAL_ARTICLE
        assert generator._determine_document_type("conference_proceedings.pdf") == DocumentType.CONFERENCE_PAPER
        assert generator._determine_document_type("book_chapter.doc") == DocumentType.BOOK
        assert generator._determine_document_type("unknown.txt") == DocumentType.UNKNOWN
    
    def test_generate_bibliography(self, generator):
        """Test bibliography generation"""
        citations = []
        
        # Create multiple citations
        for i, (title, author) in enumerate([
            ("Zebra Research", "Zoe Wilson"),
            ("Alpha Studies", "Alice Johnson"),
            ("Beta Analysis", "Bob Smith")
        ]):
            metadata = CitationMetadata(
                title=title,
                authors=[author],
                publication_date=datetime(2023, 1, 1)
            )
            citation = generator.generate_citation(metadata, CitationFormat.APA)
            citations.append(citation)
        
        bibliography = generator.generate_bibliography(citations, CitationFormat.APA)
        
        assert "References" in bibliography
        # Should be sorted alphabetically by author last name
        lines = bibliography.split('\n')
        content_lines = [line for line in lines if line.strip() and line != "References"]
        assert "Johnson, A." in content_lines[0]  # Alice first
        assert "Smith, B." in content_lines[1]    # Bob second
        assert "Wilson, Z." in content_lines[2]   # Zoe last
    
    def test_fallback_citation(self, generator):
        """Test fallback citation generation"""
        metadata = CitationMetadata(
            title="Test Document",
            authors=["Test Author"]
        )
        
        # Mock the format handler to raise an exception
        with patch.object(generator, '_format_apa', side_effect=Exception("Format error")):
            citation = generator.generate_citation(metadata, CitationFormat.APA)
            
            assert "Test Author" in citation.text
            assert "Test Document" in citation.text
            assert citation.format == CitationFormat.APA

class TestRAGCitationIntegrator:
    """Test RAGCitationIntegrator class"""
    
    @pytest.fixture
    def generator(self):
        return CitationGenerator()
    
    @pytest.fixture
    def integrator(self, generator):
        return RAGCitationIntegrator(generator)
    
    @pytest.fixture
    def sample_sources(self):
        return [
            {
                "document": "Machine Learning Paper.pdf",
                "page": 1,
                "relevance": 0.9,
                "snippet": "Machine learning is a subset of artificial intelligence...",
                "metadata": {
                    "authors": ["John Smith", "Jane Doe"],
                    "publication_date": "2023-01-15",
                    "journal": "AI Journal",
                    "volume": "10",
                    "issue": "1",
                    "pages": "1-20"
                }
            },
            {
                "document": "Deep Learning Handbook.pdf",
                "page": 45,
                "relevance": 0.8,
                "snippet": "Deep neural networks have revolutionized...",
                "metadata": {
                    "authors": ["Alice Johnson"],
                    "publication_date": "2022-08-01",
                    "publisher": "Tech Books"
                }
            }
        ]
    
    def test_add_inline_citations(self, integrator, sample_sources):
        """Test adding inline citations to response"""
        response = "Machine learning is important [Source 1]. Deep learning has shown great results [Source 2]."
        
        result = integrator.add_citations_to_response(
            response, 
            sample_sources, 
            CitationFormat.APA, 
            "inline"
        )
        
        assert result["citation_format"] == "apa"
        assert result["citation_style"] == "inline"
        assert len(result["citations"]) == 2
        assert "(Smith, 2023)" in result["response"]
        assert "(Johnson, 2022)" in result["response"]
        assert "References" in result["bibliography"]
    
    def test_add_footnote_citations(self, integrator, sample_sources):
        """Test adding footnote citations to response"""
        response = "Machine learning is important [Source 1]. Deep learning has shown results [Source 2]."
        
        result = integrator.add_citations_to_response(
            response, 
            sample_sources, 
            CitationFormat.MLA, 
            "footnote"
        )
        
        assert result["citation_style"] == "footnote"
        assert "^1^" in result["response"]
        assert "^2^" in result["response"]
        assert "---" in result["response"]  # Footnote separator
        assert len(result["citations"]) == 2
    
    def test_bibliography_style_citations(self, integrator, sample_sources):
        """Test bibliography style citations"""
        response = "This is a response without inline citations."
        
        result = integrator.add_citations_to_response(
            response, 
            sample_sources, 
            CitationFormat.CHICAGO, 
            "bibliography"
        )
        
        assert result["citation_style"] == "bibliography"
        assert result["response"] == response  # Unchanged
        assert len(result["citations"]) == 2
        assert "Bibliography" in result["bibliography"]
    
    def test_citation_caching(self, integrator, sample_sources):
        """Test citation caching functionality"""
        response = "Test response [Source 1]."
        
        # First call
        result1 = integrator.add_citations_to_response(
            response, 
            sample_sources[:1], 
            CitationFormat.APA
        )
        
        # Second call with same source
        result2 = integrator.add_citations_to_response(
            response, 
            sample_sources[:1], 
            CitationFormat.APA
        )
        
        # Should use cached citation
        assert result1["citations"][0]["text"] == result2["citations"][0]["text"]
        
        # Check cache stats
        stats = integrator.get_cache_stats()
        assert stats["cached_citations"] > 0
        assert stats["cache_size_bytes"] > 0
    
    def test_clear_cache(self, integrator, sample_sources):
        """Test cache clearing"""
        response = "Test response [Source 1]."
        
        # Add to cache
        integrator.add_citations_to_response(
            response, 
            sample_sources[:1], 
            CitationFormat.APA
        )
        
        assert integrator.get_cache_stats()["cached_citations"] > 0
        
        # Clear cache
        integrator.clear_cache()
        assert integrator.get_cache_stats()["cached_citations"] == 0
    
    def test_error_handling(self, integrator):
        """Test error handling in citation integration"""
        # Invalid source data
        invalid_sources = [{"invalid": "data"}]
        response = "Test response [Source 1]."
        
        result = integrator.add_citations_to_response(
            response, 
            invalid_sources, 
            CitationFormat.APA
        )
        
        # Should handle gracefully
        assert "error" in result or len(result["citations"]) == 0
        assert result["response"] == response
    
    def test_different_citation_formats(self, integrator, sample_sources):
        """Test different citation formats produce different results"""
        response = "Test response [Source 1]."
        
        apa_result = integrator.add_citations_to_response(
            response, sample_sources[:1], CitationFormat.APA, "inline"
        )
        
        mla_result = integrator.add_citations_to_response(
            response, sample_sources[:1], CitationFormat.MLA, "inline"
        )
        
        # Different formats should produce different citations
        assert apa_result["citations"][0]["text"] != mla_result["citations"][0]["text"]
        assert apa_result["bibliography"] != mla_result["bibliography"]
        assert "References" in apa_result["bibliography"]
        assert "Works Cited" in mla_result["bibliography"]

class TestCitationFormats:
    """Test specific citation format edge cases"""
    
    @pytest.fixture
    def generator(self):
        return CitationGenerator()
    
    def test_apa_many_authors(self, generator):
        """Test APA format with many authors"""
        metadata = CitationMetadata(
            title="Collaborative Research",
            authors=[f"Author {i}" for i in range(1, 10)]  # 9 authors
        )
        
        citation = generator.generate_citation(metadata, CitationFormat.APA)
        assert "..." in citation.text  # Should truncate after 7 authors
    
    def test_mla_et_al(self, generator):
        """Test MLA et al. usage"""
        metadata = CitationMetadata(
            title="Multi-Author Work",
            authors=["First Author", "Second Author", "Third Author", "Fourth Author"]
        )
        
        citation = generator.generate_citation(metadata, CitationFormat.MLA)
        assert "et al" in citation.text
    
    def test_ieee_numbered_citations(self, generator):
        """Test IEEE numbered citation format"""
        metadata = CitationMetadata(
            title="Technical Paper",
            authors=["Engineer One", "Engineer Two"]
        )
        
        citation = generator.generate_citation(metadata, CitationFormat.IEEE)
        assert citation.short_form == "[1]"
    
    def test_chicago_book_vs_article(self, generator):
        """Test Chicago format differences for books vs articles"""
        book_metadata = CitationMetadata(
            title="Important Book",
            authors=["Book Author"],
            publisher="Book Publisher",
            location="New York",
            document_type=DocumentType.BOOK
        )
        
        article_metadata = CitationMetadata(
            title="Important Article",
            authors=["Article Author"],
            journal="Important Journal",
            volume="5",
            issue="2"
        )
        
        book_citation = generator.generate_citation(book_metadata, CitationFormat.CHICAGO)
        article_citation = generator.generate_citation(article_metadata, CitationFormat.CHICAGO)
        
        assert "*Important Book*" in book_citation.text
        assert '"Important Article"' in article_citation.text
        assert "New York: Book Publisher" in book_citation.text
        assert "*Important Journal*" in article_citation.text

if __name__ == "__main__":
    pytest.main([__file__])