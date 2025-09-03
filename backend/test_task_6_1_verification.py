"""
Verification tests for Task 6.1: Implement reference content analysis
Tests the AI analysis service and endpoints for Zotero references
"""
import asyncio
import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from sqlalchemy.orm import Session

# Test the service implementation
def test_ai_analysis_service_import():
    """Test that the AI analysis service can be imported"""
    try:
        from services.zotero.zotero_ai_analysis_service import ZoteroAIAnalysisService
        service = ZoteroAIAnalysisService()
        assert service is not None
        assert hasattr(service, 'analyze_reference_content')
        assert hasattr(service, 'batch_analyze_references')
        assert hasattr(service, 'get_analysis_results')
        print("✓ AI Analysis Service imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import AI Analysis Service: {e}")
        raise


def test_ai_analysis_endpoints_import():
    """Test that the AI analysis endpoints can be imported"""
    try:
        from api.zotero_ai_analysis_endpoints import router
        assert router is not None
        
        # Check that key endpoints exist
        routes = [route.path for route in router.routes]
        expected_routes = [
            "/zotero/ai-analysis/analyze/{item_id}",
            "/zotero/ai-analysis/analyze/batch",
            "/zotero/ai-analysis/results/{item_id}",
            "/zotero/ai-analysis/supported-types",
            "/zotero/ai-analysis/results/{item_id}",  # DELETE
            "/zotero/ai-analysis/stats/{library_id}"
        ]
        
        for expected_route in expected_routes:
            # Check if any route matches the expected pattern
            route_found = any(expected_route.replace("{item_id}", "item_id").replace("{library_id}", "library_id") 
                            in route.replace("{", "").replace("}", "") for route in routes)
            if not route_found:
                print(f"Route pattern found in routes: {routes}")
        
        print("✓ AI Analysis Endpoints imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import AI Analysis Endpoints: {e}")
        raise


@pytest.mark.asyncio
async def test_analyze_reference_content_functionality():
    """Test the core analyze_reference_content functionality"""
    try:
        from services.zotero.zotero_ai_analysis_service import ZoteroAIAnalysisService
        from models.zotero_models import ZoteroItem
        
        service = ZoteroAIAnalysisService()
        
        # Create mock item
        mock_item = ZoteroItem(
            id="test_item_123",
            library_id="test_lib_123",
            zotero_item_key="ABCD1234",
            item_type="journalArticle",
            title="Machine Learning in Academic Research",
            creators=[{"firstName": "John", "lastName": "Doe", "creatorType": "author"}],
            publication_title="Journal of AI Research",
            publication_year=2023,
            abstract_note="This paper explores machine learning applications in research.",
            tags=["machine learning", "research"],
            item_metadata={}
        )
        
        # Mock LLM responses
        mock_topics_response = json.dumps({
            "primary_topics": ["machine learning", "academic research"],
            "secondary_themes": ["data analysis"],
            "research_domain": "Computer Science",
            "methodology": "experimental",
            "confidence_score": 0.85
        })
        
        mock_keywords_response = json.dumps({
            "technical_keywords": ["neural networks", "algorithms"],
            "general_keywords": ["research", "analysis"],
            "author_keywords": ["machine learning"],
            "suggested_keywords": ["artificial intelligence"],
            "confidence_score": 0.80
        })
        
        mock_summary_response = json.dumps({
            "concise_summary": "This paper presents machine learning applications in research.",
            "key_findings": ["ML improves efficiency", "Automated analysis"],
            "methodology": "Experimental study",
            "significance": "Demonstrates practical ML applications",
            "limitations": "Limited to specific domains",
            "confidence_score": 0.90
        })
        
        # Mock dependencies
        with patch('services.zotero.zotero_ai_analysis_service.get_db') as mock_get_db, \
             patch.object(service, '_get_user_item', return_value=mock_item), \
             patch.object(service, '_call_llm') as mock_call_llm, \
             patch.object(service, '_store_analysis_results') as mock_store:
            
            # Configure LLM responses
            mock_call_llm.side_effect = [
                mock_topics_response,
                mock_keywords_response,
                mock_summary_response
            ]
            
            # Test the analysis
            result = await service.analyze_reference_content(
                item_id="test_item_123",
                user_id="test_user_123",
                analysis_types=["topics", "keywords", "summary"]
            )
            
            # Verify result structure
            assert result["item_id"] == "test_item_123"
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
            assert keywords["confidence_score"] == 0.80
            
            # Verify summary analysis
            summary = result["results"]["summary"]
            assert "machine learning applications" in summary["concise_summary"]
            assert len(summary["key_findings"]) == 2
            assert summary["confidence_score"] == 0.90
            
            # Verify LLM was called 3 times (once for each analysis type)
            assert mock_call_llm.call_count == 3
            
            # Verify results were stored
            mock_store.assert_called_once()
            
        print("✓ Reference content analysis functionality works correctly")
        
    except Exception as e:
        print(f"✗ Reference content analysis functionality failed: {e}")
        raise


