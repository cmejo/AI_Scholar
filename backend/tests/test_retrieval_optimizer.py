"""
Tests for Retrieval Optimizer Service.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from services.retrieval_optimizer import (
    RetrievalOptimizer,
    RetrievalParameters,
    RetrievalStrategy,
    PerformanceMetrics,
    OptimizationResult,
    OptimizationMetric
)

@pytest.fixture
async def retrieval_optimizer():
    """Create a RetrievalOptimizer instance for testing."""
    optimizer = RetrievalOptimizer()
    
    # Mock dependencies
    optimizer.redis_client = AsyncMock()
    
    return optimizer

@pytest.fixture
def sample_retrieval_parameters():
    """Sample retrieval parameters for testing."""
    return RetrievalParameters(
        strategy=RetrievalStrategy.HYBRID_SEARCH,
        similarity_threshold=0.7,
        max_results=10,
        semantic_weight=0.7,
        keyword_weight=0.3,
        hierarchical_levels=3,
        knowledge_graph_weight=0.2,
        reranking_enabled=True,
        personalization_weight=0.1,
        context_window=5
    )

@pytest.fixture
def sample_performance_metrics():
    """Sample performance metrics for testing."""
    return PerformanceMetrics(
        relevance_score=0.8,
        response_time=1.5,
        user_satisfaction=0.75,
        precision=0.7,
        recall=0.8,
        f1_score=0.74,
        sample_size=100,
        timestamp=datetime.now()
    )

@pytest.fixture
def sample_performance_data():
    """Sample performance data for testing."""
    base_time = datetime.now()
    return [
        {
            'query_id': 'q1',
            'parameters': {
                'strategy': 'hybrid_search',
                'similarity_threshold': 0.7,
                'semantic_weight': 0.7,
                'keyword_weight': 0.3,
                'max_results': 10
            },
            'metrics': {
                'relevance_score': 0.8,
                'response_time': 1.5,
                'user_satisfaction': 0.75,
                'f1_score': 0.74
            },
            'timestamp': (base_time - timedelta(hours=1)).isoformat()
        },
        {
            'query_id': 'q2',
            'parameters': {
                'strategy': 'hybrid_search',
                'similarity_threshold': 0.8,
                'semantic_weight': 0.6,
                'keyword_weight': 0.4,
                'max_results': 15
            },
            'metrics': {
                'relevance_score': 0.85,
                'response_time': 2.0,
                'user_satisfaction': 0.8,
                'f1_score': 0.78
            },
            'timestamp': (base_time - timedelta(hours=2)).isoformat()
        },
        {
            'query_id': 'q3',
            'parameters': {
                'strategy': 'semantic_search',
                'similarity_threshold': 0.75,
                'semantic_weight': 0.9,
                'keyword_weight': 0.1,
                'max_results': 8
            },
            'metrics': {
                'relevance_score': 0.9,
                'response_time': 1.2,
                'user_satisfaction': 0.85,
                'f1_score': 0.82
            },
            'timestamp': (base_time - timedelta(hours=3)).isoformat()
        }
    ]

class TestRetrievalOptimizer:
    """Test cases for RetrievalOptimizer service."""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test RetrievalOptimizer initialization."""
        optimizer = RetrievalOptimizer()
        
        with patch('services.retrieval_optimizer.get_redis_client') as mock_redis:
            mock_redis.return_value = AsyncMock()
            
            await optimizer.initialize()
            
            assert optimizer.redis_client is not None
            assert optimizer.optimization_cache_ttl == 7200
            assert optimizer.min_sample_size == 20
            assert optimizer.optimization_threshold == 0.05
    
    @pytest.mark.asyncio
    async def test_retrieval_parameters(self, sample_retrieval_parameters):
        """Test RetrievalParameters functionality."""
        # Test to_dict conversion
        params_dict = sample_retrieval_parameters.to_dict()
        
        assert isinstance(params_dict, dict)
        assert params_dict['strategy'] == 'hybrid_search'
        assert params_dict['similarity_threshold'] == 0.7
        assert params_dict['semantic_weight'] == 0.7
        
        # Test from_dict conversion
        reconstructed_params = RetrievalParameters.from_dict(params_dict)
        
        assert reconstructed_params.strategy == RetrievalStrategy.HYBRID_SEARCH
        assert reconstructed_params.similarity_threshold == 0.7
        assert reconstructed_params.semantic_weight == 0.7
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, sample_performance_metrics):
        """Test PerformanceMetrics functionality."""
        # Test overall score calculation with default weights
        overall_score = sample_performance_metrics.overall_score()
        
        assert isinstance(overall_score, float)
        assert 0 <= overall_score <= 1
        assert overall_score > 0.5  # Should be decent score
        
        # Test overall score with custom weights
        custom_weights = {
            'relevance_score': 0.5,
            'response_time': 0.3,
            'user_satisfaction': 0.2,
            'f1_score': 0.0
        }
        
        custom_score = sample_performance_metrics.overall_score(custom_weights)
        assert isinstance(custom_score, float)
        assert 0 <= custom_score <= 1
    
    @pytest.mark.asyncio
    async def test_collect_performance_data(self, retrieval_optimizer, sample_retrieval_parameters, sample_performance_metrics):
        """Test performance data collection."""
        # Mock Redis operations
        retrieval_optimizer.redis_client.lpush = AsyncMock(return_value=1)
        retrieval_optimizer.redis_client.ltrim = AsyncMock(return_value=True)
        
        # Mock database storage
        with patch.object(retrieval_optimizer, '_store_performance_data') as mock_store:
            success = await retrieval_optimizer.collect_performance_data(
                'test_query_123',
                sample_retrieval_parameters,
                sample_performance_metrics
            )
            
            assert success is True
            retrieval_optimizer.redis_client.lpush.assert_called_once()
            retrieval_optimizer.redis_client.ltrim.assert_called_once()
            mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_current_performance(self, retrieval_optimizer, sample_performance_data):
        """Test current performance analysis."""
        # Mock Redis cache
        retrieval_optimizer.redis_client.setex = AsyncMock()
        
        # Mock performance data retrieval
        with patch.object(retrieval_optimizer, '_get_performance_data', return_value=sample_performance_data):
            analysis = await retrieval_optimizer.analyze_current_performance(
                RetrievalStrategy.HYBRID_SEARCH,
                time_window_hours=24
            )
            
            assert isinstance(analysis, dict)
            assert 'total_queries' in analysis
            assert 'strategy_distribution' in analysis
            assert 'performance_trends' in analysis
            assert 'parameter_correlations' in analysis
            assert 'bottlenecks' in analysis
            assert 'optimization_opportunities' in analysis
            
            assert analysis['total_queries'] == 3
            assert 'hybrid_search' in analysis['strategy_distribution']
    
    @pytest.mark.asyncio
    async def test_strategy_distribution_analysis(self, retrieval_optimizer, sample_performance_data):
        """Test strategy distribution analysis."""
        distribution = retrieval_optimizer._analyze_strategy_distribution(sample_performance_data)
        
        assert isinstance(distribution, dict)
        assert 'hybrid_search' in distribution
        assert 'semantic_search' in distribution
        assert distribution['hybrid_search'] == 2
        assert distribution['semantic_search'] == 1
    
    @pytest.mark.asyncio
    async def test_performance_trends_analysis(self, retrieval_optimizer, sample_performance_data):
        """Test performance trends analysis."""
        trends = await retrieval_optimizer._analyze_performance_trends(sample_performance_data)
        
        assert isinstance(trends, dict)
        
        # Should have trends for key metrics
        expected_metrics = ['relevance_score', 'response_time', 'user_satisfaction', 'f1_score']
        for metric in expected_metrics:
            if metric in trends:
                trend_data = trends[metric]
                assert 'slope' in trend_data
                assert 'direction' in trend_data
                assert 'current_value' in trend_data
                assert trend_data['direction'] in ['improving', 'declining', 'stable']
    
    @pytest.mark.asyncio
    async def test_bottleneck_identification(self, retrieval_optimizer, sample_performance_data):
        """Test bottleneck identification."""
        # Create performance data with bottlenecks
        bottleneck_data = [
            {
                'metrics': {
                    'relevance_score': 0.5,  # Low relevance
                    'response_time': 4.0,    # High response time
                    'user_satisfaction': 0.6  # Low satisfaction
                }
            }
        ] * 10  # Multiple samples
        
        bottlenecks = await retrieval_optimizer._identify_bottlenecks(bottleneck_data)
        
        assert isinstance(bottlenecks, list)
        
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
    
    @pytest.mark.asyncio
    async def test_optimization_opportunities_identification(self, retrieval_optimizer, sample_performance_data):
        """Test optimization opportunities identification."""
        opportunities = await retrieval_optimizer._identify_optimization_opportunities(sample_performance_data)
        
        assert isinstance(opportunities, list)
        
        # Check opportunity structure
        for opportunity in opportunities:
            assert 'type' in opportunity
            assert 'description' in opportunity
            assert 'expected_impact' in opportunity
            assert opportunity['type'] in ['parameter_optimization', 'strategy_optimization']
    
    @pytest.mark.asyncio
    async def test_parameter_similarity_calculation(self, retrieval_optimizer):
        """Test parameter similarity calculation."""
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
        
        similarity = retrieval_optimizer._calculate_parameter_similarity(params1, params2)
        
        assert isinstance(similarity, float)
        assert 0 <= similarity <= 1
        assert similarity > 0.8  # Should be high similarity
        
        # Test with very different parameters
        params3 = {
            'similarity_threshold': 0.9,
            'semantic_weight': 0.2,
            'keyword_weight': 0.8
        }
        
        similarity_low = retrieval_optimizer._calculate_parameter_similarity(params1, params3)
        assert similarity_low < similarity  # Should be lower similarity
    
    @pytest.mark.asyncio
    async def test_parameter_performance_evaluation(self, retrieval_optimizer, sample_retrieval_parameters, sample_performance_data):
        """Test parameter performance evaluation."""
        score = await retrieval_optimizer._evaluate_parameter_performance(
            sample_retrieval_parameters,
            sample_performance_data
        )
        
        assert isinstance(score, float)
        assert 0 <= score <= 1
    
    @pytest.mark.asyncio
    async def test_overall_score_calculation(self, retrieval_optimizer):
        """Test overall score calculation."""
        # Test with good metrics
        good_metrics = {
            'relevance_score': 0.9,
            'response_time': 1.0,
            'user_satisfaction': 0.85,
            'f1_score': 0.8
        }
        
        good_score = retrieval_optimizer._calculate_overall_score(good_metrics)
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
        
        poor_score = retrieval_optimizer._calculate_overall_score(poor_metrics)
        assert isinstance(poor_score, float)
        assert 0 <= poor_score <= 1
        assert poor_score < good_score  # Should be lower
    
    @pytest.mark.asyncio
    async def test_grid_search_optimization(self, retrieval_optimizer, sample_retrieval_parameters, sample_performance_data):
        """Test grid search optimization."""
        # Mock parameter evaluation
        async def mock_evaluate_performance(params, data):
            # Return higher score for certain parameter combinations
            if params.similarity_threshold > 0.75 and params.semantic_weight > 0.6:
                return 0.85
            return 0.7
        
        retrieval_optimizer._evaluate_parameter_performance = mock_evaluate_performance
        
        result = await retrieval_optimizer._grid_search_optimization(
            sample_retrieval_parameters,
            sample_performance_data,
            {'relevance_score': 0.8}
        )
        
        assert isinstance(result, OptimizationResult)
        assert result.optimization_type == "grid_search"
        assert result.performance_improvement >= 0
        assert 0 <= result.confidence <= 1
        assert result.original_parameters == sample_retrieval_parameters
    
    @pytest.mark.asyncio
    async def test_gradient_optimization(self, retrieval_optimizer, sample_retrieval_parameters, sample_performance_data):
        """Test gradient-based optimization."""
        # Mock parameter evaluation and gradient calculation
        async def mock_evaluate_performance(params, data):
            return 0.75
        
        async def mock_calculate_gradient(params, param_name, data, step_size):
            return 0.1  # Positive gradient
        
        retrieval_optimizer._evaluate_parameter_performance = mock_evaluate_performance
        retrieval_optimizer._calculate_parameter_gradient = mock_calculate_gradient
        
        result = await retrieval_optimizer._gradient_optimization(
            sample_retrieval_parameters,
            sample_performance_data,
            {'relevance_score': 0.8}
        )
        
        assert isinstance(result, OptimizationResult)
        assert result.optimization_type == "gradient_descent"
        assert result.confidence == 0.6  # Medium confidence for gradient descent
    
    @pytest.mark.asyncio
    async def test_bayesian_optimization(self, retrieval_optimizer, sample_retrieval_parameters, sample_performance_data):
        """Test Bayesian optimization."""
        # Mock parameter evaluation
        async def mock_evaluate_performance(params, data):
            # Return varying scores based on parameters
            base_score = 0.7
            if params.similarity_threshold > 0.8:
                base_score += 0.1
            if params.semantic_weight > 0.8:
                base_score += 0.05
            return min(base_score, 1.0)
        
        retrieval_optimizer._evaluate_parameter_performance = mock_evaluate_performance
        
        result = await retrieval_optimizer._bayesian_optimization(
            sample_retrieval_parameters,
            sample_performance_data,
            {'relevance_score': 0.8}
        )
        
        assert isinstance(result, OptimizationResult)
        assert result.optimization_type == "bayesian_optimization"
        assert result.confidence == 0.7  # Good confidence for Bayesian optimization
    
    @pytest.mark.asyncio
    async def test_candidate_parameter_generation(self, retrieval_optimizer, sample_retrieval_parameters):
        """Test candidate parameter generation."""
        candidate = retrieval_optimizer._generate_candidate_parameters(
            sample_retrieval_parameters,
            exploration_factor=0.5
        )
        
        assert isinstance(candidate, RetrievalParameters)
        assert candidate.strategy == sample_retrieval_parameters.strategy
        
        # Parameters should be within bounds
        assert 0.5 <= candidate.similarity_threshold <= 0.95
        assert 0.1 <= candidate.semantic_weight <= 1.0
        assert 0.0 <= candidate.keyword_weight <= 0.9
        
        # Semantic and keyword weights should sum to <= 1.0
        assert candidate.semantic_weight + candidate.keyword_weight <= 1.01  # Allow small floating point error
    
    @pytest.mark.asyncio
    async def test_optimize_parameters(self, retrieval_optimizer, sample_retrieval_parameters):
        """Test parameter optimization."""
        # Create sufficient performance data
        performance_data = []
        for i in range(25):  # Above min_sample_size
            performance_data.append({
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
            })
        
        # Mock performance data retrieval
        with patch.object(retrieval_optimizer, '_get_performance_data', return_value=performance_data):
            
            # Mock optimization methods to return results
            async def mock_grid_search(params, data, target):
                return OptimizationResult(
                    original_parameters=params,
                    optimized_parameters=params,
                    performance_improvement=0.1,
                    confidence=0.8,
                    optimization_type="grid_search",
                    applied_at=datetime.now()
                )
            
            retrieval_optimizer._grid_search_optimization = mock_grid_search
            retrieval_optimizer._gradient_optimization = lambda *args: None
            retrieval_optimizer._bayesian_optimization = lambda *args: None
            
            result = await retrieval_optimizer.optimize_parameters(sample_retrieval_parameters)
            
            assert isinstance(result, OptimizationResult)
            assert result.performance_improvement >= 0
            assert result.optimization_type == "grid_search"
    
    @pytest.mark.asyncio
    async def test_apply_optimization(self, retrieval_optimizer, sample_retrieval_parameters):
        """Test optimization application."""
        # Create optimization result
        optimization_result = OptimizationResult(
            original_parameters=sample_retrieval_parameters,
            optimized_parameters=sample_retrieval_parameters,
            performance_improvement=0.15,
            confidence=0.8,
            optimization_type="test_optimization",
            applied_at=datetime.now()
        )
        
        # Mock Redis and database operations
        retrieval_optimizer.redis_client.setex = AsyncMock(return_value=True)
        
        with patch.object(retrieval_optimizer, '_log_optimization_application') as mock_log, \
             patch.object(retrieval_optimizer, '_store_optimization_history') as mock_store:
            
            success = await retrieval_optimizer.apply_optimization(optimization_result)
            
            assert success is True
            retrieval_optimizer.redis_client.setex.assert_called_once()
            mock_log.assert_called_once()
            mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_monitor_optimization_impact(self, retrieval_optimizer, sample_retrieval_parameters):
        """Test optimization impact monitoring."""
        optimization_result = OptimizationResult(
            original_parameters=sample_retrieval_parameters,
            optimized_parameters=sample_retrieval_parameters,
            performance_improvement=0.1,
            confidence=0.8,
            optimization_type="test_optimization",
            applied_at=datetime.now() - timedelta(hours=12)
        )
        
        # Mock performance data
        before_data = [{'metrics': {'relevance_score': 0.7, 'response_time': 2.0, 'user_satisfaction': 0.6, 'f1_score': 0.65}}] * 10
        after_data = [{'metrics': {'relevance_score': 0.8, 'response_time': 1.8, 'user_satisfaction': 0.7, 'f1_score': 0.75}}] * 10
        
        with patch.object(retrieval_optimizer, '_get_performance_data', side_effect=[before_data, after_data]), \
             patch.object(retrieval_optimizer, '_store_monitoring_results') as mock_store:
            
            impact_analysis = await retrieval_optimizer.monitor_optimization_impact(optimization_result)
            
            assert isinstance(impact_analysis, dict)
            assert 'optimization_id' in impact_analysis
            assert 'before_metrics' in impact_analysis
            assert 'after_metrics' in impact_analysis
            assert 'performance_changes' in impact_analysis
            assert 'actual_improvement' in impact_analysis
            assert 'optimization_success' in impact_analysis
            
            mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_optimization_recommendations(self, retrieval_optimizer, sample_retrieval_parameters):
        """Test optimization recommendations."""
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
        
        with patch.object(retrieval_optimizer, 'analyze_current_performance', return_value=mock_analysis):
            
            # Mock recommendation generation
            async def mock_bottleneck_rec(bottleneck, params):
                return {
                    'type': 'parameter_adjustment',
                    'parameter': 'max_results',
                    'expected_impact': 0.2
                }
            
            async def mock_opportunity_rec(opportunity, params):
                return {
                    'type': 'parameter_optimization',
                    'parameter': 'similarity_threshold',
                    'expected_impact': 0.15
                }
            
            retrieval_optimizer._generate_bottleneck_recommendation = mock_bottleneck_rec
            retrieval_optimizer._generate_opportunity_recommendation = mock_opportunity_rec
            
            recommendations = await retrieval_optimizer.get_optimization_recommendations(sample_retrieval_parameters)
            
            assert isinstance(recommendations, list)
            assert len(recommendations) > 0
            
            # Check recommendation structure
            for rec in recommendations:
                assert 'type' in rec
                assert 'expected_impact' in rec
    
    @pytest.mark.asyncio
    async def test_aggregate_metrics_calculation(self, retrieval_optimizer, sample_performance_data):
        """Test aggregate metrics calculation."""
        aggregates = retrieval_optimizer._calculate_aggregate_metrics(sample_performance_data)
        
        assert isinstance(aggregates, dict)
        
        # Should have average, p95, and std for each metric
        expected_prefixes = ['avg_', 'p95_', 'std_']
        expected_metrics = ['relevance_score', 'response_time', 'user_satisfaction', 'f1_score']
        
        for prefix in expected_prefixes:
            for metric in expected_metrics:
                key = f"{prefix}{metric}"
                if key in aggregates:
                    assert isinstance(aggregates[key], (int, float))
    
    @pytest.mark.asyncio
    async def test_performance_changes_calculation(self, retrieval_optimizer):
        """Test performance changes calculation."""
        before_metrics = {
            'avg_relevance_score': 0.7,
            'avg_response_time': 2.0,
            'avg_user_satisfaction': 0.6
        }
        
        after_metrics = {
            'avg_relevance_score': 0.8,
            'avg_response_time': 1.8,
            'avg_user_satisfaction': 0.7
        }
        
        changes = retrieval_optimizer._calculate_performance_changes(before_metrics, after_metrics)
        
        assert isinstance(changes, dict)
        
        # Check expected improvements
        assert changes['avg_relevance_score'] > 0  # Should improve
        assert changes['avg_response_time'] < 0    # Should decrease (improve)
        assert changes['avg_user_satisfaction'] > 0  # Should improve
    
    @pytest.mark.asyncio
    async def test_error_handling(self, retrieval_optimizer):
        """Test error handling in optimization."""
        # Test with insufficient data
        with patch.object(retrieval_optimizer, '_get_performance_data', return_value=[]):
            with pytest.raises(ValueError, match="Insufficient data"):
                await retrieval_optimizer.optimize_parameters(RetrievalParameters(RetrievalStrategy.SEMANTIC_SEARCH))
        
        # Test with invalid parameters
        invalid_params = RetrievalParameters(RetrievalStrategy.SEMANTIC_SEARCH)
        invalid_params.similarity_threshold = 1.5  # Invalid value
        
        # Should handle gracefully without crashing
        analysis = await retrieval_optimizer.analyze_current_performance()
        assert isinstance(analysis, dict)

if __name__ == "__main__":
    pytest.main([__file__])