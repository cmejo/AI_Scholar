"""
Endpoint performance and load testing
Tests response times, concurrent requests, and performance under load
"""
import pytest
import asyncio
import time
import statistics
from datetime import datetime
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
class TestEndpointResponseTimes:
    """Test endpoint response time performance"""
    
    def test_basic_health_check_response_time(self, test_client):
        """Test basic health check response time"""
        response_times = []
        
        for _ in range(10):
            start_time = time.time()
            response = test_client.get("/api/advanced/health")
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        # Basic health check should be very fast
        assert avg_response_time < 0.1  # 100ms average
        assert max_response_time < 0.5  # 500ms max
        
        print(f"Basic health check - Avg: {avg_response_time:.3f}s, Max: {max_response_time:.3f}s")
    
    def test_detailed_health_check_response_time(self, test_client, mock_service_manager):
        """Test detailed health check response time"""
        # Mock service manager responses
        mock_service_manager.get_service_health.return_value = {
            f"service_{i}": {
                "status": "healthy",
                "last_check": datetime.utcnow().isoformat(),
                "dependencies": []
            }
            for i in range(5)  # 5 services
        }
        
        mock_service_manager.get_initialization_summary.return_value = {
            "total_services": 5,
            "healthy_services": 5,
            "failed_services": 0,
            "initialization_time": 10.5
        }
        
        response_times = []
        
        for _ in range(10):
            start_time = time.time()
            response = test_client.get("/api/advanced/health/detailed")
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        # Detailed health check should still be reasonably fast
        assert avg_response_time < 0.2  # 200ms average
        assert max_response_time < 1.0  # 1s max
        
        print(f"Detailed health check - Avg: {avg_response_time:.3f}s, Max: {max_response_time:.3f}s")
    
    def test_research_search_response_time(self, test_client, mock_service_manager):
        """Test research search endpoint response time"""
        # Mock fast service response
        mock_service = MagicMock()
        mock_service.advanced_search = AsyncMock(return_value=[
            {
                "id": f"result-{i}",
                "title": f"Research Paper {i}",
                "content": "Mock research content",
                "relevance_score": 0.9 - (i * 0.1),
                "source": "mock_db"
            }
            for i in range(10)
        ])
        
        mock_service_manager.get_service.return_value = mock_service
        mock_service_manager.is_service_healthy.return_value = True
        
        response_times = []
        
        for i in range(10):
            start_time = time.time()
            response = test_client.post(
                "/api/advanced/research/search/basic",
                json={"query": f"test query {i}", "max_results": 10}
            )
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        # Search should be reasonably fast with mocked service
        assert avg_response_time < 0.5  # 500ms average
        assert max_response_time < 2.0  # 2s max
        
        print(f"Research search - Avg: {avg_response_time:.3f}s, Max: {max_response_time:.3f}s")
    
    def test_fallback_response_time(self, test_client, mock_service_manager):
        """Test fallback response time when services are unavailable"""
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        response_times = []
        
        for _ in range(10):
            start_time = time.time()
            response = test_client.post(
                "/api/advanced/research/search/basic",
                json={"query": "test query", "max_results": 5}
            )
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        # Fallback should be very fast (no external service calls)
        assert avg_response_time < 0.1  # 100ms average
        assert max_response_time < 0.3  # 300ms max
        
        print(f"Fallback response - Avg: {avg_response_time:.3f}s, Max: {max_response_time:.3f}s")
    
    def test_analytics_endpoint_response_time(self, test_client, mock_service_manager):
        """Test analytics endpoint response time"""
        mock_service = MagicMock()
        
        # Mock analytics report
        mock_report = MagicMock()
        mock_report.id = "report-123"
        mock_report.title = "Performance Test Report"
        mock_report.summary = "Test summary"
        mock_report.metrics = []
        mock_report.visualizations = []
        mock_report.recommendations = ["Test recommendation"]
        mock_report.timeframe.value = "month"
        mock_report.generated_at = datetime.utcnow()
        mock_report.confidence_score = 0.85
        
        mock_service.generate_comprehensive_report = AsyncMock(return_value=mock_report)
        mock_service_manager.get_service.return_value = mock_service
        
        response_times = []
        
        for i in range(5):  # Fewer iterations for potentially slower endpoint
            start_time = time.time()
            response = test_client.get(f"/api/advanced/analytics/report/user{i}")
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        # Analytics might be slower but should still be reasonable
        assert avg_response_time < 1.0  # 1s average
        assert max_response_time < 3.0  # 3s max
        
        print(f"Analytics report - Avg: {avg_response_time:.3f}s, Max: {max_response_time:.3f}s")


