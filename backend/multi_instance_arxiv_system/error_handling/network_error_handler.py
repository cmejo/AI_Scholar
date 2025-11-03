"""
Network Error Handler for Multi-Instance ArXiv System.

This module provides specialized handling for network-related errors including
connection timeouts, HTTP errors, rate limiting, and DNS resolution issues.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import asyncio
import aiohttp
import time
import random
from dataclasses import dataclass
from enum import Enum

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.error_handling.error_models import ProcessingError, ErrorType
except ImportError as e:
    print(f"Import error: {e}")
    # Create minimal fallback classes for testing
    class ProcessingError:
        def __init__(self, *args, **kwargs): pass
    class ErrorType:
        CONNECTION_TIMEOUT = "connection_timeout"
        HTTP_ERROR = "http_error"

logger = logging.getLogger(__name__)


class NetworkError(Exception):
    """Custom network error exception."""
    
    def __init__(self, message: str, error_type: ErrorType, status_code: Optional[int] = None):
        super().__init__(message)
        self.error_type = error_type
        self.status_code = status_code


@dataclass
class RetryConfig:
    """Configuration for network retry logic."""
    
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    
    # HTTP status codes that should be retried
    retryable_status_codes: List[int] = None
    
    def __post_init__(self):
        if self.retryable_status_codes is None:
            self.retryable_status_codes = [408, 429, 500, 502, 503, 504]


class NetworkErrorHandler:
    """
    Specialized handler for network-related errors.
    
    Provides exponential backoff, rate limiting awareness, and intelligent
    retry strategies for different types of network failures.
    """
    
    def __init__(self, instance_name: str, retry_config: Optional[RetryConfig] = None):
        self.instance_name = instance_name
        self.retry_config = retry_config or RetryConfig()
        
        # Rate limiting tracking
        self.rate_limit_resets: Dict[str, datetime] = {}
        self.request_counts: Dict[str, int] = {}
        
        # Connection pooling
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Statistics
        self.total_requests = 0
        self.failed_requests = 0
        self.retried_requests = 0
        
        logger.info(f"NetworkErrorHandler initialized for {instance_name}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
    
    async def start(self) -> None:
        """Start the network error handler."""
        
        if self.session is None:
            # Configure session with appropriate timeouts and limits
            timeout = aiohttp.ClientTimeout(
                total=300,  # 5 minutes total
                connect=30,  # 30 seconds to connect
                sock_read=60  # 60 seconds to read
            )
            
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection pool size
                limit_per_host=10,  # Connections per host
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True
            )
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    'User-Agent': f'ArXiv-Multi-Instance-System/{self.instance_name}'
                }
            )
        
        logger.info(f"NetworkErrorHandler started for {self.instance_name}")
    
    async def stop(self) -> None:
        """Stop the network error handler."""
        
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info(f"NetworkErrorHandler stopped for {self.instance_name}")
    
    async def handle_error(self, error: ProcessingError) -> bool:
        """
        Handle a network error with appropriate recovery strategy.
        
        Args:
            error: The network error to handle
            
        Returns:
            True if recovery was successful, False otherwise
        """
        
        logger.info(f"Handling network error: {error.error_type.value}")
        
        # Determine recovery strategy based on error type
        if error.error_type == ErrorType.RATE_LIMIT_EXCEEDED:
            return await self._handle_rate_limit_error(error)
        elif error.error_type == ErrorType.CONNECTION_TIMEOUT:
            return await self._handle_timeout_error(error)
        elif error.error_type == ErrorType.HTTP_ERROR:
            return await self._handle_http_error(error)
        elif error.error_type == ErrorType.DNS_RESOLUTION:
            return await self._handle_dns_error(error)
        else:
            return await self._handle_generic_network_error(error)
    
    async def _handle_rate_limit_error(self, error: ProcessingError) -> bool:
        """Handle rate limiting errors."""
        
        url = error.context.url
        if not url:
            logger.warning("No URL in context for rate limit error")
            return False
        
        # Extract domain for rate limit tracking
        domain = self._extract_domain(url)
        
        # Check if we have rate limit reset information
        if domain in self.rate_limit_resets:
            reset_time = self.rate_limit_resets[domain]
            wait_time = (reset_time - datetime.now()).total_seconds()
            
            if wait_time > 0:
                logger.info(f"Waiting {wait_time:.1f} seconds for rate limit reset on {domain}")
                await asyncio.sleep(min(wait_time, 300))  # Cap at 5 minutes
        else:
            # Default wait time for rate limiting
            wait_time = min(60 * (error.recovery_attempts ** 2), 300)  # Exponential backoff, max 5 minutes
            logger.info(f"Rate limited, waiting {wait_time} seconds")
            await asyncio.sleep(wait_time)
        
        return True  # Rate limit handling is considered successful
    
    async def _handle_timeout_error(self, error: ProcessingError) -> bool:
        """Handle connection timeout errors."""
        
        # Implement exponential backoff with jitter
        delay = self._calculate_retry_delay(error.recovery_attempts)
        
        logger.info(f"Connection timeout, retrying after {delay:.1f} seconds")
        await asyncio.sleep(delay)
        
        # For timeout errors, we assume the retry will work
        return True
    
    async def _handle_http_error(self, error: ProcessingError) -> bool:
        """Handle HTTP errors."""
        
        # Extract status code from error message if possible
        status_code = self._extract_status_code(error.message)
        
        if status_code:
            if status_code in self.retry_config.retryable_status_codes:
                # Retryable HTTP error
                delay = self._calculate_retry_delay(error.recovery_attempts)
                logger.info(f"HTTP {status_code} error, retrying after {delay:.1f} seconds")
                await asyncio.sleep(delay)
                return True
            else:
                # Non-retryable HTTP error
                logger.info(f"HTTP {status_code} error is not retryable")
                return False
        else:
            # Unknown HTTP error, try once more
            if error.recovery_attempts == 1:
                delay = self._calculate_retry_delay(error.recovery_attempts)
                await asyncio.sleep(delay)
                return True
            else:
                return False
    
    async def _handle_dns_error(self, error: ProcessingError) -> bool:
        """Handle DNS resolution errors."""
        
        # DNS errors might be temporary, wait and retry
        delay = self._calculate_retry_delay(error.recovery_attempts)
        
        logger.info(f"DNS resolution error, retrying after {delay:.1f} seconds")
        await asyncio.sleep(delay)
        
        return True
    
    async def _handle_generic_network_error(self, error: ProcessingError) -> bool:
        """Handle generic network errors."""
        
        # For unknown network errors, use conservative retry strategy
        if error.recovery_attempts <= 2:
            delay = self._calculate_retry_delay(error.recovery_attempts)
            logger.info(f"Generic network error, retrying after {delay:.1f} seconds")
            await asyncio.sleep(delay)
            return True
        else:
            logger.info("Max retries reached for generic network error")
            return False
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff and jitter."""
        
        # Exponential backoff
        delay = self.retry_config.base_delay * (self.retry_config.exponential_base ** (attempt - 1))
        
        # Cap at max delay
        delay = min(delay, self.retry_config.max_delay)
        
        # Add jitter to avoid thundering herd
        if self.retry_config.jitter:
            jitter = random.uniform(0.1, 0.3) * delay
            delay += jitter
        
        return delay
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL for rate limit tracking."""
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return "unknown"
    
    def _extract_status_code(self, error_message: str) -> Optional[int]:
        """Extract HTTP status code from error message."""
        
        import re
        
        # Look for HTTP status codes in the error message
        patterns = [
            r'HTTP (\d{3})',
            r'status (\d{3})',
            r'(\d{3}) error',
            r'(\d{3})\s'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_message, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    async def make_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        Make an HTTP request with built-in error handling and retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional arguments for aiohttp request
            
        Returns:
            aiohttp.ClientResponse object
            
        Raises:
            NetworkError: If the request fails after all retries
        """
        
        if not self.session:
            await self.start()
        
        self.total_requests += 1
        last_exception = None
        
        for attempt in range(1, self.retry_config.max_retries + 1):
            try:
                # Check rate limiting
                domain = self._extract_domain(url)
                if await self._should_wait_for_rate_limit(domain):
                    continue
                
                # Make the request
                async with self.session.request(method, url, **kwargs) as response:
                    # Update rate limit tracking
                    self._update_rate_limit_info(response, domain)
                    
                    # Check if response indicates rate limiting
                    if response.status == 429:
                        self._handle_rate_limit_response(response, domain)
                        raise NetworkError(
                            f"Rate limited: {response.status}",
                            ErrorType.RATE_LIMIT_EXCEEDED,
                            response.status
                        )
                    
                    # Check for other HTTP errors
                    if response.status >= 400:
                        if response.status in self.retry_config.retryable_status_codes:
                            raise NetworkError(
                                f"HTTP error: {response.status}",
                                ErrorType.HTTP_ERROR,
                                response.status
                            )
                        else:
                            # Non-retryable error
                            response.raise_for_status()
                    
                    return response
            
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                
                # Determine error type
                if isinstance(e, asyncio.TimeoutError):
                    error_type = ErrorType.CONNECTION_TIMEOUT
                elif isinstance(e, aiohttp.ClientConnectorError):
                    error_type = ErrorType.CONNECTION_REFUSED
                else:
                    error_type = ErrorType.HTTP_ERROR
                
                logger.warning(f"Request attempt {attempt} failed: {e}")
                
                # Don't retry on last attempt
                if attempt == self.retry_config.max_retries:
                    break
                
                # Calculate delay and wait
                delay = self._calculate_retry_delay(attempt)
                await asyncio.sleep(delay)
        
        # All retries failed
        self.failed_requests += 1
        self.retried_requests += 1
        
        raise NetworkError(
            f"Request failed after {self.retry_config.max_retries} attempts: {last_exception}",
            ErrorType.HTTP_ERROR
        )
    
    async def _should_wait_for_rate_limit(self, domain: str) -> bool:
        """Check if we should wait due to rate limiting."""
        
        if domain in self.rate_limit_resets:
            reset_time = self.rate_limit_resets[domain]
            if datetime.now() < reset_time:
                wait_time = (reset_time - datetime.now()).total_seconds()
                if wait_time > 0:
                    logger.info(f"Waiting {wait_time:.1f} seconds for rate limit reset on {domain}")
                    await asyncio.sleep(min(wait_time, 60))  # Cap at 1 minute
                    return True
        
        return False
    
    def _update_rate_limit_info(self, response: aiohttp.ClientResponse, domain: str) -> None:
        """Update rate limit information from response headers."""
        
        # Check for common rate limit headers
        headers = response.headers
        
        # X-RateLimit-Reset (Unix timestamp)
        if 'X-RateLimit-Reset' in headers:
            try:
                reset_timestamp = int(headers['X-RateLimit-Reset'])
                self.rate_limit_resets[domain] = datetime.fromtimestamp(reset_timestamp)
            except (ValueError, OSError):
                pass
        
        # Retry-After header
        elif 'Retry-After' in headers:
            try:
                retry_after = int(headers['Retry-After'])
                self.rate_limit_resets[domain] = datetime.now() + timedelta(seconds=retry_after)
            except ValueError:
                pass
    
    def _handle_rate_limit_response(self, response: aiohttp.ClientResponse, domain: str) -> None:
        """Handle rate limit response and update tracking."""
        
        # Set default rate limit reset time if not provided in headers
        if domain not in self.rate_limit_resets:
            # Default to 1 minute wait
            self.rate_limit_resets[domain] = datetime.now() + timedelta(minutes=1)
        
        logger.warning(f"Rate limited on {domain}, reset at {self.rate_limit_resets[domain]}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get network handler statistics."""
        
        success_rate = 0.0
        if self.total_requests > 0:
            success_rate = ((self.total_requests - self.failed_requests) / self.total_requests) * 100
        
        return {
            'instance_name': self.instance_name,
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'retried_requests': self.retried_requests,
            'success_rate': success_rate,
            'active_rate_limits': len(self.rate_limit_resets),
            'rate_limit_domains': list(self.rate_limit_resets.keys())
        }
    
    def clear_rate_limit_cache(self, domain: Optional[str] = None) -> None:
        """Clear rate limit cache for a domain or all domains."""
        
        if domain:
            if domain in self.rate_limit_resets:
                del self.rate_limit_resets[domain]
                logger.info(f"Cleared rate limit cache for {domain}")
        else:
            self.rate_limit_resets.clear()
            logger.info("Cleared all rate limit cache")
    
    def configure_retry(self, retry_config: RetryConfig) -> None:
        """Update retry configuration."""
        
        self.retry_config = retry_config
        logger.info(f"Updated retry configuration for {self.instance_name}")