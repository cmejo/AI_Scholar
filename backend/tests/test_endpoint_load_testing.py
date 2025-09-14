"""
Comprehensive load testing suite for all restored endpoints
Tests endpoint performance under various load conditions and stress scenarios
"""
import pytest
import asyncio
import time
import statistics
import threading
import psutil
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from api.advanced_endpoints import router
from core.service_manager import ServiceManager, ServiceStatus, ServiceHealth


@pytest.fixture
def test_client():
    """Create test client for advanced endpoints"""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def mock_service_manager():
    """Mock service manager for testing"""
    with patch('api.advanced_endpoints.service_manager') as mock_sm:
        yield mock_sm


@pytest.mark.performance
class TestEndpointLoadTesting:
    """Comprehensive load testing for all endpoints"""
    
    def test_health_endpoints_load_testing(self, test_client, mock_service_manager):
        """Load test all health endpoints"""
        # Mock service manager for consistent responses
        mock_service_manager.get_service_health.return_value = {
            "database": {"status": "healthy", "last_check": datetime.utcnow().isoformat()}
        }
        mock_service_manager.get_initialization_summary.return_value = {
            "total_services": 1, "healthy_services": 1, "failed_services": 0
        }
        mock_service_manager.get_health_monitoring_status.return_value = {
            "enabled": True, "interval": 300
        }
        
        mock_health = ServiceHealth(
            name="database",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow(),
            initialization_time=1.0
        )
        mock_service_manager.check_service_health.return_value = mock_health
        mock_service_manager.check_all_services_health.return_value = {"database": mock_health}
        
        # Health endpoints to load test
        health_endpoints = [
            "/api/advanced/health",
            "/api/advanced/health/detailed",
            "/api/advanced/health/services",
            "/api/advanced/health/service/database",
            "/api/advanced/health/monitoring",
        ]
        
        def make_health_request(endpoint):
            start_time = time.time()
            try:
                response = test_client.get(endpoint)
                end_time = time.time()
                return {
                    "endpoint": endpoint,
                    "success": response.status_code == 200,
                    "response_time": end_time - start_time,
                    "status_code": response.status_code
                }
            except Exception as e:
                return {
                    "endpoint": endpoint,
                    "success": False,
                    "error": str(e),
                    "response_time": time.time() - start_time
                }
        
        # Load test parameters
        concurrent_users = 25
        requests_per_endpoint = 20
        
        all_requests = []
        for endpoint in health_endpoints:
            for _ in range(requests_per_endpoint):
                all_requests.append(endpoint)
        
        # Execute load test
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_health_request, endpoint) for endpoint in all_requests]
            results = [future.result() for future in as_completed(futures)]
        end_time = time.time()
        
        # Analyze results
        total_requests = len(results)
        successful_requests = [r for r in results if r["success"]]
        success_rate = len(successful_requests) / total_requests
        
        # Performance metrics
        response_times = [r["response_time"] for r in successful_requests]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = sorted(response_times)[int(0.95 * len(response_times))] if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        total_duration = end_time - start_time
        throughput = total_requests / total_duration
        
        # Assertions
        assert success_rate >= 0.98, f"Health endpoints success rate: {success_rate:.1%}"
        assert avg_response_time < 0.5, f"Average response time: {avg_response_time:.3f}s"
        assert p95_response_time < 1.0, f"P95 response time: {p95_response_time:.3f}s"
        assert throughput > 50, f"Throughput: {throughput:.1f} req/s"
        
        print(f"Health endpoints load test results:")
        print(f"  Total requests: {total_requests}")
        print(f"  Success rate: {success_rate:.1%}")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  P95 response time: {p95_response_time:.3f}s")
        print(f"  Max response time: {max_response_time:.3f}s")
        print(f"  Throughput: {throughput:.1f} req/s")
    
    def test_research_endpoints_load_testing(self, test_client, mock_service_manager):
        """Load test research endpoints"""
        # Mock research services
        mock_service = MagicMock()
        mock_service.advanced_search = AsyncMock(return_value=[
            {"id": f"result-{i}", "title": f"Result {i}", "relevance_score": 0.9 - (i * 0.1)}
            for i in range(5)
        ])
        
        mock_health = ServiceHealth(
            name="semantic_search",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow()
        )
        
        mock_service_manager.get_service.return_value = mock_service
        mock_service_manager.is_service_healthy.return_value = True
        mock_service_manager.check_service_health.return_value = mock_health
        
        def make_research_request(request_data):
            endpoint, method, data = request_data
            start_time = time.time()
            try:
                if method == "GET":
                    response = test_client.get(endpoint)
                else:
                    response = test_client.post(endpoint, json=data)
                
                end_time = time.time()
                return {
                    "endpoint": endpoint,
                    "success": response.status_code == 200,
                    "response_time": end_time - start_time,
                    "method": method
                }
            except Exception as e:
                return {
                    "endpoint": endpoint,
                    "success": False,
                    "error": str(e),
                    "response_time": time.time() - start_time,
                    "method": method
                }
        
        # Research endpoints to load test
        research_requests = [
            ("/api/advanced/research/status", "GET", None),
            ("/api/advanced/research/capabilities", "GET", None),
            ("/api/advanced/research/domains", "GET", None),
            ("/api/advanced/research/search/basic", "POST", {"query": "load test query", "max_results": 5}),
            ("/api/advanced/research/validate", "POST", {"query": "Is this a valid research query?"}),
        ]
        
        # Create load test requests
        all_requests = []
        requests_per_endpoint = 15
        for request_data in research_requests:
            for i in range(requests_per_endpoint):
                # Vary query data for POST requests
                if request_data[1] == "POST" and request_data[2]:
                    modified_data = request_data[2].copy()
                    if "query" in modified_data:
                        modified_data["query"] = f"{modified_data['query']} {i}"
                    all_requests.append((request_data[0], request_data[1], modified_data))
                else:
                    all_requests.append(request_data)
        
        # Execute load test
        concurrent_users = 20
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_research_request, req) for req in all_requests]
            results = [future.result() for future in as_completed(futures)]
        end_time = time.time()
        
        # Analyze results
        total_requests = len(results)
        successful_requests = [r for r in results if r["success"]]
        success_rate = len(successful_requests) / total_requests
        
        # Performance metrics by endpoint type
        get_requests = [r for r in successful_requests if r["method"] == "GET"]
        post_requests = [r for r in successful_requests if r["method"] == "POST"]
        
        get_response_times = [r["response_time"] for r in get_requests]
        post_response_times = [r["response_time"] for r in post_requests]
        
        get_avg_time = statistics.mean(get_response_times) if get_response_times else 0
        post_avg_time = statistics.mean(post_response_times) if post_response_times else 0
        
        total_duration = end_time - start_time
        throughput = total_requests / total_duration
        
        # Assertions
        assert success_rate >= 0.95, f"Research endpoints success rate: {success_rate:.1%}"
        assert get_avg_time < 0.3, f"GET average response time: {get_avg_time:.3f}s"
        assert post_avg_time < 1.0, f"POST average response time: {post_avg_time:.3f}s"
        assert throughput > 20, f"Throughput: {throughput:.1f} req/s"
        
        print(f"Research endpoints load test results:")
        print(f"  Total requests: {total_requests}")
        print(f"  Success rate: {success_rate:.1%}")
        print(f"  GET avg response time: {get_avg_time:.3f}s")
        print(f"  POST avg response time: {post_avg_time:.3f}s")
        print(f"  Throughput: {throughput:.1f} req/s")
    
    def test_analytics_endpoints_load_testing(self, test_client, mock_service_manager):
        """Load test analytics endpoints"""
        # Mock analytics service
        mock_service = MagicMock()
        
        # Mock report object
        mock_report = MagicMock()
        mock_report.id = "load-test-report"
        mock_report.title = "Load Test Report"
        mock_report.summary = "Load test summary"
        mock_report.metrics = []
        mock_report.visualizations = []
        mock_report.recommendations = []
        mock_report.timeframe.value = "month"
        mock_report.generated_at = datetime.utcnow()
        mock_report.confidence_score = 0.85
        
        mock_service.generate_comprehensive_report = AsyncMock(return_value=mock_report)
        mock_service.generate_usage_insights = AsyncMock(return_value={"daily_usage": 4.2})
        mock_service.analyze_content_performance = AsyncMock(return_value={"total_content": 100})
        
        mock_health = ServiceHealth(
            name="advanced_analytics",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow()
        )
        
        mock_service_manager.get_service.return_value = mock_service
        mock_service_manager.check_service_health.return_value = mock_health
        
        def make_analytics_request(endpoint):
            start_time = time.time()
            try:
                response = test_client.get(endpoint)
                end_time = time.time()
                return {
                    "endpoint": endpoint,
                    "success": response.status_code == 200,
                    "response_time": end_time - start_time
                }
            except Exception as e:
                return {
                    "endpoint": endpoint,
                    "success": False,
                    "error": str(e),
                    "response_time": time.time() - start_time
                }
        
        # Analytics endpoints to load test
        analytics_endpoints = [
            "/api/advanced/analytics/report/user1",
            "/api/advanced/analytics/usage/user1",
            "/api/advanced/analytics/content/user1",
        ]
        
        # Create load test requests with different user IDs
        all_requests = []
        requests_per_endpoint = 10
        for endpoint_template in analytics_endpoints:
            for i in range(requests_per_endpoint):
                user_id = f"user{i % 5 + 1}"  # Rotate through 5 users
                endpoint = endpoint_template.replace("user1", user_id)
                all_requests.append(endpoint)
        
        # Execute load test
        concurrent_users = 15
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_analytics_request, endpoint) for endpoint in all_requests]
            results = [future.result() for future in as_completed(futures)]
        end_time = time.time()
        
        # Analyze results
        total_requests = len(results)
        successful_requests = [r for r in results if r["success"]]
        success_rate = len(successful_requests) / total_requests
        
        response_times = [r["response_time"] for r in successful_requests]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = sorted(response_times)[int(0.95 * len(response_times))] if response_times else 0
        
        total_duration = end_time - start_time
        throughput = total_requests / total_duration
        
        # Assertions (Analytics endpoints may be slower)
        assert success_rate >= 0.90, f"Analytics endpoints success rate: {success_rate:.1%}"
        assert avg_response_time < 2.0, f"Average response time: {avg_response_time:.3f}s"
        assert p95_response_time < 5.0, f"P95 response time: {p95_response_time:.3f}s"
        assert throughput > 5, f"Throughput: {throughput:.1f} req/s"
        
        print(f"Analytics endpoints load test results:")
        print(f"  Total requests: {total_requests}")
        print(f"  Success rate: {success_rate:.1%}")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  P95 response time: {p95_response_time:.3f}s")
        print(f"  Throughput: {throughput:.1f} req/s")


