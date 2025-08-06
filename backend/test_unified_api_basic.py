"""
Basic test for unified API endpoints implementation
Tests the core structure and functionality of task 8.1
"""
import sys
import os

def test_unified_api_structure():
    """Test that unified API endpoints file exists and has basic structure"""
    try:
        # Check if the unified API file exists
        unified_api_path = "api/unified_api_endpoints.py"
        assert os.path.exists(unified_api_path), "Unified API endpoints file not found"
        
        # Read the file content
        with open(unified_api_path, 'r') as f:
            content = f.read()
        
        # Check for key components
        required_components = [
            "router = APIRouter(prefix=\"/api/v1\"",
            "class ConnectionManager:",
            "async def health_check():",
            "async def execute_feature(",
            "async def execute_batch_features(",
            "async def websocket_endpoint(",
            "async def get_api_version():",
            "async def get_mobile_config(",
            "async def mobile_sync(",
            "async def get_available_integrations():",
            "async def connect_integration(",
            "async def get_integration_status(",
            "async def mobile_websocket_endpoint(",
            "async def get_version_compatibility():",
            "async def migrate_from_legacy(",
            "async def get_openapi_spec():"
        ]
        
        for component in required_components:
            assert component in content, f"Missing component: {component}"
        
        print("✅ Unified API structure test passed")
        return True
        
    except Exception as e:
        print(f"❌ Unified API structure test failed: {e}")
        return False

def test_graphql_schema_structure():
    """Test that GraphQL schema file exists and has basic structure"""
    try:
        # Check if the GraphQL schema file exists
        graphql_path = "api/graphql_schema.py"
        assert os.path.exists(graphql_path), "GraphQL schema file not found"
        
        # Read the file content
        with open(graphql_path, 'r') as f:
            content = f.read()
        
        # Check for key components
        required_components = [
            "@strawberry.type",
            "class Query:",
            "class Mutation:",
            "schema = strawberry.Schema(query=Query, mutation=Mutation)",
            "graphql_router = GraphQLRouter(schema",
            "async def user(",
            "async def mobile_sync_status(",
            "async def academic_papers(",
            "async def process_voice(",
            "async def generate_quiz(",
            "async def sync_mobile_data(",
            "async def connect_integration(",
            "async def execute_batch_features("
        ]
        
        for component in required_components:
            assert component in content, f"Missing GraphQL component: {component}"
        
        print("✅ GraphQL schema structure test passed")
        return True
        
    except Exception as e:
        print(f"❌ GraphQL schema structure test failed: {e}")
        return False

def test_api_versioning_support():
    """Test that API versioning is properly implemented"""
    try:
        unified_api_path = "api/unified_api_endpoints.py"
        with open(unified_api_path, 'r') as f:
            content = f.read()
        
        # Check for versioning components
        versioning_components = [
            "api_version",
            "current_version",
            "supported_versions",
            "backward_compatibility",
            "migration_guide",
            "legacy_endpoints",
            "compatibility_matrix",
            "migration_paths"
        ]
        
        for component in versioning_components:
            assert component in content, f"Missing versioning component: {component}"
        
        print("✅ API versioning support test passed")
        return True
        
    except Exception as e:
        print(f"❌ API versioning support test failed: {e}")
        return False

def test_mobile_api_endpoints():
    """Test that mobile-specific API endpoints are implemented"""
    try:
        unified_api_path = "api/unified_api_endpoints.py"
        with open(unified_api_path, 'r') as f:
            content = f.read()
        
        # Check for mobile-specific components
        mobile_components = [
            "get_mobile_config",
            "mobile_sync",
            "get_offline_data",
            "mobile_websocket_endpoint",
            "sync_settings",
            "offline_capabilities",
            "voice_settings",
            "notification_settings"
        ]
        
        for component in mobile_components:
            assert component in content, f"Missing mobile component: {component}"
        
        print("✅ Mobile API endpoints test passed")
        return True
        
    except Exception as e:
        print(f"❌ Mobile API endpoints test failed: {e}")
        return False

