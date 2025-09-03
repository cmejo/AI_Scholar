"""
FastAPI endpoints for Zotero library import functionality - Task 3.1
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from services.zotero.zotero_library_import_service import ZoteroLibraryImportService
from models.zotero_schemas import SyncType, SyncStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zotero/import", tags=["zotero-import"])

# Global service instance
import_service = ZoteroLibraryImportService()


class LibraryImportRequest(BaseModel):
    """Request schema for library import"""
    connection_id: str
    library_ids: Optional[List[str]] = None
    sync_type: SyncType = SyncType.FULL


class LibraryImportResponse(BaseModel):
    """Response schema for library import"""
    import_id: str
    status: str
    message: str
    progress_url: str


@router.post("/start", response_model=LibraryImportResponse)
async def start_library_import(
    request: LibraryImportRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a library import operation
    
    This endpoint initiates the import of Zotero library data and returns
    immediately with an import ID that can be used to track progress.
    """
    try:
        # Start the import in the background
        background_tasks.add_task(
            _run_library_import,
            request.connection_id,
            request.library_ids
        )
        
        # Generate import ID for tracking
        import_id = f"import_{request.connection_id}_{int(datetime.now().timestamp())}"
        
        return LibraryImportResponse(
            import_id=import_id,
            status="started",
            message="Library import started successfully",
            progress_url=f"/api/zotero/import/progress/{import_id}"
        )
        
    except Exception as e:
        logger.error(f"Failed to start library import: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start library import: {str(e)}"
        )


@router.get("/progress/{import_id}")
async def get_import_progress(import_id: str) -> Dict[str, Any]:
    """
    Get progress information for an active import
    
    Returns detailed progress information including:
    - Current status and completion percentage
    - Items processed, added, updated
    - Error count and recent errors
    - Estimated completion time
    """
    try:
        progress = import_service.get_import_progress(import_id)
        
        if not progress:
            raise HTTPException(
                status_code=404,
                detail=f"Import {import_id} not found or has completed"
            )
        
        return progress
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get import progress: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get import progress: {str(e)}"
        )


@router.get("/active")
async def get_active_imports() -> List[Dict[str, Any]]:
    """
    Get all currently active import operations
    
    Returns a list of all imports that are currently in progress,
    including their progress information.
    """
    try:
        active_imports = import_service.get_active_imports()
        return active_imports
        
    except Exception as e:
        logger.error(f"Failed to get active imports: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get active imports: {str(e)}"
        )


@router.post("/cancel/{import_id}")
async def cancel_import(import_id: str) -> Dict[str, str]:
    """
    Cancel an active import operation
    
    Attempts to cancel the specified import. Note that imports that are
    already in progress may not be immediately cancelled.
    """
    try:
        success = await import_service.cancel_import(import_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Import {import_id} not found or already completed"
            )
        
        return {
            "message": f"Import {import_id} cancelled successfully",
            "import_id": import_id,
            "status": "cancelled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel import: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel import: {str(e)}"
        )


@router.post("/test-transform")
async def test_data_transformation(zotero_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test data transformation functionality
    
    This endpoint allows testing the data transformation logic by sending
    sample Zotero data and receiving the transformed internal format.
    Useful for debugging and validation.
    """
    try:
        transformed = import_service.transform_item_data(zotero_data)
        
        return {
            "original": zotero_data,
            "transformed": transformed,
            "transformation_successful": True
        }
        
    except Exception as e:
        logger.error(f"Data transformation test failed: {e}")
        return {
            "original": zotero_data,
            "transformed": None,
            "transformation_successful": False,
            "error": str(e)
        }


async def _run_library_import(
    connection_id: str,
    library_ids: Optional[List[str]] = None
):
    """
    Background task to run library import
    
    This function runs the actual import operation in the background
    and handles any errors that occur during the process.
    """
    try:
        progress = await import_service.import_library(
            connection_id=connection_id,
            library_ids=library_ids
        )
        
        logger.info(f"Library import completed: {progress.get_progress_dict()}")
        
    except Exception as e:
        logger.error(f"Background library import failed: {e}")


# Additional utility endpoints for development and testing

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for the import service"""
    return {
        "status": "healthy",
        "service": "zotero-library-import",
        "version": "1.0.0"
    }


@router.get("/stats")
async def get_import_stats() -> Dict[str, Any]:
    """Get statistics about import operations"""
    try:
        active_imports = import_service.get_active_imports()
        
        return {
            "active_imports_count": len(active_imports),
            "active_imports": [
                {
                    "import_id": imp["import_id"],
                    "status": imp["status"],
                    "progress_percentage": imp["progress_percentage"],
                    "items_processed": imp["processed"]["items"]
                }
                for imp in active_imports
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get import stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get import stats: {str(e)}"
        )