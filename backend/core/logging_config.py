"""
Comprehensive logging configuration for service operations
"""
import logging
import logging.config
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class ServiceLogFormatter(logging.Formatter):
    """Custom formatter for service-related logs"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = datetime.utcnow()
    
    def format(self, record):
        # Add service-specific information to log record
        if not hasattr(record, 'service_name'):
            record.service_name = 'unknown'
        
        if not hasattr(record, 'operation'):
            record.operation = 'general'
        
        # Add timestamp since startup
        current_time = datetime.utcnow()
        uptime = (current_time - self.start_time).total_seconds()
        record.uptime = f"{uptime:.2f}s"
        
        return super().format(record)


class ServiceLogFilter(logging.Filter):
    """Filter for service-related logs"""
    
    def __init__(self, service_name: str = None):
        super().__init__()
        self.service_name = service_name
    
    def filter(self, record):
        # Only allow logs from specific service if specified
        if self.service_name:
            return getattr(record, 'service_name', None) == self.service_name
        return True


def setup_service_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True,
    service_name: Optional[str] = None
) -> None:
    """
    Set up comprehensive logging configuration for services
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        enable_console: Whether to enable console logging
        service_name: Optional service name for filtering
    """
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define formatters
    formatters = {
        'detailed': {
            '()': ServiceLogFormatter,
            'format': '[{asctime}] [{levelname:8}] [{name}] [{service_name}] [{operation}] [{uptime}] {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '[{levelname}] [{name}] {message}',
            'style': '{'
        },
        'json': {
            'format': '[{asctime}] {levelname} {name} {service_name} {operation} {uptime} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    }
    
    # Define handlers
    handlers = {}
    
    if enable_console:
        handlers['console'] = {
            'class': 'logging.StreamHandler',
            'level': log_level,
            'formatter': 'detailed',
            'stream': sys.stdout
        }
    
    if log_file:
        handlers['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'detailed',
            'filename': log_file,
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8'
        }
        
        # Separate error log file
        error_log_file = str(Path(log_file).with_suffix('.error.log'))
        handlers['error_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': error_log_file,
            'maxBytes': 10485760,  # 10MB
            'backupCount': 3,
            'encoding': 'utf8'
        }
    
    # Define filters
    filters = {}
    if service_name:
        filters['service_filter'] = {
            '()': ServiceLogFilter,
            'service_name': service_name
        }
    
    # Define loggers
    loggers = {
        'backend.core.service_manager': {
            'level': log_level,
            'handlers': list(handlers.keys()),
            'propagate': False
        },
        'backend.core.conditional_importer': {
            'level': log_level,
            'handlers': list(handlers.keys()),
            'propagate': False
        },
        'backend.services': {
            'level': log_level,
            'handlers': list(handlers.keys()),
            'propagate': False
        },
        'backend.api': {
            'level': log_level,
            'handlers': list(handlers.keys()),
            'propagate': False
        }
    }
    
    # Root logger configuration
    root_config = {
        'level': log_level,
        'handlers': list(handlers.keys())
    }
    
    # Complete logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': formatters,
        'handlers': handlers,
        'filters': filters,
        'loggers': loggers,
        'root': root_config
    }
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log the configuration setup
    logger = logging.getLogger(__name__)
    logger.info("Service logging configuration initialized", extra={
        'service_name': service_name or 'system',
        'operation': 'logging_setup'
    })


def get_service_logger(
    service_name: str, 
    operation: str = 'general'
) -> logging.LoggerAdapter:
    """
    Get a logger adapter for a specific service
    
    Args:
        service_name: Name of the service
        operation: Current operation being performed
        
    Returns:
        LoggerAdapter with service context
    """
    logger = logging.getLogger(f"backend.services.{service_name}")
    
    # Create adapter with service context
    adapter = logging.LoggerAdapter(logger, {
        'service_name': service_name,
        'operation': operation
    })
    
    return adapter


def log_service_operation(
    service_name: str, 
    operation: str, 
    level: str = 'INFO'
):
    """
    Decorator for logging service operations
    
    Args:
        service_name: Name of the service
        operation: Operation being performed
        level: Log level
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_service_logger(service_name, operation)
            
            try:
                logger.log(
                    getattr(logging, level.upper()),
                    f"Starting operation: {operation}"
                )
                
                result = func(*args, **kwargs)
                
                logger.log(
                    getattr(logging, level.upper()),
                    f"Completed operation: {operation}"
                )
                
                return result
                
            except Exception as e:
                logger.error(
                    f"Operation failed: {operation} - {str(e)}",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


class ServiceMetrics:
    """Simple metrics collection for service operations"""
    
    def __init__(self):
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(f"{__name__}.ServiceMetrics")
    
    def record_operation(
        self, 
        service_name: str, 
        operation: str, 
        duration: float, 
        success: bool = True
    ):
        """
        Record a service operation metric
        
        Args:
            service_name: Name of the service
            operation: Operation performed
            duration: Duration in seconds
            success: Whether operation was successful
        """
        if service_name not in self.metrics:
            self.metrics[service_name] = {
                'operations': {},
                'total_operations': 0,
                'total_failures': 0
            }
        
        service_metrics = self.metrics[service_name]
        
        if operation not in service_metrics['operations']:
            service_metrics['operations'][operation] = {
                'count': 0,
                'failures': 0,
                'total_duration': 0.0,
                'avg_duration': 0.0,
                'min_duration': float('inf'),
                'max_duration': 0.0
            }
        
        op_metrics = service_metrics['operations'][operation]
        
        # Update operation metrics
        op_metrics['count'] += 1
        op_metrics['total_duration'] += duration
        op_metrics['avg_duration'] = op_metrics['total_duration'] / op_metrics['count']
        op_metrics['min_duration'] = min(op_metrics['min_duration'], duration)
        op_metrics['max_duration'] = max(op_metrics['max_duration'], duration)
        
        if not success:
            op_metrics['failures'] += 1
            service_metrics['total_failures'] += 1
        
        service_metrics['total_operations'] += 1
        
        # Log metrics periodically
        if service_metrics['total_operations'] % 100 == 0:
            self.logger.info(
                f"Service metrics for {service_name}: "
                f"{service_metrics['total_operations']} operations, "
                f"{service_metrics['total_failures']} failures",
                extra={
                    'service_name': service_name,
                    'operation': 'metrics_report'
                }
            )
    
    def get_metrics(self, service_name: str = None) -> Dict[str, Any]:
        """
        Get metrics for a service or all services
        
        Args:
            service_name: Optional service name
            
        Returns:
            Dict containing metrics
        """
        if service_name:
            return self.metrics.get(service_name, {})
        return self.metrics


# Global metrics instance
service_metrics = ServiceMetrics()


def setup_default_logging():
    """Set up default logging configuration for the application"""
    setup_service_logging(
        log_level="INFO",
        log_file="logs/services.log",
        enable_console=True
    )