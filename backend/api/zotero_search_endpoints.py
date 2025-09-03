"""
Zotero Advanced Search API Endpoints

This module provides REST API endpoints for advanced search functionality
including full-text search, faceted search, and similarity search.
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_user
from models.zotero_schemas import (
    ZoteroSearchRequest, ZoteroSearchResponse, ZoteroItemResponse
)
from services.zotero.zotero_search_service import get_search_service, ZoteroSearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zotero/search", tags=["Zotero Search"])


@router.post("/", response_model=ZoteroSearchResponse)
async def search_references(
    search_request: ZoteroSearchRequest,
    current_user: dict = Depends(get_current_user),
    search_service: ZoteroSearchService = Depends(get_search_service)
):
    """
    Perform advanced search across Zotero references
    
    Supports full-text search across all reference fields, faceted filtering,
    and relevance-based ranking. Search results include metadata about
    applied filters and processing time.
    """
    try:
        user_id = current_user["id"]
        results = await search_service.search_references(
            user_id=user_id,
            search_request=search_request
        )
        
        logger.info(f"User {user_id} performed search: '{search_request.query}' - {results.total_count} results")
        return results
        
    except Exception as e:
        logger.error(f"Search failed for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search operation failed"
        )


@router.get("/", response_model=ZoteroSearchResponse)
async def search_references_get(
    query: str = Query(..., min_length=1, max_length=1000, description="Search query"),
    library_id: Optional[str] = Query(None, description="Filter by library ID"),
    collection_id: Optional[str] = Query(None, description="Filter by collection ID"),
    item_type: Optional[str] = Query(None, description="Filter by item type"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    creators: Optional[List[str]] = Query(None, description="Filter by creators"),
    publication_year_start: Optional[int] = Query(None, description="Start year filter"),
    publication_year_end: Optional[int] = Query(None, description="End year filter"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Results offset"),
    sort_by: str = Query(default="relevance", description="Sort field"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: dict = Depends(get_current_user),
    search_service: ZoteroSearchService = Depends(get_search_service)
):
    """
    Perform advanced search using GET parameters
    
    Alternative endpoint for search functionality using query parameters
    instead of request body. Useful for bookmarkable search URLs.
    """
    try:
        # Build search request from query parameters
        search_request = ZoteroSearchRequest(
            query=query,
            library_id=library_id,
            collection_id=collection_id,
            item_type=item_type,
            tags=tags or [],
            creators=creators or [],
            publication_year_start=publication_year_start,
            publication_year_end=publication_year_end,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        user_id = current_user["id"]
        results = await search_service.search_references(
            user_id=user_id,
            search_request=search_request
        )
        
        logger.info(f"User {user_id} performed GET search: '{query}' - {results.total_count} results")
        return results
        
    except Exception as e:
        logger.error(f"GET search failed for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search operation failed"
        )


@router.get("/facets")
async def get_search_facets(
    library_id: Optional[str] = Query(None, description="Filter by library ID"),
    collection_id: Optional[str] = Query(None, description="Filter by collection ID"),
    current_user: dict = Depends(get_current_user),
    search_service: ZoteroSearchService = Depends(get_search_service)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get available facets for search filtering
    
    Returns facets (filters) available for the user's references including
    item types, publication years, creators, tags, and publishers with counts.
    """
    try:
        user_id = current_user["id"]
        facets = await search_service.get_search_facets(
            user_id=user_id,
            library_id=library_id,
            collection_id=collection_id
        )
        
        logger.info(f"User {user_id} requested search facets")
        return facets
        
    except Exception as e:
        logger.error(f"Failed to get search facets for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve search facets"
        )


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2, max_length=100, description="Partial search query"),
    limit: int = Query(default=10, ge=1, le=20, description="Maximum suggestions"),
    current_user: dict = Depends(get_current_user),
    search_service: ZoteroSearchService = Depends(get_search_service)
) -> List[str]:
    """
    Get search term suggestions
    
    Provides autocomplete suggestions based on partial input by searching
    through titles, tags, and creator names in the user's references.
    """
    try:
        user_id = current_user["id"]
        suggestions = await search_service.suggest_search_terms(
            user_id=user_id,
            partial_query=q,
            limit=limit
        )
        
        logger.info(f"User {user_id} requested search suggestions for: '{q}'")
        return suggestions
        
    except Exception as e:
        logger.error(f"Failed to get search suggestions for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve search suggestions"
        )


