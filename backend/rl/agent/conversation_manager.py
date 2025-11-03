"""
Conversation management and response generation pipeline.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid

from ..core.config import RLConfig
from ..models.conversation_models import ConversationState, ConversationTurn, Action
from ..models.user_models import UserProfile
from .rl_agent_controller import RLAgentController, RLResponse

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Status of a conversation session."""
    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    TERMINATED = "terminated"


@dataclass
class ConversationSession:
    """Represents an active conversation session."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    conversation_state: Optional[ConversationState] = None
    user_profile: Optional[UserProfile] = None
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    total_turns: int = 0
    session_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
        self.total_turns += 1
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session has expired."""
        timeout = timedelta(minutes=timeout_minutes)
        return datetime.now() - self.last_activity > timeout
    
    def get_session_duration(self) -> timedelta:
        """Get total session duration."""
        return self.last_activity - self.created_at


class ConversationManager:
    """Manages conversation sessions and response generation pipeline."""
    
    def __init__(self, config: RLConfig, rl_agent: RLAgentController):
        self.config = config
        self.rl_agent = rl_agent
        self.active_sessions: Dict[str, ConversationSession] = {}
        self.session_timeout_minutes = 30
        
        # Response generation settings
        self.max_response_length = config.safety.max_response_length
        self.min_response_length = config.safety.min_response_length
        self.response_timeout = config.response_timeout_seconds
        
        # Background cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """Initialize conversation manager."""
        
        # Start background cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
        
        logger.info("Conversation manager initialized")
    
    async def start_conversation(
        self,
        user_id: str,
        initial_message: Optional[str] = None,
        domain_context: str = "",
        session_metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationSession:
        """Start a new conversation session."""
        
        # Create conversation state
        conversation_state = ConversationState(
            user_id=user_id,
            domain_context=domain_context,
            current_user_input=initial_message or "",
            session_metadata=session_metadata or {}
        )
        
        # Create session
        session = ConversationSession(
            user_id=user_id,
            conversation_state=conversation_state,
            session_metadata=session_metadata or {}
        )
        
        # Store session
        self.active_sessions[session.session_id] = session
        
        logger.info(f"Started conversation session {session.session_id} for user {user_id}")
        
        # If initial message provided, generate response
        if initial_message:
            response = await self.generate_response(session.session_id, initial_message)
            session.session_metadata["initial_response"] = response.response_text
        
        return session
    
    async def generate_response(
        self,
        session_id: str,
        user_input: str,
        context_override: Optional[Dict[str, Any]] = None
    ) -> RLResponse:
        """Generate response for a conversation session."""
        
        # Get session
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session.status != SessionStatus.ACTIVE:
            raise ValueError(f"Session {session_id} is not active")
        
        try:
            # Update session activity
            session.update_activity()
            
            # Apply context override if provided
            if context_override:
                session.conversation_state.session_metadata.update(context_override)
            
            # Generate response with timeout
            response = await asyncio.wait_for(
                self.rl_agent.generate_response(
                    user_input,
                    session.conversation_state,
                    session.user_profile
                ),
                timeout=self.response_timeout
            )
            
            # Validate response
            validated_response = await self._validate_response(response, session)
            
            # Update session with response
            session.conversation_state.current_user_input = user_input
            
            logger.info(f"Generated response for session {session_id}")
            return validated_response
            
        except asyncio.TimeoutError:
            logger.error(f"Response generation timeout for session {session_id}")
            return await self._generate_timeout_response(user_input)
        
        except Exception as e:
            logger.error(f"Error generating response for session {session_id}: {e}")
            return await self._generate_error_response(user_input, str(e))
    
    async def process_feedback(
        self,
        session_id: str,
        feedback_data: Dict[str, Any]
    ) -> bool:
        """Process feedback for a conversation session."""
        
        session = self.active_sessions.get(session_id)
        if not session:
            logger.warning(f"Cannot process feedback: session {session_id} not found")
            return False
        
        try:
            # Create feedback object (simplified)
            from ..models.feedback_models import UserFeedback, FeedbackType
            
            feedback = UserFeedback(
                conversation_id=session.conversation_state.conversation_id,
                user_id=session.user_id,
                feedback_type=FeedbackType.EXPLICIT_RATING,
                rating=feedback_data.get("rating"),
                text_feedback=feedback_data.get("text"),
                timestamp=datetime.now()
            )
            
            # Process through RL agent
            await self.rl_agent.process_feedback(
                feedback,
                session.conversation_state.conversation_id
            )
            
            logger.info(f"Processed feedback for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing feedback for session {session_id}: {e}")
            return False
    
    async def end_conversation(self, session_id: str, reason: str = "user_ended") -> bool:
        """End a conversation session."""
        
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        session.status = SessionStatus.TERMINATED
        session.session_metadata["end_reason"] = reason
        session.session_metadata["ended_at"] = datetime.now().isoformat()
        
        # Store final session data (in practice, this would go to database)
        logger.info(f"Ended conversation session {session_id}: {reason}")
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        return True
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a conversation session."""
        
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "total_turns": session.total_turns,
            "session_duration": str(session.get_session_duration()),
            "conversation_length": len(session.conversation_state.conversation_history),
            "domain_context": session.conversation_state.domain_context,
            "metadata": session.session_metadata
        }
    
    async def _validate_response(
        self,
        response: RLResponse,
        session: ConversationSession
    ) -> RLResponse:
        """Validate and potentially modify response."""
        
        # Check response length
        if len(response.response_text) > self.max_response_length:
            logger.warning(f"Response too long ({len(response.response_text)} chars), truncating")
            response.response_text = response.response_text[:self.max_response_length] + "..."
        
        elif len(response.response_text) < self.min_response_length:
            logger.warning(f"Response too short ({len(response.response_text)} chars), padding")
            response.response_text += " I hope this helps with your question."
        
        # Check safety score
        if response.safety_score < 0.5:
            logger.warning(f"Low safety score ({response.safety_score}), using fallback")
            return await self._generate_safety_fallback_response(session.conversation_state.current_user_input)
        
        # Add session context to metadata
        response.metadata["session_id"] = session.session_id
        response.metadata["turn_number"] = session.total_turns
        
        return response
    
    async def _generate_timeout_response(self, user_input: str) -> RLResponse:
        """Generate response when processing times out."""
        
        timeout_responses = [
            "I apologize for the delay. Let me provide you with a helpful response to your question.",
            "Thank you for your patience. I want to make sure I give you a thoughtful answer.",
            "I'm taking a moment to consider your question carefully. Here's what I can help you with."
        ]
        
        import random
        response_text = random.choice(timeout_responses)
        
        from ..models.conversation_models import Action, ActionType
        
        action = Action(
            action_type=ActionType.EXPLANATORY_RESPONSE,
            response_text=response_text,
            confidence=0.6
        )
        
        return RLResponse(
            response_text=response_text,
            action=action,
            confidence=0.6,
            personalization_applied=False,
            safety_score=1.0,
            processing_time=self.response_timeout,
            metadata={"timeout": True}
        )
    
    async def _generate_error_response(self, user_input: str, error_message: str) -> RLResponse:
        """Generate response when an error occurs."""
        
        error_responses = [
            "I encountered an issue while processing your request. Let me try to help you in a different way.",
            "I'm having some technical difficulties, but I still want to assist you with your question.",
            "There was a problem with my response generation, but I'm here to help you."
        ]
        
        import random
        response_text = random.choice(error_responses)
        
        from ..models.conversation_models import Action, ActionType
        
        action = Action(
            action_type=ActionType.EXPLANATORY_RESPONSE,
            response_text=response_text,
            confidence=0.4
        )
        
        return RLResponse(
            response_text=response_text,
            action=action,
            confidence=0.4,
            personalization_applied=False,
            safety_score=1.0,
            processing_time=0.1,
            metadata={"error": True, "error_message": error_message}
        )
    
    async def _generate_safety_fallback_response(self, user_input: str) -> RLResponse:
        """Generate safe fallback response."""
        
        safety_responses = [
            "I want to make sure I provide you with helpful and appropriate information. Let me approach your question differently.",
            "I'm committed to giving you safe and accurate information. Here's how I can help with your question.",
            "Let me provide you with a helpful response that addresses your question appropriately."
        ]
        
        import random
        response_text = random.choice(safety_responses)
        
        from ..models.conversation_models import Action, ActionType
        
        action = Action(
            action_type=ActionType.EXPLANATORY_RESPONSE,
            response_text=response_text,
            confidence=0.7
        )
        
        return RLResponse(
            response_text=response_text,
            action=action,
            confidence=0.7,
            personalization_applied=False,
            safety_score=1.0,
            processing_time=0.1,
            metadata={"safety_fallback": True}
        )
    
    async def _cleanup_expired_sessions(self) -> None:
        """Background task to clean up expired sessions."""
        
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                current_time = datetime.now()
                expired_sessions = []
                
                for session_id, session in self.active_sessions.items():
                    if session.is_expired(self.session_timeout_minutes):
                        expired_sessions.append(session_id)
                
                # Clean up expired sessions
                for session_id in expired_sessions:
                    session = self.active_sessions[session_id]
                    session.status = SessionStatus.EXPIRED
                    
                    logger.info(f"Session {session_id} expired after {session.get_session_duration()}")
                    
                    # Store session data before removal (in practice, to database)
                    del self.active_sessions[session_id]
                
                if expired_sessions:
                    logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
    
    def get_active_sessions_count(self) -> int:
        """Get number of active sessions."""
        return len(self.active_sessions)
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get statistics about conversation sessions."""
        
        if not self.active_sessions:
            return {"active_sessions": 0}
        
        sessions = list(self.active_sessions.values())
        
        # Calculate statistics
        total_turns = sum(session.total_turns for session in sessions)
        avg_turns = total_turns / len(sessions) if sessions else 0
        
        durations = [session.get_session_duration().total_seconds() for session in sessions]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Status distribution
        status_counts = {}
        for session in sessions:
            status = session.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "active_sessions": len(sessions),
            "total_turns": total_turns,
            "average_turns_per_session": avg_turns,
            "average_session_duration_seconds": avg_duration,
            "status_distribution": status_counts,
            "session_timeout_minutes": self.session_timeout_minutes
        }
    
    async def shutdown(self) -> None:
        """Shutdown conversation manager."""
        
        # Cancel cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # End all active sessions
        for session_id in list(self.active_sessions.keys()):
            await self.end_conversation(session_id, "system_shutdown")
        
        logger.info("Conversation manager shutdown completed")