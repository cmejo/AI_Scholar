"""
Tests for Interactive Content Version Control API Endpoints

This module tests the REST API endpoints for version control functionality
including versioning, branching, merging, and backup features.
"""

import asyncio
import json
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import the router
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.interactive_content_version_control_endpoints import router
from services.interactive_content_version_control import (
    interactive_content_version_control,
    ContentType
)

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)

class TestInteractiveContentVersionControlAPI:
    """Test cases for interactive content version control API"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Clear any existing data
        interactive_content_version_control.versions.clear()
        interactive_content_version_control.branches.clear()
        interactive_content_version_control.merge_requests.clear()
        interactive_content_version_control.backups.clear()
    
    def test_initialize_content_versioning_api(self):
        """Test initializing version control via API"""
        content_id = "notebook_api_test"
        
        # Sample notebook data
        request_data = {
            "content_type": "notebook",
            "initial_data": {
                "cells": [
                    {"type": "markdown", "content": "# API Test Notebook"},
                    {"type": "code", "content": "print('Hello from API!')"}
                ],
                "metadata": {"kernel": "python3"}
            },
            "commit_message": "Initial API creation"
        }
        
        # Make API request
        response = client.post(f"/api/content/version-control/{content_id}/initialize", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "version_id" in data
        assert data["content_id"] == content_id
        assert data["content_type"] == "notebook"
        assert data["version_number"] == 1
        assert data["commit_message"] == "Initial API creation"
        assert data["author_id"] == "user_123"  # From mock auth
        
        print("✓ Initialize content versioning API test passed")
    
    def test_commit_changes_api(self):
        """Test committing changes via API"""
        content_id = "viz_api_test"
        
        # Initialize first
        init_data = {
            "content_type": "visualization",
            "initial_data": {"title": "API Test Viz", "data": {"x": [1, 2], "y": [3, 4]}},
            "commit_message": "Initial version"
        }
        
        init_response = client.post(f"/api/content/version-control/{content_id}/initialize", json=init_data)
        assert init_response.status_code == 200
        
        # Commit changes
        commit_data = {
            "updated_data": {
                "title": "Updated API Test Viz",
                "data": {"x": [1, 2, 3], "y": [3, 4, 5]},
                "layout": {"title": "New Layout"}
            },
            "commit_message": "Added data point and layout",
            "branch_name": "main"
        }
        
        response = client.post(f"/api/content/version-control/{content_id}/commit", json=commit_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["version_number"] == 2
        assert data["commit_message"] == "Added data point and layout"
        assert len(data["parent_versions"]) == 1
        
        print("✓ Commit changes API test passed")
    
    def test_get_version_history_api(self):
        """Test getting version history via API"""
        content_id = "history_api_test"
        
        # Initialize and create multiple versions
        init_data = {
            "content_type": "script",
            "initial_data": {"code": "print('v1')"},
            "commit_message": "Version 1"
        }
        
        client.post(f"/api/content/version-control/{content_id}/initialize", json=init_data)
        
        # Add second version
        commit_data = {
            "updated_data": {"code": "print('v2')"},
            "commit_message": "Version 2"
        }
        
        client.post(f"/api/content/version-control/{content_id}/commit", json=commit_data)
        
        # Get history
        response = client.get(f"/api/content/version-control/{content_id}/history")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert data[0]["version_number"] == 1
        assert data[1]["version_number"] == 2
        assert data[0]["commit_message"] == "Version 1"
        assert data[1]["commit_message"] == "Version 2"
        
        print("✓ Get version history API test passed")
    
    def test_get_version_diff_api(self):
        """Test getting version diff via API"""
        content_id = "diff_api_test"
        
        # Initialize
        init_data = {
            "content_type": "dataset",
            "initial_data": {"a": 1, "b": 2, "c": 3},
            "commit_message": "Initial data"
        }
        
        init_response = client.post(f"/api/content/version-control/{content_id}/initialize", json=init_data)
        version1_id = init_response.json()["version_id"]
        
        # Create second version
        commit_data = {
            "updated_data": {"a": 1, "b": 20, "d": 4},  # modified b, deleted c, added d
            "commit_message": "Modified data"
        }
        
        commit_response = client.post(f"/api/content/version-control/{content_id}/commit", json=commit_data)
        version2_id = commit_response.json()["version_id"]
        
        # Get diff
        response = client.get(f"/api/content/version-control/{content_id}/diff/{version1_id}/{version2_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "diff_id" in data
        assert data["from_version"] == version1_id
        assert data["to_version"] == version2_id
        assert data["summary"]["added"] == 1  # 'd' was added
        assert data["summary"]["modified"] == 1  # 'b' was modified
        assert data["summary"]["deleted"] == 1  # 'c' was deleted
        
        print("✓ Get version diff API test passed")
    
    def test_create_branch_api(self):
        """Test creating branch via API"""
        content_id = "branch_api_test"
        
        # Initialize
        init_data = {
            "content_type": "notebook",
            "initial_data": {"feature": "main"},
            "commit_message": "Initial version"
        }
        
        init_response = client.post(f"/api/content/version-control/{content_id}/initialize", json=init_data)
        version_id = init_response.json()["version_id"]
        
        # Create branch
        branch_data = {
            "branch_name": "feature/api-test",
            "from_version": version_id,
            "description": "API test feature branch"
        }
        
        response = client.post(f"/api/content/version-control/{content_id}/branches", json=branch_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["branch_name"] == "feature/api-test"
        assert data["head_version"] == version_id
        assert data["created_by"] == "user_123"
        assert data["description"] == "API test feature branch"
        assert data["is_active"] == True
        
        print("✓ Create branch API test passed")
    
    def test_get_branches_api(self):
        """Test getting branches via API"""
        content_id = "branches_api_test"
        
        # Initialize (creates main branch)
        init_data = {
            "content_type": "visualization",
            "initial_data": {"data": "test"},
            "commit_message": "Initial version"
        }
        
        init_response = client.post(f"/api/content/version-control/{content_id}/initialize", json=init_data)
        version_id = init_response.json()["version_id"]
        
        # Create additional branch
        branch_data = {
            "branch_name": "develop",
            "from_version": version_id,
            "description": "Development branch"
        }
        
        client.post(f"/api/content/version-control/{content_id}/branches", json=branch_data)
        
        # Get branches
        response = client.get(f"/api/content/version-control/{content_id}/branches")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        branch_names = [branch["branch_name"] for branch in data]
        assert "main" in branch_names
        assert "develop" in branch_names
        
        print("✓ Get branches API test passed")
    
    def test_merge_branches_api(self):
        """Test merging branches via API"""
        content_id = "merge_api_test"
        
        # Initialize
        init_data = {
            "content_type": "script",
            "initial_data": {"base": "data", "count": 0},
            "commit_message": "Initial version"
        }
        
        init_response = client.post(f"/api/content/version-control/{content_id}/initialize", json=init_data)
        version_id = init_response.json()["version_id"]
        
        # Create feature branch
        branch_data = {
            "branch_name": "feature",
            "from_version": version_id,
            "description": "Feature branch"
        }
        
        client.post(f"/api/content/version-control/{content_id}/branches", json=branch_data)
        
        # Make changes in feature branch
        feature_commit = {
            "updated_data": {"base": "data", "count": 0, "feature_flag": True},
            "commit_message": "Added feature flag",
            "branch_name": "feature"
        }
        
        client.post(f"/api/content/version-control/{content_id}/commit", json=feature_commit)
        
        # Make changes in main branch
        main_commit = {
            "updated_data": {"base": "data", "count": 0, "updated": True},
            "commit_message": "Updated main",
            "branch_name": "main"
        }
        
        client.post(f"/api/content/version-control/{content_id}/commit", json=main_commit)
        
        # Merge branches
        merge_data = {
            "source_branch": "feature",
            "target_branch": "main",
            "merge_message": "Merge feature into main"
        }
        
        response = client.post(f"/api/content/version-control/{content_id}/merge", json=merge_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["source_branch"] == "feature"
        assert data["target_branch"] == "main"
        assert data["status"] in ["success", "conflict"]  # Either is acceptable
        assert data["author_id"] == "user_123"
        
        print("✓ Merge branches API test passed")
    
    def test_revert_to_version_api(self):
        """Test reverting to version via API"""
        content_id = "revert_api_test"
        
        # Initialize
        init_data = {
            "content_type": "dataset",
            "initial_data": {"step": 1, "data": "initial"},
            "commit_message": "Step 1"
        }
        
        init_response = client.post(f"/api/content/version-control/{content_id}/initialize", json=init_data)
        version1_id = init_response.json()["version_id"]
        
        # Create version 2
        commit_data = {
            "updated_data": {"step": 2, "data": "updated"},
            "commit_message": "Step 2"
        }
        
        client.post(f"/api/content/version-control/{content_id}/commit", json=commit_data)
        
        # Create version 3
        commit_data = {
            "updated_data": {"step": 3, "data": "final", "extra": "field"},
            "commit_message": "Step 3"
        }
        
        client.post(f"/api/content/version-control/{content_id}/commit", json=commit_data)
        
        # Revert to version 1
        revert_data = {
            "version_id": version1_id,
            "branch_name": "main"
        }
        
        response = client.post(f"/api/content/version-control/{content_id}/revert", json=revert_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["version_number"] == 4  # New version created for revert
        assert "reverted_from" in data["metadata"]
        assert data["metadata"]["reverted_from"] == version1_id
        
        print("✓ Revert to version API test passed")
    
    def test_backup_and_restore_api(self):
        """Test backup and restore via API"""
        content_id = "backup_api_test"
        
        # Initialize
        init_data = {
            "content_type": "notebook",
            "initial_data": {"important": "data", "timestamp": "2024-01-01"},
            "commit_message": "Initial data"
        }
        
        client.post(f"/api/content/version-control/{content_id}/initialize", json=init_data)
        
        # Make changes
        commit_data = {
            "updated_data": {"important": "modified_data", "timestamp": "2024-01-02", "new_field": "added"},
            "commit_message": "Important changes"
        }
        
        client.post(f"/api/content/version-control/{content_id}/commit", json=commit_data)
        
        # Create backup
        backup_data = {"backup_type": "manual"}
        
        backup_response = client.post(f"/api/content/version-control/{content_id}/backup", json=backup_data)
        
        assert backup_response.status_code == 200
        backup_data = backup_response.json()
        backup_id = backup_data["backup_id"]
        
        assert backup_data["backup_type"] == "manual"
        assert backup_data["content_id"] == content_id
        
        # Make corrupting changes
        corrupt_data = {
            "updated_data": {"important": "corrupted", "timestamp": "2024-01-03"},
            "commit_message": "Corrupted data"
        }
        
        client.post(f"/api/content/version-control/{content_id}/commit", json=corrupt_data)
        
        # Restore from backup
        restore_data = {"backup_id": backup_id}
        
        response = client.post(f"/api/content/version-control/{content_id}/restore", json=restore_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["version_number"] == 4  # New version created for restore
        assert "restored_from_backup" in data["metadata"]
        assert data["metadata"]["restored_from_backup"] == backup_id
        
        print("✓ Backup and restore API test passed")
    
    def test_get_backups_api(self):
        """Test getting backups via API"""
        content_id = "backups_list_test"
        
        # Initialize
        init_data = {
            "content_type": "visualization",
            "initial_data": {"data": "test"},
            "commit_message": "Initial version"
        }
        
        client.post(f"/api/content/version-control/{content_id}/initialize", json=init_data)
        
        # Create manual backup
        backup_data = {"backup_type": "manual"}
        client.post(f"/api/content/version-control/{content_id}/backup", json=backup_data)
        
        # Get backups
        response = client.get(f"/api/content/version-control/{content_id}/backups")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have at least 2 backups (initial + manual)
        assert len(data) >= 2
        backup_types = [backup["backup_type"] for backup in data]
        assert "initial" in backup_types
        assert "manual" in backup_types
        
        print("✓ Get backups API test passed")
    
    def test_health_check_api(self):
        """Test health check endpoint"""
        response = client.get("/api/content/version-control/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "interactive-content-version-control"
        assert "content_items" in data
        assert "total_branches" in data
        assert "supported_content_types" in data
        
        print("✓ Health check API test passed")
    
    def test_error_handling_api(self):
        """Test API error handling"""
        # Test with non-existent content
        response = client.get("/api/content/version-control/non_existent/history")
        assert response.status_code == 200  # Should return empty list
        assert response.json() == []
        
        # Test invalid content type
        invalid_init = {
            "content_type": "invalid_type",
            "initial_data": {"test": "data"},
            "commit_message": "Should fail"
        }
        
        response = client.post("/api/content/version-control/test/initialize", json=invalid_init)
        assert response.status_code == 400
        
        # Test commit to non-existent content
        commit_data = {
            "updated_data": {"test": "data"},
            "commit_message": "Should fail"
        }
        
        response = client.post("/api/content/version-control/non_existent/commit", json=commit_data)
        assert response.status_code == 404
        
        print("✓ Error handling API test passed")

def run_tests():
    """Run all API tests"""
    test_instance = TestInteractiveContentVersionControlAPI()
    
    print("Running Interactive Content Version Control API Tests...")
    print("=" * 70)
    
    try:
        # Setup
        test_instance.setup_method()
        
        # Run tests
        test_instance.test_initialize_content_versioning_api()
        test_instance.test_commit_changes_api()
        test_instance.test_get_version_history_api()
        test_instance.test_get_version_diff_api()
        test_instance.test_create_branch_api()
        test_instance.test_get_branches_api()
        test_instance.test_merge_branches_api()
        test_instance.test_revert_to_version_api()
        test_instance.test_backup_and_restore_api()
        test_instance.test_get_backups_api()
        test_instance.test_health_check_api()
        test_instance.test_error_handling_api()
        
        print("=" * 70)
        print("✅ All Interactive Content Version Control API tests passed!")
        
        # Test summary
        print(f"\nAPI Test Summary:")
        print(f"- Content items versioned: {len(interactive_content_version_control.versions)}")
        print(f"- Total branches: {sum(len(branches) for branches in interactive_content_version_control.branches.values())}")
        print(f"- Merge requests: {len(interactive_content_version_control.merge_requests)}")
        print(f"- Backup records: {sum(len(backups) for backups in interactive_content_version_control.backups.values())}")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        interactive_content_version_control.cleanup()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)