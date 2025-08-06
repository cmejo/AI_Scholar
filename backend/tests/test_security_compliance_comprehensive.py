"""
Comprehensive Security and Compliance Testing Suite

This module provides comprehensive testing for:
- Voice data privacy and encryption
- Integration security with OAuth and API key validation
- Institutional policy compliance
- Accessibility compliance testing
"""

import pytest
import asyncio
import json
import base64
import hashlib
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import jwt
import requests_mock
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from axe_selenium_python import Axe

# Import services for testing
from backend.services.voice_processing_service import VoiceProcessingService
from backend.services.oauth_server import OAuthServer
from backend.services.api_key_service import APIKeyService
from backend.services.compliance_monitoring_service import ComplianceMonitoringService
from backend.services.institutional_role_management_service import InstitutionalRoleManagementService
from backend.core.database import get_db_connection


class TestVoiceDataSecurity:
    """Test voice data privacy and encryption compliance"""
    
    @pytest.fixture
    def voice_service(self):
        return VoiceProcessingService()
    
    @pytest.fixture
    def encryption_key(self):
        """Generate test encryption key"""
        password = b"test_voice_encryption_key"
        salt = b"test_salt_12345678"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)
    
    @pytest.mark.asyncio
    async def test_voice_data_encryption_at_rest(self, voice_service, encryption_key):
        """Test that voice data is encrypted when stored"""
        # Simulate voice data
        test_audio_data = b"test_audio_data_sample"
        
        # Test encryption
        encrypted_data = encryption_key.encrypt(test_audio_data)
        assert encrypted_data != test_audio_data
        
        # Test decryption
        decrypted_data = encryption_key.decrypt(encrypted_data)
        assert decrypted_data == test_audio_data
        
        # Verify no plaintext audio data in storage
        with patch('backend.services.voice_processing_service.store_audio_data') as mock_store:
            await voice_service.process_audio(test_audio_data)
            
            # Verify stored data is encrypted
            stored_data = mock_store.call_args[0][0]
            assert stored_data != test_audio_data
            assert len(stored_data) > len(test_audio_data)  # Encrypted data is larger
    
    @pytest.mark.asyncio
    async def test_voice_data_transmission_security(self, voice_service):
        """Test voice data is encrypted during transmission"""
        test_audio_data = b"test_transmission_audio"
        
        with patch('backend.services.voice_processing_service.transmit_audio') as mock_transmit:
            await voice_service.transmit_voice_data(test_audio_data)
            
            # Verify transmission uses encryption
            transmitted_data = mock_transmit.call_args[0][0]
            assert 'encrypted' in str(transmitted_data).lower() or len(transmitted_data) != len(test_audio_data)
    
    @pytest.mark.asyncio
    async def test_voice_data_retention_policy(self, voice_service):
        """Test voice data retention and deletion policies"""
        test_session_id = "test_voice_session_123"
        
        with patch('backend.services.voice_processing_service.get_voice_session_age') as mock_age:
            # Test data older than retention period is deleted
            mock_age.return_value = timedelta(days=31)  # Older than 30-day policy
            
            result = await voice_service.cleanup_expired_voice_data(test_session_id)
            assert result.deleted is True
            
            # Test data within retention period is kept
            mock_age.return_value = timedelta(days=15)  # Within 30-day policy
            
            result = await voice_service.cleanup_expired_voice_data(test_session_id)
            assert result.deleted is False
    
    @pytest.mark.asyncio
    async def test_voice_biometric_protection(self, voice_service):
        """Test voice biometric data protection"""
        test_voice_profile = {
            "user_id": "test_user_123",
            "voice_characteristics": "test_biometric_data",
            "created_at": datetime.now()
        }
        
        with patch('backend.services.voice_processing_service.store_voice_profile') as mock_store:
            await voice_service.create_voice_profile(test_voice_profile)
            
            # Verify biometric data is hashed/encrypted
            stored_profile = mock_store.call_args[0][0]
            assert stored_profile["voice_characteristics"] != test_voice_profile["voice_characteristics"]
    
    @pytest.mark.asyncio
    async def test_voice_consent_management(self, voice_service):
        """Test voice data consent and opt-out mechanisms"""
        user_id = "test_user_consent"
        
        # Test consent recording
        consent_result = await voice_service.record_voice_consent(user_id, consent=True)
        assert consent_result.success is True
        
        # Test opt-out functionality
        opt_out_result = await voice_service.opt_out_voice_processing(user_id)
        assert opt_out_result.success is True
        
        # Test data deletion after opt-out
        with patch('backend.services.voice_processing_service.delete_user_voice_data') as mock_delete:
            await voice_service.process_opt_out_request(user_id)
            mock_delete.assert_called_once_with(user_id)


