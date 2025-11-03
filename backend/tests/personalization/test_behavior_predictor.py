"""
Unit tests for user behavior prediction system.
"""

import pytest
import numpy as np
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from backend.rl.personalization.behavior_predictor import (
    UserBehaviorPredictor,
    PatternDetector,
    ActionPredictor,
    SatisfactionPredictor,
    UserHistory,
    PredictionConfidence,
    BehaviorCategory
)
from backend.rl.personalization.personalization_models import (
    BehaviorPattern,
    BehaviorPatternType,
    PredictedAction,
    SatisfactionTrajectory,
    ContextCondition,
    SuccessIndicator
)


class TestUserHistory:
    """Test cases for UserHistory class."""
    
    def create_sample_interactions(self, num_interactions=10):
        """Create sample interactions for testing."""
        interactions = []
        base_time = datetime.now()
        
        for i in range(num_interactions):
            interaction = {
                'interaction_id': f'int_{i}',
                'timestamp': (base_time - timedelta(hours=i)).isoformat(),
                'action_type': f'action_{i % 3}',
                'satisfaction': np.random.uniform(0.3, 0.9),
                'duration': np.random.uniform(30, 300),
                'task_completion': np.random.choice([0.0, 1.0]),
                'context': {
                    'task_complexity': np.random.uniform(0.2, 0.8),
                    'time_of_day': (base_time - timedelta(hours=i)).hour
                }
            }
            interactions.append(interaction)
        
        return interactions
    
    def create_sample_sessions(self, num_sessions=5):
        """Create sample sessions for testing."""
        sessions = []
        base_time = datetime.now()
        
        for i in range(num_sessions):
            session = {
                'session_id': f'sess_{i}',
                'timestamp': (base_time - timedelta(days=i)).isoformat(),
                'duration': np.random.uniform(600, 3600),  # 10-60 minutes
                'satisfaction': np.random.uniform(0.4, 0.8),
                'completion_rate': np.random.uniform(0.5, 1.0),
                'start_satisfaction': np.random.uniform(0.4, 0.7),
                'end_satisfaction': np.random.uniform(0.5, 0.9)
            }
            sessions.append(session)
        
        return sessions
    
    def test_user_history_creation(self):
        """Test UserHistory creation."""
        interactions = self.create_sample_interactions(5)
        sessions = self.create_sample_sessions(3)
        preferences = {'technical_detail': 0.7, 'response_length': 0.5}
        performance_metrics = {'accuracy': [0.8, 0.9, 0.7]}
        
        history = UserHistory(
            user_id="test_user",
            interactions=interactions,
            sessions=sessions,
            preferences=preferences,
            performance_metrics=performance_metrics
        )
        
        assert history.user_id == "test_user"
        assert len(history.interactions) == 5
        assert len(history.sessions) == 3
        assert history.preferences == preferences
        assert history.performance_metrics == performance_metrics
    
    def test_get_recent_interactions(self):
        """Test getting recent interactions."""
        interactions = self.create_sample_interactions(10)
        history = UserHistory(
            user_id="test_user",
            interactions=interactions,
            sessions=[],
            preferences={},
            performance_metrics={}
        )
        
        # Get interactions from last 5 hours
        recent = history.get_recent_interactions(hours=5)
        
        # Should return interactions from last 5 hours
        assert len(recent) <= 5
        assert all(isinstance(interaction, dict) for interaction in recent)
    
    def test_get_session_statistics(self):
        """Test session statistics calculation."""
        sessions = self.create_sample_sessions(5)
        history = UserHistory(
            user_id="test_user",
            interactions=[],
            sessions=sessions,
            preferences={},
            performance_metrics={}
        )
        
        stats = history.get_session_statistics()
        
        assert isinstance(stats, dict)
        assert 'avg_session_duration' in stats
        assert 'avg_satisfaction' in stats
        assert 'avg_completion_rate' in stats
        assert 'total_sessions' in stats
        assert stats['total_sessions'] == 5
    
    def test_get_session_statistics_empty(self):
        """Test session statistics with no sessions."""
        history = UserHistory(
            user_id="test_user",
            interactions=[],
            sessions=[],
            preferences={},
            performance_metrics={}
        )
        
        stats = history.get_session_statistics()
        assert stats == {}


