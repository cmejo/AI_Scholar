"""
Zotero Export and Sharing API Endpoints

This module provides REST API endpoints for conversation export with citations,
reference sharing between users, and research project reference collections.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.database import get_db
from backend.services.auth_service import get_current_user
from backend.services.zotero.zotero_export_sharing_service import ZoteroExportSharingService
from backend.models.schemas import User


router = APIRouter(prefix="/api/zotero/export-sharing", tags=["zotero-export-sharing"])


# Request/Response Models
class ConversationExportRequest(BaseModel):
    conversation_id: str = Field(..., description="ID of the conversation to export")
    conversation_data: Dict[str, Any] = Field(..., description="Conversation messages and metadata")
    citation_style: str = Field(default="apa", description="Citation style to use")
    export_format: str = Field(default="json", description="Export format")


class ConversationExportResponse(BaseModel):
    export_id: str
    conversation: Dict[str, Any]
    bibliography: List[str]
    citation_count: int
    export_date: str


class ShareReferenceRequest(BaseModel):
    target_user_id: str = Field(..., description="ID of user to share with")
    reference_id: str = Field(..., description="ID of reference to share")
    permission_level: str = Field(default="read", description="Permission level")
    message: Optional[str] = Field(None, description="Optional message")


class ShareReferenceResponse(BaseModel):
    share_id: str
    reference_id: str
    reference_title: str
    shared_with: str
    permission_level: str
    message: Optional[str]
    shared_at: str


class CreateProjectCollectionRequest(BaseModel):
    project_name: str = Field(..., description="Name of the research project")
    description: Optional[str] = Field(None, description="Project description")
    reference_ids: Optional[List[str]] = Field(None, description="Initial reference IDs")
    collaborator_ids: Optional[List[str]] = Field(None, description="Collaborator user IDs")


class ProjectCollectionResponse(BaseModel):
    collection_id: str
    name: str
    description: Optional[str]
    owner_id: str
    reference_count: int
    collaborator_count: int
    created_at: str


class SharedReferencesResponse(BaseModel):
    shared_by_me: List[Dict[str, Any]]
    shared_with_me: List[Dict[str, Any]]


# API Endpoints
@router.post("/conversations/export", response_model=ConversationExportResponse)
async def export_conversation_with_citations(
    request: ConversationExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export conversation with proper citations for referenced papers
    
    This endpoint processes a conversation and generates an export that includes
    proper citations for any referenced Zotero items, along with a bibliography.
    """
    try:
        service = ZoteroExportSharingService(db)
        
        result = await service.export_conversation_with_citations(
            user_id=current_user.id,
            conversation_id=request.conversation_id,
            conversation_data=request.conversation_data,
            citation_style=request.citation_style
        )
        
        return ConversationExportResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export conversation: {str(e)}"
        )


@router.post("/references/share", response_model=ShareReferenceResponse)
async def share_reference_with_user(
    request: ShareReferenceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Share a reference with another user
    
    This endpoint allows users to share their Zotero references with other
    AI Scholar users, with configurable permission levels.
    """
    try:
        service = ZoteroExportSharingService(db)
        
        result = await service.share_reference_with_user(
            owner_id=current_user.id,
            target_user_id=request.target_user_id,
            reference_id=request.reference_id,
            permission_level=request.permission_level,
            message=request.message
        )
        
        return ShareReferenceResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to share reference: {str(e)}"
        )


@router.post("/collections/research-project", response_model=ProjectCollectionResponse)
async def create_research_project_collection(
    request: CreateProjectCollectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a research project reference collection
    
    This endpoint creates a collaborative collection for organizing references
    around a specific research project, with support for multiple collaborators.
    """
    try:
        service = ZoteroExportSharingService(db)
        
        result = await service.create_research_project_collection(
            user_id=current_user.id,
            project_name=request.project_name,
            description=request.description,
            reference_ids=request.reference_ids,
            collaborator_ids=request.collaborator_ids
        )
        
        return ProjectCollectionResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create research project: {str(e)}"
        )


@router.get("/references/shared", response_model=SharedReferencesResponse)
async def get_shared_references(
    include_owned: bool = True,
    include_received: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get references shared by or with the user
    
    This endpoint returns all references that the user has shared with others
    or that have been shared with the user.
    """
    try:
        service = ZoteroExportSharingService(db)
        
        result = await service.get_shared_references(
            user_id=current_user.id,
            include_owned=include_owned,
            include_received=include_received
        )
        
        return SharedReferencesResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get shared references: {str(e)}"
        )


@router.get("/collections/research-projects")
async def get_research_project_collections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get research project collections for a user
    
    This endpoint returns all research project collections that the user owns
    or collaborates on.
    """
    try:
        service = ZoteroExportSharingService(db)
        
        result = await service.get_research_project_collections(
            user_id=current_user.id
        )
        
        return {"collections": result}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get research projects: {str(e)}"
        )


@router.delete("/references/share/{share_id}")
async def revoke_reference_share(
    share_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke a reference share
    
    This endpoint allows users to revoke access to a previously shared reference.
    """
    try:
        from backend.models.zotero_models import ZoteroSharedReference
        
        # Find the share record
        share = db.query(ZoteroSharedReference).filter(
            ZoteroSharedReference.id == share_id,
            ZoteroSharedReference.owner_user_id == current_user.id
        ).first()
        
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share not found or access denied"
            )
        
        # Deactivate the share
        share.is_active = False
        db.commit()
        
        return {"message": "Reference share revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke share: {str(e)}"
        )


@router.put("/collections/{collection_id}/references")
async def add_references_to_collection(
    collection_id: str,
    reference_ids: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add references to a research project collection
    
    This endpoint allows adding references to an existing research project collection.
    """
    try:
        from backend.models.zotero_models import ZoteroSharedCollection, ZoteroCollectionReference
        
        # Verify collection exists and user has permission
        collection = db.query(ZoteroSharedCollection).filter(
            ZoteroSharedCollection.id == collection_id
        ).first()
        
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found"
            )
        
        # Check if user is owner or collaborator with edit permission
        if collection.owner_user_id != current_user.id:
            # Check collaborator permissions (simplified for now)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Add references to collection
        added_count = 0
        for ref_id in reference_ids:
            # Check if reference already in collection
            existing = db.query(ZoteroCollectionReference).filter(
                ZoteroCollectionReference.collection_id == collection_id,
                ZoteroCollectionReference.reference_id == ref_id
            ).first()
            
            if not existing:
                collection_ref = ZoteroCollectionReference(
                    collection_id=collection_id,
                    reference_id=ref_id,
                    added_by=current_user.id
                )
                db.add(collection_ref)
                added_count += 1
        
        db.commit()
        
        return {
            "message": f"Added {added_count} references to collection",
            "added_count": added_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add references: {str(e)}"
        )


@router.get("/exports/{export_id}")
async def get_conversation_export(
    export_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a conversation export by ID
    
    This endpoint retrieves a previously created conversation export.
    """
    try:
        from backend.models.zotero_models import ZoteroConversationExport
        
        export = db.query(ZoteroConversationExport).filter(
            ZoteroConversationExport.id == export_id,
            ZoteroConversationExport.user_id == current_user.id
        ).first()
        
        if not export:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export not found"
            )
        
        # Update download count
        export.download_count += 1
        export.last_downloaded = func.now()
        db.commit()
        
        return {
            "export_id": export.id,
            "conversation_id": export.conversation_id,
            "export_format": export.export_format,
            "citation_style": export.citation_style,
            "export_data": export.export_data,
            "created_at": export.created_at.isoformat(),
            "download_count": export.download_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get export: {str(e)}"
        )