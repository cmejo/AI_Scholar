"""
Enhanced Personalization Engine
Provides adaptive user interfaces, smart content recommendations,
personalized research workflows, and learning style adaptation.
"""
import asyncio
import logging
import json
import uuid
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, Counter
import pickle

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, or_

from core.database import (
    get_db, Document, DocumentChunk, DocumentTag, AnalyticsEvent,
    User, UserProfile
)

logger = logging.getLogger(__name__)

class LearningStyle(str, Enum):
    """Learning style types"""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"
    MULTIMODAL = "multimodal"

class PersonalityType(str, Enum):
    """Research personality types"""
    EXPLORER = "explorer"  # Likes to discover new topics
    ANALYZER = "analyzer"  # Prefers deep analysis
    SYNTHESIZER = "synthesizer"  # Combines information
    COLLABORATOR = "collaborator"  # Works well with others
    METHODICAL = "methodical"  # Follows structured approaches

class ContentPreference(str, Enum):
    """Content preference types"""
    ACADEMIC_PAPERS = "academic_papers"
    VISUAL_CONTENT = "visual_content"
    AUDIO_CONTENT = "audio_content"
    INTERACTIVE_CONTENT = "interactive_content"
    STRUCTURED_DATA = "structured_data"
    COLLABORATIVE_CONTENT = "collaborative_content"

@dataclass
class UserPersonalizationProfile:
    """Comprehensive user personalization profile"""
    user_id: str
    learning_style: LearningStyle
    personality_type: PersonalityType
    content_preferences: List[ContentPreference]
    research_domains: List[str]
    skill_levels: Dict[str, float]  # domain -> skill level (0-1)
    interaction_patterns: Dict[str, Any]
    ui_preferences: Dict[str, Any]
    workflow_preferences: Dict[str, Any]
    recommendation_history: List[Dict[str, Any]]
    adaptation_score: float
    last_updated: datetime
    confidence_score: float

@dataclass
class PersonalizedRecommendation:
    """Personalized content recommendation"""
    id: str
    user_id: str
    recommendation_type: str
    title: str
    description: str
    content_id: str
    relevance_score: float
    personalization_score: float
    reasoning: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    interacted: bool = False

