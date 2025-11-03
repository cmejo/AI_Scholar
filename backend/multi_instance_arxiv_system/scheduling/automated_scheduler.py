#!/usr/bin/env python3
"""
Automated Scheduler for multi-instance ArXiv system.

Provides comprehensive automated scheduling with health checks, conflict resolution,
and error recovery for monthly updates and maintenance tasks.
"""

import asyncio
import logging
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from .cron_scheduler import CronScheduler, CronJobConfig
from .health_checker import HealthChecker, SystemHealthStatus
from .error_recovery_manager import ErrorRecoveryManager, RecoveryConfig
from .conflict_resolver import ConflictResolver, ConflictInfo
from .monthly_update_orchestrator import MonthlyUpdateOrchestrator, OrchestrationConfig
try:
    from ..shared.multi_instance_data_models import InstanceConfig
except ImportError:
    # Fallback for testing
    from dataclasses import dataclass
    from typing import List, Optional
    
    @dataclass
    class InstanceConfig:
        instance_name: str
        display_name: str = ""
        description: str = ""
        arxiv_categories: List[str] = None
        journal_sources: List[str] = None
        storage_paths: Optional[object] = None
        vector_store_config: Optional[object] = None
        processing_config: Optional[object] = None
        notification_config: Optional[object] = None

logger = logging.getLogger(__name__)


@dataclass
class SchedulingConfig:
    """Configuration for automated scheduling."""
    enable_health_checks: bool = True
    enable_conflict_resolution: bool = True
    enable_error_recovery: bool = True
    max_retry_attempts: int = 3
    health_check_timeout_minutes: int = 10
    conflict_resolution_timeout_minutes: int = 30
    pre_execution_delay_minutes: int = 5
    post_execution_cleanup: bool = True
    notification_on_failure: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'enable_health_checks': self.enable_health_checks,
            'enable_conflict_resolution': self.enable_conflict_resolution,
            'enable_error_recovery': self.enable_error_recovery,
            'max_retry_attempts': self.max_retry_attempts,
            'health_check_timeout_minutes': self.health_check_timeout_minutes,
            'conflict_resolution_timeout_minutes': self.conflict_resolution_timeout_minutes,
            'pre_execution_delay_minutes': self.pre_execution_delay_minutes,
            'post_execution_cleanup': self.post_execution_cleanup,
            'notification_on_failure': self.notification_on_failure
        }


@dataclass
class ScheduledExecutionResult:
    """Result of a scheduled execution."""
    execution_id: str
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    health_check_passed: bool = False
    conflicts_resolved: bool = False
    execution_result: Any = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'execution_id': self.execution_id,
            'operation_name': self.operation_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'success': self.success,
            'health_check_passed': self.health_check_passed,
            'conflicts_resolved': self.conflicts_resolved,
            'execution_result': str(self.execution_result) if self.execution_result else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count
        }


