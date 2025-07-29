"""
Retrieval Strategy Optimizer for dynamically adjusting retrieval parameters based on performance.
"""

import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
from enum import Enum
import statistics

from core.database import get_db
from core.redis_client import get_redis_client

logger = logging.getLogger(__name__)

class RetrievalStrategy(Enum):
    """Types of retrieval strategies."""
    SEMANTIC_SEARCH = "semantic_search"
    KEYWORD_SEARCH = "keyword_search"
    HYBRID_SEARCH = "hybrid_search"
    HIERARCHICAL_SEARCH = "hierarchical_search"
    KNOWLEDGE_GRAPH_SEARCH = "knowledge_graph_search"

class OptimizationMetric(Enum):
    """Metrics for optimization."""
    RELEVANCE_SCORE = "relevance_score"
    RESPONSE_TIME = "response_time"
    USER_SATISFACTION = "user_satisfaction"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"

@dataclass
class RetrievalParameters:
    """Represents retrieval parameters."""
    strategy: RetrievalStrategy
    similarity_threshold: float = 0.7
    max_results: int = 10
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3
    hierarchical_levels: int = 3
    knowledge_graph_weight: float = 0.2
    reranking_enabled: bool = True
    personalization_weight: float = 0.1
    context_window: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['strategy'] = self.strategy.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RetrievalParameters':
        """Create from dictionary."""
        data = data.copy()
        data['strategy'] = RetrievalStrategy(data['strategy'])
        return cls(**data)

@dataclass
class PerformanceMetrics:
    """Represents performance metrics for a retrieval configuration."""
    relevance_score: float
    response_time: float
    user_satisfaction: float
    precision: float
    recall: float
    f1_score: float
    sample_size: int
    timestamp: datetime
    
    def overall_score(self, weights: Dict[str, float] = None) -> float:
        """Calculate overall performance score."""
        if weights is None:
            weights = {
                'relevance_score': 0.3,
                'response_time': 0.2,  # Lower is better, so we'll invert
                'user_satisfaction': 0.3,
                'f1_score': 0.2
            }
        
        # Normalize response time (invert since lower is better)
        normalized_response_time = max(0, 1 - (self.response_time / 10.0))  # Assume 10s is worst case
        
        score = (
            weights.get('relevance_score', 0) * self.relevance_score +
            weights.get('response_time', 0) * normalized_response_time +
            weights.get('user_satisfaction', 0) * self.user_satisfaction +
            weights.get('f1_score', 0) * self.f1_score
        )
        
        return min(max(score, 0), 1)  # Clamp between 0 and 1

@dataclass
class OptimizationResult:
    """Represents the result of an optimization."""
    original_parameters: RetrievalParameters
    optimized_parameters: RetrievalParameters
    performance_improvement: float
    confidence: float
    optimization_type: str
    applied_at: datetime

