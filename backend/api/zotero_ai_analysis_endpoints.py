"""
FastAPI endpoints for Zotero AI analysis features
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from core.auth import get_current_user
from services.zotero.zotero_ai_analysis_service import ZoteroAIAnalysisService
from models.schemas import User

router = APIRouter(prefix="/zotero/ai-analysis", tags=["zotero-ai-analysis"])


# Request/Response Schemas
class AnalysisRequest(BaseModel):
    """Schema for analysis request"""
    analysis_types: List[str] = Field(
        default=["topics", "keywords", "summary"],
        description="Types of analysis to perform"
    )


class BatchAnalysisRequest(BaseModel):
    """Schema for batch analysis request"""
    item_ids: List[str] = Field(..., min_items=1, max_items=50, description="Item IDs to analyze")
    analysis_types: List[str] = Field(
        default=["topics", "keywords", "summary"],
        description="Types of analysis to perform"
    )


class AnalysisResponse(BaseModel):
    """Schema for analysis response"""
    item_id: str = Field(..., description="Item ID")
    analysis_timestamp: str = Field(..., description="Analysis timestamp")
    analysis_types: List[str] = Field(..., description="Types of analysis performed")
    results: Dict[str, Any] = Field(..., description="Analysis results")


class BatchAnalysisResponse(BaseModel):
    """Schema for batch analysis response"""
    batch_id: str = Field(..., description="Batch ID")
    timestamp: str = Field(..., description="Batch timestamp")
    total_items: int = Field(..., description="Total items processed")
    successful: int = Field(..., description="Successfully processed items")
    failed: int = Field(..., description="Failed items")
    results: Dict[str, AnalysisResponse] = Field(..., description="Analysis results by item ID")
    errors: List[Dict[str, str]] = Field(..., description="Error details for failed items")


# Initialize service
ai_analysis_service = ZoteroAIAnalysisService()


@router.post("/analyze/{item_id}", response_model=AnalysisResponse)
async def analyze_reference_content(
    item_id: str,
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze reference content using AI
    
    Performs AI-enhanced analysis of a Zotero reference including:
    - Topic extraction and theme identification
    - Keyword extraction (technical and general)
    - Content summarization with key findings
    
    Args:
        item_id: Zotero item ID to analyze
        request: Analysis configuration
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Analysis results including topics, keywords, and summary
        
    Raises:
        HTTPException: If item not found, access denied, or analysis fails
    """
    try:
        # Validate analysis types
        valid_types = {"topics", "keywords", "summary"}
        invalid_types = set(request.analysis_types) - valid_types
        if invalid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid analysis types: {list(invalid_types)}. Valid types: {list(valid_types)}"
            )
        
        result = await ai_analysis_service.analyze_reference_content(
            item_id=item_id,
            user_id=current_user.id,
            analysis_types=request.analysis_types
        )
        
        return AnalysisResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/batch", response_model=BatchAnalysisResponse)
