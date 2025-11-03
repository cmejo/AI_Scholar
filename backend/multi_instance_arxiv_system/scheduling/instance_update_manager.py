"""
Instance Update Manager for individual scholar instance updates.

Manages the complete update lifecycle for a single scholar instance including
downloading, processing, and reporting.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import shutil
import psutil

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from ..shared.multi_instance_data_models import (
    InstanceConfig, UpdateReport, StorageStats, PerformanceMetrics, ProcessingResult
)
from ..shared.multi_instance_state_manager import MultiInstanceStateManager
from ..downloaders.ai_scholar_downloader import AIScholarDownloader
from ..downloaders.quant_scholar_downloader import QuantScholarDownloader
from ..processors.ai_scholar_processor import AIScholarProcessor
from ..processors.quant_scholar_processor import QuantScholarProcessor

logger = logging.getLogger(__name__)


class InstanceUpdateManager:
    """Manages updates for individual scholar instances."""
    
    def __init__(self, instance_config: InstanceConfig):
        """
        Initialize instance update manager.
        
        Args:
            instance_config: Configuration for the scholar instance
        """
        self.config = instance_config
        self.instance_name = instance_config.instance_name
        
        # Initialize components
        self.state_manager = MultiInstanceStateManager(
            Path(instance_config.storage_paths.state_directory),
            instance_config.instance_name
        )
        
        # Initialize downloader and processor based on instance type
        if 'ai' in self.instance_name.lower():
            self.downloader = AIScholarDownloader(instance_config)
            self.processor = AIScholarProcessor(instance_config)
        elif 'quant' in self.instance_name.lower():
            self.downloader = QuantScholarDownloader(instance_config)
            self.processor = QuantScholarProcessor(instance_config)
        else:
            raise ValueError(f"Unknown instance type: {self.instance_name}")
        
        # Update tracking
        self.current_update: Optional[UpdateReport] = None
        self._stop_requested = False
        
        logger.info(f"InstanceUpdateManager initialized for '{self.instance_name}'")
    
    async def run_instance_update(self, force_update: bool = False) -> UpdateReport:
        """
        Run complete update for the instance.
        
        Args:
            force_update: Force update even if recently updated
            
        Returns:
            UpdateReport with comprehensive results
        """
        update_start_time = datetime.now()
        
        logger.info(f"Starting instance update for '{self.instance_name}'")
        
        # Initialize update report
        self.current_update = UpdateReport(
            instance_name=self.instance_name,
            update_date=update_start_time,
            papers_discovered=0,
            papers_downloaded=0,
            papers_processed=0,
            papers_failed=0,
            storage_used_mb=0,
            processing_time_seconds=0.0,
            errors=[],
            storage_stats=StorageStats(
                total_space_gb=0.0,
                used_space_gb=0.0,
                available_space_gb=0.0,
                usage_percentage=0.0,
                instance_breakdown={}
            ),
            performance_metrics=PerformanceMetrics()
        )
        
        try:
            # Check if update is needed
            if not force_update and await self._is_recent_update():
                logger.info(f"Recent update found for '{self.instance_name}', skipping")
                return self.current_update
            
            # Pre-update validation
            await self._validate_update_environment()
            
            # Initialize components
            await self._initialize_components()
            
            # Run update phases
            await self._run_discovery_phase()
            
            if self._stop_requested:
                logger.info("Update stopped during discovery phase")
                return self.current_update
            
            await self._run_download_phase()
            
            if self._stop_requested:
                logger.info("Update stopped during download phase")
                return self.current_update
            
            await self._run_processing_phase()
            
            if self._stop_requested:
                logger.info("Update stopped during processing phase")
                return self.current_update
            
            # Post-update tasks
            await self._run_cleanup_phase()
            await self._collect_final_metrics()
            
        except Exception as e:
            logger.error(f"Instance update failed for '{self.instance_name}': {e}")
            self.current_update.errors.append({
                'error_type': 'update_failure',
                'error_message': str(e),
                'timestamp': datetime.now().isoformat(),
                'phase': 'general'
            })
            raise
        
        finally:
            # Finalize update report
            self.current_update.processing_time_seconds = (
                datetime.now() - update_start_time
            ).total_seconds()
            
            # Save update report
            await self._save_update_report()
            
            logger.info(f"Instance update completed for '{self.instance_name}' "
                       f"in {self.current_update.processing_time_seconds:.2f} seconds")
        
        return self.current_update
    
    async def _is_recent_update(self) -> bool:
        """Check if there was a recent update for this instance."""
        try:
            # Check for recent update reports
            reports_dir = Path(self.config.storage_paths.state_directory) / "reports"
            if not reports_dir.exists():
                return False
            
            # Look for reports from the last 25 days (monthly updates)
            cutoff_date = datetime.now() - timedelta(days=25)
            
            for report_file in reports_dir.glob(f"{self.instance_name}_update_*.json"):
                try:
                    with open(report_file, 'r') as f:
                        report_data = json.load(f)
                    
                    update_date = datetime.fromisoformat(report_data['update_date'])
                    if update_date > cutoff_date:
                        logger.info(f"Found recent update from {update_date}")
                        return True
                        
                except Exception as e:
                    logger.warning(f"Could not read report file {report_file}: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check for recent updates: {e}")
            return False
    
    async def _validate_update_environment(self) -> None:
        """Validate that the update environment is ready."""
        logger.info(f"Validating update environment for '{self.instance_name}'")
        
        # Check storage paths
        storage_paths = self.config.storage_paths
        required_dirs = [
            storage_paths.pdf_directory,
            storage_paths.processed_directory,
            storage_paths.state_directory,
            storage_paths.error_log_directory
        ]
        
        for dir_path in required_dirs:
            path = Path(dir_path)
            path.mkdir(parents=True, exist_ok=True)
            
            # Check write permissions
            if not os.access(path, os.W_OK):
                raise RuntimeError(f"No write permission for directory: {path}")
        
        # Check available disk space
        storage_stats = await self._get_storage_stats()
        if storage_stats.usage_percentage > 90:
            raise RuntimeError(f"Insufficient disk space: {storage_stats.usage_percentage:.1f}% used")
        
        # Check system resources
        memory_usage = psutil.virtual_memory().percent
        if memory_usage > 85:
            logger.warning(f"High memory usage: {memory_usage:.1f}%")
        
        logger.info("Update environment validation successful")
    
    async def _initialize_components(self) -> None:
        """Initialize downloader and processor components."""
        logger.info(f"Initializing components for '{self.instance_name}'")
        
        # Initialize downloader
        success = await self.downloader.initialize()
        if not success:
            raise RuntimeError("Failed to initialize downloader")
        
        # Initialize processor
        success = await self.processor.initialize()
        if not success:
            raise RuntimeError("Failed to initialize processor")
        
        logger.info("Components initialized successfully")
    
    async def _run_discovery_phase(self) -> None:
        """Run paper discovery phase."""
        logger.info(f"Running discovery phase for '{self.instance_name}'")
        
        try:
            # Calculate date range for monthly update
            end_date = datetime.now()
            start_date = end_date - timedelta(days=35)  # Slightly more than a month for overlap
            
            # Discover papers
            discovered_papers = await self.downloader.discover_papers(start_date, end_date)
            
            self.current_update.papers_discovered = len(discovered_papers)
            logger.info(f"Discovered {len(discovered_papers)} papers")
            
            # Store discovered papers for download phase
            self._discovered_papers = discovered_papers
            
        except Exception as e:
            logger.error(f"Discovery phase failed: {e}")
            self.current_update.errors.append({
                'error_type': 'discovery_failure',
                'error_message': str(e),
                'timestamp': datetime.now().isoformat(),
                'phase': 'discovery'
            })
            raise
    
    async def _run_download_phase(self) -> None:
        """Run paper download phase."""
        logger.info(f"Running download phase for '{self.instance_name}'")
        
        try:
            if not hasattr(self, '_discovered_papers'):
                raise RuntimeError("No discovered papers available for download")
            
            # Download papers with progress tracking
            download_result = await self.downloader.download_papers(
                self._discovered_papers,
                max_concurrent=self.config.processing_config.max_concurrent_downloads
            )
            
            self.current_update.papers_downloaded = len(download_result.successful_downloads)
            self.current_update.papers_failed += len(download_result.failed_downloads)
            
            # Add download errors to report
            for error in download_result.errors:
                self.current_update.errors.append({
                    'error_type': 'download_error',
                    'error_message': str(error),
                    'timestamp': datetime.now().isoformat(),
                    'phase': 'download'
                })
            
            logger.info(f"Downloaded {len(download_result.successful_downloads)} papers, "
                       f"{len(download_result.failed_downloads)} failed")
            
            # Store downloaded files for processing phase
            self._downloaded_files = download_result.successful_downloads
            
        except Exception as e:
            logger.error(f"Download phase failed: {e}")
            self.current_update.errors.append({
                'error_type': 'download_phase_failure',
                'error_message': str(e),
                'timestamp': datetime.now().isoformat(),
                'phase': 'download'
            })
            raise
    
    async def _run_processing_phase(self) -> None:
        """Run paper processing phase."""
        logger.info(f"Running processing phase for '{self.instance_name}'")
        
        try:
            if not hasattr(self, '_downloaded_files'):
                logger.warning("No downloaded files available for processing")
                return
            
            # Process papers with the processor
            processing_result = await self.processor.process_papers(self._downloaded_files)
            
            self.current_update.papers_processed = processing_result.success_count
            self.current_update.papers_failed += processing_result.failure_count
            
            # Add processing errors to report
            for error in processing_result.processing_errors:
                self.current_update.errors.append({
                    'error_type': 'processing_error',
                    'error_message': str(error),
                    'timestamp': datetime.now().isoformat(),
                    'phase': 'processing'
                })
            
            logger.info(f"Processed {processing_result.success_count} papers, "
                       f"{processing_result.failure_count} failed")
            
        except Exception as e:
            logger.error(f"Processing phase failed: {e}")
            self.current_update.errors.append({
                'error_type': 'processing_phase_failure',
                'error_message': str(e),
                'timestamp': datetime.now().isoformat(),
                'phase': 'processing'
            })
            raise
    
    async def _run_cleanup_phase(self) -> None:
        """Run cleanup phase."""
        logger.info(f"Running cleanup phase for '{self.instance_name}'")
        
        try:
            # Clean up temporary files
            temp_dir = Path(self.config.storage_paths.pdf_directory) / "temp"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                logger.info("Cleaned up temporary files")
            
            # Clean up old error logs (keep last 30 days)
            await self._cleanup_old_logs()
            
            # Clean up old state files
            cleanup_count = self.state_manager.cleanup_instance_states(max_age_days=30)
            if cleanup_count > 0:
                logger.info(f"Cleaned up {cleanup_count} old state files")
            
        except Exception as e:
            logger.warning(f"Cleanup phase had issues: {e}")
            # Don't fail the entire update for cleanup issues
    
    async def _cleanup_old_logs(self) -> None:
        """Clean up old log files."""
        try:
            logs_dir = Path(self.config.storage_paths.error_log_directory)
            if not logs_dir.exists():
                return
            
            cutoff_date = datetime.now() - timedelta(days=30)
            cleaned_count = 0
            
            for log_file in logs_dir.glob("*.log"):
                try:
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        log_file.unlink()
                        cleaned_count += 1
                except Exception as e:
                    logger.warning(f"Could not clean log file {log_file}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old log files")
                
        except Exception as e:
            logger.warning(f"Failed to cleanup old logs: {e}")
    
    async def _collect_final_metrics(self) -> None:
        """Collect final metrics and statistics."""
        logger.info(f"Collecting final metrics for '{self.instance_name}'")
        
        try:
            # Get storage statistics
            self.current_update.storage_stats = await self._get_storage_stats()
            
            # Get performance metrics
            self.current_update.performance_metrics = await self._get_performance_metrics()
            
            # Calculate storage used
            pdf_dir = Path(self.config.storage_paths.pdf_directory)
            processed_dir = Path(self.config.storage_paths.processed_directory)
            
            pdf_size = sum(f.stat().st_size for f in pdf_dir.rglob('*') if f.is_file())
            processed_size = sum(f.stat().st_size for f in processed_dir.rglob('*') if f.is_file())
            
            self.current_update.storage_used_mb = int((pdf_size + processed_size) / (1024 * 1024))
            
        except Exception as e:
            logger.error(f"Failed to collect final metrics: {e}")
    
    async def _get_storage_stats(self) -> StorageStats:
        """Get current storage statistics."""
        try:
            # Get disk usage for the main storage directory
            storage_path = Path(self.config.storage_paths.pdf_directory).parent
            disk_usage = shutil.disk_usage(storage_path)
            
            total_gb = disk_usage.total / (1024**3)
            free_gb = disk_usage.free / (1024**3)
            used_gb = total_gb - free_gb
            usage_percentage = (used_gb / total_gb) * 100
            
            # Calculate instance breakdown
            instance_breakdown = {}
            for instance_dir in storage_path.iterdir():
                if instance_dir.is_dir():
                    try:
                        size = sum(f.stat().st_size for f in instance_dir.rglob('*') if f.is_file())
                        instance_breakdown[instance_dir.name] = size / (1024**3)  # GB
                    except Exception:
                        pass
            
            return StorageStats(
                total_space_gb=total_gb,
                used_space_gb=used_gb,
                available_space_gb=free_gb,
                usage_percentage=usage_percentage,
                instance_breakdown=instance_breakdown
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
    
    async def _get_performance_metrics(self) -> PerformanceMetrics:
        """Get performance metrics."""
        try:
            # Calculate processing rate
            processing_time = self.current_update.processing_time_seconds
            papers_processed = self.current_update.papers_processed
            
            processing_rate = 0.0
            if processing_time > 0:
                processing_rate = (papers_processed / processing_time) * 3600  # papers per hour
            
            # Get system metrics
            memory_info = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Calculate error rate
            total_papers = self.current_update.papers_discovered
            error_count = len(self.current_update.errors)
            error_rate = (error_count / total_papers * 100) if total_papers > 0 else 0.0
            
            return PerformanceMetrics(
                processing_rate_papers_per_hour=processing_rate,
                memory_usage_peak_mb=int(memory_info.used / (1024**2)),
                cpu_usage_average_percent=cpu_percent,
                error_rate_percentage=error_rate
            )
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return PerformanceMetrics()
    
    async def _save_update_report(self) -> None:
        """Save update report to file."""
        try:
            reports_dir = Path(self.config.storage_paths.state_directory) / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            report_filename = f"{self.instance_name}_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_file = reports_dir / report_filename
            
            with open(report_file, 'w') as f:
                json.dump(self.current_update.to_dict(), f, indent=2, default=str)
            
            logger.info(f"Update report saved: {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save update report: {e}")
    
    async def stop_update(self) -> None:
        """Stop the current update gracefully."""
        logger.info(f"Stopping update for '{self.instance_name}'")
        self._stop_requested = True
        
        # Stop downloader if running
        if hasattr(self.downloader, 'stop'):
            await self.downloader.stop()
        
        # Stop processor if running
        if hasattr(self.processor, 'stop'):
            await self.processor.stop()
    
    def get_update_status(self) -> Optional[Dict[str, Any]]:
        """Get current update status."""
        if not self.current_update:
            return None
        
        return {
            'instance_name': self.instance_name,
            'update_date': self.current_update.update_date.isoformat(),
            'papers_discovered': self.current_update.papers_discovered,
            'papers_downloaded': self.current_update.papers_downloaded,
            'papers_processed': self.current_update.papers_processed,
            'papers_failed': self.current_update.papers_failed,
            'error_count': len(self.current_update.errors),
            'is_running': self.current_update.processing_time_seconds == 0.0
        }