class RetrievalOptimizer:
    """Service for optimizing retrieval strategies based on performance data."""
    
    def __init__(self):
        self.redis_client = None
        self.optimization_cache_ttl = 7200  # 2 hours
        self.min_sample_size = 20
        self.optimization_threshold = 0.05  # 5% improvement threshold
        self.parameter_bounds = {
            'similarity_threshold': (0.5, 0.95),
            'max_results': (5, 50),
            'semantic_weight': (0.1, 1.0),
            'keyword_weight': (0.0, 0.9),
            'hierarchical_levels': (1, 5),
            'knowledge_graph_weight': (0.0, 0.5),
            'personalization_weight': (0.0, 0.3),
            'context_window': (1, 10)
        }
        
    async def initialize(self):
        """Initialize the retrieval optimizer service."""
        try:
            self.redis_client = await get_redis_client()
            logger.info("RetrievalOptimizer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RetrievalOptimizer: {e}")
            raise
    
    async def collect_performance_data(self, query_id: str, parameters: RetrievalParameters,
                                     metrics: PerformanceMetrics) -> bool:
        """Collect performance data for a retrieval configuration."""
        try:
            # Store performance data
            performance_data = {
                'query_id': query_id,
                'parameters': parameters.to_dict(),
                'metrics': asdict(metrics),
                'timestamp': datetime.now().isoformat()
            }
            
            # Store in Redis for real-time access
            await self.redis_client.lpush(
                'retrieval_performance_data',
                json.dumps(performance_data, default=str)
            )
            
            # Keep only recent data (last 1000 entries)
            await self.redis_client.ltrim('retrieval_performance_data', 0, 999)
            
            # Store in database for long-term analysis
            await self._store_performance_data(performance_data)
            
            logger.debug(f"Collected performance data for query {query_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error collecting performance data: {e}")
            return False
    
    async def analyze_current_performance(self, strategy: RetrievalStrategy = None,
                                        time_window_hours: int = 24) -> Dict[str, Any]:
        """Analyze current retrieval performance."""
        try:
            # Get performance data
            performance_data = await self._get_performance_data(strategy, time_window_hours)
            
            if not performance_data:
                return {'error': 'No performance data available'}
            
            # Calculate aggregate metrics
            analysis = {
                'total_queries': len(performance_data),
                'strategy_distribution': self._analyze_strategy_distribution(performance_data),
                'performance_trends': await self._analyze_performance_trends(performance_data),
                'parameter_correlations': await self._analyze_parameter_correlations(performance_data),
                'bottlenecks': await self._identify_bottlenecks(performance_data),
                'optimization_opportunities': await self._identify_optimization_opportunities(performance_data)
            }
            
            # Cache results
            cache_key = f"performance_analysis:{strategy.value if strategy else 'all'}:{time_window_hours}"
            await self.redis_client.setex(
                cache_key,
                self.optimization_cache_ttl,
                json.dumps(analysis, default=str)
            )
            
            logger.info(f"Analyzed performance for {len(performance_data)} queries")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing current performance: {e}")
            return {}
    
    async def optimize_parameters(self, current_parameters: RetrievalParameters,
                                performance_target: Dict[str, float] = None) -> OptimizationResult:
        """Optimize retrieval parameters based on performance data."""
        try:
            if performance_target is None:
                performance_target = {
                    'relevance_score': 0.8,
                    'response_time': 2.0,
                    'user_satisfaction': 0.75,
                    'f1_score': 0.7
                }
            
            # Get historical performance data
            performance_data = await self._get_performance_data(
                current_parameters.strategy, 
                time_window_hours=168  # 1 week
            )
            
            if len(performance_data) < self.min_sample_size:
                raise ValueError(f"Insufficient data for optimization (need {self.min_sample_size}, got {len(performance_data)})")
            
            # Find optimal parameters using different optimization strategies
            optimization_results = []
            
            # Grid search optimization
            grid_result = await self._grid_search_optimization(current_parameters, performance_data, performance_target)
            if grid_result:
                optimization_results.append(grid_result)
            
            # Gradient-based optimization
            gradient_result = await self._gradient_optimization(current_parameters, performance_data, performance_target)
            if gradient_result:
                optimization_results.append(gradient_result)
            
            # Bayesian optimization
            bayesian_result = await self._bayesian_optimization(current_parameters, performance_data, performance_target)
            if bayesian_result:
                optimization_results.append(bayesian_result)
            
            # Select best optimization result
            if not optimization_results:
                raise ValueError("No optimization results generated")
            
            best_result = max(optimization_results, key=lambda x: x.performance_improvement)
            
            # Validate improvement threshold
            if best_result.performance_improvement < self.optimization_threshold:
                logger.info(f"Optimization improvement {best_result.performance_improvement:.3f} below threshold {self.optimization_threshold}")
            
            logger.info(f"Optimized parameters with {best_result.performance_improvement:.3f} improvement")
            return best_result
            
        except Exception as e:
            logger.error(f"Error optimizing parameters: {e}")
            raise
    
    async def apply_optimization(self, optimization_result: OptimizationResult) -> bool:
        """Apply optimized parameters to the retrieval system."""
        try:
            # Store optimized parameters in Redis for retrieval service
            optimization_key = f"retrieval_optimization:{optimization_result.optimized_parameters.strategy.value}"
            optimization_data = {
                'parameters': optimization_result.optimized_parameters.to_dict(),
                'performance_improvement': optimization_result.performance_improvement,
                'confidence': optimization_result.confidence,
                'applied_at': optimization_result.applied_at.isoformat(),
                'optimization_type': optimization_result.optimization_type
            }
            
            await self.redis_client.setex(
                optimization_key,
                86400,  # 24 hours
                json.dumps(optimization_data, default=str)
            )
            
            # Log optimization application
            await self._log_optimization_application(optimization_result)
            
            # Store optimization history
            await self._store_optimization_history(optimization_result)
            
            logger.info(f"Applied optimization for {optimization_result.optimized_parameters.strategy.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying optimization: {e}")
            return False
    
    async def monitor_optimization_impact(self, optimization_result: OptimizationResult,
                                        monitoring_period_hours: int = 24) -> Dict[str, Any]:
        """Monitor the impact of applied optimizations."""
        try:
            # Get performance data before and after optimization
            before_data = await self._get_performance_data(
                optimization_result.original_parameters.strategy,
                time_window_hours=monitoring_period_hours,
                end_time=optimization_result.applied_at
            )
            
            after_data = await self._get_performance_data(
                optimization_result.optimized_parameters.strategy,
                time_window_hours=monitoring_period_hours,
                start_time=optimization_result.applied_at
            )
            
            if not before_data or not after_data:
                return {'error': 'Insufficient data for impact monitoring'}
            
            # Calculate performance changes
            before_metrics = self._calculate_aggregate_metrics(before_data)
            after_metrics = self._calculate_aggregate_metrics(after_data)
            
            impact_analysis = {
                'optimization_id': f"{optimization_result.optimization_type}_{optimization_result.applied_at.strftime('%Y%m%d_%H%M%S')}",
                'monitoring_period_hours': monitoring_period_hours,
                'before_metrics': before_metrics,
                'after_metrics': after_metrics,
                'performance_changes': self._calculate_performance_changes(before_metrics, after_metrics),
                'expected_improvement': optimization_result.performance_improvement,
                'actual_improvement': self._calculate_actual_improvement(before_metrics, after_metrics),
                'optimization_success': self._evaluate_optimization_success(optimization_result, before_metrics, after_metrics)
            }
            
            # Store monitoring results
            await self._store_monitoring_results(impact_analysis)
            
            logger.info(f"Monitored optimization impact: {impact_analysis['actual_improvement']:.3f} actual vs {optimization_result.performance_improvement:.3f} expected")
            return impact_analysis
            
        except Exception as e:
            logger.error(f"Error monitoring optimization impact: {e}")
            return {}
    
    async def get_optimization_recommendations(self, current_parameters: RetrievalParameters) -> List[Dict[str, Any]]:
        """Get optimization recommendations based on current performance."""
        try:
            # Analyze current performance
            performance_analysis = await self.analyze_current_performance(current_parameters.strategy)
            
            if 'error' in performance_analysis:
                return []
            
            recommendations = []
            
            # Analyze bottlenecks
            bottlenecks = performance_analysis.get('bottlenecks', [])
            for bottleneck in bottlenecks:
                recommendation = await self._generate_bottleneck_recommendation(bottleneck, current_parameters)
                if recommendation:
                    recommendations.append(recommendation)
            
            # Analyze optimization opportunities
            opportunities = performance_analysis.get('optimization_opportunities', [])
            for opportunity in opportunities:
                recommendation = await self._generate_opportunity_recommendation(opportunity, current_parameters)
                if recommendation:
                    recommendations.append(recommendation)
            
            # Sort by expected impact
            recommendations.sort(key=lambda x: x.get('expected_impact', 0), reverse=True)
            
            logger.info(f"Generated {len(recommendations)} optimization recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting optimization recommendations: {e}")
            return []
    
    async def _store_performance_data(self, performance_data: Dict[str, Any]):
        """Store performance data in database."""
        try:
            from core.database import AnalyticsEvent
            
            db_session = next(get_db())
            try:
                analytics_event = AnalyticsEvent(
                    event_type="retrieval_performance",
                    event_data=performance_data,
                    timestamp=datetime.now()
                )
                
                db_session.add(analytics_event)
                db_session.commit()
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error storing performance data: {e}")
    
    async def _get_performance_data(self, strategy: RetrievalStrategy = None,
                                  time_window_hours: int = 24,
                                  start_time: datetime = None,
                                  end_time: datetime = None) -> List[Dict[str, Any]]:
        """Get performance data from database."""
        try:
            from core.database import AnalyticsEvent
            
            db_session = next(get_db())
            try:
                # Set time bounds
                if end_time is None:
                    end_time = datetime.now()
                if start_time is None:
                    start_time = end_time - timedelta(hours=time_window_hours)
                
                # Query performance data
                query = db_session.query(AnalyticsEvent).filter(
                    AnalyticsEvent.event_type == 'retrieval_performance',
                    AnalyticsEvent.timestamp >= start_time,
                    AnalyticsEvent.timestamp <= end_time
                )
                
                results = query.all()
                
                performance_data = []
                for result in results:
                    data = result.event_data or {}
                    
                    # Filter by strategy if specified
                    if strategy and data.get('parameters', {}).get('strategy') != strategy.value:
                        continue
                    
                    performance_data.append(data)
                
                return performance_data
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error getting performance data: {e}")
            return []
    
    def _analyze_strategy_distribution(self, performance_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of retrieval strategies."""
        strategy_counts = Counter()
        
        for data in performance_data:
            strategy = data.get('parameters', {}).get('strategy', 'unknown')
            strategy_counts[strategy] += 1
        
        return dict(strategy_counts)
    
    async def _analyze_performance_trends(self, performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        try:
            # Sort by timestamp
            sorted_data = sorted(performance_data, key=lambda x: x.get('timestamp', ''))
            
            if len(sorted_data) < 2:
                return {'error': 'Insufficient data for trend analysis'}
            
            # Calculate trends for key metrics
            metrics = ['relevance_score', 'response_time', 'user_satisfaction', 'f1_score']
            trends = {}
            
            for metric in metrics:
                values = []
                timestamps = []
                
                for data in sorted_data:
                    metric_data = data.get('metrics', {})
                    if metric in metric_data:
                        values.append(metric_data[metric])
                        timestamps.append(data.get('timestamp', ''))
                
                if len(values) >= 2:
                    # Simple trend calculation (slope of linear regression)
                    x = list(range(len(values)))
                    slope = np.polyfit(x, values, 1)[0] if len(values) > 1 else 0
                    
                    trends[metric] = {
                        'slope': slope,
                        'direction': 'improving' if slope > 0 else 'declining' if slope < 0 else 'stable',
                        'current_value': values[-1] if values else 0,
                        'change_rate': slope * len(values) if len(values) > 1 else 0
                    }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")
            return {}
    
    async def _analyze_parameter_correlations(self, performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze correlations between parameters and performance."""
        try:
            if len(performance_data) < 10:
                return {'error': 'Insufficient data for correlation analysis'}
            
            # Extract parameter and metric values
            parameter_values = defaultdict(list)
            metric_values = defaultdict(list)
            
            for data in performance_data:
                parameters = data.get('parameters', {})
                metrics = data.get('metrics', {})
                
                for param, value in parameters.items():
                    if isinstance(value, (int, float)):
                        parameter_values[param].append(value)
                        
                        # Store corresponding metric values
                        for metric, metric_value in metrics.items():
                            if isinstance(metric_value, (int, float)):
                                if len(parameter_values[param]) == len(metric_values[f"{param}_{metric}"]) + 1:
                                    metric_values[f"{param}_{metric}"].append(metric_value)
            
            # Calculate correlations
            correlations = {}
            for param in parameter_values:
                correlations[param] = {}
                
                for metric in ['relevance_score', 'response_time', 'user_satisfaction', 'f1_score']:
                    key = f"{param}_{metric}"
                    if key in metric_values and len(parameter_values[param]) == len(metric_values[key]):
                        if len(parameter_values[param]) > 1:
                            correlation = np.corrcoef(parameter_values[param], metric_values[key])[0, 1]
                            if not np.isnan(correlation):
                                correlations[param][metric] = correlation
            
            return correlations
            
        except Exception as e:
            logger.error(f"Error analyzing parameter correlations: {e}")
            return {}
    
    async def _identify_bottlenecks(self, performance_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks."""
        try:
            bottlenecks = []
            
            # Analyze response time bottlenecks
            response_times = [data.get('metrics', {}).get('response_time', 0) for data in performance_data]
            if response_times:
                avg_response_time = statistics.mean(response_times)
                p95_response_time = np.percentile(response_times, 95)
                
                if avg_response_time > 3.0:  # 3 seconds threshold
                    bottlenecks.append({
                        'type': 'response_time',
                        'severity': 'high' if avg_response_time > 5.0 else 'medium',
                        'description': f'Average response time {avg_response_time:.2f}s exceeds threshold',
                        'metric_value': avg_response_time,
                        'threshold': 3.0
                    })
                
                if p95_response_time > 8.0:  # 8 seconds P95 threshold
                    bottlenecks.append({
                        'type': 'response_time_p95',
                        'severity': 'high',
                        'description': f'95th percentile response time {p95_response_time:.2f}s is too high',
                        'metric_value': p95_response_time,
                        'threshold': 8.0
                    })
            
            # Analyze relevance bottlenecks
            relevance_scores = [data.get('metrics', {}).get('relevance_score', 0) for data in performance_data]
            if relevance_scores:
                avg_relevance = statistics.mean(relevance_scores)
                
                if avg_relevance < 0.7:  # 70% relevance threshold
                    bottlenecks.append({
                        'type': 'relevance',
                        'severity': 'high' if avg_relevance < 0.5 else 'medium',
                        'description': f'Average relevance score {avg_relevance:.3f} below threshold',
                        'metric_value': avg_relevance,
                        'threshold': 0.7
                    })
            
            # Analyze user satisfaction bottlenecks
            satisfaction_scores = [data.get('metrics', {}).get('user_satisfaction', 0) for data in performance_data]
            if satisfaction_scores:
                avg_satisfaction = statistics.mean(satisfaction_scores)
                
                if avg_satisfaction < 0.75:  # 75% satisfaction threshold
                    bottlenecks.append({
                        'type': 'user_satisfaction',
                        'severity': 'medium',
                        'description': f'Average user satisfaction {avg_satisfaction:.3f} below threshold',
                        'metric_value': avg_satisfaction,
                        'threshold': 0.75
                    })
            
            return bottlenecks
            
        except Exception as e:
            logger.error(f"Error identifying bottlenecks: {e}")
            return []
    
    async def _identify_optimization_opportunities(self, performance_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify optimization opportunities."""
        try:
            opportunities = []
            
            # Analyze parameter variance
            parameter_stats = defaultdict(list)
            for data in performance_data:
                parameters = data.get('parameters', {})
                for param, value in parameters.items():
                    if isinstance(value, (int, float)):
                        parameter_stats[param].append(value)
            
            # Look for parameters with high variance (optimization potential)
            for param, values in parameter_stats.items():
                if len(values) > 5:
                    variance = np.var(values)
                    mean_val = np.mean(values)
                    cv = variance / mean_val if mean_val > 0 else 0  # Coefficient of variation
                    
                    if cv > 0.2:  # High variance threshold
                        opportunities.append({
                            'type': 'parameter_optimization',
                            'parameter': param,
                            'description': f'Parameter {param} shows high variance (CV={cv:.3f}), optimization potential',
                            'variance': variance,
                            'coefficient_of_variation': cv,
                            'expected_impact': min(cv * 0.5, 0.3)  # Estimate impact
                        })
            
            # Look for strategy-specific opportunities
            strategy_performance = defaultdict(list)
            for data in performance_data:
                strategy = data.get('parameters', {}).get('strategy', 'unknown')
                metrics = data.get('metrics', {})
                overall_score = self._calculate_overall_score(metrics)
                strategy_performance[strategy].append(overall_score)
            
            # Compare strategy performance
            if len(strategy_performance) > 1:
                strategy_means = {s: np.mean(scores) for s, scores in strategy_performance.items()}
                best_strategy = max(strategy_means, key=strategy_means.get)
                worst_strategy = min(strategy_means, key=strategy_means.get)
                
                improvement_potential = strategy_means[best_strategy] - strategy_means[worst_strategy]
                
                if improvement_potential > 0.1:  # 10% improvement potential
                    opportunities.append({
                        'type': 'strategy_optimization',
                        'description': f'Strategy optimization: {best_strategy} outperforms {worst_strategy}',
                        'best_strategy': best_strategy,
                        'worst_strategy': worst_strategy,
                        'improvement_potential': improvement_potential,
                        'expected_impact': improvement_potential * 0.8
                    })
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error identifying optimization opportunities: {e}")
            return []
    
    def _calculate_overall_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall performance score from metrics."""
        try:
            relevance = metrics.get('relevance_score', 0)
            response_time = metrics.get('response_time', 10)  # Default to high value
            satisfaction = metrics.get('user_satisfaction', 0)
            f1 = metrics.get('f1_score', 0)
            
            # Normalize response time (invert since lower is better)
            normalized_response_time = max(0, 1 - (response_time / 10.0))
            
            # Weighted average
            score = (
                0.3 * relevance +
                0.2 * normalized_response_time +
                0.3 * satisfaction +
                0.2 * f1
            )
            
            return min(max(score, 0), 1)
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 0.0
    
    async def _grid_search_optimization(self, current_parameters: RetrievalParameters,
                                      performance_data: List[Dict[str, Any]],
                                      performance_target: Dict[str, float]) -> OptimizationResult:
        """Perform grid search optimization."""
        try:
            # Define parameter grid
            param_grid = {
                'similarity_threshold': [0.6, 0.7, 0.8, 0.9],
                'semantic_weight': [0.5, 0.7, 0.9],
                'keyword_weight': [0.1, 0.3, 0.5],
                'max_results': [5, 10, 15, 20]
            }
            
            best_score = 0
            best_params = current_parameters
            
            # Evaluate current performance
            current_score = await self._evaluate_parameter_performance(current_parameters, performance_data)
            
            # Try different parameter combinations
            for similarity_threshold in param_grid['similarity_threshold']:
                for semantic_weight in param_grid['semantic_weight']:
                    for keyword_weight in param_grid['keyword_weight']:
                        for max_results in param_grid['max_results']:
                            # Create test parameters
                            test_params = RetrievalParameters(
                                strategy=current_parameters.strategy,
                                similarity_threshold=similarity_threshold,
                                semantic_weight=semantic_weight,
                                keyword_weight=keyword_weight,
                                max_results=max_results,
                                hierarchical_levels=current_parameters.hierarchical_levels,
                                knowledge_graph_weight=current_parameters.knowledge_graph_weight,
                                reranking_enabled=current_parameters.reranking_enabled,
                                personalization_weight=current_parameters.personalization_weight,
                                context_window=current_parameters.context_window
                            )
                            
                            # Evaluate performance
                            score = await self._evaluate_parameter_performance(test_params, performance_data)
                            
                            if score > best_score:
                                best_score = score
                                best_params = test_params
            
            # Calculate improvement
            improvement = best_score - current_score
            
            return OptimizationResult(
                original_parameters=current_parameters,
                optimized_parameters=best_params,
                performance_improvement=improvement,
                confidence=0.8,  # Grid search has high confidence
                optimization_type="grid_search",
                applied_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in grid search optimization: {e}")
            return None
    
    async def _gradient_optimization(self, current_parameters: RetrievalParameters,
                                   performance_data: List[Dict[str, Any]],
                                   performance_target: Dict[str, float]) -> OptimizationResult:
        """Perform gradient-based optimization."""
        try:
            # Simple gradient descent simulation
            learning_rate = 0.1
            iterations = 10
            
            best_params = current_parameters
            current_score = await self._evaluate_parameter_performance(current_parameters, performance_data)
            
            # Optimize key parameters
            for _ in range(iterations):
                # Calculate gradients (simplified)
                similarity_gradient = await self._calculate_parameter_gradient(
                    best_params, 'similarity_threshold', performance_data, step_size=0.05
                )
                semantic_gradient = await self._calculate_parameter_gradient(
                    best_params, 'semantic_weight', performance_data, step_size=0.1
                )
                
                # Update parameters
                new_similarity = best_params.similarity_threshold + learning_rate * similarity_gradient
                new_semantic = best_params.semantic_weight + learning_rate * semantic_gradient
                
                # Apply bounds
                new_similarity = max(0.5, min(0.95, new_similarity))
                new_semantic = max(0.1, min(1.0, new_semantic))
                
                # Create updated parameters
                updated_params = RetrievalParameters(
                    strategy=best_params.strategy,
                    similarity_threshold=new_similarity,
                    semantic_weight=new_semantic,
                    keyword_weight=max(0.0, min(0.9, 1.0 - new_semantic)),  # Adjust keyword weight
                    max_results=best_params.max_results,
                    hierarchical_levels=best_params.hierarchical_levels,
                    knowledge_graph_weight=best_params.knowledge_graph_weight,
                    reranking_enabled=best_params.reranking_enabled,
                    personalization_weight=best_params.personalization_weight,
                    context_window=best_params.context_window
                )
                
                # Evaluate new parameters
                new_score = await self._evaluate_parameter_performance(updated_params, performance_data)
                
                if new_score > current_score:
                    best_params = updated_params
                    current_score = new_score
                else:
                    learning_rate *= 0.9  # Reduce learning rate
            
            # Calculate improvement
            original_score = await self._evaluate_parameter_performance(current_parameters, performance_data)
            improvement = current_score - original_score
            
            return OptimizationResult(
                original_parameters=current_parameters,
                optimized_parameters=best_params,
                performance_improvement=improvement,
                confidence=0.6,  # Gradient descent has medium confidence
                optimization_type="gradient_descent",
                applied_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in gradient optimization: {e}")
            return None
    
    async def _bayesian_optimization(self, current_parameters: RetrievalParameters,
                                   performance_data: List[Dict[str, Any]],
                                   performance_target: Dict[str, float]) -> OptimizationResult:
        """Perform Bayesian optimization (simplified)."""
        try:
            # Simplified Bayesian optimization using random sampling with exploitation/exploration
            num_samples = 20
            best_score = await self._evaluate_parameter_performance(current_parameters, performance_data)
            best_params = current_parameters
            
            for i in range(num_samples):
                # Generate candidate parameters with some randomness
                exploration_factor = max(0.1, 1.0 - (i / num_samples))  # Decrease exploration over time
                
                candidate_params = self._generate_candidate_parameters(
                    current_parameters, exploration_factor
                )
                
                # Evaluate candidate
                score = await self._evaluate_parameter_performance(candidate_params, performance_data)
                
                if score > best_score:
                    best_score = score
                    best_params = candidate_params
            
            # Calculate improvement
            original_score = await self._evaluate_parameter_performance(current_parameters, performance_data)
            improvement = best_score - original_score
            
            return OptimizationResult(
                original_parameters=current_parameters,
                optimized_parameters=best_params,
                performance_improvement=improvement,
                confidence=0.7,  # Bayesian optimization has good confidence
                optimization_type="bayesian_optimization",
                applied_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in Bayesian optimization: {e}")
            return None
    
    def _generate_candidate_parameters(self, base_parameters: RetrievalParameters,
                                     exploration_factor: float) -> RetrievalParameters:
        """Generate candidate parameters for optimization."""
        import random
        
        # Add noise to parameters based on exploration factor
        noise_scale = exploration_factor * 0.2
        
        similarity_noise = random.gauss(0, noise_scale)
        semantic_noise = random.gauss(0, noise_scale)
        keyword_noise = random.gauss(0, noise_scale)
        
        # Apply bounds
        new_similarity = max(0.5, min(0.95, base_parameters.similarity_threshold + similarity_noise))
        new_semantic = max(0.1, min(1.0, base_parameters.semantic_weight + semantic_noise))
        new_keyword = max(0.0, min(0.9, base_parameters.keyword_weight + keyword_noise))
        
        # Normalize semantic and keyword weights
        total_weight = new_semantic + new_keyword
        if total_weight > 1.0:
            new_semantic /= total_weight
            new_keyword /= total_weight
        
        return RetrievalParameters(
            strategy=base_parameters.strategy,
            similarity_threshold=new_similarity,
            semantic_weight=new_semantic,
            keyword_weight=new_keyword,
            max_results=base_parameters.max_results,
            hierarchical_levels=base_parameters.hierarchical_levels,
            knowledge_graph_weight=base_parameters.knowledge_graph_weight,
            reranking_enabled=base_parameters.reranking_enabled,
            personalization_weight=base_parameters.personalization_weight,
            context_window=base_parameters.context_window
        )
    
    async def _evaluate_parameter_performance(self, parameters: RetrievalParameters,
                                            performance_data: List[Dict[str, Any]]) -> float:
        """Evaluate parameter performance based on historical data."""
        try:
            # Find similar parameter configurations in historical data
            similar_configs = []
            
            for data in performance_data:
                data_params = data.get('parameters', {})
                similarity = self._calculate_parameter_similarity(parameters.to_dict(), data_params)
                
                if similarity > 0.7:  # Threshold for similar configurations
                    metrics = data.get('metrics', {})
                    score = self._calculate_overall_score(metrics)
                    similar_configs.append((score, similarity))
            
            if not similar_configs:
                # No similar configurations, return baseline score
                return 0.5
            
            # Weighted average based on similarity
            total_weight = sum(similarity for _, similarity in similar_configs)
            weighted_score = sum(score * similarity for score, similarity in similar_configs) / total_weight
            
            return weighted_score
            
        except Exception as e:
            logger.error(f"Error evaluating parameter performance: {e}")
            return 0.0
    
    def _calculate_parameter_similarity(self, params1: Dict[str, Any], params2: Dict[str, Any]) -> float:
        """Calculate similarity between parameter configurations."""
        try:
            # Normalize parameters for comparison
            normalized_params = ['similarity_threshold', 'semantic_weight', 'keyword_weight']
            
            similarities = []
            for param in normalized_params:
                if param in params1 and param in params2:
                    val1 = params1[param]
                    val2 = params2[param]
                    
                    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                        # Calculate normalized difference
                        max_diff = self.parameter_bounds.get(param, (0, 1))[1] - self.parameter_bounds.get(param, (0, 1))[0]
                        diff = abs(val1 - val2) / max_diff if max_diff > 0 else 0
                        similarity = 1 - diff
                        similarities.append(similarity)
            
            return np.mean(similarities) if similarities else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating parameter similarity: {e}")
            return 0.0
    
    async def _calculate_parameter_gradient(self, parameters: RetrievalParameters,
                                          param_name: str, performance_data: List[Dict[str, Any]],
                                          step_size: float = 0.01) -> float:
        """Calculate gradient for a parameter."""
        try:
            # Get current performance
            current_score = await self._evaluate_parameter_performance(parameters, performance_data)
            
            # Create parameter variation
            varied_params = RetrievalParameters(**parameters.to_dict())
            current_value = getattr(varied_params, param_name)
            setattr(varied_params, param_name, current_value + step_size)
            
            # Apply bounds
            bounds = self.parameter_bounds.get(param_name, (0, 1))
            new_value = max(bounds[0], min(bounds[1], getattr(varied_params, param_name)))
            setattr(varied_params, param_name, new_value)
            
            # Get varied performance
            varied_score = await self._evaluate_parameter_performance(varied_params, performance_data)
            
            # Calculate gradient
            gradient = (varied_score - current_score) / step_size
            
            return gradient
            
        except Exception as e:
            logger.error(f"Error calculating parameter gradient: {e}")
            return 0.0
    
    def _calculate_aggregate_metrics(self, performance_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate aggregate metrics from performance data."""
        try:
            metrics = {
                'relevance_score': [],
                'response_time': [],
                'user_satisfaction': [],
                'f1_score': []
            }
            
            for data in performance_data:
                data_metrics = data.get('metrics', {})
                for metric in metrics:
                    if metric in data_metrics:
                        metrics[metric].append(data_metrics[metric])
            
            # Calculate aggregates
            aggregates = {}
            for metric, values in metrics.items():
                if values:
                    aggregates[f'avg_{metric}'] = np.mean(values)
                    aggregates[f'p95_{metric}'] = np.percentile(values, 95)
                    aggregates[f'std_{metric}'] = np.std(values)
            
            return aggregates
            
        except Exception as e:
            logger.error(f"Error calculating aggregate metrics: {e}")
            return {}
    
    def _calculate_performance_changes(self, before_metrics: Dict[str, float],
                                     after_metrics: Dict[str, float]) -> Dict[str, float]:
        """Calculate performance changes between before and after metrics."""
        changes = {}
        
        for metric in before_metrics:
            if metric in after_metrics:
                before_val = before_metrics[metric]
                after_val = after_metrics[metric]
                
                if before_val != 0:
                    change = (after_val - before_val) / before_val
                    changes[metric] = change
        
        return changes
    
    def _calculate_actual_improvement(self, before_metrics: Dict[str, float],
                                    after_metrics: Dict[str, float]) -> float:
        """Calculate actual improvement score."""
        try:
            # Calculate overall scores
            before_score = self._calculate_overall_score_from_aggregates(before_metrics)
            after_score = self._calculate_overall_score_from_aggregates(after_metrics)
            
            return after_score - before_score
            
        except Exception as e:
            logger.error(f"Error calculating actual improvement: {e}")
            return 0.0
    
    def _calculate_overall_score_from_aggregates(self, aggregates: Dict[str, float]) -> float:
        """Calculate overall score from aggregate metrics."""
        try:
            relevance = aggregates.get('avg_relevance_score', 0)
            response_time = aggregates.get('avg_response_time', 10)
            satisfaction = aggregates.get('avg_user_satisfaction', 0)
            f1 = aggregates.get('avg_f1_score', 0)
            
            # Normalize response time
            normalized_response_time = max(0, 1 - (response_time / 10.0))
            
            score = (
                0.3 * relevance +
                0.2 * normalized_response_time +
                0.3 * satisfaction +
                0.2 * f1
            )
            
            return min(max(score, 0), 1)
            
        except Exception as e:
            logger.error(f"Error calculating overall score from aggregates: {e}")
            return 0.0
    
    def _evaluate_optimization_success(self, optimization_result: OptimizationResult,
                                     before_metrics: Dict[str, float],
                                     after_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Evaluate if optimization was successful."""
        try:
            actual_improvement = self._calculate_actual_improvement(before_metrics, after_metrics)
            expected_improvement = optimization_result.performance_improvement
            
            success_threshold = 0.8  # 80% of expected improvement
            success = actual_improvement >= (expected_improvement * success_threshold)
            
            return {
                'success': success,
                'actual_improvement': actual_improvement,
                'expected_improvement': expected_improvement,
                'improvement_ratio': actual_improvement / expected_improvement if expected_improvement > 0 else 0,
                'success_threshold': success_threshold
            }
            
        except Exception as e:
            logger.error(f"Error evaluating optimization success: {e}")
            return {'success': False}
    
    async def _generate_bottleneck_recommendation(self, bottleneck: Dict[str, Any],
                                                current_parameters: RetrievalParameters) -> Dict[str, Any]:
        """Generate recommendation based on bottleneck."""
        try:
            bottleneck_type = bottleneck['type']
            
            if bottleneck_type == 'response_time':
                return {
                    'type': 'parameter_adjustment',
                    'parameter': 'max_results',
                    'current_value': current_parameters.max_results,
                    'recommended_value': max(5, current_parameters.max_results - 5),
                    'reason': 'Reduce max_results to improve response time',
                    'expected_impact': 0.2,
                    'confidence': 0.8
                }
            
            elif bottleneck_type == 'relevance':
                return {
                    'type': 'parameter_adjustment',
                    'parameter': 'similarity_threshold',
                    'current_value': current_parameters.similarity_threshold,
                    'recommended_value': max(0.5, current_parameters.similarity_threshold - 0.1),
                    'reason': 'Lower similarity threshold to improve relevance coverage',
                    'expected_impact': 0.15,
                    'confidence': 0.7
                }
            
            elif bottleneck_type == 'user_satisfaction':
                return {
                    'type': 'parameter_adjustment',
                    'parameter': 'personalization_weight',
                    'current_value': current_parameters.personalization_weight,
                    'recommended_value': min(0.3, current_parameters.personalization_weight + 0.05),
                    'reason': 'Increase personalization to improve user satisfaction',
                    'expected_impact': 0.1,
                    'confidence': 0.6
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating bottleneck recommendation: {e}")
            return None
    
    async def _generate_opportunity_recommendation(self, opportunity: Dict[str, Any],
                                                 current_parameters: RetrievalParameters) -> Dict[str, Any]:
        """Generate recommendation based on opportunity."""
        try:
            opportunity_type = opportunity['type']
            
            if opportunity_type == 'parameter_optimization':
                parameter = opportunity['parameter']
                expected_impact = opportunity.get('expected_impact', 0.1)
                
                return {
                    'type': 'parameter_optimization',
                    'parameter': parameter,
                    'reason': opportunity['description'],
                    'expected_impact': expected_impact,
                    'confidence': 0.7,
                    'optimization_method': 'grid_search'
                }
            
            elif opportunity_type == 'strategy_optimization':
                best_strategy = opportunity['best_strategy']
                expected_impact = opportunity.get('expected_impact', 0.2)
                
                return {
                    'type': 'strategy_change',
                    'current_strategy': current_parameters.strategy.value,
                    'recommended_strategy': best_strategy,
                    'reason': opportunity['description'],
                    'expected_impact': expected_impact,
                    'confidence': 0.8
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating opportunity recommendation: {e}")
            return None
    
    async def _log_optimization_application(self, optimization_result: OptimizationResult):
        """Log optimization application."""
        try:
            from core.database import AnalyticsEvent
            
            db_session = next(get_db())
            try:
                event_data = {
                    'optimization_type': optimization_result.optimization_type,
                    'strategy': optimization_result.optimized_parameters.strategy.value,
                    'performance_improvement': optimization_result.performance_improvement,
                    'confidence': optimization_result.confidence,
                    'original_parameters': optimization_result.original_parameters.to_dict(),
                    'optimized_parameters': optimization_result.optimized_parameters.to_dict()
                }
                
                analytics_event = AnalyticsEvent(
                    event_type="retrieval_optimization_applied",
                    event_data=event_data,
                    timestamp=optimization_result.applied_at
                )
                
                db_session.add(analytics_event)
                db_session.commit()
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error logging optimization application: {e}")
    
    async def _store_optimization_history(self, optimization_result: OptimizationResult):
        """Store optimization history."""
        try:
            history_key = f"optimization_history:{optimization_result.optimized_parameters.strategy.value}"
            history_data = {
                'optimization_id': f"{optimization_result.optimization_type}_{optimization_result.applied_at.strftime('%Y%m%d_%H%M%S')}",
                'optimization_type': optimization_result.optimization_type,
                'performance_improvement': optimization_result.performance_improvement,
                'confidence': optimization_result.confidence,
                'applied_at': optimization_result.applied_at.isoformat(),
                'parameters': optimization_result.optimized_parameters.to_dict()
            }
            
            # Store in Redis list (keep last 50 optimizations)
            await self.redis_client.lpush(history_key, json.dumps(history_data, default=str))
            await self.redis_client.ltrim(history_key, 0, 49)
            
        except Exception as e:
            logger.error(f"Error storing optimization history: {e}")
    
    async def _store_monitoring_results(self, impact_analysis: Dict[str, Any]):
        """Store monitoring results."""
        try:
            monitoring_key = f"optimization_monitoring:{impact_analysis['optimization_id']}"
            await self.redis_client.setex(
                monitoring_key,
                86400 * 7,  # Keep for 7 days
                json.dumps(impact_analysis, default=str)
            )
            
        except Exception as e:
            logger.error(f"Error storing monitoring results: {e}")

# Global instance
retrieval_optimizer = RetrievalOptimizer()