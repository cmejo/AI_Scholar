"""
Webhook and notification endpoints
Provides API for managing webhooks and push notifications
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from services.webhook_service import WebhookService, WEBHOOK_EVENTS
from services.push_notification_service import (
    PushNotificationService, 
    NotificationType, 
    NotificationChannel,
    NotificationPreferences
)
from services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/webhooks-notifications", tags=["webhooks-notifications"])

# Initialize services
webhook_service = WebhookService()
push_service = PushNotificationService()
auth_service = AuthService()

# Security
security = HTTPBearer()

# Pydantic models
class WebhookRegistration(BaseModel):
    url: str
    events: List[str]
    secret: Optional[str] = None

class WebhookUpdate(BaseModel):
    url: Optional[str] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None

class EventEmission(BaseModel):
    event_type: str
    data: Dict[str, Any]
    source: str = "api"
    metadata: Optional[Dict[str, Any]] = None

class PushSubscriptionRequest(BaseModel):
    endpoint: str
    p256dh_key: str
    auth_key: str
    user_agent: str

class NotificationRequest(BaseModel):
    title: str
    body: str
    type: str = "info"
    category: str = "general"
    data: Optional[Dict[str, Any]] = None
    channels: Optional[List[str]] = None
    priority: int = 2
    expires_in_hours: int = 24

class NotificationPreferencesRequest(BaseModel):
    channels: Dict[str, bool]
    quiet_hours: Optional[Dict[str, str]] = None
    frequency_limits: Optional[Dict[str, int]] = None
    categories: Optional[Dict[str, bool]] = None

class CollaborationEventRequest(BaseModel):
    collaboration_type: str
    title: str
    body: str
    collaboration_data: Dict[str, Any]
    collaborators: Optional[List[str]] = None
    priority: int = 1

class VoiceShortcutEventRequest(BaseModel):
    shortcut_type: str
    command: str
    voice_data: Dict[str, Any]

class MobileSyncEventRequest(BaseModel):
    sync_type: str
    sync_status: str
    sync_data: Dict[str, Any]

class APIResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        user = await auth_service.verify_token(credentials.credentials)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Webhook Endpoints

@router.post("/webhooks", response_model=APIResponse)
async def register_webhook(
    request: WebhookRegistration,
    user = Depends(get_current_user)
):
    """Register a new webhook endpoint"""
    try:
        # Validate events
        invalid_events = set(request.events) - set(WEBHOOK_EVENTS.keys())
        if invalid_events:
            return APIResponse(
                success=False,
                error=f"Invalid events: {invalid_events}"
            )
        
        webhook = await webhook_service.register_webhook(
            user_id=user.id,
            url=request.url,
            events=request.events,
            secret=request.secret
        )
        
        return APIResponse(
            success=True,
            data={
                "webhook_id": webhook.id,
                "url": webhook.url,
                "events": webhook.events,
                "secret": webhook.secret,
                "created_at": webhook.created_at.isoformat(),
                "warning": "Store the webhook secret securely for signature verification."
            }
        )
    except Exception as e:
        logger.error(f"Webhook registration failed: {e}")
        return APIResponse(
            success=False,
            error=f"Webhook registration failed: {str(e)}"
        )

@router.get("/webhooks", response_model=APIResponse)
async def list_webhooks(user = Depends(get_current_user)):
    """List user's webhooks"""
    try:
        webhooks = await webhook_service.get_user_webhooks(user.id)
        
        return APIResponse(
            success=True,
            data={
                "webhooks": webhooks,
                "total": len(webhooks)
            }
        )
    except Exception as e:
        logger.error(f"Webhook listing failed: {e}")
        return APIResponse(
            success=False,
            error=f"Failed to list webhooks: {str(e)}"
        )

@router.get("/webhooks/{webhook_id}/deliveries", response_model=APIResponse)
async def get_webhook_deliveries(
    webhook_id: str,
    limit: int = 50,
    user = Depends(get_current_user)
):
    """Get webhook delivery history"""
    try:
        # Verify webhook ownership
        webhooks = await webhook_service.get_user_webhooks(user.id)
        webhook_ids = [w["id"] for w in webhooks]
        
        if webhook_id not in webhook_ids:
            return APIResponse(
                success=False,
                error="Webhook not found or access denied"
            )
        
        deliveries = await webhook_service.get_webhook_deliveries(webhook_id, limit)
        
        return APIResponse(
            success=True,
            data={
                "webhook_id": webhook_id,
                "deliveries": deliveries,
                "total": len(deliveries)
            }
        )
    except Exception as e:
        logger.error(f"Failed to get webhook deliveries: {e}")
        return APIResponse(
            success=False,
            error=f"Failed to get webhook deliveries: {str(e)}"
        )

