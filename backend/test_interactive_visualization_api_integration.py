"""
API Integration tests for Interactive Visualization Service

This module tests the REST API endpoints for interactive visualizations
including creation, updates, annotations, collaboration, and embedding.
"""

import asyncio
import json
from fastapi.testclient import TestClient
from fastapi import FastAPI
from api.interactive_visualization_endpoints import router
from services.interactive_visualization_service import interactive_visualization_service

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)

class TestInteractiveVisualizationAPI:
    """Test cases for interactive visualization API endpoints"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Clear any existing data
        interactive_visualization_service.visualizations.clear()
        interactive_visualization_service.active_sessions.clear()
        interactive_visualization_service.update_queue.clear()
    
    def test_create_plotly_visualization_api(self):
        """Test creating Plotly visualization via API"""
        request_data = {
            "title": "API Test Plotly Chart",
            "description": "Test Plotly visualization via API",
            "visualization_type": "plotly",
            "data": {
                "x": [1, 2, 3, 4, 5],
                "y": [2, 4, 6, 8, 10],
                "type": "scatter",
                "mode": "lines+markers"
            },
            "layout": {
                "title": "API Test Chart",
                "xaxis": {"title": "X Axis"},
                "yaxis": {"title": "Y Axis"}
            },
            "config": {
                "displayModeBar": True,
                "responsive": True
            },
            "traces": [{
                "x": [1, 2, 3, 4, 5],
                "y": [2, 4, 6, 8, 10],
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Test Data"
            }],
            "tags": ["api", "test", "plotly"]
        }
        
        response = client.post("/api/visualizations/", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "visualization_id" in data
        assert data["message"] == "Visualization created successfully"
        
        # Verify visualization was created
        viz_id = data["visualization_id"]
        get_response = client.get(f"/api/visualizations/{viz_id}")
        assert get_response.status_code == 200
        
        viz_data = get_response.json()
        assert viz_data["title"] == "API Test Plotly Chart"
        assert viz_data["visualization_type"] == "plotly"
        assert len(viz_data["data"]["traces"]) == 1
        
        print("✓ Create Plotly visualization API test passed")
    
    def test_create_d3_visualization_api(self):
        """Test creating D3 visualization via API"""
        request_data = {
            "title": "API Test D3 Network",
            "description": "Test D3 network visualization via API",
            "visualization_type": "d3",
            "data": {
                "nodes": [
                    {"id": "A", "group": 1},
                    {"id": "B", "group": 1},
                    {"id": "C", "group": 2}
                ],
                "links": [
                    {"source": "A", "target": "B", "value": 1},
                    {"source": "B", "target": "C", "value": 2}
                ]
            },
            "layout": {
                "width": 800,
                "height": 600,
                "force": {
                    "charge": -300,
                    "linkDistance": 50
                }
            },
            "config": {
                "interactive": True,
                "zoomable": True
            },
            "tags": ["api", "test", "d3", "network"]
        }
        
        response = client.post("/api/visualizations/", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "visualization_id" in data
        
        # Verify visualization was created
        viz_id = data["visualization_id"]
        get_response = client.get(f"/api/visualizations/{viz_id}")
        assert get_response.status_code == 200
        
        viz_data = get_response.json()
        assert viz_data["title"] == "API Test D3 Network"
        assert viz_data["visualization_type"] == "d3"
        assert len(viz_data["data"]["data"]["nodes"]) == 3
        assert len(viz_data["data"]["data"]["links"]) == 2
        
        print("✓ Create D3 visualization API test passed")
    
    def test_list_visualizations_api(self):
        """Test listing visualizations via API"""
        # Create multiple visualizations first
        visualizations = [
            {
                "title": "Test Viz 1",
                "description": "First test visualization",
                "visualization_type": "plotly",
                "data": {"test": "data1"},
                "tags": ["test1"]
            },
            {
                "title": "Test Viz 2", 
                "description": "Second test visualization",
                "visualization_type": "d3",
                "data": {"test": "data2"},
                "tags": ["test2"]
            }
        ]
        
        created_ids = []
        for viz_data in visualizations:
            response = client.post("/api/visualizations/", json=viz_data)
            assert response.status_code == 200
            created_ids.append(response.json()["visualization_id"])
        
        # List visualizations
        response = client.get("/api/visualizations/")
        assert response.status_code == 200
        
        viz_list = response.json()
        assert len(viz_list) == 2
        assert all(viz["visualization_id"] in created_ids for viz in viz_list)
        
        # Check visualization summaries
        titles = [viz["title"] for viz in viz_list]
        assert "Test Viz 1" in titles
        assert "Test Viz 2" in titles
        
        print("✓ List visualizations API test passed")
    
    def test_update_visualization_data_api(self):
        """Test updating visualization data via API"""
        # Create visualization first
        create_data = {
            "title": "Update Test",
            "description": "Test data updates",
            "visualization_type": "plotly",
            "data": {"values": [1, 2, 3]},
            "layout": {"title": "Original"},
            "config": {}
        }
        
        create_response = client.post("/api/visualizations/", json=create_data)
        assert create_response.status_code == 200
        viz_id = create_response.json()["visualization_id"]
        
        # Update data
        update_data = {
            "data_updates": {"values": [4, 5, 6, 7, 8]},
            "update_type": "data"
        }
        
        update_response = client.put(f"/api/visualizations/{viz_id}/data", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["message"] == "Visualization updated successfully"
        
        # Verify update
        get_response = client.get(f"/api/visualizations/{viz_id}")
        assert get_response.status_code == 200
        
        viz_data = get_response.json()
        assert viz_data["data"]["data"]["values"] == [4, 5, 6, 7, 8]
        assert viz_data["version"] > 1
        
        print("✓ Update visualization data API test passed")
    
    def test_annotations_api(self):
        """Test annotation operations via API"""
        # Create visualization first
        create_data = {
            "title": "Annotation Test",
            "description": "Test annotations",
            "visualization_type": "plotly",
            "data": {"test": "data"},
            "layout": {"title": "Annotation Test"},
            "config": {}
        }
        
        create_response = client.post("/api/visualizations/", json=create_data)
        assert create_response.status_code == 200
        viz_id = create_response.json()["visualization_id"]
        
        # Add annotation
        annotation_data = {
            "content": "This is a test annotation",
            "position": {"x": 100, "y": 200},
            "annotation_type": "text",
            "style": {"color": "red", "fontSize": 14}
        }
        
        add_response = client.post(f"/api/visualizations/{viz_id}/annotations", json=annotation_data)
        assert add_response.status_code == 200
        annotation_id = add_response.json()["annotation_id"]
        
        # Verify annotation was added
        get_response = client.get(f"/api/visualizations/{viz_id}")
        assert get_response.status_code == 200
        
        viz_data = get_response.json()
        assert len(viz_data["annotations"]) == 1
        assert viz_data["annotations"][0]["content"] == "This is a test annotation"
        assert viz_data["annotations"][0]["position"]["x"] == 100
        
        # Update annotation
        update_data = {
            "updates": {"content": "Updated annotation content"}
        }
        
        update_response = client.put(
            f"/api/visualizations/{viz_id}/annotations/{annotation_id}", 
            json=update_data
        )
        assert update_response.status_code == 200
        
        # Verify update
        get_response = client.get(f"/api/visualizations/{viz_id}")
        viz_data = get_response.json()
        assert viz_data["annotations"][0]["content"] == "Updated annotation content"
        
        # Delete annotation
        delete_response = client.delete(f"/api/visualizations/{viz_id}/annotations/{annotation_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_response = client.get(f"/api/visualizations/{viz_id}")
        viz_data = get_response.json()
        assert len(viz_data["annotations"]) == 0
        
        print("✓ Annotations API test passed")
    
    def test_interaction_recording_api(self):
        """Test interaction recording via API"""
        # Create visualization first
        create_data = {
            "title": "Interaction Test",
            "description": "Test interaction recording",
            "visualization_type": "plotly",
            "data": {"test": "data"},
            "layout": {"title": "Interaction Test"},
            "config": {}
        }
        
        create_response = client.post("/api/visualizations/", json=create_data)
        assert create_response.status_code == 200
        viz_id = create_response.json()["visualization_id"]
        
        # Record interactions
        interactions = [
            {
                "interaction_type": "click",
                "interaction_data": {"element": "data-point", "value": 42},
                "coordinates": {"x": 100, "y": 200}
            },
            {
                "interaction_type": "hover",
                "interaction_data": {"element": "axis", "position": "x"}
            },
            {
                "interaction_type": "zoom",
                "interaction_data": {"scale": 1.5, "center": [400, 300]}
            }
        ]
        
        for interaction in interactions:
            response = client.post(f"/api/visualizations/{viz_id}/interactions", json=interaction)
            assert response.status_code == 200
            assert response.json()["message"] == "Interaction recorded successfully"
        
        print("✓ Interaction recording API test passed")
    
    def test_collaboration_api(self):
        """Test collaboration features via API"""
        # Create visualization first
        create_data = {
            "title": "Collaboration Test",
            "description": "Test collaboration features",
            "visualization_type": "plotly",
            "data": {"test": "data"},
            "layout": {"title": "Collaboration Test"},
            "config": {}
        }
        
        create_response = client.post("/api/visualizations/", json=create_data)
        assert create_response.status_code == 200
        viz_id = create_response.json()["visualization_id"]
        
        # Add collaborator
        collaborator_data = {"collaborator_id": "user_456"}
        add_response = client.post(f"/api/visualizations/{viz_id}/collaborators", json=collaborator_data)
        assert add_response.status_code == 200
        assert add_response.json()["message"] == "Collaborator added successfully"
        
        # Verify collaborator was added
        get_response = client.get(f"/api/visualizations/{viz_id}")
        viz_data = get_response.json()
        assert "user_456" in viz_data["collaborators"]
        
        # Join session
        join_response = client.post(f"/api/visualizations/{viz_id}/sessions/join")
        assert join_response.status_code == 200
        assert join_response.json()["message"] == "Joined session successfully"
        
        # Leave session
        leave_response = client.post(f"/api/visualizations/{viz_id}/sessions/leave")
        assert leave_response.status_code == 200
        assert leave_response.json()["message"] == "Left session successfully"
        
        # Remove collaborator
        remove_response = client.delete(f"/api/visualizations/{viz_id}/collaborators/user_456")
        assert remove_response.status_code == 200
        assert remove_response.json()["message"] == "Collaborator removed successfully"
        
        # Verify collaborator was removed
        get_response = client.get(f"/api/visualizations/{viz_id}")
        viz_data = get_response.json()
        assert "user_456" not in viz_data["collaborators"]
        
        print("✓ Collaboration API test passed")
    
    def test_embed_code_generation_api(self):
        """Test embed code generation via API"""
        # Create visualization first
        create_data = {
            "title": "Embed Test",
            "description": "Test embed code generation",
            "visualization_type": "plotly",
            "data": {"x": [1, 2, 3], "y": [4, 5, 6]},
            "layout": {"title": "Embed Test"},
            "config": {"displayModeBar": True},
            "traces": [{"x": [1, 2, 3], "y": [4, 5, 6], "type": "scatter"}]
        }
        
        create_response = client.post("/api/visualizations/", json=create_data)
        assert create_response.status_code == 200
        viz_id = create_response.json()["visualization_id"]
        
        # Generate embed code
        embed_data = {
            "width": 600,
            "height": 400,
            "interactive": True
        }
        
        embed_response = client.post(f"/api/visualizations/{viz_id}/embed", json=embed_data)
        assert embed_response.status_code == 200
        
        embed_result = embed_response.json()
        assert "embed_code" in embed_result
        assert embed_result["width"] == 600
        assert embed_result["height"] == 400
        assert embed_result["interactive"] is True
        
        # Verify embed code contains expected elements
        embed_code = embed_result["embed_code"]
        assert "plotly-div-" in embed_code
        assert "Plotly.newPlot" in embed_code
        assert "600px" in embed_code
        assert "400px" in embed_code
        
        print("✓ Embed code generation API test passed")
    
    def test_get_updates_api(self):
        """Test getting visualization updates via API"""
        # Create visualization first
        create_data = {
            "title": "Updates Test",
            "description": "Test getting updates",
            "visualization_type": "plotly",
            "data": {"values": [1, 2, 3]},
            "layout": {"title": "Updates Test"},
            "config": {}
        }
        
        create_response = client.post("/api/visualizations/", json=create_data)
        assert create_response.status_code == 200
        viz_id = create_response.json()["visualization_id"]
        
        # Make some updates
        update_data = {
            "data_updates": {"values": [4, 5, 6]},
            "update_type": "data"
        }
        
        client.put(f"/api/visualizations/{viz_id}/data", json=update_data)
        
        # Get updates
        updates_response = client.get(f"/api/visualizations/{viz_id}/updates")
        assert updates_response.status_code == 200
        
        updates_data = updates_response.json()
        assert "updates" in updates_data
        assert "count" in updates_data
        assert updates_data["count"] > 0
        assert len(updates_data["updates"]) > 0
        
        # Check update structure
        update = updates_data["updates"][0]
        assert "update_id" in update
        assert "user_id" in update
        assert "update_type" in update
        assert "changes" in update
        assert "timestamp" in update
        
        print("✓ Get updates API test passed")
    
    def test_supported_libraries_api(self):
        """Test getting supported libraries via API"""
        response = client.get("/api/visualizations/libraries/supported")
        assert response.status_code == 200
        
        data = response.json()
        assert "libraries" in data
        assert "message" in data
        
        libraries = data["libraries"]
        assert "plotly" in libraries
        assert "d3" in libraries
        assert "chartjs" in libraries
        
        # Check library details
        plotly_info = libraries["plotly"]
        assert "name" in plotly_info
        assert "version" in plotly_info
        assert "cdn" in plotly_info
        assert "features" in plotly_info
        
        print("✓ Supported libraries API test passed")
    
    def test_health_check_api(self):
        """Test health check endpoint"""
        response = client.get("/api/visualizations/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "interactive-visualization"
        assert "visualizations_count" in data
        assert "active_sessions" in data
        assert "supported_types" in data
        
        print("✓ Health check API test passed")
    
    def test_error_handling_api(self):
        """Test API error handling"""
        # Test invalid visualization type
        invalid_data = {
            "title": "Invalid Test",
            "description": "Test invalid type",
            "visualization_type": "invalid_type",
            "data": {"test": "data"}
        }
        
        response = client.post("/api/visualizations/", json=invalid_data)
        assert response.status_code == 400
        
        # Test accessing non-existent visualization
        response = client.get("/api/visualizations/non_existent_id")
        assert response.status_code == 404
        
        # Test updating non-existent visualization
        update_data = {"data_updates": {"test": "data"}}
        response = client.put("/api/visualizations/non_existent_id/data", json=update_data)
        assert response.status_code == 404
        
        print("✓ Error handling API test passed")

def run_api_tests():
    """Run all API tests"""
    test_instance = TestInteractiveVisualizationAPI()
    
    print("Running Interactive Visualization API Integration Tests...")
    print("=" * 80)
    
    try:
        # Setup
        test_instance.setup_method()
        
        # Run API tests
        test_instance.test_create_plotly_visualization_api()
        test_instance.test_create_d3_visualization_api()
        test_instance.test_list_visualizations_api()
        test_instance.test_update_visualization_data_api()
        test_instance.test_annotations_api()
        test_instance.test_interaction_recording_api()
        test_instance.test_collaboration_api()
        test_instance.test_embed_code_generation_api()
        test_instance.test_get_updates_api()
        test_instance.test_supported_libraries_api()
        test_instance.test_health_check_api()
        test_instance.test_error_handling_api()
        
        print("=" * 80)
        print("✅ All Interactive Visualization API tests passed!")
        
        # API test summary
        print(f"\nAPI Test Summary:")
        print(f"- Endpoints tested: 12")
        print(f"- CRUD operations: ✓")
        print(f"- Real-time features: ✓")
        print(f"- Collaboration: ✓")
        print(f"- Error handling: ✓")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_api_tests()
    exit(0 if success else 1)