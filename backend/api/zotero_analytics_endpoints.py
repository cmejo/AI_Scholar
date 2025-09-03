"""
API endpoints for Zotero analytics and monitoring.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from services.zotero.zotero_monitoring_service import monitoring_service, MetricType
from core.auth import get_current_user
from models.schemas import User


router = APIRouter(prefix="/api/zotero/analytics", tags=["zotero-analytics"])


class MetricEventRequest(BaseModel):
    """Request model for recording metric events."""
    metric_type: str
    operation: str
    duration: Optional[float] = None
    success: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics."""
    operation_type: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    average_duration: float
    min_duration: float
    max_duration: float
    p95_duration: float
    error_rate: float
    throughput: float


class UsageAnalyticsResponse(BaseModel):
    """Response model for usage analytics."""
    total_users: int
    active_users_24h: int
    active_users_7d: int
    active_users_30d: int
    total_connections: int
    active_connections: int
    total_sync_operations: int
    total_search_queries: int
    total_citations_generated: int
    most_popular_features: List[Dict[str, Any]]
    user_engagement_score: float


class ErrorAnalyticsResponse(BaseModel):
    """Response model for error analytics."""
    total_errors: int
    error_rate: float
    error_types: Dict[str, int]
    error_operations: Dict[str, int]
    error_timeline: Dict[str, int]
    top_errors: List[List[Any]]


class UserActivityResponse(BaseModel):
    """Response model for user activity."""
    user_id: str
    time_range: Dict[str, str]
    total_activities: int
    activity_by_type: Dict[str, int]
    activity_timeline: Dict[str, int]
    total_duration: float
    average_duration: float
    success_rate: float
    most_active_day: Optional[str]


