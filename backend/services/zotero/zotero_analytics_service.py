"""
Zotero Analytics Service

Provides comprehensive analytics and usage tracking for Zotero integration features.
Tracks user interactions, feature usage, performance metrics, and system health.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AnalyticsEventType(Enum):
    """Types of analytics events to track"""
    # Authentication events
    AUTH_INITIATED = "auth_initiated"
    AUTH_COMPLETED = "auth_completed"
    AUTH_FAILED = "auth_failed"
    TOKEN_REFRESHED = "token_refreshed"
    
    # Library operations
    LIBRARY_IMPORT_STARTED = "library_import_started"
    LIBRARY_IMPORT_COMPLETED = "library_import_completed"
    LIBRARY_SYNC_STARTED = "library_sync_started"
    LIBRARY_SYNC_COMPLETED = "library_sync_completed"
    
    # Search and browsing
    SEARCH_PERFORMED = "search_performed"
    REFERENCE_VIEWED = "reference_viewed"
    COLLECTION_BROWSED = "collection_browsed"
    
    # Citation operations
    CITATION_GENERATED = "citation_generated"
    BIBLIOGRAPHY_EXPORTED = "bibliography_exported"
    REFERENCE_EXPORTED = "reference_exported"
    
    # AI features
    AI_ANALYSIS_REQUESTED = "ai_analysis_requested"
    SIMILARITY_SEARCH = "similarity_search"
    RESEARCH_INSIGHTS_GENERATED = "research_insights_generated"
    
    # Collaboration
    REFERENCE_SHARED = "reference_shared"
    COLLECTION_SHARED = "collection_shared"
    ANNOTATION_CREATED = "annotation_created"
    
    # Errors
    SYNC_ERROR = "sync_error"
    API_ERROR = "api_error"
    SYSTEM_ERROR = "system_error"


@dataclass
class AnalyticsEvent:
    """Analytics event data structure"""
    event_type: AnalyticsEventType
    user_id: str
    timestamp: datetime
    session_id: Optional[str] = None
    library_id: Optional[str] = None
    item_count: Optional[int] = None
    duration_ms: Optional[int] = None
    success: bool = True
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UsageMetrics:
    """Usage metrics summary"""
    total_users: int
    active_users_24h: int
    active_users_7d: int
    active_users_30d: int
    total_libraries: int
    total_references: int
    total_citations_generated: int
    avg_library_size: float
    most_used_features: List[Tuple[str, int]]


@dataclass
class PerformanceMetrics:
    """Performance metrics summary"""
    avg_sync_time: float
    avg_search_time: float
    avg_citation_time: float
    sync_success_rate: float
    api_error_rate: float
    system_uptime: float
    peak_concurrent_users: int


class ZoteroAnalyticsService:
    """Service for tracking and analyzing Zotero integration usage"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def track_event(
        self,
        event_type: AnalyticsEventType,
        user_id: str,
        session_id: Optional[str] = None,
        library_id: Optional[str] = None,
        item_count: Optional[int] = None,
        duration_ms: Optional[int] = None,
        success: bool = True,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track an analytics event"""
        try:
            event = AnalyticsEvent(
                event_type=event_type,
                user_id=user_id,
                timestamp=datetime.utcnow(),
                session_id=session_id,
                library_id=library_id,
                item_count=item_count,
                duration_ms=duration_ms,
                success=success,
                error_code=error_code,
                error_message=error_message,
                metadata=metadata
            )
            
            async with get_db_session() as session:
                await self._store_event(session, event)
                
            self.logger.debug(f"Tracked analytics event: {event_type.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to track analytics event: {e}")
            return False
    
    async def _store_event(self, session: AsyncSession, event: AnalyticsEvent):
        """Store analytics event in database"""
        query = text("""
            INSERT INTO zotero.analytics_events (
                event_type, user_id, timestamp, session_id, library_id,
                item_count, duration_ms, success, error_code, error_message, metadata
            ) VALUES (
                :event_type, :user_id, :timestamp, :session_id, :library_id,
                :item_count, :duration_ms, :success, :error_code, :error_message, :metadata
            )
        """)
        
        await session.execute(query, {
            "event_type": event.event_type.value,
            "user_id": event.user_id,
            "timestamp": event.timestamp,
            "session_id": event.session_id,
            "library_id": event.library_id,
            "item_count": event.item_count,
            "duration_ms": event.duration_ms,
            "success": event.success,
            "error_code": event.error_code,
            "error_message": event.error_message,
            "metadata": json.dumps(event.metadata) if event.metadata else None
        })
        await session.commit()
    
    async def get_usage_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> UsageMetrics:
        """Get comprehensive usage metrics"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            async with get_db_session() as session:
                # Total users with Zotero connections
                total_users_query = text("""
                    SELECT COUNT(DISTINCT user_id) 
                    FROM zotero.connections 
                    WHERE status = 'active'
                """)
                total_users_result = await session.execute(total_users_query)
                total_users = total_users_result.scalar() or 0
                
                # Active users in different time periods
                active_users_24h = await self._get_active_users(session, hours=24)
                active_users_7d = await self._get_active_users(session, days=7)
                active_users_30d = await self._get_active_users(session, days=30)
                
                # Library and reference counts
                library_stats = await self._get_library_stats(session)
                
                # Citation generation count
                citations_query = text("""
                    SELECT COUNT(*) 
                    FROM zotero.analytics_events 
                    WHERE event_type = 'citation_generated'
                    AND timestamp >= :start_date AND timestamp <= :end_date
                """)
                citations_result = await session.execute(
                    citations_query, 
                    {"start_date": start_date, "end_date": end_date}
                )
                total_citations = citations_result.scalar() or 0
                
                # Most used features
                most_used_features = await self._get_most_used_features(
                    session, start_date, end_date
                )
                
                return UsageMetrics(
                    total_users=total_users,
                    active_users_24h=active_users_24h,
                    active_users_7d=active_users_7d,
                    active_users_30d=active_users_30d,
                    total_libraries=library_stats["total_libraries"],
                    total_references=library_stats["total_references"],
                    total_citations_generated=total_citations,
                    avg_library_size=library_stats["avg_library_size"],
                    most_used_features=most_used_features
                )
                
        except Exception as e:
            self.logger.error(f"Failed to get usage metrics: {e}")
            raise
    
    async def _get_active_users(
        self, 
        session: AsyncSession, 
        hours: Optional[int] = None, 
        days: Optional[int] = None
    ) -> int:
        """Get count of active users in specified time period"""
        if hours:
            time_threshold = datetime.utcnow() - timedelta(hours=hours)
        elif days:
            time_threshold = datetime.utcnow() - timedelta(days=days)
        else:
            time_threshold = datetime.utcnow() - timedelta(hours=24)
        
        query = text("""
            SELECT COUNT(DISTINCT user_id) 
            FROM zotero.analytics_events 
            WHERE timestamp >= :time_threshold
        """)
        result = await session.execute(query, {"time_threshold": time_threshold})
        return result.scalar() or 0
    
    async def _get_library_stats(self, session: AsyncSession) -> Dict[str, Any]:
        """Get library and reference statistics"""
        stats_query = text("""
            SELECT 
                COUNT(DISTINCT l.id) as total_libraries,
                COUNT(DISTINCT i.id) as total_references,
                AVG(library_sizes.item_count) as avg_library_size
            FROM zotero.libraries l
            LEFT JOIN zotero.items i ON l.id = i.library_id
            LEFT JOIN (
                SELECT library_id, COUNT(*) as item_count
                FROM zotero.items
                GROUP BY library_id
            ) library_sizes ON l.id = library_sizes.library_id
        """)
        result = await session.execute(stats_query)
        row = result.fetchone()
        
        return {
            "total_libraries": row[0] or 0,
            "total_references": row[1] or 0,
            "avg_library_size": float(row[2] or 0)
        }
    
    async def _get_most_used_features(
        self, 
        session: AsyncSession, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Tuple[str, int]]:
        """Get most frequently used features"""
        query = text("""
            SELECT event_type, COUNT(*) as usage_count
            FROM zotero.analytics_events
            WHERE timestamp >= :start_date AND timestamp <= :end_date
            AND success = true
            GROUP BY event_type
            ORDER BY usage_count DESC
            LIMIT 10
        """)
        result = await session.execute(
            query, 
            {"start_date": start_date, "end_date": end_date}
        )
        return [(row[0], row[1]) for row in result.fetchall()]
    
    async def get_performance_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> PerformanceMetrics:
        """Get performance metrics"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
            async with get_db_session() as session:
                # Average operation times
                avg_sync_time = await self._get_avg_operation_time(
                    session, "library_sync_completed", start_date, end_date
                )
                avg_search_time = await self._get_avg_operation_time(
                    session, "search_performed", start_date, end_date
                )
                avg_citation_time = await self._get_avg_operation_time(
                    session, "citation_generated", start_date, end_date
                )
                
                # Success rates
                sync_success_rate = await self._get_success_rate(
                    session, "library_sync_completed", start_date, end_date
                )
                
                # Error rates
                api_error_rate = await self._get_error_rate(
                    session, start_date, end_date
                )
                
                # Peak concurrent users (approximation)
                peak_concurrent_users = await self._get_peak_concurrent_users(
                    session, start_date, end_date
                )
                
                return PerformanceMetrics(
                    avg_sync_time=avg_sync_time,
                    avg_search_time=avg_search_time,
                    avg_citation_time=avg_citation_time,
                    sync_success_rate=sync_success_rate,
                    api_error_rate=api_error_rate,
                    system_uptime=99.9,  # This would come from infrastructure monitoring
                    peak_concurrent_users=peak_concurrent_users
                )
                
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {e}")
            raise
    
    async def _get_avg_operation_time(
        self, 
        session: AsyncSession, 
        event_type: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> float:
        """Get average operation time for specific event type"""
        query = text("""
            SELECT AVG(duration_ms) 
            FROM zotero.analytics_events 
            WHERE event_type = :event_type 
            AND timestamp >= :start_date AND timestamp <= :end_date
            AND duration_ms IS NOT NULL
            AND success = true
        """)
        result = await session.execute(query, {
            "event_type": event_type,
            "start_date": start_date,
            "end_date": end_date
        })
        return float(result.scalar() or 0)
    
    async def _get_success_rate(
        self, 
        session: AsyncSession, 
        event_type: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> float:
        """Get success rate for specific operation"""
        query = text("""
            SELECT 
                COUNT(CASE WHEN success = true THEN 1 END) * 100.0 / COUNT(*) as success_rate
            FROM zotero.analytics_events 
            WHERE event_type = :event_type 
            AND timestamp >= :start_date AND timestamp <= :end_date
        """)
        result = await session.execute(query, {
            "event_type": event_type,
            "start_date": start_date,
            "end_date": end_date
        })
        return float(result.scalar() or 0)
    
    async def _get_error_rate(
        self, 
        session: AsyncSession, 
        start_date: datetime, 
        end_date: datetime
    ) -> float:
        """Get overall error rate"""
        query = text("""
            SELECT 
                COUNT(CASE WHEN success = false THEN 1 END) * 100.0 / COUNT(*) as error_rate
            FROM zotero.analytics_events 
            WHERE timestamp >= :start_date AND timestamp <= :end_date
        """)
        result = await session.execute(query, {
            "start_date": start_date,
            "end_date": end_date
        })
        return float(result.scalar() or 0)
    
    async def _get_peak_concurrent_users(
        self, 
        session: AsyncSession, 
        start_date: datetime, 
        end_date: datetime
    ) -> int:
        """Get peak concurrent users (approximation based on hourly activity)"""
        query = text("""
            SELECT MAX(hourly_users) as peak_users
            FROM (
                SELECT 
                    DATE_TRUNC('hour', timestamp) as hour,
                    COUNT(DISTINCT user_id) as hourly_users
                FROM zotero.analytics_events 
                WHERE timestamp >= :start_date AND timestamp <= :end_date
                GROUP BY DATE_TRUNC('hour', timestamp)
            ) hourly_stats
        """)
        result = await session.execute(query, {
            "start_date": start_date,
            "end_date": end_date
        })
        return int(result.scalar() or 0)
    
    async def get_error_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get summary of recent errors"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
            async with get_db_session() as session:
                query = text("""
                    SELECT 
                        error_code,
                        error_message,
                        event_type,
                        COUNT(*) as occurrence_count,
                        MAX(timestamp) as last_occurrence,
                        COUNT(DISTINCT user_id) as affected_users
                    FROM zotero.analytics_events 
                    WHERE success = false 
                    AND timestamp >= :start_date AND timestamp <= :end_date
                    AND error_code IS NOT NULL
                    GROUP BY error_code, error_message, event_type
                    ORDER BY occurrence_count DESC, last_occurrence DESC
                    LIMIT :limit
                """)
                result = await session.execute(query, {
                    "start_date": start_date,
                    "end_date": end_date,
                    "limit": limit
                })
                
                errors = []
                for row in result.fetchall():
                    errors.append({
                        "error_code": row[0],
                        "error_message": row[1],
                        "event_type": row[2],
                        "occurrence_count": row[3],
                        "last_occurrence": row[4],
                        "affected_users": row[5]
                    })
                
                return errors
                
        except Exception as e:
            self.logger.error(f"Failed to get error summary: {e}")
            raise
    
    async def get_user_activity_timeline(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get user activity timeline"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            async with get_db_session() as session:
                query = text("""
                    SELECT 
                        timestamp,
                        event_type,
                        success,
                        duration_ms,
                        item_count,
                        error_code,
                        metadata
                    FROM zotero.analytics_events 
                    WHERE user_id = :user_id
                    AND timestamp >= :start_date AND timestamp <= :end_date
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """)
                result = await session.execute(query, {
                    "user_id": user_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "limit": limit
                })
                
                activities = []
                for row in result.fetchall():
                    activities.append({
                        "timestamp": row[0],
                        "event_type": row[1],
                        "success": row[2],
                        "duration_ms": row[3],
                        "item_count": row[4],
                        "error_code": row[5],
                        "metadata": json.loads(row[6]) if row[6] else None
                    })
                
                return activities
                
        except Exception as e:
            self.logger.error(f"Failed to get user activity timeline: {e}")
            raise


# Global analytics service instance
analytics_service = ZoteroAnalyticsService()