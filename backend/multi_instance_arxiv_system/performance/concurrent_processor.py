"""
Concurrent Processing System for Multi-Instance ArXiv System.

This module provides configurable batch processing with concurrency limits,
memory management, and resource isolation between instances.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from datetime import datetime, timedelta
import logging
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
import queue
import time

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.performance.memory_manager import MemoryManager
    from multi_instance_arxiv_system.shared.multi_instance_data_models import ProcessingError
except ImportError as e:
    print(f"Import error: {e}")
    # Create minimal fallback classes for testing
    class MemoryManager:
        def __init__(self, *args, **kwargs): pass
        def check_memory_usage(self): 
            class MockMemoryStats:
                available_memory_mb = 1000
                used_memory_mb = 100
            return MockMemoryStats()
        def cleanup_if_needed(self): return True
    
    class ProcessingError:
        def __init__(self, file_path, error_message, error_type, timestamp):
            self.file_path = file_path
            self.error_message = error_message
            self.error_type = error_type
            self.timestamp = timestamp

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProcessingTask:
    """Represents a processing task with metadata and configuration."""
    
    task_id: str
    instance_name: str
    task_type: str  # 'download', 'process', 'embed', 'index'
    priority: TaskPriority
    
    # Task data
    input_data: Any
    processing_function: Callable
    callback_function: Optional[Callable] = None
    
    # Configuration
    max_retries: int = 3
    timeout_seconds: int = 300
    memory_limit_mb: int = 1024
    
    # Status tracking
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results and errors
    result: Any = None
    error: Optional[Exception] = None
    retry_count: int = 0
    
    @property
    def execution_time_seconds(self) -> Optional[float]:
        """Get task execution time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_expired(self) -> bool:
        """Check if task has exceeded timeout."""
        if self.started_at and self.status == TaskStatus.RUNNING:
            elapsed = (datetime.now() - self.started_at).total_seconds()
            return elapsed > self.timeout_seconds
        return False
    
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries and self.status == TaskStatus.FAILED


@dataclass
class ProcessingStats:
    """Statistics for concurrent processing operations."""
    
    instance_name: str
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    cancelled_tasks: int = 0
    
    # Performance metrics
    average_execution_time: float = 0.0
    total_processing_time: float = 0.0
    throughput_tasks_per_second: float = 0.0
    
    # Resource usage
    peak_memory_usage_mb: int = 0
    average_cpu_usage: float = 0.0
    
    # Error tracking
    error_rate: float = 0.0
    most_common_errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100.0


