"""
Error handling and recovery system for the multi-instance ArXiv system.

This module provides comprehensive error handling, recovery strategies, analysis,
and prevention mechanisms for robust system operation.
"""

from .error_models import (
    ProcessingError, ErrorContext, ErrorSeverity, ErrorCategory, ErrorType,
    ErrorSummary, RecoveryReport
)
from .error_recovery_manager import ErrorRecoveryManager, RecoveryStrategy, RecoveryConfig
from .network_error_handler import NetworkErrorHandler, NetworkError, RetryConfig
from .pdf_processing_error_handler import PDFProcessingErrorHandler, PDFProcessingError, PDFValidationResult
from .storage_error_handler import StorageErrorHandler, StorageError, DiskSpaceInfo, StorageRecoveryAction
from .error_analyzer import ErrorAnalyzer, ErrorPattern, ErrorTrend, ErrorImpactAssessment, ResolutionSuggestion
from .error_prevention_system import ErrorPreventionSystem, PreventionRule, EarlyWarning, PreventionStrategy

__all__ = [
    # Error models
    'ProcessingError',
    'ErrorContext',
    'ErrorSeverity',
    'ErrorCategory',
    'ErrorType',
    'ErrorSummary',
    'RecoveryReport',
    
    # Error recovery manager
    'ErrorRecoveryManager',
    'RecoveryStrategy',
    'RecoveryConfig',
    
    # Network error handler
    'NetworkErrorHandler',
    'NetworkError',
    'RetryConfig',
    
    # PDF processing error handler
    'PDFProcessingErrorHandler',
    'PDFProcessingError',
    'PDFValidationResult',
    
    # Storage error handler
    'StorageErrorHandler',
    'StorageError',
    'DiskSpaceInfo',
    'StorageRecoveryAction',
    
    # Error analyzer
    'ErrorAnalyzer',
    'ErrorPattern',
    'ErrorTrend',
    'ErrorImpactAssessment',
    'ResolutionSuggestion',
    
    # Error prevention system
    'ErrorPreventionSystem',
    'PreventionRule',
    'EarlyWarning',
    'PreventionStrategy'
]