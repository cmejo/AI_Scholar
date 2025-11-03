#!/usr/bin/env python3
"""
Test script for Task 8.2: Implement instance-specific document processing.

This script tests the instance-specific document processing capabilities,
metadata schemas, and unified search interface.
"""

import sys
from pathlib import Path
from datetime import datetime
import asyncio

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.vector_store.document_processor import (
        DocumentProcessorFactory, AIScholarDocumentProcessor, QuantScholarDocumentProcessor
    )
    from multi_instance_arxiv_system.vector_store.unified_search_interface import (
        UnifiedSearchInterface, SearchScope, SearchFilter, SortOrder
    )
    from multi_instance_arxiv_system.vector_store.multi_instance_vector_store_service import MultiInstanceVectorStoreService
    from multi_instance_arxiv_system.shared.multi_instance_data_models import (
        ArxivPaper, JournalPaper, InstanceConfig, VectorStoreConfig, 
        ProcessingConfig, NotificationConfig, StoragePaths
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)


def create_test_instance_config(instance_name: str) -> InstanceConfig:
    """Create a test instance configuration."""
    
    storage_paths = StoragePaths(
        pdf_directory=f"/tmp/test_{instance_name}/pdf",
        processed_directory=f"/tmp/test_{instance_name}/processed",
        state_directory=f"/tmp/test_{instance_name}/state",
        error_log_directory=f"/tmp/test_{instance_name}/logs",
        archive_directory=f"/tmp/test_{instance_name}/archive"
    )
    
    vector_store_config = VectorStoreConfig(
        collection_name=f"test_{instance_name}_papers",
        embedding_model="all-MiniLM-L6-v2"
    )
    
    processing_config = ProcessingConfig(
        batch_size=20,
        max_concurrent_downloads=3,
        max_concurrent_processing=2
    )
    
    notification_config = NotificationConfig(
        enabled=False
    )
    
    return InstanceConfig(
        instance_name=instance_name,
        display_name=f"Test {instance_name.title()}",
        description=f"Test configuration for {instance_name}",
        arxiv_categories=["cs.AI", "cs.LG"] if "ai" in instance_name else ["q-fin.CP", "econ.EM"],
        journal_sources=[],
        storage_paths=storage_paths,
        vector_store_config=vector_store_config,
        processing_config=processing_config,
        notification_config=notification_config
    )


def create_test_papers():
    """Create test papers for different instances."""
    
    # AI Scholar paper
    ai_paper = ArxivPaper(
        paper_id="2301.00001",
        title="Attention Mechanisms in Deep Learning: A Comprehensive Survey",
        authors=["Alice Johnson", "Bob Smith", "Carol Davis"],
        abstract="This paper provides a comprehensive survey of attention mechanisms in deep learning. We cover the mathematical foundations of attention, including self-attention and cross-attention mechanisms. The survey includes applications in natural language processing, computer vision, and reinforcement learning. We also discuss recent advances in transformer architectures and their impact on various AI tasks.",
        published_date=datetime(2023, 1, 15),
        instance_name="ai_scholar",
        arxiv_id="2301.00001",
        categories=["cs.AI", "cs.LG", "cs.CL"],
        pdf_url="https://arxiv.org/pdf/2301.00001.pdf"
    )
    
    # Quant Scholar paper
    quant_paper = JournalPaper(
        paper_id="jss_2023_001",
        title="Portfolio Optimization with Machine Learning: A Statistical Approach",
        authors=["David Wilson", "Eva Martinez", "Frank Brown"],
        abstract="This paper presents a comprehensive approach to portfolio optimization using machine learning techniques. We develop statistical models for risk assessment and return prediction. The methodology includes time series analysis, regression models, and Monte Carlo simulations. We demonstrate the effectiveness of our approach using real market data and compare results with traditional portfolio optimization methods.",
        published_date=datetime(2023, 2, 1),
        instance_name="quant_scholar",
        journal_name="Journal of Statistical Software",
        volume="105",
        issue="3",
        pages="1-25",
        pdf_url="https://www.jstatsoft.org/article/view/v105i03"
    )
    
    return ai_paper, quant_paper


