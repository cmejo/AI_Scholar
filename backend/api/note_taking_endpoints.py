"""
Note-Taking Integration API Endpoints

Provides REST API endpoints for note-taking app integrations:
- Obsidian vault synchronization
- Notion workspace integration
- Roam Research graph synchronization
- Bidirectional knowledge graph synchronization
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import tempfile
import os
import logging

from ..services.note_taking_integration_service import (
    NoteTakingIntegrationService,
    NoteTakingApp,
    Note,
    SyncConfig,
    SyncResult
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/note-taking", tags=["note-taking"])

# Pydantic models for API
class ObsidianIntegrationRequest(BaseModel):
    vault_path: str = Field(..., description="Path to Obsidian vault directory")

class NotionIntegrationRequest(BaseModel):
    api_token: str = Field(..., description="Notion API token")
    database_id: str = Field(..., description="Notion database ID")

class RoamIntegrationRequest(BaseModel):
    graph_name: str = Field(..., description="Roam Research graph name")
    api_token: str = Field(..., description="Roam Research API token")

class SyncConfigRequest(BaseModel):
    sync_direction: str = Field("bidirectional", description="Sync direction: bidirectional, import_only, export_only")
    auto_sync: bool = Field(False, description="Enable automatic synchronization")
    sync_interval_minutes: int = Field(30, description="Sync interval in minutes")
    preserve_formatting: bool = Field(True, description="Preserve original formatting")
    include_attachments: bool = Field(False, description="Include file attachments")

class NoteResponse(BaseModel):
    id: str
    title: str
    content: str
    tags: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    app_source: str
    app_id: Optional[str] = None
    parent_id: Optional[str] = None
    links: List[str] = []
    backlinks: List[str] = []
    metadata: Dict[str, Any] = {}

class SyncResultResponse(BaseModel):
    success: bool
    notes_synced: int
    notes_created: int
    notes_updated: int
    notes_deleted: int
    errors: List[str]
    last_sync: datetime

class IntegrationInfoResponse(BaseModel):
    id: str
    type: str
    config: Dict[str, Any]

# Initialize service
note_service = NoteTakingIntegrationService()

@router.get("/supported-apps")
async def get_supported_apps():
    """Get list of supported note-taking applications"""
    try:
        apps = note_service.get_supported_apps()
        return {
            "success": True,
            "apps": apps,
            "descriptions": {
                "obsidian": "Obsidian - Local markdown-based knowledge management",
                "notion": "Notion - Cloud-based workspace and database",
                "roam": "Roam Research - Networked thought and graph database"
            },
            "features": {
                "obsidian": ["file_system_access", "markdown_preservation", "wikilinks", "backlinks"],
                "notion": ["api_integration", "database_sync", "rich_content", "collaboration"],
                "roam": ["graph_structure", "block_references", "bidirectional_links", "daily_notes"]
            }
        }
    except Exception as e:
        logger.error(f"Error getting supported apps: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integrations/obsidian")
async def add_obsidian_integration(request: ObsidianIntegrationRequest):
    """Add Obsidian vault integration"""
    try:
        # Validate vault path exists
        if not os.path.exists(request.vault_path):
            raise HTTPException(
                status_code=400,
                detail=f"Vault path does not exist: {request.vault_path}"
            )
        
        if not os.path.isdir(request.vault_path):
            raise HTTPException(
                status_code=400,
                detail=f"Vault path is not a directory: {request.vault_path}"
            )
        
        integration_id = note_service.add_obsidian_integration(request.vault_path)
        
        return {
            "success": True,
            "integration_id": integration_id,
            "message": f"Obsidian vault integration added: {request.vault_path}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding Obsidian integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integrations/notion")
async def add_notion_integration(request: NotionIntegrationRequest):
    """Add Notion workspace integration"""
    try:
        integration_id = note_service.add_notion_integration(
            request.api_token, request.database_id
        )
        
        return {
            "success": True,
            "integration_id": integration_id,
            "message": f"Notion workspace integration added: {request.database_id}"
        }
        
    except Exception as e:
        logger.error(f"Error adding Notion integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integrations/roam")
async def add_roam_integration(request: RoamIntegrationRequest):
    """Add Roam Research graph integration"""
    try:
        integration_id = note_service.add_roam_integration(
            request.graph_name, request.api_token
        )
        
        return {
            "success": True,
            "integration_id": integration_id,
            "message": f"Roam Research graph integration added: {request.graph_name}"
        }
        
    except Exception as e:
        logger.error(f"Error adding Roam integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/integrations", response_model=List[IntegrationInfoResponse])
async def list_integrations():
    """List all configured integrations"""
    try:
        integrations = note_service.list_integrations()
        return integrations
        
    except Exception as e:
        logger.error(f"Error listing integrations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/integrations/{integration_id}")
async def get_integration_info(integration_id: str):
    """Get information about a specific integration"""
    try:
        info = note_service.get_integration_info(integration_id)
        
        if not info:
            raise HTTPException(
                status_code=404,
                detail=f"Integration not found: {integration_id}"
            )
        
        return {
            "success": True,
            "integration": info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting integration info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/integrations/{integration_id}")
async def remove_integration(integration_id: str):
    """Remove an integration"""
    try:
        success = note_service.remove_integration(integration_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Integration not found: {integration_id}"
            )
        
        return {
            "success": True,
            "message": f"Integration removed: {integration_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/{integration_id}", response_model=SyncResultResponse)
async def sync_integration(integration_id: str, config: SyncConfigRequest):
    """Synchronize a specific integration"""
    try:
        # Get integration info to determine app type
        info = note_service.get_integration_info(integration_id)
        if not info:
            raise HTTPException(
                status_code=404,
                detail=f"Integration not found: {integration_id}"
            )
        
        # Create sync config
        app_type = NoteTakingApp(info['type'])
        sync_config = SyncConfig(
            app_type=app_type,
            credentials=info['config'],
            sync_direction=config.sync_direction,
            auto_sync=config.auto_sync,
            sync_interval_minutes=config.sync_interval_minutes,
            preserve_formatting=config.preserve_formatting,
            include_attachments=config.include_attachments
        )
        
        # Perform synchronization
        result = await note_service.sync_integration(integration_id, sync_config)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/all")
async def sync_all_integrations(config: SyncConfigRequest):
    """Synchronize all configured integrations"""
    try:
        results = await note_service.sync_all_integrations()
        
        # Convert results to response format
        response_results = {}
        for integration_id, result in results.items():
            response_results[integration_id] = SyncResultResponse(
                success=result.success,
                notes_synced=result.notes_synced,
                notes_created=result.notes_created,
                notes_updated=result.notes_updated,
                notes_deleted=result.notes_deleted,
                errors=result.errors,
                last_sync=result.last_sync
            )
        
        return {
            "success": True,
            "results": response_results,
            "total_integrations": len(results),
            "successful_syncs": sum(1 for r in results.values() if r.success)
        }
        
    except Exception as e:
        logger.error(f"Error syncing all integrations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import/obsidian-vault")
async def import_obsidian_vault(
    vault_archive: UploadFile = File(..., description="Obsidian vault archive (.zip)")
):
    """Import Obsidian vault from uploaded archive"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            content = await vault_archive.read()
            temp_file.write(content)
            temp_archive_path = temp_file.name
        
        # Extract to temporary directory
        import zipfile
        temp_vault_dir = tempfile.mkdtemp(prefix='obsidian_vault_')
        
        try:
            with zipfile.ZipFile(temp_archive_path, 'r') as zip_ref:
                zip_ref.extractall(temp_vault_dir)
            
            # Add integration
            integration_id = note_service.add_obsidian_integration(temp_vault_dir)
            
            # Perform initial sync
            app_type = NoteTakingApp.OBSIDIAN
            sync_config = SyncConfig(
                app_type=app_type,
                credentials={'vault_path': temp_vault_dir},
                sync_direction="import_only"
            )
            
            result = await note_service.sync_integration(integration_id, sync_config)
            
            return {
                "success": True,
                "integration_id": integration_id,
                "sync_result": result,
                "message": f"Obsidian vault imported with {result.notes_synced} notes"
            }
            
        finally:
            # Clean up temporary files
            os.unlink(temp_archive_path)
            # Note: temp_vault_dir is kept for the integration to use
            
    except Exception as e:
        logger.error(f"Error importing Obsidian vault: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{integration_id}/knowledge-graph")
