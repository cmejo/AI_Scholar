"""
Zotero Admin Dashboard Service

Provides comprehensive administrative dashboard functionality for Zotero integration.
Aggregates data from analytics, monitoring, and error tracking services to provide
insights for system administrators and support teams.
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
from services.zotero.zotero_analytics_service import analytics_service, UsageMetrics, PerformanceMetrics
from services.zotero.zotero_monitoring_service import monitoring_service, HealthCheck, Alert
from services.zotero.zotero_error_tracking_service import error_tracking_service, ErrorSummary

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class DashboardOverview:
    """High-level dashboard overview"""
    total_users: int
    active_users_24h: int
    total_libraries: int
    total_references: int
    system_health_score: float
    critical_alerts: int
    unresolved_errors: int
    sync_success_rate: float
    api_response_time: float
    uptime_percentage: float


@dataclass
class UserEngagementMetrics:
    """User engagement and activity metrics"""
    daily_active_users: List[Tuple[datetime, int]]
    weekly_active_users: List[Tuple[datetime, int]]
    monthly_active_users: List[Tuple[datetime, int]]
    user_retention_rate: float
    average_session_duration: float
    feature_adoption_rates: Dict[str, float]
    user_satisfaction_score: Optional[float]


@dataclass
class SystemPerformanceMetrics:
    """System performance and reliability metrics"""
    api_response_times: List[Tuple[datetime, float]]
    error_rates: List[Tuple[datetime, float]]
    sync_performance: List[Tuple[datetime, float]]
    resource_utilization: Dict[str, float]
    throughput_metrics: Dict[str, int]
    availability_metrics: Dict[str, float]


@dataclass
class OperationalInsights:
    """Operational insights and recommendations"""
    top_issues: List[Dict[str, Any]]
    performance_bottlenecks: List[Dict[str, Any]]
    capacity_recommendations: List[str]
    optimization_opportunities: List[str]
    maintenance_alerts: List[str]


class ZoteroAdminDashboardService:
    """Service for providing administrative dashboard data and insights"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def get_dashboard_overview(self) -> DashboardOverview:
        """Get high-level dashboard overview"""
        try:
            # Get usage metrics
            usage_metrics = await analytics_service.get_usage_metrics()
            
            # Get performance metrics
            performance_metrics = await analytics_service.get_performance_metrics()
            
            # Get health status
            health_checks = await monitoring_service.perform_health_check()
            system_health_score = self._calculate_health_score(health_checks)
            
            # Get active alerts
            active_alerts = await monitoring_service.get_active_alerts()
            critical_alerts = len([a for a in active_alerts if a.severity.value == "critical"])
            
            # Get error summary
            error_summary = await error_tracking_service.get_error_summary()
            unresolved_errors = error_summary.total_errors - int(error_summary.total_errors * error_summary.resolution_rate / 100)
            
            return DashboardOverview(
                total_users=usage_metrics.total_users,
                active_users_24h=usage_metrics.active_users_24h,
                total_libraries=usage_metrics.total_libraries,
                total_references=usage_metrics.total_references,
                system_health_score=system_health_score,
                critical_alerts=critical_alerts,
                unresolved_errors=unresolved_errors,
                sync_success_rate=performance_metrics.sync_success_rate,
                api_response_time=performance_metrics.avg_sync_time,
                uptime_percentage=performance_metrics.system_uptime
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get dashboard overview: {e}")
            raise
    
    def _calculate_health_score(self, health_checks: Dict[str, HealthCheck]) -> float:
        """Calculate overall system health score"""
        if not health_checks:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        # Weight different services based on importance
        service_weights = {
            "zotero_api": 0.3,
            "database": 0.25,
            "sync_service": 0.2,
            "redis": 0.15,
            "file_storage": 0.1
        }
        
        for service, check in health_checks.items():
            weight = service_weights.get(service, 0.1)
            
            if check.status == "healthy":
                score = 100.0
            elif check.status == "degraded":
                score = 60.0
            else:  # unhealthy
                score = 0.0
            
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    async def get_user_engagement_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> UserEngagementMetrics:
        """Get comprehensive user engagement metrics"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            async with get_db_session() as session:
                # Daily active users
                daily_users = await self._get_daily_active_users(session, start_date, end_date)
                
                # Weekly active users
                weekly_users = await self._get_weekly_active_users(session, start_date, end_date)
                
                # Monthly active users
                monthly_users = await self._get_monthly_active_users(session, start_date, end_date)
                
                # User retention rate
                retention_rate = await self._calculate_user_retention_rate(session)
                
                # Average session duration
                avg_session_duration = await self._calculate_avg_session_duration(session, start_date, end_date)
                
                # Feature adoption rates
                feature_adoption = await self._calculate_feature_adoption_rates(session, start_date, end_date)
                
                return UserEngagementMetrics(
                    daily_active_users=daily_users,
                    weekly_active_users=weekly_users,
                    monthly_active_users=monthly_users,
                    user_retention_rate=retention_rate,
                    average_session_duration=avg_session_duration,
                    feature_adoption_rates=feature_adoption,
                    user_satisfaction_score=None  # Would come from user feedback system
                )
                
        except Exception as e:
            self.logger.error(f"Failed to get user engagement metrics: {e}")
            raise
    
    async def _get_daily_active_users(
        self, 
        session: AsyncSession, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Tuple[datetime, int]]:
        """Get daily active users over time period"""
        query = text("""
            SELECT 
                DATE_TRUNC('day', timestamp) as day,
                COUNT(DISTINCT user_id) as active_users
            FROM zotero.analytics_events 
            WHERE timestamp >= :start_date AND timestamp <= :end_date
            GROUP BY DATE_TRUNC('day', timestamp)
            ORDER BY day
        """)
        result = await session.execute(query, {
            "start_date": start_date,
            "end_date": end_date
        })
        return [(row[0], row[1]) for row in result.fetchall()]
    
    async def _get_weekly_active_users(
        self, 
        session: AsyncSession, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Tuple[datetime, int]]:
        """Get weekly active users over time period"""
        query = text("""
            SELECT 
                DATE_TRUNC('week', timestamp) as week,
                COUNT(DISTINCT user_id) as active_users
            FROM zotero.analytics_events 
            WHERE timestamp >= :start_date AND timestamp <= :end_date
            GROUP BY DATE_TRUNC('week', timestamp)
            ORDER BY week
        """)
        result = await session.execute(query, {
            "start_date": start_date,
            "end_date": end_date
        })
        return [(row[0], row[1]) for row in result.fetchall()]
    
    async def _get_monthly_active_users(
        self, 
        session: AsyncSession, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Tuple[datetime, int]]:
        """Get monthly active users over time period"""
        query = text("""
            SELECT 
                DATE_TRUNC('month', timestamp) as month,
                COUNT(DISTINCT user_id) as active_users
            FROM zotero.analytics_events 
            WHERE timestamp >= :start_date AND timestamp <= :end_date
            GROUP BY DATE_TRUNC('month', timestamp)
            ORDER BY month
        """)
        result = await session.execute(query, {
            "start_date": start_date,
            "end_date": end_date
        })
        return [(row[0], row[1]) for row in result.fetchall()]
    
    async def _calculate_user_retention_rate(self, session: AsyncSession) -> float:
        """Calculate user retention rate"""
        # Users who were active in the last 30 days and are still active in the last 7 days
        query = text("""
            WITH users_30d AS (
                SELECT DISTINCT user_id
                FROM zotero.analytics_events 
                WHERE timestamp >= :thirty_days_ago
                AND timestamp < :seven_days_ago
            ),
            users_7d AS (
                SELECT DISTINCT user_id
                FROM zotero.analytics_events 
                WHERE timestamp >= :seven_days_ago
            )
            SELECT 
                COUNT(DISTINCT u7.user_id) * 100.0 / COUNT(DISTINCT u30.user_id) as retention_rate
            FROM users_30d u30
            LEFT JOIN users_7d u7 ON u30.user_id = u7.user_id
        """)
        
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        result = await session.execute(query, {
            "thirty_days_ago": thirty_days_ago,
            "seven_days_ago": seven_days_ago
        })
        return float(result.scalar() or 0)
    
    async def _calculate_avg_session_duration(
        self, 
        session: AsyncSession, 
        start_date: datetime, 
        end_date: datetime
    ) -> float:
        """Calculate average session duration in minutes"""
        # This is a simplified calculation - in practice you'd track session start/end events
        query = text("""
            WITH session_events AS (
                SELECT 
                    session_id,
                    MIN(timestamp) as session_start,
                    MAX(timestamp) as session_end
                FROM zotero.analytics_events 
                WHERE session_id IS NOT NULL
                AND timestamp >= :start_date AND timestamp <= :end_date
                GROUP BY session_id
                HAVING COUNT(*) > 1
            )
            SELECT AVG(EXTRACT(EPOCH FROM (session_end - session_start)) / 60) as avg_duration_minutes
            FROM session_events
        """)
        result = await session.execute(query, {
            "start_date": start_date,
            "end_date": end_date
        })
        return float(result.scalar() or 0)
    
    async def _calculate_feature_adoption_rates(
        self, 
        session: AsyncSession, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, float]:
        """Calculate feature adoption rates"""
        # Get total active users
        total_users_query = text("""
            SELECT COUNT(DISTINCT user_id) 
            FROM zotero.analytics_events 
            WHERE timestamp >= :start_date AND timestamp <= :end_date
        """)
        result = await session.execute(total_users_query, {
            "start_date": start_date,
            "end_date": end_date
        })
        total_users = result.scalar() or 1
        
        # Get feature usage by event type
        feature_usage_query = text("""
            SELECT 
                event_type,
                COUNT(DISTINCT user_id) as users_using_feature
            FROM zotero.analytics_events 
            WHERE timestamp >= :start_date AND timestamp <= :end_date
            GROUP BY event_type
        """)
        result = await session.execute(feature_usage_query, {
            "start_date": start_date,
            "end_date": end_date
        })
        
        adoption_rates = {}
        for row in result.fetchall():
            event_type = row[0]
            users_using = row[1]
            adoption_rate = (users_using / total_users) * 100
            adoption_rates[event_type] = adoption_rate
        
        return adoption_rates
    
    async def get_system_performance_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> SystemPerformanceMetrics:
        """Get comprehensive system performance metrics"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
            async with get_db_session() as session:
                # API response times over time
                api_response_times = await self._get_api_response_times(session, start_date, end_date)
                
                # Error rates over time
                error_rates = await self._get_error_rates(session, start_date, end_date)
                
                # Sync performance over time
                sync_performance = await self._get_sync_performance(session, start_date, end_date)
                
                # Resource utilization
                resource_utilization = await self._get_resource_utilization(session)
                
                # Throughput metrics
                throughput_metrics = await self._get_throughput_metrics(session, start_date, end_date)
                
                # Availability metrics
                availability_metrics = await self._get_availability_metrics(session, start_date, end_date)
                
                return SystemPerformanceMetrics(
                    api_response_times=api_response_times,
                    error_rates=error_rates,
                    sync_performance=sync_performance,
                    resource_utilization=resource_utilization,
                    throughput_metrics=throughput_metrics,
                    availability_metrics=availability_metrics
                )
                
        except Exception as e:
            self.logger.error(f"Failed to get system performance metrics: {e}")
            raise
    
    async def _get_api_response_times(
        self, 
        session: AsyncSession, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Tuple[datetime, float]]:
        """Get API response times over time"""
        query = text("""
            SELECT 
                DATE_TRUNC('hour', timestamp) as hour,
                AVG(response_time_ms) as avg_response_time
            FROM zotero.health_checks 
            WHERE service = 'zotero_api'
            AND timestamp >= :start_date AND timestamp <= :end_date
            AND response_time_ms IS NOT NULL
            GROUP BY DATE_TRUNC('hour', timestamp)
            ORDER BY hour
        """)
        result = await session.execute(query, {
            "start_date": start_date,
            "end_date": end_date
        })
        return [(row[0], float(row[1])) for row in result.fetchall()]
    
    async def _get_error_rates(
        self, 
        session: AsyncSession, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Tuple[datetime, float]]:
        """Get error rates over time"""
        query = text("""
            SELECT 
                DATE_TRUNC('hour', timestamp) as hour,
                COUNT(CASE WHEN success = false THEN 1 END) * 100.0 / COUNT(*) as error_rate
            FROM zotero.analytics_events 
            WHERE timestamp >= :start_date AND timestamp <= :end_date
            GROUP BY DATE_TRUNC('hour', timestamp)
            ORDER BY hour
        """)
        result = await session.execute(query, {
            "start_date": start_date,
            "end_date": end_date
        })
        return [(row[0], float(row[1] or 0)) for row in result.fetchall()]
    
    async def _get_sync_performance(
        self, 
        session: AsyncSession, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Tuple[datetime, float]]:
        """Get sync performance over time"""
        query = text("""
            SELECT 
                DATE_TRUNC('hour', timestamp) as hour,
                AVG(duration_ms) as avg_sync_time
            FROM zotero.analytics_events 
            WHERE event_type IN ('library_sync_completed', 'library_import_completed')
            AND timestamp >= :start_date AND timestamp <= :end_date
            AND duration_ms IS NOT NULL
            AND success = true
            GROUP BY DATE_TRUNC('hour', timestamp)
            ORDER BY hour
        """)
        result = await session.execute(query, {
            "start_date": start_date,
            "end_date": end_date
        })
        return [(row[0], float(row[1] or 0)) for row in result.fetchall()]
    
    async def _get_resource_utilization(self, session: AsyncSession) -> Dict[str, float]:
        """Get current resource utilization"""
        # Get latest system metrics
        query = text("""
            SELECT 
                memory_usage_percent,
                cpu_usage_percent,
                disk_usage_percent,
                active_connections
            FROM zotero.system_metrics 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        result = await session.execute(query)
        row = result.fetchone()
        
        if row:
            return {
                "memory_usage": float(row[0] or 0),
                "cpu_usage": float(row[1] or 0),
                "disk_usage": float(row[2] or 0),
                "database_connections": float(row[3] or 0)
            }
        else:
            return {
                "memory_usage": 0.0,
                "cpu_usage": 0.0,
                "disk_usage": 0.0,
                "database_connections": 0.0
            }
    
    async def _get_throughput_metrics(
        self, 
        session: AsyncSession, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, int]:
        """Get throughput metrics"""
        query = text("""
            SELECT 
                COUNT(*) as total_operations,
                COUNT(CASE WHEN event_type LIKE '%sync%' THEN 1 END) as sync_operations,
                COUNT(CASE WHEN event_type LIKE '%search%' THEN 1 END) as search_operations,
                COUNT(CASE WHEN event_type LIKE '%citation%' THEN 1 END) as citation_operations
            FROM zotero.analytics_events 
            WHERE timestamp >= :start_date AND timestamp <= :end_date
        """)
        result = await session.execute(query, {
            "start_date": start_date,
            "end_date": end_date
        })
        row = result.fetchone()
        
        if row:
            return {
                "total_operations": row[0] or 0,
                "sync_operations": row[1] or 0,
                "search_operations": row[2] or 0,
                "citation_operations": row[3] or 0
            }
        else:
            return {
                "total_operations": 0,
                "sync_operations": 0,
                "search_operations": 0,
                "citation_operations": 0
            }
    
    async def _get_availability_metrics(
        self, 
        session: AsyncSession, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, float]:
        """Get service availability metrics"""
        query = text("""
            SELECT 
                service,
                COUNT(CASE WHEN status = 'healthy' THEN 1 END) * 100.0 / COUNT(*) as availability
            FROM zotero.health_checks 
            WHERE timestamp >= :start_date AND timestamp <= :end_date
            GROUP BY service
        """)
        result = await session.execute(query, {
            "start_date": start_date,
            "end_date": end_date
        })
        
        availability = {}
        for row in result.fetchall():
            availability[row[0]] = float(row[1] or 0)
        
        return availability
    
    async def get_operational_insights(self) -> OperationalInsights:
        """Get operational insights and recommendations"""
        try:
            # Get top issues from error tracking
            error_summary = await error_tracking_service.get_error_summary()
            top_issues = [
                {
                    "type": "error",
                    "title": error[0],
                    "count": error[1],
                    "severity": "high" if error[1] > 10 else "medium"
                }
                for error in error_summary.most_common_errors[:5]
            ]
            
            # Get performance bottlenecks
            performance_bottlenecks = await self._identify_performance_bottlenecks()
            
            # Generate capacity recommendations
            capacity_recommendations = await self._generate_capacity_recommendations()
            
            # Generate optimization opportunities
            optimization_opportunities = await self._identify_optimization_opportunities()
            
            # Generate maintenance alerts
            maintenance_alerts = await self._generate_maintenance_alerts()
            
            return OperationalInsights(
                top_issues=top_issues,
                performance_bottlenecks=performance_bottlenecks,
                capacity_recommendations=capacity_recommendations,
                optimization_opportunities=optimization_opportunities,
                maintenance_alerts=maintenance_alerts
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get operational insights: {e}")
            raise
    
    async def _identify_performance_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        try:
            async with get_db_session() as session:
                # Check for slow sync operations
                slow_sync_query = text("""
                    SELECT AVG(duration_ms) as avg_duration
                    FROM zotero.analytics_events 
                    WHERE event_type = 'library_sync_completed'
                    AND timestamp >= :threshold
                    AND duration_ms IS NOT NULL
                """)
                threshold = datetime.utcnow() - timedelta(days=1)
                result = await session.execute(slow_sync_query, {"threshold": threshold})
                avg_sync_time = result.scalar() or 0
                
                if avg_sync_time > 30000:  # 30 seconds
                    bottlenecks.append({
                        "type": "performance",
                        "component": "sync_service",
                        "issue": "Slow sync operations",
                        "metric": f"Average sync time: {avg_sync_time/1000:.1f}s",
                        "recommendation": "Consider optimizing sync batch sizes or database queries"
                    })
                
                # Check for high error rates
                error_rate_query = text("""
                    SELECT 
                        COUNT(CASE WHEN success = false THEN 1 END) * 100.0 / COUNT(*) as error_rate
                    FROM zotero.analytics_events 
                    WHERE timestamp >= :threshold
                """)
                result = await session.execute(error_rate_query, {"threshold": threshold})
                error_rate = result.scalar() or 0
                
                if error_rate > 5.0:
                    bottlenecks.append({
                        "type": "reliability",
                        "component": "api_layer",
                        "issue": "High error rate",
                        "metric": f"Error rate: {error_rate:.1f}%",
                        "recommendation": "Investigate common error patterns and improve error handling"
                    })
        
        except Exception as e:
            self.logger.error(f"Failed to identify performance bottlenecks: {e}")
        
        return bottlenecks
    
    async def _generate_capacity_recommendations(self) -> List[str]:
        """Generate capacity planning recommendations"""
        recommendations = []
        
        try:
            async with get_db_session() as session:
                # Check database connection usage
                connection_query = text("""
                    SELECT active_connections
                    FROM zotero.system_metrics 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                result = await session.execute(connection_query)
                active_connections = result.scalar() or 0
                
                if active_connections > 50:  # Assuming max pool size of 100
                    recommendations.append(
                        "Consider increasing database connection pool size due to high usage"
                    )
                
                # Check storage usage trends
                storage_query = text("""
                    SELECT disk_usage_percent
                    FROM zotero.system_metrics 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                result = await session.execute(storage_query)
                disk_usage = result.scalar() or 0
                
                if disk_usage > 80:
                    recommendations.append(
                        "Disk usage is high - consider adding storage capacity or implementing cleanup policies"
                    )
                
                # Check user growth trends
                user_growth_query = text("""
                    SELECT COUNT(DISTINCT user_id) as recent_users
                    FROM zotero.analytics_events 
                    WHERE timestamp >= :recent_threshold
                """)
                recent_threshold = datetime.utcnow() - timedelta(days=7)
                result = await session.execute(user_growth_query, {"threshold": recent_threshold})
                recent_users = result.scalar() or 0
                
                if recent_users > 1000:  # Arbitrary threshold
                    recommendations.append(
                        "User activity is growing - consider scaling application instances"
                    )
        
        except Exception as e:
            self.logger.error(f"Failed to generate capacity recommendations: {e}")
        
        return recommendations
    
    async def _identify_optimization_opportunities(self) -> List[str]:
        """Identify optimization opportunities"""
        opportunities = []
        
        try:
            async with get_db_session() as session:
                # Check for unused features
                feature_usage_query = text("""
                    SELECT 
                        event_type,
                        COUNT(*) as usage_count
                    FROM zotero.analytics_events 
                    WHERE timestamp >= :threshold
                    GROUP BY event_type
                    HAVING COUNT(*) < 10
                """)
                threshold = datetime.utcnow() - timedelta(days=30)
                result = await session.execute(feature_usage_query, {"threshold": threshold})
                
                unused_features = result.fetchall()
                if unused_features:
                    opportunities.append(
                        f"Consider deprecating or improving {len(unused_features)} low-usage features"
                    )
                
                # Check for frequent error patterns
                error_pattern_query = text("""
                    SELECT error_code, COUNT(*) as error_count
                    FROM zotero.error_reports 
                    WHERE timestamp >= :threshold
                    AND resolved = false
                    GROUP BY error_code
                    HAVING COUNT(*) > 5
                """)
                result = await session.execute(error_pattern_query, {"threshold": threshold})
                
                frequent_errors = result.fetchall()
                if frequent_errors:
                    opportunities.append(
                        f"Address {len(frequent_errors)} frequently occurring error patterns"
                    )
        
        except Exception as e:
            self.logger.error(f"Failed to identify optimization opportunities: {e}")
        
        return opportunities
    
    async def _generate_maintenance_alerts(self) -> List[str]:
        """Generate maintenance alerts"""
        alerts = []
        
        try:
            async with get_db_session() as session:
                # Check for old unresolved errors
                old_errors_query = text("""
                    SELECT COUNT(*) 
                    FROM zotero.error_reports 
                    WHERE resolved = false 
                    AND timestamp < :old_threshold
                """)
                old_threshold = datetime.utcnow() - timedelta(days=7)
                result = await session.execute(old_errors_query, {"old_threshold": old_threshold})
                old_errors = result.scalar() or 0
                
                if old_errors > 0:
                    alerts.append(f"{old_errors} unresolved errors older than 7 days need attention")
                
                # Check for stuck sync operations
                stuck_sync_query = text("""
                    SELECT COUNT(*) 
                    FROM zotero.sync_operations 
                    WHERE status = 'in_progress' 
                    AND started_at < :stuck_threshold
                """)
                stuck_threshold = datetime.utcnow() - timedelta(hours=2)
                result = await session.execute(stuck_sync_query, {"stuck_threshold": stuck_threshold})
                stuck_syncs = result.scalar() or 0
                
                if stuck_syncs > 0:
                    alerts.append(f"{stuck_syncs} sync operations appear to be stuck")
                
                # Check for database maintenance needs
                # This would typically check table sizes, index usage, etc.
                alerts.append("Schedule routine database maintenance and optimization")
        
        except Exception as e:
            self.logger.error(f"Failed to generate maintenance alerts: {e}")
        
        return alerts


# Global admin dashboard service instance
admin_dashboard_service = ZoteroAdminDashboardService()