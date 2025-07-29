"""
AI Research Chat API Endpoints
Provides endpoints for conversational research assistance through an intelligent chat interface.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from core.auth import get_current_user
from models.schemas import User
from services.ai_research_chat import (
    AIResearchChatService, ChatMessage, ResearchAnswer, ChatSession,
    ChatMessageType, ResearchContext
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Request/Response Models
class StartChatRequest(BaseModel):
    context: ResearchContext = ResearchContext.GENERAL_RESEARCH
    title: Optional[str] = None

class AskQuestionRequest(BaseModel):
    session_id: str
    question: str
    context_override: Optional[ResearchContext] = None

class ChatMessageResponse(BaseModel):
    id: str
    message_type: str
    content: str
    context: Optional[str] = None
    timestamp: str
    confidence_score: Optional[float] = None
    sources: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ResearchAnswerResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[str]
    related_concepts: List[str]
    follow_up_questions: List[str]
    methodology_suggestions: List[str]
    context: str

class ChatSessionResponse(BaseModel):
    id: str
    title: str
    context: str
    created_at: str
    updated_at: str
    is_active: bool
    message_count: int
    messages: List[ChatMessageResponse]

# Endpoints

@router.post("/start", response_model=ChatSessionResponse)
async def start_chat_session(
    request: StartChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new AI research chat session"""
    try:
        chat_service = AIResearchChatService(db)
        
        session = await chat_service.start_chat_session(
            user_id=current_user.id,
            context=request.context,
            title=request.title
        )
        
        # Convert messages to response format
        messages = []
        for msg in session.messages:
            messages.append(ChatMessageResponse(
                id=msg.id,
                message_type=msg.message_type.value,
                content=msg.content,
                context=msg.context.value if msg.context else None,
                timestamp=msg.timestamp.isoformat() if msg.timestamp else datetime.utcnow().isoformat(),
                confidence_score=msg.confidence_score,
                sources=msg.sources,
                suggestions=msg.suggestions,
                metadata=msg.metadata
            ))
        
        return ChatSessionResponse(
            id=session.id,
            title=session.title,
            context=session.context.value,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            is_active=session.is_active,
            message_count=len(session.messages),
            messages=messages
        )
        
    except Exception as e:
        logger.error(f"Error starting chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ask", response_model=ResearchAnswerResponse)
async def ask_research_question(
    request: AskQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ask a research question in a chat session"""
    try:
        chat_service = AIResearchChatService(db)
        
        answer = await chat_service.ask_research_question(
            session_id=request.session_id,
            question=request.question,
            context_override=request.context_override
        )
        
        return ResearchAnswerResponse(
            answer=answer.answer,
            confidence=answer.confidence,
            sources=answer.sources,
            related_concepts=answer.related_concepts,
            follow_up_questions=answer.follow_up_questions,
            methodology_suggestions=answer.methodology_suggestions,
            context=answer.context.value
        )
        
    except Exception as e:
        logger.error(f"Error asking research question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific chat session"""
    try:
        chat_service = AIResearchChatService(db)
        
        session = await chat_service.get_chat_history(
            user_id=current_user.id,
            session_id=session_id
        )
        
        if not isinstance(session, ChatSession):
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Convert messages to response format
        messages = []
        for msg in session.messages:
            messages.append(ChatMessageResponse(
                id=msg.id,
                message_type=msg.message_type.value,
                content=msg.content,
                context=msg.context.value if msg.context else None,
                timestamp=msg.timestamp.isoformat() if msg.timestamp else datetime.utcnow().isoformat(),
                confidence_score=msg.confidence_score,
                sources=msg.sources,
                suggestions=msg.suggestions,
                metadata=msg.metadata
            ))
        
        return ChatSessionResponse(
            id=session.id,
            title=session.title,
            context=session.context.value,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            is_active=session.is_active,
            message_count=len(session.messages),
            messages=messages
        )
        
    except Exception as e:
        logger.error(f"Error getting chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[ChatMessageResponse])
async def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200)
):
    """Get user's chat history across all sessions"""
    try:
        chat_service = AIResearchChatService(db)
        
        messages = await chat_service.get_chat_history(
            user_id=current_user.id,
            limit=limit
        )
        
        if not isinstance(messages, list):
            messages = []
        
        # Convert messages to response format
        response_messages = []
        for msg in messages:
            response_messages.append(ChatMessageResponse(
                id=msg.id,
                message_type=msg.message_type.value,
                content=msg.content,
                context=msg.context.value if msg.context else None,
                timestamp=msg.timestamp.isoformat() if msg.timestamp else datetime.utcnow().isoformat(),
                confidence_score=msg.confidence_score,
                sources=msg.sources,
                suggestions=msg.suggestions,
                metadata=msg.metadata
            ))
        
        return response_messages
        
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions", response_model=List[Dict[str, Any]])
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's active chat sessions"""
    try:
        chat_service = AIResearchChatService(db)
        
        # Get active sessions for user
        user_sessions = []
        for session_id, session in chat_service.active_sessions.items():
            if session.user_id == current_user.id:
                user_sessions.append({
                    "id": session.id,
                    "title": session.title,
                    "context": session.context.value,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "is_active": session.is_active,
                    "message_count": len(session.messages),
                    "last_message": session.messages[-1].content if session.messages else None
                })
        
        # Sort by updated_at descending
        user_sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        
        return user_sessions
        
    except Exception as e:
        logger.error(f"Error getting user sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/contexts", response_model=List[Dict[str, str]])
