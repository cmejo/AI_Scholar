"""
Learning Progress Tracking Service for Educational Enhancement System

This service provides comprehensive learning analytics with performance metrics,
knowledge gap identification, targeted recommendations, visual progress dashboards,
and competency mapping with skill development tracking.
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
    LearningProgress as LearningProgressModel,
    StudySession as StudySessionModel,
    Quiz as QuizModel,
    QuizAttempt as QuizAttemptModel,
    SpacedRepetitionItem as SRItemModel
)

logger = logging.getLogger(__name__)

class CompetencyLevel(str, Enum):
    """Competency levels for learning progress"""
    NOVICE = "novice"          # 0.0 - 0.2
    BEGINNER = "beginner"      # 0.2 - 0.4
    INTERMEDIATE = "intermediate"  # 0.4 - 0.6
    ADVANCED = "advanced"      # 0.6 - 0.8
    EXPERT = "expert"          # 0.8 - 1.0

class LearningGoalType(str, Enum):
    """Types of learning goals"""
    MASTERY = "mastery"        # Master a specific topic
    RETENTION = "retention"    # Maintain knowledge over time
    SPEED = "speed"           # Improve response time
    ACCURACY = "accuracy"     # Improve accuracy rate

@dataclass
class LearningProgress:
    """Represents learning progress for a specific topic"""
    id: str
    user_id: str
    topic: str
    competency_level: float  # 0.0 to 1.0
    last_studied: Optional[datetime]
    study_count: int
    average_score: float
    trend: str  # "improving", "stable", "declining"
    confidence_interval: Tuple[float, float]
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class KnowledgeGap:
    """Represents an identified knowledge gap"""
    topic: str
    gap_type: str  # "weak_foundation", "missing_connection", "outdated_knowledge"
    severity: float  # 0.0 to 1.0
    evidence: List[str]
    recommendations: List[str]
    related_topics: List[str]

@dataclass
class LearningTrajectory:
    """Represents learning trajectory over time"""
    topic: str
    time_points: List[datetime]
    competency_scores: List[float]
    study_sessions: List[int]
    trend_analysis: Dict[str, Any]
    predictions: Dict[str, Any]

@dataclass
class CompetencyMap:
    """Represents a user's competency across multiple topics"""
    user_id: str
    competencies: Dict[str, float]
    skill_tree: Dict[str, List[str]]  # Prerequisites and dependencies
    mastery_path: List[str]  # Recommended learning order
    generated_at: datetime

@dataclass
class LearningRecommendation:
    """Represents a personalized learning recommendation"""
    type: str  # "review", "advance", "practice", "explore"
    topic: str
    priority: float  # 0.0 to 1.0
    reason: str
    suggested_actions: List[str]
    estimated_time_minutes: int