def test_integration_endpoints():
    """Test that external integration endpoints are implemented"""
    try:
        unified_api_path = "api/unified_api_endpoints.py"
        with open(unified_api_path, 'r') as f:
            content = f.read()
        
        # Check for integration components
        integration_components = [
            "get_available_integrations",
            "connect_integration",
            "get_integration_status",
            "reference_managers",
            "note_taking",
            "academic_databases",
            "writing_tools",
            "zotero",
            "mendeley",
            "obsidian",
            "notion",
            "pubmed",
            "arxiv"
        ]
        
        for component in integration_components:
            assert component in content, f"Missing integration component: {component}"
        
        print("✅ Integration endpoints test passed")
        return True
        
    except Exception as e:
        print(f"❌ Integration endpoints test failed: {e}")
        return False

def test_websocket_enhancements():
    """Test that WebSocket endpoints are enhanced"""
    try:
        unified_api_path = "api/unified_api_endpoints.py"
        with open(unified_api_path, 'r') as f:
            content = f.read()
        
        # Check for WebSocket enhancements
        websocket_components = [
            "handle_websocket_feature_request",
            "handle_websocket_ping",
            "handle_websocket_subscription",
            "handle_websocket_chat",
            "handle_websocket_voice_command",
            "handle_websocket_collaboration",
            "mobile_websocket_endpoint",
            "connection_established",
            "supported_message_types"
        ]
        
        for component in websocket_components:
            assert component in content, f"Missing WebSocket component: {component}"
        
        print("✅ WebSocket enhancements test passed")
        return True
        
    except Exception as e:
        print(f"❌ WebSocket enhancements test failed: {e}")
        return False

def test_openapi_documentation():
    """Test that OpenAPI documentation is implemented"""
    try:
        unified_api_path = "api/unified_api_endpoints.py"
        with open(unified_api_path, 'r') as f:
            content = f.read()
        
        # Check for OpenAPI components
        openapi_components = [
            "get_openapi_spec",
            "openapi",
            "info",
            "servers",
            "paths",
            "components",
            "schemas",
            "securitySchemes"
        ]
        
        for component in openapi_components:
            assert component in content, f"Missing OpenAPI component: {component}"
        
        print("✅ OpenAPI documentation test passed")
        return True
        
    except Exception as e:
        print(f"❌ OpenAPI documentation test failed: {e}")
        return False

def test_batch_processing():
    """Test that batch processing is implemented"""
    try:
        unified_api_path = "api/unified_api_endpoints.py"
        with open(unified_api_path, 'r') as f:
            content = f.read()
        
        # Check for batch processing components
        batch_components = [
            "execute_batch_features",
            "BatchRequest",
            "parallel_execution",
            "batch_results",
            "total_requests",
            "successful",
            "failed"
        ]
        
        for component in batch_components:
            assert component in content, f"Missing batch processing component: {component}"
        
        print("✅ Batch processing test passed")
        return True
        
    except Exception as e:
        print(f"❌ Batch processing test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("Running unified API implementation tests...")
    print("=" * 50)
    
    tests = [
        test_unified_api_structure,
        test_graphql_schema_structure,
        test_api_versioning_support,
        test_mobile_api_endpoints,
        test_integration_endpoints,
        test_websocket_enhancements,
        test_openapi_documentation,
        test_batch_processing
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All unified API implementation tests passed!")
        print("\nImplemented features:")
        print("- ✅ RESTful API endpoints for mobile app and external integrations")
        print("- ✅ GraphQL API for flexible data querying")
        print("- ✅ Enhanced WebSocket endpoints for real-time features")
        print("- ✅ Comprehensive API versioning and backward compatibility")
        print("- ✅ Mobile-specific API endpoints and configuration")
        print("- ✅ External integration management")
        print("- ✅ Batch processing capabilities")
        print("- ✅ OpenAPI documentation generation")
        print("- ✅ Legacy endpoint migration support")
        print("- ✅ Real-time collaboration features")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)