"""Advanced logging configuration for RL system components."""

import logging
import logging.handlers
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum

from ..exceptions.advanced_exceptions import RLSystemError


class LogLevel(Enum):
    """Log levels for different components."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ComponentLogger:
    """Specialized logger for RL system components."""
    
    def __init__(self, component_name: str, log_level: LogLevel = LogLevel.INFO):
        self.component_name = component_name
        self.logger = logging.getLogger(f"rl.{component_name}")
        self.logger.setLevel(getattr(logging, log_level.value))
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up logging handlers for the component."""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for component-specific logs
        log_dir = Path("backend/logs/rl")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{self.component_name}.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # JSON handler for structured logging
        json_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{self.component_name}_structured.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(json_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exception: Exception = None, **kwargs):
        """Log error message with context and exception details."""
        if exception:
            kwargs['exception_type'] = type(exception).__name__
            kwargs['exception_message'] = str(exception)
            if isinstance(exception, RLSystemError):
                kwargs.update(exception.context)
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, exception: Exception = None, **kwargs):
        """Log critical message with context and exception details."""
        if exception:
            kwargs['exception_type'] = type(exception).__name__
            kwargs['exception_message'] = str(exception)
            if isinstance(exception, RLSystemError):
                kwargs.update(exception.context)
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log message with additional context."""
        extra = {
            'component': self.component_name,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        self.logger.log(level, message, extra=extra)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'component': getattr(record, 'component', 'unknown'),
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra context if available
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info', 'component', 'timestamp']:
                log_entry[key] = value
        
        return json.dumps(log_entry)


class MultiModalLogger(ComponentLogger):
    """Specialized logger for multi-modal processing."""
    
    def __init__(self):
        super().__init__("multimodal", LogLevel.DEBUG)
    
    def log_visual_processing(self, operation: str, image_info: Dict[str, Any], 
                            success: bool = True, processing_time: float = None):
        """Log visual processing operations."""
        self.info(
            f"Visual processing: {operation}",
            operation=operation,
            success=success,
            processing_time=processing_time,
            **image_info
        )
    
    def log_feature_integration(self, text_features_count: int, visual_features_count: int,
                              integration_method: str, success: bool = True):
        """Log feature integration operations."""
        self.info(
            f"Feature integration: {integration_method}",
            text_features_count=text_features_count,
            visual_features_count=visual_features_count,
            integration_method=integration_method,
            success=success
        )
    
    def log_chart_analysis(self, chart_type: str, data_points_extracted: int,
                          confidence: float, success: bool = True):
        """Log chart analysis operations."""
        self.info(
            f"Chart analysis: {chart_type}",
            chart_type=chart_type,
            data_points_extracted=data_points_extracted,
            confidence=confidence,
            success=success
        )


class PersonalizationLogger(ComponentLogger):
    """Specialized logger for personalization system."""
    
    def __init__(self):
        super().__init__("personalization", LogLevel.DEBUG)
    
    def log_adaptation(self, user_id: str, algorithm: str, adaptation_type: str,
                      success: bool = True, improvement_score: float = None):
        """Log adaptation operations."""
        self.info(
            f"Adaptation: {algorithm} - {adaptation_type}",
            user_id=user_id,
            algorithm=algorithm,
            adaptation_type=adaptation_type,
            success=success,
            improvement_score=improvement_score
        )
    
    def log_behavior_prediction(self, user_id: str, prediction_type: str,
                              confidence: float, prediction_horizon: str):
        """Log behavior prediction operations."""
        self.info(
            f"Behavior prediction: {prediction_type}",
            user_id=user_id,
            prediction_type=prediction_type,
            confidence=confidence,
            prediction_horizon=prediction_horizon
        )
    
    def log_preference_learning(self, user_id: str, learning_method: str,
                              preferences_updated: int, learning_rate: float):
        """Log preference learning operations."""
        self.info(
            f"Preference learning: {learning_method}",
            user_id=user_id,
            learning_method=learning_method,
            preferences_updated=preferences_updated,
            learning_rate=learning_rate
        )


class ResearchAssistantLogger(ComponentLogger):
    """Specialized logger for research assistant mode."""
    
    def __init__(self):
        super().__init__("research_assistant", LogLevel.DEBUG)
    
    def log_workflow_optimization(self, workflow_id: str, optimization_type: str,
                                efficiency_improvement: float, success: bool = True):
        """Log workflow optimization operations."""
        self.info(
            f"Workflow optimization: {optimization_type}",
            workflow_id=workflow_id,
            optimization_type=optimization_type,
            efficiency_improvement=efficiency_improvement,
            success=success
        )
    
    def log_pattern_learning(self, pattern_type: str, patterns_learned: int,
                           confidence: float, domain: str):
        """Log pattern learning operations."""
        self.info(
            f"Pattern learning: {pattern_type}",
            pattern_type=pattern_type,
            patterns_learned=patterns_learned,
            confidence=confidence,
            domain=domain
        )
    
    def log_workflow_analysis(self, workflow_id: str, analysis_type: str,
                            bottlenecks_found: int, recommendations_generated: int):
        """Log workflow analysis operations."""
        self.info(
            f"Workflow analysis: {analysis_type}",
            workflow_id=workflow_id,
            analysis_type=analysis_type,
            bottlenecks_found=bottlenecks_found,
            recommendations_generated=recommendations_generated
        )


class PerformanceLogger(ComponentLogger):
    """Specialized logger for performance monitoring."""
    
    def __init__(self):
        super().__init__("performance", LogLevel.INFO)
    
    def log_processing_time(self, operation: str, component: str, 
                          processing_time: float, input_size: int = None):
        """Log processing time metrics."""
        self.info(
            f"Performance: {component} - {operation}",
            operation=operation,
            component=component,
            processing_time=processing_time,
            input_size=input_size
        )
    
    def log_memory_usage(self, component: str, operation: str,
                        memory_before: float, memory_after: float):
        """Log memory usage metrics."""
        memory_delta = memory_after - memory_before
        self.info(
            f"Memory usage: {component} - {operation}",
            component=component,
            operation=operation,
            memory_before=memory_before,
            memory_after=memory_after,
            memory_delta=memory_delta
        )
    
    def log_throughput(self, component: str, operation: str,
                      items_processed: int, time_elapsed: float):
        """Log throughput metrics."""
        throughput = items_processed / time_elapsed if time_elapsed > 0 else 0
        self.info(
            f"Throughput: {component} - {operation}",
            component=component,
            operation=operation,
            items_processed=items_processed,
            time_elapsed=time_elapsed,
            throughput=throughput
        )


class ErrorLogger(ComponentLogger):
    """Specialized logger for error tracking and analysis."""
    
    def __init__(self):
        super().__init__("errors", LogLevel.WARNING)
    
    def log_error_recovery(self, error_type: str, recovery_strategy: str,
                          recovery_success: bool, recovery_time: float = None):
        """Log error recovery operations."""
        self.info(
            f"Error recovery: {error_type}",
            error_type=error_type,
            recovery_strategy=recovery_strategy,
            recovery_success=recovery_success,
            recovery_time=recovery_time
        )
    
    def log_error_pattern(self, error_pattern: str, frequency: int,
                         components_affected: List[str], severity: str):
        """Log error pattern analysis."""
        self.warning(
            f"Error pattern detected: {error_pattern}",
            error_pattern=error_pattern,
            frequency=frequency,
            components_affected=components_affected,
            severity=severity
        )
    
    def log_system_health(self, component: str, health_status: str,
                         health_score: float, issues: List[str] = None):
        """Log system health status."""
        level = logging.INFO if health_status == "healthy" else logging.WARNING
        self._log_with_context(
            level,
            f"System health: {component} - {health_status}",
            component=component,
            health_status=health_status,
            health_score=health_score,
            issues=issues or []
        )


# Global logger instances
multimodal_logger = MultiModalLogger()
personalization_logger = PersonalizationLogger()
research_assistant_logger = ResearchAssistantLogger()
performance_logger = PerformanceLogger()
error_logger = ErrorLogger()


def get_component_logger(component_name: str) -> ComponentLogger:
    """Get or create a logger for a specific component."""
    logger_map = {
        "multimodal": multimodal_logger,
        "personalization": personalization_logger,
        "research_assistant": research_assistant_logger,
        "performance": performance_logger,
        "errors": error_logger
    }
    
    if component_name in logger_map:
        return logger_map[component_name]
    
    return ComponentLogger(component_name)


def setup_logging(log_level: LogLevel = LogLevel.INFO, 
                 enable_structured_logging: bool = True):
    """Set up global logging configuration."""
    # Create logs directory
    log_dir = Path("backend/logs/rl")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger("rl")
    root_logger.setLevel(getattr(logging, log_level.value))
    
    # Prevent duplicate handlers
    if not root_logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # Main log file
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "rl_system.log",
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10
        )
        file_handler.setLevel(getattr(logging, log_level.value))
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        if enable_structured_logging:
            # Structured logging file
            json_handler = logging.handlers.RotatingFileHandler(
                log_dir / "rl_system_structured.log",
                maxBytes=50*1024*1024,  # 50MB
                backupCount=10
            )
            json_handler.setLevel(logging.INFO)
            json_handler.setFormatter(StructuredFormatter())
            root_logger.addHandler(json_handler)


def log_system_startup(components: List[str], startup_time: float):
    """Log system startup information."""
    logger = get_component_logger("system")
    logger.info(
        "RL system startup completed",
        components=components,
        startup_time=startup_time,
        startup_timestamp=datetime.now().isoformat()
    )


def log_system_shutdown(shutdown_reason: str, cleanup_time: float):
    """Log system shutdown information."""
    logger = get_component_logger("system")
    logger.info(
        "RL system shutdown initiated",
        shutdown_reason=shutdown_reason,
        cleanup_time=cleanup_time,
        shutdown_timestamp=datetime.now().isoformat()
    )