@pytest.mark.performance
class TestConcurrentRequests:
    """Test endpoint performance under concurrent load"""
    
    def test_concurrent_health_checks(self, test_client):
        """Test concurrent health check requests"""
        def make_health_request():
            start_time = time.time()
            response = test_client.get("/api/advanced/health")
            end_time = time.time()
            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 200
            }
        
        # Test with 20 concurrent requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_health_request) for _ in range(20)]
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed
        success_count = sum(1 for r in results if r["success"])
        assert success_count == 20
        
        # Calculate performance metrics
        response_times = [r["response_time"] for r in results]
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        # Performance should not degrade significantly under concurrent load
        assert avg_response_time < 0.5  # 500ms average
        assert max_response_time < 2.0  # 2s max
        
        print(f"Concurrent health checks - Success: {success_count}/20, Avg: {avg_response_time:.3f}s")
    
    def test_concurrent_search_requests(self, test_client, mock_service_manager):
        """Test concurrent search requests"""
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        def make_search_request(query_id):
            start_time = time.time()
            response = test_client.post(
                "/api/advanced/research/search/basic",
                json={"query": f"concurrent test query {query_id}", "max_results": 5}
            )
            end_time = time.time()
            return {
                "query_id": query_id,
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 200,
                "results_count": len(response.json().get("results", [])) if response.status_code == 200 else 0
            }
        
        # Test with 15 concurrent search requests
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(make_search_request, i) for i in range(15)]
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed
        success_count = sum(1 for r in results if r["success"])
        assert success_count == 15
        
        # All should return results
        total_results = sum(r["results_count"] for r in results)
        assert total_results > 0
        
        # Calculate performance metrics
        response_times = [r["response_time"] for r in results]
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        assert avg_response_time < 1.0  # 1s average
        assert max_response_time < 3.0  # 3s max
        
        print(f"Concurrent searches - Success: {success_count}/15, Avg: {avg_response_time:.3f}s")
    
    def test_mixed_concurrent_requests(self, test_client, mock_service_manager):
        """Test mixed concurrent requests to different endpoints"""
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        mock_service_manager.get_service_health.return_value = {}
        mock_service_manager.get_initialization_summary.return_value = {
            "total_services": 0,
            "healthy_services": 0,
            "failed_services": 0
        }
        
        def make_mixed_request(request_type, request_id):
            start_time = time.time()
            
            if request_type == "health":
                response = test_client.get("/api/advanced/health")
            elif request_type == "detailed_health":
                response = test_client.get("/api/advanced/health/detailed")
            elif request_type == "search":
                response = test_client.post(
                    "/api/advanced/research/search/basic",
                    json={"query": f"mixed test {request_id}", "max_results": 3}
                )
            elif request_type == "domains":
                response = test_client.get("/api/advanced/research/domains")
            else:
                response = test_client.get("/api/advanced/health")
            
            end_time = time.time()
            return {
                "request_type": request_type,
                "request_id": request_id,
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 200
            }
        
        # Create mixed request types
        request_types = ["health", "detailed_health", "search", "domains"]
        requests = [(request_types[i % len(request_types)], i) for i in range(20)]
        
        # Execute concurrent mixed requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_mixed_request, req_type, req_id) 
                      for req_type, req_id in requests]
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed
        success_count = sum(1 for r in results if r["success"])
        assert success_count == 20
        
        # Analyze performance by request type
        by_type = {}
        for result in results:
            req_type = result["request_type"]
            if req_type not in by_type:
                by_type[req_type] = []
            by_type[req_type].append(result["response_time"])
        
        for req_type, times in by_type.items():
            avg_time = statistics.mean(times)
            max_time = max(times)
            print(f"Mixed concurrent {req_type} - Count: {len(times)}, Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
            
            # Each type should perform reasonably
            assert avg_time < 2.0  # 2s average
            assert max_time < 5.0   # 5s max
    
    def test_sustained_load(self, test_client, mock_service_manager):
        """Test sustained load over time"""
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        def make_sustained_request(batch_id, request_id):
            start_time = time.time()
            response = test_client.post(
                "/api/advanced/research/search/basic",
                json={"query": f"sustained load test {batch_id}-{request_id}", "max_results": 3}
            )
            end_time = time.time()
            return {
                "batch_id": batch_id,
                "request_id": request_id,
                "response_time": end_time - start_time,
                "success": response.status_code == 200
            }
        
        all_results = []
        batch_times = []
        
        # Run 5 batches of 10 concurrent requests each
        for batch in range(5):
            batch_start = time.time()
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_sustained_request, batch, i) for i in range(10)]
                batch_results = [future.result() for future in as_completed(futures)]
            
            batch_end = time.time()
            batch_times.append(batch_end - batch_start)
            all_results.extend(batch_results)
            
            # Small delay between batches
            time.sleep(0.1)
        
        # All requests should succeed
        total_requests = len(all_results)
        success_count = sum(1 for r in all_results if r["success"])
        assert success_count == total_requests
        
        # Performance should remain consistent across batches
        response_times = [r["response_time"] for r in all_results]
        avg_response_time = statistics.mean(response_times)
        
        # Check that performance doesn't degrade over time
        first_half = response_times[:total_requests//2]
        second_half = response_times[total_requests//2:]
        
        first_half_avg = statistics.mean(first_half)
        second_half_avg = statistics.mean(second_half)
        
        # Second half shouldn't be significantly slower than first half
        degradation_ratio = second_half_avg / first_half_avg
        assert degradation_ratio < 2.0  # Less than 2x degradation
        
        print(f"Sustained load - Total: {total_requests}, Success: {success_count}")
        print(f"Avg response time: {avg_response_time:.3f}s")
        print(f"Performance degradation ratio: {degradation_ratio:.2f}")


@pytest.mark.performance
class TestMemoryAndResourceUsage:
    """Test memory and resource usage under load"""
    
    def test_memory_usage_during_concurrent_requests(self, test_client, mock_service_manager):
        """Test memory usage during concurrent requests"""
        import psutil
        import os
        
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        def make_memory_test_request(request_id):
            response = test_client.post(
                "/api/advanced/research/search/basic",
                json={"query": f"memory test query {request_id}", "max_results": 10}
            )
            return response.status_code == 200
        
        # Make many concurrent requests
        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(make_memory_test_request, i) for i in range(100)]
            results = [future.result() for future in as_completed(futures)]
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # All requests should succeed
        success_count = sum(results)
        assert success_count == 100
        
        # Memory increase should be reasonable (less than 100MB for 100 requests)
        assert memory_increase < 100
        
        print(f"Memory usage - Initial: {initial_memory:.1f}MB, Final: {final_memory:.1f}MB")
        print(f"Memory increase: {memory_increase:.1f}MB for 100 requests")
    
    def test_response_size_consistency(self, test_client, mock_service_manager):
        """Test response size consistency"""
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        response_sizes = []
        
        for i in range(20):
            response = test_client.post(
                "/api/advanced/research/search/basic",
                json={"query": f"size test query {i}", "max_results": 5}
            )
            
            assert response.status_code == 200
            response_size = len(response.content)
            response_sizes.append(response_size)
        
        # Response sizes should be relatively consistent
        avg_size = statistics.mean(response_sizes)
        size_variance = statistics.variance(response_sizes)
        size_std_dev = statistics.stdev(response_sizes)
        
        # Standard deviation should be small relative to average size
        coefficient_of_variation = size_std_dev / avg_size
        assert coefficient_of_variation < 0.1  # Less than 10% variation
        
        print(f"Response sizes - Avg: {avg_size:.0f} bytes, StdDev: {size_std_dev:.0f} bytes")
        print(f"Coefficient of variation: {coefficient_of_variation:.3f}")


@pytest.mark.performance
class TestEndpointScalability:
    """Test endpoint scalability characteristics"""
    
    def test_response_time_vs_load(self, test_client, mock_service_manager):
        """Test how response time scales with load"""
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        load_levels = [1, 5, 10, 15, 20]
        results = {}
        
        for load_level in load_levels:
            def make_load_request():
                start_time = time.time()
                response = test_client.get("/api/advanced/health")
                end_time = time.time()
                return {
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200
                }
            
            # Test with current load level
            with ThreadPoolExecutor(max_workers=load_level) as executor:
                futures = [executor.submit(make_load_request) for _ in range(load_level)]
                load_results = [future.result() for future in as_completed(futures)]
            
            # Calculate metrics for this load level
            response_times = [r["response_time"] for r in load_results]
            success_count = sum(1 for r in load_results if r["success"])
            
            results[load_level] = {
                "avg_response_time": statistics.mean(response_times),
                "max_response_time": max(response_times),
                "success_rate": success_count / load_level,
                "total_requests": load_level
            }
            
            # All requests should succeed
            assert success_count == load_level
        
        # Analyze scalability
        print("Load scalability analysis:")
        for load_level, metrics in results.items():
            print(f"Load {load_level}: Avg {metrics['avg_response_time']:.3f}s, "
                  f"Max {metrics['max_response_time']:.3f}s, "
                  f"Success {metrics['success_rate']:.1%}")
        
        # Response time should not increase dramatically with load
        min_load_time = results[min(load_levels)]["avg_response_time"]
        max_load_time = results[max(load_levels)]["avg_response_time"]
        
        # Response time shouldn't increase by more than 5x
        scalability_ratio = max_load_time / min_load_time
        assert scalability_ratio < 5.0
        
        print(f"Scalability ratio (max/min response time): {scalability_ratio:.2f}")
    
    def test_throughput_measurement(self, test_client, mock_service_manager):
        """Test endpoint throughput measurement"""
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        def make_throughput_request():
            response = test_client.get("/api/advanced/health")
            return response.status_code == 200
        
        # Measure throughput over 10 seconds with 20 concurrent workers
        test_duration = 10  # seconds
        max_workers = 20
        
        start_time = time.time()
        completed_requests = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            
            # Keep submitting requests for the test duration
            while time.time() - start_time < test_duration:
                if len(futures) < max_workers * 2:  # Keep queue full
                    future = executor.submit(make_throughput_request)
                    futures.append(future)
                
                # Check completed futures
                completed_futures = [f for f in futures if f.done()]
                for future in completed_futures:
                    if future.result():
                        completed_requests += 1
                    futures.remove(future)
                
                time.sleep(0.01)  # Small delay to prevent busy waiting
            
            # Wait for remaining futures to complete
            for future in futures:
                if future.result():
                    completed_requests += 1
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        # Calculate throughput
        throughput = completed_requests / actual_duration
        
        # Should achieve reasonable throughput
        assert throughput > 10  # At least 10 requests per second
        
        print(f"Throughput test - Duration: {actual_duration:.1f}s, "
              f"Requests: {completed_requests}, "
              f"Throughput: {throughput:.1f} req/s")
    
    def test_error_rate_under_load(self, test_client, mock_service_manager):
        """Test error rate under high load"""
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        def make_error_test_request(request_id):
            try:
                response = test_client.post(
                    "/api/advanced/research/search/basic",
                    json={"query": f"error test {request_id}", "max_results": 5}
                )
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "error": None
                }
            except Exception as e:
                return {
                    "success": False,
                    "status_code": None,
                    "error": str(e)
                }
        
        # High load test with 50 concurrent requests
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_error_test_request, i) for i in range(100)]
            results = [future.result() for future in as_completed(futures)]
        
        # Calculate error rate
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r["success"])
        error_rate = (total_requests - successful_requests) / total_requests
        
        # Error rate should be very low (less than 1%)
        assert error_rate < 0.01
        
        # Analyze error types if any
        errors = [r for r in results if not r["success"]]
        if errors:
            error_types = {}
            for error in errors:
                error_key = error["status_code"] or "exception"
                error_types[error_key] = error_types.get(error_key, 0) + 1
            
            print(f"Error analysis - Total errors: {len(errors)}")
            for error_type, count in error_types.items():
                print(f"  {error_type}: {count}")
        
        print(f"Error rate under load: {error_rate:.1%} ({len(errors)}/{total_requests})")