class LearningProgressService:
    """Service for tracking and analyzing learning progress"""
    
    def __init__(self):
        self.competency_thresholds = {
            CompetencyLevel.NOVICE: (0.0, 0.2),
            CompetencyLevel.BEGINNER: (0.2, 0.4),
            CompetencyLevel.INTERMEDIATE: (0.4, 0.6),
            CompetencyLevel.ADVANCED: (0.6, 0.8),
            CompetencyLevel.EXPERT: (0.8, 1.0)
        }

    async def update_learning_progress(
        self,
        user_id: str,
        topic: str,
        performance_score: float,
        study_duration_minutes: int = None,
        metadata: Dict[str, Any] = None
    ) -> LearningProgress:
        """Update learning progress for a specific topic"""
        try:
            # Get existing progress or create new
            existing_progress = await self.get_topic_progress(user_id, topic)
            
            if existing_progress:
                # Update existing progress
                new_study_count = existing_progress.study_count + 1
                new_average_score = (
                    (existing_progress.average_score * existing_progress.study_count + performance_score) 
                    / new_study_count
                )
                
                # Calculate new competency level using weighted average
                competency_weight = 0.7  # Weight for new performance
                new_competency = (
                    existing_progress.competency_level * (1 - competency_weight) +
                    performance_score * competency_weight
                )
                
                progress = LearningProgress(
                    id=existing_progress.id,
                    user_id=user_id,
                    topic=topic,
                    competency_level=min(1.0, max(0.0, new_competency)),
                    last_studied=datetime.now(),
                    study_count=new_study_count,
                    average_score=new_average_score,
                    trend=await self._calculate_trend(user_id, topic),
                    confidence_interval=await self._calculate_confidence_interval(user_id, topic),
                    metadata=metadata or existing_progress.metadata
                )
            else:
                # Create new progress
                progress = LearningProgress(
                    id=f"progress_{user_id}_{topic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    user_id=user_id,
                    topic=topic,
                    competency_level=performance_score,
                    last_studied=datetime.now(),
                    study_count=1,
                    average_score=performance_score,
                    trend="new",
                    confidence_interval=(performance_score * 0.8, performance_score * 1.2),
                    metadata=metadata or {}
                )
            
            # Store in database
            await self._store_learning_progress(progress)
            
            logger.info(f"Updated learning progress for {topic}: competency={progress.competency_level:.2f}")
            return progress
            
        except Exception as e:
            logger.error(f"Error updating learning progress: {str(e)}")
            raise

    async def get_user_progress_overview(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive progress overview for a user"""
        try:
            db = next(get_db())
            try:
                # Get all progress records
                progress_records = db.query(LearningProgressModel).filter(
                    LearningProgressModel.user_id == user_id
                ).all()
                
                if not progress_records:
                    return {
                        'total_topics': 0,
                        'average_competency': 0.0,
                        'topics_by_level': {},
                        'recent_activity': [],
                        'overall_trend': 'no_data'
                    }
                
                # Calculate overview statistics
                total_topics = len(progress_records)
                competencies = [record.competency_level for record in progress_records]
                average_competency = sum(competencies) / len(competencies)
                
                # Group by competency level
                topics_by_level = {}
                for level in CompetencyLevel:
                    min_val, max_val = self.competency_thresholds[level]
                    topics_by_level[level.value] = [
                        record.topic for record in progress_records
                        if min_val <= record.competency_level < max_val
                    ]
                
                # Get recent activity
                recent_records = sorted(
                    [r for r in progress_records if r.last_studied],
                    key=lambda x: x.last_studied,
                    reverse=True
                )[:10]
                
                recent_activity = [
                    {
                        'topic': record.topic,
                        'competency_level': record.competency_level,
                        'last_studied': record.last_studied.isoformat() if record.last_studied else None,
                        'study_count': record.study_count
                    }
                    for record in recent_records
                ]
                
                # Calculate overall trend
                overall_trend = await self._calculate_overall_trend(user_id)
                
                return {
                    'total_topics': total_topics,
                    'average_competency': average_competency,
                    'topics_by_level': topics_by_level,
                    'recent_activity': recent_activity,
                    'overall_trend': overall_trend,
                    'generated_at': datetime.now().isoformat()
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting progress overview: {str(e)}")
            return {'error': str(e)}

    async def identify_knowledge_gaps(self, user_id: str) -> List[KnowledgeGap]:
        """Identify knowledge gaps and areas needing attention"""
        try:
            db = next(get_db())
            try:
                # Get all progress records
                progress_records = db.query(LearningProgressModel).filter(
                    LearningProgressModel.user_id == user_id
                ).all()
                
                gaps = []
                
                for record in progress_records:
                    # Identify weak foundations (low competency)
                    if record.competency_level < 0.3:
                        gaps.append(KnowledgeGap(
                            topic=record.topic,
                            gap_type="weak_foundation",
                            severity=1.0 - record.competency_level,
                            evidence=[
                                f"Competency level: {record.competency_level:.2f}",
                                f"Average score: {record.average_score:.2f}",
                                f"Study sessions: {record.study_count}"
                            ],
                            recommendations=[
                                "Review fundamental concepts",
                                "Practice basic exercises",
                                "Seek additional resources"
                            ],
                            related_topics=await self._find_related_topics(record.topic)
                        ))
                    
                    # Identify declining performance
                    if hasattr(record, 'progress_metadata') and record.progress_metadata:
                        metadata = record.progress_metadata
                        if 'trend' in metadata and metadata['trend'] == 'declining':
                            gaps.append(KnowledgeGap(
                                topic=record.topic,
                                gap_type="declining_performance",
                                severity=0.6,
                                evidence=[
                                    "Performance trend is declining",
                                    f"Last studied: {record.last_studied}"
                                ],
                                recommendations=[
                                    "Schedule regular review sessions",
                                    "Use spaced repetition",
                                    "Identify specific problem areas"
                                ],
                                related_topics=await self._find_related_topics(record.topic)
                            ))
                    
                    # Identify stale knowledge (not studied recently)
                    if record.last_studied and record.last_studied < datetime.now() - timedelta(days=30):
                        gaps.append(KnowledgeGap(
                            topic=record.topic,
                            gap_type="outdated_knowledge",
                            severity=0.4,
                            evidence=[
                                f"Last studied: {record.last_studied.strftime('%Y-%m-%d')}",
                                "Knowledge may be fading"
                            ],
                            recommendations=[
                                "Schedule refresher session",
                                "Quick review of key concepts",
                                "Test current knowledge level"
                            ],
                            related_topics=await self._find_related_topics(record.topic)
                        ))
                
                # Sort by severity
                gaps.sort(key=lambda x: x.severity, reverse=True)
                
                logger.info(f"Identified {len(gaps)} knowledge gaps for user {user_id}")
                return gaps
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error identifying knowledge gaps: {str(e)}")
            return []

    async def generate_learning_recommendations(self, user_id: str) -> List[LearningRecommendation]:
        """Generate personalized learning recommendations"""
        try:
            # Get user progress and knowledge gaps
            progress_overview = await self.get_user_progress_overview(user_id)
            knowledge_gaps = await self.identify_knowledge_gaps(user_id)
            
            recommendations = []
            
            # Recommendations based on knowledge gaps
            for gap in knowledge_gaps[:5]:  # Top 5 gaps
                if gap.gap_type == "weak_foundation":
                    recommendations.append(LearningRecommendation(
                        type="review",
                        topic=gap.topic,
                        priority=gap.severity,
                        reason=f"Weak foundation in {gap.topic}",
                        suggested_actions=gap.recommendations,
                        estimated_time_minutes=30
                    ))
                elif gap.gap_type == "outdated_knowledge":
                    recommendations.append(LearningRecommendation(
                        type="practice",
                        topic=gap.topic,
                        priority=gap.severity * 0.8,
                        reason=f"Knowledge in {gap.topic} needs refreshing",
                        suggested_actions=gap.recommendations,
                        estimated_time_minutes=15
                    ))
            
            # Recommendations for advancing strong areas
            if 'topics_by_level' in progress_overview:
                advanced_topics = progress_overview['topics_by_level'].get('advanced', [])
                for topic in advanced_topics[:3]:  # Top 3 advanced topics
                    recommendations.append(LearningRecommendation(
                        type="advance",
                        topic=topic,
                        priority=0.7,
                        reason=f"Ready to advance in {topic}",
                        suggested_actions=[
                            "Explore advanced concepts",
                            "Apply knowledge to complex problems",
                            "Teach or explain to others"
                        ],
                        estimated_time_minutes=45
                    ))
            
            # Exploration recommendations
            recent_activity = progress_overview.get('recent_activity', [])
            studied_topics = set(activity.get('topic', '') for activity in recent_activity if isinstance(activity, dict))
            if len(studied_topics) >= 3:
                recommendations.append(LearningRecommendation(
                    type="explore",
                    topic="new_domain",
                    priority=0.5,
                    reason="Expand knowledge to new areas",
                    suggested_actions=[
                        "Explore related fields",
                        "Take introductory courses",
                        "Read survey papers"
                    ],
                    estimated_time_minutes=60
                ))
            
            # Sort by priority
            recommendations.sort(key=lambda x: x.priority, reverse=True)
            
            logger.info(f"Generated {len(recommendations)} learning recommendations for user {user_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []

    async def get_learning_trajectory(self, user_id: str, topic: str) -> LearningTrajectory:
        """Get learning trajectory for a specific topic"""
        try:
            # Get historical data from study sessions and quiz attempts
            db = next(get_db())
            try:
                # Get study sessions
                sessions = db.query(StudySessionModel).filter(
                    StudySessionModel.user_id == user_id
                ).order_by(StudySessionModel.started_at).all()
                
                # Get quiz attempts (if available)
                quiz_attempts = db.query(QuizAttemptModel).join(QuizModel).filter(
                    QuizAttemptModel.user_id == user_id
                ).order_by(QuizAttemptModel.started_at).all()
                
                # Combine and sort by time
                time_points = []
                competency_scores = []
                study_sessions = []
                
                # Process study sessions
                for session in sessions:
                    if session.session_metadata and 'topic' in session.session_metadata:
                        if session.session_metadata['topic'] == topic:
                            time_points.append(session.started_at)
                            competency_scores.append(session.performance_score or 0.5)
                            study_sessions.append(1)
                
                # Process quiz attempts
                for attempt in quiz_attempts:
                    if attempt.score is not None and attempt.total_points:
                        score_ratio = attempt.score / attempt.total_points
                        time_points.append(attempt.started_at)
                        competency_scores.append(score_ratio)
                        study_sessions.append(0)  # Quiz, not study session
                
                # Sort by time
                combined = list(zip(time_points, competency_scores, study_sessions))
                combined.sort(key=lambda x: x[0])
                
                if combined:
                    time_points, competency_scores, study_sessions = zip(*combined)
                    time_points = list(time_points)
                    competency_scores = list(competency_scores)
                    study_sessions = list(study_sessions)
                else:
                    time_points = []
                    competency_scores = []
                    study_sessions = []
                
                # Analyze trends
                trend_analysis = await self._analyze_trajectory_trends(competency_scores)
                
                # Make predictions
                predictions = await self._predict_future_performance(competency_scores, time_points)
                
                return LearningTrajectory(
                    topic=topic,
                    time_points=time_points,
                    competency_scores=competency_scores,
                    study_sessions=study_sessions,
                    trend_analysis=trend_analysis,
                    predictions=predictions
                )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting learning trajectory: {str(e)}")
            return LearningTrajectory(
                topic=topic,
                time_points=[],
                competency_scores=[],
                study_sessions=[],
                trend_analysis={},
                predictions={}
            )

    async def create_competency_map(self, user_id: str) -> CompetencyMap:
        """Create a comprehensive competency map for the user"""
        try:
            db = next(get_db())
            try:
                # Get all progress records
                progress_records = db.query(LearningProgressModel).filter(
                    LearningProgressModel.user_id == user_id
                ).all()
                
                # Build competencies dictionary
                competencies = {
                    record.topic: record.competency_level
                    for record in progress_records
                }
                
                # Build skill tree (simplified - would need domain knowledge)
                skill_tree = await self._build_skill_tree(list(competencies.keys()))
                
                # Generate mastery path
                mastery_path = await self._generate_mastery_path(competencies, skill_tree)
                
                return CompetencyMap(
                    user_id=user_id,
                    competencies=competencies,
                    skill_tree=skill_tree,
                    mastery_path=mastery_path,
                    generated_at=datetime.now()
                )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error creating competency map: {str(e)}")
            return CompetencyMap(
                user_id=user_id,
                competencies={},
                skill_tree={},
                mastery_path=[],
                generated_at=datetime.now()
            )

    async def get_topic_progress(self, user_id: str, topic: str) -> Optional[LearningProgress]:
        """Get progress for a specific topic"""
        try:
            db = next(get_db())
            try:
                record = db.query(LearningProgressModel).filter(
                    LearningProgressModel.user_id == user_id,
                    LearningProgressModel.topic == topic
                ).first()
                
                if record:
                    return LearningProgress(
                        id=record.id,
                        user_id=record.user_id,
                        topic=record.topic,
                        competency_level=record.competency_level,
                        last_studied=record.last_studied,
                        study_count=record.study_count,
                        average_score=record.average_score,
                        trend="stable",  # Would calculate from history
                        confidence_interval=(record.competency_level * 0.9, record.competency_level * 1.1),
                        metadata=record.progress_metadata or {}
                    )
                return None
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting topic progress: {str(e)}")
            return None

    async def _store_learning_progress(self, progress: LearningProgress):
        """Store learning progress in database"""
        try:
            db = next(get_db())
            try:
                # Check if exists
                existing = db.query(LearningProgressModel).filter(
                    LearningProgressModel.user_id == progress.user_id,
                    LearningProgressModel.topic == progress.topic
                ).first()
                
                if existing:
                    # Update existing
                    existing.competency_level = progress.competency_level
                    existing.last_studied = progress.last_studied
                    existing.study_count = progress.study_count
                    existing.average_score = progress.average_score
                    existing.progress_metadata = progress.metadata
                else:
                    # Create new
                    new_progress = LearningProgressModel(
                        id=progress.id,
                        user_id=progress.user_id,
                        topic=progress.topic,
                        competency_level=progress.competency_level,
                        last_studied=progress.last_studied,
                        study_count=progress.study_count,
                        average_score=progress.average_score,
                        progress_metadata=progress.metadata
                    )
                    db.add(new_progress)
                
                db.commit()
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error storing learning progress: {str(e)}")
            raise

    async def _calculate_trend(self, user_id: str, topic: str) -> str:
        """Calculate learning trend for a topic"""
        try:
            # Get recent performance data
            trajectory = await self.get_learning_trajectory(user_id, topic)
            
            if len(trajectory.competency_scores) < 3:
                return "insufficient_data"
            
            # Calculate trend using linear regression slope
            recent_scores = trajectory.competency_scores[-5:]  # Last 5 data points
            x_values = list(range(len(recent_scores)))
            
            if len(recent_scores) >= 2:
                # Simple linear regression
                n = len(recent_scores)
                sum_x = sum(x_values)
                sum_y = sum(recent_scores)
                sum_xy = sum(x * y for x, y in zip(x_values, recent_scores))
                sum_x2 = sum(x * x for x in x_values)
                
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                
                if slope > 0.05:
                    return "improving"
                elif slope < -0.05:
                    return "declining"
                else:
                    return "stable"
            
            return "stable"
            
        except Exception as e:
            logger.error(f"Error calculating trend: {str(e)}")
            return "unknown"

    async def _calculate_confidence_interval(self, user_id: str, topic: str) -> Tuple[float, float]:
        """Calculate confidence interval for competency level"""
        try:
            trajectory = await self.get_learning_trajectory(user_id, topic)
            
            if len(trajectory.competency_scores) < 2:
                # Default confidence interval
                return (0.0, 1.0)
            
            scores = trajectory.competency_scores
            mean_score = statistics.mean(scores)
            
            if len(scores) >= 3:
                std_dev = statistics.stdev(scores)
                # 95% confidence interval (approximately)
                margin = 1.96 * std_dev / math.sqrt(len(scores))
                return (max(0.0, mean_score - margin), min(1.0, mean_score + margin))
            else:
                # Simple range for small samples
                return (max(0.0, mean_score - 0.2), min(1.0, mean_score + 0.2))
            
        except Exception as e:
            logger.error(f"Error calculating confidence interval: {str(e)}")
            return (0.0, 1.0)

    async def _calculate_overall_trend(self, user_id: str) -> str:
        """Calculate overall learning trend across all topics"""
        try:
            db = next(get_db())
            try:
                # Get recent study sessions
                recent_sessions = db.query(StudySessionModel).filter(
                    StudySessionModel.user_id == user_id,
                    StudySessionModel.started_at >= datetime.now() - timedelta(days=30)
                ).order_by(StudySessionModel.started_at).all()
                
                if len(recent_sessions) < 3:
                    return "insufficient_data"
                
                # Calculate trend in performance scores
                scores = [session.performance_score for session in recent_sessions if session.performance_score]
                
                if len(scores) >= 3:
                    # Simple trend calculation
                    first_half = scores[:len(scores)//2]
                    second_half = scores[len(scores)//2:]
                    
                    first_avg = sum(first_half) / len(first_half)
                    second_avg = sum(second_half) / len(second_half)
                    
                    if second_avg > first_avg + 0.1:
                        return "improving"
                    elif second_avg < first_avg - 0.1:
                        return "declining"
                    else:
                        return "stable"
                
                return "stable"
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error calculating overall trend: {str(e)}")
            return "unknown"

    async def _find_related_topics(self, topic: str) -> List[str]:
        """Find topics related to the given topic"""
        # Simplified implementation - would use NLP/knowledge graphs in practice
        related_topics = []
        
        # Basic keyword matching
        if "machine learning" in topic.lower():
            related_topics = ["artificial intelligence", "data science", "statistics", "algorithms"]
        elif "programming" in topic.lower():
            related_topics = ["algorithms", "data structures", "software engineering"]
        elif "mathematics" in topic.lower():
            related_topics = ["statistics", "calculus", "linear algebra"]
        
        return related_topics[:3]  # Return top 3

    async def _analyze_trajectory_trends(self, competency_scores: List[float]) -> Dict[str, Any]:
        """Analyze trends in learning trajectory"""
        if len(competency_scores) < 2:
            return {"trend": "insufficient_data"}
        
        try:
            # Calculate various trend metrics
            first_score = competency_scores[0]
            last_score = competency_scores[-1]
            max_score = max(competency_scores)
            min_score = min(competency_scores)
            
            # Overall improvement
            overall_improvement = last_score - first_score
            
            # Volatility (standard deviation)
            volatility = statistics.stdev(competency_scores) if len(competency_scores) > 1 else 0
            
            # Learning rate (improvement per session)
            learning_rate = overall_improvement / len(competency_scores) if len(competency_scores) > 0 else 0
            
            return {
                "trend": "improving" if overall_improvement > 0.1 else "declining" if overall_improvement < -0.1 else "stable",
                "overall_improvement": overall_improvement,
                "volatility": volatility,
                "learning_rate": learning_rate,
                "max_score": max_score,
                "min_score": min_score,
                "score_range": max_score - min_score
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trajectory trends: {str(e)}")
            return {"trend": "error"}

    async def _predict_future_performance(self, competency_scores: List[float], time_points: List[datetime]) -> Dict[str, Any]:
        """Predict future performance based on historical data"""
        if len(competency_scores) < 3:
            return {"prediction": "insufficient_data"}
        
        try:
            # Simple linear extrapolation
            recent_scores = competency_scores[-5:]  # Last 5 scores
            x_values = list(range(len(recent_scores)))
            
            # Calculate linear regression
            n = len(recent_scores)
            sum_x = sum(x_values)
            sum_y = sum(recent_scores)
            sum_xy = sum(x * y for x, y in zip(x_values, recent_scores))
            sum_x2 = sum(x * x for x in x_values)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n
            
            # Predict next few points
            future_predictions = []
            for i in range(1, 4):  # Next 3 sessions
                predicted_score = intercept + slope * (len(recent_scores) + i)
                future_predictions.append(max(0.0, min(1.0, predicted_score)))
            
            return {
                "prediction": "available",
                "slope": slope,
                "next_3_sessions": future_predictions,
                "confidence": "medium" if abs(slope) < 0.1 else "low"
            }
            
        except Exception as e:
            logger.error(f"Error predicting future performance: {str(e)}")
            return {"prediction": "error"}

    async def _build_skill_tree(self, topics: List[str]) -> Dict[str, List[str]]:
        """Build a skill tree showing topic dependencies"""
        # Simplified implementation - would use domain knowledge in practice
        skill_tree = {}
        
        for topic in topics:
            prerequisites = []
            
            # Basic rules for common topics
            if "advanced" in topic.lower():
                base_topic = topic.lower().replace("advanced ", "")
                if base_topic in topics:
                    prerequisites.append(base_topic)
            
            if "machine learning" in topic.lower():
                if "statistics" in topics:
                    prerequisites.append("statistics")
                if "programming" in topics:
                    prerequisites.append("programming")
            
            skill_tree[topic] = prerequisites
        
        return skill_tree

    async def _generate_mastery_path(self, competencies: Dict[str, float], skill_tree: Dict[str, List[str]]) -> List[str]:
        """Generate optimal mastery path based on competencies and dependencies"""
        # Sort topics by competency level and dependencies
        topics_with_scores = [(topic, score) for topic, score in competencies.items()]
        
        # Simple ordering: prerequisites first, then by competency level
        mastery_path = []
        remaining_topics = set(competencies.keys())
        
        while remaining_topics:
            # Find topics with satisfied prerequisites
            ready_topics = []
            for topic in remaining_topics:
                prerequisites = skill_tree.get(topic, [])
                if all(prereq in mastery_path or prereq not in remaining_topics for prereq in prerequisites):
                    ready_topics.append((topic, competencies[topic]))
            
            if not ready_topics:
                # Add remaining topics in competency order
                ready_topics = [(topic, competencies[topic]) for topic in remaining_topics]
            
            # Sort by competency (lowest first - need more work)
            ready_topics.sort(key=lambda x: x[1])
            
            # Add the topic with lowest competency
            next_topic = ready_topics[0][0]
            mastery_path.append(next_topic)
            remaining_topics.remove(next_topic)
        
        return mastery_path

    async def get_comprehensive_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive learning analytics with detailed performance metrics"""
        try:
            db = next(get_db())
            try:
                # Get all progress records
                progress_records = db.query(LearningProgressModel).filter(
                    LearningProgressModel.user_id == user_id
                ).all()
                
                # Get study sessions
                study_sessions = db.query(StudySessionModel).filter(
                    StudySessionModel.user_id == user_id
                ).order_by(StudySessionModel.started_at).all()
                
                # Get quiz attempts
                quiz_attempts = db.query(QuizAttemptModel).filter(
                    QuizAttemptModel.user_id == user_id
                ).order_by(QuizAttemptModel.started_at).all()
                
                # Calculate comprehensive metrics
                analytics = {
                    "overview": await self._calculate_overview_metrics(progress_records, study_sessions, quiz_attempts),
                    "performance_trends": await self._calculate_performance_trends(study_sessions, quiz_attempts),
                    "learning_velocity": await self._calculate_learning_velocity(progress_records, study_sessions),
                    "retention_analysis": await self._calculate_retention_analysis(progress_records, study_sessions),
                    "difficulty_progression": await self._calculate_difficulty_progression(quiz_attempts),
                    "time_investment": await self._calculate_time_investment_metrics(study_sessions),
                    "competency_distribution": await self._calculate_competency_distribution(progress_records),
                    "learning_patterns": await self._identify_learning_patterns(study_sessions, quiz_attempts),
                    "generated_at": datetime.now().isoformat()
                }
                
                return analytics
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting comprehensive analytics: {str(e)}")
            return {"error": str(e)}

    async def get_visual_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Get data formatted for visual progress dashboards"""
        try:
            # Get comprehensive analytics
            analytics = await self.get_comprehensive_analytics(user_id)
            
            # Get learning trajectories for top topics
            progress_overview = await self.get_user_progress_overview(user_id)
            top_topics = []
            if 'recent_activity' in progress_overview:
                top_topics = [activity['topic'] for activity in progress_overview['recent_activity'][:5]]
            
            trajectories = {}
            for topic in top_topics:
                trajectory = await self.get_learning_trajectory(user_id, topic)
                trajectories[topic] = {
                    "time_points": [tp.isoformat() for tp in trajectory.time_points],
                    "competency_scores": trajectory.competency_scores,
                    "trend_analysis": trajectory.trend_analysis
                }
            
            # Format dashboard data
            dashboard_data = {
                "summary_cards": {
                    "total_topics": analytics.get("overview", {}).get("total_topics", 0),
                    "average_competency": analytics.get("overview", {}).get("average_competency", 0),
                    "study_time_hours": analytics.get("overview", {}).get("total_study_time_minutes", 0) / 60,
                    "quizzes_completed": analytics.get("overview", {}).get("total_quizzes_taken", 0)
                },
                "competency_radar": {
                    "topics": list(trajectories.keys()),
                    "competency_levels": [max(traj["competency_scores"]) if traj["competency_scores"] else 0 
                                        for traj in trajectories.values()]
                },
                "learning_trajectory_chart": trajectories,
                "performance_trends": analytics.get("performance_trends", {}),
                "time_investment_chart": analytics.get("time_investment", {}),
                "competency_distribution": analytics.get("competency_distribution", {}),
                "knowledge_gaps_heatmap": await self._create_knowledge_gaps_heatmap(user_id),
                "learning_velocity_gauge": analytics.get("learning_velocity", {}),
                "retention_analysis": analytics.get("retention_analysis", {}),
                "generated_at": datetime.now().isoformat()
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting visual dashboard data: {str(e)}")
            return {"error": str(e)}

    async def _create_knowledge_gaps_heatmap(self, user_id: str) -> Dict[str, Any]:
        """Create heatmap data for knowledge gaps visualization"""
        try:
            gaps = await self.identify_knowledge_gaps(user_id)
            
            # Group gaps by topic and type
            heatmap_data = {}
            gap_types = ["weak_foundation", "declining_performance", "outdated_knowledge"]
            
            for gap in gaps:
                topic = gap.topic
                if topic not in heatmap_data:
                    heatmap_data[topic] = {gap_type: 0 for gap_type in gap_types}
                
                heatmap_data[topic][gap.gap_type] = gap.severity
            
            return {
                "topics": list(heatmap_data.keys()),
                "gap_types": gap_types,
                "severity_matrix": [[heatmap_data[topic][gap_type] for gap_type in gap_types] 
                                  for topic in heatmap_data.keys()],
                "max_severity": max(gap.severity for gap in gaps) if gaps else 0
            }
            
        except Exception as e:
            logger.error(f"Error creating knowledge gaps heatmap: {str(e)}")
            return {"topics": [], "gap_types": [], "severity_matrix": [], "max_severity": 0}

    async def _calculate_overview_metrics(self, progress_records, study_sessions, quiz_attempts) -> Dict[str, Any]:
        """Calculate overview metrics"""
        total_topics = len(progress_records)
        total_study_time = sum(session.duration_minutes or 0 for session in study_sessions)
        total_quizzes = len(quiz_attempts)
        
        if progress_records:
            avg_competency = sum(record.competency_level for record in progress_records) / len(progress_records)
            competency_std = statistics.stdev([record.competency_level for record in progress_records]) if len(progress_records) > 1 else 0
        else:
            avg_competency = 0
            competency_std = 0
        
        if quiz_attempts:
            quiz_scores = [attempt.score / attempt.total_points for attempt in quiz_attempts if attempt.total_points > 0]
            avg_quiz_score = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0
        else:
            avg_quiz_score = 0
        
        return {
            "total_topics": total_topics,
            "total_study_time_minutes": total_study_time,
            "total_quizzes_taken": total_quizzes,
            "average_competency": avg_competency,
            "competency_consistency": 1 - competency_std,  # Higher is more consistent
            "average_quiz_score": avg_quiz_score,
            "topics_mastered": len([r for r in progress_records if r.competency_level >= 0.8]),
            "topics_in_progress": len([r for r in progress_records if 0.3 <= r.competency_level < 0.8]),
            "topics_need_attention": len([r for r in progress_records if r.competency_level < 0.3])
        }

    async def _calculate_performance_trends(self, study_sessions, quiz_attempts) -> Dict[str, Any]:
        """Calculate performance trends over time"""
        # Combine study sessions and quiz attempts by time
        all_activities = []
        
        for session in study_sessions:
            if session.performance_score:
                all_activities.append({
                    "date": session.started_at,
                    "score": session.performance_score,
                    "type": "study"
                })
        
        for attempt in quiz_attempts:
            if attempt.total_points and attempt.total_points > 0:
                all_activities.append({
                    "date": attempt.started_at,
                    "score": attempt.score / attempt.total_points,
                    "type": "quiz"
                })
        
        # Sort by date
        all_activities.sort(key=lambda x: x["date"])
        
        if len(all_activities) < 3:
            return {"trend": "insufficient_data", "activities_count": len(all_activities)}
        
        # Calculate trends for different time periods
        recent_30_days = [a for a in all_activities if a["date"] >= datetime.now() - timedelta(days=30)]
        recent_7_days = [a for a in all_activities if a["date"] >= datetime.now() - timedelta(days=7)]
        
        trends = {}
        for period_name, activities in [("all_time", all_activities), ("30_days", recent_30_days), ("7_days", recent_7_days)]:
            if len(activities) >= 3:
                scores = [a["score"] for a in activities]
                trend_analysis = await self._analyze_trajectory_trends(scores)
                trends[period_name] = trend_analysis
        
        return trends

    async def _calculate_learning_velocity(self, progress_records, study_sessions) -> Dict[str, Any]:
        """Calculate learning velocity metrics"""
        if not progress_records or not study_sessions:
            return {"velocity": 0, "acceleration": 0}
        
        # Calculate competency gain per hour of study
        total_study_time = sum(session.duration_minutes or 0 for session in study_sessions) / 60  # Convert to hours
        total_competency_gain = sum(record.competency_level for record in progress_records)
        
        velocity = total_competency_gain / total_study_time if total_study_time > 0 else 0
        
        # Calculate acceleration (change in velocity over time)
        if len(study_sessions) >= 4:
            # Split sessions into first and second half
            mid_point = len(study_sessions) // 2
            first_half_sessions = study_sessions[:mid_point]
            second_half_sessions = study_sessions[mid_point:]
            
            first_half_time = sum(session.duration_minutes or 0 for session in first_half_sessions) / 60
            second_half_time = sum(session.duration_minutes or 0 for session in second_half_sessions) / 60
            
            # Estimate competency gain for each half (simplified)
            first_half_gain = len(first_half_sessions) * 0.1  # Rough estimate
            second_half_gain = len(second_half_sessions) * 0.1
            
            first_velocity = first_half_gain / first_half_time if first_half_time > 0 else 0
            second_velocity = second_half_gain / second_half_time if second_half_time > 0 else 0
            
            acceleration = second_velocity - first_velocity
        else:
            acceleration = 0
        
        return {
            "velocity": velocity,  # Competency points per hour
            "acceleration": acceleration,  # Change in velocity
            "efficiency_rating": "high" if velocity > 0.5 else "medium" if velocity > 0.2 else "low"
        }

    async def _calculate_retention_analysis(self, progress_records, study_sessions) -> Dict[str, Any]:
        """Analyze knowledge retention patterns"""
        retention_data = {}
        
        for record in progress_records:
            topic = record.topic
            
            # Find study sessions for this topic
            topic_sessions = [s for s in study_sessions 
                            if s.session_metadata and s.session_metadata.get('topic') == topic]
            
            if len(topic_sessions) >= 2:
                # Calculate retention based on performance over time
                sessions_by_time = sorted(topic_sessions, key=lambda x: x.started_at)
                
                # Look for patterns of forgetting and relearning
                scores = [s.performance_score for s in sessions_by_time if s.performance_score]
                
                if len(scores) >= 3:
                    # Calculate retention curve
                    retention_curve = []
                    for i in range(1, len(scores)):
                        time_gap = (sessions_by_time[i].started_at - sessions_by_time[i-1].started_at).days
                        score_change = scores[i] - scores[i-1]
                        retention_curve.append({
                            "time_gap_days": time_gap,
                            "score_change": score_change,
                            "retention_rate": max(0, 1 + score_change)  # Simplified retention rate
                        })
                    
                    avg_retention = sum(r["retention_rate"] for r in retention_curve) / len(retention_curve)
                    
                    retention_data[topic] = {
                        "average_retention_rate": avg_retention,
                        "retention_curve": retention_curve,
                        "forgetting_incidents": len([r for r in retention_curve if r["score_change"] < -0.1]),
                        "improvement_incidents": len([r for r in retention_curve if r["score_change"] > 0.1])
                    }
        
        # Calculate overall retention metrics
        if retention_data:
            overall_retention = sum(data["average_retention_rate"] for data in retention_data.values()) / len(retention_data)
            total_forgetting = sum(data["forgetting_incidents"] for data in retention_data.values())
            total_improvements = sum(data["improvement_incidents"] for data in retention_data.values())
        else:
            overall_retention = 0
            total_forgetting = 0
            total_improvements = 0
        
        return {
            "overall_retention_rate": overall_retention,
            "total_forgetting_incidents": total_forgetting,
            "total_improvement_incidents": total_improvements,
            "topic_retention": retention_data,
            "retention_quality": "excellent" if overall_retention > 0.8 else "good" if overall_retention > 0.6 else "needs_improvement"
        }

    async def _calculate_difficulty_progression(self, quiz_attempts) -> Dict[str, Any]:
        """Analyze difficulty progression in quizzes"""
        if not quiz_attempts:
            return {"progression": "no_data"}
        
        # Sort by date
        attempts_by_time = sorted(quiz_attempts, key=lambda x: x.started_at)
        
        # Analyze difficulty trends (simplified - would need actual difficulty ratings)
        difficulty_progression = []
        performance_by_difficulty = {}
        
        for attempt in attempts_by_time:
            # Estimate difficulty based on score (inverse relationship)
            estimated_difficulty = 1 - (attempt.score / attempt.total_points) if attempt.total_points > 0 else 0.5
            performance = attempt.score / attempt.total_points if attempt.total_points > 0 else 0
            
            difficulty_progression.append({
                "date": attempt.started_at,
                "estimated_difficulty": estimated_difficulty,
                "performance": performance
            })
            
            # Group by difficulty ranges
            difficulty_range = "easy" if estimated_difficulty < 0.3 else "medium" if estimated_difficulty < 0.7 else "hard"
            if difficulty_range not in performance_by_difficulty:
                performance_by_difficulty[difficulty_range] = []
            performance_by_difficulty[difficulty_range].append(performance)
        
        # Calculate average performance by difficulty
        avg_performance_by_difficulty = {}
        for difficulty, performances in performance_by_difficulty.items():
            avg_performance_by_difficulty[difficulty] = sum(performances) / len(performances)
        
        return {
            "difficulty_progression": difficulty_progression[-10:],  # Last 10 attempts
            "performance_by_difficulty": avg_performance_by_difficulty,
            "adaptive_readiness": "ready_for_harder" if avg_performance_by_difficulty.get("medium", 0) > 0.8 else "maintain_current"
        }

    async def _calculate_time_investment_metrics(self, study_sessions) -> Dict[str, Any]:
        """Calculate time investment and efficiency metrics"""
        if not study_sessions:
            return {
                "total_time_minutes": 0,
                "total_sessions": 0,
                "average_session_length": 0,
                "time_patterns": {
                    "by_day_of_week": {},
                    "by_hour": {},
                    "session_length_distribution": {}
                },
                "efficiency_score": 0,
                "optimal_session_length": "short",
                "consistency_score": 0
            }
        
        # Calculate session durations from start and end times
        session_durations = []
        for session in study_sessions:
            if session.ended_at and session.started_at:
                duration_minutes = (session.ended_at - session.started_at).total_seconds() / 60
                session_durations.append(duration_minutes)
            else:
                # Default duration if end time is missing (assume 30 minutes)
                session_durations.append(30)
        
        total_time = sum(session_durations)
        avg_session_length = total_time / len(study_sessions) if study_sessions else 0
        
        # Analyze time distribution by day of week and hour
        time_patterns = {
            "by_day_of_week": {},
            "by_hour": {},
            "session_length_distribution": {}
        }
        
        for i, session in enumerate(study_sessions):
            duration = session_durations[i]
            
            # Day of week analysis
            day_of_week = session.started_at.strftime("%A")
            if day_of_week not in time_patterns["by_day_of_week"]:
                time_patterns["by_day_of_week"][day_of_week] = 0
            time_patterns["by_day_of_week"][day_of_week] += duration
            
            # Hour analysis
            hour = session.started_at.hour
            if hour not in time_patterns["by_hour"]:
                time_patterns["by_hour"][hour] = 0
            time_patterns["by_hour"][hour] += duration
            
            # Session length distribution
            length_category = "short" if duration < 15 else "medium" if duration < 45 else "long"
            if length_category not in time_patterns["session_length_distribution"]:
                time_patterns["session_length_distribution"][length_category] = 0
            time_patterns["session_length_distribution"][length_category] += 1
        
        # Calculate efficiency (performance per minute)
        sessions_with_performance = []
        for i, session in enumerate(study_sessions):
            if session.performance_score and session_durations[i] > 0:
                sessions_with_performance.append((session.performance_score, session_durations[i]))
        
        if sessions_with_performance:
            efficiency_scores = [score / duration for score, duration in sessions_with_performance]
            avg_efficiency = sum(efficiency_scores) / len(efficiency_scores)
        else:
            avg_efficiency = 0
        
        # Calculate consistency score (sessions per day over time period)
        if len(study_sessions) > 1:
            date_range = (max(s.started_at for s in study_sessions) - min(s.started_at for s in study_sessions)).days
            unique_days = len(set(s.started_at.date() for s in study_sessions))
            consistency_score = unique_days / max(1, date_range) if date_range > 0 else 1
        else:
            consistency_score = 1 if study_sessions else 0
        
        return {
            "total_time_minutes": total_time,
            "total_sessions": len(study_sessions),
            "average_session_length": avg_session_length,
            "time_patterns": time_patterns,
            "efficiency_score": avg_efficiency,
            "optimal_session_length": "medium" if avg_session_length > 30 else "short",
            "consistency_score": consistency_score
        }

    async def _calculate_competency_distribution(self, progress_records) -> Dict[str, Any]:
        """Calculate competency distribution across topics"""
        if not progress_records:
            return {"distribution": {}, "balance_score": 0}
        
        competencies = [record.competency_level for record in progress_records]
        
        # Calculate distribution statistics
        distribution = {
            "mean": statistics.mean(competencies),
            "median": statistics.median(competencies),
            "std_dev": statistics.stdev(competencies) if len(competencies) > 1 else 0,
            "min": min(competencies),
            "max": max(competencies),
            "range": max(competencies) - min(competencies)
        }
        
        # Calculate balance score (lower std dev = more balanced)
        balance_score = max(0, 1 - distribution["std_dev"])
        
        # Categorize topics by competency level
        competency_categories = {
            "expert": [r.topic for r in progress_records if r.competency_level >= 0.8],
            "advanced": [r.topic for r in progress_records if 0.6 <= r.competency_level < 0.8],
            "intermediate": [r.topic for r in progress_records if 0.4 <= r.competency_level < 0.6],
            "beginner": [r.topic for r in progress_records if 0.2 <= r.competency_level < 0.4],
            "novice": [r.topic for r in progress_records if r.competency_level < 0.2]
        }
        
        return {
            "distribution": distribution,
            "balance_score": balance_score,
            "competency_categories": competency_categories,
            "development_focus": "breadth" if balance_score > 0.7 else "depth",
            "strength_areas": competency_categories["expert"] + competency_categories["advanced"],
            "growth_areas": competency_categories["novice"] + competency_categories["beginner"]
        }

    async def _identify_learning_patterns(self, study_sessions, quiz_attempts) -> Dict[str, Any]:
        """Identify learning patterns and preferences"""
        patterns = {
            "study_frequency": {},
            "performance_patterns": {},
            "learning_style_indicators": {}
        }
        
        if study_sessions:
            # Analyze study frequency patterns
            session_dates = [s.started_at.date() for s in study_sessions]
            date_counts = {}
            for date in session_dates:
                date_counts[date] = date_counts.get(date, 0) + 1
            
            # Calculate study frequency metrics
            days_with_study = len(date_counts)
            total_days = (max(session_dates) - min(session_dates)).days + 1 if session_dates else 1
            study_frequency = days_with_study / total_days
            
            patterns["study_frequency"] = {
                "frequency_rate": study_frequency,
                "average_sessions_per_day": sum(date_counts.values()) / len(date_counts) if date_counts else 0,
                "most_active_days": sorted(date_counts.items(), key=lambda x: x[1], reverse=True)[:3],
                "consistency": "high" if study_frequency > 0.7 else "medium" if study_frequency > 0.4 else "low"
            }
        
        # Analyze performance patterns
        if quiz_attempts:
            # Performance by time of day
            performance_by_hour = {}
            for attempt in quiz_attempts:
                hour = attempt.started_at.hour
                performance = attempt.score / attempt.total_points if attempt.total_points > 0 else 0
                if hour not in performance_by_hour:
                    performance_by_hour[hour] = []
                performance_by_hour[hour].append(performance)
            
            # Calculate average performance by hour
            avg_performance_by_hour = {
                hour: sum(performances) / len(performances)
                for hour, performances in performance_by_hour.items()
            }
            
            patterns["performance_patterns"] = {
                "performance_by_hour": avg_performance_by_hour,
                "peak_performance_hours": sorted(avg_performance_by_hour.items(), key=lambda x: x[1], reverse=True)[:3],
                "performance_consistency": 1 - statistics.stdev(list(avg_performance_by_hour.values())) if len(avg_performance_by_hour) > 1 else 1
            }
        
        # Learning style indicators (simplified)
        if study_sessions and quiz_attempts:
            study_to_quiz_ratio = len(study_sessions) / len(quiz_attempts)
            
            patterns["learning_style_indicators"] = {
                "study_to_assessment_ratio": study_to_quiz_ratio,
                "learning_style": "thorough_studier" if study_to_quiz_ratio > 3 else "assessment_focused" if study_to_quiz_ratio < 1 else "balanced",
                "preferred_session_length": "long" if sum(s.duration_minutes or 0 for s in study_sessions) / len(study_sessions) > 45 else "short"
            }
        
        return patterns