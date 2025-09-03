"""
Zotero Sharing and Export API Endpoints

Provides REST API endpoints for export and sharing capabilities.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..core.database import get_db
from ..services.auth_service import get_current_user
from ..services.zotero.zotero_sharing_service import zotero_sharing_service
from ..models.schemas import User


router = APIRouter(prefix="/api/zotero/sharing", tags=["zotero-sharing"])


# Request/Response Models
class ConversationExportRequest(BaseModel):
    messages: List[Dict[str, Any]]
    format: str = "markdown"
    includeCitations: bool = True
    citationStyle: str = "apa"
    includeMetadata: bool = True
    includeTimestamps: bool = True
    includeReferences: bool = True


class ConversationExportResponse(BaseModel):
    content: str
    filename: str
    mimeType: str


class ShareReferenceRequest(BaseModel):
    referenceId: str
    sharedWith: List[str]
    permissions: Dict[str, bool]
    note: Optional[str] = None


class ShareReferenceResponse(BaseModel):
    id: str
    referenceId: str
    sharedBy: str
    sharedWith: List[str]
    sharedAt: str
    permissions: Dict[str, bool]
    note: Optional[str] = None


class CreateCollectionRequest(BaseModel):
    name: str
    description: str
    referenceIds: List[str]
    isPublic: bool = False
    tags: Optional[List[str]] = None


class CreateCollectionResponse(BaseModel):
    id: str
    name: str
    description: str
    references: List[Dict[str, Any]]
    collaborators: List[Dict[str, Any]]
    isPublic: bool
    createdBy: str
    createdAt: str
    updatedAt: str
    tags: List[str]


class ProjectExportRequest(BaseModel):
    title: str
    description: str
    references: List[Dict[str, Any]] = []
    notes: List[Dict[str, Any]] = []
    format: str = "markdown"
    includeNotes: bool = True
    includeReferences: bool = True
    includeBibliography: bool = True
    citationStyle: str = "apa"


class ProjectExportResponse(BaseModel):
    content: str
    filename: str
    mimeType: str


class ExportFormat(BaseModel):
    id: str
    name: str
    extension: str
    mimeType: str
    description: str


class ShareableLinkRequest(BaseModel):
    collectionId: str
    isPublic: bool
    baseUrl: Optional[str] = None


class ShareableLinkResponse(BaseModel):
    link: str
    collectionId: str
    isPublic: bool
    expiresAt: Optional[str] = None


@router.get("/export-formats", response_model=List[ExportFormat])
async def get_export_formats(
    current_user: User = Depends(get_current_user)
):
    """
    Get available export formats.
    
    Returns a list of supported export formats with their metadata.
    """
    try:
        formats = zotero_sharing_service.get_export_formats()
        return [ExportFormat(**fmt) for fmt in formats]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get export formats: {str(e)}"
        )


@router.post("/export-conversation", response_model=ConversationExportResponse)
async def export_conversation(
    request: ConversationExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export conversation with proper citations.
    
    Exports a conversation in the specified format with optional
    citations, metadata, and reference information.
    """
    try:
        options = {
            'format': request.format,
            'includeCitations': request.includeCitations,
            'citationStyle': request.citationStyle,
            'includeMetadata': request.includeMetadata,
            'includeTimestamps': request.includeTimestamps,
            'includeReferences': request.includeReferences
        }
        
        result = await zotero_sharing_service.export_conversation(
            messages=request.messages,
            options=options,
            user_id=str(current_user.id),
            db=db
        )
        
        return ConversationExportResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export conversation: {str(e)}"
        )


