#!/usr/bin/env python3
"""
Comprehensive test for Task 5.3: Update reporting and notifications.

Tests the complete integration of update reporting, comprehensive report generation,
email notifications, and storage monitoring alerts.
"""

import asyncio
import logging
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import unittest
from unittest.mock import Mock, patch, AsyncMock

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from shared.multi_instance_data_models import (
    UpdateReport, InstanceConfig, StoragePaths, ProcessingConfig, 
    NotificationConfig, StorageStats, PerformanceMetrics
)
from reporting.update_reporter import UpdateReporter, ComprehensiveUpdateReport
from reporting.notification_service import NotificationService
from reporting.reporting_coordinator import ReportingCoordinator, ReportingConfig
from scheduling.run_with_reporting import MonthlyUpdateWithReporting

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestTask53Implementation(unittest.TestCase):
    """Test suite for Task 5.3 implementation."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.reports_dir = self.temp_dir / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test instance configurations
        self.test_configs = self._create_test_configs()
        
        # Create test update reports
        self.test_reports = self._create_test_update_reports()
        
        logger.info(f"Test environment set up in: {self.temp_dir}")
    
    def tearDown(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        logger.info("Test environment cleaned up")
    
    def _create_test_configs(self) -> List[InstanceConfig]:
        """Create test instance configurations."""
        configs = []
        
        for instance_name in ['ai_scholar', 'quant_scholar']:
            instance_dir = self.temp_dir / instance_name
            instance_dir.mkdir(parents=True, exist_ok=True)
            
            config = InstanceConfig(
                instance_name=instance_name,
                arxiv_categories=['cs.AI', 'stat.ML'] if 'ai' in instance_name else ['q-fin.*', 'stat.*'],
                journal_sources=[],
                storage_paths=StoragePaths(
                    pdf_directory=str(instance_dir / "pdf"),
                    processed_directory=str(instance_dir / "processed"),
                    state_directory=str(instance_dir / "state"),
                    error_log_directory=str(instance_dir / "logs"),
                    archive_directory=str(instance_dir / "archive")
                ),
                vector_store_config={},
                processing_config=ProcessingConfig(
                    batch_size=10,
                    max_concurrent_downloads=3,
                    max_concurrent_processing=2,
                    retry_attempts=2,
                    timeout_seconds=300,
                    memory_limit_mb=1024
                ),
                notification_config=NotificationConfig(
                    enabled=True,
                    smtp_server="smtp.test.com",
                    smtp_port=587,
                    username="test@test.com",
                    password="test_password",
                    from_email="noreply@test.com",
                    recipients=["admin@test.com"]
                )
            )
            
            # Create directories
            for path in [config.storage_paths.pdf_directory, 
                        config.storage_paths.processed_directory,
                        config.storage_paths.state_directory,
                        config.storage_paths.error_log_directory]:
                Path(path).mkdir(parents=True, exist_ok=True)
            
            configs.append(config)
        
        return configs
    
    def _create_test_update_reports(self) -> Dict[str, UpdateReport]:
        """Create test update reports."""
        reports = {}
        
        for i, config in enumerate(self.test_configs):
            # Create realistic test data
            papers_processed = 50 + i * 25
            errors_count = i * 2  # ai_scholar: 0 errors, quant_scholar: 2 errors
            
            errors = []
            if errors_count > 0:
                for j in range(errors_count):
                    errors.append({
                        'error_type': 'processing_error',
                        'error_message': f'Test error {j+1} for {config.instance_name}',
                        'timestamp': datetime.now().isoformat(),
                        'file_path': f'/test/path/paper_{j+1}.pdf'
                    })
            
            report = UpdateReport(
                instance_name=config.instance_name,
                update_date=datetime.now(),
                papers_discovered=papers_processed + 10,
                papers_downloaded=papers_processed + 5,
                papers_processed=papers_processed,
                papers_failed=errors_count,
                storage_used_mb=5000 + i * 2000,  # 5GB, 7GB
                processing_time_seconds=3600 + i * 1800,  # 1h, 1.5h
                errors=errors,
                storage_stats=StorageStats(
                    total_space_gb=100.0,
                    used_space_gb=50.0 + i * 10,
                    available_space_gb=50.0 - i * 10,
                    usage_percentage=50.0 + i * 10,
                    instance_breakdown={config.instance_name: 5.0 + i * 2}
                ),
                performance_metrics=PerformanceMetrics(
                    processing_rate_papers_per_hour=papers_processed / ((3600 + i * 1800) / 3600),
                    memory_usage_peak_mb=512 + i * 256,
                    cpu_usage_average_percent=30.0 + i * 10,
                    error_rate_percentage=(errors_count / papers_processed * 100) if papers_processed > 0 else 0
                )
            )
            
            reports[config.instance_name] = report
        
        return reports
    
    async def test_update_reporter_comprehensive_report_generation(self):
        """Test comprehensive report generation."""
        logger.info("Testing comprehensive report generation")
        
        # Initialize update reporter
        update_reporter = UpdateReporter(str(self.reports_dir))
        
        # Generate comprehensive report
        orchestration_id = "test_orchestration_001"
        comprehensive_report = await update_reporter.generate_comprehensive_report(
            self.test_reports, orchestration_id
        )
        
        # Validate comprehensive report
        self.assertIsInstance(comprehensive_report, ComprehensiveUpdateReport)
        self.assertEqual(comprehensive_report.report_id, f"comprehensive_report_{orchestration_id}")
        self.assertEqual(len(comprehensive_report.instance_reports), 2)
        
        # Validate system summary
        system_summary = comprehensive_report.system_summary
        self.assertEqual(system_summary.total_instances, 2)
        self.assertEqual(system_summary.successful_instances, 1)  # ai_scholar has no errors
        self.assertEqual(system_summary.failed_instances, 1)     # quant_scholar has errors
        self.assertEqual(system_summary.total_papers_processed, 75)  # 50 + 25
        self.assertEqual(system_summary.total_errors, 2)
        
        # Validate comparison metrics
        self.assertIn('ai_scholar', comprehensive_report.comparison_metrics)
        self.assertIn('quant_scholar', comprehensive_report.comparison_metrics)
        
        # Validate storage recommendations
        self.assertIsInstance(comprehensive_report.storage_recommendations, list)
        
        # Validate error analysis
        self.assertIn('total_errors', comprehensive_report.error_analysis)
        self.assertEqual(comprehensive_report.error_analysis['total_errors'], 2)
        
        # Validate performance insights
        self.assertIn('processing_rates', comprehensive_report.performance_insights)
        
        logger.info("✓ Comprehensive report generation test passed")
    
    async def test_notification_service_email_generation(self):
        """Test email notification generation."""
        logger.info("Testing email notification generation")
        
        # Create notification config
        notification_config = NotificationConfig(
            enabled=True,
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="test_password",
            from_email="noreply@test.com",
            recipients=["admin@test.com", "user@test.com"]
        )
        
        # Initialize notification service
        notification_service = NotificationService(
            notification_config,
            str(self.temp_dir / "templates")
        )
        
        # Create test comprehensive report
        update_reporter = UpdateReporter(str(self.reports_dir))
        comprehensive_report = await update_reporter.generate_comprehensive_report(
            self.test_reports, "test_orchestration_002"
        )
        
        # Mock SMTP to avoid actual email sending
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            # Test update completion notification
            result = await notification_service.send_update_completion_notification(
                comprehensive_report
            )
            
            # Validate notification result
            self.assertTrue(result.success)
            self.assertEqual(len(result.recipients_sent), 2)
            self.assertEqual(len(result.recipients_failed), 0)
            
            # Verify SMTP calls
            mock_smtp.assert_called_once()
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
        
        logger.info("✓ Email notification generation test passed")
    
    async def test_storage_alert_notifications(self):
        """Test storage alert notifications."""
        logger.info("Testing storage alert notifications")
        
        # Create notification config
        notification_config = NotificationConfig(
            enabled=True,
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="test_password",
            from_email="noreply@test.com",
            recipients=["admin@test.com"]
        )
        
        # Initialize notification service
        notification_service = NotificationService(
            notification_config,
            str(self.temp_dir / "templates")
        )
        
        # Create high storage usage scenario
        storage_stats = {
            'total_storage_gb': 100.0,
            'usage_percentage': 92.0,  # Above warning threshold
            'instance_breakdown': {
                'ai_scholar': 45.0,
                'quant_scholar': 47.0
            }
        }
        
        # Create storage recommendations
        from reporting.update_reporter import StorageRecommendation
        recommendations = [
            StorageRecommendation(
                recommendation_type="cleanup",
                priority="high",
                description="Clean up old PDF files to free space",
                estimated_space_savings_gb=15.0,
                action_required=True,
                commands=["find /datapool -name '*.pdf' -mtime +90 -delete"]
            )
        ]
        
        # Mock SMTP to avoid actual email sending
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            # Test storage alert notification
            result = await notification_service.send_storage_alert_notification(
                storage_stats, recommendations
            )
            
            # Validate notification result
            self.assertTrue(result.success)
            self.assertEqual(len(result.recipients_sent), 1)
            
            # Verify SMTP calls
            mock_smtp.assert_called_once()
        
        logger.info("✓ Storage alert notifications test passed")
    
    async def test_reporting_coordinator_integration(self):
        """Test reporting coordinator integration."""
        logger.info("Testing reporting coordinator integration")
        
        # Create reporting configuration
        reporting_config = ReportingConfig(
            enable_comprehensive_reports=True,
            enable_notifications=True,
            enable_storage_monitoring=True,
            storage_alert_threshold=85.0,
            storage_critical_threshold=95.0,
            auto_cleanup_reports=True,
            report_retention_days=90
        )
        
        # Create notification configuration
        notification_config = NotificationConfig(
            enabled=True,
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="test_password",
            from_email="noreply@test.com",
            recipients=["admin@test.com"]
        )
        
        # Initialize reporting coordinator
        reporting_coordinator = ReportingCoordinator(
            reporting_config=reporting_config,
            notification_config=notification_config,
            reports_directory=str(self.reports_dir)
        )
        
        # Mock SMTP to avoid actual email sending
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            # Process update completion
            orchestration_id = "test_orchestration_003"
            reporting_result = await reporting_coordinator.process_update_completion(
                self.test_reports, orchestration_id
            )
            
            # Validate reporting result
            self.assertTrue(reporting_result.success)
            self.assertIsNotNone(reporting_result.comprehensive_report)
            self.assertGreater(len(reporting_result.notification_results), 0)
            
            # Validate comprehensive report was generated
            self.assertEqual(
                reporting_result.comprehensive_report.report_id,
                f"comprehensive_report_{orchestration_id}"
            )
            
            # Validate notifications were sent
            successful_notifications = sum(
                1 for result in reporting_result.notification_results 
                if result.success
            )
            self.assertGreater(successful_notifications, 0)
        
        logger.info("✓ Reporting coordinator integration test passed")
    
    async def test_monthly_update_with_reporting_dry_run(self):
        """Test monthly update with reporting in dry run mode."""
        logger.info("Testing monthly update with reporting (dry run)")
        
        # Create temporary config directory
        config_dir = self.temp_dir / "configs"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create config files
        for config in self.test_configs:
            config_file = config_dir / f"{config.instance_name}.yaml"
            config_data = {
                'instance': {
                    'name': config.instance_name,
                    'display_name': config.instance_name.replace('_', ' ').title()
                },
                'storage': {
                    'pdf_directory': config.storage_paths.pdf_directory,
                    'processed_directory': config.storage_paths.processed_directory,
                    'state_directory': config.storage_paths.state_directory
                }
            }
            
            import yaml
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f)
        
        # Initialize monthly update system
        with patch('backend.multi_instance_arxiv_system.config.instance_config_manager.InstanceConfigManager.load_all_configs') as mock_load:
            mock_load.return_value = self.test_configs
            
            update_system = MonthlyUpdateWithReporting(
                config_directory=str(config_dir),
                enable_notifications=False,  # Disable for dry run
                enable_storage_monitoring=True
            )
            
            # Run dry run
            result = await update_system.run_monthly_updates(
                instance_names=['ai_scholar', 'quant_scholar'],
                force_update=False,
                dry_run=True
            )
            
            # Validate dry run results
            self.assertIn('valid_instances', result)
            self.assertIn('invalid_instances', result)
            self.assertIn('storage_status', result)
            self.assertTrue(result['system_readiness'])
            
            # Validate instances were validated
            self.assertEqual(len(result['valid_instances']), 2)
            self.assertEqual(len(result['invalid_instances']), 0)
        
        logger.info("✓ Monthly update with reporting (dry run) test passed")
    
    async def test_storage_report_generation(self):
        """Test storage report generation."""
        logger.info("Testing storage report generation")
        
        # Create some test files to simulate storage usage
        for config in self.test_configs:
            pdf_dir = Path(config.storage_paths.pdf_directory)
            processed_dir = Path(config.storage_paths.processed_directory)
            
            # Create test PDF files
            for i in range(5):
                test_file = pdf_dir / f"test_paper_{i}.pdf"
                test_file.write_text("Test PDF content" * 1000)  # ~17KB each
            
            # Create test processed files
            for i in range(3):
                test_file = processed_dir / f"processed_{i}.json"
                test_file.write_text('{"test": "data"}' * 500)  # ~7KB each
        
        # Initialize monthly update system
        with patch('backend.multi_instance_arxiv_system.config.instance_config_manager.InstanceConfigManager.load_all_configs') as mock_load:
            mock_load.return_value = self.test_configs
            
            update_system = MonthlyUpdateWithReporting(
                config_directory=str(self.temp_dir / "configs"),
                enable_notifications=False,
                enable_storage_monitoring=True
            )
            
            # Generate storage report
            storage_report = await update_system.generate_storage_report()
            
            # Validate storage report
            self.assertIn('storage_usage_by_instance', storage_report)
            self.assertIn('total_storage_gb', storage_report)
            self.assertIn('recommendations', storage_report)
            self.assertIn('generated_at', storage_report)
            
            # Validate instance storage data
            self.assertEqual(len(storage_report['storage_usage_by_instance']), 2)
            for instance_name in ['ai_scholar', 'quant_scholar']:
                self.assertIn(instance_name, storage_report['storage_usage_by_instance'])
                self.assertGreater(storage_report['storage_usage_by_instance'][instance_name], 0)
        
        logger.info("✓ Storage report generation test passed")
    
    def test_error_analysis_functionality(self):
        """Test error analysis functionality."""
        logger.info("Testing error analysis functionality")
        
        # Create update reporter
        update_reporter = UpdateReporter(str(self.reports_dir))
        
        # Test error analysis with the test reports
        error_analysis = asyncio.run(
            update_reporter._analyze_errors(self.test_reports)
        )
        
        # Validate error analysis
        self.assertIn('total_errors', error_analysis)
        self.assertIn('error_by_instance', error_analysis)
        self.assertIn('common_error_patterns', error_analysis)
        self.assertIn('error_trends', error_analysis)
        
        # Validate error counts
        self.assertEqual(error_analysis['total_errors'], 2)
        self.assertEqual(error_analysis['error_by_instance']['ai_scholar'], 0)
        self.assertEqual(error_analysis['error_by_instance']['quant_scholar'], 2)
        
        # Validate error trends
        self.assertEqual(error_analysis['error_trends']['instances_with_errors'], 1)
        self.assertEqual(error_analysis['error_trends']['average_errors_per_instance'], 1.0)
        
        logger.info("✓ Error analysis functionality test passed")
    
    def test_performance_analysis_functionality(self):
        """Test performance analysis functionality."""
        logger.info("Testing performance analysis functionality")
        
        # Create update reporter
        update_reporter = UpdateReporter(str(self.reports_dir))
        
        # Test performance analysis with the test reports
        performance_insights = asyncio.run(
            update_reporter._analyze_performance(self.test_reports)
        )
        
        # Validate performance insights
        self.assertIn('processing_rates', performance_insights)
        self.assertIn('efficiency_metrics', performance_insights)
        self.assertIn('resource_utilization', performance_insights)
        self.assertIn('bottlenecks', performance_insights)
        self.assertIn('recommendations', performance_insights)
        
        # Validate processing rates
        self.assertEqual(len(performance_insights['processing_rates']), 2)
        for instance_name in ['ai_scholar', 'quant_scholar']:
            self.assertIn(instance_name, performance_insights['processing_rates'])
            self.assertGreater(performance_insights['processing_rates'][instance_name], 0)
        
        # Validate resource utilization
        self.assertIn('average_processing_time_hours', performance_insights['resource_utilization'])
        self.assertIn('average_papers_processed', performance_insights['resource_utilization'])
        
        logger.info("✓ Performance analysis functionality test passed")


async def run_comprehensive_tests():
    """Run all comprehensive tests for Task 5.3."""
    logger.info("Starting comprehensive tests for Task 5.3: Update reporting and notifications")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    test_case = TestTask53Implementation()
    
    # Add async tests
    async_tests = [
        'test_update_reporter_comprehensive_report_generation',
        'test_notification_service_email_generation',
        'test_storage_alert_notifications',
        'test_reporting_coordinator_integration',
        'test_monthly_update_with_reporting_dry_run',
        'test_storage_report_generation'
    ]
    
    # Add sync tests
    sync_tests = [
        'test_error_analysis_functionality',
        'test_performance_analysis_functionality'
    ]
    
    try:
        # Run async tests
        for test_name in async_tests:
            logger.info(f"Running {test_name}")
            test_case.setUp()
            try:
                await getattr(test_case, test_name)()
                logger.info(f"✓ {test_name} PASSED")
            except Exception as e:
                logger.error(f"✗ {test_name} FAILED: {e}")
                raise
            finally:
                test_case.tearDown()
        
        # Run sync tests
        for test_name in sync_tests:
            logger.info(f"Running {test_name}")
            test_case.setUp()
            try:
                getattr(test_case, test_name)()
                logger.info(f"✓ {test_name} PASSED")
            except Exception as e:
                logger.error(f"✗ {test_name} FAILED: {e}")
                raise
            finally:
                test_case.tearDown()
        
        logger.info("🎉 All Task 5.3 tests PASSED!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Task 5.3 tests FAILED: {e}")
        return False


def main():
    """Main entry point."""
    try:
        success = asyncio.run(run_comprehensive_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()