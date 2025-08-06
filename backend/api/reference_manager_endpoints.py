"""
Reference Manager API Endpoints

Provides REST API endpoints for reference manager integrations:
- OAuth authentication flows
- Library synchronization
- Item management
- Export/import functionality
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import tempfile
import os
import logging

from ..services.reference_manager_service import (
    ReferenceManagerService, 
    ReferenceManagerType, 
    BibliographicData, 
    AuthCredentials,
    SyncResult
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reference-managers", tags=["reference-managers"])

# Pydantic models for API
class AuthUrlRequest(BaseModel):
    manager_type: str
    client_id: str
    redirect_uri: str

class TokenExchangeRequest(BaseModel):
    manager_type: str
    code: str
    client_id: str
    client_secret: str
    redirect_uri: str

class SyncRequest(BaseModel):
    manager_type: str
    credentials: Optional[Dict[str, Any]] = None
    limit: int = 100

class AddItemRequest(BaseModel):
    manager_type: str
    item: Dict[str, Any]
    credentials: Optional[Dict[str, Any]] = None

class ExportRequest(BaseModel):
    items: List[Dict[str, Any]]
    format_type: str = "ris"

class BibliographicDataResponse(BaseModel):
    title: str
    authors: List[str]
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = []
    url: Optional[str] = None
    pages: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    item_type: str = "article"
    tags: List[str] = []
    notes: Optional[str] = None
    date_added: Optional[datetime] = None
    date_modified: Optional[datetime] = None

class SyncResultResponse(BaseModel):
    success: bool
    items_synced: int
    errors: List[str]
    last_sync: datetime
    total_items: int

# Initialize service
reference_manager_service = ReferenceManagerService()

@router.get("/supported")
async def get_supported_managers():
    """Get list of supported reference managers"""
    try:
        managers = reference_manager_service.get_supported_managers()
        return {
            "success": True,
            "managers": managers,
            "descriptions": {
                "zotero": "Zotero - Free reference manager with web API",
                "mendeley": "Mendeley - Academic reference manager with social features",
                "endnote": "EndNote - Professional reference manager (file-based integration)"
            }
        }
    except Exception as e:
        logger.error(f"Error getting supported managers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auth/url")
async def get_authorization_url(request: AuthUrlRequest):
    """Get OAuth authorization URL for reference manager"""
    try:
        manager_type = ReferenceManagerType(request.manager_type)
        
        if manager_type == ReferenceManagerType.ENDNOTE:
            raise HTTPException(
                status_code=400, 
                detail="EndNote does not support OAuth authentication. Use file upload instead."
            )
        
        auth_url = await reference_manager_service.get_authorization_url(
            manager_type, request.client_id, request.redirect_uri
        )
        
        return {
            "success": True,
            "authorization_url": auth_url,
            "manager_type": request.manager_type
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting authorization URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auth/token")
async def exchange_code_for_token(request: TokenExchangeRequest):
    """Exchange authorization code for access token"""
    try:
        manager_type = ReferenceManagerType(request.manager_type)
        
        credentials = await reference_manager_service.exchange_code_for_token(
            manager_type, request.code, request.client_id, 
            request.client_secret, request.redirect_uri
        )
        
        return {
            "success": True,
            "credentials": {
                "access_token": credentials.access_token,
                "refresh_token": credentials.refresh_token,
                "token_type": credentials.token_type,
                "expires_in": credentials.expires_in,
                "user_id": credentials.user_id
            },
            "manager_type": request.manager_type
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error exchanging token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync", response_model=SyncResultResponse)
async def sync_library(request: SyncRequest):
    """Synchronize library from reference manager"""
    try:
        manager_type = ReferenceManagerType(request.manager_type)
        
        credentials = None
        if request.credentials:
            credentials = AuthCredentials(**request.credentials)
        
        sync_result = await reference_manager_service.sync_library(
            manager_type, credentials, limit=request.limit
        )
        
        return sync_result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error syncing library: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/file")
async def sync_from_file(
    manager_type: str = Form(...),
    file: UploadFile = File(...)
):
    """Synchronize library from uploaded file (EndNote)"""
    try:
        if manager_type != "endnote":
            raise HTTPException(
                status_code=400, 
                detail="File upload only supported for EndNote"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            sync_result = await reference_manager_service.sync_library(
                ReferenceManagerType.ENDNOTE, file_path=temp_file_path
            )
            
            return sync_result
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"Error syncing from file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/items/add")
async def add_item(request: AddItemRequest):
    """Add item to reference manager"""
    try:
        manager_type = ReferenceManagerType(request.manager_type)
        
        # Convert dict to BibliographicData
        item_data = request.item
        item = BibliographicData(
            title=item_data.get('title', ''),
            authors=item_data.get('authors', []),
            journal=item_data.get('journal'),
            year=item_data.get('year'),
            doi=item_data.get('doi'),
            abstract=item_data.get('abstract'),
            keywords=item_data.get('keywords', []),
            url=item_data.get('url'),
            pages=item_data.get('pages'),
            volume=item_data.get('volume'),
            issue=item_data.get('issue'),
            publisher=item_data.get('publisher'),
            isbn=item_data.get('isbn'),
            item_type=item_data.get('item_type', 'article'),
            tags=item_data.get('tags', []),
            notes=item_data.get('notes')
        )
        
        credentials = None
        if request.credentials:
            credentials = AuthCredentials(**request.credentials)
        
        success = await reference_manager_service.add_item(
            manager_type, item, credentials
        )
        
        return {
            "success": success,
            "message": "Item added successfully" if success else "Failed to add item"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_library(request: ExportRequest):
    """Export library to file"""
    try:
        # Convert dict items to BibliographicData
        items = []
        for item_data in request.items:
            item = BibliographicData(
                title=item_data.get('title', ''),
                authors=item_data.get('authors', []),
                journal=item_data.get('journal'),
                year=item_data.get('year'),
                doi=item_data.get('doi'),
                abstract=item_data.get('abstract'),
                keywords=item_data.get('keywords', []),
                url=item_data.get('url'),
                pages=item_data.get('pages'),
                volume=item_data.get('volume'),
                issue=item_data.get('issue'),
                publisher=item_data.get('publisher'),
                isbn=item_data.get('isbn'),
                item_type=item_data.get('item_type', 'article'),
                tags=item_data.get('tags', []),
                notes=item_data.get('notes')
            )
            items.append(item)
        
        # Create temporary file for export
        file_extension = '.ris' if request.format_type == 'ris' else '.enw'
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file_path = temp_file.name
        
        success = await reference_manager_service.export_library(
            items, temp_file_path, request.format_type
        )
        
        if success:
            return FileResponse(
                temp_file_path,
                media_type='application/octet-stream',
                filename=f"library_export{file_extension}"
            )
        else:
            raise HTTPException(status_code=500, detail="Export failed")
        
    except Exception as e:
        logger.error(f"Error exporting library: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "reference_manager",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/stats")
async def get_integration_stats():
    """Get integration statistics"""
    try:
        return {
            "supported_managers": reference_manager_service.get_supported_managers(),
            "total_managers": len(reference_manager_service.get_supported_managers()),
            "oauth_supported": ["zotero", "mendeley"],
            "file_supported": ["endnote"],
            "export_formats": ["ris", "enw"]
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))