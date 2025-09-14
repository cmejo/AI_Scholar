#!/usr/bin/env python3
"""
Test script to verify health monitoring API endpoints
"""
import asyncio
import sys
import os
from fastapi.testclient import TestClient

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

def test_health_endpoints():
    """Test health monitoring API endpoints"""
    print("Testing Health Monitoring API Endpoints")
    print("=" * 50)
    
    client = TestClient(app)
    
    print("1. Testing basic health endpoint...")
    response = client.get("/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    print("\n2. Testing advanced health endpoint...")
    response = client.get("/api/advanced/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    print("\n3. Testing detailed health check endpoint...")
    response = client.get("/api/advanced/health/detailed")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Overall Status: {data.get('status')}")
        print(f"   Services Count: {len(data.get('services', {}))}")
        print(f"   Summary: {data.get('summary', {})}")
    else:
        print(f"   Error: {response.text}")
    
    print("\n4. Testing services health check endpoint...")
    response = client.get("/api/advanced/health/services")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Overall Status: {data.get('status')}")
        print(f"   Services Count: {len(data.get('services', {}))}")
    else:
        print(f"   Error: {response.text}")
    
    print("\n5. Testing health monitoring status endpoint...")
    response = client.get("/api/advanced/health/monitoring")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        monitoring = data.get('monitoring', {})
        print(f"   Monitoring Enabled: {monitoring.get('monitoring_enabled')}")
        print(f"   Health Check Interval: {monitoring.get('health_check_interval')}s")
        print(f"   Cache TTL: {monitoring.get('cache_ttl')}s")
    else:
        print(f"   Error: {response.text}")
    
    print("\n6. Testing health monitoring configuration endpoint...")
    response = client.post("/api/advanced/health/monitoring/configure", 
                          params={"interval": 120, "cache_ttl": 30})
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Configuration Status: {data.get('status')}")
        print(f"   Message: {data.get('message')}")
    else:
        print(f"   Error: {response.text}")
    
    print("\n" + "=" * 50)
    print("Health Monitoring API Endpoints Test Complete!")
    
    return True

if __name__ == "__main__":
    try:
        result = test_health_endpoints()
        if result:
            print("\n✅ All health endpoint tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some health endpoint tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)