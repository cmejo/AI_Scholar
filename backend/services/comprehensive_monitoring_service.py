"""
Comprehensive Monitoring Service for AI Scholar Advanced RAG
Tracks feature usage, performance metrics, and business analytics
"""

import json
import logging
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from collections import defaultdict, deque
import psutil
import redis
from sqlalchemy import Column, String, DateTime, Float, Integer, JSON, Boolean, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.core.database import get_db_session
from backend.core.redis_client import redis_client

logger = logging.getLogger(__name__)

Base = declarative_base()

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FeatureCategory(Enum):
    MOBILE = "mobile"
    VOICE = "voice"
    INTEGRATION = "integration"
    EDUCATIONAL = "educational"
    ENTERPRISE = "enterprise"
    INTERACTIVE = "interactive"
    OPPORTUNITY = "opportunity"
    CORE = "core"

@dataclass
class MetricData:
    """Metric data structure"""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    tags: Dict[str, str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    metric_name: str
    condition: str  # >, <, ==, !=
    threshold: float
    severity: AlertSeverity
    duration_minutes: int = 5
    notification_channels: List[str] = None

class SystemMetrics(Base):
    """System metrics storage"""
    __tablename__ = "system_metrics"
    
    id = Column(String, primary_key=True)
    metric_name = Column(String, nullable=False)
    metric_type = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    tags = Column(JSON, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)
    environment = Column(String, default="production")

class FeatureUsageMetrics(Base):
    """Feature usage tracking"""
    __tablename__ = "feature_usage_metrics"
    
    id = Column(String, primary_key=True)
    feature_name = Column(String, nullable=False)
    feature_category = Column(String, nullable=False)
    user_id = Column(String)
    session_id = Column(String)
    action = Column(String, nullable=False)
    duration_ms = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    metadata = Column(JSON, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)
    environment = Column(String, default="production")

class PerformanceMetrics(Base):
    """Performance metrics storage"""
    __tablename__ = "performance_metrics"
    
    id = Column(String, primary_key=True)
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    response_time_ms = Column(Float, nullable=False)
    status_code = Column(Integer, nullable=False)
    user_id = Column(String)
    user_agent = Column(String)
    ip_address = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    environment = Column(String, default="production")

class IntegrationHealthMetrics(Base):
    """Integration health tracking"""
    __tablename__ = "integration_health_metrics"
    
    id = Column(String, primary_key=True)
    integration_name = Column(String, nullable=False)
    integration_type = Column(String, nullable=False)
    status = Column(String, nullable=False)  # healthy, degraded, unhealthy
    response_time_ms = Column(Float)
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    environment = Column(String, default="production")

class BusinessMetrics(Base):
    """Business metrics tracking"""
    __tablename__ = "business_metrics"
    
    id = Column(String, primary_key=True)
    metric_name = Column(String, nullable=False)
    metric_category = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String)
    dimensions = Column(JSON, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)
    environment = Column(String, default="production")

