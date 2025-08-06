"""
API Key management service with rate limiting and security features
Provides alternative authentication method for external integrations
"""
import asyncio
import hashlib
import secrets
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from passlib.context import CryptContext

from core.redis_client import redis_client

logger = logging.getLogger(__name__)

@dataclass
class APIKey:
    key_id: str
    key_hash: str
    name: str
    description: str
    user_id: str
    scopes: List[str]
    rate_limit: int  # requests per minute
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = True
    expires_at: Optional[datetime] = None

@dataclass
class RateLimitInfo:
    key_id: str
    requests_made: int
    requests_remaining: int
    reset_time: datetime
    rate_limit: int

@dataclass
class APIKeyUsage:
    key_id: str
    timestamp: datetime
    endpoint: str
    method: str
    status_code: int
    response_time: float
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

class APIKeyService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.redis_prefix = "api_keys:"
        self.rate_limit_prefix = "rate_limit:"
        self.usage_prefix = "usage:"
        self.default_rate_limit = 1000  # requests per minute
        self.key_prefix = "ak_"  # API key prefix
        
    async def health_check(self) -> Dict[str, Any]:
        """Health check for API key service"""
        try:
            # Check Redis connection
            await redis_client.ping()
            
            # Count active API keys
            key_keys = await redis_client.keys(f"{self.redis_prefix}keys:*")
            active_keys = 0
            
            for key in key_keys:
                key_data = await redis_client.get(key)
                if key_data:
                    key_dict = json.loads(key_data)
                    if key_dict.get("is_active", False):
                        active_keys += 1
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "total_keys": len(key_keys),
                "active_keys": active_keys,
                "default_rate_limit": self.default_rate_limit
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def create_api_key(
        self,
        user_id: str,
        name: str,
        description: str,
        scopes: List[str],
        rate_limit: Optional[int] = None,
        expires_in_days: Optional[int] = None,
        integration_type: Optional[str] = None,
        ip_whitelist: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new API key"""
        try:
            # Generate API key
            key_id = f"key_{secrets.token_urlsafe(16)}"
            raw_key = f"{self.key_prefix}{secrets.token_urlsafe(32)}"
            key_hash = self.pwd_context.hash(raw_key)
            
            # Set expiration if specified
            expires_at = None
            if expires_in_days:
                expires_at = datetime.now() + timedelta(days=expires_in_days)
            
            # Create API key object
            api_key = APIKey(
                key_id=key_id,
                key_hash=key_hash,
                name=name,
                description=description,
                user_id=user_id,
                scopes=scopes,
                rate_limit=rate_limit or self.default_rate_limit,
                created_at=datetime.now(),
                expires_at=expires_at
            )
            
            # Store integration-specific metadata if provided
            if integration_type or ip_whitelist:
                metadata = {
                    "integration_type": integration_type,
                    "ip_whitelist": ip_whitelist or [],
                    "security_level": "high" if integration_type else "standard"
                }
                await redis_client.setex(
                    f"{self.redis_prefix}metadata:{key_id}",
                    ttl or 86400 * 365,  # 1 year default
                    json.dumps(metadata, default=str)
                )
            
            # Store API key
            ttl = int((expires_at - datetime.now()).total_seconds()) if expires_at else None
            await redis_client.set(
                f"{self.redis_prefix}keys:{key_id}",
                json.dumps(asdict(api_key), default=str),
                ex=ttl
            )
            
            # Create reverse lookup (hash to key_id)
            await redis_client.set(
                f"{self.redis_prefix}lookup:{hashlib.sha256(raw_key.encode()).hexdigest()}",
                key_id,
                ex=ttl
            )
            
            # Initialize rate limit counter
            await self._initialize_rate_limit(key_id, api_key.rate_limit)
            
            return {
                "key_id": key_id,
                "api_key": raw_key,  # Only returned once
                "name": name,
                "scopes": scopes,
                "rate_limit": api_key.rate_limit,
                "created_at": api_key.created_at.isoformat(),
                "expires_at": expires_at.isoformat() if expires_at else None,
                "warning": "Store this API key securely. It will not be shown again."
            }
            
        except Exception as e:
            logger.error(f"API key creation failed: {e}")
            raise Exception(f"Failed to create API key: {str(e)}")

    async def authenticate_api_key(
        self, 
        raw_key: str, 
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[APIKey]:
        """Authenticate API key and return key info with security checks"""
        try:
            # Get key_id from hash lookup
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
            key_id = await redis_client.get(f"{self.redis_prefix}lookup:{key_hash}")
            
            if not key_id:
                return None
            
            # Get API key data
            key_data = await redis_client.get(f"{self.redis_prefix}keys:{key_id}")
            if not key_data:
                return None
            
            key_dict = json.loads(key_data)
            api_key = APIKey(**key_dict)
            
            # Check if key is active
            if not api_key.is_active:
                return None
            
            # Check if key is expired
            if api_key.expires_at and datetime.now() > api_key.expires_at:
                return None
            
            # Verify key hash
            if not self.pwd_context.verify(raw_key, api_key.key_hash):
                return None
            
            # Check IP whitelist if configured
            if client_ip:
                metadata_data = await redis_client.get(f"{self.redis_prefix}metadata:{key_id}")
                if metadata_data:
                    metadata = json.loads(metadata_data)
                    ip_whitelist = metadata.get("ip_whitelist", [])
                    if ip_whitelist and client_ip not in ip_whitelist:
                        logger.warning(f"API key {key_id} access denied from IP {client_ip}")
                        return None
            
            # Check for suspicious activity
            if await self._detect_suspicious_activity(key_id, client_ip, user_agent):
                logger.warning(f"Suspicious activity detected for API key {key_id}")
                return None
            
            # Update last used timestamp
            api_key.last_used = datetime.now()
            await redis_client.set(
                f"{self.redis_prefix}keys:{key_id}",
                json.dumps(asdict(api_key), default=str)
            )
            
            return api_key
            
        except Exception as e:
            logger.error(f"API key authentication failed: {e}")
            return None

    async def _detect_suspicious_activity(
        self,
        key_id: str,
        client_ip: Optional[str],
        user_agent: Optional[str]
    ) -> bool:
        """Detect suspicious activity patterns"""
        try:
            current_time = datetime.now()
            
            # Check for rapid requests from different IPs (potential key compromise)
            if client_ip:
                recent_ips_key = f"{self.redis_prefix}recent_ips:{key_id}"
                recent_ips = await redis_client.get(recent_ips_key)
                
                if recent_ips:
                    ip_list = json.loads(recent_ips)
                    # If more than 5 different IPs in last hour, flag as suspicious
                    if len(set(ip_list)) > 5:
                        return True
                    ip_list.append(client_ip)
                else:
                    ip_list = [client_ip]
                
                # Keep only last 10 IPs and set 1-hour expiry
                await redis_client.setex(
                    recent_ips_key,
                    3600,
                    json.dumps(ip_list[-10:])
                )
            
            # Check for unusual user agent patterns
            if user_agent:
                # Flag if user agent changes frequently (potential automation)
                ua_key = f"{self.redis_prefix}user_agents:{key_id}"
                recent_uas = await redis_client.get(ua_key)
                
                if recent_uas:
                    ua_list = json.loads(recent_uas)
                    if len(set(ua_list)) > 3:  # More than 3 different UAs in last hour
                        return True
                    ua_list.append(user_agent)
                else:
                    ua_list = [user_agent]
                
                await redis_client.setex(
                    ua_key,
                    3600,
                    json.dumps(ua_list[-5:])
                )
            
            return False
            
        except Exception as e:
            logger.error(f"Suspicious activity detection failed: {e}")
            return False

    async def create_integration_api_key(
        self,
        user_id: str,
        integration_type: str,
        integration_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create API key specifically for external integrations"""
        try:
            # Define integration-specific settings
            integration_settings = {
                "zotero": {
                    "scopes": ["read:library", "write:library"],
                    "rate_limit": 500,
                    "expires_days": 90
                },
                "mendeley": {
                    "scopes": ["read:documents", "write:documents"],
                    "rate_limit": 300,
                    "expires_days": 90
                },
                "endnote": {
                    "scopes": ["read:library", "write:library"],
                    "rate_limit": 200,
                    "expires_days": 90
                },
                "obsidian": {
                    "scopes": ["read:vault", "write:vault"],
                    "rate_limit": 1000,
                    "expires_days": 365
                },
                "notion": {
                    "scopes": ["read:workspace", "write:workspace"],
                    "rate_limit": 300,
                    "expires_days": 90
                },
                "roam": {
                    "scopes": ["read:graph", "write:graph"],
                    "rate_limit": 500,
                    "expires_days": 90
                },
                "mobile": {
                    "scopes": ["read:all", "write:all", "offline:sync"],
                    "rate_limit": 2000,
                    "expires_days": 365
                },
                "voice": {
                    "scopes": ["read:all", "write:all", "voice:commands"],
                    "rate_limit": 1500,
                    "expires_days": 180
                },
                "jupyter": {
                    "scopes": ["read:notebooks", "write:notebooks", "execute:code"],
                    "rate_limit": 800,
                    "expires_days": 180
                }
            }
            
            settings = integration_settings.get(integration_type, {
                "scopes": ["read:basic"],
                "rate_limit": 100,
                "expires_days": 30
            })
            
            # Create API key with integration-specific settings
            api_key_data = await self.create_api_key(
                user_id=user_id,
                name=f"{integration_type.title()} Integration",
                description=f"API key for {integration_type} integration",
                scopes=settings["scopes"],
                rate_limit=settings["rate_limit"],
                expires_in_days=settings["expires_days"],
                integration_type=integration_type,
                ip_whitelist=integration_config.get("ip_whitelist")
            )
            
            # Add integration-specific metadata
            api_key_data["integration_type"] = integration_type
            api_key_data["integration_config"] = integration_config
            
            return api_key_data
            
        except Exception as e:
            logger.error(f"Integration API key creation failed: {e}")
            raise Exception(f"Failed to create integration API key: {str(e)}")

    async def validate_scope_access(
        self,
        key_id: str,
        required_scopes: List[str]
    ) -> bool:
        """Validate that API key has required scopes"""
        try:
            # Get API key
            key_data = await redis_client.get(f"{self.redis_prefix}keys:{key_id}")
            if not key_data:
                return False
            
            key_dict = json.loads(key_data)
            api_key_scopes = key_dict.get("scopes", [])
            
            # Check if all required scopes are present
            missing_scopes = set(required_scopes) - set(api_key_scopes)
            return len(missing_scopes) == 0
            
        except Exception as e:
            logger.error(f"Scope validation failed: {e}")
            return False

    async def check_rate_limit(self, key_id: str) -> RateLimitInfo:
        """Check and update rate limit for API key"""
        try:
            # Get API key to get rate limit
            key_data = await redis_client.get(f"{self.redis_prefix}keys:{key_id}")
            if not key_data:
                raise Exception("API key not found")
            
            key_dict = json.loads(key_data)
            rate_limit = key_dict.get("rate_limit", self.default_rate_limit)
            
            # Get current minute window
            current_minute = datetime.now().replace(second=0, microsecond=0)
            rate_limit_key = f"{self.rate_limit_prefix}{key_id}:{int(current_minute.timestamp())}"
            
            # Get current request count
            current_count = await redis_client.get(rate_limit_key)
            current_count = int(current_count) if current_count else 0
            
            # Check if rate limit exceeded
            if current_count >= rate_limit:
                return RateLimitInfo(
                    key_id=key_id,
                    requests_made=current_count,
                    requests_remaining=0,
                    reset_time=current_minute + timedelta(minutes=1),
                    rate_limit=rate_limit
                )
            
            # Increment request count
            await redis_client.incr(rate_limit_key)
            await redis_client.expire(rate_limit_key, 60)  # Expire after 1 minute
            
            return RateLimitInfo(
                key_id=key_id,
                requests_made=current_count + 1,
                requests_remaining=rate_limit - current_count - 1,
                reset_time=current_minute + timedelta(minutes=1),
                rate_limit=rate_limit
            )
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Return conservative rate limit info on error
            return RateLimitInfo(
                key_id=key_id,
                requests_made=0,
                requests_remaining=0,
                reset_time=datetime.now() + timedelta(minutes=1),
                rate_limit=0
            )

    async def log_api_usage(
        self,
        key_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Log API key usage for analytics"""
        try:
            usage = APIKeyUsage(
                key_id=key_id,
                timestamp=datetime.now(),
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time=response_time,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            # Store usage log (with TTL to prevent infinite growth)
            usage_key = f"{self.usage_prefix}{key_id}:{int(datetime.now().timestamp())}"
            await redis_client.setex(
                usage_key,
                86400 * 30,  # Keep for 30 days
                json.dumps(asdict(usage), default=str)
            )
            
            # Update usage statistics
            await self._update_usage_stats(key_id, usage)
            
        except Exception as e:
            logger.error(f"Failed to log API usage: {e}")

    async def get_api_key_info(self, key_id: str) -> Optional[Dict[str, Any]]:
        """Get API key information (without sensitive data)"""
        try:
            key_data = await redis_client.get(f"{self.redis_prefix}keys:{key_id}")
            if not key_data:
                return None
            
            key_dict = json.loads(key_data)
            api_key = APIKey(**key_dict)
            
            # Get usage statistics
            usage_stats = await self._get_usage_stats(key_id)
            
            return {
                "key_id": api_key.key_id,
                "name": api_key.name,
                "description": api_key.description,
                "user_id": api_key.user_id,
                "scopes": api_key.scopes,
                "rate_limit": api_key.rate_limit,
                "created_at": api_key.created_at.isoformat(),
                "last_used": api_key.last_used.isoformat() if api_key.last_used else None,
                "is_active": api_key.is_active,
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                "usage_stats": usage_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get API key info: {e}")
            return None

    async def list_user_api_keys(self, user_id: str) -> List[Dict[str, Any]]:
        """List all API keys for a user"""
        try:
            # Get all API keys
            key_keys = await redis_client.keys(f"{self.redis_prefix}keys:*")
            user_keys = []
            
            for key in key_keys:
                key_data = await redis_client.get(key)
                if key_data:
                    key_dict = json.loads(key_data)
                    if key_dict.get("user_id") == user_id:
                        # Get usage stats
                        usage_stats = await self._get_usage_stats(key_dict["key_id"])
                        
                        user_keys.append({
                            "key_id": key_dict["key_id"],
                            "name": key_dict["name"],
                            "description": key_dict["description"],
                            "scopes": key_dict["scopes"],
                            "rate_limit": key_dict["rate_limit"],
                            "created_at": key_dict["created_at"],
                            "last_used": key_dict.get("last_used"),
                            "is_active": key_dict["is_active"],
                            "expires_at": key_dict.get("expires_at"),
                            "usage_stats": usage_stats
                        })
            
            # Sort by creation date (newest first)
            user_keys.sort(key=lambda x: x["created_at"], reverse=True)
            return user_keys
            
        except Exception as e:
            logger.error(f"Failed to list user API keys: {e}")
            return []

    async def revoke_api_key(self, key_id: str, user_id: str) -> bool:
        """Revoke (deactivate) an API key"""
        try:
            # Get API key
            key_data = await redis_client.get(f"{self.redis_prefix}keys:{key_id}")
            if not key_data:
                return False
            
            key_dict = json.loads(key_data)
            
            # Check ownership
            if key_dict.get("user_id") != user_id:
                return False
            
            # Deactivate key
            key_dict["is_active"] = False
            await redis_client.set(
                f"{self.redis_prefix}keys:{key_id}",
                json.dumps(key_dict, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke API key: {e}")
            return False

    async def delete_api_key(self, key_id: str, user_id: str) -> bool:
        """Permanently delete an API key"""
        try:
            # Get API key
            key_data = await redis_client.get(f"{self.redis_prefix}keys:{key_id}")
            if not key_data:
                return False
            
            key_dict = json.loads(key_data)
            
            # Check ownership
            if key_dict.get("user_id") != user_id:
                return False
            
            # Delete API key
            await redis_client.delete(f"{self.redis_prefix}keys:{key_id}")
            
            # Delete lookup entry (we need to find it)
            lookup_keys = await redis_client.keys(f"{self.redis_prefix}lookup:*")
            for lookup_key in lookup_keys:
                lookup_value = await redis_client.get(lookup_key)
                if lookup_value == key_id:
                    await redis_client.delete(lookup_key)
                    break
            
            # Clean up rate limit and usage data
            await self._cleanup_key_data(key_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete API key: {e}")
            return False

    async def update_api_key(
        self,
        key_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        rate_limit: Optional[int] = None
    ) -> bool:
        """Update API key properties"""
        try:
            # Get API key
            key_data = await redis_client.get(f"{self.redis_prefix}keys:{key_id}")
            if not key_data:
                return False
            
            key_dict = json.loads(key_data)
            
            # Check ownership
            if key_dict.get("user_id") != user_id:
                return False
            
            # Update fields
            if name is not None:
                key_dict["name"] = name
            if description is not None:
                key_dict["description"] = description
            if scopes is not None:
                key_dict["scopes"] = scopes
            if rate_limit is not None:
                key_dict["rate_limit"] = rate_limit
                # Update rate limit initialization
                await self._initialize_rate_limit(key_id, rate_limit)
            
            # Save updated key
            await redis_client.set(
                f"{self.redis_prefix}keys:{key_id}",
                json.dumps(key_dict, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update API key: {e}")
            return False

    async def _initialize_rate_limit(self, key_id: str, rate_limit: int):
        """Initialize rate limit counter for API key"""
        try:
            current_minute = datetime.now().replace(second=0, microsecond=0)
            rate_limit_key = f"{self.rate_limit_prefix}{key_id}:{int(current_minute.timestamp())}"
            
            # Set initial count to 0 if not exists
            await redis_client.setnx(rate_limit_key, 0)
            await redis_client.expire(rate_limit_key, 60)
            
        except Exception as e:
            logger.error(f"Failed to initialize rate limit: {e}")

    async def _update_usage_stats(self, key_id: str, usage: APIKeyUsage):
        """Update usage statistics for API key"""
        try:
            stats_key = f"{self.redis_prefix}stats:{key_id}"
            
            # Get current stats
            stats_data = await redis_client.get(stats_key)
            if stats_data:
                stats = json.loads(stats_data)
            else:
                stats = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "avg_response_time": 0.0,
                    "endpoints": {},
                    "last_updated": datetime.now().isoformat()
                }
            
            # Update stats
            stats["total_requests"] += 1
            if 200 <= usage.status_code < 400:
                stats["successful_requests"] += 1
            else:
                stats["failed_requests"] += 1
            
            # Update average response time
            current_avg = stats["avg_response_time"]
            total_requests = stats["total_requests"]
            stats["avg_response_time"] = ((current_avg * (total_requests - 1)) + usage.response_time) / total_requests
            
            # Update endpoint stats
            if usage.endpoint not in stats["endpoints"]:
                stats["endpoints"][usage.endpoint] = {"count": 0, "avg_response_time": 0.0}
            
            endpoint_stats = stats["endpoints"][usage.endpoint]
            endpoint_count = endpoint_stats["count"]
            endpoint_avg = endpoint_stats["avg_response_time"]
            
            endpoint_stats["count"] += 1
            endpoint_stats["avg_response_time"] = ((endpoint_avg * endpoint_count) + usage.response_time) / (endpoint_count + 1)
            
            stats["last_updated"] = datetime.now().isoformat()
            
            # Store updated stats
            await redis_client.setex(
                stats_key,
                86400 * 30,  # Keep for 30 days
                json.dumps(stats, default=str)
            )
            
        except Exception as e:
            logger.error(f"Failed to update usage stats: {e}")

    async def _get_usage_stats(self, key_id: str) -> Dict[str, Any]:
        """Get usage statistics for API key"""
        try:
            stats_data = await redis_client.get(f"{self.redis_prefix}stats:{key_id}")
            if stats_data:
                return json.loads(stats_data)
            else:
                return {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "avg_response_time": 0.0,
                    "endpoints": {},
                    "last_updated": None
                }
                
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {}

    async def _cleanup_key_data(self, key_id: str):
        """Clean up all data associated with an API key"""
        try:
            # Clean up rate limit data
            rate_limit_keys = await redis_client.keys(f"{self.rate_limit_prefix}{key_id}:*")
            if rate_limit_keys:
                await redis_client.delete(*rate_limit_keys)
            
            # Clean up usage data
            usage_keys = await redis_client.keys(f"{self.usage_prefix}{key_id}:*")
            if usage_keys:
                await redis_client.delete(*usage_keys)
            
            # Clean up stats
            await redis_client.delete(f"{self.redis_prefix}stats:{key_id}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup key data: {e}")