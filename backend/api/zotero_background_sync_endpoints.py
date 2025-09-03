"""
Zotero background sync API endpoints
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from services.auth_service import get_current_user
from services.zotero.zotero_background_sync_service import ZoteroBackgroundSyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zotero/sync", tags=["zotero-background-sync"])


class SyncJobCreate(BaseModel):
    connection_id: str = Field(..., description="Zotero connection ID")
    job_type: str = Field(..., description="Type of sync job")
    priority: int = Field(5, description="Job priority (1-10, lower is higher priority)")
    scheduled_at: Optional[datetime] = Field(None, description="When to schedule the job")
    job_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional job metadata")


class SyncJobUpdate(BaseModel):
    job_status: Optional[str] = Field(None, description="New job status")
    priority: Optional[int] = Field(None, description="New job priority")


@router.post("/jobs")
async def schedule_sync_job(
    job_data: SyncJobCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Schedule a new sync job"""
    try:
        sync_service = ZoteroBackgroundSyncService(db)
        
        # Validate job type
        valid_job_types = ['full_sync', 'incremental_sync', 'webhook_triggered', 'manual_sync']
        if job_data.job_type not in valid_job_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid job type. Must be one of: {', '.join(valid_job_types)}"
            )
        
        # Validate priority
        if not 1 <= job_data.priority <= 10:
            raise HTTPException(
                status_code=400,
                detail="Priority must be between 1 and 10"
            )
        
        job_id = sync_service.schedule_sync_job(
            connection_id=job_data.connection_id,
            job_type=job_data.job_type,
            priority=job_data.priority,
            scheduled_at=job_data.scheduled_at,
            job_metadata=job_data.job_metadata
        )
        
        return {
            "status": "success",
            "message": "Sync job scheduled successfully",
            "data": {
                "job_id": job_id,
                "job_type": job_data.job_type,
                "priority": job_data.priority,
                "scheduled_at": job_data.scheduled_at.isoformat() if job_data.scheduled_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling sync job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def get_sync_jobs(
    connection_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sync jobs with optional filtering"""
    try:
        sync_service = ZoteroBackgroundSyncService(db)
        
        # Validate limit
        if limit > 100:
            limit = 100
        
        result = sync_service.get_sync_jobs(
            connection_id=connection_id,
            status_filter=status_filter,
            limit=limit,
            offset=offset
        )
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error getting sync jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}")
async def get_sync_job(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific sync job"""
    try:
        sync_service = ZoteroBackgroundSyncService(db)
        
        result = sync_service.get_sync_jobs(limit=1, offset=0)
        job = next((j for j in result['jobs'] if j['id'] == job_id), None)
        
        if not job:
            raise HTTPException(status_code=404, detail="Sync job not found")
        
        return {
            "status": "success",
            "data": job
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sync job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/cancel")
async def cancel_sync_job(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a queued or running sync job"""
    try:
        sync_service = ZoteroBackgroundSyncService(db)
        
        success = sync_service.cancel_sync_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Job cannot be cancelled (not found or already completed)"
            )
        
        return {
            "status": "success",
            "message": "Sync job cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling sync job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/process")
async def process_sync_jobs(
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger processing of queued sync jobs"""
    try:
        sync_service = ZoteroBackgroundSyncService(db)
        
        # Add background task to process jobs
        background_tasks.add_task(sync_service.process_sync_jobs)
        
        return {
            "status": "success",
            "message": "Sync job processing started in background"
        }
        
    except Exception as e:
        logger.error(f"Error starting sync job processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/stats")
async def get_sync_job_stats(
    connection_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sync job statistics"""
    try:
        sync_service = ZoteroBackgroundSyncService(db)
        
        # Get jobs for different statuses
        all_jobs = sync_service.get_sync_jobs(connection_id=connection_id, limit=1000)
        jobs = all_jobs['jobs']
        
        # Calculate statistics
        stats = {
            'total_jobs': len(jobs),
            'queued_jobs': len([j for j in jobs if j['job_status'] == 'queued']),
            'running_jobs': len([j for j in jobs if j['job_status'] == 'running']),
            'completed_jobs': len([j for j in jobs if j['job_status'] == 'completed']),
            'failed_jobs': len([j for j in jobs if j['job_status'] == 'failed']),
            'cancelled_jobs': len([j for j in jobs if j['job_status'] == 'cancelled']),
            'total_items_processed': sum(j.get('items_processed', 0) for j in jobs),
            'total_items_added': sum(j.get('items_added', 0) for j in jobs),
            'total_items_updated': sum(j.get('items_updated', 0) for j in jobs),
            'total_items_deleted': sum(j.get('items_deleted', 0) for j in jobs),
            'total_errors': sum(j.get('errors_count', 0) for j in jobs)
        }
        
        # Calculate success rate
        completed_and_failed = stats['completed_jobs'] + stats['failed_jobs']
        if completed_and_failed > 0:
            stats['success_rate'] = (stats['completed_jobs'] / completed_and_failed) * 100
        else:
            stats['success_rate'] = 100.0
        
        # Get job type breakdown
        job_types = {}
        for job in jobs:
            job_type = job['job_type']
            if job_type not in job_types:
                job_types[job_type] = {
                    'total': 0,
                    'completed': 0,
                    'failed': 0,
                    'queued': 0,
                    'running': 0
                }
            job_types[job_type]['total'] += 1
            job_types[job_type][job['job_status']] += 1
        
        stats['job_types'] = job_types
        
        return {
            "status": "success",
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting sync job stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connections/{connection_id}/sync")
async def trigger_connection_sync(
    connection_id: str,
    sync_type: str = "incremental",
    priority: int = 3,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger immediate sync for a specific connection"""
    try:
        sync_service = ZoteroBackgroundSyncService(db)
        
        # Validate sync type
        valid_sync_types = ['full_sync', 'incremental_sync', 'manual_sync']
        if sync_type not in valid_sync_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sync type. Must be one of: {', '.join(valid_sync_types)}"
            )
        
        # Schedule immediate sync job
        job_id = sync_service.schedule_sync_job(
            connection_id=connection_id,
            job_type=sync_type,
            priority=priority,
            scheduled_at=datetime.utcnow(),
            job_metadata={
                'triggered_by': 'user',
                'user_id': current_user['id']
            }
        )
        
        return {
            "status": "success",
            "message": f"Sync job scheduled for connection {connection_id}",
            "data": {
                "job_id": job_id,
                "sync_type": sync_type,
                "priority": priority
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering connection sync: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conflicts")
async def get_sync_conflicts(
    connection_id: Optional[str] = None,
    resolution_status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sync conflicts with optional filtering"""
    try:
        from models.zotero_models import ZoteroSyncConflict, ZoteroSyncJob
        from sqlalchemy import and_
        
        query = db.query(ZoteroSyncConflict).join(ZoteroSyncJob)
        
        if connection_id:
            query = query.filter(ZoteroSyncJob.connection_id == connection_id)
        
        if resolution_status:
            query = query.filter(ZoteroSyncConflict.resolution_status == resolution_status)
        
        total_count = query.count()
        conflicts = query.order_by(ZoteroSyncConflict.created_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "status": "success",
            "data": {
                "conflicts": [
                    {
                        "id": conflict.id,
                        "sync_job_id": conflict.sync_job_id,
                        "item_id": conflict.item_id,
                        "collection_id": conflict.collection_id,
                        "conflict_type": conflict.conflict_type,
                        "local_version": conflict.local_version,
                        "remote_version": conflict.remote_version,
                        "resolution_strategy": conflict.resolution_strategy,
                        "resolution_status": conflict.resolution_status,
                        "resolved_at": conflict.resolved_at.isoformat() if conflict.resolved_at else None,
                        "resolved_by": conflict.resolved_by,
                        "resolution_notes": conflict.resolution_notes,
                        "created_at": conflict.created_at.isoformat()
                    }
                    for conflict in conflicts
                ],
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting sync conflicts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_sync_conflict(
    conflict_id: str,
    resolution_strategy: str,
    resolution_notes: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually resolve a sync conflict"""
    try:
        from models.zotero_models import ZoteroSyncConflict
        
        conflict = db.query(ZoteroSyncConflict).filter(
            ZoteroSyncConflict.id == conflict_id
        ).first()
        
        if not conflict:
            raise HTTPException(status_code=404, detail="Sync conflict not found")
        
        # Validate resolution strategy
        valid_strategies = ['zotero_wins', 'local_wins', 'merge', 'manual']
        if resolution_strategy not in valid_strategies:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid resolution strategy. Must be one of: {', '.join(valid_strategies)}"
            )
        
        # Update conflict
        conflict.resolution_strategy = resolution_strategy
        conflict.resolution_status = 'resolved' if resolution_strategy != 'manual' else 'manual_required'
        conflict.resolved_at = datetime.utcnow()
        conflict.resolved_by = current_user['id']
        conflict.resolution_notes = resolution_notes
        
        db.commit()
        
        return {
            "status": "success",
            "message": "Sync conflict resolved successfully",
            "data": {
                "conflict_id": conflict_id,
                "resolution_strategy": resolution_strategy,
                "resolution_status": conflict.resolution_status
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving sync conflict: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/status")
async def get_queue_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current status of the sync job queue"""
    try:
        sync_service = ZoteroBackgroundSyncService(db)
        result = await sync_service.get_job_queue_status()
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error getting queue status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue/cleanup")
async def cleanup_old_jobs(
    days_to_keep: int = 30,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean up old completed and failed jobs"""
    try:
        if days_to_keep < 1 or days_to_keep > 365:
            raise HTTPException(
                status_code=400,
                detail="days_to_keep must be between 1 and 365"
            )
        
        sync_service = ZoteroBackgroundSyncService(db)
        result = await sync_service.cleanup_old_jobs(days_to_keep)
        
        return {
            "status": "success",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up old jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/metrics")
async def get_performance_metrics(
    connection_id: Optional[str] = None,
    days: int = 7,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sync performance metrics"""
    try:
        if days < 1 or days > 90:
            raise HTTPException(
                status_code=400,
                detail="days must be between 1 and 90"
            )
        
        sync_service = ZoteroBackgroundSyncService(db)
        result = await sync_service.get_sync_performance_metrics(connection_id, days)
        
        return {
            "status": "success",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connections/{connection_id}/circuit-breaker/reset")
async def reset_circuit_breaker(
    connection_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset circuit breaker for a connection"""
    try:
        sync_service = ZoteroBackgroundSyncService(db)
        result = await sync_service.reset_connection_circuit_breaker(connection_id)
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error resetting circuit breaker: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/bulk-schedule")
async def bulk_schedule_jobs(
    jobs_data: List[SyncJobCreate],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Schedule multiple sync jobs in bulk"""
    try:
        if len(jobs_data) > 50:
            raise HTTPException(
                status_code=400,
                detail="Cannot schedule more than 50 jobs at once"
            )
        
        sync_service = ZoteroBackgroundSyncService(db)
        scheduled_jobs = []
        errors = []
        
        for job_data in jobs_data:
            try:
                # Validate job type
                valid_job_types = ['full_sync', 'incremental_sync', 'webhook_triggered', 'manual_sync']
                if job_data.job_type not in valid_job_types:
                    errors.append({
                        'connection_id': job_data.connection_id,
                        'error': f"Invalid job type: {job_data.job_type}"
                    })
                    continue
                
                job_id = sync_service.schedule_sync_job(
                    connection_id=job_data.connection_id,
                    job_type=job_data.job_type,
                    priority=job_data.priority,
                    scheduled_at=job_data.scheduled_at,
                    job_metadata=job_data.job_metadata,
                    deduplicate=True
                )
                
                scheduled_jobs.append({
                    'job_id': job_id,
                    'connection_id': job_data.connection_id,
                    'job_type': job_data.job_type
                })
                
            except Exception as e:
                errors.append({
                    'connection_id': job_data.connection_id,
                    'error': str(e)
                })
        
        return {
            "status": "success",
            "data": {
                "scheduled_jobs": scheduled_jobs,
                "errors": errors,
                "total_requested": len(jobs_data),
                "total_scheduled": len(scheduled_jobs),
                "total_errors": len(errors)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk scheduling jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/retry-history")
async def get_job_retry_history(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get retry history for a specific job"""
    try:
        from models.zotero_models import ZoteroSyncJob
        
        job = db.query(ZoteroSyncJob).filter(
            ZoteroSyncJob.id == job_id
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Sync job not found")
        
        retry_history = []
        if job.error_details:
            for i, error in enumerate(job.error_details):
                retry_history.append({
                    'attempt': i + 1,
                    'error': error.get('error', 'Unknown error'),
                    'timestamp': error.get('timestamp'),
                    'retry_delay': error.get('retry_delay')
                })
        
        return {
            "status": "success",
            "data": {
                "job_id": job_id,
                "total_retries": job.retry_count,
                "max_retries": job.max_retries,
                "next_retry_at": job.next_retry_at.isoformat() if job.next_retry_at else None,
                "retry_history": retry_history,
                "current_status": job.job_status
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job retry history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))