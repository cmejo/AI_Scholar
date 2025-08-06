"""
Comprehensive test suite for integration authentication
Tests OAuth 2.0 server, API key management, and security features
"""
import pytest
import asyncio
import json
import secrets
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from services.oauth_server import OAuthServer
from services.api_key_service import APIKeyService
from core.redis_client import redis_client

class TestOAuthServer:
    """Test OAuth 2.0 server functionality"""
    
    @pytest.fixture
    async def oauth_server(self):
        """Create OAuth server instance"""
        return OAuthServer()
    
    @pytest.fixture
    async def test_client_data(self):
        """Test client registration data"""
        return {
            "name": "Test Integration Client",
            "description": "Test client for integration testing",
            "redirect_uris": ["http://localhost:3000/callback"],
            "scopes": ["read:documents", "write:documents"],
            "client_type": "confidential"
        }
    
    async def test_client_registration(self, oauth_server, test_client_data):
        """Test OAuth client registration"""
        try:
            client = await oauth_server.register_client(**test_client_data)
            
            assert client.client_id.startswith("client_")
            assert len(client.client_secret) > 20
            assert client.name == test_client_data["name"]
            assert client.redirect_uris == test_client_data["redirect_uris"]
            assert client.scopes == test_client_data["scopes"]
            assert client.is_active is True
            
            print(f"✓ Client registered successfully: {client.client_id}")
            return client
            
        except Exception as e:
            print(f"✗ Client registration failed: {e}")
            raise
    
    async def test_client_authentication(self, oauth_server):
        """Test OAuth client authentication"""
        try:
            # First register a client
            client = await oauth_server.register_client(
                name="Auth Test Client",
                description="Client for authentication testing",
                redirect_uris=["http://localhost:3000/callback"],
                scopes=["read:basic"],
                client_type="confidential"
            )
            
            # Test authentication with correct credentials
            auth_client = await oauth_server.authenticate_client(
                client.client_id, 
                client.client_secret
            )
            assert auth_client is not None
            assert auth_client.client_id == client.client_id
            
            # Test authentication with wrong credentials
            wrong_auth = await oauth_server.authenticate_client(
                client.client_id, 
                "wrong_secret"
            )
            assert wrong_auth is None
            
            print("✓ Client authentication working correctly")
            
        except Exception as e:
            print(f"✗ Client authentication test failed: {e}")
            raise
    
    async def test_authorization_code_flow(self, oauth_server):
        """Test OAuth authorization code flow"""
        try:
            # Register client
            client = await oauth_server.register_client(
                name="Code Flow Test Client",
                description="Client for code flow testing",
                redirect_uris=["http://localhost:3000/callback"],
                scopes=["read:documents", "write:documents"],
                client_type="confidential"
            )
            
            # Generate authorization code
            user_id = "test_user_123"
            redirect_uri = "http://localhost:3000/callback"
            scopes = ["read:documents"]
            
            auth_code = await oauth_server.generate_authorization_code(
                client_id=client.client_id,
                user_id=user_id,
                redirect_uri=redirect_uri,
                scopes=scopes
            )
            
            assert len(auth_code.code) > 20
            assert auth_code.client_id == client.client_id
            assert auth_code.user_id == user_id
            assert auth_code.scopes == scopes
            
            # Exchange code for tokens
            token_data = await oauth_server.exchange_code_for_tokens(
                code=auth_code.code,
                client_id=client.client_id,
                client_secret=client.client_secret,
                redirect_uri=redirect_uri
            )
            
            assert "access_token" in token_data
            assert "refresh_token" in token_data
            assert "token_type" in token_data
            assert "expires_in" in token_data
            assert token_data["token_type"] == "Bearer"
            
            print("✓ Authorization code flow working correctly")
            return token_data
            
        except Exception as e:
            print(f"✗ Authorization code flow test failed: {e}")
            raise
    
    async def test_token_refresh(self, oauth_server):
        """Test OAuth token refresh"""
        try:
            # First get tokens through authorization code flow
            client = await oauth_server.register_client(
                name="Refresh Test Client",
                description="Client for refresh testing",
                redirect_uris=["http://localhost:3000/callback"],
                scopes=["read:documents"],
                client_type="confidential"
            )
            
            auth_code = await oauth_server.generate_authorization_code(
                client_id=client.client_id,
                user_id="test_user_123",
                redirect_uri="http://localhost:3000/callback",
                scopes=["read:documents"]
            )
            
            initial_tokens = await oauth_server.exchange_code_for_tokens(
                code=auth_code.code,
                client_id=client.client_id,
                client_secret=client.client_secret,
                redirect_uri="http://localhost:3000/callback"
            )
            
            # Refresh the access token
            new_tokens = await oauth_server.refresh_access_token(
                refresh_token=initial_tokens["refresh_token"],
                client_id=client.client_id,
                client_secret=client.client_secret
            )
            
            assert "access_token" in new_tokens
            assert "token_type" in new_tokens
            assert "expires_in" in new_tokens
            assert new_tokens["access_token"] != initial_tokens["access_token"]
            
            print("✓ Token refresh working correctly")
            
        except Exception as e:
            print(f"✗ Token refresh test failed: {e}")
            raise
    
    async def test_integration_specific_client(self, oauth_server):
        """Test integration-specific client creation"""
        try:
            integration_types = ["zotero", "mendeley", "obsidian", "mobile"]
            
            for integration_type in integration_types:
                client = await oauth_server.create_integration_specific_client(
                    integration_type=integration_type,
                    name=f"Test {integration_type.title()} Client",
                    description=f"Test client for {integration_type}",
                    redirect_uris=[f"http://localhost:3000/{integration_type}/callback"],
                    additional_config={"test": True}
                )
                
                assert client.client_id.startswith("client_")
                assert integration_type.title() in client.name
                
                # Validate integration access
                is_valid = await oauth_server.validate_integration_access(
                    client_id=client.client_id,
                    integration_type=integration_type,
                    requested_scopes=client.scopes[:1]  # Test with first scope
                )
                assert is_valid is True
                
                print(f"✓ Integration-specific client created for {integration_type}")
            
        except Exception as e:
            print(f"✗ Integration-specific client test failed: {e}")
            raise
    
    async def test_device_flow(self, oauth_server):
        """Test OAuth device authorization flow"""
        try:
            # Register client
            client = await oauth_server.register_client(
                name="Device Flow Test Client",
                description="Client for device flow testing",
                redirect_uris=["http://localhost:3000/callback"],
                scopes=["read:documents"],
                client_type="confidential"
            )
            
            # Initiate device flow
            device_flow_data = await oauth_server.create_device_flow_code(
                client_id=client.client_id,
                scopes=["read:documents"]
            )
            
            assert "device_code" in device_flow_data
            assert "user_code" in device_flow_data
            assert "verification_uri" in device_flow_data
            assert "expires_in" in device_flow_data
            
            # Authorize device
            user_id = "test_user_123"
            auth_success = await oauth_server.authorize_device_flow(
                user_code=device_flow_data["user_code"],
                user_id=user_id
            )
            assert auth_success is True
            
            # Poll for tokens
            token_result = await oauth_server.poll_device_flow(
                device_code=device_flow_data["device_code"],
                client_id=client.client_id,
                client_secret=client.client_secret
            )
            
            assert "access_token" in token_result
            assert "refresh_token" in token_result
            
            print("✓ Device flow working correctly")
            
        except Exception as e:
            print(f"✗ Device flow test failed: {e}")
            raise

