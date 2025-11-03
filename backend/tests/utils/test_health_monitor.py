"""Unit tests for health monitoring system."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from backend.rl.utils.health_monitor import (
    HealthStatus, HealthMetric, ComponentHealth, HealthMonitor,
    global_health_monitor, get_system_resources, get_multimodal_health,
    get_personalization_health, get_research_assistant_health,
    get_error_handler_health
)


class TestHealthMetric:
    """Test cases for HealthMetric class."""
    
    def test_health_metric_creation(self):
        """Test HealthMetric creation."""
        timestamp = datetime.now()
        metric = HealthMetric(
            name="cpu_usage",
            value=75.5,
            threshold_warning=80.0,
            threshold_critical=95.0,
            unit="%",
            timestamp=timestamp
        )
        
        assert metric.name == "cpu_usage"
        assert metric.value == 75.5
        assert metric.threshold_warning == 80.0
        assert metric.threshold_critical == 95.0
        assert metric.unit == "%"
        assert metric.timestamp == timestamp
    
    def test_health_metric_status_healthy(self):
        """Test HealthMetric status when healthy."""
        metric = HealthMetric(
            name="memory_usage",
            value=50.0,
            threshold_warning=80.0,
            threshold_critical=95.0,
            unit="%",
            timestamp=datetime.now()
        )
        
        assert metric.status == HealthStatus.HEALTHY
    
    def test_health_metric_status_warning(self):
        """Test HealthMetric status when in warning state."""
        metric = HealthMetric(
            name="memory_usage",
            value=85.0,
            threshold_warning=80.0,
            threshold_critical=95.0,
            unit="%",
            timestamp=datetime.now()
        )
        
        assert metric.status == HealthStatus.WARNING
    
    def test_health_metric_status_critical(self):
        """Test HealthMetric status when in critical state."""
        metric = HealthMetric(
            name="memory_usage",
            value=97.0,
            threshold_warning=80.0,
            threshold_critical=95.0,
            unit="%",
            timestamp=datetime.now()
        )
        
        assert metric.status == HealthStatus.CRITICAL
    
    def test_health_metric_status_boundary_conditions(self):
        """Test HealthMetric status at boundary conditions."""
        # Exactly at warning threshold
        metric = HealthMetric(
            name="test_metric",
            value=80.0,
            threshold_warning=80.0,
            threshold_critical=95.0,
            unit="%",
            timestamp=datetime.now()
        )
        assert metric.status == HealthStatus.WARNING
        
        # Exactly at critical threshold
        metric = HealthMetric(
            name="test_metric",
            value=95.0,
            threshold_warning=80.0,
            threshold_critical=95.0,
            unit="%",
            timestamp=datetime.now()
        )
        assert metric.status == HealthStatus.CRITICAL


class TestComponentHealth:
    """Test cases for ComponentHealth class."""
    
    def test_component_health_creation(self):
        """Test ComponentHealth creation."""
        timestamp = datetime.now()
        uptime = timedelta(hours=2, minutes=30)
        
        metrics = [
            HealthMetric("cpu", 50.0, 80.0, 95.0, "%", timestamp),
            HealthMetric("memory", 60.0, 80.0, 95.0, "%", timestamp)
        ]
        
        health = ComponentHealth(
            component_name="test_component",
            status=HealthStatus.HEALTHY,
            metrics=metrics,
            issues=[],
            last_check=timestamp,
            uptime=uptime
        )
        
        assert health.component_name == "test_component"
        assert health.status == HealthStatus.HEALTHY
        assert len(health.metrics) == 2
        assert health.issues == []
        assert health.last_check == timestamp
        assert health.uptime == uptime
    
    def test_component_health_to_dict(self):
        """Test ComponentHealth to_dict conversion."""
        timestamp = datetime.now()
        uptime = timedelta(hours=1)
        
        metric = HealthMetric("cpu", 50.0, 80.0, 95.0, "%", timestamp)
        health = ComponentHealth(
            component_name="test_component",
            status=HealthStatus.WARNING,
            metrics=[metric],
            issues=["Test issue"],
            last_check=timestamp,
            uptime=uptime
        )
        
        health_dict = health.to_dict()
        
        assert health_dict['component_name'] == "test_component"
        assert health_dict['status'] == "warning"
        assert len(health_dict['metrics']) == 1
        assert health_dict['issues'] == ["Test issue"]
        assert health_dict['last_check'] == timestamp.isoformat()
        assert health_dict['uptime'] == str(uptime)


class TestHealthMonitor:
    """Test cases for HealthMonitor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = HealthMonitor()
    
    def test_health_monitor_initialization(self):
        """Test HealthMonitor initialization."""
        assert self.monitor.component_health == {}
        assert self.monitor.health_checks == {}
        assert self.monitor.monitoring_active is False
        assert self.monitor.check_interval == 30
        assert isinstance(self.monitor.start_time, datetime)
    
    def test_register_health_check(self):
        """Test registering health check function."""
        check_function = Mock(return_value={'metrics': {}, 'issues': []})
        
        self.monitor.register_health_check(
            "test_component",
            check_function,
            check_interval=60
        )
        
        assert "test_component" in self.monitor.health_checks
        check_info = self.monitor.health_checks["test_component"]
        assert check_info['function'] == check_function
        assert check_info['interval'] == 60
        assert check_info['last_check'] is None
    
    def test_register_health_check_default_interval(self):
        """Test registering health check with default interval."""
        check_function = Mock()
        
        self.monitor.register_health_check("test_component", check_function)
        
        check_info = self.monitor.health_checks["test_component"]
        assert check_info['interval'] == self.monitor.check_interval
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        # Mock the health check loop to avoid infinite loop
        with patch.object(self.monitor, '_perform_health_checks', new_callable=AsyncMock) as mock_checks:
            # Start monitoring in background
            monitor_task = asyncio.create_task(self.monitor.start_monitoring())
            
            # Give it a moment to start
            await asyncio.sleep(0.1)
            assert self.monitor.monitoring_active is True
            
            # Stop monitoring
            self.monitor.stop_monitoring()
            assert self.monitor.monitoring_active is False
            
            # Cancel the task to clean up
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_perform_health_checks_sync_function(self):
        """Test performing health checks with synchronous function."""
        check_function = Mock(return_value={
            'metrics': {
                'cpu_usage': {
                    'value': 50.0,
                    'threshold_warning': 80.0,
                    'threshold_critical': 95.0,
                    'unit': '%'
                }
            },
            'issues': []
        })
        
        self.monitor.register_health_check("test_component", check_function, 1)
        
        await self.monitor._perform_health_checks()
        
        check_function.assert_called_once()
        assert "test_component" in self.monitor.component_health
        
        component_health = self.monitor.component_health["test_component"]
        assert component_health.component_name == "test_component"
        assert component_health.status == HealthStatus.HEALTHY
        assert len(component_health.metrics) == 1
        assert component_health.metrics[0].name == "cpu_usage"
        assert component_health.metrics[0].value == 50.0
    
    @pytest.mark.asyncio
    async def test_perform_health_checks_async_function(self):
        """Test performing health checks with asynchronous function."""
        async def async_check_function():
            return {
                'metrics': {
                    'memory_usage': {
                        'value': 85.0,
                        'threshold_warning': 80.0,
                        'threshold_critical': 95.0,
                        'unit': '%'
                    }
                },
                'issues': ['High memory usage']
            }
        
        self.monitor.register_health_check("async_component", async_check_function, 1)
        
        await self.monitor._perform_health_checks()
        
        assert "async_component" in self.monitor.component_health
        
        component_health = self.monitor.component_health["async_component"]
        assert component_health.component_name == "async_component"
        assert component_health.status == HealthStatus.WARNING
        assert len(component_health.metrics) == 1
        assert component_health.issues == ['High memory usage']
    
    @pytest.mark.asyncio
    async def test_perform_health_checks_with_exception(self):
        """Test performing health checks when function raises exception."""
        check_function = Mock(side_effect=Exception("Health check failed"))
        
        self.monitor.register_health_check("failing_component", check_function, 1)
        
        await self.monitor._perform_health_checks()
        
        assert "failing_component" in self.monitor.component_health
        
        component_health = self.monitor.component_health["failing_component"]
        assert component_health.status == HealthStatus.CRITICAL
        assert len(component_health.issues) == 1
        assert "Health check failed" in component_health.issues[0]
    
    def test_process_health_data_healthy(self):
        """Test processing health data for healthy component."""
        health_data = {
            'metrics': {
                'cpu_usage': {
                    'value': 50.0,
                    'threshold_warning': 80.0,
                    'threshold_critical': 95.0,
                    'unit': '%'
                },
                'memory_usage': {
                    'value': 60.0,
                    'threshold_warning': 80.0,
                    'threshold_critical': 95.0,
                    'unit': '%'
                }
            },
            'issues': []
        }
        
        component_health = self.monitor._process_health_data("test_component", health_data)
        
        assert component_health.component_name == "test_component"
        assert component_health.status == HealthStatus.HEALTHY
        assert len(component_health.metrics) == 2
        assert component_health.issues == []
    
    def test_process_health_data_warning(self):
        """Test processing health data for component in warning state."""
        health_data = {
            'metrics': {
                'cpu_usage': {
                    'value': 85.0,
                    'threshold_warning': 80.0,
                    'threshold_critical': 95.0,
                    'unit': '%'
                }
            },
            'issues': []
        }
        
        component_health = self.monitor._process_health_data("test_component", health_data)
        
        assert component_health.status == HealthStatus.WARNING
        assert component_health.metrics[0].status == HealthStatus.WARNING
    
    def test_process_health_data_critical(self):
        """Test processing health data for component in critical state."""
        health_data = {
            'metrics': {
                'disk_usage': {
                    'value': 97.0,
                    'threshold_warning': 85.0,
                    'threshold_critical': 95.0,
                    'unit': '%'
                }
            },
            'issues': []
        }
        
        component_health = self.monitor._process_health_data("test_component", health_data)
        
        assert component_health.status == HealthStatus.CRITICAL
        assert component_health.metrics[0].status == HealthStatus.CRITICAL
    
    def test_process_health_data_with_issues(self):
        """Test processing health data with issues."""
        health_data = {
            'metrics': {},
            'issues': ['Service unavailable', 'Connection timeout']
        }
        
        component_health = self.monitor._process_health_data("test_component", health_data)
        
        assert component_health.status == HealthStatus.WARNING
        assert component_health.issues == ['Service unavailable', 'Connection timeout']
    
    def test_get_system_health_no_components(self):
        """Test getting system health when no components are monitored."""
        system_health = self.monitor.get_system_health()
        
        assert system_health['overall_status'] == HealthStatus.UNKNOWN.value
        assert system_health['components'] == {}
        assert system_health['summary']['healthy'] == 0
        assert system_health['summary']['warning'] == 0
        assert system_health['summary']['critical'] == 0
        assert system_health['summary']['unknown'] == 0
    
    def test_get_system_health_with_components(self):
        """Test getting system health with monitored components."""
        # Add some mock component health data
        timestamp = datetime.now()
        uptime = timedelta(hours=1)
        
        self.monitor.component_health["healthy_component"] = ComponentHealth(
            component_name="healthy_component",
            status=HealthStatus.HEALTHY,
            metrics=[],
            issues=[],
            last_check=timestamp,
            uptime=uptime
        )
        
        self.monitor.component_health["warning_component"] = ComponentHealth(
            component_name="warning_component",
            status=HealthStatus.WARNING,
            metrics=[],
            issues=["Minor issue"],
            last_check=timestamp,
            uptime=uptime
        )
        
        self.monitor.component_health["critical_component"] = ComponentHealth(
            component_name="critical_component",
            status=HealthStatus.CRITICAL,
            metrics=[],
            issues=["Critical issue"],
            last_check=timestamp,
            uptime=uptime
        )
        
        system_health = self.monitor.get_system_health()
        
        assert system_health['overall_status'] == HealthStatus.CRITICAL.value
        assert len(system_health['components']) == 3
        assert system_health['summary']['healthy'] == 1
        assert system_health['summary']['warning'] == 1
        assert system_health['summary']['critical'] == 1
        assert system_health['summary']['unknown'] == 0
    
    def test_get_component_health_existing(self):
        """Test getting health for existing component."""
        timestamp = datetime.now()
        uptime = timedelta(hours=1)
        
        component_health = ComponentHealth(
            component_name="test_component",
            status=HealthStatus.HEALTHY,
            metrics=[],
            issues=[],
            last_check=timestamp,
            uptime=uptime
        )
        
        self.monitor.component_health["test_component"] = component_health
        
        result = self.monitor.get_component_health("test_component")
        
        assert result is not None
        assert result['component_name'] == "test_component"
        assert result['status'] == "healthy"
    
    def test_get_component_health_nonexistent(self):
        """Test getting health for non-existent component."""
        result = self.monitor.get_component_health("nonexistent_component")
        assert result is None


