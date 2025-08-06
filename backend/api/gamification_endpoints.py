"""
Gamification API Endpoints for Educational Enhancement System
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from services.gamification_service import (
    GamificationService,
    Achievement,
    UserProfile,
    PersonalizedRecommendation,
    SocialLearningData,
    LearningChallenge,
    AchievementType,
    BadgeLevel,
    LearningStyle,
    DifficultyPreference
)
from services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gamification", tags=["gamification"])
auth_service = AuthService()
gamification_service = GamificationService()

# Pydantic Models for API

class AwardAchievementRequest(BaseModel):
    achievement_type: AchievementType
    context: Optional[Dict[str, Any]] = None

class AchievementResponse(BaseModel):
    id: str
    user_id: str
    achievement_type: str
    title: str
    description: str
    badge_level: str
    points: int
    earned_at: datetime
    progress: float
    metadata: Dict[str, Any]

class PersonalizedRecommendationResponse(BaseModel):
    type: str
    content: str
    reason: str
    confidence: float
    estimated_benefit: float
    suggested_duration: int
    metadata: Dict[str, Any]

class SocialLearningDataResponse(BaseModel):
    user_rank: int
    total_users: int
    peer_group_average: float
    user_score: float
    improvement_rank: int
    study_streak_rank: int
    collaborative_sessions: int
    peer_interactions: int

class UserLevelResponse(BaseModel):
    current_level: int
    total_points: int
    progress_to_next_level: float
    points_to_next_level: int
    level_name: str

class AdaptDifficultyRequest(BaseModel):
    topic: str
    current_difficulty: float

class CreateChallengeRequest(BaseModel):
    title: str
    description: str
    challenge_type: str
    target_value: float
    duration_days: int
    points_reward: int

class LearningChallengeResponse(BaseModel):
    id: str
    title: str
    description: str
    challenge_type: str
    target_value: float
    duration_days: int
    points_reward: int
    badge_reward: Optional[str]
    participants: int
    start_date: datetime
    end_date: datetime

# Helper functions
def achievement_to_response(achievement: Achievement) -> AchievementResponse:
    """Convert Achievement to API response format"""
    return AchievementResponse(
        id=achievement.id,
        user_id=achievement.user_id,
        achievement_type=achievement.achievement_type.value,
        title=achievement.title,
        description=achievement.description,
        badge_level=achievement.badge_level.value,
        points=achievement.points,
        earned_at=achievement.earned_at,
        progress=achievement.progress,
        metadata=achievement.metadata
    )

def recommendation_to_response(rec: PersonalizedRecommendation) -> PersonalizedRecommendationResponse:
    """Convert PersonalizedRecommendation to API response format"""
    return PersonalizedRecommendationResponse(
        type=rec.type,
        content=rec.content,
        reason=rec.reason,
        confidence=rec.confidence,
        estimated_benefit=rec.estimated_benefit,
        suggested_duration=rec.suggested_duration,
        metadata=rec.metadata
    )

def social_data_to_response(data: SocialLearningData) -> SocialLearningDataResponse:
    """Convert SocialLearningData to API response format"""
    return SocialLearningDataResponse(
        user_rank=data.user_rank,
        total_users=data.total_users,
        peer_group_average=data.peer_group_average,
        user_score=data.user_score,
        improvement_rank=data.improvement_rank,
        study_streak_rank=data.study_streak_rank,
        collaborative_sessions=data.collaborative_sessions,
        peer_interactions=data.peer_interactions
    )

def challenge_to_response(challenge: LearningChallenge) -> LearningChallengeResponse:
    """Convert LearningChallenge to API response format"""
    return LearningChallengeResponse(
        id=challenge.id,
        title=challenge.title,
        description=challenge.description,
        challenge_type=challenge.challenge_type,
        target_value=challenge.target_value,
        duration_days=challenge.duration_days,
        points_reward=challenge.points_reward,
        badge_reward=challenge.badge_reward,
        participants=challenge.participants,
        start_date=challenge.start_date,
        end_date=challenge.end_date
    )

# Dependency for authentication
async def get_current_user(token: str = Depends(auth_service.get_current_user)):
    """Get current authenticated user"""
    return token

@router.post("/achievements/award", response_model=Optional[AchievementResponse])
async def award_achievement(
    request: AwardAchievementRequest,
    user = Depends(get_current_user)
):
    """Award an achievement to the user"""
    try:
        logger.info(f"Attempting to award {request.achievement_type.value} achievement to user {user.id}")
        
        achievement = await gamification_service.award_achievement(
            user_id=user.id,
            achievement_type=request.achievement_type,
            context=request.context
        )
        
        if achievement:
            return achievement_to_response(achievement)
        else:
            return None
        
    except Exception as e:
        logger.error(f"Error awarding achievement: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to award achievement")

@router.get("/achievements", response_model=List[AchievementResponse])
async def get_user_achievements(
    user = Depends(get_current_user)
):
    """Get all achievements for the user"""
    try:
        achievements = await gamification_service.get_user_achievements(user.id)
        return [achievement_to_response(achievement) for achievement in achievements]
        
    except Exception as e:
        logger.error(f"Error getting user achievements: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user achievements")

@router.get("/recommendations", response_model=List[PersonalizedRecommendationResponse])
async def get_personalized_recommendations(
    user = Depends(get_current_user),
    limit: int = Query(default=5, le=20)
):
    """Get personalized study recommendations"""
    try:
        recommendations = await gamification_service.generate_personalized_recommendations(
            user_id=user.id,
            limit=limit
        )
        return [recommendation_to_response(rec) for rec in recommendations]
        
    except Exception as e:
        logger.error(f"Error getting personalized recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get personalized recommendations")

@router.get("/social", response_model=SocialLearningDataResponse)
async def get_social_learning_data(
    user = Depends(get_current_user)
):
    """Get social learning statistics and peer comparisons"""
    try:
        social_data = await gamification_service.get_social_learning_data(user.id)
        return social_data_to_response(social_data)
        
    except Exception as e:
        logger.error(f"Error getting social learning data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get social learning data")

@router.post("/difficulty/adapt")
async def adapt_content_difficulty(
    request: AdaptDifficultyRequest,
    user = Depends(get_current_user)
):
    """Adapt content difficulty based on user's learning curve"""
    try:
        # Validate difficulty range
        if not 0.0 <= request.current_difficulty <= 1.0:
            raise HTTPException(status_code=400, detail="Current difficulty must be between 0.0 and 1.0")
        
        new_difficulty = await gamification_service.adapt_content_difficulty(
            user_id=user.id,
            topic=request.topic,
            current_difficulty=request.current_difficulty
        )
        
        return {
            "topic": request.topic,
            "previous_difficulty": request.current_difficulty,
            "new_difficulty": new_difficulty,
            "adjustment": new_difficulty - request.current_difficulty
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adapting content difficulty: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to adapt content difficulty")

@router.get("/level", response_model=UserLevelResponse)
async def get_user_level(
    user = Depends(get_current_user)
):
    """Get user's current level and progress"""
    try:
        level_data = await gamification_service.get_user_level_and_progress(user.id)
        
        return UserLevelResponse(
            current_level=level_data["current_level"],
            total_points=level_data["total_points"],
            progress_to_next_level=level_data["progress_to_next_level"],
            points_to_next_level=level_data["points_to_next_level"],
            level_name=level_data["level_name"]
        )
        
    except Exception as e:
        logger.error(f"Error getting user level: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user level")

@router.post("/challenges", response_model=LearningChallengeResponse)
async def create_learning_challenge(
    request: CreateChallengeRequest,
    user = Depends(get_current_user)
):
    """Create a new learning challenge"""
    try:
        # Validate input
        if request.duration_days <= 0 or request.duration_days > 365:
            raise HTTPException(status_code=400, detail="Duration must be between 1 and 365 days")
        
        if request.points_reward <= 0:
            raise HTTPException(status_code=400, detail="Points reward must be positive")
        
        challenge = await gamification_service.create_learning_challenge(
            title=request.title,
            description=request.description,
            challenge_type=request.challenge_type,
            target_value=request.target_value,
            duration_days=request.duration_days,
            points_reward=request.points_reward
        )
        
        return challenge_to_response(challenge)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating learning challenge: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create learning challenge")

@router.get("/achievement-types")
async def get_achievement_types():
    """Get available achievement types"""
    return {
        "achievement_types": [
            {
                "name": achievement_type.value,
                "description": _get_achievement_type_description(achievement_type)
            }
            for achievement_type in AchievementType
        ]
    }

@router.get("/badge-levels")
async def get_badge_levels():
    """Get available badge levels"""
    return {
        "badge_levels": [
            {
                "name": badge_level.value,
                "description": _get_badge_level_description(badge_level)
            }
            for badge_level in BadgeLevel
        ]
    }

@router.get("/learning-styles")
async def get_learning_styles():
    """Get available learning styles"""
    return {
        "learning_styles": [
            {
                "name": learning_style.value,
                "description": _get_learning_style_description(learning_style)
            }
            for learning_style in LearningStyle
        ]
    }

@router.get("/difficulty-preferences")
async def get_difficulty_preferences():
    """Get available difficulty preferences"""
    return {
        "difficulty_preferences": [
            {
                "name": difficulty_pref.value,
                "description": _get_difficulty_preference_description(difficulty_pref)
            }
            for difficulty_pref in DifficultyPreference
        ]
    }

@router.get("/leaderboard")
async def get_leaderboard(
    user = Depends(get_current_user),
    limit: int = Query(default=10, le=100)
):
    """Get leaderboard with top users"""
    try:
        # Get social learning data for context
        social_data = await gamification_service.get_social_learning_data(user.id)
        
        # This would typically query all users and rank them
        # For now, return simplified leaderboard data
        leaderboard = {
            "user_rank": social_data.user_rank,
            "user_score": social_data.user_score,
            "total_users": social_data.total_users,
            "top_users": [
                {
                    "rank": i + 1,
                    "user_id": f"user_{i+1}",
                    "username": f"User {i+1}",
                    "points": max(0, int(social_data.peer_group_average * (1.2 - i * 0.1))),
                    "level": min(9, i + 1),
                    "badges": i + 1
                }
                for i in range(min(limit, 10))
            ]
        }
        
        return leaderboard
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get leaderboard")

@router.get("/dashboard")
async def get_gamification_dashboard(
    user = Depends(get_current_user)
):
    """Get comprehensive gamification dashboard"""
    try:
        # Get various gamification components
        achievements = await gamification_service.get_user_achievements(user.id)
        recommendations = await gamification_service.generate_personalized_recommendations(user.id, limit=3)
        social_data = await gamification_service.get_social_learning_data(user.id)
        level_data = await gamification_service.get_user_level_and_progress(user.id)
        
        # Combine into dashboard
        dashboard = {
            "level_info": level_data,
            "recent_achievements": [achievement_to_response(a).__dict__ for a in achievements[:5]],
            "recommendations": [recommendation_to_response(r).__dict__ for r in recommendations],
            "social_stats": social_data_to_response(social_data).__dict__,
            "points_breakdown": {
                "total_points": level_data["total_points"],
                "points_this_week": 0,  # Would calculate from recent achievements
                "points_this_month": 0,  # Would calculate from recent achievements
                "average_daily_points": level_data["total_points"] / 30  # Simplified
            },
            "streaks": {
                "current_study_streak": 0,  # Would calculate from study sessions
                "longest_study_streak": 0,  # Would calculate from study sessions
                "quiz_streak": 0  # Would calculate from quiz attempts
            },
            "generated_at": datetime.now().isoformat()
        }
        
        return dashboard
        
    except Exception as e:
        logger.error(f"Error getting gamification dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get gamification dashboard")

# New endpoints for enhanced gamification features

class CreateStudyGroupRequest(BaseModel):
    name: str
    description: str
    max_members: int = 10

class JoinStudyGroupRequest(BaseModel):
    group_id: str

class TrackPeerInteractionRequest(BaseModel):
    interaction_type: str
    peer_id: str
    context: Optional[Dict[str, Any]] = None

class PersonalizedStudyPlanRequest(BaseModel):
    goals: List[str]
    time_available_minutes: int

@router.get("/peer-comparison")
async def get_peer_comparison_data(
    user = Depends(get_current_user)
):
    """Get detailed peer comparison data for social learning"""
    try:
        comparison_data = await gamification_service.get_peer_comparison_data(user.id)
        return comparison_data
        
    except Exception as e:
        logger.error(f"Error getting peer comparison data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get peer comparison data")

@router.post("/study-groups")
async def create_study_group(
    request: CreateStudyGroupRequest,
    user = Depends(get_current_user)
):
    """Create a collaborative study group"""
    try:
        if len(request.name.strip()) < 3:
            raise HTTPException(status_code=400, detail="Study group name must be at least 3 characters")
        
        if request.max_members < 2 or request.max_members > 50:
            raise HTTPException(status_code=400, detail="Max members must be between 2 and 50")
        
        study_group = await gamification_service.create_study_group(
            creator_id=user.id,
            name=request.name,
            description=request.description,
            max_members=request.max_members
        )
        
        return study_group
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating study group: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create study group")

@router.post("/study-groups/join")
async def join_study_group(
    request: JoinStudyGroupRequest,
    user = Depends(get_current_user)
):
    """Join a study group"""
    try:
        success = await gamification_service.join_study_group(user.id, request.group_id)
        
        if success:
            return {"message": "Successfully joined study group", "group_id": request.group_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to join study group")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining study group: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to join study group")

@router.get("/collaborative-challenges")
async def get_collaborative_challenges(
    user = Depends(get_current_user)
):
    """Get available collaborative challenges"""
    try:
        challenges = await gamification_service.get_collaborative_challenges(user.id)
        return {"challenges": challenges}
        
    except Exception as e:
        logger.error(f"Error getting collaborative challenges: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get collaborative challenges")

@router.get("/adaptive-content/{topic}")
async def get_adaptive_content_recommendations(
    topic: str,
    user = Depends(get_current_user)
):
    """Get adaptive content recommendations for a specific topic"""
    try:
        recommendations = await gamification_service.generate_adaptive_content_recommendations(
            user_id=user.id,
            topic=topic
        )
        return recommendations
        
    except Exception as e:
        logger.error(f"Error getting adaptive content recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get adaptive content recommendations")

@router.post("/peer-interactions")
async def track_peer_interaction(
    request: TrackPeerInteractionRequest,
    user = Depends(get_current_user)
):
    """Track peer interactions for social learning analytics"""
    try:
        valid_interaction_types = ["help_given", "help_received", "collaboration", "discussion"]
        if request.interaction_type not in valid_interaction_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid interaction type. Must be one of: {', '.join(valid_interaction_types)}"
            )
        
        success = await gamification_service.track_peer_interactions(
            user_id=user.id,
            interaction_type=request.interaction_type,
            peer_id=request.peer_id,
            context=request.context
        )
        
        if success:
            return {"message": "Peer interaction tracked successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to track peer interaction")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking peer interaction: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track peer interaction")

