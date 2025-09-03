"""
Zotero Annotation Synchronization Service

This service handles synchronization of PDF annotations between AI Scholar and Zotero,
including bidirectional sync, conflict resolution, and collaboration features.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from models.zotero_models import (
    ZoteroAnnotation, ZoteroAnnotationSyncLog, ZoteroAnnotationCollaboration,
    ZoteroAnnotationShare, ZoteroAnnotationHistory, ZoteroAttachment, ZoteroConnection
)
from services.zotero.zotero_client import ZoteroClient
from core.database import get_db_session

logger = logging.getLogger(__name__)


class ZoteroAnnotationSyncService:
    """Service for managing annotation synchronization with Zotero"""
    
    def __init__(self, db_session: Session = None):
        self.db = db_session or get_db_session()
        self.zotero_client = ZoteroClient()
    
    async def sync_annotations_for_attachment(
        self, 
        attachment_id: str, 
        user_id: str,
        sync_direction: str = 'bidirectional'
    ) -> Dict[str, Any]:
        """
        Synchronize annotations for a specific attachment
        
        Args:
            attachment_id: ID of the attachment to sync
            user_id: ID of the user performing the sync
            sync_direction: 'from_zotero', 'to_zotero', or 'bidirectional'
            
        Returns:
            Dict with sync results and statistics
        """
        try:
            # Get attachment and connection info
            attachment = self.db.query(ZoteroAttachment).filter(
                ZoteroAttachment.id == attachment_id
            ).first()
            
            if not attachment:
                raise ValueError(f"Attachment {attachment_id} not found")
            
            # Get Zotero connection for the user
            connection = self._get_user_connection(user_id)
            if not connection:
                raise ValueError(f"No Zotero connection found for user {user_id}")
            
            sync_results = {
                'attachment_id': attachment_id,
                'sync_direction': sync_direction,
                'annotations_imported': 0,
                'annotations_exported': 0,
                'annotations_updated': 0,
                'conflicts_detected': 0,
                'errors': []
            }
            
            # Perform sync based on direction
            if sync_direction in ['from_zotero', 'bidirectional']:
                import_results = await self._import_annotations_from_zotero(
                    attachment, connection
                )
                sync_results.update(import_results)
            
            if sync_direction in ['to_zotero', 'bidirectional']:
                export_results = await self._export_annotations_to_zotero(
                    attachment, connection
                )
                sync_results['annotations_exported'] += export_results.get('exported', 0)
                sync_results['errors'].extend(export_results.get('errors', []))
            
            # Log sync operation
            await self._log_sync_operation(
                attachment_id, sync_direction, 'completed', sync_results
            )
            
            return sync_results
            
        except Exception as e:
            logger.error(f"Error syncing annotations for attachment {attachment_id}: {str(e)}")
            await self._log_sync_operation(
                attachment_id, sync_direction, 'failed', {'error': str(e)}
            )
            raise
    
    async def _import_annotations_from_zotero(
        self, 
        attachment: ZoteroAttachment, 
        connection: ZoteroConnection
    ) -> Dict[str, Any]:
        """Import annotations from Zotero for an attachment"""
        results = {
            'annotations_imported': 0,
            'annotations_updated': 0,
            'conflicts_detected': 0,
            'errors': []
        }
        
        try:
            # Get annotations from Zotero API
            zotero_annotations = await self.zotero_client.get_item_annotations(
                connection.zotero_user_id,
                attachment.zotero_attachment_key,
                connection.access_token
            )
            
            for zotero_annotation in zotero_annotations:
                try:
                    result = await self._process_zotero_annotation(
                        attachment, zotero_annotation
                    )
                    
                    if result['action'] == 'imported':
                        results['annotations_imported'] += 1
                    elif result['action'] == 'updated':
                        results['annotations_updated'] += 1
                    elif result['action'] == 'conflict':
                        results['conflicts_detected'] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing annotation {zotero_annotation.get('key', 'unknown')}: {str(e)}")
                    results['errors'].append({
                        'annotation_key': zotero_annotation.get('key', 'unknown'),
                        'error': str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error importing annotations from Zotero: {str(e)}")
            results['errors'].append({'error': str(e)})
            return results
    
    async def _process_zotero_annotation(
        self, 
        attachment: ZoteroAttachment, 
        zotero_annotation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a single annotation from Zotero"""
        annotation_key = zotero_annotation['key']
        
        # Check if annotation already exists locally
        existing_annotation = self.db.query(ZoteroAnnotation).filter(
            and_(
                ZoteroAnnotation.attachment_id == attachment.id,
                ZoteroAnnotation.zotero_annotation_key == annotation_key
            )
        ).first()
        
        annotation_data = self._extract_annotation_data(zotero_annotation)
        
        if existing_annotation:
            # Check for conflicts
            if self._has_annotation_conflict(existing_annotation, annotation_data):
                await self._handle_annotation_conflict(
                    existing_annotation, annotation_data, 'from_zotero'
                )
                return {'action': 'conflict', 'annotation_id': existing_annotation.id}
            else:
                # Update existing annotation
                await self._update_annotation(existing_annotation, annotation_data)
                return {'action': 'updated', 'annotation_id': existing_annotation.id}
        else:
            # Create new annotation
            new_annotation = await self._create_annotation(attachment.id, annotation_data)
            return {'action': 'imported', 'annotation_id': new_annotation.id}
    
    async def _export_annotations_to_zotero(
        self, 
        attachment: ZoteroAttachment, 
        connection: ZoteroConnection
    ) -> Dict[str, Any]:
        """Export local annotations to Zotero"""
        results = {
            'exported': 0,
            'errors': []
        }
        
        try:
            # Get local annotations that need to be exported
            local_annotations = self.db.query(ZoteroAnnotation).filter(
                and_(
                    ZoteroAnnotation.attachment_id == attachment.id,
                    or_(
                        ZoteroAnnotation.sync_status == 'pending',
                        ZoteroAnnotation.last_synced_at.is_(None)
                    )
                )
            ).all()
            
            for annotation in local_annotations:
                try:
                    # Convert to Zotero format and upload
                    zotero_data = self._convert_to_zotero_format(annotation)
                    
                    if annotation.zotero_annotation_key:
                        # Update existing annotation in Zotero
                        await self.zotero_client.update_annotation(
                            connection.zotero_user_id,
                            annotation.zotero_annotation_key,
                            zotero_data,
                            connection.access_token
                        )
                    else:
                        # Create new annotation in Zotero
                        response = await self.zotero_client.create_annotation(
                            connection.zotero_user_id,
                            attachment.zotero_attachment_key,
                            zotero_data,
                            connection.access_token
                        )
                        annotation.zotero_annotation_key = response['key']
                    
                    # Update sync status
                    annotation.sync_status = 'synced'
                    annotation.last_synced_at = datetime.utcnow()
                    self.db.commit()
                    
                    results['exported'] += 1
                    
                except Exception as e:
                    logger.error(f"Error exporting annotation {annotation.id}: {str(e)}")
                    results['errors'].append({
                        'annotation_id': annotation.id,
                        'error': str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error exporting annotations to Zotero: {str(e)}")
            results['errors'].append({'error': str(e)})
            return results
    
    async def create_annotation_collaboration(
        self, 
        annotation_id: str, 
        user_id: str,
        collaboration_type: str,
        content: str,
        parent_collaboration_id: Optional[str] = None
    ) -> ZoteroAnnotationCollaboration:
        """Create a new annotation collaboration (comment, reply, etc.)"""
        try:
            collaboration = ZoteroAnnotationCollaboration(
                annotation_id=annotation_id,
                user_id=user_id,
                collaboration_type=collaboration_type,
                content=content,
                parent_collaboration_id=parent_collaboration_id
            )
            
            self.db.add(collaboration)
            self.db.commit()
            self.db.refresh(collaboration)
            
            # Log the collaboration activity
            await self._log_annotation_history(
                annotation_id, user_id, 'comment', 
                {'collaboration_type': collaboration_type, 'content': content}
            )
            
            return collaboration
            
        except Exception as e:
            logger.error(f"Error creating annotation collaboration: {str(e)}")
            self.db.rollback()
            raise
    
    async def share_annotation(
        self, 
        annotation_id: str, 
        owner_user_id: str,
        shared_with_user_id: str,
        permission_level: str = 'read',
        share_message: Optional[str] = None
    ) -> ZoteroAnnotationShare:
        """Share an annotation with another user"""
        try:
            # Check if annotation is already shared with this user
            existing_share = self.db.query(ZoteroAnnotationShare).filter(
                and_(
                    ZoteroAnnotationShare.annotation_id == annotation_id,
                    ZoteroAnnotationShare.shared_with_user_id == shared_with_user_id,
                    ZoteroAnnotationShare.is_active == True
                )
            ).first()
            
            if existing_share:
                # Update existing share
                existing_share.permission_level = permission_level
                existing_share.share_message = share_message
                existing_share.updated_at = datetime.utcnow()
                self.db.commit()
                return existing_share
            
            # Create new share
            share = ZoteroAnnotationShare(
                annotation_id=annotation_id,
                owner_user_id=owner_user_id,
                shared_with_user_id=shared_with_user_id,
                permission_level=permission_level,
                share_message=share_message
            )
            
            self.db.add(share)
            self.db.commit()
            self.db.refresh(share)
            
            # Log the sharing activity
            await self._log_annotation_history(
                annotation_id, owner_user_id, 'share',
                {
                    'shared_with_user_id': shared_with_user_id,
                    'permission_level': permission_level
                }
            )
            
            return share
            
        except Exception as e:
            logger.error(f"Error sharing annotation: {str(e)}")
            self.db.rollback()
            raise
    
    async def get_annotation_collaborations(
        self, 
        annotation_id: str,
        user_id: Optional[str] = None
    ) -> List[ZoteroAnnotationCollaboration]:
        """Get collaborations for an annotation"""
        query = self.db.query(ZoteroAnnotationCollaboration).filter(
            and_(
                ZoteroAnnotationCollaboration.annotation_id == annotation_id,
                ZoteroAnnotationCollaboration.is_active == True
            )
        )
        
        if user_id:
            query = query.filter(ZoteroAnnotationCollaboration.user_id == user_id)
        
        return query.order_by(ZoteroAnnotationCollaboration.created_at).all()
    
    async def get_annotation_history(
        self, 
        annotation_id: str,
        limit: int = 50
    ) -> List[ZoteroAnnotationHistory]:
        """Get change history for an annotation"""
        return self.db.query(ZoteroAnnotationHistory).filter(
            ZoteroAnnotationHistory.annotation_id == annotation_id
        ).order_by(desc(ZoteroAnnotationHistory.created_at)).limit(limit).all()
    
    async def get_shared_annotations(
        self, 
        user_id: str,
        permission_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get annotations shared with a user"""
        query = self.db.query(ZoteroAnnotationShare).filter(
            and_(
                ZoteroAnnotationShare.shared_with_user_id == user_id,
                ZoteroAnnotationShare.is_active == True
            )
        )
        
        if permission_level:
            query = query.filter(ZoteroAnnotationShare.permission_level == permission_level)
        
        shares = query.all()
        
        # Get annotation details for each share
        result = []
        for share in shares:
            annotation = self.db.query(ZoteroAnnotation).filter(
                ZoteroAnnotation.id == share.annotation_id
            ).first()
            
            if annotation:
                result.append({
                    'share': share,
                    'annotation': annotation,
                    'attachment': annotation.attachment
                })
        
        return result
    
    def _get_user_connection(self, user_id: str) -> Optional[ZoteroConnection]:
        """Get active Zotero connection for a user"""
        return self.db.query(ZoteroConnection).filter(
            and_(
                ZoteroConnection.user_id == user_id,
                ZoteroConnection.connection_status == 'active'
            )
        ).first()
    
    def _extract_annotation_data(self, zotero_annotation: Dict[str, Any]) -> Dict[str, Any]:
        """Extract annotation data from Zotero API response"""
        data = zotero_annotation.get('data', {})
        
        return {
            'zotero_annotation_key': zotero_annotation['key'],
            'annotation_type': data.get('annotationType', 'highlight'),
            'annotation_text': data.get('annotationText', ''),
            'annotation_comment': data.get('annotationComment', ''),
            'page_number': data.get('annotationPageLabel'),
            'position_data': {
                'position': data.get('annotationPosition'),
                'sortIndex': data.get('annotationSortIndex')
            },
            'color': data.get('annotationColor', '#ffff00'),
            'annotation_metadata': {
                'dateAdded': data.get('dateAdded'),
                'dateModified': data.get('dateModified'),
                'version': zotero_annotation.get('version')
            }
        }
    
    def _has_annotation_conflict(
        self, 
        local_annotation: ZoteroAnnotation, 
        zotero_data: Dict[str, Any]
    ) -> bool:
        """Check if there's a conflict between local and Zotero annotation"""
        # Simple conflict detection based on modification time and content
        local_modified = local_annotation.updated_at
        zotero_modified = datetime.fromisoformat(
            zotero_data['annotation_metadata'].get('dateModified', '').replace('Z', '+00:00')
        ) if zotero_data['annotation_metadata'].get('dateModified') else None
        
        if not zotero_modified:
            return False
        
        # Check if both have been modified since last sync
        if (local_annotation.last_synced_at and 
            local_modified > local_annotation.last_synced_at and
            zotero_modified > local_annotation.last_synced_at):
            return True
        
        return False
    
    async def _handle_annotation_conflict(
        self, 
        local_annotation: ZoteroAnnotation,
        zotero_data: Dict[str, Any],
        resolution_strategy: str = 'from_zotero'
    ):
        """Handle annotation sync conflicts"""
        # Log the conflict
        await self._log_annotation_history(
            local_annotation.id, 
            'system', 
            'conflict',
            {
                'local_data': {
                    'text': local_annotation.annotation_text,
                    'comment': local_annotation.annotation_comment,
                    'updated_at': local_annotation.updated_at.isoformat()
                },
                'zotero_data': zotero_data,
                'resolution_strategy': resolution_strategy
            }
        )
        
        # Apply resolution strategy
        if resolution_strategy == 'from_zotero':
            await self._update_annotation(local_annotation, zotero_data)
            local_annotation.sync_status = 'synced'
        elif resolution_strategy == 'keep_local':
            local_annotation.sync_status = 'conflict'
        
        self.db.commit()
    
    async def _create_annotation(
        self, 
        attachment_id: str, 
        annotation_data: Dict[str, Any]
    ) -> ZoteroAnnotation:
        """Create a new annotation from data"""
        annotation = ZoteroAnnotation(
            attachment_id=attachment_id,
            **annotation_data,
            sync_status='synced',
            last_synced_at=datetime.utcnow()
        )
        
        self.db.add(annotation)
        self.db.commit()
        self.db.refresh(annotation)
        
        return annotation
    
    async def _update_annotation(
        self, 
        annotation: ZoteroAnnotation, 
        annotation_data: Dict[str, Any]
    ):
        """Update an existing annotation with new data"""
        for key, value in annotation_data.items():
            if hasattr(annotation, key):
                setattr(annotation, key, value)
        
        annotation.last_synced_at = datetime.utcnow()
        annotation.sync_status = 'synced'
        annotation.annotation_version += 1
        
        self.db.commit()
    
    def _convert_to_zotero_format(self, annotation: ZoteroAnnotation) -> Dict[str, Any]:
        """Convert local annotation to Zotero API format"""
        return {
            'annotationType': annotation.annotation_type,
            'annotationText': annotation.annotation_text or '',
            'annotationComment': annotation.annotation_comment or '',
            'annotationPageLabel': str(annotation.page_number) if annotation.page_number else '',
            'annotationPosition': annotation.position_data.get('position') if annotation.position_data else None,
            'annotationSortIndex': annotation.position_data.get('sortIndex') if annotation.position_data else None,
            'annotationColor': annotation.color or '#ffff00'
        }
    
    async def _log_sync_operation(
        self, 
        attachment_id: str, 
        sync_direction: str,
        status: str, 
        metadata: Dict[str, Any]
    ):
        """Log a sync operation"""
        # This would typically log to the ZoteroAnnotationSyncLog table
        # For now, just log to the application logger
        logger.info(f"Annotation sync for attachment {attachment_id}: {status}")
    
    async def _log_annotation_history(
        self, 
        annotation_id: str, 
        user_id: str,
        change_type: str, 
        change_data: Dict[str, Any]
    ):
        """Log annotation history entry"""
        history_entry = ZoteroAnnotationHistory(
            annotation_id=annotation_id,
            user_id=user_id,
            change_type=change_type,
            new_content=change_data,
            change_description=f"{change_type.title()} operation on annotation"
        )
        
        self.db.add(history_entry)
        self.db.commit()