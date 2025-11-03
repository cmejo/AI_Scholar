"""
Monthly Update Orchestrator for multi-instance ArXiv system.

Coordinates monthly updates across all scholar instances with comprehensive
reporting, monitoring, and error handling.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import fcntl
import os
import signal
from dataclasses import dataclass, field

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from ..shared.multi_instance_data_models import (
    UpdateReport, InstanceConfig, StorageStats, PerformanceMetrics
)
from ..shared.multi_instance_state_manager import GlobalStateManager
from .instance_update_manager import InstanceUpdateManager

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationConfig:
    """Configuration for monthly update orchestration."""
    max_concurrent_instances: int = 2
    instance_timeout_hours: int = 12
    retry_failed_instances: bool = True
    max_retry_attempts: int = 2
    cleanup_old_reports: bool = True
    report_retention_days: int = 90
    enable_notifications: bool = True
    lock_file_path: str = "/tmp/multi_instance_monthly_update.lock"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'max_concurrent_instances': self.max_concurrent_instances,
            'instance_timeout_hours': self.instance_timeout_hours,
            'retry_failed_instances': self.retry_failed_instances,
            'max_retry_attempts': self.max_retry_attempts,
            'cleanup_old_reports': self.cleanup_old_reports,
            'report_retention_days': self.report_retention_days,
            'enable_notifications': self.enable_notifications,
            'lock_file_path': self.lock_file_path
        }


@dataclass
class OrchestrationResult:
    """Result of monthly update orchestration."""
    orchestration_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    instance_reports: Dict[str, UpdateReport] = field(default_factory=dict)
    failed_instances: List[str] = field(default_factory=list)
    skipped_instances: List[str] = field(default_factory=list)
    total_papers_processed: int = 0
    total_errors: int = 0
    orchestration_errors: List[str] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get orchestration duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        total_instances = len(self.instance_reports) + len(self.failed_instances)
        if total_instances == 0:
            return 0.0
        successful_instances = len(self.instance_reports) - len(self.failed_instances)
        return (successful_instances / total_instances) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'orchestration_id': self.orchestration_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'instance_reports': {k: v.to_dict() for k, v in self.instance_reports.items()},
            'failed_instances': self.failed_instances,
            'skipped_instances': self.skipped_instances,
            'total_papers_processed': self.total_papers_processed,
            'total_errors': self.total_errors,
            'orchestration_errors': self.orchestration_errors,
            'duration_seconds': self.duration_seconds,
            'success_rate': self.success_rate
        }


class FileLock:
    """File-based locking mechanism to prevent concurrent executions."""
    
    def __init__(self, lock_file_path: str):
        """
        Initialize file lock.
        
        Args:
            lock_file_path: Path to the lock file
        """
        self.lock_file_path = Path(lock_file_path)
        self.lock_file = None
        self.locked = False
    
    def acquire(self, timeout: int = 30) -> bool:
        """
        Acquire the lock.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            True if lock acquired, False otherwise
        """
        try:
            # Create lock file directory if it doesn't exist
            self.lock_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Open lock file
            self.lock_file = open(self.lock_file_path, 'w')
            
            # Try to acquire exclusive lock
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Write process info to lock file
            lock_info = {
                'pid': os.getpid(),
                'acquired_at': datetime.now().isoformat(),
                'process_name': 'monthly_update_orchestrator'
            }
            self.lock_file.write(json.dumps(lock_info, indent=2))
            self.lock_file.flush()
            
            self.locked = True
            logger.info(f"Acquired lock: {self.lock_file_path}")
            return True
            
        except (IOError, OSError) as e:
            logger.warning(f"Failed to acquire lock {self.lock_file_path}: {e}")
            if self.lock_file:
                self.lock_file.close()
                self.lock_file = None
            return False
    
    def release(self) -> None:
        """Release the lock."""
        if self.locked and self.lock_file:
            try:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.lock_file.close()
                
                # Remove lock file
                if self.lock_file_path.exists():
                    self.lock_file_path.unlink()
                
                logger.info(f"Released lock: {self.lock_file_path}")
                
            except Exception as e:
                logger.error(f"Error releasing lock: {e}")
            finally:
                self.locked = False
                self.lock_file = None
    
    def __enter__(self):
        """Context manager entry."""
        if not self.acquire():
            raise RuntimeError(f"Could not acquire lock: {self.lock_file_path}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()


class MonthlyUpdateOrchestrator:
    """Orchestrates monthly updates across all scholar instances."""
    
    def __init__(self, 
                 config_path: Optional[str] = None,
                 orchestration_config: Optional[OrchestrationConfig] = None):
        """
        Initialize monthly update orchestrator.
        
        Args:
            config_path: Path to orchestration configuration file
            orchestration_config: Direct orchestration configuration
        """
        self.config_path = config_path
        self.orchestration_config = orchestration_config or OrchestrationConfig()
        
        # Initialize components
        self.state_manager = GlobalStateManager(Path("/tmp/multi_instance_state"))
        self.instance_managers: Dict[str, InstanceUpdateManager] = {}
        self.current_orchestration: Optional[OrchestrationResult] = None
        
        # Signal handling for graceful shutdown
        self._shutdown_requested = False
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("MonthlyUpdateOrchestrator initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, requesting graceful shutdown...")
        self._shutdown_requested = True
    
    async def run_monthly_updates(self, 
                                instance_configs: List[InstanceConfig],
                                force_update: bool = False) -> OrchestrationResult:
        """
        Run monthly updates for all configured instances.
        
        Args:
            instance_configs: List of instance configurations
            force_update: Force update even if recently updated
            
        Returns:
            OrchestrationResult with comprehensive results
        """
        orchestration_id = f"monthly_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting monthly update orchestration: {orchestration_id}")
        logger.info(f"Configured instances: {[config.instance_name for config in instance_configs]}")
        
        # Initialize orchestration result
        self.current_orchestration = OrchestrationResult(
            orchestration_id=orchestration_id,
            start_time=datetime.now()
        )
        
        try:
            # Acquire global lock to prevent concurrent orchestrations
            with FileLock(self.orchestration_config.lock_file_path):
                logger.info("Acquired orchestration lock, proceeding with updates")
                
                # Validate instances before starting
                validated_configs = await self._validate_instances(instance_configs)
                
                if not validated_configs:
                    raise RuntimeError("No valid instances found for update")
                
                # Run updates with concurrency control
                await self._run_concurrent_updates(validated_configs, force_update)
                
                # Generate consolidated statistics
                self._calculate_consolidated_stats()
                
                # Cleanup old reports if configured
                if self.orchestration_config.cleanup_old_reports:
                    await self._cleanup_old_reports()
                
        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            self.current_orchestration.orchestration_errors.append(str(e))
            raise
        
        finally:
            # Finalize orchestration
            self.current_orchestration.end_time = datetime.now()
            
            # Save orchestration report
            await self._save_orchestration_report()
            
            logger.info(f"Monthly update orchestration completed: {orchestration_id}")
            logger.info(f"Duration: {self.current_orchestration.duration_seconds:.2f} seconds")
            logger.info(f"Success rate: {self.current_orchestration.success_rate:.1f}%")
        
        return self.current_orchestration
    
    async def _validate_instances(self, 
                                instance_configs: List[InstanceConfig]) -> List[InstanceConfig]:
        """Validate instance configurations before starting updates."""
        validated_configs = []
        
        for config in instance_configs:
            try:
                # Check if instance directories exist
                storage_paths = config.storage_paths
                pdf_dir = Path(storage_paths.pdf_directory)
                processed_dir = Path(storage_paths.processed_directory)
                state_dir = Path(storage_paths.state_directory)
                
                # Create directories if they don't exist
                pdf_dir.mkdir(parents=True, exist_ok=True)
                processed_dir.mkdir(parents=True, exist_ok=True)
                state_dir.mkdir(parents=True, exist_ok=True)
                
                # Check if instance is already running
                instance_state_manager = self.state_manager.get_instance_manager(config.instance_name)
                active_processors = instance_state_manager.list_instance_processors()
                
                if active_processors:
                    logger.warning(f"Instance {config.instance_name} has active processors, skipping")
                    self.current_orchestration.skipped_instances.append(config.instance_name)
                    continue
                
                validated_configs.append(config)
                logger.info(f"Validated instance: {config.instance_name}")
                
            except Exception as e:
                logger.error(f"Failed to validate instance {config.instance_name}: {e}")
                self.current_orchestration.orchestration_errors.append(
                    f"Instance validation failed for {config.instance_name}: {e}"
                )
        
        return validated_configs
    
    async def _run_concurrent_updates(self, 
                                    instance_configs: List[InstanceConfig],
                                    force_update: bool) -> None:
        """Run updates for multiple instances with concurrency control."""
        semaphore = asyncio.Semaphore(self.orchestration_config.max_concurrent_instances)
        
        async def run_single_instance(config: InstanceConfig) -> None:
            """Run update for a single instance."""
            async with semaphore:
                if self._shutdown_requested:
                    logger.info(f"Shutdown requested, skipping {config.instance_name}")
                    return
                
                try:
                    # Create instance update manager
                    instance_manager = InstanceUpdateManager(config)
                    self.instance_managers[config.instance_name] = instance_manager
                    
                    # Run instance update with timeout
                    timeout_seconds = self.orchestration_config.instance_timeout_hours * 3600
                    
                    logger.info(f"Starting update for instance: {config.instance_name}")
                    
                    update_report = await asyncio.wait_for(
                        instance_manager.run_instance_update(force_update=force_update),
                        timeout=timeout_seconds
                    )
                    
                    self.current_orchestration.instance_reports[config.instance_name] = update_report
                    logger.info(f"Completed update for instance: {config.instance_name}")
                    
                except asyncio.TimeoutError:
                    error_msg = f"Instance {config.instance_name} timed out after {timeout_seconds} seconds"
                    logger.error(error_msg)
                    self.current_orchestration.failed_instances.append(config.instance_name)
                    self.current_orchestration.orchestration_errors.append(error_msg)
                    
                except Exception as e:
                    error_msg = f"Instance {config.instance_name} failed: {e}"
                    logger.error(error_msg)
                    self.current_orchestration.failed_instances.append(config.instance_name)
                    self.current_orchestration.orchestration_errors.append(error_msg)
        
        # Run all instances concurrently
        tasks = [run_single_instance(config) for config in instance_configs]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle retry logic for failed instances
        if (self.orchestration_config.retry_failed_instances and 
            self.current_orchestration.failed_instances):
            await self._retry_failed_instances(instance_configs, force_update)
    
    async def _retry_failed_instances(self, 
                                    instance_configs: List[InstanceConfig],
                                    force_update: bool) -> None:
        """Retry failed instances with exponential backoff."""
        failed_instance_names = self.current_orchestration.failed_instances.copy()
        self.current_orchestration.failed_instances.clear()
        
        for attempt in range(self.orchestration_config.max_retry_attempts):
            if not failed_instance_names or self._shutdown_requested:
                break
            
            logger.info(f"Retry attempt {attempt + 1} for {len(failed_instance_names)} failed instances")
            
            # Wait before retry (exponential backoff)
            wait_time = 2 ** attempt * 60  # 1, 2, 4 minutes
            await asyncio.sleep(wait_time)
            
            # Get configs for failed instances
            retry_configs = [
                config for config in instance_configs 
                if config.instance_name in failed_instance_names
            ]
            
            # Run retry
            current_failed = failed_instance_names.copy()
            failed_instance_names.clear()
            
            for config in retry_configs:
                try:
                    instance_manager = InstanceUpdateManager(config)
                    update_report = await instance_manager.run_instance_update(force_update=force_update)
                    
                    self.current_orchestration.instance_reports[config.instance_name] = update_report
                    logger.info(f"Retry successful for instance: {config.instance_name}")
                    
                    # Remove from failed list
                    if config.instance_name in current_failed:
                        current_failed.remove(config.instance_name)
                        
                except Exception as e:
                    logger.error(f"Retry failed for instance {config.instance_name}: {e}")
                    failed_instance_names.append(config.instance_name)
        
        # Update final failed instances list
        self.current_orchestration.failed_instances = failed_instance_names
    
    def _calculate_consolidated_stats(self) -> None:
        """Calculate consolidated statistics across all instances."""
        total_papers = 0
        total_errors = 0
        
        for report in self.current_orchestration.instance_reports.values():
            total_papers += report.papers_processed
            total_errors += len(report.errors)
        
        self.current_orchestration.total_papers_processed = total_papers
        self.current_orchestration.total_errors = total_errors
        
        logger.info(f"Consolidated stats: {total_papers} papers processed, {total_errors} errors")
    
    async def _cleanup_old_reports(self) -> None:
        """Clean up old orchestration reports."""
        try:
            reports_dir = Path("/tmp/multi_instance_reports")
            if not reports_dir.exists():
                return
            
            cutoff_date = datetime.now() - timedelta(days=self.orchestration_config.report_retention_days)
            cleaned_count = 0
            
            for report_file in reports_dir.glob("orchestration_*.json"):
                try:
                    # Extract date from filename
                    date_str = report_file.stem.split('_')[2]  # orchestration_monthly_update_YYYYMMDD_HHMMSS
                    report_date = datetime.strptime(date_str, '%Y%m%d')
                    
                    if report_date < cutoff_date:
                        report_file.unlink()
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.warning(f"Could not process report file {report_file}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old orchestration reports")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old reports: {e}")
    
    async def _save_orchestration_report(self) -> None:
        """Save orchestration report to file."""
        try:
            reports_dir = Path("/tmp/multi_instance_reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            report_file = reports_dir / f"{self.current_orchestration.orchestration_id}.json"
            
            with open(report_file, 'w') as f:
                json.dump(self.current_orchestration.to_dict(), f, indent=2, default=str)
            
            logger.info(f"Orchestration report saved: {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save orchestration report: {e}")
    
    def get_orchestration_status(self) -> Optional[Dict[str, Any]]:
        """Get current orchestration status."""
        if not self.current_orchestration:
            return None
        
        return {
            'orchestration_id': self.current_orchestration.orchestration_id,
            'start_time': self.current_orchestration.start_time.isoformat(),
            'running_instances': len(self.instance_managers),
            'completed_instances': len(self.current_orchestration.instance_reports),
            'failed_instances': len(self.current_orchestration.failed_instances),
            'skipped_instances': len(self.current_orchestration.skipped_instances),
            'is_running': self.current_orchestration.end_time is None
        }
    
    async def stop_orchestration(self) -> bool:
        """Stop current orchestration gracefully."""
        if not self.current_orchestration or self.current_orchestration.end_time:
            return False
        
        logger.info("Stopping orchestration gracefully...")
        self._shutdown_requested = True
        
        # Stop all running instance managers
        for instance_name, manager in self.instance_managers.items():
            try:
                await manager.stop_update()
                logger.info(f"Stopped instance manager: {instance_name}")
            except Exception as e:
                logger.error(f"Failed to stop instance manager {instance_name}: {e}")
        
        return True