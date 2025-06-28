#!/usr/bin/env python3
"""
AI Chatbot Web Application - Enterprise Edition
Enhanced with real-time collaboration and admin dashboard
"""

from flask import Flask, request, jsonify, Blueprint
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import requests
import json
import os
import time
from datetime import datetime, timedelta
import jwt
import logging
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import models and services
from models import (
    db, init_db, User, ChatSession, ChatMessage, UserSession, DatabaseQueries,
    SessionInvitation, SessionActivityLog, CustomDashboard, AnalyticsWidget,
    MLMetric, Prediction, AnomalyDetection, UserBehaviorPattern, 
    ModelPerformanceTracking, TrendAnalysis
)
from services.collaboration_websocket_service import CollaborationWebSocketService
from services.admin_service import AdminService
from services.advanced_sharing_service import AdvancedSharingService
from services.custom_analytics_service import CustomAnalyticsService
from services.ml_analytics_service import MLAnalyticsService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=int(os.environ.get('JWT_EXPIRES_HOURS', 24)))

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///chatbot_enterprise.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
init_db(app)

# Enable CORS for React frontend
CORS(app, origins=["http://localhost:3000", "http://localhost:80"], supports_credentials=True)

# Initialize SocketIO with enhanced configuration
socketio = SocketIO(
    app, 
    cors_allowed_origins=["http://localhost:3000", "http://localhost:80"], 
    supports_credentials=True,
    logger=True,
    engineio_logger=True
)

# AI Configuration
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
DEFAULT_MODEL = os.environ.get('DEFAULT_MODEL', 'llama2:latest')

# Initialize collaboration service
collaboration_service = CollaborationWebSocketService(socketio, app.config['JWT_SECRET_KEY'])

class OllamaService:
    """Enhanced Ollama service for local LLM management"""
    
    def __init__(self, base_url=OLLAMA_BASE_URL):
        self.base_url = base_url
    
    def is_available(self):
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self):
        """Get list of available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        except Exception:
            return []
    
    def generate_response(self, model, prompt, stream=False):
        """Generate response from model"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=stream,
                timeout=30
            )
            response.raise_for_status()
            
            if stream:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            yield data
                        except json.JSONDecodeError:
                            continue
            else:
                return response.json()
                
        except Exception as e:
            if stream:
                yield {"error": str(e), "done": True}
            else:
                return {"error": str(e)}

# Initialize services
ollama_service = OllamaService()

# Authentication helpers
def token_required(f):
    """Decorator to require JWT token for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid'}), 401
        
        return f(current_user_id, *args, **kwargs)
    return decorated

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated(current_user_id, *args, **kwargs):
        user = User.query.get(current_user_id)
        if not user or not user.is_admin:
            return jsonify({'message': 'Admin privileges required'}), 403
        
        return f(current_user_id, *args, **kwargs)
    return decorated

# Basic Routes
@app.route('/')
def index():
    """Serve the main chat interface"""
    return jsonify({
        "message": "AI Scholar Chatbot Backend - Enterprise Edition", 
        "status": "running",
        "features": ["real-time-collaboration", "admin-dashboard", "analytics"]
    })

@app.route('/api/health')
def health_check():
    """Enhanced health check endpoint"""
    try:
        ollama_status = ollama_service.is_available()
        models = ollama_service.list_models()
        
        # Get collaboration stats
        collaboration_stats = collaboration_service.get_active_sessions()
        
        # Get system health
        system_health = AdminService.get_system_health()
        
        return jsonify({
            "status": "healthy" if ollama_status and system_health['status'] != 'unhealthy' else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "ollama": {
                    "status": "up" if ollama_status else "down",
                    "models_available": len(models)
                },
                "database": system_health.get('database', {}),
                "collaboration": {
                    "status": "up",
                    "active_rooms": collaboration_stats['total_rooms'],
                    "active_users": collaboration_stats['total_users']
                }
            },
            "models": models,
            "system_health": system_health
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# Authentication routes (enhanced from original)
@app.route('/api/auth/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not username or not email or not password:
            return jsonify({'message': 'Username, email, and password are required'}), 400
        
        if len(password) < 8:
            return jsonify({'message': 'Password must be at least 8 characters long'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            return jsonify({'message': 'Username or email already exists'}), 400
        
        # Create new user
        user = User(username=username, email=email, password=password)
        
        db.session.add(user)
        db.session.commit()
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user.id,
            'username': user.username,
            'is_admin': user.is_admin,
            'exp': datetime.utcnow() + app.config['JWT_ACCESS_TOKEN_EXPIRES']
        }, app.config['JWT_SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Registration failed: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'message': 'Username and password are required'}), 400
        
        # Find user by username or email
        user = DatabaseQueries.get_user_by_username_or_email(username)
        
        if not user or not user.check_password(password):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Update last login
        user.update_last_login()
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user.id,
            'username': user.username,
            'is_admin': user.is_admin,
            'exp': datetime.utcnow() + app.config['JWT_ACCESS_TOKEN_EXPIRES']
        }, app.config['JWT_SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Login failed: {str(e)}'}), 500

# Chat routes (enhanced with collaboration)
@app.route('/api/chat/send', methods=['POST'])
@token_required
def send_message(current_user_id):
    """Enhanced chat endpoint with collaboration support"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        model = data.get('model', DEFAULT_MODEL)
        session_id = data.get('session_id')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
        
        # Create or get session
        if session_id:
            session = ChatSession.query.filter_by(id=session_id, user_id=current_user_id).first()
            if not session:
                return jsonify({'success': False, 'error': 'Session not found'}), 404
        else:
            session = ChatSession(user_id=current_user_id, model_name=model)
            db.session.add(session)
            db.session.commit()
            session_id = session.id
        
        # Save user message (initial save)
        user_message = ChatMessage(
            session_id=session_id,
            user_id=current_user_id,
            message_type='user',
            content=message
        )
        db.session.add(user_message)
        db.session.commit()
        
        # Process user message for safety (PII redaction and content moderation)
        from services.safety_compliance_service import SafetyComplianceService
        safety_service = SafetyComplianceService()
        
        user_safety_result = safety_service.process_message_safety(
            message=user_message,
            content=message,
            message_type='user_input'
        )
        
        # Update user message with safety processing results
        if user_safety_result['pii_redacted']:
            user_message.content = user_safety_result['final_content']
        
        # Check if user input should be blocked
        if user_safety_result['should_block']:
            db.session.commit()
            return jsonify({
                "success": False,
                "error": "Your message contains content that violates our safety guidelines.",
                "session_id": session_id,
                "safety_blocked": True
            }), 400
        
        # Broadcast user message to collaboration room (use processed content)
        collaboration_service.broadcast_to_session(session_id, 'new_message', {
            'message_id': user_message.id,
            'user_id': current_user_id,
            'message_type': 'user',
            'content': user_message.content,  # Use processed content
            'timestamp': user_message.timestamp.isoformat(),
            'session_id': session_id,
            'has_pii_redaction': user_safety_result['pii_redacted']
        })
        
        # Create enhanced prompt with tool capabilities
        from services.chat_service import chat_service
        enhanced_prompt = chat_service.create_enhanced_prompt_with_tools(user_message.content)
        
        # Generate AI response
        start_time = time.time()
        result = ollama_service.generate_response(model, enhanced_prompt, stream=False)
        response_time = time.time() - start_time
        
        if 'error' not in result:
            raw_ai_response = result.get('response', 'Sorry, I could not generate a response.')
            
            # Process AI response for tool calls and mixed content
            processed_response = chat_service.process_ai_response_with_tools(
                raw_ai_response, user_message.content
            )
            
            # Determine final content for storage
            if processed_response['type'] == 'mixed':
                # Store the processed content as JSON for mixed content
                final_content = json.dumps(processed_response)
                content_type = 'mixed'
            else:
                # Store as regular text
                final_content = processed_response['content']
                content_type = 'text'
            
            # Save bot response (initial save)
            bot_message = ChatMessage(
                session_id=session_id,
                user_id=current_user_id,
                message_type='bot',
                content=final_content,
                model_used=model,
                response_time=response_time,
                metadata={
                    'content_type': content_type,
                    'has_tools': processed_response.get('has_tools', False),
                    'tool_count': processed_response.get('tool_count', 0)
                }
            )
            db.session.add(bot_message)
            db.session.commit()
            
            # Process AI response for safety (content moderation)
            # Use the raw response for safety checking
            ai_safety_result = safety_service.process_message_safety(
                message=bot_message,
                content=raw_ai_response,
                message_type='ai_response'
            )
            
            # Update bot message with safety processing results if needed
            if ai_safety_result['should_block']:
                bot_message.content = ai_safety_result['final_content']
                bot_message.metadata['safety_blocked'] = True
            
            # Update session timestamp
            session.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Broadcast bot response to collaboration room
            collaboration_service.broadcast_to_session(session_id, 'new_message', {
                'message_id': bot_message.id,
                'user_id': current_user_id,
                'message_type': 'bot',
                'content': bot_message.content,
                'timestamp': bot_message.timestamp.isoformat(),
                'model_used': model,
                'response_time': response_time,
                'session_id': session_id
            })
            
            return jsonify({
                "success": True,
                "response": bot_message.content,
                "model": model,
                "session_id": session_id,
                "message_id": bot_message.id,
                "response_time": response_time,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Unknown error'),
                "session_id": session_id
            })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": f"Server Error: {str(e)}"
        }), 500

