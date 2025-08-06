"""
Learning Progress API Endpoints for Educational Enhancement System
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from services.learning_progress_service import (
    LearningProgressService,
    LearningProgress,
    KnowledgeGap,
    LearningTrajectory,
    CompetencyMap,
    LearningRecommendation,
    CompetencyLevel,
    LearningGoalType
)
from services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/learning-progress", tags=["learning-progress"])
auth_service = AuthService()
progress_service = LearningProgressService()

# Pydantic Models for API

class UpdateProgressRequest(BaseModel):
    topic: str
    performance_score: float
    study_duration_minutes: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class LearningProgressResponse(BaseModel):
    id: str
    user_id: str
    topic: str
    competency_level: float
    last_studied: Optional[datetime]
    study_count: int
    average_score: float
    trend: str
    confidence_interval: List[float]
    metadata: Dict[str, Any]

class KnowledgeGapResponse(BaseModel):
    topic: str
    gap_type: str
    severity: float
    evidence: List[str]
    recommendations: List[str]
    related_topics: List[str]

class LearningRecommendationResponse(BaseModel):
    type: str
    topic: str
    priority: float
    reason: str
    suggested_actions: List[str]
    estimated_time_minutes: int

class LearningTrajectoryResponse(BaseModel):
    topic: str
    time_points: List[datetime]
    competency_scores: List[float]
    study_sessions: List[int]
    trend_analysis: Dict[str, Any]
    predictions: Dict[str, Any]

class CompetencyMapResponse(BaseModel):
    user_id: str
    competencies: Dict[str, float]
    skill_tree: Dict[str, List[str]]
    mastery_path: List[str]
    generated_at: datetime

class ProgressOverviewResponse(BaseModel):
    total_topics: int
    average_competency: float
    topics_by_level: Dict[str, List[str]]
    recent_activity: List[Dict[str, Any]]
    overall_trend: str
    generated_at: str

# Helper functions
def progress_to_response(progress: LearningProgress) -> LearningProgressResponse:
    """Convert LearningProgress to API response format"""
    return LearningProgressResponse(
        id=progress.id,
        user_id=progress.user_id,
        topic=progress.topic,
        competency_level=progress.competency_level,
        last_studied=progress.last_studied,
        study_count=progress.study_count,
        average_score=progress.average_score,
        trend=progress.trend,
        confidence_interval=list(progress.confidence_interval),
        metadata=progress.metadata
    )

def gap_to_response(gap: KnowledgeGap) -> KnowledgeGapResponse:
    """Convert KnowledgeGap to API response format"""
    return KnowledgeGapResponse(
        topic=gap.topic,
        gap_type=gap.gap_type,
        severity=gap.severity,
        evidence=gap.evidence,
        recommendations=gap.recommendations,
        related_topics=gap.related_topics
    )

def recommendation_to_response(rec: LearningRecommendation) -> LearningRecommendationResponse:
    """Convert LearningRecommendation to API response format"""
    return LearningRecommendationResponse(
        type=rec.type,
        topic=rec.topic,
        priority=rec.priority,
        reason=rec.reason,
        suggested_actions=rec.suggested_actions,
        estimated_time_minutes=rec.estimated_time_minutes
    )

def trajectory_to_response(trajectory: LearningTrajectory) -> LearningTrajectoryResponse:
    """Convert LearningTrajectory to API response format"""
    return LearningTrajectoryResponse(
        topic=trajectory.topic,
        time_points=trajectory.time_points,
        competency_scores=trajectory.competency_scores,
        study_sessions=trajectory.study_sessions,
        trend_analysis=trajectory.trend_analysis,
        predictions=trajectory.predictions
    )

def competency_map_to_response(comp_map: CompetencyMap) -> CompetencyMapResponse:
    """Convert CompetencyMap to API response format"""
    return CompetencyMapResponse(
        user_id=comp_map.user_id,
        competencies=comp_map.competencies,
        skill_tree=comp_map.skill_tree,
        mastery_path=comp_map.mastery_path,
        generated_at=comp_map.generated_at
    )

# Dependency for authentication
async def get_current_user(token: str = Depends(auth_service.get_current_user)):
    """Get current authenticated user"""
    return token

@router.post("/update", response_model=LearningProgressResponse)
async def update_learning_progress(
    request: UpdateProgressRequest,
    user = Depends(get_current_user)
):
    """Update learning progress for a specific topic"""
    try:
        logger.info(f"Updating learning progress for topic {request.topic} by user {user.id}")
        
        # Validate performance score
        if not 0.0 <= request.performance_score <= 1.0:
            raise HTTPException(status_code=400, detail="Performance score must be between 0.0 and 1.0")
        
        progress = await progress_service.update_learning_progress(
            user_id=user.id,
            topic=request.topic,
            performance_score=request.performance_score,
            study_duration_minutes=request.study_duration_minutes,
            metadata=request.metadata
        )
        
        return progress_to_response(progress)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating learning progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update learning progress")

@router.get("/overview", response_model=ProgressOverviewResponse)
async def get_progress_overview(
    user = Depends(get_current_user)
):
    """Get comprehensive progress overview for the user"""
    try:
        overview = await progress_service.get_user_progress_overview(user.id)
        
        return ProgressOverviewResponse(
            total_topics=overview.get('total_topics', 0),
            average_competency=overview.get('average_competency', 0.0),
            topics_by_level=overview.get('topics_by_level', {}),
            recent_activity=overview.get('recent_activity', []),
            overall_trend=overview.get('overall_trend', 'no_data'),
            generated_at=overview.get('generated_at', datetime.now().isoformat())
        )
        
    except Exception as e:
        logger.error(f"Error getting progress overview: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get progress overview")

@router.get("/gaps", response_model=List[KnowledgeGapResponse])
async def get_knowledge_gaps(
    user = Depends(get_current_user)
):
    """Identify knowledge gaps and areas needing attention"""
    try:
        gaps = await progress_service.identify_knowledge_gaps(user.id)
        return [gap_to_response(gap) for gap in gaps]
        
    except Exception as e:
        logger.error(f"Error getting knowledge gaps: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to identify knowledge gaps")

@router.get("/recommendations", response_model=List[LearningRecommendationResponse])
async def get_learning_recommendations(
    user = Depends(get_current_user)
):
    """Generate personalized learning recommendations"""
    try:
        recommendations = await progress_service.generate_learning_recommendations(user.id)
        return [recommendation_to_response(rec) for rec in recommendations]
        
    except Exception as e:
        logger.error(f"Error getting learning recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate learning recommendations")

@router.get("/trajectory/{topic}", response_model=LearningTrajectoryResponse)
async def get_learning_trajectory(
    topic: str,
    user = Depends(get_current_user)
):
    """Get learning trajectory for a specific topic"""
    try:
        trajectory = await progress_service.get_learning_trajectory(user.id, topic)
        return trajectory_to_response(trajectory)
        
    except Exception as e:
        logger.error(f"Error getting learning trajectory: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get learning trajectory")

@router.get("/competency-map", response_model=CompetencyMapResponse)
async def get_competency_map(
    user = Depends(get_current_user)
):
    """Create a comprehensive competency map for the user"""
    try:
        comp_map = await progress_service.create_competency_map(user.id)
        return competency_map_to_response(comp_map)
        
    except Exception as e:
        logger.error(f"Error creating competency map: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create competency map")

@router.get("/topic/{topic}", response_model=LearningProgressResponse)
async def get_topic_progress(
    topic: str,
    user = Depends(get_current_user)
):
    """Get progress for a specific topic"""
    try:
        progress = await progress_service.get_topic_progress(user.id, topic)
        if not progress:
            raise HTTPException(status_code=404, detail="No progress found for this topic")
        
        return progress_to_response(progress)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting topic progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get topic progress")

@router.get("/competency-levels")
async def get_competency_levels():
    """Get available competency levels"""
    return {
        "levels": [
            {
                "name": level.value,
                "range": progress_service.competency_thresholds[level],
                "description": _get_competency_description(level)
            }
            for level in CompetencyLevel
        ]
    }

@router.get("/goal-types")
async def get_learning_goal_types():
    """Get available learning goal types"""
    return {
        "goal_types": [
            {
                "name": goal_type.value,
                "description": _get_goal_type_description(goal_type)
            }
            for goal_type in LearningGoalType
        ]
    }

@router.get("/analytics/dashboard")
async def get_learning_analytics_dashboard(
    user = Depends(get_current_user),
    time_range: str = Query(default="30d", regex="^(7d|30d|90d|1y)$")
):
    """Get comprehensive learning analytics dashboard"""
    try:
        # Get various analytics components
        overview = await progress_service.get_user_progress_overview(user.id)
        gaps = await progress_service.identify_knowledge_gaps(user.id)
        recommendations = await progress_service.generate_learning_recommendations(user.id)
        comp_map = await progress_service.create_competency_map(user.id)
        
        # Combine into dashboard
        dashboard = {
            "overview": overview,
            "knowledge_gaps": [gap_to_response(gap).__dict__ for gap in gaps[:5]],
            "recommendations": [recommendation_to_response(rec).__dict__ for rec in recommendations[:5]],
            "competency_summary": {
                "total_topics": len(comp_map.competencies),
                "mastery_progress": len([c for c in comp_map.competencies.values() if c >= 0.8]) / len(comp_map.competencies) if comp_map.competencies else 0,
                "next_focus_areas": comp_map.mastery_path[:3]
            },
            "time_range": time_range,
            "generated_at": datetime.now().isoformat()
        }
        
        return dashboard
        
    except Exception as e:
        logger.error(f"Error getting learning analytics dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get learning analytics dashboard")

@router.post("/bulk-update")
async def bulk_update_progress(
    updates: List[UpdateProgressRequest],
    user = Depends(get_current_user)
):
    """Update progress for multiple topics at once"""
    try:
        if len(updates) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 updates allowed per request")
        
        results = []
        for update in updates:
            try:
                progress = await progress_service.update_learning_progress(
                    user_id=user.id,
                    topic=update.topic,
                    performance_score=update.performance_score,
                    study_duration_minutes=update.study_duration_minutes,
                    metadata=update.metadata
                )
                results.append({
                    "topic": update.topic,
                    "success": True,
                    "progress": progress_to_response(progress).__dict__
                })
            except Exception as e:
                results.append({
                    "topic": update.topic,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "results": results,
            "total_updates": len(updates),
            "successful_updates": len([r for r in results if r["success"]]),
            "failed_updates": len([r for r in results if not r["success"]])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk update: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to perform bulk update")

def _get_competency_description(level: CompetencyLevel) -> str:
    """Get description for competency level"""
    descriptions = {
        CompetencyLevel.NOVICE: "Just starting to learn, basic awareness",
        CompetencyLevel.BEGINNER: "Basic understanding, can perform simple tasks",
        CompetencyLevel.INTERMEDIATE: "Good understanding, can handle most common scenarios",
        CompetencyLevel.ADVANCED: "Strong expertise, can handle complex situations",
        CompetencyLevel.EXPERT: "Mastery level, can teach and innovate"
    }
    return descriptions.get(level, "Unknown competency level")

def _get_goal_type_description(goal_type: LearningGoalType) -> str:
    """Get description for learning goal type"""
    descriptions = {
        LearningGoalType.MASTERY: "Achieve deep understanding and expertise",
        LearningGoalType.RETENTION: "Maintain knowledge over time",
        LearningGoalType.SPEED: "Improve response time and efficiency",
        LearningGoalType.ACCURACY: "Improve correctness and precision"
    }
    return descriptions.get(goal_type, "Unknown goal type")

@router.get("/analytics/comprehensive")
async def get_comprehensive_analytics(
    user = Depends(get_current_user)
):
    """Get comprehensive learning analytics with detailed performance metrics"""
    try:
        analytics = await progress_service.get_comprehensive_analytics(user.id)
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting comprehensive analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get comprehensive analytics")

@router.get("/dashboard/visual")
async def get_visual_dashboard_data(
    user = Depends(get_current_user)
):
    """Get data formatted for visual progress dashboards with learning trajectory visualization"""
    try:
        dashboard_data = await progress_service.get_visual_dashboard_data(user.id)
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error getting visual dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get visual dashboard data")

@router.get("/analytics/performance-metrics")
async def get_performance_metrics(
    user = Depends(get_current_user),
    time_range: str = Query(default="30d", regex="^(7d|30d|90d|1y|all)$")
):
    """Get detailed performance metrics for specified time range"""
    try:
        analytics = await progress_service.get_comprehensive_analytics(user.id)
        
        # Filter based on time range
        performance_metrics = {
            "overview": analytics.get("overview", {}),
            "performance_trends": analytics.get("performance_trends", {}),
            "learning_velocity": analytics.get("learning_velocity", {}),
            "retention_analysis": analytics.get("retention_analysis", {}),
            "time_range": time_range,
            "generated_at": datetime.now().isoformat()
        }
        
        return performance_metrics
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")

@router.get("/analytics/competency-mapping")
async def get_competency_mapping_data(
    user = Depends(get_current_user)
):
    """Get enhanced competency mapping and skill development tracking data"""
    try:
        # Get competency map
        comp_map = await progress_service.create_competency_map(user.id)
        
        # Get comprehensive analytics for additional context
        analytics = await progress_service.get_comprehensive_analytics(user.id)
        
        competency_mapping = {
            "competency_map": competency_map_to_response(comp_map).__dict__,
            "competency_distribution": analytics.get("competency_distribution", {}),
            "skill_development_trends": analytics.get("performance_trends", {}),
            "learning_patterns": analytics.get("learning_patterns", {}),
            "generated_at": datetime.now().isoformat()
        }
        
        return competency_mapping
        
    except Exception as e:
        logger.error(f"Error getting competency mapping data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get competency mapping data")

@router.get("/analytics/knowledge-gaps-enhanced")
async def get_enhanced_knowledge_gaps(
    user = Depends(get_current_user),
    include_recommendations: bool = Query(default=True),
    severity_threshold: float = Query(default=0.0, ge=0.0, le=1.0)
):
    """Get enhanced knowledge gap identification with targeted recommendations"""
    try:
        # Get knowledge gaps
        gaps = await progress_service.identify_knowledge_gaps(user.id)
        
        # Filter by severity threshold
        filtered_gaps = [gap for gap in gaps if gap.severity >= severity_threshold]
        
        # Get recommendations if requested
        recommendations = []
        if include_recommendations:
            recommendations = await progress_service.generate_learning_recommendations(user.id)
        
        # Get analytics for context
        analytics = await progress_service.get_comprehensive_analytics(user.id)
        
        enhanced_gaps = {
            "knowledge_gaps": [gap_to_response(gap).__dict__ for gap in filtered_gaps],
            "targeted_recommendations": [recommendation_to_response(rec).__dict__ for rec in recommendations] if include_recommendations else [],
            "gap_analysis": {
                "total_gaps": len(filtered_gaps),
                "high_severity_gaps": len([g for g in filtered_gaps if g.severity >= 0.7]),
                "medium_severity_gaps": len([g for g in filtered_gaps if 0.4 <= g.severity < 0.7]),
                "low_severity_gaps": len([g for g in filtered_gaps if g.severity < 0.4]),
                "most_common_gap_type": max(set(g.gap_type for g in filtered_gaps), key=lambda x: len([g for g in filtered_gaps if g.gap_type == x])) if filtered_gaps else None
            },
            "competency_context": analytics.get("competency_distribution", {}),
            "severity_threshold": severity_threshold,
            "generated_at": datetime.now().isoformat()
        }
        
        return enhanced_gaps
        
    except Exception as e:
        logger.error(f"Error getting enhanced knowledge gaps: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get enhanced knowledge gaps")

@router.get("/trajectory/multiple")
async def get_multiple_learning_trajectories(
    topics: List[str] = Query(..., description="List of topics to get trajectories for"),
    user = Depends(get_current_user)
):
    """Get learning trajectories for multiple topics for comparison visualization"""
    try:
        if len(topics) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 topics allowed per request")
        
        trajectories = {}
        for topic in topics:
            trajectory = await progress_service.get_learning_trajectory(user.id, topic)
            trajectories[topic] = trajectory_to_response(trajectory).__dict__
        
        # Add comparison metrics
        comparison_data = {
            "trajectories": trajectories,
            "comparison_metrics": {
                "topic_count": len(topics),
                "average_improvement_rates": {
                    topic: traj["trend_analysis"].get("learning_rate", 0) 
                    for topic, traj in trajectories.items()
                },
                "most_improved_topic": max(trajectories.items(), 
                                         key=lambda x: x[1]["trend_analysis"].get("learning_rate", 0))[0] if trajectories else None,
                "most_volatile_topic": max(trajectories.items(), 
                                         key=lambda x: x[1]["trend_analysis"].get("volatility", 0))[0] if trajectories else None
            },
            "generated_at": datetime.now().isoformat()
        }
        
        return comparison_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting multiple learning trajectories: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get multiple learning trajectories")