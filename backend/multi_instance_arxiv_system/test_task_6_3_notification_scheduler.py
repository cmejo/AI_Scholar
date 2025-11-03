#!/usr/bin/env python3
"""
Test for Task 6.3: Notification Scheduling and Management functionality.

Tests the notification scheduler including different notification types, throttling,
preferences, filtering, and notification history tracking.
"""

import sys
import asyncio
import tempfile
import logging
from pathlib import Path
from datetime import datetime, timedelta
import time

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_notification_scheduler_initialization():
    """Test NotificationScheduler initialization."""
    try:
        from multi_instance_arxiv_system.reporting.notification_scheduler import (
            NotificationScheduler, NotificationType, NotificationPriority, ThrottleRule
        )
        from multi_instance_arxiv_system.reporting.email_notification_service import EmailNotificationService
        from multi_instance_arxiv_system.shared.multi_instance_data_models import NotificationConfig
        
        logger.info("=== Testing NotificationScheduler Initialization ===")
        
        # Create mock email service
        notification_config = NotificationConfig(
            enabled=True,
            recipients=["test@example.com"],
            smtp_server="localhost",
            smtp_port=587,
            username="",
            password="",
            from_email="system@example.com"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            email_service = EmailNotificationService(notification_config, temp_dir)
            
            # Create scheduler
            db_path = Path(temp_dir) / "test_scheduler.db"
            scheduler = NotificationScheduler(email_service, str(db_path))
            
            assert scheduler is not None, "Should create scheduler"
            assert scheduler.email_service == email_service, "Should set email service"
            assert len(scheduler.preferences) == 0, "Should start with no preferences"
            assert len(scheduler.scheduled_notifications) == 0, "Should start with no scheduled notifications"
            
            logger.info("   ✓ NotificationScheduler created successfully")
            
            # Test database initialization
            assert Path(db_path).exists(), "Should create database file"
            
            logger.info("   ✓ Database initialized successfully")
            
            # Cleanup
            scheduler.stop_scheduler()
            email_service.shutdown()
        
        return True
        
    except Exception as e:
        logger.error(f"NotificationScheduler initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_user_preferences_management():
    """Test user preferences management."""
    try:
        from multi_instance_arxiv_system.reporting.notification_scheduler import (
            NotificationScheduler, NotificationType, NotificationPriority, ThrottleRule
        )
        from multi_instance_arxiv_system.reporting.email_notification_service import EmailNotificationService
        from multi_instance_arxiv_system.shared.multi_instance_data_models import NotificationConfig
        
        logger.info("=== Testing User Preferences Management ===")
        
        # Create scheduler
        notification_config = NotificationConfig(
            enabled=True,
            recipients=["test@example.com"],
            smtp_server="localhost",
            smtp_port=587,
            username="",
            password="",
            from_email="system@example.com"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            email_service = EmailNotificationService(notification_config, temp_dir)
            db_path = Path(temp_dir) / "test_scheduler.db"
            scheduler = NotificationScheduler(email_service, str(db_path))
            
            # Add user preferences
            success = scheduler.add_user_preferences(
                user_id="user1",
                email="user1@example.com",
                enabled_types={NotificationType.MONTHLY_UPDATE_SUCCESS, NotificationType.STORAGE_WARNING},
                disabled_types={NotificationType.SYSTEM_HEALTH},
                priority_threshold=NotificationPriority.NORMAL,
                throttle_rules={
                    NotificationType.MONTHLY_UPDATE_SUCCESS: ThrottleRule.DAILY,
                    NotificationType.STORAGE_WARNING: ThrottleRule.HOURLY
                },
                quiet_hours_start=22,
                quiet_hours_end=6
            )
            
            assert success == True, "Should add user preferences successfully"
            assert len(scheduler.preferences) == 1, "Should have one user preference"
            
            logger.info("   ✓ User preferences added successfully")
            
            # Get user preferences
            prefs = scheduler.get_user_preferences("user1")
            assert prefs is not None, "Should retrieve user preferences"
            assert prefs.email == "user1@example.com", "Should have correct email"
            assert NotificationType.MONTHLY_UPDATE_SUCCESS in prefs.enabled_types, "Should have enabled types"
            assert NotificationType.SYSTEM_HEALTH in prefs.disabled_types, "Should have disabled types"
            
            logger.info("   ✓ User preferences retrieved successfully")
            
            # Test preference filtering
            should_receive_success = prefs.should_receive(
                NotificationType.MONTHLY_UPDATE_SUCCESS, 
                NotificationPriority.NORMAL
            )
            assert should_receive_success == True, "Should receive enabled notification type"
            
            should_receive_health = prefs.should_receive(
                NotificationType.SYSTEM_HEALTH,
                NotificationPriority.NORMAL
            )
            assert should_receive_health == False, "Should not receive disabled notification type"
            
            should_receive_low_priority = prefs.should_receive(
                NotificationType.MONTHLY_UPDATE_SUCCESS,
                NotificationPriority.LOW
            )
            assert should_receive_low_priority == False, "Should not receive low priority notification"
            
            logger.info("   ✓ Preference filtering working correctly")
            
            # Cleanup
            scheduler.stop_scheduler()
            email_service.shutdown()
        
        return True
        
    except Exception as e:
        logger.error(f"User preferences management test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_notification_throttling():
    """Test notification throttling functionality."""
    try:
        from multi_instance_arxiv_system.reporting.notification_scheduler import (
            NotificationThrottler, NotificationType, NotificationPriority, ThrottleRule
        )
        
        logger.info("=== Testing Notification Throttling ===")
        
        # Create throttler
        throttler = NotificationThrottler()
        
        # Test no throttle
        can_send = throttler.can_send_notification(
            "user1", 
            NotificationType.MONTHLY_UPDATE_SUCCESS,
            ThrottleRule.NO_THROTTLE,
            NotificationPriority.NORMAL
        )
        assert can_send == True, "Should allow sending with no throttle"
        
        logger.info("   ✓ No throttle rule working")
        
        # Test critical notifications bypass throttling
        can_send_critical = throttler.can_send_notification(
            "user1",
            NotificationType.STORAGE_CRITICAL,
            ThrottleRule.HOURLY,
            NotificationPriority.CRITICAL
        )
        assert can_send_critical == True, "Should allow critical notifications"
        
        logger.info("   ✓ Critical notifications bypass throttling")
        
        # Test hourly throttling
        # Send notifications up to limit
        for i in range(10):  # Default hourly limit
            can_send = throttler.can_send_notification(
                "user2",
                NotificationType.STORAGE_WARNING,
                ThrottleRule.HOURLY,
                NotificationPriority.NORMAL
            )
            if can_send:
                throttler.record_notification("user2")
        
        # Should be throttled now
        can_send_throttled = throttler.can_send_notification(
            "user2",
            NotificationType.STORAGE_WARNING,
            ThrottleRule.HOURLY,
            NotificationPriority.NORMAL
        )
        assert can_send_throttled == False, "Should be throttled after reaching limit"
        
        logger.info("   ✓ Hourly throttling working correctly")
        
        # Test throttle status
        status = throttler.get_throttle_status("user2")
        assert isinstance(status, dict), "Should return throttle status"
        assert 'hourly' in status, "Should have hourly status"
        assert status['hourly']['recent_count'] >= 10, "Should track recent notifications"
        
        logger.info("   ✓ Throttle status tracking working")
        
        return True
        
    except Exception as e:
        logger.error(f"Notification throttling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scheduled_notifications():
    """Test scheduled notification functionality."""
    try:
        from multi_instance_arxiv_system.reporting.notification_scheduler import (
            NotificationScheduler, NotificationType, NotificationPriority
        )
        from multi_instance_arxiv_system.reporting.email_notification_service import EmailNotificationService
        from multi_instance_arxiv_system.shared.multi_instance_data_models import NotificationConfig
        
        logger.info("=== Testing Scheduled Notifications ===")
        
        # Create scheduler
        notification_config = NotificationConfig(
            enabled=False,  # Disable actual email sending for test
            recipients=["test@example.com"],
            smtp_server="localhost",
            smtp_port=587,
            username="",
            password="",
            from_email="system@example.com"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            email_service = EmailNotificationService(notification_config, temp_dir)
            db_path = Path(temp_dir) / "test_scheduler.db"
            scheduler = NotificationScheduler(email_service, str(db_path))
            
            # Schedule a notification
            scheduled_time = datetime.now() + timedelta(seconds=2)
            notification_id = scheduler.schedule_notification(
                notification_type=NotificationType.MONTHLY_UPDATE_SUCCESS,
                subject="Test Scheduled Notification",
                template_name="update_success.html",
                context={"test": "data"},
                scheduled_at=scheduled_time,
                priority=NotificationPriority.NORMAL
            )
            
            assert notification_id is not None, "Should return notification ID"
            assert len(scheduler.scheduled_notifications) == 1, "Should have one scheduled notification"
            
            logger.info("   ✓ Notification scheduled successfully")
            
            # Get scheduled notifications
            scheduled = scheduler.get_scheduled_notifications(status="pending")
            assert len(scheduled) == 1, "Should have one pending notification"
            assert scheduled[0].notification_id == notification_id, "Should match notification ID"
            
            logger.info("   ✓ Scheduled notifications retrieved successfully")
            
            # Cancel scheduled notification
            success = scheduler.cancel_scheduled_notification(notification_id)
            assert success == True, "Should cancel notification successfully"
            
            cancelled_notification = scheduler.scheduled_notifications[notification_id]
            assert cancelled_notification.status == "cancelled", "Should be marked as cancelled"
            
            logger.info("   ✓ Notification cancelled successfully")
            
            # Cleanup
            scheduler.stop_scheduler()
            email_service.shutdown()
        
        return True
        
    except Exception as e:
        logger.error(f"Scheduled notifications test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_immediate_notifications():
    """Test immediate notification sending with filtering."""
    try:
        from multi_instance_arxiv_system.reporting.notification_scheduler import (
            NotificationScheduler, NotificationType, NotificationPriority
        )
        from multi_instance_arxiv_system.reporting.email_notification_service import EmailNotificationService
        from multi_instance_arxiv_system.shared.multi_instance_data_models import NotificationConfig
        
        logger.info("=== Testing Immediate Notifications ===")
        
        # Create scheduler
        notification_config = NotificationConfig(
            enabled=False,  # Disable actual email sending for test
            recipients=["test@example.com"],
            smtp_server="localhost",
            smtp_port=587,
            username="",
            password="",
            from_email="system@example.com"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            email_service = EmailNotificationService(notification_config, temp_dir)
            db_path = Path(temp_dir) / "test_scheduler.db"
            scheduler = NotificationScheduler(email_service, str(db_path))
            
            # Add user preferences
            scheduler.add_user_preferences(
                user_id="user1",
                email="user1@example.com",
                enabled_types={NotificationType.MONTHLY_UPDATE_SUCCESS},
                priority_threshold=NotificationPriority.NORMAL
            )
            
            # Send immediate notification
            result = await scheduler.send_immediate_notification(
                notification_type=NotificationType.MONTHLY_UPDATE_SUCCESS,
                subject="Test Immediate Notification",
                template_name="update_success.html",
                context={"test": "data"},
                priority=NotificationPriority.NORMAL
            )
            
            # Note: This will fail because email service is disabled, but we can check the filtering logic
            assert isinstance(result, dict), "Should return result dictionary"
            assert 'success' in result, "Should have success field"
            assert 'sent_count' in result, "Should have sent count"
            assert 'filtered_count' in result, "Should have filtered count"
            
            logger.info("   ✓ Immediate notification processing working")
            
            # Test with disabled notification type
            scheduler.add_user_preferences(
                user_id="user2",
                email="user2@example.com",
                disabled_types={NotificationType.MONTHLY_UPDATE_SUCCESS},
                priority_threshold=NotificationPriority.NORMAL
            )
            
            result2 = await scheduler.send_immediate_notification(
                notification_type=NotificationType.MONTHLY_UPDATE_SUCCESS,
                subject="Test Filtered Notification",
                template_name="update_success.html",
                context={"test": "data"},
                priority=NotificationPriority.NORMAL
            )
            
            # Should be filtered out (user2 has disabled this type)
            # The filtering happens at the preference level, so we check that user2 preferences work
            user2_prefs = scheduler.get_user_preferences("user2")
            should_receive = user2_prefs.should_receive(NotificationType.MONTHLY_UPDATE_SUCCESS, NotificationPriority.NORMAL)
            assert should_receive == False, "User2 should not receive disabled notification type"
            
            logger.info("   ✓ Notification filtering working correctly")
            
            # Cleanup
            scheduler.stop_scheduler()
            email_service.shutdown()
        
        return True
        
    except Exception as e:
        logger.error(f"Immediate notifications test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_notification_history():
    """Test notification history tracking."""
    try:
        from multi_instance_arxiv_system.reporting.notification_scheduler import (
            NotificationScheduler, NotificationType, NotificationPriority, NotificationHistory
        )
        from multi_instance_arxiv_system.reporting.email_notification_service import EmailNotificationService
        from multi_instance_arxiv_system.shared.multi_instance_data_models import NotificationConfig
        
        logger.info("=== Testing Notification History ===")
        
        # Create scheduler
        notification_config = NotificationConfig(
            enabled=False,
            recipients=["test@example.com"],
            smtp_server="localhost",
            smtp_port=587,
            username="",
            password="",
            from_email="system@example.com"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            email_service = EmailNotificationService(notification_config, temp_dir)
            db_path = Path(temp_dir) / "test_scheduler.db"
            scheduler = NotificationScheduler(email_service, str(db_path))
            
            # Add some mock history
            history1 = NotificationHistory(
                notification_id="test1",
                notification_type=NotificationType.MONTHLY_UPDATE_SUCCESS,
                subject="Test 1",
                recipients=["user1@example.com"],
                priority=NotificationPriority.NORMAL,
                sent_at=datetime.now() - timedelta(days=1),
                delivery_status={"user1@example.com": True},
                template_used="update_success.html",
                context_hash="hash1"
            )
            
            history2 = NotificationHistory(
                notification_id="test2",
                notification_type=NotificationType.STORAGE_WARNING,
                subject="Test 2",
                recipients=["user1@example.com"],
                priority=NotificationPriority.HIGH,
                sent_at=datetime.now() - timedelta(days=5),
                delivery_status={"user1@example.com": True},
                template_used="storage_alert.html",
                context_hash="hash2"
            )
            
            scheduler.notification_history = [history1, history2]
            
            # Test getting history
            recent_history = scheduler.get_notification_history(days=7)
            assert len(recent_history) == 2, "Should return all recent history"
            
            older_history = scheduler.get_notification_history(days=3)
            assert len(older_history) == 1, "Should filter by date"
            
            logger.info("   ✓ History retrieval working correctly")
            
            # Test filtering by type
            success_history = scheduler.get_notification_history(
                days=7, 
                notification_type=NotificationType.MONTHLY_UPDATE_SUCCESS
            )
            assert len(success_history) == 1, "Should filter by notification type"
            assert success_history[0].notification_type == NotificationType.MONTHLY_UPDATE_SUCCESS, "Should match type"
            
            logger.info("   ✓ History filtering by type working")
            
            # Test cleanup
            cleanup_result = scheduler.cleanup_old_data(days=2)
            assert isinstance(cleanup_result, dict), "Should return cleanup results"
            assert 'history_cleaned' in cleanup_result, "Should report history cleaned"
            
            # Should have removed old history
            remaining_history = scheduler.get_notification_history(days=30)
            assert len(remaining_history) == 1, "Should have cleaned old history"
            
            logger.info("   ✓ History cleanup working correctly")
            
            # Cleanup
            scheduler.stop_scheduler()
            email_service.shutdown()
        
        return True
        
    except Exception as e:
        logger.error(f"Notification history test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scheduler_statistics():
    """Test scheduler statistics and monitoring."""
    try:
        from multi_instance_arxiv_system.reporting.notification_scheduler import (
            NotificationScheduler, NotificationType, NotificationPriority
        )
        from multi_instance_arxiv_system.reporting.email_notification_service import EmailNotificationService
        from multi_instance_arxiv_system.shared.multi_instance_data_models import NotificationConfig
        
        logger.info("=== Testing Scheduler Statistics ===")
        
        # Create scheduler
        notification_config = NotificationConfig(
            enabled=False,
            recipients=["test@example.com"],
            smtp_server="localhost",
            smtp_port=587,
            username="",
            password="",
            from_email="system@example.com"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            email_service = EmailNotificationService(notification_config, temp_dir)
            db_path = Path(temp_dir) / "test_scheduler.db"
            scheduler = NotificationScheduler(email_service, str(db_path))
            
            # Add some users and scheduled notifications
            scheduler.add_user_preferences("user1", "user1@example.com")
            scheduler.add_user_preferences("user2", "user2@example.com")
            
            scheduler.schedule_notification(
                notification_type=NotificationType.MONTHLY_UPDATE_SUCCESS,
                subject="Test 1",
                template_name="update_success.html",
                context={},
                scheduled_at=datetime.now() + timedelta(hours=1)
            )
            
            # Get statistics
            stats = scheduler.get_statistics()
            
            assert isinstance(stats, dict), "Should return statistics dictionary"
            assert stats['total_users'] == 2, "Should count total users"
            assert stats['active_users'] == 2, "Should count active users"
            assert stats['total_scheduled'] == 1, "Should count scheduled notifications"
            assert stats['pending_scheduled'] == 1, "Should count pending notifications"
            assert 'recent_notifications_7d' in stats, "Should include recent notifications count"
            assert 'scheduler_running' in stats, "Should include scheduler status"
            assert 'throttler_status' in stats, "Should include throttler status"
            
            logger.info("   ✓ Statistics generation working correctly")
            logger.info(f"     Total users: {stats['total_users']}")
            logger.info(f"     Active users: {stats['active_users']}")
            logger.info(f"     Scheduled notifications: {stats['total_scheduled']}")
            
            # Cleanup
            scheduler.stop_scheduler()
            email_service.shutdown()
        
        return True
        
    except Exception as e:
        logger.error(f"Scheduler statistics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all notification scheduler tests."""
    logger.info("Starting Task 6.3 Notification Scheduling and Management Tests...")
    
    tests = [
        ("NotificationScheduler Initialization", test_notification_scheduler_initialization),
        ("User Preferences Management", test_user_preferences_management),
        ("Notification Throttling", test_notification_throttling),
        ("Scheduled Notifications", test_scheduled_notifications),
        ("Immediate Notifications", test_immediate_notifications),
        ("Notification History", test_notification_history),
        ("Scheduler Statistics", test_scheduler_statistics)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                logger.info(f"✅ {test_name} Test: PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} Test: FAILED")
                failed += 1
        except Exception as e:
            logger.error(f"❌ {test_name} Test: FAILED with exception: {e}")
            failed += 1
    
    logger.info(f"\n--- Test Summary ---")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 All tests passed! Notification Scheduling and Management is working correctly.")
        return True
    else:
        logger.error("❌ Some tests failed.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)