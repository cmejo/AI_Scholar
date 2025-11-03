"""
Unit tests for advanced adaptation algorithms.
"""

import pytest
import numpy as np
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from backend.rl.personalization.advanced_algorithms import (
    AdvancedAdaptationAlgorithms,
    DeepPreferenceLearner,
    ContextualBanditOptimizer,
    MetaLearningAdapter,
    OptimalAction
)
from backend.rl.personalization.personalization_models import (
    DeepPreferenceModel,
    AdaptationStrategy,
    AdaptationStrategyType,
    RiskAssessment,
    RiskLevel,
    RollbackCondition
)


class TestDeepPreferenceLearner:
    """Test cases for DeepPreferenceLearner class."""
    
    def create_sample_interactions(self, num_interactions=10):
        """Create sample user interactions for testing."""
        interactions = []
        
        for i in range(num_interactions):
            interaction = {
                'duration': np.random.uniform(30, 300),
                'satisfaction': np.random.uniform(0.3, 0.9),
                'engagement': np.random.uniform(0.4, 0.8),
                'task_completion': np.random.choice([0.0, 1.0]),
                'actions': [f'action_{j}' for j in range(np.random.randint(1, 5))],
                'context': {
                    'time_of_day': np.random.randint(0, 24),
                    'day_of_week': np.random.randint(0, 7),
                    'session_length': np.random.uniform(10, 120)
                },
                'response_length': np.random.randint(50, 500),
                'technical_level': np.random.uniform(0.0, 1.0),
                'formality': np.random.uniform(0.0, 1.0),
                'friendliness': np.random.uniform(0.0, 1.0),
                'content_types': ['text', 'code', 'explanation'][:np.random.randint(1, 4)],
                'timestamp': datetime.now() - timedelta(days=np.random.randint(0, 30))
            }
            interactions.append(interaction)
        
        return interactions
    
    @pytest.mark.asyncio
    async def test_learn_preferences_basic(self):
        """Test basic preference learning."""
        learner = DeepPreferenceLearner()
        interactions = self.create_sample_interactions(5)
        
        model = await learner.learn_preferences(interactions)
        
        assert isinstance(model, DeepPreferenceModel)
        assert model.preference_embeddings.size > 0
        assert len(model.preference_weights) > 0
        assert isinstance(model.temporal_preferences, list)
        assert isinstance(model.contextual_modifiers, dict)
        assert isinstance(model.confidence_intervals, dict)
    
    @pytest.mark.asyncio
    async def test_learn_preferences_empty_interactions(self):
        """Test preference learning with empty interactions."""
        learner = DeepPreferenceLearner()
        
        model = await learner.learn_preferences([])
        
        assert isinstance(model, DeepPreferenceModel)
        assert model.preference_embeddings.size > 0
        # Should return default model
        assert len(model.preference_weights) > 0
    
    @pytest.mark.asyncio
    async def test_extract_interaction_features(self):
        """Test interaction feature extraction."""
        learner = DeepPreferenceLearner()
        interactions = self.create_sample_interactions(3)
        
        features = await learner._extract_interaction_features(interactions)
        
        assert isinstance(features, np.ndarray)
        assert features.shape[0] == 3  # Number of interactions
        assert features.shape[1] == 8  # Number of features
    
    @pytest.mark.asyncio
    async def test_train_embeddings(self):
        """Test embedding training."""
        learner = DeepPreferenceLearner(embedding_dim=64)
        features = np.random.rand(10, 8)
        
        embeddings = await learner._train_embeddings(features)
        
        assert isinstance(embeddings, np.ndarray)
        assert len(embeddings) == 64
    
    @pytest.mark.asyncio
    async def test_extract_preference_weights(self):
        """Test preference weight extraction."""
        learner = DeepPreferenceLearner()
        interactions = self.create_sample_interactions(5)
        
        weights = await learner._extract_preference_weights(interactions)
        
        assert isinstance(weights, dict)
        assert len(weights) > 0
        
        # Check all weights are in valid range
        for weight in weights.values():
            assert 0 <= weight <= 1
    
    def test_calculate_length_preference(self):
        """Test length preference calculation."""
        learner = DeepPreferenceLearner()
        interactions = [
            {'response_length': 100, 'satisfaction': 0.8},
            {'response_length': 200, 'satisfaction': 0.9},
            {'response_length': 300, 'satisfaction': 0.7}
        ]
        
        length_pref = learner._calculate_length_preference(interactions)
        
        assert isinstance(length_pref, float)
        assert 0 <= length_pref <= 1
    
    def test_calculate_technical_preference(self):
        """Test technical preference calculation."""
        learner = DeepPreferenceLearner()
        interactions = [
            {'technical_level': 0.8, 'satisfaction': 0.9},
            {'technical_level': 0.3, 'satisfaction': 0.6},
            {'technical_level': 0.7, 'satisfaction': 0.8}
        ]
        
        tech_pref = learner._calculate_technical_preference(interactions)
        
        assert isinstance(tech_pref, float)
        assert 0 <= tech_pref <= 1
    
    @pytest.mark.asyncio
    async def test_identify_temporal_patterns(self):
        """Test temporal pattern identification."""
        learner = DeepPreferenceLearner()
        
        # Create interactions with temporal patterns
        interactions = []
        for i in range(15):
            # Morning interactions with higher satisfaction
            timestamp = datetime.now().replace(hour=9, minute=0) - timedelta(days=i)
            interaction = {
                'satisfaction': 0.8 + np.random.uniform(-0.1, 0.1),
                'timestamp': timestamp
            }
            interactions.append(interaction)
        
        temporal_prefs = await learner._identify_temporal_patterns(interactions)
        
        assert isinstance(temporal_prefs, list)
        # Should identify morning pattern
        morning_prefs = [tp for tp in temporal_prefs if tp.time_period == "morning"]
        assert len(morning_prefs) > 0
    
    @pytest.mark.asyncio
    async def test_calculate_contextual_modifiers(self):
        """Test contextual modifier calculation."""
        learner = DeepPreferenceLearner()
        interactions = [
            {'context': {'task_complexity': 0.8}, 'satisfaction': 0.9},
            {'context': {'task_complexity': 0.3}, 'satisfaction': 0.6},
            {'context': {'task_complexity': 0.7}, 'satisfaction': 0.8}
        ]
        
        modifiers = await learner._calculate_contextual_modifiers(interactions)
        
        assert isinstance(modifiers, dict)
        # Should detect correlation between task_complexity and satisfaction
        if 'task_complexity' in modifiers:
            assert isinstance(modifiers['task_complexity'], float)


