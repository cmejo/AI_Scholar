"""
Processors package for multi-instance ArXiv system.

Contains specialized processing pipelines for different scholar instances.
"""

from .ai_scholar_processor import AIScholarProcessor, MultiInstanceVectorStoreService, ScientificChunker

__all__ = [
    'AIScholarProcessor',
    'MultiInstanceVectorStoreService', 
    'ScientificChunker'
]