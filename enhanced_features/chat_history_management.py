#!/usr/bin/env python3
"""
Advanced Chat History Management
Comprehensive chat session management with search, organization, and analytics
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import or_, func, desc, asc
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import re
from models import ChatSession, ChatMessage, User, db
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Create blueprint for chat history management
chat_history_bp = Blueprint('chat_history', __name__)

class ChatHistoryManager:
    """Advanced chat history management with search and analytics"""
    
    def __init__(self):
        self.search_cache = {}
        self.analytics_cache = {}
        
    def get_user_sessions(self, user_id: int, page: int = 1, per_page: int = 20, 
                         sort_by: str = 'updated_at', sort_order: str = 'desc',
                         search_query: str = None, date_filter: str = None) -> Dict:
        """Get user's chat sessions with advanced filtering and pagination"""
        try:
            # Base query
            query = ChatSession.query.filter_by(user_id=user_id)
            
            # Apply search filter
            if search_query:
                search_pattern = f"%{search_query}%"
                query = query.filter(
                    or_(
                        ChatSession.session_name.ilike(search_pattern),
                        ChatSession.id.in_(
                            db.session.query(ChatMessage.session_id)
                            .filter(ChatMessage.content.ilike(search_pattern))
                            .distinct()
                        )
                    )
                )
            
            # Apply date filter
            if date_filter:
                if date_filter == 'today':
                    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    query = query.filter(ChatSession.updated_at >= start_date)
                elif date_filter == 'week':
                    start_date = datetime.now() - timedelta(days=7)
                    query = query.filter(ChatSession.updated_at >= start_date)
                elif date_filter == 'month':
                    start_date = datetime.now() - timedelta(days=30)
                    query = query.filter(ChatSession.updated_at >= start_date)
                elif date_filter == 'year':
                    start_date = datetime.now() - timedelta(days=365)
                    query = query.filter(ChatSession.updated_at >= start_date)
            
            # Apply sorting
            sort_column = getattr(ChatSession, sort_by, ChatSession.updated_at)
            if sort_order == 'desc':
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination
            sessions = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Enhance sessions with additional data
            enhanced_sessions = []
            for session in sessions:
                session_data = session.to_dict()
                
                # Add message count
                message_count = ChatMessage.query.filter_by(session_id=session.id).count()
                session_data['message_count'] = message_count
                
                # Add last message preview
                last_message = ChatMessage.query.filter_by(session_id=session.id)\
                                               .order_by(desc(ChatMessage.timestamp))\
                                               .first()
                if last_message:
                    session_data['last_message'] = {
                        'content': last_message.content[:100] + '...' if len(last_message.content) > 100 else last_message.content,
                        'timestamp': last_message.timestamp.isoformat(),
                        'type': last_message.message_type
                    }
                
                # Add session statistics
                session_stats = self._get_session_statistics(session.id)
                session_data['statistics'] = session_stats
                
                enhanced_sessions.append(session_data)
            
            return {
                'sessions': enhanced_sessions,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': (total_count + per_page - 1) // per_page
                },
                'filters': {
                    'search_query': search_query,
                    'date_filter': date_filter,
                    'sort_by': sort_by,
                    'sort_order': sort_order
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return {'sessions': [], 'pagination': {}, 'filters': {}}
    
    def _get_session_statistics(self, session_id: int) -> Dict:
        """Get detailed statistics for a chat session"""
        try:
            messages = ChatMessage.query.filter_by(session_id=session_id).all()
            
            if not messages:
                return {}
            
            user_messages = [m for m in messages if m.message_type == 'user']
            bot_messages = [m for m in messages if m.message_type == 'bot']
            
            # Calculate session duration
            first_message = min(messages, key=lambda m: m.timestamp)
            last_message = max(messages, key=lambda m: m.timestamp)
            duration = (last_message.timestamp - first_message.timestamp).total_seconds()
            
            # Calculate average response time
            response_times = []
            for i in range(len(user_messages)):
                user_msg = user_messages[i]
                # Find the next bot message after this user message
                next_bot_msg = next(
                    (m for m in bot_messages if m.timestamp > user_msg.timestamp),
                    None
                )
                if next_bot_msg:
                    response_time = (next_bot_msg.timestamp - user_msg.timestamp).total_seconds()
                    response_times.append(response_time)
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Calculate word counts
            user_word_count = sum(len(m.content.split()) for m in user_messages)
            bot_word_count = sum(len(m.content.split()) for m in bot_messages)
            
            # Extract models used
            models_used = list(set(m.model_used for m in bot_messages if m.model_used))
            
            return {
                'total_messages': len(messages),
                'user_messages': len(user_messages),
                'bot_messages': len(bot_messages),
                'duration_seconds': duration,
                'avg_response_time': avg_response_time,
                'user_word_count': user_word_count,
                'bot_word_count': bot_word_count,
                'models_used': models_used,
                'first_message_time': first_message.timestamp.isoformat(),
                'last_message_time': last_message.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating session statistics: {e}")
            return {}
    
    def search_chat_history(self, user_id: int, query: str, 
                           search_type: str = 'content', limit: int = 50) -> List[Dict]:
        """Advanced search through chat history"""
        try:
            results = []
            
            if search_type == 'content':
                # Search in message content
                messages = ChatMessage.query.join(ChatSession)\
                                          .filter(ChatSession.user_id == user_id)\
                                          .filter(ChatMessage.content.ilike(f"%{query}%"))\
                                          .order_by(desc(ChatMessage.timestamp))\
                                          .limit(limit).all()
                
                for message in messages:
                    # Highlight search terms
                    highlighted_content = self._highlight_search_terms(message.content, query)
                    
                    results.append({
                        'type': 'message',
                        'message_id': message.id,
                        'session_id': message.session_id,
                        'content': highlighted_content,
                        'original_content': message.content,
                        'message_type': message.message_type,
                        'timestamp': message.timestamp.isoformat(),
                        'model_used': message.model_used,
                        'session_name': message.session.session_name if message.session else 'Unknown'
                    })
            
            elif search_type == 'sessions':
                # Search in session names
                sessions = ChatSession.query.filter_by(user_id=user_id)\
                                          .filter(ChatSession.session_name.ilike(f"%{query}%"))\
                                          .order_by(desc(ChatSession.updated_at))\
                                          .limit(limit).all()
                
                for session in sessions:
                    results.append({
                        'type': 'session',
                        'session_id': session.id,
                        'session_name': session.session_name,
                        'created_at': session.created_at.isoformat(),
                        'updated_at': session.updated_at.isoformat(),
                        'message_count': ChatMessage.query.filter_by(session_id=session.id).count()
                    })
            
            elif search_type == 'semantic':
                # Semantic search (would require embeddings)
                # For now, implement enhanced keyword matching
                results = self._semantic_search(user_id, query, limit)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching chat history: {e}")
            return []
    
    def _highlight_search_terms(self, content: str, query: str) -> str:
        """Highlight search terms in content"""
        # Simple highlighting - in production, use more sophisticated highlighting
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        return pattern.sub(f'<mark>{query}</mark>', content)
    
    def _semantic_search(self, user_id: int, query: str, limit: int) -> List[Dict]:
        """Semantic search using keyword expansion and relevance scoring"""
        # This is a simplified semantic search
        # In production, you'd use embeddings and vector similarity
        
        # Expand query with synonyms and related terms
        expanded_terms = self._expand_query_terms(query)
        
        results = []
        for term in expanded_terms:
            messages = ChatMessage.query.join(ChatSession)\
                                      .filter(ChatSession.user_id == user_id)\
                                      .filter(ChatMessage.content.ilike(f"%{term}%"))\
                                      .limit(limit // len(expanded_terms)).all()
            
            for message in messages:
                relevance_score = self._calculate_relevance_score(message.content, query, expanded_terms)
                
                results.append({
                    'type': 'semantic_message',
                    'message_id': message.id,
                    'session_id': message.session_id,
                    'content': message.content[:200] + '...' if len(message.content) > 200 else message.content,
                    'relevance_score': relevance_score,
                    'timestamp': message.timestamp.isoformat(),
                    'session_name': message.session.session_name if message.session else 'Unknown'
                })
        
        # Sort by relevance score
        results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return results[:limit]
    
    def _expand_query_terms(self, query: str) -> List[str]:
        """Expand query with related terms"""
        # Simple term expansion - in production, use word embeddings or thesaurus
        expansions = {
            'machine learning': ['ML', 'artificial intelligence', 'AI', 'deep learning'],
            'programming': ['coding', 'development', 'software'],
            'python': ['py', 'programming', 'code'],
            'data science': ['analytics', 'data analysis', 'statistics']
        }
        
        terms = [query.lower()]
        for key, values in expansions.items():
            if key in query.lower():
                terms.extend(values)
        
        return list(set(terms))
    
    def _calculate_relevance_score(self, content: str, query: str, expanded_terms: List[str]) -> float:
        """Calculate relevance score for semantic search"""
        content_lower = content.lower()
        query_lower = query.lower()
        
        score = 0.0
        
        # Exact query match
        if query_lower in content_lower:
            score += 1.0
        
        # Individual term matches
        query_words = query_lower.split()
        for word in query_words:
            if word in content_lower:
                score += 0.5
        
        # Expanded term matches
        for term in expanded_terms:
            if term.lower() in content_lower:
                score += 0.3
        
        # Length penalty (prefer shorter, more relevant content)
        length_penalty = min(len(content) / 1000, 0.5)
        score -= length_penalty
        
        return max(score, 0.0)
    
    def update_session_name(self, session_id: int, user_id: int, new_name: str) -> bool:
        """Update session name"""
        try:
            session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
            if session:
                session.session_name = new_name
                session.updated_at = datetime.utcnow()
                db.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating session name: {e}")
            db.session.rollback()
            return False
    
    def delete_session(self, session_id: int, user_id: int) -> bool:
        """Delete a chat session and all its messages"""
        try:
            session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
            if session:
                # Delete all messages in the session
                ChatMessage.query.filter_by(session_id=session_id).delete()
                
                # Delete the session
                db.session.delete(session)
                db.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            db.session.rollback()
            return False
    
    def bulk_delete_sessions(self, session_ids: List[int], user_id: int) -> Dict:
        """Delete multiple sessions"""
        try:
            deleted_count = 0
            failed_count = 0
            
            for session_id in session_ids:
                if self.delete_session(session_id, user_id):
                    deleted_count += 1
                else:
                    failed_count += 1
            
            return {
                'deleted': deleted_count,
                'failed': failed_count,
                'total': len(session_ids)
            }
        except Exception as e:
            logger.error(f"Error in bulk delete: {e}")
            return {'deleted': 0, 'failed': len(session_ids), 'total': len(session_ids)}
    
    def export_session(self, session_id: int, user_id: int, format_type: str = 'json') -> Dict:
        """Export session data in various formats"""
        try:
            session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
            if not session:
                return {'error': 'Session not found'}
            
            messages = ChatMessage.query.filter_by(session_id=session_id)\
                                       .order_by(ChatMessage.timestamp).all()
            
            export_data = {
                'session': session.to_dict(),
                'messages': [msg.to_dict() for msg in messages],
                'statistics': self._get_session_statistics(session_id),
                'exported_at': datetime.utcnow().isoformat()
            }
            
            if format_type == 'markdown':
                return self._export_as_markdown(export_data)
            elif format_type == 'txt':
                return self._export_as_text(export_data)
            else:
                return export_data
                
        except Exception as e:
            logger.error(f"Error exporting session: {e}")
            return {'error': str(e)}
    
    def _export_as_markdown(self, data: Dict) -> str:
        """Export session as markdown"""
        session = data['session']
        messages = data['messages']
        
        markdown = f"# {session['session_name']}\n\n"
        markdown += f"**Created:** {session['created_at']}\n"
        markdown += f"**Updated:** {session['updated_at']}\n\n"
        
        for message in messages:
            role = "**User:**" if message['message_type'] == 'user' else "**AI:**"
            markdown += f"{role} {message['content']}\n\n"
        
        return markdown
    
    def _export_as_text(self, data: Dict) -> str:
        """Export session as plain text"""
        session = data['session']
        messages = data['messages']
        
        text = f"{session['session_name']}\n"
        text += f"Created: {session['created_at']}\n"
        text += f"Updated: {session['updated_at']}\n\n"
        
        for message in messages:
            role = "User:" if message['message_type'] == 'user' else "AI:"
            text += f"{role} {message['content']}\n\n"
        
        return text
    
    def get_user_analytics(self, user_id: int, period: str = 'month') -> Dict:
        """Get comprehensive analytics for user's chat history"""
        try:
            # Define date range
            if period == 'week':
                start_date = datetime.now() - timedelta(days=7)
            elif period == 'month':
                start_date = datetime.now() - timedelta(days=30)
            elif period == 'year':
                start_date = datetime.now() - timedelta(days=365)
            else:
                start_date = datetime.now() - timedelta(days=30)
            
            # Get sessions in period
            sessions = ChatSession.query.filter_by(user_id=user_id)\
                                       .filter(ChatSession.created_at >= start_date).all()
            
            # Get messages in period
            session_ids = [s.id for s in sessions]
            messages = ChatMessage.query.filter(ChatMessage.session_id.in_(session_ids)).all()
            
            # Calculate analytics
            analytics = {
                'period': period,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': datetime.now().isoformat()
                },
                'sessions': {
                    'total': len(sessions),
                    'avg_per_day': len(sessions) / (datetime.now() - start_date).days if (datetime.now() - start_date).days > 0 else 0
                },
                'messages': {
                    'total': len(messages),
                    'user_messages': len([m for m in messages if m.message_type == 'user']),
                    'bot_messages': len([m for m in messages if m.message_type == 'bot']),
                    'avg_per_session': len(messages) / len(sessions) if sessions else 0
                },
                'usage_patterns': self._analyze_usage_patterns(messages),
                'popular_topics': self._extract_popular_topics(messages),
                'model_usage': self._analyze_model_usage(messages),
                'response_times': self._analyze_response_times(messages)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            return {}
    
    def _analyze_usage_patterns(self, messages: List) -> Dict:
        """Analyze usage patterns by time of day and day of week"""
        if not messages:
            return {}
        
        hour_counts = {}
        day_counts = {}
        
        for message in messages:
            if message.message_type == 'user':  # Only count user messages for activity
                hour = message.timestamp.hour
                day = message.timestamp.strftime('%A')
                
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
                day_counts[day] = day_counts.get(day, 0) + 1
        
        return {
            'by_hour': hour_counts,
            'by_day': day_counts,
            'most_active_hour': max(hour_counts, key=hour_counts.get) if hour_counts else None,
            'most_active_day': max(day_counts, key=day_counts.get) if day_counts else None
        }
    
    def _extract_popular_topics(self, messages: List) -> List[Dict]:
        """Extract popular topics from message content"""
        # Simple keyword extraction - in production, use NLP
        word_counts = {}
        
        for message in messages:
            if message.message_type == 'user':
                words = re.findall(r'\b\w+\b', message.content.lower())
                for word in words:
                    if len(word) > 3:  # Ignore short words
                        word_counts[word] = word_counts.get(word, 0) + 1
        
        # Get top topics
        sorted_topics = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [{'topic': topic, 'count': count} for topic, count in sorted_topics[:10]]
    
    def _analyze_model_usage(self, messages: List) -> Dict:
        """Analyze which models are used most frequently"""
        model_counts = {}
        
        for message in messages:
            if message.message_type == 'bot' and message.model_used:
                model = message.model_used
                model_counts[model] = model_counts.get(model, 0) + 1
        
        return {
            'model_counts': model_counts,
            'most_used_model': max(model_counts, key=model_counts.get) if model_counts else None,
            'total_models_used': len(model_counts)
        }
    
    def _analyze_response_times(self, messages: List) -> Dict:
        """Analyze AI response times"""
        response_times = []
        
        user_messages = [m for m in messages if m.message_type == 'user']
        bot_messages = [m for m in messages if m.message_type == 'bot']
        
        for user_msg in user_messages:
            # Find the next bot message
            next_bot_msg = next(
                (m for m in bot_messages if m.timestamp > user_msg.timestamp),
                None
            )
            if next_bot_msg:
                response_time = (next_bot_msg.timestamp - user_msg.timestamp).total_seconds()
                response_times.append(response_time)
        
        if response_times:
            return {
                'avg_response_time': sum(response_times) / len(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'total_responses': len(response_times)
            }
        
        return {}

# Initialize history manager
history_manager = ChatHistoryManager()

# API Routes
@chat_history_bp.route('/api/chat/sessions', methods=['GET'])
def get_chat_sessions():
    """Get user's chat sessions with filtering and pagination"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        sort_by = request.args.get('sort_by', 'updated_at')
        sort_order = request.args.get('sort_order', 'desc')
        search_query = request.args.get('search')
        date_filter = request.args.get('date_filter')
        
        # Get user ID from token (implement your auth logic)
        user_id = 1  # Replace with actual user ID from JWT token
        
        result = history_manager.get_user_sessions(
            user_id=user_id,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search_query=search_query,
            date_filter=date_filter
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting chat sessions: {e}")
        return jsonify({'error': str(e)}), 500

@chat_history_bp.route('/api/chat/sessions/<int:session_id>', methods=['PUT'])
def update_session_name(session_id):
    """Update session name"""
    try:
        data = request.get_json()
        new_name = data.get('session_name', '').strip()
        
        if not new_name:
            return jsonify({'error': 'Session name cannot be empty'}), 400
        
        user_id = 1  # Replace with actual user ID from JWT token
        
        success = history_manager.update_session_name(session_id, user_id, new_name)
        
        if success:
            return jsonify({'message': 'Session name updated successfully'})
        else:
            return jsonify({'error': 'Session not found or update failed'}), 404
            
    except Exception as e:
        logger.error(f"Error updating session name: {e}")
        return jsonify({'error': str(e)}), 500

@chat_history_bp.route('/api/chat/sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a chat session"""
    try:
        user_id = 1  # Replace with actual user ID from JWT token
        
        success = history_manager.delete_session(session_id, user_id)
        
        if success:
            return jsonify({'message': 'Session deleted successfully'})
        else:
            return jsonify({'error': 'Session not found or deletion failed'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        return jsonify({'error': str(e)}), 500

@chat_history_bp.route('/api/chat/sessions/bulk-delete', methods=['POST'])
def bulk_delete_sessions():
    """Delete multiple sessions"""
    try:
        data = request.get_json()
        session_ids = data.get('session_ids', [])
        
        if not session_ids:
            return jsonify({'error': 'No session IDs provided'}), 400
        
        user_id = 1  # Replace with actual user ID from JWT token
        
        result = history_manager.bulk_delete_sessions(session_ids, user_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in bulk delete: {e}")
        return jsonify({'error': str(e)}), 500

@chat_history_bp.route('/api/chat/search', methods=['GET'])
def search_chat_history():
    """Search through chat history"""
    try:
        query = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'content')
        limit = int(request.args.get('limit', 50))
        
        if not query:
            return jsonify({'error': 'Search query cannot be empty'}), 400
        
        user_id = 1  # Replace with actual user ID from JWT token
        
        results = history_manager.search_chat_history(
            user_id=user_id,
            query=query,
            search_type=search_type,
            limit=limit
        )
        
        return jsonify({
            'query': query,
            'search_type': search_type,
            'results': results,
            'total_results': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error searching chat history: {e}")
        return jsonify({'error': str(e)}), 500

@chat_history_bp.route('/api/chat/sessions/<int:session_id>/export', methods=['GET'])
def export_session(session_id):
    """Export session data"""
    try:
        format_type = request.args.get('format', 'json')
        user_id = 1  # Replace with actual user ID from JWT token
        
        result = history_manager.export_session(session_id, user_id, format_type)
        
        if 'error' in result:
            return jsonify(result), 404
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error exporting session: {e}")
        return jsonify({'error': str(e)}), 500

@chat_history_bp.route('/api/chat/analytics', methods=['GET'])
def get_chat_analytics():
    """Get user's chat analytics"""
    try:
        period = request.args.get('period', 'month')
        user_id = 1  # Replace with actual user ID from JWT token
        
        analytics = history_manager.get_user_analytics(user_id, period)
        
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return jsonify({'error': str(e)}), 500

# Setup function
def setup_chat_history_management(app):
    """Setup chat history management with the app"""
    app.register_blueprint(chat_history_bp)
    
    print("✅ Advanced Chat History Management enabled:")
    print("  📋 Sessions: GET /api/chat/sessions")
    print("  ✏️  Update: PUT /api/chat/sessions/<id>")
    print("  🗑️  Delete: DELETE /api/chat/sessions/<id>")
    print("  🔍 Search: GET /api/chat/search")
    print("  📊 Analytics: GET /api/chat/analytics")
    print("  📤 Export: GET /api/chat/sessions/<id>/export")