class TestContextualBanditOptimizer:
    """Test cases for ContextualBanditOptimizer class."""
    
    def create_sample_context(self):
        """Create sample context for testing."""
        return {
            'time_of_day': 14,
            'day_of_week': 2,
            'user_satisfaction': 0.7,
            'session_length': 45,
            'task_complexity': 0.6,
            'user_expertise': 0.8,
            'interaction_count': 10,
            'response_time': 2.0,
            'recent_actions': ['action1', 'action2'],
            'engagement_score': 0.75
        }
    
    def create_sample_actions(self):
        """Create sample actions for testing."""
        return [
            {'id': 'action1', 'type': 'detailed_explanation', 'complexity': 0.8},
            {'id': 'action2', 'type': 'simple_answer', 'complexity': 0.3},
            {'id': 'action3', 'type': 'interactive_demo', 'complexity': 0.6}
        ]
    
    @pytest.mark.asyncio
    async def test_select_optimal_action(self):
        """Test optimal action selection."""
        optimizer = ContextualBanditOptimizer()
        context = self.create_sample_context()
        actions = self.create_sample_actions()
        
        optimal_action = await optimizer.select_optimal_action(context, actions)
        
        assert isinstance(optimal_action, OptimalAction)
        assert optimal_action.action_id in ['action1', 'action2', 'action3']
        assert 0 <= optimal_action.expected_reward <= 1
        assert 0 <= optimal_action.confidence <= 1
        assert optimal_action.exploration_factor >= 0
    
    @pytest.mark.asyncio
    async def test_select_optimal_action_empty_actions(self):
        """Test action selection with empty actions list."""
        optimizer = ContextualBanditOptimizer()
        context = self.create_sample_context()
        
        with pytest.raises(ValueError, match="No available actions provided"):
            await optimizer.select_optimal_action(context, [])
    
    @pytest.mark.asyncio
    async def test_update_reward(self):
        """Test reward update mechanism."""
        optimizer = ContextualBanditOptimizer()
        context = self.create_sample_context()
        
        # Update reward for an action
        await optimizer.update_reward('action1', context, 0.8)
        
        assert 'action1' in optimizer.arm_rewards
        assert len(optimizer.arm_rewards['action1']) == 1
        assert optimizer.arm_rewards['action1'][0] == 0.8
        
        assert 'action1' in optimizer.arm_contexts
        assert len(optimizer.arm_contexts['action1']) == 1
    
    @pytest.mark.asyncio
    async def test_vectorize_context(self):
        """Test context vectorization."""
        optimizer = ContextualBanditOptimizer()
        context = self.create_sample_context()
        
        vector = await optimizer._vectorize_context(context)
        
        assert isinstance(vector, np.ndarray)
        assert len(vector) == 10  # Expected number of features
        
        # Check normalization
        assert 0 <= vector[0] <= 1  # time_of_day normalized
        assert 0 <= vector[1] <= 1  # day_of_week normalized
    
    @pytest.mark.asyncio
    async def test_predict_contextual_reward(self):
        """Test contextual reward prediction."""
        optimizer = ContextualBanditOptimizer()
        context_vector = np.random.rand(10)
        
        # Test with no history
        reward = await optimizer._predict_contextual_reward('new_action', context_vector)
        assert reward == 0.5  # Default prediction
        
        # Add some history
        optimizer.arm_rewards['test_action'] = [0.7, 0.8, 0.6]
        optimizer.arm_contexts['test_action'] = [np.random.rand(10) for _ in range(3)]
        
        reward = await optimizer._predict_contextual_reward('test_action', context_vector)
        assert 0 <= reward <= 1
    
    @pytest.mark.asyncio
    async def test_update_context_weights(self):
        """Test context weight updates."""
        optimizer = ContextualBanditOptimizer()
        context_vector = np.random.rand(10)
        
        # Add some context history first
        optimizer.arm_contexts['test_action'] = [context_vector, np.random.rand(10)]
        
        initial_weights = optimizer.context_weights.copy()
        await optimizer._update_context_weights('test_action', context_vector, 0.8)
        
        # Weights should have changed
        assert not np.array_equal(initial_weights, optimizer.context_weights)
        
        # Weights should be clipped to [-1, 1]
        assert np.all(optimizer.context_weights >= -1.0)
        assert np.all(optimizer.context_weights <= 1.0)


