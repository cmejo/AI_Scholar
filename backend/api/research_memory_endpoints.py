"""
Research Memory API Endpoints
Provides endpoints for research context persistence, project management,
timeline generation, and intelligent context switching.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from core.auth import get_current_user, User
from services.research_memory_engine import (
    ResearchMemoryEngine, ResearchContextData, ResearchProjectSummary,
    ResearchTimelineEvent, ContextSwitchRecommendation, ProjectStatus, TimelineEventType
)

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Pydantic models
class CreateProjectRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(default="", max_length=2000)
    research_domain: str = Field(default="general", max_length=200)

class SaveContextRequest(BaseModel):
    project_id: str
    session_id: Optional[str] = None
    active_documents: List[str] = Field(default_factory=list)
    current_queries: List[str] = Field(default_factory=list)
    research_focus: str = Field(default="", max_length=1000)
    insights_generated: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class UpdateFocusRequest(BaseModel):
    project_id: str
    new_focus: str = Field(..., max_length=1000)

class AddInsightRequest(BaseModel):
    project_id: str
    insight: Dict[str, Any]

class ProjectResponse(BaseModel):
    id: str
    title: str
    description: str
    research_domain: str
    status: str
    created_at: datetime
    updated_at: datetime

class ProjectSummaryResponse(BaseModel):
    id: str
    title: str
    description: str
    research_domain: str
    status: str
    created_at: datetime
    updated_at: datetime
    document_count: int
    insight_count: int
    milestone_progress: float
    last_activity: datetime

class ContextResponse(BaseModel):
    project_id: str
    user_id: str
    session_id: str
    active_documents: List[str]
    current_queries: List[str]
    research_focus: str
    insights_generated: List[Dict[str, Any]]
    context_metadata: Dict[str, Any]
    session_timestamp: datetime
    is_active: bool

class TimelineEventResponse(BaseModel):
    id: str
    project_id: str
    event_type: str
    event_description: str
    event_data: Dict[str, Any]
    timestamp: datetime

class ContextSwitchResponse(BaseModel):
    target_project_id: str
    target_project_title: str
    relevance_score: float
    switch_reason: str
    related_insights: List[str]
    estimated_context_load_time: int

class ProjectInsightsSummaryResponse(BaseModel):
    project_id: str
    project_title: str
    status: str
    last_updated: str
    current_focus: str
    active_documents: int
    recent_insights: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    analytics_insights: List[Dict[str, Any]]
    research_domain: str
    progress_indicators: Dict[str, Any]

# Router setup
router = APIRouter(prefix="/api/v1/research-memory", tags=["Research Memory"])

# Global service instance
memory_service: Optional[ResearchMemoryEngine] = None

def get_memory_service(db: Session = Depends(get_db)) -> ResearchMemoryEngine:
    """Get research memory service instance"""
    global memory_service
    if memory_service is None:
        memory_service = ResearchMemoryEngine(db)
    return memory_service

# Project management endpoints
@router.post("/projects", response_model=ProjectResponse)
async def create_research_project(
    request: CreateProjectRequest,
    current_user: User = Depends(get_current_user),
    service: ResearchMemoryEngine = Depends(get_memory_service)
):
    """Create a new research project"""
    try:
        project = await service.create_research_project(
            user_id=str(current_user.id),
            title=request.title,
            description=request.description,
            research_domain=request.research_domain
        )
        
        return ProjectResponse(
            id=str(project.id),
            title=project.title,
            description=project.description or "",
            research_domain=project.research_domain or "general",
            status=project.status,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error creating research project: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create research project")

@router.get("/projects", response_model=List[ProjectSummaryResponse])
async def list_research_projects(
    status: Optional[str] = Query(None, description="Filter by project status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of projects to return"),
    current_user: User = Depends(get_current_user),
    service: ResearchMemoryEngine = Depends(get_memory_service)
):
    """List user's research projects with summaries"""
    try:
        status_filter = None
        if status:
            try:
                status_filter = ProjectStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        projects = await service.list_research_projects(
            user_id=str(current_user.id),
            status_filter=status_filter,
            limit=limit
        )
        
        return [
            ProjectSummaryResponse(
                id=project.id,
                title=project.title,
                description=project.description,
                research_domain=project.research_domain,
                status=project.status.value,
                created_at=project.created_at,
                updated_at=project.updated_at,
                document_count=project.document_count,
                insight_count=project.insight_count,
                milestone_progress=project.milestone_progress,
                last_activity=project.last_activity
            )
            for project in projects
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing research projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list research projects")

@router.get("/projects/{project_id}/summary", response_model=ProjectInsightsSummaryResponse)
async def get_project_insights_summary(
    project_id: str,
    current_user: User = Depends(get_current_user),
    service: ResearchMemoryEngine = Depends(get_memory_service)
):
    """Get comprehensive insights summary for a project"""
    try:
        summary = await service.get_project_insights_summary(
            user_id=str(current_user.id),
            project_id=project_id
        )
        
        if not summary:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return ProjectInsightsSummaryResponse(**summary)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project insights summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get project insights summary")

# Context management endpoints
@router.post("/context/save")
async def save_research_context(
    request: SaveContextRequest,
    current_user: User = Depends(get_current_user),
    service: ResearchMemoryEngine = Depends(get_memory_service)
):
    """Save current research context"""
    try:
        context_data = {
            "session_id": request.session_id,
            "active_documents": request.active_documents,
            "current_queries": request.current_queries,
            "research_focus": request.research_focus,
            "insights_generated": request.insights_generated,
            "metadata": request.metadata
        }
        
        success = await service.save_research_context(
            user_id=str(current_user.id),
            project_id=request.project_id,
            context_data=context_data
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save research context")
        
        return {"status": "success", "message": "Research context saved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving research context: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save research context")

@router.get("/context/{project_id}", response_model=ContextResponse)
async def restore_research_context(
    project_id: str,
    current_user: User = Depends(get_current_user),
    service: ResearchMemoryEngine = Depends(get_memory_service)
):
    """Restore research context for a project"""
    try:
        context = await service.restore_research_context(
            user_id=str(current_user.id),
            project_id=project_id
        )
        
        if not context:
            raise HTTPException(status_code=404, detail="Research context not found")
        
        return ContextResponse(
            project_id=context.project_id,
            user_id=context.user_id,
            session_id=context.session_id,
            active_documents=context.active_documents,
            current_queries=context.current_queries,
            research_focus=context.research_focus,
            insights_generated=context.insights_generated,
            context_metadata=context.context_metadata,
            session_timestamp=context.session_timestamp,
            is_active=context.is_active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring research context: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to restore research context")

@router.post("/context/switch")
async def switch_project_context(
    from_project_id: str = Query(..., description="Source project ID"),
    to_project_id: str = Query(..., description="Target project ID"),
    current_user: User = Depends(get_current_user),
    service: ResearchMemoryEngine = Depends(get_memory_service)
):
    """Switch between research project contexts"""
    try:
        success = await service.switch_project_context(
            user_id=str(current_user.id),
            from_project_id=from_project_id,
            to_project_id=to_project_id
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to switch project context")
        
        return {"status": "success", "message": "Project context switched successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching project context: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to switch project context")

@router.get("/context/{project_id}/suggestions", response_model=List[ContextSwitchResponse])
async def suggest_context_switch(
    project_id: str,
    current_user: User = Depends(get_current_user),
    service: ResearchMemoryEngine = Depends(get_memory_service)
):
    """Get context switch suggestions based on current project"""
    try:
        suggestions = await service.suggest_context_switch(
            user_id=str(current_user.id),
            current_project_id=project_id
        )
        
        return [
            ContextSwitchResponse(
                target_project_id=suggestion.target_project_id,
                target_project_title=suggestion.target_project_title,
                relevance_score=suggestion.relevance_score,
                switch_reason=suggestion.switch_reason,
                related_insights=suggestion.related_insights,
                estimated_context_load_time=suggestion.estimated_context_load_time
            )
            for suggestion in suggestions
        ]
        
    except Exception as e:
        logger.error(f"Error getting context switch suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get context switch suggestions")

# Timeline endpoints
@router.get("/timeline/{project_id}", response_model=List[TimelineEventResponse])
async def get_research_timeline(
    project_id: str,
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: User = Depends(get_current_user),
    service: ResearchMemoryEngine = Depends(get_memory_service)
):
    """Get research timeline for a project"""
    try:
        timeline = await service.generate_research_timeline(
            user_id=str(current_user.id),
            project_id=project_id,
            days_back=days_back
        )
        
        return [
            TimelineEventResponse(
                id=event.id,
                project_id=event.project_id,
                event_type=event.event_type.value,
                event_description=event.event_description,
                event_data=event.event_data,
                timestamp=event.timestamp
            )
            for event in timeline
        ]
        
    except Exception as e:
        logger.error(f"Error getting research timeline: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get research timeline")

# Context update endpoints
@router.put("/context/focus")
async def update_research_focus(
    request: UpdateFocusRequest,
    current_user: User = Depends(get_current_user),
    service: ResearchMemoryEngine = Depends(get_memory_service)
):
    """Update research focus for current context"""
    try:
        success = await service.update_research_focus(
            user_id=str(current_user.id),
            project_id=request.project_id,
            new_focus=request.new_focus
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Research context not found")
        
        return {"status": "success", "message": "Research focus updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating research focus: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update research focus")

@router.post("/context/insights")
async def add_insight_to_context(
    request: AddInsightRequest,
    current_user: User = Depends(get_current_user),
    service: ResearchMemoryEngine = Depends(get_memory_service)
):
    """Add new insight to research context"""
    try:
        success = await service.add_insight_to_context(
            user_id=str(current_user.id),
            project_id=request.project_id,
            insight=request.insight
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Research context not found")
        
        return {"status": "success", "message": "Insight added to context successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding insight to context: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add insight to context")

# Utility endpoints
@router.get("/context/{project_id}/active", response_model=ContextResponse)
async def get_active_context(
    project_id: str,
    current_user: User = Depends(get_current_user),
    service: ResearchMemoryEngine = Depends(get_memory_service)
):
    """Get currently active research context"""
    try:
        context = await service.get_active_context(
            user_id=str(current_user.id),
            project_id=project_id
        )
        
        if not context:
            raise HTTPException(status_code=404, detail="Active context not found")
        
        return ContextResponse(
            project_id=context.project_id,
            user_id=context.user_id,
            session_id=context.session_id,
            active_documents=context.active_documents,
            current_queries=context.current_queries,
            research_focus=context.research_focus,
            insights_generated=context.insights_generated,
            context_metadata=context.context_metadata,
            session_timestamp=context.session_timestamp,
            is_active=context.is_active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active context: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get active context")

@router.delete("/context/cleanup")
async def cleanup_old_contexts(
    days_old: int = Query(90, ge=30, le=365, description="Age threshold for cleanup in days"),
    current_user: User = Depends(get_current_user),
    service: ResearchMemoryEngine = Depends(get_memory_service)
):
    """Clean up old inactive contexts"""
    try:
        service.cleanup_old_contexts(days_old=days_old)
        
        return {
            "status": "success",
            "message": f"Cleaned up contexts older than {days_old} days"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old contexts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clean up old contexts")

# Analytics endpoints
@router.get("/analytics/context-patterns")
async def get_context_usage_patterns(
    current_user: User = Depends(get_current_user),
    service: ResearchMemoryEngine = Depends(get_memory_service)
):
    """Get context usage patterns and analytics"""
    try:
        # Get user's projects for analysis
        projects = await service.list_research_projects(str(current_user.id))
        
        # Calculate usage patterns
        patterns = {
            "total_projects": len(projects),
            "active_projects": len([p for p in projects if p.status == ProjectStatus.ACTIVE]),
            "average_documents_per_project": sum(p.document_count for p in projects) / len(projects) if projects else 0,
            "average_insights_per_project": sum(p.insight_count for p in projects) / len(projects) if projects else 0,
            "most_active_domain": None,
            "context_switch_frequency": "medium"  # Placeholder
        }
        
        # Find most active domain
        if projects:
            domain_counts = {}
            for project in projects:
                domain = project.research_domain
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
            patterns["most_active_domain"] = max(domain_counts.items(), key=lambda x: x[1])[0]
        
        return patterns
        
    except Exception as e:
        logger.error(f"Error getting context usage patterns: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get context usage patterns")

@router.get("/analytics/productivity-insights")
async def get_productivity_insights(
    project_id: Optional[str] = Query(None, description="Specific project ID for insights"),
    current_user: User = Depends(get_current_user),
    service: ResearchMemoryEngine = Depends(get_memory_service)
):
    """Get productivity insights based on research context usage"""
    try:
        insights = {
            "insights_per_day": 0.0,
            "most_productive_time": "morning",
            "average_session_length": 45,  # minutes
            "context_switch_efficiency": 0.8,
            "research_momentum": "increasing",
            "recommendations": []
        }
        
        if project_id:
            # Get project-specific insights
            timeline = await service.generate_research_timeline(
                user_id=str(current_user.id),
                project_id=project_id,
                days_back=30
            )
            
            if timeline:
                insights["insights_per_day"] = len([
                    e for e in timeline 
                    if e.event_type == TimelineEventType.INSIGHT_GENERATED
                ]) / 30
                
                insights["recommendations"].append(
                    "Continue current research momentum"
                )
        else:
            # Get general productivity insights
            projects = await service.list_research_projects(str(current_user.id))
            
            if projects:
                total_insights = sum(p.insight_count for p in projects)
                total_days = sum((datetime.utcnow() - p.created_at).days for p in projects)
                
                if total_days > 0:
                    insights["insights_per_day"] = total_insights / total_days
                
                insights["recommendations"].extend([
                    "Consider focusing on fewer projects for deeper insights",
                    "Regular context switching can boost creativity"
                ])
        
        return insights
        
    except Exception as e:
        logger.error(f"Error getting productivity insights: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get productivity insights")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "research memory engine",
        "timestamp": datetime.utcnow().isoformat()
    }

# Import missing types
from typing import Optional