#!/usr/bin/env python3
"""
Demonstration of Task 6.2: Email Notification Service functionality.

This script demonstrates the complete EmailNotificationService including:
- SMTP configuration with multiple recipients and priority levels
- Immediate alert system for critical failures
- Email delivery tracking and retry logic with exponential backoff
- Template-based notifications and recipient management
"""

import asyncio
import logging
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from multi_instance_arxiv_system.reporting.email_notification_service import (
    EmailNotificationService, EmailRecipient, NotificationPriority, NotificationStatus
)
from multi_instance_arxiv_system.shared.multi_instance_data_models import NotificationConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_smtp_configuration():
    """Demonstrate SMTP configuration and setup."""
    logger.info("=== Demonstrating SMTP Configuration ===")
    
    # Create comprehensive notification configuration
    config = NotificationConfig(
        enabled=True,
        recipients=[
            "admin@example.com",
            "ops@example.com", 
            "alerts@example.com"
        ],
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        username="system@example.com",
        password="app_password_here",  # In production, use environment variables
        from_email="multi-instance-arxiv@example.com"
    )
    
    logger.info("SMTP Configuration:")
    logger.info(f"  Server: {config.smtp_server}:{config.smtp_port}")
    logger.info(f"  From Email: {config.from_email}")
    logger.info(f"  Recipients: {len(config.recipients)} configured")
    logger.info(f"  Authentication: {'Yes' if config.username else 'No'}")
    logger.info(f"  TLS/SSL: {'SSL' if config.smtp_port == 465 else 'TLS'}")
    
    return config


def demo_multiple_recipients_and_priorities():
    """Demonstrate multiple recipients with different priority levels."""
    logger.info("=== Demonstrating Multiple Recipients and Priority Levels ===")
    
    config = demo_smtp_configuration()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create service
        service = EmailNotificationService(
            notification_config=config,
            templates_directory=temp_dir,
            worker_threads=2
        )
        
        # Add recipients with different priority thresholds
        service.add_recipient(
            email="critical-alerts@example.com",
            name="Critical Alerts Team",
            priority_threshold=NotificationPriority.CRITICAL,
            notification_types=["alerts", "failures"]
        )
        
        service.add_recipient(
            email="dev-team@example.com", 
            name="Development Team",
            priority_threshold=NotificationPriority.HIGH,
            notification_types=["reports", "alerts"]
        )
        
        service.add_recipient(
            email="management@example.com",
            name="Management",
            priority_threshold=NotificationPriority.NORMAL,
            notification_types=["reports"]
        )
        
        logger.info("Configured Recipients:")
        for recipient in service.recipients:
            logger.info(f"  {recipient.email}:")
            logger.info(f"    Name: {recipient.name or 'N/A'}")
            logger.info(f"    Priority Threshold: {recipient.priority_threshold.name}")
            logger.info(f"    Notification Types: {', '.join(recipient.notification_types)}")
            logger.info(f"    Enabled: {recipient.enabled}")
        
        # Demonstrate priority filtering
        logger.info("\nPriority Filtering Examples:")
        
        # Test different priority levels
        test_cases = [
            (NotificationPriority.LOW, "reports"),
            (NotificationPriority.NORMAL, "reports"), 
            (NotificationPriority.HIGH, "alerts"),
            (NotificationPriority.CRITICAL, "failures")
        ]
        
        for priority, notification_type in test_cases:
            eligible_count = 0
            for recipient in service.recipients:
                if recipient.should_receive(priority, notification_type):
                    eligible_count += 1
            
            logger.info(f"  {priority.name} {notification_type}: {eligible_count} recipients would receive")
        
        service.shutdown()


