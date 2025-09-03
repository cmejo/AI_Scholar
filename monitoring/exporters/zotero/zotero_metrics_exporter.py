#!/usr/bin/env python3
"""
Zotero Integration Metrics Exporter

This service exports custom metrics for Zotero integration monitoring.
It collects metrics from the database and Redis, then exposes them
in Prometheus format.
"""

import os
import time
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

import psycopg2
import redis
import uvicorn
from fastapi import FastAPI, Response
from prometheus_client import (
    Counter, Gauge, Histogram, Info,
    generate_latest, CONTENT_TYPE_LATEST
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
zotero_info = Info('zotero_integration', 'Zotero integration information')
zotero_active_connections = Gauge('zotero_active_connections', 'Number of active Zotero connections')
zotero_libraries_total = Gauge('zotero_libraries_total', 'Total number of Zotero libraries')
zotero_items_total = Gauge('zotero_items_total', 'Total number of Zotero items')
zotero_sync_operations_total = Counter('zotero_sync_operations_total', 'Total sync operations', ['status'])
zotero_sync_duration = Histogram('zotero_sync_duration_seconds', 'Sync operation duration')
zotero_api_requests_total = Counter('zotero_api_requests_total', 'Total API requests', ['endpoint', 'method'])
zotero_api_errors_total = Counter('zotero_api_errors_total', 'Total API errors', ['endpoint', 'error_type'])
zotero_cache_hits_total = Counter('zotero_cache_hits_total', 'Total cache hits')
zotero_cache_misses_total = Counter('zotero_cache_misses_total', 'Total cache misses')
zotero_storage_used_bytes = Gauge('zotero_storage_used_bytes', 'Storage space used in bytes')
zotero_storage_total_bytes = Gauge('zotero_storage_total_bytes', 'Total storage space in bytes')
zotero_sync_queue_size = Gauge('zotero_sync_queue_size', 'Number of items in sync queue')
zotero_auth_success_total = Counter('zotero_auth_success_total', 'Total successful authentications')
zotero_auth_failures_total = Counter('zotero_auth_failures_total', 'Total authentication failures')
zotero_database_connections_active = Gauge('zotero_database_connections_active', 'Active database connections')
zotero_database_connections_idle = Gauge('zotero_database_connections_idle', 'Idle database connections')

class ZoteroMetricsExporter:
    """Zotero metrics exporter service."""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'ai_scholar'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }
        
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = None
        self.db_connection = None
        
        # Initialize info metric
        zotero_info.info({
            'version': os.getenv('DEPLOYMENT_VERSION', 'unknown'),
            'environment': os.getenv('ENVIRONMENT', 'unknown'),
            'build_date': os.getenv('BUILD_DATE', 'unknown')
        })
    
    def connect_database(self) -> Optional[psycopg2.extensions.connection]:
        """Connect to PostgreSQL database."""
        try:
            conn = psycopg2.connect(**self.db_config)
            logger.info("Connected to database")
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def connect_redis(self) -> Optional[redis.Redis]:
        """Connect to Redis."""
        try:
            client = redis.from_url(self.redis_url)
            client.ping()
            logger.info("Connected to Redis")
            return client
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return None
    
    def collect_database_metrics(self):
        """Collect metrics from the database."""
        if not self.db_connection:
            self.db_connection = self.connect_database()
            if not self.db_connection:
                return
        
        try:
            cursor = self.db_connection.cursor()
            
            # Active connections count
            cursor.execute("""
                SELECT COUNT(*) FROM zotero.zotero_connections 
                WHERE status = 'active' AND expires_at > NOW();
            """)
            active_connections = cursor.fetchone()[0]
            zotero_active_connections.set(active_connections)
            
            # Total libraries
            cursor.execute("SELECT COUNT(*) FROM zotero.zotero_libraries;")
            total_libraries = cursor.fetchone()[0]
            zotero_libraries_total.set(total_libraries)
            
            # Total items
            cursor.execute("SELECT COUNT(*) FROM zotero.zotero_items;")
            total_items = cursor.fetchone()[0]
            zotero_items_total.set(total_items)
            
            # Sync operations (last 24 hours)
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM zotero.zotero_sync_logs 
                WHERE created_at > NOW() - INTERVAL '24 hours'
                GROUP BY status;
            """)
            
            sync_stats = cursor.fetchall()
            for status, count in sync_stats:
                # Update counter with the difference
                current_value = zotero_sync_operations_total.labels(status=status)._value._value
                if count > current_value:
                    zotero_sync_operations_total.labels(status=status).inc(count - current_value)
            
            # Authentication metrics (last 24 hours)
            cursor.execute("""
                SELECT 
                    CASE WHEN success THEN 'success' ELSE 'failure' END as result,
                    COUNT(*) as count
                FROM zotero.zotero_auth_logs 
                WHERE created_at > NOW() - INTERVAL '24 hours'
                GROUP BY success;
            """)
            
            auth_stats = cursor.fetchall()
            for result, count in auth_stats:
                if result == 'success':
                    current_value = zotero_auth_success_total._value._value
                    if count > current_value:
                        zotero_auth_success_total.inc(count - current_value)
                else:
                    current_value = zotero_auth_failures_total._value._value
                    if count > current_value:
                        zotero_auth_failures_total.inc(count - current_value)
            
            # Database connection pool stats
            cursor.execute("""
                SELECT 
                    state,
                    COUNT(*) as count
                FROM pg_stat_activity 
                WHERE datname = %s
                GROUP BY state;
            """, (self.db_config['database'],))
            
            connection_stats = cursor.fetchall()
            active_conns = 0
            idle_conns = 0
            
            for state, count in connection_stats:
                if state == 'active':
                    active_conns = count
                elif state == 'idle':
                    idle_conns = count
            
            zotero_database_connections_active.set(active_conns)
            zotero_database_connections_idle.set(idle_conns)
            
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            # Reconnect on next iteration
            if self.db_connection:
                self.db_connection.close()
                self.db_connection = None
    
    def collect_redis_metrics(self):
        """Collect metrics from Redis."""
        if not self.redis_client:
            self.redis_client = self.connect_redis()
            if not self.redis_client:
                return
        
        try:
            # Cache hit/miss stats
            info = self.redis_client.info()
            
            # Sync queue size
            queue_size = self.redis_client.llen('zotero:sync_queue') or 0
            zotero_sync_queue_size.set(queue_size)
            
            # Cache statistics (if available)
            if 'keyspace_hits' in info:
                hits = info['keyspace_hits']
                current_hits = zotero_cache_hits_total._value._value
                if hits > current_hits:
                    zotero_cache_hits_total.inc(hits - current_hits)
            
            if 'keyspace_misses' in info:
                misses = info['keyspace_misses']
                current_misses = zotero_cache_misses_total._value._value
                if misses > current_misses:
                    zotero_cache_misses_total.inc(misses - current_misses)
            
        except Exception as e:
            logger.error(f"Error collecting Redis metrics: {e}")
            # Reconnect on next iteration
            self.redis_client = None
    
    def collect_storage_metrics(self):
        """Collect storage metrics."""
        try:
            attachment_path = os.getenv('ZOTERO_ATTACHMENT_PATH', '/app/data/zotero_attachments')
            
            if os.path.exists(attachment_path):
                # Calculate used storage
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(attachment_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        try:
                            total_size += os.path.getsize(filepath)
                        except (OSError, IOError):
                            continue
                
                zotero_storage_used_bytes.set(total_size)
                
                # Get total available space
                statvfs = os.statvfs(attachment_path)
                total_space = statvfs.f_frsize * statvfs.f_blocks
                zotero_storage_total_bytes.set(total_space)
            
        except Exception as e:
            logger.error(f"Error collecting storage metrics: {e}")
    
    def collect_all_metrics(self):
        """Collect all metrics."""
        logger.info("Collecting metrics...")
        
        self.collect_database_metrics()
        self.collect_redis_metrics()
        self.collect_storage_metrics()
        
        logger.info("Metrics collection completed")

# FastAPI app for serving metrics
app = FastAPI(title="Zotero Metrics Exporter", version="1.0.0")
exporter = ZoteroMetricsExporter()

@app.get("/metrics")
async def metrics():
    """Serve Prometheus metrics."""
    exporter.collect_all_metrics()
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv('DEPLOYMENT_VERSION', 'unknown')
    }

@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "service": "Zotero Metrics Exporter",
        "version": os.getenv('DEPLOYMENT_VERSION', 'unknown'),
        "endpoints": {
            "metrics": "/metrics",
            "health": "/health"
        }
    }

async def metrics_collection_loop():
    """Background task to collect metrics periodically."""
    while True:
        try:
            exporter.collect_all_metrics()
            await asyncio.sleep(30)  # Collect every 30 seconds
        except Exception as e:
            logger.error(f"Error in metrics collection loop: {e}")
            await asyncio.sleep(60)  # Wait longer on error

@app.on_event("startup")
async def startup_event():
    """Start background metrics collection."""
    asyncio.create_task(metrics_collection_loop())
    logger.info("Zotero Metrics Exporter started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if exporter.db_connection:
        exporter.db_connection.close()
    if exporter.redis_client:
        exporter.redis_client.close()
    logger.info("Zotero Metrics Exporter stopped")

if __name__ == "__main__":
    port = int(os.getenv("METRICS_PORT", 9999))
    host = os.getenv("METRICS_HOST", "0.0.0.0")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )