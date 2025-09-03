"""
Core Citation Formatting Engine

This module provides a robust citation formatting engine with support for multiple
citation styles (APA, MLA, Chicago) and output formats. It includes citation style
parsers, formatters, and comprehensive validation.
"""
import re
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from models.zotero_models import ZoteroItem
from core.logging_config import get_logger

logger = get_logger(__name__)


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
    """Structured citation data extracted from ZoteroItem"""
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


class CitationValidationError(Exception):
    """Exception raised for citation validation errors"""
    pass


class CitationFormattingError(Exception):
    """Exception raised for citation formatting errors"""
    pass


class CitationStyleParser:
    """Parser for extracting and validating citation data"""
    
    def __init__(self):
        self.required_fields_by_type = {
            'article': ['title', 'authors', 'publication_title', 'publication_year'],
            'book': ['title', 'authors', 'publisher', 'publication_year'],
            'chapter': ['title', 'authors', 'publication_title', 'publisher', 'publication_year'],
            'thesis': ['title', 'authors', 'publisher', 'publication_year'],
            'report': ['title', 'authors', 'publisher', 'publication_year'],
            'webpage': ['title', 'url'],
            'conference': ['title', 'authors', 'publication_title', 'publication_year'],
            'patent': ['title', 'authors', 'publication_year'],
            'software': ['title', 'authors'],
            'dataset': ['title', 'authors', 'publication_year']
        }
    
    def parse_zotero_item(self, item: ZoteroItem) -> CitationData:
        """Parse ZoteroItem into structured CitationData"""
        try:
            citation_data = CitationData(
                title=self._clean_text(item.title),
                authors=self._parse_creators(item.creators or []),
                publication_title=self._clean_text(item.publication_title),
                publication_year=item.publication_year,
                publisher=self._clean_text(item.publisher),
                volume=self._clean_text(getattr(item, 'volume', None)),
                issue=self._clean_text(getattr(item, 'issue', None)),
                pages=self._clean_text(getattr(item, 'pages', None)),
                doi=self._clean_text(item.doi),
                url=self._clean_text(item.url),
                isbn=self._clean_text(getattr(item, 'isbn', None)),
                item_type=item.item_type,
                access_date=datetime.now() if item.url else None
            )
            
            return citation_data
            
        except Exception as e:
            logger.error(f"Failed to parse Zotero item {item.id}: {str(e)}")
            raise CitationFormattingError(f"Failed to parse citation data: {str(e)}")
    
    def validate_citation_data(self, data: CitationData) -> Dict[str, Any]:
        """Validate citation data and return validation results"""
        validation_result = {
            'is_valid': True,
            'missing_fields': [],
            'warnings': [],
            'item_type': data.item_type
        }
        
        # Get required fields for item type
        required_fields = self.required_fields_by_type.get(data.item_type, ['title', 'authors'])
        
        # Check required fields
        for field in required_fields:
            if not self._has_valid_field_value(data, field):
                validation_result['missing_fields'].append(field)
                validation_result['is_valid'] = False
        
        # Check for warnings
        self._add_validation_warnings(data, validation_result)
        
        return validation_result
    
    def _parse_creators(self, creators: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Parse creator information"""
        parsed_creators = []
        
        for creator in creators:
            if not isinstance(creator, dict):
                continue
                
            creator_type = creator.get('creator_type', 'author')
            
            # Handle organizational authors
            if creator.get('name'):
                parsed_creators.append({
                    'type': creator_type,
                    'name': creator['name'],
                    'is_organization': True
                })
            else:
                # Handle individual authors
                first_name = creator.get('first_name', '').strip()
                last_name = creator.get('last_name', '').strip()
                
                if last_name or first_name:
                    parsed_creators.append({
                        'type': creator_type,
                        'first_name': first_name,
                        'last_name': last_name,
                        'is_organization': False
                    })
        
        return parsed_creators
    
    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """Clean and normalize text"""
        if not text:
            return None
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove HTML tags if present
        text = re.sub(r'<[^>]+>', '', text)
        
        return text if text else None
    
    def _has_valid_field_value(self, data: CitationData, field: str) -> bool:
        """Check if field has a valid value"""
        value = getattr(data, field, None)
        
        if value is None:
            return False
        
        if isinstance(value, str):
            return bool(value.strip())
        elif isinstance(value, list):
            return len(value) > 0
        else:
            return bool(value)
    
    def _add_validation_warnings(self, data: CitationData, validation_result: Dict[str, Any]):
        """Add validation warnings"""
        # Check for suspicious publication years
        if data.publication_year:
            current_year = datetime.now().year
            if data.publication_year < 1000 or data.publication_year > current_year + 5:
                validation_result['warnings'].append(
                    f'Publication year {data.publication_year} seems invalid'
                )
        
        # Check for authors without names
        if data.authors:
            for author in data.authors:
                if not author.get('is_organization', False):
                    if not author.get('last_name') and not author.get('first_name'):
                        validation_result['warnings'].append('Author missing name information')
        
        # Check for missing DOI in journal articles
        if data.item_type == 'article' and not data.doi and not data.url:
            validation_result['warnings'].append('Journal article missing DOI or URL')
        
        # Check for missing page numbers in articles
        if data.item_type == 'article' and not data.pages:
            validation_result['warnings'].append('Article missing page numbers')


class BaseCitationFormatter(ABC):
    """Abstract base class for citation formatters"""
    
    def __init__(self, style: CitationStyle):
        self.style = style
        self.parser = CitationStyleParser()
    
    @abstractmethod
    def format_citation(self, data: CitationData, output_format: OutputFormat) -> str:
        """Format a single citation"""
        pass
    
    @abstractmethod
    def format_bibliography_entry(self, data: CitationData, output_format: OutputFormat) -> str:
        """Format a bibliography entry"""
        pass
    
    def format_author_list(self, authors: List[Dict[str, str]], max_authors: Optional[int] = None) -> FormattedText:
        """Format author list according to style"""
        if not authors:
            return FormattedText("")
        
        # Filter to only authors (not editors, etc.)
        author_list = [a for a in authors if a.get('type', 'author') == 'author']
        
        if not author_list:
            return FormattedText("")
        
        # Apply max authors limit if specified
        if max_authors and len(author_list) > max_authors:
            author_list = author_list[:max_authors]
            truncated = True
        else:
            truncated = False
        
        return self._format_author_names(author_list, truncated)
    
    @abstractmethod
    def _format_author_names(self, authors: List[Dict[str, str]], truncated: bool) -> FormattedText:
        """Format author names according to style"""
        pass
    
    def format_title(self, title: str, item_type: str) -> FormattedText:
        """Format title according to style and item type"""
        if not title:
            return FormattedText("")
        
        # Determine if title should be italicized
        italic_types = ['book', 'thesis', 'report', 'software', 'dataset']
        is_italic = item_type in italic_types
        
        return FormattedText(title, is_italic=is_italic)
    
    def format_date(self, year: Optional[int], month: Optional[str] = None, day: Optional[int] = None) -> str:
        """Format date according to style"""
        if not year:
            return ""
        
        return str(year)
    
    def format_doi(self, doi: str) -> str:
        """Format DOI according to style"""
        if not doi:
            return ""
        
        # Ensure DOI starts with https://doi.org/
        if doi.startswith('10.'):
            return f"https://doi.org/{doi}"
        elif doi.startswith('doi:'):
            return f"https://doi.org/{doi[4:]}"
        elif doi.startswith('https://doi.org/'):
            return doi
        else:
            return f"https://doi.org/{doi}"


class APAFormatter(BaseCitationFormatter):
    """APA (American Psychological Association) citation formatter"""
    
    def __init__(self):
        super().__init__(CitationStyle.APA)
    
    def format_citation(self, data: CitationData, output_format: OutputFormat) -> str:
        """Format citation in APA style"""
        parts = []
        
        # Authors
        authors = self.format_author_list(data.authors)
        if authors.text:
            parts.append(authors.to_format(output_format))
        
        # Year
        if data.publication_year:
            parts.append(f"({data.publication_year})")
        
        # Title
        title = self.format_title(data.title or "", data.item_type or "")
        if title.text:
            parts.append(title.to_format(output_format))
        
        # Publication details
        pub_details = self._format_publication_details(data, output_format)
        if pub_details:
            parts.append(pub_details)
        
        # DOI or URL
        if data.doi:
            parts.append(self.format_doi(data.doi))
        elif data.url:
            parts.append(data.url)
        
        return '. '.join(filter(None, parts)) + '.'
    
    def format_bibliography_entry(self, data: CitationData, output_format: OutputFormat) -> str:
        """Format bibliography entry in APA style"""
        return self.format_citation(data, output_format)
    
    def _format_author_names(self, authors: List[Dict[str, str]], truncated: bool) -> FormattedText:
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
        
        if truncated:
            result += ", et al."
        
        return FormattedText(result)
    
    def _format_publication_details(self, data: CitationData, output_format: OutputFormat) -> str:
        """Format publication details in APA style"""
        if data.item_type == 'article':
            parts = []
            if data.publication_title:
                journal = FormattedText(data.publication_title, is_italic=True)
                parts.append(journal.to_format(output_format))
            
            # Volume and issue
            if data.volume:
                vol_text = FormattedText(data.volume, is_italic=True)
                if data.issue:
                    vol_issue = f"{vol_text.to_format(output_format)}({data.issue})"
                else:
                    vol_issue = vol_text.to_format(output_format)
                parts.append(vol_issue)
            
            # Pages
            if data.pages:
                parts.append(data.pages)
            
            return ', '.join(parts)
        
        elif data.item_type in ['book', 'thesis', 'report']:
            if data.publisher:
                return data.publisher
        
        return ""


class MLAFormatter(BaseCitationFormatter):
    """MLA (Modern Language Association) citation formatter"""
    
    def __init__(self):
        super().__init__(CitationStyle.MLA)
    
    def format_citation(self, data: CitationData, output_format: OutputFormat) -> str:
        """Format citation in MLA style"""
        parts = []
        
        # Authors
        authors = self.format_author_list(data.authors)
        if authors.text:
            parts.append(authors.to_format(output_format))
        
        # Title
        title = self._format_mla_title(data.title or "", data.item_type or "", output_format)
        if title:
            parts.append(title)
        
        # Publication details
        pub_details = self._format_publication_details(data, output_format)
        if pub_details:
            parts.append(pub_details)
        
        # Date
        if data.publication_year:
            parts.append(str(data.publication_year))
        
        # URL and access date
        if data.url:
            parts.append(f"Web. {datetime.now().strftime('%d %b %Y')}")
        
        return ', '.join(filter(None, parts)) + '.'
    
    def format_bibliography_entry(self, data: CitationData, output_format: OutputFormat) -> str:
        """Format bibliography entry in MLA style"""
        return self.format_citation(data, output_format)
    
    def _format_author_names(self, authors: List[Dict[str, str]], truncated: bool) -> FormattedText:
        """Format author names in MLA style"""
        formatted_names = []
        
        for i, author in enumerate(authors):
            if author.get('is_organization', False):
                formatted_names.append(author['name'])
            else:
                last = author.get('last_name', '')
                first = author.get('first_name', '')
                if last:
                    if i == 0:  # First author: Last, First
                        if first:
                            formatted_names.append(f"{last}, {first}")
                        else:
                            formatted_names.append(last)
                    else:  # Subsequent authors: First Last
                        if first:
                            formatted_names.append(f"{first} {last}")
                        else:
                            formatted_names.append(last)
        
        if not formatted_names:
            return FormattedText("")
        
        if len(formatted_names) == 1:
            result = formatted_names[0]
        elif len(formatted_names) == 2:
            result = f"{formatted_names[0]} and {formatted_names[1]}"
        else:
            result = f"{', '.join(formatted_names[:-1])}, and {formatted_names[-1]}"
        
        if truncated:
            result += ", et al."
        
        return FormattedText(result)
    
    def _format_mla_title(self, title: str, item_type: str, output_format: OutputFormat) -> str:
        """Format title in MLA style"""
        if not title:
            return ""
        
        if item_type in ['book', 'thesis', 'report']:
            title_formatted = FormattedText(title, is_italic=True)
            return title_formatted.to_format(output_format)
        else:
            return f'"{title}"'
    
    def _format_publication_details(self, data: CitationData, output_format: OutputFormat) -> str:
        """Format publication details in MLA style"""
        parts = []
        
        if data.publication_title:
            journal = FormattedText(data.publication_title, is_italic=True)
            parts.append(journal.to_format(output_format))
        
        if data.publisher:
            parts.append(data.publisher)
        
        return ', '.join(parts)


class ChicagoFormatter(BaseCitationFormatter):
    """Chicago Manual of Style citation formatter"""
    
    def __init__(self):
        super().__init__(CitationStyle.CHICAGO)
    
    def format_citation(self, data: CitationData, output_format: OutputFormat) -> str:
        """Format citation in Chicago author-date style"""
        parts = []
        
        # Authors
        authors = self.format_author_list(data.authors)
        if authors.text:
            parts.append(authors.to_format(output_format))
        
        # Year
        if data.publication_year:
            parts.append(str(data.publication_year))
        
        # Title
        title = self._format_chicago_title(data.title or "", data.item_type or "", output_format)
        if title:
            parts.append(title)
        
        # Publication details
        pub_details = self._format_publication_details(data, output_format)
        if pub_details:
            parts.append(pub_details)
        
        # DOI or URL
        if data.doi:
            parts.append(f"doi:{data.doi}")
        elif data.url:
            parts.append(data.url)
        
        return '. '.join(filter(None, parts)) + '.'
    
    def format_bibliography_entry(self, data: CitationData, output_format: OutputFormat) -> str:
        """Format bibliography entry in Chicago style"""
        return self.format_citation(data, output_format)
    
    def _format_author_names(self, authors: List[Dict[str, str]], truncated: bool) -> FormattedText:
        """Format author names in Chicago style (similar to APA)"""
        formatted_names = []
        
        for author in authors:
            if author.get('is_organization', False):
                formatted_names.append(author['name'])
            else:
                last = author.get('last_name', '')
                first = author.get('first_name', '')
                if last:
                    if first:
                        formatted_names.append(f"{last}, {first}")
                    else:
                        formatted_names.append(last)
        
        if not formatted_names:
            return FormattedText("")
        
        if len(formatted_names) == 1:
            result = formatted_names[0]
        elif len(formatted_names) == 2:
            result = f"{formatted_names[0]} and {formatted_names[1]}"
        else:
            result = f"{', '.join(formatted_names[:-1])}, and {formatted_names[-1]}"
        
        if truncated:
            result += ", et al."
        
        return FormattedText(result)
    
    def _format_chicago_title(self, title: str, item_type: str, output_format: OutputFormat) -> str:
        """Format title in Chicago style"""
        if not title:
            return ""
        
        if item_type in ['book', 'thesis', 'report']:
            title_formatted = FormattedText(title, is_italic=True)
            return title_formatted.to_format(output_format)
        else:
            return f'"{title}"'
    
    def _format_publication_details(self, data: CitationData, output_format: OutputFormat) -> str:
        """Format publication details in Chicago style"""
        if data.item_type == 'article':
            parts = []
            if data.publication_title:
                journal = FormattedText(data.publication_title, is_italic=True)
                parts.append(journal.to_format(output_format))
            
            # Volume and issue
            if data.volume:
                if data.issue:
                    parts.append(f"{data.volume}, no. {data.issue}")
                else:
                    parts.append(data.volume)
            
            # Pages
            if data.pages:
                parts.append(data.pages)
            
            return ', '.join(parts)
        
        elif data.item_type in ['book', 'thesis', 'report']:
            if data.publisher:
                return data.publisher
        
        return ""


class IEEEFormatter(BaseCitationFormatter):
    """IEEE citation formatter"""
    
    def __init__(self):
        super().__init__(CitationStyle.IEEE)
    
    def format_citation(self, data: CitationData, output_format: OutputFormat) -> str:
        """Format citation in IEEE style"""
        parts = []
        
        # Authors
        authors = self.format_author_list(data.authors)
        if authors.text:
            parts.append(authors.to_format(output_format))
        
        # Title
        title = self._format_ieee_title(data.title or "", data.item_type or "", output_format)
        if title:
            parts.append(title)
        
        # Publication details
        pub_details = self._format_publication_details(data, output_format)
        if pub_details:
            parts.append(pub_details)
        
        # Year
        if data.publication_year:
            parts.append(str(data.publication_year))
        
        return ', '.join(filter(None, parts)) + '.'
    
    def format_bibliography_entry(self, data: CitationData, output_format: OutputFormat) -> str:
        """Format bibliography entry in IEEE style"""
        return self.format_citation(data, output_format)
    
    def _format_author_names(self, authors: List[Dict[str, str]], truncated: bool) -> FormattedText:
        """Format author names in IEEE style"""
        formatted_names = []
        
        for author in authors:
            if author.get('is_organization', False):
                formatted_names.append(author['name'])
            else:
                last = author.get('last_name', '')
                first = author.get('first_name', '')
                if last and first:
                    formatted_names.append(f"{first[0]}. {last}")
                elif last:
                    formatted_names.append(last)
        
        if not formatted_names:
            return FormattedText("")
        
        result = ', '.join(formatted_names)
        
        if truncated:
            result += ", et al."
        
        return FormattedText(result)
    
    def _format_ieee_title(self, title: str, item_type: str, output_format: OutputFormat) -> str:
        """Format title in IEEE style"""
        if not title:
            return ""
        
        if item_type in ['book', 'thesis', 'report']:
            title_formatted = FormattedText(title, is_italic=True)
            return title_formatted.to_format(output_format)
        else:
            return f'"{title}"'
    
    def _format_publication_details(self, data: CitationData, output_format: OutputFormat) -> str:
        """Format publication details in IEEE style"""
        parts = []
        
        if data.publication_title:
            journal = FormattedText(data.publication_title, is_italic=True)
            parts.append(journal.to_format(output_format))
        
        return ', '.join(parts)


class CitationFormatterFactory:
    """Factory for creating citation formatters"""
    
    _formatters = {
        CitationStyle.APA: APAFormatter,
        CitationStyle.MLA: MLAFormatter,
        CitationStyle.CHICAGO: ChicagoFormatter,
        CitationStyle.CHICAGO_NOTE: ChicagoFormatter,  # Same as Chicago for now
        CitationStyle.IEEE: IEEEFormatter
    }
    
    @classmethod
    def create_formatter(cls, style: CitationStyle) -> BaseCitationFormatter:
        """Create a formatter for the specified style"""
        formatter_class = cls._formatters.get(style)
        if not formatter_class:
            raise CitationFormattingError(f"Unsupported citation style: {style.value}")
        
        return formatter_class()
    
    @classmethod
    def get_supported_styles(cls) -> List[CitationStyle]:
        """Get list of supported citation styles"""
        return list(cls._formatters.keys())


class CoreCitationEngine:
    """Core citation formatting engine"""
    
    def __init__(self):
        self.parser = CitationStyleParser()
        self.factory = CitationFormatterFactory()
    
    def format_citation(
        self,
        item: ZoteroItem,
        style: CitationStyle,
        output_format: OutputFormat = OutputFormat.TEXT
    ) -> str:
        """Format a single citation"""
        try:
            # Parse item data
            citation_data = self.parser.parse_zotero_item(item)
            
            # Validate data
            validation = self.parser.validate_citation_data(citation_data)
            if not validation['is_valid']:
                logger.warning(f"Citation data validation failed for item {item.id}: {validation['missing_fields']}")
            
            # Create formatter and format citation
            formatter = self.factory.create_formatter(style)
            citation = formatter.format_citation(citation_data, output_format)
            
            return citation
            
        except Exception as e:
            logger.error(f"Failed to format citation for item {item.id}: {str(e)}")
            raise CitationFormattingError(f"Citation formatting failed: {str(e)}")
    
    def format_bibliography_entry(
        self,
        item: ZoteroItem,
        style: CitationStyle,
        output_format: OutputFormat = OutputFormat.TEXT
    ) -> str:
        """Format a bibliography entry"""
        try:
            # Parse item data
            citation_data = self.parser.parse_zotero_item(item)
            
            # Create formatter and format bibliography entry
            formatter = self.factory.create_formatter(style)
            entry = formatter.format_bibliography_entry(citation_data, output_format)
            
            return entry
            
        except Exception as e:
            logger.error(f"Failed to format bibliography entry for item {item.id}: {str(e)}")
            raise CitationFormattingError(f"Bibliography formatting failed: {str(e)}")
    
    def validate_item_for_citation(self, item: ZoteroItem) -> Dict[str, Any]:
        """Validate item for citation formatting"""
        try:
            citation_data = self.parser.parse_zotero_item(item)
            return self.parser.validate_citation_data(citation_data)
        except Exception as e:
            logger.error(f"Failed to validate item {item.id}: {str(e)}")
            return {
                'is_valid': False,
                'missing_fields': [],
                'warnings': [f"Validation error: {str(e)}"],
                'item_type': item.item_type
            }
    
    def get_supported_styles(self) -> List[str]:
        """Get list of supported citation styles"""
        return [style.value for style in self.factory.get_supported_styles()]
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats"""
        return [fmt.value for fmt in OutputFormat]