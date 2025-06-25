#!/usr/bin/env python3
"""
Enhanced Streaming Chat Implementation
Provides real-time streaming responses with proper error handling and performance optimization
"""

from flask import Response, request, jsonify, stream_template
import json
import time
import uuid
from typing import Generator, Dict, Any
import asyncio
from datetime import datetime
from services.ollama_service import ollama_service
from services.chat_service import chat_service
from models import ChatMessage, ChatSession, db
import logging

logger = logging.getLogger(__name__)

class StreamingChatService:
    """Enhanced streaming chat service with advanced features"""
    
    def __init__(self):
        self.active_streams = {}  # Track active streaming sessions
        self.stream_metrics = {}  # Performance metrics
        
    def create_streaming_response(self, user_id: int, session_id: int, 
                                message: str, model: str = None, 
                                system_prompt: str = None) -> Response:
        """Create a streaming response for chat messages"""
        
        # Generate unique stream ID for tracking
        stream_id = str(uuid.uuid4())
        self.active_streams[stream_id] = {
            'user_id': user_id,
            'session_id': session_id,
            'start_time': time.time(),
            'status': 'active'
        }
        
        def generate_stream():
            try:
                # Save user message first
                user_msg = ChatMessage(
                    session_id=session_id,
                    user_id=user_id,
                    message_type='user',
                    content=message,
                    timestamp=datetime.utcnow()
                )
                db.session.add(user_msg)
                db.session.commit()
                
                # Send initial response with metadata
                yield self._format_stream_chunk({
                    'type': 'start',
                    'stream_id': stream_id,
                    'message_id': str(uuid.uuid4()),
                    'model': model or 'llama2:7b-chat',
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                # Generate AI response with streaming
                full_response = ""
                chunk_count = 0
                start_time = time.time()
                
                for response_chunk in self._generate_ai_response(
                    message, model, system_prompt, session_id, user_id
                ):
                    if response_chunk.get('error'):
                        yield self._format_stream_chunk({
                            'type': 'error',
                            'error': response_chunk['error'],
                            'stream_id': stream_id
                        })
                        break
                    
                    content = response_chunk.get('content', '')
                    if content:
                        full_response += content
                        chunk_count += 1
                        
                        # Send content chunk
                        yield self._format_stream_chunk({
                            'type': 'content',
                            'content': content,
                            'chunk_id': chunk_count,
                            'stream_id': stream_id,
                            'timestamp': datetime.utcnow().isoformat()
                        })
                        
                        # Add small delay to prevent overwhelming the client
                        time.sleep(0.01)
                
                # Send completion signal
                end_time = time.time()
                duration = end_time - start_time
                
                # Save complete AI response
                if full_response:
                    ai_msg = ChatMessage(
                        session_id=session_id,
                        user_id=user_id,
                        message_type='bot',
                        content=full_response,
                        model_used=model,
                        timestamp=datetime.utcnow()
                    )
                    db.session.add(ai_msg)
                    db.session.commit()
                
                yield self._format_stream_chunk({
                    'type': 'complete',
                    'stream_id': stream_id,
                    'total_chunks': chunk_count,
                    'duration': duration,
                    'tokens_per_second': len(full_response.split()) / duration if duration > 0 else 0,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                # Update metrics
                self._update_stream_metrics(stream_id, duration, chunk_count, len(full_response))
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield self._format_stream_chunk({
                    'type': 'error',
                    'error': str(e),
                    'stream_id': stream_id
                })
            finally:
                # Clean up active stream
                if stream_id in self.active_streams:
                    self.active_streams[stream_id]['status'] = 'completed'
                    del self.active_streams[stream_id]
        
        return Response(
            generate_stream(),
            mimetype='text/plain',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'  # Disable nginx buffering
            }
        )
    
    def _generate_ai_response(self, message: str, model: str, 
                            system_prompt: str, session_id: int, 
                            user_id: int) -> Generator[Dict, None, None]:
        """Generate AI response with streaming"""
        try:
            # Get conversation context
            context = self._get_conversation_context(session_id, limit=5)
            
            # Prepare the prompt with context
            full_prompt = self._prepare_prompt_with_context(message, context, system_prompt)
            
            # Stream from Ollama
            for chunk in ollama_service.generate_response(
                model=model or 'llama2:7b-chat',
                prompt=full_prompt,
                stream=True
            ):
                if chunk.get('done', False):
                    break
                
                content = chunk.get('response', '')
                if content:
                    yield {'content': content}
                    
        except Exception as e:
            yield {'error': str(e)}
    
    def _get_conversation_context(self, session_id: int, limit: int = 5) -> list:
        """Get recent conversation context"""
        try:
            recent_messages = ChatMessage.query.filter_by(session_id=session_id)\
                                             .order_by(ChatMessage.timestamp.desc())\
                                             .limit(limit * 2).all()  # Get more to account for user/bot pairs
            
            context = []
            for msg in reversed(recent_messages):
                context.append({
                    'role': 'user' if msg.message_type == 'user' else 'assistant',
                    'content': msg.content
                })
            
            return context[-limit:] if len(context) > limit else context
            
        except Exception as e:
            logger.error(f"Error getting context: {e}")
            return []
    
    def _prepare_prompt_with_context(self, message: str, context: list, system_prompt: str = None) -> str:
        """Prepare prompt with conversation context"""
        prompt_parts = []
        
        if system_prompt:
            prompt_parts.append(f"System: {system_prompt}")
        
        # Add conversation context
        for ctx_msg in context:
            role = "Human" if ctx_msg['role'] == 'user' else "Assistant"
            prompt_parts.append(f"{role}: {ctx_msg['content']}")
        
        # Add current message
        prompt_parts.append(f"Human: {message}")
        prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)
    
    def _format_stream_chunk(self, data: Dict) -> str:
        """Format data as SSE (Server-Sent Events) chunk"""
        return f"data: {json.dumps(data)}\n\n"
    
    def _update_stream_metrics(self, stream_id: str, duration: float, 
                             chunk_count: int, response_length: int):
        """Update streaming performance metrics"""
        self.stream_metrics[stream_id] = {
            'duration': duration,
            'chunk_count': chunk_count,
            'response_length': response_length,
            'tokens_per_second': len(response_length.split()) / duration if duration > 0 else 0,
            'chunks_per_second': chunk_count / duration if duration > 0 else 0,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_stream_status(self, stream_id: str) -> Dict:
        """Get status of a streaming session"""
        if stream_id in self.active_streams:
            stream_info = self.active_streams[stream_id]
            return {
                'status': stream_info['status'],
                'duration': time.time() - stream_info['start_time'],
                'user_id': stream_info['user_id'],
                'session_id': stream_info['session_id']
            }
        elif stream_id in self.stream_metrics:
            return {
                'status': 'completed',
                'metrics': self.stream_metrics[stream_id]
            }
        else:
            return {'status': 'not_found'}
    
    def cancel_stream(self, stream_id: str) -> bool:
        """Cancel an active streaming session"""
        if stream_id in self.active_streams:
            self.active_streams[stream_id]['status'] = 'cancelled'
            del self.active_streams[stream_id]
            return True
        return False

# Initialize streaming service
streaming_service = StreamingChatService()

# Enhanced API endpoints for streaming
def setup_streaming_routes(app):
    """Setup streaming chat routes"""
    
    @app.route('/api/chat/stream', methods=['POST'])
    def stream_chat():
        """Stream chat responses in real-time"""
        try:
            data = request.get_json()
            message = data.get('message', '').strip()
            session_id = data.get('session_id')
            model = data.get('model', 'llama2:7b-chat')
            system_prompt = data.get('system_prompt')
            
            # Get user ID from token (implement your auth logic)
            user_id = 1  # Replace with actual user ID from JWT token
            
            if not message:
                return jsonify({'error': 'Message cannot be empty'}), 400
            
            # Create new session if not provided
            if not session_id:
                session = ChatSession(user_id=user_id, session_name='New Chat')
                db.session.add(session)
                db.session.commit()
                session_id = session.id
            
            # Return streaming response
            return streaming_service.create_streaming_response(
                user_id=user_id,
                session_id=session_id,
                message=message,
                model=model,
                system_prompt=system_prompt
            )
            
        except Exception as e:
            logger.error(f"Stream chat error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/chat/stream/<stream_id>/status', methods=['GET'])
    def get_stream_status(stream_id):
        """Get status of a streaming session"""
        status = streaming_service.get_stream_status(stream_id)
        return jsonify(status)
    
    @app.route('/api/chat/stream/<stream_id>/cancel', methods=['POST'])
    def cancel_stream(stream_id):
        """Cancel a streaming session"""
        success = streaming_service.cancel_stream(stream_id)
        return jsonify({'cancelled': success})
    
    @app.route('/api/chat/stream/metrics', methods=['GET'])
    def get_streaming_metrics():
        """Get streaming performance metrics"""
        return jsonify({
            'active_streams': len(streaming_service.active_streams),
            'recent_metrics': list(streaming_service.stream_metrics.values())[-10:]  # Last 10
        })

# WebSocket implementation for even better real-time experience
from flask_socketio import emit, join_room, leave_room

def setup_websocket_streaming(socketio):
    """Setup WebSocket streaming for real-time chat"""
    
    @socketio.on('join_chat')
    def on_join_chat(data):
        """Join a chat session room"""
        session_id = data.get('session_id')
        if session_id:
            join_room(f"chat_{session_id}")
            emit('joined', {'session_id': session_id})
    
    @socketio.on('leave_chat')
    def on_leave_chat(data):
        """Leave a chat session room"""
        session_id = data.get('session_id')
        if session_id:
            leave_room(f"chat_{session_id}")
            emit('left', {'session_id': session_id})
    
    @socketio.on('stream_message')
    def handle_stream_message(data):
        """Handle streaming message via WebSocket"""
        try:
            message = data.get('message', '').strip()
            session_id = data.get('session_id')
            model = data.get('model', 'llama2:7b-chat')
            user_id = 1  # Get from auth
            
            if not message:
                emit('error', {'message': 'Message cannot be empty'})
                return
            
            # Create new session if needed
            if not session_id:
                session = ChatSession(user_id=user_id, session_name='New Chat')
                db.session.add(session)
                db.session.commit()
                session_id = session.id
                emit('session_created', {'session_id': session_id})
            
            # Join the session room
            join_room(f"chat_{session_id}")
            
            # Save user message
            user_msg = ChatMessage(
                session_id=session_id,
                user_id=user_id,
                message_type='user',
                content=message,
                timestamp=datetime.utcnow()
            )
            db.session.add(user_msg)
            db.session.commit()
            
            # Emit user message to room
            emit('user_message', {
                'message': message,
                'timestamp': datetime.utcnow().isoformat(),
                'session_id': session_id
            }, room=f"chat_{session_id}")
            
            # Start streaming AI response
            emit('stream_start', {
                'session_id': session_id,
                'model': model,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"chat_{session_id}")
            
            # Generate and stream response
            full_response = ""
            for chunk in streaming_service._generate_ai_response(
                message, model, None, session_id, user_id
            ):
                if chunk.get('error'):
                    emit('stream_error', {
                        'error': chunk['error'],
                        'session_id': session_id
                    }, room=f"chat_{session_id}")
                    break
                
                content = chunk.get('content', '')
                if content:
                    full_response += content
                    emit('stream_chunk', {
                        'content': content,
                        'session_id': session_id,
                        'timestamp': datetime.utcnow().isoformat()
                    }, room=f"chat_{session_id}")
            
            # Save complete AI response
            if full_response:
                ai_msg = ChatMessage(
                    session_id=session_id,
                    user_id=user_id,
                    message_type='bot',
                    content=full_response,
                    model_used=model,
                    timestamp=datetime.utcnow()
                )
                db.session.add(ai_msg)
                db.session.commit()
            
            # Emit completion
            emit('stream_complete', {
                'session_id': session_id,
                'full_response': full_response,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"chat_{session_id}")
            
        except Exception as e:
            logger.error(f"WebSocket streaming error: {e}")
            emit('stream_error', {
                'error': str(e),
                'session_id': data.get('session_id')
            })

# Usage example for integration
def integrate_streaming_with_app(app, socketio):
    """Integrate streaming features with the main app"""
    setup_streaming_routes(app)
    setup_websocket_streaming(socketio)
    
    print("✅ Streaming chat features enabled:")
    print("  📡 HTTP Streaming: /api/chat/stream")
    print("  🔌 WebSocket Streaming: stream_message event")
    print("  📊 Metrics: /api/chat/stream/metrics")
    print("  ⏹️  Cancel: /api/chat/stream/<id>/cancel")