#!/usr/bin/env python3
"""
Script 3: Monthly arXiv Update Automation

This script automatically downloads and processes new arXiv papers published
in the previous month and integrates them into the AI Scholar RAG system.

Features:
- Automated monthly execution via cron scheduling
- New paper detection for previous month
- Duplicate detection against existing papers
- Comprehensive update reporting
- Email notifications (optional)
- Storage monitoring and cleanup

Usage:
    python run_monthly_update.py [options]

Options:
    --categories: arXiv categories to update (default: all supported)
    --output-dir: Output directory for processed files
    --config-file: Configuration file for scheduling and notifications
    --dry-run: Show what would be updated without actually processing
    --setup-cron: Generate cron configuration for automated scheduling
    --verbose: Enable verbose logging
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from arxiv_rag_enhancement.processors.monthly_updater import ArxivMonthlyUpdater

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


def setup_logging(verbose: bool = False, log_file: str = None):
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
    if not log_file:
        log_file = "/datapool/aischolar/arxiv-dataset-2024/processed/error_logs/monthly_updater.log"
    
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_path)
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


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Monthly automated update of arXiv papers for AI Scholar RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Supported Categories:
{', '.join(SUPPORTED_CATEGORIES)}

Examples:
    # Run monthly update for all categories
    python run_monthly_update.py
    
    # Update specific categories only
    python run_monthly_update.py --categories cond-mat gr-qc hep-ph
    
    # Dry run to see what would be updated
    python run_monthly_update.py --dry-run
    
    # Setup cron scheduling
    python run_monthly_update.py --setup-cron
    
    # Use custom configuration
    python run_monthly_update.py --config-file /path/to/config.json
        """
    )
    
    parser.add_argument(
        '--categories',
        nargs='+',
        choices=SUPPORTED_CATEGORIES,
        default=SUPPORTED_CATEGORIES,
        help='arXiv categories to update (default: all supported categories)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='/datapool/aischolar/arxiv-dataset-2024',
        help='Output directory for processed files (default: /datapool/aischolar/arxiv-dataset-2024)'
    )
    
    parser.add_argument(
        '--config-file',
        type=str,
        default=None,
        help='Configuration file for scheduling and notifications'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without actually processing'
    )
    
    parser.add_argument(
        '--setup-cron',
        action='store_true',
        help='Generate cron configuration for automated scheduling'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force update even if not scheduled to run'
    )
    
    parser.add_argument(
        '--cleanup-only',
        action='store_true',
        help='Only perform cleanup of old data, no paper processing'
    )
    
    return parser.parse_args()


