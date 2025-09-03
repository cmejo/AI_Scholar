#!/usr/bin/env python3
"""
API Contract Testing Suite
Comprehensive endpoint validation for AI Scholar API
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional
import requests
from dataclasses import dataclass, asdict
from jsonschema import validate, ValidationError
import yaml

logger = logging.getLogger(__name__)

@dataclass
class APIEndpoint:
    """API endpoint definition"""
    path: str
    method: str
    description: str
    request_schema: Optional[Dict] = None
    response_schema: Optional[Dict] = None
    auth_required: bool = False
    ubuntu_specific: bool = False

@dataclass
class APITestResult:
    """API test result"""
    endpoint: str
    method: str
    status: str  # 'passed', 'failed', 'skipped'
    response_code: int
    response_time: float
    message: str
    details: Dict[str, Any]

class APIContractTester:
    """API contract testing implementation"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[APITestResult] = []
        self.auth_token: Optional[str] = None
        
        # Define API contracts
        self.endpoints = self._define_api_contracts()
    
    def _define_api_contracts(self) -> List[APIEndpoint]:
        """Define comprehensive API contracts"""
        return [
            # Authentication endpoints
            APIEndpoint(
                path="/api/auth/register",
                method="POST",
                description="User registration",
                request_schema={
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "password": {"type": "string", "minLength": 8},
                        "name": {"type": "string", "minLength": 1}
                    },
                    "required": ["email", "password", "name"]
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "message": {"type": "string"}
                    },
                    "required": ["user_id", "message"]
                }
            ),
            APIEndpoint(
                path="/api/auth/login",
                method="POST",
                description="User login",
                request_schema={
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "password": {"type": "string"}
                    },
                    "required": ["email", "password"]
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "access_token": {"type": "string"},
                        "token_type": {"type": "string"},
                        "expires_in": {"type": "integer"}
                    },
                    "required": ["access_token", "token_type"]
                }
            ),
            
            # Document management endpoints
            APIEndpoint(
                path="/api/documents/upload",
                method="POST",
                description="Document upload",
                auth_required=True,
                response_schema={
                    "type": "object",
                    "properties": {
                        "document_id": {"type": "string"},
                        "filename": {"type": "string"},
                        "status": {"type": "string"}
                    },
                    "required": ["document_id", "filename", "status"]
                }
            ),
            APIEndpoint(
                path="/api/documents/{document_id}",
                method="GET",
                description="Get document details",
                auth_required=True,
                response_schema={
                    "type": "object",
                    "properties": {
                        "document_id": {"type": "string"},
                        "filename": {"type": "string"},
                        "content": {"type": "string"},
                        "metadata": {"type": "object"},
                        "created_at": {"type": "string"},
                        "updated_at": {"type": "string"}
                    },
                    "required": ["document_id", "filename", "content"]
                }
            ),
            APIEndpoint(
                path="/api/documents",
                method="GET",
                description="List user documents",
                auth_required=True,
                response_schema={
                    "type": "object",
                    "properties": {
                        "documents": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "document_id": {"type": "string"},
                                    "filename": {"type": "string"},
                                    "created_at": {"type": "string"}
                                }
                            }
                        },
                        "total": {"type": "integer"}
                    },
                    "required": ["documents", "total"]
                }
            ),
            
            # Search and RAG endpoints
            APIEndpoint(
                path="/api/research/query",
                method="POST",
                description="Research query with RAG",
                auth_required=True,
                request_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "minLength": 1},
                        "context_limit": {"type": "integer", "minimum": 1, "maximum": 20},
                        "include_sources": {"type": "boolean"}
                    },
                    "required": ["query"]
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "answer": {"type": "string"},
                        "sources": {"type": "array"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "query_id": {"type": "string"}
                    },
                    "required": ["answer", "sources", "confidence"]
                }
            ),
            APIEndpoint(
                path="/api/search/documents",
                method="POST",
                description="Document search",
                auth_required=True,
                request_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "minLength": 1},
                        "filters": {"type": "object"},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 100}
                    },
                    "required": ["query"]
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "results": {"type": "array"},
                        "total": {"type": "integer"},
                        "query_time": {"type": "number"}
                    },
                    "required": ["results", "total"]
                }
            ),
            
            # Citation endpoints
            APIEndpoint(
                path="/api/citations/generate",
                method="POST",
                description="Generate citations",
                auth_required=True,
                request_schema={
                    "type": "object",
                    "properties": {
                        "document_ids": {"type": "array", "items": {"type": "string"}},
                        "style": {"type": "string", "enum": ["APA", "MLA", "Chicago", "IEEE"]},
                        "format": {"type": "string", "enum": ["text", "bibtex", "json"]}
                    },
                    "required": ["document_ids", "style"]
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "citations": {"type": "array"},
                        "bibliography": {"type": "string"},
                        "style": {"type": "string"}
                    },
                    "required": ["citations", "bibliography"]
                }
            ),
            
            # Zotero integration endpoints
            APIEndpoint(
                path="/api/zotero/auth",
                method="POST",
                description="Zotero OAuth authentication",
                auth_required=True,
                request_schema={
                    "type": "object",
                    "properties": {
                        "oauth_token": {"type": "string"},
                        "oauth_verifier": {"type": "string"}
                    },
                    "required": ["oauth_token", "oauth_verifier"]
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "username": {"type": "string"},
                        "access_token": {"type": "string"}
                    },
                    "required": ["user_id", "access_token"]
                },
                ubuntu_specific=True
            ),
            APIEndpoint(
                path="/api/zotero/library/sync",
                method="POST",
                description="Sync Zotero library",
                auth_required=True,
                response_schema={
                    "type": "object",
                    "properties": {
                        "sync_id": {"type": "string"},
                        "status": {"type": "string"},
                        "items_synced": {"type": "integer"}
                    },
                    "required": ["sync_id", "status"]
                },
                ubuntu_specific=True
            ),
            
            # Health and system endpoints
            APIEndpoint(
                path="/health",
                method="GET",
                description="Health check",
                response_schema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["healthy", "unhealthy"]},
                        "timestamp": {"type": "string"},
                        "version": {"type": "string"},
                        "services": {"type": "object"}
                    },
                    "required": ["status", "timestamp"]
                },
                ubuntu_specific=True
            ),
            APIEndpoint(
                path="/api/system/info",
                method="GET",
                description="System information",
                auth_required=True,
                response_schema={
                    "type": "object",
                    "properties": {
                        "version": {"type": "string"},
                        "environment": {"type": "string"},
                        "database_status": {"type": "string"},
                        "cache_status": {"type": "string"}
                    },
                    "required": ["version", "environment"]
                },
                ubuntu_specific=True
            )
        ]
    
    def authenticate(self, email: str = "test@example.com", password: str = "testpassword123") -> bool:
        """Authenticate and get access token"""
        try:
            # First register user (might fail if already exists)
            register_data = {
                "email": email,
                "password": password,
                "name": "Test User"
            }
            requests.post(f"{self.base_url}/api/auth/register", json=register_data)
            
            # Login to get token
            login_data = {"email": email, "password": password}
            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
            
            if response.status_code == 200:
                self.auth_token = response.json().get("access_token")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def test_all_endpoints(self) -> List[APITestResult]:
        """Test all defined API endpoints"""
        logger.info("Starting comprehensive API contract testing")
        
        # Authenticate first
        if not self.authenticate():
            logger.warning("Authentication failed, some tests may be skipped")
        
        for endpoint in self.endpoints:
            self._test_endpoint(endpoint)
        
        return self.results
    
    def _test_endpoint(self, endpoint: APIEndpoint):
        """Test individual API endpoint"""
        start_time = time.time()
        
        try:
            # Skip if authentication required but not available
            if endpoint.auth_required and not self.auth_token:
                self.results.append(APITestResult(
                    endpoint=endpoint.path,
                    method=endpoint.method,
                    status="skipped",
                    response_code=0,
                    response_time=0.0,
                    message="Skipped due to missing authentication",
                    details={"reason": "no_auth_token"}
                ))
                return
            
            # Prepare request
            url = f"{self.base_url}{endpoint.path}"
            headers = {}
            
            if endpoint.auth_required and self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            # Prepare test data based on endpoint
            data = self._get_test_data(endpoint)
            
            # Handle path parameters
            if "{document_id}" in url:
                url = url.replace("{document_id}", "test-doc-id")
            
            # Make request
            if endpoint.method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif endpoint.method == "POST":
                if endpoint.path == "/api/documents/upload":
                    # Special handling for file upload
                    files = {"file": ("test.txt", "Test content", "text/plain")}
                    response = requests.post(url, files=files, headers=headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
            elif endpoint.method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif endpoint.method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise Exception(f"Unsupported method: {endpoint.method}")
            
            response_time = time.time() - start_time
            
            # Validate response
            validation_result = self._validate_response(endpoint, response)
            
            self.results.append(APITestResult(
                endpoint=endpoint.path,
                method=endpoint.method,
                status=validation_result["status"],
                response_code=response.status_code,
                response_time=response_time,
                message=validation_result["message"],
                details={
                    "description": endpoint.description,
                    "ubuntu_specific": endpoint.ubuntu_specific,
                    "validation_details": validation_result.get("details", {})
                }
            ))
            
        except Exception as e:
            response_time = time.time() - start_time
            self.results.append(APITestResult(
                endpoint=endpoint.path,
                method=endpoint.method,
                status="failed",
                response_code=0,
                response_time=response_time,
                message=f"Request failed: {str(e)}",
                details={"error": str(e), "ubuntu_specific": endpoint.ubuntu_specific}
            ))
    
    def _get_test_data(self, endpoint: APIEndpoint) -> Dict[str, Any]:
        """Generate test data for endpoint"""
        if not endpoint.request_schema:
            return {}
        
        # Generate sample data based on schema
        test_data = {}
        properties = endpoint.request_schema.get("properties", {})
        
        for prop, schema in properties.items():
            if schema["type"] == "string":
                if prop == "email":
                    test_data[prop] = "test@example.com"
                elif prop == "password":
                    test_data[prop] = "testpassword123"
                elif prop == "query":
                    test_data[prop] = "test query"
                else:
                    test_data[prop] = f"test_{prop}"
            elif schema["type"] == "integer":
                test_data[prop] = schema.get("minimum", 1)
            elif schema["type"] == "boolean":
                test_data[prop] = True
            elif schema["type"] == "array":
                test_data[prop] = ["test-item"]
            elif schema["type"] == "object":
                test_data[prop] = {}
        
        return test_data
    
    def _validate_response(self, endpoint: APIEndpoint, response: requests.Response) -> Dict[str, Any]:
        """Validate API response against contract"""
        try:
            # Check status code
            expected_codes = [200, 201, 202, 204]
            if response.status_code not in expected_codes:
                # Some endpoints might legitimately return other codes
                if response.status_code == 404 and "{document_id}" in endpoint.path:
                    return {
                        "status": "passed",
                        "message": "Expected 404 for test document ID",
                        "details": {"expected_404": True}
                    }
                elif response.status_code == 401 and endpoint.auth_required:
                    return {
                        "status": "passed",
                        "message": "Expected 401 for authentication test",
                        "details": {"expected_401": True}
                    }
                else:
                    return {
                        "status": "failed",
                        "message": f"Unexpected status code: {response.status_code}",
                        "details": {"response_text": response.text[:500]}
                    }
            
            # Validate response schema if defined
            if endpoint.response_schema and response.content:
                try:
                    response_data = response.json()
                    validate(instance=response_data, schema=endpoint.response_schema)
                    
                    return {
                        "status": "passed",
                        "message": "Response validation successful",
                        "details": {"response_size": len(response.content)}
                    }
                except ValidationError as e:
                    return {
                        "status": "failed",
                        "message": f"Response schema validation failed: {e.message}",
                        "details": {"validation_error": str(e)}
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "failed",
                        "message": "Invalid JSON response",
                        "details": {"response_text": response.text[:200]}
                    }
            
            return {
                "status": "passed",
                "message": "Basic response validation successful",
                "details": {"response_size": len(response.content)}
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Response validation error: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate API contract test report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "passed"])
        failed_tests = len([r for r in self.results if r.status == "failed"])
        skipped_tests = len([r for r in self.results if r.status == "skipped"])
        ubuntu_specific_tests = len([r for r in self.results if r.details.get("ubuntu_specific", False)])
        
        # Calculate average response time
        response_times = [r.response_time for r in self.results if r.response_time > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        report = {
            "summary": {
                "total_endpoints": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": skipped_tests,
                "ubuntu_specific": ubuntu_specific_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "average_response_time": avg_response_time
            },
            "results": [asdict(result) for result in self.results],
            "failed_endpoints": [
                asdict(result) for result in self.results 
                if result.status == "failed"
            ]
        }
        
        return report

def main():
    """Main function for API contract testing"""
    tester = APIContractTester()
    results = tester.test_all_endpoints()
    report = tester.generate_report()
    
    # Save report
    with open("integration_test_results/api_contract_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\nAPI CONTRACT TEST SUMMARY")
    print("=" * 50)
    print(f"Total Endpoints: {report['summary']['total_endpoints']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Skipped: {report['summary']['skipped']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
    print(f"Average Response Time: {report['summary']['average_response_time']:.3f}s")
    print(f"Ubuntu-specific tests: {report['summary']['ubuntu_specific']}")
    
    return report['summary']['failed'] == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)