def create_test_content():
    """Create test content for document processing."""
    
    ai_content = """
    Abstract
    
    This paper provides a comprehensive survey of attention mechanisms in deep learning. 
    Attention mechanisms have revolutionized the field of artificial intelligence by allowing 
    models to focus on relevant parts of the input data. We examine various types of attention 
    including self-attention, cross-attention, and multi-head attention.
    
    Introduction
    
    Deep learning has achieved remarkable success in various domains including natural language 
    processing, computer vision, and speech recognition. The introduction of attention mechanisms 
    has been a key factor in this success. The attention mechanism allows neural networks to 
    selectively focus on different parts of the input sequence.
    
    The mathematical foundation of attention can be expressed as:
    Attention(Q, K, V) = softmax(QK^T / √d_k)V
    
    Where Q, K, and V represent queries, keys, and values respectively.
    
    Methodology
    
    We implement several attention mechanisms using PyTorch:
    
    ```python
    class MultiHeadAttention(nn.Module):
        def __init__(self, d_model, num_heads):
            super().__init__()
            self.d_model = d_model
            self.num_heads = num_heads
            
        def forward(self, query, key, value):
            # Implementation details
            return attention_output
    ```
    
    Results
    
    Our experiments show that transformer models with attention mechanisms achieve 
    state-of-the-art performance on various benchmarks. The attention weights provide 
    interpretability by showing which parts of the input the model focuses on.
    
    Conclusion
    
    Attention mechanisms have fundamentally changed how we approach sequence modeling 
    in deep learning. Future work should explore more efficient attention mechanisms 
    and their applications to new domains.
    """
    
    quant_content = """
    Abstract
    
    This paper presents a comprehensive approach to portfolio optimization using machine 
    learning techniques. We develop statistical models for risk assessment and return 
    prediction. The methodology includes time series analysis, regression models, and 
    Monte Carlo simulations.
    
    Introduction
    
    Portfolio optimization is a fundamental problem in quantitative finance. The goal 
    is to construct a portfolio that maximizes expected return while minimizing risk. 
    Traditional approaches rely on mean-variance optimization introduced by Markowitz.
    
    The expected return of a portfolio can be expressed as:
    E[R_p] = Σ w_i * E[R_i]
    
    Where w_i represents the weight of asset i and E[R_i] is the expected return.
    
    Methodology
    
    We employ several statistical methods:
    
    1. Time series analysis using ARIMA models
    2. Regression analysis for factor modeling
    3. Monte Carlo simulation for risk assessment
    4. Machine learning algorithms for return prediction
    
    Table 1: Portfolio Performance Metrics
    
    | Strategy | Return | Volatility | Sharpe Ratio |
    |----------|--------|------------|--------------|
    | Traditional | 8.5% | 12.3% | 0.69 |
    | ML-Enhanced | 10.2% | 11.8% | 0.86 |
    
    Results
    
    Our empirical analysis shows that machine learning enhanced portfolio optimization 
    significantly outperforms traditional methods. The Sharpe ratio improves from 0.69 
    to 0.86, indicating better risk-adjusted returns.
    
    The statistical significance of our results is confirmed through hypothesis testing 
    with p-values < 0.05 for all performance metrics.
    
    Conclusion
    
    This study demonstrates the effectiveness of combining machine learning with 
    traditional portfolio optimization techniques. The approach provides better 
    risk-adjusted returns and more robust portfolio construction.
    """
    
    return ai_content, quant_content


