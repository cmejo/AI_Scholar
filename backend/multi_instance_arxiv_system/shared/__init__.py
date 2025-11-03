"""
Shared components for multi-instance ArXiv system.

This module provides extended shared components that support instance separation
and multi-instance operations while maintaining compatibility with the existing
ArXiv RAG Enhancement system.
"""

from .instance_manager import InstanceManager
from .multi_instance_state_manager import MultiInstanceStateManager
from .multi_instance_progress_tracker import MultiInstanceProgressTracker
from .multi_instance_error_handler import MultiInstanceErrorHandler
from .multi_instance_data_models import *

__all__ = [
    'InstanceManager',
    'MultiInstanceStateManager',
    'MultiInstanceProgressTracker', 
    'MultiInstanceErrorHandler',
    # Data models
    'BasePaper',
    'ArxivPaper',
    'JournalPaper',
    'InstanceConfig',
    'StoragePaths',
    'ProcessingConfig',
    'NotificationConfig',
    'VectorStoreConfig',
    'UpdateReport',
    'StorageStats',
    'PerformanceMetrics',
    'InstanceStats'
]