async def export_knowledge_graph(integration_id: str):
    """Export knowledge graph data from integration"""
    try:
        info = note_service.get_integration_info(integration_id)
        if not info:
            raise HTTPException(
                status_code=404,
                detail=f"Integration not found: {integration_id}"
            )
        
        # This would extract knowledge graph data
        # For now, return placeholder
        return {
            "success": True,
            "integration_id": integration_id,
            "knowledge_graph": {
                "nodes": [],
                "edges": [],
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "source_app": info['type']
                }
            },
            "message": "Knowledge graph export (placeholder implementation)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting knowledge graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "note_taking_integration",
        "timestamp": datetime.now().isoformat(),
        "supported_apps": note_service.get_supported_apps(),
        "active_integrations": len(note_service.list_integrations())
    }

@router.get("/stats")
async def get_integration_stats():
    """Get integration statistics"""
    try:
        integrations = note_service.list_integrations()
        
        # Count by app type
        app_counts = {}
        for integration in integrations:
            app_type = integration['type']
            app_counts[app_type] = app_counts.get(app_type, 0) + 1
        
        return {
            "total_integrations": len(integrations),
            "integrations_by_app": app_counts,
            "supported_apps": note_service.get_supported_apps(),
            "features": {
                "bidirectional_sync": True,
                "knowledge_graph_export": True,
                "markdown_preservation": True,
                "link_extraction": True,
                "backlink_detection": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))