class TestIntegrationSecurity:
    """Test integration security with OAuth and API key validation"""
    
    @pytest.fixture
    def oauth_server(self):
        return OAuthServer()
    
    @pytest.fixture
    def api_key_service(self):
        return APIKeyService()
    
    @pytest.mark.asyncio
    async def test_oauth_token_security(self, oauth_server):
        """Test OAuth token generation and validation security"""
        client_id = "test_client_123"
        client_secret = "test_secret_456"
        
        # Test token generation
        token_result = await oauth_server.generate_access_token(client_id, client_secret)
        assert token_result.success is True
        assert len(token_result.access_token) > 32  # Sufficient length
        
        # Test token validation
        validation_result = await oauth_server.validate_token(token_result.access_token)
        assert validation_result.valid is True
        
        # Test token expiration
        expired_token = jwt.encode(
            {"exp": datetime.utcnow() - timedelta(hours=1)},
            "secret",
            algorithm="HS256"
        )
        
        validation_result = await oauth_server.validate_token(expired_token)
        assert validation_result.valid is False
    
    @pytest.mark.asyncio
    async def test_api_key_security(self, api_key_service):
        """Test API key generation and validation security"""
        user_id = "test_user_api"
        
        # Test API key generation
        key_result = await api_key_service.generate_api_key(user_id)
        assert key_result.success is True
        assert len(key_result.api_key) >= 32  # Minimum secure length
        
        # Test key validation
        validation_result = await api_key_service.validate_api_key(key_result.api_key)
        assert validation_result.valid is True
        assert validation_result.user_id == user_id
        
        # Test key rotation
        rotation_result = await api_key_service.rotate_api_key(key_result.api_key)
        assert rotation_result.success is True
        assert rotation_result.new_key != key_result.api_key
        
        # Test old key is invalidated
        old_validation = await api_key_service.validate_api_key(key_result.api_key)
        assert old_validation.valid is False
    
    @pytest.mark.asyncio
    async def test_integration_rate_limiting(self, api_key_service):
        """Test rate limiting for API integrations"""
        api_key = "test_rate_limit_key"
        
        # Simulate multiple requests
        for i in range(100):  # Exceed rate limit
            result = await api_key_service.check_rate_limit(api_key)
            if i < 50:  # Within limit
                assert result.allowed is True
            else:  # Exceeds limit
                assert result.allowed is False
                assert result.retry_after > 0
    
    @pytest.mark.asyncio
    async def test_integration_permission_validation(self, oauth_server):
        """Test integration permission scopes and validation"""
        client_id = "test_permissions_client"
        requested_scopes = ["read:documents", "write:notes", "admin:users"]
        
        # Test scope validation
        scope_result = await oauth_server.validate_scopes(client_id, requested_scopes)
        
        # Should reject admin scope for regular client
        assert "admin:users" not in scope_result.granted_scopes
        assert "read:documents" in scope_result.granted_scopes
        assert "write:notes" in scope_result.granted_scopes
    
    @pytest.mark.asyncio
    async def test_integration_data_isolation(self):
        """Test data isolation between different integrations"""
        integration_a_id = "integration_a"
        integration_b_id = "integration_b"
        
        # Test that integration A cannot access integration B's data
        with patch('backend.services.api_key_service.get_integration_data') as mock_get_data:
            mock_get_data.return_value = {"integration_id": integration_a_id, "data": "sensitive_data_a"}
            
            # Integration B tries to access Integration A's data
            with pytest.raises(PermissionError):
                await APIKeyService().get_integration_data(integration_b_id, integration_a_id)