@pytest.mark.performance
class TestPerformanceRegression:
    """Test for performance regressions"""
    
    def test_baseline_performance_metrics(self, test_client, mock_service_manager):
        """Establish baseline performance metrics"""
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        # Test different endpoint types
        test_cases = [
            ("health", lambda: test_client.get("/api/advanced/health")),
            ("search", lambda: test_client.post(
                "/api/advanced/research/search/basic",
                json={"query": "baseline test", "max_results": 5}
            )),
            ("domains", lambda: test_client.get("/api/advanced/research/domains"))
        ]
        
        baseline_metrics = {}
        
        for test_name, test_func in test_cases:
            response_times = []
            
            # Warm up
            for _ in range(3):
                test_func()
            
            # Measure performance
            for _ in range(20):
                start_time = time.time()
                response = test_func()
                end_time = time.time()
                
                assert response.status_code == 200
                response_times.append(end_time - start_time)
            
            baseline_metrics[test_name] = {
                "avg_response_time": statistics.mean(response_times),
                "p95_response_time": sorted(response_times)[int(0.95 * len(response_times))],
                "max_response_time": max(response_times),
                "min_response_time": min(response_times)
            }
        
        # Print baseline metrics for reference
        print("Baseline performance metrics:")
        for test_name, metrics in baseline_metrics.items():
            print(f"{test_name}:")
            print(f"  Avg: {metrics['avg_response_time']:.3f}s")
            print(f"  P95: {metrics['p95_response_time']:.3f}s")
            print(f"  Max: {metrics['max_response_time']:.3f}s")
            print(f"  Min: {metrics['min_response_time']:.3f}s")
        
        # Store baseline for comparison (in real scenario, this would be persisted)
        return baseline_metrics
    
    def test_performance_consistency(self, test_client, mock_service_manager):
        """Test performance consistency over multiple runs"""
        mock_service_manager.get_service.return_value = None
        mock_service_manager.is_service_healthy.return_value = False
        
        # Run the same test multiple times
        run_results = []
        
        for run in range(5):
            response_times = []
            
            for _ in range(10):
                start_time = time.time()
                response = test_client.get("/api/advanced/health")
                end_time = time.time()
                
                assert response.status_code == 200
                response_times.append(end_time - start_time)
            
            run_avg = statistics.mean(response_times)
            run_results.append(run_avg)
        
        # Calculate consistency metrics
        overall_avg = statistics.mean(run_results)
        consistency_std_dev = statistics.stdev(run_results)
        consistency_cv = consistency_std_dev / overall_avg
        
        # Performance should be consistent across runs (CV < 20%)
        assert consistency_cv < 0.2
        
        print(f"Performance consistency - Avg: {overall_avg:.3f}s, "
              f"StdDev: {consistency_std_dev:.3f}s, CV: {consistency_cv:.1%}")
        
        return {
            "avg_response_time": overall_avg,
            "consistency_cv": consistency_cv,
            "run_results": run_results
        }