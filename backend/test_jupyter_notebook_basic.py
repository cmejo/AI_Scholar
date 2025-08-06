"""
Basic tests for Jupyter Notebook Service

This module tests the core functionality of the Jupyter notebook service
including notebook creation, cell management, execution, and collaboration.
"""

import asyncio
from datetime import datetime
from services.jupyter_notebook_service import jupyter_service, NotebookData, NotebookCell

class TestJupyterNotebookService:
    """Test cases for Jupyter notebook service"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Clear any existing notebooks
        jupyter_service.notebooks.clear()
        jupyter_service.execution_queue.clear()
    
    async def test_create_notebook(self):
        """Test notebook creation"""
        # Test basic notebook creation
        notebook = await jupyter_service.create_notebook(
            title="Test Notebook",
            owner_id="user_123"
        )
        
        assert notebook is not None
        assert notebook.title == "Test Notebook"
        assert notebook.owner_id == "user_123"
        assert len(notebook.cells) == 2  # Default markdown and code cells
        assert notebook.cells[0].cell_type == "markdown"
        assert notebook.cells[1].cell_type == "code"
        assert notebook.notebook_id in jupyter_service.notebooks
        
        print("✓ Notebook creation test passed")
    
    async def test_create_notebook_with_custom_cells(self):
        """Test notebook creation with custom initial cells"""
        initial_cells = [
            {
                'cell_type': 'markdown',
                'source': '# Custom Notebook'
            },
            {
                'cell_type': 'code',
                'source': 'print("Custom code")'
            },
            {
                'cell_type': 'code',
                'source': 'x = 42\nprint(x)'
            }
        ]
        
        notebook = await jupyter_service.create_notebook(
            title="Custom Notebook",
            owner_id="user_123",
            initial_cells=initial_cells
        )
        
        assert len(notebook.cells) == 3
        assert notebook.cells[0].source == "# Custom Notebook"
        assert notebook.cells[1].source == 'print("Custom code")'
        assert notebook.cells[2].source == "x = 42\nprint(x)"
        
        print("✓ Custom notebook creation test passed")
    
    async def test_get_notebook_access_control(self):
        """Test notebook access control"""
        # Create notebook as user_123
        notebook = await jupyter_service.create_notebook(
            title="Private Notebook",
            owner_id="user_123"
        )
        
        # Owner should have access
        retrieved = await jupyter_service.get_notebook(notebook.notebook_id, "user_123")
        assert retrieved is not None
        assert retrieved.notebook_id == notebook.notebook_id
        
        # Non-owner should not have access
        retrieved = await jupyter_service.get_notebook(notebook.notebook_id, "user_456")
        assert retrieved is None
        
        # Add collaborator
        await jupyter_service.add_collaborator(notebook.notebook_id, "user_456", "user_123")
        
        # Collaborator should now have access
        retrieved = await jupyter_service.get_notebook(notebook.notebook_id, "user_456")
        assert retrieved is not None
        
        print("✓ Access control test passed")
    
    async def test_cell_management(self):
        """Test cell addition, update, and deletion"""
        # Create notebook
        notebook = await jupyter_service.create_notebook(
            title="Cell Test Notebook",
            owner_id="user_123"
        )
        
        initial_cell_count = len(notebook.cells)
        
        # Add a new cell
        cell_id = await jupyter_service.add_cell(
            notebook_id=notebook.notebook_id,
            cell_type="code",
            source="print('New cell')",
            user_id="user_123"
        )
        
        assert cell_id is not None
        updated_notebook = await jupyter_service.get_notebook(notebook.notebook_id, "user_123")
        assert len(updated_notebook.cells) == initial_cell_count + 1
        
        # Update the cell
        success = await jupyter_service.update_cell(
            notebook_id=notebook.notebook_id,
            cell_id=cell_id,
            source="print('Updated cell')",
            user_id="user_123"
        )
        
        assert success is True
        updated_notebook = await jupyter_service.get_notebook(notebook.notebook_id, "user_123")
        updated_cell = next(cell for cell in updated_notebook.cells if cell.cell_id == cell_id)
        assert updated_cell.source == "print('Updated cell')"
        
        # Delete the cell
        success = await jupyter_service.delete_cell(
            notebook_id=notebook.notebook_id,
            cell_id=cell_id,
            user_id="user_123"
        )
        
        assert success is True
        updated_notebook = await jupyter_service.get_notebook(notebook.notebook_id, "user_123")
        assert len(updated_notebook.cells) == initial_cell_count
        
        print("✓ Cell management test passed")
    
    async def test_cell_execution(self):
        """Test cell execution"""
        # Create notebook with code cell
        notebook = await jupyter_service.create_notebook(
            title="Execution Test",
            owner_id="user_123",
            initial_cells=[
                {
                    'cell_type': 'code',
                    'source': 'print("Hello, World!")'
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
        
        # Check that cell state was updated
        updated_notebook = await jupyter_service.get_notebook(notebook.notebook_id, "user_123")
        executed_cell = updated_notebook.cells[0]
        assert executed_cell.execution_state == "completed"
        assert executed_cell.execution_count is not None
        
        print("✓ Cell execution test passed")
    
    async def test_execute_all_cells(self):
        """Test executing all cells in notebook"""
        # Create notebook with multiple code cells
        initial_cells = [
            {'cell_type': 'code', 'source': 'x = 10'},
            {'cell_type': 'code', 'source': 'y = 20'},
            {'cell_type': 'code', 'source': 'print(x + y)'},
            {'cell_type': 'markdown', 'source': '# This is markdown'}
        ]
        
        notebook = await jupyter_service.create_notebook(
            title="Execute All Test",
            owner_id="user_123",
            initial_cells=initial_cells
        )
        
        # Execute all cells
        results = await jupyter_service.execute_all_cells(notebook.notebook_id, "user_123")
        
        # Should have 3 results (only code cells)
        assert len(results) == 3
        
        for result in results:
            assert result.success is True
            assert result.execution_count > 0
        
        print("✓ Execute all cells test passed")
    
    async def test_collaboration_features(self):
        """Test collaboration features"""
        # Create notebook
        notebook = await jupyter_service.create_notebook(
            title="Collaboration Test",
            owner_id="user_123"
        )
        
        # Add collaborator
        success = await jupyter_service.add_collaborator(
            notebook_id=notebook.notebook_id,
            collaborator_id="user_456",
            owner_id="user_123"
        )
        
        assert success is True
        
        # Verify collaborator was added
        updated_notebook = await jupyter_service.get_notebook(notebook.notebook_id, "user_123")
        assert "user_456" in updated_notebook.collaborators
        
        # Collaborator should be able to access notebook
        collab_notebook = await jupyter_service.get_notebook(notebook.notebook_id, "user_456")
        assert collab_notebook is not None
        
        # Collaborator should be able to edit cells
        success = await jupyter_service.update_cell(
            notebook_id=notebook.notebook_id,
            cell_id=notebook.cells[0].cell_id,
            source="# Edited by collaborator",
            user_id="user_456"
        )
        
        assert success is True
        
        # Remove collaborator
        success = await jupyter_service.remove_collaborator(
            notebook_id=notebook.notebook_id,
            collaborator_id="user_456",
            owner_id="user_123"
        )
        
        assert success is True
        
        # Verify collaborator was removed
        updated_notebook = await jupyter_service.get_notebook(notebook.notebook_id, "user_123")
        assert "user_456" not in updated_notebook.collaborators
        
        print("✓ Collaboration test passed")
    
    async def test_export_notebook(self):
        """Test notebook export functionality"""
        # Create notebook
        notebook = await jupyter_service.create_notebook(
            title="Export Test",
            owner_id="user_123",
            initial_cells=[
                {'cell_type': 'markdown', 'source': '# Export Test'},
                {'cell_type': 'code', 'source': 'print("Export test")'}
            ]
        )
        
        # Test JSON export
        json_export = await jupyter_service.export_notebook(
            notebook_id=notebook.notebook_id,
            user_id="user_123",
            format="json"
        )
        
        assert json_export is not None
        assert json_export['notebook_id'] == notebook.notebook_id
        assert json_export['title'] == "Export Test"
        assert len(json_export['cells']) == 2
        
        print("✓ Export test passed")
    
    async def test_list_user_notebooks(self):
        """Test listing user notebooks"""
        # Clear existing notebooks first
        jupyter_service.notebooks.clear()
        
        # Create multiple notebooks
        notebook1 = await jupyter_service.create_notebook("Notebook 1", "user_123")
        notebook2 = await jupyter_service.create_notebook("Notebook 2", "user_123")
        notebook3 = await jupyter_service.create_notebook("Notebook 3", "user_456")
        
        # Add user_123 as collaborator to notebook3
        await jupyter_service.add_collaborator(notebook3.notebook_id, "user_123", "user_456")
        
        # List notebooks for user_123
        notebooks = await jupyter_service.list_user_notebooks("user_123")
        
        print(f"Found {len(notebooks)} notebooks for user_123")
        for nb in notebooks:
            print(f"  - {nb['title']} (owner: {nb['is_owner']})")
        
        # Should see 3 notebooks (2 owned + 1 collaboration)
        assert len(notebooks) == 3
        
        # Check notebook summaries
        notebook_titles = [nb['title'] for nb in notebooks]
        assert "Notebook 1" in notebook_titles
        assert "Notebook 2" in notebook_titles
        assert "Notebook 3" in notebook_titles
        
        # Check ownership flags
        owned_notebooks = [nb for nb in notebooks if nb['is_owner']]
        assert len(owned_notebooks) == 2
        
        print("✓ List user notebooks test passed")
    
    async def test_error_handling(self):
        """Test error handling scenarios"""
        # Test accessing non-existent notebook
        notebook = await jupyter_service.get_notebook("non_existent", "user_123")
        assert notebook is None
        
        # Test updating non-existent cell
        success = await jupyter_service.update_cell(
            notebook_id="non_existent",
            cell_id="non_existent",
            source="test",
            user_id="user_123"
        )
        assert success is False
        
        # Test executing non-existent cell
        result = await jupyter_service.execute_cell(
            notebook_id="non_existent",
            cell_id="non_existent",
            user_id="user_123"
        )
        assert result is None
        
        print("✓ Error handling test passed")

async def run_tests():
    """Run all tests"""
    test_instance = TestJupyterNotebookService()
    
    print("Running Jupyter Notebook Service Tests...")
    print("=" * 50)
    
    try:
        # Setup
        test_instance.setup_method()
        
        # Run tests
        await test_instance.test_create_notebook()
        await test_instance.test_create_notebook_with_custom_cells()
        await test_instance.test_get_notebook_access_control()
        await test_instance.test_cell_management()
        await test_instance.test_cell_execution()
        await test_instance.test_execute_all_cells()
        await test_instance.test_collaboration_features()
        await test_instance.test_export_notebook()
        await test_instance.test_list_user_notebooks()
        await test_instance.test_error_handling()
        
        print("=" * 50)
        print("✅ All Jupyter Notebook Service tests passed!")
        
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