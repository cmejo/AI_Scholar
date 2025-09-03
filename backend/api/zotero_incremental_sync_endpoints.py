"""
FastAPI endpoints for Zotero incremental synchronization functionality - Task 3.2
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from services.zotero.zotero_sync_service import ZoteroLibrarySyncService
from models.zotero_schemas import SyncType, SyncStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zotero/sync", tags=["zotero-sync"])

# Global service instance
sync_service = ZoteroLibrarySyncService()


class IncrementalSyncRequest(BaseModel):
    """Request schema for incremental sync"""
    connection_id: str
    library_ids: Optional[List[str]] = None
    force_full_sync: bool = False


class IncrementalSyncResponse(BaseModel):
    """Response schema for incremental sync"""
    sync_id: str
    status: str
    message: str
    progress_url: str


class ConflictDetectionResponse(BaseModel):
    """Response schema for conflict detection"""
    has_conflicts: bool
    total_conflicts: int
    conflict_types: Dict[str, int]
    libraries: List[Dict[str, Any]]


class ConflictResolutionRequest(BaseModel):
    """Request schema for conflict resolution"""
    connection_id: str
    resolution_strategy: str = "zotero_wins"  # zotero_wins, local_wins, merge
    library_ids: Optional[List[str]] = None


@router.post("/incremental", response_model=IncrementalSyncResponse)
async def start_incremental_sync(
    request: IncrementalSyncRequest,
    background_tasks: BackgroundTasks
):
    """
    Start an incremental synchronization operation
    
    This endpoint initiates incremental sync that only processes items
    that have changed since the last sync, making it much faster than
    full sync for large libraries.
    """
    try:
        # Start the sync in the background
        background_tasks.add_task(
            _run_incremental_sync,
            request.connection_id,
            request.library_ids,
            request.force_full_sync
        )
        
        # Generate sync ID for tracking
        sync_id = f"incremental_{request.connection_id}_{int(datetime.now().timestamp())}"
        
        return IncrementalSyncResponse(
            sync_id=sync_id,
            status="started",
            message="Incremental sync started successfully",
            progress_url=f"/api/zotero/sync/progress/{sync_id}"
        )
        
    except Exception as e:
        logger.error(f"Failed to start incremental sync: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start incremental sync: {str(e)}"
        )


@router.get("/progress/{sync_id}")
async def get_sync_progress(sync_id: str) -> Dict[str, Any]:
    """
    Get progress information for an active sync operation
    
    Returns detailed progress information including:
    - Current status and completion percentage
    - Items processed, added, updated, deleted
    - Error count and recent errors
    - Estimated completion time
    """
    try:
        progress = sync_service.get_sync_progress(sync_id)
        
        if not progress:
            raise HTTPException(
                status_code=404,
                detail=f"Sync {sync_id} not found or has completed"
            )
        
        return progress
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sync progress: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sync progress: {str(e)}"
        )


@router.get("/active")
async def get_active_syncs() -> List[Dict[str, Any]]:
    """
    Get all currently active sync operations
    
    Returns a list of all syncs that are currently in progress,
    including their progress information.
    """
    try:
        active_syncs = sync_service.get_active_syncs()
        return active_syncs
        
    except Exception as e:
        logger.error(f"Failed to get active syncs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get active syncs: {str(e)}"
        )


@router.post("/detect-conflicts/{connection_id}", response_model=ConflictDetectionResponse)
async def detect_sync_conflicts(
    connection_id: str,
    library_ids: Optional[List[str]] = None
):
    """
    Detect potential sync conflicts before performing sync
    
    This endpoint analyzes the differences between local and remote
    library versions to identify potential conflicts that would occur
    during synchronization.
    """
    try:
        conflicts = await sync_service.detect_sync_conflicts(
            connection_id=connection_id,
            library_ids=library_ids
        )
        
        return ConflictDetectionResponse(
            has_conflicts=conflicts["has_conflicts"],
            total_conflicts=conflicts["total_conflicts"],
            conflict_types=conflicts["conflict_types"],
            libraries=conflicts["libraries"]
        )
        
    except Exception as e:
        logger.error(f"Failed to detect sync conflicts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect sync conflicts: {str(e)}"
        )


@router.post("/resolve-conflicts")
async def resolve_sync_conflicts(
    request: ConflictResolutionRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Resolve sync conflicts using specified strategy
    
    Available strategies:
    - zotero_wins: Accept all changes from Zotero (default)
    - local_wins: Keep local changes (not yet implemented)
    - merge: Attempt to merge changes (not yet implemented)
    """
    try:
        # Start conflict resolution in the background
        background_tasks.add_task(
            _run_conflict_resolution,
            request.connection_id,
            request.resolution_strategy,
            request.library_ids
        )
        
        return {
            "message": f"Conflict resolution started with strategy: {request.resolution_strategy}",
            "strategy": request.resolution_strategy,
            "connection_id": request.connection_id,
            "status": "started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start conflict resolution: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start conflict resolution: {str(e)}"
        )


