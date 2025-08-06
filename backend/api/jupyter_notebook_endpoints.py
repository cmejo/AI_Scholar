"""
Jupyter Notebook API Endpoints for AI Scholar Advanced RAG System

This module provides REST API endpoints for Jupyter notebook management,
execution, and collaboration features.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..services.jupyter_notebook_service import jupyter_service, NotebookData, ExecutionResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jupyter", tags=["jupyter-notebooks"])

# Pydantic models for API requests/responses

class CreateNotebookRequest(BaseModel):
    title: str = Field(..., description="Notebook title")
    kernel_name: str = Field(default="python3", description="Kernel name")
    initial_cells: Optional[List[Dict[str, Any]]] = Field(default=None, description="Initial cells")

class UpdateCellRequest(BaseModel):
    source: str = Field(..., description="Cell source code")

class AddCellRequest(BaseModel):
    cell_type: str = Field(..., description="Cell type (code, markdown, raw)")
    source: str = Field(..., description="Cell source content")
    position: Optional[int] = Field(default=None, description="Position to insert cell")

class ExecuteCellResponse(BaseModel):
    success: bool
    outputs: List[Dict[str, Any]]
    execution_count: int
    execution_time: float
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None

class NotebookSummary(BaseModel):
    notebook_id: str
    title: str
    created_at: str
    modified_at: str
    owner_id: str
    is_owner: bool
    cell_count: int
    version: int

class CollaboratorRequest(BaseModel):
    collaborator_id: str = Field(..., description="User ID of collaborator")

class ExportRequest(BaseModel):
    format: str = Field(default="ipynb", description="Export format (ipynb, json)")

class ImportRequest(BaseModel):
    notebook_data: str = Field(..., description="Notebook data to import")
    format: str = Field(default="ipynb", description="Import format (ipynb)")

# Dependency for user authentication (simplified)
async def get_current_user() -> str:
    """Get current user ID - simplified implementation"""
    # In production, this would validate JWT tokens and return user info
    return "user_123"

@router.post("/notebooks", response_model=Dict[str, str])
async def create_notebook(
    request: CreateNotebookRequest,
    current_user: str = Depends(get_current_user)
):
    """Create a new Jupyter notebook"""
    try:
        notebook = await jupyter_service.create_notebook(
            title=request.title,
            owner_id=current_user,
            kernel_name=request.kernel_name,
            initial_cells=request.initial_cells
        )
        
        return {
            "notebook_id": notebook.notebook_id,
            "message": "Notebook created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating notebook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notebook: {str(e)}"
        )

@router.get("/notebooks", response_model=List[NotebookSummary])
async def list_notebooks(current_user: str = Depends(get_current_user)):
    """List all notebooks accessible to the current user"""
    try:
        notebooks = await jupyter_service.list_user_notebooks(current_user)
        return [NotebookSummary(**nb) for nb in notebooks]
        
    except Exception as e:
        logger.error(f"Error listing notebooks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list notebooks: {str(e)}"
        )

@router.get("/notebooks/{notebook_id}")
async def get_notebook(
    notebook_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get a specific notebook by ID"""
    try:
        notebook = await jupyter_service.get_notebook(notebook_id, current_user)
        
        if not notebook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found or access denied"
            )
        
        # Convert to dict for JSON response
        return {
            "notebook_id": notebook.notebook_id,
            "title": notebook.title,
            "cells": [
                {
                    "cell_id": cell.cell_id,
                    "cell_type": cell.cell_type,
                    "source": cell.source,
                    "outputs": cell.outputs,
                    "execution_count": cell.execution_count,
                    "metadata": cell.metadata,
                    "execution_state": cell.execution_state,
                    "execution_time": cell.execution_time
                }
                for cell in notebook.cells
            ],
            "metadata": notebook.metadata,
            "kernel_spec": notebook.kernel_spec,
            "created_at": notebook.created_at.isoformat(),
            "modified_at": notebook.modified_at.isoformat(),
            "owner_id": notebook.owner_id,
            "collaborators": notebook.collaborators,
            "version": notebook.version
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notebook {notebook_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notebook: {str(e)}"
        )

@router.put("/notebooks/{notebook_id}/cells/{cell_id}")
async def update_cell(
    notebook_id: str,
    cell_id: str,
    request: UpdateCellRequest,
    current_user: str = Depends(get_current_user)
):
    """Update a cell's content"""
    try:
        success = await jupyter_service.update_cell(
            notebook_id=notebook_id,
            cell_id=cell_id,
            source=request.source,
            user_id=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook or cell not found, or access denied"
            )
        
        return {"message": "Cell updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cell {cell_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update cell: {str(e)}"
        )

@router.post("/notebooks/{notebook_id}/cells")
async def add_cell(
    notebook_id: str,
    request: AddCellRequest,
    current_user: str = Depends(get_current_user)
):
    """Add a new cell to the notebook"""
    try:
        cell_id = await jupyter_service.add_cell(
            notebook_id=notebook_id,
            cell_type=request.cell_type,
            source=request.source,
            position=request.position,
            user_id=current_user
        )
        
        if not cell_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found or access denied"
            )
        
        return {
            "cell_id": cell_id,
            "message": "Cell added successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding cell to notebook {notebook_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add cell: {str(e)}"
        )

