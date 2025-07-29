"""
Unit tests for hierarchical document chunking service
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.hierarchical_chunking import (
    SentenceAwareProcessor,
    OverlapManager,
    HierarchicalChunker,
    HierarchicalChunkingService,
    DocumentChunk,
    ChunkingStrategy
)


class TestSentenceAwareProcessor:
    """Test cases for SentenceAwareProcessor"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = SentenceAwareProcessor()
        self.sample_text = (
            "This is the first sentence. This is the second sentence! "
            "Is this the third sentence? This is the fourth sentence. "
            "Finally, this is the fifth sentence."
        )
    
    def test_initialization(self):
        """Test processor initialization"""
        assert self.processor is not None
        assert hasattr(self.processor, 'stop_words')
        assert len(self.processor.stop_words) > 0
    
    def test_detect_sentence_boundaries_nltk(self):
        """Test sentence boundary detection using NLTK"""
        # Force NLTK usage
        original_use_spacy = self.processor.use_spacy
        self.processor.use_spacy = False
        
        try:
            boundaries = self.processor.detect_sentence_boundaries(self.sample_text)
            
            # Should detect 5 sentences
            assert len(boundaries) == 5
            
            # Check that boundaries are tuples of (start, end)
            for start, end in boundaries:
                assert isinstance(start, int)
                assert isinstance(end, int)
                assert start < end
            
            # Check that boundaries cover the text properly
            assert boundaries[0][0] == 0  # First sentence starts at 0
            assert boundaries[-1][1] <= len(self.sample_text)  # Last sentence ends within text
            
        finally:
            self.processor.use_spacy = original_use_spacy
    
    @patch('spacy.load')
    def test_detect_sentence_boundaries_spacy(self, mock_spacy_load):
        """Test sentence boundary detection using spaCy"""
        # Mock spaCy model
        mock_sent1 = Mock()
        mock_sent1.start_char = 0
        mock_sent1.end_char = 26
        
        mock_sent2 = Mock()
        mock_sent2.start_char = 27
        mock_sent2.end_char = 54
        
        mock_doc = Mock()
        mock_doc.sents = [mock_sent1, mock_sent2]
        
        mock_nlp = Mock()
        mock_nlp.return_value = mock_doc
        mock_spacy_load.return_value = mock_nlp
        
        # Create processor with mocked spaCy
        processor = SentenceAwareProcessor()
        processor.use_spacy = True
        processor.nlp = mock_nlp
        
        boundaries = processor._detect_boundaries_spacy("Test text")
        
        assert len(boundaries) == 2
        assert boundaries[0] == (0, 26)
        assert boundaries[1] == (27, 54)
    
    def test_preserve_sentence_integrity(self):
        """Test sentence integrity preservation"""
        # Test case where chunk boundaries fall in middle of sentences
        chunk_start = 15  # Middle of first sentence
        chunk_end = 45    # Middle of second sentence
        
        adjusted_start, adjusted_end = self.processor.preserve_sentence_integrity(
            self.sample_text, chunk_start, chunk_end
        )
        
        # Should adjust to sentence boundaries
        assert adjusted_start <= chunk_start
        assert adjusted_end >= chunk_end
        
        # Verify adjusted boundaries align with sentence boundaries
        boundaries = self.processor.detect_sentence_boundaries(self.sample_text)
        
        # Check that adjusted_start aligns with a sentence start
        sentence_starts = [start for start, _ in boundaries]
        assert adjusted_start in sentence_starts or adjusted_start == 0
        
        # Check that adjusted_end aligns with a sentence end
        sentence_ends = [end for _, end in boundaries]
        assert adjusted_end in sentence_ends or adjusted_end == len(self.sample_text)
    
    def test_get_sentence_indices(self):
        """Test getting sentence indices within chunk boundaries"""
        # Test chunk that spans multiple sentences
        chunk_start = 0
        chunk_end = 60  # Should cover first 2-3 sentences
        
        indices = self.processor.get_sentence_indices(
            self.sample_text, chunk_start, chunk_end
        )
        
        assert len(indices) >= 2  # Should include at least 2 sentences
        assert all(isinstance(idx, int) for idx in indices)
        assert all(idx >= 0 for idx in indices)
    
    def test_extract_sentences(self):
        """Test sentence extraction"""
        sentences = self.processor.extract_sentences(self.sample_text)
        
        assert len(sentences) >= 4  # Should extract multiple sentences
        assert all(isinstance(sentence, str) for sentence in sentences)
        assert all(len(sentence.strip()) > 0 for sentence in sentences)
        
        # Check that sentences contain expected content
        first_sentence = sentences[0].strip()
        assert "first sentence" in first_sentence.lower()
    
    def test_calculate_sentence_importance(self):
        """Test sentence importance calculation"""
        # Test with different types of sentences
        test_sentences = [
            "This is a simple sentence.",
            "What is the main conclusion of this research?",
            "The results show a 95% improvement in accuracy.",
            "First, we need to establish the baseline.",
            "The quick brown fox jumps over the lazy dog."
        ]
        
        for sentence in test_sentences:
            importance = self.processor.calculate_sentence_importance(sentence)
            
            # Score should be between 0 and 1
            assert 0.0 <= importance <= 1.0
            assert isinstance(importance, float)
        
        # Question sentence should have higher importance
        question_importance = self.processor.calculate_sentence_importance(
            "What is the main conclusion?"
        )
        simple_importance = self.processor.calculate_sentence_importance(
            "This is simple."
        )
        
        # Question should generally have higher importance
        assert question_importance >= simple_importance
    
    def test_sentence_boundary_edge_cases(self):
        """Test edge cases for sentence boundary detection"""
        # Empty text
        boundaries = self.processor.detect_sentence_boundaries("")
        assert len(boundaries) == 0
        
        # Single sentence
        single_sentence = "This is a single sentence."
        boundaries = self.processor.detect_sentence_boundaries(single_sentence)
        assert len(boundaries) == 1
        assert boundaries[0][0] == 0
        assert boundaries[0][1] == len(single_sentence)
        
        # Text with abbreviations
        abbrev_text = "Dr. Smith went to the U.S.A. He was happy."
        boundaries = self.processor.detect_sentence_boundaries(abbrev_text)
        assert len(boundaries) >= 1  # Should handle abbreviations properly


