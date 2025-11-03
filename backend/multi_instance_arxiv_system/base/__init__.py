"""
Base classes for multi-instance ArXiv system.

This module provides abstract base classes and framework components for
implementing scholar instances with different data sources and processing
capabilities.
"""

from .base_scholar_downloader import BaseScholarDownloader
from .base_journal_handler import BaseJournalHandler

__all__ = [
    'BaseScholarDownloader',
    'BaseJournalHandler'
]