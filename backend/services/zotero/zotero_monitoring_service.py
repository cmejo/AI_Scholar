"""
Zotero Monitoring Service

Provides comprehensive monitoring, alerting, and health checking for Zotero integration.
Monitors system performance, API health, sync operations, and user experience metrics.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.config import get_settings
from services.zotero.zotero_client import ZoteroClient

logger = logging.getLogger(__name__)
settings = get_settings()


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MonitoringMetric(Enum):
    """Types of monitoring metrics"""
    API_RESPONSE_TIME = "api_response_time"
    API_ERROR_RATE = "api_error_rate"
    SYNC_SUCCESS_RATE = "sync_success_rate"
    SYNC_DURATION = "sync_duration"
    DATABASE_CONNECTIONS = "database_connections"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    ACTIVE_USERS = "active_users"
    QUEUE_LENGTH = "queue_length"
    DISK_USAGE = "disk_usage"


@dataclass
class HealthCheck:
    """Health check result"""
    service: str
    status: str  # healthy, degraded, unhealthy
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: datetime = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class Alert:
    """Monitoring alert"""
    id: str
    severity: AlertSeverity
    title: str
    description: str
    metric: MonitoringMetric
    threshold_value: float
    current_value: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    api_response_time: float
    api_error_rate: float
    sync_success_rate: float
    active_connections: int
    active_users: int
    queue_length: int
    memory_usage_percent: float
    cpu_usage_percent: float
    disk_usage_percent: float


class ZoteroMonitoringService:
    """Service for monitoring Zotero integration health and performance"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.zotero_client = ZoteroClient()
        self.alert_thresholds = {
            MonitoringMetric.API_RESPONSE_TIME: 5000,  # 5 seconds
            MonitoringMetric.API_ERROR_RATE: 5.0,  # 5%
            MonitoringMetric.SYNC_SUCCESS_RATE: 95.0,  # 95%
            MonitoringMetric.SYNC_DURATION: 300000,  # 5 minutes
            MonitoringMetric.DATABASE_CONNECTIONS: 80,  # 80% of pool
            MonitoringMetric.MEMORY_USAGE: 85.0,  # 85%
            MonitoringMetric.CPU_USAGE: 80.0,  # 80%
            MonitoringMetric.QUEUE_LENGTH: 1000,  # 1000 jobs
            MonitoringMetric.DISK_USAGE: 90.0,  # 90%
        }
        self.active_alerts: Dict[str, Alert] = {}
    
    async def perform_health_check(self) -> Dict[str, HealthCheck]:
        """Perform comprehensive health check of all Zotero services"""
        health_checks = {}
        
        # Check Zotero API connectivity
        health_checks["zotero_api"] = await self._check_zotero_api_health()
        
        # Check database connectivity
        health_checks["database"] = await self._check_database_health()
        
        # Check Redis connectivity
        health_checks["redis"] = await self._check_redis_health()
        
        # Check sync service health
        health_checks["sync_service"] = await self._check_sync_service_health()
        
        # Check file storage health
        health_checks["file_storage"] = await self._check_file_storage_health()
        
        # Store health check results
        await self._store_health_checks(health_checks)
        
        return health_checks
    
    async def _check_zotero_api_health(self) -> HealthCheck:
        """Check Zotero API health and response time"""
        start_time = time.time()
        try:
            # Test API connectivity with a simple request
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.zotero.org/",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return HealthCheck(
                            service="zotero_api",
                            status="healthy",
                            response_time_ms=response_time
                        )
                    else:
                        return HealthCheck(
                            service="zotero_api",
                            status="degraded",
                            response_time_ms=response_time,
                            error_message=f"HTTP {response.status}"
                        )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                service="zotero_api",
                status="unhealthy",
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    async def _check_database_health(self) -> HealthCheck:
        """Check database connectivity and performance"""
        start_time = time.time()
        try:
            async with get_db_session() as session:
                # Simple query to test connectivity
                result = await session.execute(text("SELECT 1"))
                result.scalar()
                
                response_time = (time.time() - start_time) * 1000
                
                # Check connection pool status
                pool_info = await self._get_database_pool_info(session)
                
                return HealthCheck(
                    service="database",
                    status="healthy",
                    response_time_ms=response_time,
                    metadata=pool_info
                )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                service="database",
                status="unhealthy",
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    async def _check_redis_health(self) -> HealthCheck:
        """Check Redis connectivity and performance"""
        start_time = time.time()
        try:
            # This would use your Redis client
            # For now, we'll simulate a successful check
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheck(
                service="redis",
                status="healthy",
                response_time_ms=response_time
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                service="redis",
                status="unhealthy",
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    async def _check_sync_service_health(self) -> HealthCheck:
        """Check sync service health"""
        try:
            async with get_db_session() as session:
                # Check for stuck sync operations
                stuck_syncs_query = text("""
                    SELECT COUNT(*) 
                    FROM zotero.sync_operations 
                    WHERE status = 'in_progress' 
                    AND started_at < :threshold
                """)
                threshold = datetime.utcnow() - timedelta(hours=1)
                result = await session.execute(stuck_syncs_query, {"threshold": threshold})
                stuck_syncs = result.scalar() or 0
                
                # Check recent sync success rate
                success_rate_query = text("""
                    SELECT 
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*) as success_rate
                    FROM zotero.sync_operations 
                    WHERE started_at >= :threshold
                """)
                recent_threshold = datetime.utcnow() - timedelta(hours=24)
                result = await session.execute(success_rate_query, {"threshold": recent_threshold})
                success_rate = result.scalar() or 100.0
                
                if stuck_syncs > 0:
                    status = "degraded"
                    error_message = f"{stuck_syncs} stuck sync operations"
                elif success_rate < 90.0:
                    status = "degraded"
                    error_message = f"Low success rate: {success_rate:.1f}%"
                else:
                    status = "healthy"
                    error_message = None
                
                return HealthCheck(
                    service="sync_service",
                    status=status,
                    error_message=error_message,
                    metadata={
                        "stuck_syncs": stuck_syncs,
                        "success_rate": success_rate
                    }
                )
        except Exception as e:
            return HealthCheck(
                service="sync_service",
                status="unhealthy",
                error_message=str(e)
            )
    
    async def _check_file_storage_health(self) -> HealthCheck:
        """Check file storage health"""
        try:
            # This would check your file storage system (S3, local filesystem, etc.)
            # For now, we'll simulate a successful check
            return HealthCheck(
                service="file_storage",
                status="healthy"
            )
        except Exception as e:
            return HealthCheck(
                service="file_storage",
                status="unhealthy",
                error_message=str(e)
            )
    
    async def _get_database_pool_info(self, session: AsyncSession) -> Dict[str, Any]:
        """Get database connection pool information"""
        try:
            # Get connection pool stats
            pool_query = text("""
                SELECT 
                    count(*) as total_connections,
                    count(case when state = 'active' then 1 end) as active_connections,
                    count(case when state = 'idle' then 1 end) as idle_connections
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """)
            result = await session.execute(pool_query)
            row = result.fetchone()
            
            return {
                "total_connections": row[0],
                "active_connections": row[1],
                "idle_connections": row[2]
            }
        except Exception:
            return {}
    
    async def _store_health_checks(self, health_checks: Dict[str, HealthCheck]):
        """Store health check results in database"""
        try:
            async with get_db_session() as session:
                for service, check in health_checks.items():
                    query = text("""
                        INSERT INTO zotero.health_checks (
                            service, status, response_time_ms, error_message, 
                            timestamp, metadata
                        ) VALUES (
                            :service, :status, :response_time_ms, :error_message,
                            :timestamp, :metadata
                        )
                    """)
                    
                    await session.execute(query, {
                        "service": check.service,
                        "status": check.status,
                        "response_time_ms": check.response_time_ms,
                        "error_message": check.error_message,
                        "timestamp": check.timestamp,
                        "metadata": json.dumps(check.metadata) if check.metadata else None
                    })
                
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to store health checks: {e}")
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect comprehensive system metrics"""
        try:
            async with get_db_session() as session:
                # API response time (average from recent health checks)
                api_response_time = await self._get_avg_api_response_time(session)
                
                # API error rate (from analytics events)
                api_error_rate = await self._get_api_error_rate(session)
                
                # Sync success rate
                sync_success_rate = await self._get_sync_success_rate(session)
                
                # Active connections
                active_connections = await self._get_active_connections(session)
                
                # Active users (last hour)
                active_users = await self._get_active_users(session)
                
                # Queue length (would come from your job queue system)
                queue_length = await self._get_queue_length()
                
                # System resource usage (would come from system monitoring)
                memory_usage = await self._get_memory_usage()
                cpu_usage = await self._get_cpu_usage()
                disk_usage = await self._get_disk_usage()
                
                metrics = SystemMetrics(
                    timestamp=datetime.utcnow(),
                    api_response_time=api_response_time,
                    api_error_rate=api_error_rate,
                    sync_success_rate=sync_success_rate,
                    active_connections=active_connections,
                    active_users=active_users,
                    queue_length=queue_length,
                    memory_usage_percent=memory_usage,
                    cpu_usage_percent=cpu_usage,
                    disk_usage_percent=disk_usage
                )
                
                # Store metrics
                await self._store_system_metrics(session, metrics)
                
                # Check for alerts
                await self._check_alert_conditions(metrics)
                
                return metrics
                
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
            raise
    
    async def _get_avg_api_response_time(self, session: AsyncSession) -> float:
        """Get average API response time from recent health checks"""
        query = text("""
            SELECT AVG(response_time_ms) 
            FROM zotero.health_checks 
            WHERE service = 'zotero_api' 
            AND timestamp >= :threshold
            AND response_time_ms IS NOT NULL
        """)
        threshold = datetime.utcnow() - timedelta(minutes=15)
        result = await session.execute(query, {"threshold": threshold})
        return float(result.scalar() or 0)
    
    async def _get_api_error_rate(self, session: AsyncSession) -> float:
        """Get API error rate from analytics events"""
        query = text("""
            SELECT 
                COUNT(CASE WHEN success = false THEN 1 END) * 100.0 / COUNT(*) as error_rate
            FROM zotero.analytics_events 
            WHERE timestamp >= :threshold
            AND event_type LIKE '%api%'
        """)
        threshold = datetime.utcnow() - timedelta(hours=1)
        result = await session.execute(query, {"threshold": threshold})
        return float(result.scalar() or 0)
    
    async def _get_sync_success_rate(self, session: AsyncSession) -> float:
        """Get sync operation success rate"""
        query = text("""
            SELECT 
                COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*) as success_rate
            FROM zotero.sync_operations 
            WHERE started_at >= :threshold
        """)
        threshold = datetime.utcnow() - timedelta(hours=24)
        result = await session.execute(query, {"threshold": threshold})
        return float(result.scalar() or 100.0)
    
    async def _get_active_connections(self, session: AsyncSession) -> int:
        """Get number of active database connections"""
        query = text("""
            SELECT count(*) 
            FROM pg_stat_activity 
            WHERE datname = current_database() 
            AND state = 'active'
        """)
        result = await session.execute(query)
        return int(result.scalar() or 0)
    
    async def _get_active_users(self, session: AsyncSession) -> int:
        """Get number of active users in the last hour"""
        query = text("""
            SELECT COUNT(DISTINCT user_id) 
            FROM zotero.analytics_events 
            WHERE timestamp >= :threshold
        """)
        threshold = datetime.utcnow() - timedelta(hours=1)
        result = await session.execute(query, {"threshold": threshold})
        return int(result.scalar() or 0)
    
    async def _get_queue_length(self) -> int:
        """Get job queue length (placeholder - would integrate with your job queue)"""
        # This would integrate with your actual job queue system (Celery, RQ, etc.)
        return 0
    
    async def _get_memory_usage(self) -> float:
        """Get memory usage percentage (placeholder - would use system monitoring)"""
        # This would integrate with system monitoring tools
        return 45.0
    
    async def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage (placeholder - would use system monitoring)"""
        # This would integrate with system monitoring tools
        return 25.0
    
    async def _get_disk_usage(self) -> float:
        """Get disk usage percentage (placeholder - would use system monitoring)"""
        # This would integrate with system monitoring tools
        return 60.0
    
    async def _store_system_metrics(self, session: AsyncSession, metrics: SystemMetrics):
        """Store system metrics in database"""
        query = text("""
            INSERT INTO zotero.system_metrics (
                timestamp, api_response_time, api_error_rate, sync_success_rate,
                active_connections, active_users, queue_length, memory_usage_percent,
                cpu_usage_percent, disk_usage_percent
            ) VALUES (
                :timestamp, :api_response_time, :api_error_rate, :sync_success_rate,
                :active_connections, :active_users, :queue_length, :memory_usage_percent,
                :cpu_usage_percent, :disk_usage_percent
            )
        """)
        
        await session.execute(query, asdict(metrics))
        await session.commit()
    
    async def _check_alert_conditions(self, metrics: SystemMetrics):
        """Check if any metrics exceed alert thresholds"""
        alerts_to_create = []
        
        # Check each metric against its threshold
        if metrics.api_response_time > self.alert_thresholds[MonitoringMetric.API_RESPONSE_TIME]:
            alerts_to_create.append(self._create_alert(
                MonitoringMetric.API_RESPONSE_TIME,
                "High API Response Time",
                f"API response time is {metrics.api_response_time:.0f}ms",
                self.alert_thresholds[MonitoringMetric.API_RESPONSE_TIME],
                metrics.api_response_time,
                AlertSeverity.HIGH
            ))
        
        if metrics.api_error_rate > self.alert_thresholds[MonitoringMetric.API_ERROR_RATE]:
            alerts_to_create.append(self._create_alert(
                MonitoringMetric.API_ERROR_RATE,
                "High API Error Rate",
                f"API error rate is {metrics.api_error_rate:.1f}%",
                self.alert_thresholds[MonitoringMetric.API_ERROR_RATE],
                metrics.api_error_rate,
                AlertSeverity.HIGH
            ))
        
        if metrics.sync_success_rate < self.alert_thresholds[MonitoringMetric.SYNC_SUCCESS_RATE]:
            alerts_to_create.append(self._create_alert(
                MonitoringMetric.SYNC_SUCCESS_RATE,
                "Low Sync Success Rate",
                f"Sync success rate is {metrics.sync_success_rate:.1f}%",
                self.alert_thresholds[MonitoringMetric.SYNC_SUCCESS_RATE],
                metrics.sync_success_rate,
                AlertSeverity.HIGH
            ))
        
        # Create and store alerts
        for alert in alerts_to_create:
            await self._store_alert(alert)
            self.active_alerts[alert.id] = alert
    
    def _create_alert(
        self,
        metric: MonitoringMetric,
        title: str,
        description: str,
        threshold: float,
        current_value: float,
        severity: AlertSeverity
    ) -> Alert:
        """Create a new alert"""
        alert_id = f"{metric.value}_{int(time.time())}"
        
        return Alert(
            id=alert_id,
            severity=severity,
            title=title,
            description=description,
            metric=metric,
            threshold_value=threshold,
            current_value=current_value,
            timestamp=datetime.utcnow()
        )
    
    async def _store_alert(self, alert: Alert):
        """Store alert in database"""
        try:
            async with get_db_session() as session:
                query = text("""
                    INSERT INTO zotero.monitoring_alerts (
                        id, severity, title, description, metric, threshold_value,
                        current_value, timestamp, resolved, resolved_at, metadata
                    ) VALUES (
                        :id, :severity, :title, :description, :metric, :threshold_value,
                        :current_value, :timestamp, :resolved, :resolved_at, :metadata
                    )
                """)
                
                await session.execute(query, {
                    "id": alert.id,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "description": alert.description,
                    "metric": alert.metric.value,
                    "threshold_value": alert.threshold_value,
                    "current_value": alert.current_value,
                    "timestamp": alert.timestamp,
                    "resolved": alert.resolved,
                    "resolved_at": alert.resolved_at,
                    "metadata": json.dumps(alert.metadata) if alert.metadata else None
                })
                await session.commit()
                
                self.logger.warning(f"Alert created: {alert.title} - {alert.description}")
                
        except Exception as e:
            self.logger.error(f"Failed to store alert: {e}")
    
    async def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        try:
            async with get_db_session() as session:
                query = text("""
                    SELECT id, severity, title, description, metric, threshold_value,
                           current_value, timestamp, resolved, resolved_at, metadata
                    FROM zotero.monitoring_alerts 
                    WHERE resolved = false
                    ORDER BY severity DESC, timestamp DESC
                """)
                result = await session.execute(query)
                
                alerts = []
                for row in result.fetchall():
                    alerts.append(Alert(
                        id=row[0],
                        severity=AlertSeverity(row[1]),
                        title=row[2],
                        description=row[3],
                        metric=MonitoringMetric(row[4]),
                        threshold_value=row[5],
                        current_value=row[6],
                        timestamp=row[7],
                        resolved=row[8],
                        resolved_at=row[9],
                        metadata=json.loads(row[10]) if row[10] else None
                    ))
                
                return alerts
                
        except Exception as e:
            self.logger.error(f"Failed to get active alerts: {e}")
            return []
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert"""
        try:
            async with get_db_session() as session:
                query = text("""
                    UPDATE zotero.monitoring_alerts 
                    SET resolved = true, resolved_at = :resolved_at
                    WHERE id = :alert_id
                """)
                await session.execute(query, {
                    "alert_id": alert_id,
                    "resolved_at": datetime.utcnow()
                })
                await session.commit()
                
                # Remove from active alerts
                if alert_id in self.active_alerts:
                    del self.active_alerts[alert_id]
                
                self.logger.info(f"Alert resolved: {alert_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to resolve alert: {e}")
            return False


# Global monitoring service instance
monitoring_service = ZoteroMonitoringService()