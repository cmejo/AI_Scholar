"""
Tests for Zotero AI Analysis API endpoints
"""
import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import HTTPException

from api.zotero_ai_analysis_endpoints import router
from models.schemas import User


class TestZoteroAIAnalysisEndpoints:
    """Test cases for Zotero AI Analysis API endpoints"""
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user"""
        return User(
            id="user_123",
            email="test@example.com",
            username="testuser"
        )
    
    @pytest.fixture
    def mock_analysis_result(self):
        """Create mock analysis result"""
        return {
            "item_id": "item_123",
            "analysis_timestamp": "2023-01-01T00:00:00",
            "analysis_types": ["topics", "keywords", "summary"],
            "results": {
                "topics": {
                    "primary_topics": ["machine learning", "AI"],
                    "research_domain": "Computer Science",
                    "confidence_score": 0.85
                },
                "keywords": {
                    "technical_keywords": ["neural networks", "deep learning"],
                    "general_keywords": ["research", "analysis"],
                    "confidence_score": 0.80
                },
                "summary": {
                    "concise_summary": "This paper explores ML applications",
                    "key_findings": ["Finding 1", "Finding 2"],
                    "confidence_score": 0.90
                }
            }
        }
    
    @pytest.fixture
    def mock_batch_result(self):
        """Create mock batch analysis result"""
        return {
            "batch_id": "batch_123",
            "timestamp": "2023-01-01T00:00:00",
            "total_items": 2,
            "successful": 2,
            "failed": 0,
            "results": {
                "item_1": {
                    "item_id": "item_1",
                    "analysis_timestamp": "2023-01-01T00:00:00",
                    "analysis_types": ["topics"],
                    "results": {"topics": {"primary_topics": ["test"]}}
                },
                "item_2": {
                    "item_id": "item_2",
                    "analysis_timestamp": "2023-01-01T00:00:00",
                    "analysis_types": ["topics"],
                    "results": {"topics": {"primary_topics": ["test"]}}
                }
            },
            "errors": []
        }
    
    @pytest.mark.asyncio
    async def test_analyze_reference_content_success(self, mock_user, mock_analysis_result):
        """Test successful reference analysis"""
        from api.zotero_ai_analysis_endpoints import analyze_reference_content, ai_analysis_service
        
        request_data = {
            "analysis_types": ["topics", "keywords", "summary"]
        }
        
        with patch.object(ai_analysis_service, 'analyze_reference_content', return_value=mock_analysis_result):
            from api.zotero_ai_analysis_endpoints import AnalysisRequest
            request = AnalysisRequest(**request_data)
            
            result = await analyze_reference_content(
                item_id="item_123",
                request=request,
                current_user=mock_user,
                db=Mock()
            )
            
            assert result.item_id == "item_123"
            assert result.analysis_types == ["topics", "keywords", "summary"]
            assert "topics" in result.results
            assert "keywords" in result.results
            assert "summary" in result.results
    
    @pytest.mark.asyncio
    async def test_analyze_reference_content_invalid_types(self, mock_user):
        """Test analysis with invalid analysis types"""
        from api.zotero_ai_analysis_endpoints import analyze_reference_content
        
        request_data = {
            "analysis_types": ["invalid_type", "topics"]
        }
        
        from api.zotero_ai_analysis_endpoints import AnalysisRequest
        request = AnalysisRequest(**request_data)
        
        with pytest.raises(HTTPException) as exc_info:
            await analyze_reference_content(
                item_id="item_123",
                request=request,
                current_user=mock_user,
                db=Mock()
            )
        
        assert exc_info.value.status_code == 400
        assert "Invalid analysis types" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_analyze_reference_content_item_not_found(self, mock_user):
        """Test analysis when item not found"""
        from api.zotero_ai_analysis_endpoints import analyze_reference_content, ai_analysis_service
        
        request_data = {
            "analysis_types": ["topics"]
        }
        
        with patch.object(
            ai_analysis_service, 'analyze_reference_content',
            side_effect=ValueError("Item not found")
        ):
            from api.zotero_ai_analysis_endpoints import AnalysisRequest
            request = AnalysisRequest(**request_data)
            
            with pytest.raises(HTTPException) as exc_info:
                await analyze_reference_content(
                    item_id="item_123",
                    request=request,
                    current_user=mock_user,
                    db=Mock()
                )
            
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_analyze_reference_content_service_error(self, mock_user):
        """Test analysis with service error"""
        from api.zotero_ai_analysis_endpoints import analyze_reference_content, ai_analysis_service
        
        request_data = {
            "analysis_types": ["topics"]
        }
        
        with patch.object(
            ai_analysis_service, 'analyze_reference_content',
            side_effect=Exception("Service error")
        ):
            from api.zotero_ai_analysis_endpoints import AnalysisRequest
            request = AnalysisRequest(**request_data)
            
            with pytest.raises(HTTPException) as exc_info:
                await analyze_reference_content(
                    item_id="item_123",
                    request=request,
                    current_user=mock_user,
                    db=Mock()
                )
            
            assert exc_info.value.status_code == 500
            assert "Analysis failed" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_batch_analyze_references_small_batch(self, mock_user, mock_batch_result):
        """Test batch analysis with small batch (synchronous)"""
        from api.zotero_ai_analysis_endpoints import batch_analyze_references, ai_analysis_service
        
        request_data = {
            "item_ids": ["item_1", "item_2"],
            "analysis_types": ["topics"]
        }
        
        with patch.object(ai_analysis_service, 'batch_analyze_references', return_value=mock_batch_result):
            from api.zotero_ai_analysis_endpoints import BatchAnalysisRequest
            request = BatchAnalysisRequest(**request_data)
            
            result = await batch_analyze_references(
                request=request,
                background_tasks=Mock(),
                current_user=mock_user,
                db=Mock()
            )
            
            assert result.total_items == 2
            assert result.successful == 2
            assert result.failed == 0
            assert len(result.results) == 2
    
    @pytest.mark.asyncio
    async def test_batch_analyze_references_large_batch(self, mock_user):
        """Test batch analysis with large batch (background processing)"""
        from api.zotero_ai_analysis_endpoints import batch_analyze_references
        
        # Create large batch (>10 items)
        item_ids = [f"item_{i}" for i in range(15)]
        request_data = {
            "item_ids": item_ids,
            "analysis_types": ["topics"]
        }
        
        mock_background_tasks = Mock()
        
        from api.zotero_ai_analysis_endpoints import BatchAnalysisRequest
        request = BatchAnalysisRequest(**request_data)
        
        result = await batch_analyze_references(
            request=request,
            background_tasks=mock_background_tasks,
            current_user=mock_user,
            db=Mock()
        )
        
        # Should return immediate response for background processing
        assert result.total_items == 15
        assert result.successful == 0  # Not processed yet
        assert result.failed == 0
        assert len(result.results) == 0
        
        # Verify background task was added
        mock_background_tasks.add_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_analyze_references_invalid_types(self, mock_user):
        """Test batch analysis with invalid analysis types"""
        from api.zotero_ai_analysis_endpoints import batch_analyze_references
        
        request_data = {
            "item_ids": ["item_1"],
            "analysis_types": ["invalid_type"]
        }
        
        from api.zotero_ai_analysis_endpoints import BatchAnalysisRequest
        request = BatchAnalysisRequest(**request_data)
        
        with pytest.raises(HTTPException) as exc_info:
            await batch_analyze_references(
                request=request,
                background_tasks=Mock(),
                current_user=mock_user,
                db=Mock()
            )
        
        assert exc_info.value.status_code == 400
        assert "Invalid analysis types" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_analysis_results_success(self, mock_user, mock_analysis_result):
        """Test retrieving analysis results"""
        from api.zotero_ai_analysis_endpoints import get_analysis_results, ai_analysis_service
        
        with patch.object(ai_analysis_service, 'get_analysis_results', return_value=mock_analysis_result):
            result = await get_analysis_results(
                item_id="item_123",
                current_user=mock_user,
                db=Mock()
            )
            
            assert result.item_id == "item_123"
            assert "topics" in result.results
    
    @pytest.mark.asyncio
    async def test_get_analysis_results_not_found(self, mock_user):
        """Test retrieving analysis results when not found"""
        from api.zotero_ai_analysis_endpoints import get_analysis_results, ai_analysis_service
        
        with patch.object(ai_analysis_service, 'get_analysis_results', return_value=None):
            result = await get_analysis_results(
                item_id="item_123",
                current_user=mock_user,
                db=Mock()
            )
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_analysis_results_service_error(self, mock_user):
        """Test retrieving analysis results with service error"""
        from api.zotero_ai_analysis_endpoints import get_analysis_results, ai_analysis_service
        
        with patch.object(
            ai_analysis_service, 'get_analysis_results',
            side_effect=Exception("Service error")
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_analysis_results(
                    item_id="item_123",
                    current_user=mock_user,
                    db=Mock()
                )
            
            assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_get_supported_analysis_types(self):
        """Test getting supported analysis types"""
        from api.zotero_ai_analysis_endpoints import get_supported_analysis_types
        
        result = await get_supported_analysis_types()
        
        assert "supported_types" in result
        assert "topics" in result["supported_types"]
        assert "keywords" in result["supported_types"]
        assert "summary" in result["supported_types"]
        assert result["default_types"] == ["topics", "keywords", "summary"]
        assert result["max_batch_size"] == 50
    
    @pytest.mark.asyncio
    async def test_delete_analysis_results_success(self, mock_user):
        """Test deleting analysis results"""
        from api.zotero_ai_analysis_endpoints import delete_analysis_results
        
        # Mock database objects
        mock_item = Mock()
        mock_item.item_metadata = {"ai_analysis": {"test": "data"}}
        
        mock_db = Mock()
        mock_db.query.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = mock_item
        
        result = await delete_analysis_results(
            item_id="item_123",
            current_user=mock_user,
            db=mock_db
        )
        
        assert result["message"] == "Analysis results deleted successfully"
        assert "ai_analysis" not in mock_item.item_metadata
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_analysis_results_item_not_found(self, mock_user):
        """Test deleting analysis results when item not found"""
        from api.zotero_ai_analysis_endpoints import delete_analysis_results
        
        mock_db = Mock()
        mock_db.query.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_analysis_results(
                item_id="item_123",
                current_user=mock_user,
                db=mock_db
            )
        
        assert exc_info.value.status_code == 404
        assert "Item not found or access denied" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_delete_analysis_results_no_analysis(self, mock_user):
        """Test deleting analysis results when no analysis exists"""
        from api.zotero_ai_analysis_endpoints import delete_analysis_results
        
        mock_item = Mock()
        mock_item.item_metadata = {}
        
        mock_db = Mock()
        mock_db.query.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = mock_item
        
        result = await delete_analysis_results(
            item_id="item_123",
            current_user=mock_user,
            db=mock_db
        )
        
        assert result["message"] == "No analysis results found to delete"
    
    @pytest.mark.asyncio
    async def test_delete_analysis_results_database_error(self, mock_user):
        """Test deleting analysis results with database error"""
        from api.zotero_ai_analysis_endpoints import delete_analysis_results
        
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_analysis_results(
                item_id="item_123",
                current_user=mock_user,
                db=mock_db
            )
        
        assert exc_info.value.status_code == 500
        mock_db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_analysis_statistics_success(self, mock_user):
        """Test getting analysis statistics"""
        from api.zotero_ai_analysis_endpoints import get_analysis_statistics
        
        # Mock database objects
        mock_library = Mock()
        mock_library.library_name = "Test Library"
        
        mock_analyzed_item = Mock()
        mock_analyzed_item.item_metadata = {
            "ai_analysis": {
                "results": {
                    "topics": {
                        "primary_topics": ["machine learning", "AI"],
                        "research_domain": "Computer Science"
                    }
                }
            }
        }
        
        mock_db = Mock()
        mock_db.query.return_value.join.return_value.filter.return_value.first.return_value = mock_library
        mock_db.query.return_value.filter.return_value.scalar.return_value = 10  # total items
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_analyzed_item]  # analyzed items
        
        result = await get_analysis_statistics(
            library_id="lib_123",
            current_user=mock_user,
            db=mock_db
        )
        
        assert result["library_id"] == "lib_123"
        assert result["library_name"] == "Test Library"
        assert result["total_items"] == 10
        assert result["analyzed_items"] == 1
        assert result["analysis_coverage"] == 10.0
        assert len(result["top_topics"]) > 0
        assert len(result["research_domains"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_analysis_statistics_library_not_found(self, mock_user):
        """Test getting analysis statistics when library not found"""
        from api.zotero_ai_analysis_endpoints import get_analysis_statistics
        
        mock_db = Mock()
        mock_db.query.return_value.join.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await get_analysis_statistics(
                library_id="lib_123",
                current_user=mock_user,
                db=mock_db
            )
        
        assert exc_info.value.status_code == 404
        assert "Library not found or access denied" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_analysis_statistics_database_error(self, mock_user):
        """Test getting analysis statistics with database error"""
        from api.zotero_ai_analysis_endpoints import get_analysis_statistics
        
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_analysis_statistics(
                library_id="lib_123",
                current_user=mock_user,
                db=mock_db
            )
        
        assert exc_info.value.status_code == 500