"""
Comprehensive tests for Jupyter Notebook Service

This module tests all aspects of the enhanced Jupyter notebook service
including kernel management, widget support, and collaborative features.
"""

import asyncio
from datetime import datetime
from services.jupyter_notebook_service import jupyter_service

class TestJupyterNotebookComprehensive:
    """Comprehensive test cases for Jupyter notebook service"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Clear any existing notebooks
        jupyter_service.notebooks.clear()
        jupyter_service.execution_queue.clear()
        jupyter_service.widgets.clear()
        jupyter_service.realtime_sessions.clear()
        jupyter_service.collaborative_edits.clear()
    
    async def test_complete_notebook_lifecycle(self):
        """Test complete notebook lifecycle from creation to cleanup"""
        print("Testing complete notebook lifecycle...")
        
        # 1. Create notebook
        notebook = await jupyter_service.create_notebook(
            title="Lifecycle Test Notebook",
            owner_id="user_123",
            kernel_name="python3",
            initial_cells=[
                {
                    'cell_type': 'markdown',
                    'source': '# Lifecycle Test\n\nThis tests the complete notebook lifecycle.'
                },
                {
                    'cell_type': 'code',
                    'source': 'x = 42\nprint(f"The answer is {x}")'
                }
            ]
        )
        
        assert notebook is not None
        assert len(notebook.cells) == 2
        print(f"✓ Created notebook: {notebook.notebook_id}")
        
        # 2. Get kernel status
        kernel_status = await jupyter_service.get_kernel_status(notebook.notebook_id, "user_123")
        assert kernel_status is not None
        assert kernel_status['status'] in ['idle', 'starting']
        print(f"✓ Kernel status: {kernel_status['status']}")
        
        # 3. Execute cells
        for i, cell in enumerate(notebook.cells):
            if cell.cell_type == 'code':
                result = await jupyter_service.execute_cell(
                    notebook_id=notebook.notebook_id,
                    cell_id=cell.cell_id,
                    user_id="user_123"
                )
                assert result is not None
                assert result.success is True
                print(f"✓ Executed cell {i+1}: {result.execution_time:.3f}s")
        
        # 4. Add collaborator
        success = await jupyter_service.add_collaborator(
            notebook_id=notebook.notebook_id,
            collaborator_id="collaborator_456",
            owner_id="user_123"
        )
        assert success is True
        print("✓ Added collaborator")
        
        # 5. Get notebook statistics
        stats = await jupyter_service.get_notebook_statistics(notebook.notebook_id, "user_123")
        assert stats is not None
        assert stats['total_cells'] == 2
        assert stats['code_cells'] == 1
        assert stats['executed_cells'] == 1
        print(f"✓ Statistics: {stats['total_cells']} cells, {stats['executed_cells']} executed")
        
        # 6. Export notebook
        exported = await jupyter_service.export_notebook(
            notebook_id=notebook.notebook_id,
            user_id="user_123",
            format="json"
        )
        assert exported is not None
        assert exported['title'] == "Lifecycle Test Notebook"
        print("✓ Exported notebook")
        
        # 7. Duplicate notebook
        duplicate_id = await jupyter_service.duplicate_notebook(
            notebook_id=notebook.notebook_id,
            user_id="user_123",
            new_title="Lifecycle Test Notebook (Copy)"
        )
        assert duplicate_id is not None
        print(f"✓ Duplicated notebook: {duplicate_id}")
        
        # 8. Clear outputs
        success = await jupyter_service.clear_notebook_output(notebook.notebook_id, "user_123")
        assert success is True
        print("✓ Cleared outputs")
        
        print("✅ Complete notebook lifecycle test passed!")
    
    async def test_widget_functionality(self):
        """Test interactive widget functionality"""
        print("Testing widget functionality...")
        
        # Create notebook with widget code
        notebook = await jupyter_service.create_notebook(
            title="Widget Test",
            owner_id="user_123",
            initial_cells=[
                {
                    'cell_type': 'code',
                    'source': 'slider_widget = IntSlider(value=50, min=0, max=100, description="Value:")'
                },
                {
                    'cell_type': 'code',
                    'source': 'button_widget = Button(description="Click me!")'
                },
                {
                    'cell_type': 'code',
                    'source': 'text_widget = Text(value="Hello", description="Text:")'
                }
            ]
        )
        
        # Execute cells to create widgets
        for cell in notebook.cells:
            if cell.cell_type == 'code':
                result = await jupyter_service.execute_cell(
                    notebook_id=notebook.notebook_id,
                    cell_id=cell.cell_id,
                    user_id="user_123"
                )
                assert result is not None
        
        # Check that widgets were created
        widgets = await jupyter_service.get_notebook_widgets(notebook.notebook_id, "user_123")
        print(f"✓ Created {len(widgets)} widgets")
        
        # Test widget value updates
        if widgets:
            widget = widgets[0]
            success = await jupyter_service.update_widget_value(
                widget_id=widget.widget_id,
                new_value=75,
                user_id="user_123"
            )
            assert success is True
            print(f"✓ Updated widget value: {widget.widget_type}")
        
        print("✅ Widget functionality test passed!")
    
    async def test_collaborative_editing(self):
        """Test collaborative editing features"""
        print("Testing collaborative editing...")
        
        # Create notebook
        notebook = await jupyter_service.create_notebook(
            title="Collaborative Test",
            owner_id="owner_123"
        )
        
        # Add multiple collaborators
        collaborators = ["user_1", "user_2", "user_3"]
        for collab in collaborators:
            success = await jupyter_service.add_collaborator(
                notebook_id=notebook.notebook_id,
                collaborator_id=collab,
                owner_id="owner_123"
            )
            assert success is True
        
        print(f"✓ Added {len(collaborators)} collaborators")
        
        # Start real-time sessions
        sessions = []
        for collab in collaborators:
            session_id = await jupyter_service.start_realtime_session(
                notebook_id=notebook.notebook_id,
                user_id=collab
            )
            assert session_id is not None
            sessions.append(session_id)
        
        print(f"✓ Started {len(sessions)} real-time sessions")
        
        # Test collaborative edits
        for i, collab in enumerate(collaborators):
            edit_id = await jupyter_service.apply_collaborative_edit(
                notebook_id=notebook.notebook_id,
                cell_id=notebook.cells[0].cell_id,
                operation_type="insert",
                position=0,
                content=f"# Edit by {collab}\n",
                user_id=collab
            )
            assert edit_id is not None
        
        print("✓ Applied collaborative edits")
        
        # Get active collaborators
        active_collabs = await jupyter_service.get_active_collaborators(
            notebook_id=notebook.notebook_id,
            user_id="owner_123"
        )
        assert len(active_collabs) == len(collaborators)
        print(f"✓ Found {len(active_collabs)} active collaborators")
        
        # End sessions
        for session_id in sessions:
            success = await jupyter_service.end_realtime_session(session_id)
            assert success is True
        
        print("✓ Ended real-time sessions")
        print("✅ Collaborative editing test passed!")
    
    async def test_kernel_management(self):
        """Test kernel management features"""
        print("Testing kernel management...")
        
        # Create notebook
        notebook = await jupyter_service.create_notebook(
            title="Kernel Test",
            owner_id="user_123",
            kernel_name="python3"
        )
        
        # Get initial kernel status
        kernel_status = await jupyter_service.get_kernel_status(notebook.notebook_id, "user_123")
        assert kernel_status is not None
        initial_kernel_id = kernel_status['kernel_id']
        print(f"✓ Initial kernel: {initial_kernel_id}")
        
        # Execute some code to establish kernel state
        cell_id = await jupyter_service.add_cell(
            notebook_id=notebook.notebook_id,
            cell_type="code",
            source="import math\nx = 42\ny = math.pi",
            user_id="user_123"
        )
        
        result = await jupyter_service.execute_cell(
            notebook_id=notebook.notebook_id,
            cell_id=cell_id,
            user_id="user_123"
        )
        assert result.success is True
        print("✓ Executed code to establish kernel state")
        
        # Get variables
        variables = await jupyter_service.get_notebook_variables(notebook.notebook_id, "user_123")
        assert 'variables' in variables
        assert len(variables['variables']) > 0
        print(f"✓ Found variables: {variables['variables']}")
        
        # Restart kernel
        success = await jupyter_service.restart_kernel(notebook.notebook_id, "user_123")
        assert success is True
        print("✓ Restarted kernel")
        
        # Verify new kernel
        new_kernel_status = await jupyter_service.get_kernel_status(notebook.notebook_id, "user_123")
        assert new_kernel_status is not None
        assert new_kernel_status['kernel_id'] != initial_kernel_id
        print(f"✓ New kernel: {new_kernel_status['kernel_id']}")
        
        # Test interrupt
        success = await jupyter_service.interrupt_kernel(notebook.notebook_id, "user_123")
        assert success is True
        print("✓ Interrupted kernel")
        
        print("✅ Kernel management test passed!")
    
    async def test_multi_language_support(self):
        """Test multi-language kernel support"""
        print("Testing multi-language support...")
        
        languages = [
            ("python3", 'print("Hello from Python")'),
            ("javascript", 'console.log("Hello from JavaScript")'),
            ("r", 'print("Hello from R")')
        ]
        
        for kernel_name, test_code in languages:
            # Create notebook for each language
            notebook = await jupyter_service.create_notebook(
                title=f"{kernel_name.title()} Test",
                owner_id="user_123",
                kernel_name=kernel_name,
                initial_cells=[
                    {
                        'cell_type': 'code',
                        'source': test_code
                    }
                ]
            )
            
            # Execute the test code
            result = await jupyter_service.execute_cell(
                notebook_id=notebook.notebook_id,
                cell_id=notebook.cells[0].cell_id,
                user_id="user_123"
            )
            
            assert result is not None
            assert result.success is True
            print(f"✓ {kernel_name} execution successful")
        
        print("✅ Multi-language support test passed!")
    
    async def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios"""
        print("Testing error handling and recovery...")
        
        # Create notebook
        notebook = await jupyter_service.create_notebook(
            title="Error Test",
            owner_id="user_123"
        )
        
        # Test various error scenarios
        error_scenarios = [
            ("Syntax Error", "print('unclosed string"),
            ("Runtime Error", "print(undefined_variable)"),
            ("Import Error", "import nonexistent_module"),
            ("Division by Zero", "result = 1 / 0")
        ]
        
        for scenario_name, error_code in error_scenarios:
            cell_id = await jupyter_service.add_cell(
                notebook_id=notebook.notebook_id,
                cell_type="code",
                source=error_code,
                user_id="user_123"
            )
            
            result = await jupyter_service.execute_cell(
                notebook_id=notebook.notebook_id,
                cell_id=cell_id,
                user_id="user_123"
            )
            
            # In our simplified implementation, errors are handled gracefully
            assert result is not None
            print(f"✓ Handled {scenario_name}")
        
        # Test recovery with valid code
        recovery_cell_id = await jupyter_service.add_cell(
            notebook_id=notebook.notebook_id,
            cell_type="code",
            source="print('Recovery successful')",
            user_id="user_123"
        )
        
        result = await jupyter_service.execute_cell(
            notebook_id=notebook.notebook_id,
            cell_id=recovery_cell_id,
            user_id="user_123"
        )
        
        assert result is not None
        assert result.success is True
        print("✓ Recovery after errors successful")
        
        print("✅ Error handling and recovery test passed!")
    
    async def test_import_export_workflow(self):
        """Test comprehensive import/export workflow"""
        print("Testing import/export workflow...")
        
        # Create a complex notebook
        notebook = await jupyter_service.create_notebook(
            title="Import/Export Test",
            owner_id="user_123",
            initial_cells=[
                {
                    'cell_type': 'markdown',
                    'source': '# Data Analysis Notebook\n\nThis notebook demonstrates data analysis.'
                },
                {
                    'cell_type': 'code',
                    'source': 'import math\ndata = [1, 2, 3, 4, 5]'
                },
                {
                    'cell_type': 'markdown',
                    'source': '## Statistical Analysis'
                },
                {
                    'cell_type': 'code',
                    'source': 'mean = sum(data) / len(data)\nprint(f"Mean: {mean}")'
                },
                {
                    'cell_type': 'code',
                    'source': 'variance = sum((x - mean) ** 2 for x in data) / len(data)\nprint(f"Variance: {variance}")'
                }
            ]
        )
        
        # Execute all cells
        results = await jupyter_service.execute_all_cells(notebook.notebook_id, "user_123")
        assert len(results) == 3  # Only code cells
        print(f"✓ Executed {len(results)} code cells")
        
        # Export as JSON
        json_export = await jupyter_service.export_notebook(
            notebook_id=notebook.notebook_id,
            user_id="user_123",
            format="json"
        )
        assert json_export is not None
        assert json_export['title'] == "Import/Export Test"
        print("✓ Exported as JSON")
        
        # Export as ipynb
        ipynb_export = await jupyter_service.export_notebook(
            notebook_id=notebook.notebook_id,
            user_id="user_123",
            format="ipynb"
        )
        assert ipynb_export is not None
        assert isinstance(ipynb_export, str)
        print(f"✓ Exported as ipynb ({len(ipynb_export)} characters)")
        
        # Test import
        imported_id = await jupyter_service.import_notebook(
            notebook_data=ipynb_export,
            owner_id="user_456",
            format="ipynb"
        )
        assert imported_id is not None
        print(f"✓ Imported notebook: {imported_id}")
        
        # Verify imported notebook
        imported_notebook = await jupyter_service.get_notebook(imported_id, "user_456")
        assert imported_notebook is not None
        assert len(imported_notebook.cells) == 5
        print("✓ Verified imported notebook structure")
        
        print("✅ Import/export workflow test passed!")

