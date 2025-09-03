"""
Zotero API client for making authenticated requests to Zotero Web API
"""
import asyncio
import aiohttp
import logging
import secrets
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json

from core.config import settings

logger = logging.getLogger(__name__)


class ZoteroAPIError(Exception):
    """Custom exception for Zotero API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class ZoteroAPIClient:
    """
    Enhanced Zotero Web API client with OAuth 2.0 and API key authentication support
    """
    
    BASE_URL = "https://api.zotero.org"
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self._rate_limit_remaining = 1000
        self._rate_limit_reset = datetime.now()
        self._request_count = 0
        self._session_start_time = datetime.now()
        
        # Enhanced rate limiting with adaptive algorithms
        self._rate_limit_window = timedelta(seconds=60)  # 1 minute window
        self._max_requests_per_window = 1000
        self._request_timestamps: List[datetime] = []
        
        # Adaptive rate limiting
        self._adaptive_delay = 0.0  # Additional delay based on server responses
        self._consecutive_errors = 0
        self._last_error_time = None
        
        # Request statistics
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._retry_count = 0
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def _ensure_session(self):
        """Ensure aiohttp session is created"""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "User-Agent": f"AI Scholar/{settings.PROJECT_NAME}",
                    "Content-Type": "application/json"
                }
            )
    
    async def _check_rate_limit(self):
        """Enhanced rate limiting with sliding window and adaptive delays"""
        now = datetime.now()
        
        # Clean old timestamps outside the window
        cutoff_time = now - self._rate_limit_window
        self._request_timestamps = [
            ts for ts in self._request_timestamps 
            if ts > cutoff_time
        ]
        
        # Apply adaptive delay based on recent errors
        if self._adaptive_delay > 0:
            logger.debug(f"Applying adaptive delay: {self._adaptive_delay:.2f}s")
            await asyncio.sleep(self._adaptive_delay)
        
        # Check if we're approaching the rate limit
        current_requests = len(self._request_timestamps)
        if current_requests >= self._max_requests_per_window * 0.9:  # 90% threshold
            logger.warning(f"Approaching rate limit ({current_requests}/{self._max_requests_per_window}), slowing down requests")
            await asyncio.sleep(1)
        elif current_requests >= self._max_requests_per_window * 0.7:  # 70% threshold
            logger.debug("Rate limit at 70%, applying small delay")
            await asyncio.sleep(0.5)
        
        # Check server-imposed rate limits
        if self._rate_limit_remaining <= 0 and now < self._rate_limit_reset:
            wait_time = (self._rate_limit_reset - now).total_seconds()
            logger.warning(f"Server rate limit exceeded, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
        
        # Exponential backoff for consecutive errors
        if self._consecutive_errors > 0:
            backoff_delay = min(2 ** self._consecutive_errors, 60)  # Cap at 60 seconds
            logger.debug(f"Applying error backoff delay: {backoff_delay:.2f}s (consecutive errors: {self._consecutive_errors})")
            await asyncio.sleep(backoff_delay)
        
        # Add current request timestamp
        self._request_timestamps.append(now)
    
    def _update_rate_limit(self, headers: Dict[str, str]):
        """Update rate limit information from response headers"""
        try:
            if "X-RateLimit-Remaining" in headers:
                self._rate_limit_remaining = int(headers["X-RateLimit-Remaining"])
                logger.debug(f"Rate limit remaining: {self._rate_limit_remaining}")
            
            if "X-RateLimit-Reset" in headers:
                reset_timestamp = int(headers["X-RateLimit-Reset"])
                self._rate_limit_reset = datetime.fromtimestamp(reset_timestamp)
                logger.debug(f"Rate limit resets at: {self._rate_limit_reset}")
            
            # Log additional rate limit headers if present
            if "X-RateLimit-Limit" in headers:
                limit = headers["X-RateLimit-Limit"]
                logger.debug(f"Rate limit: {limit}")
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing rate limit headers: {e}")
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        return {
            "remaining": self._rate_limit_remaining,
            "reset_time": self._rate_limit_reset.isoformat(),
            "requests_in_window": len(self._request_timestamps),
            "window_size_seconds": self._rate_limit_window.total_seconds(),
            "session_request_count": self._request_count,
            "session_duration": (datetime.now() - self._session_start_time).total_seconds()
        }
    
    def get_client_statistics(self) -> Dict[str, Any]:
        """Get comprehensive client statistics"""
        session_duration = (datetime.now() - self._session_start_time).total_seconds()
        
        return {
            "session_info": {
                "start_time": self._session_start_time.isoformat(),
                "duration_seconds": session_duration,
                "requests_per_second": self._total_requests / max(session_duration, 1)
            },
            "request_statistics": {
                "total_requests": self._total_requests,
                "successful_requests": self._successful_requests,
                "failed_requests": self._failed_requests,
                "retry_count": self._retry_count,
                "success_rate": (self._successful_requests / max(self._total_requests, 1)) * 100
            },
            "rate_limiting": {
                "server_limit_remaining": self._rate_limit_remaining,
                "server_limit_reset": self._rate_limit_reset.isoformat(),
                "client_requests_in_window": len(self._request_timestamps),
                "adaptive_delay": self._adaptive_delay,
                "consecutive_errors": self._consecutive_errors
            },
            "error_info": {
                "last_error_time": self._last_error_time.isoformat() if self._last_error_time else None,
                "consecutive_errors": self._consecutive_errors
            }
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        auth_token: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Zotero API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            auth_token: Authentication token (OAuth token or API key)
            params: Query parameters
            data: Request body data
            headers: Additional headers
            
        Returns:
            Response data as dictionary
            
        Raises:
            ZoteroAPIError: If request fails
        """
        await self._ensure_session()
        await self._check_rate_limit()
        
        url = f"{self.BASE_URL}{endpoint}"
        
        # Prepare headers
        request_headers = {
            "Authorization": f"Bearer {auth_token}",
            "Zotero-API-Version": "3"
        }
        if headers:
            request_headers.update(headers)
        
        # Prepare request kwargs
        kwargs = {
            "headers": request_headers,
            "params": params or {}
        }
        
        if data:
            kwargs["json"] = data
        
        try:
            self._request_count += 1
            self._total_requests += 1
            logger.debug(f"Making {method} request to {url} (request #{self._request_count})")
            
            async with self.session.request(method, url, **kwargs) as response:
                # Update rate limit info
                self._update_rate_limit(dict(response.headers))
                
                # Handle response
                response_text = await response.text()
                
                # Update success/failure statistics
                if response.status < 400:
                    self._successful_requests += 1
                    self._consecutive_errors = 0  # Reset error counter on success
                    self._adaptive_delay = max(0, self._adaptive_delay - 0.1)  # Reduce adaptive delay
                else:
                    self._failed_requests += 1
                    self._consecutive_errors += 1
                    self._last_error_time = datetime.now()
                    
                    # Increase adaptive delay for server errors
                    if response.status >= 500:
                        self._adaptive_delay = min(self._adaptive_delay + 0.5, 10.0)  # Cap at 10 seconds
                
                if response.status == 200:
                    try:
                        return json.loads(response_text) if response_text else {}
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON response: {e}")
                        return {"raw_response": response_text}
                elif response.status == 204:
                    return {}  # No content
                elif response.status == 304:
                    return {"not_modified": True}
                elif response.status == 429:
                    # Rate limit exceeded - implement exponential backoff
                    retry_after = int(response.headers.get("Retry-After", 60))
                    backoff_time = min(retry_after, 300)  # Cap at 5 minutes
                    
                    logger.warning(f"Rate limit exceeded, backing off for {backoff_time} seconds")
                    await asyncio.sleep(backoff_time)
                    
                    # Retry the request once
                    return await self._make_request(method, endpoint, auth_token, params, data, headers)
                elif response.status == 401:
                    # Unauthorized - token may be invalid
                    raise ZoteroAPIError(
                        "Authentication failed - token may be invalid or expired",
                        status_code=response.status,
                        response_data={"error": "unauthorized", "raw_response": response_text}
                    )
                elif response.status == 403:
                    # Forbidden - insufficient permissions
                    raise ZoteroAPIError(
                        "Access forbidden - insufficient permissions",
                        status_code=response.status,
                        response_data={"error": "forbidden", "raw_response": response_text}
                    )
                elif response.status == 404:
                    # Not found
                    raise ZoteroAPIError(
                        "Resource not found",
                        status_code=response.status,
                        response_data={"error": "not_found", "raw_response": response_text}
                    )
                elif response.status >= 500:
                    # Server error - may be temporary
                    raise ZoteroAPIError(
                        f"Zotero server error: {response.status} {response.reason}",
                        status_code=response.status,
                        response_data={"error": "server_error", "raw_response": response_text}
                    )
                else:
                    # Other error response
                    try:
                        error_data = json.loads(response_text) if response_text else {}
                    except json.JSONDecodeError:
                        error_data = {"raw_error": response_text}
                    
                    raise ZoteroAPIError(
                        f"Zotero API request failed: {response.status} {response.reason}",
                        status_code=response.status,
                        response_data=error_data
                    )
                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            raise ZoteroAPIError(f"HTTP client error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in Zotero API request: {e}")
            raise ZoteroAPIError(f"Unexpected error: {e}")
    
    # User and Group Information
    async def get_user_info(self, auth_token: str, user_id: str) -> Dict[str, Any]:
        """Get user information"""
        return await self._make_request("GET", f"/users/{user_id}", auth_token)
    
    async def get_user_groups(self, auth_token: str, user_id: str) -> List[Dict[str, Any]]:
        """Get user's groups"""
        response = await self._make_request("GET", f"/users/{user_id}/groups", auth_token)
        return response if isinstance(response, list) else []
    
    # Library Operations
    async def get_libraries(self, auth_token: str, user_id: str) -> List[Dict[str, Any]]:
        """Get user's libraries (personal + groups)"""
        libraries = []
        
        # Add personal library
        user_info = await self.get_user_info(auth_token, user_id)
        libraries.append({
            "id": user_id,
            "type": "user",
            "name": f"{user_info.get('username', 'Personal')} Library",
            "owner": user_id
        })
        
        # Add group libraries
        groups = await self.get_user_groups(auth_token, user_id)
        for group in groups:
            libraries.append({
                "id": str(group["id"]),
                "type": "group", 
                "name": group["name"],
                "owner": group.get("owner"),
                "group_type": group.get("type"),
                "description": group.get("description")
            })
        
        return libraries
    
    # Collections
    async def get_collections(
        self,
        auth_token: str,
        library_type: str,
        library_id: str,
        since_version: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get collections from a library"""
        endpoint = f"/{library_type}s/{library_id}/collections"
        params = {}
        if since_version:
            params["since"] = since_version
        
        response = await self._make_request("GET", endpoint, auth_token, params=params)
        return response if isinstance(response, list) else []
    
    async def get_collection(
        self,
        auth_token: str,
        library_type: str,
        library_id: str,
        collection_key: str
    ) -> Dict[str, Any]:
        """Get a specific collection"""
        endpoint = f"/{library_type}s/{library_id}/collections/{collection_key}"
        return await self._make_request("GET", endpoint, auth_token)
    
    # Items
    async def get_items(
        self,
        auth_token: str,
        library_type: str,
        library_id: str,
        collection_key: Optional[str] = None,
        since_version: Optional[int] = None,
        limit: int = 100,
        start: int = 0,
        item_type: Optional[str] = None,
        tag: Optional[str] = None,
        q: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get items from a library or collection"""
        if collection_key:
            endpoint = f"/{library_type}s/{library_id}/collections/{collection_key}/items"
        else:
            endpoint = f"/{library_type}s/{library_id}/items"
        
        params = {
            "limit": limit,
            "start": start
        }
        
        if since_version:
            params["since"] = since_version
        if item_type:
            params["itemType"] = item_type
        if tag:
            params["tag"] = tag
        if q:
            params["q"] = q
        
        response = await self._make_request("GET", endpoint, auth_token, params=params)
        return response if isinstance(response, list) else []
    
    async def get_item(
        self,
        auth_token: str,
        library_type: str,
        library_id: str,
        item_key: str
    ) -> Dict[str, Any]:
        """Get a specific item"""
        endpoint = f"/{library_type}s/{library_id}/items/{item_key}"
        return await self._make_request("GET", endpoint, auth_token)
    
    async def get_item_children(
        self,
        auth_token: str,
        library_type: str,
        library_id: str,
        item_key: str
    ) -> List[Dict[str, Any]]:
        """Get child items (attachments, notes) of an item"""
        endpoint = f"/{library_type}s/{library_id}/items/{item_key}/children"
        response = await self._make_request("GET", endpoint, auth_token)
        return response if isinstance(response, list) else []
    
    # Tags
    async def get_tags(
        self,
        auth_token: str,
        library_type: str,
        library_id: str,
        since_version: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get tags from a library"""
        endpoint = f"/{library_type}s/{library_id}/tags"
        params = {}
        if since_version:
            params["since"] = since_version
        
        response = await self._make_request("GET", endpoint, auth_token, params=params)
        return response if isinstance(response, list) else []
    
    # Searches
    async def get_searches(
        self,
        auth_token: str,
        library_type: str,
        library_id: str,
        since_version: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get saved searches from a library"""
        endpoint = f"/{library_type}s/{library_id}/searches"
        params = {}
        if since_version:
            params["since"] = since_version
        
        response = await self._make_request("GET", endpoint, auth_token, params=params)
        return response if isinstance(response, list) else []
    
    # File Operations
    async def get_file_info(
        self,
        auth_token: str,
        library_type: str,
        library_id: str,
        item_key: str
    ) -> Dict[str, Any]:
        """Get file information for an attachment"""
        endpoint = f"/{library_type}s/{library_id}/items/{item_key}/file"
        return await self._make_request("GET", endpoint, auth_token)
    
    async def download_file(
        self,
        auth_token: str,
        library_type: str,
        library_id: str,
        item_key: str
    ) -> bytes:
        """Download file content for an attachment"""
        await self._ensure_session()
        
        endpoint = f"/{library_type}s/{library_id}/items/{item_key}/file"
        url = f"{self.BASE_URL}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Zotero-API-Version": "3"
        }
        
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise ZoteroAPIError(
                        f"Failed to download file: {response.status} {response.reason}",
                        status_code=response.status
                    )
        except aiohttp.ClientError as e:
            raise ZoteroAPIError(f"HTTP client error during file download: {e}")
    
    # Version Information
    async def get_library_version(
        self,
        auth_token: str,
        library_type: str,
        library_id: str
    ) -> int:
        """Get the current version of a library"""
        endpoint = f"/{library_type}s/{library_id}/items"
        params = {"limit": 1, "format": "versions"}
        
        response = await self._make_request("GET", endpoint, auth_token, params=params)
        
        # Extract version from Last-Modified-Version header or response
        if isinstance(response, dict) and "version" in response:
            return response["version"]
        
        # Fallback: make a simple request and check headers
        try:
            await self._make_request("HEAD", endpoint, auth_token, params={"limit": 1})
            # Version would be in headers, but we need to modify _make_request to return headers
            return 0  # Fallback
        except Exception:
            return 0
    
    # Utility Methods
    async def test_connection(self, auth_token: str, user_id: str) -> Dict[str, Any]:
        """
        Test if the connection and authentication are working
        
        Returns:
            Dictionary with connection test results
        """
        test_result = {
            "is_valid": False,
            "user_info": None,
            "error": None,
            "permissions": None,
            "test_timestamp": datetime.now().isoformat()
        }
        
        try:
            # Test basic user info access
            user_info = await self.get_user_info(auth_token, user_id)
            test_result["user_info"] = user_info
            test_result["is_valid"] = True
            
            # Test API key permissions if using API key
            if len(auth_token) == 32:  # API key format
                try:
                    permissions = await self.get_api_key_permissions(auth_token)
                    test_result["permissions"] = permissions
                except Exception as e:
                    logger.debug(f"Could not get API key permissions: {e}")
            
            logger.info(f"Connection test successful for user {user_id}")
            
        except ZoteroAPIError as e:
            test_result["error"] = {
                "message": e.message,
                "status_code": e.status_code,
                "response_data": e.response_data
            }
            logger.warning(f"Connection test failed for user {user_id}: {e.message}")
        except Exception as e:
            test_result["error"] = {
                "message": f"Unexpected error: {e}",
                "type": type(e).__name__
            }
            logger.error(f"Unexpected error in connection test: {e}")
        
        return test_result
    
    async def make_request_with_retry(
        self,
        method: str,
        endpoint: str,
        auth_token: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
        backoff_factor: float = 1.0
    ) -> Dict[str, Any]:
        """
        Make request with exponential backoff retry logic
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            auth_token: Authentication token
            params: Query parameters
            data: Request body data
            headers: Additional headers
            max_retries: Maximum number of retries
            backoff_factor: Backoff multiplier
            
        Returns:
            Response data
            
        Raises:
            ZoteroAPIError: If all retries fail
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await self._make_request(method, endpoint, auth_token, params, data, headers)
            
            except ZoteroAPIError as e:
                last_exception = e
                
                # Don't retry on authentication errors
                if e.status_code in [401, 403]:
                    raise
                
                # Don't retry on client errors (except rate limiting)
                if e.status_code and 400 <= e.status_code < 500 and e.status_code != 429:
                    raise
                
                if attempt < max_retries:
                    wait_time = backoff_factor * (2 ** attempt)
                    # Add jitter to prevent thundering herd
                    jitter = wait_time * 0.1 * (0.5 - secrets.randbits(1))
                    total_wait = wait_time + jitter
                    
                    self._retry_count += 1
                    logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {total_wait:.2f}s: {e.message}")
                    await asyncio.sleep(total_wait)
                else:
                    logger.error(f"Request failed after {max_retries + 1} attempts")
                    raise
            
            except Exception as e:
                last_exception = ZoteroAPIError(f"Unexpected error: {e}")
                
                if attempt < max_retries:
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Unexpected error (attempt {attempt + 1}/{max_retries + 1}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {max_retries + 1} attempts with unexpected error")
                    raise last_exception
        
        # This should never be reached, but just in case
        raise last_exception or ZoteroAPIError("Request failed after all retries")
    
    async def get_api_key_permissions(self, api_key: str) -> Dict[str, Any]:
        """Get permissions for an API key"""
        endpoint = "/keys/current"
        try:
            return await self._make_request("GET", endpoint, api_key)
        except ZoteroAPIError as e:
            if e.status_code == 403:
                return {"error": "Invalid API key"}
            raise