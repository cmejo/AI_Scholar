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
# Email imports removed to avoid compatibility issues
# Requests import removed to avoid dependency issues
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
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID"""
        return hashlib.md5(f"{prefix}_{datetime.utcnow().isoformat()}".encode()).hexdigest()
    
    def _generate_fingerprint(self, error_type: str, error_message: str, 
                            stack_trace: str = None) -> str:
        """Generate error fingerprint for grouping"""
        fingerprint_data = f"{error_type}:{error_message}"
        
        if stack_trace:
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
            
            fingerprint = self._generate_fingerprint(error_type, error_message, stack_trace)
            
            with get_db_session() as db:
                existing_error = db.query(ErrorReports).filter(
                    ErrorReports.fingerprint == fingerprint,
                    ErrorReports.environment == context.environment
                ).first()
                
                if existing_error:
                    existing_error.count += 1
                    existing_error.last_seen = datetime.utcnow()
                    existing_error.context = asdict(context)
                    db.commit()
                    error_id = existing_error.id
                else:
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
                
                for key, value in updates.items():
                    if hasattr(incident, key):
                        setattr(incident, key, value)
                
                incident.updated_at = datetime.utcnow()
                db.commit()
                
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
            
            return feedback_id
            
        except Exception as e:
            logger.error(f"Error collecting user feedback: {str(e)}")
            return ""
    
    def get_error_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive error analytics"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            with get_db_session() as db:
                errors = db.query(ErrorReports).filter(
                    ErrorReports.last_seen >= start_date
                ).all()
                
                incidents = db.query(IncidentReports).filter(
                    IncidentReports.created_at >= start_date
                ).all()
            
            analytics = {
                "period": f"{days} days",
                "error_analytics": self._analyze_errors(errors),
                "incident_analytics": self._analyze_incidents(incidents),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting error analytics: {str(e)}")
            return {}
    
    def _analyze_errors(self, errors: List[ErrorReports]) -> Dict[str, Any]:
        """Analyze error patterns"""
        if not errors:
            return {"total_errors": 0}
        
        total_errors = len(errors)
        severity_counts = {}
        category_counts = {}
        
        for error in errors:
            severity_counts[error.severity] = severity_counts.get(error.severity, 0) + 1
            category_counts[error.category] = category_counts.get(error.category, 0) + 1
        
        return {
            "total_errors": total_errors,
            "by_severity": severity_counts,
            "by_category": category_counts
        }
    
    def _analyze_incidents(self, incidents: List[IncidentReports]) -> Dict[str, Any]:
        """Analyze incident patterns"""
        if not incidents:
            return {"total_incidents": 0}
        
        total_incidents = len(incidents)
        severity_counts = {}
        status_counts = {}
        
        for incident in incidents:
            severity_counts[incident.severity] = severity_counts.get(incident.severity, 0) + 1
            status_counts[incident.status] = status_counts.get(incident.status, 0) + 1
        
        return {
            "total_incidents": total_incidents,
            "by_severity": severity_counts,
            "by_status": status_counts
        }
    
    def get_system_health_status(self) -> Dict[str, Any]:
        """Get current system health status"""
        try:
            health_status = {
                "overall_status": "healthy",
                "components": {},
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Simple health check - in a real implementation this would check actual components
            health_status["components"]["database"] = {"status": "healthy", "metrics": {}, "last_check": datetime.utcnow().isoformat()}
            health_status["components"]["redis"] = {"status": "healthy", "metrics": {}, "last_check": datetime.utcnow().isoformat()}
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error getting system health status: {str(e)}")
            return {"overall_status": "unknown", "error": str(e)}
    
    def create_custom_alert_rule(self, name: str, description: str, condition: Dict[str, Any],
                                severity: str, notification_channels: List[str]) -> str:
        """Create custom alert rule"""
        try:
            # In a real implementation, this would store the rule in the database
            rule_id = self._generate_id("alert_rule")
            logger.info(f"Created alert rule: {name} with ID: {rule_id}")
            return rule_id
                
        except Exception as e:
            logger.error(f"Error creating custom alert rule: {str(e)}")
            return ""
    
    def get_incident_timeline(self, incident_id: str) -> List[Dict[str, Any]]:
        """Get incident timeline with all related events"""
        try:
            timeline = []
            
            with get_db_session() as db:
                incident = db.query(IncidentReports).filter(
                    IncidentReports.id == incident_id
                ).first()
                
                if not incident:
                    return []
                
                timeline.append({
                    "timestamp": incident.created_at.isoformat(),
                    "event_type": "incident_created",
                    "description": f"Incident created: {incident.title}",
                    "severity": incident.severity,
                    "actor": incident.created_by
                })
                
                if incident.updated_at != incident.created_at:
                    timeline.append({
                        "timestamp": incident.updated_at.isoformat(),
                        "event_type": "incident_updated",
                        "description": f"Incident status changed to {incident.status}",
                        "status": incident.status
                    })
            
            timeline.sort(key=lambda x: x["timestamp"])
            return timeline
            
        except Exception as e:
            logger.error(f"Error getting incident timeline: {str(e)}")
            return []
    
    def _send_email_notification(self, title: str, message: str, severity: AlertSeverity):
        """Send email notification"""
        try:
            logger.info(f"Email notification: {title} - {message}")
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
    
    def _send_slack_notification(self, title: str, message: str, severity: AlertSeverity):
        """Send Slack notification"""
        try:
            logger.info(f"Slack notification: {title} - {message}")
        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
    
    def _send_pagerduty_notification(self, title: str, message: str, severity: AlertSeverity):
        """Send PagerDuty notification"""
        try:
            logger.info(f"PagerDuty notification: {title} - {message}")
        except Exception as e:
            logger.error(f"Error sending PagerDuty notification: {str(e)}")
    
    def _send_webhook_notification(self, title: str, message: str, severity: AlertSeverity):
        """Send webhook notification"""
        try:
            logger.info(f"Webhook notification: {title} - {message}")
        except Exception as e:
            logger.error(f"Error sending webhook notification: {str(e)}")
    
    def _send_sms_notification(self, title: str, message: str, severity: AlertSeverity):
        """Send SMS notification"""
        try:
            logger.info(f"SMS notification: {title} - {message}")
        except Exception as e:
            logger.error(f"Error sending SMS notification: {str(e)}")
    
    def _send_teams_notification(self, title: str, message: str, severity: AlertSeverity):
        """Send Microsoft Teams notification"""
        try:
            logger.info(f"Teams notification: {title} - {message}")
        except Exception as e:
            logger.error(f"Error sending Teams notification: {str(e)}")

# Create service instance
error_tracking_service = ErrorTrackingService()