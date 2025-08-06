"""
Gamification and Personalization Service for Educational Enhancement System

This service implements achievement systems with badges and progress rewards,
personalized study recommendations based on learning patterns, social learning
features with peer comparison and collaboration, and adaptive content difficulty
based on individual learning curves.
"""

import asyncio
import json
import logging
import math
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from core.database import (
    get_db,
    Achievement as AchievementModel,
    StudySession as StudySessionModel,
    LearningProgress as LearningProgressModel,
    User
)

# Try to import QuizAttemptModel, but handle if it doesn't exist
try:
    from core.database import QuizAttempt as QuizAttemptModel
except ImportError:
    QuizAttemptModel = None

logger = logging.getLogger(__name__)

class AchievementType(str, Enum):
    """Types of achievements"""
    STREAK = "streak"                    # Study streak achievements
    MASTERY = "mastery"                  # Topic mastery achievements
    PROGRESS = "progress"                # Progress milestones
    SOCIAL = "social"                    # Social learning achievements
    CHALLENGE = "challenge"              # Challenge completions
    CONSISTENCY = "consistency"          # Consistent learning
    EXPLORATION = "exploration"          # Exploring new topics
    IMPROVEMENT = "improvement"          # Performance improvements

class BadgeLevel(str, Enum):
    """Badge levels"""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"

class LearningStyle(str, Enum):
    """Learning style preferences"""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING = "reading"
    MIXED = "mixed"

class DifficultyPreference(str, Enum):
    """Difficulty preferences"""
    EASY = "easy"
    MODERATE = "moderate"
    CHALLENGING = "challenging"
    ADAPTIVE = "adaptive"

@dataclass
class Achievement:
    """Represents a user achievement"""
    id: str
    user_id: str
    achievement_type: AchievementType
    title: str
    description: str
    badge_level: BadgeLevel
    points: int
    earned_at: datetime
    progress: float  # 0.0 to 1.0 for partial achievements
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class UserProfile:
    """Enhanced user profile for personalization"""
    user_id: str
    learning_style: LearningStyle
    difficulty_preference: DifficultyPreference
    study_time_preference: str  # "morning", "afternoon", "evening", "night"
    session_length_preference: int  # minutes
    motivation_factors: List[str]
    interests: List[str]
    goals: List[str]
    total_points: int
    level: int
    badges: List[str]
    created_at: datetime
    updated_at: datetime

@dataclass
class PersonalizedRecommendation:
    """Personalized study recommendation"""
    type: str  # "topic", "difficulty", "timing", "method"
    content: str
    reason: str
    confidence: float  # 0.0 to 1.0
    estimated_benefit: float  # 0.0 to 1.0
    suggested_duration: int  # minutes
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class SocialLearningData:
    """Social learning statistics and comparisons"""
    user_rank: int
    total_users: int
    peer_group_average: float
    user_score: float
    improvement_rank: int
    study_streak_rank: int
    collaborative_sessions: int
    peer_interactions: int

@dataclass
class LearningChallenge:
    """Learning challenge definition"""
    id: str
    title: str
    description: str
    challenge_type: str  # "streak", "mastery", "speed", "accuracy"
    target_value: float
    duration_days: int
    points_reward: int
    badge_reward: Optional[str]
    participants: int
    start_date: datetime
    end_date: datetime

