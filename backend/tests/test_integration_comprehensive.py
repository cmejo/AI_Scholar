"""
Comprehensive integration tests for the AI Scholar RAG system.
Tests service interactions and end-to-end workflows.
"""
import pytest
import asyncio
import tempfile
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app import app
from services.enhanced_rag_service import EnhancedRAGService
from services.memory_service import ConversationMemoryManager
from services.knowledge_graph import KnowledgeGraphService
from services.user_profile_service import UserProfileService
from services.analytics_service import AnalyticsService
from models.schemas import User, Document, Conversation, Message


@pytest.mark.integration
class TestRAGServiceIntegration:
    """Integration tests for RAG service with other components."""
    
    @pytest.fixture
    async def integration_setup(self, test_db_session, mock_redis, mock_vector_store):
        """Setup for integration tests."""
        # Create test user
        test_user = User(
            id="integration-user",
            email="integration@test.com",
            username="integration_user",
            is_active=True
        )
        test_db_session.add(test_user)
        test_db_session.commit()
        
        # Create test document
        test_doc = Document(
            id="integration-doc",
            title="Integration Test Document",
            content="This is a test document about machine learning and AI.",
            file_path="/tmp/test.pdf",
            user_id="integration-user",
            metadata={"pages": 1, "size": 1024}
        )
        test_db_session.add(test_doc)
        test_db_session.commit()
        
        return {
            'user': test_user,
            'document': test_doc,
            'redis': mock_redis,
            'vector_store': mock_vector_store,
            'db': test_db_session
        }
    
    @pytest.mark.asyncio
    async def test_rag_with_memory_integration(self, integration_setup):
        """Test RAG service integration with memory management."""
        setup = integration_setup
        
        # Mock services
        with patch('services.enhanced_rag_service.ConversationMemoryManager') as mock_memory_manager, \
             patch('services.enhanced_rag_service.VectorStore') as mock_vector_store:
            
            # Setup mocks
            mock_memory_instance = AsyncMock()
            mock_memory_manager.return_value = mock_memory_instance
            mock_memory_instance.get_conversation_context.return_value = {
                'context': ['Previous discussion about AI'],
                'user_preferences': {'complexity': 'intermediate'}
            }
            
            mock_vector_instance = AsyncMock()
            mock_vector_store.return_value = mock_vector_instance
            mock_vector_instance.similarity_search.return_value = [
                {
                    'content': 'Machine learning is a subset of AI',
                    'metadata': {'source': 'test.pdf', 'page': 1},
                    'score': 0.95
                }
            ]
            
            # Create RAG service
            rag_service = EnhancedRAGService(
                db_session=setup['db'],
                redis_client=setup['redis']
            )
            
            # Test query with memory context
            query = "What is deep learning?"
            conversation_id = "test-conv-123"
            
            response = await rag_service.generate_response(
                query=query,
                user_id=setup['user'].id,
                conversation_id=conversation_id,
                use_memory=True
            )
            
            # Verify response structure
            assert 'response' in response
            assert 'sources' in response
            assert 'confidence_score' in response
            assert 'reasoning_steps' in response
            
            # Verify memory was used
            mock_memory_instance.get_conversation_context.assert_called_once()
            mock_memory_instance.store_memory_item.assert_called()

    @pytest.mark.asyncio
    async def test_rag_with_knowledge_graph_integration(self, integration_setup):
        """Test RAG service integration with knowledge graph."""
        setup = integration_setup
        
        with patch('services.enhanced_rag_service.KnowledgeGraphService') as mock_kg_service:
            # Setup knowledge graph mock
            mock_kg_instance = AsyncMock()
            mock_kg_service.return_value = mock_kg_instance
            mock_kg_instance.query_graph.return_value = {
                'entities': [
                    {'name': 'machine learning', 'type': 'concept'},
                    {'name': 'neural networks', 'type': 'technique'}
                ],
                'relationships': [
                    {'source': 'machine learning', 'target': 'neural networks', 'type': 'includes'}
                ]
            }
            
            # Create RAG service
            rag_service = EnhancedRAGService(
                db_session=setup['db'],
                redis_client=setup['redis']
            )
            
            # Test query with knowledge graph
            query = "How are neural networks related to machine learning?"
            
            response = await rag_service.generate_response(
                query=query,
                user_id=setup['user'].id,
                use_knowledge_graph=True
            )
            
            # Verify knowledge graph was used
            mock_kg_instance.query_graph.assert_called_once()
            assert 'knowledge_graph_context' in response
            assert len(response['knowledge_graph_context']['entities']) == 2

    @pytest.mark.asyncio
    async def test_rag_with_personalization_integration(self, integration_setup):
        """Test RAG service integration with personalization."""
        setup = integration_setup
        
        with patch('services.enhanced_rag_service.UserProfileService') as mock_profile_service:
            # Setup personalization mock
            mock_profile_instance = AsyncMock()
            mock_profile_service.return_value = mock_profile_instance
            mock_profile_instance.get_user_profile.return_value = {
                'preferences': {
                    'complexity': 'advanced',
                    'domain': 'machine_learning',
                    'explanation_style': 'detailed'
                },
                'expertise_level': 0.8
            }
            
            # Create RAG service
            rag_service = EnhancedRAGService(
                db_session=setup['db'],
                redis_client=setup['redis']
            )
            
            # Test personalized query
            query = "Explain gradient descent"
            
            response = await rag_service.generate_response(
                query=query,
                user_id=setup['user'].id,
                personalize=True
            )
            
            # Verify personalization was applied
            mock_profile_instance.get_user_profile.assert_called_once()
            assert 'personalization_applied' in response
            assert response['personalization_applied'] is True