class TestMetaLearningAdapter:
    """Test cases for MetaLearningAdapter class."""
    
    def create_sample_user_profile(self, user_id="user1"):
        """Create sample user profile."""
        return {
            'user_id': user_id,
            'age': np.random.randint(20, 60),
            'experience_level': np.random.uniform(0.2, 0.9),
            'domain_expertise': np.random.uniform(0.3, 0.8),
            'technical_background': np.random.uniform(0.4, 0.9),
            'avg_session_length': np.random.uniform(20, 100),
            'interaction_frequency': np.random.uniform(3, 15),
            'task_completion_rate': np.random.uniform(0.5, 0.9),
            'satisfaction_score': np.random.uniform(0.4, 0.8),
            'preferences': {
                'response_length': np.random.uniform(0.3, 0.8),
                'technical_detail': np.random.uniform(0.2, 0.9),
                'interaction_style': np.random.uniform(0.4, 0.7),
                'explanation_depth': np.random.uniform(0.3, 0.8)
            }
        }
    
    def create_similar_users(self, num_users=5):
        """Create list of similar users."""
        return [self.create_sample_user_profile(f"user_{i}") for i in range(num_users)]
    
    @pytest.mark.asyncio
    async def test_adapt_from_similar_users(self):
        """Test adaptation from similar users."""
        adapter = MetaLearningAdapter()
        target_user = self.create_sample_user_profile("target_user")
        similar_users = self.create_similar_users(3)
        
        # Add some adaptation history
        for user in similar_users:
            user_id = user['user_id']
            adapter.adaptation_history[user_id] = [
                {
                    'strategy_type': 'gradual_adjustment',
                    'parameters': {'adjustment_rate': 0.2},
                    'improvement': 0.3,
                    'success_score': 0.7,
                    'timestamp': datetime.now()
                }
            ]
        
        strategy = await adapter.adapt_from_similar_users(target_user, similar_users)
        
        assert isinstance(strategy, AdaptationStrategy)
        assert strategy.strategy_id
        assert isinstance(strategy.strategy_type, AdaptationStrategyType)
        assert 0 <= strategy.expected_improvement <= 1
        assert isinstance(strategy.risk_assessment, RiskAssessment)
        assert isinstance(strategy.rollback_conditions, list)
    
    @pytest.mark.asyncio
    async def test_adapt_from_similar_users_empty(self):
        """Test adaptation with no similar users."""
        adapter = MetaLearningAdapter()
        target_user = self.create_sample_user_profile()
        
        strategy = await adapter.adapt_from_similar_users(target_user, [])
        
        assert isinstance(strategy, AdaptationStrategy)
        # Should return default strategy
        assert strategy.strategy_type == AdaptationStrategyType.CONSERVATIVE_CHANGE
    
    @pytest.mark.asyncio
    async def test_calculate_user_similarity(self):
        """Test user similarity calculation."""
        adapter = MetaLearningAdapter()
        user1 = self.create_sample_user_profile("user1")
        user2 = self.create_sample_user_profile("user2")
        
        # Test with identical users
        similarity = await adapter._calculate_user_similarity(user1, user1)
        assert abs(similarity - 1.0) < 0.01  # Should be very close to 1
        
        # Test with different users
        similarity = await adapter._calculate_user_similarity(user1, user2)
        assert 0 <= similarity <= 1
    
    @pytest.mark.asyncio
    async def test_extract_user_features(self):
        """Test user feature extraction."""
        adapter = MetaLearningAdapter()
        user_profile = self.create_sample_user_profile()
        
        features = await adapter._extract_user_features(user_profile)
        
        assert isinstance(features, np.ndarray)
        assert len(features) == 12  # Expected number of features
        
        # Check normalization
        assert np.all(features >= 0)
        assert np.all(features <= 1)
    
    @pytest.mark.asyncio
    async def test_extract_successful_adaptations(self):
        """Test extraction of successful adaptations."""
        adapter = MetaLearningAdapter()
        
        # Create similar users with adaptation history
        similar_users = [(0.8, {'user_id': 'user1'}), (0.7, {'user_id': 'user2'})]
        
        adapter.adaptation_history = {
            'user1': [
                {'success_score': 0.8, 'strategy_type': 'gradual_adjustment'},
                {'success_score': 0.3, 'strategy_type': 'rapid_adaptation'}  # Not successful
            ],
            'user2': [
                {'success_score': 0.7, 'strategy_type': 'conservative_change'}
            ]
        }
        
        successful = await adapter._extract_successful_adaptations(similar_users)
        
        assert len(successful) == 2  # Only successful adaptations
        assert all(adaptation['success_score'] > 0.6 for adaptation in successful)
        assert all('similarity_weight' in adaptation for adaptation in successful)
    
    def test_record_adaptation_outcome(self):
        """Test recording adaptation outcomes."""
        adapter = MetaLearningAdapter()
        
        strategy = AdaptationStrategy(
            strategy_id="test_strategy",
            strategy_type=AdaptationStrategyType.GRADUAL_ADJUSTMENT,
            parameters={'adjustment_rate': 0.2},
            expected_improvement=0.3,
            risk_assessment=RiskAssessment(
                risk_level=RiskLevel.LOW,
                risk_factors=[],
                mitigation_strategies=[],
                rollback_probability=0.1,
                impact_assessment={}
            ),
            rollback_conditions=[],
            implementation_steps=[],
            success_metrics=[]
        )
        
        outcome = {
            'improvement': 0.4,
            'success_score': 0.8,
            'satisfaction_change': 0.2
        }
        
        adapter.record_adaptation_outcome("test_user", strategy, outcome)
        
        assert "test_user" in adapter.adaptation_history
        assert len(adapter.adaptation_history["test_user"]) == 1
        
        record = adapter.adaptation_history["test_user"][0]
        assert record['strategy_type'] == 'gradual_adjustment'
        assert record['actual_improvement'] == 0.4
        assert record['success_score'] == 0.8


