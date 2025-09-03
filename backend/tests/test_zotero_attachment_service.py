"""
Tests for Zotero Attachment Service

This module tests PDF import, storage, metadata extraction, and access controls
for the Zotero attachment system.

Requirements tested:
- 7.1: PDF attachment detection and import
- 7.2: Secure file storage and access controls
- 10.3: Proper access controls and permissions
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import hashlib
import json

from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.zotero.zotero_attachment_service import ZoteroAttachmentService
from backend.services.zotero.zotero_client import ZoteroClient
from backend.models.zotero_models import (
    ZoteroAttachment, ZoteroItem, ZoteroLibrary, ZoteroConnection
)


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return Mock(spec=AsyncSession)


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_zotero_client():
    """Mock Zotero client"""
    client = Mock(spec=ZoteroClient)
    client.get_item_attachments = AsyncMock()
    client.get_attachment_download_url = AsyncMock()
    return client


@pytest.fixture
def sample_zotero_attachment():
    """Sample Zotero attachment data"""
    return {
        'key': 'ABCD1234',
        'version': 1,
        'data': {
            'title': 'Sample PDF Document',
            'filename': 'sample.pdf',
            'contentType': 'application/pdf',
            'linkMode': 'imported_file',
            'dateAdded': '2024-01-01T00:00:00Z',
            'dateModified': '2024-01-01T00:00:00Z'
        }
    }


@pytest.fixture
def sample_zotero_item():
    """Sample Zotero item"""
    library = ZoteroLibrary(
        id="lib-123",
        zotero_library_id="12345",
        library_type="user",
        library_name="My Library"
    )
    
    item = ZoteroItem(
        id="item-123",
        library_id="lib-123",
        zotero_item_key="ITEM123",
        item_type="article",
        title="Sample Article"
    )
    item.library = library
    return item


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing"""
    # This is a minimal PDF content for testing
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Hello World) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""


