"""
Research Workflow Automation API Endpoints
Provides endpoints for creating and managing automated research workflows.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from core.auth import get_current_user
from models.schemas import User
from services.research_automation import (
    ResearchAutomationService, AutomatedWorkflow,
    WorkflowType, WorkflowStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/automation", tags=["automation"])

# Request/Response Models
class CreateWorkflowRequest(BaseModel):
    name: str
    workflow_type: WorkflowType
    description: str
    configuration: Dict[str, Any]
    schedule_config: Dict[str, Any]

class WorkflowResponse(BaseModel):
    id: str
    name: str
    workflow_type: str
    description: str
    status: str
    created_at: str
    last_run: Optional[str]
    next_run: Optional[str]
    run_count: int
    success_count: int
    failure_count: int
    success_rate: float

class WorkflowExecutionRequest(BaseModel):
    workflow_id: str
    manual_trigger: bool = True

# Endpoints

@router.post("/workflows/create", response_model=WorkflowResponse)
async def create_automated_workflow(
    request: CreateWorkflowRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new automated research workflow"""
    try:
        automation_service = ResearchAutomationService(db)
        
        workflow = await automation_service.create_automated_workflow(
            user_id=current_user.id,
            name=request.name,
            workflow_type=request.workflow_type,
            description=request.description,
            configuration=request.configuration,
            schedule_config=request.schedule_config
        )
        
        success_rate = (workflow.success_count / max(1, workflow.run_count)) * 100
        
        return WorkflowResponse(
            id=workflow.id,
            name=workflow.name,
            workflow_type=workflow.workflow_type.value,
            description=workflow.description,
            status=workflow.status.value,
            created_at=workflow.created_at.isoformat(),
            last_run=workflow.last_run.isoformat() if workflow.last_run else None,
            next_run=workflow.next_run.isoformat() if workflow.next_run else None,
            run_count=workflow.run_count,
            success_count=workflow.success_count,
            failure_count=workflow.failure_count,
            success_rate=success_rate
        )
        
    except Exception as e:
        logger.error(f"Error creating automated workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflows/execute", response_model=Dict[str, Any])
