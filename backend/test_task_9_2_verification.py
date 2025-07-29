"""
Verification script for Task 9.2: Build feedback-driven improvement system
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from services.feedback_analyzer import (
    FeedbackAnalyzer,
    FeedbackItem,
    FeedbackType,
    ImprovementAction,
    ImprovementType,
    ABTestVariant,
    ABTestResult
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_feedback_analyzer_initialization():
    """Test FeedbackAnalyzer initialization."""
    print("Testing FeedbackAnalyzer initialization...")
    
    analyzer = FeedbackAnalyzer()
    
    # Test basic properties
    assert analyzer.feedback_cache_ttl == 3600
    assert analyzer.min_feedback_threshold == 10
    assert analyzer.improvement_confidence_threshold == 0.7
    assert analyzer.ab_test_duration_days == 14
    
    print("✓ FeedbackAnalyzer initialization test passed")

async def test_feedback_processing():
    """Test feedback processing functionality."""
    print("Testing feedback processing...")
    
    analyzer = FeedbackAnalyzer()
    
    # Mock Redis client
    class MockRedis:
        def __init__(self):
            self.data = {}
        async def setex(self, key, ttl, value):
            self.data[key] = value
            return True
        async def get(self, key):
            return self.data.get(key)
        async def lpush(self, key, value):
            return 1
    
    analyzer.redis_client = MockRedis()
    
    # Mock database operations
    async def mock_store_feedback(feedback_item):
        feedback_item.feedback_id = "test_feedback_123"
    async def mock_get_user_feedback_count(user_id):
        return 5
    async def mock_update_feedback_status(feedback_id, processed):
        pass
    async def mock_check_improvement_trigger(feedback_item):
        pass
    
    analyzer._store_feedback = mock_store_feedback
    analyzer._get_user_feedback_count = mock_get_user_feedback_count
    analyzer._update_feedback_status = mock_update_feedback_status
    analyzer._check_improvement_trigger = mock_check_improvement_trigger
    
    # Create test feedback item
    feedback_item = FeedbackItem(
        feedback_id="",
        user_id="test_user",
        message_id="test_message",
        feedback_type=FeedbackType.RATING,
        feedback_value={"rating": 4},
        context={"query": "test query"},
        timestamp=datetime.now()
    )
    
    # Process feedback
    success = await analyzer.process_feedback(feedback_item)
    
    assert success is True
    assert feedback_item.feedback_id == "test_feedback_123"
    assert feedback_item.impact_score > 0
    
    print("✓ Feedback processing test passed")

async def test_feedback_impact_calculation():
    """Test feedback impact calculation."""
    print("Testing feedback impact calculation...")
    
    analyzer = FeedbackAnalyzer()
    
    # Mock user feedback count
    async def mock_get_user_feedback_count(user_id):
        return 5
    analyzer._get_user_feedback_count = mock_get_user_feedback_count
    
    # Test different feedback types
    test_cases = [
        (FeedbackType.RATING, {"rating": 5}, 0.3),  # Normal rating
        (FeedbackType.RATING, {"rating": 1}, 0.45),  # Extreme rating (higher impact)
        (FeedbackType.CORRECTION, {"correction": "Wrong"}, 0.8),  # High impact
        (FeedbackType.ACCURACY, {"accurate": False}, 0.9),  # Very high impact
    ]
    
    for feedback_type, feedback_value, expected_min_impact in test_cases:
        feedback_item = FeedbackItem(
            feedback_id="test",
            user_id="test_user",
            message_id="test_message",
            feedback_type=feedback_type,
            feedback_value=feedback_value,
            context={},
            timestamp=datetime.now()
        )
        
        impact = await analyzer._calculate_feedback_impact(feedback_item)
        
        assert isinstance(impact, float)
        assert 0 <= impact <= 1
        assert impact >= expected_min_impact - 0.01, f"Impact {impact} should be >= {expected_min_impact} for {feedback_type}"
    
    print("✓ Feedback impact calculation test passed")

async def test_feedback_analysis():
    """Test feedback analysis functionality."""
    print("Testing feedback analysis...")
    
    analyzer = FeedbackAnalyzer()
    
    # Mock Redis client
    class MockRedis:
        def __init__(self):
            self.data = {}
        async def setex(self, key, ttl, value):
            self.data[key] = value
            return True
    
    analyzer.redis_client = MockRedis()
    
    # Sample feedback data
    sample_feedback_data = [
        {
            'feedback_id': 'fb1',
            'user_id': 'user1',
            'message_id': 'msg1',
            'feedback_type': 'rating',
            'feedback_value': {'rating': 4},
            'created_at': datetime.now() - timedelta(hours=1),
            'processed': True
        },
        {
            'feedback_id': 'fb2',
            'user_id': 'user2',
            'message_id': 'msg2',
            'feedback_type': 'rating',
            'feedback_value': {'rating': 2},
            'created_at': datetime.now() - timedelta(hours=2),
            'processed': True
        },
        {
            'feedback_id': 'fb3',
            'user_id': 'user3',
            'message_id': 'msg3',
            'feedback_type': 'correction',
            'feedback_value': {'correction': 'This is wrong'},
            'created_at': datetime.now() - timedelta(hours=3),
            'processed': False
        }
    ]
    
    # Mock database query
    async def mock_get_feedback_data(time_window_days):
        return sample_feedback_data
    analyzer._get_feedback_data = mock_get_feedback_data
    
    # Analyze feedback patterns
    analysis = await analyzer.analyze_feedback_patterns(time_window_days=30)
    
    # Verify analysis structure
    assert isinstance(analysis, dict)
    assert 'total_feedback' in analysis
    assert 'feedback_by_type' in analysis
    assert 'rating_trends' in analysis
    assert 'common_issues' in analysis
    assert 'user_satisfaction' in analysis
    assert 'improvement_opportunities' in analysis
    
    # Verify analysis content
    assert analysis['total_feedback'] == 3
    assert 'rating' in analysis['feedback_by_type']
    assert 'correction' in analysis['feedback_by_type']
    
    # Verify rating trends
    rating_trends = analysis['rating_trends']
    assert 'average_rating' in rating_trends
    assert 'rating_distribution' in rating_trends
    assert rating_trends['average_rating'] == 3.0  # (4 + 2) / 2
    
    # Verify user satisfaction
    satisfaction = analysis['user_satisfaction']
    assert 'satisfaction_score' in satisfaction
    assert 'nps_score' in satisfaction
    assert satisfaction['satisfaction_score'] == 0.5  # 1 out of 2 ratings >= 4
    
    print("✓ Feedback analysis test passed")

async def test_improvement_action_generation():
    """Test improvement action generation."""
    print("Testing improvement action generation...")
    
    analyzer = FeedbackAnalyzer()
    
    # Sample feedback analysis with issues
    feedback_analysis = {
        'rating_trends': {
            'average_rating': 3.0,  # Low rating triggers improvement
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
                'opportunity_type': 'retrieval_improvement',
                'priority': 'high',
                'description': 'Retrieval improvements needed',
                'expected_impact': 0.5
            }
        ]
    }
    
    # Generate improvement actions
    actions = await analyzer.generate_improvement_actions(feedback_analysis)
    
    assert isinstance(actions, list)
    assert len(actions) > 0
    
    # Verify action structure
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
    
    # Should generate actions for accuracy issues and retrieval improvements
    action_types = [action.improvement_type for action in actions]
    assert ImprovementType.KNOWLEDGE_UPDATE in action_types  # For accuracy issues
    assert ImprovementType.RETRIEVAL_TUNING in action_types  # For retrieval improvements
    
    print("✓ Improvement action generation test passed")

async def test_improvement_action_application():
    """Test improvement action application."""
    print("Testing improvement action application...")
    
    analyzer = FeedbackAnalyzer()
    
    # Mock Redis client
    class MockRedis:
        def __init__(self):
            self.data = {}
        async def setex(self, key, ttl, value):
            self.data[key] = value
            return True
        async def get(self, key):
            return self.data.get(key)
    
    analyzer.redis_client = MockRedis()
    
    # Mock database operations
    async def mock_update_action_status(action_id, applied):
        pass
    async def mock_log_improvement_application(action):
        pass
    
    analyzer._update_action_status = mock_update_action_status
    analyzer._log_improvement_application = mock_log_improvement_application
    
    # Test different improvement types
    test_actions = [
        ImprovementAction(
            action_id="retrieval_test",
            improvement_type=ImprovementType.RETRIEVAL_TUNING,
            description="Test retrieval tuning",
            target_component="retrieval_engine",
            parameters={"relevance_threshold": 0.8},
            expected_impact=0.5,
            confidence=0.8,
            priority="high",
            created_at=datetime.now()
        ),
        ImprovementAction(
            action_id="personalization_test",
            improvement_type=ImprovementType.PERSONALIZATION,
            description="Test personalization",
            target_component="personalization_engine",
            parameters={"personalization_level": "enhanced"},
            expected_impact=0.3,
            confidence=0.7,
            priority="medium",
            created_at=datetime.now()
        )
    ]
    
    for action in test_actions:
        success = await analyzer.apply_improvement_action(action)
        
        assert success is True
        
        # Verify configuration was stored in Redis
        if action.improvement_type == ImprovementType.RETRIEVAL_TUNING:
            key = f"retrieval_tuning:{action.action_id}"
        elif action.improvement_type == ImprovementType.PERSONALIZATION:
            key = f"personalization_improvement:{action.action_id}"
        
        stored_data = await analyzer.redis_client.get(key)
        assert stored_data is not None
        
        config = json.loads(stored_data)
        assert config['action_id'] == action.action_id
        assert config['parameters'] == action.parameters
    
    print("✓ Improvement action application test passed")

async def test_ab_testing():
    """Test A/B testing functionality."""
    print("Testing A/B testing...")
    
    analyzer = FeedbackAnalyzer()
    
    # Mock Redis client
    class MockRedis:
        def __init__(self):
            self.data = {}
        async def setex(self, key, ttl, value):
            self.data[key] = value
            return True
        async def get(self, key):
            return self.data.get(key)
    
    analyzer.redis_client = MockRedis()
    
    # Create test variants
    variants = [
        ABTestVariant(
            variant_id="control",
            name="Control",
            description="Current system",
            parameters={},
            traffic_percentage=50.0
        ),
        ABTestVariant(
            variant_id="treatment",
            name="Treatment",
            description="Improved system",
            parameters={"improvement": True},
            traffic_percentage=50.0
        )
    ]
    
    # Create A/B test
    test_id = await analyzer.create_ab_test("test_improvement", variants, "satisfaction_score")
    
    assert test_id.startswith("ab_test_test_improvement_")
    
    # Test user assignment
    import random
    random.seed(42)  # For reproducible results
    
    user_assignments = {}
    for i in range(10):
        user_id = f"user_{i}"
        variant_id = await analyzer.assign_ab_test_variant(test_id, user_id)
        user_assignments[user_id] = variant_id
        
        assert variant_id in ["control", "treatment"]
    
    # Verify traffic distribution is reasonable (not exactly 50/50 due to randomness)
    control_count = sum(1 for v in user_assignments.values() if v == "control")
    treatment_count = sum(1 for v in user_assignments.values() if v == "treatment")
    
    assert control_count > 0
    assert treatment_count > 0
    assert control_count + treatment_count == 10
    
    # Test metric recording (record multiple metrics per user to meet minimum sample size)
    for user_id, variant_id in user_assignments.items():
        for i in range(15):  # Record 15 metrics per user to meet minimum sample size of 10
            metric_value = 0.8 if variant_id == "control" else 0.85
            metric_value += (i * 0.01)  # Add slight variation
            success = await analyzer.record_ab_test_metric(test_id, variant_id, metric_value)
            assert success is True
    
    # Test result analysis
    results = await analyzer.analyze_ab_test_results(test_id)
    
    assert isinstance(results, list)
    assert len(results) == 2  # Two variants
    
    for result in results:
        assert isinstance(result, ABTestResult)
        assert result.test_id == test_id
        assert result.variant_id in ["control", "treatment"]
        assert result.metric_name == "satisfaction_score"
        assert result.sample_size > 0
        assert isinstance(result.confidence_interval, tuple)
        assert len(result.confidence_interval) == 2
    
    print("✓ A/B testing test passed")

async def test_effectiveness_measurement():
    """Test improvement effectiveness measurement."""
    print("Testing effectiveness measurement...")
    
    analyzer = FeedbackAnalyzer()
    
    # Mock Redis client
    class MockRedis:
        def __init__(self):
            self.data = {}
        async def setex(self, key, ttl, value):
            self.data[key] = value
            return True
    
    analyzer.redis_client = MockRedis()
    
    # Create test action
    action = ImprovementAction(
        action_id="test_action",
        improvement_type=ImprovementType.RETRIEVAL_TUNING,
        description="Test action",
        target_component="retrieval",
        parameters={},
        expected_impact=0.4,
        confidence=0.8,
        priority="high",
        created_at=datetime.now() - timedelta(days=7)
    )
    
    # Mock performance metrics
    baseline_metrics = {'avg_response_time': 2.0, 'avg_satisfaction': 3.5}
    post_metrics = {'avg_response_time': 1.8, 'avg_satisfaction': 4.0}
    
    async def mock_get_performance_metrics(start_date, end_date):
        return baseline_metrics if start_date < action.created_at else post_metrics
    
    async def mock_store_improvement_effectiveness(action_id, effectiveness):
        pass
    
    analyzer._get_performance_metrics = mock_get_performance_metrics
    analyzer._store_improvement_effectiveness = mock_store_improvement_effectiveness
    
    # Measure effectiveness
    effectiveness = await analyzer.measure_improvement_effectiveness(action)
    
    assert isinstance(effectiveness, dict)
    assert 'avg_response_time' in effectiveness
    assert 'avg_satisfaction' in effectiveness
    
    # Response time should improve (decrease) by 10%
    assert abs(effectiveness['avg_response_time'] - (-0.1)) < 0.01
    
    # Satisfaction should improve (increase) by ~14.3%
    assert effectiveness['avg_satisfaction'] > 0.1
    
    print("✓ Effectiveness measurement test passed")

async def test_feedback_driven_improvements():
    """Test end-to-end feedback-driven improvements."""
    print("Testing feedback-driven improvements...")
    
    analyzer = FeedbackAnalyzer()
    
    # Mock Redis client
    class MockRedis:
        def __init__(self):
            self.data = {}
        async def setex(self, key, ttl, value):
            self.data[key] = value
            return True
        async def get(self, key):
            return self.data.get(key)
        async def lpush(self, key, value):
            return 1
    
    analyzer.redis_client = MockRedis()
    
    # Mock database operations
    async def mock_store_feedback(feedback_item):
        feedback_item.feedback_id = f"fb_{len(feedback_items)}"
    async def mock_get_user_feedback_count(user_id):
        return 5
    async def mock_update_feedback_status(feedback_id, processed):
        pass
    async def mock_check_improvement_trigger(feedback_item):
        pass
    async def mock_get_feedback_data(time_window_days):
        return [
            {
                'feedback_id': 'fb1',
                'user_id': 'user1',
                'feedback_type': 'rating',
                'feedback_value': {'rating': 2},
                'created_at': datetime.now(),
                'processed': True
            },
            {
                'feedback_id': 'fb2',
                'user_id': 'user2',
                'feedback_type': 'correction',
                'feedback_value': {'correction': 'Wrong answer'},
                'created_at': datetime.now(),
                'processed': True
            }
        ]
    async def mock_update_action_status(action_id, applied):
        pass
    async def mock_log_improvement_application(action):
        pass
    
    analyzer._store_feedback = mock_store_feedback
    analyzer._get_user_feedback_count = mock_get_user_feedback_count
    analyzer._update_feedback_status = mock_update_feedback_status
    analyzer._check_improvement_trigger = mock_check_improvement_trigger
    analyzer._get_feedback_data = mock_get_feedback_data
    analyzer._update_action_status = mock_update_action_status
    analyzer._log_improvement_application = mock_log_improvement_application
    
    # Step 1: Process feedback
    feedback_items = [
        FeedbackItem(
            feedback_id="",
            user_id="user1",
            message_id="msg1",
            feedback_type=FeedbackType.RATING,
            feedback_value={"rating": 2},
            context={},
            timestamp=datetime.now()
        ),
        FeedbackItem(
            feedback_id="",
            user_id="user2",
            message_id="msg2",
            feedback_type=FeedbackType.CORRECTION,
            feedback_value={"correction": "Wrong answer"},
            context={},
            timestamp=datetime.now()
        )
    ]
    
    for feedback in feedback_items:
        success = await analyzer.process_feedback(feedback)
        assert success is True
        assert feedback.impact_score > 0
    
    # Step 2: Analyze feedback patterns
    analysis = await analyzer.analyze_feedback_patterns()
    assert analysis['total_feedback'] == 2
    assert len(analysis['common_issues']) > 0
    
    # Step 3: Generate improvement actions
    actions = await analyzer.generate_improvement_actions(analysis)
    assert len(actions) > 0
    
    # Step 4: Apply improvement actions
    for action in actions[:2]:  # Apply first 2 actions
        success = await analyzer.apply_improvement_action(action)
        assert success is True
    
    print("✓ Feedback-driven improvements test passed")

async def main():
    """Run all verification tests."""
    print("TASK 9.2 VERIFICATION: Feedback-driven improvement system")
    print("=" * 60)
    
    try:
        await test_feedback_analyzer_initialization()
        await test_feedback_processing()
        await test_feedback_impact_calculation()
        await test_feedback_analysis()
        await test_improvement_action_generation()
        await test_improvement_action_application()
        await test_ab_testing()
        await test_effectiveness_measurement()
        await test_feedback_driven_improvements()
        
        print("\n" + "=" * 60)
        print("✓ ALL TASK 9.2 VERIFICATION TESTS PASSED!")
        print("✓ Feedback-driven improvement system is working correctly")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ TASK 9.2 VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)