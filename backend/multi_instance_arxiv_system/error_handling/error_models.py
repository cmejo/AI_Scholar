"""
Error models and data structures for the multi-instance ArXiv system.

This module defines the core error data models, severity levels, and categories
used throughout the error handling system.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import traceback
import json

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    NETWORK = "network"
    PDF_PROCESSING = "pdf_processing"
    STORAGE = "storage"
    VECTOR_STORE = "vector_store"
    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class ErrorType(Enum):
    """Specific error types."""
    # Network errors
    CONNECTION_TIMEOUT = "connection_timeout"
    CONNECTION_REFUSED = "connection_refused"
    DNS_RESOLUTION = "dns_resolution"
    HTTP_ERROR = "http_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    
    # PDF processing errors
    PDF_CORRUPT = "pdf_corrupt"
    PDF_ENCRYPTED = "pdf_encrypted"
    PDF_PARSING_FAILED = "pdf_parsing_failed"
    PDF_EXTRACTION_FAILED = "pdf_extraction_failed"
    
    # Storage errors
    DISK_FULL = "disk_full"
    PERMISSION_DENIED = "permission_denied"
    FILE_NOT_FOUND = "file_not_found"
    DIRECTORY_NOT_FOUND = "directory_not_found"
    IO_ERROR = "io_error"
    
    # Vector store errors
    COLLECTION_NOT_FOUND = "collection_not_found"
    EMBEDDING_FAILED = "embedding_failed"
    INDEX_CORRUPTION = "index_corruption"
    
    # Configuration errors
    CONFIG_MISSING = "config_missing"
    CONFIG_INVALID = "config_invalid"
    
    # System errors
    MEMORY_ERROR = "memory_error"
    CPU_OVERLOAD = "cpu_overload"
    PROCESS_KILLED = "process_killed"


@dataclass
class ErrorContext:
    """Context information for an error."""
    
    instance_name: str
    operation: str
    file_path: Optional[str] = None
    paper_id: Optional[str] = None
    url: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingError:
    """Comprehensive error information for processing operations."""
    
    error_id: str
    timestamp: datetime
    instance_name: str
    
    # Error classification
    error_type: ErrorType
    error_category: ErrorCategory
    severity: ErrorSeverity
    
    # Error details
    message: str
    exception_type: str
    stack_trace: Optional[str] = None
    
    # Context
    context: ErrorContext = field(default_factory=lambda: ErrorContext("", ""))
    
    # Recovery information
    is_recoverable: bool = True
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3
    last_recovery_attempt: Optional[datetime] = None
    
    # Resolution
    is_resolved: bool = False
    resolution_method: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        instance_name: str,
        context: ErrorContext,
        error_type: Optional[ErrorType] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ) -> 'ProcessingError':
        """Create ProcessingError from an exception."""
        
        error_id = f"{instance_name}_{int(datetime.now().timestamp())}_{id(exception)}"
        
        # Determine error type and category from exception
        if error_type is None:
            error_type, error_category = cls._classify_exception(exception)
        else:
            error_category = cls._get_category_for_type(error_type)
        
        return cls(
            error_id=error_id,
            timestamp=datetime.now(),
            instance_name=instance_name,
            error_type=error_type,
            error_category=error_category,
            severity=severity,
            message=str(exception),
            exception_type=type(exception).__name__,
            stack_trace=traceback.format_exc(),
            context=context
        )
    
    @staticmethod
    def _classify_exception(exception: Exception) -> tuple[ErrorType, ErrorCategory]:
        """Classify an exception into error type and category."""
        
        exception_name = type(exception).__name__.lower()
        exception_message = str(exception).lower()
        
        # Network errors
        if any(term in exception_name for term in ['connection', 'timeout', 'http', 'url']):
            if 'timeout' in exception_message:
                return ErrorType.CONNECTION_TIMEOUT, ErrorCategory.NETWORK
            elif 'refused' in exception_message:
                return ErrorType.CONNECTION_REFUSED, ErrorCategory.NETWORK
            elif any(code in exception_message for code in ['404', '500', '503']):
                return ErrorType.HTTP_ERROR, ErrorCategory.NETWORK
            else:
                return ErrorType.HTTP_ERROR, ErrorCategory.NETWORK
        
        # PDF processing errors
        elif any(term in exception_name for term in ['pdf', 'parsing', 'extraction']):
            if 'corrupt' in exception_message or 'invalid' in exception_message:
                return ErrorType.PDF_CORRUPT, ErrorCategory.PDF_PROCESSING
            elif 'encrypted' in exception_message:
                return ErrorType.PDF_ENCRYPTED, ErrorCategory.PDF_PROCESSING
            else:
                return ErrorType.PDF_PARSING_FAILED, ErrorCategory.PDF_PROCESSING
        
        # Storage errors
        elif any(term in exception_name for term in ['io', 'file', 'permission', 'disk']):
            if 'permission' in exception_message or 'denied' in exception_message:
                return ErrorType.PERMISSION_DENIED, ErrorCategory.STORAGE
            elif 'not found' in exception_message:
                return ErrorType.FILE_NOT_FOUND, ErrorCategory.STORAGE
            elif 'no space' in exception_message or 'disk full' in exception_message:
                return ErrorType.DISK_FULL, ErrorCategory.STORAGE
            else:
                return ErrorType.IO_ERROR, ErrorCategory.STORAGE
        
        # Memory errors
        elif 'memory' in exception_name:
            return ErrorType.MEMORY_ERROR, ErrorCategory.SYSTEM
        
        # Default
        else:
            return ErrorType.HTTP_ERROR, ErrorCategory.UNKNOWN
    
    @staticmethod
    def _get_category_for_type(error_type: ErrorType) -> ErrorCategory:
        """Get error category for a given error type."""
        
        type_to_category = {
            # Network
            ErrorType.CONNECTION_TIMEOUT: ErrorCategory.NETWORK,
            ErrorType.CONNECTION_REFUSED: ErrorCategory.NETWORK,
            ErrorType.DNS_RESOLUTION: ErrorCategory.NETWORK,
            ErrorType.HTTP_ERROR: ErrorCategory.NETWORK,
            ErrorType.RATE_LIMIT_EXCEEDED: ErrorCategory.NETWORK,
            
            # PDF Processing
            ErrorType.PDF_CORRUPT: ErrorCategory.PDF_PROCESSING,
            ErrorType.PDF_ENCRYPTED: ErrorCategory.PDF_PROCESSING,
            ErrorType.PDF_PARSING_FAILED: ErrorCategory.PDF_PROCESSING,
            ErrorType.PDF_EXTRACTION_FAILED: ErrorCategory.PDF_PROCESSING,
            
            # Storage
            ErrorType.DISK_FULL: ErrorCategory.STORAGE,
            ErrorType.PERMISSION_DENIED: ErrorCategory.STORAGE,
            ErrorType.FILE_NOT_FOUND: ErrorCategory.STORAGE,
            ErrorType.DIRECTORY_NOT_FOUND: ErrorCategory.STORAGE,
            ErrorType.IO_ERROR: ErrorCategory.STORAGE,
            
            # Vector Store
            ErrorType.COLLECTION_NOT_FOUND: ErrorCategory.VECTOR_STORE,
            ErrorType.EMBEDDING_FAILED: ErrorCategory.VECTOR_STORE,
            ErrorType.INDEX_CORRUPTION: ErrorCategory.VECTOR_STORE,
            
            # Configuration
            ErrorType.CONFIG_MISSING: ErrorCategory.CONFIGURATION,
            ErrorType.CONFIG_INVALID: ErrorCategory.CONFIGURATION,
            
            # System
            ErrorType.MEMORY_ERROR: ErrorCategory.SYSTEM,
            ErrorType.CPU_OVERLOAD: ErrorCategory.SYSTEM,
            ErrorType.PROCESS_KILLED: ErrorCategory.SYSTEM,
        }
        
        return type_to_category.get(error_type, ErrorCategory.UNKNOWN)
    
    def can_retry(self) -> bool:
        """Check if this error can be retried."""
        return (self.is_recoverable and 
                self.recovery_attempts < self.max_recovery_attempts and
                not self.is_resolved)
    
    def mark_recovery_attempt(self) -> None:
        """Mark a recovery attempt."""
        self.recovery_attempts += 1
        self.last_recovery_attempt = datetime.now()
    
    def mark_resolved(self, resolution_method: str) -> None:
        """Mark the error as resolved."""
        self.is_resolved = True
        self.resolution_method = resolution_method
        self.resolved_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            'error_id': self.error_id,
            'timestamp': self.timestamp.isoformat(),
            'instance_name': self.instance_name,
            'error_type': self.error_type.value,
            'error_category': self.error_category.value,
            'severity': self.severity.value,
            'message': self.message,
            'exception_type': self.exception_type,
            'stack_trace': self.stack_trace,
            'context': {
                'instance_name': self.context.instance_name,
                'operation': self.context.operation,
                'file_path': self.context.file_path,
                'paper_id': self.context.paper_id,
                'url': self.context.url,
                'additional_data': self.context.additional_data
            },
            'is_recoverable': self.is_recoverable,
            'recovery_attempts': self.recovery_attempts,
            'max_recovery_attempts': self.max_recovery_attempts,
            'last_recovery_attempt': self.last_recovery_attempt.isoformat() if self.last_recovery_attempt else None,
            'is_resolved': self.is_resolved,
            'resolution_method': self.resolution_method,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingError':
        """Create ProcessingError from dictionary."""
        
        context = ErrorContext(
            instance_name=data['context']['instance_name'],
            operation=data['context']['operation'],
            file_path=data['context']['file_path'],
            paper_id=data['context']['paper_id'],
            url=data['context']['url'],
            additional_data=data['context']['additional_data']
        )
        
        return cls(
            error_id=data['error_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            instance_name=data['instance_name'],
            error_type=ErrorType(data['error_type']),
            error_category=ErrorCategory(data['error_category']),
            severity=ErrorSeverity(data['severity']),
            message=data['message'],
            exception_type=data['exception_type'],
            stack_trace=data['stack_trace'],
            context=context,
            is_recoverable=data['is_recoverable'],
            recovery_attempts=data['recovery_attempts'],
            max_recovery_attempts=data['max_recovery_attempts'],
            last_recovery_attempt=datetime.fromisoformat(data['last_recovery_attempt']) if data['last_recovery_attempt'] else None,
            is_resolved=data['is_resolved'],
            resolution_method=data['resolution_method'],
            resolved_at=datetime.fromisoformat(data['resolved_at']) if data['resolved_at'] else None
        )


@dataclass
class ErrorSummary:
    """Summary of errors for reporting."""
    
    instance_name: str
    time_period: timedelta
    total_errors: int
    errors_by_category: Dict[ErrorCategory, int] = field(default_factory=dict)
    errors_by_severity: Dict[ErrorSeverity, int] = field(default_factory=dict)
    errors_by_type: Dict[ErrorType, int] = field(default_factory=dict)
    resolved_errors: int = 0
    unresolved_errors: int = 0
    most_common_errors: List[str] = field(default_factory=list)
    error_rate_per_hour: float = 0.0
    
    @classmethod
    def from_errors(cls, errors: List[ProcessingError], instance_name: str, time_period: timedelta) -> 'ErrorSummary':
        """Create error summary from list of errors."""
        
        summary = cls(
            instance_name=instance_name,
            time_period=time_period,
            total_errors=len(errors)
        )
        
        # Count by category
        for error in errors:
            summary.errors_by_category[error.error_category] = summary.errors_by_category.get(error.error_category, 0) + 1
            summary.errors_by_severity[error.severity] = summary.errors_by_severity.get(error.severity, 0) + 1
            summary.errors_by_type[error.error_type] = summary.errors_by_type.get(error.error_type, 0) + 1
            
            if error.is_resolved:
                summary.resolved_errors += 1
            else:
                summary.unresolved_errors += 1
        
        # Calculate error rate
        if time_period.total_seconds() > 0:
            hours = time_period.total_seconds() / 3600
            summary.error_rate_per_hour = len(errors) / hours
        
        # Find most common errors
        error_counts = {}
        for error in errors:
            key = f"{error.error_type.value}: {error.message[:50]}"
            error_counts[key] = error_counts.get(key, 0) + 1
        
        summary.most_common_errors = sorted(error_counts.keys(), key=lambda x: error_counts[x], reverse=True)[:5]
        
        return summary


@dataclass
class RecoveryReport:
    """Report on error recovery operations."""
    
    instance_name: str
    recovery_session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Recovery statistics
    total_errors_processed: int = 0
    successful_recoveries: int = 0
    failed_recoveries: int = 0
    skipped_errors: int = 0
    
    # Recovery details
    recovery_methods_used: List[str] = field(default_factory=list)
    errors_by_recovery_method: Dict[str, int] = field(default_factory=dict)
    
    # Performance
    average_recovery_time_seconds: float = 0.0
    total_recovery_time_seconds: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate recovery success rate."""
        if self.total_errors_processed == 0:
            return 0.0
        return (self.successful_recoveries / self.total_errors_processed) * 100.0
    
    @property
    def duration_seconds(self) -> float:
        """Get total duration of recovery session."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    def add_recovery_result(self, method: str, success: bool, duration_seconds: float) -> None:
        """Add a recovery result to the report."""
        
        self.total_errors_processed += 1
        
        if success:
            self.successful_recoveries += 1
        else:
            self.failed_recoveries += 1
        
        if method not in self.recovery_methods_used:
            self.recovery_methods_used.append(method)
        
        self.errors_by_recovery_method[method] = self.errors_by_recovery_method.get(method, 0) + 1
        
        # Update timing
        self.total_recovery_time_seconds += duration_seconds
        if self.total_errors_processed > 0:
            self.average_recovery_time_seconds = self.total_recovery_time_seconds / self.total_errors_processed
    
    def finalize(self) -> None:
        """Finalize the recovery report."""
        self.end_time = datetime.now()