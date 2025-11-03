"""
Feedback collection components for the RL system.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import logging
from dataclasses import asdict

from ..models.feedback_models import (
    UserFeedback, FeedbackType, EngagementMetrics, QualityMetrics
)
from ..models.conversation_models import ConversationState, ConversationTurn
from ..core.config import RLConfig

logger = logging.getLogger(__name__)


class ExplicitFeedbackCollector:
    """Collects explicit feedback from users (ratings, text feedback)."""
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.feedback_storage: List[UserFeedback] = []
        self.feedback_callbacks: List[Callable] = []
    
    async def collect_rating_feedback(
        self,
        conversation_id: str,
        turn_id: str,
        user_id: str,
        rating: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserFeedback:
        """Collect explicit rating feedback from user."""
        
        # Validate rating
        if not (1.0 <= rating <= 5.0):
            raise ValueError("Rating must be between 1.0 and 5.0")
        
        feedback = UserFeedback(
            conversation_id=conversation_id,
            turn_id=turn_id,
            user_id=user_id,
            feedback_type=FeedbackType.EXPLICIT_RATING,
            rating=rating,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        await self._store_feedback(feedback)
        await self._notify_callbacks(feedback)
        
        logger.info(f"Collected rating feedback: {rating} for conversation {conversation_id}")
        return feedback
    
    async def collect_text_feedback(
        self,
        conversation_id: str,
        turn_id: str,
        user_id: str,
        text_feedback: str,
        rating: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserFeedback:
        """Collect explicit text feedback from user."""
        
        if not text_feedback or len(text_feedback.strip()) < 3:
            raise ValueError("Text feedback must be at least 3 characters")
        
        feedback = UserFeedback(
            conversation_id=conversation_id,
            turn_id=turn_id,
            user_id=user_id,
            feedback_type=FeedbackType.EXPLICIT_TEXT,
            rating=rating,
            text_feedback=text_feedback.strip(),
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        await self._store_feedback(feedback)
        await self._notify_callbacks(feedback)
        
        logger.info(f"Collected text feedback for conversation {conversation_id}")
        return feedback
    
    async def collect_quality_assessment(
        self,
        conversation_id: str,
        turn_id: str,
        user_id: str,
        quality_metrics: QualityMetrics,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserFeedback:
        """Collect quality assessment feedback."""
        
        feedback = UserFeedback(
            conversation_id=conversation_id,
            turn_id=turn_id,
            user_id=user_id,
            feedback_type=FeedbackType.QUALITY_ASSESSMENT,
            quality_metrics=quality_metrics,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        await self._store_feedback(feedback)
        await self._notify_callbacks(feedback)
        
        logger.info(f"Collected quality assessment for conversation {conversation_id}")
        return feedback
    
    async def _store_feedback(self, feedback: UserFeedback) -> None:
        """Store feedback in memory (would be database in production)."""
        self.feedback_storage.append(feedback)
        
        # Keep only recent feedback in memory
        if len(self.feedback_storage) > 10000:
            self.feedback_storage = self.feedback_storage[-5000:]
    
    async def _notify_callbacks(self, feedback: UserFeedback) -> None:
        """Notify registered callbacks about new feedback."""
        for callback in self.feedback_callbacks:
            try:
                await callback(feedback)
            except Exception as e:
                logger.error(f"Error in feedback callback: {e}")
    
    def register_callback(self, callback: Callable) -> None:
        """Register callback for new feedback."""
        self.feedback_callbacks.append(callback)
    
    async def get_feedback_for_conversation(self, conversation_id: str) -> List[UserFeedback]:
        """Get all feedback for a specific conversation."""
        return [f for f in self.feedback_storage if f.conversation_id == conversation_id]


class ImplicitFeedbackCollector:
    """Collects implicit feedback from user behavior and engagement."""
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.engagement_tracking: Dict[str, Dict[str, Any]] = {}
        self.feedback_storage: List[UserFeedback] = []
        self.feedback_callbacks: List[Callable] = []
    
    async def start_engagement_tracking(
        self,
        conversation_id: str,
        turn_id: str,
        user_id: str
    ) -> None:
        """Start tracking engagement for a conversation turn."""
        
        tracking_key = f"{conversation_id}:{turn_id}"
        self.engagement_tracking[tracking_key] = {
            "conversation_id": conversation_id,
            "turn_id": turn_id,
            "user_id": user_id,
            "start_time": time.time(),
            "interactions": [],
            "scroll_events": [],
            "copy_events": 0,
            "link_clicks": 0,
            "follow_up_questions": 0
        }
        
        logger.debug(f"Started engagement tracking for {tracking_key}")
    
    async def record_interaction(
        self,
        conversation_id: str,
        turn_id: str,
        interaction_type: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a user interaction."""
        
        tracking_key = f"{conversation_id}:{turn_id}"
        if tracking_key not in self.engagement_tracking:
            logger.warning(f"No engagement tracking found for {tracking_key}")
            return
        
        interaction = {
            "type": interaction_type,
            "timestamp": time.time(),
            "data": data or {}
        }
        
        self.engagement_tracking[tracking_key]["interactions"].append(interaction)
        
        # Update specific counters
        if interaction_type == "copy_text":
            self.engagement_tracking[tracking_key]["copy_events"] += 1
        elif interaction_type == "click_link":
            self.engagement_tracking[tracking_key]["link_clicks"] += 1
        elif interaction_type == "follow_up_question":
            self.engagement_tracking[tracking_key]["follow_up_questions"] += 1
        elif interaction_type == "scroll":
            self.engagement_tracking[tracking_key]["scroll_events"].append(data)
    
    async def end_engagement_tracking(
        self,
        conversation_id: str,
        turn_id: str,
        task_completed: bool = False
    ) -> UserFeedback:
        """End engagement tracking and generate implicit feedback."""
        
        tracking_key = f"{conversation_id}:{turn_id}"
        if tracking_key not in self.engagement_tracking:
            raise ValueError(f"No engagement tracking found for {tracking_key}")
        
        tracking_data = self.engagement_tracking[tracking_key]
        end_time = time.time()
        
        # Calculate engagement metrics
        engagement_metrics = self._calculate_engagement_metrics(
            tracking_data, end_time, task_completed
        )
        
        feedback = UserFeedback(
            conversation_id=conversation_id,
            turn_id=turn_id,
            user_id=tracking_data["user_id"],
            feedback_type=FeedbackType.IMPLICIT_ENGAGEMENT,
            engagement_metrics=engagement_metrics,
            timestamp=datetime.now(),
            metadata={"tracking_data": tracking_data}
        )
        
        # Clean up tracking data
        del self.engagement_tracking[tracking_key]
        
        await self._store_feedback(feedback)
        await self._notify_callbacks(feedback)
        
        logger.info(f"Generated implicit feedback for {tracking_key}")
        return feedback
    
    def _calculate_engagement_metrics(
        self,
        tracking_data: Dict[str, Any],
        end_time: float,
        task_completed: bool
    ) -> EngagementMetrics:
        """Calculate engagement metrics from tracking data."""
        
        start_time = tracking_data["start_time"]
        session_duration = end_time - start_time
        
        # Calculate reading time (time between start and first interaction)
        interactions = tracking_data["interactions"]
        if interactions:
            first_interaction_time = min(i["timestamp"] for i in interactions)
            reading_time = first_interaction_time - start_time
        else:
            reading_time = session_duration
        
        # Calculate response time (time to first user action)
        response_time = reading_time if reading_time > 0 else 0
        
        # Calculate scroll depth
        scroll_events = tracking_data["scroll_events"]
        max_scroll_depth = 0.0
        if scroll_events:
            max_scroll_depth = max(
                event.get("scroll_percentage", 0) for event in scroll_events
            )
        
        return EngagementMetrics(
            response_time=response_time,
            reading_time=reading_time,
            follow_up_questions=tracking_data["follow_up_questions"],
            copy_paste_actions=tracking_data["copy_events"],
            link_clicks=tracking_data["link_clicks"],
            scroll_depth=max_scroll_depth,
            session_duration=session_duration,
            task_completion=task_completed
        )
    
    async def _store_feedback(self, feedback: UserFeedback) -> None:
        """Store feedback in memory."""
        self.feedback_storage.append(feedback)
        
        # Keep only recent feedback in memory
        if len(self.feedback_storage) > 10000:
            self.feedback_storage = self.feedback_storage[-5000:]
    
    async def _notify_callbacks(self, feedback: UserFeedback) -> None:
        """Notify registered callbacks about new feedback."""
        for callback in self.feedback_callbacks:
            try:
                await callback(feedback)
            except Exception as e:
                logger.error(f"Error in feedback callback: {e}")
    
    def register_callback(self, callback: Callable) -> None:
        """Register callback for new feedback."""
        self.feedback_callbacks.append(callback)