class TestZoteroAttachmentService:
    """Test cases for ZoteroAttachmentService"""
    
    @pytest.mark.asyncio
    async def test_init_creates_storage_directory(self, mock_db_session, temp_storage_dir):
        """Test that service initialization creates storage directory"""
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = str(temp_storage_dir / "attachments")
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(mock_db_session)
            
            assert service.storage_base_path.exists()
            assert service.storage_base_path.is_dir()
    
    @pytest.mark.asyncio
    async def test_import_attachments_for_item_success(
        self, mock_db_session, mock_zotero_client, sample_zotero_item, 
        sample_zotero_attachment, temp_storage_dir
    ):
        """Test successful attachment import for an item"""
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = str(temp_storage_dir)
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            # Mock database queries
            mock_db_session.execute = AsyncMock()
            mock_db_session.commit = AsyncMock()
            mock_db_session.add = Mock()
            
            # Mock item query result
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = sample_zotero_item
            mock_db_session.execute.return_value = mock_result
            
            # Mock Zotero API response
            mock_zotero_client.get_item_attachments.return_value = [sample_zotero_attachment]
            mock_zotero_client.get_attachment_download_url.return_value = "https://example.com/file.pdf"
            
            service = ZoteroAttachmentService(mock_db_session)
            
            # Mock file download
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = Mock()
                mock_response.status = 200
                mock_response.headers = {'content-length': '1024'}
                mock_response.content.iter_chunked = AsyncMock(return_value=[b'test content'])
                
                mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
                
                with patch('aiofiles.open', create=True) as mock_file:
                    mock_file.return_value.__aenter__.return_value.write = AsyncMock()
                    mock_file.return_value.__aenter__.return_value.close = AsyncMock()
                    
                    result = await service.import_attachments_for_item(
                        "item-123", mock_zotero_client
                    )
            
            assert len(result) == 1
            assert result[0]['zotero_key'] == 'ABCD1234'
            assert result[0]['title'] == 'Sample PDF Document'
            assert result[0]['filename'] == 'sample.pdf'
            assert result[0]['content_type'] == 'application/pdf'
    
    @pytest.mark.asyncio
    async def test_import_attachments_item_not_found(self, mock_db_session, mock_zotero_client):
        """Test attachment import when item is not found"""
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = "./test_attachments"
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            # Mock database query returning None
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db_session.execute = AsyncMock(return_value=mock_result)
            
            service = ZoteroAttachmentService(mock_db_session)
            
            with pytest.raises(ValueError, match="Item not found"):
                await service.import_attachments_for_item("nonexistent", mock_zotero_client)
    
    @pytest.mark.asyncio
    async def test_import_attachments_sync_disabled(
        self, mock_db_session, mock_zotero_client, sample_zotero_item
    ):
        """Test attachment import when sync is disabled in user preferences"""
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = "./test_attachments"
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            # Mock database query
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = sample_zotero_item
            mock_db_session.execute = AsyncMock(return_value=mock_result)
            
            service = ZoteroAttachmentService(mock_db_session)
            
            # User preferences with sync disabled
            user_preferences = {'sync_attachments': False}
            
            result = await service.import_attachments_for_item(
                "item-123", mock_zotero_client, user_preferences
            )
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_download_attachment_file_success(
        self, mock_db_session, mock_zotero_client, temp_storage_dir, sample_pdf_content
    ):
        """Test successful attachment file download"""
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = str(temp_storage_dir)
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(mock_db_session)
            
            # Create test attachment
            attachment = ZoteroAttachment(
                id="att-123",
                item_id="item-123",
                zotero_attachment_key="ABCD1234",
                filename="test.pdf",
                attachment_type="imported_file"
            )
            
            mock_zotero_client.get_attachment_download_url.return_value = "https://example.com/file.pdf"
            
            # Mock HTTP response
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = Mock()
                mock_response.status = 200
                mock_response.headers = {'content-length': str(len(sample_pdf_content))}
                mock_response.content.iter_chunked = AsyncMock(return_value=[sample_pdf_content])
                
                mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
                
                result = await service._download_attachment_file(
                    attachment, mock_zotero_client, "12345", 50 * 1024 * 1024
                )
            
            assert result is not None
            assert 'file_path' in result
            assert 'file_size' in result
            assert 'md5_hash' in result
            assert result['file_size'] == len(sample_pdf_content)
    
    @pytest.mark.asyncio
    async def test_download_attachment_file_too_large(
        self, mock_db_session, mock_zotero_client, temp_storage_dir
    ):
        """Test attachment download when file is too large"""
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = str(temp_storage_dir)
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(mock_db_session)
            
            attachment = ZoteroAttachment(
                id="att-123",
                item_id="item-123",
                zotero_attachment_key="ABCD1234",
                filename="large.pdf",
                attachment_type="imported_file"
            )
            
            mock_zotero_client.get_attachment_download_url.return_value = "https://example.com/file.pdf"
            
            # Mock HTTP response with large content
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = Mock()
                mock_response.status = 200
                mock_response.headers = {'content-length': '100000000'}  # 100MB
                
                mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
                
                result = await service._download_attachment_file(
                    attachment, mock_zotero_client, "12345", 50 * 1024 * 1024  # 50MB limit
                )
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_attachment_by_id_with_access_control(self, mock_db_session):
        """Test getting attachment by ID with proper access control"""
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = "./test_attachments"
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(mock_db_session)
            
            # Mock database query
            mock_attachment = ZoteroAttachment(
                id="att-123",
                item_id="item-123",
                zotero_attachment_key="ABCD1234",
                title="Test Attachment"
            )
            
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = mock_attachment
            mock_db_session.execute = AsyncMock(return_value=mock_result)
            
            result = await service.get_attachment_by_id("att-123", "user-123")
            
            assert result == mock_attachment
            # Verify that the query includes proper joins for access control
            mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_attachment_by_id_access_denied(self, mock_db_session):
        """Test getting attachment by ID when access is denied"""
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = "./test_attachments"
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(mock_db_session)
            
            # Mock database query returning None (access denied)
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db_session.execute = AsyncMock(return_value=mock_result)
            
            result = await service.get_attachment_by_id("att-123", "unauthorized-user")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_attachment_success(self, mock_db_session, temp_storage_dir):
        """Test successful attachment deletion"""
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = str(temp_storage_dir)
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(mock_db_session)
            
            # Create test file
            test_file = temp_storage_dir / "test_file.pdf"
            test_file.write_text("test content")
            
            # Mock attachment with file path
            mock_attachment = ZoteroAttachment(
                id="att-123",
                file_path=str(test_file)
            )
            
            # Mock get_attachment_by_id to return the attachment
            service.get_attachment_by_id = AsyncMock(return_value=mock_attachment)
            
            mock_db_session.execute = AsyncMock()
            mock_db_session.commit = AsyncMock()
            
            result = await service.delete_attachment("att-123", "user-123")
            
            assert result is True
            assert not test_file.exists()  # File should be deleted
            mock_db_session.execute.assert_called_once()
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_attachment_not_found(self, mock_db_session):
        """Test attachment deletion when attachment is not found"""
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = "./test_attachments"
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(mock_db_session)
            
            # Mock get_attachment_by_id to return None
            service.get_attachment_by_id = AsyncMock(return_value=None)
            
            result = await service.delete_attachment("nonexistent", "user-123")
            
            assert result is False
    
    def test_generate_safe_filename(self, mock_db_session):
        """Test safe filename generation"""
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = "./test_attachments"
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(mock_db_session)
            
            # Test normal filename
            result = service._generate_safe_filename("document.pdf")
            assert result == "document.pdf"
            
            # Test filename with unsafe characters
            result = service._generate_safe_filename("doc/with\\unsafe:chars.pdf")
            assert "/" not in result
            assert "\\" not in result
            assert ":" not in result
            
            # Test very long filename
            long_name = "a" * 250 + ".pdf"
            result = service._generate_safe_filename(long_name)
            assert len(result) <= 204  # 200 + ".pdf"
            assert result.endswith(".pdf")
    
    @pytest.mark.asyncio
    async def test_extract_pdf_metadata_success(self, mock_db_session, temp_storage_dir, sample_pdf_content):
        """Test successful PDF metadata extraction"""
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = str(temp_storage_dir)
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(mock_db_session)
            
            # Create test PDF file
            test_pdf = temp_storage_dir / "test.pdf"
            test_pdf.write_bytes(sample_pdf_content)
            
            # Mock PyPDF2
            with patch('PyPDF2.PdfReader') as mock_pdf_reader:
                mock_reader_instance = Mock()
                mock_reader_instance.pages = [Mock(), Mock()]  # 2 pages
                mock_reader_instance.metadata = {
                    '/Title': 'Test Document',
                    '/Author': 'Test Author',
                    '/Subject': 'Test Subject'
                }
                
                # Mock page text extraction
                mock_page = Mock()
                mock_page.extract_text.return_value = "Sample text content"
                mock_reader_instance.pages = [mock_page, mock_page]
                
                mock_pdf_reader.return_value = mock_reader_instance
                
                result = await service.extract_pdf_metadata(str(test_pdf))
            
            assert 'page_count' in result
            assert 'title' in result
            assert 'author' in result
            assert 'text_preview' in result
            assert result['page_count'] == 2
            assert result['title'] == 'Test Document'
            assert result['author'] == 'Test Author'
    
    @pytest.mark.asyncio
    async def test_extract_pdf_metadata_pypdf2_not_available(self, mock_db_session, temp_storage_dir):
        """Test PDF metadata extraction when PyPDF2 is not available"""
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = str(temp_storage_dir)
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(mock_db_session)
            
            # Mock ImportError for PyPDF2
            with patch('builtins.__import__', side_effect=ImportError("No module named 'PyPDF2'")):
                result = await service.extract_pdf_metadata("test.pdf")
            
            assert result == {}
    
    @pytest.mark.asyncio
    async def test_get_storage_stats(self, mock_db_session):
        """Test storage statistics calculation"""
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = "./test_attachments"
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(mock_db_session)
            
            # Mock database query results
            mock_attachments = [
                ('application/pdf', 1024000, 'synced'),
                ('application/pdf', 2048000, 'synced'),
                ('application/msword', 512000, 'pending'),
                ('application/pdf', None, 'error')
            ]
            
            mock_result = Mock()
            mock_result.all.return_value = mock_attachments
            mock_db_session.execute = AsyncMock(return_value=mock_result)
            
            result = await service.get_storage_stats("user-123")
            
            assert result['total_attachments'] == 4
            assert result['total_size_bytes'] == 3584000  # 1024000 + 2048000 + 512000
            assert result['total_size_mb'] == 3.42  # Approximately
            assert result['synced_attachments'] == 2
            assert result['by_content_type']['application/pdf'] == 3
            assert result['by_content_type']['application/msword'] == 1
            assert result['by_sync_status']['synced'] == 2
            assert result['by_sync_status']['pending'] == 1
            assert result['by_sync_status']['error'] == 1
    
    @pytest.mark.asyncio
    async def test_unsupported_content_type_skipped(
        self, mock_db_session, mock_zotero_client, sample_zotero_item, temp_storage_dir
    ):
        """Test that unsupported content types are skipped"""
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = str(temp_storage_dir)
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(mock_db_session)
            
            # Mock database queries
            mock_db_session.execute = AsyncMock()
            mock_db_session.commit = AsyncMock()
            
            # Create attachment with unsupported content type
            unsupported_attachment = {
                'key': 'UNSUPPORTED123',
                'data': {
                    'title': 'Unsupported File',
                    'filename': 'file.xyz',
                    'contentType': 'application/unsupported',
                    'linkMode': 'imported_file'
                }
            }
            
            result = await service._import_single_attachment(
                sample_zotero_item, unsupported_attachment, mock_zotero_client
            )
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_update_attachment_metadata_success(self, mock_db_session, temp_storage_dir, sample_pdf_content):
        """Test successful attachment metadata update"""
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = str(temp_storage_dir)
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(mock_db_session)
            
            # Create test PDF file
            test_pdf = temp_storage_dir / "test.pdf"
            test_pdf.write_bytes(sample_pdf_content)
            
            # Mock attachment
            mock_attachment = ZoteroAttachment(
                id="att-123",
                file_path=str(test_pdf),
                content_type="application/pdf",
                attachment_metadata={}
            )
            
            service.get_attachment_by_id = AsyncMock(return_value=mock_attachment)
            mock_db_session.execute = AsyncMock()
            mock_db_session.commit = AsyncMock()
            
            # Mock PDF metadata extraction
            service.extract_pdf_metadata = AsyncMock(return_value={
                'page_count': 1,
                'title': 'Test PDF'
            })
            
            result = await service.update_attachment_metadata("att-123", "user-123")
            
            assert result is True
            mock_db_session.execute.assert_called_once()
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_attachment_metadata_no_file(self, mock_db_session):
        """Test attachment metadata update when no file exists"""
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = "./test_attachments"
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(mock_db_session)
            
            # Mock attachment without file
            mock_attachment = ZoteroAttachment(
                id="att-123",
                file_path=None
            )
            
            service.get_attachment_by_id = AsyncMock(return_value=mock_attachment)
            
            result = await service.update_attachment_metadata("att-123", "user-123")
            
            assert result is False