@router.post("/study-plan")
async def get_personalized_study_plan(
    request: PersonalizedStudyPlanRequest,
    user = Depends(get_current_user)
):
    """Generate a personalized study plan based on user goals and available time"""
    try:
        if not request.goals:
            raise HTTPException(status_code=400, detail="At least one goal must be specified")
        
        if request.time_available_minutes <= 0 or request.time_available_minutes > 480:  # Max 8 hours
            raise HTTPException(status_code=400, detail="Time available must be between 1 and 480 minutes")
        
        study_plan = await gamification_service.get_personalized_study_plan(
            user_id=user.id,
            goals=request.goals,
            time_available_minutes=request.time_available_minutes
        )
        
        return study_plan
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating personalized study plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate personalized study plan")

@router.get("/learning-insights")
async def get_learning_insights(
    user = Depends(get_current_user)
):
    """Get comprehensive learning insights and analytics"""
    try:
        # Get peer comparison data
        peer_data = await gamification_service.get_peer_comparison_data(user.id)
        
        # Get social learning data
        social_data = await gamification_service.get_social_learning_data(user.id)
        
        # Get recent achievements
        achievements = await gamification_service.get_user_achievements(user.id)
        recent_achievements = achievements[:5]
        
        # Get personalized recommendations
        recommendations = await gamification_service.generate_personalized_recommendations(user.id, limit=5)
        
        insights = {
            "peer_comparison": peer_data,
            "social_stats": social_data_to_response(social_data).__dict__,
            "recent_achievements": [achievement_to_response(a).__dict__ for a in recent_achievements],
            "personalized_recommendations": [recommendation_to_response(r).__dict__ for r in recommendations],
            "learning_trends": {
                "improvement_velocity": "steady",  # Would calculate from historical data
                "consistency_score": 0.75,  # Would calculate from study patterns
                "challenge_readiness": "moderate"  # Would calculate from performance
            },
            "generated_at": datetime.now().isoformat()
        }
        
        return insights
        
    except Exception as e:
        logger.error(f"Error getting learning insights: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get learning insights")

