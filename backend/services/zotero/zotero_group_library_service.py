"""
Zotero Group Library Service

Handles group library management, permissions, and synchronization.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from models.zotero_models import (
    ZoteroLibrary, ZoteroGroupMember, ZoteroGroupSyncSettings,
    ZoteroGroupPermissionTemplate, ZoteroGroupActivityLog,
    ZoteroGroupAccessControl, ZoteroGroupSyncConflict
)
from services.zotero.zotero_client import ZoteroClient
from core.database import get_db

logger = logging.getLogger(__name__)


class ZoteroGroupLibraryService:
    """Service for managing Zotero group libraries"""
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.zotero_client = ZoteroClient()
    
    async def import_group_libraries(self, connection_id: str, user_id: str) -> Dict[str, Any]:
        """Import all accessible group libraries for a user"""
        try:
            # Get user's group libraries from Zotero API
            groups_data = await self.zotero_client.get_user_groups(connection_id)
            
            imported_libraries = []
            errors = []
            
            for group_data in groups_data:
                try:
                    library = await self._import_single_group_library(
                        connection_id, user_id, group_data
                    )
                    imported_libraries.append(library)
                    
                    # Import group members
                    await self._import_group_members(library.id, group_data)
                    
                    # Set up default sync settings for user
                    await self._create_default_sync_settings(library.id, user_id)
                    
                except Exception as e:
                    logger.error(f"Failed to import group library {group_data.get('id')}: {str(e)}")
                    errors.append({
                        'group_id': group_data.get('id'),
                        'error': str(e)
                    })
            
            return {
                'imported_count': len(imported_libraries),
                'libraries': [lib.id for lib in imported_libraries],
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Failed to import group libraries: {str(e)}")
            raise
    
    async def _import_single_group_library(
        self, connection_id: str, user_id: str, group_data: Dict[str, Any]
    ) -> ZoteroLibrary:
        """Import a single group library"""
        
        # Check if library already exists
        existing_library = self.db.query(ZoteroLibrary).filter(
            and_(
                ZoteroLibrary.connection_id == connection_id,
                ZoteroLibrary.zotero_library_id == str(group_data['id']),
                ZoteroLibrary.library_type == 'group'
            )
        ).first()
        
        if existing_library:
            # Update existing library
            existing_library.library_name = group_data['data']['name']
            existing_library.group_description = group_data['data'].get('description', '')
            existing_library.group_url = group_data['data'].get('url', '')
            existing_library.is_public = group_data['data'].get('type') == 'PublicOpen'
            existing_library.member_count = group_data['data'].get('numMembers', 0)
            existing_library.group_permissions = group_data['data'].get('libraryReading', {})
            existing_library.group_settings = group_data['data']
            existing_library.updated_at = datetime.utcnow()
            
            self.db.commit()
            return existing_library
        
        # Create new library
        library = ZoteroLibrary(
            connection_id=connection_id,
            zotero_library_id=str(group_data['id']),
            library_type='group',
            library_name=group_data['data']['name'],
            group_id=str(group_data['id']),
            group_description=group_data['data'].get('description', ''),
            group_url=group_data['data'].get('url', ''),
            is_public=group_data['data'].get('type') == 'PublicOpen',
            member_count=group_data['data'].get('numMembers', 0),
            group_permissions=group_data['data'].get('libraryReading', {}),
            group_settings=group_data['data'],
            library_metadata=group_data
        )
        
        self.db.add(library)
        self.db.commit()
        self.db.refresh(library)
        
        # Log activity
        await self._log_group_activity(
            library.id, user_id, 'library_imported',
            'library', library.id,
            f"Group library '{library.library_name}' imported"
        )
        
        return library
    
    async def _import_group_members(self, library_id: str, group_data: Dict[str, Any]) -> None:
        """Import group members for a library"""
        try:
            members_data = group_data['data'].get('members', [])
            
            for member_data in members_data:
                # Check if member already exists
                existing_member = self.db.query(ZoteroGroupMember).filter(
                    and_(
                        ZoteroGroupMember.library_id == library_id,
                        ZoteroGroupMember.zotero_user_id == str(member_data['userID'])
                    )
                ).first()
                
                if existing_member:
                    # Update existing member
                    existing_member.member_role = member_data.get('role', 'member')
                    existing_member.permissions = member_data.get('permissions', {})
                    existing_member.last_activity = datetime.utcnow()
                    existing_member.updated_at = datetime.utcnow()
                else:
                    # Create new member
                    member = ZoteroGroupMember(
                        library_id=library_id,
                        user_id=member_data.get('userID', ''),  # This might need mapping to local user_id
                        zotero_user_id=str(member_data['userID']),
                        member_role=member_data.get('role', 'member'),
                        permissions=member_data.get('permissions', {}),
                        join_date=datetime.utcnow(),
                        member_metadata=member_data
                    )
                    self.db.add(member)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to import group members for library {library_id}: {str(e)}")
            raise
    
    async def _create_default_sync_settings(self, library_id: str, user_id: str) -> None:
        """Create default sync settings for a user and group library"""
        
        # Check if settings already exist
        existing_settings = self.db.query(ZoteroGroupSyncSettings).filter(
            and_(
                ZoteroGroupSyncSettings.library_id == library_id,
                ZoteroGroupSyncSettings.user_id == user_id
            )
        ).first()
        
        if not existing_settings:
            settings = ZoteroGroupSyncSettings(
                library_id=library_id,
                user_id=user_id,
                sync_enabled=True,
                sync_frequency_minutes=60,
                sync_collections=True,
                sync_items=True,
                sync_attachments=False,  # Conservative default for group libraries
                sync_annotations=True,
                auto_resolve_conflicts=True,
                conflict_resolution_strategy='zotero_wins'
            )
            self.db.add(settings)
            self.db.commit()
    
    async def get_user_group_libraries(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all group libraries accessible to a user"""
        
        # Get libraries where user is a member
        libraries = self.db.query(ZoteroLibrary).join(
            ZoteroGroupMember,
            ZoteroLibrary.id == ZoteroGroupMember.library_id
        ).filter(
            and_(
                ZoteroLibrary.library_type == 'group',
                ZoteroLibrary.is_active == True,
                ZoteroGroupMember.user_id == user_id,
                ZoteroGroupMember.is_active == True
            )
        ).all()
        
        result = []
        for library in libraries:
            # Get user's role in this group
            member = self.db.query(ZoteroGroupMember).filter(
                and_(
                    ZoteroGroupMember.library_id == library.id,
                    ZoteroGroupMember.user_id == user_id,
                    ZoteroGroupMember.is_active == True
                )
            ).first()
            
            # Get sync settings
            sync_settings = self.db.query(ZoteroGroupSyncSettings).filter(
                and_(
                    ZoteroGroupSyncSettings.library_id == library.id,
                    ZoteroGroupSyncSettings.user_id == user_id
                )
            ).first()
            
            result.append({
                'id': library.id,
                'zotero_library_id': library.zotero_library_id,
                'name': library.library_name,
                'description': library.group_description,
                'is_public': library.is_public,
                'member_count': library.member_count,
                'user_role': member.member_role if member else 'unknown',
                'user_permissions': member.permissions if member else {},
                'sync_enabled': sync_settings.sync_enabled if sync_settings else False,
                'last_sync_at': library.last_sync_at,
                'created_at': library.created_at
            })
        
        return result
    
    async def get_group_members(self, library_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get members of a group library"""
        
        # Check if user has permission to view members
        if not await self._check_permission(library_id, user_id, 'read'):
            raise PermissionError("User does not have permission to view group members")
        
        members = self.db.query(ZoteroGroupMember).filter(
            and_(
                ZoteroGroupMember.library_id == library_id,
                ZoteroGroupMember.is_active == True
            )
        ).order_by(ZoteroGroupMember.member_role, ZoteroGroupMember.join_date).all()
        
        return [
            {
                'id': member.id,
                'user_id': member.user_id,
                'zotero_user_id': member.zotero_user_id,
                'role': member.member_role,
                'permissions': member.permissions,
                'join_date': member.join_date,
                'last_activity': member.last_activity,
                'invitation_status': member.invitation_status
            }
            for member in members
        ]
    
    async def update_member_permissions(
        self, library_id: str, member_id: str, new_role: str, 
        new_permissions: Dict[str, Any], updated_by: str
    ) -> Dict[str, Any]:
        """Update a group member's role and permissions"""
        
        # Check if user has permission to manage members
        if not await self._check_permission(library_id, updated_by, 'manage_members'):
            raise PermissionError("User does not have permission to manage group members")
        
        member = self.db.query(ZoteroGroupMember).filter(
            and_(
                ZoteroGroupMember.id == member_id,
                ZoteroGroupMember.library_id == library_id,
                ZoteroGroupMember.is_active == True
            )
        ).first()
        
        if not member:
            raise ValueError("Group member not found")
        
        # Store old data for logging
        old_data = {
            'role': member.member_role,
            'permissions': member.permissions
        }
        
        # Update member
        member.member_role = new_role
        member.permissions = new_permissions
        member.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # Log activity
        await self._log_group_activity(
            library_id, updated_by, 'permission_changed',
            'member', member_id,
            f"Updated permissions for member {member.zotero_user_id}",
            old_data=old_data,
            new_data={'role': new_role, 'permissions': new_permissions}
        )
        
        return {
            'member_id': member_id,
            'new_role': new_role,
            'new_permissions': new_permissions,
            'updated_at': member.updated_at
        }
    
    async def get_group_sync_settings(self, library_id: str, user_id: str) -> Dict[str, Any]:
        """Get sync settings for a user and group library"""
        
        settings = self.db.query(ZoteroGroupSyncSettings).filter(
            and_(
                ZoteroGroupSyncSettings.library_id == library_id,
                ZoteroGroupSyncSettings.user_id == user_id
            )
        ).first()
        
        if not settings:
            # Create default settings
            await self._create_default_sync_settings(library_id, user_id)
            settings = self.db.query(ZoteroGroupSyncSettings).filter(
                and_(
                    ZoteroGroupSyncSettings.library_id == library_id,
                    ZoteroGroupSyncSettings.user_id == user_id
                )
            ).first()
        
        return {
            'sync_enabled': settings.sync_enabled,
            'sync_frequency_minutes': settings.sync_frequency_minutes,
            'sync_collections': settings.sync_collections,
            'sync_items': settings.sync_items,
            'sync_attachments': settings.sync_attachments,
            'sync_annotations': settings.sync_annotations,
            'auto_resolve_conflicts': settings.auto_resolve_conflicts,
            'conflict_resolution_strategy': settings.conflict_resolution_strategy,
            'last_sync_at': settings.last_sync_at
        }
    
    async def update_group_sync_settings(
        self, library_id: str, user_id: str, settings_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update sync settings for a user and group library"""
        
        settings = self.db.query(ZoteroGroupSyncSettings).filter(
            and_(
                ZoteroGroupSyncSettings.library_id == library_id,
                ZoteroGroupSyncSettings.user_id == user_id
            )
        ).first()
        
        if not settings:
            raise ValueError("Sync settings not found")
        
        # Update settings
        for key, value in settings_data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        settings.updated_at = datetime.utcnow()
        self.db.commit()
        
        return await self.get_group_sync_settings(library_id, user_id)
    
    async def get_group_activity_log(
        self, library_id: str, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get activity log for a group library"""
        
        # Check if user has permission to view activity
        if not await self._check_permission(library_id, user_id, 'read'):
            raise PermissionError("User does not have permission to view group activity")
        
        activities = self.db.query(ZoteroGroupActivityLog).filter(
            ZoteroGroupActivityLog.library_id == library_id
        ).order_by(desc(ZoteroGroupActivityLog.created_at)).limit(limit).offset(offset).all()
        
        return [
            {
                'id': activity.id,
                'user_id': activity.user_id,
                'activity_type': activity.activity_type,
                'target_type': activity.target_type,
                'target_id': activity.target_id,
                'description': activity.activity_description,
                'created_at': activity.created_at
            }
            for activity in activities
        ]
    
    async def _check_permission(self, library_id: str, user_id: str, permission: str) -> bool:
        """Check if user has specific permission for a group library"""
        
        # Get user's membership
        member = self.db.query(ZoteroGroupMember).filter(
            and_(
                ZoteroGroupMember.library_id == library_id,
                ZoteroGroupMember.user_id == user_id,
                ZoteroGroupMember.is_active == True
            )
        ).first()
        
        if not member:
            return False
        
        # Check role-based permissions
        role_permissions = {
            'owner': ['read', 'write', 'delete', 'admin', 'manage_members', 'manage_permissions', 'manage_settings'],
            'admin': ['read', 'write', 'delete', 'admin', 'manage_members', 'manage_permissions'],
            'member': ['read', 'write'],
            'reader': ['read']
        }
        
        if permission in role_permissions.get(member.member_role, []):
            return True
        
        # Check specific permissions
        return member.permissions.get(permission, False)
    
    async def _log_group_activity(
        self, library_id: str, user_id: str, activity_type: str,
        target_type: str, target_id: str, description: str,
        old_data: Dict[str, Any] = None, new_data: Dict[str, Any] = None,
        ip_address: str = None, user_agent: str = None
    ) -> None:
        """Log group activity"""
        
        activity = ZoteroGroupActivityLog(
            library_id=library_id,
            user_id=user_id,
            activity_type=activity_type,
            target_type=target_type,
            target_id=target_id,
            activity_description=description,
            old_data=old_data or {},
            new_data=new_data or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(activity)
        self.db.commit()
    
    async def get_permission_templates(self) -> List[Dict[str, Any]]:
        """Get available permission templates"""
        
        templates = self.db.query(ZoteroGroupPermissionTemplate).filter(
            ZoteroGroupPermissionTemplate.is_system == True
        ).all()
        
        return [
            {
                'id': template.id,
                'name': template.template_name,
                'description': template.template_description,
                'permissions': template.permissions,
                'is_default': template.is_default
            }
            for template in templates
        ]
    
    async def sync_group_library(self, library_id: str, user_id: str) -> Dict[str, Any]:
        """Trigger sync for a specific group library"""
        
        # Check if user has permission to sync
        if not await self._check_permission(library_id, user_id, 'read'):
            raise PermissionError("User does not have permission to sync this group library")
        
        # Get sync settings
        sync_settings = await self.get_group_sync_settings(library_id, user_id)
        
        if not sync_settings['sync_enabled']:
            raise ValueError("Sync is disabled for this group library")
        
        # This would typically trigger a background sync job
        # For now, return a placeholder response
        return {
            'sync_initiated': True,
            'library_id': library_id,
            'sync_type': 'manual_group_sync',
            'message': 'Group library sync initiated'
        }