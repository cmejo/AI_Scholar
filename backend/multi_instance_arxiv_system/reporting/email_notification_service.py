#!/usr/bin/env python3
"""
Enhanced Email Notification Service for multi-instance ArXiv system.

Implements EmailNotificationService with SMTP configuration, multiple recipients,
priority levels, immediate alert system, and email delivery tracking with retry logic.
"""

import asyncio
import logging
import sys
import smtplib
import ssl
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import jinja2
import threading
from queue import Queue, PriorityQueue
import hashlib

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from ..shared.multi_instance_data_models import NotificationConfig

logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class NotificationStatus(Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class EmailRecipient:
    """Email recipient with priority and preferences."""
    email: str
    name: Optional[str] = None
    priority_threshold: NotificationPriority = NotificationPriority.NORMAL
    enabled: bool = True
    notification_types: List[str] = field(default_factory=lambda: ["all"])
    
    def should_receive(self, notification_priority: NotificationPriority, 
                      notification_type: str) -> bool:
        """Check if recipient should receive this notification."""
        if not self.enabled:
            return False
        
        # Check priority threshold
        if notification_priority.value < self.priority_threshold.value:
            return False
        
        # Check notification types
        if "all" not in self.notification_types and notification_type not in self.notification_types:
            return False
        
        return True


@dataclass
class EmailNotification:
    """Email notification with tracking and retry logic."""
    notification_id: str
    subject: str
    html_content: str
    text_content: str
    recipients: List[EmailRecipient]
    priority: NotificationPriority
    notification_type: str
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    status: NotificationStatus = NotificationStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    last_attempt_at: Optional[datetime] = None
    error_message: Optional[str] = None
    delivery_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def __lt__(self, other):
        """For priority queue ordering."""
        return self.priority.value > other.priority.value
    
    def should_retry(self) -> bool:
        """Check if notification should be retried."""
        if self.status != NotificationStatus.FAILED:
            return False
        
        if self.attempts >= self.max_attempts:
            return False
        
        # Exponential backoff
        if self.last_attempt_at:
            backoff_minutes = 2 ** (self.attempts - 1)  # 1, 2, 4, 8 minutes
            next_attempt = self.last_attempt_at + timedelta(minutes=backoff_minutes)
            return datetime.now() >= next_attempt
        
        return True
    
    def get_eligible_recipients(self) -> List[EmailRecipient]:
        """Get recipients eligible for this notification."""
        return [
            recipient for recipient in self.recipients
            if recipient.should_receive(self.priority, self.notification_type)
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'notification_id': self.notification_id,
            'subject': self.subject,
            'priority': self.priority.name,
            'notification_type': self.notification_type,
            'created_at': self.created_at.isoformat(),
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'status': self.status.value,
            'attempts': self.attempts,
            'max_attempts': self.max_attempts,
            'last_attempt_at': self.last_attempt_at.isoformat() if self.last_attempt_at else None,
            'error_message': self.error_message,
            'delivery_results': self.delivery_results,
            'recipients_count': len(self.recipients),
            'eligible_recipients_count': len(self.get_eligible_recipients())
        }


@dataclass
class DeliveryResult:
    """Result of email delivery attempt."""
    recipient_email: str
    success: bool
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    smtp_response: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'recipient_email': self.recipient_email,
            'success': self.success,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'smtp_response': self.smtp_response
        }


