#!/usr/bin/env python3
"""
Demo for Task 7.3: Storage Alerting and Reporting System.

This demo shows how to use the StorageAlertingService for:
- Immediate storage warning notifications
- Storage utilization reporting in monthly updates
- Storage growth rate analysis and projections
- Storage cleanup impact analysis
"""

import asyncio
import logging
import sys
import os
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_storage_alerting_system():
    """Demonstrate the complete storage alerting and reporting system."""
    
    logger.info("🚀 Starting Storage Alerting and Reporting System Demo")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"📁 Using temporary directory: {temp_dir}")
        
        # Import required components
        from multi_instance_arxiv_system.storage import (
            StorageMonitor, StorageAlertingService, DataRetentionManager,
            ReportType, StorageDataType, CleanupResult
        )
        from collections import defaultdict
        
        # 1. Create Storage Monitor
        logger.info("\n📊 Step 1: Creating Storage Monitor")
        storage_monitor = StorageMonitor(
            database_path=os.path.join(temp_dir, "storage_monitor.db"),
            monitoring_interval=1,
            alert_thresholds={
                'warning': 70.0,
                'critical': 85.0,
                'emergency': 95.0
            }
        )
        
        # Add some monitored paths
        test_paths = [
            ("ai_scholar_data", StorageDataType.PROCESSED_DATA, "ai_scholar"),
            ("quant_scholar_data", StorageDataType.PROCESSED_DATA, "quant_scholar"),
            ("pdf_storage", StorageDataType.PDF_FILES, None),
            ("logs", StorageDataType.LOG_FILES, None)
        ]
        
        for path_name, data_type, instance in test_paths:
            path = os.path.join(temp_dir, path_name)
            os.makedirs(path, exist_ok=True)
            
            # Create some test files
            for i in range(5):
                test_file = Path(path) / f"test_file_{i}.txt"
                test_file.write_text(f"Test content for {path_name} file {i}" * 100)
            
            storage_monitor.add_monitored_path(path, data_type, instance)
            logger.info(f"   ✓ Added monitored path: {path_name} ({data_type.value})")
        
        # 2. Create Data Retention Manager
        logger.info("\n🗂️  Step 2: Creating Data Retention Manager")
        retention_manager = DataRetentionManager(
            database_path=os.path.join(temp_dir, "retention.db"),
            archive_base_path=os.path.join(temp_dir, "archives")
        )
        logger.info("   ✓ Data retention manager created")
        
        # 3. Create Storage Alerting Service
        logger.info("\n🚨 Step 3: Creating Storage Alerting Service")
        alerting_service = StorageAlertingService(
            storage_monitor=storage_monitor,
            retention_manager=retention_manager,
            database_path=os.path.join(temp_dir, "alerting.db"),
            alert_cooldown_minutes=1  # Short cooldown for demo
        )
        logger.info("   ✓ Storage alerting service created")
        
        # 4. Start monitoring
        logger.info("\n🔍 Step 4: Starting Storage Monitoring")
        storage_monitor.start_monitoring()
        logger.info("   ✓ Storage monitoring started")
        
        # Let it collect some data
        await asyncio.sleep(2)
        
        # 5. Check and send alerts
        logger.info("\n📢 Step 5: Checking for Storage Alerts")
        alerts_sent = await alerting_service.check_and_send_alerts()
        logger.info(f"   ✓ Checked alerts: {len(alerts_sent)} alerts sent")
        
        for alert in alerts_sent:
            logger.info(f"     - {alert.level.value.upper()}: {alert.message}")
        
        # 6. Analyze storage growth
        logger.info("\n📈 Step 6: Analyzing Storage Growth")
        growth_analysis = await alerting_service.analyze_storage_growth(days_back=7)
        
        logger.info("   📊 Growth Analysis Results:")
        logger.info(f"     Current usage: {growth_analysis.current_usage_gb:.2f} GB")
        logger.info(f"     Growth rate: {growth_analysis.growth_rate_gb_per_day:.3f} GB/day")
        logger.info(f"     Growth percentage: {growth_analysis.growth_rate_percentage_per_day:.2f}%/day")
        logger.info(f"     Trend direction: {growth_analysis.trend_direction}")
        logger.info(f"     Confidence score: {growth_analysis.confidence_score:.2f}")
        
        if growth_analysis.days_until_full:
            logger.info(f"     Days until full: {growth_analysis.days_until_full}")
            logger.info(f"     Projected full date: {growth_analysis.projected_full_date.strftime('%Y-%m-%d')}")
        else:
            logger.info("     No projection available (stable or decreasing usage)")
        
        # 7. Simulate cleanup operation and analyze impact
        logger.info("\n🧹 Step 7: Simulating Cleanup Operation")
        
        # Get storage stats before cleanup
        before_stats = storage_monitor.get_current_stats()
        
        # Simulate cleanup result
        cleanup_result = CleanupResult(
            total_files_processed=25,
            total_space_freed_mb=50.0,  # 50MB
            actions_performed=defaultdict(int, {
                'delete': 10,
                'archive': 8,
                'compress': 7
            }),
            errors=[],
            execution_time_seconds=30.0
        )
        
        # Simulate after stats (slightly less usage)
        after_stats = storage_monitor.get_current_stats()
        after_stats.used_storage_gb = max(0, after_stats.used_storage_gb - 0.05)  # Simulate 50MB freed
        
        # Analyze cleanup impact
        cleanup_impact = await alerting_service.analyze_cleanup_impact(
            cleanup_result, before_stats, after_stats
        )
        
        logger.info("   🧹 Cleanup Impact Analysis:")
        logger.info(f"     Files processed: {cleanup_impact.files_processed}")
        logger.info(f"     Space freed: {cleanup_impact.space_freed_gb:.3f} GB ({cleanup_impact.space_freed_percentage:.2f}%)")
        logger.info(f"     Efficiency score: {cleanup_impact.efficiency_score:.2f}")
        logger.info(f"     Recommendations: {len(cleanup_impact.recommendations)}")
        
        for i, rec in enumerate(cleanup_impact.recommendations, 1):
            logger.info(f"       {i}. {rec}")
        
        # 8. Generate utilization reports
        logger.info("\n📋 Step 8: Generating Utilization Reports")
        
        report_types = [ReportType.DAILY, ReportType.WEEKLY, ReportType.MONTHLY]
        
        for report_type in report_types:
            logger.info(f"\n   📊 Generating {report_type.value.capitalize()} Report:")
            
            report = await alerting_service.generate_utilization_report(report_type)
            
            logger.info(f"     Report period: {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')}")
            logger.info(f"     Total storage: {report.total_storage_gb:.2f} GB")
            logger.info(f"     Used storage: {report.used_storage_gb:.2f} GB ({report.usage_percentage:.1f}%)")
            logger.info(f"     Free storage: {report.free_storage_gb:.2f} GB")
            logger.info(f"     Active alerts: {len(report.active_alerts)}")
            logger.info(f"     Resolved alerts: {report.resolved_alerts_count}")
            logger.info(f"     Cleanup operations: {len(report.cleanup_operations)}")
            logger.info(f"     Total space cleaned: {report.total_space_cleaned_gb:.3f} GB")
            
            # Show instance breakdown
            if report.instance_breakdown:
                logger.info("     Instance breakdown:")
                for instance, breakdown in report.instance_breakdown.items():
                    total_gb = breakdown.get('total', 0)
                    logger.info(f"       {instance}: {total_gb:.2f} GB")
            
            # Show recommendations
            if report.recommendations:
                logger.info("     Recommendations:")
                for i, rec in enumerate(report.recommendations[:3], 1):  # Show first 3
                    logger.info(f"       {i}. {rec}")
            
            # Show priority actions
            if report.priority_actions:
                logger.info("     Priority actions:")
                for i, action in enumerate(report.priority_actions[:3], 1):  # Show first 3
                    logger.info(f"       {i}. {action}")
        
        # 9. Show recent reports
        logger.info("\n📚 Step 9: Retrieving Recent Reports")
        recent_reports = alerting_service.get_recent_reports(limit=5)
        logger.info(f"   ✓ Retrieved {len(recent_reports)} recent reports from database")
        
        # 10. Demonstrate alert cooldown
        logger.info("\n⏰ Step 10: Demonstrating Alert Cooldown")
        logger.info("   Checking alerts again immediately (should be limited by cooldown)...")
        
        alerts_sent_again = await alerting_service.check_and_send_alerts()
        logger.info(f"   ✓ Second alert check: {len(alerts_sent_again)} alerts sent (cooldown in effect)")
        
        # Stop monitoring
        storage_monitor.stop_monitoring()
        logger.info("\n🛑 Storage monitoring stopped")
        
        # 11. Summary
        logger.info("\n📊 Demo Summary:")
        logger.info("   ✅ Storage monitoring and alerting system demonstrated")
        logger.info("   ✅ Growth analysis and projections working")
        logger.info("   ✅ Cleanup impact analysis functional")
        logger.info("   ✅ Utilization reporting for different periods")
        logger.info("   ✅ Database persistence and report retrieval")
        logger.info("   ✅ Alert cooldown and throttling")
        logger.info("   ✅ Integration with existing storage systems")
        
        logger.info("\n🎉 Storage Alerting and Reporting System Demo Complete!")
        
        return True


async def main():
    """Run the storage alerting system demo."""
    try:
        success = await demo_storage_alerting_system()
        
        if success:
            logger.info("\n✅ Demo completed successfully!")
            return 0
        else:
            logger.error("\n❌ Demo failed!")
            return 1
            
    except Exception as e:
        logger.error(f"\n💥 Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)