@router.delete("/notebooks/{notebook_id}/cells/{cell_id}")
async def delete_cell(
    notebook_id: str,
    cell_id: str,
    current_user: str = Depends(get_current_user)
):
    """Delete a cell from the notebook"""
    try:
        success = await jupyter_service.delete_cell(
            notebook_id=notebook_id,
            cell_id=cell_id,
            user_id=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook or cell not found, or access denied"
            )
        
        return {"message": "Cell deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cell {cell_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete cell: {str(e)}"
        )

@router.post("/notebooks/{notebook_id}/cells/{cell_id}/execute", response_model=ExecuteCellResponse)
async def execute_cell(
    notebook_id: str,
    cell_id: str,
    current_user: str = Depends(get_current_user)
):
    """Execute a specific cell"""
    try:
        result = await jupyter_service.execute_cell(
            notebook_id=notebook_id,
            cell_id=cell_id,
            user_id=current_user
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook or cell not found, or access denied"
            )
        
        return ExecuteCellResponse(
            success=result.success,
            outputs=result.outputs,
            execution_count=result.execution_count,
            execution_time=result.execution_time,
            error_message=result.error_message,
            warnings=result.warnings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing cell {cell_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute cell: {str(e)}"
        )

@router.post("/notebooks/{notebook_id}/execute-all")
async def execute_all_cells(
    notebook_id: str,
    current_user: str = Depends(get_current_user)
):
    """Execute all cells in the notebook"""
    try:
        results = await jupyter_service.execute_all_cells(notebook_id, current_user)
        
        return {
            "message": f"Executed {len(results)} cells",
            "results": [
                {
                    "success": result.success,
                    "execution_count": result.execution_count,
                    "execution_time": result.execution_time,
                    "error_message": result.error_message
                }
                for result in results
            ]
        }
        
    except Exception as e:
        logger.error(f"Error executing all cells in notebook {notebook_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute cells: {str(e)}"
        )

@router.post("/notebooks/{notebook_id}/collaborators")
async def add_collaborator(
    notebook_id: str,
    request: CollaboratorRequest,
    current_user: str = Depends(get_current_user)
):
    """Add a collaborator to the notebook"""
    try:
        success = await jupyter_service.add_collaborator(
            notebook_id=notebook_id,
            collaborator_id=request.collaborator_id,
            owner_id=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found or you don't have permission to add collaborators"
            )
        
        return {"message": "Collaborator added successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding collaborator to notebook {notebook_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add collaborator: {str(e)}"
        )

@router.delete("/notebooks/{notebook_id}/collaborators/{collaborator_id}")
async def remove_collaborator(
    notebook_id: str,
    collaborator_id: str,
    current_user: str = Depends(get_current_user)
):
    """Remove a collaborator from the notebook"""
    try:
        success = await jupyter_service.remove_collaborator(
            notebook_id=notebook_id,
            collaborator_id=collaborator_id,
            owner_id=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found or you don't have permission to remove collaborators"
            )
        
        return {"message": "Collaborator removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing collaborator from notebook {notebook_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove collaborator: {str(e)}"
        )

@router.post("/notebooks/{notebook_id}/export")
async def export_notebook(
    notebook_id: str,
    request: ExportRequest,
    current_user: str = Depends(get_current_user)
):
    """Export notebook in specified format"""
    try:
        exported_data = await jupyter_service.export_notebook(
            notebook_id=notebook_id,
            user_id=current_user,
            format=request.format
        )
        
        if not exported_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found or access denied"
            )
        
        return {
            "format": request.format,
            "data": exported_data,
            "message": "Notebook exported successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting notebook {notebook_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export notebook: {str(e)}"
        )

@router.post("/notebooks/import")
async def import_notebook(
    request: ImportRequest,
    current_user: str = Depends(get_current_user)
):
    """Import notebook from external format"""
    try:
        notebook_id = await jupyter_service.import_notebook(
            notebook_data=request.notebook_data,
            owner_id=current_user,
            format=request.format
        )
        
        if not notebook_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to import notebook - invalid format or data"
            )
        
        return {
            "notebook_id": notebook_id,
            "message": "Notebook imported successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing notebook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import notebook: {str(e)}"
        )