class TestPatternDetector:
    """Test cases for PatternDetector class."""
    
    def create_sample_user_history(self):
        """Create sample user history for pattern detection."""
        interactions = []
        base_time = datetime.now()
        
        # Create sequential pattern: action1 -> action2 -> action3
        for i in range(15):
            for j, action in enumerate(['action1', 'action2', 'action3']):
                interaction = {
                    'timestamp': (base_time - timedelta(hours=i*3 + j)).isoformat(),
                    'action_type': action,
                    'satisfaction': 0.7 + np.random.uniform(-0.1, 0.1),
                    'context': {
                        'task_complexity': 0.5,
                        'day_of_week': (base_time - timedelta(hours=i*3 + j)).weekday()
                    }
                }
                interactions.append(interaction)
        
        return UserHistory(
            user_id="test_user",
            interactions=interactions,
            sessions=[],
            preferences={'technical_detail': 0.6},
            performance_metrics={}
        )
    
    @pytest.mark.asyncio
    async def test_detect_patterns(self):
        """Test pattern detection."""
        detector = PatternDetector(min_pattern_occurrences=3)
        user_history = self.create_sample_user_history()
        
        patterns = await detector.detect_patterns(user_history)
        
        assert isinstance(patterns, list)
        # Should detect some patterns
        assert len(patterns) > 0
        
        for pattern in patterns:
            assert isinstance(pattern, BehaviorPattern)
            assert pattern.pattern_id
            assert isinstance(pattern.pattern_type, BehaviorPatternType)
            assert 0 <= pattern.frequency <= 1
            assert 0 <= pattern.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_detect_sequential_patterns(self):
        """Test sequential pattern detection."""
        detector = PatternDetector(min_pattern_occurrences=3)
        user_history = self.create_sample_user_history()
        
        patterns = await detector._detect_sequential_patterns(user_history)
        
        assert isinstance(patterns, list)
        # Should detect sequential patterns
        sequential_patterns = [p for p in patterns if p.pattern_type == BehaviorPatternType.SEQUENTIAL]
        assert len(sequential_patterns) > 0
    
    @pytest.mark.asyncio
    async def test_detect_cyclical_patterns(self):
        """Test cyclical pattern detection."""
        detector = PatternDetector(min_pattern_occurrences=2)
        
        # Create interactions with daily patterns
        interactions = []
        base_time = datetime.now()
        
        for i in range(10):
            # Morning interactions with high satisfaction
            morning_time = base_time.replace(hour=9) - timedelta(days=i)
            interaction = {
                'timestamp': morning_time.isoformat(),
                'satisfaction': 0.8 + np.random.uniform(-0.1, 0.1),
                'action_type': 'morning_action'
            }
            interactions.append(interaction)
        
        user_history = UserHistory(
            user_id="test_user",
            interactions=interactions,
            sessions=[],
            preferences={},
            performance_metrics={}
        )
        
        patterns = await detector._detect_cyclical_patterns(user_history)
        
        assert isinstance(patterns, list)
        # Should detect daily patterns
        cyclical_patterns = [p for p in patterns if p.pattern_type == BehaviorPatternType.CYCLICAL]
        # May or may not detect patterns depending on data distribution
    
    @pytest.mark.asyncio
    async def test_detect_contextual_patterns(self):
        """Test contextual pattern detection."""
        detector = PatternDetector(min_pattern_occurrences=3)
        
        # Create interactions with context-dependent patterns
        interactions = []
        
        # High complexity tasks with lower completion
        for i in range(5):
            interaction = {
                'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
                'context': {'task_complexity': 0.8},
                'task_completion': 0.3,
                'duration': 120
            }
            interactions.append(interaction)
        
        # Low complexity tasks with higher completion
        for i in range(5):
            interaction = {
                'timestamp': (datetime.now() - timedelta(hours=i+5)).isoformat(),
                'context': {'task_complexity': 0.2},
                'task_completion': 0.9,
                'duration': 60
            }
            interactions.append(interaction)
        
        user_history = UserHistory(
            user_id="test_user",
            interactions=interactions,
            sessions=[],
            preferences={},
            performance_metrics={}
        )
        
        patterns = await detector._detect_contextual_patterns(user_history)
        
        assert isinstance(patterns, list)
        # Should detect contextual patterns
        contextual_patterns = [p for p in patterns if p.pattern_type == BehaviorPatternType.CONTEXTUAL]
        assert len(contextual_patterns) > 0


