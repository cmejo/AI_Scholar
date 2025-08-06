"""
Interactive Content Version Control API Endpoints for AI Scholar Advanced RAG System

This module provides REST API endpoints for version control of interactive content
including notebooks, visualizations, and other interactive elements.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from services.interactive_content_version_control import (
    interactive_content_version_control,
    ContentType,
    MergeStatus,
    ContentVersion,
    ContentDiff,
    Branch,
    MergeRequest,
    BackupRecord
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/content/version-control", tags=["content-version-control"])

# Pydantic models for API requests/responses

class InitializeVersioningRequest(BaseModel):
    content_type: str = Field(..., description="Type of content (notebook, visualization, dataset, script)")
    initial_data: Dict[str, Any] = Field(..., description="Initial content data")
    commit_message: str = Field(default="Initial version", description="Initial commit message")

class CommitChangesRequest(BaseModel):
    updated_data: Dict[str, Any] = Field(..., description="Updated content data")
    commit_message: str = Field(..., description="Commit message")
    branch_name: str = Field(default="main", description="Branch name")

class CreateBranchRequest(BaseModel):
    branch_name: str = Field(..., description="Name of the new branch")
    from_version: str = Field(..., description="Version ID to branch from")
    description: str = Field(default="", description="Branch description")

class MergeBranchesRequest(BaseModel):
    source_branch: str = Field(..., description="Source branch name")
    target_branch: str = Field(..., description="Target branch name")
    merge_message: str = Field(..., description="Merge commit message")

class RevertToVersionRequest(BaseModel):
    version_id: str = Field(..., description="Version ID to revert to")
    branch_name: str = Field(default="main", description="Branch to revert in")

class CreateBackupRequest(BaseModel):
    backup_type: str = Field(default="manual", description="Type of backup")

class RestoreFromBackupRequest(BaseModel):
    backup_id: str = Field(..., description="Backup ID to restore from")

# Response models
class ContentVersionResponse(BaseModel):
    version_id: str
    content_id: str
    content_type: str
    version_number: int
    commit_hash: str
    author_id: str
    commit_message: str
    created_at: str
    parent_versions: List[str]
    tags: List[str]
    metadata: Dict[str, Any]

class ContentDiffResponse(BaseModel):
    diff_id: str
    from_version: str
    to_version: str
    content_id: str
    changes: List[Dict[str, Any]]
    summary: Dict[str, int]
    created_at: str

class BranchResponse(BaseModel):
    branch_id: str
    content_id: str
    branch_name: str
    head_version: str
    created_from: str
    created_by: str
    created_at: str
    is_active: bool
    description: str

class MergeRequestResponse(BaseModel):
    merge_id: str
    content_id: str
    source_branch: str
    target_branch: str
    title: str
    description: str
    author_id: str
    status: str
    conflicts: List[Dict[str, Any]]
    created_at: str
    merged_at: Optional[str] = None
    merged_by: Optional[str] = None

class BackupRecordResponse(BaseModel):
    backup_id: str
    content_id: str
    backup_type: str
    version_snapshot: str
    created_at: str
    retention_until: str

# Dependency for user authentication (simplified)
async def get_current_user() -> str:
    """Get current user ID - simplified implementation"""
    # In production, this would validate JWT tokens and return user info
    return "user_123"

@router.post("/{content_id}/initialize", response_model=ContentVersionResponse)
async def initialize_content_versioning(
    content_id: str,
    request: InitializeVersioningRequest,
    current_user: str = Depends(get_current_user)
):
    """Initialize version control for new content"""
    try:
        # Validate content type
        try:
            content_type = ContentType(request.content_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported content type: {request.content_type}"
            )
        
        # Initialize versioning
        version = await interactive_content_version_control.initialize_content_versioning(
            content_id=content_id,
            content_type=content_type,
            initial_data=request.initial_data,
            author_id=current_user,
            commit_message=request.commit_message
        )
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize version control"
            )
        
        return ContentVersionResponse(
            version_id=version.version_id,
            content_id=version.content_id,
            content_type=version.content_type.value,
            version_number=version.version_number,
            commit_hash=version.commit_hash,
            author_id=version.author_id,
            commit_message=version.commit_message,
            created_at=version.created_at.isoformat(),
            parent_versions=version.parent_versions,
            tags=version.tags,
            metadata=version.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing version control for {content_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize version control: {str(e)}"
        )

@router.post("/{content_id}/commit", response_model=ContentVersionResponse)
async def commit_changes(
    content_id: str,
    request: CommitChangesRequest,
    current_user: str = Depends(get_current_user)
):
    """Commit changes to content"""
    try:
        version = await interactive_content_version_control.commit_changes(
            content_id=content_id,
            updated_data=request.updated_data,
            author_id=current_user,
            commit_message=request.commit_message,
            branch_name=request.branch_name
        )
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found or no changes detected"
            )
        
        return ContentVersionResponse(
            version_id=version.version_id,
            content_id=version.content_id,
            content_type=version.content_type.value,
            version_number=version.version_number,
            commit_hash=version.commit_hash,
            author_id=version.author_id,
            commit_message=version.commit_message,
            created_at=version.created_at.isoformat(),
            parent_versions=version.parent_versions,
            tags=version.tags,
            metadata=version.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error committing changes to {content_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to commit changes: {str(e)}"
        )

@router.get("/{content_id}/history", response_model=List[ContentVersionResponse])
async def get_version_history(
    content_id: str,
    branch_name: Optional[str] = None,
    current_user: str = Depends(get_current_user)
):
    """Get version history for content"""
    try:
        versions = await interactive_content_version_control.get_version_history(
            content_id=content_id,
            branch_name=branch_name
        )
        
        return [
            ContentVersionResponse(
                version_id=version.version_id,
                content_id=version.content_id,
                content_type=version.content_type.value,
                version_number=version.version_number,
                commit_hash=version.commit_hash,
                author_id=version.author_id,
                commit_message=version.commit_message,
                created_at=version.created_at.isoformat(),
                parent_versions=version.parent_versions,
                tags=version.tags,
                metadata=version.metadata
            )
            for version in versions
        ]
        
    except Exception as e:
        logger.error(f"Error getting version history for {content_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get version history: {str(e)}"
        )

@router.get("/{content_id}/diff/{from_version}/{to_version}", response_model=ContentDiffResponse)
async def get_version_diff(
    content_id: str,
    from_version: str,
    to_version: str,
    current_user: str = Depends(get_current_user)
):
    """Generate diff between two versions"""
    try:
        diff = await interactive_content_version_control.get_version_diff(
            content_id=content_id,
            from_version=from_version,
            to_version=to_version
        )
        
        if not diff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Versions not found or diff generation failed"
            )
        
        return ContentDiffResponse(
            diff_id=diff.diff_id,
            from_version=diff.from_version,
            to_version=diff.to_version,
            content_id=diff.content_id,
            changes=diff.changes,
            summary=diff.summary,
            created_at=diff.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating diff for {content_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate diff: {str(e)}"
        )

@router.post("/{content_id}/branches", response_model=BranchResponse)
async def create_branch(
    content_id: str,
    request: CreateBranchRequest,
    current_user: str = Depends(get_current_user)
):
    """Create a new branch from a specific version"""
    try:
        branch = await interactive_content_version_control.create_branch(
            content_id=content_id,
            branch_name=request.branch_name,
            from_version=request.from_version,
            author_id=current_user,
            description=request.description
        )
        
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create branch - branch may already exist or version not found"
            )
        
        return BranchResponse(
            branch_id=branch.branch_id,
            content_id=branch.content_id,
            branch_name=branch.branch_name,
            head_version=branch.head_version,
            created_from=branch.created_from,
            created_by=branch.created_by,
            created_at=branch.created_at.isoformat(),
            is_active=branch.is_active,
            description=branch.description
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating branch for {content_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create branch: {str(e)}"
        )

@router.get("/{content_id}/branches", response_model=List[BranchResponse])
async def get_content_branches(
    content_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get all branches for content"""
    try:
        branches = await interactive_content_version_control.get_content_branches(content_id)
        
        return [
            BranchResponse(
                branch_id=branch.branch_id,
                content_id=branch.content_id,
                branch_name=branch.branch_name,
                head_version=branch.head_version,
                created_from=branch.created_from,
                created_by=branch.created_by,
                created_at=branch.created_at.isoformat(),
                is_active=branch.is_active,
                description=branch.description
            )
            for branch in branches
        ]
        
    except Exception as e:
        logger.error(f"Error getting branches for {content_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get branches: {str(e)}"
        )

