"""
Institutional Policy and Regulatory Compliance Tests

Tests for institutional policy enforcement, regulatory compliance,
and governance requirements.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

from backend.services.compliance_monitoring_service import ComplianceMonitoringService
from backend.services.institutional_role_management_service import InstitutionalRoleManagementService
from backend.services.security_testing_service import ComplianceTestingService


class TestGDPRCompliance:
    """Test GDPR (General Data Protection Regulation) compliance"""
    
    @pytest.fixture
    def compliance_service(self):
        return ComplianceMonitoringService()
    
    @pytest.fixture
    def compliance_testing_service(self):
        return ComplianceTestingService()
    
    @pytest.mark.asyncio
    async def test_gdpr_consent_management(self, compliance_service):
        """Test GDPR consent management requirements"""
        user_id = "test_user_gdpr_consent"
        
        # Test consent recording
        consent_data = {
            "user_id": user_id,
            "consent_type": "data_processing",
            "consent_given": True,
            "consent_date": datetime.now(),
            "purpose": "research_assistance",
            "data_categories": ["personal_data", "research_data"],
            "lawful_basis": "consent",
            "retention_period": "7_years"
        }
        
        consent_result = await compliance_service.record_gdpr_consent(consent_data)
        assert consent_result.success is True
        assert consent_result.consent_id is not None
        
        # Test consent verification
        verification_result = await compliance_service.verify_gdpr_consent(
            user_id, "data_processing"
        )
        assert verification_result.has_valid_consent is True
        assert verification_result.lawful_basis == "consent"
        
        # Test consent withdrawal
        withdrawal_result = await compliance_service.withdraw_gdpr_consent(
            user_id, "data_processing"
        )
        assert withdrawal_result.success is True
        
        # Verify consent is withdrawn
        post_withdrawal_verification = await compliance_service.verify_gdpr_consent(
            user_id, "data_processing"
        )
        assert post_withdrawal_verification.has_valid_consent is False
    
    @pytest.mark.asyncio
    async def test_gdpr_data_subject_rights(self, compliance_service):
        """Test GDPR data subject rights implementation"""
        user_id = "test_user_gdpr_rights"
        
        # Test right of access (Article 15)
        access_request = await compliance_service.process_data_access_request(user_id)
        assert access_request.success is True
        assert access_request.personal_data is not None
        assert access_request.processing_purposes is not None
        assert access_request.data_recipients is not None
        assert access_request.retention_period is not None
        
        # Test right to rectification (Article 16)
        rectification_data = {
            "user_id": user_id,
            "field": "email",
            "old_value": "old@example.com",
            "new_value": "new@example.com"
        }
        
        rectification_result = await compliance_service.process_data_rectification(rectification_data)
        assert rectification_result.success is True
        assert rectification_result.updated_fields == ["email"]
        
        # Test right to erasure (Article 17) - "Right to be forgotten"
        erasure_result = await compliance_service.process_data_erasure_request(user_id)
        assert erasure_result.success is True
        assert erasure_result.data_deleted is True
        assert erasure_result.deletion_confirmation is not None
        
        # Test right to data portability (Article 20)
        portability_result = await compliance_service.process_data_portability_request(user_id)
        assert portability_result.success is True
        assert portability_result.exported_data is not None
        assert portability_result.export_format in ["JSON", "CSV", "XML"]
    
    @pytest.mark.asyncio
    async def test_gdpr_data_breach_notification(self, compliance_service):
        """Test GDPR data breach notification requirements"""
        breach_data = {
            "breach_id": "breach_001",
            "breach_type": "unauthorized_access",
            "affected_users": ["user1", "user2", "user3"],
            "data_categories": ["personal_data", "research_data"],
            "severity": "high",
            "detected_at": datetime.now(),
            "contained_at": datetime.now() + timedelta(hours=2),
            "root_cause": "security_vulnerability"
        }
        
        # Test breach notification to supervisory authority (Article 33)
        authority_notification = await compliance_service.notify_supervisory_authority(breach_data)
        assert authority_notification.success is True
        assert authority_notification.notification_time <= timedelta(hours=72)
        assert authority_notification.notification_id is not None
        
        # Test breach notification to data subjects (Article 34)
        if breach_data["severity"] == "high":
            subject_notification = await compliance_service.notify_data_subjects(breach_data)
            assert subject_notification.success is True
            assert subject_notification.users_notified == len(breach_data["affected_users"])
    
    @pytest.mark.asyncio
    async def test_gdpr_privacy_by_design(self, compliance_service):
        """Test GDPR privacy by design and by default principles"""
        system_design = {
            "data_minimization": True,
            "purpose_limitation": True,
            "storage_limitation": True,
            "accuracy": True,
            "integrity_confidentiality": True,
            "accountability": True
        }
        
        privacy_assessment = await compliance_service.assess_privacy_by_design(system_design)
        assert privacy_assessment.compliant is True
        assert privacy_assessment.principles_met == 6  # All 6 principles
        
        # Test data protection impact assessment (DPIA)
        dpia_data = {
            "processing_type": "automated_decision_making",
            "data_categories": ["personal_data", "sensitive_data"],
            "processing_scale": "large_scale",
            "risk_level": "high"
        }
        
        dpia_result = await compliance_service.conduct_dpia(dpia_data)
        assert dpia_result.dpia_required is True
        assert dpia_result.risk_assessment is not None
        assert dpia_result.mitigation_measures is not None


class TestFERPACompliance:
    """Test FERPA (Family Educational Rights and Privacy Act) compliance"""
    
    @pytest.fixture
    def compliance_service(self):
        return ComplianceMonitoringService()
    
    @pytest.mark.asyncio
    async def test_ferpa_educational_record_protection(self, compliance_service):
        """Test FERPA educational record protection"""
        student_record = {
            "student_id": "student_123",
            "institution_id": "university_001",
            "record_type": "academic_transcript",
            "data": {
                "grades": [{"course": "CS101", "grade": "A"}],
                "gpa": 3.8,
                "enrollment_status": "active"
            },
            "classification": "educational_record"
        }
        
        # Test record protection
        protection_result = await compliance_service.protect_educational_record(student_record)
        assert protection_result.protected is True
        assert protection_result.access_controls_applied is True
        assert protection_result.encryption_applied is True
        
        # Test unauthorized access prevention
        unauthorized_access_attempt = {
            "requester_id": "external_user_123",
            "requester_role": "external",
            "student_id": student_record["student_id"],
            "record_type": "academic_transcript"
        }
        
        access_result = await compliance_service.check_ferpa_access_rights(unauthorized_access_attempt)
        assert access_result.access_granted is False
        assert access_result.denial_reason == "unauthorized_requester"
    
    @pytest.mark.asyncio
    async def test_ferpa_directory_information_handling(self, compliance_service):
        """Test FERPA directory information handling"""
        directory_info = {
            "student_id": "student_456",
            "name": "John Doe",
            "email": "john.doe@university.edu",
            "major": "Computer Science",
            "enrollment_dates": "2020-2024",
            "classification": "directory_information"
        }
        
        # Test directory information consent
        consent_result = await compliance_service.manage_directory_info_consent(
            student_id=directory_info["student_id"],
            consent_given=True
        )
        assert consent_result.success is True
        
        # Test directory information disclosure
        disclosure_request = {
            "requester": "potential_employer",
            "student_id": directory_info["student_id"],
            "information_requested": ["name", "major", "enrollment_dates"]
        }
        
        disclosure_result = await compliance_service.process_directory_info_disclosure(disclosure_request)
        assert disclosure_result.disclosure_allowed is True
        assert disclosure_result.disclosed_information is not None
        
        # Test opt-out of directory information
        opt_out_result = await compliance_service.manage_directory_info_consent(
            student_id=directory_info["student_id"],
            consent_given=False
        )
        assert opt_out_result.success is True
        
        # Verify disclosure is now denied
        post_opt_out_disclosure = await compliance_service.process_directory_info_disclosure(disclosure_request)
        assert post_opt_out_disclosure.disclosure_allowed is False
    
    @pytest.mark.asyncio
    async def test_ferpa_parent_student_rights(self, compliance_service):
        """Test FERPA parent and student access rights"""
        # Test student access rights (18+ or in postsecondary education)
        adult_student = {
            "student_id": "adult_student_789",
            "age": 20,
            "education_level": "undergraduate",
            "institution_id": "university_001"
        }
        
        student_access_result = await compliance_service.check_ferpa_access_rights({
            "requester_id": adult_student["student_id"],
            "requester_role": "student",
            "student_id": adult_student["student_id"],
            "record_type": "academic_transcript"
        })
        assert student_access_result.access_granted is True
        assert student_access_result.access_type == "student_self_access"
        
        # Test parent access rights (for minor students)
        minor_student = {
            "student_id": "minor_student_101",
            "age": 16,
            "education_level": "high_school",
            "institution_id": "high_school_001"
        }
        
        parent_access_result = await compliance_service.check_ferpa_access_rights({
            "requester_id": "parent_123",
            "requester_role": "parent",
            "student_id": minor_student["student_id"],
            "record_type": "academic_transcript",
            "parent_verification": True
        })
        assert parent_access_result.access_granted is True
        assert parent_access_result.access_type == "parent_access"


class TestInstitutionalPolicyCompliance:
    """Test institutional policy compliance"""
    
    @pytest.fixture
    def compliance_service(self):
        return ComplianceMonitoringService()
    
    @pytest.fixture
    def role_service(self):
        return InstitutionalRoleManagementService()
    
    @pytest.mark.asyncio
    async def test_research_ethics_policy_compliance(self, compliance_service):
        """Test research ethics policy compliance"""
        research_proposal = {
            "proposal_id": "research_001",
            "researcher_id": "researcher_123",
            "institution_id": "university_001",
            "research_type": "human_subjects",
            "data_collection": {
                "personal_data": True,
                "sensitive_data": True,
                "consent_obtained": True,
                "irb_approval": True
            },
            "data_handling": {
                "anonymization": True,
                "encryption": True,
                "retention_period": "5_years",
                "sharing_restrictions": True
            }
        }
        
        # Test ethics compliance check
        ethics_result = await compliance_service.check_research_ethics_compliance(research_proposal)
        assert ethics_result.compliant is True
        assert ethics_result.irb_approval_verified is True
        assert ethics_result.consent_requirements_met is True
        
        # Test non-compliant proposal
        non_compliant_proposal = research_proposal.copy()
        non_compliant_proposal["data_collection"]["irb_approval"] = False
        non_compliant_proposal["data_handling"]["anonymization"] = False
        
        non_compliant_result = await compliance_service.check_research_ethics_compliance(non_compliant_proposal)
        assert non_compliant_result.compliant is False
        assert len(non_compliant_result.violations) > 0
        assert "irb_approval_missing" in [v.violation_type for v in non_compliant_result.violations]
    
    @pytest.mark.asyncio
    async def test_data_governance_policy_compliance(self, compliance_service):
        """Test data governance policy compliance"""
        data_governance_policy = {
            "policy_id": "data_gov_001",
            "institution_id": "university_001",
            "requirements": {
                "data_classification": True,
                "access_controls": True,
                "audit_logging": True,
                "backup_requirements": True,
                "retention_schedules": True
            }
        }
        
        data_handling_practice = {
            "data_classification": "confidential",
            "access_controls": ["RBAC", "MFA"],
            "audit_logging": True,
            "backup_frequency": "daily",
            "retention_period": "7_years"
        }
        
        # Test governance compliance
        governance_result = await compliance_service.check_data_governance_compliance(
            data_handling_practice, data_governance_policy
        )
        assert governance_result.compliant is True
        assert governance_result.policy_requirements_met == 5
        
        # Test audit trail requirements
        audit_result = await compliance_service.verify_audit_trail_compliance(
            "data_access_event", data_handling_practice
        )
        assert audit_result.audit_trail_complete is True
        assert audit_result.retention_compliant is True
    
    @pytest.mark.asyncio
    async def test_role_based_access_control_compliance(self, role_service):
        """Test role-based access control compliance"""
        # Define institutional roles
        institutional_roles = {
            "student": {
                "permissions": ["read_own_data", "submit_assignments"],
                "restrictions": ["no_admin_access", "no_grade_modification"]
            },
            "faculty": {
                "permissions": ["read_student_data", "grade_assignments", "create_courses"],
                "restrictions": ["no_system_admin", "department_scope_only"]
            },
            "admin": {
                "permissions": ["full_system_access", "user_management", "policy_enforcement"],
                "restrictions": ["audit_logged", "approval_required"]
            }
        }
        
        # Test role assignment compliance
        user_role_assignment = {
            "user_id": "user_123",
            "assigned_roles": ["student"],
            "institution_id": "university_001",
            "department": "computer_science"
        }
        
        role_compliance_result = await role_service.verify_role_assignment_compliance(
            user_role_assignment, institutional_roles
        )
        assert role_compliance_result.compliant is True
        assert role_compliance_result.roles_valid is True
        
        # Test access control enforcement
        access_request = {
            "user_id": "user_123",
            "requested_resource": "student_grades",
            "requested_action": "read",
            "resource_owner": "user_123"
        }
        
        access_result = await role_service.enforce_access_control(access_request, institutional_roles)
        assert access_result.access_granted is True  # Student can read own grades
        
        # Test unauthorized access prevention
        unauthorized_request = {
            "user_id": "user_123",
            "requested_resource": "all_student_grades",
            "requested_action": "read",
            "resource_owner": "other_students"
        }
        
        unauthorized_result = await role_service.enforce_access_control(unauthorized_request, institutional_roles)
        assert unauthorized_result.access_granted is False
        assert unauthorized_result.denial_reason == "insufficient_permissions"
    
    @pytest.mark.asyncio
    async def test_compliance_monitoring_and_reporting(self, compliance_service):
        """Test compliance monitoring and reporting"""
        # Test compliance monitoring setup
        monitoring_config = {
            "institution_id": "university_001",
            "policies_monitored": ["research_ethics", "data_governance", "ferpa", "gdpr"],
            "monitoring_frequency": "daily",
            "alert_thresholds": {
                "policy_violations": 5,
                "access_anomalies": 10,
                "data_breaches": 1
            }
        }
        
        monitoring_result = await compliance_service.setup_compliance_monitoring(monitoring_config)
        assert monitoring_result.success is True
        assert monitoring_result.monitoring_active is True
        
        # Test compliance report generation
        report_request = {
            "institution_id": "university_001",
            "report_period": "monthly",
            "report_types": ["violations", "access_patterns", "policy_effectiveness"],
            "start_date": datetime.now() - timedelta(days=30),
            "end_date": datetime.now()
        }
        
        report_result = await compliance_service.generate_compliance_report(report_request)
        assert report_result.success is True
        assert report_result.report_data is not None
        assert "violations_summary" in report_result.report_data
        assert "compliance_score" in report_result.report_data
        
        # Test automated compliance alerts
        violation_event = {
            "event_type": "policy_violation",
            "policy_id": "research_ethics_001",
            "user_id": "researcher_456",
            "violation_severity": "high",
            "timestamp": datetime.now()
        }
        
        alert_result = await compliance_service.process_compliance_alert(violation_event)
        assert alert_result.alert_triggered is True
        assert alert_result.notification_sent is True
        assert alert_result.escalation_required is True  # High severity


class TestRegulatoryComplianceIntegration:
    """Test integration of multiple regulatory compliance requirements"""
    
    @pytest.fixture
    def compliance_testing_service(self):
        return ComplianceTestingService()
    
    @pytest.mark.asyncio
    async def test_multi_framework_compliance(self, compliance_testing_service):
        """Test compliance with multiple regulatory frameworks simultaneously"""
        compliance_data = {
            "gdpr_consent_obtained": True,
            "ferpa_educational_records_protected": True,
            "data_portability_supported": True,
            "right_to_be_forgotten_supported": True,
            "lawful_basis_documented": True,
            "breach_notification_process": True,
            "access_rights_implemented": True,
            "directory_info_consent": True
        }
        
        # Test GDPR compliance
        gdpr_result = await compliance_testing_service.test_framework_compliance("GDPR", compliance_data)
        assert gdpr_result.passed is True
        
        # Test FERPA compliance
        ferpa_result = await compliance_testing_service.test_framework_compliance("FERPA", compliance_data)
        assert ferpa_result.passed is True
        
        # Test combined compliance score
        combined_score = (len([r for r in [gdpr_result, ferpa_result] if r.passed]) / 2) * 100
        assert combined_score == 100.0  # Both frameworks compliant
    
    @pytest.mark.asyncio
    async def test_compliance_conflict_resolution(self, compliance_testing_service):
        """Test resolution of conflicts between different compliance requirements"""
        conflict_scenario = {
            "gdpr_right_to_erasure": True,  # GDPR requires data deletion
            "ferpa_record_retention": "7_years",  # FERPA requires record retention
            "legal_hold": True,  # Legal requirement to preserve data
            "data_type": "educational_record_with_personal_data"
        }
        
        # Test conflict detection
        conflict_result = await compliance_testing_service.detect_compliance_conflicts(conflict_scenario)
        assert conflict_result.conflicts_detected is True
        assert len(conflict_result.conflicts) > 0
        
        # Test conflict resolution
        resolution_result = await compliance_testing_service.resolve_compliance_conflicts(conflict_scenario)
        assert resolution_result.resolution_found is True
        assert resolution_result.recommended_action is not None
        
        # In this case, legal hold should take precedence
        assert "legal_hold_precedence" in resolution_result.recommended_action
    
    @pytest.mark.asyncio
    async def test_compliance_automation_effectiveness(self, compliance_testing_service):
        """Test effectiveness of automated compliance checking"""
        test_scenarios = [
            {
                "scenario": "gdpr_consent_missing",
                "data": {"gdpr_consent_obtained": False},
                "expected_violation": True
            },
            {
                "scenario": "ferpa_unauthorized_access",
                "data": {"requester_role": "external", "record_type": "educational"},
                "expected_violation": True
            },
            {
                "scenario": "compliant_data_processing",
                "data": {"consent_obtained": True, "lawful_basis": "consent", "purpose_limitation": True},
                "expected_violation": False
            }
        ]
        
        automation_effectiveness = 0
        
        for scenario in test_scenarios:
            result = await compliance_testing_service.test_automated_compliance_check(scenario)
            
            if result.violation_detected == scenario["expected_violation"]:
                automation_effectiveness += 1
        
        effectiveness_rate = (automation_effectiveness / len(test_scenarios)) * 100
        assert effectiveness_rate >= 90.0  # At least 90% effectiveness


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])