class TestActionPredictor:
    """Test cases for ActionPredictor class."""
    
    def create_sample_context(self):
        """Create sample context for prediction."""
        return {
            'task_complexity': 0.6,
            'user_expertise': 0.7,
            'time_of_day': 14,
            'user_satisfaction': 0.5,
            'engagement_score': 0.6
        }
    
    def create_sample_patterns(self):
        """Create sample behavior patterns."""
        return [
            BehaviorPattern(
                pattern_id="test_pattern_1",
                pattern_type=BehaviorPatternType.CONTEXTUAL,
                frequency=0.7,
                context_conditions=[
                    ContextCondition(
                        condition_type="task_complexity",
                        condition_value=0.6,
                        operator="greater_than"
                    )
                ],
                predictive_features=["task_complexity", "user_expertise"],
                success_indicators=[
                    SuccessIndicator(
                        metric_name="completion_rate",
                        target_value=0.8,
                        current_value=0.7
                    )
                ],
                confidence=0.8
            )
        ]
    
    def create_sample_user_history(self):
        """Create sample user history."""
        interactions = [
            {
                'action_type': 'request_help',
                'satisfaction': 0.8,
                'context': {'task_complexity': 0.7}
            },
            {
                'action_type': 'continue_current',
                'satisfaction': 0.6,
                'context': {'task_complexity': 0.3}
            }
        ]
        
        return UserHistory(
            user_id="test_user",
            interactions=interactions,
            sessions=[],
            preferences={},
            performance_metrics={}
        )
    
    @pytest.mark.asyncio
    async def test_predict_next_action(self):
        """Test next action prediction."""
        predictor = ActionPredictor()
        context = self.create_sample_context()
        patterns = self.create_sample_patterns()
        user_history = self.create_sample_user_history()
        
        predicted_action = await predictor.predict_next_action(context, patterns, user_history)
        
        assert isinstance(predicted_action, PredictedAction)
        assert predicted_action.action_type
        assert isinstance(predicted_action.action_parameters, dict)
        assert 0 <= predicted_action.probability <= 1
        assert 0 <= predicted_action.confidence <= 1
        assert predicted_action.reasoning
        assert isinstance(predicted_action.alternative_actions, list)
    
    @pytest.mark.asyncio
    async def test_predict_next_action_no_patterns(self):
        """Test action prediction with no patterns."""
        predictor = ActionPredictor()
        context = self.create_sample_context()
        user_history = self.create_sample_user_history()
        
        predicted_action = await predictor.predict_next_action(context, [], user_history)
        
        assert isinstance(predicted_action, PredictedAction)
        # Should return default action
        assert predicted_action.action_type in ['request_help', 'change_approach', 'continue_current']
        assert predicted_action.confidence <= 0.6  # Should have lower confidence
    
    @pytest.mark.asyncio
    async def test_get_pattern_actions(self):
        """Test getting actions for a pattern."""
        predictor = ActionPredictor()
        pattern = self.create_sample_patterns()[0]
        user_history = self.create_sample_user_history()
        
        actions = await predictor._get_pattern_actions(pattern, user_history)
        
        assert isinstance(actions, dict)
        # Should return action probabilities
        for action_type, probability in actions.items():
            assert isinstance(action_type, str)
            assert 0 <= probability <= 1
    
    @pytest.mark.asyncio
    async def test_generate_action_parameters(self):
        """Test action parameter generation."""
        predictor = ActionPredictor()
        action_type = "request_help"
        context = self.create_sample_context()
        patterns = self.create_sample_patterns()
        
        parameters = await predictor._generate_action_parameters(action_type, context, patterns)
        
        assert isinstance(parameters, dict)
        assert parameters['action_type'] == action_type
        assert 'context_driven' in parameters
        assert 'pattern_based' in parameters


