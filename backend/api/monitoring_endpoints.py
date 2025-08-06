"""
Monitoring API Endpoints for AI Scholar Advanced RAG
Provides access to monitoring data and system health
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from backend.services.comprehensive_monitoring_service import (
    monitoring_service, MetricData, MetricType, AlertSeverity
)
from backend.services.feature_flag_service import feature_flag_service
from backend.core.database import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

@router.get("/health")
async def get_system_health():
    """Get overall system health status"""
    try:
        health_data = monitoring_service.get_system_health()
        return JSONResponse(content=health_data)
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get system health")

@router.get("/health/detailed")
async def get_detailed_health():
    """Get detailed system health with all metrics"""
    try:
        health_data = monitoring_service.get_system_health()
        
        # Add additional detailed metrics
        detailed_data = {
            **health_data,
            'feature_flags': feature_flag_service.get_all_flags(),
            'performance_metrics': monitoring_service.get_performance_metrics(hours=1),
            'integration_health': monitoring_service.get_integration_health_status()
        }
        
        return JSONResponse(content=detailed_data)
    except Exception as e:
        logger.error(f"Error getting detailed health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get detailed health")

@router.get("/features/usage")
async def get_feature_usage_stats(
    feature_name: Optional[str] = Query(None, description="Specific feature name"),
    category: Optional[str] = Query(None, description="Feature category"),
    hours: int = Query(24, description="Time period in hours"),
    environment: str = Query("production", description="Environment")
):
    """Get feature usage statistics"""
    try:
        from backend.services.comprehensive_monitoring_service import FeatureCategory
        
        category_enum = None
        if category:
            try:
                category_enum = FeatureCategory(category)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
        
        stats = monitoring_service.get_feature_usage_stats(
            feature_name=feature_name,
            category=category_enum,
            hours=hours,
            environment=environment
        )
        
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"Error getting feature usage stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get feature usage stats")

@router.get("/performance")
async def get_performance_metrics(
    endpoint: Optional[str] = Query(None, description="Specific endpoint"),
    hours: int = Query(24, description="Time period in hours"),
    environment: str = Query("production", description="Environment")
):
    """Get performance metrics"""
    try:
        metrics = monitoring_service.get_performance_metrics(
            endpoint=endpoint,
            hours=hours,
            environment=environment
        )
        
        return JSONResponse(content=metrics)
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")

@router.get("/integrations/health")
async def get_integration_health(
    environment: str = Query("production", description="Environment")
):
    """Get integration health status"""
    try:
        health_status = monitoring_service.get_integration_health_status(environment)
        return JSONResponse(content=health_status)
        
    except Exception as e:
        logger.error(f"Error getting integration health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get integration health")

@router.get("/business")
async def get_business_metrics(
    category: Optional[str] = Query(None, description="Metric category"),
    hours: int = Query(24, description="Time period in hours"),
    environment: str = Query("production", description="Environment")
):
    """Get business metrics summary"""
    try:
        metrics = monitoring_service.get_business_metrics_summary(
            category=category,
            hours=hours,
            environment=environment
        )
        
        return JSONResponse(content=metrics)
        
    except Exception as e:
        logger.error(f"Error getting business metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get business metrics")

@router.post("/metrics")
async def record_custom_metric(request: Request):
    """Record a custom metric"""
    try:
        data = await request.json()
        
        from backend.services.comprehensive_monitoring_service import MetricData, MetricType
        
        metric = MetricData(
            name=data["name"],
            value=data["value"],
            metric_type=MetricType(data.get("type", "gauge")),
            tags=data.get("tags", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else None
        )
        
        monitoring_service.record_metric(metric, data.get("environment", "production"))
        
        return JSONResponse(content={"status": "success", "message": "Metric recorded"})
        
    except Exception as e:
        logger.error(f"Error recording custom metric: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record metric")

@router.post("/features/track")
async def track_feature_usage(request: Request):
    """Track feature usage"""
    try:
        data = await request.json()
        
        from backend.services.comprehensive_monitoring_service import FeatureCategory
        
        category = FeatureCategory(data["category"])
        
        monitoring_service.track_feature_usage(
            feature_name=data["feature_name"],
            category=category,
            action=data["action"],
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            duration_ms=data.get("duration_ms"),
            success=data.get("success", True),
            error_message=data.get("error_message"),
            metadata=data.get("metadata", {}),
            environment=data.get("environment", "production")
        )
        
        return JSONResponse(content={"status": "success", "message": "Feature usage tracked"})
        
    except Exception as e:
        logger.error(f"Error tracking feature usage: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track feature usage")

@router.get("/features/flags")
async def get_feature_flags():
    """Get all feature flags"""
    try:
        flags = feature_flag_service.get_all_flags()
        return JSONResponse(content={"flags": flags})
        
    except Exception as e:
        logger.error(f"Error getting feature flags: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get feature flags")

@router.get("/features/flags/{flag_name}")
async def get_feature_flag(flag_name: str):
    """Get specific feature flag"""
    try:
        flag = feature_flag_service.get_flag(flag_name)
        if not flag:
            raise HTTPException(status_code=404, detail="Feature flag not found")
        
        return JSONResponse(content=flag)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feature flag {flag_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get feature flag")

@router.post("/features/flags/{flag_name}/evaluate")
async def evaluate_feature_flag(flag_name: str, request: Request):
    """Evaluate feature flag for given context"""
    try:
        data = await request.json()
        user_context = data.get("context", {})
        
        is_enabled = feature_flag_service.is_enabled(flag_name, user_context)
        
        return JSONResponse(content={
            "flag_name": flag_name,
            "enabled": is_enabled,
            "context": user_context
        })
        
    except Exception as e:
        logger.error(f"Error evaluating feature flag {flag_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to evaluate feature flag")

@router.get("/features/flags/{flag_name}/usage")
async def get_feature_flag_usage(
    flag_name: str,
    days: int = Query(7, description="Number of days")
):
    """Get feature flag usage statistics"""
    try:
        usage_stats = feature_flag_service.get_usage_stats(flag_name, days)
        return JSONResponse(content=usage_stats)
        
    except Exception as e:
        logger.error(f"Error getting feature flag usage for {flag_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get feature flag usage")

@router.get("/alerts")
async def get_active_alerts():
    """Get active monitoring alerts"""
    try:
        # This would integrate with your alerting system
        # For now, return system health-based alerts
        health_data = monitoring_service.get_system_health()
        
        alerts = []
        
        # Check for system resource alerts
        if health_data.get("system_resources", {}).get("cpu_usage_percent", 0) > 80:
            alerts.append({
                "id": "high_cpu_usage",
                "severity": "medium",
                "message": f"High CPU usage: {health_data['system_resources']['cpu_usage_percent']:.1f}%",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        if health_data.get("system_resources", {}).get("memory_usage_percent", 0) > 85:
            alerts.append({
                "id": "high_memory_usage",
                "severity": "high",
                "message": f"High memory usage: {health_data['system_resources']['memory_usage_percent']:.1f}%",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check for unhealthy services
        services = health_data.get("services", {})
        for service_name, service_data in services.items():
            if service_data.get("status") != "healthy":
                alerts.append({
                    "id": f"unhealthy_service_{service_name}",
                    "severity": "critical",
                    "message": f"Service {service_name} is {service_data.get('status', 'unknown')}",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return JSONResponse(content={"alerts": alerts})
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get active alerts")

@router.get("/dashboard")
async def get_monitoring_dashboard():
    """Get comprehensive monitoring dashboard data"""
    try:
        # Get real-time dashboard data
        dashboard_data = monitoring_service.get_realtime_dashboard_data()
        return JSONResponse(content=dashboard_data)
        
    except Exception as e:
        logger.error(f"Error getting monitoring dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get monitoring dashboard")

@router.get("/analytics/features")
async def get_detailed_feature_analytics(
    category: Optional[str] = Query(None, description="Feature category"),
    hours: int = Query(24, description="Time period in hours"),
    environment: str = Query("production", description="Environment")
):
    """Get detailed feature usage analytics with user behavior tracking"""
    try:
        from backend.services.comprehensive_monitoring_service import FeatureCategory
        
        category_enum = None
        if category:
            try:
                category_enum = FeatureCategory(category)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
        
        analytics = monitoring_service.get_detailed_feature_analytics(
            feature_category=category_enum,
            hours=hours,
            environment=environment
        )
        
        return JSONResponse(content=analytics)
        
    except Exception as e:
        logger.error(f"Error getting detailed feature analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get feature analytics")

@router.post("/voice/performance")
async def track_voice_performance(request: Request):
    """Track voice processing performance metrics"""
    try:
        data = await request.json()
        
        monitoring_service.track_voice_performance(
            operation=data["operation"],
            language=data["language"],
            duration_ms=data["duration_ms"],
            accuracy_score=data.get("accuracy_score"),
            user_id=data.get("user_id"),
            error_message=data.get("error_message"),
            environment=data.get("environment", "production")
        )
        
        return JSONResponse(content={"status": "success", "message": "Voice performance tracked"})
        
    except Exception as e:
        logger.error(f"Error tracking voice performance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track voice performance")

@router.get("/voice/analytics")
async def get_voice_analytics(
    hours: int = Query(24, description="Time period in hours"),
    environment: str = Query("production", description="Environment")
):
    """Get voice processing analytics"""
    try:
        from backend.services.comprehensive_monitoring_service import FeatureCategory
        
        analytics = monitoring_service.get_detailed_feature_analytics(
            feature_category=FeatureCategory.VOICE,
            hours=hours,
            environment=environment
        )
        
        return JSONResponse(content=analytics)
        
    except Exception as e:
        logger.error(f"Error getting voice analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get voice analytics")

@router.post("/mobile/performance")
async def track_mobile_performance(request: Request):
    """Track mobile performance metrics"""
    try:
        data = await request.json()
        
        monitoring_service.track_mobile_performance(
            device_type=data["device_type"],
            operation=data["operation"],
            duration_ms=data["duration_ms"],
            network_type=data.get("network_type"),
            battery_level=data.get("battery_level"),
            user_id=data.get("user_id"),
            error_message=data.get("error_message"),
            environment=data.get("environment", "production")
        )
        
        return JSONResponse(content={"status": "success", "message": "Mobile performance tracked"})
        
    except Exception as e:
        logger.error(f"Error tracking mobile performance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track mobile performance")

@router.get("/mobile/analytics")
async def get_mobile_analytics(
    hours: int = Query(24, description="Time period in hours"),
    environment: str = Query("production", description="Environment")
):
    """Get mobile performance analytics"""
    try:
        from backend.services.comprehensive_monitoring_service import FeatureCategory
        
        analytics = monitoring_service.get_detailed_feature_analytics(
            feature_category=FeatureCategory.MOBILE,
            hours=hours,
            environment=environment
        )
        
        return JSONResponse(content=analytics)
        
    except Exception as e:
        logger.error(f"Error getting mobile analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get mobile analytics")

@router.get("/integrations/health/detailed")
async def get_detailed_integration_health(
    environment: str = Query("production", description="Environment")
):
    """Get detailed integration health with SLA tracking"""
    try:
        health_details = monitoring_service.get_integration_health_details(environment)
        return JSONResponse(content=health_details)
        
    except Exception as e:
        logger.error(f"Error getting detailed integration health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get integration health details")

@router.post("/educational/metrics")
async def track_educational_metric(request: Request):
    """Track educational feature business metrics"""
    try:
        data = await request.json()
        
        monitoring_service.track_educational_metrics(
            metric_name=data["metric_name"],
            value=data["value"],
            user_id=data.get("user_id"),
            institution_id=data.get("institution_id"),
            course_id=data.get("course_id"),
            metadata=data.get("metadata", {}),
            environment=data.get("environment", "production")
        )
        
        return JSONResponse(content={"status": "success", "message": "Educational metric tracked"})
        
    except Exception as e:
        logger.error(f"Error tracking educational metric: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track educational metric")

@router.get("/educational/analytics")
async def get_educational_analytics(
    hours: int = Query(24, description="Time period in hours"),
    environment: str = Query("production", description="Environment")
):
    """Get educational features analytics"""
    try:
        from backend.services.comprehensive_monitoring_service import FeatureCategory
        
        analytics = monitoring_service.get_detailed_feature_analytics(
            feature_category=FeatureCategory.EDUCATIONAL,
            hours=hours,
            environment=environment
        )
        
        return JSONResponse(content=analytics)
        
    except Exception as e:
        logger.error(f"Error getting educational analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get educational analytics")

@router.post("/enterprise/metrics")
async def track_enterprise_metric(request: Request):
    """Track enterprise feature business metrics"""
    try:
        data = await request.json()
        
        monitoring_service.track_enterprise_metrics(
            metric_name=data["metric_name"],
            value=data["value"],
            institution_id=data["institution_id"],
            department_id=data.get("department_id"),
            user_id=data.get("user_id"),
            metadata=data.get("metadata", {}),
            environment=data.get("environment", "production")
        )
        
        return JSONResponse(content={"status": "success", "message": "Enterprise metric tracked"})
        
    except Exception as e:
        logger.error(f"Error tracking enterprise metric: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track enterprise metric")

@router.get("/enterprise/analytics")
async def get_enterprise_analytics(
    hours: int = Query(24, description="Time period in hours"),
    environment: str = Query("production", description="Environment")
):
    """Get enterprise features analytics"""
    try:
        from backend.services.comprehensive_monitoring_service import FeatureCategory
        
        analytics = monitoring_service.get_detailed_feature_analytics(
            feature_category=FeatureCategory.ENTERPRISE,
            hours=hours,
            environment=environment
        )
        
        return JSONResponse(content=analytics)
        
    except Exception as e:
        logger.error(f"Error getting enterprise analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get enterprise analytics")

@router.get("/realtime/counters")
async def get_realtime_counters():
    """Get real-time feature usage counters"""
    try:
        # Get real-time counters from Redis
        realtime_counters = {}
        counter_keys = monitoring_service.redis_client.keys("feature_usage:*:production")
        
        for key in counter_keys:
            key_str = key.decode()
            counter_value = monitoring_service.redis_client.get(key)
            if counter_value:
                realtime_counters[key_str] = int(counter_value)
        
        return JSONResponse(content={
            "counters": realtime_counters,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting realtime counters: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get realtime counters")

@router.get("/analytics/user-behavior")
async def get_user_behavior_patterns(
    days: int = Query(30, description="Number of days to analyze"),
    environment: str = Query("production", description="Environment")
):
    """Get user behavior patterns and engagement analytics"""
    try:
        from backend.services.advanced_analytics_service import advanced_analytics_service
        
        patterns = advanced_analytics_service.analyze_user_behavior_patterns(days, environment)
        
        # Convert to serializable format
        patterns_data = [
            {
                "user_id": p.user_id,
                "session_count": p.session_count,
                "total_duration_minutes": p.total_duration_minutes,
                "favorite_features": p.favorite_features,
                "usage_frequency": p.usage_frequency,
                "engagement_score": p.engagement_score,
                "churn_risk": p.churn_risk,
                "last_activity": p.last_activity.isoformat()
            }
            for p in patterns
        ]
        
        return JSONResponse(content={
            "patterns": patterns_data,
            "total_users": len(patterns_data),
            "analysis_period_days": days,
            "environment": environment,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting user behavior patterns: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user behavior patterns")

@router.get("/analytics/feature-insights")
async def get_feature_performance_insights(
    days: int = Query(30, description="Number of days to analyze"),
    environment: str = Query("production", description="Environment")
):
    """Get feature performance insights and trends"""
    try:
        from backend.services.advanced_analytics_service import advanced_analytics_service
        
        insights = advanced_analytics_service.analyze_feature_performance_insights(days, environment)
        
        # Convert to serializable format
        insights_data = [
            {
                "feature_name": i.feature_name,
                "category": i.category,
                "usage_trend": i.usage_trend,
                "performance_trend": i.performance_trend,
                "user_satisfaction": i.user_satisfaction,
                "adoption_rate": i.adoption_rate,
                "retention_rate": i.retention_rate,
                "key_issues": i.key_issues
            }
            for i in insights
        ]
        
        return JSONResponse(content={
            "insights": insights_data,
            "total_features": len(insights_data),
            "analysis_period_days": days,
            "environment": environment,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting feature performance insights: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get feature performance insights")

@router.get("/analytics/business-intelligence")
async def get_business_intelligence_report(
    report_type: str = Query("comprehensive", description="Report type: comprehensive, performance, engagement"),
    days: int = Query(30, description="Number of days to analyze"),
    environment: str = Query("production", description="Environment")
):
    """Get business intelligence report"""
    try:
        from backend.services.advanced_analytics_service import advanced_analytics_service
        
        report = advanced_analytics_service.generate_business_intelligence_report(report_type, days, environment)
        
        # Convert to serializable format
        report_data = {
            "report_type": report.report_type,
            "period": report.period,
            "key_metrics": report.key_metrics,
            "insights": report.insights,
            "recommendations": report.recommendations,
            "trends": report.trends,
            "generated_at": report.generated_at.isoformat()
        }
        
        return JSONResponse(content=report_data)
        
    except Exception as e:
        logger.error(f"Error getting business intelligence report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get business intelligence report")

@router.get("/analytics/predictive-insights")
async def get_predictive_insights(
    days: int = Query(30, description="Number of days of historical data to analyze"),
    environment: str = Query("production", description="Environment")
):
    """Get predictive insights based on historical data"""
    try:
        from backend.services.advanced_analytics_service import advanced_analytics_service
        
        insights = advanced_analytics_service.get_predictive_insights(days, environment)
        
        return JSONResponse(content=insights)
        
    except Exception as e:
        logger.error(f"Error getting predictive insights: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get predictive insights")

@router.get("/analytics/comprehensive-dashboard")
async def get_comprehensive_analytics_dashboard():
    """Get comprehensive analytics dashboard with all insights"""
    try:
        from backend.services.advanced_analytics_service import advanced_analytics_service
        
        # Get all analytics data
        user_patterns = advanced_analytics_service.analyze_user_behavior_patterns(30)
        feature_insights = advanced_analytics_service.analyze_feature_performance_insights(30)
        business_report = advanced_analytics_service.generate_business_intelligence_report("comprehensive", 30)
        predictive_insights = advanced_analytics_service.get_predictive_insights(30)
        
        # Get real-time monitoring data
        realtime_data = monitoring_service.get_realtime_dashboard_data()
        
        dashboard_data = {
            "user_behavior": {
                "total_users": len(user_patterns),
                "high_engagement_users": sum(1 for p in user_patterns if p.engagement_score >= 80),
                "churn_risk_users": sum(1 for p in user_patterns if p.churn_risk == "high"),
                "patterns": [
                    {
                        "user_id": p.user_id,
                        "engagement_score": p.engagement_score,
                        "churn_risk": p.churn_risk,
                        "usage_frequency": p.usage_frequency
                    }
                    for p in user_patterns[:10]  # Top 10 users
                ]
            },
            "feature_performance": {
                "total_features": len(feature_insights),
                "improving_features": sum(1 for i in feature_insights if i.performance_trend == "improving"),
                "degrading_features": sum(1 for i in feature_insights if i.performance_trend == "degrading"),
                "insights": [
                    {
                        "feature_name": i.feature_name,
                        "usage_trend": i.usage_trend,
                        "performance_trend": i.performance_trend,
                        "user_satisfaction": i.user_satisfaction
                    }
                    for i in feature_insights
                ]
            },
            "business_intelligence": {
                "report_type": business_report.report_type,
                "key_metrics": business_report.key_metrics,
                "insights": business_report.insights,
                "recommendations": business_report.recommendations,
                "trends": business_report.trends
            },
            "predictive_insights": predictive_insights,
            "realtime_data": realtime_data,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=dashboard_data)
        
    except Exception as e:
        logger.error(f"Error getting comprehensive analytics dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get comprehensive analytics dashboard")
async def get_feature_usage_stats(
    feature_name: Optional[str] = Query(None, description="Specific feature name"),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """Get feature usage statistics"""
    try:
        stats = monitoring_service.get_feature_usage_stats(feature_name, days)
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Error getting feature usage stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get feature usage stats")

@router.get("/features/{feature_name}/usage")
async def get_specific_feature_usage(
    feature_name: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """Get usage statistics for a specific feature"""
    try:
        stats = monitoring_service.get_feature_usage_stats(feature_name, days)
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Error getting feature usage for {feature_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get usage for {feature_name}")

@router.get("/performance/metrics")
async def get_performance_metrics(
    metric_name: Optional[str] = Query(None, description="Specific metric name"),
    hours: int = Query(24, ge=1, le=168, description="Number of hours to analyze")
):
    """Get performance metrics"""
    try:
        metrics = monitoring_service.get_performance_metrics(metric_name, hours)
        return JSONResponse(content=metrics)
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")

@router.post("/performance/metrics")
async def record_custom_metric(
    metric_name: str,
    value: float,
    metric_type: str = "gauge",
    tags: Optional[Dict[str, str]] = None
):
    """Record a custom performance metric"""
    try:
        # Validate metric type
        try:
            metric_type_enum = MetricType(metric_type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid metric type")
        
        metric = MetricData(
            name=metric_name,
            value=value,
            metric_type=metric_type_enum,
            tags=tags or {}
        )
        
        monitoring_service.record_performance_metric(metric)
        
        return JSONResponse(content={
            "message": "Metric recorded successfully",
            "metric_name": metric_name,
            "value": value,
            "timestamp": metric.timestamp.isoformat()
        })
    except Exception as e:
        logger.error(f"Error recording custom metric: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record metric")

@router.get("/voice/performance")
async def get_voice_performance_metrics(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to analyze")
):
    """Get voice processing performance metrics"""
    try:
        # Get voice-specific metrics
        voice_metrics = monitoring_service.get_performance_metrics(hours=hours)
        
        # Filter for voice-related metrics
        voice_data = {
            key: value for key, value in voice_metrics.items()
            if 'voice' in key.lower()
        }
        
        return JSONResponse(content=voice_data)
    except Exception as e:
        logger.error(f"Error getting voice performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get voice performance metrics")

@router.get("/mobile/performance")
async def get_mobile_performance_metrics(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to analyze")
):
    """Get mobile performance metrics"""
    try:
        # Get mobile-specific metrics
        mobile_metrics = monitoring_service.get_performance_metrics(hours=hours)
        
        # Filter for mobile-related metrics
        mobile_data = {
            key: value for key, value in mobile_metrics.items()
            if 'mobile' in key.lower()
        }
        
        return JSONResponse(content=mobile_data)
    except Exception as e:
        logger.error(f"Error getting mobile performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get mobile performance metrics")

@router.get("/integrations/health")
async def get_integration_health(
    service_name: Optional[str] = Query(None, description="Specific service name")
):
    """Get external integration health status"""
    try:
        health_status = monitoring_service.get_integration_health_status(service_name)
        return JSONResponse(content=health_status)
    except Exception as e:
        logger.error(f"Error getting integration health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get integration health")

@router.post("/integrations/{service_name}/health")
async def report_integration_health(
    service_name: str,
    endpoint: str,
    response_time_ms: int,
    status_code: int,
    success: bool = True,
    error_message: Optional[str] = None
):
    """Report integration health status"""
    try:
        monitoring_service.track_integration_health(
            service_name=service_name,
            endpoint=endpoint,
            response_time_ms=response_time_ms,
            status_code=status_code,
            success=success,
            error_message=error_message
        )
        
        return JSONResponse(content={
            "message": "Integration health reported successfully",
            "service_name": service_name,
            "endpoint": endpoint,
            "success": success
        })
    except Exception as e:
        logger.error(f"Error reporting integration health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to report integration health")

@router.get("/business/metrics")
async def get_business_metrics(
    category: Optional[str] = Query(None, description="Metric category"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get business metrics"""
    try:
        metrics = monitoring_service.get_business_metrics(category, days)
        return JSONResponse(content=metrics)
    except Exception as e:
        logger.error(f"Error getting business metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get business metrics")