def _get_achievement_type_description(achievement_type: AchievementType) -> str:
    """Get description for achievement type"""
    descriptions = {
        AchievementType.STREAK: "Achievements for maintaining study streaks",
        AchievementType.MASTERY: "Achievements for mastering topics or skills",
        AchievementType.PROGRESS: "Achievements for reaching learning milestones",
        AchievementType.SOCIAL: "Achievements for social learning activities",
        AchievementType.CHALLENGE: "Achievements for completing challenges",
        AchievementType.CONSISTENCY: "Achievements for consistent learning habits",
        AchievementType.EXPLORATION: "Achievements for exploring new topics",
        AchievementType.IMPROVEMENT: "Achievements for improving performance"
    }
    return descriptions.get(achievement_type, "Unknown achievement type")

def _get_badge_level_description(badge_level: BadgeLevel) -> str:
    """Get description for badge level"""
    descriptions = {
        BadgeLevel.BRONZE: "Entry-level achievement",
        BadgeLevel.SILVER: "Intermediate achievement",
        BadgeLevel.GOLD: "Advanced achievement",
        BadgeLevel.PLATINUM: "Expert-level achievement",
        BadgeLevel.DIAMOND: "Master-level achievement"
    }
    return descriptions.get(badge_level, "Unknown badge level")

def _get_learning_style_description(learning_style: LearningStyle) -> str:
    """Get description for learning style"""
    descriptions = {
        LearningStyle.VISUAL: "Learn best through visual aids and diagrams",
        LearningStyle.AUDITORY: "Learn best through listening and discussion",
        LearningStyle.KINESTHETIC: "Learn best through hands-on practice",
        LearningStyle.READING: "Learn best through reading and writing",
        LearningStyle.MIXED: "Learn effectively through multiple methods"
    }
    return descriptions.get(learning_style, "Unknown learning style")

def _get_difficulty_preference_description(difficulty_pref: DifficultyPreference) -> str:
    """Get description for difficulty preference"""
    descriptions = {
        DifficultyPreference.EASY: "Prefer easier content to build confidence",
        DifficultyPreference.MODERATE: "Prefer moderately challenging content",
        DifficultyPreference.CHALLENGING: "Prefer challenging content for growth",
        DifficultyPreference.ADAPTIVE: "Prefer difficulty that adapts to performance"
    }
    return descriptions.get(difficulty_pref, "Unknown difficulty preference")