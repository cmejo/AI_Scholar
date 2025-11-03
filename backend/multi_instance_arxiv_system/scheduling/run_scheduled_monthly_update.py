#!/usr/bin/env python3
"""
Scheduled Monthly Update Script with comprehensive validation and error handling.

This script is designed to be run by cron and includes health checks,
conflict resolution, and automated error recovery.
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

from .automated_scheduler import AutomatedScheduler, SchedulingConfig
from .monthly_update_orchestrator import MonthlyUpdateOrchestrator, OrchestrationConfig
from ..shared.multi_instance_data_models import InstanceConfig
from .error_recovery_manager import RecoveryConfig

# Configure logging for cron execution
log_dir = Path("/var/log/multi_instance_arxiv")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / "scheduled_monthly_update.log")
    ]
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
        return create_default_configs()
    
    # Look for YAML configuration files
    for config_file in config_path.glob("*.yaml"):
        try:
            import yaml
            
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Convert YAML config to InstanceConfig (simplified version)
            config = create_instance_config_from_yaml(config_data)
            configs.append(config)
            
            logger.info(f"Loaded configuration for instance: {config.instance_name}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_file}: {e}")
    
    if not configs:
        logger.warning("No configurations loaded, using defaults")
        return create_default_configs()
    
    return configs


def create_instance_config_from_yaml(config_data: dict) -> InstanceConfig:
    """Create InstanceConfig from YAML configuration data."""
    from ..shared.multi_instance_data_models import (
        StoragePaths, VectorStoreConfig, ProcessingConfig, NotificationConfig
    )
    
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
    """Create default configurations for AI Scholar and Quant Scholar."""
    from ..shared.multi_instance_data_models import (
        StoragePaths, VectorStoreConfig, ProcessingConfig, NotificationConfig
    )
    
    configs = []
    
    # AI Scholar configuration
    ai_scholar_storage = StoragePaths(
        pdf_directory="/datapool/aischolar/ai-scholar-arxiv-dataset/pdf",
        processed_directory="/datapool/aischolar/ai-scholar-arxiv-dataset/processed",
        state_directory="/datapool/aischolar/ai-scholar-arxiv-dataset/state",
        error_log_directory="/datapool/aischolar/ai-scholar-arxiv-dataset/logs",
        archive_directory="/datapool/aischolar/ai-scholar-arxiv-dataset/archive"
    )
    
    ai_scholar_config = InstanceConfig(
        instance_name="ai_scholar",
        display_name="AI Scholar",
        description="General AI and Physics Research Papers",
        arxiv_categories=["cond-mat", "gr-qc", "hep-ph", "hep-th", "math", "math-ph", "physics", "q-alg", "quant-ph"],
        journal_sources=[],
        storage_paths=ai_scholar_storage,
        vector_store_config=VectorStoreConfig(collection_name="ai_scholar_papers"),
        processing_config=ProcessingConfig(),
        notification_config=NotificationConfig(enabled=False)
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
    
    quant_scholar_config = InstanceConfig(
        instance_name="quant_scholar",
        display_name="Quant Scholar",
        description="Quantitative Finance and Statistics Research Papers",
        arxiv_categories=["econ.EM", "econ.GN", "econ.TH", "eess.SY", "math.ST", "math.PR", "math.OC", "q-fin.*", "stat.*"],
        journal_sources=["Journal of Statistical Software", "The R Journal"],
        storage_paths=quant_scholar_storage,
        vector_store_config=VectorStoreConfig(collection_name="quant_scholar_papers"),
        processing_config=ProcessingConfig(),
        notification_config=NotificationConfig(enabled=False)
    )
    
    configs.append(quant_scholar_config)
    
    return configs


async def run_monthly_update_with_orchestrator(instance_configs: List[InstanceConfig],
                                             force_update: bool = False) -> Any:
    """
    Run monthly update using the orchestrator.
    
    Args:
        instance_configs: List of instance configurations
        force_update: Whether to force update even if recently updated
        
    Returns:
        Orchestration result
    """
    logger.info("Starting monthly update orchestration")
    
    # Create orchestration configuration
    orchestration_config = OrchestrationConfig(
        max_concurrent_instances=2,
        instance_timeout_hours=12,
        retry_failed_instances=True,
        max_retry_attempts=2,
        cleanup_old_reports=True,
        report_retention_days=90,
        enable_notifications=True
    )
    
    # Create and run orchestrator
    orchestrator = MonthlyUpdateOrchestrator(orchestration_config=orchestration_config)
    
    result = await orchestrator.run_monthly_updates(
        instance_configs=instance_configs,
        force_update=force_update
    )
    
    logger.info(f"Monthly update orchestration completed: {result.orchestration_id}")
    logger.info(f"Success rate: {result.success_rate:.1f}%")
    logger.info(f"Total papers processed: {result.total_papers_processed}")
    
    if result.failed_instances:
        logger.error(f"Failed instances: {', '.join(result.failed_instances)}")
        raise Exception(f"Monthly update failed for instances: {', '.join(result.failed_instances)}")
    
    return result


async def main():
    """Main entry point for scheduled monthly update."""
    parser = argparse.ArgumentParser(description="Run scheduled monthly update with validation")
    
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
        '--skip-health-check',
        action='store_true',
        help='Skip pre-execution health check'
    )
    
    parser.add_argument(
        '--skip-conflict-resolution',
        action='store_true',
        help='Skip conflict detection and resolution'
    )
    
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum number of retry attempts'
    )
    
    parser.add_argument(
        '--timeout-minutes',
        type=int,
        default=720,  # 12 hours
        help='Timeout for the entire operation in minutes'
    )
    
    parser.add_argument(
        '--report-file',
        type=str,
        help='Output file for execution report'
    )
    
    args = parser.parse_args()
    
    # Log startup information
    logger.info("=== Scheduled Monthly Update Started ===")
    logger.info(f"Start time: {datetime.now().isoformat()}")
    logger.info(f"Arguments: {vars(args)}")
    
    try:
        # Load instance configurations
        instance_configs = load_instance_configs(args.config_dir)
        
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
        for config in instance_configs:
            logger.info(f"  - {config.instance_name}: {config.display_name}")
        
        # Create scheduling configuration
        scheduling_config = SchedulingConfig(
            enable_health_checks=not args.skip_health_check,
            enable_conflict_resolution=not args.skip_conflict_resolution,
            enable_error_recovery=True,
            max_retry_attempts=args.max_retries,
            health_check_timeout_minutes=10,
            conflict_resolution_timeout_minutes=30,
            pre_execution_delay_minutes=2,
            post_execution_cleanup=True,
            notification_on_failure=True
        )
        
        # Create error recovery configuration
        recovery_config = RecoveryConfig(
            max_retry_attempts=args.max_retries,
            base_delay_seconds=60.0,  # 1 minute base delay
            max_delay_seconds=1800.0,  # 30 minutes max delay
            exponential_base=2.0,
            circuit_breaker_threshold=3,
            circuit_breaker_timeout_minutes=60,
            enable_intelligent_retry=True
        )
        
        # Initialize automated scheduler
        scheduler = AutomatedScheduler(
            config=scheduling_config,
            recovery_config=recovery_config
        )
        
        # Execute monthly update with comprehensive validation
        execution_result = await asyncio.wait_for(
            scheduler.execute_with_validation(
                operation_name="monthly_update",
                operation_func=run_monthly_update_with_orchestrator,
                instance_configs=instance_configs,
                instance_configs=instance_configs,
                force_update=args.force
            ),
            timeout=args.timeout_minutes * 60
        )
        
        # Log execution results
        logger.info("=== Scheduled Monthly Update Completed ===")
        logger.info(f"Execution ID: {execution_result.execution_id}")
        logger.info(f"Success: {execution_result.success}")
        logger.info(f"Health check passed: {execution_result.health_check_passed}")
        logger.info(f"Conflicts resolved: {execution_result.conflicts_resolved}")
        logger.info(f"Retry count: {execution_result.retry_count}")
        
        if execution_result.error_message:
            logger.error(f"Error: {execution_result.error_message}")
        
        # Export execution report if requested
        if args.report_file:
            report_path = Path(args.report_file)
            success = scheduler.export_execution_report(report_path)
            if success:
                logger.info(f"Execution report saved to: {report_path}")
            else:
                logger.warning("Failed to save execution report")
        
        # Return appropriate exit code
        return 0 if execution_result.success else 1
        
    except asyncio.TimeoutError:
        logger.error(f"Monthly update timed out after {args.timeout_minutes} minutes")
        return 1
    except Exception as e:
        logger.error(f"Scheduled monthly update failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        logger.info(f"End time: {datetime.now().isoformat()}")


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)