@app.route('/api/chat/sessions', methods=['GET'])
@token_required
def get_chat_sessions(current_user_id):
    """Get user's chat sessions"""
    try:
        sessions = ChatSession.query.filter_by(user_id=current_user_id)\
                                  .order_by(ChatSession.updated_at.desc()).all()
        sessions_data = [session.to_dict() for session in sessions]
        return jsonify({'sessions': sessions_data}), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to get sessions: {str(e)}'}), 500

@app.route('/api/chat/sessions/<int:session_id>', methods=['GET'])
@token_required
def get_session_messages(current_user_id, session_id):
    """Get messages for a specific session"""
    try:
        # Verify session belongs to user or is shared
        session = ChatSession.query.filter_by(id=session_id).first()
        
        if not session:
            return jsonify({'message': 'Session not found'}), 404
        
        # Check if user owns session or has access to shared session
        if session.user_id != current_user_id and not session.is_shared:
            return jsonify({'message': 'Access denied'}), 403
        
        messages = ChatMessage.query.filter_by(session_id=session_id)\
                                  .order_by(ChatMessage.timestamp.asc()).all()
        messages_data = [message.to_dict() for message in messages]
        
        # Get active users in this session
        active_users = collaboration_service.get_session_users(session_id)
        
        return jsonify({
            'messages': messages_data,
            'session': session.to_dict(),
            'active_users': active_users
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to get messages: {str(e)}'}), 500

# Admin Dashboard Routes
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/overview', methods=['GET'])
@token_required
@admin_required
def get_admin_overview(current_user_id):
    """Get admin dashboard overview"""
    try:
        overview = AdminService.get_system_overview()
        return jsonify(overview), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/analytics/users', methods=['GET'])
@token_required
@admin_required
def get_user_analytics(current_user_id):
    """Get user analytics"""
    try:
        days = request.args.get('days', 30, type=int)
        analytics = AdminService.get_user_analytics(days)
        return jsonify(analytics), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/analytics/usage', methods=['GET'])
@token_required
@admin_required
def get_usage_analytics(current_user_id):
    """Get usage analytics"""
    try:
        days = request.args.get('days', 30, type=int)
        analytics = AdminService.get_usage_analytics(days)
        return jsonify(analytics), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_users_list(current_user_id):
    """Get paginated list of users"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', None)
        
        users_data = AdminService.get_user_list(page, per_page, search)
        return jsonify(users_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@token_required
@admin_required
def toggle_user_status(current_user_id, user_id):
    """Toggle user active status"""
    try:
        result = AdminService.toggle_user_status(user_id, current_user_id)
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/promote', methods=['POST'])
@token_required
@admin_required
def promote_user(current_user_id, user_id):
    """Promote user to admin"""
    try:
        result = AdminService.promote_user_to_admin(user_id, current_user_id)
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/system/health', methods=['GET'])
@token_required
@admin_required
def get_system_health(current_user_id):
    """Get detailed system health"""
    try:
        health = AdminService.get_system_health()
        return jsonify(health), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/collaboration/stats', methods=['GET'])
@token_required
@admin_required
def get_collaboration_stats(current_user_id):
    """Get collaboration statistics"""
    try:
        stats = AdminService.get_collaboration_stats()
        
        # Add real-time collaboration stats
        realtime_stats = collaboration_service.get_active_sessions()
        stats['realtime'] = realtime_stats
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Advanced Sharing Routes
@app.route('/api/sessions/<int:session_id>/invite', methods=['POST'])
@token_required
def create_session_invitation(current_user_id, session_id):
    """Create a session invitation"""
    try:
        data = request.get_json()
        email = data.get('email')
        permissions = data.get('permissions', 'view')
        message = data.get('message')
        
        result = AdvancedSharingService.create_session_invitation(
            session_id, current_user_id, email, permissions, message
        )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invitations/<invitation_token>/accept', methods=['POST'])
@token_required
def accept_invitation(current_user_id, invitation_token):
    """Accept a session invitation"""
    try:
        result = AdvancedSharingService.accept_invitation(invitation_token, current_user_id)
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invitations/<invitation_token>/decline', methods=['POST'])
@token_required
def decline_invitation(current_user_id, invitation_token):
    """Decline a session invitation"""
    try:
        result = AdvancedSharingService.decline_invitation(invitation_token, current_user_id)
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sessions/<int:session_id>/collaborators', methods=['GET'])
@token_required
def get_session_collaborators(current_user_id, session_id):
    """Get session collaborators"""
    try:
        result = AdvancedSharingService.get_session_collaborators(session_id, current_user_id)
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sessions/<int:session_id>/collaborators/<int:collaborator_id>', methods=['DELETE'])
@token_required
def remove_collaborator(current_user_id, session_id, collaborator_id):
    """Remove a collaborator from session"""
    try:
        result = AdvancedSharingService.remove_collaborator(session_id, current_user_id, collaborator_id)
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sessions/<int:session_id>/collaboration-settings', methods=['PUT'])
@token_required
def update_collaboration_settings(current_user_id, session_id):
    """Update collaboration settings"""
    try:
        settings = request.get_json()
        result = AdvancedSharingService.update_collaboration_settings(session_id, current_user_id, settings)
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sessions/<int:session_id>/activity', methods=['GET'])
@token_required
def get_session_activity(current_user_id, session_id):
    """Get session activity log"""
    try:
        limit = request.args.get('limit', 50, type=int)
        result = AdvancedSharingService.get_session_activity(session_id, current_user_id, limit)
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Custom Analytics Dashboard Routes
@admin_bp.route('/dashboards', methods=['GET'])
@token_required
@admin_required
def get_custom_dashboards(current_user_id):
    """Get custom dashboards"""
    try:
        include_public = request.args.get('include_public', True, type=bool)
        result = CustomAnalyticsService.get_user_dashboards(current_user_id, include_public)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/dashboards', methods=['POST'])
@token_required
@admin_required
def create_custom_dashboard(current_user_id):
    """Create a custom dashboard"""
    try:
        data = request.get_json()
        result = CustomAnalyticsService.create_custom_dashboard(
            current_user_id,
            data.get('name'),
            data.get('layout'),
            data.get('widgets'),
            description=data.get('description'),
            is_default=data.get('is_default', False),
            is_public=data.get('is_public', False)
        )
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/dashboards/<int:dashboard_id>', methods=['GET'])
@token_required
@admin_required
def get_dashboard(current_user_id, dashboard_id):
    """Get a specific dashboard"""
    try:
        dashboard = CustomDashboard.query.get(dashboard_id)
        if not dashboard:
            return jsonify({'success': False, 'error': 'Dashboard not found'}), 404
        
        # Check permissions
        if dashboard.user_id != current_user_id and not dashboard.is_public:
            return jsonify({'success': False, 'error': 'Permission denied'}), 403
        
        return jsonify({'success': True, 'dashboard': dashboard.to_dict()}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/dashboards/<int:dashboard_id>', methods=['PUT'])
@token_required
@admin_required
def update_dashboard(current_user_id, dashboard_id):
    """Update a custom dashboard"""
    try:
        updates = request.get_json()
        result = CustomAnalyticsService.update_dashboard(dashboard_id, current_user_id, updates)
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/dashboards/<int:dashboard_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_dashboard(current_user_id, dashboard_id):
    """Delete a custom dashboard"""
    try:
        result = CustomAnalyticsService.delete_dashboard(dashboard_id, current_user_id)
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/widgets/<widget_type>/data', methods=['GET'])
@token_required
@admin_required
def get_widget_data(current_user_id, widget_type):
    """Get data for a specific widget"""
    try:
        data_source = request.args.get('data_source', widget_type)
        config = request.args.to_dict()
        
        # Convert string values to appropriate types
        if 'days' in config:
            config['days'] = int(config['days'])
        if 'limit' in config:
            config['limit'] = int(config['limit'])
        
        result = CustomAnalyticsService.get_widget_data(widget_type, data_source, config, current_user_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/dashboards/<int:dashboard_id>/export', methods=['GET'])
@token_required
@admin_required
def export_dashboard_data(current_user_id, dashboard_id):
    """Export dashboard data"""
    try:
        format_type = request.args.get('format', 'json')
        result = CustomAnalyticsService.export_dashboard_data(dashboard_id, current_user_id, format_type)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/analytics/collaboration', methods=['GET'])
@token_required
@admin_required
def get_collaboration_analytics(current_user_id):
    """Get collaboration analytics"""
    try:
        days = request.args.get('days', 30, type=int)
        result = AdvancedSharingService.get_collaboration_analytics(current_user_id, days)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# User Invitation Routes
@app.route('/api/user/invitations', methods=['GET'])
@token_required
def get_user_invitations(current_user_id):
    """Get user's invitations"""
    try:
        status = request.args.get('status')
        result = AdvancedSharingService.get_user_invitations(current_user_id, status)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ML Analytics Routes
@admin_bp.route('/ml-insights/predictions', methods=['GET'])
@token_required
@admin_required
def get_ml_predictions(current_user_id):
    """Get ML predictions"""
    try:
        days = request.args.get('days', 30, type=int)
        predictions = Prediction.query.filter(
            Prediction.created_at >= datetime.utcnow() - timedelta(days=days)
        ).order_by(Prediction.target_date.asc()).all()
        
        return jsonify({
            'success': True,
            'predictions': [p.to_dict() for p in predictions]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/ml-insights/anomalies', methods=['GET'])
@token_required
@admin_required
def get_ml_anomalies(current_user_id):
    """Get ML anomalies"""
    try:
        days = request.args.get('days', 30, type=int)
        anomalies = AnomalyDetection.query.filter(
            AnomalyDetection.created_at >= datetime.utcnow() - timedelta(days=days)
        ).order_by(AnomalyDetection.created_at.desc()).all()
        
        # Get severity distribution
        severity_dist = db.session.query(
            AnomalyDetection.severity,
            func.count(AnomalyDetection.id).label('count')
        ).filter(
            AnomalyDetection.created_at >= datetime.utcnow() - timedelta(days=days)
        ).group_by(AnomalyDetection.severity).all()
        
        return jsonify({
            'success': True,
            'anomalies': [a.to_dict() for a in anomalies],
            'severity_distribution': {row.severity: row.count for row in severity_dist},
            'unresolved_count': len([a for a in anomalies if not a.is_resolved])
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/ml-insights/trends', methods=['GET'])
@token_required
@admin_required
def get_ml_trends(current_user_id):
    """Get ML trend analyses"""
    try:
        days = request.args.get('days', 30, type=int)
        trends = TrendAnalysis.query.filter(
            TrendAnalysis.created_at >= datetime.utcnow() - timedelta(days=days)
        ).order_by(TrendAnalysis.analysis_date.desc()).all()
        
        return jsonify({
            'success': True,
            'trends': [t.to_dict() for t in trends]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/ml-insights/user-patterns', methods=['GET'])
@token_required
@admin_required
def get_user_patterns(current_user_id):
    """Get user behavior patterns"""
    try:
        days = request.args.get('days', 30, type=int)
        patterns = UserBehaviorPattern.query.filter(
            UserBehaviorPattern.last_updated >= datetime.utcnow() - timedelta(days=days)
        ).order_by(UserBehaviorPattern.confidence_score.desc()).all()
        
        return jsonify({
            'success': True,
            'patterns': [p.to_dict() for p in patterns]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/ml-insights/metrics', methods=['GET'])
@token_required
@admin_required
def get_ml_metrics(current_user_id):
    """Get ML metrics"""
    try:
        days = request.args.get('days', 30, type=int)
        metrics = MLMetric.query.filter(
            MLMetric.created_at >= datetime.utcnow() - timedelta(days=days)
        ).order_by(MLMetric.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'metrics': [m.to_dict() for m in metrics]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/ml-insights/generate-predictions', methods=['POST'])
@token_required
@admin_required
def generate_predictions(current_user_id):
    """Generate new predictions"""
    try:
        data = request.get_json()
        days_ahead = data.get('days_ahead', 30)
        
        result = MLAnalyticsService.generate_user_growth_predictions(days_ahead)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/ml-insights/detect-anomalies', methods=['POST'])
@token_required
@admin_required
def detect_anomalies(current_user_id):
    """Run anomaly detection"""
    try:
        data = request.get_json()
        lookback_days = data.get('lookback_days', 30)
        
        result = MLAnalyticsService.detect_usage_anomalies(lookback_days)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/ml-insights/analyze-behavior', methods=['POST'])
@token_required
@admin_required
def analyze_behavior(current_user_id):
    """Analyze user behavior patterns"""
    try:
        result = MLAnalyticsService.analyze_user_behavior_patterns()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/ml-insights/trend-analysis', methods=['POST'])
@token_required
@admin_required
def perform_trend_analysis(current_user_id):
    """Perform trend analysis"""
    try:
        data = request.get_json()
        metric_name = data.get('metric_name', 'user_activity')
        time_period = data.get('time_period', 'daily')
        days = data.get('days', 30)
        
        result = MLAnalyticsService.perform_trend_analysis(metric_name, time_period, days)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/ml-insights/summary', methods=['GET'])
@token_required
@admin_required
def get_ml_insights_summary(current_user_id):
    """Get ML insights summary"""
    try:
        result = MLAnalyticsService.generate_ml_insights_summary()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/ml-insights/anomalies/<int:anomaly_id>/resolve', methods=['POST'])
@token_required
@admin_required
def resolve_anomaly(current_user_id, anomaly_id):
    """Resolve an anomaly"""
    try:
        anomaly = AnomalyDetection.query.get(anomaly_id)
        if not anomaly:
            return jsonify({'success': False, 'error': 'Anomaly not found'}), 404
        
        anomaly.resolve()
        return jsonify({'success': True, 'message': 'Anomaly resolved'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Register admin blueprint
app.register_blueprint(admin_bp)

# Models endpoint
@app.route('/api/models/simple', methods=['GET'])
def get_models_simple():
    """Get simple list of model names"""
    try:
        models = ollama_service.list_models()
        
        return jsonify({
            'models': models,
            'default_model': DEFAULT_MODEL
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Failed to get models: {str(e)}'}), 500

# Browser Extension API Routes
@app.route('/api/extension/process', methods=['POST'])
def extension_process_text():
    """Process text from browser extension"""
    try:
        from services.browser_extension_service import BrowserExtensionService
        
        # Get API key from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'API key required'}), 401
        
        api_key = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Authenticate user
        extension_service = BrowserExtensionService()
        user = extension_service.authenticate_api_key(api_key)
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid API key'}), 401
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        text = data.get('text', '').strip()
        action = data.get('action', 'explain')
        context = data.get('context', {})
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        # Process the text
        result = extension_service.process_text_action(user, action, text, context)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in extension process endpoint: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/extension/stats', methods=['GET'])
def extension_get_stats():
    """Get usage statistics for browser extension"""
    try:
        from services.browser_extension_service import BrowserExtensionService
        
        # Get API key from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'API key required'}), 401
        
        api_key = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Authenticate user
        extension_service = BrowserExtensionService()
        user = extension_service.authenticate_api_key(api_key)
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid API key'}), 401
        
        # Get stats
        result = extension_service.get_user_stats(user)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in extension stats endpoint: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/extension/test', methods=['GET'])
def extension_test_connection():
    """Test browser extension connection"""
    try:
        from services.browser_extension_service import BrowserExtensionService
        
        # Get API key from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'API key required'}), 401
        
        api_key = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Authenticate user
        extension_service = BrowserExtensionService()
        user = extension_service.authenticate_api_key(api_key)
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid API key'}), 401
        
        # Test connection
        result = extension_service.test_connection(user)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in extension test endpoint: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/extension/usage', methods=['POST'])
def extension_track_usage():
    """Track browser extension usage (for analytics)"""
    try:
        from services.browser_extension_service import BrowserExtensionService
        
        # Get API key from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'API key required'}), 401
        
        api_key = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Authenticate user
        extension_service = BrowserExtensionService()
        user = extension_service.authenticate_api_key(api_key)
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid API key'}), 401
        
        # This endpoint is for additional tracking if needed
        # The main tracking happens in process_text_action
        
        return jsonify({'success': True, 'message': 'Usage tracked'})
        
    except Exception as e:
        logger.error(f"Error in extension usage endpoint: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# API Key Management Routes
@app.route('/api/keys', methods=['GET'])
@token_required
def get_api_keys():
    """Get user's API keys"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        api_keys = APIKey.query.filter_by(user_id=user.id, is_active=True).all()
        
        return jsonify({
            'success': True,
            'api_keys': [key.to_dict() for key in api_keys]
        })
        
    except Exception as e:
        logger.error(f"Error getting API keys: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/keys', methods=['POST'])
@token_required
def create_api_key():
    """Create a new API key"""
    try:
        from services.browser_extension_service import BrowserExtensionService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        key_name = data.get('name', 'Browser Extension Key')
        permissions = data.get('permissions', ['explain', 'summarize', 'rewrite', 'translate', 'analyze'])
        
        extension_service = BrowserExtensionService()
        result = extension_service.create_api_key(user.id, key_name, permissions)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/keys/<int:key_id>', methods=['DELETE'])
@token_required
def delete_api_key(key_id):
    """Delete an API key"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        api_key = APIKey.query.filter_by(id=key_id, user_id=user.id).first()
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        api_key.is_active = False
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'API key deleted'})
        
    except Exception as e:
        logger.error(f"Error deleting API key: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# External Data Source Management Routes
@app.route('/api/data-sources', methods=['GET'])
@token_required
def get_data_sources():
    """Get user's external data sources"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data_sources = ExternalDataSource.query.filter_by(user_id=user.id).all()
        
        return jsonify({
            'success': True,
            'data_sources': [source.to_dict() for source in data_sources]
        })
        
    except Exception as e:
        logger.error(f"Error getting data sources: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/data-sources/<int:source_id>/sync', methods=['POST'])
@token_required
def trigger_data_source_sync(source_id):
    """Trigger sync for a data source"""
    try:
        from services.automated_sync_service import AutomatedSyncService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data_source = ExternalDataSource.query.filter_by(
            id=source_id, 
            user_id=user.id
        ).first()
        
        if not data_source:
            return jsonify({'error': 'Data source not found'}), 404
        
        sync_service = AutomatedSyncService()
        result = sync_service.trigger_sync(source_id, 'manual_sync')
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error triggering sync: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/data-sources/<int:source_id>/status', methods=['GET'])
@token_required
def get_data_source_status(source_id):
    """Get sync status for a data source"""
    try:
        from services.automated_sync_service import AutomatedSyncService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data_source = ExternalDataSource.query.filter_by(
            id=source_id, 
            user_id=user.id
        ).first()
        
        if not data_source:
            return jsonify({'error': 'Data source not found'}), 404
        
        sync_service = AutomatedSyncService()
        result = sync_service.get_sync_status(source_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Safety and Compliance API Routes
@app.route('/api/safety/dashboard', methods=['GET'])
@token_required
def get_safety_dashboard():
    """Get safety and compliance dashboard data"""
    try:
        from services.safety_compliance_service import SafetyComplianceService
        
        user = get_current_user()
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        days = request.args.get('days', 30, type=int)
        
        safety_service = SafetyComplianceService()
        dashboard_data = safety_service.get_safety_dashboard_data(days=days)
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        logger.error(f"Error getting safety dashboard: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/safety/user/<int:user_id>/profile', methods=['GET'])
@token_required
def get_user_safety_profile(user_id):
    """Get safety profile for a specific user"""
    try:
        from services.safety_compliance_service import SafetyComplianceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Users can only view their own profile unless they're admin
        if user.id != user_id and not user.is_admin:
            return jsonify({'error': 'Access denied'}), 403
        
        safety_service = SafetyComplianceService()
        profile_data = safety_service.get_user_safety_profile(user_id)
        
        return jsonify(profile_data)
        
    except Exception as e:
        logger.error(f"Error getting user safety profile: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/safety/incidents', methods=['GET'])
@token_required
def get_safety_incidents():
    """Get safety incidents (admin only)"""
    try:
        user = get_current_user()
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from models import SafetyIncident
        
        # Get query parameters
        status = request.args.get('status')
        severity = request.args.get('severity')
        limit = request.args.get('limit', 50, type=int)
        
        # Build query
        query = SafetyIncident.query
        
        if status:
            query = query.filter_by(status=status)
        if severity:
            query = query.filter_by(severity=severity)
        
        incidents = query.order_by(SafetyIncident.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'incidents': [incident.to_dict() for incident in incidents]
        })
        
    except Exception as e:
        logger.error(f"Error getting safety incidents: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/safety/incidents/<int:incident_id>/assign', methods=['POST'])
@token_required
def assign_safety_incident(incident_id):
    """Assign safety incident to admin"""
    try:
        user = get_current_user()
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from models import db, SafetyIncident
        
        incident = SafetyIncident.query.get(incident_id)
        if not incident:
            return jsonify({'error': 'Incident not found'}), 404
        
        data = request.get_json()
        admin_id = data.get('admin_id', user.id)
        
        incident.assign_to(admin_id)
        
        return jsonify({
            'success': True,
            'message': 'Incident assigned successfully'
        })
        
    except Exception as e:
        logger.error(f"Error assigning safety incident: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/safety/incidents/<int:incident_id>/resolve', methods=['POST'])
@token_required
def resolve_safety_incident(incident_id):
    """Resolve safety incident"""
    try:
        user = get_current_user()
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from models import db, SafetyIncident
        
        incident = SafetyIncident.query.get(incident_id)
        if not incident:
            return jsonify({'error': 'Incident not found'}), 404
        
        data = request.get_json()
        resolution = data.get('resolution', '')
        actions_taken = data.get('actions_taken', [])
        
        incident.resolve(resolution, actions_taken)
        
        return jsonify({
            'success': True,
            'message': 'Incident resolved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error resolving safety incident: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/privacy/consent', methods=['POST'])
@token_required
def manage_user_consent():
    """Manage user consent for privacy compliance"""
    try:
        from services.safety_compliance_service import SafetyComplianceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        consent_type = data.get('consent_type')
        granted = data.get('granted', False)
        consent_text = data.get('consent_text')
        
        if not consent_type:
            return jsonify({'error': 'Consent type is required'}), 400
        
        safety_service = SafetyComplianceService()
        result = safety_service.manage_user_consent(
            user_id=user.id,
            consent_type=consent_type,
            granted=granted,
            consent_text=consent_text
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error managing user consent: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/privacy/export', methods=['POST'])
@token_required
def export_user_data():
    """Export user data for GDPR compliance"""
    try:
        from services.safety_compliance_service import SafetyComplianceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        safety_service = SafetyComplianceService()
        result = safety_service.export_user_data(user_id=user.id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error exporting user data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/privacy/delete', methods=['DELETE'])
@token_required
def delete_user_data():
    """Delete user data for GDPR compliance (right to be forgotten)"""
    try:
        from services.safety_compliance_service import SafetyComplianceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Require explicit confirmation
        data = request.get_json()
        if not data or not data.get('confirm_deletion'):
            return jsonify({'error': 'Deletion confirmation required'}), 400
        
        safety_service = SafetyComplianceService()
        result = safety_service.delete_user_data(user_id=user.id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error deleting user data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# AI & Model Mastery API Routes
@app.route('/api/ai-mastery/feedback-stats', methods=['GET'])
@token_required
def get_feedback_statistics():
    """Get feedback statistics for fine-tuning readiness"""
    try:
        user = get_current_user()
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from services.fine_tuning_service import fine_tuning_service
        
        days = request.args.get('days', 30, type=int)
        stats = fine_tuning_service.get_feedback_statistics(days=days)
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting feedback statistics: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/ai-mastery/prepare-dataset', methods=['POST'])
@token_required
def prepare_fine_tuning_dataset():
    """Prepare dataset for fine-tuning from user feedback"""
    try:
        user = get_current_user()
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from services.fine_tuning_service import fine_tuning_service
        
        data = request.get_json() or {}
        min_feedback_pairs = data.get('min_feedback_pairs', 100)
        days = data.get('days', 30)
        
        result = fine_tuning_service.prepare_dpo_dataset_from_feedback(
            min_feedback_pairs=min_feedback_pairs,
            days=days
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error preparing dataset: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/ai-mastery/start-fine-tuning', methods=['POST'])
@token_required
def start_fine_tuning():
    """Start a fine-tuning job"""
    try:
        user = get_current_user()
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from services.fine_tuning_service import fine_tuning_service
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        dataset_file = data.get('dataset_file')
        base_model = data.get('base_model', 'llama2:7b-chat')
        training_config = data.get('training_config', {})
        
        if not dataset_file:
            return jsonify({'error': 'Dataset file is required'}), 400
        
        result = fine_tuning_service.start_dpo_fine_tuning(
            dataset_file=dataset_file,
            base_model=base_model,
            training_config=training_config
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error starting fine-tuning: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/ai-mastery/fine-tuning-jobs', methods=['GET'])
@token_required
def get_fine_tuning_jobs():
    """Get list of fine-tuning jobs"""
    try:
        user = get_current_user()
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from models import FineTuningJob
        
        limit = request.args.get('limit', 20, type=int)
        jobs = FineTuningJob.query.order_by(FineTuningJob.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'jobs': [job.to_dict() for job in jobs]
        })
        
    except Exception as e:
        logger.error(f"Error getting fine-tuning jobs: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/ai-mastery/fine-tuning-jobs/<int:job_id>', methods=['GET'])
@token_required
def get_fine_tuning_job(job_id):
    """Get specific fine-tuning job details"""
    try:
        user = get_current_user()
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from models import FineTuningJob
        
        job = FineTuningJob.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify({
            'success': True,
            'job': job.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting fine-tuning job: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/ai-mastery/rag-evaluation-stats', methods=['GET'])
@token_required
def get_rag_evaluation_stats():
    """Get RAG evaluation statistics"""
    try:
        user = get_current_user()
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from services.rag_evaluation_service import rag_evaluation_service
        
        days = request.args.get('days', 30, type=int)
        stats = rag_evaluation_service.get_evaluation_statistics(days=days)
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting RAG evaluation stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/ai-mastery/low-quality-queries', methods=['GET'])
@token_required
def get_low_quality_queries():
    """Get queries with low RAG quality for improvement"""
    try:
        user = get_current_user()
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from services.rag_evaluation_service import rag_evaluation_service
        
        threshold = request.args.get('threshold', 0.6, type=float)
        limit = request.args.get('limit', 20, type=int)
        
        result = rag_evaluation_service.get_low_quality_queries(
            threshold=threshold,
            limit=limit
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting low quality queries: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/ai-mastery/evaluate-rag', methods=['POST'])
@token_required
def trigger_rag_evaluation():
    """Manually trigger RAG evaluation for a message"""
    try:
        user = get_current_user()
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        message_id = data.get('message_id')
        if not message_id:
            return jsonify({'error': 'Message ID is required'}), 400
        
        # Get message details
        from models import ChatMessage
        message = ChatMessage.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Trigger evaluation task
        from tasks.fine_tuning_tasks import evaluate_rag_response_task
        
        # For now, use dummy context - in real implementation, get from RAG service
        retrieved_contexts = data.get('retrieved_contexts', [])
        query = data.get('query', 'Manual evaluation')
        
        task = evaluate_rag_response_task.delay(
            message_id=message_id,
            query=query,
            retrieved_contexts=retrieved_contexts,
            response=message.content
        )
        
        return jsonify({
            'success': True,
            'task_id': task.id,
            'message': 'RAG evaluation started'
        })
        
    except Exception as e:
        logger.error(f"Error triggering RAG evaluation: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/ai-mastery/model-performance', methods=['GET'])
@token_required
def get_model_performance():
    """Get model performance metrics over time"""
    try:
        user = get_current_user()
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from models import ModelPerformanceTracking
        from datetime import timedelta
        
        days = request.args.get('days', 30, type=int)
        model_name = request.args.get('model_name', 'current_rag_pipeline')
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        performance_data = ModelPerformanceTracking.query.filter(
            ModelPerformanceTracking.model_name == model_name,
            ModelPerformanceTracking.evaluation_date >= cutoff_date
        ).order_by(ModelPerformanceTracking.evaluation_date.desc()).all()
        
        # Group by metric name
        metrics_by_name = {}
        for record in performance_data:
            metric_name = record.metric_name
            if metric_name not in metrics_by_name:
                metrics_by_name[metric_name] = []
            metrics_by_name[metric_name].append(record.to_dict())
        
        return jsonify({
            'success': True,
            'model_name': model_name,
            'period_days': days,
            'metrics': metrics_by_name,
            'total_records': len(performance_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/ai-mastery/trigger-weekly-improvement', methods=['POST'])
@token_required
def trigger_weekly_improvement():
    """Manually trigger weekly model improvement"""
    try:
        user = get_current_user()
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from tasks.fine_tuning_tasks import weekly_model_improvement_task
        
        task = weekly_model_improvement_task.delay()
        
        return jsonify({
            'success': True,
            'task_id': task.id,
            'message': 'Weekly model improvement started'
        })
        
    except Exception as e:
        logger.error(f"Error triggering weekly improvement: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/ai-mastery/dashboard', methods=['GET'])
@token_required
def get_ai_mastery_dashboard():
    """Get comprehensive AI mastery dashboard data"""
    try:
        user = get_current_user()
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from services.fine_tuning_service import fine_tuning_service
        from services.rag_evaluation_service import rag_evaluation_service
        from models import FineTuningJob, ModelPerformanceTracking
        
        days = request.args.get('days', 30, type=int)
        
        # Get feedback statistics
        feedback_stats = fine_tuning_service.get_feedback_statistics(days=days)
        
        # Get RAG evaluation statistics
        rag_stats = rag_evaluation_service.get_evaluation_statistics(days=days)
        
        # Get recent fine-tuning jobs
        recent_jobs = FineTuningJob.query.order_by(FineTuningJob.created_at.desc()).limit(5).all()
        
        # Get model performance trends
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        performance_records = ModelPerformanceTracking.query.filter(
            ModelPerformanceTracking.evaluation_date >= cutoff_date
        ).order_by(ModelPerformanceTracking.evaluation_date.desc()).limit(50).all()
        
        return jsonify({
            'success': True,
            'period_days': days,
            'feedback_statistics': feedback_stats,
            'rag_evaluation_statistics': rag_stats,
            'recent_fine_tuning_jobs': [job.to_dict() for job in recent_jobs],
            'model_performance_records': [record.to_dict() for record in performance_records],
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting AI mastery dashboard: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Advanced Interaction Paradigms API Routes

# Visualization API Routes
@app.route('/api/visualizations/generate', methods=['POST'])
@token_required
def generate_visualization():
    """Generate a visualization from data"""
    try:
        from services.visualization_service import visualization_service
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        chart_type = data.get('chart_type')
        chart_data = data.get('data')
        title = data.get('title')
        description = data.get('description')
        
        if not chart_type or not chart_data:
            return jsonify({'error': 'chart_type and data are required'}), 400
        
        result = visualization_service.create_visualization_tool_response(
            chart_type=chart_type,
            data=chart_data,
            title=title,
            description=description
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating visualization: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/visualizations/suggest', methods=['POST'])
@token_required
def suggest_visualizations():
    """Suggest appropriate visualizations for a query and data"""
    try:
        from services.visualization_service import visualization_service
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        query = data.get('query', '')
        chart_data = data.get('data')
        
        suggestions = visualization_service.suggest_visualization_for_query(query, chart_data)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        logger.error(f"Error suggesting visualizations: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/visualizations/tools', methods=['GET'])
@token_required
def get_visualization_tools():
    """Get available visualization tools for AI agents"""
    try:
        from services.visualization_service import visualization_service
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        tools = visualization_service.get_visualization_tools_for_agent()
        
        return jsonify({
            'success': True,
            'tools': tools
        })
        
    except Exception as e:
        logger.error(f"Error getting visualization tools: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Workspace API Routes
@app.route('/api/workspaces', methods=['GET'])
@token_required
def get_workspaces():
    """Get all workspaces for the current user"""
    try:
        from services.workspace_service import WorkspaceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        workspace_service = WorkspaceService()
        result = workspace_service.get_user_workspaces(user.id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting workspaces: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/workspaces', methods=['POST'])
@token_required
def create_workspace():
    """Create a new workspace"""
    try:
        from services.workspace_service import WorkspaceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        name = data.get('name')
        description = data.get('description')
        tags = data.get('tags', [])
        
        if not name:
            return jsonify({'error': 'Workspace name is required'}), 400
        
        workspace_service = WorkspaceService()
        result = workspace_service.create_workspace(
            user_id=user.id,
            name=name,
            description=description,
            tags=tags
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error creating workspace: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/workspaces/<int:workspace_id>', methods=['GET'])
@token_required
def get_workspace(workspace_id):
    """Get a specific workspace with its elements"""
    try:
        from services.workspace_service import WorkspaceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        workspace_service = WorkspaceService()
        result = workspace_service.get_workspace(
            workspace_id=workspace_id,
            user_id=user.id,
            include_elements=True
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting workspace: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/workspaces/<int:workspace_id>', methods=['PUT'])
@token_required
def update_workspace(workspace_id):
    """Update a workspace"""
    try:
        from services.workspace_service import WorkspaceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        workspace_service = WorkspaceService()
        result = workspace_service.update_workspace(
            workspace_id=workspace_id,
            user_id=user.id,
            updates=data
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error updating workspace: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/workspaces/<int:workspace_id>', methods=['DELETE'])
@token_required
def delete_workspace(workspace_id):
    """Delete a workspace"""
    try:
        from services.workspace_service import WorkspaceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        workspace_service = WorkspaceService()
        result = workspace_service.delete_workspace(
            workspace_id=workspace_id,
            user_id=user.id
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error deleting workspace: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/workspaces/<int:workspace_id>/elements', methods=['POST'])
@token_required
def add_workspace_element(workspace_id):
    """Add an element to a workspace"""
    try:
        from services.workspace_service import WorkspaceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        element_type = data.get('element_type')
        position = data.get('position')
        
        if not element_type or not position:
            return jsonify({'error': 'element_type and position are required'}), 400
        
        workspace_service = WorkspaceService()
        result = workspace_service.add_element(
            workspace_id=workspace_id,
            user_id=user.id,
            element_type=element_type,
            position=position,
            **{k: v for k, v in data.items() if k not in ['element_type', 'position']}
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error adding workspace element: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/workspaces/elements/<int:element_id>', methods=['PUT'])
@token_required
def update_workspace_element(element_id):
    """Update a workspace element"""
    try:
        from services.workspace_service import WorkspaceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        workspace_service = WorkspaceService()
        result = workspace_service.update_element(
            element_id=element_id,
            user_id=user.id,
            updates=data
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error updating workspace element: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/workspaces/elements/<int:element_id>', methods=['DELETE'])
@token_required
def delete_workspace_element(element_id):
    """Delete a workspace element"""
    try:
        from services.workspace_service import WorkspaceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        workspace_service = WorkspaceService()
        result = workspace_service.delete_element(
            element_id=element_id,
            user_id=user.id
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error deleting workspace element: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/workspaces/<int:workspace_id>/connections', methods=['POST'])
@token_required
def add_workspace_connection(workspace_id):
    """Add a connection between workspace elements"""
    try:
        from services.workspace_service import WorkspaceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        source_element_id = data.get('source_element_id')
        target_element_id = data.get('target_element_id')
        
        if not source_element_id or not target_element_id:
            return jsonify({'error': 'source_element_id and target_element_id are required'}), 400
        
        workspace_service = WorkspaceService()
        result = workspace_service.add_connection(
            workspace_id=workspace_id,
            user_id=user.id,
            source_element_id=source_element_id,
            target_element_id=target_element_id,
            **{k: v for k, v in data.items() if k not in ['source_element_id', 'target_element_id']}
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error adding workspace connection: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/workspaces/connections/<int:connection_id>', methods=['DELETE'])
@token_required
def delete_workspace_connection(connection_id):
    """Delete a workspace connection"""
    try:
        from services.workspace_service import WorkspaceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        workspace_service = WorkspaceService()
        result = workspace_service.delete_connection(
            connection_id=connection_id,
            user_id=user.id
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error deleting workspace connection: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/workspaces/<int:workspace_id>/chat-card', methods=['POST'])
@token_required
def create_chat_card(workspace_id):
    """Create a chat card from an existing chat session"""
    try:
        from services.workspace_service import WorkspaceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        chat_session_id = data.get('chat_session_id')
        position = data.get('position')
        
        if not chat_session_id or not position:
            return jsonify({'error': 'chat_session_id and position are required'}), 400
        
        workspace_service = WorkspaceService()
        result = workspace_service.create_chat_card_from_session(
            workspace_id=workspace_id,
            user_id=user.id,
            chat_session_id=chat_session_id,
            position=position
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error creating chat card: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/workspaces/<int:workspace_id>/note', methods=['POST'])
@token_required
def create_note_element(workspace_id):
    """Create a note element in a workspace"""
    try:
        from services.workspace_service import WorkspaceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        position = data.get('position')
        content = data.get('content', '')
        title = data.get('title')
        
        if not position:
            return jsonify({'error': 'position is required'}), 400
        
        workspace_service = WorkspaceService()
        result = workspace_service.create_note_element(
            workspace_id=workspace_id,
            user_id=user.id,
            position=position,
            content=content,
            title=title
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error creating note element: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/workspaces/<int:workspace_id>/share', methods=['POST'])
@token_required
def share_workspace(workspace_id):
    """Share a workspace"""
    try:
        from services.workspace_service import WorkspaceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        workspace_service = WorkspaceService()
        result = workspace_service.share_workspace(
            workspace_id=workspace_id,
            user_id=user.id
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error sharing workspace: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/workspaces/<int:workspace_id>/unshare', methods=['POST'])
@token_required
def unshare_workspace(workspace_id):
    """Remove sharing from a workspace"""
    try:
        from services.workspace_service import WorkspaceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        workspace_service = WorkspaceService()
        result = workspace_service.unshare_workspace(
            workspace_id=workspace_id,
            user_id=user.id
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error unsharing workspace: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/workspaces/shared/<share_token>', methods=['GET'])
def get_shared_workspace(share_token):
    """Get a shared workspace by token (no authentication required)"""
    try:
        from services.workspace_service import WorkspaceService
        
        workspace_service = WorkspaceService()
        result = workspace_service.get_shared_workspace(share_token)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting shared workspace: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/workspaces/<int:workspace_id>/duplicate', methods=['POST'])
@token_required
def duplicate_workspace(workspace_id):
    """Duplicate a workspace"""
    try:
        from services.workspace_service import WorkspaceService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json() or {}
        new_name = data.get('name')
        
        workspace_service = WorkspaceService()
        result = workspace_service.duplicate_workspace(
            workspace_id=workspace_id,
            user_id=user.id,
            new_name=new_name
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error duplicating workspace: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Multi-Modal Document Processing API Routes
@app.route('/api/documents/upload', methods=['POST'])
@token_required
def upload_document(current_user_id):
    """Upload and process a document with multi-modal capabilities"""
    try:
        from services.document_processing_api import document_processing_api
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Get processing options from form data
        processing_options = {}
        if 'processing_options' in request.form:
            try:
                processing_options = json.loads(request.form['processing_options'])
            except json.JSONDecodeError:
                pass
        
        # Read file data
        file_data = file.read()
        filename = file.filename
        
        # Process document
        result = document_processing_api.upload_document(
            user_id=current_user_id,
            file_data=file_data,
            filename=filename,
            processing_options=processing_options
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/documents', methods=['GET'])
@token_required
def list_documents(current_user_id):
    """List user's processed documents"""
    try:
        from services.document_processing_api import document_processing_api
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        file_type = request.args.get('file_type')
        
        result = document_processing_api.list_documents(
            user_id=current_user_id,
            page=page,
            per_page=per_page,
            file_type=file_type
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/documents/<document_id>', methods=['GET'])
@token_required
def get_document(current_user_id, document_id):
    """Get a specific processed document"""
    try:
        from services.document_processing_api import document_processing_api
        
        include_elements = request.args.get('include_elements', 'false').lower() == 'true'
        
        result = document_processing_api.get_document(
            user_id=current_user_id,
            document_id=document_id,
            include_elements=include_elements
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/documents/<document_id>', methods=['DELETE'])
@token_required
def delete_document(current_user_id, document_id):
    """Delete a processed document"""
    try:
        from services.document_processing_api import document_processing_api
        
        result = document_processing_api.delete_document(
            user_id=current_user_id,
            document_id=document_id
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/documents/search', methods=['POST'])
@token_required
def search_documents(current_user_id):
    """Search through processed documents"""
    try:
        from services.document_processing_api import document_processing_api
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No search data provided'}), 400
        
        query = data.get('query', '')
        element_types = data.get('element_types')
        min_confidence = data.get('min_confidence', 0.0)
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query is required'}), 400
        
        result = document_processing_api.search_documents(
            user_id=current_user_id,
            query=query,
            element_types=element_types,
            min_confidence=min_confidence
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/documents/process-image', methods=['POST'])
@token_required
def process_image_base64(current_user_id):
    """Process image from base64 data"""
    try:
        from services.document_processing_api import document_processing_api
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No image data provided'}), 400
        
        image_data = data.get('image_data')
        filename = data.get('filename', 'image.png')
        
        if not image_data:
            return jsonify({'success': False, 'error': 'Image data is required'}), 400
        
        result = document_processing_api.process_image_from_base64(
            user_id=current_user_id,
            image_data=image_data,
            filename=filename
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/documents/stats', methods=['GET'])
@token_required
def get_document_processing_stats(current_user_id):
    """Get document processing statistics"""
    try:
        from services.document_processing_api import document_processing_api
        
        # Admin can see global stats, users see only their own
        user = User.query.get(current_user_id)
        if user and user.is_admin:
            result = document_processing_api.get_processing_stats()
        else:
            result = document_processing_api.get_processing_stats(user_id=current_user_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting processing stats: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/documents/capabilities', methods=['GET'])
def get_processing_capabilities():
    """Get available processing capabilities"""
    try:
        from services.multimodal_document_processor import multimodal_processor
        
        stats = multimodal_processor.get_stats()
        capabilities = stats.get('capabilities', {})
        
        return jsonify({
            'success': True,
            'capabilities': capabilities,
            'supported_formats': {
                'images': ['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif'],
                'documents': ['pdf', 'txt', 'md', 'docx', 'doc', 'html', 'htm'],
                'max_file_size_mb': 50
            },
            'features': {
                'ocr_text_extraction': capabilities.get('ocr_available', False),
                'image_captioning': capabilities.get('vision_models_available', False),
                'table_extraction': capabilities.get('table_extraction_available', False),
                'layout_analysis': capabilities.get('layout_analysis_available', False),
                'pdf_processing': capabilities.get('pdf_processing_available', False)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# Enhanced RAG endpoints with multi-modal support
@app.route('/api/rag/ingest-document', methods=['POST'])
@token_required
def rag_ingest_document(current_user_id):
    """Ingest a document into the RAG system with multi-modal processing"""
    try:
        from services.rag_service import rag_service
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Save file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            file.save(tmp_file.name)
            
            # Ingest with metadata
            metadata = {
                'user_id': current_user_id,
                'filename': file.filename,
                'ingested_via': 'api',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            success = rag_service.ingest_file(tmp_file.name, metadata)
            
            # Clean up
            os.unlink(tmp_file.name)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Document ingested successfully into RAG system'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to ingest document'
            }), 500
        
    except Exception as e:
        logger.error(f"Error ingesting document to RAG: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/rag/search', methods=['POST'])
@token_required
def rag_search_documents(current_user_id):
    """Search RAG system for relevant documents"""
    try:
        from services.rag_service import rag_service
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No search data provided'}), 400
        
        query = data.get('query', '')
        n_results = data.get('n_results', 5)
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query is required'}), 400
        
        results = rag_service.search_documents(query, n_results)
        
        return jsonify({
            'success': True,
            'query': query,
            'results': [
                {
                    'content': result.document.content,
                    'metadata': result.document.metadata,
                    'score': result.score,
                    'rank': result.rank
                }
                for result in results
            ],
            'total_results': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error searching RAG: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/rag/generate-response', methods=['POST'])
@token_required
def rag_generate_response(current_user_id):
    """Generate RAG-enhanced response"""
    try:
        from services.rag_service import rag_service
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No query data provided'}), 400
        
        query = data.get('query', '')
        model_name = data.get('model', DEFAULT_MODEL)
        max_sources = data.get('max_sources', 5)
        
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400
        
        rag_response = rag_service.generate_rag_response(
            query=query,
            model_name=model_name,
            max_sources=max_sources
        )
        
        return jsonify({
            'success': True,
            'answer': rag_response.answer,
            'sources': [
                {
                    'content': source.document.content,
                    'metadata': source.document.metadata,
                    'score': source.score,
                    'rank': source.rank
                }
                for source in rag_response.sources
            ],
            'confidence': rag_response.confidence,
            'model_used': rag_response.model_used,
            'retrieval_time': rag_response.retrieval_time,
            'generation_time': rag_response.generation_time,
            'context_used_length': len(rag_response.context_used)
        })
        
    except Exception as e:
        logger.error(f"Error generating RAG response: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/rag/stats', methods=['GET'])
@token_required
def get_rag_stats(current_user_id):
    """Get RAG system statistics"""
    try:
        from services.rag_service import rag_service
        
        stats = rag_service.get_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting RAG stats: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# OAuth Routes for External Data Sources
@app.route('/api/oauth/<source_type>/authorize', methods=['GET'])
@token_required
def oauth_authorize(source_type):
    """Start OAuth flow for external data source"""
    try:
        from services.automated_sync_service import AutomatedSyncService
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Build redirect URI
        redirect_uri = f"{request.host_url}api/oauth/{source_type}/callback"
        
        sync_service = AutomatedSyncService()
        flow = sync_service.get_oauth_flow(source_type, redirect_uri)
        
        if not flow:
            return jsonify({'error': f'OAuth not supported for {source_type}'}), 400
        
        # Store user ID in session for callback
        session['oauth_user_id'] = user.id
        session['oauth_source_type'] = source_type
        
        # Get authorization URL
        auth_url, state = flow.authorization_url(prompt='consent')
        session['oauth_state'] = state
        
        return jsonify({
            'success': True,
            'auth_url': auth_url
        })
        
    except Exception as e:
        logger.error(f"Error starting OAuth flow: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/oauth/<source_type>/callback', methods=['GET'])
def oauth_callback(source_type):
    """Handle OAuth callback for external data source"""
    try:
        from services.automated_sync_service import AutomatedSyncService
        
        # Get user ID from session
        user_id = session.get('oauth_user_id')
        if not user_id:
            return jsonify({'error': 'OAuth session expired'}), 400
        
        # Verify state parameter
        state = request.args.get('state')
        if state != session.get('oauth_state'):
            return jsonify({'error': 'Invalid OAuth state'}), 400
        
        # Get authorization code
        code = request.args.get('code')
        if not code:
            return jsonify({'error': 'Authorization code not provided'}), 400
        
        # Build redirect URI
        redirect_uri = f"{request.host_url}api/oauth/{source_type}/callback"
        
        sync_service = AutomatedSyncService()
        flow = sync_service.get_oauth_flow(source_type, redirect_uri)
        
        if not flow:
            return jsonify({'error': f'OAuth not supported for {source_type}'}), 400
        
        # Exchange code for tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Create data source
        source_name = f"{source_type.title()} - {datetime.utcnow().strftime('%Y-%m-%d')}"
        
        result = sync_service.create_data_source(
            user_id=user_id,
            source_type=source_type,
            source_name=source_name,
            oauth_credentials={
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'expires_at': credentials.expiry
            },
            connection_config={}
        )
        
        # Clear session
        session.pop('oauth_user_id', None)
        session.pop('oauth_source_type', None)
        session.pop('oauth_state', None)
        
        if result['success']:
            # Redirect to success page
            return redirect(f"{request.host_url}#/data-sources?success=true")
        else:
            return redirect(f"{request.host_url}#/data-sources?error={result['error']}")
        
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        return redirect(f"{request.host_url}#/data-sources?error=oauth_failed")

if __name__ == '__main__':
    print("🚀 Starting AI Chatbot Web Application - Enterprise Edition...")
    print(f"🤖 Ollama URL: {OLLAMA_BASE_URL}")
    print(f"🧠 Default Model: {DEFAULT_MODEL}")
    print(f"💾 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("🌐 Server will be available at: http://localhost:5000")
    print("👥 Real-time collaboration enabled")
    print("📊 Admin dashboard available at: /api/admin/*")
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created successfully")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
    
    # Run with SocketIO support
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)