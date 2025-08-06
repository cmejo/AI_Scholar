"""
Push notification service for mobile and web clients
Handles real-time notifications with delivery optimization
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp

from core.redis_client import redis_client

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    URGENT = "urgent"

class NotificationChannel(Enum):
    WEB_PUSH = "web_push"
    MOBILE_PUSH = "mobile_push"
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"

@dataclass
class NotificationPreferences:
    user_id: str
    channels: Dict[str, bool]  # channel -> enabled
    quiet_hours: Optional[Dict[str, str]] = None  # start_time, end_time
    frequency_limits: Optional[Dict[str, int]] = None  # notification_type -> max_per_hour
    categories: Optional[Dict[str, bool]] = None  # category -> enabled

@dataclass
class PushSubscription:
    user_id: str
    endpoint: str
    p256dh_key: str
    auth_key: str
    user_agent: str
    created_at: datetime
    is_active: bool = True

@dataclass
class Notification:
    id: str
    user_id: str
    title: str
    body: str
    type: NotificationType
    category: str
    data: Optional[Dict[str, Any]] = None
    channels: List[NotificationChannel] = None
    priority: int = 1  # 1=high, 2=medium, 3=low
    expires_at: Optional[datetime] = None
    created_at: datetime = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    status: str = "pending"  # pending, delivered, failed, expired

@dataclass
class NotificationDelivery:
    id: str
    notification_id: str
    channel: NotificationChannel
    status: str  # pending, delivered, failed
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    error_message: Optional[str] = None

class PushNotificationService:
    def __init__(self):
        self.redis_prefix = "notifications:"
        self.subscription_prefix = "push_subscriptions:"
        self.preferences_prefix = "notification_preferences:"
        self.delivery_prefix = "notification_deliveries:"
        self.max_retry_attempts = 3
        self.default_ttl = 86400  # 24 hours
        
        # VAPID keys for web push (should be from config)
        self.vapid_public_key = "your-vapid-public-key"
        self.vapid_private_key = "your-vapid-private-key"
        self.vapid_email = "mailto:your-email@example.com"
        
        # Delivery optimization settings
        self.batch_size = 20
        self.batch_timeout = 10  # seconds
        self.priority_queue_enabled = True
        self.adaptive_scheduling_enabled = True
        
        # Rate limiting settings
        self.rate_limit_window = 3600  # 1 hour
        self.default_rate_limits = {
            NotificationType.URGENT.value: 10,
            NotificationType.ERROR.value: 5,
            NotificationType.WARNING.value: 15,
            NotificationType.SUCCESS.value: 20,
            NotificationType.INFO.value: 30
        }
        
        # Delivery channels priority
        self.channel_priority = {
            NotificationChannel.MOBILE_PUSH.value: 1,
            NotificationChannel.WEB_PUSH.value: 2,
            NotificationChannel.IN_APP.value: 3,
            NotificationChannel.EMAIL.value: 4,
            NotificationChannel.SMS.value: 5
        }
        
        # Enhanced notification categories for requirements 1.6 and 2.6
        self.collaboration_categories = [
            "collaboration", "document_sharing", "real_time_editing", 
            "comments", "invitations", "team_updates"
        ]
        
        self.voice_shortcut_categories = [
            "voice_commands", "voice_navigation", "voice_feedback",
            "quick_actions", "accessibility"
        ]
        
        # Mobile-specific notification settings
        self.mobile_notification_settings = {
            "collaboration_priority": 1,  # High priority for collaboration updates
            "voice_feedback_priority": 2,  # Medium-high priority for voice feedback
            "batch_collaboration_updates": True,  # Batch multiple collaboration updates
            "voice_shortcut_confirmations": True  # Send confirmations for voice shortcuts
        }
        
    async def health_check(self) -> Dict[str, Any]:
        """Health check for push notification service"""
        try:
            # Check Redis connection
            await redis_client.ping()
            
            # Count active subscriptions
            subscription_keys = await redis_client.keys(f"{self.subscription_prefix}*")
            active_subscriptions = 0
            
            for key in subscription_keys:
                sub_data = await redis_client.get(key)
                if sub_data:
                    if isinstance(sub_data, str):
                        sub_dict = json.loads(sub_data)
                    else:
                        sub_dict = sub_data
                    if sub_dict.get("is_active", False):
                        active_subscriptions += 1
            
            # Count pending notifications
            pending_notifications = await redis_client.llen(f"{self.redis_prefix}queue")
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "total_subscriptions": len(subscription_keys),
                "active_subscriptions": active_subscriptions,
                "pending_notifications": pending_notifications,
                "supported_channels": [channel.value for channel in NotificationChannel]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def subscribe_push(
        self,
        user_id: str,
        endpoint: str,
        p256dh_key: str,
        auth_key: str,
        user_agent: str
    ) -> bool:
        """Subscribe user to push notifications"""
        try:
            subscription = PushSubscription(
                user_id=user_id,
                endpoint=endpoint,
                p256dh_key=p256dh_key,
                auth_key=auth_key,
                user_agent=user_agent,
                created_at=datetime.now()
            )
            
            # Store subscription
            subscription_id = f"{user_id}_{hash(endpoint)}"
            await redis_client.set(
                f"{self.subscription_prefix}{subscription_id}",
                json.dumps(asdict(subscription), default=str)
            )
            
            # Add to user's subscriptions
            await redis_client.sadd(f"{self.subscription_prefix}user:{user_id}", subscription_id)
            
            logger.info(f"Push subscription created for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Push subscription failed: {e}")
            return False

    async def unsubscribe_push(self, user_id: str, endpoint: str) -> bool:
        """Unsubscribe user from push notifications"""
        try:
            subscription_id = f"{user_id}_{hash(endpoint)}"
            
            # Remove subscription
            await redis_client.delete(f"{self.subscription_prefix}{subscription_id}")
            
            # Remove from user's subscriptions
            await redis_client.srem(f"{self.subscription_prefix}user:{user_id}", subscription_id)
            
            logger.info(f"Push subscription removed for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Push unsubscription failed: {e}")
            return False

    async def set_notification_preferences(
        self,
        user_id: str,
        preferences: NotificationPreferences
    ) -> bool:
        """Set user notification preferences"""
        try:
            await redis_client.set(
                f"{self.preferences_prefix}{user_id}",
                json.dumps(asdict(preferences), default=str)
            )
            
            logger.info(f"Notification preferences updated for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set notification preferences: {e}")
            return False

    async def get_notification_preferences(self, user_id: str) -> NotificationPreferences:
        """Get user notification preferences"""
        try:
            prefs_data = await redis_client.get(f"{self.preferences_prefix}{user_id}")
            
            if prefs_data:
                # Handle both dict and string data
                if isinstance(prefs_data, dict):
                    prefs_dict = prefs_data
                else:
                    prefs_dict = json.loads(prefs_data)
                return NotificationPreferences(**prefs_dict)
            else:
                # Return default preferences
                return NotificationPreferences(
                    user_id=user_id,
                    channels={
                        NotificationChannel.WEB_PUSH.value: True,
                        NotificationChannel.MOBILE_PUSH.value: True,
                        NotificationChannel.IN_APP.value: True,
                        NotificationChannel.EMAIL.value: False,
                        NotificationChannel.SMS.value: False
                    },
                    categories={
                        "system": True,
                        "research": True,
                        "collaboration": True,
                        "learning": True,
                        "compliance": True
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to get notification preferences: {e}")
            return NotificationPreferences(
                user_id=user_id, 
                channels={
                    NotificationChannel.WEB_PUSH.value: True,
                    NotificationChannel.MOBILE_PUSH.value: True,
                    NotificationChannel.IN_APP.value: True,
                    NotificationChannel.EMAIL.value: False,
                    NotificationChannel.SMS.value: False
                },
                categories={
                    "system": True,
                    "research": True,
                    "collaboration": True,
                    "learning": True,
                    "compliance": True
                }
            )

    async def send_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        notification_type: NotificationType = NotificationType.INFO,
        category: str = "general",
        data: Optional[Dict[str, Any]] = None,
        channels: Optional[List[NotificationChannel]] = None,
        priority: int = 2,
        expires_in_hours: int = 24
    ) -> str:
        """Send notification to user"""
        try:
            # Generate notification ID
            notification_id = f"notif_{datetime.now().timestamp()}_{user_id}"
            
            # Create notification
            notification = Notification(
                id=notification_id,
                user_id=user_id,
                title=title,
                body=body,
                type=notification_type,
                category=category,
                data=data or {},
                channels=channels or [NotificationChannel.WEB_PUSH, NotificationChannel.IN_APP],
                priority=priority,
                expires_at=datetime.now() + timedelta(hours=expires_in_hours),
                created_at=datetime.now()
            )
            
            # Check user preferences
            preferences = await self.get_notification_preferences(user_id)
            
            # Filter channels based on preferences
            enabled_channels = []
            for channel in notification.channels:
                if preferences.channels.get(channel.value, False):
                    enabled_channels.append(channel)
            
            # Check category preferences
            if not preferences.categories.get(category, True):
                logger.info(f"Notification {notification_id} skipped due to category preferences")
                return notification_id
            
            # Check quiet hours
            if await self._is_quiet_hours(preferences):
                # Delay notification or skip based on priority
                if priority == 1:  # High priority, send anyway
                    pass
                else:
                    logger.info(f"Notification {notification_id} delayed due to quiet hours")
                    # Could implement delayed delivery here
                    return notification_id
            
            # Check frequency limits
            if await self._exceeds_frequency_limit(user_id, notification_type, preferences):
                logger.info(f"Notification {notification_id} skipped due to frequency limits")
                return notification_id
            
            notification.channels = enabled_channels
            
            # Store notification
            await redis_client.setex(
                f"{self.redis_prefix}{notification_id}",
                self.default_ttl,
                json.dumps(asdict(notification), default=str)
            )
            
            # Add to user's notifications
            await redis_client.lpush(f"{self.redis_prefix}user:{user_id}", notification_id)
            await redis_client.ltrim(f"{self.redis_prefix}user:{user_id}", 0, 99)  # Keep last 100
            
            # Queue for delivery based on priority
            if priority == 1:  # High priority - use priority queue
                await redis_client.lpush(
                    f"{self.redis_prefix}priority_queue",
                    json.dumps(asdict(notification), default=str)
                )
            elif self.adaptive_scheduling_enabled and len(enabled_channels) > 1:
                # Use batch queue for multi-channel notifications
                await redis_client.lpush(
                    f"{self.redis_prefix}batch_queue",
                    json.dumps(asdict(notification), default=str)
                )
            else:
                # Use regular queue
                await redis_client.lpush(
                    f"{self.redis_prefix}queue",
                    json.dumps(asdict(notification), default=str)
                )
            
            logger.info(f"Notification {notification_id} queued for delivery")
            return notification_id
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            raise Exception(f"Failed to send notification: {str(e)}")

    async def process_notifications(self):
        """Process notification delivery queue"""
        try:
            while True:
                # Get next notification from queue
                notification_data = await redis_client.brpop(f"{self.redis_prefix}queue", timeout=1)
                
                if not notification_data:
                    continue
                
                notification_dict = json.loads(notification_data[1])
                notification = Notification(**notification_dict)
                
                # Check if notification is expired
                if notification.expires_at and datetime.now() > notification.expires_at:
                    notification.status = "expired"
                    await self._update_notification_status(notification)
                    continue
                
                # Process delivery for each channel
                for channel in notification.channels:
                    await self._deliver_notification(notification, channel)
                
        except Exception as e:
            logger.error(f"Notification processing failed: {e}")

    async def _deliver_notification(self, notification: Notification, channel: NotificationChannel):
        """Deliver notification through specific channel"""
        try:
            delivery_id = f"delivery_{notification.id}_{channel.value}"
            delivery = NotificationDelivery(
                id=delivery_id,
                notification_id=notification.id,
                channel=channel,
                status="pending"
            )
            
            success = False
            
            if channel == NotificationChannel.WEB_PUSH:
                success = await self._send_web_push(notification)
            elif channel == NotificationChannel.MOBILE_PUSH:
                success = await self._send_mobile_push(notification)
            elif channel == NotificationChannel.IN_APP:
                success = await self._send_in_app_notification(notification)
            elif channel == NotificationChannel.EMAIL:
                success = await self._send_email_notification(notification)
            elif channel == NotificationChannel.SMS:
                success = await self._send_sms_notification(notification)
            
            delivery.status = "delivered" if success else "failed"
            delivery.last_attempt = datetime.now()
            delivery.attempts = 1
            
            # Store delivery record
            await redis_client.setex(
                f"{self.delivery_prefix}{delivery_id}",
                86400,  # Keep for 24 hours
                json.dumps(asdict(delivery), default=str)
            )
            
            if success:
                notification.delivered_at = datetime.now()
                notification.status = "delivered"
                await self._update_notification_status(notification)
                
                logger.info(f"Notification {notification.id} delivered via {channel.value}")
            else:
                logger.warning(f"Notification {notification.id} failed to deliver via {channel.value}")
                
        except Exception as e:
            logger.error(f"Notification delivery failed: {e}")

    async def _send_web_push(self, notification: Notification) -> bool:
        """Send web push notification"""
        try:
            # Get user's push subscriptions
            subscription_ids = await redis_client.smembers(f"{self.subscription_prefix}user:{notification.user_id}")
            
            if not subscription_ids:
                return False
            
            success_count = 0
            
            for subscription_id in subscription_ids:
                sub_data = await redis_client.get(f"{self.subscription_prefix}{subscription_id}")
                if not sub_data:
                    continue
                
                sub_dict = json.loads(sub_data)
                subscription = PushSubscription(**sub_dict)
                
                if not subscription.is_active:
                    continue
                
                # Prepare push payload
                payload = {
                    "title": notification.title,
                    "body": notification.body,
                    "icon": "/icon-192x192.png",
                    "badge": "/badge-72x72.png",
                    "data": {
                        "notification_id": notification.id,
                        "type": notification.type.value,
                        "category": notification.category,
                        **notification.data
                    },
                    "actions": [
                        {"action": "view", "title": "View"},
                        {"action": "dismiss", "title": "Dismiss"}
                    ]
                }
                
                # Send push notification (simplified - would use pywebpush in production)
                try:
                    # This is a placeholder - actual implementation would use pywebpush
                    # from pywebpush import webpush
                    # webpush(
                    #     subscription_info={
                    #         "endpoint": subscription.endpoint,
                    #         "keys": {
                    #             "p256dh": subscription.p256dh_key,
                    #             "auth": subscription.auth_key
                    #         }
                    #     },
                    #     data=json.dumps(payload),
                    #     vapid_private_key=self.vapid_private_key,
                    #     vapid_claims={"sub": self.vapid_email}
                    # )
                    
                    success_count += 1
                    
                except Exception as push_error:
                    logger.error(f"Web push failed for subscription {subscription_id}: {push_error}")
                    
                    # Deactivate subscription if endpoint is invalid
                    if "invalid" in str(push_error).lower():
                        subscription.is_active = False
                        await redis_client.set(
                            f"{self.subscription_prefix}{subscription_id}",
                            json.dumps(asdict(subscription), default=str)
                        )
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Web push notification failed: {e}")
            return False

    async def _send_mobile_push(self, notification: Notification) -> bool:
        """Send mobile push notification (FCM/APNS)"""
        try:
            # This would integrate with Firebase Cloud Messaging or Apple Push Notification Service
            # Placeholder implementation
            
            payload = {
                "title": notification.title,
                "body": notification.body,
                "data": notification.data
            }
            
            # Would send to FCM/APNS here
            logger.info(f"Mobile push sent: {payload}")
            return True
            
        except Exception as e:
            logger.error(f"Mobile push notification failed: {e}")
            return False

    async def _send_in_app_notification(self, notification: Notification) -> bool:
        """Send in-app notification"""
        try:
            # Store in-app notification
            await redis_client.lpush(
                f"{self.redis_prefix}in_app:{notification.user_id}",
                json.dumps(asdict(notification), default=str)
            )
            await redis_client.ltrim(f"{self.redis_prefix}in_app:{notification.user_id}", 0, 49)  # Keep last 50
            
            # Publish to WebSocket if user is connected
            await redis_client.publish(
                f"user_notifications:{notification.user_id}",
                json.dumps(asdict(notification), default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"In-app notification failed: {e}")
            return False

    async def _send_email_notification(self, notification: Notification) -> bool:
        """Send email notification"""
        try:
            # This would integrate with email service (SendGrid, SES, etc.)
            # Placeholder implementation
            
            logger.info(f"Email notification sent to user {notification.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return False

    async def _send_sms_notification(self, notification: Notification) -> bool:
        """Send SMS notification"""
        try:
            # This would integrate with SMS service (Twilio, etc.)
            # Placeholder implementation
            
            logger.info(f"SMS notification sent to user {notification.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"SMS notification failed: {e}")
            return False

    async def get_user_notifications(
        self,
        user_id: str,
        limit: int = 20,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get user's notifications"""
        try:
            notification_ids = await redis_client.lrange(f"{self.redis_prefix}user:{user_id}", 0, limit - 1)
            notifications = []
            
            for notification_id in notification_ids:
                notification_data = await redis_client.get(f"{self.redis_prefix}{notification_id}")
                if notification_data:
                    notification_dict = json.loads(notification_data)
                    
                    if unread_only and notification_dict.get("read_at"):
                        continue
                    
                    notifications.append(notification_dict)
            
            return notifications
            
        except Exception as e:
            logger.error(f"Failed to get user notifications: {e}")
            return []

    async def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark notification as read"""
        try:
            notification_data = await redis_client.get(f"{self.redis_prefix}{notification_id}")
            if not notification_data:
                return False
            
            notification_dict = json.loads(notification_data)
            
            # Check ownership
            if notification_dict.get("user_id") != user_id:
                return False
            
            # Mark as read
            notification_dict["read_at"] = datetime.now().isoformat()
            
            await redis_client.setex(
                f"{self.redis_prefix}{notification_id}",
                self.default_ttl,
                json.dumps(notification_dict, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return False

    async def _update_notification_status(self, notification: Notification):
        """Update notification status"""
        try:
            await redis_client.setex(
                f"{self.redis_prefix}{notification.id}",
                self.default_ttl,
                json.dumps(asdict(notification), default=str)
            )
        except Exception as e:
            logger.error(f"Failed to update notification status: {e}")

    async def _is_quiet_hours(self, preferences: NotificationPreferences) -> bool:
        """Check if current time is within user's quiet hours"""
        try:
            if not preferences.quiet_hours:
                return False
            
            # Implementation would check current time against quiet hours
            # Placeholder
            return False
            
        except Exception as e:
            logger.error(f"Failed to check quiet hours: {e}")
            return False

    async def _exceeds_frequency_limit(
        self,
        user_id: str,
        notification_type: NotificationType,
        preferences: NotificationPreferences
    ) -> bool:
        """Check if notification exceeds frequency limits"""
        try:
            if not preferences.frequency_limits:
                return False
            
            limit = preferences.frequency_limits.get(notification_type.value)
            if not limit:
                return False
            
            # Count notifications of this type in the last hour
            # Implementation would check Redis for recent notifications
            # Placeholder
            return False
            
        except Exception as e:
            logger.error(f"Failed to check frequency limits: {e}")
            return False

    async def send_collaboration_notification(
        self,
        user_id: str,
        collaboration_type: str,
        title: str,
        body: str,
        collaboration_data: Dict[str, Any],
        collaborators: List[str] = None,
        priority: int = 1
    ) -> str:
        """Send collaboration notification for requirement 1.6 - mobile push notifications for collaboration updates"""
        try:
            # Enhanced data for collaboration notifications
            enhanced_data = {
                "collaboration_type": collaboration_type,
                "collaborators": collaborators or [],
                "document_id": collaboration_data.get("document_id"),
                "action_url": collaboration_data.get("action_url"),
                "initiated_by": collaboration_data.get("initiated_by"),
                "timestamp": datetime.now().isoformat(),
                **collaboration_data
            }
            
            # Send notification with high priority for mobile devices
            notification_id = await self.send_notification(
                user_id=user_id,
                title=title,
                body=body,
                notification_type=NotificationType.INFO if collaboration_type != "urgent" else NotificationType.URGENT,
                category="collaboration",
                data=enhanced_data,
                channels=[NotificationChannel.MOBILE_PUSH, NotificationChannel.WEB_PUSH, NotificationChannel.IN_APP],
                priority=priority,
                expires_in_hours=48  # Collaboration updates are important for longer
            )
            
            # Send to all collaborators if specified
            if collaborators:
                for collaborator_id in collaborators:
                    if collaborator_id != user_id:
                        await self.send_notification(
                            user_id=collaborator_id,
                            title=f"Collaboration Update: {title}",
                            body=body,
                            notification_type=NotificationType.INFO,
                            category="collaboration",
                            data={
                                **enhanced_data,
                                "collaboration_role": "participant",
                                "initiated_by": user_id
                            },
                            channels=[NotificationChannel.MOBILE_PUSH, NotificationChannel.WEB_PUSH],
                            priority=priority
                        )
            
            logger.info(f"Collaboration notification sent: {collaboration_type} for user {user_id}")
            return notification_id
            
        except Exception as e:
            logger.error(f"Collaboration notification failed: {e}")
            raise Exception(f"Failed to send collaboration notification: {str(e)}")

    async def send_voice_shortcut_feedback(
        self,
        user_id: str,
        shortcut_type: str,
        command: str,
        success: bool,
        feedback_data: Dict[str, Any]
    ) -> str:
        """Send voice shortcut feedback notification for requirement 2.6 - voice shortcuts for quick access"""
        try:
            title = f"Voice Command {'Executed' if success else 'Failed'}"
            body = f"'{command}' - {feedback_data.get('message', 'Command processed')}"
            
            notification_data = {
                "shortcut_type": shortcut_type,
                "command": command,
                "success": success,
                "execution_time": feedback_data.get("execution_time", 0),
                "confidence_score": feedback_data.get("confidence_score", 0),
                "suggested_alternatives": feedback_data.get("alternatives", []),
                "voice_feedback_audio": feedback_data.get("audio_response_url"),
                **feedback_data
            }
            
            # Use appropriate notification type based on success
            notification_type = NotificationType.SUCCESS if success else NotificationType.WARNING
            
            # Send notification with voice-specific settings
            notification_id = await self.send_notification(
                user_id=user_id,
                title=title,
                body=body,
                notification_type=notification_type,
                category="voice_commands",
                data=notification_data,
                channels=[NotificationChannel.IN_APP, NotificationChannel.WEB_PUSH],  # Avoid mobile push for voice feedback
                priority=2,  # Medium priority
                expires_in_hours=1  # Voice feedback is short-lived
            )
            
            logger.info(f"Voice shortcut feedback sent: {shortcut_type} for user {user_id}")
            return notification_id
            
        except Exception as e:
            logger.error(f"Voice shortcut feedback failed: {e}")
            raise Exception(f"Failed to send voice shortcut feedback: {str(e)}")

    async def send_mobile_sync_notification(
        self,
        user_id: str,
        sync_type: str,
        sync_status: str,
        sync_data: Dict[str, Any]
    ) -> str:
        """Send mobile sync notification for requirement 1.6 - mobile data synchronization"""
        try:
            if sync_status == "completed":
                title = "Mobile Sync Complete"
                body = f"Your {sync_type} data has been synchronized successfully"
                notification_type = NotificationType.SUCCESS
            elif sync_status == "failed":
                title = "Mobile Sync Failed"
                body = f"Failed to sync {sync_type} data. Please try again."
                notification_type = NotificationType.ERROR
            else:
                title = "Mobile Sync In Progress"
                body = f"Synchronizing {sync_type} data..."
                notification_type = NotificationType.INFO
            
            notification_data = {
                "sync_type": sync_type,
                "sync_status": sync_status,
                "device_id": sync_data.get("device_id"),
                "sync_timestamp": datetime.now().isoformat(),
                "items_synced": sync_data.get("items_synced", 0),
                "conflicts_resolved": sync_data.get("conflicts_resolved", 0),
                "error_details": sync_data.get("error_details"),
                **sync_data
            }
            
            # Send notification primarily to mobile devices
            notification_id = await self.send_notification(
                user_id=user_id,
                title=title,
                body=body,
                notification_type=notification_type,
                category="mobile_sync",
                data=notification_data,
                channels=[NotificationChannel.MOBILE_PUSH, NotificationChannel.IN_APP],
                priority=2 if sync_status != "failed" else 1,  # High priority for failures
                expires_in_hours=6
            )
            
            logger.info(f"Mobile sync notification sent: {sync_type} - {sync_status} for user {user_id}")
            return notification_id
            
        except Exception as e:
            logger.error(f"Mobile sync notification failed: {e}")
            raise Exception(f"Failed to send mobile sync notification: {str(e)}")

    async def start_background_tasks(self):
        """Start background tasks for processing notifications"""
        try:
            # Start notification processor
            asyncio.create_task(self.process_notifications())
            
            # Start priority queue processor
            asyncio.create_task(self.process_priority_notifications())
            
            # Start batch processor
            asyncio.create_task(self.process_batch_notifications())
            
            # Start delivery optimizer
            asyncio.create_task(self.optimize_delivery_schedules())
            
            # Start cleanup task
            asyncio.create_task(self.cleanup_expired_notifications())
            
            # Start collaboration notification processor
            asyncio.create_task(self.process_collaboration_notifications())
            
            # Start voice shortcut feedback processor
            asyncio.create_task(self.process_voice_shortcut_notifications())
            
            logger.info("Push notification background tasks started")
            
        except Exception as e:
            logger.error(f"Failed to start push notification background tasks: {e}")

    async def process_collaboration_notifications(self):
        """Process collaboration-specific notifications with enhanced delivery"""
        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe("collaboration_events")
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        collaboration_event = json.loads(message['data'])
                        await self._handle_collaboration_event(collaboration_event)
                    except Exception as e:
                        logger.error(f"Failed to handle collaboration event: {e}")
                        
        except Exception as e:
            logger.error(f"Collaboration notification processor failed: {e}")

    async def process_voice_shortcut_notifications(self):
        """Process voice shortcut feedback notifications"""
        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe("voice_shortcuts_events")
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        voice_event = json.loads(message['data'])
                        await self._handle_voice_shortcut_event(voice_event)
                    except Exception as e:
                        logger.error(f"Failed to handle voice shortcut event: {e}")
                        
        except Exception as e:
            logger.error(f"Voice shortcut notification processor failed: {e}")

    async def _handle_collaboration_event(self, event_data: Dict[str, Any]):
        """Handle collaboration events and send appropriate notifications"""
        try:
            event_type = event_data.get("event_type", "")
            user_id = event_data.get("user_id", "")
            collaborators = event_data.get("collaborators", [])
            data = event_data.get("data", {})
            
            if "collaboration." in event_type:
                if event_type == "collaboration.invite_sent":
                    await self.send_collaboration_notification(
                        user_id=user_id,
                        collaboration_type="invitation",
                        title="Collaboration Invitation Sent",
                        body=f"You invited others to collaborate on {data.get('document_name', 'a document')}",
                        collaboration_data=data,
                        collaborators=collaborators
                    )
                elif event_type == "collaboration.document_updated":
                    await self.send_collaboration_notification(
                        user_id=user_id,
                        collaboration_type="update",
                        title="Document Updated",
                        body=f"{data.get('updated_by', 'Someone')} updated the shared document",
                        collaboration_data=data,
                        collaborators=collaborators
                    )
                elif event_type == "collaboration.real_time_edit":
                    # Send less intrusive notification for real-time edits
                    await self.send_notification(
                        user_id=user_id,
                        title="Live Collaboration",
                        body="Real-time edits are happening in your shared document",
                        notification_type=NotificationType.INFO,
                        category="collaboration",
                        data=data,
                        channels=[NotificationChannel.IN_APP],  # Only in-app for real-time
                        priority=3,  # Low priority
                        expires_in_hours=1
                    )
                    
        except Exception as e:
            logger.error(f"Collaboration event handling failed: {e}")

    async def _handle_voice_shortcut_event(self, event_data: Dict[str, Any]):
        """Handle voice shortcut events and send feedback notifications"""
        try:
            shortcut_type = event_data.get("shortcut_type", "")
            user_id = event_data.get("user_id", "")
            voice_data = event_data.get("voice_data", {})
            
            # Send feedback notification for voice shortcuts
            await self.send_voice_shortcut_feedback(
                user_id=user_id,
                shortcut_type=shortcut_type,
                command=voice_data.get("command", ""),
                success=voice_data.get("success", True),
                feedback_data={
                    "message": voice_data.get("feedback_message", "Command executed successfully"),
                    "execution_time": voice_data.get("processing_time", 0),
                    "confidence_score": voice_data.get("confidence", 0),
                    "alternatives": voice_data.get("suggested_alternatives", [])
                }
            )
                    
        except Exception as e:
            logger.error(f"Voice shortcut event handling failed: {e}")

    async def process_priority_notifications(self):
        """Process high-priority notifications with faster delivery"""
        try:
            while True:
                # Get high-priority notification from queue
                notification_data = await redis_client.brpop(
                    f"{self.redis_prefix}priority_queue", 
                    timeout=1
                )
                
                if not notification_data:
                    continue
                
                notification_dict = json.loads(notification_data[1])
                notification = Notification(**notification_dict)
                
                # Process immediately without batching
                for channel in notification.channels:
                    await self._deliver_notification(notification, channel)
                    
        except Exception as e:
            logger.error(f"Priority notification processing failed: {e}")

    async def process_batch_notifications(self):
        """Process notifications in batches for efficiency"""
        try:
            batch = []
            last_batch_time = datetime.now()
            
            while True:
                try:
                    # Get notification from batch queue
                    notification_data = await redis_client.brpop(
                        f"{self.redis_prefix}batch_queue", 
                        timeout=1
                    )
                    
                    if notification_data:
                        notification_dict = json.loads(notification_data[1])
                        batch.append(notification_dict)
                    
                    # Process batch if conditions are met
                    current_time = datetime.now()
                    time_since_last_batch = (current_time - last_batch_time).total_seconds()
                    
                    if (len(batch) >= self.batch_size or 
                        (batch and time_since_last_batch >= self.batch_timeout)):
                        
                        await self._process_notification_batch(batch)
                        batch = []
                        last_batch_time = current_time
                        
                except Exception as e:
                    logger.error(f"Batch notification processing error: {e}")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Batch notification processor failed: {e}")

    async def _process_notification_batch(self, batch: List[Dict[str, Any]]):
        """Process a batch of notifications concurrently"""
        try:
            # Group notifications by channel for optimization
            channel_groups = {}
            
            for notification_dict in batch:
                notification = Notification(**notification_dict)
                
                for channel in notification.channels:
                    if channel not in channel_groups:
                        channel_groups[channel] = []
                    channel_groups[channel].append(notification)
            
            # Process each channel group concurrently
            tasks = []
            for channel, notifications in channel_groups.items():
                tasks.append(self._deliver_batch_to_channel(notifications, channel))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info(f"Processed batch of {len(batch)} notifications")
            
        except Exception as e:
            logger.error(f"Batch notification processing failed: {e}")

    async def _deliver_batch_to_channel(
        self, 
        notifications: List[Notification], 
        channel: NotificationChannel
    ):
        """Deliver a batch of notifications to a specific channel"""
        try:
            if channel == NotificationChannel.WEB_PUSH:
                await self._send_batch_web_push(notifications)
            elif channel == NotificationChannel.MOBILE_PUSH:
                await self._send_batch_mobile_push(notifications)
            elif channel == NotificationChannel.IN_APP:
                await self._send_batch_in_app_notifications(notifications)
            elif channel == NotificationChannel.EMAIL:
                await self._send_batch_email_notifications(notifications)
            else:
                # Fallback to individual delivery
                for notification in notifications:
                    await self._deliver_notification(notification, channel)
                    
        except Exception as e:
            logger.error(f"Batch delivery to {channel.value} failed: {e}")

    async def _send_batch_web_push(self, notifications: List[Notification]):
        """Send batch of web push notifications"""
        try:
            # Group by user for efficiency
            user_notifications = {}
            for notification in notifications:
                if notification.user_id not in user_notifications:
                    user_notifications[notification.user_id] = []
                user_notifications[notification.user_id].append(notification)
            
            # Send to each user
            for user_id, user_notifs in user_notifications.items():
                subscription_ids = await redis_client.smembers(
                    f"{self.subscription_prefix}user:{user_id}"
                )
                
                for subscription_id in subscription_ids:
                    sub_data = await redis_client.get(f"{self.subscription_prefix}{subscription_id}")
                    if sub_data:
                        sub_dict = json.loads(sub_data)
                        subscription = PushSubscription(**sub_dict)
                        
                        if subscription.is_active:
                            # Send consolidated notification or multiple
                            if len(user_notifs) == 1:
                                await self._send_single_web_push(user_notifs[0], subscription)
                            else:
                                await self._send_consolidated_web_push(user_notifs, subscription)
                                
        except Exception as e:
            logger.error(f"Batch web push failed: {e}")

    async def _send_consolidated_web_push(
        self, 
        notifications: List[Notification], 
        subscription: PushSubscription
    ):
        """Send consolidated web push notification"""
        try:
            # Create consolidated payload
            total_count = len(notifications)
            urgent_count = sum(1 for n in notifications if n.type == NotificationType.URGENT)
            
            if urgent_count > 0:
                title = f"{urgent_count} urgent notification{'s' if urgent_count != 1 else ''}"
                body = f"You have {total_count} new notifications, {urgent_count} urgent"
            else:
                title = f"{total_count} new notifications"
                body = "Click to view your notifications"
            
            payload = {
                "title": title,
                "body": body,
                "icon": "/icon-192x192.png",
                "badge": "/badge-72x72.png",
                "data": {
                    "type": "consolidated",
                    "count": total_count,
                    "urgent_count": urgent_count,
                    "notification_ids": [n.id for n in notifications]
                },
                "actions": [
                    {"action": "view_all", "title": "View All"},
                    {"action": "dismiss", "title": "Dismiss"}
                ]
            }
            
            # Send consolidated push (placeholder implementation)
            logger.info(f"Consolidated web push sent: {payload}")
            
        except Exception as e:
            logger.error(f"Consolidated web push failed: {e}")

    async def _send_single_web_push(
        self, 
        notification: Notification, 
        subscription: PushSubscription
    ):
        """Send single web push notification"""
        try:
            payload = {
                "title": notification.title,
                "body": notification.body,
                "icon": "/icon-192x192.png",
                "badge": "/badge-72x72.png",
                "data": {
                    "notification_id": notification.id,
                    "type": notification.type.value,
                    "category": notification.category,
                    **notification.data
                }
            }
            
            # Send push (placeholder implementation)
            logger.info(f"Single web push sent: {payload}")
            
        except Exception as e:
            logger.error(f"Single web push failed: {e}")

    async def _send_batch_mobile_push(self, notifications: List[Notification]):
        """Send batch of mobile push notifications"""
        try:
            # Group by user and send batch to FCM/APNS
            user_notifications = {}
            for notification in notifications:
                if notification.user_id not in user_notifications:
                    user_notifications[notification.user_id] = []
                user_notifications[notification.user_id].append(notification)
            
            # Send batch to each user
            for user_id, user_notifs in user_notifications.items():
                # This would integrate with FCM/APNS batch API
                logger.info(f"Batch mobile push sent to user {user_id}: {len(user_notifs)} notifications")
                
        except Exception as e:
            logger.error(f"Batch mobile push failed: {e}")

    async def _send_batch_in_app_notifications(self, notifications: List[Notification]):
        """Send batch of in-app notifications"""
        try:
            # Group by user
            user_notifications = {}
            for notification in notifications:
                if notification.user_id not in user_notifications:
                    user_notifications[notification.user_id] = []
                user_notifications[notification.user_id].append(notification)
            
            # Store and publish for each user
            for user_id, user_notifs in user_notifications.items():
                # Store all notifications
                for notification in user_notifs:
                    await redis_client.lpush(
                        f"{self.redis_prefix}in_app:{user_id}",
                        json.dumps(asdict(notification), default=str)
                    )
                
                await redis_client.ltrim(f"{self.redis_prefix}in_app:{user_id}", 0, 49)
                
                # Publish batch update
                batch_data = {
                    "type": "batch_notifications",
                    "count": len(user_notifs),
                    "notifications": [asdict(n) for n in user_notifs]
                }
                
                await redis_client.publish(
                    f"user_notifications:{user_id}",
                    json.dumps(batch_data, default=str)
                )
                
        except Exception as e:
            logger.error(f"Batch in-app notifications failed: {e}")

    async def _send_batch_email_notifications(self, notifications: List[Notification]):
        """Send batch of email notifications"""
        try:
            # Group by user and send digest email
            user_notifications = {}
            for notification in notifications:
                if notification.user_id not in user_notifications:
                    user_notifications[notification.user_id] = []
                user_notifications[notification.user_id].append(notification)
            
            # Send digest email to each user
            for user_id, user_notifs in user_notifications.items():
                # This would create and send a digest email
                logger.info(f"Digest email sent to user {user_id}: {len(user_notifs)} notifications")
                
        except Exception as e:
            logger.error(f"Batch email notifications failed: {e}")

    async def optimize_delivery_schedules(self):
        """Optimize notification delivery schedules based on user behavior"""
        try:
            while True:
                # Get all users with notification preferences
                preference_keys = await redis_client.keys(f"{self.preferences_prefix}*")
                
                for key in preference_keys:
                    user_id = key.split(":")[-1]
                    await self._optimize_user_delivery_schedule(user_id)
                
                # Run optimization every hour
                await asyncio.sleep(3600)
                
        except Exception as e:
            logger.error(f"Delivery schedule optimization failed: {e}")

    async def _optimize_user_delivery_schedule(self, user_id: str):
        """Optimize delivery schedule for a specific user"""
        try:
            # Get user's notification interaction history
            interaction_key = f"{self.redis_prefix}interactions:{user_id}"
            interaction_data = await redis_client.get(interaction_key)
            
            if not interaction_data:
                return
            
            interactions = json.loads(interaction_data)
            
            # Analyze optimal delivery times
            optimal_times = self._analyze_optimal_delivery_times(interactions)
            
            # Update user preferences with optimal times
            preferences = await self.get_notification_preferences(user_id)
            if not preferences.quiet_hours:
                preferences.quiet_hours = {}
            
            preferences.quiet_hours["optimal_times"] = optimal_times
            
            await self.set_notification_preferences(user_id, preferences)
            
            logger.info(f"Optimized delivery schedule for user {user_id}")
            
        except Exception as e:
            logger.error(f"User delivery optimization failed: {e}")

    def _analyze_optimal_delivery_times(self, interactions: List[Dict[str, Any]]) -> List[str]:
        """Analyze user interactions to find optimal delivery times"""
        try:
            # Simple analysis - find hours with highest engagement
            hour_engagement = {}
            
            for interaction in interactions:
                timestamp = datetime.fromisoformat(interaction.get("timestamp", ""))
                hour = timestamp.hour
                
                if hour not in hour_engagement:
                    hour_engagement[hour] = 0
                
                # Weight by interaction type
                if interaction.get("type") == "read":
                    hour_engagement[hour] += 2
                elif interaction.get("type") == "click":
                    hour_engagement[hour] += 3
                else:
                    hour_engagement[hour] += 1
            
            # Get top 3 hours
            sorted_hours = sorted(hour_engagement.items(), key=lambda x: x[1], reverse=True)
            optimal_hours = [str(hour) for hour, _ in sorted_hours[:3]]
            
            return optimal_hours
            
        except Exception as e:
            logger.error(f"Optimal time analysis failed: {e}")
            return []

    async def cleanup_expired_notifications(self):
        """Clean up expired notifications and delivery records"""
        try:
            while True:
                # Clean up expired notifications
                notification_keys = await redis_client.keys(f"{self.redis_prefix}*")
                
                for key in notification_keys:
                    if "user:" in key or "in_app:" in key:
                        continue
                        
                    notification_data = await redis_client.get(key)
                    if notification_data:
                        try:
                            notification_dict = json.loads(notification_data)
                            expires_at = notification_dict.get("expires_at")
                            
                            if expires_at:
                                expire_time = datetime.fromisoformat(expires_at)
                                if datetime.now() > expire_time:
                                    await redis_client.delete(key)
                                    
                        except Exception:
                            continue
                
                # Clean up old delivery records
                delivery_keys = await redis_client.keys(f"{self.delivery_prefix}records:*")
                cutoff_time = datetime.now() - timedelta(days=7)
                
                for key in delivery_keys:
                    delivery_data = await redis_client.get(key)
                    if delivery_data:
                        try:
                            delivery_dict = json.loads(delivery_data)
                            last_attempt = delivery_dict.get("last_attempt")
                            
                            if last_attempt:
                                attempt_time = datetime.fromisoformat(last_attempt)
                                if attempt_time < cutoff_time:
                                    await redis_client.delete(key)
                                    
                        except Exception:
                            continue
                
                # Run cleanup every 6 hours
                await asyncio.sleep(21600)
                
        except Exception as e:
            logger.error(f"Notification cleanup failed: {e}")

    async def get_delivery_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get delivery analytics for a user"""
        try:
            # Get delivery statistics
            delivery_keys = await redis_client.keys(f"{self.delivery_prefix}records:*")
            
            total_deliveries = 0
            successful_deliveries = 0
            failed_deliveries = 0
            channel_stats = {}
            
            for key in delivery_keys:
                delivery_data = await redis_client.get(key)
                if delivery_data:
                    delivery_dict = json.loads(delivery_data)
                    
                    # Check if delivery belongs to user
                    notification_id = delivery_dict.get("notification_id")
                    if notification_id:
                        notification_data = await redis_client.get(f"{self.redis_prefix}{notification_id}")
                        if notification_data:
                            notification_dict = json.loads(notification_data)
                            if notification_dict.get("user_id") == user_id:
                                total_deliveries += 1
                                
                                channel = delivery_dict.get("channel")
                                if channel not in channel_stats:
                                    channel_stats[channel] = {"total": 0, "successful": 0, "failed": 0}
                                
                                channel_stats[channel]["total"] += 1
                                
                                if delivery_dict.get("status") == "delivered":
                                    successful_deliveries += 1
                                    channel_stats[channel]["successful"] += 1
                                elif delivery_dict.get("status") == "failed":
                                    failed_deliveries += 1
                                    channel_stats[channel]["failed"] += 1
            
            success_rate = (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0
            
            return {
                "total_deliveries": total_deliveries,
                "successful_deliveries": successful_deliveries,
                "failed_deliveries": failed_deliveries,
                "success_rate": round(success_rate, 2),
                "channel_statistics": channel_stats,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get delivery analytics: {e}")
            return {}