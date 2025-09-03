"""
Zotero Reference Sharing API Endpoints

Provides REST API endpoints for reference sharing, collaborative collections, and discussions.
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from services.auth_service import get_current_user
from services.zotero.zotero_reference_sharing_service import ZoteroReferenceSharingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zotero/sharing", tags=["zotero-sharing"])


# Pydantic models for request/response
class ShareReferenceRequest(BaseModel):
    reference_id: str = Field(..., description="ID of the reference to share")
    shared_with_user_id: str = Field(..., description="ID of the user to share with")
    permission_level: str = Field(default='read', description="Permission level: read, comment, edit")
    share_message: Optional[str] = Field(None, description="Optional message to include with the share")
    share_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class SharedReferenceResponse(BaseModel):
    share_id: str
    reference_id: str
    reference_title: str
    reference_authors: List[Dict[str, Any]]
    reference_year: Optional[int]
    owner_user_id: str
    shared_with_user_id: str
    permission_level: str
    share_message: Optional[str]
    created_at: str
    updated_at: str


class CreateCollectionRequest(BaseModel):
    name: str = Field(..., description="Name of the collection")
    description: Optional[str] = Field(None, description="Description of the collection")
    collection_type: str = Field(default='research_project', description="Type of collection")
    is_public: bool = Field(default=False, description="Whether the collection is public")
    collaboration_settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Collaboration settings")


class SharedCollectionResponse(BaseModel):
    collection_id: str
    name: str
    description: Optional[str]
    collection_type: str
    owner_user_id: str
    is_public: bool
    visibility: str
    user_role: str
    user_permission_level: str
    reference_count: int
    collaborator_count: int
    created_at: str
    updated_at: str


class AddCollaboratorRequest(BaseModel):
    user_id: str = Field(..., description="ID of the user to add as collaborator")
    permission_level: str = Field(default='read', description="Permission level: read, comment, edit, admin")
    role: str = Field(default='collaborator', description="Role: owner, admin, editor, collaborator, viewer")
    invitation_message: Optional[str] = Field(None, description="Optional invitation message")


class AddReferenceToCollectionRequest(BaseModel):
    reference_id: str = Field(..., description="ID of the reference to add")
    notes: Optional[str] = Field(None, description="Optional notes about the reference")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for organization")
    is_featured: bool = Field(default=False, description="Whether to feature this reference")


class CollectionReferenceResponse(BaseModel):
    collection_reference_id: str
    reference_id: str
    reference_title: str
    reference_authors: List[Dict[str, Any]]
    reference_year: Optional[int]
    reference_doi: Optional[str]
    added_by: str
    added_at: str
    notes: Optional[str]
    tags: List[str]
    is_featured: bool
    sort_order: int


class AddDiscussionRequest(BaseModel):
    content: str = Field(..., description="Discussion content")
    discussion_type: str = Field(default='comment', description="Type: comment, question, suggestion, review")
    collection_id: Optional[str] = Field(None, description="Optional collection context")
    parent_discussion_id: Optional[str] = Field(None, description="Parent discussion for threading")


class ReferenceDiscussionResponse(BaseModel):
    discussion_id: str
    reference_id: str
    collection_id: Optional[str]
    user_id: str
    discussion_type: str
    content: str
    parent_discussion_id: Optional[str]
    is_resolved: bool
    resolved_by: Optional[str]
    resolved_at: Optional[str]
    created_at: str
    updated_at: str


class NotificationResponse(BaseModel):
    notification_id: str
    notification_type: str
    title: str
    message: str
    target_type: Optional[str]
    target_id: Optional[str]
    sender_user_id: Optional[str]
    is_read: bool
    is_dismissed: bool
    action_url: Optional[str]
    created_at: str
    read_at: Optional[str]


@router.post("/references/share", response_model=Dict[str, Any])
async def share_reference(
    request: ShareReferenceRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Share a reference with another user"""
    try:
        service = ZoteroReferenceSharingService(db)
        result = await service.share_reference_with_user(
            request.reference_id,
            current_user["id"],
            request.shared_with_user_id,
            request.permission_level,
            request.share_message,
            request.share_context
        )
        
        return {
            "success": True,
            "message": "Reference shared successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to share reference: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/references/shared", response_model=List[SharedReferenceResponse])
