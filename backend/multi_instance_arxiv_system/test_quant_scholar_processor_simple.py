#!/usr/bin/env python3
"""
Simple test for Quant Scholar Processor functionality.
Tests the unified processing pipeline for both arXiv and journal papers.
"""

import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_quant_scholar_processor():
    """Test Quant Scholar processor initialization and basic functionality."""
    
    try:
        # Import required components
        from multi_instance_arxiv_system.shared.multi_instance_data_models import (
            InstanceConfig, VectorStoreConfig, StoragePaths, ProcessingConfig, NotificationConfig
        )
        from multi_instance_arxiv_system.processors.quant_scholar_processor import QuantScholarProcessor
        
        logger.info("=== Testing Quant Scholar Processor ===")
        
        # Create test configuration
        storage_paths = StoragePaths(
            pdf_directory="/tmp/test_quant_scholar/pdf",
            processed_directory="/tmp/test_quant_scholar/processed",
            state_directory="/tmp/test_quant_scholar/state",
            error_log_directory="/tmp/test_quant_scholar/logs",
            archive_directory="/tmp/test_quant_scholar/archive"
        )
        
        vector_store_config = VectorStoreConfig(
            collection_name="test_quant_scholar_papers",
            embedding_model="all-MiniLM-L6-v2",
            chunk_size=1000,
            chunk_overlap=200,
            host="localhost",
            port=8082
        )
        
        processing_config = ProcessingConfig(
            batch_size=10,
            max_concurrent_downloads=3,
            max_concurrent_processing=2,
            retry_attempts=3,
            timeout_seconds=300,
            memory_limit_mb=2048
        )
        
        notification_config = NotificationConfig()
        
        instance_config = InstanceConfig(
            instance_name="test_quant_scholar",
            display_name="Test Quant Scholar",
            description="Test instance for Quant Scholar processor",
            arxiv_categories=["q-fin.*", "stat.*", "econ.EM"],
            journal_sources=["jss", "rjournal"],
            storage_paths=storage_paths,
            vector_store_config=vector_store_config,
            processing_config=processing_config,
            notification_config=notification_config
        )
        
        # Initialize processor
        logger.info("1. Initializing Quant Scholar processor...")
        processor = QuantScholarProcessor(instance_config)
        
        # Test basic functionality
        logger.info("2. Testing source type determination...")
        
        # Test arXiv paper detection
        arxiv_path = "/tmp/test/2023.12345v1_Quantitative_Finance_Paper.pdf"
        source_type = processor._determine_source_type(arxiv_path)
        assert source_type == 'arxiv', f"Expected 'arxiv', got '{source_type}'"
        logger.info(f"   ✓ arXiv paper detected correctly: {source_type}")
        
        # Test JSS paper detection
        jss_path = "/tmp/test/jss_v95_i01_paper.pdf"
        source_type = processor._determine_source_type(jss_path)
        assert source_type == 'journal_jss', f"Expected 'journal_jss', got '{source_type}'"
        logger.info(f"   ✓ JSS paper detected correctly: {source_type}")
        
        # Test R Journal paper detection
        rjournal_path = "/tmp/test/rjournal_2023_2_article.pdf"
        source_type = processor._determine_source_type(rjournal_path)
        assert source_type == 'journal_rjournal', f"Expected 'journal_rjournal', got '{source_type}'"
        logger.info(f"   ✓ R Journal paper detected correctly: {source_type}")
        
        # Test paper ID extraction
        logger.info("3. Testing paper ID extraction...")
        
        arxiv_id = processor._extract_paper_id_from_path(arxiv_path)
        assert arxiv_id == "2023.12345v1", f"Expected '2023.12345v1', got '{arxiv_id}'"
        logger.info(f"   ✓ arXiv ID extracted: {arxiv_id}")
        
        jss_id = processor._extract_paper_id_from_path(jss_path)
        assert jss_id == "jss_v95_i01_paper", f"Expected 'jss_v95_i01_paper', got '{jss_id}'"
        logger.info(f"   ✓ JSS ID extracted: {jss_id}")
        
        rjournal_id = processor._extract_paper_id_from_path(rjournal_path)
        assert rjournal_id == "rjournal_2023_2_article", f"Expected 'rjournal_2023_2_article', got '{rjournal_id}'"
        logger.info(f"   ✓ R Journal ID extracted: {rjournal_id}")
        
        # Test category inference
        logger.info("4. Testing arXiv category inference...")
        
        test_content = {
            'full_text': 'This paper presents a statistical analysis of portfolio optimization using machine learning techniques.',
            'sections': {
                'abstract': 'We apply statistical methods to portfolio management and risk assessment.'
            }
        }
        
        categories = processor._infer_arxiv_categories("q-fin.12345", test_content)
        logger.info(f"   ✓ Inferred categories: {categories}")
        assert len(categories) > 0, "Should infer at least one category"
        
        # Test processing statistics
        logger.info("5. Testing processing statistics...")
        
        # Add some mock processed documents
        processor.processed_documents.add("2023.12345v1")
        processor.processed_documents.add("jss_v95_i01_paper")
        processor.processed_documents.add("rjournal_2023_2_article")
        
        stats = processor.get_processing_stats()
        logger.info(f"   ✓ Processing stats: {stats}")
        
        assert stats['total_processed_documents'] == 3, "Should have 3 processed documents"
        assert stats['source_breakdown']['arxiv_papers'] == 1, "Should have 1 arXiv paper"
        assert stats['source_breakdown']['journal_papers'] == 2, "Should have 2 journal papers"
        assert stats['unified_processing'] == True, "Should support unified processing"
        
        # Test error summary
        logger.info("6. Testing error summary...")
        error_summary = processor.get_error_summary()
        logger.info(f"   ✓ Error summary generated: {error_summary['processor_type']}")
        
        logger.info("=== All Quant Scholar Processor Tests Passed! ===")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_async_functionality():
    """Test async functionality if components are available."""
    try:
        logger.info("=== Testing Async Functionality (if available) ===")
        
        # This would require actual PDF processor and vector store services
        # For now, just test that the async methods exist
        from multi_instance_arxiv_system.processors.quant_scholar_processor import QuantScholarProcessor
        
        # Check that async methods exist
        assert hasattr(QuantScholarProcessor, 'initialize'), "Should have initialize method"
        assert hasattr(QuantScholarProcessor, 'process_papers'), "Should have process_papers method"
        assert hasattr(QuantScholarProcessor, 'validate_processing_environment'), "Should have validate_processing_environment method"
        
        logger.info("   ✓ All async methods are available")
        logger.info("   Note: Full async testing requires PDF processor and vector store services")
        
        return True
        
    except Exception as e:
        logger.error(f"Async test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("Starting Quant Scholar Processor Tests...")
    
    # Test basic functionality
    basic_test_passed = test_quant_scholar_processor()
    
    # Test async functionality
    async_test_passed = asyncio.run(test_async_functionality())
    
    if basic_test_passed and async_test_passed:
        logger.info("🎉 All tests passed! Quant Scholar processor is working correctly.")
        return True
    else:
        logger.error("❌ Some tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)