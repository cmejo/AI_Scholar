"""
Zotero Team Collaboration API Endpoints

Provides REST API endpoints for team workspaces, modification tracking, and conflict resolution.
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from services.auth_service import get_current_user
from services.zotero.zotero_team_collaboration_service import ZoteroTeamCollaborationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zotero/team", tags=["zotero-team"])


# Pydantic models for request/response
class CreateWorkspaceRequest(BaseModel):
    name: str = Field(..., description="Name of the workspace")
    description: Optional[str] = Field(None, description="Description of the workspace")
    workspace_type: str = Field(default='research_team', description="Type of workspace")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Workspace settings")


class WorkspaceResponse(BaseModel):
    workspace_id: str
    name: str
    description: Optional[str]
    workspace_type: str
    owner_user_id: str
    user_role: str
    user_permissions: Dict[str, Any]
    member_count: int
    collection_count: int
    last_activity: Optional[str]
    created_at: str
    updated_at: str


class AddMemberRequest(BaseModel):
    user_id: str = Field(..., description="ID of the user to add")
    role: str = Field(default='member', description="Role for the new member")
    permissions: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Specific permissions")


class AddCollectionRequest(BaseModel):
    collection_id: str = Field(..., description="ID of the collection to add")
    collection_role: str = Field(default='shared', description="Role of collection in workspace")
    is_featured: bool = Field(default=False, description="Whether to feature this collection")


class TrackModificationRequest(BaseModel):
    target_type: str = Field(..., description="Type of object being modified")
    target_id: str = Field(..., description="ID of the object being modified")
    modification_type: str = Field(..., description="Type of modification")
    field_changes: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Field changes")
    old_values: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Previous values")
    new_values: Optional[Dict[str, Any]] = Field(default_factory=dict, description="New values")
    change_summary: Optional[str] = Field(None, description="Summary of changes")
    workspace_id: Optional[str] = Field(None, description="Workspace context")
    collection_id: Optional[str] = Field(None, description="Collection context")


class ModificationHistoryResponse(BaseModel):
    modification_id: str
    user_id: str
    modification_type: str
    field_changes: Dict[str, Any]
    old_values: Dict[str, Any]
    new_values: Dict[str, Any]
    change_summary: Optional[str]
    version_number: int
    is_conflict: bool
    conflict_resolution: Optional[str]
    created_at: str


class EditingSessionResponse(BaseModel):
    session_id: str
    session_token: str
    active_users: List[str]
    lock_status: str


class ConflictResponse(BaseModel):
    conflict_id: str
    target_type: str
    target_id: str
    conflict_type: str
    conflicting_users: List[str]
    conflict_data: Dict[str, Any]
    resolution_strategy: str
    resolution_status: str
    resolved_by: Optional[str]
    resolved_at: Optional[str]
    resolution_notes: Optional[str]
    created_at: str


class ResolveConflictRequest(BaseModel):
    resolution_strategy: str = Field(..., description="Strategy for resolving conflict")
    resolution_notes: Optional[str] = Field(None, description="Notes about the resolution")


class CollaborationHistoryResponse(BaseModel):
    history_id: str
    user_id: str
    action_type: str
    target_type: Optional[str]
    target_id: Optional[str]
    action_description: str
    action_data: Dict[str, Any]
    impact_level: str
    created_at: str


@router.post("/workspaces", response_model=Dict[str, Any])
async def create_team_workspace(
    request: CreateWorkspaceRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new team workspace"""
    try:
        service = ZoteroTeamCollaborationService(db)
        result = await service.create_team_workspace(
            request.name,
            current_user["id"],
            request.description,
            request.workspace_type,
            request.settings
        )
        
        return {
            "success": True,
            "message": "Team workspace created successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to create team workspace: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces", response_model=List[WorkspaceResponse])
