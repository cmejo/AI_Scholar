#!/usr/bin/env python3
"""
Comprehensive Container Startup Validation Script
Tests container startup with all services restored
"""

import requests
import subprocess
import json
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

def test_container_health():
    """Test container health endpoints with comprehensive service validation"""
    print("Testing Container Health Endpoints...")
    print("-" * 50)
    
    endpoints = [
        "/health",
        "/api/advanced/health",
        "/api/advanced/health/detailed",
        "/api/advanced/health/services"
    ]
    
    base_url = "http://localhost:8000"
    results = {}
    
    for endpoint in endpoints:
        try:
            print(f"Testing {endpoint}...")
            start_time = time.time()
            response = requests.get(f"{base_url}{endpoint}", timeout=15)
            response_time = time.time() - start_time
            
            results[endpoint] = {
                "status_code": response.status_code,
                "response_time": response_time,
                "healthy": response.status_code == 200
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    results[endpoint]["data"] = data
                    
                    # Extract service information for detailed endpoints
                    if endpoint == "/api/advanced/health/detailed":
                        services = data.get("services", {})
                        print(f"  ✓ {endpoint}: OK ({response_time:.2f}s) - {len(services)} services")
                        for service_name, service_info in services.items():
                            status = service_info.get("status", "unknown")
                            print(f"    - {service_name}: {status}")
                    elif endpoint == "/api/advanced/health/services":
                        services = data.get("services", {})
                        print(f"  ✓ {endpoint}: OK ({response_time:.2f}s) - {len(services)} services")
                        for service_name, service_info in services.items():
                            status = service_info.get("status", "unknown")
                            last_check = service_info.get("last_check", "unknown")
                            print(f"    - {service_name}: {status} (checked: {last_check})")
                    else:
                        print(f"  ✓ {endpoint}: OK ({response_time:.2f}s)")
                        
                except Exception as e:
                    print(f"  ✓ {endpoint}: OK (JSON parse error: {e})")
            else:
                print(f"  ✗ {endpoint}: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"    Error: {error_data.get('detail', 'No error details')}")
                except:
                    print(f"    Error: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            results[endpoint] = {
                "healthy": False,
                "error": "Request timeout"
            }
            print(f"  ✗ {endpoint}: TIMEOUT (>15s)")
        except requests.exceptions.ConnectionError:
            results[endpoint] = {
                "healthy": False,
                "error": "Connection error"
            }
            print(f"  ✗ {endpoint}: CONNECTION ERROR")
        except Exception as e:
            results[endpoint] = {
                "healthy": False,
                "error": str(e)
            }
            print(f"  ✗ {endpoint}: ERROR - {e}")
    
    return results

def test_container_stats():
    """Test container resource usage with detailed monitoring"""
    print("\nTesting Container Resource Usage...")
    print("-" * 50)
    
    try:
        # Get container ID
        result = subprocess.run(
            ["docker", "ps", "-q", "--filter", "name=advanced-rag-backend"],
            capture_output=True, text=True, check=True
        )
        container_id = result.stdout.strip()
        
        if not container_id:
            print("  ✗ Container not found")
            return None
        
        print(f"  Container ID: {container_id[:12]}")
        
        # Get container stats multiple times for average
        stats_samples = []
        for i in range(3):
            try:
                result = subprocess.run(
                    ["docker", "stats", "--no-stream", "--format", "json", container_id],
                    capture_output=True, text=True, check=True, timeout=10
                )
                stats = json.loads(result.stdout.strip())
                stats_samples.append(stats)
                if i < 2:  # Don't sleep after last sample
                    time.sleep(2)
            except Exception as e:
                print(f"  ⚠ Error getting stats sample {i+1}: {e}")
        
        if not stats_samples:
            print("  ✗ No stats samples collected")
            return None
        
        # Calculate averages
        cpu_percents = []
        memory_percents = []
        
        for stats in stats_samples:
            try:
                cpu_percent = float(stats.get("CPUPerc", "0%").replace("%", ""))
                memory_percent = float(stats.get("MemPerc", "0%").replace("%", ""))
                cpu_percents.append(cpu_percent)
                memory_percents.append(memory_percent)
            except ValueError:
                continue
        
        if cpu_percents and memory_percents:
            avg_cpu = sum(cpu_percents) / len(cpu_percents)
            avg_memory = sum(memory_percents) / len(memory_percents)
            max_cpu = max(cpu_percents)
            max_memory = max(memory_percents)
        else:
            avg_cpu = avg_memory = max_cpu = max_memory = 0
        
        # Use latest stats for other metrics
        latest_stats = stats_samples[-1]
        
        print(f"  CPU Usage (avg): {avg_cpu:.2f}% (max: {max_cpu:.2f}%)")
        print(f"  Memory Usage (avg): {avg_memory:.2f}% (max: {max_memory:.2f}%)")
        print(f"  Memory: {latest_stats.get('MemUsage', 'N/A')}")
        print(f"  Network I/O: {latest_stats.get('NetIO', 'N/A')}")
        print(f"  Block I/O: {latest_stats.get('BlockIO', 'N/A')}")
        print(f"  PIDs: {latest_stats.get('PIDs', 'N/A')}")
        
        # Resource usage assessment
        if avg_cpu < 50 and avg_memory < 70:
            print("  ✓ Resource usage within optimal limits")
        elif avg_cpu < 80 and avg_memory < 85:
            print("  ⚠ Resource usage within acceptable limits")
        else:
            print("  ✗ High resource usage detected")
        
        return {
            "cpu_percent_avg": avg_cpu,
            "cpu_percent_max": max_cpu,
            "memory_percent_avg": avg_memory,
            "memory_percent_max": max_memory,
            "memory_usage": latest_stats.get("MemUsage"),
            "network_io": latest_stats.get("NetIO"),
            "block_io": latest_stats.get("BlockIO"),
            "pids": latest_stats.get("PIDs"),
            "samples_count": len(stats_samples)
        }
        
    except Exception as e:
        print(f"  ✗ Error getting container stats: {e}")
        return None

def test_container_logs():
    """Test container logs for errors"""
    print("\nAnalyzing Container Logs...")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", "50", "advanced-rag-backend"],
            capture_output=True, text=True, check=True
        )
        
        logs = result.stdout + result.stderr
        lines = logs.split('\n')
        
        error_lines = [line for line in lines if 'ERROR' in line.upper()]
        warning_lines = [line for line in lines if 'WARNING' in line.upper()]
        
        print(f"  Total log lines analyzed: {len(lines)}")
        print(f"  Error lines: {len(error_lines)}")
        print(f"  Warning lines: {len(warning_lines)}")
        
        if error_lines:
            print("  Recent errors:")
            for error in error_lines[-3:]:  # Show last 3 errors
                print(f"    {error.strip()}")
        
        if len(error_lines) < 5:
            print("  ✓ Low error count in logs")
        else:
            print("  ⚠ High error count in logs")
        
        return {
            "total_lines": len(lines),
            "error_count": len(error_lines),
            "warning_count": len(warning_lines),
            "recent_errors": error_lines[-3:] if error_lines else []
        }
        
    except Exception as e:
        print(f"  ✗ Error analyzing logs: {e}")
        return None

def test_service_endpoints():
    """Test specific service endpoints to validate functionality"""
    print("\nTesting Service Endpoints...")
    print("-" * 50)
    
    base_url = "http://localhost:8000"
    service_endpoints = [
        # Research endpoints
        ("/api/advanced/research/search", "POST", {"query": "test search", "limit": 5}),
        ("/api/advanced/research/hypotheses", "POST", {"research_area": "AI", "user_id": "test"}),
        
        # Analytics endpoints
        ("/api/advanced/analytics/user-behavior", "GET", None),
        ("/api/advanced/analytics/feature-performance", "GET", None),
        ("/api/advanced/analytics/business-intelligence", "GET", None),
        
        # Knowledge graph endpoints
        ("/api/advanced/knowledge-graph/entities", "GET", None),
        ("/api/advanced/knowledge-graph/query", "POST", {"entity_name": "test"}),
    ]
    
    results = {}
    
    for endpoint, method, payload in service_endpoints:
        try:
            print(f"Testing {method} {endpoint}...")
            start_time = time.time()
            
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
            elif method == "POST":
                response = requests.post(f"{base_url}{endpoint}", json=payload, timeout=10)
            else:
                continue
            
            response_time = time.time() - start_time
            
            results[endpoint] = {
                "method": method,
                "status_code": response.status_code,
                "response_time": response_time,
                "healthy": response.status_code in [200, 201, 422]  # 422 is acceptable for validation errors
            }
            
            if response.status_code in [200, 201]:
                print(f"  ✓ {endpoint}: OK ({response_time:.2f}s)")
            elif response.status_code == 422:
                print(f"  ⚠ {endpoint}: Validation error (expected) ({response_time:.2f}s)")
            elif response.status_code == 503:
                print(f"  ⚠ {endpoint}: Service unavailable ({response_time:.2f}s)")
            else:
                print(f"  ✗ {endpoint}: HTTP {response.status_code} ({response_time:.2f}s)")
                
        except requests.exceptions.Timeout:
            results[endpoint] = {"healthy": False, "error": "timeout"}
            print(f"  ✗ {endpoint}: TIMEOUT")
        except Exception as e:
            results[endpoint] = {"healthy": False, "error": str(e)}
            print(f"  ✗ {endpoint}: ERROR - {e}")
    
    return results

def monitor_startup_time():
    """Monitor container startup time and readiness"""
    print("\nMonitoring Container Startup Time...")
    print("-" * 50)
    
    try:
        # Get container start time
        result = subprocess.run(
            ["docker", "inspect", "advanced-rag-backend", "--format", "{{.State.StartedAt}}"],
            capture_output=True, text=True, check=True
        )
        start_time_str = result.stdout.strip()
        
        if not start_time_str:
            print("  ✗ Could not get container start time")
            return None
        
        # Parse start time (Docker returns RFC3339 format)
        try:
            from dateutil import parser
            start_time = parser.parse(start_time_str)
        except ImportError:
            # Fallback parsing for basic ISO format
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        
        current_time = datetime.now(start_time.tzinfo)
        uptime = (current_time - start_time).total_seconds()
        
        print(f"  Container started: {start_time_str}")
        print(f"  Current uptime: {uptime:.1f} seconds")
        
        # Test readiness by checking health endpoint
        base_url = "http://localhost:8000"
        readiness_start = time.time()
        max_wait = 60  # Maximum wait time for readiness
        
        while time.time() - readiness_start < max_wait:
            try:
                response = requests.get(f"{base_url}/health", timeout=5)
                if response.status_code == 200:
                    readiness_time = time.time() - readiness_start
                    print(f"  ✓ Container ready in {readiness_time:.1f} seconds")
                    
                    return {
                        "start_time": start_time_str,
                        "uptime_seconds": uptime,
                        "readiness_time": readiness_time,
                        "ready": True
                    }
            except:
                time.sleep(1)
                continue
        
        print(f"  ✗ Container not ready after {max_wait} seconds")
        return {
            "start_time": start_time_str,
            "uptime_seconds": uptime,
            "readiness_time": None,
            "ready": False
        }
        
    except Exception as e:
        print(f"  ✗ Error monitoring startup time: {e}")
        return None

def test_all_services_health():
    """Test health of all individual services"""
    print("\nTesting Individual Service Health...")
    print("-" * 50)
    
    base_url = "http://localhost:8000"
    
    try:
        # Get detailed health information
        response = requests.get(f"{base_url}/api/advanced/health/detailed", timeout=15)
        
        if response.status_code != 200:
            print(f"  ✗ Could not get service health: HTTP {response.status_code}")
            return {}
        
        data = response.json()
        services = data.get("services", {})
        
        print(f"  Found {len(services)} services")
        
        service_results = {}
        for service_name, service_info in services.items():
            status = service_info.get("status", "unknown")
            error_msg = service_info.get("error_message")
            service_type = service_info.get("type", "unknown")
            
            service_results[service_name] = {
                "status": status,
                "type": service_type,
                "healthy": status in ["healthy", "mock"],
                "error_message": error_msg
            }
            
            if status == "healthy":
                print(f"  ✓ {service_name}: {status}")
            elif status == "mock":
                print(f"  ⚠ {service_name}: {status} (fallback service)")
            else:
                print(f"  ✗ {service_name}: {status}")
                if error_msg:
                    print(f"    Error: {error_msg}")
        
        return service_results
        
    except Exception as e:
        print(f"  ✗ Error testing service health: {e}")
        return {}

def main():
    """Run comprehensive container startup validation"""
    print("=" * 70)
    print("COMPREHENSIVE CONTAINER STARTUP VALIDATION")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Monitor startup time
    startup_results = monitor_startup_time()
    
    # Test health endpoints
    health_results = test_container_health()
    
    # Test individual services
    service_results = test_all_services_health()
    
    # Test service endpoints
    endpoint_results = test_service_endpoints()
    
    # Test container stats
    stats_results = test_container_stats()
    
    # Test container logs
    log_results = test_container_logs()
    
    # Summary
    print("\n" + "=" * 70)
    print("COMPREHENSIVE VALIDATION SUMMARY")
    print("=" * 70)
    
    # Startup summary
    if startup_results:
        print(f"Container Uptime: {startup_results['uptime_seconds']:.1f}s")
        if startup_results['ready']:
            print(f"Readiness Time: {startup_results['readiness_time']:.1f}s")
        else:
            print("Readiness: NOT READY")
    
    # Health summary
    healthy_endpoints = sum(1 for r in health_results.values() if r.get("healthy", False))
    total_endpoints = len(health_results)
    health_score = (healthy_endpoints / total_endpoints) * 100 if total_endpoints > 0 else 0
    print(f"Health Endpoints: {healthy_endpoints}/{total_endpoints} ({health_score:.1f}%)")
    
    # Service summary
    if service_results:
        healthy_services = sum(1 for s in service_results.values() if s.get("healthy", False))
        total_services = len(service_results)
        service_score = (healthy_services / total_services) * 100 if total_services > 0 else 0
        print(f"Services Health: {healthy_services}/{total_services} ({service_score:.1f}%)")
    
    # Endpoint summary
    if endpoint_results:
        healthy_endpoints_svc = sum(1 for r in endpoint_results.values() if r.get("healthy", False))
        total_endpoints_svc = len(endpoint_results)
        endpoint_score = (healthy_endpoints_svc / total_endpoints_svc) * 100 if total_endpoints_svc > 0 else 0
        print(f"Service Endpoints: {healthy_endpoints_svc}/{total_endpoints_svc} ({endpoint_score:.1f}%)")
    
    # Resource summary
    if stats_results:
        print(f"CPU Usage: {stats_results['cpu_percent_avg']:.1f}% (max: {stats_results['cpu_percent_max']:.1f}%)")
        print(f"Memory Usage: {stats_results['memory_percent_avg']:.1f}% (max: {stats_results['memory_percent_max']:.1f}%)")
    
    # Log summary
    if log_results:
        print(f"Log Errors: {log_results['error_count']}")
        print(f"Log Warnings: {log_results['warning_count']}")
    
    # Overall assessment
    overall_healthy = (
        health_score >= 75 and
        (not service_results or (sum(1 for s in service_results.values() if s.get("healthy", False)) / len(service_results)) >= 0.8) and
        (not stats_results or (stats_results['cpu_percent_avg'] < 70 and stats_results['memory_percent_avg'] < 80)) and
        (not log_results or log_results['error_count'] < 5) and
        (not startup_results or startup_results['ready'])
    )
    
    print(f"\nOverall Status: {'✓ HEALTHY' if overall_healthy else '⚠ NEEDS ATTENTION'}")
    print("=" * 70)
    
    # Detailed recommendations
    if not overall_healthy:
        print("\nRecommendations:")
        if health_score < 75:
            print("- Check health endpoint implementations")
        if service_results and (sum(1 for s in service_results.values() if s.get("healthy", False)) / len(service_results)) < 0.8:
            print("- Review service initialization and dependencies")
        if stats_results and (stats_results['cpu_percent_avg'] >= 70 or stats_results['memory_percent_avg'] >= 80):
            print("- Monitor resource usage and optimize if needed")
        if log_results and log_results['error_count'] >= 5:
            print("- Review container logs for errors")
        if startup_results and not startup_results['ready']:
            print("- Check container startup process")
    
    return overall_healthy

if __name__ == "__main__":
    main()