@router.get("/similar/{reference_id}", response_model=List[ZoteroItemResponse])
async def get_similar_references(
    reference_id: str,
    limit: int = Query(default=10, ge=1, le=20, description="Maximum similar references"),
    current_user: dict = Depends(get_current_user),
    search_service: ZoteroSearchService = Depends(get_search_service)
):
    """
    Find references similar to a given reference
    
    Uses similarity algorithms based on item type, publication year, tags,
    title words, and creators to find related references in the user's library.
    """
    try:
        user_id = current_user["id"]
        similar_refs = await search_service.get_similar_references(
            user_id=user_id,
            reference_id=reference_id,
            limit=limit
        )
        
        logger.info(f"User {user_id} requested similar references for: {reference_id}")
        return similar_refs
        
    except Exception as e:
        logger.error(f"Failed to get similar references for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve similar references"
        )


@router.get("/advanced")
async def advanced_search_form(
    current_user: dict = Depends(get_current_user),
    search_service: ZoteroSearchService = Depends(get_search_service)
):
    """
    Get advanced search form configuration
    
    Returns the configuration for building advanced search forms including
    available fields, operators, search options, and user-specific facets.
    """
    try:
        user_id = current_user["id"]
        
        # Get user's available facets for dynamic options
        facets = await search_service.get_search_facets(user_id=user_id)
        
        # Extract unique item types from user's library
        item_types = [facet["value"] for facet in facets.get("item_types", [])]
        
        # Extract top tags for suggestions
        top_tags = [facet["value"] for facet in facets.get("tags", [])[:20]]
        
        # Extract top creators for suggestions
        top_creators = [facet["value"] for facet in facets.get("creators", [])[:20]]
        
        return {
            "search_fields": [
                {
                    "name": "title",
                    "label": "Title",
                    "type": "text",
                    "operators": ["contains", "equals", "starts_with", "ends_with"],
                    "placeholder": "Enter title keywords..."
                },
                {
                    "name": "creators",
                    "label": "Authors/Creators",
                    "type": "text",
                    "operators": ["contains", "equals"],
                    "placeholder": "Enter author name...",
                    "suggestions": top_creators
                },
                {
                    "name": "publication_title",
                    "label": "Publication",
                    "type": "text",
                    "operators": ["contains", "equals", "starts_with"],
                    "placeholder": "Enter journal or publication name..."
                },
                {
                    "name": "publication_year",
                    "label": "Publication Year",
                    "type": "number",
                    "operators": ["equals", "greater_than", "less_than", "between"],
                    "min_year": min([facet["value"] for facet in facets.get("publication_years", [])]) if facets.get("publication_years") else 1900,
                    "max_year": max([facet["value"] for facet in facets.get("publication_years", [])]) if facets.get("publication_years") else 2024
                },
                {
                    "name": "item_type",
                    "label": "Item Type",
                    "type": "select",
                    "operators": ["equals"],
                    "options": item_types if item_types else [
                        "article", "book", "bookSection", "conferencePaper",
                        "thesis", "report", "webpage", "document"
                    ]
                },
                {
                    "name": "tags",
                    "label": "Tags",
                    "type": "text",
                    "operators": ["contains", "equals"],
                    "placeholder": "Enter tags...",
                    "suggestions": top_tags
                },
                {
                    "name": "abstract_note",
                    "label": "Abstract",
                    "type": "text",
                    "operators": ["contains"],
                    "placeholder": "Search in abstracts..."
                },
                {
                    "name": "doi",
                    "label": "DOI",
                    "type": "text",
                    "operators": ["equals", "contains"],
                    "placeholder": "Enter DOI..."
                },
                {
                    "name": "publisher",
                    "label": "Publisher",
                    "type": "text",
                    "operators": ["contains", "equals"],
                    "placeholder": "Enter publisher name..."
                }
            ],
            "sort_options": [
                {"value": "relevance", "label": "Relevance", "description": "Best matches first"},
                {"value": "title", "label": "Title", "description": "Alphabetical by title"},
                {"value": "date_added", "label": "Date Added", "description": "Recently added first"},
                {"value": "date_modified", "label": "Date Modified", "description": "Recently modified first"},
                {"value": "publication_year", "label": "Publication Year", "description": "By publication year"},
                {"value": "item_type", "label": "Item Type", "description": "Grouped by type"}
            ],
            "sort_orders": [
                {"value": "desc", "label": "Descending"},
                {"value": "asc", "label": "Ascending"}
            ],
            "search_tips": [
                "Use quotes for exact phrases: \"machine learning\"",
                "Use multiple terms to narrow results",
                "Try different spellings or synonyms",
                "Use filters to refine your search",
                "Sort by relevance for best matches"
            ],
            "facets": facets
        }
        
    except Exception as e:
        logger.error(f"Failed to get advanced search form for user {current_user['id']}: {str(e)}")
        # Return basic configuration on error
        return {
            "search_fields": [
                {
                    "name": "title",
                    "label": "Title",
                    "type": "text",
                    "operators": ["contains", "equals", "starts_with", "ends_with"]
                },
                {
                    "name": "creators",
                    "label": "Authors/Creators",
                    "type": "text",
                    "operators": ["contains", "equals"]
                }
            ],
            "sort_options": [
                {"value": "relevance", "label": "Relevance"},
                {"value": "title", "label": "Title"}
            ],
            "sort_orders": [
                {"value": "desc", "label": "Descending"},
                {"value": "asc", "label": "Ascending"}
            ]
        }


