"""
Test suite for Secure Code Execution Service

Tests the containerized code execution with security sandboxing,
dependency management, resource limits, and security scanning.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from services.secure_code_execution import (
    SecureCodeExecutionService,
    CodeExecutionRequest,
    ExecutionResult,
    ExecutionLanguage,
    ExecutionStatus,
    ResourceLimits,
    SecurityPolicy,
    SecurityScanner,
    DependencyManager,
    ContainerManager
)

class TestSecurityScanner:
    """Test security scanning functionality"""
    
    def setup_method(self):
        self.scanner = SecurityScanner()
        self.security_policy = SecurityPolicy()
    
    @pytest.mark.asyncio
    async def test_scan_python_safe_code(self):
        """Test scanning safe Python code"""
        safe_code = """
import math
import numpy as np

def calculate_mean(numbers):
    return sum(numbers) / len(numbers)

result = calculate_mean([1, 2, 3, 4, 5])
print(f"Mean: {result}")
"""
        
        violations = await self.scanner.scan_python_code(safe_code, self.security_policy)
        assert len(violations) == 0
    
    @pytest.mark.asyncio
    async def test_scan_python_dangerous_code(self):
        """Test scanning dangerous Python code"""
        dangerous_code = """
import os
import subprocess

# Dangerous operations
os.system("rm -rf /")
subprocess.call(["curl", "malicious-site.com"])
exec("malicious_code")
eval("dangerous_eval")
"""
        
        violations = await self.scanner.scan_python_code(dangerous_code, self.security_policy)
        assert len(violations) > 0
        
        # Check for specific violations
        violation_text = " ".join(violations)
        assert "os" in violation_text.lower()
        assert "subprocess" in violation_text.lower()
        assert "exec" in violation_text.lower()
        assert "eval" in violation_text.lower()
    
    @pytest.mark.asyncio
    async def test_scan_javascript_safe_code(self):
        """Test scanning safe JavaScript code"""
        safe_code = """