class TestAdvancedAdaptationAlgorithms:
    """Test cases for AdvancedAdaptationAlgorithms class."""
    
    def create_sample_interactions(self):
        """Create sample interactions for testing."""
        return [
            {
                'duration': 120,
                'satisfaction': 0.8,
                'engagement': 0.7,
                'task_completion': 1.0,
                'actions': ['action1', 'action2'],
                'context': {'time_of_day': 14, 'day_of_week': 2}
            }
        ]
    
    def create_sample_context(self):
        """Create sample context for testing."""
        return {
            'time_of_day': 14,
            'user_satisfaction': 0.7,
            'task_complexity': 0.6
        }
    
    def create_sample_actions(self):
        """Create sample actions for testing."""
        return [
            {'id': 'action1', 'type': 'explanation'},
            {'id': 'action2', 'type': 'example'}
        ]
    
    def create_sample_user_profile(self):
        """Create sample user profile for testing."""
        return {
            'user_id': 'test_user',
            'experience_level': 0.7,
            'preferences': {'technical_detail': 0.6}
        }
    
    @pytest.mark.asyncio
    async def test_deep_preference_learning(self):
        """Test deep preference learning integration."""
        algorithms = AdvancedAdaptationAlgorithms()
        interactions = self.create_sample_interactions()
        
        model = await algorithms.deep_preference_learning(interactions)
        
        assert isinstance(model, DeepPreferenceModel)
        assert model.preference_embeddings.size > 0
    
    @pytest.mark.asyncio
    async def test_contextual_bandit_optimization(self):
        """Test contextual bandit optimization integration."""
        algorithms = AdvancedAdaptationAlgorithms()
        context = self.create_sample_context()
        actions = self.create_sample_actions()
        
        optimal_action = await algorithms.contextual_bandit_optimization(context, actions)
        
        assert isinstance(optimal_action, OptimalAction)
        assert optimal_action.action_id in ['action1', 'action2']
    
    @pytest.mark.asyncio
    async def test_meta_learning_adaptation(self):
        """Test meta-learning adaptation integration."""
        algorithms = AdvancedAdaptationAlgorithms()
        user_profile = self.create_sample_user_profile()
        similar_users = [self.create_sample_user_profile()]
        
        strategy = await algorithms.meta_learning_adaptation(user_profile, similar_users)
        
        assert isinstance(strategy, AdaptationStrategy)
        assert strategy.strategy_id
    
    @pytest.mark.asyncio
    async def test_update_bandit_reward(self):
        """Test bandit reward update integration."""
        algorithms = AdvancedAdaptationAlgorithms()
        context = self.create_sample_context()
        
        # Should not raise any errors
        await algorithms.update_bandit_reward('action1', context, 0.8)
        
        # Verify reward was recorded
        assert 'action1' in algorithms.contextual_bandit.arm_rewards
    
    def test_record_adaptation_outcome(self):
        """Test adaptation outcome recording integration."""
        algorithms = AdvancedAdaptationAlgorithms()
        
        strategy = AdaptationStrategy(
            strategy_id="test",
            strategy_type=AdaptationStrategyType.GRADUAL_ADJUSTMENT,
            parameters={},
            expected_improvement=0.3,
            risk_assessment=RiskAssessment(
                risk_level=RiskLevel.LOW,
                risk_factors=[],
                mitigation_strategies=[],
                rollback_probability=0.1,
                impact_assessment={}
            ),
            rollback_conditions=[],
            implementation_steps=[],
            success_metrics=[]
        )
        
        outcome = {'improvement': 0.4, 'success_score': 0.8}
        
        # Should not raise any errors
        algorithms.record_adaptation_outcome("test_user", strategy, outcome)
        
        # Verify outcome was recorded
        assert "test_user" in algorithms.meta_learner.adaptation_history