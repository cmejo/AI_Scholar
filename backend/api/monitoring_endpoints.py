"""
API endpoints for system monitoring and performance management.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel

from services.monitoring_service import get_performance_monitor, get_performance_benchmark, AlertLevel, MetricType
from services.performance_testing import get_performance_tester, LoadTestConfig
from services.caching_service import get_caching_service
from core.database_optimization import db_optimizer, initialize_database_optimizations, perform_database_maintenance
from core.redis_client import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

# Pydantic models for request/response
class SystemHealthResponse(BaseModel):
    status: str
    health_score: float
    critical_alerts: int
    error_alerts: int
    latest_metrics: Dict[str, Any]
    timestamp: str

class MetricsResponse(BaseModel):
    metrics: List[Dict[str, Any]]
    metric_name: str
    time_range_hours: int

class AlertsResponse(BaseModel):
    alerts: List[Dict[str, Any]]
    total_count: int
    level_filter: Optional[str] = None

class LoadTestRequest(BaseModel):
    concurrent_users: int = 10
    test_duration_seconds: int = 60
    ramp_up_seconds: int = 10
    endpoint_weights: Optional[Dict[str, float]] = None
    think_time_seconds: float = 1.0

class BenchmarkResponse(BaseModel):
    benchmark_results: Dict[str, Any]
    report: str
    timestamp: str

class CacheStatsResponse(BaseModel):
    cache_stats: Dict[str, Any]
    timestamp: str

class DatabaseStatsResponse(BaseModel):
    database_stats: Dict[str, Any]
    timestamp: str

@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health():
    """Get overall system health status."""
    try:
        performance_monitor = get_performance_monitor()
        health_data = await performance_monitor.get_system_health()
        
        return SystemHealthResponse(
            status=health_data['status'],
            health_score=health_data['health_score'],
            critical_alerts=health_data['critical_alerts'],
            error_alerts=health_data['error_alerts'],
            latest_metrics=health_data['latest_metrics'],
            timestamp=health_data['timestamp']
        )
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/{metric_name}", response_model=MetricsResponse)
async def get_metrics(
    metric_name: str,
    hours: int = Query(24, ge=1, le=168, description="Hours of historical data (1-168)")
):
    """Get historical metrics for a specific metric."""
    try:
        performance_monitor = get_performance_monitor()
        metrics = await performance_monitor.get_metrics(metric_name, hours)
        
        return MetricsResponse(
            metrics=metrics,
            metric_name=metric_name,
            time_range_hours=hours
        )
    except Exception as e:
        logger.error(f"Error getting metrics for {metric_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts", response_model=AlertsResponse)
async def get_alerts(
    level: Optional[str] = Query(None, description="Filter by alert level: info, warning, error, critical"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of alerts to return")
):
    """Get recent system alerts."""
    try:
        performance_monitor = get_performance_monitor()
        
        alert_level = None
        if level:
            try:
                alert_level = AlertLevel(level.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid alert level: {level}")
        
        alerts = await performance_monitor.get_alerts(alert_level, limit)
        
        return AlertsResponse(
            alerts=alerts,
            total_count=len(alerts),
            level_filter=level
        )
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/thresholds")
async def get_alert_thresholds():
    """Get current alert thresholds."""
    try:
        performance_monitor = get_performance_monitor()
        thresholds = performance_monitor.get_thresholds()
        
        return {
            "thresholds": thresholds,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting thresholds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/thresholds/{metric_type}")
async def set_alert_threshold(
    metric_type: str,
    threshold: float = Query(..., description="New threshold value")
):
    """Set alert threshold for a metric type."""
    try:
        # Validate metric type
        try:
            metric_enum = MetricType(metric_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid metric type: {metric_type}")
        
        performance_monitor = get_performance_monitor()
        performance_monitor.set_threshold(metric_enum, threshold)
        
        return {
            "message": f"Threshold for {metric_type} set to {threshold}",
            "metric_type": metric_type,
            "threshold": threshold,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error setting threshold: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitoring/start")
async def start_monitoring(
    interval_seconds: int = Query(60, ge=10, le=300, description="Monitoring interval in seconds")
):
    """Start system monitoring."""
    try:
        performance_monitor = get_performance_monitor()
        await performance_monitor.start_monitoring(interval_seconds)
        
        return {
            "message": "Monitoring started",
            "interval_seconds": interval_seconds,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitoring/stop")
async def stop_monitoring():
    """Stop system monitoring."""
    try:
        performance_monitor = get_performance_monitor()
        await performance_monitor.stop_monitoring()
        
        return {
            "message": "Monitoring stopped",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/load-test")
async def run_load_test(
    config: LoadTestRequest,
    background_tasks: BackgroundTasks
):
    """Run a load test against the system."""
    try:
        performance_tester = get_performance_tester()
        
        # Convert request to config
        load_config = LoadTestConfig(
            concurrent_users=config.concurrent_users,
            test_duration_seconds=config.test_duration_seconds,
            ramp_up_seconds=config.ramp_up_seconds,
            endpoint_weights=config.endpoint_weights,
            think_time_seconds=config.think_time_seconds
        )
        
        # Run load test in background for long tests
        if config.test_duration_seconds > 60:
            background_tasks.add_task(performance_tester.run_load_test, load_config)
            return {
                "message": "Load test started in background",
                "config": config.dict(),
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Run synchronously for short tests
            result = await performance_tester.run_load_test(load_config)
            return {
                "message": "Load test completed",
                "results": result.__dict__,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error running load test: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/benchmark", response_model=BenchmarkResponse)
async def run_performance_benchmark():
    """Run comprehensive performance benchmark."""
    try:
        performance_tester = get_performance_tester()
        benchmark_results = await performance_tester.run_comprehensive_benchmark()
        report = performance_tester.generate_performance_report(benchmark_results)
        
        return BenchmarkResponse(
            benchmark_results=benchmark_results,
            report=report,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error running benchmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sla-compliance")
async def get_sla_compliance(
    hours: int = Query(24, ge=1, le=168, description="Hours to analyze for SLA compliance")
):
    """Get SLA compliance report."""
    try:
        performance_benchmark = get_performance_benchmark()
        compliance_data = performance_benchmark.get_all_sla_compliance(hours)
        
        # Calculate overall compliance
        compliant_benchmarks = sum(1 for c in compliance_data.values() 
                                 if isinstance(c, dict) and c.get('meets_sla', False))
        total_benchmarks = len([c for c in compliance_data.values() if isinstance(c, dict)])
        overall_compliance = compliant_benchmarks / total_benchmarks if total_benchmarks > 0 else 0
        
        return {
            "overall_compliance": overall_compliance,
            "compliant_benchmarks": compliant_benchmarks,
            "total_benchmarks": total_benchmarks,
            "benchmark_details": compliance_data,
            "time_range_hours": hours,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting SLA compliance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """Get cache performance statistics."""
    try:
        caching_service = get_caching_service()
        cache_stats = caching_service.get_cache_stats()
        
        return CacheStatsResponse(
            cache_stats=cache_stats,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/clear")
async def clear_cache(
    pattern: Optional[str] = Query(None, description="Pattern to match for selective clearing")
):
    """Clear cache entries."""
    try:
        caching_service = get_caching_service()
        await caching_service.cache.clear(pattern)
        
        return {
            "message": "Cache cleared successfully",
            "pattern": pattern,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database/stats", response_model=DatabaseStatsResponse)
async def get_database_stats():
    """Get database performance statistics."""
    try:
        database_stats = await db_optimizer.get_database_statistics()
        
        return DatabaseStatsResponse(
            database_stats=database_stats,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/database/optimize")
async def optimize_database(background_tasks: BackgroundTasks):
    """Optimize database performance."""
    try:
        # Run optimization in background as it can take time
        background_tasks.add_task(initialize_database_optimizations)
        
        return {
            "message": "Database optimization started in background",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting database optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/database/maintenance")
async def run_database_maintenance(background_tasks: BackgroundTasks):
    """Run database maintenance operations."""
    try:
        # Run maintenance in background as it can take time
        background_tasks.add_task(perform_database_maintenance)
        
        return {
            "message": "Database maintenance started in background",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting database maintenance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database/slow-queries")
async def get_slow_queries(
    threshold_seconds: float = Query(1.0, ge=0.1, le=10.0, description="Threshold for slow queries in seconds")
):
    """Get slow query analysis."""
    try:
        slow_queries = await db_optimizer.monitor_slow_queries(threshold_seconds)
        
        return {
            "slow_queries": slow_queries,
            "threshold_seconds": threshold_seconds,
            "total_slow_queries": len(slow_queries),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting slow queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/redis/info")
async def get_redis_info():
    """Get Redis server information."""
    try:
        redis_client = get_redis_client()
        
        if not redis_client.redis_client:
            raise HTTPException(status_code=503, detail="Redis not connected")
        
        info = await redis_client.redis_client.info()
        
        # Extract key metrics
        key_metrics = {
            'connected_clients': info.get('connected_clients', 0),
            'used_memory': info.get('used_memory', 0),
            'used_memory_human': info.get('used_memory_human', '0B'),
            'keyspace_hits': info.get('keyspace_hits', 0),
            'keyspace_misses': info.get('keyspace_misses', 0),
            'total_commands_processed': info.get('total_commands_processed', 0),
            'uptime_in_seconds': info.get('uptime_in_seconds', 0)
        }
        
        # Calculate hit rate
        hits = key_metrics['keyspace_hits']
        misses = key_metrics['keyspace_misses']
        hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
        
        return {
            "redis_info": key_metrics,
            "hit_rate": hit_rate,
            "full_info": info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting Redis info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-summary")
async def get_performance_summary():
    """Get a comprehensive performance summary."""
    try:
        performance_monitor = get_performance_monitor()
        performance_benchmark = get_performance_benchmark()
        caching_service = get_caching_service()
        
        # Get system health
        system_health = await performance_monitor.get_system_health()
        
        # Get SLA compliance
        sla_compliance = performance_benchmark.get_all_sla_compliance(24)
        
        # Get cache stats
        cache_stats = caching_service.get_cache_stats()
        
        # Get database stats
        db_stats = await db_optimizer.get_database_statistics()
        
        # Calculate summary metrics
        compliant_slas = sum(1 for c in sla_compliance.values() 
                           if isinstance(c, dict) and c.get('meets_sla', False))
        total_slas = len([c for c in sla_compliance.values() if isinstance(c, dict)])
        sla_compliance_rate = compliant_slas / total_slas if total_slas > 0 else 0
        
        return {
            "summary": {
                "system_status": system_health['status'],
                "health_score": system_health['health_score'],
                "sla_compliance_rate": sla_compliance_rate,
                "cache_hit_rate": cache_stats.get('overall_cache_hit_rate', 0),
                "total_documents": db_stats.get('total_documents', 0),
                "total_users": db_stats.get('total_users', 0),
                "database_size_mb": db_stats.get('database_size', 0) / (1024 * 1024)
            },
            "detailed_metrics": {
                "system_health": system_health,
                "sla_compliance": sla_compliance,
                "cache_stats": cache_stats,
                "database_stats": db_stats
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))