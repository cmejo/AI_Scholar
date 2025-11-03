"""
Multi-Instance Error Handler for arXiv RAG Enhancement system.

Extends the existing ErrorHandler to support multiple scholar instances with
instance-specific error tracking, aggregated reporting, and cross-instance
error analysis.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

# Import base ErrorHandler
from arxiv_rag_enhancement.shared.error_handler import ErrorHandler
from arxiv_rag_enhancement.shared.data_models import ProcessingError, ErrorSummary
from .multi_instance_data_models import InstanceStats

logger = logging.getLogger(__name__)


class MultiInstanceErrorHandler(ErrorHandler):
    """Extended ErrorHandler with multi-instance support and aggregation."""
    
    def __init__(self, error_log_dir: Path, instance_name: str, processor_id: str):
        """
        Initialize MultiInstanceErrorHandler.
        
        Args:
            error_log_dir: Base directory to store error logs
            instance_name: Name of the scholar instance
            processor_id: Unique identifier for the processor
        """
        self.instance_name = instance_name
        
        # Create instance-specific error log directory
        instance_error_dir = Path(error_log_dir) / instance_name
        
        # Initialize parent with instance-specific directory and processor ID
        super().__init__(instance_error_dir, f"{instance_name}_{processor_id}")
        
        # Instance-specific tracking
        self.instance_error_stats = {
            'total_errors': 0,
            'critical_errors': 0,
            'warning_errors': 0,
            'network_errors': 0,
            'processing_errors': 0,
            'storage_errors': 0,
            'first_error_time': None,
            'last_error_time': None
        }
        
        logger.info(f"MultiInstanceErrorHandler initialized for instance '{instance_name}' "
                   f"with error directory: {self.error_log_dir}")
    
    def log_instance_error(self, 
                          error: Exception, 
                          context: Dict[str, Any],
                          error_type: str = "processing_error",
                          severity: str = "error") -> ProcessingError:
        """
        Log an error with instance-specific context and categorization.
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            error_type: Type/category of the error
            severity: Severity level (critical, error, warning)
            
        Returns:
            ProcessingError object that was created
        """
        # Add instance information to context
        enhanced_context = context.copy()
        enhanced_context.update({
            'instance_name': self.instance_name,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        })
        
        # Log using parent method
        processing_error = self.log_error(error, enhanced_context, error_type)
        
        # Update instance-specific statistics
        self._update_instance_stats(error_type, severity)
        
        return processing_error
    
    def _update_instance_stats(self, error_type: str, severity: str) -> None:
        """Update instance-specific error statistics."""
        now = datetime.now()
        
        self.instance_error_stats['total_errors'] += 1
        
        if self.instance_error_stats['first_error_time'] is None:
            self.instance_error_stats['first_error_time'] = now
        self.instance_error_stats['last_error_time'] = now
        
        # Update severity counters
        if severity == 'critical':
            self.instance_error_stats['critical_errors'] += 1
        elif severity == 'warning':
            self.instance_error_stats['warning_errors'] += 1
        
        # Update type counters
        if 'network' in error_type.lower():
            self.instance_error_stats['network_errors'] += 1
        elif 'processing' in error_type.lower():
            self.instance_error_stats['processing_errors'] += 1
        elif 'storage' in error_type.lower():
            self.instance_error_stats['storage_errors'] += 1
    
    def get_instance_error_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive error summary for this instance.
        
        Returns:
            Dictionary with instance-specific error summary
        """
        base_summary = self.get_error_summary()
        
        return {
            'instance_name': self.instance_name,
            'processor_id': self.processor_id,
            'base_summary': base_summary.to_dict(),
            'instance_stats': self.instance_error_stats.copy(),
            'error_categories': {
                'by_type': self.error_counts.copy(),
                'by_severity': {
                    'critical': self.instance_error_stats['critical_errors'],
                    'error': (self.instance_error_stats['total_errors'] - 
                             self.instance_error_stats['critical_errors'] - 
                             self.instance_error_stats['warning_errors']),
                    'warning': self.instance_error_stats['warning_errors']
                },
                'by_category': {
                    'network': self.instance_error_stats['network_errors'],
                    'processing': self.instance_error_stats['processing_errors'],
                    'storage': self.instance_error_stats['storage_errors'],
                    'other': (self.instance_error_stats['total_errors'] - 
                             self.instance_error_stats['network_errors'] - 
                             self.instance_error_stats['processing_errors'] - 
                             self.instance_error_stats['storage_errors'])
                }
            },
            'recent_errors': [error.to_dict() for error in self.get_recent_errors(5)],
            'failed_files_count': len(self.failed_files),
            'last_updated': datetime.now().isoformat()
        }
    
    def has_instance_critical_errors(self) -> bool:
        """
        Check if there are critical errors that should stop instance processing.
        
        Returns:
            True if critical errors are present for this instance
        """
        return (self.has_critical_errors() or 
                self.instance_error_stats['critical_errors'] > 0)
    
    def should_instance_continue_processing(self, 
                                          max_error_rate: float = 50.0,
                                          max_critical_errors: int = 5,
                                          total_processed: int = 0) -> bool:
        """
        Determine if instance processing should continue based on error patterns.
        
        Args:
            max_error_rate: Maximum acceptable error rate (percentage)
            max_critical_errors: Maximum number of critical errors allowed
            total_processed: Total number of items processed so far
            
        Returns:
            True if processing should continue, False otherwise
        """
        # Check critical error count
        if self.instance_error_stats['critical_errors'] >= max_critical_errors:
            logger.error(f"Instance '{self.instance_name}' has {self.instance_error_stats['critical_errors']} "
                        f"critical errors, exceeding limit of {max_critical_errors}")
            return False
        
        # Use parent method for other checks
        return self.should_continue_processing(max_error_rate, total_processed)
    
    def export_instance_error_report(self, output_path: Path) -> bool:
        """
        Export comprehensive error report for this instance.
        
        Args:
            output_path: Path to save the error report
            
        Returns:
            True if successful, False otherwise
        """
        try:
            summary = self.get_instance_error_summary()
            
            # Add detailed error analysis
            error_analysis = self._analyze_instance_errors()
            summary['error_analysis'] = error_analysis
            
            # Add recommendations
            recommendations = self._generate_error_recommendations()
            summary['recommendations'] = recommendations
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"Instance error report exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export instance error report: {e}")
            return False
    
    def _analyze_instance_errors(self) -> Dict[str, Any]:
        """Analyze error patterns for this instance."""
        analysis = {
            'error_trends': {},
            'common_failures': {},
            'time_patterns': {},
            'file_patterns': {}
        }
        
        if not self.errors:
            return analysis
        
        # Analyze error trends over time
        error_times = [error.timestamp for error in self.errors]
        if len(error_times) >= 2:
            time_span = (error_times[-1] - error_times[0]).total_seconds()
            if time_span > 0:
                analysis['error_trends']['errors_per_hour'] = len(self.errors) / (time_span / 3600)
        
        # Find most common error messages
        error_messages = {}
        for error in self.errors:
            msg_key = error.error_message[:100]  # First 100 chars
            error_messages[msg_key] = error_messages.get(msg_key, 0) + 1
        
        analysis['common_failures'] = dict(sorted(
            error_messages.items(), key=lambda x: x[1], reverse=True
        )[:5])  # Top 5 most common
        
        # Analyze file patterns
        failed_extensions = {}
        for file_path in self.failed_files:
            ext = Path(file_path).suffix.lower()
            failed_extensions[ext] = failed_extensions.get(ext, 0) + 1
        
        analysis['file_patterns']['failed_by_extension'] = failed_extensions
        
        return analysis
    
    def _generate_error_recommendations(self) -> List[str]:
        """Generate recommendations based on error patterns."""
        recommendations = []
        
        # Check error rate
        if self.instance_error_stats['total_errors'] > 100:
            recommendations.append(
                "High error count detected. Consider reviewing input data quality "
                "and processing parameters."
            )
        
        # Check critical errors
        if self.instance_error_stats['critical_errors'] > 0:
            recommendations.append(
                "Critical errors detected. Review system configuration and "
                "ensure all dependencies are properly installed."
            )
        
        # Check network errors
        if self.instance_error_stats['network_errors'] > 10:
            recommendations.append(
                "Multiple network errors detected. Check internet connectivity "
                "and consider implementing retry logic with exponential backoff."
            )
        
        # Check storage errors
        if self.instance_error_stats['storage_errors'] > 0:
            recommendations.append(
                "Storage errors detected. Check disk space and file permissions."
            )
        
        # Check processing errors
        processing_rate = (self.instance_error_stats['processing_errors'] / 
                          max(self.instance_error_stats['total_errors'], 1)) * 100
        if processing_rate > 50:
            recommendations.append(
                "High processing error rate. Consider reducing batch size or "
                "implementing more robust error handling."
            )
        
        return recommendations