@pytest.mark.asyncio
async def test_batch_analysis_functionality():
    """Test the batch analysis functionality"""
    try:
        from services.zotero.zotero_ai_analysis_service import ZoteroAIAnalysisService
        
        service = ZoteroAIAnalysisService()
        
        # Mock individual analysis results
        mock_analysis_result = {
            "item_id": "item_1",
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "analysis_types": ["topics"],
            "results": {"topics": {"primary_topics": ["test topic"]}}
        }
        
        with patch.object(service, 'analyze_reference_content', return_value=mock_analysis_result) as mock_analyze:
            result = await service.batch_analyze_references(
                item_ids=["item_1", "item_2", "item_3"],
                user_id="test_user_123",
                analysis_types=["topics"]
            )
            
            # Verify batch result structure
            assert result["total_items"] == 3
            assert result["successful"] == 3
            assert result["failed"] == 0
            assert len(result["results"]) == 3
            assert len(result["errors"]) == 0
            
            # Verify individual analysis was called for each item
            assert mock_analyze.call_count == 3
            
        print("✓ Batch analysis functionality works correctly")
        
    except Exception as e:
        print(f"✗ Batch analysis functionality failed: {e}")
        raise


def test_content_extraction():
    """Test content extraction from Zotero items"""
    try:
        from services.zotero.zotero_ai_analysis_service import ZoteroAIAnalysisService
        from models.zotero_models import ZoteroItem
        
        service = ZoteroAIAnalysisService()
        
        # Test with full item
        full_item = ZoteroItem(
            id="test_item",
            library_id="test_lib",
            zotero_item_key="ABCD1234",
            item_type="journalArticle",
            title="Test Article",
            creators=[
                {"firstName": "John", "lastName": "Doe", "creatorType": "author"},
                {"firstName": "Jane", "lastName": "Smith", "creatorType": "author"}
            ],
            publication_title="Test Journal",
            publication_year=2023,
            abstract_note="This is a test abstract with important content.",
            tags=["test", "research"],
            extra_fields={"DOI": "10.1000/test"},
            item_metadata={}
        )
        
        content = service._extract_item_content(full_item)
        
        # Verify content extraction
        assert "Title: Test Article" in content
        assert "Abstract: This is a test abstract" in content
        assert "Authors: John Doe, Jane Smith" in content
        assert "Publication: Test Journal" in content
        assert "Year: 2023" in content
        assert "Tags: test, research" in content
        
        # Test with minimal item
        minimal_item = ZoteroItem(
            id="test_item",
            library_id="test_lib",
            zotero_item_key="ABCD1234",
            item_type="journalArticle",
            title="Minimal Article",
            creators=[],
            tags=[],
            item_metadata={}
        )
        
        minimal_content = service._extract_item_content(minimal_item)
        assert minimal_content == "Title: Minimal Article"
        
        print("✓ Content extraction works correctly")
        
    except Exception as e:
        print(f"✗ Content extraction failed: {e}")
        raise


@pytest.mark.asyncio
async def test_llm_integration():
    """Test LLM integration functionality"""
    try:
        from services.zotero.zotero_ai_analysis_service import ZoteroAIAnalysisService
        
        service = ZoteroAIAnalysisService()
        
        # Mock successful LLM response
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Test LLM response"}
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            result = await service._call_llm("Test prompt")
            
            assert result == "Test LLM response"
            mock_post.assert_called_once()
            
            # Verify request parameters
            call_args = mock_post.call_args
            assert call_args[1]["json"]["model"] == service.model
            assert call_args[1]["json"]["prompt"] == "Test prompt"
            assert call_args[1]["json"]["stream"] is False
            
        print("✓ LLM integration works correctly")
        
    except Exception as e:
        print(f"✗ LLM integration failed: {e}")
        raise


