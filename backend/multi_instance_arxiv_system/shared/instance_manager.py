"""
Instance Manager for multi-instance ArXiv system.

Provides centralized management of scholar instances, including configuration
loading, instance lifecycle management, and coordination between instances.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import yaml
import json

from .multi_instance_data_models import InstanceConfig, InstanceStats
from .multi_instance_state_manager import MultiInstanceStateManager, GlobalStateManager
from .multi_instance_progress_tracker import MultiInstanceProgressTracker, GlobalProgressTracker
from .multi_instance_error_handler import MultiInstanceErrorHandler, GlobalErrorHandler

logger = logging.getLogger(__name__)


class InstanceManager:
    """Manages individual scholar instances and their components."""
    
    def __init__(self, 
                 instance_name: str,
                 config_path: Optional[Path] = None,
                 base_state_dir: Optional[Path] = None,
                 base_error_dir: Optional[Path] = None):
        """
        Initialize InstanceManager.
        
        Args:
            instance_name: Name of the scholar instance
            config_path: Path to instance configuration file
            base_state_dir: Base directory for state management
            base_error_dir: Base directory for error logging
        """
        self.instance_name = instance_name
        self.config_path = config_path
        
        # Set default directories if not provided
        if base_state_dir is None:
            base_state_dir = Path("/datapool/aischolar/multi-instance-state")
        if base_error_dir is None:
            base_error_dir = Path("/datapool/aischolar/multi-instance-errors")
        
        self.base_state_dir = Path(base_state_dir)
        self.base_error_dir = Path(base_error_dir)
        
        # Instance configuration
        self.config: Optional[InstanceConfig] = None
        
        # Instance components
        self.state_manager: Optional[MultiInstanceStateManager] = None
        self.progress_tracker: Optional[MultiInstanceProgressTracker] = None
        self.error_handler: Optional[MultiInstanceErrorHandler] = None
        
        # Instance status
        self.is_initialized = False
        self.last_activity = datetime.now()
        
        logger.info(f"InstanceManager created for '{instance_name}'")
    
    def initialize(self) -> bool:
        """
        Initialize the instance with configuration and components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Load configuration
            if not self._load_configuration():
                logger.error(f"Failed to load configuration for instance '{self.instance_name}'")
                return False
            
            # Initialize components
            self._initialize_components()
            
            # Validate instance setup
            validation_errors = self._validate_instance()
            if validation_errors:
                logger.error(f"Instance validation failed: {validation_errors}")
                return False
            
            self.is_initialized = True
            self.last_activity = datetime.now()
            
            logger.info(f"Instance '{self.instance_name}' initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize instance '{self.instance_name}': {e}")
            return False
    
    def _load_configuration(self) -> bool:
        """Load instance configuration from file or create default."""
        try:
            if self.config_path and self.config_path.exists():
                # Load from file
                with open(self.config_path, 'r') as f:
                    if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                        config_data = yaml.safe_load(f)
                    else:
                        config_data = json.load(f)
                
                self.config = InstanceConfig.from_dict(config_data)
                logger.info(f"Loaded configuration from {self.config_path}")
                
            else:
                # Create default configuration
                self.config = self._create_default_config()
                logger.info(f"Created default configuration for instance '{self.instance_name}'")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False
    
    def _create_default_config(self) -> InstanceConfig:
        """Create default configuration for the instance."""
        from .multi_instance_data_models import (
            StoragePaths, ProcessingConfig, VectorStoreConfig, NotificationConfig
        )
        
        # Determine default settings based on instance name
        if self.instance_name == 'ai_scholar':
            arxiv_categories = [
                'cond-mat', 'gr-qc', 'hep-ph', 'hep-th', 'math', 
                'math-ph', 'physics', 'q-alg', 'quant-ph'
            ]
            display_name = "AI Scholar"
            description = "General AI and Physics Research Papers"
            base_path = "/datapool/aischolar/ai-scholar-arxiv-dataset"
            
        elif self.instance_name == 'quant_scholar':
            arxiv_categories = [
                'econ.EM', 'econ.GN', 'econ.TH', 'eess.SY', 'math.ST', 
                'math.PR', 'math.OC', 'q-fin.*', 'stat.*'
            ]
            display_name = "Quant Scholar"
            description = "Quantitative Finance and Statistics Research Papers"
            base_path = "/datapool/aischolar/quant-scholar-dataset"
            
        else:
            # Generic defaults
            arxiv_categories = ['cs.AI', 'cs.LG', 'cs.CL']
            display_name = self.instance_name.replace('_', ' ').title()
            description = f"Research papers for {display_name}"
            base_path = f"/datapool/aischolar/{self.instance_name}-dataset"
        
        return InstanceConfig(
            instance_name=self.instance_name,
            display_name=display_name,
            description=description,
            arxiv_categories=arxiv_categories,
            journal_sources=[],
            storage_paths=StoragePaths(
                pdf_directory=f"{base_path}/pdf",
                processed_directory=f"{base_path}/processed",
                state_directory=f"{base_path}/state",
                error_log_directory=f"{base_path}/errors",
                archive_directory=f"{base_path}/archive"
            ),
            vector_store_config=VectorStoreConfig(
                collection_name=f"{self.instance_name}_papers",
                embedding_model="all-MiniLM-L6-v2",
                host="localhost",
                port=8082
            ),
            processing_config=ProcessingConfig(
                batch_size=20,
                max_concurrent_downloads=5,
                max_concurrent_processing=3,
                retry_attempts=3,
                timeout_seconds=300
            ),
            notification_config=NotificationConfig(
                enabled=False,
                recipients=[],
                smtp_server="localhost",
                smtp_port=587
            )
        )
    
    def _initialize_components(self) -> None:
        """Initialize instance components."""
        # Initialize state manager
        self.state_manager = MultiInstanceStateManager(
            self.base_state_dir, self.instance_name
        )
        
        # Initialize progress tracker
        self.progress_tracker = MultiInstanceProgressTracker(
            instance_name=self.instance_name,
            update_callback=None,
            update_interval=1.0
        )
        
        # Initialize error handler (will be created when needed with processor_id)
        # self.error_handler will be created in get_error_handler()
        
        logger.info(f"Components initialized for instance '{self.instance_name}'")
    
    def _validate_instance(self) -> List[str]:
        """Validate instance configuration and setup."""
        errors = []
        
        if not self.config:
            errors.append("Configuration not loaded")
            return errors
        
        # Validate configuration
        if not self.config.instance_name:
            errors.append("Instance name not specified")
        
        if not self.config.arxiv_categories:
            errors.append("No arXiv categories specified")
        
        # Validate storage paths
        try:
            storage_paths = self.config.storage_paths
            for path_name, path_value in [
                ('pdf_directory', storage_paths.pdf_directory),
                ('processed_directory', storage_paths.processed_directory),
                ('state_directory', storage_paths.state_directory),
                ('error_log_directory', storage_paths.error_log_directory)
            ]:
                if not path_value:
                    errors.append(f"Storage path '{path_name}' not specified")
        except Exception as e:
            errors.append(f"Invalid storage paths configuration: {e}")
        
        # Validate vector store configuration
        try:
            vs_config = self.config.vector_store_config
            if not vs_config.collection_name:
                errors.append("Vector store collection name not specified")
            if vs_config.port <= 0 or vs_config.port > 65535:
                errors.append("Invalid vector store port")
        except Exception as e:
            errors.append(f"Invalid vector store configuration: {e}")
        
        return errors
    
    def get_error_handler(self, processor_id: str) -> MultiInstanceErrorHandler:
        """
        Get or create error handler for a specific processor.
        
        Args:
            processor_id: Unique identifier for the processor
            
        Returns:
            MultiInstanceErrorHandler for the processor
        """
        if not self.error_handler or self.error_handler.processor_id != f"{self.instance_name}_{processor_id}":
            self.error_handler = MultiInstanceErrorHandler(
                self.base_error_dir, self.instance_name, processor_id
            )
        
        return self.error_handler
    
    def create_storage_directories(self) -> bool:
        """
        Create all required storage directories for the instance.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.config:
            logger.error("Configuration not loaded")
            return False
        
        try:
            storage_paths = self.config.storage_paths
            
            directories = [
                storage_paths.pdf_directory,
                storage_paths.processed_directory,
                storage_paths.state_directory,
                storage_paths.error_log_directory,
                storage_paths.archive_directory
            ]
            
            for directory in directories:
                Path(directory).mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {directory}")
            
            logger.info(f"Storage directories created for instance '{self.instance_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create storage directories: {e}")
            return False
    
    def get_instance_stats(self) -> InstanceStats:
        """
        Get current statistics for this instance.
        
        Returns:
            InstanceStats object with current instance information
        """
        if not self.is_initialized or not self.config:
            return InstanceStats(
                instance_name=self.instance_name,
                total_papers=0,
                processed_papers=0,
                failed_papers=0,
                storage_used_mb=0,
                last_update=datetime.now(),
                processing_rate=0.0,
                error_rate=0.0
            )
        
        # Get statistics from components
        if self.progress_tracker:
            return self.progress_tracker.get_instance_stats()
        
        # Return basic stats if progress tracker not available
        return InstanceStats(
            instance_name=self.instance_name,
            total_papers=0,
            processed_papers=0,
            failed_papers=0,
            storage_used_mb=0,
            last_update=self.last_activity,
            processing_rate=0.0,
            error_rate=0.0
        )
    
    def get_instance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive summary of instance status.
        
        Returns:
            Dictionary with instance summary information
        """
        summary = {
            'instance_name': self.instance_name,
            'is_initialized': self.is_initialized,
            'last_activity': self.last_activity.isoformat(),
            'config_loaded': self.config is not None,
            'components': {
                'state_manager': self.state_manager is not None,
                'progress_tracker': self.progress_tracker is not None,
                'error_handler': self.error_handler is not None
            }
        }
        
        if self.config:
            summary['configuration'] = {
                'display_name': self.config.display_name,
                'description': self.config.description,
                'arxiv_categories': self.config.arxiv_categories,
                'journal_sources': self.config.journal_sources,
                'vector_store_collection': self.config.vector_store_config.collection_name
            }
        
        if self.is_initialized:
            summary['stats'] = self.get_instance_stats().to_dict()
            
            if self.state_manager:
                summary['state_info'] = self.state_manager.get_instance_summary()
        
        return summary
    
    def save_configuration(self, output_path: Optional[Path] = None) -> bool:
        """
        Save current configuration to file.
        
        Args:
            output_path: Optional output file path
            
        Returns:
            True if successful, False otherwise
        """
        if not self.config:
            logger.error("No configuration to save")
            return False
        
        try:
            if output_path is None:
                output_path = self.config_path or Path(f"configs/{self.instance_name}.yaml")
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = self.config.to_dict()
            
            with open(output_path, 'w') as f:
                if output_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(config_data, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config_data, f, indent=2)
            
            logger.info(f"Configuration saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def shutdown(self) -> None:
        """Shutdown the instance and cleanup resources."""
        logger.info(f"Shutting down instance '{self.instance_name}'")
        
        # Cleanup components
        if self.progress_tracker:
            self.progress_tracker.reset()
        
        if self.error_handler:
            self.error_handler.clear_errors()
        
        # Reset state
        self.is_initialized = False
        self.last_activity = datetime.now()
        
        logger.info(f"Instance '{self.instance_name}' shutdown complete")


class MultiInstanceManager:
    """Manages multiple scholar instances and provides coordination."""
    
    def __init__(self, 
                 base_config_dir: Path,
                 base_state_dir: Path,
                 base_error_dir: Path):
        """
        Initialize MultiInstanceManager.
        
        Args:
            base_config_dir: Base directory for instance configurations
            base_state_dir: Base directory for state management
            base_error_dir: Base directory for error logging
        """
        self.base_config_dir = Path(base_config_dir)
        self.base_state_dir = Path(base_state_dir)
        self.base_error_dir = Path(base_error_dir)
        
        # Create base directories
        self.base_config_dir.mkdir(parents=True, exist_ok=True)
        self.base_state_dir.mkdir(parents=True, exist_ok=True)
        self.base_error_dir.mkdir(parents=True, exist_ok=True)
        
        # Instance managers
        self.instances: Dict[str, InstanceManager] = {}
        
        # Global managers
        self.global_state_manager = GlobalStateManager(base_state_dir)
        self.global_progress_tracker = GlobalProgressTracker()
        self.global_error_handler = GlobalErrorHandler(base_error_dir)
        
        logger.info("MultiInstanceManager initialized")
    
    def register_instance(self, instance_name: str, config_path: Optional[Path] = None) -> InstanceManager:
        """
        Register and initialize a new instance.
        
        Args:
            instance_name: Name of the scholar instance
            config_path: Optional path to configuration file
            
        Returns:
            InstanceManager for the registered instance
        """
        if instance_name in self.instances:
            logger.warning(f"Instance '{instance_name}' already registered")
            return self.instances[instance_name]
        
        # Determine config path if not provided
        if config_path is None:
            config_path = self.base_config_dir / f"{instance_name}.yaml"
        
        # Create instance manager
        instance_manager = InstanceManager(
            instance_name=instance_name,
            config_path=config_path,
            base_state_dir=self.base_state_dir,
            base_error_dir=self.base_error_dir
        )
        
        # Initialize instance
        if instance_manager.initialize():
            self.instances[instance_name] = instance_manager
            
            # Register with global trackers
            self.global_progress_tracker.register_instance(instance_name)
            
            logger.info(f"Instance '{instance_name}' registered successfully")
        else:
            logger.error(f"Failed to initialize instance '{instance_name}'")
            raise RuntimeError(f"Instance initialization failed: {instance_name}")
        
        return instance_manager
    
    def get_instance(self, instance_name: str) -> Optional[InstanceManager]:
        """
        Get an instance manager by name.
        
        Args:
            instance_name: Name of the instance
            
        Returns:
            InstanceManager if found, None otherwise
        """
        return self.instances.get(instance_name)
    
    def list_instances(self) -> List[str]:
        """
        List all registered instance names.
        
        Returns:
            List of instance names
        """
        return list(self.instances.keys())
    
    def get_global_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive summary of all instances.
        
        Returns:
            Dictionary with global summary information
        """
        instance_summaries = {}
        
        for instance_name, instance_manager in self.instances.items():
            try:
                instance_summaries[instance_name] = instance_manager.get_instance_summary()
            except Exception as e:
                logger.error(f"Failed to get summary for instance {instance_name}: {e}")
                instance_summaries[instance_name] = {'error': str(e)}
        
        # Get global statistics
        progress_summary = self.global_progress_tracker.get_global_summary()
        state_summary = self.global_state_manager.get_global_summary()
        error_summary = self.global_error_handler.get_global_error_summary()
        
        return {
            'total_instances': len(self.instances),
            'instances': instance_summaries,
            'global_progress': progress_summary,
            'global_state': state_summary,
            'global_errors': error_summary,
            'last_updated': datetime.now().isoformat()
        }
    
    def shutdown_all_instances(self) -> None:
        """Shutdown all registered instances."""
        logger.info("Shutting down all instances")
        
        for instance_name, instance_manager in self.instances.items():
            try:
                instance_manager.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down instance {instance_name}: {e}")
        
        self.instances.clear()
        logger.info("All instances shutdown complete")