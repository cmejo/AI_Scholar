#!/usr/bin/env python3
"""
Comprehensive test runner for backend service restoration testing suite
Runs all service manager, conditional importer, and endpoint tests
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=False)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED (exit code: {e.returncode})")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run comprehensive backend tests")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--performance", action="store_true", help="Run only performance tests")
    parser.add_argument("--service-manager", action="store_true", help="Run only service manager tests")
    parser.add_argument("--conditional-importer", action="store_true", help="Run only conditional importer tests")
    parser.add_argument("--endpoints", action="store_true", help="Run only endpoint tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    
    args = parser.parse_args()
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Base pytest command
    pytest_cmd = "python -m pytest"
    
    # Add verbose flag if requested
    if args.verbose:
        pytest_cmd += " -v"
    
    # Add parallel execution if requested
    if args.parallel:
        pytest_cmd += " -n auto"
    
    # Add coverage if requested
    if args.coverage:
        pytest_cmd += " --cov=core --cov=api --cov-report=html --cov-report=term-missing"
    
    # Test categories and their files
    test_categories = {
        "service_manager": [
            "tests/test_service_manager.py",
            "tests/test_service_integration.py",
            "tests/test_service_dependency_validation.py"
        ],
        "conditional_importer": [
            "tests/test_conditional_importer.py"
        ],
        "endpoints": [
            "tests/test_advanced_endpoints.py",
            "tests/test_endpoint_validation.py",
            "tests/test_endpoint_performance.py",
            "tests/test_endpoint_automation.py",
            "tests/test_endpoint_load_testing.py"
        ]
    }
    
    # Test markers
    test_markers = {
        "unit": "-m unit",
        "integration": "-m integration", 
        "performance": "-m performance"
    }
    
    results = []
    
    # Determine which tests to run
    if args.service_manager:
        test_files = test_categories["service_manager"]
        description = "Service Manager Tests"
    elif args.conditional_importer:
        test_files = test_categories["conditional_importer"]
        description = "Conditional Importer Tests"
    elif args.endpoints:
        test_files = test_categories["endpoints"]
        description = "Endpoint Tests"
    else:
        # Run all tests
        test_files = []
        for category_files in test_categories.values():
            test_files.extend(category_files)
        description = "All Comprehensive Tests"
    
    # Add marker filters
    marker_filter = ""
    if args.unit:
        marker_filter = test_markers["unit"]
        description += " (Unit Tests Only)"
    elif args.integration:
        marker_filter = test_markers["integration"]
        description += " (Integration Tests Only)"
    elif args.performance:
        marker_filter = test_markers["performance"]
        description += " (Performance Tests Only)"
    
    # Build final command
    test_files_str = " ".join(test_files)
    final_command = f"{pytest_cmd} {marker_filter} {test_files_str}".strip()
    
    # Run the tests
    success = run_command(final_command, description)
    results.append((description, success))
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{description}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} test suites passed")
    
    if failed_tests > 0:
        print(f"\n⚠️  {failed_tests} test suite(s) failed!")
        sys.exit(1)
    else:
        print(f"\n🎉 All test suites passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()