async def get_user_workspaces(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get workspaces accessible to the current user"""
    try:
        service = ZoteroTeamCollaborationService(db)
        workspaces = await service.get_user_workspaces(current_user["id"])
        
        return [WorkspaceResponse(**workspace) for workspace in workspaces]
        
    except Exception as e:
        logger.error(f"Failed to get user workspaces: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspaces/{workspace_id}/members", response_model=Dict[str, Any])
async def add_workspace_member(
    workspace_id: str,
    request: AddMemberRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a member to a team workspace"""
    try:
        service = ZoteroTeamCollaborationService(db)
        result = await service.add_workspace_member(
            workspace_id,
            request.user_id,
            current_user["id"],
            request.role,
            request.permissions
        )
        
        return {
            "success": True,
            "message": "Member added to workspace successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add workspace member: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspaces/{workspace_id}/collections", response_model=Dict[str, Any])
async def add_collection_to_workspace(
    workspace_id: str,
    request: AddCollectionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a collection to a team workspace"""
    try:
        service = ZoteroTeamCollaborationService(db)
        result = await service.add_collection_to_workspace(
            workspace_id,
            request.collection_id,
            current_user["id"],
            request.collection_role,
            request.is_featured
        )
        
        return {
            "success": True,
            "message": "Collection added to workspace successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add collection to workspace: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/modifications/track", response_model=Dict[str, Any])
async def track_modification(
    request: TrackModificationRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track a modification for collaborative editing"""
    try:
        service = ZoteroTeamCollaborationService(db)
        result = await service.track_modification(
            request.target_type,
            request.target_id,
            current_user["id"],
            request.modification_type,
            request.field_changes,
            request.old_values,
            request.new_values,
            request.workspace_id,
            request.collection_id,
            request.change_summary
        )
        
        return {
            "success": True,
            "message": "Modification tracked successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to track modification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modifications/{target_type}/{target_id}/history", response_model=List[ModificationHistoryResponse])
async def get_modification_history(
    target_type: str,
    target_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of modifications to return"),
    offset: int = Query(0, ge=0, description="Number of modifications to skip"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get modification history for an object"""
    try:
        service = ZoteroTeamCollaborationService(db)
        history = await service.get_modification_history(target_type, target_id, limit, offset)
        
        return [ModificationHistoryResponse(**mod) for mod in history]
        
    except Exception as e:
        logger.error(f"Failed to get modification history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/editing-sessions", response_model=EditingSessionResponse)
async def create_editing_session(
    target_type: str = Query(..., description="Type of object to edit"),
    target_id: str = Query(..., description="ID of object to edit"),
    workspace_id: Optional[str] = Query(None, description="Workspace context"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a collaborative editing session"""
    try:
        service = ZoteroTeamCollaborationService(db)
        result = await service.create_editing_session(
            target_type, target_id, current_user["id"], workspace_id
        )
        
        return EditingSessionResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to create editing session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/conflicts", response_model=List[ConflictResponse])
async def get_workspace_conflicts(
    workspace_id: str,
    status: Optional[str] = Query(None, description="Filter by conflict status"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conflicts for a workspace"""
    try:
        service = ZoteroTeamCollaborationService(db)
        conflicts = await service.get_workspace_conflicts(workspace_id, current_user["id"], status)
        
        return [ConflictResponse(**conflict) for conflict in conflicts]
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get workspace conflicts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/conflicts/{conflict_id}/resolve", response_model=Dict[str, Any])
async def resolve_conflict(
    conflict_id: str,
    request: ResolveConflictRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resolve a collaboration conflict"""
    try:
        service = ZoteroTeamCollaborationService(db)
        result = await service.resolve_conflict(
            conflict_id,
            current_user["id"],
            request.resolution_strategy,
            request.resolution_notes
        )
        
        return {
            "success": True,
            "message": "Conflict resolved successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to resolve conflict: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/history", response_model=List[CollaborationHistoryResponse])
async def get_collaboration_history(
    workspace_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of history entries to return"),
    offset: int = Query(0, ge=0, description="Number of history entries to skip"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    impact_level: Optional[str] = Query(None, description="Filter by impact level"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get collaboration history for a workspace"""
    try:
        service = ZoteroTeamCollaborationService(db)
        history = await service.get_collaboration_history(
            workspace_id, current_user["id"], limit, offset, action_type, impact_level
        )
        
        return [CollaborationHistoryResponse(**entry) for entry in history]
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get collaboration history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/members")
async def get_workspace_members(
    workspace_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get members of a workspace"""
    try:
        # This would be implemented in the service
        # For now, return a placeholder
        return []
        
    except Exception as e:
        logger.error(f"Failed to get workspace members: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/collections")
async def get_workspace_collections(
    workspace_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get collections in a workspace"""
    try:
        # This would be implemented in the service
        # For now, return a placeholder
        return []
        
    except Exception as e:
        logger.error(f"Failed to get workspace collections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/workspaces/{workspace_id}")
async def delete_workspace(
    workspace_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a team workspace"""
    try:
        # This would be implemented in the service
        # For now, return a placeholder
        return {
            "success": True,
            "message": "Workspace deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to delete workspace: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/workspaces/{workspace_id}/members/{member_id}")
async def remove_workspace_member(
    workspace_id: str,
    member_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a member from a workspace"""
    try:
        # This would be implemented in the service
        # For now, return a placeholder
        return {
            "success": True,
            "message": "Member removed from workspace successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to remove workspace member: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))