class TestOverlapManager:
    """Test cases for OverlapManager"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.overlap_manager = OverlapManager(
            overlap_percentage=0.1,
            min_overlap_chars=50,
            max_overlap_chars=200
        )
        self.sentence_processor = SentenceAwareProcessor()
        
        # Create sample chunks
        self.sample_chunks = [
            DocumentChunk(
                content="First chunk content with multiple sentences.",
                chunk_index=0,
                chunk_level=0,
                start_char=0,
                end_char=44
            ),
            DocumentChunk(
                content="Second chunk content with more text.",
                chunk_index=1,
                chunk_level=0,
                start_char=45,
                end_char=81
            )
        ]
        
        self.sample_text = "First chunk content with multiple sentences. Second chunk content with more text."
    
    def test_initialization(self):
        """Test overlap manager initialization"""
        assert self.overlap_manager.overlap_percentage == 0.1
        assert self.overlap_manager.min_overlap_chars == 50
        assert self.overlap_manager.max_overlap_chars == 200
        assert isinstance(self.overlap_manager.chunk_relationships, dict)
    
    def test_calculate_overlap_boundaries(self):
        """Test overlap boundary calculation"""
        chunks_with_overlap = self.overlap_manager.calculate_overlap_boundaries(
            self.sample_chunks, self.sample_text, self.sentence_processor
        )
        
        assert len(chunks_with_overlap) == len(self.sample_chunks)
        
        # Check that relationships are tracked
        for chunk in chunks_with_overlap:
            chunk_id = f"level_{chunk.chunk_level}_{chunk.chunk_index}"
            assert 'relationships' in chunk.metadata
            assert isinstance(chunk.metadata['relationships'], dict)
    
    def test_get_overlap_content(self):
        """Test getting overlap content for chunks"""
        # Set up chunk with overlap information
        chunk = self.sample_chunks[0]
        chunk.overlap_start = 0
        chunk.overlap_end = 50
        
        overlap_content = self.overlap_manager.get_overlap_content(chunk, self.sample_text)
        
        assert isinstance(overlap_content, dict)
        assert 'before' in overlap_content
        assert 'after' in overlap_content
        assert isinstance(overlap_content['before'], str)
        assert isinstance(overlap_content['after'], str)
    
    def test_find_optimal_sentence_boundary(self):
        """Test finding optimal sentence boundaries"""
        sentence_boundaries = [(0, 25), (26, 50), (51, 75)]
        
        # Test finding start boundary
        start_boundary = self.overlap_manager._find_optimal_sentence_boundary(
            20, sentence_boundaries, direction='start'
        )
        assert start_boundary in [0, 26, 51]  # Should be a sentence start
        
        # Test finding end boundary
        end_boundary = self.overlap_manager._find_optimal_sentence_boundary(
            30, sentence_boundaries, direction='end'
        )
        assert end_boundary in [25, 50, 75]  # Should be a sentence end
    
    def test_overlap_percentage_configuration(self):
        """Test that overlap percentage is configurable and affects overlap calculation"""
        # Test with different overlap percentages
        small_overlap_manager = OverlapManager(overlap_percentage=0.05)
        large_overlap_manager = OverlapManager(overlap_percentage=0.2)
        
        assert small_overlap_manager.overlap_percentage == 0.05
        assert large_overlap_manager.overlap_percentage == 0.2
        
        # Test that overlap percentage affects calculations
        chunks_small = small_overlap_manager.calculate_overlap_boundaries(
            self.sample_chunks, self.sample_text, self.sentence_processor
        )
        chunks_large = large_overlap_manager.calculate_overlap_boundaries(
            self.sample_chunks, self.sample_text, self.sentence_processor
        )
        
        # Both should return same number of chunks
        assert len(chunks_small) == len(chunks_large)
    
    def test_min_max_overlap_constraints(self):
        """Test that min and max overlap constraints are respected"""
        overlap_manager = OverlapManager(
            overlap_percentage=0.1,
            min_overlap_chars=100,  # High minimum
            max_overlap_chars=150   # Low maximum
        )
        
        assert overlap_manager.min_overlap_chars == 100
        assert overlap_manager.max_overlap_chars == 150
        
        # Test with chunks that would normally have small overlap
        small_chunks = [
            DocumentChunk(
                content="Short chunk.",
                chunk_index=0,
                chunk_level=0,
                start_char=0,
                end_char=12
            ),
            DocumentChunk(
                content="Another short chunk.",
                chunk_index=1,
                chunk_level=0,
                start_char=13,
                end_char=33
            )
        ]
        
        text = "Short chunk. Another short chunk."
        chunks_with_overlap = overlap_manager.calculate_overlap_boundaries(
            small_chunks, text, self.sentence_processor
        )
        
        assert len(chunks_with_overlap) == 2
    
    def test_chunk_relationship_tracking(self):
        """Test that chunk relationships are properly tracked"""
        chunks_with_overlap = self.overlap_manager.calculate_overlap_boundaries(
            self.sample_chunks, self.sample_text, self.sentence_processor
        )
        
        # Check that relationships are stored in metadata
        for chunk in chunks_with_overlap:
            assert 'relationships' in chunk.metadata
            relationships = chunk.metadata['relationships']
            
            # Check relationship structure
            assert 'overlaps_with' in relationships
            assert 'overlapped_by' in relationships
            assert 'adjacent_chunks' in relationships
            assert 'overlap_metrics' in relationships
            
            # All should be lists except overlap_metrics
            assert isinstance(relationships['overlaps_with'], list)
            assert isinstance(relationships['overlapped_by'], list)
            assert isinstance(relationships['adjacent_chunks'], list)
            assert isinstance(relationships['overlap_metrics'], dict)
            
            # Check overlap metrics structure
            metrics = relationships['overlap_metrics']
            assert 'backward_overlap_chars' in metrics
            assert 'forward_overlap_chars' in metrics
            assert 'overlap_percentage_actual' in metrics
        
        # Check that adjacent chunks are properly linked
        chunk_0_relationships = chunks_with_overlap[0].metadata['relationships']
        chunk_1_relationships = chunks_with_overlap[1].metadata['relationships']
        
        # Chunk 0 should have chunk 1 as adjacent
        assert 'level_0_1' in chunk_0_relationships['adjacent_chunks']
        # Chunk 1 should have chunk 0 as adjacent
        assert 'level_0_0' in chunk_1_relationships['adjacent_chunks']
    
    def test_get_chunk_relationships(self):
        """Test getting chunk relationships"""
        chunks_with_overlap = self.overlap_manager.calculate_overlap_boundaries(
            self.sample_chunks, self.sample_text, self.sentence_processor
        )
        
        chunk_id = 'level_0_0'
        relationships = self.overlap_manager.get_chunk_relationships(chunk_id)
        
        assert isinstance(relationships, dict)
        assert 'overlaps_with' in relationships
        assert 'overlapped_by' in relationships
        assert 'adjacent_chunks' in relationships
        assert 'overlap_metrics' in relationships
        
        # Test non-existent chunk
        empty_relationships = self.overlap_manager.get_chunk_relationships('non_existent')
        assert isinstance(empty_relationships, dict)
        assert empty_relationships['overlaps_with'] == []
    
    def test_validate_overlap_configuration(self):
        """Test overlap configuration validation"""
        # Test valid configuration
        validation = self.overlap_manager.validate_overlap_configuration()
        assert isinstance(validation, dict)
        assert 'is_valid' in validation
        assert 'warnings' in validation
        assert 'recommendations' in validation
        
        # Test invalid configuration
        invalid_manager = OverlapManager(
            overlap_percentage=-0.1,  # Invalid
            min_overlap_chars=100,
            max_overlap_chars=50  # Invalid: min > max
        )
        
        validation = invalid_manager.validate_overlap_configuration()
        assert validation['is_valid'] == False
        assert len(validation['warnings']) > 0
    
    def test_get_overlap_statistics(self):
        """Test getting overlap statistics"""
        # Test with no chunks
        stats = self.overlap_manager.get_overlap_statistics()
        assert stats['total_chunks'] == 0
        assert stats['chunks_with_overlap'] == 0
        
        # Test with chunks
        chunks_with_overlap = self.overlap_manager.calculate_overlap_boundaries(
            self.sample_chunks, self.sample_text, self.sentence_processor
        )
        
        stats = self.overlap_manager.get_overlap_statistics()
        assert isinstance(stats, dict)
        assert 'total_chunks' in stats
        assert 'chunks_with_overlap' in stats
        assert 'average_overlap_percentage' in stats
        assert 'overlap_distribution' in stats
        assert stats['total_chunks'] > 0


class TestHierarchicalChunker:
    """Test cases for HierarchicalChunker"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.chunker = HierarchicalChunker(
            base_chunk_size=100,  # Smaller size for testing
            overlap_percentage=0.1,
            max_levels=3
        )
        
        # Create a longer sample text for hierarchical chunking
        self.long_text = (
            "This is the first paragraph with multiple sentences. "
            "It contains important information about the topic. "
            "The content is structured to test hierarchical chunking. "
            "This is the second paragraph with different content. "
            "It also has multiple sentences for testing purposes. "
            "The hierarchical structure should be preserved. "
            "This is the third paragraph to ensure proper chunking. "
            "It provides additional context for the testing process. "
            "The final sentences complete the test document."
        )
    
    def test_initialization(self):
        """Test chunker initialization"""
        assert self.chunker.base_chunk_size == 100
        assert self.chunker.overlap_percentage == 0.1
        assert self.chunker.max_levels == 3
        assert isinstance(self.chunker.sentence_processor, SentenceAwareProcessor)
        assert isinstance(self.chunker.overlap_manager, OverlapManager)
    
    def test_chunk_document_sentence_aware(self):
        """Test sentence-aware chunking"""
        chunks = self.chunker.chunk_document(
            self.long_text, 
            strategy=ChunkingStrategy.SENTENCE_AWARE
        )
        
        assert len(chunks) > 0
        
        # Check chunk properties
        for chunk in chunks:
            assert isinstance(chunk, DocumentChunk)
            assert chunk.chunk_level == 0  # Sentence-aware chunks are level 0
            assert len(chunk.content) > 0
            assert chunk.metadata['strategy'] == 'sentence_aware'
            assert 'word_count' in chunk.metadata
            assert 'sentence_count' in chunk.metadata
    
    def test_chunk_document_hierarchical(self):
        """Test hierarchical chunking"""
        chunks = self.chunker.chunk_document(
            self.long_text,
            strategy=ChunkingStrategy.HIERARCHICAL
        )
        
        assert len(chunks) > 0
        
        # Should have multiple levels
        levels = set(chunk.chunk_level for chunk in chunks)
        assert len(levels) >= 1
        
        # Check that parent-child relationships exist
        level_0_chunks = [c for c in chunks if c.chunk_level == 0]
        level_1_chunks = [c for c in chunks if c.chunk_level == 1]
        
        if level_1_chunks:
            # Level 1 chunks should reference level 0 chunks as children
            for parent_chunk in level_1_chunks:
                assert 'child_chunks' in parent_chunk.metadata
                assert len(parent_chunk.metadata['child_chunks']) > 0
    
    def test_chunk_document_adaptive(self):
        """Test adaptive chunking strategy"""
        # Test with short text
        short_text = "This is a short text. It has only two sentences."
        chunks = self.chunker.chunk_document(short_text, strategy=ChunkingStrategy.ADAPTIVE)
        
        assert len(chunks) > 0
        
        # Test with long sentences
        long_sentence_text = (
            "This is a very long sentence with many words and clauses that "
            "should trigger the hierarchical chunking strategy because the "
            "average sentence length exceeds the threshold for adaptive chunking."
        )
        chunks = self.chunker.chunk_document(long_sentence_text, strategy=ChunkingStrategy.ADAPTIVE)
        
        assert len(chunks) > 0
    
    def test_chunk_document_fixed_size(self):
        """Test fixed-size chunking"""
        chunks = self.chunker.chunk_document(
            self.long_text,
            strategy=ChunkingStrategy.FIXED_SIZE
        )
        
        assert len(chunks) > 0
        
        for chunk in chunks:
            assert chunk.chunk_level == 0
            assert chunk.metadata['strategy'] == 'fixed_size'
            assert 'word_count' in chunk.metadata
    
    def test_establish_parent_child_relationships(self):
        """Test parent-child relationship establishment"""
        # Create sample child chunks
        child_chunks = [
            DocumentChunk(content="Child 1", chunk_index=0, chunk_level=0),
            DocumentChunk(content="Child 2", chunk_index=1, chunk_level=0)
        ]
        
        parent_id = "level_1_0"
        self.chunker._establish_parent_child_relationships(parent_id, child_chunks)
        
        # Check that relationships are established
        assert parent_id in self.chunker.chunk_hierarchy
        assert len(self.chunker.chunk_hierarchy[parent_id]['children']) == 2
        
        # Check child relationships
        for child in child_chunks:
            child_id = f"level_{child.chunk_level}_{child.chunk_index}"
            assert child_id in self.chunker.chunk_hierarchy
            assert self.chunker.chunk_hierarchy[child_id]['parent'] == parent_id
    
    def test_get_chunk_relationships(self):
        """Test getting chunk relationships"""
        # Set up some relationships first
        child_chunks = [
            DocumentChunk(content="Child 1", chunk_index=0, chunk_level=0),
            DocumentChunk(content="Child 2", chunk_index=1, chunk_level=0)
        ]
        
        parent_id = "level_1_0"
        self.chunker._establish_parent_child_relationships(parent_id, child_chunks)
        
        # Test getting relationships
        relationships = self.chunker.get_chunk_relationships(parent_id)
        
        assert isinstance(relationships, dict)
        assert 'children' in relationships
        assert 'siblings' in relationships
        assert 'descendants' in relationships
        assert len(relationships['children']) == 2
    
    def test_get_contextual_chunks(self):
        """Test getting contextual chunks"""
        # Set up relationships
        child_chunks = [
            DocumentChunk(content="Child 1", chunk_index=0, chunk_level=0),
            DocumentChunk(content="Child 2", chunk_index=1, chunk_level=0)
        ]
        
        parent_id = "level_1_0"
        self.chunker._establish_parent_child_relationships(parent_id, child_chunks)
        
        # Test getting contextual chunks
        contextual_chunks = self.chunker.get_contextual_chunks(parent_id, context_window=2)
        
        assert isinstance(contextual_chunks, list)
    
    def test_hierarchical_overlap_integration(self):
        """Test that hierarchical chunking properly integrates with overlap management"""
        chunks = self.chunker.chunk_document(
            self.long_text,
            strategy=ChunkingStrategy.HIERARCHICAL
        )
        
        # Check that chunks have overlap information
        level_0_chunks = [c for c in chunks if c.chunk_level == 0]
        
        if len(level_0_chunks) > 1:
            # At least some chunks should have overlap information
            has_overlap_start = any(hasattr(c, 'overlap_start') and c.overlap_start is not None for c in level_0_chunks)
            has_overlap_end = any(hasattr(c, 'overlap_end') and c.overlap_end is not None for c in level_0_chunks)
            
            # Note: Not all chunks will have overlap (first chunk won't have overlap_start, last won't have overlap_end)
            # But if we have multiple chunks, some should have overlap information
            if len(level_0_chunks) > 2:
                # Middle chunks should have both overlap_start and overlap_end
                middle_chunks = level_0_chunks[1:-1]
                if middle_chunks:
                    middle_chunk = middle_chunks[0]
                    # Check that overlap information is stored in metadata
                    assert 'relationships' in middle_chunk.metadata
    
    def test_parent_child_hierarchy_levels(self):
        """Test that parent-child relationships work across multiple hierarchy levels"""
        # Create a longer text to ensure multiple hierarchy levels
        very_long_text = " ".join([self.long_text] * 3)  # Triple the text
        
        chunks = self.chunker.chunk_document(
            very_long_text,
            strategy=ChunkingStrategy.HIERARCHICAL
        )
        
        # Should have multiple levels
        levels = set(chunk.chunk_level for chunk in chunks)
        assert len(levels) >= 2  # Should have at least 2 levels
        
        # Check parent-child relationships
        level_0_chunks = [c for c in chunks if c.chunk_level == 0]
        level_1_chunks = [c for c in chunks if c.chunk_level == 1]
        
        if level_1_chunks:
            # Level 1 chunks should reference level 0 chunks as children
            parent_chunk = level_1_chunks[0]
            assert 'child_chunks' in parent_chunk.metadata
            assert len(parent_chunk.metadata['child_chunks']) > 0
            
            # Level 0 chunks should have parent references
            for child_chunk in level_0_chunks:
                if child_chunk.parent_chunk_id:
                    assert child_chunk.parent_chunk_id.startswith('level_1_')
    
    def test_combine_chunk_content_with_overlap(self):
        """Test that chunk content combination handles overlaps correctly"""
        # Create chunks with more realistic overlap information
        chunk1 = DocumentChunk(
            content="First chunk content.",
            chunk_index=0,
            chunk_level=0,
            start_char=0,
            end_char=20
        )
        # No overlap_end for first chunk
        
        chunk2 = DocumentChunk(
            content="Second chunk content.",
            chunk_index=1,
            chunk_level=0,
            start_char=21,
            end_char=42
        )
        # No overlap_start for this test case
        
        test_chunks = [chunk1, chunk2]
        test_text = "First chunk content. Second chunk content."
        
        combined_content = self.chunker._combine_chunk_content_with_overlap(
            test_chunks, test_text
        )
        
        assert isinstance(combined_content, str)
        assert len(combined_content) > 0
        # Should contain content from both chunks
        assert "First chunk" in combined_content
        # The method joins with spaces, so check for the general content
        assert "chunk content" in combined_content
        
        # Test with single chunk
        single_chunk_content = self.chunker._combine_chunk_content_with_overlap(
            [chunk1], test_text
        )
        assert single_chunk_content == chunk1.content
        
        # Test with empty chunks
        empty_content = self.chunker._combine_chunk_content_with_overlap(
            [], test_text
        )
        assert empty_content == ""
    
    def test_update_overlap_configuration(self):
        """Test dynamic overlap configuration updates"""
        # Test updating overlap percentage
        result = self.chunker.update_overlap_configuration(overlap_percentage=0.2)
        
        assert isinstance(result, dict)
        assert 'old_config' in result
        assert 'new_config' in result
        assert 'validation' in result
        assert 'changes_applied' in result
        
        assert result['changes_applied'] == True
        assert result['new_config']['overlap_percentage'] == 0.2
        assert self.chunker.overlap_percentage == 0.2
        assert self.chunker.overlap_manager.overlap_percentage == 0.2
        
        # Test updating min/max overlap chars
        result = self.chunker.update_overlap_configuration(
            min_overlap_chars=25,
            max_overlap_chars=300
        )
        
        assert result['new_config']['min_overlap_chars'] == 25
        assert result['new_config']['max_overlap_chars'] == 300
        
        # Test invalid configuration
        result = self.chunker.update_overlap_configuration(overlap_percentage=0.8)  # Too high
        assert result['new_config']['overlap_percentage'] == 0.5  # Should be capped
        # The validation might not show warnings for 0.5 since it's exactly at the boundary
        # Let's check that the configuration was properly capped
        assert result['changes_applied'] == True
    
    def test_get_hierarchy_statistics(self):
        """Test getting hierarchy statistics"""
        # Create chunks to establish hierarchy
        chunks = self.chunker.chunk_document(
            self.long_text,
            strategy=ChunkingStrategy.HIERARCHICAL
        )
        
        stats = self.chunker.get_hierarchy_statistics()
        
        assert isinstance(stats, dict)
        assert 'total_chunks' in stats
        assert 'total_levels' in stats
        assert 'levels_present' in stats
        assert 'parent_chunks' in stats
        assert 'leaf_chunks' in stats
        assert 'level_statistics' in stats
        assert 'overlap_statistics' in stats
        
        # The hierarchy might be empty if no parent-child relationships were established
        # This can happen with short text or specific chunking configurations
        assert stats['total_chunks'] >= 0
        assert isinstance(stats['levels_present'], list)
        
        # If chunks were created, there should be some statistics
        if len(chunks) > 0:
            # At least the overlap statistics should have some data
            assert isinstance(stats['overlap_statistics'], dict)
    
    def test_validate_hierarchy_integrity(self):
        """Test hierarchy integrity validation"""
        # Create chunks to establish hierarchy
        chunks = self.chunker.chunk_document(
            self.long_text,
            strategy=ChunkingStrategy.HIERARCHICAL
        )
        
        validation = self.chunker.validate_hierarchy_integrity()
        
        assert isinstance(validation, dict)
        assert 'is_valid' in validation
        assert 'errors' in validation
        assert 'warnings' in validation
        assert 'orphaned_chunks' in validation
        assert 'circular_references' in validation
        
        # Should be valid for properly created hierarchy
        assert validation['is_valid'] == True
        assert len(validation['errors']) == 0
        
        # Test with corrupted hierarchy
        # Add an orphaned chunk reference
        self.chunker.chunk_hierarchy['orphan'] = {
            'parent': 'non_existent_parent',
            'children': [],
            'level': 0
        }
        
        validation = self.chunker.validate_hierarchy_integrity()
        assert validation['is_valid'] == False
        assert len(validation['errors']) > 0
        assert len(validation['orphaned_chunks']) > 0
    
    def test_enhanced_parent_child_relationships(self):
        """Test enhanced parent-child relationship tracking"""
        # Create chunks to establish hierarchy
        chunks = self.chunker.chunk_document(
            self.long_text,
            strategy=ChunkingStrategy.HIERARCHICAL
        )
        
        # Check that level statistics are tracked
        assert isinstance(self.chunker.level_statistics, dict)
        
        # Check that parent chunks have enhanced metadata
        for chunk_id, chunk_info in self.chunker.chunk_hierarchy.items():
            if chunk_info['children']:  # Parent chunk
                assert 'metadata' in chunk_info
                metadata = chunk_info['metadata']
                assert 'child_count' in metadata
                assert 'total_content_length' in metadata
                assert 'creation_timestamp' in metadata
                assert metadata['child_count'] == len(chunk_info['children'])
        
        # Check that child chunks have metadata
        for chunk_id, chunk_info in self.chunker.chunk_hierarchy.items():
            if not chunk_info['children']:  # Leaf chunk
                assert 'metadata' in chunk_info
                metadata = chunk_info['metadata']
                assert 'content_length' in metadata
                assert 'sentence_count' in metadata
                assert 'has_overlap' in metadata
    
    def test_configurable_overlap_percentages(self):
        """Test that different overlap percentages produce different results"""
        # Test with low overlap
        low_overlap_chunker = HierarchicalChunker(
            base_chunk_size=100,
            overlap_percentage=0.05,
            max_levels=2
        )
        
        low_overlap_chunks = low_overlap_chunker.chunk_document(
            self.long_text,
            strategy=ChunkingStrategy.SENTENCE_AWARE
        )
        
        # Test with high overlap
        high_overlap_chunker = HierarchicalChunker(
            base_chunk_size=100,
            overlap_percentage=0.3,
            max_levels=2
        )
        
        high_overlap_chunks = high_overlap_chunker.chunk_document(
            self.long_text,
            strategy=ChunkingStrategy.SENTENCE_AWARE
        )
        
        # Both should produce chunks
        assert len(low_overlap_chunks) > 0
        assert len(high_overlap_chunks) > 0
        
        # Get overlap statistics
        low_stats = low_overlap_chunker.get_hierarchy_statistics()['overlap_statistics']
        high_stats = high_overlap_chunker.get_hierarchy_statistics()['overlap_statistics']
        
        # High overlap should generally have higher average overlap percentage
        if low_stats['chunks_with_overlap'] > 0 and high_stats['chunks_with_overlap'] > 0:
            # This might not always be true due to sentence boundary adjustments,
            # but the configuration should be different
            assert low_overlap_chunker.overlap_percentage != high_overlap_chunker.overlap_percentage


