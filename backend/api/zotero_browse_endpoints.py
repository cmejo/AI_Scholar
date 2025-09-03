"""
Zotero Reference Browsing and Filtering API Endpoints

This module provides REST API endpoints for browsing and filtering
Zotero references with collection-based navigation and advanced filtering.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_user
from models.zotero_schemas import ZoteroItemResponse, ZoteroBrowseResponse
from services.zotero.zotero_browse_service import get_browse_service, ZoteroBrowseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zotero/browse", tags=["Zotero Browse"])


@router.get("/", response_model=ZoteroBrowseResponse)
async def browse_references(
    library_id: Optional[str] = Query(None, description="Filter by library ID"),
    collection_id: Optional[str] = Query(None, description="Filter by collection ID"),
    item_type: Optional[str] = Query(None, description="Filter by item type"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    creators: Optional[List[str]] = Query(None, description="Filter by creators"),
    publication_year_start: Optional[int] = Query(None, description="Start year filter"),
    publication_year_end: Optional[int] = Query(None, description="End year filter"),
    publisher: Optional[str] = Query(None, description="Filter by publisher"),
    has_doi: Optional[bool] = Query(None, description="Filter by DOI presence"),
    has_attachments: Optional[bool] = Query(None, description="Filter by attachment presence"),
    date_added_start: Optional[datetime] = Query(None, description="Start date for date added filter"),
    date_added_end: Optional[datetime] = Query(None, description="End date for date added filter"),
    sort_by: str = Query(default="date_modified", description="Sort field"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$", description="Sort order"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Results offset"),
    current_user: dict = Depends(get_current_user),
    browse_service: ZoteroBrowseService = Depends(get_browse_service)
):
    """
    Browse references with comprehensive filtering options
    
    Provides advanced filtering capabilities including collection-based filtering,
    item type filtering, tag filtering, creator filtering, and date range filtering.
    Results are paginated and can be sorted by various fields.
    """
    try:
        user_id = current_user["id"]
        
        references, total_count, browse_metadata = await browse_service.browse_references(
            user_id=user_id,
            library_id=library_id,
            collection_id=collection_id,
            item_type=item_type,
            tags=tags or [],
            creators=creators or [],
            publication_year_start=publication_year_start,
            publication_year_end=publication_year_end,
            publisher=publisher,
            has_doi=has_doi,
            has_attachments=has_attachments,
            date_added_start=date_added_start,
            date_added_end=date_added_end,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        
        # Add browse metadata to response headers
        from fastapi import Response
        response = Response()
        response.headers["X-Total-Count"] = str(total_count)
        response.headers["X-Page-Count"] = str(browse_metadata["page_count"])
        response.headers["X-Current-Page"] = str(browse_metadata["current_page"])
        response.headers["X-Has-Next-Page"] = str(browse_metadata["has_next_page"]).lower()
        response.headers["X-Has-Previous-Page"] = str(browse_metadata["has_previous_page"]).lower()
        response.headers["X-Filters-Applied"] = str(len([
            f for f in browse_metadata["filters_applied"].values() 
            if f is not None and f != [] and f != ""
        ]))
        response.headers["X-Has-Suggestions"] = str(len(browse_metadata.get("suggestions", []))).lower()
        
        logger.info(f"User {user_id} browsed references - {total_count} results with {len([f for f in browse_metadata['filters_applied'].values() if f is not None and f != [] and f != ''])} filters")
        
        # Return response with metadata
        return {
            "references": references,
            "metadata": browse_metadata
        }
        
    except Exception as e:
        logger.error(f"Browse failed for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Browse operation failed"
        )


@router.get("/recent", response_model=List[ZoteroItemResponse])
async def get_recent_references(
    library_id: Optional[str] = Query(None, description="Filter by library ID"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum results"),
    current_user: dict = Depends(get_current_user),
    browse_service: ZoteroBrowseService = Depends(get_browse_service)
):
    """
    Get recently added or modified references
    
    Returns references that have been added or modified within the specified
    number of days. Useful for seeing what's new in the library.
    """
    try:
        user_id = current_user["id"]
        
        references = await browse_service.get_recent_references(
            user_id=user_id,
            library_id=library_id,
            days=days,
            limit=limit
        )
        
        logger.info(f"User {user_id} requested recent references - {len(references)} results")
        return references
        
    except Exception as e:
        logger.error(f"Failed to get recent references for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent references"
        )


@router.get("/popular", response_model=List[ZoteroItemResponse])
async def get_popular_references(
    library_id: Optional[str] = Query(None, description="Filter by library ID"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum results"),
    current_user: dict = Depends(get_current_user),
    browse_service: ZoteroBrowseService = Depends(get_browse_service)
):
    """
    Get popular references based on various metrics
    
    Returns references ranked by popularity based on factors like number of tags,
    presence of attachments, recency, and credibility indicators like DOI.
    """
    try:
        user_id = current_user["id"]
        
        references = await browse_service.get_popular_references(
            user_id=user_id,
            library_id=library_id,
            limit=limit
        )
        
        logger.info(f"User {user_id} requested popular references - {len(references)} results")
        return references
        
    except Exception as e:
        logger.error(f"Failed to get popular references for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve popular references"
        )


@router.get("/year/{year}", response_model=List[ZoteroItemResponse])
async def get_references_by_year(
    year: int,
    library_id: Optional[str] = Query(None, description="Filter by library ID"),
    sort_by: str = Query(default="title", description="Sort field"),
    sort_order: str = Query(default="asc", regex="^(asc|desc)$", description="Sort order"),
    limit: int = Query(default=100, ge=1, le=200, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Results offset"),
    current_user: dict = Depends(get_current_user),
    browse_service: ZoteroBrowseService = Depends(get_browse_service)
):
    """
    Get references from a specific publication year
    
    Returns all references published in the specified year, with pagination
    and sorting options. Useful for browsing publications by time period.
    """
    try:
        user_id = current_user["id"]
        
        references, total_count = await browse_service.get_references_by_year(
            user_id=user_id,
            year=year,
            library_id=library_id,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        
        # Add pagination headers
        from fastapi import Response
        response = Response()
        response.headers["X-Total-Count"] = str(total_count)
        response.headers["X-Year"] = str(year)
        
        logger.info(f"User {user_id} browsed references for year {year} - {total_count} results")
        return references
        
    except Exception as e:
        logger.error(f"Failed to get references for year {year}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve references for year {year}"
        )


@router.get("/tag/{tag}", response_model=List[ZoteroItemResponse])
async def get_references_by_tag(
    tag: str,
    library_id: Optional[str] = Query(None, description="Filter by library ID"),
    sort_by: str = Query(default="date_modified", description="Sort field"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$", description="Sort order"),
    limit: int = Query(default=100, ge=1, le=200, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Results offset"),
    current_user: dict = Depends(get_current_user),
    browse_service: ZoteroBrowseService = Depends(get_browse_service)
):
    """
    Get references with a specific tag
    
    Returns all references tagged with the specified tag, with pagination
    and sorting options. Useful for browsing references by topic or category.
    """
    try:
        user_id = current_user["id"]
        
        references, total_count = await browse_service.get_references_by_tag(
            user_id=user_id,
            tag=tag,
            library_id=library_id,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        
        # Add pagination headers
        from fastapi import Response
        response = Response()
        response.headers["X-Total-Count"] = str(total_count)
        response.headers["X-Tag"] = tag
        
        logger.info(f"User {user_id} browsed references for tag '{tag}' - {total_count} results")
        return references
        
    except Exception as e:
        logger.error(f"Failed to get references for tag '{tag}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve references for tag '{tag}'"
        )


@router.get("/creator/{creator_name}", response_model=List[ZoteroItemResponse])
async def get_references_by_creator(
    creator_name: str,
    library_id: Optional[str] = Query(None, description="Filter by library ID"),
    sort_by: str = Query(default="publication_year", description="Sort field"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$", description="Sort order"),
    limit: int = Query(default=100, ge=1, le=200, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Results offset"),
    current_user: dict = Depends(get_current_user),
    browse_service: ZoteroBrowseService = Depends(get_browse_service)
):
    """
    Get references by a specific creator
    
    Returns all references authored or edited by the specified creator, with
    pagination and sorting options. Useful for browsing an author's work.
    """
    try:
        user_id = current_user["id"]
        
        references, total_count = await browse_service.get_references_by_creator(
            user_id=user_id,
            creator_name=creator_name,
            library_id=library_id,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        
        # Add pagination headers
        from fastapi import Response
        response = Response()
        response.headers["X-Total-Count"] = str(total_count)
        response.headers["X-Creator"] = creator_name
        
        logger.info(f"User {user_id} browsed references for creator '{creator_name}' - {total_count} results")
        return references
        
    except Exception as e:
        logger.error(f"Failed to get references for creator '{creator_name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve references for creator '{creator_name}'"
        )


@router.get("/collections/{library_id}")
async def get_collection_hierarchy(
    library_id: str,
    include_item_counts: bool = Query(default=True, description="Include item counts"),
    current_user: dict = Depends(get_current_user),
    browse_service: ZoteroBrowseService = Depends(get_browse_service)
) -> List[Dict[str, Any]]:
    """
    Get hierarchical collection structure for browsing
    
    Returns the collection hierarchy for the specified library, including
    nested collections and optional item counts. Useful for building
    collection navigation interfaces.
    """
    try:
        user_id = current_user["id"]
        
        hierarchy = await browse_service.get_collection_hierarchy(
            user_id=user_id,
            library_id=library_id,
            include_item_counts=include_item_counts
        )
        
        logger.info(f"User {user_id} requested collection hierarchy for library {library_id}")
        return hierarchy
        
    except PermissionError as e:
        logger.warning(f"Permission denied for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get collection hierarchy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collection hierarchy"
        )


@router.get("/statistics")
async def get_browse_statistics(
    library_id: Optional[str] = Query(None, description="Filter by library ID"),
    current_user: dict = Depends(get_current_user),
    browse_service: ZoteroBrowseService = Depends(get_browse_service)
) -> Dict[str, Any]:
    """
    Get browsing statistics for the user's references
    
    Returns comprehensive statistics about the user's reference collection
    including item type distribution, publication year distribution, recent
    activity, and other useful metrics for browsing insights.
    """
    try:
        user_id = current_user["id"]
        
        statistics = await browse_service.get_browse_statistics(
            user_id=user_id,
            library_id=library_id
        )
        
        logger.info(f"User {user_id} requested browse statistics")
        return statistics
        
    except Exception as e:
        logger.error(f"Failed to get browse statistics for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve browse statistics"
        )


@router.get("/filters")
async def get_available_filters(
    library_id: Optional[str] = Query(None, description="Filter by library ID"),
    current_user: dict = Depends(get_current_user),
    browse_service: ZoteroBrowseService = Depends(get_browse_service)
) -> Dict[str, Any]:
    """
    Get available filter options for browsing
    
    Returns all available filter options including item types, tags, creators,
    publishers, and year ranges. Useful for building dynamic filter interfaces.
    """
    try:
        user_id = current_user["id"]
        
        # Get statistics which include filter options
        statistics = await browse_service.get_browse_statistics(
            user_id=user_id,
            library_id=library_id
        )
        
        # Extract filter options from statistics
        filters = {
            "item_types": [item["type"] for item in statistics["item_types"]],
            "publication_years": {
                "min": min([item["year"] for item in statistics["publication_years"]]) if statistics["publication_years"] else None,
                "max": max([item["year"] for item in statistics["publication_years"]]) if statistics["publication_years"] else None,
                "available": [item["year"] for item in statistics["publication_years"]]
            },
            "tags": [item["tag"] for item in statistics["top_tags"]],
            "sort_options": [
                {"value": "title", "label": "Title"},
                {"value": "date_added", "label": "Date Added"},
                {"value": "date_modified", "label": "Date Modified"},
                {"value": "publication_year", "label": "Publication Year"},
                {"value": "item_type", "label": "Item Type"},
                {"value": "publisher", "label": "Publisher"}
            ],
            "sort_orders": [
                {"value": "asc", "label": "Ascending"},
                {"value": "desc", "label": "Descending"}
            ],
            "boolean_filters": [
                {"key": "has_doi", "label": "Has DOI"},
                {"key": "has_attachments", "label": "Has Attachments"}
            ]
        }
        
        logger.info(f"User {user_id} requested available filters")
        return filters
        
    except Exception as e:
        logger.error(f"Failed to get available filters for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available filters"
        )


@router.get("/metadata")
async def get_browse_metadata(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get browse interface metadata and configuration
    
    Returns metadata about the browse interface including available sort options,
    filter types, pagination settings, and other configuration information.
    """
    return {
        "pagination": {
            "default_limit": 50,
            "max_limit": 200,
            "available_limits": [10, 20, 50, 100, 200]
        },
        "sorting": {
            "default_sort_by": "date_modified",
            "default_sort_order": "desc",
            "available_sort_fields": [
                "title", "date_added", "date_modified", "publication_year",
                "item_type", "publisher", "doi"
            ]
        },
        "filters": {
            "text_filters": ["publisher"],
            "list_filters": ["tags", "creators"],
            "boolean_filters": ["has_doi", "has_attachments"],
            "range_filters": ["publication_year", "date_added"],
            "select_filters": ["item_type", "library_id", "collection_id"]
        },
        "views": [
            {"key": "recent", "label": "Recent", "description": "Recently added or modified"},
            {"key": "popular", "label": "Popular", "description": "Most relevant and active"},
            {"key": "by_year", "label": "By Year", "description": "Browse by publication year"},
            {"key": "by_tag", "label": "By Tag", "description": "Browse by tags"},
            {"key": "by_creator", "label": "By Creator", "description": "Browse by author/creator"}
        ]
    }


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for browse service"""
    return {
        "status": "healthy",
        "service": "zotero_browse",
        "timestamp": "2024-01-15T10:00:00Z"
    }