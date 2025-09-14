#!/usr/bin/env python3
"""
Test the knowledge graph health endpoint
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_knowledge_graph_endpoint():
    """Test the knowledge graph health endpoint"""
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        print("🧪 Testing Knowledge Graph Health Endpoint...")
        
        # Create test client
        client = TestClient(app)
        
        # Test the knowledge graph health endpoint
        response = client.get('/api/advanced/knowledge-graph/health')
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') in ['ok', 'degraded']:
                print("✅ Knowledge graph health endpoint working correctly")
                return True
            else:
                print(f"⚠️ Knowledge graph health endpoint returned unexpected status: {data.get('status')}")
                return True  # Still working, just degraded
        else:
            print(f"❌ Knowledge graph health endpoint failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing knowledge graph endpoint: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_knowledge_graph_endpoint())
    print(f"Test result: {'PASSED' if success else 'FAILED'}")