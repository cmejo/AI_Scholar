"""
Performance testing and load testing utilities for system benchmarking.
"""
import asyncio
import time
import statistics
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import json
import random
import string

from core.config import settings
from services.monitoring_service import get_performance_monitor, get_performance_benchmark
from services.caching_service import get_caching_service
from core.database_optimization import db_optimizer

logger = logging.getLogger(__name__)

@dataclass
class LoadTestConfig:
    """Configuration for load testing."""
    concurrent_users: int = 10
    test_duration_seconds: int = 60
    ramp_up_seconds: int = 10
    endpoint_weights: Dict[str, float] = None
    think_time_seconds: float = 1.0
    
    def __post_init__(self):
        if self.endpoint_weights is None:
            self.endpoint_weights = {
                '/api/chat/enhanced': 0.4,
                '/api/search/semantic': 0.3,
                '/api/documents/upload': 0.1,
                '/api/analytics/dashboard': 0.1,
                '/api/knowledge-graph': 0.1
            }

@dataclass
class LoadTestResult:
    """Results from load testing."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    errors: List[Dict[str, Any]]
    endpoint_stats: Dict[str, Dict[str, Any]]

class PerformanceTester:
    """Performance testing and benchmarking utilities."""
    
    def __init__(self):
        self.base_url = f"http://localhost:8000"
        self.test_results = []
        self.performance_monitor = get_performance_monitor()
        self.performance_benchmark = get_performance_benchmark()
        self.caching_service = get_caching_service()
    
    async def run_load_test(self, config: LoadTestConfig) -> LoadTestResult:
        """Run a comprehensive load test."""
        logger.info(f"Starting load test with {config.concurrent_users} users for {config.test_duration_seconds}s")
        
        # Start monitoring
        await self.performance_monitor.start_monitoring(interval_seconds=5)
        
        # Prepare test data
        test_data = await self._prepare_test_data()
        
        # Run the load test
        start_time = time.time()
        results = []
        errors = []
        
        # Create semaphore to control concurrent users
        semaphore = asyncio.Semaphore(config.concurrent_users)
        
        # Generate tasks for the test duration
        tasks = []
        end_time = start_time + config.test_duration_seconds
        
        async def user_session():
            """Simulate a user session."""
            async with semaphore:
                session_results = []
                session_errors = []
                
                async with aiohttp.ClientSession() as session:
                    while time.time() < end_time:
                        # Select endpoint based on weights
                        endpoint = self._select_weighted_endpoint(config.endpoint_weights)
                        
                        # Execute request
                        result = await self._execute_request(session, endpoint, test_data)
                        
                        if result['success']:
                            session_results.append(result)
                        else:
                            session_errors.append(result)
                        
                        # Think time
                        await asyncio.sleep(config.think_time_seconds)
                
                return session_results, session_errors
        
        # Create user sessions with ramp-up
        for i in range(config.concurrent_users):
            # Stagger user start times for ramp-up
            delay = (config.ramp_up_seconds / config.concurrent_users) * i
            task = asyncio.create_task(self._delayed_user_session(user_session, delay))
            tasks.append(task)
        
        # Wait for all tasks to complete
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for session_result in all_results:
            if isinstance(session_result, Exception):
                logger.error(f"User session failed: {session_result}")
                continue
            
            session_results, session_errors = session_result
            results.extend(session_results)
            errors.extend(session_errors)
        
        # Stop monitoring
        await self.performance_monitor.stop_monitoring()
        
        # Calculate statistics
        test_result = self._calculate_load_test_stats(results, errors, time.time() - start_time)
        
        # Record benchmark data
        self.performance_benchmark.record_performance(
            'load_test_avg_response_time',
            test_result.average_response_time
        )
        self.performance_benchmark.record_performance(
            'load_test_requests_per_second',
            test_result.requests_per_second
        )
        
        logger.info(f"Load test completed: {test_result.requests_per_second:.2f} RPS, "
                   f"{test_result.error_rate:.2%} error rate")
        
        return test_result
    
    async def _delayed_user_session(self, user_session_func: Callable, delay: float):
        """Execute user session with delay for ramp-up."""
        await asyncio.sleep(delay)
        return await user_session_func()
    
    def _select_weighted_endpoint(self, weights: Dict[str, float]) -> str:
        """Select endpoint based on weights."""
        endpoints = list(weights.keys())
        weights_list = list(weights.values())
        return random.choices(endpoints, weights=weights_list)[0]
    
    async def _prepare_test_data(self) -> Dict[str, Any]:
        """Prepare test data for load testing."""
        return {
            'test_queries': [
                "What is machine learning?",
                "Explain neural networks",
                "How does deep learning work?",
                "What are the applications of AI?",
                "Describe natural language processing"
            ],
            'test_user_id': 'test_user_' + ''.join(random.choices(string.ascii_lowercase, k=8)),
            'test_conversation_id': 'test_conv_' + ''.join(random.choices(string.ascii_lowercase, k=8))
        }
    
    async def _execute_request(self, session: aiohttp.ClientSession, endpoint: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single request and measure performance."""
        start_time = time.time()
        
        try:
            # Prepare request based on endpoint
            if endpoint == '/api/chat/enhanced':
                payload = {
                    'message': random.choice(test_data['test_queries']),
                    'conversation_id': test_data['test_conversation_id'],
                    'use_chain_of_thought': random.choice([True, False]),
                    'enable_reasoning': random.choice([True, False]),
                    'enable_memory': random.choice([True, False]),
                    'personalization_level': random.randint(0, 3)
                }
                response = await session.post(f"{self.base_url}{endpoint}", json=payload)
            
            elif endpoint == '/api/search/semantic':
                params = {
                    'query': random.choice(test_data['test_queries']),
                    'limit': random.randint(5, 20),
                    'enable_personalization': random.choice([True, False])
                }
                response = await session.get(f"{self.base_url}{endpoint}", params=params)
            
            elif endpoint == '/api/analytics/dashboard':
                params = {
                    'time_range': random.choice(['1d', '7d', '30d']),
                    'include_insights': random.choice([True, False])
                }
                response = await session.get(f"{self.base_url}{endpoint}", params=params)
            
            elif endpoint == '/api/knowledge-graph':
                # This would need a valid document_id in real testing
                document_id = 'test_doc_id'
                params = {
                    'include_relationships': True,
                    'max_depth': random.randint(1, 3),
                    'min_confidence': random.uniform(0.3, 0.8)
                }
                response = await session.get(f"{self.base_url}{endpoint}/{document_id}", params=params)
            
            else:
                # Default GET request
                response = await session.get(f"{self.base_url}{endpoint}")
            
            response_time = time.time() - start_time
            
            return {
                'endpoint': endpoint,
                'response_time': response_time,
                'status_code': response.status,
                'success': 200 <= response.status < 400,
                'timestamp': datetime.now().isoformat(),
                'response_size': len(await response.text()) if response.status == 200 else 0
            }
        
        except Exception as e:
            response_time = time.time() - start_time
            return {
                'endpoint': endpoint,
                'response_time': response_time,
                'status_code': 0,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'response_size': 0
            }
    
    def _calculate_load_test_stats(self, results: List[Dict[str, Any]], errors: List[Dict[str, Any]], 
                                 total_duration: float) -> LoadTestResult:
        """Calculate load test statistics."""
        total_requests = len(results) + len(errors)
        successful_requests = len(results)
        failed_requests = len(errors)
        
        if not results:
            return LoadTestResult(
                total_requests=total_requests,
                successful_requests=0,
                failed_requests=failed_requests,
                average_response_time=0,
                median_response_time=0,
                p95_response_time=0,
                p99_response_time=0,
                requests_per_second=0,
                error_rate=1.0,
                errors=errors,
                endpoint_stats={}
            )
        
        response_times = [r['response_time'] for r in results]
        
        # Calculate percentiles
        response_times_sorted = sorted(response_times)
        p95_index = int(0.95 * len(response_times_sorted))
        p99_index = int(0.99 * len(response_times_sorted))
        
        # Calculate endpoint-specific stats
        endpoint_stats = {}
        endpoints = set(r['endpoint'] for r in results)
        
        for endpoint in endpoints:
            endpoint_results = [r for r in results if r['endpoint'] == endpoint]
            endpoint_times = [r['response_time'] for r in endpoint_results]
            
            endpoint_stats[endpoint] = {
                'request_count': len(endpoint_results),
                'average_response_time': statistics.mean(endpoint_times),
                'median_response_time': statistics.median(endpoint_times),
                'success_rate': len(endpoint_results) / len([r for r in results + errors if r['endpoint'] == endpoint])
            }
        
        return LoadTestResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=statistics.mean(response_times),
            median_response_time=statistics.median(response_times),
            p95_response_time=response_times_sorted[p95_index] if p95_index < len(response_times_sorted) else max(response_times),
            p99_response_time=response_times_sorted[p99_index] if p99_index < len(response_times_sorted) else max(response_times),
            requests_per_second=total_requests / total_duration,
            error_rate=failed_requests / total_requests if total_requests > 0 else 0,
            errors=errors,
            endpoint_stats=endpoint_stats
        )
    
    async def run_database_performance_test(self) -> Dict[str, Any]:
        """Run database-specific performance tests."""
        logger.info("Starting database performance test")
        
        test_queries = [
            # User queries
            ("SELECT * FROM users WHERE email = 'test@example.com'", "user_lookup"),
            ("SELECT COUNT(*) FROM users WHERE created_at > datetime('now', '-7 days')", "recent_users"),
            
            # Document queries
            ("SELECT * FROM documents WHERE user_id = 'test_user' ORDER BY created_at DESC LIMIT 10", "user_documents"),
            ("SELECT COUNT(*) FROM documents WHERE status = 'completed'", "completed_documents"),
            
            # Conversation queries
            ("SELECT * FROM conversations WHERE user_id = 'test_user' ORDER BY updated_at DESC LIMIT 20", "user_conversations"),
            ("SELECT COUNT(*) FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE user_id = 'test_user')", "user_messages"),
            
            # Knowledge graph queries
            ("SELECT * FROM kg_entities WHERE document_id = 'test_doc' ORDER BY importance_score DESC LIMIT 50", "document_entities"),
            ("SELECT * FROM kg_relationships WHERE source_entity_id IN (SELECT id FROM kg_entities WHERE document_id = 'test_doc')", "entity_relationships"),
            
            # Analytics queries
            ("SELECT event_type, COUNT(*) FROM analytics_events WHERE user_id = 'test_user' AND timestamp > datetime('now', '-24 hours') GROUP BY event_type", "user_analytics"),
            ("SELECT DATE(timestamp) as date, COUNT(*) FROM analytics_events WHERE timestamp > datetime('now', '-30 days') GROUP BY DATE(timestamp)", "daily_analytics"),
        ]
        
        results = {}
        
        for query, test_name in test_queries:
            # Run query multiple times to get average performance
            times = []
            for _ in range(5):
                performance_data = await db_optimizer.analyze_query_performance(query)
                times.append(performance_data['execution_time'])
            
            results[test_name] = {
                'average_time': statistics.mean(times),
                'median_time': statistics.median(times),
                'max_time': max(times),
                'min_time': min(times),
                'query': query
            }
            
            # Record benchmark
            self.performance_benchmark.record_performance(
                f'db_query_{test_name}',
                statistics.mean(times)
            )
        
        logger.info("Database performance test completed")
        return results
    
    async def run_cache_performance_test(self) -> Dict[str, Any]:
        """Run cache performance tests."""
        logger.info("Starting cache performance test")
        
        # Test cache operations
        test_operations = [
            ('set_operation', self._test_cache_set),
            ('get_operation', self._test_cache_get),
            ('delete_operation', self._test_cache_delete),
            ('bulk_operations', self._test_cache_bulk)
        ]
        
        results = {}
        
        for operation_name, test_func in test_operations:
            times = []
            for _ in range(10):
                start_time = time.time()
                await test_func()
                execution_time = time.time() - start_time
                times.append(execution_time)
            
            results[operation_name] = {
                'average_time': statistics.mean(times),
                'median_time': statistics.median(times),
                'max_time': max(times),
                'min_time': min(times)
            }
            
            # Record benchmark
            self.performance_benchmark.record_performance(
                f'cache_{operation_name}',
                statistics.mean(times)
            )
        
        # Get cache statistics
        cache_stats = self.caching_service.get_cache_stats()
        results['cache_stats'] = cache_stats
        
        logger.info("Cache performance test completed")
        return results
    
    async def _test_cache_set(self):
        """Test cache set operations."""
        test_data = {'test': 'data', 'timestamp': time.time()}
        await self.caching_service.cache.set('test_key', test_data, ttl=300)
    
    async def _test_cache_get(self):
        """Test cache get operations."""
        await self.caching_service.cache.get('test_key')
    
    async def _test_cache_delete(self):
        """Test cache delete operations."""
        await self.caching_service.cache.delete('test_key')
    
    async def _test_cache_bulk(self):
        """Test bulk cache operations."""
        # Set multiple keys
        for i in range(10):
            await self.caching_service.cache.set(f'bulk_test_{i}', {'data': i}, ttl=300)
        
        # Get multiple keys
        for i in range(10):
            await self.caching_service.cache.get(f'bulk_test_{i}')
        
        # Delete multiple keys
        for i in range(10):
            await self.caching_service.cache.delete(f'bulk_test_{i}')
    
    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive performance benchmark."""
        logger.info("Starting comprehensive performance benchmark")
        
        benchmark_results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': await self._get_system_info(),
            'database_performance': await self.run_database_performance_test(),
            'cache_performance': await self.run_cache_performance_test(),
            'sla_compliance': self.performance_benchmark.get_all_sla_compliance(),
            'system_health': await self.performance_monitor.get_system_health()
        }
        
        # Run a light load test
        light_load_config = LoadTestConfig(
            concurrent_users=5,
            test_duration_seconds=30,
            ramp_up_seconds=5
        )
        
        try:
            load_test_result = await self.run_load_test(light_load_config)
            benchmark_results['load_test'] = asdict(load_test_result)
        except Exception as e:
            logger.error(f"Load test failed during benchmark: {e}")
            benchmark_results['load_test'] = {'error': str(e)}
        
        logger.info("Comprehensive performance benchmark completed")
        return benchmark_results
    
    async def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for benchmarking context."""
        import psutil
        import platform
        
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'disk_total': psutil.disk_usage('/').total,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_performance_report(self, benchmark_results: Dict[str, Any]) -> str:
        """Generate a human-readable performance report."""
        report = []
        report.append("=" * 60)
        report.append("PERFORMANCE BENCHMARK REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {benchmark_results['timestamp']}")
        report.append("")
        
        # System Information
        system_info = benchmark_results.get('system_info', {})
        report.append("SYSTEM INFORMATION:")
        report.append(f"  Platform: {system_info.get('platform', 'Unknown')}")
        report.append(f"  Python: {system_info.get('python_version', 'Unknown')}")
        report.append(f"  CPU Cores: {system_info.get('cpu_count', 'Unknown')}")
        report.append(f"  Memory: {system_info.get('memory_total', 0) / (1024**3):.1f} GB")
        report.append("")
        
        # Database Performance
        db_perf = benchmark_results.get('database_performance', {})
        report.append("DATABASE PERFORMANCE:")
        for test_name, results in db_perf.items():
            avg_time = results.get('average_time', 0)
            report.append(f"  {test_name}: {avg_time*1000:.2f}ms avg")
        report.append("")
        
        # Cache Performance
        cache_perf = benchmark_results.get('cache_performance', {})
        report.append("CACHE PERFORMANCE:")
        for operation, results in cache_perf.items():
            if operation != 'cache_stats':
                avg_time = results.get('average_time', 0)
                report.append(f"  {operation}: {avg_time*1000:.2f}ms avg")
        
        cache_stats = cache_perf.get('cache_stats', {})
        if cache_stats:
            hit_rate = cache_stats.get('overall_cache_hit_rate', 0)
            report.append(f"  Cache Hit Rate: {hit_rate:.2%}")
        report.append("")
        
        # Load Test Results
        load_test = benchmark_results.get('load_test', {})
        if 'error' not in load_test:
            report.append("LOAD TEST RESULTS:")
            report.append(f"  Requests/Second: {load_test.get('requests_per_second', 0):.2f}")
            report.append(f"  Average Response Time: {load_test.get('average_response_time', 0)*1000:.2f}ms")
            report.append(f"  95th Percentile: {load_test.get('p95_response_time', 0)*1000:.2f}ms")
            report.append(f"  Error Rate: {load_test.get('error_rate', 0):.2%}")
            report.append("")
        
        # SLA Compliance
        sla_compliance = benchmark_results.get('sla_compliance', {})
        report.append("SLA COMPLIANCE:")
        for benchmark_name, compliance in sla_compliance.items():
            if 'error' not in compliance:
                meets_sla = compliance.get('meets_sla', False)
                compliance_rate = compliance.get('compliance_rate', 0)
                status = "✓" if meets_sla else "✗"
                report.append(f"  {benchmark_name}: {status} {compliance_rate:.2%}")
        report.append("")
        
        # System Health
        system_health = benchmark_results.get('system_health', {})
        health_status = system_health.get('status', 'unknown')
        health_score = system_health.get('health_score', 0)
        report.append("SYSTEM HEALTH:")
        report.append(f"  Status: {health_status.upper()}")
        report.append(f"  Health Score: {health_score:.1f}/100")
        report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)

# Global performance tester instance
performance_tester = PerformanceTester()

def get_performance_tester() -> PerformanceTester:
    """Get the global performance tester instance."""
    return performance_tester