class PersonalizationEngine:
    """Main personalization engine"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # User profiles
        self.user_profiles: Dict[str, UserPersonalizationProfile] = {}
        
        # Recommendation models
        self.content_vectors: Dict[str, np.ndarray] = {}
        self.user_vectors: Dict[str, np.ndarray] = {}
        
        # Adaptation rules
        self.adaptation_rules = {
            LearningStyle.VISUAL: {
                "ui_preferences": {"chart_emphasis": True, "visual_summaries": True},
                "content_weights": {"images": 1.5, "charts": 1.3, "videos": 1.2}
            },
            LearningStyle.AUDITORY: {
                "ui_preferences": {"audio_feedback": True, "voice_interface": True},
                "content_weights": {"audio": 1.5, "podcasts": 1.3, "discussions": 1.2}
            },
            LearningStyle.READING_WRITING: {
                "ui_preferences": {"text_emphasis": True, "note_taking": True},
                "content_weights": {"text": 1.3, "documents": 1.2, "articles": 1.4}
            }
        }

    async def build_user_profile(self, user_id: str) -> UserPersonalizationProfile:
        """Build comprehensive personalization profile for user"""
        try:
            logger.info(f"Building personalization profile for user {user_id}")
            
            # Analyze user behavior
            interaction_patterns = await self._analyze_interaction_patterns(user_id)
            
            # Determine learning style
            learning_style = await self._determine_learning_style(user_id, interaction_patterns)
            
            # Identify personality type
            personality_type = await self._identify_personality_type(user_id, interaction_patterns)
            
            # Extract content preferences
            content_preferences = await self._extract_content_preferences(user_id)
            
            # Identify research domains
            research_domains = await self._identify_research_domains(user_id)
            
            # Calculate skill levels
            skill_levels = await self._calculate_skill_levels(user_id, research_domains)
            
            # Generate UI preferences
            ui_preferences = await self._generate_ui_preferences(learning_style, personality_type)
            
            # Create workflow preferences
            workflow_preferences = await self._create_workflow_preferences(
                personality_type, skill_levels
            )
            
            # Calculate adaptation score
            adaptation_score = await self._calculate_adaptation_score(user_id)
            
            profile = UserPersonalizationProfile(
                user_id=user_id,
                learning_style=learning_style,
                personality_type=personality_type,
                content_preferences=content_preferences,
                research_domains=research_domains,
                skill_levels=skill_levels,
                interaction_patterns=interaction_patterns,
                ui_preferences=ui_preferences,
                workflow_preferences=workflow_preferences,
                recommendation_history=[],
                adaptation_score=adaptation_score,
                last_updated=datetime.utcnow(),
                confidence_score=0.8
            )
            
            # Store profile
            self.user_profiles[user_id] = profile
            
            return profile
            
        except Exception as e:
            logger.error(f"Error building user profile: {str(e)}")
            raise

    async def generate_personalized_recommendations(
        self,
        user_id: str,
        context: str = "general",
        limit: int = 10
    ) -> List[PersonalizedRecommendation]:
        """Generate personalized content recommendations"""
        try:
            profile = self.user_profiles.get(user_id)
            if not profile:
                profile = await self.build_user_profile(user_id)
            
            recommendations = []
            
            # Content-based recommendations
            content_recs = await self._generate_content_based_recommendations(
                profile, context, limit // 2
            )
            recommendations.extend(content_recs)
            
            # Collaborative filtering recommendations
            collab_recs = await self._generate_collaborative_recommendations(
                profile, context, limit // 2
            )
            recommendations.extend(collab_recs)
            
            # Rank by personalization score
            recommendations.sort(key=lambda x: x.personalization_score, reverse=True)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            raise

    async def adapt_user_interface(
        self,
        user_id: str,
        current_context: str = "dashboard"
    ) -> Dict[str, Any]:
        """Adapt user interface based on personalization profile"""
        try:
            profile = self.user_profiles.get(user_id)
            if not profile:
                profile = await self.build_user_profile(user_id)
            
            # Base UI configuration
            ui_config = {
                "layout": "default",
                "theme": "light",
                "navigation": "sidebar",
                "content_density": "medium",
                "interaction_style": "click"
            }
            
            # Apply learning style adaptations
            learning_adaptations = self.adaptation_rules.get(profile.learning_style, {})
            ui_config.update(learning_adaptations.get("ui_preferences", {}))
            
            # Apply personality type adaptations
            personality_adaptations = await self._get_personality_ui_adaptations(
                profile.personality_type
            )
            ui_config.update(personality_adaptations)
            
            # Apply context-specific adaptations
            context_adaptations = await self._get_context_ui_adaptations(
                current_context, profile
            )
            ui_config.update(context_adaptations)
            
            # Apply user-specific preferences
            ui_config.update(profile.ui_preferences)
            
            return ui_config
            
        except Exception as e:
            logger.error(f"Error adapting user interface: {str(e)}")
            return {"layout": "default"}

    async def create_personalized_workflow(
        self,
        user_id: str,
        workflow_type: str,
        base_workflow: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create personalized research workflow"""
        try:
            profile = self.user_profiles.get(user_id)
            if not profile:
                profile = await self.build_user_profile(user_id)
            
            # Start with base workflow
            personalized_workflow = base_workflow.copy()
            
            # Apply personality-based modifications
            personality_mods = await self._get_personality_workflow_modifications(
                profile.personality_type, workflow_type
            )
            personalized_workflow.update(personality_mods)
            
            # Apply skill-level modifications
            skill_mods = await self._get_skill_based_modifications(
                profile.skill_levels, workflow_type
            )
            personalized_workflow.update(skill_mods)
            
            # Apply learning style modifications
            learning_mods = await self._get_learning_style_modifications(
                profile.learning_style, workflow_type
            )
            personalized_workflow.update(learning_mods)
            
            # Add personalization metadata
            personalized_workflow["personalization"] = {
                "adapted_for": user_id,
                "learning_style": profile.learning_style.value,
                "personality_type": profile.personality_type.value,
                "adaptation_score": profile.adaptation_score,
                "created_at": datetime.utcnow().isoformat()
            }
            
            return personalized_workflow
            
        except Exception as e:
            logger.error(f"Error creating personalized workflow: {str(e)}")
            return base_workflow

    # Analysis methods
    async def _analyze_interaction_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze user interaction patterns"""
        try:
            # Get user's analytics events
            events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.user_id == user_id
            ).order_by(desc(AnalyticsEvent.created_at)).limit(1000).all()
            
            patterns = {
                "total_interactions": len(events),
                "event_types": {},
                "time_patterns": {},
                "session_patterns": {},
                "content_interactions": {},
                "feature_usage": {}
            }
            
            if not events:
                return patterns
            
            # Analyze event types
            event_types = Counter([event.event_type for event in events])
            patterns["event_types"] = dict(event_types)
            
            # Analyze time patterns
            hours = [event.created_at.hour for event in events]
            patterns["time_patterns"] = {
                "peak_hours": Counter(hours).most_common(3),
                "average_hour": sum(hours) / len(hours)
            }
            
            # Analyze content interactions
            content_events = [e for e in events if "document" in e.event_type]
            patterns["content_interactions"] = {
                "document_events": len(content_events),
                "avg_per_day": len(content_events) / max(1, (datetime.utcnow() - events[-1].created_at).days)
            }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing interaction patterns: {str(e)}")
            return {"total_interactions": 0}

    async def _determine_learning_style(
        self, user_id: str, interaction_patterns: Dict[str, Any]
    ) -> LearningStyle:
        """Determine user's learning style"""
        try:
            # Analyze interaction patterns for learning style indicators
            event_types = interaction_patterns.get("event_types", {})
            
            # Visual indicators
            visual_score = (
                event_types.get("chart_viewed", 0) * 2 +
                event_types.get("image_processed", 0) * 1.5 +
                event_types.get("visualization_created", 0) * 2
            )
            
            # Auditory indicators
            auditory_score = (
                event_types.get("audio_processed", 0) * 2 +
                event_types.get("voice_command", 0) * 1.5
            )
            
            # Reading/Writing indicators
            text_score = (
                event_types.get("document_processed", 0) * 1.5 +
                event_types.get("text_analyzed", 0) * 1.2 +
                event_types.get("note_created", 0) * 2
            )
            
            # Determine dominant style
            scores = {
                LearningStyle.VISUAL: visual_score,
                LearningStyle.AUDITORY: auditory_score,
                LearningStyle.READING_WRITING: text_score
            }
            
            if max(scores.values()) == 0:
                return LearningStyle.MULTIMODAL
            
            return max(scores.items(), key=lambda x: x[1])[0]
            
        except Exception as e:
            logger.error(f"Error determining learning style: {str(e)}")
            return LearningStyle.MULTIMODAL

    async def _identify_personality_type(
        self, user_id: str, interaction_patterns: Dict[str, Any]
    ) -> PersonalityType:
        """Identify user's research personality type"""
        try:
            event_types = interaction_patterns.get("event_types", {})
            
            # Explorer indicators
            explorer_score = (
                event_types.get("search_performed", 0) * 1.5 +
                event_types.get("topic_explored", 0) * 2 +
                event_types.get("cross_domain_search", 0) * 2
            )
            
            # Analyzer indicators
            analyzer_score = (
                event_types.get("deep_analysis", 0) * 2 +
                event_types.get("detailed_view", 0) * 1.5 +
                event_types.get("analytics_viewed", 0) * 1.3
            )
            
            # Collaborator indicators
            collaborator_score = (
                event_types.get("collaboration_joined", 0) * 2 +
                event_types.get("shared_content", 0) * 1.5 +
                event_types.get("comment_added", 0) * 1.2
            )
            
            scores = {
                PersonalityType.EXPLORER: explorer_score,
                PersonalityType.ANALYZER: analyzer_score,
                PersonalityType.COLLABORATOR: collaborator_score
            }
            
            if max(scores.values()) == 0:
                return PersonalityType.METHODICAL
            
            return max(scores.items(), key=lambda x: x[1])[0]
            
        except Exception as e:
            logger.error(f"Error identifying personality type: {str(e)}")
            return PersonalityType.METHODICAL

    async def _extract_content_preferences(self, user_id: str) -> List[ContentPreference]:
        """Extract user's content preferences"""
        try:
            # Get user's documents
            documents = self.db.query(Document).filter(
                Document.user_id == user_id
            ).all()
            
            content_types = Counter([doc.content_type for doc in documents])
            preferences = []
            
            # Map content types to preferences
            if content_types.get("image", 0) > 5:
                preferences.append(ContentPreference.VISUAL_CONTENT)
            
            if content_types.get("audio", 0) > 3:
                preferences.append(ContentPreference.AUDIO_CONTENT)
            
            if content_types.get("application/pdf", 0) > 10:
                preferences.append(ContentPreference.ACADEMIC_PAPERS)
            
            if not preferences:
                preferences.append(ContentPreference.ACADEMIC_PAPERS)
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error extracting content preferences: {str(e)}")
            return [ContentPreference.ACADEMIC_PAPERS]

    async def _identify_research_domains(self, user_id: str) -> List[str]:
        """Identify user's research domains"""
        try:
            # Get document tags
            tags = self.db.query(DocumentTag).join(Document).filter(
                Document.user_id == user_id
            ).all()
            
            tag_counts = Counter([tag.tag_name.lower() for tag in tags])
            
            # Map tags to domains
            domain_mapping = {
                "machine learning": "computer_science",
                "ai": "computer_science",
                "health": "medicine",
                "psychology": "psychology",
                "education": "education",
                "business": "business"
            }
            
            domains = []
            for tag, count in tag_counts.most_common(5):
                domain = domain_mapping.get(tag, tag)
                if domain not in domains:
                    domains.append(domain)
            
            return domains[:3] if domains else ["general"]
            
        except Exception as e:
            logger.error(f"Error identifying research domains: {str(e)}")
            return ["general"]

    async def _calculate_skill_levels(
        self, user_id: str, domains: List[str]
    ) -> Dict[str, float]:
        """Calculate skill levels for different domains"""
        try:
            skill_levels = {}
            
            for domain in domains:
                # Simple heuristic based on document count and interaction frequency
                doc_count = self.db.query(Document).filter(
                    Document.user_id == user_id
                ).count()
                
                # Base skill level on activity
                if doc_count > 50:
                    skill_level = 0.8
                elif doc_count > 20:
                    skill_level = 0.6
                elif doc_count > 5:
                    skill_level = 0.4
                else:
                    skill_level = 0.2
                
                skill_levels[domain] = skill_level
            
            return skill_levels
            
        except Exception as e:
            logger.error(f"Error calculating skill levels: {str(e)}")
            return {"general": 0.5}

    # UI and workflow adaptation methods
    async def _generate_ui_preferences(
        self, learning_style: LearningStyle, personality_type: PersonalityType
    ) -> Dict[str, Any]:
        """Generate UI preferences based on learning style and personality"""
        preferences = {
            "theme": "light",
            "layout": "standard",
            "navigation": "sidebar"
        }
        
        # Learning style adaptations
        if learning_style == LearningStyle.VISUAL:
            preferences.update({
                "chart_emphasis": True,
                "visual_summaries": True,
                "color_coding": True
            })
        elif learning_style == LearningStyle.READING_WRITING:
            preferences.update({
                "text_emphasis": True,
                "detailed_descriptions": True,
                "note_taking_tools": True
            })
        
        # Personality adaptations
        if personality_type == PersonalityType.EXPLORER:
            preferences.update({
                "quick_access_search": True,
                "discovery_widgets": True
            })
        elif personality_type == PersonalityType.ANALYZER:
            preferences.update({
                "detailed_analytics": True,
                "advanced_filters": True
            })
        
        return preferences

    async def _get_personality_ui_adaptations(
        self, personality_type: PersonalityType
    ) -> Dict[str, Any]:
        """Get UI adaptations for personality type"""
        adaptations = {
            PersonalityType.EXPLORER: {
                "dashboard_layout": "discovery_focused",
                "search_prominence": "high",
                "recommendation_panel": True
            },
            PersonalityType.ANALYZER: {
                "dashboard_layout": "analytics_focused",
                "detail_level": "high",
                "chart_complexity": "advanced"
            },
            PersonalityType.COLLABORATOR: {
                "social_features": True,
                "sharing_tools": "prominent",
                "activity_feed": True
            },
            PersonalityType.METHODICAL: {
                "step_by_step_guides": True,
                "progress_tracking": True,
                "structured_layout": True
            }
        }
        
        return adaptations.get(personality_type, {})

    async def _calculate_adaptation_score(self, user_id: str) -> float:
        """Calculate how well the system has adapted to the user"""
        try:
            # Get recent user interactions
            recent_events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.created_at >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            if not recent_events:
                return 0.5
            
            # Calculate engagement metrics
            positive_events = [
                "document_processed", "search_performed", "content_viewed",
                "recommendation_clicked", "workflow_completed"
            ]
            
            positive_count = len([e for e in recent_events if e.event_type in positive_events])
            total_count = len(recent_events)
            
            engagement_score = positive_count / total_count if total_count > 0 else 0.5
            
            # Factor in user retention
            days_active = len(set(e.created_at.date() for e in recent_events))
            retention_score = min(1.0, days_active / 30)
            
            # Combined adaptation score
            adaptation_score = (engagement_score * 0.7 + retention_score * 0.3)
            
            return min(1.0, max(0.0, adaptation_score))
            
        except Exception as e:
            logger.error(f"Error calculating adaptation score: {str(e)}")
            return 0.5

    # Missing recommendation methods
    async def _generate_content_based_recommendations(
        self, profile: UserPersonalizationProfile, context: str, limit: int
    ) -> List[PersonalizedRecommendation]:
        """Generate content-based recommendations"""
        try:
            recommendations = []
            
            # Get user's documents for content analysis
            user_docs = self.db.query(Document).filter(
                Document.user_id == profile.user_id
            ).limit(50).all()
            
            if not user_docs:
                return recommendations
            
            # Simple content-based recommendation
            for i, doc in enumerate(user_docs[:limit]):
                if i >= limit:
                    break
                    
                recommendation = PersonalizedRecommendation(
                    id=str(uuid.uuid4()),
                    user_id=profile.user_id,
                    recommendation_type="content_based",
                    title=f"Similar to: {doc.title[:50]}...",
                    description=f"Based on your interest in {doc.title}",
                    content_id=str(doc.id),
                    relevance_score=0.8 - (i * 0.1),
                    personalization_score=0.7 + (profile.adaptation_score * 0.3),
                    reasoning=[
                        f"Matches your {profile.learning_style.value} learning style",
                        f"Aligns with your {profile.personality_type.value} research approach"
                    ],
                    metadata={"source": "content_analysis", "context": context},
                    created_at=datetime.utcnow()
                )
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating content-based recommendations: {str(e)}")
            return []

    async def _generate_collaborative_recommendations(
        self, profile: UserPersonalizationProfile, context: str, limit: int
    ) -> List[PersonalizedRecommendation]:
        """Generate collaborative filtering recommendations"""
        try:
            recommendations = []
            
            # Find similar users (simplified)
            similar_users = self.db.query(User).filter(
                User.id != profile.user_id
            ).limit(10).all()
            
            for i, user in enumerate(similar_users[:limit]):
                if i >= limit:
                    break
                    
                recommendation = PersonalizedRecommendation(
                    id=str(uuid.uuid4()),
                    user_id=profile.user_id,
                    recommendation_type="collaborative",
                    title=f"Popular with similar researchers",
                    description=f"Users with similar interests also liked this",
                    content_id=f"collab_{user.id}",
                    relevance_score=0.6 - (i * 0.05),
                    personalization_score=0.5 + (profile.adaptation_score * 0.2),
                    reasoning=[
                        "Based on similar user preferences",
                        f"Matches your research domains: {', '.join(profile.research_domains[:2])}"
                    ],
                    metadata={"source": "collaborative_filtering", "context": context},
                    created_at=datetime.utcnow()
                )
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating collaborative recommendations: {str(e)}")
            return []

    async def _create_workflow_preferences(
        self, personality_type: PersonalityType, skill_levels: Dict[str, float]
    ) -> Dict[str, Any]:
        """Create workflow preferences based on personality and skills"""
        preferences = {
            "default_workflow": "standard",
            "automation_level": "medium",
            "guidance_level": "medium"
        }
        
        # Personality-based preferences
        if personality_type == PersonalityType.EXPLORER:
            preferences.update({
                "default_workflow": "discovery_focused",
                "automation_level": "low",  # Explorers like control
                "guidance_level": "low"
            })
        elif personality_type == PersonalityType.ANALYZER:
            preferences.update({
                "default_workflow": "analysis_focused",
                "automation_level": "medium",
                "guidance_level": "high"
            })
        elif personality_type == PersonalityType.METHODICAL:
            preferences.update({
                "default_workflow": "step_by_step",
                "automation_level": "high",
                "guidance_level": "high"
            })
        
        # Skill-based adjustments
        avg_skill = sum(skill_levels.values()) / len(skill_levels) if skill_levels else 0.5
        if avg_skill > 0.7:
            preferences["guidance_level"] = "low"
            preferences["automation_level"] = "high"
        elif avg_skill < 0.3:
            preferences["guidance_level"] = "high"
            preferences["automation_level"] = "low"
        
        return preferences

    async def _get_context_ui_adaptations(
        self, context: str, profile: UserPersonalizationProfile
    ) -> Dict[str, Any]:
        """Get context-specific UI adaptations"""
        adaptations = {}
        
        if context == "research":
            adaptations.update({
                "focus_mode": True,
                "distraction_free": True,
                "research_tools": "prominent"
            })
        elif context == "analysis":
            adaptations.update({
                "analytics_panel": True,
                "chart_tools": "prominent",
                "data_views": "expanded"
            })
        elif context == "collaboration":
            adaptations.update({
                "social_panel": True,
                "sharing_tools": "prominent",
                "communication_tools": True
            })
        
        return adaptations

    async def _get_personality_workflow_modifications(
        self, personality_type: PersonalityType, workflow_type: str
    ) -> Dict[str, Any]:
        """Get personality-based workflow modifications"""
        modifications = {}
        
        if personality_type == PersonalityType.EXPLORER:
            modifications.update({
                "discovery_phase": "extended",
                "exploration_tools": True,
                "serendipity_factor": "high"
            })
        elif personality_type == PersonalityType.ANALYZER:
            modifications.update({
                "analysis_depth": "deep",
                "validation_steps": "thorough",
                "detail_level": "high"
            })
        elif personality_type == PersonalityType.COLLABORATOR:
            modifications.update({
                "collaboration_checkpoints": True,
                "sharing_prompts": True,
                "peer_review_steps": True
            })
        
        return modifications

    async def _get_skill_based_modifications(
        self, skill_levels: Dict[str, float], workflow_type: str
    ) -> Dict[str, Any]:
        """Get skill-based workflow modifications"""
        modifications = {}
        
        avg_skill = sum(skill_levels.values()) / len(skill_levels) if skill_levels else 0.5
        
        if avg_skill > 0.7:  # Advanced user
            modifications.update({
                "guidance_level": "minimal",
                "advanced_features": True,
                "shortcuts_enabled": True
            })
        elif avg_skill < 0.3:  # Beginner user
            modifications.update({
                "guidance_level": "detailed",
                "tutorial_mode": True,
                "safety_checks": True
            })
        else:  # Intermediate user
            modifications.update({
                "guidance_level": "moderate",
                "progressive_disclosure": True
            })
        
        return modifications

    async def _get_learning_style_modifications(
        self, learning_style: LearningStyle, workflow_type: str
    ) -> Dict[str, Any]:
        """Get learning style-based workflow modifications"""
        modifications = {}
        
        if learning_style == LearningStyle.VISUAL:
            modifications.update({
                "visual_feedback": True,
                "progress_visualization": True,
                "diagram_generation": True
            })
        elif learning_style == LearningStyle.AUDITORY:
            modifications.update({
                "audio_feedback": True,
                "voice_guidance": True,
                "sound_notifications": True
            })
        elif learning_style == LearningStyle.READING_WRITING:
            modifications.update({
                "text_summaries": True,
                "note_taking_integration": True,
                "written_instructions": "detailed"
            })
        
        return modifications

    # Public API methods
    async def update_user_profile(
        self, user_id: str, updates: Dict[str, Any]
    ) -> UserPersonalizationProfile:
        """Update user personalization profile"""
        try:
            profile = self.user_profiles.get(user_id)
            if not profile:
                profile = await self.build_user_profile(user_id)
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            
            profile.last_updated = datetime.utcnow()
            self.user_profiles[user_id] = profile
            
            return profile
            
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            raise

    async def get_user_profile(self, user_id: str) -> Optional[UserPersonalizationProfile]:
        """Get user personalization profile"""
        try:
            profile = self.user_profiles.get(user_id)
            if not profile:
                profile = await self.build_user_profile(user_id)
            
            return profile
            
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return None

    async def record_recommendation_interaction(
        self, user_id: str, recommendation_id: str, interaction_type: str
    ) -> bool:
        """Record user interaction with recommendation"""
        try:
            profile = self.user_profiles.get(user_id)
            if not profile:
                return False
            
            # Find recommendation in history
            for rec in profile.recommendation_history:
                if rec.get("id") == recommendation_id:
                    rec["interactions"] = rec.get("interactions", [])
                    rec["interactions"].append({
                        "type": interaction_type,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    break
            
            # Update profile
            self.user_profiles[user_id] = profile
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording recommendation interaction: {str(e)}")
            return False

    def get_personalization_metrics(self, user_id: str) -> Dict[str, Any]:
        """Get personalization metrics for user"""
        try:
            profile = self.user_profiles.get(user_id)
            if not profile:
                return {}
            
            return {
                "adaptation_score": profile.adaptation_score,
                "confidence_score": profile.confidence_score,
                "learning_style": profile.learning_style.value,
                "personality_type": profile.personality_type.value,
                "research_domains": profile.research_domains,
                "skill_levels": profile.skill_levels,
                "last_updated": profile.last_updated.isoformat(),
                "recommendation_count": len(profile.recommendation_history)
            }
            
        except Exception as e:
            logger.error(f"Error getting personalization metrics: {str(e)}")
            return {}

# Export classes
__all__ = [
    'PersonalizationEngine',
    'UserPersonalizationProfile',
    'PersonalizedRecommendation',
    'LearningStyle',
    'PersonalityType',
    'ContentPreference'
]