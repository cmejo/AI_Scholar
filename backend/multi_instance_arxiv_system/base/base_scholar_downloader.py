"""
Base Scholar Downloader for multi-instance ArXiv system.

Provides abstract base class for implementing scholar-specific downloaders
with common functionality for arXiv and journal source handling.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import asyncio

from ..shared.multi_instance_data_models import (
    BasePaper, ArxivPaper, JournalPaper, InstanceConfig, 
    UpdateReport, StorageStats, PerformanceMetrics
)
from ..shared.multi_instance_state_manager import MultiInstanceStateManager
from ..shared.multi_instance_progress_tracker import MultiInstanceProgressTracker
from ..shared.multi_instance_error_handler import MultiInstanceErrorHandler

logger = logging.getLogger(__name__)


class DateRange:
    """Represents a date range for paper discovery."""
    
    def __init__(self, start_date: datetime, end_date: datetime):
        self.start_date = start_date
        self.end_date = end_date
    
    def __str__(self) -> str:
        return f"{self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}"


class DownloadResult:
    """Result of a download operation."""
    
    def __init__(self):
        self.successful_downloads: List[str] = []
        self.failed_downloads: List[str] = []
        self.skipped_downloads: List[str] = []
        self.total_size_mb: float = 0.0
        self.download_time_seconds: float = 0.0
    
    @property
    def success_count(self) -> int:
        return len(self.successful_downloads)
    
    @property
    def failure_count(self) -> int:
        return len(self.failed_downloads)
    
    @property
    def skip_count(self) -> int:
        return len(self.skipped_downloads)
    
    @property
    def download_rate_mbps(self) -> float:
        if self.download_time_seconds > 0:
            return self.total_size_mb / self.download_time_seconds
        return 0.0


class ProcessingResult:
    """Result of a processing operation."""
    
    def __init__(self):
        self.processed_papers: List[str] = []
        self.failed_papers: List[str] = []
        self.skipped_papers: List[str] = []
        self.processing_time_seconds: float = 0.0
        self.storage_used_mb: float = 0.0
    
    @property
    def success_count(self) -> int:
        return len(self.processed_papers)
    
    @property
    def failure_count(self) -> int:
        return len(self.failed_papers)
    
    @property
    def skip_count(self) -> int:
        return len(self.skipped_papers)
    
    @property
    def processing_rate(self) -> float:
        if self.processing_time_seconds > 0:
            return len(self.processed_papers) / self.processing_time_seconds
        return 0.0


class BaseScholarDownloader(ABC):
    """Abstract base class for scholar-specific downloaders."""
    
    def __init__(self, instance_config: InstanceConfig):
        """
        Initialize BaseScholarDownloader.
        
        Args:
            instance_config: Configuration for the scholar instance
        """
        self.config = instance_config
        self.instance_name = instance_config.instance_name
        
        # Initialize components
        self.state_manager: Optional[MultiInstanceStateManager] = None
        self.progress_tracker: Optional[MultiInstanceProgressTracker] = None
        self.error_handler: Optional[MultiInstanceErrorHandler] = None
        
        # Processing state
        self.is_initialized = False
        self.current_processor_id: Optional[str] = None
        
        logger.info(f"BaseScholarDownloader initialized for instance '{self.instance_name}'")
    
    async def initialize_instance(self) -> bool:
        """
        Initialize the scholar instance with required components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Create storage directories
            if not self._create_storage_directories():
                return False
            
            # Initialize state manager
            state_dir = Path(self.config.storage_paths.state_directory).parent
            self.state_manager = MultiInstanceStateManager(state_dir, self.instance_name)
            
            # Initialize progress tracker
            self.progress_tracker = MultiInstanceProgressTracker(self.instance_name)
            
            # Create processor ID
            self.current_processor_id = f"{self.instance_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Initialize error handler
            error_dir = Path(self.config.storage_paths.error_log_directory).parent
            self.error_handler = MultiInstanceErrorHandler(
                error_dir, self.instance_name, self.current_processor_id
            )
            
            self.is_initialized = True
            logger.info(f"Instance '{self.instance_name}' initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize instance '{self.instance_name}': {e}")
            return False
    
    def _create_storage_directories(self) -> bool:
        """Create all required storage directories."""
        try:
            directories = [
                self.config.storage_paths.pdf_directory,
                self.config.storage_paths.processed_directory,
                self.config.storage_paths.state_directory,
                self.config.storage_paths.error_log_directory,
                self.config.storage_paths.archive_directory
            ]
            
            for directory in directories:
                Path(directory).mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Storage directories created for instance '{self.instance_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create storage directories: {e}")
            return False
    
    @abstractmethod
    async def discover_papers(self, date_range: DateRange) -> List[BasePaper]:
        """
        Discover papers from all configured sources for the given date range.
        
        Args:
            date_range: Date range to search for papers
            
        Returns:
            List of discovered papers
        """
        pass
    
    @abstractmethod
    async def download_papers(self, papers: List[BasePaper]) -> DownloadResult:
        """
        Download PDFs for the specified papers.
        
        Args:
            papers: List of papers to download
            
        Returns:
            DownloadResult with download statistics
        """
        pass
    
    @abstractmethod
    async def process_papers(self, pdf_paths: List[str]) -> ProcessingResult:
        """
        Process downloaded PDFs into the vector store.
        
        Args:
            pdf_paths: List of PDF file paths to process
            
        Returns:
            ProcessingResult with processing statistics
        """
        pass
    
    async def discover_arxiv_papers(self, date_range: DateRange) -> List[ArxivPaper]:
        """
        Discover arXiv papers for the configured categories.
        
        Args:
            date_range: Date range to search for papers
            
        Returns:
            List of discovered arXiv papers
        """
        # This is a common implementation that can be overridden
        arxiv_papers = []
        
        try:
            # Import arXiv API functionality from existing system
            from arxiv_rag_enhancement.processors.bulk_downloader import BulkDownloader
            
            # Create temporary bulk downloader for arXiv discovery
            # This would need to be adapted to work with the new system
            logger.info(f"Discovering arXiv papers for categories: {self.config.arxiv_categories}")
            
            # Placeholder implementation - would need actual arXiv API integration
            # For now, return empty list
            
        except Exception as e:
            if self.error_handler:
                self.error_handler.log_instance_error(
                    e, 
                    {'operation': 'arxiv_discovery', 'date_range': str(date_range)},
                    'arxiv_discovery_error'
                )
            logger.error(f"Failed to discover arXiv papers: {e}")
        
        return arxiv_papers
    
    async def discover_journal_papers(self, date_range: DateRange) -> List[JournalPaper]:
        """
        Discover journal papers from configured journal sources.
        
        Args:
            date_range: Date range to search for papers
            
        Returns:
            List of discovered journal papers
        """
        # Default implementation returns empty list
        # Subclasses should override this if they support journal sources
        return []
    
    def get_instance_stats(self) -> Dict[str, Any]:
        """
        Get current statistics for this instance.
        
        Returns:
            Dictionary with instance statistics
        """
        if not self.is_initialized:
            return {
                'instance_name': self.instance_name,
                'is_initialized': False,
                'error': 'Instance not initialized'
            }
        
        stats = {
            'instance_name': self.instance_name,
            'is_initialized': True,
            'processor_id': self.current_processor_id,
            'config': {
                'arxiv_categories': self.config.arxiv_categories,
                'journal_sources': len(self.config.journal_sources),
                'batch_size': self.config.processing_config.batch_size
            }
        }
        
        # Add progress tracker stats if available
        if self.progress_tracker:
            try:
                progress_stats = self.progress_tracker.get_instance_stats()
                stats['progress'] = progress_stats.to_dict()
            except Exception as e:
                stats['progress_error'] = str(e)
        
        # Add error handler stats if available
        if self.error_handler:
            try:
                error_summary = self.error_handler.get_instance_error_summary()
                stats['errors'] = {
                    'total_errors': error_summary['instance_stats']['total_errors'],
                    'critical_errors': error_summary['instance_stats']['critical_errors'],
                    'failed_files': len(error_summary['base_summary']['failed_files'])
                }
            except Exception as e:
                stats['error_summary_error'] = str(e)
        
        return stats
    
    async def run_monthly_update(self, 
                               target_date: Optional[datetime] = None) -> UpdateReport:
        """
        Run a complete monthly update for this instance.
        
        Args:
            target_date: Target date for the update (defaults to previous month)
            
        Returns:
            UpdateReport with comprehensive update statistics
        """
        if not self.is_initialized:
            raise RuntimeError("Instance not initialized")
        
        # Determine date range for update
        if target_date is None:
            target_date = datetime.now().replace(day=1) - timedelta(days=1)  # Last month
        
        start_date = target_date.replace(day=1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        date_range = DateRange(start_date, end_date)
        
        logger.info(f"Starting monthly update for '{self.instance_name}' "
                   f"for period: {date_range}")
        
        update_start_time = datetime.now()
        
        try:
            # Discover papers
            papers = await self.discover_papers(date_range)
            logger.info(f"Discovered {len(papers)} papers for {date_range}")
            
            # Download papers
            download_result = await self.download_papers(papers)
            logger.info(f"Downloaded {download_result.success_count} papers, "
                       f"failed: {download_result.failure_count}")
            
            # Process papers
            processing_result = await self.process_papers(download_result.successful_downloads)
            logger.info(f"Processed {processing_result.success_count} papers, "
                       f"failed: {processing_result.failure_count}")
            
            # Calculate processing time
            processing_time = (datetime.now() - update_start_time).total_seconds()
            
            # Get storage statistics
            storage_stats = self._get_storage_stats()
            
            # Get performance metrics
            performance_metrics = self._get_performance_metrics(
                download_result, processing_result, processing_time
            )
            
            # Collect errors
            errors = []
            if self.error_handler:
                recent_errors = self.error_handler.get_recent_errors(10)
                errors.extend(recent_errors)
            
            # Create update report
            update_report = UpdateReport(
                instance_name=self.instance_name,
                update_date=datetime.now(),
                papers_discovered=len(papers),
                papers_downloaded=download_result.success_count,
                papers_processed=processing_result.success_count,
                papers_failed=download_result.failure_count + processing_result.failure_count,
                storage_used_mb=int(storage_stats.used_space_gb * 1024),
                processing_time_seconds=processing_time,
                errors=errors,
                storage_stats=storage_stats,
                performance_metrics=performance_metrics,
                categories_processed=self.config.arxiv_categories,
                duplicate_papers_skipped=download_result.skip_count + processing_result.skip_count
            )
            
            # Save update report
            report_path = Path(self.config.storage_paths.state_directory) / "reports" / f"update_{update_start_time.strftime('%Y%m%d_%H%M%S')}.json"
            update_report.save_to_file(report_path)
            
            logger.info(f"Monthly update completed for '{self.instance_name}' in {processing_time:.2f} seconds")
            return update_report
            
        except Exception as e:
            if self.error_handler:
                self.error_handler.log_instance_error(
                    e,
                    {'operation': 'monthly_update', 'date_range': str(date_range)},
                    'monthly_update_error',
                    'critical'
                )
            
            logger.error(f"Monthly update failed for '{self.instance_name}': {e}")
            raise
    
    def _get_storage_stats(self) -> StorageStats:
        """Get current storage statistics."""
        try:
            import shutil
            
            # Get storage info for the base directory
            base_path = Path(self.config.storage_paths.pdf_directory).parent
            total, used, free = shutil.disk_usage(base_path)
            
            # Convert to GB
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            usage_percentage = (used_gb / total_gb) * 100
            
            # Calculate instance-specific usage (simplified)
            instance_usage = 0.0
            try:
                for directory in [
                    self.config.storage_paths.pdf_directory,
                    self.config.storage_paths.processed_directory
                ]:
                    dir_path = Path(directory)
                    if dir_path.exists():
                        instance_usage += sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                instance_usage = instance_usage / (1024**3)  # Convert to GB
            except Exception:
                instance_usage = 0.0
            
            return StorageStats(
                total_space_gb=total_gb,
                used_space_gb=used_gb,
                available_space_gb=free_gb,
                usage_percentage=usage_percentage,
                instance_breakdown={self.instance_name: instance_usage}
            )
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return StorageStats(
                total_space_gb=0.0,
                used_space_gb=0.0,
                available_space_gb=0.0,
                usage_percentage=0.0,
                instance_breakdown={}
            )
    
    def _get_performance_metrics(self, 
                               download_result: DownloadResult,
                               processing_result: ProcessingResult,
                               total_time: float) -> PerformanceMetrics:
        """Calculate performance metrics from operation results."""
        return PerformanceMetrics(
            download_rate_mbps=download_result.download_rate_mbps,
            processing_rate_papers_per_hour=(
                processing_result.success_count / (total_time / 3600) 
                if total_time > 0 else 0.0
            ),
            embedding_generation_rate=0.0,  # Would need to be calculated during processing
            memory_usage_peak_mb=0,  # Would need to be monitored during processing
            cpu_usage_average_percent=0.0,  # Would need to be monitored during processing
            error_rate_percentage=(
                ((download_result.failure_count + processing_result.failure_count) / 
                 max(download_result.success_count + download_result.failure_count + 
                     processing_result.success_count + processing_result.failure_count, 1)) * 100
            )
        )
    
    async def cleanup_old_files(self, retention_days: int = 30) -> Dict[str, Any]:
        """
        Clean up old files based on retention policy.
        
        Args:
            retention_days: Number of days to retain files
            
        Returns:
            Dictionary with cleanup statistics
        """
        cleanup_stats = {
            'files_removed': 0,
            'space_freed_mb': 0.0,
            'directories_cleaned': []
        }
        
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Clean up old PDFs if configured
            pdf_dir = Path(self.config.storage_paths.pdf_directory)
            if pdf_dir.exists():
                removed_count, space_freed = self._cleanup_directory(pdf_dir, cutoff_date)
                cleanup_stats['files_removed'] += removed_count
                cleanup_stats['space_freed_mb'] += space_freed
                if removed_count > 0:
                    cleanup_stats['directories_cleaned'].append(str(pdf_dir))
            
            # Clean up old state files
            if self.state_manager:
                state_cleanup = self.state_manager.cleanup_instance_states(retention_days)
                cleanup_stats['state_files_cleaned'] = state_cleanup
            
            logger.info(f"Cleanup completed for '{self.instance_name}': "
                       f"{cleanup_stats['files_removed']} files removed, "
                       f"{cleanup_stats['space_freed_mb']:.2f} MB freed")
            
        except Exception as e:
            if self.error_handler:
                self.error_handler.log_instance_error(
                    e,
                    {'operation': 'cleanup', 'retention_days': retention_days},
                    'cleanup_error'
                )
            logger.error(f"Cleanup failed for '{self.instance_name}': {e}")
        
        return cleanup_stats
    
    def _cleanup_directory(self, directory: Path, cutoff_date: datetime) -> tuple[int, float]:
        """Clean up files in a directory older than cutoff date."""
        removed_count = 0
        space_freed = 0.0
        
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        removed_count += 1
                        space_freed += file_size / (1024**2)  # Convert to MB
        except Exception as e:
            logger.error(f"Error cleaning directory {directory}: {e}")
        
        return removed_count, space_freed
    
    def shutdown(self) -> None:
        """Shutdown the downloader and cleanup resources."""
        logger.info(f"Shutting down downloader for instance '{self.instance_name}'")
        
        # Reset components
        if self.progress_tracker:
            self.progress_tracker.reset()
        
        if self.error_handler:
            self.error_handler.clear_errors()
        
        self.is_initialized = False
        self.current_processor_id = None
        
        logger.info(f"Downloader shutdown complete for instance '{self.instance_name}'")