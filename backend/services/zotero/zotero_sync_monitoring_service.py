"""
Zotero sync status monitoring and notifications service
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from models.zotero_models import (
    ZoteroSyncStatus, ZoteroSyncAuditLog, ZoteroSyncJob,
    ZoteroConnection, ZoteroWebhookEvent
)

logger = logging.getLogger(__name__)


class ZoteroSyncMonitoringService:
    """Service for sync status monitoring and user notifications"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_sync_notification(
        self,
        connection_id: str,
        status_type: str,
        status: str,
        title: str,
        message: Optional[str] = None,
        progress_percentage: int = 0,
        details: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None
    ) -> str:
        """Create a sync status notification"""
        try:
            sync_status = ZoteroSyncStatus(
                connection_id=connection_id,
                status_type=status_type,
                status=status,
                title=title,
                message=message,
                progress_percentage=progress_percentage,
                details=details or {},
                expires_at=expires_at
            )
            
            self.db.add(sync_status)
            self.db.commit()
            
            return sync_status.id
            
        except Exception as e:
            logger.error(f"Error creating sync notification: {str(e)}")
            self.db.rollback()
            raise
    
    def get_sync_notifications(
        self,
        connection_id: str,
        status_type: Optional[str] = None,
        is_read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get sync notifications for a connection"""
        try:
            query = self.db.query(ZoteroSyncStatus).filter(
                ZoteroSyncStatus.connection_id == connection_id
            )
            
            if status_type:
                query = query.filter(ZoteroSyncStatus.status_type == status_type)
            
            if is_read is not None:
                query = query.filter(ZoteroSyncStatus.is_read == is_read)
            
            # Filter out expired notifications
            query = query.filter(
                or_(
                    ZoteroSyncStatus.expires_at.is_(None),
                    ZoteroSyncStatus.expires_at > datetime.utcnow()
                )
            )
            
            total_count = query.count()
            notifications = query.order_by(desc(ZoteroSyncStatus.created_at)).offset(offset).limit(limit).all()
            
            return {
                'notifications': [
                    {
                        'id': notification.id,
                        'status_type': notification.status_type,
                        'status': notification.status,
                        'title': notification.title,
                        'message': notification.message,
                        'progress_percentage': notification.progress_percentage,
                        'details': notification.details,
                        'is_read': notification.is_read,
                        'created_at': notification.created_at.isoformat(),
                        'updated_at': notification.updated_at.isoformat(),
                        'expires_at': notification.expires_at.isoformat() if notification.expires_at else None
                    }
                    for notification in notifications
                ],
                'total_count': total_count,
                'unread_count': self._get_unread_count(connection_id),
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            logger.error(f"Error getting sync notifications: {str(e)}")
            raise
    
    def mark_notification_as_read(self, notification_id: str, connection_id: str) -> bool:
        """Mark a notification as read"""
        try:
            notification = self.db.query(ZoteroSyncStatus).filter(
                and_(
                    ZoteroSyncStatus.id == notification_id,
                    ZoteroSyncStatus.connection_id == connection_id
                )
            ).first()
            
            if not notification:
                return False
            
            notification.is_read = True
            notification.updated_at = datetime.utcnow()
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            self.db.rollback()
            raise
    
    def mark_all_notifications_as_read(self, connection_id: str) -> int:
        """Mark all notifications as read for a connection"""
        try:
            updated_count = self.db.query(ZoteroSyncStatus).filter(
                and_(
                    ZoteroSyncStatus.connection_id == connection_id,
                    ZoteroSyncStatus.is_read == False
                )
            ).update({
                'is_read': True,
                'updated_at': datetime.utcnow()
            })
            
            self.db.commit()
            return updated_count
            
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            self.db.rollback()
            raise
    
    def delete_notification(self, notification_id: str, connection_id: str) -> bool:
        """Delete a notification"""
        try:
            notification = self.db.query(ZoteroSyncStatus).filter(
                and_(
                    ZoteroSyncStatus.id == notification_id,
                    ZoteroSyncStatus.connection_id == connection_id
                )
            ).first()
            
            if not notification:
                return False
            
            self.db.delete(notification)
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting notification: {str(e)}")
            self.db.rollback()
            raise
    
    def cleanup_expired_notifications(self) -> int:
        """Clean up expired notifications"""
        try:
            deleted_count = self.db.query(ZoteroSyncStatus).filter(
                and_(
                    ZoteroSyncStatus.expires_at.isnot(None),
                    ZoteroSyncStatus.expires_at <= datetime.utcnow()
                )
            ).delete()
            
            self.db.commit()
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired notifications: {str(e)}")
            self.db.rollback()
            raise
    
    def get_sync_history(
        self,
        connection_id: str,
        limit: int = 50,
        offset: int = 0,
        action_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get sync history from audit logs"""
        try:
            query = self.db.query(ZoteroSyncAuditLog).filter(
                ZoteroSyncAuditLog.connection_id == connection_id
            )
            
            if action_filter:
                query = query.filter(ZoteroSyncAuditLog.action == action_filter)
            
            total_count = query.count()
            history = query.order_by(desc(ZoteroSyncAuditLog.created_at)).offset(offset).limit(limit).all()
            
            return {
                'history': [
                    {
                        'id': log.id,
                        'sync_job_id': log.sync_job_id,
                        'action': log.action,
                        'target_type': log.target_type,
                        'target_id': log.target_id,
                        'user_id': log.user_id,
                        'old_data': log.old_data,
                        'new_data': log.new_data,
                        'created_at': log.created_at.isoformat(),
                        'audit_metadata': log.audit_metadata
                    }
                    for log in history
                ],
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            logger.error(f"Error getting sync history: {str(e)}")
            raise
    
    def get_sync_statistics(self, connection_id: str, days: int = 30) -> Dict[str, Any]:
        """Get sync statistics for a connection"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Get sync job statistics
            job_stats = self.db.query(
                ZoteroSyncJob.job_status,
                func.count(ZoteroSyncJob.id).label('count'),
                func.sum(ZoteroSyncJob.items_processed).label('total_items_processed'),
                func.sum(ZoteroSyncJob.items_added).label('total_items_added'),
                func.sum(ZoteroSyncJob.items_updated).label('total_items_updated'),
                func.sum(ZoteroSyncJob.items_deleted).label('total_items_deleted'),
                func.sum(ZoteroSyncJob.errors_count).label('total_errors')
            ).filter(
                and_(
                    ZoteroSyncJob.connection_id == connection_id,
                    ZoteroSyncJob.created_at >= since_date
                )
            ).group_by(ZoteroSyncJob.job_status).all()
            
            # Get webhook event statistics
            webhook_stats = self.db.query(
                ZoteroWebhookEvent.processing_status,
                func.count(ZoteroWebhookEvent.id).label('count')
            ).join(
                ZoteroSyncJob, ZoteroSyncJob.connection_id == connection_id
            ).filter(
                ZoteroWebhookEvent.created_at >= since_date
            ).group_by(ZoteroWebhookEvent.processing_status).all()
            
            # Get recent sync performance
            recent_jobs = self.db.query(ZoteroSyncJob).filter(
                and_(
                    ZoteroSyncJob.connection_id == connection_id,
                    ZoteroSyncJob.job_status == 'completed',
                    ZoteroSyncJob.completed_at >= since_date
                )
            ).order_by(desc(ZoteroSyncJob.completed_at)).limit(10).all()
            
            # Calculate average sync time
            avg_sync_time = 0
            if recent_jobs:
                total_time = sum(
                    (job.completed_at - job.started_at).total_seconds()
                    for job in recent_jobs
                    if job.started_at and job.completed_at
                )
                avg_sync_time = total_time / len(recent_jobs) if recent_jobs else 0
            
            # Format statistics
            job_status_counts = {stat.job_status: stat.count for stat in job_stats}
            webhook_status_counts = {stat.processing_status: stat.count for stat in webhook_stats}
            
            total_jobs = sum(job_status_counts.values())
            successful_jobs = job_status_counts.get('completed', 0)
            success_rate = (successful_jobs / total_jobs * 100) if total_jobs > 0 else 100
            
            return {
                'period_days': days,
                'sync_jobs': {
                    'total': total_jobs,
                    'completed': job_status_counts.get('completed', 0),
                    'failed': job_status_counts.get('failed', 0),
                    'queued': job_status_counts.get('queued', 0),
                    'running': job_status_counts.get('running', 0),
                    'cancelled': job_status_counts.get('cancelled', 0),
                    'success_rate': success_rate
                },
                'items': {
                    'total_processed': sum(stat.total_items_processed or 0 for stat in job_stats),
                    'total_added': sum(stat.total_items_added or 0 for stat in job_stats),
                    'total_updated': sum(stat.total_items_updated or 0 for stat in job_stats),
                    'total_deleted': sum(stat.total_items_deleted or 0 for stat in job_stats),
                    'total_errors': sum(stat.total_errors or 0 for stat in job_stats)
                },
                'webhook_events': {
                    'total': sum(webhook_status_counts.values()),
                    'completed': webhook_status_counts.get('completed', 0),
                    'failed': webhook_status_counts.get('failed', 0),
                    'pending': webhook_status_counts.get('pending', 0),
                    'processing': webhook_status_counts.get('processing', 0)
                },
                'performance': {
                    'average_sync_time_seconds': avg_sync_time,
                    'recent_jobs_count': len(recent_jobs)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting sync statistics: {str(e)}")
            raise
    
    def get_error_summary(
        self,
        connection_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get error summary for troubleshooting"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Get failed sync jobs with error details
            failed_jobs = self.db.query(ZoteroSyncJob).filter(
                and_(
                    ZoteroSyncJob.connection_id == connection_id,
                    ZoteroSyncJob.job_status == 'failed',
                    ZoteroSyncJob.created_at >= since_date
                )
            ).order_by(desc(ZoteroSyncJob.created_at)).limit(20).all()
            
            # Get error notifications
            error_notifications = self.db.query(ZoteroSyncStatus).filter(
                and_(
                    ZoteroSyncStatus.connection_id == connection_id,
                    ZoteroSyncStatus.status == 'error',
                    ZoteroSyncStatus.created_at >= since_date
                )
            ).order_by(desc(ZoteroSyncStatus.created_at)).limit(20).all()
            
            # Categorize errors
            error_categories = {}
            for job in failed_jobs:
                if job.error_details:
                    for error in job.error_details:
                        error_msg = error.get('error', 'Unknown error')
                        category = self._categorize_error(error_msg)
                        if category not in error_categories:
                            error_categories[category] = {
                                'count': 0,
                                'examples': [],
                                'latest_occurrence': None
                            }
                        error_categories[category]['count'] += 1
                        if len(error_categories[category]['examples']) < 3:
                            error_categories[category]['examples'].append(error_msg)
                        if not error_categories[category]['latest_occurrence'] or job.created_at > error_categories[category]['latest_occurrence']:
                            error_categories[category]['latest_occurrence'] = job.created_at
            
            return {
                'period_days': days,
                'failed_jobs': [
                    {
                        'id': job.id,
                        'job_type': job.job_type,
                        'created_at': job.created_at.isoformat(),
                        'error_count': job.errors_count,
                        'retry_count': job.retry_count,
                        'error_details': job.error_details
                    }
                    for job in failed_jobs
                ],
                'error_notifications': [
                    {
                        'id': notification.id,
                        'title': notification.title,
                        'message': notification.message,
                        'created_at': notification.created_at.isoformat(),
                        'details': notification.details
                    }
                    for notification in error_notifications
                ],
                'error_categories': {
                    category: {
                        'count': data['count'],
                        'examples': data['examples'],
                        'latest_occurrence': data['latest_occurrence'].isoformat() if data['latest_occurrence'] else None
                    }
                    for category, data in error_categories.items()
                },
                'total_failed_jobs': len(failed_jobs),
                'total_error_notifications': len(error_notifications)
            }
            
        except Exception as e:
            logger.error(f"Error getting error summary: {str(e)}")
            raise
    
    def create_progress_notification(
        self,
        connection_id: str,
        job_id: str,
        progress_percentage: int,
        items_processed: int,
        total_items: int,
        current_operation: str
    ) -> str:
        """Create or update a progress notification"""
        try:
            # Check if progress notification already exists for this job
            existing_notification = self.db.query(ZoteroSyncStatus).filter(
                and_(
                    ZoteroSyncStatus.connection_id == connection_id,
                    ZoteroSyncStatus.status_type == 'sync_progress',
                    ZoteroSyncStatus.details['job_id'].astext == job_id
                )
            ).first()
            
            if existing_notification:
                # Update existing notification
                existing_notification.progress_percentage = progress_percentage
                existing_notification.message = f"{current_operation} - {items_processed}/{total_items} items processed"
                existing_notification.details.update({
                    'items_processed': items_processed,
                    'total_items': total_items,
                    'current_operation': current_operation
                })
                existing_notification.updated_at = datetime.utcnow()
                self.db.commit()
                return existing_notification.id
            else:
                # Create new progress notification
                return self.create_sync_notification(
                    connection_id=connection_id,
                    status_type='sync_progress',
                    status='in_progress',
                    title='Sync in Progress',
                    message=f"{current_operation} - {items_processed}/{total_items} items processed",
                    progress_percentage=progress_percentage,
                    details={
                        'job_id': job_id,
                        'items_processed': items_processed,
                        'total_items': total_items,
                        'current_operation': current_operation
                    }
                )
                
        except Exception as e:
            logger.error(f"Error creating progress notification: {str(e)}")
            raise
    
    def create_error_notification(
        self,
        connection_id: str,
        job_id: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> str:
        """Create an error notification for sync failures"""
        try:
            return self.create_sync_notification(
                connection_id=connection_id,
                status_type='error_report',
                status='error',
                title='Sync Error',
                message=error_message,
                details={
                    'job_id': job_id,
                    'error_details': error_details or {},
                    'retry_count': retry_count,
                    'error_category': self._categorize_error(error_message)
                }
            )
            
        except Exception as e:
            logger.error(f"Error creating error notification: {str(e)}")
            raise
    
    def create_completion_notification(
        self,
        connection_id: str,
        job_id: str,
        items_processed: int,
        items_added: int,
        items_updated: int,
        items_deleted: int,
        sync_duration: float
    ) -> str:
        """Create a completion notification for successful syncs"""
        try:
            message = f"Sync completed successfully. Processed {items_processed} items"
            if items_added > 0:
                message += f", added {items_added}"
            if items_updated > 0:
                message += f", updated {items_updated}"
            if items_deleted > 0:
                message += f", deleted {items_deleted}"
            
            return self.create_sync_notification(
                connection_id=connection_id,
                status_type='completion_notification',
                status='completed',
                title='Sync Completed',
                message=message,
                progress_percentage=100,
                details={
                    'job_id': job_id,
                    'items_processed': items_processed,
                    'items_added': items_added,
                    'items_updated': items_updated,
                    'items_deleted': items_deleted,
                    'sync_duration_seconds': sync_duration
                },
                expires_at=datetime.utcnow() + timedelta(hours=24)  # Auto-expire after 24 hours
            )
            
        except Exception as e:
            logger.error(f"Error creating completion notification: {str(e)}")
            raise
    
    def create_warning_notification(
        self,
        connection_id: str,
        job_id: str,
        warning_message: str,
        warning_details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a warning notification for sync issues"""
        try:
            return self.create_sync_notification(
                connection_id=connection_id,
                status_type='warning',
                status='warning',
                title='Sync Warning',
                message=warning_message,
                details={
                    'job_id': job_id,
                    'warning_details': warning_details or {}
                },
                expires_at=datetime.utcnow() + timedelta(hours=48)  # Auto-expire after 48 hours
            )
            
        except Exception as e:
            logger.error(f"Error creating warning notification: {str(e)}")
            raise
    
    def log_sync_audit_event(
        self,
        connection_id: str,
        sync_job_id: Optional[str],
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log a sync audit event"""
        try:
            audit_log = ZoteroSyncAuditLog(
                connection_id=connection_id,
                sync_job_id=sync_job_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                old_data=old_data,
                new_data=new_data,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                audit_metadata=metadata or {}
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
            return audit_log.id
            
        except Exception as e:
            logger.error(f"Error logging sync audit event: {str(e)}")
            self.db.rollback()
            raise
    
    def get_real_time_sync_status(self, connection_id: str) -> Dict[str, Any]:
        """Get real-time sync status for a connection"""
        try:
            # Get active sync jobs
            active_jobs = self.db.query(ZoteroSyncJob).filter(
                and_(
                    ZoteroSyncJob.connection_id == connection_id,
                    ZoteroSyncJob.job_status.in_(['queued', 'running'])
                )
            ).all()
            
            # Get latest progress notifications
            progress_notifications = self.db.query(ZoteroSyncStatus).filter(
                and_(
                    ZoteroSyncStatus.connection_id == connection_id,
                    ZoteroSyncStatus.status_type == 'sync_progress',
                    ZoteroSyncStatus.status == 'in_progress'
                )
            ).order_by(ZoteroSyncStatus.updated_at.desc()).limit(5).all()
            
            # Get recent errors
            recent_errors = self.db.query(ZoteroSyncStatus).filter(
                and_(
                    ZoteroSyncStatus.connection_id == connection_id,
                    ZoteroSyncStatus.status == 'error',
                    ZoteroSyncStatus.created_at >= datetime.utcnow() - timedelta(hours=1)
                )
            ).count()
            
            return {
                'is_syncing': len(active_jobs) > 0,
                'active_jobs': [
                    {
                        'id': job.id,
                        'job_type': job.job_type,
                        'status': job.job_status,
                        'progress_percentage': job.progress_percentage,
                        'items_processed': job.items_processed,
                        'started_at': job.started_at.isoformat() if job.started_at else None
                    }
                    for job in active_jobs
                ],
                'progress_notifications': [
                    {
                        'id': notification.id,
                        'message': notification.message,
                        'progress_percentage': notification.progress_percentage,
                        'updated_at': notification.updated_at.isoformat()
                    }
                    for notification in progress_notifications
                ],
                'recent_error_count': recent_errors,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time sync status: {str(e)}")
            raise
    
    def _get_unread_count(self, connection_id: str) -> int:
        """Get count of unread notifications"""
        try:
            return self.db.query(ZoteroSyncStatus).filter(
                and_(
                    ZoteroSyncStatus.connection_id == connection_id,
                    ZoteroSyncStatus.is_read == False,
                    or_(
                        ZoteroSyncStatus.expires_at.is_(None),
                        ZoteroSyncStatus.expires_at > datetime.utcnow()
                    )
                )
            ).count()
            
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0
    
    def _categorize_error(self, error_message: str) -> str:
        """Categorize error message for better organization"""
        error_lower = error_message.lower()
        
        if 'network' in error_lower or 'connection' in error_lower or 'timeout' in error_lower:
            return 'Network/Connection'
        elif 'authentication' in error_lower or 'unauthorized' in error_lower or 'token' in error_lower:
            return 'Authentication'
        elif 'rate limit' in error_lower or 'too many requests' in error_lower:
            return 'Rate Limiting'
        elif 'permission' in error_lower or 'forbidden' in error_lower:
            return 'Permissions'
        elif 'not found' in error_lower or '404' in error_lower:
            return 'Resource Not Found'
        elif 'validation' in error_lower or 'invalid' in error_lower:
            return 'Data Validation'
        elif 'database' in error_lower or 'sql' in error_lower:
            return 'Database'
        elif 'conflict' in error_lower or 'version' in error_lower:
            return 'Sync Conflicts'
        else:
            return 'Other'