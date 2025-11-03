#!/usr/bin/env python3
"""
Demonstration of Task 2.2: Instance Configuration Management functionality.

This script demonstrates the complete instance configuration management system including:
- InstanceConfig dataclass with storage paths and processing settings
- YAML configuration loader with validation
- Separate config files for AI Scholar and Quant Scholar instances
- Environment variable support for sensitive settings
"""

import os
import tempfile
import logging
from pathlib import Path

# Add backend to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from multi_instance_arxiv_system.config.instance_config_manager import (
    InstanceConfigManager, MultiInstanceConfigManager
)
from multi_instance_arxiv_system.config.default_instance_configs import (
    DEFAULT_AI_SCHOLAR_CONFIG, DEFAULT_QUANT_SCHOLAR_CONFIG,
    get_categories_for_field, create_custom_instance_config
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_instance_config_dataclass():
    """Demonstrate InstanceConfig dataclass functionality."""
    logger.info("=== Demonstrating InstanceConfig Dataclass ===")
    
    # Load AI Scholar configuration
    ai_manager = InstanceConfigManager(
        instance_name='ai_scholar',
        config_dir='backend/multi_instance_arxiv_system/configs'
    )
    
    ai_config = ai_manager.get_instance_config()
    
    logger.info(f"AI Scholar Configuration:")
    logger.info(f"  Instance Name: {ai_config.instance_name}")
    logger.info(f"  Display Name: {ai_config.display_name}")
    logger.info(f"  Description: {ai_config.description}")
    logger.info(f"  ArXiv Categories: {len(ai_config.arxiv_categories)} categories")
    logger.info(f"    - {', '.join(ai_config.arxiv_categories[:3])}...")
    logger.info(f"  Storage Paths:")
    logger.info(f"    - PDF Directory: {ai_config.storage_paths.pdf_directory}")
    logger.info(f"    - Processed Directory: {ai_config.storage_paths.processed_directory}")
    logger.info(f"    - State Directory: {ai_config.storage_paths.state_directory}")
    logger.info(f"  Processing Config:")
    logger.info(f"    - Batch Size: {ai_config.processing_config.batch_size}")
    logger.info(f"    - Max Downloads: {ai_config.processing_config.max_concurrent_downloads}")
    logger.info(f"    - Max Processing: {ai_config.processing_config.max_concurrent_processing}")
    logger.info(f"  Vector Store Config:")
    logger.info(f"    - Collection: {ai_config.vector_store_config.collection_name}")
    logger.info(f"    - Embedding Model: {ai_config.vector_store_config.embedding_model}")
    logger.info(f"    - Host: {ai_config.vector_store_config.host}:{ai_config.vector_store_config.port}")
    logger.info(f"  Notifications: {'Enabled' if ai_config.notification_config.enabled else 'Disabled'}")


def demo_yaml_configuration_loader():
    """Demonstrate YAML configuration loading with validation."""
    logger.info("=== Demonstrating YAML Configuration Loader ===")
    
    # Load Quant Scholar configuration
    quant_manager = InstanceConfigManager(
        instance_name='quant_scholar',
        config_dir='backend/multi_instance_arxiv_system/configs'
    )
    
    quant_config = quant_manager.get_instance_config()
    
    logger.info(f"Quant Scholar Configuration:")
    logger.info(f"  Instance Name: {quant_config.instance_name}")
    logger.info(f"  Display Name: {quant_config.display_name}")
    logger.info(f"  ArXiv Categories: {len(quant_config.arxiv_categories)} categories")
    logger.info(f"    - {', '.join(quant_config.arxiv_categories[:3])}...")
    logger.info(f"  Journal Sources: {len(quant_config.journal_sources)} sources")
    for journal in quant_config.journal_sources:
        logger.info(f"    - {journal}")
    
    # Validate configuration
    validation_errors = quant_manager.validate_instance_config()
    if validation_errors:
        logger.warning(f"Validation errors found: {validation_errors}")
    else:
        logger.info("  ✓ Configuration validation passed")
    
    # Print configuration summary
    logger.info("\nConfiguration Summary:")
    quant_manager.print_instance_config_summary()


def demo_separate_config_files():
    """Demonstrate separate configuration files for different instances."""
    logger.info("=== Demonstrating Separate Configuration Files ===")
    
    # Use MultiInstanceConfigManager to manage multiple instances
    multi_manager = MultiInstanceConfigManager(
        config_dir=Path('backend/multi_instance_arxiv_system/configs')
    )
    
    # List all configured instances
    instances = multi_manager.list_configured_instances()
    logger.info(f"Configured instances: {instances}")
    
    # Get managers for each instance
    for instance_name in instances:
        manager = multi_manager.get_instance_manager(instance_name)
        config = manager.get_instance_config()
        
        logger.info(f"\n{instance_name.upper()} Instance:")
        logger.info(f"  Config File: {manager.config_file}")
        logger.info(f"  Display Name: {config.display_name}")
        logger.info(f"  Categories: {len(config.arxiv_categories)}")
        logger.info(f"  Journal Sources: {len(config.journal_sources)}")
        logger.info(f"  Vector Collection: {config.vector_store_config.collection_name}")
    
    # Validate all configurations
    validation_results = multi_manager.validate_all_configs()
    logger.info(f"\nValidation Results:")
    for instance, errors in validation_results.items():
        status = "✓ VALID" if not errors else f"❌ {len(errors)} errors"
        logger.info(f"  {instance}: {status}")


def demo_environment_variable_support():
    """Demonstrate environment variable support for sensitive settings."""
    logger.info("=== Demonstrating Environment Variable Support ===")
    
    # Set some test environment variables
    test_env_vars = {
        'AI_SCHOLAR_BATCH_SIZE': '100',
        'AI_SCHOLAR_MAX_DOWNLOADS': '20',
        'AI_SCHOLAR_NOTIFICATIONS_ENABLED': 'true',
        'AI_SCHOLAR_SMTP_SERVER': 'smtp.example.com',
        'AI_SCHOLAR_FROM_EMAIL': 'ai-scholar@example.com',
        'AI_SCHOLAR_TO_EMAILS': 'admin@example.com,user@example.com',
        'CHROMADB_HOST': 'production-chromadb',
        'CHROMADB_PORT': '8083'
    }
    
    logger.info("Setting test environment variables:")
    for key, value in test_env_vars.items():
        os.environ[key] = value
        logger.info(f"  {key} = {value}")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "configs"
            
            # Create config manager (will use environment variables)
            manager = InstanceConfigManager(
                instance_name='ai_scholar',
                config_dir=config_dir
            )
            
            config = manager.get_instance_config()
            
            logger.info("\nConfiguration with environment variable overrides:")
            logger.info(f"  Batch Size: {config.processing_config.batch_size} (from env)")
            logger.info(f"  Max Downloads: {config.processing_config.max_concurrent_downloads} (from env)")
            logger.info(f"  Notifications Enabled: {config.notification_config.enabled} (from env)")
            logger.info(f"  SMTP Server: {config.notification_config.smtp_server} (from env)")
            logger.info(f"  From Email: {config.notification_config.from_email} (from env)")
            logger.info(f"  Recipients: {config.notification_config.recipients} (from env)")
            logger.info(f"  ChromaDB Host: {config.vector_store_config.host} (from env)")
            logger.info(f"  ChromaDB Port: {config.vector_store_config.port} (from env)")
            
    finally:
        # Clean up environment variables
        for key in test_env_vars:
            if key in os.environ:
                del os.environ[key]
        
        logger.info("Environment variables cleaned up")


def demo_configuration_creation():
    """Demonstrate creating new configuration files."""
    logger.info("=== Demonstrating Configuration Creation ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "demo_configs"
        
        # Create multi-instance manager
        multi_manager = MultiInstanceConfigManager(config_dir)
        
        # Create default configurations
        logger.info("Creating default AI Scholar and Quant Scholar configurations...")
        success = multi_manager.create_default_configs()
        logger.info(f"Default configs created: {success}")
        
        # Create a custom instance configuration
        logger.info("\nCreating custom instance configuration...")
        
        custom_config_data = create_custom_instance_config(
            instance_name='ml_scholar',
            display_name='ML Scholar',
            description='Machine Learning and Deep Learning Research Papers',
            arxiv_categories=get_categories_for_field('ai_ml')
        )
        
        # Create custom instance manager
        custom_manager = InstanceConfigManager(
            instance_name='ml_scholar',
            config_dir=config_dir
        )
        
        # Override with custom configuration
        custom_manager.config = custom_config_data
        
        # Create configuration file
        custom_config_file = config_dir / "ml_scholar.yaml"
        success = custom_manager.create_instance_config_file(custom_config_file)
        logger.info(f"Custom config file created: {success}")
        
        # List all created configurations
        instances = multi_manager.list_configured_instances()
        logger.info(f"\nCreated configurations: {instances}")
        
        # Show custom configuration details
        if 'ml_scholar' in instances:
            ml_manager = multi_manager.get_instance_manager('ml_scholar')
            ml_config = ml_manager.get_instance_config()
            
            logger.info(f"\nCustom ML Scholar Configuration:")
            logger.info(f"  Display Name: {ml_config.display_name}")
            logger.info(f"  Description: {ml_config.description}")
            logger.info(f"  Categories: {ml_config.arxiv_categories}")
            logger.info(f"  Collection: {ml_config.vector_store_config.collection_name}")


def demo_default_configurations():
    """Demonstrate default configuration values and helpers."""
    logger.info("=== Demonstrating Default Configurations ===")
    
    # Show AI Scholar defaults
    logger.info("AI Scholar Default Configuration:")
    ai_defaults = DEFAULT_AI_SCHOLAR_CONFIG
    logger.info(f"  Name: {ai_defaults['instance']['name']}")
    logger.info(f"  Display Name: {ai_defaults['instance']['display_name']}")
    logger.info(f"  Categories: {len(ai_defaults['data_sources']['arxiv']['categories'])}")
    logger.info(f"  Batch Size: {ai_defaults['processing']['batch_size']}")
    logger.info(f"  Collection: {ai_defaults['vector_store']['collection_name']}")
    
    # Show Quant Scholar defaults
    logger.info("\nQuant Scholar Default Configuration:")
    quant_defaults = DEFAULT_QUANT_SCHOLAR_CONFIG
    logger.info(f"  Name: {quant_defaults['instance']['name']}")
    logger.info(f"  Display Name: {quant_defaults['instance']['display_name']}")
    logger.info(f"  Categories: {len(quant_defaults['data_sources']['arxiv']['categories'])}")
    logger.info(f"  Journal Sources: {len(quant_defaults['data_sources']['journals'])}")
    logger.info(f"  Batch Size: {quant_defaults['processing']['batch_size']}")
    
    # Demonstrate category helpers
    logger.info("\nCategory Helpers:")
    fields = ['ai_ml', 'physics', 'mathematics', 'economics_finance', 'statistics']
    
    for field in fields:
        categories = get_categories_for_field(field)
        logger.info(f"  {field}: {len(categories)} categories")
        if categories:
            logger.info(f"    Examples: {', '.join(categories[:3])}...")


def main():
    """Run all configuration management demonstrations."""
    logger.info("🚀 Starting Task 2.2 Instance Configuration Management Demonstration")
    logger.info("=" * 80)
    
    try:
        # Demonstrate InstanceConfig dataclass
        demo_instance_config_dataclass()
        
        # Demonstrate YAML configuration loading
        demo_yaml_configuration_loader()
        
        # Demonstrate separate config files
        demo_separate_config_files()
        
        # Demonstrate environment variable support
        demo_environment_variable_support()
        
        # Demonstrate configuration creation
        demo_configuration_creation()
        
        # Demonstrate default configurations
        demo_default_configurations()
        
        logger.info("=" * 80)
        logger.info("✅ Task 2.2 Implementation Demonstration Complete!")
        logger.info("")
        logger.info("📋 Summary of Implemented Components:")
        logger.info("  ✓ InstanceConfig dataclass - Comprehensive configuration structure")
        logger.info("  ✓ InstanceConfigManager - YAML loading and validation")
        logger.info("  ✓ MultiInstanceConfigManager - Multi-instance management")
        logger.info("  ✓ Environment variable support - Secure configuration overrides")
        logger.info("  ✓ YAML configuration files - AI Scholar and Quant Scholar configs")
        logger.info("  ✓ Configuration validation - Comprehensive validation rules")
        logger.info("  ✓ Default configurations - Pre-built templates and helpers")
        logger.info("")
        logger.info("🎯 Requirements Satisfied:")
        logger.info("  ✓ 8.1 - InstanceConfig dataclass with storage paths and processing settings")
        logger.info("  ✓ 8.2 - YAML configuration loader with validation")
        logger.info("  ✓ 8.5 - Separate config files for AI Scholar and Quant Scholar instances")
        logger.info("  ✓ 8.1 - Environment variable support for sensitive settings")
        logger.info("")
        logger.info("🔧 Key Features:")
        logger.info("  • Comprehensive configuration structure with all required settings")
        logger.info("  • YAML-based configuration files with metadata and validation")
        logger.info("  • Environment variable overrides for sensitive/deployment settings")
        logger.info("  • Multi-instance management with separate configurations")
        logger.info("  • Default configurations for AI Scholar and Quant Scholar")
        logger.info("  • Configuration validation with detailed error reporting")
        logger.info("  • Helper functions for arXiv categories and custom configs")
        logger.info("  • Automatic configuration file creation and management")
        
        return True
        
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)