@router.delete("/webhooks/{webhook_id}", response_model=APIResponse)
async def unregister_webhook(
    webhook_id: str,
    user = Depends(get_current_user)
):
    """Unregister a webhook"""
    try:
        success = await webhook_service.unregister_webhook(webhook_id, user.id)
        
        if success:
            return APIResponse(
                success=True,
                data={"message": "Webhook unregistered successfully"}
            )
        else:
            return APIResponse(
                success=False,
                error="Webhook not found or access denied"
            )
    except Exception as e:
        logger.error(f"Webhook unregistration failed: {e}")
        return APIResponse(
            success=False,
            error=f"Webhook unregistration failed: {str(e)}"
        )

@router.post("/webhooks/test-event", response_model=APIResponse)
async def emit_test_event(
    request: EventEmission,
    user = Depends(get_current_user)
):
    """Emit a test event to trigger webhooks"""
    try:
        if request.event_type not in WEBHOOK_EVENTS:
            return APIResponse(
                success=False,
                error=f"Invalid event type. Available events: {list(WEBHOOK_EVENTS.keys())}"
            )
        
        event_id = await webhook_service.emit_event(
            event_type=request.event_type,
            data=request.data,
            user_id=user.id,
            source=request.source,
            metadata=request.metadata
        )
        
        return APIResponse(
            success=True,
            data={
                "event_id": event_id,
                "event_type": request.event_type,
                "message": "Event emitted successfully"
            }
        )
    except Exception as e:
        logger.error(f"Event emission failed: {e}")
        return APIResponse(
            success=False,
            error=f"Event emission failed: {str(e)}"
        )

@router.get("/webhooks/events", response_model=APIResponse)
async def list_webhook_events():
    """List available webhook events"""
    try:
        return APIResponse(
            success=True,
            data={
                "events": WEBHOOK_EVENTS,
                "total": len(WEBHOOK_EVENTS)
            }
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Failed to list events: {str(e)}"
        )

# Push Notification Endpoints

@router.post("/push/subscribe", response_model=APIResponse)
async def subscribe_push_notifications(
    request: PushSubscriptionRequest,
    user = Depends(get_current_user)
):
    """Subscribe to push notifications"""
    try:
        success = await push_service.subscribe_push(
            user_id=user.id,
            endpoint=request.endpoint,
            p256dh_key=request.p256dh_key,
            auth_key=request.auth_key,
            user_agent=request.user_agent
        )
        
        if success:
            return APIResponse(
                success=True,
                data={"message": "Push subscription created successfully"}
            )
        else:
            return APIResponse(
                success=False,
                error="Failed to create push subscription"
            )
    except Exception as e:
        logger.error(f"Push subscription failed: {e}")
        return APIResponse(
            success=False,
            error=f"Push subscription failed: {str(e)}"
        )

@router.delete("/push/unsubscribe", response_model=APIResponse)
async def unsubscribe_push_notifications(
    endpoint: str,
    user = Depends(get_current_user)
):
    """Unsubscribe from push notifications"""
    try:
        success = await push_service.unsubscribe_push(user.id, endpoint)
        
        if success:
            return APIResponse(
                success=True,
                data={"message": "Push subscription removed successfully"}
            )
        else:
            return APIResponse(
                success=False,
                error="Failed to remove push subscription"
            )
    except Exception as e:
        logger.error(f"Push unsubscription failed: {e}")
        return APIResponse(
            success=False,
            error=f"Push unsubscription failed: {str(e)}"
        )

@router.post("/notifications/send", response_model=APIResponse)
async def send_notification(
    request: NotificationRequest,
    user = Depends(get_current_user)
):
    """Send a notification to the user"""
    try:
        # Convert string type to enum
        try:
            notification_type = NotificationType(request.type)
        except ValueError:
            return APIResponse(
                success=False,
                error=f"Invalid notification type. Available types: {[t.value for t in NotificationType]}"
            )
        
        # Convert string channels to enums
        channels = []
        if request.channels:
            for channel_str in request.channels:
                try:
                    channels.append(NotificationChannel(channel_str))
                except ValueError:
                    return APIResponse(
                        success=False,
                        error=f"Invalid channel: {channel_str}. Available channels: {[c.value for c in NotificationChannel]}"
                    )
        
        notification_id = await push_service.send_notification(
            user_id=user.id,
            title=request.title,
            body=request.body,
            notification_type=notification_type,
            category=request.category,
            data=request.data,
            channels=channels,
            priority=request.priority,
            expires_in_hours=request.expires_in_hours
        )
        
        return APIResponse(
            success=True,
            data={
                "notification_id": notification_id,
                "message": "Notification sent successfully"
            }
        )
    except Exception as e:
        logger.error(f"Notification sending failed: {e}")
        return APIResponse(
            success=False,
            error=f"Notification sending failed: {str(e)}"
        )

