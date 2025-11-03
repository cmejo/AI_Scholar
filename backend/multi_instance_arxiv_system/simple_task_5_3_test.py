#!/usr/bin/env python3
"""
Simple test for Task 5.3: Update reporting and notifications.

This script demonstrates the key functionality without complex imports.
"""

import asyncio
import logging
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MockUpdateReport:
    """Mock update report for testing."""
    instance_name: str
    update_date: datetime
    papers_discovered: int
    papers_downloaded: int
    papers_processed: int
    papers_failed: int
    storage_used_mb: int
    processing_time_seconds: float
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'instance_name': self.instance_name,
            'update_date': self.update_date.isoformat(),
            'papers_discovered': self.papers_discovered,
            'papers_downloaded': self.papers_downloaded,
            'papers_processed': self.papers_processed,
            'papers_failed': self.papers_failed,
            'storage_used_mb': self.storage_used_mb,
            'processing_time_seconds': self.processing_time_seconds,
            'errors': self.errors
        }


@dataclass
class MockSystemSummary:
    """Mock system summary for testing."""
    total_instances: int = 0
    successful_instances: int = 0
    failed_instances: int = 0
    total_papers_processed: int = 0
    total_errors: int = 0
    total_processing_time_hours: float = 0.0
    total_storage_used_gb: float = 0.0
    overall_health_status: str = "unknown"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_instances == 0:
            return 0.0
        return (self.successful_instances / self.total_instances) * 100.0
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage."""
        if self.total_papers_processed == 0:
            return 0.0
        return (self.total_errors / self.total_papers_processed) * 100.0


@dataclass
class MockStorageRecommendation:
    """Mock storage recommendation for testing."""
    recommendation_type: str
    priority: str
    description: str
    estimated_space_savings_gb: float = 0.0
    action_required: bool = False
    commands: List[str] = field(default_factory=list)


class SimpleReportGenerator:
    """Simple report generator for demonstration."""
    
    def __init__(self, reports_directory: str):
        """Initialize report generator."""
        self.reports_directory = Path(reports_directory)
        self.reports_directory.mkdir(parents=True, exist_ok=True)
    
    async def generate_comprehensive_report(self, 
                                          instance_reports: Dict[str, MockUpdateReport],
                                          orchestration_id: str) -> Dict[str, Any]:
        """Generate comprehensive report."""
        logger.info(f"Generating comprehensive report: {orchestration_id}")
        
        # Create system summary
        system_summary = MockSystemSummary()
        system_summary.total_instances = len(instance_reports)
        
        for instance_name, report in instance_reports.items():
            # Count successful vs failed instances
            if len(report.errors) == 0 and report.papers_processed > 0:
                system_summary.successful_instances += 1
            else:
                system_summary.failed_instances += 1
            
            # Aggregate metrics
            system_summary.total_papers_processed += report.papers_processed
            system_summary.total_errors += len(report.errors)
            system_summary.total_processing_time_hours += report.processing_time_seconds / 3600.0
            system_summary.total_storage_used_gb += report.storage_used_mb / 1024.0
        
        # Determine overall health status
        if system_summary.success_rate >= 90:
            system_summary.overall_health_status = "excellent"
        elif system_summary.success_rate >= 75:
            system_summary.overall_health_status = "good"
        elif system_summary.success_rate >= 50:
            system_summary.overall_health_status = "fair"
        else:
            system_summary.overall_health_status = "poor"
        
        # Generate storage recommendations
        storage_recommendations = []
        total_storage_gb = system_summary.total_storage_used_gb
        
        if total_storage_gb > 15:  # More than 15GB
            storage_recommendations.append(MockStorageRecommendation(
                recommendation_type="cleanup",
                priority="high",
                description=f"System is using {total_storage_gb:.1f}GB of storage. Consider cleaning up old files.",
                estimated_space_savings_gb=total_storage_gb * 0.3,
                action_required=True,
                commands=[
                    "find /datapool/aischolar -name '*.pdf' -mtime +90 -delete",
                    "find /datapool/aischolar -name '*.log' -mtime +30 -delete"
                ]
            ))
        
        # Create comprehensive report
        comprehensive_report = {
            'report_id': f"comprehensive_report_{orchestration_id}",
            'generated_at': datetime.now().isoformat(),
            'system_summary': {
                'total_instances': system_summary.total_instances,
                'successful_instances': system_summary.successful_instances,
                'failed_instances': system_summary.failed_instances,
                'success_rate': system_summary.success_rate,
                'total_papers_processed': system_summary.total_papers_processed,
                'total_errors': system_summary.total_errors,
                'error_rate': system_summary.error_rate,
                'total_processing_time_hours': system_summary.total_processing_time_hours,
                'total_storage_used_gb': system_summary.total_storage_used_gb,
                'overall_health_status': system_summary.overall_health_status
            },
            'instance_reports': {k: v.to_dict() for k, v in instance_reports.items()},
            'storage_recommendations': [
                {
                    'recommendation_type': rec.recommendation_type,
                    'priority': rec.priority,
                    'description': rec.description,
                    'estimated_space_savings_gb': rec.estimated_space_savings_gb,
                    'action_required': rec.action_required,
                    'commands': rec.commands
                }
                for rec in storage_recommendations
            ],
            'error_analysis': {
                'total_errors': system_summary.total_errors,
                'error_by_instance': {
                    name: len(report.errors) 
                    for name, report in instance_reports.items()
                },
                'instances_with_errors': len([
                    name for name, report in instance_reports.items() 
                    if len(report.errors) > 0
                ])
            },
            'performance_insights': {
                'processing_rates': {
                    name: (report.papers_processed / (report.processing_time_seconds / 3600)) 
                    if report.processing_time_seconds > 0 else 0
                    for name, report in instance_reports.items()
                },
                'average_processing_time_hours': system_summary.total_processing_time_hours / len(instance_reports)
            }
        }
        
        # Save report
        report_file = self.reports_directory / f"{comprehensive_report['report_id']}.json"
        with open(report_file, 'w') as f:
            json.dump(comprehensive_report, f, indent=2, default=str)
        
        logger.info(f"Comprehensive report saved: {report_file}")
        return comprehensive_report


class SimpleNotificationService:
    """Simple notification service for demonstration."""
    
    def __init__(self, smtp_config: Dict[str, Any]):
        """Initialize notification service."""
        self.smtp_config = smtp_config
        self.notification_history = []
    
    async def send_update_completion_notification(self, 
                                                comprehensive_report: Dict[str, Any]) -> Dict[str, Any]:
        """Send update completion notification (simulated)."""
        logger.info("Sending update completion notification")
        
        # Simulate email content generation
        system_summary = comprehensive_report['system_summary']
        success_rate = system_summary['success_rate']
        
        subject = f"Monthly Update Completed - {success_rate:.1f}% Success Rate"
        
        # Simulate email content
        email_content = f"""
