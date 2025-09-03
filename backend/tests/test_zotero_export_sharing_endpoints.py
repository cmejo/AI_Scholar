"""
Tests for Zotero Export and Sharing API Endpoints

This module tests the REST API endpoints for conversation export,
reference sharing, and research project collections.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from backend.api.zotero_export_sharing_endpoints import router
from backend.models.schemas import User


# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestZoteroExportSharingEndpoints:
    """Test cases for Zotero export and sharing endpoints"""
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        return User(
            id="user123",
            email="test@example.com",
            username="testuser"
        )
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {"Authorization": "Bearer test-token"}

    def test_export_conversation_success(self, mock_user, mock_db, auth_headers):
        """Test successful conversation export"""
        # Setup
        request_data = {
            "conversation_id": "conv123",
            "conversation_data": {
                "title": "Test Conversation",
                "messages": [
                    {"content": "Test message with zotero_ref:123"}
                ]
            },
            "citation_style": "apa"
        }
        
        expected_response = {
            "export_id": "export123",
            "conversation": {
                "id": "conv123",
                "title": "Test Conversation",
                "messages": [{"content": "Test message with (Citation)"}]
            },
            "bibliography": ["Citation text"],
            "citation_count": 1,
            "export_date": "2024-01-15T10:00:00Z"
        }
        
        with patch('backend.api.zotero_export_sharing_endpoints.get_current_user', return_value=mock_user), \
             patch('backend.api.zotero_export_sharing_endpoints.get_db', return_value=mock_db), \
             patch('backend.api.zotero_export_sharing_endpoints.ZoteroExportSharingService') as mock_service_class:
            
            mock_service = mock_service_class.return_value
            mock_service.export_conversation_with_citations = AsyncMock(return_value=expected_response)
            
            # Execute
            response = client.post(
                "/api/zotero/export-sharing/conversations/export",
                json=request_data,
                headers=auth_headers
            )
            
            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["export_id"] == "export123"
            assert data["citation_count"] == 1
            mock_service.export_conversation_with_citations.assert_called_once()

    def test_export_conversation_validation_error(self, mock_user, mock_db, auth_headers):
        """Test conversation export with validation error"""
        # Setup - missing required fields
        request_data = {
            "conversation_id": "conv123"
            # Missing conversation_data
        }
        
        with patch('backend.api.zotero_export_sharing_endpoints.get_current_user', return_value=mock_user), \
             patch('backend.api.zotero_export_sharing_endpoints.get_db', return_value=mock_db):
            
            # Execute
            response = client.post(
                "/api/zotero/export-sharing/conversations/export",
                json=request_data,
                headers=auth_headers
            )
            
            # Verify
            assert response.status_code == 422  # Validation error

    def test_export_conversation_service_error(self, mock_user, mock_db, auth_headers):
        """Test conversation export with service error"""
        # Setup
        request_data = {
            "conversation_id": "conv123",
            "conversation_data": {
                "messages": [{"content": "test"}]
            }
        }
        
        with patch('backend.api.zotero_export_sharing_endpoints.get_current_user', return_value=mock_user), \
             patch('backend.api.zotero_export_sharing_endpoints.get_db', return_value=mock_db), \
             patch('backend.api.zotero_export_sharing_endpoints.ZoteroExportSharingService') as mock_service_class:
            
            mock_service = mock_service_class.return_value
            mock_service.export_conversation_with_citations = AsyncMock(
                side_effect=Exception("Service error")
            )
            
            # Execute
            response = client.post(
                "/api/zotero/export-sharing/conversations/export",
                json=request_data,
                headers=auth_headers
            )
            
            # Verify
            assert response.status_code == 500
            assert "Failed to export conversation" in response.json()["detail"]

    def test_share_reference_success(self, mock_user, mock_db, auth_headers):
        """Test successful reference sharing"""
        # Setup
        request_data = {
            "target_user_id": "user456",
            "reference_id": "ref123",
            "permission_level": "read",
            "message": "Check this out"
        }
        
        expected_response = {
            "share_id": "share123",
            "reference_id": "ref123",
            "reference_title": "Test Paper",
            "shared_with": "user456",
            "permission_level": "read",
            "message": "Check this out",
            "shared_at": "2024-01-15T10:00:00Z"
        }
        
        with patch('backend.api.zotero_export_sharing_endpoints.get_current_user', return_value=mock_user), \
             patch('backend.api.zotero_export_sharing_endpoints.get_db', return_value=mock_db), \
             patch('backend.api.zotero_export_sharing_endpoints.ZoteroExportSharingService') as mock_service_class:
            
            mock_service = mock_service_class.return_value
            mock_service.share_reference_with_user = AsyncMock(return_value=expected_response)
            
            # Execute
            response = client.post(
                "/api/zotero/export-sharing/references/share",
                json=request_data,
                headers=auth_headers
            )
            
            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["share_id"] == "share123"
            assert data["reference_title"] == "Test Paper"
            mock_service.share_reference_with_user.assert_called_once()

    def test_share_reference_not_found(self, mock_user, mock_db, auth_headers):
        """Test sharing non-existent reference"""
        # Setup
        request_data = {
            "target_user_id": "user456",
            "reference_id": "nonexistent",
            "permission_level": "read"
        }
        
        with patch('backend.api.zotero_export_sharing_endpoints.get_current_user', return_value=mock_user), \
             patch('backend.api.zotero_export_sharing_endpoints.get_db', return_value=mock_db), \
             patch('backend.api.zotero_export_sharing_endpoints.ZoteroExportSharingService') as mock_service_class:
            
            mock_service = mock_service_class.return_value
            mock_service.share_reference_with_user = AsyncMock(
                side_effect=ValueError("Reference not found")
            )
            
            # Execute
            response = client.post(
                "/api/zotero/export-sharing/references/share",
                json=request_data,
                headers=auth_headers
            )
            
            # Verify
            assert response.status_code == 400
            assert "Reference not found" in response.json()["detail"]

    def test_create_research_project_success(self, mock_user, mock_db, auth_headers):
        """Test successful research project creation"""
        # Setup
        request_data = {
            "project_name": "My Research Project",
            "description": "A test project",
            "reference_ids": ["ref1", "ref2"],
            "collaborator_ids": ["user456"]
        }
        
        expected_response = {
            "collection_id": "collection123",
            "name": "My Research Project",
            "description": "A test project",
            "owner_id": "user123",
            "reference_count": 2,
            "collaborator_count": 1,
            "created_at": "2024-01-15T10:00:00Z"
        }
        
        with patch('backend.api.zotero_export_sharing_endpoints.get_current_user', return_value=mock_user), \
             patch('backend.api.zotero_export_sharing_endpoints.get_db', return_value=mock_db), \
             patch('backend.api.zotero_export_sharing_endpoints.ZoteroExportSharingService') as mock_service_class:
            
            mock_service = mock_service_class.return_value
            mock_service.create_research_project_collection = AsyncMock(return_value=expected_response)
            
            # Execute
            response = client.post(
                "/api/zotero/export-sharing/collections/research-project",
                json=request_data,
                headers=auth_headers
            )
            
            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["collection_id"] == "collection123"
            assert data["reference_count"] == 2
            mock_service.create_research_project_collection.assert_called_once()

    def test_get_shared_references_success(self, mock_user, mock_db, auth_headers):
        """Test getting shared references"""
        # Setup
        expected_response = {
            "shared_by_me": [
                {
                    "share_id": "share1",
                    "reference": {
                        "id": "ref1",
                        "title": "Paper 1",
                        "authors": [{"firstName": "John", "lastName": "Doe"}],
                        "year": 2023
                    },
                    "shared_with": "user456",
                    "permission_level": "read",
                    "shared_at": "2024-01-15T10:00:00Z"
                }
            ],
            "shared_with_me": [
                {
                    "share_id": "share2",
                    "reference": {
                        "id": "ref2",
                        "title": "Paper 2",
                        "authors": [{"firstName": "Jane", "lastName": "Smith"}],
                        "year": 2022
                    },
                    "shared_by": "user789",
                    "permission_level": "edit",
                    "shared_at": "2024-01-14T10:00:00Z"
                }
            ]
        }
        
        with patch('backend.api.zotero_export_sharing_endpoints.get_current_user', return_value=mock_user), \
             patch('backend.api.zotero_export_sharing_endpoints.get_db', return_value=mock_db), \
             patch('backend.api.zotero_export_sharing_endpoints.ZoteroExportSharingService') as mock_service_class:
            
            mock_service = mock_service_class.return_value
            mock_service.get_shared_references = AsyncMock(return_value=expected_response)
            
            # Execute
            response = client.get(
                "/api/zotero/export-sharing/references/shared",
                headers=auth_headers
            )
            
            # Verify
            assert response.status_code == 200
            data = response.json()
            assert len(data["shared_by_me"]) == 1
            assert len(data["shared_with_me"]) == 1
            mock_service.get_shared_references.assert_called_once()

    def test_get_research_project_collections_success(self, mock_user, mock_db, auth_headers):
        """Test getting research project collections"""
        # Setup
        expected_collections = [
            {
                "collection_id": "collection123",
                "name": "My Project",
                "description": "Test project",
                "owner_id": "user123",
                "is_owner": True,
                "reference_count": 5,
                "collaborator_count": 2,
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z"
            }
        ]
        
        with patch('backend.api.zotero_export_sharing_endpoints.get_current_user', return_value=mock_user), \
             patch('backend.api.zotero_export_sharing_endpoints.get_db', return_value=mock_db), \
             patch('backend.api.zotero_export_sharing_endpoints.ZoteroExportSharingService') as mock_service_class:
            
            mock_service = mock_service_class.return_value
            mock_service.get_research_project_collections = AsyncMock(return_value=expected_collections)
            
            # Execute
            response = client.get(
                "/api/zotero/export-sharing/collections/research-projects",
                headers=auth_headers
            )
            
            # Verify
            assert response.status_code == 200
            data = response.json()
            assert len(data["collections"]) == 1
            assert data["collections"][0]["name"] == "My Project"
            mock_service.get_research_project_collections.assert_called_once()

    def test_revoke_reference_share_success(self, mock_user, mock_db, auth_headers):
        """Test revoking reference share"""
        # Setup
        share_id = "share123"
        
        mock_share = Mock()
        mock_share.id = share_id
        mock_share.owner_user_id = mock_user.id
        mock_share.is_active = True
        
        with patch('backend.api.zotero_export_sharing_endpoints.get_current_user', return_value=mock_user), \
             patch('backend.api.zotero_export_sharing_endpoints.get_db', return_value=mock_db):
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_share
            mock_db.commit = Mock()
            
            # Execute
            response = client.delete(
                f"/api/zotero/export-sharing/references/share/{share_id}",
                headers=auth_headers
            )
            
            # Verify
            assert response.status_code == 200
            assert "revoked successfully" in response.json()["message"]
            assert mock_share.is_active == False
            mock_db.commit.assert_called_once()

    def test_revoke_reference_share_not_found(self, mock_user, mock_db, auth_headers):
        """Test revoking non-existent share"""
        # Setup
        share_id = "nonexistent"
        
        with patch('backend.api.zotero_export_sharing_endpoints.get_current_user', return_value=mock_user), \
             patch('backend.api.zotero_export_sharing_endpoints.get_db', return_value=mock_db):
            
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            # Execute
            response = client.delete(
                f"/api/zotero/export-sharing/references/share/{share_id}",
                headers=auth_headers
            )
            
            # Verify
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_add_references_to_collection_success(self, mock_user, mock_db, auth_headers):
        """Test adding references to collection"""
        # Setup
        collection_id = "collection123"
        reference_ids = ["ref1", "ref2", "ref3"]
        
        mock_collection = Mock()
        mock_collection.id = collection_id
        mock_collection.owner_user_id = mock_user.id
        
        with patch('backend.api.zotero_export_sharing_endpoints.get_current_user', return_value=mock_user), \
             patch('backend.api.zotero_export_sharing_endpoints.get_db', return_value=mock_db):
            
            # Mock collection exists
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_collection,  # Collection exists
                None, None, None  # No existing references
            ]
            mock_db.add = Mock()
            mock_db.commit = Mock()
            
            # Execute
            response = client.put(
                f"/api/zotero/export-sharing/collections/{collection_id}/references",
                json=reference_ids,
                headers=auth_headers
            )
            
            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["added_count"] == 3
            assert mock_db.add.call_count == 3
            mock_db.commit.assert_called_once()

    def test_add_references_to_collection_not_found(self, mock_user, mock_db, auth_headers):
        """Test adding references to non-existent collection"""
        # Setup
        collection_id = "nonexistent"
        reference_ids = ["ref1"]
        
        with patch('backend.api.zotero_export_sharing_endpoints.get_current_user', return_value=mock_user), \
             patch('backend.api.zotero_export_sharing_endpoints.get_db', return_value=mock_db):
            
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            # Execute
            response = client.put(
                f"/api/zotero/export-sharing/collections/{collection_id}/references",
                json=reference_ids,
                headers=auth_headers
            )
            
            # Verify
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_get_conversation_export_success(self, mock_user, mock_db, auth_headers):
        """Test getting conversation export"""
        # Setup
        export_id = "export123"
        
        mock_export = Mock()
        mock_export.id = export_id
        mock_export.user_id = mock_user.id
        mock_export.conversation_id = "conv123"
        mock_export.export_format = "json"
        mock_export.citation_style = "apa"
        mock_export.export_data = {"test": "data"}
        mock_export.created_at = Mock()
        mock_export.created_at.isoformat.return_value = "2024-01-15T10:00:00Z"
        mock_export.download_count = 0
        mock_export.last_downloaded = None
        
        with patch('backend.api.zotero_export_sharing_endpoints.get_current_user', return_value=mock_user), \
             patch('backend.api.zotero_export_sharing_endpoints.get_db', return_value=mock_db), \
             patch('backend.api.zotero_export_sharing_endpoints.func'):
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_export
            mock_db.commit = Mock()
            
            # Execute
            response = client.get(
                f"/api/zotero/export-sharing/exports/{export_id}",
                headers=auth_headers
            )
            
            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["export_id"] == export_id
            assert data["conversation_id"] == "conv123"
            assert mock_export.download_count == 1
            mock_db.commit.assert_called_once()

    def test_get_conversation_export_not_found(self, mock_user, mock_db, auth_headers):
        """Test getting non-existent export"""
        # Setup
        export_id = "nonexistent"
        
        with patch('backend.api.zotero_export_sharing_endpoints.get_current_user', return_value=mock_user), \
             patch('backend.api.zotero_export_sharing_endpoints.get_db', return_value=mock_db):
            
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            # Execute
            response = client.get(
                f"/api/zotero/export-sharing/exports/{export_id}",
                headers=auth_headers
            )
            
            # Verify
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__])