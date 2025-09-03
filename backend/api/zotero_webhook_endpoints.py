"""
Zotero webhook API endpoints
"""
import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from services.auth_service import get_current_user
from services.zotero.zotero_webhook_service import ZoteroWebhookService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zotero/webhooks", tags=["zotero-webhooks"])


class WebhookEndpointCreate(BaseModel):
    connection_id: str = Field(..., description="Zotero connection ID")
    webhook_url: str = Field(..., description="Webhook URL endpoint")
    webhook_secret: Optional[str] = Field(None, description="Optional webhook secret")


class WebhookEventPayload(BaseModel):
    event_type: str = Field(..., description="Type of webhook event")
    event_data: Dict[str, Any] = Field(..., description="Event data payload")


class WebhookEndpointUpdate(BaseModel):
    status: str = Field(..., description="New webhook status")
    error_message: Optional[str] = Field(None, description="Optional error message")


@router.post("/endpoints")
async def register_webhook_endpoint(
    endpoint_data: WebhookEndpointCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register a new webhook endpoint for Zotero notifications"""
    try:
        webhook_service = ZoteroWebhookService(db)
        
        result = webhook_service.register_webhook_endpoint(
            user_id=current_user["id"],
            connection_id=endpoint_data.connection_id,
            webhook_url=endpoint_data.webhook_url,
            webhook_secret=endpoint_data.webhook_secret
        )
        
        return {
            "status": "success",
            "message": "Webhook endpoint registered successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error registering webhook endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/endpoints")
async def get_webhook_endpoints(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all webhook endpoints for the current user"""
    try:
        webhook_service = ZoteroWebhookService(db)
        
        endpoints = webhook_service.get_webhook_endpoints(current_user["id"])
        
        return {
            "status": "success",
            "data": {
                "endpoints": endpoints,
                "total_count": len(endpoints)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting webhook endpoints: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/endpoints/{endpoint_id}/status")
async def update_webhook_endpoint_status(
    endpoint_id: str,
    update_data: WebhookEndpointUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update webhook endpoint status"""
    try:
        webhook_service = ZoteroWebhookService(db)
        
        webhook_service.update_webhook_endpoint_status(
            endpoint_id=endpoint_id,
            status=update_data.status,
            error_message=update_data.error_message
        )
        
        return {
            "status": "success",
            "message": "Webhook endpoint status updated successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating webhook endpoint status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/endpoints/{endpoint_id}")
async def delete_webhook_endpoint(
    endpoint_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a webhook endpoint"""
    try:
        webhook_service = ZoteroWebhookService(db)
        
        success = webhook_service.delete_webhook_endpoint(
            endpoint_id=endpoint_id,
            user_id=current_user["id"]
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Webhook endpoint not found")
        
        return {
            "status": "success",
            "message": "Webhook endpoint deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting webhook endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/endpoints/{endpoint_id}/events")
async def process_webhook_event(
    endpoint_id: str,
    event_payload: WebhookEventPayload,
    request: Request,
    x_zotero_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Process incoming webhook event from Zotero"""
    try:
        webhook_service = ZoteroWebhookService(db)
        
        # Get raw request body for signature validation
        raw_payload = await request.body()
        
        result = webhook_service.process_webhook_event(
            endpoint_id=endpoint_id,
            event_type=event_payload.event_type,
            event_data=event_payload.event_data,
            signature=x_zotero_signature,
            raw_payload=raw_payload
        )
        
        return {
            "status": "success",
            "message": "Webhook event processed successfully",
            "data": result
        }
        
    except ValueError as e:
        logger.warning(f"Invalid webhook event: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing webhook event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/endpoints/{endpoint_id}/events")
async def get_webhook_events(
    endpoint_id: str,
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get webhook events for an endpoint"""
    try:
        webhook_service = ZoteroWebhookService(db)
        
        # Verify user owns the endpoint
        endpoints = webhook_service.get_webhook_endpoints(current_user["id"])
        if not any(ep["id"] == endpoint_id for ep in endpoints):
            raise HTTPException(status_code=404, detail="Webhook endpoint not found")
        
        result = webhook_service.get_webhook_events(
            endpoint_id=endpoint_id,
            limit=limit,
            offset=offset,
            status_filter=status_filter
        )
        
        return {
            "status": "success",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting webhook events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/endpoints/{endpoint_id}/events/retry")
async def retry_failed_webhook_events(
    endpoint_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retry failed webhook events for an endpoint"""
    try:
        webhook_service = ZoteroWebhookService(db)
        
        # Verify user owns the endpoint
        endpoints = webhook_service.get_webhook_endpoints(current_user["id"])
        if not any(ep["id"] == endpoint_id for ep in endpoints):
            raise HTTPException(status_code=404, detail="Webhook endpoint not found")
        
        result = webhook_service.retry_failed_webhook_events(endpoint_id)
        
        return {
            "status": "success",
            "message": f"Retried {result['retried_count']} failed webhook events",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying failed webhook events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/endpoints/{endpoint_id}/health")
async def check_webhook_endpoint_health(
    endpoint_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check webhook endpoint health and connectivity"""
    try:
        webhook_service = ZoteroWebhookService(db)
        
        # Verify user owns the endpoint
        endpoints = webhook_service.get_webhook_endpoints(current_user["id"])
        endpoint = next((ep for ep in endpoints if ep["id"] == endpoint_id), None)
        
        if not endpoint:
            raise HTTPException(status_code=404, detail="Webhook endpoint not found")
        
        # Get recent events to assess health
        recent_events = webhook_service.get_webhook_events(
            endpoint_id=endpoint_id,
            limit=10,
            offset=0
        )
        
        # Calculate health metrics
        total_events = recent_events["total_count"]
        failed_events = len([e for e in recent_events["events"] if e["processing_status"] == "failed"])
        success_rate = ((total_events - failed_events) / total_events * 100) if total_events > 0 else 100
        
        health_status = "healthy"
        if endpoint["error_count"] > 5:
            health_status = "unhealthy"
        elif endpoint["error_count"] > 2 or success_rate < 80:
            health_status = "degraded"
        
        return {
            "status": "success",
            "data": {
                "endpoint_id": endpoint_id,
                "health_status": health_status,
                "success_rate": success_rate,
                "total_events": total_events,
                "failed_events": failed_events,
                "error_count": endpoint["error_count"],
                "last_ping_at": endpoint["last_ping_at"],
                "last_error_at": endpoint["last_error_at"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking webhook endpoint health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))