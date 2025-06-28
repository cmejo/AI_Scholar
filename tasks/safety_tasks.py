"""
Celery tasks for safety and compliance processing
"""

import os
import logging
from celery import Celery, Task
from datetime import datetime, timedelta

# Configure Celery
broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery_app = Celery('safety_tasks', broker=broker_url, backend=result_backend)

logger = logging.getLogger(__name__)

class LoggingTask(Task):
    """Task base class with logging"""
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {self.name}[{task_id}] succeeded: {retval}")
        return super().on_success(retval, task_id, args, kwargs)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {self.name}[{task_id}] failed: {exc}")
        return super().on_failure(exc, task_id, args, kwargs, einfo)

@celery_app.task(base=LoggingTask, bind=True, max_retries=3)
def process_message_pii_redaction(self, message_id, original_content):
    """
    Asynchronously process PII redaction for a message
    """
    try:
        # Import here to avoid circular imports
        from models import db, ChatMessage
        from services.pii_redaction_service import PIIRedactionService
        
        # Create Flask app context
        from app_enterprise import app
        with app.app_context():
            # Get the message
            message = ChatMessage.query.get(message_id)
            if not message:
                raise Exception(f"Message not found: {message_id}")
            
            # Initialize PII service
            pii_service = PIIRedactionService()
            
            # Process PII redaction
            result = pii_service.detect_and_redact_pii(
                text=original_content,
                user_id=message.user_id,
                message_id=message.id
            )
            
            if result['success'] and result['has_pii']:
                # Update message with redacted content
                message.original_content = original_content
                message.content = result['redacted_text']
                message.has_pii_redaction = True
                
                db.session.commit()
                
                logger.info(f"PII redaction completed for message {message_id}: {result['redaction_count']} redactions")
                
                return {
                    'success': True,
                    'message_id': message_id,
                    'redaction_count': result['redaction_count'],
                    'pii_types': result['pii_types_found']
                }
            else:
                logger.info(f"No PII found in message {message_id}")
                return {
                    'success': True,
                    'message_id': message_id,
                    'redaction_count': 0,
                    'pii_types': []
                }
                
    except Exception as e:
        logger.error(f"Error processing PII redaction for message {message_id}: {e}")
        
        # Retry with exponential backoff
        retry_in = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
        self.retry(exc=e, countdown=retry_in)
        
        return {'success': False, 'error': str(e)}

@celery_app.task(base=LoggingTask, bind=True, max_retries=3)
def process_message_content_moderation(self, message_id, content, content_type):
    """
    Asynchronously process content moderation for a message
    """
    try:
        # Import here to avoid circular imports
        from models import db, ChatMessage
        from services.content_moderation_service import ContentModerationService
        
        # Create Flask app context
        from app_enterprise import app
        with app.app_context():
            # Get the message
            message = ChatMessage.query.get(message_id)
            if not message:
                raise Exception(f"Message not found: {message_id}")
            
            # Initialize moderation service
            moderation_service = ContentModerationService()
            
            # Process content moderation
            result = moderation_service.moderate_content(
                text=content,
                content_type=content_type,
                user_id=message.user_id,
                message_id=message.id
            )
            
            if result['success']:
                # Update message with moderation results
                message.content_moderated = True
                message.moderation_status = result['result']
                
                # Calculate and store safety score
                if result['result'] == 'approved':
                    safety_score = 1.0
                elif result['result'] == 'flagged':
                    max_confidence = max(result.get('confidence_scores', {}).values(), default=0)
                    safety_score = max(0.1, 1.0 - max_confidence)
                elif result['result'] == 'blocked':
                    safety_score = 0.1
                else:
                    safety_score = 0.5
                
                message.safety_score = safety_score
                
                # If content should be blocked and this is an AI response, update content
                if result['should_block'] and content_type == 'ai_response':
                    message.content = result.get('replacement_content', message.content)
                
                db.session.commit()
                
                logger.info(f"Content moderation completed for message {message_id}: {result['result']}")
                
                return {
                    'success': True,
                    'message_id': message_id,
                    'moderation_result': result['result'],
                    'safety_score': safety_score,
                    'should_block': result['should_block']
                }
            else:
                raise Exception(result.get('error', 'Unknown moderation error'))
                
    except Exception as e:
        logger.error(f"Error processing content moderation for message {message_id}: {e}")
        
        # Retry with exponential backoff
        retry_in = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
        self.retry(exc=e, countdown=retry_in)
        
        return {'success': False, 'error': str(e)}

