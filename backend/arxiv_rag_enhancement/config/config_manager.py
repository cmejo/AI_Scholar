"""
Configuration Manager for arXiv RAG Enhancement system.

Handles loading and merging configuration from multiple sources:
1. Default configuration
2. YAML/JSON configuration files
3. Environment variables
4. Command-line arguments
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from datetime import datetime

from .default_config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class ConfigManager:
    """Centralized configuration management system."""
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """
        Initialize ConfigManager.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.config_file = Path(config_file) if config_file else None
        self.config = DEFAULT_CONFIG.copy()
        self._load_configuration()
    
    def _load_configuration(self):
        """Load configuration from all sources in priority order."""
        # 1. Start with default configuration (already loaded)
        
        # 2. Load from configuration file if provided
        if self.config_file and self.config_file.exists():
            self._load_config_file()
        
        # 3. Override with environment variables
        self._load_environment_variables()
        
        logger.info("Configuration loaded successfully")
    
    def _load_config_file(self):
        """Load configuration from YAML or JSON file."""
        try:
            with open(self.config_file, 'r') as f:
                if self.config_file.suffix.lower() in ['.yaml', '.yml']:
                    file_config = yaml.safe_load(f)
                elif self.config_file.suffix.lower() == '.json':
                    file_config = json.load(f)
                else:
                    logger.warning(f"Unsupported config file format: {self.config_file}")
                    return
            
            if file_config:
                self._merge_config(self.config, file_config)
                logger.info(f"Loaded configuration from {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to load config file {self.config_file}: {e}")
    
    def _load_environment_variables(self):
        """Load configuration from environment variables."""
        env_mappings = {
            # Global settings
            'ARXIV_RAG_OUTPUT_DIR': ['global', 'output_dir'],
            'ARXIV_RAG_BATCH_SIZE': ['global', 'batch_size'],
            'ARXIV_RAG_VERBOSE': ['global', 'verbose_logging'],
            
            # Local processor
            'ARXIV_LOCAL_SOURCE_DIR': ['local_processor', 'source_dir'],
            'ARXIV_LOCAL_MAX_FILES': ['local_processor', 'max_files'],
            
            # Bulk downloader
            'ARXIV_BULK_START_DATE': ['bulk_downloader', 'start_date'],
            'ARXIV_BULK_MAX_PAPERS': ['bulk_downloader', 'max_papers'],
            
            # ChromaDB
            'CHROMADB_HOST': ['rag_integration', 'chromadb', 'host'],
            'CHROMADB_PORT': ['rag_integration', 'chromadb', 'port'],
            
            # Email notifications
            'ARXIV_EMAIL_ENABLED': ['monthly_updater', 'email_notifications', 'enabled'],
            'ARXIV_SMTP_SERVER': ['monthly_updater', 'email_notifications', 'smtp_server'],
            'ARXIV_SMTP_PORT': ['monthly_updater', 'email_notifications', 'smtp_port'],
            'ARXIV_SMTP_USERNAME': ['monthly_updater', 'email_notifications', 'username'],
            'ARXIV_SMTP_PASSWORD': ['monthly_updater', 'email_notifications', 'password'],
            'ARXIV_FROM_EMAIL': ['monthly_updater', 'email_notifications', 'from_email'],
            'ARXIV_TO_EMAILS': ['monthly_updater', 'email_notifications', 'to_emails'],
            
            # Logging
            'ARXIV_LOG_LEVEL': ['error_handling', 'log_level'],
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_value(self.config, config_path, self._convert_env_value(value))
                logger.debug(f"Set config from env var {env_var}: {'.'.join(config_path)} = {value}")
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Boolean values
        if value.lower() in ['true', 'yes', '1', 'on']:
            return True
        elif value.lower() in ['false', 'no', '0', 'off']:
            return False
        
        # Numeric values
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # List values (comma-separated)
        if ',' in value:
            return [item.strip() for item in value.split(',')]
        
        # String value
        return value
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _set_nested_value(self, config: Dict[str, Any], path: List[str], value: Any):
        """Set a nested configuration value using a path."""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            path: Configuration path (e.g., 'global.batch_size')
            default: Default value if path not found
            
        Returns:
            Configuration value or default
        """
        keys = path.split('.')
        current = self.config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, path: str, value: Any):
        """
        Set configuration value using dot notation.
        
        Args:
            path: Configuration path (e.g., 'global.batch_size')
            value: Value to set
        """
        keys = path.split('.')
        self._set_nested_value(self.config, keys, value)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.
        
        Args:
            section: Section name (e.g., 'local_processor')
            
        Returns:
            Configuration section dictionary
        """
        return self.config.get(section, {})
    
    def save_config(self, output_file: Optional[Union[str, Path]] = None) -> bool:
        """
        Save current configuration to file.
        
        Args:
            output_file: Optional output file path (defaults to loaded config file)
            
        Returns:
            True if successful, False otherwise
        """
        output_path = Path(output_file) if output_file else self.config_file
        
        if not output_path:
            logger.error("No output file specified for saving configuration")
            return False
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Add metadata
            config_with_metadata = {
                '_metadata': {
                    'generated_by': 'arXiv RAG Enhancement System',
                    'generated_at': datetime.now().isoformat(),
                    'version': '1.0.0'
                },
                **self.config
            }
            
            with open(output_path, 'w') as f:
                if output_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(config_with_metadata, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config_with_metadata, f, indent=2)
            
            logger.info(f"Configuration saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def validate_config(self) -> List[str]:
        """
        Validate current configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate required directories
        output_dir = self.get('global.output_dir')
        if not output_dir:
            errors.append("Global output directory not specified")
        
        # Validate categories
        categories = self.get('global.categories', [])
        if not categories:
            errors.append("No arXiv categories specified")
        
        valid_categories = [
            'cond-mat', 'gr-qc', 'hep-ph', 'hep-th', 'math', 
            'math-ph', 'physics', 'q-alg', 'quant-ph'
        ]
        
        for category in categories:
            if category not in valid_categories:
                errors.append(f"Invalid arXiv category: {category}")
        
        # Validate numeric values
        batch_size = self.get('global.batch_size')
        if not isinstance(batch_size, int) or batch_size <= 0:
            errors.append("Batch size must be a positive integer")
        
        # Validate ChromaDB settings
        chromadb_port = self.get('rag_integration.chromadb.port')
        if not isinstance(chromadb_port, int) or not (1 <= chromadb_port <= 65535):
            errors.append("ChromaDB port must be a valid port number (1-65535)")
        
        # Validate email settings if enabled
        if self.get('monthly_updater.email_notifications.enabled'):
            smtp_server = self.get('monthly_updater.email_notifications.smtp_server')
            if not smtp_server:
                errors.append("SMTP server required when email notifications are enabled")
            
            to_emails = self.get('monthly_updater.email_notifications.to_emails', [])
            if not to_emails:
                errors.append("At least one recipient email required when email notifications are enabled")
        
        # Validate date formats
        start_date = self.get('bulk_downloader.start_date')
        if start_date:
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                errors.append(f"Invalid start date format: {start_date} (expected YYYY-MM-DD)")
        
        return errors
    
    def create_sample_config(self, output_file: Union[str, Path]) -> bool:
        """
        Create a sample configuration file with comments.
        
        Args:
            output_file: Path to create sample config file
            
        Returns:
            True if successful, False otherwise
        """
        sample_config = {
            '_metadata': {
                'description': 'Sample configuration for arXiv RAG Enhancement System',
                'created_at': datetime.now().isoformat(),
                'version': '1.0.0'
            },
            
            'global': {
                'output_dir': '/datapool/aischolar/arxiv-dataset-2024',
                'categories': ['cond-mat', 'gr-qc', 'hep-ph', 'hep-th', 'math'],
                'batch_size': 10,
                'verbose_logging': False
            },
            
            'local_processor': {
                'source_dir': '~/arxiv-dataset/pdf',
                'max_files': None,  # null for no limit
                'resume_enabled': True
            },
            
            'bulk_downloader': {
                'start_date': '2024-07-01',
                'max_papers': 1000,
                'max_concurrent_downloads': 5
            },
            
            'monthly_updater': {
                'enabled': True,
                'schedule': {
                    'day_of_month': 1,
                    'hour': 2,
                    'minute': 0
                },
                'email_notifications': {
                    'enabled': False,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'username': 'your-email@gmail.com',
                    'password': 'your-app-password',
                    'from_email': 'arxiv-updater@yourdomain.com',
                    'to_emails': ['admin@yourdomain.com']
                }
            },
            
            'rag_integration': {
                'chromadb': {
                    'host': 'localhost',
                    'port': 8082
                }
            }
        }
        
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                if output_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(sample_config, f, default_flow_style=False, indent=2)
                else:
                    json.dump(sample_config, f, indent=2)
            
            logger.info(f"Sample configuration created at {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create sample configuration: {e}")
            return False
    
    def get_effective_config(self) -> Dict[str, Any]:
        """Get the complete effective configuration."""
        return self.config.copy()
    
    def print_config_summary(self):
        """Print a summary of the current configuration."""
        print("Configuration Summary:")
        print("=" * 50)
        print(f"Output Directory: {self.get('global.output_dir')}")
        print(f"Categories: {', '.join(self.get('global.categories', []))}")
        print(f"Batch Size: {self.get('global.batch_size')}")
        print(f"ChromaDB: {self.get('rag_integration.chromadb.host')}:{self.get('rag_integration.chromadb.port')}")
        print(f"Email Notifications: {'Enabled' if self.get('monthly_updater.email_notifications.enabled') else 'Disabled'}")
        print(f"Monthly Updates: {'Enabled' if self.get('monthly_updater.enabled') else 'Disabled'}")
        print("=" * 50)