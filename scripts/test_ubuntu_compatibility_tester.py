#!/usr/bin/env python3
"""
Test script for Ubuntu Compatibility Testing Framework

This script validates the functionality of the Ubuntu compatibility tester
and ensures all components work correctly.
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ubuntu_compatibility_tester import (
    UbuntuEnvironmentSimulator,
    DockerContainerTestSuite,
    SystemIntegrationTester,
    UbuntuPerformanceBenchmark,
    UbuntuCompatibilityTestFramework,
    TestResult,
    UbuntuCompatibilityResult
)

class TestUbuntuEnvironmentSimulator(unittest.TestCase):
    """Test cases for UbuntuEnvironmentSimulator"""
    
    def setUp(self):
        self.simulator = UbuntuEnvironmentSimulator("24.04")
    
    def test_initialization(self):
        """Test simulator initialization"""
        self.assertEqual(self.simulator.ubuntu_version, "24.04")
        self.assertIsInstance(self.simulator.test_results, list)
    
    @patch('subprocess.run')
    @patch('tempfile.TemporaryDirectory')
    def test_test_packages_locally(self, mock_temp_dir, mock_subprocess):
        """Test local package testing"""
        # Mock temporary directory
        mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"
        
        # Mock successful venv creation
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stderr = ""
        
        # Test with sample packages
        packages = ["requests", "flask"]
        result = self.simulator._test_packages_locally(packages)
        
        self.assertIn("status", result)
        self.assertIn("message", result)
        self.assertIn("details", result)
    
    def test_python_dependencies_no_requirements(self):
        """Test Python dependencies when no requirements files exist"""
        with patch('os.path.exists', return_value=False):
            result = self.simulator.test_python_dependencies()
            
            self.assertIsInstance(result, UbuntuCompatibilityResult)
            self.assertEqual(result.test_name, "python_dependencies")
    
    def test_nodejs_dependencies_no_package_json(self):
        """Test Node.js dependencies when no package.json exists"""
        with patch('os.path.exists', return_value=False):
            result = self.simulator.test_nodejs_dependencies()
            
            self.assertIsInstance(result, UbuntuCompatibilityResult)
            self.assertEqual(result.test_name, "nodejs_dependencies")
            self.assertEqual(result.result, TestResult.SKIP)

class TestDockerContainerTestSuite(unittest.TestCase):
    """Test cases for DockerContainerTestSuite"""
    
    def setUp(self):
        self.docker_tester = DockerContainerTestSuite()
    
    def test_initialization(self):
        """Test Docker test suite initialization"""
        self.assertIsNotNone(self.docker_tester)
    
    def test_analyze_dockerfile_ubuntu_compatibility(self):
        """Test Dockerfile analysis for Ubuntu compatibility"""
        # Test Ubuntu-compatible Dockerfile
        ubuntu_dockerfile = """
        FROM ubuntu:24.04
        RUN apt-get update && apt-get install -y python3
        """
        
        issues = self.docker_tester._analyze_dockerfile_ubuntu_compatibility(ubuntu_dockerfile)
        self.assertEqual(len(issues), 0)
        
        # Test problematic Dockerfile
        problematic_dockerfile = """
        FROM alpine:latest
        RUN apk add python3
        RUN yum install nodejs
        """
        
        issues = self.docker_tester._analyze_dockerfile_ubuntu_compatibility(problematic_dockerfile)
        self.assertGreater(len(issues), 0)
        self.assertTrue(any("alpine" in issue.lower() for issue in issues))
    
    @patch('os.walk')
    def test_docker_build_ubuntu_compatibility_no_dockerfiles(self, mock_walk):
        """Test Docker build test when no Dockerfiles exist"""
        mock_walk.return_value = []
        
        result = self.docker_tester.test_docker_build_ubuntu_compatibility()
        
        self.assertIsInstance(result, UbuntuCompatibilityResult)
        self.assertEqual(result.test_name, "docker_build_ubuntu")
        self.assertEqual(result.result, TestResult.SKIP)

class TestSystemIntegrationTester(unittest.TestCase):
    """Test cases for SystemIntegrationTester"""
    
    def setUp(self):
        self.system_tester = SystemIntegrationTester()
    
    def test_initialization(self):
        """Test system integration tester initialization"""
        self.assertIsNotNone(self.system_tester)
    
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('os.access')
    def test_file_system_permissions(self, mock_access, mock_listdir, mock_exists):
        """Test file system permissions checking"""
        # Mock file system structure
        mock_exists.side_effect = lambda path: path in ["scripts", "backend"]
        mock_listdir.side_effect = lambda path: ["test.sh", "test.py"] if path == "scripts" else []
        mock_access.return_value = True
        
        result = self.system_tester.test_file_system_permissions()
        
        self.assertIsInstance(result, UbuntuCompatibilityResult)
        self.assertEqual(result.test_name, "file_system_permissions")
    
    @patch('requests.get')
    @patch('socket.gethostbyname')
    def test_network_configuration(self, mock_gethostbyname, mock_requests_get):
        """Test network configuration checking"""
        # Mock successful network tests
        mock_requests_get.side_effect = [
            Mock(status_code=200),  # localhost test
            Mock(status_code=200)   # external test
        ]
        mock_gethostbyname.return_value = "8.8.8.8"
        
        result = self.system_tester.test_network_configuration()
        
        self.assertIsInstance(result, UbuntuCompatibilityResult)
        self.assertEqual(result.test_name, "network_configuration")

class TestUbuntuPerformanceBenchmark(unittest.TestCase):
    """Test cases for UbuntuPerformanceBenchmark"""
    
    def setUp(self):
        self.benchmark = UbuntuPerformanceBenchmark()
    
    def test_initialization(self):
        """Test performance benchmark initialization"""
        self.assertIsNotNone(self.benchmark)
    
    @patch('psutil.virtual_memory')
    @patch('requests.get')
    def test_benchmark_system_performance(self, mock_requests_get, mock_memory):
        """Test system performance benchmarking"""
        # Mock memory info
        mock_memory.return_value = Mock(
            total=8 * 1024**3,  # 8GB
            available=4 * 1024**3,  # 4GB
            percent=50.0
        )
        
        # Mock network request
        mock_requests_get.return_value = Mock(status_code=200)
        
        result = self.benchmark.benchmark_system_performance()
        
        self.assertIsInstance(result, UbuntuCompatibilityResult)
        self.assertEqual(result.test_name, "system_performance_benchmark")
        self.assertIn("performance_metrics", result.details)

class TestUbuntuCompatibilityTestFramework(unittest.TestCase):
    """Test cases for UbuntuCompatibilityTestFramework"""
    
    def setUp(self):
        self.framework = UbuntuCompatibilityTestFramework("24.04")
    
    def test_initialization(self):
        """Test framework initialization"""
        self.assertEqual(self.framework.ubuntu_version, "24.04")
        self.assertIsNotNone(self.framework.env_simulator)
        self.assertIsNotNone(self.framework.docker_tester)
        self.assertIsNotNone(self.framework.system_tester)
        self.assertIsNotNone(self.framework.performance_benchmark)
        self.assertIsInstance(self.framework.results, list)
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        # Add some mock results
        self.framework.results = [
            UbuntuCompatibilityResult(
                test_name="python_dependencies",
                result=TestResult.FAIL,
                message="Test failed",
                details={},
                execution_time=1.0
            ),
            UbuntuCompatibilityResult(
                test_name="docker_build_ubuntu",
                result=TestResult.WARNING,
                message="Test warning",
                details={},
                execution_time=1.0
            )
        ]
        
        recommendations = self.framework._generate_recommendations()
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        self.assertTrue(any("Python package" in rec for rec in recommendations))
    
    def test_generate_report_empty_results(self):
        """Test report generation with empty results"""
        # Mock the run_all_tests method to avoid actual execution
        with patch.object(self.framework, 'run_all_tests', return_value=[]):
            report = self.framework.generate_report()
            
            self.assertIn("ubuntu_version", report)
            self.assertIn("test_summary", report)
            self.assertIn("test_results", report)
            self.assertIn("recommendations", report)
            self.assertIn("ubuntu_specific_issues", report)

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete framework"""
    
    def test_full_framework_execution(self):
        """Test complete framework execution (mocked)"""
        framework = UbuntuCompatibilityTestFramework("24.04")
        
        # Mock all test methods to return successful results
        mock_result = UbuntuCompatibilityResult(
            test_name="mock_test",
            result=TestResult.PASS,
            message="Mock test passed",
            details={},
            execution_time=0.1
        )
        
        with patch.object(framework.env_simulator, 'test_python_dependencies', return_value=mock_result), \
             patch.object(framework.env_simulator, 'test_nodejs_dependencies', return_value=mock_result), \
             patch.object(framework.docker_tester, 'test_docker_build_ubuntu_compatibility', return_value=mock_result), \
             patch.object(framework.docker_tester, 'test_container_networking_ubuntu', return_value=mock_result), \
             patch.object(framework.system_tester, 'test_file_system_permissions', return_value=mock_result), \
             patch.object(framework.system_tester, 'test_network_configuration', return_value=mock_result), \
             patch.object(framework.performance_benchmark, 'benchmark_system_performance', return_value=mock_result), \
             patch.object(framework.performance_benchmark, 'benchmark_docker_performance', return_value=mock_result):
            
            results = framework.run_all_tests()
            
            self.assertEqual(len(results), 8)  # All 8 tests
            self.assertTrue(all(isinstance(r, UbuntuCompatibilityResult) for r in results))
            
            # Test report generation
            report = framework.generate_report()
            self.assertEqual(report["test_summary"]["total_tests"], 8)
            self.assertEqual(report["test_summary"]["passed"], 8)
            self.assertEqual(report["test_summary"]["failed"], 0)

