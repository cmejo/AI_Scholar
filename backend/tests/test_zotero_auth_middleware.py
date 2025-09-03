"""
Unit tests for Zotero authentication middleware
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from middleware.zotero_auth_middleware import (
    ZoteroAuthMiddleware,
    ZoteroPermissionChecker,
    get_current_user,
    get_zotero_connection,
    get_validated_zotero_client,
    require_library_access,
    require_item_access
)
from services.zotero.zotero_auth_service import ZoteroAuthError
from services.zotero.zotero_client import ZoteroAPIError
from models.zotero_models import ZoteroConnection


class TestZoteroAuthMiddleware:
    """Test cases for ZoteroAuthMiddleware"""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance"""
        return ZoteroAuthMiddleware()
    
    @pytest.fixture
    def mock_user(self):
        """Mock user object"""
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
    def mock_credentials(self):
        """Mock HTTP authorization credentials"""
        credentials = Mock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = "test_jwt_token"
        return credentials
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, middleware, mock_user, mock_credentials):
        """Test successful user authentication"""
        with patch.object(middleware.auth_service, 'verify_token', return_value=mock_user):
            result = await middleware.get_current_user(mock_credentials)
            assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, middleware, mock_credentials):
        """Test user authentication with invalid token"""
        with patch.object(middleware.auth_service, 'verify_token', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await middleware.get_current_user(mock_credentials)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid authentication credentials" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_service_error(self, middleware, mock_credentials):
        """Test user authentication with service error"""
        with patch.object(middleware.auth_service, 'verify_token', side_effect=Exception("Service error")):
            with pytest.raises(HTTPException) as exc_info:
                await middleware.get_current_user(mock_credentials)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_zotero_connection_success(self, middleware, mock_user, mock_connection):
        """Test successful Zotero connection retrieval"""
        with patch.object(middleware.zotero_auth_service, 'get_connection_with_valid_token', return_value=mock_connection):
            result = await middleware.get_zotero_connection(mock_user)
            assert result == mock_connection
    
    @pytest.mark.asyncio
    async def test_get_zotero_connection_not_found(self, middleware, mock_user):
        """Test Zotero connection retrieval with no connection"""
        with patch.object(middleware.zotero_auth_service, 'get_connection_with_valid_token', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await middleware.get_zotero_connection(mock_user)
            
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "No active Zotero connection found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_zotero_connection_auth_error(self, middleware, mock_user):
        """Test Zotero connection retrieval with auth error"""
        with patch.object(middleware.zotero_auth_service, 'get_connection_with_valid_token', 
                         side_effect=ZoteroAuthError("Token expired", "TOKEN_EXPIRED")):
            with pytest.raises(HTTPException) as exc_info:
                await middleware.get_zotero_connection(mock_user)
            
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "Zotero connection error" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_validate_zotero_credentials_success(self, middleware, mock_connection):
        """Test successful credential validation"""
        test_result = {
            "is_valid": True,
            "user_info": {"userID": "12345", "username": "testuser"},
            "test_timestamp": datetime.now().isoformat()
        }
        
        with patch('middleware.zotero_auth_middleware.ZoteroAPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.test_connection = AsyncMock(return_value=test_result)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            result = await middleware.validate_zotero_credentials(mock_connection)
            assert result == test_result
    
    @pytest.mark.asyncio
    async def test_validate_zotero_credentials_invalid(self, middleware, mock_connection):
        """Test credential validation with invalid credentials"""
        test_result = {
            "is_valid": False,
            "error": {"message": "Unauthorized", "status_code": 401}
        }
        
        with patch('middleware.zotero_auth_middleware.ZoteroAPIClient') as mock_client_class, \
             patch.object(middleware.zotero_auth_service, '_mark_connection_error') as mock_mark_error:
            
            mock_client = AsyncMock()
            mock_client.test_connection = AsyncMock(return_value=test_result)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            with pytest.raises(HTTPException) as exc_info:
                await middleware.validate_zotero_credentials(mock_connection)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "invalid or expired" in exc_info.value.detail
            mock_mark_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_zotero_credentials_api_error_401(self, middleware, mock_connection):
        """Test credential validation with 401 API error"""
        with patch('middleware.zotero_auth_middleware.ZoteroAPIClient') as mock_client_class, \
             patch.object(middleware.zotero_auth_service, '_mark_connection_error') as mock_mark_error:
            
            mock_client = AsyncMock()
            mock_client.test_connection = AsyncMock(side_effect=ZoteroAPIError("Unauthorized", 401))
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            with pytest.raises(HTTPException) as exc_info:
                await middleware.validate_zotero_credentials(mock_connection)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            mock_mark_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_zotero_credentials_api_error_403(self, middleware, mock_connection):
        """Test credential validation with 403 API error"""
        with patch('middleware.zotero_auth_middleware.ZoteroAPIClient') as mock_client_class, \
             patch.object(middleware.zotero_auth_service, '_mark_connection_error') as mock_mark_error:
            
            mock_client = AsyncMock()
            mock_client.test_connection = AsyncMock(side_effect=ZoteroAPIError("Forbidden", 403))
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            with pytest.raises(HTTPException) as exc_info:
                await middleware.validate_zotero_credentials(mock_connection)
            
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "Insufficient permissions" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_validate_zotero_credentials_api_error_500(self, middleware, mock_connection):
        """Test credential validation with 500 API error"""
        with patch('middleware.zotero_auth_middleware.ZoteroAPIClient') as mock_client_class, \
             patch.object(middleware.zotero_auth_service, '_mark_connection_error') as mock_mark_error:
            
            mock_client = AsyncMock()
            mock_client.test_connection = AsyncMock(side_effect=ZoteroAPIError("Server Error", 500))
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            with pytest.raises(HTTPException) as exc_info:
                await middleware.validate_zotero_credentials(mock_connection)
            
            assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert "temporarily unavailable" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_validated_zotero_client_success(self, middleware, mock_user, mock_connection):
        """Test successful validated client retrieval"""
        test_result = {"is_valid": True}
        
        with patch.object(middleware, 'get_zotero_connection', return_value=mock_connection), \
             patch.object(middleware, 'validate_zotero_credentials', return_value=test_result), \
             patch('middleware.zotero_auth_middleware.ZoteroAPIClient') as mock_client_class:
            
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            client, connection = await middleware.get_validated_zotero_client(mock_user)
            
            assert client == mock_client
            assert connection == mock_connection


class TestZoteroPermissionChecker:
    """Test cases for ZoteroPermissionChecker"""
    
    @pytest.fixture
    def permission_checker(self):
        """Create permission checker instance"""
        return ZoteroPermissionChecker()
    
    @pytest.fixture
    def mock_connection(self):
        """Mock Zotero connection"""
        connection = Mock(spec=ZoteroConnection)
        connection.zotero_user_id = "12345"
        connection.access_token = "test_token"
        return connection
    
    @pytest.mark.asyncio
    async def test_check_library_access_user_library_success(self, permission_checker, mock_connection):
        """Test successful user library access check"""
        result = await permission_checker.check_library_access(
            mock_connection, "user", "12345", "read"
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_library_access_user_library_denied(self, permission_checker, mock_connection):
        """Test denied user library access check"""
        result = await permission_checker.check_library_access(
            mock_connection, "user", "54321", "read"
        )
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_library_access_group_library_success(self, permission_checker, mock_connection):
        """Test successful group library access check"""
        groups = [{"id": 1, "name": "Group 1"}, {"id": 2, "name": "Group 2"}]
        
        with patch('middleware.zotero_auth_middleware.ZoteroAPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_user_groups = AsyncMock(return_value=groups)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            result = await permission_checker.check_library_access(
                mock_connection, "group", "1", "read"
            )
            assert result is True
    
    @pytest.mark.asyncio
    async def test_check_library_access_group_library_denied(self, permission_checker, mock_connection):
        """Test denied group library access check"""
        groups = [{"id": 1, "name": "Group 1"}, {"id": 2, "name": "Group 2"}]
        
        with patch('middleware.zotero_auth_middleware.ZoteroAPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_user_groups = AsyncMock(return_value=groups)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            result = await permission_checker.check_library_access(
                mock_connection, "group", "999", "read"
            )
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_library_access_error(self, permission_checker, mock_connection):
        """Test library access check with error"""
        with patch('middleware.zotero_auth_middleware.ZoteroAPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_user_groups = AsyncMock(side_effect=Exception("API error"))
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            result = await permission_checker.check_library_access(
                mock_connection, "group", "1", "read"
            )
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_item_access_success(self, permission_checker, mock_connection):
        """Test successful item access check"""
        item_data = {"key": "ITEM123", "data": {"title": "Test Item"}}
        
        with patch.object(permission_checker, 'check_library_access', return_value=True), \
             patch('middleware.zotero_auth_middleware.ZoteroAPIClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client.get_item = AsyncMock(return_value=item_data)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            result = await permission_checker.check_item_access(
                mock_connection, "user", "12345", "ITEM123", "read"
            )
            assert result is True
    
    @pytest.mark.asyncio
    async def test_check_item_access_no_library_access(self, permission_checker, mock_connection):
        """Test item access check with no library access"""
        with patch.object(permission_checker, 'check_library_access', return_value=False):
            result = await permission_checker.check_item_access(
                mock_connection, "user", "54321", "ITEM123", "read"
            )
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_item_access_item_not_found(self, permission_checker, mock_connection):
        """Test item access check with item not found"""
        with patch.object(permission_checker, 'check_library_access', return_value=True), \
             patch('middleware.zotero_auth_middleware.ZoteroAPIClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client.get_item = AsyncMock(side_effect=ZoteroAPIError("Not Found", 404))
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            result = await permission_checker.check_item_access(
                mock_connection, "user", "12345", "NONEXISTENT", "read"
            )
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_item_access_permission_denied(self, permission_checker, mock_connection):
        """Test item access check with permission denied"""
        with patch.object(permission_checker, 'check_library_access', return_value=True), \
             patch('middleware.zotero_auth_middleware.ZoteroAPIClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client.get_item = AsyncMock(side_effect=ZoteroAPIError("Forbidden", 403))
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            result = await permission_checker.check_item_access(
                mock_connection, "user", "12345", "ITEM123", "read"
            )
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_item_access_api_error(self, permission_checker, mock_connection):
        """Test item access check with API error"""
        with patch.object(permission_checker, 'check_library_access', return_value=True), \
             patch('middleware.zotero_auth_middleware.ZoteroAPIClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client.get_item = AsyncMock(side_effect=ZoteroAPIError("Server Error", 500))
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            with pytest.raises(ZoteroAPIError):
                await permission_checker.check_item_access(
                    mock_connection, "user", "12345", "ITEM123", "read"
                )


class TestDependencyFunctions:
    """Test cases for FastAPI dependency functions"""
    
    @pytest.fixture
    def mock_user(self):
        """Mock user object"""
        user = Mock()
        user.id = "test_user_123"
        return user
    
    @pytest.fixture
    def mock_connection(self):
        """Mock Zotero connection"""
        connection = Mock(spec=ZoteroConnection)
        connection.id = "conn_123"
        connection.user_id = "test_user_123"
        connection.zotero_user_id = "12345"
        return connection
    
    @pytest.fixture
    def mock_credentials(self):
        """Mock HTTP authorization credentials"""
        credentials = Mock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = "test_jwt_token"
        return credentials
    
    @pytest.mark.asyncio
    async def test_get_current_user_dependency(self, mock_user, mock_credentials):
        """Test get_current_user dependency function"""
        with patch('middleware.zotero_auth_middleware.zotero_auth_middleware.get_current_user', return_value=mock_user):
            result = await get_current_user(mock_credentials)
            assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_get_zotero_connection_dependency(self, mock_user, mock_connection):
        """Test get_zotero_connection dependency function"""
        with patch('middleware.zotero_auth_middleware.zotero_auth_middleware.get_zotero_connection', return_value=mock_connection):
            result = await get_zotero_connection(mock_user)
            assert result == mock_connection
    
    @pytest.mark.asyncio
    async def test_get_validated_zotero_client_dependency(self, mock_user):
        """Test get_validated_zotero_client dependency function"""
        mock_client = Mock()
        mock_connection = Mock()
        
        with patch('middleware.zotero_auth_middleware.zotero_auth_middleware.get_validated_zotero_client', 
                  return_value=(mock_client, mock_connection)):
            client, connection = await get_validated_zotero_client(mock_user)
            assert client == mock_client
            assert connection == mock_connection
    
    @pytest.mark.asyncio
    async def test_require_library_access_success(self, mock_connection):
        """Test require_library_access dependency with success"""
        with patch('middleware.zotero_auth_middleware.permission_checker.check_library_access', return_value=True):
            result = await require_library_access("user", "12345", "read", mock_connection)
            assert result == mock_connection
    
    @pytest.mark.asyncio
    async def test_require_library_access_denied(self, mock_connection):
        """Test require_library_access dependency with access denied"""
        with patch('middleware.zotero_auth_middleware.permission_checker.check_library_access', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await require_library_access("user", "54321", "read", mock_connection)
            
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "Access denied" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_require_item_access_success(self, mock_connection):
        """Test require_item_access dependency with success"""
        with patch('middleware.zotero_auth_middleware.permission_checker.check_item_access', return_value=True):
            result = await require_item_access("user", "12345", "ITEM123", "read", mock_connection)
            assert result == mock_connection
    
    @pytest.mark.asyncio
    async def test_require_item_access_denied(self, mock_connection):
        """Test require_item_access dependency with access denied"""
        with patch('middleware.zotero_auth_middleware.permission_checker.check_item_access', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await require_item_access("user", "12345", "ITEM123", "read", mock_connection)
            
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "Access denied" in exc_info.value.detail


if __name__ == "__main__":
    pytest.main([__file__])