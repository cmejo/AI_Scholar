#!/usr/bin/env python3
"""
Test script for AI Scholar Downloader.

Tests the AI Scholar downloader functionality including:
- Configuration loading
- Paper discovery
- Download functionality
- Processing integration
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

try:
    from multi_instance_arxiv_system.downloaders.ai_scholar_downloader import AIScholarDownloader
    from multi_instance_arxiv_system.base.base_scholar_downloader import DateRange
except ImportError as e:
    print(f"Import error: {e}")
    print("This test requires the full multi-instance system to be properly set up.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_ai_scholar_downloader():
    """Test AI Scholar downloader functionality."""
    logger.info("Starting AI Scholar Downloader test")
    
    try:
        # Initialize downloader
        config_path = "multi_instance_arxiv_system/configs/ai_scholar.yaml"
        downloader = AIScholarDownloader(config_path)
        
        # Initialize instance
        logger.info("Initializing AI Scholar instance...")
        success = await downloader.initialize_instance()
        if not success:
            logger.error("Failed to initialize AI Scholar instance")
            return False
        
        logger.info("AI Scholar instance initialized successfully")
        
        # Get instance stats
        stats = downloader.get_instance_stats()
        logger.info(f"Instance stats: {stats}")
        
        # Test paper discovery (small date range for testing)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Last week
        date_range = DateRange(start_date, end_date)
        
        logger.info(f"Testing paper discovery for date range: {date_range}")
        
        # Discover papers (limit to small number for testing)
        papers = await downloader.discover_papers(date_range)
        logger.info(f"Discovered {len(papers)} papers")
        
        if papers:
            # Show sample paper
            sample_paper = papers[0]
            logger.info(f"Sample paper: {sample_paper.title[:100]}...")
            logger.info(f"ArXiv ID: {sample_paper.arxiv_id}")
            logger.info(f"Categories: {sample_paper.categories}")
            logger.info(f"Authors: {sample_paper.authors[:3]}...")  # First 3 authors
            
            # Test download (just first few papers)
            test_papers = papers[:3]  # Limit to 3 papers for testing
            logger.info(f"Testing download of {len(test_papers)} papers...")
            
            download_result = await downloader.download_papers(test_papers)
            logger.info(f"Download result: {download_result.success_count} successful, "
                       f"{download_result.failure_count} failed, {download_result.skip_count} skipped")
            
            if download_result.successful_downloads:
                logger.info(f"Successfully downloaded: {download_result.successful_downloads}")
                
                # Test processing (just first downloaded paper)
                test_pdf = download_result.successful_downloads[:1]
                logger.info(f"Testing processing of {len(test_pdf)} PDF...")
                
                processing_result = await downloader.process_papers(test_pdf)
                logger.info(f"Processing result: {processing_result.success_count} successful, "
                           f"{processing_result.failure_count} failed")
        
        # Test cleanup
        logger.info("Testing cleanup functionality...")
        cleanup_stats = await downloader.cleanup_old_files(retention_days=1)  # Very short retention for testing
        logger.info(f"Cleanup stats: {cleanup_stats}")
        
        # Shutdown
        downloader.shutdown()
        logger.info("AI Scholar Downloader test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"AI Scholar Downloader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_arxiv_api_client():
    """Test arXiv API client functionality."""
    logger.info("Testing arXiv API client...")
    
    try:
        from multi_instance_arxiv_system.downloaders.ai_scholar_downloader import ArxivAPIClient
        
        client = ArxivAPIClient()
        
        # Test with a small search
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)  # Last 3 days
        
        papers = await client.search_papers(
            categories=['quant-ph'],  # Single category for testing
            start_date=start_date,
            end_date=end_date,
            max_results=5  # Small number for testing
        )
        
        logger.info(f"ArXiv API test: Found {len(papers)} papers")
        
        if papers:
            sample = papers[0]
            logger.info(f"Sample paper: {sample.title[:100]}...")
            logger.info(f"ArXiv ID: {sample.arxiv_id}")
            logger.info(f"Published: {sample.published_date}")
        
        return True
        
    except Exception as e:
        logger.error(f"ArXiv API client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    logger.info("Starting AI Scholar Downloader tests")
    
    # Test arXiv API client first
    api_success = await test_arxiv_api_client()
    if not api_success:
        logger.error("ArXiv API client test failed")
        return
    
    # Test full downloader
    downloader_success = await test_ai_scholar_downloader()
    if not downloader_success:
        logger.error("AI Scholar Downloader test failed")
        return
    
    logger.info("All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())