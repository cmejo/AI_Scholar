"""
Enhanced tests for Interactive Visualization Service

This module tests the enhanced functionality including real-time updates,
collaborative features, embedding, and advanced visualization support.
"""

import asyncio
import json
from datetime import datetime
from services.interactive_visualization_service import (
    interactive_visualization_service,
    VisualizationType,
    InteractionType,
    VisualizationData
)

class TestEnhancedInteractiveVisualization:
    """Test cases for enhanced interactive visualization features"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Clear any existing data
        interactive_visualization_service.visualizations.clear()
        interactive_visualization_service.active_sessions.clear()
        interactive_visualization_service.update_queue.clear()
        if hasattr(interactive_visualization_service, 'snapshots'):
            interactive_visualization_service.snapshots.clear()
    
    async def test_plotly_visualization_with_traces(self):
        """Test creating Plotly visualization with multiple traces"""
        viz_data = VisualizationData(
            data={
                'title': 'Multi-trace Chart',
                'type': 'scatter'
            },
            layout={
                'title': 'Research Metrics Over Time',
                'xaxis': {'title': 'Year'},
                'yaxis': {'title': 'Count'},
                'showlegend': True
            },
            config={
                'displayModeBar': True,
                'responsive': True
            },
            traces=[
                {
                    'x': ['2020', '2021', '2022', '2023', '2024'],
                    'y': [45, 67, 89, 123, 156],
                    'type': 'scatter',
                    'mode': 'lines+markers',
                    'name': 'Citations',
                    'line': {'color': '#3B82F6'}
                },
                {
                    'x': ['2020', '2021', '2022', '2023', '2024'],
                    'y': [12, 18, 25, 34, 42],
                    'type': 'scatter',
                    'mode': 'lines+markers',
                    'name': 'Publications',
                    'line': {'color': '#10B981'}
                }
            ]
        )
        
        visualization = await interactive_visualization_service.create_visualization(
            title="Research Metrics Dashboard",
            description="Multi-trace visualization of research metrics",
            visualization_type=VisualizationType.PLOTLY,
            data=viz_data,
            owner_id="researcher_123",
            tags=["research", "metrics", "dashboard"]
        )
        
        assert visualization is not None
        assert len(visualization.data.traces) == 2
        assert visualization.data.traces[0]['name'] == 'Citations'
        assert visualization.data.traces[1]['name'] == 'Publications'
        
        print("✓ Plotly multi-trace visualization test passed")
    
    async def test_d3_network_visualization(self):
        """Test creating D3.js network visualization"""
        viz_data = VisualizationData(
            data={
                'nodes': [
                    {'id': 'AI', 'group': 1, 'size': 20},
                    {'id': 'Machine Learning', 'group': 1, 'size': 18},
                    {'id': 'Deep Learning', 'group': 1, 'size': 16},
                    {'id': 'Neural Networks', 'group': 2, 'size': 14},
                    {'id': 'Computer Vision', 'group': 2, 'size': 12},
                    {'id': 'NLP', 'group': 2, 'size': 12},
                    {'id': 'Reinforcement Learning', 'group': 3, 'size': 10}
                ],
                'links': [
                    {'source': 'AI', 'target': 'Machine Learning', 'value': 5},
                    {'source': 'Machine Learning', 'target': 'Deep Learning', 'value': 4},
                    {'source': 'Deep Learning', 'target': 'Neural Networks', 'value': 3},
                    {'source': 'Deep Learning', 'target': 'Computer Vision', 'value': 2},
                    {'source': 'Deep Learning', 'target': 'NLP', 'value': 2},
                    {'source': 'Machine Learning', 'target': 'Reinforcement Learning', 'value': 2}
                ]
            },
            layout={
                'width': 800,
                'height': 600,
                'force': {
                    'charge': -300,
                    'linkDistance': 80,
                    'gravity': 0.1
                }
            },
            config={
                'interactive': True,
                'zoomable': True,
                'draggable': True
            }
        )
        
        visualization = await interactive_visualization_service.create_visualization(
            title="AI Research Knowledge Graph",
            description="Network visualization of AI research concepts",
            visualization_type=VisualizationType.D3,
            data=viz_data,
            owner_id="researcher_456",
            tags=["knowledge-graph", "ai", "network"]
        )
        
        assert visualization is not None
        assert len(visualization.data.data['nodes']) == 7
        assert len(visualization.data.data['links']) == 6
        assert visualization.data.config['interactive'] is True
        
        print("✓ D3 network visualization test passed")
    
    async def test_chartjs_dashboard_visualization(self):
        """Test creating Chart.js dashboard visualization"""
        viz_data = VisualizationData(
            data={
                'type': 'bar',
                'data': {
                    'labels': ['Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024'],
                    'datasets': [
                        {
                            'label': 'Papers Published',
                            'data': [12, 18, 15, 22],
                            'backgroundColor': '#3B82F6',
                            'borderColor': '#1D4ED8',
                            'borderWidth': 1
                        },
                        {
                            'label': 'Citations Received',
                            'data': [45, 67, 58, 89],
                            'backgroundColor': '#10B981',
                            'borderColor': '#047857',
                            'borderWidth': 1
                        }
                    ]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Quarterly Research Output'
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True
                        }
                    }
                }
            },
            layout={
                'responsive': True,
                'maintainAspectRatio': False
            },
            config={
                'interaction': {
                    'intersect': False,
                    'mode': 'index'
                }
            }
        )
        
        visualization = await interactive_visualization_service.create_visualization(
            title="Research Output Dashboard",
            description="Quarterly research metrics visualization",
            visualization_type=VisualizationType.CHART_JS,
            data=viz_data,
            owner_id="researcher_789",
            tags=["dashboard", "metrics", "quarterly"]
        )
        
        assert visualization is not None
        assert visualization.data.data['type'] == 'bar'
        assert len(visualization.data.data['data']['datasets']) == 2
        
        print("✓ Chart.js dashboard visualization test passed")
    
    async def test_real_time_data_streaming(self):
        """Test real-time data streaming functionality"""
        # Create base visualization
        viz_data = VisualizationData(
            data={'values': [1, 2, 3, 4, 5]},
            layout={'title': 'Real-time Data Stream'},
            config={'updateInterval': 1000}
        )
        
        visualization = await interactive_visualization_service.create_visualization(
            title="Live Data Stream",
            description="Real-time updating visualization",
            visualization_type=VisualizationType.PLOTLY,
            data=viz_data,
            owner_id="user_123"
        )
        
        # Test streaming updates
        stream_data = {
            'values': [2, 3, 4, 5, 6, 7],
            'timestamp': datetime.now().isoformat()
        }
        
        success = await interactive_visualization_service.stream_data_update(
            visualization_id=visualization.visualization_id,
            user_id="user_123",
            data_stream=stream_data,
            update_interval=0.5
        )
        
        assert success is True
        
        # Check that update was queued
        updates = await interactive_visualization_service.get_visualization_updates(
            visualization.visualization_id
        )
        assert len(updates) > 0
        assert updates[-1].update_type == 'stream'
        assert updates[-1].changes['values'] == [2, 3, 4, 5, 6, 7]
        
        print("✓ Real-time data streaming test passed")
    
    async def test_collaborative_annotations_with_replies(self):
        """Test collaborative annotation system with replies"""
        # Create visualization
        viz_data = VisualizationData(
            data={'test': 'data'},
            layout={'title': 'Collaborative Annotation Test'},
            config={}
        )
        
        visualization = await interactive_visualization_service.create_visualization(
            title="Collaboration Test",
            description="Test collaborative annotations",
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
        
        # Add initial annotation
        annotation_id = await interactive_visualization_service.add_annotation(
            visualization_id=visualization.visualization_id,
            user_id="user_123",
            content="This data point is interesting",
            position={'x': 150, 'y': 200},
            annotation_type='highlight',
            style={'color': '#F59E0B', 'fontSize': 12}
        )
        
        assert annotation_id is not None
        
        # Simulate reply to annotation (would be handled by a separate reply system)
        updated_viz = await interactive_visualization_service.get_visualization(
            visualization.visualization_id, "user_456"
        )
        
        # Find the annotation and add a reply ID
        for ann in updated_viz.annotations:
            if ann.annotation_id == annotation_id:
                ann.replies.append("reply_123")
                break
        
        # Add another annotation from collaborator
        annotation_id_2 = await interactive_visualization_service.add_annotation(
            visualization_id=visualization.visualization_id,
            user_id="user_456",
            content="I agree, let's investigate further",
            position={'x': 180, 'y': 220},
            annotation_type='arrow',
            style={'color': '#10B981', 'fontSize': 12}
        )
        
        assert annotation_id_2 is not None
        
        # Check final state
        final_viz = await interactive_visualization_service.get_visualization(
            visualization.visualization_id, "user_123"
        )
        assert len(final_viz.annotations) == 2
        assert len(final_viz.collaborators) == 2
        
        print("✓ Collaborative annotations test passed")
    
    async def test_enhanced_embed_code_generation(self):
        """Test enhanced embed code generation with multiple libraries"""
        visualizations = []
        
        # Test Plotly embed
        plotly_data = VisualizationData(
            data={'x': [1, 2, 3], 'y': [4, 5, 6]},
            layout={'title': 'Plotly Embed Test'},
            config={'displayModeBar': True},
            traces=[{'x': [1, 2, 3], 'y': [4, 5, 6], 'type': 'scatter'}]
        )
        
        plotly_viz = await interactive_visualization_service.create_visualization(
            "Plotly Embed", "Test Plotly embedding", VisualizationType.PLOTLY, plotly_data, "user_123"
        )
        visualizations.append((plotly_viz, 'plotly'))
        
        # Test D3 embed
        d3_data = VisualizationData(
            data={'nodes': [{'id': 'A'}, {'id': 'B'}], 'links': [{'source': 'A', 'target': 'B'}]},
            layout={'width': 400, 'height': 300},
            config={'interactive': True}
        )
        
        d3_viz = await interactive_visualization_service.create_visualization(
            "D3 Embed", "Test D3 embedding", VisualizationType.D3, d3_data, "user_123"
        )
        visualizations.append((d3_viz, 'd3'))
        
        # Test Chart.js embed
        chartjs_data = VisualizationData(
            data={'type': 'pie', 'data': {'labels': ['A', 'B'], 'datasets': [{'data': [1, 2]}]}},
            layout={'responsive': True},
            config={}
        )
        
        chartjs_viz = await interactive_visualization_service.create_visualization(
            "Chart.js Embed", "Test Chart.js embedding", VisualizationType.CHART_JS, chartjs_data, "user_123"
        )
        visualizations.append((chartjs_viz, 'chartjs'))
        
        # Test embed code generation for each
        for viz, viz_type in visualizations:
            embed_code = await interactive_visualization_service.generate_embed_code(
                visualization_id=viz.visualization_id,
                user_id="user_123",
                width=600,
                height=400,
                interactive=True
            )
            
            assert embed_code is not None
            assert isinstance(embed_code, str)
            assert f'{viz_type}' in embed_code.lower() or 'div' in embed_code
            assert '600px' in embed_code
            assert '400px' in embed_code
            assert 'visualizationUpdates' in embed_code  # Real-time update support
            
        print("✓ Enhanced embed code generation test passed")
    
    async def test_visualization_snapshots(self):
        """Test visualization snapshot and restore functionality"""
        # Create visualization
        viz_data = VisualizationData(
            data={'values': [1, 2, 3, 4, 5]},
            layout={'title': 'Snapshot Test'},
            config={}
        )
        
        visualization = await interactive_visualization_service.create_visualization(
            title="Snapshot Test",
            description="Test snapshot functionality",
            visualization_type=VisualizationType.PLOTLY,
            data=viz_data,
            owner_id="user_123"
        )
        
        original_version = visualization.version
        
        # Create snapshot
        snapshot_id = await interactive_visualization_service.create_visualization_snapshot(
            visualization_id=visualization.visualization_id,
            user_id="user_123",
            snapshot_name="Initial State"
        )
        
        assert snapshot_id is not None
        
        # Modify visualization
        await interactive_visualization_service.update_visualization_data(
            visualization_id=visualization.visualization_id,
            user_id="user_123",
            data_updates={'values': [10, 20, 30, 40, 50]},
            update_type='data'
        )
        
        # Verify modification
        modified_viz = await interactive_visualization_service.get_visualization(
            visualization.visualization_id, "user_123"
        )
        assert modified_viz.data.data['values'] == [10, 20, 30, 40, 50]
        assert modified_viz.version > original_version
        
        # Restore from snapshot
        success = await interactive_visualization_service.restore_visualization_snapshot(
            visualization_id=visualization.visualization_id,
            snapshot_id=snapshot_id,
            user_id="user_123"
        )
        
        assert success is True
        
        # Verify restoration
        restored_viz = await interactive_visualization_service.get_visualization(
            visualization.visualization_id, "user_123"
        )
        assert restored_viz.data.data['values'] == [1, 2, 3, 4, 5]
        
        print("✓ Visualization snapshots test passed")
    
    async def test_advanced_interaction_tracking(self):
        """Test advanced interaction tracking and analytics"""
        # Create visualization
        viz_data = VisualizationData(
            data={'test': 'data'},
            layout={'title': 'Interaction Tracking Test'},
            config={}
        )
        
        visualization = await interactive_visualization_service.create_visualization(
            title="Interaction Test",
            description="Test advanced interaction tracking",
            visualization_type=VisualizationType.PLOTLY,
            data=viz_data,
            owner_id="user_123"
        )
        
        # Record various complex interactions
        interactions = [
            {
                'type': InteractionType.CLICK,
                'data': {'element': 'data-point', 'value': 42, 'series': 'A'},
                'coords': {'x': 100, 'y': 200}
            },
            {
                'type': InteractionType.BRUSH,
                'data': {'selection': {'x': [1, 5], 'y': [10, 50]}, 'points': 15},
                'coords': {'x': 150, 'y': 250}
            },
            {
                'type': InteractionType.ZOOM,
                'data': {'scale': 2.5, 'center': [400, 300], 'bounds': {'x': [0, 800], 'y': [0, 600]}},
                'coords': {'x': 400, 'y': 300}
            },
            {
                'type': InteractionType.FILTER,
                'data': {'filter': 'category', 'value': 'research', 'applied': True},
                'coords': None
            }
        ]
        
        for interaction in interactions:
            success = await interactive_visualization_service.record_interaction(
                visualization_id=visualization.visualization_id,
                user_id="user_123",
                interaction_type=interaction['type'],
                interaction_data=interaction['data'],
                coordinates=interaction['coords']
            )
            assert success is True
        
        # Verify interactions were recorded
        updated_viz = await interactive_visualization_service.get_visualization(
            visualization.visualization_id, "user_123"
        )
        assert len(updated_viz.interaction_history) == 4
        
        # Check interaction types
        recorded_types = [event.interaction_type for event in updated_viz.interaction_history]
        assert InteractionType.CLICK in recorded_types
        assert InteractionType.BRUSH in recorded_types
        assert InteractionType.ZOOM in recorded_types
        assert InteractionType.FILTER in recorded_types
        
        # Check interaction data integrity
        brush_interaction = next(
            event for event in updated_viz.interaction_history 
            if event.interaction_type == InteractionType.BRUSH
        )
        assert brush_interaction.data['points'] == 15
        assert brush_interaction.coordinates['x'] == 150
        
        print("✓ Advanced interaction tracking test passed")
    
    async def test_multi_user_collaborative_session(self):
        """Test multi-user collaborative session management"""
        # Create visualization
        viz_data = VisualizationData(
            data={'collaborative': True},
            layout={'title': 'Multi-user Collaboration Test'},
            config={}
        )
        
        visualization = await interactive_visualization_service.create_visualization(
            title="Multi-user Collaboration",
            description="Test multi-user collaborative features",
            visualization_type=VisualizationType.PLOTLY,
            data=viz_data,
            owner_id="owner_123"
        )
        
        # Add multiple collaborators
        collaborators = ["user_456", "user_789", "user_101", "user_202"]
        for collaborator in collaborators:
            await interactive_visualization_service.add_collaborator(
                visualization.visualization_id, collaborator, "owner_123"
            )
        
        # All users join session
        all_users = ["owner_123"] + collaborators
        for user in all_users:
            success = await interactive_visualization_service.join_session(
                visualization.visualization_id, user
            )
            assert success is True
        
        # Check active sessions
        active_users = interactive_visualization_service.active_sessions.get(
            visualization.visualization_id, []
        )
        assert len(active_users) == 5
        assert all(user in active_users for user in all_users)
        
        # Simulate concurrent updates from different users
        updates = [
            ("user_456", {'data_point_1': 10}),
            ("user_789", {'data_point_2': 20}),
            ("user_101", {'data_point_3': 30})
        ]
        
        for user, update_data in updates:
            success = await interactive_visualization_service.update_visualization_data(
                visualization_id=visualization.visualization_id,
                user_id=user,
                data_updates=update_data,
                update_type='data'
            )
            assert success is True
        
        # Check that all updates were recorded
        final_updates = await interactive_visualization_service.get_visualization_updates(
            visualization.visualization_id
        )
        assert len(final_updates) >= 3
        
        # Users leave session gradually
        for user in collaborators[:2]:
            await interactive_visualization_service.leave_session(
                visualization.visualization_id, user
            )
        
        # Check remaining active users
        remaining_users = interactive_visualization_service.active_sessions.get(
            visualization.visualization_id, []
        )
        assert len(remaining_users) == 3
        assert "user_456" not in remaining_users
        assert "user_789" not in remaining_users
        
        print("✓ Multi-user collaborative session test passed")

async def run_enhanced_tests():
    """Run all enhanced tests"""
    test_instance = TestEnhancedInteractiveVisualization()
    
    print("Running Enhanced Interactive Visualization Tests...")
    print("=" * 70)
    
    try:
        # Setup
        test_instance.setup_method()
        
        # Run enhanced tests
        await test_instance.test_plotly_visualization_with_traces()
        await test_instance.test_d3_network_visualization()
        await test_instance.test_chartjs_dashboard_visualization()
        await test_instance.test_real_time_data_streaming()
        await test_instance.test_collaborative_annotations_with_replies()
        await test_instance.test_enhanced_embed_code_generation()
        await test_instance.test_visualization_snapshots()
        await test_instance.test_advanced_interaction_tracking()
        await test_instance.test_multi_user_collaborative_session()
        
        print("=" * 70)
        print("✅ All Enhanced Interactive Visualization tests passed!")
        
        # Enhanced test summary
        print(f"\nEnhanced Test Summary:")
        print(f"- Total visualizations: {len(interactive_visualization_service.visualizations)}")
        print(f"- Supported libraries: Plotly, D3.js, Chart.js, Custom")
        print(f"- Features tested: Real-time updates, Collaboration, Embedding, Snapshots")
        print(f"- Active sessions: {len(interactive_visualization_service.active_sessions)}")
        
        if hasattr(interactive_visualization_service, 'snapshots'):
            print(f"- Snapshots created: {len(interactive_visualization_service.snapshots)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_enhanced_tests())
    exit(0 if success else 1)