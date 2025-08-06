"""
Funding Matcher API Endpoints

This module provides REST API endpoints for funding opportunity discovery and matching.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from services.funding_matcher_service import FundingMatcherService

router = APIRouter(prefix="/api/funding", tags=["funding"])
funding_service = FundingMatcherService()

# Request/Response Models

class ResearchProfileCreate(BaseModel):
    """Model for creating/updating research profile"""
    research_interests: List[str] = Field(..., description="List of research interests/keywords")
    expertise_areas: Dict[str, float] = Field(..., description="Areas of expertise with proficiency levels (0-1)")
    research_domains: List[str] = Field(..., description="Academic research domains")
    career_stage: str = Field(..., description="Career stage (undergraduate, graduate, postdoc, faculty)")
    institution_affiliation: Optional[str] = Field(None, description="Current institution")
    previous_funding: List[Dict[str, Any]] = Field(default_factory=list, description="Previous funding history")
    publications: List[Dict[str, Any]] = Field(default_factory=list, description="Publication history")
    collaborators: List[str] = Field(default_factory=list, description="Frequent collaborators")
    geographic_preferences: List[str] = Field(default_factory=list, description="Preferred funding regions")
    funding_amount_range: Dict[str, float] = Field(default_factory=dict, description="Preferred funding amount range")

class FundingOpportunityCreate(BaseModel):
    """Model for creating funding opportunity"""
    title: str = Field(..., description="Opportunity title")
    description: str = Field(..., description="Detailed description")
    funding_agency: str = Field(..., description="Funding agency name")
    program_name: Optional[str] = Field(None, description="Program name")
    opportunity_type: str = Field(..., description="Type of opportunity (grant, fellowship, award)")
    funding_amount_min: Optional[float] = Field(None, description="Minimum funding amount")
    funding_amount_max: Optional[float] = Field(None, description="Maximum funding amount")
    duration_months: Optional[int] = Field(None, description="Duration in months")
    eligibility_criteria: Dict[str, Any] = Field(default_factory=dict, description="Eligibility requirements")
    research_areas: List[str] = Field(default_factory=list, description="Relevant research areas")
    keywords: List[str] = Field(default_factory=list, description="Keywords for matching")
    application_deadline: datetime = Field(..., description="Application deadline")
    application_url: Optional[str] = Field(None, description="Application URL")
    requirements: Dict[str, Any] = Field(default_factory=dict, description="Application requirements")
    restrictions: Dict[str, Any] = Field(default_factory=dict, description="Geographic or other restrictions")

class FundingAlertCreate(BaseModel):
    """Model for creating funding alert"""
    alert_name: str = Field(..., description="Name for the alert")
    search_criteria: Dict[str, Any] = Field(..., description="Search criteria for matching")
    notification_frequency: str = Field(default="weekly", description="Notification frequency")

class FundingSearchRequest(BaseModel):
    """Model for funding search request"""
    keywords: List[str] = Field(..., description="Search keywords")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional search filters")
    limit: int = Field(default=50, description="Maximum results to return")
    min_relevance: float = Field(default=0.4, description="Minimum relevance score")

class FundingMatchResponse(BaseModel):
    """Model for funding match response"""
    opportunity_id: str
    title: str
    funding_agency: str
    relevance_score: float
    match_reasons: List[str]
    eligibility_status: str
    recommendation_strength: str
    application_deadline: Optional[datetime]
    funding_amount_range: List[Optional[float]]

# API Endpoints

@router.post("/profile", response_model=Dict[str, str])
async def create_research_profile(
    profile: ResearchProfileCreate,
    user_id: str = Query(..., description="User ID")
):
    """Create or update user's research profile"""
    try:
        from core.database import get_db, ResearchProfile
        
        db = next(get_db())
        
        # Check if profile exists
        existing_profile = db.query(ResearchProfile).filter(
            ResearchProfile.user_id == user_id
        ).first()
        
        if existing_profile:
            # Update existing profile
            existing_profile.research_interests = profile.research_interests
            existing_profile.expertise_areas = profile.expertise_areas
            existing_profile.research_domains = profile.research_domains
            existing_profile.career_stage = profile.career_stage
            existing_profile.institution_affiliation = profile.institution_affiliation
            existing_profile.previous_funding = profile.previous_funding
            existing_profile.publications = profile.publications
            existing_profile.collaborators = profile.collaborators
            existing_profile.geographic_preferences = profile.geographic_preferences
            existing_profile.funding_amount_range = profile.funding_amount_range
            existing_profile.updated_at = datetime.now()
        else:
            # Create new profile
            new_profile = ResearchProfile(
                user_id=user_id,
                research_interests=profile.research_interests,
                expertise_areas=profile.expertise_areas,
                research_domains=profile.research_domains,
                career_stage=profile.career_stage,
                institution_affiliation=profile.institution_affiliation,
                previous_funding=profile.previous_funding,
                publications=profile.publications,
                collaborators=profile.collaborators,
                geographic_preferences=profile.geographic_preferences,
                funding_amount_range=profile.funding_amount_range
            )
            db.add(new_profile)
        
        db.commit()
        db.close()
        
        return {"message": "Research profile created/updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating research profile: {str(e)}")

