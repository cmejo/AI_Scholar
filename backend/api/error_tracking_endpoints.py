"""
Error Tracking API Endpoints for AI Scholar Advanced RAG
Provides access to error tracking, incident management, and user feedback
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel
from backend.services.error_tracking_service import (
    error_tracking_service, ErrorSeverity, ErrorCategory, IncidentStatus,
    ErrorContext
)
from backend.core.database import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/error-tracking", tags=["error-tracking"])

# Pydantic models for request/response
class ErrorReportRequest(BaseModel):
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    severity: str = "medium"
    category: str = "application"
    feature_name: Optional[str] = None
    operation: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None

class IncidentCreateRequest(BaseModel):
    title: str
    description: str
    severity: str
    category: str
    affected_features: Optional[List[str]] = None
    assigned_to: Optional[str] = None

class IncidentUpdateRequest(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    update_description: Optional[str] = None

class UserFeedbackRequest(BaseModel):
    feedback_type: str  # bug_report, feature_request, general
    title: str
    description: str
    user_email: Optional[str] = None
    severity: str = "medium"
    category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@router.post("/errors/report")
async def report_error(request: ErrorReportRequest, req: Request):
    """Report an error"""
    try:
        # Extract context from request
        context = ErrorContext(
            user_id=request.user_id,
            session_id=request.session_id,
            feature_name=request.feature_name,
            operation=request.operation,
            request_id=req.headers.get("x-request-id"),
            user_agent=req.headers.get("user-agent"),
            ip_address=req.client.host,
            environment="production",
            additional_data=request.context_data
        )
        
        # Convert string enums to enum objects
        severity = ErrorSeverity(request.severity)
        category = ErrorCategory(request.category)
        
        error_id = error_tracking_service.report_error(
            error_type=request.error_type,
            error_message=request.error_message,
            stack_trace=request.stack_trace,
            severity=severity,
            category=category,
            context=context
        )
        
        return JSONResponse(content={
            "status": "success",
            "error_id": error_id,
            "message": "Error reported successfully"
        })
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {str(e)}")
    except Exception as e:
        logger.error(f"Error reporting error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to report error")

@router.get("/errors")
async def get_error_reports(
    limit: int = Query(100, description="Number of errors to return"),
    environment: str = Query("production", description="Environment"),
    severity: Optional[str] = Query(None, description="Error severity"),
    category: Optional[str] = Query(None, description="Error category"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status")
):
    """Get error reports"""
    try:
        severity_enum = None
        if severity:
            severity_enum = ErrorSeverity(severity)
        
        category_enum = None
        if category:
            category_enum = ErrorCategory(category)
        
        error_reports = error_tracking_service.get_error_reports(
            limit=limit,
            environment=environment,
            severity=severity_enum,
            category=category_enum,
            resolved=resolved
        )
        
        return JSONResponse(content={"error_reports": error_reports})
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting error reports: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get error reports")

@router.post("/incidents")
async def create_incident(request: IncidentCreateRequest):
    """Create a new incident"""
    try:
        severity = ErrorSeverity(request.severity)
        category = ErrorCategory(request.category)
        
        incident_id = error_tracking_service.create_incident(
            title=request.title,
            description=request.description,
            severity=severity,
            category=category,
            affected_features=request.affected_features,
            assigned_to=request.assigned_to,
            created_by="api_user"  # Would get from authentication
        )
        
        return JSONResponse(content={
            "status": "success",
            "incident_id": incident_id,
            "message": "Incident created successfully"
        })
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating incident: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create incident")

@router.put("/incidents/{incident_id}")
async def update_incident(incident_id: str, request: IncidentUpdateRequest):
    """Update an incident"""
    try:
        updates = {}
        
        if request.status:
            updates["status"] = request.status
        if request.assigned_to:
            updates["assigned_to"] = request.assigned_to
        if request.resolution_notes:
            updates["resolution_notes"] = request.resolution_notes
        
        success = error_tracking_service.update_incident(incident_id, updates)
        
        if not success:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        return JSONResponse(content={
            "status": "success",
            "message": "Incident updated successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating incident {incident_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update incident")

@router.get("/incidents")
async def get_incidents(
    limit: int = Query(50, description="Number of incidents to return"),
    environment: str = Query("production", description="Environment"),
    status: Optional[str] = Query(None, description="Incident status")
):
    """Get incident reports"""
    try:
        status_enum = None
        if status:
            status_enum = IncidentStatus(status)
        
        incidents = error_tracking_service.get_incidents(
            limit=limit,
            environment=environment,
            status=status_enum
        )
        
        return JSONResponse(content={"incidents": incidents})
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting incidents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get incidents")

@router.post("/feedback")
async def submit_user_feedback(request: UserFeedbackRequest, req: Request):
    """Submit user feedback"""
    try:
        # Extract user ID from authentication if available
        user_id = None  # Would extract from JWT token or session
        
        feedback_id = error_tracking_service.collect_user_feedback(
            feedback_type=request.feedback_type,
            title=request.title,
            description=request.description,
            user_id=user_id,
            user_email=request.user_email,
            severity=request.severity,
            category=request.category,
            metadata=request.metadata
        )
        
        return JSONResponse(content={
            "status": "success",
            "feedback_id": feedback_id,
            "message": "Feedback submitted successfully"
        })
        
    except Exception as e:
        logger.error(f"Error submitting user feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@router.get("/feedback")
async def get_user_feedback(
    limit: int = Query(100, description="Number of feedback items to return"),
    environment: str = Query("production", description="Environment"),
    feedback_type: Optional[str] = Query(None, description="Feedback type"),
    status: Optional[str] = Query(None, description="Feedback status")
):
    """Get user feedback"""
    try:
        feedback_records = error_tracking_service.get_user_feedback(
            limit=limit,
            environment=environment,
            feedback_type=feedback_type,
            status=status
        )
        
        return JSONResponse(content={"feedback": feedback_records})
        
    except Exception as e:
        logger.error(f"Error getting user feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user feedback")

@router.get("/dashboard")
async def get_error_tracking_dashboard():
    """Get error tracking dashboard data"""
    try:
        # Get recent error reports
        recent_errors = error_tracking_service.get_error_reports(limit=50)
        
        # Get open incidents
        open_incidents = error_tracking_service.get_incidents(
            limit=20,
            status=IncidentStatus.OPEN
        )
        
        # Get recent user feedback
        recent_feedback = error_tracking_service.get_user_feedback(limit=30)
        
        # Calculate error statistics
        total_errors = len(recent_errors)
        critical_errors = len([e for e in recent_errors if e["severity"] == "critical"])
        resolved_errors = len([e for e in recent_errors if e["is_resolved"]])
        
        # Calculate incident statistics
        total_incidents = len(open_incidents)
        critical_incidents = len([i for i in open_incidents if i["severity"] == "critical"])
        
        # Calculate feedback statistics
        bug_reports = len([f for f in recent_feedback if f["feedback_type"] == "bug_report"])
        feature_requests = len([f for f in recent_feedback if f["feedback_type"] == "feature_request"])
        
        dashboard_data = {
            "error_statistics": {
                "total_errors": total_errors,
                "critical_errors": critical_errors,
                "resolved_errors": resolved_errors,
                "resolution_rate": (resolved_errors / total_errors * 100) if total_errors > 0 else 0
            },
            "incident_statistics": {
                "open_incidents": total_incidents,
                "critical_incidents": critical_incidents
            },
            "feedback_statistics": {
                "total_feedback": len(recent_feedback),
                "bug_reports": bug_reports,
                "feature_requests": feature_requests
            },
            "recent_errors": recent_errors[:10],
            "open_incidents": open_incidents[:10],
            "recent_feedback": recent_feedback[:10],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=dashboard_data)
        
    except Exception as e:
        logger.error(f"Error getting error tracking dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")

@router.get("/health")
async def get_error_tracking_health():
    """Get comprehensive system health status"""
    try:
        health_status = error_tracking_service.get_system_health_status()
        return JSONResponse(content=health_status)
        
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        return JSONResponse(
            content={
                "overall_status": "unhealthy",
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat()
            },
            status_code=500
        )

@router.get("/analytics")
async def get_comprehensive_analytics(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """Get comprehensive error and incident analytics"""
    try:
        analytics = error_tracking_service.get_error_analytics(days)
        return JSONResponse(content=analytics)
        
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

@router.get("/incidents/{incident_id}/timeline")
async def get_incident_timeline(incident_id: str):
    """Get detailed incident timeline"""
    try:
        timeline = error_tracking_service.get_incident_timeline(incident_id)
        return JSONResponse(content={"timeline": timeline})
        
    except Exception as e:
        logger.error(f"Error getting incident timeline: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get incident timeline")

@router.post("/alert-rules")
async def create_alert_rule(
    name: str,
    description: str,
    condition: Dict[str, Any],
    severity: str,
    notification_channels: List[str]
):
    """Create custom alert rule"""
    try:
        rule_id = error_tracking_service.create_custom_alert_rule(
            name=name,
            description=description,
            condition=condition,
            severity=severity,
            notification_channels=notification_channels
        )
        
        if rule_id:
            return JSONResponse(content={
                "status": "success",
                "rule_id": rule_id,
                "message": "Alert rule created successfully"
            })
        else:
            raise HTTPException(status_code=400, detail="Failed to create alert rule")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating alert rule: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create alert rule")

@router.get("/alert-rules")
async def get_alert_rules():
    """Get all alert rules"""
    try:
        with get_db_session() as db:
            from backend.services.error_tracking_service import AlertRules
            
            rules = db.query(AlertRules).all()
            
            rule_data = [{
                'id': rule.id,
                'name': rule.name,
                'description': rule.description,
                'condition': json.loads(rule.condition),
                'severity': rule.severity,
                'notification_channels': rule.notification_channels,
                'is_active': rule.is_active,
                'created_at': rule.created_at.isoformat(),
                'updated_at': rule.updated_at.isoformat()
            } for rule in rules]
            
            return JSONResponse(content={"alert_rules": rule_data})
            
    except Exception as e:
        logger.error(f"Error getting alert rules: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get alert rules")

@router.put("/alert-rules/{rule_id}")
async def update_alert_rule(
    rule_id: str,
    is_active: Optional[bool] = None,
    notification_channels: Optional[List[str]] = None
):
    """Update alert rule"""
    try:
        with get_db_session() as db:
            from backend.services.error_tracking_service import AlertRules
            
            rule = db.query(AlertRules).filter_by(id=rule_id).first()
            if not rule:
                raise HTTPException(status_code=404, detail="Alert rule not found")
            
            if is_active is not None:
                rule.is_active = is_active
            if notification_channels is not None:
                rule.notification_channels = notification_channels
            
            rule.updated_at = datetime.utcnow()
            db.commit()
            
            return JSONResponse(content={
                "status": "success",
                "message": "Alert rule updated successfully"
            })
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert rule: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update alert rule")

@router.get("/escalation-rules")
async def get_escalation_rules():
    """Get all escalation rules"""
    try:
        with get_db_session() as db:
            from backend.services.error_tracking_service import EscalationRules
            
            rules = db.query(EscalationRules).all()
            
            rule_data = [{
                'id': rule.id,
                'name': rule.name,
                'description': rule.description,
                'trigger_conditions': rule.trigger_conditions,
                'escalation_levels': rule.escalation_levels,
                'escalation_delays': rule.escalation_delays,
                'is_active': rule.is_active,
                'created_at': rule.created_at.isoformat(),
                'updated_at': rule.updated_at.isoformat()
            } for rule in rules]
            
            return JSONResponse(content={"escalation_rules": rule_data})
            
    except Exception as e:
        logger.error(f"Error getting escalation rules: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get escalation rules")

@router.get("/responses")
async def get_incident_responses(
    incident_id: Optional[str] = Query(None, description="Filter by incident ID"),
    response_type: Optional[str] = Query(None, description="Filter by response type"),
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results")
):
    """Get incident responses"""
    try:
        with get_db_session() as db:
            from backend.services.error_tracking_service import IncidentResponse
            
            start_date = datetime.utcnow() - timedelta(days=days)
            query = db.query(IncidentResponse).filter(
                IncidentResponse.created_at >= start_date
            )
            
            if incident_id:
                query = query.filter(IncidentResponse.incident_id == incident_id)
            if response_type:
                query = query.filter(IncidentResponse.response_type == response_type)
            
            responses = query.order_by(IncidentResponse.created_at.desc()).limit(limit).all()
            
            response_data = [{
                'id': response.id,
                'incident_id': response.incident_id,
                'response_type': response.response_type,
                'action_taken': response.action_taken,
                'response_time': response.response_time,
                'success': response.success,
                'error_message': response.error_message,
                'responder': response.responder,
                'created_at': response.created_at.isoformat()
            } for response in responses]
            
            return JSONResponse(content={"responses": response_data})
            
    except Exception as e:
        logger.error(f"Error getting incident responses: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get incident responses")

@router.post("/test-notification")
async def test_notification(
    channel: str,
    title: str = "Test Notification",
    message: str = "This is a test notification",
    severity: str = "medium"
):
    """Test notification channel"""
    try:
        from backend.services.error_tracking_service import NotificationChannel, AlertSeverity
        
        notification_channel = NotificationChannel(channel)
        alert_severity = AlertSeverity(severity)
        
        error_tracking_service._send_notification(
            notification_channel, title, message, alert_severity
        )
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Test notification sent via {channel}"
        })
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid channel or severity: {str(e)}")
    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send test notification")
    title: str
    description: str
    severity: str = "medium"
    category: str = "general"
    feature_name: Optional[str] = None
    browser_info: Optional[Dict[str, Any]] = None
    steps_to_reproduce: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None

@router.post("/errors/report")
async def report_error(error_report: ErrorReportRequest, request: Request):
    """Report an error manually"""
    try:
        # Validate severity and category
        try:
            severity = ErrorSeverity(error_report.severity.lower())
            category = ErrorCategory(error_report.category.lower())
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid severity or category: {str(e)}")
        
        # Create error context
        context = ErrorContext(
            user_id=error_report.user_id,
            session_id=error_report.session_id,
            feature_name=error_report.feature_name,
            operation=error_report.operation,
            user_agent=request.headers.get('user-agent'),
            ip_address=request.client.host if request.client else None,
            additional_data=error_report.context_data
        )
        
        # Create a mock exception for tracking
        class ReportedError(Exception):
            pass
        
        mock_error = ReportedError(error_report.error_message)
        mock_error.__class__.__name__ = error_report.error_type
        
        # Track the error
        error_id = error_tracking_service.track_error(mock_error, context, severity, category)
        
        if error_id:
            return JSONResponse(content={
                "message": "Error reported successfully",
                "error_id": error_id,
                "severity": severity.value,
                "category": category.value
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to report error")
            
    except Exception as e:
        logger.error(f"Error reporting error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to report error")

@router.get("/errors/analytics")
async def get_error_analytics(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """Get error analytics and trends"""
    try:
        analytics = error_tracking_service.get_error_analytics(days)
        return JSONResponse(content=analytics)
    except Exception as e:
        logger.error(f"Error getting error analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get error analytics")

@router.get("/errors")
async def get_errors(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    category: Optional[str] = Query(None, description="Filter by category"),
    feature_name: Optional[str] = Query(None, description="Filter by feature"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results")
):
    """Get error records with filtering"""
    try:
        with get_db_session() as session:
            from backend.services.error_tracking_service import ErrorRecord
            
            start_date = datetime.utcnow() - timedelta(days=days)
            query = session.query(ErrorRecord).filter(
                ErrorRecord.created_at >= start_date
            )
            
            if severity:
                query = query.filter(ErrorRecord.severity == severity)
            if category:
                query = query.filter(ErrorRecord.category == category)
            if feature_name:
                query = query.filter(ErrorRecord.feature_name == feature_name)
            if resolved is not None:
                query = query.filter(ErrorRecord.resolved == resolved)
            
            errors = query.order_by(ErrorRecord.created_at.desc()).limit(limit).all()
            
            error_data = [{
                'id': error.id,
                'error_hash': error.error_hash,
                'error_type': error.error_type,
                'error_message': error.error_message,
                'severity': error.severity,
                'category': error.category,
                'feature_name': error.feature_name,
                'operation': error.operation,
                'user_id': error.user_id,
                'occurrence_count': error.occurrence_count,
                'resolved': error.resolved,
                'first_seen': error.first_seen.isoformat(),
                'last_seen': error.last_seen.isoformat(),
                'created_at': error.created_at.isoformat()
            } for error in errors]
            
            return JSONResponse(content=error_data)
            
    except Exception as e:
        logger.error(f"Error getting errors: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get errors")

@router.get("/errors/{error_id}")
async def get_error_details(error_id: str):
    """Get detailed information about a specific error"""
    try:
        with get_db_session() as session:
            from backend.services.error_tracking_service import ErrorRecord
            
            error = session.query(ErrorRecord).filter_by(id=error_id).first()
            if not error:
                raise HTTPException(status_code=404, detail="Error not found")
            
            error_data = {
                'id': error.id,
                'error_hash': error.error_hash,
                'error_type': error.error_type,
                'error_message': error.error_message,
                'stack_trace': error.stack_trace,
                'severity': error.severity,
                'category': error.category,
                'feature_name': error.feature_name,
                'operation': error.operation,
                'user_id': error.user_id,
                'session_id': error.session_id,
                'request_id': error.request_id,
                'user_agent': error.user_agent,
                'ip_address': error.ip_address,
                'context_data': error.context_data,
                'occurrence_count': error.occurrence_count,
                'resolved': error.resolved,
                'resolved_at': error.resolved_at.isoformat() if error.resolved_at else None,
                'first_seen': error.first_seen.isoformat(),
                'last_seen': error.last_seen.isoformat(),
                'created_at': error.created_at.isoformat()
            }
            
            return JSONResponse(content=error_data)
            
    except Exception as e:
        logger.error(f"Error getting error details: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get error details")

@router.put("/errors/{error_id}/resolve")
async def resolve_error(error_id: str):
    """Mark an error as resolved"""
    try:
        with get_db_session() as session:
            from backend.services.error_tracking_service import ErrorRecord
            
            error = session.query(ErrorRecord).filter_by(id=error_id).first()
            if not error:
                raise HTTPException(status_code=404, detail="Error not found")
            
            error.resolved = True
            error.resolved_at = datetime.utcnow()
            session.commit()
            
            return JSONResponse(content={
                "message": "Error resolved successfully",
                "error_id": error_id
            })
            
    except Exception as e:
        logger.error(f"Error resolving error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to resolve error")

@router.post("/incidents")
async def create_incident(incident_request: IncidentCreateRequest):
    """Create a new incident"""
    try:
        # Validate severity and category
        try:
            severity = ErrorSeverity(incident_request.severity.lower())
            category = ErrorCategory(incident_request.category.lower())
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid severity or category: {str(e)}")
        
        incident_id = error_tracking_service.create_incident(
            title=incident_request.title,
            description=incident_request.description,
            severity=severity,
            category=category,
            affected_features=incident_request.affected_features,
            assigned_to=incident_request.assigned_to
        )
        
        if incident_id:
            return JSONResponse(content={
                "message": "Incident created successfully",
                "incident_id": incident_id
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to create incident")
            
    except Exception as e:
        logger.error(f"Error creating incident: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create incident")

@router.get("/incidents")
async def get_incidents(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results")
):
    """Get incidents with filtering"""
    try:
        with get_db_session() as session:
            from backend.services.error_tracking_service import Incident
            
            start_date = datetime.utcnow() - timedelta(days=days)
            query = session.query(Incident).filter(
                Incident.created_at >= start_date
            )
            
            if status:
                query = query.filter(Incident.status == status)
            if severity:
                query = query.filter(Incident.severity == severity)
            if assigned_to:
                query = query.filter(Incident.assigned_to == assigned_to)
            
            incidents = query.order_by(Incident.created_at.desc()).limit(limit).all()
            
            incident_data = [{
                'id': incident.id,
                'title': incident.title,
                'description': incident.description,
                'severity': incident.severity,
                'status': incident.status,
                'category': incident.category,
                'affected_features': incident.affected_features,
                'assigned_to': incident.assigned_to,
                'created_by': incident.created_by,
                'created_at': incident.created_at.isoformat(),
                'updated_at': incident.updated_at.isoformat(),
                'resolved_at': incident.resolved_at.isoformat() if incident.resolved_at else None
            } for incident in incidents]
            
            return JSONResponse(content=incident_data)
            
    except Exception as e:
        logger.error(f"Error getting incidents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get incidents")

@router.get("/incidents/{incident_id}")
async def get_incident_details(incident_id: str):
    """Get detailed information about a specific incident"""
    try:
        with get_db_session() as session:
            from backend.services.error_tracking_service import Incident
            
            incident = session.query(Incident).filter_by(id=incident_id).first()
            if not incident:
                raise HTTPException(status_code=404, detail="Incident not found")
            
            incident_data = {
                'id': incident.id,
                'title': incident.title,
                'description': incident.description,
                'severity': incident.severity,
                'status': incident.status,
                'category': incident.category,
                'affected_features': incident.affected_features,
                'error_records': incident.error_records,
                'assigned_to': incident.assigned_to,
                'created_by': incident.created_by,
                'created_at': incident.created_at.isoformat(),
                'updated_at': incident.updated_at.isoformat(),
                'resolved_at': incident.resolved_at.isoformat() if incident.resolved_at else None,
                'resolution_notes': incident.resolution_notes,
                'impact_assessment': incident.impact_assessment,
                'timeline': incident.timeline
            }
            
            return JSONResponse(content=incident_data)
            
    except Exception as e:
        logger.error(f"Error getting incident details: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get incident details")

@router.put("/incidents/{incident_id}")
async def update_incident(incident_id: str, update_request: IncidentUpdateRequest):
    """Update an incident"""
    try:
        status = None
        if update_request.status:
            try:
                status = IncidentStatus(update_request.status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid incident status")
        
        success = error_tracking_service.update_incident(
            incident_id=incident_id,
            status=status,
            assigned_to=update_request.assigned_to,
            resolution_notes=update_request.resolution_notes,
            update_description=update_request.update_description
        )
        
        if success:
            return JSONResponse(content={
                "message": "Incident updated successfully",
                "incident_id": incident_id
            })
        else:
            raise HTTPException(status_code=404, detail="Incident not found")
            
    except Exception as e:
        logger.error(f"Error updating incident: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update incident")

@router.get("/incidents/summary")
async def get_incident_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get incident summary and metrics"""
    try:
        summary = error_tracking_service.get_incident_summary(days)
        return JSONResponse(content=summary)
    except Exception as e:
        logger.error(f"Error getting incident summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get incident summary")

