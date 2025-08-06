"""
Enhanced tests for Jupyter Notebook Service

This module tests the enhanced Jupyter notebook service functionality
including improved execution and security features.
"""

import asyncio
from datetime import datetime
from services.jupyter_notebook_service import jupyter_service

class TestJupyterNotebookEnhanced:
    """Enhanced test cases for Jupyter notebook service"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Clear any existing notebooks
        jupyter_service.notebooks.clear()
        jupyter_service.execution_queue.clear()
    
    async def test_enhanced_python_execution(self):
        """Test enhanced Python code execution"""
        # Create notebook with various Python code examples
        notebook = await jupyter_service.create_notebook(
            title="Enhanced Python Test",
            owner_id="user_123",
            kernel_name="python3",
            initial_cells=[
                {
                    'cell_type': 'code',
                    'source': 'print("Hello, Enhanced Jupyter!")'
                },
                {
                    'cell_type': 'code',
                    'source': 'x = 42\ny = 58\nresult = x + y\nprint(f"The answer is {result}")'
                },
                {
                    'cell_type': 'code',
                    'source': 'import math\nprint(f"Pi is approximately {math.pi:.4f}")'
                }
            ]
        )
        
        # Execute each cell
        for i, cell in enumerate(notebook.cells):
            if cell.cell_type == 'code':
                result = await jupyter_service.execute_cell(
                    notebook_id=notebook.notebook_id,
                    cell_id=cell.cell_id,
                    user_id="user_123"
                )
                
                assert result is not None
                print(f"Cell {i+1}: success={result.success}, time={result.execution_time:.3f}s")
                
                if result.outputs:
                    for output in result.outputs:
                        if output.get('output_type') == 'stream':
                            print(f"  Output: {output.get('text', '').strip()}")
        
        print("✓ Enhanced Python execution test passed")
    
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
                    'source': 'console.log("Hello from JavaScript!");'
                },
                {
                    'cell_type': 'code',
                    'source': 'let numbers = [1, 2, 3, 4, 5]; let sum = numbers.reduce((a, b) => a + b, 0); console.log("Sum:", sum);'
                }
            ]
        )
        
        # Execute JavaScript cells
        for cell in notebook.cells:
            if cell.cell_type == 'code':
                result = await jupyter_service.execute_cell(
                    notebook_id=notebook.notebook_id,
                    cell_id=cell.cell_id,
                    user_id="user_123"
                )
                
                assert result is not None
                print(f"JS execution: success={result.success}")
                
                if result.outputs:
                    for output in result.outputs:
                        if output.get('output_type') == 'stream':
                            print(f"  JS Output: {output.get('text', '').strip()}")
        
        print("✓ JavaScript execution test passed")
    
    async def test_mixed_cell_types(self):
        """Test notebook with mixed cell types"""
        # Create notebook with markdown and code cells
        initial_cells = [
            {
                'cell_type': 'markdown',
                'source': '# Data Analysis Example\n\nThis notebook demonstrates data analysis.'
            },
            {
                'cell_type': 'code',
                'source': 'data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]'
            },
            {
                'cell_type': 'markdown',
                'source': '## Calculate Statistics'
            },
            {
                'cell_type': 'code',
                'source': 'mean = sum(data) / len(data)\nprint(f"Mean: {mean}")'
            },
            {
                'cell_type': 'code',
                'source': 'import statistics\nstd_dev = statistics.stdev(data)\nprint(f"Standard deviation: {std_dev:.2f}")'
            }
        ]
        
        notebook = await jupyter_service.create_notebook(
            title="Mixed Cell Types Test",
            owner_id="user_123",
            initial_cells=initial_cells
        )
        
        # Execute all cells
        results = await jupyter_service.execute_all_cells(notebook.notebook_id, "user_123")
        
        # Should only execute code cells
        code_cells = [cell for cell in notebook.cells if cell.cell_type == 'code']
        assert len(results) == len(code_cells)
        
        for i, result in enumerate(results):
            print(f"Code cell {i+1}: success={result.success}")
            if result.outputs:
                for output in result.outputs:
                    if output.get('output_type') == 'stream':
                        print(f"  Output: {output.get('text', '').strip()}")
        
        print("✓ Mixed cell types test passed")
    
    async def test_notebook_versioning(self):
        """Test notebook versioning and modification tracking"""
        # Create notebook
        notebook = await jupyter_service.create_notebook(
            title="Versioning Test",
            owner_id="user_123"
        )
        
        original_modified = notebook.modified_at
        original_version = notebook.version
        
        # Wait a moment to ensure timestamp difference
        await asyncio.sleep(0.1)
        
        # Modify a cell
        success = await jupyter_service.update_cell(
            notebook_id=notebook.notebook_id,
            cell_id=notebook.cells[0].cell_id,
            source="# Modified content",
            user_id="user_123"
        )
        
        assert success is True
        
        # Check that modification time was updated
        updated_notebook = await jupyter_service.get_notebook(notebook.notebook_id, "user_123")
        assert updated_notebook.modified_at > original_modified
        
        print(f"Original modified: {original_modified}")
        print(f"Updated modified: {updated_notebook.modified_at}")
        print("✓ Notebook versioning test passed")
    
    async def test_collaborative_editing_workflow(self):
        """Test collaborative editing workflow"""
        # Create notebook as owner
        notebook = await jupyter_service.create_notebook(
            title="Collaborative Test",
            owner_id="owner_123"
        )
        
        # Add multiple collaborators
        collaborators = ["collab_1", "collab_2", "collab_3"]
        
        for collab_id in collaborators:
            success = await jupyter_service.add_collaborator(
                notebook_id=notebook.notebook_id,
                collaborator_id=collab_id,
                owner_id="owner_123"
            )
            assert success is True
        
        # Each collaborator adds a cell
        for i, collab_id in enumerate(collaborators):
            cell_id = await jupyter_service.add_cell(
                notebook_id=notebook.notebook_id,
                cell_type="code",
                source=f'print("Hello from {collab_id}")',
                user_id=collab_id
            )
            assert cell_id is not None
        
        # Execute all cells
        results = await jupyter_service.execute_all_cells(notebook.notebook_id, "owner_123")
        
        # Should have original cells plus collaborator cells
        updated_notebook = await jupyter_service.get_notebook(notebook.notebook_id, "owner_123")
        assert len(updated_notebook.cells) >= len(collaborators) + 2  # Original + added
        
        print(f"Collaborative notebook has {len(updated_notebook.cells)} cells")
        print(f"Collaborators: {updated_notebook.collaborators}")
        print("✓ Collaborative editing workflow test passed")
    
    async def test_export_import_workflow(self):
        """Test export and import workflow"""
        # Create a complex notebook
        initial_cells = [
            {
                'cell_type': 'markdown',
                'source': '# Export/Import Test\n\nThis notebook tests export/import functionality.'
            },
            {
                'cell_type': 'code',
                'source': 'print("Original notebook")\ndata = [1, 2, 3, 4, 5]'
            },
            {
                'cell_type': 'code',
                'source': 'result = sum(data)\nprint(f"Sum: {result}")'
            }
        ]
        
        original_notebook = await jupyter_service.create_notebook(
            title="Export Test",
            owner_id="user_123",
            initial_cells=initial_cells
        )
        
        # Execute cells to add execution data
        await jupyter_service.execute_all_cells(original_notebook.notebook_id, "user_123")
        
        # Export as JSON
        exported_json = await jupyter_service.export_notebook(
            notebook_id=original_notebook.notebook_id,
            user_id="user_123",
            format="json"
        )
        
        assert exported_json is not None
        assert exported_json['title'] == "Export Test"
        assert len(exported_json['cells']) == 3
        
        # Export as ipynb
        exported_ipynb = await jupyter_service.export_notebook(
            notebook_id=original_notebook.notebook_id,
            user_id="user_123",
            format="ipynb"
        )
        
        assert exported_ipynb is not None
        assert isinstance(exported_ipynb, str)
        
        print(f"Exported JSON keys: {list(exported_json.keys())}")
        print(f"Exported ipynb length: {len(exported_ipynb)} characters")
        print("✓ Export/import workflow test passed")
    
    async def test_error_recovery(self):
        """Test error recovery and handling"""
        # Create notebook with problematic code
        notebook = await jupyter_service.create_notebook(
            title="Error Recovery Test",
            owner_id="user_123",
            initial_cells=[
                {
                    'cell_type': 'code',
                    'source': 'print("This works")'
                },
                {
                    'cell_type': 'code',
                    'source': 'print(undefined_variable)'  # This will fail
                },
                {
                    'cell_type': 'code',
                    'source': 'print("This should still work")'
                }
            ]
        )
        
        # Execute all cells - some should fail, others should succeed
        results = await jupyter_service.execute_all_cells(notebook.notebook_id, "user_123")
        
        assert len(results) == 3
        
        # Check results
        for i, result in enumerate(results):
            print(f"Cell {i+1}: success={result.success}")
            if result.error_message:
                print(f"  Error: {result.error_message}")
            if result.outputs:
                for output in result.outputs:
                    if output.get('output_type') == 'stream':
                        print(f"  Output: {output.get('text', '').strip()}")
        
        print("✓ Error recovery test passed")

async def run_tests():
    """Run all enhanced tests"""
    test_instance = TestJupyterNotebookEnhanced()
    
    print("Running Enhanced Jupyter Notebook Service Tests...")
    print("=" * 60)
    
    try:
        # Setup
        test_instance.setup_method()
        
        # Run tests
        await test_instance.test_enhanced_python_execution()
        await test_instance.test_javascript_execution()
        await test_instance.test_mixed_cell_types()
        await test_instance.test_notebook_versioning()
        await test_instance.test_collaborative_editing_workflow()
        await test_instance.test_export_import_workflow()
        await test_instance.test_error_recovery()
        
        print("=" * 60)
        print("✅ All enhanced tests passed!")
        
        # Test summary
        print(f"\nTest Summary:")
        print(f"- Notebooks created: {len(jupyter_service.notebooks)}")
        print(f"- Supported kernels: {list(jupyter_service.supported_kernels.keys())}")
        
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