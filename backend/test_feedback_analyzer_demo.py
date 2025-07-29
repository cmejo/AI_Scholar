"""
Demo script for Feedback Analyzer Service functionality.
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
    ABTestVariant
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockRedisClient:
    """Mock Redis client for demo."""
    
    def __init__(self):
        self.data = {}
    
    async def setex(self, key, ttl, value):
        self.data[key] = value
        return True
    
    async def get(self, key):
        return self.data.get(key)
    
    async def lpush(self, key, value):
        if key not in self.data:
            self.data[key] = []
        self.data[key].append(value)
        return len(self.data[key])

async def demo_feedback_processing():
    """Demonstrate feedback processing functionality."""
    print("\n" + "="*60)
    print("FEEDBACK PROCESSING DEMO")
    print("="*60)
    
    # Initialize feedback analyzer
    analyzer = FeedbackAnalyzer()
    analyzer.redis_client = MockRedisClient()
    
    # Create sample feedback items
    feedback_items = [
        FeedbackItem(
            feedback_id="fb1",
            user_id="user1",
            message_id="msg1",
            feedback_type=FeedbackType.RATING,
            feedback_value={"rating": 4, "comment": "Good response"},
            context={"query": "machine learning basics", "response_length": 150},
            timestamp=datetime.now()
        ),
        FeedbackItem(
            feedback_id="fb2",
            user_id="user2",
            message_id="msg2",
            feedback_type=FeedbackType.CORRECTION,
            feedback_value={"correction": "The date mentioned is incorrect"},
            context={"query": "historical events", "response_length": 200},
            timestamp=datetime.now()
        ),
        FeedbackItem(
            feedback_id="fb3",
            user_id="user3",
            message_id="msg3",
            feedback_type=FeedbackType.RELEVANCE,
            feedback_value={"relevant": False, "reason": "Off-topic response"},
            context={"query": "python programming", "response_length": 100},
            timestamp=datetime.now()
        )
    ]
    
    print("Processing feedback items...")
    for feedback in feedback_items:
        # Mock the database operations for demo
        async def mock_store_feedback(x):
            return None
        async def mock_get_user_feedback_count(x):
            return 5
        async def mock_update_feedback_status(x, y):
            return None
        async def mock_check_improvement_trigger(x):
            return None
        
        analyzer._store_feedback = mock_store_feedback
        analyzer._get_user_feedback_count = mock_get_user_feedback_count
        analyzer._update_feedback_status = mock_update_feedback_status
        analyzer._check_improvement_trigger = mock_check_improvement_trigger
        
        success = await analyzer.process_feedback(feedback)
        
        print(f"\n- Feedback ID: {feedback.feedback_id}")
        print(f"  Type: {feedback.feedback_type.value}")
        print(f"  User: {feedback.user_id}")
        print(f"  Impact Score: {feedback.impact_score:.3f}")
        print(f"  Processed: {'✓' if success else '✗'}")

async def demo_feedback_analysis():
    """Demonstrate feedback analysis functionality."""
    print("\n" + "="*60)
    print("FEEDBACK ANALYSIS DEMO")
    print("="*60)
    
    # Initialize feedback analyzer
    analyzer = FeedbackAnalyzer()
    analyzer.redis_client = MockRedisClient()
    
    # Create sample feedback data
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
        },
        {
            'feedback_id': 'fb4',
            'user_id': 'user4',
            'message_id': 'msg4',
            'feedback_type': 'relevance',
            'feedback_value': {'relevant': False},
            'created_at': datetime.now() - timedelta(hours=4),
            'processed': True
        },
        {
            'feedback_id': 'fb5',
            'user_id': 'user5',
            'message_id': 'msg5',
            'feedback_type': 'rating',
            'feedback_value': {'rating': 5},
            'created_at': datetime.now() - timedelta(hours=5),
            'processed': True
        }
    ]
    
    # Mock database query
    async def mock_get_feedback_data(x):
        return sample_feedback_data
    analyzer._get_feedback_data = mock_get_feedback_data
    
    print("Analyzing feedback patterns...")
    analysis = await analyzer.analyze_feedback_patterns(time_window_days=30)
    
    print(f"\nFeedback Analysis Results:")
    print(f"- Total Feedback: {analysis['total_feedback']}")
    print(f"- Feedback by Type: {analysis['feedback_by_type']}")
    print(f"- Rating Trends: {analysis['rating_trends']}")
    print(f"- Common Issues: {len(analysis['common_issues'])} issues identified")
    print(f"- User Satisfaction: {analysis['user_satisfaction']}")
    print(f"- Improvement Opportunities: {len(analysis['improvement_opportunities'])} opportunities")

async def demo_improvement_actions():
    """Demonstrate improvement action generation."""
    print("\n" + "="*60)
    print("IMPROVEMENT ACTION GENERATION DEMO")
    print("="*60)
    
    # Initialize feedback analyzer
    analyzer = FeedbackAnalyzer()
    analyzer.redis_client = MockRedisClient()
    
    # Sample feedback analysis results
    feedback_analysis = {
        'total_feedback': 20,
        'feedback_by_type': {'rating': 12, 'correction': 5, 'relevance': 3},
        'rating_trends': {
            'average_rating': 3.2,
            'rating_distribution': {2: 3, 3: 4, 4: 3, 5: 2},
            'total_ratings': 12,
            'trend': 'declining'
        },
        'common_issues': [
            {
                'issue_type': 'accuracy',
                'frequency': 5,
                'severity': 'high',
                'description': '5 accuracy corrections reported'
            },
            {
                'issue_type': 'satisfaction',
                'frequency': 7,
                'severity': 'medium',
                'description': '7 low satisfaction ratings'
            }
        ],
        'user_satisfaction': {
            'satisfaction_score': 0.42,
            'nps_score': -0.17
        },
        'improvement_opportunities': [
            {
                'opportunity_type': 'retrieval_improvement',
                'priority': 'high',
                'description': 'Retrieval improvements needed based on 3 relevance issues',
                'expected_impact': 0.5
            },
            {
                'opportunity_type': 'personalization',
                'priority': 'medium',
                'description': 'Personalization improvements based on user preferences',
                'expected_impact': 0.3
            }
        ]
    }
    
    print("Generating improvement actions...")
    actions = await analyzer.generate_improvement_actions(feedback_analysis)
    
    print(f"\nGenerated {len(actions)} improvement actions:")
    for i, action in enumerate(actions, 1):
        print(f"\n{i}. Action ID: {action.action_id}")
        print(f"   Type: {action.improvement_type.value}")
        print(f"   Description: {action.description}")
        print(f"   Target Component: {action.target_component}")
        print(f"   Expected Impact: {action.expected_impact:.3f}")
        print(f"   Confidence: {action.confidence:.3f}")
        print(f"   Priority: {action.priority}")
        print(f"   Parameters: {action.parameters}")

async def demo_improvement_application():
    """Demonstrate improvement action application."""
    print("\n" + "="*60)
    print("IMPROVEMENT ACTION APPLICATION DEMO")
    print("="*60)
    
    # Initialize feedback analyzer
    analyzer = FeedbackAnalyzer()
    analyzer.redis_client = MockRedisClient()
    
    # Create sample improvement actions
    actions = [
        ImprovementAction(
            action_id="retrieval_improvement_001",
            improvement_type=ImprovementType.RETRIEVAL_TUNING,
            description="Improve retrieval relevance based on user feedback",
            target_component="retrieval_engine",
            parameters={
                "relevance_threshold": 0.8,
                "ranking_boost": True,
                "semantic_search_weight": 1.2
            },
            expected_impact=0.5,
            confidence=0.8,
            priority="high",
            created_at=datetime.now()
        ),
        ImprovementAction(
            action_id="personalization_improvement_001",
            improvement_type=ImprovementType.PERSONALIZATION,
            description="Enhance personalization based on user preferences",
            target_component="personalization_engine",
            parameters={
                "personalization_level": "enhanced",
                "preference_weight": 1.5,
                "learning_rate": 0.1
            },
            expected_impact=0.3,
            confidence=0.7,
            priority="medium",
            created_at=datetime.now()
        )
    ]
    
    # Mock database operations
    async def mock_update_action_status(x, y):
        return None
    async def mock_log_improvement_application(x):
        return None
    analyzer._update_action_status = mock_update_action_status
    analyzer._log_improvement_application = mock_log_improvement_application
    
    print("Applying improvement actions...")
    for action in actions:
        success = await analyzer.apply_improvement_action(action)
        
        print(f"\n- Action: {action.description}")
        print(f"  Type: {action.improvement_type.value}")
        print(f"  Target: {action.target_component}")
        print(f"  Applied: {'✓' if success else '✗'}")
        
        if success:
            # Check what was stored in Redis
            if action.improvement_type == ImprovementType.RETRIEVAL_TUNING:
                key = f"retrieval_tuning:{action.action_id}"
            elif action.improvement_type == ImprovementType.PERSONALIZATION:
                key = f"personalization_improvement:{action.action_id}"
            
            stored_data = await analyzer.redis_client.get(key)
            if stored_data:
                print(f"  ✓ Configuration stored in Redis: {key}")

async def demo_ab_testing():
    """Demonstrate A/B testing functionality."""
    print("\n" + "="*60)
    print("A/B TESTING DEMO")
    print("="*60)
    
    # Initialize feedback analyzer
    analyzer = FeedbackAnalyzer()
    analyzer.redis_client = MockRedisClient()
    
    # Create A/B test variants
    variants = [
        ABTestVariant(
            variant_id="control",
            name="Current System",
            description="Existing retrieval and response system",
            parameters={},
            traffic_percentage=50.0
        ),
        ABTestVariant(
            variant_id="treatment",
            name="Improved System",
            description="Enhanced retrieval with better ranking",
            parameters={
                "enhanced_ranking": True,
                "semantic_boost": 1.3,
                "personalization_weight": 1.2
            },
            traffic_percentage=50.0
        )
    ]
    
    print("Creating A/B test...")
    test_id = await analyzer.create_ab_test("retrieval_improvement", variants, "user_satisfaction")
    
    if test_id:
        print(f"✓ A/B test created: {test_id}")
        
        # Simulate user assignments
        users = [f"user_{i}" for i in range(10)]
        assignments = {}
        
        print(f"\nAssigning users to variants...")
        for user_id in users:
            variant_id = await analyzer.assign_ab_test_variant(test_id, user_id)
            assignments[user_id] = variant_id
            print(f"- {user_id}: {variant_id}")
        
        # Simulate metric recording
        print(f"\nRecording test metrics...")
        import random
        for user_id, variant_id in assignments.items():
            # Simulate different performance for variants
            if variant_id == "control":
                metric_value = random.uniform(0.6, 0.8)
            else:  # treatment
                metric_value = random.uniform(0.7, 0.9)
            
            success = await analyzer.record_ab_test_metric(test_id, variant_id, metric_value)
            if success:
                print(f"- {user_id} ({variant_id}): {metric_value:.3f}")
        
        # Analyze results
        print(f"\nAnalyzing A/B test results...")
        results = await analyzer.analyze_ab_test_results(test_id)
        
        for result in results:
            print(f"\n- Variant: {result.variant_id}")
            print(f"  Metric: {result.metric_name}")
            print(f"  Value: {result.metric_value:.3f}")
            print(f"  Sample Size: {result.sample_size}")
            print(f"  Confidence Interval: ({result.confidence_interval[0]:.3f}, {result.confidence_interval[1]:.3f})")
            print(f"  Statistically Significant: {result.statistical_significance}")

async def demo_effectiveness_measurement():
    """Demonstrate improvement effectiveness measurement."""
    print("\n" + "="*60)
    print("EFFECTIVENESS MEASUREMENT DEMO")
    print("="*60)
    
    # Initialize feedback analyzer
    analyzer = FeedbackAnalyzer()
    analyzer.redis_client = MockRedisClient()
    
    # Create sample improvement action
    action = ImprovementAction(
        action_id="test_improvement_001",
        improvement_type=ImprovementType.RETRIEVAL_TUNING,
        description="Test retrieval improvement",
        target_component="retrieval_engine",
        parameters={"relevance_threshold": 0.8},
        expected_impact=0.4,
        confidence=0.8,
        priority="high",
        created_at=datetime.now() - timedelta(days=7)  # Applied 7 days ago
    )
    
    # Mock performance metrics
    baseline_metrics = {
        'avg_response_time': 2.5,
        'avg_satisfaction': 3.2,
        'satisfaction_rate': 0.45
    }
    
    post_metrics = {
        'avg_response_time': 2.1,
        'avg_satisfaction': 3.8,
        'satisfaction_rate': 0.62
    }
    
    async def mock_get_performance_metrics(start, end):
        return baseline_metrics if start < action.created_at else post_metrics
    async def mock_store_improvement_effectiveness(action_id, effectiveness):
        return None
    analyzer._get_performance_metrics = mock_get_performance_metrics
    analyzer._store_improvement_effectiveness = mock_store_improvement_effectiveness
    
    print("Measuring improvement effectiveness...")
    effectiveness = await analyzer.measure_improvement_effectiveness(action, measurement_period_days=7)
    
    print(f"\nEffectiveness Results for Action: {action.description}")
    for metric, improvement in effectiveness.items():
        direction = "↑" if improvement > 0 else "↓" if improvement < 0 else "→"
        print(f"- {metric}: {improvement:+.1%} {direction}")
    
    # Calculate overall effectiveness score
    if effectiveness:
        overall_score = sum(abs(v) for v in effectiveness.values()) / len(effectiveness)
        print(f"\nOverall Effectiveness Score: {overall_score:.3f}")
        
        if overall_score > 0.1:
            print("✓ Improvement was effective!")
        else:
            print("⚠ Improvement had minimal impact")

async def main():
    """Run all demos."""
    print("FEEDBACK ANALYZER SERVICE DEMO")
    print("="*60)
    
    try:
        await demo_feedback_processing()
        await demo_feedback_analysis()
        await demo_improvement_actions()
        await demo_improvement_application()
        await demo_ab_testing()
        await demo_effectiveness_measurement()
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())