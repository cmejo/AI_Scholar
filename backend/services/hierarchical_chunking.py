"""
Hierarchical Document Chunking Service with sentence-aware processing
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import nltk
import spacy
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

# Ensure required NLTK data is available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

logger = logging.getLogger(__name__)

class ChunkingStrategy(Enum):
    ADAPTIVE = "adaptive"
    FIXED_SIZE = "fixed_size"
    SENTENCE_AWARE = "sentence_aware"
    HIERARCHICAL = "hierarchical"

@dataclass
class ChunkBoundary:
    """Represents a chunk boundary with sentence awareness"""
    start_char: int
    end_char: int
    start_sentence: int
    end_sentence: int
    is_sentence_boundary: bool = True

@dataclass
class DocumentChunk:
    """Enhanced document chunk with hierarchical information"""
    content: str
    chunk_index: int
    chunk_level: int = 0
    parent_chunk_id: Optional[str] = None
    start_char: int = 0
    end_char: int = 0
    start_sentence: int = 0
    end_sentence: int = 0
    sentence_boundaries: List[int] = None
    overlap_start: Optional[int] = None
    overlap_end: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.sentence_boundaries is None:
            self.sentence_boundaries = []
        if self.metadata is None:
            self.metadata = {}

class SentenceAwareProcessor:
    """Handles sentence boundary detection and preservation"""
    
    def __init__(self):
        """Initialize the sentence-aware processor with NLTK and spaCy"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.use_spacy = True
            logger.info("Loaded spaCy model for sentence processing")
        except OSError:
            logger.warning("spaCy model not available, falling back to NLTK")
            self.nlp = None
            self.use_spacy = False
        
        self.stop_words = set(stopwords.words('english'))
    
    def detect_sentence_boundaries(self, text: str) -> List[Tuple[int, int]]:
        """
        Detect sentence boundaries in text
        Returns list of (start_char, end_char) tuples for each sentence
        """
        if self.use_spacy and self.nlp:
            return self._detect_boundaries_spacy(text)
        else:
            return self._detect_boundaries_nltk(text)
    
    def _detect_boundaries_spacy(self, text: str) -> List[Tuple[int, int]]:
        """Use spaCy for more accurate sentence boundary detection"""
        doc = self.nlp(text)
        boundaries = []
        
        for sent in doc.sents:
            boundaries.append((sent.start_char, sent.end_char))
        
        return boundaries
    
    def _detect_boundaries_nltk(self, text: str) -> List[Tuple[int, int]]:
        """Fallback to NLTK for sentence boundary detection"""
        sentences = sent_tokenize(text)
        boundaries = []
        current_pos = 0
        
        for sentence in sentences:
            start_pos = text.find(sentence, current_pos)
            if start_pos != -1:
                end_pos = start_pos + len(sentence)
                boundaries.append((start_pos, end_pos))
                current_pos = end_pos
            else:
                # Fallback: estimate position
                end_pos = current_pos + len(sentence)
                boundaries.append((current_pos, end_pos))
                current_pos = end_pos
        
        return boundaries
    
    def preserve_sentence_integrity(self, text: str, chunk_start: int, chunk_end: int) -> Tuple[int, int]:
        """
        Adjust chunk boundaries to preserve sentence integrity
        Returns adjusted (start, end) positions
        """
        sentence_boundaries = self.detect_sentence_boundaries(text)
        
        # Find the best sentence boundary for start position
        adjusted_start = chunk_start
        for start_char, end_char in sentence_boundaries:
            if start_char <= chunk_start <= end_char:
                # If we're in the middle of a sentence, move to sentence start
                if chunk_start > start_char:
                    adjusted_start = start_char
                break
        
        # Find the best sentence boundary for end position
        adjusted_end = chunk_end
        for start_char, end_char in sentence_boundaries:
            if start_char <= chunk_end <= end_char:
                # If we're in the middle of a sentence, move to sentence end
                if chunk_end < end_char:
                    adjusted_end = end_char
                break
        
        return adjusted_start, adjusted_end
    
    def get_sentence_indices(self, text: str, chunk_start: int, chunk_end: int) -> List[int]:
        """
        Get sentence indices that fall within the chunk boundaries
        Returns list of sentence indices (0-based)
        """
        sentence_boundaries = self.detect_sentence_boundaries(text)
        sentence_indices = []
        
        for i, (start_char, end_char) in enumerate(sentence_boundaries):
            # Check if sentence overlaps with chunk
            if not (end_char <= chunk_start or start_char >= chunk_end):
                sentence_indices.append(i)
        
        return sentence_indices
    
    def extract_sentences(self, text: str) -> List[str]:
        """Extract individual sentences from text"""
        if self.use_spacy and self.nlp:
            doc = self.nlp(text)
            return [sent.text.strip() for sent in doc.sents]
        else:
            return sent_tokenize(text)
    
    def calculate_sentence_importance(self, sentence: str, context: str = "") -> float:
        """
        Calculate importance score for a sentence based on various factors
        Returns score between 0.0 and 1.0
        """
        score = 0.0
        
        # Length factor (moderate length sentences are often more important)
        words = word_tokenize(sentence.lower())
        word_count = len(words)
        if 10 <= word_count <= 30:
            score += 0.2
        elif 5 <= word_count <= 50:
            score += 0.1
        
        # Keyword density (sentences with fewer stop words might be more important)
        content_words = [w for w in words if w.isalpha() and w not in self.stop_words]
        if words:
            content_ratio = len(content_words) / len(words)
            score += content_ratio * 0.3
        
        # Position indicators (sentences with certain patterns might be important)
        sentence_lower = sentence.lower()
        
        # Question sentences
        if sentence.strip().endswith('?'):
            score += 0.1
        
        # Sentences with numbers or statistics
        if re.search(r'\d+', sentence):
            score += 0.1
        
        # Sentences with emphasis indicators
        emphasis_patterns = [
            r'\b(important|significant|crucial|key|main|primary|essential)\b',
            r'\b(conclusion|summary|result|finding)\b',
            r'\b(first|second|third|finally|lastly)\b'
        ]
        
        for pattern in emphasis_patterns:
            if re.search(pattern, sentence_lower):
                score += 0.1
                break
        
        # Named entities (if spaCy is available)
        if self.use_spacy and self.nlp:
            doc = self.nlp(sentence)
            if doc.ents:
                score += min(len(doc.ents) * 0.05, 0.2)
        
        return min(score, 1.0)