async def execute_workflow(
    request: WorkflowExecutionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a research workflow manually"""
    try:
        automation_service = ResearchAutomationService(db)
        
        result = await automation_service.execute_workflow(
            workflow_id=request.workflow_id,
            manual_trigger=request.manual_trigger
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows", response_model=List[WorkflowResponse])
async def get_user_workflows(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's automated workflows"""
    try:
        automation_service = ResearchAutomationService(db)
        
        user_workflows = []
        for workflow in automation_service.active_workflows.values():
            if workflow.user_id == current_user.id:
                success_rate = (workflow.success_count / max(1, workflow.run_count)) * 100
                
                user_workflows.append(WorkflowResponse(
                    id=workflow.id,
                    name=workflow.name,
                    workflow_type=workflow.workflow_type.value,
                    description=workflow.description,
                    status=workflow.status.value,
                    created_at=workflow.created_at.isoformat(),
                    last_run=workflow.last_run.isoformat() if workflow.last_run else None,
                    next_run=workflow.next_run.isoformat() if workflow.next_run else None,
                    run_count=workflow.run_count,
                    success_count=workflow.success_count,
                    failure_count=workflow.failure_count,
                    success_rate=success_rate
                ))
        
        return user_workflows
        
    except Exception as e:
        logger.error(f"Error getting user workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows/{workflow_id}", response_model=Dict[str, Any])
async def get_workflow_details(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a workflow"""
    try:
        automation_service = ResearchAutomationService(db)
        
        workflow = automation_service.active_workflows.get(workflow_id)
        if not workflow or workflow.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        success_rate = (workflow.success_count / max(1, workflow.run_count)) * 100
        
        return {
            "id": workflow.id,
            "name": workflow.name,
            "workflow_type": workflow.workflow_type.value,
            "description": workflow.description,
            "configuration": workflow.configuration,
            "schedule": workflow.schedule,
            "status": workflow.status.value,
            "created_at": workflow.created_at.isoformat(),
            "last_run": workflow.last_run.isoformat() if workflow.last_run else None,
            "next_run": workflow.next_run.isoformat() if workflow.next_run else None,
            "run_count": workflow.run_count,
            "success_count": workflow.success_count,
            "failure_count": workflow.failure_count,
            "success_rate": success_rate,
            "recent_results": workflow.results[-10:]  # Last 10 results
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/workflows/{workflow_id}/status")
async def update_workflow_status(
    workflow_id: str,
    status: WorkflowStatus = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update workflow status (pause/resume/stop)"""
    try:
        automation_service = ResearchAutomationService(db)
        
        workflow = automation_service.active_workflows.get(workflow_id)
        if not workflow or workflow.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        workflow.status = status
        
        return {"message": f"Workflow status updated to {status.value}"}
        
    except Exception as e:
        logger.error(f"Error updating workflow status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow-types", response_model=List[Dict[str, str]])
async def get_workflow_types():
    """Get available workflow types"""
    try:
        types = []
        
        type_descriptions = {
            WorkflowType.LITERATURE_MONITORING: "Automated monitoring of new literature and papers",
            WorkflowType.CITATION_MANAGEMENT: "Automatic citation generation and bibliography management",
            WorkflowType.DATA_COLLECTION: "Automated data collection and processing",
            WorkflowType.ANALYSIS_PIPELINE: "Automated analysis pipelines and processing",
            WorkflowType.REPORT_GENERATION: "Automated report and summary generation",
            WorkflowType.PEER_REVIEW: "Automated peer review assistance and feedback"
        }
        
        for workflow_type in WorkflowType:
            types.append({
                "value": workflow_type.value,
                "name": workflow_type.value.replace("_", " ").title(),
                "description": type_descriptions.get(workflow_type, "Automated workflow type")
            })
        
        return types
        
    except Exception as e:
        logger.error(f"Error getting workflow types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates/{workflow_type}", response_model=Dict[str, Any])
async def get_workflow_template(
    workflow_type: WorkflowType
):
    """Get configuration template for a workflow type"""
    try:
        templates = {
            WorkflowType.LITERATURE_MONITORING: {
                "configuration": {
                    "search_terms": ["machine learning", "artificial intelligence"],
                    "domains": ["computer_science", "engineering"],
                    "max_papers_per_run": 20,
                    "min_relevance_score": 0.7
                },
                "schedule_config": {
                    "type": "daily",
                    "time": "09:00",
                    "timezone": "UTC"
                }
            },
            WorkflowType.CITATION_MANAGEMENT: {
                "configuration": {
                    "citation_style": "APA",
                    "include_abstracts": True,
                    "auto_format": True,
                    "export_format": "bibtex"
                },
                "schedule_config": {
                    "type": "weekly",
                    "day": "sunday",
                    "time": "10:00"
                }
            },
            WorkflowType.DATA_COLLECTION: {
                "configuration": {
                    "collection_type": "documents",
                    "auto_process": True,
                    "quality_threshold": 0.8,
                    "max_files_per_run": 50
                },
                "schedule_config": {
                    "type": "daily",
                    "time": "02:00"
                }
            },
            WorkflowType.ANALYSIS_PIPELINE: {
                "configuration": {
                    "analysis_type": "topic_modeling",
                    "n_topics": 5,
                    "auto_tag": True,
                    "update_knowledge_graph": True
                },
                "schedule_config": {
                    "type": "weekly",
                    "day": "monday",
                    "time": "08:00"
                }
            },
            WorkflowType.REPORT_GENERATION: {
                "configuration": {
                    "report_type": "summary",
                    "timeframe": "week",
                    "include_analytics": True,
                    "export_format": "pdf"
                },
                "schedule_config": {
                    "type": "weekly",
                    "day": "friday",
                    "time": "17:00"
                }
            }
        }
        
        template = templates.get(workflow_type)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return template
        
    except Exception as e:
        logger.error(f"Error getting workflow template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/workflows", response_model=Dict[str, Any])
async def get_workflow_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365)
):
    """Get workflow analytics for user"""
    try:
        automation_service = ResearchAutomationService(db)
        
        # Get user's workflows
        user_workflows = [
            w for w in automation_service.active_workflows.values()
            if w.user_id == current_user.id
        ]
        
        # Calculate analytics
        analytics = {
            "total_workflows": len(user_workflows),
            "active_workflows": len([w for w in user_workflows if w.status == WorkflowStatus.ACTIVE]),
            "total_executions": sum(w.run_count for w in user_workflows),
            "total_successes": sum(w.success_count for w in user_workflows),
            "overall_success_rate": 0,
            "workflow_types": {},
            "execution_trends": {},
            "most_successful_workflow": None,
            "recommendations": []
        }
        
        if analytics["total_executions"] > 0:
            analytics["overall_success_rate"] = (analytics["total_successes"] / analytics["total_executions"]) * 100
        
        # Workflow type distribution
        type_counts = {}
        for workflow in user_workflows:
            wf_type = workflow.workflow_type.value
            type_counts[wf_type] = type_counts.get(wf_type, 0) + 1
        analytics["workflow_types"] = type_counts
        
        # Find most successful workflow
        if user_workflows:
            most_successful = max(
                user_workflows,
                key=lambda w: (w.success_count / max(1, w.run_count)) * 100
            )
            analytics["most_successful_workflow"] = {
                "name": most_successful.name,
                "type": most_successful.workflow_type.value,
                "success_rate": (most_successful.success_count / max(1, most_successful.run_count)) * 100
            }
        
        # Generate recommendations
        recommendations = []
        if analytics["total_workflows"] == 0:
            recommendations.append("Create your first automated workflow to streamline research tasks")
        elif analytics["overall_success_rate"] < 80:
            recommendations.append("Review workflow configurations to improve success rates")
        elif analytics["active_workflows"] < analytics["total_workflows"]:
            recommendations.append("Consider reactivating paused workflows that were performing well")
        
        analytics["recommendations"] = recommendations
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting workflow analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for automation service"""
    try:
        return {
            "status": "healthy",
            "service": "research_automation",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "workflow_automation",
                "literature_monitoring",
                "citation_management",
                "data_collection",
                "analysis_pipelines",
                "report_generation"
            ]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Service unhealthy")