@router.post("/{content_id}/merge", response_model=MergeRequestResponse)
async def merge_branches(
    content_id: str,
    request: MergeBranchesRequest,
    current_user: str = Depends(get_current_user)
):
    """Merge one branch into another"""
    try:
        merge_request = await interactive_content_version_control.merge_branches(
            content_id=content_id,
            source_branch=request.source_branch,
            target_branch=request.target_branch,
            author_id=current_user,
            merge_message=request.merge_message
        )
        
        return MergeRequestResponse(
            merge_id=merge_request.merge_id,
            content_id=merge_request.content_id,
            source_branch=merge_request.source_branch,
            target_branch=merge_request.target_branch,
            title=merge_request.title,
            description=merge_request.description,
            author_id=merge_request.author_id,
            status=merge_request.status.value,
            conflicts=merge_request.conflicts,
            created_at=merge_request.created_at.isoformat(),
            merged_at=merge_request.merged_at.isoformat() if merge_request.merged_at else None,
            merged_by=merge_request.merged_by
        )
        
    except Exception as e:
        logger.error(f"Error merging branches for {content_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to merge branches: {str(e)}"
        )

@router.get("/{content_id}/merge-requests", response_model=List[MergeRequestResponse])
async def get_merge_requests(
    content_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get merge requests for content"""
    try:
        merge_requests = await interactive_content_version_control.get_merge_requests(content_id)
        
        return [
            MergeRequestResponse(
                merge_id=mr.merge_id,
                content_id=mr.content_id,
                source_branch=mr.source_branch,
                target_branch=mr.target_branch,
                title=mr.title,
                description=mr.description,
                author_id=mr.author_id,
                status=mr.status.value,
                conflicts=mr.conflicts,
                created_at=mr.created_at.isoformat(),
                merged_at=mr.merged_at.isoformat() if mr.merged_at else None,
                merged_by=mr.merged_by
            )
            for mr in merge_requests
        ]
        
    except Exception as e:
        logger.error(f"Error getting merge requests for {content_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get merge requests: {str(e)}"
        )

@router.post("/{content_id}/revert", response_model=ContentVersionResponse)
async def revert_to_version(
    content_id: str,
    request: RevertToVersionRequest,
    current_user: str = Depends(get_current_user)
):
    """Revert content to a specific version"""
    try:
        version = await interactive_content_version_control.revert_to_version(
            content_id=content_id,
            version_id=request.version_id,
            author_id=current_user,
            branch_name=request.branch_name
        )
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found or revert failed"
            )
        
        return ContentVersionResponse(
            version_id=version.version_id,
            content_id=version.content_id,
            content_type=version.content_type.value,
            version_number=version.version_number,
            commit_hash=version.commit_hash,
            author_id=version.author_id,
            commit_message=version.commit_message,
            created_at=version.created_at.isoformat(),
            parent_versions=version.parent_versions,
            tags=version.tags,
            metadata=version.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reverting {content_id} to version: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revert to version: {str(e)}"
        )

@router.post("/{content_id}/backup", response_model=BackupRecordResponse)
async def create_backup(
    content_id: str,
    request: CreateBackupRequest,
    current_user: str = Depends(get_current_user)
):
    """Create manual backup of current content state"""
    try:
        backup = await interactive_content_version_control.create_backup(
            content_id=content_id,
            backup_type=request.backup_type
        )
        
        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found or backup creation failed"
            )
        
        return BackupRecordResponse(
            backup_id=backup.backup_id,
            content_id=backup.content_id,
            backup_type=backup.backup_type,
            version_snapshot=backup.version_snapshot,
            created_at=backup.created_at.isoformat(),
            retention_until=backup.retention_until.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating backup for {content_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create backup: {str(e)}"
        )

@router.get("/{content_id}/backups", response_model=List[BackupRecordResponse])
async def get_backups(
    content_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get backup records for content"""
    try:
        backups = await interactive_content_version_control.get_backups(content_id)
        
        return [
            BackupRecordResponse(
                backup_id=backup.backup_id,
                content_id=backup.content_id,
                backup_type=backup.backup_type,
                version_snapshot=backup.version_snapshot,
                created_at=backup.created_at.isoformat(),
                retention_until=backup.retention_until.isoformat()
            )
            for backup in backups
        ]
        
    except Exception as e:
        logger.error(f"Error getting backups for {content_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backups: {str(e)}"
        )

@router.post("/{content_id}/restore", response_model=ContentVersionResponse)
async def restore_from_backup(
    content_id: str,
    request: RestoreFromBackupRequest,
    current_user: str = Depends(get_current_user)
):
    """Restore content from backup"""
    try:
        version = await interactive_content_version_control.restore_from_backup(
            content_id=content_id,
            backup_id=request.backup_id,
            author_id=current_user
        )
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup not found or restore failed"
            )
        
        return ContentVersionResponse(
            version_id=version.version_id,
            content_id=version.content_id,
            content_type=version.content_type.value,
            version_number=version.version_number,
            commit_hash=version.commit_hash,
            author_id=version.author_id,
            commit_message=version.commit_message,
            created_at=version.created_at.isoformat(),
            parent_versions=version.parent_versions,
            tags=version.tags,
            metadata=version.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring {content_id} from backup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore from backup: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint for version control service"""
    try:
        total_content = len(interactive_content_version_control.versions)
        total_branches = sum(len(branches) for branches in interactive_content_version_control.branches.values())
        total_merges = len(interactive_content_version_control.merge_requests)
        total_backups = sum(len(backups) for backups in interactive_content_version_control.backups.values())
        
        return {
            "status": "healthy",
            "service": "interactive-content-version-control",
            "content_items": total_content,
            "total_branches": total_branches,
            "merge_requests": total_merges,
            "backup_records": total_backups,
            "supported_content_types": [ct.value for ct in ContentType]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Service unhealthy: {str(e)}"
        )