"""
Scheduling Conflict Resolver for multi-instance ArXiv system.

Provides conflict detection and resolution for scheduling operations,
preventing overlapping executions and managing resource contention.
"""

import asyncio
import logging
import sys
import fcntl
import os
import signal
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import json
from dataclasses import dataclass, field
from enum import Enum

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of scheduling conflicts."""
    PROCESS_OVERLAP = "process_overlap"
    RESOURCE_CONTENTION = "resource_contention"
    FILE_LOCK_CONFLICT = "file_lock_conflict"
    INSTANCE_CONFLICT = "instance_conflict"
    SCHEDULE_OVERLAP = "schedule_overlap"


class ConflictSeverity(Enum):
    """Severity levels for conflicts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResolutionStrategy(Enum):
    """Conflict resolution strategies."""
    WAIT_AND_RETRY = "wait_and_retry"
    TERMINATE_CONFLICTING = "terminate_conflicting"
    RESCHEDULE = "reschedule"
    SKIP_EXECUTION = "skip_execution"
    FORCE_EXECUTION = "force_execution"


@dataclass
class ConflictInfo:
    """Information about a detected conflict."""
    conflict_type: ConflictType
    severity: ConflictSeverity
    description: str
    conflicting_processes: List[int] = field(default_factory=list)
    conflicting_files: List[str] = field(default_factory=list)
    conflicting_instances: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'conflict_type': self.conflict_type.value,
            'severity': self.severity.value,
            'description': self.description,
            'conflicting_processes': self.conflicting_processes,
            'conflicting_files': self.conflicting_files,
            'conflicting_instances': self.conflicting_instances,
            'detected_at': self.detected_at.isoformat()
        }


@dataclass
class ResolutionResult:
    """Result of conflict resolution attempt."""
    success: bool
    strategy_used: ResolutionStrategy
    actions_taken: List[str] = field(default_factory=list)
    remaining_conflicts: List[ConflictInfo] = field(default_factory=list)
    resolution_time_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'success': self.success,
            'strategy_used': self.strategy_used.value,
            'actions_taken': self.actions_taken,
            'remaining_conflicts': [c.to_dict() for c in self.remaining_conflicts],
            'resolution_time_seconds': self.resolution_time_seconds
        }


