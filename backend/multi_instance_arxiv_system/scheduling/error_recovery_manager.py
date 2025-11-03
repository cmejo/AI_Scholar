"""
Error Recovery Manager for automated scheduling system.

Provides automated error recovery and retry mechanisms for the multi-instance
ArXiv system, including intelligent retry strategies and error pattern analysis.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
import json
import traceback
from dataclasses import dataclass, field
from enum import Enum

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from ..shared.multi_instance_data_models import ProcessingResult, UpdateReport

logger = logging.getLogger(__name__)


class RecoveryStrategy(Enum):
    """Recovery strategy types."""
    IMMEDIATE_RETRY = "immediate_retry"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"
    SKIP_AND_CONTINUE = "skip_and_continue"
    ABORT_OPERATION = "abort_operation"


class ErrorSeverity(Enum):
    """Error severity levels for recovery decisions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RecoveryConfig:
    """Configuration for error recovery behavior."""
    max_retry_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 300.0
    exponential_base: float = 2.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout_minutes: int = 30
    enable_intelligent_retry: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'max_retry_attempts': self.max_retry_attempts,
            'base_delay_seconds': self.base_delay_seconds,
            'max_delay_seconds': self.max_delay_seconds,
            'exponential_base': self.exponential_base,
            'circuit_breaker_threshold': self.circuit_breaker_threshold,
            'circuit_breaker_timeout_minutes': self.circuit_breaker_timeout_minutes,
            'enable_intelligent_retry': self.enable_intelligent_retry
        }


@dataclass
class ErrorPattern:
    """Represents an error pattern for intelligent recovery."""
    error_type: str
    error_message_pattern: str
    severity: ErrorSeverity
    recommended_strategy: RecoveryStrategy
    recovery_actions: List[str] = field(default_factory=list)
    
    def matches(self, error: Exception) -> bool:
        """Check if this pattern matches the given error."""
        error_str = str(error).lower()
        error_type_str = type(error).__name__.lower()
        
        return (self.error_type.lower() in error_type_str or 
                self.error_message_pattern.lower() in error_str)


@dataclass
class RecoveryAttempt:
    """Record of a recovery attempt."""
    attempt_number: int
    strategy: RecoveryStrategy
    delay_seconds: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'attempt_number': self.attempt_number,
            'strategy': self.strategy.value,
            'delay_seconds': self.delay_seconds,
            'timestamp': self.timestamp.isoformat(),
            'success': self.success,
            'error_message': self.error_message
        }


@dataclass
class RecoveryResult:
    """Result of error recovery operation."""
    success: bool
    final_result: Any = None
    attempts: List[RecoveryAttempt] = field(default_factory=list)
    total_time_seconds: float = 0.0
    recovery_strategy_used: Optional[RecoveryStrategy] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'success': self.success,
            'final_result': str(self.final_result) if self.final_result else None,
            'attempts': [attempt.to_dict() for attempt in self.attempts],
            'total_time_seconds': self.total_time_seconds,
            'recovery_strategy_used': self.recovery_strategy_used.value if self.recovery_strategy_used else None
        }


