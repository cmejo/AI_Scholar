"""
Storage Error Handler for Multi-Instance ArXiv System.

This module provides specialized handling for storage-related errors including
disk space issues, permission problems, I/O errors, and file system corruption.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import asyncio
import shutil
import os
import stat
import tempfile
from dataclasses import dataclass
from enum import Enum

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.error_handling.error_models import ProcessingError, ErrorType
except ImportError as e:
    print(f"Import error: {e}")
    # Create minimal fallback classes for testing
    class ProcessingError:
        def __init__(self, *args, **kwargs): pass
    class ErrorType:
        DISK_FULL = "disk_full"
        PERMISSION_DENIED = "permission_denied"

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Custom storage error exception."""
    
    def __init__(self, message: str, error_type: ErrorType, path: Optional[str] = None):
        super().__init__(message)
        self.error_type = error_type
        self.path = path


@dataclass
class DiskSpaceInfo:
    """Information about disk space usage."""
    
    path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    
    @property
    def usage_percentage(self) -> float:
        """Calculate disk usage percentage."""
        if self.total_bytes == 0:
            return 0.0
        return (self.used_bytes / self.total_bytes) * 100.0
    
    @property
    def free_percentage(self) -> float:
        """Calculate free space percentage."""
        return 100.0 - self.usage_percentage


@dataclass
class StorageRecoveryAction:
    """Represents a storage recovery action."""
    
    action_type: str
    description: str
    estimated_space_freed_mb: int
    risk_level: str  # "low", "medium", "high"
    requires_confirmation: bool = False