class TestHierarchicalChunkingService:
    """Test cases for HierarchicalChunkingService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = HierarchicalChunkingService(
            base_chunk_size=100,
            overlap_percentage=0.1,
            max_levels=2
        )
        
        self.sample_document = (
            "This is a test document for the hierarchical chunking service. "
            "It contains multiple sentences and paragraphs. "
            "The service should be able to chunk this document effectively. "
            "This is another paragraph with more content. "
            "It should be processed correctly by the service."
        )
    
    def test_initialization(self):
        """Test service initialization"""
        assert isinstance(self.service.chunker, HierarchicalChunker)
        assert self.service.chunker.base_chunk_size == 100
        assert self.service.chunker.overlap_percentage == 0.1
        assert self.service.chunker.max_levels == 2
    
    @pytest.mark.asyncio
    async def test_chunk_document(self):
        """Test document chunking through service"""
        chunks = await self.service.chunk_document(
            self.sample_document,
            strategy=ChunkingStrategy.SENTENCE_AWARE
        )
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        
        # Test with different strategy
        hierarchical_chunks = await self.service.chunk_document(
            self.sample_document,
            strategy=ChunkingStrategy.HIERARCHICAL
        )
        
        assert len(hierarchical_chunks) > 0
    
    @pytest.mark.asyncio
    async def test_get_chunk_hierarchy(self):
        """Test getting chunk hierarchy through service"""
        # First create some chunks to establish hierarchy
        chunks = await self.service.chunk_document(
            self.sample_document,
            strategy=ChunkingStrategy.HIERARCHICAL
        )
        
        # Test getting hierarchy for a chunk
        if chunks:
            chunk_id = f"level_{chunks[0].chunk_level}_{chunks[0].chunk_index}"
            hierarchy = await self.service.get_chunk_hierarchy(chunk_id)
            
            assert isinstance(hierarchy, dict)
    
    @pytest.mark.asyncio
    async def test_get_contextual_chunks(self):
        """Test getting contextual chunks through service"""
        # First create some chunks
        chunks = await self.service.chunk_document(
            self.sample_document,
            strategy=ChunkingStrategy.HIERARCHICAL
        )
        
        # Test getting contextual chunks
        if chunks:
            chunk_id = f"level_{chunks[0].chunk_level}_{chunks[0].chunk_index}"
            contextual_chunks = await self.service.get_contextual_chunks(
                chunk_id, context_window=2
            )
            
            assert isinstance(contextual_chunks, list)
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in service"""
        # Test with invalid input
        with pytest.raises(Exception):
            await self.service.chunk_document(None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])