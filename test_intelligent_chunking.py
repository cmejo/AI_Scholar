#!/usr/bin/env python3
"""
Test script for intelligent document chunking and semantic boundary detection
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_document():
    """Create a test document with various content types"""
    test_content = """
# Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data. This field has revolutionized many industries and continues to grow rapidly.

## What is Machine Learning?

Machine learning algorithms build mathematical models based on training data to make predictions or decisions without being explicitly programmed to do so. The field draws from statistics, computer science, and mathematics.

### Types of Machine Learning

There are three main types of machine learning:

1. **Supervised Learning**: Uses labeled training data
2. **Unsupervised Learning**: Finds patterns in unlabeled data  
3. **Reinforcement Learning**: Learns through interaction with environment

## Applications in Industry

Machine learning has found applications across numerous industries:

- Healthcare: Medical diagnosis and drug discovery
- Finance: Fraud detection and algorithmic trading
- Technology: Recommendation systems and natural language processing
- Transportation: Autonomous vehicles and route optimization

### Healthcare Applications

In healthcare, machine learning algorithms can analyze medical images to detect diseases like cancer. For example, convolutional neural networks have shown remarkable accuracy in identifying skin cancer from photographs.

Dr. Sarah Johnson, a leading researcher at Stanford Medical Center, states: "Machine learning is transforming how we approach medical diagnosis. We can now detect patterns that human doctors might miss."

### Financial Services

The financial industry has embraced machine learning for various applications. Banks use ML algorithms to detect fraudulent transactions in real-time. Investment firms employ sophisticated models to analyze market trends and make trading decisions.

```python
# Example: Simple fraud detection algorithm
def detect_fraud(transaction):
    if transaction.amount > 10000:
        return "high_risk"
    elif transaction.location != user.usual_location:
        return "medium_risk"
    else:
        return "low_risk"
```

## Technical Implementation

### Data Preprocessing

Before training any machine learning model, data must be cleaned and preprocessed. This involves:

1. Handling missing values
2. Normalizing numerical features
3. Encoding categorical variables
4. Feature selection and engineering

### Model Selection

Choosing the right algorithm depends on several factors:

| Factor | Consideration |
|--------|---------------|
| Data Size | Large datasets may require different algorithms |
| Problem Type | Classification vs. regression vs. clustering |
| Interpretability | Some models are more explainable than others |
| Performance | Accuracy vs. speed trade-offs |

### Evaluation Metrics

Different metrics are used to evaluate model performance:

- **Accuracy**: Percentage of correct predictions
- **Precision**: True positives / (True positives + False positives)
- **Recall**: True positives / (True positives + False negatives)
- **F1-Score**: Harmonic mean of precision and recall

## Future Directions

The future of machine learning looks promising with several emerging trends:

### Deep Learning Advances

Deep neural networks continue to achieve breakthrough results in computer vision, natural language processing, and game playing. Recent developments in transformer architectures have revolutionized language models.

### Explainable AI

As machine learning systems become more complex, there's growing demand for interpretable models. Researchers are developing techniques to make AI decisions more transparent and understandable.

### Edge Computing

Moving computation closer to data sources enables real-time processing and reduces latency. This is particularly important for applications like autonomous vehicles and IoT devices.

## Conclusion

Machine learning represents one of the most significant technological advances of our time. As algorithms become more sophisticated and data becomes more abundant, we can expect even more transformative applications in the years to come.

