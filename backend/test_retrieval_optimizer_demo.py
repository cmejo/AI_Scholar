"""
Demo script for Retrieval Optimizer Service functionality.
"""

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from services.retrieval_optimizer import (
    RetrievalOptimizer,
    RetrievalParameters,
    RetrievalStrategy,
    PerformanceMetrics,
    OptimizationResult
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockRedisClient:
    """Mock Redis client for demo."""
    
    def __init__(self):
        self.data = {}
        self.lists = {}
    
    async def setex(self, key, ttl, value):
        self.data[key] = value
        return True
    
    async def get(self, key):
        return self.data.get(key)
    
    async def lpush(self, key, value):
        if key not in self.lists:
            self.lists[key] = []
        self.lists[key].insert(0, value)
        return len(self.lists[key])
    
    async def ltrim(self, key, start, stop):
        if key in self.lists:
            self.lists[key] = self.lists[key][start:stop+1]
        return True

async def demo_performance_data_collection():
    """Demonstrate performance data collection."""
    print("\n" + "="*60)
    print("PERFORMANCE DATA COLLECTION DEMO")
    print("="*60)
    
    # Initialize optimizer
    optimizer = RetrievalOptimizer()
    optimizer.redis_client = MockRedisClient()
    
    # Mock database storage
    async def mock_store_performance_data(data):
        print(f"  📊 Stored performance data for query: {data['query_id']}")
    
    optimizer._store_performance_data = mock_store_performance_data
    
    # Create sample retrieval configurations
    configurations = [
        RetrievalParameters(
            strategy=RetrievalStrategy.HYBRID_SEARCH,
            similarity_threshold=0.7,
            semantic_weight=0.7,
            keyword_weight=0.3,
            max_results=10
        ),
        RetrievalParameters(
            strategy=RetrievalStrategy.SEMANTIC_SEARCH,
            similarity_threshold=0.8,
            semantic_weight=0.9,
            keyword_weight=0.1,
            max_results=15
        ),
        RetrievalParameters(
            strategy=RetrievalStrategy.KNOWLEDGE_GRAPH_SEARCH,
            similarity_threshold=0.75,
            semantic_weight=0.6,
            keyword_weight=0.2,
            knowledge_graph_weight=0.4,
            max_results=12
        )
    ]
    
    print("Collecting performance data for different retrieval configurations...")
    
    for i, config in enumerate(configurations):
        # Simulate performance metrics
        metrics = PerformanceMetrics(
            relevance_score=random.uniform(0.6, 0.9),
            response_time=random.uniform(0.8, 3.0),
            user_satisfaction=random.uniform(0.5, 0.9),
            precision=random.uniform(0.6, 0.85),
            recall=random.uniform(0.65, 0.9),
            f1_score=random.uniform(0.6, 0.87),
            sample_size=random.randint(50, 200),
            timestamp=datetime.now()
        )
        
        query_id = f"query_{i+1:03d}"
        success = await optimizer.collect_performance_data(query_id, config, metrics)
        
        print(f"\n- Query: {query_id}")
        print(f"  Strategy: {config.strategy.value}")
        print(f"  Relevance: {metrics.relevance_score:.3f}")
        print(f"  Response Time: {metrics.response_time:.2f}s")
        print(f"  User Satisfaction: {metrics.user_satisfaction:.3f}")
        print(f"  Overall Score: {metrics.overall_score():.3f}")
        print(f"  Collected: {'✓' if success else '✗'}")

async def demo_performance_analysis():
    """Demonstrate performance analysis."""
    print("\n" + "="*60)
    print("PERFORMANCE ANALYSIS DEMO")
    print("="*60)
    
    # Initialize optimizer
    optimizer = RetrievalOptimizer()
    optimizer.redis_client = MockRedisClient()
    
    # Generate sample performance data
    performance_data = []
    strategies = [RetrievalStrategy.HYBRID_SEARCH, RetrievalStrategy.SEMANTIC_SEARCH, RetrievalStrategy.KEYWORD_SEARCH]
    
    for i in range(30):
        strategy = random.choice(strategies)
        base_time = datetime.now() - timedelta(hours=random.randint(1, 24))
        
        # Simulate different performance characteristics for different strategies
        if strategy == RetrievalStrategy.SEMANTIC_SEARCH:
            relevance_base = 0.85
            response_time_base = 1.2
        elif strategy == RetrievalStrategy.HYBRID_SEARCH:
            relevance_base = 0.8
            response_time_base = 1.8
        else:  # KEYWORD_SEARCH
            relevance_base = 0.7
            response_time_base = 0.9
        
        performance_data.append({
            'query_id': f'q{i+1}',
            'parameters': {
                'strategy': strategy.value,
                'similarity_threshold': random.uniform(0.6, 0.9),
                'semantic_weight': random.uniform(0.5, 0.9),
                'keyword_weight': random.uniform(0.1, 0.5),
                'max_results': random.randint(5, 20)
            },
            'metrics': {
                'relevance_score': relevance_base + random.uniform(-0.15, 0.1),
                'response_time': response_time_base + random.uniform(-0.3, 0.8),
                'user_satisfaction': random.uniform(0.6, 0.9),
                'f1_score': random.uniform(0.65, 0.85)
            },
            'timestamp': base_time.isoformat()
        })
    
    # Mock performance data retrieval
    async def mock_get_performance_data(strategy=None, time_window_hours=24):
        return performance_data
    
    optimizer._get_performance_data = mock_get_performance_data
    
    print("Analyzing current performance...")
    analysis = await optimizer.analyze_current_performance(time_window_hours=24)
    
    print(f"\nPerformance Analysis Results:")
    print(f"- Total Queries: {analysis['total_queries']}")
    print(f"- Strategy Distribution: {analysis['strategy_distribution']}")
    
    if 'performance_trends' in analysis and analysis['performance_trends']:
        print(f"\nPerformance Trends:")
        for metric, trend in analysis['performance_trends'].items():
            if isinstance(trend, dict):
                direction = trend.get('direction', 'unknown')
                current_value = trend.get('current_value', 0)
                print(f"  - {metric}: {direction} (current: {current_value:.3f})")
    
    if 'bottlenecks' in analysis:
        print(f"\nBottlenecks Identified: {len(analysis['bottlenecks'])}")
        for bottleneck in analysis['bottlenecks']:
            print(f"  - {bottleneck['type']}: {bottleneck['description']} (severity: {bottleneck['severity']})")
    
    if 'optimization_opportunities' in analysis:
        print(f"\nOptimization Opportunities: {len(analysis['optimization_opportunities'])}")
        for opportunity in analysis['optimization_opportunities']:
            print(f"  - {opportunity['type']}: {opportunity['description']}")

async def demo_parameter_optimization():
    """Demonstrate parameter optimization."""
    print("\n" + "="*60)
    print("PARAMETER OPTIMIZATION DEMO")
    print("="*60)
    
    # Initialize optimizer
    optimizer = RetrievalOptimizer()
    optimizer.redis_client = MockRedisClient()
    
    # Current parameters
    current_parameters = RetrievalParameters(
        strategy=RetrievalStrategy.HYBRID_SEARCH,
        similarity_threshold=0.7,
        semantic_weight=0.7,
        keyword_weight=0.3,
        max_results=10,
        hierarchical_levels=3,
        knowledge_graph_weight=0.2,
        reranking_enabled=True,
        personalization_weight=0.1,
        context_window=5
    )
    
    print("Current Parameters:")
    print(f"- Strategy: {current_parameters.strategy.value}")
    print(f"- Similarity Threshold: {current_parameters.similarity_threshold}")
    print(f"- Semantic Weight: {current_parameters.semantic_weight}")
    print(f"- Keyword Weight: {current_parameters.keyword_weight}")
    print(f"- Max Results: {current_parameters.max_results}")
    
    # Generate performance data for optimization
    performance_data = []
    for i in range(50):  # Sufficient data for optimization
        # Simulate performance based on parameter values
        sim_threshold = random.uniform(0.6, 0.9)
        sem_weight = random.uniform(0.5, 0.9)
        key_weight = random.uniform(0.1, 0.5)
        max_results = random.randint(5, 20)
        
        # Better performance with higher similarity threshold and balanced weights
        relevance_score = 0.6 + (sim_threshold - 0.6) * 0.5 + abs(sem_weight - 0.7) * -0.2
        response_time = 1.0 + (max_results - 10) * 0.1 + random.uniform(-0.2, 0.4)
        user_satisfaction = relevance_score * 0.9 + random.uniform(-0.1, 0.1)
        f1_score = relevance_score * 0.85 + random.uniform(-0.05, 0.1)
        
        performance_data.append({
            'parameters': {
                'strategy': 'hybrid_search',
                'similarity_threshold': sim_threshold,
                'semantic_weight': sem_weight,
                'keyword_weight': key_weight,
                'max_results': max_results
            },
            'metrics': {
                'relevance_score': max(0.4, min(1.0, relevance_score)),
                'response_time': max(0.5, response_time),
                'user_satisfaction': max(0.3, min(1.0, user_satisfaction)),
                'f1_score': max(0.4, min(1.0, f1_score))
            }
        })
    
    # Mock performance data retrieval
    async def mock_get_performance_data(strategy=None, time_window_hours=168):
        return performance_data
    
    optimizer._get_performance_data = mock_get_performance_data
    
    print("\nOptimizing parameters...")
    
    try:
        optimization_result = await optimizer.optimize_parameters(
            current_parameters,
            performance_target={
                'relevance_score': 0.85,
                'response_time': 1.5,
                'user_satisfaction': 0.8,
                'f1_score': 0.75
            }
        )
        
        print(f"\nOptimization Results:")
        print(f"- Optimization Type: {optimization_result.optimization_type}")
        print(f"- Performance Improvement: {optimization_result.performance_improvement:.3f}")
        print(f"- Confidence: {optimization_result.confidence:.3f}")
        
        print(f"\nOptimized Parameters:")
        optimized = optimization_result.optimized_parameters
        print(f"- Similarity Threshold: {current_parameters.similarity_threshold:.3f} → {optimized.similarity_threshold:.3f}")
        print(f"- Semantic Weight: {current_parameters.semantic_weight:.3f} → {optimized.semantic_weight:.3f}")
        print(f"- Keyword Weight: {current_parameters.keyword_weight:.3f} → {optimized.keyword_weight:.3f}")
        print(f"- Max Results: {current_parameters.max_results} → {optimized.max_results}")
        
        # Apply optimization
        print(f"\nApplying optimization...")
        success = await optimizer.apply_optimization(optimization_result)
        print(f"Applied: {'✓' if success else '✗'}")
        
    except ValueError as e:
        print(f"Optimization failed: {e}")

async def demo_optimization_monitoring():
    """Demonstrate optimization impact monitoring."""
    print("\n" + "="*60)
    print("OPTIMIZATION MONITORING DEMO")
    print("="*60)
    
    # Initialize optimizer
    optimizer = RetrievalOptimizer()
    optimizer.redis_client = MockRedisClient()
    
    # Create optimization result
    original_params = RetrievalParameters(
        strategy=RetrievalStrategy.HYBRID_SEARCH,
        similarity_threshold=0.7,
        semantic_weight=0.7,
        keyword_weight=0.3,
        max_results=10
    )
    
    optimized_params = RetrievalParameters(
        strategy=RetrievalStrategy.HYBRID_SEARCH,
        similarity_threshold=0.8,
        semantic_weight=0.75,
        keyword_weight=0.25,
        max_results=8
    )
    
    optimization_result = OptimizationResult(
        original_parameters=original_params,
        optimized_parameters=optimized_params,
        performance_improvement=0.15,
        confidence=0.8,
        optimization_type="grid_search",
        applied_at=datetime.now() - timedelta(hours=12)
    )
    
    # Generate before/after performance data
    def generate_performance_data(is_after_optimization=False):
        data = []
        for i in range(20):
            if is_after_optimization:
                # Better performance after optimization
                relevance = random.uniform(0.75, 0.9)
                response_time = random.uniform(1.0, 2.0)
                satisfaction = random.uniform(0.7, 0.85)
                f1 = random.uniform(0.7, 0.85)
            else:
                # Baseline performance before optimization
                relevance = random.uniform(0.65, 0.8)
                response_time = random.uniform(1.5, 2.5)
                satisfaction = random.uniform(0.6, 0.75)
                f1 = random.uniform(0.6, 0.75)
            
            data.append({
                'metrics': {
                    'relevance_score': relevance,
                    'response_time': response_time,
                    'user_satisfaction': satisfaction,
                    'f1_score': f1
                }
            })
        return data
    
    before_data = generate_performance_data(is_after_optimization=False)
    after_data = generate_performance_data(is_after_optimization=True)
    
    # Mock performance data retrieval
    async def mock_get_performance_data(strategy=None, time_window_hours=24, start_time=None, end_time=None):
        if start_time and start_time > optimization_result.applied_at:
            return after_data
        else:
            return before_data
    
    async def mock_store_monitoring_results(analysis):
        print(f"  📊 Stored monitoring results for optimization: {analysis['optimization_id']}")
    
    optimizer._get_performance_data = mock_get_performance_data
    optimizer._store_monitoring_results = mock_store_monitoring_results
    
    print("Monitoring optimization impact...")
    impact_analysis = await optimizer.monitor_optimization_impact(
        optimization_result,
        monitoring_period_hours=24
    )
    
    if 'error' not in impact_analysis:
        print(f"\nImpact Analysis Results:")
        print(f"- Optimization ID: {impact_analysis['optimization_id']}")
        print(f"- Expected Improvement: {impact_analysis['expected_improvement']:.3f}")
        print(f"- Actual Improvement: {impact_analysis['actual_improvement']:.3f}")
        
        success_info = impact_analysis['optimization_success']
        print(f"- Optimization Success: {'✓' if success_info['success'] else '✗'}")
        print(f"- Improvement Ratio: {success_info['improvement_ratio']:.2f}")
        
        print(f"\nPerformance Changes:")
        for metric, change in impact_analysis['performance_changes'].items():
            direction = "↑" if change > 0 else "↓" if change < 0 else "→"
            print(f"  - {metric}: {change:+.1%} {direction}")

async def demo_optimization_recommendations():
    """Demonstrate optimization recommendations."""
    print("\n" + "="*60)
    print("OPTIMIZATION RECOMMENDATIONS DEMO")
    print("="*60)
    
    # Initialize optimizer
    optimizer = RetrievalOptimizer()
    optimizer.redis_client = MockRedisClient()
    
    current_parameters = RetrievalParameters(
        strategy=RetrievalStrategy.HYBRID_SEARCH,
        similarity_threshold=0.6,  # Low threshold
        semantic_weight=0.5,       # Suboptimal weight
        keyword_weight=0.5,
        max_results=20             # High result count
    )
    
    # Mock performance analysis with bottlenecks and opportunities
    mock_analysis = {
        'total_queries': 100,
        'strategy_distribution': {'hybrid_search': 80, 'semantic_search': 20},
        'bottlenecks': [
            {
                'type': 'response_time',
                'severity': 'high',
                'description': 'Average response time 4.2s exceeds threshold',
                'metric_value': 4.2,
                'threshold': 3.0
            },
            {
                'type': 'relevance',
                'severity': 'medium',
                'description': 'Average relevance score 0.65 below threshold',
                'metric_value': 0.65,
                'threshold': 0.7
            }
        ],
        'optimization_opportunities': [
            {
                'type': 'parameter_optimization',
                'parameter': 'similarity_threshold',
                'description': 'Parameter similarity_threshold shows high variance (CV=0.25), optimization potential',
                'expected_impact': 0.2
            },
            {
                'type': 'strategy_optimization',
                'description': 'Strategy optimization: semantic_search outperforms hybrid_search',
                'best_strategy': 'semantic_search',
                'worst_strategy': 'hybrid_search',
                'expected_impact': 0.15
            }
        ]
    }
    
    # Mock analysis method
    async def mock_analyze_performance(strategy):
        return mock_analysis
    
    optimizer.analyze_current_performance = mock_analyze_performance
    
    print("Current Parameters:")
    print(f"- Strategy: {current_parameters.strategy.value}")
    print(f"- Similarity Threshold: {current_parameters.similarity_threshold}")
    print(f"- Semantic Weight: {current_parameters.semantic_weight}")
    print(f"- Max Results: {current_parameters.max_results}")
    
    print("\nGenerating optimization recommendations...")
    recommendations = await optimizer.get_optimization_recommendations(current_parameters)
    
    print(f"\nGenerated {len(recommendations)} recommendations:")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. Type: {rec['type']}")
        if 'parameter' in rec:
            print(f"   Parameter: {rec['parameter']}")
            if 'current_value' in rec and 'recommended_value' in rec:
                print(f"   Current Value: {rec['current_value']}")
                print(f"   Recommended Value: {rec['recommended_value']}")
        if 'reason' in rec:
            print(f"   Reason: {rec['reason']}")
        print(f"   Expected Impact: {rec.get('expected_impact', 0):.3f}")
        print(f"   Confidence: {rec.get('confidence', 0):.3f}")

async def demo_retrieval_strategies():
    """Demonstrate different retrieval strategies."""
    print("\n" + "="*60)
    print("RETRIEVAL STRATEGIES COMPARISON DEMO")
    print("="*60)
    
    strategies = [
        (RetrievalStrategy.SEMANTIC_SEARCH, "Pure semantic similarity search"),
        (RetrievalStrategy.KEYWORD_SEARCH, "Traditional keyword-based search"),
        (RetrievalStrategy.HYBRID_SEARCH, "Combined semantic and keyword search"),
        (RetrievalStrategy.HIERARCHICAL_SEARCH, "Multi-level hierarchical search"),
        (RetrievalStrategy.KNOWLEDGE_GRAPH_SEARCH, "Knowledge graph enhanced search")
    ]
    
    print("Comparing retrieval strategies:")
    
    for strategy, description in strategies:
        # Create parameters for each strategy
        if strategy == RetrievalStrategy.SEMANTIC_SEARCH:
            params = RetrievalParameters(
                strategy=strategy,
                similarity_threshold=0.8,
                semantic_weight=1.0,
                keyword_weight=0.0,
                max_results=10
            )
            # Simulate high relevance, medium speed
            simulated_metrics = PerformanceMetrics(
                relevance_score=0.85,
                response_time=1.8,
                user_satisfaction=0.8,
                precision=0.82,
                recall=0.75,
                f1_score=0.78,
                sample_size=100,
                timestamp=datetime.now()
            )
        
        elif strategy == RetrievalStrategy.KEYWORD_SEARCH:
            params = RetrievalParameters(
                strategy=strategy,
                similarity_threshold=0.6,
                semantic_weight=0.0,
                keyword_weight=1.0,
                max_results=15
            )
            # Simulate medium relevance, high speed
            simulated_metrics = PerformanceMetrics(
                relevance_score=0.7,
                response_time=0.9,
                user_satisfaction=0.65,
                precision=0.68,
                recall=0.8,
                f1_score=0.73,
                sample_size=100,
                timestamp=datetime.now()
            )
        
        elif strategy == RetrievalStrategy.HYBRID_SEARCH:
            params = RetrievalParameters(
                strategy=strategy,
                similarity_threshold=0.75,
                semantic_weight=0.7,
                keyword_weight=0.3,
                max_results=12
            )
            # Simulate balanced performance
            simulated_metrics = PerformanceMetrics(
                relevance_score=0.78,
                response_time=1.4,
                user_satisfaction=0.75,
                precision=0.76,
                recall=0.78,
                f1_score=0.77,
                sample_size=100,
                timestamp=datetime.now()
            )
        
        elif strategy == RetrievalStrategy.KNOWLEDGE_GRAPH_SEARCH:
            params = RetrievalParameters(
                strategy=strategy,
                similarity_threshold=0.7,
                semantic_weight=0.6,
                keyword_weight=0.2,
                knowledge_graph_weight=0.4,
                max_results=10
            )
            # Simulate high relevance, slower speed
            simulated_metrics = PerformanceMetrics(
                relevance_score=0.88,
                response_time=2.2,
                user_satisfaction=0.82,
                precision=0.85,
                recall=0.8,
                f1_score=0.82,
                sample_size=100,
                timestamp=datetime.now()
            )
        
        else:  # HIERARCHICAL_SEARCH
            params = RetrievalParameters(
                strategy=strategy,
                similarity_threshold=0.75,
                semantic_weight=0.8,
                keyword_weight=0.2,
                hierarchical_levels=4,
                max_results=8
            )
            # Simulate very high relevance, medium speed
            simulated_metrics = PerformanceMetrics(
                relevance_score=0.9,
                response_time=1.6,
                user_satisfaction=0.85,
                precision=0.88,
                recall=0.82,
                f1_score=0.85,
                sample_size=100,
                timestamp=datetime.now()
            )
        
        print(f"\n{strategy.value.upper()}:")
        print(f"  Description: {description}")
        print(f"  Relevance Score: {simulated_metrics.relevance_score:.3f}")
        print(f"  Response Time: {simulated_metrics.response_time:.2f}s")
        print(f"  User Satisfaction: {simulated_metrics.user_satisfaction:.3f}")
        print(f"  F1 Score: {simulated_metrics.f1_score:.3f}")
        print(f"  Overall Score: {simulated_metrics.overall_score():.3f}")
        
        # Show key parameters
        print(f"  Key Parameters:")
        print(f"    - Similarity Threshold: {params.similarity_threshold}")
        print(f"    - Semantic Weight: {params.semantic_weight}")
        print(f"    - Keyword Weight: {params.keyword_weight}")
        if params.knowledge_graph_weight > 0:
            print(f"    - Knowledge Graph Weight: {params.knowledge_graph_weight}")
        if params.hierarchical_levels > 1:
            print(f"    - Hierarchical Levels: {params.hierarchical_levels}")

async def main():
    """Run all demos."""
    print("RETRIEVAL OPTIMIZER SERVICE DEMO")
    print("="*60)
    
    try:
        await demo_performance_data_collection()
        await demo_performance_analysis()
        await demo_parameter_optimization()
        await demo_optimization_monitoring()
        await demo_optimization_recommendations()
        await demo_retrieval_strategies()
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())