#!/usr/bin/env python3
"""
Advanced Metrics Collection System for AI Scholar
Collects comprehensive metrics for AI operations, system performance, and user behavior
"""

import asyncio
import time
import psutil
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging
import sqlite3
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """Individual metric data point"""
    timestamp: float
    value: float
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class AIMetrics:
    """AI-specific metrics"""
    embedding_generation_time: List[float] = field(default_factory=list)
    rag_response_time: List[float] = field(default_factory=list)
    document_processing_time: List[float] = field(default_factory=list)
    cache_hit_rates: Dict[str, float] = field(default_factory=dict)
    model_usage: Dict[str, int] = field(default_factory=dict)
    confidence_scores: List[float] = field(default_factory=list)
    error_rates: Dict[str, float] = field(default_factory=dict)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_usage: List[float] = field(default_factory=list)
    memory_usage: List[float] = field(default_factory=list)
    disk_usage: List[float] = field(default_factory=list)
    network_io: List[Dict[str, float]] = field(default_factory=list)
    active_connections: List[int] = field(default_factory=list)
    response_times: List[float] = field(default_factory=list)

@dataclass
class UserMetrics:
    """User behavior metrics"""
    active_users: int = 0
    session_durations: List[float] = field(default_factory=list)
    query_counts: Dict[str, int] = field(default_factory=dict)
    feature_usage: Dict[str, int] = field(default_factory=dict)
    error_encounters: Dict[str, int] = field(default_factory=dict)