class OverlapManager:
    """Enhanced overlap manager for managing chunk boundaries and relationships"""
    
    def __init__(self, overlap_percentage: float = 0.1, min_overlap_chars: int = 50, max_overlap_chars: int = 500):
        """
        Initialize overlap manager with configurable parameters
        
        Args:
            overlap_percentage: Percentage of chunk to overlap (0.0 to 0.5)
            min_overlap_chars: Minimum overlap in characters
            max_overlap_chars: Maximum overlap in characters
        """
        self.overlap_percentage = max(0.0, min(overlap_percentage, 0.5))
        self.min_overlap_chars = min_overlap_chars
        self.max_overlap_chars = max_overlap_chars
        self.chunk_relationships = {}  # Track relationships between chunks
        self.boundary_cache = {}  # Cache for boundary calculations
    
    def calculate_overlap_boundaries(self, 
                                   chunks: List[DocumentChunk], 
                                   text: str,
                                   sentence_processor: SentenceAwareProcessor) -> List[DocumentChunk]:
        """
        Enhanced overlap boundary calculation with relationship tracking and configurable overlap
        """
        if len(chunks) <= 1:
            return chunks
        
        sentence_boundaries = sentence_processor.detect_sentence_boundaries(text)
        
        # Clear previous relationships for this calculation
        self.chunk_relationships.clear()
        
        for i in range(len(chunks)):
            current_chunk = chunks[i]
            chunk_id = f"level_{current_chunk.chunk_level}_{current_chunk.chunk_index}"
            
            # Initialize relationships for this chunk
            self.chunk_relationships[chunk_id] = {
                'overlaps_with': [],
                'overlapped_by': [],
                'adjacent_chunks': [],
                'overlap_metrics': {
                    'backward_overlap_chars': 0,
                    'forward_overlap_chars': 0,
                    'overlap_percentage_actual': 0.0
                }
            }
            
            # Calculate overlap with previous chunk
            if i > 0:
                prev_chunk = chunks[i - 1]
                prev_chunk_id = f"level_{prev_chunk.chunk_level}_{prev_chunk.chunk_index}"
                
                overlap_start_char, overlap_content_before, overlap_chars = self._calculate_backward_overlap(
                    current_chunk, prev_chunk, text, sentence_boundaries
                )
                
                if overlap_start_char is not None:
                    current_chunk.overlap_start = overlap_start_char
                    current_chunk.metadata['overlap_content_before'] = overlap_content_before
                    
                    # Track overlap metrics
                    self.chunk_relationships[chunk_id]['overlap_metrics']['backward_overlap_chars'] = overlap_chars
                    
                    # Track relationships
                    self.chunk_relationships[chunk_id]['overlapped_by'].append(prev_chunk_id)
                    if prev_chunk_id in self.chunk_relationships:
                        self.chunk_relationships[prev_chunk_id]['overlaps_with'].append(chunk_id)
                        self.chunk_relationships[prev_chunk_id]['overlap_metrics']['forward_overlap_chars'] = overlap_chars
                
                # Track adjacency
                self.chunk_relationships[chunk_id]['adjacent_chunks'].append(prev_chunk_id)
                if prev_chunk_id in self.chunk_relationships:
                    self.chunk_relationships[prev_chunk_id]['adjacent_chunks'].append(chunk_id)
            
            # Calculate overlap with next chunk
            if i < len(chunks) - 1:
                next_chunk = chunks[i + 1]
                next_chunk_id = f"level_{next_chunk.chunk_level}_{next_chunk.chunk_index}"
                
                overlap_end_char, overlap_content_after, overlap_chars = self._calculate_forward_overlap(
                    current_chunk, next_chunk, text, sentence_boundaries
                )
                
                if overlap_end_char is not None:
                    current_chunk.overlap_end = overlap_end_char
                    current_chunk.metadata['overlap_content_after'] = overlap_content_after
                    
                    # Track overlap metrics
                    self.chunk_relationships[chunk_id]['overlap_metrics']['forward_overlap_chars'] = overlap_chars
                    
                    # Track relationships
                    self.chunk_relationships[chunk_id]['overlaps_with'].append(next_chunk_id)
            
            # Calculate actual overlap percentage
            total_overlap = (self.chunk_relationships[chunk_id]['overlap_metrics']['backward_overlap_chars'] + 
                           self.chunk_relationships[chunk_id]['overlap_metrics']['forward_overlap_chars'])
            if len(current_chunk.content) > 0:
                actual_overlap_percentage = total_overlap / len(current_chunk.content)
                self.chunk_relationships[chunk_id]['overlap_metrics']['overlap_percentage_actual'] = actual_overlap_percentage
        
        # Store relationship information in chunk metadata
        for chunk in chunks:
            chunk_id = f"level_{chunk.chunk_level}_{chunk.chunk_index}"
            if chunk_id in self.chunk_relationships:
                chunk.metadata['relationships'] = self.chunk_relationships[chunk_id]
        
        return chunks
    
    def _calculate_backward_overlap(self, current_chunk: DocumentChunk, prev_chunk: DocumentChunk, 
                                  text: str, sentence_boundaries: List[Tuple[int, int]]) -> Tuple[Optional[int], str, int]:
        """Calculate overlap with previous chunk"""
        # Calculate desired overlap size based on configurable percentage
        base_overlap_size = int(len(prev_chunk.content) * self.overlap_percentage)
        overlap_size = max(
            self.min_overlap_chars,
            min(self.max_overlap_chars, base_overlap_size)
        )
        
        # Find optimal overlap start position
        target_start = max(0, current_chunk.start_char - overlap_size)
        
        # Adjust to sentence boundary for better coherence
        overlap_start_char = self._find_optimal_sentence_boundary(
            target_start, sentence_boundaries, direction='start'
        )
        
        # Ensure overlap doesn't go beyond previous chunk's start
        if overlap_start_char < prev_chunk.start_char:
            overlap_start_char = prev_chunk.start_char
        
        # Ensure overlap doesn't exceed current chunk's start
        if overlap_start_char >= current_chunk.start_char:
            overlap_start_char = max(0, current_chunk.start_char - self.min_overlap_chars)
        
        # Extract overlap content
        overlap_content = text[overlap_start_char:current_chunk.start_char] if overlap_start_char < current_chunk.start_char else ""
        overlap_chars = len(overlap_content)
        
        return overlap_start_char if overlap_content else None, overlap_content, overlap_chars
    
    def _calculate_forward_overlap(self, current_chunk: DocumentChunk, next_chunk: DocumentChunk,
                                 text: str, sentence_boundaries: List[Tuple[int, int]]) -> Tuple[Optional[int], str, int]:
        """Calculate overlap with next chunk"""
        # Calculate desired overlap size based on configurable percentage
        base_overlap_size = int(len(current_chunk.content) * self.overlap_percentage)
        overlap_size = max(
            self.min_overlap_chars,
            min(self.max_overlap_chars, base_overlap_size)
        )
        
        # Find optimal overlap end position
        target_end = min(len(text), current_chunk.end_char + overlap_size)
        
        # Adjust to sentence boundary for better coherence
        overlap_end_char = self._find_optimal_sentence_boundary(
            target_end, sentence_boundaries, direction='end'
        )
        
        # Ensure overlap doesn't go beyond next chunk's end
        if overlap_end_char > next_chunk.end_char:
            overlap_end_char = next_chunk.end_char
        
        # Ensure overlap doesn't go before current chunk's end
        if overlap_end_char <= current_chunk.end_char:
            overlap_end_char = min(len(text), current_chunk.end_char + self.min_overlap_chars)
        
        # Extract overlap content
        overlap_content = text[current_chunk.end_char:overlap_end_char] if overlap_end_char > current_chunk.end_char else ""
        overlap_chars = len(overlap_content)
        
        return overlap_end_char if overlap_content else None, overlap_content, overlap_chars
    
    def _find_optimal_sentence_boundary(self, target_pos: int, sentence_boundaries: List[Tuple[int, int]], 
                                      direction: str = 'start') -> int:
        """Find optimal sentence boundary near target position"""
        if not sentence_boundaries:
            return target_pos
        
        best_pos = target_pos
        min_distance = float('inf')
        
        for start_char, end_char in sentence_boundaries:
            if direction == 'start':
                # Look for sentence starts
                distance = abs(start_char - target_pos)
                if distance < min_distance:
                    min_distance = distance
                    best_pos = start_char
            else:
                # Look for sentence ends
                distance = abs(end_char - target_pos)
                if distance < min_distance:
                    min_distance = distance
                    best_pos = end_char
        
        return best_pos
    
    def get_overlap_content(self, chunk: DocumentChunk, text: str) -> Dict[str, str]:
        """
        Get overlap content for a chunk
        
        Returns:
            Dict with 'before' and 'after' overlap content
        """
        overlap_content = {'before': '', 'after': ''}
        
        if chunk.overlap_start is not None:
            overlap_content['before'] = text[chunk.overlap_start:chunk.start_char]
        
        if chunk.overlap_end is not None:
            overlap_content['after'] = text[chunk.end_char:chunk.overlap_end]
        
        return overlap_content
    
    def get_chunk_relationships(self, chunk_id: str) -> Dict[str, Any]:
        """
        Get detailed relationship information for a specific chunk
        
        Args:
            chunk_id: ID of the chunk to get relationships for
            
        Returns:
            Dict containing relationship information
        """
        if chunk_id not in self.chunk_relationships:
            return {
                'overlaps_with': [],
                'overlapped_by': [],
                'adjacent_chunks': [],
                'overlap_metrics': {
                    'backward_overlap_chars': 0,
                    'forward_overlap_chars': 0,
                    'overlap_percentage_actual': 0.0
                }
            }
        
        return self.chunk_relationships[chunk_id].copy()
    
    def validate_overlap_configuration(self) -> Dict[str, Any]:
        """
        Validate the current overlap configuration
        
        Returns:
            Dict with validation results and recommendations
        """
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'recommendations': []
        }
        
        # Check overlap percentage
        if self.overlap_percentage <= 0:
            validation_result['warnings'].append("Overlap percentage is 0 or negative - no overlap will be applied")
        elif self.overlap_percentage > 0.5:
            validation_result['warnings'].append("Overlap percentage is very high (>50%) - may cause excessive redundancy")
            validation_result['recommendations'].append("Consider reducing overlap percentage to 0.1-0.3 range")
        
        # Check overlap bounds
        if self.min_overlap_chars > self.max_overlap_chars:
            validation_result['is_valid'] = False
            validation_result['warnings'].append("Minimum overlap chars is greater than maximum overlap chars")
        
        if self.min_overlap_chars < 10:
            validation_result['recommendations'].append("Consider increasing minimum overlap to at least 10 characters for meaningful context")
        
        if self.max_overlap_chars > 1000:
            validation_result['recommendations'].append("Consider reducing maximum overlap to avoid excessive memory usage")
        
        return validation_result
    
    def get_overlap_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about overlap usage across all managed chunks
        
        Returns:
            Dict with overlap statistics
        """
        if not self.chunk_relationships:
            return {
                'total_chunks': 0,
                'chunks_with_overlap': 0,
                'average_overlap_percentage': 0.0,
                'overlap_distribution': {}
            }
        
        total_chunks = len(self.chunk_relationships)
        chunks_with_overlap = 0
        total_overlap_percentage = 0.0
        overlap_ranges = {'0-5%': 0, '5-15%': 0, '15-30%': 0, '30%+': 0}
        
        for chunk_id, relationships in self.chunk_relationships.items():
            overlap_metrics = relationships.get('overlap_metrics', {})
            actual_percentage = overlap_metrics.get('overlap_percentage_actual', 0.0)
            
            if actual_percentage > 0:
                chunks_with_overlap += 1
                total_overlap_percentage += actual_percentage
                
                # Categorize overlap percentage
                if actual_percentage < 0.05:
                    overlap_ranges['0-5%'] += 1
                elif actual_percentage < 0.15:
                    overlap_ranges['5-15%'] += 1
                elif actual_percentage < 0.30:
                    overlap_ranges['15-30%'] += 1
                else:
                    overlap_ranges['30%+'] += 1
        
        average_overlap = total_overlap_percentage / chunks_with_overlap if chunks_with_overlap > 0 else 0.0
        
        return {
            'total_chunks': total_chunks,
            'chunks_with_overlap': chunks_with_overlap,
            'average_overlap_percentage': average_overlap,
            'overlap_distribution': overlap_ranges
        }

class HierarchicalChunker:
    """Enhanced hierarchical chunking implementation with configurable overlap and relationship tracking"""
    
    def __init__(self, 
                 base_chunk_size: int = 512,
                 overlap_percentage: float = 0.1,
                 max_levels: int = 3,
                 min_overlap_chars: int = 50,
                 max_overlap_chars: int = 500,
                 level_size_multipliers: Optional[List[float]] = None):
        """
        Initialize hierarchical chunker with enhanced configuration
        
        Args:
            base_chunk_size: Base size for chunks in tokens/words
            overlap_percentage: Percentage overlap between chunks (0.0 to 0.5)
            max_levels: Maximum hierarchy levels
            min_overlap_chars: Minimum overlap in characters
            max_overlap_chars: Maximum overlap in characters
            level_size_multipliers: Size multipliers for each level (default: [1.0, 2.0, 4.0])
        """
        self.base_chunk_size = base_chunk_size
        self.overlap_percentage = max(0.0, min(overlap_percentage, 0.5))  # Ensure valid range
        self.max_levels = max(1, max_levels)  # Ensure at least 1 level
        self.min_overlap_chars = max(0, min_overlap_chars)
        self.max_overlap_chars = max(min_overlap_chars, max_overlap_chars)
        
        # Default size multipliers for hierarchical levels
        self.level_size_multipliers = level_size_multipliers or [1.0, 2.0, 4.0]
        
        self.sentence_processor = SentenceAwareProcessor()
        self.overlap_manager = OverlapManager(
            overlap_percentage=self.overlap_percentage,
            min_overlap_chars=self.min_overlap_chars,
            max_overlap_chars=self.max_overlap_chars
        )
        
        # Track parent-child relationships with enhanced structure
        self.chunk_hierarchy = {}
        self.parent_child_map = {}
        self.level_statistics = {}  # Track statistics per level
    
    def update_overlap_configuration(self, 
                                   overlap_percentage: Optional[float] = None,
                                   min_overlap_chars: Optional[int] = None,
                                   max_overlap_chars: Optional[int] = None) -> Dict[str, Any]:
        """
        Update overlap configuration dynamically
        
        Args:
            overlap_percentage: New overlap percentage (0.0 to 0.5)
            min_overlap_chars: New minimum overlap in characters
            max_overlap_chars: New maximum overlap in characters
            
        Returns:
            Dict with update results and validation
        """
        old_config = {
            'overlap_percentage': self.overlap_percentage,
            'min_overlap_chars': self.min_overlap_chars,
            'max_overlap_chars': self.max_overlap_chars
        }
        
        # Update values if provided
        if overlap_percentage is not None:
            self.overlap_percentage = max(0.0, min(overlap_percentage, 0.5))
        
        if min_overlap_chars is not None:
            self.min_overlap_chars = max(0, min_overlap_chars)
        
        if max_overlap_chars is not None:
            self.max_overlap_chars = max(self.min_overlap_chars, max_overlap_chars)
        
        # Update overlap manager with new configuration
        self.overlap_manager.overlap_percentage = self.overlap_percentage
        self.overlap_manager.min_overlap_chars = self.min_overlap_chars
        self.overlap_manager.max_overlap_chars = self.max_overlap_chars
        
        # Validate new configuration
        validation = self.overlap_manager.validate_overlap_configuration()
        
        new_config = {
            'overlap_percentage': self.overlap_percentage,
            'min_overlap_chars': self.min_overlap_chars,
            'max_overlap_chars': self.max_overlap_chars
        }
        
        return {
            'old_config': old_config,
            'new_config': new_config,
            'validation': validation,
            'changes_applied': old_config != new_config
        }
    
    def chunk_document(self, text: str, strategy: ChunkingStrategy = ChunkingStrategy.HIERARCHICAL) -> List[DocumentChunk]:
        """
        Main entry point for document chunking
        
        Args:
            text: Input text to chunk
            strategy: Chunking strategy to use
            
        Returns:
            List of DocumentChunk objects
        """
        if strategy == ChunkingStrategy.SENTENCE_AWARE:
            return self._chunk_sentence_aware(text)
        elif strategy == ChunkingStrategy.HIERARCHICAL:
            return self._chunk_hierarchical(text)
        elif strategy == ChunkingStrategy.ADAPTIVE:
            return self._chunk_adaptive(text)
        else:
            return self._chunk_fixed_size(text)
    
    def _chunk_sentence_aware(self, text: str) -> List[DocumentChunk]:
        """Create chunks with sentence boundary awareness"""
        sentences = self.sentence_processor.extract_sentences(text)
        sentence_boundaries = self.sentence_processor.detect_sentence_boundaries(text)
        
        chunks = []
        current_chunk_sentences = []
        current_word_count = 0
        chunk_index = 0
        
        for i, sentence in enumerate(sentences):
            sentence_words = len(word_tokenize(sentence))
            
            # Check if adding this sentence would exceed chunk size
            if current_word_count + sentence_words > self.base_chunk_size and current_chunk_sentences:
                # Create chunk from current sentences
                chunk_content = ' '.join(current_chunk_sentences)
                start_sentence_idx = i - len(current_chunk_sentences)
                
                # Get character boundaries
                start_char = sentence_boundaries[start_sentence_idx][0] if start_sentence_idx < len(sentence_boundaries) else 0
                end_char = sentence_boundaries[i-1][1] if i-1 < len(sentence_boundaries) else len(chunk_content)
                
                chunk = DocumentChunk(
                    content=chunk_content,
                    chunk_index=chunk_index,
                    chunk_level=0,
                    start_char=start_char,
                    end_char=end_char,
                    start_sentence=start_sentence_idx,
                    end_sentence=i-1,
                    sentence_boundaries=list(range(start_sentence_idx, i)),
                    metadata={
                        'word_count': current_word_count,
                        'sentence_count': len(current_chunk_sentences),
                        'strategy': 'sentence_aware'
                    }
                )
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk_sentences = [sentence]
                current_word_count = sentence_words
                chunk_index += 1
            else:
                current_chunk_sentences.append(sentence)
                current_word_count += sentence_words
        
        # Add final chunk
        if current_chunk_sentences:
            chunk_content = ' '.join(current_chunk_sentences)
            start_sentence_idx = len(sentences) - len(current_chunk_sentences)
            
            start_char = sentence_boundaries[start_sentence_idx][0] if start_sentence_idx < len(sentence_boundaries) else 0
            end_char = len(text)
            
            chunk = DocumentChunk(
                content=chunk_content,
                chunk_index=chunk_index,
                chunk_level=0,
                start_char=start_char,
                end_char=end_char,
                start_sentence=start_sentence_idx,
                end_sentence=len(sentences)-1,
                sentence_boundaries=list(range(start_sentence_idx, len(sentences))),
                metadata={
                    'word_count': current_word_count,
                    'sentence_count': len(current_chunk_sentences),
                    'strategy': 'sentence_aware'
                }
            )
            chunks.append(chunk)
        
        # Apply overlap management
        chunks = self.overlap_manager.calculate_overlap_boundaries(chunks, text, self.sentence_processor)
        
        return chunks
    
    def _chunk_hierarchical(self, text: str) -> List[DocumentChunk]:
        """Create hierarchical chunks with multiple levels"""
        all_chunks = []
        
        # Level 0: Base sentence-aware chunks
        base_chunks = self._chunk_sentence_aware(text)
        all_chunks.extend(base_chunks)
        
        # Level 1: Combine adjacent base chunks
        if len(base_chunks) > 1 and self.max_levels > 1:
            level1_chunks = self._create_parent_chunks(base_chunks, text, level=1)
            all_chunks.extend(level1_chunks)
        
        # Level 2: Combine level 1 chunks if needed
        if len(all_chunks) > 4 and self.max_levels > 2:
            level1_only = [c for c in all_chunks if c.chunk_level == 1]
            if len(level1_only) > 1:
                level2_chunks = self._create_parent_chunks(level1_only, text, level=2)
                all_chunks.extend(level2_chunks)
        
        return all_chunks
    
    def _create_parent_chunks(self, child_chunks: List[DocumentChunk], text: str, level: int) -> List[DocumentChunk]:
        """Enhanced parent chunk creation with improved relationship tracking"""
        parent_chunks = []
        chunk_index = 0
        
        # Determine group size based on level and configuration
        if level < len(self.level_size_multipliers):
            multiplier = self.level_size_multipliers[level]
            group_size = max(2, int(2 * multiplier))
        else:
            group_size = 2 if level == 1 else 3
        
        for i in range(0, len(child_chunks), group_size):
            group = child_chunks[i:i + group_size]
            parent_chunk_id = f"level_{level}_{chunk_index}"
            
            # Combine content with overlap consideration
            combined_content = self._combine_chunk_content_with_overlap(group, text)
            
            # Calculate boundaries
            start_char = group[0].start_char
            end_char = group[-1].end_char
            start_sentence = group[0].start_sentence
            end_sentence = group[-1].end_sentence
            
            # Combine sentence boundaries
            sentence_boundaries = []
            for chunk in group:
                sentence_boundaries.extend(chunk.sentence_boundaries)
            sentence_boundaries = sorted(list(set(sentence_boundaries)))
            
            parent_chunk = DocumentChunk(
                content=combined_content,
                chunk_index=chunk_index,
                chunk_level=level,
                start_char=start_char,
                end_char=end_char,
                start_sentence=start_sentence,
                end_sentence=end_sentence,
                sentence_boundaries=sentence_boundaries,
                metadata={
                    'child_chunks': [f"level_{chunk.chunk_level}_{chunk.chunk_index}" for chunk in group],
                    'child_chunk_indices': [chunk.chunk_index for chunk in group],
                    'word_count': sum(len(word_tokenize(chunk.content)) for chunk in group),
                    'sentence_count': len(sentence_boundaries),
                    'strategy': 'hierarchical',
                    'level': level,
                    'group_size': len(group)
                }
            )
            
            # Enhanced parent-child relationship tracking
            self._establish_parent_child_relationships(parent_chunk_id, group)
            
            # Set parent reference in child chunks
            for child in group:
                child.parent_chunk_id = parent_chunk_id
                child.metadata['parent_level'] = level
                child.metadata['parent_index'] = chunk_index
            
            parent_chunks.append(parent_chunk)
            chunk_index += 1
        
        return parent_chunks
    
    def _combine_chunk_content_with_overlap(self, chunks: List[DocumentChunk], text: str) -> str:
        """Combine chunk content while handling overlaps intelligently"""
        if not chunks:
            return ""
        
        if len(chunks) == 1:
            return chunks[0].content
        
        combined_parts = []
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                # First chunk: use full content
                combined_parts.append(chunk.content)
            else:
                # Subsequent chunks: handle overlap with previous chunk
                prev_chunk = chunks[i - 1]
                
                # Check if there's overlap content to avoid duplication
                if (hasattr(chunk, 'overlap_start') and chunk.overlap_start is not None and
                    hasattr(prev_chunk, 'overlap_end') and prev_chunk.overlap_end is not None):
                    
                    # Calculate overlap region
                    overlap_start = max(chunk.overlap_start, prev_chunk.end_char)
                    overlap_end = min(chunk.start_char, prev_chunk.overlap_end)
                    
                    if overlap_start < overlap_end:
                        # There's actual overlap, skip the overlapping part in current chunk
                        overlap_length = overlap_end - overlap_start
                        chunk_content = chunk.content[overlap_length:] if overlap_length < len(chunk.content) else chunk.content
                    else:
                        chunk_content = chunk.content
                else:
                    chunk_content = chunk.content
                
                combined_parts.append(chunk_content)
        
        return ' '.join(combined_parts)
    
    def _establish_parent_child_relationships(self, parent_id: str, child_chunks: List[DocumentChunk]):
        """Enhanced parent-child relationship establishment with detailed tracking"""
        # Extract level from parent_id
        parent_level = int(parent_id.split('_')[1])
        
        if parent_id not in self.chunk_hierarchy:
            self.chunk_hierarchy[parent_id] = {
                'children': [],
                'level': parent_level,
                'parent': None,
                'metadata': {
                    'child_count': 0,
                    'total_content_length': 0,
                    'creation_timestamp': datetime.now().isoformat()
                }
            }
        
        total_content_length = 0
        
        for child in child_chunks:
            child_id = f"level_{child.chunk_level}_{child.chunk_index}"
            
            # Add child to parent's children list
            self.chunk_hierarchy[parent_id]['children'].append(child_id)
            total_content_length += len(child.content)
            
            # Create child entry if it doesn't exist
            if child_id not in self.chunk_hierarchy:
                self.chunk_hierarchy[child_id] = {
                    'children': [],
                    'level': child.chunk_level,
                    'parent': parent_id,
                    'metadata': {
                        'content_length': len(child.content),
                        'sentence_count': len(child.sentence_boundaries) if child.sentence_boundaries else 0,
                        'has_overlap': hasattr(child, 'overlap_start') or hasattr(child, 'overlap_end')
                    }
                }
            else:
                self.chunk_hierarchy[child_id]['parent'] = parent_id
                self.chunk_hierarchy[child_id]['metadata'] = {
                    'content_length': len(child.content),
                    'sentence_count': len(child.sentence_boundaries) if child.sentence_boundaries else 0,
                    'has_overlap': hasattr(child, 'overlap_start') or hasattr(child, 'overlap_end')
                }
            
            # Update parent-child mapping
            self.parent_child_map[child_id] = parent_id
        
        # Update parent metadata
        self.chunk_hierarchy[parent_id]['metadata']['child_count'] = len(child_chunks)
        self.chunk_hierarchy[parent_id]['metadata']['total_content_length'] = total_content_length
        
        # Update level statistics
        if parent_level not in self.level_statistics:
            self.level_statistics[parent_level] = {
                'chunk_count': 0,
                'total_children': 0,
                'avg_children_per_chunk': 0.0
            }
        
        self.level_statistics[parent_level]['chunk_count'] += 1
        self.level_statistics[parent_level]['total_children'] += len(child_chunks)
        self.level_statistics[parent_level]['avg_children_per_chunk'] = (
            self.level_statistics[parent_level]['total_children'] / 
            self.level_statistics[parent_level]['chunk_count']
        )
    
    def get_chunk_relationships(self, chunk_id: str) -> Dict[str, Any]:
        """Get relationship information for a specific chunk"""
        if chunk_id not in self.chunk_hierarchy:
            return {}
        
        relationships = self.chunk_hierarchy[chunk_id].copy()
        
        # Add sibling information
        parent_id = relationships.get('parent')
        if parent_id and parent_id in self.chunk_hierarchy:
            siblings = [child for child in self.chunk_hierarchy[parent_id]['children'] if child != chunk_id]
            relationships['siblings'] = siblings
        else:
            relationships['siblings'] = []
        
        # Add descendant information
        relationships['descendants'] = self._get_all_descendants(chunk_id)
        
        return relationships
    
    def _get_all_descendants(self, chunk_id: str) -> List[str]:
        """Get all descendants of a chunk (children, grandchildren, etc.)"""
        descendants = []
        
        if chunk_id in self.chunk_hierarchy:
            children = self.chunk_hierarchy[chunk_id]['children']
            descendants.extend(children)
            
            # Recursively get descendants of children
            for child_id in children:
                descendants.extend(self._get_all_descendants(child_id))
        
        return descendants
    

    
    def get_chunk_hierarchy(self, chunk_id: str) -> Dict[str, Any]:
        """Get hierarchy information for a specific chunk"""
        return self.get_chunk_relationships(chunk_id)
    
    def get_contextual_chunks(self, chunk_id: str, context_window: int = 2) -> List[str]:
        """
        Get contextual chunks around a specific chunk
        
        Args:
            chunk_id: ID of the target chunk
            context_window: Number of chunks to include on each side
            
        Returns:
            List of chunk IDs in the contextual window
        """
        contextual_chunk_ids = []
        
        if chunk_id not in self.chunk_hierarchy:
            return contextual_chunk_ids
        
        # Get chunk information
        chunk_info = self.chunk_hierarchy[chunk_id]
        chunk_level = chunk_info.get('level', 0)
        
        # Find all chunks at the same level
        same_level_chunks = []
        for cid, info in self.chunk_hierarchy.items():
            if info.get('level') == chunk_level:
                same_level_chunks.append(cid)
        
        # Sort chunks by their index (assuming chunk IDs follow pattern level_X_Y)
        try:
            same_level_chunks.sort(key=lambda x: int(x.split('_')[-1]))
        except (ValueError, IndexError):
            # Fallback: use original order
            pass
        
        # Find the target chunk position
        try:
            target_index = same_level_chunks.index(chunk_id)
        except ValueError:
            return contextual_chunk_ids
        
        # Get contextual window
        start_index = max(0, target_index - context_window)
        end_index = min(len(same_level_chunks), target_index + context_window + 1)
        
        contextual_chunk_ids = same_level_chunks[start_index:end_index]
        
        # Also include parent and children if available
        parent_id = chunk_info.get('parent')
        if parent_id:
            contextual_chunk_ids.append(parent_id)
        
        children = chunk_info.get('children', [])
        contextual_chunk_ids.extend(children)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_contextual_chunks = []
        for cid in contextual_chunk_ids:
            if cid not in seen:
                seen.add(cid)
                unique_contextual_chunks.append(cid)
        
        return unique_contextual_chunks
    
    def _chunk_adaptive(self, text: str) -> List[DocumentChunk]:
        """Adaptive chunking that chooses strategy based on text characteristics"""
        # Analyze text characteristics
        sentences = self.sentence_processor.extract_sentences(text)
        avg_sentence_length = sum(len(word_tokenize(s)) for s in sentences) / len(sentences) if sentences else 0
        
        # Choose strategy based on text characteristics
        if len(sentences) < 5:
            # Short text: use sentence-aware
            return self._chunk_sentence_aware(text)
        elif avg_sentence_length > 30:
            # Long sentences: use hierarchical
            return self._chunk_hierarchical(text)
        else:
            # Medium text: use sentence-aware with larger chunks
            return self._chunk_sentence_aware(text)
    
    def _chunk_fixed_size(self, text: str) -> List[DocumentChunk]:
        """Fixed-size chunking as fallback"""
        words = word_tokenize(text)
        chunks = []
        chunk_index = 0
        
        for i in range(0, len(words), self.base_chunk_size):
            chunk_words = words[i:i + self.base_chunk_size]
            chunk_content = ' '.join(chunk_words)
            
            # Estimate character positions (rough approximation)
            start_char = i * 6  # Rough estimate: 6 chars per word on average
            end_char = start_char + len(chunk_content)
            
            chunk = DocumentChunk(
                content=chunk_content,
                chunk_index=chunk_index,
                chunk_level=0,
                start_char=start_char,
                end_char=end_char,
                metadata={
                    'word_count': len(chunk_words),
                    'strategy': 'fixed_size'
                }
            )
            chunks.append(chunk)
            chunk_index += 1
        
        return chunks
    
    def get_chunk_hierarchy(self, chunk_id: str) -> Dict[str, Any]:
        """Get complete hierarchy information for a chunk"""
        return self.get_chunk_relationships(chunk_id)
    
    def get_hierarchy_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the chunk hierarchy
        
        Returns:
            Dict with hierarchy statistics
        """
        total_chunks = len(self.chunk_hierarchy)
        levels = set()
        parent_count = 0
        leaf_count = 0
        
        for chunk_id, chunk_info in self.chunk_hierarchy.items():
            levels.add(chunk_info['level'])
            
            if chunk_info['children']:
                parent_count += 1
            else:
                leaf_count += 1
        
        return {
            'total_chunks': total_chunks,
            'total_levels': len(levels),
            'levels_present': sorted(list(levels)),
            'parent_chunks': parent_count,
            'leaf_chunks': leaf_count,
            'level_statistics': self.level_statistics.copy(),
            'overlap_statistics': self.overlap_manager.get_overlap_statistics()
        }
    
    def validate_hierarchy_integrity(self) -> Dict[str, Any]:
        """
        Validate the integrity of the chunk hierarchy
        
        Returns:
            Dict with validation results
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'orphaned_chunks': [],
            'circular_references': []
        }
        
        # Check for orphaned chunks (children without valid parents)
        for chunk_id, chunk_info in self.chunk_hierarchy.items():
            parent_id = chunk_info.get('parent')
            if parent_id and parent_id not in self.chunk_hierarchy:
                validation_result['orphaned_chunks'].append(chunk_id)
                validation_result['errors'].append(f"Chunk {chunk_id} references non-existent parent {parent_id}")
        
        # Check for circular references
        visited = set()
        for chunk_id in self.chunk_hierarchy:
            if chunk_id not in visited:
                path = []
                current = chunk_id
                
                while current and current not in visited:
                    if current in path:
                        # Circular reference detected
                        cycle_start = path.index(current)
                        cycle = path[cycle_start:] + [current]
                        validation_result['circular_references'].append(cycle)
                        validation_result['errors'].append(f"Circular reference detected: {' -> '.join(cycle)}")
                        break
                    
                    path.append(current)
                    current = self.chunk_hierarchy.get(current, {}).get('parent')
                
                visited.update(path)
        
        # Check parent-child consistency
        for parent_id, parent_info in self.chunk_hierarchy.items():
            for child_id in parent_info.get('children', []):
                if child_id not in self.chunk_hierarchy:
                    validation_result['errors'].append(f"Parent {parent_id} references non-existent child {child_id}")
                elif self.chunk_hierarchy[child_id].get('parent') != parent_id:
                    validation_result['warnings'].append(f"Inconsistent parent-child relationship: {parent_id} <-> {child_id}")
        
        validation_result['is_valid'] = len(validation_result['errors']) == 0
        
        return validation_result
    
    def get_contextual_chunks(self, chunk_id: str, context_window: int = 2) -> List[DocumentChunk]:
        """Get chunks within a context window of the specified chunk"""
        # This would need access to the stored chunks to implement properly
        # For now, return relationship information
        relationships = self.get_chunk_relationships(chunk_id)
        contextual_chunk_ids = []
        
        # Add siblings
        contextual_chunk_ids.extend(relationships.get('siblings', []))
        
        # Add parent
        if relationships.get('parent'):
            contextual_chunk_ids.append(relationships['parent'])
        
        # Add children
        contextual_chunk_ids.extend(relationships.get('children', []))
        
        return contextual_chunk_ids  # Return IDs for now




class HierarchicalChunkingService:
    """Main service interface for hierarchical document chunking"""
    
    def __init__(self, 
                 base_chunk_size: int = 512,
                 overlap_percentage: float = 0.1,
                 max_levels: int = 3):
        """Initialize the hierarchical chunking service"""
        self.chunker = HierarchicalChunker(
            base_chunk_size=base_chunk_size,
            overlap_percentage=overlap_percentage,
            max_levels=max_levels
        )
        logger.info(f"Initialized HierarchicalChunkingService with chunk_size={base_chunk_size}, overlap={overlap_percentage}")
    
    async def chunk_document(self, 
                           text: str, 
                           strategy: ChunkingStrategy = ChunkingStrategy.HIERARCHICAL) -> List[DocumentChunk]:
        """
        Chunk a document using the specified strategy
        
        Args:
            text: Input text to chunk
            strategy: Chunking strategy to use
            
        Returns:
            List of DocumentChunk objects
        """
        try:
            chunks = self.chunker.chunk_document(text, strategy)
            logger.info(f"Successfully chunked document into {len(chunks)} chunks using {strategy.value} strategy")
            return chunks
        except Exception as e:
            logger.error(f"Error chunking document: {str(e)}")
            raise
    
    async def get_chunk_hierarchy(self, chunk_id: str) -> Dict[str, Any]:
        """Get hierarchy information for a specific chunk"""
        return self.chunker.get_chunk_hierarchy(chunk_id)
    
    async def get_contextual_chunks(self, 
                                  chunk_id: str, 
                                  context_window: int = 2) -> List[str]:
        """Get contextual chunks around a specific chunk"""
        return self.chunker.get_contextual_chunks(chunk_id, context_window)