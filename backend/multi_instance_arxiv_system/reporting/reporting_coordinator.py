"""
Reporting Coordinator for multi-instance ArXiv system.

Coordinates update reporting and notifications, integrating comprehensive
report generation with automated email notifications.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from .update_reporter import UpdateReporter, ComprehensiveUpdateReport
from .notification_service import NotificationService, NotificationResult
from ..shared.multi_instance_data_models import (
    UpdateReport, NotificationConfig, StorageStats
)

logger = logging.getLogger(__name__)


@dataclass
class ReportingConfig:
    """Configuration for reporting coordinator."""
    enable_comprehensive_reports: bool = True
    enable_notifications: bool = True
    enable_storage_monitoring: bool = True
    storage_alert_threshold: float = 85.0  # Percentage
    storage_critical_threshold: float = 95.0  # Percentage
    auto_cleanup_reports: bool = True
    report_retention_days: int = 90
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'enable_comprehensive_reports': self.enable_comprehensive_reports,
            'enable_notifications': self.enable_notifications,
            'enable_storage_monitoring': self.enable_storage_monitoring,
            'storage_alert_threshold': self.storage_alert_threshold,
            'storage_critical_threshold': self.storage_critical_threshold,
            'auto_cleanup_reports': self.auto_cleanup_reports,
            'report_retention_days': self.report_retention_days
        }


@dataclass
class ReportingResult:
    """Result of reporting coordination."""
    success: bool
    comprehensive_report: Optional[ComprehensiveUpdateReport] = None
    notification_results: List[NotificationResult] = None
    storage_alerts_sent: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.notification_results is None:
            self.notification_results = []
        if self.errors is None:
            self.errors = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'success': self.success,
            'comprehensive_report_id': self.comprehensive_report.report_id if self.comprehensive_report else None,
            'notification_results': [r.to_dict() for r in self.notification_results],
            'storage_alerts_sent': self.storage_alerts_sent,
            'errors': self.errors
        }


class ReportingCoordinator:
    """Coordinates comprehensive reporting and notifications."""
    
    def __init__(self, 
                 reporting_config: Optional[ReportingConfig] = None,
                 notification_config: Optional[NotificationConfig] = None,
                 reports_directory: str = "/var/log/multi_instance_arxiv/reports"):
        """
        Initialize reporting coordinator.
        
        Args:
            reporting_config: Configuration for reporting behavior
            notification_config: Configuration for email notifications
            reports_directory: Directory for storing reports
        """
        self.reporting_config = reporting_config or ReportingConfig()
        self.notification_config = notification_config or NotificationConfig()
        self.reports_directory = Path(reports_directory)
        
        # Initialize components
        self.update_reporter = UpdateReporter(str(self.reports_directory))
        self.notification_service = NotificationService(self.notification_config)
        
        # Reporting history
        self.reporting_history: List[ReportingResult] = []
        
        logger.info("ReportingCoordinator initialized")
    
    async def process_update_completion(self, 
                                      instance_reports: Dict[str, UpdateReport],
                                      orchestration_id: str) -> ReportingResult:
        """
        Process update completion with comprehensive reporting and notifications.
        
        Args:
            instance_reports: Dictionary of instance update reports
            orchestration_id: ID of the orchestration run
            
        Returns:
            ReportingResult with processing outcome
        """
        result = ReportingResult(success=True)
        
        logger.info(f"Processing update completion for orchestration: {orchestration_id}")
        
        try:
            # Generate comprehensive report
            if self.reporting_config.enable_comprehensive_reports:
                comprehensive_report = await self._generate_comprehensive_report(
                    instance_reports, orchestration_id, result
                )
                result.comprehensive_report = comprehensive_report
            
            # Send notifications
            if self.reporting_config.enable_notifications and self.notification_config.enabled:
                await self._send_update_notifications(result)
            
            # Check storage and send alerts if needed
            if self.reporting_config.enable_storage_monitoring:
                await self._monitor_storage_and_alert(instance_reports, result)
            
            # Cleanup old reports if configured
            if self.reporting_config.auto_cleanup_reports:
                await self._cleanup_old_reports()
            
            logger.info(f"Update completion processing finished: success={result.success}")
            
        except Exception as e:
            logger.error(f"Update completion processing failed: {e}")
            result.success = False
            result.errors.append(str(e))
        
        finally:
            # Record reporting attempt
            self.reporting_history.append(result)
            
            # Keep only recent history
            if len(self.reporting_history) > 50:
                self.reporting_history = self.reporting_history[-50:]
        
        return result
    
    async def _generate_comprehensive_report(self, 
                                           instance_reports: Dict[str, UpdateReport],
                                           orchestration_id: str,
                                           result: ReportingResult) -> Optional[ComprehensiveUpdateReport]:
        """Generate comprehensive report."""
        try:
            logger.info("Generating comprehensive report")
            
            comprehensive_report = await self.update_reporter.generate_comprehensive_report(
                instance_reports, orchestration_id
            )
            
            logger.info(f"Comprehensive report generated: {comprehensive_report.report_id}")
            return comprehensive_report
            
        except Exception as e:
            logger.error(f"Failed to generate comprehensive report: {e}")
            result.errors.append(f"Report generation failed: {e}")
            return None
    
    async def _send_update_notifications(self, result: ReportingResult) -> None:
        """Send update completion notifications."""
        try:
            if not result.comprehensive_report:
                logger.warning("No comprehensive report available for notifications")
                return
            
            logger.info("Sending update completion notification")
            
            # Send main update completion notification
            notification_result = await self.notification_service.send_update_completion_notification(
                result.comprehensive_report
            )
            result.notification_results.append(notification_result)
            
            # Send error summary if there are significant errors
            if result.comprehensive_report.error_analysis.get('total_errors', 0) > 0:
                logger.info("Sending error summary notification")
                
                error_notification_result = await self.notification_service.send_error_summary_notification(
                    result.comprehensive_report.error_analysis,
                    result.comprehensive_report.instance_reports
                )
                result.notification_results.append(error_notification_result)
            
            # Log notification results
            successful_notifications = sum(1 for r in result.notification_results if r.success)
            logger.info(f"Sent {successful_notifications}/{len(result.notification_results)} notifications successfully")
            
        except Exception as e:
            logger.error(f"Failed to send update notifications: {e}")
            result.errors.append(f"Notification sending failed: {e}")
    
    async def _monitor_storage_and_alert(self, 
                                       instance_reports: Dict[str, UpdateReport],
                                       result: ReportingResult) -> None:
        """Monitor storage usage and send alerts if needed."""
        try:
            logger.info("Monitoring storage usage")
            
            # Calculate total storage usage
            total_storage_mb = sum(report.storage_used_mb for report in instance_reports.values())
            total_storage_gb = total_storage_mb / 1024.0
            
            # Get storage statistics (simplified - in practice would check actual disk usage)
            storage_stats = {
                'total_storage_gb': total_storage_gb,
                'usage_percentage': min(total_storage_gb / 100.0 * 100, 100),  # Simplified calculation
                'instance_breakdown': {
                    name: report.storage_used_mb / 1024.0 
                    for name, report in instance_reports.items()
                }
            }
            
            # Check if storage alert is needed
            usage_percentage = storage_stats['usage_percentage']
            
            if usage_percentage >= self.reporting_config.storage_critical_threshold:
                alert_level = "critical"
            elif usage_percentage >= self.reporting_config.storage_alert_threshold:
                alert_level = "warning"
            else:
                alert_level = None
            
            if alert_level:
                logger.info(f"Storage usage {usage_percentage:.1f}% exceeds {alert_level} threshold")
                
                # Get storage recommendations from comprehensive report
                recommendations = []
                if result.comprehensive_report:
                    recommendations = result.comprehensive_report.storage_recommendations
                
                # Send storage alert
                storage_notification_result = await self.notification_service.send_storage_alert_notification(
                    storage_stats, recommendations
                )
                result.notification_results.append(storage_notification_result)
                
                if storage_notification_result.success:
                    result.storage_alerts_sent += 1
                    logger.info(f"Storage {alert_level} alert sent successfully")
                else:
                    logger.error(f"Failed to send storage {alert_level} alert")
            else:
                logger.info(f"Storage usage {usage_percentage:.1f}% is within normal limits")
            
        except Exception as e:
            logger.error(f"Storage monitoring failed: {e}")
            result.errors.append(f"Storage monitoring failed: {e}")
    
    async def _cleanup_old_reports(self) -> None:
        """Clean up old reports and logs."""
        try:
            logger.info("Cleaning up old reports")
            
            # Clean up comprehensive reports
            cleaned_reports = self.update_reporter.cleanup_old_reports(
                self.reporting_config.report_retention_days
            )
            
            # Clean up notification history
            cutoff_date = datetime.now() - timedelta(days=self.reporting_config.report_retention_days)
            original_count = len(self.reporting_history)
            self.reporting_history = [
                r for r in self.reporting_history 
                if hasattr(r, 'timestamp') and r.timestamp > cutoff_date
            ]
            cleaned_history = original_count - len(self.reporting_history)
            
            logger.info(f"Cleaned up {cleaned_reports} old reports and {cleaned_history} old history entries")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    async def send_test_notification(self) -> NotificationResult:
        """Send a test notification to verify configuration."""
        logger.info("Sending test notification")
        
        try:
            return self.notification_service.test_notification_setup()
        except Exception as e:
            logger.error(f"Test notification failed: {e}")
            return NotificationResult(
                success=False,
                message=f"Test notification failed: {e}"
            )
    
    def get_reporting_statistics(self) -> Dict[str, Any]:
        """Get reporting and notification statistics."""
        # Get notification statistics
        notification_stats = self.notification_service.get_notification_statistics()
        
        # Get reporting statistics
        total_reports = len(self.reporting_history)
        successful_reports = sum(1 for r in self.reporting_history if r.success)
        
        # Recent activity (last 7 days)
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_reports = [
            r for r in self.reporting_history 
            if hasattr(r, 'timestamp') and r.timestamp > recent_cutoff
        ]
        
        return {
            'reporting': {
                'total_reports_generated': total_reports,
                'successful_reports': successful_reports,
                'success_rate': (successful_reports / total_reports * 100) if total_reports > 0 else 0,
                'recent_reports_7d': len(recent_reports),
                'configuration': self.reporting_config.to_dict()
            },
            'notifications': notification_stats,
            'latest_reports': [
                {
                    'report_id': r.comprehensive_report.report_id if r.comprehensive_report else None,
                    'success': r.success,
                    'notifications_sent': len(r.notification_results),
                    'storage_alerts': r.storage_alerts_sent,
                    'errors': len(r.errors)
                }
                for r in self.reporting_history[-5:]  # Last 5 reports
            ]
        }
    
    def get_latest_comprehensive_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the latest comprehensive reports."""
        return self.update_reporter.get_latest_reports(limit)
    
    async def generate_storage_recommendations(self, 
                                             instance_reports: Dict[str, UpdateReport]) -> List[Dict[str, Any]]:
        """Generate storage recommendations without full report."""
        try:
            # Create a temporary comprehensive report to get recommendations
            temp_report = await self.update_reporter.generate_comprehensive_report(
                instance_reports, f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            return [rec.to_dict() for rec in temp_report.storage_recommendations]
            
        except Exception as e:
            logger.error(f"Failed to generate storage recommendations: {e}")
            return []
    
    def update_notification_config(self, new_config: NotificationConfig) -> bool:
        """Update notification configuration."""
        try:
            self.notification_config = new_config
            self.notification_service = NotificationService(new_config)
            logger.info("Notification configuration updated")
            return True
        except Exception as e:
            logger.error(f"Failed to update notification configuration: {e}")
            return False
    
    def update_reporting_config(self, new_config: ReportingConfig) -> bool:
        """Update reporting configuration."""
        try:
            self.reporting_config = new_config
            logger.info("Reporting configuration updated")
            return True
        except Exception as e:
            logger.error(f"Failed to update reporting configuration: {e}")
            return False