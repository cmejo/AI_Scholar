"""
Quant Scholar Error Handler with specialized error handling and recovery.

Provides comprehensive error handling for Quant Scholar operations including:
- Network error handling with exponential backoff
- PDF processing error handling and skip logic
- Journal source error handling
- Storage error detection and recovery procedures
- Retry logic with intelligent backoff strategies
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
import json
import traceback
from enum import Enum

from ..shared.multi_instance_error_handler import MultiInstanceErrorHandler
from ..shared.multi_instance_data_models import ProcessingError

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Error categories for Quant Scholar operations."""
    NETWORK = "network"
    PDF_PROCESSING = "pdf_processing"
    VECTOR_STORE = "vector_store"
    STORAGE = "storage"
    CONFIGURATION = "configuration"
    ARXIV_API = "arxiv_api"
    DOWNLOAD = "download"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    JOURNAL_SOURCE = "journal_source"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RetryStrategy:
    """Retry strategy configuration."""
    
    def __init__(self, 
                 max_attempts: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0,
                 jitter: bool = True):
        """
        Initialize retry strategy.
        
        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter to delays
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Get delay for the given attempt number."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
        
        return delay


class QuantScholarErrorHandler(MultiInstanceErrorHandler):
    """Enhanced error handler for Quant Scholar operations."""
    
    def __init__(self, error_log_dir: Path, instance_name: str, processor_id: str):
        """
        Initialize Quant Scholar error handler.
        
        Args:
            error_log_dir: Base directory to store error logs
            instance_name: Name of the scholar instance
            processor_id: Unique identifier for the processor
        """
        super().__init__(error_log_dir, instance_name, processor_id)
        
        # Quant Scholar specific error tracking
        self.quant_scholar_stats = {
            'arxiv_api_errors': 0,
            'pdf_download_errors': 0,
            'pdf_processing_errors': 0,
            'vector_store_errors': 0,
            'chunking_errors': 0,
            'embedding_errors': 0,
            'journal_source_errors': 0,
            'consecutive_failures': 0,
            'last_success_time': None,
            'error_patterns': {}
        }
        
        # Retry strategies for different operations
        self.retry_strategies = {
            ErrorCategory.NETWORK: RetryStrategy(max_attempts=5, base_delay=2.0, max_delay=120.0),
            ErrorCategory.ARXIV_API: RetryStrategy(max_attempts=3, base_delay=3.0, max_delay=60.0),
            ErrorCategory.DOWNLOAD: RetryStrategy(max_attempts=4, base_delay=1.5, max_delay=90.0),
            ErrorCategory.PDF_PROCESSING: RetryStrategy(max_attempts=2, base_delay=0.5, max_delay=10.0),
            ErrorCategory.VECTOR_STORE: RetryStrategy(max_attempts=3, base_delay=1.0, max_delay=30.0),
            ErrorCategory.STORAGE: RetryStrategy(max_attempts=2, base_delay=0.5, max_delay=5.0),
            ErrorCategory.JOURNAL_SOURCE: RetryStrategy(max_attempts=3, base_delay=2.0, max_delay=60.0)
        }
        
        # Circuit breaker states
        self.circuit_breakers = {
            'arxiv_api': {'failures': 0, 'last_failure': None, 'state': 'closed'},
            'vector_store': {'failures': 0, 'last_failure': None, 'state': 'closed'},
            'pdf_processing': {'failures': 0, 'last_failure': None, 'state': 'closed'},
            'journal_sources': {'failures': 0, 'last_failure': None, 'state': 'closed'}
        }
        
        logger.info(f"QuantScholarErrorHandler initialized for instance '{instance_name}'")
    
    async def handle_with_retry(self,
                              operation: Callable,
                              error_category: ErrorCategory,
                              context: Dict[str, Any],
                              *args, **kwargs) -> Tuple[bool, Any, Optional[Exception]]:
        """
        Execute operation with retry logic and error handling.
        
        Args:
            operation: Async function to execute
            error_category: Category of the operation for retry strategy
            context: Context information for error logging
            *args, **kwargs: Arguments to pass to the operation
            
        Returns:
            Tuple of (success, result, last_exception)
        """
        strategy = self.retry_strategies.get(error_category, RetryStrategy())
        last_exception = None
        
        for attempt in range(strategy.max_attempts):
            try:
                # Check circuit breaker
                if not self._check_circuit_breaker(error_category):
                    logger.warning(f"Circuit breaker open for {error_category.value}, skipping operation")
                    return False, None, Exception(f"Circuit breaker open for {error_category.value}")
                
                # Execute operation
                result = await operation(*args, **kwargs)
                
                # Success - reset circuit breaker and consecutive failures
                self._reset_circuit_breaker(error_category)
                self.quant_scholar_stats['consecutive_failures'] = 0
                self.quant_scholar_stats['last_success_time'] = datetime.now()
                
                if attempt > 0:
                    logger.info(f"Operation succeeded on attempt {attempt + 1} for {error_category.value}")
                
                return True, result, None
                
            except Exception as e:
                last_exception = e
                self.quant_scholar_stats['consecutive_failures'] += 1
                
                # Log error with context
                error_context = context.copy()
                error_context.update({
                    'attempt': attempt + 1,
                    'max_attempts': strategy.max_attempts,
                    'error_category': error_category.value,
                    'operation': operation.__name__ if hasattr(operation, '__name__') else str(operation)
                })
                
                severity = ErrorSeverity.ERROR if attempt == strategy.max_attempts - 1 else ErrorSeverity.WARNING
                self.log_quant_scholar_error(e, error_context, error_category, severity)
                
                # Update circuit breaker
                self._update_circuit_breaker(error_category)
                
                # If this is the last attempt, don't wait
                if attempt == strategy.max_attempts - 1:
                    break
                
                # Wait before retry
                delay = strategy.get_delay(attempt)
                logger.info(f"Retrying {error_category.value} operation in {delay:.2f} seconds "
                           f"(attempt {attempt + 1}/{strategy.max_attempts})")
                await asyncio.sleep(delay)
        
        logger.error(f"Operation failed after {strategy.max_attempts} attempts for {error_category.value}")
        return False, None, last_exception    
    
    def log_quant_scholar_error(self,
                              error: Exception,
                              context: Dict[str, Any],
                              error_category: ErrorCategory,
                              severity: ErrorSeverity = ErrorSeverity.ERROR) -> ProcessingError:
        """
        Log Quant Scholar specific error with enhanced categorization.
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            error_category: Category of the error
            severity: Severity level of the error
            
        Returns:
            ProcessingError object that was created
        """
        # Update Quant Scholar specific statistics
        self._update_quant_scholar_stats(error_category)
        
        # Enhance context with Quant Scholar specific information
        enhanced_context = context.copy()
        enhanced_context.update({
            'error_category': error_category.value,
            'severity': severity.value,
            'consecutive_failures': self.quant_scholar_stats['consecutive_failures'],
            'error_pattern': self._detect_error_pattern(error, error_category),
            'suggested_action': self._get_suggested_action(error, error_category),
            'stack_trace': traceback.format_exc()
        })
        
        # Log using parent method
        return self.log_instance_error(
            error, 
            enhanced_context, 
            f"quant_scholar_{error_category.value}",
            severity.value
        )
    
    def _update_quant_scholar_stats(self, error_category: ErrorCategory) -> None:
        """Update Quant Scholar specific error statistics."""
        category_map = {
            ErrorCategory.ARXIV_API: 'arxiv_api_errors',
            ErrorCategory.DOWNLOAD: 'pdf_download_errors',
            ErrorCategory.PDF_PROCESSING: 'pdf_processing_errors',
            ErrorCategory.VECTOR_STORE: 'vector_store_errors',
            ErrorCategory.CHUNKING: 'chunking_errors',
            ErrorCategory.EMBEDDING: 'embedding_errors',
            ErrorCategory.JOURNAL_SOURCE: 'journal_source_errors'
        }
        
        stat_key = category_map.get(error_category)
        if stat_key:
            self.quant_scholar_stats[stat_key] += 1
    
    def _detect_error_pattern(self, error: Exception, category: ErrorCategory) -> str:
        """Detect error patterns for better diagnostics."""
        error_msg = str(error).lower()
        
        # Network-related patterns
        if category == ErrorCategory.NETWORK or category == ErrorCategory.ARXIV_API:
            if 'timeout' in error_msg:
                return 'timeout_pattern'
            elif 'connection' in error_msg:
                return 'connection_pattern'
            elif 'rate limit' in error_msg or '429' in error_msg:
                return 'rate_limit_pattern'
            elif 'dns' in error_msg:
                return 'dns_pattern'
        
        # PDF processing patterns
        elif category == ErrorCategory.PDF_PROCESSING:
            if 'corrupt' in error_msg or 'invalid' in error_msg:
                return 'corrupt_pdf_pattern'
            elif 'permission' in error_msg:
                return 'permission_pattern'
            elif 'memory' in error_msg:
                return 'memory_pattern'
        
        # Storage patterns
        elif category == ErrorCategory.STORAGE:
            if 'disk' in error_msg or 'space' in error_msg:
                return 'disk_space_pattern'
            elif 'permission' in error_msg:
                return 'permission_pattern'
        
        # Journal source patterns
        elif category == ErrorCategory.JOURNAL_SOURCE:
            if 'jss' in error_msg or 'jstatsoft' in error_msg:
                return 'jss_source_pattern'
            elif 'rjournal' in error_msg or 'r-project' in error_msg:
                return 'rjournal_source_pattern'
            elif 'html' in error_msg or 'parse' in error_msg:
                return 'html_parsing_pattern'
        
        return 'unknown_pattern'
    
    def _get_suggested_action(self, error: Exception, category: ErrorCategory) -> str:
        """Get suggested action for error resolution."""
        error_msg = str(error).lower()
        
        if category == ErrorCategory.NETWORK:
            if 'timeout' in error_msg:
                return 'Increase timeout values or check network connectivity'
            elif 'rate limit' in error_msg:
                return 'Implement longer delays between requests'
            else:
                return 'Check network connectivity and retry'
        
        elif category == ErrorCategory.PDF_PROCESSING:
            if 'corrupt' in error_msg:
                return 'Skip corrupted PDF and continue processing'
            elif 'memory' in error_msg:
                return 'Process PDFs in smaller batches'
            else:
                return 'Verify PDF file integrity and retry'
        
        elif category == ErrorCategory.STORAGE:
            if 'space' in error_msg:
                return 'Free up disk space or clean old files'
            elif 'permission' in error_msg:
                return 'Check file permissions and directory access'
            else:
                return 'Verify storage configuration and retry'
        
        elif category == ErrorCategory.VECTOR_STORE:
            return 'Check ChromaDB service status and connection'
        
        elif category == ErrorCategory.JOURNAL_SOURCE:
            if 'jss' in error_msg:
                return 'Check Journal of Statistical Software website availability'
            elif 'rjournal' in error_msg:
                return 'Check R Journal website availability'
            else:
                return 'Verify journal source configuration and connectivity'
        
        return 'Review error details and retry operation'
    
    def _check_circuit_breaker(self, category: ErrorCategory) -> bool:
        """Check if circuit breaker allows operation."""
        breaker_key = self._get_breaker_key(category)
        if not breaker_key:
            return True
        
        breaker = self.circuit_breakers[breaker_key]
        
        if breaker['state'] == 'open':
            # Check if enough time has passed to try again
            if breaker['last_failure']:
                time_since_failure = datetime.now() - breaker['last_failure']
                if time_since_failure > timedelta(minutes=5):  # 5 minute cooldown
                    breaker['state'] = 'half_open'
                    logger.info(f"Circuit breaker for {breaker_key} moved to half-open state")
                    return True
                else:
                    return False
        
        return True
    
    def _update_circuit_breaker(self, category: ErrorCategory) -> None:
        """Update circuit breaker state after failure."""
        breaker_key = self._get_breaker_key(category)
        if not breaker_key:
            return
        
        breaker = self.circuit_breakers[breaker_key]
        breaker['failures'] += 1
        breaker['last_failure'] = datetime.now()
        
        # Open circuit breaker after 5 consecutive failures
        if breaker['failures'] >= 5 and breaker['state'] != 'open':
            breaker['state'] = 'open'
            logger.warning(f"Circuit breaker for {breaker_key} opened after {breaker['failures']} failures")
    
    def _reset_circuit_breaker(self, category: ErrorCategory) -> None:
        """Reset circuit breaker after successful operation."""
        breaker_key = self._get_breaker_key(category)
        if not breaker_key:
            return
        
        breaker = self.circuit_breakers[breaker_key]
        if breaker['failures'] > 0:
            logger.info(f"Circuit breaker for {breaker_key} reset after successful operation")
        
        breaker['failures'] = 0
        breaker['state'] = 'closed'
        breaker['last_failure'] = None
    
    def _get_breaker_key(self, category: ErrorCategory) -> Optional[str]:
        """Get circuit breaker key for error category."""
        category_map = {
            ErrorCategory.ARXIV_API: 'arxiv_api',
            ErrorCategory.VECTOR_STORE: 'vector_store',
            ErrorCategory.PDF_PROCESSING: 'pdf_processing',
            ErrorCategory.JOURNAL_SOURCE: 'journal_sources'
        }
        return category_map.get(category)
    
    def get_quant_scholar_error_summary(self) -> Dict[str, Any]:
        """Get comprehensive Quant Scholar error summary."""
        base_summary = self.get_instance_error_summary()
        
        return {
            **base_summary,
            'quant_scholar_stats': self.quant_scholar_stats.copy(),
            'circuit_breakers': {k: v.copy() for k, v in self.circuit_breakers.items()},
            'retry_strategies': {k.value: {
                'max_attempts': v.max_attempts,
                'base_delay': v.base_delay,
                'max_delay': v.max_delay
            } for k, v in self.retry_strategies.items()},
            'health_status': self._get_health_status(),
            'recommendations': self._get_error_recommendations()
        }
    
    def _get_health_status(self) -> str:
        """Get overall health status based on error patterns."""
        total_errors = self.quant_scholar_stats['consecutive_failures']
        
        # Check circuit breakers
        open_breakers = [k for k, v in self.circuit_breakers.items() if v['state'] == 'open']
        if open_breakers:
            return 'critical'
        
        # Check consecutive failures
        if total_errors >= 10:
            return 'critical'
        elif total_errors >= 5:
            return 'warning'
        elif total_errors > 0:
            return 'degraded'
        else:
            return 'healthy'
    
    def _get_error_recommendations(self) -> List[str]:
        """Get recommendations based on error patterns."""
        recommendations = []
        
        # Check for high error rates
        if self.quant_scholar_stats['consecutive_failures'] >= 5:
            recommendations.append("High consecutive failure rate detected - consider pausing operations")
        
        # Check circuit breakers
        for breaker_name, breaker in self.circuit_breakers.items():
            if breaker['state'] == 'open':
                recommendations.append(f"Circuit breaker open for {breaker_name} - check service health")
        
        # Check specific error types
        if self.quant_scholar_stats['arxiv_api_errors'] > 10:
            recommendations.append("High arXiv API error rate - implement longer delays")
        
        if self.quant_scholar_stats['pdf_processing_errors'] > 5:
            recommendations.append("High PDF processing error rate - check file integrity")
        
        if self.quant_scholar_stats['vector_store_errors'] > 3:
            recommendations.append("Vector store errors detected - check ChromaDB service")
        
        if self.quant_scholar_stats['journal_source_errors'] > 5:
            recommendations.append("Journal source errors detected - check website availability")
        
        return recommendations
    
    def should_continue_processing(self) -> bool:
        """Determine if Quant Scholar processing should continue."""
        # Check circuit breakers
        critical_breakers = ['arxiv_api', 'vector_store', 'journal_sources']
        for breaker_name in critical_breakers:
            if self.circuit_breakers[breaker_name]['state'] == 'open':
                logger.error(f"Critical circuit breaker '{breaker_name}' is open")
                return False
        
        # Check consecutive failures
        if self.quant_scholar_stats['consecutive_failures'] >= 15:
            logger.error(f"Too many consecutive failures: {self.quant_scholar_stats['consecutive_failures']}")
            return False
        
        # Use parent method for additional checks
        return self.should_instance_continue_processing(
            max_error_rate=35.0,  # Allow 35% error rate for Quant Scholar (higher due to journal sources)
            max_critical_errors=3
        )
    
    def export_quant_scholar_report(self, output_path: Path) -> bool:
        """Export comprehensive Quant Scholar error report."""
        try:
            summary = self.get_quant_scholar_error_summary()
            
            # Add timestamp and metadata
            report = {
                'report_type': 'quant_scholar_error_report',
                'generated_at': datetime.now().isoformat(),
                'instance_name': self.instance_name,
                'processor_id': self.processor_id,
                'summary': summary
            }
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Quant Scholar error report exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export Quant Scholar error report: {e}")
            return False