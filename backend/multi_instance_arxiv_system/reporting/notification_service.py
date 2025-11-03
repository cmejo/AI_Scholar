"""
Notification Service for multi-instance ArXiv system.

Provides automated email notifications for update completion,
error summaries, and storage monitoring alerts.
"""

import asyncio
import logging
import sys
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import json
import jinja2

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from .update_reporter import ComprehensiveUpdateReport, StorageRecommendation
from ..shared.multi_instance_data_models import NotificationConfig

logger = logging.getLogger(__name__)


@dataclass
class NotificationTemplate:
    """Email notification template."""
    template_name: str
    subject_template: str
    html_template: str
    text_template: str
    priority: str = "normal"  # "low", "normal", "high", "critical"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'template_name': self.template_name,
            'subject_template': self.subject_template,
            'html_template': self.html_template,
            'text_template': self.text_template,
            'priority': self.priority
        }


@dataclass
class NotificationResult:
    """Result of notification sending attempt."""
    success: bool
    message: str
    recipients_sent: List[str] = field(default_factory=list)
    recipients_failed: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'success': self.success,
            'message': self.message,
            'recipients_sent': self.recipients_sent,
            'recipients_failed': self.recipients_failed,
            'timestamp': self.timestamp.isoformat()
        }


class NotificationService:
    """Handles email notifications for the multi-instance system."""
    
    def __init__(self, 
                 notification_config: NotificationConfig,
                 templates_directory: str = None):
        """
        Initialize notification service.
        
        Args:
            notification_config: Email configuration
            templates_directory: Directory containing email templates
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
        
        # Notification history
        self.notification_history: List[NotificationResult] = []
        
        # Create default templates if they don't exist
        self._create_default_templates()
        
        logger.info("NotificationService initialized")
    
    def _create_default_templates(self) -> None:
        """Create default email templates if they don't exist."""
        templates = {
            'update_success.html': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Monthly Update Completed Successfully</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .summary { background-color: #f9f9f9; padding: 15px; margin: 10px 0; border-left: 4px solid #4CAF50; }
        .instance { margin: 10px 0; padding: 10px; border: 1px solid #ddd; }
        .success { color: #4CAF50; }
        .warning { color: #ff9800; }
        .error { color: #f44336; }
        .footer { margin-top: 20px; padding: 10px; background-color: #f5f5f5; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Monthly Update Completed Successfully</h1>
        <p>{{ report.generated_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
    </div>
    
    <div class="content">
        <div class="summary">
            <h2>System Summary</h2>
            <p><strong>Total Instances:</strong> {{ report.system_summary.total_instances }}</p>
            <p><strong>Success Rate:</strong> <span class="success">{{ "%.1f"|format(report.system_summary.success_rate) }}%</span></p>
            <p><strong>Papers Processed:</strong> {{ report.system_summary.total_papers_processed }}</p>
            <p><strong>Total Processing Time:</strong> {{ "%.1f"|format(report.system_summary.total_processing_time_hours) }} hours</p>
            <p><strong>Storage Used:</strong> {{ "%.1f"|format(report.system_summary.total_storage_used_gb) }} GB</p>
        </div>
        
        <h2>Instance Details</h2>
        {% for instance_name, instance_report in report.instance_reports.items() %}
        <div class="instance">
            <h3>{{ instance_name }}</h3>
            <p><strong>Papers Processed:</strong> {{ instance_report.papers_processed }}</p>
            <p><strong>Processing Time:</strong> {{ "%.1f"|format(instance_report.processing_time_seconds / 3600) }} hours</p>
            <p><strong>Errors:</strong> 
                {% if instance_report.errors|length == 0 %}
                    <span class="success">None</span>
                {% else %}
                    <span class="error">{{ instance_report.errors|length }}</span>
                {% endif %}
            </p>
            <p><strong>Storage Used:</strong> {{ "%.1f"|format(instance_report.storage_used_mb / 1024) }} GB</p>
        </div>
        {% endfor %}
        
        {% if report.storage_recommendations %}
        <h2>Storage Recommendations</h2>
        {% for recommendation in report.storage_recommendations %}
        <div class="instance">
            <h4>{{ recommendation.recommendation_type|title }} - {{ recommendation.priority|title }} Priority</h4>
            <p>{{ recommendation.description }}</p>
            {% if recommendation.estimated_space_savings_gb > 0 %}
            <p><strong>Estimated Savings:</strong> {{ "%.1f"|format(recommendation.estimated_space_savings_gb) }} GB</p>
            {% endif %}
        </div>
        {% endfor %}
        {% endif %}
    </div>
    
    <div class="footer">
        <p>This is an automated notification from the Multi-Instance ArXiv System.</p>
        <p>Report ID: {{ report.report_id }}</p>
    </div>
</body>
</html>
            ''',
            
            'update_failure.html': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Monthly Update Failed</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f44336; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .summary { background-color: #ffebee; padding: 15px; margin: 10px 0; border-left: 4px solid #f44336; }
        .error { color: #f44336; }
        .warning { color: #ff9800; }
        .footer { margin-top: 20px; padding: 10px; background-color: #f5f5f5; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Monthly Update Failed</h1>
        <p>{{ timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</p>
    </div>
    
    <div class="content">
        <div class="summary">
            <h2>Failure Summary</h2>
            <p><strong>Error Message:</strong> <span class="error">{{ error_message }}</span></p>
            <p><strong>Failed Instances:</strong> {{ failed_instances|length }}</p>
            <p><strong>Successful Instances:</strong> {{ successful_instances|length }}</p>
        </div>
        
        {% if failed_instances %}
        <h2>Failed Instances</h2>
        {% for instance in failed_instances %}
        <div class="instance">
            <h3>{{ instance }}</h3>
            <p class="error">Update failed for this instance</p>
        </div>
        {% endfor %}
        {% endif %}
        
        {% if error_details %}
        <h2>Error Details</h2>
        <pre>{{ error_details }}</pre>
        {% endif %}
        
        <h2>Recommended Actions</h2>
        <ul>
            <li>Check system logs for detailed error information</li>
            <li>Verify system resources (disk space, memory)</li>
            <li>Run health check to identify issues</li>
            <li>Consider manual intervention if problems persist</li>
        </ul>
    </div>
    
    <div class="footer">
        <p>This is an automated notification from the Multi-Instance ArXiv System.</p>
        <p>Please investigate and resolve the issues as soon as possible.</p>
    </div>
</body>
</html>
            ''',
            
            'storage_alert.html': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Storage Alert</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #ff9800; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .alert { background-color: #fff3e0; padding: 15px; margin: 10px 0; border-left: 4px solid #ff9800; }
        .critical { background-color: #ffebee; border-left-color: #f44336; }
        .footer { margin-top: 20px; padding: 10px; background-color: #f5f5f5; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Storage Alert</h1>
        <p>{{ timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</p>
    </div>
    
    <div class="content">
        <div class="alert {% if alert_level == 'critical' %}critical{% endif %}">
            <h2>{{ alert_level|title }} Storage Alert</h2>
            <p><strong>Total Storage Used:</strong> {{ "%.1f"|format(total_storage_gb) }} GB</p>
            <p><strong>Alert Threshold:</strong> {{ threshold }}%</p>
            <p><strong>Current Usage:</strong> {{ "%.1f"|format(usage_percentage) }}%</p>
        </div>
        
        {% if recommendations %}
        <h2>Immediate Actions Required</h2>
        {% for recommendation in recommendations %}
        <div class="alert">
            <h3>{{ recommendation.description }}</h3>
            <p><strong>Priority:</strong> {{ recommendation.priority|title }}</p>
            <p><strong>Estimated Savings:</strong> {{ "%.1f"|format(recommendation.estimated_space_savings_gb) }} GB</p>
            {% if recommendation.commands %}
            <p><strong>Commands to run:</strong></p>
            <ul>
            {% for command in recommendation.commands %}
                <li><code>{{ command }}</code></li>
            {% endfor %}
            </ul>
            {% endif %}
        </div>
        {% endfor %}
        {% endif %}
    </div>
    
    <div class="footer">
        <p>This is an automated storage alert from the Multi-Instance ArXiv System.</p>
        <p>Please take immediate action to prevent system disruption.</p>
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
    
    async def send_update_completion_notification(self, 
                                                report: ComprehensiveUpdateReport) -> NotificationResult:
        """Send notification for completed update."""
        if not self.config.enabled:
            return NotificationResult(
                success=False,
                message="Notifications disabled in configuration"
            )
        
        try:
            # Determine if update was successful
            success_rate = report.system_summary.success_rate
            template_name = "update_success.html" if success_rate >= 75 else "update_failure.html"
            
            # Prepare template context
            context = {
                'report': report,
                'timestamp': datetime.now(),
                'success_rate': success_rate
            }
            
            # Generate subject
            if success_rate >= 75:
                subject = f"Monthly Update Completed Successfully - {success_rate:.1f}% Success Rate"
            else:
                subject = f"Monthly Update Issues Detected - {success_rate:.1f}% Success Rate"
            
            # Send notification
            result = await self._send_notification(
                template_name=template_name,
                subject=subject,
                context=context,
                priority="high" if success_rate < 75 else "normal"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send update completion notification: {e}")
            return NotificationResult(
                success=False,
                message=f"Failed to send notification: {e}"
            )
    
    async def send_error_summary_notification(self, 
                                            error_analysis: Dict[str, Any],
                                            instance_reports: Dict[str, Any]) -> NotificationResult:
        """Send notification for error summary."""
        if not self.config.enabled:
            return NotificationResult(
                success=False,
                message="Notifications disabled in configuration"
            )
        
        try:
            # Only send if there are significant errors
            total_errors = error_analysis.get('total_errors', 0)
            critical_errors = len(error_analysis.get('critical_errors', []))
            
            if total_errors == 0:
                return NotificationResult(
                    success=True,
                    message="No errors to report"
                )
            
            # Prepare template context
            context = {
                'error_analysis': error_analysis,
                'instance_reports': instance_reports,
                'timestamp': datetime.now(),
                'total_errors': total_errors,
                'critical_errors': critical_errors
            }
            
            # Generate subject
            subject = f"Error Summary Report - {total_errors} Errors Detected"
            if critical_errors > 0:
                subject += f" ({critical_errors} Critical)"
            
            # Use failure template for error notifications
            result = await self._send_notification(
                template_name="update_failure.html",
                subject=subject,
                context=context,
                priority="high" if critical_errors > 0 else "normal"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send error summary notification: {e}")
            return NotificationResult(
                success=False,
                message=f"Failed to send notification: {e}"
            )
    
    async def send_storage_alert_notification(self, 
                                            storage_stats: Dict[str, Any],
                                            recommendations: List[StorageRecommendation]) -> NotificationResult:
        """Send storage monitoring alert notification."""
        if not self.config.enabled:
            return NotificationResult(
                success=False,
                message="Notifications disabled in configuration"
            )
        
        try:
            total_storage_gb = storage_stats.get('total_storage_gb', 0)
            usage_percentage = storage_stats.get('usage_percentage', 0)
            
            # Determine alert level
            if usage_percentage >= 95:
                alert_level = "critical"
                priority = "critical"
            elif usage_percentage >= 85:
                alert_level = "warning"
                priority = "high"
            else:
                alert_level = "info"
                priority = "normal"
            
            # Only send alerts for warning level and above
            if alert_level == "info":
                return NotificationResult(
                    success=True,
                    message="Storage usage within normal limits"
                )
            
            # Prepare template context
            context = {
                'alert_level': alert_level,
                'total_storage_gb': total_storage_gb,
                'usage_percentage': usage_percentage,
                'threshold': 85 if alert_level == "warning" else 95,
                'recommendations': recommendations,
                'timestamp': datetime.now()
            }
            
            # Generate subject
            subject = f"{alert_level.title()} Storage Alert - {usage_percentage:.1f}% Used ({total_storage_gb:.1f}GB)"
            
            # Send notification
            result = await self._send_notification(
                template_name="storage_alert.html",
                subject=subject,
                context=context,
                priority=priority
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send storage alert notification: {e}")
            return NotificationResult(
                success=False,
                message=f"Failed to send notification: {e}"
            )
    
    async def _send_notification(self, 
                               template_name: str,
                               subject: str,
                               context: Dict[str, Any],
                               priority: str = "normal") -> NotificationResult:
        """Send email notification using template."""
        result = NotificationResult(success=False, message="")
        
        try:
            # Load and render template
            template = self.jinja_env.get_template(template_name)
            html_content = template.render(**context)
            
            # Create text version (simplified)
            text_content = self._html_to_text(html_content)
            
            # Create email message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"[Multi-Instance ArXiv] {subject}"
            message["From"] = self.config.from_email
            message["To"] = ", ".join(self.config.recipients)
            
            # Add priority header
            if priority == "critical":
                message["X-Priority"] = "1"
                message["Importance"] = "high"
            elif priority == "high":
                message["X-Priority"] = "2"
                message["Importance"] = "high"
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            await self._send_email(message, result)
            
        except Exception as e:
            result.success = False
            result.message = f"Failed to send notification: {e}"
            logger.error(f"Notification sending failed: {e}")
        
        # Record notification attempt
        self.notification_history.append(result)
        
        # Keep only recent history
        if len(self.notification_history) > 100:
            self.notification_history = self.notification_history[-100:]
        
        return result
    
    async def _send_email(self, message: MIMEMultipart, result: NotificationResult) -> None:
        """Send email using SMTP."""
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
            
            # Send email to each recipient
            for recipient in self.config.recipients:
                try:
                    server.send_message(message, to_addrs=[recipient])
                    result.recipients_sent.append(recipient)
                except Exception as e:
                    logger.error(f"Failed to send to {recipient}: {e}")
                    result.recipients_failed.append(recipient)
            
            server.quit()
            
            # Determine overall success
            result.success = len(result.recipients_sent) > 0
            if result.success:
                result.message = f"Sent to {len(result.recipients_sent)} recipients"
                if result.recipients_failed:
                    result.message += f", failed to send to {len(result.recipients_failed)} recipients"
            else:
                result.message = f"Failed to send to all {len(result.recipients_failed)} recipients"
            
        except Exception as e:
            result.success = False
            result.message = f"SMTP error: {e}"
            result.recipients_failed = self.config.recipients.copy()
            logger.error(f"SMTP connection failed: {e}")
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML content to plain text (simplified)."""
        try:
            # Simple HTML to text conversion
            import re
            
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', html_content)
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            return text
            
        except Exception:
            return "Plain text version not available"
    
    def get_notification_statistics(self) -> Dict[str, Any]:
        """Get notification sending statistics."""
        if not self.notification_history:
            return {'total_notifications': 0}
        
        total_notifications = len(self.notification_history)
        successful_notifications = sum(1 for n in self.notification_history if n.success)
        
        # Recent notifications (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_notifications = [
            n for n in self.notification_history 
            if n.timestamp > recent_cutoff
        ]
        
        return {
            'total_notifications': total_notifications,
            'successful_notifications': successful_notifications,
            'success_rate': (successful_notifications / total_notifications * 100) if total_notifications > 0 else 0,
            'recent_notifications_24h': len(recent_notifications),
            'configuration': {
                'enabled': self.config.enabled,
                'smtp_server': self.config.smtp_server,
                'recipients_count': len(self.config.recipients)
            }
        }
    
    def test_notification_setup(self) -> NotificationResult:
        """Test notification configuration by sending a test email."""
        if not self.config.enabled:
            return NotificationResult(
                success=False,
                message="Notifications disabled in configuration"
            )
        
        try:
            # Create simple test message
            message = MIMEText("This is a test notification from the Multi-Instance ArXiv System.")
            message["Subject"] = "[Multi-Instance ArXiv] Test Notification"
            message["From"] = self.config.from_email
            message["To"] = ", ".join(self.config.recipients)
            
            result = NotificationResult(success=False, message="")
            
            # Send test email
            asyncio.create_task(self._send_email(message, result))
            
            return result
            
        except Exception as e:
            return NotificationResult(
                success=False,
                message=f"Test notification failed: {e}"
            )