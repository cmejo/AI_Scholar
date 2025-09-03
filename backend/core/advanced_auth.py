"""
Advanced Authentication System for AI Scholar
Implements MFA, OAuth providers, and RBAC
"""

import asyncio
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import hashlib
import pyotp
import qrcode
from io import BytesIO
import base64
import logging

from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    RESEARCHER = "researcher"
    STUDENT = "student"
    VIEWER = "viewer"
    GUEST = "guest"

class Permission(Enum):
    """System permissions"""
    READ_DOCUMENTS = "read_documents"
    WRITE_DOCUMENTS = "write_documents"
    DELETE_DOCUMENTS = "delete_documents"
    MANAGE_USERS = "manage_users"
    ADMIN_PANEL = "admin_panel"
    AI_QUERIES = "ai_queries"
    EXPORT_DATA = "export_data"
    SYSTEM_CONFIG = "system_config"

@dataclass
class MFAConfig:
    """Multi-factor authentication configuration"""
    enabled: bool = False
    method: str = "totp"  # totp, sms, email
    backup_codes_count: int = 10
    totp_issuer: str = "AI Scholar"
    totp_period: int = 30

@dataclass
class OAuthProvider:
    """OAuth provider configuration"""
    name: str
    client_id: str
    client_secret: str
    authorization_url: str
    token_url: str
    user_info_url: str
    scopes: List[str]
    enabled: bool = True

@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_symbols: bool = True
    password_history_count: int = 5
    session_timeout_minutes: int = 60
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    require_mfa: bool = False