@celery_app.task(base=LoggingTask)
def cleanup_expired_data():
    """
    Clean up expired data for compliance
    """
    try:
        # Import here to avoid circular imports
        from models import db, ComplianceAuditLog, ContentModerationLog, PIIRedactionLog
        
        # Create Flask app context
        from app_enterprise import app
        with app.app_context():
            # Default retention period: 2 years
            retention_cutoff = datetime.utcnow() - timedelta(days=365 * 2)
            
            # Clean up old audit logs
            old_audit_logs = ComplianceAuditLog.query.filter(
                ComplianceAuditLog.created_at < retention_cutoff
            ).all()
            
            audit_count = len(old_audit_logs)
            for log in old_audit_logs:
                db.session.delete(log)
            
            # Clean up old moderation logs
            old_mod_logs = ContentModerationLog.query.filter(
                ContentModerationLog.created_at < retention_cutoff
            ).all()
            
            mod_count = len(old_mod_logs)
            for log in old_mod_logs:
                db.session.delete(log)
            
            # Clean up old PII redaction logs
            old_pii_logs = PIIRedactionLog.query.filter(
                PIIRedactionLog.created_at < retention_cutoff
            ).all()
            
            pii_count = len(old_pii_logs)
            for log in old_pii_logs:
                db.session.delete(log)
            
            db.session.commit()
            
            logger.info(f"Data cleanup completed: {audit_count} audit logs, {mod_count} moderation logs, {pii_count} PII logs deleted")
            
            return {
                'success': True,
                'deleted_counts': {
                    'audit_logs': audit_count,
                    'moderation_logs': mod_count,
                    'pii_logs': pii_count
                }
            }
            
    except Exception as e:
        logger.error(f"Error in data cleanup: {e}")
        db.session.rollback()
        return {'success': False, 'error': str(e)}

@celery_app.task(base=LoggingTask)
def generate_safety_report():
    """
    Generate periodic safety and compliance reports
    """
    try:
        # Import here to avoid circular imports
        from services.safety_compliance_service import SafetyComplianceService
        
        # Create Flask app context
        from app_enterprise import app
        with app.app_context():
            # Initialize safety service
            safety_service = SafetyComplianceService()
            
            # Generate dashboard data for the last 7 days
            dashboard_data = safety_service.get_safety_dashboard_data(days=7)
            
            if dashboard_data['success']:
                # Log the report generation
                from models import db, ComplianceAuditLog
                
                log_entry = ComplianceAuditLog(
                    event_type='safety_report_generated',
                    event_category='compliance',
                    description='Weekly safety and compliance report generated',
                    metadata=dashboard_data
                )
                
                db.session.add(log_entry)
                db.session.commit()
                
                logger.info("Weekly safety report generated successfully")
                
                return {
                    'success': True,
                    'report_data': dashboard_data
                }
            else:
                raise Exception(dashboard_data.get('error', 'Unknown error generating report'))
                
    except Exception as e:
        logger.error(f"Error generating safety report: {e}")
        return {'success': False, 'error': str(e)}

@celery_app.task(base=LoggingTask)
def check_user_safety_patterns():
    """
    Check for concerning user safety patterns across all users
    """
    try:
        # Import here to avoid circular imports
        from models import db, User, ContentModerationLog, SafetyIncident
        
        # Create Flask app context
        from app_enterprise import app
        with app.app_context():
            # Get all active users
            users = User.query.filter_by(is_active=True).all()
            
            patterns_found = 0
            incidents_created = 0
            
            for user in users:
                # Check for violation patterns in the last 7 days
                week_ago = datetime.utcnow() - timedelta(days=7)
                
                violations = ContentModerationLog.query.filter(
                    ContentModerationLog.user_id == user.id,
                    ContentModerationLog.moderation_result.in_(['flagged', 'blocked']),
                    ContentModerationLog.created_at >= week_ago
                ).count()
                
                # Check for high-risk violations
                high_risk_violations = ContentModerationLog.query.filter(
                    ContentModerationLog.user_id == user.id,
                    ContentModerationLog.moderation_result == 'blocked',
                    ContentModerationLog.created_at >= week_ago
                ).count()
                
                # Create incident if patterns are concerning
                if violations >= 10 or high_risk_violations >= 2:
                    patterns_found += 1
                    
                    # Check if incident already exists
                    existing_incident = SafetyIncident.query.filter(
                        SafetyIncident.user_id == user.id,
                        SafetyIncident.incident_type == 'pattern_violation',
                        SafetyIncident.status.in_(['open', 'investigating']),
                        SafetyIncident.created_at >= week_ago
                    ).first()
                    
                    if not existing_incident:
                        severity = 'high' if high_risk_violations >= 2 else 'medium'
                        
                        incident = SafetyIncident(
                            user_id=user.id,
                            incident_type='pattern_violation',
                            severity=severity,
                            description=f"User has {violations} violations ({high_risk_violations} high-risk) in the past week",
                            evidence={
                                'weekly_violations': violations,
                                'high_risk_violations': high_risk_violations,
                                'detection_method': 'automated_pattern_check'
                            }
                        )
                        
                        db.session.add(incident)
                        incidents_created += 1
            
            db.session.commit()
            
            logger.info(f"Safety pattern check completed: {patterns_found} patterns found, {incidents_created} incidents created")
            
            return {
                'success': True,
                'users_checked': len(users),
                'patterns_found': patterns_found,
                'incidents_created': incidents_created
            }
            
    except Exception as e:
        logger.error(f"Error checking user safety patterns: {e}")
        db.session.rollback()
        return {'success': False, 'error': str(e)}

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-expired-data': {
        'task': 'tasks.safety_tasks.cleanup_expired_data',
        'schedule': 86400.0,  # Run daily
    },
    'generate-safety-report': {
        'task': 'tasks.safety_tasks.generate_safety_report',
        'schedule': 604800.0,  # Run weekly
    },
    'check-user-safety-patterns': {
        'task': 'tasks.safety_tasks.check_user_safety_patterns',
        'schedule': 3600.0,  # Run hourly
    },
}

celery_app.conf.timezone = 'UTC'