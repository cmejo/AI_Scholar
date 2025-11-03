"""
Error Handler for arXiv RAG Enhancement system.

Provides centralized error handling, logging, and reporting functionality
for all processing scripts.
"""

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import csv

from .data_models import ProcessingError, ErrorSummary

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling and logging system."""
    
    def __init__(self, error_log_dir: Path, processor_id: str):
        """
        Initialize ErrorHandler.
        
        Args:
            error_log_dir: Directory to store error logs
            processor_id: Unique identifier for the processor
        """
        self.error_log_dir = Path(error_log_dir)
        self.processor_id = processor_id
        self.error_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Error tracking
        self.errors: List[ProcessingError] = []
        self.error_counts: Dict[str, int] = {}
        self.failed_files: List[str] = []
        
        # Log files
        self.error_log_file = self.error_log_dir / f"{processor_id}_errors.json"
        self.failed_files_log = self.error_log_dir / f"{processor_id}_failed_files.csv"
        
        logger.info(f"ErrorHandler initialized for processor {processor_id}")
    
    def log_error(self, 
                  error: Exception, 
                  context: Dict[str, Any],
                  error_type: str = "processing_error") -> ProcessingError:
        """
        Log an error with context information.
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            error_type: Type/category of the error
            
        Returns:
            ProcessingError object that was created
        """
        # Create ProcessingError object
        processing_error = ProcessingError(
            timestamp=datetime.now(),
            error_type=error_type,
            file_path=context.get('file_path', ''),
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            context=context,
            retry_count=context.get('retry_count', 0)
        )
        
        # Add to internal tracking
        self.errors.append(processing_error)
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Log to file
        self._write_error_to_log(processing_error)
        
        # Log to Python logger
        logger.error(
            f"Error in {self.processor_id}: {error_type} - {str(error)}",
            extra={
                'processor_id': self.processor_id,
                'error_type': error_type,
                'file_path': context.get('file_path', ''),
                'context': context
            }
        )
        
        return processing_error
    
    def log_failed_file(self, file_path: str, error_message: str, error_type: str = "file_error") -> None:
        """
        Log a failed file with error details.
        
        Args:
            file_path: Path to the file that failed
            error_message: Error message describing the failure
            error_type: Type/category of the error
        """
        self.failed_files.append(file_path)
        
        # Write to CSV log
        self._write_failed_file_to_csv(file_path, error_message, error_type)
        
        logger.warning(f"File failed: {file_path} - {error_message}")
    
    def _write_error_to_log(self, error: ProcessingError) -> None:
        """Write error to JSON log file."""
        try:
            # Load existing errors
            existing_errors = []
            if self.error_log_file.exists():
                try:
                    with open(self.error_log_file, 'r') as f:
                        existing_errors = json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted error log file: {self.error_log_file}")
                    existing_errors = []
            
            # Add new error
            existing_errors.append(error.to_dict())
            
            # Write back to file
            with open(self.error_log_file, 'w') as f:
                json.dump(existing_errors, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to write error to log file: {e}")
    
    def _write_failed_file_to_csv(self, file_path: str, error_message: str, error_type: str) -> None:
        """Write failed file information to CSV log."""
        try:
            # Check if file exists to determine if we need headers
            file_exists = self.failed_files_log.exists()
            
            with open(self.failed_files_log, 'a', newline='') as f:
                writer = csv.writer(f)
                
                # Write header if file is new
                if not file_exists:
                    writer.writerow(['timestamp', 'file_path', 'error_type', 'error_message'])
                
                # Write error record
                writer.writerow([
                    datetime.now().isoformat(),
                    file_path,
                    error_type,
                    error_message
                ])
                
        except Exception as e:
            logger.error(f"Failed to write failed file to CSV: {e}")
    
    def get_error_summary(self) -> ErrorSummary:
        """
        Get summary of all errors encountered.
        
        Returns:
            ErrorSummary object with error statistics
        """
        total_errors = len(self.errors)
        recent_errors = self.errors[-10:] if len(self.errors) > 10 else self.errors
        
        # Calculate error rate (errors per processed item)
        # This would need to be updated by the calling code with total processed count
        error_rate = 0.0  # Placeholder
        
        return ErrorSummary(
            total_errors=total_errors,
            error_types=self.error_counts.copy(),
            failed_files=self.failed_files.copy(),
            recent_errors=recent_errors,
            error_rate=error_rate
        )
    
    def export_error_report(self, output_path: Path) -> bool:
        """
        Export comprehensive error report to file.
        
        Args:
            output_path: Path to save the error report
            
        Returns:
            True if successful, False otherwise
        """
        try:
            summary = self.get_error_summary()
            
            report = {
                'processor_id': self.processor_id,
                'report_generated': datetime.now().isoformat(),
                'summary': summary.to_dict(),
                'detailed_errors': [error.to_dict() for error in self.errors]
            }
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Error report exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export error report: {e}")
            return False
    
    def clear_errors(self) -> None:
        """Clear all error tracking data."""
        self.errors.clear()
        self.error_counts.clear()
        self.failed_files.clear()
        
        logger.info(f"Cleared error tracking data for processor {self.processor_id}")
    
    def get_error_count(self, error_type: Optional[str] = None) -> int:
        """
        Get count of errors by type.
        
        Args:
            error_type: Specific error type to count, or None for total
            
        Returns:
            Number of errors
        """
        if error_type is None:
            return len(self.errors)
        return self.error_counts.get(error_type, 0)
    
    def get_recent_errors(self, count: int = 10) -> List[ProcessingError]:
        """
        Get most recent errors.
        
        Args:
            count: Number of recent errors to return
            
        Returns:
            List of recent ProcessingError objects
        """
        return self.errors[-count:] if len(self.errors) > count else self.errors
    
    def has_critical_errors(self) -> bool:
        """
        Check if there are any critical errors that should stop processing.
        
        Returns:
            True if critical errors are present
        """
        critical_error_types = [
            'storage_full',
            'permission_denied',
            'service_unavailable',
            'configuration_error'
        ]
        
        return any(error_type in self.error_counts for error_type in critical_error_types)
    
    def get_error_rate(self, total_processed: int) -> float:
        """
        Calculate error rate as percentage of processed items.
        
        Args:
            total_processed: Total number of items processed
            
        Returns:
            Error rate as percentage (0-100)
        """
        if total_processed == 0:
            return 0.0
        
        return (len(self.errors) / total_processed) * 100
    
    def should_continue_processing(self, 
                                   max_error_rate: float = 50.0,
                                   total_processed: int = 0) -> bool:
        """
        Determine if processing should continue based on error rate.
        
        Args:
            max_error_rate: Maximum acceptable error rate (percentage)
            total_processed: Total number of items processed so far
            
        Returns:
            True if processing should continue, False otherwise
        """
        # Check for critical errors
        if self.has_critical_errors():
            logger.error("Critical errors detected, processing should stop")
            return False
        
        # Check error rate
        if total_processed > 10:  # Only check rate after processing some items
            error_rate = self.get_error_rate(total_processed)
            if error_rate > max_error_rate:
                logger.error(f"Error rate {error_rate:.2f}% exceeds maximum {max_error_rate}%")
                return False
        
        return True
    
    def create_retry_context(self, 
                           original_context: Dict[str, Any], 
                           retry_count: int) -> Dict[str, Any]:
        """
        Create context for retry operations.
        
        Args:
            original_context: Original error context
            retry_count: Current retry attempt number
            
        Returns:
            Updated context for retry
        """
        retry_context = original_context.copy()
        retry_context['retry_count'] = retry_count
        retry_context['is_retry'] = True
        retry_context['original_error_time'] = original_context.get('timestamp', datetime.now().isoformat())
        
        return retry_context