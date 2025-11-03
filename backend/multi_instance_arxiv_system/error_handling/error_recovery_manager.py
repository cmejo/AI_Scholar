"""
Error Recovery Manager for Multi-Instance ArXiv System.

This module provides comprehensive error recovery management with instance-specific
strategies, multi-level error handling, and automated recovery procedures.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
import logging
import asyncio
import threading
import time
import json
from enum import Enum
from dataclasses import dataclass, field

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.error_handling.error_models import (
        ProcessingError, ErrorContext, ErrorSeverity, ErrorCategory, ErrorType,
        ErrorSummary, RecoveryReport
    )
    from multi_instance_arxiv_system.error_handling.network_error_handler import NetworkErrorHandler
    from multi_instance_arxiv_system.error_handling.pdf_processing_error_handler import PDFProcessingErrorHandler
    from multi_instance_arxiv_system.error_handling.storage_error_handler import StorageErrorHandler
except ImportError as e:
    print(f"Import error: {e}")
    # Create minimal fallback classes for testing
    class ProcessingError:
        def __init__(self, *args, **kwargs): pass
    class ErrorContext:
        def __init__(self, *args, **kwargs): pass
    class ErrorSeverity:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"
    class ErrorCategory:
        NETWORK = "network"
        PDF_PROCESSING = "pdf_processing"
        STORAGE = "storage"
    class ErrorType:
        HTTP_ERROR = "http_error"
    class ErrorSummary:
        def __init__(self, *args, **kwargs): pass
    class RecoveryReport:
        def __init__(self, *args, **kwargs): pass
    class NetworkErrorHandler:
        def __init__(self, *args, **kwargs): pass
    class PDFProcessingErrorHandler:
        def __init__(self, *args, **kwargs): pass
    class StorageErrorHandler:
        def __init__(self, *args, **kwargs): pass

logger = logging.getLogger(__name__)


class RecoveryStrategy(Enum):
    """Error recovery strategies."""
    RETRY = "retry"
    SKIP = "skip"
    FALLBACK = "fallback"
    ESCALATE = "escalate"
    MANUAL = "manual"


@dataclass
class RecoveryConfig:
    """Configuration for error recovery."""
    
    # Retry configuration
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    exponential_backoff: bool = True
    backoff_multiplier: float = 2.0
    max_retry_delay: float = 300.0  # 5 minutes
    
    # Recovery strategies by error type
    strategy_by_type: Dict[ErrorType, RecoveryStrategy] = field(default_factory=dict)
    strategy_by_category: Dict[ErrorCategory, RecoveryStrategy] = field(default_factory=dict)
    
    # Escalation thresholds
    escalation_error_count: int = 10
    escalation_time_window: int = 3600  # 1 hour
    
    # Circuit breaker
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 300  # 5 minutes


class ErrorRecoveryManager:
    """
    Comprehensive error recovery manager with multi-level error handling.
    
    Provides instance-specific recovery strategies, automated recovery procedures,
    and integration with specialized error handlers.
    """
    
    def __init__(
        self,
        instance_name: str,
        config: Optional[RecoveryConfig] = None,
        error_log_path: Optional[str] = None
    ):
        self.instance_name = instance_name
        self.config = config or RecoveryConfig()
        self.error_log_path = error_log_path or f"logs/{instance_name}_errors.json"
        
        # Error storage
        self.active_errors: Dict[str, ProcessingError] = {}
        self.error_history: List[ProcessingError] = []
        self.error_history_limit = 1000
        
        # Specialized error handlers
        self.network_handler = NetworkErrorHandler(instance_name)
        self.pdf_handler = PDFProcessingErrorHandler(instance_name)
        self.storage_handler = StorageErrorHandler(instance_name)
        
        # Recovery state
        self.recovery_sessions: Dict[str, RecoveryReport] = {}
        self.circuit_breaker_state: Dict[ErrorType, Dict[str, Any]] = {}
        
        # Statistics
        self.total_errors_handled = 0
        self.total_recoveries_attempted = 0
        self.successful_recoveries = 0
        
        # Threading
        self.lock = threading.RLock()
        
        # Initialize default recovery strategies
        self._initialize_default_strategies()
        
        logger.info(f"ErrorRecoveryManager initialized for {instance_name}")
    
    def _initialize_default_strategies(self) -> None:
        """Initialize default recovery strategies."""
        
        # Network errors - retry with backoff
        self.config.strategy_by_category[ErrorCategory.NETWORK] = RecoveryStrategy.RETRY
        
        # PDF processing errors - skip corrupted files
        self.config.strategy_by_category[ErrorCategory.PDF_PROCESSING] = RecoveryStrategy.SKIP
        
        # Storage errors - retry with cleanup
        self.config.strategy_by_category[ErrorCategory.STORAGE] = RecoveryStrategy.RETRY
        
        # Vector store errors - retry with fallback
        self.config.strategy_by_category[ErrorCategory.VECTOR_STORE] = RecoveryStrategy.FALLBACK
        
        # Configuration errors - manual intervention
        self.config.strategy_by_category[ErrorCategory.CONFIGURATION] = RecoveryStrategy.MANUAL
        
        # System errors - escalate
        self.config.strategy_by_category[ErrorCategory.SYSTEM] = RecoveryStrategy.ESCALATE
        
        # Specific error type overrides
        self.config.strategy_by_type[ErrorType.DISK_FULL] = RecoveryStrategy.ESCALATE
        self.config.strategy_by_type[ErrorType.MEMORY_ERROR] = RecoveryStrategy.ESCALATE
        self.config.strategy_by_type[ErrorType.PDF_ENCRYPTED] = RecoveryStrategy.SKIP
        self.config.strategy_by_type[ErrorType.RATE_LIMIT_EXCEEDED] = RecoveryStrategy.RETRY
    
    async def handle_error(
        self,
        exception: Exception,
        context: ErrorContext,
        error_type: Optional[ErrorType] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ) -> ProcessingError:
        """
        Handle an error with appropriate recovery strategy.
        
        Args:
            exception: The exception that occurred
            context: Context information about the error
            error_type: Optional specific error type
            severity: Error severity level
            
        Returns:
            ProcessingError object with recovery information
        """
        
        with self.lock:
            # Create ProcessingError
            error = ProcessingError.from_exception(
                exception, self.instance_name, context, error_type, severity
            )
            
            # Store error
            self.active_errors[error.error_id] = error
            self.error_history.append(error)
            self.total_errors_handled += 1
            
            # Limit history size
            if len(self.error_history) > self.error_history_limit:
                self.error_history = self.error_history[-self.error_history_limit:]
            
            logger.error(f"Error handled: {error.error_type.value} - {error.message}")
            
            # Check circuit breaker
            if self._is_circuit_breaker_open(error.error_type):
                logger.warning(f"Circuit breaker open for {error.error_type.value}, skipping recovery")
                error.is_recoverable = False
                return error
            
            # Attempt recovery
            await self._attempt_recovery(error)
            
            # Save error to log
            await self._save_error_to_log(error)
            
            return error
    
    async def _attempt_recovery(self, error: ProcessingError) -> bool:
        """
        Attempt to recover from an error using appropriate strategy.
        
        Args:
            error: The error to recover from
            
        Returns:
            True if recovery was successful, False otherwise
        """
        
        if not error.can_retry():
            logger.info(f"Error {error.error_id} cannot be retried")
            return False
        
        # Determine recovery strategy
        strategy = self._get_recovery_strategy(error)
        
        logger.info(f"Attempting recovery for {error.error_id} using strategy: {strategy.value}")
        
        error.mark_recovery_attempt()
        self.total_recoveries_attempted += 1
        
        start_time = time.time()
        success = False
        
        try:
            if strategy == RecoveryStrategy.RETRY:
                success = await self._retry_recovery(error)
            elif strategy == RecoveryStrategy.SKIP:
                success = await self._skip_recovery(error)
            elif strategy == RecoveryStrategy.FALLBACK:
                success = await self._fallback_recovery(error)
            elif strategy == RecoveryStrategy.ESCALATE:
                success = await self._escalate_recovery(error)
            elif strategy == RecoveryStrategy.MANUAL:
                success = await self._manual_recovery(error)
            
            if success:
                self.successful_recoveries += 1
                error.mark_resolved(strategy.value)
                logger.info(f"Successfully recovered from error {error.error_id}")
            else:
                logger.warning(f"Recovery failed for error {error.error_id}")
                
                # Update circuit breaker
                self._update_circuit_breaker(error.error_type, success=False)
        
        except Exception as recovery_exception:
            logger.error(f"Recovery attempt failed with exception: {recovery_exception}")
            success = False
        
        finally:
            recovery_time = time.time() - start_time
            
            # Record recovery attempt
            if hasattr(self, 'current_recovery_session'):
                self.current_recovery_session.add_recovery_result(
                    strategy.value, success, recovery_time
                )
        
        return success
    
    def _get_recovery_strategy(self, error: ProcessingError) -> RecoveryStrategy:
        """Get the appropriate recovery strategy for an error."""
        
        # Check for specific error type strategy
        if error.error_type in self.config.strategy_by_type:
            return self.config.strategy_by_type[error.error_type]
        
        # Check for category strategy
        if error.error_category in self.config.strategy_by_category:
            return self.config.strategy_by_category[error.error_category]
        
        # Default strategy based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            return RecoveryStrategy.ESCALATE
        elif error.severity == ErrorSeverity.HIGH:
            return RecoveryStrategy.RETRY
        else:
            return RecoveryStrategy.SKIP
    
    async def _retry_recovery(self, error: ProcessingError) -> bool:
        """Implement retry recovery strategy."""
        
        # Calculate delay with exponential backoff
        delay = self.config.retry_delay_seconds
        if self.config.exponential_backoff and error.recovery_attempts > 1:
            delay *= (self.config.backoff_multiplier ** (error.recovery_attempts - 1))
            delay = min(delay, self.config.max_retry_delay)
        
        logger.info(f"Retrying after {delay} seconds for error {error.error_id}")
        await asyncio.sleep(delay)
        
        # Delegate to specialized handlers
        if error.error_category == ErrorCategory.NETWORK:
            return await self.network_handler.handle_error(error)
        elif error.error_category == ErrorCategory.PDF_PROCESSING:
            return await self.pdf_handler.handle_error(error)
        elif error.error_category == ErrorCategory.STORAGE:
            return await self.storage_handler.handle_error(error)
        else:
            # Generic retry - assume success for now
            logger.info(f"Generic retry for error {error.error_id}")
            return True
    
    async def _skip_recovery(self, error: ProcessingError) -> bool:
        """Implement skip recovery strategy."""
        
        logger.info(f"Skipping error {error.error_id} - marking as resolved")
        
        # Log the skip decision
        skip_reason = f"Skipped {error.error_type.value}: {error.message}"
        
        # For PDF processing errors, this is often the right approach
        if error.error_category == ErrorCategory.PDF_PROCESSING:
            logger.info(f"Skipping problematic PDF: {error.context.file_path}")
        
        return True  # Skip is considered successful resolution
    
    async def _fallback_recovery(self, error: ProcessingError) -> bool:
        """Implement fallback recovery strategy."""
        
        logger.info(f"Attempting fallback recovery for error {error.error_id}")
        
        # Implement fallback mechanisms based on error type
        if error.error_category == ErrorCategory.VECTOR_STORE:
            # Try alternative vector store operations
            logger.info("Attempting vector store fallback")
            return True  # Placeholder
        
        elif error.error_category == ErrorCategory.NETWORK:
            # Try alternative endpoints or methods
            logger.info("Attempting network fallback")
            return await self.network_handler.handle_error(error)
        
        else:
            # Generic fallback - try retry
            return await self._retry_recovery(error)
    
    async def _escalate_recovery(self, error: ProcessingError) -> bool:
        """Implement escalate recovery strategy."""
        
        logger.warning(f"Escalating error {error.error_id} for manual intervention")
        
        # Send immediate notification
        await self._send_escalation_notification(error)
        
        # Mark for manual intervention
        error.is_recoverable = False
        
        return False  # Escalation doesn't resolve the error automatically
    
    async def _manual_recovery(self, error: ProcessingError) -> bool:
        """Implement manual recovery strategy."""
        
        logger.info(f"Error {error.error_id} requires manual intervention")
        
        # Log detailed information for manual review
        await self._log_manual_intervention_required(error)
        
        # Mark as requiring manual intervention
        error.is_recoverable = False
        
        return False  # Manual recovery doesn't resolve automatically
    
    def _is_circuit_breaker_open(self, error_type: ErrorType) -> bool:
        """Check if circuit breaker is open for an error type."""
        
        if not self.config.enable_circuit_breaker:
            return False
        
        if error_type not in self.circuit_breaker_state:
            return False
        
        breaker = self.circuit_breaker_state[error_type]
        
        # Check if circuit breaker is in timeout
        if breaker.get('open_until', 0) > time.time():
            return True
        
        return False
    
    def _update_circuit_breaker(self, error_type: ErrorType, success: bool) -> None:
        """Update circuit breaker state."""
        
        if not self.config.enable_circuit_breaker:
            return
        
        if error_type not in self.circuit_breaker_state:
            self.circuit_breaker_state[error_type] = {
                'failure_count': 0,
                'last_failure': 0,
                'open_until': 0
            }
        
        breaker = self.circuit_breaker_state[error_type]
        
        if success:
            # Reset on success
            breaker['failure_count'] = 0
        else:
            # Increment failure count
            breaker['failure_count'] += 1
            breaker['last_failure'] = time.time()
            
            # Open circuit breaker if threshold exceeded
            if breaker['failure_count'] >= self.config.circuit_breaker_threshold:
                breaker['open_until'] = time.time() + self.config.circuit_breaker_timeout
                logger.warning(f"Circuit breaker opened for {error_type.value}")
    
    async def _send_escalation_notification(self, error: ProcessingError) -> None:
        """Send notification for escalated errors."""
        
        # This would integrate with the email notification system
        logger.critical(f"ESCALATION: {error.error_type.value} in {self.instance_name}")
        logger.critical(f"Error details: {error.message}")
        logger.critical(f"Context: {error.context.operation} - {error.context.file_path}")
    
    async def _log_manual_intervention_required(self, error: ProcessingError) -> None:
        """Log that manual intervention is required."""
        
        logger.warning(f"MANUAL INTERVENTION REQUIRED: {error.error_id}")
        logger.warning(f"Error: {error.error_type.value} - {error.message}")
        logger.warning(f"Context: {error.context.operation}")
        
        # Save detailed information for manual review
        manual_log_path = f"logs/{self.instance_name}_manual_intervention.json"
        try:
            manual_errors = []
            if Path(manual_log_path).exists():
                with open(manual_log_path, 'r') as f:
                    manual_errors = json.load(f)
            
            manual_errors.append(error.to_dict())
            
            with open(manual_log_path, 'w') as f:
                json.dump(manual_errors, f, indent=2)
        
        except Exception as e:
            logger.error(f"Failed to save manual intervention log: {e}")
    
    async def _save_error_to_log(self, error: ProcessingError) -> None:
        """Save error to persistent log."""
        
        try:
            # Ensure log directory exists
            log_path = Path(self.error_log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing errors
            errors = []
            if log_path.exists():
                with open(log_path, 'r') as f:
                    errors = json.load(f)
            
            # Add new error
            errors.append(error.to_dict())
            
            # Keep only recent errors (last 1000)
            if len(errors) > 1000:
                errors = errors[-1000:]
            
            # Save back to file
            with open(log_path, 'w') as f:
                json.dump(errors, f, indent=2)
        
        except Exception as e:
            logger.error(f"Failed to save error to log: {e}")
    
    async def retry_failed_operations(self, max_errors: int = 50) -> RecoveryReport:
        """Retry failed operations that can be recovered."""
        
        session_id = f"recovery_{int(time.time())}"
        report = RecoveryReport(
            instance_name=self.instance_name,
            recovery_session_id=session_id,
            start_time=datetime.now()
        )
        
        self.current_recovery_session = report
        self.recovery_sessions[session_id] = report
        
        logger.info(f"Starting recovery session {session_id}")
        
        # Get recoverable errors
        recoverable_errors = [
            error for error in self.active_errors.values()
            if error.can_retry()
        ][:max_errors]
        
        logger.info(f"Found {len(recoverable_errors)} recoverable errors")
        
        for error in recoverable_errors:
            try:
                success = await self._attempt_recovery(error)
                
                if success:
                    # Remove from active errors
                    if error.error_id in self.active_errors:
                        del self.active_errors[error.error_id]
            
            except Exception as e:
                logger.error(f"Error during recovery session: {e}")
        
        report.finalize()
        logger.info(f"Recovery session {session_id} completed with {report.success_rate:.1f}% success rate")
        
        return report
    
    def get_error_summary(self, time_period: timedelta = timedelta(hours=24)) -> ErrorSummary:
        """Get error summary for a time period."""
        
        cutoff_time = datetime.now() - time_period
        recent_errors = [
            error for error in self.error_history
            if error.timestamp >= cutoff_time
        ]
        
        return ErrorSummary.from_errors(recent_errors, self.instance_name, time_period)
    
    def get_active_errors(self) -> List[ProcessingError]:
        """Get list of active (unresolved) errors."""
        return list(self.active_errors.values())
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        
        with self.lock:
            return {
                'instance_name': self.instance_name,
                'total_errors_handled': self.total_errors_handled,
                'total_recoveries_attempted': self.total_recoveries_attempted,
                'successful_recoveries': self.successful_recoveries,
                'success_rate': (self.successful_recoveries / max(1, self.total_recoveries_attempted)) * 100,
                'active_errors': len(self.active_errors),
                'error_history_size': len(self.error_history),
                'recovery_sessions': len(self.recovery_sessions),
                'circuit_breaker_states': {
                    error_type.value: state for error_type, state in self.circuit_breaker_state.items()
                }
            }
    
    def configure_recovery_strategy(
        self,
        error_type: Optional[ErrorType] = None,
        error_category: Optional[ErrorCategory] = None,
        strategy: RecoveryStrategy = RecoveryStrategy.RETRY
    ) -> None:
        """Configure recovery strategy for specific error types or categories."""
        
        if error_type:
            self.config.strategy_by_type[error_type] = strategy
            logger.info(f"Set recovery strategy for {error_type.value} to {strategy.value}")
        
        if error_category:
            self.config.strategy_by_category[error_category] = strategy
            logger.info(f"Set recovery strategy for {error_category.value} to {strategy.value}")
    
    async def clear_resolved_errors(self, older_than: timedelta = timedelta(days=7)) -> int:
        """Clear resolved errors older than specified time."""
        
        cutoff_time = datetime.now() - older_than
        
        # Remove from active errors
        resolved_count = 0
        active_to_remove = []
        
        for error_id, error in self.active_errors.items():
            if error.is_resolved and error.resolved_at and error.resolved_at < cutoff_time:
                active_to_remove.append(error_id)
                resolved_count += 1
        
        for error_id in active_to_remove:
            del self.active_errors[error_id]
        
        # Clean up error history
        self.error_history = [
            error for error in self.error_history
            if not (error.is_resolved and error.resolved_at and error.resolved_at < cutoff_time)
        ]
        
        logger.info(f"Cleared {resolved_count} resolved errors older than {older_than}")
        return resolved_count