@router.post("/export")
async def export_search_results(
    search_request: ZoteroSearchRequest,
    export_format: str = Query(default="json", regex="^(json|csv|bibtex|ris)$"),
    current_user: dict = Depends(get_current_user),
    search_service: ZoteroSearchService = Depends(get_search_service)
):
    """
    Export search results in various formats
    
    Performs a search and exports the results in the specified format.
    Useful for saving search results or importing into other tools.
    """
    try:
        user_id = current_user["id"]
        
        # Perform the search
        results = await search_service.search_references(
            user_id=user_id,
            search_request=search_request
        )
        
        # Export based on format
        if export_format == "json":
            return {
                "format": "json",
                "query": search_request.query,
                "total_count": results.total_count,
                "items": [item.dict() for item in results.items],
                "exported_at": "2024-01-15T10:00:00Z"
            }
        
        elif export_format == "csv":
            # Convert to CSV format
            csv_data = "ID,Title,Authors,Publication,Year,DOI,Item Type\n"
            for item in results.items:
                authors = "; ".join([
                    f"{c.first_name or ''} {c.last_name or ''}".strip() or c.name or ""
                    for c in item.creators
                ])
                csv_data += f'"{item.id}","{item.title or ''}","{authors}","{item.publication_title or ''}","{item.publication_year or ''}","{item.doi or ''}","{item.item_type}"\n'
            
            return {
                "format": "csv",
                "data": csv_data,
                "filename": f"zotero_search_results_{search_request.query[:20]}.csv"
            }
        
        elif export_format == "bibtex":
            # Convert to BibTeX format (simplified)
            bibtex_data = ""
            for item in results.items:
                entry_type = "article" if item.item_type == "article" else "misc"
                bibtex_data += f"@{entry_type}{{{item.id},\n"
                if item.title:
                    bibtex_data += f"  title = {{{item.title}}},\n"
                if item.creators:
                    authors = " and ".join([
                        f"{c.first_name or ''} {c.last_name or ''}".strip() or c.name or ""
                        for c in item.creators
                    ])
                    bibtex_data += f"  author = {{{authors}}},\n"
                if item.publication_year:
                    bibtex_data += f"  year = {{{item.publication_year}}},\n"
                if item.publication_title:
                    bibtex_data += f"  journal = {{{item.publication_title}}},\n"
                if item.doi:
                    bibtex_data += f"  doi = {{{item.doi}}},\n"
                bibtex_data += "}\n\n"
            
            return {
                "format": "bibtex",
                "data": bibtex_data,
                "filename": f"zotero_search_results_{search_request.query[:20]}.bib"
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported export format: {export_format}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export search results for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export search results"
        )


@router.get("/stats")
async def get_search_statistics(
    current_user: dict = Depends(get_current_user),
    search_service: ZoteroSearchService = Depends(get_search_service)
):
    """
    Get search statistics for the user's library
    
    Returns statistics about the user's reference collection including
    total counts, distribution by type, and other useful metrics.
    """
    try:
        user_id = current_user["id"]
        
        # Get facets to calculate statistics
        facets = await search_service.get_search_facets(user_id=user_id)
        
        # Calculate statistics
        total_references = sum(facet["count"] for facet in facets.get("item_types", []))
        
        stats = {
            "total_references": total_references,
            "item_type_distribution": facets.get("item_types", []),
            "year_distribution": facets.get("publication_years", [])[:10],  # Top 10 years
            "top_creators": facets.get("creators", [])[:10],  # Top 10 creators
            "top_tags": facets.get("tags", [])[:20],  # Top 20 tags
            "top_publishers": facets.get("publishers", [])[:10],  # Top 10 publishers
            "generated_at": "2024-01-15T10:00:00Z"
        }
        
        logger.info(f"User {user_id} requested search statistics")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get search statistics for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve search statistics"
        )


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for search service"""
    return {
        "status": "healthy",
        "service": "zotero_search",
        "timestamp": "2024-01-15T10:00:00Z"
    }