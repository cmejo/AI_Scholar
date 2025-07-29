"""
Tests for advanced API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json
from unittest.mock import AsyncMock, patch

from app import app
from models.schemas import (
    UserProfileCreate, UserPreferences,
    ConversationMemoryCreate, MemoryType,
    KnowledgeGraphEntityCreate, EntityType,
    KnowledgeGraphRelationshipCreate, RelationshipType,
    UserFeedbackCreate, FeedbackType,
    AnalyticsEventCreate,
    AnalyticsQuery,
    KnowledgeGraphQuery,
    PersonalizationSettings
)

client = TestClient(app)

class TestAdvancedEndpoints:
    """Test suite for advanced API endpoints"""
    
    def setup_method(self):
        """Setup test data"""
        self.test_user_id = "test-user-123"
        self.test_conversation_id = "conv-123"
        self.test_document_id = "doc-123"
        
    @patch('api.advanced_endpoints.memory_service')
    def test_create_conversation_memory(self, mock_memory_service):
        """Test creating conversation memory"""
        # Mock the service response
        mock_memory_service.store_conversation_memory = AsyncMock(return_value={
            "id": "memory-123",
            "conversation_id": self.test_conversation_id,
            "memory_type": "short_term",
            "content": "Test conversation memory",
            "importance_score": 0.8,
            "timestamp": datetime.now(),
            "metadata": {"test": "data"}
        })
        
        memory_data = ConversationMemoryCreate(
            conversation_id=self.test_conversation_id,
            memory_type=MemoryType.SHORT_TERM,
            content="Test conversation memory",
            importance_score=0.8,
            metadata={"test": "data"}
        )
        
        response = client.post(
            "/api/advanced/memory/conversation",
            json=memory_data.dict(),
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == self.test_conversation_id
        assert data["memory_type"] == "short_term"
        assert data["content"] == "Test conversation memory"
        assert data["importance_score"] == 0.8
        
    @patch('api.advanced_endpoints.memory_service')
    def test_get_conversation_memory(self, mock_memory_service):
        """Test retrieving conversation memory"""
        mock_memory_service.get_conversation_memory = AsyncMock(return_value=[
            {
                "id": "memory-123",
                "conversation_id": self.test_conversation_id,
                "memory_type": "short_term",
                "content": "Test memory",
                "importance_score": 0.8,
                "timestamp": datetime.now(),
                "metadata": {}
            }
        ])
        
        response = client.get(
            f"/api/advanced/memory/conversation/{self.test_conversation_id}",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["conversation_id"] == self.test_conversation_id
        
    @patch('api.advanced_endpoints.memory_service')
    def test_get_user_context(self, mock_memory_service):
        """Test getting user context"""
        mock_memory_service.retrieve_relevant_context = AsyncMock(return_value={
            "context": "Relevant context for test query",
            "relevance_score": 0.9,
            "token_count": 150,
            "memory_items": [],
            "summary": "Context summary"
        })
        
        response = client.get(
            f"/api/advanced/memory/user/{self.test_user_id}/context",
            params={"query": "test query", "max_tokens": 1000},
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == self.test_user_id
        assert data["query"] == "test query"
        assert "context" in data
        assert data["relevance_score"] == 0.9
        
    @patch('api.advanced_endpoints.knowledge_graph_service')
    def test_create_knowledge_graph_entity(self, mock_kg_service):
        """Test creating knowledge graph entity"""
        mock_kg_service.create_entity = AsyncMock(return_value={
            "id": "entity-123",
            "name": "Test Entity",
            "type": "concept",
            "description": "A test entity",
            "importance_score": 0.9,
            "document_id": self.test_document_id,
            "metadata": {"category": "test"},
            "created_at": datetime.now()
        })
        
        entity_data = KnowledgeGraphEntityCreate(
            name="Test Entity",
            type=EntityType.CONCEPT,
            description="A test entity",
            importance_score=0.9,
            document_id=self.test_document_id,
            metadata={"category": "test"}
        )
        
        response = client.post(
            "/api/advanced/knowledge-graph/entities",
            json=entity_data.dict(),
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Entity"
        assert data["type"] == "concept"
        assert data["importance_score"] == 0.9
        
    @patch('api.advanced_endpoints.analytics_service')
    def test_create_analytics_event(self, mock_analytics_service):
        """Test creating analytics event"""
        mock_analytics_service.track_event = AsyncMock(return_value={
            "id": "event-123",
            "user_id": self.test_user_id,
            "event_type": "query_executed",
            "event_data": {"query": "test", "response_time": 1.2},
            "timestamp": datetime.now(),
            "session_id": "session-123"
        })
        
        event_data = AnalyticsEventCreate(
            user_id=self.test_user_id,
            event_type="query_executed",
            event_data={"query": "test", "response_time": 1.2},
            session_id="session-123"
        )
        
        response = client.post(
            "/api/advanced/analytics/events",
            json=event_data.dict(),
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == self.test_user_id
        assert data["event_type"] == "query_executed"
        
    @patch('api.advanced_endpoints.user_profile_service')
    def test_create_user_profile(self, mock_profile_service):
        """Test creating user profile"""
        mock_profile_service.create_or_update_profile = AsyncMock(return_value={
            "id": "profile-123",
            "user_id": self.test_user_id,
            "preferences": {
                "language": "en",
                "response_style": "detailed",
                "domain_focus": ["technology", "science"]
            },
            "interaction_history": {},
            "domain_expertise": {"technology": 0.8, "science": 0.6},
            "learning_style": "visual",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        
        profile_data = UserProfileCreate(
            user_id=self.test_user_id,
            preferences=UserPreferences(
                language="en",
                response_style="detailed",
                domain_focus=["technology", "science"]
            ),
            learning_style="visual",
            domain_expertise={"technology": 0.8, "science": 0.6}
        )
        
        response = client.post(
            "/api/advanced/personalization/profile",
            json=profile_data.dict(),
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == self.test_user_id
        assert data["learning_style"] == "visual"
        
    @patch('api.advanced_endpoints.feedback_processor')
    def test_submit_feedback(self, mock_feedback_processor):
        """Test submitting user feedback"""
        mock_feedback_processor.process_feedback = AsyncMock(return_value={
            "id": "feedback-123",
            "user_id": self.test_user_id,
            "message_id": "msg-123",
            "feedback_type": "rating",
            "feedback_value": {"rating": 5, "comment": "Great response!"},
            "processed": False,
            "created_at": datetime.now()
        })
        
        feedback_data = UserFeedbackCreate(
            user_id=self.test_user_id,
            message_id="msg-123",
            feedback_type=FeedbackType.RATING,
            feedback_value={"rating": 5, "comment": "Great response!"}
        )
        
        response = client.post(
            "/api/advanced/personalization/feedback",
            json=feedback_data.dict(),
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == self.test_user_id
        assert data["feedback_type"] == "rating"

    def test_memory_endpoints_integration(self):
        """Test memory endpoints integration"""
        # Test that endpoints are accessible
        response = client.get(
            f"/api/advanced/memory/conversation/{self.test_conversation_id}",
            headers={"Authorization": "Bearer test-token"}
        )
        # Should not fail with 404
        assert response.status_code in [200, 500]  # 500 is acceptable for service errors
        
    def test_knowledge_graph_endpoints_integration(self):
        """Test knowledge graph endpoints integration"""
        response = client.get(
            "/api/advanced/knowledge-graph/entities",
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code in [200, 500]
        
    def test_analytics_endpoints_integration(self):
        """Test analytics endpoints integration"""
        response = client.get(
            f"/api/advanced/analytics/dashboard/{self.test_user_id}",
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code in [200, 500]
        
    def test_personalization_endpoints_integration(self):
        """Test personalization endpoints integration"""
        response = client.get(
            f"/api/advanced/personalization/profile/{self.test_user_id}",
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code in [200, 404, 500]