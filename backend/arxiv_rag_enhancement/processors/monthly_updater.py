"""
Monthly arXiv Updater for arXiv RAG Enhancement system.

Automated monthly updates of new arXiv papers, with support for:
- Scheduled execution via cron or similar
- New paper detection for previous month
- Integration with existing duplicate detection
- Comprehensive update reporting
- Storage monitoring and cleanup
"""

import asyncio
import logging
import sys
import smtplib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import shutil

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from ..shared import (
    StateManager, 
    ProgressTracker, 
    ErrorHandler,
    UpdateReport
)

from .bulk_downloader import ArxivBulkDownloader

logger = logging.getLogger(__name__)


class ScheduleManager:
    """Handles cron-like scheduling configuration."""
    
    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load scheduling configuration."""
        default_config = {
            'enabled': True,
            'schedule': {
                'day_of_month': 1,  # First day of month
                'hour': 2,          # 2 AM
                'minute': 0
            },
            'email_notifications': {
                'enabled': False,
                'smtp_server': 'localhost',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'from_email': 'arxiv-updater@localhost',
                'to_emails': []
            },
            'retention': {
                'keep_reports_days': 90,
                'keep_logs_days': 30,
                'cleanup_old_pdfs': False
            }
        }
        
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    default_config.update(user_config)
        except Exception as e:
            logger.warning(f"Could not load config file: {e}, using defaults")
        
        return default_config
    
    def save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def is_enabled(self) -> bool:
        """Check if scheduled updates are enabled."""
        return self.config.get('enabled', True)
    
    def should_run_now(self) -> bool:
        """Check if update should run now based on schedule."""
        if not self.is_enabled():
            return False
        
        now = datetime.now()
        schedule = self.config.get('schedule', {})
        
        # Check if it's the right day of month
        target_day = schedule.get('day_of_month', 1)
        if now.day != target_day:
            return False
        
        # Check if it's the right hour
        target_hour = schedule.get('hour', 2)
        if now.hour != target_hour:
            return False
        
        # Check if it's the right minute (within 5 minute window)
        target_minute = schedule.get('minute', 0)
        if abs(now.minute - target_minute) > 5:
            return False
        
        return True
    
    def get_next_run_time(self) -> datetime:
        """Get the next scheduled run time."""
        now = datetime.now()
        schedule = self.config.get('schedule', {})
        
        target_day = schedule.get('day_of_month', 1)
        target_hour = schedule.get('hour', 2)
        target_minute = schedule.get('minute', 0)
        
        # Calculate next run time
        if now.day < target_day:
            # This month
            next_run = now.replace(day=target_day, hour=target_hour, minute=target_minute, second=0, microsecond=0)
        else:
            # Next month
            if now.month == 12:
                next_run = now.replace(year=now.year + 1, month=1, day=target_day, hour=target_hour, minute=target_minute, second=0, microsecond=0)
            else:
                next_run = now.replace(month=now.month + 1, day=target_day, hour=target_hour, minute=target_minute, second=0, microsecond=0)
        
        return next_run
    
    def generate_cron_expression(self) -> str:
        """Generate cron expression for the current schedule."""
        schedule = self.config.get('schedule', {})
        
        minute = schedule.get('minute', 0)
        hour = schedule.get('hour', 2)
        day = schedule.get('day_of_month', 1)
        
        return f"{minute} {hour} {day} * *"


class NewPaperDetector:
    """Identifies papers published in the previous month."""
    
    def __init__(self, categories: List[str]):
        self.categories = categories
    
    def get_previous_month_range(self) -> tuple[datetime, datetime]:
        """Get date range for the previous month."""
        now = datetime.now()
        
        # First day of current month
        first_day_current = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Last day of previous month
        last_day_previous = first_day_current - timedelta(days=1)
        
        # First day of previous month
        first_day_previous = last_day_previous.replace(day=1)
        
        return first_day_previous, last_day_previous
    
    async def discover_new_papers(self, downloader: ArxivBulkDownloader) -> List:
        """Discover new papers from the previous month."""
        start_date, end_date = self.get_previous_month_range()
        
        logger.info(f"Discovering papers from {start_date.date()} to {end_date.date()}")
        
        # Update downloader date range
        downloader.start_date = start_date
        downloader.date_filter.start_date = start_date
        downloader.date_filter.end_date = end_date
        
        # Discover papers
        papers = await downloader.discover_papers()
        
        logger.info(f"Discovered {len(papers)} new papers from previous month")
        return papers


class UpdateProcessor:
    """Processes new papers and integrates with existing corpus."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.reports_dir = output_dir / "processed" / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_monthly_update(self, 
                                   categories: List[str],
                                   output_dir: str) -> UpdateReport:
        """Process monthly update of new papers."""
        update_start = datetime.now()
        
        try:
            # Create downloader for this update
            detector = NewPaperDetector(categories)
            start_date, end_date = detector.get_previous_month_range()
            
            downloader = ArxivBulkDownloader(
                categories=categories,
                start_date=start_date,
                output_dir=output_dir
            )
            
            # Discover new papers
            papers = await detector.discover_new_papers(downloader)
            
            if not papers:
                return UpdateReport(
                    update_date=update_start,
                    papers_discovered=0,
                    papers_downloaded=0,
                    papers_processed=0,
                    papers_failed=0,
                    storage_used=0,
                    processing_time=0,
                    errors=[],
                    summary="No new papers found for the previous month",
                    categories_processed=categories
                )
            
            # Download papers
            downloaded_files = await downloader.download_papers(papers)
            
            # Process papers
            processing_success = await downloader.process_downloaded_papers(downloaded_files)
            
            # Calculate storage used
            storage_used = sum(f.stat().st_size for f in downloaded_files if f.exists())
            
            # Get processing statistics
            stats = downloader.get_download_stats()
            
            # Create update report
            processing_time = (datetime.now() - update_start).total_seconds()
            
            report = UpdateReport(
                update_date=update_start,
                papers_discovered=len(papers),
                papers_downloaded=len(downloaded_files),
                papers_processed=stats.get('processed_papers', 0),
                papers_failed=stats.get('failed_papers', 0),
                storage_used=storage_used,
                processing_time=processing_time,
                errors=self._extract_errors(downloader.error_handler),
                summary=self._generate_summary(len(papers), len(downloaded_files), stats),
                categories_processed=categories,
                duplicate_papers_skipped=len(papers) - len(downloaded_files)
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Monthly update processing failed: {e}")
            
            return UpdateReport(
                update_date=update_start,
                papers_discovered=0,
                papers_downloaded=0,
                papers_processed=0,
                papers_failed=0,
                storage_used=0,
                processing_time=(datetime.now() - update_start).total_seconds(),
                errors=[str(e)],
                summary=f"Update failed: {str(e)}",
                categories_processed=categories
            )
    
    def _extract_errors(self, error_handler: ErrorHandler) -> List[str]:
        """Extract error messages from error handler."""
        errors = []
        error_summary = error_handler.get_error_summary()
        
        for error in error_summary.recent_errors:
            errors.append(f"{error.error_type}: {error.error_message}")
        
        return errors[:10]  # Limit to 10 most recent errors
    
    def _generate_summary(self, 
                         discovered: int, 
                         downloaded: int, 
                         stats: Dict[str, Any]) -> str:
        """Generate human-readable summary of update."""
        processed = stats.get('processed_papers', 0)
        failed = stats.get('failed_papers', 0)
        
        if discovered == 0:
            return "No new papers found for the previous month."
        
        summary_parts = [
            f"Discovered {discovered} new papers",
            f"Downloaded {downloaded} papers",
            f"Successfully processed {processed} papers"
        ]
        
        if failed > 0:
            summary_parts.append(f"Failed to process {failed} papers")
        
        success_rate = (processed / discovered * 100) if discovered > 0 else 0
        summary_parts.append(f"Success rate: {success_rate:.1f}%")
        
        return ". ".join(summary_parts) + "."


class ReportGenerator:
    """Creates summary reports of update activities."""
    
    def __init__(self, reports_dir: Path):
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def save_report(self, report: UpdateReport) -> Path:
        """Save update report to file."""
        timestamp = report.update_date.strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"monthly_update_{timestamp}.json"
        
        if report.save_to_file(report_file):
            logger.info(f"Update report saved to {report_file}")
            return report_file
        else:
            logger.error(f"Failed to save update report")
            return None
    
    def generate_html_report(self, report: UpdateReport) -> str:
        """Generate HTML version of the report."""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>arXiv Monthly Update Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
                .stats { display: flex; justify-content: space-around; margin: 20px 0; }
                .stat { text-align: center; padding: 10px; background-color: #e8f4f8; border-radius: 5px; }
                .errors { background-color: #ffe6e6; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .success { color: green; }
                .warning { color: orange; }
                .error { color: red; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>arXiv Monthly Update Report</h1>
                <p><strong>Update Date:</strong> {update_date}</p>
                <p><strong>Categories:</strong> {categories}</p>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <h3>{papers_discovered}</h3>
                    <p>Papers Discovered</p>
                </div>
                <div class="stat">
                    <h3>{papers_downloaded}</h3>
                    <p>Papers Downloaded</p>
                </div>
                <div class="stat">
                    <h3>{papers_processed}</h3>
                    <p>Papers Processed</p>
                </div>
                <div class="stat">
                    <h3>{storage_mb} MB</h3>
                    <p>Storage Used</p>
                </div>
            </div>
            
            <div>
                <h2>Summary</h2>
                <p class="{summary_class}">{summary}</p>
            </div>
            
            <div>
                <h2>Processing Details</h2>
                <ul>
                    <li>Processing Time: {processing_time:.1f} seconds</li>
                    <li>Success Rate: {success_rate:.1f}%</li>
                    <li>Duplicate Papers Skipped: {duplicate_papers_skipped}</li>
                </ul>
            </div>
            
            {errors_section}
            
            <div>
                <p><em>Report generated on {report_date}</em></p>
            </div>
        </body>
        </html>
        """
        
        # Determine summary class based on results
        success_rate = (report.papers_processed / report.papers_discovered * 100) if report.papers_discovered > 0 else 0
        if success_rate >= 90:
            summary_class = "success"
        elif success_rate >= 70:
            summary_class = "warning"
        else:
            summary_class = "error"
        
        # Generate errors section
        errors_section = ""
        if report.errors:
            errors_html = "<ul>" + "".join(f"<li>{error}</li>" for error in report.errors) + "</ul>"
            errors_section = f"""
            <div class="errors">
                <h2>Errors</h2>
                {errors_html}
            </div>
            """
        
        return html_template.format(
            update_date=report.update_date.strftime("%Y-%m-%d %H:%M:%S"),
            categories=", ".join(report.categories_processed),
            papers_discovered=report.papers_discovered,
            papers_downloaded=report.papers_downloaded,
            papers_processed=report.papers_processed,
            storage_mb=report.storage_used // (1024 * 1024),
            summary=report.summary,
            summary_class=summary_class,
            processing_time=report.processing_time,
            success_rate=success_rate,
            duplicate_papers_skipped=report.duplicate_papers_skipped,
            errors_section=errors_section,
            report_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def send_email_report(self, report: UpdateReport, config: Dict[str, Any]) -> bool:
        """Send email report if configured."""
        email_config = config.get('email_notifications', {})
        
        if not email_config.get('enabled', False):
            return True  # Not an error if email is disabled
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"arXiv Monthly Update Report - {report.update_date.strftime('%Y-%m-%d')}"
            msg['From'] = email_config.get('from_email', 'arxiv-updater@localhost')
            msg['To'] = ', '.join(email_config.get('to_emails', []))
            
            # Create text and HTML versions
            text_content = self._generate_text_report(report)
            html_content = self.generate_html_report(report)
            
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(email_config.get('smtp_server', 'localhost'), email_config.get('smtp_port', 587)) as server:
                if email_config.get('username'):
                    server.starttls()
                    server.login(email_config['username'], email_config.get('password', ''))
                
                server.send_message(msg)
            
            logger.info("Email report sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email report: {e}")
            return False
    
    def _generate_text_report(self, report: UpdateReport) -> str:
        """Generate plain text version of the report."""
        lines = [
            "arXiv Monthly Update Report",
            "=" * 30,
            f"Update Date: {report.update_date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Categories: {', '.join(report.categories_processed)}",
            "",
            "Results:",
            f"  Papers Discovered: {report.papers_discovered}",
            f"  Papers Downloaded: {report.papers_downloaded}",
            f"  Papers Processed: {report.papers_processed}",
            f"  Papers Failed: {report.papers_failed}",
            f"  Storage Used: {report.storage_used // (1024 * 1024)} MB",
            f"  Processing Time: {report.processing_time:.1f} seconds",
            "",
            f"Summary: {report.summary}",
        ]
        
        if report.errors:
            lines.extend([
                "",
                "Errors:",
                *[f"  - {error}" for error in report.errors]
            ])
        
        return "\n".join(lines)


class ArxivMonthlyUpdater:
    """Main class for automated monthly arXiv updates."""
    
    def __init__(self, 
                 categories: List[str],
                 output_dir: str = "/datapool/aischolar/arxiv-dataset-2024"):
        """
        Initialize ArxivMonthlyUpdater.
        
        Args:
            categories: List of arXiv categories to update
            output_dir: Output directory for processed files
        """
        self.categories = categories
        self.output_dir = Path(output_dir)
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir = self.output_dir / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.schedule_manager = ScheduleManager(self.config_dir / "monthly_updater_config.json")
        self.update_processor = UpdateProcessor(self.output_dir)
        self.report_generator = ReportGenerator(self.output_dir / "processed" / "reports")
        
        logger.info(f"ArxivMonthlyUpdater initialized for categories: {categories}")
    
    async def run_monthly_update(self) -> UpdateReport:
        """
        Run monthly update process.
        
        Returns:
            UpdateReport with results of the update
        """
        logger.info("Starting monthly update process...")
        
        try:
            # Process monthly update
            report = await self.update_processor.process_monthly_update(
                self.categories,
                str(self.output_dir)
            )
            
            # Save report
            report_file = self.report_generator.save_report(report)
            
            # Send email notification if configured
            self.report_generator.send_email_report(report, self.schedule_manager.config)
            
            # Cleanup old data if configured
            await self.cleanup_old_data()
            
            logger.info(f"Monthly update completed: {report.summary}")
            return report
            
        except Exception as e:
            logger.error(f"Monthly update failed: {e}")
            
            # Create error report
            error_report = UpdateReport(
                update_date=datetime.now(),
                papers_discovered=0,
                papers_downloaded=0,
                papers_processed=0,
                papers_failed=0,
                storage_used=0,
                processing_time=0,
                errors=[str(e)],
                summary=f"Monthly update failed: {str(e)}",
                categories_processed=self.categories
            )
            
            return error_report
    
    async def setup_scheduling(self, cron_expression: str = None) -> bool:
        """
        Set up automated scheduling.
        
        Args:
            cron_expression: Optional cron expression to use
            
        Returns:
            True if setup successful
        """
        try:
            if cron_expression:
                # Parse cron expression and update config
                # This is a simplified implementation
                logger.info(f"Custom cron expression provided: {cron_expression}")
            
            # Generate cron command
            script_path = Path(__file__).parent.parent.parent / "run_monthly_update.py"
            cron_cmd = f"python {script_path} --categories {' '.join(self.categories)} --output-dir {self.output_dir}"
            
            # Generate cron expression
            cron_expr = self.schedule_manager.generate_cron_expression()
            full_cron_line = f"{cron_expr} {cron_cmd}"
            
            logger.info(f"Suggested cron line: {full_cron_line}")
            
            # Save cron information to file
            cron_file = self.config_dir / "cron_setup.txt"
            with open(cron_file, 'w') as f:
                f.write(f"# arXiv Monthly Updater Cron Setup\n")
                f.write(f"# Add this line to your crontab (crontab -e):\n")
                f.write(f"{full_cron_line}\n")
                f.write(f"\n# Next scheduled run: {self.schedule_manager.get_next_run_time()}\n")
            
            logger.info(f"Cron setup information saved to {cron_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup scheduling: {e}")
            return False
    
    def generate_update_report(self, report: UpdateReport) -> str:
        """Generate formatted update report."""
        return self.report_generator.generate_html_report(report)
    
    async def cleanup_old_data(self, retention_days: int = None) -> bool:
        """
        Clean up old data based on retention policy.
        
        Args:
            retention_days: Override default retention period
            
        Returns:
            True if cleanup successful
        """
        try:
            retention_config = self.schedule_manager.config.get('retention', {})
            
            # Clean up old reports
            reports_retention = retention_days or retention_config.get('keep_reports_days', 90)
            await self._cleanup_old_files(
                self.output_dir / "processed" / "reports",
                reports_retention,
                "*.json"
            )
            
            # Clean up old logs
            logs_retention = retention_config.get('keep_logs_days', 30)
            await self._cleanup_old_files(
                self.output_dir / "processed" / "error_logs",
                logs_retention,
                "*.log"
            )
            
            logger.info("Old data cleanup completed")
            return True
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return False
    
    async def _cleanup_old_files(self, directory: Path, retention_days: int, pattern: str):
        """Clean up old files in directory."""
        if not directory.exists():
            return
        
        cutoff_time = datetime.now() - timedelta(days=retention_days)
        cutoff_timestamp = cutoff_time.timestamp()
        
        cleaned_count = 0
        for file_path in directory.glob(pattern):
            try:
                if file_path.stat().st_mtime < cutoff_timestamp:
                    file_path.unlink()
                    cleaned_count += 1
            except Exception as e:
                logger.warning(f"Failed to clean up {file_path}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old files from {directory}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the monthly updater."""
        return {
            'categories': self.categories,
            'output_dir': str(self.output_dir),
            'scheduling_enabled': self.schedule_manager.is_enabled(),
            'next_run_time': self.schedule_manager.get_next_run_time().isoformat(),
            'config': self.schedule_manager.config
        }