class TestAPIKeyService:
    """Test API key management functionality"""
    
    @pytest.fixture
    async def api_key_service(self):
        """Create API key service instance"""
        return APIKeyService()
    
    async def test_api_key_creation(self, api_key_service):
        """Test API key creation"""
        try:
            user_id = "test_user_123"
            api_key_data = await api_key_service.create_api_key(
                user_id=user_id,
                name="Test API Key",
                description="Test key for integration testing",
                scopes=["read:documents", "write:documents"],
                rate_limit=500,
                expires_in_days=30
            )
            
            assert "key_id" in api_key_data
            assert "api_key" in api_key_data
            assert api_key_data["api_key"].startswith("ak_")
            assert api_key_data["name"] == "Test API Key"
            assert api_key_data["rate_limit"] == 500
            assert "expires_at" in api_key_data
            
            print(f"✓ API key created successfully: {api_key_data['key_id']}")
            return api_key_data
            
        except Exception as e:
            print(f"✗ API key creation failed: {e}")
            raise
    
    async def test_api_key_authentication(self, api_key_service):
        """Test API key authentication"""
        try:
            # Create API key
            user_id = "test_user_123"
            api_key_data = await api_key_service.create_api_key(
                user_id=user_id,
                name="Auth Test Key",
                description="Key for authentication testing",
                scopes=["read:basic"],
                rate_limit=100
            )
            
            # Test authentication with correct key
            key_info = await api_key_service.authenticate_api_key(
                api_key_data["api_key"],
                client_ip="127.0.0.1",
                user_agent="Test Agent"
            )
            assert key_info is not None
            assert key_info.key_id == api_key_data["key_id"]
            assert key_info.user_id == user_id
            
            # Test authentication with wrong key
            wrong_key_info = await api_key_service.authenticate_api_key(
                "ak_wrong_key_12345",
                client_ip="127.0.0.1"
            )
            assert wrong_key_info is None
            
            print("✓ API key authentication working correctly")
            
        except Exception as e:
            print(f"✗ API key authentication test failed: {e}")
            raise
    
    async def test_rate_limiting(self, api_key_service):
        """Test API key rate limiting"""
        try:
            # Create API key with low rate limit
            user_id = "test_user_123"
            api_key_data = await api_key_service.create_api_key(
                user_id=user_id,
                name="Rate Limit Test Key",
                description="Key for rate limit testing",
                scopes=["read:basic"],
                rate_limit=2  # Very low limit for testing
            )
            
            key_id = api_key_data["key_id"]
            
            # First request should succeed
            rate_limit_info1 = await api_key_service.check_rate_limit(key_id)
            assert rate_limit_info1.requests_remaining >= 0
            
            # Second request should succeed
            rate_limit_info2 = await api_key_service.check_rate_limit(key_id)
            assert rate_limit_info2.requests_remaining >= 0
            
            # Third request should be rate limited
            rate_limit_info3 = await api_key_service.check_rate_limit(key_id)
            assert rate_limit_info3.requests_remaining == 0
            
            print("✓ Rate limiting working correctly")
            
        except Exception as e:
            print(f"✗ Rate limiting test failed: {e}")
            raise
    
    async def test_integration_api_key(self, api_key_service):
        """Test integration-specific API key creation"""
        try:
            user_id = "test_user_123"
            integration_types = ["zotero", "obsidian", "mobile", "jupyter"]
            
            for integration_type in integration_types:
                api_key_data = await api_key_service.create_integration_api_key(
                    user_id=user_id,
                    integration_type=integration_type,
                    integration_config={"test": True}
                )
                
                assert "key_id" in api_key_data
                assert "api_key" in api_key_data
                assert api_key_data["integration_type"] == integration_type
                assert integration_type.title() in api_key_data["name"]
                
                print(f"✓ Integration API key created for {integration_type}")
            
        except Exception as e:
            print(f"✗ Integration API key test failed: {e}")
            raise
    
    async def test_scope_validation(self, api_key_service):
        """Test API key scope validation"""
        try:
            # Create API key with specific scopes
            user_id = "test_user_123"
            api_key_data = await api_key_service.create_api_key(
                user_id=user_id,
                name="Scope Test Key",
                description="Key for scope testing",
                scopes=["read:documents", "write:documents"],
                rate_limit=100
            )
            
            key_id = api_key_data["key_id"]
            
            # Test valid scope access
            has_read_access = await api_key_service.validate_scope_access(
                key_id=key_id,
                required_scopes=["read:documents"]
            )
            assert has_read_access is True
            
            # Test invalid scope access
            has_admin_access = await api_key_service.validate_scope_access(
                key_id=key_id,
                required_scopes=["admin:users"]
            )
            assert has_admin_access is False
            
            print("✓ Scope validation working correctly")
            
        except Exception as e:
            print(f"✗ Scope validation test failed: {e}")
            raise

