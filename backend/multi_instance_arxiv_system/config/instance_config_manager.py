"""
Instance Configuration Manager for multi-instance ArXiv system.

Extends the existing ConfigManager to support multiple scholar instances with
YAML configuration files, validation, and environment variable overrides.
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from datetime import datetime

# Import base ConfigManager
try:
    from arxiv_rag_enhancement.config.config_manager import ConfigManager
except ImportError:
    # Fallback for when running from different directory
    import sys
    from pathlib import Path
    backend_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(backend_dir))
    from arxiv_rag_enhancement.config.config_manager import ConfigManager
from ..shared.multi_instance_data_models import InstanceConfig
from .default_instance_configs import DEFAULT_AI_SCHOLAR_CONFIG, DEFAULT_QUANT_SCHOLAR_CONFIG

logger = logging.getLogger(__name__)


class InstanceConfigManager(ConfigManager):
    """Extended ConfigManager with multi-instance support and YAML configuration."""
    
    def __init__(self, 
                 instance_name: str,
                 config_file: Optional[Union[str, Path]] = None,
                 config_dir: Optional[Union[str, Path]] = None):
        """
        Initialize InstanceConfigManager.
        
        Args:
            instance_name: Name of the scholar instance
            config_file: Optional path to specific configuration file
            config_dir: Optional directory containing configuration files
        """
        self.instance_name = instance_name
        self.config_dir = Path(config_dir) if config_dir else Path("configs")
        
        # Determine config file path
        if config_file:
            self.config_file = Path(config_file)
        else:
            self.config_file = self.config_dir / f"{instance_name}.yaml"
        
        # Load default configuration for instance
        self.default_config = self._get_default_config(instance_name)
        
        # Initialize parent with instance-specific config
        super().__init__(self.config_file)
        
        logger.info(f"InstanceConfigManager initialized for '{instance_name}' "
                   f"with config file: {self.config_file}")
    
    def _get_default_config(self, instance_name: str) -> Dict[str, Any]:
        """Get default configuration for the specified instance."""
        if instance_name == 'ai_scholar':
            return DEFAULT_AI_SCHOLAR_CONFIG.copy()
        elif instance_name == 'quant_scholar':
            return DEFAULT_QUANT_SCHOLAR_CONFIG.copy()
        else:
            # Generic default configuration
            return self._create_generic_default_config(instance_name)
    
    def _create_generic_default_config(self, instance_name: str) -> Dict[str, Any]:
        """Create a generic default configuration for custom instances."""
        return {
            'instance': {
                'name': instance_name,
                'display_name': instance_name.replace('_', ' ').title(),
                'description': f'Research papers for {instance_name}'
            },
            'data_sources': {
                'arxiv': {
                    'categories': ['cs.AI', 'cs.LG', 'cs.CL'],
                    'start_date': '2020-01-01'
                },
                'journals': []
            },
            'storage': {
                'pdf_directory': f'/datapool/aischolar/{instance_name}-dataset/pdf',
                'processed_directory': f'/datapool/aischolar/{instance_name}-dataset/processed',
                'state_directory': f'/datapool/aischolar/{instance_name}-dataset/state',
                'error_log_directory': f'/datapool/aischolar/{instance_name}-dataset/errors',
                'archive_directory': f'/datapool/aischolar/{instance_name}-dataset/archive'
            },
            'processing': {
                'batch_size': 20,
                'max_concurrent_downloads': 5,
                'max_concurrent_processing': 3,
                'retry_attempts': 3,
                'timeout_seconds': 300,
                'memory_limit_mb': 4096
            },
            'vector_store': {
                'collection_name': f'{instance_name}_papers',
                'embedding_model': 'all-MiniLM-L6-v2',
                'chunk_size': 1000,
                'chunk_overlap': 200,
                'host': 'localhost',
                'port': 8082
            },
            'notifications': {
                'enabled': False,
                'recipients': [],
                'smtp_server': 'localhost',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'from_email': f'{instance_name}@localhost'
            }
        }
    
    def _load_configuration(self):
        """Load configuration with instance-specific defaults and environment variables."""
        # Start with instance-specific default configuration
        self.config = self.default_config.copy()
        
        # Load from configuration file if it exists
        if self.config_file and self.config_file.exists():
            self._load_config_file()
        
        # Override with environment variables
        self._load_instance_environment_variables()
        
        logger.info(f"Configuration loaded for instance '{self.instance_name}'")
    
    def _load_instance_environment_variables(self):
        """Load instance-specific environment variables."""
        # Instance-specific environment variable mappings
        env_mappings = {
            # Instance settings
            f'{self.instance_name.upper()}_DISPLAY_NAME': ['instance', 'display_name'],
            f'{self.instance_name.upper()}_DESCRIPTION': ['instance', 'description'],
            
            # Storage paths
            f'{self.instance_name.upper()}_PDF_DIR': ['storage', 'pdf_directory'],
            f'{self.instance_name.upper()}_PROCESSED_DIR': ['storage', 'processed_directory'],
            f'{self.instance_name.upper()}_STATE_DIR': ['storage', 'state_directory'],
            f'{self.instance_name.upper()}_ERROR_DIR': ['storage', 'error_log_directory'],
            f'{self.instance_name.upper()}_ARCHIVE_DIR': ['storage', 'archive_directory'],
            
            # Processing settings
            f'{self.instance_name.upper()}_BATCH_SIZE': ['processing', 'batch_size'],
            f'{self.instance_name.upper()}_MAX_DOWNLOADS': ['processing', 'max_concurrent_downloads'],
            f'{self.instance_name.upper()}_MAX_PROCESSING': ['processing', 'max_concurrent_processing'],
            f'{self.instance_name.upper()}_RETRY_ATTEMPTS': ['processing', 'retry_attempts'],
            f'{self.instance_name.upper()}_TIMEOUT': ['processing', 'timeout_seconds'],
            f'{self.instance_name.upper()}_MEMORY_LIMIT': ['processing', 'memory_limit_mb'],
            
            # Vector store settings
            f'{self.instance_name.upper()}_COLLECTION_NAME': ['vector_store', 'collection_name'],
            f'{self.instance_name.upper()}_EMBEDDING_MODEL': ['vector_store', 'embedding_model'],
            f'{self.instance_name.upper()}_CHROMADB_HOST': ['vector_store', 'host'],
            f'{self.instance_name.upper()}_CHROMADB_PORT': ['vector_store', 'port'],
            
            # Notification settings
            f'{self.instance_name.upper()}_NOTIFICATIONS_ENABLED': ['notifications', 'enabled'],
            f'{self.instance_name.upper()}_SMTP_SERVER': ['notifications', 'smtp_server'],
            f'{self.instance_name.upper()}_SMTP_PORT': ['notifications', 'smtp_port'],
            f'{self.instance_name.upper()}_SMTP_USERNAME': ['notifications', 'username'],
            f'{self.instance_name.upper()}_SMTP_PASSWORD': ['notifications', 'password'],
            f'{self.instance_name.upper()}_FROM_EMAIL': ['notifications', 'from_email'],
            f'{self.instance_name.upper()}_TO_EMAILS': ['notifications', 'recipients'],
            
            # ArXiv categories (comma-separated)
            f'{self.instance_name.upper()}_ARXIV_CATEGORIES': ['data_sources', 'arxiv', 'categories'],
            f'{self.instance_name.upper()}_START_DATE': ['data_sources', 'arxiv', 'start_date'],
        }
        
        # Load global environment variables as well
        global_env_mappings = {
            'MULTI_INSTANCE_BASE_DIR': ['global', 'base_directory'],
            'MULTI_INSTANCE_LOG_LEVEL': ['global', 'log_level'],
            'CHROMADB_HOST': ['vector_store', 'host'],
            'CHROMADB_PORT': ['vector_store', 'port'],
        }
        
        # Combine mappings
        all_mappings = {**env_mappings, **global_env_mappings}
        
        for env_var, config_path in all_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_value(self.config, config_path, self._convert_env_value(value))
                logger.debug(f"Set config from env var {env_var}: {'.'.join(config_path)} = {value}")
    
    def get_instance_config(self) -> InstanceConfig:
        """
        Get the configuration as an InstanceConfig object.
        
        Returns:
            InstanceConfig object with current configuration
        """
        from ..shared.multi_instance_data_models import (
            StoragePaths, ProcessingConfig, VectorStoreConfig, NotificationConfig
        )
        
        # Extract configuration sections
        instance_info = self.get_section('instance')
        storage_info = self.get_section('storage')
        processing_info = self.get_section('processing')
        vector_store_info = self.get_section('vector_store')
        notifications_info = self.get_section('notifications')
        data_sources_info = self.get_section('data_sources')
        
        # Create configuration objects
        storage_paths = StoragePaths(
            pdf_directory=storage_info.get('pdf_directory', ''),
            processed_directory=storage_info.get('processed_directory', ''),
            state_directory=storage_info.get('state_directory', ''),
            error_log_directory=storage_info.get('error_log_directory', ''),
            archive_directory=storage_info.get('archive_directory', '')
        )
        
        processing_config = ProcessingConfig(
            batch_size=processing_info.get('batch_size', 20),
            max_concurrent_downloads=processing_info.get('max_concurrent_downloads', 5),
            max_concurrent_processing=processing_info.get('max_concurrent_processing', 3),
            retry_attempts=processing_info.get('retry_attempts', 3),
            timeout_seconds=processing_info.get('timeout_seconds', 300),
            memory_limit_mb=processing_info.get('memory_limit_mb', 4096)
        )
        
        vector_store_config = VectorStoreConfig(
            collection_name=vector_store_info.get('collection_name', f'{self.instance_name}_papers'),
            embedding_model=vector_store_info.get('embedding_model', 'all-MiniLM-L6-v2'),
            chunk_size=vector_store_info.get('chunk_size', 1000),
            chunk_overlap=vector_store_info.get('chunk_overlap', 200),
            host=vector_store_info.get('host', 'localhost'),
            port=vector_store_info.get('port', 8082)
        )
        
        notification_config = NotificationConfig(
            enabled=notifications_info.get('enabled', False),
            recipients=notifications_info.get('recipients', []),
            smtp_server=notifications_info.get('smtp_server', 'localhost'),
            smtp_port=notifications_info.get('smtp_port', 587),
            username=notifications_info.get('username', ''),
            password=notifications_info.get('password', ''),
            from_email=notifications_info.get('from_email', f'{self.instance_name}@localhost')
        )
        
        # Extract arXiv categories and journal sources
        arxiv_info = data_sources_info.get('arxiv', {})
        arxiv_categories = arxiv_info.get('categories', [])
        journal_sources = data_sources_info.get('journals', [])
        
        return InstanceConfig(
            instance_name=instance_info.get('name', self.instance_name),
            display_name=instance_info.get('display_name', self.instance_name.title()),
            description=instance_info.get('description', f'Research papers for {self.instance_name}'),
            arxiv_categories=arxiv_categories,
            journal_sources=journal_sources,
            storage_paths=storage_paths,
            vector_store_config=vector_store_config,
            processing_config=processing_config,
            notification_config=notification_config,
            metadata={
                'config_file': str(self.config_file),
                'loaded_at': datetime.now().isoformat(),
                'version': '1.0.0'
            }
        )
    
    def validate_instance_config(self) -> List[str]:
        """
        Validate instance-specific configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate instance information
        instance_info = self.get_section('instance')
        if not instance_info.get('name'):
            errors.append("Instance name not specified")
        
        if not instance_info.get('display_name'):
            errors.append("Instance display name not specified")
        
        # Validate data sources
        data_sources = self.get_section('data_sources')
        arxiv_info = data_sources.get('arxiv', {})
        categories = arxiv_info.get('categories', [])
        
        if not categories:
            errors.append("No arXiv categories specified")
        
        # Validate arXiv categories format
        valid_category_patterns = [
            'cond-mat', 'gr-qc', 'hep-ph', 'hep-th', 'math', 'math-ph', 
            'physics', 'q-alg', 'quant-ph', 'econ.EM', 'econ.GN', 'econ.TH',
            'eess.SY', 'math.ST', 'math.PR', 'math.OC', 'q-fin.*', 'stat.*',
            'cs.AI', 'cs.LG', 'cs.CL', 'cs.CV', 'cs.NE'
        ]
        
        for category in categories:
            # Allow wildcard patterns
            if category.endswith('.*'):
                base_category = category[:-2]
                if not any(pattern.startswith(base_category) for pattern in valid_category_patterns):
                    errors.append(f"Invalid arXiv category pattern: {category}")
            elif category not in valid_category_patterns:
                errors.append(f"Invalid arXiv category: {category}")
        
        # Validate storage paths
        storage_info = self.get_section('storage')
        required_paths = [
            'pdf_directory', 'processed_directory', 'state_directory', 
            'error_log_directory', 'archive_directory'
        ]
        
        for path_name in required_paths:
            path_value = storage_info.get(path_name)
            if not path_value:
                errors.append(f"Storage path '{path_name}' not specified")
            elif not isinstance(path_value, str):
                errors.append(f"Storage path '{path_name}' must be a string")
        
        # Validate processing configuration
        processing_info = self.get_section('processing')
        
        batch_size = processing_info.get('batch_size', 0)
        if not isinstance(batch_size, int) or batch_size <= 0:
            errors.append("Batch size must be a positive integer")
        
        max_downloads = processing_info.get('max_concurrent_downloads', 0)
        if not isinstance(max_downloads, int) or max_downloads <= 0:
            errors.append("Max concurrent downloads must be a positive integer")
        
        # Validate vector store configuration
        vector_store_info = self.get_section('vector_store')
        
        collection_name = vector_store_info.get('collection_name')
        if not collection_name:
            errors.append("Vector store collection name not specified")
        elif not isinstance(collection_name, str):
            errors.append("Vector store collection name must be a string")
        
        port = vector_store_info.get('port', 0)
        if not isinstance(port, int) or not (1 <= port <= 65535):
            errors.append("Vector store port must be a valid port number (1-65535)")
        
        # Validate notification configuration if enabled
        notifications_info = self.get_section('notifications')
        if notifications_info.get('enabled', False):
            smtp_server = notifications_info.get('smtp_server')
            if not smtp_server:
                errors.append("SMTP server required when notifications are enabled")
            
            recipients = notifications_info.get('recipients', [])
            if not recipients:
                errors.append("At least one recipient required when notifications are enabled")
        
        return errors
    
    def create_instance_config_file(self, output_path: Optional[Path] = None) -> bool:
        """
        Create a configuration file for this instance.
        
        Args:
            output_path: Optional output file path
            
        Returns:
            True if successful, False otherwise
        """
        if output_path is None:
            output_path = self.config_file
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get current configuration
            config_data = self.get_effective_config()
            
            # Add metadata
            config_with_metadata = {
                '_metadata': {
                    'description': f'Configuration for {self.instance_name} scholar instance',
                    'generated_by': 'Multi-Instance ArXiv System',
                    'generated_at': datetime.now().isoformat(),
                    'version': '1.0.0',
                    'instance_name': self.instance_name
                },
                **config_data
            }
            
            with open(output_path, 'w') as f:
                yaml.dump(config_with_metadata, f, default_flow_style=False, indent=2)
            
            logger.info(f"Instance configuration file created: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create instance configuration file: {e}")
            return False
    
    def print_instance_config_summary(self):
        """Print a summary of the instance configuration."""
        instance_config = self.get_instance_config()
        
        print(f"Instance Configuration Summary: {self.instance_name}")
        print("=" * 60)
        print(f"Display Name: {instance_config.display_name}")
        print(f"Description: {instance_config.description}")
        print(f"ArXiv Categories: {', '.join(instance_config.arxiv_categories)}")
        print(f"Journal Sources: {len(instance_config.journal_sources)} configured")
        print(f"PDF Directory: {instance_config.storage_paths.pdf_directory}")
        print(f"Vector Store Collection: {instance_config.vector_store_config.collection_name}")
        print(f"Batch Size: {instance_config.processing_config.batch_size}")
        print(f"Notifications: {'Enabled' if instance_config.notification_config.enabled else 'Disabled'}")
        print("=" * 60)