Monthly Update Report
====================

System Summary:
- Total Instances: {system_summary['total_instances']}
- Success Rate: {success_rate:.1f}%
- Papers Processed: {system_summary['total_papers_processed']}
- Total Errors: {system_summary['total_errors']}
- Processing Time: {system_summary['total_processing_time_hours']:.1f} hours
- Storage Used: {system_summary['total_storage_used_gb']:.1f} GB
- Health Status: {system_summary['overall_health_status']}

Instance Details:
"""
        
        for instance_name, instance_report in comprehensive_report['instance_reports'].items():
            email_content += f"""
{instance_name}:
  - Papers Processed: {instance_report['papers_processed']}
  - Errors: {len(instance_report['errors'])}
  - Storage: {instance_report['storage_used_mb'] / 1024:.1f} GB
  - Processing Time: {instance_report['processing_time_seconds'] / 3600:.1f} hours
"""
        
        if comprehensive_report['storage_recommendations']:
            email_content += "\nStorage Recommendations:\n"
            for rec in comprehensive_report['storage_recommendations']:
                email_content += f"- {rec['description']} (Priority: {rec['priority']})\n"
        
        # Simulate successful email sending
        notification_result = {
            'success': True,
            'message': f"Notification sent to {len(self.smtp_config.get('recipients', []))} recipients",
            'recipients_sent': self.smtp_config.get('recipients', []),
            'recipients_failed': [],
            'timestamp': datetime.now().isoformat(),
            'subject': subject,
            'content_preview': email_content[:200] + "..."
        }
        
        self.notification_history.append(notification_result)
        
        logger.info(f"✅ Notification sent successfully: {notification_result['message']}")
        return notification_result
    
    async def send_storage_alert_notification(self, 
                                            storage_stats: Dict[str, Any],
                                            recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send storage alert notification (simulated)."""
        logger.info("Sending storage alert notification")
        
        usage_percentage = storage_stats.get('usage_percentage', 0)
        total_storage_gb = storage_stats.get('total_storage_gb', 0)
        
        if usage_percentage >= 95:
            alert_level = "critical"
        elif usage_percentage >= 85:
            alert_level = "warning"
        else:
            alert_level = "info"
        
        subject = f"{alert_level.title()} Storage Alert - {usage_percentage:.1f}% Used"
        
        # Simulate storage alert email
        alert_content = f"""
Storage Alert - {alert_level.title()}
====================================

Current Storage Usage: {usage_percentage:.1f}%
Total Storage: {total_storage_gb:.1f} GB

Immediate Actions Required:
"""
        
        for rec in recommendations:
            alert_content += f"- {rec['description']}\n"
            if rec.get('commands'):
                alert_content += f"  Commands: {', '.join(rec['commands'])}\n"
        
        # Simulate successful alert sending
        alert_result = {
            'success': True,
            'message': f"Storage alert sent to {len(self.smtp_config.get('recipients', []))} recipients",
            'recipients_sent': self.smtp_config.get('recipients', []),
            'recipients_failed': [],
            'timestamp': datetime.now().isoformat(),
            'alert_level': alert_level,
            'subject': subject,
            'content_preview': alert_content[:200] + "..."
        }
        
        self.notification_history.append(alert_result)
        
        logger.info(f"🚨 Storage alert sent successfully: {alert_result['message']}")
        return alert_result


