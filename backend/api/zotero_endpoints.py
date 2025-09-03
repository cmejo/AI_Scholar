"""
Zotero integration API endpoints
"""
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models.zotero_schemas import (
    ZoteroConnectionCreate,
    ZoteroConnectionResponse,
    ZoteroConnectionUpdate,
    ZoteroLibraryResponse,
    ZoteroCollectionResponse,
    ZoteroItemResponse,
    ZoteroSearchRequest,
    ZoteroSearchResponse,
    ZoteroOAuthInitiateResponse,
    ZoteroOAuthCallbackRequest,
    ZoteroUserPreferencesResponse,
    ZoteroUserPreferencesUpdate,
    ZoteroSyncRequest,
    ZoteroSyncResponse
)
from services.zotero.zotero_auth_service import ZoteroAuthService
from services.zotero.zotero_sync_service import ZoteroLibrarySyncService
from services.zotero.zotero_collection_service import ZoteroCollectionService
from services.zotero.zotero_client import ZoteroAPIClient, ZoteroAPIError
from middleware.zotero_auth_middleware import (
    get_current_user,
    get_zotero_connection,
    get_validated_zotero_client,
    require_library_access,
    require_item_access
)

# Import research integration endpoints
from .zotero_research_endpoints import router as research_router
from .zotero_webhook_endpoints import router as webhook_router

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zotero", tags=["zotero"])

# Initialize services
zotero_auth_service = ZoteroAuthService()
sync_service = ZoteroLibrarySyncService()
collection_service = ZoteroCollectionService()


@router.post("/oauth/initiate", response_model=ZoteroOAuthInitiateResponse)
async def initiate_oauth(
    scopes: Optional[List[str]] = Query(None, description="OAuth scopes to request"),
    user=Depends(get_current_user)
):
    """
    Initiate Zotero OAuth 2.0 flow
    
    Returns authorization URL for user to visit
    """
    try:
        logger.info(f"Initiating OAuth flow for user {user.id}")
        
        # Generate authorization URL with secure state
        auth_url, state = zotero_auth_service.get_authorization_url(
            user_id=user.id,
            scopes=scopes
        )
        
        logger.info(f"Generated OAuth URL for user {user.id}")
        
        return ZoteroOAuthInitiateResponse(
            authorization_url=auth_url,
            state=state,
            expires_in=600  # 10 minutes
        )
        
    except Exception as e:
        logger.error(f"Error initiating OAuth for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OAuth flow"
        )


@router.post("/oauth/callback", response_model=ZoteroConnectionResponse)
async def oauth_callback(callback_data: ZoteroOAuthCallbackRequest):
    """
    Handle Zotero OAuth callback
    
    Exchanges authorization code for access token and creates connection
    """
    try:
        logger.info(f"Processing OAuth callback with state: {callback_data.state[:10]}...")
        
        # Get state information to extract user_id
        state_info = zotero_auth_service.get_oauth_state_info(callback_data.state)
        if not state_info:
            logger.error(f"Invalid or expired OAuth state: {callback_data.state}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OAuth state"
            )
        
        user_id = state_info["user_id"]
        
        # Exchange code for token
        token_data = await zotero_auth_service.exchange_code_for_token(
            authorization_code=callback_data.code,
            state=callback_data.state,
            user_id=user_id
        )
        
        # Store connection
        connection = await zotero_auth_service.store_connection(
            user_id=user_id,
            token_data=token_data
        )
        
        logger.info(f"Successfully created Zotero connection for user {user_id}")
        
        return ZoteroConnectionResponse.from_attributes(connection)
        
    except Exception as auth_error:
        logger.error(f"OAuth callback error: {auth_error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth callback failed"
        )
    except Exception as e:
        logger.error(f"Unexpected error in OAuth callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth callback failed"
        )


