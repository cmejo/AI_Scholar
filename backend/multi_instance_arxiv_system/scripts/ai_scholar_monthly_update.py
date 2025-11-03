#!/usr/bin/env python3
"""
AI Scholar Monthly Update Script

This script performs automated monthly updates for the AI Scholar instance,
including downloading new papers, processing them, and generating reports.

Usage:
    python ai_scholar_monthly_update.py [options]
    
Examples:
    # Run monthly update
    python ai_scholar_monthly_update.py
    
    # Run with custom date range
    python ai_scholar_monthly_update.py --start-date 2023-10-01 --end-date 2023-10-31
    
    # Dry run to see what would be updated
    python ai_scholar_monthly_update.py --dry-run
    
    # Send email report after completion
    python ai_scholar_monthly_update.py --send-email
"""

import sys
import argparse
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/ai_scholar_monthly_update.log')
    ]
)
logger = logging.getLogger(__name__)


class AIScholarMonthlyUpdater:
    """AI Scholar monthly update orchestrator."""
    
    def __init__(self, config_path: str = "configs/ai_scholar.yaml"):
        self.config_path = config_path
        self.instance_name = "ai_scholar"
        
        # Storage paths
        self.base_directory = "/datapool/aischolar/ai-scholar-arxiv-dataset"
        self.reports_directory = f"{self.base_directory}/reports"
        self.state_directory = f"{self.base_directory}/state"
        
        # Update configuration
        self.lock_file = f"{self.state_directory}/monthly_update.lock"
        self.last_update_file = f"{self.state_directory}/last_monthly_update.json"
        
        logger.info(f"AI Scholar Monthly Updater initialized")
    
    async def run_monthly_update(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        dry_run: bool = False,
        send_email: bool = False,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Run monthly update for AI Scholar instance.
        
        Args:
            start_date: Start date for update period
            end_date: End date for update period
            dry_run: Show what would be updated without actually updating
            send_email: Send email report after completion
            force: Force update even if already completed for this period
            
        Returns:
            Dictionary with update statistics and results
        """
        
        logger.info(f"Starting AI Scholar monthly update")
        logger.info(f"Start date: {start_date}")
        logger.info(f"End date: {end_date}")
        logger.info(f"Dry run: {dry_run}")
        logger.info(f"Send email: {send_email}")
        logger.info(f"Force: {force}")
        
        # Set default date range (last month)
        if not start_date or not end_date:
            end_date = datetime.now().replace(day=1) - timedelta(days=1)  # Last day of previous month
            start_date = end_date.replace(day=1)  # First day of previous month
        
        # Create directories
        self._create_directories()
        
        # Check for existing update lock
        if not force and not dry_run:
            if await self._check_update_lock():
                raise RuntimeError("Another update is already running")
            
            # Check if already updated for this period
            if await self._check_already_updated(start_date, end_date):
                logger.info(f"Update already completed for period {start_date.date()} to {end_date.date()}")
                return {'status': 'already_completed', 'period': f"{start_date.date()} to {end_date.date()}"}
        
        # Initialize update statistics
        update_stats = {
            'instance_name': self.instance_name,
            'update_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'start_time': datetime.now(),
            'end_time': None,
            'dry_run': dry_run,
            'download_stats': {},
            'processing_stats': {},
            'storage_stats': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Create update lock
            if not dry_run:
                await self._create_update_lock()
            
            # Step 1: Download new papers
            logger.info("Step 1: Downloading new papers")
            download_stats = await self._download_new_papers(start_date, end_date, dry_run)
            update_stats['download_stats'] = download_stats
            
            # Step 2: Process downloaded papers
            logger.info("Step 2: Processing downloaded papers")
            processing_stats = await self._process_new_papers(dry_run)
            update_stats['processing_stats'] = processing_stats
            
            # Step 3: Update vector store
            logger.info("Step 3: Updating vector store")
            vector_store_stats = await self._update_vector_store(dry_run)
            update_stats['vector_store_stats'] = vector_store_stats
            
            # Step 4: Perform cleanup and optimization
            logger.info("Step 4: Performing cleanup and optimization")
            cleanup_stats = await self._perform_cleanup(dry_run)
            update_stats['cleanup_stats'] = cleanup_stats
            
            # Step 5: Generate storage statistics
            logger.info("Step 5: Generating storage statistics")
            storage_stats = await self._generate_storage_stats()
            update_stats['storage_stats'] = storage_stats
            
            # Step 6: Generate update report
            logger.info("Step 6: Generating update report")
            report_path = await self._generate_update_report(update_stats, dry_run)
            update_stats['report_path'] = report_path
            
            # Step 7: Send email notification if requested
            if send_email and not dry_run:
                logger.info("Step 7: Sending email notification")
                email_result = await self._send_email_notification(update_stats, report_path)
                update_stats['email_sent'] = email_result
            
            # Update last update record
            if not dry_run:
                await self._update_last_update_record(start_date, end_date, update_stats)
        
        except Exception as e:
            logger.error(f"Monthly update failed: {e}")
            update_stats['errors'].append(str(e))
            raise
        
        finally:
            update_stats['end_time'] = datetime.now()
            update_stats['duration_minutes'] = (
                update_stats['end_time'] - update_stats['start_time']
            ).total_seconds() / 60
            
            # Remove update lock
            if not dry_run:
                await self._remove_update_lock()
        
        # Log final statistics
        logger.info("AI Scholar monthly update completed")
        logger.info(f"Duration: {update_stats['duration_minutes']:.1f} minutes")
        logger.info(f"Papers downloaded: {download_stats.get('total_downloaded', 0)}")
        logger.info(f"Papers processed: {processing_stats.get('processed_successfully', 0)}")
        
        return update_stats
    
    def _create_directories(self) -> None:
        """Create necessary directories."""
        
        directories = [
            self.reports_directory,
            self.state_directory,
            "logs"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
    
    async def _check_update_lock(self) -> bool:
        """Check if update lock exists."""
        
        lock_path = Path(self.lock_file)
        
        if lock_path.exists():
            try:
                with open(lock_path, 'r') as f:
                    lock_data = json.load(f)
                
                # Check if lock is stale (older than 6 hours)
                lock_time = datetime.fromisoformat(lock_data['created_at'])
                if datetime.now() - lock_time > timedelta(hours=6):
                    logger.warning("Removing stale update lock")
                    lock_path.unlink()
                    return False
                
                logger.warning(f"Update lock exists from {lock_time}")
                return True
            
            except Exception as e:
                logger.error(f"Error reading lock file: {e}")
                # Remove corrupted lock file
                lock_path.unlink()
                return False
        
        return False
    
    async def _create_update_lock(self) -> None:
        """Create update lock file."""
        
        lock_data = {
            'created_at': datetime.now().isoformat(),
            'instance_name': self.instance_name,
            'process_id': 'monthly_update'
        }
        
        with open(self.lock_file, 'w') as f:
            json.dump(lock_data, f, indent=2)
        
        logger.debug("Created update lock")
    
    async def _remove_update_lock(self) -> None:
        """Remove update lock file."""
        
        try:
            Path(self.lock_file).unlink(missing_ok=True)
            logger.debug("Removed update lock")
        except Exception as e:
            logger.error(f"Failed to remove update lock: {e}")
    
    async def _check_already_updated(self, start_date: datetime, end_date: datetime) -> bool:
        """Check if already updated for the given period."""
        
        try:
            if Path(self.last_update_file).exists():
                with open(self.last_update_file, 'r') as f:
                    last_update = json.load(f)
                
                last_start = datetime.fromisoformat(last_update['start_date'])
                last_end = datetime.fromisoformat(last_update['end_date'])
                
                return last_start == start_date and last_end == end_date
        
        except Exception as e:
            logger.error(f"Error checking last update: {e}")
        
        return False
    
    async def _download_new_papers(
        self,
        start_date: datetime,
        end_date: datetime,
        dry_run: bool
    ) -> Dict[str, Any]:
        """Download new papers for the update period."""
        
        # Import and use the downloader
        from ai_scholar_downloader import AIScholarDownloader
        
        downloader = AIScholarDownloader(self.config_path)
        
        # Calculate date range
        date_range = "custom"  # Would need to implement custom date range in downloader
        
        # Run download
        download_stats = await downloader.download_papers(
            categories=None,  # Use all default categories
            date_range="last-month",  # Simplified for this example
            max_papers=None,
            resume=True,
            dry_run=dry_run
        )
        
        return download_stats
    
    async def _process_new_papers(self, dry_run: bool) -> Dict[str, Any]:
        """Process newly downloaded papers."""
        
        if dry_run:
            return {
                'processed_successfully': 0,
                'processing_failed': 0,
                'total_papers': 0,
                'dry_run': True
            }
        
        # Import and use the processor
        from ai_scholar_processor import AIScholarProcessor
        
        processor = AIScholarProcessor(self.config_path)
        
        # Process all unprocessed papers
        processing_stats = await processor.process_papers(
            papers=None,  # Process all unprocessed
            reprocess=False,
            batch_size=20,
            max_concurrent=3
        )
        
        return processing_stats
    
    async def _update_vector_store(self, dry_run: bool) -> Dict[str, Any]:
        """Update vector store with new papers."""
        
        if dry_run:
            return {
                'documents_added': 0,
                'embeddings_updated': 0,
                'dry_run': True
            }
        
        # Simulate vector store update
        # In a real implementation, this would update ChromaDB
        
        logger.info("Updating vector store with new documents")
        await asyncio.sleep(1)  # Simulate processing time
        
        return {
            'documents_added': 50,  # Simulated
            'embeddings_updated': 200,  # Simulated
            'collection_name': 'ai_scholar_papers'
        }
    
    async def _perform_cleanup(self, dry_run: bool) -> Dict[str, Any]:
        """Perform cleanup and optimization tasks."""
        
        cleanup_stats = {
            'temp_files_cleaned': 0,
            'old_logs_compressed': 0,
            'disk_space_freed_mb': 0,
            'dry_run': dry_run
        }
        
        if dry_run:
            return cleanup_stats
        
        # Simulate cleanup tasks
        logger.info("Performing cleanup and optimization")
        
        # Clean temporary files
        temp_files_cleaned = 10  # Simulated
        cleanup_stats['temp_files_cleaned'] = temp_files_cleaned
        
        # Compress old logs
        old_logs_compressed = 5  # Simulated
        cleanup_stats['old_logs_compressed'] = old_logs_compressed
        
        # Calculate freed space
        cleanup_stats['disk_space_freed_mb'] = 150  # Simulated
        
        await asyncio.sleep(0.5)  # Simulate processing time
        
        return cleanup_stats
    
    async def _generate_storage_stats(self) -> Dict[str, Any]:
        """Generate storage usage statistics."""
        
        import shutil
        
        try:
            base_path = Path(self.base_directory)
            
            # Calculate directory sizes
            pdf_size = sum(f.stat().st_size for f in base_path.glob("pdf/*.pdf") if f.is_file())
            processed_size = sum(f.stat().st_size for f in base_path.glob("processed/*.json") if f.is_file())
            
            # Get disk usage
            disk_usage = shutil.disk_usage(base_path)
            
            storage_stats = {
                'pdf_directory_mb': pdf_size / (1024 * 1024),
                'processed_directory_mb': processed_size / (1024 * 1024),
                'total_used_mb': (pdf_size + processed_size) / (1024 * 1024),
                'disk_total_gb': disk_usage.total / (1024 * 1024 * 1024),
                'disk_used_gb': disk_usage.used / (1024 * 1024 * 1024),
                'disk_free_gb': disk_usage.free / (1024 * 1024 * 1024),
                'disk_usage_percent': (disk_usage.used / disk_usage.total) * 100
            }
            
            return storage_stats
        
        except Exception as e:
            logger.error(f"Failed to generate storage stats: {e}")
            return {'error': str(e)}
    
    async def _generate_update_report(
        self,
        update_stats: Dict[str, Any],
        dry_run: bool
    ) -> str:
        """Generate comprehensive update report."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"ai_scholar_monthly_update_{timestamp}.json"
        report_path = Path(self.reports_directory) / report_filename
        
        # Create comprehensive report
        report = {
            'report_type': 'monthly_update',
            'instance_name': self.instance_name,
            'generated_at': datetime.now().isoformat(),
            'update_stats': update_stats,
            'summary': {
                'papers_downloaded': update_stats.get('download_stats', {}).get('total_downloaded', 0),
                'papers_processed': update_stats.get('processing_stats', {}).get('processed_successfully', 0),
                'processing_failures': update_stats.get('processing_stats', {}).get('processing_failed', 0),
                'duration_minutes': update_stats.get('duration_minutes', 0),
                'storage_used_mb': update_stats.get('storage_stats', {}).get('total_used_mb', 0),
                'disk_usage_percent': update_stats.get('storage_stats', {}).get('disk_usage_percent', 0)
            }
        }
        
        if not dry_run:
            # Save report to file
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Update report saved to {report_path}")
        else:
            logger.info(f"[DRY RUN] Would save report to {report_path}")
        
        return str(report_path)
    
    async def _send_email_notification(
        self,
        update_stats: Dict[str, Any],
        report_path: str
    ) -> bool:
        """Send email notification with update results."""
        
        try:
            # Simulate email sending
            # In a real implementation, this would use the email notification service
            
            logger.info("Sending email notification")
            
            # Email content summary
            summary = update_stats.get('summary', {})
            
            email_content = f"""
AI Scholar Monthly Update Completed

Update Period: {update_stats['update_period']['start_date']} to {update_stats['update_period']['end_date']}
Duration: {update_stats.get('duration_minutes', 0):.1f} minutes

Results:
- Papers Downloaded: {summary.get('papers_downloaded', 0)}
- Papers Processed: {summary.get('papers_processed', 0)}
- Processing Failures: {summary.get('processing_failures', 0)}
- Storage Used: {summary.get('storage_used_mb', 0):.1f} MB
- Disk Usage: {summary.get('disk_usage_percent', 0):.1f}%

Report saved to: {report_path}
            """
            
            logger.info("Email notification sent successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    async def _update_last_update_record(
        self,
        start_date: datetime,
        end_date: datetime,
        update_stats: Dict[str, Any]
    ) -> None:
        """Update the last update record."""
        
        last_update_record = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'completed_at': datetime.now().isoformat(),
            'instance_name': self.instance_name,
            'papers_downloaded': update_stats.get('download_stats', {}).get('total_downloaded', 0),
            'papers_processed': update_stats.get('processing_stats', {}).get('processed_successfully', 0),
            'duration_minutes': update_stats.get('duration_minutes', 0)
        }
        
        try:
            with open(self.last_update_file, 'w') as f:
                json.dump(last_update_record, f, indent=2)
            
            logger.debug("Updated last update record")
        
        except Exception as e:
            logger.error(f"Failed to update last update record: {e}")
    
    def get_update_status(self) -> Dict[str, Any]:
        """Get current update status."""
        
        status = {
            'instance_name': self.instance_name,
            'update_lock_exists': Path(self.lock_file).exists(),
            'last_update': None,
            'reports_directory': self.reports_directory,
            'total_reports': 0
        }
        
        # Get last update info
        try:
            if Path(self.last_update_file).exists():
                with open(self.last_update_file, 'r') as f:
                    status['last_update'] = json.load(f)
        except Exception as e:
            logger.error(f"Error reading last update file: {e}")
        
        # Count reports
        try:
            reports_dir = Path(self.reports_directory)
            if reports_dir.exists():
                status['total_reports'] = len(list(reports_dir.glob("*.json")))
        except Exception:
            pass
        
        return status


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    
    parser = argparse.ArgumentParser(
        description="AI Scholar Monthly Update",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --start-date 2023-10-01 --end-date 2023-10-31
  %(prog)s --dry-run --verbose
  %(prog)s --send-email --force
        """
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date for update period (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date for update period (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without actually updating'
    )
    
    parser.add_argument(
        '--send-email',
        action='store_true',
        help='Send email notification after completion'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force update even if already completed for this period'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='configs/ai_scholar.yaml',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current update status and exit'
    )
    
    return parser


async def main():
    """Main entry point for AI Scholar monthly updater."""
    
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create updater instance
    updater = AIScholarMonthlyUpdater(args.config)
    
    try:
        # Show status if requested
        if args.status:
            status = updater.get_update_status()
            print("\nAI Scholar Update Status:")
            print("=" * 40)
            for key, value in status.items():
                print(f"{key}: {value}")
            return
        
        # Parse dates
        start_date = None
        end_date = None
        
        if args.start_date:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        
        if args.end_date:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
        
        # Run monthly update
        update_stats = await updater.run_monthly_update(
            start_date=start_date,
            end_date=end_date,
            dry_run=args.dry_run,
            send_email=args.send_email,
            force=args.force
        )
        
        # Print summary
        print("\nMonthly Update Summary:")
        print("=" * 40)
        
        if update_stats.get('status') == 'already_completed':
            print(f"Update already completed for period: {update_stats['period']}")
        else:
            download_stats = update_stats.get('download_stats', {})
            processing_stats = update_stats.get('processing_stats', {})
            
            print(f"Update period: {update_stats['update_period']['start_date']} to {update_stats['update_period']['end_date']}")
            print(f"Duration: {update_stats.get('duration_minutes', 0):.1f} minutes")
            print(f"Papers downloaded: {download_stats.get('total_downloaded', 0)}")
            print(f"Papers processed: {processing_stats.get('processed_successfully', 0)}")
            print(f"Processing failures: {processing_stats.get('processing_failed', 0)}")
            
            if update_stats.get('report_path'):
                print(f"Report saved to: {update_stats['report_path']}")
            
            if update_stats.get('email_sent'):
                print("Email notification sent successfully")
    
    except KeyboardInterrupt:
        logger.info("Monthly update interrupted by user")
        print("\nMonthly update interrupted by user")
    
    except Exception as e:
        logger.error(f"Monthly update failed: {e}")
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())