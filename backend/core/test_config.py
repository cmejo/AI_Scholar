"""
Test configuration management system.
"""
import os
import json
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class APITestConfig:
    """Configuration for API testing."""
    base_url: str = "http://localhost:8000"
    timeout_seconds: int = 30
    retry_attempts: int = 3
    auth_token: Optional[str] = None
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {"Content-Type": "application/json"}

@dataclass
class DatabaseTestConfig:
    """Configuration for database testing."""
    connection_timeout: int = 10
    query_timeout: int = 30
    test_database_name: str = "test_advanced_rag_db"
    cleanup_after_tests: bool = True
    performance_threshold_ms: int = 2000

@dataclass
class PerformanceTestConfig:
    """Configuration for performance testing."""
    load_test_duration: int = 60  # seconds
    concurrent_users: int = 10
    ramp_up_time: int = 10  # seconds
    response_time_threshold: float = 5.0  # seconds
    throughput_threshold: int = 100  # requests per second
    memory_threshold_mb: int = 1024
    cpu_threshold_percent: float = 80.0

@dataclass
class IntegrationTestConfig:
    """Configuration for integration testing."""
    test_data_path: str = "test_data"
    cleanup_test_data: bool = True
    mock_external_services: bool = True
    test_file_upload_size_mb: int = 10
    websocket_timeout: int = 30

@dataclass
class TestExecutionConfig:
    """Configuration for test execution."""
    parallel_execution: bool = True
    max_concurrent_tests: int = 10
    stop_on_first_failure: bool = False
    detailed_logging: bool = True
    generate_html_report: bool = True
    report_output_dir: str = "test_reports"

@dataclass
class NotificationConfig:
    """Configuration for test result notifications."""
    enabled: bool = False
    email_recipients: List[str] = None
    slack_webhook_url: Optional[str] = None
    notify_on_failure_only: bool = True
    
    def __post_init__(self):
        if self.email_recipients is None:
            self.email_recipients = []

@dataclass
class TestSuiteConfig:
    """Configuration for individual test suites."""
    api_tests: bool = True
    database_tests: bool = True
    integration_tests: bool = True
    performance_tests: bool = True
    security_tests: bool = False
    ui_tests: bool = False

