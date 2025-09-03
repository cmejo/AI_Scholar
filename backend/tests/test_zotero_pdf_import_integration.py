"""
Integration Tests for Zotero PDF Import and Storage System

This module tests the complete workflow of PDF attachment detection, import,
storage, and metadata extraction in an integrated environment.

Requirements tested:
- 7.1: PDF attachment detection and import
- 7.2: Secure file storage and access controls
- 10.3: Proper access controls and permissions
"""

import pytest
import tempfile
import shutil
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from backend.services.zotero.zotero_attachment_service import ZoteroAttachmentService
from backend.services.zotero.zotero_client import ZoteroClient
from backend.models.zotero_models import (
    ZoteroConnection, ZoteroLibrary, ZoteroItem, ZoteroAttachment
)
from backend.core.database import Base


@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing"""
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
/Title (Test Document)
/Author (Test Author)
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
(Hello World Test Content) Tj
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


@pytest.fixture
async def test_data_setup(test_db):
    """Set up test data in database"""
    # Create connection
    connection = ZoteroConnection(
        id="conn-123",
        user_id="user-123",
        zotero_user_id="12345",
        access_token="test-token",
        connection_status="active"
    )
    test_db.add(connection)
    
    # Create library
    library = ZoteroLibrary(
        id="lib-123",
        connection_id="conn-123",
        zotero_library_id="12345",
        library_type="user",
        library_name="Test Library"
    )
    test_db.add(library)
    
    # Create item
    item = ZoteroItem(
        id="item-123",
        library_id="lib-123",
        zotero_item_key="ITEM123",
        item_type="article",
        title="Test Article"
    )
    test_db.add(item)
    
    await test_db.commit()
    
    return {
        'connection': connection,
        'library': library,
        'item': item
    }


class TestZoteroPDFImportIntegration:
    """Integration tests for PDF import and storage system"""
    
    @pytest.mark.asyncio
    async def test_complete_pdf_import_workflow(
        self, test_db, test_data_setup, temp_storage_dir, sample_pdf_content
    ):
        """Test complete PDF import workflow from Zotero API to local storage"""
        
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = str(temp_storage_dir)
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            # Initialize service
            service = ZoteroAttachmentService(test_db)
            
            # Mock Zotero client
            mock_client = Mock(spec=ZoteroClient)
            mock_client.get_item_attachments = AsyncMock(return_value=[
                {
                    'key': 'ATTACH123',
                    'version': 1,
                    'data': {
                        'title': 'Test PDF Document',
                        'filename': 'test_document.pdf',
                        'contentType': 'application/pdf',
                        'linkMode': 'imported_file',
                        'dateAdded': '2024-01-01T00:00:00Z',
                        'dateModified': '2024-01-01T00:00:00Z'
                    }
                }
            ])
            mock_client.get_attachment_download_url = AsyncMock(
                return_value="https://api.zotero.org/users/12345/items/ATTACH123/file"
            )
            
            # Mock HTTP download
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = Mock()
                mock_response.status = 200
                mock_response.headers = {'content-length': str(len(sample_pdf_content))}
                mock_response.content.iter_chunked = AsyncMock(return_value=[sample_pdf_content])
                
                mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
                
                # Import attachments
                result = await service.import_attachments_for_item(
                    "item-123", mock_client
                )
            
            # Verify results
            assert len(result) == 1
            attachment_info = result[0]
            assert attachment_info['zotero_key'] == 'ATTACH123'
            assert attachment_info['title'] == 'Test PDF Document'
            assert attachment_info['filename'] == 'test_document.pdf'
            assert attachment_info['content_type'] == 'application/pdf'
            assert attachment_info['sync_status'] == 'synced'
            
            # Verify attachment was saved to database
            from sqlalchemy import select
            db_result = await test_db.execute(
                select(ZoteroAttachment).where(
                    ZoteroAttachment.zotero_attachment_key == 'ATTACH123'
                )
            )
            attachment = db_result.scalar_one()
            
            assert attachment.title == 'Test PDF Document'
            assert attachment.filename == 'test_document.pdf'
            assert attachment.content_type == 'application/pdf'
            assert attachment.sync_status == 'synced'
            assert attachment.file_size == len(sample_pdf_content)
            assert attachment.file_path is not None
            
            # Verify file was saved to storage
            file_path = Path(attachment.file_path)
            assert file_path.exists()
            assert file_path.read_bytes() == sample_pdf_content
    
    @pytest.mark.asyncio
    async def test_pdf_metadata_extraction_integration(
        self, test_db, test_data_setup, temp_storage_dir, sample_pdf_content
    ):
        """Test PDF metadata extraction integration"""
        
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = str(temp_storage_dir)
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(test_db)
            
            # Create test PDF file
            test_pdf = temp_storage_dir / "test.pdf"
            test_pdf.write_bytes(sample_pdf_content)
            
            # Create attachment in database
            attachment = ZoteroAttachment(
                id="att-123",
                item_id="item-123",
                zotero_attachment_key="ATTACH123",
                title="Test PDF",
                filename="test.pdf",
                content_type="application/pdf",
                attachment_type="imported_file",
                file_path=str(test_pdf),
                sync_status="synced"
            )
            test_db.add(attachment)
            await test_db.commit()
            
            # Extract metadata
            success = await service.update_attachment_metadata("att-123", "user-123")
            
            assert success is True
            
            # Verify metadata was extracted and saved
            await test_db.refresh(attachment)
            metadata = attachment.attachment_metadata
            
            assert metadata is not None
            assert 'page_count' in metadata
            assert 'text_preview' in metadata
            assert metadata['page_count'] == 1
            assert 'Hello World Test Content' in metadata['text_preview']
    
    @pytest.mark.asyncio
    async def test_access_control_integration(
        self, test_db, test_data_setup, temp_storage_dir
    ):
        """Test access control integration across all operations"""
        
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = str(temp_storage_dir)
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(test_db)
            
            # Create attachment for user-123
            attachment = ZoteroAttachment(
                id="att-123",
                item_id="item-123",
                zotero_attachment_key="ATTACH123",
                title="Test PDF",
                filename="test.pdf",
                content_type="application/pdf",
                attachment_type="imported_file",
                sync_status="synced"
            )
            test_db.add(attachment)
            await test_db.commit()
            
            # Test authorized access (user-123)
            result = await service.get_attachment_by_id("att-123", "user-123")
            assert result is not None
            assert result.id == "att-123"
            
            # Test unauthorized access (different user)
            result = await service.get_attachment_by_id("att-123", "user-456")
            assert result is None
            
            # Test deletion with proper access control
            success = await service.delete_attachment("att-123", "user-123")
            assert success is True
            
            # Verify attachment was deleted
            from sqlalchemy import select
            db_result = await test_db.execute(
                select(ZoteroAttachment).where(ZoteroAttachment.id == "att-123")
            )
            deleted_attachment = db_result.scalar_one_or_none()
            assert deleted_attachment is None
    
    @pytest.mark.asyncio
    async def test_large_file_handling_integration(
        self, test_db, test_data_setup, temp_storage_dir
    ):
        """Test handling of large files that exceed size limits"""
        
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = str(temp_storage_dir)
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 1  # 1MB limit for testing
            
            service = ZoteroAttachmentService(test_db)
            
            # Mock Zotero client
            mock_client = Mock(spec=ZoteroClient)
            mock_client.get_item_attachments = AsyncMock(return_value=[
                {
                    'key': 'LARGE123',
                    'version': 1,
                    'data': {
                        'title': 'Large PDF Document',
                        'filename': 'large_document.pdf',
                        'contentType': 'application/pdf',
                        'linkMode': 'imported_file'
                    }
                }
            ])
            mock_client.get_attachment_download_url = AsyncMock(
                return_value="https://api.zotero.org/users/12345/items/LARGE123/file"
            )
            
            # Mock HTTP response with large content
            large_content = b'x' * (2 * 1024 * 1024)  # 2MB content
            
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = Mock()
                mock_response.status = 200
                mock_response.headers = {'content-length': str(len(large_content))}
                
                mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
                
                # Import attachments
                result = await service.import_attachments_for_item(
                    "item-123", mock_client
                )
            
            # Verify that large file was handled appropriately
            assert len(result) == 1
            attachment_info = result[0]
            assert attachment_info['sync_status'] == 'error'  # Should fail due to size
    
    @pytest.mark.asyncio
    async def test_storage_statistics_integration(
        self, test_db, test_data_setup, temp_storage_dir
    ):
        """Test storage statistics calculation integration"""
        
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = str(temp_storage_dir)
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(test_db)
            
            # Create multiple attachments with different properties
            attachments = [
                ZoteroAttachment(
                    id="att-1",
                    item_id="item-123",
                    zotero_attachment_key="ATTACH1",
                    content_type="application/pdf",
                    file_size=1024000,  # 1MB
                    sync_status="synced"
                ),
                ZoteroAttachment(
                    id="att-2",
                    item_id="item-123",
                    zotero_attachment_key="ATTACH2",
                    content_type="application/pdf",
                    file_size=2048000,  # 2MB
                    sync_status="synced"
                ),
                ZoteroAttachment(
                    id="att-3",
                    item_id="item-123",
                    zotero_attachment_key="ATTACH3",
                    content_type="application/msword",
                    file_size=512000,  # 0.5MB
                    sync_status="pending"
                ),
                ZoteroAttachment(
                    id="att-4",
                    item_id="item-123",
                    zotero_attachment_key="ATTACH4",
                    content_type="application/pdf",
                    sync_status="error"
                )
            ]
            
            for attachment in attachments:
                test_db.add(attachment)
            await test_db.commit()
            
            # Get storage statistics
            stats = await service.get_storage_stats("user-123")
            
            # Verify statistics
            assert stats['total_attachments'] == 4
            assert stats['total_size_bytes'] == 3584000  # 1MB + 2MB + 0.5MB
            assert stats['total_size_mb'] == 3.42  # Approximately
            assert stats['synced_attachments'] == 2
            assert stats['by_content_type']['application/pdf'] == 3
            assert stats['by_content_type']['application/msword'] == 1
            assert stats['by_sync_status']['synced'] == 2
            assert stats['by_sync_status']['pending'] == 1
            assert stats['by_sync_status']['error'] == 1
    
    @pytest.mark.asyncio
    async def test_concurrent_import_operations(
        self, test_db, test_data_setup, temp_storage_dir, sample_pdf_content
    ):
        """Test concurrent attachment import operations"""
        
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = str(temp_storage_dir)
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(test_db)
            
            # Create additional items for concurrent testing
            items = []
            for i in range(3):
                item = ZoteroItem(
                    id=f"item-{i}",
                    library_id="lib-123",
                    zotero_item_key=f"ITEM{i}",
                    item_type="article",
                    title=f"Test Article {i}"
                )
                test_db.add(item)
                items.append(item)
            
            await test_db.commit()
            
            # Mock Zotero client for each item
            async def mock_get_attachments(library_id, item_key):
                return [{
                    'key': f'ATTACH{item_key}',
                    'version': 1,
                    'data': {
                        'title': f'PDF for {item_key}',
                        'filename': f'{item_key.lower()}.pdf',
                        'contentType': 'application/pdf',
                        'linkMode': 'imported_file'
                    }
                }]
            
            mock_client = Mock(spec=ZoteroClient)
            mock_client.get_item_attachments = mock_get_attachments
            mock_client.get_attachment_download_url = AsyncMock(
                return_value="https://api.zotero.org/test.pdf"
            )
            
            # Mock HTTP downloads
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = Mock()
                mock_response.status = 200
                mock_response.headers = {'content-length': str(len(sample_pdf_content))}
                mock_response.content.iter_chunked = AsyncMock(return_value=[sample_pdf_content])
                
                mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
                
                # Run concurrent import operations
                tasks = []
                for i in range(3):
                    task = service.import_attachments_for_item(f"item-{i}", mock_client)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify all operations completed successfully
            for i, result in enumerate(results):
                assert not isinstance(result, Exception), f"Task {i} failed: {result}"
                assert len(result) == 1
                assert result[0]['zotero_key'] == f'ATTACHITEM{i}'
            
            # Verify all attachments were saved
            from sqlalchemy import select
            db_result = await test_db.execute(select(ZoteroAttachment))
            all_attachments = db_result.scalars().all()
            assert len(all_attachments) == 3
    
    @pytest.mark.asyncio
    async def test_error_recovery_integration(
        self, test_db, test_data_setup, temp_storage_dir
    ):
        """Test error recovery and partial success scenarios"""
        
        with patch('backend.services.zotero.zotero_attachment_service.settings') as mock_settings:
            mock_settings.ATTACHMENT_STORAGE_PATH = str(temp_storage_dir)
            mock_settings.MAX_ATTACHMENT_SIZE_MB = 50
            
            service = ZoteroAttachmentService(test_db)
            
            # Mock Zotero client with mixed success/failure responses
            mock_client = Mock(spec=ZoteroClient)
            mock_client.get_item_attachments = AsyncMock(return_value=[
                {
                    'key': 'SUCCESS123',
                    'version': 1,
                    'data': {
                        'title': 'Successful PDF',
                        'filename': 'success.pdf',
                        'contentType': 'application/pdf',
                        'linkMode': 'imported_file'
                    }
                },
                {
                    'key': 'FAIL123',
                    'version': 1,
                    'data': {
                        'title': 'Failed PDF',
                        'filename': 'fail.pdf',
                        'contentType': 'application/pdf',
                        'linkMode': 'imported_file'
                    }
                }
            ])
            
            # Mock download URLs - one success, one failure
            async def mock_get_download_url(library_id, attachment_key):
                if attachment_key == 'SUCCESS123':
                    return "https://api.zotero.org/success.pdf"
                else:
                    return None  # Simulate failure
            
            mock_client.get_attachment_download_url = mock_get_download_url
            
            # Mock HTTP session for successful download
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = Mock()
                mock_response.status = 200
                mock_response.headers = {'content-length': '1024'}
                mock_response.content.iter_chunked = AsyncMock(return_value=[b'test content'])
                
                mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
                
                # Import attachments (should handle partial failures gracefully)
                result = await service.import_attachments_for_item(
                    "item-123", mock_client
                )
            
            # Verify partial success - one attachment should succeed
            assert len(result) == 1  # Only successful attachment returned
            assert result[0]['zotero_key'] == 'SUCCESS123'
            assert result[0]['sync_status'] == 'synced'
            
            # Verify database state
            from sqlalchemy import select
            db_result = await test_db.execute(
                select(ZoteroAttachment).where(
                    ZoteroAttachment.item_id == "item-123"
                )
            )
            attachments = db_result.scalars().all()
            
            # Should have both attachments, but with different sync statuses
            assert len(attachments) == 2
            
            success_attachment = next(a for a in attachments if a.zotero_attachment_key == 'SUCCESS123')
            fail_attachment = next(a for a in attachments if a.zotero_attachment_key == 'FAIL123')
            
            assert success_attachment.sync_status == 'synced'
            assert fail_attachment.sync_status == 'error'