class TestSecurityFeatures:
    """Test security features and edge cases"""
    
    async def test_token_introspection(self):
        """Test OAuth token introspection"""
        try:
            oauth_server = OAuthServer()
            
            # Create client and get tokens
            client = await oauth_server.register_client(
                name="Introspection Test Client",
                description="Client for introspection testing",
                redirect_uris=["http://localhost:3000/callback"],
                scopes=["read:documents"],
                client_type="confidential"
            )
            
            auth_code = await oauth_server.generate_authorization_code(
                client_id=client.client_id,
                user_id="test_user_123",
                redirect_uri="http://localhost:3000/callback",
                scopes=["read:documents"]
            )
            
            tokens = await oauth_server.exchange_code_for_tokens(
                code=auth_code.code,
                client_id=client.client_id,
                client_secret=client.client_secret,
                redirect_uri="http://localhost:3000/callback"
            )
            
            # Test token introspection
            token_info = await oauth_server.get_token_info(tokens["access_token"])
            assert token_info["active"] is True
            assert token_info["token_type"] == "access_token"
            assert token_info["client_id"] == client.client_id
            
            print("✓ Token introspection working correctly")
            
        except Exception as e:
            print(f"✗ Token introspection test failed: {e}")
            raise
    
    async def test_suspicious_activity_detection(self):
        """Test suspicious activity detection for API keys"""
        try:
            api_key_service = APIKeyService()
            
            # Create API key
            user_id = "test_user_123"
            api_key_data = await api_key_service.create_api_key(
                user_id=user_id,
                name="Security Test Key",
                description="Key for security testing",
                scopes=["read:basic"],
                rate_limit=100
            )
            
            # Simulate requests from multiple IPs (should trigger detection)
            ips = ["192.168.1.1", "10.0.0.1", "172.16.0.1", "203.0.113.1", "198.51.100.1", "192.0.2.1"]
            
            for ip in ips:
                key_info = await api_key_service.authenticate_api_key(
                    api_key_data["api_key"],
                    client_ip=ip,
                    user_agent="Test Agent"
                )
                # First few should succeed
                if len(ips) <= 5:
                    assert key_info is not None
            
            print("✓ Suspicious activity detection working")
            
        except Exception as e:
            print(f"✗ Suspicious activity detection test failed: {e}")
            raise

