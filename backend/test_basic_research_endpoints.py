#!/usr/bin/env python3
"""
Simple test script for basic research endpoints
Tests the research endpoints without requiring pytest
"""
import sys
import os
import asyncio
import json
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_research_endpoints():
    """Test the basic research endpoints"""
    print("Testing Basic Research Endpoints")
    print("=" * 50)
    
    try:
        # Import the required modules
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from api.advanced_endpoints import router
        
        # Create a test FastAPI app
        app = FastAPI()
        app.include_router(router)
        
        # Create test client
        client = TestClient(app)
        
        # Test 1: Research Status Endpoint
        print("\n1. Testing /api/advanced/research/status")
        try:
            response = client.get("/api/advanced/research/status")
            print(f"   Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response Status: {data.get('status')}")
                print(f"   Services Count: {len(data.get('services', {}))}")
                print("   ✅ Research status endpoint working")
            else:
                print(f"   ❌ Unexpected status code: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Error testing research status: {str(e)}")
        
        # Test 2: Research Capabilities Endpoint
        print("\n2. Testing /api/advanced/research/capabilities")
        try:
            response = client.get("/api/advanced/research/capabilities")
            print(f"   Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response Status: {data.get('status')}")
                capabilities = data.get('capabilities', {})
                print(f"   Capabilities Count: {len(capabilities)}")
                for cap_name, cap_info in capabilities.items():
                    print(f"     - {cap_name}: {cap_info.get('status', 'unknown')}")
                print("   ✅ Research capabilities endpoint working")
            else:
                print(f"   ❌ Unexpected status code: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Error testing research capabilities: {str(e)}")
        
        # Test 3: Research Domains Endpoint
        print("\n3. Testing /api/advanced/research/domains")
        try:
            response = client.get("/api/advanced/research/domains")
            print(f"   Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response Status: {data.get('status')}")
                domains = data.get('domains', {})
                print(f"   Domains Count: {len(domains)}")
                for domain_name in domains.keys():
                    print(f"     - {domain_name}")
                print("   ✅ Research domains endpoint working")
            else:
                print(f"   ❌ Unexpected status code: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Error testing research domains: {str(e)}")
        
        # Test 4: Basic Research Search Endpoint
        print("\n4. Testing /api/advanced/research/search/basic")
        try:
            search_request = {
                "query": "machine learning algorithms",
                "max_results": 5,
                "user_id": "test_user"
            }
            response = client.post("/api/advanced/research/search/basic", json=search_request)
            print(f"   Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response Status: {data.get('status')}")
                print(f"   Query: {data.get('query')}")
                results = data.get('results', [])
                print(f"   Results Count: {len(results)}")
                print(f"   Service Used: {data.get('service_used')}")
                print("   ✅ Basic research search endpoint working")
            else:
                print(f"   ❌ Unexpected status code: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Error testing basic research search: {str(e)}")
        
        # Test 5: Research Query Validation Endpoint
        print("\n5. Testing /api/advanced/research/validate")
        try:
            validation_request = {
                "query": "What are the latest developments in artificial intelligence?",
                "domain": "computer_science",
                "user_id": "test_user"
            }
            response = client.post("/api/advanced/research/validate", json=validation_request)
            print(f"   Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response Status: {data.get('status')}")
                validation = data.get('validation', {})
                print(f"   Query Valid: {validation.get('is_valid')}")
                print(f"   Query Type: {validation.get('query_type')}")
                print(f"   Confidence: {validation.get('confidence')}")
                print("   ✅ Research query validation endpoint working")
            else:
                print(f"   ❌ Unexpected status code: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Error testing research query validation: {str(e)}")
        
        print("\n" + "=" * 50)
        print("Basic Research Endpoints Test Complete")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure all required dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    """Main function to run the tests"""
    try:
        # Run the async test
        result = asyncio.run(test_research_endpoints())
        if result:
            print("\n🎉 All basic research endpoint tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to run tests: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()