async def test_document_processor_factory():
    """Test the DocumentProcessorFactory."""
    print("Testing DocumentProcessorFactory...")
    
    try:
        # Test supported instances
        supported = DocumentProcessorFactory.get_supported_instances()
        assert 'ai_scholar' in supported
        assert 'quant_scholar' in supported
        print(f"✓ Supported instances: {supported}")
        
        # Test processor creation
        ai_config = create_test_instance_config("ai_scholar")
        ai_processor = DocumentProcessorFactory.create_processor("ai_scholar", ai_config)
        assert isinstance(ai_processor, AIScholarDocumentProcessor)
        print("✓ AI Scholar processor created")
        
        quant_config = create_test_instance_config("quant_scholar")
        quant_processor = DocumentProcessorFactory.create_processor("quant_scholar", quant_config)
        assert isinstance(quant_processor, QuantScholarDocumentProcessor)
        print("✓ Quant Scholar processor created")
        
        # Test processor info
        ai_info = DocumentProcessorFactory.get_processor_info("ai_scholar")
        assert ai_info['name'] == 'AI Scholar Document Processor'
        print(f"✓ AI Scholar info: {ai_info['description']}")
        
        quant_info = DocumentProcessorFactory.get_processor_info("quant_scholar")
        assert quant_info['name'] == 'Quant Scholar Document Processor'
        print(f"✓ Quant Scholar info: {quant_info['description']}")
        
        print("✓ DocumentProcessorFactory tests passed")
        return True
        
    except Exception as e:
        print(f"❌ DocumentProcessorFactory test failed: {e}")
        return False


