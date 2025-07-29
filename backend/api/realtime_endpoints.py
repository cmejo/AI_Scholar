"""
Real-time Intelligence API Endpoints
Provides WebSocket and HTTP endpoints for real-time features including
live document processing, smart notifications, and streaming analytics.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from core.auth import get_current_user, User
from services.realtime_intelligence import (
    RealTimeIntelligenceService, NotificationType, StreamType,
    SmartNotification, LiveProcessingJob, RealTimeEvent
)

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Pydantic models
class NotificationRequest(BaseModel):
    notification_type: NotificationType
    title: str
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=3, ge=1, le=5)
    action_url: Optional[str] = None
    expires_in_hours: int = Field(default=24, ge=1, le=168)

class ProcessingRequest(BaseModel):
    document_id: str
    file_path: str
    quality: str = "balanced"

class SubscriptionRequest(BaseModel):
    stream_types: List[StreamType]

class NotificationResponse(BaseModel):
    id: str
    notification_type: NotificationType
    title: str
    message: str
    data: Dict[str, Any]
    priority: int
    created_at: datetime
    read: bool
    action_url: Optional[str]
    expires_at: Optional[datetime]

class ProcessingJobResponse(BaseModel):
    id: str
    document_id: str
    status: str
    progress: float
    started_at: datetime
    estimated_completion: Optional[datetime]
    current_stage: str
    stages_completed: List[str]
    error_message: Optional[str]

class RealTimeMetricsResponse(BaseModel):
    active_connections: int
    pending_notifications: int
    active_processing_jobs: int
    subscriptions: List[str]
    analytics_stream_active: bool

# Router setup
router = APIRouter(prefix="/api/v1/realtime", tags=["Real-time Intelligence"])

# Global service instance (would be properly injected in production)
realtime_service: Optional[RealTimeIntelligenceService] = None

def get_realtime_service(db: Session = Depends(get_db)) -> RealTimeIntelligenceService:
    """Get real-time intelligence service instance"""
    global realtime_service
    if realtime_service is None:
        realtime_service = RealTimeIntelligenceService(db)
    return realtime_service

# WebSocket endpoint for real-time connections
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    stream_types: str = Query(default="notifications,document_processing,analytics_updates"),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time communication"""
    try:
        await websocket.accept()
        
        # Parse stream types
        subscriptions = []
        for stream_type in stream_types.split(","):
            try:
                subscriptions.append(StreamType(stream_type.strip()))
            except ValueError:
                logger.warning(f"Invalid stream type: {stream_type}")
        
        # Connect user to real-time service
        service = get_realtime_service(db)
        success = await service.connect_user(user_id, websocket, subscriptions)
        
        if not success:
            await websocket.close(code=1000, reason="Failed to connect to real-time service")
            return
        
        try:
            # Keep connection alive and handle incoming messages
            while True:
                try:
                    # Wait for messages from client
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Handle different message types
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}))
                    
                    elif message.get("type") == "subscribe":
                        # Update subscriptions
                        new_streams = message.get("streams", [])
                        for stream in new_streams:
                            try:
                                service.user_subscriptions[user_id].add(StreamType(stream))
                            except ValueError:
                                logger.warning(f"Invalid stream type in subscription: {stream}")
                    
                    elif message.get("type") == "unsubscribe":
                        # Remove subscriptions
                        remove_streams = message.get("streams", [])
                        for stream in remove_streams:
                            try:
                                service.user_subscriptions[user_id].discard(StreamType(stream))
                            except ValueError:
                                logger.warning(f"Invalid stream type in unsubscription: {stream}")
                    
                    elif message.get("type") == "mark_notification_read":
                        # Mark notification as read
                        notification_id = message.get("notification_id")
                        if notification_id:
                            await service.mark_notification_read(user_id, notification_id)
                    
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from user {user_id}")
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {str(e)}")
                
        except WebSocketDisconnect:
            logger.info(f"User {user_id} disconnected from WebSocket")
        
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
    
    finally:
        # Clean up connection
        if realtime_service:
            await realtime_service.disconnect_user(user_id)

# HTTP endpoints
@router.post("/notifications", response_model=NotificationResponse)
async def create_notification(
    request: NotificationRequest,
    current_user: User = Depends(get_current_user),
    service: RealTimeIntelligenceService = Depends(get_realtime_service)
):
    """Create a smart notification"""
    try:
        notification = await service.create_smart_notification(
            user_id=str(current_user.id),
            notification_type=request.notification_type,
            title=request.title,
            message=request.message,
            data=request.data,
            priority=request.priority,
            action_url=request.action_url,
            expires_in_hours=request.expires_in_hours
        )
        
        return NotificationResponse(
            id=notification.id,
            notification_type=notification.notification_type,
            title=notification.title,
            message=notification.message,
            data=notification.data,
            priority=notification.priority,
            created_at=notification.created_at,
            read=notification.read,
            action_url=notification.action_url,
            expires_at=notification.expires_at
        )
        
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create notification")

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: RealTimeIntelligenceService = Depends(get_realtime_service)
):
    """Get user notifications"""
    try:
        notifications = await service.get_user_notifications(str(current_user.id), limit)
        
        return [
            NotificationResponse(
                id=n.id,
                notification_type=n.notification_type,
                title=n.title,
                message=n.message,
                data=n.data,
                priority=n.priority,
                created_at=n.created_at,
                read=n.read,
                action_url=n.action_url,
                expires_at=n.expires_at
            )
            for n in notifications
        ]
        
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get notifications")

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    service: RealTimeIntelligenceService = Depends(get_realtime_service)
):
    """Mark notification as read"""
    try:
        success = await service.mark_notification_read(str(current_user.id), notification_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"status": "success", "message": "Notification marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")

