"""
Analytics API routes
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import PlainTextResponse

from analytics.models import AnalyticsData, UserMetrics, SystemMetrics, EventData
from analytics.service import analytics_service
from auth.dependencies import get_current_user, get_optional_user, require_role
from auth.models import UserRole

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/dashboard", response_model=AnalyticsData)
async def get_dashboard_analytics(
    range: str = "30d",
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """Get analytics dashboard data"""
    try:
        # Allow public access to demo analytics, but with limited data for non-authenticated users
        if not current_user:
            # Return limited demo data for non-authenticated users
            return analytics_service.get_dashboard_analytics("7d")  # Limited to 7 days
        
        # Full access for authenticated users
        return analytics_service.get_dashboard_analytics(range)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics data: {str(e)}"
        )

@router.get("/users/{user_id}", response_model=UserMetrics)
async def get_user_metrics(
    user_id: str,
    current_user: dict = Depends(require_role(UserRole.RESEARCHER))
):
    """Get metrics for a specific user (requires researcher role or higher)"""
    try:
        # Users can only view their own metrics unless they're admin/researcher
        if current_user["role"] not in [UserRole.ADMIN.value, UserRole.RESEARCHER.value]:
            if current_user["id"] != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        return analytics_service.get_user_metrics(user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user metrics: {str(e)}"
        )

@router.get("/system", response_model=SystemMetrics)
async def get_system_metrics(
    current_user: dict = Depends(require_role(UserRole.ADMIN))
):
    """Get system metrics (admin only)"""
    try:
        return analytics_service.get_system_metrics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system metrics: {str(e)}"
        )

@router.post("/events")
async def track_event(
    event_data: EventData,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """Track an analytics event"""
    try:
        user_id = current_user["id"] if current_user else None
        analytics_service.track_event(
            user_id=user_id,
            event=event_data.event,
            properties=event_data.properties
        )
        return {"status": "success", "message": "Event tracked successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track event: {str(e)}"
        )

@router.get("/export")
async def export_analytics(
    range: str = "30d",
    format: str = "csv",
    current_user: dict = Depends(require_role(UserRole.RESEARCHER))
):
    """Export analytics data"""
    try:
        if format.lower() not in ["csv", "json"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported format. Use 'csv' or 'json'"
            )
        
        exported_data = analytics_service.export_analytics_data(range, format)
        
        if format.lower() == "csv":
            return PlainTextResponse(
                content=exported_data,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=analytics_{range}.csv"}
            )
        else:
            return Response(
                content=exported_data,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=analytics_{range}.json"}
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export analytics data: {str(e)}"
        )

# Public endpoints for demo purposes
@router.get("/demo/dashboard")
async def get_demo_analytics():
    """Get demo analytics data (public access)"""
    try:
        # Return simple dict to avoid serialization issues
        return {
            "total_users": 2847,
            "active_users": 1234,
            "total_messages": 15692,
            "avg_response_time": 150,
            "user_growth": 12.5,
            "message_growth": 18.3,
            "daily_activity": [
                {"date": "2025-08-10", "users": 120, "messages": 250},
                {"date": "2025-08-11", "users": 135, "messages": 280},
                {"date": "2025-08-12", "users": 98, "messages": 190},
                {"date": "2025-08-13", "users": 142, "messages": 310},
                {"date": "2025-08-14", "users": 156, "messages": 340},
                {"date": "2025-08-15", "users": 134, "messages": 275},
                {"date": "2025-08-16", "users": 128, "messages": 260},
                {"date": "2025-08-17", "users": 145, "messages": 295},
                {"date": "2025-08-18", "users": 167, "messages": 380},
                {"date": "2025-08-19", "users": 152, "messages": 320},
                {"date": "2025-08-20", "users": 139, "messages": 285},
                {"date": "2025-08-21", "users": 148, "messages": 305},
                {"date": "2025-08-22", "users": 161, "messages": 350},
                {"date": "2025-08-23", "users": 143, "messages": 290},
                {"date": "2025-08-24", "users": 157, "messages": 335},
                {"date": "2025-08-25", "users": 172, "messages": 395},
                {"date": "2025-08-26", "users": 165, "messages": 365},
                {"date": "2025-08-27", "users": 149, "messages": 300},
                {"date": "2025-08-28", "users": 158, "messages": 340},
                {"date": "2025-08-29", "users": 174, "messages": 410},
                {"date": "2025-08-30", "users": 168, "messages": 375},
                {"date": "2025-08-31", "users": 155, "messages": 325},
                {"date": "2025-09-01", "users": 162, "messages": 355},
                {"date": "2025-09-02", "users": 179, "messages": 420},
                {"date": "2025-09-03", "users": 171, "messages": 385},
                {"date": "2025-09-04", "users": 164, "messages": 360},
                {"date": "2025-09-05", "users": 176, "messages": 405},
                {"date": "2025-09-06", "users": 183, "messages": 445},
                {"date": "2025-09-07", "users": 189, "messages": 465},
                {"date": "2025-09-08", "users": 195, "messages": 485}
            ],
            "top_content": [
                {"title": "AI Research Paper Analysis", "views": 1250, "engagement": 85},
                {"title": "Machine Learning Discussion", "views": 980, "engagement": 72},
                {"title": "Data Science Workflow", "views": 856, "engagement": 68},
                {"title": "Natural Language Processing", "views": 743, "engagement": 91},
                {"title": "Computer Vision Tutorial", "views": 692, "engagement": 64},
                {"title": "Deep Learning Concepts", "views": 587, "engagement": 78},
                {"title": "Statistical Analysis Guide", "views": 534, "engagement": 56},
                {"title": "Research Methodology", "views": 489, "engagement": 82},
                {"title": "Academic Writing Tips", "views": 445, "engagement": 59},
                {"title": "Citation Management", "views": 398, "engagement": 73}
            ],
            "performance_metrics": {
                "uptime": 99.8,
                "error_rate": 0.1,
                "avg_load_time": 150
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve demo analytics: {str(e)}"
        )

@router.get("/health")
async def analytics_health():
    """Analytics service health check"""
    from datetime import datetime
    from fastapi.encoders import jsonable_encoder
    
    response = {
        "status": "ok",
        "service": "analytics",
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonable_encoder(response)

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Analytics API is working!"}