async def demo_immediate_alert_system():
    """Demonstrate immediate alert system for critical failures."""
    logger.info("=== Demonstrating Immediate Alert System ===")
    
    config = demo_smtp_configuration()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        service = EmailNotificationService(
            notification_config=config,
            templates_directory=temp_dir,
            worker_threads=1
        )
        
        # Configure critical alerts recipient
        service.add_recipient(
            email="emergency@example.com",
            name="Emergency Response",
            priority_threshold=NotificationPriority.CRITICAL,
            notification_types=["all"]
        )
        
        logger.info("Sending immediate critical alerts...")
        
        # Send different types of critical alerts
        alert_scenarios = [
            {
                "subject": "System Storage Critical",
                "message": "System storage has reached 98% capacity. Immediate action required to prevent system failure.",
                "alert_type": "storage_critical"
            },
            {
                "subject": "Database Connection Lost", 
                "message": "Lost connection to primary database. System is operating in degraded mode.",
                "alert_type": "database_failure"
            },
            {
                "subject": "Memory Usage Critical",
                "message": "System memory usage has exceeded 95%. Risk of system instability.",
                "alert_type": "memory_critical"
            }
        ]
        
        alert_ids = []
        for scenario in alert_scenarios:
            alert_id = await service.send_immediate_alert(
                subject=scenario["subject"],
                message=scenario["message"],
                alert_type=scenario["alert_type"]
            )
            alert_ids.append(alert_id)
            
            logger.info(f"  ✓ Critical alert sent: {scenario['subject']} (ID: {alert_id})")
        
        # Show alert details
        logger.info("\nAlert Details:")
        for alert_id in alert_ids:
            status = service.get_notification_status(alert_id)
            if status:
                logger.info(f"  Alert {alert_id}:")
                logger.info(f"    Priority: {status['priority']}")
                logger.info(f"    Type: {status['notification_type']}")
                logger.info(f"    Status: {status['status']}")
                logger.info(f"    Max Attempts: {status['max_attempts']}")
        
        service.shutdown()


async def demo_delivery_tracking_and_retry():
    """Demonstrate email delivery tracking and retry logic."""
    logger.info("=== Demonstrating Delivery Tracking and Retry Logic ===")
    
    # Use invalid SMTP config to trigger failures for demonstration
    config = NotificationConfig(
        enabled=True,
        recipients=["test@example.com"],
        smtp_server="invalid-smtp-server.example.com",
        smtp_port=587,
        username="test",
        password="test",
        from_email="system@example.com"
    )
    
    with tempfile.TemporaryDirectory() as temp_dir:
        service = EmailNotificationService(
            notification_config=config,
            templates_directory=temp_dir,
            worker_threads=1
        )
        
        logger.info("Sending notification that will fail (for retry demonstration)...")
        
        # Send notification that will fail
        notification_id = await service.send_notification(
            subject="Test Retry Logic",
            html_content="<h1>This will fail and retry</h1>",
            priority=NotificationPriority.HIGH,
            notification_type="test",
            max_attempts=3
        )
        
        logger.info(f"Notification queued: {notification_id}")
        
        # Wait for processing and retries
        logger.info("Waiting for processing and retry attempts...")
        await asyncio.sleep(5)
        
        # Check notification status
        status = service.get_notification_status(notification_id)
        if status:
            logger.info("Notification Status:")
            logger.info(f"  ID: {status['notification_id']}")
            logger.info(f"  Status: {status['status']}")
            logger.info(f"  Attempts: {status['attempts']}/{status['max_attempts']}")
            logger.info(f"  Created: {status['created_at']}")
            logger.info(f"  Last Attempt: {status['last_attempt_at']}")
            logger.info(f"  Error: {status['error_message']}")
        
        # Show delivery statistics
        stats = service.get_delivery_statistics()
        logger.info("\nDelivery Statistics:")
        logger.info(f"  Total Notifications: {stats['total_notifications']}")
        logger.info(f"  Status Breakdown: {stats['status_breakdown']}")
        logger.info(f"  Queue Size: {stats['queue_size']}")
        logger.info(f"  Delivery Stats: {stats['delivery_statistics']}")
        
        service.shutdown()


