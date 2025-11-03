#!/usr/bin/env python3
"""
Script 2: Bulk arXiv Paper Downloader and Processor

This script downloads and processes recent arXiv papers from specific scientific
categories using arXiv's bulk data access and integrates them into the AI Scholar RAG system.

Features:
- arXiv API integration for paper discovery
- Google Cloud Storage bulk download support
- Category and date range filtering
- Duplicate detection and resume functionality
- Real-time progress tracking
- Integration with existing ChromaDB vector store

Usage:
    python download_bulk_arxiv_papers.py [options]

Options:
    --categories: arXiv categories to download (default: all supported)
    --start-date: Start date for paper search (default: 2024-07-01)
    --end-date: End date for paper search (default: now)
    --output-dir: Output directory for downloaded files
    --max-papers: Maximum number of papers to process
    --verbose: Enable verbose logging
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from arxiv_rag_enhancement.processors.bulk_downloader import ArxivBulkDownloader

# Supported arXiv categories
SUPPORTED_CATEGORIES = [
    'cond-mat',  # Condensed Matter
    'gr-qc',     # General Relativity and Quantum Cosmology
    'hep-ph',    # High Energy Physics - Phenomenology
    'hep-th',    # High Energy Physics - Theory
    'math',      # Mathematics
    'math-ph',   # Mathematical Physics
    'physics',   # Physics
    'q-alg',     # Quantum Algebra
    'quant-ph'   # Quantum Physics
]


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # File handler
    log_file = Path("/datapool/aischolar/arxiv-dataset-2024/processed/error_logs/bulk_downloader.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Reduce noise from some libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)


def parse_date(date_str: str) -> datetime:
    """Parse date string in various formats."""
    formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y-%m-%d %H:%M:%S']
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Invalid date format: {date_str}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download and process bulk arXiv papers for AI Scholar RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Supported Categories:
{', '.join(SUPPORTED_CATEGORIES)}

Examples:
    # Download all categories since July 2024
    python download_bulk_arxiv_papers.py
    
    # Download specific categories
    python download_bulk_arxiv_papers.py --categories cond-mat gr-qc hep-ph
    
    # Download papers from specific date range
    python download_bulk_arxiv_papers.py --start-date 2024-08-01 --end-date 2024-09-01
    
    # Limit number of papers and use verbose logging
    python download_bulk_arxiv_papers.py --max-papers 100 --verbose
        """
    )
    
    parser.add_argument(
        '--categories',
        nargs='+',
        choices=SUPPORTED_CATEGORIES,
        default=SUPPORTED_CATEGORIES,
        help='arXiv categories to download (default: all supported categories)'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        default='2024-07-01',
        help='Start date for paper search (YYYY-MM-DD format, default: 2024-07-01)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        default=None,
        help='End date for paper search (YYYY-MM-DD format, default: now)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='/datapool/aischolar/arxiv-dataset-2024',
        help='Output directory for downloaded files (default: /datapool/aischolar/arxiv-dataset-2024)'
    )
    
    parser.add_argument(
        '--max-papers',
        type=int,
        default=None,
        help='Maximum number of papers to process (default: no limit)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be downloaded without actually downloading'
    )
    
    parser.add_argument(
        '--discovery-only',
        action='store_true',
        help='Only discover papers, do not download or process'
    )
    
    parser.add_argument(
        '--download-only',
        action='store_true',
        help='Only download papers, do not process into RAG system'
    )
    
    return parser.parse_args()