class TestComplianceTesting:
    """Test institutional policy and regulatory compliance"""
    
    @pytest.fixture
    def compliance_service(self):
        return ComplianceMonitoringService()
    
    @pytest.fixture
    def role_service(self):
        return InstitutionalRoleManagementService()
    
    @pytest.mark.asyncio
    async def test_gdpr_compliance(self, compliance_service):
        """Test GDPR compliance for data processing"""
        user_data = {
            "user_id": "test_gdpr_user",
            "personal_data": "sensitive_personal_information",
            "consent_given": True,
            "data_purpose": "research_assistance"
        }
        
        # Test data processing consent
        consent_check = await compliance_service.check_gdpr_consent(user_data)
        assert consent_check.compliant is True
        
        # Test data subject rights (right to be forgotten)
        deletion_result = await compliance_service.process_deletion_request(user_data["user_id"])
        assert deletion_result.success is True
        
        # Test data portability
        export_result = await compliance_service.export_user_data(user_data["user_id"])
        assert export_result.success is True
        assert "personal_data" in export_result.exported_data
    
    @pytest.mark.asyncio
    async def test_ferpa_compliance(self, compliance_service):
        """Test FERPA compliance for educational records"""
        student_record = {
            "student_id": "test_student_123",
            "educational_data": "grades_and_progress",
            "institution_id": "test_university",
            "access_level": "restricted"
        }
        
        # Test educational record access controls
        access_check = await compliance_service.check_ferpa_access(
            student_record["student_id"],
            requester_role="instructor"
        )
        assert access_check.allowed is True
        
        # Test unauthorized access prevention
        unauthorized_check = await compliance_service.check_ferpa_access(
            student_record["student_id"],
            requester_role="external_user"
        )
        assert unauthorized_check.allowed is False
    
    @pytest.mark.asyncio
    async def test_institutional_policy_enforcement(self, compliance_service):
        """Test institutional policy enforcement"""
        policy_data = {
            "policy_id": "research_ethics_001",
            "institution_id": "test_institution",
            "policy_type": "research_ethics",
            "rules": [
                {"type": "data_retention", "value": "7_years"},
                {"type": "consent_required", "value": True},
                {"type": "anonymization_required", "value": True}
            ]
        }
        
        research_proposal = {
            "proposal_id": "test_proposal_123",
            "data_retention_period": "5_years",  # Violates policy
            "consent_obtained": True,
            "data_anonymized": False  # Violates policy
        }
        
        # Test policy compliance check
        compliance_result = await compliance_service.check_policy_compliance(
            research_proposal, policy_data
        )
        
        assert compliance_result.compliant is False
        assert len(compliance_result.violations) == 2  # Two violations
        assert "data_retention" in [v.rule_type for v in compliance_result.violations]
        assert "anonymization_required" in [v.rule_type for v in compliance_result.violations]
    
    @pytest.mark.asyncio
    async def test_audit_logging_compliance(self, compliance_service):
        """Test audit logging for compliance requirements"""
        audit_event = {
            "event_type": "data_access",
            "user_id": "test_user_audit",
            "resource_id": "sensitive_document_123",
            "timestamp": datetime.now(),
            "ip_address": "192.168.1.100",
            "user_agent": "test_browser"
        }
        
        # Test audit log creation
        log_result = await compliance_service.create_audit_log(audit_event)
        assert log_result.success is True
        
        # Test audit log integrity (tamper detection)
        log_integrity = await compliance_service.verify_audit_log_integrity(log_result.log_id)
        assert log_integrity.valid is True
        
        # Test audit log retention
        retention_check = await compliance_service.check_audit_retention_policy()
        assert retention_check.compliant is True
    
    @pytest.mark.asyncio
    async def test_role_based_access_compliance(self, role_service):
        """Test role-based access control compliance"""
        user_roles = {
            "user_id": "test_rbac_user",
            "roles": ["student", "research_assistant"],
            "institution_id": "test_institution",
            "department": "computer_science"
        }
        
        # Test access to student resources
        student_access = await role_service.check_resource_access(
            user_roles["user_id"],
            resource_type="student_records",
            action="read"
        )
        assert student_access.allowed is True
        
        # Test denied access to admin resources
        admin_access = await role_service.check_resource_access(
            user_roles["user_id"],
            resource_type="admin_panel",
            action="write"
        )
        assert admin_access.allowed is False


