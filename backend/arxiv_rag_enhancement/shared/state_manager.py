"""
State Manager for arXiv RAG Enhancement system.

Handles persistence of processing state for resume functionality, including
file locking to prevent concurrent access and state corruption.
"""

import json
import logging
import fcntl
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import tempfile
import shutil

from .data_models import ProcessingState

logger = logging.getLogger(__name__)


class FileLock:
    """Simple file-based locking mechanism."""
    
    def __init__(self, lock_file: Path):
        self.lock_file = lock_file
        self.lock_fd = None
    
    def __enter__(self):
        """Acquire the lock."""
        try:
            # Create lock file if it doesn't exist
            self.lock_file.parent.mkdir(parents=True, exist_ok=True)
            self.lock_fd = open(self.lock_file, 'w')
            
            # Try to acquire exclusive lock (non-blocking)
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Write process info to lock file
            lock_info = {
                'pid': os.getpid(),
                'timestamp': datetime.now().isoformat(),
                'hostname': os.uname().nodename if hasattr(os, 'uname') else 'unknown'
            }
            self.lock_fd.write(json.dumps(lock_info, indent=2))
            self.lock_fd.flush()
            
            logger.debug(f"Acquired lock: {self.lock_file}")
            return self
            
        except (IOError, OSError) as e:
            if self.lock_fd:
                self.lock_fd.close()
                self.lock_fd = None
            raise RuntimeError(f"Failed to acquire lock {self.lock_file}: {e}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release the lock."""
        if self.lock_fd:
            try:
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                self.lock_fd.close()
                
                # Remove lock file
                if self.lock_file.exists():
                    self.lock_file.unlink()
                
                logger.debug(f"Released lock: {self.lock_file}")
                
            except Exception as e:
                logger.error(f"Error releasing lock {self.lock_file}: {e}")
            finally:
                self.lock_fd = None


class StateManager:
    """Manages processing state persistence and resume functionality."""
    
    def __init__(self, state_dir: Path):
        """
        Initialize StateManager.
        
        Args:
            state_dir: Directory to store state files
        """
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.state_dir / "active").mkdir(exist_ok=True)
        (self.state_dir / "completed").mkdir(exist_ok=True)
        (self.state_dir / "locks").mkdir(exist_ok=True)
        
        logger.info(f"StateManager initialized with state directory: {self.state_dir}")
    
    def _get_state_file(self, processor_id: str) -> Path:
        """Get the state file path for a processor."""
        return self.state_dir / "active" / f"{processor_id}.json"
    
    def _get_completed_state_file(self, processor_id: str) -> Path:
        """Get the completed state file path for a processor."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.state_dir / "completed" / f"{processor_id}_{timestamp}.json"
    
    def _get_lock_file(self, processor_id: str) -> Path:
        """Get the lock file path for a processor."""
        return self.state_dir / "locks" / f"{processor_id}.lock"
    
    def save_state(self, processor_id: str, state: ProcessingState) -> bool:
        """
        Save processing state to file.
        
        Args:
            processor_id: Unique identifier for the processor
            state: Processing state to save
            
        Returns:
            True if successful, False otherwise
        """
        state_file = self._get_state_file(processor_id)
        temp_file = state_file.with_suffix('.tmp')
        
        try:
            # Update last_update timestamp
            state.last_update = datetime.now()
            
            # Write to temporary file first
            with open(temp_file, 'w') as f:
                json.dump(state.to_dict(), f, indent=2)
            
            # Atomic move to final location
            shutil.move(str(temp_file), str(state_file))
            
            logger.debug(f"Saved state for processor {processor_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save state for processor {processor_id}: {e}")
            
            # Clean up temp file if it exists
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass
            
            return False
    
    def load_state(self, processor_id: str) -> Optional[ProcessingState]:
        """
        Load processing state from file.
        
        Args:
            processor_id: Unique identifier for the processor
            
        Returns:
            ProcessingState if found and valid, None otherwise
        """
        state_file = self._get_state_file(processor_id)
        
        try:
            if not state_file.exists():
                logger.debug(f"No state file found for processor {processor_id}")
                return None
            
            with open(state_file, 'r') as f:
                data = json.load(f)
            
            state = ProcessingState.from_dict(data)
            logger.info(f"Loaded state for processor {processor_id}")
            return state
            
        except Exception as e:
            logger.error(f"Failed to load state for processor {processor_id}: {e}")
            return None
    
    def clear_state(self, processor_id: str) -> bool:
        """
        Clear processing state (move to completed).
        
        Args:
            processor_id: Unique identifier for the processor
            
        Returns:
            True if successful, False otherwise
        """
        state_file = self._get_state_file(processor_id)
        
        try:
            if state_file.exists():
                # Move to completed directory with timestamp
                completed_file = self._get_completed_state_file(processor_id)
                shutil.move(str(state_file), str(completed_file))
                logger.info(f"Moved state for processor {processor_id} to completed")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear state for processor {processor_id}: {e}")
            return False
    
    def get_lock(self, processor_id: str) -> FileLock:
        """
        Get a file lock for a processor.
        
        Args:
            processor_id: Unique identifier for the processor
            
        Returns:
            FileLock instance
        """
        lock_file = self._get_lock_file(processor_id)
        return FileLock(lock_file)
    
    def list_active_processors(self) -> Dict[str, Dict[str, Any]]:
        """
        List all active processors with their state information.
        
        Returns:
            Dictionary mapping processor_id to state summary
        """
        active_processors = {}
        active_dir = self.state_dir / "active"
        
        try:
            for state_file in active_dir.glob("*.json"):
                processor_id = state_file.stem
                
                try:
                    with open(state_file, 'r') as f:
                        data = json.load(f)
                    
                    # Extract summary information
                    summary = {
                        'processor_id': processor_id,
                        'start_time': data.get('start_time'),
                        'last_update': data.get('last_update'),
                        'total_files': data.get('total_files', 0),
                        'processed_count': data.get('processing_stats', {}).get('processed_count', 0),
                        'failed_count': data.get('processing_stats', {}).get('failed_count', 0),
                        'current_batch': data.get('current_batch', 0)
                    }
                    
                    active_processors[processor_id] = summary
                    
                except Exception as e:
                    logger.warning(f"Failed to read state file {state_file}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to list active processors: {e}")
        
        return active_processors
    
    def cleanup_old_states(self, max_age_days: int = 30) -> int:
        """
        Clean up old completed state files.
        
        Args:
            max_age_days: Maximum age in days for completed state files
            
        Returns:
            Number of files cleaned up
        """
        cleaned_count = 0
        completed_dir = self.state_dir / "completed"
        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)
        
        try:
            for state_file in completed_dir.glob("*.json"):
                try:
                    if state_file.stat().st_mtime < cutoff_time:
                        state_file.unlink()
                        cleaned_count += 1
                        logger.debug(f"Cleaned up old state file: {state_file}")
                        
                except Exception as e:
                    logger.warning(f"Failed to clean up state file {state_file}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to cleanup old states: {e}")
        
        logger.info(f"Cleaned up {cleaned_count} old state files")
        return cleaned_count
    
    def get_state_summary(self, processor_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of the current state for a processor.
        
        Args:
            processor_id: Unique identifier for the processor
            
        Returns:
            State summary dictionary or None if not found
        """
        state = self.load_state(processor_id)
        if not state:
            return None
        
        return {
            'processor_id': state.processor_id,
            'start_time': state.start_time.isoformat(),
            'last_update': state.last_update.isoformat(),
            'total_files': state.total_files,
            'processed_files': len(state.processed_files),
            'failed_files': len(state.failed_files),
            'current_batch': state.current_batch,
            'processing_rate': state.processing_stats.processing_rate,
            'estimated_completion': (
                state.processing_stats.estimated_completion.isoformat()
                if state.processing_stats.estimated_completion else None
            ),
            'percentage_complete': (
                (len(state.processed_files) / state.total_files * 100)
                if state.total_files > 0 else 0
            )
        }
    
    def is_processor_running(self, processor_id: str) -> bool:
        """
        Check if a processor is currently running (has an active lock).
        
        Args:
            processor_id: Unique identifier for the processor
            
        Returns:
            True if processor appears to be running, False otherwise
        """
        lock_file = self._get_lock_file(processor_id)
        
        if not lock_file.exists():
            return False
        
        try:
            # Try to acquire lock (non-blocking)
            with open(lock_file, 'r') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                # If we got here, the lock was available (not running)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                return False
                
        except (IOError, OSError):
            # Lock is held by another process
            return True