class TestHealthCheckFunctions:
    """Test cases for health check functions."""
    
    @patch('backend.rl.utils.health_monitor.psutil')
    def test_get_system_resources_success(self, mock_psutil):
        """Test successful system resource health check."""
        # Mock psutil functions
        mock_psutil.cpu_percent.return_value = 75.0
        
        mock_memory = Mock()
        mock_memory.percent = 60.0
        mock_psutil.virtual_memory.return_value = mock_memory
        
        mock_disk = Mock()
        mock_disk.percent = 45.0
        mock_psutil.disk_usage.return_value = mock_disk
        
        result = get_system_resources()
        
        assert 'metrics' in result
        assert 'issues' in result
        assert result['issues'] == []
        
        metrics = result['metrics']
        assert 'cpu_usage' in metrics
        assert 'memory_usage' in metrics
        assert 'disk_usage' in metrics
        
        assert metrics['cpu_usage']['value'] == 75.0
        assert metrics['memory_usage']['value'] == 60.0
        assert metrics['disk_usage']['value'] == 45.0
    
    @patch('backend.rl.utils.health_monitor.psutil')
    def test_get_system_resources_exception(self, mock_psutil):
        """Test system resource health check with exception."""
        mock_psutil.cpu_percent.side_effect = Exception("psutil error")
        
        result = get_system_resources()
        
        assert 'metrics' in result
        assert 'issues' in result
        assert len(result['issues']) == 1
        assert "Failed to get system resources" in result['issues'][0]
    
    def test_get_multimodal_health_success(self):
        """Test successful multimodal health check."""
        with patch('builtins.__import__') as mock_import:
            # Mock successful imports
            mock_import.return_value = Mock()
            
            result = get_multimodal_health()
            
            assert 'metrics' in result
            assert 'issues' in result
            
            metrics = result['metrics']
            assert 'opencv_available' in metrics
            assert 'processing_queue_size' in metrics
            
            assert metrics['opencv_available']['value'] == 1.0
    
    def test_get_multimodal_health_missing_opencv(self):
        """Test multimodal health check with missing OpenCV."""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'cv2'")):
            result = get_multimodal_health()
            
            assert 'metrics' in result
            assert 'issues' in result
            assert len(result['issues']) == 1
            assert "OpenCV not available" in result['issues'][0]
            
            metrics = result['metrics']
            assert metrics['opencv_available']['value'] == 0.0
    
    def test_get_personalization_health(self):
        """Test personalization health check."""
        result = get_personalization_health()
        
        assert 'metrics' in result
        assert 'issues' in result
        
        metrics = result['metrics']
        assert 'models_loaded' in metrics
        assert 'adaptation_latency' in metrics
        
        # Default mock values
        assert metrics['models_loaded']['value'] == 1.0
        assert metrics['adaptation_latency']['value'] == 0.1
    
    def test_get_research_assistant_health(self):
        """Test research assistant health check."""
        result = get_research_assistant_health()
        
        assert 'metrics' in result
        assert 'issues' in result
        
        metrics = result['metrics']
        assert 'optimization_active' in metrics
        assert 'pattern_learning_accuracy' in metrics
        
        # Default mock values
        assert metrics['optimization_active']['value'] == 1.0
        assert metrics['pattern_learning_accuracy']['value'] == 0.85
    
    @patch('backend.rl.utils.health_monitor.global_error_handler')
    def test_get_error_handler_health(self, mock_error_handler):
        """Test error handler health check."""
        mock_error_handler.get_error_statistics.return_value = {
            'total_errors': 100,
            'unique_error_types': 10
        }
        
        result = get_error_handler_health()
        
        assert 'metrics' in result
        assert 'issues' in result
        
        metrics = result['metrics']
        assert 'total_errors' in metrics
        assert 'unique_error_types' in metrics
        
        assert metrics['total_errors']['value'] == 100
        assert metrics['unique_error_types']['value'] == 10
    
    @patch('backend.rl.utils.health_monitor.global_error_handler')
    def test_get_error_handler_health_high_errors(self, mock_error_handler):
        """Test error handler health check with high error counts."""
        mock_error_handler.get_error_statistics.return_value = {
            'total_errors': 1500,
            'unique_error_types': 60
        }
        
        result = get_error_handler_health()
        
        assert len(result['issues']) == 2
        assert "High total error count" in result['issues'][0]
        assert "High error type diversity" in result['issues'][1]


