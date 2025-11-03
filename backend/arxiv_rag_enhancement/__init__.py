"""
arXiv RAG Enhancement System

This package provides three comprehensive scripts for enhancing the AI Scholar RAG system
with arXiv papers:

1. Local Dataset Processor - Process existing PDFs from local dataset
2. Bulk arXiv Downloader - Download and process papers from arXiv bulk data
3. Monthly Auto-Updater - Automated monthly updates of new research papers

The system integrates with existing ChromaDB vector store and scientific PDF processing
infrastructure to provide seamless enhancement of the AI Scholar chatbot's knowledge base.
"""

__version__ = "1.0.0"
__author__ = "AI Scholar Team"

# Import main components for easy access
from .shared.state_manager import StateManager
from .shared.progress_tracker import ProgressTracker
from .shared.error_handler import ErrorHandler
from .shared.data_models import (
    ProcessingState,
    ArxivPaper,
    ProcessingStats,
    UpdateReport,
    ProcessingError,
    ProgressStats,
    ErrorSummary
)

__all__ = [
    'StateManager',
    'ProgressTracker', 
    'ErrorHandler',
    'ProcessingState',
    'ArxivPaper',
    'ProcessingStats',
    'UpdateReport',
    'ProcessingError',
    'ProgressStats',
    'ErrorSummary'
]