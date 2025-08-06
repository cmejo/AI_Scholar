#!/usr/bin/env python3
"""
Test Security and Compliance Implementation

Quick verification script to test the security and compliance
testing implementation without requiring full system setup.
"""

import asyncio
import sys
import json
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from services.security_testing_service import SecurityTestingService, ComplianceTestingService


async def test_voice_data_security():
    """Test voice data security implementation"""
    print("🎤 Testing Voice Data Security...")
    
    security_service = SecurityTestingService()
    
    # Test voice data encryption
    sample_audio = b"test_voice_data_for_security_verification" * 20
    encryption_result = await security_service.test_voice_data_encryption(sample_audio)
    
    print(f"   Encryption Test: {'✅ PASS' if encryption_result.passed else '❌ FAIL'}")
    if not encryption_result.passed:
        print(f"   Issues: {encryption_result.vulnerabilities}")
    
    security_service.add_test_result(encryption_result)
    return encryption_result.passed


async def test_oauth_api_security():
    """Test OAuth and API key security implementation"""
    print("🔐 Testing OAuth and API Key Security...")
    
    security_service = SecurityTestingService()
    
    # Test OAuth security
    oauth_result = await security_service.test_oauth_security(
        "test_client_verification", 
        "secure_test_secret_for_verification_123456789"
    )
    
    print(f"   OAuth Test: {'✅ PASS' if oauth_result.passed else '❌ FAIL'}")
    if not oauth_result.passed:
        print(f"   Issues: {oauth_result.vulnerabilities}")
    
    # Test API key security
    test_api_key = "test_api_key_abcdef123456789012345678901234567890"
    api_key_result = await security_service.test_api_key_security(test_api_key)
    
    print(f"   API Key Test: {'✅ PASS' if api_key_result.passed else '❌ FAIL'}")
    if not api_key_result.passed:
        print(f"   Issues: {api_key_result.vulnerabilities}")
    
    security_service.add_test_result(oauth_result)
    security_service.add_test_result(api_key_result)
    
    return oauth_result.passed and api_key_result.passed


async def test_compliance_frameworks():
    """Test compliance framework implementation"""
    print("🏛️  Testing Compliance Frameworks...")
    
    compliance_service = ComplianceTestingService()
    
    # Test GDPR compliance
    gdpr_test_data = {
        "gdpr_consent_obtained": True,
        "data_portability_supported": True,
        "right_to_be_forgotten_supported": True,
        "lawful_basis_documented": True,
        "breach_notification_process": True
    }
    
    gdpr_result = await compliance_service.test_framework_compliance("GDPR", gdpr_test_data)
    print(f"   GDPR Test: {'✅ PASS' if gdpr_result.passed else '❌ FAIL'}")
    
    # Test FERPA compliance
    ferpa_test_data = {
        "educational_records_protected": True,
        "access_rights_implemented": True,
        "directory_info_consent": True
    }
    
    ferpa_result = await compliance_service.test_framework_compliance("FERPA", ferpa_test_data)
    print(f"   FERPA Test: {'✅ PASS' if ferpa_result.passed else '❌ FAIL'}")
    
    return gdpr_result.passed and ferpa_result.passed


async def test_policy_enforcement():
    """Test policy enforcement implementation"""
    print("📋 Testing Policy Enforcement...")
    
    security_service = SecurityTestingService()
    
    # Test policy compliance
    policy_data = {
        "data_retention": "7_years",
        "consent_required": True,
        "anonymization_required": True,
        "access_controls": ["RBAC", "MFA"]
    }
    
    test_data = {
        "retention_period": "5_years",  # Violates policy
        "consent_obtained": True,
        "data_anonymized": False,  # Violates policy
        "access_controls": ["RBAC"]  # Missing MFA
    }
    
    policy_result = await security_service.test_compliance_policy_enforcement(policy_data, test_data)
    
    # This should fail due to policy violations
    expected_to_fail = not policy_result.passed
    print(f"   Policy Enforcement Test: {'✅ PASS' if expected_to_fail else '❌ FAIL'}")
    
    if policy_result.passed:
        print("   ⚠️  Warning: Policy enforcement should have detected violations")
        return False
    else:
        print(f"   ✅ Correctly detected {len(policy_result.vulnerabilities)} policy violations")
        return True


async def generate_test_report():
    """Generate a test report"""
    print("📊 Generating Test Report...")
    
    security_service = SecurityTestingService()
    
    # Add some test results for report generation
    sample_audio = b"report_test_audio_data" * 10
    encryption_result = await security_service.test_voice_data_encryption(sample_audio)
    security_service.add_test_result(encryption_result)
    
    oauth_result = await security_service.test_oauth_security("report_client", "report_secret_123")
    security_service.add_test_result(oauth_result)
    
    # Generate report
    report = await security_service.generate_security_report()
    
    print(f"   Security Score: {report['security_score']:.1f}%")
    print(f"   Tests Run: {report['total_tests']}")
    print(f"   Tests Passed: {report['passed_tests']}")
    
    # Save report
    report_file = f"test_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"   Report saved to: {report_file}")
    
    return report['security_score'] > 0


async def verify_test_files():
    """Verify that all test files exist and are properly structured"""
    print("📁 Verifying Test Files...")
    
    test_files = [
        "tests/test_security_compliance_comprehensive.py",
        "tests/test_voice_security_compliance.py", 
        "tests/test_integration_security_compliance.py",
        "tests/test_institutional_compliance.py",
        "tests/test_accessibility_compliance.py",
        "services/security_testing_service.py",
        "run_security_compliance_tests.py",
        "security_compliance_config.json"
    ]
    
    missing_files = []
    for test_file in test_files:
        file_path = Path(__file__).parent / test_file
        if not file_path.exists():
            missing_files.append(test_file)
    
    if missing_files:
        print(f"   ❌ Missing files: {missing_files}")
        return False
    else:
        print(f"   ✅ All {len(test_files)} test files present")
        return True


async def main():
    """Main verification function"""
    print("🔒 Security and Compliance Implementation Verification")
    print("=" * 60)
    
    test_results = []
    
    # Run verification tests
    test_results.append(await verify_test_files())
    test_results.append(await test_voice_data_security())
    test_results.append(await test_oauth_api_security())
    test_results.append(await test_compliance_frameworks())
    test_results.append(await test_policy_enforcement())
    test_results.append(await generate_test_report())
    
    # Calculate results
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100
    
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("🎉 Security and compliance implementation verified successfully!")
        return 0
    elif success_rate >= 70:
        print("⚠️  Most tests passed, but some issues need attention.")
        return 1
    else:
        print("❌ Significant issues found in implementation.")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)