class TestConfigManager:
    """Manages test configuration from multiple sources."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "test_config.yaml"
        self.config_dir = Path("config/testing")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Default configuration
        self.api_config = APITestConfig()
        self.database_config = DatabaseTestConfig()
        self.performance_config = PerformanceTestConfig()
        self.integration_config = IntegrationTestConfig()
        self.execution_config = TestExecutionConfig()
        self.notification_config = NotificationConfig()
        self.suite_config = TestSuiteConfig()
        
        # Load configuration from file and environment
        self.load_configuration()
    
    def load_configuration(self):
        """Load configuration from file and environment variables."""
        # Load from file
        config_path = self.config_dir / self.config_file
        if config_path.exists():
            self._load_from_file(config_path)
        
        # Override with environment variables
        self._load_from_environment()
    
    def _load_from_file(self, config_path: Path):
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            if not config_data:
                return
            
            # Update configurations
            if 'api' in config_data:
                self._update_config(self.api_config, config_data['api'])
            
            if 'database' in config_data:
                self._update_config(self.database_config, config_data['database'])
            
            if 'performance' in config_data:
                self._update_config(self.performance_config, config_data['performance'])
            
            if 'integration' in config_data:
                self._update_config(self.integration_config, config_data['integration'])
            
            if 'execution' in config_data:
                self._update_config(self.execution_config, config_data['execution'])
            
            if 'notifications' in config_data:
                self._update_config(self.notification_config, config_data['notifications'])
            
            if 'suites' in config_data:
                self._update_config(self.suite_config, config_data['suites'])
        
        except Exception as e:
            print(f"Warning: Failed to load configuration from {config_path}: {e}")
    
    def _load_from_environment(self):
        """Load configuration from environment variables."""
        # API configuration
        if os.getenv('TEST_API_BASE_URL'):
            self.api_config.base_url = os.getenv('TEST_API_BASE_URL')
        
        if os.getenv('TEST_API_TIMEOUT'):
            self.api_config.timeout_seconds = int(os.getenv('TEST_API_TIMEOUT'))
        
        if os.getenv('TEST_AUTH_TOKEN'):
            self.api_config.auth_token = os.getenv('TEST_AUTH_TOKEN')
        
        # Database configuration
        if os.getenv('TEST_DATABASE_NAME'):
            self.database_config.test_database_name = os.getenv('TEST_DATABASE_NAME')
        
        if os.getenv('TEST_DB_TIMEOUT'):
            self.database_config.connection_timeout = int(os.getenv('TEST_DB_TIMEOUT'))
        
        # Performance configuration
        if os.getenv('TEST_LOAD_DURATION'):
            self.performance_config.load_test_duration = int(os.getenv('TEST_LOAD_DURATION'))
        
        if os.getenv('TEST_CONCURRENT_USERS'):
            self.performance_config.concurrent_users = int(os.getenv('TEST_CONCURRENT_USERS'))
        
        # Execution configuration
        if os.getenv('TEST_PARALLEL_EXECUTION'):
            self.execution_config.parallel_execution = os.getenv('TEST_PARALLEL_EXECUTION').lower() == 'true'
        
        if os.getenv('TEST_MAX_CONCURRENT'):
            self.execution_config.max_concurrent_tests = int(os.getenv('TEST_MAX_CONCURRENT'))
        
        # Notification configuration
        if os.getenv('TEST_NOTIFICATIONS_ENABLED'):
            self.notification_config.enabled = os.getenv('TEST_NOTIFICATIONS_ENABLED').lower() == 'true'
        
        if os.getenv('TEST_SLACK_WEBHOOK'):
            self.notification_config.slack_webhook_url = os.getenv('TEST_SLACK_WEBHOOK')
        
        # Suite configuration
        if os.getenv('TEST_ENABLE_API_TESTS'):
            self.suite_config.api_tests = os.getenv('TEST_ENABLE_API_TESTS').lower() == 'true'
        
        if os.getenv('TEST_ENABLE_DB_TESTS'):
            self.suite_config.database_tests = os.getenv('TEST_ENABLE_DB_TESTS').lower() == 'true'
        
        if os.getenv('TEST_ENABLE_INTEGRATION_TESTS'):
            self.suite_config.integration_tests = os.getenv('TEST_ENABLE_INTEGRATION_TESTS').lower() == 'true'
        
        if os.getenv('TEST_ENABLE_PERFORMANCE_TESTS'):
            self.suite_config.performance_tests = os.getenv('TEST_ENABLE_PERFORMANCE_TESTS').lower() == 'true'
    
    def _update_config(self, config_obj, config_data: Dict[str, Any]):
        """Update configuration object with data from dictionary."""
        for key, value in config_data.items():
            if hasattr(config_obj, key):
                setattr(config_obj, key, value)
    
    def save_configuration(self):
        """Save current configuration to file."""
        config_data = {
            'api': asdict(self.api_config),
            'database': asdict(self.database_config),
            'performance': asdict(self.performance_config),
            'integration': asdict(self.integration_config),
            'execution': asdict(self.execution_config),
            'notifications': asdict(self.notification_config),
            'suites': asdict(self.suite_config)
        }
        
        config_path = self.config_dir / self.config_file
        try:
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            print(f"Configuration saved to {config_path}")
        except Exception as e:
            print(f"Failed to save configuration: {e}")
    
    def get_all_configs(self) -> Dict[str, Any]:
        """Get all configuration objects."""
        return {
            'api': self.api_config,
            'database': self.database_config,
            'performance': self.performance_config,
            'integration': self.integration_config,
            'execution': self.execution_config,
            'notifications': self.notification_config,
            'suites': self.suite_config
        }
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Validate API configuration
        if not self.api_config.base_url:
            issues.append("API base URL is required")
        
        if self.api_config.timeout_seconds <= 0:
            issues.append("API timeout must be positive")
        
        # Validate database configuration
        if self.database_config.connection_timeout <= 0:
            issues.append("Database connection timeout must be positive")
        
        # Validate performance configuration
        if self.performance_config.concurrent_users <= 0:
            issues.append("Concurrent users must be positive")
        
        if self.performance_config.load_test_duration <= 0:
            issues.append("Load test duration must be positive")
        
        # Validate execution configuration
        if self.execution_config.max_concurrent_tests <= 0:
            issues.append("Max concurrent tests must be positive")
        
        # Validate notification configuration
        if self.notification_config.enabled:
            if not self.notification_config.email_recipients and not self.notification_config.slack_webhook_url:
                issues.append("At least one notification method must be configured when notifications are enabled")
        
        return issues
    
    def create_default_config_file(self):
        """Create a default configuration file."""
        default_config = {
            'api': {
                'base_url': 'http://localhost:8000',
                'timeout_seconds': 30,
                'retry_attempts': 3,
                'headers': {
                    'Content-Type': 'application/json'
                }
            },
            'database': {
                'connection_timeout': 10,
                'query_timeout': 30,
                'test_database_name': 'test_advanced_rag_db',
                'cleanup_after_tests': True,
                'performance_threshold_ms': 2000
            },
            'performance': {
                'load_test_duration': 60,
                'concurrent_users': 10,
                'ramp_up_time': 10,
                'response_time_threshold': 5.0,
                'throughput_threshold': 100,
                'memory_threshold_mb': 1024,
                'cpu_threshold_percent': 80.0
            },
            'integration': {
                'test_data_path': 'test_data',
                'cleanup_test_data': True,
                'mock_external_services': True,
                'test_file_upload_size_mb': 10,
                'websocket_timeout': 30
            },
            'execution': {
                'parallel_execution': True,
                'max_concurrent_tests': 10,
                'stop_on_first_failure': False,
                'detailed_logging': True,
                'generate_html_report': True,
                'report_output_dir': 'test_reports'
            },
            'notifications': {
                'enabled': False,
                'email_recipients': [],
                'slack_webhook_url': None,
                'notify_on_failure_only': True
            },
            'suites': {
                'api_tests': True,
                'database_tests': True,
                'integration_tests': True,
                'performance_tests': True,
                'security_tests': False,
                'ui_tests': False
            }
        }
        
        config_path = self.config_dir / self.config_file
        try:
            with open(config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
            print(f"Default configuration created at {config_path}")
        except Exception as e:
            print(f"Failed to create default configuration: {e}")

# Global configuration manager
config_manager = TestConfigManager()

def get_test_config_manager() -> TestConfigManager:
    """Get the global test configuration manager."""
    return config_manager