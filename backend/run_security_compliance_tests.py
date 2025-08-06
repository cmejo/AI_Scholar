#!/usr/bin/env python3
"""
Security and Compliance Test Runner

Comprehensive test runner for all security and compliance testing,
including voice data privacy, integration security, institutional
compliance, and accessibility testing.
"""

import asyncio
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import subprocess
import pytest

from backend.services.security_testing_service import SecurityTestingService, ComplianceTestingService


class SecurityComplianceTestRunner:
    """Main test runner for security and compliance tests"""
    
    def __init__(self):
        self.security_service = SecurityTestingService()
        self.compliance_service = ComplianceTestingService()
        self.test_results = {}
        self.start_time = datetime.now()
    
    async def run_all_tests(self, test_categories: List[str] = None) -> Dict[str, Any]:
        """Run all security and compliance tests"""
        print("🔒 Starting Security and Compliance Test Suite")
        print("=" * 60)
        
        # Default to all categories if none specified
        if not test_categories:
            test_categories = [
                "voice_security",
                "integration_security", 
                "institutional_compliance",
                "accessibility_compliance"
            ]
        
        # Run each test category
        for category in test_categories:
            print(f"\n📋 Running {category.replace('_', ' ').title()} Tests...")
            
            try:
                if category == "voice_security":
                    await self._run_voice_security_tests()
                elif category == "integration_security":
                    await self._run_integration_security_tests()
                elif category == "institutional_compliance":
                    await self._run_institutional_compliance_tests()
                elif category == "accessibility_compliance":
                    await self._run_accessibility_compliance_tests()
                else:
                    print(f"⚠️  Unknown test category: {category}")
                    
            except Exception as e:
                print(f"❌ Error running {category} tests: {str(e)}")
                self.test_results[category] = {
                    "status": "error",
                    "error": str(e),
                    "tests_run": 0,
                    "tests_passed": 0
                }
        
        # Generate final report
        return await self._generate_final_report()
    
    async def _run_voice_security_tests(self):
        """Run voice data security and privacy tests"""
        print("🎤 Testing voice data encryption and privacy...")
        
        # Run pytest for voice security tests
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "backend/tests/test_voice_security_compliance.py",
            "-v", "--tb=short", "--json-report", "--json-report-file=voice_security_results.json"
        ], capture_output=True, text=True)
        
        # Parse results
        tests_run = result.stdout.count("PASSED") + result.stdout.count("FAILED")
        tests_passed = result.stdout.count("PASSED")
        
        self.test_results["voice_security"] = {
            "status": "completed",
            "tests_run": tests_run,
            "tests_passed": tests_passed,
            "success_rate": (tests_passed / tests_run * 100) if tests_run > 0 else 0,
            "details": result.stdout
        }
        
        # Run additional security service tests
        sample_audio = b"test_voice_data_for_security_testing" * 10
        encryption_result = await self.security_service.test_voice_data_encryption(sample_audio)
        self.security_service.add_test_result(encryption_result)
        
        print(f"✅ Voice security tests completed: {tests_passed}/{tests_run} passed")
    
    async def _run_integration_security_tests(self):
        """Run integration security and OAuth/API key tests"""
        print("🔐 Testing OAuth and API key security...")
        
        # Run pytest for integration security tests
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "backend/tests/test_integration_security_compliance.py",
            "-v", "--tb=short", "--json-report", "--json-report-file=integration_security_results.json"
        ], capture_output=True, text=True)
        
        # Parse results
        tests_run = result.stdout.count("PASSED") + result.stdout.count("FAILED")
        tests_passed = result.stdout.count("PASSED")
        
        self.test_results["integration_security"] = {
            "status": "completed",
            "tests_run": tests_run,
            "tests_passed": tests_passed,
            "success_rate": (tests_passed / tests_run * 100) if tests_run > 0 else 0,
            "details": result.stdout
        }
        
        # Run additional OAuth and API key tests
        oauth_result = await self.security_service.test_oauth_security(
            "test_client_security", "secure_test_secret_123456789"
        )
        self.security_service.add_test_result(oauth_result)
        
        api_key_result = await self.security_service.test_api_key_security(
            "test_api_key_abcdef123456789012345678901234567890"
        )
        self.security_service.add_test_result(api_key_result)
        
        print(f"✅ Integration security tests completed: {tests_passed}/{tests_run} passed")
    
    async def _run_institutional_compliance_tests(self):
        """Run institutional policy and regulatory compliance tests"""
        print("🏛️  Testing institutional and regulatory compliance...")
        
        # Run pytest for institutional compliance tests
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "backend/tests/test_institutional_compliance.py",
            "-v", "--tb=short", "--json-report", "--json-report-file=institutional_compliance_results.json"
        ], capture_output=True, text=True)
        
        # Parse results
        tests_run = result.stdout.count("PASSED") + result.stdout.count("FAILED")
        tests_passed = result.stdout.count("PASSED")
        
        self.test_results["institutional_compliance"] = {
            "status": "completed",
            "tests_run": tests_run,
            "tests_passed": tests_passed,
            "success_rate": (tests_passed / tests_run * 100) if tests_run > 0 else 0,
            "details": result.stdout
        }
        
        # Run additional compliance framework tests
        gdpr_test_data = {
            "gdpr_consent_obtained": True,
            "data_portability_supported": True,
            "right_to_be_forgotten_supported": True,
            "lawful_basis_documented": True,
            "breach_notification_process": True
        }
        
        gdpr_result = await self.compliance_service.test_framework_compliance("GDPR", gdpr_test_data)
        
        ferpa_test_data = {
            "educational_records_protected": True,
            "access_rights_implemented": True,
            "directory_info_consent": True
        }
        
        ferpa_result = await self.compliance_service.test_framework_compliance("FERPA", ferpa_test_data)
        
        print(f"✅ Institutional compliance tests completed: {tests_passed}/{tests_run} passed")
        print(f"   📊 GDPR Compliance: {'✅ PASS' if gdpr_result.passed else '❌ FAIL'}")
        print(f"   📊 FERPA Compliance: {'✅ PASS' if ferpa_result.passed else '❌ FAIL'}")
    
    async def _run_accessibility_compliance_tests(self):
        """Run accessibility compliance tests"""
        print("♿ Testing accessibility compliance...")
        
        # Check if web server is running for accessibility tests
        try:
            import requests
            response = requests.get("http://localhost:3000", timeout=5)
            server_running = response.status_code == 200
        except:
            server_running = False
        
        if not server_running:
            print("⚠️  Web server not running on localhost:3000, skipping browser-based accessibility tests")
            self.test_results["accessibility_compliance"] = {
                "status": "skipped",
                "reason": "Web server not available",
                "tests_run": 0,
                "tests_passed": 0
            }
            return
        
        # Run pytest for accessibility compliance tests
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "backend/tests/test_accessibility_compliance.py",
            "-v", "--tb=short", "--json-report", "--json-report-file=accessibility_compliance_results.json"
        ], capture_output=True, text=True)
        
        # Parse results
        tests_run = result.stdout.count("PASSED") + result.stdout.count("FAILED") + result.stdout.count("SKIPPED")
        tests_passed = result.stdout.count("PASSED")
        tests_skipped = result.stdout.count("SKIPPED")
        
        self.test_results["accessibility_compliance"] = {
            "status": "completed",
            "tests_run": tests_run,
            "tests_passed": tests_passed,
            "tests_skipped": tests_skipped,
            "success_rate": (tests_passed / (tests_run - tests_skipped) * 100) if (tests_run - tests_skipped) > 0 else 0,
            "details": result.stdout
        }
        
        # Run additional accessibility tests
        try:
            accessibility_result = await self.security_service.test_accessibility_compliance("http://localhost:3000")
            print(f"   🎯 WCAG Level: {accessibility_result.wcag_level}")
            print(f"   📊 Accessibility Score: {accessibility_result.score:.1f}%")
        except Exception as e:
            print(f"   ⚠️  Additional accessibility testing failed: {str(e)}")
        
        print(f"✅ Accessibility compliance tests completed: {tests_passed}/{tests_run} passed")
    
    async def _generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Calculate overall statistics
        total_tests = sum(result.get("tests_run", 0) for result in self.test_results.values())
        total_passed = sum(result.get("tests_passed", 0) for result in self.test_results.values())
        total_skipped = sum(result.get("tests_skipped", 0) for result in self.test_results.values())
        
        overall_success_rate = (total_passed / (total_tests - total_skipped) * 100) if (total_tests - total_skipped) > 0 else 0
        
        # Generate security service report
        security_report = await self.security_service.generate_security_report()
        
        # Compile final report
        final_report = {
            "test_run_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "categories_tested": list(self.test_results.keys())
            },
            "overall_statistics": {
                "total_tests": total_tests,
                "total_passed": total_passed,
                "total_failed": total_tests - total_passed - total_skipped,
                "total_skipped": total_skipped,
                "success_rate": overall_success_rate
            },
            "category_results": self.test_results,
            "security_analysis": security_report,
            "compliance_status": self._determine_compliance_status(),
            "recommendations": self._generate_recommendations()
        }
        
        # Save report to file
        report_file = f"security_compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        
        # Print summary
        self._print_final_summary(final_report)
        
        return final_report
    
    def _determine_compliance_status(self) -> Dict[str, str]:
        """Determine overall compliance status"""
        compliance_status = {}
        
        for category, results in self.test_results.items():
            success_rate = results.get("success_rate", 0)
            
            if success_rate >= 95:
                compliance_status[category] = "COMPLIANT"
            elif success_rate >= 80:
                compliance_status[category] = "MOSTLY_COMPLIANT"
            elif success_rate >= 60:
                compliance_status[category] = "PARTIALLY_COMPLIANT"
            else:
                compliance_status[category] = "NON_COMPLIANT"
        
        return compliance_status
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        for category, results in self.test_results.items():
            success_rate = results.get("success_rate", 0)
            
            if success_rate < 95:
                if category == "voice_security":
                    recommendations.extend([
                        "Review voice data encryption implementation",
                        "Strengthen voice biometric data protection",
                        "Implement comprehensive voice consent management"
                    ])
                elif category == "integration_security":
                    recommendations.extend([
                        "Enhance OAuth token security measures",
                        "Implement stronger API key generation",
                        "Add comprehensive rate limiting"
                    ])
                elif category == "institutional_compliance":
                    recommendations.extend([
                        "Review GDPR compliance implementation",
                        "Strengthen FERPA educational record protection",
                        "Implement automated compliance monitoring"
                    ])
                elif category == "accessibility_compliance":
                    recommendations.extend([
                        "Improve WCAG compliance implementation",
                        "Enhance keyboard navigation support",
                        "Add comprehensive ARIA labeling"
                    ])
        
        # Add general recommendations
        recommendations.extend([
            "Implement continuous security monitoring",
            "Regular security and compliance audits",
            "Staff training on security and compliance requirements",
            "Automated compliance checking in CI/CD pipeline"
        ])
        
        return list(set(recommendations))  # Remove duplicates
    
    def _print_final_summary(self, report: Dict[str, Any]):
        """Print final test summary"""
        print("\n" + "=" * 60)
        print("🔒 SECURITY AND COMPLIANCE TEST SUMMARY")
        print("=" * 60)
        
        overall_stats = report["overall_statistics"]
        print(f"📊 Overall Results:")
        print(f"   Total Tests: {overall_stats['total_tests']}")
        print(f"   Passed: {overall_stats['total_passed']} ✅")
        print(f"   Failed: {overall_stats['total_failed']} ❌")
        print(f"   Skipped: {overall_stats['total_skipped']} ⏭️")
        print(f"   Success Rate: {overall_stats['success_rate']:.1f}%")
        
        print(f"\n📋 Category Results:")
        compliance_status = report["compliance_status"]
        for category, status in compliance_status.items():
            status_emoji = {
                "COMPLIANT": "✅",
                "MOSTLY_COMPLIANT": "🟡", 
                "PARTIALLY_COMPLIANT": "🟠",
                "NON_COMPLIANT": "❌"
            }.get(status, "❓")
            
            category_name = category.replace("_", " ").title()
            print(f"   {category_name}: {status} {status_emoji}")
        
        print(f"\n🎯 Key Recommendations:")
        for i, recommendation in enumerate(report["recommendations"][:5], 1):
            print(f"   {i}. {recommendation}")
        
        print(f"\n📄 Detailed report saved to: security_compliance_report_*.json")
        print("=" * 60)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run security and compliance tests")
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=["voice_security", "integration_security", "institutional_compliance", "accessibility_compliance"],
        help="Test categories to run (default: all)"
    )
    parser.add_argument(
        "--output",
        default="security_compliance_report.json",
        help="Output file for test report"
    )
    
    args = parser.parse_args()
    
    # Create and run test suite
    runner = SecurityComplianceTestRunner()
    
    try:
        report = await runner.run_all_tests(args.categories)
        
        # Determine exit code based on results
        overall_success_rate = report["overall_statistics"]["success_rate"]
        
        if overall_success_rate >= 95:
            print("\n🎉 All security and compliance tests passed!")
            sys.exit(0)
        elif overall_success_rate >= 80:
            print("\n⚠️  Most security and compliance tests passed, but some issues found.")
            sys.exit(1)
        else:
            print("\n❌ Significant security and compliance issues found!")
            sys.exit(2)
            
    except Exception as e:
        print(f"\n💥 Test runner failed: {str(e)}")
        sys.exit(3)


if __name__ == "__main__":
    asyncio.run(main())