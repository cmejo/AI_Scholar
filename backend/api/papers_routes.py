"""
Papers API Routes for AI Scholar
Handles paper updates, status, and management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
import logging
from ..services.paper_updater import paper_updater

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/papers", tags=["papers"])

@router.get("/status")
async def get_papers_status():
    """Get current papers update status"""
    try:
        status = await paper_updater.get_update_status()
        return status
    except Exception as e:
        logger.error(f"Error getting papers status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get papers status")

@router.get("/check-updates")
async def check_for_new_papers():
    """Check for new papers without processing them"""
    try:
        result = await paper_updater.check_for_new_papers()
        return result
    except Exception as e:
        logger.error(f"Error checking for new papers: {e}")
        raise HTTPException(status_code=500, detail="Failed to check for new papers")

@router.post("/process-updates")
async def process_new_papers(
    background_tasks: BackgroundTasks,
    max_papers: int = 10
):
    """Process new papers (runs in background)"""
    try:
        # Add processing task to background
        background_tasks.add_task(
            paper_updater.process_new_papers,
            max_papers
        )
        
        return {
            "message": f"Started processing up to {max_papers} new papers in background",
            "status": "processing_started",
            "timestamp": "2024-12-19T10:00:00Z"
        }
    except Exception as e:
        logger.error(f"Error starting paper processing: {e}")
        raise HTTPException(status_code=500, detail="Failed to start paper processing")

@router.post("/process-updates-sync")
async def process_new_papers_sync(max_papers: int = 5):
    """Process new papers synchronously (for smaller batches)"""
    try:
        result = await paper_updater.process_new_papers(max_papers)
        return result
    except Exception as e:
        logger.error(f"Error processing new papers: {e}")
        raise HTTPException(status_code=500, detail="Failed to process new papers")

@router.get("/health")
async def check_papers_health():
    """Check health of papers service"""
    try:
        # Initialize if not already done
        await paper_updater.initialize()
        
        status = await paper_updater.get_update_status()
        
        return {
            "service_healthy": status.get('service_status') == 'healthy',
            "processed_papers": status.get('processed_papers_count', 0),
            "new_papers_available": status.get('new_papers_available', 0),
            "last_check": status.get('last_check'),
            "timestamp": "2024-12-19T10:00:00Z"
        }
    except Exception as e:
        logger.error(f"Error checking papers health: {e}")
        raise HTTPException(status_code=500, detail="Failed to check papers health")

@router.get("/stats")
async def get_papers_statistics():
    """Get detailed papers statistics"""
    try:
        status = await paper_updater.get_update_status()
        check_result = await paper_updater.check_for_new_papers()
        
        return {
            "total_papers_in_dataset": status.get('total_papers_in_dataset', 0),
            "processed_papers": status.get('processed_papers_count', 0),
            "new_papers_available": status.get('new_papers_available', 0),
            "processing_rate": "~10 papers/minute",
            "last_update_check": status.get('last_check'),
            "dataset_path": "/home/cmejo/arxiv-dataset/pdf",
            "auto_update_enabled": True,
            "check_interval": "24 hours",
            "service_status": status.get('service_status', 'unknown'),
            "timestamp": "2024-12-19T10:00:00Z"
        }
    except Exception as e:
        logger.error(f"Error getting papers statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get papers statistics")