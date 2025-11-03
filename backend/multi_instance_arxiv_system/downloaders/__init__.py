"""
Downloaders package for multi-instance ArXiv system.

Contains specialized downloader implementations for different scholar instances.
"""

from .ai_scholar_downloader import AIScholarDownloader

__all__ = [
    'AIScholarDownloader'
]