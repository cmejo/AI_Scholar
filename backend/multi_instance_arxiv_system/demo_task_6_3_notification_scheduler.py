#!/usr/bin/env python3
"""
Demonstration of Task 6.3: Notification Scheduling and Management functionality.

This script demonstrates the complete notification scheduling and management system including:
- NotificationScheduler for different notification types
- Notification throttling to prevent spam
- Notification preferences and filtering
- Notification history and tracking
"""

import asyncio
import tempfile
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from multi_instance_arxiv_system.reporting.notification_scheduler import (
    NotificationScheduler, NotificationType, NotificationPriority, ThrottleRule
)
from multi_instance_arxiv_system.reporting.email_notification_service import EmailNotificationService
from multi_instance_arxiv_system.shared.multi_instance_data_models import NotificationConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_notification_types_and_priorities():
    """Demonstrate different notification types and priority levels."""
    logger.info("=== Demonstrating Notification Types and Priorities ===")
    
    # Show available notification types
    logger.info("Available Notification Types:")
    for notification_type in NotificationType:
        logger.info(f"  - {notification_type.name}: {notification_type.value}")
    
    # Show priority levels
    logger.info("\nNotification Priority Levels:")
    for priority in NotificationPriority:
        logger.info(f"  - {priority.name}: Level {priority.value}")
    
    # Show throttle rules
    logger.info("\nThrottle Rules:")
    for rule in ThrottleRule:
        logger.info(f"  - {rule.name}: {rule.value}")


async def demo_notification_scheduler_setup():
    """Demonstrate notification scheduler setup and configuration."""
    logger.info("=== Demonstrating Notification Scheduler Setup ===")
    
    # Create notification configuration
    notification_config = NotificationConfig(
        enabled=False,  # Disable actual email sending for demo
        recipients=["admin@example.com", "user@example.com"],
        smtp_server="smtp.example.com",
        smtp_port=587,
        username="system@example.com",
        password="password",
        from_email="multi-instance-arxiv@example.com"
    )
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create email service
        email_service = EmailNotificationService(notification_config, temp_dir)
        logger.info(f"Created EmailNotificationService with {len(notification_config.recipients)} recipients")
        
        # Create notification scheduler
        db_path = Path(temp_dir) / "scheduler.db"
        scheduler = NotificationScheduler(email_service, str(db_path))
        logger.info(f"Created NotificationScheduler with database: {db_path}")
        
        # Start scheduler
        scheduler.start_scheduler()
        logger.info("Started notification scheduler background processing")
        
        return scheduler, email_service