class TestHealthMonitorIntegration:
    """Integration tests for health monitoring system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_health_monitoring(self):
        """Test complete health monitoring workflow."""
        monitor = HealthMonitor()
        
        # Register a simple health check
        def simple_health_check():
            return {
                'metrics': {
                    'test_metric': {
                        'value': 50.0,
                        'threshold_warning': 80.0,
                        'threshold_critical': 95.0,
                        'unit': '%'
                    }
                },
                'issues': []
            }
        
        monitor.register_health_check("test_component", simple_health_check, 1)
        
        # Perform health checks
        await monitor._perform_health_checks()
        
        # Verify results
        assert "test_component" in monitor.component_health
        
        system_health = monitor.get_system_health()
        assert system_health['overall_status'] == HealthStatus.HEALTHY.value
        assert system_health['summary']['healthy'] == 1
        
        component_health = monitor.get_component_health("test_component")
        assert component_health is not None
        assert component_health['status'] == "healthy"
    
    def test_global_health_monitor_usage(self):
        """Test using global health monitor instance."""
        # Should be able to register health checks on global instance
        def test_check():
            return {'metrics': {}, 'issues': []}
        
        global_health_monitor.register_health_check("global_test", test_check)
        
        assert "global_test" in global_health_monitor.health_checks


if __name__ == "__main__":
    pytest.main([__file__])