"""
System monitoring and alerting service for performance and health tracking.
"""
import asyncio
import logging
import time
import psutil
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import statistics

from core.redis_client import RedisClient, get_redis_client
from core.database_optimization import db_optimizer
from services.caching_service import get_caching_service

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    """Types of metrics to monitor."""
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    DISK_USAGE = "disk_usage"
    CACHE_HIT_RATE = "cache_hit_rate"
    DATABASE_CONNECTIONS = "database_connections"
    ACTIVE_USERS = "active_users"

@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    unit: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class Alert:
    """Alert data structure."""
    id: str
    level: AlertLevel
    message: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **asdict(self),
            'level': self.level.value,
            'timestamp': self.timestamp.isoformat()
        }

class PerformanceMonitor:
    """Performance monitoring and metrics collection."""
    
    def __init__(self, redis_client: Optional[RedisClient] = None):
        self.redis_client = redis_client or get_redis_client()
        self.metrics_buffer = []
        self.alerts = []
        self.thresholds = {
            MetricType.RESPONSE_TIME: 5.0,  # 5 seconds
            MetricType.ERROR_RATE: 0.05,    # 5%
            MetricType.MEMORY_USAGE: 0.85,  # 85%
            MetricType.CPU_USAGE: 0.80,     # 80%
            MetricType.DISK_USAGE: 0.90,    # 90%
            MetricType.CACHE_HIT_RATE: 0.70, # 70% minimum
        }
        self.monitoring_active = False
        self.monitoring_task = None
    
    async def start_monitoring(self, interval_seconds: int = 60):
        """Start continuous monitoring."""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop(interval_seconds))
        logger.info(f"Started performance monitoring with {interval_seconds}s interval")
    
    async def stop_monitoring(self):
        """Stop continuous monitoring."""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped performance monitoring")
    
    async def _monitoring_loop(self, interval_seconds: int):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                await self.collect_system_metrics()
                await self.collect_application_metrics()
                await self.check_thresholds()
                await self.store_metrics()
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)
    
    async def collect_system_metrics(self):
        """Collect system-level metrics."""
        timestamp = datetime.now()
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics_buffer.append(PerformanceMetric(
            name=MetricType.CPU_USAGE.value,
            value=cpu_percent / 100.0,
            timestamp=timestamp,
            tags={'type': 'system'},
            unit='percentage'
        ))
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.metrics_buffer.append(PerformanceMetric(
            name=MetricType.MEMORY_USAGE.value,
            value=memory.percent / 100.0,
            timestamp=timestamp,
            tags={'type': 'system'},
            unit='percentage'
        ))
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        self.metrics_buffer.append(PerformanceMetric(
            name=MetricType.DISK_USAGE.value,
            value=disk_percent / 100.0,
            timestamp=timestamp,
            tags={'type': 'system'},
            unit='percentage'
        ))
        
        # Network I/O (if available)
        try:
            network = psutil.net_io_counters()
            self.metrics_buffer.extend([
                PerformanceMetric(
                    name='network_bytes_sent',
                    value=network.bytes_sent,
                    timestamp=timestamp,
                    tags={'type': 'system'},
                    unit='bytes'
                ),
                PerformanceMetric(
                    name='network_bytes_recv',
                    value=network.bytes_recv,
                    timestamp=timestamp,
                    tags={'type': 'system'},
                    unit='bytes'
                )
            ])
        except Exception as e:
            logger.debug(f"Network metrics not available: {e}")
    
    async def collect_application_metrics(self):
        """Collect application-specific metrics."""
        timestamp = datetime.now()
        
        # Database statistics
        try:
            db_stats = await db_optimizer.get_database_statistics()
            for stat_name, value in db_stats.items():
                if isinstance(value, (int, float)) and stat_name != 'database_size':
                    self.metrics_buffer.append(PerformanceMetric(
                        name=f'database_{stat_name}',
                        value=float(value),
                        timestamp=timestamp,
                        tags={'type': 'database'},
                        unit='count'
                    ))
        except Exception as e:
            logger.warning(f"Failed to collect database metrics: {e}")
        
        # Cache statistics
        try:
            caching_service = get_caching_service()
            cache_stats = caching_service.get_cache_stats()
            
            # Cache hit rate
            hit_rate = cache_stats.get('overall_cache_hit_rate', 0)
            self.metrics_buffer.append(PerformanceMetric(
                name=MetricType.CACHE_HIT_RATE.value,
                value=hit_rate,
                timestamp=timestamp,
                tags={'type': 'cache'},
                unit='percentage'
            ))
            
            # Memory cache size
            memory_cache_size = cache_stats.get('memory_cache', {}).get('size', 0)
            self.metrics_buffer.append(PerformanceMetric(
                name='cache_memory_size',
                value=float(memory_cache_size),
                timestamp=timestamp,
                tags={'type': 'cache'},
                unit='count'
            ))
            
        except Exception as e:
            logger.warning(f"Failed to collect cache metrics: {e}")
        
        # Redis metrics
        try:
            redis_info = await self._get_redis_info()
            if redis_info:
                self.metrics_buffer.append(PerformanceMetric(
                    name='redis_connected_clients',
                    value=float(redis_info.get('connected_clients', 0)),
                    timestamp=timestamp,
                    tags={'type': 'redis'},
                    unit='count'
                ))
                
                self.metrics_buffer.append(PerformanceMetric(
                    name='redis_used_memory',
                    value=float(redis_info.get('used_memory', 0)),
                    timestamp=timestamp,
                    tags={'type': 'redis'},
                    unit='bytes'
                ))
        except Exception as e:
            logger.warning(f"Failed to collect Redis metrics: {e}")
    
    async def _get_redis_info(self) -> Optional[Dict[str, Any]]:
        """Get Redis server information."""
        try:
            if self.redis_client.redis_client:
                info = await self.redis_client.redis_client.info()
                return info
        except Exception as e:
            logger.debug(f"Redis info not available: {e}")
        return None
    
    async def check_thresholds(self):
        """Check metrics against thresholds and generate alerts."""
        current_time = datetime.now()
        
        # Group recent metrics by name
        recent_metrics = {}
        cutoff_time = current_time - timedelta(minutes=5)
        
        for metric in self.metrics_buffer:
            if metric.timestamp > cutoff_time:
                if metric.name not in recent_metrics:
                    recent_metrics[metric.name] = []
                recent_metrics[metric.name].append(metric.value)
        
        # Check thresholds
        for metric_name, values in recent_metrics.items():
            if not values:
                continue
            
            avg_value = statistics.mean(values)
            max_value = max(values)
            
            # Check if metric type has a threshold
            metric_type = None
            for mt in MetricType:
                if mt.value == metric_name:
                    metric_type = mt
                    break
            
            if metric_type and metric_type in self.thresholds:
                threshold = self.thresholds[metric_type]
                
                # Determine alert level based on how much threshold is exceeded
                if metric_type == MetricType.CACHE_HIT_RATE:
                    # For cache hit rate, alert if below threshold
                    if avg_value < threshold:
                        alert_level = AlertLevel.WARNING if avg_value > threshold * 0.8 else AlertLevel.ERROR
                        await self._create_alert(
                            alert_level,
                            f"Cache hit rate is low: {avg_value:.2%}",
                            metric_name,
                            avg_value,
                            threshold
                        )
                else:
                    # For other metrics, alert if above threshold
                    if max_value > threshold:
                        if max_value > threshold * 1.2:
                            alert_level = AlertLevel.CRITICAL
                        elif max_value > threshold * 1.1:
                            alert_level = AlertLevel.ERROR
                        else:
                            alert_level = AlertLevel.WARNING
                        
                        await self._create_alert(
                            alert_level,
                            f"{metric_name} is high: {max_value:.2f}",
                            metric_name,
                            max_value,
                            threshold
                        )
    
    async def _create_alert(self, level: AlertLevel, message: str, metric_name: str, 
                          current_value: float, threshold: float):
        """Create and store an alert."""
        alert_id = f"{metric_name}_{int(time.time())}"
        
        alert = Alert(
            id=alert_id,
            level=level,
            message=message,
            metric_name=metric_name,
            current_value=current_value,
            threshold=threshold,
            timestamp=datetime.now()
        )
        
        self.alerts.append(alert)
        
        # Store alert in Redis for persistence
        try:
            await self.redis_client.lpush(
                "system_alerts",
                alert.to_dict()
            )
            # Keep only last 100 alerts
            await self.redis_client.redis_client.ltrim("system_alerts", 0, 99)
        except Exception as e:
            logger.error(f"Failed to store alert: {e}")
        
        # Log alert
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }.get(level, logging.INFO)
        
        logger.log(log_level, f"ALERT [{level.value.upper()}]: {message}")
    
    async def store_metrics(self):
        """Store metrics in Redis for historical analysis."""
        if not self.metrics_buffer:
            return
        
        try:
            # Store metrics in Redis with time-based keys
            current_time = datetime.now()
            date_key = current_time.strftime("%Y-%m-%d")
            hour_key = current_time.strftime("%H")
            
            metrics_key = f"metrics:{date_key}:{hour_key}"
            
            # Convert metrics to JSON
            metrics_data = [metric.to_dict() for metric in self.metrics_buffer]
            
            await self.redis_client.lpush(metrics_key, *metrics_data)
            
            # Set expiration for metrics (keep for 7 days)
            await self.redis_client.expire(metrics_key, 7 * 24 * 3600)
            
            # Clear buffer
            self.metrics_buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")
    
    async def get_metrics(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical metrics."""
        metrics = []
        current_time = datetime.now()
        
        try:
            for hour_offset in range(hours):
                time_point = current_time - timedelta(hours=hour_offset)
                date_key = time_point.strftime("%Y-%m-%d")
                hour_key = time_point.strftime("%H")
                metrics_key = f"metrics:{date_key}:{hour_key}"
                
                hour_metrics = await self.redis_client.lrange(metrics_key, 0, -1)
                
                for metric_data in hour_metrics:
                    if isinstance(metric_data, dict) and metric_data.get('name') == metric_name:
                        metrics.append(metric_data)
        
        except Exception as e:
            logger.error(f"Failed to retrieve metrics: {e}")
        
        return sorted(metrics, key=lambda x: x.get('timestamp', ''))
    
    async def get_alerts(self, level: Optional[AlertLevel] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        try:
            all_alerts = await self.redis_client.lrange("system_alerts", 0, limit - 1)
            
            if level:
                filtered_alerts = [
                    alert for alert in all_alerts 
                    if isinstance(alert, dict) and alert.get('level') == level.value
                ]
                return filtered_alerts
            
            return all_alerts
        
        except Exception as e:
            logger.error(f"Failed to retrieve alerts: {e}")
            return []
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        try:
            # Get recent metrics
            recent_alerts = await self.get_alerts(limit=10)
            critical_alerts = [a for a in recent_alerts if a.get('level') == AlertLevel.CRITICAL.value]
            error_alerts = [a for a in recent_alerts if a.get('level') == AlertLevel.ERROR.value]
            
            # Calculate health score
            health_score = 100.0
            health_score -= len(critical_alerts) * 20  # -20 per critical alert
            health_score -= len(error_alerts) * 10     # -10 per error alert
            health_score = max(health_score, 0)
            
            # Determine status
            if health_score >= 90:
                status = "healthy"
            elif health_score >= 70:
                status = "warning"
            elif health_score >= 50:
                status = "degraded"
            else:
                status = "critical"
            
            # Get latest metrics
            latest_metrics = {}
            if self.metrics_buffer:
                for metric in self.metrics_buffer[-10:]:  # Last 10 metrics
                    latest_metrics[metric.name] = {
                        'value': metric.value,
                        'timestamp': metric.timestamp.isoformat(),
                        'unit': metric.unit
                    }
            
            return {
                'status': status,
                'health_score': health_score,
                'critical_alerts': len(critical_alerts),
                'error_alerts': len(error_alerts),
                'latest_metrics': latest_metrics,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {
                'status': 'unknown',
                'health_score': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def set_threshold(self, metric_type: MetricType, threshold: float):
        """Set alert threshold for a metric type."""
        self.thresholds[metric_type] = threshold
        logger.info(f"Set threshold for {metric_type.value}: {threshold}")
    
    def get_thresholds(self) -> Dict[str, float]:
        """Get current alert thresholds."""
        return {mt.value: threshold for mt, threshold in self.thresholds.items()}

class PerformanceBenchmark:
    """Performance benchmarking and SLA tracking."""
    
    def __init__(self):
        self.benchmarks = {
            'query_response_time': {
                'target': 2.0,  # 2 seconds
                'sla': 0.95     # 95% of queries should meet target
            },
            'document_processing_time': {
                'target': 30.0,  # 30 seconds per document
                'sla': 0.90      # 90% should meet target
            },
            'system_availability': {
                'target': 0.999,  # 99.9% uptime
                'sla': 0.999
            },
            'cache_hit_rate': {
                'target': 0.80,   # 80% cache hit rate
                'sla': 0.75       # Minimum 75%
            }
        }
        self.performance_data = {}
    
    def record_performance(self, benchmark_name: str, value: float, timestamp: Optional[datetime] = None):
        """Record a performance measurement."""
        if timestamp is None:
            timestamp = datetime.now()
        
        if benchmark_name not in self.performance_data:
            self.performance_data[benchmark_name] = []
        
        self.performance_data[benchmark_name].append({
            'value': value,
            'timestamp': timestamp,
            'meets_target': value <= self.benchmarks.get(benchmark_name, {}).get('target', float('inf'))
        })
        
        # Keep only last 1000 measurements per benchmark
        if len(self.performance_data[benchmark_name]) > 1000:
            self.performance_data[benchmark_name] = self.performance_data[benchmark_name][-1000:]
    
    def get_sla_compliance(self, benchmark_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get SLA compliance for a benchmark."""
        if benchmark_name not in self.performance_data:
            return {'error': 'No data available'}
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_data = [
            d for d in self.performance_data[benchmark_name]
            if d['timestamp'] > cutoff_time
        ]
        
        if not recent_data:
            return {'error': 'No recent data available'}
        
        total_measurements = len(recent_data)
        successful_measurements = sum(1 for d in recent_data if d['meets_target'])
        compliance_rate = successful_measurements / total_measurements
        
        benchmark_config = self.benchmarks.get(benchmark_name, {})
        target = benchmark_config.get('target')
        sla_threshold = benchmark_config.get('sla')
        
        values = [d['value'] for d in recent_data]
        
        return {
            'benchmark_name': benchmark_name,
            'compliance_rate': compliance_rate,
            'sla_threshold': sla_threshold,
            'meets_sla': compliance_rate >= sla_threshold,
            'target': target,
            'total_measurements': total_measurements,
            'successful_measurements': successful_measurements,
            'average_value': statistics.mean(values),
            'median_value': statistics.median(values),
            'p95_value': statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values),
            'p99_value': statistics.quantiles(values, n=100)[98] if len(values) >= 100 else max(values),
            'time_range_hours': hours
        }
    
    def get_all_sla_compliance(self, hours: int = 24) -> Dict[str, Any]:
        """Get SLA compliance for all benchmarks."""
        compliance_data = {}
        
        for benchmark_name in self.benchmarks.keys():
            compliance_data[benchmark_name] = self.get_sla_compliance(benchmark_name, hours)
        
        return compliance_data
    
    def set_benchmark(self, name: str, target: float, sla: float):
        """Set a new benchmark or update existing one."""
        self.benchmarks[name] = {
            'target': target,
            'sla': sla
        }

# Global instances
performance_monitor = PerformanceMonitor()
performance_benchmark = PerformanceBenchmark()

def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return performance_monitor

def get_performance_benchmark() -> PerformanceBenchmark:
    """Get the global performance benchmark instance."""
    return performance_benchmark