async def main():
    """Main processing function."""
    args = parse_arguments()
    
    # Set up logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Parse dates
    try:
        start_date = parse_date(args.start_date)
        end_date = parse_date(args.end_date) if args.end_date else datetime.now()
    except ValueError as e:
        print(f"❌ Date parsing error: {e}")
        return
    
    print("🚀 AI Scholar Bulk arXiv Paper Downloader")
    print("=" * 60)
    print(f"Categories: {', '.join(args.categories)}")
    print(f"Date Range: {start_date.date()} to {end_date.date()}")
    print(f"Output Directory: {args.output_dir}")
    print(f"Max Papers: {args.max_papers or 'No limit'}")
    print(f"Mode: {'Dry Run' if args.dry_run else 'Full Processing'}")
    print("=" * 60)
    
    try:
        # Create downloader
        downloader = ArxivBulkDownloader(
            categories=args.categories,
            start_date=start_date,
            output_dir=args.output_dir
        )
        
        # Step 1: Discover papers
        print("\n📡 Discovering papers from arXiv API...")
        papers = await downloader.discover_papers()
        
        if not papers:
            print("❌ No papers found matching criteria")
            return
        
        # Limit papers if requested
        if args.max_papers and len(papers) > args.max_papers:
            papers = papers[:args.max_papers]
            print(f"📊 Limited to first {args.max_papers} papers")
        
        print(f"✅ Discovered {len(papers)} papers to process")
        
        # Show sample papers
        print(f"\nSample papers:")
        for i, paper in enumerate(papers[:5]):
            print(f"  {i+1}. {paper.title[:80]}...")
            print(f"     ID: {paper.arxiv_id}, Categories: {', '.join(paper.categories[:3])}")
        
        if len(papers) > 5:
            print(f"  ... and {len(papers) - 5} more papers")
        
        # Dry run mode
        if args.dry_run:
            print(f"\n🔍 DRY RUN MODE - No files will be downloaded or processed")
            
            # Calculate estimated download size (rough estimate)
            estimated_size_mb = len(papers) * 2  # Assume ~2MB per paper
            print(f"📊 Estimated download size: ~{estimated_size_mb} MB")
            
            return
        
        # Discovery only mode
        if args.discovery_only:
            print(f"\n📋 DISCOVERY ONLY MODE - Papers discovered and metadata saved")
            return
        
        # Confirm processing
        response = input(f"\nProceed with downloading {len(papers)} papers? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Processing cancelled")
            return
        
        # Step 2: Download papers
        print(f"\n⬇️  Downloading {len(papers)} papers...")
        start_time = datetime.now()
        
        downloaded_files = await downloader.download_papers(papers)
        
        download_time = datetime.now() - start_time
        print(f"✅ Downloaded {len(downloaded_files)} papers in {download_time}")
        
        if not downloaded_files:
            print("❌ No papers were downloaded successfully")
            return
        
        # Download only mode
        if args.download_only:
            print(f"\n📁 DOWNLOAD ONLY MODE - Papers downloaded to {args.output_dir}")
            return
        
        # Step 3: Process papers into RAG system
        print(f"\n🔄 Processing {len(downloaded_files)} papers into RAG system...")
        
        processing_start = datetime.now()
        success = await downloader.process_downloaded_papers(downloaded_files)
        processing_time = datetime.now() - processing_start
        
        # Display final results
        total_time = datetime.now() - start_time
        stats = downloader.get_download_stats()
        
        print("\n" + "=" * 60)
        print("PROCESSING COMPLETE")
        print("=" * 60)
        
        if success:
            print("🎉 Processing completed successfully!")
            print(f"✅ Papers discovered: {stats['discovered_papers']}")
            print(f"⬇️  Papers downloaded: {stats['downloaded_papers']}")
            print(f"🔄 Papers processed: {stats['processed_papers']}")
            print(f"❌ Papers failed: {stats['failed_papers']}")
            print(f"⏱️  Total time: {total_time}")
            print(f"📊 Success rate: {(stats['processed_papers'] / len(papers) * 100):.1f}%" if len(papers) > 0 else "N/A")
            
            if stats['failed_papers'] > 0:
                print(f"📋 Error details available in: {downloader.error_log_dir}")
            
            # Get updated collection stats
            try:
                from services.vector_store_service import vector_store_service
                collection_stats = await vector_store_service.get_collection_stats()
                print(f"📚 Updated collection: {collection_stats.get('total_chunks', 0)} chunks from {collection_stats.get('document_count', 0)} documents")
            except Exception as e:
                logger.warning(f"Could not get updated collection stats: {e}")
            
            print("\nYour AI Scholar chatbot now has enhanced knowledge from the latest arXiv papers!")
            
        else:
            print("❌ Processing failed")
            print("Check the logs for detailed error information")
        
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n⏸️  Processing interrupted by user")
        logger.info("Processing interrupted by user")
        print("You can run the script again to resume from where it left off.")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"❌ Unexpected error: {e}")
        print("Check the logs for detailed error information")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())