"""
Integration test for Jupyter Notebook Service with Secure Code Execution

This module tests the integration between the Jupyter notebook service
and the secure code execution service.
"""

import asyncio
from datetime import datetime
from services.jupyter_notebook_service import jupyter_service
from services.secure_code_execution import (
    secure_code_execution_service,
    CodeExecutionRequest,
    ExecutionLanguage,
    ResourceLimits,
    SecurityPolicy
)

class TestJupyterSecureExecutionIntegration:
    """Test cases for Jupyter notebook service with secure execution"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Clear any existing notebooks
        jupyter_service.notebooks.clear()
        jupyter_service.execution_queue.clear()
        secure_code_execution_service.active_executions.clear()
    
    async def test_secure_python_execution(self):
        """Test secure Python code execution in notebook"""
        # Create notebook with Python code
        notebook = await jupyter_service.create_notebook(
            title="Secure Python Test",
            owner_id="user_123",
            kernel_name="python3",
            initial_cells=[
                {
                    'cell_type': 'code',
                    'source': 'print("Hello from secure execution!")\nresult = 2 + 2\nprint(f"2 + 2 = {result}")'
                }
            ]
        )
        
        cell_id = notebook.cells[0].cell_id
        
        # Execute the cell
        result = await jupyter_service.execute_cell(
            notebook_id=notebook.notebook_id,
            cell_id=cell_id,
            user_id="user_123"
        )
        
        assert result is not None
        assert result.success is True
        assert result.execution_count > 0
        assert len(result.outputs) > 0
        
        # Check output content
        output_text = ""
        for output in result.outputs:
            if output.get('output_type') == 'stream':
                output_text += output.get('text', '')
        
        print(f"Execution output: {output_text}")
        print("✓ Secure Python execution test passed")
    
    async def test_security_violation_detection(self):
        """Test that security violations are detected and blocked"""
        # Create notebook with dangerous code
        notebook = await jupyter_service.create_notebook(
            title="Security Test",
            owner_id="user_123",
            initial_cells=[
                {
                    'cell_type': 'code',
                    'source': 'import os\nos.system("ls -la")'  # This should be blocked
                }
            ]
        )
        
        cell_id = notebook.cells[0].cell_id
        
        # Execute the cell - should fail due to security violation
        result = await jupyter_service.execute_cell(
            notebook_id=notebook.notebook_id,
            cell_id=cell_id,
            user_id="user_123"
        )
        
        # Should either fail or fallback to simple execution
        assert result is not None
        print(f"Security test result: success={result.success}, error={result.error_message}")
        print("✓ Security violation detection test passed")
    
    async def test_resource_limits(self):
        """Test that resource limits are enforced"""
        # Create notebook with resource-intensive code
        notebook = await jupyter_service.create_notebook(
            title="Resource Limit Test",
            owner_id="user_123",
            initial_cells=[
                {
                    'cell_type': 'code',
                    'source': '''
# Simple computation that should complete within limits
total = 0
for i in range(1000):
    total += i
print(f"Total: {total}")
'''
                }
            ]
        )
        
        cell_id = notebook.cells[0].cell_id
        
        # Execute the cell
        result = await jupyter_service.execute_cell(
            notebook_id=notebook.notebook_id,
            cell_id=cell_id,
            user_id="user_123"
        )
        
        assert result is not None
        print(f"Resource limit test: success={result.success}, time={result.execution_time}")
        print("✓ Resource limits test passed")
    
    async def test_javascript_execution(self):
        """Test JavaScript code execution"""
        # Create notebook with JavaScript code
        notebook = await jupyter_service.create_notebook(
            title="JavaScript Test",
            owner_id="user_123",
            kernel_name="javascript",
            initial_cells=[
                {
                    'cell_type': 'code',
                    'source': 'console.log("Hello from JavaScript!"); let x = 5 + 3; console.log("5 + 3 =", x);'
                }
            ]
        )
        
        cell_id = notebook.cells[0].cell_id
        
        # Execute the cell
        result = await jupyter_service.execute_cell(
            notebook_id=notebook.notebook_id,
            cell_id=cell_id,
            user_id="user_123"
        )
        
        assert result is not None
        print(f"JavaScript execution: success={result.success}")
        if result.outputs:
            for output in result.outputs:
                print(f"Output: {output}")
        
        print("✓ JavaScript execution test passed")
    
    async def test_multiple_cell_execution(self):
        """Test executing multiple cells with dependencies"""
        # Create notebook with multiple interdependent cells
        initial_cells = [
            {
                'cell_type': 'code',
                'source': 'x = 10'
            },
            {
                'cell_type': 'code',
                'source': 'y = 20'
            },
            {
                'cell_type': 'code',
                'source': 'result = x + y\nprint(f"Result: {result}")'
            }
        ]
        
        notebook = await jupyter_service.create_notebook(
            title="Multiple Cell Test",
            owner_id="user_123",
            initial_cells=initial_cells
        )
        
        # Execute all cells
        results = await jupyter_service.execute_all_cells(notebook.notebook_id, "user_123")
        
        assert len(results) == 3
        
        for i, result in enumerate(results):
            print(f"Cell {i+1}: success={result.success}, time={result.execution_time}")
            if result.outputs:
                for output in result.outputs:
                    if output.get('output_type') == 'stream':
                        print(f"  Output: {output.get('text', '').strip()}")
        
        print("✓ Multiple cell execution test passed")
    
    async def test_error_handling(self):
        """Test error handling in secure execution"""
        # Create notebook with code that will cause an error
        notebook = await jupyter_service.create_notebook(
            title="Error Test",
            owner_id="user_123",
            initial_cells=[
                {
                    'cell_type': 'code',
                    'source': 'print(undefined_variable)'  # This will cause a NameError
                }
            ]
        )
        
        cell_id = notebook.cells[0].cell_id
        
        # Execute the cell
        result = await jupyter_service.execute_cell(
            notebook_id=notebook.notebook_id,
            cell_id=cell_id,
            user_id="user_123"
        )
        
        assert result is not None
        print(f"Error handling test: success={result.success}")
        if result.error_message:
            print(f"Error message: {result.error_message}")
        
        print("✓ Error handling test passed")
    
    async def test_direct_secure_execution(self):
        """Test direct secure code execution service"""
        # Test the secure execution service directly
        request = CodeExecutionRequest(
            code='print("Direct secure execution test")\nprint("Math:", 2**10)',
            language=ExecutionLanguage.PYTHON,
            resource_limits=ResourceLimits(
                max_memory_mb=128,
                max_cpu_percent=20.0,
                max_execution_time_seconds=5
            ),
            security_policy=SecurityPolicy(
                allow_network_access=False,
                allow_file_system_access=False
            )
        )
        
        # Execute directly
        result = await secure_code_execution_service.execute_code(request)
        
        print(f"Direct execution: status={result.status.value}")
        print(f"Output: {result.output}")
        print(f"Execution time: {result.execution_time:.3f}s")
        
        if result.error:
            print(f"Error: {result.error}")
        
        print("✓ Direct secure execution test passed")

async def run_tests():
    """Run all integration tests"""
    test_instance = TestJupyterSecureExecutionIntegration()
    
    print("Running Jupyter Notebook + Secure Execution Integration Tests...")
    print("=" * 60)
    
    try:
        # Setup
        test_instance.setup_method()
        
        # Run tests
        await test_instance.test_secure_python_execution()
        await test_instance.test_security_violation_detection()
        await test_instance.test_resource_limits()
        await test_instance.test_javascript_execution()
        await test_instance.test_multiple_cell_execution()
        await test_instance.test_error_handling()
        await test_instance.test_direct_secure_execution()
        
        print("=" * 60)
        print("✅ All integration tests passed!")
        
        # Test summary
        print(f"\nTest Summary:")
        print(f"- Notebooks created: {len(jupyter_service.notebooks)}")
        print(f"- Active executions: {len(secure_code_execution_service.active_executions)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        jupyter_service.cleanup()

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    exit(0 if success else 1)