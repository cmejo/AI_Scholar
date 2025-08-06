"""
Integration tests for Secure Code Execution Service

Tests the complete integration of secure code execution including
API endpoints, service integration, and end-to-end workflows.
"""

import pytest
import asyncio
import json
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock

from app import app
from services.secure_code_execution import (
    SecureCodeExecutionService,
    ExecutionLanguage,
    ExecutionStatus,
    ResourceLimits,
    SecurityPolicy
)

class TestSecureCodeExecutionAPI:
    """Test secure code execution API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_auth_user(self):
        """Mock authenticated user"""
        with patch('app.get_current_user') as mock_user:
            mock_user.return_value = Mock(id="test-user-123", email="test@example.com")
            yield mock_user
    
    def test_get_supported_languages(self, client, mock_auth_user):
        """Test getting supported programming languages"""
        response = client.get("/api/secure-execution/languages")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "languages" in data
        languages = data["languages"]
        assert len(languages) > 0
        
        # Check for expected languages
        language_values = [lang["value"] for lang in languages]
        assert "python" in language_values
        assert "javascript" in language_values
        assert "r" in language_values
        assert "bash" in language_values
    
    def test_get_default_security_policy(self, client, mock_auth_user):
        """Test getting default security policy"""
        response = client.get("/api/secure-execution/security-policy/default")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "allow_network_access" in data
        assert "allow_file_system_access" in data
        assert "blocked_imports" in data
        assert "blocked_functions" in data
        
        # Verify security defaults
        assert data["allow_network_access"] is False
        assert data["allow_file_system_access"] is False
        assert "os" in data["blocked_imports"]
        assert "exec" in data["blocked_functions"]
    
    def test_get_default_resource_limits(self, client, mock_auth_user):
        """Test getting default resource limits"""
        response = client.get("/api/secure-execution/resource-limits/default")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "max_memory_mb" in data
        assert "max_cpu_percent" in data
        assert "max_execution_time_seconds" in data
        assert "max_disk_usage_mb" in data
        assert "max_network_requests" in data
        
        # Verify reasonable defaults
        assert data["max_memory_mb"] == 512
        assert data["max_cpu_percent"] == 50.0
        assert data["max_execution_time_seconds"] == 30
    
    @patch('services.secure_code_execution.secure_code_execution_service.execute_code')
    def test_execute_code_success(self, mock_execute, client, mock_auth_user):
        """Test successful code execution via API"""
        # Mock successful execution result
        from services.secure_code_execution import ExecutionResult
        mock_result = ExecutionResult(
            execution_id="test-123",
            status=ExecutionStatus.COMPLETED,
            output="Hello, World!\n",
            execution_time=1.5,
            memory_used_mb=50.0,
            cpu_used_percent=25.0
        )
        mock_execute.return_value = mock_result
        
        request_data = {
            "code": "print('Hello, World!')",
            "language": "python",
            "dependencies": [],
            "resource_limits": {
                "max_memory_mb": 256,
                "max_execution_time_seconds": 10
            },
            "security_policy": {
                "allow_network_access": False,
                "allow_file_system_access": False
            }
        }
        
        response = client.post("/api/secure-execution/execute", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["execution_id"] == "test-123"
        assert data["status"] == "completed"
        assert data["output"] == "Hello, World!\n"
        assert data["execution_time"] == 1.5
        assert len(data["security_violations"]) == 0
        
        mock_execute.assert_called_once()
    
    @patch('services.secure_code_execution.secure_code_execution_service.execute_code')
    def test_execute_code_security_violation(self, mock_execute, client, mock_auth_user):
        """Test code execution blocked by security violations"""
        from services.secure_code_execution import ExecutionResult
        mock_result = ExecutionResult(
            execution_id="test-456",
            status=ExecutionStatus.SECURITY_VIOLATION,
            output="",
            error="Security violations detected: Blocked import: os",
            security_violations=["Blocked import: os"]
        )
        mock_execute.return_value = mock_result
        
        request_data = {
            "code": "import os; os.system('rm -rf /')",
            "language": "python"
        }
        
        response = client.post("/api/secure-execution/execute", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "security_violation"
        assert len(data["security_violations"]) > 0
        assert "os" in data["security_violations"][0]
    
    def test_execute_code_invalid_language(self, client, mock_auth_user):
        """Test code execution with invalid language"""
        request_data = {
            "code": "print('Hello')",
            "language": "invalid_language"
        }
        
        response = client.post("/api/secure-execution/execute", json=request_data)
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_execute_code_invalid_resource_limits(self, client, mock_auth_user):
        """Test code execution with invalid resource limits"""
        request_data = {
            "code": "print('Hello')",
            "language": "python",
            "resource_limits": {
                "max_memory_mb": -1,  # Invalid negative value
                "max_execution_time_seconds": 0  # Invalid zero value
            }
        }
        
        response = client.post("/api/secure-execution/execute", json=request_data)
        
        # Should return validation error
        assert response.status_code == 422
    
    @patch('services.secure_code_execution.secure_code_execution_service.get_execution_result')
    def test_get_execution_result_success(self, mock_get_result, client, mock_auth_user):
        """Test getting execution result by ID"""
        from services.secure_code_execution import ExecutionResult
        mock_result = ExecutionResult(
            execution_id="test-789",
            status=ExecutionStatus.COMPLETED,
            output="Result output"
        )
        mock_get_result.return_value = mock_result
        
        response = client.get("/api/secure-execution/result/test-789")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["execution_id"] == "test-789"
        assert data["status"] == "completed"
        assert data["output"] == "Result output"
    
    @patch('services.secure_code_execution.secure_code_execution_service.get_execution_result')
    def test_get_execution_result_not_found(self, mock_get_result, client, mock_auth_user):
        """Test getting non-existent execution result"""
        mock_get_result.return_value = None
        
        response = client.get("/api/secure-execution/result/non-existent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @patch('services.secure_code_execution.secure_code_execution_service.list_active_executions')
    def test_list_active_executions(self, mock_list_executions, client, mock_auth_user):
        """Test listing active executions"""
        from services.secure_code_execution import ExecutionResult
        mock_results = [
            ExecutionResult("exec-1", ExecutionStatus.COMPLETED, "Output 1"),
            ExecutionResult("exec-2", ExecutionStatus.RUNNING, "")
        ]
        mock_list_executions.return_value = mock_results
        
        response = client.get("/api/secure-execution/executions")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert data[0]["execution_id"] == "exec-1"
        assert data[1]["execution_id"] == "exec-2"
    
    @patch('services.secure_code_execution.secure_code_execution_service.cancel_execution')
    def test_cancel_execution_success(self, mock_cancel, client, mock_auth_user):
        """Test successful execution cancellation"""
        mock_cancel.return_value = True
        
        response = client.post("/api/secure-execution/cancel/test-123")
        
        assert response.status_code == 200
        data = response.json()
        assert "cancelled successfully" in data["message"].lower()
    
    @patch('services.secure_code_execution.secure_code_execution_service.cancel_execution')
    def test_cancel_execution_not_found(self, mock_cancel, client, mock_auth_user):
        """Test cancelling non-existent execution"""
        mock_cancel.return_value = False
        
        response = client.post("/api/secure-execution/cancel/non-existent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @patch('services.secure_code_execution.SecurityScanner.scan_code')
    def test_validate_code_safe(self, mock_scan, client, mock_auth_user):
        """Test code validation for safe code"""
        mock_scan.return_value = []  # No violations
        
        response = client.post(
            "/api/secure-execution/validate-code",
            params={"code": "print('Hello')", "language": "python"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_safe"] is True
        assert len(data["violations"]) == 0
        assert data["language"] == "python"
    
    @patch('services.secure_code_execution.SecurityScanner.scan_code')
    def test_validate_code_unsafe(self, mock_scan, client, mock_auth_user):
        """Test code validation for unsafe code"""
        mock_scan.return_value = ["Blocked import: os", "Dangerous pattern: exec("]
        
        response = client.post(
            "/api/secure-execution/validate-code",
            params={"code": "import os; exec('malicious')", "language": "python"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_safe"] is False
        assert len(data["violations"]) == 2
        assert "os" in data["violations"][0]
        assert "exec" in data["violations"][1]
    
    @patch('services.secure_code_execution.secure_code_execution_service.cleanup_old_executions')
    def test_cleanup_old_executions(self, mock_cleanup, client, mock_auth_user):
        """Test cleanup of old execution results"""
        mock_cleanup.return_value = None
        
        response = client.delete("/api/secure-execution/cleanup?max_age_hours=48")
        
        assert response.status_code == 200
        data = response.json()
        assert "48 hours" in data["message"]
        mock_cleanup.assert_called_once_with(48)

class TestSecureCodeExecutionIntegration:
    """Test complete integration scenarios"""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        return SecureCodeExecutionService()
    
    @pytest.mark.asyncio
    async def test_python_code_execution_workflow(self, service):
        """Test complete Python code execution workflow"""
        # This test requires Docker to be available
        # In a real environment, this would test the full container workflow
        
        with patch.object(service.container_manager, 'create_container') as mock_create, \
             patch.object(service.container_manager, 'execute_in_container') as mock_execute, \
             patch.object(service.container_manager, 'cleanup_container') as mock_cleanup:
            
            mock_create.return_value = "test-container"
            mock_execute.return_value = ("42\n", "", 0)
            mock_cleanup.return_value = None
            
            from services.secure_code_execution import CodeExecutionRequest
            request = CodeExecutionRequest(
                code="""
