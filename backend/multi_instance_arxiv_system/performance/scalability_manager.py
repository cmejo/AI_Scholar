"""
Scalability Manager for Multi-Instance ArXiv System.

This module provides configurable worker processes, thread pools, load balancing,
and dynamic resource allocation based on system load with graceful degradation.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
import logging
import asyncio
import threading
import psutil
import time
from dataclasses import dataclass, field
from enum import Enum
import json

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.performance.load_balancer import LoadBalancer, LoadBalancingStrategy
    from multi_instance_arxiv_system.performance.concurrent_processor import ConcurrentProcessor, ProcessingTask, TaskPriority
    from multi_instance_arxiv_system.performance.memory_manager import MemoryManager
    from multi_instance_arxiv_system.performance.resource_monitor import ResourceMonitor
except ImportError as e:
    print(f"Import error: {e}")
    # Create minimal fallback classes for testing
    class LoadBalancer:
        def __init__(self, *args, **kwargs): pass
        async def start(self): pass
        async def stop(self): pass
        def get_load_balancer_stats(self): return {}
    
    class ConcurrentProcessor:
        def __init__(self, *args, **kwargs): pass
        async def start(self): pass
        async def stop(self): pass
        def get_processing_stats(self): return type('Stats', (), {'total_tasks': 0})()
    
    class MemoryManager:
        def __init__(self, *args, **kwargs): pass
        def check_memory_usage(self): return {'available_mb': 1000}
    
    class ResourceMonitor:
        def __init__(self, *args, **kwargs): pass
        def get_system_metrics(self): return {}

logger = logging.getLogger(__name__)


class ScalabilityMode(Enum):
    """Scalability operation modes."""
    NORMAL = "normal"
    HIGH_LOAD = "high_load"
    DEGRADED = "degraded"
    EMERGENCY = "emergency"


class ResourceAllocationStrategy(Enum):
    """Resource allocation strategies."""
    STATIC = "static"
    DYNAMIC = "dynamic"
    ADAPTIVE = "adaptive"
    PREDICTIVE = "predictive"


@dataclass
class ScalabilityConfig:
    """Configuration for scalability manager."""
    
    # Worker configuration
    min_workers: int = 2
    max_workers: int = 16
    initial_workers: int = 4
    worker_scale_factor: float = 1.5
    
    # Thread pool configuration
    min_threads_per_worker: int = 2
    max_threads_per_worker: int = 8
    thread_scale_factor: float = 1.2
    
    # Load thresholds
    scale_up_cpu_threshold: float = 0.75
    scale_up_memory_threshold: float = 0.80
    scale_down_cpu_threshold: float = 0.30
    scale_down_memory_threshold: float = 0.40
    
    # Degradation thresholds
    degradation_cpu_threshold: float = 0.90
    degradation_memory_threshold: float = 0.95
    emergency_cpu_threshold: float = 0.98
    emergency_memory_threshold: float = 0.99
    
    # Timing configuration
    scale_check_interval: int = 30  # seconds
    scale_up_cooldown: int = 120  # seconds
    scale_down_cooldown: int = 300  # seconds
    
    # Resource allocation
    allocation_strategy: ResourceAllocationStrategy = ResourceAllocationStrategy.DYNAMIC
    enable_predictive_scaling: bool = True
    enable_graceful_degradation: bool = True


@dataclass
class ScalabilityMetrics:
    """Metrics for scalability operations."""
    
    instance_name: str
    current_mode: ScalabilityMode
    
    # Worker metrics
    active_workers: int = 0
    total_thread_capacity: int = 0
    active_threads: int = 0
    
    # Resource utilization
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    disk_io_percent: float = 0.0
    network_io_mbps: float = 0.0
    
    # Performance metrics
    tasks_per_second: float = 0.0
    average_response_time: float = 0.0
    error_rate_percent: float = 0.0
    
    # Scaling history
    last_scale_action: Optional[datetime] = None
    scale_actions_count: int = 0
    degradation_events: int = 0
    
    # Predictions
    predicted_load_1h: float = 0.0
    predicted_memory_1h: float = 0.0
    recommended_workers: int = 0


class ScalabilityManager:
    """
    Advanced scalability manager with dynamic resource allocation and graceful degradation.
    
    Provides configurable worker processes, thread pools, load balancing, and automatic
    scaling based on system load with predictive capabilities.
    """
    
    def __init__(
        self,
        instance_name: str,
        config: Optional[ScalabilityConfig] = None
    ):
        self.instance_name = instance_name
        self.config = config or ScalabilityConfig()
        
        # Core components
        self.load_balancer: Optional[LoadBalancer] = None
        self.concurrent_processor: Optional[ConcurrentProcessor] = None
        self.memory_manager: Optional[MemoryManager] = None
        self.resource_monitor: Optional[ResourceMonitor] = None
        
        # State management
        self.current_mode = ScalabilityMode.NORMAL
        self.is_running = False
        self.shutdown_requested = False
        
        # Scaling state
        self.current_workers = self.config.initial_workers
        self.last_scale_action = datetime.now()
        self.scale_history: List[Dict[str, Any]] = []
        
        # Metrics and monitoring
        self.metrics = ScalabilityMetrics(instance_name, self.current_mode)
        self.load_history: List[float] = []
        self.memory_history: List[float] = []
        
        # Threading
        self.lock = threading.RLock()
        
        # Predictive scaling
        self.load_predictor = LoadPredictor() if self.config.enable_predictive_scaling else None
        
        logger.info(f"ScalabilityManager initialized for {instance_name}")
    
    async def start(self) -> None:
        """Start the scalability manager."""
        
        if self.is_running:
            logger.warning(f"ScalabilityManager for {self.instance_name} is already running")
            return
        
        logger.info(f"Starting ScalabilityManager for {self.instance_name}")
        
        # Initialize components
        await self._initialize_components()
        
        # Initialize metrics
        self.metrics.active_workers = self.current_workers
        self.metrics.total_thread_capacity = self.current_workers * self.config.max_threads_per_worker
        self.metrics.current_mode = self.current_mode
        
        self.is_running = True
        self.shutdown_requested = False
        
        # Start monitoring and scaling loops
        asyncio.create_task(self._scaling_monitor())
        asyncio.create_task(self._performance_monitor())
        asyncio.create_task(self._degradation_monitor())
        
        if self.load_predictor:
            asyncio.create_task(self._predictive_scaling_monitor())
        
        logger.info(f"ScalabilityManager started for {self.instance_name}")
    
    async def stop(self) -> None:
        """Stop the scalability manager gracefully."""
        
        logger.info(f"Stopping ScalabilityManager for {self.instance_name}")
        
        self.shutdown_requested = True
        
        # Stop components
        if self.concurrent_processor:
            await self.concurrent_processor.stop()
        
        if self.load_balancer:
            await self.load_balancer.stop()
        
        self.is_running = False
        
        logger.info(f"ScalabilityManager stopped for {self.instance_name}")
    
    async def _initialize_components(self) -> None:
        """Initialize core scalability components."""
        
        # Initialize load balancer
        self.load_balancer = LoadBalancer(
            instance_name=self.instance_name,
            initial_workers=self.config.initial_workers,
            max_workers=self.config.max_workers,
            min_workers=self.config.min_workers,
            strategy=LoadBalancingStrategy.RESOURCE_BASED
        )
        await self.load_balancer.start()
        
        # Initialize concurrent processor
        self.concurrent_processor = ConcurrentProcessor(
            instance_name=self.instance_name,
            max_workers=self.config.initial_workers,
            max_concurrent_tasks=self.config.initial_workers * self.config.max_threads_per_worker,
            memory_limit_mb=4096,
            enable_process_pool=True
        )
        await self.concurrent_processor.start()
        
        # Initialize memory manager
        self.memory_manager = MemoryManager(
            instance_name=self.instance_name,
            memory_limit_mb=8192
        )
        
        # Initialize resource monitor
        self.resource_monitor = ResourceMonitor(self.instance_name)
        
        logger.info(f"Core components initialized for {self.instance_name}")
    
    async def _scaling_monitor(self) -> None:
        """Monitor system load and make scaling decisions."""
        
        while not self.shutdown_requested:
            try:
                await self._check_scaling_needs()
                await asyncio.sleep(self.config.scale_check_interval)
                
            except Exception as e:
                logger.error(f"Error in scaling monitor for {self.instance_name}: {e}")
                await asyncio.sleep(60)
    
    async def _check_scaling_needs(self) -> None:
        """Check if scaling is needed and execute scaling actions."""
        
        # Get current system metrics
        system_metrics = self.resource_monitor.get_system_metrics()
        cpu_usage = system_metrics.get('cpu_percent', 0.0)
        memory_usage = system_metrics.get('memory_percent', 0.0)
        
        # Update history
        self.load_history.append(cpu_usage)
        self.memory_history.append(memory_usage)
        
        # Keep only recent history
        if len(self.load_history) > 100:
            self.load_history = self.load_history[-100:]
            self.memory_history = self.memory_history[-100:]
        
        # Check cooldown periods
        time_since_last_scale = (datetime.now() - self.last_scale_action).total_seconds()
        
        # Determine scaling action
        scaling_action = self._determine_scaling_action(cpu_usage, memory_usage, time_since_last_scale)
        
        if scaling_action:
            await self._execute_scaling_action(scaling_action, cpu_usage, memory_usage)
    
    def _determine_scaling_action(
        self, 
        cpu_usage: float, 
        memory_usage: float, 
        time_since_last_scale: float
    ) -> Optional[str]:
        """Determine what scaling action to take."""
        
        # Check for scale up conditions
        if (cpu_usage > self.config.scale_up_cpu_threshold or 
            memory_usage > self.config.scale_up_memory_threshold):
            
            if (time_since_last_scale > self.config.scale_up_cooldown and
                self.current_workers < self.config.max_workers):
                return "scale_up"
        
        # Check for scale down conditions
        elif (cpu_usage < self.config.scale_down_cpu_threshold and 
              memory_usage < self.config.scale_down_memory_threshold):
            
            if (time_since_last_scale > self.config.scale_down_cooldown and
                self.current_workers > self.config.min_workers):
                return "scale_down"
        
        return None
    
    async def _execute_scaling_action(
        self, 
        action: str, 
        cpu_usage: float, 
        memory_usage: float
    ) -> None:
        """Execute a scaling action."""
        
        with self.lock:
            if action == "scale_up":
                new_workers = min(
                    self.config.max_workers,
                    int(self.current_workers * self.config.worker_scale_factor)
                )
                
                if new_workers > self.current_workers:
                    await self._scale_workers(new_workers)
                    logger.info(f"Scaled up {self.instance_name} from {self.current_workers} to {new_workers} workers")
            
            elif action == "scale_down":
                new_workers = max(
                    self.config.min_workers,
                    int(self.current_workers / self.config.worker_scale_factor)
                )
                
                if new_workers < self.current_workers:
                    await self._scale_workers(new_workers)
                    logger.info(f"Scaled down {self.instance_name} from {self.current_workers} to {new_workers} workers")
            
            # Record scaling action
            self.last_scale_action = datetime.now()
            self.scale_history.append({
                'timestamp': self.last_scale_action.isoformat(),
                'action': action,
                'old_workers': self.current_workers,
                'new_workers': new_workers if 'new_workers' in locals() else self.current_workers,
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'trigger': 'automatic'
            })
            
            # Keep only recent history
            if len(self.scale_history) > 50:
                self.scale_history = self.scale_history[-50:]
    
    async def _scale_workers(self, target_workers: int) -> None:
        """Scale the number of workers to target count."""
        
        if target_workers == self.current_workers:
            return
        
        # Update concurrent processor
        if self.concurrent_processor:
            # Stop current processor
            await self.concurrent_processor.stop()
            
            # Create new processor with updated worker count
            self.concurrent_processor = ConcurrentProcessor(
                instance_name=self.instance_name,
                max_workers=target_workers,
                max_concurrent_tasks=target_workers * self.config.max_threads_per_worker,
                memory_limit_mb=4096,
                enable_process_pool=True
            )
            await self.concurrent_processor.start()
        
        # Update load balancer
        if self.load_balancer:
            # The load balancer will automatically adjust its worker pools
            pass
        
        self.current_workers = target_workers
        self.metrics.active_workers = target_workers
        self.metrics.total_thread_capacity = target_workers * self.config.max_threads_per_worker
    
    async def _performance_monitor(self) -> None:
        """Monitor performance metrics and update statistics."""
        
        while not self.shutdown_requested:
            try:
                await self._update_performance_metrics()
                await asyncio.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in performance monitor for {self.instance_name}: {e}")
                await asyncio.sleep(30)
    
    async def _update_performance_metrics(self) -> None:
        """Update performance metrics."""
        
        # Get system metrics
        system_metrics = self.resource_monitor.get_system_metrics()
        
        # Update metrics
        self.metrics.cpu_usage_percent = system_metrics.get('cpu_percent', 0.0)
        self.metrics.memory_usage_percent = system_metrics.get('memory_percent', 0.0)
        self.metrics.disk_io_percent = system_metrics.get('disk_io_percent', 0.0)
        self.metrics.network_io_mbps = system_metrics.get('network_io_mbps', 0.0)
        
        # Get processing stats
        if self.concurrent_processor:
            processing_stats = self.concurrent_processor.get_processing_stats()
            self.metrics.tasks_per_second = processing_stats.throughput_tasks_per_second
            self.metrics.error_rate_percent = processing_stats.error_rate
            self.metrics.average_response_time = processing_stats.average_execution_time
        
        # Update worker metrics
        self.metrics.active_workers = self.current_workers
        self.metrics.total_thread_capacity = self.current_workers * self.config.max_threads_per_worker
        
        if self.concurrent_processor:
            self.metrics.active_threads = self.concurrent_processor.get_active_task_count()
    
    async def _degradation_monitor(self) -> None:
        """Monitor for degradation conditions and manage graceful degradation."""
        
        while not self.shutdown_requested:
            try:
                await self._check_degradation_needs()
                await asyncio.sleep(5)  # Check every 5 seconds for degradation
                
            except Exception as e:
                logger.error(f"Error in degradation monitor for {self.instance_name}: {e}")
                await asyncio.sleep(30)
    
    async def _check_degradation_needs(self) -> None:
        """Check if degradation mode changes are needed."""
        
        cpu_usage = self.metrics.cpu_usage_percent / 100.0
        memory_usage = self.metrics.memory_usage_percent / 100.0
        
        # Determine target mode
        target_mode = self._determine_target_mode(cpu_usage, memory_usage)
        
        if target_mode != self.current_mode:
            await self._change_mode(target_mode, cpu_usage, memory_usage)
    
    def _determine_target_mode(self, cpu_usage: float, memory_usage: float) -> ScalabilityMode:
        """Determine target scalability mode based on resource usage."""
        
        # Emergency mode
        if (cpu_usage > self.config.emergency_cpu_threshold or 
            memory_usage > self.config.emergency_memory_threshold):
            return ScalabilityMode.EMERGENCY
        
        # Degraded mode
        elif (cpu_usage > self.config.degradation_cpu_threshold or 
              memory_usage > self.config.degradation_memory_threshold):
            return ScalabilityMode.DEGRADED
        
        # High load mode
        elif (cpu_usage > self.config.scale_up_cpu_threshold or 
              memory_usage > self.config.scale_up_memory_threshold):
            return ScalabilityMode.HIGH_LOAD
        
        # Normal mode
        else:
            return ScalabilityMode.NORMAL
    
    async def _change_mode(self, target_mode: ScalabilityMode, cpu_usage: float, memory_usage: float) -> None:
        """Change scalability mode and apply appropriate measures."""
        
        old_mode = self.current_mode
        self.current_mode = target_mode
        self.metrics.current_mode = target_mode
        
        logger.info(f"Changing {self.instance_name} mode from {old_mode.value} to {target_mode.value}")
        
        if target_mode == ScalabilityMode.EMERGENCY:
            await self._enter_emergency_mode()
        elif target_mode == ScalabilityMode.DEGRADED:
            await self._enter_degraded_mode()
        elif target_mode == ScalabilityMode.HIGH_LOAD:
            await self._enter_high_load_mode()
        else:  # NORMAL
            await self._enter_normal_mode()
        
        # Record mode change
        self.metrics.degradation_events += 1
        
        # Log mode change
        logger.warning(f"Mode changed for {self.instance_name}: {old_mode.value} -> {target_mode.value} "
                      f"(CPU: {cpu_usage:.1%}, Memory: {memory_usage:.1%})")
    
    async def _enter_emergency_mode(self) -> None:
        """Enter emergency mode with maximum resource conservation."""
        
        # Drastically reduce concurrent operations
        if self.concurrent_processor:
            # Reduce to minimum workers and threads
            await self._scale_workers(self.config.min_workers)
        
        # Enable aggressive memory cleanup
        if self.memory_manager:
            self.memory_manager.cleanup_if_needed()
        
        # Reduce load balancer capacity
        if self.load_balancer:
            self.load_balancer.degraded_mode = True
        
        logger.critical(f"Entered EMERGENCY mode for {self.instance_name}")
    
    async def _enter_degraded_mode(self) -> None:
        """Enter degraded mode with reduced capacity."""
        
        # Reduce concurrent operations
        if self.concurrent_processor:
            reduced_workers = max(self.config.min_workers, self.current_workers // 2)
            await self._scale_workers(reduced_workers)
        
        # Enable memory cleanup
        if self.memory_manager:
            self.memory_manager.cleanup_if_needed()
        
        logger.warning(f"Entered DEGRADED mode for {self.instance_name}")
    
    async def _enter_high_load_mode(self) -> None:
        """Enter high load mode with optimized performance."""
        
        # Optimize for high throughput
        if self.load_balancer:
            self.load_balancer.set_load_balancing_strategy("default", LoadBalancingStrategy.RESOURCE_BASED)
        
        logger.info(f"Entered HIGH_LOAD mode for {self.instance_name}")
    
    async def _enter_normal_mode(self) -> None:
        """Enter normal mode with standard operations."""
        
        # Restore normal operations
        if self.load_balancer:
            self.load_balancer.degraded_mode = False
        
        logger.info(f"Entered NORMAL mode for {self.instance_name}")
    
    async def _predictive_scaling_monitor(self) -> None:
        """Monitor and execute predictive scaling decisions."""
        
        if not self.load_predictor:
            return
        
        while not self.shutdown_requested:
            try:
                # Update predictor with current data
                self.load_predictor.update_data(
                    self.load_history[-20:] if len(self.load_history) >= 20 else self.load_history,
                    self.memory_history[-20:] if len(self.memory_history) >= 20 else self.memory_history
                )
                
                # Get predictions
                predictions = self.load_predictor.predict_load(horizon_minutes=60)
                
                if predictions:
                    self.metrics.predicted_load_1h = predictions.get('cpu_load', 0.0)
                    self.metrics.predicted_memory_1h = predictions.get('memory_load', 0.0)
                    self.metrics.recommended_workers = predictions.get('recommended_workers', self.current_workers)
                    
                    # Execute predictive scaling if needed
                    await self._execute_predictive_scaling(predictions)
                
                await asyncio.sleep(300)  # Predict every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in predictive scaling monitor for {self.instance_name}: {e}")
                await asyncio.sleep(300)
    
    async def _execute_predictive_scaling(self, predictions: Dict[str, Any]) -> None:
        """Execute predictive scaling based on predictions."""
        
        recommended_workers = predictions.get('recommended_workers', self.current_workers)
        confidence = predictions.get('confidence', 0.0)
        
        # Only act on high-confidence predictions
        if confidence > 0.8 and recommended_workers != self.current_workers:
            # Check if we're not in cooldown
            time_since_last_scale = (datetime.now() - self.last_scale_action).total_seconds()
            
            if time_since_last_scale > self.config.scale_up_cooldown:
                await self._scale_workers(recommended_workers)
                
                logger.info(f"Predictive scaling for {self.instance_name}: "
                           f"{self.current_workers} -> {recommended_workers} workers "
                           f"(confidence: {confidence:.2f})")
    
    def get_scalability_metrics(self) -> ScalabilityMetrics:
        """Get current scalability metrics."""
        
        self.metrics.last_scale_action = self.last_scale_action
        self.metrics.scale_actions_count = len(self.scale_history)
        
        return self.metrics
    
    def get_scaling_history(self) -> List[Dict[str, Any]]:
        """Get scaling action history."""
        return self.scale_history.copy()
    
    async def manual_scale(self, target_workers: int, reason: str = "manual") -> bool:
        """Manually scale to target worker count."""
        
        if target_workers < self.config.min_workers or target_workers > self.config.max_workers:
            logger.error(f"Target workers {target_workers} outside allowed range "
                        f"[{self.config.min_workers}, {self.config.max_workers}]")
            return False
        
        old_workers = self.current_workers
        await self._scale_workers(target_workers)
        
        # Record manual scaling action
        self.scale_history.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'manual_scale',
            'old_workers': old_workers,
            'new_workers': target_workers,
            'cpu_usage': self.metrics.cpu_usage_percent,
            'memory_usage': self.metrics.memory_usage_percent,
            'trigger': reason
        })
        
        logger.info(f"Manual scaling for {self.instance_name}: {old_workers} -> {target_workers} workers")
        return True
    
    def update_config(self, new_config: ScalabilityConfig) -> None:
        """Update scalability configuration."""
        
        self.config = new_config
        logger.info(f"Updated scalability configuration for {self.instance_name}")
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export comprehensive metrics for monitoring."""
        
        return {
            'instance_name': self.instance_name,
            'current_mode': self.current_mode.value,
            'metrics': {
                'active_workers': self.metrics.active_workers,
                'total_thread_capacity': self.metrics.total_thread_capacity,
                'active_threads': self.metrics.active_threads,
                'cpu_usage_percent': self.metrics.cpu_usage_percent,
                'memory_usage_percent': self.metrics.memory_usage_percent,
                'tasks_per_second': self.metrics.tasks_per_second,
                'error_rate_percent': self.metrics.error_rate_percent,
                'predicted_load_1h': self.metrics.predicted_load_1h,
                'recommended_workers': self.metrics.recommended_workers
            },
            'scaling_history': self.scale_history[-10:],  # Last 10 actions
            'load_history': self.load_history[-20:],  # Last 20 measurements
            'config': {
                'min_workers': self.config.min_workers,
                'max_workers': self.config.max_workers,
                'current_workers': self.current_workers,
                'allocation_strategy': self.config.allocation_strategy.value,
                'enable_predictive_scaling': self.config.enable_predictive_scaling,
                'enable_graceful_degradation': self.config.enable_graceful_degradation
            }
        }


