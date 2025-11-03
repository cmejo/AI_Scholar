"""Unit tests for extended reward system."""

import pytest
import numpy as np
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from backend.rl.rewards.extended_reward_system import (
    ExtendedRewardCalculator,
    RewardType,
    EngagementLevel,
    MultiModalReward,
    WorkflowEfficiencyReward,
    VisualEngagementReward,
    ResearchProductivityReward,
    PersonalizationAccuracyReward,
    ExtendedRewardCalculation
)
from backend.rl.models.feedback_models import FeedbackData
from backend.rl.multimodal.models import MultiModalFeatures, VisualElement, VisualElementType
from backend.rl.research_assistant.workflow_optimizer import EfficiencyMetrics


class TestExtendedRewardCalculator:
    """Test cases for ExtendedRewardCalculator class."""
    
    def create_sample_feedback(self):
        """Create sample feedback data."""
        return FeedbackData(
            feedback_id="feedback_1",
            user_id="user_1",
            rating=4.0,
            interaction_time=180.0,  # 3 minutes
            clicked=True,
            completed=True
        )
    
    def create_sample_multimodal_features(self):
        """Create sample multi-modal features."""
        visual_elements = [
            VisualElement(
                element_id="chart_1",
                element_type=VisualElementType.CHART,
                content="Sample chart",
                complexity_score=0.7
            ),
            VisualElement(
                element_id="diagram_1",
                element_type=VisualElementType.DIAGRAM,
                content="Sample diagram",
                complexity_score=0.8
            )
        ]
        
        return MultiModalFeatures(
            text_features={"key_terms": ["research", "analysis"]},
            visual_elements=visual_elements,
            cross_modal_coherence=0.85,
            integration_quality=0.9
        )
    
    def create_sample_efficiency_metrics(self):
        """Create sample efficiency metrics."""
        return EfficiencyMetrics(
            time_efficiency=0.8,
            resource_utilization=0.75,
            task_completion_rate=0.9,
            user_satisfaction=0.85,
            bottleneck_frequency=0.2,
            context_switch_penalty=0.1,
            overall_efficiency=0.82
        )
    
    @pytest.mark.asyncio
    async def test_calculate_extended_reward_all_components(self):
        """Test extended reward calculation with all components."""
        calculator = ExtendedRewardCalculator()
        
        # Prepare all input data
        feedback = self.create_sample_feedback()
        multimodal_features = self.create_sample_multimodal_features()
        workflow_metrics = self.create_sample_efficiency_metrics()
        
        visual_engagement = {
            'engagement_level': 'high',
            'interaction_quality': 0.8,
            'visual_comprehension': 0.85,
            'attention_distribution': {'important_elements': 0.9},
            'learning_effectiveness': 0.8
        }
        
        research_session = {
            'tasks_completed': 4,
            'expected_tasks': 5,
            'quality_score': 0.85,
            'efficiency_score': 0.8,
            'knowledge_gain': 0.7,
            'research_progress': 0.75
        }
        
        personalization_data = {
            'prediction_accuracy': 0.8,
            'preference_alignment': 0.85,
            'adaptation_effectiveness': 0.75,
            'user_satisfaction_delta': 0.1,
            'behavioral_prediction_score': 0.8
        }
        
        result = await calculator.calculate_extended_reward(
            user_id="user_1",
            traditional_feedback=feedback,
            multi_modal_features=multimodal_features,
            workflow_metrics=workflow_metrics,
            visual_engagement=visual_engagement,
            research_session=research_session,
            personalization_data=personalization_data
        )
        
        assert isinstance(result, ExtendedRewardCalculation)
        assert 0.0 <= result.total_reward <= 1.0
        assert len(result.reward_breakdown) == 6  # All reward types
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.explanation
        assert isinstance(result.contributing_factors, list)
        assert isinstance(result.improvement_suggestions, list)
        
        # Check that all reward types are present
        expected_types = set(RewardType)
        actual_types = set(result.reward_breakdown.keys())
        assert expected_types == actual_types
    
    @pytest.mark.asyncio
    async def test_calculate_extended_reward_partial_components(self):
        """Test extended reward calculation with partial components."""
        calculator = ExtendedRewardCalculator()
        
        # Only provide some components
        feedback = self.create_sample_feedback()
        workflow_metrics = self.create_sample_efficiency_metrics()
        
        result = await calculator.calculate_extended_reward(
            user_id="user_1",
            traditional_feedback=feedback,
            workflow_metrics=workflow_metrics
        )
        
        assert isinstance(result, ExtendedRewardCalculation)
        assert 0.0 <= result.total_reward <= 1.0
        assert len(result.reward_breakdown) == 2  # Only traditional and workflow
        
        # Check specific components
        assert RewardType.TRADITIONAL in result.reward_breakdown
        assert RewardType.WORKFLOW_EFFICIENCY in result.reward_breakdown
        assert RewardType.MULTI_MODAL not in result.reward_breakdown
    
    @pytest.mark.asyncio
    async def test_calculate_traditional_reward(self):
        """Test traditional reward calculation."""
        calculator = ExtendedRewardCalculator()
        
        # High quality feedback
        good_feedback = FeedbackData(
            feedback_id="feedback_1",
            user_id="user_1",
            rating=5.0,
            interaction_time=240.0,
            clicked=True,
            completed=True
        )
        
        reward = await calculator._calculate_traditional_reward(good_feedback)
        
        assert isinstance(reward, float)
        assert 0.0 <= reward <= 1.0
        assert reward > 0.8  # Should be high for good feedback
        
        # Poor quality feedback
        poor_feedback = FeedbackData(
            feedback_id="feedback_2",
            user_id="user_1",
            rating=1.0,
            interaction_time=10.0,
            clicked=False,
            completed=False
        )
        
        poor_reward = await calculator._calculate_traditional_reward(poor_feedback)
        
        assert isinstance(poor_reward, float)
        assert 0.0 <= poor_reward <= 1.0
        assert poor_reward < reward  # Should be lower than good feedback
    
    @pytest.mark.asyncio
    async def test_calculate_multimodal_reward(self):
        """Test multi-modal reward calculation."""
        calculator = ExtendedRewardCalculator()
        
        multimodal_features = self.create_sample_multimodal_features()
        
        visual_engagement = {
            'engagement_score': 0.8,
            'attention_score': 0.85,
            'comprehension_score': 0.9
        }
        
        reward = await calculator._calculate_multi_modal_reward(
            "user_1", multimodal_features, visual_engagement
        )
        
        assert isinstance(reward, float)
        assert 0.0 <= reward <= 1.0
        assert reward > 0.5  # Should be reasonably high for good engagement
    
    @pytest.mark.asyncio
    async def test_calculate_workflow_efficiency_reward(self):
        """Test workflow efficiency reward calculation."""
        calculator = ExtendedRewardCalculator()
        
        # High efficiency metrics
        high_metrics = EfficiencyMetrics(
            time_efficiency=0.9,
            resource_utilization=0.85,
            task_completion_rate=0.95,
            user_satisfaction=0.9,
            bottleneck_frequency=0.1,
            context_switch_penalty=0.05,
            overall_efficiency=0.9
        )
        
        reward = await calculator._calculate_workflow_efficiency_reward("user_1", high_metrics)
        
        assert isinstance(reward, float)
        assert 0.0 <= reward <= 1.0
        assert reward > 0.7  # Should be high for good metrics
        
        # Check that baseline was updated
        assert "user_1" in calculator.baseline_metrics
        assert "time_efficiency" in calculator.baseline_metrics["user_1"]
    
    @pytest.mark.asyncio
    async def test_calculate_visual_engagement_reward(self):
        """Test visual engagement reward calculation."""
        calculator = ExtendedRewardCalculator()
        
        high_engagement = {
            'engagement_level': 'exceptional',
            'interaction_quality': 0.9,
            'visual_comprehension': 0.85,
            'attention_distribution': {'important_elements': 0.9},
            'learning_effectiveness': 0.8
        }
        
        reward = await calculator._calculate_visual_engagement_reward("user_1", high_engagement)
        
        assert isinstance(reward, float)
        assert 0.0 <= reward <= 1.0
        assert reward > 0.8  # Should be high for exceptional engagement
        
        # Test with low engagement
        low_engagement = {
            'engagement_level': 'low',
            'interaction_quality': 0.3,
            'visual_comprehension': 0.4,
            'learning_effectiveness': 0.3
        }
        
        low_reward = await calculator._calculate_visual_engagement_reward("user_1", low_engagement)
        
        assert low_reward < reward  # Should be lower
    
    @pytest.mark.asyncio
    async def test_calculate_research_productivity_reward(self):
        """Test research productivity reward calculation."""
        calculator = ExtendedRewardCalculator()
        
        high_productivity = {
            'tasks_completed': 6,
            'expected_tasks': 5,  # Exceeded expectations
            'quality_score': 0.9,
            'efficiency_score': 0.85,
            'knowledge_gain': 0.8,
            'research_progress': 0.9
        }
        
        reward = await calculator._calculate_research_productivity_reward("user_1", high_productivity)
        
        assert isinstance(reward, float)
        assert 0.0 <= reward <= 1.0
        assert reward > 0.8  # Should be high for exceeding expectations
    
    @pytest.mark.asyncio
    async def test_calculate_personalization_accuracy_reward(self):
        """Test personalization accuracy reward calculation."""
        calculator = ExtendedRewardCalculator()
        
        high_accuracy = {
            'prediction_accuracy': 0.9,
            'preference_alignment': 0.85,
            'adaptation_effectiveness': 0.8,
            'user_satisfaction_delta': 0.2,  # Good improvement
            'behavioral_prediction_score': 0.85
        }
        
        reward = await calculator._calculate_personalization_accuracy_reward("user_1", high_accuracy)
        
        assert isinstance(reward, float)
        assert 0.0 <= reward <= 1.0
        assert reward > 0.7  # Should be high for good accuracy
    
    @pytest.mark.asyncio
    async def test_calculate_confidence_score(self):
        """Test confidence score calculation."""
        calculator = ExtendedRewardCalculator()
        
        # High consistency (similar values)
        consistent_rewards = {
            RewardType.TRADITIONAL: 0.8,
            RewardType.MULTI_MODAL: 0.82,
            RewardType.WORKFLOW_EFFICIENCY: 0.78
        }
        
        confidence = await calculator._calculate_confidence_score(consistent_rewards)
        
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
        
        # Low consistency (varied values)
        inconsistent_rewards = {
            RewardType.TRADITIONAL: 0.9,
            RewardType.MULTI_MODAL: 0.2,
            RewardType.WORKFLOW_EFFICIENCY: 0.7
        }
        
        low_confidence = await calculator._calculate_confidence_score(inconsistent_rewards)
        
        assert low_confidence < confidence  # Should be lower for inconsistent rewards
    
    @pytest.mark.asyncio
    async def test_generate_improvement_suggestions(self):
        """Test improvement suggestion generation."""
        calculator = ExtendedRewardCalculator()
        
        # Low performing components
        low_rewards = {
            RewardType.TRADITIONAL: 0.8,
            RewardType.MULTI_MODAL: 0.3,  # Low
            RewardType.WORKFLOW_EFFICIENCY: 0.4,  # Low
            RewardType.VISUAL_ENGAGEMENT: 0.2  # Low
        }
        
        suggestions = await calculator._generate_improvement_suggestions("user_1", low_rewards)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert len(suggestions) <= 5  # Should be limited
        
        # Check that suggestions are relevant to low-performing areas
        suggestion_text = " ".join(suggestions).lower()
        assert any(keyword in suggestion_text for keyword in ["visual", "workflow", "engagement"])
    
    @pytest.mark.asyncio
    async def test_generate_reward_explanation(self):
        """Test reward explanation generation."""
        calculator = ExtendedRewardCalculator()
        
        reward_components = {
            RewardType.TRADITIONAL: 0.8,
            RewardType.MULTI_MODAL: 0.7,
            RewardType.WORKFLOW_EFFICIENCY: 0.9
        }
        total_reward = 0.8
        
        explanation = await calculator._generate_reward_explanation(reward_components, total_reward)
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert "Total reward" in explanation
        assert "breakdown" in explanation.lower()
        
        # Should contain performance assessment
        assert any(word in explanation.lower() for word in ["excellent", "good", "moderate", "below"])
    
    def test_update_reward_weights(self):
        """Test reward weight updates."""
        calculator = ExtendedRewardCalculator()
        
        # Test valid weight update
        new_weights = {
            RewardType.TRADITIONAL: 0.4,
            RewardType.MULTI_MODAL: 0.3,
            RewardType.WORKFLOW_EFFICIENCY: 0.2,
            RewardType.VISUAL_ENGAGEMENT: 0.05,
            RewardType.RESEARCH_PRODUCTIVITY: 0.04,
            RewardType.PERSONALIZATION_ACCURACY: 0.01
        }
        
        calculator.update_reward_weights(new_weights)
        
        # Check that weights were normalized and updated
        current_weights = calculator.get_current_weights()
        assert abs(sum(calculator.reward_weights.values()) - 1.0) < 1e-6  # Should sum to 1
        assert calculator.reward_weights[RewardType.TRADITIONAL] == 0.4
    
    def test_get_reward_analytics(self):
        """Test reward analytics generation."""
        calculator = ExtendedRewardCalculator()
        
        # Add some reward history
        for i in range(5):
            calculator.reward_history["user_1"].append({
                'timestamp': datetime.now().isoformat(),
                'total_reward': 0.7 + i * 0.05,  # Improving trend
                'components': {
                    'traditional': 0.8,
                    'multi_modal': 0.6 + i * 0.1
                },
                'component_count': 2
            })
        
        analytics = calculator.get_reward_analytics("user_1")
        
        assert isinstance(analytics, dict)
        assert analytics["user_id"] == "user_1"
        assert analytics["total_calculations"] == 5
        assert isinstance(analytics["average_reward"], float)
        assert isinstance(analytics["recent_average"], float)
        assert isinstance(analytics["reward_trend"], float)
        assert analytics["reward_trend"] > 0  # Should detect improving trend
        assert "component_statistics" in analytics
    
    def test_get_reward_analytics_no_history(self):
        """Test reward analytics with no history."""
        calculator = ExtendedRewardCalculator()
        
        analytics = calculator.get_reward_analytics("new_user")
        
        assert "message" in analytics
        assert analytics["message"] == "No reward history available"
    
    @pytest.mark.asyncio
    async def test_store_reward_history(self):
        """Test reward history storage."""
        calculator = ExtendedRewardCalculator()
        
        reward_components = {
            RewardType.TRADITIONAL: 0.8,
            RewardType.MULTI_MODAL: 0.7
        }
        
        await calculator._store_reward_history("user_1", reward_components, 0.75)
        
        assert len(calculator.reward_history["user_1"]) == 1
        
        history_entry = calculator.reward_history["user_1"][0]
        assert history_entry["total_reward"] == 0.75
        assert "traditional" in history_entry["components"]
        assert "multi_modal" in history_entry["components"]
        assert history_entry["component_count"] == 2
    
    @pytest.mark.asyncio
    async def test_reward_history_limit(self):
        """Test that reward history is limited to prevent memory issues."""
        calculator = ExtendedRewardCalculator()
        
        # Add more than the limit (100 entries)
        for i in range(105):
            await calculator._store_reward_history("user_1", {RewardType.TRADITIONAL: 0.5}, 0.5)
        
        # Should be limited to 100 entries
        assert len(calculator.reward_history["user_1"]) == 100
    
    @pytest.mark.asyncio
    async def test_empty_inputs_handling(self):
        """Test handling of empty or None inputs."""
        calculator = ExtendedRewardCalculator()
        
        # Test with all None inputs
        result = await calculator.calculate_extended_reward("user_1")
        
        assert isinstance(result, ExtendedRewardCalculation)
        assert result.total_reward == 0.0
        assert len(result.reward_breakdown) == 0
        assert result.confidence_score == 0.0
    
    @pytest.mark.asyncio
    async def test_baseline_metrics_update(self):
        """Test that baseline metrics are updated correctly."""
        calculator = ExtendedRewardCalculator()
        
        # First calculation should establish baseline
        metrics1 = EfficiencyMetrics(
            time_efficiency=0.8,
            resource_utilization=0.7,
            task_completion_rate=0.9,
            user_satisfaction=0.8,
            bottleneck_frequency=0.2,
            context_switch_penalty=0.1,
            overall_efficiency=0.8
        )
        
        await calculator._calculate_workflow_efficiency_reward("user_1", metrics1)
        
        # Check baseline was set
        baseline = calculator.baseline_metrics["user_1"]
        assert "time_efficiency" in baseline
        
        # Second calculation should update baseline
        metrics2 = EfficiencyMetrics(
            time_efficiency=0.9,
            resource_utilization=0.8,
            task_completion_rate=0.95,
            user_satisfaction=0.85,
            bottleneck_frequency=0.15,
            context_switch_penalty=0.05,
            overall_efficiency=0.85
        )
        
        await calculator._calculate_workflow_efficiency_reward("user_1", metrics2)
        
        # Baseline should have moved toward new values
        new_baseline = calculator.baseline_metrics["user_1"]
        assert new_baseline["time_efficiency"] > baseline["time_efficiency"]
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in reward calculation."""
        calculator = ExtendedRewardCalculator()
        
        # Test with malformed input that might cause errors
        malformed_feedback = Mock()
        malformed_feedback.rating = "invalid"  # Should be numeric
        
        # Should handle errors gracefully and return default result
        result = await calculator.calculate_extended_reward(
            "user_1", 
            traditional_feedback=malformed_feedback
        )
        
        assert isinstance(result, ExtendedRewardCalculation)
        # Should return some default values even with errors
        assert result.total_reward >= 0.0
        assert isinstance(result.explanation, str)


class TestRewardDataClasses:
    """Test cases for reward data classes."""
    
    def test_multimodal_reward_creation(self):
        """Test MultiModalReward creation."""
        visual_elements = [
            VisualElement("chart_1", VisualElementType.CHART, "Chart content")
        ]
        
        reward = MultiModalReward(
            reward_id="mm_reward_1",
            user_id="user_1",
            content_type="research_paper",
            visual_elements=visual_elements,
            engagement_score=0.8,
            comprehension_score=0.75,
            interaction_duration=120.0,
            visual_attention_score=0.85,
            cross_modal_coherence=0.9
        )
        
        assert reward.reward_id == "mm_reward_1"
        assert reward.user_id == "user_1"
        assert reward.engagement_score == 0.8
        assert len(reward.visual_elements) == 1
        assert isinstance(reward.timestamp, datetime)
    
    def test_workflow_efficiency_reward_creation(self):
        """Test WorkflowEfficiencyReward creation."""
        metrics = EfficiencyMetrics(
            time_efficiency=0.8,
            resource_utilization=0.7,
            task_completion_rate=0.9,
            user_satisfaction=0.85,
            bottleneck_frequency=0.2,
            context_switch_penalty=0.1,
            overall_efficiency=0.8
        )
        
        reward = WorkflowEfficiencyReward(
            reward_id="wf_reward_1",
            user_id="user_1",
            workflow_id="workflow_1",
            efficiency_metrics=metrics,
            improvement_score=0.15,
            productivity_gain=0.2,
            time_savings=30.0,
            satisfaction_improvement=0.1
        )
        
        assert reward.reward_id == "wf_reward_1"
        assert reward.improvement_score == 0.15
        assert reward.efficiency_metrics == metrics
        assert isinstance(reward.timestamp, datetime)
    
    def test_visual_engagement_reward_creation(self):
        """Test VisualEngagementReward creation."""
        reward = VisualEngagementReward(
            reward_id="ve_reward_1",
            user_id="user_1",
            visual_content_id="content_1",
            engagement_level=EngagementLevel.HIGH,
            interaction_quality=0.8,
            visual_comprehension=0.85,
            attention_distribution={"important": 0.7, "secondary": 0.3},
            learning_effectiveness=0.75
        )
        
        assert reward.engagement_level == EngagementLevel.HIGH
        assert reward.interaction_quality == 0.8
        assert "important" in reward.attention_distribution
        assert isinstance(reward.timestamp, datetime)
    
    def test_extended_reward_calculation_creation(self):
        """Test ExtendedRewardCalculation creation."""
        reward_breakdown = {
            RewardType.TRADITIONAL: 0.8,
            RewardType.MULTI_MODAL: 0.7
        }
        
        calculation = ExtendedRewardCalculation(
            total_reward=0.75,
            reward_breakdown=reward_breakdown,
            confidence_score=0.85,
            explanation="Good performance overall",
            contributing_factors=["Traditional: 0.8", "Multi-modal: 0.7"],
            improvement_suggestions=["Focus on visual engagement"]
        )
        
        assert calculation.total_reward == 0.75
        assert len(calculation.reward_breakdown) == 2
        assert calculation.confidence_score == 0.85
        assert "Good performance" in calculation.explanation
        assert len(calculation.contributing_factors) == 2
        assert len(calculation.improvement_suggestions) == 1