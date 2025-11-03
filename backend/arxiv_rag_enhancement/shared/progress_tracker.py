"""
Progress Tracker for arXiv RAG Enhancement system.

Provides real-time progress monitoring, ETA calculation, and statistics
for long-running processing operations.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable, Any
from collections import deque
import threading

from .data_models import ProgressStats

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Real-time progress monitoring and ETA calculation."""
    
    def __init__(self, 
                 update_callback: Optional[Callable[[ProgressStats], None]] = None,
                 update_interval: float = 1.0):
        """
        Initialize ProgressTracker.
        
        Args:
            update_callback: Optional callback function called on progress updates
            update_interval: Minimum interval between progress updates (seconds)
        """
        self.update_callback = update_callback
        self.update_interval = update_interval
        
        # Progress state
        self.total_items = 0
        self.completed_items = 0
        self.current_item = ""
        self.start_time: Optional[datetime] = None
        self.last_update_time: Optional[datetime] = None
        
        # Rate calculation
        self.rate_window = deque(maxlen=10)  # Keep last 10 measurements
        self.last_rate_update = 0
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Display state
        self.last_display_time = 0
        self.display_interval = 2.0  # Display updates every 2 seconds
        
        logger.debug("ProgressTracker initialized")
    
    def start_tracking(self, total_items: int) -> None:
        """
        Start tracking progress for a new operation.
        
        Args:
            total_items: Total number of items to process
        """
        with self._lock:
            self.total_items = total_items
            self.completed_items = 0
            self.current_item = ""
            self.start_time = datetime.now()
            self.last_update_time = self.start_time
            self.rate_window.clear()
            self.last_rate_update = time.time()
            self.last_display_time = 0
            
        logger.info(f"Started tracking progress for {total_items} items")
        self._update_progress()
    
    def update_progress(self, completed: int, current_item: str = "") -> None:
        """
        Update progress information.
        
        Args:
            completed: Number of completed items
            current_item: Description of current item being processed
        """
        with self._lock:
            if self.start_time is None:
                logger.warning("Progress tracking not started")
                return
            
            self.completed_items = completed
            self.current_item = current_item
            self.last_update_time = datetime.now()
            
            # Update rate calculation
            current_time = time.time()
            if current_time - self.last_rate_update >= 1.0:  # Update rate every second
                elapsed = current_time - self.last_rate_update
                items_processed = completed - (self.rate_window[-1][1] if self.rate_window else 0)
                rate = items_processed / elapsed if elapsed > 0 else 0
                
                self.rate_window.append((current_time, completed))
                self.last_rate_update = current_time
        
        # Update progress (may trigger callback)
        self._update_progress()
    
    def increment_progress(self, current_item: str = "") -> None:
        """
        Increment progress by one item.
        
        Args:
            current_item: Description of current item being processed
        """
        with self._lock:
            self.update_progress(self.completed_items + 1, current_item)
    
    def get_stats(self) -> ProgressStats:
        """
        Get current progress statistics.
        
        Returns:
            ProgressStats object with current progress information
        """
        with self._lock:
            if self.start_time is None:
                return ProgressStats(
                    total_items=0,
                    completed_items=0,
                    current_item="",
                    start_time=datetime.now(),
                    last_update=datetime.now(),
                    processing_rate=0.0,
                    percentage_complete=0.0
                )
            
            # Calculate processing rate
            processing_rate = self._calculate_rate()
            
            # Calculate ETA
            estimated_completion = self._estimate_completion(processing_rate)
            
            # Calculate percentage
            percentage = (self.completed_items / self.total_items * 100) if self.total_items > 0 else 0
            
            return ProgressStats(
                total_items=self.total_items,
                completed_items=self.completed_items,
                current_item=self.current_item,
                start_time=self.start_time,
                last_update=self.last_update_time or self.start_time,
                processing_rate=processing_rate,
                estimated_completion=estimated_completion,
                percentage_complete=percentage
            )
    
    def _calculate_rate(self) -> float:
        """Calculate current processing rate (items per second)."""
        if not self.rate_window or len(self.rate_window) < 2:
            # Fallback to overall rate
            if self.start_time and self.completed_items > 0:
                elapsed = (datetime.now() - self.start_time).total_seconds()
                return self.completed_items / elapsed if elapsed > 0 else 0
            return 0.0
        
        # Calculate rate from recent measurements
        recent_time, recent_count = self.rate_window[-1]
        old_time, old_count = self.rate_window[0]
        
        time_diff = recent_time - old_time
        count_diff = recent_count - old_count
        
        return count_diff / time_diff if time_diff > 0 else 0.0
    
    def _estimate_completion(self, processing_rate: float) -> Optional[datetime]:
        """Estimate completion time based on current rate."""
        if processing_rate <= 0 or self.completed_items >= self.total_items:
            return None
        
        remaining_items = self.total_items - self.completed_items
        remaining_seconds = remaining_items / processing_rate
        
        return datetime.now() + timedelta(seconds=remaining_seconds)
    
    def _update_progress(self) -> None:
        """Internal method to handle progress updates."""
        current_time = time.time()
        
        # Check if we should display progress
        if current_time - self.last_display_time >= self.display_interval:
            self._display_progress()
            self.last_display_time = current_time
        
        # Call update callback if provided
        if self.update_callback:
            try:
                stats = self.get_stats()
                self.update_callback(stats)
            except Exception as e:
                logger.error(f"Error in progress update callback: {e}")
    
    def _display_progress(self) -> None:
        """Display progress information to console."""
        stats = self.get_stats()
        
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
        
        # Format rate
        rate_str = f"{stats.processing_rate:.2f} items/sec"
        
        # Format current item (truncate if too long)
        current_item = stats.current_item
        if len(current_item) > 50:
            current_item = current_item[:47] + "..."
        
        # Print progress line
        progress_line = (
            f"\r[{bar}] {stats.percentage_complete:6.2f}% "
            f"({stats.completed_items}/{stats.total_items}) "
            f"{rate_str}{eta_str}"
        )
        
        print(progress_line, end="", flush=True)
        
        # Print current item on new line if it's meaningful
        if current_item and current_item != "":
            print(f"\nProcessing: {current_item}", flush=True)
    
    def finish(self, message: str = "Processing complete") -> None:
        """
        Mark progress as finished and display final statistics.
        
        Args:
            message: Final message to display
        """
        with self._lock:
            if self.start_time is None:
                return
            
            self.completed_items = self.total_items
            self.current_item = ""
            self.last_update_time = datetime.now()
        
        # Display final progress
        print()  # New line after progress bar
        stats = self.get_stats()
        
        elapsed = stats.last_update - stats.start_time
        elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
        
        print(f"\n{message}")
        print(f"Total items: {stats.total_items}")
        print(f"Completed: {stats.completed_items}")
        print(f"Time elapsed: {elapsed_str}")
        print(f"Average rate: {stats.processing_rate:.2f} items/sec")
        
        logger.info(f"Progress tracking finished: {message}")
    
    def reset(self) -> None:
        """Reset progress tracker to initial state."""
        with self._lock:
            self.total_items = 0
            self.completed_items = 0
            self.current_item = ""
            self.start_time = None
            self.last_update_time = None
            self.rate_window.clear()
            self.last_rate_update = 0
            self.last_display_time = 0
        
        logger.debug("ProgressTracker reset")
    
    def is_active(self) -> bool:
        """Check if progress tracking is currently active."""
        with self._lock:
            return self.start_time is not None and self.completed_items < self.total_items
    
    def get_elapsed_time(self) -> Optional[timedelta]:
        """Get elapsed time since tracking started."""
        with self._lock:
            if self.start_time is None:
                return None
            return datetime.now() - self.start_time
    
    def get_remaining_time(self) -> Optional[timedelta]:
        """Get estimated remaining time."""
        stats = self.get_stats()
        if stats.estimated_completion:
            remaining = stats.estimated_completion - datetime.now()
            return remaining if remaining.total_seconds() > 0 else timedelta(0)
        return None