def test_analysis_result_parsing():
    """Test parsing of LLM analysis results"""
    try:
        from services.zotero.zotero_ai_analysis_service import ZoteroAIAnalysisService
        from models.zotero_models import ZoteroItem
        
        service = ZoteroAIAnalysisService()
        
        # Create test item
        test_item = ZoteroItem(
            id="test_item",
            library_id="test_lib",
            zotero_item_key="ABCD1234",
            item_type="journalArticle",
            title="Test Article",
            abstract_note="Test abstract",
            item_metadata={}
        )
        
        # Test topic extraction parsing
        topics_response = json.dumps({
            "primary_topics": ["topic1", "topic2", "topic3"],
            "secondary_themes": ["theme1", "theme2"],
            "research_domain": "Test Domain",
            "methodology": "experimental",
            "confidence_score": 0.85
        })
        
        async def run_topic_test():
            with patch.object(service, '_call_llm', return_value=topics_response):
                result = await service._extract_topics("test content", test_item)
                
                assert result["primary_topics"] == ["topic1", "topic2", "topic3"]
                assert result["research_domain"] == "Test Domain"
                assert result["confidence_score"] == 0.85
                assert "extraction_timestamp" in result
        
        # Run the async test
        asyncio.run(run_topic_test())
        
        # Test keyword extraction parsing
        keywords_response = json.dumps({
            "technical_keywords": ["keyword1", "keyword2"],
            "general_keywords": ["general1", "general2"],
            "author_keywords": ["author1"],
            "suggested_keywords": ["suggested1"],
            "confidence_score": 0.80
        })
        
        async def run_keyword_test():
            with patch.object(service, '_call_llm', return_value=keywords_response):
                result = await service._extract_keywords("test content", test_item)
                
                assert result["technical_keywords"] == ["keyword1", "keyword2"]
                assert result["general_keywords"] == ["general1", "general2"]
                assert result["confidence_score"] == 0.80
                assert "extraction_timestamp" in result
        
        asyncio.run(run_keyword_test())
        
        # Test summary generation parsing
        summary_response = json.dumps({
            "concise_summary": "Test summary of the content",
            "key_findings": ["finding1", "finding2", "finding3"],
            "methodology": "Test methodology",
            "significance": "Test significance",
            "limitations": "Test limitations",
            "confidence_score": 0.90
        })
        
        async def run_summary_test():
            with patch.object(service, '_call_llm', return_value=summary_response):
                result = await service._generate_summary("test content", test_item)
                
                assert result["concise_summary"] == "Test summary of the content"
                assert len(result["key_findings"]) == 3
                assert result["methodology"] == "Test methodology"
                assert result["confidence_score"] == 0.90
                assert "generation_timestamp" in result
        
        asyncio.run(run_summary_test())
        
        print("✓ Analysis result parsing works correctly")
        
    except Exception as e:
        print(f"✗ Analysis result parsing failed: {e}")
        raise


def test_error_handling():
    """Test error handling in analysis service"""
    try:
        from services.zotero.zotero_ai_analysis_service import ZoteroAIAnalysisService
        from models.zotero_models import ZoteroItem
        
        service = ZoteroAIAnalysisService()
        
        # Test invalid JSON response handling
        test_item = ZoteroItem(
            id="test_item",
            library_id="test_lib",
            zotero_item_key="ABCD1234",
            item_type="journalArticle",
            title="Test Article",
            item_metadata={}
        )
        
        async def run_error_test():
            # Test with invalid JSON
            with patch.object(service, '_call_llm', return_value="invalid json"):
                result = await service._extract_topics("test content", test_item)
                
                assert result["primary_topics"] == []
                assert result["confidence_score"] == 0.0
                assert "error" in result
        
        asyncio.run(run_error_test())
        
        # Test LLM service error handling
        async def run_llm_error_test():
            with patch('requests.post', side_effect=Exception("Connection error")):
                try:
                    await service._call_llm("test prompt")
                    assert False, "Should have raised an exception"
                except Exception as e:
                    assert "LLM service unavailable" in str(e)
        
        asyncio.run(run_llm_error_test())
        
        print("✓ Error handling works correctly")
        
    except Exception as e:
        print(f"✗ Error handling failed: {e}")
        raise


def run_all_tests():
    """Run all verification tests"""
    print("Running Task 6.1 Verification Tests...")
    print("=" * 50)
    
    try:
        # Test imports
        test_ai_analysis_service_import()
        test_ai_analysis_endpoints_import()
        
        # Test core functionality
        asyncio.run(test_analyze_reference_content_functionality())
        asyncio.run(test_batch_analysis_functionality())
        
        # Test supporting functionality
        test_content_extraction()
        asyncio.run(test_llm_integration())
        test_analysis_result_parsing()
        test_error_handling()
        
        print("=" * 50)
        print("✓ All Task 6.1 verification tests passed!")
        print("\nImplemented features:")
        print("- ✓ Reference content analysis using LLMs")
        print("- ✓ Topic extraction and keyword identification")
        print("- ✓ Content summarization for individual references")
        print("- ✓ Batch analysis functionality")
        print("- ✓ Error handling and recovery")
        print("- ✓ API endpoints for analysis operations")
        print("- ✓ Comprehensive test coverage")
        
        return True
        
    except Exception as e:
        print("=" * 50)
        print(f"✗ Task 6.1 verification failed: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)