@router.post("/connections", response_model=ZoteroConnectionResponse)
async def create_api_key_connection(
    connection_data: ZoteroConnectionCreate,
    user=Depends(get_current_user)
):
    """
    Create Zotero connection using API key
    
    Alternative to OAuth for users who prefer API key authentication
    """
    try:
        if connection_data.connection_type != "api_key":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This endpoint only supports API key connections"
            )
        
        if not connection_data.api_key or not connection_data.zotero_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key and Zotero user ID are required"
            )
        
        connection = await zotero_auth_service.create_api_key_connection(
            user_id=user.id,
            api_key=connection_data.api_key,
            zotero_user_id=connection_data.zotero_user_id
        )
        
        return ZoteroConnectionResponse.from_orm(connection)
        
    except Exception as auth_error:
        logger.error(f"API key connection error: {auth_error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create API key connection"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating API key connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key connection"
        )


@router.get("/connections", response_model=List[ZoteroConnectionResponse])
async def get_connections(user=Depends(get_current_user)):
    """
    Get all Zotero connections for the current user
    """
    try:
        connections = await zotero_auth_service.get_user_connections(user.id)
        return [ZoteroConnectionResponse.from_orm(conn) for conn in connections]
        
    except Exception as e:
        logger.error(f"Error getting connections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve connections"
        )


@router.get("/connections/{connection_id}", response_model=ZoteroConnectionResponse)
async def get_connection(connection_id: str, user=Depends(get_current_user)):
    """
    Get a specific Zotero connection
    """
    try:
        connections = await zotero_auth_service.get_user_connections(user.id)
        connection = next((conn for conn in connections if conn.id == connection_id), None)
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        return ZoteroConnectionResponse.from_orm(connection)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve connection"
        )


@router.put("/connections/{connection_id}", response_model=ZoteroConnectionResponse)
async def update_connection(
    connection_id: str,
    update_data: ZoteroConnectionUpdate,
    user=Depends(get_current_user)
):
    """
    Update a Zotero connection
    """
    try:
        # This is a placeholder - implement connection update logic
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Connection update not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update connection"
        )


@router.delete("/connections/{connection_id}")
async def revoke_connection(connection_id: str, user=Depends(get_current_user)):
    """
    Revoke a Zotero connection
    """
    try:
        success = await zotero_auth_service.revoke_connection(user.id, connection_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        return {"message": "Connection revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke connection"
        )


@router.post("/connections/{connection_id}/validate")
async def validate_connection(connection_id: str, user=Depends(get_current_user)):
    """
    Validate a Zotero connection and refresh token if needed
    """
    try:
        connections = await zotero_auth_service.get_user_connections(user.id)
        connection = next((conn for conn in connections if conn.id == connection_id), None)
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        # Validate connection
        is_valid = await zotero_auth_service.validate_connection(connection)
        
        if is_valid:
            # Refresh token metadata
            await zotero_auth_service.refresh_token(connection)
            
            return {
                "connection_id": connection_id,
                "is_valid": True,
                "message": "Connection is valid and token refreshed",
                "validated_at": datetime.now().isoformat()
            }
        else:
            return {
                "connection_id": connection_id,
                "is_valid": False,
                "message": "Connection is invalid - please reconnect your Zotero account",
                "validated_at": datetime.now().isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate connection"
        )


@router.post("/connections/{connection_id}/test")
async def test_connection(connection_id: str, user=Depends(get_current_user)):
    """
    Test Zotero API connection and return detailed results
    """
    try:
        connections = await zotero_auth_service.get_user_connections(user.id)
        connection = next((conn for conn in connections if conn.id == connection_id), None)
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        # Test connection with detailed results
        async with ZoteroAPIClient() as client:
            test_result = await client.test_connection(
                connection.access_token,
                connection.zotero_user_id
            )
            
            # Add rate limit status
            rate_limit_status = client.get_rate_limit_status()
            test_result["rate_limit_status"] = rate_limit_status
            
            return {
                "connection_id": connection_id,
                "test_result": test_result,
                "connection_metadata": {
                    "connection_type": connection.connection_type,
                    "created_at": connection.created_at.isoformat(),
                    "last_sync_at": connection.last_sync_at.isoformat() if connection.last_sync_at else None,
                    "sync_enabled": connection.sync_enabled
                }
            }
        
    except HTTPException:
        raise
    except ZoteroAPIError as e:
        logger.error(f"Zotero API error during connection test: {e.message}")
        return {
            "connection_id": connection_id,
            "test_result": {
                "is_valid": False,
                "error": {
                    "message": e.message,
                    "status_code": e.status_code,
                    "response_data": e.response_data
                }
            }
        }
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test connection"
        )


