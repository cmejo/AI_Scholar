"""
Advanced adaptation algorithms for personalization system.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .personalization_models import (
    DeepPreferenceModel,
    AdaptationStrategy,
    AdaptationStrategyType,
    BehaviorPattern,
    PredictedAction,
    RiskAssessment,
    RiskLevel,
    RollbackCondition
)
from ..models.user_models import UserProfile, PersonalizationContext
from ..models.conversation_models import ConversationState, Action

logger = logging.getLogger(__name__)


class LearningStrategy(Enum):
    """Different learning strategies for adaptation."""
    GRADIENT_DESCENT = "gradient_descent"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    EVOLUTIONARY_ALGORITHM = "evolutionary_algorithm"


@dataclass
class OptimalAction:
    """Optimal action selected by contextual bandit."""
    action_id: str
    action_parameters: Dict[str, Any]
    expected_reward: float
    confidence: float
    exploration_factor: float = 0.1


class DeepPreferenceLearner:
    """Deep learning approach for user preference modeling."""
    
    def __init__(self, embedding_dim: int = 128, learning_rate: float = 0.001):
        self.embedding_dim = embedding_dim
        self.learning_rate = learning_rate
        self.preference_history: List[Dict[str, Any]] = []
        self.model_weights = np.random.randn(embedding_dim, embedding_dim) * 0.01
        
    async def learn_preferences(self, user_interactions: List[Dict[str, Any]]) -> DeepPreferenceModel:
        """Learn deep preferences from user interactions."""
        
        if not user_interactions:
            return self._create_default_model()
        
        # Extract features from interactions
        interaction_features = await self._extract_interaction_features(user_interactions)
        
        # Train preference embeddings
        preference_embeddings = await self._train_embeddings(interaction_features)
        
        # Extract preference weights
        preference_weights = await self._extract_preference_weights(user_interactions)
        
        # Identify temporal patterns
        temporal_preferences = await self._identify_temporal_patterns(user_interactions)
        
        # Calculate contextual modifiers
        contextual_modifiers = await self._calculate_contextual_modifiers(user_interactions)
        
        # Estimate confidence intervals
        confidence_intervals = await self._estimate_confidence_intervals(preference_weights)
        
        return DeepPreferenceModel(
            preference_embeddings=preference_embeddings,
            preference_weights=preference_weights,
            temporal_preferences=temporal_preferences,
            contextual_modifiers=contextual_modifiers,
            confidence_intervals=confidence_intervals
        )
    
    async def _extract_interaction_features(self, interactions: List[Dict[str, Any]]) -> np.ndarray:
        """Extract features from user interactions."""
        features = []
        
        for interaction in interactions:
            # Basic interaction features
            feature_vector = [
                interaction.get('duration', 0.0),
                interaction.get('satisfaction', 0.5),
                interaction.get('engagement', 0.5),
                interaction.get('task_completion', 0.0),
                len(interaction.get('actions', [])),
            ]
            
            # Add contextual features
            context = interaction.get('context', {})
            feature_vector.extend([
                context.get('time_of_day', 12) / 24.0,  # Normalize to [0,1]
                context.get('day_of_week', 3) / 7.0,
                context.get('session_length', 30) / 120.0,  # Normalize assuming max 2 hours
            ])
            
            features.append(feature_vector)
        
        return np.array(features) if features else np.zeros((1, 8))
    
    async def _train_embeddings(self, features: np.ndarray) -> np.ndarray:
        """Train preference embeddings using simple neural network."""
        # Simplified embedding training (in practice, would use proper deep learning)
        
        # Apply PCA-like dimensionality reduction
        if features.shape[0] > 1:
            # Center the data
            centered_features = features - np.mean(features, axis=0)
            
            # Compute covariance matrix
            cov_matrix = np.cov(centered_features.T)
            
            # Eigendecomposition
            eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
            
            # Sort by eigenvalues (descending)
            idx = np.argsort(eigenvalues)[::-1]
            eigenvectors = eigenvectors[:, idx]
            
            # Take top components for embedding
            embedding_components = min(self.embedding_dim, eigenvectors.shape[1])
            embedding_matrix = eigenvectors[:, :embedding_components]
            
            # Project features to embedding space
            embeddings = np.dot(centered_features, embedding_matrix)
            
            # Pad if necessary
            if embeddings.shape[1] < self.embedding_dim:
                padding = np.zeros((embeddings.shape[0], self.embedding_dim - embeddings.shape[1]))
                embeddings = np.hstack([embeddings, padding])
            
            # Return mean embedding
            return np.mean(embeddings, axis=0)
        else:
            return np.random.randn(self.embedding_dim) * 0.1
    
    async def _extract_preference_weights(self, interactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extract preference weights from interactions."""
        preference_weights = {}
        
        # Analyze interaction patterns
        total_interactions = len(interactions)
        if total_interactions == 0:
            return {"default": 0.5}
        
        # Calculate preferences based on interaction outcomes
        satisfaction_sum = sum(interaction.get('satisfaction', 0.5) for interaction in interactions)
        engagement_sum = sum(interaction.get('engagement', 0.5) for interaction in interactions)
        
        preference_weights.update({
            "response_length": self._calculate_length_preference(interactions),
            "technical_detail": self._calculate_technical_preference(interactions),
            "interaction_style": self._calculate_style_preference(interactions),
            "content_type": self._calculate_content_preference(interactions),
            "explanation_depth": satisfaction_sum / total_interactions,
            "engagement_level": engagement_sum / total_interactions,
        })
        
        return preference_weights
    
    def _calculate_length_preference(self, interactions: List[Dict[str, Any]]) -> float:
        """Calculate preference for response length."""
        length_satisfaction = []
        
        for interaction in interactions:
            response_length = interaction.get('response_length', 100)
            satisfaction = interaction.get('satisfaction', 0.5)
            
            # Normalize length (assuming 50-500 character range)
            normalized_length = min(1.0, max(0.0, (response_length - 50) / 450))
            length_satisfaction.append((normalized_length, satisfaction))
        
        if not length_satisfaction:
            return 0.5
        
        # Find length that correlates with highest satisfaction
        best_length = 0.5
        best_satisfaction = 0.0
        
        for length, satisfaction in length_satisfaction:
            if satisfaction > best_satisfaction:
                best_satisfaction = satisfaction
                best_length = length
        
        return best_length
    
    def _calculate_technical_preference(self, interactions: List[Dict[str, Any]]) -> float:
        """Calculate preference for technical detail level."""
        technical_scores = []
        
        for interaction in interactions:
            technical_level = interaction.get('technical_level', 0.5)
            satisfaction = interaction.get('satisfaction', 0.5)
            technical_scores.append(technical_level * satisfaction)
        
        return np.mean(technical_scores) if technical_scores else 0.5
    
    def _calculate_style_preference(self, interactions: List[Dict[str, Any]]) -> float:
        """Calculate preference for interaction style."""
        style_scores = []
        
        for interaction in interactions:
            # Analyze style indicators
            formality = interaction.get('formality', 0.5)
            friendliness = interaction.get('friendliness', 0.5)
            satisfaction = interaction.get('satisfaction', 0.5)
            
            # Combine style factors
            style_score = (formality + friendliness) / 2
            style_scores.append(style_score * satisfaction)
        
        return np.mean(style_scores) if style_scores else 0.5
    
    def _calculate_content_preference(self, interactions: List[Dict[str, Any]]) -> float:
        """Calculate preference for content type."""
        content_scores = []
        
        for interaction in interactions:
            content_types = interaction.get('content_types', [])
            satisfaction = interaction.get('satisfaction', 0.5)
            
            # Score based on content diversity and satisfaction
            diversity_score = len(set(content_types)) / max(1, len(content_types))
            content_scores.append(diversity_score * satisfaction)
        
        return np.mean(content_scores) if content_scores else 0.5
    
    async def _identify_temporal_patterns(self, interactions: List[Dict[str, Any]]) -> List:
        """Identify temporal preference patterns."""
        from .personalization_models import TemporalPreference
        
        temporal_preferences = []
        
        # Group interactions by time periods
        time_groups = {
            "morning": [],
            "afternoon": [],
            "evening": [],
            "weekend": []
        }
        
        for interaction in interactions:
            timestamp = interaction.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                
                hour = timestamp.hour
                weekday = timestamp.weekday()
                
                if weekday >= 5:
                    time_groups["weekend"].append(interaction)
                elif hour < 12:
                    time_groups["morning"].append(interaction)
                elif hour < 18:
                    time_groups["afternoon"].append(interaction)
                else:
                    time_groups["evening"].append(interaction)
        
        # Analyze preferences for each time period
        for period, period_interactions in time_groups.items():
            if len(period_interactions) >= 3:  # Minimum for pattern
                avg_satisfaction = np.mean([
                    interaction.get('satisfaction', 0.5) 
                    for interaction in period_interactions
                ])
                
                confidence = min(1.0, len(period_interactions) / 10.0)
                
                temporal_pref = TemporalPreference(
                    preference_key="satisfaction",
                    time_period=period,
                    preference_value=avg_satisfaction,
                    confidence=confidence
                )
                temporal_preferences.append(temporal_pref)
        
        return temporal_preferences
    
    async def _calculate_contextual_modifiers(self, interactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate contextual modifiers for preferences."""
        modifiers = {}
        
        # Analyze context impact on satisfaction
        context_impacts = {}
        
        for interaction in interactions:
            context = interaction.get('context', {})
            satisfaction = interaction.get('satisfaction', 0.5)
            
            for context_key, context_value in context.items():
                if context_key not in context_impacts:
                    context_impacts[context_key] = []
                
                # Normalize context value if numeric
                if isinstance(context_value, (int, float)):
                    normalized_value = min(1.0, max(0.0, context_value))
                else:
                    normalized_value = 1.0 if context_value else 0.0
                
                context_impacts[context_key].append((normalized_value, satisfaction))
        
        # Calculate modifiers based on correlation with satisfaction
        for context_key, impact_data in context_impacts.items():
            if len(impact_data) >= 3:
                values, satisfactions = zip(*impact_data)
                correlation = np.corrcoef(values, satisfactions)[0, 1]
                
                if not np.isnan(correlation):
                    modifiers[context_key] = correlation * 0.5  # Scale modifier
        
        return modifiers
    
    async def _estimate_confidence_intervals(self, preference_weights: Dict[str, float]) -> Dict[str, Tuple[float, float]]:
        """Estimate confidence intervals for preferences."""
        confidence_intervals = {}
        
        for key, value in preference_weights.items():
            # Simple confidence interval based on value
            # In practice, would use proper statistical methods
            uncertainty = 0.1  # Base uncertainty
            
            # Higher uncertainty for extreme values
            if value < 0.2 or value > 0.8:
                uncertainty = 0.15
            
            lower_bound = max(0.0, value - uncertainty)
            upper_bound = min(1.0, value + uncertainty)
            
            confidence_intervals[key] = (lower_bound, upper_bound)
        
        return confidence_intervals
    
    def _create_default_model(self) -> DeepPreferenceModel:
        """Create default preference model when no data available."""
        return DeepPreferenceModel(
            preference_embeddings=np.random.randn(self.embedding_dim) * 0.1,
            preference_weights={
                "response_length": 0.5,
                "technical_detail": 0.5,
                "interaction_style": 0.5,
                "content_type": 0.5,
                "explanation_depth": 0.5,
                "engagement_level": 0.5
            },
            temporal_preferences=[],
            contextual_modifiers={},
            confidence_intervals={
                key: (0.3, 0.7) for key in [
                    "response_length", "technical_detail", "interaction_style",
                    "content_type", "explanation_depth", "engagement_level"
                ]
            }
        )

cla
ss ContextualBanditOptimizer:
    """Contextual bandit algorithm for action selection."""
    
    def __init__(self, num_arms: int = 10, exploration_rate: float = 0.1):
        self.num_arms = num_arms
        self.exploration_rate = exploration_rate
        self.arm_rewards: Dict[str, List[float]] = {}
        self.arm_contexts: Dict[str, List[np.ndarray]] = {}
        self.context_weights = np.random.randn(10) * 0.1  # Context feature weights
        
    async def select_optimal_action(
        self, 
        context: Dict[str, Any], 
        available_actions: List[Dict[str, Any]]
    ) -> OptimalAction:
        """Select optimal action using contextual bandit algorithm."""
        
        if not available_actions:
            raise ValueError("No available actions provided")
        
        context_vector = await self._vectorize_context(context)
        
        # Calculate expected rewards for each action
        action_scores = []
        
        for action in available_actions:
            action_id = action.get('id', str(len(action_scores)))
            
            # Get historical performance
            if action_id in self.arm_rewards and self.arm_rewards[action_id]:
                # Use contextual information to predict reward
                expected_reward = await self._predict_contextual_reward(
                    action_id, context_vector
                )
                confidence = min(1.0, len(self.arm_rewards[action_id]) / 10.0)
            else:
                # No history, use optimistic initialization
                expected_reward = 0.7  # Optimistic default
                confidence = 0.1
            
            # Add exploration bonus (Upper Confidence Bound)
            exploration_bonus = self.exploration_rate * np.sqrt(
                np.log(max(1, sum(len(rewards) for rewards in self.arm_rewards.values()))) /
                max(1, len(self.arm_rewards.get(action_id, [1])))
            )
            
            total_score = expected_reward + exploration_bonus
            
            action_scores.append({
                'action': action,
                'action_id': action_id,
                'expected_reward': expected_reward,
                'confidence': confidence,
                'exploration_factor': exploration_bonus,
                'total_score': total_score
            })
        
        # Select action with highest score
        best_action = max(action_scores, key=lambda x: x['total_score'])
        
        return OptimalAction(
            action_id=best_action['action_id'],
            action_parameters=best_action['action'],
            expected_reward=best_action['expected_reward'],
            confidence=best_action['confidence'],
            exploration_factor=best_action['exploration_factor']
        )
    
    async def update_reward(self, action_id: str, context: Dict[str, Any], reward: float):
        """Update reward information for an action."""
        if action_id not in self.arm_rewards:
            self.arm_rewards[action_id] = []
            self.arm_contexts[action_id] = []
        
        self.arm_rewards[action_id].append(reward)
        
        context_vector = await self._vectorize_context(context)
        self.arm_contexts[action_id].append(context_vector)
        
        # Update context weights using simple gradient descent
        await self._update_context_weights(action_id, context_vector, reward)
    
    async def _vectorize_context(self, context: Dict[str, Any]) -> np.ndarray:
        """Convert context dictionary to feature vector."""
        features = []
        
        # Standard context features
        features.extend([
            context.get('time_of_day', 12) / 24.0,
            context.get('day_of_week', 3) / 7.0,
            context.get('user_satisfaction', 0.5),
            context.get('session_length', 30) / 120.0,
            context.get('task_complexity', 0.5),
            context.get('user_expertise', 0.5),
            context.get('interaction_count', 5) / 20.0,
            context.get('response_time', 1.0) / 5.0,
            len(context.get('recent_actions', [])) / 10.0,
            context.get('engagement_score', 0.5)
        ])
        
        return np.array(features)
    
    async def _predict_contextual_reward(self, action_id: str, context_vector: np.ndarray) -> float:
        """Predict reward for action given context."""
        if action_id not in self.arm_contexts or not self.arm_contexts[action_id]:
            return 0.5  # Default prediction
        
        # Simple linear model: reward = context · weights
        base_reward = np.dot(context_vector, self.context_weights)
        
        # Add historical average
        historical_avg = np.mean(self.arm_rewards[action_id])
        
        # Combine predictions
        predicted_reward = 0.6 * historical_avg + 0.4 * base_reward
        
        # Ensure valid range
        return max(0.0, min(1.0, predicted_reward))
    
    async def _update_context_weights(self, action_id: str, context_vector: np.ndarray, reward: float):
        """Update context weights using gradient descent."""
        if len(self.arm_contexts[action_id]) < 2:
            return
        
        # Predict reward with current weights
        predicted_reward = np.dot(context_vector, self.context_weights)
        
        # Calculate error
        error = reward - predicted_reward
        
        # Update weights (simple gradient descent)
        learning_rate = 0.01
        self.context_weights += learning_rate * error * context_vector
        
        # Clip weights to reasonable range
        self.context_weights = np.clip(self.context_weights, -1.0, 1.0)


class MetaLearningAdapter:
    """Meta-learning approach for cross-user adaptation."""
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
        self.user_profiles: Dict[str, Dict[str, Any]] = {}
        self.adaptation_history: Dict[str, List[Dict[str, Any]]] = {}
        
    async def adapt_from_similar_users(
        self, 
        target_user_profile: Dict[str, Any], 
        similar_users: List[Dict[str, Any]]
    ) -> AdaptationStrategy:
        """Create adaptation strategy based on similar users."""
        
        if not similar_users:
            return await self._create_default_strategy()
        
        # Find most similar users
        similarities = []
        for user in similar_users:
            similarity = await self._calculate_user_similarity(target_user_profile, user)
            if similarity >= self.similarity_threshold:
                similarities.append((similarity, user))
        
        if not similarities:
            return await self._create_default_strategy()
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        # Extract successful adaptations from similar users
        successful_adaptations = await self._extract_successful_adaptations(similarities)
        
        # Create meta-learned strategy
        strategy = await self._create_meta_strategy(
            target_user_profile, successful_adaptations
        )
        
        return strategy
    
    async def _calculate_user_similarity(
        self, 
        user1: Dict[str, Any], 
        user2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between two user profiles."""
        
        # Extract comparable features
        features1 = await self._extract_user_features(user1)
        features2 = await self._extract_user_features(user2)
        
        # Calculate cosine similarity
        dot_product = np.dot(features1, features2)
        norm1 = np.linalg.norm(features1)
        norm2 = np.linalg.norm(features2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return max(0.0, similarity)  # Ensure non-negative
    
    async def _extract_user_features(self, user_profile: Dict[str, Any]) -> np.ndarray:
        """Extract feature vector from user profile."""
        features = []
        
        # Demographic features
        features.extend([
            user_profile.get('age', 30) / 100.0,
            user_profile.get('experience_level', 0.5),
            user_profile.get('domain_expertise', 0.5),
            user_profile.get('technical_background', 0.5)
        ])
        
        # Behavioral features
        features.extend([
            user_profile.get('avg_session_length', 30) / 120.0,
            user_profile.get('interaction_frequency', 5) / 20.0,
            user_profile.get('task_completion_rate', 0.7),
            user_profile.get('satisfaction_score', 0.5)
        ])
        
        # Preference features
        preferences = user_profile.get('preferences', {})
        features.extend([
            preferences.get('response_length', 0.5),
            preferences.get('technical_detail', 0.5),
            preferences.get('interaction_style', 0.5),
            preferences.get('explanation_depth', 0.5)
        ])
        
        return np.array(features)
    
    async def _extract_successful_adaptations(
        self, 
        similar_users: List[Tuple[float, Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Extract successful adaptations from similar users."""
        successful_adaptations = []
        
        for similarity, user in similar_users:
            user_id = user.get('user_id')
            if user_id in self.adaptation_history:
                # Filter for successful adaptations
                for adaptation in self.adaptation_history[user_id]:
                    if adaptation.get('success_score', 0.0) > 0.6:
                        # Weight by user similarity
                        weighted_adaptation = adaptation.copy()
                        weighted_adaptation['similarity_weight'] = similarity
                        successful_adaptations.append(weighted_adaptation)
        
        return successful_adaptations
    
    async def _create_meta_strategy(
        self, 
        target_user: Dict[str, Any], 
        successful_adaptations: List[Dict[str, Any]]
    ) -> AdaptationStrategy:
        """Create meta-learning based adaptation strategy."""
        
        if not successful_adaptations:
            return await self._create_default_strategy()
        
        # Aggregate successful strategies
        strategy_types = {}
        parameters = {}
        expected_improvements = []
        
        for adaptation in successful_adaptations:
            strategy_type = adaptation.get('strategy_type', 'gradual_adjustment')
            weight = adaptation.get('similarity_weight', 1.0)
            
            # Count strategy types (weighted)
            if strategy_type not in strategy_types:
                strategy_types[strategy_type] = 0
            strategy_types[strategy_type] += weight
            
            # Aggregate parameters
            for param_key, param_value in adaptation.get('parameters', {}).items():
                if param_key not in parameters:
                    parameters[param_key] = []
                parameters[param_key].append((param_value, weight))
            
            # Collect improvements
            improvement = adaptation.get('improvement', 0.0) * weight
            expected_improvements.append(improvement)
        
        # Select most common strategy type
        best_strategy_type = max(strategy_types.items(), key=lambda x: x[1])[0]
        
        # Average parameters (weighted)
        averaged_parameters = {}
        for param_key, param_values in parameters.items():
            weighted_sum = sum(value * weight for value, weight in param_values)
            total_weight = sum(weight for _, weight in param_values)
            averaged_parameters[param_key] = weighted_sum / total_weight if total_weight > 0 else 0.5
        
        # Calculate expected improvement
        expected_improvement = np.mean(expected_improvements) if expected_improvements else 0.3
        
        # Create risk assessment
        risk_assessment = RiskAssessment(
            risk_level=RiskLevel.MEDIUM,
            risk_factors=["meta_learning_uncertainty", "user_similarity_assumption"],
            mitigation_strategies=["gradual_rollout", "continuous_monitoring"],
            rollback_probability=0.2,
            impact_assessment={"satisfaction": expected_improvement}
        )
        
        # Create rollback conditions
        rollback_conditions = [
            RollbackCondition(
                condition_name="satisfaction_drop",
                metric_threshold=0.4,
                time_window=300,  # 5 minutes
                consecutive_failures=3
            )
        ]
        
        return AdaptationStrategy(
            strategy_id=f"meta_learned_{datetime.now().timestamp()}",
            strategy_type=AdaptationStrategyType(best_strategy_type),
            parameters=averaged_parameters,
            expected_improvement=expected_improvement,
            risk_assessment=risk_assessment,
            rollback_conditions=rollback_conditions,
            implementation_steps=[
                "analyze_target_user_context",
                "apply_meta_learned_parameters",
                "monitor_adaptation_performance",
                "adjust_based_on_feedback"
            ],
            success_metrics=["satisfaction_improvement", "engagement_increase", "task_completion_rate"]
        )
    
    async def _create_default_strategy(self) -> AdaptationStrategy:
        """Create default adaptation strategy when no similar users found."""
        
        risk_assessment = RiskAssessment(
            risk_level=RiskLevel.LOW,
            risk_factors=["no_historical_data"],
            mitigation_strategies=["conservative_changes", "frequent_monitoring"],
            rollback_probability=0.1,
            impact_assessment={"satisfaction": 0.2}
        )
        
        rollback_conditions = [
            RollbackCondition(
                condition_name="satisfaction_drop",
                metric_threshold=0.3,
                time_window=600,
                consecutive_failures=2
            )
        ]
        
        return AdaptationStrategy(
            strategy_id=f"default_{datetime.now().timestamp()}",
            strategy_type=AdaptationStrategyType.CONSERVATIVE_CHANGE,
            parameters={
                "adjustment_rate": 0.1,
                "exploration_factor": 0.05,
                "personalization_strength": 0.3
            },
            expected_improvement=0.2,
            risk_assessment=risk_assessment,
            rollback_conditions=rollback_conditions,
            implementation_steps=[
                "establish_baseline_metrics",
                "apply_conservative_changes",
                "monitor_user_response",
                "gradually_increase_personalization"
            ],
            success_metrics=["user_retention", "basic_satisfaction"]
        )
    
    def record_adaptation_outcome(
        self, 
        user_id: str, 
        strategy: AdaptationStrategy, 
        outcome: Dict[str, Any]
    ):
        """Record outcome of adaptation for future meta-learning."""
        if user_id not in self.adaptation_history:
            self.adaptation_history[user_id] = []
        
        adaptation_record = {
            'strategy_type': strategy.strategy_type.value,
            'parameters': strategy.parameters,
            'expected_improvement': strategy.expected_improvement,
            'actual_improvement': outcome.get('improvement', 0.0),
            'success_score': outcome.get('success_score', 0.0),
            'timestamp': datetime.now(),
            'outcome_metrics': outcome
        }
        
        self.adaptation_history[user_id].append(adaptation_record)
        
        # Keep only recent history (last 50 adaptations per user)
        if len(self.adaptation_history[user_id]) > 50:
            self.adaptation_history[user_id] = self.adaptation_history[user_id][-25:]


class AdvancedAdaptationAlgorithms:
    """Main class coordinating all advanced adaptation algorithms."""
    
    def __init__(self):
        self.deep_preference_learner = DeepPreferenceLearner()
        self.contextual_bandit = ContextualBanditOptimizer()
        self.meta_learner = MetaLearningAdapter()
        
    async def deep_preference_learning(
        self, 
        user_interactions: List[Dict[str, Any]]
    ) -> DeepPreferenceModel:
        """Perform deep preference learning."""
        return await self.deep_preference_learner.learn_preferences(user_interactions)
    
    async def contextual_bandit_optimization(
        self, 
        context: Dict[str, Any], 
        available_actions: List[Dict[str, Any]]
    ) -> OptimalAction:
        """Perform contextual bandit optimization."""
        return await self.contextual_bandit.select_optimal_action(context, available_actions)
    
    async def meta_learning_adaptation(
        self, 
        user_profile: Dict[str, Any], 
        similar_users: List[Dict[str, Any]]
    ) -> AdaptationStrategy:
        """Perform meta-learning adaptation."""
        return await self.meta_learner.adapt_from_similar_users(user_profile, similar_users)
    
    async def update_bandit_reward(self, action_id: str, context: Dict[str, Any], reward: float):
        """Update contextual bandit with reward feedback."""
        await self.contextual_bandit.update_reward(action_id, context, reward)
    
    def record_adaptation_outcome(
        self, 
        user_id: str, 
        strategy: AdaptationStrategy, 
        outcome: Dict[str, Any]
    ):
        """Record adaptation outcome for meta-learning."""
        self.meta_learner.record_adaptation_outcome(user_id, strategy, outcome)