class ErrorRecoveryManager:
    """Manages automated error recovery and retry mechanisms."""
    
    def __init__(self, config: Optional[RecoveryConfig] = None):
        """
        Initialize error recovery manager.
        
        Args:
            config: Recovery configuration, uses defaults if not provided
        """
        self.config = config or RecoveryConfig()
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.error_history: List[Dict[str, Any]] = []
        
        # Define common error patterns
        self.error_patterns = [
            # Network-related errors
            ErrorPattern(
                error_type="ConnectionError",
                error_message_pattern="connection",
                severity=ErrorSeverity.MEDIUM,
                recommended_strategy=RecoveryStrategy.EXPONENTIAL_BACKOFF,
                recovery_actions=["Check network connectivity", "Verify service availability"]
            ),
            ErrorPattern(
                error_type="TimeoutError",
                error_message_pattern="timeout",
                severity=ErrorSeverity.MEDIUM,
                recommended_strategy=RecoveryStrategy.EXPONENTIAL_BACKOFF,
                recovery_actions=["Increase timeout", "Check network latency"]
            ),
            
            # File system errors
            ErrorPattern(
                error_type="PermissionError",
                error_message_pattern="permission denied",
                severity=ErrorSeverity.HIGH,
                recommended_strategy=RecoveryStrategy.ABORT_OPERATION,
                recovery_actions=["Check file permissions", "Verify user privileges"]
            ),
            ErrorPattern(
                error_type="FileNotFoundError",
                error_message_pattern="no such file",
                severity=ErrorSeverity.MEDIUM,
                recommended_strategy=RecoveryStrategy.SKIP_AND_CONTINUE,
                recovery_actions=["Verify file path", "Check if file was moved"]
            ),
            ErrorPattern(
                error_type="OSError",
                error_message_pattern="no space left",
                severity=ErrorSeverity.CRITICAL,
                recommended_strategy=RecoveryStrategy.ABORT_OPERATION,
                recovery_actions=["Free disk space", "Clean up temporary files"]
            ),
            
            # Processing errors
            ErrorPattern(
                error_type="MemoryError",
                error_message_pattern="memory",
                severity=ErrorSeverity.HIGH,
                recommended_strategy=RecoveryStrategy.CIRCUIT_BREAKER,
                recovery_actions=["Reduce batch size", "Free memory", "Restart process"]
            ),
            ErrorPattern(
                error_type="ValueError",
                error_message_pattern="invalid",
                severity=ErrorSeverity.LOW,
                recommended_strategy=RecoveryStrategy.SKIP_AND_CONTINUE,
                recovery_actions=["Validate input data", "Check data format"]
            ),
            
            # API and service errors
            ErrorPattern(
                error_type="HTTPError",
                error_message_pattern="500",
                severity=ErrorSeverity.MEDIUM,
                recommended_strategy=RecoveryStrategy.EXPONENTIAL_BACKOFF,
                recovery_actions=["Check service status", "Wait for service recovery"]
            ),
            ErrorPattern(
                error_type="HTTPError",
                error_message_pattern="429",
                severity=ErrorSeverity.MEDIUM,
                recommended_strategy=RecoveryStrategy.LINEAR_BACKOFF,
                recovery_actions=["Reduce request rate", "Implement rate limiting"]
            )
        ]
        
        logger.info("ErrorRecoveryManager initialized")
    
    async def execute_with_recovery(self,
                                  operation: Callable,
                                  operation_name: str,
                                  *args,
                                  **kwargs) -> RecoveryResult:
        """
        Execute an operation with automatic error recovery.
        
        Args:
            operation: The operation to execute
            operation_name: Name of the operation for logging
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            RecoveryResult with execution results and recovery information
        """
        start_time = datetime.now()
        recovery_result = RecoveryResult(success=False)
        
        logger.info(f"Executing operation '{operation_name}' with recovery")
        
        for attempt in range(1, self.config.max_retry_attempts + 1):
            try:
                # Check circuit breaker
                if self._is_circuit_breaker_open(operation_name):
                    logger.warning(f"Circuit breaker open for '{operation_name}', skipping attempt")
                    break
                
                # Execute the operation
                logger.debug(f"Attempt {attempt} for operation '{operation_name}'")
                result = await operation(*args, **kwargs)
                
                # Success - record attempt and return
                recovery_attempt = RecoveryAttempt(
                    attempt_number=attempt,
                    strategy=RecoveryStrategy.IMMEDIATE_RETRY,
                    delay_seconds=0.0,
                    timestamp=datetime.now(),
                    success=True
                )
                recovery_result.attempts.append(recovery_attempt)
                recovery_result.success = True
                recovery_result.final_result = result
                
                # Reset circuit breaker on success
                self._reset_circuit_breaker(operation_name)
                
                logger.info(f"Operation '{operation_name}' succeeded on attempt {attempt}")
                break
                
            except Exception as e:
                logger.warning(f"Operation '{operation_name}' failed on attempt {attempt}: {e}")
                
                # Analyze error and determine recovery strategy
                error_pattern = self._analyze_error(e)
                strategy = error_pattern.recommended_strategy if error_pattern else RecoveryStrategy.EXPONENTIAL_BACKOFF
                
                # Record the failed attempt
                recovery_attempt = RecoveryAttempt(
                    attempt_number=attempt,
                    strategy=strategy,
                    delay_seconds=0.0,
                    timestamp=datetime.now(),
                    success=False,
                    error_message=str(e)
                )
                
                # Record error in history
                self._record_error(operation_name, e, error_pattern)
                
                # Check if we should abort immediately
                if strategy == RecoveryStrategy.ABORT_OPERATION:
                    recovery_result.attempts.append(recovery_attempt)
                    logger.error(f"Aborting operation '{operation_name}' due to critical error: {e}")
                    break
                
                # Check if this is the last attempt
                if attempt >= self.config.max_retry_attempts:
                    recovery_result.attempts.append(recovery_attempt)
                    logger.error(f"Operation '{operation_name}' failed after {attempt} attempts")
                    
                    # Update circuit breaker
                    self._update_circuit_breaker(operation_name)
                    break
                
                # Calculate delay and wait before retry
                delay = self._calculate_delay(strategy, attempt, error_pattern)
                recovery_attempt.delay_seconds = delay
                recovery_result.attempts.append(recovery_attempt)
                
                if delay > 0:
                    logger.info(f"Waiting {delay:.1f} seconds before retry {attempt + 1}")
                    await asyncio.sleep(delay)
        
        # Calculate total time and finalize result
        recovery_result.total_time_seconds = (datetime.now() - start_time).total_seconds()
        recovery_result.recovery_strategy_used = strategy if 'strategy' in locals() else None
        
        logger.info(f"Recovery completed for '{operation_name}': "
                   f"success={recovery_result.success}, "
                   f"attempts={len(recovery_result.attempts)}, "
                   f"time={recovery_result.total_time_seconds:.1f}s")
        
        return recovery_result
    
    def _analyze_error(self, error: Exception) -> Optional[ErrorPattern]:
        """Analyze an error and find matching pattern."""
        for pattern in self.error_patterns:
            if pattern.matches(error):
                logger.debug(f"Error matches pattern: {pattern.error_type}")
                return pattern
        
        logger.debug(f"No pattern found for error: {type(error).__name__}")
        return None
    
    def _calculate_delay(self, 
                        strategy: RecoveryStrategy, 
                        attempt: int, 
                        error_pattern: Optional[ErrorPattern]) -> float:
        """Calculate delay before retry based on strategy."""
        if strategy == RecoveryStrategy.IMMEDIATE_RETRY:
            return 0.0
        elif strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay_seconds * (self.config.exponential_base ** (attempt - 1))
            return min(delay, self.config.max_delay_seconds)
        elif strategy == RecoveryStrategy.LINEAR_BACKOFF:
            delay = self.config.base_delay_seconds * attempt
            return min(delay, self.config.max_delay_seconds)
        elif strategy == RecoveryStrategy.CIRCUIT_BREAKER:
            return self.config.base_delay_seconds * 2  # Short delay before circuit breaker check
        else:
            return self.config.base_delay_seconds
    
    def _is_circuit_breaker_open(self, operation_name: str) -> bool:
        """Check if circuit breaker is open for the given operation."""
        if operation_name not in self.circuit_breakers:
            return False
        
        breaker = self.circuit_breakers[operation_name]
        
        # Check if circuit breaker timeout has expired
        if breaker['opened_at']:
            timeout_minutes = self.config.circuit_breaker_timeout_minutes
            if datetime.now() - breaker['opened_at'] > timedelta(minutes=timeout_minutes):
                logger.info(f"Circuit breaker timeout expired for '{operation_name}', resetting")
                self._reset_circuit_breaker(operation_name)
                return False
        
        return breaker['is_open']
    
    def _update_circuit_breaker(self, operation_name: str) -> None:
        """Update circuit breaker state after failure."""
        if operation_name not in self.circuit_breakers:
            self.circuit_breakers[operation_name] = {
                'failure_count': 0,
                'is_open': False,
                'opened_at': None
            }
        
        breaker = self.circuit_breakers[operation_name]
        breaker['failure_count'] += 1
        
        if breaker['failure_count'] >= self.config.circuit_breaker_threshold:
            breaker['is_open'] = True
            breaker['opened_at'] = datetime.now()
            logger.warning(f"Circuit breaker opened for '{operation_name}' after {breaker['failure_count']} failures")
    
    def _reset_circuit_breaker(self, operation_name: str) -> None:
        """Reset circuit breaker after successful operation."""
        if operation_name in self.circuit_breakers:
            self.circuit_breakers[operation_name] = {
                'failure_count': 0,
                'is_open': False,
                'opened_at': None
            }
            logger.debug(f"Circuit breaker reset for '{operation_name}'")
    
    def _record_error(self, 
                     operation_name: str, 
                     error: Exception, 
                     error_pattern: Optional[ErrorPattern]) -> None:
        """Record error in history for analysis."""
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'operation_name': operation_name,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'stack_trace': traceback.format_exc(),
            'pattern_matched': error_pattern.error_type if error_pattern else None,
            'severity': error_pattern.severity.value if error_pattern else 'unknown'
        }
        
        self.error_history.append(error_record)
        
        # Keep only recent errors (last 1000)
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and patterns."""
        if not self.error_history:
            return {'total_errors': 0}
        
        # Analyze error patterns
        error_types = {}
        operations = {}
        severities = {}
        
        for error in self.error_history:
            # Count by error type
            error_type = error['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Count by operation
            operation = error['operation_name']
            operations[operation] = operations.get(operation, 0) + 1
            
            # Count by severity
            severity = error['severity']
            severities[severity] = severities.get(severity, 0) + 1
        
        # Calculate recent error rate (last hour)
        recent_errors = [
            error for error in self.error_history
            if datetime.fromisoformat(error['timestamp']) > datetime.now() - timedelta(hours=1)
        ]
        
        return {
            'total_errors': len(self.error_history),
            'recent_errors_last_hour': len(recent_errors),
            'error_types': error_types,
            'operations': operations,
            'severities': severities,
            'circuit_breakers': {
                name: {
                    'failure_count': breaker['failure_count'],
                    'is_open': breaker['is_open'],
                    'opened_at': breaker['opened_at'].isoformat() if breaker['opened_at'] else None
                }
                for name, breaker in self.circuit_breakers.items()
            }
        }
    
    def export_error_report(self, output_path: Path) -> bool:
        """Export comprehensive error report."""
        try:
            report = {
                'report_type': 'error_recovery_report',
                'generated_at': datetime.now().isoformat(),
                'config': self.config.to_dict(),
                'statistics': self.get_error_statistics(),
                'recent_errors': self.error_history[-50:],  # Last 50 errors
                'error_patterns': [
                    {
                        'error_type': pattern.error_type,
                        'severity': pattern.severity.value,
                        'strategy': pattern.recommended_strategy.value,
                        'actions': pattern.recovery_actions
                    }
                    for pattern in self.error_patterns
                ]
            }
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Error recovery report exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export error recovery report: {e}")
            return False
    
    def clear_error_history(self) -> None:
        """Clear error history and reset circuit breakers."""
        self.error_history.clear()
        self.circuit_breakers.clear()
        logger.info("Error history and circuit breakers cleared")
    
    def add_custom_error_pattern(self, pattern: ErrorPattern) -> None:
        """Add a custom error pattern for intelligent recovery."""
        self.error_patterns.append(pattern)
        logger.info(f"Added custom error pattern: {pattern.error_type}")
    
    def get_recovery_recommendations(self, operation_name: str) -> List[str]:
        """Get recovery recommendations for a specific operation."""
        recommendations = []
        
        # Check circuit breaker status
        if operation_name in self.circuit_breakers:
            breaker = self.circuit_breakers[operation_name]
            if breaker['is_open']:
                recommendations.append(f"Circuit breaker is open for '{operation_name}' - investigate root cause")
            elif breaker['failure_count'] > 0:
                recommendations.append(f"Operation '{operation_name}' has {breaker['failure_count']} recent failures")
        
        # Analyze recent errors for this operation
        recent_errors = [
            error for error in self.error_history
            if (error['operation_name'] == operation_name and 
                datetime.fromisoformat(error['timestamp']) > datetime.now() - timedelta(hours=24))
        ]
        
        if recent_errors:
            # Find most common error types
            error_counts = {}
            for error in recent_errors:
                error_type = error['error_type']
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
            
            most_common = max(error_counts.items(), key=lambda x: x[1])
            recommendations.append(f"Most common error in last 24h: {most_common[0]} ({most_common[1]} occurrences)")
            
            # Find matching patterns and their recommendations
            for error in recent_errors[-5:]:  # Last 5 errors
                for pattern in self.error_patterns:
                    if pattern.error_type.lower() in error['error_type'].lower():
                        recommendations.extend(pattern.recovery_actions)
                        break
        
        return list(set(recommendations))  # Remove duplicates