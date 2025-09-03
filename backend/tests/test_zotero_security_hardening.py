"""
Tests for Zotero security hardening service.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from services.zotero.zotero_security_hardening_service import (
    ZoteroSecurityHardeningService,
    SecurityHardeningLevel,
    ComplianceFramework,
    SecurityPolicy,
    VulnerabilityAssessment
)


class TestZoteroSecurityHardeningService:
    """Test cases for Zotero security hardening service."""
    
    @pytest.fixture
    def hardening_service(self):
        """Create hardening service instance."""
        return ZoteroSecurityHardeningService()
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock()
        mock_redis.get = AsyncMock()
        mock_redis.lpush = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=[])
        mock_redis.ltrim = AsyncMock()
        mock_redis.expire = AsyncMock()
        return mock_redis
    
    def test_init_security_policies(self, hardening_service):
        """Test security policies initialization."""
        assert len(hardening_service.security_policies) > 0
        
        # Check password policy
        password_policy = hardening_service.security_policies.get('password_policy')
        assert password_policy is not None
        assert password_policy.enabled is True
        assert password_policy.severity == "high"
        assert password_policy.rules['min_length'] >= 12
        
        # Check session policy
        session_policy = hardening_service.security_policies.get('session_policy')
        assert session_policy is not None
        assert session_policy.rules['max_session_duration'] <= 1800
        
        # Check data protection policy
        data_policy = hardening_service.security_policies.get('data_protection_policy')
        assert data_policy is not None
        assert data_policy.severity == "critical"
        assert data_policy.rules['encryption_at_rest'] is True
    
    def test_init_threat_intelligence(self, hardening_service):
        """Test threat intelligence initialization."""
        assert len(hardening_service.threat_indicators) > 0
        assert len(hardening_service.malicious_patterns) > 0
        
        # Check for SQL injection patterns
        sql_patterns = [p for p in hardening_service.malicious_patterns if 'union' in p.lower()]
        assert len(sql_patterns) > 0
        
        # Check for XSS patterns
        xss_patterns = [p for p in hardening_service.malicious_patterns if 'script' in p.lower()]
        assert len(xss_patterns) > 0
    
    def test_init_compliance_requirements(self, hardening_service):
        """Test compliance requirements initialization."""
        assert ComplianceFramework.GDPR in hardening_service.compliance_requirements
        assert ComplianceFramework.SOC2 in hardening_service.compliance_requirements
        assert ComplianceFramework.OWASP in hardening_service.compliance_requirements
        
        # Check GDPR requirements
        gdpr_reqs = hardening_service.compliance_requirements[ComplianceFramework.GDPR]
        assert gdpr_reqs['data_minimization'] is True
        assert gdpr_reqs['consent_management'] is True
        assert gdpr_reqs['right_to_erasure'] is True
        
        # Check OWASP requirements
        owasp_reqs = hardening_service.compliance_requirements[ComplianceFramework.OWASP]
        assert owasp_reqs['injection_prevention'] is True
        assert owasp_reqs['broken_authentication'] is True
    
    @pytest.mark.asyncio
    async def test_perform_comprehensive_security_audit(self, hardening_service, mock_redis):
        """Test comprehensive security audit."""
        with patch('services.zotero.zotero_security_hardening_service.get_redis_client', return_value=mock_redis):
            with patch.object(hardening_service, '_get_recent_security_events', return_value=[]):
                audit_results = await hardening_service.perform_comprehensive_security_audit()
                
                assert 'audit_id' in audit_results
                assert 'timestamp' in audit_results
                assert 'hardening_level' in audit_results
                assert 'policy_compliance' in audit_results
                assert 'vulnerability_assessment' in audit_results
                assert 'threat_analysis' in audit_results
                assert 'compliance_status' in audit_results
                assert 'recommendations' in audit_results
                assert 'risk_score' in audit_results
                
                # Check that audit results are stored
                mock_redis.set.assert_called()
                mock_redis.lpush.assert_called()
    
    @pytest.mark.asyncio
    async def test_audit_policy_compliance(self, hardening_service):
        """Test policy compliance audit."""
        compliance_results = await hardening_service._audit_policy_compliance()
        
        assert isinstance(compliance_results, dict)
        assert len(compliance_results) > 0
        
        for policy_name, result in compliance_results.items():
            assert 'score' in result
            assert 'violations' in result
            assert 'severity' in result
            assert 'compliance_frameworks' in result
            assert 0.0 <= result['score'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_perform_vulnerability_assessment(self, hardening_service):
        """Test vulnerability assessment."""
        vulnerabilities = await hardening_service._perform_vulnerability_assessment()
        
        assert isinstance(vulnerabilities, list)
        
        for vuln in vulnerabilities:
            assert isinstance(vuln, VulnerabilityAssessment)
            assert vuln.vulnerability_id
            assert vuln.category
            assert vuln.severity in ['low', 'medium', 'high', 'critical']
            assert vuln.description
            assert isinstance(vuln.affected_components, list)
            assert isinstance(vuln.remediation_steps, list)
            assert isinstance(vuln.compliance_impact, dict)
            assert 0.0 <= vuln.risk_score <= 10.0
    
    @pytest.mark.asyncio
    async def test_analyze_threats(self, hardening_service):
        """Test threat analysis."""
        with patch.object(hardening_service, '_get_recent_security_events', return_value=[
            {'event_type': 'authentication_failure', 'details': {}},
            {'event_type': 'rate_limit_exceeded', 'details': {}},
            {'event_type': 'security_violation', 'details': {'patterns': ['injection']}}
        ]):
            threat_analysis = await hardening_service._analyze_threats()
            
            assert 'active_threats' in threat_analysis
            assert 'threat_categories' in threat_analysis
            assert 'risk_indicators' in threat_analysis
            assert 'mitigation_status' in threat_analysis
            
            assert threat_analysis['active_threats'] >= 0
            assert isinstance(threat_analysis['threat_categories'], dict)
            assert isinstance(threat_analysis['risk_indicators'], list)
    
    @pytest.mark.asyncio
    async def test_assess_compliance_frameworks(self, hardening_service):
        """Test compliance framework assessment."""
        compliance_status = await hardening_service._assess_compliance_frameworks()
        
        assert isinstance(compliance_status, dict)
        
        for framework, status in compliance_status.items():
            assert 'score' in status
            assert 'met_requirements' in status
            assert 'total_requirements' in status
            assert 'compliance_percentage' in status
            assert 'gaps' in status
            assert 'status' in status
            
            assert 0.0 <= status['score'] <= 1.0
            assert status['status'] in ['compliant', 'non_compliant']
    
    @pytest.mark.asyncio
    async def test_generate_security_recommendations(self, hardening_service):
        """Test security recommendations generation."""
        # Mock audit results
        audit_results = {
            'policy_compliance': {
                'password_policy': {
                    'score': 0.6,
                    'violations': ['Password complexity not enforced'],
                    'severity': 'high',
                    'compliance_frameworks': ['gdpr', 'soc2']
                }
            },
            'vulnerability_assessment': [
                VulnerabilityAssessment(
                    vulnerability_id="TEST-001",
                    category="authentication",
                    severity="high",
                    description="Test vulnerability",
                    affected_components=["auth_service"],
                    remediation_steps=["Fix authentication"],
                    compliance_impact={"SOC2": "Control deficiency"},
                    risk_score=7.5
                )
            ],
            'compliance_status': {
                'gdpr': {
                    'status': 'non_compliant',
                    'gaps': ['data_minimization', 'consent_management']
                }
            },
            'threat_analysis': {
                'active_threats': 100
            }
        }
        
        recommendations = await hardening_service._generate_security_recommendations(audit_results)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        for rec in recommendations:
            assert 'category' in rec
            assert 'priority' in rec
            assert 'title' in rec
            assert 'description' in rec
            assert 'estimated_effort' in rec
            assert 'compliance_impact' in rec
    
    def test_calculate_risk_score(self, hardening_service):
        """Test risk score calculation."""
        # Mock audit results
        audit_results = {
            'policy_compliance': {
                'policy1': {'score': 0.8},
                'policy2': {'score': 0.6}
            },
            'vulnerability_assessment': [
                VulnerabilityAssessment(
                    vulnerability_id="TEST-001",
                    category="test",
                    severity="high",
                    description="Test",
                    affected_components=[],
                    remediation_steps=[],
                    compliance_impact={},
                    risk_score=7.0
                )
            ],
            'compliance_status': {
                'framework1': {'score': 0.9},
                'framework2': {'score': 0.7}
            },
            'threat_analysis': {
                'active_threats': 25
            }
        }
        
        risk_score = hardening_service._calculate_risk_score(audit_results)
        
        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 10.0
    
    @pytest.mark.asyncio
    async def test_store_audit_results(self, hardening_service, mock_redis):
        """Test audit results storage."""
        audit_results = {
            'audit_id': 'test-audit-123',
            'timestamp': datetime.utcnow().isoformat(),
            'test_data': 'test_value'
        }
        
        with patch('services.zotero.zotero_security_hardening_service.get_redis_client', return_value=mock_redis):
            await hardening_service._store_audit_results(audit_results)
            
            # Verify Redis calls
            mock_redis.set.assert_called_once()
            mock_redis.lpush.assert_called_once()
            mock_redis.ltrim.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_recent_security_events(self, hardening_service, mock_redis):
        """Test getting recent security events."""
        # Mock Redis responses
        mock_redis.lrange.return_value = [
            "{'event_type': 'authentication_failure', 'timestamp': '2023-12-07T10:00:00Z'}",
            "{'event_type': 'rate_limit_exceeded', 'timestamp': '2023-12-07T10:05:00Z'}"
        ]
        
        with patch('services.zotero.zotero_security_hardening_service.get_redis_client', return_value=mock_redis):
            events = await hardening_service._get_recent_security_events()
            
            assert isinstance(events, list)
            # Note: In production, would use json.loads instead of eval
    
    @pytest.mark.asyncio
    async def test_check_compliance_requirement(self, hardening_service):
        """Test compliance requirement checking."""
        # Test GDPR requirements
        result = await hardening_service._check_compliance_requirement(
            ComplianceFramework.GDPR, 'data_minimization'
        )
        assert isinstance(result, bool)
        
        # Test OWASP requirements
        result = await hardening_service._check_compliance_requirement(
            ComplianceFramework.OWASP, 'injection_prevention'
        )
        assert isinstance(result, bool)
        
        # Test unknown requirement
        result = await hardening_service._check_compliance_requirement(
            ComplianceFramework.GDPR, 'unknown_requirement'
        )
        assert result is False
    
    def test_security_check_methods(self, hardening_service):
        """Test various security check methods."""
        # Test password complexity check
        result = hardening_service._check_password_complexity()
        assert isinstance(result, bool)
        
        # Test account lockout check
        result = hardening_service._check_account_lockout()
        assert isinstance(result, bool)
        
        # Test session security check
        result = hardening_service._check_session_security()
        assert isinstance(result, bool)
        
        # Test encryption implementation check
        result = hardening_service._check_encryption_implementation()
        assert isinstance(result, bool)
        
        # Test rate limiting check
        result = hardening_service._check_rate_limiting()
        assert isinstance(result, bool)
        
        # Test input validation check
        result = hardening_service._check_input_validation()
        assert isinstance(result, bool)
        
        # Test authentication implementation check
        result = hardening_service._check_authentication_implementation()
        assert isinstance(result, bool)
        
        # Test MFA implementation check
        result = hardening_service._check_mfa_implementation()
        assert isinstance(result, bool)
        
        # Test RBAC implementation check
        result = hardening_service._check_rbac_implementation()
        assert isinstance(result, bool)
        
        # Test data encryption check
        result = hardening_service._check_data_encryption()
        assert isinstance(result, bool)
        
        # Test comprehensive input validation check
        result = hardening_service._check_comprehensive_input_validation()
        assert isinstance(result, bool)
        
        # Test secure session management check
        result = hardening_service._check_secure_session_management()
        assert isinstance(result, bool)
        
        # Test security monitoring check
        result = hardening_service._check_security_monitoring()
        assert isinstance(result, bool)


class TestSecurityPolicy:
    """Test cases for SecurityPolicy dataclass."""
    
    def test_security_policy_creation(self):
        """Test SecurityPolicy creation."""
        policy = SecurityPolicy(
            name="Test Policy",
            description="Test description",
            enabled=True,
            severity="high",
            rules={'rule1': 'value1'},
            compliance_frameworks=[ComplianceFramework.GDPR]
        )
        
        assert policy.name == "Test Policy"
        assert policy.description == "Test description"
        assert policy.enabled is True
        assert policy.severity == "high"
        assert policy.rules == {'rule1': 'value1'}
        assert ComplianceFramework.GDPR in policy.compliance_frameworks


class TestVulnerabilityAssessment:
    """Test cases for VulnerabilityAssessment dataclass."""
    
    def test_vulnerability_assessment_creation(self):
        """Test VulnerabilityAssessment creation."""
        vuln = VulnerabilityAssessment(
            vulnerability_id="TEST-001",
            category="authentication",
            severity="high",
            description="Test vulnerability",
            affected_components=["auth_service"],
            remediation_steps=["Fix authentication"],
            compliance_impact={"SOC2": "Control deficiency"},
            risk_score=7.5
        )
        
        assert vuln.vulnerability_id == "TEST-001"
        assert vuln.category == "authentication"
        assert vuln.severity == "high"
        assert vuln.description == "Test vulnerability"
        assert vuln.affected_components == ["auth_service"]
        assert vuln.remediation_steps == ["Fix authentication"]
        assert vuln.compliance_impact == {"SOC2": "Control deficiency"}
        assert vuln.risk_score == 7.5


class TestSecurityHardeningIntegration:
    """Integration tests for security hardening service."""
    
    @pytest.mark.asyncio
    async def test_full_security_audit_workflow(self):
        """Test complete security audit workflow."""
        hardening_service = ZoteroSecurityHardeningService()
        
        # Mock dependencies
        with patch('services.zotero.zotero_security_hardening_service.get_redis_client') as mock_redis_client:
            mock_redis = AsyncMock()
            mock_redis.set = AsyncMock()
            mock_redis.lpush = AsyncMock()
            mock_redis.ltrim = AsyncMock()
            mock_redis.lrange = AsyncMock(return_value=[])
            mock_redis_client.return_value = mock_redis
            
            # Perform audit
            audit_results = await hardening_service.perform_comprehensive_security_audit()
            
            # Verify audit results structure
            assert isinstance(audit_results, dict)
            assert 'audit_id' in audit_results
            assert 'risk_score' in audit_results
            assert isinstance(audit_results['risk_score'], float)
            
            # Verify storage was attempted
            mock_redis.set.assert_called()
    
    def test_security_hardening_service_singleton(self):
        """Test that security hardening service can be imported as singleton."""
        from services.zotero.zotero_security_hardening_service import security_hardening_service
        
        assert security_hardening_service is not None
        assert isinstance(security_hardening_service, ZoteroSecurityHardeningService)
        assert hasattr(security_hardening_service, 'security_policies')
        assert hasattr(security_hardening_service, 'compliance_requirements')


if __name__ == '__main__':
    pytest.main([__file__])