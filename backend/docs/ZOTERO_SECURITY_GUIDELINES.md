# Zotero Integration Security Guidelines

## Overview

This document outlines the security guidelines, best practices, and implementation details for the Zotero integration in AI Scholar. It covers authentication, authorization, data protection, monitoring, and incident response procedures.

## Table of Contents

1. [Authentication Security](#authentication-security)
2. [Authorization and Access Control](#authorization-and-access-control)
3. [Data Protection](#data-protection)
4. [Network Security](#network-security)
5. [Input Validation and Sanitization](#input-validation-and-sanitization)
6. [Rate Limiting and Abuse Prevention](#rate-limiting-and-abuse-prevention)
7. [Logging and Monitoring](#logging-and-monitoring)
8. [Incident Response](#incident-response)
9. [Compliance Requirements](#compliance-requirements)
10. [Security Testing](#security-testing)

## Authentication Security

### OAuth 2.0 Implementation

The Zotero integration uses OAuth 2.0 for secure authentication with the Zotero API.

#### Security Requirements:
- **HTTPS Only**: All OAuth flows must use HTTPS
- **State Parameter**: Always include and validate the `state` parameter to prevent CSRF attacks
- **Token Storage**: Store access tokens and refresh tokens securely using encryption
- **Token Expiration**: Implement proper token expiration and refresh mechanisms
- **Scope Limitation**: Request only the minimum required scopes

#### Implementation:
```python
# Example secure OAuth implementation
class ZoteroOAuthHandler:
    def initiate_oauth(self, user_id: str) -> dict:
        state = secrets.token_urlsafe(32)
        # Store state securely associated with user session
        redis_client.set(f"oauth_state:{user_id}", state, ex=600)
        
        return {
            'authorization_url': f"{ZOTERO_OAUTH_URL}?{params}",
            'state': state
        }
    
    def validate_callback(self, user_id: str, code: str, state: str) -> bool:
        stored_state = redis_client.get(f"oauth_state:{user_id}")
        return hmac.compare_digest(stored_state, state)
```

### Multi-Factor Authentication (MFA)

#### Requirements:
- **Admin Accounts**: MFA is mandatory for all admin accounts
- **High-Risk Operations**: Require MFA for sensitive operations like data export
- **TOTP Support**: Support Time-based One-Time Passwords (TOTP)
- **Backup Codes**: Provide backup recovery codes

### Session Management

#### Security Measures:
- **Session Timeout**: 30-minute idle timeout
- **Secure Cookies**: Use `Secure`, `HttpOnly`, and `SameSite` flags
- **Session Rotation**: Rotate session IDs after authentication
- **Concurrent Session Limits**: Limit concurrent sessions per user

## Authorization and Access Control

### Role-Based Access Control (RBAC)

#### User Roles:
- **User**: Basic Zotero integration access
- **Premium User**: Enhanced features and higher rate limits
- **Admin**: Full system access and monitoring capabilities
- **System**: Internal service accounts

#### Permission Matrix:
| Resource | User | Premium | Admin | System |
|----------|------|---------|-------|--------|
| Own Zotero Data | R/W | R/W | R/W | R/W |
| Others' Data | - | - | R | R/W |
| System Config | - | - | R/W | R/W |
| Analytics | - | Limited | Full | Full |
| Audit Logs | - | - | R | R/W |

### Resource-Level Authorization

#### Implementation:
```python
async def check_resource_access(user_id: str, resource_type: str, resource_id: str, action: str) -> bool:
    # Check if user owns the resource
    if resource_type == "zotero_connection":
        connection = await get_zotero_connection(resource_id)
        return connection.user_id == user_id
    
    # Check admin permissions
    user = await get_user(user_id)
    if user.role == "admin":
        return True
    
    return False
```

## Data Protection

### Encryption

#### Data at Rest:
- **Database Encryption**: Use AES-256 encryption for sensitive fields
- **File Encryption**: Encrypt PDF attachments and other files
- **Key Management**: Use secure key derivation and rotation

#### Data in Transit:
- **TLS 1.3**: Use TLS 1.3 for all communications
- **Certificate Pinning**: Implement certificate pinning for critical connections
- **HSTS**: Enable HTTP Strict Transport Security

#### Implementation:
```python
class DataEncryption:
    def __init__(self):
        self.cipher_suite = Fernet(self._derive_key())
    
    def encrypt_sensitive_data(self, data: str) -> str:
        return base64.b64encode(
            self.cipher_suite.encrypt(data.encode())
        ).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        return self.cipher_suite.decrypt(
            base64.b64decode(encrypted_data)
        ).decode()
```

### Data Minimization

#### Principles:
- **Collect Only Necessary Data**: Only store required Zotero metadata
- **Data Retention**: Implement automatic data purging policies
- **User Control**: Allow users to delete their data
- **Anonymization**: Anonymize data for analytics when possible

### Privacy Protection

#### GDPR Compliance:
- **Consent Management**: Explicit consent for data processing
- **Right to Access**: Users can export their data
- **Right to Deletion**: Users can delete their accounts and data
- **Data Portability**: Provide data in machine-readable formats
- **Privacy by Design**: Build privacy into system architecture

## Network Security

### API Security

#### Rate Limiting:
```python
RATE_LIMITS = {
    '/api/zotero/auth/': {'requests': 10, 'window': 300},
    '/api/zotero/sync/': {'requests': 100, 'window': 3600},
    '/api/zotero/search/': {'requests': 500, 'window': 3600},
    '/api/zotero/citations/': {'requests': 200, 'window': 3600},
    'default': {'requests': 1000, 'window': 3600}
}
```

#### IP Blocking:
- **Automatic Blocking**: Block IPs with suspicious activity
- **Whitelist Support**: Allow trusted IP ranges
- **Geographic Restrictions**: Block requests from high-risk countries (if required)

### CORS Configuration

#### Secure CORS Setup:
```python
CORS_SETTINGS = {
    "allow_origins": ["https://yourdomain.com"],  # Never use "*" in production
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE"],
    "allow_headers": ["Authorization", "Content-Type"],
    "max_age": 86400
}
```

## Input Validation and Sanitization

### Validation Rules

#### Input Sanitization:
```python
class InputValidator:
    SUSPICIOUS_PATTERNS = [
        r"(?i)(union|select|insert|update|delete|drop)\s+",
        r"(?i)<script[^>]*>.*?</script>",
        r"\.\.[\\/]",
        r"(?i)(;|\||\&)\s*(cat|ls|dir|type|echo|ping)"
    ]
    
    def validate_input(self, data: dict) -> tuple[bool, list]:
        violations = []
        
        for key, value in data.items():
            if isinstance(value, str):
                # Check length
                if len(value) > 10000:
                    violations.append(f"Input too long: {key}")
                
                # Check for suspicious patterns
                for pattern in self.SUSPICIOUS_PATTERNS:
                    if re.search(pattern, value):
                        violations.append(f"Suspicious pattern in {key}")
        
        return len(violations) == 0, violations
```

### File Upload Security

#### File Validation:
- **File Type Validation**: Only allow specific file types (.pdf, .txt, .doc, .docx)
- **File Size Limits**: Maximum 100MB per file
- **Virus Scanning**: Scan uploaded files for malware
- **Content Validation**: Validate file headers and content

## Rate Limiting and Abuse Prevention

### Rate Limiting Strategy

#### Sliding Window Implementation:
```python
async def check_rate_limit(client_id: str, endpoint: str) -> tuple[bool, int]:
    key = f"rate_limit:{client_id}:{endpoint}"
    current_time = time.time()
    window_start = current_time - RATE_LIMIT_WINDOW
    
    # Remove old entries
    await redis_client.zremrangebyscore(key, 0, window_start)
    
    # Check current count
    current_requests = await redis_client.zcard(key)
    
    if current_requests >= MAX_REQUESTS:
        return False, 0
    
    # Add current request
    await redis_client.zadd(key, {str(current_time): current_time})
    
    return True, MAX_REQUESTS - current_requests - 1
```

### Abuse Detection

#### Suspicious Activity Patterns:
- **Rapid Authentication Attempts**: Multiple failed logins
- **Unusual Access Patterns**: Access from multiple IPs simultaneously
- **Data Scraping**: High-volume data requests
- **API Abuse**: Excessive API calls or unusual endpoints

## Logging and Monitoring

### Security Event Logging

#### Event Types:
```python
class SecurityEventType(Enum):
    AUTHENTICATION_SUCCESS = "auth_success"
    AUTHENTICATION_FAILURE = "auth_failure"
    AUTHORIZATION_FAILURE = "authz_failure"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    DATA_ACCESS = "data_access"
    SECURITY_VIOLATION = "security_violation"
```

#### Log Format:
```json
{
    "timestamp": "2023-12-07T10:30:00Z",
    "event_id": "sec_evt_123456",
    "event_type": "authentication_failure",
    "threat_level": "medium",
    "user_id": "user_123",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "resource": "/api/zotero/auth/login",
    "action": "login_attempt",
    "details": {
        "reason": "invalid_credentials",
        "attempt_count": 3
    }
}
```

### Monitoring and Alerting

#### Alert Conditions:
- **Critical**: Multiple authentication failures, security violations
- **High**: Rate limit exceeded, suspicious activity
- **Medium**: Authorization failures, unusual access patterns
- **Low**: Normal security events for audit trail

#### Monitoring Metrics:
- Authentication success/failure rates
- API response times and error rates
- Rate limiting effectiveness
- Security event frequency
- System resource usage

## Incident Response

### Incident Classification

#### Severity Levels:
- **P0 (Critical)**: Active security breach, data compromise
- **P1 (High)**: Potential security breach, system compromise
- **P2 (Medium)**: Security policy violation, suspicious activity
- **P3 (Low)**: Minor security events, policy compliance issues

### Response Procedures

#### Immediate Response (P0/P1):
1. **Isolate**: Block suspicious IPs, disable compromised accounts
2. **Assess**: Determine scope and impact of incident
3. **Contain**: Prevent further damage or data loss
4. **Notify**: Alert security team and stakeholders
5. **Document**: Record all actions and findings

#### Investigation Process:
1. **Evidence Collection**: Gather logs, system snapshots
2. **Timeline Reconstruction**: Map sequence of events
3. **Impact Assessment**: Determine data/system compromise
4. **Root Cause Analysis**: Identify vulnerability or attack vector
5. **Remediation**: Fix vulnerabilities, improve security

### Communication Plan

#### Internal Communication:
- **Security Team**: Immediate notification for P0/P1 incidents
- **Development Team**: For technical remediation
- **Management**: For business impact assessment
- **Legal/Compliance**: For regulatory requirements

#### External Communication:
- **Users**: Notification of security incidents affecting them
- **Regulators**: As required by law (GDPR, etc.)
- **Partners**: If third-party systems are affected

## Compliance Requirements

### GDPR Compliance

#### Data Processing:
- **Lawful Basis**: Consent or legitimate interest
- **Data Minimization**: Only collect necessary data
- **Purpose Limitation**: Use data only for stated purposes
- **Storage Limitation**: Delete data when no longer needed

#### User Rights:
- **Right to Access**: Provide user data on request
- **Right to Rectification**: Allow data correction
- **Right to Erasure**: Delete user data on request
- **Right to Portability**: Export data in machine-readable format

### OAuth 2.0 Compliance

#### Security Requirements:
- **Authorization Code Flow**: Use most secure OAuth flow
- **PKCE**: Implement Proof Key for Code Exchange
- **State Parameter**: Prevent CSRF attacks
- **Scope Limitation**: Request minimal required permissions

### API Security Standards

#### OWASP API Security Top 10:
1. **Broken Object Level Authorization**: Implement proper access controls
2. **Broken User Authentication**: Secure authentication mechanisms
3. **Excessive Data Exposure**: Return only necessary data
4. **Lack of Resources & Rate Limiting**: Implement rate limiting
5. **Broken Function Level Authorization**: Validate function access
6. **Mass Assignment**: Validate input parameters
7. **Security Misconfiguration**: Secure default configurations
8. **Injection**: Validate and sanitize all inputs
9. **Improper Assets Management**: Maintain API inventory
10. **Insufficient Logging & Monitoring**: Comprehensive logging

## Security Testing

### Automated Security Testing

#### Static Analysis:
```bash
# Security linting
bandit -r backend/services/zotero/
semgrep --config=security backend/

# Dependency scanning
safety check
pip-audit
```

#### Dynamic Analysis:
```bash
# API security testing
zap-baseline.py -t http://localhost:8000/api/zotero/
nuclei -u http://localhost:8000 -t security/

# Load testing with security focus
locust -f security_load_test.py --host=http://localhost:8000
```

### Manual Security Testing

#### Penetration Testing Checklist:
- [ ] Authentication bypass attempts
- [ ] Authorization escalation tests
- [ ] Input validation testing (SQL injection, XSS, etc.)
- [ ] Session management testing
- [ ] Rate limiting effectiveness
- [ ] Error handling security
- [ ] File upload security
- [ ] API endpoint security

#### Security Code Review:
- [ ] Authentication implementation
- [ ] Authorization checks
- [ ] Input validation
- [ ] Cryptographic implementations
- [ ] Error handling
- [ ] Logging and monitoring
- [ ] Configuration security

### Vulnerability Management

#### Vulnerability Scanning:
- **Automated Scans**: Weekly vulnerability scans
- **Dependency Checks**: Daily dependency vulnerability checks
- **Code Analysis**: Security code analysis on every commit
- **Infrastructure Scans**: Monthly infrastructure security scans

#### Patch Management:
- **Critical Vulnerabilities**: Patch within 24 hours
- **High Vulnerabilities**: Patch within 7 days
- **Medium Vulnerabilities**: Patch within 30 days
- **Low Vulnerabilities**: Patch in next release cycle

## Security Configuration

### Environment Variables

#### Required Security Settings:
```bash
# Encryption
ZOTERO_ENCRYPTION_KEY=<base64-encoded-key>
SECRET_KEY=<cryptographically-secure-key>

# Database
DATABASE_SSL_MODE=require
DATABASE_SSL_CERT=/path/to/cert.pem

# Redis
REDIS_SSL=true
REDIS_PASSWORD=<secure-password>

# OAuth
ZOTERO_CLIENT_SECRET=<secure-secret>
OAUTH_STATE_SECRET=<secure-secret>

# Security
SECURITY_HEADERS_ENABLED=true
RATE_LIMITING_ENABLED=true
IP_BLOCKING_ENABLED=true
```

### Security Headers

#### Required Headers:
```python
SECURITY_HEADERS = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Content-Security-Policy': "default-src 'self'; script-src 'self'",
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
}
```

## Conclusion

This security guidelines document provides comprehensive security measures for the Zotero integration. Regular review and updates of these guidelines are essential to maintain security posture as threats evolve.

### Key Takeaways:
1. **Defense in Depth**: Multiple layers of security controls
2. **Principle of Least Privilege**: Minimal required permissions
3. **Security by Design**: Built-in security from the start
4. **Continuous Monitoring**: Real-time threat detection
5. **Incident Preparedness**: Ready response procedures

### Regular Security Tasks:
- [ ] Monthly security reviews
- [ ] Quarterly penetration testing
- [ ] Annual security audits
- [ ] Continuous vulnerability monitoring
- [ ] Regular security training for development team

For questions or security concerns, contact the security team at security@yourcompany.com.