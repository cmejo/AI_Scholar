"""
Zotero Group Library API Endpoints

Provides REST API endpoints for group library management, permissions, and synchronization.
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from services.auth_service import get_current_user
from services.zotero.zotero_group_library_service import ZoteroGroupLibraryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zotero/groups", tags=["zotero-groups"])


# Pydantic models for request/response
class GroupLibraryResponse(BaseModel):
    id: str
    zotero_library_id: str
    name: str
    description: Optional[str] = None
    is_public: bool
    member_count: int
    user_role: str
    user_permissions: Dict[str, Any]
    sync_enabled: bool
    last_sync_at: Optional[str] = None
    created_at: str


class GroupMemberResponse(BaseModel):
    id: str
    user_id: str
    zotero_user_id: str
    role: str
    permissions: Dict[str, Any]
    join_date: str
    last_activity: Optional[str] = None
    invitation_status: str


class UpdateMemberPermissionsRequest(BaseModel):
    role: str = Field(..., description="New role for the member")
    permissions: Dict[str, Any] = Field(default_factory=dict, description="Specific permissions")


class GroupSyncSettingsResponse(BaseModel):
    sync_enabled: bool
    sync_frequency_minutes: int
    sync_collections: bool
    sync_items: bool
    sync_attachments: bool
    sync_annotations: bool
    auto_resolve_conflicts: bool
    conflict_resolution_strategy: str
    last_sync_at: Optional[str] = None


class UpdateSyncSettingsRequest(BaseModel):
    sync_enabled: Optional[bool] = None
    sync_frequency_minutes: Optional[int] = None
    sync_collections: Optional[bool] = None
    sync_items: Optional[bool] = None
    sync_attachments: Optional[bool] = None
    sync_annotations: Optional[bool] = None
    auto_resolve_conflicts: Optional[bool] = None
    conflict_resolution_strategy: Optional[str] = None


class GroupActivityResponse(BaseModel):
    id: str
    user_id: str
    activity_type: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    description: str
    created_at: str


class PermissionTemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    permissions: Dict[str, Any]
    is_default: bool


@router.post("/import", response_model=Dict[str, Any])
async def import_group_libraries(
    connection_id: str = Query(..., description="Zotero connection ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import all accessible group libraries for the current user"""
    try:
        service = ZoteroGroupLibraryService(db)
        result = await service.import_group_libraries(connection_id, current_user["id"])
        
        return {
            "success": True,
            "message": f"Imported {result['imported_count']} group libraries",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to import group libraries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[GroupLibraryResponse])
async def get_user_group_libraries(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all group libraries accessible to the current user"""
    try:
        service = ZoteroGroupLibraryService(db)
        libraries = await service.get_user_group_libraries(current_user["id"])
        
        return [GroupLibraryResponse(**lib) for lib in libraries]
        
    except Exception as e:
        logger.error(f"Failed to get user group libraries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{library_id}/members", response_model=List[GroupMemberResponse])
async def get_group_members(
    library_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get members of a specific group library"""
    try:
        service = ZoteroGroupLibraryService(db)
        members = await service.get_group_members(library_id, current_user["id"])
        
        return [GroupMemberResponse(**member) for member in members]
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get group members: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{library_id}/members/{member_id}/permissions", response_model=Dict[str, Any])
async def update_member_permissions(
    library_id: str,
    member_id: str,
    request: UpdateMemberPermissionsRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a group member's role and permissions"""
    try:
        service = ZoteroGroupLibraryService(db)
        result = await service.update_member_permissions(
            library_id, member_id, request.role, request.permissions, current_user["id"]
        )
        
        return {
            "success": True,
            "message": "Member permissions updated successfully",
            "data": result
        }
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update member permissions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{library_id}/sync-settings", response_model=GroupSyncSettingsResponse)
async def get_group_sync_settings(
    library_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sync settings for a group library"""
    try:
        service = ZoteroGroupLibraryService(db)
        settings = await service.get_group_sync_settings(library_id, current_user["id"])
        
        return GroupSyncSettingsResponse(**settings)
        
    except Exception as e:
        logger.error(f"Failed to get group sync settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{library_id}/sync-settings", response_model=GroupSyncSettingsResponse)
async def update_group_sync_settings(
    library_id: str,
    request: UpdateSyncSettingsRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update sync settings for a group library"""
    try:
        service = ZoteroGroupLibraryService(db)
        
        # Convert request to dict, excluding None values
        settings_data = {k: v for k, v in request.dict().items() if v is not None}
        
        settings = await service.update_group_sync_settings(
            library_id, current_user["id"], settings_data
        )
        
        return GroupSyncSettingsResponse(**settings)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update group sync settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{library_id}/activity", response_model=List[GroupActivityResponse])
async def get_group_activity_log(
    library_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of activities to return"),
    offset: int = Query(0, ge=0, description="Number of activities to skip"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get activity log for a group library"""
    try:
        service = ZoteroGroupLibraryService(db)
        activities = await service.get_group_activity_log(
            library_id, current_user["id"], limit, offset
        )
        
        return [GroupActivityResponse(**activity) for activity in activities]
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get group activity log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/permission-templates", response_model=List[PermissionTemplateResponse])
async def get_permission_templates(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available permission templates"""
    try:
        service = ZoteroGroupLibraryService(db)
        templates = await service.get_permission_templates()
        
        return [PermissionTemplateResponse(**template) for template in templates]
        
    except Exception as e:
        logger.error(f"Failed to get permission templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{library_id}/sync", response_model=Dict[str, Any])
async def sync_group_library(
    library_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger sync for a specific group library"""
    try:
        service = ZoteroGroupLibraryService(db)
        result = await service.sync_group_library(library_id, current_user["id"])
        
        return {
            "success": True,
            "message": "Group library sync initiated",
            "data": result
        }
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to sync group library: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{library_id}/permissions/check")
async def check_user_permissions(
    library_id: str,
    permission: str = Query(..., description="Permission to check"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if user has specific permission for a group library"""
    try:
        service = ZoteroGroupLibraryService(db)
        has_permission = await service._check_permission(
            library_id, current_user["id"], permission
        )
        
        return {
            "user_id": current_user["id"],
            "library_id": library_id,
            "permission": permission,
            "has_permission": has_permission
        }
        
    except Exception as e:
        logger.error(f"Failed to check user permissions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))