"""
Tests for Zotero Attachment API Endpoints

This module tests the REST API endpoints for PDF import, storage, and management.

Requirements tested:
- 7.1: PDF attachment detection and import
- 7.2: Secure file storage and access controls
- 10.3: Proper access controls and permissions
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from backend.api.zotero_attachment_endpoints import router
from backend.models.zotero_models import ZoteroAttachment
from backend.models.schemas import User


@pytest.fixture
def mock_current_user():
    """Mock current user"""
    return User(
        id="user-123",
        email="test@example.com",
        username="testuser"
    )


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return Mock()


@pytest.fixture
def mock_attachment_service():
    """Mock attachment service"""
    service = Mock()
    service.import_attachments_for_item = AsyncMock()
    service.get_attachments_for_item = AsyncMock()
    service.get_attachment_by_id = AsyncMock()
    service.get_attachment_file_path = AsyncMock()
    service.delete_attachment = AsyncMock()
    service.update_attachment_metadata = AsyncMock()
    service.get_storage_stats = AsyncMock()
    return service


@pytest.fixture
def mock_auth_service():
    """Mock auth service"""
    service = Mock()
    service.get_active_connection = AsyncMock()
    service.get_user_preferences = AsyncMock()
    return service


@pytest.fixture
def sample_attachment():
    """Sample attachment for testing"""
    return ZoteroAttachment(
        id="att-123",
        zotero_attachment_key="ABCD1234",
        title="Sample PDF",
        filename="sample.pdf",
        content_type="application/pdf",
        attachment_type="imported_file",
        file_size=1024000,
        sync_status="synced",
        file_path="/path/to/file.pdf"
    )


class TestZoteroAttachmentEndpoints:
    """Test cases for Zotero attachment API endpoints"""
    
    @pytest.mark.asyncio
    async def test_import_attachments_success(self, mock_current_user, mock_db_session):
        """Test successful attachment import"""
        with patch('backend.api.zotero_attachment_endpoints.ZoteroAttachmentService') as mock_service_class, \
             patch('backend.api.zotero_attachment_endpoints.ZoteroAuthService') as mock_auth_class, \
             patch('backend.api.zotero_attachment_endpoints.ZoteroClient') as mock_client_class, \
             patch('backend.api.zotero_attachment_endpoints.get_current_user', return_value=mock_current_user), \
             patch('backend.api.zotero_attachment_endpoints.get_db', return_value=mock_db_session):
            
            # Mock services
            mock_service = Mock()
            mock_service.import_attachments_for_item = AsyncMock(return_value=[
                {
                    'id': 'att-123',
                    'zotero_key': 'ABCD1234',
                    'title': 'Sample PDF',
                    'filename': 'sample.pdf',
                    'content_type': 'application/pdf',
                    'attachment_type': 'imported_file',
                    'file_size': 1024000,
                    'sync_status': 'synced'
                }
            ])
            mock_service_class.return_value = mock_service
            
            mock_auth_service = Mock()
            mock_connection = Mock()
            mock_connection.access_token = "test-token"
            mock_connection.zotero_user_id = "12345"
            mock_auth_service.get_active_connection = AsyncMock(return_value=mock_connection)
            mock_auth_service.get_user_preferences = AsyncMock(return_value={})
            mock_auth_class.return_value = mock_auth_service
            
            # Create test client
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            # Make request
            response = client.post(
                "/api/zotero/attachments/import",
                json={"item_id": "item-123", "force_refresh": False}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["imported_count"] == 1
            assert len(data["attachments"]) == 1
            assert data["attachments"][0]["zotero_key"] == "ABCD1234"
    
    @pytest.mark.asyncio
    async def test_import_attachments_no_connection(self, mock_current_user, mock_db_session):
        """Test attachment import when no Zotero connection exists"""
        with patch('backend.api.zotero_attachment_endpoints.ZoteroAttachmentService') as mock_service_class, \
             patch('backend.api.zotero_attachment_endpoints.ZoteroAuthService') as mock_auth_class, \
             patch('backend.api.zotero_attachment_endpoints.get_current_user', return_value=mock_current_user), \
             patch('backend.api.zotero_attachment_endpoints.get_db', return_value=mock_db_session):
            
            # Mock auth service returning no connection
            mock_auth_service = Mock()
            mock_auth_service.get_active_connection = AsyncMock(return_value=None)
            mock_auth_class.return_value = mock_auth_service
            
            # Create test client
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            # Make request
            response = client.post(
                "/api/zotero/attachments/import",
                json={"item_id": "item-123"}
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "No active Zotero connection found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_item_attachments_success(self, mock_current_user, mock_db_session, sample_attachment):
        """Test successful retrieval of item attachments"""
        with patch('backend.api.zotero_attachment_endpoints.ZoteroAttachmentService') as mock_service_class, \
             patch('backend.api.zotero_attachment_endpoints.get_current_user', return_value=mock_current_user), \
             patch('backend.api.zotero_attachment_endpoints.get_db', return_value=mock_db_session):
            
            # Mock service
            mock_service = Mock()
            mock_service.get_attachments_for_item = AsyncMock(return_value=[sample_attachment])
            mock_service_class.return_value = mock_service
            
            # Create test client
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            # Make request
            response = client.get("/api/zotero/attachments/item/item-123")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == "att-123"
            assert data[0]["zotero_key"] == "ABCD1234"
            assert data[0]["title"] == "Sample PDF"
    
    @pytest.mark.asyncio
    async def test_get_attachment_success(self, mock_current_user, mock_db_session, sample_attachment):
        """Test successful retrieval of single attachment"""
        with patch('backend.api.zotero_attachment_endpoints.ZoteroAttachmentService') as mock_service_class, \
             patch('backend.api.zotero_attachment_endpoints.get_current_user', return_value=mock_current_user), \
             patch('backend.api.zotero_attachment_endpoints.get_db', return_value=mock_db_session):
            
            # Mock service
            mock_service = Mock()
            mock_service.get_attachment_by_id = AsyncMock(return_value=sample_attachment)
            mock_service_class.return_value = mock_service
            
            # Create test client
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            # Make request
            response = client.get("/api/zotero/attachments/att-123")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == "att-123"
            assert data["zotero_key"] == "ABCD1234"
            assert data["title"] == "Sample PDF"
    
    @pytest.mark.asyncio
    async def test_get_attachment_not_found(self, mock_current_user, mock_db_session):
        """Test retrieval of non-existent attachment"""
        with patch('backend.api.zotero_attachment_endpoints.ZoteroAttachmentService') as mock_service_class, \
             patch('backend.api.zotero_attachment_endpoints.get_current_user', return_value=mock_current_user), \
             patch('backend.api.zotero_attachment_endpoints.get_db', return_value=mock_db_session):
            
            # Mock service returning None
            mock_service = Mock()
            mock_service.get_attachment_by_id = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service
            
            # Create test client
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            # Make request
            response = client.get("/api/zotero/attachments/nonexistent")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Attachment not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_download_attachment_success(self, mock_current_user, mock_db_session, sample_attachment):
        """Test successful attachment download"""
        with patch('backend.api.zotero_attachment_endpoints.ZoteroAttachmentService') as mock_service_class, \
             patch('backend.api.zotero_attachment_endpoints.get_current_user', return_value=mock_current_user), \
             patch('backend.api.zotero_attachment_endpoints.get_db', return_value=mock_db_session), \
             patch('backend.api.zotero_attachment_endpoints.FileResponse') as mock_file_response:
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(b"test content")
                temp_file_path = temp_file.name
            
            # Mock service
            mock_service = Mock()
            mock_service.get_attachment_file_path = AsyncMock(return_value=temp_file_path)
            mock_service.get_attachment_by_id = AsyncMock(return_value=sample_attachment)
            mock_service_class.return_value = mock_service
            
            # Mock FileResponse
            mock_file_response.return_value = Mock()
            
            # Create test client
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            # Make request
            response = client.get("/api/zotero/attachments/att-123/download")
            
            # Verify FileResponse was called with correct parameters
            mock_file_response.assert_called_once_with(
                path=temp_file_path,
                filename="sample.pdf",
                media_type="application/pdf"
            )
            
            # Clean up
            Path(temp_file_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_download_attachment_file_not_found(self, mock_current_user, mock_db_session):
        """Test download when attachment file is not found"""
        with patch('backend.api.zotero_attachment_endpoints.ZoteroAttachmentService') as mock_service_class, \
             patch('backend.api.zotero_attachment_endpoints.get_current_user', return_value=mock_current_user), \
             patch('backend.api.zotero_attachment_endpoints.get_db', return_value=mock_db_session):
            
            # Mock service returning None for file path
            mock_service = Mock()
            mock_service.get_attachment_file_path = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service
            
            # Create test client
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            # Make request
            response = client.get("/api/zotero/attachments/att-123/download")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Attachment file not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_extract_attachment_metadata_success(self, mock_current_user, mock_db_session, sample_attachment):
        """Test successful metadata extraction"""
        with patch('backend.api.zotero_attachment_endpoints.ZoteroAttachmentService') as mock_service_class, \
             patch('backend.api.zotero_attachment_endpoints.get_current_user', return_value=mock_current_user), \
             patch('backend.api.zotero_attachment_endpoints.get_db', return_value=mock_db_session):
            
            # Mock service
            mock_service = Mock()
            mock_service.update_attachment_metadata = AsyncMock(return_value=True)
            mock_service.get_attachment_by_id = AsyncMock(return_value=sample_attachment)
            mock_service_class.return_value = mock_service
            
            # Create test client
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            # Make request
            response = client.post("/api/zotero/attachments/att-123/extract-metadata")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == "att-123"
            assert data["zotero_key"] == "ABCD1234"
    
    @pytest.mark.asyncio
    async def test_extract_attachment_metadata_not_found(self, mock_current_user, mock_db_session):
        """Test metadata extraction when attachment is not found"""
        with patch('backend.api.zotero_attachment_endpoints.ZoteroAttachmentService') as mock_service_class, \
             patch('backend.api.zotero_attachment_endpoints.get_current_user', return_value=mock_current_user), \
             patch('backend.api.zotero_attachment_endpoints.get_db', return_value=mock_db_session):
            
            # Mock service returning False
            mock_service = Mock()
            mock_service.update_attachment_metadata = AsyncMock(return_value=False)
            mock_service_class.return_value = mock_service
            
            # Create test client
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            # Make request
            response = client.post("/api/zotero/attachments/att-123/extract-metadata")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Attachment not found or no file available" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_delete_attachment_success(self, mock_current_user, mock_db_session):
        """Test successful attachment deletion"""
        with patch('backend.api.zotero_attachment_endpoints.ZoteroAttachmentService') as mock_service_class, \
             patch('backend.api.zotero_attachment_endpoints.get_current_user', return_value=mock_current_user), \
             patch('backend.api.zotero_attachment_endpoints.get_db', return_value=mock_db_session):
            
            # Mock service
            mock_service = Mock()
            mock_service.delete_attachment = AsyncMock(return_value=True)
            mock_service_class.return_value = mock_service
            
            # Create test client
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            # Make request
            response = client.delete("/api/zotero/attachments/att-123")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "deleted successfully" in data["message"]
    
    @pytest.mark.asyncio
    async def test_delete_attachment_not_found(self, mock_current_user, mock_db_session):
        """Test deletion of non-existent attachment"""
        with patch('backend.api.zotero_attachment_endpoints.ZoteroAttachmentService') as mock_service_class, \
             patch('backend.api.zotero_attachment_endpoints.get_current_user', return_value=mock_current_user), \
             patch('backend.api.zotero_attachment_endpoints.get_db', return_value=mock_db_session):
            
            # Mock service returning False
            mock_service = Mock()
            mock_service.delete_attachment = AsyncMock(return_value=False)
            mock_service_class.return_value = mock_service
            
            # Create test client
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            # Make request
            response = client.delete("/api/zotero/attachments/nonexistent")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Attachment not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_storage_stats_success(self, mock_current_user, mock_db_session):
        """Test successful storage statistics retrieval"""
        with patch('backend.api.zotero_attachment_endpoints.ZoteroAttachmentService') as mock_service_class, \
             patch('backend.api.zotero_attachment_endpoints.get_current_user', return_value=mock_current_user), \
             patch('backend.api.zotero_attachment_endpoints.get_db', return_value=mock_db_session):
            
            # Mock service
            mock_service = Mock()
            mock_service.get_storage_stats = AsyncMock(return_value={
                'total_attachments': 10,
                'total_size_bytes': 10485760,
                'total_size_mb': 10.0,
                'synced_attachments': 8,
                'by_content_type': {'application/pdf': 8, 'application/msword': 2},
                'by_sync_status': {'synced': 8, 'pending': 1, 'error': 1}
            })
            mock_service_class.return_value = mock_service
            
            # Create test client
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            # Make request
            response = client.get("/api/zotero/attachments/stats/storage")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["total_attachments"] == 10
            assert data["total_size_mb"] == 10.0
            assert data["synced_attachments"] == 8
            assert data["by_content_type"]["application/pdf"] == 8
    
    @pytest.mark.asyncio
    async def test_import_attachments_invalid_request(self, mock_current_user, mock_db_session):
        """Test attachment import with invalid request data"""
        with patch('backend.api.zotero_attachment_endpoints.get_current_user', return_value=mock_current_user), \
             patch('backend.api.zotero_attachment_endpoints.get_db', return_value=mock_db_session):
            
            # Create test client
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            # Make request with missing required field
            response = client.post(
                "/api/zotero/attachments/import",
                json={"force_refresh": True}  # Missing item_id
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_service_error_handling(self, mock_current_user, mock_db_session):
        """Test error handling when service raises exception"""
        with patch('backend.api.zotero_attachment_endpoints.ZoteroAttachmentService') as mock_service_class, \
             patch('backend.api.zotero_attachment_endpoints.get_current_user', return_value=mock_current_user), \
             patch('backend.api.zotero_attachment_endpoints.get_db', return_value=mock_db_session):
            
            # Mock service raising exception
            mock_service = Mock()
            mock_service.get_attachments_for_item = AsyncMock(side_effect=Exception("Database error"))
            mock_service_class.return_value = mock_service
            
            # Create test client
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            
            # Make request
            response = client.get("/api/zotero/attachments/item/item-123")
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to get attachments" in response.json()["detail"]