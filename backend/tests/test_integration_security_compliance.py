"""
Integration Security and OAuth/API Key Compliance Tests

Tests for external integration security, OAuth implementation,
and API key management compliance.
"""

import pytest
import asyncio
import jwt
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import requests_mock
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from backend.services.oauth_server import OAuthServer
from backend.services.api_key_service import APIKeyService
from backend.services.security_testing_service import SecurityTestingService
from backend.middleware.integration_auth_middleware import IntegrationAuthMiddleware


class TestOAuthSecurityCompliance:
    """Test OAuth 2.0 implementation security and compliance"""
    
    @pytest.fixture
    def oauth_server(self):
        return OAuthServer()
    
    @pytest.fixture
    def security_service(self):
        return SecurityTestingService()
    
    @pytest.mark.asyncio
    async def test_oauth_client_authentication(self, oauth_server):
        """Test OAuth client authentication security"""
        # Test valid client credentials
        valid_client = {
            "client_id": "test_client_12345",
            "client_secret": "secure_client_secret_abcdef123456789",
            "grant_type": "client_credentials",
            "scope": "read write"
        }
        
        auth_result = await oauth_server.authenticate_client(
            valid_client["client_id"],
            valid_client["client_secret"]
        )
        
        assert auth_result.authenticated is True
        assert auth_result.client_id == valid_client["client_id"]
        
        # Test invalid client credentials
        invalid_client = {
            "client_id": "invalid_client",
            "client_secret": "wrong_secret",
            "grant_type": "client_credentials"
        }
        
        invalid_auth_result = await oauth_server.authenticate_client(
            invalid_client["client_id"],
            invalid_client["client_secret"]
        )
        
        assert invalid_auth_result.authenticated is False
        assert invalid_auth_result.error == "invalid_client"
    
    @pytest.mark.asyncio
    async def test_oauth_token_generation_security(self, oauth_server):
        """Test OAuth token generation security measures"""
        client_id = "test_client_token_gen"
        client_secret = "secure_secret_for_token_generation_123"
        
        # Generate access token
        token_result = await oauth_server.generate_access_token(
            client_id=client_id,
            client_secret=client_secret,
            scope=["read", "write"],
            expires_in=3600
        )
        
        assert token_result.success is True
        assert token_result.access_token is not None
        assert token_result.token_type == "Bearer"
        assert token_result.expires_in == 3600
        
        # Verify token structure and security
        token = token_result.access_token
        
        # Token should be JWT format
        try:
            # Decode without verification to check structure
            decoded_header = jwt.get_unverified_header(token)
            assert decoded_header["alg"] in ["RS256", "HS256"]
            assert decoded_header["typ"] == "JWT"
            
            # Decode payload without verification
            decoded_payload = jwt.decode(token, options={"verify_signature": False})
            assert decoded_payload["client_id"] == client_id
            assert "exp" in decoded_payload
            assert "iat" in decoded_payload
            assert "scope" in decoded_payload
            
        except jwt.InvalidTokenError:
            pytest.fail("Generated token is not a valid JWT")
    
    @pytest.mark.asyncio
    async def test_oauth_token_validation_security(self, oauth_server):
        """Test OAuth token validation security"""
        client_id = "test_client_validation"
        client_secret = "secure_secret_validation_456"
        
        # Generate valid token
        token_result = await oauth_server.generate_access_token(client_id, client_secret)
        valid_token = token_result.access_token
        
        # Test valid token validation
        validation_result = await oauth_server.validate_access_token(valid_token)
        assert validation_result.valid is True
        assert validation_result.client_id == client_id
        
        # Test expired token
        expired_payload = {
            "client_id": client_id,
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired
            "iat": datetime.utcnow() - timedelta(hours=2),
            "scope": ["read"]
        }
        expired_token = jwt.encode(expired_payload, client_secret, algorithm="HS256")
        
        expired_validation = await oauth_server.validate_access_token(expired_token)
        assert expired_validation.valid is False
        assert expired_validation.error == "token_expired"
        
        # Test tampered token
        tampered_token = valid_token[:-5] + "XXXXX"  # Tamper with signature
        
        tampered_validation = await oauth_server.validate_access_token(tampered_token)
        assert tampered_validation.valid is False
        assert tampered_validation.error == "invalid_signature"
    
    @pytest.mark.asyncio
    async def test_oauth_scope_validation(self, oauth_server):
        """Test OAuth scope validation and enforcement"""
        client_id = "test_client_scopes"
        client_secret = "secure_secret_scopes_789"
        
        # Test scope validation during token generation
        requested_scopes = ["read", "write", "admin", "delete"]
        
        token_result = await oauth_server.generate_access_token(
            client_id=client_id,
            client_secret=client_secret,
            scope=requested_scopes
        )
        
        # Verify only allowed scopes are granted
        validation_result = await oauth_server.validate_access_token(token_result.access_token)
        granted_scopes = validation_result.scope
        
        # Admin and delete scopes should be restricted
        assert "read" in granted_scopes
        assert "write" in granted_scopes
        assert "admin" not in granted_scopes  # Should be restricted
        assert "delete" not in granted_scopes  # Should be restricted
    
    @pytest.mark.asyncio
    async def test_oauth_rate_limiting(self, oauth_server):
        """Test OAuth rate limiting for token requests"""
        client_id = "test_client_rate_limit"
        client_secret = "secure_secret_rate_limit_abc"
        
        # Make multiple token requests rapidly
        successful_requests = 0
        rate_limited_requests = 0
        
        for i in range(20):  # Attempt 20 requests
            token_result = await oauth_server.generate_access_token(client_id, client_secret)
            
            if token_result.success:
                successful_requests += 1
            else:
                if token_result.error == "rate_limit_exceeded":
                    rate_limited_requests += 1
        
        # Should have some rate limiting after initial requests
        assert successful_requests > 0
        assert rate_limited_requests > 0
        assert successful_requests < 20  # Not all requests should succeed
    
    @pytest.mark.asyncio
    async def test_oauth_pkce_support(self, oauth_server):
        """Test OAuth PKCE (Proof Key for Code Exchange) support"""
        # Generate PKCE parameters
        code_verifier = secrets.token_urlsafe(32)
        code_challenge = hashlib.sha256(code_verifier.encode()).hexdigest()
        
        # Authorization request with PKCE
        auth_request = {
            "client_id": "test_pkce_client",
            "response_type": "code",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "redirect_uri": "https://example.com/callback"
        }
        
        auth_result = await oauth_server.handle_authorization_request(auth_request)
        assert auth_result.success is True
        assert auth_result.authorization_code is not None
        
        # Token request with PKCE verification
        token_request = {
            "grant_type": "authorization_code",
            "code": auth_result.authorization_code,
            "code_verifier": code_verifier,
            "client_id": "test_pkce_client"
        }
        
        token_result = await oauth_server.exchange_authorization_code(token_request)
        assert token_result.success is True
        assert token_result.access_token is not None
        
        # Test invalid code verifier
        invalid_token_request = token_request.copy()
        invalid_token_request["code_verifier"] = "invalid_verifier"
        
        invalid_result = await oauth_server.exchange_authorization_code(invalid_token_request)
        assert invalid_result.success is False
        assert invalid_result.error == "invalid_grant"


