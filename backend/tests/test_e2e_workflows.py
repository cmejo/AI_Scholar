"""
End-to-end tests for complete user workflows in the AI Scholar RAG system.
Tests complete user journeys from document upload to query responses.
"""
import pytest
import asyncio
import tempfile
import json
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app import app
from models.schemas import User, Document, Conversation


@pytest.mark.e2e
class TestDocumentUploadToQueryWorkflow:
    """End-to-end tests for document upload to query workflow."""
    
    @pytest.fixture
    def test_client_e2e(self, test_db_session, mock_redis):
        """Create test client for E2E tests."""
        app.dependency_overrides.clear()
        
        # Override dependencies
        from core.database import get_db
        from core.redis_client import get_redis_client
        
        app.dependency_overrides[get_db] = lambda: test_db_session
        app.dependency_overrides[get_redis_client] = lambda: mock_redis
        
        with TestClient(app) as client:
            yield client
        
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def test_user_e2e(self, test_db_session):
        """Create test user for E2E tests."""
        user = User(
            id="e2e-user-123",
            email="e2e@test.com",
            username="e2e_user",
            is_active=True
        )
        test_db_session.add(user)
        test_db_session.commit()
        return user
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Create sample PDF content for testing."""
        return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Machine Learning Basics) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000206 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n299\n%%EOF"
    
    def test_complete_document_workflow(self, test_client_e2e, test_user_e2e, sample_pdf_content):
        """Test complete workflow from document upload to query."""
        
        # Mock all the services that would be called
        with patch('services.document_processor.HierarchicalChunkingService') as mock_chunking, \
             patch('services.document_processor.KnowledgeGraphService') as mock_kg, \
             patch('services.document_processor.VectorStore') as mock_vector_store, \
             patch('services.enhanced_rag_service.VectorStore') as mock_rag_vector_store:
            
            # Setup mocks for document processing
            mock_chunking_instance = AsyncMock()
            mock_chunking.return_value = mock_chunking_instance
            mock_chunking_instance.chunk_document.return_value = [
                {
                    'id': 'chunk-1',
                    'content': 'Machine learning is a subset of artificial intelligence.',
                    'metadata': {'page': 1, 'chunk_index': 0}
                },
                {
                    'id': 'chunk-2', 
                    'content': 'It focuses on algorithms that can learn from data.',
                    'metadata': {'page': 1, 'chunk_index': 1}
                }
            ]
            
            mock_kg_instance = AsyncMock()
            mock_kg.return_value = mock_kg_instance
            mock_kg_instance.extract_entities.return_value = [
                {'name': 'machine learning', 'type': 'concept'},
                {'name': 'artificial intelligence', 'type': 'concept'}
            ]
            
            mock_vector_instance = AsyncMock()
            mock_vector_store.return_value = mock_vector_instance
            mock_vector_instance.add_documents.return_value = True
            
            # Setup mocks for RAG service
            mock_rag_vector_instance = AsyncMock()
            mock_rag_vector_store.return_value = mock_rag_vector_instance
            mock_rag_vector_instance.similarity_search.return_value = [
                {
                    'content': 'Machine learning is a subset of artificial intelligence.',
                    'metadata': {'source': 'test.pdf', 'page': 1},
                    'score': 0.95
                }
            ]
            
            # Step 1: Upload document
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(sample_pdf_content)
                temp_file.flush()
                
                with open(temp_file.name, 'rb') as f:
                    response = test_client_e2e.post(
                        "/api/documents/upload",
                        files={"file": ("test.pdf", f, "application/pdf")},
                        data={"user_id": test_user_e2e.id}
                    )
            
            # Verify document upload
            assert response.status_code == 200
            upload_data = response.json()
            assert upload_data["success"] is True
            assert "document_id" in upload_data
            
            document_id = upload_data["document_id"]
            
            # Step 2: Wait for processing (simulate async processing completion)
            import time
            time.sleep(1)  # Simulate processing time
            
            # Step 3: Query the document
            query_response = test_client_e2e.post(
                "/api/chat/query",
                json={
                    "query": "What is machine learning?",
                    "user_id": test_user_e2e.id,
                    "conversation_id": "e2e-conv-123"
                }
            )
            
            # Verify query response
            assert query_response.status_code == 200
            query_data = query_response.json()
            assert "response" in query_data
            assert "sources" in query_data
            assert len(query_data["sources"]) > 0
            
            # Step 4: Provide feedback
            feedback_response = test_client_e2e.post(
                "/api/feedback",
                json={
                    "user_id": test_user_e2e.id,
                    "message_id": query_data.get("message_id", "test-msg"),
                    "feedback": {
                        "rating": 5,
                        "helpful": True,
                        "comment": "Great explanation!"
                    }
                }
            )
            
            # Verify feedback submission
            assert feedback_response.status_code == 200
            feedback_data = feedback_response.json()
            assert feedback_data["success"] is True
            
            # Step 5: Check analytics
            analytics_response = test_client_e2e.get(
                f"/api/analytics/user/{test_user_e2e.id}/summary"
            )
            
            # Verify analytics
            assert analytics_response.status_code == 200
            analytics_data = analytics_response.json()
            assert "query_count" in analytics_data
            assert analytics_data["query_count"] >= 1

    def test_multi_document_query_workflow(self, test_client_e2e, test_user_e2e, sample_pdf_content):
        """Test workflow with multiple documents and cross-document queries."""
        
        with patch('services.document_processor.HierarchicalChunkingService') as mock_chunking, \
             patch('services.enhanced_rag_service.VectorStore') as mock_vector_store:
            
            # Setup mocks
            mock_chunking.return_value.chunk_document.return_value = [
                {'id': 'chunk-1', 'content': 'Document content', 'metadata': {}}
            ]
            
            mock_vector_store.return_value.similarity_search.return_value = [
                {
                    'content': 'Content from document 1',
                    'metadata': {'source': 'doc1.pdf'},
                    'score': 0.9
                },
                {
                    'content': 'Content from document 2', 
                    'metadata': {'source': 'doc2.pdf'},
                    'score': 0.85
                }
            ]
            
            # Upload multiple documents
            document_ids = []
            for i in range(2):
                with tempfile.NamedTemporaryFile(suffix=f'_doc{i}.pdf', delete=False) as temp_file:
                    temp_file.write(sample_pdf_content)
                    temp_file.flush()
                    
                    with open(temp_file.name, 'rb') as f:
                        response = test_client_e2e.post(
                            "/api/documents/upload",
                            files={"file": (f"doc{i}.pdf", f, "application/pdf")},
                            data={"user_id": test_user_e2e.id}
                        )
                    
                    assert response.status_code == 200
                    document_ids.append(response.json()["document_id"])
            
            # Query across documents
            query_response = test_client_e2e.post(
                "/api/chat/query",
                json={
                    "query": "Compare information from both documents",
                    "user_id": test_user_e2e.id,
                    "conversation_id": "multi-doc-conv"
                }
            )
            
            assert query_response.status_code == 200
            query_data = query_response.json()
            
            # Verify sources from multiple documents
            sources = query_data.get("sources", [])
            source_files = {source.get("metadata", {}).get("source") for source in sources}
            assert len(source_files) >= 1  # Should have sources from documents


@pytest.mark.e2e
class TestConversationWorkflow:
    """End-to-end tests for conversation workflows."""
    
    def test_multi_turn_conversation(self, test_client_e2e, test_user_e2e):
        """Test multi-turn conversation with memory."""
        
        with patch('services.enhanced_rag_service.VectorStore') as mock_vector_store, \
             patch('services.memory_service.ConversationMemoryManager') as mock_memory:
            
            # Setup mocks
            mock_vector_store.return_value.similarity_search.return_value = [
                {
                    'content': 'Machine learning information',
                    'metadata': {'source': 'ml.pdf'},
                    'score': 0.9
                }
            ]
            
            mock_memory_instance = AsyncMock()
            mock_memory.return_value = mock_memory_instance
            mock_memory_instance.get_conversation_context.return_value = {
                'context': [],
                'user_preferences': {}
            }
            
            conversation_id = "multi-turn-conv-123"
            
            # Turn 1: Initial query
            response1 = test_client_e2e.post(
                "/api/chat/query",
                json={
                    "query": "What is machine learning?",
                    "user_id": test_user_e2e.id,
                    "conversation_id": conversation_id
                }
            )
            
            assert response1.status_code == 200
            data1 = response1.json()
            assert "response" in data1
            
            # Update mock to include previous context
            mock_memory_instance.get_conversation_context.return_value = {
                'context': ['Previous discussion about machine learning'],
                'user_preferences': {}
            }
            
            # Turn 2: Follow-up query
            response2 = test_client_e2e.post(
                "/api/chat/query",
                json={
                    "query": "Can you give me more details about that?",
                    "user_id": test_user_e2e.id,
                    "conversation_id": conversation_id
                }
            )
            
            assert response2.status_code == 200
            data2 = response2.json()
            assert "response" in data2
            
            # Verify memory was used in second query
            assert mock_memory_instance.get_conversation_context.call_count >= 2

    def test_conversation_with_personalization(self, test_client_e2e, test_user_e2e):
        """Test conversation with user personalization."""
        
        with patch('services.enhanced_rag_service.VectorStore') as mock_vector_store, \
             patch('services.user_profile_service.UserProfileService') as mock_profile:
            
            # Setup mocks
            mock_vector_store.return_value.similarity_search.return_value = [
                {
                    'content': 'Technical content about AI',
                    'metadata': {'source': 'ai.pdf'},
                    'score': 0.9
                }
            ]
            
            mock_profile_instance = AsyncMock()
            mock_profile.return_value = mock_profile_instance
            mock_profile_instance.get_user_profile.return_value = {
                'preferences': {
                    'complexity': 'advanced',
                    'domain': 'machine_learning'
                },
                'expertise_level': 0.8
            }
            
            # Query with personalization
            response = test_client_e2e.post(
                "/api/chat/query",
                json={
                    "query": "Explain neural networks",
                    "user_id": test_user_e2e.id,
                    "conversation_id": "personalized-conv",
                    "personalize": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert data.get("personalization_applied") is True


@pytest.mark.e2e
class TestAnalyticsWorkflow:
    """End-to-end tests for analytics workflows."""
    
    def test_analytics_data_collection_workflow(self, test_client_e2e, test_user_e2e):
        """Test complete analytics data collection workflow."""
        
        with patch('services.enhanced_rag_service.VectorStore') as mock_vector_store:
            mock_vector_store.return_value.similarity_search.return_value = [
                {
                    'content': 'Analytics test content',
                    'metadata': {'source': 'test.pdf'},
                    'score': 0.9
                }
            ]
            
            # Perform multiple queries to generate analytics data
            queries = [
                "What is artificial intelligence?",
                "How does machine learning work?",
                "Explain deep learning",
                "What are neural networks?",
                "Describe natural language processing"
            ]
            
            conversation_id = "analytics-conv-123"
            
            for i, query in enumerate(queries):
                response = test_client_e2e.post(
                    "/api/chat/query",
                    json={
                        "query": query,
                        "user_id": test_user_e2e.id,
                        "conversation_id": f"{conversation_id}-{i}"
                    }
                )
                
                assert response.status_code == 200
                
                # Provide feedback for some queries
                if i % 2 == 0:
                    query_data = response.json()
                    test_client_e2e.post(
                        "/api/feedback",
                        json={
                            "user_id": test_user_e2e.id,
                            "message_id": query_data.get("message_id", f"msg-{i}"),
                            "feedback": {
                                "rating": 4 + (i % 2),
                                "helpful": True
                            }
                        }
                    )
            
            # Get analytics summary
            analytics_response = test_client_e2e.get(
                f"/api/analytics/user/{test_user_e2e.id}/summary"
            )
            
            assert analytics_response.status_code == 200
            analytics_data = analytics_response.json()
            
            # Verify analytics data
            assert analytics_data["query_count"] == len(queries)
            assert "average_response_time" in analytics_data
            assert "user_satisfaction" in analytics_data

    def test_system_wide_analytics_workflow(self, test_client_e2e, test_user_e2e):
        """Test system-wide analytics collection."""
        
        with patch('services.enhanced_rag_service.VectorStore') as mock_vector_store:
            mock_vector_store.return_value.similarity_search.return_value = [
                {
                    'content': 'System analytics content',
                    'metadata': {'source': 'system.pdf'},
                    'score': 0.9
                }
            ]
            
            # Simulate system usage
            for i in range(10):
                test_client_e2e.post(
                    "/api/chat/query",
                    json={
                        "query": f"System test query {i}",
                        "user_id": test_user_e2e.id,
                        "conversation_id": f"system-conv-{i}"
                    }
                )
            
            # Get system analytics
            system_analytics_response = test_client_e2e.get("/api/analytics/system/summary")
            
            assert system_analytics_response.status_code == 200
            system_data = system_analytics_response.json()
            
            # Verify system analytics
            assert "total_queries" in system_data
            assert "active_users" in system_data
            assert "system_performance" in system_data


@pytest.mark.e2e
class TestErrorHandlingWorkflow:
    """End-to-end tests for error handling workflows."""
    
    def test_service_failure_recovery_workflow(self, test_client_e2e, test_user_e2e):
        """Test system behavior when services fail."""
        
        # Test with vector store failure
        with patch('services.enhanced_rag_service.VectorStore') as mock_vector_store:
            mock_vector_store.side_effect = Exception("Vector store unavailable")
            
            response = test_client_e2e.post(
                "/api/chat/query",
                json={
                    "query": "Test query with service failure",
                    "user_id": test_user_e2e.id,
                    "conversation_id": "error-conv-123"
                }
            )
            
            # Should return error response but not crash
            assert response.status_code in [200, 500]  # Depending on error handling strategy
            
            if response.status_code == 200:
                data = response.json()
                assert "error" in data or "response" in data

    def test_invalid_input_handling_workflow(self, test_client_e2e):
        """Test handling of invalid inputs."""
        
        # Test with invalid user ID
        response = test_client_e2e.post(
            "/api/chat/query",
            json={
                "query": "Test query",
                "user_id": "invalid-user-id",
                "conversation_id": "test-conv"
            }
        )
        
        # Should handle invalid user gracefully
        assert response.status_code in [400, 404, 422]
        
        # Test with empty query
        response = test_client_e2e.post(
            "/api/chat/query",
            json={
                "query": "",
                "user_id": "test-user",
                "conversation_id": "test-conv"
            }
        )
        
        # Should handle empty query
        assert response.status_code in [400, 422]

    def test_rate_limiting_workflow(self, test_client_e2e, test_user_e2e):
        """Test rate limiting behavior."""
        
        with patch('services.enhanced_rag_service.VectorStore') as mock_vector_store:
            mock_vector_store.return_value.similarity_search.return_value = [
                {
                    'content': 'Rate limit test content',
                    'metadata': {'source': 'test.pdf'},
                    'score': 0.9
                }
            ]
            
            # Send many requests quickly
            responses = []
            for i in range(20):  # Send 20 requests
                response = test_client_e2e.post(
                    "/api/chat/query",
                    json={
                        "query": f"Rate limit test query {i}",
                        "user_id": test_user_e2e.id,
                        "conversation_id": f"rate-limit-conv-{i}"
                    }
                )
                responses.append(response)
            
            # Check if rate limiting is applied
            status_codes = [r.status_code for r in responses]
            
            # Should have some successful requests
            assert 200 in status_codes
            
            # May have rate limit responses (429) if rate limiting is implemented
            if 429 in status_codes:
                print("Rate limiting is active")
            else:
                print("No rate limiting detected")


@pytest.mark.e2e
class TestUserJourneyWorkflows:
    """End-to-end tests for complete user journeys."""
    
    def test_new_user_onboarding_workflow(self, test_client_e2e):
        """Test complete new user onboarding workflow."""
        
        # Step 1: User registration (simulated)
        new_user_data = {
            "email": "newuser@test.com",
            "username": "newuser",
            "password": "testpassword"
        }
        
        # Note: Actual user registration endpoint would be implemented
        # For now, we'll simulate user creation
        
        # Step 2: First document upload
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"Welcome to AI Scholar! This is your first document.")
            temp_file.flush()
            
            with open(temp_file.name, 'rb') as f:
                with patch('services.document_processor.HierarchicalChunkingService'):
                    response = test_client_e2e.post(
                        "/api/documents/upload",
                        files={"file": ("welcome.txt", f, "text/plain")},
                        data={"user_id": "new-user-123"}
                    )
        
        # Should handle new user gracefully
        assert response.status_code in [200, 400, 404]  # Depending on user validation
        
        # Step 3: First query
        with patch('services.enhanced_rag_service.VectorStore') as mock_vector_store:
            mock_vector_store.return_value.similarity_search.return_value = [
                {
                    'content': 'Welcome information',
                    'metadata': {'source': 'welcome.txt'},
                    'score': 0.9
                }
            ]
            
            query_response = test_client_e2e.post(
                "/api/chat/query",
                json={
                    "query": "What is this document about?",
                    "user_id": "new-user-123",
                    "conversation_id": "onboarding-conv"
                }
            )
            
            # Should work for new user
            assert query_response.status_code in [200, 404]  # Depending on user validation

    def test_power_user_workflow(self, test_client_e2e, test_user_e2e, sample_pdf_content):
        """Test workflow for power users with advanced features."""
        
        with patch('services.document_processor.HierarchicalChunkingService') as mock_chunking, \
             patch('services.enhanced_rag_service.VectorStore') as mock_vector_store, \
             patch('services.knowledge_graph.KnowledgeGraphService') as mock_kg:
            
            # Setup mocks
            mock_chunking.return_value.chunk_document.return_value = [
                {'id': 'chunk-1', 'content': 'Advanced AI content', 'metadata': {}}
            ]
            
            mock_vector_store.return_value.similarity_search.return_value = [
                {
                    'content': 'Advanced AI information',
                    'metadata': {'source': 'advanced.pdf'},
                    'score': 0.95
                }
            ]
            
            mock_kg.return_value.query_graph.return_value = {
                'entities': [{'name': 'AI', 'type': 'concept'}],
                'relationships': []
            }
            
            # Upload multiple documents
            for i in range(3):
                with tempfile.NamedTemporaryFile(suffix=f'_advanced{i}.pdf', delete=False) as temp_file:
                    temp_file.write(sample_pdf_content)
                    temp_file.flush()
                    
                    with open(temp_file.name, 'rb') as f:
                        test_client_e2e.post(
                            "/api/documents/upload",
                            files={"file": (f"advanced{i}.pdf", f, "application/pdf")},
                            data={"user_id": test_user_e2e.id}
                        )
            
            # Advanced query with all features
            advanced_response = test_client_e2e.post(
                "/api/chat/query",
                json={
                    "query": "Provide a comprehensive analysis of AI trends",
                    "user_id": test_user_e2e.id,
                    "conversation_id": "power-user-conv",
                    "use_knowledge_graph": True,
                    "use_reasoning": True,
                    "personalize": True
                }
            )
            
            assert advanced_response.status_code == 200
            advanced_data = advanced_response.json()
            assert "response" in advanced_data
            
            # Get detailed analytics
            analytics_response = test_client_e2e.get(
                f"/api/analytics/user/{test_user_e2e.id}/detailed"
            )
            
            # Should provide detailed analytics for power user
            assert analytics_response.status_code in [200, 404]  # Depending on endpoint implementation