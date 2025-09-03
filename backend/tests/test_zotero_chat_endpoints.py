"""
Tests for Zotero Chat Integration API Endpoints

Tests the REST API endpoints for integrating Zotero references with chat functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from ..api.zotero_chat_endpoints import router
from ..models.schemas import User


# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestZoteroChatEndpoints:
    """Test suite for Zotero Chat Integration API endpoints"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_user = User(
            id="test-user-123",
            email="test@example.com",
            username="testuser"
        )
        
        self.sample_references = [
            {
                'id': 'item-123',
                'title': 'Machine Learning in Healthcare',
                'creators': ['John Smith', 'Jane Doe'],
                'year': 2023,
                'publicationTitle': 'Journal of Medical AI',
                'relevance': 0.9,
                'citationKey': 'Smith2023'
            }
        ]
    
    @patch('backend.api.zotero_chat_endpoints.get_current_user')
    @patch('backend.api.zotero_chat_endpoints.get_db')
    @patch('backend.api.zotero_chat_endpoints.zotero_chat_service')
    def test_process_chat_message(self, mock_service, mock_db, mock_user):
        """Test processing chat message with reference context"""
        mock_user.return_value = self.mock_user
        mock_db.return_value = Mock()
        
        # Mock service response
        mock_service.inject_reference_context = AsyncMock(return_value=(
            "Enhanced content with context",
            self.sample_references
        ))
        
        request_data = {
            "content": "Tell me about @[Machine Learning in Healthcare]",
            "includeZoteroContext": True,
            "contextType": "research"
        }
        
        response = client.post("/api/zotero/chat/process-message", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['content'] == request_data['content']
        assert data['enhancedContent'] == "Enhanced content with context"
        assert len(data['references']) == 1
        assert data['references'][0]['title'] == 'Machine Learning in Healthcare'
    
    @patch('backend.api.zotero_chat_endpoints.get_current_user')
    @patch('backend.api.zotero_chat_endpoints.get_db')
    @patch('backend.api.zotero_chat_endpoints.zotero_chat_service')
    def test_extract_reference_mentions(self, mock_service, mock_db, mock_user):
        """Test extracting reference mentions from content"""
        mock_user.return_value = self.mock_user
        mock_db.return_value = Mock()
        
        # Mock service responses
        mock_service.extract_reference_mentions.return_value = ["Machine Learning in Healthcare"]
        mock_service.find_referenced_items = AsyncMock(return_value=[])
        mock_service.convert_to_chat_references.return_value = self.sample_references
        
        request_data = {
            "content": "I want to discuss @[Machine Learning in Healthcare]"
        }
        
        response = client.post("/api/zotero/chat/extract-mentions", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['mentions'] == ["Machine Learning in Healthcare"]
        assert len(data['references']) == 1
    
    @patch('backend.api.zotero_chat_endpoints.get_current_user')
    @patch('backend.api.zotero_chat_endpoints.get_db')
    @patch('backend.api.zotero_chat_endpoints.zotero_chat_service')
    def test_get_relevant_references(self, mock_service, mock_db, mock_user):
        """Test getting relevant references for a topic"""
        mock_user.return_value = self.mock_user
        mock_db.return_value = Mock()
        
        mock_service.get_relevant_references = AsyncMock(return_value=self.sample_references)
        
        request_data = {
            "topic": "machine learning",
            "limit": 5
        }
        
        response = client.post("/api/zotero/chat/relevant-references", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['references']) == 1
        assert data['references'][0]['title'] == 'Machine Learning in Healthcare'
    
    @patch('backend.api.zotero_chat_endpoints.get_current_user')
    @patch('backend.api.zotero_chat_endpoints.get_db')
    @patch('backend.api.zotero_chat_endpoints.zotero_chat_service')
    def test_create_research_summary(self, mock_service, mock_db, mock_user):
        """Test creating research summary with references"""
        mock_user.return_value = self.mock_user
        mock_db.return_value = Mock()
        
        mock_service.create_research_summary = AsyncMock(return_value={
            'summary': 'Research Summary: Machine Learning\nBased on 1 references...',
            'references': self.sample_references
        })
        
        request_data = {
            "topic": "machine learning",
            "referenceIds": ["item-123"]
        }
        
        response = client.post("/api/zotero/chat/research-summary", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "Research Summary: Machine Learning" in data['summary']
        assert len(data['references']) == 1
    
    @patch('backend.api.zotero_chat_endpoints.get_current_user')
    @patch('backend.api.zotero_chat_endpoints.get_db')
    @patch('backend.api.zotero_chat_endpoints.zotero_chat_service')
    def test_export_conversation_with_citations(self, mock_service, mock_db, mock_user):
        """Test exporting conversation with proper citations"""
        mock_user.return_value = self.mock_user
        mock_db.return_value = Mock()
        
        mock_service.export_conversation_with_citations = AsyncMock(
            return_value="# AI Scholar Conversation Export\n\n## User\nHello\n\n## References\nSmith, J. (2023)..."
        )
        
        request_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2023-12-01T10:00:00",
                    "references": self.sample_references
                }
            ],
            "citationStyle": "apa"
        }
        
        response = client.post("/api/zotero/chat/export-conversation", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "# AI Scholar Conversation Export" in data['exportContent']
        assert data['format'] == 'markdown'
    
    @patch('backend.api.zotero_chat_endpoints.get_current_user')
    @patch('backend.api.zotero_chat_endpoints.zotero_chat_service')
    def test_process_ai_response(self, mock_service, mock_user):
        """Test processing AI response to add reference links"""
        mock_user.return_value = self.mock_user
        
        mock_service.process_ai_response.return_value = (
            "According to [@Machine Learning in Healthcare](zotero:item-123), AI shows promise."
        )
        
        request_data = {
            "response": "According to Smith2023, AI shows promise.",
            "references": self.sample_references
        }
        
        response = client.post("/api/zotero/chat/process-ai-response", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "[@Machine Learning in Healthcare](zotero:item-123)" in data['processedResponse']
    
    @patch('backend.api.zotero_chat_endpoints.get_current_user')
    @patch('backend.api.zotero_chat_endpoints.get_db')
    @patch('backend.api.zotero_chat_endpoints.zotero_chat_service')
    def test_generate_citations_for_references(self, mock_service, mock_db, mock_user):
        """Test generating citations for referenced items"""
        mock_user.return_value = self.mock_user
        mock_db.return_value = Mock()
        
        mock_service.generate_citations_for_references = AsyncMock(return_value=[
            "Smith, J., & Doe, J. (2023). Machine Learning in Healthcare. Journal of Medical AI."
        ])
        
        request_data = {
            "references": self.sample_references,
            "style": "apa"
        }
        
        response = client.post("/api/zotero/chat/generate-citations", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['citations']) == 1
        assert "Smith, J., & Doe, J. (2023)" in data['citations'][0]
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/api/zotero/chat/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'zotero-chat-integration'


class TestZoteroChatEndpointsErrorHandling:
    """Test error handling in chat integration endpoints"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_user = User(
            id="test-user-123",
            email="test@example.com",
            username="testuser"
        )
    
    @patch('backend.api.zotero_chat_endpoints.get_current_user')
    @patch('backend.api.zotero_chat_endpoints.get_db')
    @patch('backend.api.zotero_chat_endpoints.zotero_chat_service')
    def test_process_message_service_error(self, mock_service, mock_db, mock_user):
        """Test handling of service errors in process message"""
        mock_user.return_value = self.mock_user
        mock_db.return_value = Mock()
        
        mock_service.inject_reference_context = AsyncMock(
            side_effect=Exception("Service error")
        )
        
        request_data = {
            "content": "Test message",
            "includeZoteroContext": True
        }
        
        response = client.post("/api/zotero/chat/process-message", json=request_data)
        
        assert response.status_code == 500
        assert "Failed to process chat message" in response.json()['detail']
    
    @patch('backend.api.zotero_chat_endpoints.get_current_user')
    @patch('backend.api.zotero_chat_endpoints.get_db')
    @patch('backend.api.zotero_chat_endpoints.zotero_chat_service')
    def test_extract_mentions_service_error(self, mock_service, mock_db, mock_user):
        """Test handling of service errors in extract mentions"""
        mock_user.return_value = self.mock_user
        mock_db.return_value = Mock()
        
        mock_service.extract_reference_mentions.side_effect = Exception("Service error")
        
        request_data = {
            "content": "Test content with @[mention]"
        }
        
        response = client.post("/api/zotero/chat/extract-mentions", json=request_data)
        
        assert response.status_code == 500
        assert "Failed to extract mentions" in response.json()['detail']
    
    @patch('backend.api.zotero_chat_endpoints.get_current_user')
    @patch('backend.api.zotero_chat_endpoints.get_db')
    @patch('backend.api.zotero_chat_endpoints.zotero_chat_service')
    def test_get_relevant_references_service_error(self, mock_service, mock_db, mock_user):
        """Test handling of service errors in get relevant references"""
        mock_user.return_value = self.mock_user
        mock_db.return_value = Mock()
        
        mock_service.get_relevant_references = AsyncMock(
            side_effect=Exception("Service error")
        )
        
        request_data = {
            "topic": "test topic"
        }
        
        response = client.post("/api/zotero/chat/relevant-references", json=request_data)
        
        assert response.status_code == 500
        assert "Failed to get relevant references" in response.json()['detail']
    
    @patch('backend.api.zotero_chat_endpoints.get_current_user')
    @patch('backend.api.zotero_chat_endpoints.get_db')
    @patch('backend.api.zotero_chat_endpoints.zotero_chat_service')
    def test_create_research_summary_service_error(self, mock_service, mock_db, mock_user):
        """Test handling of service errors in create research summary"""
        mock_user.return_value = self.mock_user
        mock_db.return_value = Mock()
        
        mock_service.create_research_summary = AsyncMock(
            side_effect=Exception("Service error")
        )
        
        request_data = {
            "topic": "test topic"
        }
        
        response = client.post("/api/zotero/chat/research-summary", json=request_data)
        
        assert response.status_code == 500
        assert "Failed to create research summary" in response.json()['detail']
    
    @patch('backend.api.zotero_chat_endpoints.get_current_user')
    @patch('backend.api.zotero_chat_endpoints.get_db')
    @patch('backend.api.zotero_chat_endpoints.zotero_chat_service')
    def test_export_conversation_service_error(self, mock_service, mock_db, mock_user):
        """Test handling of service errors in export conversation"""
        mock_user.return_value = self.mock_user
        mock_db.return_value = Mock()
        
        mock_service.export_conversation_with_citations = AsyncMock(
            side_effect=Exception("Service error")
        )
        
        request_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "Test message",
                    "timestamp": "2023-12-01T10:00:00"
                }
            ]
        }
        
        response = client.post("/api/zotero/chat/export-conversation", json=request_data)
        
        assert response.status_code == 500
        assert "Failed to export conversation" in response.json()['detail']
    
    def test_invalid_request_data(self):
        """Test handling of invalid request data"""
        # Missing required content field
        request_data = {
            "includeZoteroContext": True
        }
        
        response = client.post("/api/zotero/chat/process-message", json=request_data)
        
        assert response.status_code == 422  # Validation error


class TestZoteroChatEndpointsIntegration:
    """Integration tests for chat endpoints"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_user = User(
            id="test-user-123",
            email="test@example.com",
            username="testuser"
        )
    
    @patch('backend.api.zotero_chat_endpoints.get_current_user')
    @patch('backend.api.zotero_chat_endpoints.get_db')
    def test_full_chat_workflow(self, mock_db, mock_user):
        """Test complete chat workflow with references"""
        mock_user.return_value = self.mock_user
        mock_db.return_value = Mock()
        
        with patch('backend.api.zotero_chat_endpoints.zotero_chat_service') as mock_service:
            # Step 1: Process message with mentions
            mock_service.inject_reference_context = AsyncMock(return_value=(
                "Enhanced content",
                [{'id': 'item-123', 'title': 'Test Paper', 'creators': ['Author']}]
            ))
            
            message_response = client.post("/api/zotero/chat/process-message", json={
                "content": "Tell me about @[Test Paper]",
                "includeZoteroContext": True
            })
            
            assert message_response.status_code == 200
            
            # Step 2: Get relevant references
            mock_service.get_relevant_references = AsyncMock(return_value=[
                {'id': 'item-456', 'title': 'Related Paper', 'creators': ['Another Author']}
            ])
            
            refs_response = client.post("/api/zotero/chat/relevant-references", json={
                "topic": "machine learning"
            })
            
            assert refs_response.status_code == 200
            
            # Step 3: Export conversation
            mock_service.export_conversation_with_citations = AsyncMock(
                return_value="# Exported Conversation\n\n## References\n..."
            )
            
            export_response = client.post("/api/zotero/chat/export-conversation", json={
                "messages": [
                    {
                        "role": "user",
                        "content": "Test message",
                        "timestamp": "2023-12-01T10:00:00",
                        "references": [{'id': 'item-123', 'title': 'Test Paper'}]
                    }
                ]
            })
            
            assert export_response.status_code == 200
            assert "# Exported Conversation" in export_response.json()['exportContent']