@router.get("/conflicts/preview/{connection_id}")
async def preview_conflict_resolution(
    connection_id: str,
    strategy: str = "zotero_wins",
    library_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Preview what would happen during conflict resolution
    
    This endpoint shows what changes would be made without actually
    performing the resolution, allowing users to understand the
    impact before proceeding.
    """
    try:
        # First detect conflicts
        conflicts = await sync_service.detect_sync_conflicts(
            connection_id=connection_id,
            library_ids=library_ids
        )
        
        if not conflicts["has_conflicts"]:
            return {
                "has_conflicts": False,
                "message": "No conflicts detected",
                "preview": None
            }
        
        # Generate preview based on strategy
        preview = {
            "strategy": strategy,
            "total_changes": conflicts["total_conflicts"],
            "changes_by_type": conflicts["conflict_types"],
            "libraries_affected": len(conflicts["libraries"]),
            "detailed_changes": []
        }
        
        for library in conflicts["libraries"]:
            library_preview = {
                "library_name": library["library_name"],
                "changes": []
            }
            
            for conflict in library["conflicts"]:
                if strategy == "zotero_wins":
                    if conflict["type"] == "version_mismatch":
                        library_preview["changes"].append({
                            "action": "update_library_version",
                            "description": f"Update library version to {conflict['remote_version']}"
                        })
                    elif conflict["type"] == "modified_item":
                        library_preview["changes"].append({
                            "action": "update_item",
                            "description": f"Update item: {conflict['item_title']}"
                        })
                    elif conflict["type"] == "deleted_item":
                        library_preview["changes"].append({
                            "action": "delete_item",
                            "description": f"Mark item as deleted: {conflict['item_title']}"
                        })
                elif strategy == "local_wins":
                    library_preview["changes"].append({
                        "action": "keep_local",
                        "description": f"Keep local version (strategy not implemented)"
                    })
                elif strategy == "merge":
                    library_preview["changes"].append({
                        "action": "merge",
                        "description": f"Merge changes (strategy not implemented)"
                    })
            
            preview["detailed_changes"].append(library_preview)
        
        return {
            "has_conflicts": True,
            "message": f"Preview for {strategy} strategy",
            "preview": preview
        }
        
    except Exception as e:
        logger.error(f"Failed to preview conflict resolution: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to preview conflict resolution: {str(e)}"
        )


@router.get("/status/{connection_id}")
async def get_sync_status(connection_id: str) -> Dict[str, Any]:
    """
    Get overall sync status for a connection
    
    Returns information about the last sync, current sync state,
    and any pending conflicts or issues.
    """
    try:
        # This would typically query the database for sync logs
        # For now, return basic status information
        return {
            "connection_id": connection_id,
            "last_sync": None,  # Would be populated from database
            "sync_enabled": True,
            "has_pending_conflicts": False,
            "active_sync": None,
            "message": "Sync status endpoint - implementation pending"
        }
        
    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sync status: {str(e)}"
        )


async def _run_incremental_sync(
    connection_id: str,
    library_ids: Optional[List[str]] = None,
    force_full_sync: bool = False
):
    """
    Background task to run incremental sync
    
    This function runs the actual sync operation in the background
    and handles any errors that occur during the process.
    """
    try:
        if force_full_sync:
            # Use full import instead of incremental sync
            progress = await sync_service.import_library(
                connection_id=connection_id,
                library_ids=library_ids
            )
        else:
            progress = await sync_service.incremental_sync(
                connection_id=connection_id,
                library_ids=library_ids
            )
        
        logger.info(f"Incremental sync completed: {progress.get_progress_dict()}")
        
    except Exception as e:
        logger.error(f"Background incremental sync failed: {e}")


async def _run_conflict_resolution(
    connection_id: str,
    resolution_strategy: str,
    library_ids: Optional[List[str]] = None
):
    """
    Background task to run conflict resolution
    
    This function runs the actual conflict resolution in the background
    and handles any errors that occur during the process.
    """
    try:
        result = await sync_service.resolve_sync_conflicts(
            connection_id=connection_id,
            resolution_strategy=resolution_strategy,
            library_ids=library_ids
        )
        
        logger.info(f"Conflict resolution completed: {result}")
        
    except Exception as e:
        logger.error(f"Background conflict resolution failed: {e}")


# Additional utility endpoints for development and testing

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for the sync service"""
    return {
        "status": "healthy",
        "service": "zotero-incremental-sync",
        "version": "1.0.0"
    }


@router.get("/stats")
async def get_sync_stats() -> Dict[str, Any]:
    """Get statistics about sync operations"""
    try:
        active_syncs = sync_service.get_active_syncs()
        
        return {
            "active_syncs_count": len(active_syncs),
            "active_syncs": [
                {
                    "sync_id": sync["sync_id"],
                    "sync_type": sync["sync_type"],
                    "status": sync["status"],
                    "items_processed": sync["progress"]["items_processed"],
                    "items_added": sync["progress"]["items_added"],
                    "items_updated": sync["progress"]["items_updated"],
                    "items_deleted": sync["progress"]["items_deleted"]
                }
                for sync in active_syncs
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get sync stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sync stats: {str(e)}"
        )


@router.post("/test-conflict-detection")
async def test_conflict_detection(test_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test conflict detection logic with sample data
    
    This endpoint allows testing the conflict detection algorithms
    with custom test data for development and debugging purposes.
    """
    try:
        # Extract test parameters
        local_version = test_data.get("local_version", 100)
        remote_version = test_data.get("remote_version", 110)
        modified_items = test_data.get("modified_items", [])
        
        # Simple conflict detection logic for testing
        conflicts = {
            "has_conflicts": False,
            "total_conflicts": 0,
            "conflict_types": {
                "version_mismatch": 0,
                "deleted_items": 0,
                "modified_items": 0
            },
            "conflicts": []
        }
        
        # Check version mismatch
        if remote_version > local_version:
            conflicts["has_conflicts"] = True
            conflicts["total_conflicts"] += 1
            conflicts["conflict_types"]["version_mismatch"] = 1
            conflicts["conflicts"].append({
                "type": "version_mismatch",
                "local_version": local_version,
                "remote_version": remote_version
            })
            
            # Check modified items
            for item in modified_items:
                conflicts["total_conflicts"] += 1
                if item.get("deleted", False):
                    conflicts["conflict_types"]["deleted_items"] += 1
                    conflicts["conflicts"].append({
                        "type": "deleted_item",
                        "item_key": item["key"],
                        "item_title": item.get("title", "Untitled")
                    })
                else:
                    conflicts["conflict_types"]["modified_items"] += 1
                    conflicts["conflicts"].append({
                        "type": "modified_item",
                        "item_key": item["key"],
                        "item_title": item.get("title", "Untitled")
                    })
        
        return {
            "test_data": test_data,
            "conflicts": conflicts,
            "test_successful": True
        }
        
    except Exception as e:
        logger.error(f"Conflict detection test failed: {e}")
        return {
            "test_data": test_data,
            "conflicts": None,
            "test_successful": False,
            "error": str(e)
        }