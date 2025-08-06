"""
Integration authentication endpoints
Provides OAuth 2.0 and API key authentication for external integrations
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Form, Query, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field

from services.oauth_server import OAuthServer
from services.api_key_service import APIKeyService
from services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["integration-auth"])

# Initialize services
oauth_server = OAuthServer()
api_key_service = APIKeyService()
auth_service = AuthService()

# Security schemes
security_bearer = HTTPBearer()
security_basic = HTTPBasic()

# Pydantic models
class OAuthClientRegistration(BaseModel):
    name: str
    description: str
    redirect_uris: List[str]
    scopes: List[str]
    client_type: str = "confidential"

class AuthorizeRequest(BaseModel):
    response_type: str = "code"
    client_id: str
    redirect_uri: str
    scope: str
    state: Optional[str] = None

class TokenRequest(BaseModel):
    grant_type: str
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    client_id: str
    client_secret: str
    refresh_token: Optional[str] = None

class APIKeyCreateRequest(BaseModel):
    name: str
    description: str
    scopes: List[str]
    rate_limit: Optional[int] = None
    expires_in_days: Optional[int] = None
    integration_type: Optional[str] = None
    ip_whitelist: Optional[List[str]] = None

class IntegrationAPIKeyRequest(BaseModel):
    integration_type: str
    integration_config: Dict[str, Any] = {}

class DeviceFlowRequest(BaseModel):
    client_id: str
    scope: str

class DeviceAuthRequest(BaseModel):
    user_code: str

class DeviceTokenRequest(BaseModel):
    grant_type: str = "urn:ietf:params:oauth:grant-type:device_code"
    device_code: str
    client_id: str
    client_secret: str

class APIKeyUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    scopes: Optional[List[str]] = None
    rate_limit: Optional[int] = None

class AuthResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# Authentication dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)):
    """Get current authenticated user from JWT token"""
    try:
        user = await auth_service.verify_token(credentials.credentials)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def authenticate_oauth_client(credentials: HTTPBasicCredentials = Depends(security_basic)):
    """Authenticate OAuth client using basic auth"""
    try:
        client = await oauth_server.authenticate_client(credentials.username, credentials.password)
        if not client:
            raise HTTPException(status_code=401, detail="Invalid client credentials")
        return client
    except Exception as e:
        raise HTTPException(status_code=401, detail="Client authentication failed")

async def authenticate_api_key(request: Request):
    """Authenticate API key from header with enhanced security"""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Get client IP and user agent for security checks
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    
    key_info = await api_key_service.authenticate_api_key(
        api_key, 
        client_ip=client_ip,
        user_agent=user_agent
    )
    if not key_info:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Check rate limit
    rate_limit_info = await api_key_service.check_rate_limit(key_info.key_id)
    if rate_limit_info.requests_remaining <= 0:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(rate_limit_info.rate_limit),
                "X-RateLimit-Remaining": str(rate_limit_info.requests_remaining),
                "X-RateLimit-Reset": str(int(rate_limit_info.reset_time.timestamp()))
            }
        )
    
    return key_info

# OAuth 2.0 Endpoints

@router.post("/oauth/register", response_model=AuthResponse)
async def register_oauth_client(
    request: OAuthClientRegistration,
    user = Depends(get_current_user)
):
    """Register a new OAuth client"""
    try:
        client = await oauth_server.register_client(
            name=request.name,
            description=request.description,
            redirect_uris=request.redirect_uris,
            scopes=request.scopes,
            client_type=request.client_type
        )
        
        return AuthResponse(
            success=True,
            data={
                "client_id": client.client_id,
                "client_secret": client.client_secret,
                "name": client.name,
                "redirect_uris": client.redirect_uris,
                "scopes": client.scopes,
                "client_type": client.client_type,
                "created_at": client.created_at.isoformat(),
                "warning": "Store the client secret securely. It will not be shown again."
            }
        )
    except Exception as e:
        logger.error(f"OAuth client registration failed: {e}")
        return AuthResponse(
            success=False,
            error=f"Client registration failed: {str(e)}"
        )

@router.get("/oauth/authorize")
async def authorize_oauth_client(
    response_type: str = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str = Query(...),
    state: Optional[str] = Query(None),
    user = Depends(get_current_user)
):
    """OAuth authorization endpoint"""
    try:
        if response_type != "code":
            raise HTTPException(status_code=400, detail="Unsupported response type")
        
        # Validate client and redirect URI
        client = await oauth_server.get_client(client_id)
        if not client:
            raise HTTPException(status_code=400, detail="Invalid client")
        
        if redirect_uri not in client.redirect_uris:
            raise HTTPException(status_code=400, detail="Invalid redirect URI")
        
        # Parse and validate scopes
        requested_scopes = scope.split()
        invalid_scopes = set(requested_scopes) - set(client.scopes)
        if invalid_scopes:
            raise HTTPException(status_code=400, detail=f"Invalid scopes: {invalid_scopes}")
        
        # Generate authorization code
        auth_code = await oauth_server.generate_authorization_code(
            client_id=client_id,
            user_id=user.id,
            redirect_uri=redirect_uri,
            scopes=requested_scopes
        )
        
        # Build redirect URL
        redirect_url = f"{redirect_uri}?code={auth_code.code}"
        if state:
            redirect_url += f"&state={state}"
        
        return {"redirect_url": redirect_url}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth authorization failed: {e}")
        raise HTTPException(status_code=500, detail="Authorization failed")

@router.post("/oauth/token")
async def oauth_token_endpoint(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    refresh_token: Optional[str] = Form(None)
):
    """OAuth token endpoint"""
    try:
        if grant_type == "authorization_code":
            if not code or not redirect_uri:
                raise HTTPException(status_code=400, detail="Missing required parameters")
            
            token_data = await oauth_server.exchange_code_for_tokens(
                code=code,
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri
            )
            return token_data
            
        elif grant_type == "refresh_token":
            if not refresh_token:
                raise HTTPException(status_code=400, detail="Missing refresh token")
            
            token_data = await oauth_server.refresh_access_token(
                refresh_token=refresh_token,
                client_id=client_id,
                client_secret=client_secret
            )
            return token_data
            
        else:
            raise HTTPException(status_code=400, detail="Unsupported grant type")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth token exchange failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/oauth/revoke")
async def revoke_oauth_token(
    token: str = Form(...),
    token_type_hint: Optional[str] = Form(None),
    client = Depends(authenticate_oauth_client)
):
    """OAuth token revocation endpoint"""
    try:
        # Determine token type
        token_type = token_type_hint or "access_token"
        
        success = await oauth_server.revoke_token(token, token_type)
        
        if success:
            return {"message": "Token revoked successfully"}
        else:
            raise HTTPException(status_code=400, detail="Token revocation failed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token revocation failed: {e}")
        raise HTTPException(status_code=500, detail="Token revocation failed")

@router.post("/oauth/introspect")
async def introspect_oauth_token(
    token: str = Form(...),
    client = Depends(authenticate_oauth_client)
):
    """OAuth token introspection endpoint"""
    try:
        token_info = await oauth_server.get_token_info(token)
        return token_info
        
    except Exception as e:
        logger.error(f"Token introspection failed: {e}")
        return {"active": False}

# API Key Endpoints

@router.post("/api-keys", response_model=AuthResponse)
async def create_api_key(
    request: APIKeyCreateRequest,
    user = Depends(get_current_user)
):
    """Create a new API key"""
    try:
        api_key_data = await api_key_service.create_api_key(
            user_id=user.id,
            name=request.name,
            description=request.description,
            scopes=request.scopes,
            rate_limit=request.rate_limit,
            expires_in_days=request.expires_in_days,
            integration_type=request.integration_type,
            ip_whitelist=request.ip_whitelist
        )
        
        return AuthResponse(
            success=True,
            data=api_key_data
        )
    except Exception as e:
        logger.error(f"API key creation failed: {e}")
        return AuthResponse(
            success=False,
            error=f"API key creation failed: {str(e)}"
        )

@router.post("/api-keys/integration", response_model=AuthResponse)
async def create_integration_api_key(
    request: IntegrationAPIKeyRequest,
    user = Depends(get_current_user)
):
    """Create API key for specific integration"""
    try:
        api_key_data = await api_key_service.create_integration_api_key(
            user_id=user.id,
            integration_type=request.integration_type,
            integration_config=request.integration_config
        )
        
        return AuthResponse(
            success=True,
            data=api_key_data
        )
    except Exception as e:
        logger.error(f"Integration API key creation failed: {e}")
        return AuthResponse(
            success=False,
            error=f"Integration API key creation failed: {str(e)}"
        )

@router.get("/api-keys", response_model=AuthResponse)
async def list_api_keys(user = Depends(get_current_user)):
    """List user's API keys"""
    try:
        api_keys = await api_key_service.list_user_api_keys(user.id)
        
        return AuthResponse(
            success=True,
            data={
                "api_keys": api_keys,
                "total": len(api_keys)
            }
        )
    except Exception as e:
        logger.error(f"API key listing failed: {e}")
        return AuthResponse(
            success=False,
            error=f"Failed to list API keys: {str(e)}"
        )

