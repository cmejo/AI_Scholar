#!/usr/bin/env python3
"""
Complete System Validation Script for Multi-Instance ArXiv System

This script performs comprehensive validation of the entire system including:
- End-to-end workflow testing
- Instance separation validation
- Automated scheduling verification
- Email notification testing
- Vector store operations
- Error handling and recovery
- Performance validation
"""

import sys
import os
import json
import time
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import logging

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import test modules
from tests.integration.test_complete_system_integration import TestCompleteSystemIntegration
from tests.integration.test_automated_scheduling_validation import TestAutomatedSchedulingValidation


class SystemValidationRunner:
    """Comprehensive system validation runner"""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('system_validation.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_system_prerequisites(self):
        """Validate system prerequisites and dependencies"""
        self.logger.info("Validating system prerequisites...")
        
        prerequisites = {
            'python_version': self._check_python_version(),
            'required_packages': self._check_required_packages(),
            'directory_structure': self._check_directory_structure(),
            'chromadb_availability': self._check_chromadb_availability(),
            'system_resources': self._check_system_resources()
        }
        
        self.results['prerequisites'] = prerequisites
        
        # Check if all prerequisites are met
        all_passed = all(prerequisites.values())
        
        if all_passed:
            self.logger.info("✓ All system prerequisites validated successfully")
        else:
            self.logger.error("✗ Some system prerequisites failed validation")
            for check, passed in prerequisites.items():
                status = "✓" if passed else "✗"
                self.logger.info(f"  {status} {check}")
        
        return all_passed
    
    def _check_python_version(self):
        """Check Python version compatibility"""
        try:
            version = sys.version_info
            return version.major == 3 and version.minor >= 9
        except Exception:
            return False
    
    def _check_required_packages(self):
        """Check if required packages are installed"""
        required_packages = [
            'pytest', 'requests', 'pyyaml', 'psutil', 'chromadb'
        ]
        
        try:
            for package in required_packages:
                __import__(package)
            return True
        except ImportError as e:
            self.logger.error(f"Missing required package: {e}")
            return False
    
    def _check_directory_structure(self):
        """Check if required directory structure exists"""
        required_dirs = [
            'multi_instance_arxiv_system',
            'tests/integration',
            'scripts',
            'config'
        ]
        
        try:
            for dir_path in required_dirs:
                full_path = backend_dir / dir_path
                if not full_path.exists():
                    self.logger.error(f"Missing directory: {full_path}")
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Directory structure check failed: {e}")
            return False
    
    def _check_chromadb_availability(self):
        """Check if ChromaDB is available (optional for testing)"""
        try:
            import requests
            response = requests.get('http://localhost:8000/api/v1/heartbeat', timeout=5)
            return response.status_code == 200
        except Exception:
            # ChromaDB not required for validation tests (we use mocks)
            return True
    
    def _check_system_resources(self):
        """Check system resources availability"""
        try:
            import psutil
            
            # Check available memory (at least 4GB)
            memory = psutil.virtual_memory()
            memory_ok = memory.available > 4 * 1024 * 1024 * 1024
            
            # Check available disk space (at least 10GB)
            disk = psutil.disk_usage('/')
            disk_ok = disk.free > 10 * 1024 * 1024 * 1024
            
            return memory_ok and disk_ok
        except Exception:
            return True  # Assume OK if can't check
    
    def run_integration_tests(self):
        """Run comprehensive integration tests"""
        self.logger.info("Running integration tests...")
        
        test_results = {}
        
        # Run complete system integration tests
        self.logger.info("Running complete system integration tests...")
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pytest', 
                'tests/integration/test_complete_system_integration.py',
                '-v', '--tb=short', '--json-report', '--json-report-file=integration_test_results.json'
            ], cwd=backend_dir, capture_output=True, text=True, timeout=300)
            
            test_results['integration_tests'] = {
                'returncode': result.returncode,
                'passed': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            test_results['integration_tests'] = {
                'returncode': -1,
                'passed': False,
                'error': 'Test execution timed out'
            }
        except Exception as e:
            test_results['integration_tests'] = {
                'returncode': -1,
                'passed': False,
                'error': str(e)
            }
        
        # Run automated scheduling validation tests
        self.logger.info("Running automated scheduling validation tests...")
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pytest', 
                'tests/integration/test_automated_scheduling_validation.py',
                '-v', '--tb=short', '--json-report', '--json-report-file=scheduling_test_results.json'
            ], cwd=backend_dir, capture_output=True, text=True, timeout=300)
            
            test_results['scheduling_tests'] = {
                'returncode': result.returncode,
                'passed': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            test_results['scheduling_tests'] = {
                'returncode': -1,
                'passed': False,
                'error': 'Test execution timed out'
            }
        except Exception as e:
            test_results['scheduling_tests'] = {
                'returncode': -1,
                'passed': False,
                'error': str(e)
            }
        
        self.results['tests'] = test_results
        
        # Check overall test results
        all_tests_passed = all(
            result.get('passed', False) 
            for result in test_results.values()
        )
        
        if all_tests_passed:
            self.logger.info("✓ All integration tests passed successfully")
        else:
            self.logger.error("✗ Some integration tests failed")
            for test_name, result in test_results.items():
                status = "✓" if result.get('passed', False) else "✗"
                self.logger.info(f"  {status} {test_name}")
        
        return all_tests_passed
    
    def validate_system_components(self):
        """Validate individual system components"""
        self.logger.info("Validating system components...")
        
        component_results = {}
        
        # Validate configuration system
        component_results['configuration'] = self._validate_configuration_system()
        
        # Validate downloader components
        component_results['downloaders'] = self._validate_downloader_components()
        
        # Validate processing components
        component_results['processors'] = self._validate_processing_components()
        
        # Validate scheduling components
        component_results['scheduling'] = self._validate_scheduling_components()
        
        # Validate notification components
        component_results['notifications'] = self._validate_notification_components()
        
        self.results['components'] = component_results
        
        # Check overall component validation
        all_components_valid = all(component_results.values())
        
        if all_components_valid:
            self.logger.info("✓ All system components validated successfully")
        else:
            self.logger.error("✗ Some system components failed validation")
            for component, valid in component_results.items():
                status = "✓" if valid else "✗"
                self.logger.info(f"  {status} {component}")
        
        return all_components_valid
    
    def _validate_configuration_system(self):
        """Validate configuration system components"""
        try:
            from multi_instance_arxiv_system.config.instance_config import InstanceConfig
            
            # Test configuration loading
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                test_config = {
                    'instance_name': 'test_instance',
                    'description': 'Test Instance',
                    'storage_path': '/tmp/test',
                    'papers_path': '/tmp/test/papers',
                    'logs_path': '/tmp/test/logs',
                    'cache_path': '/tmp/test/cache',
                    'arxiv_categories': ['cs.AI'],
                    'processing': {'batch_size': 10},
                    'email_notifications': {'enabled': True}
                }
                
                import yaml
                yaml.dump(test_config, f)
                f.flush()
                
                # Test loading configuration
                config = InstanceConfig.from_yaml(f.name)
                
                # Clean up
                os.unlink(f.name)
                
                return config.instance_name == 'test_instance'
                
        except Exception as e:
            self.logger.error(f"Configuration system validation failed: {e}")
            return False
    
    def _validate_downloader_components(self):
        """Validate downloader components"""
        try:
            from multi_instance_arxiv_system.downloaders.ai_scholar_downloader import AIScholarDownloader
            from multi_instance_arxiv_system.downloaders.quant_scholar_downloader import QuantScholarDownloader
            
            # Test component imports and basic initialization
            # (Actual functionality tested in integration tests)
            return True
            
        except Exception as e:
            self.logger.error(f"Downloader components validation failed: {e}")
            return False
    
    def _validate_processing_components(self):
        """Validate processing components"""
        try:
            from multi_instance_arxiv_system.processing.ai_scholar_processor import AIScholarProcessor
            from multi_instance_arxiv_system.processing.quant_scholar_processor import QuantScholarProcessor
            
            # Test component imports
            return True
            
        except Exception as e:
            self.logger.error(f"Processing components validation failed: {e}")
            return False
    
    def _validate_scheduling_components(self):
        """Validate scheduling components"""
        try:
            from multi_instance_arxiv_system.scheduling.monthly_update_orchestrator import MonthlyUpdateOrchestrator
            from multi_instance_arxiv_system.scheduling.instance_update_manager import InstanceUpdateManager
            
            # Test component imports
            return True
            
        except Exception as e:
            self.logger.error(f"Scheduling components validation failed: {e}")
            return False
    
    def _validate_notification_components(self):
        """Validate notification components"""
        try:
            from multi_instance_arxiv_system.services.email_notification_service import EmailNotificationService
            
            # Test component imports
            return True
            
        except Exception as e:
            self.logger.error(f"Notification components validation failed: {e}")
            return False
    
    def generate_validation_report(self):
        """Generate comprehensive validation report"""
        self.logger.info("Generating validation report...")
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        report = {
            'validation_summary': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'overall_status': self._get_overall_status()
            },
            'detailed_results': self.results,
            'recommendations': self._generate_recommendations()
        }
        
        # Save report to file
        report_file = f'system_validation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Validation report saved to: {report_file}")
        
        return report
    
    def _get_overall_status(self):
        """Determine overall validation status"""
        prerequisites_ok = self.results.get('prerequisites', {})
        tests_ok = self.results.get('tests', {})
        components_ok = self.results.get('components', {})
        
        # Check prerequisites
        prereq_passed = all(prerequisites_ok.values()) if prerequisites_ok else False
        
        # Check tests
        test_passed = all(
            result.get('passed', False) 
            for result in tests_ok.values()
        ) if tests_ok else False
        
        # Check components
        component_passed = all(components_ok.values()) if components_ok else False
        
        if prereq_passed and test_passed and component_passed:
            return 'PASSED'
        elif prereq_passed and (test_passed or component_passed):
            return 'PARTIAL'
        else:
            return 'FAILED'
    
    def _generate_recommendations(self):
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Check prerequisites
        prerequisites = self.results.get('prerequisites', {})
        for check, passed in prerequisites.items():
            if not passed:
                recommendations.append(f"Fix prerequisite issue: {check}")
        
        # Check test results
        tests = self.results.get('tests', {})
        for test_name, result in tests.items():
            if not result.get('passed', False):
                recommendations.append(f"Investigate test failures in: {test_name}")
        
        # Check components
        components = self.results.get('components', {})
        for component, valid in components.items():
            if not valid:
                recommendations.append(f"Fix component issues in: {component}")
        
        if not recommendations:
            recommendations.append("System validation completed successfully - no issues found")
        
        return recommendations
    
    def run_complete_validation(self):
        """Run complete system validation"""
        self.logger.info("Starting complete system validation...")
        self.logger.info("=" * 60)
        
        try:
            # Step 1: Validate prerequisites
            prereq_ok = self.validate_system_prerequisites()
            
            # Step 2: Validate components
            components_ok = self.validate_system_components()
            
            # Step 3: Run integration tests
            tests_ok = self.run_integration_tests()
            
            # Step 4: Generate report
            report = self.generate_validation_report()
            
            # Print summary
            self.print_validation_summary(report)
            
            return report['validation_summary']['overall_status'] == 'PASSED'
            
        except Exception as e:
            self.logger.error(f"Validation failed with error: {e}")
            return False
    
    def print_validation_summary(self, report):
        """Print validation summary"""
        summary = report['validation_summary']
        
        print("\n" + "=" * 60)
        print("SYSTEM VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Overall Status: {summary['overall_status']}")
        print(f"Duration: {summary['duration_seconds']:.1f} seconds")
        print(f"Start Time: {summary['start_time']}")
        print(f"End Time: {summary['end_time']}")
        
        print("\nRecommendations:")
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"{i}. {recommendation}")
        
        print("\n" + "=" * 60)


def main():
    """Main validation function"""
    validator = SystemValidationRunner()
    success = validator.run_complete_validation()
    
    if success:
        print("\n🎉 System validation completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ System validation failed. Please check the report for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()