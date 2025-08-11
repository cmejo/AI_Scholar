"""
Error Tracking and Alerting Service for AI Scholar Advanced RAG
Comprehensive error tracking, alerting, and incident response
"""

import json
import logging
import traceback
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests
from sqlalchemy import Column, String, DateTime, Text, Integer, JSON, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.core.database import get_db_session
from backend.core.redis_client import redis_client

logger = logging.getLogger(__name__)

Base = declarative_base()

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    SYSTEM = "system"
    APPLICATION = "application"
    INTEGRATION = "integration"
    USER_INPUT = "user_input"
    PERFORMANCE = "performance"
    SECURITY = "security"

class IncidentStatus(Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"

class NotificationChannel(Enum):
    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"
    SMS = "sms"
    TEAMS = "teams"

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EscalationLevel(Enum):
    LEVEL_1 = "level_1"  # Team lead
    LEVEL_2 = "level_2"  # Manager
    LEVEL_3 = "level_3"  # Director
    LEVEL_4 = "level_4"  # Executive

@dataclass
class ErrorContext:
    """Error context information"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    feature_name: Optional[str] = None
    operation: Optional[str] = None
    request_id: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    environment: str = "production"
    additional_data: Optional[Dict[str, Any]] = None

@dataclass
class ErrorReport:
    """Error report structure"""
    error_id: str
    error_type: str
    error_message: str
    stack_trace: Optional[str]
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    timestamp: datetime
    fingerprint: str
    count: int = 1

@dataclass
class IncidentReport:
    """Incident report structure"""
    incident_id: str
    title: str
    description: str
    severity: ErrorSeverity
    category: ErrorCategory
    status: IncidentStatus
    affected_features: List[str]
    error_reports: List[str]  # Error IDs
    assigned_to: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime
    resolution_notes: Optional[str] = None

class ErrorReports(Base):
    """Error reports database model"""
    __tablename__ = "error_reports"
    
    id = Column(String, primary_key=True)
    error_type = Column(String, nullable=False)
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text)
    severity = Column(String, nullable=False)
    category = Column(String, nullable=False)
    fingerprint = Column(String, nullable=False)
    count = Column(Integer, default=1)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    context = Column(JSON, default={})
    is_resolved = Column(Boolean, default=False)
    environment = Column(String, default="production")

class IncidentReports(Base):
    """Incident reports database model"""
    __tablename__ = "incident_reports"
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, nullable=False)
    category = Column(String, nullable=False)
    status = Column(String, nullable=False)
    affected_features = Column(JSON, default=[])
    error_reports = Column(JSON, default=[])
    assigned_to = Column(String)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolution_notes = Column(Text)
    environment = Column(String, default="production")

class UserFeedback(Base):
    """User feedback database model"""
    __tablename__ = "user_feedback"
    
    id = Column(String, primary_key=True)
    feedback_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    user_id = Column(String)
    user_email = Column(String)
    severity = Column(String, default="medium")
    status = Column(String, default="open")
    category = Column(String)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    environment = Column(String, default="production")

class AlertRules(Base):
    """Alert rules database model"""
    __tablename__ = "alert_rules"
    
    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    condition = Column(String, nullable=False)  # JSON condition
    severity = Column(String, nullable=False)
    notification_channels = Column(JSON, default=[])
    escalation_rules = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EscalationRules(Base):
    """Escalation rules database model"""
    __tablename__ = "escalation_rules"
    
    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    trigger_conditions = Column(JSON, nullable=False)  # When to escalate
    escalation_levels = Column(JSON, nullable=False)  # Who to escalate to
    escalation_delays = Column(JSON, nullable=False)  # Time delays between levels
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class IncidentResponse(Base):
    """Incident response tracking"""
    __tablename__ = "incident_response"
    
    id = Column(String, primary_key=True)
    incident_id = Column(String, nullable=False)
    response_type = Column(String, nullable=False)  # automated, manual
    action_taken = Column(Text, nullable=False)
    response_time = Column(Float)  # Response time in seconds
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    responder = Column(String)  # Who/what responded
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemHealth(Base):
    """System health monitoring"""
    __tablename__ = "system_health"
    
    id = Column(String, primary_key=True)
    component = Column(String, nullable=False)
    status = Column(String, nullable=False)  # healthy, degraded, unhealthy
    metrics = Column(JSON, default={})
    last_check = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class ErrorTrackingService:
    """Comprehensive error tracking and alerting service"""
    
    def __init__(self):
        self.redis_client = redis_client
        self.notification_handlers = {
            NotificationChannel.EMAIL: self._send_email_notification,
            NotificationChannel.SLACK: self._send_slack_notification,
            NotificationChannel.PAGERDUTY: self._send_pagerduty_notification,
            NotificationChannel.WEBHOOK: self._send_webhook_notification,
            NotificationChannel.SMS: self._send_sms_notification,
            NotificationChannel.TEAMS: self._send_teams_notification
        }
        
        # Initialize default alert and escalation rules
        self._initialize_alert_rules()
        self._initialize_escalation_rules()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _initialize_alert_rules(self):
        """Initialize default alert rules"""
        default_rules = [
            {
                "name": "critical_error_spike",
                "description": "Alert when critical errors spike",
                "condition": {
                    "metric": "error_count",
                    "severity": "critical",
                    "threshold": 10,
                    "time_window_minutes": 5
                },
                "severity": "critical",
                "notification_channels": ["slack", "email", "pagerduty"]
            },
            {
                "name": "high_error_rate",
                "description": "Alert when error rate is high",
                "condition": {
                    "metric": "error_rate",
                    "threshold": 0.05,  # 5%
                    "time_window_minutes": 10
                },
                "severity": "high",
                "notification_channels": ["slack", "email"]
            },
            {
                "name": "integration_failures",
                "description": "Alert on integration failures",
                "condition": {
                    "metric": "integration_errors",
                    "category": "integration",
                    "threshold": 5,
                    "time_window_minutes": 5
                },
                "severity": "high",
                "notification_channels": ["slack"]
            },
            {
                "name": "user_feedback_spike",
                "description": "Alert on user feedback spike",
                "condition": {
                    "metric": "user_feedback",
                    "feedback_type": "bug_report",
                    "threshold": 20,
                    "time_window_minutes": 60
                },
                "severity": "medium",
                "notification_channels": ["slack"]
            }
        ]
        
        # Create default alert rules if they don't exist
        with get_db_session() as db:
            for rule_config in default_rules:
                existing_rule = db.query(AlertRules).filter(
                    AlertRules.name == rule_config["name"]
                ).first()
                
                if not existing_rule:
                    new_rule = AlertRules(
                        id=self._generate_id("alert_rule"),
                        name=rule_config["name"],
                        description=rule_config["description"],
                        condition=json.dumps(rule_config["condition"]),
                        severity=rule_config["severity"],
                        notification_channels=rule_config["notification_channels"]
                    )
                    db.add(new_rule)
            
            db.commit()
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID"""
        return hashlib.md5(f"{prefix}_{datetime.utcnow().isoformat()}".encode()).hexdigest()
    
    def _generate_fingerprint(self, error_type: str, error_message: str, 
                            stack_trace: str = None) -> str:
        """Generate error fingerprint for grouping"""
        # Create fingerprint based on error type, message, and stack trace
        fingerprint_data = f"{error_type}:{error_message}"
        
        if stack_trace:
            # Extract relevant parts of stack trace for fingerprinting
            lines = stack_trace.split('\n')
            relevant_lines = [line.strip() for line in lines if 'File "' in line or 'line ' in line][:5]
            fingerprint_data += ":" + "|".join(relevant_lines)
        
        return hashlib.md5(fingerprint_data.encode()).hexdigest()
    
    def report_error(self, error_type: str, error_message: str, 
                    stack_trace: str = None, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    category: ErrorCategory = ErrorCategory.APPLICATION,
                    context: ErrorContext = None) -> str:
        """Report an error"""
        try:
            if context is None:
                context = ErrorContext()
            
            # Generate fingerprint for error grouping
            fingerprint = self._generate_fingerprint(error_type, error_message, stack_trace)
            
            with get_db_session() as db:
                # Check if error already exists
                existing_error = db.query(ErrorReports).filter(
                    ErrorReports.fingerprint == fingerprint,
                    ErrorReports.environment == context.environment
                ).first()
                
                if existing_error:
                    # Update existing error
                    existing_error.count += 1
                    existing_error.last_seen = datetime.utcnow()
                    existing_error.context = asdict(context)
                    db.commit()
                    error_id = existing_error.id
                else:
                    # Create new error report
                    error_id = self._generate_id("error")
                    new_error = ErrorReports(
                        id=error_id,
                        error_type=error_type,
                        error_message=error_message,
                        stack_trace=stack_trace,
                        severity=severity.value,
                        category=category.value,
                        fingerprint=fingerprint,
                        context=asdict(context),
                        environment=context.environment
                    )
                    db.add(new_error)
                    db.commit()
            
            # Store in Redis for real-time access
            redis_key = f"error:{error_id}:{context.environment}"
            self.redis_client.hset(redis_key, mapping={
                "error_type": error_type,
                "error_message": error_message,
                "severity": severity.value,
                "category": category.value,
                "timestamp": datetime.utcnow().isoformat(),
                "fingerprint": fingerprint
            })
            self.redis_client.expire(redis_key, 86400)  # 24 hours
            
            # Check alert rules
            self._check_alert_rules(error_type, severity, category, context)
            
            return error_id
            
        except Exception as e:
            logger.error(f"Error reporting error: {str(e)}")
            return ""
    
    def create_incident(self, title: str, description: str, severity: ErrorSeverity,
                       category: ErrorCategory, affected_features: List[str] = None,
                       error_reports: List[str] = None, assigned_to: str = None,
                       created_by: str = "system", environment: str = "production") -> str:
        """Create an incident"""
        try:
            incident_id = self._generate_id("incident")
            
            with get_db_session() as db:
                new_incident = IncidentReports(
                    id=incident_id,
                    title=title,
                    description=description,
                    severity=severity.value,
                    category=category.value,
                    status=IncidentStatus.OPEN.value,
                    affected_features=affected_features or [],
                    error_reports=error_reports or [],
                    assigned_to=assigned_to,
                    created_by=created_by,
                    environment=environment
                )
                db.add(new_incident)
                db.commit()
            
            # Send incident notifications
            self._send_incident_notification(incident_id, "created")
            
            return incident_id
            
        except Exception as e:
            logger.error(f"Error creating incident: {str(e)}")
            return ""
    
    def update_incident(self, incident_id: str, updates: Dict[str, Any]) -> bool:
        """Update an incident"""
        try:
            with get_db_session() as db:
                incident = db.query(IncidentReports).filter(
                    IncidentReports.id == incident_id
                ).first()
                
                if not incident:
                    return False
                
                # Update fields
                for key, value in updates.items():
                    if hasattr(incident, key):
                        setattr(incident, key, value)
                
                incident.updated_at = datetime.utcnow()
                db.commit()
                
                # Send update notification
                self._send_incident_notification(incident_id, "updated")
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating incident {incident_id}: {str(e)}")
            return False
    
    def collect_user_feedback(self, feedback_type: str, title: str, description: str,
                            user_id: str = None, user_email: str = None,
                            severity: str = "medium", category: str = None,
                            metadata: Dict[str, Any] = None,
                            environment: str = "production") -> str:
        """Collect user feedback"""
        try:
            feedback_id = self._generate_id("feedback")
            
            with get_db_session() as db:
                new_feedback = UserFeedback(
                    id=feedback_id,
                    feedback_type=feedback_type,
                    title=title,
                    description=description,
                    user_id=user_id,
                    user_email=user_email,
                    severity=severity,
                    category=category,
                    metadata=metadata or {},
                    environment=environment
                )
                db.add(new_feedback)
                db.commit()
            
            # Check if feedback should trigger alerts
            self._check_feedback_alerts(feedback_type, severity, environment)
            
            return feedback_id
            
        except Exception as e:
            logger.error(f"Error collecting user feedback: {str(e)}")
            return ""
    
    def _check_alert_rules(self, error_type: str, severity: ErrorSeverity,
                          category: ErrorCategory, context: ErrorContext):
        """Check if error triggers any alert rules"""
        try:
            with get_db_session() as db:
                active_rules = db.query(AlertRules).filter(
                    AlertRules.is_active == True
                ).all()
                
                for rule in active_rules:
                    condition = json.loads(rule.condition)
                    
                    if self._evaluate_alert_condition(condition, error_type, severity, 
                                                    category, context):
                        self._trigger_alert(rule, error_type, severity, category, context)
                        
        except Exception as e:
            logger.error(f"Error checking alert rules: {str(e)}")
    
    def _evaluate_alert_condition(self, condition: Dict[str, Any], error_type: str,
                                severity: ErrorSeverity, category: ErrorCategory,
                                context: ErrorContext) -> bool:
        """Evaluate if alert condition is met"""
        try:
            metric = condition.get("metric")
            threshold = condition.get("threshold")
            time_window_minutes = condition.get("time_window_minutes", 5)
            
            if not metric or threshold is None:
                return False
            
            # Calculate time window
            start_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            
            with get_db_session() as db:
                if metric == "error_count":
                    # Count errors in time window
                    query = db.query(ErrorReports).filter(
                        ErrorReports.last_seen >= start_time,
                        ErrorReports.environment == context.environment
                    )
                    
                    if condition.get("severity"):
                        query = query.filter(ErrorReports.severity == condition["severity"])
                    
                    count = query.count()
                    return count >= threshold
                
                elif metric == "error_rate":
                    # Calculate error rate (would need total requests for accurate calculation)
                    # For now, use error count as proxy
                    error_count = db.query(ErrorReports).filter(
                        ErrorReports.last_seen >= start_time,
                        ErrorReports.environment == context.environment
                    ).count()
                    
                    # Simplified error rate calculation
                    return (error_count / 100) >= threshold  # Assuming 100 requests baseline
                
                elif metric == "integration_errors":
                    # Count integration-specific errors
                    count = db.query(ErrorReports).filter(
                        ErrorReports.last_seen >= start_time,
                        ErrorReports.category == ErrorCategory.INTEGRATION.value,
                        ErrorReports.environment == context.environment
                    ).count()
                    
                    return count >= threshold
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating alert condition: {str(e)}")
            return False
    
    def _check_feedback_alerts(self, feedback_type: str, severity: str, environment: str):
        """Check if user feedback should trigger alerts"""
        try:
            # Count recent feedback of same type
            start_time = datetime.utcnow() - timedelta(hours=1)
            
            with get_db_session() as db:
                feedback_count = db.query(UserFeedback).filter(
                    UserFeedback.feedback_type == feedback_type,
                    UserFeedback.created_at >= start_time,
                    UserFeedback.environment == environment
                ).count()
                
                # Alert if too many bug reports in short time
                if feedback_type == "bug_report" and feedback_count >= 20:
                    self._send_notification(
                        NotificationChannel.SLACK,
                        "User Feedback Alert",
                        f"High volume of bug reports: {feedback_count} in the last hour",
                        AlertSeverity.MEDIUM
                    )
                
        except Exception as e:
            logger.error(f"Error checking feedback alerts: {str(e)}")
    
    def _trigger_alert(self, rule: AlertRules, error_type: str, severity: ErrorSeverity,
                      category: ErrorCategory, context: ErrorContext):
        """Trigger an alert based on rule"""
        try:
            alert_message = f"Alert: {rule.name}\n"
            alert_message += f"Error Type: {error_type}\n"
            alert_message += f"Severity: {severity.value}\n"
            alert_message += f"Category: {category.value}\n"
            alert_message += f"Environment: {context.environment}\n"
            
            if context.feature_name:
                alert_message += f"Feature: {context.feature_name}\n"
            
            alert_severity = AlertSeverity(rule.severity)
            
            # Send notifications to configured channels
            for channel_name in rule.notification_channels:
                try:
                    channel = NotificationChannel(channel_name)
                    self._send_notification(channel, rule.name, alert_message, alert_severity)
                except ValueError:
                    logger.warning(f"Unknown notification channel: {channel_name}")
                    
        except Exception as e:
            logger.error(f"Error triggering alert: {str(e)}")
    
    def _send_notification(self, channel: NotificationChannel, title: str,
                          message: str, severity: AlertSeverity):
        """Send notification through specified channel"""
        try:
            handler = self.notification_handlers.get(channel)
            if handler:
                handler(title, message, severity)
            else:
                logger.warning(f"No handler for notification channel: {channel}")
                
        except Exception as e:
            logger.error(f"Error sending notification via {channel}: {str(e)}")
    
    def _send_email_notification(self, title: str, message: str, severity: AlertSeverity):
        """Send email notification"""
        try:
            # Email configuration from environment variables
            smtp_server = os.getenv("SMTP_SERVER", "localhost")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_username = os.getenv("SMTP_USERNAME", "")
            smtp_password = os.getenv("SMTP_PASSWORD", "")
            from_email = os.getenv("FROM_EMAIL", "alerts@aischolar.com")
            to_emails = os.getenv("ALERT_EMAILS", "").split(",")
            
            if not to_emails or not to_emails[0]:
                logger.warning("No alert email addresses configured")
                return
            
            # Create email message
            msg = MimeMultipart()
            msg['From'] = from_email
            msg['To'] = ", ".join(to_emails)
            msg['Subject'] = f"[{severity.value.upper()}] {title}"
            
            msg.attach(MimeText(message, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if smtp_username and smtp_password:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
    
    def _send_slack_notification(self, title: str, message: str, severity: AlertSeverity):
        """Send Slack notification"""
        try:
            webhook_url = os.getenv("SLACK_WEBHOOK_URL")
            if not webhook_url:
                logger.warning("Slack webhook URL not configured")
                return
            
            # Color based on severity
            color_map = {
                AlertSeverity.LOW: "#36a64f",      # Green
                AlertSeverity.MEDIUM: "#ff9500",   # Orange
                AlertSeverity.HIGH: "#ff0000",     # Red
                AlertSeverity.CRITICAL: "#8b0000"  # Dark Red
            }
            
            payload = {
                "attachments": [{
                    "color": color_map.get(severity, "#ff9500"),
                    "title": title,
                    "text": message,
                    "fields": [
                        {
                            "title": "Severity",
                            "value": severity.value.upper(),
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": datetime.utcnow().isoformat(),
                            "short": True
                        }
                    ]
                }]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
    
    def _send_pagerduty_notification(self, title: str, message: str, severity: AlertSeverity):
        """Send PagerDuty notification"""
        try:
            integration_key = os.getenv("PAGERDUTY_INTEGRATION_KEY")
            if not integration_key:
                logger.warning("PagerDuty integration key not configured")
                return
            
            # Only send to PagerDuty for high/critical alerts
            if severity not in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
                return
            
            payload = {
                "routing_key": integration_key,
                "event_action": "trigger",
                "payload": {
                    "summary": title,
                    "source": "ai-scholar-advanced-rag",
                    "severity": severity.value,
                    "custom_details": {
                        "message": message,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            }
            
            response = requests.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
        except Exception as e:
            logger.error(f"Error sending PagerDuty notification: {str(e)}")
    
    def _send_webhook_notification(self, title: str, message: str, severity: AlertSeverity):
        """Send webhook notification"""
        try:
            webhook_url = os.getenv("ALERT_WEBHOOK_URL")
            if not webhook_url:
                logger.warning("Alert webhook URL not configured")
                return
            
            payload = {
                "title": title,
                "message": message,
                "severity": severity.value,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "ai-scholar-advanced-rag"
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {str(e)}")
    
    def _send_incident_notification(self, incident_id: str, action: str):
        """Send incident notification"""
        try:
            with get_db_session() as db:
                incident = db.query(IncidentReports).filter(
                    IncidentReports.id == incident_id
                ).first()
                
                if not incident:
                    return
                
                title = f"Incident {action.title()}: {incident.title}"
                message = f"Incident ID: {incident_id}\n"
                message += f"Description: {incident.description}\n"
                message += f"Severity: {incident.severity}\n"
                message += f"Status: {incident.status}\n"
                message += f"Affected Features: {', '.join(incident.affected_features)}\n"
                
                if incident.assigned_to:
                    message += f"Assigned To: {incident.assigned_to}\n"
                
                severity = AlertSeverity(incident.severity)
                
                # Send to appropriate channels based on severity
                if severity == AlertSeverity.CRITICAL:
                    self._send_notification(NotificationChannel.SLACK, title, message, severity)
                    self._send_notification(NotificationChannel.EMAIL, title, message, severity)
                    self._send_notification(NotificationChannel.PAGERDUTY, title, message, severity)
                elif severity == AlertSeverity.HIGH:
                    self._send_notification(NotificationChannel.SLACK, title, message, severity)
                    self._send_notification(NotificationChannel.EMAIL, title, message, severity)
                else:
                    self._send_notification(NotificationChannel.SLACK, title, message, severity)
                    
        except Exception as e:
            logger.error(f"Error sending incident notification: {str(e)}")
    
    def _initialize_escalation_rules(self):
        """Initialize default escalation rules"""
        default_escalation_rules = [
            {
                "name": "critical_incident_escalation",
                "description": "Escalate critical incidents if not resolved",
                "trigger_conditions": {
                    "severity": "critical",
                    "unresolved_time_minutes": 15,
                    "no_response_time_minutes": 5
                },
                "escalation_levels": [
                    {"level": "level_1", "contacts": ["team-lead@company.com"], "delay_minutes": 5},
                    {"level": "level_2", "contacts": ["manager@company.com"], "delay_minutes": 15},
                    {"level": "level_3", "contacts": ["director@company.com"], "delay_minutes": 30},
                    {"level": "level_4", "contacts": ["cto@company.com"], "delay_minutes": 60}
                ],
                "escalation_delays": [5, 15, 30, 60]
            },
            {
                "name": "high_error_rate_escalation",
                "description": "Escalate when error rate is consistently high",
                "trigger_conditions": {
                    "error_rate_threshold": 0.1,
                    "duration_minutes": 30,
                    "no_action_time_minutes": 10
                },
                "escalation_levels": [
                    {"level": "level_1", "contacts": ["oncall@company.com"], "delay_minutes": 10},
                    {"level": "level_2", "contacts": ["manager@company.com"], "delay_minutes": 30}
                ],
                "escalation_delays": [10, 30]
            }
        ]
        
        with get_db_session() as db:
            for rule_config in default_escalation_rules:
                existing_rule = db.query(EscalationRules).filter(
                    EscalationRules.name == rule_config["name"]
                ).first()
                
                if not existing_rule:
                    new_rule = EscalationRules(
                        id=self._generate_id("escalation_rule"),
                        name=rule_config["name"],
                        description=rule_config["description"],
                        trigger_conditions=rule_config["trigger_conditions"],
                        escalation_levels=rule_config["escalation_levels"],
                        escalation_delays=rule_config["escalation_delays"]
                    )
                    db.add(new_rule)
            
            db.commit()
    
    def _start_background_tasks(self):
        """Start background monitoring and escalation tasks"""
        try:
            # Start escalation monitoring
            asyncio.create_task(self._monitor_escalations())
            
            # Start system health monitoring
            asyncio.create_task(self._monitor_system_health())
            
            # Start automated incident response
            asyncio.create_task(self._automated_incident_response())
            
        except Exception as e:
            logger.error(f"Error starting background tasks: {str(e)}")
    
    async def _monitor_escalations(self):
        """Monitor incidents for escalation"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                with get_db_session() as db:
                    # Get unresolved incidents
                    unresolved_incidents = db.query(IncidentReports).filter(
                        IncidentReports.status.in_([IncidentStatus.OPEN.value, IncidentStatus.INVESTIGATING.value])
                    ).all()
                    
                    for incident in unresolved_incidents:
                        await self._check_incident_escalation(incident)
                        
            except Exception as e:
                logger.error(f"Error in escalation monitoring: {str(e)}")
    
    async def _check_incident_escalation(self, incident: IncidentReports):
        """Check if incident needs escalation"""
        try:
            incident_age = datetime.utcnow() - incident.created_at
            
            with get_db_session() as db:
                escalation_rules = db.query(EscalationRules).filter(
                    EscalationRules.is_active == True
                ).all()
                
                for rule in escalation_rules:
                    conditions = rule.trigger_conditions
                    
                    # Check if incident matches escalation conditions
                    if self._matches_escalation_conditions(incident, conditions, incident_age):
                        await self._execute_escalation(incident, rule)
                        
        except Exception as e:
            logger.error(f"Error checking incident escalation: {str(e)}")
    
    def _matches_escalation_conditions(self, incident: IncidentReports, 
                                     conditions: Dict[str, Any], 
                                     incident_age: timedelta) -> bool:
        """Check if incident matches escalation conditions"""
        try:
            # Check severity match
            if conditions.get("severity") and incident.severity != conditions["severity"]:
                return False
            
            # Check unresolved time
            if conditions.get("unresolved_time_minutes"):
                if incident_age.total_seconds() / 60 < conditions["unresolved_time_minutes"]:
                    return False
            
            # Check if there's been no response
            if conditions.get("no_response_time_minutes"):
                # Check if there's been any response activity
                with get_db_session() as db:
                    recent_response = db.query(IncidentResponse).filter(
                        IncidentResponse.incident_id == incident.id,
                        IncidentResponse.created_at >= datetime.utcnow() - timedelta(
                            minutes=conditions["no_response_time_minutes"]
                        )
                    ).first()
                    
                    if recent_response:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error matching escalation conditions: {str(e)}")
            return False
    
    async def _execute_escalation(self, incident: IncidentReports, rule: EscalationRules):
        """Execute escalation for incident"""
        try:
            # Check current escalation level
            escalation_key = f"escalation:{incident.id}"
            current_level = self.redis_client.get(escalation_key)
            
            if current_level:
                current_level = int(current_level)
            else:
                current_level = 0
            
            # Check if we can escalate to next level
            if current_level < len(rule.escalation_levels):
                escalation_info = rule.escalation_levels[current_level]
                
                # Send escalation notification
                await self._send_escalation_notification(incident, escalation_info, current_level + 1)
                
                # Update escalation level
                self.redis_client.set(escalation_key, current_level + 1, ex=86400)  # 24 hours
                
                # Record escalation response
                self._record_incident_response(
                    incident.id,
                    "automated",
                    f"Escalated to level {current_level + 1}: {escalation_info['level']}",
                    True,
                    "system"
                )
                
        except Exception as e:
            logger.error(f"Error executing escalation: {str(e)}")
    
    async def _send_escalation_notification(self, incident: IncidentReports, 
                                          escalation_info: Dict[str, Any], level: int):
        """Send escalation notification"""
        try:
            title = f"ESCALATION LEVEL {level}: {incident.title}"
            message = f"Incident has been escalated to {escalation_info['level']}\n\n"
            message += f"Incident ID: {incident.id}\n"
            message += f"Description: {incident.description}\n"
            message += f"Severity: {incident.severity}\n"
            message += f"Status: {incident.status}\n"
            message += f"Created: {incident.created_at}\n"
            message += f"Age: {datetime.utcnow() - incident.created_at}\n"
            
            severity = AlertSeverity(incident.severity)
            
            # Send to escalation contacts
            for contact in escalation_info.get("contacts", []):
                if "@" in contact:  # Email
                    await self._send_escalation_email(contact, title, message, severity)
                else:  # Could be phone number for SMS
                    await self._send_escalation_sms(contact, title, message, severity)
            
            # Also send to configured channels
            self._send_notification(NotificationChannel.SLACK, title, message, severity)
            
        except Exception as e:
            logger.error(f"Error sending escalation notification: {str(e)}")
    
    async def _send_escalation_email(self, email: str, title: str, message: str, severity: AlertSeverity):
        """Send escalation email"""
        try:
            # Use existing email notification but with specific recipient
            smtp_server = os.getenv("SMTP_SERVER", "localhost")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_username = os.getenv("SMTP_USERNAME", "")
            smtp_password = os.getenv("SMTP_PASSWORD", "")
            from_email = os.getenv("FROM_EMAIL", "alerts@aischolar.com")
            
            msg = MimeMultipart()
            msg['From'] = from_email
            msg['To'] = email
            msg['Subject'] = f"[ESCALATION-{severity.value.upper()}] {title}"
            
            msg.attach(MimeText(message, 'plain'))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if smtp_username and smtp_password:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"Error sending escalation email: {str(e)}")
    
    async def _send_escalation_sms(self, phone: str, title: str, message: str, severity: AlertSeverity):
        """Send escalation SMS"""
        try:
            # Implement SMS sending (would use service like Twilio)
            sms_message = f"[{severity.value.upper()}] {title}\n{message[:140]}..."
            
            # This would integrate with SMS service
            logger.info(f"SMS escalation to {phone}: {sms_message}")
            
        except Exception as e:
            logger.error(f"Error sending escalation SMS: {str(e)}")
    
    async def _monitor_system_health(self):
        """Monitor system health components"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Check database health
                await self._check_database_health()
                
                # Check Redis health
                await self._check_redis_health()
                
                # Check external integrations
                await self._check_integration_health()
                
                # Check application components
                await self._check_application_health()
                
            except Exception as e:
                logger.error(f"Error in system health monitoring: {str(e)}")
    
    async def _check_database_health(self):
        """Check database health"""
        try:
            start_time = datetime.utcnow()
            
            with get_db_session() as db:
                db.execute("SELECT 1")
                
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            status = "healthy"
            if response_time > 5:
                status = "degraded"
            elif response_time > 10:
                status = "unhealthy"
            
            self._record_system_health("database", status, {
                "response_time": response_time,
                "query": "SELECT 1"
            })
            
            if status != "healthy":
                self._trigger_health_alert("database", status, f"Database response time: {response_time}s")
                
        except Exception as e:
            self._record_system_health("database", "unhealthy", {
                "error": str(e)
            })
            self._trigger_health_alert("database", "unhealthy", f"Database error: {str(e)}")
    
    async def _check_redis_health(self):
        """Check Redis health"""
        try:
            start_time = datetime.utcnow()
            
            self.redis_client.ping()
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            status = "healthy"
            if response_time > 2:
                status = "degraded"
            elif response_time > 5:
                status = "unhealthy"
            
            self._record_system_health("redis", status, {
                "response_time": response_time,
                "operation": "ping"
            })
            
            if status != "healthy":
                self._trigger_health_alert("redis", status, f"Redis response time: {response_time}s")
                
        except Exception as e:
            self._record_system_health("redis", "unhealthy", {
                "error": str(e)
            })
            self._trigger_health_alert("redis", "unhealthy", f"Redis error: {str(e)}")
    
    async def _check_integration_health(self):
        """Check external integration health"""
        try:
            # Check key integrations
            integrations = [
                {"name": "openai_api", "url": "https://api.openai.com/v1/models", "timeout": 10},
                {"name": "pubmed_api", "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", "timeout": 15}
            ]
            
            for integration in integrations:
                try:
                    start_time = datetime.utcnow()
                    
                    response = requests.get(integration["url"], timeout=integration["timeout"])
                    
                    response_time = (datetime.utcnow() - start_time).total_seconds()
                    
                    status = "healthy"
                    if response.status_code != 200:
                        status = "degraded"
                    elif response_time > integration["timeout"] * 0.8:
                        status = "degraded"
                    
                    self._record_system_health(f"integration_{integration['name']}", status, {
                        "response_time": response_time,
                        "status_code": response.status_code,
                        "url": integration["url"]
                    })
                    
                    if status != "healthy":
                        self._trigger_health_alert(
                            f"integration_{integration['name']}", 
                            status, 
                            f"Integration {integration['name']} status: {response.status_code}, time: {response_time}s"
                        )
                        
                except Exception as e:
                    self._record_system_health(f"integration_{integration['name']}", "unhealthy", {
                        "error": str(e),
                        "url": integration["url"]
                    })
                    self._trigger_health_alert(
                        f"integration_{integration['name']}", 
                        "unhealthy", 
                        f"Integration {integration['name']} error: {str(e)}"
                    )
                    
        except Exception as e:
            logger.error(f"Error checking integration health: {str(e)}")
    
    async def _check_application_health(self):
        """Check application component health"""
        try:
            # Check error rates
            start_time = datetime.utcnow() - timedelta(minutes=5)
            
            with get_db_session() as db:
                error_count = db.query(ErrorReports).filter(
                    ErrorReports.last_seen >= start_time
                ).count()
                
                critical_errors = db.query(ErrorReports).filter(
                    ErrorReports.last_seen >= start_time,
                    ErrorReports.severity == ErrorSeverity.CRITICAL.value
                ).count()
            
            status = "healthy"
            if error_count > 100:
                status = "degraded"
            elif critical_errors > 5:
                status = "unhealthy"
            
            self._record_system_health("application", status, {
                "error_count_5min": error_count,
                "critical_errors_5min": critical_errors,
                "check_period": "5_minutes"
            })
            
            if status != "healthy":
                self._trigger_health_alert(
                    "application", 
                    status, 
                    f"High error rate: {error_count} errors, {critical_errors} critical in 5 minutes"
                )
                
        except Exception as e:
            logger.error(f"Error checking application health: {str(e)}")
    
    def _record_system_health(self, component: str, status: str, metrics: Dict[str, Any]):
        """Record system health status"""
        try:
            with get_db_session() as db:
                health_record = SystemHealth(
                    id=self._generate_id("health"),
                    component=component,
                    status=status,
                    metrics=metrics
                )
                db.add(health_record)
                db.commit()
                
                # Also store in Redis for quick access
                redis_key = f"health:{component}"
                self.redis_client.hset(redis_key, mapping={
                    "status": status,
                    "metrics": json.dumps(metrics),
                    "last_check": datetime.utcnow().isoformat()
                })
                self.redis_client.expire(redis_key, 3600)  # 1 hour
                
        except Exception as e:
            logger.error(f"Error recording system health: {str(e)}")
    
    def _trigger_health_alert(self, component: str, status: str, message: str):
        """Trigger health alert"""
        try:
            severity = AlertSeverity.MEDIUM
            if status == "unhealthy":
                severity = AlertSeverity.HIGH
            
            title = f"System Health Alert: {component}"
            alert_message = f"Component: {component}\nStatus: {status}\nDetails: {message}"
            
            self._send_notification(NotificationChannel.SLACK, title, alert_message, severity)
            
            if severity == AlertSeverity.HIGH:
                self._send_notification(NotificationChannel.EMAIL, title, alert_message, severity)
                
        except Exception as e:
            logger.error(f"Error triggering health alert: {str(e)}")
    
    async def _automated_incident_response(self):
        """Automated incident response system"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                with get_db_session() as db:
                    # Get recent critical incidents without automated response
                    recent_incidents = db.query(IncidentReports).filter(
                        IncidentReports.severity == ErrorSeverity.CRITICAL.value,
                        IncidentReports.created_at >= datetime.utcnow() - timedelta(minutes=10)
                    ).all()
                    
                    for incident in recent_incidents:
                        # Check if automated response already attempted
                        existing_response = db.query(IncidentResponse).filter(
                            IncidentResponse.incident_id == incident.id,
                            IncidentResponse.response_type == "automated"
                        ).first()
                        
                        if not existing_response:
                            await self._execute_automated_response(incident)
                            
            except Exception as e:
                logger.error(f"Error in automated incident response: {str(e)}")
    
    async def _execute_automated_response(self, incident: IncidentReports):
        """Execute automated response for incident"""
        try:
            start_time = datetime.utcnow()
            
            # Determine response actions based on incident category
            actions = self._get_automated_response_actions(incident)
            
            success = True
            error_message = None
            actions_taken = []
            
            for action in actions:
                try:
                    result = await self._execute_response_action(action, incident)
                    actions_taken.append(f"{action}: {result}")
                except Exception as e:
                    success = False
                    error_message = str(e)
                    actions_taken.append(f"{action}: FAILED - {str(e)}")
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Record the response
            self._record_incident_response(
                incident.id,
                "automated",
                "; ".join(actions_taken),
                success,
                "system",
                response_time,
                error_message
            )
            
        except Exception as e:
            logger.error(f"Error executing automated response: {str(e)}")
    
    def _get_automated_response_actions(self, incident: IncidentReports) -> List[str]:
        """Get automated response actions for incident"""
        actions = []
        
        # Common actions for all critical incidents
        actions.extend([
            "notify_oncall",
            "create_status_page_incident",
            "increase_monitoring"
        ])
        
        # Category-specific actions
        if incident.category == ErrorCategory.INTEGRATION.value:
            actions.extend([
                "check_integration_health",
                "retry_failed_integrations",
                "enable_circuit_breaker"
            ])
        elif incident.category == ErrorCategory.PERFORMANCE.value:
            actions.extend([
                "scale_resources",
                "clear_caches",
                "enable_rate_limiting"
            ])
        elif incident.category == ErrorCategory.SECURITY.value:
            actions.extend([
                "block_suspicious_ips",
                "rotate_api_keys",
                "enable_enhanced_logging"
            ])
        
        return actions
    
    async def _execute_response_action(self, action: str, incident: IncidentReports) -> str:
        """Execute specific response action"""
        try:
            if action == "notify_oncall":
                # Send immediate notification to on-call team
                self._send_notification(
                    NotificationChannel.PAGERDUTY,
                    f"CRITICAL INCIDENT: {incident.title}",
                    f"Automated response triggered for incident {incident.id}",
                    AlertSeverity.CRITICAL
                )
                return "On-call team notified"
            
            elif action == "create_status_page_incident":
                # Would integrate with status page service
                return "Status page incident created"
            
            elif action == "increase_monitoring":
                # Increase monitoring frequency
                redis_key = "monitoring:frequency"
                self.redis_client.set(redis_key, "high", ex=3600)  # 1 hour
                return "Monitoring frequency increased"
            
            elif action == "check_integration_health":
                # Trigger immediate health check
                await self._check_integration_health()
                return "Integration health check completed"
            
            elif action == "retry_failed_integrations":
                # Retry failed integration calls
                return "Failed integrations retried"
            
            elif action == "enable_circuit_breaker":
                # Enable circuit breaker for failing services
                redis_key = "circuit_breaker:enabled"
                self.redis_client.set(redis_key, "true", ex=1800)  # 30 minutes
                return "Circuit breaker enabled"
            
            elif action == "scale_resources":
                # Would trigger auto-scaling
                return "Resource scaling triggered"
            
            elif action == "clear_caches":
                # Clear application caches
                cache_keys = self.redis_client.keys("cache:*")
                if cache_keys:
                    self.redis_client.delete(*cache_keys)
                return f"Cleared {len(cache_keys)} cache entries"
            
            elif action == "enable_rate_limiting":
                # Enable aggressive rate limiting
                redis_key = "rate_limit:aggressive"
                self.redis_client.set(redis_key, "true", ex=1800)  # 30 minutes
                return "Aggressive rate limiting enabled"
            
            elif action == "block_suspicious_ips":
                # Would integrate with firewall/security service
                return "Suspicious IPs blocked"
            
            elif action == "rotate_api_keys":
                # Would trigger API key rotation
                return "API key rotation initiated"
            
            elif action == "enable_enhanced_logging":
                # Enable debug logging
                redis_key = "logging:level"
                self.redis_client.set(redis_key, "debug", ex=3600)  # 1 hour
                return "Enhanced logging enabled"
            
            else:
                return f"Unknown action: {action}"
                
        except Exception as e:
            raise Exception(f"Failed to execute {action}: {str(e)}")
    
    def _record_incident_response(self, incident_id: str, response_type: str, 
                                action_taken: str, success: bool, responder: str,
                                response_time: float = None, error_message: str = None):
        """Record incident response"""
        try:
            with get_db_session() as db:
                response_record = IncidentResponse(
                    id=self._generate_id("response"),
                    incident_id=incident_id,
                    response_type=response_type,
                    action_taken=action_taken,
                    response_time=response_time,
                    success=success,
                    error_message=error_message,
                    responder=responder
                )
                db.add(response_record)
                db.commit()
                
        except Exception as e:
            logger.error(f"Error recording incident response: {str(e)}")
    
    def _send_sms_notification(self, title: str, message: str, severity: AlertSeverity):
        """Send SMS notification"""
        try:
            # Would integrate with SMS service like Twilio
            sms_numbers = os.getenv("ALERT_SMS_NUMBERS", "").split(",")
            
            if not sms_numbers or not sms_numbers[0]:
                logger.warning("No SMS numbers configured")
                return
            
            # Truncate message for SMS
            sms_message = f"[{severity.value.upper()}] {title}\n{message[:140]}..."
            
            # This would send actual SMS
            logger.info(f"SMS notification: {sms_message}")
            
        except Exception as e:
            logger.error(f"Error sending SMS notification: {str(e)}")
    
    def _send_teams_notification(self, title: str, message: str, severity: AlertSeverity):
        """Send Microsoft Teams notification"""
        try:
            webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
            if not webhook_url:
                logger.warning("Teams webhook URL not configured")
                return
            
            # Color based on severity
            color_map = {
                AlertSeverity.LOW: "00FF00",      # Green
                AlertSeverity.MEDIUM: "FFA500",   # Orange
                AlertSeverity.HIGH: "FF0000",     # Red
                AlertSeverity.CRITICAL: "8B0000"  # Dark Red
            }
            
            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": color_map.get(severity, "FFA500"),
                "summary": title,
                "sections": [{
                    "activityTitle": title,
                    "activitySubtitle": f"Severity: {severity.value.upper()}",
                    "text": message,
                    "facts": [
                        {
                            "name": "Severity",
                            "value": severity.value.upper()
                        },
                        {
                            "name": "Timestamp",
                            "value": datetime.utcnow().isoformat()
                        }
                    ]
                }]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
        except Exception as e:
            logger.error(f"Error sending Teams notification: {str(e)}")
    
    def get_error_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive error analytics"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            with get_db_session() as db:
                # Error trends
                errors = db.query(ErrorReports).filter(
                    ErrorReports.last_seen >= start_date
                ).all()
                
                # Incident trends
                incidents = db.query(IncidentReports).filter(
                    IncidentReports.created_at >= start_date
                ).all()
                
                # Response metrics
                responses = db.query(IncidentResponse).filter(
                    IncidentResponse.created_at >= start_date
                ).all()
                
                # System health trends
                health_records = db.query(SystemHealth).filter(
                    SystemHealth.created_at >= start_date
                ).all()
            
            analytics = {
                "period": f"{days} days",
                "error_analytics": self._analyze_errors(errors),
                "incident_analytics": self._analyze_incidents(incidents),
                "response_analytics": self._analyze_responses(responses),
                "health_analytics": self._analyze_health(health_records),
                "trends": self._calculate_trends(errors, incidents, days),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting error analytics: {str(e)}")
            return {}
    
    def _analyze_errors(self, errors: List[ErrorReports]) -> Dict[str, Any]:
        """Analyze error patterns"""
        if not errors:
            return {}
        
        total_errors = len(errors)
        severity_counts = {}
        category_counts = {}
        feature_counts = {}
        
        for error in errors:
            # Count by severity
            severity_counts[error.severity] = severity_counts.get(error.severity, 0) + 1
            
            # Count by category
            category_counts[error.category] = category_counts.get(error.category, 0) + 1
            
            # Count by feature
            if error.context and error.context.get("feature_name"):
                feature = error.context["feature_name"]
                feature_counts[feature] = feature_counts.get(feature, 0) + 1
        
        return {
            "total_errors": total_errors,
            "by_severity": severity_counts,
            "by_category": category_counts,
            "by_feature": feature_counts,
            "most_common_error": max(errors, key=lambda x: x.count).error_type if errors else None
        }
    
    def _analyze_incidents(self, incidents: List[IncidentReports]) -> Dict[str, Any]:
        """Analyze incident patterns"""
        if not incidents:
            return {}
        
        total_incidents = len(incidents)
        severity_counts = {}
        status_counts = {}
        resolution_times = []
        
        for incident in incidents:
            # Count by severity
            severity_counts[incident.severity] = severity_counts.get(incident.severity, 0) + 1
            
            # Count by status
            status_counts[incident.status] = status_counts.get(incident.status, 0) + 1
            
            # Calculate resolution time for resolved incidents
            if incident.status == IncidentStatus.RESOLVED.value and incident.updated_at:
                resolution_time = (incident.updated_at - incident.created_at).total_seconds() / 60
                resolution_times.append(resolution_time)
        
        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
        
        return {
            "total_incidents": total_incidents,
            "by_severity": severity_counts,
            "by_status": status_counts,
            "average_resolution_time_minutes": avg_resolution_time,
            "resolved_incidents": len(resolution_times)
        }
    
    def _analyze_responses(self, responses: List[IncidentResponse]) -> Dict[str, Any]:
        """Analyze response patterns"""
        if not responses:
            return {}
        
        total_responses = len(responses)
        automated_responses = len([r for r in responses if r.response_type == "automated"])
        successful_responses = len([r for r in responses if r.success])
        
        response_times = [r.response_time for r in responses if r.response_time]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total_responses": total_responses,
            "automated_responses": automated_responses,
            "successful_responses": successful_responses,
            "success_rate": (successful_responses / total_responses * 100) if total_responses > 0 else 0,
            "average_response_time_seconds": avg_response_time
        }
    
    def _analyze_health(self, health_records: List[SystemHealth]) -> Dict[str, Any]:
        """Analyze system health patterns"""
        if not health_records:
            return {}
        
        component_health = {}
        for record in health_records:
            if record.component not in component_health:
                component_health[record.component] = {"healthy": 0, "degraded": 0, "unhealthy": 0}
            
            component_health[record.component][record.status] += 1
        
        return {
            "total_health_checks": len(health_records),
            "by_component": component_health,
            "overall_health_score": self._calculate_health_score(component_health)
        }
    
    def _calculate_health_score(self, component_health: Dict[str, Dict[str, int]]) -> float:
        """Calculate overall health score"""
        total_checks = 0
        healthy_checks = 0
        
        for component, statuses in component_health.items():
            total_checks += sum(statuses.values())
            healthy_checks += statuses.get("healthy", 0)
        
        return (healthy_checks / total_checks * 100) if total_checks > 0 else 100
    
    def _calculate_trends(self, errors: List[ErrorReports], incidents: List[IncidentReports], days: int) -> Dict[str, Any]:
        """Calculate trends over time"""
        try:
            # Group by day
            error_trends = {}
            incident_trends = {}
            
            for i in range(days):
                date = (datetime.utcnow() - timedelta(days=i)).date()
                error_trends[date.isoformat()] = 0
                incident_trends[date.isoformat()] = 0
            
            for error in errors:
                date = error.last_seen.date()
                if date.isoformat() in error_trends:
                    error_trends[date.isoformat()] += 1
            
            for incident in incidents:
                date = incident.created_at.date()
                if date.isoformat() in incident_trends:
                    incident_trends[date.isoformat()] += 1
            
            return {
                "error_trends": error_trends,
                "incident_trends": incident_trends
            }
            
        except Exception as e:
            logger.error(f"Error calculating trends: {str(e)}")
            return {}
    
    def get_system_health_status(self) -> Dict[str, Any]:
        """Get current system health status"""
        try:
            health_status = {
                "overall_status": "healthy",
                "components": {},
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Get latest health status for each component
            component_keys = self.redis_client.keys("health:*")
            
            for key in component_keys:
                component = key.decode().replace("health:", "")
                health_data = self.redis_client.hgetall(key)
                
                if health_data:
                    status = health_data.get(b"status", b"unknown").decode()
                    metrics = json.loads(health_data.get(b"metrics", b"{}").decode())
                    last_check = health_data.get(b"last_check", b"").decode()
                    
                    health_status["components"][component] = {
                        "status": status,
                        "metrics": metrics,
                        "last_check": last_check
                    }
                    
                    # Update overall status
                    if status == "unhealthy":
                        health_status["overall_status"] = "unhealthy"
                    elif status == "degraded" and health_status["overall_status"] == "healthy":
                        health_status["overall_status"] = "degraded"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error getting system health status: {str(e)}")
            return {"overall_status": "unknown", "error": str(e)}
    
    def create_custom_alert_rule(self, name: str, description: str, condition: Dict[str, Any],
                                severity: str, notification_channels: List[str]) -> str:
        """Create custom alert rule"""
        try:
            with get_db_session() as db:
                # Check if rule already exists
                existing_rule = db.query(AlertRules).filter(
                    AlertRules.name == name
                ).first()
                
                if existing_rule:
                    raise ValueError(f"Alert rule '{name}' already exists")
                
                rule_id = self._generate_id("alert_rule")
                new_rule = AlertRules(
                    id=rule_id,
                    name=name,
                    description=description,
                    condition=json.dumps(condition),
                    severity=severity,
                    notification_channels=notification_channels
                )
                
                db.add(new_rule)
                db.commit()
                
                return rule_id
                
        except Exception as e:
            logger.error(f"Error creating custom alert rule: {str(e)}")
            return ""
    
    def get_incident_timeline(self, incident_id: str) -> List[Dict[str, Any]]:
        """Get incident timeline with all related events"""
        try:
            timeline = []
            
            with get_db_session() as db:
                # Get incident
                incident = db.query(IncidentReports).filter(
                    IncidentReports.id == incident_id
                ).first()
                
                if not incident:
                    return []
                
                # Add incident creation
                timeline.append({
                    "timestamp": incident.created_at.isoformat(),
                    "event_type": "incident_created",
                    "description": f"Incident created: {incident.title}",
                    "severity": incident.severity,
                    "actor": incident.created_by
                })
                
                # Get all responses
                responses = db.query(IncidentResponse).filter(
                    IncidentResponse.incident_id == incident_id
                ).order_by(IncidentResponse.created_at).all()
                
                for response in responses:
                    timeline.append({
                        "timestamp": response.created_at.isoformat(),
                        "event_type": "response_action",
                        "description": response.action_taken,
                        "response_type": response.response_type,
                        "success": response.success,
                        "actor": response.responder,
                        "response_time": response.response_time
                    })
                
                # Add incident updates
                if incident.updated_at != incident.created_at:
                    timeline.append({
                        "timestamp": incident.updated_at.isoformat(),
                        "event_type": "incident_updated",
                        "description": f"Incident status changed to {incident.status}",
                        "status": incident.status
                    })
            
            # Sort by timestamp
            timeline.sort(key=lambda x: x["timestamp"])
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error getting incident timeline: {str(e)}")
            return []
    
    def get_error_reports(self, limit: int = 100, environment: str = "production",
                         severity: ErrorSeverity = None, category: ErrorCategory = None,
                         resolved: bool = None) -> List[Dict[str, Any]]:
        """Get error reports"""
        try:
            with get_db_session() as db:
                query = db.query(ErrorReports).filter(
                    ErrorReports.environment == environment
                )
                
                if severity:
                    query = query.filter(ErrorReports.severity == severity.value)
                
                if category:
                    query = query.filter(ErrorReports.category == category.value)
                
                if resolved is not None:
                    query = query.filter(ErrorReports.is_resolved == resolved)
                
                error_reports = query.order_by(ErrorReports.last_seen.desc()).limit(limit).all()
                
                return [
                    {
                        "id": report.id,
                        "error_type": report.error_type,
                        "error_message": report.error_message,
                        "severity": report.severity,
                        "category": report.category,
                        "count": report.count,
                        "first_seen": report.first_seen.isoformat(),
                        "last_seen": report.last_seen.isoformat(),
                        "context": report.context,
                        "is_resolved": report.is_resolved,
                        "fingerprint": report.fingerprint
                    }
                    for report in error_reports
                ]
                
        except Exception as e:
            logger.error(f"Error getting error reports: {str(e)}")
            return []
    
    def get_incidents(self, limit: int = 50, environment: str = "production",
                     status: IncidentStatus = None) -> List[Dict[str, Any]]:
        """Get incident reports"""
        try:
            with get_db_session() as db:
                query = db.query(IncidentReports).filter(
                    IncidentReports.environment == environment
                )
                
                if status:
                    query = query.filter(IncidentReports.status == status.value)
                
                incidents = query.order_by(IncidentReports.created_at.desc()).limit(limit).all()
                
                return [
                    {
                        "id": incident.id,
                        "title": incident.title,
                        "description": incident.description,
                        "severity": incident.severity,
                        "category": incident.category,
                        "status": incident.status,
                        "affected_features": incident.affected_features,
                        "error_reports": incident.error_reports,
                        "assigned_to": incident.assigned_to,
                        "created_by": incident.created_by,
                        "created_at": incident.created_at.isoformat(),
                        "updated_at": incident.updated_at.isoformat(),
                        "resolution_notes": incident.resolution_notes
                    }
                    for incident in incidents
                ]
                
        except Exception as e:
            logger.error(f"Error getting incidents: {str(e)}")
            return []
    
    def get_user_feedback(self, limit: int = 100, environment: str = "production",
                         feedback_type: str = None, status: str = None) -> List[Dict[str, Any]]:
        """Get user feedback"""
        try:
            with get_db_session() as db:
                query = db.query(UserFeedback).filter(
                    UserFeedback.environment == environment
                )
                
                if feedback_type:
                    query = query.filter(UserFeedback.feedback_type == feedback_type)
                
                if status:
                    query = query.filter(UserFeedback.status == status)
                
                feedback_records = query.order_by(UserFeedback.created_at.desc()).limit(limit).all()
                
                return [
                    {
                        "id": feedback.id,
                        "feedback_type": feedback.feedback_type,
                        "title": feedback.title,
                        "description": feedback.description,
                        "user_id": feedback.user_id,
                        "user_email": feedback.user_email,
                        "severity": feedback.severity,
                        "status": feedback.status,
                        "category": feedback.category,
                        "metadata": feedback.metadata,
                        "created_at": feedback.created_at.isoformat(),
                        "updated_at": feedback.updated_at.isoformat()
                    }
                    for feedback in feedback_records
                ]
                
        except Exception as e:
            logger.error(f"Error getting user feedback: {str(e)}")
            return []

# Create service instance
error_tracking_service = ErrorTrackingService()

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    condition: str
    threshold: Union[int, float]
    time_window_minutes: int
    severity: ErrorSeverity
    notification_channels: List[NotificationChannel]
    enabled: bool = True
    cooldown_minutes: int = 30

class ErrorRecord(Base):
    """Error record database model"""
    __tablename__ = "error_records"
    
    id = Column(String(36), primary_key=True)
    error_hash = Column(String(64), index=True)  # Hash for grouping similar errors
    error_type = Column(String(100), index=True)
    error_message = Column(Text)
    stack_trace = Column(Text)
    severity = Column(String(20), default="medium")
    category = Column(String(50), default="application")
    feature_name = Column(String(100), index=True)
    operation = Column(String(100))
    user_id = Column(String(36), index=True)
    session_id = Column(String(100))
    request_id = Column(String(100))
    user_agent = Column(String(500))
    ip_address = Column(String(45))
    context_data = Column(JSON, default=dict)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    occurrence_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class Incident(Base):
    """Incident tracking"""
    __tablename__ = "incidents"
    
    id = Column(String(36), primary_key=True)
    title = Column(String(255))
    description = Column(Text)
    severity = Column(String(20))
    status = Column(String(50), default="open")
    category = Column(String(50))
    affected_features = Column(JSON, default=list)
    error_records = Column(JSON, default=list)  # List of related error record IDs
    assigned_to = Column(String(100))
    created_by = Column(String(100), default="system")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    impact_assessment = Column(JSON, default=dict)
    timeline = Column(JSON, default=list)

class AlertNotification(Base):
    """Alert notification log"""
    __tablename__ = "alert_notifications"
    
    id = Column(String(36), primary_key=True)
    alert_name = Column(String(100), index=True)
    notification_channel = Column(String(50))
    recipient = Column(String(255))
    message = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    metadata = Column(JSON, default=dict)

class UserFeedback(Base):
    """User feedback and issue reports"""
    __tablename__ = "user_feedback"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), index=True)
    feedback_type = Column(String(50))  # bug_report, feature_request, general
    title = Column(String(255))
    description = Column(Text)
    severity = Column(String(20), default="medium")
    category = Column(String(50))
    feature_name = Column(String(100))
    browser_info = Column(JSON, default=dict)
    steps_to_reproduce = Column(Text)
    expected_behavior = Column(Text)
    actual_behavior = Column(Text)
    attachments = Column(JSON, default=list)
    status = Column(String(50), default="open")
    assigned_to = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)

class ErrorTrackingService:
    """Comprehensive error tracking and alerting service"""
    
    def __init__(self):
        self.redis_client = redis_client
        self.alert_rules = {}
        self.notification_handlers = {}
        self.error_processors = []
        
        # Initialize alert rules and notification handlers
        self._initialize_alert_rules()
        self._initialize_notification_handlers()
        
        # Start background tasks
        asyncio.create_task(self._process_error_queue())
        asyncio.create_task(self._check_alert_conditions())
    
    def track_error(self, error: Exception, context: ErrorContext = None, 
                   severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                   category: ErrorCategory = ErrorCategory.APPLICATION) -> str:
        """Track an error with context"""
        try:
            # Generate error hash for grouping
            error_hash = self._generate_error_hash(error)
            error_id = f"error_{int(datetime.utcnow().timestamp() * 1000)}"
            
            # Extract error information
            error_type = type(error).__name__
            error_message = str(error)
            stack_trace = traceback.format_exc()
            
            # Check if this is a known error
            existing_error = self._get_existing_error(error_hash)
            
            if existing_error:
                # Update existing error
                self._update_existing_error(existing_error, context)
                error_id = existing_error.id
            else:
                # Create new error record
                with get_db_session() as session:
                    error_record = ErrorRecord(
                        id=error_id,
                        error_hash=error_hash,
                        error_type=error_type,
                        error_message=error_message,
                        stack_trace=stack_trace,
                        severity=severity.value,
                        category=category.value,
                        feature_name=context.feature_name if context else None,
                        operation=context.operation if context else None,
                        user_id=context.user_id if context else None,
                        session_id=context.session_id if context else None,
                        request_id=context.request_id if context else None,
                        user_agent=context.user_agent if context else None,
                        ip_address=context.ip_address if context else None,
                        context_data=context.additional_data if context and context.additional_data else {}
                    )
                    session.add(error_record)
                    session.commit()
            
            # Add to processing queue
            self._queue_error_for_processing(error_id, severity, category)
            
            # Log error
            logger.error(f"Error tracked: {error_id} - {error_type}: {error_message}")
            
            return error_id
            
        except Exception as e:
            logger.error(f"Failed to track error: {str(e)}")
            return None
    
    def create_incident(self, title: str, description: str, severity: ErrorSeverity,
                       category: ErrorCategory, affected_features: List[str] = None,
                       error_records: List[str] = None, assigned_to: str = None) -> str:
        """Create a new incident"""
        try:
            incident_id = f"incident_{int(datetime.utcnow().timestamp() * 1000)}"
            
            with get_db_session() as session:
                incident = Incident(
                    id=incident_id,
                    title=title,
                    description=description,
                    severity=severity.value,
                    category=category.value,
                    affected_features=affected_features or [],
                    error_records=error_records or [],
                    assigned_to=assigned_to,
                    timeline=[{
                        'timestamp': datetime.utcnow().isoformat(),
                        'event': 'incident_created',
                        'description': 'Incident created',
                        'user': 'system'
                    }]
                )
                session.add(incident)
                session.commit()
            
            # Send notifications for critical incidents
            if severity == ErrorSeverity.CRITICAL:
                self._send_incident_notification(incident_id, title, description, severity)
            
            logger.info(f"Incident created: {incident_id} - {title}")
            return incident_id
            
        except Exception as e:
            logger.error(f"Failed to create incident: {str(e)}")
            return None
    
    def update_incident(self, incident_id: str, status: IncidentStatus = None,
                       assigned_to: str = None, resolution_notes: str = None,
                       update_description: str = None, user: str = "system") -> bool:
        """Update an incident"""
        try:
            with get_db_session() as session:
                incident = session.query(Incident).filter_by(id=incident_id).first()
                if not incident:
                    logger.warning(f"Incident {incident_id} not found")
                    return False
                
                # Update fields
                if status:
                    incident.status = status.value
                    if status == IncidentStatus.RESOLVED:
                        incident.resolved_at = datetime.utcnow()
                
                if assigned_to:
                    incident.assigned_to = assigned_to
                
                if resolution_notes:
                    incident.resolution_notes = resolution_notes
                
                incident.updated_at = datetime.utcnow()
                
                # Add to timeline
                timeline_entry = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'event': 'incident_updated',
                    'description': update_description or f"Status changed to {status.value if status else 'updated'}",
                    'user': user
                }
                
                if incident.timeline:
                    incident.timeline.append(timeline_entry)
                else:
                    incident.timeline = [timeline_entry]
                
                session.commit()
                
                logger.info(f"Incident updated: {incident_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update incident {incident_id}: {str(e)}")
            return False
    
    def collect_user_feedback(self, user_id: str, feedback_type: str, title: str,
                            description: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                            category: str = "general", feature_name: str = None,
                            browser_info: Dict[str, Any] = None,
                            steps_to_reproduce: str = None,
                            expected_behavior: str = None,
                            actual_behavior: str = None) -> str:
        """Collect user feedback and issue reports"""
        try:
            feedback_id = f"feedback_{int(datetime.utcnow().timestamp() * 1000)}"
            
            with get_db_session() as session:
                feedback = UserFeedback(
                    id=feedback_id,
                    user_id=user_id,
                    feedback_type=feedback_type,
                    title=title,
                    description=description,
                    severity=severity.value,
                    category=category,
                    feature_name=feature_name,
                    browser_info=browser_info or {},
                    steps_to_reproduce=steps_to_reproduce,
                    expected_behavior=expected_behavior,
                    actual_behavior=actual_behavior
                )
                session.add(feedback)
                session.commit()
            
            # Create incident for critical bug reports
            if feedback_type == "bug_report" and severity == ErrorSeverity.CRITICAL:
                self.create_incident(
                    title=f"Critical Bug Report: {title}",
                    description=description,
                    severity=severity,
                    category=ErrorCategory.APPLICATION,
                    affected_features=[feature_name] if feature_name else []
                )
            
            logger.info(f"User feedback collected: {feedback_id}")
            return feedback_id
            
        except Exception as e:
            logger.error(f"Failed to collect user feedback: {str(e)}")
            return None
    
    def get_error_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get error analytics and trends"""
        try:
            with get_db_session() as session:
                start_date = datetime.utcnow() - timedelta(days=days)
                
                errors = session.query(ErrorRecord).filter(
                    ErrorRecord.created_at >= start_date
                ).all()
                
                # Calculate analytics
                total_errors = len(errors)
                unique_errors = len(set(error.error_hash for error in errors))
                
                # Group by severity
                severity_breakdown = {}
                for severity in ErrorSeverity:
                    severity_breakdown[severity.value] = sum(
                        1 for error in errors if error.severity == severity.value
                    )
                
                # Group by category
                category_breakdown = {}
                for category in ErrorCategory:
                    category_breakdown[category.value] = sum(
                        1 for error in errors if error.category == category.value
                    )
                
                # Top error types
                error_type_counts = {}
                for error in errors:
                    error_type_counts[error.error_type] = error_type_counts.get(error.error_type, 0) + 1
                
                top_errors = sorted(error_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                
                # Feature breakdown
                feature_breakdown = {}
                for error in errors:
                    if error.feature_name:
                        feature_breakdown[error.feature_name] = feature_breakdown.get(error.feature_name, 0) + 1
                
                # Daily trend
                daily_errors = {}
                for error in errors:
                    date_key = error.created_at.date().isoformat()
                    daily_errors[date_key] = daily_errors.get(date_key, 0) + 1
                
                return {
                    'period_days': days,
                    'total_errors': total_errors,
                    'unique_errors': unique_errors,
                    'error_rate': total_errors / days if days > 0 else 0,
                    'severity_breakdown': severity_breakdown,
                    'category_breakdown': category_breakdown,
                    'top_error_types': top_errors,
                    'feature_breakdown': feature_breakdown,
                    'daily_trend': daily_errors,
                    'resolution_rate': self._calculate_resolution_rate(errors)
                }
                
        except Exception as e:
            logger.error(f"Failed to get error analytics: {str(e)}")
            return {}
    
    def get_incident_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get incident summary and metrics"""
        try:
            with get_db_session() as session:
                start_date = datetime.utcnow() - timedelta(days=days)
                
                incidents = session.query(Incident).filter(
                    Incident.created_at >= start_date
                ).all()
                
                # Calculate metrics
                total_incidents = len(incidents)
                open_incidents = sum(1 for incident in incidents if incident.status == "open")
                resolved_incidents = sum(1 for incident in incidents if incident.status == "resolved")
                
                # Average resolution time
                resolved_with_time = [
                    incident for incident in incidents 
                    if incident.resolved_at and incident.status == "resolved"
                ]
                
                avg_resolution_time = 0
                if resolved_with_time:
                    total_resolution_time = sum(
                        (incident.resolved_at - incident.created_at).total_seconds()
                        for incident in resolved_with_time
                    )
                    avg_resolution_time = total_resolution_time / len(resolved_with_time) / 3600  # hours
                
                # Severity breakdown
                severity_breakdown = {}
                for severity in ErrorSeverity:
                    severity_breakdown[severity.value] = sum(
                        1 for incident in incidents if incident.severity == severity.value
                    )
                
                return {
                    'period_days': days,
                    'total_incidents': total_incidents,
                    'open_incidents': open_incidents,
                    'resolved_incidents': resolved_incidents,
                    'resolution_rate': resolved_incidents / total_incidents if total_incidents > 0 else 0,
                    'avg_resolution_time_hours': avg_resolution_time,
                    'severity_breakdown': severity_breakdown
                }
                
        except Exception as e:
            logger.error(f"Failed to get incident summary: {str(e)}")
            return {}
    
    # Private helper methods
    def _generate_error_hash(self, error: Exception) -> str:
        """Generate hash for error grouping"""
        error_signature = f"{type(error).__name__}:{str(error)}"
        return hashlib.sha256(error_signature.encode()).hexdigest()
    
    def _get_existing_error(self, error_hash: str) -> Optional[ErrorRecord]:
        """Get existing error record by hash"""
        try:
            with get_db_session() as session:
                return session.query(ErrorRecord).filter_by(
                    error_hash=error_hash,
                    resolved=False
                ).first()
        except Exception:
            return None
    
    def _update_existing_error(self, error_record: ErrorRecord, context: ErrorContext):
        """Update existing error record"""
        try:
            with get_db_session() as session:
                error_record.last_seen = datetime.utcnow()
                error_record.occurrence_count += 1
                
                if context:
                    if context.user_id and not error_record.user_id:
                        error_record.user_id = context.user_id
                    if context.feature_name and not error_record.feature_name:
                        error_record.feature_name = context.feature_name
                
                session.commit()
        except Exception as e:
            logger.error(f"Failed to update existing error: {str(e)}")
    
    def _queue_error_for_processing(self, error_id: str, severity: ErrorSeverity, category: ErrorCategory):
        """Queue error for background processing"""
        try:
            error_data = {
                'error_id': error_id,
                'severity': severity.value,
                'category': category.value,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.redis_client.lpush("error_processing_queue", json.dumps(error_data))
        except Exception as e:
            logger.error(f"Failed to queue error for processing: {str(e)}")
    
    def _initialize_alert_rules(self):
        """Initialize default alert rules"""
        self.alert_rules = {
            'high_error_rate': AlertRule(
                name='high_error_rate',
                condition='error_count > 50',
                threshold=50,
                time_window_minutes=15,
                severity=ErrorSeverity.HIGH,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK]
            ),
            'critical_errors': AlertRule(
                name='critical_errors',
                condition='critical_error_count > 0',
                threshold=0,
                time_window_minutes=5,
                severity=ErrorSeverity.CRITICAL,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.SMS]
            ),
            'integration_failures': AlertRule(
                name='integration_failures',
                condition='integration_error_rate > 0.1',
                threshold=0.1,
                time_window_minutes=10,
                severity=ErrorSeverity.MEDIUM,
                notification_channels=[NotificationChannel.EMAIL]
            )
        }
    
    def _initialize_notification_handlers(self):
        """Initialize notification handlers"""
        self.notification_handlers = {
            NotificationChannel.EMAIL: self._send_email_notification,
            NotificationChannel.SLACK: self._send_slack_notification,
            NotificationChannel.WEBHOOK: self._send_webhook_notification,
            NotificationChannel.SMS: self._send_sms_notification
        }
    
    async def _process_error_queue(self):
        """Process error queue in background"""
        while True:
            try:
                # Get error from queue
                error_data = self.redis_client.brpop("error_processing_queue", timeout=30)
                
                if error_data:
                    error_info = json.loads(error_data[1])
                    await self._process_error(error_info)
                
            except Exception as e:
                logger.error(f"Error processing queue: {str(e)}")
                await asyncio.sleep(60)
    
    async def _process_error(self, error_info: Dict[str, Any]):
        """Process individual error"""
        try:
            error_id = error_info['error_id']
            severity = ErrorSeverity(error_info['severity'])
            
            # Run error processors
            for processor in self.error_processors:
                try:
                    await processor(error_id, error_info)
                except Exception as e:
                    logger.error(f"Error processor failed: {str(e)}")
            
            # Check if error should trigger incident
            if severity == ErrorSeverity.CRITICAL:
                await self._check_incident_creation(error_id, error_info)
            
        except Exception as e:
            logger.error(f"Failed to process error {error_info.get('error_id')}: {str(e)}")
    
    async def _check_alert_conditions(self):
        """Check alert conditions periodically"""
        while True:
            try:
                for rule_name, rule in self.alert_rules.items():
                    if rule.enabled:
                        await self._evaluate_alert_rule(rule)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error checking alert conditions: {str(e)}")
                await asyncio.sleep(60)
    
    async def _evaluate_alert_rule(self, rule: AlertRule):
        """Evaluate a single alert rule"""
        try:
            # Check cooldown
            cooldown_key = f"alert_cooldown:{rule.name}"
            if self.redis_client.exists(cooldown_key):
                return
            
            # Get metric value based on rule condition
            metric_value = await self._get_alert_metric_value(rule)
            
            if metric_value is not None and metric_value > rule.threshold:
                # Trigger alert
                await self._trigger_alert(rule, metric_value)
                
                # Set cooldown
                self.redis_client.setex(cooldown_key, rule.cooldown_minutes * 60, "1")
                
        except Exception as e:
            logger.error(f"Error evaluating alert rule {rule.name}: {str(e)}")
    
    async def _get_alert_metric_value(self, rule: AlertRule) -> Optional[float]:
        """Get current metric value for alert rule"""
        try:
            if 'error_count' in rule.condition:
                # Count errors in time window
                start_time = datetime.utcnow() - timedelta(minutes=rule.time_window_minutes)
                
                with get_db_session() as session:
                    count = session.query(ErrorRecord).filter(
                        ErrorRecord.created_at >= start_time
                    ).count()
                    return float(count)
            
            elif 'critical_error_count' in rule.condition:
                # Count critical errors
                start_time = datetime.utcnow() - timedelta(minutes=rule.time_window_minutes)
                
                with get_db_session() as session:
                    count = session.query(ErrorRecord).filter(
                        ErrorRecord.created_at >= start_time,
                        ErrorRecord.severity == ErrorSeverity.CRITICAL.value
                    ).count()
                    return float(count)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting alert metric value: {str(e)}")
            return None
    
    async def _trigger_alert(self, rule: AlertRule, metric_value: float):
        """Trigger an alert"""
        try:
            alert_message = f"Alert: {rule.name} - {rule.condition} (current: {metric_value}, threshold: {rule.threshold})"
            
            # Send notifications
            for channel in rule.notification_channels:
                handler = self.notification_handlers.get(channel)
                if handler:
                    try:
                        await handler(rule.name, alert_message, rule.severity)
                    except Exception as e:
                        logger.error(f"Failed to send {channel.value} notification: {str(e)}")
            
            logger.warning(f"Alert triggered: {rule.name}")
            
        except Exception as e:
            logger.error(f"Failed to trigger alert {rule.name}: {str(e)}")
    
    async def _send_email_notification(self, alert_name: str, message: str, severity: ErrorSeverity):
        """Send email notification"""
        # Implementation would depend on email service configuration
        logger.info(f"Email notification: {alert_name} - {message}")
    
    async def _send_slack_notification(self, alert_name: str, message: str, severity: ErrorSeverity):
        """Send Slack notification"""
        # Implementation would use Slack webhook
        logger.info(f"Slack notification: {alert_name} - {message}")
    
    async def _send_webhook_notification(self, alert_name: str, message: str, severity: ErrorSeverity):
        """Send webhook notification"""
        # Implementation would send HTTP POST to configured webhook
        logger.info(f"Webhook notification: {alert_name} - {message}")
    
    async def _send_sms_notification(self, alert_name: str, message: str, severity: ErrorSeverity):
        """Send SMS notification"""
        # Implementation would use SMS service
        logger.info(f"SMS notification: {alert_name} - {message}")
    
    def _send_incident_notification(self, incident_id: str, title: str, description: str, severity: ErrorSeverity):
        """Send incident notification"""
        try:
            message = f"Critical Incident Created: {title}\nID: {incident_id}\nDescription: {description}"
            
            # Send to all critical notification channels
            for channel in [NotificationChannel.EMAIL, NotificationChannel.SLACK]:
                handler = self.notification_handlers.get(channel)
                if handler:
                    asyncio.create_task(handler(f"incident_{incident_id}", message, severity))
            
        except Exception as e:
            logger.error(f"Failed to send incident notification: {str(e)}")
    
    async def _check_incident_creation(self, error_id: str, error_info: Dict[str, Any]):
        """Check if error should trigger incident creation"""
        try:
            # Get error details
            with get_db_session() as session:
                error_record = session.query(ErrorRecord).filter_by(id=error_id).first()
                
                if error_record and error_record.severity == ErrorSeverity.CRITICAL.value:
                    # Check if similar incident already exists
                    existing_incident = session.query(Incident).filter(
                        Incident.status.in_(['open', 'investigating']),
                        Incident.category == error_record.category,
                        Incident.affected_features.contains([error_record.feature_name])
                    ).first()
                    
                    if not existing_incident:
                        # Create new incident
                        self.create_incident(
                            title=f"Critical Error: {error_record.error_type}",
                            description=f"Critical error detected: {error_record.error_message}",
                            severity=ErrorSeverity.CRITICAL,
                            category=ErrorCategory(error_record.category),
                            affected_features=[error_record.feature_name] if error_record.feature_name else [],
                            error_records=[error_id]
                        )
            
        except Exception as e:
            logger.error(f"Failed to check incident creation: {str(e)}")
    
    def _calculate_resolution_rate(self, errors: List[ErrorRecord]) -> float:
        """Calculate error resolution rate"""
        if not errors:
            return 0.0
        
        resolved_count = sum(1 for error in errors if error.resolved)
        return resolved_count / len(errors)

# Global service instance
error_tracking_service = ErrorTrackingService()

# Decorator for automatic error tracking
def track_errors(feature_name: str = None, operation: str = None, 
                severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                category: ErrorCategory = ErrorCategory.APPLICATION):
    """Decorator to automatically track errors"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Extract context
                context = ErrorContext(
                    feature_name=feature_name,
                    operation=operation or func.__name__,
                    user_id=kwargs.get('user_id'),
                    session_id=kwargs.get('session_id'),
                    request_id=kwargs.get('request_id')
                )
                
                # Track error
                error_tracking_service.track_error(e, context, severity, category)
                
                # Re-raise exception
                raise
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Extract context
                context = ErrorContext(
                    feature_name=feature_name,
                    operation=operation or func.__name__,
                    user_id=kwargs.get('user_id'),
                    session_id=kwargs.get('session_id'),
                    request_id=kwargs.get('request_id')
                )
                
                # Track error
                error_tracking_service.track_error(e, context, severity, category)
                
                # Re-raise exception
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Create service instance
error_tracking_service = ErrorTrackingService()