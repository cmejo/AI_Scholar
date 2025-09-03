"""
Zotero OAuth 2.0 authentication service with enhanced security and PKCE support
"""
import asyncio
import aiohttp
import logging
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any, List
from urllib.parse import urlencode, parse_qs, urlparse
import json
import time
import os
try:
    from cryptography.fernet import Fernet
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    logger.warning("Cryptography library not available. Token encryption will be disabled.")

from core.config import settings
from core.database import SessionLocal
from models.zotero_models import ZoteroConnection
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ZoteroAuthError(Exception):
    """Custom exception for Zotero authentication errors"""
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ZoteroAuthService:
    """
    Service for handling Zotero OAuth 2.0 authentication flow with enhanced security, PKCE support, and error handling
    """
    
    def __init__(self):
        self.client_id = settings.ZOTERO_CLIENT_ID
        self.client_secret = settings.ZOTERO_CLIENT_SECRET
        self.redirect_uri = settings.ZOTERO_REDIRECT_URI
        self.oauth_base_url = settings.ZOTERO_OAUTH_BASE_URL
        self.api_base_url = settings.ZOTERO_API_BASE_URL
        
        # OAuth state storage (in production, use Redis or database)
        self._oauth_states: Dict[str, Dict[str, Any]] = {}
        
        # PKCE code verifier storage
        self._pkce_verifiers: Dict[str, str] = {}
        
        # Rate limiting for OAuth requests
        self._last_request_time = 0
        self._min_request_interval = 1.0  # 1 second between requests
        
        # Enhanced security features
        self._max_state_age = timedelta(minutes=10)  # States expire after 10 minutes
        self._max_stored_states = 1000  # Prevent memory exhaustion
        
        # Initialize encryption for sensitive data
        self._init_encryption()
    
    def _init_encryption(self):
        """Initialize encryption for sensitive data storage"""
        if not ENCRYPTION_AVAILABLE:
            logger.warning("Encryption not available - cryptography library not installed")
            self._cipher = None
            return
            
        try:
            # Use a key from environment or generate one (in production, use a proper key management system)
            encryption_key = os.environ.get('ZOTERO_ENCRYPTION_KEY')
            if not encryption_key:
                # Generate a key for development (not secure for production)
                encryption_key = Fernet.generate_key().decode()
                logger.warning("Using generated encryption key. Set ZOTERO_ENCRYPTION_KEY environment variable for production.")
            
            if isinstance(encryption_key, str):
                encryption_key = encryption_key.encode()
            
            self._cipher = Fernet(encryption_key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            # Fallback to no encryption (not recommended for production)
            self._cipher = None
    
    def _encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data like tokens"""
        if self._cipher and data:
            try:
                return self._cipher.encrypt(data.encode()).decode()
            except Exception as e:
                logger.error(f"Encryption failed: {e}")
                return data
        return data
    
    def _decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data like tokens"""
        if self._cipher and encrypted_data:
            try:
                return self._cipher.decrypt(encrypted_data.encode()).decode()
            except Exception as e:
                logger.error(f"Decryption failed: {e}")
                return encrypted_data
        return encrypted_data
    
    def _generate_pkce_challenge(self) -> Tuple[str, str]:
        """
        Generate PKCE code verifier and challenge for enhanced OAuth security
        
        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate code verifier (43-128 characters, URL-safe)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Generate code challenge (SHA256 hash of verifier, base64url encoded)
        challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def generate_oauth_state(self, user_id: str, use_pkce: bool = True) -> Tuple[str, Optional[str]]:
        """
        Generate a secure random state parameter for OAuth with enhanced security and optional PKCE
        
        Args:
            user_id: User ID to associate with the state
            use_pkce: Whether to use PKCE for enhanced security
            
        Returns:
            Tuple of (state, code_challenge) - code_challenge is None if PKCE is disabled
        """
        # Clean up expired states first to prevent memory exhaustion
        self._cleanup_expired_states()
        
        # Check if we have too many stored states
        if len(self._oauth_states) >= self._max_stored_states:
            logger.warning(f"Too many stored OAuth states ({len(self._oauth_states)}), cleaning up oldest")
            self._cleanup_oldest_states()
        
        state = secrets.token_urlsafe(32)
        code_challenge = None
        code_verifier = None
        
        # Generate PKCE parameters if enabled
        if use_pkce:
            code_verifier, code_challenge = self._generate_pkce_challenge()
            self._pkce_verifiers[state] = code_verifier
        
        # Store state with metadata for validation
        self._oauth_states[state] = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + self._max_state_age,
            "used": False,
            "use_pkce": use_pkce,
            "ip_address": None,  # Could be populated from request context
            "user_agent": None   # Could be populated from request context
        }
        
        logger.debug(f"Generated OAuth state for user {user_id} with PKCE: {use_pkce}")
        
        return state, code_challenge
    
    def _cleanup_expired_states(self):
        """Remove expired OAuth states and PKCE verifiers"""
        now = datetime.now()
        expired_states = [
            state for state, data in self._oauth_states.items()
            if data["expires_at"] < now
        ]
        
        for state in expired_states:
            # Clean up OAuth state
            del self._oauth_states[state]
            
            # Clean up corresponding PKCE verifier
            if state in self._pkce_verifiers:
                del self._pkce_verifiers[state]
        
        if expired_states:
            logger.debug(f"Cleaned up {len(expired_states)} expired OAuth states")
    
    def _cleanup_oldest_states(self, keep_count: int = 500):
        """Remove oldest OAuth states to prevent memory exhaustion"""
        if len(self._oauth_states) <= keep_count:
            return
        
        # Sort states by creation time and remove oldest
        sorted_states = sorted(
            self._oauth_states.items(),
            key=lambda x: x[1]["created_at"]
        )
        
        states_to_remove = sorted_states[:-keep_count]
        
        for state, _ in states_to_remove:
            del self._oauth_states[state]
            if state in self._pkce_verifiers:
                del self._pkce_verifiers[state]
        
        logger.warning(f"Cleaned up {len(states_to_remove)} oldest OAuth states to prevent memory exhaustion")
    
    def validate_oauth_state(self, state: str, user_id: str, additional_checks: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate OAuth state parameter with enhanced security checks
        
        Args:
            state: OAuth state to validate
            user_id: Expected user ID
            additional_checks: Optional additional validation parameters (IP, user agent, etc.)
            
        Returns:
            True if state is valid, False otherwise
        """
        if not state or state not in self._oauth_states:
            logger.warning(f"Invalid OAuth state: {state[:10] if state else 'None'}...")
            return False
        
        state_data = self._oauth_states[state]
        
        # Check if state is expired
        if datetime.now() > state_data["expires_at"]:
            logger.warning(f"Expired OAuth state: {state[:10]}... (expired at {state_data['expires_at']})")
            self._cleanup_state(state)
            return False
        
        # Check if state was already used (replay attack protection)
        if state_data["used"]:
            logger.warning(f"OAuth state already used (potential replay attack): {state[:10]}...")
            return False
        
        # Check if user ID matches
        if state_data["user_id"] != user_id:
            logger.warning(f"OAuth state user ID mismatch: expected {user_id}, got {state_data['user_id']}")
            return False
        
        # Additional security checks if provided
        if additional_checks:
            if "ip_address" in additional_checks and state_data.get("ip_address"):
                if additional_checks["ip_address"] != state_data["ip_address"]:
                    logger.warning(f"OAuth state IP address mismatch for user {user_id}")
                    return False
            
            if "user_agent" in additional_checks and state_data.get("user_agent"):
                if additional_checks["user_agent"] != state_data["user_agent"]:
                    logger.warning(f"OAuth state user agent mismatch for user {user_id}")
                    return False
        
        # Mark state as used
        state_data["used"] = True
        state_data["validated_at"] = datetime.now()
        
        logger.debug(f"Successfully validated OAuth state for user {user_id}")
        return True
    
    def _cleanup_state(self, state: str):
        """Clean up a specific OAuth state and its PKCE verifier"""
        if state in self._oauth_states:
            del self._oauth_states[state]
        if state in self._pkce_verifiers:
            del self._pkce_verifiers[state]
    
    def get_authorization_url(
        self, 
        user_id: str, 
        scopes: Optional[List[str]] = None, 
        use_pkce: bool = True,
        additional_params: Optional[Dict[str, str]] = None
    ) -> Tuple[str, str]:
        """
        Generate the Zotero OAuth authorization URL with enhanced security and PKCE support
        
        Args:
            user_id: User ID to associate with the connection
            scopes: List of requested scopes (defaults to ['all'])
            use_pkce: Whether to use PKCE for enhanced security
            additional_params: Additional parameters to include in the authorization URL
            
        Returns:
            Tuple of (authorization_url, state)
        """
        # Generate secure state and PKCE challenge
        state, code_challenge = self.generate_oauth_state(user_id, use_pkce)
        
        # Default scopes
        if scopes is None:
            scopes = ["all"]
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "scope": " ".join(scopes)
        }
        
        # Add PKCE parameters if enabled
        if use_pkce and code_challenge:
            params.update({
                "code_challenge": code_challenge,
                "code_challenge_method": "S256"
            })
        
        # Add any additional parameters
        if additional_params:
            params.update(additional_params)
        
        auth_url = f"{self.oauth_base_url}/authorize?{urlencode(params)}"
        
        logger.info(f"Generated OAuth authorization URL for user {user_id} with scopes: {scopes}, PKCE: {use_pkce}")
        
        return auth_url, state
    
    async def _rate_limit_request(self):
        """Apply rate limiting to OAuth requests"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            wait_time = self._min_request_interval - time_since_last
            logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
        
        self._last_request_time = time.time()

    async def exchange_code_for_token(
        self,
        authorization_code: str,
        state: str,
        user_id: str,
        additional_validation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token with enhanced validation and PKCE support
        
        Args:
            authorization_code: Authorization code from OAuth callback
            state: OAuth state parameter to validate
            user_id: User ID for state validation
            additional_validation: Additional validation parameters (IP, user agent, etc.)
            
        Returns:
            Dictionary containing access token and user info
            
        Raises:
            ZoteroAuthError: If token exchange fails
        """
        # Validate state parameter with additional checks
        if not self.validate_oauth_state(state, user_id, additional_validation):
            raise ZoteroAuthError(
                "Invalid or expired OAuth state",
                error_code="INVALID_STATE"
            )
        
        # Get state data for PKCE verification
        state_data = self._oauth_states.get(state)
        if not state_data:
            raise ZoteroAuthError(
                "OAuth state not found after validation",
                error_code="STATE_NOT_FOUND"
            )
        
        # Apply rate limiting
        await self._rate_limit_request()
        
        # Prepare token request
        token_data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        # Add PKCE code verifier if this was a PKCE flow
        if state_data.get("use_pkce") and state in self._pkce_verifiers:
            token_data["code_verifier"] = self._pkce_verifiers[state]
            logger.debug(f"Including PKCE code verifier in token exchange for user {user_id}")
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": f"AI Scholar/{settings.PROJECT_NAME}",
            "Accept": "application/x-www-form-urlencoded"
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                token_url = f"{self.oauth_base_url}/access"
                
                logger.debug(f"Exchanging authorization code for access token")
                
                async with session.post(
                    token_url,
                    data=urlencode(token_data),
                    headers=headers
                ) as response:
                    
                    response_text = await response.text()
                    
                    if response.status != 200:
                        logger.error(f"Token exchange failed: {response.status} - {response_text}")
                        
                        # Parse error details if available
                        error_details = {}
                        try:
                            if response_text:
                                error_params = parse_qs(response_text)
                                error_details = {k: v[0] if v else None for k, v in error_params.items()}
                        except Exception:
                            pass
                        
                        raise ZoteroAuthError(
                            f"Token exchange failed: {response.status}",
                            error_code="TOKEN_EXCHANGE_FAILED",
                            details=error_details
                        )
                    
                    # Parse response
                    token_params = parse_qs(response_text)
                    
                    # Extract token information
                    access_token = token_params.get("access_token", [None])[0]
                    zotero_user_id = token_params.get("userID", [None])[0]
                    username = token_params.get("username", [None])[0]
                    
                    if not access_token or not zotero_user_id:
                        logger.error("Missing access_token or userID in token response")
                        raise ZoteroAuthError(
                            "Invalid token response from Zotero",
                            error_code="INVALID_TOKEN_RESPONSE",
                            details={"response": response_text}
                        )
                    
                    logger.info(f"Successfully obtained access token for Zotero user {zotero_user_id}")
                    
                    # Clean up PKCE verifier after successful exchange
                    if state in self._pkce_verifiers:
                        del self._pkce_verifiers[state]
                    
                    return {
                        "access_token": access_token,
                        "zotero_user_id": zotero_user_id,
                        "username": username or zotero_user_id,
                        "token_type": "Bearer",
                        "obtained_at": datetime.now().isoformat(),
                        "pkce_used": state_data.get("use_pkce", False)
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error during token exchange: {e}")
            raise ZoteroAuthError(
                f"HTTP client error: {e}",
                error_code="HTTP_ERROR",
                details={"error": str(e)}
            )
        except ZoteroAuthError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token exchange: {e}")
            raise ZoteroAuthError(
                f"Unexpected error: {e}",
                error_code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def store_connection(
        self,
        user_id: str,
        token_data: Dict[str, Any]
    ) -> ZoteroConnection:
        """
        Store Zotero connection in database with enhanced security
        
        Args:
            user_id: AI Scholar user ID
            token_data: Token data from OAuth exchange
            
        Returns:
            Created or updated ZoteroConnection instance
            
        Raises:
            ZoteroAuthError: If storage fails
        """
        db = SessionLocal()
        try:
            zotero_user_id = token_data["zotero_user_id"]
            access_token = token_data["access_token"]
            username = token_data.get("username")
            
            # Encrypt sensitive token data
            encrypted_access_token = self._encrypt_sensitive_data(access_token)
            
            # Check if connection already exists
            existing_connection = db.query(ZoteroConnection).filter(
                ZoteroConnection.user_id == user_id,
                ZoteroConnection.zotero_user_id == zotero_user_id
            ).first()
            
            connection_metadata = {
                "username": username,
                "token_type": token_data.get("token_type", "Bearer"),
                "obtained_at": token_data.get("obtained_at"),
                "last_validated": datetime.now().isoformat(),
                "oauth_version": "2.0",
                "pkce_used": token_data.get("pkce_used", False),
                "security_features": {
                    "encryption_enabled": self._cipher is not None,
                    "pkce_supported": True,
                    "state_validation": True
                }
            }
            
            if existing_connection:
                # Update existing connection
                existing_connection.access_token = encrypted_access_token
                existing_connection.connection_status = "active"
                existing_connection.updated_at = datetime.now()
                existing_connection.connection_metadata.update(connection_metadata)
                existing_connection.connection_metadata["last_token_refresh"] = datetime.now().isoformat()
                
                # Mark the updated metadata for SQLAlchemy
                existing_connection.connection_metadata = existing_connection.connection_metadata.copy()
                
                db.commit()
                db.refresh(existing_connection)
                
                logger.info(f"Updated existing Zotero connection for user {user_id} with enhanced security")
                return existing_connection
            else:
                # Create new connection
                connection_metadata.update({
                    "created_via": "oauth",
                    "initial_connection": datetime.now().isoformat()
                })
                
                connection = ZoteroConnection(
                    user_id=user_id,
                    zotero_user_id=zotero_user_id,
                    access_token=encrypted_access_token,
                    connection_type="oauth",
                    connection_status="active",
                    sync_enabled=True,
                    connection_metadata=connection_metadata
                )
                
                db.add(connection)
                db.commit()
                db.refresh(connection)
                
                logger.info(f"Created new Zotero connection for user {user_id} with enhanced security")
                return connection
                
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing Zotero connection: {e}")
            raise ZoteroAuthError(
                f"Failed to store connection: {e}",
                error_code="STORAGE_ERROR",
                details={"error": str(e)}
            )
        finally:
            db.close()
    
    async def create_api_key_connection(
        self,
        user_id: str,
        api_key: str,
        zotero_user_id: str
    ) -> ZoteroConnection:
        """
        Create connection using Zotero API key (alternative to OAuth)
        
        Args:
            user_id: AI Scholar user ID
            api_key: Zotero API key
            zotero_user_id: Zotero user ID
            
        Returns:
            Created ZoteroConnection instance
        """
        # Validate API key by making a test request
        from .zotero_client import ZoteroAPIClient
        
        async with ZoteroAPIClient() as client:
            is_valid = await client.test_connection(api_key, zotero_user_id)
            if not is_valid:
                raise ZoteroAuthError("Invalid API key or user ID")
        
        db = SessionLocal()
        try:
            # Check if connection already exists
            existing_connection = db.query(ZoteroConnection).filter(
                ZoteroConnection.user_id == user_id,
                ZoteroConnection.zotero_user_id == zotero_user_id
            ).first()
            
            if existing_connection:
                # Update existing connection
                existing_connection.api_key = api_key
                existing_connection.access_token = api_key  # For API key auth, token = key
                existing_connection.connection_type = "api_key"
                existing_connection.connection_status = "active"
                existing_connection.updated_at = datetime.now()
                
                db.commit()
                db.refresh(existing_connection)
                
                logger.info(f"Updated existing API key connection for user {user_id}")
                return existing_connection
            else:
                # Create new connection
                connection = ZoteroConnection(
                    user_id=user_id,
                    zotero_user_id=zotero_user_id,
                    access_token=api_key,
                    api_key=api_key,
                    connection_type="api_key",
                    connection_status="active",
                    sync_enabled=True,
                    connection_metadata={
                        "created_via": "api_key",
                        "initial_connection": datetime.now().isoformat()
                    }
                )
                
                db.add(connection)
                db.commit()
                db.refresh(connection)
                
                logger.info(f"Created new API key connection for user {user_id}")
                return connection
                
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating API key connection: {e}")
            raise ZoteroAuthError(f"Failed to create API key connection: {e}")
        finally:
            db.close()
    
    async def get_user_connections(self, user_id: str) -> list[ZoteroConnection]:
        """
        Get all Zotero connections for a user
        
        Args:
            user_id: AI Scholar user ID
            
        Returns:
            List of ZoteroConnection instances
        """
        db = SessionLocal()
        try:
            connections = db.query(ZoteroConnection).filter(
                ZoteroConnection.user_id == user_id
            ).all()
            
            return connections
        finally:
            db.close()
    
    async def get_active_connection(self, user_id: str) -> Optional[ZoteroConnection]:
        """
        Get the active Zotero connection for a user
        
        Args:
            user_id: AI Scholar user ID
            
        Returns:
            Active ZoteroConnection or None
        """
        db = SessionLocal()
        try:
            connection = db.query(ZoteroConnection).filter(
                ZoteroConnection.user_id == user_id,
                ZoteroConnection.connection_status == "active"
            ).first()
            
            return connection
        finally:
            db.close()
    
    async def revoke_connection(self, user_id: str, connection_id: str) -> bool:
        """
        Revoke a Zotero connection
        
        Args:
            user_id: AI Scholar user ID
            connection_id: Connection ID to revoke
            
        Returns:
            True if successful, False otherwise
        """
        db = SessionLocal()
        try:
            connection = db.query(ZoteroConnection).filter(
                ZoteroConnection.id == connection_id,
                ZoteroConnection.user_id == user_id
            ).first()
            
            if not connection:
                return False
            
            connection.connection_status = "revoked"
            connection.sync_enabled = False
            connection.updated_at = datetime.now()
            
            db.commit()
            
            logger.info(f"Revoked Zotero connection {connection_id} for user {user_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error revoking connection: {e}")
            return False
        finally:
            db.close()
    
    async def validate_connection(self, connection: ZoteroConnection) -> bool:
        """
        Validate that a connection is still working
        
        Args:
            connection: ZoteroConnection to validate
            
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            from .zotero_client import ZoteroAPIClient
            
            # Decrypt access token for API call
            decrypted_token = self._decrypt_sensitive_data(connection.access_token)
            
            async with ZoteroAPIClient() as client:
                test_result = await client.test_connection(
                    decrypted_token,
                    connection.zotero_user_id
                )
                is_valid = test_result.get("is_valid", False)
                
                if not is_valid:
                    # Update connection status
                    db = SessionLocal()
                    try:
                        connection.connection_status = "error"
                        connection.updated_at = datetime.now()
                        db.commit()
                    except Exception as e:
                        logger.error(f"Error updating connection status: {e}")
                    finally:
                        db.close()
                
                return is_valid
                
        except Exception as e:
            logger.error(f"Error validating connection: {e}")
            return False
    
    async def refresh_token(self, connection: ZoteroConnection) -> bool:
        """
        Refresh access token (Note: Zotero OAuth doesn't support refresh tokens)
        This method validates the existing token and updates metadata
        
        Args:
            connection: ZoteroConnection to refresh
            
        Returns:
            True if token is still valid, False otherwise
        """
        try:
            # Zotero OAuth tokens don't expire, but we can validate them
            is_valid = await self.validate_connection(connection)
            
            if is_valid:
                # Update metadata to indicate validation
                db = SessionLocal()
                try:
                    connection.connection_metadata = connection.connection_metadata or {}
                    connection.connection_metadata["last_validated"] = datetime.now().isoformat()
                    connection.updated_at = datetime.now()
                    
                    db.commit()
                    logger.info(f"Token validated for connection {connection.id}")
                    return True
                except Exception as e:
                    db.rollback()
                    logger.error(f"Error updating token validation: {e}")
                    return False
                finally:
                    db.close()
            else:
                logger.warning(f"Token validation failed for connection {connection.id}")
                return False
                
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return False
    
    async def get_connection_with_valid_token(self, user_id: str) -> Optional[ZoteroConnection]:
        """
        Get active connection with validated token
        
        Args:
            user_id: User ID
            
        Returns:
            Valid ZoteroConnection or None
        """
        connection = await self.get_active_connection(user_id)
        
        if not connection:
            return None
        
        # Check if token needs validation (validate every hour)
        last_validated = connection.connection_metadata.get("last_validated")
        if last_validated:
            try:
                last_validated_dt = datetime.fromisoformat(last_validated)
                if datetime.now() - last_validated_dt < timedelta(hours=1):
                    return connection  # Token was recently validated
            except Exception:
                pass  # Invalid timestamp, proceed with validation
        
        # Validate token
        if await self.refresh_token(connection):
            return connection
        else:
            # Token is invalid, mark connection as error
            await self._mark_connection_error(connection, "Token validation failed")
            return None
    
    async def _mark_connection_error(self, connection: ZoteroConnection, error_message: str):
        """Mark connection as having an error"""
        db = SessionLocal()
        try:
            connection.connection_status = "error"
            connection.connection_metadata = connection.connection_metadata or {}
            connection.connection_metadata["last_error"] = error_message
            connection.connection_metadata["error_timestamp"] = datetime.now().isoformat()
            connection.updated_at = datetime.now()
            
            db.commit()
            logger.warning(f"Marked connection {connection.id} as error: {error_message}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking connection as error: {e}")
        finally:
            db.close()
    
    def get_oauth_state_info(self, state: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an OAuth state
        
        Args:
            state: OAuth state parameter
            
        Returns:
            State information or None if not found
        """
        return self._oauth_states.get(state)
    
    def get_decrypted_token(self, connection: ZoteroConnection) -> str:
        """
        Get decrypted access token for API usage
        
        Args:
            connection: ZoteroConnection instance
            
        Returns:
            Decrypted access token
        """
        return self._decrypt_sensitive_data(connection.access_token)
    
    def get_connection_security_info(self, connection: ZoteroConnection) -> Dict[str, Any]:
        """
        Get security information about a connection
        
        Args:
            connection: ZoteroConnection instance
            
        Returns:
            Dictionary with security information
        """
        metadata = connection.connection_metadata or {}
        security_features = metadata.get("security_features", {})
        
        return {
            "connection_id": connection.id,
            "connection_type": connection.connection_type,
            "encryption_enabled": security_features.get("encryption_enabled", False),
            "pkce_used": metadata.get("pkce_used", False),
            "oauth_version": metadata.get("oauth_version", "unknown"),
            "created_at": connection.created_at.isoformat(),
            "last_validated": metadata.get("last_validated"),
            "security_score": self._calculate_security_score(connection)
        }
    
    def _calculate_security_score(self, connection: ZoteroConnection) -> int:
        """
        Calculate a security score for a connection (0-100)
        
        Args:
            connection: ZoteroConnection instance
            
        Returns:
            Security score (0-100)
        """
        score = 0
        metadata = connection.connection_metadata or {}
        security_features = metadata.get("security_features", {})
        
        # Base score for OAuth
        if connection.connection_type == "oauth":
            score += 40
        elif connection.connection_type == "api_key":
            score += 20
        
        # Encryption bonus
        if security_features.get("encryption_enabled"):
            score += 20
        
        # PKCE bonus
        if metadata.get("pkce_used"):
            score += 20
        
        # Recent validation bonus
        last_validated = metadata.get("last_validated")
        if last_validated:
            try:
                validated_dt = datetime.fromisoformat(last_validated)
                hours_since_validation = (datetime.now() - validated_dt).total_seconds() / 3600
                if hours_since_validation < 1:
                    score += 10
                elif hours_since_validation < 24:
                    score += 5
            except Exception:
                pass
        
        # Active status bonus
        if connection.connection_status == "active":
            score += 10
        
        return min(score, 100)