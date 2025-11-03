"""
Vector Store Optimization Service for Multi-Instance System.

This module provides optimization capabilities for vector store collections
including performance optimization, storage optimization, and quality improvements.
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
    from multi_instance_arxiv_system.vector_store.monitoring_service import VectorStoreMonitoringService
    from multi_instance_arxiv_system.shared.multi_instance_data_models import CleanupRecommendation
except ImportError as e:
    print(f"Import error: {e}")
    raise

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """Types of optimization operations."""
    PERFORMANCE = "performance"
    STORAGE = "storage"
    QUALITY = "quality"
    INDEX = "index"
    CLEANUP = "cleanup"


@dataclass
class OptimizationResult:
    """Result of an optimization operation."""
    
    optimization_type: OptimizationType
    instance_name: str
    success: bool
    start_time: datetime
    end_time: datetime
    
    # Metrics before optimization
    before_metrics: Dict[str, Any]
    
    # Metrics after optimization
    after_metrics: Dict[str, Any]
    
    # Changes made
    changes_made: List[str]
    
    # Performance impact
    performance_improvement: Dict[str, float]
    
    # Any issues encountered
    issues: List[str]
    warnings: List[str]
    
    @property
    def duration_seconds(self) -> float:
        """Duration of optimization in seconds."""
        return (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['optimization_type'] = self.optimization_type.value
        data['start_time'] = self.start_time.isoformat()
        data['end_time'] = self.end_time.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OptimizationResult':
        """Create from dictionary (JSON deserialization)."""
        data['optimization_type'] = OptimizationType(data['optimization_type'])
        data['start_time'] = datetime.fromisoformat(data['start_time'])
        data['end_time'] = datetime.fromisoformat(data['end_time'])
        return cls(**data)


@dataclass
class OptimizationRecommendation:
    """Recommendation for optimization."""
    
    recommendation_id: str
    instance_name: str
    optimization_type: OptimizationType
    priority: str  # 'low', 'medium', 'high', 'critical'
    
    title: str
    description: str
    expected_benefit: str
    estimated_time_minutes: int
    
    # Risk assessment
    risk_level: str  # 'low', 'medium', 'high'
    potential_issues: List[str]
    
    # Implementation details
    implementation_steps: List[str]
    requires_downtime: bool
    
    created_at: datetime = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['optimization_type'] = self.optimization_type.value
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OptimizationRecommendation':
        """Create from dictionary (JSON deserialization)."""
        data['optimization_type'] = OptimizationType(data['optimization_type'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


class VectorStoreOptimizationService:
    """
    Optimization service for multi-instance vector store.
    Provides performance optimization, storage optimization, and quality improvements.
    """
    
    def __init__(
        self, 
        vector_store_service: MultiInstanceVectorStoreService,
        monitoring_service: Optional[VectorStoreMonitoringService] = None
    ):
        self.vector_store_service = vector_store_service
        self.monitoring_service = monitoring_service
        self.optimization_history: List[OptimizationResult] = []
        self.recommendations: List[OptimizationRecommendation] = []
        
        # Optimization configuration
        self.optimization_config = {
            'auto_optimization_enabled': False,
            'optimization_schedule_hours': [2, 14],  # Run at 2 AM and 2 PM
            'performance_threshold_ms': 1000,
            'storage_efficiency_threshold': 0.8,
            'quality_threshold': 0.7,
            'max_optimization_time_minutes': 60,
            'backup_before_optimization': True
        }
    
    async def analyze_optimization_opportunities(
        self, 
        instance_name: Optional[str] = None
    ) -> List[OptimizationRecommendation]:
        """Analyze and generate optimization recommendations."""
        
        logger.info(f"Analyzing optimization opportunities for {instance_name or 'all instances'}")
        
        recommendations = []
        instances_to_analyze = [instance_name] if instance_name else list(self.vector_store_service.initialized_instances)
        
        for inst_name in instances_to_analyze:
            try:
                # Get current metrics
                instance_stats = await self.vector_store_service.get_instance_stats(inst_name)
                
                # Analyze performance optimization opportunities
                perf_recommendations = await self._analyze_performance_optimization(inst_name, instance_stats)
                recommendations.extend(perf_recommendations)
                
                # Analyze storage optimization opportunities
                storage_recommendations = await self._analyze_storage_optimization(inst_name, instance_stats)
                recommendations.extend(storage_recommendations)
                
                # Analyze quality optimization opportunities
                quality_recommendations = await self._analyze_quality_optimization(inst_name, instance_stats)
                recommendations.extend(quality_recommendations)
                
                # Analyze cleanup opportunities
                cleanup_recommendations = await self._analyze_cleanup_opportunities(inst_name, instance_stats)
                recommendations.extend(cleanup_recommendations)
                
            except Exception as e:
                logger.error(f"Error analyzing optimization opportunities for {inst_name}: {e}")
        
        # Sort recommendations by priority
        recommendations.sort(key=lambda r: {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}[r.priority], reverse=True)
        
        # Store recommendations
        self.recommendations.extend(recommendations)
        
        logger.info(f"Generated {len(recommendations)} optimization recommendations")
        return recommendations
    
    async def _analyze_performance_optimization(
        self, 
        instance_name: str, 
        stats: Dict[str, Any]
    ) -> List[OptimizationRecommendation]:
        """Analyze performance optimization opportunities."""
        
        recommendations = []
        
        # Check query performance
        if self.monitoring_service:
            avg_query_time = self.monitoring_service._get_average_query_time(instance_name)
            
            if avg_query_time > self.optimization_config['performance_threshold_ms']:
                recommendations.append(OptimizationRecommendation(
                    recommendation_id=f"perf_{instance_name}_{datetime.now().timestamp()}",
                    instance_name=instance_name,
                    optimization_type=OptimizationType.PERFORMANCE,
                    priority="high",
                    title="Optimize Query Performance",
                    description=f"Average query time ({avg_query_time:.1f}ms) exceeds threshold",
                    expected_benefit="Reduce query time by 20-40%",
                    estimated_time_minutes=15,
                    risk_level="low",
                    potential_issues=["Temporary performance impact during optimization"],
                    implementation_steps=[
                        "Analyze slow queries",
                        "Optimize embedding index",
                        "Adjust batch sizes",
                        "Clear embedding cache if needed"
                    ],
                    requires_downtime=False
                ))
        
        # Check embedding cache efficiency
        if hasattr(self.vector_store_service, 'embedding_service'):
            cache_stats = self.vector_store_service.embedding_service.get_cache_stats()
            hit_rate = cache_stats.get('cache_hit_ratio', 0.0)
            
            if hit_rate < 0.5:
                recommendations.append(OptimizationRecommendation(
                    recommendation_id=f"cache_{instance_name}_{datetime.now().timestamp()}",
                    instance_name=instance_name,
                    optimization_type=OptimizationType.PERFORMANCE,
                    priority="medium",
                    title="Optimize Embedding Cache",
                    description=f"Low cache hit rate ({hit_rate:.1%}) indicates inefficient caching",
                    expected_benefit="Improve embedding generation speed by 30-50%",
                    estimated_time_minutes=10,
                    risk_level="low",
                    potential_issues=["Temporary memory usage increase"],
                    implementation_steps=[
                        "Analyze cache usage patterns",
                        "Adjust cache size",
                        "Optimize cache eviction policy"
                    ],
                    requires_downtime=False
                ))
        
        return recommendations
    
    async def _analyze_storage_optimization(
        self, 
        instance_name: str, 
        stats: Dict[str, Any]
    ) -> List[OptimizationRecommendation]:
        """Analyze storage optimization opportunities."""
        
        recommendations = []
        
        # Check for duplicate documents
        total_chunks = stats.get('total_chunks', 0)
        if total_chunks > 1000:  # Only for larger collections
            
            recommendations.append(OptimizationRecommendation(
                recommendation_id=f"storage_{instance_name}_{datetime.now().timestamp()}",
                instance_name=instance_name,
                optimization_type=OptimizationType.STORAGE,
                priority="medium",
                title="Optimize Storage Efficiency",
                description="Analyze and remove duplicate or low-quality chunks",
                expected_benefit="Reduce storage usage by 10-20%",
                estimated_time_minutes=30,
                risk_level="medium",
                potential_issues=["Potential data loss if not careful", "Temporary performance impact"],
                implementation_steps=[
                    "Identify duplicate chunks",
                    "Analyze chunk quality scores",
                    "Remove low-quality duplicates",
                    "Compact collection"
                ],
                requires_downtime=True
            ))
        
        return recommendations
    
    async def _analyze_quality_optimization(
        self, 
        instance_name: str, 
        stats: Dict[str, Any]
    ) -> List[OptimizationRecommendation]:
        """Analyze quality optimization opportunities."""
        
        recommendations = []
        
        # Check embedding quality if monitoring is available
        if self.monitoring_service:
            try:
                health_results = await self.monitoring_service.perform_health_check()
                instance_health = health_results.get(instance_name)
                
                if instance_health and instance_health.embedding_quality_score < self.optimization_config['quality_threshold']:
                    recommendations.append(OptimizationRecommendation(
                        recommendation_id=f"quality_{instance_name}_{datetime.now().timestamp()}",
                        instance_name=instance_name,
                        optimization_type=OptimizationType.QUALITY,
                        priority="high",
                        title="Improve Embedding Quality",
                        description=f"Low embedding quality score ({instance_health.embedding_quality_score:.2f})",
                        expected_benefit="Improve search relevance and accuracy",
                        estimated_time_minutes=45,
                        risk_level="medium",
                        potential_issues=["Requires regenerating embeddings", "Significant processing time"],
                        implementation_steps=[
                            "Identify low-quality embeddings",
                            "Regenerate embeddings for affected documents",
                            "Validate embedding quality",
                            "Update collection"
                        ],
                        requires_downtime=True
                    ))
            except Exception as e:
                logger.error(f"Error checking quality for {instance_name}: {e}")
        
        return recommendations
    
    async def _analyze_cleanup_opportunities(
        self, 
        instance_name: str, 
        stats: Dict[str, Any]
    ) -> List[OptimizationRecommendation]:
        """Analyze cleanup opportunities."""
        
        recommendations = []
        
        # Check for old or stale data
        total_chunks = stats.get('total_chunks', 0)
        if total_chunks > 500:
            
            recommendations.append(OptimizationRecommendation(
                recommendation_id=f"cleanup_{instance_name}_{datetime.now().timestamp()}",
                instance_name=instance_name,
                optimization_type=OptimizationType.CLEANUP,
                priority="low",
                title="Clean Up Stale Data",
                description="Remove old, unused, or corrupted data",
                expected_benefit="Improve performance and reduce storage usage",
                estimated_time_minutes=20,
                risk_level="low",
                potential_issues=["Potential removal of useful data"],
                implementation_steps=[
                    "Identify stale or corrupted chunks",
                    "Backup data before cleanup",
                    "Remove identified chunks",
                    "Validate collection integrity"
                ],
                requires_downtime=False
            ))
        
        return recommendations
    
    async def optimize_instance_performance(self, instance_name: str) -> OptimizationResult:
        """Optimize performance for a specific instance."""
        
        logger.info(f"Starting performance optimization for {instance_name}")
        
        start_time = datetime.now()
        changes_made = []
        issues = []
        warnings = []
        
        # Get before metrics
        before_metrics = await self._collect_performance_metrics(instance_name)
        
        try:
            # Optimization steps
            
            # 1. Optimize embedding cache
            if hasattr(self.vector_store_service, 'embedding_service'):
                cache_cleared = self.vector_store_service.embedding_service.clear_cache()
                if cache_cleared > 0:
                    changes_made.append(f"Cleared {cache_cleared} cached embeddings")
            
            # 2. Analyze and optimize query patterns
            if self.monitoring_service:
                # Reset query time tracking to get fresh metrics
                self.monitoring_service.query_times[instance_name] = []
                changes_made.append("Reset query performance tracking")
            
            # 3. Validate collection health
            service = self.vector_store_service.instance_services.get(instance_name)
            if service and service.collection:
                try:
                    # Test a simple query to warm up the collection
                    test_results = service.collection.query(
                        query_texts=["test query"],
                        n_results=1
                    )
                    changes_made.append("Warmed up collection with test query")
                except Exception as e:
                    issues.append(f"Collection warm-up failed: {str(e)}")
            
            success = len(issues) == 0
            
        except Exception as e:
            logger.error(f"Error during performance optimization: {e}")
            issues.append(f"Optimization failed: {str(e)}")
            success = False
        
        end_time = datetime.now()
        
        # Get after metrics
        after_metrics = await self._collect_performance_metrics(instance_name)
        
        # Calculate performance improvement
        performance_improvement = self._calculate_performance_improvement(before_metrics, after_metrics)
        
        result = OptimizationResult(
            optimization_type=OptimizationType.PERFORMANCE,
            instance_name=instance_name,
            success=success,
            start_time=start_time,
            end_time=end_time,
            before_metrics=before_metrics,
            after_metrics=after_metrics,
            changes_made=changes_made,
            performance_improvement=performance_improvement,
            issues=issues,
            warnings=warnings
        )
        
        self.optimization_history.append(result)
        
        logger.info(f"Performance optimization completed for {instance_name}: {'success' if success else 'failed'}")
        return result
    
    async def optimize_instance_storage(self, instance_name: str) -> OptimizationResult:
        """Optimize storage for a specific instance."""
        
        logger.info(f"Starting storage optimization for {instance_name}")
        
        start_time = datetime.now()
        changes_made = []
        issues = []
        warnings = []
        
        # Get before metrics
        before_metrics = await self._collect_storage_metrics(instance_name)
        
        try:
            service = self.vector_store_service.instance_services.get(instance_name)
            if not service or not service.collection:
                raise ValueError(f"Instance {instance_name} not properly initialized")
            
            collection = service.collection
            
            # 1. Analyze for duplicates
            sample_data = collection.get(
                limit=1000,
                include=['documents', 'metadatas', 'ids']
            )
            
            documents = sample_data.get('documents', [])
            ids = sample_data.get('ids', [])
            
            # Find potential duplicates (simplified approach)
            seen_docs = set()
            duplicate_ids = []
            
            for doc, doc_id in zip(documents, ids):
                doc_hash = hash(doc[:100])  # Hash first 100 characters
                if doc_hash in seen_docs:
                    duplicate_ids.append(doc_id)
                else:
                    seen_docs.add(doc_hash)
            
            # Remove duplicates if found
            if duplicate_ids:
                # In a real implementation, we'd be more careful about this
                warnings.append(f"Found {len(duplicate_ids)} potential duplicates (not removed in this demo)")
                changes_made.append(f"Identified {len(duplicate_ids)} potential duplicate documents")
            
            # 2. Analyze chunk quality and remove low-quality chunks
            metadatas = sample_data.get('metadatas', [])
            low_quality_ids = []
            
            for metadata, doc_id in zip(metadatas, ids):
                if metadata and metadata.get('text_quality_score', 1.0) < 0.3:
                    low_quality_ids.append(doc_id)
            
            if low_quality_ids:
                warnings.append(f"Found {len(low_quality_ids)} low-quality chunks (not removed in this demo)")
                changes_made.append(f"Identified {len(low_quality_ids)} low-quality chunks")
            
            success = True
            
        except Exception as e:
            logger.error(f"Error during storage optimization: {e}")
            issues.append(f"Storage optimization failed: {str(e)}")
            success = False
        
        end_time = datetime.now()
        
        # Get after metrics
        after_metrics = await self._collect_storage_metrics(instance_name)
        
        # Calculate performance improvement
        performance_improvement = self._calculate_storage_improvement(before_metrics, after_metrics)
        
        result = OptimizationResult(
            optimization_type=OptimizationType.STORAGE,
            instance_name=instance_name,
            success=success,
            start_time=start_time,
            end_time=end_time,
            before_metrics=before_metrics,
            after_metrics=after_metrics,
            changes_made=changes_made,
            performance_improvement=performance_improvement,
            issues=issues,
            warnings=warnings
        )
        
        self.optimization_history.append(result)
        
        logger.info(f"Storage optimization completed for {instance_name}: {'success' if success else 'failed'}")
        return result
    
    async def _collect_performance_metrics(self, instance_name: str) -> Dict[str, Any]:
        """Collect performance metrics for an instance."""
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'instance_name': instance_name
        }
        
        # Get query performance metrics
        if self.monitoring_service:
            avg_query_time = self.monitoring_service._get_average_query_time(instance_name)
            query_count = self.monitoring_service.query_counts.get(instance_name, 0)
            
            metrics.update({
                'average_query_time_ms': avg_query_time,
                'total_queries': query_count
            })
        
        # Get embedding cache metrics
        if hasattr(self.vector_store_service, 'embedding_service'):
            cache_stats = self.vector_store_service.embedding_service.get_cache_stats()
            metrics.update({
                'cache_size': cache_stats.get('cache_size', 0),
                'cache_hit_ratio': cache_stats.get('cache_hit_ratio', 0.0)
            })
        
        # Get collection metrics
        try:
            instance_stats = await self.vector_store_service.get_instance_stats(instance_name)
            metrics.update({
                'total_chunks': instance_stats.get('total_chunks', 0),
                'collection_name': instance_stats.get('collection_name', '')
            })
        except Exception as e:
            logger.error(f"Error collecting instance stats: {e}")
        
        return metrics
    
    async def _collect_storage_metrics(self, instance_name: str) -> Dict[str, Any]:
        """Collect storage metrics for an instance."""
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'instance_name': instance_name
        }
        
        try:
            service = self.vector_store_service.instance_services.get(instance_name)
            if service and service.collection:
                collection = service.collection
                document_count = collection.count()
                
                # Get sample for analysis
                sample_data = collection.get(
                    limit=min(100, document_count),
                    include=['documents', 'metadatas']
                )
                
                documents = sample_data.get('documents', [])
                metadatas = sample_data.get('metadatas', [])
                
                # Calculate storage estimates
                total_text_size = sum(len(doc.encode('utf-8')) for doc in documents)
                avg_doc_size = total_text_size / len(documents) if documents else 0
                estimated_total_size_mb = (avg_doc_size * document_count) / (1024 * 1024)
                
                # Calculate quality metrics
                quality_scores = [m.get('text_quality_score', 0.0) for m in metadatas if m]
                avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
                
                metrics.update({
                    'document_count': document_count,
                    'estimated_size_mb': estimated_total_size_mb,
                    'average_document_size_bytes': avg_doc_size,
                    'average_quality_score': avg_quality,
                    'sample_size': len(documents)
                })
        
        except Exception as e:
            logger.error(f"Error collecting storage metrics: {e}")
            metrics['error'] = str(e)
        
        return metrics
    
    def _calculate_performance_improvement(
        self, 
        before_metrics: Dict[str, Any], 
        after_metrics: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate performance improvement between before and after metrics."""
        
        improvements = {}
        
        # Query time improvement
        before_query_time = before_metrics.get('average_query_time_ms', 0)
        after_query_time = after_metrics.get('average_query_time_ms', 0)
        
        if before_query_time > 0:
            query_time_improvement = ((before_query_time - after_query_time) / before_query_time) * 100
            improvements['query_time_improvement_percent'] = query_time_improvement
        
        # Cache hit rate improvement
        before_cache_hit = before_metrics.get('cache_hit_ratio', 0)
        after_cache_hit = after_metrics.get('cache_hit_ratio', 0)
        
        cache_improvement = after_cache_hit - before_cache_hit
        improvements['cache_hit_rate_improvement'] = cache_improvement
        
        return improvements
    
    def _calculate_storage_improvement(
        self, 
        before_metrics: Dict[str, Any], 
        after_metrics: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate storage improvement between before and after metrics."""
        
        improvements = {}
        
        # Storage size improvement
        before_size = before_metrics.get('estimated_size_mb', 0)
        after_size = after_metrics.get('estimated_size_mb', 0)
        
        if before_size > 0:
            size_improvement = ((before_size - after_size) / before_size) * 100
            improvements['storage_size_reduction_percent'] = size_improvement
        
        # Quality improvement
        before_quality = before_metrics.get('average_quality_score', 0)
        after_quality = after_metrics.get('average_quality_score', 0)
        
        quality_improvement = after_quality - before_quality
        improvements['quality_score_improvement'] = quality_improvement
        
        return improvements
    
    async def run_automated_optimization(self) -> Dict[str, List[OptimizationResult]]:
        """Run automated optimization for all instances."""
        
        logger.info("Starting automated optimization for all instances")
        
        results = {}
        
        for instance_name in self.vector_store_service.initialized_instances:
            try:
                instance_results = []
                
                # Generate recommendations
                recommendations = await self.analyze_optimization_opportunities(instance_name)
                
                # Execute high-priority, low-risk optimizations
                for recommendation in recommendations:
                    if (recommendation.priority in ['high', 'critical'] and 
                        recommendation.risk_level == 'low' and 
                        not recommendation.requires_downtime):
                        
                        if recommendation.optimization_type == OptimizationType.PERFORMANCE:
                            result = await self.optimize_instance_performance(instance_name)
                            instance_results.append(result)
                        
                        # Add other optimization types as needed
                
                results[instance_name] = instance_results
                
            except Exception as e:
                logger.error(f"Automated optimization failed for {instance_name}: {e}")
        
        return results
    
    def get_optimization_history(
        self, 
        instance_name: Optional[str] = None,
        optimization_type: Optional[OptimizationType] = None,
        days: int = 30
    ) -> List[OptimizationResult]:
        """Get optimization history with optional filtering."""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        history = [
            result for result in self.optimization_history
            if result.start_time >= cutoff_date
        ]
        
        if instance_name:
            history = [r for r in history if r.instance_name == instance_name]
        
        if optimization_type:
            history = [r for r in history if r.optimization_type == optimization_type]
        
        return history
    
    def get_optimization_recommendations(
        self, 
        instance_name: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[OptimizationRecommendation]:
        """Get optimization recommendations with optional filtering."""
        
        recommendations = self.recommendations.copy()
        
        if instance_name:
            recommendations = [r for r in recommendations if r.instance_name == instance_name]
        
        if priority:
            recommendations = [r for r in recommendations if r.priority == priority]
        
        return recommendations
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """Get optimization service statistics."""
        
        total_optimizations = len(self.optimization_history)
        successful_optimizations = len([r for r in self.optimization_history if r.success])
        
        # Calculate average improvements
        performance_improvements = [
            r.performance_improvement.get('query_time_improvement_percent', 0)
            for r in self.optimization_history
            if r.optimization_type == OptimizationType.PERFORMANCE and r.success
        ]
        
        avg_performance_improvement = np.mean(performance_improvements) if performance_improvements else 0.0
        
        return {
            'total_optimizations': total_optimizations,
            'successful_optimizations': successful_optimizations,
            'success_rate': successful_optimizations / max(1, total_optimizations),
            'average_performance_improvement_percent': avg_performance_improvement,
            'active_recommendations': len(self.recommendations),
            'optimization_types_used': list(set(r.optimization_type.value for r in self.optimization_history)),
            'instances_optimized': list(set(r.instance_name for r in self.optimization_history))
        }