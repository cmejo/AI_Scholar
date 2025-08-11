"""
Real-time Intelligence Service
Provides live document processing, streaming analytics, smart notifications,
and dynamic knowledge graph updates with real-time capabilities.
"""
import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
from collections import defaultdict, deque
import threading
import time

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, or_

from core.database import (
    get_db, Document, DocumentChunk, DocumentTag, AnalyticsEvent,
    User, UserProfile, KGEntity, KGRelationship
)
from services.multimodal_processor import MultiModalProcessor
from services.knowledge_graph import KnowledgeGraphService
from services.advanced_analytics import AdvancedAnalyticsService

logger = logging.getLogger(__name__)

class NotificationType(str, Enum):
    """Smart notification types"""
    NEW_DOCUMENT = "new_document"
    RELEVANT_CONTENT = "relevant_content"
    KNOWLEDGE_UPDATE = "knowledge_update"
    RESEARCH_OPPORTUNITY = "research_opportunity"
    COLLABORATION_INVITE = "collaboration_invite"
    SYSTEM_ALERT = "system_alert"
    TREND_ALERT = "trend_alert"
    DEADLINE_REMINDER = "deadline_reminder"

class ProcessingPriority(str, Enum):
    """Real-time processing priority levels"""
    IMMEDIATE = "immediate"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"

@dataclass
class RealTimeEvent:
    """Real-time event structure"""
    id: str
    event_type: str
    user_id: str
    data: Dict[str, Any]
    timestamp: datetime
    priority: ProcessingPriority
    processed: bool = False

@dataclass
class SmartNotification:
    """Smart notification structure"""
    id: str
    user_id: str
    notification_type: NotificationType
    title: str
    message: str
    data: Dict[str, Any]
    priority: int  # 1-5, 5 being highest
    created_at: datetime
    read: bool = False
    action_url: Optional[str] = None
    expires_at: Optional[datetime] = None

@dataclass
class LiveProcessingJob:
    """Live document processing job"""
    id: str
    user_id: str
    document_id: str
    file_path: str
    priority: ProcessingPriority
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None

