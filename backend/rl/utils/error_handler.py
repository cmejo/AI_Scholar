"""Comprehensive error handling utilities for RL system."""

import traceback
import functools
import asyncio
from typing import Dict, Any, Optional, Callable, Type, List, Union
from datetime import datetime, timedelta
from enum import Enum

from ..exceptions.advanced_exceptions import (
    RLSystemError, MultiModalProcessingError, PersonalizationError,
    ResearchAssistantError, ConfigurationError, IntegrationError
)
from .logging_config import get_component_logger, error_logger


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    """Error recovery strategies."""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ABORT = "abort"
    GRACEFUL_DEGRADATION = "graceful_degradation"


class ErrorHandler:
    """Centralized error handling and recovery system."""
    
    def __init__(self):
        self.error_counts = {}
        self.recovery_strategies = {}
        self.error_patterns = {}
        self.circuit_breakers = {}
        self.logger = error_logger
    
    def register_recovery_strategy(self, error_type: Type[Exception], 
                                 strategy: RecoveryStrategy,
                                 fallback_function: Optional[Callable] = None,
                                 max_retries: int = 3,
                                 retry_delay: float = 1.0):
        """Register a recovery strategy for a specific error type."""
        self.recovery_strategies[error_type] = {
            'strategy': strategy,
            'fallback_function': fallback_function,
            'max_retries': max_retries,
            'retry_delay': retry_delay
        }
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None,
                    component: str = None) -> Dict[str, Any]:
        """Handle an error with appropriate recovery strategy."""
        context = context or {}
        error_type = type(error)
        error_key = f"{component or 'unknown'}:{error_type.__name__}"
        
        # Track error occurrence
        self._track_error(error_key, error, context)
        
        # Log the error
        self.logger.error(
            f"Error in {component or 'unknown'}: {str(error)}",
            exception=error,
            component=component,
            **context
        )
        
        # Determine recovery strategy
        recovery_info = self._get_recovery_strategy(error_type)
        
        # Execute recovery
        recovery_result = self._execute_recovery(error, recovery_info, context)
        
        return {
            'error_handled': True,
            'recovery_strategy': recovery_info['strategy'].value,
            'recovery_success': recovery_result.get('success', False),
            'recovery_details': recovery_result
        }
    
    def _track_error(self, error_key: str, error: Exception, context: Dict[str, Any]):
        """Track error occurrence for pattern analysis."""
        if error_key not in self.error_counts:
            self.error_counts[error_key] = {
                'count': 0,
                'first_occurrence': datetime.now(),
                'last_occurrence': datetime.now(),
                'contexts': []
            }
        
        self.error_counts[error_key]['count'] += 1
        self.error_counts[error_key]['last_occurrence'] = datetime.now()
        self.error_counts[error_key]['contexts'].append({
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'error_message': str(error)
        })
        
        # Keep only last 10 contexts to prevent memory bloat
        if len(self.error_counts[error_key]['contexts']) > 10:
            self.error_counts[error_key]['contexts'] = \
                self.error_counts[error_key]['contexts'][-10:]
        
        # Check for error patterns
        self._analyze_error_patterns(error_key)
    
    def _get_recovery_strategy(self, error_type: Type[Exception]) -> Dict[str, Any]:
        """Get recovery strategy for error type."""
        # Check for exact match
        if error_type in self.recovery_strategies:
            return self.recovery_strategies[error_type]
        
        # Check for parent class matches
        for registered_type, strategy in self.recovery_strategies.items():
            if issubclass(error_type, registered_type):
                return strategy
        
        # Default strategy based on error type
        if issubclass(error_type, MultiModalProcessingError):
            return {
                'strategy': RecoveryStrategy.FALLBACK,
                'fallback_function': None,
                'max_retries': 2,
                'retry_delay': 0.5
            }
        elif issubclass(error_type, PersonalizationError):
            return {
                'strategy': RecoveryStrategy.GRACEFUL_DEGRADATION,
                'fallback_function': None,
                'max_retries': 1,
                'retry_delay': 0.1
            }
        elif issubclass(error_type, ResearchAssistantError):
            return {
                'strategy': RecoveryStrategy.RETRY,
                'fallback_function': None,
                'max_retries': 3,
                'retry_delay': 1.0
            }
        else:
            return {
                'strategy': RecoveryStrategy.ABORT,
                'fallback_function': None,
                'max_retries': 0,
                'retry_delay': 0.0
            }
    
    def _execute_recovery(self, error: Exception, recovery_info: Dict[str, Any],
                         context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the recovery strategy."""
        strategy = recovery_info['strategy']
        
        if strategy == RecoveryStrategy.RETRY:
            return self._retry_recovery(error, recovery_info, context)
        elif strategy == RecoveryStrategy.FALLBACK:
            return self._fallback_recovery(error, recovery_info, context)
        elif strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
            return self._graceful_degradation_recovery(error, recovery_info, context)
        elif strategy == RecoveryStrategy.SKIP:
            return self._skip_recovery(error, recovery_info, context)
        else:  # ABORT
            return self._abort_recovery(error, recovery_info, context)
    
    def _retry_recovery(self, error: Exception, recovery_info: Dict[str, Any],
                       context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute retry recovery strategy."""
        max_retries = recovery_info.get('max_retries', 3)
        retry_delay = recovery_info.get('retry_delay', 1.0)
        
        self.logger.info(
            f"Initiating retry recovery for {type(error).__name__}",
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        return {
            'success': False,  # Actual retry would be handled by decorator
            'strategy': 'retry',
            'max_retries': max_retries,
            'retry_delay': retry_delay,
            'message': f"Retry recovery configured for {type(error).__name__}"
        }
    
    def _fallback_recovery(self, error: Exception, recovery_info: Dict[str, Any],
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fallback recovery strategy."""
        fallback_function = recovery_info.get('fallback_function')
        
        if fallback_function:
            try:
                result = fallback_function(error, context)
                self.logger.info(
                    f"Fallback recovery successful for {type(error).__name__}",
                    fallback_result=str(result)
                )
                return {
                    'success': True,
                    'strategy': 'fallback',
                    'result': result,
                    'message': f"Fallback recovery successful for {type(error).__name__}"
                }
            except Exception as fallback_error:
                self.logger.error(
                    f"Fallback recovery failed for {type(error).__name__}",
                    exception=fallback_error
                )
                return {
                    'success': False,
                    'strategy': 'fallback',
                    'error': str(fallback_error),
                    'message': f"Fallback recovery failed for {type(error).__name__}"
                }
        else:
            return {
                'success': False,
                'strategy': 'fallback',
                'message': f"No fallback function configured for {type(error).__name__}"
            }
    
    def _graceful_degradation_recovery(self, error: Exception, recovery_info: Dict[str, Any],
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute graceful degradation recovery strategy."""
        self.logger.info(
            f"Graceful degradation recovery for {type(error).__name__}",
            context=context
        )
        
        return {
            'success': True,
            'strategy': 'graceful_degradation',
            'message': f"System continues with reduced functionality due to {type(error).__name__}"
        }
    
    def _skip_recovery(self, error: Exception, recovery_info: Dict[str, Any],
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute skip recovery strategy."""
        self.logger.info(
            f"Skip recovery for {type(error).__name__}",
            context=context
        )
        
        return {
            'success': True,
            'strategy': 'skip',
            'message': f"Operation skipped due to {type(error).__name__}"
        }
    
    def _abort_recovery(self, error: Exception, recovery_info: Dict[str, Any],
                       context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute abort recovery strategy."""
        self.logger.critical(
            f"Abort recovery for {type(error).__name__}",
            context=context
        )
        
        return {
            'success': False,
            'strategy': 'abort',
            'message': f"Operation aborted due to {type(error).__name__}"
        }
    
    def _analyze_error_patterns(self, error_key: str):
        """Analyze error patterns for proactive handling."""
        error_info = self.error_counts[error_key]
        
        # Check for high frequency errors
        if error_info['count'] > 10:
            time_window = datetime.now() - error_info['first_occurrence']
            if time_window < timedelta(minutes=10):
                self.logger.warning(
                    f"High frequency error pattern detected: {error_key}",
                    error_count=error_info['count'],
                    time_window=str(time_window),
                    error_pattern="high_frequency"
                )
        
        # Check for recurring errors
        if error_info['count'] > 5:
            recent_errors = [
                ctx for ctx in error_info['contexts']
                if datetime.fromisoformat(ctx['timestamp']) > 
                   datetime.now() - timedelta(minutes=5)
            ]
            if len(recent_errors) >= 3:
                self.logger.warning(
                    f"Recurring error pattern detected: {error_key}",
                    recent_error_count=len(recent_errors),
                    error_pattern="recurring"
                )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        stats = {
            'total_errors': sum(info['count'] for info in self.error_counts.values()),
            'unique_error_types': len(self.error_counts),
            'error_breakdown': {},
            'top_errors': []
        }
        
        # Error breakdown by type
        for error_key, info in self.error_counts.items():
            component, error_type = error_key.split(':', 1)
            if component not in stats['error_breakdown']:
                stats['error_breakdown'][component] = {}
            stats['error_breakdown'][component][error_type] = info['count']
        
        # Top errors by frequency
        sorted_errors = sorted(
            self.error_counts.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        stats['top_errors'] = [
            {
                'error_key': key,
                'count': info['count'],
                'first_occurrence': info['first_occurrence'].isoformat(),
                'last_occurrence': info['last_occurrence'].isoformat()
            }
            for key, info in sorted_errors[:10]
        ]
        
        return stats
    
    def reset_error_statistics(self):
        """Reset error statistics."""
        self.error_counts.clear()
        self.logger.info("Error statistics reset")


# Global error handler instance
global_error_handler = ErrorHandler()


def handle_errors(component: str = None, 
                 recovery_strategy: RecoveryStrategy = None,
                 fallback_function: Callable = None,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 log_errors: bool = True):
    """Decorator for automatic error handling."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    context = {
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys())
                    }
                    
                    result = global_error_handler.handle_error(
                        e, context, component or func.__module__
                    )
                    
                    # Handle retry strategy
                    if (recovery_strategy == RecoveryStrategy.RETRY or 
                        result.get('recovery_details', {}).get('strategy') == 'retry'):
                        
                        retries = 0
                        while retries < max_retries:
                            try:
                                import time
                                time.sleep(retry_delay)
                                return func(*args, **kwargs)
                            except Exception as retry_error:
                                retries += 1
                                if retries >= max_retries:
                                    raise retry_error
                    
                    # Handle fallback strategy
                    if fallback_function and (
                        recovery_strategy == RecoveryStrategy.FALLBACK or
                        result.get('recovery_details', {}).get('strategy') == 'fallback'
                    ):
                        return fallback_function(e, {'args': args, 'kwargs': kwargs})
                
                raise
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    context = {
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys())
                    }
                    
                    result = global_error_handler.handle_error(
                        e, context, component or func.__module__
                    )
                    
                    # Handle retry strategy
                    if (recovery_strategy == RecoveryStrategy.RETRY or 
                        result.get('recovery_details', {}).get('strategy') == 'retry'):
                        
                        retries = 0
                        while retries < max_retries:
                            try:
                                await asyncio.sleep(retry_delay)
                                return await func(*args, **kwargs)
                            except Exception as retry_error:
                                retries += 1
                                if retries >= max_retries:
                                    raise retry_error
                    
                    # Handle fallback strategy
                    if fallback_function and (
                        recovery_strategy == RecoveryStrategy.FALLBACK or
                        result.get('recovery_details', {}).get('strategy') == 'fallback'
                    ):
                        if asyncio.iscoroutinefunction(fallback_function):
                            return await fallback_function(e, {'args': args, 'kwargs': kwargs})
                        else:
                            return fallback_function(e, {'args': args, 'kwargs': kwargs})
                
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper
    return decorator


def setup_default_recovery_strategies():
    """Set up default recovery strategies for common error types."""
    # Multi-modal processing errors
    global_error_handler.register_recovery_strategy(
        MultiModalProcessingError,
        RecoveryStrategy.FALLBACK,
        max_retries=2,
        retry_delay=0.5
    )
    
    # Personalization errors
    global_error_handler.register_recovery_strategy(
        PersonalizationError,
        RecoveryStrategy.GRACEFUL_DEGRADATION,
        max_retries=1,
        retry_delay=0.1
    )
    
    # Research assistant errors
    global_error_handler.register_recovery_strategy(
        ResearchAssistantError,
        RecoveryStrategy.RETRY,
        max_retries=3,
        retry_delay=1.0
    )
    
    # Configuration errors
    global_error_handler.register_recovery_strategy(
        ConfigurationError,
        RecoveryStrategy.ABORT,
        max_retries=0
    )
    
    # Integration errors
    global_error_handler.register_recovery_strategy(
        IntegrationError,
        RecoveryStrategy.RETRY,
        max_retries=2,
        retry_delay=2.0
    )


# Initialize default recovery strategies
setup_default_recovery_strategies()