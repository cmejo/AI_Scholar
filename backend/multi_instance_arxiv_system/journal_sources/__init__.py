"""
Journal source handlers for multi-instance ArXiv system.

Contains specialized handlers for different journal sources including:
- Journal of Statistical Software (JSS)
- R Journal
- Base classes for extensible journal source handling
"""

from .base_journal_handler import BaseJournalHandler, JournalMetadata
from .jss_handler import JStatSoftwareHandler
from .rjournal_handler import RJournalHandler

__all__ = [
    'BaseJournalHandler',
    'JournalMetadata',
    'JStatSoftwareHandler',
    'RJournalHandler'
]