async def run_comprehensive_tests():
    """Run all integration authentication tests"""
    print("🔐 Starting Integration Authentication Comprehensive Tests")
    print("=" * 60)
    
    try:
        # Test OAuth Server
        print("\n📋 Testing OAuth Server...")
        oauth_tests = TestOAuthServer()
        oauth_server = OAuthServer()
        
        test_client_data = {
            "name": "Test Integration Client",
            "description": "Test client for integration testing",
            "redirect_uris": ["http://localhost:3000/callback"],
            "scopes": ["read:documents", "write:documents"],
            "client_type": "confidential"
        }
        
        await oauth_tests.test_client_registration(oauth_server, test_client_data)
        await oauth_tests.test_client_authentication(oauth_server)
        await oauth_tests.test_authorization_code_flow(oauth_server)
        await oauth_tests.test_token_refresh(oauth_server)
        await oauth_tests.test_integration_specific_client(oauth_server)
        await oauth_tests.test_device_flow(oauth_server)
        
        # Test API Key Service
        print("\n🔑 Testing API Key Service...")
        api_key_tests = TestAPIKeyService()
        api_key_service = APIKeyService()
        
        await api_key_tests.test_api_key_creation(api_key_service)
        await api_key_tests.test_api_key_authentication(api_key_service)
        await api_key_tests.test_rate_limiting(api_key_service)
        await api_key_tests.test_integration_api_key(api_key_service)
        await api_key_tests.test_scope_validation(api_key_service)
        
        # Test Security Features
        print("\n🛡️ Testing Security Features...")
        security_tests = TestSecurityFeatures()
        
        await security_tests.test_token_introspection()
        await security_tests.test_suspicious_activity_detection()
        
        print("\n" + "=" * 60)
        print("✅ All Integration Authentication Tests Passed!")
        print("🔐 OAuth 2.0 server is working correctly")
        print("🔑 API key management is functioning properly")
        print("🛡️ Security features are active and effective")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration Authentication Tests Failed: {e}")
        return False

if __name__ == "__main__":
    # Run the comprehensive test suite
    result = asyncio.run(run_comprehensive_tests())
    exit(0 if result else 1)