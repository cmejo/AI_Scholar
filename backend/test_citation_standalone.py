#!/usr/bin/env python3
"""
Standalone test for citation formatter functionality
"""
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

# Standalone citation formatter implementation for testing

class CitationStyle(Enum):
    """Supported citation styles"""
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    CHICAGO_NOTE = "chicago-note"
    IEEE = "ieee"

class OutputFormat(Enum):
    """Supported output formats"""
    TEXT = "text"
    HTML = "html"
    RTF = "rtf"

@dataclass
class FormattedText:
    """Represents formatted text with styling information"""
    text: str
    is_italic: bool = False
    is_bold: bool = False
    is_underlined: bool = False
    
    def to_format(self, format_type: OutputFormat) -> str:
        """Convert to specified output format"""
        if format_type == OutputFormat.HTML:
            result = self.text
            if self.is_italic:
                result = f"<em>{result}</em>"
            if self.is_bold:
                result = f"<strong>{result}</strong>"
            if self.is_underlined:
                result = f"<u>{result}</u>"
            return result
        elif format_type == OutputFormat.RTF:
            result = self.text
            if self.is_italic:
                result = f"\\i {result}\\i0"
            if self.is_bold:
                result = f"\\b {result}\\b0"
            if self.is_underlined:
                result = f"\\ul {result}\\ul0"
            return result
        else:  # TEXT
            return self.text

@dataclass
class CitationData:
    """Structured citation data"""
    title: Optional[str] = None
    authors: List[Dict[str, str]] = None
    publication_title: Optional[str] = None
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    isbn: Optional[str] = None
    item_type: Optional[str] = None
    access_date: Optional[datetime] = None
    
    def __post_init__(self):
        if self.authors is None:
            self.authors = []

class APAFormatter:
    """APA citation formatter"""
    
    def format_citation(self, data: CitationData, output_format: OutputFormat) -> str:
        """Format citation in APA style"""
        parts = []
        
        # Authors
        authors = self._format_author_names(data.authors or [])
        if authors.text:
            parts.append(authors.to_format(output_format))
        
        # Year
        if data.publication_year:
            parts.append(f"({data.publication_year})")
        
        # Title
        if data.title:
            if data.item_type in ['book', 'thesis', 'report']:
                title = FormattedText(data.title, is_italic=True)
                parts.append(title.to_format(output_format))
            else:
                parts.append(data.title)
        
        # Publication details
        pub_details = self._format_publication_details(data, output_format)
        if pub_details:
            parts.append(pub_details)
        
        # DOI or URL
        if data.doi:
            if data.doi.startswith('10.'):
                parts.append(f"https://doi.org/{data.doi}")
            else:
                parts.append(data.doi)
        elif data.url:
            parts.append(data.url)
        
        return '. '.join(filter(None, parts)) + '.'
    
    def _format_author_names(self, authors: List[Dict[str, str]]) -> FormattedText:
        """Format author names in APA style"""
        formatted_names = []
        
        for author in authors:
            if author.get('is_organization', False):
                formatted_names.append(author['name'])
            else:
                last = author.get('last_name', '')
                first = author.get('first_name', '')
                if last:
                    if first:
                        formatted_names.append(f"{last}, {first[0]}.")
                    else:
                        formatted_names.append(last)
        
        if not formatted_names:
            return FormattedText("")
        
        if len(formatted_names) == 1:
            result = formatted_names[0]
        elif len(formatted_names) == 2:
            result = f"{formatted_names[0]} & {formatted_names[1]}"
        else:
            result = f"{', '.join(formatted_names[:-1])}, & {formatted_names[-1]}"
        
        return FormattedText(result)
    
    def _format_publication_details(self, data: CitationData, output_format: OutputFormat) -> str:
        """Format publication details in APA style"""
        if data.item_type == 'article':
            parts = []
            if data.publication_title:
                journal = FormattedText(data.publication_title, is_italic=True)
                parts.append(journal.to_format(output_format))
            
            if data.volume:
                vol_text = FormattedText(data.volume, is_italic=True)
                if data.issue:
                    vol_issue = f"{vol_text.to_format(output_format)}({data.issue})"
                else:
                    vol_issue = vol_text.to_format(output_format)
                parts.append(vol_issue)
            
            if data.pages:
                parts.append(data.pages)
            
            return ', '.join(parts)
        
        elif data.item_type in ['book', 'thesis', 'report']:
            if data.publisher:
                return data.publisher
        
        return ""