@router.post("/feedback")
async def submit_user_feedback(feedback_request: UserFeedbackRequest, request: Request):
    """Submit user feedback or bug report"""
    try:
        # Extract user ID from request (would typically come from authentication)
        user_id = request.headers.get('x-user-id', 'anonymous')
        
        # Validate severity
        try:
            severity = ErrorSeverity(feedback_request.severity.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid severity")
        
        # Collect browser info if not provided
        browser_info = feedback_request.browser_info or {
            'user_agent': request.headers.get('user-agent'),
            'referer': request.headers.get('referer')
        }
        
        feedback_id = error_tracking_service.collect_user_feedback(
            user_id=user_id,
            feedback_type=feedback_request.feedback_type,
            title=feedback_request.title,
            description=feedback_request.description,
            severity=severity,
            category=feedback_request.category,
            feature_name=feedback_request.feature_name,
            browser_info=browser_info,
            steps_to_reproduce=feedback_request.steps_to_reproduce,
            expected_behavior=feedback_request.expected_behavior,
            actual_behavior=feedback_request.actual_behavior
        )
        
        if feedback_id:
            return JSONResponse(content={
                "message": "Feedback submitted successfully",
                "feedback_id": feedback_id,
                "type": feedback_request.feedback_type
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to submit feedback")
            
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@router.get("/feedback")
async def get_user_feedback(
    feedback_type: Optional[str] = Query(None, description="Filter by feedback type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results")
):
    """Get user feedback with filtering"""
    try:
        with get_db_session() as session:
            from backend.services.error_tracking_service import UserFeedback
            
            start_date = datetime.utcnow() - timedelta(days=days)
            query = session.query(UserFeedback).filter(
                UserFeedback.created_at >= start_date
            )
            
            if feedback_type:
                query = query.filter(UserFeedback.feedback_type == feedback_type)
            if status:
                query = query.filter(UserFeedback.status == status)
            if severity:
                query = query.filter(UserFeedback.severity == severity)
            
            feedback_records = query.order_by(UserFeedback.created_at.desc()).limit(limit).all()
            
            feedback_data = [{
                'id': feedback.id,
                'user_id': feedback.user_id,
                'feedback_type': feedback.feedback_type,
                'title': feedback.title,
                'description': feedback.description,
                'severity': feedback.severity,
                'category': feedback.category,
                'feature_name': feedback.feature_name,
                'status': feedback.status,
                'assigned_to': feedback.assigned_to,
                'created_at': feedback.created_at.isoformat(),
                'updated_at': feedback.updated_at.isoformat(),
                'resolved_at': feedback.resolved_at.isoformat() if feedback.resolved_at else None
            } for feedback in feedback_records]
            
            return JSONResponse(content=feedback_data)
            
    except Exception as e:
        logger.error(f"Error getting user feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user feedback")

@router.get("/feedback/{feedback_id}")
async def get_feedback_details(feedback_id: str):
    """Get detailed information about specific feedback"""
    try:
        with get_db_session() as session:
            from backend.services.error_tracking_service import UserFeedback
            
            feedback = session.query(UserFeedback).filter_by(id=feedback_id).first()
            if not feedback:
                raise HTTPException(status_code=404, detail="Feedback not found")
            
            feedback_data = {
                'id': feedback.id,
                'user_id': feedback.user_id,
                'feedback_type': feedback.feedback_type,
                'title': feedback.title,
                'description': feedback.description,
                'severity': feedback.severity,
                'category': feedback.category,
                'feature_name': feedback.feature_name,
                'browser_info': feedback.browser_info,
                'steps_to_reproduce': feedback.steps_to_reproduce,
                'expected_behavior': feedback.expected_behavior,
                'actual_behavior': feedback.actual_behavior,
                'attachments': feedback.attachments,
                'status': feedback.status,
                'assigned_to': feedback.assigned_to,
                'created_at': feedback.created_at.isoformat(),
                'updated_at': feedback.updated_at.isoformat(),
                'resolved_at': feedback.resolved_at.isoformat() if feedback.resolved_at else None,
                'resolution_notes': feedback.resolution_notes
            }
            
            return JSONResponse(content=feedback_data)
            
    except Exception as e:
        logger.error(f"Error getting feedback details: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get feedback details")

@router.get("/dashboard/summary")
async def get_error_dashboard_summary():
    """Get comprehensive error tracking dashboard summary"""
    try:
        # Get error analytics
        error_analytics = error_tracking_service.get_error_analytics(days=7)
        
        # Get incident summary
        incident_summary = error_tracking_service.get_incident_summary(days=30)
        
        # Get recent critical errors
        with get_db_session() as session:
            from backend.services.error_tracking_service import ErrorRecord
            
            recent_critical = session.query(ErrorRecord).filter(
                ErrorRecord.severity == ErrorSeverity.CRITICAL.value,
                ErrorRecord.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
        
        dashboard_data = {
            'error_analytics': error_analytics,
            'incident_summary': incident_summary,
            'recent_critical_errors': recent_critical,
            'system_health': {
                'error_rate_trend': 'stable',  # Would calculate from historical data
                'resolution_efficiency': incident_summary.get('resolution_rate', 0),
                'alert_status': 'normal'  # Would check current alert conditions
            }
        }
        
        return JSONResponse(content=dashboard_data)
        
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard summary")