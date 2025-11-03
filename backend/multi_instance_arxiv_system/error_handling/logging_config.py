"""
Logging Configuration for AI Scholar Error Handling.

Provides centralized logging configuration with:
- Structured logging for error analysis
- File rotation and retention
- Performance monitoring
- Error aggregation and alerting
"""

import logging
import logging.handlers
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import traceback


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log data
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from the record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                extra_fields[key] = value
        
        if extra_fields:
            log_data['extra'] = extra_fields
        
        return json.dumps(log_data, default=str)


class AIScholarLoggerConfig:
    """Configuration manager for AI Scholar logging."""
    
    def __init__(self, 
                 log_dir: Path,
                 instance_name: str = "ai_scholar",
                 log_level: str = "INFO"):
        """
        Initialize logging configuration.
        
        Args:
            log_dir: Directory to store log files
            instance_name: Name of the scholar instance
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_dir = Path(log_dir)
        self.instance_name = instance_name
        self.log_level = getattr(logging, log_level.upper())
        
        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Log file paths
        self.main_log_file = self.log_dir / f"{instance_name}_main.log"
        self.error_log_file = self.log_dir / f"{instance_name}_errors.log"
        self.structured_log_file = self.log_dir / f"{instance_name}_structured.jsonl"
        
        # Configure loggers
        self._setup_loggers()
    
    def _setup_loggers(self) -> None:
        """Setup all loggers with appropriate handlers."""
        # Main application logger
        self.main_logger = logging.getLogger(f"ai_scholar.{self.instance_name}")
        self.main_logger.setLevel(self.log_level)
        self.main_logger.handlers.clear()
        
        # Error-specific logger
        self.error_logger = logging.getLogger(f"ai_scholar.{self.instance_name}.errors")
        self.error_logger.setLevel(logging.WARNING)
        self.error_logger.handlers.clear()
        
        # Structured logger for analysis
        self.structured_logger = logging.getLogger(f"ai_scholar.{self.instance_name}.structured")
        self.structured_logger.setLevel(logging.INFO)
        self.structured_logger.handlers.clear()
        
        # Setup handlers
        self._setup_main_handler()
        self._setup_error_handler()
        self._setup_structured_handler()
        self._setup_console_handler()
    
    def _setup_main_handler(self) -> None:
        """Setup main log file handler with rotation."""
        handler = logging.handlers.RotatingFileHandler(
            self.main_log_file,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=5,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.main_logger.addHandler(handler)
    
    def _setup_error_handler(self) -> None:
        """Setup error-specific log file handler."""
        handler = logging.handlers.RotatingFileHandler(
            self.error_log_file,
            maxBytes=20 * 1024 * 1024,  # 20MB
            backupCount=10,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\n'
            '%(pathname)s\n'
            '%(exc_text)s\n' if '%(exc_text)s' else ''
        )
        handler.setFormatter(formatter)
        
        self.error_logger.addHandler(handler)
    
    def _setup_structured_handler(self) -> None:
        """Setup structured JSON log handler."""
        handler = logging.handlers.RotatingFileHandler(
            self.structured_log_file,
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=3,
            encoding='utf-8'
        )
        
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)
        
        self.structured_logger.addHandler(handler)
    
    def _setup_console_handler(self) -> None:
        """Setup console handler for immediate feedback."""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add to main logger only
        self.main_logger.addHandler(handler)
    
    def get_logger(self, name: str = "") -> logging.Logger:
        """Get a logger instance."""
        if name:
            logger_name = f"ai_scholar.{self.instance_name}.{name}"
        else:
            logger_name = f"ai_scholar.{self.instance_name}"
        
        logger = logging.getLogger(logger_name)
        logger.setLevel(self.log_level)
        
        # Inherit handlers from main logger if not already set
        if not logger.handlers:
            for handler in self.main_logger.handlers:
                logger.addHandler(handler)
        
        return logger
    
    def log_error_with_context(self, 
                             error: Exception,
                             context: Dict[str, Any],
                             operation: str = "unknown") -> None:
        """Log error with structured context."""
        error_data = {
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'instance_name': self.instance_name,
            'timestamp': datetime.now().isoformat()
        }
        
        # Log to error logger
        self.error_logger.error(
            f"Operation '{operation}' failed: {error}",
            extra=error_data,
            exc_info=True
        )
        
        # Log to structured logger
        self.structured_logger.error(
            f"Structured error log for operation '{operation}'",
            extra=error_data
        )
    
    def log_performance_metric(self, 
                             operation: str,
                             duration_seconds: float,
                             success: bool,
                             additional_metrics: Optional[Dict[str, Any]] = None) -> None:
        """Log performance metrics."""
        metrics = {
            'metric_type': 'performance',
            'operation': operation,
            'duration_seconds': duration_seconds,
            'success': success,
            'instance_name': self.instance_name,
            'timestamp': datetime.now().isoformat()
        }
        
        if additional_metrics:
            metrics.update(additional_metrics)
        
        self.structured_logger.info(
            f"Performance metric for '{operation}': {duration_seconds:.2f}s",
            extra=metrics
        )
    
    def log_processing_progress(self,
                              operation: str,
                              current: int,
                              total: int,
                              additional_info: Optional[Dict[str, Any]] = None) -> None:
        """Log processing progress."""
        progress_data = {
            'metric_type': 'progress',
            'operation': operation,
            'current': current,
            'total': total,
            'percentage': (current / total * 100) if total > 0 else 0,
            'instance_name': self.instance_name,
            'timestamp': datetime.now().isoformat()
        }
        
        if additional_info:
            progress_data.update(additional_info)
        
        self.structured_logger.info(
            f"Progress for '{operation}': {current}/{total} ({progress_data['percentage']:.1f}%)",
            extra=progress_data
        )
    
    def create_operation_logger(self, operation_name: str) -> 'OperationLogger':
        """Create a context manager for operation logging."""
        return OperationLogger(self, operation_name)
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get logging statistics."""
        stats = {
            'instance_name': self.instance_name,
            'log_directory': str(self.log_dir),
            'log_files': {
                'main_log': {
                    'path': str(self.main_log_file),
                    'exists': self.main_log_file.exists(),
                    'size_mb': self.main_log_file.stat().st_size / (1024 * 1024) if self.main_log_file.exists() else 0
                },
                'error_log': {
                    'path': str(self.error_log_file),
                    'exists': self.error_log_file.exists(),
                    'size_mb': self.error_log_file.stat().st_size / (1024 * 1024) if self.error_log_file.exists() else 0
                },
                'structured_log': {
                    'path': str(self.structured_log_file),
                    'exists': self.structured_log_file.exists(),
                    'size_mb': self.structured_log_file.stat().st_size / (1024 * 1024) if self.structured_log_file.exists() else 0
                }
            },
            'log_level': logging.getLevelName(self.log_level),
            'loggers_configured': [
                f"ai_scholar.{self.instance_name}",
                f"ai_scholar.{self.instance_name}.errors",
                f"ai_scholar.{self.instance_name}.structured"
            ]
        }
        
        return stats