class AutomatedScheduler:
    """Comprehensive automated scheduler with health checks and error recovery."""
    
    def __init__(self, 
                 config: Optional[SchedulingConfig] = None,
                 recovery_config: Optional[RecoveryConfig] = None):
        """
        Initialize automated scheduler.
        
        Args:
            config: Scheduling configuration
            recovery_config: Error recovery configuration
        """
        self.config = config or SchedulingConfig()
        
        # Initialize components
        self.cron_scheduler = CronScheduler()
        self.health_checker = HealthChecker()
        self.error_recovery = ErrorRecoveryManager(recovery_config)
        self.conflict_resolver = ConflictResolver()
        
        # Execution history
        self.execution_history: List[ScheduledExecutionResult] = []
        
        logger.info("AutomatedScheduler initialized")
    
    async def setup_monthly_scheduling(self, 
                                     instance_configs: List[InstanceConfig],
                                     schedule: str = "0 2 1 * *") -> bool:
        """
        Set up automated monthly scheduling for all instances.
        
        Args:
            instance_configs: List of instance configurations
            schedule: Cron schedule expression
            
        Returns:
            True if setup successful, False otherwise
        """
        logger.info("Setting up automated monthly scheduling")
        
        try:
            # Validate schedule
            if not self.cron_scheduler.validate_schedule(schedule):
                logger.error(f"Invalid cron schedule: {schedule}")
                return False
            
            # Create instance names list
            instance_names = [config.instance_name for config in instance_configs]
            
            # Add monthly update job with health checks and conflict resolution
            success = self.cron_scheduler.add_monthly_update_job(
                instance_names=instance_names,
                schedule=schedule,
                python_path=sys.executable,
                script_path=str(Path(__file__).parent / "run_scheduled_monthly_update.py")
            )
            
            if not success:
                logger.error("Failed to add monthly update job")
                return False
            
            # Add health check job (every 6 hours)
            success = self.cron_scheduler.add_health_check_job(
                schedule="0 */6 * * *",
                python_path=sys.executable,
                script_path=str(Path(__file__).parent / "run_health_check.py")
            )
            
            if not success:
                logger.error("Failed to add health check job")
                return False
            
            # Install cron jobs
            success = self.cron_scheduler.install_cron_jobs()
            
            if success:
                logger.info("Automated monthly scheduling setup completed")
                return True
            else:
                logger.error("Failed to install cron jobs")
                return False
                
        except Exception as e:
            logger.error(f"Failed to setup monthly scheduling: {e}")
            return False
    
    async def execute_with_validation(self,
                                    operation_name: str,
                                    operation_func,
                                    instance_configs: Optional[List[InstanceConfig]] = None,
                                    *args,
                                    **kwargs) -> ScheduledExecutionResult:
        """
        Execute an operation with comprehensive validation and error handling.
        
        Args:
            operation_name: Name of the operation
            operation_func: Function to execute
            instance_configs: Optional instance configurations for validation
            *args: Arguments to pass to operation
            **kwargs: Keyword arguments to pass to operation
            
        Returns:
            ScheduledExecutionResult with execution details
        """
        execution_id = f"{operation_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result = ScheduledExecutionResult(
            execution_id=execution_id,
            operation_name=operation_name,
            start_time=datetime.now()
        )
        
        logger.info(f"Starting scheduled execution: {execution_id}")
        
        try:
            # Step 1: Pre-execution delay
            if self.config.pre_execution_delay_minutes > 0:
                logger.info(f"Pre-execution delay: {self.config.pre_execution_delay_minutes} minutes")
                await asyncio.sleep(self.config.pre_execution_delay_minutes * 60)
            
            # Step 2: Health check
            if self.config.enable_health_checks:
                logger.info("Running pre-execution health check")
                health_status = await self._run_health_check_with_timeout(instance_configs)
                
                if health_status:
                    is_ready, blocking_issues = self.health_checker.is_system_ready_for_update(health_status)
                    result.health_check_passed = is_ready
                    
                    if not is_ready:
                        result.error_message = f"Health check failed: {'; '.join(blocking_issues)}"
                        logger.error(f"Health check failed for {operation_name}: {result.error_message}")
                        return result
                    
                    logger.info("Health check passed")
                else:
                    logger.warning("Health check timed out, proceeding with caution")
            
            # Step 3: Conflict detection and resolution
            if self.config.enable_conflict_resolution:
                logger.info("Checking for scheduling conflicts")
                conflicts = await self.conflict_resolver.detect_conflicts(
                    operation_name=operation_name,
                    instance_names=[c.instance_name for c in instance_configs] if instance_configs else None
                )
                
                if conflicts:
                    logger.warning(f"Found {len(conflicts)} conflicts, attempting resolution")
                    resolution_result = await self.conflict_resolver.resolve_conflicts(conflicts, operation_name)
                    result.conflicts_resolved = resolution_result.success
                    
                    if not resolution_result.success:
                        result.error_message = f"Failed to resolve conflicts: {len(resolution_result.remaining_conflicts)} remaining"
                        logger.error(f"Conflict resolution failed for {operation_name}")
                        return result
                    
                    logger.info("Conflicts resolved successfully")
                else:
                    result.conflicts_resolved = True
                    logger.info("No conflicts detected")
            
            # Step 4: Execute operation with error recovery
            if self.config.enable_error_recovery:
                logger.info("Executing operation with error recovery")
                recovery_result = await self.error_recovery.execute_with_recovery(
                    operation=operation_func,
                    operation_name=operation_name,
                    *args,
                    **kwargs
                )
                
                result.success = recovery_result.success
                result.execution_result = recovery_result.final_result
                result.retry_count = len(recovery_result.attempts)
                
                if not recovery_result.success:
                    result.error_message = f"Operation failed after {result.retry_count} attempts"
                    logger.error(f"Operation {operation_name} failed with error recovery")
                else:
                    logger.info(f"Operation {operation_name} completed successfully")
            else:
                # Execute without error recovery
                logger.info("Executing operation without error recovery")
                try:
                    execution_result = await operation_func(*args, **kwargs)
                    result.success = True
                    result.execution_result = execution_result
                    logger.info(f"Operation {operation_name} completed successfully")
                except Exception as e:
                    result.success = False
                    result.error_message = str(e)
                    logger.error(f"Operation {operation_name} failed: {e}")
            
        except Exception as e:
            result.success = False
            result.error_message = f"Execution framework error: {e}"
            logger.error(f"Execution framework error for {operation_name}: {e}")
        
        finally:
            result.end_time = datetime.now()
            
            # Step 5: Post-execution cleanup
            if self.config.post_execution_cleanup:
                await self._post_execution_cleanup(operation_name)
            
            # Record execution
            self.execution_history.append(result)
            
            # Keep only recent history (last 100 executions)
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]
            
            logger.info(f"Scheduled execution completed: {execution_id}, success={result.success}")
        
        return result
    
    async def _run_health_check_with_timeout(self, 
                                           instance_configs: Optional[List[InstanceConfig]]) -> Optional[SystemHealthStatus]:
        """Run health check with timeout."""
        try:
            return await asyncio.wait_for(
                self.health_checker.run_comprehensive_health_check(instance_configs),
                timeout=self.config.health_check_timeout_minutes * 60
            )
        except asyncio.TimeoutError:
            logger.warning("Health check timed out")
            return None
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return None
    
    async def _post_execution_cleanup(self, operation_name: str) -> None:
        """Perform post-execution cleanup."""
        try:
            logger.debug(f"Running post-execution cleanup for {operation_name}")
            
            # Clean up stale locks
            cleaned_locks = self.conflict_resolver.cleanup_stale_locks()
            if cleaned_locks > 0:
                logger.info(f"Cleaned up {cleaned_locks} stale lock files")
            
            # Clean up temporary files (implementation depends on specific needs)
            # This is a placeholder for actual cleanup logic
            
        except Exception as e:
            logger.warning(f"Post-execution cleanup failed: {e}")
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution statistics and performance metrics."""
        if not self.execution_history:
            return {'total_executions': 0}
        
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for exec in self.execution_history if exec.success)
        
        # Calculate success rate by operation
        operation_stats = {}
        for execution in self.execution_history:
            op_name = execution.operation_name
            if op_name not in operation_stats:
                operation_stats[op_name] = {'total': 0, 'successful': 0}
            
            operation_stats[op_name]['total'] += 1
            if execution.success:
                operation_stats[op_name]['successful'] += 1
        
        # Calculate average execution time
        completed_executions = [e for e in self.execution_history if e.end_time]
        avg_duration = 0
        if completed_executions:
            total_duration = sum(
                (e.end_time - e.start_time).total_seconds() 
                for e in completed_executions
            )
            avg_duration = total_duration / len(completed_executions)
        
        # Recent performance (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_executions = [
            e for e in self.execution_history 
            if e.start_time > recent_cutoff
        ]
        
        return {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0,
            'average_duration_seconds': avg_duration,
            'operation_statistics': {
                op: {
                    'total': stats['total'],
                    'successful': stats['successful'],
                    'success_rate': (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
                }
                for op, stats in operation_stats.items()
            },
            'recent_executions_24h': len(recent_executions),
            'recent_success_rate_24h': (
                sum(1 for e in recent_executions if e.success) / len(recent_executions) * 100
            ) if recent_executions else 0
        }
    
    def export_execution_report(self, output_path: Path) -> bool:
        """Export comprehensive execution report."""
        try:
            report = {
                'report_type': 'automated_scheduler_report',
                'generated_at': datetime.now().isoformat(),
                'config': self.config.to_dict(),
                'statistics': self.get_execution_statistics(),
                'recent_executions': [
                    exec.to_dict() for exec in self.execution_history[-20:]  # Last 20 executions
                ],
                'error_recovery_stats': self.error_recovery.get_error_statistics(),
                'conflict_resolution_stats': self.conflict_resolver.get_conflict_statistics()
            }
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Execution report exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export execution report: {e}")
            return False
    
    async def validate_scheduling_setup(self) -> Tuple[bool, List[str]]:
        """
        Validate the current scheduling setup.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        try:
            # Check cron jobs
            cron_jobs = self.cron_scheduler.list_cron_jobs()
            if not cron_jobs:
                issues.append("No cron jobs configured")
            else:
                for job in cron_jobs:
                    if not self.cron_scheduler.validate_schedule(job['schedule']):
                        issues.append(f"Invalid schedule for job '{job['name']}': {job['schedule']}")
            
            # Check system health
            health_status = await self.health_checker.run_comprehensive_health_check()
            if health_status.overall_status == 'critical':
                issues.append("System health is critical")
            
            # Check for conflicts
            conflicts = await self.conflict_resolver.detect_conflicts("validation_check")
            critical_conflicts = [c for c in conflicts if c.severity.value == 'critical']
            if critical_conflicts:
                issues.append(f"Critical scheduling conflicts detected: {len(critical_conflicts)}")
            
            # Check error recovery configuration
            if not self.config.enable_error_recovery:
                issues.append("Error recovery is disabled")
            
            is_valid = len(issues) == 0
            return is_valid, issues
            
        except Exception as e:
            issues.append(f"Validation check failed: {e}")
            return False, issues