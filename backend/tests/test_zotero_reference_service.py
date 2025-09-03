"""
Unit tests for Zotero Reference Service

Tests CRUD operations, validation, and data integrity checks
for the Zotero reference management system.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from models.zotero_models import (
    ZoteroItem, ZoteroLibrary, ZoteroCollection, ZoteroItemCollection,
    ZoteroConnection
)
from models.zotero_schemas import (
    ZoteroItemCreate, ZoteroItemUpdate, ZoteroCreator
)
from services.zotero.zotero_reference_service import ZoteroReferenceService


class TestZoteroReferenceService:
    """Test suite for ZoteroReferenceService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def reference_service(self, mock_db):
        """Reference service instance with mocked database"""
        return ZoteroReferenceService(mock_db)
    
    @pytest.fixture
    def sample_creator(self):
        """Sample creator data"""
        return ZoteroCreator(
            creator_type="author",
            first_name="John",
            last_name="Doe"
        )
    
    @pytest.fixture
    def sample_reference_data(self, sample_creator):
        """Sample reference creation data"""
        return ZoteroItemCreate(
            item_type="article",
            title="Test Article",
            creators=[sample_creator],
            publication_title="Test Journal",
            publication_year=2023,
            doi="10.1000/test.doi",
            abstract_note="Test abstract",
            tags=["test", "research"],
            collection_ids=[]
        )
    
    @pytest.fixture
    def sample_library(self):
        """Sample library model"""
        return ZoteroLibrary(
            id="lib-123",
            connection_id="conn-123",
            zotero_library_id="zotero-lib-123",
            library_type="user",
            library_name="Test Library",
            is_active=True
        )
    
    @pytest.fixture
    def sample_connection(self):
        """Sample connection model"""
        return ZoteroConnection(
            id="conn-123",
            user_id="user-123",
            zotero_user_id="zotero-user-123",
            connection_status="active"
        )
    
    @pytest.fixture
    def sample_reference(self):
        """Sample reference model"""
        return ZoteroItem(
            id="ref-123",
            library_id="lib-123",
            zotero_item_key="item-key-123",
            item_type="article",
            title="Test Article",
            creators=[{
                "creator_type": "author",
                "first_name": "John",
                "last_name": "Doe"
            }],
            publication_title="Test Journal",
            publication_year=2023,
            doi="10.1000/test.doi",
            abstract_note="Test abstract",
            tags=["test", "research"],
            is_deleted=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    # CRUD Operation Tests
    
    @pytest.mark.asyncio
    async def test_create_reference_success(
        self, reference_service, mock_db, sample_reference_data, sample_library, sample_connection
    ):
        """Test successful reference creation"""
        # Mock database queries
        mock_db.query.return_value.join.return_value.filter.return_value.first.return_value = sample_library
        mock_db.flush = Mock()
        mock_db.commit = Mock()
        
        # Mock the created reference
        created_ref = ZoteroItem(
            id="ref-123",
            library_id="lib-123",
            item_type=sample_reference_data.item_type,
            title=sample_reference_data.title
        )
        mock_db.add = Mock()
        
        # Mock the get_reference method
        with patch.object(reference_service, 'get_reference', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = Mock(id="ref-123", title="Test Article")
            
            # Mock validation methods
            with patch.object(reference_service, '_validate_library_access', new_callable=AsyncMock) as mock_validate_lib:
                mock_validate_lib.return_value = sample_library
                
                with patch.object(reference_service, '_validate_reference_data', new_callable=AsyncMock):
                    with patch.object(reference_service, '_update_metadata_index', new_callable=AsyncMock):
                        result = await reference_service.create_reference(
                            user_id="user-123",
                            library_id="lib-123",
                            reference_data=sample_reference_data
                        )
                        
                        assert result is not None
                        assert result.id == "ref-123"
                        mock_db.add.assert_called_once()
                        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_reference_validation_error(
        self, reference_service, mock_db, sample_reference_data, sample_library
    ):
        """Test reference creation with validation error"""
        # Mock validation to raise error
        with patch.object(reference_service, '_validate_library_access', new_callable=AsyncMock) as mock_validate_lib:
            mock_validate_lib.return_value = sample_library
            
            with patch.object(reference_service, '_validate_reference_data', new_callable=AsyncMock) as mock_validate:
                mock_validate.side_effect = ValueError("Invalid DOI format")
                
                with pytest.raises(ValueError, match="Invalid DOI format"):
                    await reference_service.create_reference(
                        user_id="user-123",
                        library_id="lib-123",
                        reference_data=sample_reference_data
                    )
                
                mock_db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_reference_permission_error(
        self, reference_service, mock_db, sample_reference_data
    ):
        """Test reference creation with permission error"""
        with patch.object(reference_service, '_validate_library_access', new_callable=AsyncMock) as mock_validate:
            mock_validate.side_effect = PermissionError("Access denied")
            
            with pytest.raises(PermissionError, match="Access denied"):
                await reference_service.create_reference(
                    user_id="user-123",
                    library_id="lib-123",
                    reference_data=sample_reference_data
                )
    
    @pytest.mark.asyncio
    async def test_get_reference_success(self, reference_service, mock_db, sample_reference):
        """Test successful reference retrieval"""
        # Mock database query
        mock_query = Mock()
        mock_query.options.return_value.filter.return_value.first.return_value = sample_reference
        mock_db.query.return_value = mock_query
        
        result = await reference_service.get_reference("ref-123")
        
        assert result is not None
        assert result.id == "ref-123"
        assert result.title == "Test Article"
    
    @pytest.mark.asyncio
    async def test_get_reference_not_found(self, reference_service, mock_db):
        """Test reference retrieval when not found"""
        # Mock database query to return None
        mock_query = Mock()
        mock_query.options.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = await reference_service.get_reference("nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_reference_success(
        self, reference_service, mock_db, sample_reference
    ):
        """Test successful reference update"""
        update_data = ZoteroItemUpdate(
            title="Updated Title",
            publication_year=2024
        )
        
        # Mock access check
        with patch.object(reference_service, '_get_reference_with_access_check', new_callable=AsyncMock) as mock_access:
            mock_access.return_value = sample_reference
            
            with patch.object(reference_service, '_validate_update_data', new_callable=AsyncMock):
                with patch.object(reference_service, '_update_metadata_index', new_callable=AsyncMock):
                    with patch.object(reference_service, 'get_reference', new_callable=AsyncMock) as mock_get:
                        mock_get.return_value = Mock(id="ref-123", title="Updated Title")
                        
                        result = await reference_service.update_reference(
                            user_id="user-123",
                            reference_id="ref-123",
                            update_data=update_data
                        )
                        
                        assert result is not None
                        assert sample_reference.title == "Updated Title"
                        assert sample_reference.publication_year == 2024
                        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_reference_not_found(self, reference_service, mock_db):
        """Test reference update when not found"""
        update_data = ZoteroItemUpdate(title="Updated Title")
        
        with patch.object(reference_service, '_get_reference_with_access_check', new_callable=AsyncMock) as mock_access:
            mock_access.return_value = None
            
            result = await reference_service.update_reference(
                user_id="user-123",
                reference_id="nonexistent",
                update_data=update_data
            )
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_reference_success(
        self, reference_service, mock_db, sample_reference
    ):
        """Test successful reference deletion"""
        with patch.object(reference_service, '_get_reference_with_access_check', new_callable=AsyncMock) as mock_access:
            mock_access.return_value = sample_reference
            
            result = await reference_service.delete_reference(
                user_id="user-123",
                reference_id="ref-123"
            )
            
            assert result is True
            assert sample_reference.is_deleted is True
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_reference_not_found(self, reference_service, mock_db):
        """Test reference deletion when not found"""
        with patch.object(reference_service, '_get_reference_with_access_check', new_callable=AsyncMock) as mock_access:
            mock_access.return_value = None
            
            result = await reference_service.delete_reference(
                user_id="user-123",
                reference_id="nonexistent"
            )
            
            assert result is False
    
    # Validation Tests
    
    @pytest.mark.asyncio
    async def test_validate_reference_data_success(self, reference_service, sample_reference_data):
        """Test successful reference data validation"""
        # Should not raise any exception
        await reference_service._validate_reference_data(sample_reference_data)
    
    @pytest.mark.asyncio
    async def test_validate_reference_data_missing_item_type(self, reference_service, sample_creator):
        """Test validation with missing item type"""
        invalid_data = ZoteroItemCreate(
            item_type="",  # Empty item type
            title="Test Article",
            creators=[sample_creator]
        )
        
        with pytest.raises(ValueError, match="Item type is required"):
            await reference_service._validate_reference_data(invalid_data)
    
    @pytest.mark.asyncio
    async def test_validate_reference_data_invalid_doi(self, reference_service, sample_creator):
        """Test validation with invalid DOI"""
        invalid_data = ZoteroItemCreate(
            item_type="article",
            title="Test Article",
            creators=[sample_creator],
            doi="invalid-doi"
        )
        
        with pytest.raises(ValueError, match="Invalid DOI format"):
            await reference_service._validate_reference_data(invalid_data)
    
    @pytest.mark.asyncio
    async def test_validate_reference_data_invalid_year(self, reference_service, sample_creator):
        """Test validation with invalid publication year"""
        invalid_data = ZoteroItemCreate(
            item_type="article",
            title="Test Article",
            creators=[sample_creator],
            publication_year=999  # Too old
        )
        
        with pytest.raises(ValueError, match="Invalid publication year"):
            await reference_service._validate_reference_data(invalid_data)
    
    @pytest.mark.asyncio
    async def test_validate_reference_data_invalid_creator(self, reference_service):
        """Test validation with invalid creator"""
        invalid_creator = ZoteroCreator(
            creator_type="",  # Missing creator type
            first_name="John",
            last_name="Doe"
        )
        
        invalid_data = ZoteroItemCreate(
            item_type="article",
            title="Test Article",
            creators=[invalid_creator]
        )
        
        with pytest.raises(ValueError, match="creator_type is required"):
            await reference_service._validate_reference_data(invalid_data)
    
    # Data Integrity Tests
    
    @pytest.mark.asyncio
    async def test_check_data_integrity(self, reference_service, mock_db):
        """Test data integrity check"""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.all.return_value = [Mock(id="ref-1"), Mock(id="ref-2")]
        mock_db.query.return_value.outerjoin.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.group_by.return_value.having.return_value.all.return_value = []
        
        result = await reference_service.check_data_integrity()
        
        assert "total_references" in result
        assert "orphaned_references" in result
        assert "missing_required_fields" in result
        assert "duplicate_dois" in result
        assert "invalid_years" in result
        assert "issues" in result
    
    @pytest.mark.asyncio
    async def test_repair_data_integrity(self, reference_service, mock_db):
        """Test data integrity repair"""
        # Mock database queries
        mock_db.query.return_value.outerjoin.return_value.filter.return_value.count.return_value = 2
        mock_db.query.return_value.outerjoin.return_value.filter.return_value.delete.return_value = None
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.commit = Mock()
        
        result = await reference_service.repair_data_integrity()
        
        assert "repairs_attempted" in result
        assert "repairs_successful" in result
        assert "repairs_failed" in result
        assert "actions" in result
        mock_db.commit.assert_called_once()
    
    # Helper Method Tests
    
    def test_is_valid_doi(self, reference_service):
        """Test DOI validation"""
        assert reference_service._is_valid_doi("10.1000/test.doi") is True
        assert reference_service._is_valid_doi("10.1234/example") is True
        assert reference_service._is_valid_doi("invalid-doi") is False
        assert reference_service._is_valid_doi("10.123") is False
    
    def test_is_valid_isbn(self, reference_service):
        """Test ISBN validation"""
        assert reference_service._is_valid_isbn("978-0-123456-78-9") is True
        assert reference_service._is_valid_isbn("9780123456789") is True
        assert reference_service._is_valid_isbn("0-123456-78-X") is True
        assert reference_service._is_valid_isbn("invalid-isbn") is False
        assert reference_service._is_valid_isbn("123") is False
    
    def test_is_valid_issn(self, reference_service):
        """Test ISSN validation"""
        assert reference_service._is_valid_issn("1234-5678") is True
        assert reference_service._is_valid_issn("1234-567X") is True
        assert reference_service._is_valid_issn("invalid-issn") is False
        assert reference_service._is_valid_issn("12345678") is False
    
    def test_is_valid_url(self, reference_service):
        """Test URL validation"""
        assert reference_service._is_valid_url("https://example.com") is True
        assert reference_service._is_valid_url("http://test.org/path") is True
        assert reference_service._is_valid_url("https://example.com:8080/path?query=value") is True
        assert reference_service._is_valid_url("invalid-url") is False
        assert reference_service._is_valid_url("ftp://example.com") is False
    
    def test_serialize_creators(self, reference_service, sample_creator):
        """Test creator serialization"""
        creators = [sample_creator]
        result = reference_service._serialize_creators(creators)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["creator_type"] == "author"
        assert result[0]["first_name"] == "John"
        assert result[0]["last_name"] == "Doe"
    
    def test_convert_to_response(self, reference_service, sample_reference):
        """Test conversion to response format"""
        result = reference_service._convert_to_response(sample_reference)
        
        assert result.id == sample_reference.id
        assert result.title == sample_reference.title
        assert result.item_type == sample_reference.item_type
        assert len(result.creators) == 1
        assert result.creators[0].creator_type == "author"
    
    # Library and Collection Access Tests
    
    @pytest.mark.asyncio
    async def test_get_references_by_library(
        self, reference_service, mock_db, sample_reference, sample_library
    ):
        """Test getting references by library"""
        # Mock validation
        with patch.object(reference_service, '_validate_library_access', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = sample_library
            
            # Mock database query
            mock_query = Mock()
            mock_query.filter.return_value.order_by.return_value.count.return_value = 1
            mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_reference]
            mock_db.query.return_value = mock_query
            
            references, total_count = await reference_service.get_references_by_library(
                user_id="user-123",
                library_id="lib-123",
                limit=10,
                offset=0
            )
            
            assert len(references) == 1
            assert total_count == 1
            assert references[0].id == sample_reference.id
    
    @pytest.mark.asyncio
    async def test_get_references_by_collection(
        self, reference_service, mock_db, sample_reference
    ):
        """Test getting references by collection"""
        sample_collection = Mock(id="coll-123", library_id="lib-123")
        
        # Mock validation
        with patch.object(reference_service, '_validate_collection_access', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = sample_collection
            
            # Mock database query
            mock_query = Mock()
            mock_query.join.return_value.filter.return_value.order_by.return_value.count.return_value = 1
            mock_query.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_reference]
            mock_db.query.return_value = mock_query
            
            references, total_count = await reference_service.get_references_by_collection(
                user_id="user-123",
                collection_id="coll-123",
                limit=10,
                offset=0
            )
            
            assert len(references) == 1
            assert total_count == 1
            assert references[0].id == sample_reference.id


if __name__ == "__main__":
    pytest.main([__file__])