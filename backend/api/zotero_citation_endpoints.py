"""
Zotero Citation API Endpoints

This module provides FastAPI endpoints for citation generation, bibliography creation,
and citation management functionality.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.logging_config import get_logger
from services.auth_service import get_current_user
from services.zotero.zotero_citation_service import ZoteroCitationService, CitationStyleError, CitationValidationError
from services.zotero.zotero_export_service import ZoteroExportService, ExportFormatError, ExportValidationError
from services.zotero.zotero_citation_management_service import ZoteroCitationManagementService, CitationManagementError
from models.zotero_schemas import (
    CitationRequest, CitationResponse, BibliographyRequest, BibliographyResponse,
    ZoteroExportRequest, ZoteroExportResponse
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/zotero/citations", tags=["zotero-citations"])


@router.post("/generate", response_model=CitationResponse)
async def generate_citations(
    request: CitationRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate citations for specified Zotero items
    
    Args:
        request: Citation generation request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CitationResponse with generated citations
        
    Raises:
        HTTPException: If citation generation fails
    """
    try:
        logger.info(f"Generating citations for user {current_user['user_id']}")
        
        citation_service = ZoteroCitationService(db)
        
        response = await citation_service.generate_citations(
            item_ids=request.item_ids,
            citation_style=request.citation_style,
            format_type=request.format,
            locale=request.locale,
            user_id=current_user['user_id']
        )
        
        logger.info(f"Generated {len(response.citations)} citations in {response.processing_time:.3f}s")
        return response
        
    except CitationValidationError as e:
        logger.warning(f"Citation validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except CitationStyleError as e:
        logger.error(f"Citation style error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error generating citations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate citations"
        )


@router.post("/bibliography", response_model=BibliographyResponse)
async def generate_bibliography(
    request: BibliographyRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate bibliography for specified Zotero items
    
    Args:
        request: Bibliography generation request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        BibliographyResponse with generated bibliography
        
    Raises:
        HTTPException: If bibliography generation fails
    """
    try:
        logger.info(f"Generating bibliography for user {current_user['user_id']}")
        
        citation_service = ZoteroCitationService(db)
        
        response = await citation_service.generate_bibliography(
            item_ids=request.item_ids,
            citation_style=request.citation_style,
            format_type=request.format,
            sort_by=request.sort_by,
            user_id=current_user['user_id']
        )
        
        logger.info(f"Generated bibliography with {response.item_count} items in {response.processing_time:.3f}s")
        return response
        
    except CitationValidationError as e:
        logger.warning(f"Bibliography validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except CitationStyleError as e:
        logger.error(f"Bibliography style error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error generating bibliography: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate bibliography"
        )


@router.post("/validate/{item_id}")
async def validate_citation_data(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate citation data for a specific item
    
    Args:
        item_id: Zotero item ID to validate
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Validation results with missing fields and warnings
        
    Raises:
        HTTPException: If validation fails or item not found
    """
    try:
        logger.info(f"Validating citation data for item {item_id}")
        
        citation_service = ZoteroCitationService(db)
        
        # Get the item first
        items = await citation_service._get_items_by_ids([item_id])
        if not items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        validation_result = await citation_service.validate_citation_data(items[0])
        
        logger.info(f"Validation completed for item {item_id}: valid={validation_result['is_valid']}")
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error validating citation data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate citation data"
        )


@router.get("/styles")
async def get_supported_citation_styles(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of supported citation styles
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dictionary of supported citation styles
    """
    try:
        citation_service = ZoteroCitationService(db)
        styles = await citation_service.get_supported_styles()
        
        return {
            "styles": styles,
            "count": len(styles)
        }
        
    except Exception as e:
        logger.error(f"Error getting citation styles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get citation styles"
        )


@router.get("/formats")
async def get_supported_formats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of supported output formats
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of supported output formats
    """
    try:
        citation_service = ZoteroCitationService(db)
        formats = await citation_service.get_supported_formats()
        
        return {
            "formats": formats,
            "count": len(formats)
        }
        
    except Exception as e:
        logger.error(f"Error getting output formats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get output formats"
        )


@router.post("/batch-validate")
async def batch_validate_citation_data(
    item_ids: List[str],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate citation data for multiple items
    
    Args:
        item_ids: List of Zotero item IDs to validate
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Batch validation results
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        if len(item_ids) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many items for batch validation (max 100)"
            )
        
        logger.info(f"Batch validating {len(item_ids)} items for user {current_user['user_id']}")
        
        citation_service = ZoteroCitationService(db)
        
        # Get all items
        items = await citation_service._get_items_by_ids(item_ids)
        
        # Validate each item
        validation_results = []
        for item in items:
            try:
                result = await citation_service.validate_citation_data(item)
                result['item_id'] = item.id
                validation_results.append(result)
            except Exception as e:
                logger.warning(f"Failed to validate item {item.id}: {str(e)}")
                validation_results.append({
                    'item_id': item.id,
                    'is_valid': False,
                    'error': str(e)
                })
        
        # Summary statistics
        valid_count = sum(1 for r in validation_results if r.get('is_valid', False))
        invalid_count = len(validation_results) - valid_count
        
        return {
            "results": validation_results,
            "summary": {
                "total_items": len(validation_results),
                "valid_items": valid_count,
                "invalid_items": invalid_count,
                "validation_rate": valid_count / len(validation_results) if validation_results else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in batch validation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform batch validation"
        )


@router.get("/preview/{item_id}")
async def preview_citation(
    item_id: str,
    style: str = "apa",
    format_type: str = "text",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Preview citation for a single item in different styles
    
    Args:
        item_id: Zotero item ID
        style: Citation style to preview
        format_type: Output format
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Citation preview
        
    Raises:
        HTTPException: If preview generation fails
    """
    try:
        logger.info(f"Generating citation preview for item {item_id}")
        
        citation_service = ZoteroCitationService(db)
        
        response = await citation_service.generate_citations(
            item_ids=[item_id],
            citation_style=style,
            format_type=format_type,
            user_id=current_user['user_id']
        )
        
        if not response.citations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found or citation could not be generated"
            )
        
        return {
            "item_id": item_id,
            "citation": response.citations[0],
            "style": response.style_used,
            "format": response.format,
            "processing_time": response.processing_time
        }
        
    except HTTPException:
        raise
    except CitationValidationError as e:
        logger.warning(f"Citation preview validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error generating citation preview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate citation preview"
        )


@router.post("/export", response_model=ZoteroExportResponse)
async def export_references(
    request: ZoteroExportRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export references to specified format
    
    Args:
        request: Export request with format and options
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ZoteroExportResponse with exported data
        
    Raises:
        HTTPException: If export fails
    """
    try:
        logger.info(f"Exporting {len(request.item_ids)} references to {request.export_format} for user {current_user['user_id']}")
        
        export_service = ZoteroExportService(db)
        
        response = await export_service.export_references(
            item_ids=request.item_ids,
            export_format=request.export_format,
            include_attachments=request.include_attachments,
            include_notes=request.include_notes,
            user_id=current_user['user_id']
        )
        
        logger.info(f"Exported {response.item_count} items in {response.processing_time:.3f}s")
        return response
        
    except ExportValidationError as e:
        logger.warning(f"Export validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ExportFormatError as e:
        logger.error(f"Export format error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error exporting references: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export references"
        )


@router.get("/export/formats")
async def get_supported_export_formats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of supported export formats
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dictionary of supported export formats
    """
    try:
        export_service = ZoteroExportService(db)
        formats = await export_service.get_supported_formats()
        
        return {
            "formats": formats,
            "count": len(formats)
        }
        
    except Exception as e:
        logger.error(f"Error getting export formats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get export formats"
        )


@router.post("/batch-export")
async def batch_export_by_collection(
    collection_id: str,
    export_format: str = "bibtex",
    include_attachments: bool = False,
    include_notes: bool = True,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export all references from a collection
    
    Args:
        collection_id: Collection ID to export
        export_format: Export format
        include_attachments: Whether to include attachment info
        include_notes: Whether to include notes
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Export response with all collection items
        
    Raises:
        HTTPException: If export fails
    """
    try:
        logger.info(f"Batch exporting collection {collection_id} to {export_format}")
        
        # Get all items in the collection
        from models.zotero_models import ZoteroItemCollection
        
        item_ids = db.query(ZoteroItemCollection.item_id).filter(
            ZoteroItemCollection.collection_id == collection_id
        ).all()
        
        if not item_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found or empty"
            )
        
        item_ids = [item_id[0] for item_id in item_ids]
        
        export_service = ZoteroExportService(db)
        
        response = await export_service.export_references(
            item_ids=item_ids,
            export_format=export_format,
            include_attachments=include_attachments,
            include_notes=include_notes,
            user_id=current_user['user_id']
        )
        
        logger.info(f"Batch exported {response.item_count} items from collection")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in batch export: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform batch export"
        )


@router.post("/batch-bibliography")
async def generate_batch_bibliography(
    item_ids: List[str],
    citation_style: str = "apa",
    format_type: str = "text",
    sort_by: str = "author",
    batch_size: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate bibliography for large batches of items with progress tracking
    
    Args:
        item_ids: List of Zotero item IDs
        citation_style: Citation style to use
        format_type: Output format
        sort_by: Sort order for bibliography
        batch_size: Number of items to process per batch
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Bibliography response with processing metadata
        
    Raises:
        HTTPException: If bibliography generation fails
    """
    try:
        if len(item_ids) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many items for batch bibliography (max 1000)"
            )
        
        logger.info(f"Generating batch bibliography for {len(item_ids)} items")
        
        citation_service = ZoteroCitationService(db)
        
        response = await citation_service.generate_bibliography(
            item_ids=item_ids,
            citation_style=citation_style,
            format_type=format_type,
            sort_by=sort_by,
            user_id=current_user['user_id']
        )
        
        logger.info(f"Generated batch bibliography with {response.item_count} items in {response.processing_time:.3f}s")
        return response
        
    except CitationValidationError as e:
        logger.warning(f"Batch bibliography validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except CitationStyleError as e:
        logger.error(f"Batch bibliography style error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error generating batch bibliography: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate batch bibliography"
        )


@router.post("/batch-citations")
async def generate_batch_citations(
    item_ids: List[str],
    citation_style: str = "apa",
    format_type: str = "text",
    batch_size: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate citations for large batches of items with detailed progress tracking
    
    Args:
        item_ids: List of Zotero item IDs
        citation_style: Citation style to use
        format_type: Output format
        batch_size: Number of items to process per batch
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Detailed batch citation response with per-item status
        
    Raises:
        HTTPException: If batch citation generation fails
    """
    try:
        if len(item_ids) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many items for batch citations (max 1000)"
            )
        
        logger.info(f"Generating batch citations for {len(item_ids)} items")
        
        citation_service = ZoteroCitationService(db)
        
        response = await citation_service.generate_batch_citations(
            item_ids=item_ids,
            citation_style=citation_style,
            format_type=format_type,
            batch_size=batch_size,
            user_id=current_user['user_id']
        )
        
        logger.info(f"Generated {response['successful_items']}/{response['total_items']} citations in {response['processing_time']:.3f}s")
        return response
        
    except CitationValidationError as e:
        logger.warning(f"Batch citations validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except CitationStyleError as e:
        logger.error(f"Batch citations style error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error generating batch citations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate batch citations"
        )


# Citation Management Endpoints

@router.get("/history")
async def get_citation_history(
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's citation history
    
    Args:
        limit: Maximum number of entries to return
        offset: Number of entries to skip
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Citation history with pagination metadata
    """
    try:
        management_service = ZoteroCitationManagementService(db)
        
        history = await management_service.get_citation_history(
            user_id=current_user['user_id'],
            limit=limit,
            offset=offset
        )
        
        return history
        
    except Exception as e:
        logger.error(f"Error getting citation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get citation history"
        )


@router.delete("/history")
async def clear_citation_history(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clear user's citation history
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    try:
        management_service = ZoteroCitationManagementService(db)
        
        await management_service.clear_citation_history(
            user_id=current_user['user_id']
        )
        
        return {"message": "Citation history cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing citation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear citation history"
        )


@router.post("/favorites")
async def add_to_favorites(
    item_id: str,
    citation_style: str = "apa",
    format_type: str = "text",
    note: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add citation to user's favorites
    
    Args:
        item_id: Item ID to add to favorites
        citation_style: Citation style to use
        format_type: Output format
        note: Optional user note
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Favorite ID and citation
    """
    try:
        # Generate citation first
        citation_service = ZoteroCitationService(db)
        response = await citation_service.generate_citations(
            item_ids=[item_id],
            citation_style=citation_style,
            format_type=format_type,
            user_id=current_user['user_id']
        )
        
        if not response.citations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found or citation could not be generated"
            )
        
        # Add to favorites
        management_service = ZoteroCitationManagementService(db)
        favorite_id = await management_service.add_to_favorites(
            user_id=current_user['user_id'],
            item_id=item_id,
            citation_style=citation_style,
            format_type=format_type,
            citation=response.citations[0],
            note=note
        )
        
        return {
            "favorite_id": favorite_id,
            "citation": response.citations[0],
            "message": "Citation added to favorites"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding citation to favorites: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add citation to favorites"
        )


@router.get("/favorites")
async def get_citation_favorites(
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's favorite citations
    
    Args:
        limit: Maximum number of entries to return
        offset: Number of entries to skip
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Favorite citations with pagination metadata
    """
    try:
        management_service = ZoteroCitationManagementService(db)
        
        favorites = await management_service.get_citation_favorites(
            user_id=current_user['user_id'],
            limit=limit,
            offset=offset
        )
        
        return favorites
        
    except Exception as e:
        logger.error(f"Error getting citation favorites: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get citation favorites"
        )


@router.delete("/favorites/{favorite_id}")
async def remove_from_favorites(
    favorite_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove citation from user's favorites
    
    Args:
        favorite_id: Favorite ID to remove
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    try:
        management_service = ZoteroCitationManagementService(db)
        
        removed = await management_service.remove_from_favorites(
            user_id=current_user['user_id'],
            favorite_id=favorite_id
        )
        
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Favorite not found"
            )
        
        return {"message": "Citation removed from favorites"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing citation from favorites: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove citation from favorites"
        )


@router.get("/style-preview/{item_id}")
async def preview_citation_styles(
    item_id: str,
    styles: Optional[str] = None,  # Comma-separated list
    format_type: str = "text",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Preview citation in multiple styles
    
    Args:
        item_id: Item ID to preview
        styles: Comma-separated list of styles (optional)
        format_type: Output format
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dictionary mapping style names to citation previews
    """
    try:
        management_service = ZoteroCitationManagementService(db)
        
        style_list = None
        if styles:
            style_list = [s.strip() for s in styles.split(',')]
        
        previews = await management_service.preview_citation_styles(
            item_id=item_id,
            styles=style_list,
            format_type=format_type,
            user_id=current_user['user_id']
        )
        
        return {
            "item_id": item_id,
            "format": format_type,
            "previews": previews,
            "style_count": len(previews)
        }
        
    except Exception as e:
        logger.error(f"Error generating style previews: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate style previews"
        )


@router.post("/clipboard")
async def prepare_clipboard_data(
    request: dict,  # Will contain citations, format_type, include_metadata
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Prepare citation data for clipboard integration
    
    Args:
        request: Dictionary with citations, format_type, and include_metadata
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Clipboard-ready data in multiple formats
    """
    try:
        citations = request.get('citations', [])
        format_type = request.get('format_type', 'text')
        include_metadata = request.get('include_metadata', False)
        
        if not citations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No citations provided"
            )
        
        management_service = ZoteroCitationManagementService(db)
        
        clipboard_data = await management_service.get_clipboard_data(
            citations=citations,
            format_type=format_type,
            include_metadata=include_metadata
        )
        
        return clipboard_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error preparing clipboard data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to prepare clipboard data"
        )


@router.get("/statistics")
async def get_citation_statistics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get citation usage statistics for the current user
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Citation usage statistics
    """
    try:
        management_service = ZoteroCitationManagementService(db)
        
        statistics = await management_service.get_citation_statistics(
            user_id=current_user['user_id']
        )
        
        return statistics
        
    except Exception as e:
        logger.error(f"Error getting citation statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get citation statistics"
        )


@router.post("/history/search")
async def search_citation_history(
    query: str,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search through user's citation history
    
    Args:
        query: Search query
        limit: Maximum results to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Matching citation history entries
    """
    try:
        management_service = ZoteroCitationManagementService(db)
        
        results = await management_service.search_citation_history(
            user_id=current_user['user_id'],
            query=query,
            limit=limit
        )
        
        return {
            "results": results,
            "query": query,
            "result_count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching citation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search citation history"
        )


@router.get("/history/export")
async def export_citation_history(
    export_format: str = "json",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export user's citation history
    
    Args:
        export_format: Export format (json, csv)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Exported citation history data
    """
    try:
        management_service = ZoteroCitationManagementService(db)
        
        exported_data = await management_service.export_citation_history(
            user_id=current_user['user_id'],
            export_format=export_format
        )
        
        # Set appropriate content type
        if export_format == "csv":
            content_type = "text/csv"
            filename = f"citation_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        else:
            content_type = "application/json"
            filename = f"citation_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        from fastapi.responses import Response
        return Response(
            content=exported_data,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting citation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export citation history"
        )


@router.put("/favorites/{favorite_id}/access")
async def update_favorite_access(
    favorite_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update access count for a favorite citation
    
    Args:
        favorite_id: Favorite ID to update
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    try:
        management_service = ZoteroCitationManagementService(db)
        
        updated = await management_service.update_favorite_access(
            user_id=current_user['user_id'],
            favorite_id=favorite_id
        )
        
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Favorite not found"
            )
        
        return {"message": "Favorite access updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating favorite access: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update favorite access"
        )


@router.post("/cleanup")
async def cleanup_old_citation_data(
    days_to_keep: int = 90,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clean up old citation data (admin function)
    
    Args:
        days_to_keep: Number of days of data to keep
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Cleanup statistics
    """
    try:
        # This could be restricted to admin users in production
        management_service = ZoteroCitationManagementService(db)
        
        cleanup_stats = await management_service.cleanup_old_data(
            days_to_keep=days_to_keep
        )
        
        return cleanup_stats
        
    except Exception as e:
        logger.error(f"Error cleaning up citation data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup citation data"
        ) "text",
    include_metadata: bool = False,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Prepare citation data for clipboard integration
    
    Args:
        citations: List of citations to prepare
        format_type: Output format
        include_metadata: Whether to include metadata
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Clipboard-ready data
    """
    try:
        management_service = ZoteroCitationManagementService(db)
        
        clipboard_data = await management_service.get_clipboard_data(
            citations=citations,
            format_type=format_type,
            include_metadata=include_metadata
        )
        
        return clipboard_data
        
    except Exception as e:
        logger.error(f"Error preparing clipboard data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to prepare clipboard data"
        )


@router.get("/statistics")
async def get_citation_statistics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get citation usage statistics for user
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Usage statistics
    """
    try:
        management_service = ZoteroCitationManagementService(db)
        
        statistics = await management_service.get_citation_statistics(
            user_id=current_user['user_id']
        )
        
        return statistics
        
    except Exception as e:
        logger.error(f"Error getting citation statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get citation statistics"
        )


@router.get("/history/search")
async def search_citation_history(
    query: str,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search through user's citation history
    
    Args:
        query: Search query
        limit: Maximum results to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Matching history entries
    """
    try:
        if not query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query cannot be empty"
            )
        
        management_service = ZoteroCitationManagementService(db)
        
        results = await management_service.search_citation_history(
            user_id=current_user['user_id'],
            query=query,
            limit=limit
        )
        
        return {
            "query": query,
            "results": results,
            "result_count": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching citation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search citation history"
        )


@router.get("/history/export")
async def export_citation_history(
    export_format: str = "json",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export user's citation history
    
    Args:
        export_format: Export format (json, csv)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Exported data
    """
    try:
        if export_format not in ['json', 'csv']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported export format. Use 'json' or 'csv'"
            )
        
        management_service = ZoteroCitationManagementService(db)
        
        exported_data = await management_service.export_citation_history(
            user_id=current_user['user_id'],
            export_format=export_format
        )
        
        # Set appropriate content type
        if export_format == 'json':
            media_type = "application/json"
            filename = f"citation_history_{current_user['user_id']}.json"
        else:
            media_type = "text/csv"
            filename = f"citation_history_{current_user['user_id']}.csv"
        
        from fastapi.responses import Response
        
        return Response(
            content=exported_data,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting citation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export citation history"
        )