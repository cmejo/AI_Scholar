"""Extended reward system for multi-modal feedback and workflow efficiency."""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
import json

from ..models.feedback_models import FeedbackData
from ..multimodal.models import MultiModalFeatures, VisualElement
from ..research_assistant.workflow_optimizer import Workflow, WorkflowStep, EfficiencyMetrics

logger = logging.getLogger(__name__)


class RewardType(Enum):
    """Types of rewards in the extended system."""
    TRADITIONAL = "traditional"
    MULTI_MODAL = "multi_modal"
    WORKFLOW_EFFICIENCY = "workflow_efficiency"
    VISUAL_ENGAGEMENT = "visual_engagement"
    RESEARCH_PRODUCTIVITY = "research_productivity"
    PERSONALIZATION_ACCURACY = "personalization_accuracy"


class EngagementLevel(Enum):
    """Levels of user engagement."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    EXCEPTIONAL = 4


@dataclass
class MultiModalReward:
    """Reward based on multi-modal content interaction."""
    reward_id: str
    user_id: str
    content_type: str
    visual_elements: List[VisualElement]
    engagement_score: float
    comprehension_score: float
    interaction_duration: float
    visual_attention_score: float
    cross_modal_coherence: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowEfficiencyReward:
    """Reward based on workflow efficiency metrics."""
    reward_id: str
    user_id: str
    workflow_id: str
    efficiency_metrics: EfficiencyMetrics
    improvement_score: float
    productivity_gain: float
    time_savings: float
    satisfaction_improvement: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VisualEngagementReward:
    """Reward based on visual content engagement."""
    reward_id: str
    user_id: str
    visual_content_id: str
    engagement_level: EngagementLevel
    interaction_quality: float
    visual_comprehension: float
    attention_distribution: Dict[str, float]
    learning_effectiveness: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchProductivityReward:
    """Reward based on research productivity metrics."""
    reward_id: str
    user_id: str
    session_id: str
    tasks_completed: int
    quality_score: float
    efficiency_score: float
    knowledge_gain: float
    research_progress: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PersonalizationAccuracyReward:
    """Reward based on personalization accuracy."""
    reward_id: str
    user_id: str
    prediction_accuracy: float
    preference_alignment: float
    adaptation_effectiveness: float
    user_satisfaction_delta: float
    behavioral_prediction_score: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtendedRewardCalculation:
    """Result of extended reward calculation."""
    total_reward: float
    reward_breakdown: Dict[RewardType, float]
    confidence_score: float
    explanation: str
    contributing_factors: List[str]
    improvement_suggestions: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExtendedRewardCalculator:
    """Extended reward calculator for multi-modal and workflow-based rewards."""
    
    def __init__(self):
        self.reward_weights = {
            RewardType.TRADITIONAL: 0.3,
            RewardType.MULTI_MODAL: 0.2,
            RewardType.WORKFLOW_EFFICIENCY: 0.2,
            RewardType.VISUAL_ENGAGEMENT: 0.1,
            RewardType.RESEARCH_PRODUCTIVITY: 0.15,
            RewardType.PERSONALIZATION_ACCURACY: 0.05
        }
        
        self.reward_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.baseline_metrics: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.user_preferences: Dict[str, Dict[str, float]] = defaultdict(dict)
    
    async def calculate_extended_reward(self, user_id: str, 
                                      traditional_feedback: Optional[FeedbackData] = None,
                                      multi_modal_features: Optional[MultiModalFeatures] = None,
                                      workflow_metrics: Optional[EfficiencyMetrics] = None,
                                      visual_engagement: Optional[Dict[str, Any]] = None,
                                      research_session: Optional[Dict[str, Any]] = None,
                                      personalization_data: Optional[Dict[str, Any]] = None) -> ExtendedRewardCalculation:
        """Calculate extended reward incorporating all feedback types."""
        try:
            reward_components = {}
            contributing_factors = []
            improvement_suggestions = []
            
            # Traditional reward component
            if traditional_feedback:
                traditional_reward = await self._calculate_traditional_reward(traditional_feedback)
                reward_components[RewardType.TRADITIONAL] = traditional_reward
                contributing_factors.append(f"Traditional feedback: {traditional_reward:.3f}")
            
            # Multi-modal reward component
            if multi_modal_features:
                multi_modal_reward = await self._calculate_multi_modal_reward(
                    user_id, multi_modal_features, visual_engagement
                )
                reward_components[RewardType.MULTI_MODAL] = multi_modal_reward
                contributing_factors.append(f"Multi-modal engagement: {multi_modal_reward:.3f}")
            
            # Workflow efficiency reward component
            if workflow_metrics:
                workflow_reward = await self._calculate_workflow_efficiency_reward(
                    user_id, workflow_metrics
                )
                reward_components[RewardType.WORKFLOW_EFFICIENCY] = workflow_reward
                contributing_factors.append(f"Workflow efficiency: {workflow_reward:.3f}")
            
            # Visual engagement reward component
            if visual_engagement:
                visual_reward = await self._calculate_visual_engagement_reward(
                    user_id, visual_engagement
                )
                reward_components[RewardType.VISUAL_ENGAGEMENT] = visual_reward
                contributing_factors.append(f"Visual engagement: {visual_reward:.3f}")
            
            # Research productivity reward component
            if research_session:
                productivity_reward = await self._calculate_research_productivity_reward(
                    user_id, research_session
                )
                reward_components[RewardType.RESEARCH_PRODUCTIVITY] = productivity_reward
                contributing_factors.append(f"Research productivity: {productivity_reward:.3f}")
            
            # Personalization accuracy reward component
            if personalization_data:
                personalization_reward = await self._calculate_personalization_accuracy_reward(
                    user_id, personalization_data
                )
                reward_components[RewardType.PERSONALIZATION_ACCURACY] = personalization_reward
                contributing_factors.append(f"Personalization accuracy: {personalization_reward:.3f}")
            
            # Calculate weighted total reward
            total_reward = 0.0
            total_weight = 0.0
            
            for reward_type, reward_value in reward_components.items():
                weight = self.reward_weights[reward_type]
                total_reward += weight * reward_value
                total_weight += weight
            
            # Normalize by actual weights used
            if total_weight > 0:
                total_reward /= total_weight
            
            # Calculate confidence score
            confidence_score = await self._calculate_confidence_score(reward_components)
            
            # Generate improvement suggestions
            improvement_suggestions = await self._generate_improvement_suggestions(
                user_id, reward_components
            )
            
            # Create explanation
            explanation = await self._generate_reward_explanation(reward_components, total_reward)
            
            # Store reward history
            await self._store_reward_history(user_id, reward_components, total_reward)
            
            result = ExtendedRewardCalculation(
                total_reward=total_reward,
                reward_breakdown=reward_components,
                confidence_score=confidence_score,
                explanation=explanation,
                contributing_factors=contributing_factors,
                improvement_suggestions=improvement_suggestions,
                metadata={
                    'calculation_timestamp': datetime.now().isoformat(),
                    'components_count': len(reward_components),
                    'total_weight_used': total_weight
                }
            )
            
            logger.info(f"Calculated extended reward for user {user_id}: {total_reward:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating extended reward: {str(e)}")
            return ExtendedRewardCalculation(
                total_reward=0.0,
                reward_breakdown={},
                confidence_score=0.0,
                explanation="Error in reward calculation",
                contributing_factors=[],
                improvement_suggestions=[]
            )
    
    async def _calculate_traditional_reward(self, feedback: FeedbackData) -> float:
        """Calculate traditional reward from feedback data."""
        if not feedback:
            return 0.0
        
        # Simple traditional reward calculation
        base_reward = 0.0
        
        # Explicit rating
        if hasattr(feedback, 'rating') and feedback.rating is not None:
            base_reward += feedback.rating / 5.0  # Normalize to 0-1
        
        # Implicit signals
        if hasattr(feedback, 'interaction_time') and feedback.interaction_time:
            # Longer interaction time indicates engagement (up to a point)
            normalized_time = min(1.0, feedback.interaction_time / 300.0)  # 5 minutes max
            base_reward += 0.3 * normalized_time
        
        # Click-through or engagement signals
        if hasattr(feedback, 'clicked') and feedback.clicked:
            base_reward += 0.2
        
        # Completion signals
        if hasattr(feedback, 'completed') and feedback.completed:
            base_reward += 0.3
        
        return min(1.0, base_reward)
    
    async def _calculate_multi_modal_reward(self, user_id: str, 
                                          multi_modal_features: MultiModalFeatures,
                                          visual_engagement: Optional[Dict[str, Any]]) -> float:
        """Calculate reward based on multi-modal content interaction."""
        if not multi_modal_features:
            return 0.0
        
        reward = 0.0
        
        # Visual element engagement
        if multi_modal_features.visual_elements:
            visual_reward = 0.0
            for element in multi_modal_features.visual_elements:
                # Reward based on element complexity and user interaction
                complexity_score = getattr(element, 'complexity_score', 0.5)
                visual_reward += complexity_score * 0.2
            
            # Normalize by number of elements
            visual_reward /= len(multi_modal_features.visual_elements)
            reward += visual_reward
        
        # Cross-modal coherence reward
        if hasattr(multi_modal_features, 'cross_modal_coherence'):
            coherence_score = multi_modal_features.cross_modal_coherence
            reward += 0.3 * coherence_score
        
        # Visual engagement metrics
        if visual_engagement:
            engagement_score = visual_engagement.get('engagement_score', 0.0)
            attention_score = visual_engagement.get('attention_score', 0.0)
            comprehension_score = visual_engagement.get('comprehension_score', 0.0)
            
            reward += 0.2 * engagement_score
            reward += 0.15 * attention_score
            reward += 0.25 * comprehension_score
        
        # Feature integration quality
        if hasattr(multi_modal_features, 'integration_quality'):
            integration_quality = multi_modal_features.integration_quality
            reward += 0.1 * integration_quality
        
        return min(1.0, reward)
    
    async def _calculate_workflow_efficiency_reward(self, user_id: str, 
                                                  metrics: EfficiencyMetrics) -> float:
        """Calculate reward based on workflow efficiency metrics."""
        if not metrics:
            return 0.0
        
        # Get user's baseline metrics for comparison
        baseline = self.baseline_metrics.get(user_id, {})
        
        reward = 0.0
        
        # Time efficiency reward
        time_efficiency = metrics.time_efficiency
        baseline_time = baseline.get('time_efficiency', 0.7)
        time_improvement = max(0, time_efficiency - baseline_time)
        reward += 0.25 * (time_efficiency + 0.5 * time_improvement)
        
        # Resource utilization reward
        resource_efficiency = metrics.resource_utilization
        baseline_resource = baseline.get('resource_utilization', 0.6)
        resource_improvement = max(0, resource_efficiency - baseline_resource)
        reward += 0.2 * (resource_efficiency + 0.5 * resource_improvement)
        
        # Task completion reward
        completion_rate = metrics.task_completion_rate
        baseline_completion = baseline.get('task_completion_rate', 0.8)
        completion_improvement = max(0, completion_rate - baseline_completion)
        reward += 0.25 * (completion_rate + 0.5 * completion_improvement)
        
        # User satisfaction reward
        satisfaction = metrics.user_satisfaction
        baseline_satisfaction = baseline.get('user_satisfaction', 0.7)
        satisfaction_improvement = max(0, satisfaction - baseline_satisfaction)
        reward += 0.2 * (satisfaction + 0.5 * satisfaction_improvement)
        
        # Bottleneck reduction reward (inverse of bottleneck frequency)
        bottleneck_reduction = 1.0 - metrics.bottleneck_frequency
        reward += 0.1 * bottleneck_reduction
        
        # Update baseline metrics (exponential moving average)
        alpha = 0.1  # Learning rate for baseline update
        self.baseline_metrics[user_id]['time_efficiency'] = (
            alpha * time_efficiency + (1 - alpha) * baseline_time
        )
        self.baseline_metrics[user_id]['resource_utilization'] = (
            alpha * resource_efficiency + (1 - alpha) * baseline_resource
        )
        self.baseline_metrics[user_id]['task_completion_rate'] = (
            alpha * completion_rate + (1 - alpha) * baseline_completion
        )
        self.baseline_metrics[user_id]['user_satisfaction'] = (
            alpha * satisfaction + (1 - alpha) * baseline_satisfaction
        )
        
        return min(1.0, reward)
    
    async def _calculate_visual_engagement_reward(self, user_id: str, 
                                                visual_engagement: Dict[str, Any]) -> float:
        """Calculate reward based on visual content engagement."""
        if not visual_engagement:
            return 0.0
        
        reward = 0.0
        
        # Engagement level
        engagement_level = visual_engagement.get('engagement_level', 'medium')
        engagement_scores = {
            'low': 0.2,
            'medium': 0.5,
            'high': 0.8,
            'exceptional': 1.0
        }
        reward += 0.3 * engagement_scores.get(engagement_level, 0.5)
        
        # Interaction quality
        interaction_quality = visual_engagement.get('interaction_quality', 0.5)
        reward += 0.25 * interaction_quality
        
        # Visual comprehension
        visual_comprehension = visual_engagement.get('visual_comprehension', 0.5)
        reward += 0.25 * visual_comprehension
        
        # Attention distribution quality
        attention_distribution = visual_engagement.get('attention_distribution', {})
        if attention_distribution:
            # Reward focused attention on important elements
            important_attention = attention_distribution.get('important_elements', 0.5)
            reward += 0.1 * important_attention
        
        # Learning effectiveness
        learning_effectiveness = visual_engagement.get('learning_effectiveness', 0.5)
        reward += 0.1 * learning_effectiveness
        
        return min(1.0, reward)
    
    async def _calculate_research_productivity_reward(self, user_id: str, 
                                                   research_session: Dict[str, Any]) -> float:
        """Calculate reward based on research productivity metrics."""
        if not research_session:
            return 0.0
        
        reward = 0.0
        
        # Tasks completed
        tasks_completed = research_session.get('tasks_completed', 0)
        expected_tasks = research_session.get('expected_tasks', 5)
        completion_ratio = min(1.0, tasks_completed / expected_tasks) if expected_tasks > 0 else 0.0
        reward += 0.3 * completion_ratio
        
        # Quality score
        quality_score = research_session.get('quality_score', 0.5)
        reward += 0.25 * quality_score
        
        # Efficiency score
        efficiency_score = research_session.get('efficiency_score', 0.5)
        reward += 0.25 * efficiency_score
        
        # Knowledge gain
        knowledge_gain = research_session.get('knowledge_gain', 0.5)
        reward += 0.1 * knowledge_gain
        
        # Research progress
        research_progress = research_session.get('research_progress', 0.5)
        reward += 0.1 * research_progress
        
        return min(1.0, reward)
    
    async def _calculate_personalization_accuracy_reward(self, user_id: str, 
                                                       personalization_data: Dict[str, Any]) -> float:
        """Calculate reward based on personalization accuracy."""
        if not personalization_data:
            return 0.0
        
        reward = 0.0
        
        # Prediction accuracy
        prediction_accuracy = personalization_data.get('prediction_accuracy', 0.5)
        reward += 0.3 * prediction_accuracy
        
        # Preference alignment
        preference_alignment = personalization_data.get('preference_alignment', 0.5)
        reward += 0.25 * preference_alignment
        
        # Adaptation effectiveness
        adaptation_effectiveness = personalization_data.get('adaptation_effectiveness', 0.5)
        reward += 0.25 * adaptation_effectiveness
        
        # User satisfaction delta (improvement)
        satisfaction_delta = personalization_data.get('user_satisfaction_delta', 0.0)
        # Normalize satisfaction delta to 0-1 range
        normalized_delta = max(0.0, min(1.0, (satisfaction_delta + 1.0) / 2.0))
        reward += 0.1 * normalized_delta
        
        # Behavioral prediction score
        behavioral_prediction = personalization_data.get('behavioral_prediction_score', 0.5)
        reward += 0.1 * behavioral_prediction
        
        return min(1.0, reward)
    
    async def _calculate_confidence_score(self, reward_components: Dict[RewardType, float]) -> float:
        """Calculate confidence score for the reward calculation."""
        if not reward_components:
            return 0.0
        
        # Confidence based on number of components and their consistency
        num_components = len(reward_components)
        max_components = len(RewardType)
        
        # Base confidence from component coverage
        coverage_confidence = num_components / max_components
        
        # Consistency confidence (lower variance = higher confidence)
        if num_components > 1:
            rewards = list(reward_components.values())
            variance = np.var(rewards)
            consistency_confidence = max(0.0, 1.0 - variance)
        else:
            consistency_confidence = 0.5  # Moderate confidence with single component
        
        # Combined confidence
        confidence = 0.6 * coverage_confidence + 0.4 * consistency_confidence
        
        return min(1.0, confidence)
    
    async def _generate_improvement_suggestions(self, user_id: str, 
                                              reward_components: Dict[RewardType, float]) -> List[str]:
        """Generate suggestions for improving rewards."""
        suggestions = []
        
        # Analyze low-performing components
        for reward_type, reward_value in reward_components.items():
            if reward_value < 0.5:  # Low performance threshold
                if reward_type == RewardType.MULTI_MODAL:
                    suggestions.append("Increase engagement with visual content and charts")
                elif reward_type == RewardType.WORKFLOW_EFFICIENCY:
                    suggestions.append("Focus on improving task organization and time management")
                elif reward_type == RewardType.VISUAL_ENGAGEMENT:
                    suggestions.append("Spend more time analyzing visual elements in documents")
                elif reward_type == RewardType.RESEARCH_PRODUCTIVITY:
                    suggestions.append("Set clearer research goals and track progress more systematically")
                elif reward_type == RewardType.PERSONALIZATION_ACCURACY:
                    suggestions.append("Provide more explicit feedback to improve personalization")
        
        # Missing components suggestions
        all_types = set(RewardType)
        present_types = set(reward_components.keys())
        missing_types = all_types - present_types
        
        for missing_type in missing_types:
            if missing_type == RewardType.MULTI_MODAL:
                suggestions.append("Try interacting with documents containing charts and diagrams")
            elif missing_type == RewardType.WORKFLOW_EFFICIENCY:
                suggestions.append("Use structured workflows for your research tasks")
            elif missing_type == RewardType.VISUAL_ENGAGEMENT:
                suggestions.append("Engage more with visual content in research materials")
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    async def _generate_reward_explanation(self, reward_components: Dict[RewardType, float], 
                                         total_reward: float) -> str:
        """Generate human-readable explanation of reward calculation."""
        if not reward_components:
            return "No reward components available for calculation."
        
        explanation_parts = [f"Total reward: {total_reward:.3f}"]
        
        # Sort components by contribution
        sorted_components = sorted(reward_components.items(), key=lambda x: x[1], reverse=True)
        
        explanation_parts.append("Component breakdown:")
        for reward_type, value in sorted_components:
            percentage = (value * self.reward_weights[reward_type] / total_reward * 100) if total_reward > 0 else 0
            explanation_parts.append(f"- {reward_type.value}: {value:.3f} ({percentage:.1f}% contribution)")
        
        # Performance assessment
        if total_reward >= 0.8:
            explanation_parts.append("Excellent performance across multiple dimensions!")
        elif total_reward >= 0.6:
            explanation_parts.append("Good performance with room for improvement in some areas.")
        elif total_reward >= 0.4:
            explanation_parts.append("Moderate performance - consider focusing on key improvement areas.")
        else:
            explanation_parts.append("Performance below expectations - review suggestions for improvement.")
        
        return " ".join(explanation_parts)
    
    async def _store_reward_history(self, user_id: str, reward_components: Dict[RewardType, float], 
                                  total_reward: float):
        """Store reward calculation in history for analysis."""
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'total_reward': total_reward,
            'components': {rt.value: reward for rt, reward in reward_components.items()},
            'component_count': len(reward_components)
        }
        
        self.reward_history[user_id].append(history_entry)
        
        # Keep only recent history (last 100 entries)
        if len(self.reward_history[user_id]) > 100:
            self.reward_history[user_id] = self.reward_history[user_id][-100:]
    
    def get_reward_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get analytics on user's reward history."""
        history = self.reward_history.get(user_id, [])
        
        if not history:
            return {"message": "No reward history available"}
        
        # Calculate trends and statistics
        recent_rewards = [entry['total_reward'] for entry in history[-10:]]
        all_rewards = [entry['total_reward'] for entry in history]
        
        # Component analysis
        component_averages = defaultdict(list)
        for entry in history:
            for component, value in entry['components'].items():
                component_averages[component].append(value)
        
        component_stats = {}
        for component, values in component_averages.items():
            component_stats[component] = {
                'average': np.mean(values),
                'trend': np.polyfit(range(len(values)), values, 1)[0] if len(values) > 1 else 0.0,
                'latest': values[-1] if values else 0.0
            }
        
        return {
            'user_id': user_id,
            'total_calculations': len(history),
            'average_reward': np.mean(all_rewards),
            'recent_average': np.mean(recent_rewards),
            'reward_trend': np.polyfit(range(len(all_rewards)), all_rewards, 1)[0] if len(all_rewards) > 1 else 0.0,
            'component_statistics': component_stats,
            'best_reward': max(all_rewards),
            'latest_reward': recent_rewards[-1] if recent_rewards else 0.0
        }
    
    def update_reward_weights(self, new_weights: Dict[RewardType, float]):
        """Update reward component weights."""
        # Normalize weights to sum to 1.0
        total_weight = sum(new_weights.values())
        if total_weight > 0:
            self.reward_weights = {rt: weight / total_weight for rt, weight in new_weights.items()}
            logger.info("Updated reward weights")
        else:
            logger.warning("Invalid reward weights provided - weights must sum to positive value")
    
    def get_current_weights(self) -> Dict[str, float]:
        """Get current reward weights."""
        return {rt.value: weight for rt, weight in self.reward_weights.items()}