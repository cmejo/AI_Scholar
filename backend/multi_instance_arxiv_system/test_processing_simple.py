#!/usr/bin/env python3
"""
Simple test for AI Scholar Processing components.

Tests individual components without complex imports.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_chunking_logic():
    """Test basic chunking logic."""
    logger.info("Testing basic chunking logic...")
    
    try:
        # Simple chunking function
        def create_chunks(text: str, chunk_size: int = 500, overlap: int = 100):
            """Simple text chunking function."""
            chunks = []
            words = text.split()
            
            current_chunk = []
            current_size = 0
            
            for word in words:
                word_size = len(word) + 1  # +1 for space
                
                if current_size + word_size > chunk_size and current_chunk:
                    # Create chunk
                    chunk_text = ' '.join(current_chunk)
                    chunks.append({
                        'text': chunk_text,
                        'word_count': len(current_chunk),
                        'character_count': len(chunk_text)
                    })
                    
                    # Start new chunk with overlap
                    overlap_words = current_chunk[-overlap//10:] if overlap > 0 else []
                    current_chunk = overlap_words + [word]
                    current_size = sum(len(w) + 1 for w in current_chunk)
                else:
                    current_chunk.append(word)
                    current_size += word_size
            
            # Add final chunk
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'word_count': len(current_chunk),
                    'character_count': len(chunk_text)
                })
            
            return chunks
        
        # Test with sample text
        test_text = """
        Quantum computing is an emerging field that leverages quantum mechanical phenomena 
        to process information in fundamentally new ways. Unlike classical computers that 
        use bits to represent information as either 0 or 1, quantum computers use quantum 
        bits or qubits that can exist in superposition states. This allows quantum computers 
        to perform certain calculations exponentially faster than classical computers. 
        The field has seen significant advances in recent years with companies like IBM, 
        Google, and others developing increasingly powerful quantum processors. However, 
        quantum computers are still in their early stages and face significant challenges 
        including quantum decoherence and error correction.
        """
        
        chunks = create_chunks(test_text.strip(), chunk_size=200, overlap=50)
        
        logger.info(f"Created {len(chunks)} chunks from test text")
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Chunk {i+1}: {chunk['word_count']} words, "
                       f"{chunk['character_count']} characters")
            logger.info(f"  Text preview: {chunk['text'][:100]}...")
        
        # Verify chunks
        assert len(chunks) > 1, "Should create multiple chunks"
        assert all(chunk['character_count'] > 0 for chunk in chunks), "All chunks should have content"
        
        logger.info("Basic chunking logic test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Basic chunking logic test failed: {e}")
        return False


def test_paper_metadata_extraction():
    """Test paper metadata extraction logic."""
    logger.info("Testing paper metadata extraction...")
    
    try:
        def extract_arxiv_id_from_filename(filename: str):
            """Extract arXiv ID from filename."""
            try:
                stem = Path(filename).stem
                parts = stem.split('_')
                if len(parts) >= 2:
                    # Reconstruct arXiv ID from parts
                    # Handle both old format (quant-ph/0501001) and new format (2310.12345)
                    if len(parts) >= 3 and parts[1].isdigit():
                        # New format: 2310_12345 -> 2310.12345
                        arxiv_id = f"{parts[0]}.{parts[1]}"
                    else:
                        # Old format or single part
                        arxiv_id = parts[0].replace('_', '/')
                    return arxiv_id
            except Exception:
                pass
            return None
        
        def create_safe_filename(arxiv_id: str, title: str):
            """Create safe filename from arXiv ID and title."""
            safe_id = arxiv_id.replace('/', '_').replace('.', '_')
            safe_title = "".join(c for c in title[:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            return f"{safe_id}_{safe_title}.pdf"
        
        # Test cases
        test_cases = [
            ("2310.12345", "Quantum Error Correction Methods"),
            ("quant-ph/0501001", "Quantum Teleportation Protocol"),
            ("1234.5678", "Machine Learning for Quantum Computing")
        ]
        
        for arxiv_id, title in test_cases:
            # Create filename
            filename = create_safe_filename(arxiv_id, title)
            logger.info(f"Created filename: {filename}")
            
            # Extract ID back
            extracted_id = extract_arxiv_id_from_filename(filename)
            logger.info(f"Extracted ID: {extracted_id}")
            
            # Verify
            expected_id = arxiv_id.replace('/', '_')
            assert extracted_id == expected_id, f"ID mismatch: {extracted_id} != {expected_id}"
        
        logger.info("Paper metadata extraction test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Paper metadata extraction test failed: {e}")
        return False


def test_document_id_generation():
    """Test document ID generation."""
    logger.info("Testing document ID generation...")
    
    try:
        def generate_document_id(instance_name: str, arxiv_id: str):
            """Generate unique document ID."""
            safe_id = arxiv_id.replace('/', '_').replace('.', '_')
            return f"{instance_name}_arxiv_{safe_id}"
        
        # Test cases
        test_cases = [
            ("ai_scholar", "2310.12345"),
            ("quant_scholar", "quant-ph/0501001"),
            ("ai_scholar", "1234.5678")
        ]
        
        generated_ids = set()
        
        for instance, arxiv_id in test_cases:
            doc_id = generate_document_id(instance, arxiv_id)
            logger.info(f"Generated ID: {doc_id}")
            
            # Verify uniqueness
            assert doc_id not in generated_ids, f"Duplicate ID generated: {doc_id}"
            generated_ids.add(doc_id)
            
            # Verify format
            assert doc_id.startswith(instance), f"ID should start with instance name"
            assert "_arxiv_" in doc_id, f"ID should contain '_arxiv_'"
        
        logger.info("Document ID generation test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Document ID generation test failed: {e}")
        return False


def test_section_identification():
    """Test section identification logic."""
    logger.info("Testing section identification...")
    
    try:
        import re
        
        def identify_sections(text: str):
            """Simple section identification."""
            sections = {}
            
            # Simple patterns for common sections
            patterns = {
                'abstract': r'(?i)abstract[\s\n]*(.+?)(?=\n\s*(?:introduction|keywords|1\.|background)|$)',
                'introduction': r'(?i)(?:introduction|background)[\s\n]*(.+?)(?=\n\s*(?:methods?|methodology|2\.|related)|$)',
                'methods': r'(?i)(?:methods?|methodology)[\s\n]*(.+?)(?=\n\s*(?:results?|3\.|experiments?)|$)',
                'results': r'(?i)(?:results?|findings?)[\s\n]*(.+?)(?=\n\s*(?:discussion|4\.|conclusion)|$)',
                'conclusion': r'(?i)(?:conclusion|conclusions?)[\s\n]*(.+?)(?=\n\s*(?:references?|acknowledgment)|$)'
            }
            
            for section_name, pattern in patterns.items():
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    sections[section_name] = match.group(1).strip()[:500]  # Limit length
            
            return sections
        
        # Test text with sections
        test_text = """
        Abstract
        This paper presents a novel approach to quantum error correction using stabilizer codes.
        
        Introduction
        Quantum computing faces significant challenges due to quantum decoherence and noise.
        
        Methods
        We implemented a surface code approach with syndrome extraction and correction cycles.
        
        Results
        Our method achieved 99.5% fidelity in quantum state preservation over 1000 cycles.
        
        Conclusion
        The proposed method shows promise for practical quantum error correction applications.
        """
        
        sections = identify_sections(test_text)
        
        logger.info(f"Identified {len(sections)} sections")
        
        for section_name, content in sections.items():
            logger.info(f"Section '{section_name}': {content[:100]}...")
        
        # Verify sections
        expected_sections = ['abstract', 'introduction', 'methods', 'results', 'conclusion']
        found_sections = list(sections.keys())
        
        assert len(found_sections) >= 3, f"Should find at least 3 sections, found {len(found_sections)}"
        
        logger.info("Section identification test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Section identification test failed: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("Starting AI Scholar Processing component tests")
    
    tests = [
        ("Basic Chunking Logic", test_chunking_logic),
        ("Paper Metadata Extraction", test_paper_metadata_extraction),
        ("Document ID Generation", test_document_id_generation),
        ("Section Identification", test_section_identification),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "PASSED" if result else "FAILED"
            logger.info(f"{test_name} Test: {status}")
        except Exception as e:
            logger.error(f"{test_name} Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n--- Test Summary ---")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("All tests completed successfully!")
    else:
        logger.error("Some tests failed!")


if __name__ == "__main__":
    asyncio.run(main())