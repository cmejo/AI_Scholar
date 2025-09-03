#!/usr/bin/env python3
"""
Integration Testing Suite - Test Runner
Validates the integration testing framework components
"""

import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
import sys

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from integration_testing_suite import IntegrationTestingSuite, IntegrationTestConfig, TestResult
from api_contract_tester import APIContractTester, APIEndpoint, APITestResult
from database_integration_tester import DatabaseIntegrationTester, DatabaseConfig, DatabaseTestResult
from ubuntu_environment_simulator import UbuntuEnvironmentSimulator, UbuntuEnvironmentConfig, UbuntuTestResult

class TestIntegrationTestingSuite(unittest.TestCase):
    """Test the main integration testing suite"""
    
    def setUp(self):
        self.config = IntegrationTestConfig()
        self.suite = IntegrationTestingSuite(self.config)
        
        # Create temporary results directory
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test suite initialization"""
        self.assertIsNotNone(self.suite.config)
        self.assertEqual(len(self.suite.results), 0)
        self.assertIsNotNone(self.suite.start_time)
    
    @patch('docker.from_env')
    def test_initialize_success(self, mock_docker):
        """Test successful initialization"""
        mock_docker.return_value = Mock()
        
        result = self.suite.initialize()
        
        self.assertTrue(result)
        self.assertIsNotNone(self.suite.docker_client)
        self.assertTrue(os.path.exists("integration_test_results"))
    
    @patch('docker.from_env')
    def test_initialize_failure(self, mock_docker):
        """Test initialization failure"""
        mock_docker.side_effect = Exception("Docker not available")
        
        result = self.suite.initialize()
        
        self.assertFalse(result)
    
    def test_test_result_creation(self):
        """Test TestResult data structure"""
        result = TestResult(
            test_name="test_example",
            category="unit_test",
            status="passed",
            duration=1.5,
            message="Test passed successfully",
            details={"key": "value"}
        )
        
        self.assertEqual(result.test_name, "test_example")
        self.assertEqual(result.category, "unit_test")
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.duration, 1.5)
        self.assertFalse(result.ubuntu_specific)
    
    def test_generate_report(self):
        """Test report generation"""
        # Add some test results
        self.suite.results = [
            TestResult(
                test_name="test1",
                category="category1",
                status="passed",
                duration=1.0,
                message="Test 1 passed",
                details={}
            ),
            TestResult(
                test_name="test2",
                category="category1",
                status="failed",
                duration=2.0,
                message="Test 2 failed",
                details={},
                ubuntu_specific=True
            )
        ]
        
        report = self.suite.generate_report()
        
        self.assertIn("summary", report)
        self.assertIn("categories", report)
        self.assertEqual(report["summary"]["total_tests"], 2)
        self.assertEqual(report["summary"]["passed"], 1)
        self.assertEqual(report["summary"]["failed"], 1)
        self.assertEqual(report["summary"]["ubuntu_specific"], 1)

class TestAPIContractTester(unittest.TestCase):
    """Test the API contract testing component"""
    
    def setUp(self):
        self.tester = APIContractTester("http://localhost:8000")
    
    def test_initialization(self):
        """Test API contract tester initialization"""
        self.assertEqual(self.tester.base_url, "http://localhost:8000")
        self.assertEqual(len(self.tester.results), 0)
        self.assertIsNone(self.tester.auth_token)
        self.assertGreater(len(self.tester.endpoints), 0)
    
    def test_endpoint_definition(self):
        """Test API endpoint definitions"""
        # Check that we have essential endpoints defined
        endpoint_paths = [ep.path for ep in self.tester.endpoints]
        
        self.assertIn("/api/auth/login", endpoint_paths)
        self.assertIn("/api/auth/register", endpoint_paths)
        self.assertIn("/health", endpoint_paths)
    
    def test_api_endpoint_structure(self):
        """Test APIEndpoint data structure"""
        endpoint = APIEndpoint(
            path="/api/test",
            method="GET",
            description="Test endpoint",
            auth_required=True,
            ubuntu_specific=True
        )
        
        self.assertEqual(endpoint.path, "/api/test")
        self.assertEqual(endpoint.method, "GET")
        self.assertTrue(endpoint.auth_required)
        self.assertTrue(endpoint.ubuntu_specific)
    
    def test_get_test_data(self):
        """Test test data generation"""
        endpoint = APIEndpoint(
            path="/api/test",
            method="POST",
            description="Test endpoint",
            request_schema={
                "type": "object",
                "properties": {
                    "email": {"type": "string", "format": "email"},
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                }
            }
        )
        
        test_data = self.tester._get_test_data(endpoint)
        
        self.assertIn("email", test_data)
        self.assertIn("name", test_data)
        self.assertIn("age", test_data)
        self.assertEqual(test_data["email"], "test@example.com")
    
    def test_generate_report(self):
        """Test API contract report generation"""
        # Add some test results
        self.tester.results = [
            APITestResult(
                endpoint="/api/test1",
                method="GET",
                status="passed",
                response_code=200,
                response_time=0.5,
                message="Test passed",
                details={}
            ),
            APITestResult(
                endpoint="/api/test2",
                method="POST",
                status="failed",
                response_code=500,
                response_time=1.0,
                message="Test failed",
                details={"ubuntu_specific": True}
            )
        ]
        
        report = self.tester.generate_report()
        
        self.assertIn("summary", report)
        self.assertEqual(report["summary"]["total_endpoints"], 2)
        self.assertEqual(report["summary"]["passed"], 1)
        self.assertEqual(report["summary"]["failed"], 1)
        self.assertEqual(report["summary"]["ubuntu_specific"], 1)

class TestDatabaseIntegrationTester(unittest.TestCase):
    """Test the database integration testing component"""
    
    def setUp(self):
        self.config = DatabaseConfig()
        self.tester = DatabaseIntegrationTester(self.config)
    
    def test_initialization(self):
        """Test database integration tester initialization"""
        self.assertIsNotNone(self.tester.config)
        self.assertEqual(len(self.tester.results), 0)
    
    def test_database_config(self):
        """Test database configuration"""
        self.assertEqual(self.config.postgres_host, "localhost")
        self.assertEqual(self.config.postgres_port, 5432)
        self.assertEqual(self.config.redis_host, "localhost")
        self.assertEqual(self.config.redis_port, 6379)
    
    def test_database_test_result(self):
        """Test DatabaseTestResult structure"""
        result = DatabaseTestResult(
            test_name="test_connection",
            database_type="postgresql",
            status="passed",
            duration=1.0,
            message="Connection successful",
            details={"version": "13.0"},
            ubuntu_specific=True
        )
        
        self.assertEqual(result.test_name, "test_connection")
        self.assertEqual(result.database_type, "postgresql")
        self.assertTrue(result.ubuntu_specific)
    
    def test_generate_report(self):
        """Test database integration report generation"""
        # Add some test results
        self.tester.results = [
            DatabaseTestResult(
                test_name="postgres_test",
                database_type="postgresql",
                status="passed",
                duration=1.0,
                message="Test passed",
                details={},
                ubuntu_specific=True
            ),
            DatabaseTestResult(
                test_name="redis_test",
                database_type="redis",
                status="failed",
                duration=2.0,
                message="Test failed",
                details={}
            )
        ]
        
        report = self.tester.generate_report()
        
        self.assertIn("summary", report)
        self.assertIn("results_by_database", report)
        self.assertEqual(report["summary"]["total_tests"], 2)
        self.assertEqual(report["summary"]["passed"], 1)
        self.assertEqual(report["summary"]["failed"], 1)
        self.assertEqual(report["summary"]["ubuntu_specific"], 1)

class TestUbuntuEnvironmentSimulator(unittest.TestCase):
    """Test the Ubuntu environment simulation component"""
    
    def setUp(self):
        self.config = UbuntuEnvironmentConfig()
        self.simulator = UbuntuEnvironmentSimulator(self.config)
    
    def test_initialization(self):
        """Test Ubuntu environment simulator initialization"""
        self.assertIsNotNone(self.simulator.config)
        self.assertEqual(len(self.simulator.results), 0)
        self.assertIsNone(self.simulator.docker_client)
        self.assertIsNone(self.simulator.test_container)
    
    def test_ubuntu_config(self):
        """Test Ubuntu environment configuration"""
        self.assertEqual(self.config.ubuntu_version, "24.04")
        self.assertEqual(self.config.docker_image, "ubuntu:24.04")
        self.assertEqual(self.config.python_version, "3.11")
        self.assertEqual(self.config.node_version, "20")
    
    @patch('docker.from_env')
    def test_initialize_success(self, mock_docker):
        """Test successful initialization"""
        mock_docker.return_value = Mock()
        
        result = self.simulator.initialize()
        
        self.assertTrue(result)
        self.assertIsNotNone(self.simulator.docker_client)
    
    @patch('docker.from_env')
    def test_initialize_failure(self, mock_docker):
        """Test initialization failure"""
        mock_docker.side_effect = Exception("Docker not available")
        
        result = self.simulator.initialize()
        
        self.assertFalse(result)
    
    def test_ubuntu_test_result(self):
        """Test UbuntuTestResult structure"""
        result = UbuntuTestResult(
            test_name="ubuntu_test",
            category="ubuntu_simulation",
            status="passed",
            duration=1.0,
            message="Test passed",
            details={"system_info": "Ubuntu 24.04"},
            ubuntu_version="24.04"
        )
        
        self.assertEqual(result.test_name, "ubuntu_test")
        self.assertEqual(result.ubuntu_version, "24.04")
    
    def test_generate_report(self):
        """Test Ubuntu simulation report generation"""
        # Add some test results
        self.simulator.results = [
            UbuntuTestResult(
                test_name="container_setup",
                category="ubuntu_simulation",
                status="passed",
                duration=1.0,
                message="Test passed",
                details={}
            ),
            UbuntuTestResult(
                test_name="dependency_install",
                category="ubuntu_simulation",
                status="failed",
                duration=2.0,
                message="Test failed",
                details={}
            )
        ]
        
        report = self.simulator.generate_report()
        
        self.assertIn("summary", report)
        self.assertEqual(report["summary"]["total_tests"], 2)
        self.assertEqual(report["summary"]["passed"], 1)
        self.assertEqual(report["summary"]["failed"], 1)
        self.assertEqual(report["summary"]["ubuntu_version"], "24.04")

class TestIntegrationFramework(unittest.TestCase):
    """Test the overall integration testing framework"""
    
    def test_component_integration(self):
        """Test that all components can work together"""
        # Test that all components can be imported and initialized
        config = IntegrationTestConfig()
        suite = IntegrationTestingSuite(config)
        
        api_tester = APIContractTester()
        db_config = DatabaseConfig()
        db_tester = DatabaseIntegrationTester(db_config)
        ubuntu_config = UbuntuEnvironmentConfig()
        ubuntu_simulator = UbuntuEnvironmentSimulator(ubuntu_config)
        
        # Verify all components are properly initialized
        self.assertIsNotNone(suite)
        self.assertIsNotNone(api_tester)
        self.assertIsNotNone(db_tester)
        self.assertIsNotNone(ubuntu_simulator)
    
    def test_result_data_consistency(self):
        """Test that all result data structures are consistent"""
        # Test that all result types have consistent fields
        test_result = TestResult(
            test_name="test",
            category="category",
            status="passed",
            duration=1.0,
            message="message",
            details={}
        )
        
        api_result = APITestResult(
            endpoint="/api/test",
            method="GET",
            status="passed",
            response_code=200,
            response_time=1.0,
            message="message",
            details={}
        )
        
        db_result = DatabaseTestResult(
            test_name="test",
            database_type="postgresql",
            status="passed",
            duration=1.0,
            message="message",
            details={}
        )
        
        ubuntu_result = UbuntuTestResult(
            test_name="test",
            category="category",
            status="passed",
            duration=1.0,
            message="message",
            details={}
        )
        
        # All should have status and message fields
        for result in [test_result, api_result, db_result, ubuntu_result]:
            self.assertIn("status", result.__dict__)
            self.assertIn("message", result.__dict__)

def run_integration_tests():
    """Run all integration testing framework tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestIntegrationTestingSuite,
        TestAPIContractTester,
        TestDatabaseIntegrationTester,
        TestUbuntuEnvironmentSimulator,
        TestIntegrationFramework
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Generate test report
    test_report = {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "success_rate": ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
        "failure_details": [str(failure) for failure in result.failures],
        "error_details": [str(error) for error in result.errors]
    }
    
    # Save test report
    os.makedirs("integration_test_results", exist_ok=True)
    with open("integration_test_results/framework_test_report.json", "w") as f:
        json.dump(test_report, f, indent=2)
    
    print(f"\nIntegration Testing Framework Test Results:")
    print(f"Tests Run: {test_report['tests_run']}")
    print(f"Failures: {test_report['failures']}")
    print(f"Errors: {test_report['errors']}")
    print(f"Success Rate: {test_report['success_rate']:.1f}%")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)