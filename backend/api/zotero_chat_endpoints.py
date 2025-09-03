"""
Zotero Chat Integration API Endpoints

Provides REST API endpoints for integrating Zotero references with chat functionality.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..core.database import get_db
from ..services.auth_service import get_current_user
from ..services.zotero.zotero_chat_integration_service import zotero_chat_service
from ..models.schemas import User


router = APIRouter(prefix="/api/zotero/chat", tags=["zotero-chat"])


# Request/Response Models
class ChatMessageRequest(BaseModel):
    content: str
    includeZoteroContext: Optional[bool] = False
    referenceIds: Optional[List[str]] = None
    contextType: Optional[str] = None  # 'research', 'citation', 'analysis'


class ChatMessageResponse(BaseModel):
    content: str
    enhancedContent: str
    references: List[Dict[str, Any]]


class ReferenceMentionsRequest(BaseModel):
    content: str


class ReferenceMentionsResponse(BaseModel):
    mentions: List[str]
    references: List[Dict[str, Any]]


class ResearchSummaryRequest(BaseModel):
    topic: str
    referenceIds: Optional[List[str]] = None


class ResearchSummaryResponse(BaseModel):
    summary: str
    references: List[Dict[str, Any]]


class ConversationExportRequest(BaseModel):
    messages: List[Dict[str, Any]]
    citationStyle: Optional[str] = 'apa'


class ConversationExportResponse(BaseModel):
    exportContent: str
    format: str = 'markdown'


class RelevantReferencesRequest(BaseModel):
    topic: str
    limit: Optional[int] = 5


class RelevantReferencesResponse(BaseModel):
    references: List[Dict[str, Any]]


@router.post("/process-message", response_model=ChatMessageResponse)
async def process_chat_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process a chat message to inject Zotero reference context.
    
    This endpoint:
    - Extracts reference mentions from the message
    - Finds matching Zotero items
    - Injects reference context for AI processing
    """
    try:
        options = {
            'includeZoteroContext': request.includeZoteroContext,
            'referenceIds': request.referenceIds,
            'contextType': request.contextType
        }
        
        enhanced_content, references = await zotero_chat_service.inject_reference_context(
            content=request.content,
            user_id=str(current_user.id),
            db=db,
            options=options
        )
        
        return ChatMessageResponse(
            content=request.content,
            enhancedContent=enhanced_content,
            references=references
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat message: {str(e)}"
        )


@router.post("/extract-mentions", response_model=ReferenceMentionsResponse)
async def extract_reference_mentions(
    request: ReferenceMentionsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extract reference mentions from chat content and find matching items.
    
    Supports formats like @[Title] or @[Author, Year]
    """
    try:
        mentions = zotero_chat_service.extract_reference_mentions(request.content)
        
        references = []
        if mentions:
            referenced_items = await zotero_chat_service.find_referenced_items(
                mentions=mentions,
                user_id=str(current_user.id),
                db=db
            )
            references = zotero_chat_service.convert_to_chat_references(referenced_items)
        
        return ReferenceMentionsResponse(
            mentions=mentions,
            references=references
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract mentions: {str(e)}"
        )


@router.post("/relevant-references", response_model=RelevantReferencesResponse)
async def get_relevant_references(
    request: RelevantReferencesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get relevant references for a chat topic.
    
    Searches the user's Zotero library for papers related to the topic.
    """
    try:
        references = await zotero_chat_service.get_relevant_references(
            topic=request.topic,
            user_id=str(current_user.id),
            db=db,
            limit=request.limit or 5
        )
        
        return RelevantReferencesResponse(references=references)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get relevant references: {str(e)}"
        )


@router.post("/research-summary", response_model=ResearchSummaryResponse)
async def create_research_summary(
    request: ResearchSummaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a research summary with references.
    
    Generates a summary based on either specific reference IDs or 
    by searching for relevant papers on the topic.
    """
    try:
        result = await zotero_chat_service.create_research_summary(
            topic=request.topic,
            user_id=str(current_user.id),
            db=db,
            reference_ids=request.referenceIds
        )
        
        return ResearchSummaryResponse(
            summary=result['summary'],
            references=result['references']
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create research summary: {str(e)}"
        )


@router.post("/export-conversation", response_model=ConversationExportResponse)
async def export_conversation_with_citations(
    request: ConversationExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export conversation with proper citations.
    
    Exports the conversation in markdown format with a bibliography
    of all referenced papers.
    """
    try:
        export_content = await zotero_chat_service.export_conversation_with_citations(
            messages=request.messages,
            user_id=str(current_user.id),
            db=db,
            citation_style=request.citationStyle or 'apa'
        )
        
        return ConversationExportResponse(
            exportContent=export_content,
            format='markdown'
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export conversation: {str(e)}"
        )


@router.post("/process-ai-response")
async def process_ai_response(
    response: str,
    references: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user)
):
    """
    Process AI response to add reference links.
    
    Finds mentions of references in the AI response and converts them
    to clickable links.
    """
    try:
        processed_response = zotero_chat_service.process_ai_response(
            response=response,
            available_references=references
        )
        
        return {"processedResponse": processed_response}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process AI response: {str(e)}"
        )


@router.post("/generate-citations")
async def generate_citations_for_references(
    references: List[Dict[str, Any]],
    style: str = 'apa',
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate citations for referenced items.
    
    Creates properly formatted citations for the given references
    in the specified style.
    """
    try:
        citations = await zotero_chat_service.generate_citations_for_references(
            references=references,
            style=style,
            user_id=str(current_user.id),
            db=db
        )
        
        return {"citations": citations}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate citations: {str(e)}"
        )


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for chat integration service"""
    return {"status": "healthy", "service": "zotero-chat-integration"}