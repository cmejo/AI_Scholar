#!/usr/bin/env python3
"""
Comprehensive test runner for Zotero integration tests.
Runs all integration, performance, and stress tests with reporting.
"""
import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
import argparse
import psutil


class ZoteroTestRunner:
    """Test runner for Zotero integration tests."""
    
    def __init__(self, args):
        self.args = args
        self.test_results = {
            'start_time': datetime.now().isoformat(),
            'test_suites': {},
            'summary': {},
            'system_info': self._get_system_info()
        }
        self.failed_tests = []
    
    def _get_system_info(self):
        """Get system information for test reporting."""
        return {
            'python_version': sys.version,
            'platform': sys.platform,
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total // (1024**3),  # GB
            'disk_free': psutil.disk_usage('.').free // (1024**3),  # GB
            'environment': os.getenv('ENVIRONMENT', 'test')
        }
    
    def run_test_suite(self, test_file, test_markers=None, timeout=3600):
        """Run a specific test suite."""
        print(f"\n{'='*60}")
        print(f"Running test suite: {test_file}")
        print(f"{'='*60}")
        
        cmd = [
            'python', '-m', 'pytest',
            test_file,
            '-v',
            '--tb=short',
            '--json-report',
            f'--json-report-file=test_results_{Path(test_file).stem}.json'
        ]
        
        if test_markers:
            cmd.extend(['-m', test_markers])
        
        if self.args.parallel:
            cmd.extend(['-n', str(self.args.workers)])
        
        if self.args.coverage:
            cmd.extend(['--cov=services.zotero', '--cov-report=html'])
        
        if self.args.verbose:
            cmd.append('-s')
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path(__file__).parent
            )
            
            duration = time.time() - start_time
            
            # Parse JSON report if available
            json_report_file = f'test_results_{Path(test_file).stem}.json'
            test_data = self._parse_json_report(json_report_file)
            
            suite_result = {
                'file': test_file,
                'duration': duration,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'test_data': test_data
            }
            
            self.test_results['test_suites'][Path(test_file).stem] = suite_result
            
            if result.returncode != 0:
                self.failed_tests.append(test_file)
                print(f"❌ FAILED: {test_file}")
                if self.args.verbose:
                    print(f"STDOUT:\n{result.stdout}")
                    print(f"STDERR:\n{result.stderr}")
            else:
                print(f"✅ PASSED: {test_file}")
            
            print(f"Duration: {duration:.2f} seconds")
            
            if test_data:
                print(f"Tests run: {test_data.get('summary', {}).get('total', 0)}")
                print(f"Passed: {test_data.get('summary', {}).get('passed', 0)}")
                print(f"Failed: {test_data.get('summary', {}).get('failed', 0)}")
                print(f"Skipped: {test_data.get('summary', {}).get('skipped', 0)}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print(f"❌ TIMEOUT: {test_file} (exceeded {timeout} seconds)")
            self.failed_tests.append(test_file)
            return False
        
        except Exception as e:
            print(f"❌ ERROR: {test_file} - {str(e)}")
            self.failed_tests.append(test_file)
            return False
    
    def _parse_json_report(self, json_file):
        """Parse pytest JSON report."""
        try:
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not parse JSON report {json_file}: {e}")
        return None
    
    def run_integration_tests(self):
        """Run integration tests."""
        print("\n🔄 Running Integration Tests...")
        
        integration_tests = [
            'tests/test_zotero_integration_comprehensive.py',
            'tests/test_zotero_ci_cd_integration.py'
        ]
        
        results = []
        for test_file in integration_tests:
            if os.path.exists(test_file):
                results.append(self.run_test_suite(test_file, 'integration', timeout=1800))
            else:
                print(f"⚠️  Test file not found: {test_file}")
        
        return all(results)
    
    def run_performance_tests(self):
        """Run performance tests."""
        print("\n🚀 Running Performance Tests...")
        
        performance_tests = [
            'tests/test_zotero_performance_comprehensive.py'
        ]
        
        results = []
        for test_file in performance_tests:
            if os.path.exists(test_file):
                results.append(self.run_test_suite(test_file, 'performance', timeout=3600))
            else:
                print(f"⚠️  Test file not found: {test_file}")
        
        return all(results)
    
    def run_stress_tests(self):
        """Run stress tests."""
        print("\n💪 Running Stress Tests...")
        
        stress_tests = [
            'tests/test_zotero_stress_comprehensive.py'
        ]
        
        results = []
        for test_file in stress_tests:
            if os.path.exists(test_file):
                results.append(self.run_test_suite(test_file, 'stress', timeout=7200))
            else:
                print(f"⚠️  Test file not found: {test_file}")
        
        return all(results)
    
    def run_ci_tests(self):
        """Run CI/CD tests."""
        print("\n🔧 Running CI/CD Tests...")
        
        ci_tests = [
            'tests/test_zotero_ci_cd_integration.py'
        ]
        
        results = []
        for test_file in ci_tests:
            if os.path.exists(test_file):
                results.append(self.run_test_suite(test_file, 'ci', timeout=1200))
            else:
                print(f"⚠️  Test file not found: {test_file}")
        
        return all(results)
    
    def run_all_tests(self):
        """Run all test suites."""
        print("🧪 Starting Comprehensive Zotero Integration Test Suite")
        print(f"Environment: {self.test_results['system_info']['environment']}")
        print(f"Python: {sys.version.split()[0]}")
        print(f"Platform: {sys.platform}")
        
        all_passed = True
        
        if self.args.integration or self.args.all:
            all_passed &= self.run_integration_tests()
        
        if self.args.performance or self.args.all:
            all_passed &= self.run_performance_tests()
        
        if self.args.stress or self.args.all:
            all_passed &= self.run_stress_tests()
        
        if self.args.ci or self.args.all:
            all_passed &= self.run_ci_tests()
        
        return all_passed
    
    def generate_report(self):
        """Generate comprehensive test report."""
        self.test_results['end_time'] = datetime.now().isoformat()
        self.test_results['total_duration'] = (
            datetime.fromisoformat(self.test_results['end_time']) -
            datetime.fromisoformat(self.test_results['start_time'])
        ).total_seconds()
        
        # Calculate summary statistics
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        
        for suite_name, suite_data in self.test_results['test_suites'].items():
            if suite_data.get('test_data', {}).get('summary'):
                summary = suite_data['test_data']['summary']
                total_tests += summary.get('total', 0)
                total_passed += summary.get('passed', 0)
                total_failed += summary.get('failed', 0)
                total_skipped += summary.get('skipped', 0)
        
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_skipped': total_skipped,
            'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
            'failed_suites': self.failed_tests
        }
        
        # Save detailed report
        report_file = f"zotero_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        # Generate summary report
        self._print_summary_report()
        
        return report_file
    
    def _print_summary_report(self):
        """Print summary report to console."""
        print("\n" + "="*80)
        print("🧪 ZOTERO INTEGRATION TEST SUMMARY")
        print("="*80)
        
        summary = self.test_results['summary']
        
        print(f"📊 Test Statistics:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['total_passed']} ✅")
        print(f"   Failed: {summary['total_failed']} ❌")
        print(f"   Skipped: {summary['total_skipped']} ⏭️")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        
        print(f"\n⏱️  Execution Time:")
        print(f"   Total Duration: {self.test_results['total_duration']:.2f} seconds")
        
        print(f"\n🖥️  System Information:")
        sys_info = self.test_results['system_info']
        print(f"   Environment: {sys_info['environment']}")
        print(f"   Python: {sys_info['python_version'].split()[0]}")
        print(f"   Platform: {sys_info['platform']}")
        print(f"   CPU Cores: {sys_info['cpu_count']}")
        print(f"   Memory: {sys_info['memory_total']} GB")
        
        print(f"\n📋 Test Suite Results:")
        for suite_name, suite_data in self.test_results['test_suites'].items():
            status = "✅ PASSED" if suite_data['return_code'] == 0 else "❌ FAILED"
            duration = suite_data['duration']
            print(f"   {suite_name}: {status} ({duration:.2f}s)")
        
        if self.failed_tests:
            print(f"\n❌ Failed Test Suites:")
            for failed_test in self.failed_tests:
                print(f"   - {failed_test}")
        
        print("\n" + "="*80)
        
        if summary['total_failed'] == 0:
            print("🎉 ALL TESTS PASSED! 🎉")
        else:
            print(f"⚠️  {summary['total_failed']} TESTS FAILED")
        
        print("="*80)
    
    def cleanup(self):
        """Clean up test artifacts."""
        if not self.args.keep_artifacts:
            # Clean up JSON report files
            for json_file in Path('.').glob('test_results_*.json'):
                try:
                    json_file.unlink()
                except Exception:
                    pass
            
            # Clean up coverage files if not requested
            if not self.args.coverage:
                for cov_file in Path('.').glob('.coverage*'):
                    try:
                        cov_file.unlink()
                    except Exception:
                        pass


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Zotero Integration Test Runner"
    )
    
    # Test selection arguments
    parser.add_argument('--all', action='store_true', 
                       help='Run all test suites')
    parser.add_argument('--integration', action='store_true',
                       help='Run integration tests')
    parser.add_argument('--performance', action='store_true',
                       help='Run performance tests')
    parser.add_argument('--stress', action='store_true',
                       help='Run stress tests')
    parser.add_argument('--ci', action='store_true',
                       help='Run CI/CD tests')
    
    # Execution options
    parser.add_argument('--parallel', action='store_true',
                       help='Run tests in parallel')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of parallel workers (default: 4)')
    parser.add_argument('--coverage', action='store_true',
                       help='Generate coverage reports')
    parser.add_argument('--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('--keep-artifacts', action='store_true',
                       help='Keep test artifacts after completion')
    
    # Environment options
    parser.add_argument('--environment', default='test',
                       help='Test environment (default: test)')
    
    args = parser.parse_args()
    
    # Set default to integration tests if no specific tests selected
    if not any([args.all, args.integration, args.performance, args.stress, args.ci]):
        args.integration = True
    
    # Set environment variable
    os.environ['ENVIRONMENT'] = args.environment
    
    # Create test runner
    runner = ZoteroTestRunner(args)
    
    try:
        # Run tests
        success = runner.run_all_tests()
        
        # Generate report
        report_file = runner.generate_report()
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Cleanup
        runner.cleanup()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        runner.cleanup()
        sys.exit(130)
    
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        runner.cleanup()
        sys.exit(1)


if __name__ == '__main__':
    main()