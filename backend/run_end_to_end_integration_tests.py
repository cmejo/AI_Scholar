#!/usr/bin/env python3
"""
End-to-End Integration Test Runner

This script runs comprehensive end-to-end integration testing as specified in task 8.2:
- Test all endpoints with real service dependencies
- Validate data flow between services and endpoints  
- Perform load testing and performance validation

Requirements covered:
- 5.3: Incremental Testing and Validation
- 2.1: Endpoint Functionality Restoration
- 2.2: Error Handling and Monitoring
"""

import sys
import os
import argparse
import json
import time
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from tests.test_end_to_end_integration import (
        run_integration_tests,
        run_quick_integration_test,
        run_full_integration_test,
        EndToEndIntegrationTester
    )
except ImportError as e:
    print(f"Error importing test modules: {e}")
    sys.exit(1)


def save_test_results(results: dict, filename: str = None):
    """Save test results to JSON file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"end_to_end_integration_test_results_{timestamp}.json"
    
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    try:
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nTest results saved to: {filepath}")
    except Exception as e:
        print(f"Error saving test results: {e}")


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(
        description="Run comprehensive end-to-end integration tests"
    )
    parser.add_argument(
        "--mode",
        choices=["quick", "full", "custom"],
        default="quick",
        help="Test mode: quick (no stress test), full (with stress test), custom (configurable)"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for the API server (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--save-results",
        action="store_true",
        help="Save test results to JSON file"
    )
    parser.add_argument(
        "--output-file",
        help="Custom output filename for test results"
    )
    parser.add_argument(
        "--load-duration",
        type=int,
        default=30,
        help="Duration for load testing in seconds (default: 30)"
    )
    parser.add_argument(
        "--concurrent-requests",
        type=int,
        default=5,
        help="Number of concurrent requests for load testing (default: 5)"
    )
    parser.add_argument(
        "--stress-max-concurrent",
        type=int,
        default=15,
        help="Maximum concurrent requests for stress testing (default: 15)"
    )
    
    args = parser.parse_args()
    
    print("="*100)
    print("END-TO-END INTEGRATION TEST RUNNER")
    print("="*100)
    print(f"Mode: {args.mode}")
    print(f"Base URL: {args.base_url}")
    print(f"Load Test Duration: {args.load_duration}s")
    print(f"Concurrent Requests: {args.concurrent_requests}")
    if args.mode in ["full", "custom"]:
        print(f"Stress Test Max Concurrent: {args.stress_max_concurrent}")
    print("="*100)
    
    # Check if server is accessible
    print("Checking server accessibility...")
    try:
        import requests
        response = requests.get(f"{args.base_url}/health", timeout=10)
        if response.status_code == 200:
            print(f"✓ Server is accessible at {args.base_url}")
        else:
            print(f"⚠ Server responded with status {response.status_code}")
    except Exception as e:
        print(f"✗ Server is not accessible: {e}")
        print("Please ensure the backend server is running before running tests.")
        sys.exit(1)
    
    # Run tests based on mode
    start_time = time.time()
    
    try:
        if args.mode == "quick":
            print("\nRunning quick integration tests...")
            results = run_quick_integration_test()
            
        elif args.mode == "full":
            print("\nRunning full integration tests with stress testing...")
            results = run_full_integration_test()
            
        elif args.mode == "custom":
            print("\nRunning custom integration tests...")
            tester = EndToEndIntegrationTester(base_url=args.base_url)
            
            # Override load testing parameters
            original_method = tester.perform_load_testing
            def custom_load_testing(duration=None, concurrent_requests=None):
                return original_method(
                    duration=duration or args.load_duration,
                    concurrent_requests=concurrent_requests or args.concurrent_requests
                )
            tester.perform_load_testing = custom_load_testing
            
            # Override stress testing parameters
            original_stress_method = tester.perform_stress_testing
            def custom_stress_testing(max_concurrent=None, step_duration=10):
                return original_stress_method(
                    max_concurrent=max_concurrent or args.stress_max_concurrent,
                    step_duration=step_duration
                )
            tester.perform_stress_testing = custom_stress_testing
            
            results = tester.run_comprehensive_integration_test(include_stress_test=True)
            
            # Print results manually since we used custom tester
            run_integration_tests.__globals__['results'] = results
            print("\nTest completed. Results processed.")
        
        total_time = time.time() - start_time
        
        # Save results if requested
        if args.save_results:
            save_test_results(results, args.output_file)
        
        # Print final summary
        print(f"\n{'='*100}")
        print("FINAL TEST SUMMARY")
        print("="*100)
        print(f"Total Test Time: {total_time:.2f} seconds")
        
        summary = results.get("summary", {})
        test_passed = summary.get("test_passed", False)
        
        print(f"Overall Success Rate: {summary.get('overall_success_rate', 0):.1f}%")
        print(f"Data Flow Success Rate: {summary.get('data_flow_success_rate', 0):.1f}%")
        
        load_assessment = summary.get("load_test_assessment", {})
        print(f"Performance Grade: {load_assessment.get('overall_grade', 'unknown')}")
        
        requirements_met = summary.get("requirements_met", {})
        all_requirements_met = all(requirements_met.values())
        
        print(f"\nRequirements Status:")
        for req_id, met in requirements_met.items():
            status = "✓" if met else "✗"
            req_name = req_id.replace("_", " ").title()
            print(f"  {status} {req_name}")
        
        print(f"\nAll Requirements Met: {'✓ YES' if all_requirements_met else '✗ NO'}")
        print(f"Integration Test Result: {'✓ PASSED' if test_passed else '✗ FAILED'}")
        
        # Exit with appropriate code
        sys.exit(0 if test_passed else 1)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
        
    except Exception as e:
        print(f"\nError running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()