"""
Security service for Zotero integration with audit and hardening features.
"""
import asyncio
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import re
import ipaddress
from collections import defaultdict, deque

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

from core.redis_client import get_redis_client
from core.database import get_db
from models.zotero_models import ZoteroConnection, ZoteroSecurityLog


class SecurityEventType(Enum):
    """Types of security events."""
    AUTHENTICATION_SUCCESS = "auth_success"
    AUTHENTICATION_FAILURE = "auth_failure"
    AUTHORIZATION_FAILURE = "authz_failure"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    DATA_ACCESS = "data_access"
    CONFIGURATION_CHANGE = "config_change"
    SECURITY_VIOLATION = "security_violation"


class ThreatLevel(Enum):
    """Threat levels for security events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Represents a security event."""
    event_id: str
    event_type: SecurityEventType
    threat_level: ThreatLevel
    user_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource: str
    action: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False


@dataclass
class SecurityAuditResult:
    """Results of a security audit."""
    audit_id: str
    audit_timestamp: datetime
    overall_score: float
    vulnerabilities: List[Dict[str, Any]]
    recommendations: List[str]
    compliance_status: Dict[str, bool]
    risk_assessment: Dict[str, Any]


class ZoteroSecurityService:
    """Security service for Zotero integration."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.security_events = deque(maxlen=10000)
        self.rate_limiters = defaultdict(lambda: defaultdict(deque))
        self.blocked_ips = set()
        self.suspicious_patterns = []
        
        # Initialize encryption
        self._init_encryption()
        
        # Security configuration
        self.config = {
            'max_login_attempts': 5,
            'lockout_duration': 900,  # 15 minutes
            'rate_limit_window': 3600,  # 1 hour
            'max_requests_per_hour': 1000,
            'token_expiry': 3600,  # 1 hour
            'session_timeout': 1800,  # 30 minutes
            'password_min_length': 12,
            'require_mfa': False,
            'allowed_origins': ['*'],  # Configure for production
            'max_file_size': 100 * 1024 * 1024,  # 100MB
            'allowed_file_types': ['.pdf', '.txt', '.doc', '.docx'],
        }
        
        # Initialize suspicious patterns
        self._init_suspicious_patterns()
    
    def _init_encryption(self):
        """Initialize encryption components."""
        try:
            # Get or generate encryption key
            key = os.getenv('ZOTERO_ENCRYPTION_KEY')
            if not key:
                # Generate new key (in production, this should be stored securely)
                key = Fernet.generate_key()
                self.logger.warning("Generated new encryption key - store securely!")
            
            if isinstance(key, str):
                key = key.encode()
            
            self.cipher_suite = Fernet(key)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {str(e)}")
            # Fallback to basic encryption
            self.cipher_suite = None
    
    def _init_suspicious_patterns(self):
        """Initialize patterns for detecting suspicious activity."""
        self.suspicious_patterns = [
            # SQL injection patterns
            r"(?i)(union|select|insert|update|delete|drop|create|alter)\s+",
            r"(?i)(or|and)\s+\d+\s*=\s*\d+",
            r"(?i)'.*?'.*?(or|and).*?'.*?'",
            
            # XSS patterns
            r"(?i)<script[^>]*>.*?</script>",
            r"(?i)javascript:",
            r"(?i)on\w+\s*=",
            
            # Path traversal
            r"\.\.[\\/]",
            r"(?i)etc[\\/]passwd",
            r"(?i)windows[\\/]system32",
            
            # Command injection
            r"(?i)(;|\||\&)\s*(cat|ls|dir|type|echo|ping)",
            r"(?i)\$\(.*?\)",
            r"(?i)`.*?`",
        ]
    
    async def log_security_event(
        self,
        event_type: SecurityEventType,
        threat_level: ThreatLevel,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource: str = "",
        action: str = "",
        details: Dict[str, Any] = None
    ) -> str:
        """Log a security event."""
        try:
            event_id = secrets.token_hex(16)
            
            security_event = SecurityEvent(
                event_id=event_id,
                event_type=event_type,
                threat_level=threat_level,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                resource=resource,
                action=action,
                details=details or {},
                timestamp=datetime.utcnow()
            )
            
            # Add to buffer
            self.security_events.append(security_event)
            
            # Store in Redis for real-time monitoring
            await self._store_security_event(security_event)
            
            # Check for immediate threats
            if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                await self._handle_high_threat_event(security_event)
            
            # Flush buffer if getting full
            if len(self.security_events) >= 1000:
                await self._flush_security_events()
            
            self.logger.warning(
                f"Security event: {event_type.value} - {threat_level.value}",
                extra={
                    'event_id': event_id,
                    'user_id': user_id,
                    'ip_address': ip_address,
                    'resource': resource,
                    'action': action
                }
            )
            
            return event_id
            
        except Exception as e:
            self.logger.error(f"Failed to log security event: {str(e)}")
            return ""
    
    async def _store_security_event(self, event: SecurityEvent) -> None:
        """Store security event in Redis."""
        try:
            redis_client = await get_redis_client()
            if not redis_client:
                return
            
            # Store in hourly buckets
            hour_key = f"zotero:security:{event.timestamp.strftime('%Y%m%d%H')}"
            event_data = {
                'event_id': event.event_id,
                'event_type': event.event_type.value,
                'threat_level': event.threat_level.value,
                'user_id': event.user_id,
                'ip_address': event.ip_address,
                'user_agent': event.user_agent,
                'resource': event.resource,
                'action': event.action,
                'details': event.details,
                'timestamp': event.timestamp.isoformat(),
                'resolved': event.resolved
            }
            
            await redis_client.lpush(hour_key, str(event_data))
            await redis_client.expire(hour_key, 86400 * 30)  # Keep for 30 days
            
            # Store by threat level
            threat_key = f"zotero:security:threat:{event.threat_level.value}"
            await redis_client.lpush(threat_key, str(event_data))
            await redis_client.expire(threat_key, 86400 * 7)  # Keep for 7 days
            
        except Exception as e:
            self.logger.warning(f"Failed to store security event: {str(e)}")
    
    async def _handle_high_threat_event(self, event: SecurityEvent) -> None:
        """Handle high threat security events."""
        try:
            # Block IP for critical threats
            if event.threat_level == ThreatLevel.CRITICAL and event.ip_address:
                await self.block_ip(event.ip_address, duration=timedelta(hours=24))
            
            # Disable user account for repeated failures
            if (event.event_type == SecurityEventType.AUTHENTICATION_FAILURE and 
                event.user_id):
                await self._check_user_lockout(event.user_id, event.ip_address)
            
            # Send alerts (would integrate with alerting system)
            await self._send_security_alert(event)
            
        except Exception as e:
            self.logger.error(f"Failed to handle high threat event: {str(e)}")
    
    async def _check_user_lockout(self, user_id: str, ip_address: Optional[str]) -> None:
        """Check if user should be locked out due to failed attempts."""
        try:
            redis_client = await get_redis_client()
            if not redis_client:
                return
            
            # Count recent failed attempts
            key = f"zotero:auth_failures:{user_id}"
            failures = await redis_client.incr(key)
            await redis_client.expire(key, self.config['lockout_duration'])
            
            if failures >= self.config['max_login_attempts']:
                # Lock user account
                lockout_key = f"zotero:lockout:{user_id}"
                await redis_client.set(lockout_key, "locked", ex=self.config['lockout_duration'])
                
                # Log lockout event
                await self.log_security_event(
                    SecurityEventType.SECURITY_VIOLATION,
                    ThreatLevel.HIGH,
                    user_id=user_id,
                    ip_address=ip_address,
                    action="account_lockout",
                    details={'failed_attempts': failures}
                )
                
        except Exception as e:
            self.logger.error(f"Failed to check user lockout: {str(e)}")
    
    async def _send_security_alert(self, event: SecurityEvent) -> None:
        """Send security alert (placeholder for integration with alerting system)."""
        # In a real implementation, this would integrate with:
        # - Email notifications
        # - Slack/Teams alerts
        # - SIEM systems
        # - Security monitoring dashboards
        pass
    
    async def _flush_security_events(self) -> None:
        """Flush security events to database."""
        if not self.security_events:
            return
        
        try:
            db = next(get_db())
            
            events_to_save = []
            while self.security_events:
                event = self.security_events.popleft()
                
                security_log = ZoteroSecurityLog(
                    event_id=event.event_id,
                    event_type=event.event_type.value,
                    threat_level=event.threat_level.value,
                    user_id=event.user_id,
                    ip_address=event.ip_address,
                    user_agent=event.user_agent,
                    resource=event.resource,
                    action=event.action,
                    details=event.details,
                    timestamp=event.timestamp,
                    resolved=event.resolved
                )
                
                events_to_save.append(security_log)
            
            if events_to_save:
                db.add_all(events_to_save)
                db.commit()
                
                self.logger.info(f"Flushed {len(events_to_save)} security events to database")
            
        except Exception as e:
            self.logger.error(f"Failed to flush security events: {str(e)}")
    
    async def check_rate_limit(
        self,
        user_id: str,
        ip_address: str,
        endpoint: str
    ) -> Tuple[bool, int]:
        """Check if request should be rate limited."""
        try:
            current_time = time.time()
            window_start = current_time - self.config['rate_limit_window']
            
            # Clean old entries
            user_requests = self.rate_limiters[user_id][endpoint]
            while user_requests and user_requests[0] < window_start:
                user_requests.popleft()
            
            ip_requests = self.rate_limiters[ip_address][endpoint]
            while ip_requests and ip_requests[0] < window_start:
                ip_requests.popleft()
            
            # Check limits
            user_count = len(user_requests)
            ip_count = len(ip_requests)
            
            max_requests = self.config['max_requests_per_hour']
            
            if user_count >= max_requests or ip_count >= max_requests:
                # Log rate limit event
                await self.log_security_event(
                    SecurityEventType.RATE_LIMIT_EXCEEDED,
                    ThreatLevel.MEDIUM,
                    user_id=user_id,
                    ip_address=ip_address,
                    resource=endpoint,
                    action="rate_limit",
                    details={
                        'user_requests': user_count,
                        'ip_requests': ip_count,
                        'limit': max_requests
                    }
                )
                
                return False, max_requests - max(user_count, ip_count)
            
            # Add current request
            user_requests.append(current_time)
            ip_requests.append(current_time)
            
            return True, max_requests - max(user_count + 1, ip_count + 1)
            
        except Exception as e:
            self.logger.error(f"Failed to check rate limit: {str(e)}")
            return True, 0
    
    async def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked."""
        try:
            if ip_address in self.blocked_ips:
                return True
            
            redis_client = await get_redis_client()
            if redis_client:
                blocked = await redis_client.get(f"zotero:blocked_ip:{ip_address}")
                return blocked is not None
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check IP block status: {str(e)}")
            return False
    
    async def block_ip(self, ip_address: str, duration: timedelta) -> None:
        """Block an IP address."""
        try:
            self.blocked_ips.add(ip_address)
            
            redis_client = await get_redis_client()
            if redis_client:
                await redis_client.set(
                    f"zotero:blocked_ip:{ip_address}",
                    "blocked",
                    ex=int(duration.total_seconds())
                )
            
            await self.log_security_event(
                SecurityEventType.SECURITY_VIOLATION,
                ThreatLevel.HIGH,
                ip_address=ip_address,
                action="ip_blocked",
                details={'duration_seconds': duration.total_seconds()}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to block IP: {str(e)}")
    
    async def is_user_locked_out(self, user_id: str) -> bool:
        """Check if user is locked out."""
        try:
            redis_client = await get_redis_client()
            if redis_client:
                locked = await redis_client.get(f"zotero:lockout:{user_id}")
                return locked is not None
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check user lockout: {str(e)}")
            return False
    
    def detect_suspicious_input(self, input_text: str) -> List[str]:
        """Detect suspicious patterns in input."""
        detected_patterns = []
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, input_text):
                detected_patterns.append(pattern)
        
        return detected_patterns
    
    async def validate_input_security(
        self,
        input_data: Dict[str, Any],
        user_id: str,
        ip_address: str
    ) -> Tuple[bool, List[str]]:
        """Validate input for security threats."""
        try:
            violations = []
            
            for key, value in input_data.items():
                if isinstance(value, str):
                    # Check for suspicious patterns
                    suspicious = self.detect_suspicious_input(value)
                    if suspicious:
                        violations.extend([f"Suspicious pattern in {key}: {p}" for p in suspicious])
                    
                    # Check length limits
                    if len(value) > 10000:  # 10KB limit
                        violations.append(f"Input too long in {key}: {len(value)} characters")
                
                elif isinstance(value, (int, float)):
                    # Check numeric limits
                    if abs(value) > 1e10:
                        violations.append(f"Numeric value too large in {key}: {value}")
            
            if violations:
                await self.log_security_event(
                    SecurityEventType.SECURITY_VIOLATION,
                    ThreatLevel.MEDIUM,
                    user_id=user_id,
                    ip_address=ip_address,
                    action="input_validation_failed",
                    details={'violations': violations, 'input_keys': list(input_data.keys())}
                )
                
                return False, violations
            
            return True, []
            
        except Exception as e:
            self.logger.error(f"Failed to validate input security: {str(e)}")
            return True, []
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        try:
            if self.cipher_suite:
                encrypted = self.cipher_suite.encrypt(data.encode())
                return base64.b64encode(encrypted).decode()
            else:
                # Fallback to basic encoding (not secure!)
                return base64.b64encode(data.encode()).decode()
                
        except Exception as e:
            self.logger.error(f"Failed to encrypt data: {str(e)}")
            return data
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        try:
            if self.cipher_suite:
                encrypted_bytes = base64.b64decode(encrypted_data.encode())
                decrypted = self.cipher_suite.decrypt(encrypted_bytes)
                return decrypted.decode()
            else:
                # Fallback to basic decoding
                return base64.b64decode(encrypted_data.encode()).decode()
                
        except Exception as e:
            self.logger.error(f"Failed to decrypt data: {str(e)}")
            return encrypted_data
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure token."""
        return secrets.token_urlsafe(length)
    
    def verify_hmac_signature(
        self,
        data: str,
        signature: str,
        secret: str
    ) -> bool:
        """Verify HMAC signature."""
        try:
            expected_signature = hmac.new(
                secret.encode(),
                data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            self.logger.error(f"Failed to verify HMAC signature: {str(e)}")
            return False
    
    async def perform_security_audit(self) -> SecurityAuditResult:
        """Perform comprehensive security audit."""
        try:
            audit_id = secrets.token_hex(16)
            vulnerabilities = []
            recommendations = []
            compliance_status = {}
            
            # Check authentication security
            auth_score = await self._audit_authentication()
            if auth_score < 0.8:
                vulnerabilities.append({
                    'category': 'authentication',
                    'severity': 'high',
                    'description': 'Weak authentication configuration',
                    'score': auth_score
                })
                recommendations.append('Strengthen authentication requirements')
            
            # Check authorization security
            authz_score = await self._audit_authorization()
            if authz_score < 0.8:
                vulnerabilities.append({
                    'category': 'authorization',
                    'severity': 'medium',
                    'description': 'Authorization controls need improvement',
                    'score': authz_score
                })
                recommendations.append('Review and strengthen authorization controls')
            
            # Check data protection
            data_score = await self._audit_data_protection()
            if data_score < 0.8:
                vulnerabilities.append({
                    'category': 'data_protection',
                    'severity': 'high',
                    'description': 'Data protection measures insufficient',
                    'score': data_score
                })
                recommendations.append('Implement stronger data protection measures')
            
            # Check network security
            network_score = await self._audit_network_security()
            if network_score < 0.8:
                vulnerabilities.append({
                    'category': 'network',
                    'severity': 'medium',
                    'description': 'Network security configuration needs review',
                    'score': network_score
                })
                recommendations.append('Review network security configuration')
            
            # Check logging and monitoring
            logging_score = await self._audit_logging_monitoring()
            if logging_score < 0.8:
                vulnerabilities.append({
                    'category': 'logging',
                    'severity': 'low',
                    'description': 'Logging and monitoring can be improved',
                    'score': logging_score
                })
                recommendations.append('Enhance logging and monitoring capabilities')
            
            # Calculate overall score
            scores = [auth_score, authz_score, data_score, network_score, logging_score]
            overall_score = sum(scores) / len(scores)
            
            # Compliance checks
            compliance_status = {
                'gdpr_compliant': data_score > 0.8,
                'oauth2_compliant': auth_score > 0.7,
                'rate_limiting_enabled': True,
                'encryption_enabled': self.cipher_suite is not None,
                'audit_logging_enabled': logging_score > 0.7
            }
            
            # Risk assessment
            risk_assessment = {
                'overall_risk': 'low' if overall_score > 0.8 else 'medium' if overall_score > 0.6 else 'high',
                'critical_vulnerabilities': len([v for v in vulnerabilities if v['severity'] == 'high']),
                'compliance_gaps': len([k for k, v in compliance_status.items() if not v]),
                'recommended_actions': len(recommendations)
            }
            
            return SecurityAuditResult(
                audit_id=audit_id,
                audit_timestamp=datetime.utcnow(),
                overall_score=overall_score,
                vulnerabilities=vulnerabilities,
                recommendations=recommendations,
                compliance_status=compliance_status,
                risk_assessment=risk_assessment
            )
            
        except Exception as e:
            self.logger.error(f"Failed to perform security audit: {str(e)}")
            return SecurityAuditResult(
                audit_id="error",
                audit_timestamp=datetime.utcnow(),
                overall_score=0.0,
                vulnerabilities=[],
                recommendations=[],
                compliance_status={},
                risk_assessment={}
            )
    
    async def _audit_authentication(self) -> float:
        """Audit authentication security."""
        score = 1.0
        
        # Check password requirements
        if self.config['password_min_length'] < 12:
            score -= 0.2
        
        # Check MFA requirement
        if not self.config['require_mfa']:
            score -= 0.3
        
        # Check lockout configuration
        if self.config['max_login_attempts'] > 5:
            score -= 0.1
        
        # Check token expiry
        if self.config['token_expiry'] > 3600:
            score -= 0.1
        
        return max(0.0, score)
    
    async def _audit_authorization(self) -> float:
        """Audit authorization security."""
        score = 1.0
        
        # Check session timeout
        if self.config['session_timeout'] > 1800:
            score -= 0.2
        
        # Check CORS configuration
        if '*' in self.config['allowed_origins']:
            score -= 0.3
        
        return max(0.0, score)
    
    async def _audit_data_protection(self) -> float:
        """Audit data protection measures."""
        score = 1.0
        
        # Check encryption
        if not self.cipher_suite:
            score -= 0.4
        
        # Check file upload limits
        if self.config['max_file_size'] > 100 * 1024 * 1024:
            score -= 0.1
        
        # Check allowed file types
        if not self.config['allowed_file_types']:
            score -= 0.2
        
        return max(0.0, score)
    
    async def _audit_network_security(self) -> float:
        """Audit network security configuration."""
        score = 1.0
        
        # Check rate limiting
        if self.config['max_requests_per_hour'] > 1000:
            score -= 0.2
        
        # Check IP blocking capability
        if not hasattr(self, 'blocked_ips'):
            score -= 0.3
        
        return max(0.0, score)
    
    async def _audit_logging_monitoring(self) -> float:
        """Audit logging and monitoring capabilities."""
        score = 1.0
        
        # Check security event logging
        if not hasattr(self, 'security_events'):
            score -= 0.4
        
        # Check event buffer size
        if len(self.security_events) == 0:
            score -= 0.2
        
        return max(0.0, score)


# Global security service instance
security_service = ZoteroSecurityService()