import math

def calculate_factorial(n):
    if n <= 1:
        return 1
    return n * calculate_factorial(n - 1)

result = calculate_factorial(5)
print(f"5! = {result}")
""",
                language=ExecutionLanguage.PYTHON,
                dependencies=["math"],
                resource_limits=ResourceLimits(max_execution_time_seconds=10),
                security_policy=SecurityPolicy()
            )
            
            result = await service.execute_code(request)
            
            assert result.status == ExecutionStatus.COMPLETED
            assert result.execution_id is not None
            assert result.execution_time > 0
            assert len(result.security_violations) == 0
    
    @pytest.mark.asyncio
    async def test_javascript_code_execution_workflow(self, service):
        """Test complete JavaScript code execution workflow"""
        with patch.object(service.container_manager, 'create_container') as mock_create, \
             patch.object(service.container_manager, 'execute_in_container') as mock_execute, \
             patch.object(service.container_manager, 'cleanup_container') as mock_cleanup:
            
            mock_create.return_value = "test-container"
            mock_execute.return_value = ("Hello from JavaScript!\n", "", 0)
            mock_cleanup.return_value = None
            
            from services.secure_code_execution import CodeExecutionRequest
            request = CodeExecutionRequest(
                code="""
function greet(name) {
    return `Hello from ${name}!`;
}

