"""
Zotero Attachment API Endpoints

This module provides REST API endpoints for managing Zotero PDF and file attachments.
It handles attachment import, storage, retrieval, and metadata extraction.

Requirements addressed:
- 7.1: PDF attachment detection and import
- 7.2: Secure file storage and access controls
- 10.3: Proper access controls and permissions
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from backend.core.database import get_db
from backend.services.auth_service import get_current_user
from backend.services.zotero.zotero_attachment_service import ZoteroAttachmentService
from backend.services.zotero.zotero_client import ZoteroClient
from backend.services.zotero.zotero_auth_service import ZoteroAuthService
from backend.models.schemas import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zotero/attachments", tags=["zotero-attachments"])


# Pydantic models for request/response
class AttachmentResponse(BaseModel):
    """Response model for attachment information"""
    id: str
    zotero_key: str
    title: str
    filename: Optional[str] = None
    content_type: Optional[str] = None
    attachment_type: str
    file_size: Optional[int] = None
    sync_status: str
    created_at: str
    updated_at: str
    has_file: bool = False
    metadata: Optional[Dict[str, Any]] = None


class AttachmentImportRequest(BaseModel):
    """Request model for importing attachments"""
    item_id: str = Field(..., description="Internal item ID to import attachments for")
    force_refresh: bool = Field(False, description="Force re-import even if attachments exist")


class AttachmentImportResponse(BaseModel):
    """Response model for attachment import operation"""
    success: bool
    imported_count: int
    skipped_count: int
    error_count: int
    attachments: List[AttachmentResponse]
    errors: List[str] = []


class StorageStatsResponse(BaseModel):
    """Response model for storage statistics"""
    total_attachments: int
    total_size_bytes: int
    total_size_mb: float
    synced_attachments: int
    by_content_type: Dict[str, int]
    by_sync_status: Dict[str, int]


@router.post("/import", response_model=AttachmentImportResponse)
async def import_attachments(
    request: AttachmentImportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Import attachments for a specific Zotero item
    
    This endpoint imports all attachments (PDFs, documents, etc.) associated with
    a Zotero item. Files are downloaded and stored securely with proper access controls.
    """
    try:
        # Initialize services
        attachment_service = ZoteroAttachmentService(db)
        auth_service = ZoteroAuthService(db)
        
        # Get user's Zotero connection
        connection = await auth_service.get_active_connection(current_user.id)
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active Zotero connection found"
            )
        
        # Create Zotero client
        zotero_client = ZoteroClient(
            access_token=connection.access_token,
            user_id=connection.zotero_user_id
        )
        
        # Get user preferences
        user_preferences = await auth_service.get_user_preferences(current_user.id)
        
        # Import attachments
        imported_attachments = await attachment_service.import_attachments_for_item(
            request.item_id,
            zotero_client,
            user_preferences
        )
        
        # Convert to response format
        attachment_responses = []
        for attachment_info in imported_attachments:
            attachment_responses.append(AttachmentResponse(
                id=attachment_info['id'],
                zotero_key=attachment_info['zotero_key'],
                title=attachment_info['title'],
                filename=attachment_info.get('filename'),
                content_type=attachment_info.get('content_type'),
                attachment_type=attachment_info['attachment_type'],
                file_size=attachment_info.get('file_size'),
                sync_status=attachment_info['sync_status'],
                created_at=attachment_info.get('created_at', ''),
                updated_at=attachment_info.get('updated_at', ''),
                has_file=bool(attachment_info.get('file_size'))
            ))
        
        return AttachmentImportResponse(
            success=True,
            imported_count=len(imported_attachments),
            skipped_count=0,
            error_count=0,
            attachments=attachment_responses
        )
        
    except Exception as e:
        logger.error(f"Failed to import attachments for item {request.item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import attachments: {str(e)}"
        )


