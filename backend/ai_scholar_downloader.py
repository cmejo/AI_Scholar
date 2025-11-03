#!/usr/bin/env python3
"""
AI Scholar Downloader Script

Entry point script for downloading and processing AI Scholar papers.
Handles arXiv paper discovery, bulk downloading, and processing into vector store.

Usage:
    python ai_scholar_downloader.py [options]

Options:
    --days DAYS         Number of days back to search (default: 7)
    --max-papers NUM    Maximum number of papers to process (default: 100)
    --config PATH       Path to AI Scholar config file (default: auto-detect)
    --dry-run          Show what would be downloaded without actually downloading
    --resume           Resume from previous interrupted run
    --help             Show this help message
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ai_scholar_downloader.log')
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """Main function for AI Scholar downloader."""
    parser = argparse.ArgumentParser(
        description='AI Scholar Downloader - Download and process AI research papers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Download papers from last 7 days
    python ai_scholar_downloader.py

    # Download papers from last 30 days, max 500 papers
    python ai_scholar_downloader.py --days 30 --max-papers 500

    # Dry run to see what would be downloaded
    python ai_scholar_downloader.py --days 7 --dry-run

    # Resume interrupted download
    python ai_scholar_downloader.py --resume
        """
    )
    
    parser.add_argument(
        '--days', 
        type=int, 
        default=7,
        help='Number of days back to search for papers (default: 7)'
    )
    
    parser.add_argument(
        '--max-papers',
        type=int,
        default=100,
        help='Maximum number of papers to process (default: 100, use 0 for unlimited)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to AI Scholar config file (default: auto-detect)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be downloaded without actually downloading'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from previous interrupted run'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting AI Scholar Downloader")
    logger.info(f"Configuration: days={args.days}, max_papers={args.max_papers}, dry_run={args.dry_run}")
    
    try:
        # Import AI Scholar components
        from multi_instance_arxiv_system.downloaders.ai_scholar_downloader import AIScholarDownloader
        from multi_instance_arxiv_system.base.base_scholar_downloader import DateRange
        
        # Determine config path
        config_path = args.config
        if not config_path:
            # Try to find config file
            possible_paths = [
                "multi_instance_arxiv_system/configs/ai_scholar.yaml",
                "configs/ai_scholar.yaml",
                "../configs/ai_scholar.yaml"
            ]
            
            for path in possible_paths:
                if Path(path).exists():
                    config_path = path
                    break
            
            if not config_path:
                logger.error("Could not find AI Scholar config file. Please specify with --config")
                return 1
        
        logger.info(f"Using config file: {config_path}")
        
        # Initialize downloader
        downloader = AIScholarDownloader(config_path)
        
        # Initialize instance
        logger.info("Initializing AI Scholar instance...")
        success = await downloader.initialize_instance()
        if not success:
            logger.error("Failed to initialize AI Scholar instance")
            return 1
        
        # Determine date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        date_range = DateRange(start_date, end_date)
        
        logger.info(f"Searching for papers from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Discover papers
        logger.info("Discovering papers...")
        papers = await downloader.discover_papers(date_range)
        
        if not papers:
            logger.info("No new papers found for the specified date range")
            return 0
        
        # Limit papers if specified (0 means unlimited)
        if args.max_papers > 0 and len(papers) > args.max_papers:
            logger.info(f"Limiting to {args.max_papers} papers (found {len(papers)})")
            papers = papers[:args.max_papers]
        elif args.max_papers == 0:
            logger.info(f"Processing all {len(papers)} papers (unlimited mode)")
        
        logger.info(f"Found {len(papers)} papers to process")
        
        # Show sample papers
        for i, paper in enumerate(papers[:5]):
            logger.info(f"  {i+1}. {paper.title[:80]}... (arXiv:{paper.arxiv_id})")
        
        if len(papers) > 5:
            logger.info(f"  ... and {len(papers) - 5} more papers")
        
        if args.dry_run:
            logger.info("Dry run mode - not downloading papers")
            return 0
        
        # Download papers
        logger.info("Downloading papers...")
        download_result = await downloader.download_papers(papers)
        
        logger.info(f"Download completed: {download_result.success_count} successful, "
                   f"{download_result.failure_count} failed, {download_result.skip_count} skipped")
        
        if download_result.successful_downloads:
            # Process papers
            logger.info("Processing papers into vector store...")
            processing_result = await downloader.process_papers(download_result.successful_downloads)
            
            logger.info(f"Processing completed: {processing_result.success_count} successful, "
                       f"{processing_result.failure_count} failed")
            
            # Show summary
            total_time = processing_result.processing_time_seconds
            logger.info(f"Total processing time: {total_time:.2f} seconds")
            
            if processing_result.success_count > 0:
                rate = processing_result.success_count / (total_time / 60)  # papers per minute
                logger.info(f"Processing rate: {rate:.2f} papers per minute")
        
        # Get final stats
        stats = downloader.get_instance_stats()
        logger.info("Final statistics:")
        logger.info(f"  Instance: {stats['instance_name']}")
        logger.info(f"  Initialized: {stats['is_initialized']}")
        
        if 'progress' in stats:
            progress = stats['progress']
            logger.info(f"  Total processed: {progress.get('total_processed', 0)}")
        
        if 'errors' in stats:
            errors = stats['errors']
            logger.info(f"  Total errors: {errors.get('total_errors', 0)}")
        
        logger.info("AI Scholar download and processing completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"AI Scholar downloader failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return 1
    finally:
        # Cleanup
        try:
            if 'downloader' in locals():
                downloader.shutdown()
        except:
            pass


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)