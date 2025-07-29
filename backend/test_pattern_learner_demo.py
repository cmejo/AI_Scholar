"""
Demo script for Pattern Learning Service functionality.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from services.pattern_learner import PatternLearner, QueryPattern, DocumentUsagePattern, UserBehaviorPattern

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

class MockDBConnection:
    """Mock database connection for demo."""
    
    def __init__(self):
        self.sample_data = self._generate_sample_data()
    
    def _generate_sample_data(self):
        """Generate sample analytics data."""
        base_time = datetime.now()
        
        # Sample analytics events
        events = []
        
        # Query events
        queries = [
            "machine learning algorithms",
            "deep learning neural networks", 
            "artificial intelligence basics",
            "machine learning applications",
            "how does machine learning work?",
            "what is deep learning?",
            "neural network architectures",
            "machine learning models",
            "AI applications in healthcare",
            "supervised learning techniques"
        ]
        
        users = ['user1', 'user2', 'user3', 'user4', 'user5']
        
        for i, query in enumerate(queries):
            events.append((
                'query_submitted',
                {'query': query, 'response_time': 1.2 + i * 0.1},
                base_time - timedelta(hours=i),
                users[i % len(users)]
            ))
        
        # Document access events
        documents = ['doc1', 'doc2', 'doc3']
        for i in range(20):
            events.append((
                'document_accessed',
                {
                    'document_id': documents[i % len(documents)],
                    'document_domain': 'technology' if i % 2 == 0 else 'science',
                    'access_duration': 5.0 + i * 0.5
                },
                base_time - timedelta(hours=i * 0.5),
                users[i % len(users)]
            ))
        
        # Feedback events
        for i in range(8):
            events.append((
                'feedback_provided',
                {
                    'rating': 3 + (i % 3),
                    'response_length_rating': 3 + (i % 3),
                    'feedback_text': f'Feedback {i}'
                },
                base_time - timedelta(hours=i * 2),
                users[i % len(users)]
            ))
        
        return events
    
    def cursor(self):
        return MockCursor(self.sample_data)

class MockCursor:
    """Mock database cursor."""
    
    def __init__(self, data):
        self.data = data
        self.results = []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def execute(self, query, params=None):
        # Simple query simulation
        if 'query_submitted' in query:
            self.results = [
                (
                    {'query': event[1]['query']},
                    event[2],
                    event[3]
                )
                for event in self.data
                if event[0] == 'query_submitted'
            ]
        elif 'document_accessed' in query or 'search_performed' in query:
            self.results = [
                (event[1], event[2], event[3])
                for event in self.data
                if event[0] in ['document_accessed', 'search_performed']
            ]
        elif 'user_id' in query:
            user_id = params[0] if params else 'user1'
            self.results = [
                (event[0], event[1], event[2])
                for event in self.data
                if event[3] == user_id
            ]
        else:
            self.results = []
    
    async def fetchall(self):
        return self.results
    
    async def commit(self):
        pass

async def demo_query_pattern_analysis():
    """Demonstrate query pattern analysis."""
    print("\n" + "="*60)
    print("QUERY PATTERN ANALYSIS DEMO")
    print("="*60)
    
    # Initialize pattern learner
    learner = PatternLearner()
    learner.redis_client = MockRedisClient()
    learner.db_connection = MockDBConnection()
    
    # Analyze query patterns
    print("Analyzing query patterns...")
    patterns = await learner.analyze_query_patterns(time_window_days=30)
    
    print(f"\nFound {len(patterns)} query patterns:")
    for pattern in patterns:
        print(f"\n- Pattern ID: {pattern.pattern_id}")
        print(f"  Type: {pattern.pattern_type}")
        print(f"  Description: {pattern.description}")
        print(f"  Frequency: {pattern.frequency}")
        print(f"  Confidence: {pattern.confidence:.3f}")
        if pattern.examples:
            print(f"  Examples: {pattern.examples[:2]}")
        print(f"  Metadata: {pattern.metadata}")

async def demo_document_usage_analysis():
    """Demonstrate document usage pattern analysis."""
    print("\n" + "="*60)
    print("DOCUMENT USAGE PATTERN ANALYSIS DEMO")
    print("="*60)
    
    # Initialize pattern learner
    learner = PatternLearner()
    learner.redis_client = MockRedisClient()
    learner.db_connection = MockDBConnection()
    
    # Analyze document usage patterns
    print("Analyzing document usage patterns...")
    patterns = await learner.analyze_document_usage_patterns(time_window_days=30)
    
    print(f"\nFound {len(patterns)} document usage patterns:")
    for pattern in patterns:
        print(f"\n- Document ID: {pattern.document_id}")
        print(f"  Access Frequency: {pattern.access_frequency}")
        print(f"  Peak Usage Times: {pattern.peak_usage_times}")
        print(f"  Common Query Contexts: {pattern.common_query_contexts}")
        print(f"  User Segments: {pattern.user_segments}")
        print(f"  Effectiveness Score: {pattern.effectiveness_score:.3f}")

async def demo_user_behavior_analysis():
    """Demonstrate user behavior pattern analysis."""
    print("\n" + "="*60)
    print("USER BEHAVIOR PATTERN ANALYSIS DEMO")
    print("="*60)
    
    # Initialize pattern learner
    learner = PatternLearner()
    learner.redis_client = MockRedisClient()
    learner.db_connection = MockDBConnection()
    
    # Analyze user behavior patterns
    print("Analyzing user behavior patterns...")
    pattern = await learner.analyze_user_behavior_patterns('user1', time_window_days=90)
    
    print(f"\nUser Behavior Pattern for {pattern.user_id}:")
    print(f"- Average Session Duration: {pattern.session_duration_avg:.2f} minutes")
    print(f"- Query Complexity Preference: {pattern.query_complexity_preference}")
    print(f"- Preferred Response Length: {pattern.preferred_response_length}")
    print(f"- Domain Preferences: {pattern.domain_preferences}")
    print(f"- Interaction Style: {pattern.interaction_style}")
    print(f"- Feedback Tendency: {pattern.feedback_tendency}")

async def demo_system_optimization():
    """Demonstrate system optimization generation."""
    print("\n" + "="*60)
    print("SYSTEM OPTIMIZATION DEMO")
    print("="*60)
    
    # Initialize pattern learner
    learner = PatternLearner()
    learner.redis_client = MockRedisClient()
    learner.db_connection = MockDBConnection()
    
    # Generate sample patterns
    query_patterns = [
        QueryPattern(
            pattern_id="freq_machine",
            pattern_type="frequent_terms",
            description="Frequent term: 'machine' appears in 8 queries",
            frequency=8,
            confidence=0.8,
            examples=["machine learning algorithms", "machine learning applications"],
            metadata={"term": "machine", "total_queries": 10}
        ),
        QueryPattern(
            pattern_id="semantic_cluster_0",
            pattern_type="semantic",
            description="Semantic cluster 0 with 6 similar queries",
            frequency=6,
            confidence=0.6,
            examples=["what is machine learning?", "how does AI work?"],
            metadata={"cluster_id": 0, "cluster_size": 6}
        )
    ]
    
    document_patterns = [
        DocumentUsagePattern(
            document_id="doc1",
            access_frequency=75,
            peak_usage_times=["09:00", "14:00", "16:00"],
            common_query_contexts=["machine", "learning", "algorithms"],
            user_segments=["large_group"],
            effectiveness_score=0.85
        ),
        DocumentUsagePattern(
            document_id="doc2",
            access_frequency=45,
            peak_usage_times=["10:00", "15:00"],
            common_query_contexts=["deep", "neural", "networks"],
            user_segments=["medium_group"],
            effectiveness_score=0.72
        )
    ]
    
    user_patterns = [
        UserBehaviorPattern(
            user_id="user1",
            session_duration_avg=18.5,
            query_complexity_preference="complex",
            preferred_response_length="detailed",
            domain_preferences=["technology", "science"],
            interaction_style="research",
            feedback_tendency="positive"
        ),
        UserBehaviorPattern(
            user_id="user2",
            session_duration_avg=12.3,
            query_complexity_preference="moderate",
            preferred_response_length="brief",
            domain_preferences=["technology"],
            interaction_style="targeted",
            feedback_tendency="neutral"
        )
    ]
    
    patterns = {
        'query_patterns': query_patterns,
        'document_patterns': document_patterns,
        'user_patterns': user_patterns
    }
    
    # Generate optimizations
    print("Generating system optimizations...")
    optimizations = await learner.generate_system_optimizations(patterns)
    
    print(f"\nGenerated {len(optimizations)} system optimizations:")
    for i, opt in enumerate(optimizations, 1):
        print(f"\n{i}. Optimization Type: {opt.optimization_type}")
        print(f"   Target Component: {opt.target_component}")
        print(f"   Recommendation: {opt.recommendation}")
        print(f"   Expected Improvement: {opt.expected_improvement:.3f}")
        print(f"   Confidence: {opt.confidence:.3f}")
        print(f"   Priority: {opt.implementation_priority}")

async def demo_optimization_application():
    """Demonstrate optimization application."""
    print("\n" + "="*60)
    print("OPTIMIZATION APPLICATION DEMO")
    print("="*60)
    
    # Initialize pattern learner
    learner = PatternLearner()
    learner.redis_client = MockRedisClient()
    learner.db_connection = MockDBConnection()
    
    # Create sample optimization
    from services.pattern_learner import SystemOptimization
    
    optimization = SystemOptimization(
        optimization_type="term_boosting",
        target_component="retrieval",
        recommendation="Boost relevance for term 'machine' in search results",
        expected_improvement=0.15,
        confidence=0.8,
        implementation_priority="medium"
    )
    
    print("Applying optimization...")
    print(f"- Type: {optimization.optimization_type}")
    print(f"- Target: {optimization.target_component}")
    print(f"- Recommendation: {optimization.recommendation}")
    
    success = await learner.apply_pattern_based_optimization(optimization)
    
    if success:
        print("✓ Optimization applied successfully!")
        
        # Check what was stored in Redis
        cache_key = f"retrieval_optimization:{optimization.optimization_type}"
        cached_data = await learner.redis_client.get(cache_key)
        if cached_data:
            print(f"✓ Optimization cached in Redis: {cache_key}")
    else:
        print("✗ Failed to apply optimization")

async def demo_pattern_accuracy_testing():
    """Demonstrate pattern detection accuracy testing."""
    print("\n" + "="*60)
    print("PATTERN DETECTION ACCURACY TESTING")
    print("="*60)
    
    # Initialize pattern learner
    learner = PatternLearner()
    learner.redis_client = MockRedisClient()
    learner.db_connection = MockDBConnection()
    
    # Test frequent term detection accuracy
    print("Testing frequent term detection...")
    
    # Create test data with known patterns
    test_queries = [
        {'query': 'machine learning basics', 'timestamp': datetime.now(), 'user_id': 'test1', 'metadata': {}},
        {'query': 'machine learning advanced', 'timestamp': datetime.now(), 'user_id': 'test2', 'metadata': {}},
        {'query': 'machine learning applications', 'timestamp': datetime.now(), 'user_id': 'test3', 'metadata': {}},
        {'query': 'deep learning fundamentals', 'timestamp': datetime.now(), 'user_id': 'test4', 'metadata': {}},
        {'query': 'neural network architecture', 'timestamp': datetime.now(), 'user_id': 'test5', 'metadata': {}},
    ]
    
    patterns = await learner._analyze_frequent_terms(test_queries)
    
    # Check if expected patterns were found
    expected_terms = ['machine', 'learning']
    found_terms = [p.metadata['term'] for p in patterns]
    
    accuracy_score = len(set(expected_terms) & set(found_terms)) / len(expected_terms)
    
    print(f"Expected terms: {expected_terms}")
    print(f"Found terms: {found_terms}")
    print(f"Accuracy Score: {accuracy_score:.2f}")
    
    if accuracy_score >= 0.8:
        print("✓ Pattern detection accuracy is good!")
    else:
        print("⚠ Pattern detection accuracy needs improvement")

async def main():
    """Run all demos."""
    print("PATTERN LEARNER SERVICE DEMO")
    print("="*60)
    
    try:
        await demo_query_pattern_analysis()
        await demo_document_usage_analysis()
        await demo_user_behavior_analysis()
        await demo_system_optimization()
        await demo_optimization_application()
        await demo_pattern_accuracy_testing()
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())