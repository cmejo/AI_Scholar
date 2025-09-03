"""
Zotero Reference Management API Endpoints

This module provides REST API endpoints for managing Zotero references,
including CRUD operations, validation, and data integrity checks.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_user
from models.zotero_schemas import (
    ZoteroItemCreate, ZoteroItemUpdate, ZoteroItemResponse,
    ZoteroSearchRequest, ZoteroSearchResponse
)
from services.zotero.zotero_reference_service import get_reference_service, ZoteroReferenceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zotero/references", tags=["Zotero References"])


@router.post("/", response_model=ZoteroItemResponse, status_code=status.HTTP_201_CREATED)
async def create_reference(
    reference_data: ZoteroItemCreate,
    library_id: str = Query(..., description="Library ID to add reference to"),
    current_user: dict = Depends(get_current_user),
    reference_service: ZoteroReferenceService = Depends(get_reference_service)
):
    """
    Create a new reference item
    
    Creates a new reference with validation and metadata indexing.
    The reference will be added to the specified library and optionally to collections.
    """
    try:
        user_id = current_user["id"]
        reference = await reference_service.create_reference(
            user_id=user_id,
            library_id=library_id,
            reference_data=reference_data
        )
        
        logger.info(f"User {user_id} created reference {reference.id}")
        return reference
        
    except PermissionError as e:
        logger.warning(f"Permission denied for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create reference: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create reference"
        )


@router.get("/{reference_id}", response_model=ZoteroItemResponse)
async def get_reference(
    reference_id: str,
    current_user: dict = Depends(get_current_user),
    reference_service: ZoteroReferenceService = Depends(get_reference_service)
):
    """
    Get a reference by ID
    
    Retrieves a reference item with all related data including creators,
    collections, and attachments.
    """
    try:
        reference = await reference_service.get_reference(reference_id)
        
        if not reference:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reference not found"
            )
        
        # Verify user has access (this is handled in the service layer)
        user_id = current_user["id"]
        accessible_reference = await reference_service._get_reference_with_access_check(
            user_id, reference_id
        )
        
        if not accessible_reference:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this reference"
            )
        
        return reference
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get reference {reference_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reference"
        )


@router.put("/{reference_id}", response_model=ZoteroItemResponse)
async def update_reference(
    reference_id: str,
    update_data: ZoteroItemUpdate,
    current_user: dict = Depends(get_current_user),
    reference_service: ZoteroReferenceService = Depends(get_reference_service)
):
    """
    Update a reference item
    
    Updates an existing reference with validation. Only provided fields
    will be updated, others will remain unchanged.
    """
    try:
        user_id = current_user["id"]
        reference = await reference_service.update_reference(
            user_id=user_id,
            reference_id=reference_id,
            update_data=update_data
        )
        
        if not reference:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reference not found"
            )
        
        logger.info(f"User {user_id} updated reference {reference_id}")
        return reference
        
    except PermissionError as e:
        logger.warning(f"Permission denied for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update reference {reference_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update reference"
        )


@router.delete("/{reference_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reference(
    reference_id: str,
    current_user: dict = Depends(get_current_user),
    reference_service: ZoteroReferenceService = Depends(get_reference_service)
):
    """
    Delete a reference item
    
    Performs a soft delete of the reference item. The reference will be
    marked as deleted but not physically removed from the database.
    """
    try:
        user_id = current_user["id"]
        deleted = await reference_service.delete_reference(
            user_id=user_id,
            reference_id=reference_id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reference not found"
            )
        
        logger.info(f"User {user_id} deleted reference {reference_id}")
        
    except PermissionError as e:
        logger.warning(f"Permission denied for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to delete reference {reference_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete reference"
        )


@router.get("/library/{library_id}", response_model=List[ZoteroItemResponse])
async def get_library_references(
    library_id: str,
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(default=0, ge=0, description="Results offset"),
    sort_by: str = Query(default="date_modified", description="Field to sort by"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: dict = Depends(get_current_user),
    reference_service: ZoteroReferenceService = Depends(get_reference_service)
):
    """
    Get references from a specific library
    
    Retrieves references from a library with pagination and sorting options.
    Only returns references the user has access to.
    """
    try:
        user_id = current_user["id"]
        references, total_count = await reference_service.get_references_by_library(
            user_id=user_id,
            library_id=library_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Add pagination headers
        from fastapi import Response
        response = Response()
        response.headers["X-Total-Count"] = str(total_count)
        response.headers["X-Limit"] = str(limit)
        response.headers["X-Offset"] = str(offset)
        
        return references
        
    except PermissionError as e:
        logger.warning(f"Permission denied for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get library references: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve library references"
        )


@router.get("/collection/{collection_id}", response_model=List[ZoteroItemResponse])
async def get_collection_references(
    collection_id: str,
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(default=0, ge=0, description="Results offset"),
    sort_by: str = Query(default="date_modified", description="Field to sort by"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: dict = Depends(get_current_user),
    reference_service: ZoteroReferenceService = Depends(get_reference_service)
):
    """
    Get references from a specific collection
    
    Retrieves references from a collection with pagination and sorting options.
    Only returns references the user has access to.
    """
    try:
        user_id = current_user["id"]
        references, total_count = await reference_service.get_references_by_collection(
            user_id=user_id,
            collection_id=collection_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Add pagination headers
        from fastapi import Response
        response = Response()
        response.headers["X-Total-Count"] = str(total_count)
        response.headers["X-Limit"] = str(limit)
        response.headers["X-Offset"] = str(offset)
        
        return references
        
    except PermissionError as e:
        logger.warning(f"Permission denied for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get collection references: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collection references"
        )


@router.post("/integrity/check")
async def check_data_integrity(
    library_id: Optional[str] = Query(None, description="Optional library ID to check"),
    current_user: dict = Depends(get_current_user),
    reference_service: ZoteroReferenceService = Depends(get_reference_service)
):
    """
    Check data integrity for references
    
    Performs comprehensive data integrity checks including orphaned references,
    missing required fields, duplicate DOIs, and invalid data.
    """
    try:
        user_id = current_user["id"]
        
        # If library_id is provided, validate access
        if library_id:
            await reference_service._validate_library_access(user_id, library_id)
        
        results = await reference_service.check_data_integrity(library_id)
        
        logger.info(f"User {user_id} performed integrity check")
        return results
        
    except PermissionError as e:
        logger.warning(f"Permission denied for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to check data integrity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check data integrity"
        )


@router.post("/integrity/repair")
async def repair_data_integrity(
    library_id: Optional[str] = Query(None, description="Optional library ID to repair"),
    current_user: dict = Depends(get_current_user),
    reference_service: ZoteroReferenceService = Depends(get_reference_service)
):
    """
    Repair data integrity issues
    
    Attempts to automatically repair common data integrity issues such as
    orphaned relationships and missing required fields.
    """
    try:
        user_id = current_user["id"]
        
        # If library_id is provided, validate access
        if library_id:
            await reference_service._validate_library_access(user_id, library_id)
        
        results = await reference_service.repair_data_integrity(library_id)
        
        logger.info(f"User {user_id} performed integrity repair")
        return results
        
    except PermissionError as e:
        logger.warning(f"Permission denied for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to repair data integrity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to repair data integrity"
        )


@router.get("/{reference_id}/validate")
async def validate_reference(
    reference_id: str,
    current_user: dict = Depends(get_current_user),
    reference_service: ZoteroReferenceService = Depends(get_reference_service)
):
    """
    Validate a specific reference
    
    Performs validation checks on a specific reference and returns
    any validation errors or warnings.
    """
    try:
        user_id = current_user["id"]
        
        # Get the reference with access check
        reference = await reference_service._get_reference_with_access_check(
            user_id, reference_id
        )
        
        if not reference:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reference not found"
            )
        
        # Perform validation
        validation_results = {
            "reference_id": reference_id,
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required fields
        if not reference.item_type:
            validation_results["errors"].append("Missing item_type")
            validation_results["is_valid"] = False
        
        # Check DOI format
        if reference.doi and not reference_service._is_valid_doi(reference.doi):
            validation_results["errors"].append("Invalid DOI format")
            validation_results["is_valid"] = False
        
        # Check ISBN format
        if reference.isbn and not reference_service._is_valid_isbn(reference.isbn):
            validation_results["errors"].append("Invalid ISBN format")
            validation_results["is_valid"] = False
        
        # Check ISSN format
        if reference.issn and not reference_service._is_valid_issn(reference.issn):
            validation_results["errors"].append("Invalid ISSN format")
            validation_results["is_valid"] = False
        
        # Check URL format
        if reference.url and not reference_service._is_valid_url(reference.url):
            validation_results["errors"].append("Invalid URL format")
            validation_results["is_valid"] = False
        
        # Check publication year
        if reference.publication_year:
            from datetime import datetime
            current_year = datetime.now().year
            if reference.publication_year < 1000 or reference.publication_year > current_year + 5:
                validation_results["errors"].append("Invalid publication year")
                validation_results["is_valid"] = False
        
        # Check for missing title
        if not reference.title or reference.title.strip() == "":
            validation_results["warnings"].append("Missing title")
        
        # Check for missing creators
        if not reference.creators or len(reference.creators) == 0:
            validation_results["warnings"].append("No creators specified")
        
        return validation_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate reference {reference_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate reference"
        )


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for reference management system"""
    return {
        "status": "healthy",
        "service": "zotero_reference_management",
        "timestamp": "2024-01-15T10:00:00Z"
    }