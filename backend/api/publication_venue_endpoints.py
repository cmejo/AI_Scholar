"""
Publication Venue API Endpoints

This module provides REST API endpoints for publication venue recommendation and tracking.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from services.publication_venue_matcher import PublicationVenueMatcherService

router = APIRouter(prefix="/api/publication", tags=["publication"])
venue_service = PublicationVenueMatcherService()

# Request/Response Models

class VenueRecommendationRequest(BaseModel):
    """Model for venue recommendation request"""
    paper_abstract: str = Field(..., description="Abstract of the paper")
    venue_type: Optional[str] = Field(None, description="Filter by venue type (journal, conference, workshop)")
    max_recommendations: int = Field(default=20, description="Maximum number of recommendations")
    min_fit_score: float = Field(default=0.3, description="Minimum fit score threshold")

class VenueRecommendationResponse(BaseModel):
    """Model for venue recommendation response"""
    venue_id: str
    name: str
    venue_type: str
    publisher: str
    relevance_score: float
    fit_score: float
    success_probability: float
    match_reasons: List[str]
    recommendation_strength: str
    impact_factor: Optional[float]
    acceptance_rate: Optional[float]
    next_deadline: Optional[datetime]
    average_review_time: Optional[int]

class VenueCreate(BaseModel):
    """Model for creating publication venue"""
    name: str = Field(..., description="Venue name")
    venue_type: str = Field(..., description="Type of venue (journal, conference, workshop)")
    publisher: Optional[str] = Field(None, description="Publisher name")
    issn: Optional[str] = Field(None, description="ISSN for journals")
    isbn: Optional[str] = Field(None, description="ISBN for conference proceedings")
    impact_factor: Optional[float] = Field(None, description="Impact factor")
    h_index: Optional[int] = Field(None, description="H-index")
    acceptance_rate: Optional[float] = Field(None, description="Acceptance rate percentage")
    research_areas: List[str] = Field(default_factory=list, description="Research areas")
    keywords: List[str] = Field(default_factory=list, description="Keywords for matching")
    submission_frequency: Optional[str] = Field(None, description="Submission frequency")
    review_process: Optional[str] = Field(None, description="Review process type")
    open_access: bool = Field(default=False, description="Open access publication")
    publication_fee: Optional[float] = Field(None, description="Publication fee")
    average_review_time_days: Optional[int] = Field(None, description="Average review time in days")
    geographic_scope: Optional[str] = Field(None, description="Geographic scope")
    language: str = Field(default="English", description="Publication language")
    website_url: Optional[str] = Field(None, description="Website URL")
    submission_guidelines_url: Optional[str] = Field(None, description="Submission guidelines URL")

class DeadlineCreate(BaseModel):
    """Model for creating publication deadline"""
    venue_id: str = Field(..., description="Venue ID")
    deadline_type: str = Field(..., description="Type of deadline (abstract, full_paper, camera_ready)")
    deadline_date: datetime = Field(..., description="Deadline date")
    notification_date: Optional[datetime] = Field(None, description="Notification date")
    publication_date: Optional[datetime] = Field(None, description="Publication date")
    volume_issue: Optional[str] = Field(None, description="Volume/issue information")
    special_issue_theme: Optional[str] = Field(None, description="Special issue theme")
    submission_url: Optional[str] = Field(None, description="Submission URL")
    additional_requirements: Dict[str, Any] = Field(default_factory=dict, description="Additional requirements")

class SubmissionCreate(BaseModel):
    """Model for creating submission tracker"""
    venue_id: str = Field(..., description="Venue ID")
    paper_title: str = Field(..., description="Paper title")
    paper_abstract: str = Field(..., description="Paper abstract")
    deadline_id: Optional[str] = Field(None, description="Associated deadline ID")
    submission_date: Optional[datetime] = Field(None, description="Submission date")

class SubmissionUpdate(BaseModel):
    """Model for updating submission status"""
    status: str = Field(..., description="Submission status")
    decision_date: Optional[datetime] = Field(None, description="Decision date")
    final_decision: Optional[str] = Field(None, description="Final decision")
    review_comments: Optional[str] = Field(None, description="Review comments")

# API Endpoints

@router.post("/venues/recommend", response_model=List[VenueRecommendationResponse])
async def recommend_venues(
    request: VenueRecommendationRequest,
    user_id: str = Query(..., description="User ID")
):
    """Get venue recommendations based on paper abstract"""
    try:
        recommendations = await venue_service.recommend_venues(
            user_id=user_id,
            paper_abstract=request.paper_abstract,
            venue_type=request.venue_type,
            max_recommendations=request.max_recommendations,
            min_fit_score=request.min_fit_score
        )
        
        return [
            VenueRecommendationResponse(
                venue_id=rec.venue_id,
                name=rec.name,
                venue_type=rec.venue_type,
                publisher=rec.publisher,
                relevance_score=rec.relevance_score,
                fit_score=rec.fit_score,
                success_probability=rec.success_probability,
                match_reasons=rec.match_reasons,
                recommendation_strength=rec.recommendation_strength,
                impact_factor=rec.impact_factor,
                acceptance_rate=rec.acceptance_rate,
                next_deadline=rec.next_deadline,
                average_review_time=rec.average_review_time
            )
            for rec in recommendations
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting venue recommendations: {str(e)}")

@router.get("/venues/rankings", response_model=List[Dict[str, Any]])
async def get_venue_rankings(
    research_area: Optional[str] = Query(None, description="Filter by research area"),
    venue_type: Optional[str] = Query(None, description="Filter by venue type"),
    sort_by: str = Query(default="impact_factor", description="Sort criteria"),
    limit: int = Query(default=50, description="Maximum results to return")
):
    """Get ranked list of publication venues"""
    try:
        rankings = await venue_service.get_venue_rankings(
            research_area=research_area,
            venue_type=venue_type,
            sort_by=sort_by,
            limit=limit
        )
        
        return rankings
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting venue rankings: {str(e)}")

@router.post("/venues", response_model=Dict[str, str])
async def create_venue(venue: VenueCreate):
    """Create a new publication venue (admin function)"""
    try:
        from core.database import get_db, PublicationVenue
        
        db = next(get_db())
        
        new_venue = PublicationVenue(
            name=venue.name,
            venue_type=venue.venue_type,
            publisher=venue.publisher,
            issn=venue.issn,
            isbn=venue.isbn,
            impact_factor=venue.impact_factor,
            h_index=venue.h_index,
            acceptance_rate=venue.acceptance_rate,
            research_areas=venue.research_areas,
            keywords=venue.keywords,
            submission_frequency=venue.submission_frequency,
            review_process=venue.review_process,
            open_access=venue.open_access,
            publication_fee=venue.publication_fee,
            average_review_time_days=venue.average_review_time_days,
            geographic_scope=venue.geographic_scope,
            language=venue.language,
            website_url=venue.website_url,
            submission_guidelines_url=venue.submission_guidelines_url,
            is_active=True
        )
        
        db.add(new_venue)
        db.commit()
        db.refresh(new_venue)
        db.close()
        
        return {"venue_id": new_venue.id, "message": "Publication venue created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating venue: {str(e)}")

@router.get("/venues", response_model=List[Dict[str, Any]])
async def get_venues(
    venue_type: Optional[str] = Query(None, description="Filter by venue type"),
    research_area: Optional[str] = Query(None, description="Filter by research area"),
    limit: int = Query(default=50, description="Maximum results to return")
):
    """Get publication venues"""
    try:
        from core.database import get_db, PublicationVenue
        
        db = next(get_db())
        
        query = db.query(PublicationVenue).filter(
            PublicationVenue.is_active == True
        )
        
        if venue_type:
            query = query.filter(PublicationVenue.venue_type == venue_type)
        
        venues = query.limit(limit).all()
        
        # Filter by research area if specified
        if research_area:
            filtered_venues = []
            for venue in venues:
                if venue.research_areas and any(
                    research_area.lower() in area.lower() 
                    for area in venue.research_areas
                ):
                    filtered_venues.append(venue)
            venues = filtered_venues
        
        db.close()
        
        return [
            {
                'id': venue.id,
                'name': venue.name,
                'venue_type': venue.venue_type,
                'publisher': venue.publisher,
                'impact_factor': venue.impact_factor,
                'h_index': venue.h_index,
                'acceptance_rate': venue.acceptance_rate,
                'research_areas': venue.research_areas,
                'keywords': venue.keywords,
                'open_access': venue.open_access,
                'publication_fee': venue.publication_fee,
                'average_review_time_days': venue.average_review_time_days,
                'geographic_scope': venue.geographic_scope,
                'website_url': venue.website_url
            }
            for venue in venues
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting venues: {str(e)}")

@router.post("/deadlines", response_model=Dict[str, str])
async def create_deadline(deadline: DeadlineCreate):
    """Create a publication deadline"""
    try:
        from core.database import get_db, PublicationDeadline
        
        db = next(get_db())
        
        new_deadline = PublicationDeadline(
            venue_id=deadline.venue_id,
            deadline_type=deadline.deadline_type,
            deadline_date=deadline.deadline_date,
            notification_date=deadline.notification_date,
            publication_date=deadline.publication_date,
            volume_issue=deadline.volume_issue,
            special_issue_theme=deadline.special_issue_theme,
            submission_url=deadline.submission_url,
            additional_requirements=deadline.additional_requirements,
            is_active=True
        )
        
        db.add(new_deadline)
        db.commit()
        db.refresh(new_deadline)
        db.close()
        
        return {"deadline_id": new_deadline.id, "message": "Publication deadline created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating deadline: {str(e)}")

@router.get("/deadlines", response_model=List[Dict[str, Any]])
async def get_deadlines(
    venue_id: Optional[str] = Query(None, description="Filter by venue ID"),
    upcoming_only: bool = Query(default=True, description="Return only upcoming deadlines")
):
    """Get publication deadlines"""
    try:
        from core.database import get_db, PublicationDeadline, PublicationVenue
        from sqlalchemy import and_
        
        db = next(get_db())
        
        query = db.query(PublicationDeadline, PublicationVenue).join(
            PublicationVenue, PublicationDeadline.venue_id == PublicationVenue.id
        ).filter(PublicationDeadline.is_active == True)
        
        if venue_id:
            query = query.filter(PublicationDeadline.venue_id == venue_id)
        
        if upcoming_only:
            query = query.filter(PublicationDeadline.deadline_date > datetime.now())
        
        deadlines = query.order_by(PublicationDeadline.deadline_date).all()
        
        db.close()
        
        return [
            {
                'id': deadline.id,
                'venue_name': venue.name,
                'venue_type': venue.venue_type,
                'deadline_type': deadline.deadline_type,
                'deadline_date': deadline.deadline_date,
                'notification_date': deadline.notification_date,
                'publication_date': deadline.publication_date,
                'volume_issue': deadline.volume_issue,
                'special_issue_theme': deadline.special_issue_theme,
                'submission_url': deadline.submission_url,
                'additional_requirements': deadline.additional_requirements
            }
            for deadline, venue in deadlines
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting deadlines: {str(e)}")

@router.post("/submissions", response_model=Dict[str, str])
async def create_submission(
    submission: SubmissionCreate,
    user_id: str = Query(..., description="User ID")
):
    """Track a paper submission"""
    try:
        submission_id = await venue_service.track_submission(
            user_id=user_id,
            venue_id=submission.venue_id,
            paper_title=submission.paper_title,
            paper_abstract=submission.paper_abstract,
            deadline_id=submission.deadline_id,
            submission_date=submission.submission_date
        )
        
        return {"submission_id": submission_id, "message": "Submission tracked successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking submission: {str(e)}")

@router.put("/submissions/{submission_id}", response_model=Dict[str, str])
async def update_submission(submission_id: str, update: SubmissionUpdate):
    """Update submission status"""
    try:
        await venue_service.update_submission_status(
            submission_id=submission_id,
            status=update.status,
            decision_date=update.decision_date,
            final_decision=update.final_decision,
            review_comments=update.review_comments
        )
        
        return {"message": "Submission updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating submission: {str(e)}")

@router.get("/submissions", response_model=List[Dict[str, Any]])
async def get_submissions(
    user_id: str = Query(..., description="User ID"),
    status_filter: Optional[str] = Query(None, description="Filter by status")
):
    """Get user's submission history"""
    try:
        submissions = await venue_service.get_user_submissions(
            user_id=user_id,
            status_filter=status_filter
        )
        
        return submissions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting submissions: {str(e)}")