@router.get("/libraries", response_model=List[ZoteroLibraryResponse])
async def get_libraries(user=Depends(get_current_user)):
    """
    Get all accessible Zotero libraries for the user
    """
    try:
        # This is a placeholder - implement library retrieval logic
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Library retrieval not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting libraries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve libraries"
        )


@router.get("/connections/{connection_id}/libraries/{library_id}/collections")
async def get_collections(
    connection_id: str,
    library_id: str,
    include_hierarchy: bool = Query(True, description="Include hierarchical structure"),
    include_item_counts: bool = Query(True, description="Include item counts"),
    user=Depends(get_current_user)
):
    """
    Get collections from a specific library
    """
    try:
        # Verify connection exists and belongs to user
        connections = await zotero_auth_service.get_user_connections(user.id)
        connection = next((conn for conn in connections if conn.id == connection_id), None)
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        collections = await collection_service.get_library_collections(
            connection_id=connection_id,
            library_id=library_id,
            include_hierarchy=include_hierarchy,
            include_item_counts=include_item_counts
        )
        
        return {
            "collections": collections,
            "total_count": len(collections),
            "hierarchical": include_hierarchy,
            "includes_item_counts": include_item_counts
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collections"
        )


@router.get("/connections/{connection_id}/libraries/{library_id}/collections/tree")
async def get_collection_tree(
    connection_id: str,
    library_id: str,
    collection_id: Optional[str] = Query(None, description="Specific collection ID"),
    user=Depends(get_current_user)
):
    """
    Get collection tree structure
    """
    try:
        # Verify connection exists and belongs to user
        connections = await zotero_auth_service.get_user_connections(user.id)
        connection = next((conn for conn in connections if conn.id == connection_id), None)
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        tree = await collection_service.get_collection_tree(
            connection_id=connection_id,
            library_id=library_id,
            collection_id=collection_id
        )
        
        return {
            "tree": tree,
            "root_collection_id": collection_id
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting collection tree: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collection tree"
        )


@router.get("/connections/{connection_id}/libraries/{library_id}/collections/{collection_id}/items")
async def get_collection_items(
    connection_id: str,
    library_id: str,
    collection_id: str,
    include_subcollections: bool = Query(False, description="Include items from subcollections"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of items"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    user=Depends(get_current_user)
):
    """
    Get items in a collection
    """
    try:
        # Verify connection exists and belongs to user
        connections = await zotero_auth_service.get_user_connections(user.id)
        connection = next((conn for conn in connections if conn.id == connection_id), None)
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        result = await collection_service.get_collection_items(
            connection_id=connection_id,
            library_id=library_id,
            collection_id=collection_id,
            include_subcollections=include_subcollections,
            limit=limit,
            offset=offset
        )
        
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting collection items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collection items"
        )


@router.get("/connections/{connection_id}/libraries/{library_id}/collections/search")
async def search_collections(
    connection_id: str,
    library_id: str,
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    user=Depends(get_current_user)
):
    """
    Search collections by name
    """
    try:
        # Verify connection exists and belongs to user
        connections = await zotero_auth_service.get_user_connections(user.id)
        connection = next((conn for conn in connections if conn.id == connection_id), None)
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        results = await collection_service.search_collections(
            connection_id=connection_id,
            library_id=library_id,
            query=q,
            limit=limit
        )
        
        return {
            "query": q,
            "results": results,
            "count": len(results),
            "limit": limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search collections"
        )


@router.get("/connections/{connection_id}/libraries/{library_id}/collections/statistics")
async def get_collection_statistics(
    connection_id: str,
    library_id: str,
    user=Depends(get_current_user)
):
    """
    Get collection statistics for a library
    """
    try:
        # Verify connection exists and belongs to user
        connections = await zotero_auth_service.get_user_connections(user.id)
        connection = next((conn for conn in connections if conn.id == connection_id), None)
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        statistics = await collection_service.get_collection_statistics(
            connection_id=connection_id,
            library_id=library_id
        )
        
        return statistics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collection statistics"
        )


