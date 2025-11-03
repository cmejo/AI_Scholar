#!/usr/bin/env python3
"""
AI Scholar Monthly Update Script

Entry point script for running automated monthly updates for AI Scholar.
Downloads and processes papers from the previous month.

Usage:
    python ai_scholar_monthly_update.py [options]

Options:
    --month YYYY-MM     Specific month to process (default: previous month)
    --config PATH       Path to AI Scholar config file (default: auto-detect)
    --max-papers NUM    Maximum number of papers to process (default: 1000)
    --email             Send email report after completion
    --cleanup           Run cleanup of old files after processing
    --help              Show this help message
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
import calendar

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ai_scholar_monthly_update.log')
    ]
)
logger = logging.getLogger(__name__)


def parse_month(month_str: str) -> tuple:
    """Parse month string into year and month."""
    try:
        year, month = map(int, month_str.split('-'))
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
        return year, month
    except ValueError as e:
        raise ValueError(f"Invalid month format '{month_str}'. Use YYYY-MM format.") from e


def get_month_date_range(year: int, month: int) -> tuple:
    """Get start and end dates for a given month."""
    start_date = datetime(year, month, 1)
    
    # Get last day of month
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime(year, month, last_day, 23, 59, 59)
    
    return start_date, end_date


async def main():
    """Main function for AI Scholar monthly update."""
    parser = argparse.ArgumentParser(
        description='AI Scholar Monthly Update - Automated monthly paper processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Process previous month
    python ai_scholar_monthly_update.py

    # Process specific month
    python ai_scholar_monthly_update.py --month 2024-10

    # Process with email report and cleanup
    python ai_scholar_monthly_update.py --email --cleanup

    # Process with custom limits
    python ai_scholar_monthly_update.py --max-papers 2000
        """
    )
    
    parser.add_argument(
        '--month',
        type=str,
        help='Specific month to process in YYYY-MM format (default: previous month)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to AI Scholar config file (default: auto-detect)'
    )
    
    parser.add_argument(
        '--max-papers',
        type=int,
        default=1000,
        help='Maximum number of papers to process (default: 1000)'
    )
    
    parser.add_argument(
        '--email',
        action='store_true',
        help='Send email report after completion'
    )
    
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Run cleanup of old files after processing'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine target month
    if args.month:
        try:
            year, month = parse_month(args.month)
            target_date = datetime(year, month, 15)  # Mid-month for reference
        except ValueError as e:
            logger.error(f"Invalid month specification: {e}")
            return 1
    else:
        # Previous month
        today = datetime.now()
        if today.month == 1:
            target_date = datetime(today.year - 1, 12, 15)
        else:
            target_date = datetime(today.year, today.month - 1, 15)
    
    start_date, end_date = get_month_date_range(target_date.year, target_date.month)
    
    logger.info("Starting AI Scholar Monthly Update")
    logger.info(f"Target month: {target_date.strftime('%Y-%m')} ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
    logger.info(f"Configuration: max_papers={args.max_papers}, email={args.email}, cleanup={args.cleanup}")
    
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
        
        # Run monthly update
        logger.info("Running monthly update...")
        update_start_time = datetime.now()
        
        try:
            update_report = await downloader.run_monthly_update(target_date)
            
            processing_time = (datetime.now() - update_start_time).total_seconds()
            
            # Log summary
            logger.info("Monthly update completed successfully!")
            logger.info(f"Processing time: {processing_time:.2f} seconds")
            logger.info(f"Papers discovered: {update_report.papers_discovered}")
            logger.info(f"Papers downloaded: {update_report.papers_downloaded}")
            logger.info(f"Papers processed: {update_report.papers_processed}")
            logger.info(f"Papers failed: {update_report.papers_failed}")
            logger.info(f"Storage used: {update_report.storage_used_mb} MB")
            
            if update_report.duplicate_papers_skipped > 0:
                logger.info(f"Duplicate papers skipped: {update_report.duplicate_papers_skipped}")
            
            # Show error summary if any
            if update_report.errors:
                logger.warning(f"Errors encountered: {len(update_report.errors)}")
                for error in update_report.errors[:3]:  # Show first 3 errors
                    logger.warning(f"  - {error.error_type}: {error.error_message[:100]}...")
                if len(update_report.errors) > 3:
                    logger.warning(f"  ... and {len(update_report.errors) - 3} more errors")
            
            # Performance metrics
            if update_report.performance_metrics:
                metrics = update_report.performance_metrics
                logger.info("Performance metrics:")
                logger.info(f"  Download rate: {metrics.download_rate_mbps:.2f} MB/s")
                logger.info(f"  Processing rate: {metrics.processing_rate_papers_per_hour:.2f} papers/hour")
                logger.info(f"  Error rate: {metrics.error_rate_percentage:.2f}%")
            
            # Storage statistics
            if update_report.storage_stats:
                storage = update_report.storage_stats
                logger.info("Storage statistics:")
                logger.info(f"  Total space: {storage.total_space_gb:.2f} GB")
                logger.info(f"  Used space: {storage.used_space_gb:.2f} GB")
                logger.info(f"  Usage: {storage.usage_percentage:.1f}%")
            
            # Cleanup if requested
            if args.cleanup:
                logger.info("Running cleanup...")
                cleanup_stats = await downloader.cleanup_old_files(retention_days=30)
                logger.info(f"Cleanup completed: {cleanup_stats['files_removed']} files removed, "
                           f"{cleanup_stats['space_freed_mb']:.2f} MB freed")
            
            # Email report if requested
            if args.email:
                logger.info("Sending email report...")
                # TODO: Implement email reporting
                logger.warning("Email reporting not yet implemented")
            
            return 0
            
        except Exception as e:
            logger.error(f"Monthly update failed: {e}")
            
            # Try to get error summary
            if hasattr(downloader, 'ai_error_handler') and downloader.ai_error_handler:
                try:
                    error_summary = downloader.ai_error_handler.get_ai_scholar_error_summary()
                    logger.error("Error summary:")
                    logger.error(f"  Health status: {error_summary.get('health_status', 'unknown')}")
                    logger.error(f"  Total errors: {error_summary.get('ai_scholar_stats', {}).get('consecutive_failures', 0)}")
                    
                    recommendations = error_summary.get('recommendations', [])
                    if recommendations:
                        logger.error("Recommendations:")
                        for rec in recommendations[:3]:
                            logger.error(f"  - {rec}")
                except Exception:
                    pass
            
            raise
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"AI Scholar monthly update failed: {e}")
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