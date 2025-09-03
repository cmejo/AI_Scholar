"""
Integration tests for Zotero authentication endpoints
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
import json

from api.zotero_endpoints import router
from services.zotero.zotero_auth_service import ZoteroAuthService, ZoteroAuthError
from models.zotero_models import ZoteroConnection


class TestZoteroAuthEndpoints:
    """Test cases for Zotero authentication endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        user = Mock()
        user.id = "test_user_123"
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def mock_connection(self):
        """Mock Zotero connection"""
        connection = Mock(spec=ZoteroConnection)
        connection.id = "conn_123"
        connection.user_id = "test_user_123"
        connection.zotero_user_id = "12345"
        connection.access_token = "test_token"
        connection.connection_type = "oauth"
        connection.connection_status = "active"
        connection.sync_enabled = True
        connection.created_at = datetime.now()
        connection.updated_at = datetime.now()
        connection.last_sync_at = None
        connection.connection_metadata = {"username": "testuser"}
        return connection
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authorization headers"""
        return {"Authorization": "Bearer test_jwt_token"}
    
    def test_initiate_oauth_success(self, client, mock_user, auth_headers):
        """Test successful OAuth initiation"""
        with patch('api.zotero_endpoints.get_current_user', return_value=mock_user), \
             patch('api.zotero_endpoints.zotero_auth_service.get_authorization_url') as mock_get_url:
            
            mock_get_url.return_value = ("https://zotero.org/oauth/authorize?...", "test_state")
            
            response = client.post("/api/zotero/oauth/initiate", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "authorization_url" in data
            assert "state" in data
            assert "expires_in" in data
            assert data["expires_in"] == 600
    
    def test_initiate_oauth_with_scopes(self, client, mock_user, auth_headers):
        """Test OAuth initiation with custom scopes"""
        with patch('api.zotero_endpoints.get_current_user', return_value=mock_user), \
             patch('api.zotero_endpoints.zotero_auth_service.get_authorization_url') as mock_get_url:
            
            mock_get_url.return_value = ("https://zotero.org/oauth/authorize?...", "test_state")
            
            response = client.post(
                "/api/zotero/oauth/initiate?scopes=read&scopes=write",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            mock_get_url.assert_called_once_with(user_id=mock_user.id, scopes=["read", "write"])
    
    def test_initiate_oauth_unauthorized(self, client):
        """Test OAuth initiation without authentication"""
        response = client.post("/api/zotero/oauth/initiate")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_initiate_oauth_service_error(self, client, mock_user, auth_headers):
        """Test OAuth initiation with service error"""
        with patch('api.zotero_endpoints.get_current_user', return_value=mock_user), \
             patch('api.zotero_endpoints.zotero_auth_service.get_authorization_url', side_effect=Exception("Service error")):
            
            response = client.post("/api/zotero/oauth/initiate", headers=auth_headers)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_oauth_callback_success(self, client, mock_connection):
        """Test successful OAuth callback"""
        callback_data = {
            "code": "test_auth_code",
            "state": "test_state"
        }
        
        token_data = {
            "access_token": "test_token",
            "zotero_user_id": "12345",
            "username": "testuser",
            "token_type": "Bearer",
            "obtained_at": datetime.now().isoformat()
        }
        
        state_info = {
            "user_id": "test_user_123",
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(minutes=10),
            "used": False
        }
        
        with patch('api.zotero_endpoints.zotero_auth_service.get_oauth_state_info', return_value=state_info), \
             patch('api.zotero_endpoints.zotero_auth_service.exchange_code_for_token', return_value=token_data), \
             patch('api.zotero_endpoints.zotero_auth_service.store_connection', return_value=mock_connection):
            
            response = client.post("/api/zotero/oauth/callback", json=callback_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == mock_connection.id
            assert data["user_id"] == mock_connection.user_id
            assert data["connection_status"] == "active"
    
    def test_oauth_callback_invalid_state(self, client):
        """Test OAuth callback with invalid state"""
        callback_data = {
            "code": "test_auth_code",
            "state": "invalid_state"
        }
        
        with patch('api.zotero_endpoints.zotero_auth_service.get_oauth_state_info', return_value=None):
            
            response = client.post("/api/zotero/oauth/callback", json=callback_data)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invalid or expired OAuth state" in response.json()["detail"]
    
    def test_oauth_callback_token_exchange_error(self, client):
        """Test OAuth callback with token exchange error"""
        callback_data = {
            "code": "invalid_code",
            "state": "test_state"
        }
        
        state_info = {
            "user_id": "test_user_123",
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(minutes=10),
            "used": False
        }
        
        with patch('api.zotero_endpoints.zotero_auth_service.get_oauth_state_info', return_value=state_info), \
             patch('api.zotero_endpoints.zotero_auth_service.exchange_code_for_token', 
                   side_effect=ZoteroAuthError("Token exchange failed", "TOKEN_EXCHANGE_FAILED")):
            
            response = client.post("/api/zotero/oauth/callback", json=callback_data)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Token exchange failed" in response.json()["detail"]
    
    def test_oauth_callback_storage_error(self, client):
        """Test OAuth callback with storage error"""
        callback_data = {
            "code": "test_auth_code",
            "state": "test_state"
        }
        
        token_data = {
            "access_token": "test_token",
            "zotero_user_id": "12345",
            "username": "testuser"
        }
        
        state_info = {
            "user_id": "test_user_123",
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(minutes=10),
            "used": False
        }
        
        with patch('api.zotero_endpoints.zotero_auth_service.get_oauth_state_info', return_value=state_info), \
             patch('api.zotero_endpoints.zotero_auth_service.exchange_code_for_token', return_value=token_data), \
             patch('api.zotero_endpoints.zotero_auth_service.store_connection', 
                   side_effect=ZoteroAuthError("Storage failed", "STORAGE_ERROR")):
            
            response = client.post("/api/zotero/oauth/callback", json=callback_data)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_create_api_key_connection_success(self, client, mock_user, mock_connection, auth_headers):
        """Test successful API key connection creation"""
        connection_data = {
            "connection_type": "api_key",
            "api_key": "test_api_key",
            "zotero_user_id": "12345"
        }
        
        with patch('api.zotero_endpoints.get_current_user', return_value=mock_user), \
             patch('api.zotero_endpoints.zotero_auth_service.create_api_key_connection', return_value=mock_connection):
            
            response = client.post("/api/zotero/connections", json=connection_data, headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == mock_connection.id
            assert data["connection_type"] == "oauth"  # From mock
    
    def test_create_api_key_connection_wrong_type(self, client, mock_user, auth_headers):
        """Test API key connection creation with wrong type"""
        connection_data = {
            "connection_type": "oauth",
            "api_key": "test_api_key",
            "zotero_user_id": "12345"
        }
        
        with patch('api.zotero_endpoints.get_current_user', return_value=mock_user):
            
            response = client.post("/api/zotero/connections", json=connection_data, headers=auth_headers)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "only supports API key connections" in response.json()["detail"]
    
    def test_create_api_key_connection_missing_fields(self, client, mock_user, auth_headers):
        """Test API key connection creation with missing fields"""
        connection_data = {
            "connection_type": "api_key"
            # Missing api_key and zotero_user_id
        }
        
        with patch('api.zotero_endpoints.get_current_user', return_value=mock_user):
            
            response = client.post("/api/zotero/connections", json=connection_data, headers=auth_headers)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "API key and Zotero user ID are required" in response.json()["detail"]
    
    def test_create_api_key_connection_invalid_key(self, client, mock_user, auth_headers):
        """Test API key connection creation with invalid key"""
        connection_data = {
            "connection_type": "api_key",
            "api_key": "invalid_key",
            "zotero_user_id": "12345"
        }
        
        with patch('api.zotero_endpoints.get_current_user', return_value=mock_user), \
             patch('api.zotero_endpoints.zotero_auth_service.create_api_key_connection', 
                   side_effect=ZoteroAuthError("Invalid API key")):
            
            response = client.post("/api/zotero/connections", json=connection_data, headers=auth_headers)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invalid API key" in response.json()["detail"]
    
    def test_get_connections_success(self, client, mock_user, mock_connection, auth_headers):
        """Test successful connections retrieval"""
        with patch('api.zotero_endpoints.get_current_user', return_value=mock_user), \
             patch('api.zotero_endpoints.zotero_auth_service.get_user_connections', return_value=[mock_connection]):
            
            response = client.get("/api/zotero/connections", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == mock_connection.id
    
    def test_get_connections_empty(self, client, mock_user, auth_headers):
        """Test connections retrieval with no connections"""
        with patch('api.zotero_endpoints.get_current_user', return_value=mock_user), \
             patch('api.zotero_endpoints.zotero_auth_service.get_user_connections', return_value=[]):
            
            response = client.get("/api/zotero/connections", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 0
    
    def test_get_connection_success(self, client, mock_user, mock_connection, auth_headers):
        """Test successful single connection retrieval"""
        with patch('api.zotero_endpoints.get_current_user', return_value=mock_user), \
             patch('api.zotero_endpoints.zotero_auth_service.get_user_connections', return_value=[mock_connection]):
            
            response = client.get(f"/api/zotero/connections/{mock_connection.id}", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == mock_connection.id
    
    def test_get_connection_not_found(self, client, mock_user, auth_headers):
        """Test connection retrieval with non-existent connection"""
        with patch('api.zotero_endpoints.get_current_user', return_value=mock_user), \
             patch('api.zotero_endpoints.zotero_auth_service.get_user_connections', return_value=[]):
            
            response = client.get("/api/zotero/connections/nonexistent", headers=auth_headers)
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Connection not found" in response.json()["detail"]
    
    def test_revoke_connection_success(self, client, mock_user, auth_headers):
        """Test successful connection revocation"""
        connection_id = "conn_123"
        
        with patch('api.zotero_endpoints.get_current_user', return_value=mock_user), \
             patch('api.zotero_endpoints.zotero_auth_service.revoke_connection', return_value=True):
            
            response = client.delete(f"/api/zotero/connections/{connection_id}", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "revoked successfully" in data["message"]
    
    def test_revoke_connection_not_found(self, client, mock_user, auth_headers):
        """Test connection revocation with non-existent connection"""
        connection_id = "nonexistent"
        
        with patch('api.zotero_endpoints.get_current_user', return_value=mock_user), \
             patch('api.zotero_endpoints.zotero_auth_service.revoke_connection', return_value=False):
            
            response = client.delete(f"/api/zotero/connections/{connection_id}", headers=auth_headers)
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Connection not found" in response.json()["detail"]
    
    def test_validate_connection_success(self, client, mock_user, mock_connection, auth_headers):
        """Test successful connection validation"""
        with patch('api.zotero_endpoints.get_current_user', return_value=mock_user), \
             patch('api.zotero_endpoints.zotero_auth_service.get_user_connections', return_value=[mock_connection]), \
             patch('api.zotero_endpoints.zotero_auth_service.validate_connection', return_value=True), \
             patch('api.zotero_endpoints.zotero_auth_service.refresh_token', return_value=True):
            
            response = client.post(f"/api/zotero/connections/{mock_connection.id}/validate", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["is_valid"] is True
            assert data["connection_id"] == mock_connection.id
            assert "validated_at" in data
    
    def test_validate_connection_invalid(self, client, mock_user, mock_connection, auth_headers):
        """Test connection validation with invalid connection"""
        with patch('api.zotero_endpoints.get_current_user', return_value=mock_user), \
             patch('api.zotero_endpoints.zotero_auth_service.get_user_connections', return_value=[mock_connection]), \
             patch('api.zotero_endpoints.zotero_auth_service.validate_connection', return_value=False):
            
            response = client.post(f"/api/zotero/connections/{mock_connection.id}/validate", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["is_valid"] is False
            assert "reconnect" in data["message"]
    
    def test_test_connection_success(self, client, mock_user, mock_connection, auth_headers):
        """Test successful connection test"""
        test_result = {
            "is_valid": True,
            "user_info": {"userID": "12345", "username": "testuser"},
            "test_timestamp": datetime.now().isoformat()
        }
        
        rate_limit_status = {
            "remaining": 1000,
            "reset_time": datetime.now().isoformat(),
            "requests_in_window": 5
        }
        
        with patch('api.zotero_endpoints.get_current_user', return_value=mock_user), \
             patch('api.zotero_endpoints.zotero_auth_service.get_user_connections', return_value=[mock_connection]), \
             patch('services.zotero.zotero_client.ZoteroAPIClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client.test_connection = AsyncMock(return_value=test_result)
            mock_client.get_rate_limit_status = Mock(return_value=rate_limit_status)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            response = client.post(f"/api/zotero/connections/{mock_connection.id}/test", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["connection_id"] == mock_connection.id
            assert data["test_result"]["is_valid"] is True
            assert "rate_limit_status" in data["test_result"]
            assert "connection_metadata" in data
    
    def test_test_connection_api_error(self, client, mock_user, mock_connection, auth_headers):
        """Test connection test with API error"""
        from services.zotero.zotero_client import ZoteroAPIError
        
        with patch('api.zotero_endpoints.get_current_user', return_value=mock_user), \
             patch('api.zotero_endpoints.zotero_auth_service.get_user_connections', return_value=[mock_connection]), \
             patch('services.zotero.zotero_client.ZoteroAPIClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client.test_connection = AsyncMock(side_effect=ZoteroAPIError("Unauthorized", 401))
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            response = client.post(f"/api/zotero/connections/{mock_connection.id}/test", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["test_result"]["is_valid"] is False
            assert data["test_result"]["error"]["status_code"] == 401
    
    def test_test_connection_not_found(self, client, mock_user, auth_headers):
        """Test connection test with non-existent connection"""
        with patch('api.zotero_endpoints.get_current_user', return_value=mock_user), \
             patch('api.zotero_endpoints.zotero_auth_service.get_user_connections', return_value=[]):
            
            response = client.post("/api/zotero/connections/nonexistent/test", headers=auth_headers)
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Connection not found" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__])