class TestAPIKeySecurityCompliance:
    """Test API key management security and compliance"""
    
    @pytest.fixture
    def api_key_service(self):
        return APIKeyService()
    
    @pytest.fixture
    def security_service(self):
        return SecurityTestingService()
    
    @pytest.mark.asyncio
    async def test_api_key_generation_security(self, api_key_service, security_service):
        """Test API key generation security"""
        user_id = "test_user_api_key_gen"
        
        # Generate API key
        key_result = await api_key_service.generate_api_key(
            user_id=user_id,
            name="Test API Key",
            permissions=["read", "write"]
        )
        
        assert key_result.success is True
        assert key_result.api_key is not None
        assert len(key_result.api_key) >= 32  # Minimum secure length
        
        # Test key security with security service
        security_result = await security_service.test_api_key_security(key_result.api_key)
        
        assert security_result.passed is True
        assert security_result.details["entropy"] > 4.0  # Good entropy
        assert security_result.details["character_diversity"] >= 3  # Diverse characters
    
    @pytest.mark.asyncio
    async def test_api_key_validation_security(self, api_key_service):
        """Test API key validation security"""
        user_id = "test_user_api_validation"
        
        # Generate valid API key
        key_result = await api_key_service.generate_api_key(user_id, "Valid Key")
        valid_key = key_result.api_key
        
        # Test valid key validation
        validation_result = await api_key_service.validate_api_key(valid_key)
        assert validation_result.valid is True
        assert validation_result.user_id == user_id
        
        # Test invalid key validation
        invalid_key = "invalid_api_key_12345"
        invalid_validation = await api_key_service.validate_api_key(invalid_key)
        assert invalid_validation.valid is False
        assert invalid_validation.error == "invalid_key"
        
        # Test revoked key
        revoke_result = await api_key_service.revoke_api_key(valid_key)
        assert revoke_result.success is True
        
        revoked_validation = await api_key_service.validate_api_key(valid_key)
        assert revoked_validation.valid is False
        assert revoked_validation.error == "key_revoked"
    
    @pytest.mark.asyncio
    async def test_api_key_permissions_enforcement(self, api_key_service):
        """Test API key permissions enforcement"""
        user_id = "test_user_permissions"
        
        # Generate key with limited permissions
        limited_key_result = await api_key_service.generate_api_key(
            user_id=user_id,
            name="Limited Key",
            permissions=["read"]
        )
        
        limited_key = limited_key_result.api_key
        
        # Test permission check for allowed operation
        read_permission = await api_key_service.check_permission(limited_key, "read")
        assert read_permission.allowed is True
        
        # Test permission check for disallowed operation
        write_permission = await api_key_service.check_permission(limited_key, "write")
        assert write_permission.allowed is False
        assert write_permission.error == "insufficient_permissions"
        
        # Test admin permission (should be denied)
        admin_permission = await api_key_service.check_permission(limited_key, "admin")
        assert admin_permission.allowed is False
    
    @pytest.mark.asyncio
    async def test_api_key_rate_limiting(self, api_key_service):
        """Test API key rate limiting"""
        user_id = "test_user_rate_limit"
        
        # Generate API key
        key_result = await api_key_service.generate_api_key(user_id, "Rate Limited Key")
        api_key = key_result.api_key
        
        # Test rate limiting
        successful_requests = 0
        rate_limited_requests = 0
        
        for i in range(100):  # Make many requests
            rate_check = await api_key_service.check_rate_limit(api_key)
            
            if rate_check.allowed:
                successful_requests += 1
            else:
                rate_limited_requests += 1
                assert rate_check.retry_after > 0
        
        # Should have rate limiting
        assert successful_requests > 0
        assert rate_limited_requests > 0
        assert successful_requests < 100  # Not all should succeed
    
    @pytest.mark.asyncio
    async def test_api_key_rotation_security(self, api_key_service):
        """Test API key rotation security"""
        user_id = "test_user_rotation"
        
        # Generate initial API key
        initial_result = await api_key_service.generate_api_key(user_id, "Rotation Test")
        old_key = initial_result.api_key
        
        # Rotate the key
        rotation_result = await api_key_service.rotate_api_key(old_key)
        assert rotation_result.success is True
        
        new_key = rotation_result.new_api_key
        assert new_key != old_key
        assert len(new_key) >= 32
        
        # Test old key is invalidated
        old_validation = await api_key_service.validate_api_key(old_key)
        assert old_validation.valid is False
        assert old_validation.error == "key_rotated"
        
        # Test new key is valid
        new_validation = await api_key_service.validate_api_key(new_key)
        assert new_validation.valid is True
        assert new_validation.user_id == user_id
    
    @pytest.mark.asyncio
    async def test_api_key_audit_logging(self, api_key_service):
        """Test API key usage audit logging"""
        user_id = "test_user_audit"
        
        # Generate API key
        key_result = await api_key_service.generate_api_key(user_id, "Audit Test")
        api_key = key_result.api_key
        
        with patch.object(api_key_service, 'log_api_key_usage') as mock_log:
            # Use API key
            await api_key_service.validate_api_key(api_key)
            
            # Verify usage is logged
            mock_log.assert_called_once()
            log_entry = mock_log.call_args[0][0]
            
            assert log_entry["event_type"] == "api_key_usage"
            assert log_entry["api_key_id"] is not None
            assert log_entry["user_id"] == user_id
            assert log_entry["timestamp"] is not None
            assert log_entry["ip_address"] is not None


