"""
Personalization engine for the RL system.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from enum import Enum

from ..models.user_models import (
    UserProfile, ExpertiseLevel, LearningPreferences, 
    PersonalizationContext
)
from ..models.conversation_models import ConversationState, Action, ActionType
from ..core.config import RLConfig

logger = logging.getLogger(__name__)


class ResponseStrategy(Enum):
    """Different response strategies for personalization."""
    TECHNICAL_DETAILED = "technical_detailed"
    SIMPLE_EXPLANATORY = "simple_explanatory"
    BALANCED_APPROACH = "balanced_approach"
    CREATIVE_ENGAGING = "creative_engaging"
    STEP_BY_STEP = "step_by_step"
    EXAMPLE_HEAVY = "example_heavy"
    CONCISE_DIRECT = "concise_direct"


class ResponseStrategySelector:
    """Selects appropriate response strategies based on user context."""
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.strategy_effectiveness: Dict[str, Dict[ResponseStrategy, float]] = {}
    
    async def select_response_strategy(
        self,
        personalization_context: PersonalizationContext,
        conversation_state: ConversationState
    ) -> ResponseStrategy:
        """Select the most appropriate response strategy."""
        
        user_id = personalization_context.user_id
        
        # Get strategy scores based on user context
        strategy_scores = await self._calculate_strategy_scores(
            personalization_context, conversation_state
        )
        
        # Apply historical effectiveness if available
        if user_id in self.strategy_effectiveness:
            for strategy, base_score in strategy_scores.items():
                historical_effectiveness = self.strategy_effectiveness[user_id].get(strategy, 0.5)
                # Blend base score with historical effectiveness
                strategy_scores[strategy] = base_score * 0.7 + historical_effectiveness * 0.3
        
        # Select strategy with highest score
        best_strategy = max(strategy_scores, key=strategy_scores.get)
        
        logger.debug(f"Selected strategy {best_strategy} for user {user_id}")
        return best_strategy
    
    async def _calculate_strategy_scores(
        self,
        context: PersonalizationContext,
        conversation_state: ConversationState
    ) -> Dict[ResponseStrategy, float]:
        """Calculate scores for each response strategy."""
        
        scores = {}
        
        # Base scores for each strategy
        for strategy in ResponseStrategy:
            scores[strategy] = 0.5  # Neutral baseline
        
        # Adjust based on expertise level
        expertise_factor = context.current_expertise_level.to_numeric()
        
        if expertise_factor >= 0.75:  # Expert/Advanced
            scores[ResponseStrategy.TECHNICAL_DETAILED] += 0.3
            scores[ResponseStrategy.CONCISE_DIRECT] += 0.2
        elif expertise_factor <= 0.25:  # Beginner
            scores[ResponseStrategy.SIMPLE_EXPLANATORY] += 0.3
            scores[ResponseStrategy.STEP_BY_STEP] += 0.2
            scores[ResponseStrategy.EXAMPLE_HEAVY] += 0.2
        else:  # Intermediate
            scores[ResponseStrategy.BALANCED_APPROACH] += 0.2
        
        # Adjust based on learning preferences
        prefs = context.learning_preferences
        
        if prefs.prefers_examples:
            scores[ResponseStrategy.EXAMPLE_HEAVY] += 0.15
        
        if prefs.prefers_step_by_step:
            scores[ResponseStrategy.STEP_BY_STEP] += 0.15
        
        if prefs.preferred_explanation_style == "technical":
            scores[ResponseStrategy.TECHNICAL_DETAILED] += 0.2
        elif prefs.preferred_explanation_style == "simple":
            scores[ResponseStrategy.SIMPLE_EXPLANATORY] += 0.2
        
        if prefs.preferred_response_length == "short":
            scores[ResponseStrategy.CONCISE_DIRECT] += 0.15
        elif prefs.preferred_response_length == "long":
            scores[ResponseStrategy.TECHNICAL_DETAILED] += 0.1
            scores[ResponseStrategy.EXAMPLE_HEAVY] += 0.1
        
        # Adjust based on engagement and satisfaction
        if context.engagement_level < 0.4:
            scores[ResponseStrategy.CREATIVE_ENGAGING] += 0.2
            scores[ResponseStrategy.EXAMPLE_HEAVY] += 0.1
        
        if context.satisfaction_score < 0.4:
            # Try different approach if satisfaction is low
            scores[ResponseStrategy.STEP_BY_STEP] += 0.15
            scores[ResponseStrategy.SIMPLE_EXPLANATORY] += 0.1
        
        # Adjust based on conversation context
        if len(conversation_state.conversation_history) > 5:
            # In longer conversations, be more direct
            scores[ResponseStrategy.CONCISE_DIRECT] += 0.1
        
        # Normalize scores to [0, 1] range
        for strategy in scores:
            scores[strategy] = max(0.0, min(1.0, scores[strategy]))
        
        return scores
    
    async def update_strategy_effectiveness(
        self,
        user_id: str,
        strategy: ResponseStrategy,
        effectiveness_score: float
    ) -> None:
        """Update the effectiveness score for a strategy."""
        
        if user_id not in self.strategy_effectiveness:
            self.strategy_effectiveness[user_id] = {}
        
        current_score = self.strategy_effectiveness[user_id].get(strategy, 0.5)
        # Exponential moving average update
        new_score = current_score * 0.8 + effectiveness_score * 0.2
        self.strategy_effectiveness[user_id][strategy] = new_score
        
        logger.debug(f"Updated strategy {strategy} effectiveness for user {user_id}: {new_score}")


class AdaptivePersonalizer:
    """Handles adaptive personalization based on real-time feedback."""
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.adaptation_history: Dict[str, List[Dict[str, Any]]] = {}
        self.adaptation_rate = 0.1
    
    async def adapt_response_parameters(
        self,
        user_id: str,
        base_parameters: Dict[str, Any],
        recent_feedback_score: float,
        conversation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt response parameters based on recent feedback."""
        
        adapted_parameters = base_parameters.copy()
        
        # Get adaptation history for user
        if user_id not in self.adaptation_history:
            self.adaptation_history[user_id] = []
        
        history = self.adaptation_history[user_id]
        
        # Adapt based on recent feedback
        if recent_feedback_score < 0.4:  # Poor feedback
            adapted_parameters = await self._apply_recovery_adaptations(
                adapted_parameters, history
            )
        elif recent_feedback_score > 0.7:  # Good feedback
            adapted_parameters = await self._reinforce_successful_adaptations(
                adapted_parameters, history
            )
        
        # Record adaptation
        adaptation_record = {
            "timestamp": datetime.now(),
            "original_parameters": base_parameters,
            "adapted_parameters": adapted_parameters,
            "feedback_score": recent_feedback_score,
            "context": conversation_context
        }
        
        history.append(adaptation_record)
        
        # Keep only recent history
        if len(history) > 50:
            self.adaptation_history[user_id] = history[-25:]
        
        return adapted_parameters
    
    async def _apply_recovery_adaptations(
        self,
        parameters: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply adaptations to recover from poor feedback."""
        
        adapted = parameters.copy()
        
        # Make responses more explanatory
        if "complexity_level" in adapted:
            adapted["complexity_level"] = max(0.1, adapted["complexity_level"] - 0.2)
        
        # Add more examples
        adapted["include_examples"] = True
        adapted["step_by_step"] = True
        
        # Make responses longer and more detailed
        if "response_length" in adapted:
            if adapted["response_length"] == "short":
                adapted["response_length"] = "medium"
            elif adapted["response_length"] == "medium":
                adapted["response_length"] = "long"
        
        # Increase engagement elements
        adapted["engagement_boost_needed"] = True
        
        return adapted
    
    async def _reinforce_successful_adaptations(
        self,
        parameters: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Reinforce adaptations that led to good feedback."""
        
        adapted = parameters.copy()
        
        # Find recent successful adaptations
        successful_adaptations = [
            record for record in history[-10:]
            if record["feedback_score"] > 0.6
        ]
        
        if successful_adaptations:
            # Extract common patterns from successful adaptations
            successful_params = [record["adapted_parameters"] for record in successful_adaptations]
            
            # Reinforce common successful patterns
            for key in adapted:
                if key in successful_params[0]:  # Check if key exists in successful params
                    # Find most common value for this parameter
                    values = [params.get(key) for params in successful_params if key in params]
                    if values:
                        # Use most common value (simple approach)
                        from collections import Counter
                        most_common = Counter(values).most_common(1)[0][0]
                        adapted[key] = most_common
        
        return adapted
    
    def get_adaptation_insights(self, user_id: str) -> Dict[str, Any]:
        """Get insights about adaptation patterns for a user."""
        
        if user_id not in self.adaptation_history:
            return {}
        
        history = self.adaptation_history[user_id]
        
        if not history:
            return {}
        
        # Calculate adaptation effectiveness
        feedback_scores = [record["feedback_score"] for record in history]
        avg_feedback = sum(feedback_scores) / len(feedback_scores)
        
        # Find most effective adaptations
        successful_records = [record for record in history if record["feedback_score"] > 0.6]
        
        insights = {
            "total_adaptations": len(history),
            "average_feedback_score": avg_feedback,
            "successful_adaptations": len(successful_records),
            "adaptation_success_rate": len(successful_records) / len(history) if history else 0,
            "recent_trend": self._calculate_recent_trend(feedback_scores)
        }
        
        return insights
    
    def _calculate_recent_trend(self, scores: List[float]) -> str:
        """Calculate recent trend in feedback scores."""
        
        if len(scores) < 5:
            return "insufficient_data"
        
        recent_scores = scores[-5:]
        older_scores = scores[-10:-5] if len(scores) >= 10 else scores[:-5]
        
        if not older_scores:
            return "insufficient_data"
        
        recent_avg = sum(recent_scores) / len(recent_scores)
        older_avg = sum(older_scores) / len(older_scores)
        
        diff = recent_avg - older_avg
        
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        else:
            return "stable"


class PersonalizationEngine:
    """Main personalization engine that coordinates all personalization components."""
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.strategy_selector = ResponseStrategySelector(config)
        self.adaptive_personalizer = AdaptivePersonalizer(config)
    
    async def generate_personalized_response_config(
        self,
        personalization_context: PersonalizationContext,
        conversation_state: ConversationState,
        recent_feedback_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """Generate personalized configuration for response generation."""
        
        # Select response strategy
        strategy = await self.strategy_selector.select_response_strategy(
            personalization_context, conversation_state
        )
        
        # Generate base response configuration
        base_config = await self._generate_base_config(
            strategy, personalization_context
        )
        
        # Apply adaptive personalization if feedback is available
        if recent_feedback_score is not None:
            base_config = await self.adaptive_personalizer.adapt_response_parameters(
                personalization_context.user_id,
                base_config,
                recent_feedback_score,
                {"strategy": strategy.value, "domain": conversation_state.domain_context}
            )
        
        return base_config
    
    async def _generate_base_config(
        self,
        strategy: ResponseStrategy,
        context: PersonalizationContext
    ) -> Dict[str, Any]:
        """Generate base configuration for a response strategy."""
        
        config = {
            "strategy": strategy.value,
            "complexity_level": context.current_expertise_level.to_numeric(),
            "explanation_style": context.learning_preferences.preferred_explanation_style,
            "response_length": context.learning_preferences.preferred_response_length,
            "include_examples": context.learning_preferences.prefers_examples,
            "step_by_step": context.learning_preferences.prefers_step_by_step,
            "include_code": context.learning_preferences.prefers_code_examples,
            "engagement_boost_needed": context.engagement_level < 0.4,
            "satisfaction_recovery_needed": context.satisfaction_score < 0.4
        }
        
        # Strategy-specific adjustments
        if strategy == ResponseStrategy.TECHNICAL_DETAILED:
            config.update({
                "complexity_level": min(1.0, config["complexity_level"] + 0.2),
                "include_technical_terms": True,
                "detailed_explanations": True
            })
        
        elif strategy == ResponseStrategy.SIMPLE_EXPLANATORY:
            config.update({
                "complexity_level": max(0.1, config["complexity_level"] - 0.3),
                "use_analogies": True,
                "avoid_jargon": True
            })
        
        elif strategy == ResponseStrategy.CREATIVE_ENGAGING:
            config.update({
                "use_analogies": True,
                "include_humor": True,
                "creative_examples": True
            })
        
        elif strategy == ResponseStrategy.STEP_BY_STEP:
            config.update({
                "step_by_step": True,
                "numbered_steps": True,
                "check_understanding": True
            })
        
        elif strategy == ResponseStrategy.EXAMPLE_HEAVY:
            config.update({
                "include_examples": True,
                "multiple_examples": True,
                "practical_examples": True
            })
        
        elif strategy == ResponseStrategy.CONCISE_DIRECT:
            config.update({
                "response_length": "short",
                "direct_answers": True,
                "minimal_explanation": True
            })
        
        return config
    
    async def update_personalization_effectiveness(
        self,
        user_id: str,
        strategy: ResponseStrategy,
        feedback_score: float
    ) -> None:
        """Update the effectiveness of personalization strategies."""
        
        await self.strategy_selector.update_strategy_effectiveness(
            user_id, strategy, feedback_score
        )
    
    def get_personalization_insights(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive personalization insights for a user."""
        
        strategy_insights = {}
        if user_id in self.strategy_selector.strategy_effectiveness:
            strategy_insights = self.strategy_selector.strategy_effectiveness[user_id]
        
        adaptation_insights = self.adaptive_personalizer.get_adaptation_insights(user_id)
        
        return {
            "strategy_effectiveness": strategy_insights,
            "adaptation_insights": adaptation_insights,
            "personalization_active": True
        }