async def get_research_contexts():
    """Get available research contexts for chat"""
    try:
        contexts = []
        
        context_descriptions = {
            ResearchContext.LITERATURE_REVIEW: "Literature review assistance and paper analysis",
            ResearchContext.METHODOLOGY_DESIGN: "Research methodology selection and design guidance",
            ResearchContext.DATA_ANALYSIS: "Data analysis methods and statistical guidance",
            ResearchContext.HYPOTHESIS_TESTING: "Hypothesis formulation and testing approaches",
            ResearchContext.CONCEPT_EXPLORATION: "Concept explanations and theoretical frameworks",
            ResearchContext.GENERAL_RESEARCH: "General research assistance and guidance"
        }
        
        for context in ResearchContext:
            contexts.append({
                "value": context.value,
                "name": context.value.replace("_", " ").title(),
                "description": context_descriptions.get(context, "Research assistance")
            })
        
        return contexts
        
    except Exception as e:
        logger.error(f"Error getting research contexts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggest-questions", response_model=List[str])
async def suggest_questions(
    context: ResearchContext = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get suggested questions for a research context"""
    try:
        suggestions = {
            ResearchContext.LITERATURE_REVIEW: [
                "What are the key themes in the literature on [topic]?",
                "What research gaps exist in [field]?",
                "How has research on [topic] evolved over time?",
                "What are the most cited papers in [area]?",
                "What methodologies are commonly used in [field]?"
            ],
            ResearchContext.METHODOLOGY_DESIGN: [
                "What methodology should I use for [research question]?",
                "How do I design an experimental study?",
                "What's the difference between qualitative and quantitative approaches?",
                "How do I determine appropriate sample size?",
                "What are the ethical considerations for my study?"
            ],
            ResearchContext.DATA_ANALYSIS: [
                "What statistical test should I use for my data?",
                "How do I interpret regression results?",
                "What's the best way to visualize my findings?",
                "How do I handle missing data?",
                "What software should I use for analysis?"
            ],
            ResearchContext.HYPOTHESIS_TESTING: [
                "How do I formulate a testable hypothesis?",
                "What's the difference between null and alternative hypotheses?",
                "How do I test my hypothesis?",
                "What does statistical significance mean?",
                "How do I interpret p-values?"
            ],
            ResearchContext.CONCEPT_EXPLORATION: [
                "What is [concept] and how is it used in research?",
                "How does [theory] apply to my research area?",
                "What are the key principles of [framework]?",
                "How do I apply [concept] in practice?",
                "What are examples of [theory] in action?"
            ],
            ResearchContext.GENERAL_RESEARCH: [
                "How do I get started with research in [field]?",
                "What are the steps in the research process?",
                "How do I write a research proposal?",
                "What makes good research?",
                "How do I stay current with research in my field?"
            ]
        }
        
        return suggestions.get(context, suggestions[ResearchContext.GENERAL_RESEARCH])
        
    except Exception as e:
        logger.error(f"Error getting suggested questions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/session/{session_id}")
async def end_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End a chat session"""
    try:
        chat_service = AIResearchChatService(db)
        
        # Verify session belongs to user
        session = chat_service.active_sessions.get(session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Session not found")
        
        success = await chat_service.end_chat_session(session_id)
        
        if success:
            return {"message": "Chat session ended successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to end session")
        
    except Exception as e:
        logger.error(f"Error ending chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=Dict[str, Any])
async def get_chat_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's chat statistics"""
    try:
        from core.database import AnalyticsEvent
        from datetime import timedelta
        
        # Get chat events from last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        events = db.query(AnalyticsEvent).filter(
            AnalyticsEvent.user_id == current_user.id,
            AnalyticsEvent.event_type.like("chat_%"),
            AnalyticsEvent.created_at >= start_date
        ).all()
        
        # Calculate statistics
        stats = {
            "total_sessions": 0,
            "total_questions": 0,
            "average_session_length": 0,
            "most_used_context": "general_research",
            "contexts_used": {},
            "recent_activity": []
        }
        
        session_events = [e for e in events if e.event_type == "chat_session_started"]
        question_events = [e for e in events if e.event_type == "research_question_asked"]
        
        stats["total_sessions"] = len(session_events)
        stats["total_questions"] = len(question_events)
        
        # Context usage
        contexts = {}
        for event in session_events:
            context = event.event_data.get("context", "general_research")
            contexts[context] = contexts.get(context, 0) + 1
        
        stats["contexts_used"] = contexts
        if contexts:
            stats["most_used_context"] = max(contexts.items(), key=lambda x: x[1])[0]
        
        # Recent activity (last 7 days)
        recent_start = end_date - timedelta(days=7)
        recent_events = [e for e in events if e.created_at >= recent_start]
        
        daily_activity = {}
        for event in recent_events:
            date_key = event.created_at.date().isoformat()
            daily_activity[date_key] = daily_activity.get(date_key, 0) + 1
        
        stats["recent_activity"] = [
            {"date": date, "count": count}
            for date, count in sorted(daily_activity.items())
        ]
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting chat statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for chat service"""
    try:
        return {
            "status": "healthy",
            "service": "ai_research_chat",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "conversational_research_assistance",
                "context_aware_responses",
                "session_management",
                "research_question_classification"
            ]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Service unhealthy")