@pytest.mark.performance
class TestEndpointStressTesting:
    """Stress testing for endpoints under extreme conditions"""
    
    def test_high_concurrency_stress_test(self, test_client, mock_service_manager):
        """Test endpoints under high concurrency stress"""
        # Mock lightweight service responses
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        def make_stress_request(request_id):
            start_time = time.time()
            try:
                # Alternate between different endpoints
                endpoints = [
                    "/api/advanced/health",
                    "/api/advanced/research/domains",
                ]
                
                endpoint = endpoints[request_id % len(endpoints)]
                response = test_client.get(endpoint)
                
                end_time = time.time()
                return {
                    "request_id": request_id,
                    "endpoint": endpoint,
                    "success": response.status_code == 200,
                    "response_time": end_time - start_time
                }
            except Exception as e:
                return {
                    "request_id": request_id,
                    "success": False,
                    "error": str(e),
                    "response_time": time.time() - start_time
                }
        
        # Stress test parameters
        total_requests = 200
        max_concurrent_users = 50
        
        # Execute stress test
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=max_concurrent_users) as executor:
            futures = [executor.submit(make_stress_request, i) for i in range(total_requests)]
            results = [future.result() for future in as_completed(futures)]
        end_time = time.time()
        
        # Analyze results
        successful_requests = [r for r in results if r["success"]]
        success_rate = len(successful_requests) / total_requests
        
        response_times = [r["response_time"] for r in successful_requests]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        total_duration = end_time - start_time
        throughput = total_requests / total_duration
        
        # Stress test assertions (more lenient)
        assert success_rate >= 0.85, f"Stress test success rate: {success_rate:.1%}"
        assert avg_response_time < 3.0, f"Average response time under stress: {avg_response_time:.3f}s"
        assert max_response_time < 10.0, f"Max response time under stress: {max_response_time:.3f}s"
        
        print(f"High concurrency stress test results:")
        print(f"  Total requests: {total_requests}")
        print(f"  Concurrent users: {max_concurrent_users}")
        print(f"  Success rate: {success_rate:.1%}")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Max response time: {max_response_time:.3f}s")
        print(f"  Throughput: {throughput:.1f} req/s")
    
    def test_sustained_load_stress_test(self, test_client, mock_service_manager):
        """Test endpoints under sustained load over time"""
        # Mock service responses
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        def make_sustained_request(batch_info):
            batch_id, request_id = batch_info
            start_time = time.time()
            try:
                response = test_client.post(
                    "/api/advanced/research/search/basic",
                    json={"query": f"sustained test batch {batch_id} request {request_id}"}
                )
                end_time = time.time()
                return {
                    "batch_id": batch_id,
                    "request_id": request_id,
                    "success": response.status_code == 200,
                    "response_time": end_time - start_time
                }
            except Exception as e:
                return {
                    "batch_id": batch_id,
                    "request_id": request_id,
                    "success": False,
                    "error": str(e),
                    "response_time": time.time() - start_time
                }
        
        # Sustained load parameters
        num_batches = 10
        requests_per_batch = 20
        concurrent_users = 15
        batch_interval = 0.5  # seconds between batches
        
        all_results = []
        batch_metrics = []
        
        for batch in range(num_batches):
            batch_start_time = time.time()
            
            # Create batch requests
            batch_requests = [(batch, i) for i in range(requests_per_batch)]
            
            # Execute batch
            with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = [executor.submit(make_sustained_request, req) for req in batch_requests]
                batch_results = [future.result() for future in as_completed(futures)]
            
            batch_end_time = time.time()
            
            # Analyze batch
            batch_successful = [r for r in batch_results if r["success"]]
            batch_success_rate = len(batch_successful) / len(batch_results)
            batch_avg_time = statistics.mean([r["response_time"] for r in batch_successful]) if batch_successful else 0
            batch_duration = batch_end_time - batch_start_time
            
            batch_metrics.append({
                "batch_id": batch,
                "success_rate": batch_success_rate,
                "avg_response_time": batch_avg_time,
                "duration": batch_duration
            })
            
            all_results.extend(batch_results)
            
            # Wait before next batch
            if batch < num_batches - 1:
                time.sleep(batch_interval)
        
        # Overall analysis
        total_requests = len(all_results)
        overall_successful = [r for r in all_results if r["success"]]
        overall_success_rate = len(overall_successful) / total_requests
        
        # Check for performance degradation over time
        first_half_batches = batch_metrics[:num_batches//2]
        second_half_batches = batch_metrics[num_batches//2:]
        
        first_half_avg_time = statistics.mean([b["avg_response_time"] for b in first_half_batches])
        second_half_avg_time = statistics.mean([b["avg_response_time"] for b in second_half_batches])
        
        degradation_ratio = second_half_avg_time / first_half_avg_time if first_half_avg_time > 0 else 1
        
        # Assertions
        assert overall_success_rate >= 0.90, f"Sustained load success rate: {overall_success_rate:.1%}"
        assert degradation_ratio < 2.0, f"Performance degradation ratio: {degradation_ratio:.2f}"
        
        print(f"Sustained load stress test results:")
        print(f"  Total requests: {total_requests}")
        print(f"  Batches: {num_batches}")
        print(f"  Overall success rate: {overall_success_rate:.1%}")
        print(f"  First half avg time: {first_half_avg_time:.3f}s")
        print(f"  Second half avg time: {second_half_avg_time:.3f}s")
        print(f"  Performance degradation: {degradation_ratio:.2f}x")
    
    def test_memory_pressure_stress_test(self, test_client, mock_service_manager):
        """Test endpoints under memory pressure"""
        # Mock service responses
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        def make_memory_pressure_request(request_id):
            start_time = time.time()
            try:
                # Create requests with varying data sizes
                query_size = (request_id % 10) + 1
                large_query = "memory pressure test query " * query_size * 10
                
                response = test_client.post(
                    "/api/advanced/research/search/basic",
                    json={"query": large_query, "max_results": 10}
                )
                
                end_time = time.time()
                return {
                    "request_id": request_id,
                    "success": response.status_code == 200,
                    "response_time": end_time - start_time,
                    "query_size": len(large_query)
                }
            except Exception as e:
                return {
                    "request_id": request_id,
                    "success": False,
                    "error": str(e),
                    "response_time": time.time() - start_time
                }
        
        # Memory pressure test parameters
        total_requests = 100
        concurrent_users = 20
        
        # Execute memory pressure test
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_memory_pressure_request, i) for i in range(total_requests)]
            results = [future.result() for future in as_completed(futures)]
        end_time = time.time()
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Analyze results
        successful_requests = [r for r in results if r["success"]]
        success_rate = len(successful_requests) / total_requests
        
        response_times = [r["response_time"] for r in successful_requests]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        # Assertions
        assert success_rate >= 0.85, f"Memory pressure success rate: {success_rate:.1%}"
        assert memory_increase < 200, f"Memory increase: {memory_increase:.1f}MB"
        assert avg_response_time < 2.0, f"Average response time under memory pressure: {avg_response_time:.3f}s"
        
        print(f"Memory pressure stress test results:")
        print(f"  Total requests: {total_requests}")
        print(f"  Success rate: {success_rate:.1%}")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Initial memory: {initial_memory:.1f}MB")
        print(f"  Final memory: {final_memory:.1f}MB")
        print(f"  Memory increase: {memory_increase:.1f}MB")


