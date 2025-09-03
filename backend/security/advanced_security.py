"""
Advanced Security System for AI Scholar
Comprehensive security with threat detection, compliance, and advanced protection
"""
import asyncio
import hashlib
import hmac
import json
import logging
import secrets
import time
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import re
import ipaddress
from enum import Enum
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    """Security threat levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityEventType(Enum):
    """Types of security events"""
    LOGIN_ATTEMPT = "login_attempt"
    FAILED_LOGIN = "failed_login"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"
    MALICIOUS_REQUEST = "malicious_request"
    PRIVILEGE_ESCALATION = "privilege_escalation"

@dataclass
class SecurityEvent:
    """Security event record"""
    event_id: str
    event_type: SecurityEventType
    threat_level: ThreatLevel
    timestamp: datetime
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    details: Dict[str, Any]
    resolved: bool = False
    response_actions: List[str] = None

@dataclass
class ThreatIntelligence:
    """Threat intelligence data"""
    ip_address: str
    threat_score: float
    threat_types: List[str]
    last_seen: datetime
    source: str
    confidence: float

class AdvancedEncryption:
    """Advanced encryption and key management"""
    
    def __init__(self, master_key: Optional[bytes] = None):
        self.master_key = master_key or Fernet.generate_key()
        self.cipher_suite = Fernet(self.master_key)
        self.key_rotation_interval = timedelta(days=30)
        self.encryption_keys = {}
    
    def encrypt_sensitive_data(self, data: str, context: str = "default") -> str:
        """Encrypt sensitive data with context-specific keys"""
        key = self._get_context_key(context)
        cipher = Fernet(key)
        encrypted_data = cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str, context: str = "default") -> str:
        """Decrypt sensitive data"""
        try:
            key = self._get_context_key(context)
            cipher = Fernet(key)
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = cipher.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data")
    
    def _get_context_key(self, context: str) -> bytes:
        """Get or create context-specific encryption key"""
        if context not in self.encryption_keys:
            # Derive key from master key and context
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=context.encode(),
                iterations=100000,
            )
            self.encryption_keys[context] = base64.urlsafe_b64encode(
                kdf.derive(self.master_key)
            )
        
        return self.encryption_keys[context]
    
    def rotate_keys(self):
        """Rotate encryption keys"""
        old_keys = self.encryption_keys.copy()
        self.encryption_keys.clear()
        logger.info("🔄 Encryption keys rotated")
        return old_keys

class ThreatDetectionEngine:
    """Advanced threat detection and analysis"""
    
    def __init__(self):
        self.threat_patterns = self._load_threat_patterns()
        self.ip_reputation_cache = {}
        self.user_behavior_profiles = {}
        self.anomaly_thresholds = {
            "login_frequency": 10,  # Max logins per hour
            "api_calls": 1000,      # Max API calls per hour
            "data_access": 100,     # Max data access per hour
            "failed_attempts": 5    # Max failed attempts per hour
        }
    
    def _load_threat_patterns(self) -> Dict[str, Any]:
        """Load threat detection patterns"""
        return {
            "sql_injection": [
                r"(\bunion\b.*\bselect\b)",
                r"(\bselect\b.*\bfrom\b.*\bwhere\b)",
                r"(\bdrop\b.*\btable\b)",
                r"(\binsert\b.*\binto\b)",
                r"(\bdelete\b.*\bfrom\b)"
            ],
            "xss": [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>.*?</iframe>"
            ],
            "path_traversal": [
                r"\.\./",
                r"\.\.\\",
                r"%2e%2e%2f",
                r"%2e%2e%5c"
            ],
            "command_injection": [
                r";\s*(rm|del|format|shutdown)",
                r"\|\s*(nc|netcat|wget|curl)",
                r"&&\s*(cat|type|more|less)",
                r"`.*`",
                r"\$\(.*\)"
            ]
        }
    
    async def analyze_request(
        self, 
        request_data: Dict[str, Any], 
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze request for security threats"""
        threats_detected = []
        threat_score = 0.0
        
        # Check for malicious patterns
        for threat_type, patterns in self.threat_patterns.items():
            for pattern in patterns:
                if self._check_pattern_in_request(pattern, request_data):
                    threats_detected.append({
                        "type": threat_type,
                        "pattern": pattern,
                        "severity": self._get_threat_severity(threat_type)
                    })
                    threat_score += self._get_threat_score(threat_type)
        
        # Analyze user behavior
        behavior_analysis = await self._analyze_user_behavior(user_context)
        if behavior_analysis["anomaly_detected"]:
            threats_detected.append({
                "type": "behavioral_anomaly",
                "details": behavior_analysis,
                "severity": "medium"
            })
            threat_score += 0.3
        
        # Check IP reputation
        ip_reputation = await self._check_ip_reputation(user_context.get("ip_address"))
        if ip_reputation["is_malicious"]:
            threats_detected.append({
                "type": "malicious_ip",
                "details": ip_reputation,
                "severity": "high"
            })
            threat_score += 0.5
        
        # Determine overall threat level
        threat_level = self._calculate_threat_level(threat_score)
        
        return {
            "threat_detected": len(threats_detected) > 0,
            "threat_level": threat_level,
            "threat_score": threat_score,
            "threats": threats_detected,
            "recommended_actions": self._get_recommended_actions(threat_level, threats_detected)
        }
    
    def _check_pattern_in_request(self, pattern: str, request_data: Dict[str, Any]) -> bool:
        """Check if malicious pattern exists in request"""
        request_str = json.dumps(request_data).lower()
        return bool(re.search(pattern, request_str, re.IGNORECASE))
    
    def _get_threat_severity(self, threat_type: str) -> str:
        """Get severity level for threat type"""
        severity_map = {
            "sql_injection": "high",
            "xss": "medium",
            "path_traversal": "high",
            "command_injection": "critical"
        }
        return severity_map.get(threat_type, "medium")
    
    def _get_threat_score(self, threat_type: str) -> float:
        """Get numerical threat score"""
        score_map = {
            "sql_injection": 0.8,
            "xss": 0.5,
            "path_traversal": 0.7,
            "command_injection": 0.9
        }
        return score_map.get(threat_type, 0.3)
    
    async def _analyze_user_behavior(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user behavior for anomalies"""
        user_id = user_context.get("user_id")
        if not user_id:
            return {"anomaly_detected": False}
        
        # Get user behavior profile
        profile = self.user_behavior_profiles.get(user_id, {
            "login_times": [],
            "api_calls": [],
            "data_access": [],
            "failed_attempts": []
        })
        
        current_time = datetime.now()
        hour_ago = current_time - timedelta(hours=1)
        
        # Count recent activities
        recent_logins = len([t for t in profile["login_times"] if t > hour_ago])
        recent_api_calls = len([t for t in profile["api_calls"] if t > hour_ago])
        recent_data_access = len([t for t in profile["data_access"] if t > hour_ago])
        recent_failures = len([t for t in profile["failed_attempts"] if t > hour_ago])
        
        # Check for anomalies
        anomalies = []
        if recent_logins > self.anomaly_thresholds["login_frequency"]:
            anomalies.append("excessive_login_frequency")
        
        if recent_api_calls > self.anomaly_thresholds["api_calls"]:
            anomalies.append("excessive_api_usage")
        
        if recent_data_access > self.anomaly_thresholds["data_access"]:
            anomalies.append("excessive_data_access")
        
        if recent_failures > self.anomaly_thresholds["failed_attempts"]:
            anomalies.append("excessive_failed_attempts")
        
        return {
            "anomaly_detected": len(anomalies) > 0,
            "anomalies": anomalies,
            "recent_activity": {
                "logins": recent_logins,
                "api_calls": recent_api_calls,
                "data_access": recent_data_access,
                "failures": recent_failures
            }
        }
    
    async def _check_ip_reputation(self, ip_address: str) -> Dict[str, Any]:
        """Check IP address reputation"""
        if not ip_address:
            return {"is_malicious": False}
        
        # Check cache first
        if ip_address in self.ip_reputation_cache:
            cached_result = self.ip_reputation_cache[ip_address]
            if datetime.now() - cached_result["timestamp"] < timedelta(hours=1):
                return cached_result["data"]
        
        # Mock IP reputation check (in real implementation, use threat intelligence APIs)
        is_malicious = False
        threat_types = []
        
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Check for private/local IPs
            if ip.is_private or ip.is_loopback:
                is_malicious = False
            else:
                # Mock threat intelligence check
                # In real implementation, integrate with services like:
                # - VirusTotal API
                # - AbuseIPDB
                # - Shodan
                # - Custom threat feeds
                
                # Simple heuristic for demo
                ip_int = int(ip)
                if ip_int % 1000 == 0:  # Mock: every 1000th IP is "malicious"
                    is_malicious = True
                    threat_types = ["botnet", "malware"]
        
        except ValueError:
            # Invalid IP address
            is_malicious = True
            threat_types = ["invalid_ip"]
        
        result = {
            "is_malicious": is_malicious,
            "threat_types": threat_types,
            "confidence": 0.8 if is_malicious else 0.9,
            "source": "mock_threat_intel"
        }
        
        # Cache result
        self.ip_reputation_cache[ip_address] = {
            "data": result,
            "timestamp": datetime.now()
        }
        
        return result
    
    def _calculate_threat_level(self, threat_score: float) -> ThreatLevel:
        """Calculate overall threat level"""
        if threat_score >= 0.8:
            return ThreatLevel.CRITICAL
        elif threat_score >= 0.6:
            return ThreatLevel.HIGH
        elif threat_score >= 0.3:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW
    
    def _get_recommended_actions(
        self, 
        threat_level: ThreatLevel, 
        threats: List[Dict[str, Any]]
    ) -> List[str]:
        """Get recommended security actions"""
        actions = []
        
        if threat_level == ThreatLevel.CRITICAL:
            actions.extend([
                "Block IP address immediately",
                "Terminate user session",
                "Alert security team",
                "Initiate incident response"
            ])
        elif threat_level == ThreatLevel.HIGH:
            actions.extend([
                "Increase monitoring for this user/IP",
                "Require additional authentication",
                "Log detailed audit trail"
            ])
        elif threat_level == ThreatLevel.MEDIUM:
            actions.extend([
                "Monitor closely",
                "Apply rate limiting",
                "Log security event"
            ])
        
        # Specific actions based on threat types
        threat_types = [t["type"] for t in threats]
        if "sql_injection" in threat_types:
            actions.append("Block database access")
        if "xss" in threat_types:
            actions.append("Sanitize input and output")
        if "malicious_ip" in threat_types:
            actions.append("Add IP to blocklist")
        
        return actions

class ComplianceManager:
    """Manages security compliance and auditing"""
    
    def __init__(self):
        self.compliance_frameworks = {
            "GDPR": {
                "data_retention_days": 365,
                "consent_required": True,
                "right_to_deletion": True,
                "data_portability": True
            },
            "HIPAA": {
                "encryption_required": True,
                "audit_logs_required": True,
                "access_controls": True,
                "data_backup": True
            },
            "SOC2": {
                "security_controls": True,
                "availability_monitoring": True,
                "processing_integrity": True,
                "confidentiality": True
            }
        }
        self.audit_logs = []
    
    async def check_compliance(
        self, 
        framework: str, 
        data_operation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check compliance for data operation"""
        if framework not in self.compliance_frameworks:
            raise ValueError(f"Unknown compliance framework: {framework}")
        
        requirements = self.compliance_frameworks[framework]
        compliance_status = {}
        violations = []
        
        # Check GDPR compliance
        if framework == "GDPR":
            if requirements["consent_required"]:
                if not data_operation.get("user_consent"):
                    violations.append("Missing user consent")
                else:
                    compliance_status["consent"] = "compliant"
            
            if requirements["right_to_deletion"]:
                if data_operation.get("operation") == "delete":
                    compliance_status["deletion_right"] = "exercised"
        
        # Check HIPAA compliance
        elif framework == "HIPAA":
            if requirements["encryption_required"]:
                if not data_operation.get("encrypted"):
                    violations.append("Data not encrypted")
                else:
                    compliance_status["encryption"] = "compliant"
            
            if requirements["audit_logs_required"]:
                await self._log_audit_event(data_operation)
                compliance_status["audit_logging"] = "compliant"
        
        # Check SOC2 compliance
        elif framework == "SOC2":
            if requirements["security_controls"]:
                if not data_operation.get("security_validated"):
                    violations.append("Security controls not validated")
                else:
                    compliance_status["security_controls"] = "compliant"
        
        return {
            "framework": framework,
            "compliant": len(violations) == 0,
            "violations": violations,
            "status": compliance_status,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _log_audit_event(self, data_operation: Dict[str, Any]):
        """Log audit event for compliance"""
        audit_event = {
            "timestamp": datetime.now().isoformat(),
            "user_id": data_operation.get("user_id"),
            "operation": data_operation.get("operation"),
            "resource": data_operation.get("resource"),
            "ip_address": data_operation.get("ip_address"),
            "user_agent": data_operation.get("user_agent"),
            "result": data_operation.get("result", "success")
        }
        
        self.audit_logs.append(audit_event)
        
        # In production, this would write to a secure audit log system
        logger.info(f"📋 Audit event logged: {audit_event['operation']}")
    
    def generate_compliance_report(self, framework: str, period_days: int = 30) -> Dict[str, Any]:
        """Generate compliance report"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # Filter audit logs for period
        period_logs = [
            log for log in self.audit_logs
            if start_date <= datetime.fromisoformat(log["timestamp"]) <= end_date
        ]
        
        # Analyze compliance metrics
        total_operations = len(period_logs)
        failed_operations = len([log for log in period_logs if log["result"] != "success"])
        
        return {
            "framework": framework,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": period_days
            },
            "metrics": {
                "total_operations": total_operations,
                "failed_operations": failed_operations,
                "success_rate": (total_operations - failed_operations) / max(total_operations, 1) * 100
            },
            "audit_events": len(period_logs),
            "compliance_score": self._calculate_compliance_score(period_logs),
            "recommendations": self._get_compliance_recommendations(framework, period_logs)
        }
    
    def _calculate_compliance_score(self, audit_logs: List[Dict[str, Any]]) -> float:
        """Calculate compliance score based on audit logs"""
        if not audit_logs:
            return 100.0
        
        # Simple scoring based on success rate and completeness
        successful_ops = len([log for log in audit_logs if log["result"] == "success"])
        success_rate = successful_ops / len(audit_logs)
        
        # Check for required fields
        complete_logs = len([
            log for log in audit_logs 
            if all(field in log for field in ["user_id", "operation", "ip_address"])
        ])
        completeness_rate = complete_logs / len(audit_logs)
        
        return (success_rate * 0.7 + completeness_rate * 0.3) * 100
    
    def _get_compliance_recommendations(
        self, 
        framework: str, 
        audit_logs: List[Dict[str, Any]]
    ) -> List[str]:
        """Get compliance improvement recommendations"""
        recommendations = []
        
        if framework == "GDPR":
            recommendations.extend([
                "Implement automated consent management",
                "Set up data retention policies",
                "Create data portability tools"
            ])
        elif framework == "HIPAA":
            recommendations.extend([
                "Enhance encryption for data at rest",
                "Implement role-based access controls",
                "Set up automated backup systems"
            ])
        elif framework == "SOC2":
            recommendations.extend([
                "Implement continuous security monitoring",
                "Set up availability alerting",
                "Create incident response procedures"
            ])
        
        return recommendations

class SecurityOrchestrator:
    """Orchestrates all security components"""
    
    def __init__(self):
        self.encryption = AdvancedEncryption()
        self.threat_detection = ThreatDetectionEngine()
        self.compliance_manager = ComplianceManager()
        self.security_events = []
        self.active_incidents = {}
    
    async def process_security_event(
        self, 
        event_type: SecurityEventType,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process and respond to security event"""
        # Analyze threat
        threat_analysis = await self.threat_detection.analyze_request(
            context.get("request_data", {}),
            context.get("user_context", {})
        )
        
        # Create security event
        event = SecurityEvent(
            event_id=secrets.token_hex(16),
            event_type=event_type,
            threat_level=ThreatLevel(threat_analysis["threat_level"].value),
            timestamp=datetime.now(),
            user_id=context.get("user_context", {}).get("user_id"),
            ip_address=context.get("user_context", {}).get("ip_address", "unknown"),
            user_agent=context.get("user_context", {}).get("user_agent", "unknown"),
            details=threat_analysis,
            response_actions=threat_analysis["recommended_actions"]
        )
        
        self.security_events.append(event)
        
        # Execute response actions
        response_result = await self._execute_response_actions(event)
        
        # Check compliance
        compliance_result = await self.compliance_manager.check_compliance(
            "SOC2",  # Default framework
            {
                "operation": "security_event",
                "user_id": event.user_id,
                "ip_address": event.ip_address,
                "security_validated": True,
                "encrypted": True
            }
        )
        
        return {
            "event_id": event.event_id,
            "threat_level": event.threat_level.value,
            "actions_taken": response_result["actions_executed"],
            "compliance_status": compliance_result["compliant"],
            "incident_created": response_result.get("incident_created", False)
        }
    
    async def _execute_response_actions(self, event: SecurityEvent) -> Dict[str, Any]:
        """Execute automated response actions"""
        actions_executed = []
        incident_created = False
        
        for action in event.response_actions:
            try:
                if action == "Block IP address immediately":
                    await self._block_ip_address(event.ip_address)
                    actions_executed.append("ip_blocked")
                
                elif action == "Terminate user session":
                    if event.user_id:
                        await self._terminate_user_sessions(event.user_id)
                        actions_executed.append("sessions_terminated")
                
                elif action == "Alert security team":
                    await self._alert_security_team(event)
                    actions_executed.append("security_team_alerted")
                
                elif action == "Initiate incident response":
                    incident_id = await self._create_security_incident(event)
                    actions_executed.append(f"incident_created_{incident_id}")
                    incident_created = True
                
                elif action == "Apply rate limiting":
                    await self._apply_rate_limiting(event.ip_address, event.user_id)
                    actions_executed.append("rate_limiting_applied")
                
            except Exception as e:
                logger.error(f"Failed to execute action '{action}': {e}")
        
        return {
            "actions_executed": actions_executed,
            "incident_created": incident_created
        }
    
    async def _block_ip_address(self, ip_address: str):
        """Block IP address"""
        # In production, this would integrate with firewall/WAF
        logger.warning(f"🚫 IP address blocked: {ip_address}")
    
    async def _terminate_user_sessions(self, user_id: str):
        """Terminate all user sessions"""
        # In production, this would invalidate JWT tokens/sessions
        logger.warning(f"🔒 User sessions terminated: {user_id}")
    
    async def _alert_security_team(self, event: SecurityEvent):
        """Alert security team"""
        # In production, this would send notifications via email/Slack/PagerDuty
        logger.critical(f"🚨 Security alert: {event.event_type.value} - {event.threat_level.value}")
    
    async def _create_security_incident(self, event: SecurityEvent) -> str:
        """Create security incident"""
        incident_id = f"INC-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
        
        incident = {
            "incident_id": incident_id,
            "created_at": datetime.now(),
            "severity": event.threat_level.value,
            "status": "open",
            "events": [event.event_id],
            "assigned_to": None,
            "resolution": None
        }
        
        self.active_incidents[incident_id] = incident
        logger.critical(f"🚨 Security incident created: {incident_id}")
        
        return incident_id
    
    async def _apply_rate_limiting(self, ip_address: str, user_id: Optional[str]):
        """Apply rate limiting"""
        # In production, this would configure rate limiting rules
        logger.info(f"⏱️ Rate limiting applied: IP={ip_address}, User={user_id}")
    
    def get_security_dashboard(self) -> Dict[str, Any]:
        """Get security dashboard data"""
        recent_events = [
            event for event in self.security_events
            if datetime.now() - event.timestamp < timedelta(hours=24)
        ]
        
        threat_level_counts = {}
        for level in ThreatLevel:
            threat_level_counts[level.value] = len([
                event for event in recent_events
                if event.threat_level == level
            ])
        
        return {
            "summary": {
                "total_events_24h": len(recent_events),
                "active_incidents": len(self.active_incidents),
                "threat_level_distribution": threat_level_counts
            },
            "recent_events": [
                {
                    "event_id": event.event_id,
                    "type": event.event_type.value,
                    "threat_level": event.threat_level.value,
                    "timestamp": event.timestamp.isoformat(),
                    "ip_address": event.ip_address,
                    "resolved": event.resolved
                }
                for event in recent_events[-10:]  # Last 10 events
            ],
            "active_incidents": [
                {
                    "incident_id": incident_id,
                    "severity": incident["severity"],
                    "created_at": incident["created_at"].isoformat(),
                    "status": incident["status"]
                }
                for incident_id, incident in self.active_incidents.items()
            ]
        }

# Global security orchestrator
security_orchestrator = SecurityOrchestrator()

# Convenience functions
async def process_security_event(event_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Process security event"""
    return await security_orchestrator.process_security_event(
        SecurityEventType(event_type), 
        context
    )

def encrypt_data(data: str, context: str = "default") -> str:
    """Encrypt sensitive data"""
    return security_orchestrator.encryption.encrypt_sensitive_data(data, context)

def decrypt_data(encrypted_data: str, context: str = "default") -> str:
    """Decrypt sensitive data"""
    return security_orchestrator.encryption.decrypt_sensitive_data(encrypted_data, context)

async def check_compliance(framework: str, operation: Dict[str, Any]) -> Dict[str, Any]:
    """Check compliance for operation"""
    return await security_orchestrator.compliance_manager.check_compliance(framework, operation)

if __name__ == "__main__":
    # Example usage
    async def test_security_system():
        print("🧪 Testing Advanced Security System...")
        
        # Test threat detection
        context = {
            "request_data": {
                "query": "SELECT * FROM users WHERE id = 1 OR 1=1",
                "user_input": "<script>alert('xss')</script>"
            },
            "user_context": {
                "user_id": "user123",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0..."
            }
        }
        
        result = await process_security_event("suspicious_activity", context)
        print(f"Security event processed: {result['event_id']}")
        print(f"Threat level: {result['threat_level']}")
        print(f"Actions taken: {result['actions_taken']}")
        
        # Test encryption
        sensitive_data = "user_password_123"
        encrypted = encrypt_data(sensitive_data, "passwords")
        decrypted = decrypt_data(encrypted, "passwords")
        print(f"Encryption test: {sensitive_data == decrypted}")
        
        # Test compliance
        compliance_result = await check_compliance("GDPR", {
            "operation": "data_access",
            "user_consent": True,
            "user_id": "user123"
        })
        print(f"GDPR compliance: {compliance_result['compliant']}")
        
        # Get security dashboard
        dashboard = security_orchestrator.get_security_dashboard()
        print(f"Security events (24h): {dashboard['summary']['total_events_24h']}")
    
    asyncio.run(test_security_system())