@router.post("/metrics/record")
async def record_metric(
    request: MetricEventRequest,
    current_user: User = Depends(get_current_user)
):
    """Record a metric event."""
    try:
        # Validate metric type
        try:
            metric_type = MetricType(request.metric_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid metric type: {request.metric_type}")
        
        # Create metric event
        from services.zotero.zotero_monitoring_service import MetricEvent
        
        metric_event = MetricEvent(
            metric_type=metric_type,
            user_id=current_user.id,
            connection_id=request.metadata.get('connection_id'),
            operation=request.operation,
            duration=request.duration,
            success=request.success,
            metadata=request.metadata,
            timestamp=datetime.utcnow()
        )
        
        await monitoring_service.record_metric(metric_event)
        
        return {"success": True, "message": "Metric recorded successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording metric: {str(e)}")


@router.get("/performance", response_model=Dict[str, PerformanceMetricsResponse])
async def get_performance_metrics(
    operation_type: Optional[str] = Query(None, description="Filter by operation type"),
    hours: int = Query(24, description="Time range in hours", ge=1, le=168),
    current_user: User = Depends(get_current_user)
):
    """Get performance metrics."""
    try:
        time_range = timedelta(hours=hours)
        metrics = await monitoring_service.get_performance_metrics(
            operation_type=operation_type,
            time_range=time_range
        )
        
        return {
            op_type: PerformanceMetricsResponse(
                operation_type=perf_metrics.operation_type,
                total_operations=perf_metrics.total_operations,
                successful_operations=perf_metrics.successful_operations,
                failed_operations=perf_metrics.failed_operations,
                average_duration=perf_metrics.average_duration,
                min_duration=perf_metrics.min_duration,
                max_duration=perf_metrics.max_duration,
                p95_duration=perf_metrics.p95_duration,
                error_rate=perf_metrics.error_rate,
                throughput=perf_metrics.throughput
            )
            for op_type, perf_metrics in metrics.items()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance metrics: {str(e)}")


@router.get("/usage", response_model=UsageAnalyticsResponse)
async def get_usage_analytics(
    days: int = Query(30, description="Time range in days", ge=1, le=365),
    current_user: User = Depends(get_current_user)
):
    """Get usage analytics."""
    try:
        time_range = timedelta(days=days)
        analytics = await monitoring_service.get_usage_analytics(time_range=time_range)
        
        return UsageAnalyticsResponse(
            total_users=analytics.total_users,
            active_users_24h=analytics.active_users_24h,
            active_users_7d=analytics.active_users_7d,
            active_users_30d=analytics.active_users_30d,
            total_connections=analytics.total_connections,
            active_connections=analytics.active_connections,
            total_sync_operations=analytics.total_sync_operations,
            total_search_queries=analytics.total_search_queries,
            total_citations_generated=analytics.total_citations_generated,
            most_popular_features=analytics.most_popular_features,
            user_engagement_score=analytics.user_engagement_score
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting usage analytics: {str(e)}")


@router.get("/errors", response_model=ErrorAnalyticsResponse)
async def get_error_analytics(
    hours: int = Query(24, description="Time range in hours", ge=1, le=168),
    current_user: User = Depends(get_current_user)
):
    """Get error analytics."""
    try:
        time_range = timedelta(hours=hours)
        error_analytics = await monitoring_service.get_error_analytics(time_range=time_range)
        
        return ErrorAnalyticsResponse(
            total_errors=error_analytics.get('total_errors', 0),
            error_rate=error_analytics.get('error_rate', 0),
            error_types=error_analytics.get('error_types', {}),
            error_operations=error_analytics.get('error_operations', {}),
            error_timeline=error_analytics.get('error_timeline', {}),
            top_errors=error_analytics.get('top_errors', [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting error analytics: {str(e)}")


@router.get("/user-activity", response_model=UserActivityResponse)
async def get_user_activity(
    user_id: Optional[str] = Query(None, description="User ID (defaults to current user)"),
    days: int = Query(7, description="Time range in days", ge=1, le=90),
    current_user: User = Depends(get_current_user)
):
    """Get user activity report."""
    try:
        # Use current user if no user_id specified
        target_user_id = user_id or current_user.id
        
        # Only allow users to view their own activity unless they're admin
        if target_user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        time_range = timedelta(days=days)
        activity = await monitoring_service.get_user_activity_report(
            user_id=target_user_id,
            time_range=time_range
        )
        
        return UserActivityResponse(
            user_id=activity.get('user_id', target_user_id),
            time_range=activity.get('time_range', {}),
            total_activities=activity.get('total_activities', 0),
            activity_by_type=activity.get('activity_by_type', {}),
            activity_timeline=activity.get('activity_timeline', {}),
            total_duration=activity.get('total_duration', 0),
            average_duration=activity.get('average_duration', 0),
            success_rate=activity.get('success_rate', 0),
            most_active_day=activity.get('most_active_day')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user activity: {str(e)}")


@router.get("/dashboard")
async def get_analytics_dashboard(
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive analytics dashboard data."""
    try:
        # Get data for different time ranges
        performance_24h = await monitoring_service.get_performance_metrics(time_range=timedelta(hours=24))
        performance_7d = await monitoring_service.get_performance_metrics(time_range=timedelta(days=7))
        
        usage_analytics = await monitoring_service.get_usage_analytics(time_range=timedelta(days=30))
        error_analytics = await monitoring_service.get_error_analytics(time_range=timedelta(hours=24))
        
        # Get user's personal activity
        user_activity = await monitoring_service.get_user_activity_report(
            user_id=current_user.id,
            time_range=timedelta(days=7)
        )
        
        return {
            "performance": {
                "24h": {
                    op_type: {
                        "operation_type": metrics.operation_type,
                        "total_operations": metrics.total_operations,
                        "success_rate": 100 - metrics.error_rate,
                        "average_duration": metrics.average_duration,
                        "throughput": metrics.throughput
                    }
                    for op_type, metrics in performance_24h.items()
                },
                "7d": {
                    op_type: {
                        "operation_type": metrics.operation_type,
                        "total_operations": metrics.total_operations,
                        "success_rate": 100 - metrics.error_rate,
                        "average_duration": metrics.average_duration,
                        "throughput": metrics.throughput
                    }
                    for op_type, metrics in performance_7d.items()
                }
            },
            "usage": {
                "total_users": usage_analytics.total_users,
                "active_users_24h": usage_analytics.active_users_24h,
                "active_users_7d": usage_analytics.active_users_7d,
                "active_users_30d": usage_analytics.active_users_30d,
                "user_engagement_score": usage_analytics.user_engagement_score,
                "most_popular_features": usage_analytics.most_popular_features[:5]
            },
            "errors": {
                "total_errors_24h": error_analytics.get('total_errors', 0),
                "error_rate_24h": error_analytics.get('error_rate', 0),
                "top_error_types": list(error_analytics.get('error_types', {}).items())[:5]
            },
            "user_activity": {
                "total_activities_7d": user_activity.get('total_activities', 0),
                "success_rate": user_activity.get('success_rate', 0),
                "most_used_features": list(user_activity.get('activity_by_type', {}).items())[:5]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard data: {str(e)}")


@router.get("/reports/daily")
async def get_daily_report(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (defaults to yesterday)"),
    current_user: User = Depends(get_current_user)
):
    """Get daily monitoring report."""
    try:
        # Only allow admin users to access reports
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        if date:
            try:
                report_date = datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        else:
            report_date = datetime.utcnow() - timedelta(days=1)
        
        # Generate report for the specified date
        report = await monitoring_service.generate_daily_report()
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating daily report: {str(e)}")


@router.get("/health")
async def get_monitoring_health():
    """Get monitoring service health status."""
    try:
        # Check Redis connection
        from core.redis_client import get_redis_client
        redis_client = await get_redis_client()
        redis_healthy = redis_client is not None
        
        if redis_healthy:
            try:
                await redis_client.ping()
            except Exception:
                redis_healthy = False
        
        # Check database connection
        from core.database import get_db
        db_healthy = True
        try:
            db = next(get_db())
            db.execute("SELECT 1")
        except Exception:
            db_healthy = False
        
        # Check metrics buffer status
        buffer_size = len(monitoring_service.metrics_buffer)
        buffer_healthy = buffer_size < 5000  # Alert if buffer is getting too full
        
        health_status = {
            "status": "healthy" if all([redis_healthy, db_healthy, buffer_healthy]) else "unhealthy",
            "components": {
                "redis": "healthy" if redis_healthy else "unhealthy",
                "database": "healthy" if db_healthy else "unhealthy",
                "metrics_buffer": "healthy" if buffer_healthy else "unhealthy"
            },
            "metrics": {
                "buffer_size": buffer_size,
                "cache_entries": len(monitoring_service.performance_cache) + len(monitoring_service.analytics_cache)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }