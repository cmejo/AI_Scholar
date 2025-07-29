"""
Collaborative Research Service
Enables real-time multi-user research collaboration with shared workspaces,
live document editing, and collaborative analytics.
"""
import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Set
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, or_

from core.database import (
    get_db, Document, DocumentChunk, DocumentTag, AnalyticsEvent,
    User, UserProfile
)

logger = logging.getLogger(__name__)

class CollaborationRole(str, Enum):
    """Collaboration roles"""
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    REVIEWER = "reviewer"

class ActivityType(str, Enum):
    """Activity types in collaborative space"""
    DOCUMENT_ADDED = "document_added"
    DOCUMENT_EDITED = "document_edited"
    COMMENT_ADDED = "comment_added"
    ANNOTATION_CREATED = "annotation_created"
    RESEARCH_QUESTION_ADDED = "research_question_added"
    HYPOTHESIS_PROPOSED = "hypothesis_proposed"
    METHODOLOGY_SUGGESTED = "methodology_suggested"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"

@dataclass
class ResearchSpace:
    """Collaborative research space"""
    id: str
    name: str
    description: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    research_domain: str
    research_questions: List[str]
    collaborators: List[Dict[str, Any]]
    documents: List[str]  # Document IDs
    shared_annotations: List[Dict[str, Any]]
    activity_log: List[Dict[str, Any]]
    settings: Dict[str, Any]

@dataclass
class Collaborator:
    """Collaborator information"""
    user_id: str
    username: str
    email: str
    role: CollaborationRole
    joined_at: datetime
    last_active: datetime
    permissions: List[str]
    contribution_score: float

@dataclass
class SharedAnnotation:
    """Shared annotation in research space"""
    id: str
    document_id: str
    chunk_id: str
    user_id: str
    annotation_type: str  # highlight, comment, question, insight
    content: str
    position: Dict[str, Any]  # Position in document
    created_at: datetime
    replies: List[Dict[str, Any]]
    tags: List[str]
    visibility: str  # public, private, team

@dataclass
class CollaborativeActivity:
    """Activity in collaborative space"""
    id: str
    space_id: str
    user_id: str
    activity_type: ActivityType
    content: Dict[str, Any]
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class RealTimeUpdate:
    """Real-time update message"""
    type: str
    space_id: str
    user_id: str
    data: Dict[str, Any]
    timestamp: datetime

