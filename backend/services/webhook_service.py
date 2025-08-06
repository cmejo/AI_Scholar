"""
Webhook service for real-time integration updates
Provides event-driven architecture for system-wide notifications
"""
import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
import aiohttp
# from sqlalchemy import select, update, delete
# from sqlalchemy.ext.asyncio import AsyncSession  # Not needed for Redis-based implementation

# from core.database import get_async_session  # Not needed for Redis-based implementation
from core.redis_client import redis_client

logger = logging.getLogger(__name__)

@dataclass
class WebhookEndpoint:
    id: str
    user_id: str
    url: str
    events: List[str]
    secret: str
    is_active: bool
    created_at: datetime
    last_triggered: Optional[datetime] = None
    failure_count: int = 0
    max_failures: int = 5

@dataclass
class WebhookEvent:
    id: str
    event_type: str
    data: Dict[str, Any]
    user_id: str
    timestamp: datetime
    source: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class WebhookDelivery:
    id: str
    webhook_id: str
    event_id: str
    url: str
    payload: Dict[str, Any]
    status: str  # pending, delivered, failed, retrying
    attempts: int
    last_attempt: Optional[datetime] = None
    next_retry: Optional[datetime] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None

class WebhookService:
    def __init__(self):
        self.redis_prefix = "webhooks:"
        self.event_prefix = "events:"
        self.delivery_prefix = "deliveries:"
        self.max_retry_attempts = 5
        self.retry_delays = [60, 300, 900, 3600, 7200]  # seconds
        self.timeout = 30  # seconds
        
        # Event handlers registry
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Event-driven architecture components
        self.event_bus_channel = "webhook_events"
        self.system_events_channel = "system_events"
        self.delivery_optimization_enabled = True
        
        # Enhanced event-driven features
        self.collaboration_events_channel = "collaboration_events"
        self.voice_shortcuts_channel = "voice_shortcuts_events"
        self.mobile_sync_channel = "mobile_sync_events"
        
        # Delivery optimization settings
        self.batch_size = 10
        self.batch_timeout = 5  # seconds
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 300  # 5 minutes
        
    async def health_check(self) -> Dict[str, Any]:
        """Health check for webhook service"""
        try:
            # Check Redis connection
            await redis_client.ping()
            
            # Count active webhooks
            webhook_keys = await redis_client.keys(f"{self.redis_prefix}endpoints:*")
            active_webhooks = 0
            
            for key in webhook_keys:
                webhook_data = await redis_client.get(key)
                if webhook_data:
                    if isinstance(webhook_data, str):
                        webhook_dict = json.loads(webhook_data)
                    else:
                        webhook_dict = webhook_data
                    if webhook_dict.get("is_active", False):
                        active_webhooks += 1
            
            # Count pending deliveries
            pending_deliveries = await redis_client.llen(f"{self.delivery_prefix}queue")
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "total_webhooks": len(webhook_keys),
                "active_webhooks": active_webhooks,
                "pending_deliveries": pending_deliveries,
                "registered_events": list(self.event_handlers.keys())
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def register_webhook(
        self,
        user_id: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None
    ) -> WebhookEndpoint:
        """Register a new webhook endpoint"""
        try:
            # Generate webhook ID and secret
            webhook_id = f"webhook_{datetime.now().timestamp()}_{user_id}"
            if not secret:
                secret = hashlib.sha256(f"{webhook_id}{url}{datetime.now()}".encode()).hexdigest()
            
            # Create webhook endpoint
            webhook = WebhookEndpoint(
                id=webhook_id,
                user_id=user_id,
                url=url,
                events=events,
                secret=secret,
                is_active=True,
                created_at=datetime.now()
            )
            
            # Store webhook
            await redis_client.set(
                f"{self.redis_prefix}endpoints:{webhook_id}",
                json.dumps(asdict(webhook), default=str)
            )
            
            # Add to user's webhook list
            await redis_client.sadd(f"{self.redis_prefix}user:{user_id}", webhook_id)
            
            # Add to event subscriptions
            for event_type in events:
                await redis_client.sadd(f"{self.redis_prefix}events:{event_type}", webhook_id)
            
            logger.info(f"Registered webhook {webhook_id} for user {user_id}")
            return webhook
            
        except Exception as e:
            logger.error(f"Webhook registration failed: {e}")
            raise Exception(f"Failed to register webhook: {str(e)}")

    async def unregister_webhook(self, webhook_id: str, user_id: str) -> bool:
        """Unregister a webhook endpoint"""
        try:
            # Get webhook to verify ownership
            webhook_data = await redis_client.get(f"{self.redis_prefix}endpoints:{webhook_id}")
            if not webhook_data:
                return False
            
            if isinstance(webhook_data, str):
                webhook_dict = json.loads(webhook_data)
            else:
                webhook_dict = webhook_data
            if webhook_dict.get("user_id") != user_id:
                return False
            
            # Remove from event subscriptions
            for event_type in webhook_dict.get("events", []):
                await redis_client.srem(f"{self.redis_prefix}events:{event_type}", webhook_id)
            
            # Remove from user's webhook list
            await redis_client.srem(f"{self.redis_prefix}user:{user_id}", webhook_id)
            
            # Delete webhook
            await redis_client.delete(f"{self.redis_prefix}endpoints:{webhook_id}")
            
            logger.info(f"Unregistered webhook {webhook_id}")
            return True
            
        except Exception as e:
            logger.error(f"Webhook unregistration failed: {e}")
            return False

    async def emit_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        user_id: str,
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Emit an event to trigger webhooks"""
        try:
            # Create event
            event_id = f"event_{datetime.now().timestamp()}_{event_type}"
            event = WebhookEvent(
                id=event_id,
                event_type=event_type,
                data=data,
                user_id=user_id,
                timestamp=datetime.now(),
                source=source,
                metadata=metadata
            )
            
            # Store event
            await redis_client.setex(
                f"{self.event_prefix}{event_id}",
                86400,  # Keep for 24 hours
                json.dumps(asdict(event), default=str)
            )
            
            # Find webhooks subscribed to this event
            webhook_ids = await redis_client.smembers(f"{self.redis_prefix}events:{event_type}")
            
            # Create deliveries for each webhook
            for webhook_id in webhook_ids:
                await self._create_delivery(webhook_id, event)
            
            # Call registered event handlers
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:
                        await handler(event)
                    except Exception as handler_error:
                        logger.error(f"Event handler failed: {handler_error}")
            
            logger.info(f"Emitted event {event_id} to {len(webhook_ids)} webhooks")
            return event_id
            
        except Exception as e:
            logger.error(f"Event emission failed: {e}")
            raise Exception(f"Failed to emit event: {str(e)}")

    async def process_deliveries(self):
        """Process pending webhook deliveries"""
        try:
            while True:
                # Get next delivery from queue
                delivery_data = await redis_client.brpop(f"{self.delivery_prefix}queue", timeout=1)
                
                if not delivery_data:
                    continue
                
                delivery_dict = json.loads(delivery_data[1])
                delivery = WebhookDelivery(**delivery_dict)
                
                # Process delivery
                await self._process_delivery(delivery)
                
        except Exception as e:
            logger.error(f"Delivery processing failed: {e}")

    async def _create_delivery(self, webhook_id: str, event: WebhookEvent):
        """Create a webhook delivery"""
        try:
            # Get webhook details
            webhook_data = await redis_client.get(f"{self.redis_prefix}endpoints:{webhook_id}")
            if not webhook_data:
                return
            
            if isinstance(webhook_data, str):
                webhook_dict = json.loads(webhook_data)
            else:
                webhook_dict = webhook_data
            
            # Convert datetime strings back to datetime objects
            if 'created_at' in webhook_dict and isinstance(webhook_dict['created_at'], str):
                webhook_dict['created_at'] = datetime.fromisoformat(webhook_dict['created_at'])
            if 'last_triggered' in webhook_dict and webhook_dict['last_triggered'] and isinstance(webhook_dict['last_triggered'], str):
                webhook_dict['last_triggered'] = datetime.fromisoformat(webhook_dict['last_triggered'])
            
            webhook = WebhookEndpoint(**webhook_dict)
            
            # Check if webhook is active
            if not webhook.is_active:
                return
            
            # Check if webhook has exceeded failure limit
            if webhook.failure_count >= webhook.max_failures:
                logger.warning(f"Webhook {webhook_id} disabled due to failures")
                webhook.is_active = False
                await redis_client.set(
                    f"{self.redis_prefix}endpoints:{webhook_id}",
                    json.dumps(asdict(webhook), default=str)
                )
                return
            
            # Create delivery
            delivery_id = f"delivery_{datetime.now().timestamp()}_{webhook_id}"
            payload = {
                "event": asdict(event),
                "webhook": {
                    "id": webhook.id,
                    "url": webhook.url
                },
                "timestamp": datetime.now().isoformat()
            }
            
            delivery = WebhookDelivery(
                id=delivery_id,
                webhook_id=webhook_id,
                event_id=event.id,
                url=webhook.url,
                payload=payload,
                status="pending",
                attempts=0
            )
            
            # Add to delivery queue
            await redis_client.lpush(
                f"{self.delivery_prefix}queue",
                json.dumps(asdict(delivery), default=str)
            )
            
        except Exception as e:
            logger.error(f"Delivery creation failed: {e}")

    async def _process_delivery(self, delivery: WebhookDelivery):
        """Process a single webhook delivery"""
        try:
            # Get webhook for signature
            webhook_data = await redis_client.get(f"{self.redis_prefix}endpoints:{delivery.webhook_id}")
            if not webhook_data:
                logger.error(f"Webhook {delivery.webhook_id} not found")
                return
            
            if isinstance(webhook_data, str):
                webhook_dict = json.loads(webhook_data)
            else:
                webhook_dict = webhook_data
            
            # Convert datetime strings back to datetime objects
            if 'created_at' in webhook_dict and isinstance(webhook_dict['created_at'], str):
                webhook_dict['created_at'] = datetime.fromisoformat(webhook_dict['created_at'])
            if 'last_triggered' in webhook_dict and webhook_dict['last_triggered'] and isinstance(webhook_dict['last_triggered'], str):
                webhook_dict['last_triggered'] = datetime.fromisoformat(webhook_dict['last_triggered'])
            webhook = WebhookEndpoint(**webhook_dict)
            
            # Prepare payload
            payload_json = json.dumps(delivery.payload, default=str)
            
            # Generate signature
            signature = hmac.new(
                webhook.secret.encode(),
                payload_json.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Signature": f"sha256={signature}",
                "X-Webhook-Event": delivery.payload["event"]["event_type"],
                "X-Webhook-Delivery": delivery.id,
                "User-Agent": "AI-Scholar-Webhook/1.0"
            }
            
            # Update delivery attempt
            delivery.attempts += 1
            delivery.last_attempt = datetime.now()
            delivery.status = "delivering"
            
            # Make HTTP request
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                try:
                    async with session.post(
                        delivery.url,
                        data=payload_json,
                        headers=headers
                    ) as response:
                        delivery.response_status = response.status
                        delivery.response_body = await response.text()
                        
                        if 200 <= response.status < 300:
                            # Success
                            delivery.status = "delivered"
                            webhook.last_triggered = datetime.now()
                            webhook.failure_count = 0  # Reset failure count on success
                            
                            logger.info(f"Webhook delivery {delivery.id} successful")
                            
                        else:
                            # HTTP error
                            delivery.status = "failed"
                            delivery.error_message = f"HTTP {response.status}: {delivery.response_body}"
                            webhook.failure_count += 1
                            
                            logger.warning(f"Webhook delivery {delivery.id} failed: HTTP {response.status}")
                            
                except asyncio.TimeoutError:
                    delivery.status = "failed"
                    delivery.error_message = "Request timeout"
                    webhook.failure_count += 1
                    
                    logger.warning(f"Webhook delivery {delivery.id} timed out")
                    
                except Exception as request_error:
                    delivery.status = "failed"
                    delivery.error_message = str(request_error)
                    webhook.failure_count += 1
                    
                    logger.error(f"Webhook delivery {delivery.id} failed: {request_error}")
            
            # Handle retry logic
            if delivery.status == "failed" and delivery.attempts < self.max_retry_attempts:
                # Schedule retry
                retry_delay = self.retry_delays[min(delivery.attempts - 1, len(self.retry_delays) - 1)]
                delivery.next_retry = datetime.now() + timedelta(seconds=retry_delay)
                delivery.status = "retrying"
                
                # Add back to queue with delay
                await asyncio.sleep(1)  # Small delay before re-queuing
                await redis_client.lpush(
                    f"{self.delivery_prefix}retry_queue",
                    json.dumps(asdict(delivery), default=str)
                )
                
                logger.info(f"Webhook delivery {delivery.id} scheduled for retry in {retry_delay} seconds")
            
            # Update webhook
            await redis_client.set(
                f"{self.redis_prefix}endpoints:{webhook.id}",
                json.dumps(asdict(webhook), default=str)
            )
            
            # Store delivery record
            await redis_client.setex(
                f"{self.delivery_prefix}records:{delivery.id}",
                86400 * 7,  # Keep for 7 days
                json.dumps(asdict(delivery), default=str)
            )
            
        except Exception as e:
            logger.error(f"Delivery processing failed: {e}")

    async def process_retries(self):
        """Process retry queue for failed deliveries"""
        try:
            while True:
                # Get next retry from queue
                retry_data = await redis_client.brpop(f"{self.delivery_prefix}retry_queue", timeout=1)
                
                if not retry_data:
                    continue
                
                delivery_dict = json.loads(retry_data[1])
                delivery = WebhookDelivery(**delivery_dict)
                
                # Check if it's time to retry
                if delivery.next_retry and datetime.now() >= delivery.next_retry:
                    # Add back to main queue
                    await redis_client.lpush(
                        f"{self.delivery_prefix}queue",
                        json.dumps(asdict(delivery), default=str)
                    )
                else:
                    # Put back in retry queue
                    await redis_client.lpush(
                        f"{self.delivery_prefix}retry_queue",
                        json.dumps(asdict(delivery), default=str)
                    )
                    await asyncio.sleep(10)  # Wait before checking again
                
        except Exception as e:
            logger.error(f"Retry processing failed: {e}")

    async def get_user_webhooks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all webhooks for a user"""
        try:
            webhook_ids = await redis_client.smembers(f"{self.redis_prefix}user:{user_id}")
            webhooks = []
            
            for webhook_id in webhook_ids:
                webhook_data = await redis_client.get(f"{self.redis_prefix}endpoints:{webhook_id}")
                if webhook_data:
                    if isinstance(webhook_data, str):
                        webhook_dict = json.loads(webhook_data)
                    else:
                        webhook_dict = webhook_data
                    
                    # Get delivery statistics
                    stats = await self._get_webhook_stats(webhook_id)
                    webhook_dict["stats"] = stats
                    
                    webhooks.append(webhook_dict)
            
            return webhooks
            
        except Exception as e:
            logger.error(f"Failed to get user webhooks: {e}")
            return []

    async def get_webhook_deliveries(self, webhook_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent deliveries for a webhook"""
        try:
            # Get delivery records
            delivery_keys = await redis_client.keys(f"{self.delivery_prefix}records:*")
            deliveries = []
            
            for key in delivery_keys:
                delivery_data = await redis_client.get(key)
                if delivery_data:
                    delivery_dict = json.loads(delivery_data)
                    if delivery_dict.get("webhook_id") == webhook_id:
                        deliveries.append(delivery_dict)
            
            # Sort by last attempt (newest first)
            deliveries.sort(key=lambda x: x.get("last_attempt", ""), reverse=True)
            
            return deliveries[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get webhook deliveries: {e}")
            return []

    async def _get_webhook_stats(self, webhook_id: str) -> Dict[str, Any]:
        """Get statistics for a webhook"""
        try:
            # Get delivery records for this webhook
            delivery_keys = await redis_client.keys(f"{self.delivery_prefix}records:*")
            total_deliveries = 0
            successful_deliveries = 0
            failed_deliveries = 0
            
            for key in delivery_keys:
                delivery_data = await redis_client.get(key)
                if delivery_data:
                    delivery_dict = json.loads(delivery_data)
                    if delivery_dict.get("webhook_id") == webhook_id:
                        total_deliveries += 1
                        if delivery_dict.get("status") == "delivered":
                            successful_deliveries += 1
                        elif delivery_dict.get("status") == "failed":
                            failed_deliveries += 1
            
            success_rate = (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0
            
            return {
                "total_deliveries": total_deliveries,
                "successful_deliveries": successful_deliveries,
                "failed_deliveries": failed_deliveries,
                "success_rate": round(success_rate, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get webhook stats: {e}")
            return {
                "total_deliveries": 0,
                "successful_deliveries": 0,
                "failed_deliveries": 0,
                "success_rate": 0
            }

    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler function"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def unregister_event_handler(self, event_type: str, handler: Callable):
        """Unregister an event handler function"""
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
                if not self.event_handlers[event_type]:
                    del self.event_handlers[event_type]
            except ValueError:
                pass

    async def start_background_tasks(self):
        """Start background tasks for processing deliveries and retries"""
        try:
            # Start delivery processor
            asyncio.create_task(self.process_deliveries())
            
            # Start retry processor
            asyncio.create_task(self.process_retries())
            
            # Start event bus listener
            asyncio.create_task(self.listen_to_event_bus())
            
            # Start batch delivery processor
            asyncio.create_task(self.process_batch_deliveries())
            
            # Start circuit breaker monitor
            asyncio.create_task(self.monitor_circuit_breakers())
            
            logger.info("Webhook background tasks started")
            
        except Exception as e:
            logger.error(f"Failed to start webhook background tasks: {e}")

    async def listen_to_event_bus(self):
        """Listen to system-wide events for webhook triggers"""
        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(self.event_bus_channel, self.system_events_channel)
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        event_data = json.loads(message['data'])
                        await self._handle_system_event(event_data)
                    except Exception as e:
                        logger.error(f"Failed to handle system event: {e}")
                        
        except Exception as e:
            logger.error(f"Event bus listener failed: {e}")

    async def _handle_system_event(self, event_data: Dict[str, Any]):
        """Handle system-wide events"""
        try:
            event_type = event_data.get('type')
            user_id = event_data.get('user_id')
            data = event_data.get('data', {})
            
            if not event_type or not user_id:
                return
            
            # Emit webhook event
            await self.emit_event(
                event_type=event_type,
                data=data,
                user_id=user_id,
                source="system_event_bus",
                metadata=event_data.get('metadata', {})
            )
            
        except Exception as e:
            logger.error(f"System event handling failed: {e}")

    async def process_batch_deliveries(self):
        """Process webhook deliveries in batches for optimization"""
        try:
            batch = []
            last_batch_time = datetime.now()
            
            while True:
                try:
                    # Get delivery from queue with timeout
                    delivery_data = await redis_client.brpop(
                        f"{self.delivery_prefix}batch_queue", 
                        timeout=1
                    )
                    
                    if delivery_data:
                        delivery_dict = json.loads(delivery_data[1])
                        batch.append(delivery_dict)
                    
                    # Process batch if it's full or timeout reached
                    current_time = datetime.now()
                    time_since_last_batch = (current_time - last_batch_time).total_seconds()
                    
                    if (len(batch) >= self.batch_size or 
                        (batch and time_since_last_batch >= self.batch_timeout)):
                        
                        await self._process_delivery_batch(batch)
                        batch = []
                        last_batch_time = current_time
                        
                except Exception as e:
                    logger.error(f"Batch delivery processing error: {e}")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Batch delivery processor failed: {e}")

    async def _process_delivery_batch(self, batch: List[Dict[str, Any]]):
        """Process a batch of deliveries concurrently"""
        try:
            tasks = []
            for delivery_dict in batch:
                delivery = WebhookDelivery(**delivery_dict)
                tasks.append(self._process_delivery(delivery))
            
            # Process deliveries concurrently
            await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info(f"Processed batch of {len(batch)} deliveries")
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")

    async def monitor_circuit_breakers(self):
        """Monitor and manage circuit breakers for webhook endpoints"""
        try:
            while True:
                # Check all webhook endpoints for circuit breaker status
                webhook_keys = await redis_client.keys(f"{self.redis_prefix}endpoints:*")
                
                for key in webhook_keys:
                    webhook_data = await redis_client.get(key)
                    if webhook_data:
                        if isinstance(webhook_data, str):
                            webhook_dict = json.loads(webhook_data)
                        else:
                            webhook_dict = webhook_data
                        
                        # Convert datetime strings back to datetime objects
                        if 'created_at' in webhook_dict and isinstance(webhook_dict['created_at'], str):
                            webhook_dict['created_at'] = datetime.fromisoformat(webhook_dict['created_at'])
                        if 'last_triggered' in webhook_dict and webhook_dict['last_triggered'] and isinstance(webhook_dict['last_triggered'], str):
                            webhook_dict['last_triggered'] = datetime.fromisoformat(webhook_dict['last_triggered'])
                        
                        webhook = WebhookEndpoint(**webhook_dict)
                        
                        # Check if circuit breaker should be triggered
                        if webhook.failure_count >= self.circuit_breaker_threshold:
                            await self._trigger_circuit_breaker(webhook)
                        
                        # Check if circuit breaker should be reset
                        elif not webhook.is_active:
                            await self._check_circuit_breaker_reset(webhook)
                
                await asyncio.sleep(60)  # Check every minute
                
        except Exception as e:
            logger.error(f"Circuit breaker monitor failed: {e}")

    async def _trigger_circuit_breaker(self, webhook: WebhookEndpoint):
        """Trigger circuit breaker for failing webhook"""
        try:
            if webhook.is_active:
                webhook.is_active = False
                
                # Store circuit breaker timestamp
                await redis_client.setex(
                    f"{self.redis_prefix}circuit_breaker:{webhook.id}",
                    self.circuit_breaker_timeout,
                    datetime.now().isoformat()
                )
                
                # Update webhook
                await redis_client.set(
                    f"{self.redis_prefix}endpoints:{webhook.id}",
                    json.dumps(asdict(webhook), default=str)
                )
                
                logger.warning(f"Circuit breaker triggered for webhook {webhook.id}")
                
                # Emit system event
                await self._emit_system_event(
                    "webhook.circuit_breaker.triggered",
                    webhook.user_id,
                    {"webhook_id": webhook.id, "failure_count": webhook.failure_count}
                )
                
        except Exception as e:
            logger.error(f"Circuit breaker trigger failed: {e}")

    async def _check_circuit_breaker_reset(self, webhook: WebhookEndpoint):
        """Check if circuit breaker should be reset"""
        try:
            circuit_breaker_key = f"{self.redis_prefix}circuit_breaker:{webhook.id}"
            circuit_breaker_data = await redis_client.get(circuit_breaker_key)
            
            if not circuit_breaker_data:
                # Circuit breaker timeout expired, reset webhook
                webhook.is_active = True
                webhook.failure_count = 0
                
                await redis_client.set(
                    f"{self.redis_prefix}endpoints:{webhook.id}",
                    json.dumps(asdict(webhook), default=str)
                )
                
                logger.info(f"Circuit breaker reset for webhook {webhook.id}")
                
                # Emit system event
                await self._emit_system_event(
                    "webhook.circuit_breaker.reset",
                    webhook.user_id,
                    {"webhook_id": webhook.id}
                )
                
        except Exception as e:
            logger.error(f"Circuit breaker reset check failed: {e}")

    async def emit_collaboration_event(
        self,
        event_type: str,
        user_id: str,
        collaboration_data: Dict[str, Any],
        collaborators: List[str] = None
    ) -> str:
        """Emit collaboration event for requirement 1.6 - mobile push notifications for collaboration updates"""
        try:
            # Emit event for primary user
            event_id = await self.emit_event(
                event_type=event_type,
                data=collaboration_data,
                user_id=user_id,
                source="collaboration_system",
                metadata={
                    "collaboration": True,
                    "requires_push_notification": True,
                    "priority": "high"
                }
            )
            
            # Emit events for all collaborators
            if collaborators:
                for collaborator_id in collaborators:
                    if collaborator_id != user_id:  # Don't duplicate for the initiator
                        await self.emit_event(
                            event_type=event_type,
                            data={
                                **collaboration_data,
                                "initiated_by": user_id,
                                "collaboration_role": "participant"
                            },
                            user_id=collaborator_id,
                            source="collaboration_system",
                            metadata={
                                "collaboration": True,
                                "requires_push_notification": True,
                                "priority": "high"
                            }
                        )
            
            # Publish to collaboration events channel
            await redis_client.publish(
                self.collaboration_events_channel,
                json.dumps({
                    "event_id": event_id,
                    "event_type": event_type,
                    "user_id": user_id,
                    "collaborators": collaborators or [],
                    "data": collaboration_data,
                    "timestamp": datetime.now().isoformat()
                })
            )
            
            logger.info(f"Collaboration event {event_type} emitted for user {user_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"Collaboration event emission failed: {e}")
            raise Exception(f"Failed to emit collaboration event: {str(e)}")

    async def emit_voice_shortcut_event(
        self,
        shortcut_type: str,
        user_id: str,
        voice_data: Dict[str, Any]
    ) -> str:
        """Emit voice shortcut event for requirement 2.6 - voice shortcuts for quick access"""
        try:
            event_id = await self.emit_event(
                event_type="voice.shortcut_triggered",
                data={
                    "shortcut_type": shortcut_type,
                    "voice_command": voice_data.get("command", ""),
                    "confidence_score": voice_data.get("confidence", 0.0),
                    "processing_time": voice_data.get("processing_time", 0.0),
                    "action_executed": voice_data.get("action", ""),
                    **voice_data
                },
                user_id=user_id,
                source="voice_system",
                metadata={
                    "voice_shortcut": True,
                    "shortcut_type": shortcut_type,
                    "requires_feedback": True
                }
            )
            
            # Publish to voice shortcuts channel
            await redis_client.publish(
                self.voice_shortcuts_channel,
                json.dumps({
                    "event_id": event_id,
                    "shortcut_type": shortcut_type,
                    "user_id": user_id,
                    "voice_data": voice_data,
                    "timestamp": datetime.now().isoformat()
                })
            )
            
            logger.info(f"Voice shortcut event {shortcut_type} emitted for user {user_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"Voice shortcut event emission failed: {e}")
            raise Exception(f"Failed to emit voice shortcut event: {str(e)}")

    async def emit_mobile_sync_event(
        self,
        sync_type: str,
        user_id: str,
        mobile_data: Dict[str, Any]
    ) -> str:
        """Emit mobile sync event for requirement 1.6 - mobile data synchronization"""
        try:
            event_id = await self.emit_event(
                event_type="mobile.sync_requested",
                data={
                    "sync_type": sync_type,
                    "device_id": mobile_data.get("device_id", ""),
                    "sync_timestamp": datetime.now().isoformat(),
                    "data_types": mobile_data.get("data_types", []),
                    "offline_changes": mobile_data.get("offline_changes", []),
                    **mobile_data
                },
                user_id=user_id,
                source="mobile_sync_system",
                metadata={
                    "mobile_sync": True,
                    "sync_type": sync_type,
                    "requires_push_notification": True
                }
            )
            
            # Publish to mobile sync channel
            await redis_client.publish(
                self.mobile_sync_channel,
                json.dumps({
                    "event_id": event_id,
                    "sync_type": sync_type,
                    "user_id": user_id,
                    "mobile_data": mobile_data,
                    "timestamp": datetime.now().isoformat()
                })
            )
            
            logger.info(f"Mobile sync event {sync_type} emitted for user {user_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"Mobile sync event emission failed: {e}")
            raise Exception(f"Failed to emit mobile sync event: {str(e)}")

    async def _emit_system_event(self, event_type: str, user_id: str, data: Dict[str, Any]):
        """Emit system event to event bus"""
        try:
            event_data = {
                "type": event_type,
                "user_id": user_id,
                "data": data,
                "timestamp": datetime.now().isoformat(),
                "source": "webhook_service"
            }
            
            await redis_client.publish(
                self.system_events_channel,
                json.dumps(event_data, default=str)
            )
            
        except Exception as e:
            logger.error(f"System event emission failed: {e}")

    async def get_webhook_metrics(self, webhook_id: str) -> Dict[str, Any]:
        """Get comprehensive metrics for a webhook"""
        try:
            # Get basic stats
            stats = await self._get_webhook_stats(webhook_id)
            
            # Get recent performance metrics
            performance_key = f"{self.redis_prefix}performance:{webhook_id}"
            performance_data = await redis_client.get(performance_key)
            
            performance_metrics = {}
            if performance_data:
                performance_metrics = json.loads(performance_data)
            
            # Get circuit breaker status
            circuit_breaker_key = f"{self.redis_prefix}circuit_breaker:{webhook_id}"
            circuit_breaker_active = await redis_client.exists(circuit_breaker_key)
            
            return {
                **stats,
                "performance_metrics": performance_metrics,
                "circuit_breaker_active": bool(circuit_breaker_active),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get webhook metrics: {e}")
            return {}

    async def optimize_delivery_schedule(self, webhook_id: str) -> Dict[str, Any]:
        """Optimize delivery schedule based on webhook performance"""
        try:
            metrics = await self.get_webhook_metrics(webhook_id)
            
            # Calculate optimal delivery settings
            success_rate = metrics.get("success_rate", 0)
            avg_response_time = metrics.get("performance_metrics", {}).get("avg_response_time", 1000)
            
            # Adjust retry delays based on performance
            if success_rate > 90:
                # High success rate - use shorter delays
                optimized_delays = [30, 120, 300, 900, 1800]
            elif success_rate > 70:
                # Medium success rate - use standard delays
                optimized_delays = self.retry_delays
            else:
                # Low success rate - use longer delays
                optimized_delays = [120, 600, 1800, 7200, 14400]
            
            # Adjust timeout based on response time
            optimized_timeout = min(60, max(10, int(avg_response_time / 1000 * 2)))
            
            optimization_settings = {
                "retry_delays": optimized_delays,
                "timeout": optimized_timeout,
                "batch_delivery": success_rate > 80,
                "priority_boost": success_rate > 95
            }
            
            # Store optimization settings
            await redis_client.setex(
                f"{self.redis_prefix}optimization:{webhook_id}",
                86400,  # Keep for 24 hours
                json.dumps(optimization_settings)
            )
            
            return optimization_settings
            
        except Exception as e:
            logger.error(f"Delivery optimization failed: {e}")
            return {}

# Common webhook events
WEBHOOK_EVENTS = {
    "document.uploaded": "Document uploaded",
    "document.processed": "Document processing completed",
    "document.deleted": "Document deleted",
    "document.shared": "Document shared with collaborators",
    "chat.message": "Chat message sent",
    "chat.response": "Chat response generated",
    "quiz.created": "Quiz created",
    "quiz.completed": "Quiz completed",
    "progress.updated": "Learning progress updated",
    "achievement.earned": "Achievement earned",
    "compliance.violation": "Compliance violation detected",
    "integration.connected": "External integration connected",
    "integration.disconnected": "External integration disconnected",
    "user.login": "User logged in",
    "user.logout": "User logged out",
    "system.maintenance": "System maintenance scheduled",
    "system.error": "System error occurred",
    # Collaboration events for requirement 1.6
    "collaboration.invite_sent": "Collaboration invitation sent",
    "collaboration.invite_accepted": "Collaboration invitation accepted",
    "collaboration.document_updated": "Collaborative document updated",
    "collaboration.comment_added": "Comment added to shared document",
    "collaboration.real_time_edit": "Real-time collaborative edit occurred",
    "collaboration.session_started": "Collaboration session started",
    "collaboration.session_ended": "Collaboration session ended",
    # Voice shortcut events for requirement 2.6
    "voice.shortcut_triggered": "Voice shortcut command triggered",
    "voice.command_processed": "Voice command processed successfully",
    "voice.navigation_requested": "Voice navigation command received",
    "voice.quick_action_executed": "Voice quick action executed",
    # Mobile push notification events for requirement 1.6
    "mobile.sync_requested": "Mobile device sync requested",
    "mobile.offline_mode_enabled": "Mobile offline mode enabled",
    "mobile.push_notification_sent": "Push notification sent to mobile device",
    "mobile.collaboration_update": "Mobile collaboration update received",
    # System events for enhanced event-driven architecture
    "notification.delivery_optimized": "Notification delivery schedule optimized",
    "webhook.circuit_breaker_triggered": "Webhook circuit breaker activated",
    "webhook.circuit_breaker_reset": "Webhook circuit breaker reset"
}