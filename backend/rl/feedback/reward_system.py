"""
Reward calculation system for the RL framework.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from dataclasses import asdict

from ..models.feedback_models import UserFeedback, FeedbackType, EngagementMetrics, QualityMetrics
from ..models.reward_models import MultiObjectiveReward, RewardWeights, RewardComponent
from ..models.conversation_models import ConversationState, ConversationTurn, Action
from ..core.config import RLConfig

logger = logging.getLogger(__name__)


class RewardValidator:
    """Validates and filters reward signals."""
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.reward_history: List[MultiObjectiveReward] = []
    
    def validate_reward(self, reward: MultiObjectiveReward) -> Tuple[bool, List[str]]:
        """Validate a reward signal and return validation result."""
        errors = []
        
        # Check if reward values are in valid range
        if not reward.is_valid():
            errors.append("Reward components must be between 0 and 1")
        
        # Check safety score
        if reward.safety < 0.5:
            errors.append(f"Safety score too low: {reward.safety}")
        
        # Check for extreme values that might indicate errors
        components = [
            reward.helpfulness, reward.accuracy, reward.engagement,
            reward.learning_effectiveness, reward.personalization
        ]
        
        if any(comp > 0.99 for comp in components):
            errors.append("Suspiciously high reward components detected")
        
        # Check confidence level
        if reward.confidence < 0.1:
            errors.append(f"Reward confidence too low: {reward.confidence}")
        
        return len(errors) == 0, errors
    
    def detect_outliers(self, reward: MultiObjectiveReward) -> bool:
        """Detect if reward is an outlier compared to recent history."""
        if len(self.reward_history) < 10:
            return False
        
        recent_rewards = self.reward_history[-50:]  # Last 50 rewards
        recent_totals = [r.total_reward for r in recent_rewards]
        
        mean_reward = np.mean(recent_totals)
        std_reward = np.std(recent_totals)
        
        # Check if current reward is more than 3 standard deviations away
        if abs(reward.total_reward - mean_reward) > 3 * std_reward:
            logger.warning(f"Outlier reward detected: {reward.total_reward} vs mean {mean_reward}")
            return True
        
        return False
    
    def add_to_history(self, reward: MultiObjectiveReward) -> None:
        """Add reward to validation history."""
        self.reward_history.append(reward)
        
        # Keep only recent history
        if len(self.reward_history) > 1000:
            self.reward_history = self.reward_history[-500:]


class RewardCalculator:
    """Base class for reward calculation."""
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.validator = RewardValidator(config)
    
    async def calculate_reward(
        self,
        conversation_state: ConversationState,
        action: Action,
        feedback_list: List[UserFeedback],
        quality_metrics: Optional[QualityMetrics] = None
    ) -> MultiObjectiveReward:
        """Calculate reward for a conversation turn."""
        
        reward = MultiObjectiveReward(
            conversation_id=conversation_state.conversation_id,
            turn_id=conversation_state.conversation_history[-1].turn_id if conversation_state.conversation_history else "",
            weights=RewardWeights(
                helpfulness=self.config.reward.helpfulness_weight,
                accuracy=self.config.reward.accuracy_weight,
                engagement=self.config.reward.engagement_weight,
                safety=self.config.reward.safety_weight,
                learning_effectiveness=self.config.reward.learning_effectiveness_weight,
                personalization=self.config.reward.personalization_weight,
                efficiency=self.config.reward.efficiency_weight,
                creativity=self.config.reward.creativity_weight
            )
        )
        
        # Calculate individual reward components
        reward.helpfulness = await self._calculate_helpfulness_reward(
            conversation_state, action, feedback_list
        )
        
        reward.accuracy = await self._calculate_accuracy_reward(
            conversation_state, action, quality_metrics
        )
        
        reward.engagement = await self._calculate_engagement_reward(
            feedback_list
        )
        
        reward.safety = await self._calculate_safety_reward(
            conversation_state, action, quality_metrics
        )
        
        reward.learning_effectiveness = await self._calculate_learning_reward(
            conversation_state, action, feedback_list
        )
        
        reward.personalization = await self._calculate_personalization_reward(
            conversation_state, action
        )
        
        reward.efficiency = await self._calculate_efficiency_reward(
            conversation_state, action
        )
        
        reward.creativity = await self._calculate_creativity_reward(
            conversation_state, action
        )
        
        # Apply safety penalties if needed
        reward.apply_safety_penalty(self.config.reward.safety_penalty_factor)
        
        # Calculate total reward
        reward.calculate_total_reward()
        
        # Validate reward
        is_valid, errors = self.validator.validate_reward(reward)
        if not is_valid:
            logger.warning(f"Invalid reward generated: {errors}")
            reward.confidence *= 0.5  # Reduce confidence for invalid rewards
        
        # Check for outliers
        if self.validator.detect_outliers(reward):
            reward.confidence *= 0.7  # Reduce confidence for outliers
        
        # Add to validation history
        self.validator.add_to_history(reward)
        
        return reward
    
    async def _calculate_helpfulness_reward(
        self,
        conversation_state: ConversationState,
        action: Action,
        feedback_list: List[UserFeedback]
    ) -> float:
        """Calculate helpfulness component of reward."""
        
        helpfulness_score = 0.5  # Default neutral score
        
        # Check explicit feedback
        for feedback in feedback_list:
            if feedback.feedback_type == FeedbackType.EXPLICIT_RATING and feedback.rating:
                # Convert 1-5 rating to 0-1 helpfulness score
                helpfulness_score = max(helpfulness_score, (feedback.rating - 1) / 4)
            
            elif feedback.feedback_type == FeedbackType.QUALITY_ASSESSMENT and feedback.quality_metrics:
                helpfulness_score = max(helpfulness_score, feedback.quality_metrics.helpfulness)
        
        # Check implicit signals
        for feedback in feedback_list:
            if feedback.feedback_type == FeedbackType.IMPLICIT_ENGAGEMENT and feedback.engagement_metrics:
                engagement_score = feedback.engagement_metrics.calculate_engagement_score()
                # High engagement suggests helpfulness
                helpfulness_score = max(helpfulness_score, engagement_score * 0.8)
        
        # Bonus for follow-up questions (indicates engagement)
        follow_up_count = sum(
            f.engagement_metrics.follow_up_questions 
            for f in feedback_list 
            if f.engagement_metrics
        )
        if follow_up_count > 0:
            helpfulness_score = min(1.0, helpfulness_score + 0.1)
        
        return helpfulness_score
    
    async def _calculate_accuracy_reward(
        self,
        conversation_state: ConversationState,
        action: Action,
        quality_metrics: Optional[QualityMetrics]
    ) -> float:
        """Calculate accuracy component of reward."""
        
        if quality_metrics:
            return quality_metrics.factual_accuracy
        
        # Default accuracy based on action confidence
        base_accuracy = action.confidence if action.confidence else 0.7
        
        # Penalize if response seems uncertain
        if "I'm not sure" in action.response_text or "I don't know" in action.response_text:
            base_accuracy *= 0.8
        
        # Bonus for citing sources or providing references
        if "source:" in action.response_text.lower() or "reference:" in action.response_text.lower():
            base_accuracy = min(1.0, base_accuracy + 0.1)
        
        return base_accuracy
    
    async def _calculate_engagement_reward(self, feedback_list: List[UserFeedback]) -> float:
        """Calculate engagement component of reward."""
        
        engagement_scores = []
        
        for feedback in feedback_list:
            if feedback.feedback_type == FeedbackType.IMPLICIT_ENGAGEMENT and feedback.engagement_metrics:
                engagement_scores.append(feedback.engagement_metrics.calculate_engagement_score())
        
        if not engagement_scores:
            return 0.5  # Default neutral engagement
        
        # Return average engagement score
        return sum(engagement_scores) / len(engagement_scores)
    
    async def _calculate_safety_reward(
        self,
        conversation_state: ConversationState,
        action: Action,
        quality_metrics: Optional[QualityMetrics]
    ) -> float:
        """Calculate safety component of reward."""
        
        if quality_metrics:
            return min(quality_metrics.safety_score, quality_metrics.bias_score)
        
        # Basic safety checks
        safety_score = 1.0
        
        # Check for potentially harmful content
        harmful_keywords = ["violence", "harm", "illegal", "dangerous"]
        response_lower = action.response_text.lower()
        
        for keyword in harmful_keywords:
            if keyword in response_lower:
                safety_score *= 0.8
        
        # Check response length (extremely long responses might be problematic)
        if len(action.response_text) > 2000:
            safety_score *= 0.9
        
        return max(0.0, safety_score)
    
    async def _calculate_learning_reward(
        self,
        conversation_state: ConversationState,
        action: Action,
        feedback_list: List[UserFeedback]
    ) -> float:
        """Calculate learning effectiveness component of reward."""
        
        learning_score = 0.5  # Default neutral
        
        # Check if response includes educational elements
        educational_indicators = [
            "explanation", "example", "step by step", "because", "therefore",
            "this means", "in other words", "for instance"
        ]
        
        response_lower = action.response_text.lower()
        educational_count = sum(1 for indicator in educational_indicators if indicator in response_lower)
        
        if educational_count > 0:
            learning_score = min(1.0, 0.5 + (educational_count * 0.1))
        
        # Bonus for task completion
        for feedback in feedback_list:
            if feedback.engagement_metrics and feedback.engagement_metrics.task_completion:
                learning_score = min(1.0, learning_score + 0.2)
        
        return learning_score
    
    async def _calculate_personalization_reward(
        self,
        conversation_state: ConversationState,
        action: Action
    ) -> float:
        """Calculate personalization component of reward."""
        
        # Basic personalization score based on context usage
        personalization_score = 0.5
        
        # Check if response references user's previous questions or context
        if len(conversation_state.conversation_history) > 1:
            recent_user_inputs = [
                turn.user_input.lower() 
                for turn in conversation_state.conversation_history[-3:]
            ]
            
            response_lower = action.response_text.lower()
            
            # Check for references to previous context
            context_references = ["as you mentioned", "following up on", "building on"]
            for ref in context_references:
                if ref in response_lower:
                    personalization_score = min(1.0, personalization_score + 0.2)
        
        # Check for domain-specific adaptation
        if conversation_state.domain_context:
            domain_keywords = conversation_state.domain_context.lower().split()
            response_lower = action.response_text.lower()
            
            domain_matches = sum(1 for keyword in domain_keywords if keyword in response_lower)
            if domain_matches > 0:
                personalization_score = min(1.0, personalization_score + 0.1)
        
        return personalization_score
    
    async def _calculate_efficiency_reward(
        self,
        conversation_state: ConversationState,
        action: Action
    ) -> float:
        """Calculate efficiency component of reward."""
        
        # Base efficiency on response length vs information density
        response_length = len(action.response_text)
        
        if response_length == 0:
            return 0.0
        
        # Optimal response length range
        optimal_min = 50
        optimal_max = 500
        
        if optimal_min <= response_length <= optimal_max:
            efficiency_score = 1.0
        elif response_length < optimal_min:
            efficiency_score = response_length / optimal_min
        else:
            # Penalize overly long responses
            efficiency_score = max(0.3, optimal_max / response_length)
        
        return efficiency_score
    
    async def _calculate_creativity_reward(
        self,
        conversation_state: ConversationState,
        action: Action
    ) -> float:
        """Calculate creativity component of reward."""
        
        creativity_score = 0.5  # Default neutral
        
        # Check for creative elements
        creative_indicators = [
            "analogy", "metaphor", "imagine", "think of it as", "like",
            "creative", "innovative", "unique approach"
        ]
        
        response_lower = action.response_text.lower()
        creative_count = sum(1 for indicator in creative_indicators if indicator in response_lower)
        
        if creative_count > 0:
            creativity_score = min(1.0, 0.5 + (creative_count * 0.15))
        
        # Bonus for providing multiple approaches or alternatives
        alternative_indicators = ["alternatively", "another way", "you could also", "option"]
        alternative_count = sum(1 for indicator in alternative_indicators if indicator in response_lower)
        
        if alternative_count > 0:
            creativity_score = min(1.0, creativity_score + 0.1)
        
        return creativity_score


class MultiObjectiveRewardCalculator(RewardCalculator):
    """Advanced multi-objective reward calculator with adaptive weighting."""
    
    def __init__(self, config: RLConfig):
        super().__init__(config)
        self.adaptive_weights = True
        self.weight_adaptation_rate = 0.01
        self.performance_history: Dict[str, List[float]] = {}
    
    async def calculate_adaptive_reward(
        self,
        conversation_state: ConversationState,
        action: Action,
        feedback_list: List[UserFeedback],
        quality_metrics: Optional[QualityMetrics] = None,
        user_preferences: Optional[Dict[str, float]] = None
    ) -> MultiObjectiveReward:
        """Calculate reward with adaptive weighting based on user preferences and performance."""
        
        # Calculate base reward
        reward = await self.calculate_reward(
            conversation_state, action, feedback_list, quality_metrics
        )
        
        # Adapt weights based on user preferences
        if user_preferences and self.adaptive_weights:
            adapted_weights = self._adapt_weights_to_preferences(
                reward.weights, user_preferences
            )
            reward.weights = adapted_weights
            reward.calculate_total_reward()  # Recalculate with new weights
        
        # Update performance history
        self._update_performance_history(reward)
        
        return reward
    
    def _adapt_weights_to_preferences(
        self,
        current_weights: RewardWeights,
        user_preferences: Dict[str, float]
    ) -> RewardWeights:
        """Adapt reward weights based on user preferences."""
        
        # Create new weights based on preferences
        adapted_weights = RewardWeights(
            helpfulness=current_weights.helpfulness,
            accuracy=current_weights.accuracy,
            engagement=current_weights.engagement,
            safety=current_weights.safety,
            learning_effectiveness=current_weights.learning_effectiveness,
            personalization=current_weights.personalization,
            efficiency=current_weights.efficiency,
            creativity=current_weights.creativity
        )
        
        # Adjust weights based on preferences
        for component, preference in user_preferences.items():
            if hasattr(adapted_weights, component):
                current_value = getattr(adapted_weights, component)
                # Gradually adapt towards preference
                new_value = current_value + (preference - current_value) * self.weight_adaptation_rate
                setattr(adapted_weights, component, new_value)
        
        # Normalize weights
        return adapted_weights.normalize()
    
    def _update_performance_history(self, reward: MultiObjectiveReward) -> None:
        """Update performance history for analysis."""
        
        components = reward.get_component_breakdown()
        
        for component, value in components.items():
            if component not in self.performance_history:
                self.performance_history[component] = []
            
            self.performance_history[component].append(value)
            
            # Keep only recent history
            if len(self.performance_history[component]) > 1000:
                self.performance_history[component] = self.performance_history[component][-500:]
    
    def get_performance_trends(self) -> Dict[str, float]:
        """Get performance trends for each reward component."""
        
        trends = {}
        
        for component, history in self.performance_history.items():
            if len(history) < 10:
                trends[component] = 0.0
                continue
            
            # Calculate trend as difference between recent and older averages
            recent_avg = np.mean(history[-20:])
            older_avg = np.mean(history[-40:-20]) if len(history) >= 40 else np.mean(history[:-20])
            
            trends[component] = recent_avg - older_avg
        
        return trends