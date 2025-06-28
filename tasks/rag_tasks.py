"""
Celery tasks for RAG processing of synced documents
"""

import os
import logging
from celery import Celery, Task
from datetime import datetime
import tempfile
from pathlib import Path

# Configure Celery
broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery_app = Celery('rag_tasks', broker=broker_url, backend=result_backend)

logger = logging.getLogger(__name__)

class LoggingTask(Task):
    """Task base class with logging"""
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {self.name}[{task_id}] succeeded: {retval}")
        return super().on_success(retval, task_id, args, kwargs)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {self.name}[{task_id}] failed: {exc}")
        return super().on_failure(exc, task_id, args, kwargs, einfo)

@celery_app.task(base=LoggingTask, bind=True, max_retries=2)
def process_synced_document_task(self, document_id, temp_file_path):
    """Process a synced document for RAG"""
    try:
        # Import here to avoid circular imports
        from models import db, SyncedDocument, ExternalDataSource
        from services.rag_service import RAGService
        
        # Create Flask app context
        from app_enterprise import app
        with app.app_context():
            # Get document
            document = SyncedDocument.query.get(document_id)
            if not document:
                raise Exception(f"Document not found: {document_id}")
            
            # Update processing status
            document.update_processing_status('processing')
            
            # Get user ID from data source
            data_source = ExternalDataSource.query.get(document.data_source_id)
            if not data_source:
                raise Exception(f"Data source not found: {document.data_source_id}")
            
            user_id = data_source.user_id
            
            # Check if file exists
            if not os.path.exists(temp_file_path):
                raise Exception(f"Temp file not found: {temp_file_path}")
            
            # Process document based on file type
            rag_service = RAGService()
            
            # Create metadata
            metadata = {
                'source': f"synced_{data_source.source_type}",
                'source_name': data_source.source_name,
                'file_name': document.file_name,
                'synced_at': document.last_synced_at.isoformat(),
                'external_id': document.external_id
            }
            
            # Process document
            result = rag_service.process_document(
                user_id=user_id,
                file_path=temp_file_path,
                file_name=document.file_name,
                metadata=metadata
            )
            
            if result['success']:
                # Update document status
                document.update_processing_status(
                    'completed',
                    vector_count=result.get('chunk_count', 0)
                )
                
                # Update data source document count
                data_source.total_documents = SyncedDocument.query.filter_by(
                    data_source_id=data_source.id,
                    processing_status='completed'
                ).count()
                db.session.commit()
                
                # Clean up temp file
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temp file: {e}")
                
                return {
                    'success': True,
                    'document_id': document_id,
                    'vectors_created': result.get('chunk_count', 0)
                }
            else:
                # Update document status
                document.update_processing_status('error', error_message=result.get('error'))
                
                # Clean up temp file
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temp file: {e}")
                
                raise Exception(result.get('error', 'Unknown error during RAG processing'))
            
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        
        # Update document status if possible
        try:
            from models import db, SyncedDocument
            from app_enterprise import app
            with app.app_context():
                document = SyncedDocument.query.get(document_id)
                if document:
                    document.update_processing_status('error', error_message=str(e))
        except Exception as inner_e:
            logger.error(f"Error updating document status: {inner_e}")
        
        # Clean up temp file
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except Exception as clean_e:
            logger.warning(f"Failed to remove temp file: {clean_e}")
        
        # Retry with delay
        retry_in = 300  # 5 minutes
        self.retry(exc=e, countdown=retry_in)
        
        return {'success': False, 'error': str(e)}