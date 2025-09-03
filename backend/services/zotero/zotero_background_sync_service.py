"""
Zotero background sync processing service
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from models.zotero_models import (
    ZoteroSyncJob, ZoteroConnection, ZoteroSyncConflict,
    ZoteroSyncStatus, ZoteroSyncAuditLog, ZoteroItem,
    ZoteroCollection, ZoteroLibrary
)
from services.zotero.zotero_sync_service import ZoteroSyncService
from services.zotero.zotero_client import ZoteroClient

logger = logging.getLogger(__name__)


class ZoteroBackgroundSyncService:
    """Service for background sync job processing and scheduling"""
    
    def __init__(self, db: Session):
        self.db = db
        self.sync_service = ZoteroSyncService(db)
        self.max_concurrent_jobs = 3
        self.retry_delays = [300, 900, 3600, 7200, 14400]  # 5min, 15min, 1hour, 2hours, 4hours
        self.job_timeout = 3600  # 1 hour timeout for jobs
        self.conflict_resolution_strategies = {
            'zotero_wins': self._resolve_zotero_wins,
            'local_wins': self._resolve_local_wins,
            'merge': self._resolve_merge,
            'manual': self._resolve_manual
        }
    
    async def process_sync_jobs(self) -> Dict[str, Any]:
        """Process queued sync jobs"""
        try:
            # Get queued jobs ordered by priority and scheduled time
            queued_jobs = self.db.query(ZoteroSyncJob).filter(
                ZoteroSyncJob.job_status == 'queued'
            ).order_by(
                asc(ZoteroSyncJob.priority),
                asc(ZoteroSyncJob.scheduled_at)
            ).limit(self.max_concurrent_jobs).all()
            
            if not queued_jobs:
                return {"processed_jobs": 0, "status": "no_jobs_queued"}
            
            # Process jobs concurrently
            tasks = []
            for job in queued_jobs:
                task = asyncio.create_task(self._process_single_job(job))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful and failed jobs
            successful_jobs = sum(1 for result in results if isinstance(result, dict) and result.get("status") == "success")
            failed_jobs = len(results) - successful_jobs
            
            return {
                "processed_jobs": len(queued_jobs),
                "successful_jobs": successful_jobs,
                "failed_jobs": failed_jobs,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Error processing sync jobs: {str(e)}")
            return {"error": str(e), "status": "error"}
    
    async def _process_single_job(self, job: ZoteroSyncJob) -> Dict[str, Any]:
        """Process a single sync job"""
        try:
            # Update job status to running
            job.job_status = 'running'
            job.started_at = datetime.utcnow()
            self.db.commit()
            
            # Log job start
            self._log_audit_event(
                connection_id=job.connection_id,
                sync_job_id=job.id,
                action='sync_started',
                new_data={
                    'job_type': job.job_type,
                    'priority': job.priority
                }
            )
            
            # Create sync status notification
            self._create_sync_status(
                connection_id=job.connection_id,
                status_type='sync_progress',
                status='in_progress',
                title=f'{job.job_type.replace("_", " ").title()} Started',
                message=f'Starting {job.job_type} synchronization...',
                progress_percentage=0
            )
            
            # Process based on job type
            if job.job_type == 'full_sync':
                result = await self._process_full_sync(job)
            elif job.job_type == 'incremental_sync':
                result = await self._process_incremental_sync(job)
            elif job.job_type == 'webhook_triggered':
                result = await self._process_webhook_triggered_sync(job)
            elif job.job_type == 'manual_sync':
                result = await self._process_manual_sync(job)
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")
            
            # Update job with results
            job.job_status = 'completed'
            job.completed_at = datetime.utcnow()
            job.progress_percentage = 100
            job.items_processed = result.get('items_processed', 0)
            job.items_added = result.get('items_added', 0)
            job.items_updated = result.get('items_updated', 0)
            job.items_deleted = result.get('items_deleted', 0)
            job.errors_count = result.get('errors_count', 0)
            job.error_details = result.get('error_details', [])
            
            self.db.commit()
            
            # Create completion notification
            self._create_sync_status(
                connection_id=job.connection_id,
                status_type='completion_notification',
                status='completed',
                title=f'{job.job_type.replace("_", " ").title()} Completed',
                message=f'Processed {job.items_processed} items successfully',
                details=result
            )
            
            # Log job completion
            self._log_audit_event(
                connection_id=job.connection_id,
                sync_job_id=job.id,
                action='sync_completed',
                new_data=result
            )
            
            return {"status": "success", "job_id": job.id, "result": result}
            
        except Exception as e:
            logger.error(f"Error processing sync job {job.id}: {str(e)}")
            
            # Update job status to failed
            job.job_status = 'failed'
            job.completed_at = datetime.utcnow()
            job.errors_count += 1
            if not job.error_details:
                job.error_details = []
            job.error_details.append({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Schedule retry if within retry limits
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                
                # Enhanced exponential backoff with jitter
                base_delay = self.retry_delays[min(job.retry_count - 1, len(self.retry_delays) - 1)]
                jitter = base_delay * 0.1 * (0.5 - asyncio.get_event_loop().time() % 1)  # Add jitter
                delay_seconds = base_delay + jitter
                
                # Check if connection has too many recent failures (circuit breaker)
                if self._should_circuit_break(job.connection_id):
                    delay_seconds *= 2  # Double delay for problematic connections
                
                job.next_retry_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
                job.job_status = 'queued'  # Re-queue for retry
                
                logger.info(f"Scheduled retry {job.retry_count}/{job.max_retries} for job {job.id} in {delay_seconds} seconds")
            
            self.db.commit()
            
            # Create error notification
            self._create_sync_status(
                connection_id=job.connection_id,
                status_type='error_report',
                status='error',
                title=f'{job.job_type.replace("_", " ").title()} Failed',
                message=f'Sync failed: {str(e)}',
                details={'error': str(e), 'retry_count': job.retry_count}
            )
            
            # Log error
            self._log_audit_event(
                connection_id=job.connection_id,
                sync_job_id=job.id,
                action='error_occurred',
                new_data={'error': str(e), 'retry_count': job.retry_count}
            )
            
            return {"status": "error", "job_id": job.id, "error": str(e)}
    
    async def _process_full_sync(self, job: ZoteroSyncJob) -> Dict[str, Any]:
        """Process full library synchronization"""
        try:
            connection = self.db.query(ZoteroConnection).filter(
                ZoteroConnection.id == job.connection_id
            ).first()
            
            if not connection:
                raise ValueError(f"Connection not found: {job.connection_id}")
            
            # Get all libraries for this connection
            libraries = self.db.query(ZoteroLibrary).filter(
                ZoteroLibrary.connection_id == job.connection_id
            ).all()
            
            total_items_processed = 0
            total_items_added = 0
            total_items_updated = 0
            total_items_deleted = 0
            total_errors = 0
            error_details = []
            
            for library in libraries:
                try:
                    # Update progress
                    progress = int((libraries.index(library) / len(libraries)) * 100)
                    job.progress_percentage = progress
                    self.db.commit()
                    
                    # Sync library
                    result = await self.sync_service.sync_library(
                        connection_id=job.connection_id,
                        library_id=library.id,
                        sync_type='full'
                    )
                    
                    total_items_processed += result.get('items_processed', 0)
                    total_items_added += result.get('items_added', 0)
                    total_items_updated += result.get('items_updated', 0)
                    total_items_deleted += result.get('items_deleted', 0)
                    
                    if result.get('errors'):
                        total_errors += len(result['errors'])
                        error_details.extend(result['errors'])
                    
                except Exception as e:
                    logger.error(f"Error syncing library {library.id}: {str(e)}")
                    total_errors += 1
                    error_details.append({
                        "library_id": library.id,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            return {
                'items_processed': total_items_processed,
                'items_added': total_items_added,
                'items_updated': total_items_updated,
                'items_deleted': total_items_deleted,
                'errors_count': total_errors,
                'error_details': error_details,
                'libraries_synced': len(libraries)
            }
            
        except Exception as e:
            logger.error(f"Error in full sync: {str(e)}")
            raise
    
    async def _process_incremental_sync(self, job: ZoteroSyncJob) -> Dict[str, Any]:
        """Process incremental synchronization"""
        try:
            connection = self.db.query(ZoteroConnection).filter(
                ZoteroConnection.id == job.connection_id
            ).first()
            
            if not connection:
                raise ValueError(f"Connection not found: {job.connection_id}")
            
            # Get libraries that need incremental sync
            libraries = self.db.query(ZoteroLibrary).filter(
                ZoteroLibrary.connection_id == job.connection_id
            ).all()
            
            total_items_processed = 0
            total_items_added = 0
            total_items_updated = 0
            total_items_deleted = 0
            total_errors = 0
            error_details = []
            
            for library in libraries:
                try:
                    # Update progress
                    progress = int((libraries.index(library) / len(libraries)) * 100)
                    job.progress_percentage = progress
                    self.db.commit()
                    
                    # Perform incremental sync
                    result = await self.sync_service.incremental_sync(
                        connection_id=job.connection_id,
                        library_id=library.id
                    )
                    
                    total_items_processed += result.get('items_processed', 0)
                    total_items_added += result.get('items_added', 0)
                    total_items_updated += result.get('items_updated', 0)
                    total_items_deleted += result.get('items_deleted', 0)
                    
                    if result.get('errors'):
                        total_errors += len(result['errors'])
                        error_details.extend(result['errors'])
                    
                    # Handle conflicts
                    conflicts = await self._detect_and_resolve_conflicts(job, library, result)
                    if conflicts:
                        total_errors += len(conflicts)
                        error_details.extend(conflicts)
                    
                except Exception as e:
                    logger.error(f"Error in incremental sync for library {library.id}: {str(e)}")
                    total_errors += 1
                    error_details.append({
                        "library_id": library.id,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            return {
                'items_processed': total_items_processed,
                'items_added': total_items_added,
                'items_updated': total_items_updated,
                'items_deleted': total_items_deleted,
                'errors_count': total_errors,
                'error_details': error_details,
                'libraries_synced': len(libraries)
            }
            
        except Exception as e:
            logger.error(f"Error in incremental sync: {str(e)}")
            raise
    
    async def _process_webhook_triggered_sync(self, job: ZoteroSyncJob) -> Dict[str, Any]:
        """Process webhook-triggered synchronization"""
        try:
            # Get webhook event data from job metadata
            webhook_events = job.job_metadata.get('webhook_events', [])
            trigger_event_data = job.job_metadata.get('trigger_event_data', {})
            
            # Determine what needs to be synced based on webhook data
            if 'library_id' in trigger_event_data:
                library_id = trigger_event_data['library_id']
                library = self.db.query(ZoteroLibrary).filter(
                    and_(
                        ZoteroLibrary.connection_id == job.connection_id,
                        ZoteroLibrary.zotero_library_id == library_id
                    )
                ).first()
                
                if library:
                    result = await self.sync_service.incremental_sync(
                        connection_id=job.connection_id,
                        library_id=library.id
                    )
                    
                    # Handle conflicts
                    conflicts = await self._detect_and_resolve_conflicts(job, library, result)
                    if conflicts:
                        result['errors_count'] = result.get('errors_count', 0) + len(conflicts)
                        result['error_details'] = result.get('error_details', []) + conflicts
                    
                    return result
                else:
                    raise ValueError(f"Library not found: {library_id}")
            else:
                # Fall back to incremental sync of all libraries
                return await self._process_incremental_sync(job)
            
        except Exception as e:
            logger.error(f"Error in webhook-triggered sync: {str(e)}")
            raise
    
    async def _process_manual_sync(self, job: ZoteroSyncJob) -> Dict[str, Any]:
        """Process manual synchronization"""
        try:
            # Manual sync is similar to incremental sync but with higher priority
            return await self._process_incremental_sync(job)
            
        except Exception as e:
            logger.error(f"Error in manual sync: {str(e)}")
            raise
    
    async def _detect_and_resolve_conflicts(
        self,
        job: ZoteroSyncJob,
        library: ZoteroLibrary,
        sync_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect and resolve sync conflicts"""
        try:
            conflicts = []
            
            # Check for version conflicts in sync result
            if 'conflicts' in sync_result:
                for conflict_data in sync_result['conflicts']:
                    conflict = await self._create_sync_conflict(
                        job=job,
                        conflict_data=conflict_data
                    )
                    
                    # Attempt automatic resolution
                    resolution_result = await self._resolve_conflict(conflict)
                    
                    if resolution_result['status'] != 'resolved':
                        conflicts.append({
                            'conflict_id': conflict.id,
                            'conflict_type': conflict.conflict_type,
                            'resolution_status': resolution_result['status'],
                            'error': resolution_result.get('error')
                        })
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Error detecting/resolving conflicts: {str(e)}")
            return [{'error': str(e)}]
    
    async def _create_sync_conflict(
        self,
        job: ZoteroSyncJob,
        conflict_data: Dict[str, Any]
    ) -> ZoteroSyncConflict:
        """Create a sync conflict record"""
        try:
            conflict = ZoteroSyncConflict(
                sync_job_id=job.id,
                item_id=conflict_data.get('item_id'),
                collection_id=conflict_data.get('collection_id'),
                conflict_type=conflict_data.get('conflict_type', 'version_mismatch'),
                local_version=conflict_data.get('local_version'),
                remote_version=conflict_data.get('remote_version'),
                local_data=conflict_data.get('local_data'),
                remote_data=conflict_data.get('remote_data'),
                resolution_strategy='zotero_wins'  # Default strategy
            )
            
            self.db.add(conflict)
            self.db.commit()
            
            return conflict
            
        except Exception as e:
            logger.error(f"Error creating sync conflict: {str(e)}")
            raise
    
    async def _resolve_conflict(self, conflict: ZoteroSyncConflict) -> Dict[str, Any]:
        """Resolve a sync conflict based on resolution strategy"""
        try:
            strategy_handler = self.conflict_resolution_strategies.get(
                conflict.resolution_strategy
            )
            
            if not strategy_handler:
                return {
                    'status': 'failed',
                    'error': f'Unknown resolution strategy: {conflict.resolution_strategy}'
                }
            
            result = await strategy_handler(conflict)
            
            # Update conflict status based on result
            if result['status'] == 'resolved':
                conflict.resolution_status = 'resolved'
                conflict.resolved_at = datetime.utcnow()
            elif result['status'] == 'manual_required':
                conflict.resolution_status = 'manual_required'
            else:
                conflict.resolution_status = 'failed'
            
            self.db.commit()
            return result
            
        except Exception as e:
            logger.error(f"Error resolving conflict {conflict.id}: {str(e)}")
            conflict.resolution_status = 'failed'
            self.db.commit()
            return {'status': 'failed', 'error': str(e)}
    
    async def _resolve_zotero_wins(self, conflict: ZoteroSyncConflict) -> Dict[str, Any]:
        """Resolve conflict by using Zotero data as source of truth"""
        try:
            if conflict.item_id:
                item = self.db.query(ZoteroItem).filter(
                    ZoteroItem.id == conflict.item_id
                ).first()
                
                if item and conflict.remote_data:
                    # Update local item with remote data
                    for key, value in conflict.remote_data.items():
                        if hasattr(item, key):
                            setattr(item, key, value)
                    
                    item.item_version = conflict.remote_version
                    self.db.commit()
            
            elif conflict.collection_id:
                collection = self.db.query(ZoteroCollection).filter(
                    ZoteroCollection.id == conflict.collection_id
                ).first()
                
                if collection and conflict.remote_data:
                    # Update local collection with remote data
                    for key, value in conflict.remote_data.items():
                        if hasattr(collection, key):
                            setattr(collection, key, value)
                    
                    collection.collection_version = conflict.remote_version
                    self.db.commit()
            
            return {'status': 'resolved', 'strategy': 'zotero_wins'}
            
        except Exception as e:
            logger.error(f"Error in zotero_wins resolution: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _resolve_local_wins(self, conflict: ZoteroSyncConflict) -> Dict[str, Any]:
        """Resolve conflict by keeping local data"""
        try:
            # For local_wins, we don't update the local data
            # but we need to push local changes to Zotero if possible
            
            if conflict.item_id and conflict.local_data:
                # In a real implementation, we would push local data to Zotero
                # For now, we just keep the local data unchanged
                pass
            
            elif conflict.collection_id and conflict.local_data:
                # Similar for collections
                pass
            
            return {'status': 'resolved', 'strategy': 'local_wins'}
            
        except Exception as e:
            logger.error(f"Error in local_wins resolution: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _resolve_merge(self, conflict: ZoteroSyncConflict) -> Dict[str, Any]:
        """Resolve conflict by merging local and remote data"""
        try:
            if conflict.item_id:
                item = self.db.query(ZoteroItem).filter(
                    ZoteroItem.id == conflict.item_id
                ).first()
                
                if item and conflict.remote_data and conflict.local_data:
                    # Merge strategy: prefer remote for metadata, keep local for notes/tags
                    merged_data = conflict.remote_data.copy()
                    
                    # Keep local notes and tags if they exist
                    if 'abstract_note' in conflict.local_data:
                        local_note = conflict.local_data.get('abstract_note', '')
                        remote_note = merged_data.get('abstract_note', '')
                        if local_note and remote_note and local_note != remote_note:
                            merged_data['abstract_note'] = f"{remote_note}\n\n[Local notes]: {local_note}"
                        elif local_note:
                            merged_data['abstract_note'] = local_note
                    
                    # Merge tags
                    local_tags = set(conflict.local_data.get('tags', []))
                    remote_tags = set(merged_data.get('tags', []))
                    merged_data['tags'] = list(local_tags.union(remote_tags))
                    
                    # Apply merged data
                    for key, value in merged_data.items():
                        if hasattr(item, key):
                            setattr(item, key, value)
                    
                    item.item_version = conflict.remote_version
                    self.db.commit()
            
            return {'status': 'resolved', 'strategy': 'merge'}
            
        except Exception as e:
            logger.error(f"Error in merge resolution: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _resolve_manual(self, conflict: ZoteroSyncConflict) -> Dict[str, Any]:
        """Mark conflict for manual resolution"""
        return {'status': 'manual_required', 'strategy': 'manual'}
    
    def schedule_sync_job(
        self,
        connection_id: str,
        job_type: str,
        priority: int = 5,
        scheduled_at: Optional[datetime] = None,
        job_metadata: Optional[Dict[str, Any]] = None,
        deduplicate: bool = True
    ) -> str:
        """Schedule a new sync job with deduplication and intelligent scheduling"""
        try:
            # Check for existing similar jobs if deduplication is enabled
            if deduplicate:
                existing_job = self._find_duplicate_job(connection_id, job_type, priority)
                if existing_job:
                    logger.info(f"Found duplicate job {existing_job.id}, updating priority if needed")
                    if priority < existing_job.priority:
                        existing_job.priority = priority
                        self.db.commit()
                    return existing_job.id
            
            # Determine optimal scheduling time based on job type and system load
            optimal_scheduled_at = self._calculate_optimal_schedule_time(
                job_type, scheduled_at, priority
            )
            
            job = ZoteroSyncJob(
                connection_id=connection_id,
                job_type=job_type,
                job_status='queued',
                priority=priority,
                scheduled_at=optimal_scheduled_at,
                job_metadata=job_metadata or {},
                max_retries=self._get_max_retries_for_job_type(job_type)
            )
            
            self.db.add(job)
            self.db.commit()
            
            # Log job scheduling
            self._log_audit_event(
                connection_id=connection_id,
                sync_job_id=job.id,
                action='sync_scheduled',
                new_data={
                    'job_type': job_type,
                    'priority': priority,
                    'scheduled_at': optimal_scheduled_at.isoformat()
                }
            )
            
            return job.id
            
        except Exception as e:
            logger.error(f"Error scheduling sync job: {str(e)}")
            self.db.rollback()
            raise
    
    def get_sync_jobs(
        self,
        connection_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get sync jobs with optional filtering"""
        try:
            query = self.db.query(ZoteroSyncJob)
            
            if connection_id:
                query = query.filter(ZoteroSyncJob.connection_id == connection_id)
            
            if status_filter:
                query = query.filter(ZoteroSyncJob.job_status == status_filter)
            
            total_count = query.count()
            jobs = query.order_by(desc(ZoteroSyncJob.created_at)).offset(offset).limit(limit).all()
            
            return {
                'jobs': [
                    {
                        'id': job.id,
                        'connection_id': job.connection_id,
                        'job_type': job.job_type,
                        'job_status': job.job_status,
                        'priority': job.priority,
                        'progress_percentage': job.progress_percentage,
                        'items_processed': job.items_processed,
                        'items_added': job.items_added,
                        'items_updated': job.items_updated,
                        'items_deleted': job.items_deleted,
                        'errors_count': job.errors_count,
                        'retry_count': job.retry_count,
                        'scheduled_at': job.scheduled_at.isoformat(),
                        'started_at': job.started_at.isoformat() if job.started_at else None,
                        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                        'next_retry_at': job.next_retry_at.isoformat() if job.next_retry_at else None
                    }
                    for job in jobs
                ],
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            logger.error(f"Error getting sync jobs: {str(e)}")
            raise
    
    def cancel_sync_job(self, job_id: str) -> bool:
        """Cancel a queued or running sync job"""
        try:
            job = self.db.query(ZoteroSyncJob).filter(
                ZoteroSyncJob.id == job_id
            ).first()
            
            if not job:
                return False
            
            if job.job_status in ['queued', 'running']:
                job.job_status = 'cancelled'
                job.completed_at = datetime.utcnow()
                self.db.commit()
                
                # Log cancellation
                self._log_audit_event(
                    connection_id=job.connection_id,
                    sync_job_id=job.id,
                    action='sync_cancelled'
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling sync job: {str(e)}")
            self.db.rollback()
            raise
    
    def _create_sync_status(
        self,
        connection_id: str,
        status_type: str,
        status: str,
        title: str,
        message: Optional[str] = None,
        progress_percentage: int = 0,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create a sync status notification"""
        try:
            sync_status = ZoteroSyncStatus(
                connection_id=connection_id,
                status_type=status_type,
                status=status,
                title=title,
                message=message,
                progress_percentage=progress_percentage,
                details=details or {}
            )
            
            self.db.add(sync_status)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error creating sync status: {str(e)}")
    
    def _log_audit_event(
        self,
        connection_id: str,
        action: str,
        sync_job_id: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        user_id: Optional[str] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log audit event"""
        try:
            audit_log = ZoteroSyncAuditLog(
                connection_id=connection_id,
                sync_job_id=sync_job_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                user_id=user_id,
                old_data=old_data,
                new_data=new_data
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging audit event: {str(e)}")
    
    def _find_duplicate_job(
        self,
        connection_id: str,
        job_type: str,
        priority: int
    ) -> Optional[ZoteroSyncJob]:
        """Find existing similar job that can be deduplicated"""
        try:
            # Look for queued jobs of the same type for the same connection
            existing_job = self.db.query(ZoteroSyncJob).filter(
                and_(
                    ZoteroSyncJob.connection_id == connection_id,
                    ZoteroSyncJob.job_type == job_type,
                    ZoteroSyncJob.job_status == 'queued',
                    ZoteroSyncJob.scheduled_at > datetime.utcnow() - timedelta(minutes=5)
                )
            ).first()
            
            return existing_job
            
        except Exception as e:
            logger.error(f"Error finding duplicate job: {str(e)}")
            return None
    
    def _calculate_optimal_schedule_time(
        self,
        job_type: str,
        requested_time: Optional[datetime],
        priority: int
    ) -> datetime:
        """Calculate optimal scheduling time based on system load and job type"""
        try:
            if requested_time:
                return requested_time
            
            base_time = datetime.utcnow()
            
            # Check current system load
            active_jobs_count = self.db.query(ZoteroSyncJob).filter(
                ZoteroSyncJob.job_status.in_(['queued', 'running'])
            ).count()
            
            # Add delay based on system load and job priority
            if active_jobs_count >= self.max_concurrent_jobs:
                # System is busy, add delay based on priority
                delay_minutes = max(1, (10 - priority) * 2)  # Higher priority = less delay
                base_time += timedelta(minutes=delay_minutes)
            
            # Add job-type specific delays
            job_type_delays = {
                'full_sync': timedelta(minutes=5),  # Full syncs are heavy, space them out
                'incremental_sync': timedelta(seconds=30),
                'webhook_triggered': timedelta(seconds=0),  # Immediate
                'manual_sync': timedelta(seconds=10)
            }
            
            delay = job_type_delays.get(job_type, timedelta(minutes=1))
            return base_time + delay
            
        except Exception as e:
            logger.error(f"Error calculating optimal schedule time: {str(e)}")
            return datetime.utcnow()
    
    def _get_max_retries_for_job_type(self, job_type: str) -> int:
        """Get maximum retry count based on job type"""
        retry_limits = {
            'full_sync': 2,  # Full syncs are expensive, limit retries
            'incremental_sync': 3,
            'webhook_triggered': 5,  # Webhook events should be retried more
            'manual_sync': 3
        }
        return retry_limits.get(job_type, 3)
    
    async def cleanup_old_jobs(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """Clean up old completed and failed jobs"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Count jobs to be deleted
            jobs_to_delete = self.db.query(ZoteroSyncJob).filter(
                and_(
                    ZoteroSyncJob.job_status.in_(['completed', 'failed', 'cancelled']),
                    ZoteroSyncJob.completed_at < cutoff_date
                )
            ).count()
            
            # Delete old jobs (cascading will handle related records)
            deleted_count = self.db.query(ZoteroSyncJob).filter(
                and_(
                    ZoteroSyncJob.job_status.in_(['completed', 'failed', 'cancelled']),
                    ZoteroSyncJob.completed_at < cutoff_date
                )
            ).delete()
            
            self.db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old sync jobs")
            
            return {
                'deleted_jobs': deleted_count,
                'cutoff_date': cutoff_date.isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old jobs: {str(e)}")
            self.db.rollback()
            return {'error': str(e), 'status': 'error'}
    
    async def get_job_queue_status(self) -> Dict[str, Any]:
        """Get current status of the job queue"""
        try:
            # Get job counts by status
            status_counts = {}
            for status in ['queued', 'running', 'completed', 'failed', 'cancelled']:
                count = self.db.query(ZoteroSyncJob).filter(
                    ZoteroSyncJob.job_status == status
                ).count()
                status_counts[status] = count
            
            # Get average processing time for completed jobs
            completed_jobs = self.db.query(ZoteroSyncJob).filter(
                and_(
                    ZoteroSyncJob.job_status == 'completed',
                    ZoteroSyncJob.started_at.isnot(None),
                    ZoteroSyncJob.completed_at.isnot(None)
                )
            ).limit(100).all()
            
            avg_processing_time = 0
            if completed_jobs:
                total_time = sum(
                    (job.completed_at - job.started_at).total_seconds()
                    for job in completed_jobs
                )
                avg_processing_time = total_time / len(completed_jobs)
            
            # Get next scheduled job
            next_job = self.db.query(ZoteroSyncJob).filter(
                ZoteroSyncJob.job_status == 'queued'
            ).order_by(
                asc(ZoteroSyncJob.priority),
                asc(ZoteroSyncJob.scheduled_at)
            ).first()
            
            return {
                'status_counts': status_counts,
                'total_jobs': sum(status_counts.values()),
                'avg_processing_time_seconds': avg_processing_time,
                'next_scheduled_job': {
                    'id': next_job.id,
                    'job_type': next_job.job_type,
                    'priority': next_job.priority,
                    'scheduled_at': next_job.scheduled_at.isoformat()
                } if next_job else None,
                'queue_health': self._assess_queue_health(status_counts)
            }
            
        except Exception as e:
            logger.error(f"Error getting job queue status: {str(e)}")
            return {'error': str(e), 'status': 'error'}
    
    def _assess_queue_health(self, status_counts: Dict[str, int]) -> str:
        """Assess the health of the job queue"""
        try:
            total_jobs = sum(status_counts.values())
            if total_jobs == 0:
                return 'idle'
            
            failed_ratio = status_counts.get('failed', 0) / total_jobs
            queued_count = status_counts.get('queued', 0)
            running_count = status_counts.get('running', 0)
            
            if failed_ratio > 0.2:  # More than 20% failed
                return 'unhealthy'
            elif queued_count > 50:  # Too many queued jobs
                return 'overloaded'
            elif running_count > self.max_concurrent_jobs:
                return 'overloaded'
            elif queued_count > 0 or running_count > 0:
                return 'active'
            else:
                return 'healthy'
                
        except Exception as e:
            logger.error(f"Error assessing queue health: {str(e)}")
            return 'unknown'
    
    def _should_circuit_break(self, connection_id: str) -> bool:
        """Check if connection should be circuit-broken due to too many failures"""
        try:
            # Check failure rate in the last hour
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            recent_jobs = self.db.query(ZoteroSyncJob).filter(
                and_(
                    ZoteroSyncJob.connection_id == connection_id,
                    ZoteroSyncJob.completed_at >= one_hour_ago
                )
            ).all()
            
            if len(recent_jobs) < 3:  # Not enough data
                return False
            
            failed_jobs = [job for job in recent_jobs if job.job_status == 'failed']
            failure_rate = len(failed_jobs) / len(recent_jobs)
            
            # Circuit break if failure rate > 50%
            return failure_rate > 0.5
            
        except Exception as e:
            logger.error(f"Error checking circuit breaker: {str(e)}")
            return False
    
    async def reset_connection_circuit_breaker(self, connection_id: str) -> Dict[str, Any]:
        """Reset circuit breaker for a connection by clearing recent failures"""
        try:
            # Cancel all queued retry jobs for this connection
            queued_retries = self.db.query(ZoteroSyncJob).filter(
                and_(
                    ZoteroSyncJob.connection_id == connection_id,
                    ZoteroSyncJob.job_status == 'queued',
                    ZoteroSyncJob.retry_count > 0
                )
            ).all()
            
            cancelled_count = 0
            for job in queued_retries:
                job.job_status = 'cancelled'
                job.completed_at = datetime.utcnow()
                cancelled_count += 1
            
            self.db.commit()
            
            # Log circuit breaker reset
            self._log_audit_event(
                connection_id=connection_id,
                action='circuit_breaker_reset',
                new_data={'cancelled_retry_jobs': cancelled_count}
            )
            
            return {
                'status': 'success',
                'cancelled_retry_jobs': cancelled_count,
                'message': 'Circuit breaker reset successfully'
            }
            
        except Exception as e:
            logger.error(f"Error resetting circuit breaker: {str(e)}")
            self.db.rollback()
            return {'error': str(e), 'status': 'error'}
    
    async def get_sync_performance_metrics(
        self,
        connection_id: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get sync performance metrics for monitoring"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = self.db.query(ZoteroSyncJob).filter(
                ZoteroSyncJob.completed_at >= start_date
            )
            
            if connection_id:
                query = query.filter(ZoteroSyncJob.connection_id == connection_id)
            
            jobs = query.all()
            
            if not jobs:
                return {
                    'total_jobs': 0,
                    'success_rate': 100.0,
                    'avg_processing_time': 0,
                    'throughput_per_hour': 0,
                    'error_rate': 0.0
                }
            
            # Calculate metrics
            completed_jobs = [j for j in jobs if j.job_status == 'completed']
            failed_jobs = [j for j in jobs if j.job_status == 'failed']
            
            success_rate = (len(completed_jobs) / len(jobs)) * 100 if jobs else 100.0
            error_rate = (len(failed_jobs) / len(jobs)) * 100 if jobs else 0.0
            
            # Calculate average processing time
            processing_times = []
            for job in completed_jobs:
                if job.started_at and job.completed_at:
                    processing_time = (job.completed_at - job.started_at).total_seconds()
                    processing_times.append(processing_time)
            
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            # Calculate throughput (jobs per hour)
            total_hours = days * 24
            throughput_per_hour = len(jobs) / total_hours
            
            # Calculate items processed
            total_items_processed = sum(job.items_processed or 0 for job in completed_jobs)
            total_items_added = sum(job.items_added or 0 for job in completed_jobs)
            total_items_updated = sum(job.items_updated or 0 for job in completed_jobs)
            total_items_deleted = sum(job.items_deleted or 0 for job in completed_jobs)
            
            # Get error breakdown
            error_types = {}
            for job in failed_jobs:
                if job.error_details:
                    for error in job.error_details:
                        error_msg = error.get('error', 'Unknown error')
                        error_type = error_msg.split(':')[0] if ':' in error_msg else 'Unknown'
                        error_types[error_type] = error_types.get(error_type, 0) + 1
            
            return {
                'period_days': days,
                'total_jobs': len(jobs),
                'completed_jobs': len(completed_jobs),
                'failed_jobs': len(failed_jobs),
                'success_rate': round(success_rate, 2),
                'error_rate': round(error_rate, 2),
                'avg_processing_time_seconds': round(avg_processing_time, 2),
                'throughput_per_hour': round(throughput_per_hour, 2),
                'total_items_processed': total_items_processed,
                'total_items_added': total_items_added,
                'total_items_updated': total_items_updated,
                'total_items_deleted': total_items_deleted,
                'error_breakdown': error_types,
                'performance_grade': self._calculate_performance_grade(success_rate, avg_processing_time)
            }
            
        except Exception as e:
            logger.error(f"Error getting sync performance metrics: {str(e)}")
            return {'error': str(e), 'status': 'error'}
    
    def _calculate_performance_grade(self, success_rate: float, avg_processing_time: float) -> str:
        """Calculate performance grade based on success rate and processing time"""
        try:
            if success_rate >= 95 and avg_processing_time <= 60:
                return 'A'
            elif success_rate >= 90 and avg_processing_time <= 120:
                return 'B'
            elif success_rate >= 80 and avg_processing_time <= 300:
                return 'C'
            elif success_rate >= 70:
                return 'D'
            else:
                return 'F'
        except:
            return 'Unknown'