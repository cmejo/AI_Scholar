"""
Personalization API Endpoints
Provides endpoints for adaptive user interfaces, personalized recommendations,
and customized research workflows.
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
from services.personalization_engine import (
    PersonalizationEngine, UserPersonalizationProfile, PersonalizedRecommendation,
    LearningStyle, PersonalityType, ContentPreference
)

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Pydantic models
class PersonalizationProfileResponse(BaseModel):
    user_id: str
    learning_style: LearningStyle
    personality_type: PersonalityType
    content_preferences: List[ContentPreference]
    research_domains: List[str]
    skill_levels: Dict[str, float]
    ui_preferences: Dict[str, Any]
    workflow_preferences: Dict[str, Any]
    adaptation_score: float
    confidence_score: float
    last_updated: datetime

class RecommendationResponse(BaseModel):
    id: str
    recommendation_type: str
    title: str
    description: str
    content_id: str
    relevance_score: float
    personalization_score: float
    reasoning: List[str]
    metadata: Dict[str, Any]
    created_at: datetime

class UIConfigRequest(BaseModel):
    context: str = "dashboard"

class UIConfigResponse(BaseModel):
    layout: str
    theme: str
    navigation: str
    content_density: str
    interaction_style: str
    additional_config: Dict[str, Any]

class WorkflowRequest(BaseModel):
    workflow_type: str
    base_workflow: Dict[str, Any]

class WorkflowResponse(BaseModel):
    workflow_id: str
    workflow_type: str
    personalized_workflow: Dict[str, Any]
    personalization_metadata: Dict[str, Any]

class ProfileUpdateRequest(BaseModel):
    learning_style: Optional[LearningStyle] = None
    personality_type: Optional[PersonalityType] = None
    content_preferences: Optional[List[ContentPreference]] = None
    ui_preferences: Optional[Dict[str, Any]] = None
    workflow_preferences: Optional[Dict[str, Any]] = None

class RecommendationInteractionRequest(BaseModel):
    recommendation_id: str
    interaction_type: str  # clicked, dismissed, saved, etc.

class PersonalizationMetricsResponse(BaseModel):
    adaptation_score: float
    confidence_score: float
    learning_style: str
    personality_type: str
    research_domains: List[str]
    skill_levels: Dict[str, float]
    last_updated: datetime
    recommendation_count: int

# Router setup
router = APIRouter(prefix="/api/v1/personalization", tags=["Personalization"])

# Global service instance
personalization_service: Optional[PersonalizationEngine] = None

def get_personalization_service(db: Session = Depends(get_db)) -> PersonalizationEngine:
    """Get personalization service instance"""
    global personalization_service
    if personalization_service is None:
        personalization_service = PersonalizationEngine(db)
    return personalization_service

# Profile endpoints
@router.get("/profile", response_model=PersonalizationProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    service: PersonalizationEngine = Depends(get_personalization_service)
):
    """Get user's personalization profile"""
    try:
        profile = await service.get_user_profile(str(current_user.id))
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return PersonalizationProfileResponse(
            user_id=profile.user_id,
            learning_style=profile.learning_style,
            personality_type=profile.personality_type,
            content_preferences=profile.content_preferences,
            research_domains=profile.research_domains,
            skill_levels=profile.skill_levels,
            ui_preferences=profile.ui_preferences,
            workflow_preferences=profile.workflow_preferences,
            adaptation_score=profile.adaptation_score,
            confidence_score=profile.confidence_score,
            last_updated=profile.last_updated
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user profile")

@router.put("/profile", response_model=PersonalizationProfileResponse)
async def update_user_profile(
    request: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: PersonalizationEngine = Depends(get_personalization_service)
):
    """Update user's personalization profile"""
    try:
        # Convert request to updates dict
        updates = {}
        if request.learning_style is not None:
            updates["learning_style"] = request.learning_style
        if request.personality_type is not None:
            updates["personality_type"] = request.personality_type
        if request.content_preferences is not None:
            updates["content_preferences"] = request.content_preferences
        if request.ui_preferences is not None:
            updates["ui_preferences"] = request.ui_preferences
        if request.workflow_preferences is not None:
            updates["workflow_preferences"] = request.workflow_preferences
        
        profile = await service.update_user_profile(str(current_user.id), updates)
        
        return PersonalizationProfileResponse(
            user_id=profile.user_id,
            learning_style=profile.learning_style,
            personality_type=profile.personality_type,
            content_preferences=profile.content_preferences,
            research_domains=profile.research_domains,
            skill_levels=profile.skill_levels,
            ui_preferences=profile.ui_preferences,
            workflow_preferences=profile.workflow_preferences,
            adaptation_score=profile.adaptation_score,
            confidence_score=profile.confidence_score,
            last_updated=profile.last_updated
        )
        
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update user profile")

@router.post("/profile/rebuild", response_model=PersonalizationProfileResponse)
async def rebuild_user_profile(
    current_user: User = Depends(get_current_user),
    service: PersonalizationEngine = Depends(get_personalization_service)
):
    """Rebuild user's personalization profile from scratch"""
    try:
        profile = await service.build_user_profile(str(current_user.id))
        
        return PersonalizationProfileResponse(
            user_id=profile.user_id,
            learning_style=profile.learning_style,
            personality_type=profile.personality_type,
            content_preferences=profile.content_preferences,
            research_domains=profile.research_domains,
            skill_levels=profile.skill_levels,
            ui_preferences=profile.ui_preferences,
            workflow_preferences=profile.workflow_preferences,
            adaptation_score=profile.adaptation_score,
            confidence_score=profile.confidence_score,
            last_updated=profile.last_updated
        )
        
    except Exception as e:
        logger.error(f"Error rebuilding user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to rebuild user profile")

# Recommendation endpoints
@router.get("/recommendations", response_model=List[RecommendationResponse])
async def get_personalized_recommendations(
    context: str = Query(default="general", description="Context for recommendations"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of recommendations"),
    current_user: User = Depends(get_current_user),
    service: PersonalizationEngine = Depends(get_personalization_service)
):
    """Get personalized content recommendations"""
    try:
        recommendations = await service.generate_personalized_recommendations(
            user_id=str(current_user.id),
            context=context,
            limit=limit
        )
        
        return [
            RecommendationResponse(
                id=rec.id,
                recommendation_type=rec.recommendation_type,
                title=rec.title,
                description=rec.description,
                content_id=rec.content_id,
                relevance_score=rec.relevance_score,
                personalization_score=rec.personalization_score,
                reasoning=rec.reasoning,
                metadata=rec.metadata,
                created_at=rec.created_at
            )
            for rec in recommendations
        ]
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")

@router.post("/recommendations/interaction")
async def record_recommendation_interaction(
    request: RecommendationInteractionRequest,
    current_user: User = Depends(get_current_user),
    service: PersonalizationEngine = Depends(get_personalization_service)
):
    """Record user interaction with a recommendation"""
    try:
        success = await service.record_recommendation_interaction(
            user_id=str(current_user.id),
            recommendation_id=request.recommendation_id,
            interaction_type=request.interaction_type
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        return {"status": "success", "message": "Interaction recorded"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording recommendation interaction: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record interaction")

# UI adaptation endpoints
@router.post("/ui-config", response_model=UIConfigResponse)
async def get_adaptive_ui_config(
    request: UIConfigRequest,
    current_user: User = Depends(get_current_user),
    service: PersonalizationEngine = Depends(get_personalization_service)
):
    """Get adaptive UI configuration for user"""
    try:
        ui_config = await service.adapt_user_interface(
            user_id=str(current_user.id),
            current_context=request.context
        )
        
        # Extract standard fields
        standard_fields = {
            "layout": ui_config.get("layout", "default"),
            "theme": ui_config.get("theme", "light"),
            "navigation": ui_config.get("navigation", "sidebar"),
            "content_density": ui_config.get("content_density", "medium"),
            "interaction_style": ui_config.get("interaction_style", "click")
        }
        
        # Everything else goes in additional_config
        additional_config = {
            k: v for k, v in ui_config.items() 
            if k not in standard_fields
        }
        
        return UIConfigResponse(
            **standard_fields,
            additional_config=additional_config
        )
        
    except Exception as e:
        logger.error(f"Error getting UI config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get UI configuration")

# Workflow endpoints
@router.post("/workflow", response_model=WorkflowResponse)
async def create_personalized_workflow(
    request: WorkflowRequest,
    current_user: User = Depends(get_current_user),
    service: PersonalizationEngine = Depends(get_personalization_service)
):
    """Create personalized research workflow"""
    try:
        personalized_workflow = await service.create_personalized_workflow(
            user_id=str(current_user.id),
            workflow_type=request.workflow_type,
            base_workflow=request.base_workflow
        )
        
        # Extract personalization metadata
        personalization_metadata = personalized_workflow.pop("personalization", {})
        
        return WorkflowResponse(
            workflow_id=str(uuid.uuid4()),
            workflow_type=request.workflow_type,
            personalized_workflow=personalized_workflow,
            personalization_metadata=personalization_metadata
        )
        
    except Exception as e:
        logger.error(f"Error creating personalized workflow: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create personalized workflow")

# Analytics endpoints
@router.get("/metrics", response_model=PersonalizationMetricsResponse)
async def get_personalization_metrics(
    current_user: User = Depends(get_current_user),
    service: PersonalizationEngine = Depends(get_personalization_service)
):
    """Get personalization metrics for user"""
    try:
        metrics = service.get_personalization_metrics(str(current_user.id))
        
        if not metrics:
            raise HTTPException(status_code=404, detail="Metrics not found")
        
        return PersonalizationMetricsResponse(
            adaptation_score=metrics["adaptation_score"],
            confidence_score=metrics["confidence_score"],
            learning_style=metrics["learning_style"],
            personality_type=metrics["personality_type"],
            research_domains=metrics["research_domains"],
            skill_levels=metrics["skill_levels"],
            last_updated=datetime.fromisoformat(metrics["last_updated"]),
            recommendation_count=metrics["recommendation_count"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting personalization metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get personalization metrics")

# Learning style and personality detection endpoints
@router.post("/detect/learning-style")
async def detect_learning_style(
    current_user: User = Depends(get_current_user),
    service: PersonalizationEngine = Depends(get_personalization_service)
):
    """Detect user's learning style based on behavior"""
    try:
        # Get user profile to access detection methods
        profile = await service.get_user_profile(str(current_user.id))
        if not profile:
            profile = await service.build_user_profile(str(current_user.id))
        
        return {
            "learning_style": profile.learning_style.value,
            "confidence": profile.confidence_score,
            "reasoning": [
                f"Based on your interaction patterns",
                f"Analyzed {len(profile.interaction_patterns)} behavioral indicators"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error detecting learning style: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to detect learning style")

@router.post("/detect/personality-type")
async def detect_personality_type(
    current_user: User = Depends(get_current_user),
    service: PersonalizationEngine = Depends(get_personalization_service)
):
    """Detect user's research personality type"""
    try:
        profile = await service.get_user_profile(str(current_user.id))
        if not profile:
            profile = await service.build_user_profile(str(current_user.id))
        
        return {
            "personality_type": profile.personality_type.value,
            "confidence": profile.confidence_score,
            "reasoning": [
                f"Based on your research behavior patterns",
                f"Identified from {len(profile.research_domains)} research domains"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error detecting personality type: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to detect personality type")

# Preference endpoints
@router.get("/preferences/content")
async def get_content_preferences(
    current_user: User = Depends(get_current_user),
    service: PersonalizationEngine = Depends(get_personalization_service)
):
    """Get user's content preferences"""
    try:
        profile = await service.get_user_profile(str(current_user.id))
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {
            "content_preferences": [pref.value for pref in profile.content_preferences],
            "research_domains": profile.research_domains,
            "skill_levels": profile.skill_levels
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting content preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get content preferences")

@router.get("/preferences/ui")
async def get_ui_preferences(
    current_user: User = Depends(get_current_user),
    service: PersonalizationEngine = Depends(get_personalization_service)
):
    """Get user's UI preferences"""
    try:
        profile = await service.get_user_profile(str(current_user.id))
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {
            "ui_preferences": profile.ui_preferences,
            "learning_style_adaptations": profile.learning_style.value,
            "personality_adaptations": profile.personality_type.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting UI preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get UI preferences")

@router.get("/preferences/workflow")
async def get_workflow_preferences(
    current_user: User = Depends(get_current_user),
    service: PersonalizationEngine = Depends(get_personalization_service)
):
    """Get user's workflow preferences"""
    try:
        profile = await service.get_user_profile(str(current_user.id))
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {
            "workflow_preferences": profile.workflow_preferences,
            "skill_based_adaptations": profile.skill_levels,
            "personality_based_adaptations": profile.personality_type.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get workflow preferences")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "personalization engine",
        "timestamp": datetime.utcnow().isoformat()
    }

# Import uuid for workflow ID generation
import uuid