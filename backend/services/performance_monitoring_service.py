"""
Performance Monitoring Service

This service provides real-time performance monitoring and metrics collection
for all advanced features including mobile, voice, integration, and enterprise systems.
"""

import asyncio
import time
import psutil
import json
import statistics
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
from collections import deque, defaultdict
import threading
import queue
import weakref

logger = logging.getLogger(__name__)

@dataclass
class PerformanceAlert:
    """Performance alert data structure"""
    alert_id: str
    alert_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    metric_name: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    component: str
    resolved: bool = False

@dataclass
class MetricThreshold:
    """Metric threshold configuration"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison_type: str  # 'greater_than', 'less_than', 'equals'
    enabled: bool = True

@dataclass
class PerformanceSnapshot:
    """Real-time performance snapshot"""
    timestamp: datetime
    cpu_usage_percent: float
    memory_usage_mb: float
    memory_usage_percent: float
    disk_usage_percent: float
    network_io_bytes_sent: int
    network_io_bytes_recv: int
    active_connections: int
    response_time_ms: Optional[float] = None
    throughput_ops_per_sec: Optional[float] = None
    error_rate_percent: Optional[float] = None

class PerformanceMonitoringService:
    """Real-time performance monitoring service"""
    
    def __init__(self, monitoring_interval: float = 5.0):
        self.monitoring_interval = monitoring_interval
        self.is_monitoring = False
        self.metrics_history: deque = deque(maxlen=1000)  # Keep last 1000 snapshots
        self.alerts: List[PerformanceAlert] = []
        self.thresholds: Dict[str, MetricThreshold] = {}
        self.alert_callbacks: List[Callable] = []
        self.component_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.monitoring_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Initialize default thresholds
        self._initialize_default_thresholds()
    
    def _initialize_default_thresholds(self):
        """Initialize default performance thresholds"""
        self.thresholds = {
            'cpu_usage_percent': MetricThreshold(
                metric_name='cpu_usage_percent',
                warning_threshold=70.0,
                critical_threshold=90.0,
                comparison_type='greater_than'
            ),
            'memory_usage_percent': MetricThreshold(
                metric_name='memory_usage_percent',
                warning_threshold=80.0,
                critical_threshold=95.0,
                comparison_type='greater_than'
            ),
            'disk_usage_percent': MetricThreshold(
                metric_name='disk_usage_percent',
                warning_threshold=85.0,
                critical_threshold=95.0,
                comparison_type='greater_than'
            ),
            'response_time_ms': MetricThreshold(
                metric_name='response_time_ms',
                warning_threshold=500.0,
                critical_threshold=1000.0,
                comparison_type='greater_than'
            ),
            'error_rate_percent': MetricThreshold(
                metric_name='error_rate_percent',
                warning_threshold=5.0,
                critical_threshold=10.0,
                comparison_type='greater_than'
            ),
            'throughput_ops_per_sec': MetricThreshold(
                metric_name='throughput_ops_per_sec',
                warning_threshold=10.0,
                critical_threshold=5.0,
                comparison_type='less_than'
            )
        }
    
    def start_monitoring(self):
        """Start real-time performance monitoring"""
        if self.is_monitoring:
            logger.warning("Performance monitoring is already running")
            return
        
        self.is_monitoring = True
        self.stop_event.clear()
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        self.stop_event.set()
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while not self.stop_event.is_set():
            try:
                snapshot = self._collect_performance_snapshot()
                self.metrics_history.append(snapshot)
                
                # Check thresholds and generate alerts
                self._check_thresholds(snapshot)
                
                # Sleep until next monitoring interval
                self.stop_event.wait(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                self.stop_event.wait(self.monitoring_interval)
    
    def _collect_performance_snapshot(self) -> PerformanceSnapshot:
        """Collect current performance metrics"""
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        # Network connections
        try:
            connections = len(psutil.net_connections())
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            connections = 0
        
        return PerformanceSnapshot(
            timestamp=datetime.now(),
            cpu_usage_percent=cpu_percent,
            memory_usage_mb=memory.used / 1024 / 1024,
            memory_usage_percent=memory.percent,
            disk_usage_percent=disk.percent,
            network_io_bytes_sent=network.bytes_sent,
            network_io_bytes_recv=network.bytes_recv,
            active_connections=connections
        )
    
    def _check_thresholds(self, snapshot: PerformanceSnapshot):
        """Check performance thresholds and generate alerts"""
        snapshot_dict = asdict(snapshot)
        
        for metric_name, threshold in self.thresholds.items():
            if not threshold.enabled:
                continue
            
            if metric_name not in snapshot_dict:
                continue
            
            current_value = snapshot_dict[metric_name]
            if current_value is None:
                continue
            
            # Check if threshold is exceeded
            alert_triggered = False
            severity = None
            
            if threshold.comparison_type == 'greater_than':
                if current_value >= threshold.critical_threshold:
                    alert_triggered = True
                    severity = 'critical'
                elif current_value >= threshold.warning_threshold:
                    alert_triggered = True
                    severity = 'medium'
            elif threshold.comparison_type == 'less_than':
                if current_value <= threshold.critical_threshold:
                    alert_triggered = True
                    severity = 'critical'
                elif current_value <= threshold.warning_threshold:
                    alert_triggered = True
                    severity = 'medium'
            
            if alert_triggered:
                self._generate_alert(
                    metric_name=metric_name,
                    current_value=current_value,
                    threshold_value=threshold.critical_threshold if severity == 'critical' else threshold.warning_threshold,
                    severity=severity,
                    component='system'
                )
    
    def _generate_alert(self, metric_name: str, current_value: float, threshold_value: float, 
                       severity: str, component: str):
        """Generate performance alert"""
        alert_id = f"{metric_name}_{component}_{int(time.time())}"
        
        # Check if similar alert already exists and is not resolved
        existing_alert = next(
            (alert for alert in self.alerts 
             if alert.metric_name == metric_name 
             and alert.component == component 
             and not alert.resolved),
            None
        )
        
        if existing_alert:
            # Update existing alert
            existing_alert.current_value = current_value
            existing_alert.timestamp = datetime.now()
            existing_alert.severity = severity
        else:
            # Create new alert
            alert = PerformanceAlert(
                alert_id=alert_id,
                alert_type='threshold_exceeded',
                severity=severity,
                message=f"{metric_name} exceeded threshold: {current_value:.2f} > {threshold_value:.2f}",
                metric_name=metric_name,
                current_value=current_value,
                threshold_value=threshold_value,
                timestamp=datetime.now(),
                component=component
            )
            
            self.alerts.append(alert)
            
            # Notify alert callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback: {str(e)}")
    
    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Add callback function for alert notifications"""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Remove alert callback"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def record_component_metric(self, component: str, metric_name: str, value: float, timestamp: datetime = None):
        """Record custom component metric"""
        timestamp = timestamp or datetime.now()
        
        metric_key = f"{component}_{metric_name}"
        self.component_metrics[metric_key].append({
            'timestamp': timestamp,
            'value': value,
            'component': component,
            'metric_name': metric_name
        })
        
        # Check component-specific thresholds
        if metric_name in self.thresholds:
            threshold = self.thresholds[metric_name]
            
            alert_triggered = False
            severity = None
            
            if threshold.comparison_type == 'greater_than':
                if value >= threshold.critical_threshold:
                    alert_triggered = True
                    severity = 'critical'
                elif value >= threshold.warning_threshold:
                    alert_triggered = True
                    severity = 'medium'
            elif threshold.comparison_type == 'less_than':
                if value <= threshold.critical_threshold:
                    alert_triggered = True
                    severity = 'critical'
                elif value <= threshold.warning_threshold:
                    alert_triggered = True
                    severity = 'medium'
            
            if alert_triggered:
                self._generate_alert(
                    metric_name=metric_name,
                    current_value=value,
                    threshold_value=threshold.critical_threshold if severity == 'critical' else threshold.warning_threshold,
                    severity=severity,
                    component=component
                )
    
    def get_current_metrics(self) -> Optional[PerformanceSnapshot]:
        """Get current performance metrics"""
        if not self.metrics_history:
            return None
        return self.metrics_history[-1]
    
    def get_metrics_history(self, duration_minutes: int = 60) -> List[PerformanceSnapshot]:
        """Get performance metrics history for specified duration"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        return [
            snapshot for snapshot in self.metrics_history
            if snapshot.timestamp >= cutoff_time
        ]
    
    def get_component_metrics(self, component: str, metric_name: str = None, duration_minutes: int = 60) -> List[Dict[str, Any]]:
        """Get component-specific metrics"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        if metric_name:
            metric_key = f"{component}_{metric_name}"
            if metric_key in self.component_metrics:
                return [
                    metric for metric in self.component_metrics[metric_key]
                    if metric['timestamp'] >= cutoff_time
                ]
        else:
            # Return all metrics for component
            all_metrics = []
            for metric_key, metrics in self.component_metrics.items():
                if metric_key.startswith(f"{component}_"):
                    all_metrics.extend([
                        metric for metric in metrics
                        if metric['timestamp'] >= cutoff_time
                    ])
            return all_metrics
        
        return []
    
    def get_active_alerts(self, severity: str = None) -> List[PerformanceAlert]:
        """Get active (unresolved) alerts"""
        active_alerts = [alert for alert in self.alerts if not alert.resolved]
        
        if severity:
            active_alerts = [alert for alert in active_alerts if alert.severity == severity]
        
        return active_alerts
    
    def resolve_alert(self, alert_id: str):
        """Mark alert as resolved"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                break
    
    def get_performance_summary(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """Get performance summary for specified duration"""
        history = self.get_metrics_history(duration_minutes)
        
        if not history:
            return {'error': 'No performance data available'}
        
        # Calculate statistics
        cpu_values = [s.cpu_usage_percent for s in history]
        memory_values = [s.memory_usage_percent for s in history]
        
        # Active alerts by severity
        active_alerts = self.get_active_alerts()
        alerts_by_severity = defaultdict(int)
        for alert in active_alerts:
            alerts_by_severity[alert.severity] += 1
        
        # Performance trends
        recent_snapshots = history[-10:] if len(history) >= 10 else history
        older_snapshots = history[:10] if len(history) >= 20 else history[:len(history)//2]
        
        cpu_trend = 'stable'
        memory_trend = 'stable'
        
        if recent_snapshots and older_snapshots:
            recent_cpu_avg = statistics.mean([s.cpu_usage_percent for s in recent_snapshots])
            older_cpu_avg = statistics.mean([s.cpu_usage_percent for s in older_snapshots])
            
            recent_memory_avg = statistics.mean([s.memory_usage_percent for s in recent_snapshots])
            older_memory_avg = statistics.mean([s.memory_usage_percent for s in older_snapshots])
            
            if recent_cpu_avg > older_cpu_avg * 1.1:
                cpu_trend = 'increasing'
            elif recent_cpu_avg < older_cpu_avg * 0.9:
                cpu_trend = 'decreasing'
            
            if recent_memory_avg > older_memory_avg * 1.1:
                memory_trend = 'increasing'
            elif recent_memory_avg < older_memory_avg * 0.9:
                memory_trend = 'decreasing'
        
        return {
            'timestamp': datetime.now().isoformat(),
            'duration_minutes': duration_minutes,
            'data_points': len(history),
            'system_metrics': {
                'cpu_usage': {
                    'current': history[-1].cpu_usage_percent,
                    'average': statistics.mean(cpu_values),
                    'max': max(cpu_values),
                    'min': min(cpu_values),
                    'trend': cpu_trend
                },
                'memory_usage': {
                    'current': history[-1].memory_usage_percent,
                    'average': statistics.mean(memory_values),
                    'max': max(memory_values),
                    'min': min(memory_values),
                    'trend': memory_trend
                },
                'disk_usage': history[-1].disk_usage_percent,
                'active_connections': history[-1].active_connections
            },
            'alerts': {
                'total_active': len(active_alerts),
                'by_severity': dict(alerts_by_severity),
                'recent_alerts': [asdict(alert) for alert in active_alerts[-5:]]
            },
            'health_status': self._calculate_health_status(history, active_alerts)
        }
    
    def _calculate_health_status(self, history: List[PerformanceSnapshot], active_alerts: List[PerformanceAlert]) -> str:
        """Calculate overall system health status"""
        if not history:
            return 'unknown'
        
        current = history[-1]
        critical_alerts = [alert for alert in active_alerts if alert.severity == 'critical']
        
        # Critical conditions
        if critical_alerts:
            return 'critical'
        
        if (current.cpu_usage_percent > 90 or 
            current.memory_usage_percent > 95 or 
            current.disk_usage_percent > 95):
            return 'critical'
        
        # Warning conditions
        warning_alerts = [alert for alert in active_alerts if alert.severity in ['medium', 'high']]
        if warning_alerts:
            return 'warning'
        
        if (current.cpu_usage_percent > 70 or 
            current.memory_usage_percent > 80 or 
            current.disk_usage_percent > 85):
            return 'warning'
        
        return 'healthy'
    
    def export_metrics(self, duration_minutes: int = 60, format: str = 'json') -> str:
        """Export performance metrics in specified format"""
        history = self.get_metrics_history(duration_minutes)
        active_alerts = self.get_active_alerts()
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'duration_minutes': duration_minutes,
            'metrics_history': [asdict(snapshot) for snapshot in history],
            'active_alerts': [asdict(alert) for alert in active_alerts],
            'component_metrics': {
                key: list(metrics) for key, metrics in self.component_metrics.items()
            }
        }
        
        if format.lower() == 'json':
            return json.dumps(export_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def configure_threshold(self, metric_name: str, warning_threshold: float, 
                          critical_threshold: float, comparison_type: str = 'greater_than'):
        """Configure performance threshold"""
        self.thresholds[metric_name] = MetricThreshold(
            metric_name=metric_name,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            comparison_type=comparison_type
        )
        logger.info(f"Configured threshold for {metric_name}: warning={warning_threshold}, critical={critical_threshold}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for performance dashboard"""
        current_metrics = self.get_current_metrics()
        summary = self.get_performance_summary(60)
        active_alerts = self.get_active_alerts()
        
        # Recent performance data for charts
        recent_history = self.get_metrics_history(30)  # Last 30 minutes
        
        chart_data = {
            'timestamps': [s.timestamp.isoformat() for s in recent_history],
            'cpu_usage': [s.cpu_usage_percent for s in recent_history],
            'memory_usage': [s.memory_usage_percent for s in recent_history],
            'disk_usage': [s.disk_usage_percent for s in recent_history],
            'active_connections': [s.active_connections for s in recent_history]
        }
        
        return {
            'current_metrics': asdict(current_metrics) if current_metrics else None,
            'summary': summary,
            'active_alerts': [asdict(alert) for alert in active_alerts],
            'chart_data': chart_data,
            'health_status': summary.get('health_status', 'unknown'),
            'monitoring_active': self.is_monitoring
        }

# Context manager for performance monitoring
class PerformanceMonitor:
    """Context manager for component performance monitoring"""
    
    def __init__(self, monitoring_service: PerformanceMonitoringService, 
                 component: str, operation: str):
        self.monitoring_service = monitoring_service
        self.component = component
        self.operation = operation
        self.start_time = None
        self.start_memory = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.start_memory = psutil.virtual_memory().used / 1024 / 1024
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        end_memory = psutil.virtual_memory().used / 1024 / 1024
        
        duration_ms = (end_time - self.start_time) * 1000
        memory_delta = end_memory - self.start_memory
        
        # Record metrics
        self.monitoring_service.record_component_metric(
            self.component, 
            f"{self.operation}_duration_ms", 
            duration_ms
        )
        
        self.monitoring_service.record_component_metric(
            self.component, 
            f"{self.operation}_memory_delta_mb", 
            memory_delta
        )
        
        # Record error if exception occurred
        if exc_type is not None:
            self.monitoring_service.record_component_metric(
                self.component, 
                f"{self.operation}_error_count", 
                1
            )

# Example usage
if __name__ == "__main__":
    # Create monitoring service
    monitoring_service = PerformanceMonitoringService(monitoring_interval=2.0)
    
    # Add alert callback
    def alert_handler(alert: PerformanceAlert):
        print(f"ALERT: {alert.severity.upper()} - {alert.message}")
    
    monitoring_service.add_alert_callback(alert_handler)
    
    # Start monitoring
    monitoring_service.start_monitoring()
    
    try:
        # Simulate some work and component metrics
        for i in range(10):
            time.sleep(5)
            
            # Record some component metrics
            monitoring_service.record_component_metric('voice_processing', 'latency_ms', 150 + i * 10)
            monitoring_service.record_component_metric('mobile_sync', 'sync_time_ms', 200 + i * 5)
            
            # Get dashboard data
            dashboard_data = monitoring_service.get_dashboard_data()
            print(f"Health Status: {dashboard_data['health_status']}")
            
            if i == 5:
                # Get performance summary
                summary = monitoring_service.get_performance_summary()
                print(json.dumps(summary, indent=2, default=str))
    
    finally:
        # Stop monitoring
        monitoring_service.stop_monitoring()