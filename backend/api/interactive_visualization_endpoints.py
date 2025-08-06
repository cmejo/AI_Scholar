"""
Interactive Visualization API Endpoints for AI Scholar Advanced RAG System

This module provides REST API endpoints for interactive visualization management,
real-time collaboration, and annotation features.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..services.interactive_visualization_service import (
    interactive_visualization_service,
    VisualizationType,
    InteractionType,
    VisualizationData,
    Visualization
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/visualizations", tags=["interactive-visualizations"])

# Pydantic models for API requests/responses

class CreateVisualizationRequest(BaseModel):
    title: str = Field(..., description="Visualization title")
    description: str = Field(..., description="Visualization description")
    visualization_type: str = Field(..., description="Type of visualization")
    data: Dict[str, Any] = Field(..., description="Visualization data")
    layout: Dict[str, Any] = Field(default_factory=dict, description="Layout configuration")
    config: Dict[str, Any] = Field(default_factory=dict, description="Visualization config")
    traces: Optional[List[Dict[str, Any]]] = Field(default=None, description="Plotly traces")
    tags: Optional[List[str]] = Field(default=None, description="Tags for categorization")

class UpdateVisualizationRequest(BaseModel):
    data_updates: Dict[str, Any] = Field(..., description="Data updates")
    update_type: str = Field(default="data", description="Type of update")

class AddAnnotationRequest(BaseModel):
    content: str = Field(..., description="Annotation content")
    position: Dict[str, float] = Field(..., description="Position coordinates")
    annotation_type: str = Field(default="text", description="Type of annotation")
    style: Optional[Dict[str, Any]] = Field(default=None, description="Annotation style")

class UpdateAnnotationRequest(BaseModel):
    updates: Dict[str, Any] = Field(..., description="Annotation updates")

class RecordInteractionRequest(BaseModel):
    interaction_type: str = Field(..., description="Type of interaction")
    interaction_data: Dict[str, Any] = Field(..., description="Interaction data")
    coordinates: Optional[Dict[str, float]] = Field(default=None, description="Interaction coordinates")

class CollaboratorRequest(BaseModel):
    collaborator_id: str = Field(..., description="User ID of collaborator")

class GenerateEmbedRequest(BaseModel):
    width: int = Field(default=800, description="Embed width")
    height: int = Field(default=600, description="Embed height")
    interactive: bool = Field(default=True, description="Enable interactivity")

class VisualizationSummary(BaseModel):
    visualization_id: str
    title: str
    description: str
    type: str
    created_at: str
    modified_at: str
    owner_id: str
    is_owner: bool
    collaborators_count: int
    annotations_count: int
    version: int
    tags: List[str]

# Dependency for user authentication (simplified)
async def get_current_user() -> str:
    """Get current user ID - simplified implementation"""
    # In production, this would validate JWT tokens and return user info
    return "user_123"

@router.post("/", response_model=Dict[str, str])
async def create_visualization(
    request: CreateVisualizationRequest,
    current_user: str = Depends(get_current_user)
):
    """Create a new interactive visualization"""
    try:
        # Validate visualization type
        try:
            viz_type = VisualizationType(request.visualization_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported visualization type: {request.visualization_type}"
            )
        
        # Create visualization data
        viz_data = VisualizationData(
            data=request.data,
            layout=request.layout,
            config=request.config,
            traces=request.traces or []
        )
        
        # Create visualization
        visualization = await interactive_visualization_service.create_visualization(
            title=request.title,
            description=request.description,
            visualization_type=viz_type,
            data=viz_data,
            owner_id=current_user,
            tags=request.tags
        )
        
        return {
            "visualization_id": visualization.visualization_id,
            "message": "Visualization created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating visualization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create visualization: {str(e)}"
        )

@router.get("/", response_model=List[VisualizationSummary])
async def list_visualizations(current_user: str = Depends(get_current_user)):
    """List all visualizations accessible to the current user"""
    try:
        visualizations = await interactive_visualization_service.list_user_visualizations(current_user)
        return [VisualizationSummary(**viz) for viz in visualizations]
        
    except Exception as e:
        logger.error(f"Error listing visualizations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list visualizations: {str(e)}"
        )

@router.get("/{visualization_id}")
async def get_visualization(
    visualization_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get a specific visualization by ID"""
    try:
        visualization = await interactive_visualization_service.get_visualization(
            visualization_id, current_user
        )
        
        if not visualization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Visualization not found or access denied"
            )
        
        # Convert to dict for JSON response
        return {
            "visualization_id": visualization.visualization_id,
            "title": visualization.title,
            "description": visualization.description,
            "visualization_type": visualization.visualization_type.value,
            "data": {
                "data": visualization.data.data,
                "layout": visualization.data.layout,
                "config": visualization.data.config,
                "traces": visualization.data.traces
            },
            "owner_id": visualization.owner_id,
            "collaborators": visualization.collaborators,
            "annotations": [
                {
                    "annotation_id": ann.annotation_id,
                    "user_id": ann.user_id,
                    "content": ann.content,
                    "position": ann.position,
                    "annotation_type": ann.annotation_type,
                    "style": ann.style,
                    "created_at": ann.created_at.isoformat(),
                    "modified_at": ann.modified_at.isoformat(),
                    "replies": ann.replies
                }
                for ann in visualization.annotations
            ],
            "created_at": visualization.created_at.isoformat(),
            "modified_at": visualization.modified_at.isoformat(),
            "version": visualization.version,
            "is_public": visualization.is_public,
            "tags": visualization.tags
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting visualization {visualization_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get visualization: {str(e)}"
        )

@router.put("/{visualization_id}/data")
async def update_visualization_data(
    visualization_id: str,
    request: UpdateVisualizationRequest,
    current_user: str = Depends(get_current_user)
):
    """Update visualization data with real-time sync"""
    try:
        success = await interactive_visualization_service.update_visualization_data(
            visualization_id=visualization_id,
            user_id=current_user,
            data_updates=request.data_updates,
            update_type=request.update_type
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Visualization not found or access denied"
            )
        
        return {"message": "Visualization updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating visualization {visualization_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update visualization: {str(e)}"
        )

@router.post("/{visualization_id}/annotations")
async def add_annotation(
    visualization_id: str,
    request: AddAnnotationRequest,
    current_user: str = Depends(get_current_user)
):
    """Add annotation to visualization"""
    try:
        annotation_id = await interactive_visualization_service.add_annotation(
            visualization_id=visualization_id,
            user_id=current_user,
            content=request.content,
            position=request.position,
            annotation_type=request.annotation_type,
            style=request.style
        )
        
        if not annotation_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Visualization not found or access denied"
            )
        
        return {
            "annotation_id": annotation_id,
            "message": "Annotation added successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding annotation to visualization {visualization_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add annotation: {str(e)}"
        )

