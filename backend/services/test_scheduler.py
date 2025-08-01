"""
Test scheduling and automation service.
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import croniter

from core.redis_client import RedisClient, get_redis_client
from services.test_runner_service import get_test_runner, TestRunner, ComprehensiveTestReport

logger = logging.getLogger(__name__)

class ScheduleStatus(Enum):
    """Schedule status."""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ERROR = "error"

class ExecutionTrigger(Enum):
    """Test execution triggers."""
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    EVENT_DRIVEN = "event_driven"
    HEALTH_CHECK = "health_check"

@dataclass
class TestSchedule:
    """Test execution schedule configuration."""
    schedule_id: str
    name: str
    description: str
    cron_expression: str
    test_suites: List[str]
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    created_at: datetime = None
    last_execution: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    execution_count: int = 0
    failure_count: int = 0
    max_failures: int = 5
    notification_on_failure: bool = True
    timeout_minutes: int = 60
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self._calculate_next_execution()
    
    def _calculate_next_execution(self):
        """Calculate next execution time based on cron expression."""
        try:
            cron = croniter.croniter(self.cron_expression, datetime.now())
            self.next_execution = cron.get_next(datetime)
        except Exception as e:
            logger.error(f"Invalid cron expression for schedule {self.schedule_id}: {e}")
            self.status = ScheduleStatus.ERROR
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **asdict(self),
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'next_execution': self.next_execution.isoformat() if self.next_execution else None
        }

@dataclass
class ScheduledExecution:
    """Scheduled test execution record."""
    execution_id: str
    schedule_id: str
    trigger: ExecutionTrigger
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"
    test_report: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **asdict(self),
            'trigger': self.trigger.value,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class TestScheduler:
    """Test scheduling and automation service."""
    
    def __init__(self, test_runner: Optional[TestRunner] = None):
        self.test_runner = test_runner or get_test_runner()
        self.redis_client = get_redis_client()
        self.schedules: Dict[str, TestSchedule] = {}
        self.executions: Dict[str, ScheduledExecution] = {}
        self.scheduler_running = False
        self.scheduler_task = None
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Load existing schedules
        asyncio.create_task(self._load_schedules())
    
    async def start_scheduler(self):
        """Start the test scheduler."""
        if self.scheduler_running:
            logger.warning("Scheduler already running")
            return
        
        self.scheduler_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Test scheduler started")
    
    async def stop_scheduler(self):
        """Stop the test scheduler."""
        self.scheduler_running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Test scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.scheduler_running:
            try:
                await self._check_scheduled_executions()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)
    
    async def _check_scheduled_executions(self):
        """Check for scheduled executions that need to run."""
        current_time = datetime.now()
        
        for schedule in self.schedules.values():
            if (schedule.status == ScheduleStatus.ACTIVE and 
                schedule.next_execution and 
                schedule.next_execution <= current_time):
                
                # Execute the scheduled test
                await self._execute_scheduled_test(schedule)
    
    async def _execute_scheduled_test(self, schedule: TestSchedule):
        """Execute a scheduled test."""
        execution_id = f"sched_{schedule.schedule_id}_{int(datetime.now().timestamp())}"
        
        execution = ScheduledExecution(
            execution_id=execution_id,
            schedule_id=schedule.schedule_id,
            trigger=ExecutionTrigger.SCHEDULED,
            started_at=datetime.now()
        )
        
        self.executions[execution_id] = execution
        
        try:
            logger.info(f"Starting scheduled test execution: {execution_id}")
            
            # Configure test runner for specific suites
            original_config = self.test_runner.get_test_configuration()
            
            # Update enabled suites based on schedule
            suite_config = {suite: False for suite in original_config['enabled_suites']}
            for suite in schedule.test_suites:
                if suite in suite_config:
                    suite_config[suite] = True
            
            self.test_runner.update_test_configuration({'enabled_suites': suite_config})
            
            # Run tests with timeout
            test_report = await asyncio.wait_for(
                self.test_runner.run_comprehensive_tests(),
                timeout=schedule.timeout_minutes * 60
            )
            
            # Update execution record
            execution.completed_at = datetime.now()
            execution.status = test_report.overall_status.value
            execution.test_report = test_report.to_dict()
            
            # Update schedule
            schedule.last_execution = execution.started_at
            schedule.execution_count += 1
            
            if test_report.overall_status.value in ['failed', 'error']:
                schedule.failure_count += 1
                
                # Disable schedule if too many failures
                if schedule.failure_count >= schedule.max_failures:
                    schedule.status = ScheduleStatus.DISABLED
                    logger.warning(f"Schedule {schedule.schedule_id} disabled due to repeated failures")
                
                # Send failure notification
                if schedule.notification_on_failure:
                    await self._send_failure_notification(schedule, execution, test_report)
            else:
                # Reset failure count on success
                schedule.failure_count = 0
            
            # Calculate next execution
            schedule._calculate_next_execution()
            
            # Restore original configuration
            self.test_runner.update_test_configuration(original_config)
            
            logger.info(f"Scheduled test execution completed: {execution_id}")
        
        except asyncio.TimeoutError:
            execution.completed_at = datetime.now()
            execution.status = "timeout"
            execution.error_message = f"Test execution timed out after {schedule.timeout_minutes} minutes"
            
            schedule.failure_count += 1
            logger.error(f"Scheduled test execution timed out: {execution_id}")
        
        except Exception as e:
            execution.completed_at = datetime.now()
            execution.status = "error"
            execution.error_message = str(e)
            
            schedule.failure_count += 1
            logger.error(f"Scheduled test execution failed: {execution_id} - {e}")
        
        finally:
            # Store execution record
            await self._store_execution(execution)
            await self._store_schedule(schedule)
    
    async def create_schedule(self, name: str, description: str, cron_expression: str, 
                            test_suites: List[str], **kwargs) -> TestSchedule:
        """Create a new test schedule."""
        schedule_id = f"schedule_{int(datetime.now().timestamp())}"
        
        schedule = TestSchedule(
            schedule_id=schedule_id,
            name=name,
            description=description,
            cron_expression=cron_expression,
            test_suites=test_suites,
            **kwargs
        )
        
        # Validate cron expression
        try:
            croniter.croniter(cron_expression)
        except Exception as e:
            raise ValueError(f"Invalid cron expression: {e}")
        
        self.schedules[schedule_id] = schedule
        await self._store_schedule(schedule)
        
        logger.info(f"Created test schedule: {schedule_id} - {name}")
        return schedule
    
    async def update_schedule(self, schedule_id: str, **updates) -> Optional[TestSchedule]:
        """Update an existing test schedule."""
        if schedule_id not in self.schedules:
            return None
        
        schedule = self.schedules[schedule_id]
        
        for key, value in updates.items():
            if hasattr(schedule, key):
                setattr(schedule, key, value)
        
        # Recalculate next execution if cron expression changed
        if 'cron_expression' in updates:
            schedule._calculate_next_execution()
        
        await self._store_schedule(schedule)
        logger.info(f"Updated test schedule: {schedule_id}")
        return schedule
    
    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a test schedule."""
        if schedule_id not in self.schedules:
            return False
        
        del self.schedules[schedule_id]
        
        # Remove from Redis
        try:
            await self.redis_client.delete(f"test_schedule:{schedule_id}")
        except Exception as e:
            logger.error(f"Failed to delete schedule from Redis: {e}")
        
        logger.info(f"Deleted test schedule: {schedule_id}")
        return True
    
    async def get_schedule(self, schedule_id: str) -> Optional[TestSchedule]:
        """Get a specific test schedule."""
        return self.schedules.get(schedule_id)
    
    async def list_schedules(self, status: Optional[ScheduleStatus] = None) -> List[TestSchedule]:
        """List all test schedules, optionally filtered by status."""
        schedules = list(self.schedules.values())
        
        if status:
            schedules = [s for s in schedules if s.status == status]
        
        return sorted(schedules, key=lambda x: x.created_at, reverse=True)
    
    async def execute_schedule_now(self, schedule_id: str) -> Optional[str]:
        """Execute a schedule immediately."""
        if schedule_id not in self.schedules:
            return None
        
        schedule = self.schedules[schedule_id]
        
        # Create manual execution
        execution_id = f"manual_{schedule_id}_{int(datetime.now().timestamp())}"
        
        execution = ScheduledExecution(
            execution_id=execution_id,
            schedule_id=schedule_id,
            trigger=ExecutionTrigger.MANUAL,
            started_at=datetime.now()
        )
        
        self.executions[execution_id] = execution
        
        # Execute in background
        asyncio.create_task(self._execute_manual_test(schedule, execution))
        
        return execution_id
    
    async def _execute_manual_test(self, schedule: TestSchedule, execution: ScheduledExecution):
        """Execute a manual test run."""
        try:
            # Configure and run tests
            original_config = self.test_runner.get_test_configuration()
            
            suite_config = {suite: False for suite in original_config['enabled_suites']}
            for suite in schedule.test_suites:
                if suite in suite_config:
                    suite_config[suite] = True
            
            self.test_runner.update_test_configuration({'enabled_suites': suite_config})
            
            test_report = await self.test_runner.run_comprehensive_tests()
            
            execution.completed_at = datetime.now()
            execution.status = test_report.overall_status.value
            execution.test_report = test_report.to_dict()
            
            # Restore configuration
            self.test_runner.update_test_configuration(original_config)
        
        except Exception as e:
            execution.completed_at = datetime.now()
            execution.status = "error"
            execution.error_message = str(e)
        
        finally:
            await self._store_execution(execution)
    
    async def get_execution_history(self, schedule_id: Optional[str] = None, 
                                  limit: int = 50) -> List[ScheduledExecution]:
        """Get execution history."""
        executions = list(self.executions.values())
        
        if schedule_id:
            executions = [e for e in executions if e.schedule_id == schedule_id]
        
        executions.sort(key=lambda x: x.started_at, reverse=True)
        return executions[:limit]
    
    async def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler for test automation."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered event handler for: {event_type}")
    
    async def trigger_event(self, event_type: str, event_data: Dict[str, Any]):
        """Trigger event-driven test execution."""
        if event_type not in self.event_handlers:
            return
        
        for handler in self.event_handlers[event_type]:
            try:
                await handler(event_data)
            except Exception as e:
                logger.error(f"Event handler failed for {event_type}: {e}")
    
    async def create_health_check_schedule(self, interval_minutes: int = 30):
        """Create a health check schedule."""
        cron_expression = f"*/{interval_minutes} * * * *"
        
        return await self.create_schedule(
            name="Health Check Tests",
            description="Automated health check tests",
            cron_expression=cron_expression,
            test_suites=["api_tests", "database_tests"],
            timeout_minutes=10,
            max_failures=3
        )
    
    async def _load_schedules(self):
        """Load schedules from Redis."""
        try:
            # Get all schedule keys
            keys = await self.redis_client.keys("test_schedule:*")
            
            for key in keys:
                schedule_data = await self.redis_client.get(key)
                if schedule_data:
                    schedule_dict = schedule_data if isinstance(schedule_data, dict) else json.loads(schedule_data)
                    
                    # Reconstruct schedule object
                    schedule = TestSchedule(
                        schedule_id=schedule_dict['schedule_id'],
                        name=schedule_dict['name'],
                        description=schedule_dict['description'],
                        cron_expression=schedule_dict['cron_expression'],
                        test_suites=schedule_dict['test_suites'],
                        status=ScheduleStatus(schedule_dict['status']),
                        created_at=datetime.fromisoformat(schedule_dict['created_at']),
                        last_execution=datetime.fromisoformat(schedule_dict['last_execution']) if schedule_dict.get('last_execution') else None,
                        execution_count=schedule_dict.get('execution_count', 0),
                        failure_count=schedule_dict.get('failure_count', 0),
                        max_failures=schedule_dict.get('max_failures', 5),
                        notification_on_failure=schedule_dict.get('notification_on_failure', True),
                        timeout_minutes=schedule_dict.get('timeout_minutes', 60)
                    )
                    
                    self.schedules[schedule.schedule_id] = schedule
            
            logger.info(f"Loaded {len(self.schedules)} test schedules")
        
        except Exception as e:
            logger.error(f"Failed to load schedules: {e}")
    
    async def _store_schedule(self, schedule: TestSchedule):
        """Store schedule in Redis."""
        try:
            key = f"test_schedule:{schedule.schedule_id}"
            await self.redis_client.set(key, schedule.to_dict(), ex=365 * 24 * 3600)  # Keep for 1 year
        except Exception as e:
            logger.error(f"Failed to store schedule: {e}")
    
    async def _store_execution(self, execution: ScheduledExecution):
        """Store execution record in Redis."""
        try:
            key = f"test_execution:{execution.execution_id}"
            await self.redis_client.set(key, execution.to_dict(), ex=90 * 24 * 3600)  # Keep for 90 days
        except Exception as e:
            logger.error(f"Failed to store execution: {e}")
    
    async def _send_failure_notification(self, schedule: TestSchedule, 
                                       execution: ScheduledExecution, 
                                       test_report: ComprehensiveTestReport):
        """Send failure notification."""
        # This would integrate with notification services
        # For now, just log the failure
        logger.warning(f"Test schedule failed: {schedule.name} (ID: {schedule.schedule_id})")
        logger.warning(f"Execution ID: {execution.execution_id}")
        logger.warning(f"Status: {execution.status}")
        
        if test_report:
            failed_suites = [suite.suite_name for suite in test_report.test_suites if suite.failed_tests > 0]
            if failed_suites:
                logger.warning(f"Failed test suites: {', '.join(failed_suites)}")

# Global scheduler instance
test_scheduler = TestScheduler()

def get_test_scheduler() -> TestScheduler:
    """Get the global test scheduler instance."""
    return test_scheduler