@router.get("/api-keys/{key_id}", response_model=AuthResponse)
async def get_api_key(key_id: str, user = Depends(get_current_user)):
    """Get API key information"""
    try:
        api_key_info = await api_key_service.get_api_key_info(key_id)
        
        if not api_key_info:
            return AuthResponse(
                success=False,
                error="API key not found"
            )
        
        # Check ownership
        if api_key_info["user_id"] != user.id:
            return AuthResponse(
                success=False,
                error="Access denied"
            )
        
        return AuthResponse(
            success=True,
            data=api_key_info
        )
    except Exception as e:
        logger.error(f"API key retrieval failed: {e}")
        return AuthResponse(
            success=False,
            error=f"Failed to get API key: {str(e)}"
        )

@router.put("/api-keys/{key_id}", response_model=AuthResponse)
async def update_api_key(
    key_id: str,
    request: APIKeyUpdateRequest,
    user = Depends(get_current_user)
):
    """Update API key"""
    try:
        success = await api_key_service.update_api_key(
            key_id=key_id,
            user_id=user.id,
            name=request.name,
            description=request.description,
            scopes=request.scopes,
            rate_limit=request.rate_limit
        )
        
        if success:
            return AuthResponse(
                success=True,
                data={"message": "API key updated successfully"}
            )
        else:
            return AuthResponse(
                success=False,
                error="Failed to update API key"
            )
    except Exception as e:
        logger.error(f"API key update failed: {e}")
        return AuthResponse(
            success=False,
            error=f"API key update failed: {str(e)}"
        )

@router.post("/api-keys/{key_id}/revoke", response_model=AuthResponse)
async def revoke_api_key(key_id: str, user = Depends(get_current_user)):
    """Revoke (deactivate) API key"""
    try:
        success = await api_key_service.revoke_api_key(key_id, user.id)
        
        if success:
            return AuthResponse(
                success=True,
                data={"message": "API key revoked successfully"}
            )
        else:
            return AuthResponse(
                success=False,
                error="Failed to revoke API key"
            )
    except Exception as e:
        logger.error(f"API key revocation failed: {e}")
        return AuthResponse(
            success=False,
            error=f"API key revocation failed: {str(e)}"
        )

@router.delete("/api-keys/{key_id}", response_model=AuthResponse)
async def delete_api_key(key_id: str, user = Depends(get_current_user)):
    """Delete API key permanently"""
    try:
        success = await api_key_service.delete_api_key(key_id, user.id)
        
        if success:
            return AuthResponse(
                success=True,
                data={"message": "API key deleted successfully"}
            )
        else:
            return AuthResponse(
                success=False,
                error="Failed to delete API key"
            )
    except Exception as e:
        logger.error(f"API key deletion failed: {e}")
        return AuthResponse(
            success=False,
            error=f"API key deletion failed: {str(e)}"
        )

# Authentication verification endpoints

@router.get("/verify/oauth")
async def verify_oauth_token(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)):
    """Verify OAuth access token"""
    try:
        token_info = await oauth_server.verify_access_token(credentials.credentials)
        
        if token_info:
            return {
                "valid": True,
                "user_id": token_info["user_id"],
                "client_id": token_info["client_id"],
                "scopes": token_info["scopes"],
                "expires_at": token_info["expires_at"].isoformat()
            }
        else:
            return {"valid": False}
            
    except Exception as e:
        logger.error(f"OAuth token verification failed: {e}")
        return {"valid": False, "error": str(e)}

@router.get("/verify/api-key")
async def verify_api_key_endpoint(request: Request):
    """Verify API key"""
    try:
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return {"valid": False, "error": "API key not provided"}
        
        key_info = await api_key_service.authenticate_api_key(api_key)
        
        if key_info:
            # Check rate limit
            rate_limit_info = await api_key_service.check_rate_limit(key_info.key_id)
            
            return {
                "valid": True,
                "key_id": key_info.key_id,
                "user_id": key_info.user_id,
                "scopes": key_info.scopes,
                "rate_limit": {
                    "limit": rate_limit_info.rate_limit,
                    "remaining": rate_limit_info.requests_remaining,
                    "reset_time": rate_limit_info.reset_time.isoformat()
                }
            }
        else:
            return {"valid": False}
            
    except Exception as e:
        logger.error(f"API key verification failed: {e}")
        return {"valid": False, "error": str(e)}

# Device Flow Endpoints

@router.post("/oauth/device")
async def initiate_device_flow(request: DeviceFlowRequest):
    """Initiate OAuth device authorization flow"""
    try:
        scopes = request.scope.split()
        device_flow_data = await oauth_server.create_device_flow_code(
            client_id=request.client_id,
            scopes=scopes
        )
        
        return device_flow_data
        
    except Exception as e:
        logger.error(f"Device flow initiation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/oauth/device/authorize")
async def authorize_device_flow(
    request: DeviceAuthRequest,
    user = Depends(get_current_user)
):
    """Authorize device flow with user code"""
    try:
        success = await oauth_server.authorize_device_flow(
            user_code=request.user_code,
            user_id=user.id
        )
        
        if success:
            return {"message": "Device authorized successfully"}
        else:
            raise HTTPException(status_code=400, detail="Invalid user code")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Device authorization failed: {e}")
        raise HTTPException(status_code=500, detail="Device authorization failed")

@router.post("/oauth/device/token")
async def device_flow_token(
    grant_type: str = Form(...),
    device_code: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...)
):
    """Poll for device flow token"""
    try:
        if grant_type != "urn:ietf:params:oauth:grant-type:device_code":
            raise HTTPException(status_code=400, detail="Unsupported grant type")
        
        result = await oauth_server.poll_device_flow(
            device_code=device_code,
            client_id=client_id,
            client_secret=client_secret
        )
        
        if "error" in result:
            if result["error"] == "authorization_pending":
                raise HTTPException(status_code=400, detail=result["error_description"])
            elif result["error"] == "slow_down":
                raise HTTPException(status_code=400, detail=result["error_description"])
            else:
                raise HTTPException(status_code=400, detail=result["error_description"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Device flow token failed: {e}")
        raise HTTPException(status_code=500, detail="Device flow token failed")

# Integration-specific OAuth endpoints

@router.post("/oauth/integration/register")
async def register_integration_client(
    integration_type: str,
    name: str,
    description: str,
    redirect_uris: List[str],
    additional_config: Dict[str, Any] = {},
    user = Depends(get_current_user)
):
    """Register OAuth client for specific integration"""
    try:
        client = await oauth_server.create_integration_specific_client(
            integration_type=integration_type,
            name=name,
            description=description,
            redirect_uris=redirect_uris,
            additional_config=additional_config
        )
        
        return {
            "client_id": client.client_id,
            "client_secret": client.client_secret,
            "name": client.name,
            "integration_type": integration_type,
            "scopes": client.scopes,
            "created_at": client.created_at.isoformat(),
            "warning": "Store the client secret securely. It will not be shown again."
        }
        
    except Exception as e:
        logger.error(f"Integration client registration failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/oauth/integration/validate")
async def validate_integration_access(
    client_id: str,
    integration_type: str,
    scopes: str,
    client = Depends(authenticate_oauth_client)
):
    """Validate integration access for OAuth client"""
    try:
        requested_scopes = scopes.split()
        is_valid = await oauth_server.validate_integration_access(
            client_id=client_id,
            integration_type=integration_type,
            requested_scopes=requested_scopes
        )
        
        return {
            "valid": is_valid,
            "client_id": client_id,
            "integration_type": integration_type,
            "requested_scopes": requested_scopes
        }
        
    except Exception as e:
        logger.error(f"Integration access validation failed: {e}")
        return {"valid": False, "error": str(e)}

# Scope validation endpoint

@router.post("/validate/scopes")
async def validate_api_key_scopes(
    required_scopes: List[str],
    api_key_info = Depends(authenticate_api_key)
):
    """Validate that API key has required scopes"""
    try:
        has_access = await api_key_service.validate_scope_access(
            key_id=api_key_info.key_id,
            required_scopes=required_scopes
        )
        
        return {
            "valid": has_access,
            "key_id": api_key_info.key_id,
            "required_scopes": required_scopes,
            "available_scopes": api_key_info.scopes
        }
        
    except Exception as e:
        logger.error(f"Scope validation failed: {e}")
        return {"valid": False, "error": str(e)}

# Health check endpoint
@router.get("/health")
async def auth_health_check():
    """Health check for authentication services"""
    try:
        oauth_health = await oauth_server.health_check()
        api_key_health = await api_key_service.health_check()
        
        overall_status = "healthy" if (
            oauth_health.get("status") == "healthy" and 
            api_key_health.get("status") == "healthy"
        ) else "unhealthy"
        
        return {
            "status": overall_status,
            "oauth_server": oauth_health,
            "api_key_service": api_key_health,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Auth health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }