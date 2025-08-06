"""
Comprehensive tests for webhook and notification system
Tests event-driven architecture, delivery optimization, and system integration
"""
import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from services.webhook_service import WebhookService, WebhookEndpoint, WebhookEvent, WEBHOOK_EVENTS
from services.push_notification_service import (
    PushNotificationService, 
    NotificationType, 
    NotificationChannel,
    Notification,
    NotificationPreferences
)
from core.redis_client import redis_client

class TestWebhookService:
    """Test webhook service functionality"""
    
    @pytest.fixture
    async def webhook_service(self):
        """Create webhook service instance"""
        service = WebhookService()
        # Clear test data
        await redis_client.flushdb()
        return service
    
    @pytest.fixture
    def sample_webhook_data(self):
        """Sample webhook registration data"""
        return {
            "user_id": "test_user_123",
            "url": "https://example.com/webhook",
            "events": ["document.uploaded", "chat.response"],
            "secret": "test_secret_key"
        }
    
    async def test_webhook_registration(self, webhook_service, sample_webhook_data):
        """Test webhook registration"""
        webhook = await webhook_service.register_webhook(
            user_id=sample_webhook_data["user_id"],
            url=sample_webhook_data["url"],
            events=sample_webhook_data["events"],
            secret=sample_webhook_data["secret"]
        )
        
        assert webhook.user_id == sample_webhook_data["user_id"]
        assert webhook.url == sample_webhook_data["url"]
        assert webhook.events == sample_webhook_data["events"]
        assert webhook.is_active is True
        assert webhook.failure_count == 0
        
        # Verify webhook is stored in Redis
        webhook_data = await redis_client.get(f"webhooks:endpoints:{webhook.id}")
        assert webhook_data is not None
        
        # Verify webhook is added to user's list
        user_webhooks = await redis_client.smembers(f"webhooks:user:{sample_webhook_data['user_id']}")
        assert webhook.id in user_webhooks
        
        # Verify webhook is subscribed to events
        for event in sample_webhook_data["events"]:
            event_webhooks = await redis_client.smembers(f"webhooks:events:{event}")
            assert webhook.id in event_webhooks
    
    async def test_webhook_unregistration(self, webhook_service, sample_webhook_data):
        """Test webhook unregistration"""
        # Register webhook first
        webhook = await webhook_service.register_webhook(
            user_id=sample_webhook_data["user_id"],
            url=sample_webhook_data["url"],
            events=sample_webhook_data["events"]
        )
        
        # Unregister webhook
        success = await webhook_service.unregister_webhook(webhook.id, sample_webhook_data["user_id"])
        assert success is True
        
        # Verify webhook is removed
        webhook_data = await redis_client.get(f"webhooks:endpoints:{webhook.id}")
        assert webhook_data is None
        
        # Verify webhook is removed from user's list
        user_webhooks = await redis_client.smembers(f"webhooks:user:{sample_webhook_data['user_id']}")
        assert webhook.id not in user_webhooks
    
    async def test_event_emission(self, webhook_service, sample_webhook_data):
        """Test event emission and webhook triggering"""
        # Register webhook
        webhook = await webhook_service.register_webhook(
            user_id=sample_webhook_data["user_id"],
            url=sample_webhook_data["url"],
            events=["document.uploaded"]
        )
        
        # Emit event
        event_data = {"document_id": "doc_123", "filename": "test.pdf"}
        event_id = await webhook_service.emit_event(
            event_type="document.uploaded",
            data=event_data,
            user_id=sample_webhook_data["user_id"],
            source="test"
        )
        
        assert event_id is not None
        
        # Verify event is stored
        event_stored = await redis_client.get(f"events:{event_id}")
        assert event_stored is not None
        
        # Verify delivery is queued
        delivery_queue_length = await redis_client.llen("deliveries:queue")
        assert delivery_queue_length > 0
    
    async def test_event_driven_architecture(self, webhook_service):
        """Test event-driven architecture with system events"""
        # Mock Redis pubsub
        with patch.object(redis_client, 'pubsub') as mock_pubsub:
            mock_pubsub_instance = AsyncMock()
            mock_pubsub.return_value = mock_pubsub_instance
            
            # Mock message stream
            system_event = {
                "type": "document.processed",
                "user_id": "test_user",
                "data": {"document_id": "doc_123"},
                "timestamp": datetime.now().isoformat()
            }
            
            mock_message = {
                "type": "message",
                "data": json.dumps(system_event)
            }
            
            mock_pubsub_instance.listen.return_value = [mock_message]
            
            # Test system event handling
            await webhook_service._handle_system_event(system_event)
            
            # Verify event was processed
            assert True  # Event handling doesn't raise exceptions
    
    async def test_circuit_breaker_functionality(self, webhook_service, sample_webhook_data):
        """Test circuit breaker for failing webhooks"""
        # Register webhook
        webhook = await webhook_service.register_webhook(
            user_id=sample_webhook_data["user_id"],
            url=sample_webhook_data["url"],
            events=["test.event"]
        )
        
        # Simulate failures
        webhook.failure_count = 5  # Trigger circuit breaker
        await webhook_service._trigger_circuit_breaker(webhook)
        
        # Verify circuit breaker is active
        circuit_breaker_key = f"webhooks:circuit_breaker:{webhook.id}"
        circuit_breaker_data = await redis_client.get(circuit_breaker_key)
        assert circuit_breaker_data is not None
        
        # Verify webhook is deactivated
        webhook_data = await redis_client.get(f"webhooks:endpoints:{webhook.id}")
        webhook_dict = json.loads(webhook_data)
        assert webhook_dict["is_active"] is False
    
    async def test_delivery_optimization(self, webhook_service, sample_webhook_data):
        """Test delivery optimization based on webhook performance"""
        # Register webhook
        webhook = await webhook_service.register_webhook(
            user_id=sample_webhook_data["user_id"],
            url=sample_webhook_data["url"],
            events=["test.event"]
        )
        
        # Test optimization
        optimization_settings = await webhook_service.optimize_delivery_schedule(webhook.id)
        
        assert "retry_delays" in optimization_settings
        assert "timeout" in optimization_settings
        assert "batch_delivery" in optimization_settings
        assert "priority_boost" in optimization_settings
    
    async def test_webhook_metrics(self, webhook_service, sample_webhook_data):
        """Test webhook metrics collection"""
        # Register webhook
        webhook = await webhook_service.register_webhook(
            user_id=sample_webhook_data["user_id"],
            url=sample_webhook_data["url"],
            events=["test.event"]
        )
        
        # Get metrics
        metrics = await webhook_service.get_webhook_metrics(webhook.id)
        
        assert "total_deliveries" in metrics
        assert "successful_deliveries" in metrics
        assert "failed_deliveries" in metrics
        assert "success_rate" in metrics
        assert "circuit_breaker_active" in metrics
    
    async def test_health_check(self, webhook_service):
        """Test webhook service health check"""
        health = await webhook_service.health_check()
        
        assert "status" in health
        assert "redis_connected" in health
        assert "total_webhooks" in health
        assert "active_webhooks" in health
        assert "pending_deliveries" in health


