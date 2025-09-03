"""
Zotero Attachment Service

This service handles PDF and file attachment import, storage, and management
for Zotero integration. It provides secure file storage, metadata extraction,
and access controls for attachments.

Requirements addressed:
- 7.1: PDF attachment detection and import
- 7.2: Secure file storage and access controls
- 10.3: Proper access controls and permissions
"""

import os
import hashlib
import mimetypes
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import aiofiles
import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from backend.models.zotero_models import ZoteroAttachment, ZoteroItem, ZoteroConnection
from backend.services.zotero.zotero_client import ZoteroClient
from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ZoteroAttachmentService:
    """Service for managing Zotero PDF and file attachments"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.storage_base_path = Path(settings.ATTACHMENT_STORAGE_PATH or "zotero_attachments")
        self.max_file_size = settings.MAX_ATTACHMENT_SIZE_MB * 1024 * 1024  # Convert to bytes
        self.allowed_content_types = {
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'text/html',
            'image/jpeg',
            'image/png',
            'image/gif'
        }
        
        # Ensure storage directory exists
        self.storage_base_path.mkdir(parents=True, exist_ok=True)
    
    async def import_attachments_for_item(
        self, 
        item_id: str, 
        zotero_client: ZoteroClient,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Import all attachments for a specific Zotero item
        
        Args:
            item_id: Internal item ID
            zotero_client: Authenticated Zotero client
            user_preferences: User preferences for attachment handling
            
        Returns:
            List of imported attachment information
        """
        try:
            # Get the item with its Zotero key
            result = await self.db.execute(
                select(ZoteroItem)
                .options(selectinload(ZoteroItem.library))
                .where(ZoteroItem.id == item_id)
            )
            item = result.scalar_one_or_none()
            
            if not item:
                raise ValueError(f"Item not found: {item_id}")
            
            # Check user preferences for attachment sync
            if user_preferences and not user_preferences.get('sync_attachments', True):
                logger.info(f"Attachment sync disabled for user, skipping item {item_id}")
                return []
            
            # Get attachments from Zotero API
            zotero_attachments = await zotero_client.get_item_attachments(
                item.library.zotero_library_id,
                item.zotero_item_key
            )
            
            imported_attachments = []
            
            for zotero_attachment in zotero_attachments:
                try:
                    attachment_info = await self._import_single_attachment(
                        item, zotero_attachment, zotero_client, user_preferences
                    )
                    if attachment_info:
                        imported_attachments.append(attachment_info)
                except Exception as e:
                    logger.error(f"Failed to import attachment {zotero_attachment.get('key', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Imported {len(imported_attachments)} attachments for item {item_id}")
            return imported_attachments
            
        except Exception as e:
            logger.error(f"Failed to import attachments for item {item_id}: {e}")
            raise
    
    async def _import_single_attachment(
        self,
        item: ZoteroItem,
        zotero_attachment: Dict[str, Any],
        zotero_client: ZoteroClient,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Import a single attachment from Zotero"""
        
        attachment_key = zotero_attachment['key']
        attachment_data = zotero_attachment['data']
        
        # Check if attachment already exists
        result = await self.db.execute(
            select(ZoteroAttachment)
            .where(
                ZoteroAttachment.item_id == item.id,
                ZoteroAttachment.zotero_attachment_key == attachment_key
            )
        )
        existing_attachment = result.scalar_one_or_none()
        
        # Extract attachment metadata
        attachment_type = attachment_data.get('linkMode', 'unknown')
        title = attachment_data.get('title', '')
        filename = attachment_data.get('filename', '')
        content_type = attachment_data.get('contentType', '')
        
        # Validate content type
        if content_type and content_type not in self.allowed_content_types:
            logger.warning(f"Skipping attachment with unsupported content type: {content_type}")
            return None
        
        # Check file size limits
        max_size_mb = user_preferences.get('max_attachment_size_mb', 50) if user_preferences else 50
        max_size_bytes = max_size_mb * 1024 * 1024
        
        # Create or update attachment record
        if existing_attachment:
            attachment = existing_attachment
            # Update metadata
            attachment.title = title
            attachment.filename = filename
            attachment.content_type = content_type
            attachment.attachment_type = attachment_type
            attachment.updated_at = datetime.utcnow()
        else:
            attachment = ZoteroAttachment(
                item_id=item.id,
                zotero_attachment_key=attachment_key,
                attachment_type=attachment_type,
                title=title,
                filename=filename,
                content_type=content_type,
                sync_status='pending'
            )
            self.db.add(attachment)
        
        # Try to download the file if it's a stored file
        if attachment_type in ['imported_file', 'imported_url'] and filename:
            try:
                file_info = await self._download_attachment_file(
                    attachment, zotero_client, item.library.zotero_library_id, max_size_bytes
                )
                if file_info:
                    attachment.file_path = file_info['file_path']
                    attachment.file_size = file_info['file_size']
                    attachment.md5_hash = file_info['md5_hash']
                    attachment.sync_status = 'synced'
                else:
                    attachment.sync_status = 'error'
            except Exception as e:
                logger.error(f"Failed to download attachment file {attachment_key}: {e}")
                attachment.sync_status = 'error'
        else:
            # For linked files or URLs, just store the metadata
            attachment.sync_status = 'synced'
        
        await self.db.commit()
        
        return {
            'id': str(attachment.id),
            'zotero_key': attachment_key,
            'title': title,
            'filename': filename,
            'content_type': content_type,
            'attachment_type': attachment_type,
            'sync_status': attachment.sync_status,
            'file_size': attachment.file_size
        }
    
    async def _download_attachment_file(
        self,
        attachment: ZoteroAttachment,
        zotero_client: ZoteroClient,
        library_id: str,
        max_size_bytes: int
    ) -> Optional[Dict[str, Any]]:
        """Download attachment file from Zotero and store locally"""
        
        try:
            # Get file download URL from Zotero
            download_url = await zotero_client.get_attachment_download_url(
                library_id, attachment.zotero_attachment_key
            )
            
            if not download_url:
                logger.warning(f"No download URL available for attachment {attachment.zotero_attachment_key}")
                return None
            
            # Create storage path
            storage_dir = self.storage_base_path / str(attachment.item_id)
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate safe filename
            safe_filename = self._generate_safe_filename(attachment.filename or f"{attachment.zotero_attachment_key}.pdf")
            file_path = storage_dir / safe_filename
            
            # Download file
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download attachment: HTTP {response.status}")
                        return None
                    
                    # Check content length
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > max_size_bytes:
                        logger.warning(f"Attachment too large: {content_length} bytes > {max_size_bytes} bytes")
                        return None
                    
                    # Download and save file
                    file_size = 0
                    md5_hash = hashlib.md5()
                    
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            file_size += len(chunk)
                            
                            # Check size limit during download
                            if file_size > max_size_bytes:
                                logger.warning(f"Attachment too large during download: {file_size} bytes")
                                await f.close()
                                file_path.unlink(missing_ok=True)  # Delete partial file
                                return None
                            
                            md5_hash.update(chunk)
                            await f.write(chunk)
            
            return {
                'file_path': str(file_path),
                'file_size': file_size,
                'md5_hash': md5_hash.hexdigest()
            }
            
        except Exception as e:
            logger.error(f"Error downloading attachment file: {e}")
            return None
    
    def _generate_safe_filename(self, filename: str) -> str:
        """Generate a safe filename for storage"""
        # Remove or replace unsafe characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
        safe_filename = ''.join(c if c in safe_chars else '_' for c in filename)
        
        # Ensure it's not too long
        if len(safe_filename) > 200:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:200-len(ext)] + ext
        
        return safe_filename
    
    async def get_attachment_by_id(self, attachment_id: str, user_id: str) -> Optional[ZoteroAttachment]:
        """Get attachment by ID with access control"""
        result = await self.db.execute(
            select(ZoteroAttachment)
            .join(ZoteroItem)
            .join(ZoteroItem.library)
            .join(ZoteroConnection)
            .where(
                ZoteroAttachment.id == attachment_id,
                ZoteroConnection.user_id == user_id
            )
            .options(selectinload(ZoteroAttachment.item))
        )
        return result.scalar_one_or_none()
    
    async def get_attachments_for_item(self, item_id: str, user_id: str) -> List[ZoteroAttachment]:
        """Get all attachments for an item with access control"""
        result = await self.db.execute(
            select(ZoteroAttachment)
            .join(ZoteroItem)
            .join(ZoteroItem.library)
            .join(ZoteroConnection)
            .where(
                ZoteroAttachment.item_id == item_id,
                ZoteroConnection.user_id == user_id
            )
            .order_by(ZoteroAttachment.created_at)
        )
        return result.scalars().all()
    
    async def delete_attachment(self, attachment_id: str, user_id: str) -> bool:
        """Delete attachment with access control"""
        # Get attachment with access control
        attachment = await self.get_attachment_by_id(attachment_id, user_id)
        if not attachment:
            return False
        
        # Delete file from storage if it exists
        if attachment.file_path and Path(attachment.file_path).exists():
            try:
                Path(attachment.file_path).unlink()
                logger.info(f"Deleted attachment file: {attachment.file_path}")
            except Exception as e:
                logger.error(f"Failed to delete attachment file {attachment.file_path}: {e}")
        
        # Delete from database
        await self.db.execute(
            delete(ZoteroAttachment).where(ZoteroAttachment.id == attachment_id)
        )
        await self.db.commit()
        
        return True
    
    async def get_attachment_file_path(self, attachment_id: str, user_id: str) -> Optional[str]:
        """Get file path for attachment with access control"""
        attachment = await self.get_attachment_by_id(attachment_id, user_id)
        if not attachment or not attachment.file_path:
            return None
        
        file_path = Path(attachment.file_path)
        if not file_path.exists():
            logger.warning(f"Attachment file not found: {attachment.file_path}")
            return None
        
        return str(file_path)
    
    async def extract_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF file"""
        try:
            import PyPDF2
            
            metadata = {}
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Basic metadata
                metadata['page_count'] = len(pdf_reader.pages)
                
                # Document info
                if pdf_reader.metadata:
                    doc_info = pdf_reader.metadata
                    metadata['title'] = doc_info.get('/Title', '')
                    metadata['author'] = doc_info.get('/Author', '')
                    metadata['subject'] = doc_info.get('/Subject', '')
                    metadata['creator'] = doc_info.get('/Creator', '')
                    metadata['producer'] = doc_info.get('/Producer', '')
                    metadata['creation_date'] = doc_info.get('/CreationDate', '')
                    metadata['modification_date'] = doc_info.get('/ModDate', '')
                
                # Extract text from first few pages for indexing
                text_content = []
                max_pages = min(3, len(pdf_reader.pages))  # First 3 pages
                
                for i in range(max_pages):
                    try:
                        page_text = pdf_reader.pages[i].extract_text()
                        if page_text.strip():
                            text_content.append(page_text.strip())
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {i}: {e}")
                        continue
                
                metadata['text_preview'] = '\n\n'.join(text_content)[:2000]  # Limit preview size
            
            return metadata
            
        except ImportError:
            logger.warning("PyPDF2 not available, skipping PDF metadata extraction")
            return {}
        except Exception as e:
            logger.error(f"Failed to extract PDF metadata from {file_path}: {e}")
            return {}
    
    async def update_attachment_metadata(self, attachment_id: str, user_id: str) -> bool:
        """Update attachment metadata by extracting from file"""
        attachment = await self.get_attachment_by_id(attachment_id, user_id)
        if not attachment or not attachment.file_path:
            return False
        
        file_path = Path(attachment.file_path)
        if not file_path.exists():
            return False
        
        # Extract metadata based on content type
        metadata = {}
        
        if attachment.content_type == 'application/pdf':
            metadata = await self.extract_pdf_metadata(str(file_path))
        
        # Update attachment metadata
        if metadata:
            current_metadata = attachment.attachment_metadata or {}
            current_metadata.update(metadata)
            
            await self.db.execute(
                update(ZoteroAttachment)
                .where(ZoteroAttachment.id == attachment_id)
                .values(
                    attachment_metadata=current_metadata,
                    updated_at=datetime.utcnow()
                )
            )
            await self.db.commit()
            
            return True
        
        return False
    
    async def get_storage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get storage statistics for user's attachments"""
        result = await self.db.execute(
            select(
                ZoteroAttachment.content_type,
                ZoteroAttachment.file_size,
                ZoteroAttachment.sync_status
            )
            .join(ZoteroItem)
            .join(ZoteroItem.library)
            .join(ZoteroConnection)
            .where(ZoteroConnection.user_id == user_id)
        )
        
        attachments = result.all()
        
        stats = {
            'total_attachments': len(attachments),
            'total_size_bytes': 0,
            'by_content_type': {},
            'by_sync_status': {},
            'synced_attachments': 0
        }
        
        for attachment in attachments:
            content_type, file_size, sync_status = attachment
            
            # Total size
            if file_size:
                stats['total_size_bytes'] += file_size
            
            # By content type
            if content_type:
                stats['by_content_type'][content_type] = stats['by_content_type'].get(content_type, 0) + 1
            
            # By sync status
            stats['by_sync_status'][sync_status] = stats['by_sync_status'].get(sync_status, 0) + 1
            
            if sync_status == 'synced':
                stats['synced_attachments'] += 1
        
        # Convert bytes to MB for readability
        stats['total_size_mb'] = round(stats['total_size_bytes'] / (1024 * 1024), 2)
        
        return stats