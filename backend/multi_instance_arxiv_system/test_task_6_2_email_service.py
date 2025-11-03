#!/usr/bin/env python3
"""
Test for Task 6.2: Email Notification Service functionality.

Tests the EmailNotificationService with SMTP configuration, multiple recipients,
priority levels, immediate alert system, and email delivery tracking with retry logic.
"""

import sys
import asyncio
import logging
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


def test_email_recipient_management():
    """Test EmailRecipient functionality and management."""
    try:
        from multi_instance_arxiv_system.reporting.email_notification_service import (
            EmailRecipient, NotificationPriority
        )
        
        logger.info("=== Testing EmailRecipient Management ===")
        
        # Test recipient creation
        recipient = EmailRecipient(
            email="test@example.com",
            name="Test User",
            priority_threshold=NotificationPriority.HIGH,
            enabled=True,
            notification_types=["alerts", "reports"]
        )
        
        assert recipient.email == "test@example.com", "Should set email correctly"
        assert recipient.name == "Test User", "Should set name correctly"
        assert recipient.priority_threshold == NotificationPriority.HIGH, "Should set priority threshold"
        
        logger.info("   ✓ EmailRecipient creation works")
        
        # Test should_receive logic
        should_receive_high = recipient.should_receive(NotificationPriority.HIGH, "alerts")
        assert should_receive_high == True, "Should receive high priority alerts"
        
        should_receive_low = recipient.should_receive(NotificationPriority.LOW, "alerts")
        assert should_receive_low == False, "Should not receive low priority alerts"
        
        should_receive_wrong_type = recipient.should_receive(NotificationPriority.HIGH, "other")
        assert should_receive_wrong_type == False, "Should not receive wrong notification type"
        
        logger.info("   ✓ Recipient filtering logic works")
        
        # Test disabled recipient
        recipient.enabled = False
        should_receive_disabled = recipient.should_receive(NotificationPriority.CRITICAL, "alerts")
        assert should_receive_disabled == False, "Disabled recipient should not receive notifications"
        
        logger.info("   ✓ Disabled recipient filtering works")
        
        return True
        
    except Exception as e:
        logger.error(f"EmailRecipient test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_email_notification_creation():
    """Test EmailNotification creation and management."""
    try:
        from multi_instance_arxiv_system.reporting.email_notification_service import (
            EmailNotification, EmailRecipient, NotificationPriority, NotificationStatus
        )
        
        logger.info("=== Testing EmailNotification Creation ===")
        
        # Create test recipients
        recipients = [
            EmailRecipient("user1@example.com", priority_threshold=NotificationPriority.NORMAL),
            EmailRecipient("user2@example.com", priority_threshold=NotificationPriority.HIGH),
            EmailRecipient("user3@example.com", enabled=False)
        ]
        
        # Create notification
        notification = EmailNotification(
            notification_id="test_001",
            subject="Test Notification",
            html_content="<h1>Test</h1>",
            text_content="Test",
            recipients=recipients,
            priority=NotificationPriority.HIGH,
            notification_type="test"
        )
        
        assert notification.notification_id == "test_001", "Should set notification ID"
        assert notification.priority == NotificationPriority.HIGH, "Should set priority"
        assert notification.status == NotificationStatus.PENDING, "Should start as pending"
        
        logger.info("   ✓ EmailNotification creation works")
        
        # Test eligible recipients
        eligible = notification.get_eligible_recipients()
        assert len(eligible) == 2, "Should have 2 eligible recipients (excluding disabled)"
        
        # Check specific recipients
        eligible_emails = [r.email for r in eligible]
        assert "user1@example.com" in eligible_emails, "Normal threshold user should receive high priority"
        assert "user2@example.com" in eligible_emails, "High threshold user should receive high priority"
        assert "user3@example.com" not in eligible_emails, "Disabled user should not receive"
        
        logger.info("   ✓ Eligible recipients filtering works")
        
        # Test retry logic
        notification.status = NotificationStatus.FAILED
        notification.attempts = 1
        notification.last_attempt_at = datetime.now() - timedelta(minutes=2)
        
        should_retry = notification.should_retry()
        assert should_retry == True, "Should retry after backoff period"
        
        # Test max attempts
        notification.attempts = 3
        should_not_retry = notification.should_retry()
        assert should_not_retry == False, "Should not retry after max attempts"
        
        logger.info("   ✓ Retry logic works correctly")
        
        # Test serialization
        notification_dict = notification.to_dict()
        assert isinstance(notification_dict, dict), "Should serialize to dictionary"
        assert notification_dict['notification_id'] == "test_001", "Should preserve notification ID"
        
        logger.info("   ✓ Notification serialization works")
        
        return True
        
    except Exception as e:
        logger.error(f"EmailNotification test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_email_notification_service_initialization():
    """Test EmailNotificationService initialization and configuration."""
    try:
        from multi_instance_arxiv_system.reporting.email_notification_service import (
            EmailNotificationService, NotificationPriority
        )
        from multi_instance_arxiv_system.shared.multi_instance_data_models import NotificationConfig
        
        logger.info("=== Testing EmailNotificationService Initialization ===")
        
        # Create test configuration
        config = NotificationConfig(
            enabled=True,
            recipients=["test1@example.com", "test2@example.com"],
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test_user",
            password="test_pass",
            from_email="system@example.com"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create service
            service = EmailNotificationService(
                notification_config=config,
                templates_directory=temp_dir,
                worker_threads=1
            )
            
            assert len(service.recipients) == 2, "Should load recipients from config"
            assert service.config.smtp_server == "smtp.example.com", "Should set SMTP server"
            assert len(service.workers) == 1, "Should start worker threads"
            
            logger.info("   ✓ Service initialization works")
            
            # Test recipient management
            success = service.add_recipient(
                email="test3@example.com",
                name="Test User 3",
                priority_threshold=NotificationPriority.HIGH
            )
            assert success == True, "Should add recipient successfully"
            assert len(service.recipients) == 3, "Should have 3 recipients after adding"
            
            logger.info("   ✓ Recipient addition works")
            
            # Test recipient removal
            success = service.remove_recipient("test3@example.com")
            assert success == True, "Should remove recipient successfully"
            assert len(service.recipients) == 2, "Should have 2 recipients after removal"
            
            logger.info("   ✓ Recipient removal works")
            
            # Test preference updates
            success = service.update_recipient_preferences(
                email="test1@example.com",
                priority_threshold=NotificationPriority.CRITICAL,
                enabled=False
            )
            assert success == True, "Should update preferences successfully"
            
            # Verify update
            recipient = next(r for r in service.recipients if r.email == "test1@example.com")
            assert recipient.priority_threshold == NotificationPriority.CRITICAL, "Should update priority threshold"
            assert recipient.enabled == False, "Should update enabled status"
            
            logger.info("   ✓ Preference updates work")
            
            # Test statistics
            stats = service.get_delivery_statistics()
            assert isinstance(stats, dict), "Should return statistics dictionary"
            assert 'total_notifications' in stats, "Should include total notifications"
            assert 'recipients_count' in stats, "Should include recipients count"
            
            logger.info("   ✓ Statistics collection works")
            
            # Cleanup
            service.shutdown()
            
        return True
        
    except Exception as e:
        logger.error(f"EmailNotificationService initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_notification_sending():
    """Test notification sending functionality."""
    try:
        from multi_instance_arxiv_system.reporting.email_notification_service import (
            EmailNotificationService, NotificationPriority
        )
        from multi_instance_arxiv_system.shared.multi_instance_data_models import NotificationConfig
        
        logger.info("=== Testing Notification Sending ===")
        
        # Create test configuration (using localhost for testing)
        config = NotificationConfig(
            enabled=True,
            recipients=["test@localhost"],
            smtp_server="localhost",
            smtp_port=25,
            username="",
            password="",
            from_email="system@localhost"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create service
            service = EmailNotificationService(
                notification_config=config,
                templates_directory=temp_dir,
                worker_threads=1
            )
            
            # Test basic notification sending (will fail SMTP but test logic)
            notification_id = await service.send_notification(
                subject="Test Notification",
                html_content="<h1>Test HTML Content</h1>",
                text_content="Test text content",
                priority=NotificationPriority.NORMAL,
                notification_type="test"
            )
            
            assert notification_id is not None, "Should return notification ID"
            assert notification_id in service.notification_history, "Should store in history"
            
            logger.info(f"   ✓ Basic notification queued: {notification_id}")
            
            # Test template notification
            # First create a simple template
            template_file = Path(temp_dir) / "test_template.html"
            with open(template_file, 'w') as f:
                f.write("<h1>{{ title }}</h1><p>{{ message }}</p>")
            
            template_notification_id = await service.send_template_notification(
                template_name="test_template.html",
                subject="Template Test",
                context={"title": "Test Title", "message": "Test Message"},
                priority=NotificationPriority.HIGH,
                notification_type="template_test"
            )
            
            assert template_notification_id is not None, "Should return template notification ID"
            
            logger.info(f"   ✓ Template notification queued: {template_notification_id}")
            
            # Test immediate alert
            alert_id = await service.send_immediate_alert(
                subject="Test Alert",
                message="This is a test critical alert",
                alert_type="test_alert"
            )
            
            assert alert_id is not None, "Should return alert notification ID"
            
            # Verify alert has critical priority
            alert_notification = service.notification_history[alert_id]
            assert alert_notification.priority == NotificationPriority.CRITICAL, "Alert should have critical priority"
            
            logger.info(f"   ✓ Immediate alert queued: {alert_id}")
            
            # Test notification status tracking
            status = service.get_notification_status(notification_id)
            assert status is not None, "Should return notification status"
            assert status['notification_id'] == notification_id, "Should match notification ID"
            
            logger.info("   ✓ Notification status tracking works")
            
            # Wait a moment for worker to process (will fail SMTP but test processing)
            await asyncio.sleep(2)
            
            # Check statistics after processing attempts
            stats = service.get_delivery_statistics()
            assert stats['total_notifications'] >= 3, "Should have at least 3 notifications"
            
            logger.info("   ✓ Notification processing and statistics work")
            
            # Cleanup
            service.shutdown()
            
        return True
        
    except Exception as e:
        logger.error(f"Notification sending test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_priority_and_retry_logic():
    """Test priority handling and retry logic."""
    try:
        from multi_instance_arxiv_system.reporting.email_notification_service import (
            EmailNotification, EmailRecipient, NotificationPriority, NotificationStatus
        )
        
        logger.info("=== Testing Priority and Retry Logic ===")
        
        # Create notifications with different priorities
        recipients = [EmailRecipient("test@example.com")]
        
        low_priority = EmailNotification(
            notification_id="low_001",
            subject="Low Priority",
            html_content="<p>Low</p>",
            text_content="Low",
            recipients=recipients,
            priority=NotificationPriority.LOW,
            notification_type="test"
        )
        
        critical_priority = EmailNotification(
            notification_id="critical_001",
            subject="Critical Priority",
            html_content="<p>Critical</p>",
            text_content="Critical",
            recipients=recipients,
            priority=NotificationPriority.CRITICAL,
            notification_type="test"
        )
        
        # Test priority comparison for queue ordering
        assert critical_priority < low_priority, "Critical should have higher priority than low"
        
        logger.info("   ✓ Priority comparison works")
        
        # Test retry logic with different scenarios
        failed_notification = EmailNotification(
            notification_id="retry_001",
            subject="Retry Test",
            html_content="<p>Retry</p>",
            text_content="Retry",
            recipients=recipients,
            priority=NotificationPriority.NORMAL,
            notification_type="test",
            max_attempts=3
        )
        
        # Test initial retry (should not retry when not failed)
        assert failed_notification.should_retry() == False, "Should not retry when not failed"
        
        # Set to failed and test retry
        failed_notification.status = NotificationStatus.FAILED
        failed_notification.attempts = 1
        failed_notification.last_attempt_at = datetime.now() - timedelta(minutes=5)
        
        assert failed_notification.should_retry() == True, "Should retry after backoff period"
        
        # Test too recent attempt
        failed_notification.last_attempt_at = datetime.now()
        assert failed_notification.should_retry() == False, "Should not retry too soon"
        
        # Test max attempts reached
        failed_notification.attempts = 3
        failed_notification.last_attempt_at = datetime.now() - timedelta(minutes=10)
        assert failed_notification.should_retry() == False, "Should not retry after max attempts"
        
        logger.info("   ✓ Retry logic works correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"Priority and retry logic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_template_system():
    """Test email template system."""
    try:
        from multi_instance_arxiv_system.reporting.email_notification_service import EmailNotificationService
        from multi_instance_arxiv_system.shared.multi_instance_data_models import NotificationConfig
        
        logger.info("=== Testing Template System ===")
        
        config = NotificationConfig(
            enabled=True,
            recipients=["test@example.com"],
            smtp_server="localhost",
            smtp_port=25,
            from_email="system@localhost"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            service = EmailNotificationService(
                notification_config=config,
                templates_directory=temp_dir,
                worker_threads=1
            )
            
            # Check that default templates were created
            templates_dir = Path(temp_dir)
            critical_alert_template = templates_dir / "critical_alert.html"
            assert critical_alert_template.exists(), "Should create default critical alert template"
            
            logger.info("   ✓ Default templates created")
            
            # Test template rendering
            template_content = service.jinja_env.get_template("critical_alert.html")
            rendered = template_content.render(
                timestamp=datetime.now(),
                alert_title="Test Alert",
                alert_message="Test message",
                alert_type="test"
            )
            
            assert "Test Alert" in rendered, "Should render template variables"
            assert "Test message" in rendered, "Should include alert message"
            
            logger.info("   ✓ Template rendering works")
            
            # Test custom template creation
            custom_template = templates_dir / "custom_test.html"
            with open(custom_template, 'w') as f:
                f.write("<h1>{{ custom_title }}</h1><p>{{ custom_content }}</p>")
            
            # Reload Jinja environment to pick up new template
            service.jinja_env = service.jinja_env.__class__(
                loader=service.jinja_env.loader,
                autoescape=service.jinja_env.autoescape
            )
            
            custom_rendered = service.jinja_env.get_template("custom_test.html").render(
                custom_title="Custom Title",
                custom_content="Custom Content"
            )
            
            assert "Custom Title" in custom_rendered, "Should render custom template"
            
            logger.info("   ✓ Custom template rendering works")
            
            service.shutdown()
            
        return True
        
    except Exception as e:
        logger.error(f"Template system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all email notification service tests."""
    logger.info("Starting Task 6.2 Email Notification Service Tests...")
    
    tests = [
        ("EmailRecipient Management", test_email_recipient_management),
        ("EmailNotification Creation", test_email_notification_creation),
        ("Service Initialization", test_email_notification_service_initialization),
        ("Notification Sending", lambda: asyncio.run(test_notification_sending())),
        ("Priority and Retry Logic", test_priority_and_retry_logic),
        ("Template System", test_template_system)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            if test_func():
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
        logger.info("🎉 All tests passed! Email Notification Service is working correctly.")
        return True
    else:
        logger.error("❌ Some tests failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)