async def test_ai_scholar_processing():
    """Test AI Scholar document processing."""
    print("Testing AI Scholar document processing...")
    
    try:
        # Create processor and test data
        config = create_test_instance_config("ai_scholar")
        processor = AIScholarDocumentProcessor("ai_scholar", config)
        
        ai_paper, _ = create_test_papers()
        ai_content, _ = create_test_content()
        
        # Test chunk creation
        section_markers = {
            'abstract': r'^Abstract',
            'introduction': r'^Introduction',
            'methodology': r'^Methodology',
            'results': r'^Results',
            'conclusion': r'^Conclusion'
        }
        
        chunks = processor.create_document_chunks(ai_paper, ai_content, section_markers)
        
        assert len(chunks) > 0
        print(f"✓ Created {len(chunks)} chunks")
        
        # Test chunk content
        for i, chunk in enumerate(chunks[:3]):  # Test first 3 chunks
            assert 'text' in chunk
            assert 'document_metadata' in chunk
            assert chunk['document_metadata']['instance_name'] == 'ai_scholar'
            assert chunk['document_metadata']['paper_id'] == ai_paper.paper_id
            print(f"✓ Chunk {i+1}: {len(chunk['text'])} chars, section: {chunk.get('section', 'unknown')}")
        
        # Test AI-specific metadata
        first_chunk = chunks[0]
        metadata = first_chunk['document_metadata']
        
        # Check AI-specific fields
        assert 'technical_complexity' in metadata
        assert 'contains_equations' in metadata
        assert 'contains_code' in metadata
        assert 'ml_keywords_count' in metadata
        
        print(f"✓ Technical complexity: {metadata['technical_complexity']:.2f}")
        print(f"✓ Contains equations: {metadata['contains_equations']}")
        print(f"✓ Contains code: {metadata['contains_code']}")
        print(f"✓ ML keywords count: {metadata['ml_keywords_count']}")
        
        # Test chunk validation
        validation = processor.validate_chunks(chunks)
        assert validation['valid']
        print(f"✓ Chunk validation: {validation['stats']['total_chunks']} chunks, avg quality: {validation['stats']['average_quality']:.2f}")
        
        print("✓ AI Scholar processing tests passed")
        return True
        
    except Exception as e:
        print(f"❌ AI Scholar processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_quant_scholar_processing():
    """Test Quant Scholar document processing."""
    print("Testing Quant Scholar document processing...")
    
    try:
        # Create processor and test data
        config = create_test_instance_config("quant_scholar")
        processor = QuantScholarDocumentProcessor("quant_scholar", config)
        
        _, quant_paper = create_test_papers()
        _, quant_content = create_test_content()
        
        # Test chunk creation
        section_markers = {
            'abstract': r'^Abstract',
            'introduction': r'^Introduction',
            'methodology': r'^Methodology',
            'results': r'^Results',
            'conclusion': r'^Conclusion'
        }
        
        chunks = processor.create_document_chunks(quant_paper, quant_content, section_markers)
        
        assert len(chunks) > 0
        print(f"✓ Created {len(chunks)} chunks")
        
        # Test chunk content
        for i, chunk in enumerate(chunks[:3]):  # Test first 3 chunks
            assert 'text' in chunk
            assert 'document_metadata' in chunk
            assert chunk['document_metadata']['instance_name'] == 'quant_scholar'
            assert chunk['document_metadata']['paper_id'] == quant_paper.paper_id
            print(f"✓ Chunk {i+1}: {len(chunk['text'])} chars, section: {chunk.get('section', 'unknown')}")
        
        # Test Quant-specific metadata
        first_chunk = chunks[0]
        metadata = first_chunk['document_metadata']
        
        # Check Quant-specific fields
        assert 'statistical_complexity' in metadata
        assert 'contains_formulas' in metadata
        assert 'contains_tables' in metadata
        assert 'financial_keywords_count' in metadata
        
        print(f"✓ Statistical complexity: {metadata['statistical_complexity']:.2f}")
        print(f"✓ Contains formulas: {metadata['contains_formulas']}")
        print(f"✓ Contains tables: {metadata['contains_tables']}")
        print(f"✓ Financial keywords count: {metadata['financial_keywords_count']}")
        
        # Test chunk validation
        validation = processor.validate_chunks(chunks)
        assert validation['valid']
        print(f"✓ Chunk validation: {validation['stats']['total_chunks']} chunks, avg quality: {validation['stats']['average_quality']:.2f}")
        
        print("✓ Quant Scholar processing tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Quant Scholar processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_unified_search_interface():
    """Test the unified search interface."""
    print("Testing Unified Search Interface...")
    
    try:
        # Create mock vector store service
        vector_store_service = MultiInstanceVectorStoreService()
        
        # Create unified search interface
        search_interface = UnifiedSearchInterface(vector_store_service)
        
        # Test search filter creation
        search_filter = SearchFilter(
            instances=['ai_scholar', 'quant_scholar'],
            sections=['abstract', 'introduction'],
            min_quality_score=0.5,
            date_from=datetime(2020, 1, 1),
            date_to=datetime(2024, 1, 1)
        )
        
        print("✓ Search filter created")
        
        # Test search scope and sort order enums
        assert SearchScope.ALL_INSTANCES.value == "all_instances"
        assert SortOrder.RELEVANCE_DESC.value == "relevance_desc"
        print("✓ Search enums working")
        
        # Test search history functionality
        initial_history_size = len(search_interface.get_search_history())
        
        # Simulate storing search history
        search_interface._store_search_history(
            query="test query",
            scope=SearchScope.ALL_INSTANCES,
            filters=search_filter,
            result_count=10,
            search_time=0.5
        )
        
        history = search_interface.get_search_history()
        assert len(history) == initial_history_size + 1
        assert history[-1]['query'] == "test query"
        print("✓ Search history functionality working")
        
        # Test search statistics
        stats = search_interface.get_search_statistics()
        if stats:  # Only test if there's history
            assert 'total_searches' in stats
            assert 'average_search_time_seconds' in stats
            print(f"✓ Search statistics: {stats['total_searches']} searches")
        
        # Test query preprocessing
        processed_query = search_interface._preprocess_query("machine learning deep learning")
        assert len(processed_query) > 0
        print(f"✓ Query preprocessing: '{processed_query[:50]}...'")
        
        print("✓ Unified Search Interface tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Unified Search Interface test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_chunking_strategies():
    """Test different chunking strategies."""
    print("Testing chunking strategies...")
    
    try:
        # Test AI Scholar chunking (sentence boundary)
        ai_config = create_test_instance_config("ai_scholar")
        ai_processor = AIScholarDocumentProcessor("ai_scholar", ai_config)
        
        test_text = "This is sentence one. This is sentence two! This is sentence three? This is a longer sentence with more content to test the chunking algorithm."
        
        chunks = ai_processor._sentence_boundary_chunking(test_text, "test_section")
        assert len(chunks) > 0
        print(f"✓ Sentence boundary chunking: {len(chunks)} chunks")
        
        # Test Quant Scholar chunking (paragraph boundary)
        quant_config = create_test_instance_config("quant_scholar")
        quant_processor = QuantScholarDocumentProcessor("quant_scholar", quant_config)
        
        test_text_paragraphs = "This is paragraph one.\n\nThis is paragraph two with more content.\n\nThis is paragraph three."
        
        chunks = quant_processor._paragraph_boundary_chunking(test_text_paragraphs, "test_section")
        assert len(chunks) > 0
        print(f"✓ Paragraph boundary chunking: {len(chunks)} chunks")
        
        # Test sliding window chunking
        chunks = ai_processor._sliding_window_chunking(test_text, "test_section")
        assert len(chunks) > 0
        print(f"✓ Sliding window chunking: {len(chunks)} chunks")
        
        print("✓ Chunking strategies tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Chunking strategies test failed: {e}")
        return False


async def test_metadata_extraction():
    """Test instance-specific metadata extraction."""
    print("Testing metadata extraction...")
    
    try:
        # Test AI Scholar metadata extraction
        ai_config = create_test_instance_config("ai_scholar")
        ai_processor = AIScholarDocumentProcessor("ai_scholar", ai_config)
        
        # Test technical complexity calculation
        technical_text = "This paper presents a novel neural network architecture with attention mechanisms and gradient descent optimization."
        complexity = ai_processor._calculate_technical_complexity(technical_text)
        assert 0.0 <= complexity <= 1.0
        print(f"✓ Technical complexity: {complexity:.3f}")
        
        # Test equation detection
        equation_text = "The loss function is defined as L = Σ(y - ŷ)² and E[X] = μ"
        has_equations = ai_processor._contains_equations(equation_text)
        print(f"✓ Contains equations: {has_equations}")
        
        # Test code detection
        code_text = "```python\ndef train_model():\n    return model```"
        has_code = ai_processor._contains_code(code_text)
        print(f"✓ Contains code: {has_code}")
        
        # Test Quant Scholar metadata extraction
        quant_config = create_test_instance_config("quant_scholar")
        quant_processor = QuantScholarDocumentProcessor("quant_scholar", quant_config)
        
        # Test statistical complexity
        stats_text = "We perform regression analysis with hypothesis testing and calculate p-values for significance."
        stats_complexity = quant_processor._calculate_statistical_complexity(stats_text)
        assert 0.0 <= stats_complexity <= 1.0
        print(f"✓ Statistical complexity: {stats_complexity:.3f}")
        
        # Test table detection
        table_text = "Table 1 shows the results:\n| Variable | Coefficient | Std. Error |\n|----------|-------------|------------|"
        has_tables = quant_processor._contains_tables(table_text)
        print(f"✓ Contains tables: {has_tables}")
        
        # Test financial keywords
        finance_text = "Portfolio optimization with risk management and Sharpe ratio calculation."
        finance_count = quant_processor._count_financial_keywords(finance_text)
        print(f"✓ Financial keywords count: {finance_count}")
        
        print("✓ Metadata extraction tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Metadata extraction test failed: {e}")
        return False


async def main():
    """Run all tests for Task 8.2."""
    print("Testing Task 8.2: Implement instance-specific document processing")
    print("=" * 80)
    
    test_results = []
    
    try:
        # Test individual components
        test_results.append(await test_document_processor_factory())
        test_results.append(await test_ai_scholar_processing())
        test_results.append(await test_quant_scholar_processing())
        test_results.append(await test_unified_search_interface())
        test_results.append(await test_chunking_strategies())
        test_results.append(await test_metadata_extraction())
        
        print("\n" + "=" * 80)
        
        if all(test_results):
            print("✅ All Task 8.2 tests passed!")
            print("\nImplemented features:")
            print("- Instance-aware document chunk creation with specialized strategies")
            print("- AI Scholar processor with technical complexity analysis")
            print("- Quant Scholar processor with statistical complexity analysis")
            print("- Instance-specific metadata schemas and extraction")
            print("- Unified search interface with advanced filtering")
            print("- Multiple chunking strategies (sentence, paragraph, sliding window)")
            print("- Content analysis (equations, code, tables, formulas)")
            print("- Quality scoring and validation")
            print("- Search history and statistics tracking")
            
            return True
        else:
            failed_count = len([r for r in test_results if not r])
            print(f"❌ {failed_count} out of {len(test_results)} tests failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)