async def demo_template_notifications():
    """Demonstrate template-based notifications."""
    logger.info("=== Demonstrating Template-Based Notifications ===")
    
    config = demo_smtp_configuration()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        service = EmailNotificationService(
            notification_config=config,
            templates_directory=temp_dir,
            worker_threads=1
        )
        
        # Create custom templates
        templates = {
            'monthly_report.html': '''
<!DOCTYPE html>
<html>
<head>
    <title>Monthly Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }
        .summary { background-color: #f9f9f9; padding: 15px; margin: 10px 0; }
        .metric { display: inline-block; margin: 10px; padding: 10px; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Monthly System Report</h1>
        <p>{{ report_date }}</p>
    </div>
    
    <div class="summary">
        <h2>System Summary</h2>
        <div class="metric">
            <h3>{{ total_papers }}</h3>
            <p>Papers Processed</p>
        </div>
        <div class="metric">
            <h3>{{ success_rate }}%</h3>
            <p>Success Rate</p>
        </div>
        <div class="metric">
            <h3>{{ storage_used }}GB</h3>
            <p>Storage Used</p>
        </div>
    </div>
    
    <h2>Instance Performance</h2>
    {% for instance in instances %}
    <div class="metric">
        <h4>{{ instance.name }}</h4>
        <p>Papers: {{ instance.papers }}</p>
        <p>Errors: {{ instance.errors }}</p>
    </div>
    {% endfor %}
</body>
</html>
            ''',
            
            'system_alert.html': '''
<!DOCTYPE html>
<html>
<head>
    <title>System Alert</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .alert { background-color: #ff9800; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .warning { background-color: #fff3e0; padding: 15px; border-left: 4px solid #ff9800; }
    </style>
</head>
<body>
    <div class="alert">
        <h1>{{ alert_level|upper }} ALERT</h1>
        <p>{{ timestamp }}</p>
    </div>
    
    <div class="content">
        <div class="warning">
            <h2>{{ alert_title }}</h2>
            <p>{{ alert_description }}</p>
            
            {% if metrics %}
            <h3>Current Metrics</h3>
            <ul>
            {% for key, value in metrics.items() %}
                <li><strong>{{ key }}:</strong> {{ value }}</li>
            {% endfor %}
            </ul>
            {% endif %}
        </div>
        
        {% if recommendations %}
        <h3>Recommended Actions</h3>
        <ol>
        {% for action in recommendations %}
            <li>{{ action }}</li>
        {% endfor %}
        </ol>
        {% endif %}
    </div>
</body>
</html>
            '''
        }
        
        # Create template files
        templates_dir = Path(temp_dir)
        for filename, content in templates.items():
            template_file = templates_dir / filename
            with open(template_file, 'w') as f:
                f.write(content.strip())
        
        logger.info("Created custom templates:")
        for filename in templates.keys():
            logger.info(f"  ✓ {filename}")
        
        # Send monthly report notification
        logger.info("\nSending monthly report notification...")
        
        report_id = await service.send_template_notification(
            template_name="monthly_report.html",
            subject="Monthly System Report - October 2025",
            context={
                'report_date': 'October 2025',
                'total_papers': 1250,
                'success_rate': 98.5,
                'storage_used': 45.2,
                'instances': [
                    {'name': 'AI Scholar', 'papers': 750, 'errors': 2},
                    {'name': 'Quant Scholar', 'papers': 500, 'errors': 1}
                ]
            },
            priority=NotificationPriority.NORMAL,
            notification_type="monthly_report"
        )
        
        logger.info(f"  ✓ Monthly report queued: {report_id}")
        
        # Send system alert notification
        logger.info("Sending system alert notification...")
        
        alert_id = await service.send_template_notification(
            template_name="system_alert.html",
            subject="Storage Warning - Action Required",
            context={
                'alert_level': 'warning',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'alert_title': 'Storage Usage High',
                'alert_description': 'System storage usage has reached 85% capacity.',
                'metrics': {
                    'Total Storage': '500 GB',
                    'Used Storage': '425 GB',
                    'Available Storage': '75 GB',
                    'Usage Percentage': '85%'
                },
                'recommendations': [
                    'Review and archive old processed files',
                    'Clean up temporary processing files',
                    'Consider expanding storage capacity',
                    'Monitor storage usage more frequently'
                ]
            },
            priority=NotificationPriority.HIGH,
            notification_type="storage_alert"
        )
        
        logger.info(f"  ✓ System alert queued: {alert_id}")
        
        # Show template rendering results
        await asyncio.sleep(1)
        
        for notification_id in [report_id, alert_id]:
            status = service.get_notification_status(notification_id)
            if status:
                logger.info(f"\nTemplate Notification {notification_id}:")
                logger.info(f"  Subject: {status.get('subject', 'N/A')}")
                logger.info(f"  Priority: {status['priority']}")
                logger.info(f"  Type: {status['notification_type']}")
                logger.info(f"  Recipients: {status['eligible_recipients_count']}")
        
        service.shutdown()