@router.get("/item/{item_id}", response_model=List[AttachmentResponse])
async def get_item_attachments(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all attachments for a specific item
    
    Returns a list of all attachments associated with the specified item,
    including metadata and file information.
    """
    try:
        attachment_service = ZoteroAttachmentService(db)
        
        # Get attachments with access control
        attachments = await attachment_service.get_attachments_for_item(item_id, current_user.id)
        
        # Convert to response format
        attachment_responses = []
        for attachment in attachments:
            attachment_responses.append(AttachmentResponse(
                id=str(attachment.id),
                zotero_key=attachment.zotero_attachment_key,
                title=attachment.title or '',
                filename=attachment.filename,
                content_type=attachment.content_type,
                attachment_type=attachment.attachment_type,
                file_size=attachment.file_size,
                sync_status=attachment.sync_status,
                created_at=attachment.created_at.isoformat() if attachment.created_at else '',
                updated_at=attachment.updated_at.isoformat() if attachment.updated_at else '',
                has_file=bool(attachment.file_path and Path(attachment.file_path).exists()),
                metadata=attachment.attachment_metadata
            ))
        
        return attachment_responses
        
    except Exception as e:
        logger.error(f"Failed to get attachments for item {item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attachments: {str(e)}"
        )


@router.get("/{attachment_id}", response_model=AttachmentResponse)
async def get_attachment(
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get attachment details by ID
    
    Returns detailed information about a specific attachment including
    metadata and file information.
    """
    try:
        attachment_service = ZoteroAttachmentService(db)
        
        # Get attachment with access control
        attachment = await attachment_service.get_attachment_by_id(attachment_id, current_user.id)
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )
        
        return AttachmentResponse(
            id=str(attachment.id),
            zotero_key=attachment.zotero_attachment_key,
            title=attachment.title or '',
            filename=attachment.filename,
            content_type=attachment.content_type,
            attachment_type=attachment.attachment_type,
            file_size=attachment.file_size,
            sync_status=attachment.sync_status,
            created_at=attachment.created_at.isoformat() if attachment.created_at else '',
            updated_at=attachment.updated_at.isoformat() if attachment.updated_at else '',
            has_file=bool(attachment.file_path and Path(attachment.file_path).exists()),
            metadata=attachment.attachment_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get attachment {attachment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attachment: {str(e)}"
        )


@router.get("/{attachment_id}/download")
async def download_attachment(
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download attachment file
    
    Returns the actual file content for download. Includes proper access controls
    and content type headers.
    """
    try:
        attachment_service = ZoteroAttachmentService(db)
        
        # Get file path with access control
        file_path = await attachment_service.get_attachment_file_path(attachment_id, current_user.id)
        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment file not found"
            )
        
        # Get attachment details for proper headers
        attachment = await attachment_service.get_attachment_by_id(attachment_id, current_user.id)
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )
        
        # Return file with proper headers
        return FileResponse(
            path=file_path,
            filename=attachment.filename or f"attachment_{attachment_id}",
            media_type=attachment.content_type or 'application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download attachment {attachment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download attachment: {str(e)}"
        )


@router.post("/{attachment_id}/extract-metadata")
async def extract_attachment_metadata(
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Extract and update metadata from attachment file
    
    Analyzes the attachment file (especially PDFs) to extract metadata
    such as title, author, page count, and text preview for indexing.
    """
    try:
        attachment_service = ZoteroAttachmentService(db)
        
        # Update metadata
        success = await attachment_service.update_attachment_metadata(attachment_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found or no file available"
            )
        
        # Return updated attachment info
        attachment = await attachment_service.get_attachment_by_id(attachment_id, current_user.id)
        
        return AttachmentResponse(
            id=str(attachment.id),
            zotero_key=attachment.zotero_attachment_key,
            title=attachment.title or '',
            filename=attachment.filename,
            content_type=attachment.content_type,
            attachment_type=attachment.attachment_type,
            file_size=attachment.file_size,
            sync_status=attachment.sync_status,
            created_at=attachment.created_at.isoformat() if attachment.created_at else '',
            updated_at=attachment.updated_at.isoformat() if attachment.updated_at else '',
            has_file=bool(attachment.file_path and Path(attachment.file_path).exists()),
            metadata=attachment.attachment_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to extract metadata for attachment {attachment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract metadata: {str(e)}"
        )


@router.delete("/{attachment_id}")
async def delete_attachment(
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete attachment and associated file
    
    Removes the attachment record from the database and deletes the
    associated file from storage. Includes proper access controls.
    """
    try:
        attachment_service = ZoteroAttachmentService(db)
        
        # Delete attachment with access control
        success = await attachment_service.delete_attachment(attachment_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )
        
        return {"success": True, "message": "Attachment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete attachment {attachment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete attachment: {str(e)}"
        )


@router.get("/stats/storage", response_model=StorageStatsResponse)
async def get_storage_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get storage statistics for user's attachments
    
    Returns information about total storage usage, file types,
    and sync status for all user attachments.
    """
    try:
        attachment_service = ZoteroAttachmentService(db)
        
        # Get storage statistics
        stats = await attachment_service.get_storage_stats(current_user.id)
        
        return StorageStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get storage stats for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage stats: {str(e)}"
        )