@pytest.mark.integration
class TestDocumentProcessingIntegration:
    """Integration tests for document processing pipeline."""
    
    @pytest.mark.asyncio
    async def test_document_upload_to_search_workflow(self, integration_setup, temp_file):
        """Test complete document upload to search workflow."""
        setup = integration_setup
        
        with patch('services.document_processor.HierarchicalChunkingService') as mock_chunking, \
             patch('services.document_processor.KnowledgeGraphService') as mock_kg, \
             patch('services.document_processor.VectorStore') as mock_vector_store:
            
            # Setup mocks
            mock_chunking_instance = AsyncMock()
            mock_chunking.return_value = mock_chunking_instance
            mock_chunking_instance.chunk_document.return_value = [
                {
                    'id': 'chunk-1',
                    'content': 'First chunk about AI',
                    'metadata': {'page': 1, 'chunk_index': 0}
                },
                {
                    'id': 'chunk-2',
                    'content': 'Second chunk about ML',
                    'metadata': {'page': 1, 'chunk_index': 1}
                }
            ]
            
            mock_kg_instance = AsyncMock()
            mock_kg.return_value = mock_kg_instance
            mock_kg_instance.extract_entities.return_value = [
                {'name': 'AI', 'type': 'concept'},
                {'name': 'ML', 'type': 'concept'}
            ]
            
            mock_vector_instance = AsyncMock()
            mock_vector_store.return_value = mock_vector_instance
            mock_vector_instance.add_documents.return_value = True
            
            # Test document processing
            from services.document_processor import DocumentProcessor
            processor = DocumentProcessor(
                db_session=setup['db'],
                redis_client=setup['redis']
            )
            
            result = await processor.process_document(
                file_path=temp_file,
                user_id=setup['user'].id,
                title="Test Document"
            )
            
            # Verify processing steps
            assert result['success'] is True
            assert 'document_id' in result
            mock_chunking_instance.chunk_document.assert_called_once()
            mock_kg_instance.extract_entities.assert_called()
            mock_vector_instance.add_documents.assert_called()

    @pytest.mark.asyncio
    async def test_hierarchical_chunking_integration(self, integration_setup):
        """Test hierarchical chunking with vector store integration."""
        setup = integration_setup
        
        with patch('services.hierarchical_chunking.SentenceTransformer') as mock_embeddings:
            # Setup embedding mock
            mock_embeddings.return_value.encode.return_value = [[0.1] * 384, [0.2] * 384]
            
            from services.hierarchical_chunking import HierarchicalChunkingService
            chunking_service = HierarchicalChunkingService()
            
            # Test document with multiple paragraphs
            test_content = """
            Machine learning is a subset of artificial intelligence. It focuses on algorithms that can learn from data.
            
            Deep learning is a subset of machine learning. It uses neural networks with multiple layers.
            
            Natural language processing is another AI field. It deals with understanding human language.
            """
            
            chunks = await chunking_service.chunk_document(
                content=test_content,
                strategy="hierarchical",
                overlap_percentage=0.1
            )
            
            # Verify hierarchical structure
            assert len(chunks) > 0
            assert any(chunk.get('parent_chunk_id') is not None for chunk in chunks)
            assert all('chunk_level' in chunk for chunk in chunks)


