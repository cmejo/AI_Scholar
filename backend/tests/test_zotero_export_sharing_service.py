"""
Tests for Zotero Export and Sharing Service

This module tests conversation export with citations,
reference sharing between users, and research project collections.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from backend.services.zotero.zotero_export_sharing_service import ZoteroExportSharingService
from backend.models.zotero_models import (
    ZoteroItem, ZoteroSharedReference, ZoteroSharedCollection,
    ZoteroConversationExport, ZoteroCollectionReference
)


class TestZoteroExportSharingService:
    """Test cases for ZoteroExportSharingService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mocked dependencies"""
        with patch('backend.services.zotero.zotero_export_sharing_service.ZoteroCitationService'):
            return ZoteroExportSharingService(mock_db)
    
    @pytest.fixture
    def sample_conversation_data(self):
        """Sample conversation data for testing"""
        return {
            "title": "Research Discussion",
            "created_at": "2024-01-15T10:00:00Z",
            "messages": [
                {
                    "content": "Let's discuss this paper zotero_ref:123e4567-e89b-12d3-a456-426614174000",
                    "metadata": {
                        "referenced_items": ["123e4567-e89b-12d3-a456-426614174000"]
                    }
                },
                {
                    "content": "This relates to zotero_ref:987fcdeb-51a2-43d1-b789-123456789abc as well",
                    "metadata": {}
                }
            ]
        }
    
    @pytest.fixture
    def sample_zotero_item(self):
        """Sample Zotero item for testing"""
        return ZoteroItem(
            id="123e4567-e89b-12d3-a456-426614174000",
            user_id="user123",
            library_id="lib123",
            zotero_item_key="ABCD1234",
            item_type="journalArticle",
            title="Sample Research Paper",
            creators=[{"firstName": "John", "lastName": "Doe", "creatorType": "author"}],
            publication_year=2023,
            publication_title="Journal of Research"
        )

    @pytest.mark.asyncio
    async def test_export_conversation_with_citations_success(self, service, mock_db, sample_conversation_data, sample_zotero_item):
        """Test successful conversation export with citations"""
        # Setup
        user_id = "user123"
        conversation_id = "conv123"
        citation_style = "apa"
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.return_value = sample_zotero_item
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.flush = Mock()
        
        # Mock citation service
        service.citation_service.generate_citation = AsyncMock(return_value="Doe, J. (2023). Sample Research Paper. Journal of Research.")
        
        # Execute
        result = await service.export_conversation_with_citations(
            user_id=user_id,
            conversation_id=conversation_id,
            conversation_data=sample_conversation_data,
            citation_style=citation_style
        )
        
        # Verify
        assert "export_id" in result
        assert result["conversation"]["title"] == "Research Discussion"
        assert len(result["bibliography"]) > 0
        assert result["citation_count"] > 0
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_conversation_with_no_references(self, service, mock_db):
        """Test conversation export with no referenced items"""
        # Setup
        conversation_data = {
            "title": "Simple Discussion",
            "messages": [
                {"content": "This is a simple message without references"}
            ]
        }
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        # Execute
        result = await service.export_conversation_with_citations(
            user_id="user123",
            conversation_id="conv123",
            conversation_data=conversation_data
        )
        
        # Verify
        assert result["citation_count"] == 0
        assert len(result["bibliography"]) == 0

    @pytest.mark.asyncio
    async def test_share_reference_with_user_success(self, service, mock_db, sample_zotero_item):
        """Test successful reference sharing"""
        # Setup
        owner_id = "user123"
        target_user_id = "user456"
        reference_id = "ref123"
        permission_level = "read"
        message = "Check out this paper"
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_zotero_item,  # Reference exists
            None  # No existing share
        ]
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        # Execute
        result = await service.share_reference_with_user(
            owner_id=owner_id,
            target_user_id=target_user_id,
            reference_id=reference_id,
            permission_level=permission_level,
            message=message
        )
        
        # Verify
        assert "share_id" in result
        assert result["reference_id"] == reference_id
        assert result["shared_with"] == target_user_id
        assert result["permission_level"] == permission_level
        assert result["message"] == message
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_share_reference_not_found(self, service, mock_db):
        """Test sharing non-existent reference"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Reference not found"):
            await service.share_reference_with_user(
                owner_id="user123",
                target_user_id="user456",
                reference_id="nonexistent",
                permission_level="read"
            )

    @pytest.mark.asyncio
    async def test_share_reference_update_existing(self, service, mock_db, sample_zotero_item):
        """Test updating existing reference share"""
        # Setup
        existing_share = Mock()
        existing_share.permission_level = "read"
        existing_share.message = "Old message"
        existing_share.updated_at = datetime.utcnow()
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_zotero_item,  # Reference exists
            existing_share  # Existing share
        ]
        mock_db.commit = Mock()
        
        # Execute
        result = await service.share_reference_with_user(
            owner_id="user123",
            target_user_id="user456",
            reference_id="ref123",
            permission_level="edit",
            message="Updated message"
        )
        
        # Verify
        assert existing_share.permission_level == "edit"
        assert existing_share.message == "Updated message"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_research_project_collection_success(self, service, mock_db):
        """Test successful research project collection creation"""
        # Setup
        user_id = "user123"
        project_name = "My Research Project"
        description = "A collaborative research project"
        reference_ids = ["ref1", "ref2"]
        collaborator_ids = ["user456", "user789"]
        
        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_db.commit = Mock()
        
        # Mock the collection object
        mock_collection = Mock()
        mock_collection.id = "collection123"
        mock_collection.created_at = datetime.utcnow()
        
        # Execute
        result = await service.create_research_project_collection(
            user_id=user_id,
            project_name=project_name,
            description=description,
            reference_ids=reference_ids,
            collaborator_ids=collaborator_ids
        )
        
        # Verify
        assert "collection_id" in result
        assert result["name"] == project_name
        assert result["description"] == description
        assert result["owner_id"] == user_id
        assert result["reference_count"] == len(reference_ids)
        assert result["collaborator_count"] == len(collaborator_ids)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_shared_references_success(self, service, mock_db):
        """Test getting shared references"""
        # Setup
        user_id = "user123"
        
        # Mock shared references
        shared_by_me = [Mock()]
        shared_by_me[0].id = "share1"
        shared_by_me[0].reference_id = "ref1"
        shared_by_me[0].shared_with_user_id = "user456"
        shared_by_me[0].permission_level = "read"
        shared_by_me[0].created_at = datetime.utcnow()
        
        shared_with_me = [Mock()]
        shared_with_me[0].id = "share2"
        shared_with_me[0].reference_id = "ref2"
        shared_with_me[0].owner_user_id = "user789"
        shared_with_me[0].permission_level = "edit"
        shared_with_me[0].message = "Check this out"
        shared_with_me[0].created_at = datetime.utcnow()
        
        # Mock reference objects
        mock_ref1 = Mock()
        mock_ref1.id = "ref1"
        mock_ref1.title = "Paper 1"
        mock_ref1.creators = [{"firstName": "John", "lastName": "Doe"}]
        mock_ref1.publication_year = 2023
        
        mock_ref2 = Mock()
        mock_ref2.id = "ref2"
        mock_ref2.title = "Paper 2"
        mock_ref2.creators = [{"firstName": "Jane", "lastName": "Smith"}]
        mock_ref2.publication_year = 2022
        
        # Setup query mocks
        def mock_query_side_effect(model):
            if model == ZoteroSharedReference:
                mock_query = Mock()
                mock_query.filter.return_value.all.side_effect = [shared_by_me, shared_with_me]
                return mock_query
            elif model == ZoteroItem:
                mock_query = Mock()
                mock_query.filter.return_value.first.side_effect = [mock_ref1, mock_ref2]
                return mock_query
        
        mock_db.query.side_effect = mock_query_side_effect
        
        # Execute
        result = await service.get_shared_references(user_id)
        
        # Verify
        assert "shared_by_me" in result
        assert "shared_with_me" in result
        assert len(result["shared_by_me"]) == 1
        assert len(result["shared_with_me"]) == 1
        assert result["shared_by_me"][0]["reference"]["title"] == "Paper 1"
        assert result["shared_with_me"][0]["reference"]["title"] == "Paper 2"

    @pytest.mark.asyncio
    async def test_get_research_project_collections_success(self, service, mock_db):
        """Test getting research project collections"""
        # Setup
        user_id = "user123"
        
        mock_collection = Mock()
        mock_collection.id = "collection123"
        mock_collection.name = "My Project"
        mock_collection.description = "Test project"
        mock_collection.owner_user_id = user_id
        mock_collection.references = []
        mock_collection.collaborators = []
        mock_collection.created_at = datetime.utcnow()
        mock_collection.updated_at = datetime.utcnow()
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_collection]
        
        # Execute
        result = await service.get_research_project_collections(user_id)
        
        # Verify
        assert len(result) == 1
        assert result[0]["collection_id"] == "collection123"
        assert result[0]["name"] == "My Project"
        assert result[0]["is_owner"] == True

    @pytest.mark.asyncio
    async def test_extract_referenced_items(self, service):
        """Test extracting referenced items from conversation"""
        # Setup
        conversation_data = {
            "messages": [
                {
                    "content": "Check out zotero_ref:123e4567-e89b-12d3-a456-426614174000",
                    "metadata": {
                        "referenced_items": ["987fcdeb-51a2-43d1-b789-123456789abc"]
                    }
                },
                {
                    "content": "Also see zotero_ref:456e7890-e12b-34c5-d678-901234567def"
                }
            ]
        }
        
        # Execute
        result = await service._extract_referenced_items("user123", conversation_data)
        
        # Verify
        assert len(result) == 3
        assert "123e4567-e89b-12d3-a456-426614174000" in result
        assert "987fcdeb-51a2-43d1-b789-123456789abc" in result
        assert "456e7890-e12b-34c5-d678-901234567def" in result

    @pytest.mark.asyncio
    async def test_process_messages_with_citations(self, service):
        """Test processing messages with citations"""
        # Setup
        messages = [
            {
                "content": "This paper zotero_ref:123 is interesting",
                "role": "user"
            },
            {
                "content": "I agree about zotero_ref:456",
                "role": "assistant"
            }
        ]
        
        citations = {
            "123": "Doe, J. (2023). Paper 1.",
            "456": "Smith, J. (2022). Paper 2."
        }
        
        # Execute
        result = await service._process_messages_with_citations(messages, citations)
        
        # Verify
        assert len(result) == 2
        assert "This paper (Doe, J. (2023). Paper 1.) is interesting" in result[0]["content"]
        assert "I agree about (Smith, J. (2022). Paper 2.)" in result[1]["content"]

    @pytest.mark.asyncio
    async def test_export_conversation_database_error(self, service, mock_db):
        """Test handling database errors during export"""
        # Setup
        mock_db.add.side_effect = Exception("Database error")
        mock_db.rollback = Mock()
        
        conversation_data = {"messages": [{"content": "test"}]}
        
        # Execute & Verify
        with pytest.raises(Exception, match="Failed to export conversation"):
            await service.export_conversation_with_citations(
                user_id="user123",
                conversation_id="conv123",
                conversation_data=conversation_data
            )
        
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_share_reference_database_error(self, service, mock_db, sample_zotero_item):
        """Test handling database errors during sharing"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_zotero_item,  # Reference exists
            None  # No existing share
        ]
        mock_db.add.side_effect = Exception("Database error")
        mock_db.rollback = Mock()
        
        # Execute & Verify
        with pytest.raises(Exception, match="Failed to share reference"):
            await service.share_reference_with_user(
                owner_id="user123",
                target_user_id="user456",
                reference_id="ref123",
                permission_level="read"
            )
        
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_collection_database_error(self, service, mock_db):
        """Test handling database errors during collection creation"""
        # Setup
        mock_db.add.side_effect = Exception("Database error")
        mock_db.rollback = Mock()
        
        # Execute & Verify
        with pytest.raises(Exception, match="Failed to create research project"):
            await service.create_research_project_collection(
                user_id="user123",
                project_name="Test Project"
            )
        
        mock_db.rollback.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])