async def demo_user_preferences_management(scheduler):
    """Demonstrate user preferences and filtering."""
    logger.info("=== Demonstrating User Preferences Management ===")
    
    # Add admin user with high priority threshold
    scheduler.add_user_preferences(
        user_id="admin",
        email="admin@example.com",
        enabled_types={
            NotificationType.MONTHLY_UPDATE_SUCCESS,
            NotificationType.MONTHLY_UPDATE_FAILURE,
            NotificationType.STORAGE_CRITICAL,
            NotificationType.ERROR_SUMMARY
        },
        priority_threshold=NotificationPriority.NORMAL,
        throttle_rules={
            NotificationType.MONTHLY_UPDATE_SUCCESS: ThrottleRule.DAILY,
            NotificationType.STORAGE_CRITICAL: ThrottleRule.NO_THROTTLE
        },
        quiet_hours_start=22,
        quiet_hours_end=6
    )
    logger.info("Added admin user preferences:")
    logger.info("  - Receives: Monthly updates, storage alerts, error summaries")
    logger.info("  - Priority threshold: NORMAL")
    logger.info("  - Quiet hours: 22:00 - 06:00")
    
    # Add regular user with different preferences
    scheduler.add_user_preferences(
        user_id="user1",
        email="user1@example.com",
        enabled_types={NotificationType.MONTHLY_UPDATE_SUCCESS},
        disabled_types={
            NotificationType.SYSTEM_HEALTH,
            NotificationType.PERFORMANCE_ALERT
        },
        priority_threshold=NotificationPriority.HIGH,
        throttle_rules={
            NotificationType.MONTHLY_UPDATE_SUCCESS: ThrottleRule.WEEKLY
        }
    )
    logger.info("Added regular user preferences:")
    logger.info("  - Receives: Only monthly update successes")
    logger.info("  - Priority threshold: HIGH")
    logger.info("  - Disabled: System health, performance alerts")
    
    # Add monitoring user for critical alerts only
    scheduler.add_user_preferences(
        user_id="monitoring",
        email="monitoring@example.com",
        enabled_types={
            NotificationType.STORAGE_CRITICAL,
            NotificationType.ERROR_SUMMARY,
            NotificationType.SECURITY_ALERT
        },
        priority_threshold=NotificationPriority.CRITICAL,
        throttle_rules={
            NotificationType.STORAGE_CRITICAL: ThrottleRule.NO_THROTTLE,
            NotificationType.SECURITY_ALERT: ThrottleRule.NO_THROTTLE
        }
    )
    logger.info("Added monitoring user preferences:")
    logger.info("  - Receives: Only critical alerts")
    logger.info("  - Priority threshold: CRITICAL")
    logger.info("  - No throttling for critical alerts")
    
    # Show preference filtering examples
    logger.info("\nPreference Filtering Examples:")
    
    admin_prefs = scheduler.get_user_preferences("admin")
    user1_prefs = scheduler.get_user_preferences("user1")
    monitoring_prefs = scheduler.get_user_preferences("monitoring")
    
    test_cases = [
        (NotificationType.MONTHLY_UPDATE_SUCCESS, NotificationPriority.NORMAL),
        (NotificationType.STORAGE_CRITICAL, NotificationPriority.CRITICAL),
        (NotificationType.SYSTEM_HEALTH, NotificationPriority.LOW),
        (NotificationType.ERROR_SUMMARY, NotificationPriority.HIGH)
    ]
    
    for notification_type, priority in test_cases:
        logger.info(f"\n  {notification_type.value} ({priority.name}):")
        logger.info(f"    Admin: {'✓' if admin_prefs.should_receive(notification_type, priority) else '✗'}")
        logger.info(f"    User1: {'✓' if user1_prefs.should_receive(notification_type, priority) else '✗'}")
        logger.info(f"    Monitoring: {'✓' if monitoring_prefs.should_receive(notification_type, priority) else '✗'}")


async def demo_notification_throttling(scheduler):
    """Demonstrate notification throttling functionality."""
    logger.info("=== Demonstrating Notification Throttling ===")
    
    throttler = scheduler.throttler
    
    # Demonstrate different throttle rules
    logger.info("Testing throttle rules for user 'test_user':")
    
    # Test no throttle (should always allow)
    can_send = throttler.can_send_notification(
        "test_user",
        NotificationType.STORAGE_CRITICAL,
        ThrottleRule.NO_THROTTLE,
        NotificationPriority.CRITICAL
    )
    logger.info(f"  No throttle rule: {'✓ Allowed' if can_send else '✗ Blocked'}")
    
    # Test critical notifications bypass throttling
    can_send_critical = throttler.can_send_notification(
        "test_user",
        NotificationType.STORAGE_CRITICAL,
        ThrottleRule.HOURLY,
        NotificationPriority.CRITICAL
    )
    logger.info(f"  Critical notification (with hourly throttle): {'✓ Allowed' if can_send_critical else '✗ Blocked'}")
    
    # Simulate sending notifications to reach throttle limit
    logger.info("\nSimulating notification sending to test throttling:")
    
    for i in range(12):  # Send more than hourly limit (10)
        can_send = throttler.can_send_notification(
            "throttle_test_user",
            NotificationType.MONTHLY_UPDATE_SUCCESS,
            ThrottleRule.HOURLY,
            NotificationPriority.NORMAL
        )
        
        if can_send:
            throttler.record_notification("throttle_test_user")
            logger.info(f"  Notification {i+1}: ✓ Sent")
        else:
            logger.info(f"  Notification {i+1}: ✗ Throttled (reached hourly limit)")
            break
    
    # Show throttle status
    status = throttler.get_throttle_status("throttle_test_user")
    logger.info(f"\nThrottle status for 'throttle_test_user':")
    for rule, rule_status in status.items():
        logger.info(f"  {rule}: {rule_status['recent_count']}/{rule_status['max_count']} "
                   f"({rule_status['remaining']} remaining)")