@pytest.mark.integration
class TestAnalyticsIntegration:
    """Integration tests for analytics and monitoring."""
    
    @pytest.mark.asyncio
    async def test_query_analytics_workflow(self, integration_setup):
        """Test complete query analytics workflow."""
        setup = integration_setup
        
        with patch('services.analytics_service.time') as mock_time:
            mock_time.time.side_effect = [1000.0, 1002.5]  # 2.5 second response time
            
            from services.analytics_service import AnalyticsService
            analytics = AnalyticsService(
                db_session=setup['db'],
                redis_client=setup['redis']
            )
            
            # Simulate query execution with analytics
            query_data = {
                'user_id': setup['user'].id,
                'query': 'What is machine learning?',
                'response_time': 2.5,
                'sources_used': 3,
                'confidence_score': 0.85,
                'user_feedback': 'positive'
            }
            
            # Track query
            await analytics.track_query(query_data)
            
            # Get analytics report
            report = await analytics.generate_usage_report(
                user_id=setup['user'].id,
                time_range='1d'
            )
            
            # Verify analytics data
            assert 'query_count' in report
            assert 'average_response_time' in report
            assert 'average_confidence' in report
            assert report['query_count'] >= 1

    @pytest.mark.asyncio
    async def test_user_behavior_analytics(self, integration_setup):
        """Test user behavior analytics integration."""
        setup = integration_setup
        
        from services.analytics_service import AnalyticsService
        analytics = AnalyticsService(
            db_session=setup['db'],
            redis_client=setup['redis']
        )
        
        # Simulate multiple user interactions
        interactions = [
            {'action': 'query', 'data': {'query': 'What is AI?', 'domain': 'ai'}},
            {'action': 'feedback', 'data': {'rating': 5, 'query_id': 'q1'}},
            {'action': 'document_view', 'data': {'document_id': setup['document'].id}},
            {'action': 'query', 'data': {'query': 'Explain neural networks', 'domain': 'ai'}}
        ]
        
        for interaction in interactions:
            await analytics.track_user_interaction(
                user_id=setup['user'].id,
                action=interaction['action'],
                data=interaction['data']
            )
        
        # Analyze user behavior patterns
        patterns = await analytics.analyze_user_patterns(setup['user'].id)
        
        # Verify pattern analysis
        assert 'preferred_domains' in patterns
        assert 'query_frequency' in patterns
        assert 'engagement_score' in patterns


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Integration tests for error handling and graceful degradation."""
    
    @pytest.mark.asyncio
    async def test_service_failure_graceful_degradation(self, integration_setup):
        """Test graceful degradation when services fail."""
        setup = integration_setup
        
        # Simulate memory service failure
        with patch('services.enhanced_rag_service.ConversationMemoryManager') as mock_memory:
            mock_memory.side_effect = Exception("Memory service unavailable")
            
            from services.enhanced_rag_service import EnhancedRAGService
            rag_service = EnhancedRAGService(
                db_session=setup['db'],
                redis_client=setup['redis']
            )
            
            # Query should still work without memory
            response = await rag_service.generate_response(
                query="What is AI?",
                user_id=setup['user'].id,
                use_memory=True  # This should fail gracefully
            )
            
            # Verify response is still generated
            assert 'response' in response
            assert 'error' not in response or response.get('memory_error') is True

    @pytest.mark.asyncio
    async def test_database_error_handling(self, integration_setup):
        """Test database error handling in integrated workflow."""
        setup = integration_setup
        
        # Simulate database connection error
        with patch.object(setup['db'], 'commit', side_effect=Exception("Database error")):
            from services.user_profile_service import UserProfileService
            profile_service = UserProfileService(
                db_session=setup['db'],
                redis_client=setup['redis']
            )
            
            # Should handle database error gracefully
            result = await profile_service.update_user_preferences(
                user_id=setup['user'].id,
                preferences={'language': 'en'}
            )
            
            # Verify error was handled
            assert result is False or 'error' in result

    @pytest.mark.asyncio
    async def test_redis_failure_fallback(self, integration_setup):
        """Test fallback behavior when Redis is unavailable."""
        setup = integration_setup
        
        # Simulate Redis failure
        setup['redis'].get.side_effect = Exception("Redis connection failed")
        setup['redis'].set.side_effect = Exception("Redis connection failed")
        
        from services.memory_service import ConversationMemoryManager
        memory_manager = ConversationMemoryManager(
            redis_client=setup['redis'],
            db_session=setup['db']
        )
        
        # Should fallback to database-only operation
        result = await memory_manager.store_memory_item(
            conversation_id="test-conv",
            memory_item={
                'content': 'Test memory',
                'importance_score': 0.5
            }
        )
        
        # Verify fallback behavior
        assert result is not None  # Should not crash


@pytest.mark.integration
class TestPerformanceIntegration:
    """Integration tests for performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_concurrent_query_handling(self, integration_setup, performance_timer):
        """Test handling multiple concurrent queries."""
        setup = integration_setup
        
        from services.enhanced_rag_service import EnhancedRAGService
        rag_service = EnhancedRAGService(
            db_session=setup['db'],
            redis_client=setup['redis']
        )
        
        # Create multiple concurrent queries
        queries = [
            "What is machine learning?",
            "Explain neural networks",
            "How does deep learning work?",
            "What are the applications of AI?",
            "Describe supervised learning"
        ]
        
        performance_timer.start()
        
        # Execute queries concurrently
        tasks = [
            rag_service.generate_response(
                query=query,
                user_id=setup['user'].id
            )
            for query in queries
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        performance_timer.stop()
        
        # Verify all queries completed
        assert len(responses) == len(queries)
        assert all(not isinstance(r, Exception) for r in responses)
        
        # Verify reasonable performance (should complete within 30 seconds)
        assert performance_timer.elapsed < 30.0

    @pytest.mark.asyncio
    async def test_large_document_processing_performance(self, integration_setup, performance_timer):
        """Test performance with large document processing."""
        setup = integration_setup
        
        # Create large document content
        large_content = "This is a test sentence. " * 10000  # ~250KB of text
        
        with patch('services.document_processor.HierarchicalChunkingService') as mock_chunking:
            mock_chunking_instance = AsyncMock()
            mock_chunking.return_value = mock_chunking_instance
            
            # Simulate chunking large document
            mock_chunking_instance.chunk_document.return_value = [
                {'id': f'chunk-{i}', 'content': f'Chunk {i}', 'metadata': {}}
                for i in range(100)  # 100 chunks
            ]
            
            from services.document_processor import DocumentProcessor
            processor = DocumentProcessor(
                db_session=setup['db'],
                redis_client=setup['redis']
            )
            
            performance_timer.start()
            
            result = await processor.process_document(
                content=large_content,
                user_id=setup['user'].id,
                title="Large Test Document"
            )
            
            performance_timer.stop()
            
            # Verify processing completed successfully
            assert result['success'] is True
            
            # Verify reasonable performance (should complete within 60 seconds)
            assert performance_timer.elapsed < 60.0


@pytest.mark.integration
class TestEndToEndWorkflows:
    """End-to-end integration tests for complete user workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_user_session_workflow(self, integration_setup):
        """Test complete user session from document upload to query."""
        setup = integration_setup
        
        # Mock all required services
        with patch('services.document_processor.HierarchicalChunkingService') as mock_chunking, \
             patch('services.enhanced_rag_service.VectorStore') as mock_vector_store, \
             patch('services.enhanced_rag_service.ConversationMemoryManager') as mock_memory:
            
            # Setup mocks
            mock_chunking.return_value.chunk_document.return_value = [
                {'id': 'chunk-1', 'content': 'AI content', 'metadata': {}}
            ]
            
            mock_vector_store.return_value.similarity_search.return_value = [
                {'content': 'AI content', 'metadata': {}, 'score': 0.9}
            ]
            
            mock_memory.return_value.get_conversation_context.return_value = {
                'context': [], 'user_preferences': {}
            }
            
            # Step 1: Upload document
            from services.document_processor import DocumentProcessor
            processor = DocumentProcessor(
                db_session=setup['db'],
                redis_client=setup['redis']
            )
            
            doc_result = await processor.process_document(
                content="This document discusses artificial intelligence and machine learning.",
                user_id=setup['user'].id,
                title="AI Overview"
            )
            
            assert doc_result['success'] is True
            
            # Step 2: Query the document
            from services.enhanced_rag_service import EnhancedRAGService
            rag_service = EnhancedRAGService(
                db_session=setup['db'],
                redis_client=setup['redis']
            )
            
            query_response = await rag_service.generate_response(
                query="What is artificial intelligence?",
                user_id=setup['user'].id
            )
            
            assert 'response' in query_response
            assert 'sources' in query_response
            
            # Step 3: Provide feedback
            from services.analytics_service import AnalyticsService
            analytics = AnalyticsService(
                db_session=setup['db'],
                redis_client=setup['redis']
            )
            
            feedback_result = await analytics.track_user_feedback(
                user_id=setup['user'].id,
                query_id=query_response.get('query_id', 'test-query'),
                feedback={'rating': 5, 'helpful': True}
            )
            
            assert feedback_result is True

    @pytest.mark.asyncio
    async def test_multi_user_conversation_workflow(self, integration_setup):
        """Test workflow with multiple users and conversations."""
        setup = integration_setup
        
        # Create additional test user
        user2 = User(
            id="integration-user-2",
            email="user2@test.com",
            username="user2",
            is_active=True
        )
        setup['db'].add(user2)
        setup['db'].commit()
        
        with patch('services.enhanced_rag_service.VectorStore') as mock_vector_store:
            mock_vector_store.return_value.similarity_search.return_value = [
                {'content': 'Test content', 'metadata': {}, 'score': 0.8}
            ]
            
            from services.enhanced_rag_service import EnhancedRAGService
            rag_service = EnhancedRAGService(
                db_session=setup['db'],
                redis_client=setup['redis']
            )
            
            # User 1 conversation
            response1 = await rag_service.generate_response(
                query="What is machine learning?",
                user_id=setup['user'].id,
                conversation_id="conv-user1"
            )
            
            # User 2 conversation
            response2 = await rag_service.generate_response(
                query="What is deep learning?",
                user_id=user2.id,
                conversation_id="conv-user2"
            )
            
            # Verify both conversations work independently
            assert 'response' in response1
            assert 'response' in response2
            assert response1.get('conversation_id') != response2.get('conversation_id')