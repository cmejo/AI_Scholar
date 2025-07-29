"""
Tests for AutoTaggingService
"""
import pytest
import pytest_asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session
from datetime import datetime

from services.auto_tagging_service import AutoTaggingService, auto_tagging_service
from models.schemas import DocumentTagCreate, DocumentTagResponse, TagType
from core.database import DocumentTag


class TestAutoTaggingService:
    """Test cases for AutoTaggingService"""
    
    @pytest.fixture
    def service(self):
        return AutoTaggingService()
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_content(self):
        return """
        This is a comprehensive guide to machine learning algorithms and their applications
        in modern data science. The document covers supervised learning, unsupervised learning,
        and reinforcement learning techniques. It includes practical examples using Python
        and popular libraries like scikit-learn and TensorFlow. The content is designed
        for intermediate to advanced practitioners who want to deepen their understanding
        of algorithmic approaches to artificial intelligence.
        """
    
    @pytest.fixture
    def mock_llm_response_topics(self):
        return json.dumps({
            "topics": [
                {"name": "machine learning", "confidence": 0.95, "explanation": "Primary focus on ML algorithms"},
                {"name": "data science", "confidence": 0.88, "explanation": "Applied data science context"},
                {"name": "artificial intelligence", "confidence": 0.82, "explanation": "Broader AI context"}
            ]
        })
    
    @pytest.fixture
    def mock_llm_response_domains(self):
        return json.dumps({
            "domains": [
                {"name": "computer science", "confidence": 0.92, "explanation": "Technical CS content"},
                {"name": "technology", "confidence": 0.85, "explanation": "Technology domain"}
            ]
        })
    
    @pytest.fixture
    def mock_llm_response_complexity(self):
        return json.dumps({
            "complexity": {
                "overall_level": "intermediate",
                "confidence": 0.85,
                "aspects": [
                    {"name": "technical_complexity", "level": "advanced", "confidence": 0.80},
                    {"name": "vocabulary_difficulty", "level": "intermediate", "confidence": 0.90}
                ]
            }
        })
    
    @pytest.fixture
    def mock_llm_response_sentiment(self):
        return json.dumps({
            "sentiment": {
                "emotional_tone": "neutral",
                "formality": "formal",
                "objectivity": "objective",
                "confidence": 0.80
            }
        })
    
    @pytest.fixture
    def mock_llm_response_categories(self):
        return json.dumps({
            "categories": [
                {"name": "tutorial", "confidence": 0.90},
                {"name": "technical_guide", "confidence": 0.85}
            ]
        })
    
    @patch('services.auto_tagging_service.requests.post')
    @pytest.mark.asyncio
    async def test_generate_topic_tags(self, mock_post, service, mock_llm_response_topics):
        """Test topic tag generation"""
        mock_response = Mock()
        mock_response.json.return_value = {"response": mock_llm_response_topics}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        content = "Sample content about machine learning"
        tags = await service._generate_topic_tags(content)
        
        assert len(tags) == 3
        assert tags[0]['name'] == 'machine_learning'
        assert tags[0]['type'] == 'topic'
        assert tags[0]['confidence'] == 0.95
        assert 'explanation' in tags[0]
    
    @patch('services.auto_tagging_service.requests.post')
    @pytest.mark.asyncio
    async def test_generate_domain_tags(self, mock_post, service, mock_llm_response_domains):
        """Test domain tag generation"""
        mock_response = Mock()
        mock_response.json.return_value = {"response": mock_llm_response_domains}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        content = "Sample content about computer science"
        tags = await service._generate_domain_tags(content)
        
        assert len(tags) == 2
        assert tags[0]['name'] == 'computer_science'
        assert tags[0]['type'] == 'domain'
        assert tags[0]['confidence'] == 0.92
    
    @patch('services.auto_tagging_service.requests.post')
    @pytest.mark.asyncio
    async def test_generate_complexity_tags(self, mock_post, service, mock_llm_response_complexity):
        """Test complexity tag generation"""
        mock_response = Mock()
        mock_response.json.return_value = {"response": mock_llm_response_complexity}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        content = "Sample technical content"
        tags = await service._generate_complexity_tags(content)
        
        assert len(tags) >= 1
        # Check for overall complexity tag
        overall_tag = next((tag for tag in tags if tag['name'] == 'complexity_intermediate'), None)
        assert overall_tag is not None
        assert overall_tag['type'] == 'complexity'
        assert overall_tag['confidence'] == 0.85
    
    @patch('services.auto_tagging_service.requests.post')
    @pytest.mark.asyncio
    async def test_generate_sentiment_tags(self, mock_post, service, mock_llm_response_sentiment):
        """Test sentiment tag generation"""
        mock_response = Mock()
        mock_response.json.return_value = {"response": mock_llm_response_sentiment}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        content = "Sample content with neutral tone"
        tags = await service._generate_sentiment_tags(content)
        
        assert len(tags) >= 1
        tag_names = [tag['name'] for tag in tags]
        assert any('emotional_tone_neutral' in name for name in tag_names)
        assert all(tag['type'] == 'sentiment' for tag in tags)
    
    @patch('services.auto_tagging_service.requests.post')
    @pytest.mark.asyncio
    async def test_generate_category_tags(self, mock_post, service, mock_llm_response_categories):
        """Test category tag generation"""
        mock_response = Mock()
        mock_response.json.return_value = {"response": mock_llm_response_categories}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        content = "Sample tutorial content"
        tags = await service._generate_category_tags(content)
        
        assert len(tags) == 2
        assert tags[0]['name'] == 'tutorial'
        assert tags[0]['type'] == 'category'
        assert tags[0]['confidence'] == 0.90
    
    @patch('services.auto_tagging_service.requests.post')
    @pytest.mark.asyncio
    async def test_generate_document_tags_integration(
        self, 
        mock_post, 
        service, 
        mock_db, 
        sample_content,
        mock_llm_response_topics,
        mock_llm_response_domains,
        mock_llm_response_complexity,
        mock_llm_response_sentiment,
        mock_llm_response_categories
    ):
        """Test complete document tag generation workflow"""
        # Mock LLM responses for different tag types
        responses = [
            mock_llm_response_topics,
            mock_llm_response_domains,
            mock_llm_response_complexity,
            mock_llm_response_sentiment,
            mock_llm_response_categories
        ]
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Set up side effects for multiple calls
        mock_response.json.side_effect = [{"response": resp} for resp in responses]
        
        # Mock database operations
        mock_tag_instances = []
        def mock_add(tag):
            tag.id = f"tag_{len(mock_tag_instances)}"
            tag.created_at = datetime.now()
            mock_tag_instances.append(tag)
        
        mock_db.add.side_effect = mock_add
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        document_id = "test_doc_123"
        tags = await service.generate_document_tags(document_id, sample_content, mock_db)
        
        # Verify tags were generated
        assert len(tags) > 0
        assert all(isinstance(tag, DocumentTagResponse) for tag in tags)
        
        # Verify database operations
        assert mock_db.add.call_count > 0
        assert mock_db.commit.call_count > 0
        
        # Check tag types are present
        tag_types = {tag.tag_type for tag in tags}
        expected_types = {'topic', 'domain', 'complexity', 'sentiment', 'category'}
        assert tag_types.intersection(expected_types)
    
    @pytest.mark.asyncio
    async def test_get_document_tags(self, service, mock_db):
        """Test retrieving document tags"""
        document_id = "test_doc_123"
        
        # Mock database query
        mock_tags = [
            Mock(
                id="tag_1",
                document_id=document_id,
                tag_name="machine_learning",
                tag_type="topic",
                confidence_score=0.95,
                generated_by="llm",
                created_at=datetime.now()
            ),
            Mock(
                id="tag_2",
                document_id=document_id,
                tag_name="computer_science",
                tag_type="domain",
                confidence_score=0.88,
                generated_by="llm",
                created_at=datetime.now()
            )
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_tags
        mock_db.query.return_value = mock_query
        
        tags = await service.get_document_tags(document_id, mock_db)
        
        assert len(tags) == 2
        assert all(isinstance(tag, DocumentTagResponse) for tag in tags)
        assert tags[0].tag_name == "machine_learning"
        assert tags[1].tag_name == "computer_science"
    
    @pytest.mark.asyncio
    async def test_get_document_tags_with_filter(self, service, mock_db):
        """Test retrieving document tags with type filter"""
        document_id = "test_doc_123"
        tag_type = "topic"
        
        mock_tags = [
            Mock(
                id="tag_1",
                document_id=document_id,
                tag_name="machine_learning",
                tag_type="topic",
                confidence_score=0.95,
                generated_by="llm",
                created_at=datetime.now()
            )
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_tags
        mock_db.query.return_value = mock_query
        
        tags = await service.get_document_tags(document_id, mock_db, tag_type)
        
        assert len(tags) == 1
        assert tags[0].tag_type == "topic"
        # Verify filter was applied
        assert mock_query.filter.call_count == 2  # document_id and tag_type filters
    
    @pytest.mark.asyncio
    async def test_validate_tag_consistency_no_tags(self, service, mock_db):
        """Test tag consistency validation with no tags"""
        document_id = "test_doc_123"
        
        # Mock empty query result
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        result = await service.validate_tag_consistency(document_id, mock_db)
        
        assert result['consistency_score'] == 0.0
        assert "No tags found" in result['issues'][0]
        assert "Generate tags" in result['recommendations'][0]
    
    @pytest.mark.asyncio
    async def test_validate_tag_consistency_with_tags(self, service, mock_db):
        """Test tag consistency validation with existing tags"""
        document_id = "test_doc_123"
        
        mock_tags = [
            Mock(
                id="tag_1",
                document_id=document_id,
                tag_name="machine_learning",
                tag_type="topic",
                confidence_score=0.95,
                generated_by="llm",
                created_at=datetime.now()
            ),
            Mock(
                id="tag_2",
                document_id=document_id,
                tag_name="computer_science",
                tag_type="domain",
                confidence_score=0.88,
                generated_by="llm",
                created_at=datetime.now()
            ),
            Mock(
                id="tag_3",
                document_id=document_id,
                tag_name="complexity_intermediate",
                tag_type="complexity",
                confidence_score=0.75,
                generated_by="llm",
                created_at=datetime.now()
            )
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_tags
        mock_db.query.return_value = mock_query
        
        result = await service.validate_tag_consistency(document_id, mock_db)
        
        assert result['consistency_score'] > 0.5
        assert 'tag_distribution' in result
        assert result['tag_distribution']['topic'] == 1
        assert result['tag_distribution']['domain'] == 1
        assert result['tag_distribution']['complexity'] == 1
        assert result['average_confidence'] > 0.8
    
    @pytest.mark.asyncio
    async def test_validate_tag_consistency_low_confidence(self, service, mock_db):
        """Test tag consistency validation with low confidence tags"""
        document_id = "test_doc_123"
        
        mock_tags = [
            Mock(
                id="tag_1",
                document_id=document_id,
                tag_name="uncertain_topic",
                tag_type="topic",
                confidence_score=0.3,  # Below threshold
                generated_by="llm",
                created_at=datetime.now()
            )
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_tags
        mock_db.query.return_value = mock_query
        
        result = await service.validate_tag_consistency(document_id, mock_db)
        
        assert any("low confidence" in issue for issue in result['issues'])
        assert any("remove low-confidence" in rec for rec in result['recommendations'])
    
    @patch('services.auto_tagging_service.requests.post')
    @pytest.mark.asyncio
    async def test_llm_call_error_handling(self, mock_post, service):
        """Test LLM call error handling"""
        mock_post.side_effect = Exception("Connection error")
        
        with pytest.raises(Exception):
            await service._call_llm("test prompt")
    
    @patch('services.auto_tagging_service.requests.post')
    @pytest.mark.asyncio
    async def test_tag_generation_with_json_parse_error(self, mock_post, service):
        """Test handling of invalid JSON responses from LLM"""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Invalid JSON response"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        content = "Sample content"
        tags = await service._generate_topic_tags(content)
        
        # Should return empty list on JSON parse error
        assert tags == []
    
    @pytest.mark.asyncio
    async def test_confidence_threshold_filtering(self, service, mock_db, sample_content):
        """Test that tags below confidence threshold are filtered out"""
        # Set a high confidence threshold
        service.confidence_threshold = 0.9
        
        with patch('services.auto_tagging_service.requests.post') as mock_post:
            # Mock response with mixed confidence scores
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            responses = [
                json.dumps({"topics": [{"name": "high_conf", "confidence": 0.95}, {"name": "low_conf", "confidence": 0.5}]}),
                json.dumps({"domains": [{"name": "domain", "confidence": 0.3}]}),
                json.dumps({"complexity": {"overall_level": "basic", "confidence": 0.2, "aspects": []}}),
                json.dumps({"sentiment": {"emotional_tone": "neutral", "confidence": 0.1}}),
                json.dumps({"categories": [{"name": "category", "confidence": 0.4}]})
            ]
            
            mock_response.json.side_effect = [{"response": resp} for resp in responses]
            
            # Mock database operations
            mock_tag_instances = []
            def mock_add(tag):
                tag.id = f"tag_{len(mock_tag_instances)}"
                tag.created_at = datetime.now()
                mock_tag_instances.append(tag)
            
            mock_db.add.side_effect = mock_add
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            document_id = "test_doc_123"
            tags = await service.generate_document_tags(document_id, sample_content, mock_db)
            
            # Only high confidence tags should be stored
            assert len(tags) == 1  # Only the high confidence topic tag
            assert tags[0].confidence_score >= 0.9
    
    @pytest.mark.asyncio
    async def test_batch_generate_tags(self, service, mock_db):
        """Test batch tag generation for multiple documents"""
        documents = [
            {"id": "doc1", "content": "Machine learning content"},
            {"id": "doc2", "content": "Web development tutorial"}
        ]
        
        with patch.object(service, 'generate_document_tags') as mock_generate:
            # Mock successful tag generation
            mock_generate.side_effect = [
                [Mock(tag_name="ml", tag_type="topic", confidence_score=0.9)],
                [Mock(tag_name="web", tag_type="topic", confidence_score=0.8)]
            ]
            
            results = await service.batch_generate_tags(documents, mock_db)
            
            assert len(results) == 2
            assert "doc1" in results
            assert "doc2" in results
            assert len(results["doc1"]) == 1
            assert len(results["doc2"]) == 1
    
    @pytest.mark.asyncio
    async def test_update_tag_confidence(self, service, mock_db):
        """Test updating tag confidence score"""
        tag_id = "test_tag_123"
        new_confidence = 0.85
        
        # Mock existing tag
        mock_tag = Mock()
        mock_tag.confidence_score = 0.5
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_tag
        mock_db.query.return_value = mock_query
        mock_db.commit.return_value = None
        
        result = await service.update_tag_confidence(tag_id, new_confidence, mock_db)
        
        assert result is True
        assert mock_tag.confidence_score == new_confidence
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_tag_confidence_invalid_score(self, service, mock_db):
        """Test updating tag confidence with invalid score"""
        tag_id = "test_tag_123"
        invalid_confidence = 1.5  # Above 1.0
        
        result = await service.update_tag_confidence(tag_id, invalid_confidence, mock_db)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_low_confidence_tags(self, service, mock_db):
        """Test deleting tags with low confidence scores"""
        document_id = "test_doc_123"
        
        # Mock low confidence tags
        low_conf_tags = [
            Mock(confidence_score=0.3),
            Mock(confidence_score=0.4)
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = low_conf_tags
        mock_db.query.return_value = mock_query
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None
        
        count = await service.delete_low_confidence_tags(document_id, 0.6, mock_db)
        
        assert count == 2
        assert mock_db.delete.call_count == 2
        mock_db.commit.assert_called_once()


class TestAutoTaggingServiceIntegration:
    """Integration tests for AutoTaggingService"""
    
    def test_global_service_instance(self):
        """Test that global service instance is properly initialized"""
        assert auto_tagging_service is not None
        assert isinstance(auto_tagging_service, AutoTaggingService)
        assert auto_tagging_service.confidence_threshold == 0.6
        assert auto_tagging_service.max_tags_per_type == 5


if __name__ == "__main__":
    pytest.main([__file__])