@router.get("/venues/{venue_id}/analytics", response_model=Dict[str, Any])
async def get_venue_analytics(venue_id: str):
    """Get analytics for a specific venue"""
    try:
        analytics = await venue_service.get_venue_analytics(venue_id)
        
        return {
            'venue_id': analytics.venue_id,
            'name': analytics.name,
            'total_submissions': analytics.total_submissions,
            'acceptance_rate': analytics.acceptance_rate,
            'average_review_time': analytics.average_review_time,
            'impact_metrics': analytics.impact_metrics,
            'recent_trends': analytics.recent_trends
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting venue analytics: {str(e)}")

@router.get("/matches", response_model=List[Dict[str, Any]])
async def get_publication_matches(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(default=20, description="Maximum results to return")
):
    """Get stored publication matches for a user"""
    try:
        from core.database import get_db, PublicationMatch, PublicationVenue
        from sqlalchemy import desc
        
        db = next(get_db())
        
        matches = db.query(PublicationMatch, PublicationVenue).join(
            PublicationVenue, PublicationMatch.venue_id == PublicationVenue.id
        ).filter(
            PublicationMatch.user_id == user_id
        ).order_by(
            desc(PublicationMatch.relevance_score)
        ).limit(limit).all()
        
        db.close()
        
        return [
            {
                'match_id': match.id,
                'relevance_score': match.relevance_score,
                'fit_score': match.fit_score,
                'success_probability': match.success_probability,
                'match_reasons': match.match_reasons,
                'recommendation_strength': match.recommendation_strength,
                'venue': {
                    'id': venue.id,
                    'name': venue.name,
                    'venue_type': venue.venue_type,
                    'publisher': venue.publisher,
                    'impact_factor': venue.impact_factor,
                    'acceptance_rate': venue.acceptance_rate,
                    'open_access': venue.open_access,
                    'website_url': venue.website_url
                }
            }
            for match, venue in matches
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting publication matches: {str(e)}")