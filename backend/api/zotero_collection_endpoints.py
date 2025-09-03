"""
Enhanced Zotero collection management API endpoints
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from models.zotero_schemas import (
    ZoteroCollectionResponse,
    ZoteroCollectionTree,
    ZoteroItemResponse
)
from services.zotero.zotero_auth_service import ZoteroAuthService
from services.zotero.zotero_collection_service import ZoteroCollectionService
from middleware.zotero_auth_middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zotero/collections", tags=["zotero-collections"])

# Initialize services
zotero_auth_service = ZoteroAuthService()
collection_service = ZoteroCollectionService()


class CollectionFilterRequest(BaseModel):
    """Schema for collection filtering request"""
    library_id: str = Field(..., description="Library ID to filter collections in")
    name_pattern: Optional[str] = Field(None, description="Filter by collection name pattern")
    min_item_count: Optional[int] = Field(None, ge=0, description="Minimum number of items")
    max_item_count: Optional[int] = Field(None, ge=0, description="Maximum number of items")
    max_depth: Optional[int] = Field(None, ge=1, description="Maximum collection depth")
    parent_collection_id: Optional[str] = Field(None, description="Filter by parent collection")
    include_empty: bool = Field(True, description="Include collections with no items")
    sort_by: str = Field(default="name", description="Sort field (name, item_count, depth)")
    sort_order: str = Field(default="asc", description="Sort order (asc, desc)")
    limit: int = Field(default=50, ge=1, le=200, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Results offset")


class CollectionNavigationResponse(BaseModel):
    """Schema for collection navigation response"""
    current_collection: Optional[Dict[str, Any]] = Field(None, description="Current collection info")
    parent_collections: List[Dict[str, Any]] = Field(default_factory=list, description="Parent collections (breadcrumbs)")
    child_collections: List[Dict[str, Any]] = Field(default_factory=list, description="Direct child collections")
    sibling_collections: List[Dict[str, Any]] = Field(default_factory=list, description="Sibling collections")
    collection_path: str = Field(..., description="Full hierarchical path")
    depth_level: int = Field(..., description="Depth level in hierarchy")
    total_items: int = Field(..., description="Total items in collection and subcollections")


class CollectionHierarchyResponse(BaseModel):
    """Schema for collection hierarchy response"""
    root_collections: List[ZoteroCollectionTree] = Field(..., description="Root level collections")
    total_collections: int = Field(..., description="Total number of collections")
    max_depth: int = Field(..., description="Maximum hierarchy depth")
    collections_by_depth: Dict[str, int] = Field(..., description="Collections count by depth level")


@router.post("/filter")
async def filter_collections(
    connection_id: str,
    filter_request: CollectionFilterRequest,
    user=Depends(get_current_user)
):
    """
    Filter collections with advanced criteria
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
        
        # Get all collections first
        all_collections = await collection_service.get_library_collections(
            connection_id=connection_id,
            library_id=filter_request.library_id,
            include_hierarchy=False,
            include_item_counts=True
        )
        
        # Apply filters
        filtered_collections = []
        
        for collection in all_collections:
            # Name pattern filter
            if filter_request.name_pattern:
                if filter_request.name_pattern.lower() not in collection["collection_name"].lower():
                    continue
            
            # Item count filters
            item_count = collection.get("actual_item_count", collection.get("item_count", 0))
            if filter_request.min_item_count is not None and item_count < filter_request.min_item_count:
                continue
            if filter_request.max_item_count is not None and item_count > filter_request.max_item_count:
                continue
            
            # Empty collections filter
            if not filter_request.include_empty and item_count == 0:
                continue
            
            # Depth filter
            if filter_request.max_depth is not None:
                path = collection.get("collection_path", "")
                depth = path.count('/') + 1 if path else 1
                if depth > filter_request.max_depth:
                    continue
            
            # Parent collection filter
            if filter_request.parent_collection_id is not None:
                if collection.get("parent_collection_id") != filter_request.parent_collection_id:
                    continue
            
            filtered_collections.append(collection)
        
        # Sort results
        if filter_request.sort_by == "name":
            filtered_collections.sort(
                key=lambda x: x["collection_name"].lower(),
                reverse=(filter_request.sort_order == "desc")
            )
        elif filter_request.sort_by == "item_count":
            filtered_collections.sort(
                key=lambda x: x.get("actual_item_count", x.get("item_count", 0)),
                reverse=(filter_request.sort_order == "desc")
            )
        elif filter_request.sort_by == "depth":
            filtered_collections.sort(
                key=lambda x: (x.get("collection_path", "").count('/') + 1) if x.get("collection_path") else 1,
                reverse=(filter_request.sort_order == "desc")
            )
        
        # Apply pagination
        total_count = len(filtered_collections)
        start_idx = filter_request.offset
        end_idx = start_idx + filter_request.limit
        paginated_collections = filtered_collections[start_idx:end_idx]
        
        return {
            "collections": paginated_collections,
            "total_count": total_count,
            "filtered_count": len(paginated_collections),
            "filters_applied": {
                "name_pattern": filter_request.name_pattern,
                "min_item_count": filter_request.min_item_count,
                "max_item_count": filter_request.max_item_count,
                "max_depth": filter_request.max_depth,
                "parent_collection_id": filter_request.parent_collection_id,
                "include_empty": filter_request.include_empty
            },
            "pagination": {
                "limit": filter_request.limit,
                "offset": filter_request.offset,
                "has_more": end_idx < total_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error filtering collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to filter collections"
        )


@router.get("/{connection_id}/libraries/{library_id}/collections/{collection_id}/navigation")
async def get_collection_navigation(
    connection_id: str,
    library_id: str,
    collection_id: str,
    include_siblings: bool = Query(True, description="Include sibling collections"),
    include_children: bool = Query(True, description="Include child collections"),
    user=Depends(get_current_user)
):
    """
    Get comprehensive navigation information for a collection
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
        
        # Get all collections for navigation
        all_collections = await collection_service.get_library_collections(
            connection_id=connection_id,
            library_id=library_id,
            include_hierarchy=False,
            include_item_counts=True
        )
        
        # Find current collection
        current_collection = next(
            (col for col in all_collections if col["id"] == collection_id),
            None
        )
        
        if not current_collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found"
            )
        
        # Get breadcrumbs (parent collections)
        breadcrumbs = await collection_service.get_collection_breadcrumbs(
            connection_id=connection_id,
            library_id=library_id,
            collection_id=collection_id
        )
        
        # Get child collections
        child_collections = []
        if include_children:
            child_collections = [
                col for col in all_collections
                if col.get("parent_collection_id") == collection_id
            ]
        
        # Get sibling collections
        sibling_collections = []
        if include_siblings:
            parent_id = current_collection.get("parent_collection_id")
            sibling_collections = [
                col for col in all_collections
                if col.get("parent_collection_id") == parent_id and col["id"] != collection_id
            ]
        
        # Calculate total items (including subcollections)
        def get_total_items_recursive(col_id: str) -> int:
            total = 0
            for col in all_collections:
                if col["id"] == col_id:
                    total += col.get("actual_item_count", col.get("item_count", 0))
                elif col.get("parent_collection_id") == col_id:
                    total += get_total_items_recursive(col["id"])
            return total
        
        total_items = get_total_items_recursive(collection_id)
        
        # Calculate depth level
        collection_path = current_collection.get("collection_path", "")
        depth_level = collection_path.count('/') + 1 if collection_path else 1
        
        return CollectionNavigationResponse(
            current_collection=current_collection,
            parent_collections=breadcrumbs,
            child_collections=child_collections,
            sibling_collections=sibling_collections,
            collection_path=collection_path,
            depth_level=depth_level,
            total_items=total_items
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection navigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get collection navigation"
        )


@router.get("/{connection_id}/libraries/{library_id}/hierarchy")
async def get_collection_hierarchy(
    connection_id: str,
    library_id: str,
    max_depth: Optional[int] = Query(None, ge=1, le=10, description="Maximum depth to include"),
    include_item_counts: bool = Query(True, description="Include item counts"),
    user=Depends(get_current_user)
):
    """
    Get complete collection hierarchy with statistics
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
        
        # Get hierarchical collections
        collections = await collection_service.get_library_collections(
            connection_id=connection_id,
            library_id=library_id,
            include_hierarchy=True,
            include_item_counts=include_item_counts
        )
        
        # Filter by max depth if specified
        if max_depth is not None:
            def filter_by_depth(collection_list: List[Dict[str, Any]], current_depth: int = 1) -> List[Dict[str, Any]]:
                if current_depth > max_depth:
                    return []
                
                filtered = []
                for collection in collection_list:
                    filtered_collection = collection.copy()
                    if "children" in collection and current_depth < max_depth:
                        filtered_collection["children"] = filter_by_depth(
                            collection["children"], 
                            current_depth + 1
                        )
                    elif current_depth >= max_depth:
                        filtered_collection["children"] = []
                    
                    filtered.append(filtered_collection)
                
                return filtered
            
            collections = filter_by_depth(collections)
        
        # Calculate statistics
        def calculate_hierarchy_stats(collection_list: List[Dict[str, Any]], depth: int = 1) -> Dict[str, Any]:
            stats = {
                "total_collections": 0,
                "max_depth": depth,
                "collections_by_depth": {}
            }
            
            for collection in collection_list:
                stats["total_collections"] += 1
                
                if depth not in stats["collections_by_depth"]:
                    stats["collections_by_depth"][depth] = 0
                stats["collections_by_depth"][depth] += 1
                
                if "children" in collection and collection["children"]:
                    child_stats = calculate_hierarchy_stats(collection["children"], depth + 1)
                    stats["total_collections"] += child_stats["total_collections"]
                    stats["max_depth"] = max(stats["max_depth"], child_stats["max_depth"])
                    
                    for child_depth, count in child_stats["collections_by_depth"].items():
                        if child_depth not in stats["collections_by_depth"]:
                            stats["collections_by_depth"][child_depth] = 0
                        stats["collections_by_depth"][child_depth] += count
            
            return stats
        
        hierarchy_stats = calculate_hierarchy_stats(collections)
        
        # Convert to tree format
        def convert_to_tree(collection_list: List[Dict[str, Any]]) -> List[ZoteroCollectionTree]:
            trees = []
            for collection in collection_list:
                tree = ZoteroCollectionTree(
                    id=collection["id"],
                    collection_name=collection["collection_name"],
                    item_count=collection.get("actual_item_count", collection.get("item_count", 0)),
                    children=convert_to_tree(collection.get("children", []))
                )
                trees.append(tree)
            return trees
        
        root_collections = convert_to_tree(collections)
        
        return CollectionHierarchyResponse(
            root_collections=root_collections,
            total_collections=hierarchy_stats["total_collections"],
            max_depth=hierarchy_stats["max_depth"],
            collections_by_depth={str(k): v for k, v in hierarchy_stats["collections_by_depth"].items()}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection hierarchy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get collection hierarchy"
        )


@router.get("/{connection_id}/libraries/{library_id}/collections/{collection_id}/descendants")
async def get_collection_descendants(
    connection_id: str,
    library_id: str,
    collection_id: str,
    include_items: bool = Query(False, description="Include items from all descendant collections"),
    max_depth: Optional[int] = Query(None, ge=1, description="Maximum depth to traverse"),
    user=Depends(get_current_user)
):
    """
    Get all descendant collections and optionally their items
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
        
        # Get all collections
        all_collections = await collection_service.get_library_collections(
            connection_id=connection_id,
            library_id=library_id,
            include_hierarchy=False,
            include_item_counts=True
        )
        
        # Find descendants recursively
        def find_descendants(parent_id: str, current_depth: int = 1) -> List[Dict[str, Any]]:
            if max_depth is not None and current_depth > max_depth:
                return []
            
            descendants = []
            for collection in all_collections:
                if collection.get("parent_collection_id") == parent_id:
                    # Add depth information
                    collection_with_depth = collection.copy()
                    collection_with_depth["depth_from_parent"] = current_depth
                    descendants.append(collection_with_depth)
                    
                    # Recursively find children
                    children = find_descendants(collection["id"], current_depth + 1)
                    descendants.extend(children)
            
            return descendants
        
        descendants = find_descendants(collection_id)
        
        # Get items if requested
        all_items = []
        if include_items:
            # Include items from the parent collection and all descendants
            collection_ids = [collection_id] + [desc["id"] for desc in descendants]
            
            for col_id in collection_ids:
                try:
                    items_result = await collection_service.get_collection_items(
                        connection_id=connection_id,
                        library_id=library_id,
                        collection_id=col_id,
                        include_subcollections=False,
                        limit=1000,  # Large limit to get all items
                        offset=0
                    )
                    
                    # Add collection info to each item
                    for item in items_result["items"]:
                        item["source_collection_id"] = col_id
                        item["source_collection_name"] = next(
                            (col["collection_name"] for col in all_collections if col["id"] == col_id),
                            "Unknown"
                        )
                    
                    all_items.extend(items_result["items"])
                    
                except Exception as e:
                    logger.warning(f"Failed to get items for collection {col_id}: {e}")
                    continue
        
        # Calculate statistics
        total_descendants = len(descendants)
        max_descendant_depth = max([desc["depth_from_parent"] for desc in descendants], default=0)
        descendants_by_depth = {}
        
        for descendant in descendants:
            depth = descendant["depth_from_parent"]
            if depth not in descendants_by_depth:
                descendants_by_depth[depth] = 0
            descendants_by_depth[depth] += 1
        
        return {
            "collection_id": collection_id,
            "descendants": descendants,
            "total_descendants": total_descendants,
            "max_depth": max_descendant_depth,
            "descendants_by_depth": descendants_by_depth,
            "items": all_items if include_items else None,
            "total_items": len(all_items) if include_items else None,
            "depth_limit_applied": max_depth
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection descendants: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get collection descendants"
        )