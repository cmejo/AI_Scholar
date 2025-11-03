#!/usr/bin/env python3
"""
Comprehensive test for the reporting and notification system.

Tests the implementation of task 5.3: Update reporting and notifications.
"""

import asyncio
import logging
import sys
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

# Add backend to path
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

# Import from the current directory structure
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from reporting.update_reporter import UpdateReporter, ComprehensiveUpdateReport
from reporting.notification_service import NotificationService
from reporting.reporting_coordinator import ReportingCoordinator, ReportingConfig
from shared.multi_instance_data_models import (
    UpdateReport, StorageStats, PerformanceMetrics, NotificationConfig,
    ProcessingError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_update_reports() -> Dict[str, UpdateReport]:
    """Create test update reports for AI Scholar and Quant Scholar."""
    
    # Create test storage stats
    ai_storage_stats = StorageStats(
        total_space_gb=100.0,
        used_space_gb=45.2,
        available_space_gb=54.8,
        usage_percentage=45.2,
        instance_breakdown={"ai_scholar": 45.2},
        growth_rate_gb_per_month=5.0
    )
    
    quant_storage_stats = StorageStats(
        total_space_gb=100.0,
        used_space_gb=32.1,
        available_space_gb=67.9,
        usage_percentage=32.1,
        instance_breakdown={"quant_scholar": 32.1},
        growth_rate_gb_per_month=3.5
    )
    
    # Create test performance metrics
    ai_performance = PerformanceMetrics(
        download_rate_mbps=15.5,
        processing_rate_papers_per_hour=120.0,
        embedding_generation_rate=85.0,
        memory_usage_peak_mb=2048,
        cpu_usage_average_percent=65.0,
        error_rate_percentage=2.1
    )
    
    quant_performance = PerformanceMetrics(
        download_rate_mbps=12.3,
        processing_rate_papers_per_hour=95.0,
        embedding_generation_rate=70.0,
        memory_usage_peak_mb=1536,
        cpu_usage_average_percent=55.0,
        error_rate_percentage=1.8
    )
    
    # Create test errors
    ai_errors = [
        ProcessingError(
            file_path="/path/to/failed_paper1.pdf",
            error_message="PDF parsing failed: corrupted file",
            error_type="pdf_processing",
            timestamp=datetime.now()
        ),
        ProcessingError(
            file_path="/path/to/failed_paper2.pdf",
            error_message="Network timeout during download",
            error_type="network_error",
            timestamp=datetime.now()
        )
    ]
    
    quant_errors = [
        ProcessingError(
            file_path="/path/to/quant_failed.pdf",
            error_message="Memory allocation failed",
            error_type="memory_error",
            timestamp=datetime.now()
        )
    ]
    
    # Create AI Scholar update report
    ai_report = UpdateReport(
        instance_name="ai_scholar",
        update_date=datetime.now(),
        papers_discovered=150,
        papers_downloaded=148,
        papers_processed=146,
        papers_failed=2,
        storage_used_mb=int(ai_storage_stats.used_space_gb * 1024),
        processing_time_seconds=3600.0,  # 1 hour
        errors=ai_errors,
        storage_stats=ai_storage_stats,
        performance_metrics=ai_performance,
        categories_processed=["cond-mat", "gr-qc", "hep-ph"],
        duplicate_papers_skipped=5
    )
    
    # Create Quant Scholar update report
    quant_report = UpdateReport(
        instance_name="quant_scholar",
        update_date=datetime.now(),
        papers_discovered=85,
        papers_downloaded=84,
        papers_processed=83,
        papers_failed=1,
        storage_used_mb=int(quant_storage_stats.used_space_gb * 1024),
        processing_time_seconds=2400.0,  # 40 minutes
        errors=quant_errors,
        storage_stats=quant_storage_stats,
        performance_metrics=quant_performance,
        categories_processed=["q-fin.CP", "stat.ML", "econ.EM"],
        duplicate_papers_skipped=3
    )
    
    return {
        "ai_scholar": ai_report,
        "quant_scholar": quant_report
    }


async def test_update_reporter():
    """Test the UpdateReporter functionality."""
    logger.info("Testing UpdateReporter...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize reporter
        reporter = UpdateReporter(temp_dir)
        
        # Create test reports
        instance_reports = create_test_update_reports()
        orchestration_id = f"test_orchestration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Generate comprehensive report
        comprehensive_report = await reporter.generate_comprehensive_report(
            instance_reports, orchestration_id
        )
        
        # Verify comprehensive report
        assert comprehensive_report is not None
        assert comprehensive_report.report_id == f"comprehensive_report_{orchestration_id}"
        assert comprehensive_report.system_summary.total_instances == 2
        assert comprehensive_report.system_summary.total_papers_processed == 229  # 146 + 83
        assert comprehensive_report.system_summary.total_errors == 3  # 2 + 1
        
        # Verify instance reports are included
        assert "ai_scholar" in comprehensive_report.instance_reports
        assert "quant_scholar" in comprehensive_report.instance_reports
        
        # Verify comparison metrics
        assert "ai_scholar" in comprehensive_report.comparison_metrics
        assert "quant_scholar" in comprehensive_report.comparison_metrics
        
        # Verify storage recommendations
        assert len(comprehensive_report.storage_recommendations) > 0
        
        # Verify error analysis
        assert comprehensive_report.error_analysis["total_errors"] == 3
        assert "ai_scholar" in comprehensive_report.error_analysis["error_by_instance"]
        assert "quant_scholar" in comprehensive_report.error_analysis["error_by_instance"]
        
        # Verify performance insights
        assert "processing_rates" in comprehensive_report.performance_insights
        assert "efficiency_metrics" in comprehensive_report.performance_insights
        
        # Verify predictions
        assert "estimated_papers" in comprehensive_report.next_update_predictions
        assert "storage_growth_projection" in comprehensive_report.next_update_predictions
        
        logger.info("✅ UpdateReporter tests passed")
        return comprehensive_report


async def test_notification_service():
    """Test the NotificationService functionality."""
    logger.info("Testing NotificationService...")
    
    # Create test notification config (disabled for testing)
    notification_config = NotificationConfig(
        enabled=False,  # Disabled to avoid sending actual emails during testing
        recipients=["test@example.com"],
        smtp_server="localhost",
        smtp_port=587,
        from_email="noreply@test.com"
    )
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize notification service
        notification_service = NotificationService(
            notification_config, 
            templates_directory=temp_dir
        )
        
        # Create test comprehensive report
        instance_reports = create_test_update_reports()
        comprehensive_report = ComprehensiveUpdateReport(
            report_id="test_report_123",
            generated_at=datetime.now(),
            system_summary=type('SystemSummary', (), {
                'total_instances': 2,
                'successful_instances': 2,
                'failed_instances': 0,
                'success_rate': 100.0,
                'total_papers_processed': 229,
                'total_errors': 3,
                'error_rate': 1.3,
                'total_processing_time_hours': 1.67,
                'total_storage_used_gb': 77.3,
                'overall_health_status': 'good'
            })(),
            instance_reports=instance_reports
        )
        
        # Test update completion notification (won't send due to disabled config)
        result = await notification_service.send_update_completion_notification(comprehensive_report)
        assert not result.success  # Should fail because notifications are disabled
        assert "disabled" in result.message.lower()
        
        # Test error summary notification
        error_analysis = {
            'total_errors': 3,
            'error_by_instance': {'ai_scholar': 2, 'quant_scholar': 1},
            'critical_errors': []
        }
        
        result = await notification_service.send_error_summary_notification(
            error_analysis, instance_reports
        )
        assert not result.success  # Should fail because notifications are disabled
        
        # Test storage alert notification
        storage_stats = {
            'total_storage_gb': 77.3,
            'usage_percentage': 77.3
        }
        
        result = await notification_service.send_storage_alert_notification(
            storage_stats, []
        )
        assert not result.success  # Should fail because notifications are disabled
        
        # Test notification statistics
        stats = notification_service.get_notification_statistics()
        assert stats['total_notifications'] >= 0
        assert 'configuration' in stats
        
        logger.info("✅ NotificationService tests passed")


async def test_reporting_coordinator():
    """Test the ReportingCoordinator functionality."""
    logger.info("Testing ReportingCoordinator...")
    
    # Create test configurations
    reporting_config = ReportingConfig(
        enable_comprehensive_reports=True,
        enable_notifications=False,  # Disabled for testing
        enable_storage_monitoring=True
    )
    
    notification_config = NotificationConfig(
        enabled=False,
        recipients=["test@example.com"]
    )
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize reporting coordinator
        coordinator = ReportingCoordinator(
            reporting_config=reporting_config,
            notification_config=notification_config,
            reports_directory=temp_dir
        )
        
        # Create test instance reports
        instance_reports = create_test_update_reports()
        orchestration_id = f"test_coord_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Process update completion
        result = await coordinator.process_update_completion(
            instance_reports, orchestration_id
        )
        
        # Verify result
        assert result.success
        assert result.comprehensive_report is not None
        assert result.comprehensive_report.report_id == f"comprehensive_report_{orchestration_id}"
        
        # Verify storage monitoring was performed
        assert result.storage_alerts_sent >= 0  # May be 0 if no alerts needed
        
        # Test reporting statistics
        stats = coordinator.get_reporting_statistics()
        assert 'reporting' in stats
        assert 'notifications' in stats
        assert stats['reporting']['total_reports_generated'] >= 1
        
        # Test latest reports retrieval
        latest_reports = coordinator.get_latest_comprehensive_reports(limit=5)
        assert len(latest_reports) >= 1
        
        # Test storage recommendations generation
        recommendations = await coordinator.generate_storage_recommendations(instance_reports)
        assert isinstance(recommendations, list)
        
        logger.info("✅ ReportingCoordinator tests passed")


async def test_comprehensive_workflow():
    """Test the complete reporting workflow."""
    logger.info("Testing comprehensive reporting workflow...")
    
    # This test simulates the complete workflow from update completion
    # through comprehensive report generation and notification sending
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create configurations
        reporting_config = ReportingConfig(
            enable_comprehensive_reports=True,
            enable_notifications=False,  # Disabled for testing
            enable_storage_monitoring=True,
            storage_alert_threshold=75.0,
            storage_critical_threshold=90.0
        )
        
        notification_config = NotificationConfig(enabled=False)
        
        # Initialize coordinator
        coordinator = ReportingCoordinator(
            reporting_config=reporting_config,
            notification_config=notification_config,
            reports_directory=temp_dir
        )
        
        # Create test data with high storage usage to trigger alerts
        instance_reports = create_test_update_reports()
        
        # Modify storage stats to trigger storage alerts
        for report in instance_reports.values():
            report.storage_stats.usage_percentage = 85.0  # Above threshold
            report.storage_stats.used_space_gb = 85.0
        
        orchestration_id = f"workflow_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Execute complete workflow
        result = await coordinator.process_update_completion(
            instance_reports, orchestration_id
        )
        
        # Verify workflow completion
        assert result.success
        assert result.comprehensive_report is not None
        
        # Verify comprehensive report content
        report = result.comprehensive_report
        assert report.system_summary.total_instances == 2
        assert report.system_summary.total_papers_processed > 0
        assert len(report.instance_reports) == 2
        assert len(report.storage_recommendations) > 0
        
        # Verify error analysis
        assert report.error_analysis['total_errors'] > 0
        assert 'error_by_instance' in report.error_analysis
        
        # Verify performance insights
        assert 'processing_rates' in report.performance_insights
        assert 'efficiency_metrics' in report.performance_insights
        
        # Verify storage recommendations due to high usage
        storage_recs = [r for r in report.storage_recommendations 
                      if r.recommendation_type in ['cleanup', 'alert']]
        assert len(storage_recs) > 0
        
        # Verify report was saved
        report_files = list(Path(temp_dir).glob("comprehensive_report_*.json"))
        assert len(report_files) >= 1
        
        # Verify report file content
        with open(report_files[0], 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report['report_id'] == report.report_id
        assert saved_report['system_summary']['total_instances'] == 2
        
        logger.info("✅ Comprehensive workflow test passed")


async def main():
    """Run all reporting system tests."""
    logger.info("Starting comprehensive reporting system tests...")
    
    try:
        # Test individual components
        comprehensive_report = await test_update_reporter()
        await test_notification_service()
        await test_reporting_coordinator()
        
        # Test complete workflow
        await test_comprehensive_workflow()
        
        logger.info("🎉 All reporting system tests passed successfully!")
        
        # Display sample report summary
        logger.info("\n" + "="*60)
        logger.info("SAMPLE COMPREHENSIVE REPORT SUMMARY")
        logger.info("="*60)
        logger.info(f"Report ID: {comprehensive_report.report_id}")
        logger.info(f"Generated: {comprehensive_report.generated_at}")
        logger.info(f"Total Instances: {comprehensive_report.system_summary.total_instances}")
        logger.info(f"Success Rate: {comprehensive_report.system_summary.success_rate:.1f}%")
        logger.info(f"Papers Processed: {comprehensive_report.system_summary.total_papers_processed}")
        logger.info(f"Total Errors: {comprehensive_report.system_summary.total_errors}")
        logger.info(f"Storage Recommendations: {len(comprehensive_report.storage_recommendations)}")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Reporting system tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)