class TestIntegrationSecurityScenarios:
    """Test complex integration security scenarios"""
    
    @pytest.fixture
    def auth_middleware(self):
        return IntegrationAuthMiddleware()
    
    @pytest.mark.asyncio
    async def test_oauth_api_key_integration(self):
        """Test OAuth and API key integration security"""
        oauth_server = OAuthServer()
        api_key_service = APIKeyService()
        
        # OAuth flow
        client_id = "integration_test_client"
        client_secret = "secure_integration_secret_123"
        
        # Generate OAuth token
        oauth_token_result = await oauth_server.generate_access_token(client_id, client_secret)
        oauth_token = oauth_token_result.access_token
        
        # Use OAuth token to generate API key
        api_key_result = await api_key_service.generate_api_key_with_oauth(
            oauth_token=oauth_token,
            name="OAuth Generated Key"
        )
        
        assert api_key_result.success is True
        
        # Verify API key inherits OAuth permissions
        api_key = api_key_result.api_key
        validation_result = await api_key_service.validate_api_key(api_key)
        
        assert validation_result.valid is True
        assert validation_result.oauth_client_id == client_id
    
    @pytest.mark.asyncio
    async def test_integration_data_isolation(self):
        """Test data isolation between different integrations"""
        api_key_service = APIKeyService()
        
        # Create two different integration clients
        client_a_key = await api_key_service.generate_api_key("client_a", "Client A Key")
        client_b_key = await api_key_service.generate_api_key("client_b", "Client B Key")
        
        # Test that Client A cannot access Client B's data
        with pytest.raises(PermissionError):
            await api_key_service.access_integration_data(
                api_key=client_a_key.api_key,
                target_client="client_b",
                resource="sensitive_data"
            )
        
        # Test that Client B cannot access Client A's data
        with pytest.raises(PermissionError):
            await api_key_service.access_integration_data(
                api_key=client_b_key.api_key,
                target_client="client_a",
                resource="sensitive_data"
            )
    
    @pytest.mark.asyncio
    async def test_integration_security_headers(self, auth_middleware):
        """Test security headers in integration responses"""
        mock_request = Mock()
        mock_request.headers = {
            "Authorization": "Bearer valid_token_123",
            "Content-Type": "application/json"
        }
        
        mock_response = Mock()
        mock_response.headers = {}
        
        # Process request through auth middleware
        processed_response = await auth_middleware.add_security_headers(mock_response)
        
        # Verify security headers are added
        headers = processed_response.headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Strict-Transport-Security" in headers
        assert "Content-Security-Policy" in headers
        
        # Verify header values
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["X-XSS-Protection"] == "1; mode=block"
    
    @pytest.mark.asyncio
    async def test_integration_webhook_security(self):
        """Test webhook security for integrations"""
        api_key_service = APIKeyService()
        
        # Generate webhook signing key
        webhook_key_result = await api_key_service.generate_webhook_signing_key("test_integration")
        signing_key = webhook_key_result.signing_key
        
        # Create webhook payload
        webhook_payload = {
            "event": "data_updated",
            "timestamp": datetime.now().isoformat(),
            "data": {"id": "123", "status": "updated"}
        }
        
        # Sign webhook payload
        signature = await api_key_service.sign_webhook_payload(webhook_payload, signing_key)
        
        # Verify webhook signature
        verification_result = await api_key_service.verify_webhook_signature(
            payload=webhook_payload,
            signature=signature,
            signing_key=signing_key
        )
        
        assert verification_result.valid is True
        
        # Test invalid signature
        invalid_signature = "invalid_signature_123"
        invalid_verification = await api_key_service.verify_webhook_signature(
            payload=webhook_payload,
            signature=invalid_signature,
            signing_key=signing_key
        )
        
        assert invalid_verification.valid is False
    
    @pytest.mark.asyncio
    async def test_integration_ssl_certificate_validation(self):
        """Test SSL certificate validation for external integrations"""
        with requests_mock.Mocker() as m:
            # Mock external API with valid SSL
            m.get("https://api.external-service.com/data", json={"status": "ok"})
            
            # Test SSL validation
            api_key_service = APIKeyService()
            
            ssl_validation_result = await api_key_service.validate_external_ssl(
                "https://api.external-service.com"
            )
            
            assert ssl_validation_result.valid is True
            assert ssl_validation_result.certificate_valid is True
            assert ssl_validation_result.certificate_expiry > datetime.now()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])