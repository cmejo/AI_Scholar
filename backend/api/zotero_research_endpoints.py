"""
Zotero Research Integration API Endpoints

Provides REST API endpoints for integrating Zotero references with research and note-taking features.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..core.database import get_db
from ..services.auth_service import get_current_user
from ..services.zotero.zotero_research_integration_service import zotero_research_service
from ..models.schemas import User


router = APIRouter(prefix="/api/zotero/research", tags=["zotero-research"])


# Request/Response Models
class ProcessNoteRequest(BaseModel):
    content: str


class ProcessNoteResponse(BaseModel):
    processedContent: str
    references: List[Dict[str, Any]]
    originalLinks: Dict[str, List[str]]


class ResearchSummaryRequest(BaseModel):
    topic: str
    referenceIds: Optional[List[str]] = None
    noteIds: Optional[List[str]] = None


class ResearchSummaryResponse(BaseModel):
    id: str
    topic: str
    summary: str
    keyFindings: List[str]
    references: List[Dict[str, Any]]
    gaps: List[str]
    recommendations: List[str]
    createdAt: str


class ResearchContextRequest(BaseModel):
    topic: str


class ResearchContextResponse(BaseModel):
    topic: str
    relevantReferences: List[Dict[str, Any]]
    relatedNotes: List[Dict[str, Any]]
    suggestedQuestions: List[str]
    researchGaps: List[str]


class ResearchAssistanceRequest(BaseModel):
    question: str
    referenceIds: Optional[List[str]] = None


class ResearchAssistanceResponse(BaseModel):
    prompt: str
    question: str
    referenceCount: int


class SuggestReferencesRequest(BaseModel):
    noteContent: str
    existingReferenceIds: Optional[List[str]] = None


class SuggestReferencesResponse(BaseModel):
    suggestions: List[Dict[str, Any]]
    keyTerms: List[str]


class ExportProjectRequest(BaseModel):
    title: str
    description: str
    status: str = "active"
    references: List[Dict[str, Any]] = []
    notes: List[Dict[str, Any]] = []
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class ExportProjectResponse(BaseModel):
    exportContent: str
    format: str = "markdown"


@router.post("/process-note", response_model=ProcessNoteResponse)
async def process_note_content(
    request: ProcessNoteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process note content to resolve reference links.
    
    Supports formats like [[ref:item-id]] or @[Title] and converts them
    to formatted references with proper linking.
    """
    try:
        result = await zotero_research_service.process_note_content(
            content=request.content,
            user_id=str(current_user.id),
            db=db
        )
        
        return ProcessNoteResponse(
            processedContent=result['processedContent'],
            references=result['references'],
            originalLinks=result['originalLinks']
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process note content: {str(e)}"
        )


@router.post("/create-summary", response_model=ResearchSummaryResponse)
async def create_research_summary(
    request: ResearchSummaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a research summary from references and notes.
    
    Generates a comprehensive summary including key findings, research gaps,
    and recommendations based on the user's Zotero library.
    """
    try:
        result = await zotero_research_service.create_research_summary(
            topic=request.topic,
            user_id=str(current_user.id),
            db=db,
            reference_ids=request.referenceIds,
            note_ids=request.noteIds
        )
        
        return ResearchSummaryResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create research summary: {str(e)}"
        )


@router.post("/research-context", response_model=ResearchContextResponse)
async def get_research_context(
    request: ResearchContextRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get research context for AI assistance.
    
    Provides relevant references, suggested questions, and research gaps
    for a given topic to enhance AI research assistance.
    """
    try:
        result = await zotero_research_service.get_research_context(
            topic=request.topic,
            user_id=str(current_user.id),
            db=db
        )
        
        return ResearchContextResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get research context: {str(e)}"
        )


@router.post("/assistance-prompt", response_model=ResearchAssistanceResponse)
async def create_research_assistance_prompt(
    request: ResearchAssistanceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a research assistance prompt with reference context.
    
    Generates a comprehensive prompt that includes relevant reference
    information to provide better AI research assistance.
    """
    try:
        prompt = await zotero_research_service.create_research_assistance_prompt(
            question=request.question,
            user_id=str(current_user.id),
            db=db,
            reference_ids=request.referenceIds
        )
        
        reference_count = len(request.referenceIds) if request.referenceIds else 0
        
        return ResearchAssistanceResponse(
            prompt=prompt,
            question=request.question,
            referenceCount=reference_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create assistance prompt: {str(e)}"
        )


@router.post("/suggest-references", response_model=SuggestReferencesResponse)
async def suggest_related_references(
    request: SuggestReferencesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Suggest related references for a note.
    
    Analyzes note content and suggests relevant references from the
    user's Zotero library based on content similarity.
    """
    try:
        suggestions = await zotero_research_service.suggest_related_references(
            note_content=request.noteContent,
            user_id=str(current_user.id),
            db=db,
            existing_reference_ids=request.existingReferenceIds
        )
        
        # Extract key terms for transparency
        key_terms = zotero_research_service._extract_key_terms(request.noteContent)
        
        return SuggestReferencesResponse(
            suggestions=suggestions,
            keyTerms=key_terms[:5]  # Return top 5 terms
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest references: {str(e)}"
        )


@router.post("/export-project", response_model=ExportProjectResponse)
async def export_research_project(
    request: ExportProjectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export research project with references and notes.
    
    Creates a comprehensive markdown export of a research project
    including all references, notes, and metadata.
    """
    try:
        project_data = request.dict()
        
        export_content = await zotero_research_service.export_research_project(
            project_data=project_data,
            user_id=str(current_user.id),
            db=db
        )
        
        return ExportProjectResponse(
            exportContent=export_content,
            format="markdown"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export project: {str(e)}"
        )


@router.get("/extract-links")
async def extract_reference_links(
    content: str,
    current_user: User = Depends(get_current_user)
):
    """
    Extract reference links from content.
    
    Utility endpoint to extract reference links and mentions from text
    without processing them.
    """
    try:
        links = zotero_research_service.extract_reference_links(content)
        
        return {
            "itemIds": links['itemIds'],
            "mentions": links['mentions'],
            "totalLinks": len(links['itemIds']) + len(links['mentions'])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract links: {str(e)}"
        )


@router.get("/key-terms")
async def extract_key_terms(
    content: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """
    Extract key terms from content.
    
    Utility endpoint to extract key terms from text content for
    reference suggestion and content analysis.
    """
    try:
        key_terms = zotero_research_service._extract_key_terms(content)
        
        return {
            "keyTerms": key_terms[:limit],
            "totalTerms": len(key_terms)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract key terms: {str(e)}"
        )


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for research integration service"""
    return {"status": "healthy", "service": "zotero-research-integration"}