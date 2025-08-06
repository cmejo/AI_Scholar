#!/usr/bin/env python3
"""
Comprehensive Quality Assurance Test Runner
Executes all QA tests and generates detailed reports.
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class QualityAssuranceRunner:
    """Main class for running comprehensive quality assurance tests."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.results = {
            "execution_start": self.start_time.isoformat(),
            "test_suites": {},
            "overall_summary": {},
            "quality_metrics": {}
        }
    
    def run_test_suite(self, suite_name, test_path, markers=None):
        """Run a specific test suite and capture results."""
        print(f"\n{'='*60}")
        print(f"Running {suite_name}")
        print(f"{'='*60}")
        
        cmd = [
            "python", "-m", "pytest",
            test_path,
            "-c", "pytest_qa.ini",
            "--tb=short",
            "-v"
        ]
        
        if markers:
            cmd.extend(["-m", markers])
        
        # Add JSON report for programmatic analysis
        json_report_path = f"test_results_{suite_name.lower().replace(' ', '_')}.json"
        cmd.extend(["--json-report", f"--json-report-file={json_report_path}"])
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            execution_time = time.time() - start_time
            
            # Parse results
            suite_result = {
                "suite_name": suite_name,
                "exit_code": result.returncode,
                "execution_time": execution_time,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
            # Try to load JSON report if available
            if os.path.exists(json_report_path):
                try:
                    with open(json_report_path, 'r') as f:
                        json_data = json.load(f)
                        suite_result["detailed_results"] = json_data
                except Exception as e:
                    print(f"Warning: Could not parse JSON report: {e}")
            
            self.results["test_suites"][suite_name] = suite_result
            
            if result.returncode == 0:
                print(f"✅ {suite_name} - PASSED")
            else:
                print(f"❌ {suite_name} - FAILED")
                print(f"Error output: {result.stderr}")
            
            return suite_result
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {suite_name} - TIMEOUT (30 minutes)")
            suite_result = {
                "suite_name": suite_name,
                "exit_code": -1,
                "execution_time": 1800,
                "error": "Test suite timed out",
                "success": False
            }
            self.results["test_suites"][suite_name] = suite_result
            return suite_result
        
        except Exception as e:
            print(f"💥 {suite_name} - ERROR: {e}")
            suite_result = {
                "suite_name": suite_name,
                "exit_code": -2,
                "execution_time": time.time() - start_time,
                "error": str(e),
                "success": False
            }
            self.results["test_suites"][suite_name] = suite_result
            return suite_result
    
    def run_all_qa_tests(self):
        """Run all quality assurance test suites."""
        
        test_suites = [
            {
                "name": "Mobile App Comprehensive Tests",
                "path": "tests/test_mobile_app_comprehensive.py",
                "markers": "mobile or functional"
            },
            {
                "name": "Voice Interface Comprehensive Tests",
                "path": "tests/test_voice_interface_comprehensive.py",
                "markers": "voice or functional"
            },
            {
                "name": "External Integrations Tests",
                "path": "tests/test_external_integrations_comprehensive.py",
                "markers": "integration"
            },
            {
                "name": "Educational Features Tests",
                "path": "tests/test_educational_features_comprehensive.py",
                "markers": "functional"
            },
            {
                "name": "Performance Tests",
                "path": "tests/test_performance.py",
                "markers": "performance"
            },
            {
                "name": "Security and Compliance Tests",
                "path": "tests/test_security_compliance.py",
                "markers": "security or compliance"
            },
            {
                "name": "Comprehensive QA Orchestrator",
                "path": "tests/test_comprehensive_quality_assurance.py",
                "markers": None
            }
        ]
        
        print("🚀 Starting Comprehensive Quality Assurance Testing")
        print(f"Start time: {self.start_time}")
        print(f"Total test suites: {len(test_suites)}")
        
        successful_suites = 0
        failed_suites = 0
        
        for suite in test_suites:
            result = self.run_test_suite(
                suite["name"],
                suite["path"],
                suite["markers"]
            )
            
            if result["success"]:
                successful_suites += 1
            else:
                failed_suites += 1
        
        # Generate overall summary
        end_time = datetime.now()
        total_execution_time = (end_time - self.start_time).total_seconds()
        
        self.results["execution_end"] = end_time.isoformat()
        self.results["total_execution_time"] = total_execution_time
        self.results["overall_summary"] = {
            "total_suites": len(test_suites),
            "successful_suites": successful_suites,
            "failed_suites": failed_suites,
            "success_rate": successful_suites / len(test_suites),
            "overall_success": failed_suites == 0
        }
        
        return self.results
    
    def generate_qa_report(self):
        """Generate comprehensive QA report."""
        
        print(f"\n{'='*80}")
        print("COMPREHENSIVE QUALITY ASSURANCE REPORT")
        print(f"{'='*80}")
        
        summary = self.results["overall_summary"]
        
        print(f"Execution Time: {self.results['total_execution_time']:.2f} seconds")
        print(f"Total Test Suites: {summary['total_suites']}")
        print(f"Successful Suites: {summary['successful_suites']}")
        print(f"Failed Suites: {summary['failed_suites']}")
        print(f"Success Rate: {summary['success_rate']:.2%}")
        
        if summary["overall_success"]:
            print("\n🎉 ALL QUALITY ASSURANCE TESTS PASSED!")
            print("✅ System is ready for production deployment")
        else:
            print("\n⚠️  SOME QUALITY ASSURANCE TESTS FAILED!")
            print("❌ Review failures before production deployment")
        
        print(f"\n{'='*80}")
        print("DETAILED SUITE RESULTS")
        print(f"{'='*80}")
        
        for suite_name, suite_result in self.results["test_suites"].items():
            status = "✅ PASSED" if suite_result["success"] else "❌ FAILED"
            execution_time = suite_result["execution_time"]
            
            print(f"{suite_name}: {status} ({execution_time:.2f}s)")
            
            if not suite_result["success"] and "error" in suite_result:
                print(f"  Error: {suite_result['error']}")
        
        # Save detailed results to file
        report_filename = f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_filename}")
        
        return summary["overall_success"]
    
    def run_specific_category(self, category):
        """Run tests for a specific category."""
        
        category_tests = {
            "mobile": "tests/test_mobile_app_comprehensive.py",
            "voice": "tests/test_voice_interface_comprehensive.py",
            "integration": "tests/test_external_integrations_comprehensive.py",
            "educational": "tests/test_educational_features_comprehensive.py",
            "performance": "tests/test_performance.py",
            "security": "tests/test_security_compliance.py"
        }
        
        if category not in category_tests:
            print(f"❌ Unknown category: {category}")
            print(f"Available categories: {', '.join(category_tests.keys())}")
            return False
        
        print(f"🎯 Running {category} tests only")
        
        result = self.run_test_suite(
            f"{category.title()} Tests",
            category_tests[category],
            category
        )
        
        return result["success"]


def main():
    """Main entry point for QA test runner."""
    
    runner = QualityAssuranceRunner()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        category = sys.argv[1].lower()
        success = runner.run_specific_category(category)
    else:
        # Run all tests
        runner.run_all_qa_tests()
        success = runner.generate_qa_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()