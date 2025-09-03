#!/usr/bin/env python3
"""
Integration Testing Suite Runner
Orchestrates all integration testing components
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any
import argparse

# Import all testing components
from integration_testing_suite import IntegrationTestingSuite, IntegrationTestConfig
from api_contract_tester import APIContractTester
from database_integration_tester import DatabaseIntegrationTester, DatabaseConfig
from ubuntu_environment_simulator import UbuntuEnvironmentSimulator, UbuntuEnvironmentConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('integration_test_results/integration_testing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IntegrationTestRunner:
    """Main integration test runner"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.results = {}
        
        # Ensure results directory exists
        os.makedirs("integration_test_results", exist_ok=True)
    
    def run_all_tests(self, test_categories: List[str] = None) -> Dict[str, Any]:
        """Run all integration tests"""
        logger.info("Starting comprehensive integration testing suite")
        
        # Default to all categories if none specified
        if not test_categories:
            test_categories = [
                "end_to_end",
                "api_contracts", 
                "database_integration",
                "ubuntu_simulation"
            ]
        
        # Run each test category
        for category in test_categories:
            logger.info(f"Running {category} tests")
            try:
                if category == "end_to_end":
                    self.results[category] = self._run_end_to_end_tests()
                elif category == "api_contracts":
                    self.results[category] = self._run_api_contract_tests()
                elif category == "database_integration":
                    self.results[category] = self._run_database_integration_tests()
                elif category == "ubuntu_simulation":
                    self.results[category] = self._run_ubuntu_simulation_tests()
                else:
                    logger.warning(f"Unknown test category: {category}")
                    
            except Exception as e:
                logger.error(f"Error running {category} tests: {e}")
                self.results[category] = {
                    "status": "failed",
                    "error": str(e),
                    "summary": {
                        "total_tests": 0,
                        "passed": 0,
                        "failed": 1,
                        "skipped": 0,
                        "success_rate": 0.0
                    }
                }
        
        # Generate comprehensive report
        return self._generate_comprehensive_report()
    
    def _run_end_to_end_tests(self) -> Dict[str, Any]:
        """Run end-to-end integration tests"""
        logger.info("Running end-to-end integration tests")
        
        config = IntegrationTestConfig()
        suite = IntegrationTestingSuite(config)
        
        try:
            report = suite.run_all_tests()
            return {
                "status": "completed",
                "report": report,
                "summary": report.get("summary", {})
            }
        except Exception as e:
            logger.error(f"End-to-end tests failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "summary": {
                    "total_tests": 0,
                    "passed": 0,
                    "failed": 1,
                    "skipped": 0,
                    "success_rate": 0.0
                }
            }
    
    def _run_api_contract_tests(self) -> Dict[str, Any]:
        """Run API contract tests"""
        logger.info("Running API contract tests")
        
        tester = APIContractTester()
        
        try:
            results = tester.test_all_endpoints()
            report = tester.generate_report()
            
            return {
                "status": "completed",
                "report": report,
                "summary": report.get("summary", {})
            }
        except Exception as e:
            logger.error(f"API contract tests failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "summary": {
                    "total_endpoints": 0,
                    "passed": 0,
                    "failed": 1,
                    "skipped": 0,
                    "success_rate": 0.0
                }
            }
    
    def _run_database_integration_tests(self) -> Dict[str, Any]:
        """Run database integration tests"""
        logger.info("Running database integration tests")
        
        config = DatabaseConfig()
        tester = DatabaseIntegrationTester(config)
        
        try:
            results = tester.run_all_tests()
            report = tester.generate_report()
            
            return {
                "status": "completed",
                "report": report,
                "summary": report.get("summary", {})
            }
        except Exception as e:
            logger.error(f"Database integration tests failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "summary": {
                    "total_tests": 0,
                    "passed": 0,
                    "failed": 1,
                    "skipped": 0,
                    "success_rate": 0.0
                }
            }
    
    def _run_ubuntu_simulation_tests(self) -> Dict[str, Any]:
        """Run Ubuntu environment simulation tests"""
        logger.info("Running Ubuntu environment simulation tests")
        
        config = UbuntuEnvironmentConfig()
        simulator = UbuntuEnvironmentSimulator(config)
        
        try:
            results = simulator.run_all_tests()
            report = simulator.generate_report()
            
            return {
                "status": "completed",
                "report": report,
                "summary": report.get("summary", {})
            }
        except Exception as e:
            logger.error(f"Ubuntu simulation tests failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "summary": {
                    "total_tests": 0,
                    "passed": 0,
                    "failed": 1,
                    "skipped": 0,
                    "success_rate": 0.0
                }
            }
    
    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive integration test report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Aggregate statistics
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        
        category_summaries = {}
        
        for category, result in self.results.items():
            summary = result.get("summary", {})
            category_summaries[category] = summary
            
            # Handle different summary formats
            if "total_tests" in summary:
                total_tests += summary.get("total_tests", 0)
                total_passed += summary.get("passed", 0)
                total_failed += summary.get("failed", 0)
                total_skipped += summary.get("skipped", 0)
            elif "total_endpoints" in summary:
                total_tests += summary.get("total_endpoints", 0)
                total_passed += summary.get("passed", 0)
                total_failed += summary.get("failed", 0)
                total_skipped += summary.get("skipped", 0)
        
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Identify critical failures
        critical_failures = []
        for category, result in self.results.items():
            if result.get("status") == "failed":
                critical_failures.append({
                    "category": category,
                    "error": result.get("error", "Unknown error")
                })
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        comprehensive_report = {
            "overall_summary": {
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "skipped": total_skipped,
                "success_rate": overall_success_rate,
                "total_duration": total_duration,
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "categories_tested": list(self.results.keys())
            },
            "category_summaries": category_summaries,
            "detailed_results": self.results,
            "critical_failures": critical_failures,
            "recommendations": recommendations,
            "ubuntu_compatibility": self._assess_ubuntu_compatibility(),
            "requirements_coverage": self._assess_requirements_coverage()
        }
        
        # Save comprehensive report
        report_file = f"integration_test_results/comprehensive_integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(comprehensive_report, f, indent=2)
        
        logger.info(f"Comprehensive integration test report saved to: {report_file}")
        
        return comprehensive_report
    
    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        for category, result in self.results.items():
            summary = result.get("summary", {})
            
            # Check success rates
            success_rate = summary.get("success_rate", 0)
            if success_rate < 80:
                recommendations.append({
                    "category": category,
                    "priority": "high",
                    "issue": f"Low success rate ({success_rate:.1f}%)",
                    "recommendation": f"Review and fix failing tests in {category} category"
                })
            
            # Check for specific issues
            if result.get("status") == "failed":
                recommendations.append({
                    "category": category,
                    "priority": "critical",
                    "issue": "Test suite execution failed",
                    "recommendation": f"Fix critical issues preventing {category} tests from running"
                })
            
            # Ubuntu-specific recommendations
            if category == "ubuntu_simulation":
                if summary.get("failed", 0) > 0:
                    recommendations.append({
                        "category": category,
                        "priority": "high",
                        "issue": "Ubuntu compatibility issues detected",
                        "recommendation": "Review Ubuntu-specific configurations and dependencies"
                    })
        
        return recommendations
    
    def _assess_ubuntu_compatibility(self) -> Dict[str, Any]:
        """Assess overall Ubuntu compatibility"""
        ubuntu_tests = 0
        ubuntu_passed = 0
        ubuntu_issues = []
        
        for category, result in self.results.items():
            if category == "ubuntu_simulation":
                summary = result.get("summary", {})
                ubuntu_tests += summary.get("total_tests", 0)
                ubuntu_passed += summary.get("passed", 0)
                
                # Check for Ubuntu-specific failures
                if "report" in result and "failed_tests" in result["report"]:
                    for failed_test in result["report"]["failed_tests"]:
                        ubuntu_issues.append({
                            "test": failed_test.get("test_name", "unknown"),
                            "message": failed_test.get("message", "unknown error")
                        })
        
        compatibility_score = (ubuntu_passed / ubuntu_tests * 100) if ubuntu_tests > 0 else 0
        
        return {
            "compatibility_score": compatibility_score,
            "ubuntu_tests_run": ubuntu_tests,
            "ubuntu_tests_passed": ubuntu_passed,
            "ubuntu_issues": ubuntu_issues,
            "assessment": self._get_compatibility_assessment(compatibility_score)
        }
    
    def _get_compatibility_assessment(self, score: float) -> str:
        """Get compatibility assessment based on score"""
        if score >= 90:
            return "Excellent Ubuntu compatibility"
        elif score >= 80:
            return "Good Ubuntu compatibility with minor issues"
        elif score >= 70:
            return "Moderate Ubuntu compatibility - some issues need attention"
        elif score >= 50:
            return "Poor Ubuntu compatibility - significant issues detected"
        else:
            return "Critical Ubuntu compatibility issues - major fixes required"
    
    def _assess_requirements_coverage(self) -> Dict[str, Any]:
        """Assess coverage of requirements from the spec"""
        # Map test categories to requirements
        requirement_mapping = {
            "1.1": ["end_to_end", "ubuntu_simulation"],  # Ubuntu deployment compatibility
            "1.2": ["end_to_end", "ubuntu_simulation"],  # Shell script execution
            "1.3": ["end_to_end", "ubuntu_simulation"],  # Package installation
            "3.1": ["database_integration", "ubuntu_simulation"],  # Docker Ubuntu compatibility
            "3.2": ["database_integration", "ubuntu_simulation"],  # Docker-compose compatibility
            "3.3": ["database_integration", "ubuntu_simulation"]   # Deployment script compatibility
        }
        
        covered_requirements = []
        uncovered_requirements = []
        
        for req, categories in requirement_mapping.items():
            requirement_covered = False
            for category in categories:
                if category in self.results:
                    result = self.results[category]
                    summary = result.get("summary", {})
                    success_rate = summary.get("success_rate", 0)
                    if success_rate > 70:  # Consider requirement covered if >70% success
                        requirement_covered = True
                        break
            
            if requirement_covered:
                covered_requirements.append(req)
            else:
                uncovered_requirements.append(req)
        
        coverage_percentage = (len(covered_requirements) / len(requirement_mapping) * 100) if requirement_mapping else 0
        
        return {
            "coverage_percentage": coverage_percentage,
            "covered_requirements": covered_requirements,
            "uncovered_requirements": uncovered_requirements,
            "total_requirements": len(requirement_mapping)
        }
    
    def print_summary(self, report: Dict[str, Any]):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("COMPREHENSIVE INTEGRATION TEST SUMMARY")
        print("="*80)
        
        overall = report["overall_summary"]
        print(f"Total Tests: {overall['total_tests']}")
        print(f"Passed: {overall['passed']}")
        print(f"Failed: {overall['failed']}")
        print(f"Skipped: {overall['skipped']}")
        print(f"Overall Success Rate: {overall['success_rate']:.1f}%")
        print(f"Total Duration: {overall['total_duration']:.2f} seconds")
        print(f"Categories Tested: {', '.join(overall['categories_tested'])}")
        
        # Ubuntu compatibility
        ubuntu_compat = report["ubuntu_compatibility"]
        print(f"\nUbuntu Compatibility Score: {ubuntu_compat['compatibility_score']:.1f}%")
        print(f"Assessment: {ubuntu_compat['assessment']}")
        
        # Requirements coverage
        req_coverage = report["requirements_coverage"]
        print(f"\nRequirements Coverage: {req_coverage['coverage_percentage']:.1f}%")
        print(f"Covered Requirements: {', '.join(req_coverage['covered_requirements'])}")
        if req_coverage['uncovered_requirements']:
            print(f"Uncovered Requirements: {', '.join(req_coverage['uncovered_requirements'])}")
        
        # Category breakdown
        print("\nCATEGORY BREAKDOWN:")
        print("-" * 40)
        for category, summary in report["category_summaries"].items():
            success_rate = summary.get("success_rate", 0)
            total = summary.get("total_tests", summary.get("total_endpoints", 0))
            passed = summary.get("passed", 0)
            print(f"{category}: {passed}/{total} passed ({success_rate:.1f}%)")
        
        # Critical failures
        if report["critical_failures"]:
            print("\nCRITICAL FAILURES:")
            print("-" * 40)
            for failure in report["critical_failures"]:
                print(f"  {failure['category']}: {failure['error']}")
        
        # Recommendations
        if report["recommendations"]:
            print("\nRECOMMENDATIONS:")
            print("-" * 40)
            for rec in report["recommendations"]:
                print(f"  [{rec['priority'].upper()}] {rec['category']}: {rec['recommendation']}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run comprehensive integration testing suite")
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=["end_to_end", "api_contracts", "database_integration", "ubuntu_simulation"],
        help="Test categories to run (default: all)"
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "summary"],
        default="summary",
        help="Output format (default: summary)"
    )
    
    args = parser.parse_args()
    
    runner = IntegrationTestRunner()
    
    try:
        report = runner.run_all_tests(args.categories)
        
        if args.output_format == "json":
            print(json.dumps(report, indent=2))
        else:
            runner.print_summary(report)
        
        # Return appropriate exit code
        overall_success_rate = report["overall_summary"]["success_rate"]
        return 0 if overall_success_rate >= 80 else 1
        
    except Exception as e:
        logger.error(f"Integration testing failed: {e}")
        print(f"ERROR: Integration testing failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)