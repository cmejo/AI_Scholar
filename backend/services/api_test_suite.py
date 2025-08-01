"""
Comprehensive API endpoint testing suite.
"""
import asyncio
import logging
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import aiohttp
import statistics

from services.test_runner_service import TestResult, TestStatus, TestSeverity
from core.test_config import get_test_config_manager

logger = logging.getLogger(__name__)

class APITestSuite:
    """Comprehensive API endpoint testing suite."""
    
    def __init__(self):
        self.config_manager = get_test_config_manager()
        self.api_config = self.config_manager.api_config
        self.test_results = []
        
        # Define comprehensive endpoint test cases
        self.endpoint_tests = [
            # Health check endpoints
            {
                'name': 'Health Check - Root',
                'method': 'GET',
                'path': '/health',
                'expected_status': [200],
                'timeout': 5,
                'critical': True
            },
            {
                'name': 'Health Check - API',
                'method': 'GET', 
                'path': '/api/health',
                'expected_status': [200, 404],  # May not exist
                'timeout': 5,
                'critical': False
            },
            
            # Research endpoints
            {
                'name': 'Research - Generate Topics',
                'method': 'POST',
                'path': '/api/research/topics/generate',
                'expected_status': [200, 401, 422],
                'timeout': 30,
                'critical': True,
                'requires_auth': True,
                'payload': {
                    'domain': 'Computer Science',
                    'keywords': ['machine learning', 'AI'],
                    'num_topics': 3
                }
            },
            {
                'name': 'Research - Available Methodologies',
                'method': 'GET',
                'path': '/api/research/methodologies',
                'expected_status': [200],
                'timeout': 10,
                'critical': True
            },
            {
                'name': 'Research - Research Domains',
                'method': 'GET',
                'path': '/api/research/domains',
                'expected_status': [200],
                'timeout': 10,
                'critical': True
            },
            
            # Chat endpoints
            {
                'name': 'Chat - Health Check',
                'method': 'GET',
                'path': '/api/chat/health',
                'expected_status': [200],
                'timeout': 10,
                'critical': True
            },
            {
                'name': 'Chat - Research Contexts',
                'method': 'GET',
                'path': '/api/chat/contexts',
                'expected_status': [200],
                'timeout': 10,
                'critical': True
            },
            {
                'name': 'Chat - Start Session',
                'method': 'POST',
                'path': '/api/chat/start',
                'expected_status': [200, 401],
                'timeout': 15,
                'critical': True,
                'requires_auth': True,
                'payload': {
                    'context': 'GENERAL_RESEARCH',
                    'title': 'Test Session'
                }
            },
            
            # Analytics endpoints
            {
                'name': 'Analytics - Health Check',
                'method': 'GET',
                'path': '/api/analytics/health',
                'expected_status': [200],
                'timeout': 10,
                'critical': True
            },
            {
                'name': 'Analytics - Available Visualizations',
                'method': 'GET',
                'path': '/api/analytics/visualizations/available',
                'expected_status': [200],
                'timeout': 10,
                'critical': True
            },
            {
                'name': 'Analytics - Timeframes',
                'method': 'GET',
                'path': '/api/analytics/timeframes',
                'expected_status': [200],
                'timeout': 10,
                'critical': True
            },
            {
                'name': 'Analytics - Metrics Summary',
                'method': 'GET',
                'path': '/api/analytics/metrics/summary',
                'expected_status': [200, 401],
                'timeout': 20,
                'critical': True,
                'requires_auth': True
            },
            
            # Authentication endpoints (if they exist)
            {
                'name': 'Auth - Login (Invalid)',
                'method': 'POST',
                'path': '/api/auth/login',
                'expected_status': [400, 401, 404, 422],
                'timeout': 10,
                'critical': False,
                'payload': {
                    'username': 'invalid_user',
                    'password': 'invalid_password'
                }
            },
            
            # Document endpoints (if they exist)
            {
                'name': 'Documents - List',
                'method': 'GET',
                'path': '/api/documents',
                'expected_status': [200, 401, 404],
                'timeout': 15,
                'critical': False,
                'requires_auth': True
            },
            
            # Monitoring endpoints
            {
                'name': 'Monitoring - System Health',
                'method': 'GET',
                'path': '/api/monitoring/health',
                'expected_status': [200, 404],
                'timeout': 10,
                'critical': False
            },
            {
                'name': 'Monitoring - Metrics',
                'method': 'GET',
                'path': '/api/monitoring/metrics',
                'expected_status': [200, 401, 404],
                'timeout': 15,
                'critical': False
            }
        ]
    
    async def run_all_tests(self) -> List[TestResult]:
        """Run all API endpoint tests."""
        logger.info("Starting comprehensive API endpoint tests")
        self.test_results = []
        
        # Run basic connectivity test first
        connectivity_result = await self._test_basic_connectivity()
        self.test_results.append(connectivity_result)
        
        if connectivity_result.status != TestStatus.PASSED:
            logger.error("Basic connectivity failed, skipping other tests")
            return self.test_results
        
        # Run individual endpoint tests
        for test_config in self.endpoint_tests:
            result = await self._test_endpoint(test_config)
            self.test_results.append(result)
        
        # Run performance tests
        performance_results = await self._run_performance_tests()
        self.test_results.extend(performance_results)
        
        # Run authentication tests
        auth_results = await self._run_authentication_tests()
        self.test_results.extend(auth_results)
        
        # Run error handling tests
        error_results = await self._run_error_handling_tests()
        self.test_results.extend(error_results)
        
        logger.info(f"Completed API endpoint tests: {len(self.test_results)} tests")
        return self.test_results
    
    async def _test_basic_connectivity(self) -> TestResult:
        """Test basic connectivity to the API server."""
        test_name = "API Basic Connectivity"
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Try to connect to the base URL
                async with session.get(self.api_config.base_url) as response:
                    duration = time.time() - start_time
                    
                    # Any response (even 404) indicates connectivity
                    if response.status < 500:
                        return TestResult(
                            test_name=test_name,
                            status=TestStatus.PASSED,
                            duration=duration,
                            metadata={
                                'response_status': response.status,
                                'response_time': duration,
                                'server_header': response.headers.get('Server', 'Unknown')
                            }
                        )
                    else:
                        return TestResult(
                            test_name=test_name,
                            status=TestStatus.FAILED,
                            duration=duration,
                            error_message=f"Server error: {response.status}",
                            severity=TestSeverity.CRITICAL
                        )
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=f"Connection failed: {str(e)}",
                severity=TestSeverity.CRITICAL
            )
    
    async def _test_endpoint(self, test_config: Dict[str, Any]) -> TestResult:
        """Test a specific API endpoint."""
        test_name = test_config['name']
        start_time = time.time()
        
        try:
            # Prepare request
            url = f"{self.api_config.base_url}{test_config['path']}"
            method = test_config['method']
            timeout = aiohttp.ClientTimeout(total=test_config.get('timeout', 30))
            
            # Prepare headers
            headers = dict(self.api_config.headers)
            if test_config.get('requires_auth') and self.api_config.auth_token:
                headers['Authorization'] = f"Bearer {self.api_config.auth_token}"
            
            # Prepare payload
            payload = test_config.get('payload')
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Make request
                if method.upper() == 'GET':
                    async with session.get(url, headers=headers) as response:
                        return await self._process_response(test_config, response, start_time)
                elif method.upper() == 'POST':
                    async with session.post(url, headers=headers, json=payload) as response:
                        return await self._process_response(test_config, response, start_time)
                elif method.upper() == 'PUT':
                    async with session.put(url, headers=headers, json=payload) as response:
                        return await self._process_response(test_config, response, start_time)
                elif method.upper() == 'DELETE':
                    async with session.delete(url, headers=headers) as response:
                        return await self._process_response(test_config, response, start_time)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
        
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                duration=duration,
                error_message=f"Request timed out after {test_config.get('timeout', 30)}s",
                severity=TestSeverity.HIGH if test_config.get('critical') else TestSeverity.MEDIUM
            )
        
        except Exception as e:
            duration = time.time() - start_time
            severity = TestSeverity.HIGH if test_config.get('critical') else TestSeverity.MEDIUM
            
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e),
                severity=severity
            )
    
    async def _process_response(self, test_config: Dict[str, Any], 
                              response: aiohttp.ClientResponse, 
                              start_time: float) -> TestResult:
        """Process HTTP response and create test result."""
        test_name = test_config['name']
        duration = time.time() - start_time
        expected_status = test_config['expected_status']
        
        # Check status code
        status_ok = response.status in expected_status
        
        # Read response content (with size limit)
        try:
            content_length = int(response.headers.get('Content-Length', 0))
            if content_length > 1024 * 1024:  # 1MB limit
                response_text = "Response too large to read"
                response_json = None
            else:
                response_text = await response.text()
                try:
                    response_json = await response.json() if response_text else None
                except:
                    response_json = None
        except Exception:
            response_text = "Failed to read response"
            response_json = None
        
        # Prepare metadata
        metadata = {
            'response_status': response.status,
            'response_time': duration,
            'content_type': response.headers.get('Content-Type', 'Unknown'),
            'content_length': response.headers.get('Content-Length', 'Unknown'),
            'expected_status': expected_status
        }
        
        # Add response data if it's JSON and not too large
        if response_json and len(str(response_json)) < 1000:
            metadata['response_sample'] = response_json
        
        # Determine test result
        if status_ok:
            # Additional validation for successful responses
            validation_result = await self._validate_response_content(
                test_config, response.status, response_json, response_text
            )
            
            if validation_result['valid']:
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    duration=duration,
                    metadata=metadata
                )
            else:
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.FAILED,
                    duration=duration,
                    error_message=validation_result['error'],
                    metadata=metadata,
                    severity=TestSeverity.MEDIUM
                )
        else:
            severity = TestSeverity.HIGH if test_config.get('critical') else TestSeverity.MEDIUM
            return TestResult(
                test_name=test_name,
                status=TestStatus.FAILED,
                duration=duration,
                error_message=f"Expected status {expected_status}, got {response.status}",
                metadata=metadata,
                severity=severity
            )
    
    async def _validate_response_content(self, test_config: Dict[str, Any], 
                                       status_code: int, response_json: Any, 
                                       response_text: str) -> Dict[str, Any]:
        """Validate response content based on endpoint expectations."""
        endpoint_path = test_config['path']
        
        # Skip validation for non-200 responses
        if status_code != 200:
            return {'valid': True}
        
        try:
            # Health check endpoints should return status
            if '/health' in endpoint_path:
                if response_json and 'status' in response_json:
                    return {'valid': True}
                else:
                    return {'valid': False, 'error': 'Health endpoint missing status field'}
            
            # List endpoints should return arrays
            elif any(path in endpoint_path for path in ['/methodologies', '/domains', '/contexts', '/timeframes']):
                if isinstance(response_json, list):
                    return {'valid': True}
                else:
                    return {'valid': False, 'error': 'List endpoint should return array'}
            
            # Metrics endpoints should return metrics data
            elif '/metrics' in endpoint_path:
                if response_json and (isinstance(response_json, dict) or isinstance(response_json, list)):
                    return {'valid': True}
                else:
                    return {'valid': False, 'error': 'Metrics endpoint should return structured data'}
            
            # Default validation - just check if response is not empty for 200 status
            else:
                if response_text and len(response_text.strip()) > 0:
                    return {'valid': True}
                else:
                    return {'valid': False, 'error': 'Empty response for successful request'}
        
        except Exception as e:
            return {'valid': False, 'error': f'Validation error: {str(e)}'}
    
    async def _run_performance_tests(self) -> List[TestResult]:
        """Run API performance tests."""
        logger.info("Running API performance tests")
        performance_tests = []
        
        # Test response time under load
        load_test_result = await self._test_response_time_under_load()
        performance_tests.append(load_test_result)
        
        # Test concurrent requests
        concurrent_test_result = await self._test_concurrent_requests()
        performance_tests.append(concurrent_test_result)
        
        # Test large payload handling
        payload_test_result = await self._test_large_payload_handling()
        performance_tests.append(payload_test_result)
        
        return performance_tests
    
    async def _test_response_time_under_load(self) -> TestResult:
        """Test API response times under load."""
        test_name = "API Response Time Under Load"
        start_time = time.time()
        
        try:
            # Test with multiple sequential requests to health endpoint
            response_times = []
            errors = 0
            
            for i in range(10):
                request_start = time.time()
                try:
                    timeout = aiohttp.ClientTimeout(total=10)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(f"{self.api_config.base_url}/health") as response:
                            request_time = time.time() - request_start
                            response_times.append(request_time)
                            
                            if response.status >= 500:
                                errors += 1
                
                except Exception:
                    errors += 1
                    request_time = time.time() - request_start
                    response_times.append(request_time)
            
            duration = time.time() - start_time
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                max_response_time = max(response_times)
                
                # Check if performance is acceptable
                if avg_response_time < 2.0 and max_response_time < 5.0 and errors == 0:
                    return TestResult(
                        test_name=test_name,
                        status=TestStatus.PASSED,
                        duration=duration,
                        metadata={
                            'average_response_time': avg_response_time,
                            'max_response_time': max_response_time,
                            'total_requests': len(response_times),
                            'errors': errors
                        }
                    )
                else:
                    return TestResult(
                        test_name=test_name,
                        status=TestStatus.FAILED,
                        duration=duration,
                        error_message=f"Performance degraded: avg={avg_response_time:.2f}s, max={max_response_time:.2f}s, errors={errors}",
                        metadata={
                            'average_response_time': avg_response_time,
                            'max_response_time': max_response_time,
                            'total_requests': len(response_times),
                            'errors': errors
                        }
                    )
            else:
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.ERROR,
                    duration=duration,
                    error_message="No response times recorded"
                )
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e)
            )
    
    async def _test_concurrent_requests(self) -> TestResult:
        """Test handling of concurrent requests."""
        test_name = "API Concurrent Requests"
        start_time = time.time()
        
        try:
            # Create multiple concurrent requests
            async def make_request():
                try:
                    timeout = aiohttp.ClientTimeout(total=15)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(f"{self.api_config.base_url}/health") as response:
                            return {'status': response.status, 'success': True}
                except Exception as e:
                    return {'status': 0, 'success': False, 'error': str(e)}
            
            # Run 5 concurrent requests
            tasks = [make_request() for _ in range(5)]
            results = await asyncio.gather(*tasks)
            
            duration = time.time() - start_time
            
            successful_requests = sum(1 for r in results if r['success'])
            failed_requests = len(results) - successful_requests
            
            if successful_requests >= 4:  # Allow 1 failure
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.PASSED,
                    duration=duration,
                    metadata={
                        'total_requests': len(results),
                        'successful_requests': successful_requests,
                        'failed_requests': failed_requests,
                        'success_rate': successful_requests / len(results)
                    }
                )
            else:
                return TestResult(
                    test_name=test_name,
                    status=TestStatus.FAILED,
                    duration=duration,
                    error_message=f"Too many concurrent request failures: {failed_requests}/{len(results)}",
                    metadata={
                        'total_requests': len(results),
                        'successful_requests': successful_requests,
                        'failed_requests': failed_requests
                    }
                )
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e)
            )
    
    async def _test_large_payload_handling(self) -> TestResult:
        """Test handling of large payloads."""
        test_name = "API Large Payload Handling"
        start_time = time.time()
        
        try:
            # Create a moderately large payload
            large_payload = {
                'data': 'x' * 10000,  # 10KB string
                'array': list(range(1000)),
                'nested': {
                    'field1': 'value1' * 100,
                    'field2': 'value2' * 100,
                    'field3': list(range(100))
                }
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Try to POST to a research endpoint that might accept large payloads
                url = f"{self.api_config.base_url}/api/research/topics/generate"
                headers = dict(self.api_config.headers)
                
                async with session.post(url, headers=headers, json=large_payload) as response:
                    duration = time.time() - start_time
                    
                    # We expect this to fail with 401 (auth) or 422 (validation)
                    # but not with 413 (payload too large) or 500 (server error)
                    if response.status in [401, 422, 400]:
                        return TestResult(
                            test_name=test_name,
                            status=TestStatus.PASSED,
                            duration=duration,
                            metadata={
                                'response_status': response.status,
                                'payload_size_bytes': len(json.dumps(large_payload))
                            }
                        )
                    elif response.status == 413:
                        return TestResult(
                            test_name=test_name,
                            status=TestStatus.FAILED,
                            duration=duration,
                            error_message="Server rejected payload as too large",
                            metadata={'response_status': response.status}
                        )
                    elif response.status >= 500:
                        return TestResult(
                            test_name=test_name,
                            status=TestStatus.FAILED,
                            duration=duration,
                            error_message=f"Server error handling large payload: {response.status}",
                            metadata={'response_status': response.status}
                        )
                    else:
                        # Unexpected success
                        return TestResult(
                            test_name=test_name,
                            status=TestStatus.PASSED,
                            duration=duration,
                            metadata={
                                'response_status': response.status,
                                'payload_size_bytes': len(json.dumps(large_payload)),
                                'note': 'Unexpected success - payload was processed'
                            }
                        )
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e)
            )
    
    async def _run_authentication_tests(self) -> List[TestResult]:
        """Run authentication-related tests."""
        logger.info("Running API authentication tests")
        auth_tests = []
        
        # Test protected endpoint without auth
        no_auth_test = await self._test_protected_endpoint_without_auth()
        auth_tests.append(no_auth_test)
        
        # Test invalid auth token
        invalid_auth_test = await self._test_invalid_auth_token()
        auth_tests.append(invalid_auth_test)
        
        return auth_tests
    
    async def _test_protected_endpoint_without_auth(self) -> TestResult:
        """Test accessing protected endpoint without authentication."""
        test_name = "Protected Endpoint Without Auth"
        start_time = time.time()
        
        try:
            # Try to access a protected endpoint without auth header
            url = f"{self.api_config.base_url}/api/research/topics/generate"
            payload = {'domain': 'test', 'num_topics': 1}
            
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Don't include auth header
                headers = {'Content-Type': 'application/json'}
                
                async with session.post(url, headers=headers, json=payload) as response:
                    duration = time.time() - start_time
                    
                    # Should return 401 Unauthorized
                    if response.status == 401:
                        return TestResult(
                            test_name=test_name,
                            status=TestStatus.PASSED,
                            duration=duration,
                            metadata={'response_status': response.status}
                        )
                    else:
                        return TestResult(
                            test_name=test_name,
                            status=TestStatus.FAILED,
                            duration=duration,
                            error_message=f"Expected 401, got {response.status}",
                            metadata={'response_status': response.status}
                        )
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e)
            )
    
    async def _test_invalid_auth_token(self) -> TestResult:
        """Test using invalid authentication token."""
        test_name = "Invalid Auth Token"
        start_time = time.time()
        
        try:
            url = f"{self.api_config.base_url}/api/research/topics/generate"
            payload = {'domain': 'test', 'num_topics': 1}
            
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Use invalid auth token
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer invalid_token_12345'
                }
                
                async with session.post(url, headers=headers, json=payload) as response:
                    duration = time.time() - start_time
                    
                    # Should return 401 Unauthorized
                    if response.status == 401:
                        return TestResult(
                            test_name=test_name,
                            status=TestStatus.PASSED,
                            duration=duration,
                            metadata={'response_status': response.status}
                        )
                    else:
                        return TestResult(
                            test_name=test_name,
                            status=TestStatus.FAILED,
                            duration=duration,
                            error_message=f"Expected 401, got {response.status}",
                            metadata={'response_status': response.status}
                        )
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e)
            )
    
    async def _run_error_handling_tests(self) -> List[TestResult]:
        """Run error handling tests."""
        logger.info("Running API error handling tests")
        error_tests = []
        
        # Test malformed JSON
        malformed_json_test = await self._test_malformed_json()
        error_tests.append(malformed_json_test)
        
        # Test invalid endpoint
        invalid_endpoint_test = await self._test_invalid_endpoint()
        error_tests.append(invalid_endpoint_test)
        
        # Test invalid HTTP method
        invalid_method_test = await self._test_invalid_http_method()
        error_tests.append(invalid_method_test)
        
        return error_tests
    
    async def _test_malformed_json(self) -> TestResult:
        """Test handling of malformed JSON."""
        test_name = "Malformed JSON Handling"
        start_time = time.time()
        
        try:
            url = f"{self.api_config.base_url}/api/research/topics/generate"
            malformed_json = '{"domain": "test", "num_topics": }'  # Invalid JSON
            
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {'Content-Type': 'application/json'}
                
                async with session.post(url, headers=headers, data=malformed_json) as response:
                    duration = time.time() - start_time
                    
                    # Should return 400 Bad Request or 422 Unprocessable Entity
                    if response.status in [400, 422]:
                        return TestResult(
                            test_name=test_name,
                            status=TestStatus.PASSED,
                            duration=duration,
                            metadata={'response_status': response.status}
                        )
                    else:
                        return TestResult(
                            test_name=test_name,
                            status=TestStatus.FAILED,
                            duration=duration,
                            error_message=f"Expected 400 or 422, got {response.status}",
                            metadata={'response_status': response.status}
                        )
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e)
            )
    
    async def _test_invalid_endpoint(self) -> TestResult:
        """Test accessing invalid endpoint."""
        test_name = "Invalid Endpoint"
        start_time = time.time()
        
        try:
            url = f"{self.api_config.base_url}/api/nonexistent/endpoint"
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    duration = time.time() - start_time
                    
                    # Should return 404 Not Found
                    if response.status == 404:
                        return TestResult(
                            test_name=test_name,
                            status=TestStatus.PASSED,
                            duration=duration,
                            metadata={'response_status': response.status}
                        )
                    else:
                        return TestResult(
                            test_name=test_name,
                            status=TestStatus.FAILED,
                            duration=duration,
                            error_message=f"Expected 404, got {response.status}",
                            metadata={'response_status': response.status}
                        )
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e)
            )
    
    async def _test_invalid_http_method(self) -> TestResult:
        """Test using invalid HTTP method."""
        test_name = "Invalid HTTP Method"
        start_time = time.time()
        
        try:
            # Try PATCH on an endpoint that only supports GET
            url = f"{self.api_config.base_url}/api/research/domains"
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.patch(url) as response:
                    duration = time.time() - start_time
                    
                    # Should return 405 Method Not Allowed
                    if response.status == 405:
                        return TestResult(
                            test_name=test_name,
                            status=TestStatus.PASSED,
                            duration=duration,
                            metadata={'response_status': response.status}
                        )
                    else:
                        return TestResult(
                            test_name=test_name,
                            status=TestStatus.FAILED,
                            duration=duration,
                            error_message=f"Expected 405, got {response.status}",
                            metadata={'response_status': response.status}
                        )
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                error_message=str(e)
            )
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of test results."""
        if not self.test_results:
            return {'error': 'No tests have been run'}
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t.status == TestStatus.PASSED)
        failed_tests = sum(1 for t in self.test_results if t.status == TestStatus.FAILED)
        error_tests = sum(1 for t in self.test_results if t.status == TestStatus.ERROR)
        
        # Calculate performance metrics
        durations = [t.duration for t in self.test_results if t.duration]
        avg_duration = statistics.mean(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        
        # Identify critical failures
        critical_failures = [
            t for t in self.test_results 
            if t.status in [TestStatus.FAILED, TestStatus.ERROR] and 
            t.severity in [TestSeverity.HIGH, TestSeverity.CRITICAL]
        ]
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'error_tests': error_tests,
            'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'average_duration': avg_duration,
            'max_duration': max_duration,
            'critical_failures': len(critical_failures),
            'critical_failure_details': [
                {'test_name': t.test_name, 'error': t.error_message}
                for t in critical_failures
            ]
        }

# Global instance
api_test_suite = APITestSuite()

def get_api_test_suite() -> APITestSuite:
    """Get the global API test suite instance."""
    return api_test_suite