@router.get("/connections/{connection_id}/libraries/{library_id}/collections/{collection_id}/breadcrumbs")
async def get_collection_breadcrumbs(
    connection_id: str,
    library_id: str,
    collection_id: str,
    user=Depends(get_current_user)
):
    """
    Get breadcrumb navigation for a collection
    """
    try:
        # Verify connection exists and belongs to user
        connections = await zotero_auth_service.get_user_connections(user.id)
        connection = next((conn for conn in connections if conn.id == connection_id), None)
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        breadcrumbs = await collection_service.get_collection_breadcrumbs(
            connection_id=connection_id,
            library_id=library_id,
            collection_id=collection_id
        )
        
        return {
            "breadcrumbs": breadcrumbs,
            "collection_id": collection_id
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting collection breadcrumbs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collection breadcrumbs"
        )


@router.post("/connections/{connection_id}/libraries/{library_id}/collections/update-paths")
async def update_collection_paths(
    connection_id: str,
    library_id: str,
    user=Depends(get_current_user)
):
    """
    Update collection paths for proper hierarchy
    """
    try:
        # Verify connection exists and belongs to user
        connections = await zotero_auth_service.get_user_connections(user.id)
        connection = next((conn for conn in connections if conn.id == connection_id), None)
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        result = await collection_service.update_collection_paths(
            connection_id=connection_id,
            library_id=library_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating collection paths: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update collection paths"
        )


@router.put("/connections/{connection_id}/libraries/{library_id}/collections/{collection_id}/move")
async def move_collection(
    connection_id: str,
    library_id: str,
    collection_id: str,
    new_parent_id: Optional[str] = Query(None, description="New parent collection ID"),
    user=Depends(get_current_user)
):
    """
    Move a collection to a new parent (local operation only)
    """
    try:
        # Verify connection exists and belongs to user
        connections = await zotero_auth_service.get_user_connections(user.id)
        connection = next((conn for conn in connections if conn.id == connection_id), None)
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        result = await collection_service.move_collection(
            connection_id=connection_id,
            library_id=library_id,
            collection_id=collection_id,
            new_parent_id=new_parent_id
        )
        
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error moving collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to move collection"
        )


@router.get("/libraries/{library_id}/items", response_model=List[ZoteroItemResponse])
async def get_items(
    library_id: str,
    collection_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user=Depends(get_current_user)
):
    """
    Get items from a library or collection
    """
    try:
        # This is a placeholder - implement item retrieval logic
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Item retrieval not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve items"
        )


@router.post("/search", response_model=ZoteroSearchResponse)
async def search_items(search_request: ZoteroSearchRequest, user=Depends(get_current_user)):
    """
    Search across Zotero items
    """
    try:
        # This is a placeholder - implement search logic
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Search not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


@router.post("/connections/{connection_id}/import")
async def import_library(
    connection_id: str,
    library_ids: Optional[List[str]] = Query(None, description="Specific library IDs to import"),
    user=Depends(get_current_user)
):
    """
    Import library data from Zotero
    """
    try:
        # Verify connection exists and belongs to user
        connections = await zotero_auth_service.get_user_connections(user.id)
        connection = next((conn for conn in connections if conn.id == connection_id), None)
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        if connection.connection_status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Connection is not active"
            )
        
        # Start library import
        progress = await sync_service.import_library(
            connection_id=connection_id,
            library_ids=library_ids
        )
        
        return {
            "import_id": progress.sync_id,
            "status": progress.status.value,
            "message": "Library import started",
            "started_at": progress.started_at.isoformat(),
            "progress": progress.get_progress_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting library import: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start library import"
        )


@router.get("/imports/{import_id}/progress")
async def get_import_progress(
    import_id: str,
    user=Depends(get_current_user)
):
    """
    Get progress of a library import operation
    """
    try:
        progress = sync_service.get_sync_progress(import_id)
        
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import operation not found"
            )
        
        return progress
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting import progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get import progress"
        )


@router.get("/imports/active")
async def get_active_imports(user=Depends(get_current_user)):
    """
    Get all active import operations for the user
    """
    try:
        active_syncs = sync_service.get_active_syncs()
        
        # Filter by user's connections (would need to add user filtering to sync service)
        # For now, return all active syncs
        return {
            "active_imports": active_syncs,
            "count": len(active_syncs)
        }
        
    except Exception as e:
        logger.error(f"Error getting active imports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active imports"
        )