@pytest.mark.performance
class TestEndpointPerformanceRegression:
    """Performance regression testing for endpoints"""
    
    def test_performance_baseline_establishment(self, test_client, mock_service_manager):
        """Establish performance baselines for all endpoint categories"""
        # Mock consistent service responses
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        mock_service_manager.get_service_health.return_value = {}
        mock_service_manager.get_initialization_summary.return_value = {
            "total_services": 0, "healthy_services": 0, "failed_services": 0
        }
        
        # Endpoint categories for baseline testing
        endpoint_categories = {
            "health": [
                "/api/advanced/health",
                "/api/advanced/health/detailed",
            ],
            "research": [
                "/api/advanced/research/domains",
                "/api/advanced/research/status",
            ],
            "search": [
                ("/api/advanced/research/search/basic", "POST", {"query": "baseline test"}),
                ("/api/advanced/research/validate", "POST", {"query": "Is this valid?"}),
            ]
        }
        
        baseline_results = {}
        
        for category, endpoints in endpoint_categories.items():
            category_results = []
            
            for endpoint_info in endpoints:
                if isinstance(endpoint_info, tuple):
                    endpoint, method, data = endpoint_info
                else:
                    endpoint, method, data = endpoint_info, "GET", None
                
                # Warm up
                for _ in range(3):
                    try:
                        if method == "GET":
                            test_client.get(endpoint)
                        else:
                            test_client.post(endpoint, json=data)
                    except:
                        pass
                
                # Measure performance
                response_times = []
                for _ in range(20):
                    start_time = time.time()
                    try:
                        if method == "GET":
                            response = test_client.get(endpoint)
                        else:
                            response = test_client.post(endpoint, json=data)
                        
                        end_time = time.time()
                        if response.status_code == 200:
                            response_times.append(end_time - start_time)
                    except:
                        pass
                
                if response_times:
                    category_results.extend(response_times)
            
            if category_results:
                baseline_results[category] = {
                    "avg_response_time": statistics.mean(category_results),
                    "p95_response_time": sorted(category_results)[int(0.95 * len(category_results))],
                    "p99_response_time": sorted(category_results)[int(0.99 * len(category_results))],
                    "max_response_time": max(category_results),
                    "min_response_time": min(category_results),
                    "sample_count": len(category_results)
                }
        
        # Print baseline results
        print("Performance baseline results:")
        for category, metrics in baseline_results.items():
            print(f"  {category.upper()}:")
            print(f"    Average: {metrics['avg_response_time']:.3f}s")
            print(f"    P95: {metrics['p95_response_time']:.3f}s")
            print(f"    P99: {metrics['p99_response_time']:.3f}s")
            print(f"    Max: {metrics['max_response_time']:.3f}s")
            print(f"    Min: {metrics['min_response_time']:.3f}s")
            print(f"    Samples: {metrics['sample_count']}")
        
        # Basic assertions for baseline establishment
        for category, metrics in baseline_results.items():
            assert metrics["avg_response_time"] < 5.0, f"{category} average response time too high"
            assert metrics["p95_response_time"] < 10.0, f"{category} P95 response time too high"
            assert metrics["sample_count"] > 0, f"No samples collected for {category}"
        
        return baseline_results
    
    def test_performance_consistency_over_time(self, test_client, mock_service_manager):
        """Test performance consistency over multiple measurement periods"""
        # Mock service responses
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        def measure_performance_period():
            """Measure performance for one period"""
            response_times = []
            
            for _ in range(10):
                start_time = time.time()
                try:
                    response = test_client.get("/api/advanced/health")
                    end_time = time.time()
                    if response.status_code == 200:
                        response_times.append(end_time - start_time)
                except:
                    pass
            
            return statistics.mean(response_times) if response_times else 0
        
        # Measure performance over multiple periods
        num_periods = 8
        period_results = []
        
        for period in range(num_periods):
            period_avg = measure_performance_period()
            period_results.append(period_avg)
            time.sleep(0.1)  # Small delay between periods
        
        # Analyze consistency
        overall_avg = statistics.mean(period_results)
        consistency_std_dev = statistics.stdev(period_results)
        coefficient_of_variation = consistency_std_dev / overall_avg if overall_avg > 0 else 0
        
        # Check for trends
        first_half = period_results[:num_periods//2]
        second_half = period_results[num_periods//2:]
        
        first_half_avg = statistics.mean(first_half)
        second_half_avg = statistics.mean(second_half)
        
        trend_ratio = second_half_avg / first_half_avg if first_half_avg > 0 else 1
        
        # Assertions
        assert coefficient_of_variation < 0.3, f"Performance too inconsistent: CV={coefficient_of_variation:.3f}"
        assert trend_ratio < 1.5, f"Performance degrading over time: ratio={trend_ratio:.2f}"
        
        print(f"Performance consistency results:")
        print(f"  Periods measured: {num_periods}")
        print(f"  Overall average: {overall_avg:.3f}s")
        print(f"  Standard deviation: {consistency_std_dev:.3f}s")
        print(f"  Coefficient of variation: {coefficient_of_variation:.3f}")
        print(f"  First half average: {first_half_avg:.3f}s")
        print(f"  Second half average: {second_half_avg:.3f}s")
        print(f"  Trend ratio: {trend_ratio:.2f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])