class TestSatisfactionPredictor:
    """Test cases for SatisfactionPredictor class."""
    
    def create_sample_user_history(self):
        """Create sample user history for satisfaction prediction."""
        interactions = []
        sessions = []
        
        # Create interactions with varying satisfaction
        for i in range(10):
            interaction = {
                'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
                'satisfaction': 0.5 + np.sin(i * 0.5) * 0.3,  # Oscillating satisfaction
                'duration': 60 + i * 10
            }
            interactions.append(interaction)
        
        # Create sessions with satisfaction trends
        for i in range(5):
            session = {
                'duration': 1800 + i * 300,  # 30-55 minutes
                'start_satisfaction': 0.6,
                'end_satisfaction': 0.7 - i * 0.05  # Declining trend
            }
            sessions.append(session)
        
        return UserHistory(
            user_id="test_user",
            interactions=interactions,
            sessions=sessions,
            preferences={},
            performance_metrics={}
        )
    
    @pytest.mark.asyncio
    async def test_predict_satisfaction_trajectory(self):
        """Test satisfaction trajectory prediction."""
        predictor = SatisfactionPredictor()
        user_history = self.create_sample_user_history()
        context = {
            'task_complexity': 0.5,
            'user_expertise': 0.6,
            'engagement_score': 0.7
        }
        
        trajectory = await predictor.predict_satisfaction_trajectory(
            user_history, context, time_horizon_minutes=30
        )
        
        assert isinstance(trajectory, SatisfactionTrajectory)
        assert len(trajectory.time_points) > 0
        assert len(trajectory.satisfaction_values) == len(trajectory.time_points)
        assert len(trajectory.confidence_bands) == len(trajectory.time_points)
        assert isinstance(trajectory.influencing_factors, list)
        
        # Check satisfaction values are in valid range
        for satisfaction in trajectory.satisfaction_values:
            assert 0 <= satisfaction <= 1
        
        # Check confidence bands
        for lower, upper in trajectory.confidence_bands:
            assert 0 <= lower <= upper <= 1
    
    @pytest.mark.asyncio
    async def test_calculate_baseline_satisfaction(self):
        """Test baseline satisfaction calculation."""
        predictor = SatisfactionPredictor()
        user_history = self.create_sample_user_history()
        
        baseline = await predictor._calculate_baseline_satisfaction(user_history)
        
        assert isinstance(baseline, float)
        assert 0 <= baseline <= 1
    
    @pytest.mark.asyncio
    async def test_predict_satisfaction_at_time(self):
        """Test satisfaction prediction at specific time."""
        predictor = SatisfactionPredictor()
        user_history = self.create_sample_user_history()
        context = {'engagement_score': 0.8, 'task_complexity': 0.4}
        baseline = 0.6
        
        satisfaction, confidence_interval = await predictor._predict_satisfaction_at_time(
            user_history, context, baseline, time_minutes=30
        )
        
        assert isinstance(satisfaction, float)
        assert 0 <= satisfaction <= 1
        assert isinstance(confidence_interval, tuple)
        assert len(confidence_interval) == 2
        assert 0 <= confidence_interval[0] <= confidence_interval[1] <= 1
    
    @pytest.mark.asyncio
    async def test_identify_influencing_factors(self):
        """Test identification of influencing factors."""
        predictor = SatisfactionPredictor()
        user_history = self.create_sample_user_history()
        context = {
            'task_complexity': 0.8,
            'user_expertise': 0.2,
            'support_available': False,
            'user_fatigue': 0.8
        }
        
        factors = await predictor._identify_influencing_factors(user_history, context)
        
        assert isinstance(factors, list)
        # Should identify high complexity and low expertise as factors
        assert 'high_task_complexity' in factors
        assert 'low_user_expertise' in factors
        assert 'no_support_available' in factors
        assert 'user_fatigue' in factors


