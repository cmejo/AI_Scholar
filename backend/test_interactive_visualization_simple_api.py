"""
Simple API test for Interactive Visualization Service

This module tests the basic API functionality without external dependencies.
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.interactive_visualization_service import (
    interactive_visualization_service,
    VisualizationType,
    VisualizationData
)

async def test_service_integration():
    """Test the service integration with sample data"""
    print("Testing Interactive Visualization Service Integration...")
    print("=" * 60)
    
    try:
        # Clear existing data
        interactive_visualization_service.visualizations.clear()
        interactive_visualization_service.active_sessions.clear()
        interactive_visualization_service.update_queue.clear()
        
        # Test 1: Create Plotly visualization with enhanced features
        print("1. Testing enhanced Plotly visualization creation...")
        
        plotly_data = VisualizationData(
            data={
                "title": "Research Metrics Dashboard"
            },
            layout={
                "title": {
                    "text": "Research Output Over Time",
                    "font": {"color": "#ffffff", "size": 18}
                },
                "xaxis": {"title": "Year", "color": "#ffffff"},
                "yaxis": {"title": "Count", "color": "#ffffff"},
                "showlegend": True,
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)"
            },
            config={
                "displayModeBar": True,
                "responsive": True
            },
            traces=[
                {
                    "x": ["2020", "2021", "2022", "2023", "2024"],
                    "y": [45, 67, 89, 123, 156],
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Citations",
                    "line": {"color": "#3B82F6", "width": 3}
                },
                {
                    "x": ["2020", "2021", "2022", "2023", "2024"],
                    "y": [12, 18, 25, 34, 42],
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Publications",
                    "line": {"color": "#10B981", "width": 3}
                }
            ]
        )
        
        plotly_viz = await interactive_visualization_service.create_visualization(
            title="Research Metrics Dashboard",
            description="Multi-trace visualization of research metrics",
            visualization_type=VisualizationType.PLOTLY,
            data=plotly_data,
            owner_id="researcher_123",
            tags=["research", "metrics", "dashboard"]
        )
        
        assert plotly_viz is not None
        assert len(plotly_viz.data.traces) == 2
        print("   ✓ Enhanced Plotly visualization created successfully")
        
        # Test 2: Generate enhanced embed code
        print("2. Testing enhanced embed code generation...")
        
        embed_code = await interactive_visualization_service.generate_embed_code(
            visualization_id=plotly_viz.visualization_id,
            user_id="researcher_123",
            width=800,
            height=600,
            interactive=True
        )
        
        assert embed_code is not None
        assert "visualizationUpdates" in embed_code
        assert "800px" in embed_code
        assert "600px" in embed_code
        assert "try {" in embed_code  # Check for error handling structure
        print("   ✓ Enhanced embed code generated with real-time support")
        
        # Test 3: Create D3 network visualization
        print("3. Testing D3 network visualization...")
        
        d3_data = VisualizationData(
            data={
                "nodes": [
                    {"id": "AI", "group": 1, "size": 20},
                    {"id": "Machine Learning", "group": 1, "size": 18},
                    {"id": "Deep Learning", "group": 1, "size": 16},
                    {"id": "Neural Networks", "group": 2, "size": 14}
                ],
                "links": [
                    {"source": "AI", "target": "Machine Learning", "value": 5},
                    {"source": "Machine Learning", "target": "Deep Learning", "value": 4},
                    {"source": "Deep Learning", "target": "Neural Networks", "value": 3}
                ]
            },
            layout={
                "width": 800,
                "height": 600,
                "force": {
                    "charge": -400,
                    "linkDistance": 100
                }
            },
            config={
                "interactive": True,
                "zoomable": True,
                "draggable": True
            }
        )
        
        d3_viz = await interactive_visualization_service.create_visualization(
            title="AI Knowledge Graph",
            description="Network visualization of AI concepts",
            visualization_type=VisualizationType.D3,
            data=d3_data,
            owner_id="researcher_456",
            tags=["knowledge-graph", "ai", "network"]
        )
        
        assert d3_viz is not None
        assert len(d3_viz.data.data["nodes"]) == 4
        assert len(d3_viz.data.data["links"]) == 3
        print("   ✓ D3 network visualization created successfully")
        
        # Test 4: Test real-time data streaming
        print("4. Testing real-time data streaming...")
        
        stream_data = {
            "values": [2, 3, 4, 5, 6, 7],
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        success = await interactive_visualization_service.stream_data_update(
            visualization_id=plotly_viz.visualization_id,
            user_id="researcher_123",
            data_stream=stream_data,
            update_interval=0.5
        )
        
        assert success is True
        
        # Check updates were queued
        updates = await interactive_visualization_service.get_visualization_updates(
            plotly_viz.visualization_id
        )
        assert len(updates) > 0
        assert updates[-1].update_type == "stream"
        print("   ✓ Real-time data streaming working correctly")
        
        # Test 5: Test collaborative annotations
        print("5. Testing collaborative annotations...")
        
        # Add collaborator
        await interactive_visualization_service.add_collaborator(
            plotly_viz.visualization_id, "collaborator_789", "researcher_123"
        )
        
        # Add annotation
        annotation_id = await interactive_visualization_service.add_annotation(
            visualization_id=plotly_viz.visualization_id,
            user_id="collaborator_789",
            content="Interesting trend in 2023",
            position={"x": 300, "y": 150},
            annotation_type="highlight",
            style={"color": "#F59E0B", "fontSize": 14}
        )
        
        assert annotation_id is not None
        
        # Verify annotation
        updated_viz = await interactive_visualization_service.get_visualization(
            plotly_viz.visualization_id, "researcher_123"
        )
        assert len(updated_viz.annotations) == 1
        assert updated_viz.annotations[0].content == "Interesting trend in 2023"
        print("   ✓ Collaborative annotations working correctly")
        
        # Test 6: Test visualization snapshots
        print("6. Testing visualization snapshots...")
        
        snapshot_id = await interactive_visualization_service.create_visualization_snapshot(
            visualization_id=plotly_viz.visualization_id,
            user_id="researcher_123",
            snapshot_name="Initial State"
        )
        
        assert snapshot_id is not None
        
        # Modify visualization
        await interactive_visualization_service.update_visualization_data(
            visualization_id=plotly_viz.visualization_id,
            user_id="researcher_123",
            data_updates={"modified": True},
            update_type="data"
        )
        
        # Restore snapshot
        restore_success = await interactive_visualization_service.restore_visualization_snapshot(
            visualization_id=plotly_viz.visualization_id,
            snapshot_id=snapshot_id,
            user_id="researcher_123"
        )
        
        assert restore_success is True
        print("   ✓ Visualization snapshots working correctly")
        
        # Test 7: Test Chart.js visualization
        print("7. Testing Chart.js visualization...")
        
        chartjs_data = VisualizationData(
            data={
                "type": "doughnut",
                "data": {
                    "labels": ["AI/ML", "Data Science", "Computer Vision", "NLP"],
                    "datasets": [{
                        "data": [35, 25, 20, 20],
                        "backgroundColor": ["#3B82F6", "#10B981", "#F59E0B", "#EF4444"]
                    }]
                },
                "options": {
                    "responsive": True,
                    "maintainAspectRatio": False
                }
            },
            layout={"responsive": True},
            config={"interaction": {"intersect": False}}
        )
        
        chartjs_viz = await interactive_visualization_service.create_visualization(
            title="Research Topic Distribution",
            description="Distribution of research topics",
            visualization_type=VisualizationType.CHART_JS,
            data=chartjs_data,
            owner_id="researcher_789",
            tags=["distribution", "topics"]
        )
        
        assert chartjs_viz is not None
        assert chartjs_viz.data.data["type"] == "doughnut"
        print("   ✓ Chart.js visualization created successfully")
        
        # Test 8: Test multi-user collaboration
        print("8. Testing multi-user collaboration...")
        
        # Add additional collaborator
        await interactive_visualization_service.add_collaborator(
            plotly_viz.visualization_id, "reviewer_101", "researcher_123"
        )
        
        # Multiple users join session
        users = ["researcher_123", "collaborator_789", "reviewer_101"]
        for user in users:
            success = await interactive_visualization_service.join_session(
                plotly_viz.visualization_id, user
            )
            assert success is True
        
        # Check active sessions
        active_users = interactive_visualization_service.active_sessions.get(
            plotly_viz.visualization_id, []
        )
        assert len(active_users) == 3
        print("   ✓ Multi-user collaboration working correctly")
        
        print("=" * 60)
        print("✅ All Interactive Visualization Service Integration tests passed!")
        
        # Final summary
        print(f"\nIntegration Test Summary:")
        print(f"- Total visualizations created: {len(interactive_visualization_service.visualizations)}")
        print(f"- Plotly visualizations: ✓")
        print(f"- D3.js visualizations: ✓") 
        print(f"- Chart.js visualizations: ✓")
        print(f"- Real-time streaming: ✓")
        print(f"- Collaborative annotations: ✓")
        print(f"- Visualization snapshots: ✓")
        print(f"- Multi-user sessions: ✓")
        print(f"- Enhanced embed codes: ✓")
        
        if hasattr(interactive_visualization_service, 'snapshots'):
            print(f"- Snapshots created: {len(interactive_visualization_service.snapshots)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_service_integration())
    exit(0 if success else 1)