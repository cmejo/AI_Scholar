#!/usr/bin/env python3
"""
Run monthly updates with comprehensive reporting and notifications.

This script integrates the monthly update orchestrator with the reporting
coordinator to provide complete update reporting and notification functionality.
"""

import asyncio
import logging
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from ..shared.multi_instance_data_models import (
    InstanceConfig, NotificationConfig, StorageStats
)
from ..config.instance_config_manager import InstanceConfigManager
from ..reporting.reporting_coordinator import ReportingCoordinator, ReportingConfig
from .monthly_update_orchestrator import MonthlyUpdateOrchestrator, OrchestrationConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/multi_instance_arxiv/monthly_update_with_reporting.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class MonthlyUpdateWithReporting:
    """Orchestrates monthly updates with comprehensive reporting and notifications."""
    
    def __init__(self, 
                 config_directory: str = None,
                 enable_notifications: bool = True,
                 enable_storage_monitoring: bool = True):
        """
        Initialize monthly update with reporting.
        
        Args:
            config_directory: Directory containing instance configurations
            enable_notifications: Enable email notifications
            enable_storage_monitoring: Enable storage monitoring and alerts
        """
        self.config_directory = Path(config_directory or 
                                   Path(__file__).parent.parent / "configs")
        
        # Initialize configuration manager
        self.config_manager = InstanceConfigManager(str(self.config_directory))
        
        # Initialize orchestration configuration
        self.orchestration_config = OrchestrationConfig(
            max_concurrent_instances=2,
            instance_timeout_hours=12,
            retry_failed_instances=True,
            max_retry_attempts=2,
            cleanup_old_reports=True,
            enable_notifications=enable_notifications
        )
        
        # Initialize reporting configuration
        self.reporting_config = ReportingConfig(
            enable_comprehensive_reports=True,
            enable_notifications=enable_notifications,
            enable_storage_monitoring=enable_storage_monitoring,
            storage_alert_threshold=85.0,
            storage_critical_threshold=95.0,
            auto_cleanup_reports=True,
            report_retention_days=90
        )
        
        # Initialize notification configuration
        self.notification_config = NotificationConfig(
            enabled=enable_notifications,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            username="",  # Set via environment variables
            password="",  # Set via environment variables
            from_email="noreply@aischolar.com",
            recipients=["admin@aischolar.com"]  # Configure as needed
        )
        
        # Initialize components
        self.orchestrator = MonthlyUpdateOrchestrator(
            orchestration_config=self.orchestration_config
        )
        
        self.reporting_coordinator = ReportingCoordinator(
            reporting_config=self.reporting_config,
            notification_config=self.notification_config
        )
        
        logger.info("MonthlyUpdateWithReporting initialized")
    
    async def run_monthly_updates(self, 
                                instance_names: Optional[List[str]] = None,
                                force_update: bool = False,
                                dry_run: bool = False) -> Dict[str, Any]:
        """
        Run monthly updates with comprehensive reporting.
        
        Args:
            instance_names: Specific instances to update (None for all)
            force_update: Force update even if recently updated
            dry_run: Perform validation only, don't run actual updates
            
        Returns:
            Dictionary with orchestration and reporting results
        """
        logger.info("Starting monthly updates with comprehensive reporting")
        
        try:
            # Load instance configurations
            instance_configs = await self._load_instance_configurations(instance_names)
            
            if not instance_configs:
                raise RuntimeError("No valid instance configurations found")
            
            logger.info(f"Loaded {len(instance_configs)} instance configurations")
            
            if dry_run:
                logger.info("Dry run mode - validating configurations only")
                return await self._validate_configurations(instance_configs)
            
            # Run orchestrated updates
            orchestration_result = await self.orchestrator.run_monthly_updates(
                instance_configs, force_update=force_update
            )
            
            logger.info(f"Orchestration completed: {orchestration_result.orchestration_id}")
            logger.info(f"Success rate: {orchestration_result.success_rate:.1f}%")
            
            # Process reporting and notifications
            reporting_result = await self.reporting_coordinator.process_update_completion(
                orchestration_result.instance_reports,
                orchestration_result.orchestration_id
            )
            
            logger.info(f"Reporting completed: success={reporting_result.success}")
            
            # Return comprehensive results
            return {
                'orchestration': {
                    'orchestration_id': orchestration_result.orchestration_id,
                    'success_rate': orchestration_result.success_rate,
                    'total_papers_processed': orchestration_result.total_papers_processed,
                    'total_errors': orchestration_result.total_errors,
                    'duration_seconds': orchestration_result.duration_seconds,
                    'failed_instances': orchestration_result.failed_instances,
                    'skipped_instances': orchestration_result.skipped_instances
                },
                'reporting': {
                    'success': reporting_result.success,
                    'comprehensive_report_id': (
                        reporting_result.comprehensive_report.report_id 
                        if reporting_result.comprehensive_report else None
                    ),
                    'notifications_sent': len(reporting_result.notification_results),
                    'storage_alerts_sent': reporting_result.storage_alerts_sent,
                    'errors': reporting_result.errors
                },
                'summary': {
                    'overall_success': (
                        orchestration_result.success_rate >= 75 and 
                        reporting_result.success
                    ),
                    'instances_processed': len(orchestration_result.instance_reports),
                    'total_processing_time_hours': orchestration_result.duration_seconds / 3600 if orchestration_result.duration_seconds else 0,
                    'notification_success_rate': self._calculate_notification_success_rate(reporting_result)
                }
            }
            
        except Exception as e:
            logger.error(f"Monthly updates with reporting failed: {e}")
            
            # Send failure notification
            try:
                await self._send_failure_notification(str(e))
            except Exception as notification_error:
                logger.error(f"Failed to send failure notification: {notification_error}")
            
            raise
    
    async def _load_instance_configurations(self, 
                                          instance_names: Optional[List[str]]) -> List[InstanceConfig]:
        """Load instance configurations."""
        try:
            # Get all available configurations
            all_configs = self.config_manager.load_all_configs()
            
            if instance_names:
                # Filter to specific instances
                configs = [
                    config for config in all_configs 
                    if config.instance_name in instance_names
                ]
                
                missing_instances = set(instance_names) - {c.instance_name for c in configs}
                if missing_instances:
                    logger.warning(f"Missing configurations for instances: {missing_instances}")
            else:
                # Use all available configurations
                configs = all_configs
            
            logger.info(f"Loaded configurations for instances: {[c.instance_name for c in configs]}")
            return configs
            
        except Exception as e:
            logger.error(f"Failed to load instance configurations: {e}")
            raise
    
    async def _validate_configurations(self, 
                                     instance_configs: List[InstanceConfig]) -> Dict[str, Any]:
        """Validate instance configurations in dry run mode."""
        validation_results = {
            'valid_instances': [],
            'invalid_instances': [],
            'validation_errors': [],
            'storage_status': {},
            'system_readiness': True
        }
        
        for config in instance_configs:
            try:
                # Validate storage paths
                storage_paths = config.storage_paths
                required_paths = [
                    storage_paths.pdf_directory,
                    storage_paths.processed_directory,
                    storage_paths.state_directory,
                    storage_paths.error_log_directory
                ]
                
                for path_str in required_paths:
                    path = Path(path_str)
                    if not path.exists():
                        path.mkdir(parents=True, exist_ok=True)
                    
                    if not os.access(path, os.W_OK):
                        raise RuntimeError(f"No write permission: {path}")
                
                # Check storage space
                import shutil
                disk_usage = shutil.disk_usage(Path(storage_paths.pdf_directory).parent)
                usage_percentage = ((disk_usage.total - disk_usage.free) / disk_usage.total) * 100
                
                validation_results['storage_status'][config.instance_name] = {
                    'usage_percentage': usage_percentage,
                    'available_gb': disk_usage.free / (1024**3),
                    'status': 'ok' if usage_percentage < 90 else 'warning'
                }
                
                validation_results['valid_instances'].append(config.instance_name)
                logger.info(f"Validation successful for instance: {config.instance_name}")
                
            except Exception as e:
                validation_results['invalid_instances'].append(config.instance_name)
                validation_results['validation_errors'].append(f"{config.instance_name}: {e}")
                validation_results['system_readiness'] = False
                logger.error(f"Validation failed for instance {config.instance_name}: {e}")
        
        return validation_results
    
    def _calculate_notification_success_rate(self, reporting_result) -> float:
        """Calculate notification success rate."""
        if not reporting_result.notification_results:
            return 0.0
        
        successful_notifications = sum(
            1 for result in reporting_result.notification_results 
            if result.success
        )
        
        return (successful_notifications / len(reporting_result.notification_results)) * 100
    
    async def _send_failure_notification(self, error_message: str) -> None:
        """Send notification about update failure."""
        try:
            # Create a simple failure notification
            failure_context = {
                'timestamp': datetime.now(),
                'error_message': error_message,
                'failed_instances': [],
                'successful_instances': [],
                'error_details': error_message
            }
            
            # Use the notification service directly
            await self.reporting_coordinator.notification_service._send_notification(
                template_name="update_failure.html",
                subject="Monthly Update System Failure",
                context=failure_context,
                priority="critical"
            )
            
        except Exception as e:
            logger.error(f"Failed to send failure notification: {e}")
    
    async def test_notification_system(self) -> Dict[str, Any]:
        """Test the notification system configuration."""
        logger.info("Testing notification system")
        
        try:
            # Test notification setup
            test_result = await self.reporting_coordinator.send_test_notification()
            
            # Get notification statistics
            stats = self.reporting_coordinator.get_reporting_statistics()
            
            return {
                'test_result': test_result.to_dict(),
                'notification_stats': stats['notifications'],
                'configuration': {
                    'smtp_server': self.notification_config.smtp_server,
                    'smtp_port': self.notification_config.smtp_port,
                    'recipients_count': len(self.notification_config.recipients),
                    'enabled': self.notification_config.enabled
                }
            }
            
        except Exception as e:
            logger.error(f"Notification system test failed: {e}")
            return {
                'test_result': {'success': False, 'message': str(e)},
                'error': str(e)
            }
    
    async def generate_storage_report(self) -> Dict[str, Any]:
        """Generate storage monitoring report."""
        logger.info("Generating storage monitoring report")
        
        try:
            # Load instance configurations
            instance_configs = await self._load_instance_configurations(None)
            
            # Create mock update reports for storage analysis
            mock_reports = {}
            for config in instance_configs:
                # Calculate current storage usage
                import shutil
                storage_path = Path(config.storage_paths.pdf_directory).parent
                
                pdf_size = sum(
                    f.stat().st_size for f in Path(config.storage_paths.pdf_directory).rglob('*') 
                    if f.is_file()
                )
                processed_size = sum(
                    f.stat().st_size for f in Path(config.storage_paths.processed_directory).rglob('*') 
                    if f.is_file()
                )
                
                storage_used_mb = int((pdf_size + processed_size) / (1024 * 1024))
                
                # Create mock update report
                from ..shared.multi_instance_data_models import UpdateReport
                mock_reports[config.instance_name] = UpdateReport(
                    instance_name=config.instance_name,
                    update_date=datetime.now(),
                    papers_discovered=0,
                    papers_downloaded=0,
                    papers_processed=0,
                    papers_failed=0,
                    storage_used_mb=storage_used_mb,
                    processing_time_seconds=0.0,
                    errors=[],
                    storage_stats=StorageStats(
                        total_space_gb=0.0,
                        used_space_gb=0.0,
                        available_space_gb=0.0,
                        usage_percentage=0.0,
                        instance_breakdown={}
                    ),
                    performance_metrics=None
                )
            
            # Generate storage recommendations
            recommendations = await self.reporting_coordinator.generate_storage_recommendations(
                mock_reports
            )
            
            return {
                'storage_usage_by_instance': {
                    name: report.storage_used_mb / 1024.0 
                    for name, report in mock_reports.items()
                },
                'total_storage_gb': sum(
                    report.storage_used_mb / 1024.0 
                    for report in mock_reports.values()
                ),
                'recommendations': recommendations,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Storage report generation failed: {e}")
            return {'error': str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        try:
            # Get orchestration status
            orchestration_status = self.orchestrator.get_orchestration_status()
            
            # Get reporting statistics
            reporting_stats = self.reporting_coordinator.get_reporting_statistics()
            
            # Get latest reports
            latest_reports = self.reporting_coordinator.get_latest_comprehensive_reports(5)
            
            return {
                'orchestration': orchestration_status,
                'reporting': reporting_stats,
                'latest_reports': latest_reports,
                'system_health': {
                    'orchestrator_ready': True,
                    'reporting_ready': True,
                    'notifications_enabled': self.notification_config.enabled,
                    'storage_monitoring_enabled': self.reporting_config.enable_storage_monitoring
                },
                'configuration': {
                    'max_concurrent_instances': self.orchestration_config.max_concurrent_instances,
                    'instance_timeout_hours': self.orchestration_config.instance_timeout_hours,
                    'storage_alert_threshold': self.reporting_config.storage_alert_threshold,
                    'report_retention_days': self.reporting_config.report_retention_days
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {'error': str(e)}


async def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Run monthly updates with comprehensive reporting")
    parser.add_argument('--instances', nargs='+', help='Specific instances to update')
    parser.add_argument('--force', action='store_true', help='Force update even if recently updated')
    parser.add_argument('--dry-run', action='store_true', help='Validate configurations only')
    parser.add_argument('--test-notifications', action='store_true', help='Test notification system')
    parser.add_argument('--storage-report', action='store_true', help='Generate storage report')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--config-dir', help='Configuration directory path')
    parser.add_argument('--no-notifications', action='store_true', help='Disable notifications')
    parser.add_argument('--no-storage-monitoring', action='store_true', help='Disable storage monitoring')
    
    args = parser.parse_args()
    
    try:
        # Initialize the system
        update_system = MonthlyUpdateWithReporting(
            config_directory=args.config_dir,
            enable_notifications=not args.no_notifications,
            enable_storage_monitoring=not args.no_storage_monitoring
        )
        
        if args.test_notifications:
            # Test notification system
            result = await update_system.test_notification_system()
            print("Notification Test Results:")
            print(json.dumps(result, indent=2, default=str))
            
        elif args.storage_report:
            # Generate storage report
            result = await update_system.generate_storage_report()
            print("Storage Report:")
            print(json.dumps(result, indent=2, default=str))
            
        elif args.status:
            # Show system status
            result = update_system.get_system_status()
            print("System Status:")
            print(json.dumps(result, indent=2, default=str))
            
        else:
            # Run monthly updates
            result = await update_system.run_monthly_updates(
                instance_names=args.instances,
                force_update=args.force,
                dry_run=args.dry_run
            )
            
            print("Monthly Update Results:")
            print(json.dumps(result, indent=2, default=str))
            
            # Exit with appropriate code
            if result.get('summary', {}).get('overall_success', False):
                print("\nMonthly updates completed successfully!")
                sys.exit(0)
            else:
                print("\nMonthly updates completed with issues. Check logs for details.")
                sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import json
    import os
    asyncio.run(main())