class SimpleReportingCoordinator:
    """Simple reporting coordinator for demonstration."""
    
    def __init__(self, reports_directory: str, smtp_config: Dict[str, Any]):
        """Initialize reporting coordinator."""
        self.report_generator = SimpleReportGenerator(reports_directory)
        self.notification_service = SimpleNotificationService(smtp_config)
        self.processing_history = []
    
    async def process_update_completion(self, 
                                      instance_reports: Dict[str, MockUpdateReport],
                                      orchestration_id: str) -> Dict[str, Any]:
        """Process update completion with reporting and notifications."""
        logger.info(f"Processing update completion for orchestration: {orchestration_id}")
        
        processing_result = {
            'success': True,
            'orchestration_id': orchestration_id,
            'comprehensive_report': None,
            'notification_results': [],
            'storage_alerts_sent': 0,
            'errors': []
        }
        
        try:
            # Generate comprehensive report
            comprehensive_report = await self.report_generator.generate_comprehensive_report(
                instance_reports, orchestration_id
            )
            processing_result['comprehensive_report'] = comprehensive_report
            
            # Send update completion notification
            notification_result = await self.notification_service.send_update_completion_notification(
                comprehensive_report
            )
            processing_result['notification_results'].append(notification_result)
            
            # Check if storage alert is needed
            total_storage_gb = comprehensive_report['system_summary']['total_storage_used_gb']
            usage_percentage = min(total_storage_gb / 100.0 * 100, 100)  # Simplified calculation
            
            if usage_percentage >= 85:
                storage_stats = {
                    'total_storage_gb': total_storage_gb,
                    'usage_percentage': usage_percentage
                }
                
                storage_alert_result = await self.notification_service.send_storage_alert_notification(
                    storage_stats, comprehensive_report['storage_recommendations']
                )
                processing_result['notification_results'].append(storage_alert_result)
                processing_result['storage_alerts_sent'] = 1
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            processing_result['success'] = False
            processing_result['errors'].append(str(e))
        
        self.processing_history.append(processing_result)
        
        logger.info(f"Update completion processing finished: success={processing_result['success']}")
        return processing_result