class GamificationService:
    """Service for gamification and personalization features"""
    
    def __init__(self):
        # Achievement definitions
        self.achievement_definitions = self._load_achievement_definitions()
        
        # Points system
        self.points_system = {
            "quiz_completion": 10,
            "perfect_quiz": 25,
            "study_session": 5,
            "streak_day": 15,
            "topic_mastery": 100,
            "helping_peer": 20,
            "challenge_completion": 50
        }
        
        # Level thresholds
        self.level_thresholds = [0, 100, 250, 500, 1000, 2000, 4000, 8000, 15000, 30000]

    async def award_achievement(
        self,
        user_id: str,
        achievement_type: AchievementType,
        context: Dict[str, Any] = None
    ) -> Optional[Achievement]:
        """Award an achievement to a user"""
        try:
            # Check if user qualifies for this achievement
            achievement_def = await self._check_achievement_eligibility(
                user_id, achievement_type, context or {}
            )
            
            if not achievement_def:
                return None
            
            # Check if user already has this achievement
            existing = await self._get_user_achievement(user_id, achievement_def["id"])
            if existing:
                return None
            
            # Create achievement
            achievement = Achievement(
                id=f"achievement_{user_id}_{achievement_def['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                user_id=user_id,
                achievement_type=achievement_type,
                title=achievement_def["title"],
                description=achievement_def["description"],
                badge_level=BadgeLevel(achievement_def["badge_level"]),
                points=achievement_def["points"],
                earned_at=datetime.now(),
                progress=1.0,
                metadata=context or {}
            )
            
            # Store achievement
            await self._store_achievement(achievement)
            
            # Update user points and level
            await self._update_user_points(user_id, achievement.points)
            
            logger.info(f"Awarded achievement '{achievement.title}' to user {user_id}")
            return achievement
            
        except Exception as e:
            logger.error(f"Error awarding achievement: {str(e)}")
            return None

    async def get_user_achievements(self, user_id: str) -> List[Achievement]:
        """Get all achievements for a user"""
        try:
            db = next(get_db())
            try:
                db_achievements = db.query(AchievementModel).filter(
                    AchievementModel.user_id == user_id
                ).order_by(AchievementModel.earned_at.desc()).all()
                
                achievements = []
                for db_achievement in db_achievements:
                    achievements.append(Achievement(
                        id=db_achievement.id,
                        user_id=db_achievement.user_id,
                        achievement_type=AchievementType(db_achievement.achievement_type),
                        title=db_achievement.title,
                        description=db_achievement.description,
                        badge_level=BadgeLevel("gold"),  # Default, would be stored in metadata
                        points=db_achievement.points,
                        earned_at=db_achievement.earned_at,
                        progress=1.0,
                        metadata=db_achievement.achievement_metadata or {}
                    ))
                
                return achievements
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting user achievements: {str(e)}")
            return []

    async def generate_personalized_recommendations(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[PersonalizedRecommendation]:
        """Generate personalized study recommendations"""
        try:
            # Get user profile and learning history
            user_profile = await self._get_user_profile(user_id)
            learning_history = await self._get_learning_history(user_id)
            
            recommendations = []
            
            # Topic recommendations based on performance
            topic_recs = await self._generate_topic_recommendations(user_id, learning_history)
            recommendations.extend(topic_recs)
            
            # Difficulty recommendations
            difficulty_recs = await self._generate_difficulty_recommendations(user_id, learning_history)
            recommendations.extend(difficulty_recs)
            
            # Timing recommendations
            timing_recs = await self._generate_timing_recommendations(user_id, user_profile)
            recommendations.extend(timing_recs)
            
            # Method recommendations
            method_recs = await self._generate_method_recommendations(user_id, user_profile)
            recommendations.extend(method_recs)
            
            # Sort by confidence and estimated benefit
            recommendations.sort(
                key=lambda x: (x.confidence * x.estimated_benefit), 
                reverse=True
            )
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error generating personalized recommendations: {str(e)}")
            return []

    async def get_social_learning_data(self, user_id: str) -> SocialLearningData:
        """Get social learning statistics and peer comparisons"""
        try:
            db = next(get_db())
            try:
                # Get user's total points
                user_achievements = db.query(AchievementModel).filter(
                    AchievementModel.user_id == user_id
                ).all()
                user_points = sum(achievement.points for achievement in user_achievements)
                
                # Get all users' points for ranking
                all_user_points = {}
                all_achievements = db.query(AchievementModel).all()
                for achievement in all_achievements:
                    if achievement.user_id not in all_user_points:
                        all_user_points[achievement.user_id] = 0
                    all_user_points[achievement.user_id] += achievement.points
                
                # Calculate rankings
                sorted_users = sorted(all_user_points.items(), key=lambda x: x[1], reverse=True)
                user_rank = next((i + 1 for i, (uid, _) in enumerate(sorted_users) if uid == user_id), len(sorted_users))
                
                # Calculate peer group average (users within similar range)
                peer_group = [points for uid, points in sorted_users if abs(points - user_points) <= user_points * 0.2]
                peer_group_average = sum(peer_group) / len(peer_group) if peer_group else user_points
                
                # Get study streak ranking (simplified)
                study_sessions = db.query(StudySessionModel).filter(
                    StudySessionModel.user_id == user_id
                ).count()
                
                return SocialLearningData(
                    user_rank=user_rank,
                    total_users=len(all_user_points),
                    peer_group_average=peer_group_average,
                    user_score=user_points,
                    improvement_rank=user_rank,  # Simplified
                    study_streak_rank=user_rank,  # Simplified
                    collaborative_sessions=0,  # Would track collaborative sessions
                    peer_interactions=0  # Would track peer interactions
                )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting social learning data: {str(e)}")
            return SocialLearningData(
                user_rank=1,
                total_users=1,
                peer_group_average=0.0,
                user_score=0.0,
                improvement_rank=1,
                study_streak_rank=1,
                collaborative_sessions=0,
                peer_interactions=0
            )

    async def adapt_content_difficulty(
        self,
        user_id: str,
        topic: str,
        current_difficulty: float
    ) -> float:
        """Adapt content difficulty based on user's learning curve"""
        try:
            # Get user's performance history for this topic
            db = next(get_db())
            try:
                progress_record = db.query(LearningProgressModel).filter(
                    LearningProgressModel.user_id == user_id,
                    LearningProgressModel.topic == topic
                ).first()
                
                if not progress_record:
                    return current_difficulty
                
                # Analyze performance
                competency = progress_record.competency_level
                study_count = progress_record.study_count
                average_score = progress_record.average_score
                
                # Adaptation rules
                if competency >= 0.8 and average_score >= 0.8:
                    # User is doing well, increase difficulty
                    new_difficulty = min(1.0, current_difficulty + 0.1)
                elif competency <= 0.4 or average_score <= 0.5:
                    # User is struggling, decrease difficulty
                    new_difficulty = max(0.1, current_difficulty - 0.1)
                elif study_count >= 5 and competency >= 0.6:
                    # Gradual increase for consistent performers
                    new_difficulty = min(1.0, current_difficulty + 0.05)
                else:
                    # Keep current difficulty
                    new_difficulty = current_difficulty
                
                logger.info(f"Adapted difficulty for {topic}: {current_difficulty:.2f} -> {new_difficulty:.2f}")
                return new_difficulty
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error adapting content difficulty: {str(e)}")
            return current_difficulty

    async def create_learning_challenge(
        self,
        title: str,
        description: str,
        challenge_type: str,
        target_value: float,
        duration_days: int,
        points_reward: int
    ) -> LearningChallenge:
        """Create a new learning challenge"""
        try:
            challenge = LearningChallenge(
                id=f"challenge_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                title=title,
                description=description,
                challenge_type=challenge_type,
                target_value=target_value,
                duration_days=duration_days,
                points_reward=points_reward,
                badge_reward=None,
                participants=0,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=duration_days)
            )
            
            # Store challenge (would need a challenges table)
            logger.info(f"Created learning challenge: {challenge.title}")
            return challenge
            
        except Exception as e:
            logger.error(f"Error creating learning challenge: {str(e)}")
            raise

    async def get_user_level_and_progress(self, user_id: str) -> Dict[str, Any]:
        """Get user's current level and progress to next level"""
        try:
            # Get total points
            total_points = await self._get_user_total_points(user_id)
            
            # Calculate level
            current_level = 0
            for i, threshold in enumerate(self.level_thresholds):
                if total_points >= threshold:
                    current_level = i
                else:
                    break
            
            # Calculate progress to next level
            if current_level < len(self.level_thresholds) - 1:
                current_threshold = self.level_thresholds[current_level]
                next_threshold = self.level_thresholds[current_level + 1]
                progress_to_next = (total_points - current_threshold) / (next_threshold - current_threshold)
                points_to_next = next_threshold - total_points
            else:
                progress_to_next = 1.0
                points_to_next = 0
            
            return {
                "current_level": current_level,
                "total_points": total_points,
                "progress_to_next_level": progress_to_next,
                "points_to_next_level": points_to_next,
                "level_name": self._get_level_name(current_level)
            }
            
        except Exception as e:
            logger.error(f"Error getting user level: {str(e)}")
            return {
                "current_level": 0,
                "total_points": 0,
                "progress_to_next_level": 0.0,
                "points_to_next_level": 100,
                "level_name": "Novice"
            }

    def _load_achievement_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Load achievement definitions"""
        return {
            "first_quiz": {
                "id": "first_quiz",
                "title": "First Steps",
                "description": "Complete your first quiz",
                "badge_level": "bronze",
                "points": 25,
                "type": AchievementType.PROGRESS
            },
            "quiz_master": {
                "id": "quiz_master",
                "title": "Quiz Master",
                "description": "Complete 10 quizzes with 90%+ accuracy",
                "badge_level": "gold",
                "points": 100,
                "type": AchievementType.MASTERY
            },
            "study_streak_7": {
                "id": "study_streak_7",
                "title": "Week Warrior",
                "description": "Study for 7 consecutive days",
                "badge_level": "silver",
                "points": 75,
                "type": AchievementType.STREAK
            },
            "study_streak_30": {
                "id": "study_streak_30",
                "title": "Monthly Master",
                "description": "Study for 30 consecutive days",
                "badge_level": "platinum",
                "points": 300,
                "type": AchievementType.STREAK
            },
            "topic_explorer": {
                "id": "topic_explorer",
                "title": "Topic Explorer",
                "description": "Study 5 different topics",
                "badge_level": "bronze",
                "points": 50,
                "type": AchievementType.EXPLORATION
            },
            "improvement_champion": {
                "id": "improvement_champion",
                "title": "Improvement Champion",
                "description": "Improve competency by 50% in any topic",
                "badge_level": "gold",
                "points": 150,
                "type": AchievementType.IMPROVEMENT
            }
        }

    async def _check_achievement_eligibility(
        self,
        user_id: str,
        achievement_type: AchievementType,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if user is eligible for an achievement"""
        try:
            # Get relevant achievement definitions
            eligible_achievements = [
                defn for defn in self.achievement_definitions.values()
                if defn["type"] == achievement_type
            ]
            
            for achievement_def in eligible_achievements:
                if await self._meets_achievement_criteria(user_id, achievement_def, context):
                    return achievement_def
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking achievement eligibility: {str(e)}")
            return None

    async def _meets_achievement_criteria(
        self,
        user_id: str,
        achievement_def: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if user meets specific achievement criteria"""
        try:
            achievement_id = achievement_def["id"]
            
            if achievement_id == "first_quiz":
                return context.get("event") == "quiz_completed"
            
            elif achievement_id == "quiz_master":
                # Check if user has completed 10 quizzes with 90%+ accuracy
                # This would require querying quiz attempts
                return False  # Simplified for now
            
            elif achievement_id == "study_streak_7":
                # Check if user has 7-day study streak
                streak = await self._calculate_study_streak(user_id)
                return streak >= 7
            
            elif achievement_id == "study_streak_30":
                # Check if user has 30-day study streak
                streak = await self._calculate_study_streak(user_id)
                return streak >= 30
            
            elif achievement_id == "topic_explorer":
                # Check if user has studied 5 different topics
                topic_count = await self._count_studied_topics(user_id)
                return topic_count >= 5
            
            elif achievement_id == "improvement_champion":
                # Check if user improved competency by 50% in any topic
                return context.get("improvement_percentage", 0) >= 0.5
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking achievement criteria: {str(e)}")
            return False

    async def _get_user_achievement(self, user_id: str, achievement_id: str) -> Optional[Achievement]:
        """Check if user already has a specific achievement"""
        try:
            db = next(get_db())
            try:
                db_achievement = db.query(AchievementModel).filter(
                    AchievementModel.user_id == user_id,
                    AchievementModel.achievement_metadata.contains(f'"achievement_id": "{achievement_id}"')
                ).first()
                
                return db_achievement is not None
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error checking existing achievement: {str(e)}")
            return None

    async def _store_achievement(self, achievement: Achievement):
        """Store achievement in database"""
        try:
            db = next(get_db())
            try:
                db_achievement = AchievementModel(
                    id=achievement.id,
                    user_id=achievement.user_id,
                    achievement_type=achievement.achievement_type.value,
                    title=achievement.title,
                    description=achievement.description,
                    earned_at=achievement.earned_at,
                    points=achievement.points,
                    achievement_metadata={
                        "badge_level": achievement.badge_level.value,
                        "progress": achievement.progress,
                        **achievement.metadata
                    }
                )
                db.add(db_achievement)
                db.commit()
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error storing achievement: {str(e)}")
            raise

    async def _update_user_points(self, user_id: str, points: int):
        """Update user's total points"""
        # This would update a user profile table with total points
        # For now, we'll just log it
        logger.info(f"Added {points} points to user {user_id}")

    async def _get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile for personalization"""
        # Simplified implementation - would load from user profile table
        return UserProfile(
            user_id=user_id,
            learning_style=LearningStyle.MIXED,
            difficulty_preference=DifficultyPreference.ADAPTIVE,
            study_time_preference="evening",
            session_length_preference=30,
            motivation_factors=["achievement", "progress"],
            interests=["technology", "science"],
            goals=["improve skills", "learn new topics"],
            total_points=0,
            level=1,
            badges=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    async def _get_learning_history(self, user_id: str) -> Dict[str, Any]:
        """Get user's learning history"""
        try:
            db = next(get_db())
            try:
                # Get study sessions
                sessions = db.query(StudySessionModel).filter(
                    StudySessionModel.user_id == user_id
                ).order_by(StudySessionModel.started_at.desc()).limit(50).all()
                
                # Get learning progress
                progress_records = db.query(LearningProgressModel).filter(
                    LearningProgressModel.user_id == user_id
                ).all()
                
                return {
                    "recent_sessions": len(sessions),
                    "topics_studied": len(progress_records),
                    "average_session_score": sum(s.performance_score or 0 for s in sessions) / len(sessions) if sessions else 0,
                    "study_frequency": len(sessions) / 30 if sessions else 0  # sessions per day over last 30 days
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting learning history: {str(e)}")
            return {}

    async def _generate_topic_recommendations(self, user_id: str, history: Dict[str, Any]) -> List[PersonalizedRecommendation]:
        """Generate topic-based recommendations"""
        recommendations = []
        
        if history.get("topics_studied", 0) < 3:
            recommendations.append(PersonalizedRecommendation(
                type="topic",
                content="Explore new topics to broaden your knowledge base",
                reason="You've studied fewer than 3 topics",
                confidence=0.8,
                estimated_benefit=0.7,
                suggested_duration=30
            ))
        
        return recommendations

    async def _generate_difficulty_recommendations(self, user_id: str, history: Dict[str, Any]) -> List[PersonalizedRecommendation]:
        """Generate difficulty-based recommendations"""
        recommendations = []
        
        avg_score = history.get("average_session_score", 0)
        if avg_score > 0.8:
            recommendations.append(PersonalizedRecommendation(
                type="difficulty",
                content="Try more challenging content to accelerate learning",
                reason=f"Your average score is {avg_score:.1%}, indicating readiness for harder material",
                confidence=0.7,
                estimated_benefit=0.8,
                suggested_duration=45
            ))
        elif avg_score < 0.5:
            recommendations.append(PersonalizedRecommendation(
                type="difficulty",
                content="Focus on easier content to build confidence",
                reason=f"Your average score is {avg_score:.1%}, suggesting need for foundational work",
                confidence=0.8,
                estimated_benefit=0.6,
                suggested_duration=20
            ))
        
        return recommendations

    async def _generate_timing_recommendations(self, user_id: str, profile: Optional[UserProfile]) -> List[PersonalizedRecommendation]:
        """Generate timing-based recommendations"""
        recommendations = []
        
        if profile and profile.study_time_preference:
            recommendations.append(PersonalizedRecommendation(
                type="timing",
                content=f"Schedule study sessions during your preferred {profile.study_time_preference} time",
                reason="Studying during your optimal time improves retention",
                confidence=0.6,
                estimated_benefit=0.5,
                suggested_duration=profile.session_length_preference if profile else 30
            ))
        
        return recommendations

    async def _generate_method_recommendations(self, user_id: str, profile: Optional[UserProfile]) -> List[PersonalizedRecommendation]:
        """Generate method-based recommendations"""
        recommendations = []
        
        if profile and profile.learning_style != LearningStyle.MIXED:
            style_methods = {
                LearningStyle.VISUAL: "Use diagrams, charts, and visual aids",
                LearningStyle.AUDITORY: "Try audio content and discussion-based learning",
                LearningStyle.KINESTHETIC: "Engage in hands-on practice and interactive exercises",
                LearningStyle.READING: "Focus on text-based materials and written exercises"
            }
            
            method = style_methods.get(profile.learning_style, "Use varied learning methods")
            recommendations.append(PersonalizedRecommendation(
                type="method",
                content=method,
                reason=f"Matches your {profile.learning_style.value} learning style",
                confidence=0.7,
                estimated_benefit=0.6,
                suggested_duration=profile.session_length_preference if profile else 30
            ))
        
        return recommendations

    async def get_peer_comparison_data(self, user_id: str) -> Dict[str, Any]:
        """Get detailed peer comparison data for social learning"""
        try:
            db = next(get_db())
            try:
                # Get user's performance metrics
                user_achievements = db.query(AchievementModel).filter(
                    AchievementModel.user_id == user_id
                ).all()
                user_total_points = sum(a.points for a in user_achievements)
                
                # Get user's study sessions
                user_sessions = db.query(StudySessionModel).filter(
                    StudySessionModel.user_id == user_id
                ).all()
                user_avg_score = sum(s.performance_score or 0 for s in user_sessions) / len(user_sessions) if user_sessions else 0
                
                # Get all users' data for comparison
                all_achievements = db.query(AchievementModel).all()
                all_sessions = db.query(StudySessionModel).all()
                
                # Calculate peer statistics
                user_points_by_user = {}
                user_scores_by_user = {}
                
                for achievement in all_achievements:
                    if achievement.user_id not in user_points_by_user:
                        user_points_by_user[achievement.user_id] = 0
                    user_points_by_user[achievement.user_id] += achievement.points
                
                for session in all_sessions:
                    if session.user_id not in user_scores_by_user:
                        user_scores_by_user[session.user_id] = []
                    if session.performance_score:
                        user_scores_by_user[session.user_id].append(session.performance_score)
                
                # Calculate averages
                peer_avg_points = sum(user_points_by_user.values()) / len(user_points_by_user) if user_points_by_user else 0
                peer_scores = [sum(scores)/len(scores) for scores in user_scores_by_user.values() if scores]
                peer_avg_score = sum(peer_scores) / len(peer_scores) if peer_scores else 0
                
                # Calculate percentiles
                all_points = list(user_points_by_user.values())
                all_points.sort()
                user_points_percentile = (sum(1 for p in all_points if p <= user_total_points) / len(all_points)) * 100 if all_points else 50
                
                all_avg_scores = peer_scores
                all_avg_scores.sort()
                user_score_percentile = (sum(1 for s in all_avg_scores if s <= user_avg_score) / len(all_avg_scores)) * 100 if all_avg_scores else 50
                
                return {
                    "user_metrics": {
                        "total_points": user_total_points,
                        "average_score": user_avg_score,
                        "study_sessions": len(user_sessions),
                        "achievements_count": len(user_achievements)
                    },
                    "peer_comparison": {
                        "points_percentile": user_points_percentile,
                        "score_percentile": user_score_percentile,
                        "peer_avg_points": peer_avg_points,
                        "peer_avg_score": peer_avg_score,
                        "total_peers": len(user_points_by_user)
                    },
                    "performance_insights": {
                        "points_vs_peers": "above_average" if user_total_points > peer_avg_points else "below_average",
                        "score_vs_peers": "above_average" if user_avg_score > peer_avg_score else "below_average",
                        "improvement_areas": await self._identify_improvement_areas(user_id, peer_avg_score)
                    }
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting peer comparison data: {str(e)}")
            return {}

    async def create_study_group(self, creator_id: str, name: str, description: str, max_members: int = 10) -> Dict[str, Any]:
        """Create a collaborative study group"""
        try:
            study_group = {
                "id": f"group_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "name": name,
                "description": description,
                "creator_id": creator_id,
                "members": [creator_id],
                "max_members": max_members,
                "created_at": datetime.now(),
                "group_stats": {
                    "total_study_sessions": 0,
                    "average_group_score": 0.0,
                    "collaborative_challenges": 0
                },
                "group_achievements": []
            }
            
            # In a real implementation, this would be stored in a database
            logger.info(f"Created study group '{name}' with ID {study_group['id']}")
            return study_group
            
        except Exception as e:
            logger.error(f"Error creating study group: {str(e)}")
            raise

    async def join_study_group(self, user_id: str, group_id: str) -> bool:
        """Join a study group"""
        try:
            # In a real implementation, this would update the database
            logger.info(f"User {user_id} joined study group {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error joining study group: {str(e)}")
            return False

    async def get_collaborative_challenges(self, user_id: str) -> List[Dict[str, Any]]:
        """Get available collaborative challenges"""
        try:
            # Sample collaborative challenges
            challenges = [
                {
                    "id": "collab_1",
                    "title": "Team Knowledge Quest",
                    "description": "Work together to master 5 topics in a week",
                    "type": "collaborative_mastery",
                    "participants_needed": 3,
                    "current_participants": 1,
                    "duration_days": 7,
                    "team_reward_points": 200,
                    "individual_reward_points": 50,
                    "start_date": datetime.now(),
                    "requirements": ["Active study group membership", "Minimum 3 study sessions per week"]
                },
                {
                    "id": "collab_2",
                    "title": "Peer Teaching Challenge",
                    "description": "Teach and learn from peers in your study group",
                    "type": "peer_teaching",
                    "participants_needed": 2,
                    "current_participants": 0,
                    "duration_days": 14,
                    "team_reward_points": 300,
                    "individual_reward_points": 75,
                    "start_date": datetime.now() + timedelta(days=1),
                    "requirements": ["Study group membership", "Complete at least 2 teaching sessions"]
                }
            ]
            
            return challenges
            
        except Exception as e:
            logger.error(f"Error getting collaborative challenges: {str(e)}")
            return []

    async def generate_adaptive_content_recommendations(self, user_id: str, topic: str) -> Dict[str, Any]:
        """Generate adaptive content recommendations based on learning curve analysis"""
        try:
            db = next(get_db())
            try:
                # Get user's learning progress for the topic
                progress = db.query(LearningProgressModel).filter(
                    LearningProgressModel.user_id == user_id,
                    LearningProgressModel.topic == topic
                ).first()
                
                if not progress:
                    return {
                        "recommended_difficulty": 0.3,
                        "content_type": "foundational",
                        "study_approach": "structured_learning",
                        "session_length": 20,
                        "reason": "No previous learning data for this topic",
                        "learning_metrics": {
                            "current_competency": 0.0,
                            "average_score": 0.0,
                            "study_count": 0,
                            "learning_velocity": 0.0
                        }
                    }
                
                # Analyze learning curve
                competency = progress.competency_level
                study_count = progress.study_count
                avg_score = progress.average_score
                
                # Get recent quiz attempts for trend analysis (if available)
                recent_scores = []
                if QuizAttemptModel:
                    try:
                        recent_attempts = db.query(QuizAttemptModel).filter(
                            QuizAttemptModel.user_id == user_id
                        ).order_by(QuizAttemptModel.started_at.desc()).limit(5).all()
                        
                        recent_scores = [attempt.score for attempt in recent_attempts if attempt.score is not None]
                    except Exception:
                        # If quiz attempts table doesn't exist or has issues, use empty list
                        recent_scores = []
                
                # Calculate learning velocity
                learning_velocity = self._calculate_learning_velocity(recent_scores)
                
                # Determine optimal difficulty and content type
                if competency >= 0.8 and avg_score >= 0.8:
                    # Advanced learner - challenge them
                    recommended_difficulty = min(1.0, competency + 0.2)
                    content_type = "advanced_application"
                    study_approach = "problem_solving"
                    session_length = 45
                    reason = "High competency detected - ready for advanced challenges"
                    
                elif competency <= 0.4 or avg_score <= 0.5:
                    # Struggling learner - provide support
                    recommended_difficulty = max(0.1, competency - 0.1)
                    content_type = "foundational_review"
                    study_approach = "guided_practice"
                    session_length = 15
                    reason = "Foundational gaps detected - focusing on core concepts"
                    
                elif learning_velocity > 0.1:
                    # Fast learner - accelerate
                    recommended_difficulty = min(1.0, competency + 0.15)
                    content_type = "accelerated_learning"
                    study_approach = "discovery_based"
                    session_length = 35
                    reason = "Positive learning trend - accelerating difficulty"
                    
                else:
                    # Steady learner - maintain pace
                    recommended_difficulty = competency + 0.05
                    content_type = "progressive_practice"
                    study_approach = "structured_practice"
                    session_length = 30
                    reason = "Steady progress - maintaining optimal challenge level"
                
                return {
                    "recommended_difficulty": recommended_difficulty,
                    "content_type": content_type,
                    "study_approach": study_approach,
                    "session_length": session_length,
                    "reason": reason,
                    "learning_metrics": {
                        "current_competency": competency,
                        "average_score": avg_score,
                        "study_count": study_count,
                        "learning_velocity": learning_velocity
                    }
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error generating adaptive content recommendations: {str(e)}")
            return {
                "recommended_difficulty": 0.3,
                "content_type": "foundational",
                "study_approach": "structured_learning",
                "session_length": 20,
                "reason": "Error occurred during analysis",
                "learning_metrics": {
                    "current_competency": 0.0,
                    "average_score": 0.0,
                    "study_count": 0,
                    "learning_velocity": 0.0
                }
            }

    async def track_peer_interactions(self, user_id: str, interaction_type: str, peer_id: str, context: Dict[str, Any] = None) -> bool:
        """Track peer interactions for social learning analytics"""
        try:
            interaction = {
                "id": f"interaction_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "user_id": user_id,
                "peer_id": peer_id,
                "interaction_type": interaction_type,  # "help_given", "help_received", "collaboration", "discussion"
                "context": context or {},
                "timestamp": datetime.now()
            }
            
            # In a real implementation, this would be stored in a database
            logger.info(f"Tracked peer interaction: {interaction_type} between {user_id} and {peer_id}")
            
            # Award social learning points
            if interaction_type in ["help_given", "collaboration"]:
                await self.award_achievement(user_id, AchievementType.SOCIAL, {
                    "interaction_type": interaction_type,
                    "peer_id": peer_id
                })
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking peer interaction: {str(e)}")
            return False

    async def get_personalized_study_plan(self, user_id: str, goals: List[str], time_available_minutes: int) -> Dict[str, Any]:
        """Generate a personalized study plan based on user goals and available time"""
        try:
            # Get user profile and learning history
            user_profile = await self._get_user_profile(user_id)
            learning_history = await self._get_learning_history(user_id)
            
            # Get user's current competencies
            db = next(get_db())
            try:
                progress_records = db.query(LearningProgressModel).filter(
                    LearningProgressModel.user_id == user_id
                ).all()
                
                competencies = {record.topic: record.competency_level for record in progress_records}
                
            finally:
                db.close()
            
            # Generate study plan
            study_plan = {
                "plan_id": f"plan_{user_id}_{datetime.now().strftime('%Y%m%d')}",
                "user_id": user_id,
                "goals": goals,
                "total_time_minutes": time_available_minutes,
                "generated_at": datetime.now(),
                "sessions": []
            }
            
            # Allocate time based on goals and competencies
            time_per_goal = time_available_minutes // len(goals) if goals else time_available_minutes
            
            for goal in goals:
                current_competency = competencies.get(goal, 0.0)
                
                # Determine session structure based on competency
                if current_competency < 0.3:
                    session_type = "foundational_learning"
                    recommended_activities = ["concept_review", "basic_practice", "guided_exercises"]
                elif current_competency < 0.7:
                    session_type = "skill_building"
                    recommended_activities = ["practice_problems", "application_exercises", "quiz_practice"]
                else:
                    session_type = "mastery_refinement"
                    recommended_activities = ["advanced_problems", "peer_teaching", "creative_application"]
                
                session = {
                    "topic": goal,
                    "allocated_time_minutes": time_per_goal,
                    "session_type": session_type,
                    "current_competency": current_competency,
                    "target_competency": min(1.0, current_competency + 0.2),
                    "recommended_activities": recommended_activities,
                    "difficulty_level": await self.adapt_content_difficulty(user_id, goal, current_competency),
                    "priority": self._calculate_goal_priority(goal, current_competency, learning_history)
                }
                
                study_plan["sessions"].append(session)
            
            # Sort sessions by priority
            study_plan["sessions"].sort(key=lambda x: x["priority"], reverse=True)
            
            return study_plan
            
        except Exception as e:
            logger.error(f"Error generating personalized study plan: {str(e)}")
            return {}

    def _calculate_learning_velocity(self, recent_scores: List[float]) -> float:
        """Calculate learning velocity from recent scores"""
        if len(recent_scores) < 2:
            return 0.0
        
        # Calculate trend using simple linear regression
        n = len(recent_scores)
        x_values = list(range(n))
        
        # Calculate slope (learning velocity)
        x_mean = sum(x_values) / n
        y_mean = sum(recent_scores) / n
        
        numerator = sum((x_values[i] - x_mean) * (recent_scores[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        return slope

    async def _identify_improvement_areas(self, user_id: str, peer_avg_score: float) -> List[str]:
        """Identify areas where user can improve compared to peers"""
        try:
            db = next(get_db())
            try:
                # Get user's topic-specific performance
                progress_records = db.query(LearningProgressModel).filter(
                    LearningProgressModel.user_id == user_id
                ).all()
                
                improvement_areas = []
                
                for record in progress_records:
                    if record.average_score < peer_avg_score * 0.8:  # 20% below peer average
                        improvement_areas.append(record.topic)
                
                return improvement_areas[:3]  # Return top 3 areas
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error identifying improvement areas: {str(e)}")
            return []

    def _calculate_goal_priority(self, goal: str, current_competency: float, learning_history: Dict[str, Any]) -> float:
        """Calculate priority score for a learning goal"""
        # Base priority on competency gap
        competency_gap = 1.0 - current_competency
        
        # Adjust based on recent activity
        recent_sessions = learning_history.get("recent_sessions", 0)
        activity_factor = 1.0 + (recent_sessions / 10)  # Boost active learners
        
        # Adjust based on difficulty (harder topics get higher priority for advanced learners)
        difficulty_factor = 1.0
        if current_competency > 0.7:
            difficulty_factor = 1.2  # Prioritize challenging content for advanced learners
        
        priority = competency_gap * activity_factor * difficulty_factor
        return min(1.0, priority)

    def _get_level_name(self, level: int) -> str:
        """Get level name for a given level number"""
        level_names = [
            "Novice", "Apprentice", "Student", "Scholar", "Expert",
            "Master", "Sage", "Guru", "Legend", "Grandmaster"
        ]
        
        if level < len(level_names):
            return level_names[level]
        else:
            return f"Transcendent {level - len(level_names) + 1}"

    async def _calculate_study_streak(self, user_id: str) -> int:
        """Calculate current study streak for user"""
        try:
            db = next(get_db())
            try:
                # Get recent study sessions ordered by date
                sessions = db.query(StudySessionModel).filter(
                    StudySessionModel.user_id == user_id
                ).order_by(StudySessionModel.started_at.desc()).all()
                
                if not sessions:
                    return 0
                
                # Calculate streak
                streak = 0
                current_date = datetime.now().date()
                
                for session in sessions:
                    session_date = session.started_at.date()
                    
                    if session_date == current_date or session_date == current_date - timedelta(days=streak):
                        if session_date == current_date - timedelta(days=streak):
                            streak += 1
                            current_date = session_date
                    else:
                        break
                
                return streak
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error calculating study streak: {str(e)}")
            return 0

    async def _count_studied_topics(self, user_id: str) -> int:
        """Count number of different topics studied by user"""
        try:
            db = next(get_db())
            try:
                topics = db.query(LearningProgressModel.topic).filter(
                    LearningProgressModel.user_id == user_id
                ).distinct().count()
                
                return topics
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error counting studied topics: {str(e)}")
            return 0

    async def _get_user_total_points(self, user_id: str) -> int:
        """Get user's total points from achievements"""
        try:
            db = next(get_db())
            try:
                achievements = db.query(AchievementModel).filter(
                    AchievementModel.user_id == user_id
                ).all()
                
                return sum(achievement.points for achievement in achievements)
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting user total points: {str(e)}")
            return 0

    async def _calculate_study_streak(self, user_id: str) -> int:
        """Calculate current study streak"""
        try:
            db = next(get_db())
            try:
                # Get recent study sessions
                sessions = db.query(StudySessionModel).filter(
                    StudySessionModel.user_id == user_id
                ).order_by(StudySessionModel.started_at.desc()).all()
                
                if not sessions:
                    return 0
                
                # Calculate consecutive days
                streak = 0
                current_date = datetime.now().date()
                
                for i in range(365):  # Max 1 year
                    check_date = current_date - timedelta(days=i)
                    has_session = any(
                        session.started_at.date() == check_date
                        for session in sessions
                    )
                    
                    if has_session:
                        streak += 1
                    else:
                        break
                
                return streak
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error calculating study streak: {str(e)}")
            return 0

    async def _count_studied_topics(self, user_id: str) -> int:
        """Count number of topics user has studied"""
        try:
            db = next(get_db())
            try:
                count = db.query(LearningProgressModel).filter(
                    LearningProgressModel.user_id == user_id
                ).count()
                return count
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error counting studied topics: {str(e)}")
            return 0

    async def _get_user_total_points(self, user_id: str) -> int:
        """Get user's total points from achievements"""
        try:
            db = next(get_db())
            try:
                achievements = db.query(AchievementModel).filter(
                    AchievementModel.user_id == user_id
                ).all()
                
                return sum(achievement.points for achievement in achievements)
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting user total points: {str(e)}")
            return 0

    def _get_level_name(self, level: int) -> str:
        """Get level name based on level number"""
        level_names = [
            "Novice", "Learner", "Student", "Scholar", "Expert",
            "Master", "Guru", "Sage", "Legend", "Grandmaster"
        ]
        return level_names[min(level, len(level_names) - 1)]