@router.put("/{visualization_id}/annotations/{annotation_id}")
async def update_annotation(
    visualization_id: str,
    annotation_id: str,
    request: UpdateAnnotationRequest,
    current_user: str = Depends(get_current_user)
):
    """Update existing annotation"""
    try:
        success = await interactive_visualization_service.update_annotation(
            visualization_id=visualization_id,
            annotation_id=annotation_id,
            user_id=current_user,
            updates=request.updates
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Visualization or annotation not found, or access denied"
            )
        
        return {"message": "Annotation updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating annotation {annotation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update annotation: {str(e)}"
        )

@router.delete("/{visualization_id}/annotations/{annotation_id}")
async def delete_annotation(
    visualization_id: str,
    annotation_id: str,
    current_user: str = Depends(get_current_user)
):
    """Delete annotation"""
    try:
        success = await interactive_visualization_service.delete_annotation(
            visualization_id=visualization_id,
            annotation_id=annotation_id,
            user_id=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Visualization or annotation not found, or access denied"
            )
        
        return {"message": "Annotation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting annotation {annotation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete annotation: {str(e)}"
        )

@router.post("/{visualization_id}/interactions")
async def record_interaction(
    visualization_id: str,
    request: RecordInteractionRequest,
    current_user: str = Depends(get_current_user)
):
    """Record user interaction with visualization"""
    try:
        # Validate interaction type
        try:
            interaction_type = InteractionType(request.interaction_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid interaction type: {request.interaction_type}"
            )
        
        success = await interactive_visualization_service.record_interaction(
            visualization_id=visualization_id,
            user_id=current_user,
            interaction_type=interaction_type,
            interaction_data=request.interaction_data,
            coordinates=request.coordinates
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Visualization not found or access denied"
            )
        
        return {"message": "Interaction recorded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording interaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record interaction: {str(e)}"
        )

