"""
FastAPI endpoints for Zotero research insights and gap analysis features
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from core.auth import get_current_user
from services.zotero.zotero_research_insights_service import ZoteroResearchInsightsService
from models.schemas import User

router = APIRouter(prefix="/zotero/research-insights", tags=["zotero-research-insights"])


# Request/Response Schemas
class ResearchLandscapeRequest(BaseModel):
    """Schema for research landscape analysis request"""
    library_id: Optional[str] = Field(None, description="Specific library to analyze")
    analysis_types: List[str] = Field(
        default=["topics", "trends", "gaps", "networks"],
        description="Types of analysis to perform"
    )


class ThemeIdentificationRequest(BaseModel):
    """Schema for theme identification request"""
    library_id: Optional[str] = Field(None, description="Specific library to analyze")
    clustering_method: str = Field(default="kmeans", description="Clustering algorithm")
    num_themes: Optional[int] = Field(None, ge=2, le=20, description="Number of themes to identify")


class GapAnalysisRequest(BaseModel):
    """Schema for gap analysis request"""
    library_id: Optional[str] = Field(None, description="Specific library to analyze")
    gap_types: List[str] = Field(
        default=["temporal", "topical", "methodological"],
        description="Types of gaps to detect"
    )


class TrendAnalysisRequest(BaseModel):
    """Schema for trend analysis request"""
    library_id: Optional[str] = Field(None, description="Specific library to analyze")
    trend_types: List[str] = Field(
        default=["temporal", "topical", "citation", "collaboration"],
        description="Types of trends to analyze"
    )
    time_window_years: int = Field(default=5, ge=1, le=20, description="Years to analyze for trends")


class ResearchLandscapeResponse(BaseModel):
    """Schema for research landscape response"""
    user_id: str = Field(..., description="User ID")
    library_id: Optional[str] = Field(None, description="Library ID")
    analysis_types: List[str] = Field(..., description="Analysis types performed")
    total_items: int = Field(..., description="Total items analyzed")
    analysis_timestamp: str = Field(..., description="Analysis timestamp")
    results: Dict[str, Any] = Field(..., description="Analysis results by type")


class ThemeResponse(BaseModel):
    """Schema for research theme response"""
    user_id: str = Field(..., description="User ID")
    library_id: Optional[str] = Field(None, description="Library ID")
    clustering_method: str = Field(..., description="Clustering method used")
    num_themes: int = Field(..., description="Number of themes identified")
    total_items_analyzed: int = Field(..., description="Total items analyzed")
    themes: List[Dict[str, Any]] = Field(..., description="Identified themes")
    analysis_timestamp: str = Field(..., description="Analysis timestamp")


class GapAnalysisResponse(BaseModel):
    """Schema for gap analysis response"""
    user_id: str = Field(..., description="User ID")
    library_id: Optional[str] = Field(None, description="Library ID")
    gap_types: List[str] = Field(..., description="Gap types analyzed")
    total_items: int = Field(..., description="Total items analyzed")
    gaps_detected: Dict[str, Any] = Field(..., description="Detected gaps by type")
    recommendations: List[Dict[str, Any]] = Field(..., description="Gap-filling recommendations")
    analysis_timestamp: str = Field(..., description="Analysis timestamp")


class TrendAnalysisResponse(BaseModel):
    """Schema for trend analysis response"""
    user_id: str = Field(..., description="User ID")
    library_id: Optional[str] = Field(None, description="Library ID")
    trend_types: List[str] = Field(..., description="Trend types analyzed")
    time_window_years: int = Field(..., description="Time window for analysis")
    time_range: str = Field(..., description="Time range analyzed")
    total_items: int = Field(..., description="Total items")
    recent_items: int = Field(..., description="Recent items in time window")
    trends: Dict[str, Any] = Field(..., description="Identified trends by type")
    predictions: Dict[str, Any] = Field(..., description="Trend predictions")
    analysis_timestamp: str = Field(..., description="Analysis timestamp")


# Initialize service
insights_service = ZoteroResearchInsightsService()


@router.post("/landscape", response_model=ResearchLandscapeResponse)
async def analyze_research_landscape(
    request: ResearchLandscapeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze the overall research landscape
    
    Provides comprehensive analysis of a user's research library including:
    - Topic distribution and evolution
    - Research trends over time
    - Identified gaps in coverage
    - Research networks and connections
    
    Args:
        request: Research landscape analysis configuration
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Comprehensive research landscape analysis
        
    Raises:
        HTTPException: If analysis fails or insufficient data
    """
    try:
        # Validate analysis types
        valid_types = {"topics", "trends", "gaps", "networks"}
        invalid_types = set(request.analysis_types) - valid_types
        if invalid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid analysis types: {list(invalid_types)}. Valid types: {list(valid_types)}"
            )
        
        result = await insights_service.analyze_research_landscape(
            user_id=current_user.id,
            library_id=request.library_id,
            analysis_types=request.analysis_types
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return ResearchLandscapeResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research landscape analysis failed: {str(e)}")


@router.post("/themes", response_model=ThemeResponse)
async def identify_research_themes(
    request: ThemeIdentificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Identify major research themes using topic clustering
    
    Uses machine learning algorithms to cluster references into coherent
    research themes based on content similarity and metadata.
    
    Args:
        request: Theme identification configuration
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Identified research themes with supporting papers
        
    Raises:
        HTTPException: If clustering fails or insufficient data
    """
    try:
        # Validate clustering method
        valid_methods = {"kmeans", "dbscan"}
        if request.clustering_method not in valid_methods:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid clustering method: {request.clustering_method}. Valid methods: {list(valid_methods)}"
            )
        
        result = await insights_service.identify_research_themes(
            user_id=current_user.id,
            library_id=request.library_id,
            clustering_method=request.clustering_method,
            num_themes=request.num_themes
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return ThemeResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Theme identification failed: {str(e)}")


@router.post("/gaps", response_model=GapAnalysisResponse)
async def detect_research_gaps(
    request: GapAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Detect gaps in research coverage
    
    Identifies potential gaps in research coverage including:
    - Temporal gaps (missing time periods)
    - Topical gaps (underrepresented topics)
    - Methodological gaps (missing research methods)
    
    Args:
        request: Gap analysis configuration
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Identified research gaps with filling recommendations
        
    Raises:
        HTTPException: If gap analysis fails
    """
    try:
        # Validate gap types
        valid_types = {"temporal", "topical", "methodological"}
        invalid_types = set(request.gap_types) - valid_types
        if invalid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid gap types: {list(invalid_types)}. Valid types: {list(valid_types)}"
            )
        
        result = await insights_service.detect_research_gaps(
            user_id=current_user.id,
            library_id=request.library_id,
            gap_types=request.gap_types
        )
        
        # Handle warnings (insufficient data) as successful responses
        if "warning" in result:
            return result
        
        return GapAnalysisResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gap analysis failed: {str(e)}")


@router.post("/trends", response_model=TrendAnalysisResponse)
async def analyze_research_trends(
    request: TrendAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze research trends and emerging directions
    
    Identifies trends in research over time including:
    - Temporal trends (publication patterns)
    - Topical trends (evolving research topics)
    - Citation trends (citation patterns)
    - Collaboration trends (author collaboration patterns)
    
    Args:
        request: Trend analysis configuration
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Research trend analysis with predictions
        
    Raises:
        HTTPException: If trend analysis fails
    """
    try:
        # Validate trend types
        valid_types = {"temporal", "topical", "citation", "collaboration"}
        invalid_types = set(request.trend_types) - valid_types
        if invalid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid trend types: {list(invalid_types)}. Valid types: {list(valid_types)}"
            )
        
        result = await insights_service.analyze_research_trends(
            user_id=current_user.id,
            library_id=request.library_id,
            trend_types=request.trend_types,
            time_window_years=request.time_window_years
        )
        
        # Handle warnings (insufficient data) as successful responses
        if "warning" in result:
            return result
        
        return TrendAnalysisResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@router.get("/supported-methods")
async def get_supported_methods():
    """
    Get supported analysis methods
    
    Returns information about available analysis types,
    clustering algorithms, and gap detection methods.
    
    Returns:
        Dictionary of supported methods with descriptions
    """
    return {
        "landscape_analysis_types": {
            "topics": {
                "name": "Topic Analysis",
                "description": "Analyze topic distribution and evolution",
                "best_for": "Understanding research focus areas"
            },
            "trends": {
                "name": "Trend Analysis",
                "description": "Identify research trends over time",
                "best_for": "Tracking research evolution"
            },
            "gaps": {
                "name": "Gap Analysis",
                "description": "Detect gaps in research coverage",
                "best_for": "Finding research opportunities"
            },
            "networks": {
                "name": "Network Analysis",
                "description": "Analyze research networks and connections",
                "best_for": "Understanding collaboration patterns"
            }
        },
        "clustering_methods": {
            "kmeans": {
                "name": "K-Means Clustering",
                "description": "Partitional clustering for distinct themes",
                "best_for": "Well-separated research themes"
            },
            "dbscan": {
                "name": "DBSCAN Clustering",
                "description": "Density-based clustering for variable themes",
                "best_for": "Discovering natural theme boundaries"
            }
        },
        "gap_types": {
            "temporal": {
                "name": "Temporal Gaps",
                "description": "Missing time periods in research coverage",
                "best_for": "Identifying historical research gaps"
            },
            "topical": {
                "name": "Topical Gaps",
                "description": "Underrepresented research topics",
                "best_for": "Finding unexplored research areas"
            },
            "methodological": {
                "name": "Methodological Gaps",
                "description": "Missing research methodologies",
                "best_for": "Diversifying research approaches"
            }
        },
        "trend_types": {
            "temporal": {
                "name": "Temporal Trends",
                "description": "Publication patterns over time",
                "best_for": "Understanding research activity patterns"
            },
            "topical": {
                "name": "Topical Trends",
                "description": "Evolving research topics and themes",
                "best_for": "Tracking topic evolution"
            },
            "citation": {
                "name": "Citation Trends",
                "description": "Citation and venue patterns",
                "best_for": "Understanding publication impact"
            },
            "collaboration": {
                "name": "Collaboration Trends",
                "description": "Author collaboration patterns",
                "best_for": "Analyzing research networks"
            }
        },
        "default_settings": {
            "min_items_for_analysis": 5,
            "min_items_for_clustering": 3,
            "default_time_window": 5,
            "max_themes": 15
        }
    }


@router.get("/stats/{library_id}")
async def get_insights_statistics(
    library_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get research insights statistics for a library
    
    Returns statistics about analysis readiness and coverage
    for a Zotero library.
    
    Args:
        library_id: Zotero library ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Research insights statistics
        
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
        
        # Get items with AI analysis
        items_with_analysis = db.query(ZoteroItem).filter(
            and_(
                ZoteroItem.library_id == library_id,
                ZoteroItem.is_deleted == False,
                ZoteroItem.item_metadata.op('->>')('ai_analysis').isnot(None)
            )
        ).all()
        
        analysis_count = len(items_with_analysis)
        
        # Get items with publication years
        items_with_years = db.query(func.count(ZoteroItem.id)).filter(
            and_(
                ZoteroItem.library_id == library_id,
                ZoteroItem.is_deleted == False,
                ZoteroItem.publication_year.isnot(None)
            )
        ).scalar()
        
        # Calculate year range
        year_stats = db.query(
            func.min(ZoteroItem.publication_year),
            func.max(ZoteroItem.publication_year)
        ).filter(
            and_(
                ZoteroItem.library_id == library_id,
                ZoteroItem.is_deleted == False,
                ZoteroItem.publication_year.isnot(None)
            )
        ).first()
        
        min_year, max_year = year_stats if year_stats[0] else (None, None)
        
        return {
            "library_id": library_id,
            "library_name": library.library_name,
            "total_items": total_items,
            "items_with_analysis": analysis_count,
            "analysis_coverage": round(analysis_count / total_items * 100, 2) if total_items > 0 else 0,
            "items_with_years": items_with_years,
            "temporal_coverage": round(items_with_years / total_items * 100, 2) if total_items > 0 else 0,
            "year_range": {
                "min_year": min_year,
                "max_year": max_year,
                "span_years": max_year - min_year if min_year and max_year else 0
            },
            "analysis_readiness": {
                "landscape_analysis": total_items >= 5,
                "theme_clustering": analysis_count >= 3,
                "gap_analysis": total_items >= 10,
                "trend_analysis": items_with_years >= 5 and (max_year - min_year >= 2 if min_year and max_year else False)
            },
            "recommendations": {
                "add_more_items": total_items < 10,
                "run_ai_analysis": analysis_count < total_items * 0.5,
                "add_publication_years": items_with_years < total_items * 0.8
            },
            "statistics_timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights statistics: {str(e)}")


@router.get("/export/{analysis_type}")
async def export_analysis_results(
    analysis_type: str,
    library_id: Optional[str] = Query(None, description="Library ID for analysis"),
    format: str = Query("json", description="Export format (json, csv)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export analysis results
    
    Exports the results of research insights analysis in various formats.
    
    Args:
        analysis_type: Type of analysis to export (landscape, themes, gaps, trends)
        library_id: Optional library ID
        format: Export format (json, csv)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Exported analysis results
        
    Raises:
        HTTPException: If analysis type invalid or export fails
    """
    try:
        valid_types = {"landscape", "themes", "gaps", "trends"}
        if analysis_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid analysis type: {analysis_type}. Valid types: {list(valid_types)}"
            )
        
        valid_formats = {"json", "csv"}
        if format not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format: {format}. Valid formats: {list(valid_formats)}"
            )
        
        # For now, return a placeholder response
        # In a full implementation, this would retrieve and format the actual analysis results
        return {
            "export_type": analysis_type,
            "format": format,
            "library_id": library_id,
            "user_id": current_user.id,
            "export_timestamp": datetime.utcnow().isoformat(),
            "message": f"Export functionality for {analysis_type} analysis in {format} format",
            "note": "This is a placeholder - full implementation would return actual analysis data"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")