def demo_recipient_management():
    """Demonstrate advanced recipient management features."""
    logger.info("=== Demonstrating Recipient Management ===")
    
    config = demo_smtp_configuration()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        service = EmailNotificationService(
            notification_config=config,
            templates_directory=temp_dir,
            worker_threads=1
        )
        
        logger.info("Initial recipients from configuration:")
        for recipient in service.recipients:
            logger.info(f"  {recipient.email} (threshold: {recipient.priority_threshold.name})")
        
        # Add specialized recipients
        logger.info("\nAdding specialized recipients...")
        
        specialized_recipients = [
            {
                'email': 'security-team@example.com',
                'name': 'Security Team',
                'priority_threshold': NotificationPriority.HIGH,
                'notification_types': ['security_alerts', 'failures']
            },
            {
                'email': 'storage-admin@example.com',
                'name': 'Storage Administrator',
                'priority_threshold': NotificationPriority.NORMAL,
                'notification_types': ['storage_alerts', 'reports']
            },
            {
                'email': 'on-call@example.com',
                'name': 'On-Call Engineer',
                'priority_threshold': NotificationPriority.CRITICAL,
                'notification_types': ['all']
            }
        ]
        
        for recipient_info in specialized_recipients:
            success = service.add_recipient(**recipient_info)
            if success:
                logger.info(f"  ✓ Added {recipient_info['email']}")
        
        # Update recipient preferences
        logger.info("\nUpdating recipient preferences...")
        
        # Disable a recipient temporarily
        service.update_recipient_preferences(
            email='admin@example.com',
            enabled=False
        )
        logger.info("  ✓ Disabled admin@example.com")
        
        # Change priority threshold
        service.update_recipient_preferences(
            email='ops@example.com',
            priority_threshold=NotificationPriority.HIGH,
            notification_types=['alerts', 'failures']
        )
        logger.info("  ✓ Updated ops@example.com preferences")
        
        # Show final recipient configuration
        logger.info("\nFinal recipient configuration:")
        for recipient in service.recipients:
            status = "ENABLED" if recipient.enabled else "DISABLED"
            logger.info(f"  {recipient.email} ({status}):")
            logger.info(f"    Name: {recipient.name or 'N/A'}")
            logger.info(f"    Priority Threshold: {recipient.priority_threshold.name}")
            logger.info(f"    Notification Types: {', '.join(recipient.notification_types)}")
        
        # Test configuration
        logger.info("\nTesting email configuration...")
        test_results = service.test_email_configuration()
        
        logger.info("Test Results:")
        logger.info(f"  Total Recipients: {test_results['total_recipients']}")
        logger.info(f"  Active Recipients: {test_results['active_recipients']}")
        logger.info(f"  Test Attempts: {len(test_results['test_results'])}")
        
        for result in test_results['test_results']:
            status = "✓ SUCCESS" if result['success'] else "❌ FAILED"
            logger.info(f"    {result['recipient']}: {status}")
            if not result['success']:
                logger.info(f"      Error: {result['message']}")
        
        service.shutdown()