class ConcurrentProcessor:
    """
    High-performance concurrent processor with memory management and resource isolation.
    Supports configurable batch processing, rate limiting, and instance separation.
    """
    
    def __init__(
        self,
        instance_name: str,
        max_workers: int = 4,
        max_concurrent_tasks: int = 10,
        memory_limit_mb: int = 4096,
        enable_process_pool: bool = False
    ):
        self.instance_name = instance_name
        self.max_workers = max_workers
        self.max_concurrent_tasks = max_concurrent_tasks
        self.enable_process_pool = enable_process_pool
        
        # Initialize memory manager
        self.memory_manager = MemoryManager(instance_name, memory_limit_mb)
        
        # Task management
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.active_tasks: Dict[str, ProcessingTask] = {}
        self.completed_tasks: List[ProcessingTask] = []
        self.task_history_limit = 1000
        
        # Executors
        self.thread_executor: Optional[ThreadPoolExecutor] = None
        self.process_executor: Optional[ProcessPoolExecutor] = None
        
        # Control flags
        self.is_running = False
        self.shutdown_requested = False
        
        # Statistics
        self.stats = ProcessingStats(instance_name)
        
        # Rate limiting
        self.rate_limiter = RateLimiter(max_requests_per_second=10)
        
        # Monitoring
        self.last_health_check = datetime.now()
        self.health_check_interval = timedelta(minutes=5)
        
        logger.info(f"ConcurrentProcessor initialized for {instance_name} with {max_workers} workers")
    
    async def start(self) -> None:
        """Start the concurrent processor."""
        
        if self.is_running:
            logger.warning(f"Processor for {self.instance_name} is already running")
            return
        
        logger.info(f"Starting concurrent processor for {self.instance_name}")
        
        # Initialize executors
        self.thread_executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix=f"{self.instance_name}_thread"
        )
        
        if self.enable_process_pool:
            self.process_executor = ProcessPoolExecutor(
                max_workers=max(1, self.max_workers // 2)
            )
        
        self.is_running = True
        self.shutdown_requested = False
        
        # Start background tasks
        asyncio.create_task(self._task_processor())
        asyncio.create_task(self._health_monitor())
        asyncio.create_task(self._cleanup_completed_tasks())
        
        logger.info(f"Concurrent processor started for {self.instance_name}")
    
    async def stop(self) -> None:
        """Stop the concurrent processor gracefully."""
        
        logger.info(f"Stopping concurrent processor for {self.instance_name}")
        
        self.shutdown_requested = True
        
        # Wait for active tasks to complete (with timeout)
        timeout = 30  # seconds
        start_time = time.time()
        
        while self.active_tasks and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)
        
        # Cancel remaining tasks
        for task in self.active_tasks.values():
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
        
        # Shutdown executors
        if self.thread_executor:
            self.thread_executor.shutdown(wait=True)
            self.thread_executor = None
        
        if self.process_executor:
            self.process_executor.shutdown(wait=True)
            self.process_executor = None
        
        self.is_running = False
        logger.info(f"Concurrent processor stopped for {self.instance_name}")
    
    async def submit_task(self, task: ProcessingTask) -> str:
        """Submit a task for processing."""
        
        if self.shutdown_requested:
            raise RuntimeError("Processor is shutting down")
        
        # Check memory availability
        memory_stats = self.memory_manager.check_memory_usage()
        if memory_stats.available_memory_mb < task.memory_limit_mb:
            # Try to free memory
            if not self.memory_manager.cleanup_if_needed():
                raise RuntimeError(f"Insufficient memory for task {task.task_id}")
        
        # Add to queue with priority
        priority_value = -task.priority.value  # Negative for max-heap behavior
        self.task_queue.put((priority_value, task.created_at, task))
        
        logger.debug(f"Task {task.task_id} submitted to queue for {self.instance_name}")
        return task.task_id
    
    async def submit_batch(
        self,
        tasks: List[ProcessingTask],
        batch_size: int = 10,
        delay_between_batches: float = 0.1
    ) -> List[str]:
        """Submit a batch of tasks with rate limiting."""
        
        task_ids = []
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            
            # Submit batch
            for task in batch:
                task_id = await self.submit_task(task)
                task_ids.append(task_id)
            
            # Rate limiting delay
            if i + batch_size < len(tasks):
                await asyncio.sleep(delay_between_batches)
        
        logger.info(f"Submitted batch of {len(tasks)} tasks for {self.instance_name}")
        return task_ids
    
    async def _task_processor(self) -> None:
        """Main task processing loop."""
        
        while not self.shutdown_requested:
            try:
                # Check if we can process more tasks
                if len(self.active_tasks) >= self.max_concurrent_tasks:
                    await asyncio.sleep(0.1)
                    continue
                
                # Get next task from queue
                try:
                    priority, created_at, task = self.task_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.1)
                    continue
                
                # Check rate limiting
                if not self.rate_limiter.can_proceed():
                    # Put task back in queue
                    self.task_queue.put((priority, created_at, task))
                    await asyncio.sleep(0.1)
                    continue
                
                # Start task processing
                await self._execute_task(task)
                
            except Exception as e:
                logger.error(f"Error in task processor for {self.instance_name}: {e}")
                await asyncio.sleep(1)
    
    async def _execute_task(self, task: ProcessingTask) -> None:
        """Execute a single task."""
        
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self.active_tasks[task.task_id] = task
        
        try:
            # Choose executor based on task type and configuration
            executor = self._choose_executor(task)
            
            # Execute task
            loop = asyncio.get_event_loop()
            
            if executor == self.process_executor:
                # Process pool execution
                future = executor.submit(self._execute_task_function, task)
                task.result = await loop.run_in_executor(None, future.result)
            else:
                # Thread pool execution
                task.result = await loop.run_in_executor(
                    executor, 
                    self._execute_task_function, 
                    task
                )
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            # Execute callback if provided
            if task.callback_function:
                try:
                    await self._execute_callback(task)
                except Exception as e:
                    logger.error(f"Callback failed for task {task.task_id}: {e}")
            
            logger.debug(f"Task {task.task_id} completed successfully")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = e
            task.completed_at = datetime.now()
            
            logger.error(f"Task {task.task_id} failed: {e}")
            
            # Retry if possible
            if task.can_retry():
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                task.started_at = None
                task.completed_at = None
                task.error = None
                
                # Re-submit with lower priority
                priority_value = -(task.priority.value - 1)
                self.task_queue.put((priority_value, datetime.now(), task))
                
                logger.info(f"Task {task.task_id} queued for retry ({task.retry_count}/{task.max_retries})")
        
        finally:
            # Move to completed tasks
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
            
            self.completed_tasks.append(task)
            self._update_stats(task)
    
    def _execute_task_function(self, task: ProcessingTask) -> Any:
        """Execute the task function (runs in executor)."""
        
        try:
            # Check if task is expired
            if task.is_expired:
                raise TimeoutError(f"Task {task.task_id} exceeded timeout of {task.timeout_seconds}s")
            
            # Execute the processing function
            return task.processing_function(task.input_data)
            
        except Exception as e:
            logger.error(f"Task function execution failed for {task.task_id}: {e}")
            raise
    
    async def _execute_callback(self, task: ProcessingTask) -> None:
        """Execute task callback function."""
        
        try:
            if asyncio.iscoroutinefunction(task.callback_function):
                await task.callback_function(task)
            else:
                task.callback_function(task)
        except Exception as e:
            logger.error(f"Callback execution failed for task {task.task_id}: {e}")
            raise
    
    def _choose_executor(self, task: ProcessingTask) -> Union[ThreadPoolExecutor, ProcessPoolExecutor]:
        """Choose appropriate executor for task."""
        
        # Use process pool for CPU-intensive tasks if available
        if (self.process_executor and 
            task.task_type in ['process', 'embed'] and 
            task.memory_limit_mb > 512):
            return self.process_executor
        
        return self.thread_executor
    
    def _update_stats(self, task: ProcessingTask) -> None:
        """Update processing statistics."""
        
        self.stats.total_tasks += 1
        
        if task.status == TaskStatus.COMPLETED:
            self.stats.completed_tasks += 1
            
            if task.execution_time_seconds:
                self.stats.total_processing_time += task.execution_time_seconds
                self.stats.average_execution_time = (
                    self.stats.total_processing_time / self.stats.completed_tasks
                )
        
        elif task.status == TaskStatus.FAILED:
            self.stats.failed_tasks += 1
            
            if task.error:
                error_type = type(task.error).__name__
                if error_type not in self.stats.most_common_errors:
                    self.stats.most_common_errors.append(error_type)
        
        elif task.status == TaskStatus.CANCELLED:
            self.stats.cancelled_tasks += 1
        
        # Update rates
        if self.stats.total_tasks > 0:
            self.stats.error_rate = (self.stats.failed_tasks / self.stats.total_tasks) * 100.0
        
        # Update throughput (tasks per second over last hour)
        recent_tasks = [
            t for t in self.completed_tasks[-100:]  # Last 100 tasks
            if t.completed_at and t.completed_at > datetime.now() - timedelta(hours=1)
        ]
        
        if len(recent_tasks) > 1:
            time_span = (recent_tasks[-1].completed_at - recent_tasks[0].completed_at).total_seconds()
            if time_span > 0:
                self.stats.throughput_tasks_per_second = len(recent_tasks) / time_span
    
    async def _health_monitor(self) -> None:
        """Monitor processor health and performance."""
        
        while not self.shutdown_requested:
            try:
                current_time = datetime.now()
                
                if current_time - self.last_health_check >= self.health_check_interval:
                    await self._perform_health_check()
                    self.last_health_check = current_time
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Health monitor error for {self.instance_name}: {e}")
                await asyncio.sleep(60)
    
    async def _perform_health_check(self) -> None:
        """Perform health check and cleanup."""
        
        # Check for expired tasks
        expired_tasks = [
            task for task in self.active_tasks.values()
            if task.is_expired
        ]
        
        for task in expired_tasks:
            logger.warning(f"Task {task.task_id} expired, marking as failed")
            task.status = TaskStatus.FAILED
            task.error = TimeoutError(f"Task exceeded timeout of {task.timeout_seconds}s")
            task.completed_at = datetime.now()
        
        # Memory cleanup
        memory_stats = self.memory_manager.check_memory_usage()
        if memory_stats.available_memory_mb < 500:  # Less than 500MB available
            logger.warning(f"Low memory detected for {self.instance_name}, performing cleanup")
            self.memory_manager.cleanup_if_needed()
        
        # Update resource usage stats
        self.stats.peak_memory_usage_mb = max(
            self.stats.peak_memory_usage_mb,
            memory_stats.used_memory_mb
        )
    
    async def _cleanup_completed_tasks(self) -> None:
        """Clean up old completed tasks to prevent memory leaks."""
        
        while not self.shutdown_requested:
            try:
                # Keep only recent completed tasks
                if len(self.completed_tasks) > self.task_history_limit:
                    # Sort by completion time and keep most recent
                    self.completed_tasks.sort(
                        key=lambda t: t.completed_at or datetime.min,
                        reverse=True
                    )
                    self.completed_tasks = self.completed_tasks[:self.task_history_limit]
                
                await asyncio.sleep(300)  # Clean up every 5 minutes
                
            except Exception as e:
                logger.error(f"Cleanup error for {self.instance_name}: {e}")
                await asyncio.sleep(300)
    
    def get_task_status(self, task_id: str) -> Optional[ProcessingTask]:
        """Get status of a specific task."""
        
        # Check active tasks
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        
        # Check completed tasks
        for task in self.completed_tasks:
            if task.task_id == task_id:
                return task
        
        return None
    
    def get_processing_stats(self) -> ProcessingStats:
        """Get current processing statistics."""
        return self.stats
    
    def get_active_task_count(self) -> int:
        """Get number of currently active tasks."""
        return len(self.active_tasks)
    
    def get_queue_size(self) -> int:
        """Get number of tasks in queue."""
        return self.task_queue.qsize()
    
    async def wait_for_completion(self, timeout_seconds: Optional[int] = None) -> bool:
        """Wait for all tasks to complete."""
        
        start_time = time.time()
        
        while (self.active_tasks or not self.task_queue.empty()):
            if timeout_seconds and (time.time() - start_time) > timeout_seconds:
                return False
            
            await asyncio.sleep(0.1)
        
        return True
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a specific task."""
        
        task = self.get_task_status(task_id)
        if task and task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                self.completed_tasks.append(task)
            
            return True
        
        return False


class RateLimiter:
    """Simple rate limiter for controlling task submission rate."""
    
    def __init__(self, max_requests_per_second: float):
        self.max_requests_per_second = max_requests_per_second
        self.min_interval = 1.0 / max_requests_per_second
        self.last_request_time = 0.0
        self.lock = threading.Lock()
    
    def can_proceed(self) -> bool:
        """Check if a request can proceed based on rate limit."""
        
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last >= self.min_interval:
                self.last_request_time = current_time
                return True
            
            return False
    
    def wait_if_needed(self) -> None:
        """Block until rate limit allows proceeding."""
        
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()