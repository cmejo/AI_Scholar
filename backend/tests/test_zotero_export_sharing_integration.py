"""
Integration Tests for Zotero Export and Sharing

This module provides comprehensive integration tests for the complete
export and sharing workflow including database operations.
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.core.database import Base
from backend.models.zotero_models import (
    ZoteroItem, ZoteroLibrary, ZoteroConnection,
    ZoteroSharedReference, ZoteroSharedCollection,
    ZoteroConversationExport, ZoteroCollectionReference
)
from backend.services.zotero.zotero_export_sharing_service import ZoteroExportSharingService


class TestZoteroExportSharingIntegration:
    """Integration tests for Zotero export and sharing functionality"""
    
    @pytest.fixture
    def db_engine(self):
        """Create in-memory SQLite database for testing"""
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        return engine
    
    @pytest.fixture
    def db_session(self, db_engine):
        """Create database session"""
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    @pytest.fixture
    def service(self, db_session):
        """Create service instance with real database"""
        return ZoteroExportSharingService(db_session)
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing"""
        return {
            "user_id": "user123",
            "target_user_id": "user456",
            "collaborator_id": "user789"
        }
    
    @pytest.fixture
    def sample_zotero_data(self, db_session, sample_user_data):
        """Create sample Zotero data in database"""
        # Create connection
        connection = ZoteroConnection(
            id=str(uuid.uuid4()),
            user_id=sample_user_data["user_id"],
            zotero_user_id="zotero123",
            access_token="token123",
            connection_status="active"
        )
        db_session.add(connection)
        
        # Create library
        library = ZoteroLibrary(
            id=str(uuid.uuid4()),
            connection_id=connection.id,
            zotero_library_id="lib123",
            library_type="user",
            library_name="Test Library"
        )
        db_session.add(library)
        
        # Create items
        item1 = ZoteroItem(
            id="item1",
            library_id=library.id,
            zotero_item_key="ITEM1",
            item_type="journalArticle",
            title="Test Paper 1",
            creators=[{"firstName": "John", "lastName": "Doe", "creatorType": "author"}],
            publication_year=2023,
            publication_title="Journal of Testing"
        )
        
        item2 = ZoteroItem(
            id="item2",
            library_id=library.id,
            zotero_item_key="ITEM2",
            item_type="book",
            title="Test Book",
            creators=[{"firstName": "Jane", "lastName": "Smith", "creatorType": "author"}],
            publication_year=2022,
            publisher="Test Publisher"
        )
        
        db_session.add_all([item1, item2])
        db_session.commit()
        
        return {
            "connection": connection,
            "library": library,
            "items": [item1, item2]
        }

    @pytest.mark.asyncio
    async def test_complete_conversation_export_workflow(self, service, db_session, sample_user_data, sample_zotero_data):
        """Test complete conversation export workflow"""
        # Setup conversation data with references
        conversation_data = {
            "title": "Research Discussion",
            "created_at": "2024-01-15T10:00:00Z",
            "messages": [
                {
                    "content": f"Let's discuss this paper zotero_ref:{sample_zotero_data['items'][0].id}",
                    "metadata": {
                        "referenced_items": [sample_zotero_data['items'][0].id]
                    }
                },
                {
                    "content": f"This book zotero_ref:{sample_zotero_data['items'][1].id} is also relevant",
                    "metadata": {}
                }
            ]
        }
        
        # Mock citation service
        service.citation_service.generate_citation = lambda item_id, style: f"Citation for {item_id}"
        
        # Execute export
        result = await service.export_conversation_with_citations(
            user_id=sample_user_data["user_id"],
            conversation_id="conv123",
            conversation_data=conversation_data,
            citation_style="apa"
        )
        
        # Verify result
        assert "export_id" in result
        assert result["conversation"]["title"] == "Research Discussion"
        assert result["citation_count"] == 2
        assert len(result["bibliography"]) == 2
        
        # Verify database record
        export_record = db_session.query(ZoteroConversationExport).filter(
            ZoteroConversationExport.id == result["export_id"]
        ).first()
        
        assert export_record is not None
        assert export_record.user_id == sample_user_data["user_id"]
        assert export_record.conversation_id == "conv123"
        assert export_record.citation_style == "apa"
        assert len(export_record.export_data["referenced_items"]) == 2

    @pytest.mark.asyncio
    async def test_complete_reference_sharing_workflow(self, service, db_session, sample_user_data, sample_zotero_data):
        """Test complete reference sharing workflow"""
        # Share reference
        share_result = await service.share_reference_with_user(
            owner_id=sample_user_data["user_id"],
            target_user_id=sample_user_data["target_user_id"],
            reference_id=sample_zotero_data["items"][0].id,
            permission_level="read",
            message="Check out this paper"
        )
        
        # Verify share result
        assert "share_id" in share_result
        assert share_result["reference_id"] == sample_zotero_data["items"][0].id
        assert share_result["shared_with"] == sample_user_data["target_user_id"]
        assert share_result["permission_level"] == "read"
        
        # Verify database record
        share_record = db_session.query(ZoteroSharedReference).filter(
            ZoteroSharedReference.id == share_result["share_id"]
        ).first()
        
        assert share_record is not None
        assert share_record.owner_user_id == sample_user_data["user_id"]
        assert share_record.shared_with_user_id == sample_user_data["target_user_id"]
        assert share_record.is_active == True
        
        # Test getting shared references
        shared_refs = await service.get_shared_references(sample_user_data["user_id"])
        
        assert len(shared_refs["shared_by_me"]) == 1
        assert shared_refs["shared_by_me"][0]["reference"]["title"] == "Test Paper 1"
        
        # Test updating share permission
        updated_share = await service.share_reference_with_user(
            owner_id=sample_user_data["user_id"],
            target_user_id=sample_user_data["target_user_id"],
            reference_id=sample_zotero_data["items"][0].id,
            permission_level="edit",
            message="Updated message"
        )
        
        # Verify update
        db_session.refresh(share_record)
        assert share_record.permission_level == "edit"
        assert share_record.message == "Updated message"

    @pytest.mark.asyncio
    async def test_complete_research_project_workflow(self, service, db_session, sample_user_data, sample_zotero_data):
        """Test complete research project collection workflow"""
        # Create research project
        project_result = await service.create_research_project_collection(
            user_id=sample_user_data["user_id"],
            project_name="My Research Project",
            description="A collaborative research project",
            reference_ids=[item.id for item in sample_zotero_data["items"]],
            collaborator_ids=[sample_user_data["collaborator_id"]]
        )
        
        # Verify project result
        assert "collection_id" in project_result
        assert project_result["name"] == "My Research Project"
        assert project_result["reference_count"] == 2
        assert project_result["collaborator_count"] == 1
        
        # Verify database record
        collection_record = db_session.query(ZoteroSharedCollection).filter(
            ZoteroSharedCollection.id == project_result["collection_id"]
        ).first()
        
        assert collection_record is not None
        assert collection_record.owner_user_id == sample_user_data["user_id"]
        assert collection_record.collection_type == "research_project"
        assert collection_record.metadata["reference_ids"] == [item.id for item in sample_zotero_data["items"]]
        
        # Test getting collections
        collections = await service.get_research_project_collections(sample_user_data["user_id"])
        
        assert len(collections) == 1
        assert collections[0]["name"] == "My Research Project"
        assert collections[0]["is_owner"] == True

    @pytest.mark.asyncio
    async def test_cross_user_sharing_workflow(self, service, db_session, sample_user_data, sample_zotero_data):
        """Test sharing workflow between multiple users"""
        # User 1 shares with User 2
        share1 = await service.share_reference_with_user(
            owner_id=sample_user_data["user_id"],
            target_user_id=sample_user_data["target_user_id"],
            reference_id=sample_zotero_data["items"][0].id,
            permission_level="read"
        )
        
        # User 1 shares with User 3
        share2 = await service.share_reference_with_user(
            owner_id=sample_user_data["user_id"],
            target_user_id=sample_user_data["collaborator_id"],
            reference_id=sample_zotero_data["items"][1].id,
            permission_level="edit"
        )
        
        # Check User 1's shared references
        user1_shares = await service.get_shared_references(sample_user_data["user_id"])
        assert len(user1_shares["shared_by_me"]) == 2
        assert len(user1_shares["shared_with_me"]) == 0
        
        # Check User 2's received references
        user2_shares = await service.get_shared_references(sample_user_data["target_user_id"])
        assert len(user2_shares["shared_by_me"]) == 0
        assert len(user2_shares["shared_with_me"]) == 1
        assert user2_shares["shared_with_me"][0]["reference"]["title"] == "Test Paper 1"
        
        # Check User 3's received references
        user3_shares = await service.get_shared_references(sample_user_data["collaborator_id"])
        assert len(user3_shares["shared_by_me"]) == 0
        assert len(user3_shares["shared_with_me"]) == 1
        assert user3_shares["shared_with_me"][0]["reference"]["title"] == "Test Book"

    @pytest.mark.asyncio
    async def test_conversation_export_with_multiple_citation_styles(self, service, db_session, sample_user_data, sample_zotero_data):
        """Test conversation export with different citation styles"""
        conversation_data = {
            "title": "Multi-style Test",
            "messages": [
                {
                    "content": f"Reference: zotero_ref:{sample_zotero_data['items'][0].id}",
                    "metadata": {"referenced_items": [sample_zotero_data['items'][0].id]}
                }
            ]
        }
        
        # Mock different citation styles
        def mock_citation_generator(item_id, style):
            style_formats = {
                "apa": f"Doe, J. (2023). Citation for {item_id}. APA Style.",
                "mla": f"Doe, John. Citation for {item_id}. MLA Style, 2023.",
                "chicago": f"Doe, John. Citation for {item_id}. Chicago Style, 2023."
            }
            return style_formats.get(style, f"Citation for {item_id}")
        
        service.citation_service.generate_citation = mock_citation_generator
        
        # Test different citation styles
        for style in ["apa", "mla", "chicago"]:
            result = await service.export_conversation_with_citations(
                user_id=sample_user_data["user_id"],
                conversation_id=f"conv_{style}",
                conversation_data=conversation_data,
                citation_style=style
            )
            
            assert result["citation_count"] == 1
            assert style.upper() in result["bibliography"][0]
            
            # Verify database record has correct style
            export_record = db_session.query(ZoteroConversationExport).filter(
                ZoteroConversationExport.id == result["export_id"]
            ).first()
            assert export_record.citation_style == style

    @pytest.mark.asyncio
    async def test_error_handling_and_rollback(self, service, db_session, sample_user_data):
        """Test error handling and database rollback"""
        # Test sharing non-existent reference
        with pytest.raises(ValueError, match="Reference not found"):
            await service.share_reference_with_user(
                owner_id=sample_user_data["user_id"],
                target_user_id=sample_user_data["target_user_id"],
                reference_id="nonexistent",
                permission_level="read"
            )
        
        # Verify no share record was created
        share_count = db_session.query(ZoteroSharedReference).count()
        assert share_count == 0
        
        # Test export with invalid conversation data
        with pytest.raises(Exception):
            await service.export_conversation_with_citations(
                user_id=sample_user_data["user_id"],
                conversation_id="conv123",
                conversation_data=None,  # Invalid data
                citation_style="apa"
            )
        
        # Verify no export record was created
        export_count = db_session.query(ZoteroConversationExport).count()
        assert export_count == 0

    @pytest.mark.asyncio
    async def test_large_scale_operations(self, service, db_session, sample_user_data, sample_zotero_data):
        """Test operations with larger datasets"""
        # Create additional items
        additional_items = []
        for i in range(10):
            item = ZoteroItem(
                id=f"item_{i+3}",
                library_id=sample_zotero_data["library"].id,
                zotero_item_key=f"ITEM{i+3}",
                item_type="journalArticle",
                title=f"Test Paper {i+3}",
                creators=[{"firstName": f"Author{i}", "lastName": f"Name{i}", "creatorType": "author"}],
                publication_year=2020 + i
            )
            additional_items.append(item)
        
        db_session.add_all(additional_items)
        db_session.commit()
        
        # Create conversation with many references
        all_items = sample_zotero_data["items"] + additional_items
        conversation_data = {
            "title": "Large Conversation",
            "messages": [
                {
                    "content": f"Reference {i}: zotero_ref:{item.id}",
                    "metadata": {"referenced_items": [item.id]}
                }
                for i, item in enumerate(all_items)
            ]
        }
        
        # Mock citation service for all items
        service.citation_service.generate_citation = lambda item_id, style: f"Citation for {item_id}"
        
        # Export conversation
        result = await service.export_conversation_with_citations(
            user_id=sample_user_data["user_id"],
            conversation_id="large_conv",
            conversation_data=conversation_data,
            citation_style="apa"
        )
        
        # Verify all references were processed
        assert result["citation_count"] == len(all_items)
        assert len(result["bibliography"]) == len(all_items)
        
        # Create research project with many references
        project_result = await service.create_research_project_collection(
            user_id=sample_user_data["user_id"],
            project_name="Large Project",
            reference_ids=[item.id for item in all_items]
        )
        
        assert project_result["reference_count"] == len(all_items)

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, service, db_session, sample_user_data, sample_zotero_data):
        """Test concurrent sharing operations"""
        import asyncio
        
        # Create multiple sharing tasks
        sharing_tasks = []
        for i in range(5):
            task = service.share_reference_with_user(
                owner_id=sample_user_data["user_id"],
                target_user_id=f"user{i+100}",
                reference_id=sample_zotero_data["items"][0].id,
                permission_level="read",
                message=f"Share {i}"
            )
            sharing_tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*sharing_tasks)
        
        # Verify all shares were created
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result["shared_with"] == f"user{i+100}"
        
        # Verify database consistency
        share_count = db_session.query(ZoteroSharedReference).filter(
            ZoteroSharedReference.reference_id == sample_zotero_data["items"][0].id
        ).count()
        assert share_count == 5


if __name__ == "__main__":
    pytest.main([__file__])