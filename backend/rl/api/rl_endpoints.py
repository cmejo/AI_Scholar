"""
FastAPI endpoints for the RL system.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging

from ..agent.rl_agent_controller import RLAgentController
from ..agent.conversation_manager import ConversationManager
from ..core.config import get_rl_config

logger = logging.getLogger(__name__)

# Global instances (would be properly initialized in main app)
rl_config = get_rl_config()
rl_agent = RLAgentController(rl_config)
conversation_manager = ConversationManager(rl_config, rl_agent)

rl_router = APIRouter(prefix="/rl", tags=["reinforcement_learning"])


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: Optional[str] = None
    domain_context: Optional[str] = ""
    metadata: Optional[Dict[str, Any]] = {}


class ChatResponse(BaseModel):
    response: str
    session_id: str
    confidence: float
    processing_time: float
    personalization_applied: bool
    safety_score: float
    metadata: Dict[str, Any]


class FeedbackRequest(BaseModel):
    session_id: str
    rating: Optional[float] = None
    text_feedback: Optional[str] = None
    engagement_data: Optional[Dict[str, Any]] = {}


class SessionInfo(BaseModel):
    session_id: str
    user_id: str
    status: str
    created_at: str
    total_turns: int
    metadata: Dict[str, Any]


@rl_router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint using RL system."""
    
    try:
        # Start or get existing session
        if request.session_id:
            session_info = await conversation_manager.get_session_info(request.session_id)
            if not session_info:
                raise HTTPException(status_code=404, detail="Session not found")
            session_id = request.session_id
        else:
            # Start new session
            session = await conversation_manager.start_conversation(
                user_id=request.user_id,
                domain_context=request.domain_context,
                session_metadata=request.metadata
            )
            session_id = session.session_id
        
        # Generate response
        rl_response = await conversation_manager.generate_response(
            session_id=session_id,
            user_input=request.message
        )
        
        return ChatResponse(
            response=rl_response.response_text,
            session_id=session_id,
            confidence=rl_response.confidence,
            processing_time=rl_response.processing_time,
            personalization_applied=rl_response.personalization_applied,
            safety_score=rl_response.safety_score,
            metadata=rl_response.metadata
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rl_router.post("/feedback")
async def feedback_endpoint(request: FeedbackRequest, background_tasks: BackgroundTasks):
    """Submit feedback for a conversation."""
    
    try:
        # Process feedback in background
        background_tasks.add_task(
            conversation_manager.process_feedback,
            request.session_id,
            {
                "rating": request.rating,
                "text": request.text_feedback,
                **request.engagement_data
            }
        )
        
        return {"status": "feedback_received", "session_id": request.session_id}
        
    except Exception as e:
        logger.error(f"Feedback endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rl_router.get("/session/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """Get information about a conversation session."""
    
    try:
        session_info = await conversation_manager.get_session_info(session_id)
        
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionInfo(**session_info)
        
    except Exception as e:
        logger.error(f"Session info endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rl_router.delete("/session/{session_id}")
async def end_session(session_id: str):
    """End a conversation session."""
    
    try:
        success = await conversation_manager.end_conversation(session_id, "user_ended")
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"status": "session_ended", "session_id": session_id}
        
    except Exception as e:
        logger.error(f"End session endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rl_router.get("/status")
async def get_rl_status():
    """Get RL system status and statistics."""
    
    try:
        agent_status = rl_agent.get_agent_status()
        session_stats = conversation_manager.get_session_statistics()
        
        return {
            "rl_agent": agent_status,
            "conversation_manager": session_stats,
            "system_health": "operational" if agent_status["state"] == "ready" else "degraded"
        }
        
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@rl_router.get("/analytics")
async def get_rl_analytics():
    """Get RL system analytics and insights."""
    
    try:
        # This would integrate with the analytics dashboard
        return {
            "message": "Analytics endpoint - would return comprehensive RL metrics",
            "placeholder": True
        }
        
    except Exception as e:
        logger.error(f"Analytics endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Initialize RL system on startup
@rl_router.on_event("startup")
async def startup_rl_system():
    """Initialize RL system components."""
    try:
        await rl_agent.initialize()
        await conversation_manager.initialize()
        logger.info("RL system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RL system: {e}")


@rl_router.on_event("shutdown")
async def shutdown_rl_system():
    """Shutdown RL system components."""
    try:
        await conversation_manager.shutdown()
        await rl_agent.shutdown()
        logger.info("RL system shutdown completed")
    except Exception as e:
        logger.error(f"Error during RL system shutdown: {e}")