@router.get("/profile", response_model=Dict[str, Any])
async def get_research_profile(user_id: str = Query(..., description="User ID")):
    """Get user's research profile"""
    try:
        from core.database import get_db, ResearchProfile
        
        db = next(get_db())
        
        profile = db.query(ResearchProfile).filter(
            ResearchProfile.user_id == user_id
        ).first()
        
        db.close()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Research profile not found")
        
        return {
            "user_id": profile.user_id,
            "research_interests": profile.research_interests,
            "expertise_areas": profile.expertise_areas,
            "research_domains": profile.research_domains,
            "career_stage": profile.career_stage,
            "institution_affiliation": profile.institution_affiliation,
            "previous_funding": profile.previous_funding,
            "publications": profile.publications,
            "collaborators": profile.collaborators,
            "geographic_preferences": profile.geographic_preferences,
            "funding_amount_range": profile.funding_amount_range,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting research profile: {str(e)}")

@router.post("/discover", response_model=List[FundingMatchResponse])
async def discover_funding_opportunities(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(default=50, description="Maximum results to return"),
    min_relevance: float = Query(default=0.4, description="Minimum relevance score")
):
    """Discover funding opportunities for a user"""
    try:
        matches = await funding_service.discover_funding_opportunities(
            user_id=user_id,
            limit=limit,
            min_relevance=min_relevance
        )
        
        return [
            FundingMatchResponse(
                opportunity_id=match.opportunity_id,
                title=match.title,
                funding_agency=match.funding_agency,
                relevance_score=match.relevance_score,
                match_reasons=match.match_reasons,
                eligibility_status=match.eligibility_status,
                recommendation_strength=match.recommendation_strength,
                application_deadline=match.application_deadline,
                funding_amount_range=[match.funding_amount_range[0], match.funding_amount_range[1]]
            )
            for match in matches
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error discovering funding opportunities: {str(e)}")

@router.get("/matches", response_model=List[Dict[str, Any]])
async def get_funding_matches(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(default=20, description="Maximum results to return")
):
    """Get stored funding matches for a user"""
    try:
        matches = await funding_service.get_funding_matches(user_id=user_id, limit=limit)
        return matches
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting funding matches: {str(e)}")

@router.post("/search", response_model=List[Dict[str, Any]])
async def search_grant_databases(search_request: FundingSearchRequest):
    """Search multiple grant databases for funding opportunities"""
    try:
        opportunities = await funding_service.search_grant_databases(
            keywords=search_request.keywords,
            filters=search_request.filters
        )
        
        return opportunities
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching grant databases: {str(e)}")

@router.post("/alerts", response_model=Dict[str, str])
async def create_funding_alert(
    alert: FundingAlertCreate,
    user_id: str = Query(..., description="User ID")
):
    """Create a funding alert for automatic notifications"""
    try:
        alert_id = await funding_service.create_funding_alert(
            user_id=user_id,
            alert_name=alert.alert_name,
            search_criteria=alert.search_criteria,
            notification_frequency=alert.notification_frequency
        )
        
        return {"alert_id": alert_id, "message": "Funding alert created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating funding alert: {str(e)}")

@router.get("/alerts", response_model=List[Dict[str, Any]])
async def get_funding_alerts(user_id: str = Query(..., description="User ID")):
    """Get user's funding alerts"""
    try:
        from core.database import get_db, FundingAlert
        
        db = next(get_db())
        
        alerts = db.query(FundingAlert).filter(
            FundingAlert.user_id == user_id
        ).all()
        
        db.close()
        
        return [
            {
                "id": alert.id,
                "alert_name": alert.alert_name,
                "search_criteria": alert.search_criteria,
                "notification_frequency": alert.notification_frequency,
                "is_active": alert.is_active,
                "last_triggered": alert.last_triggered,
                "created_at": alert.created_at
            }
            for alert in alerts
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting funding alerts: {str(e)}")

@router.post("/notifications/send")
async def send_funding_notifications(user_id: str = Query(..., description="User ID")):
    """Send funding opportunity notifications to user"""
    try:
        await funding_service.send_funding_notifications(user_id)
        return {"message": "Notifications sent successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending notifications: {str(e)}")

@router.get("/notifications", response_model=List[Dict[str, Any]])
async def get_funding_notifications(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(default=20, description="Maximum results to return"),
    unread_only: bool = Query(default=False, description="Return only unread notifications")
):
    """Get user's funding notifications"""
    try:
        from core.database import get_db, FundingNotification, FundingOpportunity
        from sqlalchemy import and_
        
        db = next(get_db())
        
        query = db.query(FundingNotification, FundingOpportunity).join(
            FundingOpportunity, FundingNotification.funding_opportunity_id == FundingOpportunity.id
        ).filter(FundingNotification.user_id == user_id)
        
        if unread_only:
            query = query.filter(FundingNotification.is_read == False)
        
        notifications = query.order_by(FundingNotification.sent_at.desc()).limit(limit).all()
        
        db.close()
        
        return [
            {
                "id": notification.id,
                "notification_type": notification.notification_type,
                "message": notification.message,
                "is_read": notification.is_read,
                "sent_at": notification.sent_at,
                "opportunity": {
                    "id": opportunity.id,
                    "title": opportunity.title,
                    "funding_agency": opportunity.funding_agency,
                    "application_deadline": opportunity.application_deadline
                }
            }
            for notification, opportunity in notifications
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting notifications: {str(e)}")

@router.post("/opportunities", response_model=Dict[str, str])
async def create_funding_opportunity(opportunity: FundingOpportunityCreate):
    """Create a new funding opportunity (admin function)"""
    try:
        from core.database import get_db, FundingOpportunity
        
        db = next(get_db())
        
        new_opportunity = FundingOpportunity(
            title=opportunity.title,
            description=opportunity.description,
            funding_agency=opportunity.funding_agency,
            program_name=opportunity.program_name,
            opportunity_type=opportunity.opportunity_type,
            funding_amount_min=opportunity.funding_amount_min,
            funding_amount_max=opportunity.funding_amount_max,
            duration_months=opportunity.duration_months,
            eligibility_criteria=opportunity.eligibility_criteria,
            research_areas=opportunity.research_areas,
            keywords=opportunity.keywords,
            application_deadline=opportunity.application_deadline,
            application_url=opportunity.application_url,
            requirements=opportunity.requirements,
            restrictions=opportunity.restrictions,
            is_active=True,
            source="manual"
        )
        
        db.add(new_opportunity)
        db.commit()
        db.refresh(new_opportunity)
        db.close()
        
        return {"opportunity_id": new_opportunity.id, "message": "Funding opportunity created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating funding opportunity: {str(e)}")

@router.get("/opportunities", response_model=List[Dict[str, Any]])
async def get_funding_opportunities(
    limit: int = Query(default=50, description="Maximum results to return"),
    active_only: bool = Query(default=True, description="Return only active opportunities"),
    agency: Optional[str] = Query(None, description="Filter by funding agency")
):
    """Get funding opportunities"""
    try:
        from core.database import get_db, FundingOpportunity
        from sqlalchemy import and_
        
        db = next(get_db())
        
        query = db.query(FundingOpportunity)
        
        if active_only:
            query = query.filter(
                and_(
                    FundingOpportunity.is_active == True,
                    FundingOpportunity.application_deadline > datetime.now()
                )
            )
        
        if agency:
            query = query.filter(FundingOpportunity.funding_agency.ilike(f"%{agency}%"))
        
        opportunities = query.order_by(FundingOpportunity.application_deadline).limit(limit).all()
        
        db.close()
        
        return [
            {
                "id": opp.id,
                "title": opp.title,
                "description": opp.description,
                "funding_agency": opp.funding_agency,
                "program_name": opp.program_name,
                "opportunity_type": opp.opportunity_type,
                "funding_amount_min": opp.funding_amount_min,
                "funding_amount_max": opp.funding_amount_max,
                "duration_months": opp.duration_months,
                "research_areas": opp.research_areas,
                "keywords": opp.keywords,
                "application_deadline": opp.application_deadline,
                "application_url": opp.application_url,
                "success_rate": opp.success_rate,
                "is_active": opp.is_active,
                "source": opp.source
            }
            for opp in opportunities
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting funding opportunities: {str(e)}")

@router.get("/analytics", response_model=Dict[str, Any])
async def get_funding_analytics(
    user_id: str = Query(..., description="User ID"),
    time_range_days: int = Query(default=365, description="Time range for analytics in days")
):
    """Get funding opportunity analytics and success rate data"""
    try:
        analytics = await funding_service.get_funding_analytics(
            user_id=user_id,
            time_range_days=time_range_days
        )
        
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting funding analytics: {str(e)}")

@router.get("/optimization", response_model=Dict[str, Any])
async def get_application_optimization(
    user_id: str = Query(..., description="User ID"),
    target_success_rate: float = Query(default=0.3, description="Target success rate (0.0 to 1.0)")
):
    """Get application optimization recommendations"""
    try:
        optimization = await funding_service.optimize_application_strategy(
            user_id=user_id,
            target_success_rate=target_success_rate
        )
        
        return optimization
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting optimization recommendations: {str(e)}")

@router.get("/trending", response_model=List[Dict[str, Any]])
async def get_trending_opportunities(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(default=10, description="Maximum results to return")
):
    """Get trending funding opportunities with AI-powered analysis"""
    try:
        trending = await funding_service.get_trending_opportunities(
            user_id=user_id,
            limit=limit
        )
        
        return trending
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trending opportunities: {str(e)}")

@router.post("/databases/setup")
async def setup_grant_databases():
    """Set up default grant databases (admin function)"""
    try:
        await funding_service.setup_default_grant_databases()
        return {"message": "Grant databases set up successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting up grant databases: {str(e)}")

@router.get("/databases", response_model=List[Dict[str, Any]])
async def get_grant_databases():
    """Get available grant databases"""
    try:
        from core.database import get_db, GrantDatabase
        
        db = next(get_db())
        
        databases = db.query(GrantDatabase).filter(
            GrantDatabase.is_active == True
        ).all()
        
        db.close()
        
        return [
            {
                "id": db.id,
                "name": db.name,
                "description": db.description,
                "base_url": db.base_url,
                "authentication_type": db.authentication_type,
                "last_sync": db.last_sync,
                "sync_frequency_hours": db.sync_frequency_hours,
                "supported_fields": db.supported_fields,
                "rate_limit": db.rate_limit
            }
            for db in databases
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting grant databases: {str(e)}")