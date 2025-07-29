"""
Tests for Enhanced RAG Service with Memory Integration
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import sys

# Mock the chromadb module before importing services
sys.modules['chromadb'] = MagicMock()

from services.enhanced_rag_service import EnhancedRAGService, enhanced_rag_service
from services.memory_service import MemoryItem, MemoryType
from models.schemas import EnhancedChatResponse, ReasoningResult, UncertaintyScore


class TestEnhancedRAGService:
    """Test cases for EnhancedRAGService"""
    
    @pytest.fixture
    def enhanced_rag_service(self):
        """Create enhanced RAG service instance for testing"""
        return EnhancedRAGService()
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing"""
        return "test_user_123"
    
    @pytest.fixture
    def sample_conversation_id(self):
        """Sample conversation ID for testing"""
        return "test_conv_456"
    
    @pytest.fixture
    def sample_query(self):
        """Sample user query for testing"""
        return "What are the best practices for machine learning model deployment?"
    
    @pytest.fixture
    def mock_search_results(self):
        """Mock search results for testing"""
        return [
            {
                "content": "Machine learning model deployment requires careful consideration of scalability, monitoring, and version control.",
                "relevance": 0.9,
                "metadata": {
                    "document_name": "ML Best Practices",
                    "page_number": 1,
                    "document_id": "doc_1"
                }
            },
            {
                "content": "Containerization with Docker is a popular approach for ML model deployment.",
                "relevance": 0.8,
                "metadata": {
                    "document_name": "Deployment Guide",
                    "page_number": 3,
                    "document_id": "doc_2"
                }
            }
        ]
    
    @pytest.fixture
    def mock_personalized_context(self):
        """Mock personalized context for testing"""
        return {
            "user_preferences": {
                "response_style": {"value": "detailed", "confidence": 0.8},
                "technical_level": {"value": "advanced", "confidence": 0.9}
            },
            "user_context": {
                "recent_topics": {
                    "data": {"topics": ["machine learning", "deployment"]},
                    "stored_at": datetime.now().isoformat()
                }
            },
            "conversation_history": [],
            "personalization_level": 0.8
        }
    
    @pytest.fixture
    def mock_memory_context(self):
        """Mock memory context for testing"""
        return {
            "conversation_summary": "Discussion about machine learning deployment strategies",
            "relevant_memories": [
                {
                    "content": "User asked about Docker containers",
                    "importance": 0.7,
                    "timestamp": datetime.now().isoformat(),
                    "type": "short_term"
                }
            ],
            "active_entities": ["Docker", "machine learning"],
            "memory_count": 1
        }
    
    @pytest.mark.asyncio
    async def test_generate_enhanced_response_basic(
        self, 
        enhanced_rag_service, 
        sample_user_id, 
        sample_query,
        mock_search_results,
        mock_personalized_context,
        mock_memory_context
    ):
        """Test basic enhanced response generation"""
        
        # Mock database operations
        mock_db = MagicMock()
        mock_conversation = MagicMock()
        mock_conversation.id = "test_conv_123"
        
        with patch('services.enhanced_rag_service.get_db') as mock_get_db, \
             patch.object(enhanced_rag_service, '_store_query_in_memory', return_value=None), \
             patch.object(enhanced_rag_service, '_get_memory_context', return_value=mock_memory_context), \
             patch.object(enhanced_rag_service.user_memory, 'get_personalized_context', return_value=mock_personalized_context), \
             patch.object(enhanced_rag_service, '_enhanced_semantic_search', return_value=mock_search_results), \
             patch.object(enhanced_rag_service, '_build_enhanced_context', return_value="Enhanced context"), \
             patch.object(enhanced_rag_service, '_generate_response_with_reasoning', return_value={
                 "response": "Here are the best practices for ML deployment...",
                 "reasoning_results": [],
                 "uncertainty_score": {"confidence": 0.8}
             }), \
             patch.object(enhanced_rag_service, '_store_response_in_memory', return_value=None), \
             patch.object(enhanced_rag_service, '_learn_from_interaction', return_value=None), \
             patch.object(enhanced_rag_service, '_save_messages_to_db', return_value=None):
            
            mock_get_db.return_value.__next__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = mock_conversation
            
            response = await enhanced_rag_service.generate_enhanced_response(
                query=sample_query,
                user_id=sample_user_id,
                conversation_id="test_conv_123",
                enable_memory=True,
                personalization_level=1.0
            )
            
            assert isinstance(response, EnhancedChatResponse)
            assert response.response == "Here are the best practices for ML deployment..."
            assert response.conversation_id == "test_conv_123"
            assert response.personalization_applied is True
            assert len(response.sources) == 2
    
    @pytest.mark.asyncio
    async def test_store_query_in_memory(
        self, 
        enhanced_rag_service, 
        sample_user_id, 
        sample_query
    ):
        """Test storing query in memory"""
        conversation_id = "test_conv_123"
        
        with patch.object(enhanced_rag_service.memory_manager, 'calculate_importance_score', return_value=0.7), \
             patch.object(enhanced_rag_service.memory_manager, 'store_memory_item', return_value=True), \
             patch.object(enhanced_rag_service, '_extract_entities_from_text', return_value=["machine learning", "deployment"]):
            
            await enhanced_rag_service._store_query_in_memory(
                conversation_id, sample_query, sample_user_id
            )
            
            # Verify that store_memory_item was called
            enhanced_rag_service.memory_manager.store_memory_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_response_in_memory(
        self, 
        enhanced_rag_service, 
        sample_user_id
    ):
        """Test storing response in memory"""
        conversation_id = "test_conv_123"
        response = "Here is a detailed response about machine learning deployment..."
        
        with patch.object(enhanced_rag_service.memory_manager, 'calculate_importance_score', return_value=0.8), \
             patch.object(enhanced_rag_service.memory_manager, 'store_memory_item', return_value=True), \
             patch.object(enhanced_rag_service, '_extract_entities_from_text', return_value=["deployment", "response"]):
            
            await enhanced_rag_service._store_response_in_memory(
                conversation_id, response, sample_user_id
            )
            
            # Verify that store_memory_item was called
            enhanced_rag_service.memory_manager.store_memory_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_memory_context(
        self, 
        enhanced_rag_service, 
        sample_user_id, 
        sample_query
    ):
        """Test getting memory context"""
        conversation_id = "test_conv_123"
        
        # Mock conversation context
        from services.memory_service import ConversationContext, MemoryItem
        mock_conversation_context = ConversationContext(
            conversation_id=conversation_id,
            short_term_memory=[
                MemoryItem("Previous query", MemoryType.SHORT_TERM, 0.6, datetime.now()),
                MemoryItem("User preference", MemoryType.PREFERENCE, 0.9, datetime.now())
            ],
            context_summary="Previous discussion about ML",
            active_entities=["machine learning"],
            last_updated=datetime.now(),
            total_tokens=500
        )
        
        with patch.object(enhanced_rag_service.memory_manager, 'get_conversation_context', return_value=mock_conversation_context), \
             patch.object(enhanced_rag_service.context_compressor, 'prune_context_by_relevance', return_value=mock_conversation_context.short_term_memory):
            
            memory_context = await enhanced_rag_service._get_memory_context(
                conversation_id, sample_user_id, sample_query
            )
            
            assert isinstance(memory_context, dict)
            assert "conversation_summary" in memory_context
            assert "relevant_memories" in memory_context
            assert "active_entities" in memory_context
            assert memory_context["conversation_summary"] == "Previous discussion about ML"
            assert len(memory_context["relevant_memories"]) == 2
    
    @pytest.mark.asyncio
    async def test_enhanced_semantic_search(
        self, 
        enhanced_rag_service, 
        sample_user_id, 
        sample_query,
        mock_search_results,
        mock_personalized_context
    ):
        """Test enhanced semantic search with personalization"""
        
        with patch.object(enhanced_rag_service.vector_store, 'semantic_search', return_value=mock_search_results), \
             patch.object(enhanced_rag_service, '_enhance_with_knowledge_graph', return_value=mock_search_results):
            
            results = await enhanced_rag_service._enhanced_semantic_search(
                sample_query, sample_user_id, mock_personalized_context, max_sources=5
            )
            
            assert isinstance(results, list)
            assert len(results) == 2
            assert results[0]["content"] == mock_search_results[0]["content"]
    
    @pytest.mark.asyncio
    async def test_enhance_with_knowledge_graph(
        self, 
        enhanced_rag_service, 
        sample_query,
        mock_search_results
    ):
        """Test enhancing search results with knowledge graph"""
        
        mock_related_entities = [
            {"name": "Docker", "relationship": "used_for", "confidence": 0.8},
            {"name": "Kubernetes", "relationship": "related_to", "confidence": 0.7}
        ]
        
        with patch.object(enhanced_rag_service, '_extract_entities_from_text', return_value=["machine learning", "deployment"]), \
             patch.object(enhanced_rag_service.knowledge_graph, 'get_related_entities', return_value=mock_related_entities):
            
            enhanced_results = await enhanced_rag_service._enhance_with_knowledge_graph(
                mock_search_results, sample_query
            )
            
            assert isinstance(enhanced_results, list)
            assert len(enhanced_results) == 2
            # Check if knowledge graph enhancement was applied
            for result in enhanced_results:
                assert "metadata" in result
    
    @pytest.mark.asyncio
    async def test_build_enhanced_context(
        self, 
        enhanced_rag_service,
        mock_search_results,
        mock_memory_context,
        mock_personalized_context,
        sample_query
    ):
        """Test building enhanced context"""
        
        context = await enhanced_rag_service._build_enhanced_context(
            mock_search_results, mock_memory_context, mock_personalized_context, sample_query
        )
        
        assert isinstance(context, str)
        assert "User Preferences:" in context
        assert "Conversation Context:" in context
        assert "Relevant Documents:" in context
        assert "ML Best Practices" in context  # From search results
    
    @pytest.mark.asyncio
    async def test_build_personalized_prompt(
        self, 
        enhanced_rag_service,
        sample_query
    ):
        """Test building personalized prompt"""
        
        context = "Sample context for testing"
        
        prompt = await enhanced_rag_service._build_personalized_prompt(
            sample_query, context, citation_mode=True, 
            response_style="detailed", technical_level="advanced"
        )
        
        assert isinstance(prompt, str)
        assert sample_query in prompt
        assert context in prompt
        assert "comprehensive, detailed explanation" in prompt
        assert "technical language appropriate for experts" in prompt
        assert "citations" in prompt
    
    @pytest.mark.asyncio
    async def test_apply_reasoning(
        self, 
        enhanced_rag_service,
        sample_query
    ):
        """Test applying reasoning to response"""
        
        context = "Machine learning deployment requires careful planning because of scalability concerns."
        response = "The main reasons for deployment challenges are scalability and monitoring."
        
        reasoning_results = await enhanced_rag_service._apply_reasoning(
            sample_query, context, response
        )
        
        assert isinstance(reasoning_results, list)
        # Should detect causal reasoning pattern
        causal_results = [r for r in reasoning_results if r.reasoning_type == "causal"]
        assert len(causal_results) > 0
    
    @pytest.mark.asyncio
    async def test_calculate_uncertainty_score(
        self, 
        enhanced_rag_service,
        sample_query
    ):
        """Test calculating uncertainty score"""
        
        response = "Machine learning deployment might require Docker containers. This could be helpful."
        context = "Limited information about deployment strategies."
        
        uncertainty_score = await enhanced_rag_service._calculate_uncertainty_score(
            response, context, sample_query
        )
        
        assert isinstance(uncertainty_score, UncertaintyScore)
        assert 0.0 <= uncertainty_score.confidence <= 1.0
        assert 0.0 <= uncertainty_score.reliability_score <= 1.0
        assert 0.0 <= uncertainty_score.source_quality <= 1.0
        assert isinstance(uncertainty_score.uncertainty_factors, list)
        # Should detect vague language
        assert any("vague" in factor.lower() for factor in uncertainty_score.uncertainty_factors)
    
    @pytest.mark.asyncio
    async def test_learn_from_interaction(
        self, 
        enhanced_rag_service,
        sample_user_id,
        sample_query,
        mock_search_results
    ):
        """Test learning from user interaction"""
        
        response_data = {
            "response": "Detailed response about machine learning deployment...",
            "reasoning_results": [{"type": "causal", "confidence": 0.8}],
            "uncertainty_score": {"confidence": 0.7}
        }
        
        with patch.object(enhanced_rag_service.user_memory, 'learn_preference_from_interaction', return_value=["response_style"]):
            
            await enhanced_rag_service._learn_from_interaction(
                sample_user_id, sample_query, response_data, mock_search_results
            )
            
            # Verify that learning was attempted
            enhanced_rag_service.user_memory.learn_preference_from_interaction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_entities_from_text(self, enhanced_rag_service):
        """Test entity extraction from text"""
        
        text = "Machine Learning and Docker are important for deployment. Python is also useful."
        
        entities = await enhanced_rag_service._extract_entities_from_text(text)
        
        assert isinstance(entities, list)
        assert len(entities) <= 5  # Should return max 5 entities
        # Should extract capitalized words/phrases
        expected_entities = ["Machine Learning", "Docker", "Python"]
        for entity in expected_entities:
            if entity in entities:
                assert True
                break
        else:
            # At least some entities should be extracted
            assert len(entities) > 0
    
    @pytest.mark.asyncio
    async def test_format_sources(self, enhanced_rag_service, mock_search_results):
        """Test formatting search results as sources"""
        
        sources = enhanced_rag_service._format_sources(mock_search_results)
        
        assert isinstance(sources, list)
        assert len(sources) == 2
        
        for source in sources:
            assert hasattr(source, 'document')
            assert hasattr(source, 'page')
            assert hasattr(source, 'relevance')
            assert hasattr(source, 'snippet')
        
        assert sources[0].document == "ML Best Practices"
        assert sources[0].page == 1
        assert sources[0].relevance == 0.9
    
    @pytest.mark.asyncio
    async def test_memory_integration_disabled(
        self, 
        enhanced_rag_service, 
        sample_user_id, 
        sample_query,
        mock_search_results
    ):
        """Test enhanced RAG service with memory disabled"""
        
        # Mock database operations
        mock_db = MagicMock()
        mock_conversation = MagicMock()
        mock_conversation.id = "test_conv_123"
        
        with patch('services.enhanced_rag_service.get_db') as mock_get_db, \
             patch.object(enhanced_rag_service, '_enhanced_semantic_search', return_value=mock_search_results), \
             patch.object(enhanced_rag_service, '_build_enhanced_context', return_value="Basic context"), \
             patch.object(enhanced_rag_service, '_generate_response_with_reasoning', return_value={
                 "response": "Basic response without memory",
                 "reasoning_results": [],
                 "uncertainty_score": {"confidence": 0.6}
             }), \
             patch.object(enhanced_rag_service, '_save_messages_to_db', return_value=None):
            
            mock_get_db.return_value.__next__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = mock_conversation
            
            response = await enhanced_rag_service.generate_enhanced_response(
                query=sample_query,
                user_id=sample_user_id,
                conversation_id="test_conv_123",
                enable_memory=False,  # Memory disabled
                personalization_level=0.0  # Personalization disabled
            )
            
            assert isinstance(response, EnhancedChatResponse)
            assert response.response == "Basic response without memory"
            assert response.personalization_applied is False
            assert response.memory_context == {}
    
    @pytest.mark.asyncio
    async def test_error_handling_memory_failure(
        self, 
        enhanced_rag_service, 
        sample_user_id, 
        sample_query,
        mock_search_results
    ):
        """Test error handling when memory operations fail"""
        
        # Mock database operations
        mock_db = MagicMock()
        mock_conversation = MagicMock()
        mock_conversation.id = "test_conv_123"
        
        with patch('services.enhanced_rag_service.get_db') as mock_get_db, \
             patch.object(enhanced_rag_service, '_store_query_in_memory', side_effect=Exception("Memory error")), \
             patch.object(enhanced_rag_service, '_get_memory_context', return_value={}), \
             patch.object(enhanced_rag_service.user_memory, 'get_personalized_context', return_value={}), \
             patch.object(enhanced_rag_service, '_enhanced_semantic_search', return_value=mock_search_results), \
             patch.object(enhanced_rag_service, '_build_enhanced_context', return_value="Fallback context"), \
             patch.object(enhanced_rag_service, '_generate_response_with_reasoning', return_value={
                 "response": "Response despite memory error",
                 "reasoning_results": [],
                 "uncertainty_score": {"confidence": 0.5}
             }), \
             patch.object(enhanced_rag_service, '_store_response_in_memory', side_effect=Exception("Memory error")), \
             patch.object(enhanced_rag_service, '_learn_from_interaction', return_value=None), \
             patch.object(enhanced_rag_service, '_save_messages_to_db', return_value=None):
            
            mock_get_db.return_value.__next__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = mock_conversation
            
            # Should not raise exception despite memory errors
            response = await enhanced_rag_service.generate_enhanced_response(
                query=sample_query,
                user_id=sample_user_id,
                conversation_id="test_conv_123",
                enable_memory=True
            )
            
            assert isinstance(response, EnhancedChatResponse)
            assert response.response == "Response despite memory error"


if __name__ == "__main__":
    pytest.main([__file__])