@router.post("/processing/start", response_model=Dict[str, str])
async def start_live_processing(
    request: ProcessingRequest,
    current_user: User = Depends(get_current_user),
    service: RealTimeIntelligenceService = Depends(get_realtime_service)
):
    """Start live document processing"""
    try:
        job_id = await service.process_document_live(
            user_id=str(current_user.id),
            document_id=request.document_id,
            file_path=request.file_path,
            quality=request.quality
        )
        
        return {"job_id": job_id, "status": "started"}
        
    except Exception as e:
        logger.error(f"Error starting live processing: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start live processing")

@router.get("/processing/{job_id}", response_model=ProcessingJobResponse)
async def get_processing_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    service: RealTimeIntelligenceService = Depends(get_realtime_service)
):
    """Get processing job status"""
    try:
        job = await service.get_processing_job_status(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Processing job not found")
        
        # Verify user owns this job
        if job.user_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return ProcessingJobResponse(
            id=job.id,
            document_id=job.document_id,
            status=job.status,
            progress=job.progress,
            started_at=job.started_at,
            estimated_completion=job.estimated_completion,
            current_stage=job.current_stage,
            stages_completed=job.stages_completed,
            error_message=job.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting processing status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get processing status")

@router.delete("/processing/{job_id}")
async def cancel_processing(
    job_id: str,
    current_user: User = Depends(get_current_user),
    service: RealTimeIntelligenceService = Depends(get_realtime_service)
):
    """Cancel processing job"""
    try:
        # First verify the job exists and user owns it
        job = await service.get_processing_job_status(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Processing job not found")
        
        if job.user_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        success = await service.cancel_processing_job(job_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to cancel job")
        
        return {"status": "success", "message": "Processing job cancelled"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling processing: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel processing")

@router.post("/subscriptions")
async def update_subscriptions(
    request: SubscriptionRequest,
    current_user: User = Depends(get_current_user),
    service: RealTimeIntelligenceService = Depends(get_realtime_service)
):
    """Update user's real-time subscriptions"""
    try:
        user_id = str(current_user.id)
        
        # Update subscriptions
        service.user_subscriptions[user_id] = set(request.stream_types)
        
        return {
            "status": "success",
            "subscriptions": [stream.value for stream in request.stream_types]
        }
        
    except Exception as e:
        logger.error(f"Error updating subscriptions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update subscriptions")

@router.get("/metrics", response_model=RealTimeMetricsResponse)
async def get_real_time_metrics(
    current_user: User = Depends(get_current_user),
    service: RealTimeIntelligenceService = Depends(get_realtime_service)
):
    """Get real-time metrics for current user"""
    try:
        metrics = await service.get_real_time_metrics(str(current_user.id))
        
        return RealTimeMetricsResponse(
            active_connections=metrics.get("active_connections", 0),
            pending_notifications=metrics.get("pending_notifications", 0),
            active_processing_jobs=metrics.get("active_processing_jobs", 0),
            subscriptions=metrics.get("subscriptions", []),
            analytics_stream_active=metrics.get("analytics_stream_active", False)
        )
        
    except Exception as e:
        logger.error(f"Error getting real-time metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get real-time metrics")

@router.post("/analytics/stream")
async def stream_analytics_update(
    metric_type: str,
    metric_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    service: RealTimeIntelligenceService = Depends(get_realtime_service)
):
    """Stream analytics update"""
    try:
        await service.stream_analytics_updates(
            user_id=str(current_user.id),
            metric_type=metric_type,
            metric_data=metric_data
        )
        
        return {"status": "success", "message": "Analytics update streamed"}
        
    except Exception as e:
        logger.error(f"Error streaming analytics update: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stream analytics update")

@router.post("/knowledge-graph/update")
async def update_knowledge_graph_live(
    entity_updates: List[Dict[str, Any]] = None,
    relationship_updates: List[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    service: RealTimeIntelligenceService = Depends(get_realtime_service)
):
    """Update knowledge graph with live notifications"""
    try:
        await service.update_knowledge_graph_live(
            user_id=str(current_user.id),
            entity_updates=entity_updates or [],
            relationship_updates=relationship_updates or []
        )
        
        return {"status": "success", "message": "Knowledge graph updated"}
        
    except Exception as e:
        logger.error(f"Error updating knowledge graph: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update knowledge graph")

@router.get("/status")
async def get_service_status(
    current_user: User = Depends(get_current_user),
    service: RealTimeIntelligenceService = Depends(get_realtime_service)
):
    """Get real-time service status"""
    try:
        status = service.get_service_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting service status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get service status")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "real-time intelligence",
        "timestamp": datetime.utcnow().isoformat()
    }