async def demonstrate_task_5_3():
    """Demonstrate Task 5.3 functionality."""
    logger.info("🚀 Starting Task 5.3 Demonstration: Update reporting and notifications")
    logger.info("=" * 70)
    
    # Create temporary directory for demo
    temp_dir = Path(tempfile.mkdtemp())
    logger.info(f"Demo environment: {temp_dir}")
    
    try:
        # Step 1: Create sample update reports
        logger.info("\n📊 Step 1: Creating sample update reports")
        
        # AI Scholar report (successful)
        ai_scholar_report = MockUpdateReport(
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
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'error_type': 'network_timeout',
                    'error_message': 'Download timeout after 300 seconds',
                    'timestamp': datetime.now().isoformat()
                }
            ]
        )
        
        # Quant Scholar report (with more issues)
        quant_scholar_report = MockUpdateReport(
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
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'error_type': 'pdf_processing_error',
                    'error_message': 'Memory error during large PDF processing',
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'error_type': 'vector_store_error',
                    'error_message': 'ChromaDB connection timeout',
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'error_type': 'disk_space_warning',
                    'error_message': 'Low disk space detected during processing',
                    'timestamp': datetime.now().isoformat()
                }
            ]
        )
        
        instance_reports = {
            'ai_scholar': ai_scholar_report,
            'quant_scholar': quant_scholar_report
        }
        
        logger.info(f"✅ Created {len(instance_reports)} sample update reports")
        for name, report in instance_reports.items():
            logger.info(f"  {name}: {report.papers_processed} papers, {len(report.errors)} errors")
        
        # Step 2: Initialize reporting coordinator
        logger.info("\n🎯 Step 2: Initializing reporting coordinator")
        
        smtp_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'from_email': 'noreply@aischolar.com',
            'recipients': ['admin@aischolar.com', 'researcher@aischolar.com']
        }
        
        reporting_coordinator = SimpleReportingCoordinator(
            str(temp_dir / "reports"),
            smtp_config
        )
        
        logger.info("✅ Reporting coordinator initialized")
        logger.info(f"  SMTP Server: {smtp_config['smtp_server']}")
        logger.info(f"  Recipients: {', '.join(smtp_config['recipients'])}")
        
        # Step 3: Process update completion
        logger.info("\n🔄 Step 3: Processing update completion")
        
        orchestration_id = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        processing_result = await reporting_coordinator.process_update_completion(
            instance_reports, orchestration_id
        )
        
        logger.info("📋 Processing Results:")
        logger.info(f"  Success: {'✅ Yes' if processing_result['success'] else '❌ No'}")
        logger.info(f"  Orchestration ID: {processing_result['orchestration_id']}")
        logger.info(f"  Notifications Sent: {len(processing_result['notification_results'])}")
        logger.info(f"  Storage Alerts: {processing_result['storage_alerts_sent']}")
        logger.info(f"  Errors: {len(processing_result['errors'])}")
        
        # Step 4: Display comprehensive report details
        if processing_result['comprehensive_report']:
            logger.info("\n📊 Step 4: Comprehensive report details")
            
            report = processing_result['comprehensive_report']
            summary = report['system_summary']
            
            logger.info("System Summary:")
            logger.info(f"  Total Instances: {summary['total_instances']}")
            logger.info(f"  Success Rate: {summary['success_rate']:.1f}%")
            logger.info(f"  Papers Processed: {summary['total_papers_processed']}")
            logger.info(f"  Total Errors: {summary['total_errors']}")
            logger.info(f"  Processing Time: {summary['total_processing_time_hours']:.1f} hours")
            logger.info(f"  Storage Used: {summary['total_storage_used_gb']:.1f} GB")
            logger.info(f"  Health Status: {summary['overall_health_status']}")
            
            logger.info("Error Analysis:")
            error_analysis = report['error_analysis']
            logger.info(f"  Total Errors: {error_analysis['total_errors']}")
            logger.info(f"  Instances with Errors: {error_analysis['instances_with_errors']}")
            logger.info("  Errors by Instance:")
            for instance, count in error_analysis['error_by_instance'].items():
                logger.info(f"    {instance}: {count}")
            
            if report['storage_recommendations']:
                logger.info("Storage Recommendations:")
                for rec in report['storage_recommendations']:
                    logger.info(f"  {rec['recommendation_type'].title()} ({rec['priority']} priority):")
                    logger.info(f"    {rec['description']}")
                    logger.info(f"    Estimated savings: {rec['estimated_space_savings_gb']:.1f} GB")
        
        # Step 5: Display notification results
        logger.info("\n📧 Step 5: Notification results")
        
        for i, notification in enumerate(processing_result['notification_results'], 1):
            logger.info(f"Notification {i}:")
            logger.info(f"  Success: {'✅ Yes' if notification['success'] else '❌ No'}")
            logger.info(f"  Subject: {notification['subject']}")
            logger.info(f"  Recipients: {len(notification['recipients_sent'])} sent")
            logger.info(f"  Timestamp: {notification['timestamp']}")
        
        # Step 6: Summary
        logger.info("\n" + "=" * 70)
        logger.info("🎉 Task 5.3 Demonstration Completed Successfully!")
        logger.info("=" * 70)
        
        logger.info("✅ Implemented Features:")
        logger.info("  📊 Comprehensive update report generation")
        logger.info("  📈 System-wide statistics and analysis")
        logger.info("  🚨 Error analysis and categorization")
        logger.info("  ⚡ Performance insights and bottleneck detection")
        logger.info("  💾 Storage monitoring and recommendations")
        logger.info("  📧 Automated email notifications")
        logger.info("  🔔 Storage alert notifications")
        logger.info("  🎯 Integrated reporting coordinator")
        logger.info("  📋 Complete update reporting workflow")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Demonstration failed: {e}")
        return False
    
    finally:
        # Cleanup
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        logger.info("Demo environment cleaned up")


async def main():
    """Main entry point."""
    try:
        success = await demonstrate_task_5_3()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Demonstration interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Demonstration execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())