async def main():
    """Main processing function."""
    args = parse_arguments()
    
    # Set up logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    print("🗓️  AI Scholar Monthly arXiv Updater")
    print("=" * 60)
    print(f"Categories: {', '.join(args.categories)}")
    print(f"Output Directory: {args.output_dir}")
    print(f"Mode: {'Dry Run' if args.dry_run else 'Full Update'}")
    print("=" * 60)
    
    try:
        # Create updater
        updater = ArxivMonthlyUpdater(
            categories=args.categories,
            output_dir=args.output_dir
        )
        
        # Setup cron mode
        if args.setup_cron:
            print("\n⚙️  Setting up cron scheduling...")
            
            success = await updater.setup_scheduling()
            
            if success:
                print("✅ Cron setup completed!")
                print(f"📁 Configuration saved to: {updater.config_dir}")
                print("\nTo enable automated updates:")
                print("1. Review the generated cron configuration")
                print("2. Add the cron line to your crontab (crontab -e)")
                print("3. Optionally configure email notifications in the config file")
                
                # Show current status
                status = updater.get_status()
                print(f"\n📊 Next scheduled run: {status['next_run_time']}")
                
            else:
                print("❌ Cron setup failed")
            
            return
        
        # Cleanup only mode
        if args.cleanup_only:
            print("\n🧹 Running cleanup of old data...")
            success = await updater.cleanup_old_data()
            
            if success:
                print("✅ Cleanup completed successfully")
            else:
                print("❌ Cleanup failed")
            
            return
        
        # Check if update should run (unless forced)
        if not args.force and not args.dry_run:
            if not updater.schedule_manager.should_run_now():
                next_run = updater.schedule_manager.get_next_run_time()
                print(f"⏰ Not scheduled to run now. Next run: {next_run}")
                print("Use --force to run anyway, or --dry-run to see what would be processed")
                return
        
        # Get previous month date range for display
        from arxiv_rag_enhancement.processors.monthly_updater import NewPaperDetector
        detector = NewPaperDetector(args.categories)
        start_date, end_date = detector.get_previous_month_range()
        
        print(f"\n📅 Processing papers from: {start_date.date()} to {end_date.date()}")
        
        # Dry run mode
        if args.dry_run:
            print("🔍 DRY RUN MODE - No papers will be downloaded or processed")
            
            # Create a temporary downloader to discover papers
            from arxiv_rag_enhancement.processors.bulk_downloader import ArxivBulkDownloader
            
            temp_downloader = ArxivBulkDownloader(
                categories=args.categories,
                start_date=start_date,
                output_dir=args.output_dir
            )
            
            # Update date filter
            temp_downloader.date_filter.start_date = start_date
            temp_downloader.date_filter.end_date = end_date
            
            print("📡 Discovering papers...")
            papers = await temp_downloader.discover_papers()
            
            if papers:
                print(f"📊 Would process {len(papers)} new papers:")
                
                # Show sample papers
                for i, paper in enumerate(papers[:5]):
                    print(f"  {i+1}. {paper.title[:80]}...")
                    print(f"     ID: {paper.arxiv_id}, Categories: {', '.join(paper.categories[:3])}")
                
                if len(papers) > 5:
                    print(f"  ... and {len(papers) - 5} more papers")
                
                # Estimate storage
                estimated_size_mb = len(papers) * 2  # ~2MB per paper
                print(f"📊 Estimated storage needed: ~{estimated_size_mb} MB")
                
            else:
                print("📭 No new papers found for the previous month")
            
            return
        
        # Run monthly update
        print(f"\n🔄 Starting monthly update...")
        start_time = datetime.now()
        
        report = await updater.run_monthly_update()
        
        total_time = datetime.now() - start_time
        
        # Display results
        print("\n" + "=" * 60)
        print("MONTHLY UPDATE COMPLETE")
        print("=" * 60)
        
        if report.papers_discovered > 0:
            print(f"📡 Papers Discovered: {report.papers_discovered}")
            print(f"⬇️  Papers Downloaded: {report.papers_downloaded}")
            print(f"🔄 Papers Processed: {report.papers_processed}")
            print(f"❌ Papers Failed: {report.papers_failed}")
            print(f"📊 Storage Used: {report.storage_used // (1024 * 1024)} MB")
            print(f"⏱️  Processing Time: {report.processing_time:.1f} seconds")
            print(f"📈 Success Rate: {(report.papers_processed / report.papers_discovered * 100):.1f}%" if report.papers_discovered > 0 else "N/A")
            
            if report.duplicate_papers_skipped > 0:
                print(f"🔄 Duplicate Papers Skipped: {report.duplicate_papers_skipped}")
            
            if report.errors:
                print(f"⚠️  Errors Encountered: {len(report.errors)}")
                print("📋 Check the detailed report for error information")
            
            # Get updated collection stats
            try:
                from services.vector_store_service import vector_store_service
                collection_stats = await vector_store_service.get_collection_stats()
                print(f"📚 Updated Collection: {collection_stats.get('total_chunks', 0)} chunks from {collection_stats.get('document_count', 0)} documents")
            except Exception as e:
                logger.warning(f"Could not get updated collection stats: {e}")
            
            print(f"\n✅ {report.summary}")
            
            if report.papers_processed > 0:
                print("\n🎉 Your AI Scholar chatbot has been updated with the latest research!")
            
        else:
            print("📭 No new papers found for the previous month")
            print("✅ System is up to date")
        
        # Show report location
        report_file = updater.report_generator.reports_dir / f"monthly_update_{report.update_date.strftime('%Y%m%d_%H%M%S')}.json"
        if report_file.exists():
            print(f"📋 Detailed report saved to: {report_file}")
        
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n⏸️  Update interrupted by user")
        logger.info("Monthly update interrupted by user")
        
    except Exception as e:
        logger.error(f"Monthly update failed: {e}", exc_info=True)
        print(f"❌ Monthly update failed: {e}")
        print("Check the logs for detailed error information")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())