class ConflictResolver:
    """Manages scheduling conflict detection and resolution."""
    
    def __init__(self, 
                 lock_directory: str = "/tmp/multi_instance_locks",
                 max_wait_time_minutes: int = 30):
        """
        Initialize conflict resolver.
        
        Args:
            lock_directory: Directory for lock files
            max_wait_time_minutes: Maximum time to wait for conflict resolution
        """
        self.lock_directory = Path(lock_directory)
        self.lock_directory.mkdir(parents=True, exist_ok=True)
        self.max_wait_time = timedelta(minutes=max_wait_time_minutes)
        
        # Active locks managed by this resolver
        self.active_locks: Dict[str, Any] = {}
        
        # Conflict resolution history
        self.resolution_history: List[Dict[str, Any]] = []
        
        logger.info(f"ConflictResolver initialized with lock directory: {lock_directory}")
    
    async def detect_conflicts(self, 
                             operation_name: str,
                             instance_names: Optional[List[str]] = None) -> List[ConflictInfo]:
        """
        Detect potential conflicts for a scheduled operation.
        
        Args:
            operation_name: Name of the operation to check
            instance_names: Optional list of instance names involved
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        logger.debug(f"Detecting conflicts for operation: {operation_name}")
        
        # Check for process conflicts
        process_conflicts = await self._detect_process_conflicts(operation_name)
        conflicts.extend(process_conflicts)
        
        # Check for file lock conflicts
        lock_conflicts = await self._detect_lock_conflicts(operation_name)
        conflicts.extend(lock_conflicts)
        
        # Check for instance-specific conflicts
        if instance_names:
            instance_conflicts = await self._detect_instance_conflicts(instance_names)
            conflicts.extend(instance_conflicts)
        
        # Check for resource contention
        resource_conflicts = await self._detect_resource_conflicts()
        conflicts.extend(resource_conflicts)
        
        # Check for schedule overlaps
        schedule_conflicts = await self._detect_schedule_conflicts(operation_name)
        conflicts.extend(schedule_conflicts)
        
        logger.info(f"Detected {len(conflicts)} conflicts for operation '{operation_name}'")
        return conflicts
    
    async def resolve_conflicts(self, 
                              conflicts: List[ConflictInfo],
                              operation_name: str) -> ResolutionResult:
        """
        Attempt to resolve detected conflicts.
        
        Args:
            conflicts: List of conflicts to resolve
            operation_name: Name of the operation
            
        Returns:
            ResolutionResult with resolution outcome
        """
        start_time = datetime.now()
        result = ResolutionResult(
            success=True,
            strategy_used=ResolutionStrategy.WAIT_AND_RETRY
        )
        
        logger.info(f"Attempting to resolve {len(conflicts)} conflicts for '{operation_name}'")
        
        for conflict in conflicts:
            try:
                # Determine resolution strategy based on conflict type and severity
                strategy = self._determine_resolution_strategy(conflict)
                result.strategy_used = strategy
                
                # Apply resolution strategy
                resolved = await self._apply_resolution_strategy(conflict, strategy, result)
                
                if not resolved:
                    result.remaining_conflicts.append(conflict)
                    if conflict.severity in [ConflictSeverity.HIGH, ConflictSeverity.CRITICAL]:
                        result.success = False
                        
            except Exception as e:
                logger.error(f"Failed to resolve conflict {conflict.conflict_type}: {e}")
                result.remaining_conflicts.append(conflict)
                result.actions_taken.append(f"Resolution failed for {conflict.conflict_type}: {e}")
        
        result.resolution_time_seconds = (datetime.now() - start_time).total_seconds()
        
        # Record resolution attempt
        self._record_resolution_attempt(operation_name, conflicts, result)
        
        logger.info(f"Conflict resolution completed: success={result.success}, "
                   f"remaining={len(result.remaining_conflicts)}")
        
        return result
    
    async def _detect_process_conflicts(self, operation_name: str) -> List[ConflictInfo]:
        """Detect conflicting processes."""
        conflicts = []
        
        try:
            conflicting_pids = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    
                    # Check for multi-instance related processes
                    if ('multi_instance' in cmdline.lower() or 
                        'monthly_update' in cmdline.lower() or
                        'orchestrator' in cmdline.lower()):
                        
                        # Check if it's the same operation
                        if operation_name.lower() in cmdline.lower():
                            # Check process age - if it's very old, it might be stuck
                            create_time = datetime.fromtimestamp(proc.info['create_time'])
                            if datetime.now() - create_time > timedelta(hours=12):
                                conflicting_pids.append(proc.info['pid'])
                        
                        # Check for general conflicts
                        elif ('downloader' in cmdline.lower() or 
                              'processor' in cmdline.lower()):
                            conflicting_pids.append(proc.info['pid'])
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if conflicting_pids:
                severity = ConflictSeverity.HIGH if len(conflicting_pids) > 2 else ConflictSeverity.MEDIUM
                conflicts.append(ConflictInfo(
                    conflict_type=ConflictType.PROCESS_OVERLAP,
                    severity=severity,
                    description=f"Found {len(conflicting_pids)} potentially conflicting processes",
                    conflicting_processes=conflicting_pids
                ))
                
        except Exception as e:
            logger.error(f"Failed to detect process conflicts: {e}")
        
        return conflicts
    
    async def _detect_lock_conflicts(self, operation_name: str) -> List[ConflictInfo]:
        """Detect file lock conflicts."""
        conflicts = []
        
        try:
            lock_files = list(self.lock_directory.glob("*.lock"))
            conflicting_locks = []
            
            for lock_file in lock_files:
                try:
                    # Try to read lock file info
                    with open(lock_file, 'r') as f:
                        lock_info = json.load(f)
                    
                    # Check if lock is stale
                    acquired_at = datetime.fromisoformat(lock_info.get('acquired_at', ''))
                    if datetime.now() - acquired_at > timedelta(hours=6):
                        # Stale lock - try to remove it
                        try:
                            lock_file.unlink()
                            logger.info(f"Removed stale lock file: {lock_file}")
                            continue
                        except Exception:
                            pass
                    
                    # Check if it conflicts with our operation
                    if (operation_name in lock_file.name or 
                        'monthly_update' in lock_file.name):
                        conflicting_locks.append(str(lock_file))
                        
                except Exception:
                    # If we can't read the lock file, consider it a conflict
                    conflicting_locks.append(str(lock_file))
            
            if conflicting_locks:
                conflicts.append(ConflictInfo(
                    conflict_type=ConflictType.FILE_LOCK_CONFLICT,
                    severity=ConflictSeverity.HIGH,
                    description=f"Found {len(conflicting_locks)} conflicting lock files",
                    conflicting_files=conflicting_locks
                ))
                
        except Exception as e:
            logger.error(f"Failed to detect lock conflicts: {e}")
        
        return conflicts
    
    async def _detect_instance_conflicts(self, instance_names: List[str]) -> List[ConflictInfo]:
        """Detect instance-specific conflicts."""
        conflicts = []
        
        try:
            for instance_name in instance_names:
                # Check for instance-specific lock files
                instance_locks = list(self.lock_directory.glob(f"*{instance_name}*.lock"))
                
                if instance_locks:
                    conflicts.append(ConflictInfo(
                        conflict_type=ConflictType.INSTANCE_CONFLICT,
                        severity=ConflictSeverity.MEDIUM,
                        description=f"Instance '{instance_name}' has active locks",
                        conflicting_instances=[instance_name],
                        conflicting_files=[str(lock) for lock in instance_locks]
                    ))
                
                # Check for instance-specific processes
                instance_processes = []
                for proc in psutil.process_iter(['pid', 'cmdline']):
                    try:
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if instance_name in cmdline:
                            instance_processes.append(proc.info['pid'])
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if instance_processes:
                    conflicts.append(ConflictInfo(
                        conflict_type=ConflictType.INSTANCE_CONFLICT,
                        severity=ConflictSeverity.MEDIUM,
                        description=f"Instance '{instance_name}' has active processes",
                        conflicting_instances=[instance_name],
                        conflicting_processes=instance_processes
                    ))
                    
        except Exception as e:
            logger.error(f"Failed to detect instance conflicts: {e}")
        
        return conflicts
    
    async def _detect_resource_conflicts(self) -> List[ConflictInfo]:
        """Detect resource contention conflicts."""
        conflicts = []
        
        try:
            # Check system resources
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Check disk I/O
            disk_io = psutil.disk_io_counters()
            
            # Determine if resources are under heavy load
            resource_issues = []
            
            if memory.percent > 85:
                resource_issues.append(f"High memory usage: {memory.percent:.1f}%")
            
            if cpu_percent > 80:
                resource_issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            # Check for high disk I/O (simplified check)
            if disk_io and hasattr(disk_io, 'read_bytes') and hasattr(disk_io, 'write_bytes'):
                # This is a simplified check - in practice, you'd want to compare with baseline
                total_io = disk_io.read_bytes + disk_io.write_bytes
                if total_io > 1e9:  # More than 1GB I/O (very rough heuristic)
                    resource_issues.append("High disk I/O detected")
            
            if resource_issues:
                severity = ConflictSeverity.HIGH if len(resource_issues) > 1 else ConflictSeverity.MEDIUM
                conflicts.append(ConflictInfo(
                    conflict_type=ConflictType.RESOURCE_CONTENTION,
                    severity=severity,
                    description=f"Resource contention detected: {'; '.join(resource_issues)}"
                ))
                
        except Exception as e:
            logger.error(f"Failed to detect resource conflicts: {e}")
        
        return conflicts
    
    async def _detect_schedule_conflicts(self, operation_name: str) -> List[ConflictInfo]:
        """Detect schedule overlap conflicts."""
        conflicts = []
        
        try:
            # Check for recent execution logs
            log_dir = Path("/var/log/multi_instance_arxiv")
            if log_dir.exists():
                recent_logs = []
                cutoff_time = datetime.now() - timedelta(hours=2)
                
                for log_file in log_dir.glob("*.log"):
                    try:
                        stat = log_file.stat()
                        if datetime.fromtimestamp(stat.st_mtime) > cutoff_time:
                            recent_logs.append(str(log_file))
                    except Exception:
                        continue
                
                if recent_logs and operation_name in str(recent_logs):
                    conflicts.append(ConflictInfo(
                        conflict_type=ConflictType.SCHEDULE_OVERLAP,
                        severity=ConflictSeverity.MEDIUM,
                        description=f"Recent execution detected for '{operation_name}'",
                        conflicting_files=recent_logs
                    ))
                    
        except Exception as e:
            logger.error(f"Failed to detect schedule conflicts: {e}")
        
        return conflicts
    
    def _determine_resolution_strategy(self, conflict: ConflictInfo) -> ResolutionStrategy:
        """Determine the best resolution strategy for a conflict."""
        if conflict.severity == ConflictSeverity.CRITICAL:
            return ResolutionStrategy.SKIP_EXECUTION
        elif conflict.conflict_type == ConflictType.PROCESS_OVERLAP:
            if conflict.severity == ConflictSeverity.HIGH:
                return ResolutionStrategy.TERMINATE_CONFLICTING
            else:
                return ResolutionStrategy.WAIT_AND_RETRY
        elif conflict.conflict_type == ConflictType.FILE_LOCK_CONFLICT:
            return ResolutionStrategy.WAIT_AND_RETRY
        elif conflict.conflict_type == ConflictType.RESOURCE_CONTENTION:
            return ResolutionStrategy.WAIT_AND_RETRY
        elif conflict.conflict_type == ConflictType.SCHEDULE_OVERLAP:
            return ResolutionStrategy.RESCHEDULE
        else:
            return ResolutionStrategy.WAIT_AND_RETRY
    
    async def _apply_resolution_strategy(self, 
                                       conflict: ConflictInfo,
                                       strategy: ResolutionStrategy,
                                       result: ResolutionResult) -> bool:
        """Apply a resolution strategy to a conflict."""
        try:
            if strategy == ResolutionStrategy.WAIT_AND_RETRY:
                return await self._wait_for_conflict_resolution(conflict, result)
            elif strategy == ResolutionStrategy.TERMINATE_CONFLICTING:
                return await self._terminate_conflicting_processes(conflict, result)
            elif strategy == ResolutionStrategy.RESCHEDULE:
                return await self._reschedule_operation(conflict, result)
            elif strategy == ResolutionStrategy.SKIP_EXECUTION:
                result.actions_taken.append(f"Skipped execution due to {conflict.conflict_type}")
                return False
            elif strategy == ResolutionStrategy.FORCE_EXECUTION:
                result.actions_taken.append(f"Forced execution despite {conflict.conflict_type}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to apply resolution strategy {strategy}: {e}")
            result.actions_taken.append(f"Strategy application failed: {e}")
            return False
    
    async def _wait_for_conflict_resolution(self, 
                                          conflict: ConflictInfo,
                                          result: ResolutionResult) -> bool:
        """Wait for conflict to resolve naturally."""
        max_wait_seconds = 300  # 5 minutes
        check_interval = 30  # 30 seconds
        
        logger.info(f"Waiting for conflict resolution: {conflict.conflict_type}")
        
        for elapsed in range(0, max_wait_seconds, check_interval):
            await asyncio.sleep(check_interval)
            
            # Re-check the specific conflict
            if conflict.conflict_type == ConflictType.PROCESS_OVERLAP:
                # Check if conflicting processes are still running
                still_running = []
                for pid in conflict.conflicting_processes:
                    try:
                        if psutil.pid_exists(pid):
                            still_running.append(pid)
                    except Exception:
                        pass
                
                if not still_running:
                    result.actions_taken.append(f"Waited {elapsed + check_interval}s for processes to complete")
                    return True
                    
            elif conflict.conflict_type == ConflictType.FILE_LOCK_CONFLICT:
                # Check if lock files still exist
                still_locked = []
                for lock_file in conflict.conflicting_files:
                    if Path(lock_file).exists():
                        still_locked.append(lock_file)
                
                if not still_locked:
                    result.actions_taken.append(f"Waited {elapsed + check_interval}s for locks to be released")
                    return True
        
        result.actions_taken.append(f"Timeout waiting for conflict resolution after {max_wait_seconds}s")
        return False
    
    async def _terminate_conflicting_processes(self, 
                                             conflict: ConflictInfo,
                                             result: ResolutionResult) -> bool:
        """Terminate conflicting processes."""
        terminated_count = 0
        
        for pid in conflict.conflicting_processes:
            try:
                proc = psutil.Process(pid)
                
                # First try graceful termination
                proc.terminate()
                
                # Wait a bit for graceful shutdown
                try:
                    proc.wait(timeout=10)
                    terminated_count += 1
                    logger.info(f"Gracefully terminated process {pid}")
                except psutil.TimeoutExpired:
                    # Force kill if graceful termination fails
                    proc.kill()
                    terminated_count += 1
                    logger.warning(f"Force killed process {pid}")
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.warning(f"Could not terminate process {pid}: {e}")
        
        result.actions_taken.append(f"Terminated {terminated_count} conflicting processes")
        return terminated_count > 0
    
    async def _reschedule_operation(self, 
                                  conflict: ConflictInfo,
                                  result: ResolutionResult) -> bool:
        """Reschedule operation to avoid conflict."""
        # This is a placeholder - actual rescheduling would depend on the scheduling system
        delay_minutes = 30
        result.actions_taken.append(f"Recommended rescheduling operation by {delay_minutes} minutes")
        
        # For now, just wait a short time
        await asyncio.sleep(60)  # Wait 1 minute
        return True
    
    def _record_resolution_attempt(self, 
                                 operation_name: str,
                                 conflicts: List[ConflictInfo],
                                 result: ResolutionResult) -> None:
        """Record conflict resolution attempt for analysis."""
        record = {
            'timestamp': datetime.now().isoformat(),
            'operation_name': operation_name,
            'conflicts': [c.to_dict() for c in conflicts],
            'resolution_result': result.to_dict()
        }
        
        self.resolution_history.append(record)
        
        # Keep only recent history (last 100 records)
        if len(self.resolution_history) > 100:
            self.resolution_history = self.resolution_history[-100:]
    
    def get_conflict_statistics(self) -> Dict[str, Any]:
        """Get conflict resolution statistics."""
        if not self.resolution_history:
            return {'total_resolutions': 0}
        
        # Analyze conflict patterns
        conflict_types = {}
        resolution_strategies = {}
        success_rates = {}
        
        total_attempts = len(self.resolution_history)
        successful_attempts = 0
        
        for record in self.resolution_history:
            # Count resolution success
            if record['resolution_result']['success']:
                successful_attempts += 1
            
            # Count conflict types
            for conflict in record['conflicts']:
                conflict_type = conflict['conflict_type']
                conflict_types[conflict_type] = conflict_types.get(conflict_type, 0) + 1
            
            # Count resolution strategies
            strategy = record['resolution_result']['strategy_used']
            resolution_strategies[strategy] = resolution_strategies.get(strategy, 0) + 1
        
        return {
            'total_resolutions': total_attempts,
            'successful_resolutions': successful_attempts,
            'success_rate': (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0,
            'conflict_types': conflict_types,
            'resolution_strategies': resolution_strategies,
            'active_locks': len(self.active_locks)
        }
    
    def cleanup_stale_locks(self) -> int:
        """Clean up stale lock files."""
        cleaned_count = 0
        cutoff_time = datetime.now() - timedelta(hours=6)
        
        try:
            for lock_file in self.lock_directory.glob("*.lock"):
                try:
                    # Check file modification time
                    stat = lock_file.stat()
                    if datetime.fromtimestamp(stat.st_mtime) < cutoff_time:
                        lock_file.unlink()
                        cleaned_count += 1
                        logger.info(f"Cleaned up stale lock file: {lock_file}")
                except Exception as e:
                    logger.warning(f"Could not clean up lock file {lock_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup stale locks: {e}")
        
        return cleaned_count