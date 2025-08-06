#!/usr/bin/env python3
"""
Feature-specific test suite runner for task 9.1 implementation.
This runner executes comprehensive test suites for mobile app, voice interface,
external integrations, and educational features with detailed reporting.
"""

import subprocess
import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import asyncio


class FeatureTestRunner:
    """Comprehensive test runner for feature-specific test suites."""
    
    def __init__(self, verbose: bool = False, coverage: bool = False):
        self.verbose = verbose
        self.coverage = coverage
        self.results = {}
        self.start_time = None
        self.backend_dir = Path(__file__).parent
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def run_command(self, command: str, description: str, timeout: int = 300) -> Dict[str, Any]:
        """Run a command and capture detailed results."""
        self.log(f"Starting: {description}")
        self.log(f"Command: {command}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.backend_dir
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse pytest output for detailed metrics
            test_metrics = self._parse_pytest_output(result.stdout)
            
            result_data = {
                "success": result.returncode == 0,
                "duration": duration,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "metrics": test_metrics,
                "description": description
            }
            
            if result_data["success"]:
                self.log(f"✅ {description} completed successfully in {duration:.2f}s")
                if test_metrics:
                    self.log(f"   Tests: {test_metrics.get('passed', 0)} passed, "
                           f"{test_metrics.get('failed', 0)} failed, "
                           f"{test_metrics.get('skipped', 0)} skipped")
            else:
                self.log(f"❌ {description} failed in {duration:.2f}s", "ERROR")
                if result.stderr:
                    self.log(f"   Error: {result.stderr[:200]}...", "ERROR")
            
            return result_data
            
        except subprocess.TimeoutExpired:
            self.log(f"⏰ {description} timed out after {timeout}s", "ERROR")
            return {
                "success": False,
                "duration": timeout,
                "return_code": -1,
                "stdout": "",
                "stderr": f"Test timed out after {timeout} seconds",
                "metrics": {},
                "description": description
            }
        except Exception as e:
            self.log(f"💥 {description} crashed: {str(e)}", "ERROR")
            return {
                "success": False,
                "duration": 0,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e),
                "metrics": {},
                "description": description
            }
    
    def _parse_pytest_output(self, output: str) -> Dict[str, int]:
        """Parse pytest output to extract test metrics."""
        metrics = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}
        
        lines = output.split('\n')
        for line in lines:
            if "passed" in line and "failed" in line:
                # Look for summary line like "5 passed, 2 failed, 1 skipped"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit() and i + 1 < len(parts):
                        next_part = parts[i + 1]
                        if "passed" in next_part:
                            metrics["passed"] = int(part)
                        elif "failed" in next_part:
                            metrics["failed"] = int(part)
                        elif "skipped" in next_part:
                            metrics["skipped"] = int(part)
                        elif "error" in next_part:
                            metrics["errors"] = int(part)
        
        return metrics
    
    def run_mobile_app_tests(self) -> Dict[str, Any]:
        """Run comprehensive mobile app tests with device simulation."""
        self.log("🔥 Starting Mobile App Test Suite")
        
        # Base command for mobile tests
        cmd = "pytest tests/test_mobile_app_comprehensive.py"
        
        if self.verbose:
            cmd += " -v -s"
        
        if self.coverage:
            cmd += " --cov=services.mobile_sync_service --cov=services.push_notification_service"
        
        # Add markers for specific mobile test categories
        cmd += " -m 'not slow'"  # Skip slow tests by default
        
        result = self.run_command(cmd, "Mobile App Tests")
        
        # Run device simulation tests separately
        device_sim_cmd = "pytest tests/test_mobile_app_comprehensive.py::TestMobileDeviceSimulation"
        if self.verbose:
            device_sim_cmd += " -v -s"
        
        device_result = self.run_command(device_sim_cmd, "Mobile Device Simulation Tests")
        
        # Combine results
        combined_result = {
            "success": result["success"] and device_result["success"],
            "duration": result["duration"] + device_result["duration"],
            "main_tests": result,
            "device_simulation": device_result,
            "total_tests": (result["metrics"].get("passed", 0) + 
                          device_result["metrics"].get("passed", 0)),
            "total_failures": (result["metrics"].get("failed", 0) + 
                             device_result["metrics"].get("failed", 0))
        }
        
        return combined_result
    
    def run_voice_interface_tests(self) -> Dict[str, Any]:
        """Run comprehensive voice interface tests with speech recognition validation."""
        self.log("🎤 Starting Voice Interface Test Suite")
        
        # Base command for voice tests
        cmd = "pytest tests/test_voice_interface_comprehensive.py"
        
        if self.verbose:
            cmd += " -v -s"
        
        if self.coverage:
            cmd += " --cov=services.voice_processing_service --cov=services.voice_nlp_service --cov=services.voice_command_router"
        
        result = self.run_command(cmd, "Voice Interface Tests")
        
        # Run speech recognition accuracy tests separately
        accuracy_cmd = "pytest tests/test_voice_interface_comprehensive.py::TestVoiceSpeechRecognitionAccuracy"
        if self.verbose:
            accuracy_cmd += " -v -s"
        
        accuracy_result = self.run_command(accuracy_cmd, "Speech Recognition Accuracy Tests")
        
        # Combine results
        combined_result = {
            "success": result["success"] and accuracy_result["success"],
            "duration": result["duration"] + accuracy_result["duration"],
            "main_tests": result,
            "accuracy_tests": accuracy_result,
            "total_tests": (result["metrics"].get("passed", 0) + 
                          accuracy_result["metrics"].get("passed", 0)),
            "total_failures": (result["metrics"].get("failed", 0) + 
                             accuracy_result["metrics"].get("failed", 0))
        }
        
        return combined_result
    
    def run_external_integration_tests(self) -> Dict[str, Any]:
        """Run comprehensive external integration tests for APIs and services."""
        self.log("🔗 Starting External Integration Test Suite")
        
        # Base command for integration tests
        cmd = "pytest tests/test_external_integrations_comprehensive.py"
        
        if self.verbose:
            cmd += " -v -s"
        
        if self.coverage:
            cmd += " --cov=services.reference_manager_service --cov=services.academic_database_service --cov=services.note_taking_integration_service --cov=services.writing_tools_service"
        
        result = self.run_command(cmd, "External Integration Tests")
        
        # Run error handling tests separately
        error_cmd = "pytest tests/test_external_integrations_comprehensive.py::TestIntegrationErrorHandling"
        if self.verbose:
            error_cmd += " -v -s"
        
        error_result = self.run_command(error_cmd, "Integration Error Handling Tests")
        
        # Combine results
        combined_result = {
            "success": result["success"] and error_result["success"],
            "duration": result["duration"] + error_result["duration"],
            "main_tests": result,
            "error_handling": error_result,
            "total_tests": (result["metrics"].get("passed", 0) + 
                          error_result["metrics"].get("passed", 0)),
            "total_failures": (result["metrics"].get("failed", 0) + 
                             error_result["metrics"].get("failed", 0))
        }
        
        return combined_result
    
    def run_educational_feature_tests(self) -> Dict[str, Any]:
        """Run comprehensive educational feature tests with learning outcome validation."""
        self.log("🎓 Starting Educational Features Test Suite")
        
        # Base command for educational tests
        cmd = "pytest tests/test_educational_features_comprehensive.py"
        
        if self.verbose:
            cmd += " -v -s"
        
        if self.coverage:
            cmd += " --cov=services.quiz_generation_service --cov=services.spaced_repetition_service --cov=services.learning_progress_service --cov=services.gamification_service"
        
        result = self.run_command(cmd, "Educational Features Tests")
        
        # Run learning outcome validation tests separately
        outcome_cmd = "pytest tests/test_educational_features_comprehensive.py::TestLearningOutcomeValidation"
        if self.verbose:
            outcome_cmd += " -v -s"
        
        outcome_result = self.run_command(outcome_cmd, "Learning Outcome Validation Tests")
        
        # Combine results
        combined_result = {
            "success": result["success"] and outcome_result["success"],
            "duration": result["duration"] + outcome_result["duration"],
            "main_tests": result,
            "outcome_validation": outcome_result,
            "total_tests": (result["metrics"].get("passed", 0) + 
                          outcome_result["metrics"].get("passed", 0)),
            "total_failures": (result["metrics"].get("failed", 0) + 
                             outcome_result["metrics"].get("failed", 0))
        }
        
        return combined_result
    
    def run_all_feature_tests(self) -> Dict[str, Any]:
        """Run all feature-specific test suites."""
        self.log("🚀 Starting Comprehensive Feature Test Suite")
        self.start_time = time.time()
        
        # Run all test suites
        mobile_results = self.run_mobile_app_tests()
        voice_results = self.run_voice_interface_tests()
        integration_results = self.run_external_integration_tests()
        educational_results = self.run_educational_feature_tests()
        
        total_time = time.time() - self.start_time
        
        # Aggregate results
        all_results = {
            "mobile_app": mobile_results,
            "voice_interface": voice_results,
            "external_integrations": integration_results,
            "educational_features": educational_results
        }
        
        # Calculate totals
        total_success = all([
            mobile_results["success"],
            voice_results["success"],
            integration_results["success"],
            educational_results["success"]
        ])
        
        total_tests = sum([
            mobile_results.get("total_tests", 0),
            voice_results.get("total_tests", 0),
            integration_results.get("total_tests", 0),
            educational_results.get("total_tests", 0)
        ])
        
        total_failures = sum([
            mobile_results.get("total_failures", 0),
            voice_results.get("total_failures", 0),
            integration_results.get("total_failures", 0),
            educational_results.get("total_failures", 0)
        ])
        
        summary = {
            "overall_success": total_success,
            "total_duration": total_time,
            "total_tests": total_tests,
            "total_failures": total_failures,
            "success_rate": (total_tests - total_failures) / total_tests if total_tests > 0 else 0,
            "feature_results": all_results
        }
        
        self.results = summary
        return summary
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report."""
        if not self.results:
            return "No test results available."
        
        report = []
        report.append("=" * 80)
        report.append("FEATURE-SPECIFIC TEST SUITE REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Duration: {self.results['total_duration']:.2f} seconds")
        report.append(f"Overall Success: {'✅ PASS' if self.results['overall_success'] else '❌ FAIL'}")
        report.append(f"Total Tests: {self.results['total_tests']}")
        report.append(f"Total Failures: {self.results['total_failures']}")
        report.append(f"Success Rate: {self.results['success_rate']:.1%}")
        report.append("")
        
        # Feature-specific results
        features = [
            ("Mobile App Tests", "mobile_app"),
            ("Voice Interface Tests", "voice_interface"),
            ("External Integration Tests", "external_integrations"),
            ("Educational Feature Tests", "educational_features")
        ]
        
        for feature_name, feature_key in features:
            feature_result = self.results["feature_results"][feature_key]
            status = "✅ PASS" if feature_result["success"] else "❌ FAIL"
            
            report.append(f"{feature_name}: {status}")
            report.append(f"  Duration: {feature_result['duration']:.2f}s")
            report.append(f"  Tests: {feature_result.get('total_tests', 0)}")
            report.append(f"  Failures: {feature_result.get('total_failures', 0)}")
            
            # Add sub-test details if available
            if "main_tests" in feature_result:
                main_metrics = feature_result["main_tests"]["metrics"]
                report.append(f"  Main Tests: {main_metrics.get('passed', 0)} passed, {main_metrics.get('failed', 0)} failed")
            
            report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS:")
        if self.results["total_failures"] > 0:
            report.append("- Review failed tests and fix underlying issues")
            report.append("- Check error logs for specific failure details")
        
        if self.results["success_rate"] < 0.95:
            report.append("- Consider improving test coverage")
            report.append("- Review test quality and reliability")
        
        if self.results["total_duration"] > 600:  # 10 minutes
            report.append("- Consider optimizing slow tests")
            report.append("- Implement parallel test execution")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_report(self, filename: str = None):
        """Save the test report to a file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"feature_test_report_{timestamp}.txt"
        
        report_content = self.generate_report()
        
        with open(filename, 'w') as f:
            f.write(report_content)
        
        self.log(f"📄 Test report saved to: {filename}")
        return filename
    
    def save_json_results(self, filename: str = None):
        """Save detailed results as JSON."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"feature_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        self.log(f"📊 Detailed results saved to: {filename}")
        return filename


def main():
    """Main entry point for the feature test runner."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive feature-specific test suites"
    )
    parser.add_argument(
        "--mobile", action="store_true",
        help="Run mobile app tests only"
    )
    parser.add_argument(
        "--voice", action="store_true",
        help="Run voice interface tests only"
    )
    parser.add_argument(
        "--integrations", action="store_true",
        help="Run external integration tests only"
    )
    parser.add_argument(
        "--educational", action="store_true",
        help="Run educational feature tests only"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Run all feature tests (default)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage", action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--report", action="store_true",
        help="Generate and save test report"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Save detailed results as JSON"
    )
    
    args = parser.parse_args()
    
    # If no specific test is selected, run all
    if not any([args.mobile, args.voice, args.integrations, args.educational]):
        args.all = True
    
    runner = FeatureTestRunner(verbose=args.verbose, coverage=args.coverage)
    
    try:
        if args.all:
            results = runner.run_all_feature_tests()
        else:
            results = {}
            if args.mobile:
                results["mobile_app"] = runner.run_mobile_app_tests()
            if args.voice:
                results["voice_interface"] = runner.run_voice_interface_tests()
            if args.integrations:
                results["external_integrations"] = runner.run_external_integration_tests()
            if args.educational:
                results["educational_features"] = runner.run_educational_feature_tests()
            
            # Create summary for partial runs
            runner.results = {
                "overall_success": all(r["success"] for r in results.values()),
                "total_duration": sum(r["duration"] for r in results.values()),
                "total_tests": sum(r.get("total_tests", 0) for r in results.values()),
                "total_failures": sum(r.get("total_failures", 0) for r in results.values()),
                "feature_results": results
            }
            runner.results["success_rate"] = (
                (runner.results["total_tests"] - runner.results["total_failures"]) / 
                runner.results["total_tests"] if runner.results["total_tests"] > 0 else 0
            )
        
        # Generate and display report
        print("\n" + runner.generate_report())
        
        # Save reports if requested
        if args.report:
            runner.save_report()
        
        if args.json:
            runner.save_json_results()
        
        # Return appropriate exit code
        return 0 if runner.results["overall_success"] else 1
        
    except KeyboardInterrupt:
        runner.log("🛑 Test execution interrupted by user", "WARNING")
        return 130
    except Exception as e:
        runner.log(f"💥 Unexpected error: {str(e)}", "ERROR")
        return 1


if __name__ == "__main__":
    sys.exit(main())