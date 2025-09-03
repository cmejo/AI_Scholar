#!/usr/bin/env python3
"""
Comprehensive integration test runner for Zotero features.
Designed for both local development and CI/CD pipeline execution.
"""
import os
import sys
import subprocess
import json
import time
import argparse
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('integration_test_runner.log')
    ]
)
logger = logging.getLogger(__name__)


class IntegrationTestRunner:
    """Comprehensive integration test runner."""
    
    def __init__(self, args):
        self.args = args
        self.start_time = datetime.now()
        self.test_results = {
            'start_time': self.start_time.isoformat(),
            'environment': self._get_environment_info(),
            'test_suites': {},
            'summary': {},
            'artifacts': []
        }
        self.failed_tests = []
        self.temp_dir = None
    
    def _get_environment_info(self):
        """Get comprehensive environment information."""
        return {
            'python_version': sys.version,
            'platform': sys.platform,
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total // (1024**3),
            'disk_free_gb': psutil.disk_usage('.').free // (1024**3),
            'environment_type': os.getenv('ENVIRONMENT', 'development'),
            'ci_system': os.getenv('CI', 'false').lower() == 'true',
            'github_actions': os.getenv('GITHUB_ACTIONS', 'false').lower() == 'true',
            'working_directory': os.getcwd(),
            'test_runner_version': '1.0.0'
        }
    
    def setup_test_environment(self):
        """Setup test environment and dependencies."""
        logger.info("Setting up test environment...")
        
        # Create temporary directory for test artifacts
        self.temp_dir = tempfile.mkdtemp(prefix='zotero_integration_tests_')
        logger.info(f"Created temporary directory: {self.temp_dir}")
        
        # Set environment variables
        test_env = {
            'ENVIRONMENT': 'test',
            'TESTING': 'true',
            'DATABASE_URL': f'sqlite:///{self.temp_dir}/test_zotero.db',
            'REDIS_URL': 'redis://localhost:6379/15',  # Use test database
            'LOG_LEVEL': 'DEBUG' if self.args.verbose else 'INFO',
            'PYTHONPATH': os.getcwd()
        }
        
        for key, value in test_env.items():
            os.environ[key] = value
        
        logger.info("Test environment configured")
        return True
    
    def run_test_suite(self, suite_name, test_patterns, markers=None, timeout=3600):
        """Run a specific test suite with comprehensive reporting."""
        logger.info(f"Running test suite: {suite_name}")
        
        # Build pytest command
        cmd = [
            sys.executable, '-m', 'pytest',
            '-c', 'pytest_integration.ini',
            '--verbose',
            '--tb=short',
            '--json-report',
            f'--json-report-file={self.temp_dir}/results_{suite_name}.json',
            '--html', f'{self.temp_dir}/report_{suite_name}.html',
            '--self-contained-html'
        ]
        
        # Add test patterns
        for pattern in test_patterns:
            cmd.append(pattern)
        
        # Add markers
        if markers:
            cmd.extend(['-m', markers])
        
        # Add parallel execution if requested
        if self.args.parallel and not self.args.ci:
            cmd.extend(['-n', str(self.args.workers)])
        
        # Add coverage if requested
        if self.args.coverage:
            cmd.extend([
                '--cov=services.zotero',
                f'--cov-report=html:{self.temp_dir}/coverage_{suite_name}',
                f'--cov-report=xml:{self.temp_dir}/coverage_{suite_name}.xml'
            ])
        
        # Add timeout
        cmd.extend(['--timeout', str(timeout)])
        
        # Execute test suite
        start_time = time.time()
        
        try:
            logger.info(f"Executing command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 60,  # Add buffer to pytest timeout
                cwd=Path(__file__).parent
            )
            
            duration = time.time() - start_time
            
            # Parse JSON report
            json_report_file = f'{self.temp_dir}/results_{suite_name}.json'
            test_data = self._parse_json_report(json_report_file)
            
            # Store results
            suite_result = {
                'name': suite_name,
                'duration': duration,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'test_data': test_data,
                'artifacts': [
                    f'results_{suite_name}.json',
                    f'report_{suite_name}.html'
                ]
            }
            
            if self.args.coverage:
                suite_result['artifacts'].extend([
                    f'coverage_{suite_name}/',
                    f'coverage_{suite_name}.xml'
                ])
            
            self.test_results['test_suites'][suite_name] = suite_result
            
            # Log results
            if result.returncode == 0:
                logger.info(f"✅ {suite_name} PASSED ({duration:.2f}s)")
            else:
                logger.error(f"❌ {suite_name} FAILED ({duration:.2f}s)")
                self.failed_tests.append(suite_name)
                
                if self.args.verbose:
                    logger.error(f"STDOUT:\n{result.stdout}")
                    logger.error(f"STDERR:\n{result.stderr}")
            
            # Print test statistics
            if test_data and 'summary' in test_data:
                summary = test_data['summary']
                logger.info(f"Tests: {summary.get('total', 0)}, "
                          f"Passed: {summary.get('passed', 0)}, "
                          f"Failed: {summary.get('failed', 0)}, "
                          f"Skipped: {summary.get('skipped', 0)}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            logger.error(f"❌ {suite_name} TIMEOUT (exceeded {timeout} seconds)")
            self.failed_tests.append(suite_name)
            return False
            
        except Exception as e:
            logger.error(f"❌ {suite_name} ERROR: {str(e)}")
            self.failed_tests.append(suite_name)
            return False
    
    def _parse_json_report(self, json_file):
        """Parse pytest JSON report."""
        try:
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not parse JSON report {json_file}: {e}")
        return None
    
    def run_integration_tests(self):
        """Run comprehensive integration tests."""
        logger.info("🔄 Running Integration Tests...")
        
        test_suites = [
            {
                'name': 'comprehensive_integration',
                'patterns': ['tests/test_zotero_integration_comprehensive.py'],
                'markers': 'integration',
                'timeout': 1800
            }
        ]
        
        results = []
        for suite in test_suites:
            success = self.run_test_suite(
                suite['name'],
                suite['patterns'],
                suite['markers'],
                suite['timeout']
            )
            results.append(success)
        
        return all(results)
    
    def run_performance_tests(self):
        """Run performance tests."""
        logger.info("🚀 Running Performance Tests...")
        
        test_suites = [
            {
                'name': 'performance_comprehensive',
                'patterns': ['tests/test_zotero_performance_comprehensive.py'],
                'markers': 'performance',
                'timeout': 3600
            }
        ]
        
        results = []
        for suite in test_suites:
            success = self.run_test_suite(
                suite['name'],
                suite['patterns'],
                suite['markers'],
                suite['timeout']
            )
            results.append(success)
        
        return all(results)
    
    def run_stress_tests(self):
        """Run stress tests."""
        logger.info("💪 Running Stress Tests...")
        
        test_suites = [
            {
                'name': 'stress_comprehensive',
                'patterns': ['tests/test_zotero_stress_comprehensive.py'],
                'markers': 'stress',
                'timeout': 7200
            }
        ]
        
        results = []
        for suite in test_suites:
            success = self.run_test_suite(
                suite['name'],
                suite['patterns'],
                suite['markers'],
                suite['timeout']
            )
            results.append(success)
        
        return all(results)
    
    def run_ci_tests(self):
        """Run CI/CD specific tests."""
        logger.info("🔧 Running CI/CD Tests...")
        
        test_suites = [
            {
                'name': 'ci_cd_integration',
                'patterns': ['tests/test_zotero_ci_cd_integration.py'],
                'markers': 'ci',
                'timeout': 1200
            }
        ]
        
        results = []
        for suite in test_suites:
            success = self.run_test_suite(
                suite['name'],
                suite['patterns'],
                suite['markers'],
                suite['timeout']
            )
            results.append(success)
        
        return all(results)
    
    def run_smoke_tests(self):
        """Run smoke tests for basic functionality."""
        logger.info("🔥 Running Smoke Tests...")
        
        test_suites = [
            {
                'name': 'smoke_tests',
                'patterns': [
                    'tests/test_zotero_integration_comprehensive.py::TestZoteroEndToEndWorkflows::test_complete_zotero_connection_workflow',
                    'tests/test_zotero_ci_cd_integration.py::TestZoteroCICDIntegration::test_health_check_endpoints'
                ],
                'markers': 'smoke or ci',
                'timeout': 600
            }
        ]
        
        results = []
        for suite in test_suites:
            success = self.run_test_suite(
                suite['name'],
                suite['patterns'],
                suite['markers'],
                suite['timeout']
            )
            results.append(success)
        
        return all(results)
    
    def run_all_tests(self):
        """Run all test suites."""
        logger.info("🧪 Starting Comprehensive Zotero Integration Test Suite")
        logger.info(f"Environment: {self.test_results['environment']['environment_type']}")
        logger.info(f"CI System: {self.test_results['environment']['ci_system']}")
        logger.info(f"Python: {sys.version.split()[0]}")
        logger.info(f"Platform: {sys.platform}")
        
        all_passed = True
        
        # Run test suites based on arguments
        if self.args.smoke or (self.args.ci and not any([self.args.integration, self.args.performance, self.args.stress])):
            all_passed &= self.run_smoke_tests()
        
        if self.args.integration or self.args.all:
            all_passed &= self.run_integration_tests()
        
        if self.args.performance or self.args.all:
            all_passed &= self.run_performance_tests()
        
        if self.args.stress or self.args.all:
            all_passed &= self.run_stress_tests()
        
        if self.args.ci or self.args.all:
            all_passed &= self.run_ci_tests()
        
        return all_passed
    
    def generate_comprehensive_report(self):
        """Generate comprehensive test report."""
        self.test_results['end_time'] = datetime.now().isoformat()
        self.test_results['total_duration'] = (
            datetime.now() - self.start_time
        ).total_seconds()
        
        # Calculate summary statistics
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        total_errors = 0
        
        for suite_name, suite_data in self.test_results['test_suites'].items():
            if suite_data.get('test_data', {}).get('summary'):
                summary = suite_data['test_data']['summary']
                total_tests += summary.get('total', 0)
                total_passed += summary.get('passed', 0)
                total_failed += summary.get('failed', 0)
                total_skipped += summary.get('skipped', 0)
                total_errors += summary.get('error', 0)
        
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_skipped': total_skipped,
            'total_errors': total_errors,
            'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
            'failed_suites': self.failed_tests,
            'suite_count': len(self.test_results['test_suites'])
        }
        
        # Save detailed report
        report_file = f"zotero_integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = os.path.join(self.temp_dir, report_file)
        
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        # Copy report to current directory
        final_report_path = os.path.join(os.getcwd(), report_file)
        shutil.copy2(report_path, final_report_path)
        
        # Generate summary report
        self._print_comprehensive_summary()
        
        return final_report_path
    
    def _print_comprehensive_summary(self):
        """Print comprehensive summary report."""
        print("\n" + "="*100)
        print("🧪 COMPREHENSIVE ZOTERO INTEGRATION TEST SUMMARY")
        print("="*100)
        
        summary = self.test_results['summary']
        env_info = self.test_results['environment']
        
        print(f"📊 Test Statistics:")
        print(f"   Total Test Suites: {summary['suite_count']}")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['total_passed']} ✅")
        print(f"   Failed: {summary['total_failed']} ❌")
        print(f"   Skipped: {summary['total_skipped']} ⏭️")
        print(f"   Errors: {summary['total_errors']} 💥")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        
        print(f"\n⏱️  Execution Time:")
        print(f"   Total Duration: {self.test_results['total_duration']:.2f} seconds")
        print(f"   Average per Suite: {self.test_results['total_duration'] / summary['suite_count']:.2f} seconds")
        
        print(f"\n🖥️  System Information:")
        print(f"   Environment: {env_info['environment_type']}")
        print(f"   CI System: {'Yes' if env_info['ci_system'] else 'No'}")
        print(f"   Python: {env_info['python_version'].split()[0]}")
        print(f"   Platform: {env_info['platform']}")
        print(f"   CPU Cores: {env_info['cpu_count']}")
        print(f"   Memory: {env_info['memory_total_gb']} GB")
        print(f"   Disk Free: {env_info['disk_free_gb']} GB")
        
        print(f"\n📋 Test Suite Results:")
        for suite_name, suite_data in self.test_results['test_suites'].items():
            status = "✅ PASSED" if suite_data['return_code'] == 0 else "❌ FAILED"
            duration = suite_data['duration']
            
            test_info = ""
            if suite_data.get('test_data', {}).get('summary'):
                ts = suite_data['test_data']['summary']
                test_info = f" ({ts.get('total', 0)} tests, {ts.get('passed', 0)} passed)"
            
            print(f"   {suite_name}: {status} ({duration:.2f}s){test_info}")
        
        if self.failed_tests:
            print(f"\n❌ Failed Test Suites:")
            for failed_test in self.failed_tests:
                print(f"   - {failed_test}")
        
        print(f"\n📁 Artifacts Location:")
        print(f"   Temporary Directory: {self.temp_dir}")
        print(f"   Report Files: {len([f for f in os.listdir(self.temp_dir) if f.endswith(('.json', '.html', '.xml'))])} files")
        
        print("\n" + "="*100)
        
        if summary['total_failed'] == 0 and summary['total_errors'] == 0:
            print("🎉 ALL TESTS PASSED! 🎉")
        else:
            print(f"⚠️  {summary['total_failed'] + summary['total_errors']} TESTS FAILED OR HAD ERRORS")
        
        print("="*100)
    
    def cleanup(self):
        """Clean up test environment and artifacts."""
        if not self.args.keep_artifacts and self.temp_dir:
            try:
                # Copy important artifacts before cleanup
                important_files = ['*.json', '*.html', '*.xml']
                for pattern in important_files:
                    for file_path in Path(self.temp_dir).glob(pattern):
                        if file_path.is_file():
                            shutil.copy2(file_path, os.getcwd())
                
                # Remove temporary directory
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Could not clean up temporary directory: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Zotero Integration Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python run_comprehensive_integration_tests.py --all
  
  # Run only integration tests
  python run_comprehensive_integration_tests.py --integration
  
  # Run CI/CD tests with coverage
  python run_comprehensive_integration_tests.py --ci --coverage
  
  # Run smoke tests for quick validation
  python run_comprehensive_integration_tests.py --smoke
  
  # Run performance tests with parallel execution
  python run_comprehensive_integration_tests.py --performance --parallel
        """
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
    parser.add_argument('--smoke', action='store_true',
                       help='Run smoke tests (quick validation)')
    
    # Execution options
    parser.add_argument('--parallel', action='store_true',
                       help='Run tests in parallel (not recommended for CI)')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of parallel workers (default: 4)')
    parser.add_argument('--coverage', action='store_true',
                       help='Generate coverage reports')
    parser.add_argument('--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('--keep-artifacts', action='store_true',
                       help='Keep test artifacts after completion')
    
    # Environment options
    parser.add_argument('--timeout', type=int, default=3600,
                       help='Global timeout for test execution (default: 3600s)')
    
    args = parser.parse_args()
    
    # Set default to smoke tests if no specific tests selected
    if not any([args.all, args.integration, args.performance, args.stress, args.ci, args.smoke]):
        args.smoke = True
        logger.info("No specific test suite selected, running smoke tests")
    
    # Create test runner
    runner = IntegrationTestRunner(args)
    
    try:
        # Setup test environment
        if not runner.setup_test_environment():
            logger.error("Failed to setup test environment")
            sys.exit(1)
        
        # Run tests
        success = runner.run_all_tests()
        
        # Generate comprehensive report
        report_file = runner.generate_comprehensive_report()
        logger.info(f"📄 Comprehensive report saved to: {report_file}")
        
        # Cleanup
        runner.cleanup()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.warning("⚠️  Test execution interrupted by user")
        runner.cleanup()
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"❌ Test execution failed: {str(e)}")
        runner.cleanup()
        sys.exit(1)


if __name__ == '__main__':
    main()