class OperationLogger:
    """Context manager for operation logging with automatic timing."""
    
    def __init__(self, config: AIScholarLoggerConfig, operation_name: str):
        """
        Initialize operation logger.
        
        Args:
            config: Logging configuration instance
            operation_name: Name of the operation being logged
        """
        self.config = config
        self.operation_name = operation_name
        self.logger = config.get_logger(f"operations.{operation_name}")
        self.start_time: Optional[datetime] = None
        self.success = False
        self.error: Optional[Exception] = None
        self.context: Dict[str, Any] = {}
    
    def __enter__(self) -> 'OperationLogger':
        """Enter the operation context."""
        self.start_time = datetime.now()
        self.logger.info(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the operation context."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds() if self.start_time else 0
        
        if exc_type is None:
            self.success = True
            self.logger.info(f"Operation completed successfully: {self.operation_name} ({duration:.2f}s)")
        else:
            self.success = False
            self.error = exc_val
            self.logger.error(f"Operation failed: {self.operation_name} ({duration:.2f}s)", exc_info=True)
            
            # Log error with context
            self.config.log_error_with_context(
                exc_val,
                {**self.context, 'duration_seconds': duration},
                self.operation_name
            )
        
        # Log performance metrics
        self.config.log_performance_metric(
            self.operation_name,
            duration,
            self.success,
            self.context
        )
    
    def add_context(self, **kwargs) -> None:
        """Add context information to the operation."""
        self.context.update(kwargs)
    
    def log_progress(self, current: int, total: int, **kwargs) -> None:
        """Log progress within the operation."""
        self.config.log_processing_progress(
            self.operation_name,
            current,
            total,
            {**self.context, **kwargs}
        )
    
    def log_info(self, message: str, **kwargs) -> None:
        """Log info message within the operation."""
        self.logger.info(message, extra={**self.context, **kwargs})
    
    def log_warning(self, message: str, **kwargs) -> None:
        """Log warning message within the operation."""
        self.logger.warning(message, extra={**self.context, **kwargs})
    
    def log_error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log error message within the operation."""
        if error:
            self.config.log_error_with_context(
                error,
                {**self.context, **kwargs},
                f"{self.operation_name}.{message}"
            )
        else:
            self.logger.error(message, extra={**self.context, **kwargs})


def setup_ai_scholar_logging(log_dir: Path, 
                           instance_name: str = "ai_scholar",
                           log_level: str = "INFO") -> AIScholarLoggerConfig:
    """
    Setup comprehensive logging for AI Scholar instance.
    
    Args:
        log_dir: Directory to store log files
        instance_name: Name of the scholar instance
        log_level: Logging level
        
    Returns:
        Configured AIScholarLoggerConfig instance
    """
    config = AIScholarLoggerConfig(log_dir, instance_name, log_level)
    
    # Set as default for the module
    logging.getLogger("ai_scholar").setLevel(getattr(logging, log_level.upper()))
    
    return config


# Example usage and testing
if __name__ == "__main__":
    import tempfile
    import time
    
    # Test logging configuration
    with tempfile.TemporaryDirectory() as temp_dir:
        log_dir = Path(temp_dir) / "logs"
        
        # Setup logging
        config = setup_ai_scholar_logging(log_dir, "test_instance", "DEBUG")
        
        # Get logger
        logger = config.get_logger("test")
        
        # Test basic logging
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        
        # Test error logging with context
        try:
            raise ValueError("Test exception")
        except Exception as e:
            config.log_error_with_context(
                e,
                {'test_context': 'example', 'value': 42},
                'test_operation'
            )
        
        # Test operation logger
        with config.create_operation_logger("test_operation") as op_logger:
            op_logger.add_context(test_param="value")
            op_logger.log_info("Operation in progress")
            op_logger.log_progress(50, 100, items_processed=50)
            time.sleep(0.1)  # Simulate work
        
        # Test performance logging
        config.log_performance_metric(
            "test_metric",
            1.5,
            True,
            {'items_processed': 100, 'memory_used_mb': 256}
        )
        
        # Get stats
        stats = config.get_log_stats()
        print("Logging stats:", json.dumps(stats, indent=2))
        
        print("Logging configuration test completed successfully!")