class AdvancedAuth:
    """Advanced authentication system"""
    
    def __init__(self, secret_key: str, security_policy: SecurityPolicy = None):
        self.secret_key = secret_key
        self.security_policy = security_policy or SecurityPolicy()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Role-based permissions
        self.role_permissions = {
            UserRole.ADMIN: [p for p in Permission],
            UserRole.RESEARCHER: [
                Permission.READ_DOCUMENTS,
                Permission.WRITE_DOCUMENTS,
                Permission.AI_QUERIES,
                Permission.EXPORT_DATA
            ],
            UserRole.STUDENT: [
                Permission.READ_DOCUMENTS,
                Permission.AI_QUERIES
            ],
            UserRole.VIEWER: [
                Permission.READ_DOCUMENTS
            ],
            UserRole.GUEST: []
        }
        
        # OAuth providers
        self.oauth_providers: Dict[str, OAuthProvider] = {}
        
        # Failed login attempts tracking
        self.failed_attempts: Dict[str, List[float]] = {}
        self.locked_accounts: Dict[str, float] = {}
        
        # Active sessions
        self.active_sessions: Dict[str, Dict] = {}
    
    def add_oauth_provider(self, provider: OAuthProvider):
        """Add OAuth provider"""
        self.oauth_providers[provider.name] = provider
        logger.info(f"Added OAuth provider: {provider.name}")
    
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def validate_password_policy(self, password: str) -> Dict[str, Any]:
        """Validate password against security policy"""
        errors = []
        
        if len(password) < self.security_policy.password_min_length:
            errors.append(f"Password must be at least {self.security_policy.password_min_length} characters")
        
        if self.security_policy.password_require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.security_policy.password_require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.security_policy.password_require_numbers and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if self.security_policy.password_require_symbols and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one symbol")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength": self._calculate_password_strength(password)
        }
    
    def _calculate_password_strength(self, password: str) -> str:
        """Calculate password strength"""
        score = 0
        
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if any(c.isupper() for c in password):
            score += 1
        if any(c.islower() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 1
        
        if score <= 2:
            return "weak"
        elif score <= 4:
            return "medium"
        else:
            return "strong"
    
    def check_account_lockout(self, username: str) -> bool:
        """Check if account is locked out"""
        if username in self.locked_accounts:
            lockout_time = self.locked_accounts[username]
            if time.time() - lockout_time < (self.security_policy.lockout_duration_minutes * 60):
                return True
            else:
                # Lockout expired
                del self.locked_accounts[username]
                if username in self.failed_attempts:
                    del self.failed_attempts[username]
        
        return False
    
    def record_failed_login(self, username: str):
        """Record failed login attempt"""
        current_time = time.time()
        
        if username not in self.failed_attempts:
            self.failed_attempts[username] = []
        
        # Add current attempt
        self.failed_attempts[username].append(current_time)
        
        # Remove attempts older than lockout duration
        cutoff_time = current_time - (self.security_policy.lockout_duration_minutes * 60)
        self.failed_attempts[username] = [
            attempt for attempt in self.failed_attempts[username] 
            if attempt > cutoff_time
        ]
        
        # Check if account should be locked
        if len(self.failed_attempts[username]) >= self.security_policy.max_login_attempts:
            self.locked_accounts[username] = current_time
            logger.warning(f"Account locked due to failed login attempts: {username}")
    
    def clear_failed_attempts(self, username: str):
        """Clear failed login attempts for user"""
        if username in self.failed_attempts:
            del self.failed_attempts[username]
        if username in self.locked_accounts:
            del self.locked_accounts[username]
    
    def create_access_token(self, user_data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = user_data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm="HS256")
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    
    def has_permission(self, user_role: UserRole, permission: Permission) -> bool:
        """Check if user role has specific permission"""
        return permission in self.role_permissions.get(user_role, [])
    
    def get_user_permissions(self, user_role: UserRole) -> List[Permission]:
        """Get all permissions for user role"""
        return self.role_permissions.get(user_role, [])

class MFAManager:
    """Multi-factor authentication manager"""
    
    def __init__(self, config: MFAConfig = None):
        self.config = config or MFAConfig()
        self.user_secrets: Dict[str, str] = {}
        self.backup_codes: Dict[str, List[str]] = {}
        self.used_backup_codes: Dict[str, List[str]] = {}
    
    def setup_totp(self, user_id: str, username: str) -> Dict[str, Any]:
        """Set up TOTP for user"""
        # Generate secret
        secret = pyotp.random_base32()
        self.user_secrets[user_id] = secret
        
        # Generate TOTP URI
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=username,
            issuer_name=self.config.totp_issuer
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Generate backup codes
        backup_codes = self.generate_backup_codes(user_id)
        
        return {
            "secret": secret,
            "qr_code": qr_code_base64,
            "backup_codes": backup_codes,
            "provisioning_uri": provisioning_uri
        }
    
    def verify_totp(self, user_id: str, token: str) -> bool:
        """Verify TOTP token"""
        if user_id not in self.user_secrets:
            return False
        
        secret = self.user_secrets[user_id]
        totp = pyotp.TOTP(secret)
        
        # Allow for time drift (check current and previous/next periods)
        for time_offset in [-1, 0, 1]:
            if totp.verify(token, valid_window=time_offset):
                return True
        
        return False
    
    def generate_backup_codes(self, user_id: str) -> List[str]:
        """Generate backup codes for user"""
        codes = []
        for _ in range(self.config.backup_codes_count):
            code = secrets.token_hex(4).upper()
            codes.append(code)
        
        self.backup_codes[user_id] = codes
        self.used_backup_codes[user_id] = []
        
        return codes
    
    def verify_backup_code(self, user_id: str, code: str) -> bool:
        """Verify backup code"""
        if user_id not in self.backup_codes:
            return False
        
        code = code.upper().strip()
        
        if code in self.backup_codes[user_id] and code not in self.used_backup_codes.get(user_id, []):
            # Mark code as used
            if user_id not in self.used_backup_codes:
                self.used_backup_codes[user_id] = []
            self.used_backup_codes[user_id].append(code)
            
            return True
        
        return False
    
    def get_remaining_backup_codes(self, user_id: str) -> int:
        """Get count of remaining backup codes"""
        if user_id not in self.backup_codes:
            return 0
        
        total_codes = len(self.backup_codes[user_id])
        used_codes = len(self.used_backup_codes.get(user_id, []))
        
        return total_codes - used_codes

class OAuthManager:
    """OAuth provider manager"""
    
    def __init__(self, providers: Dict[str, OAuthProvider] = None):
        self.providers = providers or {}
        self.state_storage: Dict[str, Dict] = {}
    
    def get_authorization_url(self, provider_name: str, redirect_uri: str) -> Dict[str, str]:
        """Get OAuth authorization URL"""
        if provider_name not in self.providers:
            raise ValueError(f"Unknown OAuth provider: {provider_name}")
        
        provider = self.providers[provider_name]
        
        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        self.state_storage[state] = {
            "provider": provider_name,
            "redirect_uri": redirect_uri,
            "timestamp": time.time()
        }
        
        # Build authorization URL
        params = {
            "client_id": provider.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(provider.scopes),
            "state": state,
            "response_type": "code"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        authorization_url = f"{provider.authorization_url}?{query_string}"
        
        return {
            "authorization_url": authorization_url,
            "state": state
        }
    
    async def exchange_code_for_token(self, provider_name: str, code: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        # Verify state parameter
        if state not in self.state_storage:
            raise ValueError("Invalid state parameter")
        
        state_data = self.state_storage[state]
        if state_data["provider"] != provider_name:
            raise ValueError("State parameter mismatch")
        
        # Check state expiration (5 minutes)
        if time.time() - state_data["timestamp"] > 300:
            del self.state_storage[state]
            raise ValueError("State parameter expired")
        
        provider = self.providers[provider_name]
        
        # Exchange code for token
        token_data = {
            "client_id": provider.client_id,
            "client_secret": provider.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": state_data["redirect_uri"]
        }
        
        # This would make an HTTP request to the provider's token endpoint
        # For now, we'll return a mock response
        return {
            "access_token": "mock_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "mock_refresh_token"
        }
    
    async def get_user_info(self, provider_name: str, access_token: str) -> Dict[str, Any]:
        """Get user information from OAuth provider"""
        provider = self.providers[provider_name]
        
        # This would make an HTTP request to the provider's user info endpoint
        # For now, we'll return a mock response
        return {
            "id": "mock_user_id",
            "email": "user@example.com",
            "name": "Mock User",
            "picture": "https://example.com/avatar.jpg",
            "provider": provider_name
        }

# Global instances
security_policy = SecurityPolicy()
advanced_auth = AdvancedAuth("your-secret-key", security_policy)
mfa_manager = MFAManager()
oauth_manager = OAuthManager()

# Setup OAuth providers
def setup_oauth_providers():
    """Set up OAuth providers"""
    # Google OAuth
    google_provider = OAuthProvider(
        name="google",
        client_id="your-google-client-id",
        client_secret="your-google-client-secret",
        authorization_url="https://accounts.google.com/o/oauth2/auth",
        token_url="https://oauth2.googleapis.com/token",
        user_info_url="https://www.googleapis.com/oauth2/v2/userinfo",
        scopes=["openid", "email", "profile"]
    )
    
    # GitHub OAuth
    github_provider = OAuthProvider(
        name="github",
        client_id="your-github-client-id",
        client_secret="your-github-client-secret",
        authorization_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        user_info_url="https://api.github.com/user",
        scopes=["user:email"]
    )
    
    # Microsoft OAuth
    microsoft_provider = OAuthProvider(
        name="microsoft",
        client_id="your-microsoft-client-id",
        client_secret="your-microsoft-client-secret",
        authorization_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        user_info_url="https://graph.microsoft.com/v1.0/me",
        scopes=["openid", "profile", "email"]
    )
    
    advanced_auth.add_oauth_provider(google_provider)
    advanced_auth.add_oauth_provider(github_provider)
    advanced_auth.add_oauth_provider(microsoft_provider)
    
    oauth_manager.providers = advanced_auth.oauth_providers

# Initialize OAuth providers
setup_oauth_providers()

# Convenience functions
def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would check the current user's permissions
            # For now, we'll just log the requirement
            logger.info(f"Permission required: {permission.value}")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(role: UserRole):
    """Decorator to require specific role"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would check the current user's role
            # For now, we'll just log the requirement
            logger.info(f"Role required: {role.value}")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage examples
if __name__ == "__main__":
    # Test password validation
    password_result = advanced_auth.validate_password_policy("TestPassword123!")
    print(f"Password validation: {password_result}")
    
    # Test MFA setup
    mfa_setup = mfa_manager.setup_totp("user123", "testuser@example.com")
    print(f"MFA setup complete: {len(mfa_setup['backup_codes'])} backup codes generated")
    
    # Test OAuth URL generation
    oauth_url = oauth_manager.get_authorization_url("google", "http://localhost:3000/auth/callback")
    print(f"OAuth URL generated: {oauth_url['authorization_url'][:50]}...")