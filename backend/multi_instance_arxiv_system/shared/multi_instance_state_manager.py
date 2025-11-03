"""
Multi-Instance State Manager for arXiv RAG Enhancement system.

Extends the existing StateManager to support multiple scholar instances with
complete isolation and instance-specific state management.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Import base StateManager
from arxiv_rag_enhancement.shared.state_manager import StateManager, FileLock
from .multi_instance_data_models import MultiInstanceProcessingState, InstanceConfig

logger = logging.getLogger(__name__)


class MultiInstanceStateManager(StateManager):
    """Extended StateManager with multi-instance support and isolation."""
    
    def __init__(self, base_state_dir: Path, instance_name: str):
        """
        Initialize MultiInstanceStateManager.
        
        Args:
            base_state_dir: Base directory for all instance state files
            instance_name: Name of the scholar instance (e.g., 'ai_scholar', 'quant_scholar')
        """
        self.instance_name = instance_name
        self.base_state_dir = Path(base_state_dir)
        
        # Create instance-specific state directory
        instance_state_dir = self.base_state_dir / instance_name
        
        # Initialize parent with instance-specific directory
        super().__init__(instance_state_dir)
        
        logger.info(f"MultiInstanceStateManager initialized for instance '{instance_name}' "
                   f"with state directory: {self.state_dir}")
    
    def save_instance_state(self, 
                          processor_id: str, 
                          state: MultiInstanceProcessingState) -> bool:
        """
        Save instance-specific processing state.
        
        Args:
            processor_id: Unique identifier for the processor
            state: Multi-instance processing state to save
            
        Returns:
            True if successful, False otherwise
        """
        # Ensure instance name is set
        state.instance_name = self.instance_name
        
        # Use parent's save_state method
        return self.save_state(processor_id, state)
    
    def load_instance_state(self, processor_id: str) -> Optional[MultiInstanceProcessingState]:
        """
        Load instance-specific processing state.
        
        Args:
            processor_id: Unique identifier for the processor
            
        Returns:
            MultiInstanceProcessingState if found and valid, None otherwise
        """
        # Load base state
        base_state = self.load_state(processor_id)
        if not base_state:
            return None
        
        # Convert to multi-instance state if needed
        if isinstance(base_state, MultiInstanceProcessingState):
            return base_state
        
        # Convert base state to multi-instance state
        return MultiInstanceProcessingState(
            processor_id=base_state.processor_id,
            start_time=base_state.start_time,
            last_update=base_state.last_update,
            processed_files=base_state.processed_files,
            failed_files=base_state.failed_files,
            current_batch=base_state.current_batch,
            total_files=base_state.total_files,
            processing_stats=base_state.processing_stats,
            metadata=base_state.metadata,
            instance_name=self.instance_name
        )
    
    def get_instance_lock(self, processor_id: str) -> FileLock:
        """
        Get an instance-specific file lock for a processor.
        
        Args:
            processor_id: Unique identifier for the processor
            
        Returns:
            FileLock instance with instance-specific naming
        """
        # Create instance-specific lock file name
        instance_processor_id = f"{self.instance_name}_{processor_id}"
        lock_file = self.state_dir / "locks" / f"{instance_processor_id}.lock"
        return FileLock(lock_file)
    
    def list_instance_processors(self) -> Dict[str, Dict[str, Any]]:
        """
        List all active processors for this instance.
        
        Returns:
            Dictionary mapping processor_id to state summary for this instance
        """
        active_processors = self.list_active_processors()
        
        # Add instance information to each processor summary
        for processor_id, summary in active_processors.items():
            summary['instance_name'] = self.instance_name
        
        return active_processors
    
    def get_instance_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of this instance's state.
        
        Returns:
            Dictionary with instance state summary
        """
        active_processors = self.list_instance_processors()
        
        # Calculate aggregate statistics
        total_processors = len(active_processors)
        total_files = sum(p.get('total_files', 0) for p in active_processors.values())
        processed_files = sum(p.get('processed_count', 0) for p in active_processors.values())
        failed_files = sum(p.get('failed_count', 0) for p in active_processors.values())
        
        return {
            'instance_name': self.instance_name,
            'state_directory': str(self.state_dir),
            'active_processors': total_processors,
            'total_files': total_files,
            'processed_files': processed_files,
            'failed_files': failed_files,
            'processors': active_processors,
            'last_updated': datetime.now().isoformat()
        }
    
    def cleanup_instance_states(self, max_age_days: int = 30) -> int:
        """
        Clean up old state files for this instance.
        
        Args:
            max_age_days: Maximum age in days for completed state files
            
        Returns:
            Number of files cleaned up
        """
        cleaned_count = self.cleanup_old_states(max_age_days)
        logger.info(f"Cleaned up {cleaned_count} old state files for instance '{self.instance_name}'")
        return cleaned_count
    
    def is_instance_processor_running(self, processor_id: str) -> bool:
        """
        Check if a processor is currently running for this instance.
        
        Args:
            processor_id: Unique identifier for the processor
            
        Returns:
            True if processor appears to be running, False otherwise
        """
        return self.is_processor_running(processor_id)
    
    def create_instance_processor_id(self, base_processor_id: str) -> str:
        """
        Create an instance-specific processor ID.
        
        Args:
            base_processor_id: Base processor identifier
            
        Returns:
            Instance-specific processor ID
        """
        return f"{self.instance_name}_{base_processor_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def validate_instance_state(self, processor_id: str) -> List[str]:
        """
        Validate the state for a specific processor in this instance.
        
        Args:
            processor_id: Unique identifier for the processor
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        state = self.load_instance_state(processor_id)
        if not state:
            errors.append(f"No state found for processor {processor_id}")
            return errors
        
        # Validate instance name matches
        if state.instance_name != self.instance_name:
            errors.append(f"State instance name '{state.instance_name}' does not match "
                         f"manager instance name '{self.instance_name}'")
        
        # Validate required fields
        if not state.processor_id:
            errors.append("Processor ID is missing")
        
        if not state.start_time:
            errors.append("Start time is missing")
        
        if state.total_files < 0:
            errors.append("Total files count is negative")
        
        if len(state.processed_files) > state.total_files:
            errors.append("Processed files count exceeds total files")
        
        # Validate processing stats
        if state.processing_stats:
            if state.processing_stats.processed_count != len(state.processed_files):
                errors.append("Processing stats count does not match processed files set")
            
            if state.processing_stats.failed_count != len(state.failed_files):
                errors.append("Processing stats failed count does not match failed files dict")
        
        return errors
    
    def export_instance_state_report(self, output_path: Path) -> bool:
        """
        Export comprehensive state report for this instance.
        
        Args:
            output_path: Path to save the state report
            
        Returns:
            True if successful, False otherwise
        """
        try:
            summary = self.get_instance_summary()
            
            # Add detailed processor information
            detailed_processors = {}
            for processor_id in summary['processors'].keys():
                state = self.load_instance_state(processor_id)
                if state:
                    detailed_processors[processor_id] = {
                        'summary': summary['processors'][processor_id],
                        'detailed_state': state.to_dict(),
                        'validation_errors': self.validate_instance_state(processor_id)
                    }
            
            report = {
                'instance_name': self.instance_name,
                'report_generated': datetime.now().isoformat(),
                'summary': summary,
                'detailed_processors': detailed_processors,
                'state_directory_info': {
                    'path': str(self.state_dir),
                    'exists': self.state_dir.exists(),
                    'active_dir': str(self.state_dir / "active"),
                    'completed_dir': str(self.state_dir / "completed"),
                    'locks_dir': str(self.state_dir / "locks")
                }
            }
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                import json
                json.dump(report, f, indent=2)
            
            logger.info(f"Instance state report exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export instance state report: {e}")
            return False


class GlobalStateManager:
    """Manages state across all scholar instances."""
    
    def __init__(self, base_state_dir: Path):
        """
        Initialize GlobalStateManager.
        
        Args:
            base_state_dir: Base directory for all instance state files
        """
        self.base_state_dir = Path(base_state_dir)
        self.base_state_dir.mkdir(parents=True, exist_ok=True)
        
        # Instance managers cache
        self._instance_managers: Dict[str, MultiInstanceStateManager] = {}
        
        logger.info(f"GlobalStateManager initialized with base directory: {self.base_state_dir}")
    
    def get_instance_manager(self, instance_name: str) -> MultiInstanceStateManager:
        """
        Get or create a state manager for a specific instance.
        
        Args:
            instance_name: Name of the scholar instance
            
        Returns:
            MultiInstanceStateManager for the specified instance
        """
        if instance_name not in self._instance_managers:
            self._instance_managers[instance_name] = MultiInstanceStateManager(
                self.base_state_dir, instance_name
            )
        
        return self._instance_managers[instance_name]
    
    def list_all_instances(self) -> List[str]:
        """
        List all scholar instances that have state directories.
        
        Returns:
            List of instance names
        """
        instances = []
        
        try:
            for item in self.base_state_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    instances.append(item.name)
        except Exception as e:
            logger.error(f"Failed to list instances: {e}")
        
        return sorted(instances)
    
    def get_global_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all instances and their states.
        
        Returns:
            Dictionary with global state summary
        """
        instances = self.list_all_instances()
        instance_summaries = {}
        
        for instance_name in instances:
            try:
                manager = self.get_instance_manager(instance_name)
                instance_summaries[instance_name] = manager.get_instance_summary()
            except Exception as e:
                logger.error(f"Failed to get summary for instance {instance_name}: {e}")
                instance_summaries[instance_name] = {
                    'error': str(e),
                    'instance_name': instance_name
                }
        
        # Calculate global statistics
        total_processors = sum(
            summary.get('active_processors', 0) 
            for summary in instance_summaries.values() 
            if 'error' not in summary
        )
        
        total_files = sum(
            summary.get('total_files', 0) 
            for summary in instance_summaries.values() 
            if 'error' not in summary
        )
        
        processed_files = sum(
            summary.get('processed_files', 0) 
            for summary in instance_summaries.values() 
            if 'error' not in summary
        )
        
        return {
            'base_state_directory': str(self.base_state_dir),
            'total_instances': len(instances),
            'total_active_processors': total_processors,
            'total_files': total_files,
            'total_processed_files': processed_files,
            'instances': instance_summaries,
            'last_updated': datetime.now().isoformat()
        }
    
    def cleanup_all_instances(self, max_age_days: int = 30) -> Dict[str, int]:
        """
        Clean up old state files for all instances.
        
        Args:
            max_age_days: Maximum age in days for completed state files
            
        Returns:
            Dictionary mapping instance names to cleanup counts
        """
        cleanup_results = {}
        instances = self.list_all_instances()
        
        for instance_name in instances:
            try:
                manager = self.get_instance_manager(instance_name)
                cleanup_count = manager.cleanup_instance_states(max_age_days)
                cleanup_results[instance_name] = cleanup_count
            except Exception as e:
                logger.error(f"Failed to cleanup instance {instance_name}: {e}")
                cleanup_results[instance_name] = -1
        
        return cleanup_results