"""
Basic tests for Interactive Visualization Service

This module tests the core functionality of the interactive visualization service
including visualization creation, real-time updates, annotations, and collaboration.
"""

import asyncio
from datetime import datetime
from services.interactive_visualization_service import (
    interactive_visualization_service,
    VisualizationType,
    InteractionType,
    VisualizationData
)

class TestInteractiveVisualizationService:
    """Test cases for interactive visualization service"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Clear any existing visualizations
        interactive_visualization_service.visualizations.clear()
        interactive_visualization_service.active_sessions.clear()
        interactive_visualization_service.update_queue.clear()
    
    async def test_create_plotly_visualization(self):
        """Test creating a Plotly visualization"""
        # Sample Plotly data
        viz_data = VisualizationData(
            data={
                'x': [1, 2, 3, 4, 5],
                'y': [2, 4, 6, 8, 10],
                'type': 'scatter',
                'mode': 'lines+markers'
            },
            layout={
                'title': 'Sample Line Chart',
                'xaxis': {'title': 'X Axis'},
                'yaxis': {'title': 'Y Axis'}
            },
            config={
                'displayModeBar': True,
                'responsive': True
            },
            traces=[{
                'x': [1, 2, 3, 4, 5],
                'y': [2, 4, 6, 8, 10],
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': 'Sample Data'
            }]
        )
        
        # Create visualization
        visualization = await interactive_visualization_service.create_visualization(
            title="Test Plotly Chart",
            description="A test Plotly visualization",
            visualization_type=VisualizationType.PLOTLY,
            data=viz_data,
            owner_id="user_123",
            tags=["test", "plotly", "chart"]
        )
        
        assert visualization is not None
        assert visualization.title == "Test Plotly Chart"
        assert visualization.visualization_type == VisualizationType.PLOTLY
        assert visualization.owner_id == "user_123"
        assert len(visualization.tags) == 3
        assert visualization.visualization_id in interactive_visualization_service.visualizations
        
        print("✓ Plotly visualization creation test passed")
    
    async def test_create_d3_visualization(self):
        """Test creating a D3.js visualization"""
        # Sample D3 data
        viz_data = VisualizationData(
            data={
                'nodes': [
                    {'id': 'A', 'group': 1},
                    {'id': 'B', 'group': 1},
                    {'id': 'C', 'group': 2}
                ],
                'links': [
                    {'source': 'A', 'target': 'B', 'value': 1},
                    {'source': 'B', 'target': 'C', 'value': 2}
                ]
            },
            layout={
                'width': 800,
                'height': 600,
                'force': {
                    'charge': -300,
                    'linkDistance': 50
                }
            },
            config={
                'interactive': True,
                'zoomable': True
            }
        )
        
        # Create visualization
        visualization = await interactive_visualization_service.create_visualization(
            title="Test D3 Network",
            description="A test D3.js network visualization",
            visualization_type=VisualizationType.D3,
            data=viz_data,
            owner_id="user_456"
        )
        
        assert visualization is not None
        assert visualization.title == "Test D3 Network"
        assert visualization.visualization_type == VisualizationType.D3
        assert visualization.owner_id == "user_456"
        assert len(visualization.data.data['nodes']) == 3
        assert len(visualization.data.data['links']) == 2
        
        print("✓ D3 visualization creation test passed")
    
    async def test_visualization_access_control(self):
        """Test visualization access control"""
        # Create visualization as user_123
        viz_data = VisualizationData(
            data={'test': 'data'},
            layout={'title': 'Access Test'},
            config={}
        )
        
        visualization = await interactive_visualization_service.create_visualization(
            title="Private Visualization",
            description="Test access control",
            visualization_type=VisualizationType.PLOTLY,
            data=viz_data,
            owner_id="user_123"
        )
        
        # Owner should have access
        retrieved = await interactive_visualization_service.get_visualization(
            visualization.visualization_id, "user_123"
        )
        assert retrieved is not None
        assert retrieved.visualization_id == visualization.visualization_id
        
        # Non-owner should not have access
        retrieved = await interactive_visualization_service.get_visualization(
            visualization.visualization_id, "user_456"
        )
        assert retrieved is None
        
        # Add collaborator
        await interactive_visualization_service.add_collaborator(
            visualization.visualization_id, "user_456", "user_123"
        )
        
        # Collaborator should now have access
        retrieved = await interactive_visualization_service.get_visualization(
            visualization.visualization_id, "user_456"
        )
        assert retrieved is not None
        
        print("✓ Access control test passed")
    
    async def test_real_time_data_updates(self):
        """Test real-time data updates"""
        # Create visualization
        viz_data = VisualizationData(
            data={'values': [1, 2, 3]},
            layout={'title': 'Update Test'},
            config={}
        )
        
        visualization = await interactive_visualization_service.create_visualization(
            title="Update Test",
            description="Test real-time updates",
            visualization_type=VisualizationType.PLOTLY,
            data=viz_data,
            owner_id="user_123"
        )
        
        original_version = visualization.version
        original_modified = visualization.modified_at
        
        # Wait a moment to ensure timestamp difference
        await asyncio.sleep(0.1)
        
        # Update data
        success = await interactive_visualization_service.update_visualization_data(
            visualization_id=visualization.visualization_id,
            user_id="user_123",
            data_updates={'values': [1, 2, 3, 4, 5]},
            update_type='data'
        )
        
        assert success is True
        
        # Check that data was updated
        updated_viz = await interactive_visualization_service.get_visualization(
            visualization.visualization_id, "user_123"
        )
        assert updated_viz.data.data['values'] == [1, 2, 3, 4, 5]
        assert updated_viz.version > original_version
        assert updated_viz.modified_at > original_modified
        
        # Check update queue
        updates = await interactive_visualization_service.get_visualization_updates(
            visualization.visualization_id
        )
        assert len(updates) > 0
        assert updates[0].update_type == 'data'
        
        print("✓ Real-time data updates test passed")
    
    async def test_annotations(self):
        """Test annotation functionality"""
        # Create visualization
        viz_data = VisualizationData(
            data={'test': 'data'},
            layout={'title': 'Annotation Test'},
            config={}
        )
        
        visualization = await interactive_visualization_service.create_visualization(
            title="Annotation Test",
            description="Test annotations",
            visualization_type=VisualizationType.PLOTLY,
            data=viz_data,
            owner_id="user_123"
        )
        
        # Add annotation
        annotation_id = await interactive_visualization_service.add_annotation(
            visualization_id=visualization.visualization_id,
            user_id="user_123",
            content="This is a test annotation",
            position={'x': 100, 'y': 200},
            annotation_type='text',
            style={'color': 'red', 'fontSize': 14}
        )
        
        assert annotation_id is not None
        
        # Check annotation was added
        updated_viz = await interactive_visualization_service.get_visualization(
            visualization.visualization_id, "user_123"
        )
        assert len(updated_viz.annotations) == 1
        assert updated_viz.annotations[0].content == "This is a test annotation"
        assert updated_viz.annotations[0].position['x'] == 100
        
        # Update annotation
        success = await interactive_visualization_service.update_annotation(
            visualization_id=visualization.visualization_id,
            annotation_id=annotation_id,
            user_id="user_123",
            updates={'content': 'Updated annotation content'}
        )
        
        assert success is True
        
        # Check annotation was updated
        updated_viz = await interactive_visualization_service.get_visualization(
            visualization.visualization_id, "user_123"
        )
        assert updated_viz.annotations[0].content == "Updated annotation content"
        
        # Delete annotation
        success = await interactive_visualization_service.delete_annotation(
            visualization_id=visualization.visualization_id,
            annotation_id=annotation_id,
            user_id="user_123"
        )
        
        assert success is True
        
        # Check annotation was deleted
        updated_viz = await interactive_visualization_service.get_visualization(
            visualization.visualization_id, "user_123"
        )
        assert len(updated_viz.annotations) == 0
        
        print("✓ Annotations test passed")
    
    async def test_interaction_recording(self):
        """Test interaction recording"""
        # Create visualization
        viz_data = VisualizationData(
            data={'test': 'data'},
            layout={'title': 'Interaction Test'},
            config={}
        )
        
        visualization = await interactive_visualization_service.create_visualization(
            title="Interaction Test",
            description="Test interaction recording",
            visualization_type=VisualizationType.PLOTLY,
            data=viz_data,
            owner_id="user_123"
        )
        
        # Record various interactions
        interactions = [
            (InteractionType.CLICK, {'element': 'data-point', 'value': 42}),
            (InteractionType.HOVER, {'element': 'axis', 'position': 'x'}),
            (InteractionType.ZOOM, {'scale': 1.5, 'center': [400, 300]}),
            (InteractionType.SELECT, {'selection': [1, 2, 3]})
        ]
        
        for interaction_type, data in interactions:
            success = await interactive_visualization_service.record_interaction(
                visualization_id=visualization.visualization_id,
                user_id="user_123",
                interaction_type=interaction_type,
                interaction_data=data,
                coordinates={'x': 100, 'y': 200}
            )
            assert success is True
        
        # Check interactions were recorded
        updated_viz = await interactive_visualization_service.get_visualization(
            visualization.visualization_id, "user_123"
        )
        assert len(updated_viz.interaction_history) == 4
        
        # Check interaction types
        recorded_types = [event.interaction_type for event in updated_viz.interaction_history]
        assert InteractionType.CLICK in recorded_types
        assert InteractionType.HOVER in recorded_types
        assert InteractionType.ZOOM in recorded_types
        assert InteractionType.SELECT in recorded_types
        
        print("✓ Interaction recording test passed")
    
    async def test_collaborative_sessions(self):
        """Test collaborative session management"""
        # Create visualization
        viz_data = VisualizationData(
            data={'test': 'data'},
            layout={'title': 'Collaboration Test'},
            config={}
        )
        
        visualization = await interactive_visualization_service.create_visualization(
            title="Collaboration Test",
            description="Test collaborative sessions",
            visualization_type=VisualizationType.PLOTLY,
            data=viz_data,
            owner_id="user_123"
        )
        
        # Add collaborators
        await interactive_visualization_service.add_collaborator(
            visualization.visualization_id, "user_456", "user_123"
        )
        await interactive_visualization_service.add_collaborator(
            visualization.visualization_id, "user_789", "user_123"
        )
        
        # Users join session
        users = ["user_123", "user_456", "user_789"]
        for user in users:
            success = await interactive_visualization_service.join_session(
                visualization.visualization_id, user
            )
            assert success is True
        
        # Check active sessions
        active_users = interactive_visualization_service.active_sessions.get(
            visualization.visualization_id, []
        )
        assert len(active_users) == 3
        assert all(user in active_users for user in users)
        
        # User leaves session
        success = await interactive_visualization_service.leave_session(
            visualization.visualization_id, "user_456"
        )
        assert success is True
        
        # Check session updated
        active_users = interactive_visualization_service.active_sessions.get(
            visualization.visualization_id, []
        )
        assert len(active_users) == 2
        assert "user_456" not in active_users
        
        print("✓ Collaborative sessions test passed")
    
    async def test_embed_code_generation(self):
        """Test embed code generation"""
        # Create Plotly visualization
        viz_data = VisualizationData(
            data={'x': [1, 2, 3], 'y': [4, 5, 6]},
            layout={'title': 'Embed Test'},
            config={'displayModeBar': True},
            traces=[{'x': [1, 2, 3], 'y': [4, 5, 6], 'type': 'scatter'}]
        )
        
        visualization = await interactive_visualization_service.create_visualization(
            title="Embed Test",
            description="Test embed code generation",
            visualization_type=VisualizationType.PLOTLY,
            data=viz_data,
            owner_id="user_123"
        )
        
        # Generate embed code
        embed_code = await interactive_visualization_service.generate_embed_code(
            visualization_id=visualization.visualization_id,
            user_id="user_123",
            width=800,
            height=600,
            interactive=True
        )
        
        assert embed_code is not None
        assert isinstance(embed_code, str)
        assert 'plotly-div-' in embed_code
        assert 'Plotly.newPlot' in embed_code
        assert '800px' in embed_code
        assert '600px' in embed_code
        
        print("✓ Embed code generation test passed")
    
    async def test_list_user_visualizations(self):
        """Test listing user visualizations"""
        # Clear existing visualizations
        interactive_visualization_service.visualizations.clear()
        
        # Create multiple visualizations
        viz_data = VisualizationData(
            data={'test': 'data'},
            layout={'title': 'Test'},
            config={}
        )
        
        viz1 = await interactive_visualization_service.create_visualization(
            "Visualization 1", "First viz", VisualizationType.PLOTLY, viz_data, "user_123"
        )
        viz2 = await interactive_visualization_service.create_visualization(
            "Visualization 2", "Second viz", VisualizationType.D3, viz_data, "user_123"
        )
        viz3 = await interactive_visualization_service.create_visualization(
            "Visualization 3", "Third viz", VisualizationType.CHART_JS, viz_data, "user_456"
        )
        
        # Add user_123 as collaborator to viz3
        await interactive_visualization_service.add_collaborator(viz3.visualization_id, "user_123", "user_456")
        
        # List visualizations for user_123
        visualizations = await interactive_visualization_service.list_user_visualizations("user_123")
        
        # Should see 3 visualizations (2 owned + 1 collaboration)
        assert len(visualizations) == 3
        
        # Check visualization summaries
        viz_titles = [viz['title'] for viz in visualizations]
        assert "Visualization 1" in viz_titles
        assert "Visualization 2" in viz_titles
        assert "Visualization 3" in viz_titles
        
        # Check ownership flags
        owned_visualizations = [viz for viz in visualizations if viz['is_owner']]
        assert len(owned_visualizations) == 2
        
        print("✓ List user visualizations test passed")
    
    async def test_error_handling(self):
        """Test error handling scenarios"""
        # Test accessing non-existent visualization
        viz = await interactive_visualization_service.get_visualization("non_existent", "user_123")
        assert viz is None
        
        # Test updating non-existent visualization
        success = await interactive_visualization_service.update_visualization_data(
            visualization_id="non_existent",
            user_id="user_123",
            data_updates={'test': 'data'}
        )
        assert success is False
        
        # Test adding annotation to non-existent visualization
        annotation_id = await interactive_visualization_service.add_annotation(
            visualization_id="non_existent",
            user_id="user_123",
            content="test",
            position={'x': 0, 'y': 0}
        )
        assert annotation_id is None
        
        print("✓ Error handling test passed")

async def run_tests():
    """Run all tests"""
    test_instance = TestInteractiveVisualizationService()
    
    print("Running Interactive Visualization Service Tests...")
    print("=" * 60)
    
    try:
        # Setup
        test_instance.setup_method()
        
        # Run tests
        await test_instance.test_create_plotly_visualization()
        await test_instance.test_create_d3_visualization()
        await test_instance.test_visualization_access_control()
        await test_instance.test_real_time_data_updates()
        await test_instance.test_annotations()
        await test_instance.test_interaction_recording()
        await test_instance.test_collaborative_sessions()
        await test_instance.test_embed_code_generation()
        await test_instance.test_list_user_visualizations()
        await test_instance.test_error_handling()
        
        print("=" * 60)
        print("✅ All Interactive Visualization Service tests passed!")
        
        # Test summary
        print(f"\nTest Summary:")
        print(f"- Visualizations created: {len(interactive_visualization_service.visualizations)}")
        print(f"- Supported types: {[vt.value for vt in VisualizationType]}")
        print(f"- Active sessions: {len(interactive_visualization_service.active_sessions)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    exit(0 if success else 1)