class ComprehensiveMonitoringService:
    """Comprehensive monitoring service"""
    
    def __init__(self):
        self.redis_client = redis_client
        self.metrics_buffer = defaultdict(deque)
        self.alert_rules = []
        self.performance_thresholds = {
            "response_time_p95": 2000,  # 2 seconds
            "error_rate": 0.05,  # 5%
            "cpu_usage": 80,  # 80%
            "memory_usage": 85,  # 85%
            "disk_usage": 90  # 90%
        }
        
        # Initialize alert rules
        self._initialize_alert_rules()
    
    def _initialize_alert_rules(self):
        """Initialize default alert rules"""
        self.alert_rules = [
            AlertRule(
                name="high_error_rate",
                metric_name="error_rate",
                condition=">",
                threshold=0.05,
                severity=AlertSeverity.HIGH,
                duration_minutes=5,
                notification_channels=["slack", "email"]
            ),
            AlertRule(
                name="high_response_time",
                metric_name="response_time_p95",
                condition=">",
                threshold=2000,
                severity=AlertSeverity.MEDIUM,
                duration_minutes=10,
                notification_channels=["slack"]
            ),
            AlertRule(
                name="integration_failure",
                metric_name="integration_health",
                condition="==",
                threshold=0,  # 0 = unhealthy
                severity=AlertSeverity.CRITICAL,
                duration_minutes=1,
                notification_channels=["slack", "email", "pagerduty"]
            ),
            AlertRule(
                name="high_cpu_usage",
                metric_name="cpu_usage",
                condition=">",
                threshold=80,
                severity=AlertSeverity.MEDIUM,
                duration_minutes=15,
                notification_channels=["slack"]
            ),
            AlertRule(
                name="low_disk_space",
                metric_name="disk_usage",
                condition=">",
                threshold=90,
                severity=AlertSeverity.HIGH,
                duration_minutes=5,
                notification_channels=["slack", "email"]
            )
        ]
    
    def _generate_metric_id(self, metric_name: str) -> str:
        """Generate unique metric ID"""
        return hashlib.md5(f"{metric_name}_{datetime.utcnow().isoformat()}".encode()).hexdigest()
    
    def record_metric(self, metric: MetricData, environment: str = "production"):
        """Record a metric"""
        try:
            metric_id = self._generate_metric_id(metric.name)
            
            with get_db_session() as db:
                system_metric = SystemMetrics(
                    id=metric_id,
                    metric_name=metric.name,
                    metric_type=metric.metric_type.value,
                    value=metric.value,
                    tags=metric.tags or {},
                    timestamp=metric.timestamp,
                    environment=environment
                )
                db.add(system_metric)
                db.commit()
            
            # Also store in Redis for real-time access
            redis_key = f"metric:{metric.name}:{environment}"
            self.redis_client.lpush(redis_key, json.dumps({
                "value": metric.value,
                "timestamp": metric.timestamp.isoformat(),
                "tags": metric.tags or {}
            }))
            self.redis_client.ltrim(redis_key, 0, 999)  # Keep last 1000 values
            
        except Exception as e:
            logger.error(f"Error recording metric {metric.name}: {str(e)}")
    
    def track_feature_usage(self, feature_name: str, category: FeatureCategory, 
                          action: str, user_id: str = None, session_id: str = None,
                          duration_ms: int = None, success: bool = True,
                          error_message: str = None, metadata: Dict[str, Any] = None,
                          environment: str = "production"):
        """Track feature usage"""
        try:
            usage_id = self._generate_metric_id(f"usage_{feature_name}_{action}")
            
            with get_db_session() as db:
                usage_metric = FeatureUsageMetrics(
                    id=usage_id,
                    feature_name=feature_name,
                    feature_category=category.value,
                    user_id=user_id,
                    session_id=session_id,
                    action=action,
                    duration_ms=duration_ms,
                    success=success,
                    error_message=error_message,
                    metadata=metadata or {},
                    environment=environment
                )
                db.add(usage_metric)
                db.commit()
            
            # Update real-time counters
            redis_key = f"feature_usage:{feature_name}:{action}:{environment}"
            self.redis_client.incr(redis_key)
            self.redis_client.expire(redis_key, 86400)  # 24 hours
            
        except Exception as e:
            logger.error(f"Error tracking feature usage: {str(e)}")
    
    def track_performance(self, endpoint: str, method: str, response_time_ms: float,
                         status_code: int, user_id: str = None, user_agent: str = None,
                         ip_address: str = None, environment: str = "production"):
        """Track performance metrics"""
        try:
            perf_id = self._generate_metric_id(f"perf_{endpoint}_{method}")
            
            with get_db_session() as db:
                perf_metric = PerformanceMetrics(
                    id=perf_id,
                    endpoint=endpoint,
                    method=method,
                    response_time_ms=response_time_ms,
                    status_code=status_code,
                    user_id=user_id,
                    user_agent=user_agent,
                    ip_address=ip_address,
                    environment=environment
                )
                db.add(perf_metric)
                db.commit()
            
            # Update real-time performance metrics
            redis_key = f"performance:{endpoint}:{method}:{environment}"
            self.redis_client.lpush(redis_key, json.dumps({
                "response_time_ms": response_time_ms,
                "status_code": status_code,
                "timestamp": datetime.utcnow().isoformat()
            }))
            self.redis_client.ltrim(redis_key, 0, 999)
            
        except Exception as e:
            logger.error(f"Error tracking performance: {str(e)}")
    
    def track_integration_health(self, integration_name: str, integration_type: str,
                               status: str, response_time_ms: float = None,
                               error_count: int = 0, last_error: str = None,
                               environment: str = "production"):
        """Track integration health"""
        try:
            health_id = self._generate_metric_id(f"health_{integration_name}")
            
            with get_db_session() as db:
                health_metric = IntegrationHealthMetrics(
                    id=health_id,
                    integration_name=integration_name,
                    integration_type=integration_type,
                    status=status,
                    response_time_ms=response_time_ms,
                    error_count=error_count,
                    last_error=last_error,
                    environment=environment
                )
                db.add(health_metric)
                db.commit()
            
            # Update real-time health status
            redis_key = f"integration_health:{integration_name}:{environment}"
            self.redis_client.hset(redis_key, mapping={
                "status": status,
                "response_time_ms": response_time_ms or 0,
                "error_count": error_count,
                "last_updated": datetime.utcnow().isoformat()
            })
            self.redis_client.expire(redis_key, 3600)  # 1 hour
            
        except Exception as e:
            logger.error(f"Error tracking integration health: {str(e)}")
    
    def track_business_metric(self, metric_name: str, category: str, value: float,
                            unit: str = None, dimensions: Dict[str, Any] = None,
                            environment: str = "production"):
        """Track business metrics"""
        try:
            business_id = self._generate_metric_id(f"business_{metric_name}")
            
            with get_db_session() as db:
                business_metric = BusinessMetrics(
                    id=business_id,
                    metric_name=metric_name,
                    metric_category=category,
                    value=value,
                    unit=unit,
                    dimensions=dimensions or {},
                    environment=environment
                )
                db.add(business_metric)
                db.commit()
            
            # Update real-time business metrics
            redis_key = f"business_metric:{metric_name}:{category}:{environment}"
            self.redis_client.set(redis_key, json.dumps({
                "value": value,
                "unit": unit,
                "dimensions": dimensions or {},
                "timestamp": datetime.utcnow().isoformat()
            }), ex=3600)
            
        except Exception as e:
            logger.error(f"Error tracking business metric: {str(e)}")
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            # Get system resource metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get service health from Redis
            services_health = {}
            service_keys = self.redis_client.keys("integration_health:*:production")
            
            for key in service_keys:
                service_name = key.decode().split(':')[1]
                health_data = self.redis_client.hgetall(key)
                if health_data:
                    services_health[service_name] = {
                        "status": health_data.get(b"status", b"unknown").decode(),
                        "response_time_ms": float(health_data.get(b"response_time_ms", 0)),
                        "error_count": int(health_data.get(b"error_count", 0)),
                        "last_updated": health_data.get(b"last_updated", b"").decode()
                    }
            
            # Calculate overall health score
            health_score = self._calculate_health_score(cpu_percent, memory.percent, 
                                                      disk.percent, services_health)
            
            return {
                "overall_status": self._get_status_from_score(health_score),
                "health_score": health_score,
                "timestamp": datetime.utcnow().isoformat(),
                "system_resources": {
                    "cpu_usage_percent": cpu_percent,
                    "memory_usage_percent": memory.percent,
                    "disk_usage_percent": disk.percent,
                    "available_memory_gb": round(memory.available / (1024**3), 2),
                    "free_disk_gb": round(disk.free / (1024**3), 2)
                },
                "services": services_health,
                "active_alerts": self._get_active_alerts()
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            return {
                "overall_status": "unknown",
                "health_score": 0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _calculate_health_score(self, cpu_percent: float, memory_percent: float,
                              disk_percent: float, services_health: Dict[str, Any]) -> float:
        """Calculate overall health score (0-100)"""
        # System resource score (40% weight)
        resource_score = 100
        if cpu_percent > 80:
            resource_score -= (cpu_percent - 80) * 2
        if memory_percent > 85:
            resource_score -= (memory_percent - 85) * 3
        if disk_percent > 90:
            resource_score -= (disk_percent - 90) * 5
        
        resource_score = max(0, min(100, resource_score)) * 0.4
        
        # Services health score (60% weight)
        if not services_health:
            services_score = 100 * 0.6
        else:
            healthy_services = sum(1 for service in services_health.values() 
                                 if service["status"] == "healthy")
            services_score = (healthy_services / len(services_health)) * 100 * 0.6
        
        return round(resource_score + services_score, 1)
    
    def _get_status_from_score(self, score: float) -> str:
        """Convert health score to status"""
        if score >= 90:
            return "healthy"
        elif score >= 70:
            return "degraded"
        elif score >= 50:
            return "unhealthy"
        else:
            return "critical"
    
    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts"""
        # This would integrate with your alerting system
        # For now, return empty list
        return []
    
    def get_feature_usage_stats(self, feature_name: str = None, category: FeatureCategory = None,
                              hours: int = 24, environment: str = "production") -> Dict[str, Any]:
        """Get feature usage statistics"""
        try:
            with get_db_session() as db:
                start_time = datetime.utcnow() - timedelta(hours=hours)
                
                query = db.query(FeatureUsageMetrics).filter(
                    FeatureUsageMetrics.timestamp >= start_time,
                    FeatureUsageMetrics.environment == environment
                )
                
                if feature_name:
                    query = query.filter(FeatureUsageMetrics.feature_name == feature_name)
                
                if category:
                    query = query.filter(FeatureUsageMetrics.feature_category == category.value)
                
                usage_records = query.all()
                
                # Calculate statistics
                total_usage = len(usage_records)
                successful_usage = sum(1 for record in usage_records if record.success)
                unique_users = len(set(record.user_id for record in usage_records if record.user_id))
                
                # Group by feature and action
                feature_breakdown = defaultdict(lambda: defaultdict(int))
                for record in usage_records:
                    feature_breakdown[record.feature_name][record.action] += 1
                
                return {
                    "period_hours": hours,
                    "total_usage": total_usage,
                    "successful_usage": successful_usage,
                    "success_rate": (successful_usage / total_usage * 100) if total_usage > 0 else 0,
                    "unique_users": unique_users,
                    "feature_breakdown": dict(feature_breakdown),
                    "environment": environment,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting feature usage stats: {str(e)}")
            return {"error": str(e)}
    
    def get_performance_metrics(self, endpoint: str = None, hours: int = 24,
                              environment: str = "production") -> Dict[str, Any]:
        """Get performance metrics"""
        try:
            with get_db_session() as db:
                start_time = datetime.utcnow() - timedelta(hours=hours)
                
                query = db.query(PerformanceMetrics).filter(
                    PerformanceMetrics.timestamp >= start_time,
                    PerformanceMetrics.environment == environment
                )
                
                if endpoint:
                    query = query.filter(PerformanceMetrics.endpoint == endpoint)
                
                perf_records = query.all()
                
                if not perf_records:
                    return {"error": "No performance data found"}
                
                # Calculate metrics
                response_times = [record.response_time_ms for record in perf_records]
                status_codes = [record.status_code for record in perf_records]
                
                response_times.sort()
                total_requests = len(response_times)
                error_requests = sum(1 for code in status_codes if code >= 400)
                
                return {
                    "period_hours": hours,
                    "total_requests": total_requests,
                    "error_requests": error_requests,
                    "error_rate": (error_requests / total_requests * 100) if total_requests > 0 else 0,
                    "response_time_ms": {
                        "min": min(response_times),
                        "max": max(response_times),
                        "avg": sum(response_times) / len(response_times),
                        "p50": response_times[int(len(response_times) * 0.5)],
                        "p95": response_times[int(len(response_times) * 0.95)],
                        "p99": response_times[int(len(response_times) * 0.99)]
                    },
                    "environment": environment,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {"error": str(e)}
    
    def get_integration_health_status(self, environment: str = "production") -> Dict[str, Any]:
        """Get integration health status"""
        try:
            integrations = {}
            service_keys = self.redis_client.keys(f"integration_health:*:{environment}")
            
            for key in service_keys:
                service_name = key.decode().split(':')[1]
                health_data = self.redis_client.hgetall(key)
                
                if health_data:
                    integrations[service_name] = {
                        "status": health_data.get(b"status", b"unknown").decode(),
                        "response_time_ms": float(health_data.get(b"response_time_ms", 0)),
                        "error_count": int(health_data.get(b"error_count", 0)),
                        "last_updated": health_data.get(b"last_updated", b"").decode()
                    }
            
            # Calculate overall integration health
            if integrations:
                healthy_count = sum(1 for integration in integrations.values() 
                                  if integration["status"] == "healthy")
                overall_health = (healthy_count / len(integrations)) * 100
            else:
                overall_health = 100
            
            return {
                "overall_health_percentage": overall_health,
                "total_integrations": len(integrations),
                "healthy_integrations": sum(1 for integration in integrations.values() 
                                          if integration["status"] == "healthy"),
                "integrations": integrations,
                "environment": environment,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting integration health status: {str(e)}")
            return {"error": str(e)}
    
    def get_business_metrics_summary(self, category: str = None, hours: int = 24,
                                   environment: str = "production") -> Dict[str, Any]:
        """Get business metrics summary"""
        try:
            with get_db_session() as db:
                start_time = datetime.utcnow() - timedelta(hours=hours)
                
                query = db.query(BusinessMetrics).filter(
                    BusinessMetrics.timestamp >= start_time,
                    BusinessMetrics.environment == environment
                )
                
                if category:
                    query = query.filter(BusinessMetrics.metric_category == category)
                
                business_records = query.all()
                
                # Group metrics by category and name
                metrics_summary = defaultdict(lambda: defaultdict(list))
                for record in business_records:
                    metrics_summary[record.metric_category][record.metric_name].append({
                        "value": record.value,
                        "unit": record.unit,
                        "dimensions": record.dimensions,
                        "timestamp": record.timestamp.isoformat()
                    })
                
                return {
                    "period_hours": hours,
                    "metrics_summary": dict(metrics_summary),
                    "environment": environment,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting business metrics summary: {str(e)}")
            return {"error": str(e)}
    
    # Enhanced Feature Usage Analytics
    def get_detailed_feature_analytics(self, feature_category: FeatureCategory = None, 
                                     hours: int = 24, environment: str = "production") -> Dict[str, Any]:
        """Get detailed feature usage analytics with user behavior tracking"""
        try:
            with get_db_session() as db:
                start_time = datetime.utcnow() - timedelta(hours=hours)
                
                query = db.query(FeatureUsageMetrics).filter(
                    FeatureUsageMetrics.timestamp >= start_time,
                    FeatureUsageMetrics.environment == environment
                )
                
                if feature_category:
                    query = query.filter(FeatureUsageMetrics.feature_category == feature_category.value)
                
                usage_records = query.all()
                
                # User behavior analytics
                user_sessions = defaultdict(list)
                feature_funnel = defaultdict(lambda: defaultdict(int))
                error_patterns = defaultdict(list)
                
                for record in usage_records:
                    if record.user_id:
                        user_sessions[record.user_id].append(record)
                    
                    # Track feature funnel
                    feature_funnel[record.feature_name][record.action] += 1
                    
                    # Track errors
                    if not record.success and record.error_message:
                        error_patterns[record.feature_name].append({
                            "error": record.error_message,
                            "timestamp": record.timestamp.isoformat(),
                            "action": record.action
                        })
                
                # Calculate user engagement metrics
                session_durations = []
                user_retention = {}
                
                for user_id, sessions in user_sessions.items():
                    if len(sessions) > 1:
                        sessions.sort(key=lambda x: x.timestamp)
                        session_duration = (sessions[-1].timestamp - sessions[0].timestamp).total_seconds()
                        session_durations.append(session_duration)
                        
                        # Track user retention (users who returned)
                        unique_days = len(set(s.timestamp.date() for s in sessions))
                        user_retention[user_id] = unique_days
                
                # Feature adoption rates
                feature_adoption = {}
                for feature_name, actions in feature_funnel.items():
                    total_starts = actions.get('start', 0) or actions.get('access', 0) or sum(actions.values())
                    total_completions = actions.get('complete', 0) or actions.get('success', 0)
                    
                    if total_starts > 0:
                        feature_adoption[feature_name] = {
                            "starts": total_starts,
                            "completions": total_completions,
                            "completion_rate": (total_completions / total_starts) * 100,
                            "actions": dict(actions)
                        }
                
                return {
                    "period_hours": hours,
                    "total_users": len(user_sessions),
                    "total_sessions": len(usage_records),
                    "average_session_duration_seconds": sum(session_durations) / len(session_durations) if session_durations else 0,
                    "user_retention": {
                        "returning_users": len([u for u, days in user_retention.items() if days > 1]),
                        "average_days_active": sum(user_retention.values()) / len(user_retention) if user_retention else 0
                    },
                    "feature_adoption": feature_adoption,
                    "error_patterns": dict(error_patterns),
                    "top_features": sorted(feature_adoption.items(), key=lambda x: x[1]["starts"], reverse=True)[:10],
                    "environment": environment,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting detailed feature analytics: {str(e)}")
            return {"error": str(e)}
    
    # Voice Processing Performance Monitoring
    def track_voice_performance(self, operation: str, language: str, duration_ms: float,
                              accuracy_score: float = None, user_id: str = None,
                              error_message: str = None, environment: str = "production"):
        """Track voice processing performance metrics"""
        try:
            # Track as feature usage
            self.track_feature_usage(
                feature_name="voice_processing",
                category=FeatureCategory.VOICE,
                action=operation,
                user_id=user_id,
                duration_ms=int(duration_ms),
                success=error_message is None,
                error_message=error_message,
                metadata={
                    "language": language,
                    "accuracy_score": accuracy_score,
                    "operation": operation
                },
                environment=environment
            )
            
            # Track performance metrics
            self.track_performance(
                endpoint=f"/voice/{operation}",
                method="POST",
                response_time_ms=duration_ms,
                status_code=200 if error_message is None else 500,
                user_id=user_id,
                environment=environment
            )
            
            # Track business metrics
            self.track_business_metric(
                metric_name="voice_processing_duration",
                category="voice_performance",
                value=duration_ms,
                unit="milliseconds",
                dimensions={
                    "operation": operation,
                    "language": language,
                    "success": error_message is None
                },
                environment=environment
            )
            
            if accuracy_score is not None:
                self.track_business_metric(
                    metric_name="voice_accuracy_score",
                    category="voice_performance",
                    value=accuracy_score,
                    unit="percentage",
                    dimensions={
                        "operation": operation,
                        "language": language
                    },
                    environment=environment
                )
                
        except Exception as e:
            logger.error(f"Error tracking voice performance: {str(e)}")
    
    # Mobile Performance Monitoring
    def track_mobile_performance(self, device_type: str, operation: str, duration_ms: float,
                               network_type: str = None, battery_level: int = None,
                               user_id: str = None, error_message: str = None,
                               environment: str = "production"):
        """Track mobile performance metrics"""
        try:
            # Track as feature usage
            self.track_feature_usage(
                feature_name="mobile_operation",
                category=FeatureCategory.MOBILE,
                action=operation,
                user_id=user_id,
                duration_ms=int(duration_ms),
                success=error_message is None,
                error_message=error_message,
                metadata={
                    "device_type": device_type,
                    "network_type": network_type,
                    "battery_level": battery_level,
                    "operation": operation
                },
                environment=environment
            )
            
            # Track business metrics
            self.track_business_metric(
                metric_name="mobile_operation_duration",
                category="mobile_performance",
                value=duration_ms,
                unit="milliseconds",
                dimensions={
                    "device_type": device_type,
                    "operation": operation,
                    "network_type": network_type,
                    "success": error_message is None
                },
                environment=environment
            )
            
            if battery_level is not None:
                self.track_business_metric(
                    metric_name="mobile_battery_usage",
                    category="mobile_performance",
                    value=battery_level,
                    unit="percentage",
                    dimensions={
                        "device_type": device_type,
                        "operation": operation
                    },
                    environment=environment
                )
                
        except Exception as e:
            logger.error(f"Error tracking mobile performance: {str(e)}")
    
    # Enhanced Integration Health Monitoring
    def get_integration_health_details(self, environment: str = "production") -> Dict[str, Any]:
        """Get detailed integration health with SLA tracking"""
        try:
            with get_db_session() as db:
                # Get recent integration health data
                start_time = datetime.utcnow() - timedelta(hours=24)
                
                health_records = db.query(IntegrationHealthMetrics).filter(
                    IntegrationHealthMetrics.timestamp >= start_time,
                    IntegrationHealthMetrics.environment == environment
                ).all()
                
                # Group by integration
                integration_stats = defaultdict(lambda: {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "response_times": [],
                    "error_messages": [],
                    "uptime_percentage": 0,
                    "sla_breaches": 0
                })
                
                for record in health_records:
                    stats = integration_stats[record.integration_name]
                    stats["total_requests"] += 1
                    
                    if record.status == "healthy":
                        stats["successful_requests"] += 1
                    else:
                        stats["failed_requests"] += 1
                        if record.last_error:
                            stats["error_messages"].append({
                                "error": record.last_error,
                                "timestamp": record.timestamp.isoformat()
                            })
                    
                    if record.response_time_ms:
                        stats["response_times"].append(record.response_time_ms)
                        
                        # Check SLA breach (assuming 2000ms SLA)
                        if record.response_time_ms > 2000:
                            stats["sla_breaches"] += 1
                
                # Calculate final metrics
                integration_health = {}
                for integration_name, stats in integration_stats.items():
                    if stats["total_requests"] > 0:
                        uptime = (stats["successful_requests"] / stats["total_requests"]) * 100
                        avg_response_time = sum(stats["response_times"]) / len(stats["response_times"]) if stats["response_times"] else 0
                        p95_response_time = sorted(stats["response_times"])[int(len(stats["response_times"]) * 0.95)] if stats["response_times"] else 0
                        
                        integration_health[integration_name] = {
                            "uptime_percentage": uptime,
                            "total_requests": stats["total_requests"],
                            "success_rate": uptime,
                            "average_response_time_ms": avg_response_time,
                            "p95_response_time_ms": p95_response_time,
                            "sla_breaches": stats["sla_breaches"],
                            "sla_compliance": ((stats["total_requests"] - stats["sla_breaches"]) / stats["total_requests"]) * 100,
                            "recent_errors": stats["error_messages"][-5:],  # Last 5 errors
                            "status": "healthy" if uptime >= 99.0 else "degraded" if uptime >= 95.0 else "unhealthy"
                        }
                
                # Overall integration health score
                if integration_health:
                    overall_uptime = sum(h["uptime_percentage"] for h in integration_health.values()) / len(integration_health)
                    overall_sla_compliance = sum(h["sla_compliance"] for h in integration_health.values()) / len(integration_health)
                else:
                    overall_uptime = 100
                    overall_sla_compliance = 100
                
                return {
                    "overall_health": {
                        "uptime_percentage": overall_uptime,
                        "sla_compliance": overall_sla_compliance,
                        "total_integrations": len(integration_health),
                        "healthy_integrations": len([h for h in integration_health.values() if h["status"] == "healthy"]),
                        "status": "healthy" if overall_uptime >= 99.0 else "degraded" if overall_uptime >= 95.0 else "unhealthy"
                    },
                    "integrations": integration_health,
                    "environment": environment,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting integration health details: {str(e)}")
            return {"error": str(e)}
    
    # Business Metrics for Educational and Enterprise Features
    def track_educational_metrics(self, metric_name: str, value: float, user_id: str = None,
                                institution_id: str = None, course_id: str = None,
                                metadata: Dict[str, Any] = None, environment: str = "production"):
        """Track educational feature business metrics"""
        try:
            dimensions = {
                "user_id": user_id,
                "institution_id": institution_id,
                "course_id": course_id
            }
            dimensions.update(metadata or {})
            
            self.track_business_metric(
                metric_name=metric_name,
                category="educational",
                value=value,
                dimensions=dimensions,
                environment=environment
            )
            
            # Also track as feature usage for engagement analytics
            self.track_feature_usage(
                feature_name="educational_feature",
                category=FeatureCategory.EDUCATIONAL,
                action=metric_name,
                user_id=user_id,
                success=True,
                metadata=dimensions,
                environment=environment
            )
            
        except Exception as e:
            logger.error(f"Error tracking educational metrics: {str(e)}")
    
    def track_enterprise_metrics(self, metric_name: str, value: float, institution_id: str,
                               department_id: str = None, user_id: str = None,
                               metadata: Dict[str, Any] = None, environment: str = "production"):
        """Track enterprise feature business metrics"""
        try:
            dimensions = {
                "institution_id": institution_id,
                "department_id": department_id,
                "user_id": user_id
            }
            dimensions.update(metadata or {})
            
            self.track_business_metric(
                metric_name=metric_name,
                category="enterprise",
                value=value,
                dimensions=dimensions,
                environment=environment
            )
            
            # Also track as feature usage
            self.track_feature_usage(
                feature_name="enterprise_feature",
                category=FeatureCategory.ENTERPRISE,
                action=metric_name,
                user_id=user_id,
                success=True,
                metadata=dimensions,
                environment=environment
            )
            
        except Exception as e:
            logger.error(f"Error tracking enterprise metrics: {str(e)}")
    
    # Real-time Analytics Dashboard Data
    def get_realtime_dashboard_data(self) -> Dict[str, Any]:
        """Get real-time data for monitoring dashboard"""
        try:
            # Get current system health
            system_health = self.get_system_health()
            
            # Get recent feature usage (last hour)
            feature_usage = self.get_feature_usage_stats(hours=1)
            
            # Get performance metrics (last hour)
            performance_metrics = self.get_performance_metrics(hours=1)
            
            # Get integration health
            integration_health = self.get_integration_health_details()
            
            # Get business metrics (last 24 hours)
            business_metrics = self.get_business_metrics_summary(hours=24)
            
            # Get detailed analytics
            detailed_analytics = self.get_detailed_feature_analytics(hours=24)
            
            # Real-time counters from Redis
            realtime_counters = {}
            counter_keys = self.redis_client.keys("feature_usage:*:production")
            for key in counter_keys:
                key_str = key.decode()
                counter_value = self.redis_client.get(key)
                if counter_value:
                    realtime_counters[key_str] = int(counter_value)
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "system_health": system_health,
                "feature_usage": feature_usage,
                "performance_metrics": performance_metrics,
                "integration_health": integration_health,
                "business_metrics": business_metrics,
                "detailed_analytics": detailed_analytics,
                "realtime_counters": realtime_counters,
                "alerts": self._get_active_alerts()
            }
            
        except Exception as e:
            logger.error(f"Error getting realtime dashboard data: {str(e)}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}

# Global service instance
monitoring_service = ComprehensiveMonitoringService()

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    metric_name: str
    condition: str  # e.g., "> 100", "< 0.95"
    threshold: float
    severity: AlertSeverity
    duration_minutes: int = 5
    enabled: bool = True

class FeatureUsageMetric(Base):
    """Feature usage tracking"""
    __tablename__ = "feature_usage_metrics"
    
    id = Column(String(36), primary_key=True)
    feature_name = Column(String(100), index=True)
    user_id = Column(String(36), index=True)
    action = Column(String(100))
    duration_ms = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    metadata = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_agent = Column(String(500))
    ip_address = Column(String(45))

class PerformanceMetric(Base):
    """Performance metrics storage"""
    __tablename__ = "performance_metrics"
    
    id = Column(String(36), primary_key=True)
    metric_name = Column(String(100), index=True)
    metric_type = Column(String(20))
    value = Column(Float)
    tags = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class IntegrationHealthMetric(Base):
    """External integration health tracking"""
    __tablename__ = "integration_health_metrics"
    
    id = Column(String(36), primary_key=True)
    service_name = Column(String(100), index=True)
    endpoint = Column(String(255))
    response_time_ms = Column(Integer)
    status_code = Column(Integer)
    success = Column(Boolean)
    error_message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class BusinessMetric(Base):
    """Business metrics for educational and enterprise features"""
    __tablename__ = "business_metrics"
    
    id = Column(String(36), primary_key=True)
    metric_name = Column(String(100), index=True)
    category = Column(String(50))  # educational, enterprise, engagement
    value = Column(Float)
    user_id = Column(String(36), index=True)
    institution_id = Column(String(36), index=True)
    metadata = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class SystemAlert(Base):
    """System alerts and notifications"""
    __tablename__ = "system_alerts"
    
    id = Column(String(36), primary_key=True)
    alert_name = Column(String(100), index=True)
    severity = Column(String(20))
    message = Column(Text)
    metric_name = Column(String(100))
    threshold_value = Column(Float)
    actual_value = Column(Float)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default=dict)

class ComprehensiveMonitoringService:
    """Comprehensive monitoring service"""
    
    def __init__(self):
        self.redis_client = redis_client
        self.metrics_buffer = deque(maxlen=1000)
        self.alert_rules = {}
        self.alert_states = {}
        self.performance_cache = {}
        
        # Initialize alert rules
        self._initialize_alert_rules()
        
        # Start background tasks
        asyncio.create_task(self._flush_metrics_periodically())
        asyncio.create_task(self._check_alerts_periodically())
    
    # Feature Usage Analytics
    def track_feature_usage(self, feature_name: str, user_id: str = None, action: str = "access", 
                          duration_ms: int = None, success: bool = True, error_message: str = None,
                          metadata: Dict[str, Any] = None, user_agent: str = None, ip_address: str = None):
        """Track feature usage"""
        try:
            usage_id = f"{feature_name}_{user_id or 'anon'}_{int(time.time() * 1000)}"
            
            # Store in database
            with get_db_session() as session:
                usage = FeatureUsageMetric(
                    id=usage_id,
                    feature_name=feature_name,
                    user_id=user_id,
                    action=action,
                    duration_ms=duration_ms,
                    success=success,
                    error_message=error_message,
                    metadata=metadata or {},
                    user_agent=user_agent,
                    ip_address=ip_address
                )
                session.add(usage)
                session.commit()
            
            # Update real-time counters
            self._update_realtime_counter(f"feature_usage:{feature_name}", 1)
            if not success:
                self._update_realtime_counter(f"feature_errors:{feature_name}", 1)
            
            logger.debug(f"Tracked feature usage: {feature_name} by {user_id}")
            
        except Exception as e:
            logger.error(f"Error tracking feature usage: {str(e)}")
    
    def get_feature_usage_stats(self, feature_name: str = None, days: int = 7) -> Dict[str, Any]:
        """Get feature usage statistics"""
        try:
            with get_db_session() as session:
                start_date = datetime.utcnow() - timedelta(days=days)
                
                query = session.query(FeatureUsageMetric).filter(
                    FeatureUsageMetric.timestamp >= start_date
                )
                
                if feature_name:
                    query = query.filter(FeatureUsageMetric.feature_name == feature_name)
                
                usage_records = query.all()
                
                # Aggregate statistics
                stats = {
                    'total_usage': len(usage_records),
                    'unique_users': len(set(r.user_id for r in usage_records if r.user_id)),
                    'success_rate': sum(1 for r in usage_records if r.success) / len(usage_records) if usage_records else 0,
                    'average_duration_ms': sum(r.duration_ms for r in usage_records if r.duration_ms) / len([r for r in usage_records if r.duration_ms]) if any(r.duration_ms for r in usage_records) else 0,
                    'feature_breakdown': self._get_feature_breakdown(usage_records),
                    'daily_usage': self._get_daily_usage_breakdown(usage_records, days),
                    'error_breakdown': self._get_error_breakdown(usage_records)
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting feature usage stats: {str(e)}")
            return {}
    
    # Performance Monitoring
    def record_performance_metric(self, metric: MetricData):
        """Record a performance metric"""
        try:
            # Add to buffer for batch processing
            self.metrics_buffer.append(metric)
            
            # Update real-time cache
            cache_key = f"perf:{metric.name}"
            if metric.metric_type == MetricType.GAUGE:
                self.redis_client.set(cache_key, metric.value, ex=300)
            elif metric.metric_type == MetricType.COUNTER:
                self.redis_client.incr(cache_key)
                self.redis_client.expire(cache_key, 300)
            
            # Check for alerts
            self._check_metric_alerts(metric)
            
        except Exception as e:
            logger.error(f"Error recording performance metric: {str(e)}")
    
    def get_performance_metrics(self, metric_name: str = None, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics"""
        try:
            with get_db_session() as session:
                start_time = datetime.utcnow() - timedelta(hours=hours)
                
                query = session.query(PerformanceMetric).filter(
                    PerformanceMetric.timestamp >= start_time
                )
                
                if metric_name:
                    query = query.filter(PerformanceMetric.metric_name == metric_name)
                
                metrics = query.all()
                
                # Aggregate by metric name
                aggregated = defaultdict(list)
                for metric in metrics:
                    aggregated[metric.metric_name].append({
                        'value': metric.value,
                        'timestamp': metric.timestamp.isoformat(),
                        'tags': metric.tags
                    })
                
                return dict(aggregated)
                
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {}
    
    # Voice Processing Performance
    def track_voice_processing_performance(self, operation: str, duration_ms: int, 
                                         language: str = None, success: bool = True, 
                                         error_message: str = None):
        """Track voice processing performance"""
        try:
            tags = {'operation': operation}
            if language:
                tags['language'] = language
            
            # Record performance metric
            metric = MetricData(
                name="voice_processing_duration",
                value=duration_ms,
                metric_type=MetricType.HISTOGRAM,
                tags=tags
            )
            self.record_performance_metric(metric)
            
            # Track success/failure
            result_metric = MetricData(
                name="voice_processing_success",
                value=1 if success else 0,
                metric_type=MetricType.COUNTER,
                tags=tags
            )
            self.record_performance_metric(result_metric)
            
            if not success and error_message:
                logger.warning(f"Voice processing failed: {error_message}")
            
        except Exception as e:
            logger.error(f"Error tracking voice processing performance: {str(e)}")
    
    # Mobile Performance Monitoring
    def track_mobile_performance(self, user_id: str, device_type: str, operation: str,
                               duration_ms: int, network_type: str = None, 
                               battery_level: float = None):
        """Track mobile performance metrics"""
        try:
            tags = {
                'device_type': device_type,
                'operation': operation
            }
            if network_type:
                tags['network_type'] = network_type
            
            # Record performance
            metric = MetricData(
                name="mobile_operation_duration",
                value=duration_ms,
                metric_type=MetricType.HISTOGRAM,
                tags=tags
            )
            self.record_performance_metric(metric)
            
            # Track battery impact if available
            if battery_level is not None:
                battery_metric = MetricData(
                    name="mobile_battery_level",
                    value=battery_level,
                    metric_type=MetricType.GAUGE,
                    tags={'device_type': device_type}
                )
                self.record_performance_metric(battery_metric)
            
        except Exception as e:
            logger.error(f"Error tracking mobile performance: {str(e)}")
    
    # Integration Health Monitoring
    def track_integration_health(self, service_name: str, endpoint: str, 
                               response_time_ms: int, status_code: int,
                               success: bool = True, error_message: str = None):
        """Track external integration health"""
        try:
            health_id = f"{service_name}_{endpoint}_{int(time.time() * 1000)}"
            
            with get_db_session() as session:
                health = IntegrationHealthMetric(
                    id=health_id,
                    service_name=service_name,
                    endpoint=endpoint,
                    response_time_ms=response_time_ms,
                    status_code=status_code,
                    success=success,
                    error_message=error_message
                )
                session.add(health)
                session.commit()
            
            # Update real-time status
            status_key = f"integration_status:{service_name}"
            self.redis_client.hset(status_key, mapping={
                'last_check': datetime.utcnow().isoformat(),
                'status': 'healthy' if success else 'unhealthy',
                'response_time': response_time_ms,
                'status_code': status_code
            })
            self.redis_client.expire(status_key, 3600)  # 1 hour
            
        except Exception as e:
            logger.error(f"Error tracking integration health: {str(e)}")
    
    def get_integration_health_status(self, service_name: str = None) -> Dict[str, Any]:
        """Get integration health status"""
        try:
            if service_name:
                # Get specific service status
                status_key = f"integration_status:{service_name}"
                status = self.redis_client.hgetall(status_key)
                return {service_name: status} if status else {}
            else:
                # Get all service statuses
                pattern = "integration_status:*"
                keys = self.redis_client.keys(pattern)
                
                statuses = {}
                for key in keys:
                    service = key.decode().split(':')[1]
                    status = self.redis_client.hgetall(key)
                    statuses[service] = status
                
                return statuses
                
        except Exception as e:
            logger.error(f"Error getting integration health status: {str(e)}")
            return {}
    
    # Business Metrics
    def track_business_metric(self, metric_name: str, category: str, value: float,
                            user_id: str = None, institution_id: str = None,
                            metadata: Dict[str, Any] = None):
        """Track business metrics"""
        try:
            metric_id = f"{metric_name}_{user_id or 'system'}_{int(time.time() * 1000)}"
            
            with get_db_session() as session:
                business_metric = BusinessMetric(
                    id=metric_id,
                    metric_name=metric_name,
                    category=category,
                    value=value,
                    user_id=user_id,
                    institution_id=institution_id,
                    metadata=metadata or {}
                )
                session.add(business_metric)
                session.commit()
            
            # Update aggregated metrics
            self._update_business_aggregates(metric_name, category, value)
            
        except Exception as e:
            logger.error(f"Error tracking business metric: {str(e)}")
    
    def get_business_metrics(self, category: str = None, days: int = 30) -> Dict[str, Any]:
        """Get business metrics"""
        try:
            with get_db_session() as session:
                start_date = datetime.utcnow() - timedelta(days=days)
                
                query = session.query(BusinessMetric).filter(
                    BusinessMetric.timestamp >= start_date
                )
                
                if category:
                    query = query.filter(BusinessMetric.category == category)
                
                metrics = query.all()
                
                # Aggregate by category and metric name
                aggregated = defaultdict(lambda: defaultdict(list))
                for metric in metrics:
                    aggregated[metric.category][metric.metric_name].append({
                        'value': metric.value,
                        'timestamp': metric.timestamp.isoformat(),
                        'user_id': metric.user_id,
                        'institution_id': metric.institution_id
                    })
                
                return dict(aggregated)
                
        except Exception as e:
            logger.error(f"Error getting business metrics: {str(e)}")
            return {}
    
    # System Health Monitoring
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Database health
            db_healthy = self._check_database_health()
            
            # Redis health
            redis_healthy = self._check_redis_health()
            
            # Integration health
            integration_statuses = self.get_integration_health_status()
            
            # Recent alerts
            recent_alerts = self._get_recent_alerts()
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': (disk.used / disk.total) * 100,
                    'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                },
                'services': {
                    'database': 'healthy' if db_healthy else 'unhealthy',
                    'redis': 'healthy' if redis_healthy else 'unhealthy'
                },
                'integrations': integration_statuses,
                'alerts': recent_alerts,
                'overall_status': self._calculate_overall_health(
                    cpu_percent, memory.percent, db_healthy, redis_healthy, integration_statuses
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            return {'error': str(e)}
    
    # Alert Management
    def create_alert(self, alert_name: str, severity: AlertSeverity, message: str,
                    metric_name: str = None, threshold_value: float = None,
                    actual_value: float = None, metadata: Dict[str, Any] = None):
        """Create a system alert"""
        try:
            alert_id = f"{alert_name}_{int(time.time() * 1000)}"
            
            with get_db_session() as session:
                alert = SystemAlert(
                    id=alert_id,
                    alert_name=alert_name,
                    severity=severity.value,
                    message=message,
                    metric_name=metric_name,
                    threshold_value=threshold_value,
                    actual_value=actual_value,
                    metadata=metadata or {}
                )
                session.add(alert)
                session.commit()
            
            # Send notification if critical
            if severity == AlertSeverity.CRITICAL:
                self._send_critical_alert_notification(alert_name, message)
            
            logger.warning(f"Alert created: {alert_name} - {message}")
            
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
    
    # Private helper methods
    def _initialize_alert_rules(self):
        """Initialize default alert rules"""
        self.alert_rules = {
            'high_cpu_usage': AlertRule(
                name='high_cpu_usage',
                metric_name='cpu_percent',
                condition='> 80',
                threshold=80.0,
                severity=AlertSeverity.HIGH,
                duration_minutes=5
            ),
            'high_memory_usage': AlertRule(
                name='high_memory_usage',
                metric_name='memory_percent',
                condition='> 85',
                threshold=85.0,
                severity=AlertSeverity.HIGH,
                duration_minutes=5
            ),
            'integration_failure_rate': AlertRule(
                name='integration_failure_rate',
                metric_name='integration_success_rate',
                condition='< 0.95',
                threshold=0.95,
                severity=AlertSeverity.MEDIUM,
                duration_minutes=10
            ),
            'voice_processing_latency': AlertRule(
                name='voice_processing_latency',
                metric_name='voice_processing_duration',
                condition='> 5000',
                threshold=5000.0,
                severity=AlertSeverity.MEDIUM,
                duration_minutes=5
            )
        }
    
    async def _flush_metrics_periodically(self):
        """Flush metrics buffer to database periodically"""
        while True:
            try:
                if self.metrics_buffer:
                    metrics_to_flush = []
                    while self.metrics_buffer and len(metrics_to_flush) < 100:
                        metrics_to_flush.append(self.metrics_buffer.popleft())
                    
                    # Batch insert to database
                    with get_db_session() as session:
                        for metric in metrics_to_flush:
                            perf_metric = PerformanceMetric(
                                id=f"{metric.name}_{int(metric.timestamp.timestamp() * 1000)}",
                                metric_name=metric.name,
                                metric_type=metric.metric_type.value,
                                value=metric.value,
                                tags=metric.tags,
                                timestamp=metric.timestamp
                            )
                            session.add(perf_metric)
                        session.commit()
                
                await asyncio.sleep(30)  # Flush every 30 seconds
                
            except Exception as e:
                logger.error(f"Error flushing metrics: {str(e)}")
                await asyncio.sleep(60)
    
    async def _check_alerts_periodically(self):
        """Check alert conditions periodically"""
        while True:
            try:
                for rule_name, rule in self.alert_rules.items():
                    if rule.enabled:
                        await self._evaluate_alert_rule(rule)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error checking alerts: {str(e)}")
                await asyncio.sleep(60)
    
    def _update_realtime_counter(self, key: str, increment: int = 1):
        """Update real-time counter in Redis"""
        try:
            self.redis_client.incr(key, increment)
            self.redis_client.expire(key, 3600)  # 1 hour TTL
        except Exception as e:
            logger.error(f"Error updating realtime counter: {str(e)}")
    
    def _get_feature_breakdown(self, usage_records: List[FeatureUsageMetric]) -> Dict[str, int]:
        """Get feature usage breakdown"""
        breakdown = defaultdict(int)
        for record in usage_records:
            breakdown[record.feature_name] += 1
        return dict(breakdown)
    
    def _get_daily_usage_breakdown(self, usage_records: List[FeatureUsageMetric], days: int) -> List[Dict[str, Any]]:
        """Get daily usage breakdown"""
        daily_usage = defaultdict(int)
        for record in usage_records:
            date_key = record.timestamp.date().isoformat()
            daily_usage[date_key] += 1
        
        # Fill in missing days
        result = []
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).date()
            date_key = date.isoformat()
            result.append({
                'date': date_key,
                'usage_count': daily_usage[date_key]
            })
        
        return sorted(result, key=lambda x: x['date'])
    
    def _get_error_breakdown(self, usage_records: List[FeatureUsageMetric]) -> Dict[str, int]:
        """Get error breakdown"""
        errors = defaultdict(int)
        for record in usage_records:
            if not record.success and record.error_message:
                errors[record.error_message] += 1
        return dict(errors)
    
    def _check_metric_alerts(self, metric: MetricData):
        """Check if metric triggers any alerts"""
        for rule_name, rule in self.alert_rules.items():
            if rule.metric_name == metric.name and rule.enabled:
                if self._evaluate_condition(metric.value, rule.condition, rule.threshold):
                    self._trigger_alert(rule, metric.value)
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate alert condition"""
        try:
            if condition.startswith('>'):
                return value > threshold
            elif condition.startswith('<'):
                return value < threshold
            elif condition.startswith('>='):
                return value >= threshold
            elif condition.startswith('<='):
                return value <= threshold
            elif condition.startswith('=='):
                return value == threshold
            return False
        except Exception:
            return False
    
    def _trigger_alert(self, rule: AlertRule, actual_value: float):
        """Trigger an alert"""
        # Check if alert is already active
        if rule.name in self.alert_states:
            last_triggered = self.alert_states[rule.name]
            if datetime.utcnow() - last_triggered < timedelta(minutes=rule.duration_minutes):
                return  # Don't spam alerts
        
        # Create alert
        self.create_alert(
            alert_name=rule.name,
            severity=rule.severity,
            message=f"Metric {rule.metric_name} {rule.condition} {rule.threshold} (actual: {actual_value})",
            metric_name=rule.metric_name,
            threshold_value=rule.threshold,
            actual_value=actual_value
        )
        
        # Update alert state
        self.alert_states[rule.name] = datetime.utcnow()
    
    def _check_database_health(self) -> bool:
        """Check database health"""
        try:
            with get_db_session() as session:
                session.execute("SELECT 1")
                return True
        except Exception:
            return False
    
    def _check_redis_health(self) -> bool:
        """Check Redis health"""
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False
    
    def _get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        try:
            with get_db_session() as session:
                start_time = datetime.utcnow() - timedelta(hours=hours)
                alerts = session.query(SystemAlert).filter(
                    SystemAlert.created_at >= start_time
                ).order_by(SystemAlert.created_at.desc()).limit(10).all()
                
                return [{
                    'alert_name': alert.alert_name,
                    'severity': alert.severity,
                    'message': alert.message,
                    'created_at': alert.created_at.isoformat(),
                    'resolved': alert.resolved
                } for alert in alerts]
                
        except Exception as e:
            logger.error(f"Error getting recent alerts: {str(e)}")
            return []
    
    def _calculate_overall_health(self, cpu_percent: float, memory_percent: float,
                                db_healthy: bool, redis_healthy: bool,
                                integration_statuses: Dict[str, Any]) -> str:
        """Calculate overall system health"""
        if not db_healthy or not redis_healthy:
            return 'critical'
        
        if cpu_percent > 90 or memory_percent > 90:
            return 'critical'
        
        if cpu_percent > 80 or memory_percent > 80:
            return 'warning'
        
        # Check integration health
        unhealthy_integrations = sum(1 for status in integration_statuses.values() 
                                   if status.get('status') == 'unhealthy')
        
        if unhealthy_integrations > len(integration_statuses) * 0.5:
            return 'warning'
        
        return 'healthy'
    
    def _update_business_aggregates(self, metric_name: str, category: str, value: float):
        """Update business metric aggregates"""
        try:
            # Update daily aggregates
            today = datetime.utcnow().date().isoformat()
            agg_key = f"business_agg:{category}:{metric_name}:{today}"
            
            self.redis_client.hincrby(agg_key, 'count', 1)
            self.redis_client.hincrbyfloat(agg_key, 'sum', value)
            self.redis_client.expire(agg_key, 86400 * 7)  # Keep for 7 days
            
        except Exception as e:
            logger.error(f"Error updating business aggregates: {str(e)}")
    
    def _send_critical_alert_notification(self, alert_name: str, message: str):
        """Send critical alert notification"""
        try:
            # This would integrate with notification services (Slack, email, etc.)
            logger.critical(f"CRITICAL ALERT: {alert_name} - {message}")
            
            # Store in Redis for immediate access
            alert_key = f"critical_alert:{int(time.time())}"
            self.redis_client.hset(alert_key, mapping={
                'alert_name': alert_name,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            })
            self.redis_client.expire(alert_key, 3600)  # 1 hour
            
        except Exception as e:
            logger.error(f"Error sending critical alert notification: {str(e)}")
    
    async def _evaluate_alert_rule(self, rule: AlertRule):
        """Evaluate a single alert rule"""
        try:
            # Get current metric value
            current_value = await self._get_current_metric_value(rule.metric_name)
            if current_value is not None:
                if self._evaluate_condition(current_value, rule.condition, rule.threshold):
                    self._trigger_alert(rule, current_value)
                    
        except Exception as e:
            logger.error(f"Error evaluating alert rule {rule.name}: {str(e)}")
    
    async def _get_current_metric_value(self, metric_name: str) -> Optional[float]:
        """Get current value for a metric"""
        try:
            if metric_name == 'cpu_percent':
                return psutil.cpu_percent(interval=1)
            elif metric_name == 'memory_percent':
                return psutil.virtual_memory().percent
            else:
                # Get from Redis cache
                cache_key = f"perf:{metric_name}"
                value = self.redis_client.get(cache_key)
                return float(value) if value else None
                
        except Exception as e:
            logger.error(f"Error getting current metric value for {metric_name}: {str(e)}")
            return None

# Global service instance
monitoring_service = ComprehensiveMonitoringService()

# Decorator for automatic performance tracking
def track_performance(feature_name: str, operation: str = "execute"):
    """Decorator to automatically track performance"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Extract user_id if available
                user_id = kwargs.get('user_id') or (args[0] if args and hasattr(args[0], 'user_id') else None)
                
                monitoring_service.track_feature_usage(
                    feature_name=feature_name,
                    user_id=user_id,
                    action=operation,
                    duration_ms=duration_ms,
                    success=success,
                    error_message=error_message
                )
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Extract user_id if available
                user_id = kwargs.get('user_id') or (args[0] if args and hasattr(args[0], 'user_id') else None)
                
                monitoring_service.track_feature_usage(
                    feature_name=feature_name,
                    user_id=user_id,
                    action=operation,
                    duration_ms=duration_ms,
                    success=success,
                    error_message=error_message
                )
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator