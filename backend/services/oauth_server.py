"""
OAuth 2.0 server implementation for external integrations
Provides secure authentication and authorization for third-party applications
"""
import asyncio
import hashlib
import secrets
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import jwt
from passlib.context import CryptContext
from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import SessionLocal
from core.redis_client import redis_client
from services.auth_service import AuthService
from core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class OAuthClient:
    client_id: str
    client_secret: str
    name: str
    description: str
    redirect_uris: List[str]
    scopes: List[str]
    client_type: str  # confidential, public
    created_at: datetime
    is_active: bool = True

@dataclass
class AuthorizationCode:
    code: str
    client_id: str
    user_id: str
    redirect_uri: str
    scopes: List[str]
    expires_at: datetime
    used: bool = False

@dataclass
class AccessToken:
    token: str
    client_id: str
    user_id: str
    scopes: List[str]
    expires_at: datetime
    token_type: str = "Bearer"

@dataclass
class RefreshToken:
    token: str
    client_id: str
    user_id: str
    scopes: List[str]
    expires_at: datetime
    access_token: str

class OAuthServer:
    def __init__(self):
        self.auth_service = AuthService()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.redis_prefix = "oauth:"
        self.jwt_secret = getattr(settings, 'OAUTH_JWT_SECRET', settings.SECRET_KEY)
        self.access_token_expire = timedelta(hours=1)
        self.refresh_token_expire = timedelta(days=30)
        self.auth_code_expire = timedelta(minutes=10)
        
    async def health_check(self) -> Dict[str, Any]:
        """Health check for OAuth server"""
        try:
            # Check Redis connection
            await redis_client.ping()
            
            # Check active clients count
            client_keys = await redis_client.keys(f"{self.redis_prefix}clients:*")
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "active_clients": len(client_keys),
                "token_expiry": {
                    "access_token_hours": self.access_token_expire.total_seconds() / 3600,
                    "refresh_token_days": self.refresh_token_expire.days
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def register_client(
        self,
        name: str,
        description: str,
        redirect_uris: List[str],
        scopes: List[str],
        client_type: str = "confidential"
    ) -> OAuthClient:
        """Register a new OAuth client"""
        try:
            # Generate client credentials
            client_id = f"client_{secrets.token_urlsafe(16)}"
            client_secret = secrets.token_urlsafe(32)
            
            # Create client object
            client = OAuthClient(
                client_id=client_id,
                client_secret=self.pwd_context.hash(client_secret),
                name=name,
                description=description,
                redirect_uris=redirect_uris,
                scopes=scopes,
                client_type=client_type,
                created_at=datetime.now()
            )
            
            # Store client in Redis
            await redis_client.setex(
                f"{self.redis_prefix}clients:{client_id}",
                86400 * 365,  # 1 year
                json.dumps(asdict(client), default=str)
            )
            
            # Return client with plain text secret (only time it's visible)
            client.client_secret = client_secret
            return client
            
        except Exception as e:
            logger.error(f"Client registration failed: {e}")
            raise Exception(f"Failed to register client: {str(e)}")

    async def authenticate_client(self, client_id: str, client_secret: str) -> Optional[OAuthClient]:
        """Authenticate OAuth client"""
        try:
            # Get client from Redis
            client_data = await redis_client.get(f"{self.redis_prefix}clients:{client_id}")
            if not client_data:
                return None
            
            client_dict = json.loads(client_data)
            client = OAuthClient(**client_dict)
            
            # Verify client secret
            if not self.pwd_context.verify(client_secret, client.client_secret):
                return None
            
            # Check if client is active
            if not client.is_active:
                return None
            
            return client
            
        except Exception as e:
            logger.error(f"Client authentication failed: {e}")
            return None

    async def generate_authorization_code(
        self,
        client_id: str,
        user_id: str,
        redirect_uri: str,
        scopes: List[str]
    ) -> AuthorizationCode:
        """Generate authorization code for OAuth flow"""
        try:
            # Validate client and redirect URI
            client = await self.get_client(client_id)
            if not client or redirect_uri not in client.redirect_uris:
                raise Exception("Invalid client or redirect URI")
            
            # Validate scopes
            invalid_scopes = set(scopes) - set(client.scopes)
            if invalid_scopes:
                raise Exception(f"Invalid scopes: {invalid_scopes}")
            
            # Generate authorization code
            code = secrets.token_urlsafe(32)
            auth_code = AuthorizationCode(
                code=code,
                client_id=client_id,
                user_id=user_id,
                redirect_uri=redirect_uri,
                scopes=scopes,
                expires_at=datetime.now() + self.auth_code_expire
            )
            
            # Store authorization code
            await redis_client.setex(
                f"{self.redis_prefix}auth_codes:{code}",
                int(self.auth_code_expire.total_seconds()),
                json.dumps(asdict(auth_code), default=str)
            )
            
            return auth_code
            
        except Exception as e:
            logger.error(f"Authorization code generation failed: {e}")
            raise Exception(f"Failed to generate authorization code: {str(e)}")

    async def exchange_code_for_tokens(
        self,
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens"""
        try:
            # Authenticate client
            client = await self.authenticate_client(client_id, client_secret)
            if not client:
                raise Exception("Invalid client credentials")
            
            # Get and validate authorization code
            auth_code_data = await redis_client.get(f"{self.redis_prefix}auth_codes:{code}")
            if not auth_code_data:
                raise Exception("Invalid or expired authorization code")
            
            auth_code_dict = json.loads(auth_code_data)
            auth_code = AuthorizationCode(**auth_code_dict)
            
            # Validate authorization code
            if (auth_code.client_id != client_id or 
                auth_code.redirect_uri != redirect_uri or
                auth_code.used or
                datetime.now() > auth_code.expires_at):
                raise Exception("Invalid authorization code")
            
            # Mark code as used
            auth_code.used = True
            await redis_client.setex(
                f"{self.redis_prefix}auth_codes:{code}",
                int(self.auth_code_expire.total_seconds()),
                json.dumps(asdict(auth_code), default=str)
            )
            
            # Generate access token
            access_token = await self.generate_access_token(
                client_id=client_id,
                user_id=auth_code.user_id,
                scopes=auth_code.scopes
            )
            
            # Generate refresh token
            refresh_token = await self.generate_refresh_token(
                client_id=client_id,
                user_id=auth_code.user_id,
                scopes=auth_code.scopes,
                access_token=access_token.token
            )
            
            return {
                "access_token": access_token.token,
                "token_type": access_token.token_type,
                "expires_in": int(self.access_token_expire.total_seconds()),
                "refresh_token": refresh_token.token,
                "scope": " ".join(auth_code.scopes)
            }
            
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            raise Exception(f"Failed to exchange code for tokens: {str(e)}")

    async def generate_access_token(
        self,
        client_id: str,
        user_id: str,
        scopes: List[str]
    ) -> AccessToken:
        """Generate JWT access token"""
        try:
            # Create token payload
            payload = {
                "sub": user_id,
                "client_id": client_id,
                "scopes": scopes,
                "iat": datetime.now(),
                "exp": datetime.now() + self.access_token_expire,
                "token_type": "access"
            }
            
            # Generate JWT token
            token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
            
            # Create access token object
            access_token = AccessToken(
                token=token,
                client_id=client_id,
                user_id=user_id,
                scopes=scopes,
                expires_at=datetime.now() + self.access_token_expire
            )
            
            # Store token metadata
            await redis_client.setex(
                f"{self.redis_prefix}access_tokens:{token}",
                int(self.access_token_expire.total_seconds()),
                json.dumps(asdict(access_token), default=str)
            )
            
            return access_token
            
        except Exception as e:
            logger.error(f"Access token generation failed: {e}")
            raise Exception(f"Failed to generate access token: {str(e)}")

    async def generate_refresh_token(
        self,
        client_id: str,
        user_id: str,
        scopes: List[str],
        access_token: str
    ) -> RefreshToken:
        """Generate refresh token"""
        try:
            # Generate refresh token
            token = secrets.token_urlsafe(32)
            
            refresh_token = RefreshToken(
                token=token,
                client_id=client_id,
                user_id=user_id,
                scopes=scopes,
                expires_at=datetime.now() + self.refresh_token_expire,
                access_token=access_token
            )
            
            # Store refresh token
            await redis_client.setex(
                f"{self.redis_prefix}refresh_tokens:{token}",
                int(self.refresh_token_expire.total_seconds()),
                json.dumps(asdict(refresh_token), default=str)
            )
            
            return refresh_token
            
        except Exception as e:
            logger.error(f"Refresh token generation failed: {e}")
            raise Exception(f"Failed to generate refresh token: {str(e)}")

    async def refresh_access_token(
        self,
        refresh_token: str,
        client_id: str,
        client_secret: str
    ) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            # Authenticate client
            client = await self.authenticate_client(client_id, client_secret)
            if not client:
                raise Exception("Invalid client credentials")
            
            # Get and validate refresh token
            refresh_token_data = await redis_client.get(f"{self.redis_prefix}refresh_tokens:{refresh_token}")
            if not refresh_token_data:
                raise Exception("Invalid or expired refresh token")
            
            refresh_token_dict = json.loads(refresh_token_data)
            refresh_token_obj = RefreshToken(**refresh_token_dict)
            
            # Validate refresh token
            if (refresh_token_obj.client_id != client_id or
                datetime.now() > refresh_token_obj.expires_at):
                raise Exception("Invalid refresh token")
            
            # Revoke old access token
            await redis_client.delete(f"{self.redis_prefix}access_tokens:{refresh_token_obj.access_token}")
            
            # Generate new access token
            new_access_token = await self.generate_access_token(
                client_id=client_id,
                user_id=refresh_token_obj.user_id,
                scopes=refresh_token_obj.scopes
            )
            
            # Update refresh token with new access token
            refresh_token_obj.access_token = new_access_token.token
            await redis_client.setex(
                f"{self.redis_prefix}refresh_tokens:{refresh_token}",
                int(self.refresh_token_expire.total_seconds()),
                json.dumps(asdict(refresh_token_obj), default=str)
            )
            
            return {
                "access_token": new_access_token.token,
                "token_type": new_access_token.token_type,
                "expires_in": int(self.access_token_expire.total_seconds()),
                "scope": " ".join(refresh_token_obj.scopes)
            }
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise Exception(f"Failed to refresh token: {str(e)}")

    async def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode access token"""
        try:
            # Decode JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            
            # Check if token exists in Redis (not revoked)
            token_data = await redis_client.get(f"{self.redis_prefix}access_tokens:{token}")
            if not token_data:
                return None
            
            # Verify token type
            if payload.get("token_type") != "access":
                return None
            
            return {
                "user_id": payload.get("sub"),
                "client_id": payload.get("client_id"),
                "scopes": payload.get("scopes", []),
                "expires_at": datetime.fromtimestamp(payload.get("exp"))
            }
            
        except jwt.ExpiredSignatureError:
            logger.warning("Access token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid access token")
            return None
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None

    async def revoke_token(self, token: str, token_type: str = "access") -> bool:
        """Revoke access or refresh token"""
        try:
            if token_type == "access":
                # Remove access token
                result = await redis_client.delete(f"{self.redis_prefix}access_tokens:{token}")
                return result > 0
            elif token_type == "refresh":
                # Get refresh token to also revoke associated access token
                refresh_token_data = await redis_client.get(f"{self.redis_prefix}refresh_tokens:{token}")
                if refresh_token_data:
                    refresh_token_dict = json.loads(refresh_token_data)
                    refresh_token_obj = RefreshToken(**refresh_token_dict)
                    
                    # Revoke associated access token
                    await redis_client.delete(f"{self.redis_prefix}access_tokens:{refresh_token_obj.access_token}")
                
                # Remove refresh token
                result = await redis_client.delete(f"{self.redis_prefix}refresh_tokens:{token}")
                return result > 0
            else:
                return False
                
        except Exception as e:
            logger.error(f"Token revocation failed: {e}")
            return False

    async def get_client(self, client_id: str) -> Optional[OAuthClient]:
        """Get OAuth client by ID"""
        try:
            client_data = await redis_client.get(f"{self.redis_prefix}clients:{client_id}")
            if not client_data:
                return None
            
            client_dict = json.loads(client_data)
            return OAuthClient(**client_dict)
            
        except Exception as e:
            logger.error(f"Failed to get client: {e}")
            return None

    async def list_client_tokens(self, client_id: str) -> Dict[str, Any]:
        """List active tokens for a client"""
        try:
            # Get access tokens
            access_token_keys = await redis_client.keys(f"{self.redis_prefix}access_tokens:*")
            access_tokens = []
            
            for key in access_token_keys:
                token_data = await redis_client.get(key)
                if token_data:
                    token_dict = json.loads(token_data)
                    if token_dict.get("client_id") == client_id:
                        access_tokens.append({
                            "token": token_dict["token"][:20] + "...",  # Truncated for security
                            "user_id": token_dict["user_id"],
                            "scopes": token_dict["scopes"],
                            "expires_at": token_dict["expires_at"]
                        })
            
            # Get refresh tokens
            refresh_token_keys = await redis_client.keys(f"{self.redis_prefix}refresh_tokens:*")
            refresh_tokens = []
            
            for key in refresh_token_keys:
                token_data = await redis_client.get(key)
                if token_data:
                    token_dict = json.loads(token_data)
                    if token_dict.get("client_id") == client_id:
                        refresh_tokens.append({
                            "token": token_dict["token"][:20] + "...",  # Truncated for security
                            "user_id": token_dict["user_id"],
                            "scopes": token_dict["scopes"],
                            "expires_at": token_dict["expires_at"]
                        })
            
            return {
                "client_id": client_id,
                "access_tokens": access_tokens,
                "refresh_tokens": refresh_tokens,
                "total_active_tokens": len(access_tokens) + len(refresh_tokens)
            }
            
        except Exception as e:
            logger.error(f"Failed to list client tokens: {e}")
            return {
                "client_id": client_id,
                "access_tokens": [],
                "refresh_tokens": [],
                "total_active_tokens": 0,
                "error": str(e)
            }

    async def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get information about a token (introspection endpoint)"""
        try:
            # Try to verify as access token
            token_info = await self.verify_access_token(token)
            if token_info:
                return {
                    "active": True,
                    "token_type": "access_token",
                    "client_id": token_info["client_id"],
                    "user_id": token_info["user_id"],
                    "scopes": token_info["scopes"],
                    "expires_at": token_info["expires_at"].isoformat()
                }
            
            # Try as refresh token
            refresh_token_data = await redis_client.get(f"{self.redis_prefix}refresh_tokens:{token}")
            if refresh_token_data:
                refresh_token_dict = json.loads(refresh_token_data)
                refresh_token_obj = RefreshToken(**refresh_token_dict)
                
                if datetime.now() <= refresh_token_obj.expires_at:
                    return {
                        "active": True,
                        "token_type": "refresh_token",
                        "client_id": refresh_token_obj.client_id,
                        "user_id": refresh_token_obj.user_id,
                        "scopes": refresh_token_obj.scopes,
                        "expires_at": refresh_token_obj.expires_at.isoformat()
                    }
            
            return {"active": False}
            
        except Exception as e:
            logger.error(f"Token introspection failed: {e}")
            return {"active": False, "error": str(e)}

    async def create_integration_specific_client(
        self,
        integration_type: str,
        name: str,
        description: str,
        redirect_uris: List[str],
        additional_config: Dict[str, Any] = None
    ) -> OAuthClient:
        """Create OAuth client with integration-specific configuration"""
        try:
            # Define integration-specific scopes
            integration_scopes = {
                "zotero": ["read:library", "write:library", "read:groups"],
                "mendeley": ["read:documents", "write:documents", "read:annotations"],
                "endnote": ["read:library", "write:library", "read:references"],
                "obsidian": ["read:vault", "write:vault", "read:links"],
                "notion": ["read:workspace", "write:workspace", "read:databases"],
                "roam": ["read:graph", "write:graph", "read:blocks"],
                "grammarly": ["read:documents", "write:suggestions"],
                "latex": ["read:documents", "write:documents", "compile"],
                "pubmed": ["read:search", "read:metadata"],
                "arxiv": ["read:search", "read:papers"],
                "scholar": ["read:search", "read:citations"],
                "mobile": ["read:all", "write:all", "offline:sync"],
                "voice": ["read:all", "write:all", "voice:commands"],
                "jupyter": ["read:notebooks", "write:notebooks", "execute:code"],
                "institutional": ["read:compliance", "write:reports", "admin:users"]
            }
            
            scopes = integration_scopes.get(integration_type, ["read:basic"])
            
            # Create client with integration-specific settings
            client = await self.register_client(
                name=f"{integration_type.title()} Integration - {name}",
                description=f"{description} (Integration: {integration_type})",
                redirect_uris=redirect_uris,
                scopes=scopes,
                client_type="confidential"
            )
            
            # Store integration-specific metadata
            integration_metadata = {
                "integration_type": integration_type,
                "additional_config": additional_config or {},
                "created_for": "integration",
                "security_level": "high"
            }
            
            await redis_client.setex(
                f"{self.redis_prefix}integration_metadata:{client.client_id}",
                86400 * 365,  # 1 year
                json.dumps(integration_metadata, default=str)
            )
            
            return client
            
        except Exception as e:
            logger.error(f"Integration-specific client creation failed: {e}")
            raise Exception(f"Failed to create integration client: {str(e)}")

    async def validate_integration_access(
        self,
        client_id: str,
        integration_type: str,
        requested_scopes: List[str]
    ) -> bool:
        """Validate that client has access to specific integration"""
        try:
            # Get integration metadata
            metadata_data = await redis_client.get(f"{self.redis_prefix}integration_metadata:{client_id}")
            if not metadata_data:
                return False
            
            metadata = json.loads(metadata_data)
            
            # Check integration type match
            if metadata.get("integration_type") != integration_type:
                return False
            
            # Get client to check scopes
            client = await self.get_client(client_id)
            if not client:
                return False
            
            # Validate requested scopes are within client's allowed scopes
            invalid_scopes = set(requested_scopes) - set(client.scopes)
            return len(invalid_scopes) == 0
            
        except Exception as e:
            logger.error(f"Integration access validation failed: {e}")
            return False

    async def create_device_flow_code(
        self,
        client_id: str,
        scopes: List[str]
    ) -> Dict[str, Any]:
        """Create device authorization code for OAuth device flow"""
        try:
            # Validate client
            client = await self.get_client(client_id)
            if not client:
                raise Exception("Invalid client")
            
            # Generate device and user codes
            device_code = secrets.token_urlsafe(32)
            user_code = secrets.token_hex(4).upper()  # 8-character hex code
            
            # Store device flow data
            device_flow_data = {
                "device_code": device_code,
                "user_code": user_code,
                "client_id": client_id,
                "scopes": scopes,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(minutes=15)).isoformat(),
                "status": "pending"  # pending, authorized, denied, expired
            }
            
            # Store with both device code and user code as keys
            await redis_client.setex(
                f"{self.redis_prefix}device_flow:{device_code}",
                900,  # 15 minutes
                json.dumps(device_flow_data, default=str)
            )
            
            await redis_client.setex(
                f"{self.redis_prefix}user_code:{user_code}",
                900,  # 15 minutes
                device_code
            )
            
            return {
                "device_code": device_code,
                "user_code": user_code,
                "verification_uri": f"{getattr(settings, 'BASE_URL', 'http://localhost:8000')}/auth/device",
                "verification_uri_complete": f"{getattr(settings, 'BASE_URL', 'http://localhost:8000')}/auth/device?user_code={user_code}",
                "expires_in": 900,
                "interval": 5  # Polling interval in seconds
            }
            
        except Exception as e:
            logger.error(f"Device flow code creation failed: {e}")
            raise Exception(f"Failed to create device flow code: {str(e)}")

    async def authorize_device_flow(
        self,
        user_code: str,
        user_id: str
    ) -> bool:
        """Authorize device flow with user code"""
        try:
            # Get device code from user code
            device_code = await redis_client.get(f"{self.redis_prefix}user_code:{user_code}")
            if not device_code:
                return False
            
            # Get device flow data
            device_flow_data = await redis_client.get(f"{self.redis_prefix}device_flow:{device_code}")
            if not device_flow_data:
                return False
            
            device_flow = json.loads(device_flow_data)
            
            # Check if not expired
            if datetime.now() > datetime.fromisoformat(device_flow["expires_at"]):
                return False
            
            # Update status and add user
            device_flow["status"] = "authorized"
            device_flow["user_id"] = user_id
            device_flow["authorized_at"] = datetime.now().isoformat()
            
            # Store updated data
            await redis_client.setex(
                f"{self.redis_prefix}device_flow:{device_code}",
                900,  # Keep for remaining time
                json.dumps(device_flow, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Device flow authorization failed: {e}")
            return False

    async def poll_device_flow(
        self,
        device_code: str,
        client_id: str,
        client_secret: str
    ) -> Dict[str, Any]:
        """Poll device flow for authorization status"""
        try:
            # Authenticate client
            client = await self.authenticate_client(client_id, client_secret)
            if not client:
                raise Exception("Invalid client credentials")
            
            # Get device flow data
            device_flow_data = await redis_client.get(f"{self.redis_prefix}device_flow:{device_code}")
            if not device_flow_data:
                return {"error": "invalid_request", "error_description": "Invalid device code"}
            
            device_flow = json.loads(device_flow_data)
            
            # Check client match
            if device_flow["client_id"] != client_id:
                return {"error": "invalid_client", "error_description": "Client mismatch"}
            
            # Check expiration
            if datetime.now() > datetime.fromisoformat(device_flow["expires_at"]):
                return {"error": "expired_token", "error_description": "Device code expired"}
            
            # Check status
            if device_flow["status"] == "pending":
                return {"error": "authorization_pending", "error_description": "User has not yet authorized"}
            elif device_flow["status"] == "denied":
                return {"error": "access_denied", "error_description": "User denied authorization"}
            elif device_flow["status"] == "authorized":
                # Generate tokens
                access_token = await self.generate_access_token(
                    client_id=client_id,
                    user_id=device_flow["user_id"],
                    scopes=device_flow["scopes"]
                )
                
                refresh_token = await self.generate_refresh_token(
                    client_id=client_id,
                    user_id=device_flow["user_id"],
                    scopes=device_flow["scopes"],
                    access_token=access_token.token
                )
                
                # Clean up device flow data
                await redis_client.delete(f"{self.redis_prefix}device_flow:{device_code}")
                await redis_client.delete(f"{self.redis_prefix}user_code:{device_flow['user_code']}")
                
                return {
                    "access_token": access_token.token,
                    "token_type": access_token.token_type,
                    "expires_in": int(self.access_token_expire.total_seconds()),
                    "refresh_token": refresh_token.token,
                    "scope": " ".join(device_flow["scopes"])
                }
            
            return {"error": "invalid_request", "error_description": "Unknown status"}
            
        except Exception as e:
            logger.error(f"Device flow polling failed: {e}")
            return {"error": "server_error", "error_description": str(e)}