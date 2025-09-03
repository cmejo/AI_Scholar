"""
Zotero sync monitoring API endpoints
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from services.auth_service import get_current_user
from services.zotero.zotero_sync_monitoring_service import ZoteroSyncMonitoringService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zotero/sync/monitoring", tags=["zotero-sync-monitoring"])


class NotificationCreate(BaseModel):
    connection_id: str = Field(..., description="Zotero connection ID")
    status_type: str = Field(..., description="Type of notification")
    status: str = Field(..., description="Status level")
    title: str = Field(..., description="Notification title")
    message: Optional[str] = Field(None, description="Notification message")
    progress_percentage: int = Field(0, description="Progress percentage")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


@router.get("/notifications")
async def get_sync_notifications(
    connection_id: str = Query(..., description="Zotero connection ID"),
    status_type: Optional[str] = Query(None, description="Filter by status type"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    limit: int = Query(50, description="Maximum number of notifications to return"),
    offset: int = Query(0, description="Number of notifications to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sync notifications for a connection"""
    try:
        monitoring_service = ZoteroSyncMonitoringService(db)
        
        # Validate limit
        if limit > 100:
            limit = 100
        
        result = monitoring_service.get_sync_notifications(
            connection_id=connection_id,
            status_type=status_type,
            is_read=is_read,
            limit=limit,
            offset=offset
        )
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error getting sync notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications")
async def create_sync_notification(
    notification_data: NotificationCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new sync notification"""
    try:
        monitoring_service = ZoteroSyncMonitoringService(db)
        
        # Validate status type
        valid_status_types = ['sync_progress', 'error_report', 'completion_notification', 'warning']
        if notification_data.status_type not in valid_status_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status type. Must be one of: {', '.join(valid_status_types)}"
            )
        
        # Validate status
        valid_statuses = ['in_progress', 'completed', 'error', 'warning', 'info']
        if notification_data.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        notification_id = monitoring_service.create_sync_notification(
            connection_id=notification_data.connection_id,
            status_type=notification_data.status_type,
            status=notification_data.status,
            title=notification_data.title,
            message=notification_data.message,
            progress_percentage=notification_data.progress_percentage,
            details=notification_data.details
        )
        
        return {
            "status": "success",
            "message": "Sync notification created successfully",
            "data": {
                "notification_id": notification_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating sync notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    connection_id: str = Query(..., description="Zotero connection ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    try:
        monitoring_service = ZoteroSyncMonitoringService(db)
        
        success = monitoring_service.mark_notification_as_read(
            notification_id=notification_id,
            connection_id=connection_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {
            "status": "success",
            "message": "Notification marked as read"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/read-all")
async def mark_all_notifications_as_read(
    connection_id: str = Query(..., description="Zotero connection ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read for a connection"""
    try:
        monitoring_service = ZoteroSyncMonitoringService(db)
        
        updated_count = monitoring_service.mark_all_notifications_as_read(connection_id)
        
        return {
            "status": "success",
            "message": f"Marked {updated_count} notifications as read",
            "data": {
                "updated_count": updated_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    connection_id: str = Query(..., description="Zotero connection ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a notification"""
    try:
        monitoring_service = ZoteroSyncMonitoringService(db)
        
        success = monitoring_service.delete_notification(
            notification_id=notification_id,
            connection_id=connection_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {
            "status": "success",
            "message": "Notification deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/cleanup")
async def cleanup_expired_notifications(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean up expired notifications"""
    try:
        monitoring_service = ZoteroSyncMonitoringService(db)
        
        deleted_count = monitoring_service.cleanup_expired_notifications()
        
        return {
            "status": "success",
            "message": f"Cleaned up {deleted_count} expired notifications",
            "data": {
                "deleted_count": deleted_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up expired notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_sync_history(
    connection_id: str = Query(..., description="Zotero connection ID"),
    action_filter: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(50, description="Maximum number of history entries to return"),
    offset: int = Query(0, description="Number of history entries to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sync history from audit logs"""
    try:
        monitoring_service = ZoteroSyncMonitoringService(db)
        
        # Validate limit
        if limit > 100:
            limit = 100
        
        result = monitoring_service.get_sync_history(
            connection_id=connection_id,
            action_filter=action_filter,
            limit=limit,
            offset=offset
        )
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error getting sync history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_sync_statistics(
    connection_id: str = Query(..., description="Zotero connection ID"),
    days: int = Query(30, description="Number of days to include in statistics"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sync statistics for a connection"""
    try:
        monitoring_service = ZoteroSyncMonitoringService(db)
        
        # Validate days parameter
        if days < 1 or days > 365:
            raise HTTPException(
                status_code=400,
                detail="Days parameter must be between 1 and 365"
            )
        
        result = monitoring_service.get_sync_statistics(
            connection_id=connection_id,
            days=days
        )
        
        return {
            "status": "success",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sync statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/errors")
async def get_error_summary(
    connection_id: str = Query(..., description="Zotero connection ID"),
    days: int = Query(7, description="Number of days to include in error summary"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get error summary for troubleshooting"""
    try:
        monitoring_service = ZoteroSyncMonitoringService(db)
        
        # Validate days parameter
        if days < 1 or days > 90:
            raise HTTPException(
                status_code=400,
                detail="Days parameter must be between 1 and 90"
            )
        
        result = monitoring_service.get_error_summary(
            connection_id=connection_id,
            days=days
        )
        
        return {
            "status": "success",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting error summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/progress")
async def create_progress_notification(
    connection_id: str = Query(..., description="Zotero connection ID"),
    job_id: str = Query(..., description="Sync job ID"),
    progress_percentage: int = Query(..., description="Progress percentage"),
    items_processed: int = Query(..., description="Number of items processed"),
    total_items: int = Query(..., description="Total number of items"),
    current_operation: str = Query(..., description="Current operation description"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update a progress notification"""
    try:
        monitoring_service = ZoteroSyncMonitoringService(db)
        
        # Validate progress percentage
        if progress_percentage < 0 or progress_percentage > 100:
            raise HTTPException(
                status_code=400,
                detail="Progress percentage must be between 0 and 100"
            )
        
        # Validate items counts
        if items_processed < 0 or total_items < 0 or items_processed > total_items:
            raise HTTPException(
                status_code=400,
                detail="Invalid items processed/total counts"
            )
        
        notification_id = monitoring_service.create_progress_notification(
            connection_id=connection_id,
            job_id=job_id,
            progress_percentage=progress_percentage,
            items_processed=items_processed,
            total_items=total_items,
            current_operation=current_operation
        )
        
        return {
            "status": "success",
            "message": "Progress notification created/updated successfully",
            "data": {
                "notification_id": notification_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating progress notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_sync_dashboard(
    connection_id: str = Query(..., description="Zotero connection ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive sync dashboard data"""
    try:
        monitoring_service = ZoteroSyncMonitoringService(db)
        
        # Get recent notifications
        notifications = monitoring_service.get_sync_notifications(
            connection_id=connection_id,
            limit=10
        )
        
        # Get statistics for last 30 days
        statistics = monitoring_service.get_sync_statistics(
            connection_id=connection_id,
            days=30
        )
        
        # Get error summary for last 7 days
        error_summary = monitoring_service.get_error_summary(
            connection_id=connection_id,
            days=7
        )
        
        # Get recent history
        history = monitoring_service.get_sync_history(
            connection_id=connection_id,
            limit=20
        )
        
        return {
            "status": "success",
            "data": {
                "notifications": notifications,
                "statistics": statistics,
                "error_summary": error_summary,
                "recent_history": history
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting sync dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/error")
async def create_error_notification(
    connection_id: str = Query(..., description="Zotero connection ID"),
    job_id: str = Query(..., description="Sync job ID"),
    error_message: str = Query(..., description="Error message"),
    error_details: Optional[Dict[str, Any]] = None,
    retry_count: int = Query(0, description="Number of retries attempted"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create an error notification for sync failures"""
    try:
        monitoring_service = ZoteroSyncMonitoringService(db)
        
        notification_id = monitoring_service.create_error_notification(
            connection_id=connection_id,
            job_id=job_id,
            error_message=error_message,
            error_details=error_details,
            retry_count=retry_count
        )
        
        return {
            "status": "success",
            "message": "Error notification created successfully",
            "data": {
                "notification_id": notification_id
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating error notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/completion")
async def create_completion_notification(
    connection_id: str = Query(..., description="Zotero connection ID"),
    job_id: str = Query(..., description="Sync job ID"),
    items_processed: int = Query(..., description="Number of items processed"),
    items_added: int = Query(0, description="Number of items added"),
    items_updated: int = Query(0, description="Number of items updated"),
    items_deleted: int = Query(0, description="Number of items deleted"),
    sync_duration: float = Query(..., description="Sync duration in seconds"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a completion notification for successful syncs"""
    try:
        monitoring_service = ZoteroSyncMonitoringService(db)
        
        notification_id = monitoring_service.create_completion_notification(
            connection_id=connection_id,
            job_id=job_id,
            items_processed=items_processed,
            items_added=items_added,
            items_updated=items_updated,
            items_deleted=items_deleted,
            sync_duration=sync_duration
        )
        
        return {
            "status": "success",
            "message": "Completion notification created successfully",
            "data": {
                "notification_id": notification_id
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating completion notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/warning")
async def create_warning_notification(
    connection_id: str = Query(..., description="Zotero connection ID"),
    job_id: str = Query(..., description="Sync job ID"),
    warning_message: str = Query(..., description="Warning message"),
    warning_details: Optional[Dict[str, Any]] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a warning notification for sync issues"""
    try:
        monitoring_service = ZoteroSyncMonitoringService(db)
        
        notification_id = monitoring_service.create_warning_notification(
            connection_id=connection_id,
            job_id=job_id,
            warning_message=warning_message,
            warning_details=warning_details
        )
        
        return {
            "status": "success",
            "message": "Warning notification created successfully",
            "data": {
                "notification_id": notification_id
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating warning notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit")
async def log_sync_audit_event(
    connection_id: str = Query(..., description="Zotero connection ID"),
    action: str = Query(..., description="Action performed"),
    sync_job_id: Optional[str] = Query(None, description="Sync job ID"),
    target_type: Optional[str] = Query(None, description="Target type"),
    target_id: Optional[str] = Query(None, description="Target ID"),
    old_data: Optional[Dict[str, Any]] = None,
    new_data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log a sync audit event"""
    try:
        monitoring_service = ZoteroSyncMonitoringService(db)
        
        # Extract user info from current_user
        user_id = current_user.get('id')
        
        audit_id = monitoring_service.log_sync_audit_event(
            connection_id=connection_id,
            sync_job_id=sync_job_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            old_data=old_data,
            new_data=new_data,
            user_id=user_id,
            metadata=metadata
        )
        
        return {
            "status": "success",
            "message": "Audit event logged successfully",
            "data": {
                "audit_id": audit_id
            }
        }
        
    except Exception as e:
        logger.error(f"Error logging audit event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/realtime")
async def get_real_time_sync_status(
    connection_id: str = Query(..., description="Zotero connection ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time sync status for a connection"""
    try:
        monitoring_service = ZoteroSyncMonitoringService(db)
        
        result = monitoring_service.get_real_time_sync_status(connection_id)
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error getting real-time sync status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))