@router.get("/notifications", response_model=APIResponse)
async def get_notifications(
    limit: int = 20,
    unread_only: bool = False,
    user = Depends(get_current_user)
):
    """Get user's notifications"""
    try:
        notifications = await push_service.get_user_notifications(
            user_id=user.id,
            limit=limit,
            unread_only=unread_only
        )
        
        return APIResponse(
            success=True,
            data={
                "notifications": notifications,
                "total": len(notifications),
                "unread_only": unread_only
            }
        )
    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        return APIResponse(
            success=False,
            error=f"Failed to get notifications: {str(e)}"
        )

@router.post("/notifications/{notification_id}/read", response_model=APIResponse)
async def mark_notification_read(
    notification_id: str,
    user = Depends(get_current_user)
):
    """Mark notification as read"""
    try:
        success = await push_service.mark_notification_read(notification_id, user.id)
        
        if success:
            return APIResponse(
                success=True,
                data={"message": "Notification marked as read"}
            )
        else:
            return APIResponse(
                success=False,
                error="Notification not found or access denied"
            )
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}")
        return APIResponse(
            success=False,
            error=f"Failed to mark notification as read: {str(e)}"
        )

@router.get("/notifications/preferences", response_model=APIResponse)
async def get_notification_preferences(user = Depends(get_current_user)):
    """Get user's notification preferences"""
    try:
        preferences = await push_service.get_notification_preferences(user.id)
        
        return APIResponse(
            success=True,
            data={
                "preferences": {
                    "user_id": preferences.user_id,
                    "channels": preferences.channels,
                    "quiet_hours": preferences.quiet_hours,
                    "frequency_limits": preferences.frequency_limits,
                    "categories": preferences.categories
                }
            }
        )
    except Exception as e:
        logger.error(f"Failed to get notification preferences: {e}")
        return APIResponse(
            success=False,
            error=f"Failed to get notification preferences: {str(e)}"
        )

@router.put("/notifications/preferences", response_model=APIResponse)
async def update_notification_preferences(
    request: NotificationPreferencesRequest,
    user = Depends(get_current_user)
):
    """Update user's notification preferences"""
    try:
        preferences = NotificationPreferences(
            user_id=user.id,
            channels=request.channels,
            quiet_hours=request.quiet_hours,
            frequency_limits=request.frequency_limits,
            categories=request.categories
        )
        
        success = await push_service.set_notification_preferences(user.id, preferences)
        
        if success:
            return APIResponse(
                success=True,
                data={"message": "Notification preferences updated successfully"}
            )
        else:
            return APIResponse(
                success=False,
                error="Failed to update notification preferences"
            )
    except Exception as e:
        logger.error(f"Failed to update notification preferences: {e}")
        return APIResponse(
            success=False,
            error=f"Failed to update notification preferences: {str(e)}"
        )