class TestAccessibilityCompliance:
    """Test accessibility compliance with WCAG guidelines"""
    
    @pytest.fixture
    def webdriver_instance(self):
        """Setup headless Chrome for accessibility testing"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        yield driver
        driver.quit()
    
    def test_wcag_compliance_automated(self, webdriver_instance):
        """Test WCAG compliance using automated tools"""
        driver = webdriver_instance
        
        # Navigate to application
        driver.get("http://localhost:3000")  # Adjust URL as needed
        
        # Run axe accessibility tests
        axe = Axe(driver)
        axe.inject()
        
        results = axe.run()
        
        # Check for violations
        violations = results["violations"]
        assert len(violations) == 0, f"Accessibility violations found: {violations}"
    
    def test_keyboard_navigation_compliance(self, webdriver_instance):
        """Test keyboard navigation accessibility"""
        driver = webdriver_instance
        driver.get("http://localhost:3000")
        
        # Test tab navigation
        body = driver.find_element(By.TAG_NAME, "body")
        
        # Simulate tab navigation through interactive elements
        for i in range(10):  # Navigate through first 10 focusable elements
            body.send_keys(Keys.TAB)
            
            # Check if focused element is visible and has focus indicator
            focused_element = driver.switch_to.active_element
            
            # Verify focus is visible (element should have focus styles)
            focus_styles = driver.execute_script(
                "return window.getComputedStyle(arguments[0], ':focus')",
                focused_element
            )
            
            # Should have some form of focus indication
            assert (
                focus_styles.get("outline") != "none" or
                focus_styles.get("border") != "none" or
                focus_styles.get("box-shadow") != "none"
            ), f"Element {focused_element.tag_name} lacks focus indication"
    
    def test_screen_reader_compatibility(self, webdriver_instance):
        """Test screen reader compatibility"""
        driver = webdriver_instance
        driver.get("http://localhost:3000")
        
        # Check for proper ARIA labels
        interactive_elements = driver.find_elements(
            By.CSS_SELECTOR,
            "button, input, select, textarea, [role='button'], [role='link']"
        )
        
        for element in interactive_elements:
            # Check for accessible name
            aria_label = element.get_attribute("aria-label")
            aria_labelledby = element.get_attribute("aria-labelledby")
            title = element.get_attribute("title")
            text_content = element.text.strip()
            
            has_accessible_name = any([
                aria_label,
                aria_labelledby,
                title,
                text_content
            ])
            
            assert has_accessible_name, f"Element {element.tag_name} lacks accessible name"
    
    def test_color_contrast_compliance(self, webdriver_instance):
        """Test color contrast compliance"""
        driver = webdriver_instance
        driver.get("http://localhost:3000")
        
        # Get all text elements
        text_elements = driver.find_elements(By.CSS_SELECTOR, "p, h1, h2, h3, h4, h5, h6, span, div, button, a")
        
        for element in text_elements[:10]:  # Test first 10 elements
            if element.text.strip():
                # Get computed styles
                styles = driver.execute_script("""
                    var element = arguments[0];
                    var styles = window.getComputedStyle(element);
                    return {
                        color: styles.color,
                        backgroundColor: styles.backgroundColor,
                        fontSize: styles.fontSize
                    };
                """, element)
                
                # Basic check - ensure text color is not the same as background
                assert styles["color"] != styles["backgroundColor"], \
                    f"Text color matches background color for element: {element.text[:50]}"
    
    def test_form_accessibility_compliance(self, webdriver_instance):
        """Test form accessibility compliance"""
        driver = webdriver_instance
        driver.get("http://localhost:3000")
        
        # Find all form inputs
        form_inputs = driver.find_elements(By.CSS_SELECTOR, "input, select, textarea")
        
        for input_element in form_inputs:
            input_id = input_element.get_attribute("id")
            input_name = input_element.get_attribute("name")
            
            # Check for associated label
            if input_id:
                label = driver.find_elements(By.CSS_SELECTOR, f"label[for='{input_id}']")
                assert len(label) > 0, f"Input with id '{input_id}' has no associated label"
            
            # Check for aria-label or aria-labelledby
            aria_label = input_element.get_attribute("aria-label")
            aria_labelledby = input_element.get_attribute("aria-labelledby")
            
            has_label = aria_label or aria_labelledby or (input_id and len(label) > 0)
            assert has_label, f"Form input lacks proper labeling: {input_name or input_id}"
    
    def test_mobile_accessibility_compliance(self, webdriver_instance):
        """Test mobile accessibility compliance"""
        driver = webdriver_instance
        
        # Set mobile viewport
        driver.set_window_size(375, 667)  # iPhone dimensions
        driver.get("http://localhost:3000")
        
        # Check for touch target sizes
        interactive_elements = driver.find_elements(
            By.CSS_SELECTOR,
            "button, input, select, a, [role='button']"
        )
        
        for element in interactive_elements[:5]:  # Test first 5 elements
            size = element.size
            
            # WCAG recommends minimum 44x44 pixels for touch targets
            assert size["width"] >= 44 or size["height"] >= 44, \
                f"Touch target too small: {size} for element {element.tag_name}"


class TestCompliancePolicyEnforcement:
    """Test compliance policy enforcement across the system"""
    
    @pytest.fixture
    def compliance_service(self):
        return ComplianceMonitoringService()
    
    @pytest.mark.asyncio
    async def test_compliance_policy_enforcement(self, compliance_service):
        """Test comprehensive compliance policy enforcement"""
        # Test data retention policy enforcement
        policy_data = {
            "data_retention": 30,  # days
            "consent_required": True,
            "anonymization_required": True,
            "access_controls": ["RBAC", "MFA", "audit_logging"]
        }
        
        compliant_data = {
            "retention_period": 25,  # compliant
            "consent_obtained": True,  # compliant
            "data_anonymized": True,  # compliant
            "access_controls": ["RBAC", "MFA", "audit_logging"]  # compliant
        }
        
        # Test compliant scenario
        compliance_result = await compliance_service.check_policy_compliance(
            compliant_data, policy_data
        )
        assert compliance_result.compliant is True
        
        # Test non-compliant scenario
        non_compliant_data = {
            "retention_period": 40,  # exceeds policy
            "consent_obtained": False,  # violates policy
            "data_anonymized": False,  # violates policy
            "access_controls": ["RBAC"]  # missing required controls
        }
        
        non_compliance_result = await compliance_service.check_policy_compliance(
            non_compliant_data, policy_data
        )
        assert non_compliance_result.compliant is False
        assert len(non_compliance_result.violations) > 0
    
    @pytest.mark.asyncio
    async def test_automated_policy_monitoring(self, compliance_service):
        """Test automated policy monitoring and alerting"""
        # Setup monitoring for policy violations
        monitoring_config = {
            "policies": ["data_retention", "consent_management", "access_control"],
            "alert_threshold": 5,  # violations per hour
            "escalation_enabled": True
        }
        
        monitoring_result = await compliance_service.setup_policy_monitoring(monitoring_config)
        assert monitoring_result.success is True
        
        # Simulate policy violations
        violations = [
            {"policy": "data_retention", "severity": "medium"},
            {"policy": "consent_management", "severity": "high"},
            {"policy": "access_control", "severity": "low"}
        ]
        
        for violation in violations:
            alert_result = await compliance_service.process_policy_violation(violation)
            assert alert_result.alert_triggered is True
            
            if violation["severity"] == "high":
                assert alert_result.escalation_triggered is True


class TestSecurityIntegrationScenarios:
    """Test complex security scenarios across multiple systems"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_security_flow(self):
        """Test complete security flow from authentication to data access"""
        # 1. OAuth authentication
        oauth_server = OAuthServer()
        token_result = await oauth_server.generate_access_token("test_client", "test_secret")
        
        # 2. API key validation
        api_service = APIKeyService()
        key_validation = await api_service.validate_api_key(token_result.access_token)
        
        # 3. Permission check
        compliance_service = ComplianceMonitoringService()
        permission_check = await compliance_service.check_data_access_permission(
            user_id=key_validation.user_id,
            resource="sensitive_research_data"
        )
        
        # 4. Audit logging
        audit_result = await compliance_service.create_audit_log({
            "event_type": "data_access",
            "user_id": key_validation.user_id,
            "resource": "sensitive_research_data",
            "timestamp": datetime.now()
        })
        
        # Verify complete flow
        assert token_result.success
        assert key_validation.valid
        assert permission_check.allowed
        assert audit_result.success
    
    @pytest.mark.asyncio
    async def test_security_incident_response(self):
        """Test security incident detection and response"""
        compliance_service = ComplianceMonitoringService()
        
        # Simulate suspicious activity
        suspicious_events = [
            {"event": "multiple_failed_logins", "user_id": "test_user", "count": 10},
            {"event": "unusual_data_access", "user_id": "test_user", "resource": "admin_data"},
            {"event": "off_hours_access", "user_id": "test_user", "time": "03:00:00"}
        ]
        
        for event in suspicious_events:
            incident_result = await compliance_service.detect_security_incident(event)
            
            if incident_result.is_incident:
                # Test incident response
                response_result = await compliance_service.respond_to_incident(incident_result.incident_id)
                assert response_result.actions_taken is not None
                assert "user_notification" in response_result.actions_taken
    
    @pytest.mark.asyncio
    async def test_data_breach_response_compliance(self):
        """Test data breach response and notification compliance"""
        compliance_service = ComplianceMonitoringService()
        
        # Simulate data breach
        breach_data = {
            "breach_type": "unauthorized_access",
            "affected_users": ["user1", "user2", "user3"],
            "data_types": ["personal_info", "research_data"],
            "severity": "high",
            "detected_at": datetime.now()
        }
        
        # Test breach response
        response_result = await compliance_service.handle_data_breach(breach_data)
        
        # Verify compliance requirements
        assert response_result.users_notified is True
        assert response_result.authorities_notified is True
        assert response_result.breach_contained is True
        assert response_result.notification_time <= timedelta(hours=72)  # GDPR requirement


if __name__ == "__main__":
    # Run the security and compliance tests
    pytest.main([__file__, "-v", "--tb=short"])