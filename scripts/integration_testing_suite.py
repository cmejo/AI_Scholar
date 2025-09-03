#!/usr/bin/env python3
"""
Integration Testing and Validation Suite
Comprehensive testing framework for AI Scholar application workflows
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import requests
import psycopg2
import redis
import docker
from dataclasses import dataclass, asdict
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    category: str
    status: str  # 'passed', 'failed', 'skipped'
    duration: float
    message: str
    details: Dict[str, Any]
    ubuntu_specific: bool = False

@dataclass
class IntegrationTestConfig:
    """Configuration for integration testing"""
    # Application endpoints
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    
    # Database connections
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ai_scholar"
    postgres_user: str = "postgres"
    postgres_password: str = "password"
    
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    # Docker configuration
    docker_compose_file: str = "docker-compose.yml"
    ubuntu_test_image: str = "ubuntu:24.04"
    
    # Test timeouts
    service_startup_timeout: int = 60
    api_timeout: int = 30
    database_timeout: int = 10

class IntegrationTestingSuite:
    """Main integration testing suite"""
    
    def __init__(self, config: IntegrationTestConfig = None):
        self.config = config or IntegrationTestConfig()
        self.results: List[TestResult] = []
        self.docker_client = None
        self.start_time = datetime.now()
        
    def initialize(self) -> bool:
        """Initialize testing environment"""
        try:
            # Initialize Docker client
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized")
            
            # Create results directory
            os.makedirs("integration_test_results", exist_ok=True)
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize testing suite: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete integration test suite"""
        logger.info("Starting comprehensive integration testing suite")
        
        if not self.initialize():
            return {"status": "failed", "error": "Failed to initialize testing environment"}
        
        # Test categories to run
        test_categories = [
            ("end_to_end", self.run_end_to_end_tests),
            ("service_integration", self.run_service_integration_tests),
            ("api_contract", self.run_api_contract_tests),
            ("database_integration", self.run_database_integration_tests),
            ("ubuntu_compatibility", self.run_ubuntu_compatibility_tests)
        ]
        
        for category_name, test_method in test_categories:
            logger.info(f"Running {category_name} tests")
            try:
                test_method()
            except Exception as e:
                logger.error(f"Error in {category_name} tests: {e}")
                self.results.append(TestResult(
                    test_name=f"{category_name}_suite",
                    category=category_name,
                    status="failed",
                    duration=0.0,
                    message=f"Test suite failed: {str(e)}",
                    details={"error": str(e)}
                ))
        
        return self.generate_report()
    
    def run_end_to_end_tests(self):
        """Build end-to-end testing framework for complete application workflows"""
        logger.info("Running end-to-end workflow tests")
        
        # Test 1: Complete user registration and authentication workflow
        self._test_user_authentication_workflow()
        
        # Test 2: Document upload and processing workflow
        self._test_document_processing_workflow()
        
        # Test 3: Research query and RAG workflow
        self._test_rag_query_workflow()
        
        # Test 4: Citation generation workflow
        self._test_citation_workflow()
        
        # Test 5: Zotero integration workflow
        self._test_zotero_integration_workflow()
    
    def run_service_integration_tests(self):
        """Implement service integration testing with Ubuntu environment simulation"""
        logger.info("Running service integration tests")
        
        # Test 1: Inter-service communication
        self._test_service_communication()
        
        # Test 2: Database connectivity across services
        self._test_cross_service_database_access()
        
        # Test 3: Redis caching integration
        self._test_redis_integration()
        
        # Test 4: File system integration
        self._test_file_system_integration()
        
        # Test 5: Ubuntu environment simulation
        self._test_ubuntu_environment_simulation()
    
    def run_api_contract_tests(self):
        """Create API contract testing suite with comprehensive endpoint validation"""
        logger.info("Running API contract tests")
        
        # Test 1: Authentication endpoints
        self._test_auth_api_contracts()
        
        # Test 2: Document management endpoints
        self._test_document_api_contracts()
        
        # Test 3: Search and RAG endpoints
        self._test_search_api_contracts()
        
        # Test 4: Citation endpoints
        self._test_citation_api_contracts()
        
        # Test 5: Zotero integration endpoints
        self._test_zotero_api_contracts()
    
    def run_database_integration_tests(self):
        """Build database integration testing with Ubuntu-specific configurations"""
        logger.info("Running database integration tests")
        
        # Test 1: PostgreSQL connection and operations
        self._test_postgresql_integration()
        
        # Test 2: Redis connection and caching
        self._test_redis_database_integration()
        
        # Test 3: ChromaDB vector database integration
        self._test_chromadb_integration()
        
        # Test 4: Database migration and schema validation
        self._test_database_migrations()
        
        # Test 5: Ubuntu-specific database configurations
        self._test_ubuntu_database_configs()
    
    def run_ubuntu_compatibility_tests(self):
        """Run Ubuntu-specific compatibility tests"""
        logger.info("Running Ubuntu compatibility tests")
        
        # Test 1: Docker container deployment on Ubuntu
        self._test_ubuntu_docker_deployment()
        
        # Test 2: File permissions and access
        self._test_ubuntu_file_permissions()
        
        # Test 3: Network configuration
        self._test_ubuntu_networking()
        
        # Test 4: System resource utilization
        self._test_ubuntu_resource_usage()
    
    def _test_user_authentication_workflow(self):
        """Test complete user authentication workflow"""
        start_time = time.time()
        test_name = "user_authentication_workflow"
        
        try:
            # Step 1: User registration
            registration_data = {
                "email": "test@example.com",
                "password": "testpassword123",
                "name": "Test User"
            }
            
            response = requests.post(
                f"{self.config.backend_url}/api/auth/register",
                json=registration_data,
                timeout=self.config.api_timeout
            )
            
            if response.status_code != 201:
                raise Exception(f"Registration failed: {response.status_code}")
            
            # Step 2: User login
            login_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            
            response = requests.post(
                f"{self.config.backend_url}/api/auth/login",
                json=login_data,
                timeout=self.config.api_timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"Login failed: {response.status_code}")
            
            token = response.json().get("access_token")
            if not token:
                raise Exception("No access token received")
            
            # Step 3: Authenticated request
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.config.backend_url}/api/user/profile",
                headers=headers,
                timeout=self.config.api_timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"Profile access failed: {response.status_code}")
            
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name=test_name,
                category="end_to_end",
                status="passed",
                duration=duration,
                message="User authentication workflow completed successfully",
                details={"steps_completed": 3}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name=test_name,
                category="end_to_end",
                status="failed",
                duration=duration,
                message=f"Authentication workflow failed: {str(e)}",
                details={"error": str(e)}
            ))
    
    def _test_document_processing_workflow(self):
        """Test document upload and processing workflow"""
        start_time = time.time()
        test_name = "document_processing_workflow"
        
        try:
            # Create a test document
            test_content = "This is a test document for processing workflow validation."
            
            # Step 1: Document upload
            files = {"file": ("test.txt", test_content, "text/plain")}
            response = requests.post(
                f"{self.config.backend_url}/api/documents/upload",
                files=files,
                timeout=self.config.api_timeout
            )
            
            if response.status_code != 201:
                raise Exception(f"Document upload failed: {response.status_code}")
            
            document_id = response.json().get("document_id")
            if not document_id:
                raise Exception("No document ID received")
            
            # Step 2: Check processing status
            max_retries = 10
            for _ in range(max_retries):
                response = requests.get(
                    f"{self.config.backend_url}/api/documents/{document_id}/status",
                    timeout=self.config.api_timeout
                )
                
                if response.status_code == 200:
                    status = response.json().get("status")
                    if status == "processed":
                        break
                    elif status == "failed":
                        raise Exception("Document processing failed")
                
                time.sleep(2)
            else:
                raise Exception("Document processing timeout")
            
            # Step 3: Retrieve processed document
            response = requests.get(
                f"{self.config.backend_url}/api/documents/{document_id}",
                timeout=self.config.api_timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"Document retrieval failed: {response.status_code}")
            
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name=test_name,
                category="end_to_end",
                status="passed",
                duration=duration,
                message="Document processing workflow completed successfully",
                details={"document_id": document_id}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name=test_name,
                category="end_to_end",
                status="failed",
                duration=duration,
                message=f"Document processing workflow failed: {str(e)}",
                details={"error": str(e)}
            ))
    
    def _test_rag_query_workflow(self):
        """Test research query and RAG workflow"""
        start_time = time.time()
        test_name = "rag_query_workflow"
        
        try:
            # Step 1: Submit research query
            query_data = {
                "query": "What are the latest developments in machine learning?",
                "context_limit": 5
            }
            
            response = requests.post(
                f"{self.config.backend_url}/api/research/query",
                json=query_data,
                timeout=self.config.api_timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"RAG query failed: {response.status_code}")
            
            result = response.json()
            if not result.get("answer"):
                raise Exception("No answer received from RAG system")
            
            # Step 2: Validate response structure
            required_fields = ["answer", "sources", "confidence"]
            for field in required_fields:
                if field not in result:
                    raise Exception(f"Missing required field: {field}")
            
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name=test_name,
                category="end_to_end",
                status="passed",
                duration=duration,
                message="RAG query workflow completed successfully",
                details={"confidence": result.get("confidence", 0)}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name=test_name,
                category="end_to_end",
                status="failed",
                duration=duration,
                message=f"RAG query workflow failed: {str(e)}",
                details={"error": str(e)}
            ))
    
    def _test_service_communication(self):
        """Test inter-service communication"""
        start_time = time.time()
        test_name = "service_communication"
        
        try:
            # Test backend health endpoint
            response = requests.get(
                f"{self.config.backend_url}/health",
                timeout=self.config.api_timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"Backend health check failed: {response.status_code}")
            
            # Test frontend accessibility
            response = requests.get(
                self.config.frontend_url,
                timeout=self.config.api_timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"Frontend accessibility failed: {response.status_code}")
            
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name=test_name,
                category="service_integration",
                status="passed",
                duration=duration,
                message="Service communication test passed",
                details={"services_tested": 2}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name=test_name,
                category="service_integration",
                status="failed",
                duration=duration,
                message=f"Service communication failed: {str(e)}",
                details={"error": str(e)}
            ))
    
    def _test_postgresql_integration(self):
        """Test PostgreSQL database integration"""
        start_time = time.time()
        test_name = "postgresql_integration"
        
        try:
            # Connect to PostgreSQL
            conn = psycopg2.connect(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                database=self.config.postgres_db,
                user=self.config.postgres_user,
                password=self.config.postgres_password
            )
            
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # Test table existence
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name=test_name,
                category="database_integration",
                status="passed",
                duration=duration,
                message="PostgreSQL integration test passed",
                details={
                    "version": version,
                    "tables_count": len(tables)
                },
                ubuntu_specific=True
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name=test_name,
                category="database_integration",
                status="failed",
                duration=duration,
                message=f"PostgreSQL integration failed: {str(e)}",
                details={"error": str(e)},
                ubuntu_specific=True
            ))
    
    def _test_ubuntu_docker_deployment(self):
        """Test Docker container deployment on Ubuntu"""
        start_time = time.time()
        test_name = "ubuntu_docker_deployment"
        
        try:
            if not self.docker_client:
                raise Exception("Docker client not initialized")
            
            # Pull Ubuntu test image
            image = self.docker_client.images.pull(self.config.ubuntu_test_image)
            
            # Run test container
            container = self.docker_client.containers.run(
                self.config.ubuntu_test_image,
                command="echo 'Ubuntu Docker test successful'",
                detach=True,
                remove=True
            )
            
            # Wait for container to complete
            result = container.wait()
            logs = container.logs().decode('utf-8')
            
            if result['StatusCode'] != 0:
                raise Exception(f"Container failed with status: {result['StatusCode']}")
            
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name=test_name,
                category="ubuntu_compatibility",
                status="passed",
                duration=duration,
                message="Ubuntu Docker deployment test passed",
                details={
                    "image": self.config.ubuntu_test_image,
                    "logs": logs.strip()
                },
                ubuntu_specific=True
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name=test_name,
                category="ubuntu_compatibility",
                status="failed",
                duration=duration,
                message=f"Ubuntu Docker deployment failed: {str(e)}",
                details={"error": str(e)},
                ubuntu_specific=True
            ))
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate statistics
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "passed"])
        failed_tests = len([r for r in self.results if r.status == "failed"])
        skipped_tests = len([r for r in self.results if r.status == "skipped"])
        ubuntu_specific_tests = len([r for r in self.results if r.ubuntu_specific])
        
        # Group results by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(asdict(result))
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": skipped_tests,
                "ubuntu_specific": ubuntu_specific_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_duration": total_duration,
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            "categories": categories,
            "configuration": asdict(self.config),
            "environment": {
                "python_version": subprocess.check_output(["python", "--version"]).decode().strip(),
                "docker_version": self._get_docker_version(),
                "os_info": self._get_os_info()
            }
        }
        
        # Save report to file
        report_file = f"integration_test_results/integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Integration test report saved to: {report_file}")
        logger.info(f"Test Summary: {passed_tests}/{total_tests} passed ({report['summary']['success_rate']:.1f}%)")
        
        return report
    
    def _get_docker_version(self) -> str:
        """Get Docker version information"""
        try:
            if self.docker_client:
                return self.docker_client.version()['Version']
            return "Unknown"
        except:
            return "Unknown"
    
    def _get_os_info(self) -> str:
        """Get operating system information"""
        try:
            return subprocess.check_output(["uname", "-a"]).decode().strip()
        except:
            return "Unknown"

def main():
    """Main function to run integration tests"""
    config = IntegrationTestConfig()
    suite = IntegrationTestingSuite(config)
    
    try:
        report = suite.run_all_tests()
        
        # Print summary
        print("\n" + "="*80)
        print("INTEGRATION TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Skipped: {report['summary']['skipped']}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Duration: {report['summary']['total_duration']:.2f} seconds")
        print(f"Ubuntu-specific tests: {report['summary']['ubuntu_specific']}")
        
        # Print failed tests
        if report['summary']['failed'] > 0:
            print("\nFAILED TESTS:")
            print("-" * 40)
            for category, tests in report['categories'].items():
                failed_in_category = [t for t in tests if t['status'] == 'failed']
                for test in failed_in_category:
                    print(f"  {test['test_name']}: {test['message']}")
        
        return report['summary']['failed'] == 0
        
    except Exception as e:
        logger.error(f"Integration testing failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)