"""
Tests for Zotero AI Analysis Service
"""
import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from sqlalchemy.orm import Session

from services.zotero.zotero_ai_analysis_service import ZoteroAIAnalysisService
from models.zotero_models import ZoteroItem, ZoteroLibrary, ZoteroConnection


class TestZoteroAIAnalysisService:
    """Test cases for Zotero AI Analysis Service"""
    
    @pytest.fixture
    def ai_analysis_service(self):
        """Create AI analysis service instance"""
        return ZoteroAIAnalysisService()
    
    @pytest.fixture
    def mock_zotero_item(self):
        """Create mock Zotero item"""
        return ZoteroItem(
            id="item_123",
            library_id="lib_123",
            zotero_item_key="ABCD1234",
            item_type="journalArticle",
            title="Machine Learning in Academic Research",
            creators=[
                {"firstName": "John", "lastName": "Doe", "creatorType": "author"},
                {"firstName": "Jane", "lastName": "Smith", "creatorType": "author"}
            ],
            publication_title="Journal of AI Research",
            publication_year=2023,
            abstract_note="This paper explores the application of machine learning techniques in academic research, focusing on natural language processing and data analysis methods.",
            tags=["machine learning", "NLP", "research"],
            extra_fields={"DOI": "10.1000/test.doi"},
            item_metadata={}
        )
    
    @pytest.fixture
    def mock_llm_response_topics(self):
        """Mock LLM response for topic extraction"""
        return json.dumps({
            "primary_topics": ["machine learning", "natural language processing", "academic research"],
            "secondary_themes": ["data analysis", "research methodology"],
            "research_domain": "Computer Science",
            "methodology": "experimental",
            "confidence_score": 0.85
        })
    
    @pytest.fixture
    def mock_llm_response_keywords(self):
        """Mock LLM response for keyword extraction"""
        return json.dumps({
            "technical_keywords": ["neural networks", "deep learning", "NLP", "algorithms"],
            "general_keywords": ["research", "analysis", "methodology", "data"],
            "author_keywords": ["machine learning", "NLP"],
            "suggested_keywords": ["artificial intelligence", "computational linguistics"],
            "confidence_score": 0.80
        })
    
    @pytest.fixture
    def mock_llm_response_summary(self):
        """Mock LLM response for summary generation"""
        return json.dumps({
            "concise_summary": "This paper presents a comprehensive study of machine learning applications in academic research, with particular focus on NLP techniques.",
            "key_findings": [
                "ML techniques improve research efficiency",
                "NLP methods enable better text analysis",
                "Automated data processing reduces manual effort"
            ],
            "methodology": "Experimental study with comparative analysis",
            "significance": "Demonstrates practical applications of ML in research workflows",
            "limitations": "Limited to English-language texts, requires computational resources",
            "confidence_score": 0.90
        })
    
    @pytest.mark.asyncio
    async def test_analyze_reference_content_success(
        self, ai_analysis_service, mock_zotero_item, mock_llm_response_topics,
        mock_llm_response_keywords, mock_llm_response_summary
    ):
        """Test successful reference content analysis"""
        user_id = "user_123"
        
        # Mock database and LLM calls
        with patch('services.zotero.zotero_ai_analysis_service.get_db') as mock_get_db, \
             patch.object(ai_analysis_service, '_get_user_item', return_value=mock_zotero_item), \
             patch.object(ai_analysis_service, '_call_llm') as mock_call_llm, \
             patch.object(ai_analysis_service, '_store_analysis_results') as mock_store:
            
            # Configure LLM responses
            mock_call_llm.side_effect = [
                mock_llm_response_topics,
                mock_llm_response_keywords,
                mock_llm_response_summary
            ]
            
            result = await ai_analysis_service.analyze_reference_content(
                item_id="item_123",
                user_id=user_id,
                analysis_types=["topics", "keywords", "summary"]
            )
            
            # Verify result structure
            assert result["item_id"] == "item_123"
            assert "analysis_timestamp" in result
            assert result["analysis_types"] == ["topics", "keywords", "summary"]
            assert "results" in result
            
            # Verify topics analysis
            topics = result["results"]["topics"]
            assert "machine learning" in topics["primary_topics"]
            assert topics["research_domain"] == "Computer Science"
            assert topics["confidence_score"] == 0.85
            
            # Verify keywords analysis
            keywords = result["results"]["keywords"]
            assert "neural networks" in keywords["technical_keywords"]
            assert "research" in keywords["general_keywords"]
            assert keywords["confidence_score"] == 0.80
            
            # Verify summary analysis
            summary = result["results"]["summary"]
            assert "machine learning applications" in summary["concise_summary"]
            assert len(summary["key_findings"]) == 3
            assert summary["confidence_score"] == 0.90
            
            # Verify storage was called
            mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_reference_content_item_not_found(self, ai_analysis_service):
        """Test analysis when item is not found"""
        user_id = "user_123"
        
        with patch('services.zotero.zotero_ai_analysis_service.get_db'), \
             patch.object(ai_analysis_service, '_get_user_item', return_value=None):
            
            with pytest.raises(ValueError, match="Item item_123 not found or access denied"):
                await ai_analysis_service.analyze_reference_content(
                    item_id="item_123",
                    user_id=user_id
                )
    
    @pytest.mark.asyncio
    async def test_analyze_reference_content_no_content(self, ai_analysis_service):
        """Test analysis when item has no content"""
        user_id = "user_123"
        
        # Create item with no content
        empty_item = ZoteroItem(
            id="item_123",
            library_id="lib_123",
            zotero_item_key="ABCD1234",
            item_type="journalArticle",
            title="",
            abstract_note="",
            creators=[],
            tags=[],
            item_metadata={}
        )
        
        with patch('services.zotero.zotero_ai_analysis_service.get_db'), \
             patch.object(ai_analysis_service, '_get_user_item', return_value=empty_item), \
             patch.object(ai_analysis_service, '_store_analysis_results'):
            
            result = await ai_analysis_service.analyze_reference_content(
                item_id="item_123",
                user_id=user_id
            )
            
            assert result["results"]["error"] == "No content available for analysis"
    
    @pytest.mark.asyncio
    async def test_batch_analyze_references_success(
        self, ai_analysis_service, mock_zotero_item, mock_llm_response_topics
    ):
        """Test successful batch analysis"""
        user_id = "user_123"
        item_ids = ["item_1", "item_2", "item_3"]
        
        # Mock individual analysis calls
        mock_analysis_result = {
            "item_id": "item_1",
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "analysis_types": ["topics"],
            "results": {"topics": {"primary_topics": ["test"]}}
        }
        
        with patch.object(
            ai_analysis_service, 'analyze_reference_content',
            return_value=mock_analysis_result
        ) as mock_analyze:
            
            result = await ai_analysis_service.batch_analyze_references(
                item_ids=item_ids,
                user_id=user_id,
                analysis_types=["topics"]
            )
            
            assert result["total_items"] == 3
            assert result["successful"] == 3
            assert result["failed"] == 0
            assert len(result["results"]) == 3
            assert len(result["errors"]) == 0
            
            # Verify individual analysis was called for each item
            assert mock_analyze.call_count == 3
    
    @pytest.mark.asyncio
    async def test_batch_analyze_references_partial_failure(self, ai_analysis_service):
        """Test batch analysis with some failures"""
        user_id = "user_123"
        item_ids = ["item_1", "item_2", "item_3"]
        
        # Mock analysis calls with one failure
        def mock_analyze_side_effect(item_id, user_id, analysis_types):
            if item_id == "item_2":
                raise Exception("Analysis failed")
            return {
                "item_id": item_id,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "analysis_types": analysis_types,
                "results": {"topics": {"primary_topics": ["test"]}}
            }
        
        with patch.object(
            ai_analysis_service, 'analyze_reference_content',
            side_effect=mock_analyze_side_effect
        ):
            
            result = await ai_analysis_service.batch_analyze_references(
                item_ids=item_ids,
                user_id=user_id,
                analysis_types=["topics"]
            )
            
            assert result["total_items"] == 3
            assert result["successful"] == 2
            assert result["failed"] == 1
            assert len(result["results"]) == 2
            assert len(result["errors"]) == 1
            assert result["errors"][0]["item_id"] == "item_2"
    
    @pytest.mark.asyncio
    async def test_get_analysis_results_success(self, ai_analysis_service, mock_zotero_item):
        """Test retrieving stored analysis results"""
        user_id = "user_123"
        
        # Add analysis results to item metadata
        analysis_data = {
            "item_id": "item_123",
            "analysis_timestamp": "2023-01-01T00:00:00",
            "results": {"topics": {"primary_topics": ["test"]}}
        }
        mock_zotero_item.item_metadata = {"ai_analysis": analysis_data}
        
        with patch('services.zotero.zotero_ai_analysis_service.get_db'), \
             patch.object(ai_analysis_service, '_get_user_item', return_value=mock_zotero_item):
            
            result = await ai_analysis_service.get_analysis_results(
                item_id="item_123",
                user_id=user_id
            )
            
            assert result == analysis_data
    
    @pytest.mark.asyncio
    async def test_get_analysis_results_not_found(self, ai_analysis_service):
        """Test retrieving analysis results when item not found"""
        user_id = "user_123"
        
        with patch('services.zotero.zotero_ai_analysis_service.get_db'), \
             patch.object(ai_analysis_service, '_get_user_item', return_value=None):
            
            result = await ai_analysis_service.get_analysis_results(
                item_id="item_123",
                user_id=user_id
            )
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_analysis_results_no_analysis(self, ai_analysis_service, mock_zotero_item):
        """Test retrieving analysis results when no analysis exists"""
        user_id = "user_123"
        
        with patch('services.zotero.zotero_ai_analysis_service.get_db'), \
             patch.object(ai_analysis_service, '_get_user_item', return_value=mock_zotero_item):
            
            result = await ai_analysis_service.get_analysis_results(
                item_id="item_123",
                user_id=user_id
            )
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_extract_topics_success(self, ai_analysis_service, mock_zotero_item, mock_llm_response_topics):
        """Test topic extraction"""
        content = "Machine learning and natural language processing research"
        
        with patch.object(ai_analysis_service, '_call_llm', return_value=mock_llm_response_topics):
            result = await ai_analysis_service._extract_topics(content, mock_zotero_item)
            
            assert "machine learning" in result["primary_topics"]
            assert result["research_domain"] == "Computer Science"
            assert result["confidence_score"] == 0.85
            assert "extraction_timestamp" in result
    
    @pytest.mark.asyncio
    async def test_extract_topics_invalid_json(self, ai_analysis_service, mock_zotero_item):
        """Test topic extraction with invalid JSON response"""
        content = "Test content"
        
        with patch.object(ai_analysis_service, '_call_llm', return_value="invalid json"):
            result = await ai_analysis_service._extract_topics(content, mock_zotero_item)
            
            assert result["primary_topics"] == []
            assert result["confidence_score"] == 0.0
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_extract_keywords_success(self, ai_analysis_service, mock_zotero_item, mock_llm_response_keywords):
        """Test keyword extraction"""
        content = "Machine learning and natural language processing research"
        
        with patch.object(ai_analysis_service, '_call_llm', return_value=mock_llm_response_keywords):
            result = await ai_analysis_service._extract_keywords(content, mock_zotero_item)
            
            assert "neural networks" in result["technical_keywords"]
            assert "research" in result["general_keywords"]
            assert result["confidence_score"] == 0.80
            assert "extraction_timestamp" in result
    
    @pytest.mark.asyncio
    async def test_generate_summary_success(self, ai_analysis_service, mock_zotero_item, mock_llm_response_summary):
        """Test summary generation"""
        content = "Machine learning and natural language processing research"
        
        with patch.object(ai_analysis_service, '_call_llm', return_value=mock_llm_response_summary):
            result = await ai_analysis_service._generate_summary(content, mock_zotero_item)
            
            assert "machine learning applications" in result["concise_summary"]
            assert len(result["key_findings"]) == 3
            assert result["confidence_score"] == 0.90
            assert "generation_timestamp" in result
    
    @pytest.mark.asyncio
    async def test_call_llm_success(self, ai_analysis_service):
        """Test successful LLM call"""
        prompt = "Test prompt"
        expected_response = "Test response"
        
        mock_response = Mock()
        mock_response.json.return_value = {"response": expected_response}
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            result = await ai_analysis_service._call_llm(prompt)
            
            assert result == expected_response
            mock_post.assert_called_once()
            
            # Verify request parameters
            call_args = mock_post.call_args
            assert call_args[1]["json"]["model"] == ai_analysis_service.model
            assert call_args[1]["json"]["prompt"] == prompt
            assert call_args[1]["json"]["stream"] is False
    
    @pytest.mark.asyncio
    async def test_call_llm_request_error(self, ai_analysis_service):
        """Test LLM call with request error"""
        prompt = "Test prompt"
        
        with patch('requests.post', side_effect=Exception("Connection error")):
            with pytest.raises(Exception, match="LLM service unavailable"):
                await ai_analysis_service._call_llm(prompt)
    
    def test_extract_item_content_full_item(self, ai_analysis_service, mock_zotero_item):
        """Test content extraction from full item"""
        content = ai_analysis_service._extract_item_content(mock_zotero_item)
        
        assert "Title: Machine Learning in Academic Research" in content
        assert "Abstract: This paper explores" in content
        assert "Authors: John Doe, Jane Smith" in content
        assert "Publication: Journal of AI Research" in content
        assert "Year: 2023" in content
        assert "Tags: machine learning, NLP, research" in content
    
    def test_extract_item_content_minimal_item(self, ai_analysis_service):
        """Test content extraction from minimal item"""
        minimal_item = ZoteroItem(
            id="item_123",
            library_id="lib_123",
            zotero_item_key="ABCD1234",
            item_type="journalArticle",
            title="Test Title",
            creators=[],
            tags=[],
            item_metadata={}
        )
        
        content = ai_analysis_service._extract_item_content(minimal_item)
        assert content == "Title: Test Title"
    
    def test_extract_item_content_empty_item(self, ai_analysis_service):
        """Test content extraction from empty item"""
        empty_item = ZoteroItem(
            id="item_123",
            library_id="lib_123",
            zotero_item_key="ABCD1234",
            item_type="journalArticle",
            creators=[],
            tags=[],
            item_metadata={}
        )
        
        content = ai_analysis_service._extract_item_content(empty_item)
        assert content == ""
    
    @pytest.mark.asyncio
    async def test_store_analysis_results_success(self, ai_analysis_service):
        """Test storing analysis results"""
        mock_db = Mock(spec=Session)
        mock_item = Mock()
        mock_item.item_metadata = {}
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_item
        
        analysis_results = {"test": "data"}
        
        await ai_analysis_service._store_analysis_results(
            db=mock_db,
            item_id="item_123",
            analysis_results=analysis_results
        )
        
        assert mock_item.item_metadata["ai_analysis"] == analysis_results
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_analysis_results_error(self, ai_analysis_service):
        """Test storing analysis results with database error"""
        mock_db = Mock(spec=Session)
        mock_db.query.side_effect = Exception("Database error")
        
        analysis_results = {"test": "data"}
        
        with pytest.raises(Exception):
            await ai_analysis_service._store_analysis_results(
                db=mock_db,
                item_id="item_123",
                analysis_results=analysis_results
            )
        
        mock_db.rollback.assert_called_once()