@router.post("/{visualization_id}/collaborators")
async def add_collaborator(
    visualization_id: str,
    request: CollaboratorRequest,
    current_user: str = Depends(get_current_user)
):
    """Add collaborator to visualization"""
    try:
        success = await interactive_visualization_service.add_collaborator(
            visualization_id=visualization_id,
            collaborator_id=request.collaborator_id,
            owner_id=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Visualization not found or you don't have permission to add collaborators"
            )
        
        return {"message": "Collaborator added successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding collaborator: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add collaborator: {str(e)}"
        )

@router.delete("/{visualization_id}/collaborators/{collaborator_id}")
async def remove_collaborator(
    visualization_id: str,
    collaborator_id: str,
    current_user: str = Depends(get_current_user)
):
    """Remove collaborator from visualization"""
    try:
        success = await interactive_visualization_service.remove_collaborator(
            visualization_id=visualization_id,
            collaborator_id=collaborator_id,
            owner_id=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Visualization not found or you don't have permission to remove collaborators"
            )
        
        return {"message": "Collaborator removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing collaborator: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove collaborator: {str(e)}"
        )

@router.post("/{visualization_id}/embed")
async def generate_embed_code(
    visualization_id: str,
    request: GenerateEmbedRequest,
    current_user: str = Depends(get_current_user)
):
    """Generate embeddable HTML code for visualization"""
    try:
        embed_code = await interactive_visualization_service.generate_embed_code(
            visualization_id=visualization_id,
            user_id=current_user,
            width=request.width,
            height=request.height,
            interactive=request.interactive
        )
        
        if not embed_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Visualization not found or access denied"
            )
        
        return {
            "embed_code": embed_code,
            "width": request.width,
            "height": request.height,
            "interactive": request.interactive,
            "message": "Embed code generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating embed code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embed code: {str(e)}"
        )

@router.post("/{visualization_id}/sessions/join")
async def join_session(
    visualization_id: str,
    current_user: str = Depends(get_current_user)
):
    """Join collaborative session for visualization"""
    try:
        success = await interactive_visualization_service.join_session(
            visualization_id=visualization_id,
            user_id=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Visualization not found or access denied"
            )
        
        return {"message": "Joined session successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to join session: {str(e)}"
        )

@router.post("/{visualization_id}/sessions/leave")
async def leave_session(
    visualization_id: str,
    current_user: str = Depends(get_current_user)
):
    """Leave collaborative session"""
    try:
        success = await interactive_visualization_service.leave_session(
            visualization_id=visualization_id,
            user_id=current_user
        )
        
        return {"message": "Left session successfully"}
        
    except Exception as e:
        logger.error(f"Error leaving session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to leave session: {str(e)}"
        )

@router.get("/{visualization_id}/updates")
async def get_visualization_updates(
    visualization_id: str,
    since: Optional[str] = None,
    current_user: str = Depends(get_current_user)
):
    """Get updates for visualization since timestamp"""
    try:
        # Parse timestamp if provided
        since_timestamp = None
        if since:
            try:
                since_timestamp = datetime.fromisoformat(since.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid timestamp format"
                )
        
        updates = await interactive_visualization_service.get_visualization_updates(
            visualization_id=visualization_id,
            since_timestamp=since_timestamp
        )
        
        # Convert updates to dict format
        return {
            "updates": [
                {
                    "update_id": update.update_id,
                    "user_id": update.user_id,
                    "update_type": update.update_type,
                    "changes": update.changes,
                    "timestamp": update.timestamp.isoformat()
                }
                for update in updates
            ],
            "count": len(updates)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting updates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get updates: {str(e)}"
        )

@router.get("/libraries/supported")
async def get_supported_libraries():
    """Get list of supported visualization libraries"""
    try:
        return {
            "libraries": interactive_visualization_service.supported_libraries,
            "message": "Supported libraries retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting supported libraries: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get supported libraries: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint for interactive visualization service"""
    try:
        return {
            "status": "healthy",
            "service": "interactive-visualization",
            "visualizations_count": len(interactive_visualization_service.visualizations),
            "active_sessions": len(interactive_visualization_service.active_sessions),
            "supported_types": [vt.value for vt in VisualizationType]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Service unhealthy: {str(e)}"
        )