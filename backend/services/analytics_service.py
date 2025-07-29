"""
Enhanced Analytics Service for comprehensive tracking and insights
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from sqlalchemy.sql import text

from core.database import (
    get_db, AnalyticsEvent, User, Document, Message, Conversation,
    UserProfile, DocumentTag, UserFeedback, KnowledgeGraphEntity,
    KnowledgeGraphRelationship, ConversationMemory
)
from core.redis_client import get_redis_client
from models.schemas import AnalyticsEventCreate, AnalyticsEventResponse

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    """Standard event types for analytics tracking"""
    QUERY_EXECUTED = "query_executed"
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_ACCESSED = "document_accessed"
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_ENDED = "conversation_ended"
    FEEDBACK_PROVIDED = "feedback_provided"
    SEARCH_PERFORMED = "search_performed"
    KNOWLEDGE_GRAPH_QUERIED = "knowledge_graph_queried"
    REASONING_APPLIED = "reasoning_applied"
    MEMORY_ACCESSED = "memory_accessed"
    PERSONALIZATION_APPLIED = "personalization_applied"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_METRIC = "performance_metric"
    USER_SESSION_START = "user_session_start"
    USER_SESSION_END = "user_session_end"

@dataclass
class QueryMetrics:
    """Query performance and frequency metrics"""
    total_queries: int
    avg_response_time: float
    success_rate: float
    most_common_queries: List[Tuple[str, int]]
    query_complexity_distribution: Dict[str, int]
    peak_usage_hours: List[int]

@dataclass
class DocumentMetrics:
    """Document usage and popularity metrics"""
    total_documents: int
    most_accessed_documents: List[Tuple[str, str, int]]  # (id, name, access_count)
    document_type_distribution: Dict[str, int]
    avg_document_size: float
    upload_trends: Dict[str, int]  # date -> count
    tag_popularity: Dict[str, int]

@dataclass
class UserBehaviorMetrics:
    """User interaction and behavior metrics"""
    active_users: int
    avg_session_duration: float
    user_retention_rate: float
    feature_usage: Dict[str, int]
    satisfaction_scores: Dict[str, float]
    domain_preferences: Dict[str, int]

@dataclass
class PerformanceMetrics:
    """System performance metrics"""
    avg_response_time: float
    error_rate: float
    throughput: float
    memory_usage: Dict[str, float]
    cache_hit_rate: float
    database_query_performance: Dict[str, float]

@dataclass
class AnalyticsInsights:
    """Comprehensive analytics insights"""
    query_metrics: QueryMetrics
    document_metrics: DocumentMetrics
    user_behavior: UserBehaviorMetrics
    performance: PerformanceMetrics
    trends: Dict[str, Any]
    recommendations: List[str]

class EnhancedAnalyticsService:
    """Enhanced analytics service with comprehensive tracking and insights"""
    
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = get_redis_client()
        self.real_time_buffer = defaultdict(list)
        
    async def track_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Track an analytics event with real-time buffering"""
        try:
            # Create analytics event
            event = AnalyticsEvent(
                user_id=user_id,
                event_type=event_type,
                event_data=event_data or {},
                session_id=session_id,
                timestamp=datetime.utcnow()
            )
            
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            
            # Add to real-time buffer for immediate analytics
            await self._buffer_real_time_event(event)
            
            logger.info(f"Tracked analytics event: {event_type} for user {user_id}")
            return event.id
            
        except Exception as e:
            logger.error(f"Error tracking analytics event: {str(e)}")
            self.db.rollback()
            raise

    async def _buffer_real_time_event(self, event: AnalyticsEvent):
        """Buffer event for real-time analytics processing"""
        try:
            if self.redis_client:
                # Store in Redis for real-time analytics
                buffer_key = f"analytics_buffer:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
                event_data = {
                    "id": event.id,
                    "user_id": event.user_id,
                    "event_type": event.event_type,
                    "event_data": event.event_data,
                    "timestamp": event.timestamp.isoformat(),
                    "session_id": event.session_id
                }
                
                await self.redis_client.lpush(buffer_key, json.dumps(event_data))
                await self.redis_client.expire(buffer_key, 86400)  # 24 hours
                
        except Exception as e:
            logger.warning(f"Failed to buffer real-time event: {str(e)}")

    async def get_query_metrics(
        self,
        user_id: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> QueryMetrics:
        """Get comprehensive query metrics"""
        try:
            # Default to last 30 days if no time range specified
            if not time_range:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                time_range = (start_date, end_date)
            
            # Base query for query events
            query_events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.event_type == EventType.QUERY_EXECUTED,
                AnalyticsEvent.timestamp.between(time_range[0], time_range[1])
            )
            
            if user_id:
                query_events = query_events.filter(AnalyticsEvent.user_id == user_id)
            
            events = query_events.all()
            
            # Calculate metrics
            total_queries = len(events)
            
            # Response time metrics
            response_times = [
                event.event_data.get('response_time', 0) 
                for event in events 
                if event.event_data.get('response_time')
            ]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Success rate
            successful_queries = sum(
                1 for event in events 
                if event.event_data.get('success', True)
            )
            success_rate = successful_queries / total_queries if total_queries > 0 else 0
            
            # Most common queries
            query_texts = [
                event.event_data.get('query', '').lower().strip()
                for event in events
                if event.event_data.get('query')
            ]
            most_common_queries = Counter(query_texts).most_common(10)
            
            # Query complexity distribution
            complexity_distribution = Counter(
                event.event_data.get('complexity', 'medium')
                for event in events
                if event.event_data.get('complexity')
            )
            
            # Peak usage hours
            hours = [event.timestamp.hour for event in events]
            peak_hours = [hour for hour, count in Counter(hours).most_common(5)]
            
            return QueryMetrics(
                total_queries=total_queries,
                avg_response_time=avg_response_time,
                success_rate=success_rate,
                most_common_queries=most_common_queries,
                query_complexity_distribution=dict(complexity_distribution),
                peak_usage_hours=peak_hours
            )
            
        except Exception as e:
            logger.error(f"Error getting query metrics: {str(e)}")
            raise

    async def get_document_metrics(
        self,
        user_id: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> DocumentMetrics:
        """Get comprehensive document metrics"""
        try:
            if not time_range:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                time_range = (start_date, end_date)
            
            # Document access events
            access_events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.event_type == EventType.DOCUMENT_ACCESSED,
                AnalyticsEvent.timestamp.between(time_range[0], time_range[1])
            )
            
            if user_id:
                access_events = access_events.filter(AnalyticsEvent.user_id == user_id)
            
            access_data = access_events.all()
            
            # Document access frequency
            doc_access_counts = Counter(
                event.event_data.get('document_id')
                for event in access_data
                if event.event_data.get('document_id')
            )
            
            # Get document details for most accessed
            most_accessed_docs = []
            for doc_id, count in doc_access_counts.most_common(10):
                doc = self.db.query(Document).filter(Document.id == doc_id).first()
                if doc:
                    most_accessed_docs.append((doc.id, doc.name, count))
            
            # Document type distribution
            documents_query = self.db.query(Document)
            if user_id:
                documents_query = documents_query.filter(Document.user_id == user_id)
            
            documents = documents_query.all()
            type_distribution = Counter(doc.content_type for doc in documents)
            
            # Average document size
            sizes = [doc.size for doc in documents if doc.size]
            avg_size = sum(sizes) / len(sizes) if sizes else 0
            
            # Upload trends
            upload_events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.event_type == EventType.DOCUMENT_UPLOADED,
                AnalyticsEvent.timestamp.between(time_range[0], time_range[1])
            )
            
            if user_id:
                upload_events = upload_events.filter(AnalyticsEvent.user_id == user_id)
            
            upload_data = upload_events.all()
            upload_trends = Counter(
                event.timestamp.strftime('%Y-%m-%d')
                for event in upload_data
            )
            
            # Tag popularity
            tags_query = self.db.query(DocumentTag)
            if user_id:
                # Filter by user's documents
                user_doc_ids = [doc.id for doc in documents]
                tags_query = tags_query.filter(DocumentTag.document_id.in_(user_doc_ids))
            
            tags = tags_query.all()
            tag_popularity = Counter(tag.tag_name for tag in tags)
            
            return DocumentMetrics(
                total_documents=len(documents),
                most_accessed_documents=most_accessed_docs,
                document_type_distribution=dict(type_distribution),
                avg_document_size=avg_size,
                upload_trends=dict(upload_trends),
                tag_popularity=dict(tag_popularity)
            )
            
        except Exception as e:
            logger.error(f"Error getting document metrics: {str(e)}")
            raise

    async def get_user_behavior_metrics(
        self,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> UserBehaviorMetrics:
        """Get user behavior and interaction metrics"""
        try:
            if not time_range:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                time_range = (start_date, end_date)
            
            # Active users
            active_users = self.db.query(AnalyticsEvent.user_id).filter(
                AnalyticsEvent.timestamp.between(time_range[0], time_range[1]),
                AnalyticsEvent.user_id.isnot(None)
            ).distinct().count()
            
            # Session duration
            session_events = self.db.query(AnalyticsEvent).filter(
                or_(
                    AnalyticsEvent.event_type == EventType.USER_SESSION_START,
                    AnalyticsEvent.event_type == EventType.USER_SESSION_END
                ),
                AnalyticsEvent.timestamp.between(time_range[0], time_range[1])
            ).all()
            
            # Calculate session durations
            session_durations = []
            sessions = defaultdict(dict)
            
            for event in session_events:
                session_id = event.session_id
                if event.event_type == EventType.USER_SESSION_START:
                    sessions[session_id]['start'] = event.timestamp
                elif event.event_type == EventType.USER_SESSION_END:
                    sessions[session_id]['end'] = event.timestamp
            
            for session_data in sessions.values():
                if 'start' in session_data and 'end' in session_data:
                    duration = (session_data['end'] - session_data['start']).total_seconds()
                    session_durations.append(duration)
            
            avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else 0
            
            # Feature usage
            all_events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.timestamp.between(time_range[0], time_range[1])
            ).all()
            
            feature_usage = Counter(event.event_type for event in all_events)
            
            # Satisfaction scores from feedback
            feedback_events = self.db.query(UserFeedback).filter(
                UserFeedback.created_at.between(time_range[0], time_range[1]),
                UserFeedback.feedback_type == 'rating'
            ).all()
            
            satisfaction_scores = {}
            if feedback_events:
                ratings = [
                    feedback.feedback_value.get('rating', 0)
                    for feedback in feedback_events
                    if isinstance(feedback.feedback_value, dict) and 'rating' in feedback.feedback_value
                ]
                if ratings:
                    satisfaction_scores['average'] = sum(ratings) / len(ratings)
                    satisfaction_scores['total_ratings'] = len(ratings)
            
            # Domain preferences from user profiles
            profiles = self.db.query(UserProfile).all()
            domain_preferences = Counter()
            for profile in profiles:
                if profile.domain_expertise:
                    for domain in profile.domain_expertise.keys():
                        domain_preferences[domain] += 1
            
            # User retention (simplified - users active in both halves of time range)
            mid_point = time_range[0] + (time_range[1] - time_range[0]) / 2
            
            early_users = set(
                self.db.query(AnalyticsEvent.user_id).filter(
                    AnalyticsEvent.timestamp.between(time_range[0], mid_point),
                    AnalyticsEvent.user_id.isnot(None)
                ).distinct().all()
            )
            
            late_users = set(
                self.db.query(AnalyticsEvent.user_id).filter(
                    AnalyticsEvent.timestamp.between(mid_point, time_range[1]),
                    AnalyticsEvent.user_id.isnot(None)
                ).distinct().all()
            )
            
            retained_users = early_users.intersection(late_users)
            retention_rate = len(retained_users) / len(early_users) if early_users else 0
            
            return UserBehaviorMetrics(
                active_users=active_users,
                avg_session_duration=avg_session_duration,
                user_retention_rate=retention_rate,
                feature_usage=dict(feature_usage),
                satisfaction_scores=satisfaction_scores,
                domain_preferences=dict(domain_preferences)
            )
            
        except Exception as e:
            logger.error(f"Error getting user behavior metrics: {str(e)}")
            raise

    async def get_performance_metrics(
        self,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> PerformanceMetrics:
        """Get system performance metrics"""
        try:
            if not time_range:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                time_range = (start_date, end_date)
            
            # Performance events
            perf_events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.event_type == EventType.PERFORMANCE_METRIC,
                AnalyticsEvent.timestamp.between(time_range[0], time_range[1])
            ).all()
            
            # Response times from query events
            query_events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.event_type == EventType.QUERY_EXECUTED,
                AnalyticsEvent.timestamp.between(time_range[0], time_range[1])
            ).all()
            
            response_times = [
                event.event_data.get('response_time', 0)
                for event in query_events
                if event.event_data.get('response_time')
            ]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Error rate
            error_events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.event_type == EventType.ERROR_OCCURRED,
                AnalyticsEvent.timestamp.between(time_range[0], time_range[1])
            ).count()
            
            total_events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.timestamp.between(time_range[0], time_range[1])
            ).count()
            
            error_rate = error_events / total_events if total_events > 0 else 0
            
            # Throughput (events per hour)
            hours_in_range = (time_range[1] - time_range[0]).total_seconds() / 3600
            throughput = total_events / hours_in_range if hours_in_range > 0 else 0
            
            # Memory usage and cache metrics from performance events
            memory_usage = {}
            cache_hit_rates = []
            db_query_times = []
            
            for event in perf_events:
                data = event.event_data
                if 'memory_usage' in data:
                    memory_usage.update(data['memory_usage'])
                if 'cache_hit_rate' in data:
                    cache_hit_rates.append(data['cache_hit_rate'])
                if 'db_query_time' in data:
                    db_query_times.append(data['db_query_time'])
            
            cache_hit_rate = sum(cache_hit_rates) / len(cache_hit_rates) if cache_hit_rates else 0
            
            db_performance = {}
            if db_query_times:
                db_performance['avg_query_time'] = sum(db_query_times) / len(db_query_times)
                db_performance['max_query_time'] = max(db_query_times)
                db_performance['min_query_time'] = min(db_query_times)
            
            return PerformanceMetrics(
                avg_response_time=avg_response_time,
                error_rate=error_rate,
                throughput=throughput,
                memory_usage=memory_usage,
                cache_hit_rate=cache_hit_rate,
                database_query_performance=db_performance
            )
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            raise

    async def get_comprehensive_insights(
        self,
        user_id: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> AnalyticsInsights:
        """Get comprehensive analytics insights with trends and recommendations"""
        try:
            # Gather all metrics
            query_metrics = await self.get_query_metrics(user_id, time_range)
            document_metrics = await self.get_document_metrics(user_id, time_range)
            user_behavior = await self.get_user_behavior_metrics(time_range)
            performance = await self.get_performance_metrics(time_range)
            
            # Generate trends
            trends = await self._analyze_trends(user_id, time_range)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                query_metrics, document_metrics, user_behavior, performance
            )
            
            return AnalyticsInsights(
                query_metrics=query_metrics,
                document_metrics=document_metrics,
                user_behavior=user_behavior,
                performance=performance,
                trends=trends,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error getting comprehensive insights: {str(e)}")
            raise

    async def _analyze_trends(
        self,
        user_id: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Analyze trends in usage patterns"""
        try:
            if not time_range:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                time_range = (start_date, end_date)
            
            trends = {}
            
            # Query volume trend
            query_events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.event_type == EventType.QUERY_EXECUTED,
                AnalyticsEvent.timestamp.between(time_range[0], time_range[1])
            )
            
            if user_id:
                query_events = query_events.filter(AnalyticsEvent.user_id == user_id)
            
            # Group by day
            daily_queries = defaultdict(int)
            for event in query_events.all():
                day = event.timestamp.strftime('%Y-%m-%d')
                daily_queries[day] += 1
            
            trends['daily_query_volume'] = dict(daily_queries)
            
            # Response time trend
            response_times_by_day = defaultdict(list)
            for event in query_events.all():
                if event.event_data.get('response_time'):
                    day = event.timestamp.strftime('%Y-%m-%d')
                    response_times_by_day[day].append(event.event_data['response_time'])
            
            avg_response_times = {
                day: sum(times) / len(times)
                for day, times in response_times_by_day.items()
            }
            trends['daily_avg_response_time'] = avg_response_times
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {str(e)}")
            return {}

    async def _generate_recommendations(
        self,
        query_metrics: QueryMetrics,
        document_metrics: DocumentMetrics,
        user_behavior: UserBehaviorMetrics,
        performance: PerformanceMetrics
    ) -> List[str]:
        """Generate actionable recommendations based on analytics"""
        recommendations = []
        
        try:
            # Performance recommendations
            if performance.avg_response_time > 5.0:
                recommendations.append(
                    "Consider optimizing query processing - average response time is above 5 seconds"
                )
            
            if performance.error_rate > 0.05:
                recommendations.append(
                    f"Error rate is {performance.error_rate:.2%} - investigate and fix common errors"
                )
            
            # Query optimization recommendations
            if query_metrics.success_rate < 0.9:
                recommendations.append(
                    f"Query success rate is {query_metrics.success_rate:.2%} - improve query handling"
                )
            
            # Document usage recommendations
            if document_metrics.total_documents > 0:
                access_ratio = len(document_metrics.most_accessed_documents) / document_metrics.total_documents
                if access_ratio < 0.3:
                    recommendations.append(
                        "Many documents are rarely accessed - consider improving discoverability"
                    )
            
            # User engagement recommendations
            if user_behavior.avg_session_duration < 300:  # 5 minutes
                recommendations.append(
                    "Average session duration is low - consider improving user engagement"
                )
            
            if user_behavior.user_retention_rate < 0.5:
                recommendations.append(
                    "User retention rate is below 50% - focus on user experience improvements"
                )
            
            # Feature usage recommendations
            if user_behavior.feature_usage:
                total_usage = sum(user_behavior.feature_usage.values())
                underused_features = [
                    feature for feature, count in user_behavior.feature_usage.items()
                    if count / total_usage < 0.05
                ]
                if underused_features:
                    recommendations.append(
                        f"Consider promoting underused features: {', '.join(underused_features[:3])}"
                    )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["Unable to generate recommendations due to analysis error"]

    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics from Redis buffer"""
        try:
            if not self.redis_client:
                return {}
            
            current_hour = datetime.utcnow().strftime('%Y-%m-%d-%H')
            buffer_key = f"analytics_buffer:{current_hour}"
            
            # Get recent events from buffer
            events_data = await self.redis_client.lrange(buffer_key, 0, -1)
            
            if not events_data:
                return {"active_users": 0, "queries_per_hour": 0, "avg_response_time": 0}
            
            events = [json.loads(event) for event in events_data]
            
            # Calculate real-time metrics
            active_users = len(set(event.get('user_id') for event in events if event.get('user_id')))
            
            query_events = [e for e in events if e.get('event_type') == EventType.QUERY_EXECUTED]
            queries_per_hour = len(query_events)
            
            response_times = [
                e.get('event_data', {}).get('response_time', 0)
                for e in query_events
                if e.get('event_data', {}).get('response_time')
            ]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            return {
                "active_users": active_users,
                "queries_per_hour": queries_per_hour,
                "avg_response_time": avg_response_time,
                "total_events": len(events)
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time metrics: {str(e)}")
            return {}

    async def export_analytics_data(
        self,
        user_id: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export analytics data for external analysis"""
        try:
            insights = await self.get_comprehensive_insights(user_id, time_range)
            
            export_data = {
                "export_timestamp": datetime.utcnow().isoformat(),
                "time_range": {
                    "start": time_range[0].isoformat() if time_range else None,
                    "end": time_range[1].isoformat() if time_range else None
                },
                "user_id": user_id,
                "query_metrics": {
                    "total_queries": insights.query_metrics.total_queries,
                    "avg_response_time": insights.query_metrics.avg_response_time,
                    "success_rate": insights.query_metrics.success_rate,
                    "most_common_queries": insights.query_metrics.most_common_queries,
                    "complexity_distribution": insights.query_metrics.query_complexity_distribution,
                    "peak_usage_hours": insights.query_metrics.peak_usage_hours
                },
                "document_metrics": {
                    "total_documents": insights.document_metrics.total_documents,
                    "most_accessed_documents": insights.document_metrics.most_accessed_documents,
                    "type_distribution": insights.document_metrics.document_type_distribution,
                    "avg_document_size": insights.document_metrics.avg_document_size,
                    "upload_trends": insights.document_metrics.upload_trends,
                    "tag_popularity": insights.document_metrics.tag_popularity
                },
                "user_behavior": {
                    "active_users": insights.user_behavior.active_users,
                    "avg_session_duration": insights.user_behavior.avg_session_duration,
                    "retention_rate": insights.user_behavior.user_retention_rate,
                    "feature_usage": insights.user_behavior.feature_usage,
                    "satisfaction_scores": insights.user_behavior.satisfaction_scores,
                    "domain_preferences": insights.user_behavior.domain_preferences
                },
                "performance": {
                    "avg_response_time": insights.performance.avg_response_time,
                    "error_rate": insights.performance.error_rate,
                    "throughput": insights.performance.throughput,
                    "memory_usage": insights.performance.memory_usage,
                    "cache_hit_rate": insights.performance.cache_hit_rate,
                    "db_performance": insights.performance.database_query_performance
                },
                "trends": insights.trends,
                "recommendations": insights.recommendations
            }
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting analytics data: {str(e)}")
            raise

# Convenience function for getting analytics service
def get_analytics_service(db: Session = None) -> EnhancedAnalyticsService:
    """Get analytics service instance"""
    if db is None:
        db = next(get_db())
    return EnhancedAnalyticsService(db)