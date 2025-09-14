#!/usr/bin/env python3
"""
Test script for Task 4.1: Add semantic search service
Verifies the implementation of conditional import, service initialization, and health check endpoint
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_task_4_1():
    """Test Task 4.1 implementation"""
    print("=== Testing Task 4.1: Add Semantic Search Service ===")
    
    try:
        # Test 1: Conditional import functionality
        print("\n1. Testing conditional import of semantic_search_v2 service...")
        from core.conditional_importer import ConditionalImporter
        
        # Test safe import of numpy (should fail gracefully)
        numpy_result = ConditionalImporter.safe_import("numpy", fallback=None)
        print(f"   Numpy import result: {numpy_result}")
        
        # Test safe import of semantic search service
        semantic_service_class = ConditionalImporter.safe_import(
            module_name="services.semantic_search_v2",
            attribute="SemanticSearchV2Service",
            fallback=None
        )
        print(f"   SemanticSearchV2Service import result: {semantic_service_class}")
        
        # Test 2: Service initialization with error handling
        print("\n2. Testing service initialization with error handling...")
        from core.service_manager import service_manager
        
        # Initialize semantic search service
        init_success = await service_manager.initialize_semantic_search_service()
        print(f"   Service initialization success: {init_success}")
        
        # Check if service is available
        semantic_service = service_manager.get_service("semantic_search")
        service_available = semantic_service is not None
        print(f"   Service available: {service_available}")
        
        if service_available:
            print(f"   Service type: {type(semantic_service).__name__}")
            
            # Test service status
            if hasattr(semantic_service, 'get_status'):
                status = semantic_service.get_status()
                print(f"   Service status: {status}")
        
        # Test 3: Health check functionality
        print("\n3. Testing semantic search health check...")
        
        # Test service manager health check
        health_status = await service_manager.check_service_health("semantic_search")
        print(f"   Service health status: {health_status.status.value}")
        print(f"   Health error message: {health_status.error_message}")
        
        # Test service health check method
        if service_available and hasattr(semantic_service, 'health_check'):
            service_health = await semantic_service.health_check()
            print(f"   Service health check result: {service_health}")
        
        # Test 4: Health check endpoint
        print("\n4. Testing health check endpoint...")
        try:
            from fastapi.testclient import TestClient
            from app import app
            
            # Create test client
            client = TestClient(app)
            
            # Test semantic search health endpoint
            response = client.get("/api/advanced/semantic-search/health")
            print(f"   Endpoint status code: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"   Endpoint response status: {response_data.get('status')}")
                print(f"   Endpoint response message: {response_data.get('message')}")
            else:
                print(f"   Endpoint error: {response.text}")
                
        except Exception as e:
            print(f"   Endpoint test error: {e}")
        
        # Test 5: Verify requirements compliance
        print("\n5. Verifying requirements compliance...")
        
        # Requirement 1.1: Service import restoration
        req_1_1 = init_success and service_available
        print(f"   Requirement 1.1 (Service import restoration): {'✓' if req_1_1 else '✗'}")
        
        # Requirement 1.2: Error handling
        req_1_2 = semantic_service is not None  # Should have mock service even if real service fails
        print(f"   Requirement 1.2 (Error handling): {'✓' if req_1_2 else '✗'}")
        
        # Requirement 1.4: Service functionality
        req_1_4 = service_available and hasattr(semantic_service, 'health_check')
        print(f"   Requirement 1.4 (Service functionality): {'✓' if req_1_4 else '✗'}")
        
        # Overall success
        overall_success = req_1_1 and req_1_2 and req_1_4
        print(f"\n=== Task 4.1 Implementation Status: {'✓ COMPLETE' if overall_success else '✗ INCOMPLETE'} ===")
        
        return overall_success
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_task_4_1())
    sys.exit(0 if result else 1)