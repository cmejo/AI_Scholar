"""
Zotero Team Collaboration Service

Handles team workspaces, modification tracking, collaborative editing, and conflict resolution.
"""
import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from models.zotero_models import (
    ZoteroTeamWorkspace, ZoteroTeamWorkspaceMember, ZoteroTeamWorkspaceCollection,
    ZoteroModificationTracking, ZoteroCollaborativeEditingSession,
    ZoteroCollaborationConflict, ZoteroTeamCollaborationHistory,
    ZoteroTeamWorkspaceSettings, ZoteroTeamWorkspaceInvitation,
    ZoteroTeamWorkspaceNotification, ZoteroSharedReferenceCollection,
    ZoteroItem
)
from core.database import get_db

logger = logging.getLogger(__name__)


class ZoteroTeamCollaborationService:
    """Service for managing team collaboration and workspaces"""
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
    
    async def create_team_workspace(
        self, name: str, owner_user_id: str, description: str = None,
        workspace_type: str = 'research_team', settings: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a new team workspace"""
        try:
            workspace = ZoteroTeamWorkspace(
                name=name,
                description=description,
                owner_user_id=owner_user_id,
                workspace_type=workspace_type,
                settings=settings or {}
            )
            
            self.db.add(workspace)
            self.db.commit()
            self.db.refresh(workspace)
            
            # Add owner as admin member
            owner_member = ZoteroTeamWorkspaceMember(
                workspace_id=workspace.id,
                user_id=owner_user_id,
                role='owner',
                permissions={'admin': True, 'manage_members': True, 'manage_settings': True},
                invited_by=owner_user_id,
                invitation_status='active',
                joined_at=datetime.utcnow()
            )
            
            self.db.add(owner_member)
            self.db.commit()
            
            # Initialize default settings
            await self._initialize_workspace_settings(workspace.id, owner_user_id)
            
            # Log activity
            await self._log_collaboration_history(
                workspace.id, owner_user_id, 'create_workspace',
                'workspace', workspace.id,
                f"Created team workspace '{name}'",
                {'workspace_type': workspace_type}, 'medium'
            )
            
            return {
                'workspace_id': workspace.id,
                'name': name,
                'workspace_type': workspace_type,
                'created_at': workspace.created_at
            }
            
        except Exception as e:
            logger.error(f"Failed to create team workspace: {str(e)}")
            raise
    
    async def get_user_workspaces(self, user_id: str) -> List[Dict[str, Any]]:
        """Get workspaces accessible to a user"""
        try:
            # Get workspaces where user is a member
            memberships = self.db.query(ZoteroTeamWorkspaceMember).join(
                ZoteroTeamWorkspace,
                ZoteroTeamWorkspaceMember.workspace_id == ZoteroTeamWorkspace.id
            ).filter(
                and_(
                    ZoteroTeamWorkspaceMember.user_id == user_id,
                    ZoteroTeamWorkspaceMember.is_active == True,
                    ZoteroTeamWorkspace.is_active == True
                )
            ).all()
            
            result = []
            for membership in memberships:
                workspace = self.db.query(ZoteroTeamWorkspace).filter(
                    ZoteroTeamWorkspace.id == membership.workspace_id
                ).first()
                
                if workspace:
                    # Get member count
                    member_count = self.db.query(ZoteroTeamWorkspaceMember).filter(
                        and_(
                            ZoteroTeamWorkspaceMember.workspace_id == workspace.id,
                            ZoteroTeamWorkspaceMember.is_active == True
                        )
                    ).count()
                    
                    # Get collection count
                    collection_count = self.db.query(ZoteroTeamWorkspaceCollection).filter(
                        ZoteroTeamWorkspaceCollection.workspace_id == workspace.id
                    ).count()
                    
                    result.append({
                        'workspace_id': workspace.id,
                        'name': workspace.name,
                        'description': workspace.description,
                        'workspace_type': workspace.workspace_type,
                        'owner_user_id': workspace.owner_user_id,
                        'user_role': membership.role,
                        'user_permissions': membership.permissions,
                        'member_count': member_count,
                        'collection_count': collection_count,
                        'last_activity': membership.last_activity,
                        'created_at': workspace.created_at,
                        'updated_at': workspace.updated_at
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get user workspaces: {str(e)}")
            raise
    
    async def add_workspace_member(
        self, workspace_id: str, user_id: str, invited_by: str,
        role: str = 'member', permissions: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Add a member to a team workspace"""
        try:
            # Check if workspace exists and inviter has permission
            workspace = self.db.query(ZoteroTeamWorkspace).filter(
                ZoteroTeamWorkspace.id == workspace_id
            ).first()
            
            if not workspace:
                raise ValueError("Workspace not found")
            
            # Check inviter permissions
            inviter_member = self.db.query(ZoteroTeamWorkspaceMember).filter(
                and_(
                    ZoteroTeamWorkspaceMember.workspace_id == workspace_id,
                    ZoteroTeamWorkspaceMember.user_id == invited_by,
                    ZoteroTeamWorkspaceMember.is_active == True
                )
            ).first()
            
            if not inviter_member or inviter_member.role not in ['owner', 'admin']:
                raise PermissionError("User does not have permission to add members")
            
            # Check if user is already a member
            existing_member = self.db.query(ZoteroTeamWorkspaceMember).filter(
                and_(
                    ZoteroTeamWorkspaceMember.workspace_id == workspace_id,
                    ZoteroTeamWorkspaceMember.user_id == user_id
                )
            ).first()
            
            if existing_member and existing_member.is_active:
                raise ValueError("User is already a member of this workspace")
            
            if existing_member:
                # Reactivate existing member
                existing_member.role = role
                existing_member.permissions = permissions or {}
                existing_member.is_active = True
                existing_member.invited_by = invited_by
                existing_member.invitation_status = 'active'
                existing_member.joined_at = datetime.utcnow()
                existing_member.updated_at = datetime.utcnow()
                
                member_id = existing_member.id
            else:
                # Create new member
                member = ZoteroTeamWorkspaceMember(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    role=role,
                    permissions=permissions or {},
                    invited_by=invited_by,
                    invitation_status='active',
                    joined_at=datetime.utcnow()
                )
                
                self.db.add(member)
                self.db.commit()
                self.db.refresh(member)
                
                member_id = member.id
            
            self.db.commit()
            
            # Log activity
            await self._log_collaboration_history(
                workspace_id, invited_by, 'add_member',
                'member', user_id,
                f"Added member to workspace '{workspace.name}'",
                {'role': role, 'permissions': permissions}, 'medium'
            )
            
            # Create notification for new member
            await self._create_workspace_notification(
                workspace_id, user_id, 'member_added',
                f"Added to workspace: {workspace.name}",
                f"You've been added to the '{workspace.name}' workspace",
                'workspace', workspace_id, invited_by, 'normal'
            )
            
            return {
                'member_id': member_id,
                'workspace_id': workspace_id,
                'user_id': user_id,
                'role': role,
                'joined_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to add workspace member: {str(e)}")
            raise
    
    async def add_collection_to_workspace(
        self, workspace_id: str, collection_id: str, added_by: str,
        collection_role: str = 'shared', is_featured: bool = False
    ) -> Dict[str, Any]:
        """Add a collection to a team workspace"""
        try:
            # Check permissions
            member = self.db.query(ZoteroTeamWorkspaceMember).filter(
                and_(
                    ZoteroTeamWorkspaceMember.workspace_id == workspace_id,
                    ZoteroTeamWorkspaceMember.user_id == added_by,
                    ZoteroTeamWorkspaceMember.is_active == True
                )
            ).first()
            
            if not member or member.role not in ['owner', 'admin', 'editor']:
                raise PermissionError("User does not have permission to add collections")
            
            # Check if collection exists
            collection = self.db.query(ZoteroSharedReferenceCollection).filter(
                ZoteroSharedReferenceCollection.id == collection_id
            ).first()
            
            if not collection:
                raise ValueError("Collection not found")
            
            # Check if collection is already in workspace
            existing_workspace_collection = self.db.query(ZoteroTeamWorkspaceCollection).filter(
                and_(
                    ZoteroTeamWorkspaceCollection.workspace_id == workspace_id,
                    ZoteroTeamWorkspaceCollection.collection_id == collection_id
                )
            ).first()
            
            if existing_workspace_collection:
                raise ValueError("Collection is already in this workspace")
            
            # Add collection to workspace
            workspace_collection = ZoteroTeamWorkspaceCollection(
                workspace_id=workspace_id,
                collection_id=collection_id,
                added_by=added_by,
                collection_role=collection_role,
                is_featured=is_featured
            )
            
            self.db.add(workspace_collection)
            self.db.commit()
            self.db.refresh(workspace_collection)
            
            # Log activity
            await self._log_collaboration_history(
                workspace_id, added_by, 'add_collection',
                'collection', collection_id,
                f"Added collection '{collection.name}' to workspace",
                {'collection_role': collection_role, 'is_featured': is_featured}, 'low'
            )
            
            return {
                'workspace_collection_id': workspace_collection.id,
                'workspace_id': workspace_id,
                'collection_id': collection_id,
                'collection_role': collection_role,
                'added_at': workspace_collection.added_at
            }
            
        except Exception as e:
            logger.error(f"Failed to add collection to workspace: {str(e)}")
            raise
    
    async def track_modification(
        self, target_type: str, target_id: str, user_id: str,
        modification_type: str, field_changes: Dict[str, Any] = None,
        old_values: Dict[str, Any] = None, new_values: Dict[str, Any] = None,
        workspace_id: str = None, collection_id: str = None,
        change_summary: str = None
    ) -> Dict[str, Any]:
        """Track a modification for collaborative editing"""
        try:
            # Get current version number
            latest_modification = self.db.query(ZoteroModificationTracking).filter(
                and_(
                    ZoteroModificationTracking.target_type == target_type,
                    ZoteroModificationTracking.target_id == target_id
                )
            ).order_by(desc(ZoteroModificationTracking.version_number)).first()
            
            version_number = (latest_modification.version_number + 1) if latest_modification else 1
            
            # Check for potential conflicts
            is_conflict = await self._detect_modification_conflict(
                target_type, target_id, user_id, modification_type, field_changes
            )
            
            # Create modification record
            modification = ZoteroModificationTracking(
                target_type=target_type,
                target_id=target_id,
                workspace_id=workspace_id,
                collection_id=collection_id,
                user_id=user_id,
                modification_type=modification_type,
                field_changes=field_changes or {},
                old_values=old_values or {},
                new_values=new_values or {},
                change_summary=change_summary,
                version_number=version_number,
                is_conflict=is_conflict
            )
            
            self.db.add(modification)
            self.db.commit()
            self.db.refresh(modification)
            
            # If conflict detected, create conflict record
            if is_conflict:
                await self._create_collaboration_conflict(
                    target_type, target_id, workspace_id, user_id, modification
                )
            
            # Log activity if in workspace context
            if workspace_id:
                await self._log_collaboration_history(
                    workspace_id, user_id, f'{modification_type}_{target_type}',
                    target_type, target_id,
                    change_summary or f"{modification_type.title()} {target_type}",
                    {'version': version_number, 'is_conflict': is_conflict}, 
                    'high' if is_conflict else 'low'
                )
            
            return {
                'modification_id': modification.id,
                'version_number': version_number,
                'is_conflict': is_conflict,
                'created_at': modification.created_at
            }
            
        except Exception as e:
            logger.error(f"Failed to track modification: {str(e)}")
            raise
    
    async def get_modification_history(
        self, target_type: str, target_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get modification history for an object"""
        try:
            modifications = self.db.query(ZoteroModificationTracking).filter(
                and_(
                    ZoteroModificationTracking.target_type == target_type,
                    ZoteroModificationTracking.target_id == target_id
                )
            ).order_by(desc(ZoteroModificationTracking.created_at)).limit(limit).offset(offset).all()
            
            result = []
            for modification in modifications:
                result.append({
                    'modification_id': modification.id,
                    'user_id': modification.user_id,
                    'modification_type': modification.modification_type,
                    'field_changes': modification.field_changes,
                    'old_values': modification.old_values,
                    'new_values': modification.new_values,
                    'change_summary': modification.change_summary,
                    'version_number': modification.version_number,
                    'is_conflict': modification.is_conflict,
                    'conflict_resolution': modification.conflict_resolution,
                    'created_at': modification.created_at
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get modification history: {str(e)}")
            raise
    
    async def create_editing_session(
        self, target_type: str, target_id: str, user_id: str,
        workspace_id: str = None
    ) -> Dict[str, Any]:
        """Create a collaborative editing session"""
        try:
            # Generate unique session token
            session_token = self._generate_session_token()
            
            # Check for existing session
            existing_session = self.db.query(ZoteroCollaborativeEditingSession).filter(
                and_(
                    ZoteroCollaborativeEditingSession.target_type == target_type,
                    ZoteroCollaborativeEditingSession.target_id == target_id,
                    ZoteroCollaborativeEditingSession.lock_status != 'unlocked'
                )
            ).first()
            
            if existing_session:
                # Join existing session
                active_users = existing_session.active_users or []
                if user_id not in active_users:
                    active_users.append(user_id)
                    existing_session.active_users = active_users
                    existing_session.updated_at = datetime.utcnow()
                    self.db.commit()
                
                return {
                    'session_id': existing_session.id,
                    'session_token': existing_session.session_token,
                    'active_users': active_users,
                    'lock_status': existing_session.lock_status
                }
            
            # Create new session
            session = ZoteroCollaborativeEditingSession(
                target_type=target_type,
                target_id=target_id,
                workspace_id=workspace_id,
                session_token=session_token,
                active_users=[user_id],
                lock_status='unlocked'
            )
            
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            return {
                'session_id': session.id,
                'session_token': session_token,
                'active_users': [user_id],
                'lock_status': 'unlocked'
            }
            
        except Exception as e:
            logger.error(f"Failed to create editing session: {str(e)}")
            raise
    
    async def resolve_conflict(
        self, conflict_id: str, resolved_by: str, resolution_strategy: str,
        resolution_notes: str = None
    ) -> Dict[str, Any]:
        """Resolve a collaboration conflict"""
        try:
            conflict = self.db.query(ZoteroCollaborationConflict).filter(
                ZoteroCollaborationConflict.id == conflict_id
            ).first()
            
            if not conflict:
                raise ValueError("Conflict not found")
            
            # Check if user has permission to resolve conflict
            if conflict.workspace_id:
                member = self.db.query(ZoteroTeamWorkspaceMember).filter(
                    and_(
                        ZoteroTeamWorkspaceMember.workspace_id == conflict.workspace_id,
                        ZoteroTeamWorkspaceMember.user_id == resolved_by,
                        ZoteroTeamWorkspaceMember.is_active == True
                    )
                ).first()
                
                if not member or member.role not in ['owner', 'admin']:
                    raise PermissionError("User does not have permission to resolve conflicts")
            
            # Update conflict
            conflict.resolution_strategy = resolution_strategy
            conflict.resolution_status = 'resolved'
            conflict.resolved_by = resolved_by
            conflict.resolved_at = datetime.utcnow()
            conflict.resolution_notes = resolution_notes
            
            self.db.commit()
            
            # Update related modification records
            self.db.query(ZoteroModificationTracking).filter(
                and_(
                    ZoteroModificationTracking.target_type == conflict.target_type,
                    ZoteroModificationTracking.target_id == conflict.target_id,
                    ZoteroModificationTracking.is_conflict == True,
                    ZoteroModificationTracking.conflict_resolution.is_(None)
                )
            ).update({
                'conflict_resolution': resolution_strategy
            })
            
            self.db.commit()
            
            # Log activity
            if conflict.workspace_id:
                await self._log_collaboration_history(
                    conflict.workspace_id, resolved_by, 'resolve_conflict',
                    'conflict', conflict_id,
                    f"Resolved {conflict.conflict_type} conflict",
                    {'resolution_strategy': resolution_strategy}, 'high'
                )
            
            return {
                'conflict_id': conflict_id,
                'resolution_strategy': resolution_strategy,
                'resolved_by': resolved_by,
                'resolved_at': conflict.resolved_at
            }
            
        except Exception as e:
            logger.error(f"Failed to resolve conflict: {str(e)}")
            raise
    
    async def get_workspace_conflicts(
        self, workspace_id: str, user_id: str, status: str = None
    ) -> List[Dict[str, Any]]:
        """Get conflicts for a workspace"""
        try:
            # Check user access
            member = self.db.query(ZoteroTeamWorkspaceMember).filter(
                and_(
                    ZoteroTeamWorkspaceMember.workspace_id == workspace_id,
                    ZoteroTeamWorkspaceMember.user_id == user_id,
                    ZoteroTeamWorkspaceMember.is_active == True
                )
            ).first()
            
            if not member:
                raise PermissionError("User does not have access to this workspace")
            
            query = self.db.query(ZoteroCollaborationConflict).filter(
                ZoteroCollaborationConflict.workspace_id == workspace_id
            )
            
            if status:
                query = query.filter(ZoteroCollaborationConflict.resolution_status == status)
            
            conflicts = query.order_by(desc(ZoteroCollaborationConflict.created_at)).all()
            
            result = []
            for conflict in conflicts:
                result.append({
                    'conflict_id': conflict.id,
                    'target_type': conflict.target_type,
                    'target_id': conflict.target_id,
                    'conflict_type': conflict.conflict_type,
                    'conflicting_users': conflict.conflicting_users,
                    'conflict_data': conflict.conflict_data,
                    'resolution_strategy': conflict.resolution_strategy,
                    'resolution_status': conflict.resolution_status,
                    'resolved_by': conflict.resolved_by,
                    'resolved_at': conflict.resolved_at,
                    'resolution_notes': conflict.resolution_notes,
                    'created_at': conflict.created_at
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get workspace conflicts: {str(e)}")
            raise
    
    async def get_collaboration_history(
        self, workspace_id: str, user_id: str, limit: int = 50, offset: int = 0,
        action_type: str = None, impact_level: str = None
    ) -> List[Dict[str, Any]]:
        """Get collaboration history for a workspace"""
        try:
            # Check user access
            member = self.db.query(ZoteroTeamWorkspaceMember).filter(
                and_(
                    ZoteroTeamWorkspaceMember.workspace_id == workspace_id,
                    ZoteroTeamWorkspaceMember.user_id == user_id,
                    ZoteroTeamWorkspaceMember.is_active == True
                )
            ).first()
            
            if not member:
                raise PermissionError("User does not have access to this workspace")
            
            query = self.db.query(ZoteroTeamCollaborationHistory).filter(
                ZoteroTeamCollaborationHistory.workspace_id == workspace_id
            )
            
            if action_type:
                query = query.filter(ZoteroTeamCollaborationHistory.action_type == action_type)
            
            if impact_level:
                query = query.filter(ZoteroTeamCollaborationHistory.impact_level == impact_level)
            
            history = query.order_by(desc(ZoteroTeamCollaborationHistory.created_at)).limit(limit).offset(offset).all()
            
            result = []
            for entry in history:
                result.append({
                    'history_id': entry.id,
                    'user_id': entry.user_id,
                    'action_type': entry.action_type,
                    'target_type': entry.target_type,
                    'target_id': entry.target_id,
                    'action_description': entry.action_description,
                    'action_data': entry.action_data,
                    'impact_level': entry.impact_level,
                    'created_at': entry.created_at
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get collaboration history: {str(e)}")
            raise
    
    def _generate_session_token(self, length: int = 32) -> str:
        """Generate a random session token"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    async def _detect_modification_conflict(
        self, target_type: str, target_id: str, user_id: str,
        modification_type: str, field_changes: Dict[str, Any] = None
    ) -> bool:
        """Detect if a modification conflicts with recent changes"""
        try:
            # Check for recent modifications by other users
            recent_cutoff = datetime.utcnow() - timedelta(minutes=5)
            
            recent_modifications = self.db.query(ZoteroModificationTracking).filter(
                and_(
                    ZoteroModificationTracking.target_type == target_type,
                    ZoteroModificationTracking.target_id == target_id,
                    ZoteroModificationTracking.user_id != user_id,
                    ZoteroModificationTracking.created_at >= recent_cutoff
                )
            ).all()
            
            if not recent_modifications:
                return False
            
            # Check for overlapping field changes
            if field_changes:
                for recent_mod in recent_modifications:
                    if recent_mod.field_changes:
                        overlapping_fields = set(field_changes.keys()) & set(recent_mod.field_changes.keys())
                        if overlapping_fields:
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to detect modification conflict: {str(e)}")
            return False
    
    async def _create_collaboration_conflict(
        self, target_type: str, target_id: str, workspace_id: str,
        user_id: str, modification: ZoteroModificationTracking
    ) -> None:
        """Create a collaboration conflict record"""
        try:
            # Get conflicting users
            recent_cutoff = datetime.utcnow() - timedelta(minutes=5)
            conflicting_modifications = self.db.query(ZoteroModificationTracking).filter(
                and_(
                    ZoteroModificationTracking.target_type == target_type,
                    ZoteroModificationTracking.target_id == target_id,
                    ZoteroModificationTracking.user_id != user_id,
                    ZoteroModificationTracking.created_at >= recent_cutoff
                )
            ).all()
            
            conflicting_users = [user_id] + [mod.user_id for mod in conflicting_modifications]
            
            conflict = ZoteroCollaborationConflict(
                target_type=target_type,
                target_id=target_id,
                workspace_id=workspace_id,
                conflict_type='concurrent_edit',
                conflicting_users=conflicting_users,
                conflict_data={
                    'current_modification': {
                        'user_id': user_id,
                        'modification_type': modification.modification_type,
                        'field_changes': modification.field_changes,
                        'version_number': modification.version_number
                    },
                    'conflicting_modifications': [
                        {
                            'user_id': mod.user_id,
                            'modification_type': mod.modification_type,
                            'field_changes': mod.field_changes,
                            'version_number': mod.version_number
                        }
                        for mod in conflicting_modifications
                    ]
                }
            )
            
            self.db.add(conflict)
            self.db.commit()
            
            # Notify conflicting users
            for conflicting_user in conflicting_users:
                await self._create_workspace_notification(
                    workspace_id, conflicting_user, 'conflict_detected',
                    'Editing conflict detected',
                    f'A conflict was detected while editing {target_type}',
                    target_type, target_id, None, 'high', True
                )
            
        except Exception as e:
            logger.error(f"Failed to create collaboration conflict: {str(e)}")
    
    async def _initialize_workspace_settings(self, workspace_id: str, user_id: str) -> None:
        """Initialize default settings for a workspace"""
        try:
            default_settings = [
                ('collaboration', 'allow_concurrent_editing', True),
                ('collaboration', 'auto_save_interval', 30),
                ('collaboration', 'conflict_resolution_strategy', 'manual'),
                ('permissions', 'default_member_role', 'member'),
                ('permissions', 'allow_member_invite', False),
                ('notifications', 'notify_on_conflicts', True),
                ('notifications', 'notify_on_member_join', True),
                ('sync', 'auto_sync_enabled', True),
                ('sync', 'sync_frequency_minutes', 15)
            ]
            
            for category, key, value in default_settings:
                setting = ZoteroTeamWorkspaceSettings(
                    workspace_id=workspace_id,
                    setting_category=category,
                    setting_key=key,
                    setting_value=value,
                    set_by=user_id
                )
                self.db.add(setting)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to initialize workspace settings: {str(e)}")
    
    async def _log_collaboration_history(
        self, workspace_id: str, user_id: str, action_type: str,
        target_type: str = None, target_id: str = None,
        action_description: str = None, action_data: Dict[str, Any] = None,
        impact_level: str = 'low'
    ) -> None:
        """Log collaboration history"""
        
        history = ZoteroTeamCollaborationHistory(
            workspace_id=workspace_id,
            user_id=user_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            action_description=action_description,
            action_data=action_data or {},
            impact_level=impact_level
        )
        
        self.db.add(history)
        self.db.commit()
    
    async def _create_workspace_notification(
        self, workspace_id: str, user_id: str, notification_type: str,
        title: str, message: str, target_type: str = None, target_id: str = None,
        sender_user_id: str = None, priority: str = 'normal',
        action_required: bool = False, action_url: str = None
    ) -> None:
        """Create a workspace notification"""
        
        notification = ZoteroTeamWorkspaceNotification(
            workspace_id=workspace_id,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            target_type=target_type,
            target_id=target_id,
            sender_user_id=sender_user_id,
            action_required=action_required,
            action_url=action_url
        )
        
        self.db.add(notification)
        self.db.commit()