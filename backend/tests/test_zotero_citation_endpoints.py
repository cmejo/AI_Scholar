"""
Integration tests for Zotero Citation API Endpoints

Tests the FastAPI endpoints for citation generation and bibliography creation.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.zotero_citation_endpoints import router
from services.zotero.zotero_citation_service import CitationStyleError, CitationValidationError
from models.zotero_models import ZoteroItem
from models.zotero_schemas import CitationResponse, BibliographyResponse


class TestZoteroCitationEndpoints:
    """Test cases for Zotero Citation API endpoints"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_current_user(self):
        """Mock current user"""
        return {"user_id": "user-123", "email": "test@example.com"}
    
    @pytest.fixture
    def client(self):
        """Test client with mocked dependencies"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    @pytest.fixture
    def sample_citation_request(self):
        """Sample citation request"""
        return {
            "item_ids": ["item-1", "item-2"],
            "citation_style": "apa",
            "format": "text",
            "locale": "en-US"
        }
    
    @pytest.fixture
    def sample_bibliography_request(self):
        """Sample bibliography request"""
        return {
            "item_ids": ["item-1", "item-2"],
            "citation_style": "apa",
            "format": "text",
            "sort_by": "author"
        }
    
    @pytest.fixture
    def sample_citation_response(self):
        """Sample citation response"""
        return CitationResponse(
            citations=[
                "Doe, J. & Smith, J. (2023). Sample Article Title. Journal of Testing. https://doi.org/10.1000/test.doi.",
                "Johnson, A. (2022). Sample Book Title. Academic Press."
            ],
            style_used="apa",
            format="text",
            processing_time=0.123
        )
    
    @pytest.fixture
    def sample_bibliography_response(self):
        """Sample bibliography response"""
        return BibliographyResponse(
            bibliography="Doe, J. & Smith, J. (2023). Sample Article Title. Journal of Testing.\n\nJohnson, A. (2022). Sample Book Title. Academic Press.",
            item_count=2,
            style_used="apa",
            format="text",
            processing_time=0.156
        )
    
    @patch('api.zotero_citation_endpoints.get_current_user')
    @patch('api.zotero_citation_endpoints.get_db')
    @patch('api.zotero_citation_endpoints.ZoteroCitationService')
    def test_generate_citations_success(
        self,
        mock_citation_service_class,
        mock_get_db,
        mock_get_current_user,
        client,
        mock_db,
        mock_current_user,
        sample_citation_request,
        sample_citation_response
    ):
        """Test successful citation generation"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db
        
        mock_citation_service = Mock()
        mock_citation_service.generate_citations = AsyncMock(return_value=sample_citation_response)
        mock_citation_service_class.return_value = mock_citation_service
        
        # Make request
        response = client.post("/api/zotero/citations/generate", json=sample_citation_request)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["citations"]) == 2
        assert data["style_used"] == "apa"
        assert data["format"] == "text"
        assert data["processing_time"] > 0
        
        # Verify service was called correctly
        mock_citation_service.generate_citations.assert_called_once_with(
            item_ids=sample_citation_request["item_ids"],
            citation_style=sample_citation_request["citation_style"],
            format_type=sample_citation_request["format"],
            locale=sample_citation_request["locale"],
            user_id=mock_current_user["user_id"]
        )
    
    @patch('api.zotero_citation_endpoints.get_current_user')
    @patch('api.zotero_citation_endpoints.get_db')
    @patch('api.zotero_citation_endpoints.ZoteroCitationService')
    def test_generate_citations_validation_error(
        self,
        mock_citation_service_class,
        mock_get_db,
        mock_get_current_user,
        client,
        mock_db,
        mock_current_user,
        sample_citation_request
    ):
        """Test citation generation with validation error"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db
        
        mock_citation_service = Mock()
        mock_citation_service.generate_citations = AsyncMock(
            side_effect=CitationValidationError("Invalid citation style")
        )
        mock_citation_service_class.return_value = mock_citation_service
        
        # Make request
        response = client.post("/api/zotero/citations/generate", json=sample_citation_request)
        
        # Assertions
        assert response.status_code == 400
        assert "Invalid citation style" in response.json()["detail"]
    
    @patch('api.zotero_citation_endpoints.get_current_user')
    @patch('api.zotero_citation_endpoints.get_db')
    @patch('api.zotero_citation_endpoints.ZoteroCitationService')
    def test_generate_citations_style_error(
        self,
        mock_citation_service_class,
        mock_get_db,
        mock_get_current_user,
        client,
        mock_db,
        mock_current_user,
        sample_citation_request
    ):
        """Test citation generation with style error"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db
        
        mock_citation_service = Mock()
        mock_citation_service.generate_citations = AsyncMock(
            side_effect=CitationStyleError("Citation formatting failed")
        )
        mock_citation_service_class.return_value = mock_citation_service
        
        # Make request
        response = client.post("/api/zotero/citations/generate", json=sample_citation_request)
        
        # Assertions
        assert response.status_code == 422
        assert "Citation formatting failed" in response.json()["detail"]
    
    @patch('api.zotero_citation_endpoints.get_current_user')
    @patch('api.zotero_citation_endpoints.get_db')
    @patch('api.zotero_citation_endpoints.ZoteroCitationService')
    def test_generate_bibliography_success(
        self,
        mock_citation_service_class,
        mock_get_db,
        mock_get_current_user,
        client,
        mock_db,
        mock_current_user,
        sample_bibliography_request,
        sample_bibliography_response
    ):
        """Test successful bibliography generation"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db
        
        mock_citation_service = Mock()
        mock_citation_service.generate_bibliography = AsyncMock(return_value=sample_bibliography_response)
        mock_citation_service_class.return_value = mock_citation_service
        
        # Make request
        response = client.post("/api/zotero/citations/bibliography", json=sample_bibliography_request)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["bibliography"]
        assert data["item_count"] == 2
        assert data["style_used"] == "apa"
        assert data["format"] == "text"
        assert data["processing_time"] > 0
        
        # Verify service was called correctly
        mock_citation_service.generate_bibliography.assert_called_once_with(
            item_ids=sample_bibliography_request["item_ids"],
            citation_style=sample_bibliography_request["citation_style"],
            format_type=sample_bibliography_request["format"],
            sort_by=sample_bibliography_request["sort_by"],
            user_id=mock_current_user["user_id"]
        )
    
    @patch('api.zotero_citation_endpoints.get_current_user')
    @patch('api.zotero_citation_endpoints.get_db')
    @patch('api.zotero_citation_endpoints.ZoteroCitationService')
    def test_validate_citation_data_success(
        self,
        mock_citation_service_class,
        mock_get_db,
        mock_get_current_user,
        client,
        mock_db,
        mock_current_user
    ):
        """Test successful citation data validation"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db
        
        mock_item = Mock(spec=ZoteroItem)
        validation_result = {
            "is_valid": True,
            "missing_fields": [],
            "warnings": [],
            "item_type": "article"
        }
        
        mock_citation_service = Mock()
        mock_citation_service._get_items_by_ids = AsyncMock(return_value=[mock_item])
        mock_citation_service.validate_citation_data = AsyncMock(return_value=validation_result)
        mock_citation_service_class.return_value = mock_citation_service
        
        # Make request
        response = client.post("/api/zotero/citations/validate/item-1")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] == True
        assert data["item_type"] == "article"
        assert len(data["missing_fields"]) == 0
    
    @patch('api.zotero_citation_endpoints.get_current_user')
    @patch('api.zotero_citation_endpoints.get_db')
    @patch('api.zotero_citation_endpoints.ZoteroCitationService')
    def test_validate_citation_data_item_not_found(
        self,
        mock_citation_service_class,
        mock_get_db,
        mock_get_current_user,
        client,
        mock_db,
        mock_current_user
    ):
        """Test citation data validation with item not found"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db
        
        mock_citation_service = Mock()
        mock_citation_service._get_items_by_ids = AsyncMock(return_value=[])
        mock_citation_service_class.return_value = mock_citation_service
        
        # Make request
        response = client.post("/api/zotero/citations/validate/item-1")
        
        # Assertions
        assert response.status_code == 404
        assert "Item not found" in response.json()["detail"]
    
    @patch('api.zotero_citation_endpoints.get_current_user')
    @patch('api.zotero_citation_endpoints.get_db')
    @patch('api.zotero_citation_endpoints.ZoteroCitationService')
    def test_get_supported_citation_styles(
        self,
        mock_citation_service_class,
        mock_get_db,
        mock_get_current_user,
        client,
        mock_db,
        mock_current_user
    ):
        """Test getting supported citation styles"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db
        
        styles = {
            "apa": "American Psychological Association 7th edition",
            "mla": "Modern Language Association 9th edition",
            "chicago": "Chicago Manual of Style 17th edition"
        }
        
        mock_citation_service = Mock()
        mock_citation_service.get_supported_styles = AsyncMock(return_value=styles)
        mock_citation_service_class.return_value = mock_citation_service
        
        # Make request
        response = client.get("/api/zotero/citations/styles")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert "apa" in data["styles"]
        assert "mla" in data["styles"]
        assert "chicago" in data["styles"]
    
    @patch('api.zotero_citation_endpoints.get_current_user')
    @patch('api.zotero_citation_endpoints.get_db')
    @patch('api.zotero_citation_endpoints.ZoteroCitationService')
    def test_get_supported_formats(
        self,
        mock_citation_service_class,
        mock_get_db,
        mock_get_current_user,
        client,
        mock_db,
        mock_current_user
    ):
        """Test getting supported output formats"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db
        
        formats = ["text", "html", "rtf"]
        
        mock_citation_service = Mock()
        mock_citation_service.get_supported_formats = AsyncMock(return_value=formats)
        mock_citation_service_class.return_value = mock_citation_service
        
        # Make request
        response = client.get("/api/zotero/citations/formats")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert "text" in data["formats"]
        assert "html" in data["formats"]
        assert "rtf" in data["formats"]
    
    @patch('api.zotero_citation_endpoints.get_current_user')
    @patch('api.zotero_citation_endpoints.get_db')
    @patch('api.zotero_citation_endpoints.ZoteroCitationService')
    def test_batch_validate_citation_data_success(
        self,
        mock_citation_service_class,
        mock_get_db,
        mock_get_current_user,
        client,
        mock_db,
        mock_current_user
    ):
        """Test successful batch citation data validation"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db
        
        mock_items = [Mock(id="item-1"), Mock(id="item-2")]
        validation_results = [
            {"is_valid": True, "missing_fields": [], "warnings": []},
            {"is_valid": False, "missing_fields": ["title"], "warnings": []}
        ]
        
        mock_citation_service = Mock()
        mock_citation_service._get_items_by_ids = AsyncMock(return_value=mock_items)
        mock_citation_service.validate_citation_data = AsyncMock(side_effect=validation_results)
        mock_citation_service_class.return_value = mock_citation_service
        
        # Make request
        response = client.post("/api/zotero/citations/batch-validate", json=["item-1", "item-2"])
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert data["summary"]["total_items"] == 2
        assert data["summary"]["valid_items"] == 1
        assert data["summary"]["invalid_items"] == 1
        assert data["summary"]["validation_rate"] == 0.5
    
    @patch('api.zotero_citation_endpoints.get_current_user')
    @patch('api.zotero_citation_endpoints.get_db')
    def test_batch_validate_too_many_items(
        self,
        mock_get_db,
        mock_get_current_user,
        client,
        mock_db,
        mock_current_user
    ):
        """Test batch validation with too many items"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db
        
        # Create list of 101 items
        item_ids = [f"item-{i}" for i in range(101)]
        
        # Make request
        response = client.post("/api/zotero/citations/batch-validate", json=item_ids)
        
        # Assertions
        assert response.status_code == 400
        assert "Too many items" in response.json()["detail"]
    
    @patch('api.zotero_citation_endpoints.get_current_user')
    @patch('api.zotero_citation_endpoints.get_db')
    @patch('api.zotero_citation_endpoints.ZoteroCitationService')
    def test_preview_citation_success(
        self,
        mock_citation_service_class,
        mock_get_db,
        mock_get_current_user,
        client,
        mock_db,
        mock_current_user
    ):
        """Test successful citation preview"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db
        
        citation_response = CitationResponse(
            citations=["Doe, J. (2023). Sample Title. Journal of Testing."],
            style_used="apa",
            format="text",
            processing_time=0.045
        )
        
        mock_citation_service = Mock()
        mock_citation_service.generate_citations = AsyncMock(return_value=citation_response)
        mock_citation_service_class.return_value = mock_citation_service
        
        # Make request
        response = client.get("/api/zotero/citations/preview/item-1?style=apa&format_type=text")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["item_id"] == "item-1"
        assert data["citation"] == "Doe, J. (2023). Sample Title. Journal of Testing."
        assert data["style"] == "apa"
        assert data["format"] == "text"
        assert data["processing_time"] > 0
    
    @patch('api.zotero_citation_endpoints.get_current_user')
    @patch('api.zotero_citation_endpoints.get_db')
    @patch('api.zotero_citation_endpoints.ZoteroCitationService')
    def test_preview_citation_not_found(
        self,
        mock_citation_service_class,
        mock_get_db,
        mock_get_current_user,
        client,
        mock_db,
        mock_current_user
    ):
        """Test citation preview with item not found"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db
        
        citation_response = CitationResponse(
            citations=[],
            style_used="apa",
            format="text",
            processing_time=0.001
        )
        
        mock_citation_service = Mock()
        mock_citation_service.generate_citations = AsyncMock(return_value=citation_response)
        mock_citation_service_class.return_value = mock_citation_service
        
        # Make request
        response = client.get("/api/zotero/citations/preview/item-1")
        
        # Assertions
        assert response.status_code == 404
        assert "Item not found" in response.json()["detail"]
    
    def test_generate_citations_invalid_request_body(self, client):
        """Test citation generation with invalid request body"""
        # Make request with invalid JSON
        response = client.post("/api/zotero/citations/generate", json={})
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_generate_bibliography_invalid_request_body(self, client):
        """Test bibliography generation with invalid request body"""
        # Make request with invalid JSON
        response = client.post("/api/zotero/citations/bibliography", json={})
        
        # Should return validation error
        assert response.status_code == 422
    
    @patch('api.zotero_citation_endpoints.get_current_user')
    @patch('api.zotero_citation_endpoints.get_db')
    @patch('api.zotero_citation_endpoints.ZoteroCitationService')
    def test_unexpected_error_handling(
        self,
        mock_citation_service_class,
        mock_get_db,
        mock_get_current_user,
        client,
        mock_db,
        mock_current_user,
        sample_citation_request
    ):
        """Test handling of unexpected errors"""
        # Setup mocks
        mock_get_current_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db
        
        mock_citation_service = Mock()
        mock_citation_service.generate_citations = AsyncMock(
            side_effect=Exception("Unexpected database error")
        )
        mock_citation_service_class.return_value = mock_citation_service
        
        # Make request
        response = client.post("/api/zotero/citations/generate", json=sample_citation_request)
        
        # Assertions
        assert response.status_code == 500
        assert "Failed to generate citations" in response.json()["detail"]