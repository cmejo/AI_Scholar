"""
User modeling system for the RL framework.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from collections import defaultdict, Counter
import re

from ..models.user_models import (
    UserProfile, ExpertiseLevel, LearningPreferences, 
    InteractionPatterns, PersonalizationContext
)
from ..models.feedback_models import UserFeedback, FeedbackType
from ..models.conversation_models import ConversationState, ConversationTurn
from ..core.config import RLConfig

logger = logging.getLogger(__name__)


class ExpertiseTracker:
    """Tracks and updates user expertise levels across domains."""
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.domain_keywords = {
            "machine_learning": ["ml", "machine learning", "neural network", "deep learning", "algorithm", "model training"],
            "data_science": ["data science", "statistics", "pandas", "numpy", "visualization", "analysis"],
            "programming": ["python", "javascript", "code", "programming", "function", "class", "variable"],
            "research": ["research", "paper", "study", "methodology", "hypothesis", "experiment"],
            "mathematics": ["math", "equation", "formula", "calculus", "linear algebra", "statistics"],
            "ai_ethics": ["ethics", "bias", "fairness", "responsible ai", "transparency", "accountability"]
        }
    
    async def analyze_expertise_from_conversation(
        self,
        conversation_state: ConversationState,
        user_profile: UserProfile
    ) -> Dict[str, ExpertiseLevel]:
        """Analyze user expertise based on conversation content."""
        
        expertise_updates = {}
        
        # Analyze user inputs for domain knowledge indicators
        user_inputs = [turn.user_input for turn in conversation_state.conversation_history]
        combined_input = " ".join(user_inputs).lower()
        
        for domain, keywords in self.domain_keywords.items():
            expertise_score = self._calculate_domain_expertise_score(
                combined_input, keywords, user_profile.get_expertise_in_domain(domain)
            )
            
            new_level = self._score_to_expertise_level(expertise_score)
            current_level = user_profile.get_expertise_in_domain(domain)
            
            # Only update if there's a significant change
            if new_level != current_level:
                expertise_updates[domain] = new_level
        
        return expertise_updates
    
    def _calculate_domain_expertise_score(
        self,
        text: str,
        keywords: List[str],
        current_level: ExpertiseLevel
    ) -> float:
        """Calculate expertise score for a domain based on text analysis."""
        
        # Count keyword matches
        keyword_matches = sum(1 for keyword in keywords if keyword in text)
        keyword_density = keyword_matches / len(keywords) if keywords else 0
        
        # Analyze complexity of language used
        complexity_score = self._analyze_language_complexity(text, keywords)
        
        # Check for advanced concepts
        advanced_indicators = ["implementation", "optimization", "architecture", "framework", "methodology"]
        advanced_usage = sum(1 for indicator in advanced_indicators if indicator in text)
        
        # Calculate base score
        base_score = current_level.to_numeric()
        
        # Adjust based on analysis
        if keyword_density > 0.3:  # High domain relevance
            if complexity_score > 0.7:  # Complex language
                base_score = min(1.0, base_score + 0.1)
            elif advanced_usage > 2:  # Advanced concepts
                base_score = min(1.0, base_score + 0.05)
        
        return base_score
    
    def _analyze_language_complexity(self, text: str, domain_keywords: List[str]) -> float:
        """Analyze the complexity of language used in the domain context."""
        
        # Simple complexity metrics
        words = text.split()
        if not words:
            return 0.0
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Technical term usage
        technical_terms = sum(1 for word in words if len(word) > 8)
        technical_density = technical_terms / len(words)
        
        # Domain-specific terminology
        domain_term_usage = sum(1 for keyword in domain_keywords if keyword in text)
        domain_density = domain_term_usage / len(domain_keywords) if domain_keywords else 0
        
        # Combine metrics
        complexity = (
            min(avg_word_length / 10, 1.0) * 0.3 +
            technical_density * 0.4 +
            domain_density * 0.3
        )
        
        return min(complexity, 1.0)
    
    def _score_to_expertise_level(self, score: float) -> ExpertiseLevel:
        """Convert numeric score to expertise level."""
        if score >= 0.8:
            return ExpertiseLevel.EXPERT
        elif score >= 0.6:
            return ExpertiseLevel.ADVANCED
        elif score >= 0.4:
            return ExpertiseLevel.INTERMEDIATE
        else:
            return ExpertiseLevel.BEGINNER


class InteractionAnalyzer:
    """Analyzes user interaction patterns and preferences."""
    
    def __init__(self, config: RLConfig):
        self.config = config
    
    async def analyze_interaction_patterns(
        self,
        user_feedback_history: List[UserFeedback],
        conversation_history: List[ConversationState]
    ) -> InteractionPatterns:
        """Analyze user interaction patterns from history."""
        
        patterns = InteractionPatterns()
        
        if not conversation_history:
            return patterns
        
        # Calculate session metrics
        patterns.avg_session_duration = self._calculate_avg_session_duration(conversation_history)
        patterns.avg_questions_per_session = self._calculate_avg_questions_per_session(conversation_history)
        
        # Analyze activity patterns
        patterns.most_active_hours = self._analyze_activity_hours(conversation_history)
        
        # Analyze topic preferences
        patterns.common_topics = self._extract_common_topics(conversation_history)
        
        # Analyze question types
        patterns.typical_question_types = self._analyze_question_types(conversation_history)
        
        # Analyze satisfaction trends
        patterns.response_satisfaction_trend = self._extract_satisfaction_trend(user_feedback_history)
        
        # Analyze engagement trends
        patterns.engagement_trend = self._extract_engagement_trend(user_feedback_history)
        
        # Calculate learning progress indicators
        patterns.learning_progress_indicators = self._calculate_learning_progress(
            user_feedback_history, conversation_history
        )
        
        return patterns
    
    def _calculate_avg_session_duration(self, conversations: List[ConversationState]) -> float:
        """Calculate average session duration."""
        if not conversations:
            return 0.0
        
        durations = []
        for conv in conversations:
            if conv.conversation_history:
                start_time = conv.conversation_history[0].timestamp
                end_time = conv.conversation_history[-1].timestamp
                duration = (end_time - start_time).total_seconds() / 60  # minutes
                durations.append(duration)
        
        return sum(durations) / len(durations) if durations else 0.0
    
    def _calculate_avg_questions_per_session(self, conversations: List[ConversationState]) -> int:
        """Calculate average number of questions per session."""
        if not conversations:
            return 0
        
        question_counts = [len(conv.conversation_history) for conv in conversations]
        return int(sum(question_counts) / len(question_counts))
    
    def _analyze_activity_hours(self, conversations: List[ConversationState]) -> List[int]:
        """Analyze most active hours of the day."""
        hour_counts = Counter()
        
        for conv in conversations:
            for turn in conv.conversation_history:
                hour = turn.timestamp.hour
                hour_counts[hour] += 1
        
        # Return top 3 most active hours
        return [hour for hour, _ in hour_counts.most_common(3)]
    
    def _extract_common_topics(self, conversations: List[ConversationState]) -> List[str]:
        """Extract common topics from conversation history."""
        topic_keywords = Counter()
        
        # Simple keyword extraction
        for conv in conversations:
            for turn in conv.conversation_history:
                words = re.findall(r'\b\w+\b', turn.user_input.lower())
                # Filter out common words and focus on potential topics
                meaningful_words = [
                    word for word in words 
                    if len(word) > 4 and word not in ['what', 'how', 'when', 'where', 'why', 'could', 'would', 'should']
                ]
                topic_keywords.update(meaningful_words)
        
        # Return top 10 topics
        return [topic for topic, _ in topic_keywords.most_common(10)]
    
    def _analyze_question_types(self, conversations: List[ConversationState]) -> List[str]:
        """Analyze types of questions users typically ask."""
        question_types = Counter()
        
        for conv in conversations:
            for turn in conv.conversation_history:
                user_input = turn.user_input.lower()
                
                # Classify question types
                if user_input.startswith('how'):
                    question_types['how_to'] += 1
                elif user_input.startswith('what'):
                    question_types['definition'] += 1
                elif user_input.startswith('why'):
                    question_types['explanation'] += 1
                elif user_input.startswith('can you'):
                    question_types['request'] += 1
                elif '?' in user_input:
                    question_types['general_question'] += 1
                else:
                    question_types['statement'] += 1
        
        # Return top question types
        return [qtype for qtype, _ in question_types.most_common(5)]
    
    def _extract_satisfaction_trend(self, feedback_history: List[UserFeedback]) -> List[float]:
        """Extract satisfaction trend from feedback history."""
        satisfaction_scores = []
        
        for feedback in feedback_history[-20:]:  # Last 20 feedback items
            if feedback.feedback_type == FeedbackType.EXPLICIT_RATING and feedback.rating:
                # Convert 1-5 rating to 0-1 score
                score = (feedback.rating - 1) / 4
                satisfaction_scores.append(score)
            elif feedback.engagement_metrics:
                score = feedback.engagement_metrics.calculate_engagement_score()
                satisfaction_scores.append(score)
        
        return satisfaction_scores
    
    def _extract_engagement_trend(self, feedback_history: List[UserFeedback]) -> List[float]:
        """Extract engagement trend from feedback history."""
        engagement_scores = []
        
        for feedback in feedback_history[-20:]:  # Last 20 feedback items
            if feedback.engagement_metrics:
                score = feedback.engagement_metrics.calculate_engagement_score()
                engagement_scores.append(score)
        
        return engagement_scores
    
    def _calculate_learning_progress(
        self,
        feedback_history: List[UserFeedback],
        conversation_history: List[ConversationState]
    ) -> Dict[str, float]:
        """Calculate learning progress indicators."""
        
        progress_indicators = {}
        
        # Task completion rate
        completed_tasks = sum(
            1 for feedback in feedback_history
            if feedback.engagement_metrics and feedback.engagement_metrics.task_completion
        )
        total_tasks = len([f for f in feedback_history if f.engagement_metrics])
        progress_indicators['task_completion_rate'] = completed_tasks / total_tasks if total_tasks > 0 else 0.0
        
        # Question complexity trend
        if conversation_history:
            recent_conversations = conversation_history[-5:]
            complexity_scores = []
            
            for conv in recent_conversations:
                for turn in conv.conversation_history:
                    # Simple complexity measure based on question length and vocabulary
                    words = turn.user_input.split()
                    complexity = min(len(words) / 20, 1.0)  # Normalize by 20 words
                    complexity_scores.append(complexity)
            
            progress_indicators['question_complexity_trend'] = (
                sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0.0
            )
        
        # Engagement improvement
        if len(feedback_history) >= 10:
            recent_engagement = [
                f.engagement_metrics.calculate_engagement_score()
                for f in feedback_history[-5:]
                if f.engagement_metrics
            ]
            older_engagement = [
                f.engagement_metrics.calculate_engagement_score()
                for f in feedback_history[-10:-5]
                if f.engagement_metrics
            ]
            
            if recent_engagement and older_engagement:
                recent_avg = sum(recent_engagement) / len(recent_engagement)
                older_avg = sum(older_engagement) / len(older_engagement)
                progress_indicators['engagement_improvement'] = recent_avg - older_avg
        
        return progress_indicators


class UserModelingSystem:
    """Main user modeling system that coordinates all user modeling components."""
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.expertise_tracker = ExpertiseTracker(config)
        self.interaction_analyzer = InteractionAnalyzer(config)
        self.user_profiles: Dict[str, UserProfile] = {}
        self.feedback_history: Dict[str, List[UserFeedback]] = defaultdict(list)
        self.conversation_history: Dict[str, List[ConversationState]] = defaultdict(list)
    
    async def get_or_create_user_profile(self, user_id: str) -> UserProfile:
        """Get existing user profile or create a new one."""
        
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id,
                learning_preferences=LearningPreferences(),
                interaction_patterns=InteractionPatterns()
            )
            logger.info(f"Created new user profile for user {user_id}")
        
        return self.user_profiles[user_id]
    
    async def update_user_profile(
        self,
        user_id: str,
        conversation_state: ConversationState,
        feedback: Optional[UserFeedback] = None
    ) -> UserProfile:
        """Update user profile based on new interaction data."""
        
        profile = await self.get_or_create_user_profile(user_id)
        
        # Store conversation and feedback history
        self.conversation_history[user_id].append(conversation_state)
        if feedback:
            self.feedback_history[user_id].append(feedback)
        
        # Update expertise levels
        expertise_updates = await self.expertise_tracker.analyze_expertise_from_conversation(
            conversation_state, profile
        )
        
        for domain, new_level in expertise_updates.items():
            profile.update_expertise(domain, new_level)
            logger.info(f"Updated {user_id} expertise in {domain} to {new_level}")
        
        # Update interaction patterns
        profile.interaction_patterns = await self.interaction_analyzer.analyze_interaction_patterns(
            self.feedback_history[user_id],
            self.conversation_history[user_id]
        )
        
        # Update learning preferences based on feedback
        if feedback:
            await self._update_learning_preferences(profile, feedback)
        
        # Record interaction outcome
        if feedback:
            successful = feedback.is_positive()
            profile.record_interaction(successful)
        
        # Update personalization effectiveness
        await self._update_personalization_effectiveness(profile)
        
        profile.last_updated = datetime.now()
        
        return profile
    
    async def _update_learning_preferences(
        self,
        profile: UserProfile,
        feedback: UserFeedback
    ) -> None:
        """Update learning preferences based on feedback."""
        
        # This is a simplified version - in practice, this would be more sophisticated
        if feedback.is_positive():
            # If feedback is positive, slightly reinforce current preferences
            # This is a placeholder for more complex preference learning
            pass
        else:
            # If feedback is negative, consider adjusting preferences
            # This would involve more complex analysis of what went wrong
            pass
    
    async def _update_personalization_effectiveness(self, profile: UserProfile) -> None:
        """Update personalization effectiveness metric."""
        
        # Calculate effectiveness based on recent success rate
        recent_success_rate = profile.get_success_rate()
        
        # Smooth update of personalization effectiveness
        current_effectiveness = profile.personalization_effectiveness
        new_effectiveness = (
            current_effectiveness * 0.8 + recent_success_rate * 0.2
        )
        
        profile.personalization_effectiveness = new_effectiveness
    
    async def get_personalization_context(
        self,
        user_id: str,
        current_domain: str = ""
    ) -> PersonalizationContext:
        """Generate personalization context for current interaction."""
        
        profile = await self.get_or_create_user_profile(user_id)
        return profile.get_personalization_context(current_domain)
    
    async def infer_expertise_level(
        self,
        user_id: str,
        domain: str
    ) -> ExpertiseLevel:
        """Infer user's expertise level in a specific domain."""
        
        profile = await self.get_or_create_user_profile(user_id)
        return profile.get_expertise_in_domain(domain)
    
    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a user."""
        
        if user_id not in self.user_profiles:
            return {}
        
        profile = self.user_profiles[user_id]
        feedback_history = self.feedback_history[user_id]
        conversation_history = self.conversation_history[user_id]
        
        return {
            "total_interactions": profile.total_interactions,
            "success_rate": profile.get_success_rate(),
            "personalization_effectiveness": profile.personalization_effectiveness,
            "expertise_levels": {domain: level.value for domain, level in profile.expertise_levels.items()},
            "total_conversations": len(conversation_history),
            "total_feedback": len(feedback_history),
            "avg_session_duration": profile.interaction_patterns.avg_session_duration,
            "most_active_hours": profile.interaction_patterns.most_active_hours,
            "common_topics": profile.interaction_patterns.common_topics[:5],
            "learning_progress": profile.interaction_patterns.learning_progress_indicators
        }
    
    async def cleanup_old_data(self, retention_days: int = 90) -> None:
        """Clean up old conversation and feedback data."""
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        for user_id in list(self.conversation_history.keys()):
            # Filter conversations
            self.conversation_history[user_id] = [
                conv for conv in self.conversation_history[user_id]
                if conv.timestamp > cutoff_date
            ]
            
            # Filter feedback
            self.feedback_history[user_id] = [
                feedback for feedback in self.feedback_history[user_id]
                if feedback.timestamp > cutoff_date
            ]
            
            # Remove empty entries
            if not self.conversation_history[user_id]:
                del self.conversation_history[user_id]
            if not self.feedback_history[user_id]:
                del self.feedback_history[user_id]
        
        logger.info(f"Cleaned up data older than {retention_days} days")