async def batch_analyze_references(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze multiple references in batch
    
    Performs AI analysis on multiple Zotero references simultaneously.
    For large batches, processing may continue in the background.
    
    Args:
        request: Batch analysis configuration
        background_tasks: Background task manager
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Batch analysis results with success/failure counts
        
    Raises:
        HTTPException: If request invalid or batch processing fails
    """
    try:
        # Validate analysis types
        valid_types = {"topics", "keywords", "summary"}
        invalid_types = set(request.analysis_types) - valid_types
        if invalid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid analysis types: {list(invalid_types)}. Valid types: {list(valid_types)}"
            )
        
        # For small batches, process synchronously
        if len(request.item_ids) <= 10:
            result = await ai_analysis_service.batch_analyze_references(
                item_ids=request.item_ids,
                user_id=current_user.id,
                analysis_types=request.analysis_types
            )
        else:
            # For larger batches, process in background
            background_tasks.add_task(
                ai_analysis_service.batch_analyze_references,
                item_ids=request.item_ids,
                user_id=current_user.id,
                analysis_types=request.analysis_types
            )
            
            # Return immediate response for background processing
            result = {
                "batch_id": f"batch_{int(datetime.utcnow().timestamp())}",
                "timestamp": datetime.utcnow().isoformat(),
                "total_items": len(request.item_ids),
                "successful": 0,
                "failed": 0,
                "results": {},
                "errors": [],
                "status": "processing_in_background"
            }
        
        return BatchAnalysisResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@router.get("/results/{item_id}", response_model=Optional[AnalysisResponse])
async def get_analysis_results(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get stored analysis results for a reference
    
    Retrieves previously computed AI analysis results for a Zotero reference.
    Returns None if no analysis has been performed.
    
    Args:
        item_id: Zotero item ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Stored analysis results or None if not found
        
    Raises:
        HTTPException: If item not found or access denied
    """
    try:
        result = await ai_analysis_service.get_analysis_results(
            item_id=item_id,
            user_id=current_user.id
        )
        
        if result is None:
            return None
            
        return AnalysisResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analysis results: {str(e)}")


@router.get("/supported-types")
async def get_supported_analysis_types():
    """
    Get supported analysis types
    
    Returns the list of supported AI analysis types and their descriptions.
    
    Returns:
        Dictionary of supported analysis types with descriptions
    """
    return {
        "supported_types": {
            "topics": {
                "name": "Topic Extraction",
                "description": "Extract primary research topics, themes, and research domain",
                "outputs": ["primary_topics", "secondary_themes", "research_domain", "methodology"]
            },
            "keywords": {
                "name": "Keyword Extraction", 
                "description": "Extract technical and general keywords from content",
                "outputs": ["technical_keywords", "general_keywords", "author_keywords", "suggested_keywords"]
            },
            "summary": {
                "name": "Content Summarization",
                "description": "Generate AI summary with key findings and implications",
                "outputs": ["concise_summary", "key_findings", "methodology", "significance", "limitations"]
            }
        },
        "default_types": ["topics", "keywords", "summary"],
        "max_batch_size": 50
    }


@router.delete("/results/{item_id}")
async def delete_analysis_results(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete stored analysis results for a reference
    
    Removes AI analysis results from the item's metadata.
    This action cannot be undone.
    
    Args:
        item_id: Zotero item ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Success confirmation
        
    Raises:
        HTTPException: If item not found, access denied, or deletion fails
    """
    try:
        # Get the item with access control
        from models.zotero_models import ZoteroItem, ZoteroLibrary, ZoteroConnection
        from sqlalchemy import and_
        
        item = db.query(ZoteroItem).join(
            ZoteroLibrary, ZoteroItem.library_id == ZoteroLibrary.id
        ).join(
            ZoteroConnection, ZoteroLibrary.connection_id == ZoteroConnection.id
        ).filter(
            and_(
                ZoteroItem.id == item_id,
                ZoteroConnection.user_id == current_user.id,
                ZoteroItem.is_deleted == False
            )
        ).first()
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found or access denied")
        
        # Remove analysis results from metadata
        if item.item_metadata and "ai_analysis" in item.item_metadata:
            metadata = dict(item.item_metadata)
            del metadata["ai_analysis"]
            item.item_metadata = metadata
            db.commit()
            
            return {"message": "Analysis results deleted successfully"}
        else:
            return {"message": "No analysis results found to delete"}
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete analysis results: {str(e)}")


@router.get("/stats/{library_id}")
async def get_analysis_statistics(
    library_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get analysis statistics for a library
    
    Returns statistics about AI analysis coverage and results for a Zotero library.
    
    Args:
        library_id: Zotero library ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Analysis statistics including coverage and topic distribution
        
    Raises:
        HTTPException: If library not found or access denied
    """
    try:
        from models.zotero_models import ZoteroItem, ZoteroLibrary, ZoteroConnection
        from sqlalchemy import and_, func
        
        # Verify library access
        library = db.query(ZoteroLibrary).join(
            ZoteroConnection, ZoteroLibrary.connection_id == ZoteroConnection.id
        ).filter(
            and_(
                ZoteroLibrary.id == library_id,
                ZoteroConnection.user_id == current_user.id
            )
        ).first()
        
        if not library:
            raise HTTPException(status_code=404, detail="Library not found or access denied")
        
        # Get total items in library
        total_items = db.query(func.count(ZoteroItem.id)).filter(
            and_(
                ZoteroItem.library_id == library_id,
                ZoteroItem.is_deleted == False
            )
        ).scalar()
        
        # Get items with analysis
        analyzed_items = db.query(ZoteroItem).filter(
            and_(
                ZoteroItem.library_id == library_id,
                ZoteroItem.is_deleted == False,
                ZoteroItem.item_metadata.op('->>')('ai_analysis').isnot(None)
            )
        ).all()
        
        analyzed_count = len(analyzed_items)
        
        # Aggregate topic statistics
        topic_counts = {}
        domain_counts = {}
        
        for item in analyzed_items:
            analysis = item.item_metadata.get("ai_analysis", {}).get("results", {})
            
            # Count topics
            topics_data = analysis.get("topics", {})
            for topic in topics_data.get("primary_topics", []):
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            # Count domains
            domain = topics_data.get("research_domain")
            if domain and domain != "Unknown":
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        return {
            "library_id": library_id,
            "library_name": library.library_name,
            "total_items": total_items,
            "analyzed_items": analyzed_count,
            "analysis_coverage": round(analyzed_count / total_items * 100, 2) if total_items > 0 else 0,
            "top_topics": sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "research_domains": sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "statistics_timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analysis statistics: {str(e)}")