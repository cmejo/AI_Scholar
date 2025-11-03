"""
Multi-instance vector store services for the ArXiv system.

This module provides vector store services that support multiple scholar instances
with complete separation, instance-specific configurations, monitoring, optimization,
and backup/recovery capabilities.
"""

from .multi_instance_vector_store_service import MultiInstanceVectorStoreService
from .collection_manager import CollectionManager
from .embedding_service import EmbeddingService
from .document_processor import DocumentProcessorFactory, AIScholarDocumentProcessor, QuantScholarDocumentProcessor
from .unified_search_interface import UnifiedSearchInterface, SearchScope, SearchFilter, SortOrder
from .monitoring_service import VectorStoreMonitoringService, HealthStatus, CollectionHealth
from .optimization_service import VectorStoreOptimizationService, OptimizationType, OptimizationRecommendation
from .backup_recovery_service import BackupRecoveryService, BackupType, BackupStatus

__all__ = [
    # Core services
    'MultiInstanceVectorStoreService',
    'CollectionManager', 
    'EmbeddingService',
    
    # Document processing
    'DocumentProcessorFactory',
    'AIScholarDocumentProcessor',
    'QuantScholarDocumentProcessor',
    
    # Search interface
    'UnifiedSearchInterface',
    'SearchScope',
    'SearchFilter',
    'SortOrder',
    
    # Monitoring
    'VectorStoreMonitoringService',
    'HealthStatus',
    'CollectionHealth',
    
    # Optimization
    'VectorStoreOptimizationService',
    'OptimizationType',
    'OptimizationRecommendation',
    
    # Backup and recovery
    'BackupRecoveryService',
    'BackupType',
    'BackupStatus'
]