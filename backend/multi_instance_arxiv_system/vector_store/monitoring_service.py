"""
Vector Store Monitoring Service for Multi-Instance System.

This module provides comprehensive monitoring capabilities for vector store
collections including statistics, health monitoring, and performance tracking.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import asyncio
import json
import numpy as np
from dataclasses import dataclass, asdict
from enum import Enum

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.vector_store.multi_instance_vector_store_service import MultiInstanceVectorStoreService
    from multi_instance_arxiv_system.shared.multi_instance_data_models import (
        MonitoringAlert, ProcessingMetrics, QualityMetrics
    )
except ImportError as e:
    print(f"Import error: {e}")
    raise

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class CollectionHealth:
    """Health information for a collection."""
    
    instance_name: str
    collection_name: str
    status: HealthStatus
    document_count: int
    last_updated: datetime
    
    # Performance metrics
    average_query_time_ms: float
    embedding_quality_score: float
    storage_size_mb: float
    
    # Issues and warnings
    issues: List[str]
    warnings: List[str]
    
    # Detailed metrics
    metadata_completeness: float
    duplicate_rate: float
    error_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        data['last_updated'] = self.last_updated.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollectionHealth':
        """Create from dictionary (JSON deserialization)."""
        data['status'] = HealthStatus(data['status'])
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)


@dataclass
class PerformanceSnapshot:
    """Performance snapshot for monitoring."""
    
    timestamp: datetime
    instance_name: str
    
    # Query performance
    query_count: int
    average_query_time_ms: float
    slow_query_count: int
    
    # Embedding performance
    embedding_generation_rate: float
    embedding_cache_hit_rate: float
    
    # Resource usage
    memory_usage_mb: int
    cpu_usage_percent: float
    disk_io_rate_mbps: float
    
    # Quality metrics
    average_relevance_score: float
    result_quality_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceSnapshot':
        """Create from dictionary (JSON deserialization)."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class VectorStoreMonitoringService:
    """
    Comprehensive monitoring service for multi-instance vector store.
    Provides health monitoring, performance tracking, and alerting.
    """
    
    def __init__(self, vector_store_service: MultiInstanceVectorStoreService):
        self.vector_store_service = vector_store_service
        self.monitoring_history: List[PerformanceSnapshot] = []
        self.alerts: List[MonitoringAlert] = []
        self.max_history_size = 1000
        
        # Monitoring configuration
        self.monitoring_config = {
            'health_check_interval_minutes': 15,
            'performance_snapshot_interval_minutes': 5,
            'slow_query_threshold_ms': 1000,
            'low_quality_threshold': 0.5,
            'high_error_rate_threshold': 0.1,
            'memory_warning_threshold_mb': 4096,
            'cpu_warning_threshold_percent': 80
        }
        
        # Performance tracking
        self.query_times: Dict[str, List[float]] = {}
        self.query_counts: Dict[str, int] = {}
        self.last_health_check: Optional[datetime] = None
        
    async def start_monitoring(self) -> None:
        """Start continuous monitoring of vector store instances."""
        
        logger.info("Starting vector store monitoring service")
        
        # Initial health check
        await self.perform_health_check()
        
        # Start monitoring tasks
        asyncio.create_task(self._continuous_health_monitoring())
        asyncio.create_task(self._continuous_performance_monitoring())
        
    async def _continuous_health_monitoring(self) -> None:
        """Continuous health monitoring task."""
        
        while True:
            try:
                await asyncio.sleep(self.monitoring_config['health_check_interval_minutes'] * 60)
                await self.perform_health_check()
            except Exception as e:
                logger.error(f"Error in continuous health monitoring: {e}")
    
    async def _continuous_performance_monitoring(self) -> None:
        """Continuous performance monitoring task."""
        
        while True:
            try:
                await asyncio.sleep(self.monitoring_config['performance_snapshot_interval_minutes'] * 60)
                await self.capture_performance_snapshot()
            except Exception as e:
                logger.error(f"Error in continuous performance monitoring: {e}")
    
    async def perform_health_check(self) -> Dict[str, CollectionHealth]:
        """Perform comprehensive health check on all instances."""
        
        logger.info("Performing vector store health check")
        
        health_results = {}
        
        for instance_name in self.vector_store_service.initialized_instances:
            try:
                health = await self._check_instance_health(instance_name)
                health_results[instance_name] = health
                
                # Generate alerts for issues
                await self._process_health_alerts(health)
                
            except Exception as e:
                logger.error(f"Health check failed for {instance_name}: {e}")
                
                # Create error health status
                health_results[instance_name] = CollectionHealth(
                    instance_name=instance_name,
                    collection_name="unknown",
                    status=HealthStatus.ERROR,
                    document_count=0,
                    last_updated=datetime.now(),
                    average_query_time_ms=0.0,
                    embedding_quality_score=0.0,
                    storage_size_mb=0.0,
                    issues=[f"Health check failed: {str(e)}"],
                    warnings=[],
                    metadata_completeness=0.0,
                    duplicate_rate=0.0,
                    error_rate=1.0
                )
        
        self.last_health_check = datetime.now()
        logger.info(f"Health check completed for {len(health_results)} instances")
        
        return health_results
    
    async def _check_instance_health(self, instance_name: str) -> CollectionHealth:
        """Check health of a specific instance."""
        
        service = self.vector_store_service.instance_services.get(instance_name)
        if not service or not service.collection:
            raise ValueError(f"Instance {instance_name} not properly initialized")
        
        collection = service.collection
        
        # Basic collection info
        document_count = collection.count()
        collection_name = service.collection_name
        
        # Initialize health status
        status = HealthStatus.HEALTHY
        issues = []
        warnings = []
        
        # Check document count
        if document_count == 0:
            warnings.append("Collection is empty")
            status = HealthStatus.WARNING
        elif document_count < 10:
            warnings.append("Collection has very few documents")
        
        # Sample documents for analysis
        sample_size = min(100, document_count)
        sample_data = collection.get(
            limit=sample_size,
            include=['metadatas', 'documents', 'embeddings']
        ) if document_count > 0 else {'metadatas': [], 'documents': [], 'embeddings': []}
        
        # Analyze metadata completeness
        metadata_completeness = self._calculate_metadata_completeness(sample_data.get('metadatas', []))
        if metadata_completeness < 0.8:
            warnings.append(f"Low metadata completeness: {metadata_completeness:.1%}")
        
        # Analyze embedding quality
        embedding_quality = self._analyze_embedding_quality(sample_data.get('embeddings', []))
        if embedding_quality < 0.7:
            issues.append(f"Low embedding quality: {embedding_quality:.2f}")
            status = HealthStatus.CRITICAL
        
        # Check for duplicates
        duplicate_rate = self._estimate_duplicate_rate(sample_data.get('documents', []))
        if duplicate_rate > 0.1:
            warnings.append(f"High duplicate rate: {duplicate_rate:.1%}")
        
        # Calculate storage size (estimate)
        storage_size_mb = self._estimate_storage_size(sample_data, document_count)
        
        # Get query performance metrics
        avg_query_time = self._get_average_query_time(instance_name)
        if avg_query_time > self.monitoring_config['slow_query_threshold_ms']:
            warnings.append(f"Slow query performance: {avg_query_time:.1f}ms")
        
        # Determine overall status
        if issues:
            status = HealthStatus.CRITICAL
        elif warnings:
            status = HealthStatus.WARNING
        
        return CollectionHealth(
            instance_name=instance_name,
            collection_name=collection_name,
            status=status,
            document_count=document_count,
            last_updated=datetime.now(),
            average_query_time_ms=avg_query_time,
            embedding_quality_score=embedding_quality,
            storage_size_mb=storage_size_mb,
            issues=issues,
            warnings=warnings,
            metadata_completeness=metadata_completeness,
            duplicate_rate=duplicate_rate,
            error_rate=0.0  # Would need to track actual errors
        )
    
    def _calculate_metadata_completeness(self, metadatas: List[Dict[str, Any]]) -> float:
        """Calculate metadata completeness score."""
        
        if not metadatas:
            return 0.0
        
        required_fields = [
            'instance_name', 'document_id', 'title', 'authors', 
            'published_date', 'section', 'text_quality_score'
        ]
        
        total_score = 0.0
        
        for metadata in metadatas:
            if not metadata:
                continue
            
            field_score = 0.0
            for field in required_fields:
                if field in metadata and metadata[field]:
                    field_score += 1.0
            
            total_score += field_score / len(required_fields)
        
        return total_score / len(metadatas)
    
    def _analyze_embedding_quality(self, embeddings: List[List[float]]) -> float:
        """Analyze quality of embeddings."""
        
        if not embeddings:
            return 0.0
        
        try:
            embedding_array = np.array(embeddings)
            
            # Check for zero embeddings
            zero_embeddings = np.sum(np.all(embedding_array == 0, axis=1))
            zero_rate = zero_embeddings / len(embeddings)
            
            # Check for NaN or infinite values
            invalid_embeddings = np.sum(np.any(np.isnan(embedding_array) | np.isinf(embedding_array), axis=1))
            invalid_rate = invalid_embeddings / len(embeddings)
            
            # Check magnitude distribution
            magnitudes = np.linalg.norm(embedding_array, axis=1)
            mean_magnitude = np.mean(magnitudes)
            std_magnitude = np.std(magnitudes)
            
            # Quality score based on multiple factors
            quality_score = 1.0
            
            # Penalize zero embeddings
            quality_score -= zero_rate * 0.5
            
            # Penalize invalid embeddings
            quality_score -= invalid_rate * 0.8
            
            # Penalize unusual magnitude distribution
            if mean_magnitude < 0.1 or mean_magnitude > 10.0:
                quality_score -= 0.2
            
            if std_magnitude > mean_magnitude:  # High variance
                quality_score -= 0.1
            
            return max(0.0, quality_score)
            
        except Exception as e:
            logger.error(f"Error analyzing embedding quality: {e}")
            return 0.0
    
    def _estimate_duplicate_rate(self, documents: List[str]) -> float:
        """Estimate duplicate rate in documents."""
        
        if len(documents) < 2:
            return 0.0
        
        # Simple duplicate detection based on exact matches
        unique_docs = set(documents)
        duplicate_rate = 1.0 - (len(unique_docs) / len(documents))
        
        return duplicate_rate
    
    def _estimate_storage_size(
        self, 
        sample_data: Dict[str, Any], 
        total_documents: int
    ) -> float:
        """Estimate storage size in MB."""
        
        if not sample_data or total_documents == 0:
            return 0.0
        
        # Estimate based on sample
        documents = sample_data.get('documents', [])
        metadatas = sample_data.get('metadatas', [])
        embeddings = sample_data.get('embeddings', [])
        
        if not documents:
            return 0.0
        
        # Calculate average sizes
        avg_doc_size = sum(len(doc.encode('utf-8')) for doc in documents) / len(documents)
        avg_metadata_size = sum(len(json.dumps(meta).encode('utf-8')) for meta in metadatas if meta) / max(1, len(metadatas))
        avg_embedding_size = len(embeddings[0]) * 4 if embeddings else 0  # 4 bytes per float
        
        # Estimate total size
        total_size_bytes = (avg_doc_size + avg_metadata_size + avg_embedding_size) * total_documents
        total_size_mb = total_size_bytes / (1024 * 1024)
        
        return total_size_mb
    
    def _get_average_query_time(self, instance_name: str) -> float:
        """Get average query time for an instance."""
        
        query_times = self.query_times.get(instance_name, [])
        if not query_times:
            return 0.0
        
        return sum(query_times) / len(query_times)
    
    async def _process_health_alerts(self, health: CollectionHealth) -> None:
        """Process health check results and generate alerts."""
        
        # Generate alerts for critical issues
        if health.status == HealthStatus.CRITICAL:
            for issue in health.issues:
                alert = MonitoringAlert(
                    alert_id=f"health_{health.instance_name}_{datetime.now().timestamp()}",
                    instance_name=health.instance_name,
                    alert_type="health_critical",
                    severity="critical",
                    title=f"Critical Health Issue in {health.instance_name}",
                    message=issue,
                    created_at=datetime.now()
                )
                self.alerts.append(alert)
        
        # Generate alerts for warnings
        elif health.status == HealthStatus.WARNING:
            for warning in health.warnings:
                alert = MonitoringAlert(
                    alert_id=f"health_{health.instance_name}_{datetime.now().timestamp()}",
                    instance_name=health.instance_name,
                    alert_type="health_warning",
                    severity="warning",
                    title=f"Health Warning in {health.instance_name}",
                    message=warning,
                    created_at=datetime.now()
                )
                self.alerts.append(alert)
    
    async def capture_performance_snapshot(self) -> Dict[str, PerformanceSnapshot]:
        """Capture performance snapshot for all instances."""
        
        snapshots = {}
        
        for instance_name in self.vector_store_service.initialized_instances:
            try:
                snapshot = await self._capture_instance_performance(instance_name)
                snapshots[instance_name] = snapshot
                
                # Store in history
                self.monitoring_history.append(snapshot)
                
                # Maintain history size
                if len(self.monitoring_history) > self.max_history_size:
                    self.monitoring_history = self.monitoring_history[-self.max_history_size:]
                
            except Exception as e:
                logger.error(f"Failed to capture performance snapshot for {instance_name}: {e}")
        
        return snapshots
    
    async def _capture_instance_performance(self, instance_name: str) -> PerformanceSnapshot:
        """Capture performance snapshot for a specific instance."""
        
        # Get query performance metrics
        query_times = self.query_times.get(instance_name, [])
        query_count = self.query_counts.get(instance_name, 0)
        avg_query_time = sum(query_times) / len(query_times) if query_times else 0.0
        slow_queries = len([t for t in query_times if t > self.monitoring_config['slow_query_threshold_ms']])
        
        # Get system metrics (simplified - would use actual system monitoring)
        memory_usage = self._get_memory_usage()
        cpu_usage = self._get_cpu_usage()
        disk_io_rate = self._get_disk_io_rate()
        
        # Get embedding service metrics
        embedding_service = getattr(self.vector_store_service, 'embedding_service', None)
        embedding_rate = 0.0
        cache_hit_rate = 0.0
        
        if embedding_service:
            cache_stats = embedding_service.get_cache_stats()
            cache_hit_rate = cache_stats.get('cache_hit_ratio', 0.0)
        
        return PerformanceSnapshot(
            timestamp=datetime.now(),
            instance_name=instance_name,
            query_count=query_count,
            average_query_time_ms=avg_query_time,
            slow_query_count=slow_queries,
            embedding_generation_rate=embedding_rate,
            embedding_cache_hit_rate=cache_hit_rate,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            disk_io_rate_mbps=disk_io_rate,
            average_relevance_score=0.0,  # Would need to track from actual queries
            result_quality_score=0.0
        )
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return int(process.memory_info().rss / 1024 / 1024)
        except:
            return 0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except:
            return 0.0
    
    def _get_disk_io_rate(self) -> float:
        """Get current disk I/O rate in MB/s."""
        try:
            import psutil
            disk_io = psutil.disk_io_counters()
            # This is a simplified calculation
            return (disk_io.read_bytes + disk_io.write_bytes) / 1024 / 1024
        except:
            return 0.0
    
    def record_query_time(self, instance_name: str, query_time_ms: float) -> None:
        """Record query time for performance monitoring."""
        
        if instance_name not in self.query_times:
            self.query_times[instance_name] = []
            self.query_counts[instance_name] = 0
        
        self.query_times[instance_name].append(query_time_ms)
        self.query_counts[instance_name] += 1
        
        # Keep only recent query times (last 100)
        if len(self.query_times[instance_name]) > 100:
            self.query_times[instance_name] = self.query_times[instance_name][-100:]
    
    def get_performance_history(
        self, 
        instance_name: Optional[str] = None,
        hours: int = 24
    ) -> List[PerformanceSnapshot]:
        """Get performance history for analysis."""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        history = [
            snapshot for snapshot in self.monitoring_history
            if snapshot.timestamp >= cutoff_time
        ]
        
        if instance_name:
            history = [s for s in history if s.instance_name == instance_name]
        
        return history
    
    def get_active_alerts(
        self, 
        instance_name: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[MonitoringAlert]:
        """Get active alerts with optional filtering."""
        
        active_alerts = [alert for alert in self.alerts if alert.status == "active"]
        
        if instance_name:
            active_alerts = [a for a in active_alerts if a.instance_name == instance_name]
        
        if severity:
            active_alerts = [a for a in active_alerts if a.severity == severity]
        
        return active_alerts
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert by ID."""
        
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolve()
                return True
        
        return False
    
    async def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report."""
        
        # Perform fresh health check
        health_results = await self.perform_health_check()
        
        # Get recent performance data
        recent_snapshots = self.get_performance_history(hours=24)
        
        # Get active alerts
        active_alerts = self.get_active_alerts()
        
        # Calculate summary statistics
        total_documents = sum(health.document_count for health in health_results.values())
        avg_query_time = np.mean([s.average_query_time_ms for s in recent_snapshots]) if recent_snapshots else 0.0
        avg_embedding_quality = np.mean([health.embedding_quality_score for health in health_results.values()])
        
        # Instance status summary
        status_counts = {}
        for health in health_results.values():
            status = health.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'report_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_instances': len(health_results),
                'total_documents': total_documents,
                'average_query_time_ms': avg_query_time,
                'average_embedding_quality': avg_embedding_quality,
                'active_alerts': len(active_alerts),
                'status_distribution': status_counts
            },
            'instance_health': {name: health.to_dict() for name, health in health_results.items()},
            'recent_performance': [snapshot.to_dict() for snapshot in recent_snapshots[-10:]],
            'active_alerts': [alert.to_dict() for alert in active_alerts],
            'monitoring_config': self.monitoring_config
        }
    
    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """Get monitoring service statistics."""
        
        return {
            'monitoring_active': self.last_health_check is not None,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'performance_snapshots_count': len(self.monitoring_history),
            'total_alerts_generated': len(self.alerts),
            'active_alerts_count': len(self.get_active_alerts()),
            'monitored_instances': list(self.vector_store_service.initialized_instances),
            'query_performance': {
                instance: {
                    'total_queries': self.query_counts.get(instance, 0),
                    'average_time_ms': self._get_average_query_time(instance)
                }
                for instance in self.vector_store_service.initialized_instances
            }
        }