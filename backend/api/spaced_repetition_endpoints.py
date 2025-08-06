"""
Spaced Repetition API Endpoints for Educational Enhancement System
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from services.spaced_repetition_service import (
    SpacedRepetitionService,
    SpacedRepetitionItem,
    ReviewSession,
    PerformanceMetrics,
    ReviewQuality,
    ContentType
)
from services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/spaced-repetition", tags=["spaced-repetition"])
auth_service = AuthService()
sr_service = SpacedRepetitionService()

# Pydantic Models for API

class AddItemRequest(BaseModel):
    content_id: str
    content_type: ContentType
    initial_difficulty: float = 2.5
    metadata: Optional[Dict[str, Any]] = None

class RecordReviewRequest(BaseModel):
    item_id: str
    quality: ReviewQuality
    response_time_seconds: Optional[int] = None

class SpacedRepetitionItemResponse(BaseModel):
    id: str
    user_id: str
    content_id: str
    content_type: str
    difficulty: float
    interval: int
    repetitions: int
    ease_factor: float
    next_review_date: datetime
    last_reviewed: Optional[datetime]
    metadata: Dict[str, Any]

class ReviewSessionResponse(BaseModel):
    id: str
    user_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    items_reviewed: List[str]
    performance_scores: List[float]
    session_metadata: Dict[str, Any]

class PerformanceMetricsResponse(BaseModel):
    total_reviews: int
    correct_reviews: int
    accuracy_rate: float
    average_ease_factor: float
    retention_rate: float
    streak_count: int
    last_review_date: Optional[datetime]

class ReviewScheduleResponse(BaseModel):
    schedule: Dict[str, List[SpacedRepetitionItemResponse]]
    total_items: int

class EndSessionRequest(BaseModel):
    session_id: str
    items_reviewed: List[str]
    performance_scores: List[float]

# Helper functions
def sr_item_to_response(item: SpacedRepetitionItem) -> SpacedRepetitionItemResponse:
    """Convert SpacedRepetitionItem to API response format"""
    return SpacedRepetitionItemResponse(
        id=item.id,
        user_id=item.user_id,
        content_id=item.content_id,
        content_type=item.content_type.value,
        difficulty=item.difficulty,
        interval=item.interval,
        repetitions=item.repetitions,
        ease_factor=item.ease_factor,
        next_review_date=item.next_review_date,
        last_reviewed=item.last_reviewed,
        metadata=item.metadata
    )

def review_session_to_response(session: ReviewSession) -> ReviewSessionResponse:
    """Convert ReviewSession to API response format"""
    return ReviewSessionResponse(
        id=session.id,
        user_id=session.user_id,
        started_at=session.started_at,
        ended_at=session.ended_at,
        items_reviewed=session.items_reviewed,
        performance_scores=session.performance_scores,
        session_metadata=session.session_metadata
    )

# Dependency for authentication
async def get_current_user(token: str = Depends(auth_service.get_current_user)):
    """Get current authenticated user"""
    return token

@router.post("/items", response_model=SpacedRepetitionItemResponse)
async def add_item_to_review(
    request: AddItemRequest,
    user = Depends(get_current_user)
):
    """Add a new item to the spaced repetition system"""
    try:
        logger.info(f"Adding item {request.content_id} to spaced repetition for user {user.id}")
        
        item = await sr_service.add_item_to_review(
            user_id=user.id,
            content_id=request.content_id,
            content_type=request.content_type,
            initial_difficulty=request.initial_difficulty,
            metadata=request.metadata
        )
        
        return sr_item_to_response(item)
        
    except Exception as e:
        logger.error(f"Error adding item to spaced repetition: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add item to spaced repetition")

@router.get("/items/due", response_model=List[SpacedRepetitionItemResponse])
async def get_due_items(
    user = Depends(get_current_user),
    limit: int = Query(default=20, le=100),
    content_types: Optional[List[ContentType]] = Query(default=None)
):
    """Get items that are due for review"""
    try:
        items = await sr_service.get_due_items(
            user_id=user.id,
            limit=limit,
            content_types=content_types
        )
        
        return [sr_item_to_response(item) for item in items]
        
    except Exception as e:
        logger.error(f"Error getting due items: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get due items")

@router.post("/reviews", response_model=SpacedRepetitionItemResponse)
async def record_review(
    request: RecordReviewRequest,
    user = Depends(get_current_user)
):
    """Record a review and update the item's scheduling"""
    try:
        logger.info(f"Recording review for item {request.item_id} with quality {request.quality.value}")
        
        item = await sr_service.record_review(
            item_id=request.item_id,
            user_id=user.id,
            quality=request.quality,
            response_time_seconds=request.response_time_seconds
        )
        
        return sr_item_to_response(item)
        
    except ValueError as e:
        logger.error(f"Invalid review request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error recording review: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record review")

@router.post("/sessions/start", response_model=ReviewSessionResponse)
async def start_review_session(
    user = Depends(get_current_user)
):
    """Start a new review session"""
    try:
        session = await sr_service.start_review_session(user.id)
        return review_session_to_response(session)
        
    except Exception as e:
        logger.error(f"Error starting review session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start review session")

@router.post("/sessions/end", response_model=ReviewSessionResponse)
async def end_review_session(
    request: EndSessionRequest,
    user = Depends(get_current_user)
):
    """End a review session and record performance"""
    try:
        session = await sr_service.end_review_session(
            session_id=request.session_id,
            user_id=user.id,
            items_reviewed=request.items_reviewed,
            performance_scores=request.performance_scores
        )
        
        return review_session_to_response(session)
        
    except ValueError as e:
        logger.error(f"Invalid session end request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error ending review session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to end review session")

@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    user = Depends(get_current_user),
    days_back: int = Query(default=30, ge=1, le=365)
):
    """Get performance metrics for the user"""
    try:
        metrics = await sr_service.get_performance_metrics(user.id, days_back)
        
        return PerformanceMetricsResponse(
            total_reviews=metrics.total_reviews,
            correct_reviews=metrics.correct_reviews,
            accuracy_rate=metrics.accuracy_rate,
            average_ease_factor=metrics.average_ease_factor,
            retention_rate=metrics.retention_rate,
            streak_count=metrics.streak_count,
            last_review_date=metrics.last_review_date
        )
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")

@router.get("/schedule", response_model=ReviewScheduleResponse)
async def get_review_schedule(
    user = Depends(get_current_user),
    days_ahead: int = Query(default=7, ge=1, le=30)
):
    """Get review schedule for upcoming days"""
    try:
        schedule = await sr_service.get_review_schedule(user.id, days_ahead)
        
        # Convert to response format
        response_schedule = {}
        total_items = 0
        
        for date_key, items in schedule.items():
            response_schedule[date_key] = [sr_item_to_response(item) for item in items]
            total_items += len(items)
        
        return ReviewScheduleResponse(
            schedule=response_schedule,
            total_items=total_items
        )
        
    except Exception as e:
        logger.error(f"Error getting review schedule: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get review schedule")

@router.post("/optimize")
async def optimize_review_timing(
    user = Depends(get_current_user)
):
    """Optimize review timing based on user performance patterns"""
    try:
        result = await sr_service.optimize_review_timing(user.id)
        return result
        
    except Exception as e:
        logger.error(f"Error optimizing review timing: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to optimize review timing")

@router.get("/items/{item_id}", response_model=SpacedRepetitionItemResponse)
async def get_sr_item(
    item_id: str,
    user = Depends(get_current_user)
):
    """Get a specific spaced repetition item"""
    try:
        item = await sr_service.get_sr_item_by_id(item_id, user.id)
        if not item:
            raise HTTPException(status_code=404, detail="Spaced repetition item not found")
        
        return sr_item_to_response(item)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting SR item: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get spaced repetition item")

@router.get("/stats")
async def get_sr_stats(
    user = Depends(get_current_user)
):
    """Get comprehensive spaced repetition statistics"""
    try:
        stats = await sr_service.get_user_sr_stats(user.id)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting SR stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get spaced repetition statistics")

@router.delete("/items/{item_id}")
async def remove_sr_item(
    item_id: str,
    user = Depends(get_current_user)
):
    """Remove an item from spaced repetition"""
    try:
        # Verify item exists and belongs to user
        item = await sr_service.get_sr_item_by_id(item_id, user.id)
        if not item:
            raise HTTPException(status_code=404, detail="Spaced repetition item not found")
        
        # Delete from database
        from core.database import get_db, SpacedRepetitionItem as SRItemModel
        db = next(get_db())
        try:
            db.query(SRItemModel).filter(
                SRItemModel.id == item_id,
                SRItemModel.user_id == user.id
            ).delete()
            db.commit()
        finally:
            db.close()
        
        logger.info(f"Removed SR item {item_id} for user {user.id}")
        return {"success": True, "message": "Item removed from spaced repetition"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing SR item: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove spaced repetition item")

@router.get("/content-types")
async def get_content_types():
    """Get available content types for spaced repetition"""
    return {
        "content_types": [ct.value for ct in ContentType],
        "descriptions": {
            ContentType.QUIZ_QUESTION.value: "Questions from quizzes",
            ContentType.CONCEPT.value: "Key concepts and ideas",
            ContentType.FACT.value: "Important facts and information",
            ContentType.DEFINITION.value: "Definitions of terms",
            ContentType.FORMULA.value: "Mathematical or scientific formulas"
        }
    }

@router.get("/review-qualities")
async def get_review_qualities():
    """Get available review quality ratings"""
    return {
        "qualities": [
            {"value": rq.value, "name": rq.name, "description": _get_quality_description(rq)}
            for rq in ReviewQuality
        ]
    }

@router.get("/optimal-timing")
async def get_optimal_session_timing(
    user = Depends(get_current_user)
):
    """Get optimal session timing recommendations based on user patterns"""
    try:
        timing = await sr_service.get_optimal_session_timing(user.id)
        return timing
        
    except Exception as e:
        logger.error(f"Error getting optimal session timing: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get optimal session timing")

@router.get("/retention-analytics")
async def get_advanced_retention_analytics(
    user = Depends(get_current_user)
):
    """Get advanced retention analytics with forgetting curves and predictions"""
    try:
        analytics = await sr_service.get_advanced_retention_analytics(user.id)
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting retention analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get retention analytics")

def _get_quality_description(quality: ReviewQuality) -> str:
    """Get description for review quality"""
    descriptions = {
        ReviewQuality.BLACKOUT: "Complete blackout - couldn't remember at all",
        ReviewQuality.INCORRECT: "Incorrect response, but correct answer seemed familiar",
        ReviewQuality.DIFFICULT: "Correct response with serious difficulty",
        ReviewQuality.HESITANT: "Correct response with hesitation",
        ReviewQuality.EASY: "Correct response with some hesitation",
        ReviewQuality.PERFECT: "Perfect response - remembered easily"
    }
    return descriptions.get(quality, "Unknown quality level")