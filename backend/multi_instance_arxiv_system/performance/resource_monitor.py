"""
Resource Monitoring System for Multi-Instance ArXiv System.

This module provides comprehensive resource monitoring, alerting, and
dynamic resource allocation based on system load and performance metrics.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import threading
import time
import statistics
from dataclasses import dataclass, field, asdict
from enum import Enum

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of system resources."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"


class AlertLevel(Enum):
    """Resource alert levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class ResourceStats:
    """Resource utilization statistics."""
    
    resource_type: ResourceType
    timestamp: datetime
    instance_name: str
    
    # Usage metrics
    current_usage: float  # Percentage or absolute value
    average_usage: float  # Over monitoring period
    peak_usage: float     # Maximum observed
    
    # Capacity metrics
    total_capacity: float
    available_capacity: float
    
    # Performance metrics
    throughput: float = 0.0  # Operations per second
    latency_ms: float = 0.0  # Average latency
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def usage_percentage(self) -> float:
        """Calculate usage as percentage of total capacity."""
        if self.total_capacity == 0:
            return 0.0
        return (self.current_usage / self.total_capacity) * 100.0
    
    @property
    def available_percentage(self) -> float:
        """Calculate available capacity as percentage."""
        if self.total_capacity == 0:
            return 0.0
        return (self.available_capacity / self.total_capacity) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['resource_type'] = self.resource_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResourceStats':
        """Create from dictionary (JSON deserialization)."""
        data['resource_type'] = ResourceType(data['resource_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ResourceAlert:
    """Resource utilization alert."""
    
    alert_id: str
    resource_type: ResourceType
    alert_level: AlertLevel
    instance_name: str
    
    title: str
    message: str
    current_value: float
    threshold_value: float
    
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['resource_type'] = self.resource_type.value
        data['alert_level'] = self.alert_level.value
        data['created_at'] = self.created_at.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data
    
    def resolve(self) -> None:
        """Mark alert as resolved."""
        self.resolved_at = datetime.now()
    
    def acknowledge(self) -> None:
        """Acknowledge the alert."""
        self.acknowledged = True


class ResourceMonitor:
    """
    Comprehensive resource monitor with alerting and dynamic allocation.
    """
    
    def __init__(
        self,
        instance_name: str,
        monitoring_interval: int = 30,
        history_size: int = 1000
    ):
        self.instance_name = instance_name
        self.monitoring_interval = monitoring_interval
        self.history_size = history_size
        
        # Resource tracking
        self.resource_history: Dict[ResourceType, List[ResourceStats]] = {
            resource_type: [] for resource_type in ResourceType
        }
        
        # Alerting
        self.active_alerts: List[ResourceAlert] = []
        self.alert_history: List[ResourceAlert] = []
        self.alert_thresholds = {
            ResourceType.CPU: {
                'warning': 70.0,
                'critical': 85.0,
                'emergency': 95.0
            },
            ResourceType.MEMORY: {
                'warning': 75.0,
                'critical': 90.0,
                'emergency': 98.0
            },
            ResourceType.DISK: {
                'warning': 80.0,
                'critical': 90.0,
                'emergency': 95.0
            },
            ResourceType.NETWORK: {
                'warning': 70.0,
                'critical': 85.0,
                'emergency': 95.0
            }
        }
        
        # Monitoring control
        self.monitoring_active = False
        self.last_monitoring_cycle = datetime.now()
        
        # Threading
        self.lock = threading.RLock()
        
        # Resource collectors
        self.resource_collectors = {
            ResourceType.CPU: self._collect_cpu_stats,
            ResourceType.MEMORY: self._collect_memory_stats,
            ResourceType.DISK: self._collect_disk_stats,
            ResourceType.NETWORK: self._collect_network_stats
        }
        
        logger.info(f"ResourceMonitor initialized for {instance_name}")
    
    def start_monitoring(self) -> None:
        """Start resource monitoring."""
        
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # Start monitoring thread
        monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            name=f"ResourceMonitor-{self.instance_name}",
            daemon=True
        )
        monitoring_thread.start()
        
        logger.info(f"Resource monitoring started for {self.instance_name}")
    
    def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        self.monitoring_active = False
        logger.info(f"Resource monitoring stopped for {self.instance_name}")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop (runs in separate thread)."""
        
        while self.monitoring_active:
            try:
                # Collect resource statistics
                self._collect_all_resources()
                
                # Check for alerts
                self._check_alert_conditions()
                
                # Clean up old data
                self._cleanup_old_data()
                
                self.last_monitoring_cycle = datetime.now()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in resource monitoring loop for {self.instance_name}: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _collect_all_resources(self) -> None:
        """Collect statistics for all monitored resources."""
        
        for resource_type, collector_func in self.resource_collectors.items():
            try:
                stats = collector_func()
                if stats:
                    with self.lock:
                        self.resource_history[resource_type].append(stats)
                        
                        # Maintain history size
                        if len(self.resource_history[resource_type]) > self.history_size:
                            self.resource_history[resource_type] = (
                                self.resource_history[resource_type][-self.history_size:]
                            )
                        
            except Exception as e:
                logger.error(f"Error collecting {resource_type.value} stats: {e}")
    
    def _collect_cpu_stats(self) -> Optional[ResourceStats]:
        """Collect CPU utilization statistics."""
        
        try:
            import psutil
            
            # Get CPU usage over a short interval
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Get load average (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()[0]  # 1-minute load average
            except (AttributeError, OSError):
                load_avg = cpu_percent / 100.0  # Fallback
            
            # Calculate recent average
            recent_stats = self.get_recent_stats(ResourceType.CPU, hours=1)
            avg_usage = statistics.mean([s.current_usage for s in recent_stats]) if recent_stats else cpu_percent
            peak_usage = max([s.current_usage for s in recent_stats] + [cpu_percent]) if recent_stats else cpu_percent
            
            return ResourceStats(
                resource_type=ResourceType.CPU,
                timestamp=datetime.now(),
                instance_name=self.instance_name,
                current_usage=cpu_percent,
                average_usage=avg_usage,
                peak_usage=peak_usage,
                total_capacity=100.0,  # CPU usage is in percentage
                available_capacity=100.0 - cpu_percent,
                metadata={
                    'cpu_count': cpu_count,
                    'load_average': load_avg,
                    'per_cpu_usage': psutil.cpu_percent(percpu=True)
                }
            )
            
        except ImportError:
            logger.warning("psutil not available for CPU monitoring")
            return None
        except Exception as e:
            logger.error(f"Error collecting CPU stats: {e}")
            return None
    
    def _collect_memory_stats(self) -> Optional[ResourceStats]:
        """Collect memory utilization statistics."""
        
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Convert to MB
            total_mb = memory.total / 1024 / 1024
            used_mb = memory.used / 1024 / 1024
            available_mb = memory.available / 1024 / 1024
            
            # Calculate recent average
            recent_stats = self.get_recent_stats(ResourceType.MEMORY, hours=1)
            avg_usage = statistics.mean([s.current_usage for s in recent_stats]) if recent_stats else used_mb
            peak_usage = max([s.current_usage for s in recent_stats] + [used_mb]) if recent_stats else used_mb
            
            return ResourceStats(
                resource_type=ResourceType.MEMORY,
                timestamp=datetime.now(),
                instance_name=self.instance_name,
                current_usage=used_mb,
                average_usage=avg_usage,
                peak_usage=peak_usage,
                total_capacity=total_mb,
                available_capacity=available_mb,
                metadata={
                    'memory_percent': memory.percent,
                    'swap_total_mb': swap.total / 1024 / 1024,
                    'swap_used_mb': swap.used / 1024 / 1024,
                    'swap_percent': swap.percent,
                    'cached_mb': getattr(memory, 'cached', 0) / 1024 / 1024,
                    'buffers_mb': getattr(memory, 'buffers', 0) / 1024 / 1024
                }
            )
            
        except ImportError:
            logger.warning("psutil not available for memory monitoring")
            return None
        except Exception as e:
            logger.error(f"Error collecting memory stats: {e}")
            return None
    
    def _collect_disk_stats(self) -> Optional[ResourceStats]:
        """Collect disk utilization statistics."""
        
        try:
            import psutil
            
            # Get disk usage for root partition
            disk_usage = psutil.disk_usage('/')
            
            # Convert to GB
            total_gb = disk_usage.total / 1024 / 1024 / 1024
            used_gb = disk_usage.used / 1024 / 1024 / 1024
            free_gb = disk_usage.free / 1024 / 1024 / 1024
            
            # Get I/O statistics
            disk_io = psutil.disk_io_counters()
            
            # Calculate recent average
            recent_stats = self.get_recent_stats(ResourceType.DISK, hours=1)
            avg_usage = statistics.mean([s.current_usage for s in recent_stats]) if recent_stats else used_gb
            peak_usage = max([s.current_usage for s in recent_stats] + [used_gb]) if recent_stats else used_gb
            
            return ResourceStats(
                resource_type=ResourceType.DISK,
                timestamp=datetime.now(),
                instance_name=self.instance_name,
                current_usage=used_gb,
                average_usage=avg_usage,
                peak_usage=peak_usage,
                total_capacity=total_gb,
                available_capacity=free_gb,
                metadata={
                    'usage_percent': (used_gb / total_gb) * 100 if total_gb > 0 else 0,
                    'read_bytes': disk_io.read_bytes if disk_io else 0,
                    'write_bytes': disk_io.write_bytes if disk_io else 0,
                    'read_count': disk_io.read_count if disk_io else 0,
                    'write_count': disk_io.write_count if disk_io else 0
                }
            )
            
        except ImportError:
            logger.warning("psutil not available for disk monitoring")
            return None
        except Exception as e:
            logger.error(f"Error collecting disk stats: {e}")
            return None
    
    def _collect_network_stats(self) -> Optional[ResourceStats]:
        """Collect network utilization statistics."""
        
        try:
            import psutil
            
            # Get network I/O statistics
            net_io = psutil.net_io_counters()
            
            if not net_io:
                return None
            
            # Convert to MB
            bytes_sent_mb = net_io.bytes_sent / 1024 / 1024
            bytes_recv_mb = net_io.bytes_recv / 1024 / 1024
            total_bytes_mb = bytes_sent_mb + bytes_recv_mb
            
            # Calculate throughput (simplified)
            recent_stats = self.get_recent_stats(ResourceType.NETWORK, hours=1)
            if recent_stats and len(recent_stats) > 1:
                # Calculate rate based on recent measurements
                time_diff = (datetime.now() - recent_stats[-1].timestamp).total_seconds()
                if time_diff > 0:
                    throughput = (total_bytes_mb - recent_stats[-1].current_usage) / time_diff
                else:
                    throughput = 0.0
            else:
                throughput = 0.0
            
            # Calculate recent average
            avg_usage = statistics.mean([s.current_usage for s in recent_stats]) if recent_stats else total_bytes_mb
            peak_usage = max([s.current_usage for s in recent_stats] + [total_bytes_mb]) if recent_stats else total_bytes_mb
            
            return ResourceStats(
                resource_type=ResourceType.NETWORK,
                timestamp=datetime.now(),
                instance_name=self.instance_name,
                current_usage=total_bytes_mb,
                average_usage=avg_usage,
                peak_usage=peak_usage,
                total_capacity=float('inf'),  # No fixed capacity for network
                available_capacity=float('inf'),
                throughput=throughput,
                metadata={
                    'bytes_sent_mb': bytes_sent_mb,
                    'bytes_recv_mb': bytes_recv_mb,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                    'errin': net_io.errin,
                    'errout': net_io.errout,
                    'dropin': net_io.dropin,
                    'dropout': net_io.dropout
                }
            )
            
        except ImportError:
            logger.warning("psutil not available for network monitoring")
            return None
        except Exception as e:
            logger.error(f"Error collecting network stats: {e}")
            return None
    
    def _check_alert_conditions(self) -> None:
        """Check for alert conditions and generate alerts."""
        
        with self.lock:
            for resource_type in ResourceType:
                if resource_type not in self.resource_history:
                    continue
                
                recent_stats = self.resource_history[resource_type]
                if not recent_stats:
                    continue
                
                latest_stats = recent_stats[-1]
                usage_percent = latest_stats.usage_percentage
                
                # Check thresholds
                thresholds = self.alert_thresholds.get(resource_type, {})
                
                alert_level = None
                threshold_value = 0.0
                
                if usage_percent >= thresholds.get('emergency', 95):
                    alert_level = AlertLevel.EMERGENCY
                    threshold_value = thresholds.get('emergency', 95)
                elif usage_percent >= thresholds.get('critical', 85):
                    alert_level = AlertLevel.CRITICAL
                    threshold_value = thresholds.get('critical', 85)
                elif usage_percent >= thresholds.get('warning', 70):
                    alert_level = AlertLevel.WARNING
                    threshold_value = thresholds.get('warning', 70)
                
                if alert_level:
                    # Check if similar alert already exists
                    existing_alert = self._find_active_alert(resource_type, alert_level)
                    
                    if not existing_alert:
                        # Create new alert
                        alert = ResourceAlert(
                            alert_id=f"{resource_type.value}_{alert_level.value}_{int(time.time())}",
                            resource_type=resource_type,
                            alert_level=alert_level,
                            instance_name=self.instance_name,
                            title=f"{resource_type.value.upper()} {alert_level.value.upper()}",
                            message=f"{resource_type.value.upper()} usage is {usage_percent:.1f}% (threshold: {threshold_value:.1f}%)",
                            current_value=usage_percent,
                            threshold_value=threshold_value
                        )
                        
                        self.active_alerts.append(alert)
                        logger.warning(f"Resource alert: {alert.message}")
                
                # Resolve alerts if usage has dropped
                self._resolve_alerts_if_needed(resource_type, usage_percent)
    
    def _find_active_alert(self, resource_type: ResourceType, alert_level: AlertLevel) -> Optional[ResourceAlert]:
        """Find active alert for resource type and level."""
        
        for alert in self.active_alerts:
            if (alert.resource_type == resource_type and 
                alert.alert_level == alert_level and 
                alert.resolved_at is None):
                return alert
        
        return None
    
    def _resolve_alerts_if_needed(self, resource_type: ResourceType, current_usage: float) -> None:
        """Resolve alerts if usage has dropped below thresholds."""
        
        thresholds = self.alert_thresholds.get(resource_type, {})
        
        for alert in self.active_alerts[:]:  # Copy list to avoid modification during iteration
            if (alert.resource_type == resource_type and 
                alert.resolved_at is None):
                
                # Resolve if usage dropped significantly below threshold
                resolution_threshold = alert.threshold_value * 0.9  # 10% below threshold
                
                if current_usage < resolution_threshold:
                    alert.resolve()
                    self.active_alerts.remove(alert)
                    self.alert_history.append(alert)
                    
                    logger.info(f"Resolved resource alert: {alert.message}")
    
    def _cleanup_old_data(self) -> None:
        """Clean up old resource data and alerts."""
        
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        with self.lock:
            # Clean up old alert history
            self.alert_history = [
                alert for alert in self.alert_history
                if alert.created_at >= cutoff_time
            ]
            
            # Resource history is already managed by size limit
    
    def get_recent_stats(self, resource_type: ResourceType, hours: int = 1) -> List[ResourceStats]:
        """Get recent resource statistics."""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            if resource_type not in self.resource_history:
                return []
            
            return [
                stats for stats in self.resource_history[resource_type]
                if stats.timestamp >= cutoff_time
            ]
    
    def get_current_stats(self, resource_type: ResourceType) -> Optional[ResourceStats]:
        """Get most recent statistics for a resource type."""
        
        with self.lock:
            if resource_type not in self.resource_history:
                return None
            
            history = self.resource_history[resource_type]
            return history[-1] if history else None
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """Get comprehensive resource utilization summary."""
        
        with self.lock:
            summary = {
                'instance_name': self.instance_name,
                'monitoring_active': self.monitoring_active,
                'last_monitoring_cycle': self.last_monitoring_cycle.isoformat(),
                'resources': {},
                'alerts': {
                    'active_count': len(self.active_alerts),
                    'total_history': len(self.alert_history),
                    'active_alerts': [alert.to_dict() for alert in self.active_alerts],
                    'recent_alerts': [
                        alert.to_dict() for alert in self.alert_history[-5:]
                    ]
                }
            }
            
            # Add resource summaries
            for resource_type in ResourceType:
                current_stats = self.get_current_stats(resource_type)
                recent_stats = self.get_recent_stats(resource_type, hours=1)
                
                if current_stats:
                    summary['resources'][resource_type.value] = {
                        'current_usage': current_stats.current_usage,
                        'usage_percentage': current_stats.usage_percentage,
                        'available_capacity': current_stats.available_capacity,
                        'average_usage_1h': (
                            statistics.mean([s.current_usage for s in recent_stats])
                            if recent_stats else current_stats.current_usage
                        ),
                        'peak_usage_1h': (
                            max([s.current_usage for s in recent_stats])
                            if recent_stats else current_stats.current_usage
                        ),
                        'throughput': current_stats.throughput,
                        'latency_ms': current_stats.latency_ms,
                        'last_updated': current_stats.timestamp.isoformat()
                    }
                else:
                    summary['resources'][resource_type.value] = {
                        'status': 'no_data',
                        'message': 'No recent statistics available'
                    }
            
            return summary
    
    def set_alert_threshold(
        self, 
        resource_type: ResourceType, 
        level: str, 
        threshold: float
    ) -> bool:
        """Set alert threshold for a resource type and level."""
        
        if level not in ['warning', 'critical', 'emergency']:
            return False
        
        with self.lock:
            if resource_type not in self.alert_thresholds:
                self.alert_thresholds[resource_type] = {}
            
            self.alert_thresholds[resource_type][level] = threshold
            
            logger.info(f"Set {resource_type.value} {level} threshold to {threshold}%")
            return True
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge a specific alert."""
        
        with self.lock:
            for alert in self.active_alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledge()
                    logger.info(f"Acknowledged alert: {alert_id}")
                    return True
            
            return False
    
    def get_resource_recommendations(self) -> List[str]:
        """Get resource optimization recommendations based on current usage."""
        
        recommendations = []
        
        with self.lock:
            for resource_type in ResourceType:
                current_stats = self.get_current_stats(resource_type)
                if not current_stats:
                    continue
                
                usage_percent = current_stats.usage_percentage
                
                if resource_type == ResourceType.CPU and usage_percent > 80:
                    recommendations.append("Consider reducing CPU-intensive operations or adding more processing power")
                
                elif resource_type == ResourceType.MEMORY and usage_percent > 85:
                    recommendations.append("Implement memory cleanup or increase available memory")
                
                elif resource_type == ResourceType.DISK and usage_percent > 90:
                    recommendations.append("Clean up old files or add more storage capacity")
                
                elif resource_type == ResourceType.NETWORK and current_stats.throughput > 100:
                    recommendations.append("Consider optimizing network operations or upgrading bandwidth")
        
        return recommendations