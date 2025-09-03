"""
Unit tests for Zotero API client
"""
import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from aiohttp import ClientError, ClientTimeout
import aiohttp

from services.zotero.zotero_client import ZoteroAPIClient, ZoteroAPIError


class TestZoteroAPIClient:
    """Test cases for ZoteroAPIClient"""
    
    @pytest.fixture
    async def client(self):
        """Create ZoteroAPIClient instance for testing"""
        client = ZoteroAPIClient()
        yield client
        # Cleanup
        if client.session and not client.session.closed:
            await client.session.close()
    
    @pytest.fixture
    def mock_response(self):
        """Create mock HTTP response"""
        response = AsyncMock()
        response.status = 200
        response.headers = {}
        response.text = AsyncMock(return_value='{"test": "data"}')
        response.reason = "OK"
        return response
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality"""
        async with ZoteroAPIClient() as client:
            assert client.session is not None
            assert not client.session.closed
        
        # Session should be closed after context exit
        assert client.session.closed
    
    @pytest.mark.asyncio
    async def test_ensure_session(self, client):
        """Test session creation"""
        await client._ensure_session()
        
        assert client.session is not None
        assert not client.session.closed
        assert "User-Agent" in client.session._default_headers
        assert "Content-Type" in client.session._default_headers
    
    def test_rate_limit_status(self, client):
        """Test rate limit status reporting"""
        status = client.get_rate_limit_status()
        
        assert "remaining" in status
        assert "reset_time" in status
        assert "requests_in_window" in status
        assert "window_size_seconds" in status
        assert "session_request_count" in status
        assert "session_duration" in status
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_normal(self, client):
        """Test rate limiting under normal conditions"""
        # Should not block under normal conditions
        start_time = datetime.now()
        await client._check_rate_limit()
        end_time = datetime.now()
        
        # Should complete quickly
        assert (end_time - start_time).total_seconds() < 0.1
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_approaching_limit(self, client):
        """Test rate limiting when approaching limit"""
        # Simulate many requests in the window
        now = datetime.now()
        client._request_timestamps = [now - timedelta(seconds=i) for i in range(950)]
        
        start_time = datetime.now()
        await client._check_rate_limit()
        end_time = datetime.now()
        
        # Should add some delay
        assert (end_time - start_time).total_seconds() >= 1.0
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_server_limit(self, client):
        """Test rate limiting when server limit is exceeded"""
        # Simulate server rate limit
        client._rate_limit_remaining = 0
        client._rate_limit_reset = datetime.now() + timedelta(seconds=2)
        
        start_time = datetime.now()
        await client._check_rate_limit()
        end_time = datetime.now()
        
        # Should wait for rate limit reset
        assert (end_time - start_time).total_seconds() >= 2.0
    
    def test_update_rate_limit_headers(self, client):
        """Test rate limit header parsing"""
        headers = {
            "X-RateLimit-Remaining": "500",
            "X-RateLimit-Reset": str(int((datetime.now() + timedelta(hours=1)).timestamp())),
            "X-RateLimit-Limit": "1000"
        }
        
        client._update_rate_limit(headers)
        
        assert client._rate_limit_remaining == 500
        assert client._rate_limit_reset > datetime.now()
    
    def test_update_rate_limit_invalid_headers(self, client):
        """Test rate limit header parsing with invalid data"""
        headers = {
            "X-RateLimit-Remaining": "invalid",
            "X-RateLimit-Reset": "not_a_timestamp"
        }
        
        # Should not raise exception
        client._update_rate_limit(headers)
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, client, mock_response):
        """Test successful API request"""
        with patch.object(client, '_ensure_session'), \
             patch.object(client, '_check_rate_limit'), \
             patch('aiohttp.ClientSession.request') as mock_request:
            
            mock_request.return_value.__aenter__.return_value = mock_response
            client.session = Mock()
            
            result = await client._make_request("GET", "/test", "token123")
            
            assert result == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_make_request_no_content(self, client):
        """Test API request with no content response"""
        mock_response = AsyncMock()
        mock_response.status = 204
        mock_response.headers = {}
        
        with patch.object(client, '_ensure_session'), \
             patch.object(client, '_check_rate_limit'), \
             patch('aiohttp.ClientSession.request') as mock_request:
            
            mock_request.return_value.__aenter__.return_value = mock_response
            client.session = Mock()
            
            result = await client._make_request("DELETE", "/test", "token123")
            
            assert result == {}
    
    @pytest.mark.asyncio
    async def test_make_request_not_modified(self, client):
        """Test API request with not modified response"""
        mock_response = AsyncMock()
        mock_response.status = 304
        mock_response.headers = {}
        
        with patch.object(client, '_ensure_session'), \
             patch.object(client, '_check_rate_limit'), \
             patch('aiohttp.ClientSession.request') as mock_request:
            
            mock_request.return_value.__aenter__.return_value = mock_response
            client.session = Mock()
            
            result = await client._make_request("GET", "/test", "token123")
            
            assert result == {"not_modified": True}
    
    @pytest.mark.asyncio
    async def test_make_request_rate_limit_exceeded(self, client):
        """Test API request with rate limit exceeded"""
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.headers = {"Retry-After": "2"}
        mock_response.text = AsyncMock(return_value="Rate limit exceeded")
        
        # Mock successful retry
        mock_success_response = AsyncMock()
        mock_success_response.status = 200
        mock_success_response.headers = {}
        mock_success_response.text = AsyncMock(return_value='{"success": true}')
        
        with patch.object(client, '_ensure_session'), \
             patch.object(client, '_check_rate_limit'), \
             patch('aiohttp.ClientSession.request') as mock_request, \
             patch('asyncio.sleep') as mock_sleep:
            
            # First call returns 429, second call succeeds
            mock_request.return_value.__aenter__.return_value = mock_response
            client.session = Mock()
            
            # Mock the recursive call to succeed
            with patch.object(client, '_make_request', side_effect=[
                client._make_request("GET", "/test", "token123"),  # Original call
                {"success": True}  # Retry call
            ]) as mock_recursive:
                mock_recursive.side_effect = [mock_recursive.side_effect[1]]  # Only return success
                
                result = await client._make_request("GET", "/test", "token123")
                
                mock_sleep.assert_called_once_with(2)
    
    @pytest.mark.asyncio
    async def test_make_request_unauthorized(self, client):
        """Test API request with unauthorized response"""
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value="Unauthorized")
        mock_response.reason = "Unauthorized"
        
        with patch.object(client, '_ensure_session'), \
             patch.object(client, '_check_rate_limit'), \
             patch('aiohttp.ClientSession.request') as mock_request:
            
            mock_request.return_value.__aenter__.return_value = mock_response
            client.session = Mock()
            
            with pytest.raises(ZoteroAPIError) as exc_info:
                await client._make_request("GET", "/test", "invalid_token")
            
            assert exc_info.value.status_code == 401
            assert "Authentication failed" in exc_info.value.message
    
    @pytest.mark.asyncio
    async def test_make_request_forbidden(self, client):
        """Test API request with forbidden response"""
        mock_response = AsyncMock()
        mock_response.status = 403
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value="Forbidden")
        mock_response.reason = "Forbidden"
        
        with patch.object(client, '_ensure_session'), \
             patch.object(client, '_check_rate_limit'), \
             patch('aiohttp.ClientSession.request') as mock_request:
            
            mock_request.return_value.__aenter__.return_value = mock_response
            client.session = Mock()
            
            with pytest.raises(ZoteroAPIError) as exc_info:
                await client._make_request("GET", "/test", "token123")
            
            assert exc_info.value.status_code == 403
            assert "Access forbidden" in exc_info.value.message
    
    @pytest.mark.asyncio
    async def test_make_request_not_found(self, client):
        """Test API request with not found response"""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value="Not Found")
        mock_response.reason = "Not Found"
        
        with patch.object(client, '_ensure_session'), \
             patch.object(client, '_check_rate_limit'), \
             patch('aiohttp.ClientSession.request') as mock_request:
            
            mock_request.return_value.__aenter__.return_value = mock_response
            client.session = Mock()
            
            with pytest.raises(ZoteroAPIError) as exc_info:
                await client._make_request("GET", "/test", "token123")
            
            assert exc_info.value.status_code == 404
            assert "Resource not found" in exc_info.value.message
    
    @pytest.mark.asyncio
    async def test_make_request_server_error(self, client):
        """Test API request with server error"""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        mock_response.reason = "Internal Server Error"
        
        with patch.object(client, '_ensure_session'), \
             patch.object(client, '_check_rate_limit'), \
             patch('aiohttp.ClientSession.request') as mock_request:
            
            mock_request.return_value.__aenter__.return_value = mock_response
            client.session = Mock()
            
            with pytest.raises(ZoteroAPIError) as exc_info:
                await client._make_request("GET", "/test", "token123")
            
            assert exc_info.value.status_code == 500
            assert "server error" in exc_info.value.message.lower()
    
    @pytest.mark.asyncio
    async def test_make_request_network_error(self, client):
        """Test API request with network error"""
        with patch.object(client, '_ensure_session'), \
             patch.object(client, '_check_rate_limit'), \
             patch('aiohttp.ClientSession.request') as mock_request:
            
            mock_request.side_effect = ClientError("Network error")
            client.session = Mock()
            
            with pytest.raises(ZoteroAPIError) as exc_info:
                await client._make_request("GET", "/test", "token123")
            
            assert "HTTP client error" in exc_info.value.message
    
    @pytest.mark.asyncio
    async def test_make_request_json_decode_error(self, client):
        """Test API request with invalid JSON response"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value="invalid json")
        
        with patch.object(client, '_ensure_session'), \
             patch.object(client, '_check_rate_limit'), \
             patch('aiohttp.ClientSession.request') as mock_request:
            
            mock_request.return_value.__aenter__.return_value = mock_response
            client.session = Mock()
            
            result = await client._make_request("GET", "/test", "token123")
            
            assert result == {"raw_response": "invalid json"}
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, client):
        """Test successful connection test"""
        user_info = {"userID": "12345", "username": "testuser"}
        
        with patch.object(client, 'get_user_info', return_value=user_info):
            result = await client.test_connection("token123", "12345")
            
            assert result["is_valid"] is True
            assert result["user_info"] == user_info
            assert "test_timestamp" in result
    
    @pytest.mark.asyncio
    async def test_test_connection_failure(self, client):
        """Test failed connection test"""
        with patch.object(client, 'get_user_info', side_effect=ZoteroAPIError("Unauthorized", 401)):
            result = await client.test_connection("invalid_token", "12345")
            
            assert result["is_valid"] is False
            assert result["error"] is not None
            assert result["error"]["status_code"] == 401
    
    @pytest.mark.asyncio
    async def test_test_connection_api_key_permissions(self, client):
        """Test connection test with API key permissions"""
        user_info = {"userID": "12345", "username": "testuser"}
        permissions = {"library": "read", "notes": "write"}
        api_key = "a" * 32  # 32-character API key
        
        with patch.object(client, 'get_user_info', return_value=user_info), \
             patch.object(client, 'get_api_key_permissions', return_value=permissions):
            
            result = await client.test_connection(api_key, "12345")
            
            assert result["is_valid"] is True
            assert result["permissions"] == permissions
    
    @pytest.mark.asyncio
    async def test_make_request_with_retry_success_first_try(self, client):
        """Test retry logic with success on first try"""
        expected_result = {"test": "data"}
        
        with patch.object(client, '_make_request', return_value=expected_result):
            result = await client.make_request_with_retry("GET", "/test", "token123")
            
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_make_request_with_retry_success_after_retry(self, client):
        """Test retry logic with success after retry"""
        expected_result = {"test": "data"}
        
        with patch.object(client, '_make_request', side_effect=[
            ZoteroAPIError("Server error", 500),
            expected_result
        ]), patch('asyncio.sleep'):
            
            result = await client.make_request_with_retry("GET", "/test", "token123", max_retries=2)
            
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_make_request_with_retry_auth_error_no_retry(self, client):
        """Test retry logic doesn't retry on auth errors"""
        with patch.object(client, '_make_request', side_effect=ZoteroAPIError("Unauthorized", 401)):
            
            with pytest.raises(ZoteroAPIError) as exc_info:
                await client.make_request_with_retry("GET", "/test", "token123", max_retries=3)
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_make_request_with_retry_client_error_no_retry(self, client):
        """Test retry logic doesn't retry on client errors (except 429)"""
        with patch.object(client, '_make_request', side_effect=ZoteroAPIError("Bad Request", 400)):
            
            with pytest.raises(ZoteroAPIError) as exc_info:
                await client.make_request_with_retry("GET", "/test", "token123", max_retries=3)
            
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_make_request_with_retry_max_retries_exceeded(self, client):
        """Test retry logic when max retries exceeded"""
        with patch.object(client, '_make_request', side_effect=ZoteroAPIError("Server error", 500)), \
             patch('asyncio.sleep'):
            
            with pytest.raises(ZoteroAPIError) as exc_info:
                await client.make_request_with_retry("GET", "/test", "token123", max_retries=2)
            
            assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_make_request_with_retry_exponential_backoff(self, client):
        """Test retry logic uses exponential backoff"""
        with patch.object(client, '_make_request', side_effect=[
            ZoteroAPIError("Server error", 500),
            ZoteroAPIError("Server error", 500),
            {"success": True}
        ]), patch('asyncio.sleep') as mock_sleep:
            
            result = await client.make_request_with_retry("GET", "/test", "token123", max_retries=3, backoff_factor=1.0)
            
            # Should have called sleep with exponential backoff
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(1.0)  # 1.0 * 2^0
            mock_sleep.assert_any_call(2.0)  # 1.0 * 2^1
    
    @pytest.mark.asyncio
    async def test_get_user_info(self, client):
        """Test getting user info"""
        expected_result = {"userID": "12345", "username": "testuser"}
        
        with patch.object(client, '_make_request', return_value=expected_result):
            result = await client.get_user_info("token123", "12345")
            
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_get_user_groups(self, client):
        """Test getting user groups"""
        expected_result = [{"id": 1, "name": "Group 1"}, {"id": 2, "name": "Group 2"}]
        
        with patch.object(client, '_make_request', return_value=expected_result):
            result = await client.get_user_groups("token123", "12345")
            
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_get_user_groups_non_list_response(self, client):
        """Test getting user groups with non-list response"""
        with patch.object(client, '_make_request', return_value={"error": "not a list"}):
            result = await client.get_user_groups("token123", "12345")
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_libraries(self, client):
        """Test getting user libraries"""
        user_info = {"userID": "12345", "username": "testuser"}
        groups = [{"id": 1, "name": "Group 1", "type": "PublicOpen"}]
        
        with patch.object(client, 'get_user_info', return_value=user_info), \
             patch.object(client, 'get_user_groups', return_value=groups):
            
            result = await client.get_libraries("token123", "12345")
            
            assert len(result) == 2  # Personal + 1 group
            assert result[0]["type"] == "user"
            assert result[1]["type"] == "group"
    
    @pytest.mark.asyncio
    async def test_get_collections(self, client):
        """Test getting collections"""
        expected_result = [{"key": "ABC123", "data": {"name": "Collection 1"}}]
        
        with patch.object(client, '_make_request', return_value=expected_result):
            result = await client.get_collections("token123", "user", "12345")
            
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_get_collections_with_version(self, client):
        """Test getting collections with since version"""
        expected_result = [{"key": "ABC123", "data": {"name": "Collection 1"}}]
        
        with patch.object(client, '_make_request', return_value=expected_result) as mock_request:
            result = await client.get_collections("token123", "user", "12345", since_version=100)
            
            # Verify since parameter was passed
            mock_request.assert_called_once()
            args, kwargs = mock_request.call_args
            assert kwargs["params"]["since"] == 100
    
    @pytest.mark.asyncio
    async def test_get_items(self, client):
        """Test getting items"""
        expected_result = [{"key": "ITEM123", "data": {"title": "Test Item"}}]
        
        with patch.object(client, '_make_request', return_value=expected_result):
            result = await client.get_items("token123", "user", "12345")
            
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_get_items_with_filters(self, client):
        """Test getting items with filters"""
        expected_result = [{"key": "ITEM123", "data": {"title": "Test Item"}}]
        
        with patch.object(client, '_make_request', return_value=expected_result) as mock_request:
            result = await client.get_items(
                "token123", "user", "12345",
                collection_key="COLL123",
                since_version=50,
                limit=50,
                start=10,
                item_type="journalArticle",
                tag="important",
                q="search query"
            )
            
            # Verify parameters were passed correctly
            mock_request.assert_called_once()
            args, kwargs = mock_request.call_args
            params = kwargs["params"]
            
            assert params["since"] == 50
            assert params["limit"] == 50
            assert params["start"] == 10
            assert params["itemType"] == "journalArticle"
            assert params["tag"] == "important"
            assert params["q"] == "search query"
    
    @pytest.mark.asyncio
    async def test_download_file(self, client):
        """Test downloading file"""
        expected_content = b"file content"
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=expected_content)
        
        with patch.object(client, '_ensure_session'), \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            mock_get.return_value.__aenter__.return_value = mock_response
            client.session = Mock()
            
            result = await client.download_file("token123", "user", "12345", "ITEM123")
            
            assert result == expected_content
    
    @pytest.mark.asyncio
    async def test_download_file_error(self, client):
        """Test downloading file with error"""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.reason = "Not Found"
        
        with patch.object(client, '_ensure_session'), \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            mock_get.return_value.__aenter__.return_value = mock_response
            client.session = Mock()
            
            with pytest.raises(ZoteroAPIError) as exc_info:
                await client.download_file("token123", "user", "12345", "ITEM123")
            
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_api_key_permissions(self, client):
        """Test getting API key permissions"""
        expected_result = {"library": "read", "notes": "write"}
        
        with patch.object(client, '_make_request', return_value=expected_result):
            result = await client.get_api_key_permissions("api_key_123")
            
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_get_api_key_permissions_invalid(self, client):
        """Test getting API key permissions with invalid key"""
        with patch.object(client, '_make_request', side_effect=ZoteroAPIError("Forbidden", 403)):
            result = await client.get_api_key_permissions("invalid_key")
            
            assert result == {"error": "Invalid API key"}
    
    @pytest.mark.asyncio
    async def test_adaptive_rate_limiting(self, client):
        """Test adaptive rate limiting based on errors"""
        # Simulate consecutive errors
        client._consecutive_errors = 3
        client._adaptive_delay = 2.0
        
        start_time = datetime.now()
        await client._check_rate_limit()
        end_time = datetime.now()
        
        # Should apply both adaptive delay and exponential backoff
        total_delay = (end_time - start_time).total_seconds()
        assert total_delay >= 2.0  # Adaptive delay
        assert total_delay >= 8.0  # Exponential backoff (2^3)
    
    def test_client_statistics(self, client):
        """Test client statistics collection"""
        # Simulate some activity
        client._total_requests = 100
        client._successful_requests = 90
        client._failed_requests = 10
        client._retry_count = 5
        client._consecutive_errors = 2
        client._adaptive_delay = 1.5
        
        stats = client.get_client_statistics()
        
        # Verify statistics structure
        assert "session_info" in stats
        assert "request_statistics" in stats
        assert "rate_limiting" in stats
        assert "error_info" in stats
        
        # Verify request statistics
        request_stats = stats["request_statistics"]
        assert request_stats["total_requests"] == 100
        assert request_stats["successful_requests"] == 90
        assert request_stats["failed_requests"] == 10
        assert request_stats["retry_count"] == 5
        assert request_stats["success_rate"] == 90.0
        
        # Verify rate limiting info
        rate_limit_info = stats["rate_limiting"]
        assert rate_limit_info["adaptive_delay"] == 1.5
        assert rate_limit_info["consecutive_errors"] == 2
    
    @pytest.mark.asyncio
    async def test_request_statistics_tracking(self, client, mock_response):
        """Test that request statistics are properly tracked"""
        initial_total = client._total_requests
        initial_successful = client._successful_requests
        
        with patch.object(client, '_ensure_session'), \
             patch.object(client, '_check_rate_limit'), \
             patch('aiohttp.ClientSession.request') as mock_request:
            
            mock_request.return_value.__aenter__.return_value = mock_response
            client.session = Mock()
            
            await client._make_request("GET", "/test", "token123")
            
            # Verify statistics were updated
            assert client._total_requests == initial_total + 1
            assert client._successful_requests == initial_successful + 1
            assert client._consecutive_errors == 0  # Should reset on success
    
    @pytest.mark.asyncio
    async def test_error_statistics_tracking(self, client):
        """Test that error statistics are properly tracked"""
        initial_total = client._total_requests
        initial_failed = client._failed_requests
        initial_consecutive = client._consecutive_errors
        
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value="Server Error")
        mock_response.reason = "Internal Server Error"
        
        with patch.object(client, '_ensure_session'), \
             patch.object(client, '_check_rate_limit'), \
             patch('aiohttp.ClientSession.request') as mock_request:
            
            mock_request.return_value.__aenter__.return_value = mock_response
            client.session = Mock()
            
            with pytest.raises(ZoteroAPIError):
                await client._make_request("GET", "/test", "token123")
            
            # Verify error statistics were updated
            assert client._total_requests == initial_total + 1
            assert client._failed_requests == initial_failed + 1
            assert client._consecutive_errors == initial_consecutive + 1
            assert client._adaptive_delay > 0  # Should increase for server errors
    
    @pytest.mark.asyncio
    async def test_retry_with_jitter(self, client):
        """Test retry logic includes jitter to prevent thundering herd"""
        retry_times = []
        
        async def mock_sleep(duration):
            retry_times.append(duration)
        
        with patch.object(client, '_make_request', side_effect=[
            ZoteroAPIError("Server error", 500),
            ZoteroAPIError("Server error", 500),
            {"success": True}
        ]), patch('asyncio.sleep', side_effect=mock_sleep):
            
            result = await client.make_request_with_retry("GET", "/test", "token123", max_retries=3, backoff_factor=1.0)
            
            # Should have made 2 retry sleeps
            assert len(retry_times) == 2
            
            # First retry should be around 1.0 seconds (with jitter)
            assert 0.9 <= retry_times[0] <= 1.1
            
            # Second retry should be around 2.0 seconds (with jitter)
            assert 1.8 <= retry_times[1] <= 2.2
            
            # Verify retry count was tracked
            assert client._retry_count >= 2
    
    @pytest.mark.asyncio
    async def test_rate_limit_window_cleanup(self, client):
        """Test that old request timestamps are cleaned up"""
        # Add some old timestamps
        old_time = datetime.now() - timedelta(minutes=2)
        recent_time = datetime.now() - timedelta(seconds=30)
        
        client._request_timestamps = [old_time, recent_time]
        
        await client._check_rate_limit()
        
        # Old timestamp should be removed, recent one should remain
        assert len(client._request_timestamps) == 2  # recent + new one from _check_rate_limit
        assert old_time not in client._request_timestamps
        assert recent_time in client._request_timestamps


if __name__ == "__main__":
    pytest.main([__file__])