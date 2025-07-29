#!/usr/bin/env python3
"""
Demo script to showcase the enhanced hierarchical chunking with configurable overlap management
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from services.hierarchical_chunking import (
    HierarchicalChunker,
    HierarchicalChunkingService,
    ChunkingStrategy
)

def demo_enhanced_hierarchical_chunking():
    """Demonstrate the enhanced hierarchical chunking capabilities"""
    
    print("=== Enhanced Hierarchical Chunking Demo ===\n")
    
    # Sample document for testing
    sample_document = """
    Artificial Intelligence (AI) has revolutionized numerous industries and continues to shape our future. 
    Machine learning, a subset of AI, enables computers to learn and improve from experience without being explicitly programmed.
    Deep learning, which uses neural networks with multiple layers, has achieved remarkable breakthroughs in image recognition, natural language processing, and game playing.
    
    The applications of AI are vast and growing. In healthcare, AI assists in medical diagnosis, drug discovery, and personalized treatment plans.
    In finance, algorithmic trading and fraud detection systems rely heavily on AI technologies.
    Transportation has been transformed by autonomous vehicles and intelligent traffic management systems.
    
    However, AI also presents challenges and ethical considerations. Issues such as bias in algorithms, job displacement, and privacy concerns need careful attention.
    The development of AI must be guided by ethical principles to ensure it benefits humanity as a whole.
    Collaboration between technologists, policymakers, and society is essential for responsible AI development.
    
    Looking forward, the future of AI holds immense promise. Quantum computing may unlock new possibilities for AI algorithms.
    Brain-computer interfaces could create unprecedented human-AI collaboration.
    The integration of AI with other emerging technologies will likely lead to innovations we can barely imagine today.
    """
    
    # Test 1: Basic hierarchical chunking with default overlap
    print("1. Basic Hierarchical Chunking (10% overlap)")
    print("-" * 50)
    
    chunker = HierarchicalChunker(
        base_chunk_size=150,  # Smaller for demo
        overlap_percentage=0.1,
        max_levels=3
    )
    
    chunks = chunker.chunk_document(sample_document, ChunkingStrategy.HIERARCHICAL)
    
    print(f"Created {len(chunks)} chunks across multiple levels")
    
    # Show level distribution
    level_counts = {}
    for chunk in chunks:
        level = chunk.chunk_level
        level_counts[level] = level_counts.get(level, 0) + 1
    
    for level, count in sorted(level_counts.items()):
        print(f"  Level {level}: {count} chunks")
    
    # Show hierarchy statistics
    stats = chunker.get_hierarchy_statistics()
    print(f"\nHierarchy Statistics:")
    print(f"  Total chunks in hierarchy: {stats['total_chunks']}")
    print(f"  Levels present: {stats['levels_present']}")
    print(f"  Parent chunks: {stats['parent_chunks']}")
    print(f"  Leaf chunks: {stats['leaf_chunks']}")
    
    # Show overlap statistics
    overlap_stats = stats['overlap_statistics']
    print(f"\nOverlap Statistics:")
    print(f"  Chunks with overlap: {overlap_stats['chunks_with_overlap']}/{overlap_stats['total_chunks']}")
    print(f"  Average overlap percentage: {overlap_stats['average_overlap_percentage']:.2%}")
    
    print("\n" + "="*70 + "\n")
    
    # Test 2: High overlap configuration
    print("2. High Overlap Configuration (25% overlap)")
    print("-" * 50)
    
    high_overlap_chunker = HierarchicalChunker(
        base_chunk_size=150,
        overlap_percentage=0.25,
        max_levels=2,
        min_overlap_chars=30,
        max_overlap_chars=200
    )
    
    high_overlap_chunks = high_overlap_chunker.chunk_document(sample_document, ChunkingStrategy.SENTENCE_AWARE)
    
    print(f"Created {len(high_overlap_chunks)} chunks with high overlap")
    
    # Show overlap details for first few chunks
    for i, chunk in enumerate(high_overlap_chunks[:3]):
        print(f"\nChunk {i}:")
        print(f"  Content length: {len(chunk.content)} chars")
        print(f"  Has overlap_start: {hasattr(chunk, 'overlap_start') and chunk.overlap_start is not None}")
        print(f"  Has overlap_end: {hasattr(chunk, 'overlap_end') and chunk.overlap_end is not None}")
        
        if 'relationships' in chunk.metadata:
            relationships = chunk.metadata['relationships']
            metrics = relationships.get('overlap_metrics', {})
            print(f"  Actual overlap percentage: {metrics.get('overlap_percentage_actual', 0):.2%}")
            print(f"  Adjacent chunks: {len(relationships.get('adjacent_chunks', []))}")
    
    print("\n" + "="*70 + "\n")
    
    # Test 3: Dynamic configuration update
    print("3. Dynamic Configuration Update")
    print("-" * 50)
    
    print("Original configuration:")
    print(f"  Overlap percentage: {chunker.overlap_percentage}")
    print(f"  Min overlap chars: {chunker.min_overlap_chars}")
    print(f"  Max overlap chars: {chunker.max_overlap_chars}")
    
    # Update configuration
    update_result = chunker.update_overlap_configuration(
        overlap_percentage=0.2,
        min_overlap_chars=40,
        max_overlap_chars=300
    )
    
    print(f"\nConfiguration update result:")
    print(f"  Changes applied: {update_result['changes_applied']}")
    print(f"  New overlap percentage: {update_result['new_config']['overlap_percentage']}")
    print(f"  Validation passed: {update_result['validation']['is_valid']}")
    
    if update_result['validation']['warnings']:
        print(f"  Warnings: {update_result['validation']['warnings']}")
    
    print("\n" + "="*70 + "\n")
    
    # Test 4: Relationship tracking
    print("4. Parent-Child Relationship Tracking")
    print("-" * 50)
    
    # Create hierarchical chunks to demonstrate relationships
    relationship_chunks = chunker.chunk_document(sample_document, ChunkingStrategy.HIERARCHICAL)
    
    # Find a parent chunk
    parent_chunks = [c for c in relationship_chunks if c.chunk_level > 0]
    if parent_chunks:
        parent_chunk = parent_chunks[0]
        chunk_id = f"level_{parent_chunk.chunk_level}_{parent_chunk.chunk_index}"
        
        print(f"Parent chunk: {chunk_id}")
        print(f"  Level: {parent_chunk.chunk_level}")
        print(f"  Content preview: {parent_chunk.content[:100]}...")
        
        # Get relationships
        relationships = chunker.get_chunk_relationships(chunk_id)
        print(f"  Children: {len(relationships.get('children', []))}")
        print(f"  Siblings: {len(relationships.get('siblings', []))}")
        
        if 'metadata' in relationships:
            metadata = relationships['metadata']
            print(f"  Child count: {metadata.get('child_count', 0)}")
            print(f"  Total content length: {metadata.get('total_content_length', 0)}")
    
    # Validate hierarchy integrity
    validation = chunker.validate_hierarchy_integrity()
    print(f"\nHierarchy validation:")
    print(f"  Is valid: {validation['is_valid']}")
    print(f"  Errors: {len(validation['errors'])}")
    print(f"  Warnings: {len(validation['warnings'])}")
    
    print("\n" + "="*70 + "\n")
    
    # Test 5: Service-level integration
    print("5. Service-Level Integration")
    print("-" * 50)
    
    async def test_service():
        service = HierarchicalChunkingService(
            base_chunk_size=200,
            overlap_percentage=0.15,
            max_levels=2
        )
        
        service_chunks = await service.chunk_document(
            sample_document,
            ChunkingStrategy.ADAPTIVE
        )
        
        print(f"Service created {len(service_chunks)} chunks")
        
        # Test hierarchy retrieval
        if service_chunks:
            chunk_id = f"level_{service_chunks[0].chunk_level}_{service_chunks[0].chunk_index}"
            hierarchy_info = await service.get_chunk_hierarchy(chunk_id)
            print(f"Retrieved hierarchy info for chunk: {len(hierarchy_info)} properties")
            
            # Test contextual chunks
            contextual_chunks = await service.get_contextual_chunks(chunk_id, context_window=2)
            print(f"Found {len(contextual_chunks)} contextual chunks")
    
    # Run async test
    import asyncio
    asyncio.run(test_service())
    
    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    demo_enhanced_hierarchical_chunking()