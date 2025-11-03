"""
Multi-Instance Progress Tracker for arXiv RAG Enhancement system.

Extends the existing ProgressTracker to support multiple scholar instances with
instance-specific progress monitoring and aggregated reporting.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Callable, Any, Dict, List
import threading

# Import base ProgressTracker
from arxiv_rag_enhancement.shared.progress_tracker import ProgressTracker
from arxiv_rag_enhancement.shared.data_models import ProgressStats
from .multi_instance_data_models import InstanceStats

logger = logging.getLogger(__name__)


class MultiInstanceProgressTracker(ProgressTracker):
    """Extended ProgressTracker with multi-instance support and aggregation."""
    
    def __init__(self, 
                 instance_name: str,
                 update_callback: Optional[Callable[[ProgressStats], None]] = None,
                 update_interval: float = 1.0):
        """
        Initialize MultiInstanceProgressTracker.
        
        Args:
            instance_name: Name of the scholar instance
            update_callback: Optional callback function called on progress updates
            update_interval: Minimum interval between progress updates (seconds)
        """
        self.instance_name = instance_name
        
        # Initialize parent tracker
        super().__init__(update_callback, update_interval)
        
        # Instance-specific tracking
        self.instance_stats = InstanceStats(
            instance_name=instance_name,
            total_papers=0,
            processed_papers=0,
            failed_papers=0,
            storage_used_mb=0,
            last_update=datetime.now(),
            processing_rate=0.0,
            error_rate=0.0
        )
        
        # Multi-instance coordination
        self._global_callback: Optional[Callable[[str, ProgressStats], None]] = None
        
        logger.info(f"MultiInstanceProgressTracker initialized for instance '{instance_name}'")
    
    def set_global_callback(self, callback: Callable[[str, ProgressStats], None]) -> None:
        """
        Set a global callback that receives updates from all instances.
        
        Args:
            callback: Function that receives (instance_name, progress_stats)
        """
        self._global_callback = callback
    
    def start_operation(self, operation_name: str, total_items: int) -> None:
        """
        Start tracking progress for a specific operation.
        
        Args:
            operation_name: Name of the operation being tracked
            total_items: Total number of items to process
        """
        self.start_instance_tracking(total_items, operation_name)
        logger.info(f"Started operation '{operation_name}' for instance '{self.instance_name}' with {total_items} items")
    
    def complete_operation(self, operation_name: str, message: str = "Operation completed") -> None:
        """
        Mark an operation as completed.
        
        Args:
            operation_name: Name of the operation that completed
            message: Completion message
        """
        self.finish_instance(f"{operation_name}: {message}")
        logger.info(f"Completed operation '{operation_name}' for instance '{self.instance_name}': {message}")
    
    def start_instance_tracking(self, total_items: int, operation_type: str = "processing") -> None:
        """
        Start tracking progress for an instance operation.
        
        Args:
            total_items: Total number of items to process
            operation_type: Type of operation being tracked
        """
        with self._lock:
            # Update instance stats
            self.instance_stats.total_papers = total_items
            self.instance_stats.processed_papers = 0
            self.instance_stats.failed_papers = 0
            self.instance_stats.last_update = datetime.now()
            self.instance_stats.processing_rate = 0.0
            self.instance_stats.error_rate = 0.0
        
        # Start parent tracking
        self.start_tracking(total_items)
        
        logger.info(f"Started instance tracking for '{self.instance_name}': "
                   f"{total_items} items, operation: {operation_type}")
    
    def update_instance_progress(self, 
                               completed: int, 
                               failed: int = 0,
                               current_item: str = "",
                               storage_used_mb: int = 0) -> None:
        """
        Update progress information with instance-specific data.
        
        Args:
            completed: Number of completed items
            failed: Number of failed items
            current_item: Description of current item being processed
            storage_used_mb: Current storage usage in MB
        """
        with self._lock:
            # Update instance stats
            self.instance_stats.processed_papers = completed
            self.instance_stats.failed_papers = failed
            self.instance_stats.storage_used_mb = storage_used_mb
            self.instance_stats.last_update = datetime.now()
            
            # Calculate rates
            if self.start_time:
                elapsed = (datetime.now() - self.start_time).total_seconds()
                if elapsed > 0:
                    self.instance_stats.processing_rate = completed / elapsed
                    total_processed = completed + failed
                    if total_processed > 0:
                        self.instance_stats.error_rate = (failed / total_processed) * 100
        
        # Update parent progress
        self.update_progress(completed, current_item)
        
        # Call global callback if set
        if self._global_callback:
            try:
                stats = self.get_stats()
                self._global_callback(self.instance_name, stats)
            except Exception as e:
                logger.error(f"Error in global progress callback: {e}")
    
    def get_instance_stats(self) -> InstanceStats:
        """
        Get current instance statistics.
        
        Returns:
            InstanceStats object with current instance information
        """
        with self._lock:
            return InstanceStats(
                instance_name=self.instance_stats.instance_name,
                total_papers=self.instance_stats.total_papers,
                processed_papers=self.instance_stats.processed_papers,
                failed_papers=self.instance_stats.failed_papers,
                storage_used_mb=self.instance_stats.storage_used_mb,
                last_update=self.instance_stats.last_update,
                processing_rate=self.instance_stats.processing_rate,
                error_rate=self.instance_stats.error_rate
            )
    
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """
        Get enhanced progress statistics including instance information.
        
        Returns:
            Dictionary with enhanced progress and instance statistics
        """
        base_stats = self.get_stats()
        instance_stats = self.get_instance_stats()
        
        return {
            'instance_name': self.instance_name,
            'progress': base_stats.to_dict(),
            'instance_stats': instance_stats.to_dict(),
            'performance': {
                'items_per_second': base_stats.processing_rate,
                'papers_per_hour': instance_stats.processing_rate * 3600,
                'error_percentage': instance_stats.error_rate,
                'storage_mb_per_paper': (
                    instance_stats.storage_used_mb / max(instance_stats.processed_papers, 1)
                ),
                'estimated_total_storage_mb': (
                    (instance_stats.storage_used_mb / max(instance_stats.processed_papers, 1)) * 
                    instance_stats.total_papers
                ) if instance_stats.processed_papers > 0 else 0
            }
        }
    
    def _display_progress(self) -> None:
        """Display instance-specific progress information to console."""
        stats = self.get_stats()
        instance_stats = self.get_instance_stats()
        
        if stats.total_items == 0:
            return
        
        # Format progress bar
        bar_width = 40
        filled_width = int(bar_width * stats.percentage_complete / 100)
        bar = "█" * filled_width + "░" * (bar_width - filled_width)
        
        # Format ETA
        eta_str = ""
        if stats.estimated_completion:
            eta = stats.estimated_completion - datetime.now()
            if eta.total_seconds() > 0:
                hours, remainder = divmod(int(eta.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                if hours > 0:
                    eta_str = f" ETA: {hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    eta_str = f" ETA: {minutes:02d}:{seconds:02d}"
        
        # Format rates
        rate_str = f"{stats.processing_rate:.2f} items/sec"
        papers_per_hour = instance_stats.processing_rate * 3600
        
        # Format storage
        storage_str = f"{instance_stats.storage_used_mb:.1f} MB"
        
        # Format current item (truncate if too long)
        current_item = stats.current_item
        if len(current_item) > 50:
            current_item = current_item[:47] + "..."
        
        # Print instance-specific progress line
        progress_line = (
            f"\r[{self.instance_name}] [{bar}] {stats.percentage_complete:6.2f}% "
            f"({stats.completed_items}/{stats.total_items}) "
            f"{rate_str} ({papers_per_hour:.1f} papers/hr) "
            f"Storage: {storage_str}{eta_str}"
        )
        
        print(progress_line, end="", flush=True)
        
        # Print current item on new line if it's meaningful
        if current_item and current_item != "":
            print(f"\n[{self.instance_name}] Processing: {current_item}", flush=True)
        
        # Print error information if there are failures
        if instance_stats.failed_papers > 0:
            error_rate = instance_stats.error_rate
            print(f"\n[{self.instance_name}] Errors: {instance_stats.failed_papers} "
                  f"({error_rate:.1f}%)", flush=True)
    
    def finish_instance(self, message: str = "Instance processing complete") -> None:
        """
        Mark instance progress as finished and display final statistics.
        
        Args:
            message: Final message to display
        """
        with self._lock:
            if self.start_time is None:
                return
            
            self.completed_items = self.total_items
            self.current_item = ""
            self.last_update_time = datetime.now()
            self.instance_stats.last_update = datetime.now()
        
        # Display final progress
        print()  # New line after progress bar
        stats = self.get_stats()
        instance_stats = self.get_instance_stats()
        
        elapsed = stats.last_update - stats.start_time
        elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
        
        print(f"\n[{self.instance_name}] {message}")
        print(f"[{self.instance_name}] Total papers: {instance_stats.total_papers}")
        print(f"[{self.instance_name}] Processed: {instance_stats.processed_papers}")
        print(f"[{self.instance_name}] Failed: {instance_stats.failed_papers}")
        print(f"[{self.instance_name}] Storage used: {instance_stats.storage_used_mb:.1f} MB")
        print(f"[{self.instance_name}] Time elapsed: {elapsed_str}")
        print(f"[{self.instance_name}] Average rate: {stats.processing_rate:.2f} items/sec")
        print(f"[{self.instance_name}] Error rate: {instance_stats.error_rate:.2f}%")
        
        logger.info(f"Instance progress tracking finished for '{self.instance_name}': {message}")


class GlobalProgressTracker:
    """Tracks progress across all scholar instances."""
    
    def __init__(self):
        """Initialize GlobalProgressTracker."""
        self.instance_trackers: Dict[str, MultiInstanceProgressTracker] = {}
        self._lock = threading.Lock()
        
        # Global statistics
        self.global_stats = {
            'total_instances': 0,
            'active_instances': 0,
            'total_items': 0,
            'completed_items': 0,
            'failed_items': 0,
            'total_storage_mb': 0,
            'start_time': None,
            'last_update': datetime.now()
        }
        
        logger.info("GlobalProgressTracker initialized")
    
    def register_instance(self, instance_name: str) -> MultiInstanceProgressTracker:
        """
        Register a new instance tracker.
        
        Args:
            instance_name: Name of the scholar instance
            
        Returns:
            MultiInstanceProgressTracker for the instance
        """
        with self._lock:
            if instance_name in self.instance_trackers:
                logger.warning(f"Instance tracker '{instance_name}' already registered")
                return self.instance_trackers[instance_name]
            
            # Create instance tracker with global callback
            tracker = MultiInstanceProgressTracker(
                instance_name=instance_name,
                update_callback=None,
                update_interval=1.0
            )
            
            # Set global callback to receive updates
            tracker.set_global_callback(self._on_instance_update)
            
            self.instance_trackers[instance_name] = tracker
            self.global_stats['total_instances'] = len(self.instance_trackers)
            
            logger.info(f"Registered instance tracker for '{instance_name}'")
            return tracker
    
    def _on_instance_update(self, instance_name: str, progress_stats: ProgressStats) -> None:
        """
        Handle progress updates from instance trackers.
        
        Args:
            instance_name: Name of the instance that updated
            progress_stats: Progress statistics from the instance
        """
        with self._lock:
            # Update global statistics
            self.global_stats['last_update'] = datetime.now()
            
            # Count active instances
            active_count = sum(
                1 for tracker in self.instance_trackers.values() 
                if tracker.is_active()
            )
            self.global_stats['active_instances'] = active_count
            
            # Aggregate totals
            total_items = sum(
                tracker.total_items for tracker in self.instance_trackers.values()
            )
            completed_items = sum(
                tracker.completed_items for tracker in self.instance_trackers.values()
            )
            
            self.global_stats['total_items'] = total_items
            self.global_stats['completed_items'] = completed_items
            
            # Aggregate storage usage
            total_storage = sum(
                tracker.get_instance_stats().storage_used_mb 
                for tracker in self.instance_trackers.values()
            )
            self.global_stats['total_storage_mb'] = total_storage
    
    def get_global_summary(self) -> Dict[str, Any]:
        """
        Get a summary of progress across all instances.
        
        Returns:
            Dictionary with global progress summary
        """
        with self._lock:
            instance_summaries = {}
            
            for instance_name, tracker in self.instance_trackers.items():
                try:
                    instance_summaries[instance_name] = tracker.get_enhanced_stats()
                except Exception as e:
                    logger.error(f"Failed to get stats for instance {instance_name}: {e}")
                    instance_summaries[instance_name] = {
                        'error': str(e),
                        'instance_name': instance_name
                    }
            
            return {
                'global_stats': self.global_stats.copy(),
                'instances': instance_summaries,
                'summary': {
                    'total_instances': self.global_stats['total_instances'],
                    'active_instances': self.global_stats['active_instances'],
                    'overall_progress': (
                        (self.global_stats['completed_items'] / 
                         max(self.global_stats['total_items'], 1)) * 100
                    ),
                    'total_storage_gb': self.global_stats['total_storage_mb'] / 1024,
                    'last_update': self.global_stats['last_update'].isoformat()
                }
            }
    
    def display_global_progress(self) -> None:
        """Display progress summary for all instances."""
        summary = self.get_global_summary()
        
        print("\n" + "=" * 80)
        print("MULTI-INSTANCE PROGRESS SUMMARY")
        print("=" * 80)
        
        global_stats = summary['global_stats']
        print(f"Total Instances: {global_stats['total_instances']}")
        print(f"Active Instances: {global_stats['active_instances']}")
        print(f"Overall Progress: {summary['summary']['overall_progress']:.2f}%")
        print(f"Total Storage: {summary['summary']['total_storage_gb']:.2f} GB")
        print(f"Last Update: {summary['summary']['last_update']}")
        
        print("\nPER-INSTANCE STATUS:")
        print("-" * 80)
        
        for instance_name, instance_data in summary['instances'].items():
            if 'error' in instance_data:
                print(f"{instance_name:15} ERROR: {instance_data['error']}")
                continue
            
            progress = instance_data.get('progress', {})
            instance_stats = instance_data.get('instance_stats', {})
            performance = instance_data.get('performance', {})
            
            status = "ACTIVE" if progress.get('percentage_complete', 0) < 100 else "COMPLETE"
            print(f"{instance_name:15} {status:8} "
                  f"{progress.get('percentage_complete', 0):6.2f}% "
                  f"({instance_stats.get('processed_papers', 0)}/{instance_stats.get('total_papers', 0)}) "
                  f"Rate: {performance.get('papers_per_hour', 0):.1f}/hr "
                  f"Storage: {instance_stats.get('storage_used_mb', 0):.1f}MB")
        
        print("=" * 80)
    
    def wait_for_all_instances(self, check_interval: float = 5.0) -> None:
        """
        Wait for all registered instances to complete processing.
        
        Args:
            check_interval: Interval between status checks (seconds)
        """
        import time
        
        logger.info("Waiting for all instances to complete...")
        
        while True:
            with self._lock:
                active_instances = [
                    name for name, tracker in self.instance_trackers.items()
                    if tracker.is_active()
                ]
            
            if not active_instances:
                logger.info("All instances have completed processing")
                break
            
            logger.info(f"Waiting for instances: {', '.join(active_instances)}")
            self.display_global_progress()
            
            time.sleep(check_interval)
    
    def get_instance_tracker(self, instance_name: str) -> Optional[MultiInstanceProgressTracker]:
        """
        Get the tracker for a specific instance.
        
        Args:
            instance_name: Name of the instance
            
        Returns:
            MultiInstanceProgressTracker if found, None otherwise
        """
        with self._lock:
            return self.instance_trackers.get(instance_name)