async def demo_scheduled_notifications(scheduler):
    """Demonstrate scheduled notification functionality."""
    logger.info("=== Demonstrating Scheduled Notifications ===")
    
    # Schedule immediate notification
    immediate_id = scheduler.schedule_notification(
        notification_type=NotificationType.MONTHLY_UPDATE_SUCCESS,
        subject="Demo Monthly Update Completed",
        template_name="update_success.html",
        context={
            "report": {
                "generated_at": datetime.now(),
                "system_summary": {
                    "total_instances": 2,
                    "success_rate": 95.5,
                    "total_papers_processed": 1250,
                    "total_processing_time_hours": 4.2,
                    "total_storage_used_gb": 15.8
                }
            }
        },
        scheduled_at=datetime.now() + timedelta(seconds=5),
        priority=NotificationPriority.NORMAL
    )
    logger.info(f"Scheduled immediate notification: {immediate_id}")
    
    # Schedule recurring weekly notification
    weekly_id = scheduler.schedule_notification(
        notification_type=NotificationType.SYSTEM_HEALTH,
        subject="Weekly System Health Report",
        template_name="system_health.html",
        context={"health_status": "good", "uptime": "99.9%"},
        scheduled_at=datetime.now() + timedelta(days=7),
        priority=NotificationPriority.LOW,
        recurring=True,
        recurrence_pattern="weekly"
    )
    logger.info(f"Scheduled weekly recurring notification: {weekly_id}")
    
    # Schedule maintenance reminder
    maintenance_id = scheduler.schedule_notification(
        notification_type=NotificationType.MAINTENANCE_REMINDER,
        subject="Scheduled Maintenance Reminder",
        template_name="maintenance_reminder.html",
        context={
            "maintenance_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "estimated_downtime": "2 hours"
        },
        scheduled_at=datetime.now() + timedelta(days=25),
        priority=NotificationPriority.HIGH
    )
    logger.info(f"Scheduled maintenance reminder: {maintenance_id}")
    
    # Show scheduled notifications
    scheduled = scheduler.get_scheduled_notifications(status="pending")
    logger.info(f"\nTotal scheduled notifications: {len(scheduled)}")
    
    for notification in scheduled:
        logger.info(f"  - {notification.notification_id}")
        logger.info(f"    Type: {notification.notification_type.value}")
        logger.info(f"    Subject: {notification.subject}")
        logger.info(f"    Scheduled: {notification.scheduled_at}")
        logger.info(f"    Priority: {notification.priority.name}")
        logger.info(f"    Recurring: {notification.recurring}")
    
    # Cancel one notification
    success = scheduler.cancel_scheduled_notification(maintenance_id)
    logger.info(f"\nCancelled maintenance reminder: {'✓' if success else '✗'}")


async def demo_immediate_notifications(scheduler):
    """Demonstrate immediate notification sending with filtering."""
    logger.info("=== Demonstrating Immediate Notifications ===")
    
    # Send monthly update success notification
    result1 = await scheduler.send_immediate_notification(
        notification_type=NotificationType.MONTHLY_UPDATE_SUCCESS,
        subject="Monthly Update Completed Successfully",
        template_name="update_success.html",
        context={
            "report": {
                "generated_at": datetime.now(),
                "system_summary": {
                    "total_instances": 2,
                    "success_rate": 98.5,
                    "total_papers_processed": 1500,
                    "total_processing_time_hours": 3.8
                }
            }
        },
        priority=NotificationPriority.NORMAL
    )
    
    logger.info("Sent monthly update success notification:")
    logger.info(f"  Success: {result1['success']}")
    logger.info(f"  Message: {result1['message']}")
    logger.info(f"  Recipients: {result1.get('sent_count', 0)}")
    logger.info(f"  Filtered: {result1.get('filtered_count', 0)}")
    
    # Send critical storage alert
    result2 = await scheduler.send_immediate_notification(
        notification_type=NotificationType.STORAGE_CRITICAL,
        subject="CRITICAL: Storage Space Nearly Full",
        template_name="storage_alert.html",
        context={
            "alert_level": "critical",
            "total_storage_gb": 500.0,
            "usage_percentage": 96.5,
            "threshold": 95,
            "recommendations": [
                {"description": "Clean up old processed files", "priority": "high"},
                {"description": "Archive old reports", "priority": "medium"}
            ]
        },
        priority=NotificationPriority.CRITICAL
    )
    
    logger.info("\nSent critical storage alert:")
    logger.info(f"  Success: {result2['success']}")
    logger.info(f"  Message: {result2['message']}")
    logger.info(f"  Recipients: {result2.get('sent_count', 0)}")
    logger.info(f"  Filtered: {result2.get('filtered_count', 0)}")
    
    # Send low priority system health (should be filtered for some users)
    result3 = await scheduler.send_immediate_notification(
        notification_type=NotificationType.SYSTEM_HEALTH,
        subject="System Health Check - All Systems Normal",
        template_name="system_health.html",
        context={"status": "healthy", "uptime": "99.9%"},
        priority=NotificationPriority.LOW
    )
    
    logger.info("\nSent low priority system health notification:")
    logger.info(f"  Success: {result3['success']}")
    logger.info(f"  Message: {result3['message']}")
    logger.info(f"  Recipients: {result3.get('sent_count', 0)}")
    logger.info(f"  Filtered: {result3.get('filtered_count', 0)}")