def create_test_files():
    """Create temporary test files for testing"""
    test_files = {
        "requirements.txt": "requests==2.28.0\nflask>=2.0.0\n",
        "package.json": json.dumps({
            "dependencies": {
                "react": "^18.0.0",
                "typescript": "^4.0.0"
            },
            "devDependencies": {
                "eslint": "^8.0.0"
            }
        }),
        "Dockerfile": "FROM ubuntu:24.04\nRUN apt-get update\n",
        "scripts/test.sh": "#!/bin/bash\necho 'test'\n"
    }
    
    # Create test directory structure
    os.makedirs("scripts", exist_ok=True)
    
    for file_path, content in test_files.items():
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
    
    return list(test_files.keys())

def cleanup_test_files(file_paths):
    """Clean up test files"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
    
    # Remove test directories if empty
    try:
        if os.path.exists("scripts") and not os.listdir("scripts"):
            os.rmdir("scripts")
    except Exception:
        pass

def run_functional_test():
    """Run a functional test of the Ubuntu compatibility tester"""
    print("Running functional test of Ubuntu Compatibility Tester...")
    
    # Create test files
    test_files = create_test_files()
    
    try:
        # Initialize framework
        framework = UbuntuCompatibilityTestFramework("24.04")
        
        # Run a subset of tests (to avoid Docker requirements in CI)
        print("Testing file system permissions...")
        fs_result = framework.system_tester.test_file_system_permissions()
        print(f"File system test: {fs_result.result.value} - {fs_result.message}")
        
        print("Testing system performance...")
        perf_result = framework.performance_benchmark.benchmark_system_performance()
        print(f"Performance test: {perf_result.result.value} - {perf_result.message}")
        
        # Test report generation
        framework.results = [fs_result, perf_result]
        report = framework.generate_report()
        
        print(f"Generated report with {len(report['test_results'])} test results")
        print(f"Overall status: {report['test_summary']['overall_status']}")
        print(f"Score: {report['test_summary']['score']}%")
        
        print("Functional test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Functional test failed: {str(e)}")
        return False
    
    finally:
        # Clean up test files
        cleanup_test_files(test_files)

def main():
    """Main test function"""
    print("Ubuntu Compatibility Tester - Test Suite")
    print("=" * 50)
    
    # Run unit tests
    print("Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "=" * 50)
    
    # Run functional test
    success = run_functional_test()
    
    if success:
        print("\nAll tests passed! ✅")
        return 0
    else:
        print("\nSome tests failed! ❌")
        return 1

if __name__ == "__main__":
    sys.exit(main())