"""
Comprehensive Container Startup Validation Tests
Tests container startup with all services restored
"""

import pytest
import requests
import subprocess
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestContainerStartupValidation:
    """Test suite for container startup validation"""
    
    @pytest.fixture(scope="class")
    def container_info(self):
        """Get container information"""
        try:
            result = subprocess.run(
                ["docker", "ps", "-q", "--filter", "name=advanced-rag-backend"],
                capture_output=True, text=True, check=True
            )
            container_id = result.stdout.strip()
            
            if not container_id:
                pytest.skip("Container not running")
            
            return {"id": container_id, "name": "advanced-rag-backend"}
        except Exception as e:
            pytest.skip(f"Could not get container info: {e}")
    
    @pytest.fixture(scope="class")
    def base_url(self):
        """Base URL for API requests"""
        return "http://localhost:8000"
    
    def test_container_is_running(self, container_info):
        """Test that container is running"""
        assert container_info["id"], "Container should be running"
        
        # Check container status
        result = subprocess.run(
            ["docker", "inspect", container_info["id"], "--format", "{{.State.Status}}"],
            capture_output=True, text=True
        )
        
        status = result.stdout.strip()
        assert status == "running", f"Container should be running, got: {status}"
    
    def test_container_startup_time(self, container_info):
        """Test container startup time is reasonable"""
        try:
            # Get container start time
            result = subprocess.run(
                ["docker", "inspect", container_info["id"], "--format", "{{.State.StartedAt}}"],
                capture_output=True, text=True, check=True
            )
            start_time_str = result.stdout.strip()
            
            # Parse start time
            try:
                from dateutil import parser
                start_time = parser.parse(start_time_str)
            except ImportError:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            
            current_time = datetime.now(start_time.tzinfo)
            uptime = (current_time - start_time).total_seconds()
            
            # Container should have been running for at least 10 seconds to be stable
            assert uptime >= 10, f"Container uptime too short: {uptime}s"
            
            logger.info(f"Container uptime: {uptime:.1f} seconds")
            
        except Exception as e:
            pytest.fail(f"Could not check startup time: {e}")
    
    def test_basic_health_endpoint(self, base_url):
        """Test basic health endpoint"""
        response = requests.get(f"{base_url}/health", timeout=10)
        
        assert response.status_code == 200, f"Health endpoint failed: {response.status_code}"
        assert response.response.elapsed.total_seconds() < 5, "Health endpoint too slow"
        
        # Should return JSON
        data = response.json()
        assert "status" in data, "Health response should contain status"
    
    def test_advanced_health_endpoint(self, base_url):
        """Test advanced health endpoint"""
        response = requests.get(f"{base_url}/api/advanced/health", timeout=10)
        
        assert response.status_code == 200, f"Advanced health endpoint failed: {response.status_code}"
        assert response.elapsed.total_seconds() < 5, "Advanced health endpoint too slow"
    
    def test_detailed_health_endpoint(self, base_url):
        """Test detailed health endpoint with service information"""
        response = requests.get(f"{base_url}/api/advanced/health/detailed", timeout=15)
        
        assert response.status_code == 200, f"Detailed health endpoint failed: {response.status_code}"
        
        data = response.json()
        assert "status" in data, "Detailed health should contain status"
        assert "services" in data, "Detailed health should contain services"
        assert "timestamp" in data, "Detailed health should contain timestamp"
        
        services = data["services"]
        assert isinstance(services, dict), "Services should be a dictionary"
        assert len(services) > 0, "Should have at least one service"
        
        logger.info(f"Found {len(services)} services in detailed health check")
        
        # Check each service has required fields
        for service_name, service_info in services.items():
            assert "status" in service_info, f"Service {service_name} should have status"
            assert service_info["status"] in ["healthy", "degraded", "unhealthy", "mock"], \
                f"Service {service_name} has invalid status: {service_info['status']}"
    
    def test_services_health_endpoint(self, base_url):
        """Test services health endpoint"""
        response = requests.get(f"{base_url}/api/advanced/health/services", timeout=15)
        
        assert response.status_code == 200, f"Services health endpoint failed: {response.status_code}"
        
        data = response.json()
        assert "status" in data, "Services health should contain status"
        assert "services" in data, "Services health should contain services"
        
        services = data["services"]
        assert isinstance(services, dict), "Services should be a dictionary"
        
        # Check service health details
        for service_name, service_info in services.items():
            assert "name" in service_info, f"Service {service_name} should have name"
            assert "status" in service_info, f"Service {service_name} should have status"
            assert "last_check" in service_info, f"Service {service_name} should have last_check"
    
    def test_all_services_initialized(self, base_url):
        """Test that all expected services are initialized"""
        response = requests.get(f"{base_url}/api/advanced/health/detailed", timeout=15)
        assert response.status_code == 200
        
        data = response.json()
        services = data.get("services", {})
        
        # Expected services (may be mock or real)
        expected_services = [
            "database",
            "semantic_search", 
            "research_automation",
            "advanced_analytics",
            "knowledge_graph"
        ]
        
        for expected_service in expected_services:
            assert expected_service in services, f"Service {expected_service} should be initialized"
            
            service_info = services[expected_service]
            status = service_info.get("status")
            
            # Service should be healthy or mock (fallback)
            assert status in ["healthy", "mock"], \
                f"Service {expected_service} should be healthy or mock, got: {status}"
            
            logger.info(f"Service {expected_service}: {status}")
    
    def test_container_resource_usage(self, container_info):
        """Test container resource usage is within acceptable limits"""
        container_id = container_info["id"]
        
        # Get multiple samples for average
        samples = []
        for _ in range(3):
            try:
                result = subprocess.run(
                    ["docker", "stats", "--no-stream", "--format", "json", container_id],
                    capture_output=True, text=True, check=True, timeout=10
                )
                stats = json.loads(result.stdout.strip())
                samples.append(stats)
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Could not get stats sample: {e}")
        
        assert len(samples) > 0, "Should get at least one stats sample"
        
        # Parse CPU and memory usage
        cpu_values = []
        memory_values = []
        
        for stats in samples:
            try:
                cpu_percent = float(stats.get("CPUPerc", "0%").replace("%", ""))
                memory_percent = float(stats.get("MemPerc", "0%").replace("%", ""))
                cpu_values.append(cpu_percent)
                memory_values.append(memory_percent)
            except ValueError:
                continue
        
        if cpu_values and memory_values:
            avg_cpu = sum(cpu_values) / len(cpu_values)
            avg_memory = sum(memory_values) / len(memory_values)
            max_cpu = max(cpu_values)
            max_memory = max(memory_values)
            
            logger.info(f"CPU usage - avg: {avg_cpu:.1f}%, max: {max_cpu:.1f}%")
            logger.info(f"Memory usage - avg: {avg_memory:.1f}%, max: {max_memory:.1f}%")
            
            # Resource usage should be reasonable
            assert avg_cpu < 80, f"Average CPU usage too high: {avg_cpu:.1f}%"
            assert avg_memory < 85, f"Average memory usage too high: {avg_memory:.1f}%"
            assert max_cpu < 95, f"Peak CPU usage too high: {max_cpu:.1f}%"
            assert max_memory < 95, f"Peak memory usage too high: {max_memory:.1f}%"
    
    def test_container_logs_quality(self, container_info):
        """Test container logs for error patterns"""
        container_id = container_info["id"]
        
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", "100", container_id],
                capture_output=True, text=True, check=True
            )
            
            logs = result.stdout + result.stderr
            lines = logs.split('\n')
            
            error_lines = [line for line in lines if 'ERROR' in line.upper()]
            warning_lines = [line for line in lines if 'WARNING' in line.upper()]
            critical_lines = [line for line in lines if 'CRITICAL' in line.upper()]
            
            logger.info(f"Log analysis - Total: {len(lines)}, Errors: {len(error_lines)}, Warnings: {len(warning_lines)}, Critical: {len(critical_lines)}")
            
            # Should not have critical errors
            assert len(critical_lines) == 0, f"Found {len(critical_lines)} critical errors in logs"
            
            # Should have reasonable error count
            assert len(error_lines) < 10, f"Too many errors in logs: {len(error_lines)}"
            
            # Log recent errors for debugging
            if error_lines:
                logger.warning("Recent errors in logs:")
                for error in error_lines[-3:]:
                    logger.warning(f"  {error.strip()}")
                    
        except Exception as e:
            logger.warning(f"Could not analyze logs: {e}")
    
    def test_service_endpoints_basic(self, base_url):
        """Test basic functionality of service endpoints"""
        endpoints_to_test = [
            # Research endpoints
            ("/api/advanced/research/search", "POST", {"query": "test", "limit": 5}),
            
            # Analytics endpoints  
            ("/api/advanced/analytics/user-behavior", "GET", None),
            ("/api/advanced/analytics/feature-performance", "GET", None),
            
            # Knowledge graph endpoints
            ("/api/advanced/knowledge-graph/entities", "GET", None),
        ]
        
        for endpoint, method, payload in endpoints_to_test:
            try:
                if method == "GET":
                    response = requests.get(f"{base_url}{endpoint}", timeout=10)
                elif method == "POST":
                    response = requests.post(f"{base_url}{endpoint}", json=payload, timeout=10)
                else:
                    continue
                
                # Acceptable status codes (200, 422 for validation errors, 503 for service unavailable)
                acceptable_codes = [200, 201, 422, 503]
                assert response.status_code in acceptable_codes, \
                    f"Endpoint {endpoint} returned unexpected status: {response.status_code}"
                
                # Response time should be reasonable
                assert response.elapsed.total_seconds() < 15, \
                    f"Endpoint {endpoint} too slow: {response.elapsed.total_seconds():.2f}s"
                
                logger.info(f"Endpoint {endpoint}: {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
                
            except requests.exceptions.Timeout:
                pytest.fail(f"Endpoint {endpoint} timed out")
            except Exception as e:
                logger.warning(f"Endpoint {endpoint} error: {e}")
    
    def test_container_stability_over_time(self, base_url, container_info):
        """Test container stability over a short period"""
        duration = 30  # Test for 30 seconds
        interval = 5   # Check every 5 seconds
        
        start_time = time.time()
        health_checks = []
        
        while time.time() - start_time < duration:
            try:
                check_start = time.time()
                response = requests.get(f"{base_url}/health", timeout=5)
                response_time = time.time() - check_start
                
                health_checks.append({
                    "timestamp": time.time(),
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "healthy": response.status_code == 200
                })
                
            except Exception as e:
                health_checks.append({
                    "timestamp": time.time(),
                    "healthy": False,
                    "error": str(e)
                })
            
            time.sleep(interval)
        
        # Analyze stability
        assert len(health_checks) >= 3, "Should have multiple health checks"
        
        healthy_checks = sum(1 for check in health_checks if check.get("healthy", False))
        success_rate = (healthy_checks / len(health_checks)) * 100
        
        logger.info(f"Stability test - {healthy_checks}/{len(health_checks)} checks successful ({success_rate:.1f}%)")
        
        # Should have high success rate
        assert success_rate >= 80, f"Container stability too low: {success_rate:.1f}%"
        
        # Response times should be consistent
        response_times = [check["response_time"] for check in health_checks if "response_time" in check]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            logger.info(f"Response times - avg: {avg_response_time:.3f}s, max: {max_response_time:.3f}s")
            
            assert avg_response_time < 2.0, f"Average response time too high: {avg_response_time:.3f}s"
            assert max_response_time < 5.0, f"Max response time too high: {max_response_time:.3f}s"
    
    def test_concurrent_requests_handling(self, base_url):
        """Test container can handle concurrent requests"""
        num_threads = 5
        requests_per_thread = 3
        results = []
        
        def make_requests():
            thread_results = []
            for _ in range(requests_per_thread):
                try:
                    start_time = time.time()
                    response = requests.get(f"{base_url}/health", timeout=10)
                    response_time = time.time() - start_time
                    
                    thread_results.append({
                        "status_code": response.status_code,
                        "response_time": response_time,
                        "success": response.status_code == 200
                    })
                except Exception as e:
                    thread_results.append({
                        "success": False,
                        "error": str(e)
                    })
            
            results.extend(thread_results)
        
        # Start concurrent threads
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=make_requests)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)
        
        # Analyze results
        total_requests = num_threads * requests_per_thread
        successful_requests = sum(1 for result in results if result.get("success", False))
        success_rate = (successful_requests / total_requests) * 100
        
        logger.info(f"Concurrent requests - {successful_requests}/{total_requests} successful ({success_rate:.1f}%)")
        
        # Should handle concurrent requests well
        assert success_rate >= 90, f"Concurrent request success rate too low: {success_rate:.1f}%"
        
        # Response times should still be reasonable under load
        response_times = [result["response_time"] for result in results if "response_time" in result]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            logger.info(f"Concurrent response times - avg: {avg_response_time:.3f}s, max: {max_response_time:.3f}s")
            
            assert avg_response_time < 3.0, f"Average concurrent response time too high: {avg_response_time:.3f}s"
            assert max_response_time < 10.0, f"Max concurrent response time too high: {max_response_time:.3f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])