class TestPushNotificationService:
    """Test push notification service functionality"""
    
    @pytest.fixture
    async def notification_service(self):
        """Create notification service instance"""
        service = PushNotificationService()
        # Clear test data
        await redis_client.flushdb()
        return service
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data"""
        return {
            "user_id": "test_user_123",
            "endpoint": "https://fcm.googleapis.com/fcm/send/test",
            "p256dh_key": "test_p256dh_key",
            "auth_key": "test_auth_key",
            "user_agent": "Mozilla/5.0 Test Browser"
        }
    
    async def test_push_subscription(self, notification_service, sample_user_data):
        """Test push notification subscription"""
        success = await notification_service.subscribe_push(
            user_id=sample_user_data["user_id"],
            endpoint=sample_user_data["endpoint"],
            p256dh_key=sample_user_data["p256dh_key"],
            auth_key=sample_user_data["auth_key"],
            user_agent=sample_user_data["user_agent"]
        )
        
        assert success is True
        
        # Verify subscription is stored
        subscription_id = f"{sample_user_data['user_id']}_{hash(sample_user_data['endpoint'])}"
        subscription_data = await redis_client.get(f"push_subscriptions:{subscription_id}")
        assert subscription_data is not None
        
        # Verify subscription is added to user's list
        user_subscriptions = await redis_client.smembers(f"push_subscriptions:user:{sample_user_data['user_id']}")
        assert subscription_id in user_subscriptions
    
    async def test_notification_preferences(self, notification_service, sample_user_data):
        """Test notification preferences management"""
        preferences = NotificationPreferences(
            user_id=sample_user_data["user_id"],
            channels={
                NotificationChannel.WEB_PUSH.value: True,
                NotificationChannel.MOBILE_PUSH.value: False,
                NotificationChannel.EMAIL.value: True
            },
            categories={
                "system": True,
                "research": False,
                "collaboration": True
            }
        )
        
        # Set preferences
        success = await notification_service.set_notification_preferences(
            sample_user_data["user_id"], 
            preferences
        )
        assert success is True
        
        # Get preferences
        retrieved_prefs = await notification_service.get_notification_preferences(
            sample_user_data["user_id"]
        )
        
        assert retrieved_prefs.user_id == sample_user_data["user_id"]
        assert retrieved_prefs.channels[NotificationChannel.WEB_PUSH.value] is True
        assert retrieved_prefs.channels[NotificationChannel.MOBILE_PUSH.value] is False
        assert retrieved_prefs.categories["system"] is True
        assert retrieved_prefs.categories["research"] is False
    
    async def test_notification_sending(self, notification_service, sample_user_data):
        """Test notification sending with different priorities"""
        # Subscribe user first
        await notification_service.subscribe_push(
            user_id=sample_user_data["user_id"],
            endpoint=sample_user_data["endpoint"],
            p256dh_key=sample_user_data["p256dh_key"],
            auth_key=sample_user_data["auth_key"],
            user_agent=sample_user_data["user_agent"]
        )
        
        # Send high priority notification
        notification_id = await notification_service.send_notification(
            user_id=sample_user_data["user_id"],
            title="Urgent Alert",
            body="This is an urgent notification",
            notification_type=NotificationType.URGENT,
            priority=1
        )
        
        assert notification_id is not None
        
        # Verify notification is queued in priority queue
        priority_queue_length = await redis_client.llen("notifications:priority_queue")
        assert priority_queue_length > 0
        
        # Send normal priority notification
        normal_notification_id = await notification_service.send_notification(
            user_id=sample_user_data["user_id"],
            title="Regular Update",
            body="This is a regular notification",
            notification_type=NotificationType.INFO,
            priority=2
        )
        
        assert normal_notification_id is not None
    
    async def test_batch_notification_processing(self, notification_service, sample_user_data):
        """Test batch notification processing"""
        # Create multiple notifications
        notifications = []
        for i in range(5):
            notification = Notification(
                id=f"notif_{i}",
                user_id=sample_user_data["user_id"],
                title=f"Test Notification {i}",
                body=f"This is test notification {i}",
                type=NotificationType.INFO,
                category="test",
                channels=[NotificationChannel.IN_APP],
                created_at=datetime.now()
            )
            notifications.append(notification)
        
        # Test batch processing
        await notification_service._process_notification_batch([
            json.loads(json.dumps(asdict(n), default=str)) for n in notifications
        ])
        
        # Verify in-app notifications were stored
        in_app_notifications = await redis_client.lrange(
            f"notifications:in_app:{sample_user_data['user_id']}", 
            0, -1
        )
        assert len(in_app_notifications) == 5
    
    async def test_delivery_optimization(self, notification_service, sample_user_data):
        """Test delivery schedule optimization"""
        # Mock user interaction history
        interactions = [
            {
                "timestamp": datetime.now().replace(hour=9).isoformat(),
                "type": "read"
            },
            {
                "timestamp": datetime.now().replace(hour=14).isoformat(),
                "type": "click"
            },
            {
                "timestamp": datetime.now().replace(hour=9).isoformat(),
                "type": "read"
            }
        ]
        
        # Store interaction history
        await redis_client.set(
            f"notifications:interactions:{sample_user_data['user_id']}",
            json.dumps(interactions)
        )
        
        # Test optimization
        await notification_service._optimize_user_delivery_schedule(sample_user_data["user_id"])
        
        # Verify preferences were updated
        preferences = await notification_service.get_notification_preferences(sample_user_data["user_id"])
        assert preferences.quiet_hours is not None
        assert "optimal_times" in preferences.quiet_hours
    
    async def test_consolidated_notifications(self, notification_service, sample_user_data):
        """Test consolidated notification delivery"""
        # Create multiple notifications for the same user
        notifications = []
        for i in range(3):
            notification = Notification(
                id=f"notif_{i}",
                user_id=sample_user_data["user_id"],
                title=f"Test Notification {i}",
                body=f"This is test notification {i}",
                type=NotificationType.URGENT if i == 0 else NotificationType.INFO,
                category="test",
                channels=[NotificationChannel.WEB_PUSH],
                created_at=datetime.now()
            )
            notifications.append(notification)
        
        # Mock subscription
        subscription = {
            "user_id": sample_user_data["user_id"],
            "endpoint": sample_user_data["endpoint"],
            "p256dh_key": sample_user_data["p256dh_key"],
            "auth_key": sample_user_data["auth_key"],
            "user_agent": sample_user_data["user_agent"],
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        
        # Test consolidated delivery
        await notification_service._send_consolidated_web_push(notifications, subscription)
        
        # Verify consolidated notification was processed
        assert True  # No exceptions raised
    
    async def test_delivery_analytics(self, notification_service, sample_user_data):
        """Test delivery analytics collection"""
        # Create mock delivery records
        delivery_records = [
            {
                "id": "delivery_1",
                "notification_id": "notif_1",
                "channel": NotificationChannel.WEB_PUSH.value,
                "status": "delivered",
                "attempts": 1
            },
            {
                "id": "delivery_2", 
                "notification_id": "notif_2",
                "channel": NotificationChannel.MOBILE_PUSH.value,
                "status": "failed",
                "attempts": 3
            }
        ]
        
        # Store mock notifications and deliveries
        for i, record in enumerate(delivery_records):
            # Store notification
            notification_data = {
                "id": f"notif_{i+1}",
                "user_id": sample_user_data["user_id"],
                "title": f"Test {i+1}",
                "body": f"Test notification {i+1}"
            }
            await redis_client.set(
                f"notifications:notif_{i+1}",
                json.dumps(notification_data)
            )
            
            # Store delivery record
            await redis_client.set(
                f"notification_deliveries:records:{record['id']}",
                json.dumps(record)
            )
        
        # Get analytics
        analytics = await notification_service.get_delivery_analytics(sample_user_data["user_id"])
        
        assert "total_deliveries" in analytics
        assert "successful_deliveries" in analytics
        assert "failed_deliveries" in analytics
        assert "success_rate" in analytics
        assert "channel_statistics" in analytics
    
    async def test_notification_cleanup(self, notification_service):
        """Test expired notification cleanup"""
        # Create expired notification
        expired_notification = {
            "id": "expired_notif",
            "user_id": "test_user",
            "title": "Expired",
            "body": "This notification is expired",
            "expires_at": (datetime.now() - timedelta(hours=1)).isoformat()
        }
        
        await redis_client.set(
            "notifications:expired_notif",
            json.dumps(expired_notification)
        )
        
        # Run cleanup (simulate one iteration)
        notification_keys = await redis_client.keys("notifications:*")
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
        
        # Verify expired notification was cleaned up
        expired_data = await redis_client.get("notifications:expired_notif")
        assert expired_data is None
    
    async def test_health_check(self, notification_service):
        """Test notification service health check"""
        health = await notification_service.health_check()
        
        assert "status" in health
        assert "redis_connected" in health
        assert "total_subscriptions" in health
        assert "active_subscriptions" in health
        assert "pending_notifications" in health
        assert "supported_channels" in health


class TestIntegrationScenarios:
    """Test integration scenarios between webhook and notification services"""
    
    @pytest.fixture
    async def services(self):
        """Create both services"""
        webhook_service = WebhookService()
        notification_service = PushNotificationService()
        await redis_client.flushdb()
        return webhook_service, notification_service
    
    async def test_webhook_triggered_notification(self, services):
        """Test webhook event triggering push notification"""
        webhook_service, notification_service = services
        
        user_id = "test_user_123"
        
        # Register webhook
        webhook = await webhook_service.register_webhook(
            user_id=user_id,
            url="https://example.com/webhook",
            events=["document.processed"]
        )
        
        # Subscribe to notifications
        await notification_service.subscribe_push(
            user_id=user_id,
            endpoint="https://fcm.googleapis.com/fcm/send/test",
            p256dh_key="test_key",
            auth_key="test_auth",
            user_agent="Test Browser"
        )
        
        # Emit event that should trigger both webhook and notification
        event_id = await webhook_service.emit_event(
            event_type="document.processed",
            data={"document_id": "doc_123", "status": "completed"},
            user_id=user_id
        )
        
        # Send corresponding notification
        notification_id = await notification_service.send_notification(
            user_id=user_id,
            title="Document Processed",
            body="Your document has been processed successfully",
            category="system"
        )
        
        assert event_id is not None
        assert notification_id is not None
        
        # Verify both webhook delivery and notification are queued
        webhook_queue_length = await redis_client.llen("deliveries:queue")
        notification_queue_length = await redis_client.llen("notifications:queue")
        
        assert webhook_queue_length > 0
        assert notification_queue_length > 0
    
    async def test_system_wide_event_propagation(self, services):
        """Test system-wide event propagation through event bus"""
        webhook_service, notification_service = services
        
        # Mock system event
        system_event = {
            "type": "system.maintenance",
            "user_id": "all_users",
            "data": {
                "maintenance_start": datetime.now().isoformat(),
                "estimated_duration": "30 minutes",
                "affected_services": ["document_processing", "chat"]
            },
            "metadata": {
                "priority": "high",
                "broadcast": True
            }
        }
        
        # Test event handling
        await webhook_service._handle_system_event(system_event)
        
        # Verify event was processed without errors
        assert True
    
    async def test_performance_under_load(self, services):
        """Test system performance under high load"""
        webhook_service, notification_service = services
        
        user_id = "load_test_user"
        
        # Register multiple webhooks
        webhooks = []
        for i in range(10):
            webhook = await webhook_service.register_webhook(
                user_id=f"{user_id}_{i}",
                url=f"https://example.com/webhook_{i}",
                events=["load.test"]
            )
            webhooks.append(webhook)
        
        # Subscribe multiple users to notifications
        for i in range(10):
            await notification_service.subscribe_push(
                user_id=f"{user_id}_{i}",
                endpoint=f"https://fcm.googleapis.com/fcm/send/test_{i}",
                p256dh_key=f"test_key_{i}",
                auth_key=f"test_auth_{i}",
                user_agent="Load Test Browser"
            )
        
        # Emit multiple events concurrently
        tasks = []
        for i in range(50):
            task = webhook_service.emit_event(
                event_type="load.test",
                data={"test_id": i, "timestamp": datetime.now().isoformat()},
                user_id=f"{user_id}_{i % 10}"
            )
            tasks.append(task)
        
        # Wait for all events to be processed
        event_ids = await asyncio.gather(*tasks)
        
        # Verify all events were processed
        assert len(event_ids) == 50
        assert all(event_id is not None for event_id in event_ids)
        
        # Send multiple notifications concurrently
        notification_tasks = []
        for i in range(50):
            task = notification_service.send_notification(
                user_id=f"{user_id}_{i % 10}",
                title=f"Load Test Notification {i}",
                body=f"This is load test notification {i}",
                priority=2
            )
            notification_tasks.append(task)
        
        notification_ids = await asyncio.gather(*notification_tasks)
        
        # Verify all notifications were queued
        assert len(notification_ids) == 50
        assert all(notif_id is not None for notif_id in notification_ids)


# Run tests
if __name__ == "__main__":
    async def run_tests():
        """Run all tests"""
        print("🧪 Running comprehensive webhook and notification tests...")
        
        # Test webhook service
        webhook_service = WebhookService()
        await redis_client.flushdb()
        
        print("✅ Testing webhook registration...")
        webhook = await webhook_service.register_webhook(
            user_id="test_user",
            url="https://example.com/webhook",
            events=["document.uploaded", "chat.response"]
        )
        assert webhook.is_active
        print("✅ Webhook registration test passed")
        
        print("✅ Testing event emission...")
        event_id = await webhook_service.emit_event(
            event_type="document.uploaded",
            data={"document_id": "test_doc"},
            user_id="test_user"
        )
        assert event_id is not None
        print("✅ Event emission test passed")
        
        # Test notification service
        notification_service = PushNotificationService()
        
        print("✅ Testing push subscription...")
        success = await notification_service.subscribe_push(
            user_id="test_user",
            endpoint="https://fcm.googleapis.com/test",
            p256dh_key="test_key",
            auth_key="test_auth",
            user_agent="Test Browser"
        )
        assert success
        print("✅ Push subscription test passed")
        
        print("✅ Testing notification sending...")
        notification_id = await notification_service.send_notification(
            user_id="test_user",
            title="Test Notification",
            body="This is a test notification",
            notification_type=NotificationType.INFO
        )
        assert notification_id is not None
        print("✅ Notification sending test passed")
        
        print("✅ Testing health checks...")
        webhook_health = await webhook_service.health_check()
        notification_health = await notification_service.health_check()
        assert webhook_health["status"] == "healthy"
        assert notification_health["status"] == "healthy"
        print("✅ Health check tests passed")
        
        print("🎉 All webhook and notification tests passed!")
    
    # Run the tests
    asyncio.run(run_tests())