async def demo_comprehensive_statistics():
    """Demonstrate comprehensive delivery statistics and monitoring."""
    logger.info("=== Demonstrating Delivery Statistics and Monitoring ===")
    
    config = demo_smtp_configuration()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        service = EmailNotificationService(
            notification_config=config,
            templates_directory=temp_dir,
            worker_threads=2
        )
        
        # Send various notifications to generate statistics
        logger.info("Sending various notifications to generate statistics...")
        
        notification_scenarios = [
            ("Normal Report", NotificationPriority.NORMAL, "reports"),
            ("High Priority Alert", NotificationPriority.HIGH, "alerts"), 
            ("Critical System Failure", NotificationPriority.CRITICAL, "failures"),
            ("Low Priority Info", NotificationPriority.LOW, "info"),
            ("Another Report", NotificationPriority.NORMAL, "reports")
        ]
        
        notification_ids = []
        for subject, priority, notification_type in notification_scenarios:
            notification_id = await service.send_notification(
                subject=subject,
                html_content=f"<h1>{subject}</h1><p>This is a {priority.name} priority {notification_type} notification.</p>",
                priority=priority,
                notification_type=notification_type
            )
            notification_ids.append(notification_id)
            logger.info(f"  ✓ Queued: {subject} (ID: {notification_id})")
        
        # Wait for processing
        await asyncio.sleep(3)
        
        # Get comprehensive statistics
        stats = service.get_delivery_statistics()
        
        logger.info("\nDelivery Statistics:")
        logger.info(f"  Total Notifications: {stats['total_notifications']}")
        logger.info(f"  Recent Notifications (24h): {stats['recent_notifications_24h']}")
        logger.info(f"  Current Queue Size: {stats['queue_size']}")
        logger.info(f"  Active Recipients: {stats['active_recipients']}/{stats['recipients_count']}")
        
        logger.info("\nStatus Breakdown:")
        for status, count in stats['status_breakdown'].items():
            logger.info(f"  {status.upper()}: {count}")
        
        logger.info("\nDelivery Performance:")
        delivery_stats = stats['delivery_statistics']
        logger.info(f"  Total Sent: {delivery_stats['total_sent']}")
        logger.info(f"  Total Failed: {delivery_stats['total_failed']}")
        logger.info(f"  Total Retries: {delivery_stats['total_retries']}")
        
        logger.info("\nConfiguration:")
        config_info = stats['configuration']
        logger.info(f"  Enabled: {config_info['enabled']}")
        logger.info(f"  SMTP Server: {config_info['smtp_server']}:{config_info['smtp_port']}")
        logger.info(f"  Rate Limit: {config_info['rate_limit_delay']} seconds")
        logger.info(f"  Worker Threads: {config_info['worker_threads']}")
        
        # Show individual notification statuses
        logger.info("\nIndividual Notification Status:")
        for notification_id in notification_ids:
            status = service.get_notification_status(notification_id)
            if status:
                logger.info(f"  {notification_id}:")
                logger.info(f"    Priority: {status['priority']}")
                logger.info(f"    Status: {status['status']}")
                logger.info(f"    Attempts: {status['attempts']}")
        
        service.shutdown()


async def main():
    """Run all email notification service demonstrations."""
    logger.info("🚀 Starting Task 6.2 Email Notification Service Demonstration")
    logger.info("=" * 80)
    
    try:
        # Demonstrate SMTP configuration
        demo_smtp_configuration()
        
        # Demonstrate multiple recipients and priorities
        demo_multiple_recipients_and_priorities()
        
        # Demonstrate immediate alert system
        await demo_immediate_alert_system()
        
        # Demonstrate delivery tracking and retry logic
        await demo_delivery_tracking_and_retry()
        
        # Demonstrate template notifications
        await demo_template_notifications()
        
        # Demonstrate recipient management
        demo_recipient_management()
        
        # Demonstrate comprehensive statistics
        await demo_comprehensive_statistics()
        
        logger.info("=" * 80)
        logger.info("✅ Task 6.2 Implementation Demonstration Complete!")
        logger.info("")
        logger.info("📋 Summary of Implemented Components:")
        logger.info("  ✓ EmailNotificationService - SMTP configuration and management")
        logger.info("  ✓ Multiple Recipients - Priority-based filtering and preferences")
        logger.info("  ✓ Priority Levels - LOW, NORMAL, HIGH, CRITICAL with filtering")
        logger.info("  ✓ Immediate Alert System - Critical failure notifications")
        logger.info("  ✓ Delivery Tracking - Comprehensive status and history tracking")
        logger.info("  ✓ Retry Logic - Exponential backoff with configurable attempts")
        logger.info("  ✓ Template System - Jinja2-based HTML email templates")
        logger.info("  ✓ Recipient Management - Add, remove, update preferences")
        logger.info("  ✓ Statistics and Monitoring - Comprehensive delivery metrics")
        logger.info("")
        logger.info("🎯 Requirements Satisfied:")
        logger.info("  ✓ 7.3 - EmailNotificationService with SMTP configuration")
        logger.info("  ✓ 7.4 - Support for multiple recipients and priority levels")
        logger.info("  ✓ 7.6 - Immediate alert system for critical failures")
        logger.info("  ✓ 5.7 - Email delivery tracking and retry logic")
        logger.info("")
        logger.info("🔧 Key Features:")
        logger.info("  • Multi-threaded email processing with priority queues")
        logger.info("  • Recipient filtering based on priority thresholds and types")
        logger.info("  • Exponential backoff retry logic with configurable attempts")
        logger.info("  • Template-based notifications with Jinja2 rendering")
        logger.info("  • Comprehensive delivery tracking and statistics")
        logger.info("  • Rate limiting and SMTP connection management")
        logger.info("  • Graceful shutdown and error handling")
        logger.info("  • Configuration testing and validation")
        
        return True
        
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)