"""
Jupyter Notebook Service Demo

This script demonstrates the key features of the enhanced Jupyter notebook service
including notebook creation, execution, widgets, and collaboration.
"""

import asyncio
from services.jupyter_notebook_service import jupyter_service

async def demo_jupyter_notebook_service():
    """Demonstrate Jupyter notebook service capabilities"""
    
    print("🚀 Jupyter Notebook Service Demo")
    print("=" * 50)
    
    # 1. Create a data science notebook
    print("\n📓 Creating Data Science Notebook...")
    notebook = await jupyter_service.create_notebook(
        title="Data Science Demo",
        owner_id="data_scientist_123",
        kernel_name="python3",
        initial_cells=[
            {
                'cell_type': 'markdown',
                'source': '# Data Science Demo\n\nThis notebook demonstrates data analysis capabilities.'
            },
            {
                'cell_type': 'code',
                'source': 'import math\nimport statistics\n\n# Sample data\ndata = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]\nprint(f"Dataset: {data}")'
            },
            {
                'cell_type': 'markdown',
                'source': '## Statistical Analysis'
            },
            {
                'cell_type': 'code',
                'source': 'mean = statistics.mean(data)\nstd_dev = statistics.stdev(data)\nprint(f"Mean: {mean:.2f}")\nprint(f"Standard Deviation: {std_dev:.2f}")'
            }
        ]
    )
    
    print(f"✅ Created notebook: {notebook.title}")
    print(f"   Notebook ID: {notebook.notebook_id}")
    print(f"   Cells: {len(notebook.cells)}")
    
    # 2. Execute all cells
    print("\n⚡ Executing Notebook Cells...")
    results = await jupyter_service.execute_all_cells(notebook.notebook_id, "data_scientist_123")
    
    for i, result in enumerate(results, 1):
        print(f"   Cell {i}: {'✅ Success' if result.success else '❌ Failed'} ({result.execution_time:.3f}s)")
        if result.outputs:
            for output in result.outputs:
                if output.get('output_type') == 'stream':
                    text = output.get('text', '').strip()
                    if text:
                        print(f"      Output: {text}")
    
    # 3. Add interactive widgets
    print("\n🎛️  Creating Interactive Widgets...")
    widget_cell_id = await jupyter_service.add_cell(
        notebook_id=notebook.notebook_id,
        cell_type="code",
        source="slider_widget = IntSlider(value=50, min=0, max=100, description='Threshold:')\nbutton_widget = Button(description='Analyze')",
        user_id="data_scientist_123"
    )
    
    # Execute widget cell
    widget_result = await jupyter_service.execute_cell(
        notebook_id=notebook.notebook_id,
        cell_id=widget_cell_id,
        user_id="data_scientist_123"
    )
    
    widgets = await jupyter_service.get_notebook_widgets(notebook.notebook_id, "data_scientist_123")
    print(f"✅ Created {len(widgets)} interactive widgets")
    
    for widget in widgets:
        print(f"   - {widget.widget_type.title()} Widget: {widget.properties.get('variable_name', 'unnamed')}")
    
    # 4. Add collaborators
    print("\n👥 Adding Collaborators...")
    collaborators = ["analyst_456", "researcher_789"]
    
    for collab in collaborators:
        success = await jupyter_service.add_collaborator(
            notebook_id=notebook.notebook_id,
            collaborator_id=collab,
            owner_id="data_scientist_123"
        )
        if success:
            print(f"   ✅ Added collaborator: {collab}")
    
    # 5. Start real-time collaboration session
    print("\n🔄 Starting Real-time Collaboration...")
    session_id = await jupyter_service.start_realtime_session(
        notebook_id=notebook.notebook_id,
        user_id="analyst_456"
    )
    
    if session_id:
        print(f"   ✅ Started session: {session_id}")
        
        # Simulate collaborative edit
        edit_id = await jupyter_service.apply_collaborative_edit(
            notebook_id=notebook.notebook_id,
            cell_id=notebook.cells[0].cell_id,
            operation_type="insert",
            position=0,
            content="# Collaborative Edit\n",
            user_id="analyst_456"
        )
        
        if edit_id:
            print(f"   ✅ Applied collaborative edit: {edit_id}")
        
        # End session
        await jupyter_service.end_realtime_session(session_id)
        print("   ✅ Ended collaboration session")
    
    # 6. Get notebook statistics
    print("\n📊 Notebook Statistics...")
    stats = await jupyter_service.get_notebook_statistics(notebook.notebook_id, "data_scientist_123")
    
    if stats:
        print(f"   Total Cells: {stats['total_cells']}")
        print(f"   Code Cells: {stats['code_cells']}")
        print(f"   Executed Cells: {stats['executed_cells']}")
        print(f"   Total Execution Time: {stats['total_execution_time']:.3f}s")
        print(f"   Collaborators: {stats['collaborators_count']}")
        print(f"   Widgets: {stats['widgets_count']}")
    
    # 7. Export notebook
    print("\n📤 Exporting Notebook...")
    
    # Export as JSON
    json_export = await jupyter_service.export_notebook(
        notebook_id=notebook.notebook_id,
        user_id="data_scientist_123",
        format="json"
    )
    
    if json_export:
        print(f"   ✅ JSON Export: {len(str(json_export))} characters")
    
    # Export as Jupyter notebook format
    ipynb_export = await jupyter_service.export_notebook(
        notebook_id=notebook.notebook_id,
        user_id="data_scientist_123",
        format="ipynb"
    )
    
    if ipynb_export:
        print(f"   ✅ IPYNB Export: {len(ipynb_export)} characters")
    
    # 8. Create JavaScript notebook
    print("\n🟨 Creating JavaScript Notebook...")
    js_notebook = await jupyter_service.create_notebook(
        title="JavaScript Demo",
        owner_id="js_developer_456",
        kernel_name="javascript",
        initial_cells=[
            {
                'cell_type': 'code',
                'source': 'console.log("Hello from JavaScript!");\nlet numbers = [1, 2, 3, 4, 5];\nlet sum = numbers.reduce((a, b) => a + b, 0);\nconsole.log(`Sum: ${sum}`);'
            }
        ]
    )
    
    js_result = await jupyter_service.execute_cell(
        notebook_id=js_notebook.notebook_id,
        cell_id=js_notebook.cells[0].cell_id,
        user_id="js_developer_456"
    )
    
    print(f"✅ JavaScript execution: {'Success' if js_result.success else 'Failed'}")
    if js_result.outputs:
        for output in js_result.outputs:
            if output.get('output_type') == 'stream':
                text = output.get('text', '').strip()
                if text:
                    print(f"   Output: {text}")
    
    # 9. Kernel management demo
    print("\n🔧 Kernel Management Demo...")
    kernel_status = await jupyter_service.get_kernel_status(notebook.notebook_id, "data_scientist_123")
    
    if kernel_status:
        print(f"   Kernel Status: {kernel_status['status']}")
        print(f"   Language: {kernel_status['language']}")
        print(f"   Memory Usage: {kernel_status['memory_usage']:.1f} MB")
        print(f"   CPU Usage: {kernel_status['cpu_usage']:.1f}%")
    
    # Get notebook variables
    variables = await jupyter_service.get_notebook_variables(notebook.notebook_id, "data_scientist_123")
    if variables:
        print(f"   Variables: {variables['variables']}")
        print(f"   Imports: {len(variables['imports'])} modules")
    
    # 10. Final summary
    print("\n🎯 Demo Summary")
    print("=" * 50)
    print(f"📚 Total Notebooks Created: {len(jupyter_service.notebooks)}")
    print(f"⚙️  Active Kernels: {len(jupyter_service.kernels)}")
    print(f"🎛️  Interactive Widgets: {len(jupyter_service.widgets)}")
    print(f"🔄 Real-time Sessions: {len(jupyter_service.realtime_sessions)}")
    print(f"🌐 Supported Languages: {', '.join(jupyter_service.supported_kernels.keys())}")
    
    print("\n✨ Jupyter Notebook Service Demo Complete!")
    
    # Cleanup
    jupyter_service.cleanup()

if __name__ == "__main__":
    asyncio.run(demo_jupyter_notebook_service())