class LoadPredictor:
    """Simple load predictor for predictive scaling."""
    
    def __init__(self):
        self.cpu_history: List[float] = []
        self.memory_history: List[float] = []
        self.timestamps: List[datetime] = []
    
    def update_data(self, cpu_data: List[float], memory_data: List[float]) -> None:
        """Update predictor with new data."""
        
        current_time = datetime.now()
        
        # Add new data points
        for cpu, memory in zip(cpu_data, memory_data):
            self.cpu_history.append(cpu)
            self.memory_history.append(memory)
            self.timestamps.append(current_time)
        
        # Keep only recent data (last 2 hours)
        cutoff_time = current_time - timedelta(hours=2)
        
        # Filter old data
        filtered_data = [
            (cpu, memory, ts) for cpu, memory, ts in 
            zip(self.cpu_history, self.memory_history, self.timestamps)
            if ts > cutoff_time
        ]
        
        if filtered_data:
            self.cpu_history, self.memory_history, self.timestamps = zip(*filtered_data)
            self.cpu_history = list(self.cpu_history)
            self.memory_history = list(self.memory_history)
            self.timestamps = list(self.timestamps)
    
    def predict_load(self, horizon_minutes: int = 60) -> Optional[Dict[str, Any]]:
        """Predict load for the next horizon_minutes."""
        
        if len(self.cpu_history) < 10:
            return None
        
        # Simple trend-based prediction
        recent_cpu = self.cpu_history[-10:]
        recent_memory = self.memory_history[-10:]
        
        # Calculate trends
        cpu_trend = (recent_cpu[-1] - recent_cpu[0]) / len(recent_cpu)
        memory_trend = (recent_memory[-1] - recent_memory[0]) / len(recent_memory)
        
        # Project forward
        current_cpu = recent_cpu[-1]
        current_memory = recent_memory[-1]
        
        predicted_cpu = max(0, min(100, current_cpu + (cpu_trend * horizon_minutes / 10)))
        predicted_memory = max(0, min(100, current_memory + (memory_trend * horizon_minutes / 10)))
        
        # Recommend workers based on predicted load
        if predicted_cpu > 75 or predicted_memory > 80:
            recommended_workers = min(16, int(predicted_cpu / 20) + 2)
        elif predicted_cpu < 30 and predicted_memory < 40:
            recommended_workers = max(2, int(predicted_cpu / 30) + 1)
        else:
            recommended_workers = 4  # Default
        
        # Calculate confidence based on trend stability
        cpu_variance = sum((x - sum(recent_cpu) / len(recent_cpu)) ** 2 for x in recent_cpu) / len(recent_cpu)
        confidence = max(0.5, min(1.0, 1.0 - (cpu_variance / 100)))
        
        return {
            'cpu_load': predicted_cpu,
            'memory_load': predicted_memory,
            'recommended_workers': recommended_workers,
            'confidence': confidence,
            'horizon_minutes': horizon_minutes
        }