class AdvancedMetricsCollector:
    """Advanced metrics collection system"""
    
    def __init__(self, db_path: str = "metrics.db"):
        self.db_path = db_path
        self.ai_metrics = AIMetrics()
        self.system_metrics = SystemMetrics()
        self.user_metrics = UserMetrics()
        
        # Time series storage
        self.time_series: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Aggregation windows
        self.aggregation_windows = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "1h": 3600,
            "1d": 86400
        }
        
        # Initialize database
        self._init_database()
        
        # Collection intervals
        self.collection_interval = 30  # seconds
        self.is_collecting = False
    
    def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                operation_type TEXT NOT NULL,
                duration REAL NOT NULL,
                model_used TEXT,
                input_size INTEGER,
                output_size INTEGER,
                confidence REAL,
                success BOOLEAN,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                cpu_percent REAL,
                memory_percent REAL,
                disk_percent REAL,
                network_bytes_sent INTEGER,
                network_bytes_recv INTEGER,
                active_connections INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_ops_timestamp ON ai_operations(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_timestamp ON system_health(timestamp)')
        
        conn.commit()
        conn.close()
    
    async def start_collection(self):
        """Start automatic metrics collection"""
        if self.is_collecting:
            return
        
        self.is_collecting = True
        logger.info("Starting advanced metrics collection")
        
        # Start collection tasks
        tasks = [
            asyncio.create_task(self._collect_system_metrics()),
            asyncio.create_task(self._collect_ai_metrics()),
            asyncio.create_task(self._collect_user_metrics()),
            asyncio.create_task(self._cleanup_old_metrics())
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop_collection(self):
        """Stop metrics collection"""
        self.is_collecting = False
        logger.info("Stopping metrics collection")
    
    async def _collect_system_metrics(self):
        """Collect system performance metrics"""
        while self.is_collecting:
            try:
                current_time = time.time()
                
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.system_metrics.cpu_usage.append(cpu_percent)
                self._record_metric("system.cpu.percent", cpu_percent, current_time)
                
                # Memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                self.system_metrics.memory_usage.append(memory_percent)
                self._record_metric("system.memory.percent", memory_percent, current_time)
                self._record_metric("system.memory.available_gb", memory.available / (1024**3), current_time)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                self.system_metrics.disk_usage.append(disk_percent)
                self._record_metric("system.disk.percent", disk_percent, current_time)
                
                # Network I/O
                network = psutil.net_io_counters()
                network_data = {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
                self.system_metrics.network_io.append(network_data)
                self._record_metric("system.network.bytes_sent", network.bytes_sent, current_time)
                self._record_metric("system.network.bytes_recv", network.bytes_recv, current_time)
                
                # Process information
                process = psutil.Process()
                self._record_metric("system.process.memory_mb", process.memory_info().rss / (1024**2), current_time)
                self._record_metric("system.process.cpu_percent", process.cpu_percent(), current_time)
                
                # Store in database
                await self._store_system_health(current_time, cpu_percent, memory_percent, disk_percent, network)
                
                # Keep only recent metrics in memory
                self._trim_metrics_lists()
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
            
            await asyncio.sleep(self.collection_interval)
    
    async def _collect_ai_metrics(self):
        """Collect AI-specific metrics"""
        while self.is_collecting:
            try:
                current_time = time.time()
                
                # This would integrate with your AI services to collect metrics
                # For now, we'll simulate some metrics
                
                # Cache hit rates (would come from cache manager)
                cache_metrics = {
                    "embeddings": 0.75,
                    "rag_responses": 0.60,
                    "document_summaries": 0.80
                }
                
                for cache_type, hit_rate in cache_metrics.items():
                    self.ai_metrics.cache_hit_rates[cache_type] = hit_rate
                    self._record_metric(f"ai.cache.hit_rate.{cache_type}", hit_rate, current_time)
                
                # Model usage statistics (would come from AI service)
                model_usage = {
                    "gpt-4-turbo": 150,
                    "sentence-transformers": 300,
                    "claude-3": 75
                }
                
                for model, usage_count in model_usage.items():
                    self.ai_metrics.model_usage[model] = usage_count
                    self._record_metric(f"ai.model.usage.{model}", usage_count, current_time)
                
                # Error rates
                error_rates = {
                    "embedding_generation": 0.02,
                    "rag_processing": 0.05,
                    "document_processing": 0.01
                }
                
                for operation, error_rate in error_rates.items():
                    self.ai_metrics.error_rates[operation] = error_rate
                    self._record_metric(f"ai.error_rate.{operation}", error_rate, current_time)
                
            except Exception as e:
                logger.error(f"Error collecting AI metrics: {e}")
            
            await asyncio.sleep(self.collection_interval)
    
    async def _collect_user_metrics(self):
        """Collect user behavior metrics"""
        while self.is_collecting:
            try:
                current_time = time.time()
                
                # This would integrate with your user tracking system
                # For now, we'll simulate some metrics
                
                # Active users (would come from session manager)
                active_users = 25  # Simulated
                self.user_metrics.active_users = active_users
                self._record_metric("users.active_count", active_users, current_time)
                
                # Feature usage (would come from analytics)
                feature_usage = {
                    "document_upload": 45,
                    "ai_chat": 120,
                    "search": 80,
                    "export": 15
                }
                
                for feature, usage_count in feature_usage.items():
                    self.user_metrics.feature_usage[feature] = usage_count
                    self._record_metric(f"users.feature_usage.{feature}", usage_count, current_time)
                
            except Exception as e:
                logger.error(f"Error collecting user metrics: {e}")
            
            await asyncio.sleep(self.collection_interval * 2)  # Less frequent collection
    
    def _record_metric(self, metric_name: str, value: float, timestamp: float, tags: Dict[str, str] = None):
        """Record a metric point"""
        metric_point = MetricPoint(timestamp, value, tags or {})
        self.time_series[metric_name].append(metric_point)
    
    async def _store_system_health(self, timestamp: float, cpu: float, memory: float, disk: float, network):
        """Store system health metrics in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_health 
                (timestamp, cpu_percent, memory_percent, disk_percent, 
                 network_bytes_sent, network_bytes_recv, active_connections)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, cpu, memory, disk, network.bytes_sent, network.bytes_recv, 0))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error storing system health: {e}")
    
    def record_ai_operation(self, operation_type: str, duration: float, model_used: str = None,
                           input_size: int = None, output_size: int = None, confidence: float = None,
                           success: bool = True, error_message: str = None):
        """Record an AI operation"""
        try:
            timestamp = time.time()
            
            # Add to in-memory metrics
            if operation_type == "embedding_generation":
                self.ai_metrics.embedding_generation_time.append(duration)
            elif operation_type == "rag_processing":
                self.ai_metrics.rag_response_time.append(duration)
            elif operation_type == "document_processing":
                self.ai_metrics.document_processing_time.append(duration)
            
            if confidence is not None:
                self.ai_metrics.confidence_scores.append(confidence)
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO ai_operations 
                (timestamp, operation_type, duration, model_used, input_size, 
                 output_size, confidence, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, operation_type, duration, model_used, input_size,
                  output_size, confidence, success, error_message))
            
            conn.commit()
            conn.close()
            
            # Record time series metrics
            self._record_metric(f"ai.operation.{operation_type}.duration", duration, timestamp)
            self._record_metric(f"ai.operation.{operation_type}.count", 1, timestamp)
            
            if not success:
                self._record_metric(f"ai.operation.{operation_type}.errors", 1, timestamp)
            
        except Exception as e:
            logger.error(f"Error recording AI operation: {e}")
    
    def _trim_metrics_lists(self):
        """Trim metrics lists to prevent memory issues"""
        max_length = 1000
        
        # Trim system metrics
        for attr_name in ['cpu_usage', 'memory_usage', 'disk_usage', 'network_io', 'response_times']:
            attr_list = getattr(self.system_metrics, attr_name)
            if len(attr_list) > max_length:
                setattr(self.system_metrics, attr_name, attr_list[-max_length:])
        
        # Trim AI metrics
        for attr_name in ['embedding_generation_time', 'rag_response_time', 'document_processing_time', 'confidence_scores']:
            attr_list = getattr(self.ai_metrics, attr_name)
            if len(attr_list) > max_length:
                setattr(self.ai_metrics, attr_name, attr_list[-max_length:])
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics from database"""
        while self.is_collecting:
            try:
                # Clean up metrics older than 30 days
                cutoff_time = time.time() - (30 * 24 * 3600)
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Clean up old metrics
                cursor.execute('DELETE FROM metrics WHERE timestamp < ?', (cutoff_time,))
                cursor.execute('DELETE FROM ai_operations WHERE timestamp < ?', (cutoff_time,))
                cursor.execute('DELETE FROM system_health WHERE timestamp < ?', (cutoff_time,))
                
                # Vacuum database to reclaim space
                cursor.execute('VACUUM')
                
                conn.commit()
                conn.close()
                
                logger.info("Cleaned up old metrics from database")
                
            except Exception as e:
                logger.error(f"Error cleaning up old metrics: {e}")
            
            # Run cleanup once per day
            await asyncio.sleep(24 * 3600)
    
    def get_metrics_summary(self, time_range: str = "1h") -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        try:
            end_time = time.time()
            start_time = end_time - self.aggregation_windows.get(time_range, 3600)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # System metrics summary
            cursor.execute('''
                SELECT AVG(cpu_percent), AVG(memory_percent), AVG(disk_percent),
                       MIN(cpu_percent), MAX(cpu_percent),
                       MIN(memory_percent), MAX(memory_percent)
                FROM system_health 
                WHERE timestamp BETWEEN ? AND ?
            ''', (start_time, end_time))
            
            system_row = cursor.fetchone()
            system_summary = {
                "cpu": {
                    "avg": system_row[0] or 0,
                    "min": system_row[3] or 0,
                    "max": system_row[4] or 0
                },
                "memory": {
                    "avg": system_row[1] or 0,
                    "min": system_row[5] or 0,
                    "max": system_row[6] or 0
                },
                "disk": {
                    "avg": system_row[2] or 0
                }
            }
            
            # AI operations summary
            cursor.execute('''
                SELECT operation_type, COUNT(*), AVG(duration), 
                       SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as errors,
                       AVG(confidence)
                FROM ai_operations 
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY operation_type
            ''', (start_time, end_time))
            
            ai_operations = {}
            for row in cursor.fetchall():
                op_type, count, avg_duration, errors, avg_confidence = row
                ai_operations[op_type] = {
                    "count": count,
                    "avg_duration": avg_duration or 0,
                    "error_count": errors,
                    "error_rate": (errors / count) if count > 0 else 0,
                    "avg_confidence": avg_confidence or 0
                }
            
            conn.close()
            
            # Current metrics
            current_metrics = {
                "active_users": self.user_metrics.active_users,
                "cache_hit_rates": self.ai_metrics.cache_hit_rates,
                "model_usage": self.ai_metrics.model_usage
            }
            
            return {
                "time_range": time_range,
                "start_time": start_time,
                "end_time": end_time,
                "system": system_summary,
                "ai_operations": ai_operations,
                "current": current_metrics,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error generating metrics summary: {e}")
            return {"error": str(e)}
    
    def get_ai_performance_metrics(self) -> Dict[str, Any]:
        """Get AI-specific performance metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent AI operations (last hour)
            one_hour_ago = time.time() - 3600
            
            cursor.execute('''
                SELECT operation_type, AVG(duration), COUNT(*), 
                       AVG(confidence), SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END)
                FROM ai_operations 
                WHERE timestamp > ?
                GROUP BY operation_type
            ''', (one_hour_ago,))
            
            operations = {}
            for row in cursor.fetchall():
                op_type, avg_duration, count, avg_confidence, errors = row
                operations[op_type] = {
                    "avg_duration": avg_duration,
                    "count": count,
                    "avg_confidence": avg_confidence,
                    "error_count": errors,
                    "error_rate": (errors / count) if count > 0 else 0
                }
            
            # Get model performance
            cursor.execute('''
                SELECT model_used, AVG(duration), COUNT(*)
                FROM ai_operations 
                WHERE timestamp > ? AND model_used IS NOT NULL
                GROUP BY model_used
            ''', (one_hour_ago,))
            
            models = {}
            for row in cursor.fetchall():
                model, avg_duration, count = row
                models[model] = {
                    "avg_duration": avg_duration,
                    "usage_count": count
                }
            
            conn.close()
            
            return {
                "operations": operations,
                "models": models,
                "cache_hit_rates": self.ai_metrics.cache_hit_rates,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting AI performance metrics: {e}")
            return {"error": str(e)}
    
    def export_metrics(self, output_file: str, time_range: str = "24h") -> bool:
        """Export metrics to JSON file"""
        try:
            end_time = time.time()
            start_time = end_time - self.aggregation_windows.get(time_range, 86400)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Export all metrics
            export_data = {
                "export_info": {
                    "timestamp": time.time(),
                    "time_range": time_range,
                    "start_time": start_time,
                    "end_time": end_time
                },
                "system_health": [],
                "ai_operations": [],
                "metrics": []
            }
            
            # System health data
            cursor.execute('''
                SELECT * FROM system_health 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            ''', (start_time, end_time))
            
            columns = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                export_data["system_health"].append(dict(zip(columns, row)))
            
            # AI operations data
            cursor.execute('''
                SELECT * FROM ai_operations 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            ''', (start_time, end_time))
            
            columns = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                export_data["ai_operations"].append(dict(zip(columns, row)))
            
            # General metrics data
            cursor.execute('''
                SELECT * FROM metrics 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            ''', (start_time, end_time))
            
            columns = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                export_data["metrics"].append(dict(zip(columns, row)))
            
            conn.close()
            
            # Write to file
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Metrics exported to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return False

# Global metrics collector instance
metrics_collector = AdvancedMetricsCollector()

# Convenience functions
async def start_metrics_collection():
    """Start metrics collection"""
    await metrics_collector.start_collection()

async def stop_metrics_collection():
    """Stop metrics collection"""
    await metrics_collector.stop_collection()

def record_ai_operation(operation_type: str, duration: float, **kwargs):
    """Record an AI operation"""
    metrics_collector.record_ai_operation(operation_type, duration, **kwargs)

def get_performance_dashboard() -> Dict[str, Any]:
    """Get performance dashboard data"""
    return {
        "summary": metrics_collector.get_metrics_summary("1h"),
        "ai_performance": metrics_collector.get_ai_performance_metrics(),
        "system_status": "healthy"  # This could be calculated based on thresholds
    }

# Usage example
if __name__ == "__main__":
    async def test_metrics_collection():
        # Start collection
        collection_task = asyncio.create_task(metrics_collector.start_collection())
        
        # Simulate some AI operations
        for i in range(10):
            metrics_collector.record_ai_operation(
                "embedding_generation",
                duration=0.1 + (i * 0.01),
                model_used="test-model",
                input_size=1000,
                confidence=0.8 + (i * 0.01),
                success=True
            )
            await asyncio.sleep(1)
        
        # Get metrics summary
        summary = metrics_collector.get_metrics_summary("5m")
        print(f"Metrics Summary: {json.dumps(summary, indent=2)}")
        
        # Export metrics
        success = metrics_collector.export_metrics("test_metrics_export.json", "1h")
        print(f"Export successful: {success}")
        
        # Stop collection
        await metrics_collector.stop_collection()
    
    # Run test
    asyncio.run(test_metrics_collection())