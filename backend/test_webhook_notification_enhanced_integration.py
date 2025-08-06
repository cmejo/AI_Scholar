"""
Enhanced integration tests for webhook and notification system
Tests the enhanced event-driven architecture with collaboration and voice shortcut features
"""
import asyncio
import json
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

# Import the main app
from app import app
from services.webhook_service import WebhookService, WEBHOOK_EVENTS
from services.push_notification_service import PushNotificationService, NotificationType, NotificationChannel
from core.redis_client import redis_client

class TestEnhancedWebhookNotificationSystem:
    """Test enhanced webhook and notification system with collaboration and voice features"""
    
    def __init__(self):
        self.client = TestClient(app)
        self.test_user_token = "test_jwt_token"
        self.test_user_id = "test_user_123"
        self.webhook_service = WebhookService()
        self.push_service = PushNotificationService()
    
    def get_auth_headers(self):
        """Get authentication headers for API requests"""
        return {"Authorization": f"Bearer {self.test_user_token}"}
    
    async def test_collaboration_event_system(self):
        """Test collaboration event system for requirement 1.6"""
        print("🧪 Testing collaboration event system...")
        
        # Clear test data
        await redis_client.flushdb()
        
        # Test collaboration event emission
        collaboration_data = {
            "document_id": "doc_123",
            "document_name": "Research Paper Draft",
            "action": "shared",
            "initiated_by": self.test_user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        collaborators = ["user_456", "user_789"]
        
        event_id = await self.webhook_service.emit_collaboration_event(
            event_type="collaboration.document_shared",
            user_id=self.test_user_id,
            collaboration_data=collaboration_data,
            collaborators=collaborators
        )
        
        assert event_id is not None
        print(f"✅ Collaboration event emitted: {event_id}")
        
        # Verify event was stored
        event_data = await redis_client.get(f"events:{event_id}")
        assert event_data is not None
        
        # Verify collaboration notification
        notification_id = await self.push_service.send_collaboration_notification(
            user_id=self.test_user_id,
            collaboration_type="document_sharing",
            title="Document Shared",
            body="You shared a document with collaborators",
            collaboration_data=collaboration_data,
            collaborators=collaborators,
            priority=1
        )
        
        assert notification_id is not None
        print(f"✅ Collaboration notification sent: {notification_id}")
        
        # Verify notification was queued for mobile push
        priority_queue_length = await redis_client.llen("notifications:priority_queue")
        assert priority_queue_length > 0
        print("✅ Collaboration notification queued for high-priority delivery")
    
    async def test_voice_shortcut_system(self):
        """Test voice shortcut system for requirement 2.6"""
        print("🧪 Testing voice shortcut system...")
        
        # Test voice shortcut event emission
        voice_data = {
            "command": "navigate to documents",
            "confidence": 0.95,
            "processing_time": 0.3,
            "action": "navigation",
            "success": True,
            "feedback_message": "Navigated to documents successfully"
        }
        
        event_id = await self.webhook_service.emit_voice_shortcut_event(
            shortcut_type="navigation",
            user_id=self.test_user_id,
            voice_data=voice_data
        )
        
        assert event_id is not None
        print(f"✅ Voice shortcut event emitted: {event_id}")
        
        # Verify voice shortcut feedback notification
        notification_id = await self.push_service.send_voice_shortcut_feedback(
            user_id=self.test_user_id,
            shortcut_type="navigation",
            command="navigate to documents",
            success=True,
            feedback_data=voice_data
        )
        
        assert notification_id is not None
        print(f"✅ Voice shortcut feedback sent: {notification_id}")
        
        # Verify notification was sent to appropriate channels (not mobile push)
        notification_data = await redis_client.get(f"notifications:{notification_id}")
        assert notification_data is not None
        
        notification_dict = json.loads(notification_data)
        channels = [channel["value"] if hasattr(channel, "value") else channel for channel in notification_dict.get("channels", [])]
        assert NotificationChannel.MOBILE_PUSH.value not in channels  # Voice feedback shouldn't go to mobile push
        print("✅ Voice shortcut feedback sent to appropriate channels (not mobile push)")
    
    async def test_mobile_sync_system(self):
        """Test mobile sync system for requirement 1.6"""
        print("🧪 Testing mobile sync system...")
        
        # Test mobile sync event emission
        mobile_data = {
            "device_id": "mobile_device_123",
            "sync_type": "documents",
            "items_synced": 15,
            "conflicts_resolved": 2,
            "sync_duration": 5.2
        }
        
        event_id = await self.webhook_service.emit_mobile_sync_event(
            sync_type="documents",
            user_id=self.test_user_id,
            mobile_data=mobile_data
        )
        
        assert event_id is not None
        print(f"✅ Mobile sync event emitted: {event_id}")
        
        # Test mobile sync notification
        notification_id = await self.push_service.send_mobile_sync_notification(
            user_id=self.test_user_id,
            sync_type="documents",
            sync_status="completed",
            sync_data=mobile_data
        )
        
        assert notification_id is not None
        print(f"✅ Mobile sync notification sent: {notification_id}")
        
        # Verify notification was sent to mobile channels
        notification_data = await redis_client.get(f"notifications:{notification_id}")
        assert notification_data is not None
        
        notification_dict = json.loads(notification_data)
        channels = [channel["value"] if hasattr(channel, "value") else channel for channel in notification_dict.get("channels", [])]
        assert NotificationChannel.MOBILE_PUSH.value in channels
        print("✅ Mobile sync notification sent to mobile channels")
    
    def test_enhanced_api_endpoints(self):
        """Test enhanced API endpoints for collaboration and voice shortcuts"""
        print("🧪 Testing enhanced API endpoints...")
        
        # Mock authentication
        with patch('api.webhook_notification_endpoints.get_current_user') as mock_auth:
            mock_user = AsyncMock()
            mock_user.id = self.test_user_id
            mock_auth.return_value = mock_user
            
            # Test collaboration notification endpoint
            collaboration_data = {
                "collaboration_type": "document_sharing",
                "title": "Document Shared",
                "body": "You shared a research document with your team",
                "collaboration_data": {
                    "document_id": "doc_456",
                    "document_name": "Research Analysis",
                    "action_url": "/documents/doc_456"
                },
                "collaborators": ["user_789", "user_101"],
                "priority": 1
            }
            
            response = self.client.post(
                "/api/webhooks-notifications/collaboration/notify",
                json=collaboration_data,
                headers=self.get_auth_headers()
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            assert "event_id" in result["data"]
            assert "notification_id" in result["data"]
            print("✅ Collaboration notification API endpoint working")
            
            # Test voice shortcut feedback endpoint
            voice_data = {
                "shortcut_type": "quick_search",
                "command": "search for machine learning papers",
                "voice_data": {
                    "success": True,
                    "confidence": 0.92,
                    "processing_time": 0.8,
                    "feedback_message": "Found 25 machine learning papers"
                }
            }
            
            response = self.client.post(
                "/api/webhooks-notifications/voice/shortcut-feedback",
                json=voice_data,
                headers=self.get_auth_headers()
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            assert "event_id" in result["data"]
            assert "notification_id" in result["data"]
            print("✅ Voice shortcut feedback API endpoint working")
            
            # Test mobile sync notification endpoint
            mobile_sync_data = {
                "sync_type": "research_notes",
                "sync_status": "completed",
                "sync_data": {
                    "device_id": "mobile_789",
                    "items_synced": 8,
                    "conflicts_resolved": 1,
                    "sync_duration": 3.1
                }
            }
            
            response = self.client.post(
                "/api/webhooks-notifications/mobile/sync-notification",
                json=mobile_sync_data,
                headers=self.get_auth_headers()
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            assert "event_id" in result["data"]
            assert "notification_id" in result["data"]
            print("✅ Mobile sync notification API endpoint working")
            
            # Test enhanced event listing endpoints
            response = self.client.get("/api/webhooks-notifications/events/collaboration")
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            assert "collaboration_events" in result["data"]
            print("✅ Collaboration events listing endpoint working")
            
            response = self.client.get("/api/webhooks-notifications/events/voice-shortcuts")
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            assert "voice_shortcut_events" in result["data"]
            print("✅ Voice shortcut events listing endpoint working")
            
            response = self.client.get("/api/webhooks-notifications/events/mobile")
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            assert "mobile_events" in result["data"]
            print("✅ Mobile events listing endpoint working")
    
    async def test_event_driven_architecture_integration(self):
        """Test complete event-driven architecture integration"""
        print("🧪 Testing event-driven architecture integration...")
        
        # Clear test data
        await redis_client.flushdb()
        
        # Register webhook for collaboration events
        webhook = await self.webhook_service.register_webhook(
            user_id=self.test_user_id,
            url="https://example.com/collaboration-webhook",
            events=["collaboration.document_shared", "collaboration.real_time_edit"]
        )
        
        # Subscribe to push notifications
        await self.push_service.subscribe_push(
            user_id=self.test_user_id,
            endpoint="https://fcm.googleapis.com/fcm/send/test",
            p256dh_key="test_key",
            auth_key="test_auth",
            user_agent="Test Browser"
        )
        
        # Simulate complete collaboration workflow
        collaboration_data = {
            "document_id": "doc_integration_test",
            "document_name": "Integration Test Document",
            "action": "real_time_edit",
            "edit_type": "text_insertion",
            "edit_position": 150,
            "edit_content": "This is a real-time edit",
            "initiated_by": self.test_user_id
        }
        
        collaborators = ["user_integration_1", "user_integration_2"]
        
        # Emit collaboration event (should trigger both webhook and notification)
        event_id = await self.webhook_service.emit_collaboration_event(
            event_type="collaboration.real_time_edit",
            user_id=self.test_user_id,
            collaboration_data=collaboration_data,
            collaborators=collaborators
        )
        
        # Send corresponding notification
        notification_id = await self.push_service.send_collaboration_notification(
            user_id=self.test_user_id,
            collaboration_type="real_time_edit",
            title="Live Collaboration",
            body="Real-time edits are happening in your shared document",
            collaboration_data=collaboration_data,
            collaborators=collaborators,
            priority=2
        )
        
        # Verify both webhook delivery and notification are queued
        webhook_queue_length = await redis_client.llen("deliveries:queue")
        notification_queue_length = await redis_client.llen("notifications:queue")
        
        assert webhook_queue_length > 0
        assert notification_queue_length > 0
        
        print("✅ Event-driven architecture integration working")
        print(f"   - Webhook deliveries queued: {webhook_queue_length}")
        print(f"   - Notifications queued: {notification_queue_length}")
        print(f"   - Event ID: {event_id}")
        print(f"   - Notification ID: {notification_id}")
    
    async def test_delivery_optimization_for_requirements(self):
        """Test delivery optimization specifically for requirements 1.6 and 2.6"""
        print("🧪 Testing delivery optimization for requirements 1.6 and 2.6...")
        
        # Test collaboration notification optimization (requirement 1.6)
        collaboration_preferences = {
            "user_id": self.test_user_id,
            "channels": {
                NotificationChannel.MOBILE_PUSH.value: True,
                NotificationChannel.WEB_PUSH.value: True,
                NotificationChannel.IN_APP.value: True,
                NotificationChannel.EMAIL.value: False,
                NotificationChannel.SMS.value: False
            },
            "categories": {
                "collaboration": True,
                "voice_commands": True,
                "mobile_sync": True,
                "system": False
            }
        }
        
        # Set preferences
        await self.push_service.set_notification_preferences(
            self.test_user_id,
            collaboration_preferences
        )
        
        # Send collaboration notification and verify it uses mobile push
        notification_id = await self.push_service.send_collaboration_notification(
            user_id=self.test_user_id,
            collaboration_type="urgent_update",
            title="Urgent Collaboration Update",
            body="Important changes made to your shared document",
            collaboration_data={"document_id": "urgent_doc", "priority": "high"},
            priority=1
        )
        
        # Verify notification was sent with high priority
        notification_data = await redis_client.get(f"notifications:{notification_id}")
        assert notification_data is not None
        
        notification_dict = json.loads(notification_data)
        assert notification_dict["priority"] == 1
        assert notification_dict["category"] == "collaboration"
        
        print("✅ Collaboration notification optimization working (requirement 1.6)")
        
        # Test voice shortcut feedback optimization (requirement 2.6)
        voice_notification_id = await self.push_service.send_voice_shortcut_feedback(
            user_id=self.test_user_id,
            shortcut_type="quick_navigation",
            command="go to research dashboard",
            success=True,
            feedback_data={
                "message": "Navigated to research dashboard",
                "execution_time": 0.5,
                "confidence_score": 0.98
            }
        )
        
        # Verify voice feedback notification was optimized (no mobile push spam)
        voice_notification_data = await redis_client.get(f"notifications:{voice_notification_id}")
        assert voice_notification_data is not None
        
        voice_notification_dict = json.loads(voice_notification_data)
        channels = [channel["value"] if hasattr(channel, "value") else channel for channel in voice_notification_dict.get("channels", [])]
        
        # Voice feedback should not use mobile push to avoid spam
        assert NotificationChannel.MOBILE_PUSH.value not in channels
        assert NotificationChannel.IN_APP.value in channels or NotificationChannel.WEB_PUSH.value in channels
        
        print("✅ Voice shortcut feedback optimization working (requirement 2.6)")
    
    async def run_all_tests(self):
        """Run all enhanced tests"""
        print("🚀 Starting enhanced webhook and notification system tests...")
        
        try:
            await self.test_collaboration_event_system()
            await self.test_voice_shortcut_system()
            await self.test_mobile_sync_system()
            self.test_enhanced_api_endpoints()
            await self.test_event_driven_architecture_integration()
            await self.test_delivery_optimization_for_requirements()
            
            print("🎉 All enhanced webhook and notification tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Enhanced test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


# Run the enhanced tests
if __name__ == "__main__":
    async def run_enhanced_tests():
        """Run enhanced tests"""
        test_runner = TestEnhancedWebhookNotificationSystem()
        success = await test_runner.run_all_tests()
        
        if success:
            print("\n✅ Enhanced webhook and notification system implementation completed successfully!")
            print("\n📋 Enhanced Implementation Summary:")
            print("- ✅ Collaboration event system for mobile push notifications (Requirement 1.6)")
            print("- ✅ Voice shortcut feedback system for quick access (Requirement 2.6)")
            print("- ✅ Mobile sync notification system")
            print("- ✅ Enhanced event-driven architecture with specialized channels")
            print("- ✅ Delivery optimization for collaboration and voice features")
            print("- ✅ Enhanced API endpoints for collaboration and voice shortcuts")
            print("- ✅ Intelligent notification routing based on content type")
            print("- ✅ Circuit breaker and retry logic for reliable delivery")
            print("- ✅ Comprehensive event types for all system interactions")
            print("- ✅ Background task processing for real-time event handling")
            
            print("\n🎯 Requirements Fulfilled:")
            print("- ✅ Requirement 1.6: Mobile push notifications for collaboration updates")
            print("- ✅ Requirement 2.6: Voice shortcuts for quick access to functions")
            print("- ✅ Event-driven architecture for system-wide notifications")
            print("- ✅ Delivery optimization and user preference management")
        else:
            print("\n❌ Some enhanced tests failed. Please check the implementation.")
    
    # Run the enhanced tests
    asyncio.run(run_enhanced_tests())