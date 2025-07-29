"""
Verification script for Task 9.1: Implement usage pattern learning
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from services.pattern_learner import PatternLearner, QueryPattern, DocumentUsagePattern, UserBehaviorPattern

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_pattern_learner_initialization():
    """Test PatternLearner initialization."""
    print("Testing PatternLearner initialization...")
    
    learner = PatternLearner()
    
    # Test basic properties
    assert learner.pattern_cache_ttl == 3600
    assert learner.min_pattern_frequency == 5
    assert learner.confidence_threshold == 0.7
    
    print("✓ PatternLearner initialization test passed")

async def test_frequent_term_analysis():
    """Test frequent term analysis functionality."""
    print("Testing frequent term analysis...")
    
    learner = PatternLearner()
    
    # Sample query data
    query_data = [
        {'query': 'machine learning algorithms', 'timestamp': datetime.now(), 'user_id': 'user1', 'metadata': {}},
        {'query': 'machine learning applications', 'timestamp': datetime.now(), 'user_id': 'user2', 'metadata': {}},
        {'query': 'machine learning basics', 'timestamp': datetime.now(), 'user_id': 'user3', 'metadata': {}},
        {'query': 'deep learning neural networks', 'timestamp': datetime.now(), 'user_id': 'user4', 'metadata': {}},
        {'query': 'artificial intelligence machine learning', 'timestamp': datetime.now(), 'user_id': 'user5', 'metadata': {}},
        {'query': 'machine learning models', 'timestamp': datetime.now(), 'user_id': 'user6', 'metadata': {}},
    ]
    
    patterns = await learner._analyze_frequent_terms(query_data)
    
    # Verify patterns were found
    assert isinstance(patterns, list)
    
    # Check for expected frequent terms
    pattern_terms = [p.metadata['term'] for p in patterns]
    assert 'machine' in pattern_terms
    assert 'learning' in pattern_terms
    
    # Verify pattern structure
    for pattern in patterns:
        assert isinstance(pattern, QueryPattern)
        assert pattern.pattern_type == "frequent_terms"
        assert pattern.frequency >= learner.min_pattern_frequency
        assert 0 <= pattern.confidence <= 1
        assert len(pattern.examples) > 0
    
    print("✓ Frequent term analysis test passed")

async def test_temporal_pattern_analysis():
    """Test temporal pattern analysis functionality."""
    print("Testing temporal pattern analysis...")
    
    learner = PatternLearner()
    
    # Create query data with temporal patterns
    base_time = datetime.now()
    query_data = []
    
    # Create peak at 9 AM
    for i in range(8):
        query_data.append({
            'query': f'query {i}',
            'timestamp': base_time.replace(hour=9, minute=i*5),
            'user_id': f'user{i}',
            'metadata': {}
        })
    
    # Create peak at 2 PM
    for i in range(6):
        query_data.append({
            'query': f'query {i+10}',
            'timestamp': base_time.replace(hour=14, minute=i*5),
            'user_id': f'user{i+10}',
            'metadata': {}
        })
    
    # Add some normal activity
    for i in range(2):
        query_data.append({
            'query': f'query {i+20}',
            'timestamp': base_time.replace(hour=20, minute=i*5),
            'user_id': f'user{i+20}',
            'metadata': {}
        })
    
    patterns = await learner._analyze_temporal_patterns(query_data)
    
    # Verify patterns were found
    assert isinstance(patterns, list)
    
    # Check pattern structure
    for pattern in patterns:
        assert isinstance(pattern, QueryPattern)
        assert pattern.pattern_type == "temporal"
        assert 'hour' in pattern.metadata
        assert pattern.frequency > 0
        assert 0 <= pattern.confidence <= 1
    
    print("✓ Temporal pattern analysis test passed")

async def test_semantic_pattern_analysis():
    """Test semantic pattern analysis functionality."""
    print("Testing semantic pattern analysis...")
    
    learner = PatternLearner()
    
    # Create query data with semantic patterns
    query_data = [
        {'query': 'what is machine learning?', 'timestamp': datetime.now(), 'user_id': 'user1', 'metadata': {}},
        {'query': 'how does AI work?', 'timestamp': datetime.now(), 'user_id': 'user2', 'metadata': {}},
        {'query': 'what is artificial intelligence?', 'timestamp': datetime.now(), 'user_id': 'user3', 'metadata': {}},
        {'query': 'machine learning algorithms implementation', 'timestamp': datetime.now(), 'user_id': 'user4', 'metadata': {}},
        {'query': 'deep learning neural network architecture', 'timestamp': datetime.now(), 'user_id': 'user5', 'metadata': {}},
        {'query': 'advanced machine learning techniques', 'timestamp': datetime.now(), 'user_id': 'user6', 'metadata': {}},
        {'query': 'why use machine learning?', 'timestamp': datetime.now(), 'user_id': 'user7', 'metadata': {}},
        {'query': 'when to apply AI?', 'timestamp': datetime.now(), 'user_id': 'user8', 'metadata': {}},
        {'query': 'where is machine learning used?', 'timestamp': datetime.now(), 'user_id': 'user9', 'metadata': {}},
        {'query': 'how to implement neural networks?', 'timestamp': datetime.now(), 'user_id': 'user10', 'metadata': {}},
    ]
    
    patterns = await learner._analyze_semantic_patterns(query_data)
    
    # Verify patterns were found
    assert isinstance(patterns, list)
    
    # Check pattern structure
    for pattern in patterns:
        assert isinstance(pattern, QueryPattern)
        assert pattern.pattern_type == "semantic"
        assert 'cluster_id' in pattern.metadata
        assert pattern.frequency >= learner.min_pattern_frequency
        assert 0 <= pattern.confidence <= 1
        assert len(pattern.examples) > 0
    
    print("✓ Semantic pattern analysis test passed")

async def test_peak_time_identification():
    """Test peak time identification functionality."""
    print("Testing peak time identification...")
    
    learner = PatternLearner()
    
    # Create access times with clear peaks
    base_time = datetime.now()
    access_times = []
    
    # Peak at 9 AM (10 accesses)
    for i in range(10):
        access_times.append(base_time.replace(hour=9, minute=i*5))
    
    # Peak at 2 PM (8 accesses)
    for i in range(8):
        access_times.append(base_time.replace(hour=14, minute=i*5))
    
    # Normal activity at other times (2-3 accesses each)
    for hour in [11, 16, 18]:
        for i in range(2):
            access_times.append(base_time.replace(hour=hour, minute=i*10))
    
    peak_times = await learner._identify_peak_times(access_times)
    
    # Verify peak times were identified
    assert isinstance(peak_times, list)
    assert "09:00" in peak_times
    assert "14:00" in peak_times
    
    print("✓ Peak time identification test passed")

async def test_query_context_extraction():
    """Test query context extraction functionality."""
    print("Testing query context extraction...")
    
    learner = PatternLearner()
    
    queries = [
        "machine learning algorithms",
        "machine learning applications",
        "deep learning neural networks",
        "artificial intelligence basics",
        "machine learning models",
        "neural network architecture"
    ]
    
    contexts = await learner._extract_query_contexts(queries)
    
    # Verify contexts were extracted
    assert isinstance(contexts, list)
    assert "machine" in contexts
    assert "learning" in contexts
    assert "neural" in contexts
    
    print("✓ Query context extraction test passed")

async def test_effectiveness_score_calculation():
    """Test effectiveness score calculation functionality."""
    print("Testing effectiveness score calculation...")
    
    learner = PatternLearner()
    
    # Test high effectiveness document
    high_data = {
        'access_count': 80,
        'users': [f'user{i}' for i in range(15)]
    }
    
    high_score = await learner._calculate_effectiveness_score('doc1', high_data)
    assert isinstance(high_score, float)
    assert 0 <= high_score <= 1
    assert high_score > 0.5  # Should be high
    
    # Test low effectiveness document
    low_data = {
        'access_count': 5,
        'users': ['user1']
    }
    
    low_score = await learner._calculate_effectiveness_score('doc2', low_data)
    assert isinstance(low_score, float)
    assert 0 <= low_score <= 1
    assert low_score < high_score  # Should be lower
    
    print("✓ Effectiveness score calculation test passed")

async def test_user_behavior_analysis():
    """Test user behavior analysis functionality."""
    print("Testing user behavior analysis...")
    
    learner = PatternLearner()
    
    # Test session duration calculation
    base_time = datetime.now()
    user_data = {
        'events': [
            {'type': 'query_submitted', 'data': {'query': 'test'}, 'timestamp': base_time},
            {'type': 'document_accessed', 'data': {'document_id': 'doc1'}, 'timestamp': base_time + timedelta(minutes=5)},
            {'type': 'query_submitted', 'data': {'query': 'test2'}, 'timestamp': base_time + timedelta(minutes=10)},
            # New session after 40 minutes gap
            {'type': 'query_submitted', 'data': {'query': 'test3'}, 'timestamp': base_time + timedelta(minutes=50)},
            {'type': 'document_accessed', 'data': {'document_id': 'doc2'}, 'timestamp': base_time + timedelta(minutes=55)},
        ]
    }
    
    duration = await learner._calculate_avg_session_duration(user_data)
    assert isinstance(duration, float)
    assert duration >= 0
    
    # Test query complexity analysis
    complexity = await learner._analyze_query_complexity(user_data)
    assert complexity in ['simple', 'moderate', 'complex']
    
    # Test domain preference identification
    user_data_with_domains = {
        'events': [
            {'type': 'document_accessed', 'data': {'document_domain': 'technology'}, 'timestamp': base_time},
            {'type': 'document_accessed', 'data': {'document_domain': 'technology'}, 'timestamp': base_time + timedelta(minutes=5)},
            {'type': 'document_accessed', 'data': {'document_domain': 'science'}, 'timestamp': base_time + timedelta(minutes=10)},
        ]
    }
    
    domains = await learner._identify_domain_preferences(user_data_with_domains)
    assert isinstance(domains, list)
    assert 'technology' in domains
    
    print("✓ User behavior analysis test passed")

async def test_system_optimization_generation():
    """Test system optimization generation functionality."""
    print("Testing system optimization generation...")
    
    learner = PatternLearner()
    
    # Create sample patterns
    query_patterns = [
        QueryPattern(
            pattern_id="freq_machine",
            pattern_type="frequent_terms",
            description="Frequent term: machine",
            frequency=10,
            confidence=0.8,
            examples=["machine learning"],
            metadata={"term": "machine"}
        )
    ]
    
    document_patterns = [
        DocumentUsagePattern(
            document_id="doc1",
            access_frequency=60,
            peak_usage_times=["09:00", "14:00"],
            common_query_contexts=["machine", "learning"],
            user_segments=["large_group"],
            effectiveness_score=0.8
        )
    ]
    
    user_patterns = [
        UserBehaviorPattern(
            user_id="user1",
            session_duration_avg=15.0,
            query_complexity_preference="complex",
            preferred_response_length="detailed",
            domain_preferences=["technology"],
            interaction_style="research",
            feedback_tendency="positive"
        )
    ]
    
    patterns = {
        'query_patterns': query_patterns,
        'document_patterns': document_patterns,
        'user_patterns': user_patterns
    }
    
    optimizations = await learner.generate_system_optimizations(patterns)
    
    # Verify optimizations were generated
    assert isinstance(optimizations, list)
    assert len(optimizations) > 0
    
    # Check optimization structure
    for opt in optimizations:
        assert opt.optimization_type
        assert opt.target_component in ['retrieval', 'caching', 'personalization']
        assert opt.recommendation
        assert 0 <= opt.expected_improvement <= 1
        assert 0 <= opt.confidence <= 1
        assert opt.implementation_priority in ['high', 'medium', 'low']
    
    print("✓ System optimization generation test passed")

async def test_pattern_accuracy():
    """Test pattern detection accuracy."""
    print("Testing pattern detection accuracy...")
    
    learner = PatternLearner()
    
    # Create test data with known patterns
    test_queries = [
        {'query': 'machine learning basics', 'timestamp': datetime.now(), 'user_id': 'test1', 'metadata': {}},
        {'query': 'machine learning advanced', 'timestamp': datetime.now(), 'user_id': 'test2', 'metadata': {}},
        {'query': 'machine learning applications', 'timestamp': datetime.now(), 'user_id': 'test3', 'metadata': {}},
        {'query': 'machine learning models', 'timestamp': datetime.now(), 'user_id': 'test4', 'metadata': {}},
        {'query': 'machine learning algorithms', 'timestamp': datetime.now(), 'user_id': 'test5', 'metadata': {}},
        {'query': 'deep learning fundamentals', 'timestamp': datetime.now(), 'user_id': 'test6', 'metadata': {}},
    ]
    
    patterns = await learner._analyze_frequent_terms(test_queries)
    
    # Check if expected patterns were found
    expected_terms = ['machine', 'learning']
    found_terms = [p.metadata['term'] for p in patterns]
    
    accuracy_score = len(set(expected_terms) & set(found_terms)) / len(expected_terms)
    
    # Should achieve at least 80% accuracy
    assert accuracy_score >= 0.8, f"Pattern detection accuracy too low: {accuracy_score}"
    
    print(f"✓ Pattern detection accuracy test passed (accuracy: {accuracy_score:.2f})")

async def main():
    """Run all verification tests."""
    print("TASK 9.1 VERIFICATION: Usage Pattern Learning")
    print("=" * 60)
    
    try:
        await test_pattern_learner_initialization()
        await test_frequent_term_analysis()
        await test_temporal_pattern_analysis()
        await test_semantic_pattern_analysis()
        await test_peak_time_identification()
        await test_query_context_extraction()
        await test_effectiveness_score_calculation()
        await test_user_behavior_analysis()
        await test_system_optimization_generation()
        await test_pattern_accuracy()
        
        print("\n" + "=" * 60)
        print("✓ ALL TASK 9.1 VERIFICATION TESTS PASSED!")
        print("✓ Usage pattern learning implementation is working correctly")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ TASK 9.1 VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)