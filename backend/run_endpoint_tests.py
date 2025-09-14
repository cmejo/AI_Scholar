#!/usr/bin/env python3
"""
Comprehensive endpoint testing runner for backend service restoration
Runs all endpoint validation, error handling, and performance tests
"""
import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from datetime import datetime


def run_command(command, description, timeout=300):
    """Run a command and return success status with timeout"""
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=False,
            timeout=timeout
        )
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ {description} - PASSED ({duration:.1f}s)")
        return True, duration
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT (>{timeout}s)")
        return False, timeout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED (exit code: {e.returncode})")
        return False, 0


def main():
    parser = argparse.ArgumentParser(description="Run comprehensive endpoint tests")
    parser.add_argument("--validation", action="store_true", help="Run endpoint validation tests")
    parser.add_argument("--performance", action="store_true", help="Run endpoint performance tests")
    parser.add_argument("--load", action="store_true", help="Run endpoint load tests")
    parser.add_argument("--automation", action="store_true", help="Run automated endpoint tests")
    parser.add_argument("--all", action="store_true", help="Run all endpoint tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--timeout", type=int, default=600, help="Test timeout in seconds")
    parser.add_argument("--report", action="store_true", help="Generate detailed test report")
    
    args = parser.parse_args()
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Base pytest command
    pytest_cmd = "python -m pytest"
    
    # Add verbose flag if requested
    if args.verbose:
        pytest_cmd += " -v -s"
    
    # Add parallel execution if requested
    if args.parallel:
        pytest_cmd += " -n auto"
    
    # Add coverage if requested
    if args.coverage:
        pytest_cmd += " --cov=api --cov=core --cov-report=html:htmlcov/endpoint_tests --cov-report=term-missing"
    
    # Test suites configuration
    test_suites = {
        "endpoint_validation": {
            "files": [
                "tests/test_endpoint_validation.py",
                "tests/test_advanced_endpoints.py"
            ],
            "description": "Endpoint Validation Tests",
            "markers": "unit",
            "timeout": 300
        },
        "endpoint_automation": {
            "files": [
                "tests/test_endpoint_automation.py"
            ],
            "description": "Automated Endpoint Tests",
            "markers": "unit",
            "timeout": 400
        },
        "endpoint_performance": {
            "files": [
                "tests/test_endpoint_performance.py"
            ],
            "description": "Endpoint Performance Tests",
            "markers": "performance",
            "timeout": 600
        },
        "endpoint_load": {
            "files": [
                "tests/test_endpoint_load_testing.py"
            ],
            "description": "Endpoint Load Tests",
            "markers": "performance",
            "timeout": 900
        }
    }
    
    # Determine which test suites to run
    suites_to_run = []
    
    if args.all:
        suites_to_run = list(test_suites.keys())
    else:
        if args.validation:
            suites_to_run.append("endpoint_validation")
        if args.automation:
            suites_to_run.append("endpoint_automation")
        if args.performance:
            suites_to_run.append("endpoint_performance")
        if args.load:
            suites_to_run.append("endpoint_load")
    
    # Default to validation and automation if nothing specified
    if not suites_to_run:
        suites_to_run = ["endpoint_validation", "endpoint_automation"]
    
    # Run test suites
    results = []
    total_start_time = time.time()
    
    print(f"🚀 Starting Endpoint Testing Suite")
    print(f"Test suites to run: {', '.join(suites_to_run)}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    for suite_name in suites_to_run:
        suite_config = test_suites[suite_name]
        
        # Build command for this suite
        test_files = " ".join(suite_config["files"])
        markers = f"-m {suite_config['markers']}" if suite_config["markers"] else ""
        timeout = suite_config.get("timeout", args.timeout)
        
        command = f"{pytest_cmd} {markers} {test_files}".strip()
        
        # Run the test suite
        success, duration = run_command(
            command, 
            suite_config["description"],
            timeout
        )
        
        results.append({
            "suite": suite_name,
            "description": suite_config["description"],
            "success": success,
            "duration": duration,
            "files": suite_config["files"]
        })
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Generate summary report
    print(f"\n{'='*80}")
    print("ENDPOINT TESTING SUMMARY REPORT")
    print(f"{'='*80}")
    print(f"Total execution time: {total_duration:.1f}s")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Results by suite
    total_suites = len(results)
    passed_suites = sum(1 for r in results if r["success"])
    failed_suites = total_suites - passed_suites
    
    print(f"\nTest Suite Results:")
    print(f"{'Suite':<25} {'Status':<10} {'Duration':<10} {'Description'}")
    print(f"{'-'*70}")
    
    for result in results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        duration_str = f"{result['duration']:.1f}s"
        print(f"{result['suite']:<25} {status:<10} {duration_str:<10} {result['description']}")
    
    print(f"\nOverall Results:")
    print(f"  Total suites: {total_suites}")
    print(f"  Passed: {passed_suites}")
    print(f"  Failed: {failed_suites}")
    print(f"  Success rate: {(passed_suites/total_suites)*100:.1f}%")
    
    # Detailed failure analysis
    if failed_suites > 0:
        print(f"\n❌ Failed Test Suites:")
        for result in results:
            if not result["success"]:
                print(f"  - {result['suite']}: {result['description']}")
                print(f"    Files: {', '.join(result['files'])}")
    
    # Performance summary (if performance tests were run)
    performance_suites = [r for r in results if "performance" in r["suite"] or "load" in r["suite"]]
    if performance_suites:
        print(f"\n📊 Performance Test Summary:")
        total_perf_duration = sum(r["duration"] for r in performance_suites)
        passed_perf_suites = sum(1 for r in performance_suites if r["success"])
        
        print(f"  Performance test duration: {total_perf_duration:.1f}s")
        print(f"  Performance suites passed: {passed_perf_suites}/{len(performance_suites)}")
    
    # Coverage report location
    if args.coverage:
        print(f"\n📈 Coverage Report:")
        print(f"  HTML report: htmlcov/endpoint_tests/index.html")
        print(f"  Terminal report: shown above")
    
    # Generate detailed report file if requested
    if args.report:
        report_file = f"endpoint_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write("ENDPOINT TESTING DETAILED REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total execution time: {total_duration:.1f}s\n")
            f.write(f"Command line args: {' '.join(sys.argv[1:])}\n\n")
            
            f.write("TEST SUITE RESULTS:\n")
            f.write("-" * 30 + "\n")
            for result in results:
                f.write(f"Suite: {result['suite']}\n")
                f.write(f"Description: {result['description']}\n")
                f.write(f"Status: {'PASSED' if result['success'] else 'FAILED'}\n")
                f.write(f"Duration: {result['duration']:.1f}s\n")
                f.write(f"Files: {', '.join(result['files'])}\n\n")
            
            f.write(f"SUMMARY:\n")
            f.write(f"Total suites: {total_suites}\n")
            f.write(f"Passed: {passed_suites}\n")
            f.write(f"Failed: {failed_suites}\n")
            f.write(f"Success rate: {(passed_suites/total_suites)*100:.1f}%\n")
        
        print(f"\n📄 Detailed report saved: {report_file}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if failed_suites > 0:
        print(f"  - Review failed test suites and fix issues")
        print(f"  - Run individual test files for detailed error analysis")
        print(f"  - Check service mocking and endpoint implementations")
    
    if not args.coverage:
        print(f"  - Run with --coverage to analyze test coverage")
    
    if not args.performance and not args.load:
        print(f"  - Run performance tests with --performance --load")
    
    print(f"  - Use --verbose for detailed test output")
    print(f"  - Use --parallel for faster execution")
    
    # Exit with appropriate code
    if failed_suites > 0:
        print(f"\n🔴 Endpoint testing completed with failures!")
        sys.exit(1)
    else:
        print(f"\n🟢 All endpoint tests passed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()