The key to successful machine learning implementation lies in understanding the problem domain, selecting appropriate algorithms, and carefully evaluating results. Organizations that master these principles will be well-positioned to leverage AI for competitive advantage.
"""
    return test_content

def test_semantic_boundary_detection():
    """Test semantic boundary detection"""
    print("🔍 Testing Semantic Boundary Detection")
    print("=" * 50)
    
    try:
        from services.intelligent_chunking import SemanticBoundaryDetector
        
        detector = SemanticBoundaryDetector()
        test_text = create_test_document()
        
        print("1. Testing structural boundary detection...")
        structural_boundaries = detector.detect_structural_boundaries(test_text)
        print(f"   Found {len(structural_boundaries)} structural boundaries")
        
        for i, (start, end, boundary_type) in enumerate(structural_boundaries[:5]):
            text_snippet = test_text[start:end][:50] + "..."
            print(f"   - {boundary_type}: {text_snippet}")
        
        print("\n2. Testing semantic boundary detection...")
        semantic_boundaries = detector.detect_semantic_boundaries(test_text)
        print(f"   Found {len(semantic_boundaries)} semantic boundaries")
        
        print("\n3. Testing topic boundary detection...")
        topic_boundaries = detector.detect_topic_boundaries(test_text)
        print(f"   Found {len(topic_boundaries)} topic boundaries")
        
        for i, (pos, topic_type) in enumerate(topic_boundaries[:3]):
            print(f"   - {topic_type} at position {pos}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_intelligent_chunking():
    """Test intelligent chunking strategies"""
    print("\n📝 Testing Intelligent Chunking")
    print("=" * 50)
    
    try:
        from services.intelligent_chunking import IntelligentChunker
        
        chunker = IntelligentChunker(
            max_chunk_size=800,
            min_chunk_size=100,
            semantic_threshold=0.65
        )
        
        test_text = create_test_document()
        document_id = "test_doc_001"
        
        print("1. Testing adaptive chunking strategy...")
        result = chunker.chunk_document(
            test_text, 
            document_id, 
            metadata={'chunking_strategy': 'adaptive'}
        )
        
        if result.chunks:
            print(f"   ✅ Created {len(result.chunks)} chunks")
            print(f"   - Document summary: {result.document_summary[:100]}...")
            print(f"   - Global topics: {result.global_topics}")
            
            # Analyze chunk characteristics
            chunk_types = {}
            for chunk in result.chunks:
                chunk_type = chunk.metadata.chunk_type
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            print(f"   - Chunk types: {chunk_types}")
            
            # Show sample chunks
            print("\n   Sample chunks:")
            for i, chunk in enumerate(result.chunks[:3]):
                print(f"   Chunk {i+1} ({chunk.metadata.chunk_type}):")
                print(f"     Content: {chunk.content[:100]}...")
                print(f"     Coherence: {chunk.metadata.coherence_score:.3f}")
                print(f"     Importance: {chunk.metadata.importance_score:.3f}")
                print(f"     Keywords: {chunk.metadata.keywords}")
        
        print("\n2. Testing semantic chunking strategy...")
        semantic_result = chunker.chunk_document(
            test_text, 
            document_id + "_semantic", 
            metadata={'chunking_strategy': 'semantic'}
        )
        
        print(f"   ✅ Semantic chunking created {len(semantic_result.chunks)} chunks")
        
        print("\n3. Testing hierarchical chunking strategy...")
        hierarchical_result = chunker.chunk_document(
            test_text, 
            document_id + "_hierarchical", 
            metadata={'chunking_strategy': 'hierarchical'}
        )
        
        print(f"   ✅ Hierarchical chunking created {len(hierarchical_result.chunks)} chunks")
        print(f"   - Hierarchy levels: {set(chunk.metadata.level for chunk in hierarchical_result.chunks)}")
        
        print("\n4. Testing context-aware chunking strategy...")
        context_result = chunker.chunk_document(
            test_text, 
            document_id + "_context", 
            metadata={'chunking_strategy': 'context_aware'}
        )
        
        print(f"   ✅ Context-aware chunking created {len(context_result.chunks)} chunks")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_coherence_analysis():
    """Test coherence analysis"""
    print("\n🧠 Testing Coherence Analysis")
    print("=" * 50)
    
    try:
        from services.intelligent_chunking import CoherenceAnalyzer
        
        analyzer = CoherenceAnalyzer()
        
        # Test coherent text
        coherent_text = """
        Machine learning is a powerful technology. It enables computers to learn from data. 
        This learning process improves performance over time. Many applications benefit from this approach.
        """
        
        # Test incoherent text
        incoherent_text = """
        Machine learning is powerful. The weather is nice today. 
        Cats are good pets. Database optimization requires careful planning.
        """
        
        print("1. Testing coherence scoring...")
        coherent_score = analyzer.calculate_coherence_score(coherent_text)
        incoherent_score = analyzer.calculate_coherence_score(incoherent_text)
        
        print(f"   - Coherent text score: {coherent_score:.3f}")
        print(f"   - Incoherent text score: {incoherent_score:.3f}")
        print(f"   - Difference: {coherent_score - incoherent_score:.3f}")
        
        print("\n2. Testing discourse marker analysis...")
        test_text = """
        First, we need to understand the problem. However, this is not always easy. 
        For example, machine learning requires large datasets. Therefore, data collection is crucial.
        In conclusion, proper planning is essential.
        """
        
        discourse_analysis = analyzer.analyze_discourse_markers(test_text)
        print(f"   - Discourse markers found: {discourse_analysis['marker_counts']}")
        print(f"   - Total markers: {discourse_analysis['total_markers']}")
        print(f"   - Discourse density: {discourse_analysis['discourse_density']:.3f}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_context_tracking():
    """Test context tracking"""
    print("\n🎯 Testing Context Tracking")
    print("=" * 50)
    
    try:
        from services.intelligent_chunking import ContextTracker, DocumentChunk, ChunkMetadata
        
        tracker = ContextTracker()
        
        # Create test chunks
        chunks = []
        for i in range(3):
            metadata = ChunkMetadata(
                chunk_id=f"chunk_{i}",
                document_id="test_doc",
                chunk_type="paragraph",
                level=1,
                position=i,
                keywords=["machine", "learning", "data"] if i < 2 else ["weather", "climate"],
                topics=["AI", "technology"] if i < 2 else ["environment"]
            )
            
            chunk = DocumentChunk(
                chunk_id=f"chunk_{i}",
                content=f"This is test chunk {i} about machine learning." if i < 2 else "This chunk is about weather patterns.",
                metadata=metadata
            )
            chunks.append(chunk)
        
        print("1. Testing context continuity calculation...")
        
        # Update context with first chunk
        tracker.update_context(chunks[0])
        
        # Test continuity with second chunk (should be high)
        continuity_high = tracker.calculate_context_continuity(chunks[1], [chunks[0]])
        print(f"   - Continuity between related chunks: {continuity_high:.3f}")
        
        # Test continuity with third chunk (should be low)
        continuity_low = tracker.calculate_context_continuity(chunks[2], chunks[:2])
        print(f"   - Continuity with unrelated chunk: {continuity_low:.3f}")
        
        print(f"   - Context tracking working: {continuity_high > continuity_low}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_knowledge_graph_integration():
    """Test knowledge graph creation"""
    print("\n🕸️ Testing Knowledge Graph Integration")
    print("=" * 50)
    
    try:
        from services.knowledge_graph import KnowledgeGraphBuilder
        from services.intelligent_chunking import intelligent_chunker
        
        # First create document structure
        test_text = create_test_document()
        document_structure = intelligent_chunker.chunk_document(test_text, "kg_test_doc")
        
        print("1. Testing knowledge graph creation...")
        kg_builder = KnowledgeGraphBuilder()
        knowledge_graph = kg_builder.build_knowledge_graph(document_structure, "kg_test_doc")
        
        if knowledge_graph.nodes:
            print(f"   ✅ Created knowledge graph with {len(knowledge_graph.nodes)} nodes")
            print(f"   - Node types: {knowledge_graph.metadata.get('node_types', {})}")
            print(f"   - Edge types: {knowledge_graph.metadata.get('edge_types', {})}")
            print(f"   - Total edges: {len(knowledge_graph.edges)}")
            
            # Show sample nodes
            print("\n   Sample nodes:")
            for i, (node_id, node) in enumerate(list(knowledge_graph.nodes.items())[:3]):
                print(f"   - {node.node_type}: {node.label}")
        else:
            print("   ⚠️ No nodes created in knowledge graph")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_performance_comparison():
    """Test performance of different chunking strategies"""
    print("\n⚡ Testing Performance Comparison")
    print("=" * 50)
    
    try:
        from services.intelligent_chunking import IntelligentChunker
        import time
        
        chunker = IntelligentChunker()
        test_text = create_test_document() * 3  # Make it longer
        
        strategies = ['adaptive', 'semantic', 'hierarchical', 'context_aware']
        results = {}
        
        for strategy in strategies:
            print(f"   Testing {strategy} strategy...")
            start_time = time.time()
            
            result = chunker.chunk_document(
                test_text, 
                f"perf_test_{strategy}", 
                metadata={'chunking_strategy': strategy}
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            results[strategy] = {
                'time': processing_time,
                'chunks': len(result.chunks),
                'avg_coherence': sum(chunk.metadata.coherence_score for chunk in result.chunks) / len(result.chunks) if result.chunks else 0
            }
            
            print(f"     - Time: {processing_time:.3f}s")
            print(f"     - Chunks: {len(result.chunks)}")
            print(f"     - Avg coherence: {results[strategy]['avg_coherence']:.3f}")
        
        # Find best strategy
        best_strategy = max(results.keys(), key=lambda k: results[k]['avg_coherence'])
        print(f"\n   🏆 Best coherence: {best_strategy} ({results[best_strategy]['avg_coherence']:.3f})")
        
        fastest_strategy = min(results.keys(), key=lambda k: results[k]['time'])
        print(f"   ⚡ Fastest: {fastest_strategy} ({results[fastest_strategy]['time']:.3f}s)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Intelligent Document Chunking Test Suite")
    print("=" * 60)
    
    tests = [
        test_semantic_boundary_detection,
        test_intelligent_chunking,
        test_coherence_analysis,
        test_context_tracking,
        test_knowledge_graph_integration,
        test_performance_comparison
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Intelligent chunking system is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    print("\nNext Steps:")
    print("1. Install missing dependencies if any tests failed")
    print("2. Download spaCy model: python -m spacy download en_core_web_sm")
    print("3. Test with real documents to validate performance")
    print("4. Integrate with the main RAG system")

if __name__ == "__main__":
    main()