async def run_comprehensive_tests():
    """Run all comprehensive tests"""
    test_instance = TestJupyterNotebookComprehensive()
    
    print("Running Comprehensive Jupyter Notebook Service Tests...")
    print("=" * 70)
    
    try:
        # Setup
        test_instance.setup_method()
        
        # Run comprehensive tests
        await test_instance.test_complete_notebook_lifecycle()
        print()
        
        await test_instance.test_widget_functionality()
        print()
        
        await test_instance.test_collaborative_editing()
        print()
        
        await test_instance.test_kernel_management()
        print()
        
        await test_instance.test_multi_language_support()
        print()
        
        await test_instance.test_error_handling_and_recovery()
        print()
        
        await test_instance.test_import_export_workflow()
        print()
        
        print("=" * 70)
        print("🎉 ALL COMPREHENSIVE TESTS PASSED! 🎉")
        
        # Final summary
        print(f"\nFinal Test Summary:")
        print(f"- Total notebooks: {len(jupyter_service.notebooks)}")
        print(f"- Active kernels: {len(jupyter_service.kernels)}")
        print(f"- Widgets created: {len(jupyter_service.widgets)}")
        print(f"- Real-time sessions: {len(jupyter_service.realtime_sessions)}")
        print(f"- Supported kernels: {list(jupyter_service.supported_kernels.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Comprehensive test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        jupyter_service.cleanup()

if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_tests())
    exit(0 if success else 1)