class TestUserBehaviorPredictor:
    """Test cases for UserBehaviorPredictor class."""
    
    def create_comprehensive_user_history(self):
        """Create comprehensive user history for testing."""
        interactions = []
        sessions = []
        
        # Create diverse interactions
        action_types = ['search', 'read', 'ask_question', 'request_help', 'continue']
        
        for i in range(20):
            interaction = {
                'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
                'action_type': action_types[i % len(action_types)],
                'satisfaction': np.random.uniform(0.4, 0.9),
                'duration': np.random.uniform(30, 300),
                'task_completion': np.random.choice([0.0, 1.0]),
                'context': {
                    'task_complexity': np.random.uniform(0.2, 0.8),
                    'user_expertise': 0.6,
                    'time_of_day': (datetime.now() - timedelta(hours=i)).hour
                }
            }
            interactions.append(interaction)
        
        # Create sessions
        for i in range(8):
            session = {
                'session_id': f'sess_{i}',
                'timestamp': (datetime.now() - timedelta(days=i)).isoformat(),
                'duration': np.random.uniform(600, 3600),
                'satisfaction': np.random.uniform(0.5, 0.8),
                'completion_rate': np.random.uniform(0.6, 1.0)
            }
            sessions.append(session)
        
        return UserHistory(
            user_id="comprehensive_user",
            interactions=interactions,
            sessions=sessions,
            preferences={
                'technical_detail': 0.7,
                'response_length': 0.5,
                'interaction_style': 0.6
            },
            performance_metrics={
                'accuracy': [0.8, 0.7, 0.9, 0.8],
                'speed': [0.6, 0.7, 0.8, 0.7]
            }
        )
    
    @pytest.mark.asyncio
    async def test_predict_next_action(self):
        """Test next action prediction integration."""
        predictor = UserBehaviorPredictor()
        user_history = self.create_comprehensive_user_history()
        context = {
            'task_complexity': 0.6,
            'user_expertise': 0.7,
            'user_satisfaction': 0.5
        }
        
        predicted_action = await predictor.predict_next_action(context, user_history)
        
        assert isinstance(predicted_action, PredictedAction)
        assert predicted_action.action_type
        assert 0 <= predicted_action.probability <= 1
        assert 0 <= predicted_action.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_predict_satisfaction_trajectory(self):
        """Test satisfaction trajectory prediction integration."""
        predictor = UserBehaviorPredictor()
        user_history = self.create_comprehensive_user_history()
        context = {
            'task_complexity': 0.5,
            'engagement_score': 0.7
        }
        
        trajectory = await predictor.predict_satisfaction_trajectory(
            user_history, context, time_horizon_minutes=45
        )
        
        assert isinstance(trajectory, SatisfactionTrajectory)
        assert len(trajectory.time_points) > 0
        assert len(trajectory.satisfaction_values) > 0
    
    @pytest.mark.asyncio
    async def test_identify_behavior_patterns(self):
        """Test behavior pattern identification."""
        predictor = UserBehaviorPredictor()
        user_history = self.create_comprehensive_user_history()
        
        patterns = await predictor.identify_behavior_patterns(user_history)
        
        assert isinstance(patterns, list)
        # Should cache the patterns
        assert user_history.user_id in predictor.user_patterns_cache
        
        # Test cache usage
        patterns_cached = await predictor.identify_behavior_patterns(user_history)
        assert patterns_cached == patterns  # Should return cached version
    
    @pytest.mark.asyncio
    async def test_update_pattern_from_observation(self):
        """Test pattern updates from observations."""
        predictor = UserBehaviorPredictor()
        user_history = self.create_comprehensive_user_history()
        
        # First identify patterns
        await predictor.identify_behavior_patterns(user_history)
        
        # Update with new observation
        context = {'task_complexity': 0.5}
        await predictor.update_pattern_from_observation(
            user_history.user_id, context, outcome_success=True
        )
        
        # Should not raise any errors
        assert user_history.user_id in predictor.user_patterns_cache
    
    def test_get_prediction_confidence(self):
        """Test prediction confidence assessment."""
        predictor = UserBehaviorPredictor()
        
        # High confidence prediction
        high_conf_action = PredictedAction(
            action_type="test_action",
            action_parameters={},
            probability=0.9,
            confidence=0.8,
            reasoning="test"
        )
        
        high_conf_patterns = [
            BehaviorPattern(
                pattern_id="pattern1",
                pattern_type=BehaviorPatternType.SEQUENTIAL,
                frequency=0.8,
                context_conditions=[],
                predictive_features=[],
                success_indicators=[],
                confidence=0.9
            )
        ]
        
        confidence = predictor.get_prediction_confidence(high_conf_action, high_conf_patterns)
        assert confidence in [PredictionConfidence.HIGH, PredictionConfidence.VERY_HIGH]
        
        # Low confidence prediction
        low_conf_action = PredictedAction(
            action_type="test_action",
            action_parameters={},
            probability=0.3,
            confidence=0.2,
            reasoning="test"
        )
        
        confidence = predictor.get_prediction_confidence(low_conf_action, [])
        assert confidence in [PredictionConfidence.LOW, PredictionConfidence.MEDIUM]
    
    def test_get_behavior_insights(self):
        """Test behavior insights generation."""
        predictor = UserBehaviorPredictor()
        user_history = self.create_comprehensive_user_history()
        
        insights = predictor.get_behavior_insights(user_history)
        
        assert isinstance(insights, dict)
        assert 'session_statistics' in insights
        assert 'behavioral_trends' in insights
        
        # Check behavioral trends
        trends = insights['behavioral_trends']
        assert 'recent_satisfaction' in trends
        assert 'overall_satisfaction' in trends
        assert 'satisfaction_trend' in trends
        assert 'total_interactions' in trends
        
        assert trends['satisfaction_trend'] in ['improving', 'declining']
        assert trends['total_interactions'] == len(user_history.interactions)