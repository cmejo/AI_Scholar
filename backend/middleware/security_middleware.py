"""
Security Middleware for AI Scholar
Implements comprehensive security headers, rate limiting, and request validation
"""

import time
import hashlib
import json
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from collections import defaultdict, deque
import logging
import re
import ipaddress

from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10
    window_size: int = 60  # seconds

@dataclass
class SecurityConfig:
    """Security configuration"""
    enable_cors: bool = True
    allowed_origins: List[str] = None
    enable_csrf_protection: bool = True
    enable_xss_protection: bool = True
    enable_content_type_validation: bool = True
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    blocked_user_agents: List[str] = None
    blocked_ips: List[str] = None
    trusted_proxies: List[str] = None

class RateLimiter:
    """Advanced rate limiter with multiple time windows"""
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        
        # Store requests by IP and time window
        self.requests_per_minute: Dict[str, deque] = defaultdict(deque)
        self.requests_per_hour: Dict[str, deque] = defaultdict(deque)
        self.requests_per_day: Dict[str, deque] = defaultdict(deque)
        
        # Burst protection
        self.burst_requests: Dict[str, deque] = defaultdict(deque)
        
        # Blocked IPs (temporary)
        self.blocked_ips: Dict[str, float] = {}
        self.block_duration = 300  # 5 minutes
    
    def is_allowed(self, client_ip: str, endpoint: str = None) -> Dict[str, Any]:
        """Check if request is allowed based on rate limits"""
        current_time = time.time()
        
        # Check if IP is temporarily blocked
        if client_ip in self.blocked_ips:
            if current_time - self.blocked_ips[client_ip] < self.block_duration:
                return {
                    "allowed": False,
                    "reason": "IP temporarily blocked",
                    "retry_after": self.block_duration - (current_time - self.blocked_ips[client_ip])
                }
            else:
                # Unblock IP
                del self.blocked_ips[client_ip]
        
        # Clean old requests
        self._clean_old_requests(client_ip, current_time)
        
        # Check burst limit (last 10 seconds)
        burst_window = current_time - 10
        burst_requests = self.burst_requests[client_ip]
        burst_requests.append(current_time)
        
        # Remove old burst requests
        while burst_requests and burst_requests[0] < burst_window:
            burst_requests.popleft()
        
        if len(burst_requests) > self.config.burst_limit:
            # Temporarily block IP for burst
            self.blocked_ips[client_ip] = current_time
            logger.warning(f"IP {client_ip} blocked for burst limit violation")
            return {
                "allowed": False,
                "reason": "Burst limit exceeded",
                "retry_after": self.block_duration
            }
        
        # Check rate limits
        minute_requests = len(self.requests_per_minute[client_ip])
        hour_requests = len(self.requests_per_hour[client_ip])
        day_requests = len(self.requests_per_day[client_ip])
        
        # Add current request
        self.requests_per_minute[client_ip].append(current_time)
        self.requests_per_hour[client_ip].append(current_time)
        self.requests_per_day[client_ip].append(current_time)
        
        # Check limits
        if minute_requests >= self.config.requests_per_minute:
            return {
                "allowed": False,
                "reason": "Rate limit exceeded (per minute)",
                "retry_after": 60,
                "limits": {
                    "minute": f"{minute_requests}/{self.config.requests_per_minute}",
                    "hour": f"{hour_requests}/{self.config.requests_per_hour}",
                    "day": f"{day_requests}/{self.config.requests_per_day}"
                }
            }
        
        if hour_requests >= self.config.requests_per_hour:
            return {
                "allowed": False,
                "reason": "Rate limit exceeded (per hour)",
                "retry_after": 3600,
                "limits": {
                    "minute": f"{minute_requests}/{self.config.requests_per_minute}",
                    "hour": f"{hour_requests}/{self.config.requests_per_hour}",
                    "day": f"{day_requests}/{self.config.requests_per_day}"
                }
            }
        
        if day_requests >= self.config.requests_per_day:
            return {
                "allowed": False,
                "reason": "Rate limit exceeded (per day)",
                "retry_after": 86400,
                "limits": {
                    "minute": f"{minute_requests}/{self.config.requests_per_minute}",
                    "hour": f"{hour_requests}/{self.config.requests_per_hour}",
                    "day": f"{day_requests}/{self.config.requests_per_day}"
                }
            }
        
        return {
            "allowed": True,
            "limits": {
                "minute": f"{minute_requests + 1}/{self.config.requests_per_minute}",
                "hour": f"{hour_requests + 1}/{self.config.requests_per_hour}",
                "day": f"{day_requests + 1}/{self.config.requests_per_day}"
            }
        }
    
    def _clean_old_requests(self, client_ip: str, current_time: float):
        """Clean old requests from tracking"""
        # Clean minute requests (older than 60 seconds)
        minute_cutoff = current_time - 60
        minute_requests = self.requests_per_minute[client_ip]
        while minute_requests and minute_requests[0] < minute_cutoff:
            minute_requests.popleft()
        
        # Clean hour requests (older than 3600 seconds)
        hour_cutoff = current_time - 3600
        hour_requests = self.requests_per_hour[client_ip]
        while hour_requests and hour_requests[0] < hour_cutoff:
            hour_requests.popleft()
        
        # Clean day requests (older than 86400 seconds)
        day_cutoff = current_time - 86400
        day_requests = self.requests_per_day[client_ip]
        while day_requests and day_requests[0] < day_cutoff:
            day_requests.popleft()