class CollaborativeResearchService:
    """Main collaborative research service"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Active spaces and connections
        self.active_spaces: Dict[str, ResearchSpace] = {}
        self.active_connections: Dict[str, Set[str]] = defaultdict(set)  # space_id -> user_ids
        self.websocket_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        
        # Collaboration settings
        self.max_collaborators_per_space = 20
        self.activity_retention_days = 90
        
        # Permission mappings
        self.role_permissions = {
            CollaborationRole.OWNER: [
                "create", "read", "update", "delete", "invite", "manage_roles", 
                "export", "archive", "settings"
            ],
            CollaborationRole.ADMIN: [
                "create", "read", "update", "delete", "invite", "export"
            ],
            CollaborationRole.EDITOR: [
                "create", "read", "update", "export"
            ],
            CollaborationRole.VIEWER: [
                "read", "export"
            ],
            CollaborationRole.REVIEWER: [
                "read", "comment", "annotate", "export"
            ]
        }

    async def create_research_space(
        self,
        owner_id: str,
        name: str,
        description: str,
        research_domain: str,
        initial_questions: List[str] = None
    ) -> ResearchSpace:
        """Create a new collaborative research space"""
        try:
            space_id = str(uuid.uuid4())
            
            # Create owner as first collaborator
            owner_collaborator = {
                "user_id": owner_id,
                "role": CollaborationRole.OWNER.value,
                "joined_at": datetime.utcnow().isoformat(),
                "permissions": self.role_permissions[CollaborationRole.OWNER]
            }
            
            space = ResearchSpace(
                id=space_id,
                name=name,
                description=description,
                owner_id=owner_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True,
                research_domain=research_domain,
                research_questions=initial_questions or [],
                collaborators=[owner_collaborator],
                documents=[],
                shared_annotations=[],
                activity_log=[],
                settings={
                    "allow_public_view": False,
                    "require_approval_for_edits": False,
                    "enable_real_time_sync": True,
                    "max_collaborators": self.max_collaborators_per_space
                }
            )
            
            # Store space
            self.active_spaces[space_id] = space
            
            # Log activity
            await self._log_activity(
                space_id, owner_id, ActivityType.USER_JOINED,
                {"action": "created_space", "space_name": name}
            )
            
            # Track analytics
            await self._track_collaboration_event(owner_id, "research_space_created", {
                "space_id": space_id,
                "research_domain": research_domain
            })
            
            return space
            
        except Exception as e:
            logger.error(f"Error creating research space: {str(e)}")
            raise

    async def invite_collaborator(
        self,
        space_id: str,
        inviter_id: str,
        invitee_email: str,
        role: CollaborationRole = CollaborationRole.EDITOR
    ) -> bool:
        """Invite a collaborator to research space"""
        try:
            space = self.active_spaces.get(space_id)
            if not space:
                raise ValueError("Research space not found")
            
            # Check inviter permissions
            if not await self._has_permission(space_id, inviter_id, "invite"):
                raise PermissionError("Insufficient permissions to invite collaborators")
            
            # Check if already a collaborator
            existing_collaborator = next(
                (c for c in space.collaborators if c.get("email") == invitee_email),
                None
            )
            if existing_collaborator:
                return False
            
            # Find user by email
            invitee = self.db.query(User).filter(User.email == invitee_email).first()
            if not invitee:
                # In practice, would send invitation email
                logger.info(f"User with email {invitee_email} not found - would send invitation")
                return False
            
            # Add collaborator
            new_collaborator = {
                "user_id": invitee.id,
                "username": invitee.username,
                "email": invitee.email,
                "role": role.value,
                "joined_at": datetime.utcnow().isoformat(),
                "permissions": self.role_permissions[role]
            }
            
            space.collaborators.append(new_collaborator)
            space.updated_at = datetime.utcnow()
            
            # Log activity
            await self._log_activity(
                space_id, inviter_id, ActivityType.USER_JOINED,
                {"invited_user": invitee.username, "role": role.value}
            )
            
            # Notify all active users in space
            await self._broadcast_update(space_id, {
                "type": "collaborator_added",
                "collaborator": new_collaborator
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error inviting collaborator: {str(e)}")
            raise

    async def add_document_to_space(
        self,
        space_id: str,
        user_id: str,
        document_id: str
    ) -> bool:
        """Add a document to collaborative research space"""
        try:
            space = self.active_spaces.get(space_id)
            if not space:
                raise ValueError("Research space not found")
            
            # Check permissions
            if not await self._has_permission(space_id, user_id, "create"):
                raise PermissionError("Insufficient permissions to add documents")
            
            # Verify document exists and user has access
            document = self.db.query(Document).filter(
                Document.id == document_id,
                Document.user_id == user_id
            ).first()
            
            if not document:
                raise ValueError("Document not found or access denied")
            
            # Add to space if not already present
            if document_id not in space.documents:
                space.documents.append(document_id)
                space.updated_at = datetime.utcnow()
                
                # Log activity
                await self._log_activity(
                    space_id, user_id, ActivityType.DOCUMENT_ADDED,
                    {"document_id": document_id, "document_name": document.name}
                )
                
                # Broadcast update
                await self._broadcast_update(space_id, {
                    "type": "document_added",
                    "document": {
                        "id": document_id,
                        "name": document.name,
                        "added_by": user_id
                    }
                })
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding document to space: {str(e)}")
            raise

    async def create_shared_annotation(
        self,
        space_id: str,
        user_id: str,
        document_id: str,
        chunk_id: str,
        annotation_type: str,
        content: str,
        position: Dict[str, Any],
        tags: List[str] = None
    ) -> SharedAnnotation:
        """Create a shared annotation in research space"""
        try:
            space = self.active_spaces.get(space_id)
            if not space:
                raise ValueError("Research space not found")
            
            # Check permissions
            if not await self._has_permission(space_id, user_id, "annotate"):
                raise PermissionError("Insufficient permissions to create annotations")
            
            annotation = SharedAnnotation(
                id=str(uuid.uuid4()),
                document_id=document_id,
                chunk_id=chunk_id,
                user_id=user_id,
                annotation_type=annotation_type,
                content=content,
                position=position,
                created_at=datetime.utcnow(),
                replies=[],
                tags=tags or [],
                visibility="public"
            )
            
            # Add to space
            space.shared_annotations.append(asdict(annotation))
            space.updated_at = datetime.utcnow()
            
            # Log activity
            await self._log_activity(
                space_id, user_id, ActivityType.ANNOTATION_CREATED,
                {
                    "annotation_id": annotation.id,
                    "document_id": document_id,
                    "type": annotation_type
                }
            )
            
            # Broadcast update
            await self._broadcast_update(space_id, {
                "type": "annotation_created",
                "annotation": asdict(annotation)
            })
            
            return annotation
            
        except Exception as e:
            logger.error(f"Error creating shared annotation: {str(e)}")
            raise

    async def add_research_question(
        self,
        space_id: str,
        user_id: str,
        question: str
    ) -> bool:
        """Add a research question to collaborative space"""
        try:
            space = self.active_spaces.get(space_id)
            if not space:
                raise ValueError("Research space not found")
            
            # Check permissions
            if not await self._has_permission(space_id, user_id, "update"):
                raise PermissionError("Insufficient permissions to add research questions")
            
            if question not in space.research_questions:
                space.research_questions.append(question)
                space.updated_at = datetime.utcnow()
                
                # Log activity
                await self._log_activity(
                    space_id, user_id, ActivityType.RESEARCH_QUESTION_ADDED,
                    {"question": question}
                )
                
                # Broadcast update
                await self._broadcast_update(space_id, {
                    "type": "research_question_added",
                    "question": question,
                    "added_by": user_id
                })
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding research question: {str(e)}")
            raise

    async def get_space_activity(
        self,
        space_id: str,
        user_id: str,
        limit: int = 50
    ) -> List[CollaborativeActivity]:
        """Get activity log for research space"""
        try:
            space = self.active_spaces.get(space_id)
            if not space:
                raise ValueError("Research space not found")
            
            # Check permissions
            if not await self._has_permission(space_id, user_id, "read"):
                raise PermissionError("Insufficient permissions to view activity")
            
            # Return recent activities
            activities = []
            for activity_data in space.activity_log[-limit:]:
                activity = CollaborativeActivity(
                    id=activity_data["id"],
                    space_id=space_id,
                    user_id=activity_data["user_id"],
                    activity_type=ActivityType(activity_data["activity_type"]),
                    content=activity_data["content"],
                    timestamp=datetime.fromisoformat(activity_data["timestamp"]),
                    metadata=activity_data.get("metadata", {})
                )
                activities.append(activity)
            
            return activities
            
        except Exception as e:
            logger.error(f"Error getting space activity: {str(e)}")
            raise

    async def get_collaboration_analytics(
        self,
        space_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Get collaboration analytics for research space"""
        try:
            space = self.active_spaces.get(space_id)
            if not space:
                raise ValueError("Research space not found")
            
            # Check permissions
            if not await self._has_permission(space_id, user_id, "read"):
                raise PermissionError("Insufficient permissions to view analytics")
            
            # Calculate analytics
            analytics = {
                "space_info": {
                    "name": space.name,
                    "created_at": space.created_at.isoformat(),
                    "total_collaborators": len(space.collaborators),
                    "total_documents": len(space.documents),
                    "total_annotations": len(space.shared_annotations),
                    "research_questions": len(space.research_questions)
                },
                "activity_summary": {
                    "total_activities": len(space.activity_log),
                    "activities_last_week": self._count_recent_activities(space, 7),
                    "most_active_users": self._get_most_active_users(space),
                    "activity_types": self._get_activity_type_distribution(space)
                },
                "collaboration_metrics": {
                    "average_response_time": self._calculate_avg_response_time(space),
                    "collaboration_score": self._calculate_collaboration_score(space),
                    "knowledge_sharing_index": self._calculate_knowledge_sharing_index(space)
                },
                "content_metrics": {
                    "annotations_per_document": len(space.shared_annotations) / max(1, len(space.documents)),
                    "questions_per_collaborator": len(space.research_questions) / max(1, len(space.collaborators)),
                    "document_engagement": self._calculate_document_engagement(space)
                }
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting collaboration analytics: {str(e)}")
            raise

    async def join_space_realtime(
        self,
        space_id: str,
        user_id: str,
        websocket: websockets.WebSocketServerProtocol
    ) -> bool:
        """Join research space for real-time collaboration"""
        try:
            space = self.active_spaces.get(space_id)
            if not space:
                return False
            
            # Check if user is collaborator
            is_collaborator = any(
                c["user_id"] == user_id for c in space.collaborators
            )
            if not is_collaborator:
                return False
            
            # Add to active connections
            self.active_connections[space_id].add(user_id)
            self.websocket_connections[f"{space_id}:{user_id}"] = websocket
            
            # Notify other users
            await self._broadcast_update(space_id, {
                "type": "user_joined_realtime",
                "user_id": user_id
            }, exclude_user=user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error joining space realtime: {str(e)}")
            return False

    async def leave_space_realtime(
        self,
        space_id: str,
        user_id: str
    ) -> bool:
        """Leave research space real-time session"""
        try:
            # Remove from active connections
            self.active_connections[space_id].discard(user_id)
            connection_key = f"{space_id}:{user_id}"
            if connection_key in self.websocket_connections:
                del self.websocket_connections[connection_key]
            
            # Notify other users
            await self._broadcast_update(space_id, {
                "type": "user_left_realtime",
                "user_id": user_id
            }, exclude_user=user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error leaving space realtime: {str(e)}")
            return False

    # Helper methods
    async def _has_permission(self, space_id: str, user_id: str, permission: str) -> bool:
        """Check if user has specific permission in space"""
        try:
            space = self.active_spaces.get(space_id)
            if not space:
                return False
            
            # Find user's role
            user_collab = next(
                (c for c in space.collaborators if c["user_id"] == user_id),
                None
            )
            
            if not user_collab:
                return False
            
            return permission in user_collab.get("permissions", [])
            
        except Exception as e:
            logger.error(f"Error checking permission: {str(e)}")
            return False

    async def _log_activity(
        self,
        space_id: str,
        user_id: str,
        activity_type: ActivityType,
        content: Dict[str, Any]
    ):
        """Log activity in research space"""
        try:
            space = self.active_spaces.get(space_id)
            if not space:
                return
            
            activity = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "activity_type": activity_type.value,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {}
            }
            
            space.activity_log.append(activity)
            
            # Keep only recent activities
            if len(space.activity_log) > 1000:
                space.activity_log = space.activity_log[-500:]
            
        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")

    async def _broadcast_update(
        self,
        space_id: str,
        update_data: Dict[str, Any],
        exclude_user: str = None
    ):
        """Broadcast real-time update to all active users in space"""
        try:
            active_users = self.active_connections.get(space_id, set())
            
            update = RealTimeUpdate(
                type="space_update",
                space_id=space_id,
                user_id=exclude_user or "system",
                data=update_data,
                timestamp=datetime.utcnow()
            )
            
            message = json.dumps(asdict(update), default=str)
            
            # Send to all active connections
            for user_id in active_users:
                if user_id != exclude_user:
                    connection_key = f"{space_id}:{user_id}"
                    websocket = self.websocket_connections.get(connection_key)
                    
                    if websocket:
                        try:
                            await websocket.send(message)
                        except Exception as e:
                            logger.warning(f"Failed to send update to {user_id}: {str(e)}")
                            # Remove dead connection
                            self.active_connections[space_id].discard(user_id)
                            if connection_key in self.websocket_connections:
                                del self.websocket_connections[connection_key]
            
        except Exception as e:
            logger.error(f"Error broadcasting update: {str(e)}")

    def _count_recent_activities(self, space: ResearchSpace, days: int) -> int:
        """Count activities in recent days"""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            count = 0
            
            for activity in space.activity_log:
                activity_time = datetime.fromisoformat(activity["timestamp"])
                if activity_time >= cutoff:
                    count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Error counting recent activities: {str(e)}")
            return 0

    def _get_most_active_users(self, space: ResearchSpace) -> List[Dict[str, Any]]:
        """Get most active users in space"""
        try:
            user_activity = defaultdict(int)
            
            for activity in space.activity_log:
                user_activity[activity["user_id"]] += 1
            
            # Sort by activity count
            sorted_users = sorted(
                user_activity.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            result = []
            for user_id, count in sorted_users[:5]:
                # Find user info
                user_collab = next(
                    (c for c in space.collaborators if c["user_id"] == user_id),
                    None
                )
                
                if user_collab:
                    result.append({
                        "user_id": user_id,
                        "username": user_collab.get("username", "Unknown"),
                        "activity_count": count
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting most active users: {str(e)}")
            return []

    def _get_activity_type_distribution(self, space: ResearchSpace) -> Dict[str, int]:
        """Get distribution of activity types"""
        try:
            type_counts = defaultdict(int)
            
            for activity in space.activity_log:
                type_counts[activity["activity_type"]] += 1
            
            return dict(type_counts)
            
        except Exception as e:
            logger.error(f"Error getting activity type distribution: {str(e)}")
            return {}

    def _calculate_avg_response_time(self, space: ResearchSpace) -> float:
        """Calculate average response time between activities"""
        try:
            if len(space.activity_log) < 2:
                return 0.0
            
            response_times = []
            
            for i in range(1, len(space.activity_log)):
                prev_time = datetime.fromisoformat(space.activity_log[i-1]["timestamp"])
                curr_time = datetime.fromisoformat(space.activity_log[i]["timestamp"])
                
                diff_hours = (curr_time - prev_time).total_seconds() / 3600
                if diff_hours < 24:  # Only count responses within 24 hours
                    response_times.append(diff_hours)
            
            return sum(response_times) / len(response_times) if response_times else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating avg response time: {str(e)}")
            return 0.0

    def _calculate_collaboration_score(self, space: ResearchSpace) -> float:
        """Calculate overall collaboration score"""
        try:
            # Factors: number of collaborators, activity frequency, annotation sharing
            collab_factor = min(1.0, len(space.collaborators) / 5)  # Normalize to 5 collaborators
            activity_factor = min(1.0, len(space.activity_log) / 100)  # Normalize to 100 activities
            annotation_factor = min(1.0, len(space.shared_annotations) / 50)  # Normalize to 50 annotations
            
            score = (collab_factor * 0.3 + activity_factor * 0.4 + annotation_factor * 0.3)
            return round(score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating collaboration score: {str(e)}")
            return 0.0

    def _calculate_knowledge_sharing_index(self, space: ResearchSpace) -> float:
        """Calculate knowledge sharing index"""
        try:
            if not space.collaborators:
                return 0.0
            
            # Measure how evenly knowledge sharing is distributed
            user_contributions = defaultdict(int)
            
            for activity in space.activity_log:
                if activity["activity_type"] in ["annotation_created", "research_question_added", "document_added"]:
                    user_contributions[activity["user_id"]] += 1
            
            if not user_contributions:
                return 0.0
            
            # Calculate distribution evenness (higher is better)
            total_contributions = sum(user_contributions.values())
            expected_per_user = total_contributions / len(space.collaborators)
            
            variance = sum(
                (count - expected_per_user) ** 2 
                for count in user_contributions.values()
            ) / len(space.collaborators)
            
            # Convert to index (0-1, where 1 is perfectly even distribution)
            max_variance = expected_per_user ** 2
            evenness = 1 - (variance / max_variance) if max_variance > 0 else 1
            
            return round(max(0, min(1, evenness)), 2)
            
        except Exception as e:
            logger.error(f"Error calculating knowledge sharing index: {str(e)}")
            return 0.0

    def _calculate_document_engagement(self, space: ResearchSpace) -> Dict[str, float]:
        """Calculate engagement metrics for documents"""
        try:
            if not space.documents:
                return {}
            
            doc_engagement = {}
            
            for doc_id in space.documents:
                # Count annotations for this document
                annotations = [
                    ann for ann in space.shared_annotations
                    if ann["document_id"] == doc_id
                ]
                
                # Count activities related to this document
                activities = [
                    act for act in space.activity_log
                    if act["content"].get("document_id") == doc_id
                ]
                
                engagement_score = (len(annotations) * 2 + len(activities)) / len(space.collaborators)
                doc_engagement[doc_id] = round(engagement_score, 2)
            
            return doc_engagement
            
        except Exception as e:
            logger.error(f"Error calculating document engagement: {str(e)}")
            return {}

    async def _track_collaboration_event(self, user_id: str, event_type: str, event_data: Dict[str, Any]):
        """Track collaboration analytics events"""
        try:
            event = AnalyticsEvent(
                user_id=user_id,
                event_type=event_type,
                event_data={
                    **event_data,
                    "timestamp": datetime.utcnow().isoformat(),
                    "service": "collaborative_research"
                }
            )
            
            self.db.add(event)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error tracking collaboration event: {str(e)}")

# Export classes
__all__ = [
    'CollaborativeResearchService',
    'ResearchSpace',
    'Collaborator',
    'SharedAnnotation',
    'CollaborativeActivity',
    'RealTimeUpdate',
    'CollaborationRole',
    'ActivityType'
]