class EmailNotificationService:
    """Enhanced email notification service with priority handling and retry logic."""
    
    def __init__(self, 
                 notification_config: NotificationConfig,
                 templates_directory: Optional[str] = None,
                 max_queue_size: int = 1000,
                 worker_threads: int = 2):
        """
        Initialize email notification service.
        
        Args:
            notification_config: Email configuration
            templates_directory: Directory containing email templates
            max_queue_size: Maximum size of notification queue
            worker_threads: Number of worker threads for sending emails
        """
        self.config = notification_config
        self.templates_directory = Path(templates_directory or 
                                       Path(__file__).parent / "templates")
        self.templates_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_directory)),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Notification queue and tracking
        self.notification_queue = PriorityQueue(maxsize=max_queue_size)
        self.notification_history: Dict[str, EmailNotification] = {}
        self.delivery_statistics: Dict[str, Any] = {
            'total_sent': 0,
            'total_failed': 0,
            'total_retries': 0,
            'last_reset': datetime.now()
        }
        
        # Recipients management
        self.recipients: List[EmailRecipient] = []
        self._load_recipients_from_config()
        
        # Worker threads for processing notifications
        self.worker_threads = worker_threads
        self.workers: List[threading.Thread] = []
        self.shutdown_event = threading.Event()
        
        # Rate limiting
        self.rate_limit_delay = 1.0  # seconds between emails
        self.last_send_time = 0
        
        # Create default templates
        self._create_default_templates()
        
        # Start worker threads
        self._start_workers()
        
        logger.info(f"EmailNotificationService initialized with {len(self.recipients)} recipients")
    
    def _load_recipients_from_config(self) -> None:
        """Load recipients from notification configuration."""
        self.recipients = []
        
        for email in self.config.recipients:
            recipient = EmailRecipient(
                email=email,
                priority_threshold=NotificationPriority.NORMAL,
                enabled=True,
                notification_types=["all"]
            )
            self.recipients.append(recipient)
    
    def add_recipient(self, 
                     email: str,
                     name: Optional[str] = None,
                     priority_threshold: NotificationPriority = NotificationPriority.NORMAL,
                     notification_types: List[str] = None) -> bool:
        """
        Add a new email recipient.
        
        Args:
            email: Recipient email address
            name: Optional recipient name
            priority_threshold: Minimum priority level for notifications
            notification_types: Types of notifications to receive
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            # Check if recipient already exists
            for recipient in self.recipients:
                if recipient.email == email:
                    logger.warning(f"Recipient {email} already exists")
                    return False
            
            recipient = EmailRecipient(
                email=email,
                name=name,
                priority_threshold=priority_threshold,
                enabled=True,
                notification_types=notification_types or ["all"]
            )
            
            self.recipients.append(recipient)
            logger.info(f"Added recipient: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add recipient {email}: {e}")
            return False
    
    def remove_recipient(self, email: str) -> bool:
        """
        Remove an email recipient.
        
        Args:
            email: Recipient email address to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        try:
            for i, recipient in enumerate(self.recipients):
                if recipient.email == email:
                    del self.recipients[i]
                    logger.info(f"Removed recipient: {email}")
                    return True
            
            logger.warning(f"Recipient {email} not found")
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove recipient {email}: {e}")
            return False
    
    def update_recipient_preferences(self, 
                                   email: str,
                                   priority_threshold: Optional[NotificationPriority] = None,
                                   notification_types: Optional[List[str]] = None,
                                   enabled: Optional[bool] = None) -> bool:
        """
        Update recipient preferences.
        
        Args:
            email: Recipient email address
            priority_threshold: New priority threshold
            notification_types: New notification types
            enabled: Enable/disable recipient
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            for recipient in self.recipients:
                if recipient.email == email:
                    if priority_threshold is not None:
                        recipient.priority_threshold = priority_threshold
                    if notification_types is not None:
                        recipient.notification_types = notification_types
                    if enabled is not None:
                        recipient.enabled = enabled
                    
                    logger.info(f"Updated preferences for recipient: {email}")
                    return True
            
            logger.warning(f"Recipient {email} not found")
            return False
            
        except Exception as e:
            logger.error(f"Failed to update recipient {email}: {e}")
            return False
    
    async def send_notification(self,
                              subject: str,
                              html_content: str,
                              text_content: Optional[str] = None,
                              priority: NotificationPriority = NotificationPriority.NORMAL,
                              notification_type: str = "general",
                              scheduled_at: Optional[datetime] = None,
                              max_attempts: int = 3) -> str:
        """
        Send email notification with priority handling.
        
        Args:
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)
            priority: Notification priority level
            notification_type: Type of notification
            scheduled_at: Optional scheduled delivery time
            max_attempts: Maximum retry attempts
            
        Returns:
            Notification ID for tracking
        """
        try:
            # Generate notification ID
            notification_id = self._generate_notification_id(subject, html_content)
            
            # Create text content if not provided
            if text_content is None:
                text_content = self._html_to_text(html_content)
            
            # Create notification
            notification = EmailNotification(
                notification_id=notification_id,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                recipients=self.recipients.copy(),
                priority=priority,
                notification_type=notification_type,
                scheduled_at=scheduled_at,
                max_attempts=max_attempts
            )
            
            # Add to queue
            if scheduled_at and scheduled_at > datetime.now():
                # Schedule for later
                notification.status = NotificationStatus.PENDING
            else:
                # Send immediately
                notification.scheduled_at = datetime.now()
            
            self.notification_queue.put(notification)
            self.notification_history[notification_id] = notification
            
            logger.info(f"Queued notification {notification_id} with priority {priority.name}")
            return notification_id
            
        except Exception as e:
            logger.error(f"Failed to queue notification: {e}")
            raise
    
    async def send_template_notification(self,
                                       template_name: str,
                                       subject: str,
                                       context: Dict[str, Any],
                                       priority: NotificationPriority = NotificationPriority.NORMAL,
                                       notification_type: str = "general",
                                       scheduled_at: Optional[datetime] = None) -> str:
        """
        Send notification using template.
        
        Args:
            template_name: Name of the template file
            subject: Email subject
            context: Template context variables
            priority: Notification priority level
            notification_type: Type of notification
            scheduled_at: Optional scheduled delivery time
            
        Returns:
            Notification ID for tracking
        """
        try:
            # Load and render template
            template = self.jinja_env.get_template(template_name)
            html_content = template.render(**context)
            
            # Send notification
            return await self.send_notification(
                subject=subject,
                html_content=html_content,
                priority=priority,
                notification_type=notification_type,
                scheduled_at=scheduled_at
            )
            
        except Exception as e:
            logger.error(f"Failed to send template notification: {e}")
            raise
    
    async def send_immediate_alert(self,
                                 subject: str,
                                 message: str,
                                 alert_type: str = "critical_failure") -> str:
        """
        Send immediate critical alert notification.
        
        Args:
            subject: Alert subject
            message: Alert message
            alert_type: Type of alert
            
        Returns:
            Notification ID for tracking
        """
        try:
            # Create simple HTML content for alert
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="background-color: #f44336; color: white; padding: 20px; text-align: center;">
                    <h1>CRITICAL ALERT</h1>
                    <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                <div style="padding: 20px;">
                    <h2>{subject}</h2>
                    <p>{message}</p>
                    <p><strong>Alert Type:</strong> {alert_type}</p>
                    <p><strong>Immediate Action Required</strong></p>
                </div>
                <div style="background-color: #f5f5f5; padding: 10px; font-size: 12px;">
                    <p>This is an automated critical alert from the Multi-Instance ArXiv System.</p>
                </div>
            </body>
            </html>
            """
            
            # Send with critical priority
            return await self.send_notification(
                subject=f"[CRITICAL ALERT] {subject}",
                html_content=html_content,
                priority=NotificationPriority.CRITICAL,
                notification_type=alert_type,
                max_attempts=5  # More retries for critical alerts
            )
            
        except Exception as e:
            logger.error(f"Failed to send immediate alert: {e}")
            raise
    
    def _start_workers(self) -> None:
        """Start worker threads for processing notifications."""
        for i in range(self.worker_threads):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"EmailWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Started {self.worker_threads} email worker threads")
    
    def _worker_loop(self) -> None:
        """Main worker loop for processing notifications."""
        while not self.shutdown_event.is_set():
            try:
                # Get notification from queue (with timeout)
                try:
                    notification = self.notification_queue.get(timeout=1.0)
                except:
                    continue
                
                # Check if notification should be processed now
                if notification.scheduled_at and notification.scheduled_at > datetime.now():
                    # Put back in queue for later
                    self.notification_queue.put(notification)
                    time.sleep(1)
                    continue
                
                # Process notification
                self._process_notification(notification)
                
                # Mark task as done
                self.notification_queue.task_done()
                
            except Exception as e:
                logger.error(f"Worker error: {e}")
                time.sleep(1)
    
    def _process_notification(self, notification: EmailNotification) -> None:
        """Process a single notification."""
        try:
            notification.status = NotificationStatus.SENDING
            notification.attempts += 1
            notification.last_attempt_at = datetime.now()
            
            # Get eligible recipients
            eligible_recipients = notification.get_eligible_recipients()
            
            if not eligible_recipients:
                notification.status = NotificationStatus.FAILED
                notification.error_message = "No eligible recipients"
                logger.warning(f"No eligible recipients for notification {notification.notification_id}")
                return
            
            # Rate limiting
            self._apply_rate_limit()
            
            # Send to each eligible recipient
            success_count = 0
            for recipient in eligible_recipients:
                try:
                    result = self._send_to_recipient(notification, recipient)
                    notification.delivery_results[recipient.email] = result.to_dict()
                    
                    if result.success:
                        success_count += 1
                        self.delivery_statistics['total_sent'] += 1
                    else:
                        self.delivery_statistics['total_failed'] += 1
                        
                except Exception as e:
                    logger.error(f"Failed to send to {recipient.email}: {e}")
                    notification.delivery_results[recipient.email] = DeliveryResult(
                        recipient_email=recipient.email,
                        success=False,
                        message=str(e)
                    ).to_dict()
                    self.delivery_statistics['total_failed'] += 1
            
            # Update notification status
            if success_count > 0:
                notification.status = NotificationStatus.SENT
                logger.info(f"Notification {notification.notification_id} sent to {success_count}/{len(eligible_recipients)} recipients")
            else:
                notification.status = NotificationStatus.FAILED
                notification.error_message = "Failed to send to all recipients"
                
                # Queue for retry if applicable
                if notification.should_retry():
                    notification.status = NotificationStatus.RETRYING
                    self.notification_queue.put(notification)
                    self.delivery_statistics['total_retries'] += 1
                    logger.info(f"Queued notification {notification.notification_id} for retry (attempt {notification.attempts + 1})")
                
        except Exception as e:
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(e)
            logger.error(f"Failed to process notification {notification.notification_id}: {e}")
    
    def _send_to_recipient(self, notification: EmailNotification, recipient: EmailRecipient) -> DeliveryResult:
        """Send notification to a specific recipient."""
        try:
            # Create email message
            message = MIMEMultipart("alternative")
            message["Subject"] = notification.subject
            message["From"] = self.config.from_email
            message["To"] = recipient.email
            
            if recipient.name:
                message["To"] = f"{recipient.name} <{recipient.email}>"
            
            # Add priority headers
            if notification.priority == NotificationPriority.CRITICAL:
                message["X-Priority"] = "1"
                message["Importance"] = "high"
            elif notification.priority == NotificationPriority.HIGH:
                message["X-Priority"] = "2"
                message["Importance"] = "high"
            
            # Add notification type header
            message["X-Notification-Type"] = notification.notification_type
            message["X-Notification-ID"] = notification.notification_id
            
            # Add text and HTML parts
            text_part = MIMEText(notification.text_content, "plain")
            html_part = MIMEText(notification.html_content, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            smtp_response = self._send_email_smtp(message, recipient.email)
            
            return DeliveryResult(
                recipient_email=recipient.email,
                success=True,
                message="Email sent successfully",
                smtp_response=smtp_response
            )
            
        except Exception as e:
            return DeliveryResult(
                recipient_email=recipient.email,
                success=False,
                message=str(e)
            )
    
    def _send_email_smtp(self, message: MIMEMultipart, recipient_email: str) -> str:
        """Send email using SMTP and return response."""
        try:
            # Create SMTP connection
            if self.config.smtp_port == 465:
                # SSL connection
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.config.smtp_server, self.config.smtp_port, context=context)
            else:
                # TLS connection
                server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
                server.starttls()
            
            # Login if credentials provided
            if self.config.username and self.config.password:
                server.login(self.config.username, self.config.password)
            
            # Send email
            response = server.send_message(message, to_addrs=[recipient_email])
            server.quit()
            
            return str(response)
            
        except Exception as e:
            logger.error(f"SMTP error sending to {recipient_email}: {e}")
            raise
    
    def _apply_rate_limit(self) -> None:
        """Apply rate limiting between email sends."""
        current_time = time.time()
        time_since_last = current_time - self.last_send_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_send_time = time.time()
    
    def _generate_notification_id(self, subject: str, content: str) -> str:
        """Generate unique notification ID."""
        timestamp = datetime.now().isoformat()
        content_hash = hashlib.md5(f"{subject}{content}{timestamp}".encode()).hexdigest()[:8]
        return f"notif_{int(time.time())}_{content_hash}"
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML content to plain text."""
        try:
            import re
            
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', html_content)
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            return text
            
        except Exception:
            return "Plain text version not available"
    
    def _create_default_templates(self) -> None:
        """Create default email templates."""
        templates = {
            'critical_alert.html': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Critical Alert</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
        .header { background-color: #f44336; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .alert { background-color: #ffebee; padding: 15px; margin: 10px 0; border-left: 4px solid #f44336; }
        .footer { margin-top: 20px; padding: 10px; background-color: #f5f5f5; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>CRITICAL ALERT</h1>
        <p>{{ timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</p>
    </div>
    
    <div class="content">
        <div class="alert">
            <h2>{{ alert_title }}</h2>
            <p>{{ alert_message }}</p>
            <p><strong>Alert Type:</strong> {{ alert_type }}</p>
            <p><strong>Severity:</strong> Critical</p>
        </div>
        
        {% if details %}
        <h3>Details</h3>
        <pre>{{ details }}</pre>
        {% endif %}
        
        {% if recommended_actions %}
        <h3>Recommended Actions</h3>
        <ul>
        {% for action in recommended_actions %}
            <li>{{ action }}</li>
        {% endfor %}
        </ul>
        {% endif %}
    </div>
    
    <div class="footer">
        <p>This is an automated critical alert from the Multi-Instance ArXiv System.</p>
        <p>Immediate action required.</p>
    </div>
</body>
</html>
            '''
        }
        
        # Create template files
        for filename, content in templates.items():
            template_file = self.templates_directory / filename
            if not template_file.exists():
                with open(template_file, 'w') as f:
                    f.write(content.strip())
                logger.info(f"Created default template: {filename}")
    
    def get_notification_status(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific notification."""
        notification = self.notification_history.get(notification_id)
        if notification:
            return notification.to_dict()
        return None
    
    def get_delivery_statistics(self) -> Dict[str, Any]:
        """Get email delivery statistics."""
        total_notifications = len(self.notification_history)
        
        # Count by status
        status_counts = {}
        for notification in self.notification_history.values():
            status = notification.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Recent notifications (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_notifications = [
            n for n in self.notification_history.values()
            if n.created_at > recent_cutoff
        ]
        
        return {
            'total_notifications': total_notifications,
            'status_breakdown': status_counts,
            'recent_notifications_24h': len(recent_notifications),
            'delivery_statistics': self.delivery_statistics.copy(),
            'queue_size': self.notification_queue.qsize(),
            'recipients_count': len(self.recipients),
            'active_recipients': len([r for r in self.recipients if r.enabled]),
            'configuration': {
                'enabled': self.config.enabled,
                'smtp_server': self.config.smtp_server,
                'smtp_port': self.config.smtp_port,
                'rate_limit_delay': self.rate_limit_delay,
                'worker_threads': self.worker_threads
            }
        }
    
    def test_email_configuration(self) -> Dict[str, Any]:
        """Test email configuration by sending test emails."""
        results = []
        
        for recipient in self.recipients:
            if not recipient.enabled:
                continue
                
            try:
                # Create test message
                message = MIMEText(f"This is a test email from the Multi-Instance ArXiv System.\n\nSent at: {datetime.now()}")
                message["Subject"] = "[Multi-Instance ArXiv] Email Configuration Test"
                message["From"] = self.config.from_email
                message["To"] = recipient.email
                
                # Send test email
                smtp_response = self._send_email_smtp(message, recipient.email)
                
                results.append({
                    'recipient': recipient.email,
                    'success': True,
                    'message': 'Test email sent successfully',
                    'smtp_response': smtp_response
                })
                
            except Exception as e:
                results.append({
                    'recipient': recipient.email,
                    'success': False,
                    'message': str(e)
                })
        
        return {
            'test_results': results,
            'total_recipients': len(self.recipients),
            'active_recipients': len([r for r in self.recipients if r.enabled]),
            'successful_sends': len([r for r in results if r['success']]),
            'failed_sends': len([r for r in results if not r['success']])
        }
    
    def shutdown(self) -> None:
        """Shutdown the notification service gracefully."""
        logger.info("Shutting down EmailNotificationService...")
        
        # Signal workers to stop
        self.shutdown_event.set()
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5.0)
        
        # Process remaining notifications in queue
        remaining_notifications = []
        while not self.notification_queue.empty():
            try:
                notification = self.notification_queue.get_nowait()
                remaining_notifications.append(notification)
            except:
                break
        
        if remaining_notifications:
            logger.warning(f"Shutdown with {len(remaining_notifications)} notifications still in queue")
        
        logger.info("EmailNotificationService shutdown complete")
    
    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.shutdown()
        except:
            pass