function fibonacci(n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

console.log(fibonacci(10));
"""
        
        violations = await self.scanner.scan_javascript_code(safe_code, self.security_policy)
        assert len(violations) == 0
    
    @pytest.mark.asyncio
    async def test_scan_javascript_dangerous_code(self):
        """Test scanning dangerous JavaScript code"""
        dangerous_code = """
const fs = require('fs');
const child_process = require('child_process');

eval('malicious code');
setTimeout('dangerous code', 1000);
child_process.exec('rm -rf /');
"""
        
        violations = await self.scanner.scan_javascript_code(dangerous_code, self.security_policy)
        assert len(violations) > 0
        
        violation_text = " ".join(violations)
        assert "eval" in violation_text.lower()
        assert "child_process" in violation_text.lower()
    
    @pytest.mark.asyncio
    async def test_scan_syntax_error(self):
        """Test handling of syntax errors in code"""
        invalid_code = """
def invalid_function(
    # Missing closing parenthesis and colon
    print("This will cause a syntax error"
"""
        
        violations = await self.scanner.scan_python_code(invalid_code, self.security_policy)
        assert len(violations) > 0
        assert any("syntax error" in v.lower() for v in violations)

class TestDependencyManager:
    """Test dependency management functionality"""
    
    def setup_method(self):
        self.dependency_manager = DependencyManager()
    
    @pytest.mark.asyncio
    async def test_validate_safe_python_dependencies(self):
        """Test validation of safe Python dependencies"""
        safe_deps = ["numpy==1.21.0", "pandas>=1.3.0", "matplotlib", "scipy"]
        
        validated = await self.dependency_manager.validate_dependencies(
            safe_deps, ExecutionLanguage.PYTHON
        )
        
        assert len(validated) == len(safe_deps)
        assert all(dep in validated for dep in safe_deps)
    
    @pytest.mark.asyncio
    async def test_validate_dangerous_python_dependencies(self):
        """Test filtering of dangerous Python dependencies"""
        mixed_deps = [
            "numpy==1.21.0",  # Safe
            "os",  # Dangerous
            "pandas>=1.3.0",  # Safe
            "subprocess",  # Dangerous
            "requests"  # Dangerous
        ]
        
        validated = await self.dependency_manager.validate_dependencies(
            mixed_deps, ExecutionLanguage.PYTHON
        )
        
        # Should only contain safe dependencies
        assert "numpy==1.21.0" in validated
        assert "pandas>=1.3.0" in validated
        assert "os" not in validated
        assert "subprocess" not in validated
        assert "requests" not in validated
    
    @pytest.mark.asyncio
    async def test_validate_javascript_dependencies(self):
        """Test validation of JavaScript dependencies"""
        safe_deps = ["lodash", "moment", "axios"]
        dangerous_deps = ["fs", "child_process", "net"]
        
        safe_validated = await self.dependency_manager.validate_dependencies(
            safe_deps, ExecutionLanguage.JAVASCRIPT
        )
        dangerous_validated = await self.dependency_manager.validate_dependencies(
            dangerous_deps, ExecutionLanguage.JAVASCRIPT
        )
        
        assert len(safe_validated) == len(safe_deps)
        assert len(dangerous_validated) == 0
    
    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_shell')
    async def test_install_python_dependencies_success(self, mock_subprocess):
        """Test successful Python dependency installation"""
        # Mock successful subprocess execution
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(b"Successfully installed numpy", b""))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process
        
        dependencies = ["numpy==1.21.0"]
        container_name = "test-container"
        
        installed = await self.dependency_manager.install_dependencies(
            dependencies, ExecutionLanguage.PYTHON, container_name
        )
        
        assert len(installed) == 1
        assert "numpy==1.21.0" in installed
        mock_subprocess.assert_called()
    
    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_shell')
    async def test_install_python_dependencies_failure(self, mock_subprocess):
        """Test failed Python dependency installation"""
        # Mock failed subprocess execution
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(b"", b"Package not found"))
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process
        
        dependencies = ["nonexistent-package"]
        container_name = "test-container"
        
        installed = await self.dependency_manager.install_dependencies(
            dependencies, ExecutionLanguage.PYTHON, container_name
        )
        
        assert len(installed) == 0

class TestContainerManager:
    """Test container management functionality"""
    
    def setup_method(self):
        self.container_manager = ContainerManager()
        self.resource_limits = ResourceLimits()
        self.security_policy = SecurityPolicy()
    
    @patch('docker.from_env')
    def test_container_manager_initialization(self, mock_docker):
        """Test container manager initialization"""
        mock_client = Mock()
        mock_docker.return_value = mock_client
        
        manager = ContainerManager()
        assert manager.docker_client == mock_client
    
    @patch('docker.from_env')
    def test_container_manager_initialization_failure(self, mock_docker):
        """Test container manager initialization failure"""
        mock_docker.side_effect = Exception("Docker not available")
        
        manager = ContainerManager()
        assert manager.docker_client is None
    
    @pytest.mark.asyncio
    @patch('docker.from_env')
    async def test_create_container_success(self, mock_docker):
        """Test successful container creation"""
        # Mock Docker client and container
        mock_container = Mock()
        mock_client = Mock()
        mock_client.containers.run.return_value = mock_container
        mock_docker.return_value = mock_client
        
        manager = ContainerManager()
        
        container_name = await manager.create_container(
            ExecutionLanguage.PYTHON, self.resource_limits, self.security_policy
        )
        
        assert container_name is not None
        assert container_name.startswith("code-exec-")
        mock_client.containers.run.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('docker.from_env')
    async def test_create_container_failure(self, mock_docker):
        """Test container creation failure"""
        mock_client = Mock()
        mock_client.containers.run.side_effect = Exception("Container creation failed")
        mock_docker.return_value = mock_client
        
        manager = ContainerManager()
        
        container_name = await manager.create_container(
            ExecutionLanguage.PYTHON, self.resource_limits, self.security_policy
        )
        
        assert container_name is None
    
    @pytest.mark.asyncio
    @patch('docker.from_env')
    async def test_execute_in_container_success(self, mock_docker):
        """Test successful command execution in container"""
        # Mock container execution
        mock_result = Mock()
        mock_result.output = b"Hello, World!"
        mock_result.exit_code = 0
        
        mock_container = Mock()
        mock_container.exec_run.return_value = mock_result
        
        mock_client = Mock()
        mock_client.containers.get.return_value = mock_container
        mock_docker.return_value = mock_client
        
        manager = ContainerManager()
        
        stdout, stderr, exit_code = await manager.execute_in_container(
            "test-container", "echo 'Hello, World!'", 30
        )
        
        assert stdout == "Hello, World!"
        assert stderr == ""
        assert exit_code == 0
    
    @pytest.mark.asyncio
    @patch('docker.from_env')
    async def test_execute_in_container_timeout(self, mock_docker):
        """Test command execution timeout"""
        mock_client = Mock()
        mock_container = Mock()
        mock_container.exec_run.side_effect = Exception("timeout")
        mock_client.containers.get.return_value = mock_container
        mock_docker.return_value = mock_client
        
        manager = ContainerManager()
        
        stdout, stderr, exit_code = await manager.execute_in_container(
            "test-container", "sleep 100", 1
        )
        
        assert "timeout" in stderr.lower()
        assert exit_code == 124
    
    @pytest.mark.asyncio
    @patch('docker.from_env')
    async def test_cleanup_container(self, mock_docker):
        """Test container cleanup"""
        mock_container = Mock()
        mock_client = Mock()
        mock_client.containers.get.return_value = mock_container
        mock_docker.return_value = mock_client
        
        manager = ContainerManager()
        
        await manager.cleanup_container("test-container")
        
        mock_container.stop.assert_called_once_with(timeout=5)
        mock_container.remove.assert_called_once()

class TestSecureCodeExecutionService:
    """Test the main secure code execution service"""
    
    def setup_method(self):
        self.service = SecureCodeExecutionService()
    
    @pytest.mark.asyncio
    @patch.object(SecurityScanner, 'scan_code')
    @patch.object(DependencyManager, 'validate_dependencies')
    @patch.object(ContainerManager, 'create_container')
    @patch.object(ContainerManager, 'execute_in_container')
    @patch.object(ContainerManager, 'cleanup_container')
    async def test_execute_safe_python_code(self, mock_cleanup, mock_execute, 
                                          mock_create, mock_validate, mock_scan):
        """Test execution of safe Python code"""
        # Mock all dependencies
        mock_scan.return_value = []  # No security violations
        mock_validate.return_value = ["numpy"]
        mock_create.return_value = "test-container"
        mock_execute.return_value = ("42\n", "", 0)
        mock_cleanup.return_value = None
        
        request = CodeExecutionRequest(
            code="print(6 * 7)",
            language=ExecutionLanguage.PYTHON,
            dependencies=["numpy"]
        )
        
        result = await self.service.execute_code(request)
        
        assert result.status == ExecutionStatus.COMPLETED
        assert "42" in result.output
        assert result.error is None
        assert len(result.security_violations) == 0
        
        # Verify all mocks were called
        mock_scan.assert_called_once()
        mock_validate.assert_called_once()
        mock_create.assert_called_once()
        mock_execute.assert_called_once()
        mock_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    @patch.object(SecurityScanner, 'scan_code')
    async def test_execute_code_security_violation(self, mock_scan):
        """Test execution blocked by security violations"""
        mock_scan.return_value = ["Blocked import: os", "Dangerous pattern: exec("]
        
        request = CodeExecutionRequest(
            code="import os; exec('malicious code')",
            language=ExecutionLanguage.PYTHON
        )
        
        result = await self.service.execute_code(request)
        
        assert result.status == ExecutionStatus.SECURITY_VIOLATION
        assert len(result.security_violations) == 2
        assert "Blocked import: os" in result.security_violations
        assert "Dangerous pattern: exec(" in result.security_violations
    
    @pytest.mark.asyncio
    @patch.object(SecurityScanner, 'scan_code')
    @patch.object(DependencyManager, 'validate_dependencies')
    @patch.object(ContainerManager, 'create_container')
    async def test_execute_code_container_creation_failure(self, mock_create, 
                                                         mock_validate, mock_scan):
        """Test handling of container creation failure"""
        mock_scan.return_value = []
        mock_validate.return_value = []
        mock_create.return_value = None  # Container creation failed
        
        request = CodeExecutionRequest(
            code="print('Hello')",
            language=ExecutionLanguage.PYTHON
        )
        
        result = await self.service.execute_code(request)
        
        assert result.status == ExecutionStatus.FAILED
        assert "Failed to create secure execution environment" in result.error
    
    @pytest.mark.asyncio
    @patch.object(SecurityScanner, 'scan_code')
    @patch.object(DependencyManager, 'validate_dependencies')
    @patch.object(ContainerManager, 'create_container')
    @patch.object(ContainerManager, 'execute_in_container')
    @patch.object(ContainerManager, 'cleanup_container')
    async def test_execute_code_timeout(self, mock_cleanup, mock_execute, 
                                      mock_create, mock_validate, mock_scan):
        """Test execution timeout handling"""
        mock_scan.return_value = []
        mock_validate.return_value = []
        mock_create.return_value = "test-container"
        mock_execute.return_value = ("", "Execution timeout", 124)
        mock_cleanup.return_value = None
        
        request = CodeExecutionRequest(
            code="import time; time.sleep(100)",
            language=ExecutionLanguage.PYTHON,
            resource_limits=ResourceLimits(max_execution_time_seconds=1)
        )
        
        result = await self.service.execute_code(request)
        
        assert result.status == ExecutionStatus.TIMEOUT
        assert result.error == "Execution timeout"
    
    @pytest.mark.asyncio
    async def test_get_execution_result(self):
        """Test retrieving execution results"""
        # Create a mock result
        mock_result = ExecutionResult(
            execution_id="test-123",
            status=ExecutionStatus.COMPLETED,
            output="Test output"
        )
        
        self.service.active_executions["test-123"] = mock_result
        
        result = await self.service.get_execution_result("test-123")
        assert result == mock_result
        
        # Test non-existent result
        result = await self.service.get_execution_result("non-existent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_active_executions(self):
        """Test listing active executions"""
        # Add some mock results
        result1 = ExecutionResult("test-1", ExecutionStatus.COMPLETED, "Output 1")
        result2 = ExecutionResult("test-2", ExecutionStatus.RUNNING, "")
        
        self.service.active_executions["test-1"] = result1
        self.service.active_executions["test-2"] = result2
        
        results = await self.service.list_active_executions()
        
        assert len(results) == 2
        assert result1 in results
        assert result2 in results
    
    @pytest.mark.asyncio
    async def test_cancel_execution(self):
        """Test cancelling an active execution"""
        # Add a running execution
        result = ExecutionResult("test-123", ExecutionStatus.RUNNING, "")
        self.service.active_executions["test-123"] = result
        
        success = await self.service.cancel_execution("test-123")
        assert success is True
        assert result.status == ExecutionStatus.FAILED
        assert "cancelled" in result.error.lower()
        
        # Test cancelling non-existent execution
        success = await self.service.cancel_execution("non-existent")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_cleanup_old_executions(self):
        """Test cleanup of old execution results"""
        # Add old and new results
        old_result = ExecutionResult("old-123", ExecutionStatus.COMPLETED, "Old")
        old_result.created_at = datetime.utcnow() - timedelta(hours=25)
        
        new_result = ExecutionResult("new-123", ExecutionStatus.COMPLETED, "New")
        new_result.created_at = datetime.utcnow() - timedelta(hours=1)
        
        self.service.active_executions["old-123"] = old_result
        self.service.active_executions["new-123"] = new_result
        
        await self.service.cleanup_old_executions(max_age_hours=24)
        
        # Old result should be removed, new result should remain
        assert "old-123" not in self.service.active_executions
        assert "new-123" in self.service.active_executions

class TestResourceLimits:
    """Test resource limits functionality"""
    
    def test_default_resource_limits(self):
        """Test default resource limits"""
        limits = ResourceLimits()
        
        assert limits.max_memory_mb == 512
        assert limits.max_cpu_percent == 50.0
        assert limits.max_execution_time_seconds == 30
        assert limits.max_disk_usage_mb == 100
        assert limits.max_network_requests == 10
    
    def test_custom_resource_limits(self):
        """Test custom resource limits"""
        limits = ResourceLimits(
            max_memory_mb=1024,
            max_cpu_percent=75.0,
            max_execution_time_seconds=60,
            max_disk_usage_mb=200,
            max_network_requests=20
        )
        
        assert limits.max_memory_mb == 1024
        assert limits.max_cpu_percent == 75.0
        assert limits.max_execution_time_seconds == 60
        assert limits.max_disk_usage_mb == 200
        assert limits.max_network_requests == 20

class TestSecurityPolicy:
    """Test security policy functionality"""
    
    def test_default_security_policy(self):
        """Test default security policy"""
        policy = SecurityPolicy()
        
        assert policy.allow_network_access is False
        assert policy.allow_file_system_access is False
        assert policy.allow_subprocess_execution is False
        assert 'os' in policy.blocked_imports
        assert 'subprocess' in policy.blocked_imports
        assert 'exec' in policy.blocked_functions
        assert 'eval' in policy.blocked_functions
    
    def test_custom_security_policy(self):
        """Test custom security policy"""
        policy = SecurityPolicy(
            allow_network_access=True,
            allow_file_system_access=True,
            blocked_imports=['custom_blocked'],
            blocked_functions=['custom_function']
        )
        
        assert policy.allow_network_access is True
        assert policy.allow_file_system_access is True
        assert policy.blocked_imports == ['custom_blocked']
        assert policy.blocked_functions == ['custom_function']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])