class GlobalErrorHandler:
    """Manages error handling across all scholar instances."""
    
    def __init__(self, base_error_dir: Path):
        """
        Initialize GlobalErrorHandler.
        
        Args:
            base_error_dir: Base directory for all instance error logs
        """
        self.base_error_dir = Path(base_error_dir)
        self.base_error_dir.mkdir(parents=True, exist_ok=True)
        
        # Instance handlers cache
        self._instance_handlers: Dict[str, MultiInstanceErrorHandler] = {}
        
        logger.info(f"GlobalErrorHandler initialized with base directory: {self.base_error_dir}")
    
    def get_instance_handler(self, instance_name: str, processor_id: str) -> MultiInstanceErrorHandler:
        """
        Get or create an error handler for a specific instance.
        
        Args:
            instance_name: Name of the scholar instance
            processor_id: Unique identifier for the processor
            
        Returns:
            MultiInstanceErrorHandler for the specified instance
        """
        handler_key = f"{instance_name}_{processor_id}"
        
        if handler_key not in self._instance_handlers:
            self._instance_handlers[handler_key] = MultiInstanceErrorHandler(
                self.base_error_dir, instance_name, processor_id
            )
        
        return self._instance_handlers[handler_key]
    
    def get_global_error_summary(self) -> Dict[str, Any]:
        """
        Get aggregated error summary across all instances.
        
        Returns:
            Dictionary with global error summary
        """
        instance_summaries = {}
        global_stats = {
            'total_instances': len(self._instance_handlers),
            'total_errors': 0,
            'total_critical_errors': 0,
            'total_failed_files': 0,
            'instances_with_errors': 0
        }
        
        for handler_key, handler in self._instance_handlers.items():
            try:
                summary = handler.get_instance_error_summary()
                instance_summaries[handler_key] = summary
                
                # Aggregate global statistics
                global_stats['total_errors'] += summary['instance_stats']['total_errors']
                global_stats['total_critical_errors'] += summary['instance_stats']['critical_errors']
                global_stats['total_failed_files'] += summary['failed_files_count']
                
                if summary['instance_stats']['total_errors'] > 0:
                    global_stats['instances_with_errors'] += 1
                    
            except Exception as e:
                logger.error(f"Failed to get error summary for {handler_key}: {e}")
                instance_summaries[handler_key] = {'error': str(e)}
        
        return {
            'global_stats': global_stats,
            'instances': instance_summaries,
            'summary_generated': datetime.now().isoformat()
        }
    
    def export_global_error_report(self, output_path: Path) -> bool:
        """
        Export comprehensive error report for all instances.
        
        Args:
            output_path: Path to save the global error report
            
        Returns:
            True if successful, False otherwise
        """
        try:
            global_summary = self.get_global_error_summary()
            
            # Add cross-instance analysis
            cross_analysis = self._analyze_cross_instance_errors()
            global_summary['cross_instance_analysis'] = cross_analysis
            
            # Add global recommendations
            global_recommendations = self._generate_global_recommendations(global_summary)
            global_summary['global_recommendations'] = global_recommendations
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(global_summary, f, indent=2)
            
            logger.info(f"Global error report exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export global error report: {e}")
            return False
    
    def _analyze_cross_instance_errors(self) -> Dict[str, Any]:
        """Analyze error patterns across all instances."""
        analysis = {
            'common_error_types': {},
            'instance_comparison': {},
            'system_wide_issues': []
        }
        
        # Aggregate error types across instances
        all_error_types = {}
        instance_error_rates = {}
        
        for handler_key, handler in self._instance_handlers.items():
            try:
                summary = handler.get_instance_error_summary()
                
                # Aggregate error types
                for error_type, count in summary['error_categories']['by_type'].items():
                    all_error_types[error_type] = all_error_types.get(error_type, 0) + count
                
                # Calculate instance error rate
                total_errors = summary['instance_stats']['total_errors']
                instance_error_rates[handler_key] = total_errors
                
            except Exception as e:
                logger.error(f"Failed to analyze errors for {handler_key}: {e}")
        
        analysis['common_error_types'] = dict(sorted(
            all_error_types.items(), key=lambda x: x[1], reverse=True
        ))
        
        analysis['instance_comparison'] = instance_error_rates
        
        # Identify system-wide issues
        if all_error_types.get('network_error', 0) > 50:
            analysis['system_wide_issues'].append(
                "High network error count across instances suggests connectivity issues"
            )
        
        if all_error_types.get('storage_error', 0) > 10:
            analysis['system_wide_issues'].append(
                "Storage errors across instances suggest disk space or permission issues"
            )
        
        return analysis
    
    def _generate_global_recommendations(self, global_summary: Dict[str, Any]) -> List[str]:
        """Generate system-wide recommendations based on error patterns."""
        recommendations = []
        
        global_stats = global_summary['global_stats']
        
        # Check overall error rate
        if global_stats['total_errors'] > 1000:
            recommendations.append(
                "Very high global error count. Consider implementing system-wide "
                "error prevention measures and reviewing processing pipelines."
            )
        
        # Check critical error distribution
        if global_stats['total_critical_errors'] > 20:
            recommendations.append(
                "Multiple critical errors across instances. Review system "
                "configuration and consider implementing better error recovery."
            )
        
        # Check instance distribution
        error_rate = (global_stats['instances_with_errors'] / 
                     max(global_stats['total_instances'], 1)) * 100
        if error_rate > 75:
            recommendations.append(
                "Most instances experiencing errors. Consider system-wide "
                "infrastructure review and maintenance."
            )
        
        return recommendations