@router.post("/imports/{import_id}/cancel")
async def cancel_import(
    import_id: str,
    user=Depends(get_current_user)
):
    """
    Cancel an active import operation
    """
    try:
        success = await sync_service.cancel_sync(import_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import operation not found or already completed"
            )
        
        return {
            "import_id": import_id,
            "status": "cancelled",
            "message": "Import operation cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling import: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel import"
        )


@router.post("/connections/{connection_id}/sync")
async def incremental_sync(
    connection_id: str,
    sync_request: ZoteroSyncRequest,
    user=Depends(get_current_user)
):
    """
    Perform incremental synchronization with Zotero
    """
    try:
        # Verify connection exists and belongs to user
        connections = await zotero_auth_service.get_user_connections(user.id)
        connection = next((conn for conn in connections if conn.id == connection_id), None)
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        if connection.connection_status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Connection is not active"
            )
        
        # Start incremental sync
        progress = await sync_service.incremental_sync(
            connection_id=connection_id,
            library_ids=sync_request.library_ids
        )
        
        return {
            "sync_id": progress.sync_id,
            "sync_type": progress.sync_type.value,
            "status": progress.status.value,
            "message": "Incremental sync completed" if progress.status.value == "completed" else "Incremental sync started",
            "started_at": progress.started_at.isoformat(),
            "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
            "progress": progress.get_progress_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting incremental sync: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start incremental sync"
        )


@router.get("/connections/{connection_id}/conflicts")
async def detect_sync_conflicts(
    connection_id: str,
    library_ids: Optional[List[str]] = Query(None, description="Specific library IDs to check"),
    user=Depends(get_current_user)
):
    """
    Detect potential sync conflicts before performing sync
    """
    try:
        # Verify connection exists and belongs to user
        connections = await zotero_auth_service.get_user_connections(user.id)
        connection = next((conn for conn in connections if conn.id == connection_id), None)
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        # Detect conflicts
        conflicts = await sync_service.detect_sync_conflicts(
            connection_id=connection_id,
            library_ids=library_ids
        )
        
        return conflicts
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting sync conflicts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to detect sync conflicts"
        )


@router.post("/connections/{connection_id}/resolve-conflicts")
async def resolve_sync_conflicts(
    connection_id: str,
    resolution_strategy: str = Query("zotero_wins", description="Conflict resolution strategy"),
    library_ids: Optional[List[str]] = Query(None, description="Specific library IDs to resolve"),
    user=Depends(get_current_user)
):
    """
    Resolve sync conflicts using specified strategy
    """
    try:
        # Verify connection exists and belongs to user
        connections = await zotero_auth_service.get_user_connections(user.id)
        connection = next((conn for conn in connections if conn.id == connection_id), None)
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        # Resolve conflicts
        result = await sync_service.resolve_sync_conflicts(
            connection_id=connection_id,
            resolution_strategy=resolution_strategy,
            library_ids=library_ids
        )
        
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error resolving sync conflicts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve sync conflicts"
        )


@router.post("/sync", response_model=ZoteroSyncResponse)
async def sync_libraries(sync_request: ZoteroSyncRequest, user=Depends(get_current_user)):
    """
    Trigger synchronization with Zotero (legacy endpoint)
    """
    try:
        # This is a placeholder - implement sync logic
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Legacy sync endpoint not yet implemented - use connection-specific sync endpoints"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing libraries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sync failed"
        )


@router.get("/preferences", response_model=ZoteroUserPreferencesResponse)
async def get_user_preferences(user=Depends(get_current_user)):
    """
    Get user's Zotero preferences
    """
    try:
        # This is a placeholder - implement preferences retrieval logic
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Preferences retrieval not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preferences"
        )


@router.put("/preferences", response_model=ZoteroUserPreferencesResponse)
async def update_user_preferences(
    preferences: ZoteroUserPreferencesUpdate,
    user=Depends(get_current_user)
):
    """
    Update user's Zotero preferences
    """
    try:
        # This is a placeholder - implement preferences update logic
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Preferences update not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )


# Include research integration endpoints
router.include_router(research_router)
router.include_router(webhook_router)