def demo_notification_history(scheduler):
    """Demonstrate notification history and tracking."""
    logger.info("=== Demonstrating Notification History ===")
    
    # Get recent notification history
    recent_history = scheduler.get_notification_history(days=7)
    logger.info(f"Recent notifications (last 7 days): {len(recent_history)}")
    
    # Get history by type
    success_history = scheduler.get_notification_history(
        days=30, 
        notification_type=NotificationType.MONTHLY_UPDATE_SUCCESS
    )
    logger.info(f"Monthly update success notifications (last 30 days): {len(success_history)}")
    
    critical_history = scheduler.get_notification_history(
        days=30,
        notification_type=NotificationType.STORAGE_CRITICAL
    )
    logger.info(f"Critical storage alerts (last 30 days): {len(critical_history)}")
    
    # Show sample history entries
    if recent_history:
        logger.info("\nSample notification history entries:")
        for i, history in enumerate(recent_history[:3]):  # Show first 3
            logger.info(f"  {i+1}. {history.notification_id}")
            logger.info(f"     Type: {history.notification_type.value}")
            logger.info(f"     Subject: {history.subject}")
            logger.info(f"     Recipients: {len(history.recipients)}")
            logger.info(f"     Sent: {history.sent_at}")
            logger.info(f"     Priority: {history.priority.name}")
    
    # Demonstrate cleanup
    cleanup_result = scheduler.cleanup_old_data(days=1)  # Very aggressive for demo
    logger.info(f"\nCleanup results:")
    logger.info(f"  History records cleaned: {cleanup_result['history_cleaned']}")
    logger.info(f"  Scheduled notifications cleaned: {cleanup_result['scheduled_cleaned']}")


def demo_scheduler_statistics(scheduler):
    """Demonstrate scheduler statistics and monitoring."""
    logger.info("=== Demonstrating Scheduler Statistics ===")
    
    # Get comprehensive statistics
    stats = scheduler.get_statistics()
    
    logger.info("Notification Scheduler Statistics:")
    logger.info(f"  Total users: {stats['total_users']}")
    logger.info(f"  Active users: {stats['active_users']}")
    logger.info(f"  Total scheduled notifications: {stats['total_scheduled']}")
    logger.info(f"  Pending scheduled notifications: {stats['pending_scheduled']}")
    logger.info(f"  Recent notifications (7 days): {stats['recent_notifications_7d']}")
    logger.info(f"  Scheduler running: {stats['scheduler_running']}")
    
    # Show throttle status for sample users
    logger.info("\nSample throttle status:")
    throttle_status = stats.get('throttler_status', {})
    for user_id, user_status in list(throttle_status.items())[:2]:  # Show first 2 users
        logger.info(f"  User: {user_id}")
        for rule, rule_status in user_status.items():
            logger.info(f"    {rule}: {rule_status['recent_count']}/{rule_status['max_count']} "
                       f"({rule_status['remaining']} remaining)")