def test_apa_formatter():
    """Test APA formatter"""
    print("Testing APA formatter...")
    
    formatter = APAFormatter()
    
    # Test article citation
    citation_data = CitationData(
        title="Test Article Title",
        authors=[
            {'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False},
            {'type': 'author', 'first_name': 'Jane', 'last_name': 'Smith', 'is_organization': False}
        ],
        publication_title="Test Journal",
        publication_year=2023,
        doi="10.1000/test.doi",
        item_type="article"
    )
    
    citation = formatter.format_citation(citation_data, OutputFormat.TEXT)
    print(f"APA Citation: {citation}")
    
    # Verify key components
    assert "Doe, J. & Smith, J." in citation
    assert "(2023)" in citation
    assert "Test Article Title" in citation
    assert "Test Journal" in citation
    assert "https://doi.org/10.1000/test.doi" in citation
    assert citation.endswith('.')
    
    # Test book citation with HTML formatting
    book_data = CitationData(
        title="Test Book Title",
        authors=[
            {'type': 'author', 'first_name': 'Alice', 'last_name': 'Johnson', 'is_organization': False}
        ],
        publisher="Academic Press",
        publication_year=2022,
        item_type="book"
    )
    
    book_citation = formatter.format_citation(book_data, OutputFormat.HTML)
    print(f"APA Book Citation (HTML): {book_citation}")
    
    assert "Johnson, A." in book_citation
    assert "(2022)" in book_citation
    assert "<em>Test Book Title</em>" in book_citation
    assert "Academic Press" in book_citation
    
    print("✓ APA formatter tests passed")

def test_formatted_text():
    """Test FormattedText functionality"""
    print("Testing FormattedText...")
    
    # Test plain text
    text = FormattedText("Sample Text")
    assert text.to_format(OutputFormat.TEXT) == "Sample Text"
    assert text.to_format(OutputFormat.HTML) == "Sample Text"
    assert text.to_format(OutputFormat.RTF) == "Sample Text"
    
    # Test italic text
    text = FormattedText("Sample Text", is_italic=True)
    assert text.to_format(OutputFormat.TEXT) == "Sample Text"
    assert text.to_format(OutputFormat.HTML) == "<em>Sample Text</em>"
    assert text.to_format(OutputFormat.RTF) == "\\i Sample Text\\i0"
    
    # Test bold text
    text = FormattedText("Sample Text", is_bold=True)
    assert text.to_format(OutputFormat.HTML) == "<strong>Sample Text</strong>"
    assert text.to_format(OutputFormat.RTF) == "\\b Sample Text\\b0"
    
    # Test combined formatting
    text = FormattedText("Sample Text", is_italic=True, is_bold=True)
    assert text.to_format(OutputFormat.HTML) == "<strong><em>Sample Text</em></strong>"
    
    print("✓ FormattedText tests passed")

def test_author_formatting():
    """Test various author formatting scenarios"""
    print("Testing author formatting...")
    
    formatter = APAFormatter()
    
    # Single author
    authors = [{'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False}]
    result = formatter._format_author_names(authors)
    assert result.text == "Doe, J."
    
    # Two authors
    authors = [
        {'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False},
        {'type': 'author', 'first_name': 'Jane', 'last_name': 'Smith', 'is_organization': False}
    ]
    result = formatter._format_author_names(authors)
    assert result.text == "Doe, J. & Smith, J."
    
    # Multiple authors
    authors = [
        {'type': 'author', 'first_name': 'John', 'last_name': 'Doe', 'is_organization': False},
        {'type': 'author', 'first_name': 'Jane', 'last_name': 'Smith', 'is_organization': False},
        {'type': 'author', 'first_name': 'Bob', 'last_name': 'Johnson', 'is_organization': False}
    ]
    result = formatter._format_author_names(authors)
    assert result.text == "Doe, J., Smith, J., & Johnson, B."
    
    # Organization author
    authors = [{'type': 'author', 'name': 'World Health Organization', 'is_organization': True}]
    result = formatter._format_author_names(authors)
    assert result.text == "World Health Organization"
    
    print("✓ Author formatting tests passed")

def test_publication_details():
    """Test publication details formatting"""
    print("Testing publication details...")
    
    formatter = APAFormatter()
    
    # Article with volume and issue
    data = CitationData(
        publication_title="Test Journal",
        volume="15",
        issue="3",
        pages="123-145",
        item_type="article"
    )
    
    details = formatter._format_publication_details(data, OutputFormat.HTML)
    print(f"Publication details: {details}")
    
    assert "<em>Test Journal</em>" in details
    assert "<em>15</em>(3)" in details
    assert "123-145" in details
    
    # Book with publisher
    data = CitationData(
        publisher="Academic Press",
        item_type="book"
    )
    
    details = formatter._format_publication_details(data, OutputFormat.TEXT)
    assert details == "Academic Press"
    
    print("✓ Publication details tests passed")

def run_all_tests():
    """Run all tests"""
    print("Running Standalone Citation Formatter Tests...")
    print("=" * 60)
    
    try:
        test_formatted_text()
        test_author_formatting()
        test_publication_details()
        test_apa_formatter()
        
        print("=" * 60)
        print("✅ All tests passed successfully!")
        print("Core citation formatting functionality is working correctly.")
        
        # Show example output
        print("\n" + "=" * 60)
        print("EXAMPLE CITATIONS:")
        print("=" * 60)
        
        formatter = APAFormatter()
        
        # Journal article example
        article_data = CitationData(
            title="The Impact of Machine Learning on Academic Research",
            authors=[
                {'type': 'author', 'first_name': 'Sarah', 'last_name': 'Johnson', 'is_organization': False},
                {'type': 'author', 'first_name': 'Michael', 'last_name': 'Chen', 'is_organization': False}
            ],
            publication_title="Journal of Computer Science",
            publication_year=2023,
            volume="45",
            issue="2",
            pages="123-145",
            doi="10.1000/jcs.2023.45.123",
            item_type="article"
        )
        
        article_citation = formatter.format_citation(article_data, OutputFormat.TEXT)
        print(f"Journal Article:\n{article_citation}\n")
        
        # Book example
        book_data = CitationData(
            title="Advanced Citation Formatting: A Comprehensive Guide",
            authors=[
                {'type': 'author', 'first_name': 'Robert', 'last_name': 'Williams', 'is_organization': False}
            ],
            publisher="Academic Publishing House",
            publication_year=2022,
            item_type="book"
        )
        
        book_citation = formatter.format_citation(book_data, OutputFormat.TEXT)
        print(f"Book:\n{book_citation}\n")
        
        # Organization author example
        org_data = CitationData(
            title="Global Research Standards and Best Practices",
            authors=[
                {'type': 'author', 'name': 'International Research Council', 'is_organization': True}
            ],
            publication_title="Annual Research Review",
            publication_year=2023,
            item_type="article"
        )
        
        org_citation = formatter.format_citation(org_data, OutputFormat.TEXT)
        print(f"Organization Author:\n{org_citation}\n")
        
        # HTML formatting example
        html_citation = formatter.format_citation(book_data, OutputFormat.HTML)
        print(f"HTML Formatted Book:\n{html_citation}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)