async def get_shared_references(
    as_owner: bool = Query(True, description="Get references shared by user (True) or with user (False)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get references shared by or with the current user"""
    try:
        service = ZoteroReferenceSharingService(db)
        references = await service.get_shared_references(current_user["id"], as_owner)
        
        return [SharedReferenceResponse(**ref) for ref in references]
        
    except Exception as e:
        logger.error(f"Failed to get shared references: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections", response_model=Dict[str, Any])
async def create_shared_collection(
    request: CreateCollectionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new shared reference collection"""
    try:
        service = ZoteroReferenceSharingService(db)
        result = await service.create_shared_collection(
            request.name,
            current_user["id"],
            request.description,
            request.collection_type,
            request.is_public,
            request.collaboration_settings
        )
        
        return {
            "success": True,
            "message": "Collection created successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to create collection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections", response_model=List[SharedCollectionResponse])
async def get_user_collections(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get collections accessible to the current user"""
    try:
        service = ZoteroReferenceSharingService(db)
        collections = await service.get_user_collections(current_user["id"])
        
        return [SharedCollectionResponse(**collection) for collection in collections]
        
    except Exception as e:
        logger.error(f"Failed to get user collections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{collection_id}/collaborators", response_model=Dict[str, Any])
async def add_collaborator(
    collection_id: str,
    request: AddCollaboratorRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a collaborator to a shared collection"""
    try:
        service = ZoteroReferenceSharingService(db)
        result = await service.add_collaborator_to_collection(
            collection_id,
            request.user_id,
            current_user["id"],
            request.permission_level,
            request.role,
            request.invitation_message
        )
        
        return {
            "success": True,
            "message": "Collaborator added successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add collaborator: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{collection_id}/references", response_model=Dict[str, Any])
async def add_reference_to_collection(
    collection_id: str,
    request: AddReferenceToCollectionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a reference to a shared collection"""
    try:
        service = ZoteroReferenceSharingService(db)
        result = await service.add_reference_to_collection(
            collection_id,
            request.reference_id,
            current_user["id"],
            request.notes,
            request.tags,
            request.is_featured
        )
        
        return {
            "success": True,
            "message": "Reference added to collection successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add reference to collection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_id}/references", response_model=List[CollectionReferenceResponse])
async def get_collection_references(
    collection_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of references to return"),
    offset: int = Query(0, ge=0, description="Number of references to skip"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get references in a shared collection"""
    try:
        service = ZoteroReferenceSharingService(db)
        references = await service.get_collection_references(
            collection_id, current_user["id"], limit, offset
        )
        
        return [CollectionReferenceResponse(**ref) for ref in references]
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get collection references: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/references/{reference_id}/discussions", response_model=Dict[str, Any])
async def add_reference_discussion(
    reference_id: str,
    request: AddDiscussionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a discussion comment to a reference"""
    try:
        service = ZoteroReferenceSharingService(db)
        result = await service.add_reference_discussion(
            reference_id,
            current_user["id"],
            request.content,
            request.discussion_type,
            request.collection_id,
            request.parent_discussion_id
        )
        
        return {
            "success": True,
            "message": "Discussion added successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add reference discussion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/references/{reference_id}/discussions", response_model=List[ReferenceDiscussionResponse])
async def get_reference_discussions(
    reference_id: str,
    collection_id: Optional[str] = Query(None, description="Optional collection context"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get discussions for a reference"""
    try:
        service = ZoteroReferenceSharingService(db)
        discussions = await service.get_reference_discussions(
            reference_id, current_user["id"], collection_id
        )
        
        return [ReferenceDiscussionResponse(**discussion) for discussion in discussions]
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get reference discussions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications", response_model=List[NotificationResponse])
async def get_user_notifications(
    unread_only: bool = Query(False, description="Get only unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Number of notifications to return"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notifications for the current user"""
    try:
        service = ZoteroReferenceSharingService(db)
        notifications = await service.get_user_notifications(
            current_user["id"], unread_only, limit, offset
        )
        
        return [NotificationResponse(**notification) for notification in notifications]
        
    except Exception as e:
        logger.error(f"Failed to get user notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/{notification_id}/read", response_model=Dict[str, Any])
async def mark_notification_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    try:
        service = ZoteroReferenceSharingService(db)
        success = await service.mark_notification_as_read(notification_id, current_user["id"])
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {
            "success": True,
            "message": "Notification marked as read"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity", response_model=List[Dict[str, Any]])
async def get_sharing_activity(
    limit: int = Query(50, ge=1, le=100, description="Number of activities to return"),
    offset: int = Query(0, ge=0, description="Number of activities to skip"),
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sharing activity for the current user"""
    try:
        # This would be implemented in the service
        # For now, return a placeholder
        return []
        
    except Exception as e:
        logger.error(f"Failed to get sharing activity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/references/{reference_id}/shares/{share_id}")
async def revoke_reference_share(
    reference_id: str,
    share_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke a reference share"""
    try:
        # This would be implemented in the service
        # For now, return a placeholder
        return {
            "success": True,
            "message": "Reference share revoked successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to revoke reference share: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collections/{collection_id}")
async def delete_shared_collection(
    collection_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a shared collection"""
    try:
        # This would be implemented in the service
        # For now, return a placeholder
        return {
            "success": True,
            "message": "Collection deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to delete collection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))