"""
Security middleware for Zotero integration endpoints.
"""
import asyncio
import time
from datetime import datetime
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import logging

from services.zotero.zotero_security_service import (
    security_service, SecurityEventType, ThreatLevel
)


class ZoteroSecurityMiddleware:
    """Security middleware for Zotero endpoints."""
    
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(__name__)
        
        # Paths that require security checks
        self.protected_paths = [
            '/api/zotero/',
            '/api/zotero/auth/',
            '/api/zotero/sync/',
            '/api/zotero/search/',
            '/api/zotero/citations/',
            '/api/zotero/admin/',
            '/api/zotero/analytics/'
        ]
        
        # Paths that are exempt from rate limiting
        self.rate_limit_exempt = [
            '/api/zotero/health',
            '/api/zotero/version'
        ]
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request through security middleware."""
        start_time = time.time()
        
        try:
            # Check if path requires security checks
            if not self._is_protected_path(request.url.path):
                return await call_next(request)
            
            # Extract client information
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get('user-agent', '')
            user_id = self._get_user_id(request)
            
            # Check if IP is blocked
            if await security_service.is_ip_blocked(client_ip):
                await security_service.log_security_event(
                    SecurityEventType.SECURITY_VIOLATION,
                    ThreatLevel.HIGH,
                    user_id=user_id,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    resource=request.url.path,
                    action="blocked_ip_access_attempt"
                )
                
                return JSONResponse(
                    status_code=403,
                    content={"error": "Access denied", "code": "IP_BLOCKED"}
                )
            
            # Check if user is locked out
            if user_id and await security_service.is_user_locked_out(user_id):
                await security_service.log_security_event(
                    SecurityEventType.SECURITY_VIOLATION,
                    ThreatLevel.MEDIUM,
                    user_id=user_id,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    resource=request.url.path,
                    action="locked_user_access_attempt"
                )
                
                return JSONResponse(
                    status_code=423,
                    content={"error": "Account locked", "code": "USER_LOCKED"}
                )
            
            # Rate limiting check
            if not self._is_rate_limit_exempt(request.url.path):
                allowed, remaining = await security_service.check_rate_limit(
                    user_id or client_ip,
                    client_ip,
                    request.url.path
                )
                
                if not allowed:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Rate limit exceeded",
                            "code": "RATE_LIMIT_EXCEEDED",
                            "retry_after": 3600
                        },
                        headers={"Retry-After": "3600"}
                    )
                
                # Add rate limit headers
                response_headers = {
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(int(time.time() + 3600))
                }
            else:
                response_headers = {}
            
            # Validate request data for security threats
            if request.method in ['POST', 'PUT', 'PATCH']:
                await self._validate_request_data(request, user_id, client_ip)
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            self._add_security_headers(response)
            
            # Add rate limit headers if applicable
            for header, value in response_headers.items():
                response.headers[header] = value
            
            # Log successful access
            processing_time = time.time() - start_time
            
            if response.status_code >= 400:
                threat_level = ThreatLevel.MEDIUM if response.status_code >= 500 else ThreatLevel.LOW
                
                await security_service.log_security_event(
                    SecurityEventType.SECURITY_VIOLATION if response.status_code == 403 else SecurityEventType.AUTHENTICATION_FAILURE,
                    threat_level,
                    user_id=user_id,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    resource=request.url.path,
                    action=request.method.lower(),
                    details={
                        'status_code': response.status_code,
                        'processing_time': processing_time
                    }
                )
            else:
                await security_service.log_security_event(
                    SecurityEventType.DATA_ACCESS,
                    ThreatLevel.LOW,
                    user_id=user_id,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    resource=request.url.path,
                    action=request.method.lower(),
                    details={
                        'status_code': response.status_code,
                        'processing_time': processing_time
                    }
                )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Security middleware error: {str(e)}")
            
            # Log security middleware failure
            await security_service.log_security_event(
                SecurityEventType.SECURITY_VIOLATION,
                ThreatLevel.HIGH,
                user_id=self._get_user_id(request),
                ip_address=self._get_client_ip(request),
                resource=request.url.path,
                action="middleware_error",
                details={'error': str(e)}
            )
            
            return JSONResponse(
                status_code=500,
                content={"error": "Internal security error", "code": "SECURITY_ERROR"}
            )
    
    def _is_protected_path(self, path: str) -> bool:
        """Check if path requires security checks."""
        return any(path.startswith(protected) for protected in self.protected_paths)
    
    def _is_rate_limit_exempt(self, path: str) -> bool:
        """Check if path is exempt from rate limiting."""
        return any(path.startswith(exempt) for exempt in self.rate_limit_exempt)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        # Check for forwarded headers (when behind proxy)
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return 'unknown'
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request."""
        # Try to get from JWT token or session
        auth_header = request.headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            # In a real implementation, decode JWT token
            # For now, return placeholder
            return 'user_from_token'
        
        # Try to get from session or other auth mechanism
        return None
    
    async def _validate_request_data(
        self,
        request: Request,
        user_id: Optional[str],
        client_ip: str
    ) -> None:
        """Validate request data for security threats."""
        try:
            # Get request body
            body = await request.body()
            if not body:
                return
            
            # Parse JSON if applicable
            content_type = request.headers.get('content-type', '')
            if 'application/json' in content_type:
                try:
                    import json
                    data = json.loads(body.decode())
                    
                    # Validate input security
                    is_valid, violations = await security_service.validate_input_security(
                        data, user_id or 'anonymous', client_ip
                    )
                    
                    if not is_valid:
                        raise HTTPException(
                            status_code=400,
                            detail={
                                "error": "Invalid input detected",
                                "code": "SECURITY_VIOLATION",
                                "violations": violations
                            }
                        )
                        
                except json.JSONDecodeError:
                    # Invalid JSON
                    await security_service.log_security_event(
                        SecurityEventType.SECURITY_VIOLATION,
                        ThreatLevel.LOW,
                        user_id=user_id,
                        ip_address=client_ip,
                        resource=request.url.path,
                        action="invalid_json",
                        details={'content_type': content_type}
                    )
            
            # Check for suspicious patterns in raw body
            body_text = body.decode('utf-8', errors='ignore')
            suspicious_patterns = security_service.detect_suspicious_input(body_text)
            
            if suspicious_patterns:
                await security_service.log_security_event(
                    SecurityEventType.SECURITY_VIOLATION,
                    ThreatLevel.MEDIUM,
                    user_id=user_id,
                    ip_address=client_ip,
                    resource=request.url.path,
                    action="suspicious_input",
                    details={'patterns': suspicious_patterns}
                )
                
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Suspicious input detected",
                        "code": "SECURITY_VIOLATION"
                    }
                )
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.warning(f"Request validation error: {str(e)}")
    
    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response."""
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';",
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'X-Permitted-Cross-Domain-Policies': 'none'
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value


class ZoteroRateLimitMiddleware:
    """Dedicated rate limiting middleware for Zotero endpoints."""
    
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(__name__)
        
        # Different rate limits for different endpoint types
        self.rate_limits = {
            '/api/zotero/auth/': {'requests': 10, 'window': 300},  # 10 requests per 5 minutes
            '/api/zotero/sync/': {'requests': 100, 'window': 3600},  # 100 requests per hour
            '/api/zotero/search/': {'requests': 500, 'window': 3600},  # 500 requests per hour
            '/api/zotero/citations/': {'requests': 200, 'window': 3600},  # 200 requests per hour
            '/api/zotero/admin/': {'requests': 50, 'window': 3600},  # 50 requests per hour
            'default': {'requests': 1000, 'window': 3600}  # Default: 1000 requests per hour
        }
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting."""
        try:
            # Get rate limit for this endpoint
            rate_limit = self._get_rate_limit(request.url.path)
            
            if not rate_limit:
                return await call_next(request)
            
            # Get client identifier
            client_ip = self._get_client_ip(request)
            user_id = self._get_user_id(request)
            client_id = user_id or client_ip
            
            # Check rate limit
            allowed, remaining = await self._check_rate_limit(
                client_id,
                request.url.path,
                rate_limit
            )
            
            if not allowed:
                # Log rate limit violation
                await security_service.log_security_event(
                    SecurityEventType.RATE_LIMIT_EXCEEDED,
                    ThreatLevel.MEDIUM,
                    user_id=user_id,
                    ip_address=client_ip,
                    resource=request.url.path,
                    action="rate_limit_exceeded",
                    details=rate_limit
                )
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "code": "RATE_LIMIT_EXCEEDED",
                        "limit": rate_limit['requests'],
                        "window": rate_limit['window'],
                        "retry_after": rate_limit['window']
                    },
                    headers={
                        "Retry-After": str(rate_limit['window']),
                        "X-RateLimit-Limit": str(rate_limit['requests']),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time() + rate_limit['window']))
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(rate_limit['requests'])
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + rate_limit['window']))
            
            return response
            
        except Exception as e:
            self.logger.error(f"Rate limit middleware error: {str(e)}")
            return await call_next(request)
    
    def _get_rate_limit(self, path: str) -> Optional[Dict[str, int]]:
        """Get rate limit configuration for path."""
        for endpoint_prefix, limit in self.rate_limits.items():
            if endpoint_prefix != 'default' and path.startswith(endpoint_prefix):
                return limit
        
        return self.rate_limits['default']
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return 'unknown'
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request."""
        auth_header = request.headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            # In a real implementation, decode JWT token
            return 'user_from_token'
        
        return None
    
    async def _check_rate_limit(
        self,
        client_id: str,
        endpoint: str,
        rate_limit: Dict[str, int]
    ) -> Tuple[bool, int]:
        """Check if request is within rate limit."""
        try:
            from core.redis_client import get_redis_client
            
            redis_client = await get_redis_client()
            if not redis_client:
                return True, rate_limit['requests']
            
            # Use sliding window rate limiting
            key = f"rate_limit:{client_id}:{endpoint}"
            current_time = time.time()
            window_start = current_time - rate_limit['window']
            
            # Remove old entries
            await redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            current_requests = await redis_client.zcard(key)
            
            if current_requests >= rate_limit['requests']:
                return False, 0
            
            # Add current request
            await redis_client.zadd(key, {str(current_time): current_time})
            await redis_client.expire(key, rate_limit['window'])
            
            remaining = rate_limit['requests'] - current_requests - 1
            return True, remaining
            
        except Exception as e:
            self.logger.error(f"Rate limit check error: {str(e)}")
            return True, rate_limit['requests']