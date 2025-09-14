#!/usr/bin/env python3
"""
End-to-End Integration Testing Suite

This module performs comprehensive end-to-end integration testing
of all endpoints with real service dependencies, validates data flow
between services, and performs load testing and performance validation.

Requirements covered:
- 5.3: Incremental Testing and Validation
- 2.1: Endpoint Functionality Restoration  
- 2.2: Error Handling and Monitoring
"""

import asyncio
import time
import requests
import json
import concurrent.futures
import threading
import statistics
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from core.service_manager import ServiceManager
    from models.schemas import DetailedHealthCheckResponse
except ImportError as e:
    logger.warning(f"Could not import backend modules: {e}")
    ServiceManager = None
    DetailedHealthCheckResponse = None

class EndToEndIntegrationTester:
    """
    Comprehensive end-to-end integration testing
    
    This class performs comprehensive testing of:
    1. All endpoints with real service dependencies
    2. Data flow validation between services and endpoints
    3. Load testing and performance validation
    4. Service integration and error handling
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {}
        self.performance_metrics = {}
        self.service_dependencies = {
            "semantic_search": ["database"],
            "research_automation": ["database", "semantic_search"],
            "advanced_analytics": ["database"],
            "knowledge_graph": ["database", "semantic_search"]
        }
        
    def test_basic_endpoints(self) -> Dict:
        """Test basic application endpoints"""
        endpoints = {
            "root": "/",
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
        
        results = {}
        
        for name, endpoint in endpoints.items():
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                results[name] = {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "success": response.status_code == 200,
                    "content_type": response.headers.get("content-type", ""),
                    "content_length": len(response.content)
                }
                
                # Try to parse JSON for API endpoints
                if endpoint not in ["/docs", "/openapi.json"] and response.status_code == 200:
                    try:
                        results[name]["json_data"] = response.json()
                    except:
                        pass
                        
            except Exception as e:
                results[name] = {
                    "endpoint": endpoint,
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    def test_advanced_endpoints(self) -> Dict:
        """Test advanced API endpoints"""
        endpoints = {
            "advanced_health": "/api/advanced/health",
            "detailed_health": "/api/advanced/health/detailed",
            "services_health": "/api/advanced/health/services"
        }
        
        results = {}
        
        for name, endpoint in endpoints.items():
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=15)
                response_time = time.time() - start_time
                
                results[name] = {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "success": response.status_code == 200
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        results[name]["json_data"] = data
                        
                        # Analyze health data
                        if "services" in data:
                            services = data["services"]
                            healthy_services = sum(1 for s in services.values() 
                                                 if isinstance(s, dict) and s.get("status") == "healthy")
                            results[name]["services_count"] = len(services)
                            results[name]["healthy_services"] = healthy_services
                            results[name]["health_percentage"] = (healthy_services / len(services)) * 100 if services else 0
                            
                    except Exception as e:
                        results[name]["json_error"] = str(e)
                        
            except Exception as e:
                results[name] = {
                    "endpoint": endpoint,
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    def test_service_endpoints(self) -> Dict:
        """Test individual service endpoints with comprehensive validation"""
        # Test all available service endpoints from advanced_endpoints.py
        service_endpoints = {
            # Database endpoints
            "database_health": "/api/advanced/database/health",
            "database_connection": "/api/advanced/database/connection",
            "database_models": "/api/advanced/database/models",
            "database_migration": "/api/advanced/database/migration/check",
            
            # Service health endpoints
            "semantic_search_health": "/api/advanced/semantic-search/health",
            "research_automation_health": "/api/advanced/research-automation/health",
            "advanced_analytics_health": "/api/advanced/advanced-analytics/health",
            "knowledge_graph_health": "/api/advanced/knowledge-graph/health",
            
            # Research endpoints
            "research_status": "/api/advanced/research/status",
            "research_capabilities": "/api/advanced/research/capabilities",
            "research_domains": "/api/advanced/research/domains",
            
            # Health monitoring endpoints
            "health_monitoring": "/api/advanced/health/monitoring",
        }
        
        results = {}
        
        for name, endpoint in service_endpoints.items():
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=15)
                response_time = time.time() - start_time
                
                results[name] = {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "success": response.status_code == 200,
                    "implemented": response.status_code != 404
                }
                
                if response.status_code == 200:
                    try:
                        json_data = response.json()
                        results[name]["json_data"] = json_data
                        
                        # Validate response structure for health endpoints
                        if "health" in endpoint:
                            results[name]["has_status"] = "status" in json_data
                            results[name]["has_timestamp"] = "timestamp" in json_data
                            results[name]["service_status"] = json_data.get("status", "unknown")
                            
                        # Validate service-specific data
                        if "research/status" in endpoint:
                            results[name]["has_services"] = "services" in json_data
                            if "services" in json_data:
                                services = json_data["services"]
                                results[name]["services_count"] = len(services)
                                results[name]["healthy_services"] = sum(
                                    1 for s in services.values() 
                                    if isinstance(s, dict) and s.get("status") == "healthy"
                                )
                                
                    except Exception as e:
                        results[name]["json_error"] = str(e)
                        
            except Exception as e:
                results[name] = {
                    "endpoint": endpoint,
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    def test_service_dependencies(self) -> Dict:
        """Test service dependencies and initialization order"""
        results = {}
        
        try:
            # Get detailed health information
            response = requests.get(f"{self.base_url}/api/advanced/health/detailed", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                services = data.get("services", {})
                
                results["dependency_validation"] = {}
                
                for service_name, dependencies in self.service_dependencies.items():
                    service_result = {
                        "service": service_name,
                        "dependencies": dependencies,
                        "service_available": service_name in services,
                        "dependencies_met": True,
                        "missing_dependencies": []
                    }
                    
                    if service_name in services:
                        service_status = services[service_name]
                        service_result["status"] = service_status.get("status", "unknown")
                        
                        # Check if dependencies are available
                        for dep in dependencies:
                            if dep not in services:
                                service_result["dependencies_met"] = False
                                service_result["missing_dependencies"].append(dep)
                            elif services[dep].get("status") != "healthy":
                                service_result["dependencies_met"] = False
                                service_result["missing_dependencies"].append(f"{dep} (unhealthy)")
                    
                    results["dependency_validation"][service_name] = service_result
                    
            else:
                results["dependency_validation"] = {
                    "error": f"Could not get service information: {response.status_code}"
                }
                
        except Exception as e:
            results["dependency_validation"] = {"error": str(e)}
        
        return results
    
    def test_functional_endpoints(self) -> Dict:
        """Test functional endpoints with real data"""
        results = {}
        
        # Test research search endpoint
        try:
            search_data = {
                "query": "machine learning algorithms",
                "max_results": 5,
                "user_id": "test_user"
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/advanced/research/search/basic",
                json=search_data,
                timeout=20
            )
            response_time = time.time() - start_time
            
            results["research_search"] = {
                "endpoint": "/api/advanced/research/search/basic",
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code == 200
            }
            
            if response.status_code == 200:
                json_data = response.json()
                results["research_search"]["json_data"] = json_data
                results["research_search"]["has_results"] = "results" in json_data
                results["research_search"]["service_used"] = json_data.get("service_used", "unknown")
                results["research_search"]["is_fallback"] = json_data.get("fallback", False)
                
                if "results" in json_data:
                    results["research_search"]["results_count"] = len(json_data["results"])
                    
        except Exception as e:
            results["research_search"] = {"error": str(e)}
        
        return results
    
    def test_data_flow_validation(self) -> Dict:
        """Test comprehensive data flow between services and endpoints"""
        results = {}
        
        # Test 1: Health data consistency across endpoints
        try:
            endpoints = [
                ("/health", "basic_health"),
                ("/api/advanced/health", "advanced_health"),
                ("/api/advanced/health/detailed", "detailed_health"),
                ("/api/advanced/health/services", "services_health")
            ]
            
            health_responses = {}
            
            for endpoint, name in endpoints:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=15)
                    health_responses[name] = {
                        "status_code": response.status_code,
                        "success": response.status_code == 200,
                        "data": response.json() if response.status_code == 200 else None
                    }
                except Exception as e:
                    health_responses[name] = {"error": str(e)}
            
            results["health_consistency"] = health_responses
            
            # Validate consistency between health endpoints
            if (health_responses.get("basic_health", {}).get("success") and 
                health_responses.get("advanced_health", {}).get("success")):
                
                basic_status = health_responses["basic_health"]["data"].get("status")
                advanced_status = health_responses["advanced_health"]["data"].get("status")
                results["health_consistency"]["status_consistency"] = (basic_status == advanced_status)
                
        except Exception as e:
            results["health_consistency"] = {"error": str(e)}
        
        # Test 2: Service initialization and dependency data flow
        try:
            detailed_response = requests.get(f"{self.base_url}/api/advanced/health/detailed", timeout=15)
            services_response = requests.get(f"{self.base_url}/api/advanced/health/services", timeout=15)
            
            results["service_data_flow"] = {
                "detailed_available": detailed_response.status_code == 200,
                "services_available": services_response.status_code == 200
            }
            
            if detailed_response.status_code == 200:
                detailed_data = detailed_response.json()
                results["service_data_flow"]["detailed_structure"] = {
                    "has_status": "status" in detailed_data,
                    "has_timestamp": "timestamp" in detailed_data,
                    "has_services": "services" in detailed_data,
                    "has_summary": "summary" in detailed_data
                }
                
                if "services" in detailed_data:
                    services = detailed_data["services"]
                    results["service_data_flow"]["services_count"] = len(services)
                    results["service_data_flow"]["service_names"] = list(services.keys())
                    
                    # Validate service data structure
                    service_validation = {}
                    for service_name, service_data in services.items():
                        service_validation[service_name] = {
                            "has_status": "status" in service_data,
                            "has_last_check": "last_check" in service_data,
                            "status_value": service_data.get("status", "unknown")
                        }
                    
                    results["service_data_flow"]["service_validation"] = service_validation
                    
        except Exception as e:
            results["service_data_flow"] = {"error": str(e)}
        
        # Test 3: Cross-service data flow validation
        try:
            # Test research status endpoint which aggregates multiple services
            research_status = requests.get(f"{self.base_url}/api/advanced/research/status", timeout=15)
            
            results["cross_service_flow"] = {
                "research_status_available": research_status.status_code == 200
            }
            
            if research_status.status_code == 200:
                research_data = research_status.json()
                results["cross_service_flow"]["research_data"] = {
                    "has_services": "services" in research_data,
                    "has_overall_status": "status" in research_data,
                    "overall_status": research_data.get("status", "unknown")
                }
                
                if "services" in research_data:
                    research_services = research_data["services"]
                    results["cross_service_flow"]["research_services_count"] = len(research_services)
                    
                    # Validate that research services match detailed health services
                    detailed_response = requests.get(f"{self.base_url}/api/advanced/health/detailed", timeout=10)
                    if detailed_response.status_code == 200:
                        detailed_services = detailed_response.json().get("services", {})
                        
                        consistency_check = {}
                        for service_name in research_services:
                            consistency_check[service_name] = {
                                "in_research_status": True,
                                "in_detailed_health": service_name in detailed_services,
                                "status_match": (
                                    research_services[service_name].get("status") == 
                                    detailed_services.get(service_name, {}).get("status")
                                ) if service_name in detailed_services else False
                            }
                        
                        results["cross_service_flow"]["service_consistency"] = consistency_check
                        
        except Exception as e:
            results["cross_service_flow"] = {"error": str(e)}
        
        # Test 4: Error handling data flow
        try:
            # Test endpoint with invalid data to validate error handling
            invalid_search = requests.post(
                f"{self.base_url}/api/advanced/research/search/basic",
                json={},  # Missing required 'query' field
                timeout=10
            )
            
            results["error_handling_flow"] = {
                "invalid_request_handled": invalid_search.status_code in [400, 422],
                "status_code": invalid_search.status_code
            }
            
            if invalid_search.status_code in [400, 422]:
                try:
                    error_data = invalid_search.json()
                    results["error_handling_flow"]["error_structure"] = {
                        "has_error_message": any(key in error_data for key in ["message", "detail", "error"]),
                        "error_data": error_data
                    }
                except:
                    results["error_handling_flow"]["error_structure"] = {"json_parse_failed": True}
                    
        except Exception as e:
            results["error_handling_flow"] = {"error": str(e)}
        
        return results
    
    def perform_load_testing(self, duration: int = 30, concurrent_requests: int = 5) -> Dict:
        """Perform comprehensive load testing and performance validation"""
        results = {}
        
        # Test endpoints for load testing with different complexity levels
        test_endpoints = [
            {
                "name": "basic_health",
                "endpoint": "/health",
                "method": "GET",
                "complexity": "low"
            },
            {
                "name": "advanced_health",
                "endpoint": "/api/advanced/health",
                "method": "GET", 
                "complexity": "low"
            },
            {
                "name": "detailed_health",
                "endpoint": "/api/advanced/health/detailed",
                "method": "GET",
                "complexity": "medium"
            },
            {
                "name": "services_health",
                "endpoint": "/api/advanced/health/services",
                "method": "GET",
                "complexity": "high"
            },
            {
                "name": "research_status",
                "endpoint": "/api/advanced/research/status",
                "method": "GET",
                "complexity": "high"
            },
            {
                "name": "research_search",
                "endpoint": "/api/advanced/research/search/basic",
                "method": "POST",
                "data": {"query": "test search", "max_results": 3},
                "complexity": "very_high"
            }
        ]
        
        for endpoint_config in test_endpoints:
            endpoint_name = endpoint_config["name"]
            endpoint_path = endpoint_config["endpoint"]
            method = endpoint_config["method"]
            data = endpoint_config.get("data")
            
            endpoint_results = {
                "endpoint": endpoint_path,
                "method": method,
                "complexity": endpoint_config["complexity"],
                "duration": duration,
                "concurrent_requests": concurrent_requests,
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "response_times": [],
                "status_codes": {},
                "errors": [],
                "memory_usage": [],
                "throughput_over_time": []
            }
            
            def make_request():
                try:
                    start_time = time.time()
                    
                    if method == "GET":
                        response = requests.get(f"{self.base_url}{endpoint_path}", timeout=15)
                    else:  # POST
                        response = requests.post(
                            f"{self.base_url}{endpoint_path}", 
                            json=data, 
                            timeout=15
                        )
                    
                    response_time = time.time() - start_time
                    
                    return {
                        "success": response.status_code == 200,
                        "response_time": response_time,
                        "status_code": response.status_code,
                        "content_length": len(response.content),
                        "timestamp": time.time()
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "response_time": None,
                        "timestamp": time.time()
                    }
            
            # Run load test with performance monitoring
            test_start_time = time.time()
            throughput_window = 5  # seconds
            last_throughput_check = test_start_time
            requests_in_window = 0
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
                futures = []
                
                while time.time() - test_start_time < duration:
                    # Submit requests up to concurrent limit
                    while len(futures) < concurrent_requests:
                        future = executor.submit(make_request)
                        futures.append(future)
                    
                    # Process completed requests
                    completed_futures = []
                    for future in futures:
                        if future.done():
                            try:
                                result = future.result()
                                endpoint_results["total_requests"] += 1
                                requests_in_window += 1
                                
                                if result["success"]:
                                    endpoint_results["successful_requests"] += 1
                                    if result["response_time"]:
                                        endpoint_results["response_times"].append(result["response_time"])
                                else:
                                    endpoint_results["failed_requests"] += 1
                                    if "error" in result:
                                        endpoint_results["errors"].append(result["error"])
                                
                                # Track status codes
                                status_code = result.get("status_code", "error")
                                endpoint_results["status_codes"][status_code] = (
                                    endpoint_results["status_codes"].get(status_code, 0) + 1
                                )
                                        
                                completed_futures.append(future)
                            except Exception as e:
                                endpoint_results["failed_requests"] += 1
                                endpoint_results["errors"].append(str(e))
                                completed_futures.append(future)
                    
                    # Remove completed futures
                    for future in completed_futures:
                        futures.remove(future)
                    
                    # Calculate throughput over time
                    current_time = time.time()
                    if current_time - last_throughput_check >= throughput_window:
                        throughput = requests_in_window / throughput_window
                        endpoint_results["throughput_over_time"].append({
                            "timestamp": current_time - test_start_time,
                            "throughput": throughput
                        })
                        requests_in_window = 0
                        last_throughput_check = current_time
                    
                    time.sleep(0.05)  # Small delay to prevent overwhelming
                
                # Wait for remaining futures
                for future in futures:
                    try:
                        result = future.result(timeout=10)
                        endpoint_results["total_requests"] += 1
                        
                        if result["success"]:
                            endpoint_results["successful_requests"] += 1
                            if result["response_time"]:
                                endpoint_results["response_times"].append(result["response_time"])
                        else:
                            endpoint_results["failed_requests"] += 1
                            if "error" in result:
                                endpoint_results["errors"].append(result["error"])
                    except:
                        endpoint_results["failed_requests"] += 1
            
            # Calculate comprehensive statistics
            if endpoint_results["response_times"]:
                response_times = endpoint_results["response_times"]
                endpoint_results["performance_stats"] = {
                    "avg_response_time": statistics.mean(response_times),
                    "median_response_time": statistics.median(response_times),
                    "min_response_time": min(response_times),
                    "max_response_time": max(response_times),
                    "std_dev_response_time": statistics.stdev(response_times) if len(response_times) > 1 else 0
                }
                
                # Calculate percentiles
                sorted_times = sorted(response_times)
                n = len(sorted_times)
                endpoint_results["performance_stats"]["p50_response_time"] = sorted_times[int(n * 0.5)]
                endpoint_results["performance_stats"]["p90_response_time"] = sorted_times[int(n * 0.9)]
                endpoint_results["performance_stats"]["p95_response_time"] = sorted_times[int(n * 0.95)]
                endpoint_results["performance_stats"]["p99_response_time"] = sorted_times[int(n * 0.99)]
            
            # Calculate success metrics
            endpoint_results["success_rate"] = (
                endpoint_results["successful_requests"] / endpoint_results["total_requests"] * 100
                if endpoint_results["total_requests"] > 0 else 0
            )
            
            endpoint_results["requests_per_second"] = endpoint_results["total_requests"] / duration
            endpoint_results["error_rate"] = (
                endpoint_results["failed_requests"] / endpoint_results["total_requests"] * 100
                if endpoint_results["total_requests"] > 0 else 0
            )
            
            # Performance assessment
            avg_response_time = endpoint_results.get("performance_stats", {}).get("avg_response_time", float('inf'))
            success_rate = endpoint_results["success_rate"]
            
            if success_rate >= 99 and avg_response_time <= 0.1:
                performance_grade = "excellent"
            elif success_rate >= 95 and avg_response_time <= 0.5:
                performance_grade = "good"
            elif success_rate >= 90 and avg_response_time <= 1.0:
                performance_grade = "acceptable"
            else:
                performance_grade = "poor"
            
            endpoint_results["performance_grade"] = performance_grade
            
            results[endpoint_name] = endpoint_results
        
        return results
    
    def perform_stress_testing(self, max_concurrent: int = 20, step_duration: int = 10) -> Dict:
        """Perform stress testing with increasing load"""
        results = {}
        
        test_endpoint = "/api/advanced/health"
        stress_levels = [1, 3, 5, 10, 15, max_concurrent]
        
        for concurrent_level in stress_levels:
            level_results = {
                "concurrent_requests": concurrent_level,
                "duration": step_duration,
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "response_times": [],
                "errors": []
            }
            
            def make_stress_request():
                try:
                    start_time = time.time()
                    response = requests.get(f"{self.base_url}{test_endpoint}", timeout=20)
                    response_time = time.time() - start_time
                    
                    return {
                        "success": response.status_code == 200,
                        "response_time": response_time,
                        "status_code": response.status_code
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "response_time": None
                    }
            
            # Run stress test for this level
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_level) as executor:
                futures = []
                
                while time.time() - start_time < step_duration:
                    # Maintain concurrent request level
                    while len(futures) < concurrent_level:
                        future = executor.submit(make_stress_request)
                        futures.append(future)
                    
                    # Process completed requests
                    completed_futures = []
                    for future in futures:
                        if future.done():
                            try:
                                result = future.result()
                                level_results["total_requests"] += 1
                                
                                if result["success"]:
                                    level_results["successful_requests"] += 1
                                    if result["response_time"]:
                                        level_results["response_times"].append(result["response_time"])
                                else:
                                    level_results["failed_requests"] += 1
                                    if "error" in result:
                                        level_results["errors"].append(result["error"])
                                        
                                completed_futures.append(future)
                            except Exception as e:
                                level_results["failed_requests"] += 1
                                level_results["errors"].append(str(e))
                                completed_futures.append(future)
                    
                    # Remove completed futures
                    for future in completed_futures:
                        futures.remove(future)
                    
                    time.sleep(0.01)
                
                # Wait for remaining futures
                for future in futures:
                    try:
                        result = future.result(timeout=5)
                        level_results["total_requests"] += 1
                        
                        if result["success"]:
                            level_results["successful_requests"] += 1
                            if result["response_time"]:
                                level_results["response_times"].append(result["response_time"])
                        else:
                            level_results["failed_requests"] += 1
                            if "error" in result:
                                level_results["errors"].append(result["error"])
                    except:
                        level_results["failed_requests"] += 1
            
            # Calculate metrics for this stress level
            if level_results["response_times"]:
                level_results["avg_response_time"] = statistics.mean(level_results["response_times"])
                level_results["max_response_time"] = max(level_results["response_times"])
            
            level_results["success_rate"] = (
                level_results["successful_requests"] / level_results["total_requests"] * 100
                if level_results["total_requests"] > 0 else 0
            )
            
            level_results["requests_per_second"] = level_results["total_requests"] / step_duration
            
            results[f"level_{concurrent_level}"] = level_results
        
        return results
    
    def run_comprehensive_integration_test(self, include_stress_test: bool = False) -> Dict:
        """
        Run comprehensive end-to-end integration testing
        
        This method performs all required testing as per requirements:
        - 5.3: Incremental Testing and Validation
        - 2.1: Endpoint Functionality Restoration
        - 2.2: Error Handling and Monitoring
        """
        logger.info("Starting comprehensive end-to-end integration testing...")
        
        test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_duration": 0,
            "requirements_coverage": {
                "5.3": "Incremental Testing and Validation",
                "2.1": "Endpoint Functionality Restoration", 
                "2.2": "Error Handling and Monitoring"
            }
        }
        
        start_time = time.time()
        
        # Test 1: Basic endpoints (Requirement 2.1)
        logger.info("Testing basic endpoints...")
        test_results["basic_endpoints"] = self.test_basic_endpoints()
        
        # Test 2: Advanced endpoints (Requirement 2.1)
        logger.info("Testing advanced endpoints...")
        test_results["advanced_endpoints"] = self.test_advanced_endpoints()
        
        # Test 3: Service endpoints with comprehensive validation (Requirement 2.1, 5.3)
        logger.info("Testing service endpoints...")
        test_results["service_endpoints"] = self.test_service_endpoints()
        
        # Test 4: Service dependencies (Requirement 5.3)
        logger.info("Testing service dependencies...")
        test_results["service_dependencies"] = self.test_service_dependencies()
        
        # Test 5: Functional endpoints with real data (Requirement 2.1, 2.2)
        logger.info("Testing functional endpoints...")
        test_results["functional_endpoints"] = self.test_functional_endpoints()
        
        # Test 6: Comprehensive data flow validation (Requirement 5.3, 2.2)
        logger.info("Testing data flow validation...")
        test_results["data_flow"] = self.test_data_flow_validation()
        
        # Test 7: Load testing and performance validation (Requirement 5.3)
        logger.info("Performing load testing...")
        test_results["load_testing"] = self.perform_load_testing(duration=30, concurrent_requests=5)
        
        # Test 8: Stress testing (optional, for comprehensive validation)
        if include_stress_test:
            logger.info("Performing stress testing...")
            test_results["stress_testing"] = self.perform_stress_testing(max_concurrent=15, step_duration=10)
        
        test_results["test_duration"] = time.time() - start_time
        
        # Calculate comprehensive assessment
        endpoint_categories = ["basic_endpoints", "advanced_endpoints", "service_endpoints", "functional_endpoints"]
        total_success = 0
        total_tests = 0
        
        category_results = {}
        
        for category in endpoint_categories:
            if category in test_results:
                category_data = test_results[category]
                success_count = sum(1 for r in category_data.values() if r.get("success", False))
                total_count = len(category_data)
                
                category_results[category] = {
                    "success_count": success_count,
                    "total_count": total_count,
                    "success_rate": (success_count / total_count * 100) if total_count > 0 else 0
                }
                
                total_success += success_count
                total_tests += total_count
        
        # Assess data flow validation
        data_flow_success = 0
        data_flow_total = 0
        
        if "data_flow" in test_results:
            for test_name, test_result in test_results["data_flow"].items():
                data_flow_total += 1
                if isinstance(test_result, dict) and "error" not in test_result:
                    # Check for successful indicators in the test result
                    if any(key.endswith("_available") and test_result.get(key) for key in test_result.keys()):
                        data_flow_success += 1
                    elif test_result.get("status_consistency") or test_result.get("research_status_available"):
                        data_flow_success += 1
        
        # Assess load testing performance
        load_test_assessment = {"overall_grade": "unknown", "endpoint_grades": {}}
        
        if "load_testing" in test_results:
            grades = []
            for endpoint_name, endpoint_result in test_results["load_testing"].items():
                grade = endpoint_result.get("performance_grade", "unknown")
                load_test_assessment["endpoint_grades"][endpoint_name] = grade
                
                if grade in ["excellent", "good", "acceptable", "poor"]:
                    grade_score = {"excellent": 4, "good": 3, "acceptable": 2, "poor": 1}[grade]
                    grades.append(grade_score)
            
            if grades:
                avg_grade_score = sum(grades) / len(grades)
                if avg_grade_score >= 3.5:
                    load_test_assessment["overall_grade"] = "excellent"
                elif avg_grade_score >= 2.5:
                    load_test_assessment["overall_grade"] = "good"
                elif avg_grade_score >= 1.5:
                    load_test_assessment["overall_grade"] = "acceptable"
                else:
                    load_test_assessment["overall_grade"] = "poor"
        
        # Overall assessment
        overall_success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
        data_flow_success_rate = (data_flow_success / data_flow_total * 100) if data_flow_total > 0 else 0
        
        # Determine if test passed based on comprehensive criteria
        test_passed = (
            overall_success_rate >= 80 and  # At least 80% of endpoints working
            data_flow_success_rate >= 70 and  # At least 70% of data flow tests passing
            load_test_assessment["overall_grade"] in ["excellent", "good", "acceptable"]  # Acceptable performance
        )
        
        test_results["summary"] = {
            "category_results": category_results,
            "overall_success_rate": overall_success_rate,
            "data_flow_success_rate": data_flow_success_rate,
            "load_test_assessment": load_test_assessment,
            "total_endpoints_tested": total_tests,
            "total_endpoints_successful": total_success,
            "test_passed": test_passed,
            "requirements_met": {
                "2.1_endpoint_functionality": overall_success_rate >= 80,
                "2.2_error_handling": data_flow_success_rate >= 70,
                "5.3_testing_validation": test_passed
            }
        }
        
        return test_results


def run_integration_tests(include_stress_test: bool = False):
    """Run integration tests with comprehensive detailed output"""
    tester = EndToEndIntegrationTester()
    results = tester.run_comprehensive_integration_test(include_stress_test=include_stress_test)
    
    print("\n" + "="*100)
    print("COMPREHENSIVE END-TO-END INTEGRATION TEST RESULTS")
    print("="*100)
    print(f"Test Duration: {results['test_duration']:.2f} seconds")
    print(f"Timestamp: {results['timestamp']}")
    
    # Requirements coverage
    print(f"\nRequirements Coverage:")
    for req_id, req_desc in results.get("requirements_coverage", {}).items():
        print(f"  {req_id}: {req_desc}")
    
    # Basic endpoints summary
    print(f"\n{'='*50}")
    print("BASIC ENDPOINTS")
    print("="*50)
    for name, result in results.get("basic_endpoints", {}).items():
        status = "✓" if result.get("success") else "✗"
        time_info = f" ({result.get('response_time', 0):.3f}s)" if result.get("response_time") else ""
        print(f"  {status} {name}: {result.get('endpoint', 'N/A')}{time_info}")
    
    # Advanced endpoints summary
    print(f"\n{'='*50}")
    print("ADVANCED ENDPOINTS")
    print("="*50)
    for name, result in results.get("advanced_endpoints", {}).items():
        status = "✓" if result.get("success") else "✗"
        time_info = f" ({result.get('response_time', 0):.3f}s)" if result.get("response_time") else ""
        health_info = ""
        if result.get("health_percentage") is not None:
            health_info = f" - {result.get('health_percentage', 0):.1f}% healthy"
        print(f"  {status} {name}: {result.get('endpoint', 'N/A')}{time_info}{health_info}")
    
    # Service endpoints summary
    print(f"\n{'='*50}")
    print("SERVICE ENDPOINTS")
    print("="*50)
    for name, result in results.get("service_endpoints", {}).items():
        status = "✓" if result.get("success") else "✗"
        impl_status = "implemented" if result.get("implemented") else "not implemented"
        time_info = f" ({result.get('response_time', 0):.3f}s)" if result.get("response_time") else ""
        service_status = f" [{result.get('service_status', 'unknown')}]" if result.get("service_status") else ""
        
        print(f"  {status} {name}: {result.get('endpoint', 'N/A')} ({impl_status}){time_info}{service_status}")
    
    # Service dependencies summary
    print(f"\n{'='*50}")
    print("SERVICE DEPENDENCIES")
    print("="*50)
    dep_validation = results.get("service_dependencies", {}).get("dependency_validation", {})
    for service_name, dep_result in dep_validation.items():
        status = "✓" if dep_result.get("dependencies_met") else "✗"
        available = "available" if dep_result.get("service_available") else "unavailable"
        missing_deps = dep_result.get("missing_dependencies", [])
        missing_info = f" (missing: {', '.join(missing_deps)})" if missing_deps else ""
        
        print(f"  {status} {service_name}: {available}{missing_info}")
    
    # Functional endpoints summary
    print(f"\n{'='*50}")
    print("FUNCTIONAL ENDPOINTS")
    print("="*50)
    for name, result in results.get("functional_endpoints", {}).items():
        if "error" in result:
            print(f"  ✗ {name}: Error - {result['error']}")
        else:
            status = "✓" if result.get("success") else "✗"
            time_info = f" ({result.get('response_time', 0):.3f}s)" if result.get("response_time") else ""
            service_info = f" [using {result.get('service_used', 'unknown')}]" if result.get("service_used") else ""
            fallback_info = " (fallback)" if result.get("is_fallback") else ""
            
            print(f"  {status} {name}: {result.get('endpoint', 'N/A')}{time_info}{service_info}{fallback_info}")
    
    # Data flow validation summary
    print(f"\n{'='*50}")
    print("DATA FLOW VALIDATION")
    print("="*50)
    data_flow = results.get("data_flow", {})
    for test_name, test_result in data_flow.items():
        if isinstance(test_result, dict) and "error" not in test_result:
            # Determine success based on test type
            success = False
            details = ""
            
            if test_name == "health_consistency":
                success = test_result.get("status_consistency", False)
                details = f" (status consistency: {success})"
            elif test_name == "service_data_flow":
                success = test_result.get("detailed_available", False) and test_result.get("services_available", False)
                details = f" (detailed: {test_result.get('detailed_available', False)}, services: {test_result.get('services_available', False)})"
            elif test_name == "cross_service_flow":
                success = test_result.get("research_status_available", False)
                details = f" (research status: {success})"
            elif test_name == "error_handling_flow":
                success = test_result.get("invalid_request_handled", False)
                details = f" (error handling: {success})"
            else:
                success = True  # Default to success if no error
            
            status = "✓" if success else "✗"
            print(f"  {status} {test_name}: {'OK' if success else 'Failed'}{details}")
        else:
            print(f"  ✗ {test_name}: {test_result.get('error', 'Failed')}")
    
    # Load testing summary
    print(f"\n{'='*50}")
    print("LOAD TESTING RESULTS")
    print("="*50)
    load_results = results.get("load_testing", {})
    for endpoint_name, load_result in load_results.items():
        success_rate = load_result.get("success_rate", 0)
        rps = load_result.get("requests_per_second", 0)
        performance_grade = load_result.get("performance_grade", "unknown")
        
        perf_stats = load_result.get("performance_stats", {})
        avg_time = perf_stats.get("avg_response_time", 0)
        p95_time = perf_stats.get("p95_response_time", 0)
        
        grade_symbol = {
            "excellent": "🟢",
            "good": "🟡", 
            "acceptable": "🟠",
            "poor": "🔴",
            "unknown": "⚪"
        }.get(performance_grade, "⚪")
        
        print(f"  {grade_symbol} {endpoint_name} ({performance_grade}):")
        print(f"    Success Rate: {success_rate:.1f}%")
        print(f"    Requests/sec: {rps:.1f}")
        print(f"    Avg Response: {avg_time:.3f}s")
        print(f"    P95 Response: {p95_time:.3f}s")
        print(f"    Total Requests: {load_result.get('total_requests', 0)}")
    
    # Stress testing summary (if included)
    if include_stress_test and "stress_testing" in results:
        print(f"\n{'='*50}")
        print("STRESS TESTING RESULTS")
        print("="*50)
        stress_results = results["stress_testing"]
        for level_name, level_result in stress_results.items():
            concurrent = level_result.get("concurrent_requests", 0)
            success_rate = level_result.get("success_rate", 0)
            rps = level_result.get("requests_per_second", 0)
            avg_time = level_result.get("avg_response_time", 0)
            
            print(f"  Level {concurrent} concurrent:")
            print(f"    Success Rate: {success_rate:.1f}%")
            print(f"    Requests/sec: {rps:.1f}")
            print(f"    Avg Response: {avg_time:.3f}s")
    
    # Overall summary
    summary = results.get("summary", {})
    print(f"\n" + "="*100)
    print("COMPREHENSIVE SUMMARY")
    print("="*100)
    
    # Category results
    category_results = summary.get("category_results", {})
    for category, cat_result in category_results.items():
        success_count = cat_result.get("success_count", 0)
        total_count = cat_result.get("total_count", 0)
        success_rate = cat_result.get("success_rate", 0)
        print(f"{category.replace('_', ' ').title()}: {success_count}/{total_count} ({success_rate:.1f}%)")
    
    print(f"\nOverall Endpoint Success Rate: {summary.get('overall_success_rate', 0):.1f}%")
    print(f"Data Flow Success Rate: {summary.get('data_flow_success_rate', 0):.1f}%")
    
    load_assessment = summary.get("load_test_assessment", {})
    print(f"Load Test Grade: {load_assessment.get('overall_grade', 'unknown')}")
    
    # Requirements assessment
    requirements_met = summary.get("requirements_met", {})
    print(f"\nRequirements Assessment:")
    for req_id, met in requirements_met.items():
        status = "✓" if met else "✗"
        req_name = req_id.replace("_", " ").title()
        print(f"  {status} {req_name}")
    
    # Final result
    test_passed = summary.get("test_passed", False)
    result_symbol = "✓ PASSED" if test_passed else "✗ FAILED"
    print(f"\nFinal Result: {result_symbol}")
    print("="*100)
    
    return results


def run_quick_integration_test():
    """Run a quick integration test without stress testing"""
    return run_integration_tests(include_stress_test=False)


def run_full_integration_test():
    """Run full integration test including stress testing"""
    return run_integration_tests(include_stress_test=True)


if __name__ == "__main__":
    run_integration_tests()