# Health check endpoint
@router.get("/health", response_model=APIResponse)
async def health_check():
    """Health check for webhook and notification services"""
    try:
        webhook_health = await webhook_service.health_check()
        push_health = await push_service.health_check()
        
        overall_status = "healthy" if (
            webhook_health.get("status") == "healthy" and 
            push_health.get("status") == "healthy"
        ) else "unhealthy"
        
        return APIResponse(
            success=True,
            data={
                "status": overall_status,
                "webhook_service": webhook_health,
                "push_notification_service": push_health,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return APIResponse(
            success=False,
            error=f"Health check failed: {str(e)}"
        )

# Background task to start services
@router.on_event("startup")
async def startup_event():
    """Start background tasks for webhook and notification processing"""
    try:
        await webhook_service.start_background_tasks()
        await push_service.start_background_tasks()
        logger.info("Webhook and notification background tasks started")
    except Exception as e:
        logger.error(f"Failed to start background tasks: {e}")

# Enhanced endpoints for collaboration and voice shortcuts

@router.post("/collaboration/notify", response_model=APIResponse)
async def send_collaboration_notification(
    request: CollaborationEventRequest,
    user = Depends(get_current_user)
):
    """Send collaboration notification for requirement 1.6 - mobile push notifications for collaboration updates"""
    try:
        # Emit collaboration event
        event_id = await webhook_service.emit_collaboration_event(
            event_type=f"collaboration.{request.collaboration_type}",
            user_id=user.id,
            collaboration_data=request.collaboration_data,
            collaborators=request.collaborators
        )
        
        # Send collaboration notification
        notification_id = await push_service.send_collaboration_notification(
            user_id=user.id,
            collaboration_type=request.collaboration_type,
            title=request.title,
            body=request.body,
            collaboration_data=request.collaboration_data,
            collaborators=request.collaborators,
            priority=request.priority
        )
        
        return APIResponse(
            success=True,
            data={
                "event_id": event_id,
                "notification_id": notification_id,
                "collaboration_type": request.collaboration_type,
                "collaborators_notified": len(request.collaborators or []),
                "message": "Collaboration notification sent successfully"
            }
        )
    except Exception as e:
        logger.error(f"Collaboration notification failed: {e}")
        return APIResponse(
            success=False,
            error=f"Collaboration notification failed: {str(e)}"
        )

@router.post("/voice/shortcut-feedback", response_model=APIResponse)
async def send_voice_shortcut_feedback(
    request: VoiceShortcutEventRequest,
    user = Depends(get_current_user)
):
    """Send voice shortcut feedback for requirement 2.6 - voice shortcuts for quick access"""
    try:
        # Emit voice shortcut event
        event_id = await webhook_service.emit_voice_shortcut_event(
            shortcut_type=request.shortcut_type,
            user_id=user.id,
            voice_data=request.voice_data
        )
        
        # Send voice shortcut feedback notification
        notification_id = await push_service.send_voice_shortcut_feedback(
            user_id=user.id,
            shortcut_type=request.shortcut_type,
            command=request.command,
            success=request.voice_data.get("success", True),
            feedback_data=request.voice_data
        )
        
        return APIResponse(
            success=True,
            data={
                "event_id": event_id,
                "notification_id": notification_id,
                "shortcut_type": request.shortcut_type,
                "command": request.command,
                "message": "Voice shortcut feedback sent successfully"
            }
        )
    except Exception as e:
        logger.error(f"Voice shortcut feedback failed: {e}")
        return APIResponse(
            success=False,
            error=f"Voice shortcut feedback failed: {str(e)}"
        )

@router.post("/mobile/sync-notification", response_model=APIResponse)
async def send_mobile_sync_notification(
    request: MobileSyncEventRequest,
    user = Depends(get_current_user)
):
    """Send mobile sync notification for requirement 1.6 - mobile data synchronization"""
    try:
        # Emit mobile sync event
        event_id = await webhook_service.emit_mobile_sync_event(
            sync_type=request.sync_type,
            user_id=user.id,
            mobile_data=request.sync_data
        )
        
        # Send mobile sync notification
        notification_id = await push_service.send_mobile_sync_notification(
            user_id=user.id,
            sync_type=request.sync_type,
            sync_status=request.sync_status,
            sync_data=request.sync_data
        )
        
        return APIResponse(
            success=True,
            data={
                "event_id": event_id,
                "notification_id": notification_id,
                "sync_type": request.sync_type,
                "sync_status": request.sync_status,
                "message": "Mobile sync notification sent successfully"
            }
        )
    except Exception as e:
        logger.error(f"Mobile sync notification failed: {e}")
        return APIResponse(
            success=False,
            error=f"Mobile sync notification failed: {str(e)}"
        )

@router.get("/events/collaboration", response_model=APIResponse)
async def list_collaboration_events():
    """List available collaboration events"""
    try:
        collaboration_events = {
            k: v for k, v in WEBHOOK_EVENTS.items() 
            if k.startswith("collaboration.")
        }
        
        return APIResponse(
            success=True,
            data={
                "collaboration_events": collaboration_events,
                "total": len(collaboration_events),
                "description": "Events that trigger collaboration notifications for mobile devices"
            }
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Failed to list collaboration events: {str(e)}"
        )

@router.get("/events/voice-shortcuts", response_model=APIResponse)
async def list_voice_shortcut_events():
    """List available voice shortcut events"""
    try:
        voice_events = {
            k: v for k, v in WEBHOOK_EVENTS.items() 
            if k.startswith("voice.")
        }
        
        return APIResponse(
            success=True,
            data={
                "voice_shortcut_events": voice_events,
                "total": len(voice_events),
                "description": "Events related to voice shortcuts for quick access to functions"
            }
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Failed to list voice shortcut events: {str(e)}"
        )

@router.get("/events/mobile", response_model=APIResponse)
async def list_mobile_events():
    """List available mobile-specific events"""
    try:
        mobile_events = {
            k: v for k, v in WEBHOOK_EVENTS.items() 
            if k.startswith("mobile.")
        }
        
        return APIResponse(
            success=True,
            data={
                "mobile_events": mobile_events,
                "total": len(mobile_events),
                "description": "Events related to mobile device functionality and synchronization"
            }
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Failed to list mobile events: {str(e)}"
        )

# WebSocket endpoint for real-time notifications (would be in separate file)
# This is a placeholder showing how real-time notifications could work
@router.websocket("/ws/notifications/{user_id}")
async def notification_websocket(websocket, user_id: str):
    """WebSocket endpoint for real-time notifications"""
    # This would be implemented with proper WebSocket handling
    # and Redis pub/sub for real-time notification delivery
    pass