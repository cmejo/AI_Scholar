"""Health monitoring and system diagnostics for RL components."""

import asyncio
import psutil
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict

from .logging_config import get_component_logger
from .error_handler import global_error_handler


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthMetric:
    """Individual health metric."""
    name: str
    value: float
    threshold_warning: float
    threshold_critical: float
    unit: str
    timestamp: datetime
    
    @property
    def status(self) -> HealthStatus:
        """Get health status based on thresholds."""
        if self.value >= self.threshold_critical:
            return HealthStatus.CRITICAL
        elif self.value >= self.threshold_warning:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY


@dataclass
class ComponentHealth:
    """Health status for a system component."""
    component_name: str
    status: HealthStatus
    metrics: List[HealthMetric]
    issues: List[str]
    last_check: datetime
    uptime: timedelta
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'component_name': self.component_name,
            'status': self.status.value,
            'metrics': [asdict(metric) for metric in self.metrics],
            'issues': self.issues,
            'last_check': self.last_check.isoformat(),
            'uptime': str(self.uptime)
        }


class HealthMonitor:
    """System health monitoring and diagnostics."""
    
    def __init__(self):
        self.logger = get_component_logger("health_monitor")
        self.component_health = {}
        self.health_checks = {}
        self.monitoring_active = False
        self.check_interval = 30  # seconds
        self.start_time = datetime.now()
    
    def register_health_check(self, component_name: str, 
                            check_function: Callable[[], Dict[str, Any]],
                            check_interval: int = None):
        """Register a health check function for a component."""
        self.health_checks[component_name] = {
            'function': check_function,
            'interval': check_interval or self.check_interval,
            'last_check': None
        }
        self.logger.info(f"Registered health check for {component_name}")
    
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self.monitoring_active:
            self.logger.warning("Health monitoring already active")
            return
        
        self.monitoring_active = True
        self.logger.info("Starting health monitoring")
        
        while self.monitoring_active:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error("Error in health monitoring loop", exception=e)
                await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """Stop health monitoring."""
        self.monitoring_active = False
        self.logger.info("Stopping health monitoring")
    
    async def _perform_health_checks(self):
        """Perform health checks for all registered components."""
        current_time = datetime.now()
        
        for component_name, check_info in self.health_checks.items():
            try:
                # Check if it's time to run this health check
                if (check_info['last_check'] is None or 
                    current_time - check_info['last_check'] >= 
                    timedelta(seconds=check_info['interval'])):
                    
                    # Run health check
                    if asyncio.iscoroutinefunction(check_info['function']):
                        health_data = await check_info['function']()
                    else:
                        health_data = check_info['function']()
                    
                    # Process health data
                    component_health = self._process_health_data(
                        component_name, health_data
                    )
                    
                    # Store health status
                    self.component_health[component_name] = component_health
                    check_info['last_check'] = current_time
                    
                    # Log health status
                    self._log_health_status(component_health)
                    
            except Exception as e:
                self.logger.error(
                    f"Health check failed for {component_name}",
                    exception=e
                )
                # Create error health status
                self.component_health[component_name] = ComponentHealth(
                    component_name=component_name,
                    status=HealthStatus.CRITICAL,
                    metrics=[],
                    issues=[f"Health check failed: {str(e)}"],
                    last_check=current_time,
                    uptime=current_time - self.start_time
                )
    
    def _process_health_data(self, component_name: str, 
                           health_data: Dict[str, Any]) -> ComponentHealth:
        """Process raw health data into ComponentHealth object."""
        metrics = []
        issues = []
        overall_status = HealthStatus.HEALTHY
        
        # Process metrics
        for metric_name, metric_data in health_data.get('metrics', {}).items():
            if isinstance(metric_data, dict):
                metric = HealthMetric(
                    name=metric_name,
                    value=metric_data.get('value', 0),
                    threshold_warning=metric_data.get('threshold_warning', float('inf')),
                    threshold_critical=metric_data.get('threshold_critical', float('inf')),
                    unit=metric_data.get('unit', ''),
                    timestamp=datetime.now()
                )
                metrics.append(metric)
                
                # Update overall status
                if metric.status == HealthStatus.CRITICAL:
                    overall_status = HealthStatus.CRITICAL
                elif metric.status == HealthStatus.WARNING and overall_status != HealthStatus.CRITICAL:
                    overall_status = HealthStatus.WARNING
        
        # Process issues
        issues.extend(health_data.get('issues', []))
        
        # Override status if issues are present
        if issues and overall_status == HealthStatus.HEALTHY:
            overall_status = HealthStatus.WARNING
        
        return ComponentHealth(
            component_name=component_name,
            status=overall_status,
            metrics=metrics,
            issues=issues,
            last_check=datetime.now(),
            uptime=datetime.now() - self.start_time
        )
    
    def _log_health_status(self, component_health: ComponentHealth):
        """Log component health status."""
        if component_health.status == HealthStatus.HEALTHY:
            self.logger.info(
                f"Component {component_health.component_name} is healthy",
                component=component_health.component_name,
                status=component_health.status.value,
                metrics_count=len(component_health.metrics)
            )
        elif component_health.status == HealthStatus.WARNING:
            self.logger.warning(
                f"Component {component_health.component_name} has warnings",
                component=component_health.component_name,
                status=component_health.status.value,
                issues=component_health.issues
            )
        else:  # CRITICAL
            self.logger.error(
                f"Component {component_health.component_name} is in critical state",
                component=component_health.component_name,
                status=component_health.status.value,
                issues=component_health.issues
            )
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        if not self.component_health:
            return {
                'overall_status': HealthStatus.UNKNOWN.value,
                'components': {},
                'summary': {
                    'healthy': 0,
                    'warning': 0,
                    'critical': 0,
                    'unknown': 0
                },
                'uptime': str(datetime.now() - self.start_time),
                'last_check': datetime.now().isoformat()
            }
        
        # Calculate overall status
        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.WARNING: 0,
            HealthStatus.CRITICAL: 0,
            HealthStatus.UNKNOWN: 0
        }
        
        components = {}
        for component_name, health in self.component_health.items():
            components[component_name] = health.to_dict()
            status_counts[health.status] += 1
        
        # Determine overall status
        if status_counts[HealthStatus.CRITICAL] > 0:
            overall_status = HealthStatus.CRITICAL
        elif status_counts[HealthStatus.WARNING] > 0:
            overall_status = HealthStatus.WARNING
        elif status_counts[HealthStatus.HEALTHY] > 0:
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNKNOWN
        
        return {
            'overall_status': overall_status.value,
            'components': components,
            'summary': {
                'healthy': status_counts[HealthStatus.HEALTHY],
                'warning': status_counts[HealthStatus.WARNING],
                'critical': status_counts[HealthStatus.CRITICAL],
                'unknown': status_counts[HealthStatus.UNKNOWN]
            },
            'uptime': str(datetime.now() - self.start_time),
            'last_check': datetime.now().isoformat()
        }
    
    def get_component_health(self, component_name: str) -> Optional[Dict[str, Any]]:
        """Get health status for a specific component."""
        if component_name in self.component_health:
            return self.component_health[component_name].to_dict()
        return None


# System resource monitoring functions
def get_system_resources() -> Dict[str, Any]:
    """Get system resource metrics."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'metrics': {
                'cpu_usage': {
                    'value': cpu_percent,
                    'threshold_warning': 80.0,
                    'threshold_critical': 95.0,
                    'unit': '%'
                },
                'memory_usage': {
                    'value': memory.percent,
                    'threshold_warning': 80.0,
                    'threshold_critical': 95.0,
                    'unit': '%'
                },
                'disk_usage': {
                    'value': disk.percent,
                    'threshold_warning': 85.0,
                    'threshold_critical': 95.0,
                    'unit': '%'
                }
            },
            'issues': []
        }
    except Exception as e:
        return {
            'metrics': {},
            'issues': [f"Failed to get system resources: {str(e)}"]
        }


def get_multimodal_health() -> Dict[str, Any]:
    """Get multi-modal processing component health."""
    issues = []
    metrics = {}
    
    try:
        # Check if required libraries are available
        try:
            import cv2
            import numpy as np
            metrics['opencv_available'] = {
                'value': 1.0,
                'threshold_warning': 0.5,
                'threshold_critical': 0.0,
                'unit': 'bool'
            }
        except ImportError:
            issues.append("OpenCV not available for image processing")
            metrics['opencv_available'] = {
                'value': 0.0,
                'threshold_warning': 0.5,
                'threshold_critical': 0.0,
                'unit': 'bool'
            }
        
        # Check processing queue size (mock for now)
        processing_queue_size = 0  # Would be actual queue size
        metrics['processing_queue_size'] = {
            'value': processing_queue_size,
            'threshold_warning': 100.0,
            'threshold_critical': 500.0,
            'unit': 'items'
        }
        
        return {
            'metrics': metrics,
            'issues': issues
        }
    except Exception as e:
        return {
            'metrics': {},
            'issues': [f"Multi-modal health check failed: {str(e)}"]
        }


def get_personalization_health() -> Dict[str, Any]:
    """Get personalization engine health."""
    issues = []
    metrics = {}
    
    try:
        # Check model loading status (mock for now)
        models_loaded = True  # Would check actual model status
        metrics['models_loaded'] = {
            'value': 1.0 if models_loaded else 0.0,
            'threshold_warning': 0.5,
            'threshold_critical': 0.0,
            'unit': 'bool'
        }
        
        # Check adaptation performance (mock for now)
        adaptation_latency = 0.1  # Would be actual latency
        metrics['adaptation_latency'] = {
            'value': adaptation_latency,
            'threshold_warning': 1.0,
            'threshold_critical': 5.0,
            'unit': 'seconds'
        }
        
        return {
            'metrics': metrics,
            'issues': issues
        }
    except Exception as e:
        return {
            'metrics': {},
            'issues': [f"Personalization health check failed: {str(e)}"]
        }


def get_research_assistant_health() -> Dict[str, Any]:
    """Get research assistant mode health."""
    issues = []
    metrics = {}
    
    try:
        # Check workflow optimization status (mock for now)
        optimization_active = True  # Would check actual status
        metrics['optimization_active'] = {
            'value': 1.0 if optimization_active else 0.0,
            'threshold_warning': 0.5,
            'threshold_critical': 0.0,
            'unit': 'bool'
        }
        
        # Check pattern learning performance (mock for now)
        pattern_learning_accuracy = 0.85  # Would be actual accuracy
        metrics['pattern_learning_accuracy'] = {
            'value': pattern_learning_accuracy,
            'threshold_warning': 0.7,
            'threshold_critical': 0.5,
            'unit': 'ratio'
        }
        
        return {
            'metrics': metrics,
            'issues': issues
        }
    except Exception as e:
        return {
            'metrics': {},
            'issues': [f"Research assistant health check failed: {str(e)}"]
        }


def get_error_handler_health() -> Dict[str, Any]:
    """Get error handler health."""
    try:
        error_stats = global_error_handler.get_error_statistics()
        issues = []
        
        # Check for high error rates
        if error_stats['total_errors'] > 1000:
            issues.append(f"High total error count: {error_stats['total_errors']}")
        
        # Check for error diversity
        if error_stats['unique_error_types'] > 50:
            issues.append(f"High error type diversity: {error_stats['unique_error_types']}")
        
        metrics = {
            'total_errors': {
                'value': error_stats['total_errors'],
                'threshold_warning': 500.0,
                'threshold_critical': 1000.0,
                'unit': 'count'
            },
            'unique_error_types': {
                'value': error_stats['unique_error_types'],
                'threshold_warning': 25.0,
                'threshold_critical': 50.0,
                'unit': 'count'
            }
        }
        
        return {
            'metrics': metrics,
            'issues': issues
        }
    except Exception as e:
        return {
            'metrics': {},
            'issues': [f"Error handler health check failed: {str(e)}"]
        }


# Global health monitor instance
global_health_monitor = HealthMonitor()


def setup_default_health_checks():
    """Set up default health checks for system components."""
    global_health_monitor.register_health_check("system_resources", get_system_resources, 30)
    global_health_monitor.register_health_check("multimodal", get_multimodal_health, 60)
    global_health_monitor.register_health_check("personalization", get_personalization_health, 60)
    global_health_monitor.register_health_check("research_assistant", get_research_assistant_health, 60)
    global_health_monitor.register_health_check("error_handler", get_error_handler_health, 120)


# Initialize default health checks
setup_default_health_checks()