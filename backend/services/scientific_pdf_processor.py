"""
Scientific PDF Processor for AI Scholar RAG System
Specialized for processing scientific journal articles and research papers
"""

import fitz  # PyMuPDF
import pdfplumber
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)

class ScientificPDFProcessor:
    """Enhanced PDF processor for scientific literature"""
    
    def __init__(self):
        self.section_patterns = {
            'title': r'^(.{1,200}?)(?:\n|$)',
            'abstract': r'(?:abstract|summary)[\s\n]*(.+?)(?=\n\s*(?:keywords|introduction|1\.|background)|$)',
            'keywords': r'(?:keywords?|key\s*words?)[\s\n]*[:\-]?\s*(.+?)(?=\n\s*(?:introduction|1\.|background)|$)',
            'introduction': r'(?:introduction|background)[\s\n]*(.+?)(?=\n\s*(?:methods?|methodology|materials?|2\.|related\s*work)|$)',
            'methods': r'(?:methods?|methodology|materials?\s*and\s*methods?)[\s\n]*(.+?)(?=\n\s*(?:results?|findings?|3\.|experiments?)|$)',
            'results': r'(?:results?|findings?)[\s\n]*(.+?)(?=\n\s*(?:discussion|conclusion|4\.|analysis)|$)',
            'discussion': r'(?:discussion|analysis)[\s\n]*(.+?)(?=\n\s*(?:conclusion|references?|5\.|acknowledgment)|$)',
            'conclusion': r'(?:conclusion|conclusions?)[\s\n]*(.+?)(?=\n\s*(?:references?|acknowledgment|bibliography)|$)',
            'references': r'(?:references?|bibliography)[\s\n]*(.+?)$'
        }
        
        # Patterns for extracting scientific entities
        self.doi_pattern = r'(?:doi:?\s*|https?://(?:dx\.)?doi\.org/)([^\s]+)'
        self.citation_pattern = r'\[(\d+(?:[-,]\d+)*)\]|\(([^)]+\d{4}[^)]*)\)'
        self.author_pattern = r'([A-Z][a-z]+(?:\s+[A-Z]\.)*(?:\s+[A-Z][a-z]+)*)'
        self.journal_pattern = r'(?:published\s+in|journal\s*:?\s*|in\s+)([A-Z][^.]+?)(?:\s*,|\s*\d{4}|\s*vol)'
        
    def extract_comprehensive_content(self, pdf_path: str) -> Dict[str, Any]:
        """Extract comprehensive structured content from scientific PDF"""
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            # Generate unique document ID
            doc_id = self._generate_document_id(pdf_path)
            
            # Extract content using both PyMuPDF and pdfplumber
            pymupdf_content = self._extract_with_pymupdf(pdf_path)
            pdfplumber_content = self._extract_with_pdfplumber(pdf_path)
            
            # Combine and enhance extracted content
            combined_content = self._combine_extraction_results(
                pymupdf_content, 
                pdfplumber_content
            )
            
            # Extract structured sections
            sections = self._identify_sections(combined_content['full_text'])
            
            # Extract scientific metadata
            metadata = self._extract_scientific_metadata(
                combined_content['full_text'], 
                sections
            )
            
            # Extract citations and references
            citations = self._extract_citations(combined_content['full_text'])
            references = self._extract_references(sections.get('references', ''))
            
            # Extract figures and tables
            figures_tables = self._extract_figures_tables(pdf_path)
            
            # Calculate document statistics
            stats = self._calculate_document_stats(combined_content['full_text'])
            
            return {
                'document_id': doc_id,
                'file_path': str(pdf_path),
                'metadata': metadata,
                'full_text': combined_content['full_text'],
                'sections': sections,
                'citations': citations,
                'references': references,
                'figures_tables': figures_tables,
                'statistics': stats,
                'processing_timestamp': datetime.now().isoformat(),
                'extraction_quality': self._assess_extraction_quality(sections)
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            raise
    
    def _generate_document_id(self, pdf_path: Path) -> str:
        """Generate unique document ID based on file content"""
        with open(pdf_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return f"doc_{file_hash[:16]}"
    
    def _extract_with_pymupdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract content using PyMuPDF (better for text extraction)"""
        content = {
            'full_text': '',
            'pages': [],
            'metadata': {},
            'toc': []
        }
        
        try:
            doc = fitz.open(pdf_path)
            
            # Extract metadata
            content['metadata'] = doc.metadata or {}
            
            # Extract table of contents
            content['toc'] = doc.get_toc()
            
            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                content['pages'].append({
                    'page_number': page_num + 1,
                    'text': page_text,
                    'word_count': len(page_text.split())
                })
                content['full_text'] += page_text + '\n'
            
            doc.close()
            
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            
        return content
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract content using pdfplumber (better for tables and layout)"""
        content = {
            'full_text': '',
            'pages': [],
            'tables': [],
            'metadata': {}
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract metadata
                content['metadata'] = pdf.metadata or {}
                
                # Extract content from each page
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ''
                    
                    # Extract tables from this page
                    tables = page.extract_tables()
                    page_tables = []
                    for table in tables:
                        if table:  # Skip empty tables
                            page_tables.append({
                                'page': page_num + 1,
                                'data': table,
                                'rows': len(table),
                                'cols': len(table[0]) if table else 0
                            })
                    
                    content['pages'].append({
                        'page_number': page_num + 1,
                        'text': page_text,
                        'tables': page_tables,
                        'word_count': len(page_text.split())
                    })
                    
                    content['full_text'] += page_text + '\n'
                    content['tables'].extend(page_tables)
                    
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            
        return content
    
    def _combine_extraction_results(self, pymupdf_content: Dict, pdfplumber_content: Dict) -> Dict:
        """Combine results from both extraction methods"""
        # Use the longer text extraction (usually more complete)
        if len(pymupdf_content['full_text']) > len(pdfplumber_content['full_text']):
            full_text = pymupdf_content['full_text']
        else:
            full_text = pdfplumber_content['full_text']
        
        # Combine metadata
        metadata = {**pymupdf_content.get('metadata', {}), **pdfplumber_content.get('metadata', {})}
        
        return {
            'full_text': full_text,
            'metadata': metadata,
            'tables': pdfplumber_content.get('tables', []),
            'toc': pymupdf_content.get('toc', [])
        }
    
    def _identify_sections(self, text: str) -> Dict[str, str]:
        """Identify and extract scientific paper sections"""
        sections = {}
        text_lower = text.lower()
        
        for section_name, pattern in self.section_patterns.items():
            try:
                match = re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL)
                if match:
                    # Get the matched text from original (preserve case)
                    start_pos = match.start(1) if match.groups() else match.start()
                    end_pos = match.end(1) if match.groups() else match.end()
                    
                    # Find corresponding positions in original text
                    section_text = text[start_pos:end_pos].strip()
                    sections[section_name] = section_text
                    
            except Exception as e:
                logger.warning(f"Error extracting section {section_name}: {e}")
                sections[section_name] = ""
        
        return sections
    
    def _extract_scientific_metadata(self, text: str, sections: Dict[str, str]) -> Dict[str, Any]:
        """Extract scientific metadata from the document"""
        metadata = {}
        
        # Extract DOI
        doi_match = re.search(self.doi_pattern, text, re.IGNORECASE)
        if doi_match:
            metadata['doi'] = doi_match.group(1)
        
        # Extract title (usually first line or from title section)
        title = sections.get('title', '')
        if not title and text:
            # Try to extract title from first few lines
            first_lines = text.split('\n')[:5]
            for line in first_lines:
                if len(line.strip()) > 10 and not line.strip().lower().startswith(('abstract', 'keywords')):
                    title = line.strip()
                    break
        metadata['title'] = title
        
        # Extract authors (simple pattern matching)
        authors = []
        author_matches = re.findall(self.author_pattern, text[:2000])  # Search in first 2000 chars
        if author_matches:
            authors = list(set(author_matches[:10]))  # Limit to 10 unique authors
        metadata['authors'] = authors
        
        # Extract journal information
        journal_match = re.search(self.journal_pattern, text, re.IGNORECASE)
        if journal_match:
            metadata['journal'] = journal_match.group(1).strip()
        
        # Extract publication year
        year_matches = re.findall(r'\b(19|20)\d{2}\b', text)
        if year_matches:
            # Get the most recent year that's not in the future
            current_year = datetime.now().year
            valid_years = [int(year) for year in year_matches if int(year) <= current_year]
            if valid_years:
                metadata['publication_year'] = max(valid_years)
        
        # Extract keywords
        keywords_text = sections.get('keywords', '')
        if keywords_text:
            # Split by common delimiters
            keywords = re.split(r'[,;]\s*', keywords_text)
            metadata['keywords'] = [kw.strip() for kw in keywords if kw.strip()]
        
        return metadata
    
    def _extract_citations(self, text: str) -> List[Dict[str, Any]]:
        """Extract in-text citations"""
        citations = []
        
        # Find numbered citations [1], [2-5], etc.
        numbered_citations = re.findall(r'\[(\d+(?:[-,]\s*\d+)*)\]', text)
        for citation in numbered_citations:
            citations.append({
                'type': 'numbered',
                'reference': citation,
                'context': 'in-text'
            })
        
        # Find author-year citations (Smith et al., 2020)
        author_year_citations = re.findall(r'\(([^)]+\d{4}[^)]*)\)', text)
        for citation in author_year_citations:
            if re.search(r'\d{4}', citation):  # Ensure it contains a year
                citations.append({
                    'type': 'author-year',
                    'reference': citation,
                    'context': 'in-text'
                })
        
        return citations
    
    def _extract_references(self, references_text: str) -> List[Dict[str, Any]]:
        """Extract reference list from references section"""
        references = []
        
        if not references_text:
            return references
        
        # Split references by common patterns
        ref_lines = re.split(r'\n(?=\d+\.|\[\d+\])', references_text)
        
        for ref_line in ref_lines:
            if len(ref_line.strip()) > 20:  # Filter out very short lines
                ref_data = {
                    'raw_text': ref_line.strip(),
                    'authors': [],
                    'title': '',
                    'journal': '',
                    'year': None,
                    'doi': None
                }
                
                # Extract DOI from reference
                doi_match = re.search(self.doi_pattern, ref_line)
                if doi_match:
                    ref_data['doi'] = doi_match.group(1)
                
                # Extract year
                year_match = re.search(r'\b(19|20)\d{2}\b', ref_line)
                if year_match:
                    ref_data['year'] = int(year_match.group())
                
                references.append(ref_data)
        
        return references
    
    def _extract_figures_tables(self, pdf_path: Path) -> Dict[str, List]:
        """Extract information about figures and tables"""
        figures_tables = {
            'figures': [],
            'tables': []
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract tables
                    tables = page.extract_tables()
                    for i, table in enumerate(tables):
                        if table and len(table) > 1:  # Skip empty or single-row tables
                            figures_tables['tables'].append({
                                'page': page_num + 1,
                                'table_id': f"table_{page_num + 1}_{i + 1}",
                                'rows': len(table),
                                'columns': len(table[0]) if table else 0,
                                'data_preview': table[:3] if len(table) > 3 else table  # First 3 rows
                            })
                    
                    # Look for figure references in text
                    page_text = page.extract_text() or ''
                    figure_refs = re.findall(r'(?:Figure|Fig\.?)\s*(\d+)', page_text, re.IGNORECASE)
                    for fig_num in figure_refs:
                        figures_tables['figures'].append({
                            'page': page_num + 1,
                            'figure_id': f"figure_{fig_num}",
                            'reference': f"Figure {fig_num}"
                        })
        
        except Exception as e:
            logger.error(f"Error extracting figures/tables: {e}")
        
        return figures_tables
    
    def _calculate_document_stats(self, text: str) -> Dict[str, Any]:
        """Calculate document statistics"""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        paragraphs = text.split('\n\n')
        
        return {
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'paragraph_count': len([p for p in paragraphs if p.strip()]),
            'character_count': len(text),
            'average_words_per_sentence': len(words) / max(len(sentences), 1),
            'reading_time_minutes': len(words) / 200  # Assuming 200 words per minute
        }
    
    def _assess_extraction_quality(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """Assess the quality of text extraction"""
        quality_score = 0
        quality_factors = {}
        
        # Check if key sections are present
        key_sections = ['abstract', 'introduction', 'methods', 'results', 'conclusion']
        sections_found = sum(1 for section in key_sections if sections.get(section, '').strip())
        quality_factors['sections_found'] = sections_found
        quality_score += sections_found * 0.2
        
        # Check text length (longer usually means better extraction)
        total_text_length = sum(len(text) for text in sections.values())
        if total_text_length > 5000:
            quality_factors['sufficient_text'] = True
            quality_score += 0.3
        else:
            quality_factors['sufficient_text'] = False
        
        # Check for scientific indicators
        scientific_terms = ['study', 'research', 'analysis', 'method', 'result', 'conclusion']
        full_text = ' '.join(sections.values()).lower()
        scientific_term_count = sum(1 for term in scientific_terms if term in full_text)
        quality_factors['scientific_terms'] = scientific_term_count
        quality_score += min(scientific_term_count * 0.05, 0.3)
        
        return {
            'overall_score': min(quality_score, 1.0),
            'factors': quality_factors,
            'assessment': 'high' if quality_score > 0.7 else 'medium' if quality_score > 0.4 else 'low'
        }

# Global instance
scientific_pdf_processor = ScientificPDFProcessor()