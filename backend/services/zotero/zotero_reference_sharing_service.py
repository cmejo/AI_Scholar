"""
Zotero Reference Sharing Service

Handles reference sharing between AI Scholar users, shared collections, and collaborative features.
"""
import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from models.zotero_models import (
    ZoteroItem, ZoteroUserReferenceShare, ZoteroSharedReferenceCollection,
    ZoteroCollectionCollaborator, ZoteroSharedCollectionReference,
    ZoteroReferenceDiscussion, ZoteroSharedReferenceAnnotation,
    ZoteroSharingActivityLog, ZoteroReferenceSharingInvitation,
    ZoteroSharingNotification
)
from core.database import get_db

logger = logging.getLogger(__name__)


class ZoteroReferenceSharingService:
    """Service for managing reference sharing and collaboration"""
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
    
    async def share_reference_with_user(
        self, reference_id: str, owner_user_id: str, shared_with_user_id: str,
        permission_level: str = 'read', share_message: str = None,
        share_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Share a reference with another user"""
        try:
            # Check if reference exists
            reference = self.db.query(ZoteroItem).filter(ZoteroItem.id == reference_id).first()
            if not reference:
                raise ValueError("Reference not found")
            
            # Check if already shared
            existing_share = self.db.query(ZoteroUserReferenceShare).filter(
                and_(
                    ZoteroUserReferenceShare.reference_id == reference_id,
                    ZoteroUserReferenceShare.owner_user_id == owner_user_id,
                    ZoteroUserReferenceShare.shared_with_user_id == shared_with_user_id,
                    ZoteroUserReferenceShare.is_active == True
                )
            ).first()
            
            if existing_share:
                # Update existing share
                existing_share.permission_level = permission_level
                existing_share.share_message = share_message
                existing_share.share_context = share_context or {}
                existing_share.updated_at = datetime.utcnow()
                
                self.db.commit()
                
                share_id = existing_share.id
                action = 'updated'
            else:
                # Create new share
                share = ZoteroUserReferenceShare(
                    reference_id=reference_id,
                    owner_user_id=owner_user_id,
                    shared_with_user_id=shared_with_user_id,
                    permission_level=permission_level,
                    share_message=share_message,
                    share_context=share_context or {}
                )
                
                self.db.add(share)
                self.db.commit()
                self.db.refresh(share)
                
                share_id = share.id
                action = 'created'
            
            # Log activity
            await self._log_sharing_activity(
                owner_user_id, 'share_reference', 'reference', reference_id,
                target_user_id=shared_with_user_id,
                description=f"Shared reference '{reference.title}' with user {shared_with_user_id}",
                activity_data={'permission_level': permission_level, 'action': action}
            )
            
            # Create notification for recipient
            await self._create_notification(
                shared_with_user_id, 'reference_shared',
                f"Reference shared: {reference.title}",
                f"User {owner_user_id} shared a reference with you",
                'reference', reference_id, owner_user_id
            )
            
            return {
                'share_id': share_id,
                'reference_id': reference_id,
                'shared_with_user_id': shared_with_user_id,
                'permission_level': permission_level,
                'action': action
            }
            
        except Exception as e:
            logger.error(f"Failed to share reference: {str(e)}")
            raise
    
    async def get_shared_references(self, user_id: str, as_owner: bool = True) -> List[Dict[str, Any]]:
        """Get references shared by or with a user"""
        try:
            if as_owner:
                # References shared by the user
                shares = self.db.query(ZoteroUserReferenceShare).join(
                    ZoteroItem, ZoteroUserReferenceShare.reference_id == ZoteroItem.id
                ).filter(
                    and_(
                        ZoteroUserReferenceShare.owner_user_id == user_id,
                        ZoteroUserReferenceShare.is_active == True
                    )
                ).all()
            else:
                # References shared with the user
                shares = self.db.query(ZoteroUserReferenceShare).join(
                    ZoteroItem, ZoteroUserReferenceShare.reference_id == ZoteroItem.id
                ).filter(
                    and_(
                        ZoteroUserReferenceShare.shared_with_user_id == user_id,
                        ZoteroUserReferenceShare.is_active == True
                    )
                ).all()
            
            result = []
            for share in shares:
                reference = self.db.query(ZoteroItem).filter(ZoteroItem.id == share.reference_id).first()
                if reference:
                    result.append({
                        'share_id': share.id,
                        'reference_id': share.reference_id,
                        'reference_title': reference.title,
                        'reference_authors': reference.creators,
                        'reference_year': reference.publication_year,
                        'owner_user_id': share.owner_user_id,
                        'shared_with_user_id': share.shared_with_user_id,
                        'permission_level': share.permission_level,
                        'share_message': share.share_message,
                        'created_at': share.created_at,
                        'updated_at': share.updated_at
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get shared references: {str(e)}")
            raise
    
    async def create_shared_collection(
        self, name: str, owner_user_id: str, description: str = None,
        collection_type: str = 'research_project', is_public: bool = False,
        collaboration_settings: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a new shared reference collection"""
        try:
            # Generate access code if needed
            access_code = None
            if is_public:
                access_code = self._generate_access_code()
            
            collection = ZoteroSharedReferenceCollection(
                name=name,
                description=description,
                owner_user_id=owner_user_id,
                collection_type=collection_type,
                is_public=is_public,
                access_code=access_code,
                visibility='public' if is_public else 'private',
                collaboration_settings=collaboration_settings or {}
            )
            
            self.db.add(collection)
            self.db.commit()
            self.db.refresh(collection)
            
            # Add owner as admin collaborator
            owner_collaborator = ZoteroCollectionCollaborator(
                collection_id=collection.id,
                user_id=owner_user_id,
                permission_level='admin',
                role='owner',
                invited_by=owner_user_id,
                invitation_status='accepted',
                joined_at=datetime.utcnow()
            )
            
            self.db.add(owner_collaborator)
            self.db.commit()
            
            # Log activity
            await self._log_sharing_activity(
                owner_user_id, 'create_collection', 'collection', collection.id,
                description=f"Created shared collection '{name}'",
                activity_data={'collection_type': collection_type, 'is_public': is_public}
            )
            
            return {
                'collection_id': collection.id,
                'name': name,
                'access_code': access_code,
                'is_public': is_public,
                'created_at': collection.created_at
            }
            
        except Exception as e:
            logger.error(f"Failed to create shared collection: {str(e)}")
            raise
    
    async def add_collaborator_to_collection(
        self, collection_id: str, user_id: str, invited_by: str,
        permission_level: str = 'read', role: str = 'collaborator',
        invitation_message: str = None
    ) -> Dict[str, Any]:
        """Add a collaborator to a shared collection"""
        try:
            # Check if collection exists and user has permission to add collaborators
            collection = self.db.query(ZoteroSharedReferenceCollection).filter(
                ZoteroSharedReferenceCollection.id == collection_id
            ).first()
            
            if not collection:
                raise ValueError("Collection not found")
            
            # Check if inviter has permission
            inviter_collaborator = self.db.query(ZoteroCollectionCollaborator).filter(
                and_(
                    ZoteroCollectionCollaborator.collection_id == collection_id,
                    ZoteroCollectionCollaborator.user_id == invited_by,
                    ZoteroCollectionCollaborator.invitation_status == 'accepted'
                )
            ).first()
            
            if not inviter_collaborator or inviter_collaborator.permission_level not in ['admin', 'edit']:
                raise PermissionError("User does not have permission to add collaborators")
            
            # Check if user is already a collaborator
            existing_collaborator = self.db.query(ZoteroCollectionCollaborator).filter(
                and_(
                    ZoteroCollectionCollaborator.collection_id == collection_id,
                    ZoteroCollectionCollaborator.user_id == user_id
                )
            ).first()
            
            if existing_collaborator:
                if existing_collaborator.invitation_status == 'accepted':
                    raise ValueError("User is already a collaborator")
                else:
                    # Update existing invitation
                    existing_collaborator.permission_level = permission_level
                    existing_collaborator.role = role
                    existing_collaborator.invitation_message = invitation_message
                    existing_collaborator.invitation_status = 'pending'
                    existing_collaborator.updated_at = datetime.utcnow()
                    
                    collaborator_id = existing_collaborator.id
            else:
                # Create new collaborator invitation
                collaborator = ZoteroCollectionCollaborator(
                    collection_id=collection_id,
                    user_id=user_id,
                    permission_level=permission_level,
                    role=role,
                    invited_by=invited_by,
                    invitation_message=invitation_message,
                    invitation_status='pending'
                )
                
                self.db.add(collaborator)
                self.db.commit()
                self.db.refresh(collaborator)
                
                collaborator_id = collaborator.id
            
            self.db.commit()
            
            # Log activity
            await self._log_sharing_activity(
                invited_by, 'add_collaborator', 'collection', collection_id,
                target_user_id=user_id,
                description=f"Added collaborator to collection '{collection.name}'",
                activity_data={'permission_level': permission_level, 'role': role}
            )
            
            # Create notification for invited user
            await self._create_notification(
                user_id, 'collection_invite',
                f"Collection invitation: {collection.name}",
                f"You've been invited to collaborate on '{collection.name}'",
                'collection', collection_id, invited_by
            )
            
            return {
                'collaborator_id': collaborator_id,
                'collection_id': collection_id,
                'user_id': user_id,
                'permission_level': permission_level,
                'role': role,
                'invitation_status': 'pending'
            }
            
        except Exception as e:
            logger.error(f"Failed to add collaborator: {str(e)}")
            raise
    
    async def add_reference_to_collection(
        self, collection_id: str, reference_id: str, added_by: str,
        notes: str = None, tags: List[str] = None, is_featured: bool = False
    ) -> Dict[str, Any]:
        """Add a reference to a shared collection"""
        try:
            # Check if collection exists and user has permission
            collection = self.db.query(ZoteroSharedReferenceCollection).filter(
                ZoteroSharedReferenceCollection.id == collection_id
            ).first()
            
            if not collection:
                raise ValueError("Collection not found")
            
            # Check user permission
            collaborator = self.db.query(ZoteroCollectionCollaborator).filter(
                and_(
                    ZoteroCollectionCollaborator.collection_id == collection_id,
                    ZoteroCollectionCollaborator.user_id == added_by,
                    ZoteroCollectionCollaborator.invitation_status == 'accepted'
                )
            ).first()
            
            if not collaborator or collaborator.permission_level not in ['admin', 'edit']:
                raise PermissionError("User does not have permission to add references")
            
            # Check if reference exists
            reference = self.db.query(ZoteroItem).filter(ZoteroItem.id == reference_id).first()
            if not reference:
                raise ValueError("Reference not found")
            
            # Check if reference is already in collection
            existing_ref = self.db.query(ZoteroSharedCollectionReference).filter(
                and_(
                    ZoteroSharedCollectionReference.collection_id == collection_id,
                    ZoteroSharedCollectionReference.reference_id == reference_id
                )
            ).first()
            
            if existing_ref:
                raise ValueError("Reference is already in this collection")
            
            # Add reference to collection
            collection_ref = ZoteroSharedCollectionReference(
                collection_id=collection_id,
                reference_id=reference_id,
                added_by=added_by,
                notes=notes,
                tags=tags or [],
                is_featured=is_featured
            )
            
            self.db.add(collection_ref)
            self.db.commit()
            self.db.refresh(collection_ref)
            
            # Log activity
            await self._log_sharing_activity(
                added_by, 'add_reference', 'collection', collection_id,
                description=f"Added reference '{reference.title}' to collection '{collection.name}'",
                activity_data={'reference_id': reference_id, 'is_featured': is_featured}
            )
            
            return {
                'collection_reference_id': collection_ref.id,
                'collection_id': collection_id,
                'reference_id': reference_id,
                'added_by': added_by,
                'added_at': collection_ref.added_at
            }
            
        except Exception as e:
            logger.error(f"Failed to add reference to collection: {str(e)}")
            raise
    
    async def get_user_collections(self, user_id: str) -> List[Dict[str, Any]]:
        """Get collections accessible to a user"""
        try:
            # Get collections where user is a collaborator
            collaborations = self.db.query(ZoteroCollectionCollaborator).join(
                ZoteroSharedReferenceCollection,
                ZoteroCollectionCollaborator.collection_id == ZoteroSharedReferenceCollection.id
            ).filter(
                and_(
                    ZoteroCollectionCollaborator.user_id == user_id,
                    ZoteroCollectionCollaborator.invitation_status == 'accepted'
                )
            ).all()
            
            result = []
            for collaboration in collaborations:
                collection = self.db.query(ZoteroSharedReferenceCollection).filter(
                    ZoteroSharedReferenceCollection.id == collaboration.collection_id
                ).first()
                
                if collection:
                    # Get reference count
                    ref_count = self.db.query(ZoteroSharedCollectionReference).filter(
                        ZoteroSharedCollectionReference.collection_id == collection.id
                    ).count()
                    
                    # Get collaborator count
                    collab_count = self.db.query(ZoteroCollectionCollaborator).filter(
                        and_(
                            ZoteroCollectionCollaborator.collection_id == collection.id,
                            ZoteroCollectionCollaborator.invitation_status == 'accepted'
                        )
                    ).count()
                    
                    result.append({
                        'collection_id': collection.id,
                        'name': collection.name,
                        'description': collection.description,
                        'collection_type': collection.collection_type,
                        'owner_user_id': collection.owner_user_id,
                        'is_public': collection.is_public,
                        'visibility': collection.visibility,
                        'user_role': collaboration.role,
                        'user_permission_level': collaboration.permission_level,
                        'reference_count': ref_count,
                        'collaborator_count': collab_count,
                        'created_at': collection.created_at,
                        'updated_at': collection.updated_at
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get user collections: {str(e)}")
            raise
    
    async def get_collection_references(
        self, collection_id: str, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get references in a shared collection"""
        try:
            # Check if user has access to collection
            collaborator = self.db.query(ZoteroCollectionCollaborator).filter(
                and_(
                    ZoteroCollectionCollaborator.collection_id == collection_id,
                    ZoteroCollectionCollaborator.user_id == user_id,
                    ZoteroCollectionCollaborator.invitation_status == 'accepted'
                )
            ).first()
            
            if not collaborator:
                raise PermissionError("User does not have access to this collection")
            
            # Get references
            collection_refs = self.db.query(ZoteroSharedCollectionReference).join(
                ZoteroItem, ZoteroSharedCollectionReference.reference_id == ZoteroItem.id
            ).filter(
                ZoteroSharedCollectionReference.collection_id == collection_id
            ).order_by(
                desc(ZoteroSharedCollectionReference.is_featured),
                ZoteroSharedCollectionReference.sort_order,
                desc(ZoteroSharedCollectionReference.added_at)
            ).limit(limit).offset(offset).all()
            
            result = []
            for collection_ref in collection_refs:
                reference = self.db.query(ZoteroItem).filter(
                    ZoteroItem.id == collection_ref.reference_id
                ).first()
                
                if reference:
                    result.append({
                        'collection_reference_id': collection_ref.id,
                        'reference_id': reference.id,
                        'reference_title': reference.title,
                        'reference_authors': reference.creators,
                        'reference_year': reference.publication_year,
                        'reference_doi': reference.doi,
                        'added_by': collection_ref.added_by,
                        'added_at': collection_ref.added_at,
                        'notes': collection_ref.notes,
                        'tags': collection_ref.tags,
                        'is_featured': collection_ref.is_featured,
                        'sort_order': collection_ref.sort_order
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get collection references: {str(e)}")
            raise
    
    async def add_reference_discussion(
        self, reference_id: str, user_id: str, content: str,
        discussion_type: str = 'comment', collection_id: str = None,
        parent_discussion_id: str = None
    ) -> Dict[str, Any]:
        """Add a discussion comment to a reference"""
        try:
            # Check if reference exists
            reference = self.db.query(ZoteroItem).filter(ZoteroItem.id == reference_id).first()
            if not reference:
                raise ValueError("Reference not found")
            
            # If collection_id is provided, check user has access
            if collection_id:
                collaborator = self.db.query(ZoteroCollectionCollaborator).filter(
                    and_(
                        ZoteroCollectionCollaborator.collection_id == collection_id,
                        ZoteroCollectionCollaborator.user_id == user_id,
                        ZoteroCollectionCollaborator.invitation_status == 'accepted'
                    )
                ).first()
                
                if not collaborator:
                    raise PermissionError("User does not have access to this collection")
            
            # Create discussion
            discussion = ZoteroReferenceDiscussion(
                reference_id=reference_id,
                collection_id=collection_id,
                user_id=user_id,
                discussion_type=discussion_type,
                content=content,
                parent_discussion_id=parent_discussion_id
            )
            
            self.db.add(discussion)
            self.db.commit()
            self.db.refresh(discussion)
            
            # Log activity
            await self._log_sharing_activity(
                user_id, 'add_comment', 'reference', reference_id,
                collection_id=collection_id,
                description=f"Added {discussion_type} to reference '{reference.title}'",
                activity_data={'discussion_type': discussion_type, 'parent_id': parent_discussion_id}
            )
            
            return {
                'discussion_id': discussion.id,
                'reference_id': reference_id,
                'user_id': user_id,
                'discussion_type': discussion_type,
                'content': content,
                'created_at': discussion.created_at
            }
            
        except Exception as e:
            logger.error(f"Failed to add reference discussion: {str(e)}")
            raise
    
    async def get_reference_discussions(
        self, reference_id: str, user_id: str, collection_id: str = None
    ) -> List[Dict[str, Any]]:
        """Get discussions for a reference"""
        try:
            # Check access permissions
            if collection_id:
                collaborator = self.db.query(ZoteroCollectionCollaborator).filter(
                    and_(
                        ZoteroCollectionCollaborator.collection_id == collection_id,
                        ZoteroCollectionCollaborator.user_id == user_id,
                        ZoteroCollectionCollaborator.invitation_status == 'accepted'
                    )
                ).first()
                
                if not collaborator:
                    raise PermissionError("User does not have access to this collection")
            
            # Get discussions
            discussions = self.db.query(ZoteroReferenceDiscussion).filter(
                and_(
                    ZoteroReferenceDiscussion.reference_id == reference_id,
                    ZoteroReferenceDiscussion.collection_id == collection_id if collection_id else True
                )
            ).order_by(ZoteroReferenceDiscussion.created_at).all()
            
            result = []
            for discussion in discussions:
                result.append({
                    'discussion_id': discussion.id,
                    'reference_id': discussion.reference_id,
                    'collection_id': discussion.collection_id,
                    'user_id': discussion.user_id,
                    'discussion_type': discussion.discussion_type,
                    'content': discussion.content,
                    'parent_discussion_id': discussion.parent_discussion_id,
                    'is_resolved': discussion.is_resolved,
                    'resolved_by': discussion.resolved_by,
                    'resolved_at': discussion.resolved_at,
                    'created_at': discussion.created_at,
                    'updated_at': discussion.updated_at
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get reference discussions: {str(e)}")
            raise
    
    async def get_user_notifications(
        self, user_id: str, unread_only: bool = False, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        try:
            query = self.db.query(ZoteroSharingNotification).filter(
                ZoteroSharingNotification.user_id == user_id
            )
            
            if unread_only:
                query = query.filter(ZoteroSharingNotification.is_read == False)
            
            notifications = query.order_by(
                desc(ZoteroSharingNotification.created_at)
            ).limit(limit).offset(offset).all()
            
            result = []
            for notification in notifications:
                result.append({
                    'notification_id': notification.id,
                    'notification_type': notification.notification_type,
                    'title': notification.title,
                    'message': notification.message,
                    'target_type': notification.target_type,
                    'target_id': notification.target_id,
                    'sender_user_id': notification.sender_user_id,
                    'is_read': notification.is_read,
                    'is_dismissed': notification.is_dismissed,
                    'action_url': notification.action_url,
                    'created_at': notification.created_at,
                    'read_at': notification.read_at
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get user notifications: {str(e)}")
            raise
    
    async def mark_notification_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        try:
            notification = self.db.query(ZoteroSharingNotification).filter(
                and_(
                    ZoteroSharingNotification.id == notification_id,
                    ZoteroSharingNotification.user_id == user_id
                )
            ).first()
            
            if not notification:
                return False
            
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {str(e)}")
            return False
    
    def _generate_access_code(self, length: int = 8) -> str:
        """Generate a random access code for public collections"""
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    async def _log_sharing_activity(
        self, user_id: str, activity_type: str, target_type: str, target_id: str,
        target_user_id: str = None, collection_id: str = None,
        description: str = None, activity_data: Dict[str, Any] = None,
        ip_address: str = None, user_agent: str = None
    ) -> None:
        """Log sharing activity"""
        
        activity = ZoteroSharingActivityLog(
            user_id=user_id,
            activity_type=activity_type,
            target_type=target_type,
            target_id=target_id,
            target_user_id=target_user_id,
            collection_id=collection_id,
            activity_description=description,
            activity_data=activity_data or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(activity)
        self.db.commit()
    
    async def _create_notification(
        self, user_id: str, notification_type: str, title: str, message: str,
        target_type: str = None, target_id: str = None, sender_user_id: str = None,
        action_url: str = None
    ) -> None:
        """Create a notification for a user"""
        
        notification = ZoteroSharingNotification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            target_type=target_type,
            target_id=target_id,
            sender_user_id=sender_user_id,
            action_url=action_url
        )
        
        self.db.add(notification)
        self.db.commit()