class MultiInstanceConfigManager:
    """Manages configurations for multiple scholar instances."""
    
    def __init__(self, config_dir: Path):
        """
        Initialize MultiInstanceConfigManager.
        
        Args:
            config_dir: Directory containing instance configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Instance config managers
        self._instance_managers: Dict[str, InstanceConfigManager] = {}
        
        logger.info(f"MultiInstanceConfigManager initialized with config directory: {self.config_dir}")
    
    def get_instance_manager(self, instance_name: str) -> InstanceConfigManager:
        """
        Get or create a config manager for a specific instance.
        
        Args:
            instance_name: Name of the scholar instance
            
        Returns:
            InstanceConfigManager for the specified instance
        """
        if instance_name not in self._instance_managers:
            config_file = self.config_dir / f"{instance_name}.yaml"
            self._instance_managers[instance_name] = InstanceConfigManager(
                instance_name=instance_name,
                config_file=config_file,
                config_dir=self.config_dir
            )
        
        return self._instance_managers[instance_name]
    
    def list_configured_instances(self) -> List[str]:
        """
        List all instances that have configuration files.
        
        Returns:
            List of instance names
        """
        instances = []
        
        try:
            for config_file in self.config_dir.glob("*.yaml"):
                if not config_file.name.startswith('_'):  # Skip metadata files
                    instance_name = config_file.stem
                    instances.append(instance_name)
        except Exception as e:
            logger.error(f"Failed to list configured instances: {e}")
        
        return sorted(instances)
    
    def create_default_configs(self) -> bool:
        """
        Create default configuration files for AI Scholar and Quant Scholar.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create AI Scholar config
            ai_manager = self.get_instance_manager('ai_scholar')
            ai_manager.create_instance_config_file()
            
            # Create Quant Scholar config
            quant_manager = self.get_instance_manager('quant_scholar')
            quant_manager.create_instance_config_file()
            
            logger.info("Default configuration files created")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create default configurations: {e}")
            return False
    
    def validate_all_configs(self) -> Dict[str, List[str]]:
        """
        Validate all instance configurations.
        
        Returns:
            Dictionary mapping instance names to validation errors
        """
        validation_results = {}
        
        for instance_name in self.list_configured_instances():
            try:
                manager = self.get_instance_manager(instance_name)
                errors = manager.validate_instance_config()
                validation_results[instance_name] = errors
            except Exception as e:
                validation_results[instance_name] = [f"Failed to validate: {e}"]
        
        return validation_results