@router.get("/kernels")
async def list_available_kernels():
    """List available notebook kernels"""
    try:
        return {
            "kernels": jupyter_service.supported_kernels,
            "message": "Available kernels retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error listing kernels: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list kernels: {str(e)}"
        )

@router.get("/notebooks/{notebook_id}/kernel/status")
async def get_kernel_status(
    notebook_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get kernel status for a notebook"""
    try:
        status_info = await jupyter_service.get_kernel_status(notebook_id, current_user)
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found or access denied"
            )
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting kernel status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get kernel status: {str(e)}"
        )

@router.post("/notebooks/{notebook_id}/kernel/restart")
async def restart_kernel(
    notebook_id: str,
    current_user: str = Depends(get_current_user)
):
    """Restart the kernel for a notebook"""
    try:
        success = await jupyter_service.restart_kernel(notebook_id, current_user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found or failed to restart kernel"
            )
        
        return {"message": "Kernel restarted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting kernel: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart kernel: {str(e)}"
        )

@router.post("/notebooks/{notebook_id}/kernel/interrupt")
async def interrupt_kernel(
    notebook_id: str,
    current_user: str = Depends(get_current_user)
):
    """Interrupt kernel execution"""
    try:
        success = await jupyter_service.interrupt_kernel(notebook_id, current_user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found or failed to interrupt kernel"
            )
        
        return {"message": "Kernel interrupted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error interrupting kernel: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to interrupt kernel: {str(e)}"
        )

@router.get("/notebooks/{notebook_id}/variables")
async def get_notebook_variables(
    notebook_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get variables defined in the notebook kernel"""
    try:
        variables = await jupyter_service.get_notebook_variables(notebook_id, current_user)
        return variables
        
    except Exception as e:
        logger.error(f"Error getting notebook variables: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notebook variables: {str(e)}"
        )

@router.post("/notebooks/{notebook_id}/clear-output")
async def clear_notebook_output(
    notebook_id: str,
    current_user: str = Depends(get_current_user)
):
    """Clear all cell outputs in the notebook"""
    try:
        success = await jupyter_service.clear_notebook_output(notebook_id, current_user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found or access denied"
            )
        
        return {"message": "Notebook output cleared successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing notebook output: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear notebook output: {str(e)}"
        )

@router.post("/notebooks/{notebook_id}/duplicate")
async def duplicate_notebook(
    notebook_id: str,
    new_title: Optional[str] = None,
    current_user: str = Depends(get_current_user)
):
    """Create a duplicate of an existing notebook"""
    try:
        new_notebook_id = await jupyter_service.duplicate_notebook(
            notebook_id, current_user, new_title
        )
        
        if not new_notebook_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found or access denied"
            )
        
        return {
            "notebook_id": new_notebook_id,
            "message": "Notebook duplicated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error duplicating notebook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to duplicate notebook: {str(e)}"
        )

@router.get("/notebooks/{notebook_id}/statistics")
async def get_notebook_statistics(
    notebook_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get statistics about the notebook"""
    try:
        stats = await jupyter_service.get_notebook_statistics(notebook_id, current_user)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found or access denied"
            )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notebook statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notebook statistics: {str(e)}"
        )

@router.get("/notebooks/{notebook_id}/widgets")
async def get_notebook_widgets(
    notebook_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get all widgets for a notebook"""
    try:
        widgets = await jupyter_service.get_notebook_widgets(notebook_id, current_user)
        
        return {
            "widgets": [
                {
                    "widget_id": widget.widget_id,
                    "widget_type": widget.widget_type,
                    "properties": widget.properties,
                    "value": widget.value,
                    "cell_id": widget.cell_id,
                    "created_at": widget.created_at.isoformat(),
                    "last_updated": widget.last_updated.isoformat()
                }
                for widget in widgets
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting notebook widgets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notebook widgets: {str(e)}"
        )

@router.put("/widgets/{widget_id}")
async def update_widget_value(
    widget_id: str,
    new_value: Any,
    current_user: str = Depends(get_current_user)
):
    """Update widget value"""
    try:
        success = await jupyter_service.update_widget_value(
            widget_id, new_value, current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Widget not found or access denied"
            )
        
        return {"message": "Widget value updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating widget value: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update widget value: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint for Jupyter service"""
    try:
        return {
            "status": "healthy",
            "service": "jupyter-notebook",
            "notebooks_count": len(jupyter_service.notebooks),
            "kernels_count": len(jupyter_service.kernels),
            "widgets_count": len(jupyter_service.widgets),
            "supported_kernels": list(jupyter_service.supported_kernels.keys())
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Service unhealthy: {str(e)}"
        )