async def demo_filters_and_hooks(scheduler):
    """Demonstrate pre-send filters and post-send hooks."""
    logger.info("=== Demonstrating Filters and Hooks ===")
    
    # Add a pre-send filter
    def spam_filter(notification_type, subject, context, priority):
        """Filter out notifications with 'spam' in subject."""
        if 'spam' in subject.lower():
            logger.info(f"  🚫 Pre-send filter blocked notification: {subject}")
            return False
        logger.info(f"  ✓ Pre-send filter approved notification: {subject}")
        return True
    
    scheduler.add_pre_send_filter(spam_filter)
    
    # Add a post-send hook
    def notification_logger(notification_id, notification_type, recipients):
        """Log notification sending."""
        logger.info(f"  📧 Post-send hook: Logged notification {notification_id} "
                   f"to {len(recipients)} recipients")
    
    scheduler.add_post_send_hook(notification_logger)
    
    # Test filter - this should be blocked
    result1 = await scheduler.send_immediate_notification(
        notification_type=NotificationType.CUSTOM,
        subject="This is spam notification",
        template_name="critical_alert.html",
        context={"alert_title": "Spam", "alert_message": "This should be blocked"},
        priority=NotificationPriority.NORMAL
    )
    
    logger.info(f"Spam notification result: {result1['message']}")
    
    # Test normal notification - this should go through
    result2 = await scheduler.send_immediate_notification(
        notification_type=NotificationType.CUSTOM,
        subject="Important System Update",
        template_name="critical_alert.html",
        context={"alert_title": "Update", "alert_message": "System updated successfully"},
        priority=NotificationPriority.NORMAL
    )
    
    logger.info(f"Normal notification result: {result2['message']}")


async def main():
    """Run all notification scheduler demonstrations."""
    logger.info("🚀 Starting Task 6.3 Notification Scheduling and Management Demonstration")
    logger.info("=" * 80)
    
    try:
        # Demonstrate notification types and priorities
        demo_notification_types_and_priorities()
        
        # Setup scheduler
        scheduler, email_service = await demo_notification_scheduler_setup()
        
        # Demonstrate user preferences
        await demo_user_preferences_management(scheduler)
        
        # Demonstrate throttling
        await demo_notification_throttling(scheduler)
        
        # Demonstrate scheduled notifications
        await demo_scheduled_notifications(scheduler)
        
        # Demonstrate immediate notifications
        await demo_immediate_notifications(scheduler)
        
        # Demonstrate history tracking
        demo_notification_history(scheduler)
        
        # Demonstrate statistics
        demo_scheduler_statistics(scheduler)
        
        # Demonstrate filters and hooks
        await demo_filters_and_hooks(scheduler)
        
        # Cleanup
        scheduler.stop_scheduler()
        email_service.shutdown()
        
        logger.info("=" * 80)
        logger.info("✅ Task 6.3 Implementation Demonstration Complete!")
        logger.info("")
        logger.info("📋 Summary of Implemented Components:")
        logger.info("  ✓ NotificationScheduler - Comprehensive scheduling and management")
        logger.info("  ✓ NotificationTypes - Multiple notification categories")
        logger.info("  ✓ NotificationPriority - Priority-based filtering and routing")
        logger.info("  ✓ NotificationThrottler - Spam prevention and rate limiting")
        logger.info("  ✓ NotificationPreferences - User-specific preferences and filtering")
        logger.info("  ✓ ScheduledNotifications - Future and recurring notifications")
        logger.info("  ✓ NotificationHistory - Complete tracking and audit trail")
        logger.info("  ✓ Database persistence - SQLite-based data storage")
        logger.info("  ✓ Pre-send filters - Customizable notification filtering")
        logger.info("  ✓ Post-send hooks - Extensible notification processing")
        logger.info("")
        logger.info("🎯 Requirements Satisfied:")
        logger.info("  ✓ 7.1 - NotificationScheduler for different notification types")
        logger.info("  ✓ 7.7 - Notification throttling to prevent spam")
        logger.info("  ✓ 6.4 - Notification preferences and filtering")
        logger.info("  ✓ 7.1 - Notification history and tracking")
        logger.info("")
        logger.info("🔧 Key Features:")
        logger.info("  • Multiple notification types with priority levels")
        logger.info("  • User-specific preferences with quiet hours and throttling")
        logger.info("  • Scheduled and recurring notifications")
        logger.info("  • Comprehensive throttling with bypass for critical alerts")
        logger.info("  • Complete notification history with cleanup")
        logger.info("  • Extensible filtering and hook system")
        logger.info("  • SQLite database persistence")
        logger.info("  • Background scheduler with graceful shutdown")
        
        return True
        
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)