"""
Celery tasks for automated knowledge syncing
"""

import os
import logging
from celery import Celery, Task
from celery.schedules import crontab
from datetime import datetime, timedelta

# Configure Celery
broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery_app = Celery('sync_tasks', broker=broker_url, backend=result_backend)

# Configure Celery Beat schedule
celery_app.conf.beat_schedule = {
    'sync-data-sources-daily': {
        'task': 'tasks.sync_tasks.schedule_daily_syncs',
        'schedule': crontab(hour=3, minute=0),  # Run at 3:00 AM every day
    },
    'sync-data-sources-hourly': {
        'task': 'tasks.sync_tasks.schedule_hourly_syncs',
        'schedule': crontab(minute=15),  # Run at 15 minutes past every hour
    },
}

logger = logging.getLogger(__name__)

class LoggingTask(Task):
    """Task base class with logging"""
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {self.name}[{task_id}] succeeded: {retval}")
        return super().on_success(retval, task_id, args, kwargs)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {self.name}[{task_id}] failed: {exc}")
        return super().on_failure(exc, task_id, args, kwargs, einfo)

@celery_app.task(base=LoggingTask)
def schedule_daily_syncs():
    """Schedule sync tasks for data sources with daily frequency"""
    try:
        # Import here to avoid circular imports
        from models import db, ExternalDataSource
        from services.automated_sync_service import AutomatedSyncService
        
        # Create Flask app context
        from app_enterprise import app
        with app.app_context():
            # Get data sources with daily frequency
            data_sources = ExternalDataSource.query.filter_by(
                sync_enabled=True,
                sync_frequency='daily'
            ).all()
            
            sync_service = AutomatedSyncService()
            
            for source in data_sources:
                # Skip sources synced in the last 20 hours
                if source.last_sync_at and datetime.utcnow() - source.last_sync_at < timedelta(hours=20):
                    logger.info(f"Skipping recently synced source: {source.id}")
                    continue
                
                # Trigger sync
                result = sync_service.trigger_sync(source.id, 'incremental_sync')
                logger.info(f"Scheduled sync for source {source.id}: {result}")
            
            return {
                'success': True,
                'scheduled_count': len(data_sources)
            }
            
    except Exception as e:
        logger.error(f"Error scheduling daily syncs: {e}")
        return {'success': False, 'error': str(e)}

@celery_app.task(base=LoggingTask)
def schedule_hourly_syncs():
    """Schedule sync tasks for data sources with hourly frequency"""
    try:
        # Import here to avoid circular imports
        from models import db, ExternalDataSource
        from services.automated_sync_service import AutomatedSyncService
        
        # Create Flask app context
        from app_enterprise import app
        with app.app_context():
            # Get data sources with hourly frequency
            data_sources = ExternalDataSource.query.filter_by(
                sync_enabled=True,
                sync_frequency='hourly'
            ).all()
            
            sync_service = AutomatedSyncService()
            
            for source in data_sources:
                # Skip sources synced in the last 50 minutes
                if source.last_sync_at and datetime.utcnow() - source.last_sync_at < timedelta(minutes=50):
                    logger.info(f"Skipping recently synced source: {source.id}")
                    continue
                
                # Trigger sync
                result = sync_service.trigger_sync(source.id, 'incremental_sync')
                logger.info(f"Scheduled sync for source {source.id}: {result}")
            
            return {
                'success': True,
                'scheduled_count': len(data_sources)
            }
            
    except Exception as e:
        logger.error(f"Error scheduling hourly syncs: {e}")
        return {'success': False, 'error': str(e)}

@celery_app.task(base=LoggingTask, bind=True, max_retries=3)
def sync_data_source_task(self, data_source_id, job_id):
    """Sync a specific data source"""
    try:
        # Import here to avoid circular imports
        from services.automated_sync_service import AutomatedSyncService
        
        # Create Flask app context
        from app_enterprise import app
        with app.app_context():
            sync_service = AutomatedSyncService()
            result = sync_service.sync_data_source(data_source_id, job_id)
            
            if not result['success']:
                raise Exception(result.get('error', 'Unknown error'))
            
            return result
            
    except Exception as e:
        logger.error(f"Error syncing data source {data_source_id}: {e}")
        
        # Retry with exponential backoff
        retry_in = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
        self.retry(exc=e, countdown=retry_in)
        
        return {'success': False, 'error': str(e)}