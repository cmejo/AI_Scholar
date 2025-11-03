"""
Data models for arXiv RAG Enhancement system.

This module defines all the data structures used across the processing scripts,
including state management, progress tracking, and error reporting models.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
import json
from pathlib import Path


@dataclass
class ProcessingError:
    """Represents a processing error with context information."""
    timestamp: datetime
    error_type: str
    file_path: str
    error_message: str
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingError':
        """Create from dictionary (JSON deserialization)."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ProcessingStats:
    """Statistics for processing operations."""
    total_files: int = 0
    processed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    processing_rate: float = 0.0  # files per second
    estimated_completion: Optional[datetime] = None
    current_file: str = ""
    errors: List[ProcessingError] = field(default_factory=list)
    start_time: Optional[datetime] = None
    last_update: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        if self.estimated_completion:
            data['estimated_completion'] = self.estimated_completion.isoformat()
        if self.start_time:
            data['start_time'] = self.start_time.isoformat()
        if self.last_update:
            data['last_update'] = self.last_update.isoformat()
        data['errors'] = [error.to_dict() for error in self.errors]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingStats':
        """Create from dictionary (JSON deserialization)."""
        if data.get('estimated_completion'):
            data['estimated_completion'] = datetime.fromisoformat(data['estimated_completion'])
        if data.get('start_time'):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if data.get('last_update'):
            data['last_update'] = datetime.fromisoformat(data['last_update'])
        if 'errors' in data:
            data['errors'] = [ProcessingError.from_dict(error) for error in data['errors']]
        return cls(**data)


@dataclass
class ProcessingState:
    """State information for resumable processing operations."""
    processor_id: str
    start_time: datetime
    last_update: datetime
    processed_files: Set[str] = field(default_factory=set)
    failed_files: Dict[str, str] = field(default_factory=dict)  # file_path -> error_message
    current_batch: int = 0
    total_files: int = 0
    processing_stats: ProcessingStats = field(default_factory=ProcessingStats)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        data['last_update'] = self.last_update.isoformat()
        data['processed_files'] = list(self.processed_files)
        data['processing_stats'] = self.processing_stats.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingState':
        """Create from dictionary (JSON deserialization)."""
        data['start_time'] = datetime.fromisoformat(data['start_time'])
        data['last_update'] = datetime.fromisoformat(data['last_update'])
        data['processed_files'] = set(data['processed_files'])
        if 'processing_stats' in data:
            data['processing_stats'] = ProcessingStats.from_dict(data['processing_stats'])
        return cls(**data)
    
    def save_to_file(self, file_path: Path) -> bool:
        """Save state to JSON file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save state to {file_path}: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, file_path: Path) -> Optional['ProcessingState']:
        """Load state from JSON file."""
        try:
            if not file_path.exists():
                return None
            with open(file_path, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            print(f"Failed to load state from {file_path}: {e}")
            return None


@dataclass
class ArxivPaper:
    """Represents an arXiv paper with metadata."""
    arxiv_id: str
    title: str
    authors: List[str]
    categories: List[str]
    published_date: datetime
    updated_date: datetime
    abstract: str
    pdf_url: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['published_date'] = self.published_date.isoformat()
        data['updated_date'] = self.updated_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArxivPaper':
        """Create from dictionary (JSON deserialization)."""
        data['published_date'] = datetime.fromisoformat(data['published_date'])
        data['updated_date'] = datetime.fromisoformat(data['updated_date'])
        return cls(**data)
    
    def get_document_id(self) -> str:
        """Generate a unique document ID for this paper."""
        return f"arxiv_{self.arxiv_id.replace('/', '_').replace('.', '_')}"
    
    def get_filename(self) -> str:
        """Generate a safe filename for this paper."""
        safe_title = "".join(c for c in self.title[:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        return f"{self.arxiv_id.replace('/', '_')}_{safe_title}.pdf"


@dataclass
class ProgressStats:
    """Real-time progress statistics."""
    total_items: int
    completed_items: int
    current_item: str
    start_time: datetime
    last_update: datetime
    processing_rate: float  # items per second
    estimated_completion: Optional[datetime] = None
    percentage_complete: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        data['last_update'] = self.last_update.isoformat()
        if self.estimated_completion:
            data['estimated_completion'] = self.estimated_completion.isoformat()
        return data


@dataclass
class ErrorSummary:
    """Summary of errors encountered during processing."""
    total_errors: int
    error_types: Dict[str, int]  # error_type -> count
    failed_files: List[str]
    recent_errors: List[ProcessingError]
    error_rate: float  # errors per processed item
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['recent_errors'] = [error.to_dict() for error in self.recent_errors]
        return data


@dataclass
class UpdateReport:
    """Report for monthly update operations."""
    update_date: datetime
    papers_discovered: int
    papers_downloaded: int
    papers_processed: int
    papers_failed: int
    storage_used: int  # bytes
    processing_time: float  # seconds
    errors: List[str]
    summary: str
    categories_processed: List[str] = field(default_factory=list)
    duplicate_papers_skipped: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['update_date'] = self.update_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpdateReport':
        """Create from dictionary (JSON deserialization)."""
        data['update_date'] = datetime.fromisoformat(data['update_date'])
        return cls(**data)
    
    def save_to_file(self, file_path: Path) -> bool:
        """Save report to JSON file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save report to {file_path}: {e}")
            return False


@dataclass
class DownloadStats:
    """Statistics for download operations."""
    total_papers: int = 0
    downloaded_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    download_rate: float = 0.0  # MB/s
    total_size: int = 0  # bytes
    downloaded_size: int = 0  # bytes
    start_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        if self.start_time:
            data['start_time'] = self.start_time.isoformat()
        if self.estimated_completion:
            data['estimated_completion'] = self.estimated_completion.isoformat()
        return data