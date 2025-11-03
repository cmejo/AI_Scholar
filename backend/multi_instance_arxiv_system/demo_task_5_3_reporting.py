#!/usr/bin/env python3
"""
Demonstration of Task 5.3: Update reporting and notifications.

This script demonstrates the complete workflow of update reporting,
comprehensive report generation, and email notifications.
"""

import asyncio
import logging
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from shared.multi_instance_data_models import (
    UpdateReport, InstanceConfig, StoragePaths, ProcessingConfig, 
    NotificationConfig, StorageStats, PerformanceMetrics
)
from reporting.update_reporter import UpdateReporter, ComprehensiveUpdateReport
from reporting.notification_service import NotificationService
from reporting.reporting_coordinator import ReportingCoordinator, ReportingConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Task53Demo:
    """Demonstration of Task 5.3 functionality."""
    
    def __init__(self):
        """Initialize demo environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.reports_dir = self.temp_dir / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Demo environment created: {self.temp_dir}")
    
    def cleanup(self):
        """Clean up demo environment."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        logger.info("Demo environment cleaned up")
    
    def create_sample_update_reports(self) -> Dict[str, UpdateReport]:
        """Create sample update reports for demonstration."""
        logger.info("Creating sample update reports")
        
        reports = {}
        
        # AI Scholar instance report (successful)
        ai_scholar_report = UpdateReport(
            instance_name="ai_scholar",
            update_date=datetime.now(),
            papers_discovered=125,
            papers_downloaded=120,
            papers_processed=118,
            papers_failed=2,
            storage_used_mb=8500,  # 8.5 GB
            processing_time_seconds=4200,  # 70 minutes
            errors=[
                {
                    'error_type': 'pdf_processing_error',
                    'error_message': 'Failed to extract text from corrupted PDF',
                    'timestamp': datetime.now().isoformat(),
                    'file_path': '/datapool/aischolar/ai-scholar-arxiv-dataset/pdf/2024.01.12345.pdf'
                },
                {
                    'error_type': 'network_timeout',
                    'error_message': 'Download timeout after 300 seconds',
                    'timestamp': datetime.now().isoformat(),
                    'file_path': '/datapool/aischolar/ai-scholar-arxiv-dataset/pdf/2024.01.67890.pdf'
                }
            ],
            storage_stats=StorageStats(
                total_space_gb=500.0,
                used_space_gb=245.0,
                available_space_gb=255.0,
                usage_percentage=49.0,
                instance_breakdown={'ai_scholar': 8.5, 'quant_scholar': 12.3}
            ),
            performance_metrics=PerformanceMetrics(
                processing_rate_papers_per_hour=101.1,  # 118 papers / 70 minutes * 60
                memory_usage_peak_mb=2048,
                cpu_usage_average_percent=45.2,
                error_rate_percentage=1.7  # 2 errors / 118 processed
            )
        )
        
        # Quant Scholar instance report (with more issues)
        quant_scholar_report = UpdateReport(
            instance_name="quant_scholar",
            update_date=datetime.now(),
            papers_discovered=85,
            papers_downloaded=78,
            papers_processed=72,
            papers_failed=6,
            storage_used_mb=12300,  # 12.3 GB
            processing_time_seconds=5400,  # 90 minutes
            errors=[
                {
                    'error_type': 'journal_access_error',
                    'error_message': 'Failed to access Journal of Statistical Software',
                    'timestamp': datetime.now().isoformat(),
                    'source': 'jss_handler'
                },
                {
                    'error_type': 'pdf_processing_error',
                    'error_message': 'Memory error during large PDF processing',
                    'timestamp': datetime.now().isoformat(),
                    'file_path': '/datapool/aischolar/quant-scholar-dataset/pdf/large_paper.pdf'
                },
                {
                    'error_type': 'vector_store_error',
                    'error_message': 'ChromaDB connection timeout',
                    'timestamp': datetime.now().isoformat(),
                    'operation': 'embedding_storage'
                },
                {
                    'error_type': 'disk_space_warning',
                    'error_message': 'Low disk space detected during processing',
                    'timestamp': datetime.now().isoformat(),
                    'available_space_gb': 15.2
                }
            ],
            storage_stats=StorageStats(
                total_space_gb=500.0,
                used_space_gb=257.3,
                available_space_gb=242.7,
                usage_percentage=51.5,
                instance_breakdown={'ai_scholar': 8.5, 'quant_scholar': 12.3}
            ),
            performance_metrics=PerformanceMetrics(
                processing_rate_papers_per_hour=48.0,  # 72 papers / 90 minutes * 60
                memory_usage_peak_mb=3072,
                cpu_usage_average_percent=62.8,
                error_rate_percentage=8.3  # 6 errors / 72 processed
            )
        )
        
        reports['ai_scholar'] = ai_scholar_report
        reports['quant_scholar'] = quant_scholar_report
        
        logger.info(f"Created {len(reports)} sample update reports")
        return reports
    
    async def demonstrate_comprehensive_report_generation(self, 
                                                        update_reports: Dict[str, UpdateReport]) -> ComprehensiveUpdateReport:
        """Demonstrate comprehensive report generation."""
        logger.info("=== Demonstrating Comprehensive Report Generation ===")
        
        # Initialize update reporter
        update_reporter = UpdateReporter(str(self.reports_dir))
        
        # Generate comprehensive report
        orchestration_id = f"demo_orchestration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Generating comprehensive report for orchestration: {orchestration_id}")
        
        comprehensive_report = await update_reporter.generate_comprehensive_report(
            update_reports, orchestration_id
        )
        
        # Display report summary
        logger.info("📊 Comprehensive Report Summary:")
        logger.info(f"  Report ID: {comprehensive_report.report_id}")
        logger.info(f"  Generated: {comprehensive_report.generated_at}")
        
        # System summary
        summary = comprehensive_report.system_summary
        logger.info(f"  Total Instances: {summary.total_instances}")
        logger.info(f"  Success Rate: {summary.success_rate:.1f}%")
        logger.info(f"  Papers Processed: {summary.total_papers_processed}")
        logger.info(f"  Total Errors: {summary.total_errors}")
        logger.info(f"  Processing Time: {summary.total_processing_time_hours:.1f} hours")
        logger.info(f"  Storage Used: {summary.total_storage_used_gb:.1f} GB")
        logger.info(f"  Health Status: {summary.overall_health_status}")
        
        # Instance details
        logger.info("📋 Instance Details:")
        for instance_name, report in comprehensive_report.instance_reports.items():
            logger.info(f"  {instance_name}:")
            logger.info(f"    Papers Processed: {report.papers_processed}")
            logger.info(f"    Errors: {len(report.errors)}")
            logger.info(f"    Storage: {report.storage_used_mb / 1024:.1f} GB")
            logger.info(f"    Processing Rate: {report.performance_metrics.processing_rate_papers_per_hour:.1f} papers/hour")
        
        # Storage recommendations
        if comprehensive_report.storage_recommendations:
            logger.info("💾 Storage Recommendations:")
            for rec in comprehensive_report.storage_recommendations:
                logger.info(f"  {rec.recommendation_type.title()} ({rec.priority} priority):")
                logger.info(f"    {rec.description}")
                if rec.estimated_space_savings_gb > 0:
                    logger.info(f"    Estimated savings: {rec.estimated_space_savings_gb:.1f} GB")
        
        # Error analysis
        if comprehensive_report.error_analysis['total_errors'] > 0:
            logger.info("🚨 Error Analysis:")
            logger.info(f"  Total Errors: {comprehensive_report.error_analysis['total_errors']}")
            logger.info(f"  Instances with Errors: {comprehensive_report.error_analysis['error_trends']['instances_with_errors']}")
            
            # Common error patterns
            if comprehensive_report.error_analysis['common_error_patterns']:
                logger.info("  Common Error Keywords:")
                for keyword, count in list(comprehensive_report.error_analysis['common_error_patterns'].items())[:5]:
                    logger.info(f"    {keyword}: {count}")
        
        # Performance insights
        if comprehensive_report.performance_insights['bottlenecks']:
            logger.info("⚡ Performance Bottlenecks:")
            for bottleneck in comprehensive_report.performance_insights['bottlenecks']:
                logger.info(f"  {bottleneck['instance']}: {bottleneck['issue']}")
        
        logger.info("✅ Comprehensive report generation completed")
        return comprehensive_report
    
    async def demonstrate_notification_system(self, 
                                            comprehensive_report: ComprehensiveUpdateReport):
        """Demonstrate email notification system."""
        logger.info("=== Demonstrating Email Notification System ===")
        
        # Create notification configuration
        notification_config = NotificationConfig(
            enabled=True,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            username="demo@example.com",
            password="demo_password",
            from_email="noreply@aischolar.com",
            recipients=["admin@aischolar.com", "researcher@aischolar.com"]
        )
        
        # Initialize notification service
        notification_service = NotificationService(
            notification_config,
            str(self.temp_dir / "templates")
        )
        
        logger.info("📧 Email Notification Configuration:")
        logger.info(f"  SMTP Server: {notification_config.smtp_server}:{notification_config.smtp_port}")
        logger.info(f"  From Email: {notification_config.from_email}")
        logger.info(f"  Recipients: {', '.join(notification_config.recipients)}")
        
        # Simulate sending update completion notification
        logger.info("📤 Simulating Update Completion Notification...")
        
        # Mock the SMTP sending to avoid actual email
        from unittest.mock import patch, Mock
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            # Send update completion notification
            result = await notification_service.send_update_completion_notification(
                comprehensive_report
            )
            
            logger.info(f"  Notification Result: {'✅ Success' if result.success else '❌ Failed'}")
            logger.info(f"  Message: {result.message}")
            logger.info(f"  Recipients Sent: {len(result.recipients_sent)}")
            logger.info(f"  Recipients Failed: {len(result.recipients_failed)}")
            
            # Verify SMTP interaction
            if mock_smtp.called:
                logger.info("  📨 SMTP Server Interaction: Simulated successfully")
                logger.info(f"    Server calls: {mock_smtp.call_count}")
                logger.info(f"    Login attempted: {mock_server.login.called}")
                logger.info(f"    Messages sent: {mock_server.send_message.call_count}")
        
        # Demonstrate storage alert notification
        logger.info("📤 Simulating Storage Alert Notification...")
        
        storage_stats = {
            'total_storage_gb': 500.0,
            'usage_percentage': 88.5,  # Above warning threshold
            'instance_breakdown': {
                'ai_scholar': 8.5,
                'quant_scholar': 12.3
            }
        }
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            # Send storage alert
            storage_result = await notification_service.send_storage_alert_notification(
                storage_stats, comprehensive_report.storage_recommendations
            )
            
            logger.info(f"  Storage Alert Result: {'✅ Success' if storage_result.success else '❌ Failed'}")
            logger.info(f"  Alert Level: Warning (88.5% usage)")
            logger.info(f"  Recommendations Included: {len(comprehensive_report.storage_recommendations)}")
        
        logger.info("✅ Email notification system demonstration completed")
    
    async def demonstrate_reporting_coordinator(self, 
                                              update_reports: Dict[str, UpdateReport]):
        """Demonstrate reporting coordinator integration."""
        logger.info("=== Demonstrating Reporting Coordinator Integration ===")
        
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
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            username="demo@example.com",
            password="demo_password",
            from_email="noreply@aischolar.com",
            recipients=["admin@aischolar.com"]
        )
        
        # Initialize reporting coordinator
        reporting_coordinator = ReportingCoordinator(
            reporting_config=reporting_config,
            notification_config=notification_config,
            reports_directory=str(self.reports_dir)
        )
        
        logger.info("🎯 Reporting Coordinator Configuration:")
        logger.info(f"  Comprehensive Reports: {reporting_config.enable_comprehensive_reports}")
        logger.info(f"  Notifications: {reporting_config.enable_notifications}")
        logger.info(f"  Storage Monitoring: {reporting_config.enable_storage_monitoring}")
        logger.info(f"  Storage Alert Threshold: {reporting_config.storage_alert_threshold}%")
        logger.info(f"  Report Retention: {reporting_config.report_retention_days} days")
        
        # Process update completion with mocked SMTP
        from unittest.mock import patch, Mock
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            orchestration_id = f"coordinator_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"🔄 Processing update completion for orchestration: {orchestration_id}")
            
            reporting_result = await reporting_coordinator.process_update_completion(
                update_reports, orchestration_id
            )
            
            logger.info("📊 Reporting Coordinator Results:")
            logger.info(f"  Overall Success: {'✅ Yes' if reporting_result.success else '❌ No'}")
            logger.info(f"  Comprehensive Report Generated: {'✅ Yes' if reporting_result.comprehensive_report else '❌ No'}")
            logger.info(f"  Notifications Sent: {len(reporting_result.notification_results)}")
            logger.info(f"  Storage Alerts Sent: {reporting_result.storage_alerts_sent}")
            logger.info(f"  Errors: {len(reporting_result.errors)}")
            
            if reporting_result.comprehensive_report:
                logger.info(f"  Report ID: {reporting_result.comprehensive_report.report_id}")
                logger.info(f"  System Health: {reporting_result.comprehensive_report.system_summary.overall_health_status}")
            
            # Show notification results
            if reporting_result.notification_results:
                logger.info("📧 Notification Results:")
                for i, notification_result in enumerate(reporting_result.notification_results, 1):
                    logger.info(f"  Notification {i}: {'✅ Success' if notification_result.success else '❌ Failed'}")
                    logger.info(f"    Recipients: {len(notification_result.recipients_sent)} sent, {len(notification_result.recipients_failed)} failed")
            
            # Show any errors
            if reporting_result.errors:
                logger.info("🚨 Reporting Errors:")
                for error in reporting_result.errors:
                    logger.info(f"  - {error}")
        
        # Get reporting statistics
        stats = reporting_coordinator.get_reporting_statistics()
        logger.info("📈 Reporting Statistics:")
        logger.info(f"  Total Reports Generated: {stats['reporting']['total_reports_generated']}")
        logger.info(f"  Success Rate: {stats['reporting']['success_rate']:.1f}%")
        logger.info(f"  Notifications Sent: {stats['notifications']['total_notifications']}")
        logger.info(f"  Notification Success Rate: {stats['notifications']['success_rate']:.1f}%")
        
        logger.info("✅ Reporting coordinator integration demonstration completed")
    
    async def run_complete_demonstration(self):
        """Run complete demonstration of Task 5.3 functionality."""
        logger.info("🚀 Starting Task 5.3 Complete Demonstration")
        logger.info("=" * 60)
        
        try:
            # Step 1: Create sample data
            logger.info("Step 1: Creating sample update reports")
            update_reports = self.create_sample_update_reports()
            
            # Step 2: Demonstrate comprehensive report generation
            logger.info("\nStep 2: Comprehensive report generation")
            comprehensive_report = await self.demonstrate_comprehensive_report_generation(update_reports)
            
            # Step 3: Demonstrate notification system
            logger.info("\nStep 3: Email notification system")
            await self.demonstrate_notification_system(comprehensive_report)
            
            # Step 4: Demonstrate reporting coordinator
            logger.info("\nStep 4: Reporting coordinator integration")
            await self.demonstrate_reporting_coordinator(update_reports)
            
            logger.info("\n" + "=" * 60)
            logger.info("🎉 Task 5.3 Demonstration Completed Successfully!")
            logger.info("=" * 60)
            
            # Summary
            logger.info("📋 Demonstration Summary:")
            logger.info("  ✅ Comprehensive report generation with statistics and analysis")
            logger.info("  ✅ Email notification system with HTML templates")
            logger.info("  ✅ Storage monitoring and alert notifications")
            logger.info("  ✅ Error analysis and performance insights")
            logger.info("  ✅ Reporting coordinator integration")
            logger.info("  ✅ Complete update reporting and notification workflow")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Demonstration failed: {e}")
            return False
        
        finally:
            self.cleanup()


async def main():
    """Main entry point for the demonstration."""
    try:
        demo = Task53Demo()
        success = await demo.run_complete_demonstration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Demonstration interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Demonstration execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())