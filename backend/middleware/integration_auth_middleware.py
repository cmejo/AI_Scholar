"""
Integration authentication middleware
Provides automatic authentication and authorization for API requests
"""
import logging
import time
from typing import Optional, Dict, Any, List
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from services.oauth_server import OAuthServer
from services.api_key_service import APIKeyService

logger = logging.getLogger(__name__)

class IntegrationAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for handling integration authentication"""
    
    def __init__(self, app, excluded_paths: List[str] = None):
        super().__init__(app)
        self.oauth_server = OAuthServer()
        self.api_key_service = APIKeyService()
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/auth/oauth/token",
            "/api/auth/oauth/authorize",
            "/api/auth/oauth/device",
            "/api/auth/oauth/register"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request with authentication middleware"""
        start_time = time.time()
        
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            response = await call_next(request)
            return response
        
        # Skip authentication for non-API paths
        if not request.url.path.startswith("/api/"):
            response = await call_next(request)
            return response
        
        try:
            # Attempt authentication
            auth_result = await self._authenticate_request(request)
            
            if not auth_result["authenticated"]:
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "authentication_required",
                        "message": auth_result.get("error", "Authentication required"),
                        "timestamp": time.time()
                    }
                )
            
            # Add authentication info to request state
            request.state.auth_info = auth_result
            
            # Check rate limiting for API keys
            if auth_result["auth_type"] == "api_key":
                rate_limit_result = await self._check_rate_limit(
                    auth_result["key_info"], 
                    request
                )
                
                if not rate_limit_result["allowed"]:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "rate_limit_exceeded",
                            "message": "Rate limit exceeded",
                            "rate_limit": rate_limit_result["rate_limit_info"]
                        },
                        headers={
                            "X-RateLimit-Limit": str(rate_limit_result["rate_limit_info"]["rate_limit"]),
                            "X-RateLimit-Remaining": str(rate_limit_result["rate_limit_info"]["requests_remaining"]),
                            "X-RateLimit-Reset": str(int(rate_limit_result["rate_limit_info"]["reset_time"].timestamp()))
                        }
                    )
            
            # Process request
            response = await call_next(request)
            
            # Log API usage for API keys
            if auth_result["auth_type"] == "api_key":
                await self._log_api_usage(
                    auth_result["key_info"],
                    request,
                    response,
                    time.time() - start_time
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "authentication_error",
                    "message": "Internal authentication error",
                    "timestamp": time.time()
                }
            )
    
    async def _authenticate_request(self, request: Request) -> Dict[str, Any]:
        """Authenticate request using OAuth or API key"""
        try:
            # Try OAuth Bearer token first
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                token_info = await self.oauth_server.verify_access_token(token)
                
                if token_info:
                    return {
                        "authenticated": True,
                        "auth_type": "oauth",
                        "user_id": token_info["user_id"],
                        "client_id": token_info["client_id"],
                        "scopes": token_info["scopes"],
                        "token_info": token_info
                    }
            
            # Try API key authentication
            api_key = request.headers.get("X-API-Key")
            if api_key:
                client_ip = request.client.host if request.client else None
                user_agent = request.headers.get("User-Agent")
                
                key_info = await self.api_key_service.authenticate_api_key(
                    api_key,
                    client_ip=client_ip,
                    user_agent=user_agent
                )
                
                if key_info:
                    return {
                        "authenticated": True,
                        "auth_type": "api_key",
                        "user_id": key_info.user_id,
                        "key_id": key_info.key_id,
                        "scopes": key_info.scopes,
                        "key_info": key_info
                    }
            
            return {
                "authenticated": False,
                "error": "No valid authentication credentials provided"
            }
            
        except Exception as e:
            logger.error(f"Request authentication failed: {e}")
            return {
                "authenticated": False,
                "error": f"Authentication failed: {str(e)}"
            }
    
    async def _check_rate_limit(self, key_info, request: Request) -> Dict[str, Any]:
        """Check rate limit for API key"""
        try:
            rate_limit_info = await self.api_key_service.check_rate_limit(key_info.key_id)
            
            return {
                "allowed": rate_limit_info.requests_remaining > 0,
                "rate_limit_info": {
                    "rate_limit": rate_limit_info.rate_limit,
                    "requests_remaining": rate_limit_info.requests_remaining,
                    "reset_time": rate_limit_info.reset_time
                }
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return {
                "allowed": False,
                "error": str(e)
            }
    
    async def _log_api_usage(self, key_info, request: Request, response, response_time: float):
        """Log API usage for analytics"""
        try:
            await self.api_key_service.log_api_usage(
                key_id=key_info.key_id,
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                response_time=response_time,
                user_agent=request.headers.get("User-Agent"),
                ip_address=request.client.host if request.client else None
            )
            
        except Exception as e:
            logger.error(f"API usage logging failed: {e}")

class ScopeRequiredMiddleware:
    """Middleware for checking required scopes"""
    
    def __init__(self, required_scopes: List[str]):
        self.required_scopes = required_scopes
    
    async def __call__(self, request: Request, call_next):
        """Check if authenticated user has required scopes"""
        try:
            # Get authentication info from request state
            auth_info = getattr(request.state, 'auth_info', None)
            
            if not auth_info or not auth_info.get("authenticated"):
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "authentication_required",
                        "message": "Authentication required"
                    }
                )
            
            # Check scopes
            user_scopes = auth_info.get("scopes", [])
            missing_scopes = set(self.required_scopes) - set(user_scopes)
            
            if missing_scopes:
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "insufficient_scope",
                        "message": f"Missing required scopes: {list(missing_scopes)}",
                        "required_scopes": self.required_scopes,
                        "available_scopes": user_scopes
                    }
                )
            
            # Proceed with request
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Scope checking failed: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "scope_check_error",
                    "message": "Internal scope checking error"
                }
            )

def require_scopes(scopes: List[str]):
    """Decorator for requiring specific scopes"""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # Get authentication info from request state
            auth_info = getattr(request.state, 'auth_info', None)
            
            if not auth_info or not auth_info.get("authenticated"):
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            # Check scopes
            user_scopes = auth_info.get("scopes", [])
            missing_scopes = set(scopes) - set(user_scopes)
            
            if missing_scopes:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "insufficient_scope",
                        "message": f"Missing required scopes: {list(missing_scopes)}",
                        "required_scopes": scopes,
                        "available_scopes": user_scopes
                    }
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator

def get_auth_info(request: Request) -> Optional[Dict[str, Any]]:
    """Get authentication info from request"""
    return getattr(request.state, 'auth_info', None)

def get_current_user_id(request: Request) -> Optional[str]:
    """Get current user ID from request"""
    auth_info = get_auth_info(request)
    return auth_info.get("user_id") if auth_info else None

def get_current_scopes(request: Request) -> List[str]:
    """Get current user scopes from request"""
    auth_info = get_auth_info(request)
    return auth_info.get("scopes", []) if auth_info else []

class IntegrationSpecificMiddleware:
    """Middleware for integration-specific authentication and validation"""
    
    def __init__(self, integration_type: str):
        self.integration_type = integration_type
        self.oauth_server = OAuthServer()
        self.api_key_service = APIKeyService()
    
    async def __call__(self, request: Request, call_next):
        """Validate integration-specific access"""
        try:
            auth_info = get_auth_info(request)
            
            if not auth_info or not auth_info.get("authenticated"):
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "authentication_required",
                        "message": "Authentication required for integration access"
                    }
                )
            
            # Validate integration access based on auth type
            if auth_info["auth_type"] == "oauth":
                # Check OAuth client integration access
                is_valid = await self.oauth_server.validate_integration_access(
                    client_id=auth_info["client_id"],
                    integration_type=self.integration_type,
                    requested_scopes=auth_info["scopes"]
                )
                
                if not is_valid:
                    return JSONResponse(
                        status_code=403,
                        content={
                            "error": "integration_access_denied",
                            "message": f"Access denied for {self.integration_type} integration",
                            "integration_type": self.integration_type
                        }
                    )
            
            elif auth_info["auth_type"] == "api_key":
                # Check API key integration metadata
                metadata_data = await self.api_key_service.redis_client.get(
                    f"{self.api_key_service.redis_prefix}metadata:{auth_info['key_id']}"
                )
                
                if metadata_data:
                    import json
                    metadata = json.loads(metadata_data)
                    if metadata.get("integration_type") != self.integration_type:
                        return JSONResponse(
                            status_code=403,
                            content={
                                "error": "integration_mismatch",
                                "message": f"API key not authorized for {self.integration_type} integration",
                                "integration_type": self.integration_type
                            }
                        )
            
            # Proceed with request
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Integration-specific middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "integration_validation_error",
                    "message": "Internal integration validation error"
                }
            )