class SecurityValidator:
    """Security validation utilities"""
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        
        # Compile regex patterns for performance
        self.sql_injection_patterns = [
            re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)", re.IGNORECASE),
            re.compile(r"(\b(OR|AND)\s+\d+\s*=\s*\d+)", re.IGNORECASE),
            re.compile(r"('|(\\x27)|(\\x2D)|(\\x23))", re.IGNORECASE),
            re.compile(r"(\\x00|\\n|\\r|\\x1a)", re.IGNORECASE)
        ]
        
        self.xss_patterns = [
            re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
            re.compile(r"javascript:", re.IGNORECASE),
            re.compile(r"on\w+\s*=", re.IGNORECASE),
            re.compile(r"<iframe[^>]*>.*?</iframe>", re.IGNORECASE | re.DOTALL),
            re.compile(r"<object[^>]*>.*?</object>", re.IGNORECASE | re.DOTALL)
        ]
        
        self.path_traversal_patterns = [
            re.compile(r"\.\.[\\/]"),
            re.compile(r"[\\/]\.\."),
            re.compile(r"%2e%2e[\\/]", re.IGNORECASE),
            re.compile(r"[\\/]%2e%2e", re.IGNORECASE)
        ]
    
    def validate_request(self, request: Request) -> Dict[str, Any]:
        """Comprehensive request validation"""
        issues = []
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.config.max_request_size:
            issues.append({
                "type": "request_too_large",
                "message": f"Request size {content_length} exceeds limit {self.config.max_request_size}"
            })
        
        # Check User-Agent
        user_agent = request.headers.get("user-agent", "")
        if self.config.blocked_user_agents:
            for blocked_ua in self.config.blocked_user_agents:
                if blocked_ua.lower() in user_agent.lower():
                    issues.append({
                        "type": "blocked_user_agent",
                        "message": f"Blocked user agent: {user_agent}"
                    })
        
        # Check for suspicious patterns in URL
        url_path = str(request.url.path)
        query_params = str(request.url.query)
        
        # SQL Injection detection
        for pattern in self.sql_injection_patterns:
            if pattern.search(url_path) or pattern.search(query_params):
                issues.append({
                    "type": "sql_injection_attempt",
                    "message": "Potential SQL injection detected in URL"
                })
                break
        
        # XSS detection
        for pattern in self.xss_patterns:
            if pattern.search(url_path) or pattern.search(query_params):
                issues.append({
                    "type": "xss_attempt",
                    "message": "Potential XSS attack detected in URL"
                })
                break
        
        # Path traversal detection
        for pattern in self.path_traversal_patterns:
            if pattern.search(url_path):
                issues.append({
                    "type": "path_traversal_attempt",
                    "message": "Potential path traversal attack detected"
                })
                break
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    async def validate_request_body(self, body: bytes) -> Dict[str, Any]:
        """Validate request body content"""
        if not body:
            return {"valid": True, "issues": []}
        
        issues = []
        
        try:
            # Try to decode as text for validation
            text_content = body.decode('utf-8', errors='ignore')
            
            # Check for SQL injection in body
            for pattern in self.sql_injection_patterns:
                if pattern.search(text_content):
                    issues.append({
                        "type": "sql_injection_attempt",
                        "message": "Potential SQL injection detected in request body"
                    })
                    break
            
            # Check for XSS in body
            for pattern in self.xss_patterns:
                if pattern.search(text_content):
                    issues.append({
                        "type": "xss_attempt",
                        "message": "Potential XSS attack detected in request body"
                    })
                    break
            
            # Check for suspicious file uploads
            if b"<?php" in body or b"<script" in body:
                issues.append({
                    "type": "malicious_upload",
                    "message": "Potentially malicious file upload detected"
                })
        
        except Exception as e:
            logger.warning(f"Error validating request body: {e}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware"""
    
    def __init__(self, app, config: SecurityConfig = None):
        super().__init__(app)
        self.config = config or SecurityConfig()
        self.rate_limiter = RateLimiter()
        self.validator = SecurityValidator(config)
        
        # Security headers
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security middleware"""
        start_time = time.time()
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check if IP is blocked
        if self._is_ip_blocked(client_ip):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Access denied", "message": "IP address is blocked"}
            )
        
        # Rate limiting
        rate_limit_result = self.rate_limiter.is_allowed(client_ip, str(request.url.path))
        if not rate_limit_result["allowed"]:
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": rate_limit_result["reason"],
                    "retry_after": rate_limit_result.get("retry_after", 60)
                }
            )
            response.headers["Retry-After"] = str(int(rate_limit_result.get("retry_after", 60)))
            return response
        
        # Request validation
        validation_result = self.validator.validate_request(request)
        if not validation_result["valid"]:
            logger.warning(f"Security validation failed for {client_ip}: {validation_result['issues']}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Invalid request",
                    "message": "Request failed security validation"
                }
            )
        
        # Validate request body for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            body_validation = await self.validator.validate_request_body(body)
            if not body_validation["valid"]:
                logger.warning(f"Request body validation failed for {client_ip}: {body_validation['issues']}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "Invalid request body",
                        "message": "Request body failed security validation"
                    }
                )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error"}
            )
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        # Add rate limit headers
        if "limits" in rate_limit_result:
            limits = rate_limit_result["limits"]
            response.headers["X-RateLimit-Minute"] = limits["minute"]
            response.headers["X-RateLimit-Hour"] = limits["hour"]
            response.headers["X-RateLimit-Day"] = limits["day"]
        
        # Add processing time header
        processing_time = time.time() - start_time
        response.headers["X-Processing-Time"] = f"{processing_time:.3f}"
        
        # Log request
        self._log_request(request, response, client_ip, processing_time)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address considering proxies"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.headers.get("X-Real-IP") or request.client.host
        
        return client_ip
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is in blocked list"""
        if not self.config.blocked_ips:
            return False
        
        try:
            client_ip = ipaddress.ip_address(ip)
            for blocked_ip in self.config.blocked_ips:
                if "/" in blocked_ip:
                    # CIDR notation
                    if client_ip in ipaddress.ip_network(blocked_ip, strict=False):
                        return True
                else:
                    # Single IP
                    if client_ip == ipaddress.ip_address(blocked_ip):
                        return True
        except ValueError:
            # Invalid IP format
            logger.warning(f"Invalid IP format: {ip}")
        
        return False
    
    def _log_request(self, request: Request, response: Response, client_ip: str, processing_time: float):
        """Log request details"""
        log_data = {
            "timestamp": time.time(),
            "client_ip": client_ip,
            "method": request.method,
            "path": str(request.url.path),
            "query_params": str(request.url.query),
            "user_agent": request.headers.get("user-agent", ""),
            "status_code": response.status_code,
            "processing_time": processing_time,
            "content_length": response.headers.get("content-length", "0")
        }
        
        # Log based on status code
        if response.status_code >= 500:
            logger.error(f"Server error: {json.dumps(log_data)}")
        elif response.status_code >= 400:
            logger.warning(f"Client error: {json.dumps(log_data)}")
        else:
            logger.info(f"Request: {json.dumps(log_data)}")

class CSRFProtection:
    """CSRF protection middleware"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.exempt_methods = {"GET", "HEAD", "OPTIONS", "TRACE"}
    
    def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token for session"""
        timestamp = str(int(time.time()))
        data = f"{session_id}:{timestamp}:{self.secret_key}"
        token = hashlib.sha256(data.encode()).hexdigest()
        return f"{timestamp}:{token}"
    
    def validate_csrf_token(self, token: str, session_id: str) -> bool:
        """Validate CSRF token"""
        try:
            timestamp_str, token_hash = token.split(":", 1)
            timestamp = int(timestamp_str)
            
            # Check if token is not too old (1 hour)
            if time.time() - timestamp > 3600:
                return False
            
            # Regenerate expected token
            data = f"{session_id}:{timestamp_str}:{self.secret_key}"
            expected_token = hashlib.sha256(data.encode()).hexdigest()
            
            return token_hash == expected_token
        
        except (ValueError, IndexError):
            return False

# Global instances
security_config = SecurityConfig(
    allowed_origins=["http://localhost:3000", "https://yourdomain.com"],
    blocked_user_agents=["bot", "crawler", "spider"],
    blocked_ips=[]  # Add IPs to block
)

security_middleware = SecurityMiddleware(None, security_config)
csrf_protection = CSRFProtection("your-csrf-secret-key")

# Usage example
def create_security_middleware(app):
    """Create and configure security middleware"""
    return SecurityMiddleware(app, security_config)

if __name__ == "__main__":
    # Test rate limiter
    rate_limiter = RateLimiter()
    
    # Simulate requests
    for i in range(15):
        result = rate_limiter.is_allowed("192.168.1.1")
        print(f"Request {i+1}: {'Allowed' if result['allowed'] else 'Blocked'} - {result.get('reason', 'OK')}")
        time.sleep(0.1)
    
    # Test security validator
    validator = SecurityValidator()
    
    # Test malicious patterns
    test_patterns = [
        "SELECT * FROM users WHERE id=1",
        "<script>alert('xss')</script>",
        "../../../etc/passwd",
        "normal request"
    ]
    
    for pattern in test_patterns:
        # Create mock request for testing
        class MockRequest:
            def __init__(self, path):
                self.url = type('obj', (object,), {'path': path, 'query': ''})()
                self.headers = {}
        
        mock_request = MockRequest(pattern)
        result = validator.validate_request(mock_request)
        print(f"Pattern '{pattern}': {'Valid' if result['valid'] else 'Invalid'} - {result.get('issues', [])}")