@router.post("/share-reference", response_model=ShareReferenceResponse)
async def share_reference(
    request: ShareReferenceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Share reference with other users.
    
    Creates a sharing record for a reference with specified permissions
    and optional note.
    """
    try:
        result = await zotero_sharing_service.share_reference(
            reference_id=request.referenceId,
            shared_with=request.sharedWith,
            permissions=request.permissions,
            user_id=str(current_user.id),
            db=db,
            note=request.note
        )
        
        return ShareReferenceResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to share reference: {str(e)}"
        )


@router.post("/create-collection", response_model=CreateCollectionResponse)
async def create_reference_collection(
    request: CreateCollectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a reference collection.
    
    Creates a new collection of references that can be shared
    with other users or made public.
    """
    try:
        result = await zotero_sharing_service.create_reference_collection(
            name=request.name,
            description=request.description,
            reference_ids=request.referenceIds,
            user_id=str(current_user.id),
            db=db,
            is_public=request.isPublic,
            tags=request.tags
        )
        
        return CreateCollectionResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create collection: {str(e)}"
        )


@router.post("/export-project", response_model=ProjectExportResponse)
async def export_research_project(
    request: ProjectExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export research project.
    
    Exports a complete research project including references,
    notes, and bibliography in the specified format.
    """
    try:
        project_data = {
            'title': request.title,
            'description': request.description,
            'references': request.references,
            'notes': request.notes
        }
        
        options = {
            'format': request.format,
            'includeNotes': request.includeNotes,
            'includeReferences': request.includeReferences,
            'includeBibliography': request.includeBibliography,
            'citationStyle': request.citationStyle
        }
        
        result = await zotero_sharing_service.export_project(
            project_data=project_data,
            options=options,
            user_id=str(current_user.id),
            db=db
        )
        
        return ProjectExportResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export project: {str(e)}"
        )


@router.post("/generate-link", response_model=ShareableLinkResponse)
async def generate_shareable_link(
    request: ShareableLinkRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate shareable link for collection.
    
    Creates a shareable link for a reference collection that can be
    used to share the collection with others.
    """
    try:
        base_url = request.baseUrl or "https://ai-scholar.com"
        
        link = zotero_sharing_service.generate_shareable_link(
            collection_id=request.collectionId,
            is_public=request.isPublic,
            base_url=base_url
        )
        
        # Set expiration for private links (30 days)
        expires_at = None
        if not request.isPublic:
            from datetime import datetime, timedelta
            expires_at = (datetime.now() + timedelta(days=30)).isoformat()
        
        return ShareableLinkResponse(
            link=link,
            collectionId=request.collectionId,
            isPublic=request.isPublic,
            expiresAt=expires_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate shareable link: {str(e)}"
        )


@router.get("/download-export")
async def download_export(
    content: str,
    filename: str,
    mime_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    Download exported content as file.
    
    Utility endpoint to download exported content with proper
    headers for file download.
    """
    try:
        return Response(
            content=content,
            media_type=mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": mime_type
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download export: {str(e)}"
        )


@router.get("/collection/{collection_id}")
async def get_shared_collection(
    collection_id: str,
    token: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get shared collection.
    
    Retrieves a shared collection by ID. For private collections,
    requires a valid token or user authentication.
    """
    try:
        # In a real implementation, this would:
        # 1. Check if collection exists
        # 2. Verify access permissions
        # 3. Return collection data
        
        # Placeholder response
        return {
            "id": collection_id,
            "name": "Shared Collection",
            "description": "A shared reference collection",
            "references": [],
            "isPublic": token is None,
            "accessGranted": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get shared collection: {str(e)}"
        )


@router.post("/validate-share-permissions")
async def validate_share_permissions(
    reference_id: str,
    target_users: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate sharing permissions.
    
    Checks if the current user has permission to share a reference
    with the specified target users.
    """
    try:
        # In a real implementation, this would:
        # 1. Check if reference exists and user owns it
        # 2. Validate target users exist
        # 3. Check sharing policies
        
        # Placeholder validation
        validation_results = []
        for user in target_users:
            validation_results.append({
                "userId": user,
                "canShare": True,
                "reason": "User exists and sharing is allowed"
            })
        
        return {
            "referenceId": reference_id,
            "validationResults": validation_results,
            "overallValid": all(r["canShare"] for r in validation_results)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate share permissions: {str(e)}"
        )


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for sharing service"""
    return {"status": "healthy", "service": "zotero-sharing"}