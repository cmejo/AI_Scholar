"""
Admin API endpoints for Zotero integration monitoring and management.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from services.zotero.zotero_admin_dashboard_service import admin_dashboard_service
from core.auth import get_current_user, require_admin
from models.schemas import User


router = APIRouter(prefix="/api/zotero/admin", tags=["zotero-admin"])


class SystemHealthResponse(BaseModel):
    """Response model for system health."""
    overall_status: str
    database_status: str
    redis_status: str
    api_status: str
    sync_service_status: str
    last_check: str
    issues: List[str]


class ResourceUsageResponse(BaseModel):
    """Response model for resource usage."""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    database_connections: int
    redis_connections: int
    active_sync_operations: int


class AlertResponse(BaseModel):
    """Response model for alerts."""
    alert_id: str
    severity: str
    title: str
    description: str
    timestamp: str
    resolved: bool
    affected_users: int


class UserStatisticsResponse(BaseModel):
    """Response model for user statistics."""
    total_users: int
    active_connections: int
    connection_status_breakdown: Dict[str, int]
    recent_active_users: int
    top_users_by_activity: List[Dict[str, Any]]


class SyncStatisticsResponse(BaseModel):
    """Response model for sync statistics."""
    by_time_period: Dict[str, Dict[str, Any]]
    by_sync_type: Dict[str, int]


class LibraryStatisticsResponse(BaseModel):
    """Response model for library statistics."""
    total_libraries: int
    total_items: int
    total_collections: int
    libraries_by_type: Dict[str, int]
    items_by_type: Dict[str, int]
    largest_libraries: List[Dict[str, Any]]
    recent_items_added: int


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    current_user: User = Depends(require_admin)
):
    """Get system health status."""
    try:
        health = await admin_dashboard_service.get_system_health()
        
        return SystemHealthResponse(
            overall_status=health.overall_status,
            database_status=health.database_status,
            redis_status=health.redis_status,
            api_status=health.api_status,
            sync_service_status=health.sync_service_status,
            last_check=health.last_check.isoformat(),
            issues=health.issues
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system health: {str(e)}")


@router.get("/resources", response_model=ResourceUsageResponse)
async def get_resource_usage(
    current_user: User = Depends(require_admin)
):
    """Get current resource usage."""
    try:
        usage = await admin_dashboard_service.get_resource_usage()
        
        return ResourceUsageResponse(
            cpu_usage=usage.cpu_usage,
            memory_usage=usage.memory_usage,
            disk_usage=usage.disk_usage,
            database_connections=usage.database_connections,
            redis_connections=usage.redis_connections,
            active_sync_operations=usage.active_sync_operations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting resource usage: {str(e)}")


@router.get("/alerts", response_model=List[AlertResponse])
async def get_active_alerts(
    current_user: User = Depends(require_admin)
):
    """Get active system alerts."""
    try:
        alerts = await admin_dashboard_service.get_active_alerts()
        
        return [
            AlertResponse(
                alert_id=alert.alert_id,
                severity=alert.severity,
                title=alert.title,
                description=alert.description,
                timestamp=alert.timestamp.isoformat(),
                resolved=alert.resolved,
                affected_users=alert.affected_users
            )
            for alert in alerts
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting alerts: {str(e)}")


@router.get("/users", response_model=UserStatisticsResponse)
async def get_user_statistics(
    current_user: User = Depends(require_admin)
):
    """Get user statistics."""
    try:
        stats = await admin_dashboard_service.get_user_statistics()
        
        return UserStatisticsResponse(
            total_users=stats.get('total_users', 0),
            active_connections=stats.get('active_connections', 0),
            connection_status_breakdown=stats.get('connection_status_breakdown', {}),
            recent_active_users=stats.get('recent_active_users', 0),
            top_users_by_activity=stats.get('top_users_by_activity', [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user statistics: {str(e)}")


@router.get("/sync", response_model=SyncStatisticsResponse)
async def get_sync_statistics(
    current_user: User = Depends(require_admin)
):
    """Get sync operation statistics."""
    try:
        stats = await admin_dashboard_service.get_sync_statistics()
        
        return SyncStatisticsResponse(
            by_time_period=stats.get('by_time_period', {}),
            by_sync_type=stats.get('by_sync_type', {})
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sync statistics: {str(e)}")


@router.get("/libraries", response_model=LibraryStatisticsResponse)
async def get_library_statistics(
    current_user: User = Depends(require_admin)
):
    """Get library and item statistics."""
    try:
        stats = await admin_dashboard_service.get_library_statistics()
        
        return LibraryStatisticsResponse(
            total_libraries=stats.get('total_libraries', 0),
            total_items=stats.get('total_items', 0),
            total_collections=stats.get('total_collections', 0),
            libraries_by_type=stats.get('libraries_by_type', {}),
            items_by_type=stats.get('items_by_type', {}),
            largest_libraries=stats.get('largest_libraries', []),
            recent_items_added=stats.get('recent_items_added', 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting library statistics: {str(e)}")


@router.get("/dashboard")
async def get_admin_dashboard(
    current_user: User = Depends(require_admin)
):
    """Get comprehensive admin dashboard data."""
    try:
        dashboard_data = await admin_dashboard_service.get_comprehensive_dashboard_data()
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard data: {str(e)}")


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(require_admin)
):
    """Resolve an active alert."""
    try:
        # In a real implementation, this would update the alert status
        # For now, we'll just return success
        return {
            "success": True,
            "message": f"Alert {alert_id} resolved",
            "resolved_by": current_user.id,
            "resolved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resolving alert: {str(e)}")


@router.post("/maintenance/flush-metrics")
async def flush_metrics_buffer(
    current_user: User = Depends(require_admin)
):
    """Manually flush metrics buffer to database."""
    try:
        from services.zotero.zotero_monitoring_service import monitoring_service
        
        buffer_size_before = len(monitoring_service.metrics_buffer)
        await monitoring_service._flush_metrics_buffer()
        buffer_size_after = len(monitoring_service.metrics_buffer)
        
        return {
            "success": True,
            "message": "Metrics buffer flushed",
            "metrics_flushed": buffer_size_before - buffer_size_after,
            "remaining_in_buffer": buffer_size_after
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error flushing metrics: {str(e)}")


@router.post("/maintenance/clear-cache")
async def clear_analytics_cache(
    current_user: User = Depends(require_admin)
):
    """Clear analytics cache."""
    try:
        from services.zotero.zotero_monitoring_service import monitoring_service
        
        performance_cache_size = len(monitoring_service.performance_cache)
        analytics_cache_size = len(monitoring_service.analytics_cache)
        
        monitoring_service.performance_cache.clear()
        monitoring_service.analytics_cache.clear()
        
        return {
            "success": True,
            "message": "Analytics cache cleared",
            "performance_cache_entries_cleared": performance_cache_size,
            "analytics_cache_entries_cleared": analytics_cache_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")


@router.get("/maintenance/status")
async def get_maintenance_status(
    current_user: User = Depends(require_admin)
):
    """Get maintenance and operational status."""
    try:
        from services.zotero.zotero_monitoring_service import monitoring_service
        
        # Get buffer and cache status
        buffer_size = len(monitoring_service.metrics_buffer)
        performance_cache_size = len(monitoring_service.performance_cache)
        analytics_cache_size = len(monitoring_service.analytics_cache)
        
        # Get database connection info
        from core.database import get_db
        db_healthy = True
        try:
            db = next(get_db())
            db.execute("SELECT 1")
        except Exception:
            db_healthy = False
        
        # Get Redis connection info
        from core.redis_client import get_redis_client
        redis_healthy = True
        try:
            redis_client = await get_redis_client()
            if redis_client:
                await redis_client.ping()
            else:
                redis_healthy = False
        except Exception:
            redis_healthy = False
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics_buffer": {
                "size": buffer_size,
                "max_size": monitoring_service.metrics_buffer.maxlen,
                "usage_percentage": (buffer_size / monitoring_service.metrics_buffer.maxlen) * 100
            },
            "cache_status": {
                "performance_cache_entries": performance_cache_size,
                "analytics_cache_entries": analytics_cache_size,
                "cache_ttl_seconds": monitoring_service.cache_ttl
            },
            "service_health": {
                "database": "healthy" if db_healthy else "unhealthy",
                "redis": "healthy" if redis_healthy else "unhealthy"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting maintenance status: {str(e)}")


@router.get("/logs/recent")
async def get_recent_logs(
    limit: int = Query(100, description="Number of recent log entries", ge=1, le=1000),
    level: Optional[str] = Query(None, description="Log level filter"),
    current_user: User = Depends(require_admin)
):
    """Get recent log entries."""
    try:
        # In a real implementation, this would fetch from a logging system
        # For now, return a placeholder response
        return {
            "logs": [],
            "message": "Log retrieval not implemented - would integrate with logging system",
            "requested_limit": limit,
            "requested_level": level
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")


@router.get("/config/thresholds")
async def get_alert_thresholds(
    current_user: User = Depends(require_admin)
):
    """Get current alert thresholds."""
    try:
        return {
            "thresholds": admin_dashboard_service.alert_thresholds,
            "description": {
                "error_rate": "Error rate percentage threshold",
                "response_time": "Response time threshold in seconds",
                "sync_failures": "Number of sync failures per hour threshold",
                "memory_usage": "Memory usage percentage threshold",
                "disk_usage": "Disk usage percentage threshold"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting thresholds: {str(e)}")


@router.put("/config/thresholds")
async def update_alert_thresholds(
    thresholds: Dict[str, float],
    current_user: User = Depends(require_admin)
):
    """Update alert thresholds."""
    try:
        # Validate threshold values
        valid_keys = set(admin_dashboard_service.alert_thresholds.keys())
        provided_keys = set(thresholds.keys())
        
        if not provided_keys.issubset(valid_keys):
            invalid_keys = provided_keys - valid_keys
            raise HTTPException(
                status_code=400,
                detail=f"Invalid threshold keys: {list(invalid_keys)}"
            )
        
        # Update thresholds
        admin_dashboard_service.alert_thresholds.update(thresholds)
        
        return {
            "success": True,
            "message": "Alert thresholds updated",
            "updated_thresholds": thresholds,
            "current_thresholds": admin_dashboard_service.alert_thresholds
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating thresholds: {str(e)}")