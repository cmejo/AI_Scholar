"""
Instance-Specific Document Processor for Multi-Instance Vector Store.

This module handles instance-aware document chunk creation, metadata schemas,
and processing pipelines tailored for different scholar instances.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
import re
import hashlib
from abc import ABC, abstractmethod

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.shared.multi_instance_data_models import (
        BasePaper, ArxivPaper, JournalPaper, InstanceConfig
    )
except ImportError as e:
    print(f"Import error: {e}")
    raise

logger = logging.getLogger(__name__)


class BaseDocumentProcessor(ABC):
    """
    Abstract base class for instance-specific document processors.
    """
    
    def __init__(self, instance_name: str, config: InstanceConfig):
        self.instance_name = instance_name
        self.config = config
        self.chunk_size = config.processing_config.batch_size * 50  # Approximate chunk size
        self.chunk_overlap = 200
        
        # Instance-specific processing rules
        self.processing_rules = self._get_processing_rules()
        
    @abstractmethod
    def _get_processing_rules(self) -> Dict[str, Any]:
        """Get instance-specific processing rules."""
        pass
    
    @abstractmethod
    def _get_metadata_schema(self) -> Dict[str, Any]:
        """Get instance-specific metadata schema."""
        pass
    
    def create_document_chunks(
        self, 
        paper: BasePaper, 
        content: str,
        section_markers: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Create instance-aware document chunks."""
        
        try:
            # Split content into sections if markers provided
            sections = self._split_into_sections(content, section_markers or {})
            
            # Create chunks for each section
            all_chunks = []
            chunk_index = 0
            
            for section_name, section_content in sections.items():
                section_chunks = self._create_section_chunks(
                    section_content, 
                    section_name,
                    chunk_index
                )
                
                # Add instance-specific metadata to each chunk
                for chunk in section_chunks:
                    chunk.update(self._create_chunk_metadata(paper, chunk, section_name))
                    chunk['chunk_index'] = chunk_index
                    chunk_index += 1
                
                all_chunks.extend(section_chunks)
            
            logger.info(f"Created {len(all_chunks)} chunks for {paper.get_document_id()} in {self.instance_name}")
            return all_chunks
            
        except Exception as e:
            logger.error(f"Error creating chunks for {paper.get_document_id()}: {e}")
            return []
    
    def _split_into_sections(
        self, 
        content: str, 
        section_markers: Dict[str, str]
    ) -> Dict[str, str]:
        """Split content into sections based on markers."""
        
        if not section_markers:
            return {"main": content}
        
        sections = {}
        current_section = "introduction"
        current_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            # Check if line matches any section marker
            section_found = None
            for section_name, marker_pattern in section_markers.items():
                if re.search(marker_pattern, line, re.IGNORECASE):
                    section_found = section_name
                    break
            
            if section_found:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = section_found
                current_content = [line]
            else:
                current_content.append(line)
        
        # Save final section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _create_section_chunks(
        self, 
        section_content: str, 
        section_name: str,
        start_index: int
    ) -> List[Dict[str, Any]]:
        """Create chunks for a specific section."""
        
        chunks = []
        
        # Apply instance-specific chunking rules
        chunk_strategy = self.processing_rules.get('chunk_strategy', 'sliding_window')
        
        if chunk_strategy == 'sliding_window':
            chunks = self._sliding_window_chunking(section_content, section_name)
        elif chunk_strategy == 'sentence_boundary':
            chunks = self._sentence_boundary_chunking(section_content, section_name)
        elif chunk_strategy == 'paragraph_boundary':
            chunks = self._paragraph_boundary_chunking(section_content, section_name)
        else:
            # Default to sliding window
            chunks = self._sliding_window_chunking(section_content, section_name)
        
        return chunks
    
    def _sliding_window_chunking(
        self, 
        content: str, 
        section_name: str
    ) -> List[Dict[str, Any]]:
        """Create chunks using sliding window approach."""
        
        chunks = []
        words = content.split()
        
        if len(words) <= self.chunk_size:
            # Content fits in one chunk
            chunks.append({
                'text': content,
                'section': section_name,
                'chunk_type': 'complete_section',
                'word_count': len(words),
                'character_count': len(content)
            })
        else:
            # Create overlapping chunks
            start = 0
            chunk_num = 0
            
            while start < len(words):
                end = min(start + self.chunk_size, len(words))
                chunk_words = words[start:end]
                chunk_text = ' '.join(chunk_words)
                
                chunks.append({
                    'text': chunk_text,
                    'section': section_name,
                    'chunk_type': 'sliding_window',
                    'word_count': len(chunk_words),
                    'character_count': len(chunk_text),
                    'chunk_number': chunk_num,
                    'start_word': start,
                    'end_word': end
                })
                
                # Move start position with overlap
                start += self.chunk_size - self.chunk_overlap
                chunk_num += 1
                
                # Break if we've covered all content
                if end >= len(words):
                    break
        
        return chunks
    
    def _sentence_boundary_chunking(
        self, 
        content: str, 
        section_name: str
    ) -> List[Dict[str, Any]]:
        """Create chunks respecting sentence boundaries."""
        
        # Simple sentence splitting (can be enhanced with NLP libraries)
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            if current_word_count + sentence_words > self.chunk_size and current_chunk:
                # Create chunk from current sentences
                chunk_text = '. '.join(current_chunk) + '.'
                chunks.append({
                    'text': chunk_text,
                    'section': section_name,
                    'chunk_type': 'sentence_boundary',
                    'word_count': current_word_count,
                    'character_count': len(chunk_text),
                    'sentence_count': len(current_chunk)
                })
                
                # Start new chunk
                current_chunk = [sentence]
                current_word_count = sentence_words
            else:
                current_chunk.append(sentence)
                current_word_count += sentence_words
        
        # Add final chunk
        if current_chunk:
            chunk_text = '. '.join(current_chunk) + '.'
            chunks.append({
                'text': chunk_text,
                'section': section_name,
                'chunk_type': 'sentence_boundary',
                'word_count': current_word_count,
                'character_count': len(chunk_text),
                'sentence_count': len(current_chunk)
            })
        
        return chunks
    
    def _paragraph_boundary_chunking(
        self, 
        content: str, 
        section_name: str
    ) -> List[Dict[str, Any]]:
        """Create chunks respecting paragraph boundaries."""
        
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for paragraph in paragraphs:
            paragraph_words = len(paragraph.split())
            
            if current_word_count + paragraph_words > self.chunk_size and current_chunk:
                # Create chunk from current paragraphs
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'section': section_name,
                    'chunk_type': 'paragraph_boundary',
                    'word_count': current_word_count,
                    'character_count': len(chunk_text),
                    'paragraph_count': len(current_chunk)
                })
                
                # Start new chunk
                current_chunk = [paragraph]
                current_word_count = paragraph_words
            else:
                current_chunk.append(paragraph)
                current_word_count += paragraph_words
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'section': section_name,
                'chunk_type': 'paragraph_boundary',
                'word_count': current_word_count,
                'character_count': len(chunk_text),
                'paragraph_count': len(current_chunk)
            })
        
        return chunks
    
    def _create_chunk_metadata(
        self, 
        paper: BasePaper, 
        chunk: Dict[str, Any], 
        section_name: str
    ) -> Dict[str, Any]:
        """Create instance-specific metadata for a chunk."""
        
        # Base metadata schema
        metadata_schema = self._get_metadata_schema()
        
        # Create chunk-specific metadata
        chunk_metadata = {
            'document_metadata': {
                # Instance information
                'instance_name': self.instance_name,
                'instance_type': 'scholar_instance',
                'processing_timestamp': datetime.now().isoformat(),
                
                # Paper information
                'document_id': paper.get_document_id(),
                'paper_id': paper.paper_id,
                'title': paper.title,
                'authors': paper.authors,
                'abstract': paper.abstract[:500] + "..." if len(paper.abstract) > 500 else paper.abstract,
                'published_date': paper.published_date.isoformat(),
                'source_type': paper.source_type,
                
                # Chunk information
                'section': section_name,
                'chunk_type': chunk.get('chunk_type', 'standard'),
                'word_count': chunk.get('word_count', 0),
                'character_count': chunk.get('character_count', 0),
                
                # Quality indicators
                'text_quality_score': self._calculate_text_quality(chunk['text']),
                'section_importance': self._get_section_importance(section_name),
                
                # Instance-specific fields from schema
                **{field: self._extract_field_value(paper, chunk, field, config) 
                   for field, config in metadata_schema.items()}
            }
        }
        
        # Add paper-type specific metadata
        if isinstance(paper, ArxivPaper):
            chunk_metadata['document_metadata'].update({
                'arxiv_id': paper.arxiv_id,
                'categories': paper.categories,
                'doi': paper.doi,
                'pdf_url': paper.pdf_url,
                'updated_date': paper.updated_date.isoformat() if paper.updated_date else None
            })
        elif isinstance(paper, JournalPaper):
            chunk_metadata['document_metadata'].update({
                'journal_name': paper.journal_name,
                'volume': paper.volume,
                'issue': paper.issue,
                'pages': paper.pages,
                'doi': paper.doi,
                'journal_url': paper.journal_url
            })
        
        return chunk_metadata
    
    def _calculate_text_quality(self, text: str) -> float:
        """Calculate a quality score for the text chunk."""
        
        if not text or not text.strip():
            return 0.0
        
        quality_factors = []
        
        # Length factor (not too short, not too long)
        length = len(text.split())
        if 50 <= length <= 500:
            quality_factors.append(1.0)
        elif 20 <= length < 50 or 500 < length <= 1000:
            quality_factors.append(0.8)
        else:
            quality_factors.append(0.5)
        
        # Sentence structure factor
        sentences = re.split(r'[.!?]+', text)
        complete_sentences = len([s for s in sentences if len(s.strip()) > 10])
        if complete_sentences >= 2:
            quality_factors.append(1.0)
        elif complete_sentences == 1:
            quality_factors.append(0.7)
        else:
            quality_factors.append(0.4)
        
        # Content diversity factor (variety of words)
        words = text.lower().split()
        unique_words = len(set(words))
        if len(words) > 0:
            diversity = unique_words / len(words)
            if diversity > 0.7:
                quality_factors.append(1.0)
            elif diversity > 0.5:
                quality_factors.append(0.8)
            else:
                quality_factors.append(0.6)
        else:
            quality_factors.append(0.0)
        
        # Special character factor (not too many, indicates clean text)
        special_chars = len(re.findall(r'[^\w\s.,!?;:\-()]', text))
        special_ratio = special_chars / len(text) if text else 0
        if special_ratio < 0.05:
            quality_factors.append(1.0)
        elif special_ratio < 0.1:
            quality_factors.append(0.8)
        else:
            quality_factors.append(0.6)
        
        return sum(quality_factors) / len(quality_factors)
    
    def _get_section_importance(self, section_name: str) -> float:
        """Get importance score for a section."""
        
        importance_map = {
            'abstract': 1.0,
            'introduction': 0.9,
            'conclusion': 0.9,
            'results': 0.8,
            'methodology': 0.8,
            'method': 0.8,
            'discussion': 0.7,
            'related_work': 0.6,
            'literature_review': 0.6,
            'references': 0.3,
            'acknowledgments': 0.2,
            'appendix': 0.4
        }
        
        return importance_map.get(section_name.lower(), 0.5)
    
    def _extract_field_value(
        self, 
        paper: BasePaper, 
        chunk: Dict[str, Any], 
        field_name: str, 
        field_config: Dict[str, Any]
    ) -> Any:
        """Extract value for a metadata field based on configuration."""
        
        field_type = field_config.get('type', 'string')
        source = field_config.get('source', 'paper')
        
        if source == 'paper':
            return getattr(paper, field_name, field_config.get('default'))
        elif source == 'chunk':
            return chunk.get(field_name, field_config.get('default'))
        elif source == 'computed':
            # Handle computed fields
            if field_name == 'content_hash':
                return hashlib.md5(chunk['text'].encode()).hexdigest()
            elif field_name == 'processing_version':
                return '1.0'
            else:
                return field_config.get('default')
        else:
            return field_config.get('default')
    
    def validate_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate created chunks for quality and completeness."""
        
        validation_result = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'stats': {
                'total_chunks': len(chunks),
                'empty_chunks': 0,
                'low_quality_chunks': 0,
                'missing_metadata': 0,
                'average_quality': 0.0,
                'total_words': 0,
                'total_characters': 0
            }
        }
        
        if not chunks:
            validation_result['valid'] = False
            validation_result['issues'].append("No chunks created")
            return validation_result
        
        total_quality = 0.0
        
        for i, chunk in enumerate(chunks):
            # Check for empty chunks
            if not chunk.get('text', '').strip():
                validation_result['stats']['empty_chunks'] += 1
                validation_result['issues'].append(f"Chunk {i} is empty")
                validation_result['valid'] = False
                continue
            
            # Check for missing metadata
            if 'document_metadata' not in chunk:
                validation_result['stats']['missing_metadata'] += 1
                validation_result['warnings'].append(f"Chunk {i} missing document_metadata")
            
            # Check quality
            quality = chunk.get('document_metadata', {}).get('text_quality_score', 0.0)
            total_quality += quality
            
            if quality < 0.5:
                validation_result['stats']['low_quality_chunks'] += 1
                validation_result['warnings'].append(f"Chunk {i} has low quality score: {quality:.2f}")
            
            # Update stats
            validation_result['stats']['total_words'] += chunk.get('word_count', 0)
            validation_result['stats']['total_characters'] += chunk.get('character_count', 0)
        
        # Calculate averages
        if chunks:
            validation_result['stats']['average_quality'] = total_quality / len(chunks)
        
        # Check overall quality
        if validation_result['stats']['low_quality_chunks'] > len(chunks) * 0.3:
            validation_result['warnings'].append("More than 30% of chunks have low quality scores")
        
        return validation_result


class AIScholarDocumentProcessor(BaseDocumentProcessor):
    """
    Document processor specialized for AI Scholar instance.
    Focuses on AI, ML, and physics papers with appropriate chunking strategies.
    """
    
    def _get_processing_rules(self) -> Dict[str, Any]:
        """Get AI Scholar specific processing rules."""
        return {
            'chunk_strategy': 'sentence_boundary',  # Better for technical content
            'preserve_equations': True,
            'preserve_code_blocks': True,
            'section_priorities': {
                'abstract': 1.0,
                'introduction': 0.9,
                'methodology': 0.9,
                'method': 0.9,
                'results': 0.8,
                'conclusion': 0.8,
                'related_work': 0.6,
                'references': 0.3
            },
            'technical_term_preservation': True,
            'mathematical_notation_handling': True
        }
    
    def _get_metadata_schema(self) -> Dict[str, Any]:
        """Get AI Scholar specific metadata schema."""
        return {
            'research_area': {
                'type': 'string',
                'source': 'computed',
                'default': 'artificial_intelligence'
            },
            'technical_complexity': {
                'type': 'float',
                'source': 'computed',
                'default': 0.5
            },
            'contains_equations': {
                'type': 'boolean',
                'source': 'computed',
                'default': False
            },
            'contains_code': {
                'type': 'boolean',
                'source': 'computed',
                'default': False
            },
            'ml_keywords_count': {
                'type': 'integer',
                'source': 'computed',
                'default': 0
            },
            'citation_density': {
                'type': 'float',
                'source': 'computed',
                'default': 0.0
            }
        }
    
    def _extract_field_value(
        self, 
        paper: BasePaper, 
        chunk: Dict[str, Any], 
        field_name: str, 
        field_config: Dict[str, Any]
    ) -> Any:
        """Extract AI Scholar specific field values."""
        
        if field_name == 'technical_complexity':
            return self._calculate_technical_complexity(chunk['text'])
        elif field_name == 'contains_equations':
            return self._contains_equations(chunk['text'])
        elif field_name == 'contains_code':
            return self._contains_code(chunk['text'])
        elif field_name == 'ml_keywords_count':
            return self._count_ml_keywords(chunk['text'])
        elif field_name == 'citation_density':
            return self._calculate_citation_density(chunk['text'])
        elif field_name == 'research_area':
            return self._determine_research_area(paper, chunk['text'])
        else:
            return super()._extract_field_value(paper, chunk, field_name, field_config)
    
    def _calculate_technical_complexity(self, text: str) -> float:
        """Calculate technical complexity score for AI/ML content."""
        
        complexity_indicators = [
            r'\b(algorithm|optimization|neural|network|learning|training)\b',
            r'\b(gradient|backpropagation|convolution|attention|transformer)\b',
            r'\b(classification|regression|clustering|reinforcement)\b',
            r'\b(tensor|matrix|vector|dimension|embedding)\b',
            r'\b(accuracy|precision|recall|f1|loss|error)\b'
        ]
        
        total_matches = 0
        for pattern in complexity_indicators:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            total_matches += matches
        
        # Normalize by text length
        words = len(text.split())
        if words == 0:
            return 0.0
        
        complexity = min(1.0, total_matches / (words / 100))  # Per 100 words
        return complexity
    
    def _contains_equations(self, text: str) -> bool:
        """Check if text contains mathematical equations."""
        
        equation_patterns = [
            r'\$[^$]+\$',  # LaTeX inline math
            r'\$\$[^$]+\$\$',  # LaTeX display math
            r'\\begin\{equation\}',  # LaTeX equation environment
            r'\\begin\{align\}',  # LaTeX align environment
            r'[a-zA-Z]\s*=\s*[a-zA-Z0-9\+\-\*/\(\)]+',  # Simple equations
            r'∑|∏|∫|∂|∇|α|β|γ|δ|ε|θ|λ|μ|π|σ|φ|ψ|ω'  # Mathematical symbols
        ]
        
        for pattern in equation_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _contains_code(self, text: str) -> bool:
        """Check if text contains code snippets."""
        
        code_patterns = [
            r'```[^`]*```',  # Markdown code blocks
            r'`[^`]+`',  # Inline code
            r'\bdef\s+\w+\s*\(',  # Python function definition
            r'\bclass\s+\w+\s*[\(:]',  # Python class definition
            r'\bimport\s+\w+',  # Import statements
            r'\bfrom\s+\w+\s+import',  # From import statements
            r'{\s*["\']?\w+["\']?\s*:\s*["\']?\w+["\']?\s*}',  # JSON-like objects
            r'<[^>]+>.*</[^>]+>',  # HTML/XML tags
        ]
        
        for pattern in code_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _count_ml_keywords(self, text: str) -> int:
        """Count machine learning related keywords."""
        
        ml_keywords = [
            'machine learning', 'deep learning', 'neural network', 'artificial intelligence',
            'supervised learning', 'unsupervised learning', 'reinforcement learning',
            'classification', 'regression', 'clustering', 'dimensionality reduction',
            'feature extraction', 'feature selection', 'cross validation',
            'gradient descent', 'backpropagation', 'optimization',
            'convolutional', 'recurrent', 'transformer', 'attention',
            'lstm', 'gru', 'cnn', 'rnn', 'gan', 'vae',
            'tensorflow', 'pytorch', 'keras', 'scikit-learn'
        ]
        
        text_lower = text.lower()
        count = 0
        
        for keyword in ml_keywords:
            count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
        
        return count
    
    def _calculate_citation_density(self, text: str) -> float:
        """Calculate citation density in the text."""
        
        citation_patterns = [
            r'\[[0-9,\-\s]+\]',  # [1], [1,2], [1-3]
            r'\([A-Za-z]+\s+et\s+al\.,?\s+[0-9]{4}\)',  # (Smith et al., 2020)
            r'\([A-Za-z]+\s+and\s+[A-Za-z]+,?\s+[0-9]{4}\)',  # (Smith and Jones, 2020)
            r'\([A-Za-z]+,?\s+[0-9]{4}\)'  # (Smith, 2020)
        ]
        
        total_citations = 0
        for pattern in citation_patterns:
            citations = len(re.findall(pattern, text))
            total_citations += citations
        
        # Normalize by text length (citations per 1000 characters)
        if len(text) == 0:
            return 0.0
        
        density = (total_citations / len(text)) * 1000
        return min(1.0, density)  # Cap at 1.0
    
    def _determine_research_area(self, paper: BasePaper, text: str) -> str:
        """Determine specific research area within AI."""
        
        area_keywords = {
            'natural_language_processing': [
                'nlp', 'natural language', 'text processing', 'language model',
                'tokenization', 'parsing', 'sentiment analysis', 'named entity',
                'machine translation', 'question answering', 'text generation'
            ],
            'computer_vision': [
                'computer vision', 'image processing', 'object detection',
                'image classification', 'segmentation', 'face recognition',
                'optical character recognition', 'image generation'
            ],
            'machine_learning': [
                'machine learning', 'supervised learning', 'unsupervised learning',
                'feature learning', 'ensemble methods', 'decision trees',
                'support vector machine', 'random forest'
            ],
            'deep_learning': [
                'deep learning', 'neural network', 'convolutional', 'recurrent',
                'transformer', 'attention mechanism', 'deep neural network'
            ],
            'reinforcement_learning': [
                'reinforcement learning', 'q-learning', 'policy gradient',
                'actor-critic', 'markov decision process', 'reward function'
            ],
            'robotics': [
                'robotics', 'robot', 'autonomous', 'control system',
                'path planning', 'localization', 'mapping', 'manipulation'
            ]
        }
        
        text_lower = text.lower()
        area_scores = {}
        
        for area, keywords in area_keywords.items():
            score = 0
            for keyword in keywords:
                score += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
            area_scores[area] = score
        
        # Return area with highest score, default to general AI
        if area_scores:
            best_area = max(area_scores, key=area_scores.get)
            if area_scores[best_area] > 0:
                return best_area
        
        return 'artificial_intelligence'


class QuantScholarDocumentProcessor(BaseDocumentProcessor):
    """
    Document processor specialized for Quant Scholar instance.
    Focuses on quantitative finance, economics, and statistics papers.
    """
    
    def _get_processing_rules(self) -> Dict[str, Any]:
        """Get Quant Scholar specific processing rules."""
        return {
            'chunk_strategy': 'paragraph_boundary',  # Better for financial/economic content
            'preserve_tables': True,
            'preserve_formulas': True,
            'section_priorities': {
                'abstract': 1.0,
                'introduction': 0.9,
                'methodology': 0.9,
                'empirical_results': 0.9,
                'results': 0.8,
                'conclusion': 0.8,
                'literature_review': 0.7,
                'data': 0.7,
                'references': 0.3
            },
            'financial_term_preservation': True,
            'statistical_notation_handling': True
        }
    
    def _get_metadata_schema(self) -> Dict[str, Any]:
        """Get Quant Scholar specific metadata schema."""
        return {
            'research_domain': {
                'type': 'string',
                'source': 'computed',
                'default': 'quantitative_finance'
            },
            'statistical_complexity': {
                'type': 'float',
                'source': 'computed',
                'default': 0.5
            },
            'contains_formulas': {
                'type': 'boolean',
                'source': 'computed',
                'default': False
            },
            'contains_tables': {
                'type': 'boolean',
                'source': 'computed',
                'default': False
            },
            'financial_keywords_count': {
                'type': 'integer',
                'source': 'computed',
                'default': 0
            },
            'statistical_methods_count': {
                'type': 'integer',
                'source': 'computed',
                'default': 0
            },
            'data_analysis_indicators': {
                'type': 'integer',
                'source': 'computed',
                'default': 0
            }
        }
    
    def _extract_field_value(
        self, 
        paper: BasePaper, 
        chunk: Dict[str, Any], 
        field_name: str, 
        field_config: Dict[str, Any]
    ) -> Any:
        """Extract Quant Scholar specific field values."""
        
        if field_name == 'statistical_complexity':
            return self._calculate_statistical_complexity(chunk['text'])
        elif field_name == 'contains_formulas':
            return self._contains_formulas(chunk['text'])
        elif field_name == 'contains_tables':
            return self._contains_tables(chunk['text'])
        elif field_name == 'financial_keywords_count':
            return self._count_financial_keywords(chunk['text'])
        elif field_name == 'statistical_methods_count':
            return self._count_statistical_methods(chunk['text'])
        elif field_name == 'data_analysis_indicators':
            return self._count_data_analysis_indicators(chunk['text'])
        elif field_name == 'research_domain':
            return self._determine_research_domain(paper, chunk['text'])
        else:
            return super()._extract_field_value(paper, chunk, field_name, field_config)
    
    def _calculate_statistical_complexity(self, text: str) -> float:
        """Calculate statistical complexity score for quantitative content."""
        
        complexity_indicators = [
            r'\b(regression|correlation|variance|covariance|distribution)\b',
            r'\b(hypothesis|significance|p-value|confidence|interval)\b',
            r'\b(bayesian|frequentist|likelihood|posterior|prior)\b',
            r'\b(econometric|time series|panel data|cross-section)\b',
            r'\b(volatility|risk|return|portfolio|optimization)\b'
        ]
        
        total_matches = 0
        for pattern in complexity_indicators:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            total_matches += matches
        
        # Normalize by text length
        words = len(text.split())
        if words == 0:
            return 0.0
        
        complexity = min(1.0, total_matches / (words / 100))  # Per 100 words
        return complexity
    
    def _contains_formulas(self, text: str) -> bool:
        """Check if text contains mathematical formulas."""
        
        formula_patterns = [
            r'\$[^$]+\$',  # LaTeX inline math
            r'\$\$[^$]+\$\$',  # LaTeX display math
            r'\\begin\{equation\}',  # LaTeX equation environment
            r'[A-Za-z]\s*=\s*[A-Za-z0-9\+\-\*/\(\)]+',  # Simple equations
            r'E\[[^\]]+\]',  # Expectation notation
            r'Var\[[^\]]+\]',  # Variance notation
            r'Cov\[[^\]]+\]',  # Covariance notation
            r'β|α|σ|μ|ρ|θ|λ|Σ|Π'  # Greek letters common in finance
        ]
        
        for pattern in formula_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _contains_tables(self, text: str) -> bool:
        """Check if text contains tables or tabular data."""
        
        table_patterns = [
            r'Table\s+\d+',  # Table references
            r'\|[^|]*\|[^|]*\|',  # Markdown table format
            r'\\begin\{table\}',  # LaTeX table environment
            r'\\begin\{tabular\}',  # LaTeX tabular environment
            r'(\s+\d+\.?\d*){3,}',  # Multiple numbers in a row (table data)
            r'Mean\s+Std\.\s+Dev\.',  # Common table headers
            r'Variable\s+Coefficient\s+Std\.\s+Error'  # Regression table headers
        ]
        
        for pattern in table_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _count_financial_keywords(self, text: str) -> int:
        """Count finance-related keywords."""
        
        financial_keywords = [
            'portfolio', 'risk', 'return', 'volatility', 'sharpe ratio',
            'asset pricing', 'capital asset pricing model', 'capm',
            'arbitrage', 'hedge', 'derivative', 'option', 'futures',
            'bond', 'equity', 'stock', 'market', 'trading',
            'liquidity', 'credit risk', 'market risk', 'operational risk',
            'value at risk', 'var', 'expected shortfall',
            'black-scholes', 'monte carlo', 'binomial model',
            'efficient frontier', 'markowitz', 'modern portfolio theory'
        ]
        
        text_lower = text.lower()
        count = 0
        
        for keyword in financial_keywords:
            count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
        
        return count
    
    def _count_statistical_methods(self, text: str) -> int:
        """Count statistical methods mentioned."""
        
        statistical_methods = [
            'regression', 'linear regression', 'logistic regression',
            'time series', 'arima', 'garch', 'var model',
            'panel data', 'fixed effects', 'random effects',
            'instrumental variables', 'two stage least squares',
            'maximum likelihood', 'bayesian', 'mcmc',
            'bootstrap', 'jackknife', 'cross validation',
            'hypothesis test', 't-test', 'f-test', 'chi-square',
            'anova', 'ancova', 'manova'
        ]
        
        text_lower = text.lower()
        count = 0
        
        for method in statistical_methods:
            count += len(re.findall(r'\b' + re.escape(method) + r'\b', text_lower))
        
        return count
    
    def _count_data_analysis_indicators(self, text: str) -> int:
        """Count indicators of data analysis."""
        
        analysis_indicators = [
            'dataset', 'sample', 'observation', 'variable',
            'correlation', 'coefficient', 'significant', 'p-value',
            'confidence interval', 'standard error', 'r-squared',
            'goodness of fit', 'residual', 'outlier',
            'descriptive statistics', 'summary statistics',
            'mean', 'median', 'standard deviation', 'variance'
        ]
        
        text_lower = text.lower()
        count = 0
        
        for indicator in analysis_indicators:
            count += len(re.findall(r'\b' + re.escape(indicator) + r'\b', text_lower))
        
        return count
    
    def _determine_research_domain(self, paper: BasePaper, text: str) -> str:
        """Determine specific research domain within quantitative finance."""
        
        domain_keywords = {
            'asset_pricing': [
                'asset pricing', 'capm', 'factor model', 'fama french',
                'risk premium', 'expected return', 'pricing kernel'
            ],
            'portfolio_management': [
                'portfolio', 'asset allocation', 'optimization',
                'markowitz', 'efficient frontier', 'risk parity'
            ],
            'risk_management': [
                'risk management', 'value at risk', 'var', 'expected shortfall',
                'stress testing', 'scenario analysis', 'risk measure'
            ],
            'derivatives': [
                'derivatives', 'options', 'futures', 'swaps',
                'black scholes', 'binomial model', 'monte carlo'
            ],
            'econometrics': [
                'econometrics', 'time series', 'panel data', 'regression',
                'instrumental variables', 'causality', 'identification'
            ],
            'behavioral_finance': [
                'behavioral finance', 'market anomaly', 'investor behavior',
                'sentiment', 'bias', 'psychology'
            ],
            'market_microstructure': [
                'market microstructure', 'bid ask spread', 'liquidity',
                'order flow', 'high frequency', 'market making'
            ]
        }
        
        text_lower = text.lower()
        domain_scores = {}
        
        for domain, keywords in domain_keywords.items():
            score = 0
            for keyword in keywords:
                score += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
            domain_scores[domain] = score
        
        # Return domain with highest score, default to general quantitative finance
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[best_domain] > 0:
                return best_domain
        
        return 'quantitative_finance'


class DocumentProcessorFactory:
    """
    Factory class for creating instance-specific document processors.
    """
    
    @staticmethod
    def create_processor(instance_name: str, config: InstanceConfig) -> BaseDocumentProcessor:
        """Create appropriate document processor for the instance."""
        
        if instance_name.lower() in ['ai_scholar', 'ai-scholar', 'aischolar']:
            return AIScholarDocumentProcessor(instance_name, config)
        elif instance_name.lower() in ['quant_scholar', 'quant-scholar', 'quantscholar']:
            return QuantScholarDocumentProcessor(instance_name, config)
        else:
            # Default to AI Scholar processor for unknown instances
            logger.warning(f"Unknown instance type {instance_name}, using AI Scholar processor")
            return AIScholarDocumentProcessor(instance_name, config)
    
    @staticmethod
    def get_supported_instances() -> List[str]:
        """Get list of supported instance types."""
        return ['ai_scholar', 'quant_scholar']
    
    @staticmethod
    def get_processor_info(instance_name: str) -> Dict[str, Any]:
        """Get information about a processor type."""
        
        processor_info = {
            'ai_scholar': {
                'name': 'AI Scholar Document Processor',
                'description': 'Specialized for AI, ML, and physics papers',
                'chunk_strategy': 'sentence_boundary',
                'specializations': [
                    'Technical complexity analysis',
                    'Equation and code detection',
                    'ML keyword extraction',
                    'Research area classification'
                ]
            },
            'quant_scholar': {
                'name': 'Quant Scholar Document Processor',
                'description': 'Specialized for quantitative finance and economics papers',
                'chunk_strategy': 'paragraph_boundary',
                'specializations': [
                    'Statistical complexity analysis',
                    'Formula and table detection',
                    'Financial keyword extraction',
                    'Research domain classification'
                ]
            }
        }
        
        return processor_info.get(instance_name.lower(), {})