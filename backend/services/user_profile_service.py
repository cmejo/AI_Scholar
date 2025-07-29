"""
User Profile Management Service

This service handles user profile creation, updates, interaction tracking,
and domain expertise detection for personalization features.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from core.database import UserProfile, User, Message, Conversation, DocumentTag, AnalyticsEvent
from models.schemas import (
    UserProfileCreate, UserProfileResponse, UserPreferences,
    AnalyticsEventCreate
)

logger = logging.getLogger(__name__)

class UserProfileManager:
    """
    Manages user profiles including preferences, interaction history,
    and domain expertise detection.
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    async def create_user_profile(
        self, 
        user_id: str, 
        preferences: Optional[UserPreferences] = None,
        learning_style: str = "visual"
    ) -> UserProfileResponse:
        """Create a new user profile with default settings."""
        try:
            # Check if profile already exists
            existing_profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if existing_profile:
                logger.warning(f"Profile already exists for user {user_id}")
                return self._to_response(existing_profile)
            
            # Set default preferences if none provided
            if preferences is None:
                preferences = UserPreferences()
            
            # Create new profile
            profile = UserProfile(
                user_id=user_id,
                preferences=preferences.model_dump(),
                interaction_history={
                    "total_queries": 0,
                    "total_documents": 0,
                    "query_history": [],
                    "document_interactions": {},
                    "feedback_history": [],
                    "session_count": 0,
                    "last_activity": None
                },
                domain_expertise={},
                learning_style=learning_style
            )
            
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
            
            logger.info(f"Created user profile for user {user_id}")
            return self._to_response(profile)
            
        except Exception as e:
            logger.error(f"Error creating user profile: {str(e)}")
            self.db.rollback()
            raise
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfileResponse]:
        """Get user profile by user ID."""
        try:
            profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if not profile:
                logger.info(f"No profile found for user {user_id}")
                return None
                
            return self._to_response(profile)
            
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            raise
    
    async def update_user_preferences(
        self, 
        user_id: str, 
        preferences: UserPreferences
    ) -> UserProfileResponse:
        """Update user preferences."""
        try:
            profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if not profile:
                # Create profile if it doesn't exist
                return await self.create_user_profile(user_id, preferences)
            
            profile.preferences = preferences.model_dump()
            profile.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(profile)
            
            logger.info(f"Updated preferences for user {user_id}")
            return self._to_response(profile)
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {str(e)}")
            self.db.rollback()
            raise
    
    async def track_user_interaction(
        self, 
        user_id: str, 
        interaction_type: str,
        interaction_data: Dict[str, Any]
    ) -> None:
        """Track user interaction for profile analysis."""
        try:
            profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if not profile:
                # Create profile if it doesn't exist
                await self.create_user_profile(user_id)
                profile = self.db.query(UserProfile).filter(
                    UserProfile.user_id == user_id
                ).first()
            
            # Update interaction history
            history = profile.interaction_history.copy() if profile.interaction_history else {}
            
            # Update counters
            if interaction_type == "query":
                history["total_queries"] = history.get("total_queries", 0) + 1
                
                # Track query history (keep last 100)
                query_history = history.get("query_history", [])
                query_history.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "query": interaction_data.get("query", ""),
                    "response_time": interaction_data.get("response_time", 0),
                    "sources_used": interaction_data.get("sources_used", 0),
                    "satisfaction": interaction_data.get("satisfaction")
                })
                history["query_history"] = query_history[-100:]  # Keep last 100
                
            elif interaction_type == "document":
                history["total_documents"] = history.get("total_documents", 0) + 1
                
                # Track document interactions
                doc_interactions = history.get("document_interactions", {})
                doc_id = interaction_data.get("document_id")
                if doc_id:
                    if doc_id not in doc_interactions:
                        doc_interactions[doc_id] = {
                            "access_count": 0,
                            "first_access": datetime.utcnow().isoformat(),
                            "last_access": None,
                            "queries_related": 0
                        }
                    doc_interactions[doc_id]["access_count"] += 1
                    doc_interactions[doc_id]["last_access"] = datetime.utcnow().isoformat()
                    if interaction_data.get("query_related"):
                        doc_interactions[doc_id]["queries_related"] += 1
                
                history["document_interactions"] = doc_interactions
                
            elif interaction_type == "feedback":
                feedback_history = history.get("feedback_history", [])
                feedback_history.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "feedback_type": interaction_data.get("feedback_type"),
                    "rating": interaction_data.get("rating"),
                    "message_id": interaction_data.get("message_id")
                })
                history["feedback_history"] = feedback_history[-50:]  # Keep last 50
            
            # Update last activity
            history["last_activity"] = datetime.utcnow().isoformat()
            
            profile.interaction_history = history
            profile.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(profile)
            
            # Update domain expertise asynchronously
            await self._update_domain_expertise(user_id)
            
            logger.debug(f"Tracked {interaction_type} interaction for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error tracking user interaction: {str(e)}")
            self.db.rollback()
            raise
    
    async def analyze_user_behavior(self, user_id: str) -> Dict[str, Any]:
        """Analyze user behavior patterns for personalization."""
        try:
            profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if not profile:
                return {"analysis": "insufficient_data"}
            
            history = profile.interaction_history
            if not history or (history.get("total_queries", 0) == 0 and history.get("total_documents", 0) == 0):
                return {"analysis": "insufficient_data"}
            
            analysis = {}
            
            # Activity patterns (always calculate these)
            analysis["total_interactions"] = history.get("total_queries", 0) + history.get("total_documents", 0)
            analysis["engagement_level"] = "high" if analysis["total_interactions"] > 50 else "medium" if analysis["total_interactions"] > 10 else "low"
            
            # Query patterns
            query_history = history.get("query_history", [])
            if query_history:
                # Calculate average response time preference
                response_times = [q.get("response_time", 0) for q in query_history if q.get("response_time")]
                if response_times:
                    analysis["avg_response_time"] = sum(response_times) / len(response_times)
                
                # Analyze query complexity (rough estimate based on length)
                query_lengths = [len(q.get("query", "")) for q in query_history]
                if query_lengths:
                    analysis["avg_query_length"] = sum(query_lengths) / len(query_lengths)
                    analysis["query_complexity"] = "high" if analysis["avg_query_length"] > 100 else "medium" if analysis["avg_query_length"] > 50 else "low"
                
                # Satisfaction patterns
                satisfactions = [q.get("satisfaction") for q in query_history if q.get("satisfaction") is not None]
                if satisfactions:
                    analysis["avg_satisfaction"] = sum(satisfactions) / len(satisfactions)
                    analysis["satisfaction_trend"] = "improving" if len(satisfactions) > 5 and sum(satisfactions[-3:]) > sum(satisfactions[:3]) else "stable"
                
                # Learning style inference
                visual_keywords = ["example", "diagram", "chart", "visual", "show", "image"]
                visual_queries = sum(1 for q in query_history if any(keyword in q.get("query", "").lower() for keyword in visual_keywords))
                if visual_queries > len(query_history) * 0.3:
                    analysis["inferred_learning_style"] = "visual"
                else:
                    analysis["inferred_learning_style"] = "reading"
            
            # Document usage patterns
            doc_interactions = history.get("document_interactions", {})
            if doc_interactions:
                access_counts = [doc["access_count"] for doc in doc_interactions.values()]
                analysis["avg_doc_access"] = sum(access_counts) / len(access_counts)
                analysis["doc_usage_pattern"] = "focused" if max(access_counts) > 3 * analysis["avg_doc_access"] else "diverse"
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing user behavior: {str(e)}")
            return {"error": str(e)}
    
    async def get_domain_expertise(self, user_id: str) -> Dict[str, float]:
        """Get user's domain expertise scores."""
        try:
            profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if not profile:
                return {}
            
            return profile.domain_expertise or {}
            
        except Exception as e:
            logger.error(f"Error getting domain expertise: {str(e)}")
            return {}
    
    async def _update_domain_expertise(self, user_id: str) -> None:
        """Update domain expertise based on user interactions."""
        try:
            # Get user's document interactions and queries
            profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if not profile:
                return
            
            # Analyze document tags to infer domain expertise
            domain_scores = defaultdict(float)
            
            # Get documents the user has interacted with
            history = profile.interaction_history or {}
            doc_interactions = history.get("document_interactions", {})
            
            for doc_id, interaction in doc_interactions.items():
                # Get document tags
                tags = self.db.query(DocumentTag).filter(
                    DocumentTag.document_id == doc_id
                ).all()
                
                # Weight by interaction frequency
                weight = min(interaction["access_count"] / 10.0, 1.0)  # Cap at 1.0
                
                for tag in tags:
                    if tag.tag_type == "domain":
                        domain_scores[tag.tag_name] += weight * tag.confidence_score
                    elif tag.tag_type == "topic":
                        # Topics contribute less to domain expertise
                        domain_scores[tag.tag_name] += weight * tag.confidence_score * 0.5
            
            # Analyze query patterns for domain keywords
            query_history = history.get("query_history", [])
            domain_keywords = {
                "technology": ["software", "programming", "computer", "tech", "algorithm", "data"],
                "science": ["research", "study", "experiment", "hypothesis", "theory", "analysis"],
                "business": ["market", "strategy", "finance", "management", "revenue", "profit"],
                "medicine": ["health", "medical", "patient", "treatment", "diagnosis", "clinical"],
                "education": ["learning", "teaching", "student", "curriculum", "academic", "school"],
                "law": ["legal", "court", "law", "regulation", "compliance", "contract"]
            }
            
            for query in query_history:
                query_text = query.get("query", "").lower()
                for domain, keywords in domain_keywords.items():
                    keyword_count = sum(1 for keyword in keywords if keyword in query_text)
                    if keyword_count > 0:
                        domain_scores[domain] += keyword_count * 0.1
            
            # Normalize scores (0-1 range)
            if domain_scores:
                max_score = max(domain_scores.values())
                if max_score > 0:
                    for domain in domain_scores:
                        domain_scores[domain] = min(domain_scores[domain] / max_score, 1.0)
            
            # Update profile
            profile.domain_expertise = dict(domain_scores)
            profile.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.debug(f"Updated domain expertise for user {user_id}: {dict(domain_scores)}")
            
        except Exception as e:
            logger.error(f"Error updating domain expertise: {str(e)}")
            self.db.rollback()
    
    async def get_personalization_weights(self, user_id: str) -> Dict[str, float]:
        """Get personalization weights based on user profile."""
        try:
            profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if not profile:
                return self._get_default_weights()
            
            weights = {}
            
            # Base weights from preferences
            preferences = profile.preferences or {}
            weights["response_style_weight"] = 1.0 if preferences.get("response_style") == "detailed" else 0.5
            weights["citation_weight"] = 1.0 if preferences.get("citation_preference") == "inline" else 0.7
            weights["reasoning_weight"] = 1.0 if preferences.get("reasoning_display", True) else 0.3
            weights["uncertainty_tolerance"] = preferences.get("uncertainty_tolerance", 0.5)
            
            # Domain expertise weights
            domain_expertise = profile.domain_expertise or {}
            weights["domain_weights"] = domain_expertise
            
            # Behavior-based weights
            behavior_analysis = await self.analyze_user_behavior(user_id)
            if "avg_satisfaction" in behavior_analysis:
                weights["satisfaction_weight"] = behavior_analysis["avg_satisfaction"]
            else:
                weights["satisfaction_weight"] = 0.7  # Default
            
            if "query_complexity" in behavior_analysis:
                complexity = behavior_analysis["query_complexity"]
                weights["complexity_preference"] = 1.0 if complexity == "high" else 0.7 if complexity == "medium" else 0.4
            else:
                weights["complexity_preference"] = 0.6  # Default
            
            return weights
            
        except Exception as e:
            logger.error(f"Error getting personalization weights: {str(e)}")
            return self._get_default_weights()
    
    def _get_default_weights(self) -> Dict[str, float]:
        """Get default personalization weights."""
        return {
            "response_style_weight": 0.8,
            "citation_weight": 0.8,
            "reasoning_weight": 0.7,
            "uncertainty_tolerance": 0.5,
            "domain_weights": {},
            "satisfaction_weight": 0.7,
            "complexity_preference": 0.6
        }
    
    def _to_response(self, profile: UserProfile) -> UserProfileResponse:
        """Convert database model to response model."""
        return UserProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            preferences=UserPreferences(**profile.preferences) if profile.preferences else UserPreferences(),
            interaction_history=profile.interaction_history or {},
            domain_expertise=profile.domain_expertise or {},
            learning_style=profile.learning_style,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )

class InteractionTracker:
    """
    Helper class for tracking user interactions across the system.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.profile_manager = UserProfileManager(db)
    
    async def track_query(
        self, 
        user_id: str, 
        query: str, 
        response_time: float,
        sources_used: int,
        satisfaction: Optional[float] = None
    ) -> None:
        """Track a user query interaction."""
        await self.profile_manager.track_user_interaction(
            user_id=user_id,
            interaction_type="query",
            interaction_data={
                "query": query,
                "response_time": response_time,
                "sources_used": sources_used,
                "satisfaction": satisfaction
            }
        )
    
    async def track_document_access(
        self, 
        user_id: str, 
        document_id: str,
        query_related: bool = False
    ) -> None:
        """Track document access interaction."""
        await self.profile_manager.track_user_interaction(
            user_id=user_id,
            interaction_type="document",
            interaction_data={
                "document_id": document_id,
                "query_related": query_related
            }
        )
    
    async def track_feedback(
        self, 
        user_id: str, 
        feedback_type: str,
        rating: Optional[float] = None,
        message_id: Optional[str] = None
    ) -> None:
        """Track user feedback interaction."""
        await self.profile_manager.track_user_interaction(
            user_id=user_id,
            interaction_type="feedback",
            interaction_data={
                "feedback_type": feedback_type,
                "rating": rating,
                "message_id": message_id
            }
        )