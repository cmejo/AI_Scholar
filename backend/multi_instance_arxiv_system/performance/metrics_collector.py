"""
Performance Metrics Collection System for Multi-Instance ArXiv System.

This module provides comprehensive performance tracking, bottleneck detection,
and optimization recommendations for processing operations.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
import logging
import threading
import time
import statistics
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class BottleneckType(Enum):
    """Types of performance bottlenecks."""
    CPU = "cpu"
    MEMORY = "memory"
    IO = "io"
    NETWORK = "network"
    CONCURRENCY = "concurrency"


@dataclass
class PerformanceMetric:
    """Individual performance metric."""
    
    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    instance_name: str
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['metric_type'] = self.metric_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class BottleneckDetection:
    """Performance bottleneck detection result."""
    
    bottleneck_type: BottleneckType
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    affected_operations: List[str]
    recommendations: List[str]
    confidence_score: float  # 0.0 to 1.0
    detected_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['bottleneck_type'] = self.bottleneck_type.value
        data['detected_at'] = self.detected_at.isoformat()
        return data


class MetricsCollector:
    """
    Comprehensive performance metrics collector with bottleneck detection
    and optimization recommendations.
    """
    
    def __init__(self, instance_name: str, max_history_size: int = 10000):
        self.instance_name = instance_name
        self.max_history_size = max_history_size
        
        # Metrics storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))
        self.metric_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self.operation_timers: Dict[str, float] = {}
        self.operation_counts: Dict[str, int] = defaultdict(int)
        self.operation_durations: Dict[str, List[float]] = defaultdict(list)
        
        # Bottleneck detection
        self.bottlenecks: List[BottleneckDetection] = []
        self.detection_thresholds = {
            'cpu_usage_high': 80.0,
            'memory_usage_high': 85.0,
            'io_wait_high': 20.0,
            'response_time_slow': 5.0,
            'error_rate_high': 5.0,
            'queue_size_large': 100
        }
        
        # Threading
        self.lock = threading.RLock()
        self.collection_active = False
        
        logger.info(f"MetricsCollector initialized for {instance_name}")
    
    def start_collection(self) -> None:
        """Start metrics collection."""
        
        if self.collection_active:
            return
        
        self.collection_active = True
        
        # Start collection thread
        collection_thread = threading.Thread(
            target=self._collection_loop,
            name=f"MetricsCollector-{self.instance_name}",
            daemon=True
        )
        collection_thread.start()
        
        logger.info(f"Metrics collection started for {self.instance_name}")
    
    def stop_collection(self) -> None:
        """Stop metrics collection."""
        self.collection_active = False
        logger.info(f"Metrics collection stopped for {self.instance_name}")
    
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a performance metric."""
        
        metric = PerformanceMetric(
            name=name,
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(),
            instance_name=self.instance_name,
            tags=tags or {}
        )
        
        with self.lock:
            self.metrics[name].append(metric)
            
            # Store metadata
            if name not in self.metric_metadata:
                self.metric_metadata[name] = {
                    'metric_type': metric_type,
                    'first_recorded': datetime.now(),
                    'total_recordings': 0
                }
            
            self.metric_metadata[name]['total_recordings'] += 1
            self.metric_metadata[name]['last_recorded'] = datetime.now()
    
    def increment_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        
        with self.lock:
            # Get current value
            current_value = 0.0
            if name in self.metrics and self.metrics[name]:
                current_value = self.metrics[name][-1].value
            
            # Record incremented value
            self.record_metric(name, current_value + value, MetricType.COUNTER, tags)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram metric (for distributions)."""
        self.record_metric(name, value, MetricType.HISTOGRAM, tags)
    
    def start_timer(self, operation_name: str) -> str:
        """Start timing an operation."""
        
        timer_id = f"{operation_name}_{time.time()}"
        
        with self.lock:
            self.operation_timers[timer_id] = time.time()
        
        return timer_id
    
    def end_timer(self, timer_id: str, tags: Optional[Dict[str, str]] = None) -> float:
        """End timing an operation and record the duration."""
        
        with self.lock:
            if timer_id not in self.operation_timers:
                logger.warning(f"Timer {timer_id} not found")
                return 0.0
            
            start_time = self.operation_timers.pop(timer_id)
            duration = time.time() - start_time
            
            # Extract operation name from timer_id
            operation_name = timer_id.rsplit('_', 1)[0]
            
            # Record duration
            self.record_metric(f"{operation_name}_duration", duration, MetricType.TIMER, tags)
            
            # Update operation tracking
            self.operation_counts[operation_name] += 1
            self.operation_durations[operation_name].append(duration)
            
            # Keep only recent durations (last 1000)
            if len(self.operation_durations[operation_name]) > 1000:
                self.operation_durations[operation_name] = self.operation_durations[operation_name][-1000:]
            
            return duration
    
    def record_operation_result(
        self,
        operation_name: str,
        success: bool,
        duration: Optional[float] = None,
        error_type: Optional[str] = None
    ) -> None:
        """Record the result of an operation."""
        
        tags = {'operation': operation_name, 'success': str(success)}
        if error_type:
            tags['error_type'] = error_type
        
        # Record success/failure
        self.increment_counter(f"{operation_name}_total", tags=tags)
        
        if success:
            self.increment_counter(f"{operation_name}_success", tags=tags)
        else:
            self.increment_counter(f"{operation_name}_errors", tags=tags)
        
        # Record duration if provided
        if duration is not None:
            self.record_metric(f"{operation_name}_duration", duration, MetricType.TIMER, tags)
    
    def get_metric_values(
        self,
        name: str,
        hours: int = 1,
        aggregation: str = 'raw'
    ) -> List[float]:
        """Get metric values for specified time period."""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            if name not in self.metrics:
                return []
            
            # Filter by time
            recent_metrics = [
                metric for metric in self.metrics[name]
                if metric.timestamp >= cutoff_time
            ]
            
            values = [metric.value for metric in recent_metrics]
            
            if aggregation == 'raw':
                return values
            elif aggregation == 'average' and values:
                return [statistics.mean(values)]
            elif aggregation == 'max' and values:
                return [max(values)]
            elif aggregation == 'min' and values:
                return [min(values)]
            elif aggregation == 'sum' and values:
                return [sum(values)]
            else:
                return values
    
    def get_operation_stats(self, operation_name: str) -> Dict[str, Any]:
        """Get comprehensive statistics for an operation."""
        
        with self.lock:
            durations = self.operation_durations.get(operation_name, [])
            count = self.operation_counts.get(operation_name, 0)
            
            if not durations:
                return {
                    'operation_name': operation_name,
                    'total_count': count,
                    'average_duration': 0.0,
                    'min_duration': 0.0,
                    'max_duration': 0.0,
                    'p50_duration': 0.0,
                    'p95_duration': 0.0,
                    'p99_duration': 0.0
                }
            
            # Calculate percentiles
            sorted_durations = sorted(durations)
            
            def percentile(data, p):
                k = (len(data) - 1) * p / 100
                f = int(k)
                c = k - f
                if f == len(data) - 1:
                    return data[f]
                return data[f] * (1 - c) + data[f + 1] * c
            
            return {
                'operation_name': operation_name,
                'total_count': count,
                'average_duration': statistics.mean(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'p50_duration': percentile(sorted_durations, 50),
                'p95_duration': percentile(sorted_durations, 95),
                'p99_duration': percentile(sorted_durations, 99),
                'recent_samples': len(durations)
            }
    
    def detect_bottlenecks(self) -> List[BottleneckDetection]:
        """Detect performance bottlenecks based on collected metrics."""
        
        bottlenecks = []
        
        try:
            # CPU bottleneck detection
            cpu_bottleneck = self._detect_cpu_bottleneck()
            if cpu_bottleneck:
                bottlenecks.append(cpu_bottleneck)
            
            # Memory bottleneck detection
            memory_bottleneck = self._detect_memory_bottleneck()
            if memory_bottleneck:
                bottlenecks.append(memory_bottleneck)
            
            # I/O bottleneck detection
            io_bottleneck = self._detect_io_bottleneck()
            if io_bottleneck:
                bottlenecks.append(io_bottleneck)
            
            # Response time bottleneck detection
            response_bottleneck = self._detect_response_time_bottleneck()
            if response_bottleneck:
                bottlenecks.append(response_bottleneck)
            
            # Concurrency bottleneck detection
            concurrency_bottleneck = self._detect_concurrency_bottleneck()
            if concurrency_bottleneck:
                bottlenecks.append(concurrency_bottleneck)
            
        except Exception as e:
            logger.error(f"Error detecting bottlenecks for {self.instance_name}: {e}")
        
        # Store detected bottlenecks
        with self.lock:
            self.bottlenecks.extend(bottlenecks)
            # Keep only recent bottlenecks (last 100)
            if len(self.bottlenecks) > 100:
                self.bottlenecks = self.bottlenecks[-100:]
        
        return bottlenecks
    
    def _detect_cpu_bottleneck(self) -> Optional[BottleneckDetection]:
        """Detect CPU-related bottlenecks."""
        
        cpu_values = self.get_metric_values('cpu_usage_percent', hours=1)
        if not cpu_values:
            return None
        
        avg_cpu = statistics.mean(cpu_values)
        max_cpu = max(cpu_values)
        
        if avg_cpu > self.detection_thresholds['cpu_usage_high']:
            severity = 'critical' if avg_cpu > 95 else 'high' if avg_cpu > 90 else 'medium'
            
            return BottleneckDetection(
                bottleneck_type=BottleneckType.CPU,
                severity=severity,
                description=f"High CPU usage detected: {avg_cpu:.1f}% average, {max_cpu:.1f}% peak",
                affected_operations=self._get_slow_operations(),
                recommendations=[
                    "Consider reducing concurrent processing",
                    "Optimize CPU-intensive operations",
                    "Add more worker processes if possible",
                    "Profile code for CPU hotspots"
                ],
                confidence_score=min(1.0, (avg_cpu - 50) / 50)
            )
        
        return None
    
    def _detect_memory_bottleneck(self) -> Optional[BottleneckDetection]:
        """Detect memory-related bottlenecks."""
        
        memory_values = self.get_metric_values('memory_usage_percent', hours=1)
        if not memory_values:
            return None
        
        avg_memory = statistics.mean(memory_values)
        max_memory = max(memory_values)
        
        if avg_memory > self.detection_thresholds['memory_usage_high']:
            severity = 'critical' if avg_memory > 95 else 'high' if avg_memory > 90 else 'medium'
            
            return BottleneckDetection(
                bottleneck_type=BottleneckType.MEMORY,
                severity=severity,
                description=f"High memory usage detected: {avg_memory:.1f}% average, {max_memory:.1f}% peak",
                affected_operations=self._get_memory_intensive_operations(),
                recommendations=[
                    "Implement memory cleanup procedures",
                    "Reduce batch sizes for processing",
                    "Clear caches more frequently",
                    "Consider memory-efficient algorithms"
                ],
                confidence_score=min(1.0, (avg_memory - 60) / 40)
            )
        
        return None
    
    def _detect_io_bottleneck(self) -> Optional[BottleneckDetection]:
        """Detect I/O-related bottlenecks."""
        
        io_wait_values = self.get_metric_values('io_wait_percent', hours=1)
        if not io_wait_values:
            return None
        
        avg_io_wait = statistics.mean(io_wait_values)
        
        if avg_io_wait > self.detection_thresholds['io_wait_high']:
            severity = 'high' if avg_io_wait > 30 else 'medium'
            
            return BottleneckDetection(
                bottleneck_type=BottleneckType.IO,
                severity=severity,
                description=f"High I/O wait time detected: {avg_io_wait:.1f}% average",
                affected_operations=self._get_io_intensive_operations(),
                recommendations=[
                    "Optimize file I/O operations",
                    "Use asynchronous I/O where possible",
                    "Consider SSD storage for better performance",
                    "Implement I/O batching"
                ],
                confidence_score=min(1.0, avg_io_wait / 50)
            )
        
        return None
    
    def _detect_response_time_bottleneck(self) -> Optional[BottleneckDetection]:
        """Detect response time bottlenecks."""
        
        slow_operations = []
        
        for operation_name in self.operation_durations:
            stats = self.get_operation_stats(operation_name)
            
            if (stats['average_duration'] > self.detection_thresholds['response_time_slow'] or
                stats['p95_duration'] > self.detection_thresholds['response_time_slow'] * 2):
                slow_operations.append(operation_name)
        
        if slow_operations:
            avg_response_time = statistics.mean([
                self.get_operation_stats(op)['average_duration']
                for op in slow_operations
            ])
            
            severity = 'high' if avg_response_time > 10 else 'medium'
            
            return BottleneckDetection(
                bottleneck_type=BottleneckType.NETWORK,  # Using NETWORK for response time
                severity=severity,
                description=f"Slow response times detected in {len(slow_operations)} operations",
                affected_operations=slow_operations,
                recommendations=[
                    "Profile slow operations for optimization",
                    "Add caching for frequently accessed data",
                    "Optimize database queries",
                    "Consider parallel processing"
                ],
                confidence_score=min(1.0, len(slow_operations) / 10)
            )
        
        return None
    
    def _detect_concurrency_bottleneck(self) -> Optional[BottleneckDetection]:
        """Detect concurrency-related bottlenecks."""
        
        queue_size_values = self.get_metric_values('queue_size', hours=1)
        if not queue_size_values:
            return None
        
        avg_queue_size = statistics.mean(queue_size_values)
        max_queue_size = max(queue_size_values)
        
        if avg_queue_size > self.detection_thresholds['queue_size_large']:
            severity = 'high' if avg_queue_size > 200 else 'medium'
            
            return BottleneckDetection(
                bottleneck_type=BottleneckType.CONCURRENCY,
                severity=severity,
                description=f"Large queue sizes detected: {avg_queue_size:.0f} average, {max_queue_size:.0f} peak",
                affected_operations=['queue_processing'],
                recommendations=[
                    "Increase number of worker threads",
                    "Optimize task processing speed",
                    "Implement priority queues",
                    "Add load balancing"
                ],
                confidence_score=min(1.0, avg_queue_size / 500)
            )
        
        return None
    
    def _get_slow_operations(self) -> List[str]:
        """Get list of operations with slow response times."""
        
        slow_ops = []
        
        for operation_name in self.operation_durations:
            stats = self.get_operation_stats(operation_name)
            if stats['average_duration'] > 2.0:  # Slower than 2 seconds
                slow_ops.append(operation_name)
        
        return slow_ops
    
    def _get_memory_intensive_operations(self) -> List[str]:
        """Get list of memory-intensive operations."""
        
        # This would require more sophisticated tracking
        # For now, return operations that are typically memory-intensive
        memory_intensive = []
        
        for operation_name in self.operation_durations:
            if any(keyword in operation_name.lower() for keyword in ['embed', 'process', 'batch']):
                memory_intensive.append(operation_name)
        
        return memory_intensive
    
    def _get_io_intensive_operations(self) -> List[str]:
        """Get list of I/O-intensive operations."""
        
        io_intensive = []
        
        for operation_name in self.operation_durations:
            if any(keyword in operation_name.lower() for keyword in ['download', 'save', 'load', 'read', 'write']):
                io_intensive.append(operation_name)
        
        return io_intensive
    
    def _collection_loop(self) -> None:
        """Main metrics collection loop (runs in separate thread)."""
        
        while self.collection_active:
            try:
                # Collect system metrics
                self._collect_system_metrics()
                
                # Detect bottlenecks periodically
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    self.detect_bottlenecks()
                
                time.sleep(10)  # Collect every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in metrics collection loop for {self.instance_name}: {e}")
                time.sleep(30)
    
    def _collect_system_metrics(self) -> None:
        """Collect system-level performance metrics."""
        
        try:
            # CPU usage
            cpu_percent = self._get_cpu_usage()
            if cpu_percent is not None:
                self.record_metric('cpu_usage_percent', cpu_percent)
            
            # Memory usage
            memory_info = self._get_memory_usage()
            if memory_info:
                self.record_metric('memory_usage_percent', memory_info['usage_percent'])
                self.record_metric('memory_available_mb', memory_info['available_mb'])
            
            # I/O metrics
            io_stats = self._get_io_stats()
            if io_stats:
                self.record_metric('io_wait_percent', io_stats.get('io_wait_percent', 0))
                self.record_metric('disk_read_mb_per_sec', io_stats.get('read_mb_per_sec', 0))
                self.record_metric('disk_write_mb_per_sec', io_stats.get('write_mb_per_sec', 0))
            
        except Exception as e:
            logger.error(f"Error collecting system metrics for {self.instance_name}: {e}")
    
    def _get_cpu_usage(self) -> Optional[float]:
        """Get current CPU usage percentage."""
        
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            return None
        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
            return None
    
    def _get_memory_usage(self) -> Optional[Dict[str, float]]:
        """Get current memory usage information."""
        
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            return {
                'usage_percent': memory.percent,
                'available_mb': memory.available / 1024 / 1024,
                'used_mb': memory.used / 1024 / 1024
            }
        except ImportError:
            return None
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return None
    
    def _get_io_stats(self) -> Optional[Dict[str, float]]:
        """Get current I/O statistics."""
        
        try:
            import psutil
            
            # Get disk I/O stats
            disk_io = psutil.disk_io_counters()
            if disk_io:
                # Calculate rates (simplified)
                return {
                    'read_mb_per_sec': disk_io.read_bytes / 1024 / 1024 / 10,  # Rough estimate
                    'write_mb_per_sec': disk_io.write_bytes / 1024 / 1024 / 10,
                    'io_wait_percent': 0  # Would need more sophisticated calculation
                }
            
            return None
        except ImportError:
            return None
        except Exception as e:
            logger.error(f"Error getting I/O stats: {e}")
            return None
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        
        with self.lock:
            # Get recent bottlenecks
            recent_bottlenecks = [
                b for b in self.bottlenecks
                if b.detected_at > datetime.now() - timedelta(hours=1)
            ]
            
            # Get operation statistics
            operation_stats = {}
            for operation_name in self.operation_durations:
                operation_stats[operation_name] = self.get_operation_stats(operation_name)
            
            # Get metric summaries
            metric_summaries = {}
            for metric_name in self.metrics:
                recent_values = self.get_metric_values(metric_name, hours=1)
                if recent_values:
                    metric_summaries[metric_name] = {
                        'current': recent_values[-1] if recent_values else 0,
                        'average': statistics.mean(recent_values),
                        'min': min(recent_values),
                        'max': max(recent_values),
                        'count': len(recent_values)
                    }
            
            return {
                'instance_name': self.instance_name,
                'summary_timestamp': datetime.now().isoformat(),
                'bottlenecks': {
                    'total_detected': len(self.bottlenecks),
                    'recent_count': len(recent_bottlenecks),
                    'by_type': self._group_bottlenecks_by_type(recent_bottlenecks),
                    'recent_bottlenecks': [b.to_dict() for b in recent_bottlenecks[-5:]]
                },
                'operations': operation_stats,
                'metrics': metric_summaries,
                'collection_active': self.collection_active,
                'total_metrics_recorded': sum(
                    self.metric_metadata[name]['total_recordings']
                    for name in self.metric_metadata
                )
            }
    
    def _group_bottlenecks_by_type(self, bottlenecks: List[BottleneckDetection]) -> Dict[str, int]:
        """Group bottlenecks by type and count them."""
        
        type_counts = defaultdict(int)
        for bottleneck in bottlenecks:
            type_counts[bottleneck.bottleneck_type.value] += 1
        
        return dict(type_counts)
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get optimization recommendations based on detected bottlenecks."""
        
        recommendations = set()
        
        with self.lock:
            # Get recent bottlenecks
            recent_bottlenecks = [
                b for b in self.bottlenecks
                if b.detected_at > datetime.now() - timedelta(hours=24)
            ]
            
            # Collect all recommendations
            for bottleneck in recent_bottlenecks:
                recommendations.update(bottleneck.recommendations)
            
            # Add general recommendations based on patterns
            if any(b.bottleneck_type == BottleneckType.CPU for b in recent_bottlenecks):
                recommendations.add("Consider implementing CPU-efficient algorithms")
            
            if any(b.bottleneck_type == BottleneckType.MEMORY for b in recent_bottlenecks):
                recommendations.add("Implement memory pooling and object reuse")
            
            if any(b.bottleneck_type == BottleneckType.IO for b in recent_bottlenecks):
                recommendations.add("Use asynchronous I/O operations where possible")
        
        return list(recommendations)
    
    def clear_metrics(self, older_than_hours: int = 24) -> int:
        """Clear old metrics to free memory."""
        
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        cleared_count = 0
        
        with self.lock:
            for metric_name in list(self.metrics.keys()):
                original_count = len(self.metrics[metric_name])
                
                # Filter out old metrics
                self.metrics[metric_name] = deque(
                    [m for m in self.metrics[metric_name] if m.timestamp >= cutoff_time],
                    maxlen=self.max_history_size
                )
                
                cleared_count += original_count - len(self.metrics[metric_name])
        
        logger.info(f"Cleared {cleared_count} old metrics for {self.instance_name}")
        return cleared_count