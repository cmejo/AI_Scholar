#!/usr/bin/env python3
"""
Demonstration script for hierarchical chunking with overlap management
"""
import sys
import os
import asyncio

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from services.hierarchical_chunking import (
    HierarchicalChunkingService,
    ChunkingStrategy
)

async def demonstrate_hierarchical_chunking():
    """Demonstrate the hierarchical chunking functionality"""
    
    # Sample document for testing
    sample_document = """
    Artificial Intelligence (AI) has revolutionized numerous industries and continues to shape our future. 
    Machine learning, a subset of AI, enables computers to learn and improve from experience without being explicitly programmed.
    Deep learning, which uses neural networks with multiple layers, has achieved remarkable breakthroughs in image recognition, natural language processing, and game playing.
    
    Natural Language Processing (NLP) is a branch of AI that focuses on the interaction between computers and human language.
    It involves developing algorithms and models that can understand, interpret, and generate human language in a valuable way.
    Applications of NLP include machine translation, sentiment analysis, chatbots, and text summarization.
    
    Computer Vision is another important field within AI that deals with how computers can gain high-level understanding from digital images or videos.
    It seeks to automate tasks that the human visual system can do, such as object detection, facial recognition, and medical image analysis.
    Recent advances in computer vision have been driven by deep learning techniques and large datasets.
    
    The future of AI holds immense potential for solving complex problems in healthcare, transportation, education, and environmental sustainability.
    However, it also raises important ethical considerations regarding privacy, bias, job displacement, and the need for responsible AI development.
    As AI continues to evolve, it is crucial to ensure that these technologies are developed and deployed in ways that benefit humanity as a whole.
    """
    
    # Initialize the hierarchical chunking service
    service = HierarchicalChunkingService(
        base_chunk_size=150,  # Smaller chunks for demonstration
        overlap_percentage=0.15,  # 15% overlap
        max_levels=3
    )
    
    print("=== Hierarchical Document Chunking with Overlap Management Demo ===\n")
    print(f"Document length: {len(sample_document)} characters")
    print(f"Configuration: chunk_size=150, overlap=15%, max_levels=3\n")
    
    # Test different chunking strategies
    strategies = [
        ChunkingStrategy.SENTENCE_AWARE,
        ChunkingStrategy.HIERARCHICAL,
        ChunkingStrategy.ADAPTIVE
    ]
    
    for strategy in strategies:
        print(f"--- {strategy.value.upper()} CHUNKING ---")
        
        chunks = await service.chunk_document(sample_document, strategy=strategy)
        
        print(f"Generated {len(chunks)} chunks")
        
        # Group chunks by level
        levels = {}
        for chunk in chunks:
            level = chunk.chunk_level
            if level not in levels:
                levels[level] = []
            levels[level].append(chunk)
        
        # Display chunk information by level
        for level in sorted(levels.keys()):
            level_chunks = levels[level]
            print(f"\nLevel {level}: {len(level_chunks)} chunks")
            
            for i, chunk in enumerate(level_chunks[:3]):  # Show first 3 chunks per level
                print(f"  Chunk {chunk.chunk_index}:")
                print(f"    Content: {chunk.content[:100]}{'...' if len(chunk.content) > 100 else ''}")
                print(f"    Characters: {chunk.start_char}-{chunk.end_char}")
                print(f"    Sentences: {chunk.start_sentence}-{chunk.end_sentence}")
                
                # Show overlap information
                if hasattr(chunk, 'overlap_start') and chunk.overlap_start is not None:
                    print(f"    Overlap start: {chunk.overlap_start}")
                if hasattr(chunk, 'overlap_end') and chunk.overlap_end is not None:
                    print(f"    Overlap end: {chunk.overlap_end}")
                
                # Show parent-child relationships
                if chunk.parent_chunk_id:
                    print(f"    Parent: {chunk.parent_chunk_id}")
                
                if 'child_chunks' in chunk.metadata:
                    print(f"    Children: {chunk.metadata['child_chunks']}")
                
                # Show relationship information
                if 'relationships' in chunk.metadata:
                    relationships = chunk.metadata['relationships']
                    if relationships['adjacent_chunks']:
                        print(f"    Adjacent: {relationships['adjacent_chunks']}")
                
                print()
            
            if len(level_chunks) > 3:
                print(f"    ... and {len(level_chunks) - 3} more chunks")
        
        print("\n" + "="*60 + "\n")
    
    # Demonstrate chunk hierarchy and contextual retrieval
    print("--- CHUNK HIERARCHY AND CONTEXT DEMO ---")
    
    hierarchical_chunks = await service.chunk_document(
        sample_document, 
        strategy=ChunkingStrategy.HIERARCHICAL
    )
    
    if hierarchical_chunks:
        # Pick a chunk to demonstrate hierarchy
        sample_chunk = hierarchical_chunks[0]
        chunk_id = f"level_{sample_chunk.chunk_level}_{sample_chunk.chunk_index}"
        
        print(f"Demonstrating hierarchy for chunk: {chunk_id}")
        
        # Get hierarchy information
        hierarchy = await service.get_chunk_hierarchy(chunk_id)
        print(f"Hierarchy info: {hierarchy}")
        
        # Get contextual chunks
        contextual_chunks = await service.get_contextual_chunks(chunk_id, context_window=2)
        print(f"Contextual chunks: {contextual_chunks}")
    
    print("\nDemo completed successfully!")

if __name__ == "__main__":
    asyncio.run(demonstrate_hierarchical_chunking())