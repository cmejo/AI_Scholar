"""
Verification script for Task 9.3: Create retrieval strategy optimization
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from services.retrieval_optimizer import (
    RetrievalOptimizer,
    RetrievalParameters,
    RetrievalStrategy,
    PerformanceMetrics,
    OptimizationResult,
    OptimizationMetric
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_retrieval_optimizer_initialization():
    """Test RetrievalOptimizer initialization."""
    print("Testing RetrievalOptimizer initialization...")
    
    optimizer = RetrievalOptimizer()
    
    # Test basic properties
    assert optimizer.optimization_cache_ttl == 7200
    assert optimizer.min_sample_size == 20
    assert optimizer.optimization_threshold == 0.05
    assert 'similarity_threshold' in optimizer.parameter_bounds
    assert 'semantic_weight' in optimizer.parameter_bounds
    
    print("✓ RetrievalOptimizer initialization test passed")

async def test_retrieval_parameters():
    """Test RetrievalParameters functionality."""
    print("Testing RetrievalParameters...")
    
    # Create parameters
    params = RetrievalParameters(
        strategy=RetrievalStrategy.HYBRID_SEARCH,
        similarity_threshold=0.75,
        semantic_weight=0.7,
        keyword_weight=0.3,
        max_results=12
    )
    
    # Test to_dict conversion
    params_dict = params.to_dict()
    assert isinstance(params_dict, dict)
    assert params_dict['strategy'] == 'hybrid_search'
    assert params_dict['similarity_threshold'] == 0.75
    assert params_dict['semantic_weight'] == 0.7
    
    # Test from_dict conversion
    reconstructed = RetrievalParameters.from_dict(params_dict)
    assert reconstructed.strategy == RetrievalStrategy.HYBRID_SEARCH
    assert reconstructed.similarity_threshold == 0.75
    assert reconstructed.semantic_weight == 0.7
    
    print("✓ RetrievalParameters test passed")

async def test_performance_metrics():
    """Test PerformanceMetrics functionality."""
    print("Testing PerformanceMetrics...")
    
    metrics = PerformanceMetrics(
        relevance_score=0.8,
        response_time=1.5,
        user_satisfaction=0.75,
        precision=0.7,
        recall=0.8,
        f1_score=0.74,
        sample_size=100,
        timestamp=datetime.now()
    )
    
    # Test overall score calculation
    overall_score = metrics.overall_score()
    assert isinstance(overall_score, float)
    assert 0 <= overall_score <= 1
    assert overall_score > 0.5  # Should be decent score
    
    # Test with custom weights
    custom_weights = {
        'relevance_score': 0.5,
        'response_time': 0.3,
        'user_satisfaction': 0.2,
        'f1_score': 0.0
    }
    
    custom_score = metrics.overall_score(custom_weights)
    assert isinstance(custom_score, float)
    assert 0 <= custom_score <= 1
    
    print("✓ PerformanceMetrics test passed")

async def test_performance_data_collection():
    """Test performance data collection."""
    print("Testing performance data collection...")
    
    optimizer = RetrievalOptimizer()
    
    # Mock Redis client
    class MockRedis:
        def __init__(self):
            self.data = {}
            self.lists = {}
        async def lpush(self, key, value):
            if key not in self.lists:
                self.lists[key] = []
            self.lists[key].insert(0, value)
            return len(self.lists[key])
        async def ltrim(self, key, start, stop):
            if key in self.lists:
                self.lists[key] = self.lists[key][start:stop+1]
            return True
    
    optimizer.redis_client = MockRedis()
    
    # Mock database storage
    async def mock_store_performance_data(data):
        assert 'query_id' in data
        assert 'parameters' in data
        assert 'metrics' in data
    
    optimizer._store_performance_data = mock_store_performance_data
    
    # Test data collection
    params = RetrievalParameters(RetrievalStrategy.SEMANTIC_SEARCH)
    metrics = PerformanceMetrics(
        relevance_score=0.8,
        response_time=1.2,
        user_satisfaction=0.75,
        precision=0.7,
        recall=0.8,
        f1_score=0.74,
        sample_size=50,
        timestamp=datetime.now()
    )
    
    success = await optimizer.collect_performance_data("test_query", params, metrics)
    assert success is True
    
    # Verify data was stored in Redis
    assert 'retrieval_performance_data' in optimizer.redis_client.lists
    assert len(optimizer.redis_client.lists['retrieval_performance_data']) == 1
    
    print("✓ Performance data collection test passed")

async def test_performance_analysis():
    """Test performance analysis functionality."""
    print("Testing performance analysis...")
    
    optimizer = RetrievalOptimizer()
    
    # Mock Redis client
    class MockRedis:
        def __init__(self):
            self.data = {}
        async def setex(self, key, ttl, value):
            self.data[key] = value
            return True
    
    optimizer.redis_client = MockRedis()
    
    # Sample performance data
    performance_data = [
        {
            'query_id': 'q1',
            'parameters': {
                'strategy': 'hybrid_search',
                'similarity_threshold': 0.7,
                'semantic_weight': 0.7,
                'keyword_weight': 0.3
            },
            'metrics': {
                'relevance_score': 0.8,
                'response_time': 1.5,
                'user_satisfaction': 0.75,
                'f1_score': 0.74
            },
            'timestamp': datetime.now().isoformat()
        },
        {
            'query_id': 'q2',
            'parameters': {
                'strategy': 'semantic_search',
                'similarity_threshold': 0.8,
                'semantic_weight': 0.9,
                'keyword_weight': 0.1
            },
            'metrics': {
                'relevance_score': 0.85,
                'response_time': 1.2,
                'user_satisfaction': 0.8,
                'f1_score': 0.78
            },
            'timestamp': datetime.now().isoformat()
        }
    ]
    
    # Mock performance data retrieval
    async def mock_get_performance_data(strategy=None, time_window_hours=24):
        return performance_data
    
    optimizer._get_performance_data = mock_get_performance_data
    
    # Analyze performance
    analysis = await optimizer.analyze_current_performance()
    
    assert isinstance(analysis, dict)
    assert 'total_queries' in analysis
    assert 'strategy_distribution' in analysis
    assert 'performance_trends' in analysis
    assert 'bottlenecks' in analysis
    assert 'optimization_opportunities' in analysis
    
    assert analysis['total_queries'] == 2
    assert 'hybrid_search' in analysis['strategy_distribution']
    assert 'semantic_search' in analysis['strategy_distribution']
    
    print("✓ Performance analysis test passed")

async def test_strategy_distribution_analysis():
    """Test strategy distribution analysis."""
    print("Testing strategy distribution analysis...")
    
    optimizer = RetrievalOptimizer()
    
    performance_data = [
        {'parameters': {'strategy': 'hybrid_search'}},
        {'parameters': {'strategy': 'hybrid_search'}},
        {'parameters': {'strategy': 'semantic_search'}},
        {'parameters': {'strategy': 'keyword_search'}}
    ]
    
    distribution = optimizer._analyze_strategy_distribution(performance_data)
    
    assert isinstance(distribution, dict)
    assert distribution['hybrid_search'] == 2
    assert distribution['semantic_search'] == 1
    assert distribution['keyword_search'] == 1
    
    print("✓ Strategy distribution analysis test passed")

async def test_bottleneck_identification():
    """Test bottleneck identification."""
    print("Testing bottleneck identification...")
    
    optimizer = RetrievalOptimizer()
    
    # Create performance data with bottlenecks
    bottleneck_data = []
    for i in range(10):
        bottleneck_data.append({
            'metrics': {
                'relevance_score': 0.5,  # Low relevance
                'response_time': 4.0,    # High response time
                'user_satisfaction': 0.6  # Low satisfaction
            }
        })
    
    bottlenecks = await optimizer._identify_bottlenecks(bottleneck_data)
    
    assert isinstance(bottlenecks, list)
    assert len(bottlenecks) > 0
    
    # Should identify bottlenecks
    bottleneck_types = [b['type'] for b in bottlenecks]
    assert 'response_time' in bottleneck_types
    assert 'relevance' in bottleneck_types
    
    # Check bottleneck structure
    for bottleneck in bottlenecks:
        assert 'type' in bottleneck
        assert 'severity' in bottleneck
        assert 'description' in bottleneck
        assert 'metric_value' in bottleneck
        assert 'threshold' in bottleneck
        assert bottleneck['severity'] in ['high', 'medium', 'low']
    
    print("✓ Bottleneck identification test passed")

async def test_parameter_similarity():
    """Test parameter similarity calculation."""
    print("Testing parameter similarity calculation...")
    
    optimizer = RetrievalOptimizer()
    
    params1 = {
        'similarity_threshold': 0.7,
        'semantic_weight': 0.7,
        'keyword_weight': 0.3
    }
    
    params2 = {
        'similarity_threshold': 0.75,
        'semantic_weight': 0.65,
        'keyword_weight': 0.35
    }
    
    similarity = optimizer._calculate_parameter_similarity(params1, params2)
    
    assert isinstance(similarity, float)
    assert 0 <= similarity <= 1
    assert similarity > 0.8  # Should be high similarity
    
    # Test with very different parameters
    params3 = {
        'similarity_threshold': 0.9,
        'semantic_weight': 0.2,
        'keyword_weight': 0.8
    }
    
    similarity_low = optimizer._calculate_parameter_similarity(params1, params3)
    assert similarity_low < similarity  # Should be lower similarity
    
    print("✓ Parameter similarity test passed")

async def test_overall_score_calculation():
    """Test overall score calculation."""
    print("Testing overall score calculation...")
    
    optimizer = RetrievalOptimizer()
    
    # Test with good metrics
    good_metrics = {
        'relevance_score': 0.9,
        'response_time': 1.0,
        'user_satisfaction': 0.85,
        'f1_score': 0.8
    }
    
    good_score = optimizer._calculate_overall_score(good_metrics)
    assert isinstance(good_score, float)
    assert 0 <= good_score <= 1
    assert good_score > 0.7  # Should be high
    
    # Test with poor metrics
    poor_metrics = {
        'relevance_score': 0.4,
        'response_time': 8.0,
        'user_satisfaction': 0.3,
        'f1_score': 0.2
    }
    
    poor_score = optimizer._calculate_overall_score(poor_metrics)
    assert isinstance(poor_score, float)
    assert 0 <= poor_score <= 1
    assert poor_score < good_score  # Should be lower
    
    print("✓ Overall score calculation test passed")

async def test_candidate_parameter_generation():
    """Test candidate parameter generation."""
    print("Testing candidate parameter generation...")
    
    optimizer = RetrievalOptimizer()
    
    base_params = RetrievalParameters(
        strategy=RetrievalStrategy.HYBRID_SEARCH,
        similarity_threshold=0.7,
        semantic_weight=0.7,
        keyword_weight=0.3,
        max_results=10
    )
    
    candidate = optimizer._generate_candidate_parameters(base_params, exploration_factor=0.5)
    
    assert isinstance(candidate, RetrievalParameters)
    assert candidate.strategy == base_params.strategy
    
    # Parameters should be within bounds
    assert 0.5 <= candidate.similarity_threshold <= 0.95
    assert 0.1 <= candidate.semantic_weight <= 1.0
    assert 0.0 <= candidate.keyword_weight <= 0.9
    
    # Semantic and keyword weights should sum to <= 1.0
    assert candidate.semantic_weight + candidate.keyword_weight <= 1.01  # Allow small floating point error
    
    print("✓ Candidate parameter generation test passed")

async def test_optimization_application():
    """Test optimization application."""
    print("Testing optimization application...")
    
    optimizer = RetrievalOptimizer()
    
    # Mock Redis client
    class MockRedis:
        def __init__(self):
            self.data = {}
        async def setex(self, key, ttl, value):
            self.data[key] = value
            return True
    
    optimizer.redis_client = MockRedis()
    
    # Mock database operations
    async def mock_log_optimization_application(result):
        assert isinstance(result, OptimizationResult)
    
    async def mock_store_optimization_history(result):
        assert isinstance(result, OptimizationResult)
    
    optimizer._log_optimization_application = mock_log_optimization_application
    optimizer._store_optimization_history = mock_store_optimization_history
    
    # Create optimization result
    original_params = RetrievalParameters(RetrievalStrategy.HYBRID_SEARCH)
    optimized_params = RetrievalParameters(
        strategy=RetrievalStrategy.HYBRID_SEARCH,
        similarity_threshold=0.8,
        semantic_weight=0.75,
        keyword_weight=0.25
    )
    
    optimization_result = OptimizationResult(
        original_parameters=original_params,
        optimized_parameters=optimized_params,
        performance_improvement=0.15,
        confidence=0.8,
        optimization_type="test_optimization",
        applied_at=datetime.now()
    )
    
    # Apply optimization
    success = await optimizer.apply_optimization(optimization_result)
    
    assert success is True
    
    # Verify configuration was stored in Redis
    expected_key = f"retrieval_optimization:{optimized_params.strategy.value}"
    assert expected_key in optimizer.redis_client.data
    
    stored_data = json.loads(optimizer.redis_client.data[expected_key])
    assert stored_data['parameters']['strategy'] == 'hybrid_search'
    assert stored_data['performance_improvement'] == 0.15
    assert stored_data['confidence'] == 0.8
    
    print("✓ Optimization application test passed")

async def test_optimization_monitoring():
    """Test optimization impact monitoring."""
    print("Testing optimization monitoring...")
    
    optimizer = RetrievalOptimizer()
    
    # Create optimization result
    original_params = RetrievalParameters(RetrievalStrategy.HYBRID_SEARCH)
    optimized_params = RetrievalParameters(
        strategy=RetrievalStrategy.HYBRID_SEARCH,
        similarity_threshold=0.8
    )
    
    optimization_result = OptimizationResult(
        original_parameters=original_params,
        optimized_parameters=optimized_params,
        performance_improvement=0.1,
        confidence=0.8,
        optimization_type="test_optimization",
        applied_at=datetime.now() - timedelta(hours=12)
    )
    
    # Mock performance data
    before_data = [
        {'metrics': {'relevance_score': 0.7, 'response_time': 2.0, 'user_satisfaction': 0.6, 'f1_score': 0.65}}
    ] * 10
    
    after_data = [
        {'metrics': {'relevance_score': 0.8, 'response_time': 1.8, 'user_satisfaction': 0.7, 'f1_score': 0.75}}
    ] * 10
    
    async def mock_get_performance_data(strategy=None, time_window_hours=24, start_time=None, end_time=None):
        if start_time and start_time > optimization_result.applied_at:
            return after_data
        else:
            return before_data
    
    async def mock_store_monitoring_results(analysis):
        assert 'optimization_id' in analysis
        assert 'actual_improvement' in analysis
    
    optimizer._get_performance_data = mock_get_performance_data
    optimizer._store_monitoring_results = mock_store_monitoring_results
    
    # Monitor impact
    impact_analysis = await optimizer.monitor_optimization_impact(optimization_result)
    
    assert isinstance(impact_analysis, dict)
    assert 'optimization_id' in impact_analysis
    assert 'before_metrics' in impact_analysis
    assert 'after_metrics' in impact_analysis
    assert 'performance_changes' in impact_analysis
    assert 'actual_improvement' in impact_analysis
    assert 'optimization_success' in impact_analysis
    
    # Should show improvement (actual improvement should be calculated)
    assert isinstance(impact_analysis['actual_improvement'], (int, float))
    
    print("✓ Optimization monitoring test passed")

async def test_optimization_recommendations():
    """Test optimization recommendations."""
    print("Testing optimization recommendations...")
    
    optimizer = RetrievalOptimizer()
    
    current_params = RetrievalParameters(
        strategy=RetrievalStrategy.HYBRID_SEARCH,
        similarity_threshold=0.6,
        max_results=20
    )
    
    # Mock performance analysis
    mock_analysis = {
        'bottlenecks': [
            {
                'type': 'response_time',
                'severity': 'high',
                'metric_value': 4.0,
                'threshold': 3.0
            }
        ],
        'optimization_opportunities': [
            {
                'type': 'parameter_optimization',
                'parameter': 'similarity_threshold',
                'expected_impact': 0.2
            }
        ]
    }
    
    async def mock_analyze_performance(strategy):
        return mock_analysis
    
    optimizer.analyze_current_performance = mock_analyze_performance
    
    # Get recommendations
    recommendations = await optimizer.get_optimization_recommendations(current_params)
    
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    
    # Check recommendation structure
    for rec in recommendations:
        assert 'type' in rec
        assert 'expected_impact' in rec
        assert isinstance(rec['expected_impact'], (int, float))
    
    print("✓ Optimization recommendations test passed")

async def test_retrieval_strategy_optimization():
    """Test end-to-end retrieval strategy optimization."""
    print("Testing retrieval strategy optimization...")
    
    optimizer = RetrievalOptimizer()
    
    # Mock Redis client
    class MockRedis:
        def __init__(self):
            self.data = {}
        async def setex(self, key, ttl, value):
            self.data[key] = value
            return True
        async def lpush(self, key, value):
            return 1
        async def ltrim(self, key, start, stop):
            return True
    
    optimizer.redis_client = MockRedis()
    
    # Mock database operations
    async def mock_store_performance_data(data):
        pass
    async def mock_get_performance_data(strategy=None, time_window_hours=168):
        # Return sufficient data for optimization
        return [
            {
                'parameters': {
                    'strategy': 'hybrid_search',
                    'similarity_threshold': 0.7 + (i * 0.01),
                    'semantic_weight': 0.7,
                    'keyword_weight': 0.3
                },
                'metrics': {
                    'relevance_score': 0.75 + (i * 0.005),
                    'response_time': 1.5,
                    'user_satisfaction': 0.7,
                    'f1_score': 0.72
                }
            }
            for i in range(25)  # Above min_sample_size
        ]
    async def mock_log_optimization_application(result):
        pass
    async def mock_store_optimization_history(result):
        pass
    
    optimizer._store_performance_data = mock_store_performance_data
    optimizer._get_performance_data = mock_get_performance_data
    optimizer._log_optimization_application = mock_log_optimization_application
    optimizer._store_optimization_history = mock_store_optimization_history
    
    # Test complete optimization workflow
    current_params = RetrievalParameters(RetrievalStrategy.HYBRID_SEARCH)
    
    # Step 1: Collect performance data
    metrics = PerformanceMetrics(
        relevance_score=0.75,
        response_time=1.8,
        user_satisfaction=0.7,
        precision=0.72,
        recall=0.78,
        f1_score=0.75,
        sample_size=100,
        timestamp=datetime.now()
    )
    
    success = await optimizer.collect_performance_data("test_query", current_params, metrics)
    assert success is True
    
    # Step 2: Analyze performance
    analysis = await optimizer.analyze_current_performance()
    assert isinstance(analysis, dict)
    assert 'total_queries' in analysis
    
    # Step 3: Optimize parameters
    optimization_result = await optimizer.optimize_parameters(current_params)
    assert isinstance(optimization_result, OptimizationResult)
    assert optimization_result.performance_improvement >= 0
    
    # Step 4: Apply optimization
    success = await optimizer.apply_optimization(optimization_result)
    assert success is True
    
    # Step 5: Get recommendations
    recommendations = await optimizer.get_optimization_recommendations(current_params)
    assert isinstance(recommendations, list)
    
    print("✓ Retrieval strategy optimization test passed")

async def main():
    """Run all verification tests."""
    print("TASK 9.3 VERIFICATION: Retrieval strategy optimization")
    print("=" * 60)
    
    try:
        await test_retrieval_optimizer_initialization()
        await test_retrieval_parameters()
        await test_performance_metrics()
        await test_performance_data_collection()
        await test_performance_analysis()
        await test_strategy_distribution_analysis()
        await test_bottleneck_identification()
        await test_parameter_similarity()
        await test_overall_score_calculation()
        await test_candidate_parameter_generation()
        await test_optimization_application()
        await test_optimization_monitoring()
        await test_optimization_recommendations()
        await test_retrieval_strategy_optimization()
        
        print("\n" + "=" * 60)
        print("✓ ALL TASK 9.3 VERIFICATION TESTS PASSED!")
        print("✓ Retrieval strategy optimization is working correctly")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ TASK 9.3 VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)