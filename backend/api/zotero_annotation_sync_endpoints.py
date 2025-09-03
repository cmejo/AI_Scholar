"""
Zotero Annotation Synchronization API Endpoints

This module provides REST API endpoints for managing annotation synchronization,
collaboration, and sharing features.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from core.database import get_db
from services.zotero.zotero_annotation_sync_service import ZoteroAnnotationSyncService
from middleware.zotero_auth_middleware import get_current_user_with_zotero
from models.zotero_schemas import (
    ZoteroAnnotationResponse, ZoteroAnnotationCollaborationResponse,
    ZoteroAnnotationShareResponse, ZoteroAnnotationHistoryResponse
)

router = APIRouter(prefix="/api/zotero/annotations", tags=["zotero-annotations"])


# Request/Response Models
class AnnotationSyncRequest(BaseModel):
    attachment_id: str = Field(..., description="ID of the attachment to sync")
    sync_direction: str = Field(
        default="bidirectional", 
        description="Sync direction: 'from_zotero', 'to_zotero', or 'bidirectional'"
    )


class AnnotationSyncResponse(BaseModel):
    attachment_id: str
    sync_direction: str
    annotations_imported: int
    annotations_exported: int
    annotations_updated: int
    conflicts_detected: int
    errors: List[Dict[str, Any]]
    sync_completed_at: datetime


class AnnotationCollaborationRequest(BaseModel):
    annotation_id: str = Field(..., description="ID of the annotation")
    collaboration_type: str = Field(..., description="Type of collaboration: 'comment', 'reply', 'edit'")
    content: str = Field(..., description="Collaboration content")
    parent_collaboration_id: Optional[str] = Field(None, description="Parent collaboration ID for replies")


class AnnotationShareRequest(BaseModel):
    annotation_id: str = Field(..., description="ID of the annotation to share")
    shared_with_user_id: str = Field(..., description="ID of the user to share with")
    permission_level: str = Field(default="read", description="Permission level: 'read', 'comment', 'edit'")
    share_message: Optional[str] = Field(None, description="Optional message to include with the share")


class SharedAnnotationResponse(BaseModel):
    share: ZoteroAnnotationShareResponse
    annotation: ZoteroAnnotationResponse
    attachment_title: str
    item_title: str


@router.post("/sync", response_model=AnnotationSyncResponse)
async def sync_annotations(
    request: AnnotationSyncRequest,
    current_user: dict = Depends(get_current_user_with_zotero),
    db: Session = Depends(get_db)
):
    """
    Synchronize annotations for a specific attachment with Zotero
    """
    try:
        service = ZoteroAnnotationSyncService(db)
        
        # Validate sync direction
        valid_directions = ['from_zotero', 'to_zotero', 'bidirectional']
        if request.sync_direction not in valid_directions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sync direction. Must be one of: {valid_directions}"
            )
        
        # Perform sync
        sync_results = await service.sync_annotations_for_attachment(
            attachment_id=request.attachment_id,
            user_id=current_user["user_id"],
            sync_direction=request.sync_direction
        )
        
        return AnnotationSyncResponse(
            **sync_results,
            sync_completed_at=datetime.utcnow()
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing annotations: {str(e)}"
        )


@router.post("/collaborate", response_model=ZoteroAnnotationCollaborationResponse)
async def create_annotation_collaboration(
    request: AnnotationCollaborationRequest,
    current_user: dict = Depends(get_current_user_with_zotero),
    db: Session = Depends(get_db)
):
    """
    Create a new annotation collaboration (comment, reply, etc.)
    """
    try:
        service = ZoteroAnnotationSyncService(db)
        
        # Validate collaboration type
        valid_types = ['comment', 'reply', 'edit', 'share']
        if request.collaboration_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid collaboration type. Must be one of: {valid_types}"
            )
        
        collaboration = await service.create_annotation_collaboration(
            annotation_id=request.annotation_id,
            user_id=current_user["user_id"],
            collaboration_type=request.collaboration_type,
            content=request.content,
            parent_collaboration_id=request.parent_collaboration_id
        )
        
        return ZoteroAnnotationCollaborationResponse.from_orm(collaboration)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating annotation collaboration: {str(e)}"
        )


@router.post("/share", response_model=ZoteroAnnotationShareResponse)
async def share_annotation(
    request: AnnotationShareRequest,
    current_user: dict = Depends(get_current_user_with_zotero),
    db: Session = Depends(get_db)
):
    """
    Share an annotation with another user
    """
    try:
        service = ZoteroAnnotationSyncService(db)
        
        # Validate permission level
        valid_permissions = ['read', 'comment', 'edit']
        if request.permission_level not in valid_permissions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid permission level. Must be one of: {valid_permissions}"
            )
        
        share = await service.share_annotation(
            annotation_id=request.annotation_id,
            owner_user_id=current_user["user_id"],
            shared_with_user_id=request.shared_with_user_id,
            permission_level=request.permission_level,
            share_message=request.share_message
        )
        
        return ZoteroAnnotationShareResponse.from_orm(share)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sharing annotation: {str(e)}"
        )


@router.get("/collaborations/{annotation_id}", response_model=List[ZoteroAnnotationCollaborationResponse])
async def get_annotation_collaborations(
    annotation_id: str,
    user_id: Optional[str] = Query(None, description="Filter by specific user ID"),
    current_user: dict = Depends(get_current_user_with_zotero),
    db: Session = Depends(get_db)
):
    """
    Get collaborations for a specific annotation
    """
    try:
        service = ZoteroAnnotationSyncService(db)
        
        collaborations = await service.get_annotation_collaborations(
            annotation_id=annotation_id,
            user_id=user_id
        )
        
        return [ZoteroAnnotationCollaborationResponse.from_orm(collab) for collab in collaborations]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving annotation collaborations: {str(e)}"
        )


@router.get("/history/{annotation_id}", response_model=List[ZoteroAnnotationHistoryResponse])
async def get_annotation_history(
    annotation_id: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum number of history entries to return"),
    current_user: dict = Depends(get_current_user_with_zotero),
    db: Session = Depends(get_db)
):
    """
    Get change history for a specific annotation
    """
    try:
        service = ZoteroAnnotationSyncService(db)
        
        history = await service.get_annotation_history(
            annotation_id=annotation_id,
            limit=limit
        )
        
        return [ZoteroAnnotationHistoryResponse.from_orm(entry) for entry in history]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving annotation history: {str(e)}"
        )


@router.get("/shared", response_model=List[SharedAnnotationResponse])
async def get_shared_annotations(
    permission_level: Optional[str] = Query(None, description="Filter by permission level"),
    current_user: dict = Depends(get_current_user_with_zotero),
    db: Session = Depends(get_db)
):
    """
    Get annotations shared with the current user
    """
    try:
        service = ZoteroAnnotationSyncService(db)
        
        if permission_level:
            valid_permissions = ['read', 'comment', 'edit']
            if permission_level not in valid_permissions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid permission level. Must be one of: {valid_permissions}"
                )
        
        shared_annotations = await service.get_shared_annotations(
            user_id=current_user["user_id"],
            permission_level=permission_level
        )
        
        response = []
        for item in shared_annotations:
            response.append(SharedAnnotationResponse(
                share=ZoteroAnnotationShareResponse.from_orm(item['share']),
                annotation=ZoteroAnnotationResponse.from_orm(item['annotation']),
                attachment_title=item['attachment'].title or 'Untitled',
                item_title=item['attachment'].item.title or 'Untitled'
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving shared annotations: {str(e)}"
        )


@router.delete("/share/{share_id}")
async def revoke_annotation_share(
    share_id: str,
    current_user: dict = Depends(get_current_user_with_zotero),
    db: Session = Depends(get_db)
):
    """
    Revoke an annotation share
    """
    try:
        service = ZoteroAnnotationSyncService(db)
        
        # Get the share to verify ownership
        from models.zotero_models import ZoteroAnnotationShare
        share = db.query(ZoteroAnnotationShare).filter(
            ZoteroAnnotationShare.id == share_id
        ).first()
        
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Annotation share not found"
            )
        
        # Verify user is the owner
        if share.owner_user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only revoke your own annotation shares"
            )
        
        # Revoke the share
        share.is_active = False
        db.commit()
        
        return {"message": "Annotation share revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error revoking annotation share: {str(e)}"
        )


@router.put("/collaboration/{collaboration_id}")
async def update_annotation_collaboration(
    collaboration_id: str,
    content: str,
    current_user: dict = Depends(get_current_user_with_zotero),
    db: Session = Depends(get_db)
):
    """
    Update an annotation collaboration
    """
    try:
        from models.zotero_models import ZoteroAnnotationCollaboration
        
        collaboration = db.query(ZoteroAnnotationCollaboration).filter(
            ZoteroAnnotationCollaboration.id == collaboration_id
        ).first()
        
        if not collaboration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Annotation collaboration not found"
            )
        
        # Verify user is the owner
        if collaboration.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own collaborations"
            )
        
        # Update the collaboration
        collaboration.content = content
        collaboration.updated_at = datetime.utcnow()
        db.commit()
        
        return ZoteroAnnotationCollaborationResponse.from_orm(collaboration)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating annotation collaboration: {str(e)}"
        )


@router.delete("/collaboration/{collaboration_id}")
async def delete_annotation_collaboration(
    collaboration_id: str,
    current_user: dict = Depends(get_current_user_with_zotero),
    db: Session = Depends(get_db)
):
    """
    Delete an annotation collaboration
    """
    try:
        from models.zotero_models import ZoteroAnnotationCollaboration
        
        collaboration = db.query(ZoteroAnnotationCollaboration).filter(
            ZoteroAnnotationCollaboration.id == collaboration_id
        ).first()
        
        if not collaboration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Annotation collaboration not found"
            )
        
        # Verify user is the owner
        if collaboration.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own collaborations"
            )
        
        # Soft delete the collaboration
        collaboration.is_active = False
        db.commit()
        
        return {"message": "Annotation collaboration deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting annotation collaboration: {str(e)}"
        )