class FeedbackProcessor:
    """Processes and aggregates feedback from multiple sources."""
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.explicit_collector = ExplicitFeedbackCollector(config)
        self.implicit_collector = ImplicitFeedbackCollector(config)
        self.processed_feedback: Dict[str, List[UserFeedback]] = {}
    
    async def initialize(self) -> None:
        """Initialize the feedback processor."""
        # Register callbacks to aggregate feedback
        self.explicit_collector.register_callback(self._process_feedback)
        self.implicit_collector.register_callback(self._process_feedback)
        
        logger.info("Feedback processor initialized")
    
    async def _process_feedback(self, feedback: UserFeedback) -> None:
        """Process incoming feedback."""
        conversation_key = feedback.conversation_id
        
        if conversation_key not in self.processed_feedback:
            self.processed_feedback[conversation_key] = []
        
        self.processed_feedback[conversation_key].append(feedback)
        
        # Keep only recent conversations
        if len(self.processed_feedback) > 1000:
            # Remove oldest conversations
            oldest_keys = sorted(self.processed_feedback.keys())[:100]
            for key in oldest_keys:
                del self.processed_feedback[key]
    
    async def get_conversation_feedback(self, conversation_id: str) -> List[UserFeedback]:
        """Get all feedback for a conversation."""
        explicit_feedback = await self.explicit_collector.get_feedback_for_conversation(conversation_id)
        implicit_feedback = [
            f for f in self.implicit_collector.feedback_storage 
            if f.conversation_id == conversation_id
        ]
        
        return explicit_feedback + implicit_feedback
    
    async def get_aggregated_feedback_score(self, conversation_id: str) -> float:
        """Get aggregated feedback score for a conversation."""
        feedback_list = await self.get_conversation_feedback(conversation_id)
        
        if not feedback_list:
            return 0.5  # Neutral score
        
        scores = []
        weights = []
        
        for feedback in feedback_list:
            if feedback.feedback_type == FeedbackType.EXPLICIT_RATING and feedback.rating:
                # Convert 1-5 rating to 0-1 score
                score = (feedback.rating - 1) / 4
                scores.append(score)
                weights.append(self.config.reward.explicit_feedback_weight)
            
            elif feedback.feedback_type == FeedbackType.IMPLICIT_ENGAGEMENT and feedback.engagement_metrics:
                score = feedback.engagement_metrics.calculate_engagement_score()
                scores.append(score)
                weights.append(self.config.reward.implicit_feedback_weight)
            
            elif feedback.feedback_type == FeedbackType.QUALITY_ASSESSMENT and feedback.quality_metrics:
                score = feedback.quality_metrics.calculate_overall_quality()
                scores.append(score)
                weights.append(self.config.reward.quality_assessment_weight)
        
        if not scores:
            return 0.5
        
        # Calculate weighted average
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        total_weight = sum(weights)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.5
    
    def get_explicit_collector(self) -> ExplicitFeedbackCollector:
        """Get the explicit feedback collector."""
        return self.explicit_collector
    
    def get_implicit_collector(self) -> ImplicitFeedbackCollector:
        """Get the implicit feedback collector."""
        return self.implicit_collector