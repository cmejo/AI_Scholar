"""
WebSocket handler for real-time RL interactions.
"""

import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time RL interactions."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> session_ids
    
    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_id)
        
        logger.info(f"WebSocket connected: session {session_id}, user {user_id}")
    
    def disconnect(self, session_id: str, user_id: str):
        """Handle WebSocket disconnection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        
        if user_id in self.user_sessions:
            self.user_sessions[user_id].discard(session_id)
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]
        
        logger.info(f"WebSocket disconnected: session {session_id}")
    
    async def send_message(self, session_id: str, message: Dict):
        """Send message to specific session."""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending WebSocket message to {session_id}: {e}")
    
    async def broadcast_to_user(self, user_id: str, message: Dict):
        """Broadcast message to all sessions of a user."""
        if user_id in self.user_sessions:
            for session_id in self.user_sessions[user_id]:
                await self.send_message(session_id, message)
    
    async def handle_message(self, session_id: str, user_id: str, message: Dict):
        """Handle incoming WebSocket message."""
        
        message_type = message.get("type")
        
        if message_type == "chat":
            # Handle real-time chat message
            await self._handle_chat_message(session_id, user_id, message)
        
        elif message_type == "feedback":
            # Handle real-time feedback
            await self._handle_feedback_message(session_id, user_id, message)
        
        elif message_type == "typing":
            # Handle typing indicators
            await self._handle_typing_message(session_id, user_id, message)
        
        else:
            logger.warning(f"Unknown WebSocket message type: {message_type}")
    
    async def _handle_chat_message(self, session_id: str, user_id: str, message: Dict):
        """Handle real-time chat message."""
        
        try:
            # This would integrate with the conversation manager
            response_message = {
                "type": "chat_response",
                "session_id": session_id,
                "response": "Real-time response would be generated here",
                "timestamp": datetime.now().isoformat(),
                "metadata": {"real_time": True}
            }
            
            await self.send_message(session_id, response_message)
            
        except Exception as e:
            error_message = {
                "type": "error",
                "message": f"Error processing chat message: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            await self.send_message(session_id, error_message)
    
    async def _handle_feedback_message(self, session_id: str, user_id: str, message: Dict):
        """Handle real-time feedback."""
        
        try:
            # Process feedback
            feedback_data = message.get("data", {})
            
            # Send acknowledgment
            ack_message = {
                "type": "feedback_received",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.send_message(session_id, ack_message)
            
        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
    
    async def _handle_typing_message(self, session_id: str, user_id: str, message: Dict):
        """Handle typing indicators."""
        
        # Echo typing status (could be used for multi-user scenarios)
        typing_message = {
            "type": "typing_status",
            "session_id": session_id,
            "is_typing": message.get("is_typing", False),
            "timestamp": datetime.now().isoformat()
        }
        
        await self.send_message(session_id, typing_message)
    
    def get_connection_stats(self) -> Dict:
        """Get WebSocket connection statistics."""
        
        return {
            "active_connections": len(self.active_connections),
            "active_users": len(self.user_sessions),
            "total_sessions": sum(len(sessions) for sessions in self.user_sessions.values())
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


async def websocket_endpoint(websocket: WebSocket, session_id: str, user_id: str):
    """WebSocket endpoint handler."""
    
    await websocket_manager.connect(websocket, session_id, user_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle message
            await websocket_manager.handle_message(session_id, user_id, message)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(session_id, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        websocket_manager.disconnect(session_id, user_id)