@router.post("/business/metrics")
async def record_business_metric(
    metric_name: str,
    category: str,
    value: float,
    user_id: Optional[str] = None,
    institution_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Record a business metric"""
    try:
        monitoring_service.track_business_metric(
            metric_name=metric_name,
            category=category,
            value=value,
            user_id=user_id,
            institution_id=institution_id,
            metadata=metadata
        )
        
        return JSONResponse(content={
            "message": "Business metric recorded successfully",
            "metric_name": metric_name,
            "category": category,
            "value": value
        })
    except Exception as e:
        logger.error(f"Error recording business metric: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record business metric")

@router.get("/alerts")
async def get_system_alerts(
    severity: Optional[str] = Query(None, description="Alert severity filter"),
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back")
):
    """Get system alerts"""
    try:
        with get_db_session() as session:
            from backend.services.comprehensive_monitoring_service import SystemAlert
            
            start_time = datetime.utcnow() - timedelta(hours=hours)
            query = session.query(SystemAlert).filter(
                SystemAlert.created_at >= start_time
            )
            
            if severity:
                query = query.filter(SystemAlert.severity == severity)
            
            alerts = query.order_by(SystemAlert.created_at.desc()).all()
            
            alert_data = [{
                'id': alert.id,
                'alert_name': alert.alert_name,
                'severity': alert.severity,
                'message': alert.message,
                'metric_name': alert.metric_name,
                'threshold_value': alert.threshold_value,
                'actual_value': alert.actual_value,
                'resolved': alert.resolved,
                'created_at': alert.created_at.isoformat(),
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
            } for alert in alerts]
            
            return JSONResponse(content=alert_data)
    except Exception as e:
        logger.error(f"Error getting system alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get system alerts")

@router.post("/alerts")
async def create_alert(
    alert_name: str,
    severity: str,
    message: str,
    metric_name: Optional[str] = None,
    threshold_value: Optional[float] = None,
    actual_value: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Create a system alert"""
    try:
        # Validate severity
        try:
            severity_enum = AlertSeverity(severity.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid alert severity")
        
        monitoring_service.create_alert(
            alert_name=alert_name,
            severity=severity_enum,
            message=message,
            metric_name=metric_name,
            threshold_value=threshold_value,
            actual_value=actual_value,
            metadata=metadata
        )
        
        return JSONResponse(content={
            "message": "Alert created successfully",
            "alert_name": alert_name,
            "severity": severity
        })
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create alert")

@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve a system alert"""
    try:
        with get_db_session() as session:
            from backend.services.comprehensive_monitoring_service import SystemAlert
            
            alert = session.query(SystemAlert).filter_by(id=alert_id).first()
            if not alert:
                raise HTTPException(status_code=404, detail="Alert not found")
            
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            session.commit()
            
            return JSONResponse(content={
                "message": "Alert resolved successfully",
                "alert_id": alert_id
            })
    except Exception as e:
        logger.error(f"Error resolving alert: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to resolve alert")

@router.get("/dashboard/data")
async def get_dashboard_data():
    """Get comprehensive dashboard data"""
    try:
        # Get all monitoring data for dashboard
        dashboard_data = {
            'system_health': monitoring_service.get_system_health(),
            'feature_usage': monitoring_service.get_feature_usage_stats(days=7),
            'performance_metrics': monitoring_service.get_performance_metrics(hours=24),
            'integration_health': monitoring_service.get_integration_health_status(),
            'business_metrics': monitoring_service.get_business_metrics(days=30),
            'recent_alerts': monitoring_service._get_recent_alerts(hours=24),
            'feature_flags': feature_flag_service.get_all_flags()
        }
        
        return JSONResponse(content=dashboard_data)
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")

@router.get("/export/metrics")
async def export_metrics(
    format: str = Query("json", description="Export format (json, csv)"),
    days: int = Query(7, ge=1, le=90, description="Number of days to export")
):
    """Export monitoring metrics"""
    try:
        if format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="Invalid export format")
        
        # Get all metrics
        export_data = {
            'feature_usage': monitoring_service.get_feature_usage_stats(days=days),
            'performance_metrics': monitoring_service.get_performance_metrics(hours=days*24),
            'business_metrics': monitoring_service.get_business_metrics(days=days),
            'export_timestamp': datetime.utcnow().isoformat(),
            'export_period_days': days
        }
        
        if format == "json":
            return JSONResponse(content=export_data)
        elif format == "csv":
            # Convert to CSV format (simplified)
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(['metric_type', 'metric_name', 'value', 'timestamp'])
            
            # Write feature usage data
            for feature, count in export_data['feature_usage'].get('feature_breakdown', {}).items():
                writer.writerow(['feature_usage', feature, count, datetime.utcnow().isoformat()])
            
            csv_content = output.getvalue()
            output.close()
            
            return JSONResponse(
                content=csv_content,
                headers={"Content-Type": "text/csv", "Content-Disposition": "attachment; filename=metrics.csv"}
            )
    except Exception as e:
        logger.error(f"Error exporting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export metrics")

# Middleware for automatic request tracking
@router.middleware("http")
async def track_api_requests(request: Request, call_next):
    """Middleware to track API request performance"""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        success = response.status_code < 400
        
        # Track API performance
        duration_ms = int((time.time() - start_time) * 1000)
        
        monitoring_service.track_feature_usage(
            feature_name="api_request",
            action=f"{request.method} {request.url.path}",
            duration_ms=duration_ms,
            success=success,
            metadata={
                'status_code': response.status_code,
                'method': request.method,
                'path': str(request.url.path)
            },
            user_agent=request.headers.get('user-agent'),
            ip_address=request.client.host if request.client else None
        )
        
        return response
    except Exception as e:
        # Track failed requests
        duration_ms = int((time.time() - start_time) * 1000)
        
        monitoring_service.track_feature_usage(
            feature_name="api_request",
            action=f"{request.method} {request.url.path}",
            duration_ms=duration_ms,
            success=False,
            error_message=str(e),
            user_agent=request.headers.get('user-agent'),
            ip_address=request.client.host if request.client else None
        )
        
        raise