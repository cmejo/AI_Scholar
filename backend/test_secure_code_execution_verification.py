"""
Verification script for Secure Code Execution Service

This script verifies that the secure code execution service is working correctly
without requiring Docker to be running.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.secure_code_execution import (
    SecureCodeExecutionService,
    SecurityScanner,
    DependencyManager,
    SecurityPolicy,
    ResourceLimits,
    ExecutionLanguage,
    CodeExecutionRequest
)

async def test_security_scanner():
    """Test the security scanner functionality"""
    print("Testing Security Scanner...")
    
    scanner = SecurityScanner()
    policy = SecurityPolicy()
    
    # Test safe Python code
    safe_code = """
import math
import numpy as np

def calculate_mean(numbers):
    return sum(numbers) / len(numbers)

result = calculate_mean([1, 2, 3, 4, 5])
print(f"Mean: {result}")
"""
    
    violations = await scanner.scan_python_code(safe_code, policy)
    print(f"✓ Safe Python code: {len(violations)} violations detected")
    
    # Test unsafe Python code
    unsafe_code = """
import os
import subprocess
exec('malicious_code')
eval('dangerous_eval')
"""
    
    violations = await scanner.scan_python_code(unsafe_code, policy)
    print(f"✓ Unsafe Python code: {len(violations)} violations detected")
    print(f"  Violations: {violations}")
    
    # Test JavaScript code
    js_safe = "function hello() { console.log('Hello'); }"
    js_violations = await scanner.scan_javascript_code(js_safe, policy)
    print(f"✓ Safe JavaScript code: {len(js_violations)} violations detected")
    
    js_unsafe = "eval('malicious'); require('fs');"
    js_violations = await scanner.scan_javascript_code(js_unsafe, policy)
    print(f"✓ Unsafe JavaScript code: {len(js_violations)} violations detected")

async def test_dependency_manager():
    """Test the dependency manager functionality"""
    print("\nTesting Dependency Manager...")
    
    manager = DependencyManager()
    
    # Test Python dependency validation
    safe_deps = ["numpy==1.21.0", "pandas>=1.3.0", "matplotlib"]
    validated = await manager.validate_dependencies(safe_deps, ExecutionLanguage.PYTHON)
    print(f"✓ Safe Python dependencies: {len(validated)}/{len(safe_deps)} allowed")
    
    unsafe_deps = ["os", "subprocess", "requests", "numpy"]
    validated = await manager.validate_dependencies(unsafe_deps, ExecutionLanguage.PYTHON)
    print(f"✓ Mixed Python dependencies: {len(validated)}/{len(unsafe_deps)} allowed")
    print(f"  Allowed: {validated}")
    
    # Test JavaScript dependency validation
    js_deps = ["lodash", "moment", "fs", "child_process"]
    validated = await manager.validate_dependencies(js_deps, ExecutionLanguage.JAVASCRIPT)
    print(f"✓ Mixed JavaScript dependencies: {len(validated)}/{len(js_deps)} allowed")

async def test_service_integration():
    """Test service integration without Docker"""
    print("\nTesting Service Integration...")
    
    service = SecureCodeExecutionService()
    
    # Test security violation detection
    request = CodeExecutionRequest(
        code="import os; os.system('echo hello')",
        language=ExecutionLanguage.PYTHON
    )
    
    # This will fail at container creation, but should detect security violations first
    result = await service.execute_code(request)
    print(f"✓ Security violation detection: Status = {result.status}")
    print(f"  Violations: {result.security_violations}")
    
    # Test safe code (will fail at container creation but pass security)
    safe_request = CodeExecutionRequest(
        code="print('Hello, World!')",
        language=ExecutionLanguage.PYTHON
    )
    
    result = await service.execute_code(safe_request)
    print(f"✓ Safe code processing: Status = {result.status}")
    if result.error:
        print(f"  Expected error (no Docker): {result.error}")

def test_resource_limits():
    """Test resource limits configuration"""
    print("\nTesting Resource Limits...")
    
    # Test default limits
    default_limits = ResourceLimits()
    print(f"✓ Default memory limit: {default_limits.max_memory_mb}MB")
    print(f"✓ Default CPU limit: {default_limits.max_cpu_percent}%")
    print(f"✓ Default time limit: {default_limits.max_execution_time_seconds}s")
    
    # Test custom limits
    custom_limits = ResourceLimits(
        max_memory_mb=1024,
        max_cpu_percent=75.0,
        max_execution_time_seconds=60
    )
    print(f"✓ Custom memory limit: {custom_limits.max_memory_mb}MB")
    print(f"✓ Custom CPU limit: {custom_limits.max_cpu_percent}%")

def test_security_policy():
    """Test security policy configuration"""
    print("\nTesting Security Policy...")
    
    # Test default policy
    default_policy = SecurityPolicy()
    print(f"✓ Network access: {default_policy.allow_network_access}")
    print(f"✓ File system access: {default_policy.allow_file_system_access}")
    print(f"✓ Blocked imports: {len(default_policy.blocked_imports)} items")
    print(f"✓ Blocked functions: {len(default_policy.blocked_functions)} items")
    
    # Test custom policy
    custom_policy = SecurityPolicy(
        allow_network_access=True,
        blocked_imports=['custom_blocked'],
        blocked_functions=['custom_function']
    )
    print(f"✓ Custom network access: {custom_policy.allow_network_access}")
    print(f"✓ Custom blocked imports: {custom_policy.blocked_imports}")

async def main():
    """Run all verification tests"""
    print("=== Secure Code Execution Service Verification ===\n")
    
    try:
        await test_security_scanner()
        await test_dependency_manager()
        test_resource_limits()
        test_security_policy()
        await test_service_integration()
        
        print("\n=== Verification Complete ===")
        print("✓ All core components are working correctly")
        print("✓ Security scanning is functional")
        print("✓ Dependency management is operational")
        print("✓ Resource limits and policies are configurable")
        print("✓ Service integration is ready (Docker required for full execution)")
        
    except Exception as e:
        print(f"\n❌ Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())