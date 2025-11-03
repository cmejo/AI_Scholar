#!/usr/bin/env python3
"""
Main entry point for running monthly updates across all scholar instances.

This script is designed to be run by cron for automated monthly updates.
"""

import asyncio
import argparse
import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from multi_instance_arxiv_system.scheduling.monthly_update_orchestrator import MonthlyUpdateOrchestrator, OrchestrationConfig
from multi_instance_arxiv_system.shared.multi_instance_data_models import (
    InstanceConfig, VectorStoreConfig, StoragePaths, ProcessingConfig, NotificationConfig
)

# Configure logging
log_handlers = [logging.StreamHandler(sys.stdout)]

# Add file handler if log directory exists or can be created
try:
    log_dir = Path('/var/log/multi_instance_arxiv')
    log_dir.mkdir(parents=True, exist_ok=True)
    log_handlers.append(logging.FileHandler(log_dir / 'monthly_update.log'))
except Exception:
    # Fall back to console logging only
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)


def load_instance_configs(config_dir: str) -> List[InstanceConfig]:
    """
    Load instance configurations from directory.
    
    Args:
        config_dir: Directory containing instance configuration files
        
    Returns:
        List of loaded instance configurations
    """
    configs = []
    config_path = Path(config_dir)
    
    if not config_path.exists():
        logger.error(f"Configuration directory not found: {config_dir}")
        return configs
    
    # Look for YAML configuration files
    for config_file in config_path.glob("*.yaml"):
        try:
            import yaml
            
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Convert YAML config to InstanceConfig
            config = create_instance_config_from_yaml(config_data)
            configs.append(config)
            
            logger.info(f"Loaded configuration for instance: {config.instance_name}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_file}: {e}")
    
    return configs


def create_instance_config_from_yaml(config_data: dict) -> InstanceConfig:
    """
    Create InstanceConfig from YAML configuration data.
    
    Args:
        config_data: YAML configuration dictionary
        
    Returns:
        InstanceConfig object
    """
    instance_info = config_data['instance']
    storage_info = config_data['storage']
    processing_info = config_data.get('processing', {})
    vector_store_info = config_data.get('vector_store', {})
    notifications_info = config_data.get('notifications', {})
    data_sources = config_data.get('data_sources', {})
    
    # Create storage paths
    storage_paths = StoragePaths(
        pdf_directory=storage_info['pdf_directory'],
        processed_directory=storage_info['processed_directory'],
        state_directory=storage_info.get('state_directory', storage_info['processed_directory'] + '/state'),
        error_log_directory=storage_info.get('error_log_directory', storage_info['processed_directory'] + '/logs'),
        archive_directory=storage_info.get('archive_directory', storage_info['processed_directory'] + '/archive')
    )
    
    # Create vector store config
    vector_store_config = VectorStoreConfig(
        collection_name=vector_store_info.get('collection_name', f"{instance_info['name']}_papers"),
        embedding_model=vector_store_info.get('embedding_model', 'all-MiniLM-L6-v2'),
        chunk_size=vector_store_info.get('chunk_size', 1000),
        chunk_overlap=vector_store_info.get('chunk_overlap', 200),
        host=vector_store_info.get('host', 'localhost'),
        port=vector_store_info.get('port', 8082)
    )
    
    # Create processing config
    processing_config = ProcessingConfig(
        batch_size=processing_info.get('batch_size', 20),
        max_concurrent_downloads=processing_info.get('max_concurrent_downloads', 5),
        max_concurrent_processing=processing_info.get('max_concurrent_processing', 3),
        retry_attempts=processing_info.get('retry_attempts', 3),
        timeout_seconds=processing_info.get('timeout_seconds', 300),
        memory_limit_mb=processing_info.get('memory_limit_mb', 4096)
    )
    
    # Create notification config
    notification_config = NotificationConfig(
        enabled=notifications_info.get('enabled', False),
        recipients=notifications_info.get('recipients', []),
        smtp_server=notifications_info.get('smtp_server', 'localhost'),
        smtp_port=notifications_info.get('smtp_port', 587),
        username=notifications_info.get('username', ''),
        password=notifications_info.get('password', ''),
        from_email=notifications_info.get('from_email', '')
    )
    
    # Extract categories and journal sources
    arxiv_categories = []
    journal_sources = []
    
    if 'arxiv' in data_sources:
        arxiv_categories = data_sources['arxiv'].get('categories', [])
    
    if 'journals' in data_sources:
        journal_sources = [journal['name'] for journal in data_sources['journals']]
    
    return InstanceConfig(
        instance_name=instance_info['name'],
        display_name=instance_info.get('display_name', instance_info['name']),
        description=instance_info.get('description', ''),
        arxiv_categories=arxiv_categories,
        journal_sources=journal_sources,
        storage_paths=storage_paths,
        vector_store_config=vector_store_config,
        processing_config=processing_config,
        notification_config=notification_config
    )


