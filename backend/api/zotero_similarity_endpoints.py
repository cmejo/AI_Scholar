"""
FastAPI endpoints for Zotero similarity and recommendation features
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from core.auth import get_current_user
from services.zotero.zotero_similarity_service import ZoteroSimilarityService
from models.schemas import User

router = APIRouter(prefix="/zotero/similarity", tags=["zotero-similarity"])


# Request/Response Schemas
class EmbeddingRequest(BaseModel):
    """Schema for embedding generation request"""
    force_regenerate: bool = Field(default=False, description="Force regeneration of existing embeddings")


class SimilarityRequest(BaseModel):
    """Schema for similarity search request"""
    similarity_types: List[str] = Field(
        default=["semantic", "tfidf", "metadata"],
        description="Types of similarity to compute"
    )
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum number of similar items")
    min_similarity: float = Field(default=0.3, ge=0.0, le=1.0, description="Minimum similarity threshold")


class RecommendationRequest(BaseModel):
    """Schema for recommendation request"""
    library_id: Optional[str] = Field(None, description="Specific library for recommendations")
    recommendation_types: List[str] = Field(
        default=["similar", "trending", "gap_filling"],
        description="Types of recommendations"
    )
    max_recommendations: int = Field(default=10, ge=1, le=50, description="Maximum recommendations")


class ClusteringRequest(BaseModel):
    """Schema for clustering request"""
    library_id: Optional[str] = Field(None, description="Specific library to cluster")
    num_clusters: Optional[int] = Field(None, ge=2, le=20, description="Number of clusters")
    clustering_method: str = Field(default="kmeans", description="Clustering algorithm")


class EmbeddingResponse(BaseModel):
    """Schema for embedding response"""
    item_id: str = Field(..., description="Item ID")
    generation_timestamp: str = Field(..., description="Generation timestamp")
    content_hash: str = Field(..., description="Content hash for cache validation")
    embeddings: Dict[str, Any] = Field(..., description="Generated embeddings by type")


class SimilarItemResponse(BaseModel):
    """Schema for similar item response"""
    item_id: str = Field(..., description="Similar item ID")
    item_title: str = Field(..., description="Item title")
    item_type: str = Field(..., description="Item type")
    publication_year: Optional[int] = Field(None, description="Publication year")
    creators: List[Dict[str, Any]] = Field(default=[], description="Item creators")
    overall_similarity: float = Field(..., description="Overall similarity score")
    similarity_scores: Dict[str, float] = Field(..., description="Similarity scores by type")
    similarity_reasons: List[str] = Field(..., description="Human-readable similarity reasons")


class SimilarityResponse(BaseModel):
    """Schema for similarity search response"""
    target_item_id: str = Field(..., description="Target item ID")
    similarity_types: List[str] = Field(..., description="Similarity types used")
    min_similarity: float = Field(..., description="Minimum similarity threshold")
    total_candidates: int = Field(..., description="Total candidate items")
    similar_items_found: int = Field(..., description="Number of similar items found")
    similar_items: List[SimilarItemResponse] = Field(..., description="Similar items")
    analysis_timestamp: str = Field(..., description="Analysis timestamp")


class RecommendationResponse(BaseModel):
    """Schema for recommendation response"""
    user_id: str = Field(..., description="User ID")
    library_id: Optional[str] = Field(None, description="Library ID")
    recommendation_types: List[str] = Field(..., description="Recommendation types")
    recommendations: Dict[str, List[Dict[str, Any]]] = Field(..., description="Recommendations by type")
    generation_timestamp: str = Field(..., description="Generation timestamp")


class ClusterResponse(BaseModel):
    """Schema for clustering response"""
    user_id: str = Field(..., description="User ID")
    library_id: Optional[str] = Field(None, description="Library ID")
    clustering_method: str = Field(..., description="Clustering method used")
    num_clusters: int = Field(..., description="Number of clusters")
    total_items: int = Field(..., description="Total items clustered")
    clusters: List[Dict[str, Any]] = Field(..., description="Cluster results")
    clustering_timestamp: str = Field(..., description="Clustering timestamp")


# Initialize service
similarity_service = ZoteroSimilarityService()


@router.post("/embeddings/{item_id}", response_model=EmbeddingResponse)
async def generate_embeddings(
    item_id: str,
    request: EmbeddingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate vector embeddings for a reference
    
    Creates multiple types of embeddings for similarity analysis:
    - Semantic embeddings using LLM
    - TF-IDF embeddings for keyword similarity
    - Metadata embeddings for bibliographic similarity
    
    Args:
        item_id: Zotero item ID
        request: Embedding generation configuration
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Generated embeddings with metadata
        
    Raises:
        HTTPException: If item not found, access denied, or generation fails
    """
    try:
        result = await similarity_service.generate_embeddings(
            item_id=item_id,
            user_id=current_user.id,
            force_regenerate=request.force_regenerate
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return EmbeddingResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@router.post("/similar/{item_id}", response_model=SimilarityResponse)
async def find_similar_references(
    item_id: str,
    request: SimilarityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Find similar references to a given item
    
    Computes similarity using multiple methods:
    - Semantic similarity based on content embeddings
    - TF-IDF similarity based on keyword overlap
    - Metadata similarity based on bibliographic features
    
    Args:
        item_id: Reference item ID to find similarities for
        request: Similarity search configuration
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of similar references with similarity scores
        
    Raises:
        HTTPException: If item not found, access denied, or search fails
    """
    try:
        # Validate similarity types
        valid_types = {"semantic", "tfidf", "metadata"}
        invalid_types = set(request.similarity_types) - valid_types
        if invalid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid similarity types: {list(invalid_types)}. Valid types: {list(valid_types)}"
            )
        
        result = await similarity_service.find_similar_references(
            item_id=item_id,
            user_id=current_user.id,
            similarity_types=request.similarity_types,
            max_results=request.max_results,
            min_similarity=request.min_similarity
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return SimilarityResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity search failed: {str(e)}")


@router.post("/recommendations", response_model=RecommendationResponse)
async def generate_recommendations(
    request: RecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate personalized recommendations
    
    Creates recommendations based on:
    - Similar items to user's existing references
    - Trending topics in the research domain
    - Gap-filling suggestions for comprehensive coverage
    
    Args:
        request: Recommendation configuration
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Personalized recommendations by type
        
    Raises:
        HTTPException: If recommendation generation fails
    """
    try:
        # Validate recommendation types
        valid_types = {"similar", "trending", "gap_filling"}
        invalid_types = set(request.recommendation_types) - valid_types
        if invalid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid recommendation types: {list(invalid_types)}. Valid types: {list(valid_types)}"
            )
        
        result = await similarity_service.generate_recommendations(
            user_id=current_user.id,
            library_id=request.library_id,
            recommendation_types=request.recommendation_types,
            max_recommendations=request.max_recommendations
        )
        
        return RecommendationResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation generation failed: {str(e)}")


@router.post("/cluster", response_model=ClusterResponse)
async def cluster_references(
    request: ClusteringRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cluster references based on similarity
    
    Groups references into clusters using machine learning algorithms
    based on content similarity and metadata features.
    
    Args:
        request: Clustering configuration
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Clustering results with cluster summaries
        
    Raises:
        HTTPException: If clustering fails or insufficient data
    """
    try:
        # Validate clustering method
        valid_methods = {"kmeans"}
        if request.clustering_method not in valid_methods:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid clustering method: {request.clustering_method}. Valid methods: {list(valid_methods)}"
            )
        
        result = await similarity_service.cluster_references(
            user_id=current_user.id,
            library_id=request.library_id,
            num_clusters=request.num_clusters,
            clustering_method=request.clustering_method
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return ClusterResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clustering failed: {str(e)}")


@router.get("/embeddings/{item_id}")
async def get_embeddings(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get stored embeddings for a reference
    
    Retrieves previously generated embeddings for a Zotero reference.
    Returns None if no embeddings have been generated.
    
    Args:
        item_id: Zotero item ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Stored embeddings or None if not found
        
    Raises:
        HTTPException: If item not found or access denied
    """
    try:
        result = await similarity_service._get_stored_embeddings(db, item_id)
        
        if result is None:
            return None
            
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve embeddings: {str(e)}")


@router.delete("/embeddings/{item_id}")
async def delete_embeddings(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete stored embeddings for a reference
    
    Removes embeddings from the item's metadata.
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
        
        # Remove embeddings from metadata
        if item.item_metadata and "embeddings" in item.item_metadata:
            metadata = dict(item.item_metadata)
            del metadata["embeddings"]
            item.item_metadata = metadata
            db.commit()
            
            return {"message": "Embeddings deleted successfully"}
        else:
            return {"message": "No embeddings found to delete"}
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete embeddings: {str(e)}")


@router.get("/supported-methods")
async def get_supported_methods():
    """
    Get supported similarity and clustering methods
    
    Returns information about available similarity types,
    clustering algorithms, and recommendation types.
    
    Returns:
        Dictionary of supported methods with descriptions
    """
    return {
        "similarity_types": {
            "semantic": {
                "name": "Semantic Similarity",
                "description": "Content-based similarity using embeddings",
                "best_for": "Finding papers with similar themes and concepts"
            },
            "tfidf": {
                "name": "Keyword Similarity",
                "description": "TF-IDF based keyword overlap similarity",
                "best_for": "Finding papers with similar terminology"
            },
            "metadata": {
                "name": "Bibliographic Similarity",
                "description": "Similarity based on publication metadata",
                "best_for": "Finding papers from same authors, venues, or time periods"
            }
        },
        "clustering_methods": {
            "kmeans": {
                "name": "K-Means Clustering",
                "description": "Partitional clustering algorithm",
                "best_for": "Creating distinct topic-based clusters"
            }
        },
        "recommendation_types": {
            "similar": {
                "name": "Similar Papers",
                "description": "Recommendations based on similarity to user's papers",
                "best_for": "Finding related work in your research area"
            },
            "trending": {
                "name": "Trending Topics",
                "description": "Recommendations based on trending research topics",
                "best_for": "Discovering emerging research directions"
            },
            "gap_filling": {
                "name": "Gap Filling",
                "description": "Recommendations to fill gaps in research coverage",
                "best_for": "Comprehensive literature coverage"
            }
        },
        "default_settings": {
            "similarity_threshold": 0.3,
            "max_results": 10,
            "clustering_auto_clusters": True
        }
    }


@router.get("/stats/{library_id}")
async def get_similarity_statistics(
    library_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get similarity and clustering statistics for a library
    
    Returns statistics about embeddings coverage, similarity patterns,
    and clustering results for a Zotero library.
    
    Args:
        library_id: Zotero library ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Similarity and clustering statistics
        
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
        
        # Get items with embeddings
        items_with_embeddings = db.query(ZoteroItem).filter(
            and_(
                ZoteroItem.library_id == library_id,
                ZoteroItem.is_deleted == False,
                ZoteroItem.item_metadata.op('->>')('embeddings').isnot(None)
            )
        ).all()
        
        embeddings_count = len(items_with_embeddings)
        
        return {
            "library_id": library_id,
            "library_name": library.library_name,
            "total_items": total_items,
            "items_with_embeddings": embeddings_count,
            "embeddings_coverage": round(embeddings_count / total_items * 100, 2) if total_items > 0 else 0,
            "embedding_types": ["semantic", "tfidf", "metadata"],
            "similarity_methods": ["semantic", "tfidf", "metadata"],
            "clustering_ready": embeddings_count >= 3,
            "recommended_clusters": min(max(2, embeddings_count // 5), 10) if embeddings_count >= 3 else 0,
            "statistics_timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get similarity statistics: {str(e)}")