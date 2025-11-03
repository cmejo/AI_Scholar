"""
Scheduling Coordinator for automated monthly updates.

Coordinates all aspects of automated scheduling including health checks,
conflict resolution, error recovery, and execution monitoring.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
from dataclasses import dataclass, field

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from .health_checker import HealthChecker, SystemHealthStatus
from .error_recovery_manager import ErrorRecoveryManager, RecoveryConfig
from .conflict_resolver import ConflictResolver, ConflictInfo
from .monthly_update_orchestrator import MonthlyUpdateOrchestrator, OrchestrationConfig
from ..shared.multi_instance_data_models import InstanceConfig

logger = logging.getLogger(__name__)


@dataclass
class SchedulingConfig:
    """Configuration for scheduling coordinator."""
    enable_health_checks: bool = True
    enable_conflict_resolution: bool = True
    enable_error_recovery: bool = True
    health_check_timeout_minutes: int = 10
    conflict_resolution_timeout_minutes: int = 30
    max_execution_time_hours: int = 12
    retry_failed_executions: bool = True
    send_notifications: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'enable_health_checks': self.enable_health_checks,
            'enable_conflict_resolution': self.enable_conflict_resolution,
            'enable_error_recovery': self.enable_error_recovery,
            'health_check_timeout_minutes': self.health_check_timeout_minutes,
            'conflict_resolution_timeout_minutes': self.conflict_resolution_timeout_minutes,
            'max_execution_time_hours': self.max_execution_time_hours,
            'retry_failed_executions': self.retry_failed_executions,
            'send_notifications': self.send_notifications
        }


@dataclass
class SchedulingResult:
    """Result of scheduled execution."""
    execution_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    health_check_passed: bool = False
    conflicts_resolved: bool = False
    orchestration_result: Optional[Any] = None
    error_message: Optional[str] = None
    actions_taken: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'execution_id': self.execution_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'success': self.success,
            'health_check_passed': self.health_check_passed,
            'conflicts_resolved': self.conflicts_resolved,
            'orchestration_result': str(self.orchestration_result) if self.orchestration_result else None,
            'error_message': self.error_message,
            'actions_taken': self.actions_taken
        }


class SchedulingCoordinator:
    """Coordinates automated scheduling with comprehensive monitoring and recovery."""
    
    def __init__(self, 
                 scheduling_config: Optional[SchedulingConfig] = None,
                 orchestration_config: Optional[OrchestrationConfig] = None,
                 recovery_config: Optional[RecoveryConfig] = None):
        """
        Initialize scheduling coordinator.
        
        Args:
            scheduling_config: Configuration for scheduling behavior
            orchestration_config: Configuration for orchestration
            recovery_config: Configuration for error recovery
        """
        self.scheduling_config = scheduling_config or SchedulingConfig()
        self.orchestration_config = orchestration_config or OrchestrationConfig()
        self.recovery_config = recovery_config or RecoveryConfig()
        
        # Initialize components
        self.health_checker = HealthChecker()
        self.error_recovery_manager = ErrorRecoveryManager(self.recovery_config)
        self.conflict_resolver = ConflictResolver()
        self.orchestrator = MonthlyUpdateOrchestrator(orchestration_config=self.orchestration_config)
        
        # Execution history
        self.execution_history: List[SchedulingResult] = []
        
        logger.info("SchedulingCoordinator initialized")
    
    async def execute_scheduled_update(self, 
                                     instance_configs: List[InstanceConfig],
                                     force_execution: bool = False) -> SchedulingResult:
        """
        Execute a scheduled update with full coordination.
        
        Args:
            instance_configs: List of instance configurations
            force_execution: Force execution even if health checks fail
            
        Returns:
            SchedulingResult with execution details
        """
        execution_id = f"scheduled_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = SchedulingResult(
            execution_id=execution_id,
            start_time=datetime.now()
        )
        
        logger.info(f"Starting scheduled update execution: {execution_id}")
        
        try:
            # Phase 1: Health Check
            if self.scheduling_config.enable_health_checks:
                health_status = await self._perform_health_check(instance_configs, result)
                
                if not health_status and not force_execution:
                    result.error_message = "Health check failed and force_execution is False"
                    logger.error("Aborting execution due to failed health check")
                    return result
            else:
                result.health_check_passed = True
                result.actions_taken.append("Health checks disabled")
            
            # Phase 2: Conflict Detection and Resolution
            if self.scheduling_config.enable_conflict_resolution:
                conflicts_resolved = await self._resolve_conflicts(instance_configs, result)
                
                if not conflicts_resolved and not force_execution:
                    result.error_message = "Conflict resolution failed and force_execution is False"
                    logger.error("Aborting execution due to unresolved conflicts")
                    return result
            else:
                result.conflicts_resolved = True
                result.actions_taken.append("Conflict resolution disabled")
            
            # Phase 3: Execute with Error Recovery
            if self.scheduling_config.enable_error_recovery:
                orchestration_result = await self._execute_with_recovery(instance_configs, result)
            else:
                orchestration_result = await self._execute_without_recovery(instance_configs, result)
            
            result.orchestration_result = orchestration_result
            result.success = orchestration_result is not None
            
            if result.success:
                logger.info(f"Scheduled update execution completed successfully: {execution_id}")
            else:
                logger.error(f"Scheduled update execution failed: {execution_id}")
                
        except Exception as e:
            logger.error(f"Scheduled update execution failed with exception: {e}")
            result.error_message = str(e)
            result.success = False
            
        finally:
            result.end_time = datetime.now()
            self.execution_history.append(result)
            
            # Keep only recent history (last 50 executions)
            if len(self.execution_history) > 50:
                self.execution_history = self.execution_history[-50:]
            
            # Save execution report
            await self._save_execution_report(result)
        
        return result
    
    async def _perform_health_check(self, 
                                  instance_configs: List[InstanceConfig],
                                  result: SchedulingResult) -> bool:
        """Perform comprehensive health check."""
        logger.info("Performing health check")
        
        try:
            # Run health check with timeout
            health_status = await asyncio.wait_for(
                self.health_checker.run_comprehensive_health_check(instance_configs),
                timeout=self.scheduling_config.health_check_timeout_minutes * 60
            )
            
            # Evaluate health status
            is_ready, blocking_issues = self.health_checker.is_system_ready_for_update(health_status)
            
            result.health_check_passed = is_ready
            
            if is_ready:
                result.actions_taken.append("Health check passed")
                logger.info("Health check passed - system is ready for update")
            else:
                result.actions_taken.append(f"Health check failed: {'; '.join(blocking_issues)}")
                logger.warning(f"Health check failed with blocking issues: {blocking_issues}")
            
            return is_ready
            
        except asyncio.TimeoutError:
            result.actions_taken.append("Health check timed out")
            logger.error("Health check timed out")
            return False
            
        except Exception as e:
            result.actions_taken.append(f"Health check error: {e}")
            logger.error(f"Health check failed with error: {e}")
            return False
    
    async def _resolve_conflicts(self, 
                               instance_configs: List[InstanceConfig],
                               result: SchedulingResult) -> bool:
        """Detect and resolve scheduling conflicts."""
        logger.info("Detecting and resolving conflicts")
        
        try:
            # Detect conflicts
            instance_names = [config.instance_name for config in instance_configs]
            conflicts = await self.conflict_resolver.detect_conflicts(
                operation_name="monthly_update",
                instance_names=instance_names
            )
            
            if not conflicts:
                result.conflicts_resolved = True
                result.actions_taken.append("No conflicts detected")
                return True
            
            # Attempt to resolve conflicts
            resolution_result = await asyncio.wait_for(
                self.conflict_resolver.resolve_conflicts(conflicts, "monthly_update"),
                timeout=self.scheduling_config.conflict_resolution_timeout_minutes * 60
            )
            
            result.conflicts_resolved = resolution_result.success
            result.actions_taken.extend(resolution_result.actions_taken)
            
            if resolution_result.success:
                logger.info("All conflicts resolved successfully")
            else:
                logger.warning(f"Conflict resolution incomplete: {len(resolution_result.remaining_conflicts)} conflicts remain")
            
            return resolution_result.success
            
        except asyncio.TimeoutError:
            result.actions_taken.append("Conflict resolution timed out")
            logger.error("Conflict resolution timed out")
            return False
            
        except Exception as e:
            result.actions_taken.append(f"Conflict resolution error: {e}")
            logger.error(f"Conflict resolution failed with error: {e}")
            return False
    
    async def _execute_with_recovery(self, 
                                   instance_configs: List[InstanceConfig],
                                   result: SchedulingResult) -> Optional[Any]:
        """Execute orchestration with error recovery."""
        logger.info("Executing orchestration with error recovery")
        
        async def orchestration_operation():
            return await self.orchestrator.run_monthly_updates(
                instance_configs=instance_configs,
                force_update=False
            )
        
        # Execute with recovery
        recovery_result = await self.error_recovery_manager.execute_with_recovery(
            operation=orchestration_operation,
            operation_name="monthly_update_orchestration"
        )
        
        # Record recovery information
        result.actions_taken.append(f"Recovery attempts: {len(recovery_result.attempts)}")
        result.actions_taken.append(f"Recovery time: {recovery_result.total_time_seconds:.1f}s")
        
        if recovery_result.success:
            logger.info("Orchestration completed successfully with recovery")
            return recovery_result.final_result
        else:
            logger.error("Orchestration failed even with recovery")
            result.actions_taken.append("Orchestration failed after recovery attempts")
            return None
    
    async def _execute_without_recovery(self, 
                                      instance_configs: List[InstanceConfig],
                                      result: SchedulingResult) -> Optional[Any]:
        """Execute orchestration without error recovery."""
        logger.info("Executing orchestration without error recovery")
        
        try:
            orchestration_result = await self.orchestrator.run_monthly_updates(
                instance_configs=instance_configs,
                force_update=False
            )
            
            result.actions_taken.append("Orchestration completed without recovery")
            return orchestration_result
            
        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            result.actions_taken.append(f"Orchestration failed: {e}")
            return None
    
    async def _save_execution_report(self, result: SchedulingResult) -> None:
        """Save execution report to file."""
        try:
            reports_dir = Path("/var/log/multi_instance_arxiv/scheduling")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            report_file = reports_dir / f"scheduling_report_{result.execution_id}.json"
            
            with open(report_file, 'w') as f:
                json.dump(result.to_dict(), f, indent=2, default=str)
            
            logger.info(f"Execution report saved: {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save execution report: {e}")
    
    def get_scheduling_statistics(self) -> Dict[str, Any]:
        """Get scheduling statistics and performance metrics."""
        if not self.execution_history:
            return {'total_executions': 0}
        
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for r in self.execution_history if r.success)
        health_check_failures = sum(1 for r in self.execution_history if not r.health_check_passed)
        conflict_resolution_failures = sum(1 for r in self.execution_history if not r.conflicts_resolved)
        
        # Calculate average execution time
        execution_times = [
            (r.end_time - r.start_time).total_seconds() 
            for r in self.execution_history 
            if r.end_time
        ]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        # Recent performance (last 10 executions)
        recent_executions = self.execution_history[-10:]
        recent_success_rate = (
            sum(1 for r in recent_executions if r.success) / len(recent_executions) * 100
            if recent_executions else 0
        )
        
        return {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0,
            'health_check_failures': health_check_failures,
            'conflict_resolution_failures': conflict_resolution_failures,
            'average_execution_time_seconds': avg_execution_time,
            'recent_success_rate': recent_success_rate,
            'configuration': self.scheduling_config.to_dict(),
            'component_statistics': {
                'error_recovery': self.error_recovery_manager.get_error_statistics(),
                'conflict_resolution': self.conflict_resolver.get_conflict_statistics()
            }
        }
    
    async def validate_scheduling_environment(self) -> Tuple[bool, List[str]]:
        """Validate that the scheduling environment is properly configured."""
        issues = []
        
        try:
            # Check component initialization
            if not self.health_checker:
                issues.append("Health checker not initialized")
            
            if not self.error_recovery_manager:
                issues.append("Error recovery manager not initialized")
            
            if not self.conflict_resolver:
                issues.append("Conflict resolver not initialized")
            
            if not self.orchestrator:
                issues.append("Orchestrator not initialized")
            
            # Check configuration validity
            if self.scheduling_config.health_check_timeout_minutes <= 0:
                issues.append("Invalid health check timeout")
            
            if self.scheduling_config.max_execution_time_hours <= 0:
                issues.append("Invalid max execution time")
            
            # Check file system permissions
            log_dir = Path("/var/log/multi_instance_arxiv")
            if not log_dir.exists():
                try:
                    log_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    issues.append(f"Cannot create log directory: {e}")
            
            # Check lock directory
            lock_dir = Path("/tmp/multi_instance_locks")
            if not lock_dir.exists():
                try:
                    lock_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    issues.append(f"Cannot create lock directory: {e}")
            
            is_valid = len(issues) == 0
            return is_valid, issues
            
        except Exception as e:
            issues.append(f"Environment validation failed: {e}")
            return False, issues
    
    def cleanup_old_reports(self, days_to_keep: int = 30) -> int:
        """Clean up old scheduling reports."""
        cleaned_count = 0
        
        try:
            reports_dir = Path("/var/log/multi_instance_arxiv/scheduling")
            if not reports_dir.exists():
                return 0
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            for report_file in reports_dir.glob("scheduling_report_*.json"):
                try:
                    stat = report_file.stat()
                    if datetime.fromtimestamp(stat.st_mtime) < cutoff_date:
                        report_file.unlink()
                        cleaned_count += 1
                except Exception as e:
                    logger.warning(f"Could not clean up report file {report_file}: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} old scheduling reports")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old reports: {e}")
        
        return cleaned_count
    
    async def emergency_stop(self) -> bool:
        """Emergency stop of all scheduling operations."""
        logger.warning("Emergency stop requested for scheduling coordinator")
        
        try:
            # Stop orchestrator
            if hasattr(self.orchestrator, 'stop_orchestration'):
                await self.orchestrator.stop_orchestration()
            
            # Clean up locks
            if hasattr(self.conflict_resolver, 'cleanup_stale_locks'):
                self.conflict_resolver.cleanup_stale_locks()
            
            logger.info("Emergency stop completed")
            return True
            
        except Exception as e:
            logger.error(f"Emergency stop failed: {e}")
            return False