def create_default_configs() -> List[InstanceConfig]:
    """
    Create default configurations for AI Scholar and Quant Scholar.
    
    Returns:
        List of default instance configurations
    """
    configs = []
    
    # AI Scholar configuration
    ai_scholar_storage = StoragePaths(
        pdf_directory="/datapool/aischolar/ai-scholar-arxiv-dataset/pdf",
        processed_directory="/datapool/aischolar/ai-scholar-arxiv-dataset/processed",
        state_directory="/datapool/aischolar/ai-scholar-arxiv-dataset/state",
        error_log_directory="/datapool/aischolar/ai-scholar-arxiv-dataset/logs",
        archive_directory="/datapool/aischolar/ai-scholar-arxiv-dataset/archive"
    )
    
    ai_scholar_vector_store = VectorStoreConfig(
        collection_name="ai_scholar_papers",
        embedding_model="all-MiniLM-L6-v2",
        chunk_size=1000,
        chunk_overlap=200
    )
    
    ai_scholar_processing = ProcessingConfig(
        batch_size=20,
        max_concurrent_downloads=5,
        max_concurrent_processing=3
    )
    
    ai_scholar_notifications = NotificationConfig(enabled=False)
    
    ai_scholar_config = InstanceConfig(
        instance_name="ai_scholar",
        display_name="AI Scholar",
        description="General AI and Physics Research Papers",
        arxiv_categories=["cond-mat", "gr-qc", "hep-ph", "hep-th", "math", "math-ph", "physics", "q-alg", "quant-ph"],
        journal_sources=[],
        storage_paths=ai_scholar_storage,
        vector_store_config=ai_scholar_vector_store,
        processing_config=ai_scholar_processing,
        notification_config=ai_scholar_notifications
    )
    
    configs.append(ai_scholar_config)
    
    # Quant Scholar configuration
    quant_scholar_storage = StoragePaths(
        pdf_directory="/datapool/aischolar/quant-scholar-dataset/pdf",
        processed_directory="/datapool/aischolar/quant-scholar-dataset/processed",
        state_directory="/datapool/aischolar/quant-scholar-dataset/state",
        error_log_directory="/datapool/aischolar/quant-scholar-dataset/logs",
        archive_directory="/datapool/aischolar/quant-scholar-dataset/archive"
    )
    
    quant_scholar_vector_store = VectorStoreConfig(
        collection_name="quant_scholar_papers",
        embedding_model="all-MiniLM-L6-v2",
        chunk_size=1000,
        chunk_overlap=200
    )
    
    quant_scholar_processing = ProcessingConfig(
        batch_size=15,
        max_concurrent_downloads=3,
        max_concurrent_processing=2
    )
    
    quant_scholar_notifications = NotificationConfig(enabled=False)
    
    quant_scholar_config = InstanceConfig(
        instance_name="quant_scholar",
        display_name="Quant Scholar",
        description="Quantitative Finance and Statistics Research Papers",
        arxiv_categories=["econ.EM", "econ.GN", "econ.TH", "eess.SY", "math.ST", "math.PR", "math.OC", "q-fin.*", "stat.*"],
        journal_sources=["Journal of Statistical Software", "The R Journal"],
        storage_paths=quant_scholar_storage,
        vector_store_config=quant_scholar_vector_store,
        processing_config=quant_scholar_processing,
        notification_config=quant_scholar_notifications
    )
    
    configs.append(quant_scholar_config)
    
    return configs


async def main():
    """Main entry point for monthly updates."""
    parser = argparse.ArgumentParser(description="Run monthly updates for multi-instance ArXiv system")
    
    parser.add_argument(
        '--instances',
        type=str,
        help='Comma-separated list of instance names to update (default: all)'
    )
    
    parser.add_argument(
        '--config-dir',
        type=str,
        default='/etc/multi_instance_arxiv/instances',
        help='Directory containing instance configuration files'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force update even if recently updated'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually running updates'
    )
    
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=2,
        help='Maximum number of concurrent instance updates'
    )
    
    parser.add_argument(
        '--timeout-hours',
        type=int,
        default=12,
        help='Timeout for individual instance updates in hours'
    )
    
    args = parser.parse_args()
    
    logger.info("Starting monthly update orchestration")
    logger.info(f"Arguments: {vars(args)}")
    
    try:
        # Load instance configurations
        if Path(args.config_dir).exists():
            instance_configs = load_instance_configs(args.config_dir)
        else:
            logger.warning(f"Config directory not found: {args.config_dir}, using defaults")
            instance_configs = create_default_configs()
        
        if not instance_configs:
            logger.error("No instance configurations found")
            return 1
        
        # Filter instances if specified
        if args.instances:
            requested_instances = [name.strip() for name in args.instances.split(',')]
            instance_configs = [
                config for config in instance_configs 
                if config.instance_name in requested_instances
            ]
            
            if not instance_configs:
                logger.error(f"No matching instances found for: {args.instances}")
                return 1
        
        logger.info(f"Loaded {len(instance_configs)} instance configurations")
        
        # Create orchestration configuration
        orchestration_config = OrchestrationConfig(
            max_concurrent_instances=args.max_concurrent,
            instance_timeout_hours=args.timeout_hours,
            retry_failed_instances=True,
            max_retry_attempts=2,
            cleanup_old_reports=True,
            report_retention_days=90,
            enable_notifications=True
        )
        
        if args.dry_run:
            logger.info("DRY RUN MODE - No actual updates will be performed")
            logger.info("Instances that would be updated:")
            for config in instance_configs:
                logger.info(f"  - {config.instance_name}: {config.display_name}")
            return 0
        
        # Create and run orchestrator
        orchestrator = MonthlyUpdateOrchestrator(orchestration_config=orchestration_config)
        
        result = await orchestrator.run_monthly_updates(
            instance_configs=instance_configs,
            force_update=args.force
        )
        
        # Log results
        logger.info("Monthly update orchestration completed")
        logger.info(f"Orchestration ID: {result.orchestration_id}")
        logger.info(f"Duration: {result.duration_seconds:.2f} seconds")
        logger.info(f"Success rate: {result.success_rate:.1f}%")
        logger.info(f"Total papers processed: {result.total_papers_processed}")
        logger.info(f"Total errors: {result.total_errors}")
        
        if result.failed_instances:
            logger.error(f"Failed instances: {', '.join(result.failed_instances)}")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Monthly update orchestration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)