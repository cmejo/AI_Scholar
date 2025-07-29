"""
Tests for Feedback Analyzer Service.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from services.feedback_analyzer import (
    FeedbackAnalyzer,
    FeedbackItem,
    FeedbackType,
    ImprovementAction,
    ImprovementType,
    ABTestVariant,
    ABTestResult
)

@pytest.fixture
async def feedback_analyzer():
    """Create a FeedbackAnalyzer instance for testing."""
    analyzer = FeedbackAnalyzer()
    
    # Mock dependencies
    analyzer.redis_client = AsyncMock()
    
    return analyzer

@pytest.fixture
def sample_feedback_item():
    """Sample feedback item for testing."""
    return FeedbackItem(
        feedback_id="feedback_123",
        user_id="user_456",
        message_id="message_789",
        feedback_type=FeedbackType.RATING,
        feedback_value={"rating": 4, "comment": "Good response"},
        context={"query": "test query", "response_length": 150},
        timestamp=datetime.now()
    )

@pytest.fixture
def sample_feedback_data():
    """Sample feedback data for testing."""
    base_time = datetime.now()
    return [
        {
            'feedback_id': 'fb1',
            'user_id': 'user1',
            'message_id': 'msg1',
            'feedback_type': 'rating',
            'feedback_value': {'rating': 4},
            'created_at': base_time - timedelta(hours=1),
            'processed': True
        },
        {
            'feedback_id': 'fb2',
            'user_id': 'user2',
            'message_id': 'msg2',
            'feedback_type': 'rating',
            'feedback_value': {'rating': 2},
            'created_at': base_time - timedelta(hours=2),
            'processed': True
        },
        {
            'feedback_id': 'fb3',
            'user_id': 'user3',
            'message_id': 'msg3',
            'feedback_type': 'correction',
            'feedback_value': {'correction': 'This is wrong'},
            'created_at': base_time - timedelta(hours=3),
            'processed': False
        },
        {
            'feedback_id': 'fb4',
            'user_id': 'user1',
            'message_id': 'msg4',
            'feedback_type': 'relevance',
            'feedback_value': {'relevant': False},
            'created_at': base_time - timedelta(hours=4),
            'processed': True
        }
    ]

class TestFeedbackAnalyzer:
    """Test cases for FeedbackAnalyzer service."""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test FeedbackAnalyzer initialization."""
        analyzer = FeedbackAnalyzer()
        
        with patch('services.feedback_analyzer.get_redis_client') as mock_redis:
            mock_redis.return_value = AsyncMock()
            
            await analyzer.initialize()
            
            assert analyzer.redis_client is not None
            assert analyzer.feedback_cache_ttl == 3600
            assert analyzer.min_feedback_threshold == 10
            assert analyzer.improvement_confidence_threshold == 0.7
    
    @pytest.mark.asyncio
    async def test_process_feedback(self, feedback_analyzer, sample_feedback_item):
        """Test feedback processing."""
        # Mock database operations
        with patch.object(feedback_analyzer, '_store_feedback') as mock_store, \
             patch.object(feedback_analyzer, '_calculate_feedback_impact', return_value=0.8) as mock_impact, \
             patch.object(feedback_analyzer, '_update_feedback_status') as mock_update, \
             patch.object(feedback_analyzer, '_check_improvement_trigger') as mock_trigger:
            
            result = await feedback_analyzer.process_feedback(sample_feedback_item)
            
            assert result is True
            assert sample_feedback_item.impact_score == 0.8
            mock_store.assert_called_once()
            mock_impact.assert_called_once()
            mock_update.assert_called_once()
            mock_trigger.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_calculate_feedback_impact(self, feedback_analyzer):
        """Test feedback impact calculation."""
        # Test rating feedback
        rating_feedback = FeedbackItem(
            feedback_id="fb1",
            user_id="user1",
            message_id="msg1",
            feedback_type=FeedbackType.RATING,
            feedback_value={"rating": 2},  # Low rating
            context={},
            timestamp=datetime.now()
        )
        
        with patch.object(feedback_analyzer, '_get_user_feedback_count', return_value=5):
            impact = await feedback_analyzer._calculate_feedback_impact(rating_feedback)
            assert isinstance(impact, float)
            assert 0 <= impact <= 1
            assert impact > 0.3  # Should be higher for extreme rating
        
        # Test correction feedback
        correction_feedback = FeedbackItem(
            feedback_id="fb2",
            user_id="user2",
            message_id="msg2",
            feedback_type=FeedbackType.CORRECTION,
            feedback_value={"correction": "This is wrong"},
            context={},
            timestamp=datetime.now()
        )
        
        with patch.object(feedback_analyzer, '_get_user_feedback_count', return_value=15):
            impact = await feedback_analyzer._calculate_feedback_impact(correction_feedback)
            assert impact > 0.8  # Corrections should have high impact
    
    @pytest.mark.asyncio
    async def test_analyze_feedback_patterns(self, feedback_analyzer, sample_feedback_data):
        """Test feedback pattern analysis."""
        with patch.object(feedback_analyzer, '_get_feedback_data', return_value=sample_feedback_data):
            
            # Mock Redis cache
            feedback_analyzer.redis_client.setex = AsyncMock()
            
            analysis = await feedback_analyzer.analyze_feedback_patterns(time_window_days=30)
            
            assert isinstance(analysis, dict)
            assert 'total_feedback' in analysis
            assert 'feedback_by_type' in analysis
            assert 'rating_trends' in analysis
            assert 'common_issues' in analysis
            assert 'user_satisfaction' in analysis
            assert 'improvement_opportunities' in analysis
            
            assert analysis['total_feedback'] == 4
            assert 'rating' in analysis['feedback_by_type']
            assert 'correction' in analysis['feedback_by_type']
    
    @pytest.mark.asyncio
    async def test_analyze_rating_trends(self, feedback_analyzer, sample_feedback_data):
        """Test rating trend analysis."""
        rating_trends = await feedback_analyzer._analyze_rating_trends(sample_feedback_data)
        
        assert isinstance(rating_trends, dict)
        assert 'average_rating' in rating_trends
        assert 'rating_distribution' in rating_trends
        assert 'total_ratings' in rating_trends
        assert 'trend' in rating_trends
        
        # Should calculate average of ratings 4 and 2 = 3.0
        assert rating_trends['average_rating'] == 3.0
        assert rating_trends['total_ratings'] == 2
        assert rating_trends['trend'] == 'declining'  # Average < 3.5
    
    @pytest.mark.asyncio
    async def test_identify_common_issues(self, feedback_analyzer, sample_feedback_data):
        """Test common issue identification."""
        issues = await feedback_analyzer._identify_common_issues(sample_feedback_data)
        
        assert isinstance(issues, list)
        
        # Should identify accuracy issue from correction feedback
        accuracy_issues = [i for i in issues if i['issue_type'] == 'accuracy']
        assert len(accuracy_issues) > 0
        assert accuracy_issues[0]['severity'] == 'high'
    
    @pytest.mark.asyncio
    async def test_calculate_user_satisfaction(self, feedback_analyzer, sample_feedback_data):
        """Test user satisfaction calculation."""
        satisfaction = await feedback_analyzer._calculate_user_satisfaction(sample_feedback_data)
        
        assert isinstance(satisfaction, dict)
        assert 'satisfaction_score' in satisfaction
        assert 'nps_score' in satisfaction
        
        # Should calculate based on ratings 4 and 2
        # Satisfaction: 1 rating >= 4 out of 2 = 0.5
        assert satisfaction['satisfaction_score'] == 0.5
        
        # NPS: 1 promoter (>=4), 1 detractor (<=2) out of 2 = 0.0
        assert satisfaction['nps_score'] == 0.0
    
    @pytest.mark.asyncio
    async def test_identify_improvement_opportunities(self, feedback_analyzer, sample_feedback_data):
        """Test improvement opportunity identification."""
        opportunities = await feedback_analyzer._identify_improvement_opportunities(sample_feedback_data)
        
        assert isinstance(opportunities, list)
        
        # Should identify retrieval improvement from relevance feedback
        retrieval_opportunities = [o for o in opportunities if o['opportunity_type'] == 'retrieval_improvement']
        assert len(retrieval_opportunities) > 0
        assert retrieval_opportunities[0]['priority'] == 'high'
    
    @pytest.mark.asyncio
    async def test_generate_improvement_actions(self, feedback_analyzer):
        """Test improvement action generation."""
        # Sample feedback analysis
        feedback_analysis = {
            'rating_trends': {
                'average_rating': 3.0,
                'trend': 'declining'
            },
            'common_issues': [
                {
                    'issue_type': 'accuracy',
                    'frequency': 5,
                    'severity': 'high',
                    'description': '5 accuracy corrections reported'
                }
            ],
            'improvement_opportunities': [
                {
                    'opportunity_type': 'personalization',
                    'priority': 'medium',
                    'description': 'Personalization improvements needed',
                    'expected_impact': 0.3
                }
            ]
        }
        
        actions = await feedback_analyzer.generate_improvement_actions(feedback_analysis)
        
        assert isinstance(actions, list)
        assert len(actions) > 0
        
        # Check action structure
        for action in actions:
            assert isinstance(action, ImprovementAction)
            assert action.action_id
            assert isinstance(action.improvement_type, ImprovementType)
            assert action.description
            assert action.target_component
            assert isinstance(action.parameters, dict)
            assert 0 <= action.expected_impact <= 1
            assert 0 <= action.confidence <= 1
            assert action.priority in ['high', 'medium', 'low']
    
    @pytest.mark.asyncio
    async def test_apply_improvement_action(self, feedback_analyzer):
        """Test improvement action application."""
        action = ImprovementAction(
            action_id="test_action_123",
            improvement_type=ImprovementType.RETRIEVAL_TUNING,
            description="Test retrieval tuning",
            target_component="retrieval_engine",
            parameters={"relevance_threshold": 0.8},
            expected_impact=0.5,
            confidence=0.8,
            priority="high",
            created_at=datetime.now()
        )
        
        # Mock Redis operations
        feedback_analyzer.redis_client.setex = AsyncMock(return_value=True)
        
        with patch.object(feedback_analyzer, '_update_action_status') as mock_update, \
             patch.object(feedback_analyzer, '_log_improvement_application') as mock_log:
            
            result = await feedback_analyzer.apply_improvement_action(action)
            
            assert result is True
            mock_update.assert_called_once()
            mock_log.assert_called_once()
            feedback_analyzer.redis_client.setex.assert_called()
    
    @pytest.mark.asyncio
    async def test_create_ab_test(self, feedback_analyzer):
        """Test A/B test creation."""
        variants = [
            ABTestVariant(
                variant_id="variant_a",
                name="Control",
                description="Current system",
                parameters={},
                traffic_percentage=50.0
            ),
            ABTestVariant(
                variant_id="variant_b",
                name="Treatment",
                description="Improved system",
                parameters={"improvement": True},
                traffic_percentage=50.0
            )
        ]
        
        # Mock Redis operations
        feedback_analyzer.redis_client.setex = AsyncMock(return_value=True)
        
        test_id = await feedback_analyzer.create_ab_test("test_improvement", variants, "satisfaction_score")
        
        assert test_id.startswith("ab_test_test_improvement_")
        
        # Should have called setex for test config and each variant
        assert feedback_analyzer.redis_client.setex.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_assign_ab_test_variant(self, feedback_analyzer):
        """Test A/B test variant assignment."""
        test_id = "test_123"
        user_id = "user_456"
        
        # Mock test configuration
        test_config = {
            'test_id': test_id,
            'active': True,
            'variants': [
                {'variant_id': 'variant_a', 'traffic_percentage': 60.0},
                {'variant_id': 'variant_b', 'traffic_percentage': 40.0}
            ]
        }
        
        feedback_analyzer.redis_client.get = AsyncMock(side_effect=[
            json.dumps(test_config),  # Test config
            None  # No existing assignment
        ])
        feedback_analyzer.redis_client.setex = AsyncMock(return_value=True)
        
        with patch('random.random', return_value=0.3):  # Should assign to variant_a (30% < 60%)
            variant_id = await feedback_analyzer.assign_ab_test_variant(test_id, user_id)
            
            assert variant_id == 'variant_a'
            feedback_analyzer.redis_client.setex.assert_called()
    
    @pytest.mark.asyncio
    async def test_record_ab_test_metric(self, feedback_analyzer):
        """Test A/B test metric recording."""
        test_id = "test_123"
        variant_id = "variant_a"
        metric_value = 0.85
        
        # Mock existing metrics
        existing_metrics = {
            'samples': [{'value': 0.8, 'timestamp': '2023-01-01T00:00:00'}],
            'count': 1
        }
        
        feedback_analyzer.redis_client.get = AsyncMock(return_value=json.dumps(existing_metrics))
        feedback_analyzer.redis_client.setex = AsyncMock(return_value=True)
        
        result = await feedback_analyzer.record_ab_test_metric(test_id, variant_id, metric_value)
        
        assert result is True
        feedback_analyzer.redis_client.setex.assert_called()
        
        # Check that the call included the new metric
        call_args = feedback_analyzer.redis_client.setex.call_args
        updated_metrics = json.loads(call_args[0][2])
        assert updated_metrics['count'] == 2
        assert len(updated_metrics['samples']) == 2
    
    @pytest.mark.asyncio
    async def test_analyze_ab_test_results(self, feedback_analyzer):
        """Test A/B test result analysis."""
        test_id = "test_123"
        
        # Mock test configuration
        test_config = {
            'test_id': test_id,
            'metric_name': 'satisfaction_score',
            'variants': [
                {'variant_id': 'variant_a'},
                {'variant_id': 'variant_b'}
            ]
        }
        
        # Mock metrics data
        variant_a_metrics = {
            'samples': [{'value': 0.8} for _ in range(50)],  # 50 samples
            'count': 50
        }
        
        variant_b_metrics = {
            'samples': [{'value': 0.85} for _ in range(50)],  # 50 samples
            'count': 50
        }
        
        feedback_analyzer.redis_client.get = AsyncMock(side_effect=[
            json.dumps(test_config),
            json.dumps(variant_a_metrics),
            json.dumps(variant_b_metrics)
        ])
        
        results = await feedback_analyzer.analyze_ab_test_results(test_id)
        
        assert isinstance(results, list)
        assert len(results) == 2
        
        # Check result structure
        for result in results:
            assert isinstance(result, ABTestResult)
            assert result.test_id == test_id
            assert result.variant_id in ['variant_a', 'variant_b']
            assert result.metric_name == 'satisfaction_score'
            assert result.sample_size == 50
            assert isinstance(result.confidence_interval, tuple)
            assert isinstance(result.statistical_significance, bool)
    
    @pytest.mark.asyncio
    async def test_measure_improvement_effectiveness(self, feedback_analyzer):
        """Test improvement effectiveness measurement."""
        action = ImprovementAction(
            action_id="test_action_123",
            improvement_type=ImprovementType.RETRIEVAL_TUNING,
            description="Test action",
            target_component="retrieval",
            parameters={},
            expected_impact=0.5,
            confidence=0.8,
            priority="high",
            created_at=datetime.now()
        )
        
        # Mock performance metrics
        baseline_metrics = {'avg_response_time': 2.0, 'avg_satisfaction': 3.5}
        post_metrics = {'avg_response_time': 1.8, 'avg_satisfaction': 4.0}
        
        with patch.object(feedback_analyzer, '_get_performance_metrics', side_effect=[baseline_metrics, post_metrics]), \
             patch.object(feedback_analyzer, '_store_improvement_effectiveness') as mock_store:
            
            effectiveness = await feedback_analyzer.measure_improvement_effectiveness(action)
            
            assert isinstance(effectiveness, dict)
            assert 'avg_response_time' in effectiveness
            assert 'avg_satisfaction' in effectiveness
            
            # Response time improved by 10% (1.8 vs 2.0)
            assert abs(effectiveness['avg_response_time'] - (-0.1)) < 0.01
            
            # Satisfaction improved by ~14.3% (4.0 vs 3.5)
            assert effectiveness['avg_satisfaction'] > 0.1
            
            mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, feedback_analyzer):
        """Test error handling in feedback analysis."""
        # Test with invalid feedback data
        with patch.object(feedback_analyzer, '_get_feedback_data', side_effect=Exception("Database error")):
            analysis = await feedback_analyzer.analyze_feedback_patterns()
            assert analysis == {}
        
        # Test with invalid improvement action
        invalid_action = ImprovementAction(
            action_id="invalid",
            improvement_type=ImprovementType.RETRIEVAL_TUNING,
            description="Invalid action",
            target_component="invalid",
            parameters={},
            expected_impact=0.5,
            confidence=0.8,
            priority="high",
            created_at=datetime.now()
        )
        
        with patch.object(feedback_analyzer, '_apply_retrieval_tuning', side_effect=Exception("Apply error")):
            result = await feedback_analyzer.apply_improvement_action(invalid_action)
            assert result is False
    
    @pytest.mark.asyncio
    async def test_feedback_type_enum(self):
        """Test FeedbackType enum."""
        assert FeedbackType.RATING.value == "rating"
        assert FeedbackType.CORRECTION.value == "correction"
        assert FeedbackType.PREFERENCE.value == "preference"
        assert FeedbackType.RELEVANCE.value == "relevance"
        assert FeedbackType.ACCURACY.value == "accuracy"
        assert FeedbackType.COMPLETENESS.value == "completeness"
    
    @pytest.mark.asyncio
    async def test_improvement_type_enum(self):
        """Test ImprovementType enum."""
        assert ImprovementType.RETRIEVAL_TUNING.value == "retrieval_tuning"
        assert ImprovementType.RESPONSE_GENERATION.value == "response_generation"
        assert ImprovementType.RANKING_ADJUSTMENT.value == "ranking_adjustment"
        assert ImprovementType.PERSONALIZATION.value == "personalization"
        assert ImprovementType.KNOWLEDGE_UPDATE.value == "knowledge_update"

if __name__ == "__main__":
    pytest.main([__file__])