"""
API endpoints for compliance monitoring and institutional features
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from core.database import get_db
from services.compliance_monitoring_service import ComplianceMonitoringService

router = APIRouter(prefix="/api/compliance", tags=["compliance"])
compliance_service = ComplianceMonitoringService()

# Request/Response Models
class ComplianceCheckRequest(BaseModel):
    user_id: str
    action: str
    context: Dict[str, Any]

class ComplianceCheckResponse(BaseModel):
    compliant: bool
    violations: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    institution_id: Optional[str]

class ResearchProposalRequest(BaseModel):
    user_id: str
    content: str
    title: str
    research_type: str

class EthicalComplianceResponse(BaseModel):
    compliant: bool
    ethical_issues: List[Dict[str, Any]]
    requires_review: bool

class ViolationResponse(BaseModel):
    critical: List[Dict[str, Any]]
    high: List[Dict[str, Any]]
    medium: List[Dict[str, Any]]
    low: List[Dict[str, Any]]

class ComplianceDashboardResponse(BaseModel):
    violation_statistics: Dict[str, int]
    compliance_rate: float
    total_checks: int
    recent_violations: List[Dict[str, Any]]
    policy_effectiveness: List[Dict[str, Any]]
    generated_at: datetime

@router.post("/check-guidelines", response_model=ComplianceCheckResponse)
async def check_institutional_guidelines(
    request: ComplianceCheckRequest,
    db: Session = Depends(get_db)
):
    """Check if user action complies with institutional guidelines"""
    try:
        result = await compliance_service.check_institutional_guidelines(
            request.user_id, request.action, request.context
        )
        return ComplianceCheckResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance check failed: {str(e)}")

@router.post("/check-ethics", response_model=EthicalComplianceResponse)
async def monitor_ethical_compliance(
    request: ResearchProposalRequest,
    db: Session = Depends(get_db)
):
    """Monitor research proposals for ethical compliance"""
    try:
        research_proposal = {
            "user_id": request.user_id,
            "content": request.content,
            "title": request.title,
            "research_type": request.research_type
        }
        
        result = await compliance_service.monitor_ethical_compliance(research_proposal)
        return EthicalComplianceResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ethics check failed: {str(e)}")

@router.get("/violations/{institution_id}", response_model=ViolationResponse)
async def get_compliance_violations(
    institution_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get compliance violations for an institution"""
    try:
        time_range = {}
        if start_date:
            time_range['start'] = start_date
        if end_date:
            time_range['end'] = end_date
        
        violations = await compliance_service.detect_violations(
            institution_id, time_range if time_range else None
        )
        return ViolationResponse(**violations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get violations: {str(e)}")

@router.get("/dashboard/{institution_id}")
async def get_compliance_dashboard(
    institution_id: str,
    db: Session = Depends(get_db)
):
    """Get enhanced real-time compliance dashboard data"""
    try:
        dashboard_data = await compliance_service.generate_compliance_dashboard_data(institution_id)
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard: {str(e)}")

@router.get("/dashboard/{institution_id}/real-time")
async def get_real_time_compliance_status(
    institution_id: str,
    db: Session = Depends(get_db)
):
    """Get real-time compliance status for live monitoring"""
    try:
        # Get critical violations in the last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        from core.database import ComplianceViolation
        
        recent_critical = db.query(ComplianceViolation).filter(
            and_(
                ComplianceViolation.institution_id == institution_id,
                ComplianceViolation.severity == 'critical',
                ComplianceViolation.detected_at >= one_hour_ago,
                ComplianceViolation.resolution_status == 'open'
            )
        ).all()
        
        return {
            "status": "critical" if recent_critical else "normal",
            "critical_violations": len(recent_critical),
            "alerts": [
                {
                    "id": v.id,
                    "description": v.description,
                    "detected_at": v.detected_at,
                    "user_id": v.user_id
                } for v in recent_critical
            ],
            "last_updated": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get real-time status: {str(e)}")

@router.post("/violations/bulk-resolve")
async def bulk_resolve_violations(
    violation_ids: List[str],
    resolution_notes: str,
    db: Session = Depends(get_db)
):
    """Bulk resolve multiple violations"""
    try:
        from core.database import ComplianceViolation
        
        resolved_count = 0
        for violation_id in violation_ids:
            violation = db.query(ComplianceViolation).filter(
                ComplianceViolation.id == violation_id
            ).first()
            
            if violation:
                violation.resolution_status = 'resolved'
                violation.resolution_notes = resolution_notes
                violation.resolved_at = datetime.now()
                resolved_count += 1
        
        db.commit()
        
        return {
            "message": f"Successfully resolved {resolved_count} violations",
            "resolved_count": resolved_count,
            "total_requested": len(violation_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk resolve violations: {str(e)}")

@router.get("/analytics/{institution_id}")
async def get_compliance_analytics(
    institution_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get detailed compliance analytics"""
    try:
        time_range = {
            'start': datetime.now() - timedelta(days=days),
            'end': datetime.now()
        }
        
        violations_data = await compliance_service.detect_violations(institution_id, time_range)
        
        return {
            "period_days": days,
            "violations_analysis": violations_data,
            "generated_at": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.post("/policies/{policy_id}/test")
async def test_policy(
    policy_id: str,
    test_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Test a policy against sample data"""
    try:
        from core.database import InstitutionalPolicy
        
        policy = db.query(InstitutionalPolicy).filter(
            InstitutionalPolicy.id == policy_id
        ).first()
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Test the policy
        result = await compliance_service._check_policy_compliance(
            policy, 
            test_data.get('user_id', 'test_user'),
            test_data.get('action', 'test_action'),
            test_data.get('context', {}),
            db
        )
        
        return {
            "policy_id": policy_id,
            "policy_name": policy.policy_name,
            "test_result": result,
            "tested_at": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test policy: {str(e)}")

@router.post("/violations/{violation_id}/resolve")
async def resolve_violation(
    violation_id: str,
    resolution_notes: str,
    db: Session = Depends(get_db)
):
    """Mark a compliance violation as resolved"""
    try:
        from core.database import ComplianceViolation
        
        violation = db.query(ComplianceViolation).filter(
            ComplianceViolation.id == violation_id
        ).first()
        
        if not violation:
            raise HTTPException(status_code=404, detail="Violation not found")
        
        violation.resolution_status = 'resolved'
        violation.resolution_notes = resolution_notes
        violation.resolved_at = datetime.now()
        
        db.commit()
        
        return {"message": "Violation resolved successfully", "violation_id": violation_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve violation: {str(e)}")

@router.get("/policies/{institution_id}")
async def get_institutional_policies(
    institution_id: str,
    db: Session = Depends(get_db)
):
    """Get all policies for an institution"""
    try:
        from core.database import InstitutionalPolicy
        
        policies = db.query(InstitutionalPolicy).filter(
            InstitutionalPolicy.institution_id == institution_id
        ).all()
        
        return [
            {
                "id": policy.id,
                "policy_name": policy.policy_name,
                "policy_type": policy.policy_type,
                "description": policy.description,
                "enforcement_level": policy.enforcement_level,
                "is_active": policy.is_active,
                "effective_date": policy.effective_date,
                "rules": policy.rules
            }
            for policy in policies
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get policies: {str(e)}")

@router.post("/policies")
async def create_institutional_policy(
    policy_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a new institutional policy"""
    try:
        from core.database import InstitutionalPolicy
        
        policy = InstitutionalPolicy(
            institution_id=policy_data['institution_id'],
            policy_name=policy_data['policy_name'],
            policy_type=policy_data['policy_type'],
            description=policy_data.get('description'),
            rules=policy_data.get('rules', {}),
            enforcement_level=policy_data.get('enforcement_level', 'warning')
        )
        
        db.add(policy)
        db.commit()
        db.refresh(policy)
        
        return {
            "message": "Policy created successfully",
            "policy_id": policy.id,
            "policy_name": policy.policy_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create policy: {str(e)}")

@router.put("/policies/{policy_id}")
async def update_institutional_policy(
    policy_id: str,
    policy_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update an institutional policy"""
    try:
        from core.database import InstitutionalPolicy
        
        policy = db.query(InstitutionalPolicy).filter(
            InstitutionalPolicy.id == policy_id
        ).first()
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Update policy fields
        for field, value in policy_data.items():
            if hasattr(policy, field):
                setattr(policy, field, value)
        
        policy.updated_at = datetime.now()
        db.commit()
        
        return {"message": "Policy updated successfully", "policy_id": policy_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update policy: {str(e)}")

@router.delete("/policies/{policy_id}")
async def delete_institutional_policy(
    policy_id: str,
    db: Session = Depends(get_db)
):
    """Delete an institutional policy"""
    try:
        from core.database import InstitutionalPolicy
        
        policy = db.query(InstitutionalPolicy).filter(
            InstitutionalPolicy.id == policy_id
        ).first()
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Soft delete by marking as inactive
        policy.is_active = False
        policy.updated_at = datetime.now()
        db.commit()
        
        return {"message": "Policy deleted successfully", "policy_id": policy_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete policy: {str(e)}")

@router.get("/audit-logs/{institution_id}")
async def get_audit_logs(
    institution_id: str,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    action_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get audit logs for an institution"""
    try:
        from core.database import AuditLog
        
        query = db.query(AuditLog).filter(
            AuditLog.institution_id == institution_id
        )
        
        if action_filter:
            query = query.filter(AuditLog.action.contains(action_filter))
        
        logs = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
        
        return [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "success": log.success,
                "timestamp": log.timestamp,
                "ip_address": log.ip_address,
                "error_message": log.error_message
            }
            for log in logs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit logs: {str(e)}")