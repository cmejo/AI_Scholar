#!/usr/bin/env python3
"""
Demonstration of endpoint error handling implementation
Shows how the error handling works in practice
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def demo_error_handling():
    """Demonstrate error handling functionality"""
    print("🔧 Endpoint Error Handling Implementation Demo")
    print("=" * 60)
    
    # 1. Demonstrate error response creation
    print("\n1. Creating standardized error responses:")
    print("-" * 40)
    
    from core.error_handler import EndpointErrorHandler
    
    error_response = EndpointErrorHandler.create_error_response(
        error_type="service_unavailable",
        message="Semantic search service is temporarily unavailable",
        details={"service_name": "semantic_search", "retry_after": 30},
        request_id="demo-request-123"
    )
    
    print(f"Error Type: {error_response.error}")
    print(f"Message: {error_response.message}")
    print(f"Details: {error_response.details}")
    print(f"Request ID: {error_response.request_id}")
    print(f"Timestamp: {error_response.timestamp}")
    
    # 2. Demonstrate fallback responses
    print("\n2. Creating fallback responses:")
    print("-" * 40)
    
    from core.error_handler import create_fallback_response
    
    fallback = create_fallback_response(
        message="Search service temporarily unavailable - using cached results",
        data={"results": [{"title": "Cached Result 1", "score": 0.8}]},
        status="degraded"
    )
    
    print(f"Status: {fallback['status']}")
    print(f"Message: {fallback['message']}")
    print(f"Data: {fallback['data']}")
    print(f"Fallback Flag: {fallback['fallback']}")
    
    # 3. Demonstrate error logging
    print("\n3. Error logging with data sanitization:")
    print("-" * 40)
    
    test_error = Exception("Database connection timeout")
    request_data = {
        "query": "machine learning research",
        "user_id": "user123",
        "api_key": "secret-key-456",
        "password": "user-password"
    }
    
    EndpointErrorHandler.log_error(
        endpoint_name="semantic_search",
        error=test_error,
        request_data=request_data,
        user_id="user123",
        request_id="demo-request-456"
    )
    
    print("✓ Error logged with sensitive data sanitized")
    
    # 4. Demonstrate decorator usage
    print("\n4. Endpoint decorator with error handling:")
    print("-" * 40)
    
    from core.error_handler import handle_endpoint_errors, ValidationError
    
    @handle_endpoint_errors(
        "demo_endpoint",
        required_services=["nonexistent_service"],
        fallback_response=create_fallback_response(
            message="Demo service unavailable",
            data={"demo": True}
        )
    )
    async def demo_endpoint(query: str):
        # This would normally do something with the service
        return {"status": "ok", "results": []}
    
    result = await demo_endpoint("test query")
    print(f"Endpoint result: {result}")
    print("✓ Decorator returned fallback response for missing service")
    
    # 5. Demonstrate validation
    print("\n5. Request validation:")
    print("-" * 40)
    
    from core.error_handler import validate_request_data
    
    try:
        validate_request_data(
            {"query": "test", "user_id": ""},  # user_id is empty
            ["query", "user_id"]
        )
    except ValidationError as e:
        print(f"Validation error: {e.message}")
        print(f"Details: {e.details}")
        print("✓ Validation correctly caught invalid data")
    
    # 6. Show service status integration
    print("\n6. Service status integration:")
    print("-" * 40)
    
    from core.service_manager import service_manager
    
    status_context = EndpointErrorHandler.get_service_status_context(
        service_manager,
        ["semantic_search", "research_automation"]
    )
    
    for service, status in status_context.items():
        print(f"  {service}: {status}")
    
    print("\n🎉 Error handling implementation demonstration complete!")
    print("\nKey features implemented:")
    print("✓ Graceful error responses for service unavailability")
    print("✓ Consistent error message formats across all endpoints")
    print("✓ Comprehensive error logging with data sanitization")
    print("✓ Endpoint decorators with fallback responses")
    print("✓ Request validation with detailed error messages")
    print("✓ Service status integration and monitoring")

if __name__ == "__main__":
    asyncio.run(demo_error_handling())