class StorageErrorHandler:
    """
    Specialized handler for storage-related errors.
    
    Provides disk space monitoring, cleanup strategies, permission handling,
    and intelligent recovery procedures for storage issues.
    """
    
    def __init__(
        self,
        instance_name: str,
        monitored_paths: Optional[List[str]] = None,
        cleanup_threshold_mb: int = 1024  # 1GB
    ):
        self.instance_name = instance_name
        self.monitored_paths = monitored_paths or []
        self.cleanup_threshold_mb = cleanup_threshold_mb
        
        # Storage monitoring
        self.disk_space_cache: Dict[str, DiskSpaceInfo] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        self.cache_duration = timedelta(minutes=5)
        
        # Recovery statistics
        self.total_storage_errors = 0
        self.successful_recoveries = 0
        self.space_freed_mb = 0
        self.cleanup_operations = 0
        
        # Cleanup strategies
        self.cleanup_strategies = [
            self._cleanup_temp_files,
            self._cleanup_old_logs,
            self._cleanup_cache_files,
            self._compress_old_files,
            self._archive_processed_files
        ]
        
        logger.info(f"StorageErrorHandler initialized for {instance_name}")
    
    async def handle_error(self, error: ProcessingError) -> bool:
        """
        Handle a storage error with appropriate recovery strategy.
        
        Args:
            error: The storage error to handle
            
        Returns:
            True if recovery was successful, False otherwise
        """
        
        logger.info(f"Handling storage error: {error.error_type.value}")
        
        self.total_storage_errors += 1
        
        # Determine recovery strategy based on error type
        if error.error_type == ErrorType.DISK_FULL:
            return await self._handle_disk_full_error(error)
        elif error.error_type == ErrorType.PERMISSION_DENIED:
            return await self._handle_permission_error(error)
        elif error.error_type == ErrorType.FILE_NOT_FOUND:
            return await self._handle_file_not_found_error(error)
        elif error.error_type == ErrorType.DIRECTORY_NOT_FOUND:
            return await self._handle_directory_not_found_error(error)
        elif error.error_type == ErrorType.IO_ERROR:
            return await self._handle_io_error(error)
        else:
            return await self._handle_generic_storage_error(error)
    
    async def _handle_disk_full_error(self, error: ProcessingError) -> bool:
        """Handle disk full errors."""
        
        logger.warning(f"Handling disk full error for path: {error.context.file_path}")
        
        # Get the path that's full
        target_path = error.context.file_path or "/"
        disk_path = self._get_disk_path(target_path)
        
        # Check current disk space
        disk_info = await self._get_disk_space_info(disk_path)
        
        logger.info(f"Disk space on {disk_path}: {disk_info.free_bytes / (1024**3):.2f} GB free "
                   f"({disk_info.free_percentage:.1f}%)")
        
        # If we have less than 1GB free, attempt cleanup
        if disk_info.free_bytes < (1024**3):  # Less than 1GB
            logger.info("Attempting automated cleanup to free disk space")
            
            space_freed = await self._perform_automated_cleanup(disk_path)
            
            if space_freed > 0:
                logger.info(f"Freed {space_freed / (1024**2):.1f} MB of disk space")
                self.space_freed_mb += space_freed / (1024**2)
                self.successful_recoveries += 1
                return True
            else:
                logger.warning("Automated cleanup did not free sufficient space")
                
                # Generate cleanup recommendations
                recommendations = await self._generate_cleanup_recommendations(disk_path)
                await self._log_cleanup_recommendations(recommendations)
                
                return False
        else:
            # Disk space seems fine now, might have been temporary
            logger.info("Disk space appears sufficient, error may have been temporary")
            return True
    
    async def _handle_permission_error(self, error: ProcessingError) -> bool:
        """Handle permission denied errors."""
        
        logger.info(f"Handling permission error for path: {error.context.file_path}")
        
        file_path = error.context.file_path
        if not file_path:
            logger.warning("No file path provided for permission error")
            return False
        
        path_obj = Path(file_path)
        
        # Check if path exists
        if not path_obj.exists():
            logger.info(f"Path does not exist, creating: {file_path}")
            try:
                if file_path.endswith('/') or '.' not in path_obj.name:
                    # Looks like a directory
                    path_obj.mkdir(parents=True, exist_ok=True)
                else:
                    # Looks like a file, create parent directory
                    path_obj.parent.mkdir(parents=True, exist_ok=True)
                
                self.successful_recoveries += 1
                return True
            
            except Exception as e:
                logger.error(f"Failed to create path {file_path}: {e}")
                return False
        
        # Try to fix permissions
        try:
            current_permissions = path_obj.stat().st_mode
            logger.info(f"Current permissions for {file_path}: {oct(current_permissions)}")
            
            # Try to make it readable/writable
            if path_obj.is_dir():
                # Directory: rwxr-xr-x
                new_permissions = stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
            else:
                # File: rw-r--r--
                new_permissions = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
            
            path_obj.chmod(new_permissions)
            logger.info(f"Updated permissions for {file_path} to {oct(new_permissions)}")
            
            self.successful_recoveries += 1
            return True
        
        except Exception as e:
            logger.error(f"Failed to fix permissions for {file_path}: {e}")
            return False
    
    async def _handle_file_not_found_error(self, error: ProcessingError) -> bool:
        """Handle file not found errors."""
        
        logger.info(f"Handling file not found error for: {error.context.file_path}")
        
        file_path = error.context.file_path
        if not file_path:
            return False
        
        path_obj = Path(file_path)
        
        # Check if parent directory exists
        if not path_obj.parent.exists():
            logger.info(f"Creating parent directory: {path_obj.parent}")
            try:
                path_obj.parent.mkdir(parents=True, exist_ok=True)
                self.successful_recoveries += 1
                return True
            except Exception as e:
                logger.error(f"Failed to create parent directory: {e}")
                return False
        
        # File doesn't exist but directory does - this might be expected
        logger.info(f"File {file_path} does not exist, but parent directory exists")
        return True  # Not really an error if we're trying to create the file
    
    async def _handle_directory_not_found_error(self, error: ProcessingError) -> bool:
        """Handle directory not found errors."""
        
        logger.info(f"Handling directory not found error for: {error.context.file_path}")
        
        dir_path = error.context.file_path
        if not dir_path:
            return False
        
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            self.successful_recoveries += 1
            return True
        
        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            return False
    
    async def _handle_io_error(self, error: ProcessingError) -> bool:
        """Handle generic I/O errors."""
        
        logger.info(f"Handling I/O error: {error.message}")
        
        file_path = error.context.file_path
        if not file_path:
            return False
        
        path_obj = Path(file_path)
        
        # Check if it's a disk space issue
        disk_info = await self._get_disk_space_info(self._get_disk_path(file_path))
        if disk_info.free_bytes < (100 * 1024 * 1024):  # Less than 100MB
            return await self._handle_disk_full_error(error)
        
        # Check if it's a permission issue
        if path_obj.exists():
            try:
                # Try to read/write test
                if path_obj.is_file():
                    with open(path_obj, 'r') as f:
                        f.read(1)
                else:
                    # Try to create a temp file in the directory
                    with tempfile.NamedTemporaryFile(dir=path_obj, delete=True):
                        pass
                
                # If we get here, permissions seem OK
                logger.info("I/O error might be temporary, allowing retry")
                return True
            
            except PermissionError:
                return await self._handle_permission_error(error)
            except Exception as e:
                logger.warning(f"I/O test failed: {e}")
                return False
        
        return False
    
    async def _handle_generic_storage_error(self, error: ProcessingError) -> bool:
        """Handle generic storage errors."""
        
        logger.info(f"Handling generic storage error: {error.message}")
        
        # Try basic recovery strategies
        file_path = error.context.file_path
        if file_path:
            path_obj = Path(file_path)
            
            # Ensure parent directory exists
            if not path_obj.parent.exists():
                try:
                    path_obj.parent.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created missing parent directory: {path_obj.parent}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to create parent directory: {e}")
        
        # If first attempt, allow retry
        if error.recovery_attempts == 1:
            logger.info("Allowing retry for generic storage error")
            return True
        
        return False
    
    async def _get_disk_space_info(self, path: str) -> DiskSpaceInfo:
        """Get disk space information for a path."""
        
        # Check cache first
        if path in self.disk_space_cache and path in self.cache_expiry:
            if datetime.now() < self.cache_expiry[path]:
                return self.disk_space_cache[path]
        
        try:
            # Get disk usage
            usage = shutil.disk_usage(path)
            
            disk_info = DiskSpaceInfo(
                path=path,
                total_bytes=usage.total,
                used_bytes=usage.used,
                free_bytes=usage.free
            )
            
            # Cache the result
            self.disk_space_cache[path] = disk_info
            self.cache_expiry[path] = datetime.now() + self.cache_duration
            
            return disk_info
        
        except Exception as e:
            logger.error(f"Failed to get disk space info for {path}: {e}")
            # Return dummy info
            return DiskSpaceInfo(path=path, total_bytes=0, used_bytes=0, free_bytes=0)
    
    def _get_disk_path(self, file_path: str) -> str:
        """Get the disk/mount point path for a file path."""
        
        try:
            path_obj = Path(file_path)
            
            # Find the mount point
            while not path_obj.exists() and path_obj != path_obj.parent:
                path_obj = path_obj.parent
            
            return str(path_obj) if path_obj.exists() else "/"
        
        except Exception:
            return "/"
    
    async def _perform_automated_cleanup(self, disk_path: str) -> int:
        """Perform automated cleanup to free disk space."""
        
        logger.info(f"Performing automated cleanup for {disk_path}")
        
        total_freed = 0
        
        for cleanup_strategy in self.cleanup_strategies:
            try:
                freed = await cleanup_strategy(disk_path)
                total_freed += freed
                
                if freed > 0:
                    logger.info(f"Cleanup strategy freed {freed / (1024**2):.1f} MB")
                
                # Check if we've freed enough space
                if total_freed > (self.cleanup_threshold_mb * 1024 * 1024):
                    logger.info(f"Cleanup threshold reached, stopping cleanup")
                    break
            
            except Exception as e:
                logger.error(f"Cleanup strategy failed: {e}")
        
        self.cleanup_operations += 1
        return total_freed
    
    async def _cleanup_temp_files(self, disk_path: str) -> int:
        """Clean up temporary files."""
        
        logger.info("Cleaning up temporary files")
        
        freed_bytes = 0
        temp_dirs = ["/tmp", tempfile.gettempdir()]
        
        # Add instance-specific temp directories
        for monitored_path in self.monitored_paths:
            temp_dirs.append(os.path.join(monitored_path, "temp"))
            temp_dirs.append(os.path.join(monitored_path, "tmp"))
        
        for temp_dir in temp_dirs:
            try:
                temp_path = Path(temp_dir)
                if not temp_path.exists():
                    continue
                
                # Clean files older than 1 day
                cutoff_time = datetime.now() - timedelta(days=1)
                
                for file_path in temp_path.rglob("*"):
                    if file_path.is_file():
                        try:
                            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if file_mtime < cutoff_time:
                                file_size = file_path.stat().st_size
                                file_path.unlink()
                                freed_bytes += file_size
                        except Exception:
                            continue
            
            except Exception as e:
                logger.warning(f"Failed to clean temp directory {temp_dir}: {e}")
        
        return freed_bytes
    
    async def _cleanup_old_logs(self, disk_path: str) -> int:
        """Clean up old log files."""
        
        logger.info("Cleaning up old log files")
        
        freed_bytes = 0
        log_dirs = ["logs", "/var/log"]
        
        # Add instance-specific log directories
        for monitored_path in self.monitored_paths:
            log_dirs.append(os.path.join(monitored_path, "logs"))
        
        for log_dir in log_dirs:
            try:
                log_path = Path(log_dir)
                if not log_path.exists():
                    continue
                
                # Clean log files older than 30 days
                cutoff_time = datetime.now() - timedelta(days=30)
                
                for file_path in log_path.rglob("*.log*"):
                    if file_path.is_file():
                        try:
                            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if file_mtime < cutoff_time:
                                file_size = file_path.stat().st_size
                                file_path.unlink()
                                freed_bytes += file_size
                        except Exception:
                            continue
            
            except Exception as e:
                logger.warning(f"Failed to clean log directory {log_dir}: {e}")
        
        return freed_bytes
    
    async def _cleanup_cache_files(self, disk_path: str) -> int:
        """Clean up cache files."""
        
        logger.info("Cleaning up cache files")
        
        freed_bytes = 0
        cache_patterns = ["*.cache", "*.tmp", "__pycache__"]
        
        for monitored_path in self.monitored_paths:
            try:
                path_obj = Path(monitored_path)
                if not path_obj.exists():
                    continue
                
                for pattern in cache_patterns:
                    for file_path in path_obj.rglob(pattern):
                        if file_path.is_file():
                            try:
                                file_size = file_path.stat().st_size
                                file_path.unlink()
                                freed_bytes += file_size
                            except Exception:
                                continue
                        elif file_path.is_dir() and pattern == "__pycache__":
                            try:
                                dir_size = sum(f.stat().st_size for f in file_path.rglob("*") if f.is_file())
                                shutil.rmtree(file_path)
                                freed_bytes += dir_size
                            except Exception:
                                continue
            
            except Exception as e:
                logger.warning(f"Failed to clean cache in {monitored_path}: {e}")
        
        return freed_bytes
    
    async def _compress_old_files(self, disk_path: str) -> int:
        """Compress old files to save space."""
        
        logger.info("Compressing old files")
        
        # This would implement file compression logic
        # For now, return 0 (no compression performed)
        return 0
    
    async def _archive_processed_files(self, disk_path: str) -> int:
        """Archive old processed files."""
        
        logger.info("Archiving old processed files")
        
        # This would implement archival logic
        # For now, return 0 (no archival performed)
        return 0
    
    async def _generate_cleanup_recommendations(self, disk_path: str) -> List[StorageRecoveryAction]:
        """Generate cleanup recommendations for manual intervention."""
        
        recommendations = []
        
        # Analyze disk usage and generate recommendations
        try:
            # Check for large files
            large_files = []
            for monitored_path in self.monitored_paths:
                path_obj = Path(monitored_path)
                if path_obj.exists():
                    for file_path in path_obj.rglob("*"):
                        if file_path.is_file():
                            try:
                                size_mb = file_path.stat().st_size / (1024 * 1024)
                                if size_mb > 100:  # Files larger than 100MB
                                    large_files.append((file_path, size_mb))
                            except Exception:
                                continue
            
            # Sort by size
            large_files.sort(key=lambda x: x[1], reverse=True)
            
            # Generate recommendations for large files
            for file_path, size_mb in large_files[:10]:  # Top 10 largest files
                recommendations.append(StorageRecoveryAction(
                    action_type="delete_large_file",
                    description=f"Delete large file: {file_path} ({size_mb:.1f} MB)",
                    estimated_space_freed_mb=int(size_mb),
                    risk_level="medium",
                    requires_confirmation=True
                ))
            
            # Recommend cleaning old processed files
            recommendations.append(StorageRecoveryAction(
                action_type="clean_old_processed",
                description="Clean processed files older than 90 days",
                estimated_space_freed_mb=500,  # Estimate
                risk_level="low",
                requires_confirmation=False
            ))
            
            # Recommend archiving
            recommendations.append(StorageRecoveryAction(
                action_type="archive_old_data",
                description="Archive data older than 6 months to compressed storage",
                estimated_space_freed_mb=1000,  # Estimate
                risk_level="low",
                requires_confirmation=False
            ))
        
        except Exception as e:
            logger.error(f"Failed to generate cleanup recommendations: {e}")
        
        return recommendations
    
    async def _log_cleanup_recommendations(self, recommendations: List[StorageRecoveryAction]) -> None:
        """Log cleanup recommendations for manual review."""
        
        logger.warning("STORAGE CLEANUP RECOMMENDATIONS:")
        logger.warning("=" * 50)
        
        for i, rec in enumerate(recommendations, 1):
            logger.warning(f"{i}. {rec.description}")
            logger.warning(f"   Estimated space freed: {rec.estimated_space_freed_mb} MB")
            logger.warning(f"   Risk level: {rec.risk_level}")
            logger.warning(f"   Requires confirmation: {rec.requires_confirmation}")
            logger.warning("")
        
        # Also save to file for manual review
        try:
            recommendations_file = f"logs/{self.instance_name}_storage_recommendations.json"
            Path(recommendations_file).parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(recommendations_file, 'w') as f:
                json.dump([{
                    'action_type': rec.action_type,
                    'description': rec.description,
                    'estimated_space_freed_mb': rec.estimated_space_freed_mb,
                    'risk_level': rec.risk_level,
                    'requires_confirmation': rec.requires_confirmation,
                    'timestamp': datetime.now().isoformat()
                } for rec in recommendations], f, indent=2)
            
            logger.info(f"Cleanup recommendations saved to {recommendations_file}")
        
        except Exception as e:
            logger.error(f"Failed to save cleanup recommendations: {e}")
    
    def add_monitored_path(self, path: str) -> None:
        """Add a path to monitor for storage issues."""
        
        if path not in self.monitored_paths:
            self.monitored_paths.append(path)
            logger.info(f"Added monitored path: {path}")
    
    def remove_monitored_path(self, path: str) -> None:
        """Remove a path from monitoring."""
        
        if path in self.monitored_paths:
            self.monitored_paths.remove(path)
            logger.info(f"Removed monitored path: {path}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get storage error handler statistics."""
        
        success_rate = 0.0
        if self.total_storage_errors > 0:
            success_rate = (self.successful_recoveries / self.total_storage_errors) * 100
        
        return {
            'instance_name': self.instance_name,
            'total_storage_errors': self.total_storage_errors,
            'successful_recoveries': self.successful_recoveries,
            'success_rate': success_rate,
            'space_freed_mb': self.space_freed_mb,
            'cleanup_operations': self.cleanup_operations,
            'monitored_paths': self.monitored_paths,
            'cleanup_threshold_mb': self.cleanup_threshold_mb
        }
    
    async def get_disk_usage_report(self) -> Dict[str, DiskSpaceInfo]:
        """Get disk usage report for all monitored paths."""
        
        report = {}
        
        for path in self.monitored_paths:
            disk_path = self._get_disk_path(path)
            disk_info = await self._get_disk_space_info(disk_path)
            report[path] = disk_info
        
        return report
    
    def clear_cache(self) -> None:
        """Clear disk space cache."""
        
        self.disk_space_cache.clear()
        self.cache_expiry.clear()
        logger.info(f"Cleared disk space cache for {self.instance_name}")