"""
Load Balancing and Scalability System for Multi-Instance ArXiv System.

This module provides configurable worker processes, thread pools, load balancing,
and dynamic resource allocation based on system load.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
import logging
import threading
import asyncio
import time
import random
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future
from dataclasses import dataclass, field
from enum import Enum
import queue
import multiprocessing

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RESOURCE_BASED = "resource_based"
    RANDOM = "random"


class WorkerStatus(Enum):
    """Worker status states."""
    IDLE = "idle"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    FAILED = "failed"
    SHUTDOWN = "shutdown"


@dataclass
class WorkerStats:
    """Statistics for a worker."""
    
    worker_id: str
    status: WorkerStatus
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_task_duration: float
    cpu_usage: float
    memory_usage_mb: int
    last_activity: datetime
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        total_tasks = self.completed_tasks + self.failed_tasks
        if total_tasks == 0:
            return 100.0
        return (self.completed_tasks / total_tasks) * 100.0
    
    @property
    def load_score(self) -> float:
        """Calculate load score for balancing decisions."""
        # Higher score means more loaded
        base_score = self.active_tasks * 10
        
        # Add CPU and memory factors
        base_score += self.cpu_usage * 0.5
        base_score += (self.memory_usage_mb / 1024) * 0.3
        
        # Penalize failed tasks
        if self.failed_tasks > 0:
            base_score += self.failed_tasks * 2
        
        return base_score


@dataclass
class WorkerPool:
    """Pool of workers with load balancing."""
    
    pool_id: str
    workers: Dict[str, 'Worker'] = field(default_factory=dict)
    strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_CONNECTIONS
    max_workers: int = 4
    min_workers: int = 1
    
    # Load balancing state
    round_robin_index: int = 0
    worker_weights: Dict[str, float] = field(default_factory=dict)
    
    def add_worker(self, worker: 'Worker') -> None:
        """Add a worker to the pool."""
        self.workers[worker.worker_id] = worker
        self.worker_weights[worker.worker_id] = 1.0
    
    def remove_worker(self, worker_id: str) -> bool:
        """Remove a worker from the pool."""
        if worker_id in self.workers:
            del self.workers[worker_id]
            if worker_id in self.worker_weights:
                del self.worker_weights[worker_id]
            return True
        return False
    
    def get_available_workers(self) -> List['Worker']:
        """Get list of available workers."""
        return [
            worker for worker in self.workers.values()
            if worker.status in [WorkerStatus.IDLE, WorkerStatus.BUSY] and not worker.is_overloaded()
        ]
    
    def select_worker(self) -> Optional['Worker']:
        """Select a worker based on the load balancing strategy."""
        
        available_workers = self.get_available_workers()
        if not available_workers:
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._select_round_robin(available_workers)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._select_least_connections(available_workers)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._select_weighted_round_robin(available_workers)
        elif self.strategy == LoadBalancingStrategy.RESOURCE_BASED:
            return self._select_resource_based(available_workers)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return random.choice(available_workers)
        else:
            return available_workers[0]
    
    def _select_round_robin(self, workers: List['Worker']) -> 'Worker':
        """Select worker using round-robin strategy."""
        worker = workers[self.round_robin_index % len(workers)]
        self.round_robin_index = (self.round_robin_index + 1) % len(workers)
        return worker
    
    def _select_least_connections(self, workers: List['Worker']) -> 'Worker':
        """Select worker with least active connections."""
        return min(workers, key=lambda w: w.get_stats().active_tasks)
    
    def _select_weighted_round_robin(self, workers: List['Worker']) -> 'Worker':
        """Select worker using weighted round-robin strategy."""
        # Simple weighted selection based on worker weights
        total_weight = sum(self.worker_weights.get(w.worker_id, 1.0) for w in workers)
        if total_weight == 0:
            return workers[0]
        
        # Select based on cumulative weights
        target = random.uniform(0, total_weight)
        cumulative = 0
        
        for worker in workers:
            cumulative += self.worker_weights.get(worker.worker_id, 1.0)
            if cumulative >= target:
                return worker
        
        return workers[-1]
    
    def _select_resource_based(self, workers: List['Worker']) -> 'Worker':
        """Select worker based on resource utilization."""
        return min(workers, key=lambda w: w.get_stats().load_score)


class Worker:
    """Individual worker that can process tasks."""
    
    def __init__(
        self,
        worker_id: str,
        executor: Union[ThreadPoolExecutor, ProcessPoolExecutor],
        max_concurrent_tasks: int = 5
    ):
        self.worker_id = worker_id
        self.executor = executor
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # Task tracking
        self.active_tasks: Dict[str, Future] = {}
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.task_durations: List[float] = []
        
        # Status
        self.status = WorkerStatus.IDLE
        self.last_activity = datetime.now()
        
        # Resource monitoring
        self.cpu_usage = 0.0
        self.memory_usage_mb = 0
        
        # Threading
        self.lock = threading.RLock()
    
    def submit_task(self, task_func: Callable, *args, **kwargs) -> Optional[str]:
        """Submit a task to this worker."""
        
        with self.lock:
            if len(self.active_tasks) >= self.max_concurrent_tasks:
                return None
            
            task_id = f"{self.worker_id}_task_{time.time()}"
            
            try:
                future = self.executor.submit(task_func, *args, **kwargs)
                self.active_tasks[task_id] = future
                
                # Update status
                if len(self.active_tasks) == 1:
                    self.status = WorkerStatus.BUSY
                
                self.last_activity = datetime.now()
                
                # Set up completion callback
                future.add_done_callback(lambda f: self._task_completed(task_id, f))
                
                return task_id
                
            except Exception as e:
                logger.error(f"Error submitting task to worker {self.worker_id}: {e}")
                return None
    
    def _task_completed(self, task_id: str, future: Future) -> None:
        """Handle task completion."""
        
        with self.lock:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            # Update statistics
            if future.exception():
                self.failed_tasks += 1
                logger.error(f"Task {task_id} failed: {future.exception()}")
            else:
                self.completed_tasks += 1
            
            # Update status
            if len(self.active_tasks) == 0:
                self.status = WorkerStatus.IDLE
            
            self.last_activity = datetime.now()
    
    def is_overloaded(self) -> bool:
        """Check if worker is overloaded."""
        with self.lock:
            return (len(self.active_tasks) >= self.max_concurrent_tasks or
                    self.cpu_usage > 90 or
                    self.memory_usage_mb > 2048)
    
    def get_stats(self) -> WorkerStats:
        """Get current worker statistics."""
        
        with self.lock:
            avg_duration = 0.0
            if self.task_durations:
                avg_duration = sum(self.task_durations) / len(self.task_durations)
            
            return WorkerStats(
                worker_id=self.worker_id,
                status=self.status,
                active_tasks=len(self.active_tasks),
                completed_tasks=self.completed_tasks,
                failed_tasks=self.failed_tasks,
                average_task_duration=avg_duration,
                cpu_usage=self.cpu_usage,
                memory_usage_mb=self.memory_usage_mb,
                last_activity=self.last_activity
            )
    
    def shutdown(self) -> None:
        """Shutdown the worker."""
        
        with self.lock:
            self.status = WorkerStatus.SHUTDOWN
            
            # Cancel active tasks
            for future in self.active_tasks.values():
                future.cancel()
            
            self.active_tasks.clear()


class LoadBalancer:
    """
    Advanced load balancer with dynamic resource allocation and graceful degradation.
    """
    
    def __init__(
        self,
        instance_name: str,
        initial_workers: int = 4,
        max_workers: int = 16,
        min_workers: int = 1,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_CONNECTIONS
    ):
        self.instance_name = instance_name
        self.initial_workers = initial_workers
        self.max_workers = max_workers
        self.min_workers = min_workers
        self.strategy = strategy
        
        # Worker management
        self.worker_pools: Dict[str, WorkerPool] = {}
        self.thread_executor: Optional[ThreadPoolExecutor] = None
        self.process_executor: Optional[ProcessPoolExecutor] = None
        
        # Load monitoring
        self.system_load_history: List[float] = []
        self.load_check_interval = 30  # seconds
        self.last_load_check = datetime.now()
        
        # Auto-scaling configuration
        self.auto_scaling_enabled = True
        self.scale_up_threshold = 0.8  # Scale up when load > 80%
        self.scale_down_threshold = 0.3  # Scale down when load < 30%
        self.scale_up_cooldown = timedelta(minutes=5)
        self.scale_down_cooldown = timedelta(minutes=10)
        self.last_scale_action = datetime.now()
        
        # Graceful degradation
        self.degradation_enabled = True
        self.degradation_threshold = 0.95  # Start degradation at 95% load
        self.degraded_mode = False
        
        # Threading
        self.lock = threading.RLock()
        self.monitoring_active = False
        
        logger.info(f"LoadBalancer initialized for {instance_name}")
    
    async def start(self) -> None:
        """Start the load balancer."""
        
        with self.lock:
            if self.monitoring_active:
                return
            
            # Initialize executors
            self.thread_executor = ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix=f"{self.instance_name}_lb_thread"
            )
            
            # Create initial worker pool
            self._create_worker_pool("default", self.initial_workers)
            
            self.monitoring_active = True
        
        # Start monitoring
        asyncio.create_task(self._monitoring_loop())
        
        logger.info(f"LoadBalancer started for {self.instance_name}")
    
    async def stop(self) -> None:
        """Stop the load balancer."""
        
        with self.lock:
            self.monitoring_active = False
            
            # Shutdown all workers
            for pool in self.worker_pools.values():
                for worker in pool.workers.values():
                    worker.shutdown()
            
            # Shutdown executors
            if self.thread_executor:
                self.thread_executor.shutdown(wait=True)
                self.thread_executor = None
            
            if self.process_executor:
                self.process_executor.shutdown(wait=True)
                self.process_executor = None
        
        logger.info(f"LoadBalancer stopped for {self.instance_name}")
    
    def _create_worker_pool(self, pool_id: str, num_workers: int) -> WorkerPool:
        """Create a new worker pool."""
        
        pool = WorkerPool(
            pool_id=pool_id,
            strategy=self.strategy,
            max_workers=self.max_workers,
            min_workers=self.min_workers
        )
        
        # Create workers
        for i in range(num_workers):
            worker_id = f"{pool_id}_worker_{i}"
            worker = Worker(
                worker_id=worker_id,
                executor=self.thread_executor,
                max_concurrent_tasks=5
            )
            pool.add_worker(worker)
        
        self.worker_pools[pool_id] = pool
        
        logger.info(f"Created worker pool {pool_id} with {num_workers} workers")
        return pool
    
    async def submit_task(
        self,
        task_func: Callable,
        pool_id: str = "default",
        *args,
        **kwargs
    ) -> Optional[str]:
        """Submit a task to the load balancer."""
        
        with self.lock:
            if pool_id not in self.worker_pools:
                logger.error(f"Worker pool {pool_id} not found")
                return None
            
            pool = self.worker_pools[pool_id]
            worker = pool.select_worker()
            
            if not worker:
                # Try to scale up if possible
                if self.auto_scaling_enabled and self._can_scale_up(pool):
                    self._scale_up_pool(pool)
                    worker = pool.select_worker()
                
                if not worker:
                    logger.warning(f"No available workers in pool {pool_id}")
                    return None
            
            return worker.submit_task(task_func, *args, **kwargs)
    
    def _can_scale_up(self, pool: WorkerPool) -> bool:
        """Check if pool can be scaled up."""
        
        current_time = datetime.now()
        
        return (len(pool.workers) < pool.max_workers and
                current_time - self.last_scale_action > self.scale_up_cooldown and
                self._get_pool_load(pool) > self.scale_up_threshold)
    
    def _can_scale_down(self, pool: WorkerPool) -> bool:
        """Check if pool can be scaled down."""
        
        current_time = datetime.now()
        
        return (len(pool.workers) > pool.min_workers and
                current_time - self.last_scale_action > self.scale_down_cooldown and
                self._get_pool_load(pool) < self.scale_down_threshold)
    
    def _scale_up_pool(self, pool: WorkerPool) -> None:
        """Scale up a worker pool."""
        
        if len(pool.workers) >= pool.max_workers:
            return
        
        # Add one new worker
        worker_id = f"{pool.pool_id}_worker_{len(pool.workers)}"
        worker = Worker(
            worker_id=worker_id,
            executor=self.thread_executor,
            max_concurrent_tasks=5
        )
        pool.add_worker(worker)
        
        self.last_scale_action = datetime.now()
        
        logger.info(f"Scaled up pool {pool.pool_id} to {len(pool.workers)} workers")
    
    def _scale_down_pool(self, pool: WorkerPool) -> None:
        """Scale down a worker pool."""
        
        if len(pool.workers) <= pool.min_workers:
            return
        
        # Find least active worker to remove
        workers_by_activity = sorted(
            pool.workers.values(),
            key=lambda w: w.get_stats().active_tasks
        )
        
        worker_to_remove = workers_by_activity[0]
        if worker_to_remove.get_stats().active_tasks == 0:
            worker_to_remove.shutdown()
            pool.remove_worker(worker_to_remove.worker_id)
            
            self.last_scale_action = datetime.now()
            
            logger.info(f"Scaled down pool {pool.pool_id} to {len(pool.workers)} workers")
    
    def _get_pool_load(self, pool: WorkerPool) -> float:
        """Calculate current load for a pool."""
        
        if not pool.workers:
            return 0.0
        
        total_capacity = len(pool.workers) * 5  # Assuming 5 tasks per worker max
        active_tasks = sum(w.get_stats().active_tasks for w in pool.workers.values())
        
        return active_tasks / total_capacity if total_capacity > 0 else 0.0
    
    def _get_system_load(self) -> float:
        """Get overall system load."""
        
        total_load = 0.0
        total_pools = len(self.worker_pools)
        
        if total_pools == 0:
            return 0.0
        
        for pool in self.worker_pools.values():
            total_load += self._get_pool_load(pool)
        
        return total_load / total_pools
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop for auto-scaling and load management."""
        
        while self.monitoring_active:
            try:
                current_time = datetime.now()
                
                if current_time - self.last_load_check >= timedelta(seconds=self.load_check_interval):
                    await self._check_and_adjust_load()
                    self.last_load_check = current_time
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in load balancer monitoring loop: {e}")
                await asyncio.sleep(30)
    
    async def _check_and_adjust_load(self) -> None:
        """Check system load and adjust resources accordingly."""
        
        system_load = self._get_system_load()
        self.system_load_history.append(system_load)
        
        # Keep only recent history (last 100 measurements)
        if len(self.system_load_history) > 100:
            self.system_load_history = self.system_load_history[-100:]
        
        # Check for graceful degradation
        if self.degradation_enabled and system_load > self.degradation_threshold:
            if not self.degraded_mode:
                self._enter_degraded_mode()
        elif self.degraded_mode and system_load < self.degradation_threshold * 0.8:
            self._exit_degraded_mode()
        
        # Auto-scaling decisions
        if self.auto_scaling_enabled:
            for pool in self.worker_pools.values():
                pool_load = self._get_pool_load(pool)
                
                if self._can_scale_up(pool) and pool_load > self.scale_up_threshold:
                    self._scale_up_pool(pool)
                elif self._can_scale_down(pool) and pool_load < self.scale_down_threshold:
                    self._scale_down_pool(pool)
    
    def _enter_degraded_mode(self) -> None:
        """Enter graceful degradation mode."""
        
        self.degraded_mode = True
        
        # Reduce worker capacity
        for pool in self.worker_pools.values():
            for worker in pool.workers.values():
                worker.max_concurrent_tasks = max(1, worker.max_concurrent_tasks // 2)
        
        logger.warning(f"LoadBalancer for {self.instance_name} entered degraded mode")
    
    def _exit_degraded_mode(self) -> None:
        """Exit graceful degradation mode."""
        
        self.degraded_mode = False
        
        # Restore worker capacity
        for pool in self.worker_pools.values():
            for worker in pool.workers.values():
                worker.max_concurrent_tasks = 5  # Restore to default
        
        logger.info(f"LoadBalancer for {self.instance_name} exited degraded mode")
    
    def get_load_balancer_stats(self) -> Dict[str, Any]:
        """Get comprehensive load balancer statistics."""
        
        with self.lock:
            pool_stats = {}
            
            for pool_id, pool in self.worker_pools.items():
                worker_stats = [w.get_stats() for w in pool.workers.values()]
                
                pool_stats[pool_id] = {
                    'worker_count': len(pool.workers),
                    'strategy': pool.strategy.value,
                    'load': self._get_pool_load(pool),
                    'available_workers': len(pool.get_available_workers()),
                    'total_active_tasks': sum(w.active_tasks for w in worker_stats),
                    'total_completed_tasks': sum(w.completed_tasks for w in worker_stats),
                    'total_failed_tasks': sum(w.failed_tasks for w in worker_stats),
                    'average_success_rate': (
                        sum(w.success_rate for w in worker_stats) / len(worker_stats)
                        if worker_stats else 0.0
                    )
                }
            
            return {
                'instance_name': self.instance_name,
                'system_load': self._get_system_load(),
                'degraded_mode': self.degraded_mode,
                'auto_scaling_enabled': self.auto_scaling_enabled,
                'monitoring_active': self.monitoring_active,
                'pools': pool_stats,
                'load_history': self.system_load_history[-20:],  # Last 20 measurements
                'last_scale_action': self.last_scale_action.isoformat()
            }
    
    def set_load_balancing_strategy(self, pool_id: str, strategy: LoadBalancingStrategy) -> bool:
        """Set load balancing strategy for a specific pool."""
        
        with self.lock:
            if pool_id in self.worker_pools:
                self.worker_pools[pool_id].strategy = strategy
                logger.info(f"Set load balancing strategy for pool {pool_id} to {strategy.value}")
                return True
            return False
    
    def set_worker_weight(self, pool_id: str, worker_id: str, weight: float) -> bool:
        """Set weight for a specific worker (used in weighted round-robin)."""
        
        with self.lock:
            if pool_id in self.worker_pools:
                pool = self.worker_pools[pool_id]
                if worker_id in pool.workers:
                    pool.worker_weights[worker_id] = weight
                    return True
            return False