class RealTimeIntelligenceService:
    """Main real-time intelligence service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.multimodal_service = MultiModalProcessor(db)
        self.kg_service = KnowledgeGraphService(db)
        self.analytics_service = AdvancedAnalyticsService(db)
        
        # Real-time components
        self.active_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.user_subscriptions: Dict[str, Set[str]] = defaultdict(set)  # user_id -> event_types
        self.event_queue: deque = deque(maxlen=10000)
        self.processing_queue: Dict[ProcessingPriority, deque] = {
            priority: deque() for priority in ProcessingPriority
        }
        
        # Notification system
        self.user_notifications: Dict[str, List[SmartNotification]] = defaultdict(list)
        self.notification_rules: Dict[str, List[Callable]] = defaultdict(list)
        
        # Live processing
        self.active_jobs: Dict[str, LiveProcessingJob] = {}
        self.processing_workers: Dict[ProcessingPriority, bool] = {
            priority: False for priority in ProcessingPriority
        }
        
        # Analytics streaming
        self.analytics_streams: Dict[str, Dict[str, Any]] = {}
        self.metric_buffers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Knowledge graph updates
        self.kg_update_queue: deque = deque(maxlen=1000)
        self.entity_watchers: Dict[str, Set[str]] = defaultdict(set)  # entity_id -> user_ids
        
        # System state
        self.service_running = False
        self.last_heartbeat = datetime.utcnow()

    async def start_service(self):
        """Start the real-time intelligence service"""
        try:
            self.service_running = True
            
            # Start background tasks
            asyncio.create_task(self._event_processor())
            asyncio.create_task(self._notification_processor())
            asyncio.create_task(self._analytics_streamer())
            asyncio.create_task(self._kg_updater())
            asyncio.create_task(self._heartbeat_monitor())
            
            # Start processing workers
            for priority in ProcessingPriority:
                asyncio.create_task(self._processing_worker(priority))
            
            logger.info("Real-time intelligence service started")
            
        except Exception as e:
            logger.error(f"Error starting real-time service: {str(e)}")
            raise

    async def connect_user(
        self,
        user_id: str,
        websocket: websockets.WebSocketServerProtocol,
        subscriptions: List[str] = None
    ) -> bool:
        """Connect user for real-time updates"""
        try:
            # Store connection
            self.active_connections[user_id] = websocket
            
            # Set subscriptions
            if subscriptions:
                self.user_subscriptions[user_id] = set(subscriptions)
            else:
                # Default subscriptions
                self.user_subscriptions[user_id] = {
                    "document_processed", "knowledge_updated", "notification",
                    "analytics_update", "collaboration_update"
                }
            
            # Send welcome message
            await self._send_to_user(user_id, {
                "type": "connection_established",
                "subscriptions": list(self.user_subscriptions[user_id]),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Start user-specific analytics stream
            await self._start_user_analytics_stream(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting user {user_id}: {str(e)}")
            return False

    async def disconnect_user(self, user_id: str):
        """Disconnect user from real-time updates"""
        try:
            # Remove connection
            if user_id in self.active_connections:
                del self.active_connections[user_id]
            
            # Clear subscriptions
            if user_id in self.user_subscriptions:
                del self.user_subscriptions[user_id]
            
            # Stop analytics stream
            if user_id in self.analytics_streams:
                del self.analytics_streams[user_id]
            
        except Exception as e:
            logger.error(f"Error disconnecting user {user_id}: {str(e)}")

    async def process_document_live(
        self,
        user_id: str,
        document_id: str,
        file_path: str,
        priority: ProcessingPriority = ProcessingPriority.NORMAL
    ) -> str:
        """Queue document for live processing"""
        try:
            job_id = str(uuid.uuid4())
            
            job = LiveProcessingJob(
                id=job_id,
                user_id=user_id,
                document_id=document_id,
                file_path=file_path,
                priority=priority,
                created_at=datetime.utcnow()
            )
            
            # Add to processing queue
            self.processing_queue[priority].append(job)
            self.active_jobs[job_id] = job
            
            # Notify user
            await self._emit_event(RealTimeEvent(
                id=str(uuid.uuid4()),
                event_type="document_queued",
                user_id=user_id,
                data={
                    "job_id": job_id,
                    "document_id": document_id,
                    "priority": priority.value,
                    "queue_position": len(self.processing_queue[priority])
                },
                timestamp=datetime.utcnow(),
                priority=priority
            ))
            
            return job_id
            
        except Exception as e:
            logger.error(f"Error queuing document for live processing: {str(e)}")
            raise

    async def create_smart_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Dict[str, Any] = None,
        priority: int = 3,
        action_url: str = None,
        expires_in_hours: int = 24
    ) -> SmartNotification:
        """Create a smart notification"""
        try:
            notification_id = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
            
            notification = SmartNotification(
                id=notification_id,
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                data=data or {},
                priority=priority,
                created_at=datetime.utcnow(),
                action_url=action_url,
                expires_at=expires_at
            )
            
            # Store notification
            self.user_notifications[user_id].append(notification)
            
            # Keep only recent notifications
            self.user_notifications[user_id] = self.user_notifications[user_id][-100:]
            
            # Send real-time notification
            await self._emit_event(RealTimeEvent(
                id=str(uuid.uuid4()),
                event_type="notification",
                user_id=user_id,
                data=asdict(notification),
                timestamp=datetime.utcnow(),
                priority=ProcessingPriority.HIGH if priority >= 4 else ProcessingPriority.NORMAL
            ))
            
            return notification
            
        except Exception as e:
            logger.error(f"Error creating smart notification: {str(e)}")
            raise

    async def update_knowledge_graph_live(
        self,
        user_id: str,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ):
        """Update knowledge graph with real-time notifications"""
        try:
            # Queue KG update
            update_data = {
                "user_id": user_id,
                "entities": entities,
                "relationships": relationships,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.kg_update_queue.append(update_data)
            
            # Notify watchers
            affected_entities = [e.get("id") for e in entities if e.get("id")]
            for entity_id in affected_entities:
                watchers = self.entity_watchers.get(entity_id, set())
                for watcher_id in watchers:
                    await self._emit_event(RealTimeEvent(
                        id=str(uuid.uuid4()),
                        event_type="knowledge_updated",
                        user_id=watcher_id,
                        data={
                            "entity_id": entity_id,
                            "update_type": "entity_modified",
                            "source_user": user_id
                        },
                        timestamp=datetime.utcnow(),
                        priority=ProcessingPriority.NORMAL
                    ))
            
        except Exception as e:
            logger.error(f"Error updating knowledge graph live: {str(e)}")

    async def stream_analytics_update(
        self,
        user_id: str,
        metric_name: str,
        value: Any,
        metadata: Dict[str, Any] = None
    ):
        """Stream analytics update to user"""
        try:
            # Add to metric buffer
            self.metric_buffers[f"{user_id}:{metric_name}"].append({
                "value": value,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            })
            
            # Send real-time update
            await self._emit_event(RealTimeEvent(
                id=str(uuid.uuid4()),
                event_type="analytics_update",
                user_id=user_id,
                data={
                    "metric_name": metric_name,
                    "value": value,
                    "metadata": metadata
                },
                timestamp=datetime.utcnow(),
                priority=ProcessingPriority.LOW
            ))
            
        except Exception as e:
            logger.error(f"Error streaming analytics update: {str(e)}")

    async def add_entity_watcher(self, user_id: str, entity_id: str):
        """Add user as watcher for entity updates"""
        self.entity_watchers[entity_id].add(user_id)

    async def remove_entity_watcher(self, user_id: str, entity_id: str):
        """Remove user as watcher for entity updates"""
        self.entity_watchers[entity_id].discard(user_id)

    # Background processing methods
    async def _event_processor(self):
        """Process real-time events"""
        while self.service_running:
            try:
                if self.event_queue:
                    event = self.event_queue.popleft()
                    await self._process_event(event)
                else:
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error in event processor: {str(e)}")
                await asyncio.sleep(1)

    async def _process_event(self, event: RealTimeEvent):
        """Process a single real-time event"""
        try:
            # Send to subscribed users
            if event.user_id in self.user_subscriptions:
                if event.event_type in self.user_subscriptions[event.user_id]:
                    await self._send_to_user(event.user_id, {
                        "type": event.event_type,
                        "data": event.data,
                        "timestamp": event.timestamp.isoformat(),
                        "id": event.id
                    })
            
            # Mark as processed
            event.processed = True
            
        except Exception as e:
            logger.error(f"Error processing event {event.id}: {str(e)}")

    async def _processing_worker(self, priority: ProcessingPriority):
        """Worker for processing documents by priority"""
        while self.service_running:
            try:
                if self.processing_queue[priority]:
                    job = self.processing_queue[priority].popleft()
                    await self._process_document_job(job)
                else:
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Error in {priority.value} processing worker: {str(e)}")
                await asyncio.sleep(1)

    async def _process_document_job(self, job: LiveProcessingJob):
        """Process a document job"""
        try:
            job.status = "processing"
            job.started_at = datetime.utcnow()
            job.progress = 0.1
            
            # Notify start
            await self._emit_event(RealTimeEvent(
                id=str(uuid.uuid4()),
                event_type="document_processing_started",
                user_id=job.user_id,
                data={
                    "job_id": job.id,
                    "document_id": job.document_id
                },
                timestamp=datetime.utcnow(),
                priority=job.priority
            ))
            
            # Process with multimodal service
            result = await self.multimodal_service.process_content(
                file_path=job.file_path,
                user_id=job.user_id
            )
            
            job.progress = 0.8
            
            # Update knowledge graph if entities found
            if result.metadata.get("entities"):
                await self.update_knowledge_graph_live(
                    job.user_id,
                    result.metadata["entities"],
                    result.metadata.get("relationships", [])
                )
            
            job.progress = 1.0
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.result = {
                "extracted_text": result.extracted_text,
                "confidence": result.confidence_score,
                "metadata": result.metadata
            }
            
            # Notify completion
            await self._emit_event(RealTimeEvent(
                id=str(uuid.uuid4()),
                event_type="document_processed",
                user_id=job.user_id,
                data={
                    "job_id": job.id,
                    "document_id": job.document_id,
                    "result": job.result,
                    "processing_time": (job.completed_at - job.started_at).total_seconds()
                },
                timestamp=datetime.utcnow(),
                priority=job.priority
            ))
            
            # Create smart notification for important content
            if result.confidence_score > 0.8:
                await self.create_smart_notification(
                    job.user_id,
                    NotificationType.NEW_DOCUMENT,
                    "Document Processed Successfully",
                    f"High-quality content extracted with {result.confidence_score:.1%} confidence",
                    {"document_id": job.document_id, "job_id": job.id},
                    priority=4
                )
            
        except Exception as e:
            logger.error(f"Error processing document job {job.id}: {str(e)}")
            job.status = "failed"
            job.completed_at = datetime.utcnow()
            
            await self._emit_event(RealTimeEvent(
                id=str(uuid.uuid4()),
                event_type="document_processing_failed",
                user_id=job.user_id,
                data={
                    "job_id": job.id,
                    "document_id": job.document_id,
                    "error": str(e)
                },
                timestamp=datetime.utcnow(),
                priority=job.priority
            ))

    async def _notification_processor(self):
        """Process and clean up notifications"""
        while self.service_running:
            try:
                current_time = datetime.utcnow()
                
                # Clean up expired notifications
                for user_id in list(self.user_notifications.keys()):
                    notifications = self.user_notifications[user_id]
                    active_notifications = [
                        n for n in notifications
                        if not n.expires_at or n.expires_at > current_time
                    ]
                    self.user_notifications[user_id] = active_notifications
                
                await asyncio.sleep(300)  # Clean up every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in notification processor: {str(e)}")
                await asyncio.sleep(60)

    async def _analytics_streamer(self):
        """Stream analytics updates"""
        while self.service_running:
            try:
                # Process analytics streams
                for user_id, stream_config in self.analytics_streams.items():
                    if stream_config.get("active", False):
                        await self._generate_analytics_update(user_id, stream_config)
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in analytics streamer: {str(e)}")
                await asyncio.sleep(10)

    async def _generate_analytics_update(self, user_id: str, stream_config: Dict[str, Any]):
        """Generate analytics update for user"""
        try:
            # Get recent metrics
            metrics = {}
            for metric_name in stream_config.get("metrics", []):
                buffer_key = f"{user_id}:{metric_name}"
                if buffer_key in self.metric_buffers:
                    recent_values = list(self.metric_buffers[buffer_key])[-10:]  # Last 10 values
                    if recent_values:
                        metrics[metric_name] = {
                            "current": recent_values[-1]["value"],
                            "trend": recent_values,
                            "count": len(recent_values)
                        }
            
            if metrics:
                await self.stream_analytics_update(
                    user_id,
                    "dashboard_update",
                    metrics,
                    {"stream_id": stream_config.get("id")}
                )
                
        except Exception as e:
            logger.error(f"Error generating analytics update: {str(e)}")

    async def _kg_updater(self):
        """Process knowledge graph updates"""
        while self.service_running:
            try:
                if self.kg_update_queue:
                    update_data = self.kg_update_queue.popleft()
                    await self._process_kg_update(update_data)
                else:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in KG updater: {str(e)}")
                await asyncio.sleep(5)

    async def _process_kg_update(self, update_data: Dict[str, Any]):
        """Process knowledge graph update"""
        try:
            user_id = update_data["user_id"]
            entities = update_data["entities"]
            relationships = update_data["relationships"]
            
            # Update knowledge graph
            for entity in entities:
                await self.kg_service.add_entity(
                    user_id=user_id,
                    name=entity["name"],
                    entity_type=entity.get("type", "unknown"),
                    properties=entity.get("properties", {})
                )
            
            for relationship in relationships:
                await self.kg_service.add_relationship(
                    user_id=user_id,
                    source_entity=relationship["source"],
                    target_entity=relationship["target"],
                    relationship_type=relationship.get("type", "related"),
                    properties=relationship.get("properties", {})
                )
            
        except Exception as e:
            logger.error(f"Error processing KG update: {str(e)}")

    async def _heartbeat_monitor(self):
        """Monitor service health"""
        while self.service_running:
            try:
                self.last_heartbeat = datetime.utcnow()
                
                # Check connection health
                dead_connections = []
                for user_id, websocket in self.active_connections.items():
                    try:
                        await websocket.ping()
                    except:
                        dead_connections.append(user_id)
                
                # Clean up dead connections
                for user_id in dead_connections:
                    await self.disconnect_user(user_id)
                
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {str(e)}")
                await asyncio.sleep(30)

    async def _start_user_analytics_stream(self, user_id: str):
        """Start analytics stream for user"""
        try:
            stream_id = str(uuid.uuid4())
            
            self.analytics_streams[user_id] = {
                "id": stream_id,
                "active": True,
                "metrics": [
                    "document_count",
                    "processing_queue_size",
                    "knowledge_entities",
                    "recent_activity"
                ],
                "started_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error starting analytics stream: {str(e)}")

    # Utility methods
    async def _emit_event(self, event: RealTimeEvent):
        """Emit a real-time event"""
        self.event_queue.append(event)

    async def _send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to specific user"""
        try:
            websocket = self.active_connections.get(user_id)
            if websocket:
                await websocket.send(json.dumps(message, default=str))
                
        except Exception as e:
            logger.warning(f"Failed to send message to user {user_id}: {str(e)}")
            # Remove dead connection
            await self.disconnect_user(user_id)

    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service_running": self.service_running,
            "active_connections": len(self.active_connections),
            "total_subscriptions": sum(len(subs) for subs in self.user_subscriptions.values()),
            "event_queue_size": len(self.event_queue),
            "processing_queues": {
                priority.value: len(queue) 
                for priority, queue in self.processing_queue.items()
            },
            "active_jobs": len(self.active_jobs),
            "analytics_streams": len(self.analytics_streams),
            "kg_update_queue_size": len(self.kg_update_queue),
            "last_heartbeat": self.last_heartbeat.isoformat()
        }

# Export classes
__all__ = [
    'RealTimeIntelligenceService',
    'RealTimeEvent',
    'SmartNotification',
    'LiveProcessingJob',
    'NotificationType',
    'ProcessingPriority'
]