console.log(greet('JavaScript'));
""",
                language=ExecutionLanguage.JAVASCRIPT,
                dependencies=["lodash"],
                resource_limits=ResourceLimits(max_memory_mb=256),
                security_policy=SecurityPolicy()
            )
            
            result = await service.execute_code(request)
            
            assert result.status == ExecutionStatus.COMPLETED
            assert "JavaScript" in result.output
    
    @pytest.mark.asyncio
    async def test_security_violation_workflow(self, service):
        """Test security violation detection workflow"""
        from services.secure_code_execution import CodeExecutionRequest
        request = CodeExecutionRequest(
            code="""
import os
import subprocess

# Attempt dangerous operations
os.system("echo 'This should be blocked'")
subprocess.call(["ls", "-la"])
exec("print('This is dangerous')")
""",
            language=ExecutionLanguage.PYTHON
        )
        
        result = await service.execute_code(request)
        
        assert result.status == ExecutionStatus.SECURITY_VIOLATION
        assert len(result.security_violations) > 0
        
        # Check that specific violations are detected
        violations_text = " ".join(result.security_violations)
        assert "os" in violations_text.lower()
        assert "subprocess" in violations_text.lower()
        assert "exec" in violations_text.lower()
    
    @pytest.mark.asyncio
    async def test_resource_limit_enforcement(self, service):
        """Test resource limit enforcement"""
        with patch.object(service.container_manager, 'create_container') as mock_create, \
             patch.object(service.container_manager, 'execute_in_container') as mock_execute, \
             patch.object(service.container_manager, 'cleanup_container') as mock_cleanup:
            
            mock_create.return_value = "test-container"
            mock_execute.return_value = ("", "Execution timeout", 124)  # Timeout exit code
            mock_cleanup.return_value = None
            
            from services.secure_code_execution import CodeExecutionRequest
            request = CodeExecutionRequest(
                code="import time; time.sleep(100)",  # Long-running code
                language=ExecutionLanguage.PYTHON,
                resource_limits=ResourceLimits(max_execution_time_seconds=1)  # Very short timeout
            )
            
            result = await service.execute_code(request)
            
            assert result.status == ExecutionStatus.TIMEOUT
            assert "timeout" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_dependency_management_workflow(self, service):
        """Test dependency management workflow"""
        with patch.object(service.dependency_manager, 'install_dependencies') as mock_install, \
             patch.object(service.container_manager, 'create_container') as mock_create, \
             patch.object(service.container_manager, 'execute_in_container') as mock_execute, \
             patch.object(service.container_manager, 'cleanup_container') as mock_cleanup:
            
            mock_install.return_value = ["numpy==1.21.0", "pandas==1.3.0"]
            mock_create.return_value = "test-container"
            mock_execute.return_value = ("Dependencies installed successfully\n", "", 0)
            mock_cleanup.return_value = None
            
            from services.secure_code_execution import CodeExecutionRequest
            request = CodeExecutionRequest(
                code="print('Using installed dependencies')",
                language=ExecutionLanguage.PYTHON,
                dependencies=["numpy==1.21.0", "pandas==1.3.0", "os"]  # Mix of safe and unsafe
            )
            
            result = await service.execute_code(request)
            
            assert result.status == ExecutionStatus.COMPLETED
            assert len(result.dependencies_installed) == 2
            assert "numpy==1.21.0" in result.dependencies_installed
            assert "pandas==1.3.0" in result.dependencies_installed
            assert "os" not in result.dependencies_installed  # Should be filtered out
    
    @pytest.mark.asyncio
    async def test_execution_lifecycle_management(self, service):
        """Test complete execution lifecycle management"""
        # Test execution tracking
        assert len(await service.list_active_executions()) == 0
        
        with patch.object(service.container_manager, 'create_container') as mock_create, \
             patch.object(service.container_manager, 'execute_in_container') as mock_execute, \
             patch.object(service.container_manager, 'cleanup_container') as mock_cleanup:
            
            mock_create.return_value = "test-container"
            mock_execute.return_value = ("Test output\n", "", 0)
            mock_cleanup.return_value = None
            
            from services.secure_code_execution import CodeExecutionRequest
            request = CodeExecutionRequest(
                code="print('Test execution')",
                language=ExecutionLanguage.PYTHON
            )
            
            # Execute code
            result = await service.execute_code(request)
            execution_id = result.execution_id
            
            # Verify execution is tracked
            executions = await service.list_active_executions()
            assert len(executions) == 1
            assert executions[0].execution_id == execution_id
            
            # Retrieve specific execution
            retrieved_result = await service.get_execution_result(execution_id)
            assert retrieved_result is not None
            assert retrieved_result.execution_id == execution_id
            
            # Test cleanup
            await service.cleanup_old_executions(max_age_hours=0)  # Clean all
            executions_after_cleanup = await service.list_active_executions()
            assert len(executions_after_cleanup) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])