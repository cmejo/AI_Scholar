"""
Citation Generation Service for Advanced RAG Features

This service provides comprehensive citation generation capabilities including:
- Multiple citation formats (APA, MLA, Chicago, IEEE)
- Automatic bibliography generation
- Integration with RAG responses
- Citation accuracy and format compliance
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class CitationFormat(str, Enum):
    """Supported citation formats"""
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    IEEE = "ieee"
    HARVARD = "harvard"

class DocumentType(str, Enum):
    """Document types for citation"""
    BOOK = "book"
    JOURNAL_ARTICLE = "journal_article"
    WEB_PAGE = "web_page"
    PDF = "pdf"
    REPORT = "report"
    THESIS = "thesis"
    CONFERENCE_PAPER = "conference_paper"
    UNKNOWN = "unknown"

@dataclass
class CitationMetadata:
    """Metadata required for citation generation"""
    title: str
    authors: List[str] = None
    publication_date: Optional[datetime] = None
    publisher: Optional[str] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    isbn: Optional[str] = None
    document_type: DocumentType = DocumentType.UNKNOWN
    access_date: Optional[datetime] = None
    edition: Optional[str] = None
    location: Optional[str] = None
    conference: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.authors is None:
            self.authors = []
        if self.access_date is None and self.url:
            self.access_date = datetime.now()

@dataclass
class Citation:
    """A formatted citation"""
    text: str
    format: CitationFormat
    metadata: CitationMetadata
    short_form: Optional[str] = None
    
class CitationGenerator:
    """Main citation generation service"""
    
    def __init__(self):
        self.format_handlers = {
            CitationFormat.APA: self._format_apa,
            CitationFormat.MLA: self._format_mla,
            CitationFormat.CHICAGO: self._format_chicago,
            CitationFormat.IEEE: self._format_ieee,
            CitationFormat.HARVARD: self._format_harvard,
        }
    
    def generate_citation(
        self, 
        metadata: CitationMetadata, 
        format: CitationFormat = CitationFormat.APA
    ) -> Citation:
        """Generate a citation in the specified format"""
        try:
            handler = self.format_handlers.get(format)
            if not handler:
                raise ValueError(f"Unsupported citation format: {format}")
            
            citation_text = handler(metadata)
            short_form = self._generate_short_form(metadata, format)
            
            return Citation(
                text=citation_text,
                format=format,
                metadata=metadata,
                short_form=short_form
            )
        except Exception as e:
            logger.error(f"Error generating citation: {e}")
            # Fallback to basic citation
            return self._generate_fallback_citation(metadata, format)
    
    def generate_bibliography(
        self, 
        citations: List[Citation], 
        format: CitationFormat = CitationFormat.APA
    ) -> str:
        """Generate a formatted bibliography"""
        if not citations:
            return ""
        
        # Sort citations alphabetically by first author's last name
        sorted_citations = sorted(
            citations, 
            key=lambda c: self._get_sort_key(c.metadata)
        )
        
        bibliography_lines = []
        
        # Add header based on format
        header = self._get_bibliography_header(format)
        if header:
            bibliography_lines.append(header)
            bibliography_lines.append("")
        
        # Add citations
        for citation in sorted_citations:
            bibliography_lines.append(citation.text)
        
        return "\n".join(bibliography_lines)
    
    def extract_metadata_from_document(
        self, 
        document_name: str, 
        content: str = None,
        document_metadata: Dict[str, Any] = None
    ) -> CitationMetadata:
        """Extract citation metadata from document information"""
        metadata = CitationMetadata(title=document_name)
        
        # Extract from document metadata if available
        if document_metadata:
            metadata.authors = document_metadata.get('authors', [])
            metadata.publication_date = self._parse_date(
                document_metadata.get('publication_date')
            )
            metadata.publisher = document_metadata.get('publisher')
            metadata.journal = document_metadata.get('journal')
            metadata.volume = document_metadata.get('volume')
            metadata.issue = document_metadata.get('issue')
            metadata.pages = document_metadata.get('pages')
            metadata.url = document_metadata.get('url')
            metadata.doi = document_metadata.get('doi')
            metadata.isbn = document_metadata.get('isbn')
            metadata.document_type = DocumentType(
                document_metadata.get('document_type', DocumentType.UNKNOWN)
            )
        
        # Try to extract from filename and content
        if not metadata.authors:
            metadata.authors = self._extract_authors_from_content(content or "")
        
        if not metadata.publication_date:
            metadata.publication_date = self._extract_date_from_content(content or "")
        
        # Determine document type from filename
        if metadata.document_type == DocumentType.UNKNOWN:
            metadata.document_type = self._determine_document_type(document_name)
        
        # Set document type for journal articles if journal is present
        if metadata.journal and metadata.document_type == DocumentType.UNKNOWN:
            metadata.document_type = DocumentType.JOURNAL_ARTICLE
        
        return metadata
    
    def _format_apa(self, metadata: CitationMetadata) -> str:
        """Format citation in APA style"""
        parts = []
        
        # Authors
        if metadata.authors:
            author_str = self._format_authors_apa(metadata.authors)
            parts.append(author_str)
        
        # Date
        if metadata.publication_date:
            year = metadata.publication_date.year
            parts.append(f"({year})")
        else:
            parts.append("(n.d.)")
        
        # Title
        if metadata.document_type in [DocumentType.BOOK, DocumentType.REPORT]:
            parts.append(f"*{metadata.title}*")
        else:
            parts.append(metadata.title)
        
        # Journal/Publisher info
        if metadata.journal:
            journal_part = f"*{metadata.journal}*"
            if metadata.volume:
                journal_part += f", {metadata.volume}"
                if metadata.issue:
                    journal_part += f"({metadata.issue})"
            if metadata.pages:
                journal_part += f", {metadata.pages}"
            parts.append(journal_part)
        elif metadata.publisher:
            parts.append(metadata.publisher)
        
        # URL/DOI
        if metadata.doi:
            parts.append(f"https://doi.org/{metadata.doi}")
        elif metadata.url:
            parts.append(metadata.url)
        
        return ". ".join(parts) + "."
    
    def _format_mla(self, metadata: CitationMetadata) -> str:
        """Format citation in MLA style"""
        parts = []
        
        # Authors
        if metadata.authors:
            author_str = self._format_authors_mla(metadata.authors)
            parts.append(author_str)
        
        # Title
        if metadata.document_type in [DocumentType.BOOK, DocumentType.REPORT]:
            parts.append(f"*{metadata.title}*")
        else:
            parts.append(f'"{metadata.title}"')
        
        # Container (journal, website, etc.)
        if metadata.journal:
            container_part = f"*{metadata.journal}*"
            if metadata.volume:
                container_part += f", vol. {metadata.volume}"
                if metadata.issue:
                    container_part += f", no. {metadata.issue}"
            parts.append(container_part)
        
        # Publisher
        if metadata.publisher:
            parts.append(metadata.publisher)
        
        # Date
        if metadata.publication_date:
            parts.append(str(metadata.publication_date.year))
        
        # Pages
        if metadata.pages:
            parts.append(f"pp. {metadata.pages}")
        
        # Web
        if metadata.url:
            parts.append(metadata.url)
            if metadata.access_date:
                access_str = metadata.access_date.strftime("%d %b %Y")
                parts.append(f"Accessed {access_str}")
        
        return ", ".join(parts) + "."
    
    def _format_chicago(self, metadata: CitationMetadata) -> str:
        """Format citation in Chicago style"""
        parts = []
        
        # Authors
        if metadata.authors:
            author_str = self._format_authors_chicago(metadata.authors)
            parts.append(author_str)
        
        # Title
        if metadata.document_type in [DocumentType.BOOK, DocumentType.REPORT]:
            parts.append(f"*{metadata.title}*")
        else:
            parts.append(f'"{metadata.title}"')
        
        # Journal info
        if metadata.journal:
            journal_part = f"*{metadata.journal}*"
            if metadata.volume:
                journal_part += f" {metadata.volume}"
                if metadata.issue:
                    journal_part += f", no. {metadata.issue}"
            if metadata.publication_date:
                journal_part += f" ({metadata.publication_date.year})"
            if metadata.pages:
                journal_part += f": {metadata.pages}"
            parts.append(journal_part)
        else:
            # Publisher and location
            pub_parts = []
            if metadata.location:
                pub_parts.append(metadata.location)
            if metadata.publisher:
                pub_parts.append(metadata.publisher)
            if pub_parts:
                parts.append(": ".join(pub_parts))
            
            if metadata.publication_date:
                parts.append(str(metadata.publication_date.year))
        
        # URL/DOI
        if metadata.doi:
            parts.append(f"https://doi.org/{metadata.doi}")
        elif metadata.url:
            parts.append(metadata.url)
        
        return ". ".join(parts) + "."
    
    def _format_ieee(self, metadata: CitationMetadata) -> str:
        """Format citation in IEEE style"""
        parts = []
        
        # Authors
        if metadata.authors:
            author_str = self._format_authors_ieee(metadata.authors)
            parts.append(author_str)
        
        # Title
        if metadata.journal:  # Journal article
            parts.append(f'"{metadata.title},"')
        else:
            parts.append(f"*{metadata.title}*")
        
        # Journal/Conference
        if metadata.journal:
            journal_part = f"*{metadata.journal}*"
            if metadata.volume:
                journal_part += f", vol. {metadata.volume}"
                if metadata.issue:
                    journal_part += f", no. {metadata.issue}"
            if metadata.pages:
                journal_part += f", pp. {metadata.pages}"
            if metadata.publication_date:
                journal_part += f", {metadata.publication_date.year}"
            parts.append(journal_part)
        elif metadata.conference:
            conf_part = f"in *{metadata.conference}*"
            if metadata.publication_date:
                conf_part += f", {metadata.publication_date.year}"
            if metadata.pages:
                conf_part += f", pp. {metadata.pages}"
            parts.append(conf_part)
        else:
            # Book or other
            if metadata.publisher:
                parts.append(metadata.publisher)
            if metadata.publication_date:
                parts.append(str(metadata.publication_date.year))
        
        # DOI/URL
        if metadata.doi:
            parts.append(f"doi: {metadata.doi}")
        elif metadata.url:
            parts.append(f"[Online]. Available: {metadata.url}")
        
        return ", ".join(parts) + "."
    
    def _format_harvard(self, metadata: CitationMetadata) -> str:
        """Format citation in Harvard style"""
        parts = []
        
        # Authors and date
        if metadata.authors:
            author_str = self._format_authors_harvard(metadata.authors)
            if metadata.publication_date:
                parts.append(f"{author_str} ({metadata.publication_date.year})")
            else:
                parts.append(f"{author_str} (n.d.)")
        
        # Title
        if metadata.document_type in [DocumentType.BOOK, DocumentType.REPORT]:
            parts.append(f"*{metadata.title}*")
        else:
            parts.append(f"'{metadata.title}'")
        
        # Journal/Publisher
        if metadata.journal:
            journal_part = f"*{metadata.journal}*"
            if metadata.volume:
                journal_part += f", {metadata.volume}"
                if metadata.issue:
                    journal_part += f"({metadata.issue})"
            if metadata.pages:
                journal_part += f", pp. {metadata.pages}"
            parts.append(journal_part)
        elif metadata.publisher:
            parts.append(metadata.publisher)
        
        # URL
        if metadata.url:
            url_part = f"Available at: {metadata.url}"
            if metadata.access_date:
                access_str = metadata.access_date.strftime("%d %B %Y")
                url_part += f" (Accessed: {access_str})"
            parts.append(url_part)
        
        return ", ".join(parts) + "."
    
    def _format_authors_apa(self, authors: List[str]) -> str:
        """Format authors for APA style"""
        if not authors:
            return ""
        
        formatted_authors = []
        for author in authors[:7]:  # APA limits to 7 authors
            # Convert "First Last" to "Last, F."
            parts = author.strip().split()
            if len(parts) >= 2:
                last = parts[-1]
                first_initials = ". ".join([p[0] for p in parts[:-1] if p]) + "."
                formatted_authors.append(f"{last}, {first_initials}")
            else:
                formatted_authors.append(author)
        
        if len(authors) > 7:
            formatted_authors.append("... " + self._format_single_author_apa(authors[-1]))
        
        if len(formatted_authors) == 1:
            return formatted_authors[0]
        elif len(formatted_authors) == 2:
            return f"{formatted_authors[0]} & {formatted_authors[1]}"
        else:
            return ", ".join(formatted_authors[:-1]) + f", & {formatted_authors[-1]}"
    
    def _format_authors_mla(self, authors: List[str]) -> str:
        """Format authors for MLA style"""
        if not authors:
            return ""
        
        if len(authors) == 1:
            # "Last, First"
            parts = authors[0].strip().split()
            if len(parts) >= 2:
                return f"{parts[-1]}, {' '.join(parts[:-1])}"
            return authors[0]
        elif len(authors) == 2:
            first_author = self._format_single_author_mla(authors[0], first=True)
            second_author = self._format_single_author_mla(authors[1], first=False)
            return f"{first_author} and {second_author}"
        else:
            first_author = self._format_single_author_mla(authors[0], first=True)
            return f"{first_author}, et al"
    
    def _format_authors_chicago(self, authors: List[str]) -> str:
        """Format authors for Chicago style"""
        if not authors:
            return ""
        
        if len(authors) == 1:
            return authors[0]
        elif len(authors) <= 3:
            return ", ".join(authors[:-1]) + f", and {authors[-1]}"
        else:
            return f"{authors[0]}, et al"
    
    def _format_authors_ieee(self, authors: List[str]) -> str:
        """Format authors for IEEE style"""
        if not authors:
            return ""
        
        formatted_authors = []
        for author in authors:
            # Convert "First Last" to "F. Last"
            parts = author.strip().split()
            if len(parts) >= 2:
                first_initials = ". ".join([p[0] for p in parts[:-1] if p]) + "."
                last = parts[-1]
                formatted_authors.append(f"{first_initials} {last}")
            else:
                formatted_authors.append(author)
        
        if len(formatted_authors) <= 6:
            return ", ".join(formatted_authors)
        else:
            return ", ".join(formatted_authors[:6]) + ", et al."
    
    def _format_authors_harvard(self, authors: List[str]) -> str:
        """Format authors for Harvard style"""
        if not authors:
            return ""
        
        if len(authors) == 1:
            return authors[0]
        elif len(authors) == 2:
            return f"{authors[0]} and {authors[1]}"
        else:
            return f"{authors[0]} et al."
    
    def _format_single_author_mla(self, author: str, first: bool = True) -> str:
        """Format a single author for MLA"""
        parts = author.strip().split()
        if len(parts) >= 2:
            if first:
                return f"{parts[-1]}, {' '.join(parts[:-1])}"
            else:
                return ' '.join(parts)
        return author
    
    def _format_single_author_apa(self, author: str) -> str:
        """Format a single author for APA"""
        parts = author.strip().split()
        if len(parts) >= 2:
            last = parts[-1]
            first_initials = ". ".join([p[0] for p in parts[:-1] if p]) + "."
            return f"{last}, {first_initials}"
        return author
    
    def _generate_short_form(
        self, 
        metadata: CitationMetadata, 
        format: CitationFormat
    ) -> str:
        """Generate short form citation for in-text use"""
        if format == CitationFormat.APA:
            if metadata.authors:
                author = metadata.authors[0].split()[-1]  # Last name
                year = metadata.publication_date.year if metadata.publication_date else "n.d."
                return f"({author}, {year})"
            return "(Unknown, n.d.)"
        
        elif format == CitationFormat.MLA:
            if metadata.authors:
                author = metadata.authors[0].split()[-1]  # Last name
                return f"({author})"
            return "(Unknown)"
        
        elif format == CitationFormat.CHICAGO:
            if metadata.authors:
                author = metadata.authors[0].split()[-1]  # Last name
                year = metadata.publication_date.year if metadata.publication_date else "n.d."
                return f"({author} {year})"
            return "(Unknown n.d.)"
        
        elif format == CitationFormat.IEEE:
            return "[1]"  # IEEE uses numbered citations
        
        elif format == CitationFormat.HARVARD:
            if metadata.authors:
                author = metadata.authors[0].split()[-1]  # Last name
                year = metadata.publication_date.year if metadata.publication_date else "n.d."
                return f"({author} {year})"
            return "(Unknown n.d.)"
        
        return ""
    
    def _generate_fallback_citation(
        self, 
        metadata: CitationMetadata, 
        format: CitationFormat
    ) -> Citation:
        """Generate a basic fallback citation when formatting fails"""
        basic_citation = f"{metadata.title}"
        if metadata.authors:
            basic_citation = f"{', '.join(metadata.authors)}. {basic_citation}"
        if metadata.publication_date:
            basic_citation += f" ({metadata.publication_date.year})"
        
        return Citation(
            text=basic_citation,
            format=format,
            metadata=metadata,
            short_form=f"({metadata.authors[0].split()[-1] if metadata.authors else 'Unknown'})"
        )
    
    def _get_sort_key(self, metadata: CitationMetadata) -> str:
        """Get sort key for bibliography ordering"""
        if metadata.authors:
            return metadata.authors[0].split()[-1].lower()  # Last name
        return metadata.title.lower()
    
    def _get_bibliography_header(self, format: CitationFormat) -> str:
        """Get bibliography header for the format"""
        headers = {
            CitationFormat.APA: "References",
            CitationFormat.MLA: "Works Cited",
            CitationFormat.CHICAGO: "Bibliography",
            CitationFormat.IEEE: "References",
            CitationFormat.HARVARD: "References"
        }
        return headers.get(format, "References")
    
    def _parse_date(self, date_str: Union[str, datetime, None]) -> Optional[datetime]:
        """Parse date from various formats"""
        if isinstance(date_str, datetime):
            return date_str
        
        if not date_str:
            return None
        
        # Try common date formats
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y",
            "%B %Y",
            "%B %d, %Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue
        
        return None
    
    def _extract_authors_from_content(self, content: str) -> List[str]:
        """Extract authors from document content"""
        # Simple heuristic - look for "Author:" or "By:" patterns
        author_patterns = [
            r"Author[s]?:\s*([^\n]+)",
            r"By:\s*([^\n]+)",
            r"Written by:\s*([^\n]+)",
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                authors_str = match.group(1).strip()
                # Split by common separators
                authors = re.split(r'[,;&]|\sand\s', authors_str)
                return [author.strip() for author in authors if author.strip()]
        
        return []
    
    def _extract_date_from_content(self, content: str) -> Optional[datetime]:
        """Extract publication date from document content"""
        # Look for date patterns
        date_patterns = [
            r"Published:\s*([^\n]+)",
            r"Date:\s*([^\n]+)",
            r"(\d{4})",  # Just a year
            r"(\w+ \d{1,2}, \d{4})",  # Month Day, Year
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content)
            if match:
                date_str = match.group(1).strip()
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    return parsed_date
        
        return None
    
    def _determine_document_type(self, filename: str) -> DocumentType:
        """Determine document type from filename"""
        filename_lower = filename.lower()
        
        # Check for specific keywords first (more specific)
        if any(keyword in filename_lower for keyword in ['thesis', 'dissertation']):
            return DocumentType.THESIS
        elif any(keyword in filename_lower for keyword in ['journal', 'article']):
            return DocumentType.JOURNAL_ARTICLE
        elif any(keyword in filename_lower for keyword in ['conference', 'proceedings']):
            return DocumentType.CONFERENCE_PAPER
        elif any(keyword in filename_lower for keyword in ['book', 'manual']):
            return DocumentType.BOOK
        # Then check file extensions (less specific)
        elif filename_lower.endswith('.pdf'):
            return DocumentType.PDF
        elif any(ext in filename_lower for ext in ['.doc', '.docx']):
            return DocumentType.REPORT
        else:
            return DocumentType.UNKNOWN


class RAGCitationIntegrator:
    """Integrates citation generation with RAG responses"""
    
    def __init__(self, citation_generator: CitationGenerator):
        self.citation_generator = citation_generator
        self.citation_cache = {}  # Cache citations to avoid regeneration
    
    def add_citations_to_response(
        self, 
        response: str, 
        sources: List[Dict[str, Any]], 
        format: CitationFormat = CitationFormat.APA,
        style: str = "inline"  # inline, footnote, bibliography
    ) -> Dict[str, Any]:
        """Add citations to RAG response"""
        try:
            citations = []
            citation_map = {}
            
            # Generate citations for each source
            for i, source in enumerate(sources, 1):
                cache_key = f"{source.get('document', '')}-{format.value}"
                
                if cache_key in self.citation_cache:
                    citation = self.citation_cache[cache_key]
                else:
                    # Extract metadata from source
                    metadata = self.citation_generator.extract_metadata_from_document(
                        document_name=source.get('document', 'Unknown Document'),
                        content=source.get('snippet', ''),
                        document_metadata=source.get('metadata', {})
                    )
                    
                    citation = self.citation_generator.generate_citation(metadata, format)
                    self.citation_cache[cache_key] = citation
                
                citations.append(citation)
                citation_map[i] = citation
            
            # Apply citation style to response
            if style == "inline":
                enhanced_response = self._add_inline_citations(response, citation_map)
            elif style == "footnote":
                enhanced_response = self._add_footnote_citations(response, citation_map)
            else:  # bibliography
                enhanced_response = response
            
            # Generate bibliography
            bibliography = self.citation_generator.generate_bibliography(citations, format)
            
            return {
                "response": enhanced_response,
                "citations": [
                    {
                        "id": i,
                        "text": citation.text,
                        "short_form": citation.short_form,
                        "format": citation.format.value
                    }
                    for i, citation in citation_map.items()
                ],
                "bibliography": bibliography,
                "citation_format": format.value,
                "citation_style": style
            }
            
        except Exception as e:
            logger.error(f"Error adding citations to response: {e}")
            return {
                "response": response,
                "citations": [],
                "bibliography": "",
                "citation_format": format.value,
                "citation_style": style,
                "error": str(e)
            }
    
    def _add_inline_citations(
        self, 
        response: str, 
        citation_map: Dict[int, Citation]
    ) -> str:
        """Add inline citations to response"""
        # Replace [Source X] patterns with proper citations
        def replace_citation(match):
            source_num = int(match.group(1))
            if source_num in citation_map:
                citation = citation_map[source_num]
                return citation.short_form or f"[{source_num}]"
            return match.group(0)
        
        return re.sub(r'\[Source (\d+)\]', replace_citation, response)
    
    def _add_footnote_citations(
        self, 
        response: str, 
        citation_map: Dict[int, Citation]
    ) -> str:
        """Add footnote-style citations to response"""
        # Replace [Source X] with superscript numbers
        def replace_citation(match):
            source_num = int(match.group(1))
            return f"^{source_num}^"
        
        footnoted_response = re.sub(r'\[Source (\d+)\]', replace_citation, response)
        
        # Add footnotes at the end
        footnotes = []
        for num, citation in citation_map.items():
            footnotes.append(f"^{num}^ {citation.text}")
        
        if footnotes:
            footnoted_response += "\n\n---\n" + "\n".join(footnotes)
        
        return footnoted_response
    
    def clear_cache(self):
        """Clear citation cache"""
        self.citation_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get citation cache statistics"""
        return {
            "cached_citations": len(self.citation_cache),
            "cache_size_bytes": sum(
                len(str(citation.text)) for citation in self.citation_cache.values()
            )
        }