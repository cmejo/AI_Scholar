#!/usr/bin/env python3
"""
Test script for production-grade features
Tests rate limiting, monitoring, and structured logging
"""

import requests
import time
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Configuration
BASE_URL = os.environ.get('API_URL', 'http://localhost:5000')
TEST_USERNAME = 'prod_test_user'
TEST_PASSWORD = 'test_password_123'
TEST_EMAIL = 'prod_test@example.com'

class ProductionFeaturesTest:
    def __init__(self):
        self.token = None
        
    def register_and_login(self):
        """Register and login test user"""
        print("🔐 Setting up test user...")
        
        # Try to register
        register_data = {
            'username': TEST_USERNAME,
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD,
            'firstName': 'Production',
            'lastName': 'Test'
        }
        
        response = requests.post(f'{BASE_URL}/api/auth/register', json=register_data)
        
        if response.status_code == 201:
            print("✅ User registered successfully")
            self.token = response.json()['token']
        elif response.status_code == 400 and 'already exists' in response.json().get('message', ''):
            print("ℹ️ User already exists, logging in...")
            # Login instead
            login_data = {
                'username': TEST_USERNAME,
                'password': TEST_PASSWORD
            }
            response = requests.post(f'{BASE_URL}/api/auth/login', json=login_data)
            if response.status_code == 200:
                print("✅ Login successful")
                self.token = response.json()['token']
            else:
                print(f"❌ Login failed: {response.json()}")
                return False
        else:
            print(f"❌ Registration failed: {response.json()}")
            return False
        
        return True
    
    def test_health_check(self):
        """Test enhanced health check endpoint"""
        print("\n🏥 Testing enhanced health check...")
        
        response = requests.get(f'{BASE_URL}/api/health')
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check successful")
            print(f"📊 Status: {data.get('status')}")
            print(f"🗄️ Database: {data.get('database', {}).get('status')}")
            
            features = data.get('features', {})
            print(f"🔒 Rate Limiting: {features.get('rate_limiting')}")
            print(f"📈 Monitoring: {features.get('monitoring')}")
            print(f"📝 Structured Logging: {features.get('structured_logging')}")
            
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    
    def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint"""
        print("\n📊 Testing metrics endpoint...")
        
        response = requests.get(f'{BASE_URL}/metrics')
        
        if response.status_code == 200:
            metrics_data = response.text
            print("✅ Metrics endpoint accessible")
            
            # Check for key metrics
            key_metrics = [
                'http_requests_total',
                'system_cpu_usage_percent',
                'system_memory_usage_percent',
                'application_info'
            ]
            
            found_metrics = []
            for metric in key_metrics:
                if metric in metrics_data:
                    found_metrics.append(metric)
            
            print(f"📈 Found {len(found_metrics)}/{len(key_metrics)} key metrics")
            print(f"📝 Metrics sample: {metrics_data[:200]}...")
            
            return len(found_metrics) > 0
        else:
            print(f"❌ Metrics endpoint failed: {response.status_code}")
            return False
    
    def test_rate_limiting_auth(self):
        """Test rate limiting on authentication endpoints"""
        print("\n🔒 Testing authentication rate limiting...")
        
        # Test login rate limiting
        login_data = {
            'username': 'invalid_user',
            'password': 'invalid_password'
        }
        
        success_count = 0
        rate_limited_count = 0
        
        # Make multiple rapid requests
        for i in range(10):
            response = requests.post(f'{BASE_URL}/api/auth/login', json=login_data)
            
            if response.status_code == 401:
                success_count += 1  # Expected failure
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"🚫 Rate limited after {i + 1} requests")
                break
            
            time.sleep(0.1)  # Small delay
        
        if rate_limited_count > 0:
            print("✅ Authentication rate limiting working")
            return True
        else:
            print("⚠️ Authentication rate limiting not triggered")
            return False
    
    def test_rate_limiting_chat(self):
        """Test rate limiting on chat endpoints"""
        print("\n💬 Testing chat rate limiting...")
        
        if not self.token:
            print("❌ No token available for chat testing")
            return False
        
        headers = {'Authorization': f'Bearer {self.token}'}
        chat_data = {
            'message': 'Test message for rate limiting',
            'model': 'test_model'
        }
        
        success_count = 0
        rate_limited_count = 0
        
        # Make multiple rapid chat requests
        for i in range(35):  # Exceed typical chat limit
            response = requests.post(f'{BASE_URL}/api/chat', json=chat_data, headers=headers)
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"🚫 Chat rate limited after {success_count} successful requests")
                
                # Check rate limit headers
                headers_info = {
                    'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit'),
                    'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining'),
                    'Retry-After': response.headers.get('Retry-After')
                }
                print(f"📊 Rate limit headers: {headers_info}")
                break
            
            time.sleep(0.1)
        
        if rate_limited_count > 0:
            print("✅ Chat rate limiting working")
            return True
        else:
            print("⚠️ Chat rate limiting not triggered")
            return False
    
    def test_concurrent_requests(self):
        """Test system behavior under concurrent load"""
        print("\n🚀 Testing concurrent request handling...")
        
        if not self.token:
            print("❌ No token available for concurrent testing")
            return False
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        def make_request(i):
            chat_data = {
                'message': f'Concurrent test message {i}',
                'model': 'test_model'
            }
            
            start_time = time.time()
            response = requests.post(f'{BASE_URL}/api/chat', json=chat_data, headers=headers)
            duration = time.time() - start_time
            
            return {
                'request_id': i,
                'status_code': response.status_code,
                'duration': duration,
                'success': response.status_code == 200
            }
        
        # Make 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            results = [future.result() for future in futures]
        
        # Analyze results
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        avg_duration = sum(r['duration'] for r in results) / len(results)
        
        print(f"✅ Concurrent requests completed")
        print(f"📊 Successful: {len(successful)}/10")
        print(f"❌ Failed: {len(failed)}/10")
        print(f"⏱️ Average duration: {avg_duration:.3f}s")
        
        return len(successful) > 0
    
    def test_monitoring_status(self):
        """Test monitoring status endpoint"""
        print("\n📈 Testing monitoring status...")
        
        if not self.token:
            print("❌ No token available for monitoring testing")
            return False
        
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(f'{BASE_URL}/api/monitoring/status', headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Monitoring status accessible")
            
            # Check for key sections
            sections = ['health', 'performance', 'rate_limits']
            found_sections = [s for s in sections if s in data]
            
            print(f"📊 Found sections: {found_sections}")
            
            # Show health status
            health = data.get('health', {})
            print(f"🏥 System health: {health.get('status', 'unknown')}")
            print(f"💯 Health score: {health.get('health_score', 0)}")
            
            return len(found_sections) >= 2
        else:
            print(f"❌ Monitoring status failed: {response.status_code}")
            return False
    
    def test_rate_limit_status(self):
        """Test rate limit status endpoint"""
        print("\n🔍 Testing rate limit status...")
        
        if not self.token:
            print("❌ No token available for rate limit testing")
            return False
        
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(f'{BASE_URL}/api/rate-limits', headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Rate limit status accessible")
            
            # Show rate limit info for different endpoints
            for rule_name, rule_info in data.items():
                print(f"🔒 {rule_name}: {rule_info.get('current', 0)}/{rule_info.get('limit', 0)} used")
            
            return True
        else:
            print(f"❌ Rate limit status failed: {response.status_code}")
            return False
    
    def test_security_headers(self):
        """Test security headers in responses"""
        print("\n🛡️ Testing security headers...")
        
        response = requests.get(f'{BASE_URL}/api/health')
        
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Strict-Transport-Security'
        ]
        
        found_headers = []
        for header in security_headers:
            if header in response.headers:
                found_headers.append(header)
                print(f"✅ {header}: {response.headers[header]}")
        
        if len(found_headers) >= 3:
            print("✅ Security headers properly configured")
            return True
        else:
            print(f"⚠️ Only {len(found_headers)}/{len(security_headers)} security headers found")
            return False
    
    def run_all_tests(self):
        """Run all production feature tests"""
        print("🚀 Starting Production Features Test Suite")
        print("=" * 60)
        
        test_results = {}
        
        # Test 1: Health Check
        test_results['health_check'] = self.test_health_check()
        
        # Test 2: Metrics Endpoint
        test_results['metrics'] = self.test_metrics_endpoint()
        
        # Test 3: Security Headers
        test_results['security_headers'] = self.test_security_headers()
        
        # Test 4: Authentication Rate Limiting
        test_results['auth_rate_limiting'] = self.test_rate_limiting_auth()
        
        # Test 5: User Setup
        if self.register_and_login():
            # Test 6: Chat Rate Limiting
            test_results['chat_rate_limiting'] = self.test_rate_limiting_chat()
            
            # Test 7: Concurrent Requests
            test_results['concurrent_requests'] = self.test_concurrent_requests()
            
            # Test 8: Monitoring Status
            test_results['monitoring_status'] = self.test_monitoring_status()
            
            # Test 9: Rate Limit Status
            test_results['rate_limit_status'] = self.test_rate_limit_status()
        else:
            print("❌ User setup failed, skipping authenticated tests")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Results Summary:")
        
        passed = 0
        total = 0
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
            if result:
                passed += 1
            total += 1
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All production features working correctly!")
        elif passed >= total * 0.8:
            print("⚠️ Most production features working, some issues detected")
        else:
            print("❌ Multiple production features have issues")
        
        return passed / total if total > 0 else 0

def main():
    """Main test function"""
    tester = ProductionFeaturesTest()
    
    try:
        success_rate = tester.run_all_tests()
        
        if success_rate >= 0.8:
            print("\n🎊 Production features test completed successfully!")
            return 0
        else:
            print(f"\n⚠️ Production features test completed with issues (success rate: {success_rate:.1%})")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return 1

if __name__ == '__main__':
    exit(main())