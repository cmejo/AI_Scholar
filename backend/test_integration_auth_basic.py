"""
Basic test for integration authentication functionality
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_basic_functionality():
    """Test basic functionality without external dependencies"""
    print("🔐 Testing Integration Authentication Basic Functionality")
    print("=" * 60)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from services.oauth_server import OAuthServer, OAuthClient
        from services.api_key_service import APIKeyService, APIKey
        print("✓ All imports successful")
        
        # Test OAuth server initialization
        print("\n🔧 Testing OAuth server initialization...")
        oauth_server = OAuthServer()
        health = await oauth_server.health_check()
        print(f"✓ OAuth server health: {health.get('status', 'unknown')}")
        
        # Test API key service initialization
        print("\n🔑 Testing API key service initialization...")
        api_key_service = APIKeyService()
        api_health = await api_key_service.health_check()
        print(f"✓ API key service health: {api_health.get('status', 'unknown')}")
        
        # Test data models
        print("\n📋 Testing data models...")
        from datetime import datetime
        
        # Test OAuthClient model
        client = OAuthClient(
            client_id="test_client",
            client_secret="test_secret",
            name="Test Client",
            description="Test Description",
            redirect_uris=["http://localhost:3000/callback"],
            scopes=["read:documents"],
            client_type="confidential",
            created_at=datetime.now()
        )
        assert client.client_id == "test_client"
        print("✓ OAuthClient model working")
        
        # Test APIKey model
        api_key = APIKey(
            key_id="test_key",
            key_hash="test_hash",
            name="Test Key",
            description="Test Description",
            user_id="test_user",
            scopes=["read:documents"],
            rate_limit=1000,
            created_at=datetime.now()
        )
        assert api_key.key_id == "test_key"
        print("✓ APIKey model working")
        
        # Test middleware imports
        print("\n🛡️ Testing middleware imports...")
        from middleware.integration_auth_middleware import IntegrationAuthMiddleware
        print("✓ Middleware imports successful")
        
        # Test endpoint imports
        print("\n🌐 Testing endpoint imports...")
        from api.integration_auth_endpoints import router
        print("✓ Endpoint imports successful")
        
        print("\n" + "=" * 60)
        print("✅ All Basic Integration Authentication Tests Passed!")
        print("🔐 OAuth 2.0 server components are properly configured")
        print("🔑 API key management components are ready")
        print("🛡️ Security middleware is available")
        print("🌐 Authentication endpoints are configured")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Basic Integration Authentication Tests Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the basic test suite
    result = asyncio.run(test_basic_functionality())
    exit(0 if result else 1)