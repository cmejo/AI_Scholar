"""
Integration tests for Zotero Reference API Endpoints

Tests the REST API endpoints for reference management including
CRUD operations, validation, and error handling.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from api.zotero_reference_endpoints import router
from models.zotero_schemas import ZoteroItemCreate, ZoteroCreator, ZoteroItemResponse
from services.zotero.zotero_reference_service import ZoteroReferenceService


class TestZoteroReferenceEndpoints:
    """Test suite for Zotero Reference API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client for API endpoints"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    @pytest.fixture
    def mock_current_user(self):
        """Mock current user"""
        return {"id": "user-123", "email": "test@example.com"}
    
    @pytest.fixture
    def mock_reference_service(self):
        """Mock reference service"""
        return Mock(spec=ZoteroReferenceService)
    
    @pytest.fixture
    def sample_reference_data(self):
        """Sample reference creation data"""
        return {
            "item_type": "article",
            "title": "Test Article",
            "creators": [{
                "creator_type": "author",
                "first_name": "John",
                "last_name": "Doe"
            }],
            "publication_title": "Test Journal",
            "publication_year": 2023,
            "doi": "10.1000/test.doi",
            "abstract_note": "Test abstract",
            "tags": ["test", "research"],
            "collection_ids": []
        }
    
    @pytest.fixture
    def sample_reference_response(self):
        """Sample reference response"""
        return {
            "id": "ref-123",
            "library_id": "lib-123",
            "zotero_item_key": "item-key-123",
            "parent_item_id": None,
            "item_type": "article",
            "item_version": 1,
            "title": "Test Article",
            "creators": [{
                "creator_type": "author",
                "first_name": "John",
                "last_name": "Doe",
                "name": None
            }],
            "publication_title": "Test Journal",
            "publication_year": 2023,
            "publisher": None,
            "doi": "10.1000/test.doi",
            "isbn": None,
            "issn": None,
            "url": None,
            "abstract_note": "Test abstract",
            "date_added": "2024-01-15T10:00:00Z",
            "date_modified": "2024-01-15T10:00:00Z",
            "extra_fields": {},
            "tags": ["test", "research"],
            "is_deleted": False,
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        }
    
    # Create Reference Tests
    
    def test_create_reference_success(
        self, client, mock_current_user, mock_reference_service, 
        sample_reference_data, sample_reference_response
    ):
        """Test successful reference creation"""
        # Mock the service response
        mock_reference_service.create_reference = AsyncMock(
            return_value=ZoteroItemResponse(**sample_reference_response)
        )
        
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            with patch('api.zotero_reference_endpoints.get_reference_service', return_value=mock_reference_service):
                response = client.post(
                    "/api/zotero/references/?library_id=lib-123",
                    json=sample_reference_data
                )
                
                assert response.status_code == 201
                data = response.json()
                assert data["id"] == "ref-123"
                assert data["title"] == "Test Article"
                assert data["item_type"] == "article"
                
                # Verify service was called correctly
                mock_reference_service.create_reference.assert_called_once()
                call_args = mock_reference_service.create_reference.call_args
                assert call_args[1]["user_id"] == "user-123"
                assert call_args[1]["library_id"] == "lib-123"
    
    def test_create_reference_validation_error(
        self, client, mock_current_user, mock_reference_service, sample_reference_data
    ):
        """Test reference creation with validation error"""
        # Mock service to raise validation error
        mock_reference_service.create_reference = AsyncMock(
            side_effect=ValueError("Invalid DOI format")
        )
        
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            with patch('api.zotero_reference_endpoints.get_reference_service', return_value=mock_reference_service):
                response = client.post(
                    "/api/zotero/references/?library_id=lib-123",
                    json=sample_reference_data
                )
                
                assert response.status_code == 400
                assert "Invalid DOI format" in response.json()["detail"]
    
    def test_create_reference_permission_error(
        self, client, mock_current_user, mock_reference_service, sample_reference_data
    ):
        """Test reference creation with permission error"""
        # Mock service to raise permission error
        mock_reference_service.create_reference = AsyncMock(
            side_effect=PermissionError("Access denied to library")
        )
        
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            with patch('api.zotero_reference_endpoints.get_reference_service', return_value=mock_reference_service):
                response = client.post(
                    "/api/zotero/references/?library_id=lib-123",
                    json=sample_reference_data
                )
                
                assert response.status_code == 403
                assert "Access denied to library" in response.json()["detail"]
    
    def test_create_reference_missing_library_id(self, client, mock_current_user, sample_reference_data):
        """Test reference creation without library_id parameter"""
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            response = client.post(
                "/api/zotero/references/",
                json=sample_reference_data
            )
            
            assert response.status_code == 422  # Validation error
    
    # Get Reference Tests
    
    def test_get_reference_success(
        self, client, mock_current_user, mock_reference_service, sample_reference_response
    ):
        """Test successful reference retrieval"""
        # Mock service responses
        mock_reference_service.get_reference = AsyncMock(
            return_value=ZoteroItemResponse(**sample_reference_response)
        )
        mock_reference_service._get_reference_with_access_check = AsyncMock(
            return_value=Mock(id="ref-123")
        )
        
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            with patch('api.zotero_reference_endpoints.get_reference_service', return_value=mock_reference_service):
                response = client.get("/api/zotero/references/ref-123")
                
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == "ref-123"
                assert data["title"] == "Test Article"
    
    def test_get_reference_not_found(
        self, client, mock_current_user, mock_reference_service
    ):
        """Test reference retrieval when not found"""
        # Mock service to return None
        mock_reference_service.get_reference = AsyncMock(return_value=None)
        
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            with patch('api.zotero_reference_endpoints.get_reference_service', return_value=mock_reference_service):
                response = client.get("/api/zotero/references/nonexistent")
                
                assert response.status_code == 404
                assert "Reference not found" in response.json()["detail"]
    
    def test_get_reference_access_denied(
        self, client, mock_current_user, mock_reference_service, sample_reference_response
    ):
        """Test reference retrieval with access denied"""
        # Mock service responses
        mock_reference_service.get_reference = AsyncMock(
            return_value=ZoteroItemResponse(**sample_reference_response)
        )
        mock_reference_service._get_reference_with_access_check = AsyncMock(
            return_value=None  # No access
        )
        
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            with patch('api.zotero_reference_endpoints.get_reference_service', return_value=mock_reference_service):
                response = client.get("/api/zotero/references/ref-123")
                
                assert response.status_code == 403
                assert "Access denied" in response.json()["detail"]
    
    # Update Reference Tests
    
    def test_update_reference_success(
        self, client, mock_current_user, mock_reference_service, sample_reference_response
    ):
        """Test successful reference update"""
        update_data = {
            "title": "Updated Title",
            "publication_year": 2024
        }
        
        # Mock updated response
        updated_response = sample_reference_response.copy()
        updated_response["title"] = "Updated Title"
        updated_response["publication_year"] = 2024
        
        mock_reference_service.update_reference = AsyncMock(
            return_value=ZoteroItemResponse(**updated_response)
        )
        
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            with patch('api.zotero_reference_endpoints.get_reference_service', return_value=mock_reference_service):
                response = client.put(
                    "/api/zotero/references/ref-123",
                    json=update_data
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["title"] == "Updated Title"
                assert data["publication_year"] == 2024
    
    def test_update_reference_not_found(
        self, client, mock_current_user, mock_reference_service
    ):
        """Test reference update when not found"""
        update_data = {"title": "Updated Title"}
        
        mock_reference_service.update_reference = AsyncMock(return_value=None)
        
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            with patch('api.zotero_reference_endpoints.get_reference_service', return_value=mock_reference_service):
                response = client.put(
                    "/api/zotero/references/nonexistent",
                    json=update_data
                )
                
                assert response.status_code == 404
                assert "Reference not found" in response.json()["detail"]
    
    # Delete Reference Tests
    
    def test_delete_reference_success(
        self, client, mock_current_user, mock_reference_service
    ):
        """Test successful reference deletion"""
        mock_reference_service.delete_reference = AsyncMock(return_value=True)
        
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            with patch('api.zotero_reference_endpoints.get_reference_service', return_value=mock_reference_service):
                response = client.delete("/api/zotero/references/ref-123")
                
                assert response.status_code == 204
    
    def test_delete_reference_not_found(
        self, client, mock_current_user, mock_reference_service
    ):
        """Test reference deletion when not found"""
        mock_reference_service.delete_reference = AsyncMock(return_value=False)
        
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            with patch('api.zotero_reference_endpoints.get_reference_service', return_value=mock_reference_service):
                response = client.delete("/api/zotero/references/nonexistent")
                
                assert response.status_code == 404
                assert "Reference not found" in response.json()["detail"]
    
    # Library References Tests
    
    def test_get_library_references_success(
        self, client, mock_current_user, mock_reference_service, sample_reference_response
    ):
        """Test successful library references retrieval"""
        references = [ZoteroItemResponse(**sample_reference_response)]
        total_count = 1
        
        mock_reference_service.get_references_by_library = AsyncMock(
            return_value=(references, total_count)
        )
        
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            with patch('api.zotero_reference_endpoints.get_reference_service', return_value=mock_reference_service):
                response = client.get("/api/zotero/references/library/lib-123")
                
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["id"] == "ref-123"
                
                # Check pagination headers
                assert response.headers["X-Total-Count"] == "1"
                assert response.headers["X-Limit"] == "50"
                assert response.headers["X-Offset"] == "0"
    
    def test_get_library_references_with_pagination(
        self, client, mock_current_user, mock_reference_service, sample_reference_response
    ):
        """Test library references retrieval with pagination parameters"""
        references = [ZoteroItemResponse(**sample_reference_response)]
        total_count = 100
        
        mock_reference_service.get_references_by_library = AsyncMock(
            return_value=(references, total_count)
        )
        
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            with patch('api.zotero_reference_endpoints.get_reference_service', return_value=mock_reference_service):
                response = client.get(
                    "/api/zotero/references/library/lib-123?limit=10&offset=20&sort_by=title&sort_order=asc"
                )
                
                assert response.status_code == 200
                
                # Verify service was called with correct parameters
                call_args = mock_reference_service.get_references_by_library.call_args
                assert call_args[1]["limit"] == 10
                assert call_args[1]["offset"] == 20
                assert call_args[1]["sort_by"] == "title"
                assert call_args[1]["sort_order"] == "asc"
    
    # Collection References Tests
    
    def test_get_collection_references_success(
        self, client, mock_current_user, mock_reference_service, sample_reference_response
    ):
        """Test successful collection references retrieval"""
        references = [ZoteroItemResponse(**sample_reference_response)]
        total_count = 1
        
        mock_reference_service.get_references_by_collection = AsyncMock(
            return_value=(references, total_count)
        )
        
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            with patch('api.zotero_reference_endpoints.get_reference_service', return_value=mock_reference_service):
                response = client.get("/api/zotero/references/collection/coll-123")
                
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["id"] == "ref-123"
    
    # Data Integrity Tests
    
    def test_check_data_integrity_success(
        self, client, mock_current_user, mock_reference_service
    ):
        """Test successful data integrity check"""
        integrity_results = {
            "total_references": 100,
            "orphaned_references": 2,
            "missing_required_fields": 1,
            "duplicate_dois": 0,
            "invalid_years": 1,
            "issues": ["Found 2 orphaned references", "Reference ref-123: missing item_type"]
        }
        
        mock_reference_service.check_data_integrity = AsyncMock(
            return_value=integrity_results
        )
        mock_reference_service._validate_library_access = AsyncMock()
        
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            with patch('api.zotero_reference_endpoints.get_reference_service', return_value=mock_reference_service):
                response = client.post("/api/zotero/references/integrity/check")
                
                assert response.status_code == 200
                data = response.json()
                assert data["total_references"] == 100
                assert data["orphaned_references"] == 2
                assert len(data["issues"]) == 2
    
    def test_repair_data_integrity_success(
        self, client, mock_current_user, mock_reference_service
    ):
        """Test successful data integrity repair"""
        repair_results = {
            "repairs_attempted": 2,
            "repairs_successful": 2,
            "repairs_failed": 0,
            "actions": [
                "Removed 2 orphaned item-collection relationships",
                "Set default item_type for 1 items"
            ]
        }
        
        mock_reference_service.repair_data_integrity = AsyncMock(
            return_value=repair_results
        )
        mock_reference_service._validate_library_access = AsyncMock()
        
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            with patch('api.zotero_reference_endpoints.get_reference_service', return_value=mock_reference_service):
                response = client.post("/api/zotero/references/integrity/repair")
                
                assert response.status_code == 200
                data = response.json()
                assert data["repairs_attempted"] == 2
                assert data["repairs_successful"] == 2
                assert len(data["actions"]) == 2
    
    # Validation Tests
    
    def test_validate_reference_success(
        self, client, mock_current_user, mock_reference_service
    ):
        """Test successful reference validation"""
        mock_reference = Mock(
            id="ref-123",
            item_type="article",
            doi="10.1000/test.doi",
            isbn=None,
            issn=None,
            url=None,
            publication_year=2023,
            title="Test Article",
            creators=[{"creator_type": "author", "first_name": "John", "last_name": "Doe"}]
        )
        
        mock_reference_service._get_reference_with_access_check = AsyncMock(
            return_value=mock_reference
        )
        
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            with patch('api.zotero_reference_endpoints.get_reference_service', return_value=mock_reference_service):
                response = client.get("/api/zotero/references/ref-123/validate")
                
                assert response.status_code == 200
                data = response.json()
                assert data["reference_id"] == "ref-123"
                assert data["is_valid"] is True
                assert len(data["errors"]) == 0
    
    def test_validate_reference_with_errors(
        self, client, mock_current_user, mock_reference_service
    ):
        """Test reference validation with errors"""
        mock_reference = Mock(
            id="ref-123",
            item_type="",  # Missing item type
            doi="invalid-doi",  # Invalid DOI
            isbn=None,
            issn=None,
            url=None,
            publication_year=999,  # Invalid year
            title="Test Article",
            creators=[]
        )
        
        mock_reference_service._get_reference_with_access_check = AsyncMock(
            return_value=mock_reference
        )
        mock_reference_service._is_valid_doi = Mock(return_value=False)
        
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            with patch('api.zotero_reference_endpoints.get_reference_service', return_value=mock_reference_service):
                response = client.get("/api/zotero/references/ref-123/validate")
                
                assert response.status_code == 200
                data = response.json()
                assert data["reference_id"] == "ref-123"
                assert data["is_valid"] is False
                assert len(data["errors"]) > 0
                assert "Missing item_type" in data["errors"]
    
    # Health Check Test
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/zotero/references/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "zotero_reference_management"
    
    # Error Handling Tests
    
    def test_internal_server_error_handling(
        self, client, mock_current_user, mock_reference_service, sample_reference_data
    ):
        """Test internal server error handling"""
        # Mock service to raise unexpected error
        mock_reference_service.create_reference = AsyncMock(
            side_effect=Exception("Database connection failed")
        )
        
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            with patch('api.zotero_reference_endpoints.get_reference_service', return_value=mock_reference_service):
                response = client.post(
                    "/api/zotero/references/?library_id=lib-123",
                    json=sample_reference_data
                )
                
                assert response.status_code == 500
                assert "Failed to create reference" in response.json()["detail"]
    
    def test_invalid_query_parameters(self, client, mock_current_user):
        """Test invalid query parameters"""
        with patch('api.zotero_reference_endpoints.get_current_user', return_value=mock_current_user):
            # Test invalid limit
            response = client.get("/api/zotero/references/library/lib-123?limit=0")
            assert response.status_code == 422
            
            # Test invalid offset
            response = client.get("/api/zotero/references/library/lib-123?offset=-1")
            assert response.status_code == 422
            
            # Test invalid sort order
            response = client.get("/api/zotero/references/library/lib-123?sort_order=invalid")
            assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__])