"""
Zotero webhook handling service
"""
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models.zotero_models import (
    ZoteroWebhookEndpoint, ZoteroWebhookEvent, ZoteroSyncJob,
    ZoteroConnection, ZoteroSyncStatus, ZoteroSyncAuditLog
)
from services.zotero.zotero_sync_service import ZoteroSyncService

logger = logging.getLogger(__name__)


class ZoteroWebhookService:
    """Service for handling Zotero webhooks and real-time synchronization"""
    
    def __init__(self, db: Session):
        self.db = db
        self.sync_service = ZoteroSyncService(db)
    
    def register_webhook_endpoint(
        self,
        user_id: str,
        connection_id: str,
        webhook_url: str,
        webhook_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register a new webhook endpoint for a Zotero connection"""
        try:
            # Generate webhook secret if not provided
            if not webhook_secret:
                webhook_secret = self._generate_webhook_secret()
            
            # Check if endpoint already exists
            existing_endpoint = self.db.query(ZoteroWebhookEndpoint).filter(
                and_(
                    ZoteroWebhookEndpoint.connection_id == connection_id,
                    ZoteroWebhookEndpoint.webhook_url == webhook_url
                )
            ).first()
            
            if existing_endpoint:
                # Update existing endpoint
                existing_endpoint.webhook_secret = webhook_secret
                existing_endpoint.webhook_status = 'active'
                existing_endpoint.error_count = 0
                existing_endpoint.updated_at = datetime.utcnow()
                endpoint = existing_endpoint
            else:
                # Create new endpoint
                endpoint = ZoteroWebhookEndpoint(
                    user_id=user_id,
                    connection_id=connection_id,
                    webhook_url=webhook_url,
                    webhook_secret=webhook_secret,
                    webhook_status='active'
                )
                self.db.add(endpoint)
            
            self.db.commit()
            
            # Log the registration
            self._log_audit_event(
                connection_id=connection_id,
                action='webhook_registered',
                target_type='webhook',
                target_id=endpoint.id,
                user_id=user_id,
                new_data={'webhook_url': webhook_url}
            )
            
            return {
                'endpoint_id': endpoint.id,
                'webhook_url': endpoint.webhook_url,
                'webhook_secret': endpoint.webhook_secret,
                'status': endpoint.webhook_status
            }
            
        except Exception as e:
            logger.error(f"Error registering webhook endpoint: {str(e)}")
            self.db.rollback()
            raise
    
    def validate_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        webhook_secret: str
    ) -> bool:
        """Validate webhook signature using HMAC-SHA256"""
        try:
            # Create expected signature
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures (constant time comparison)
            return hmac.compare_digest(f"sha256={expected_signature}", signature)
            
        except Exception as e:
            logger.error(f"Error validating webhook signature: {str(e)}")
            return False
    
    def process_webhook_event(
        self,
        endpoint_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        signature: Optional[str] = None,
        raw_payload: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Process incoming webhook event"""
        try:
            # Get webhook endpoint
            endpoint = self.db.query(ZoteroWebhookEndpoint).filter(
                ZoteroWebhookEndpoint.id == endpoint_id
            ).first()
            
            if not endpoint:
                raise ValueError(f"Webhook endpoint not found: {endpoint_id}")
            
            # Validate signature if provided
            if signature and raw_payload:
                if not self.validate_webhook_signature(raw_payload, signature, endpoint.webhook_secret):
                    raise ValueError("Invalid webhook signature")
            
            # Create webhook event record
            webhook_event = ZoteroWebhookEvent(
                endpoint_id=endpoint_id,
                event_type=event_type,
                event_data=event_data,
                processing_status='pending'
            )
            self.db.add(webhook_event)
            self.db.commit()
            
            # Update endpoint last ping
            endpoint.last_ping_at = datetime.utcnow()
            endpoint.error_count = 0
            self.db.commit()
            
            # Process the event asynchronously
            self._queue_sync_job_for_event(webhook_event)
            
            return {
                'event_id': webhook_event.id,
                'status': 'accepted',
                'processing_status': webhook_event.processing_status
            }
            
        except Exception as e:
            logger.error(f"Error processing webhook event: {str(e)}")
            if endpoint:
                endpoint.error_count += 1
                endpoint.last_error_at = datetime.utcnow()
                if endpoint.error_count >= 5:
                    endpoint.webhook_status = 'error'
                self.db.commit()
            raise
    
    def _queue_sync_job_for_event(self, webhook_event: ZoteroWebhookEvent) -> None:
        """Queue a sync job based on webhook event"""
        try:
            endpoint = webhook_event.endpoint
            connection_id = endpoint.connection_id
            
            # Determine sync type based on event
            job_type = self._determine_sync_type(webhook_event.event_type, webhook_event.event_data)
            
            # Check if there's already a pending job for this connection
            existing_job = self.db.query(ZoteroSyncJob).filter(
                and_(
                    ZoteroSyncJob.connection_id == connection_id,
                    ZoteroSyncJob.job_status.in_(['queued', 'running'])
                )
            ).first()
            
            if existing_job:
                # Update existing job metadata to include this event
                if 'webhook_events' not in existing_job.job_metadata:
                    existing_job.job_metadata['webhook_events'] = []
                existing_job.job_metadata['webhook_events'].append(webhook_event.id)
                existing_job.job_metadata['last_webhook_event'] = webhook_event.id
            else:
                # Create new sync job
                sync_job = ZoteroSyncJob(
                    connection_id=connection_id,
                    job_type=job_type,
                    job_status='queued',
                    priority=2,  # Higher priority for webhook-triggered syncs
                    job_metadata={
                        'webhook_events': [webhook_event.id],
                        'trigger_event_type': webhook_event.event_type,
                        'trigger_event_data': webhook_event.event_data
                    }
                )
                self.db.add(sync_job)
            
            # Update webhook event status
            webhook_event.processing_status = 'processing'
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error queuing sync job for webhook event: {str(e)}")
            webhook_event.processing_status = 'failed'
            webhook_event.error_message = str(e)
            self.db.commit()
    
    def _determine_sync_type(self, event_type: str, event_data: Dict[str, Any]) -> str:
        """Determine the appropriate sync job type based on webhook event"""
        if event_type in ['library_update', 'full_sync_required']:
            return 'incremental_sync'
        elif event_type in ['item_update', 'collection_update', 'attachment_update']:
            return 'webhook_triggered'
        else:
            return 'incremental_sync'
    
    def get_webhook_endpoints(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all webhook endpoints for a user"""
        try:
            endpoints = self.db.query(ZoteroWebhookEndpoint).filter(
                ZoteroWebhookEndpoint.user_id == user_id
            ).all()
            
            return [
                {
                    'id': endpoint.id,
                    'connection_id': endpoint.connection_id,
                    'webhook_url': endpoint.webhook_url,
                    'status': endpoint.webhook_status,
                    'last_ping_at': endpoint.last_ping_at.isoformat() if endpoint.last_ping_at else None,
                    'last_error_at': endpoint.last_error_at.isoformat() if endpoint.last_error_at else None,
                    'error_count': endpoint.error_count,
                    'created_at': endpoint.created_at.isoformat()
                }
                for endpoint in endpoints
            ]
            
        except Exception as e:
            logger.error(f"Error getting webhook endpoints: {str(e)}")
            raise
    
    def update_webhook_endpoint_status(
        self,
        endpoint_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Update webhook endpoint status"""
        try:
            endpoint = self.db.query(ZoteroWebhookEndpoint).filter(
                ZoteroWebhookEndpoint.id == endpoint_id
            ).first()
            
            if not endpoint:
                raise ValueError(f"Webhook endpoint not found: {endpoint_id}")
            
            endpoint.webhook_status = status
            endpoint.updated_at = datetime.utcnow()
            
            if error_message:
                endpoint.last_error_at = datetime.utcnow()
                endpoint.error_count += 1
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating webhook endpoint status: {str(e)}")
            self.db.rollback()
            raise
    
    def delete_webhook_endpoint(self, endpoint_id: str, user_id: str) -> bool:
        """Delete a webhook endpoint"""
        try:
            endpoint = self.db.query(ZoteroWebhookEndpoint).filter(
                and_(
                    ZoteroWebhookEndpoint.id == endpoint_id,
                    ZoteroWebhookEndpoint.user_id == user_id
                )
            ).first()
            
            if not endpoint:
                return False
            
            # Log the deletion
            self._log_audit_event(
                connection_id=endpoint.connection_id,
                action='webhook_deleted',
                target_type='webhook',
                target_id=endpoint_id,
                user_id=user_id,
                old_data={'webhook_url': endpoint.webhook_url}
            )
            
            self.db.delete(endpoint)
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting webhook endpoint: {str(e)}")
            self.db.rollback()
            raise
    
    def get_webhook_events(
        self,
        endpoint_id: str,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get webhook events for an endpoint"""
        try:
            query = self.db.query(ZoteroWebhookEvent).filter(
                ZoteroWebhookEvent.endpoint_id == endpoint_id
            )
            
            if status_filter:
                query = query.filter(ZoteroWebhookEvent.processing_status == status_filter)
            
            total_count = query.count()
            events = query.order_by(ZoteroWebhookEvent.created_at.desc()).offset(offset).limit(limit).all()
            
            return {
                'events': [
                    {
                        'id': event.id,
                        'event_type': event.event_type,
                        'event_data': event.event_data,
                        'processing_status': event.processing_status,
                        'retry_count': event.retry_count,
                        'error_message': event.error_message,
                        'created_at': event.created_at.isoformat(),
                        'processed_at': event.processed_at.isoformat() if event.processed_at else None
                    }
                    for event in events
                ],
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            logger.error(f"Error getting webhook events: {str(e)}")
            raise
    
    def retry_failed_webhook_events(self, endpoint_id: str) -> Dict[str, Any]:
        """Retry failed webhook events for an endpoint"""
        try:
            failed_events = self.db.query(ZoteroWebhookEvent).filter(
                and_(
                    ZoteroWebhookEvent.endpoint_id == endpoint_id,
                    ZoteroWebhookEvent.processing_status == 'failed',
                    ZoteroWebhookEvent.retry_count < ZoteroWebhookEvent.max_retries
                )
            ).all()
            
            retried_count = 0
            for event in failed_events:
                event.processing_status = 'retrying'
                event.retry_count += 1
                event.next_retry_at = datetime.utcnow() + timedelta(minutes=5 * event.retry_count)
                event.error_message = None
                
                # Queue sync job for retry
                self._queue_sync_job_for_event(event)
                retried_count += 1
            
            self.db.commit()
            
            return {
                'retried_count': retried_count,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error retrying failed webhook events: {str(e)}")
            self.db.rollback()
            raise
    
    def _generate_webhook_secret(self) -> str:
        """Generate a secure webhook secret"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def _log_audit_event(
        self,
        connection_id: str,
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        user_id: Optional[str] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log audit event"""
        try:
            audit_log = ZoteroSyncAuditLog(
                connection_id=connection_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                user_id=user_id,
                old_data=old_data,
                new_data=new_data,
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.db.add(audit_log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging audit event: {str(e)}")