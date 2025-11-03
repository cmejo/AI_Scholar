"""
Enhanced data models for multi-instance ArXiv system.

This module extends the existing data models to support multiple scholar instances
with enhanced metadata, configuration management, and reporting capabilities.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Set, Optional, Any, Union
import json
from pathlib import Path
from abc import ABC, abstractmethod

# Import base models from existing system
try:
    from arxiv_rag_enhancement.shared.data_models import (
        ProcessingError, ProcessingStats, ProcessingState, ProgressStats, ErrorSummary
    )
except ImportError:
    # Fallback for when running from different directory
    import sys
    from pathlib import Path
    backend_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(backend_dir))
    from arxiv_rag_enhancement.shared.data_models import (
        ProcessingError, ProcessingStats, ProcessingState, ProgressStats, ErrorSummary
    )


@dataclass
class BasePaper(ABC):
    """Abstract base class for all paper types."""
    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    published_date: datetime
    instance_name: str  # 'ai_scholar', 'quant_scholar'
    source_type: str = ""  # 'arxiv', 'journal' - set by subclasses
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @abstractmethod
    def get_document_id(self) -> str:
        """Generate a unique document ID for this paper."""
        pass
    
    @abstractmethod
    def get_filename(self) -> str:
        """Generate a safe filename for this paper."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['published_date'] = self.published_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BasePaper':
        """Create from dictionary (JSON deserialization)."""
        data['published_date'] = datetime.fromisoformat(data['published_date'])
        return cls(**data)


@dataclass
class ArxivPaper(BasePaper):
    """Enhanced ArXiv paper model with instance information."""
    arxiv_id: str = ""
    categories: List[str] = field(default_factory=list)
    updated_date: Optional[datetime] = None
    pdf_url: str = ""
    doi: Optional[str] = None
    
    def __post_init__(self):
        if not self.paper_id and self.arxiv_id:
            self.paper_id = self.arxiv_id
        # Always set source_type for ArXiv papers
        self.source_type = 'arxiv'
    
    def get_document_id(self) -> str:
        """Generate a unique document ID for this paper."""
        return f"{self.instance_name}_arxiv_{self.arxiv_id.replace('/', '_').replace('.', '_')}"
    
    def get_filename(self) -> str:
        """Generate a safe filename for this paper."""
        safe_title = "".join(c for c in self.title[:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_arxiv_id = self.arxiv_id.replace('/', '_').replace('.', '_')
        return f"{safe_arxiv_id}_{safe_title}.pdf"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = super().to_dict()
        if self.updated_date:
            data['updated_date'] = self.updated_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArxivPaper':
        """Create from dictionary (JSON deserialization)."""
        if data.get('updated_date'):
            data['updated_date'] = datetime.fromisoformat(data['updated_date'])
        data['published_date'] = datetime.fromisoformat(data['published_date'])
        return cls(**data)


@dataclass
class JournalPaper(BasePaper):
    """Journal paper model for non-arXiv sources."""
    journal_name: str = ""
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    pdf_url: str = ""
    journal_url: str = ""
    
    def __post_init__(self):
        # Always set source_type for Journal papers
        self.source_type = 'journal'
    
    def get_document_id(self) -> str:
        """Generate a unique document ID for this paper."""
        safe_journal = self.journal_name.replace(' ', '_').replace('.', '_').lower()
        safe_title = "".join(c for c in self.title[:30] if c.isalnum() or c in ('_', '-')).lower()
        return f"{self.instance_name}_journal_{safe_journal}_{safe_title}_{self.paper_id}"
    
    def get_filename(self) -> str:
        """Generate a safe filename for this paper."""
        safe_title = "".join(c for c in self.title[:40] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_journal = "".join(c for c in self.journal_name[:20] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        return f"{safe_journal}_{self.paper_id}_{safe_title}.pdf"


@dataclass
class StoragePaths:
    """Storage path configuration for an instance."""
    pdf_directory: str
    processed_directory: str
    state_directory: str
    error_log_directory: str
    archive_directory: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StoragePaths':
        """Create from dictionary (JSON deserialization)."""
        return cls(**data)


@dataclass
class ProcessingConfig:
    """Processing configuration for an instance."""
    batch_size: int = 20
    max_concurrent_downloads: int = 5
    max_concurrent_processing: int = 3
    retry_attempts: int = 3
    timeout_seconds: int = 300
    memory_limit_mb: int = 4096
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingConfig':
        """Create from dictionary (JSON deserialization)."""
        return cls(**data)


@dataclass
class VectorStoreConfig:
    """Vector store configuration for an instance."""
    collection_name: str
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    host: str = "localhost"
    port: int = 8082
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VectorStoreConfig':
        """Create from dictionary (JSON deserialization)."""
        return cls(**data)


@dataclass
class NotificationConfig:
    """Email notification configuration for an instance."""
    enabled: bool = False
    recipients: List[str] = field(default_factory=list)
    smtp_server: str = "localhost"
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    from_email: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationConfig':
        """Create from dictionary (JSON deserialization)."""
        return cls(**data)


@dataclass
class InstanceConfig:
    """Complete configuration for a scholar instance."""
    instance_name: str
    display_name: str
    description: str
    arxiv_categories: List[str]
    journal_sources: List[str]
    storage_paths: StoragePaths
    vector_store_config: VectorStoreConfig
    processing_config: ProcessingConfig
    notification_config: NotificationConfig
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'instance_name': self.instance_name,
            'display_name': self.display_name,
            'description': self.description,
            'arxiv_categories': self.arxiv_categories,
            'journal_sources': self.journal_sources,
            'storage_paths': self.storage_paths.to_dict(),
            'vector_store_config': self.vector_store_config.to_dict(),
            'processing_config': self.processing_config.to_dict(),
            'notification_config': self.notification_config.to_dict(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InstanceConfig':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            instance_name=data['instance_name'],
            display_name=data['display_name'],
            description=data['description'],
            arxiv_categories=data['arxiv_categories'],
            journal_sources=data['journal_sources'],
            storage_paths=StoragePaths.from_dict(data['storage_paths']),
            vector_store_config=VectorStoreConfig.from_dict(data['vector_store_config']),
            processing_config=ProcessingConfig.from_dict(data['processing_config']),
            notification_config=NotificationConfig.from_dict(data['notification_config']),
            metadata=data.get('metadata', {})
        )


@dataclass
class StorageStats:
    """Storage statistics and monitoring data."""
    total_space_gb: float
    used_space_gb: float
    available_space_gb: float
    usage_percentage: float
    instance_breakdown: Dict[str, float]
    growth_rate_gb_per_month: float = 0.0
    projected_full_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        if self.projected_full_date:
            data['projected_full_date'] = self.projected_full_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StorageStats':
        """Create from dictionary (JSON deserialization)."""
        if data.get('projected_full_date'):
            data['projected_full_date'] = datetime.fromisoformat(data['projected_full_date'])
        return cls(**data)


@dataclass
class PerformanceMetrics:
    """Performance metrics for processing operations."""
    download_rate_mbps: float = 0.0
    processing_rate_papers_per_hour: float = 0.0
    embedding_generation_rate: float = 0.0
    memory_usage_peak_mb: int = 0
    cpu_usage_average_percent: float = 0.0
    error_rate_percentage: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceMetrics':
        """Create from dictionary (JSON deserialization)."""
        return cls(**data)


@dataclass
class UpdateReport:
    """Comprehensive report for monthly update operations."""
    instance_name: str
    update_date: datetime
    papers_discovered: int
    papers_downloaded: int
    papers_processed: int
    papers_failed: int
    storage_used_mb: int
    processing_time_seconds: float
    errors: List[ProcessingError]
    storage_stats: StorageStats
    performance_metrics: PerformanceMetrics
    categories_processed: List[str] = field(default_factory=list)
    duplicate_papers_skipped: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'instance_name': self.instance_name,
            'update_date': self.update_date.isoformat(),
            'papers_discovered': self.papers_discovered,
            'papers_downloaded': self.papers_downloaded,
            'papers_processed': self.papers_processed,
            'papers_failed': self.papers_failed,
            'storage_used_mb': self.storage_used_mb,
            'processing_time_seconds': self.processing_time_seconds,
            'errors': [error.to_dict() for error in self.errors],
            'storage_stats': self.storage_stats.to_dict(),
            'performance_metrics': self.performance_metrics.to_dict(),
            'categories_processed': self.categories_processed,
            'duplicate_papers_skipped': self.duplicate_papers_skipped
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpdateReport':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            instance_name=data['instance_name'],
            update_date=datetime.fromisoformat(data['update_date']),
            papers_discovered=data['papers_discovered'],
            papers_downloaded=data['papers_downloaded'],
            papers_processed=data['papers_processed'],
            papers_failed=data['papers_failed'],
            storage_used_mb=data['storage_used_mb'],
            processing_time_seconds=data['processing_time_seconds'],
            errors=[ProcessingError.from_dict(error) for error in data['errors']],
            storage_stats=StorageStats.from_dict(data['storage_stats']),
            performance_metrics=PerformanceMetrics.from_dict(data['performance_metrics']),
            categories_processed=data.get('categories_processed', []),
            duplicate_papers_skipped=data.get('duplicate_papers_skipped', 0)
        )
    
    def save_to_file(self, file_path: Path) -> bool:
        """Save report to JSON file."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save report to {file_path}: {e}")
            return False


@dataclass
class InstanceStats:
    """Statistics for a scholar instance."""
    instance_name: str
    total_papers: int
    processed_papers: int
    failed_papers: int
    storage_used_mb: int
    last_update: datetime
    processing_rate: float
    error_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['last_update'] = self.last_update.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InstanceStats':
        """Create from dictionary (JSON deserialization)."""
        data['last_update'] = datetime.fromisoformat(data['last_update'])
        return cls(**data)


@dataclass
class EmailReport:
    """Email report model for notification formatting."""
    report_id: str
    instance_name: str
    report_type: str  # 'monthly_update', 'error_alert', 'storage_warning'
    subject: str
    html_content: str
    text_content: str
    recipients: List[str]
    attachments: List[str] = field(default_factory=list)
    priority: str = "normal"  # 'low', 'normal', 'high', 'urgent'
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    delivery_status: str = "pending"  # 'pending', 'sent', 'failed', 'bounced'
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.sent_at:
            data['sent_at'] = self.sent_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailReport':
        """Create from dictionary (JSON deserialization)."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('sent_at'):
            data['sent_at'] = datetime.fromisoformat(data['sent_at'])
        return cls(**data)
    
    def mark_as_sent(self) -> None:
        """Mark the email report as sent."""
        self.sent_at = datetime.now()
        self.delivery_status = "sent"
    
    def mark_as_failed(self, error_message: str = "") -> None:
        """Mark the email report as failed."""
        self.delivery_status = "failed"
        if error_message:
            self.metadata['error_message'] = error_message
    
    def get_size_estimate(self) -> int:
        """Get estimated size of the email in bytes."""
        content_size = len(self.html_content.encode('utf-8')) + len(self.text_content.encode('utf-8'))
        subject_size = len(self.subject.encode('utf-8'))
        return content_size + subject_size


@dataclass
class CleanupRecommendation:
    """Recommendation for storage cleanup operations."""
    recommendation_id: str
    instance_name: str
    cleanup_type: str  # 'old_files', 'duplicates', 'failed_processing', 'temp_files'
    description: str
    files_to_remove: List[str]
    space_to_free_mb: int
    risk_level: str = "low"  # 'low', 'medium', 'high'
    auto_executable: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    execution_status: str = "pending"  # 'pending', 'executed', 'failed', 'skipped'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.executed_at:
            data['executed_at'] = self.executed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CleanupRecommendation':
        """Create from dictionary (JSON deserialization)."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('executed_at'):
            data['executed_at'] = datetime.fromisoformat(data['executed_at'])
        return cls(**data)


@dataclass
class SystemHealthReport:
    """Comprehensive system health report."""
    report_id: str
    generated_at: datetime
    overall_status: str  # 'healthy', 'warning', 'critical', 'error'
    instance_reports: Dict[str, 'InstanceHealthReport']
    storage_health: StorageStats
    system_metrics: PerformanceMetrics
    active_alerts: List[str] = field(default_factory=list)
    recommendations: List[CleanupRecommendation] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'report_id': self.report_id,
            'generated_at': self.generated_at.isoformat(),
            'overall_status': self.overall_status,
            'instance_reports': {k: v.to_dict() for k, v in self.instance_reports.items()},
            'storage_health': self.storage_health.to_dict(),
            'system_metrics': self.system_metrics.to_dict(),
            'active_alerts': self.active_alerts,
            'recommendations': [rec.to_dict() for rec in self.recommendations]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemHealthReport':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            report_id=data['report_id'],
            generated_at=datetime.fromisoformat(data['generated_at']),
            overall_status=data['overall_status'],
            instance_reports={k: InstanceHealthReport.from_dict(v) for k, v in data['instance_reports'].items()},
            storage_health=StorageStats.from_dict(data['storage_health']),
            system_metrics=PerformanceMetrics.from_dict(data['system_metrics']),
            active_alerts=data.get('active_alerts', []),
            recommendations=[CleanupRecommendation.from_dict(rec) for rec in data.get('recommendations', [])]
        )


@dataclass
class InstanceHealthReport:
    """Health report for a specific scholar instance."""
    instance_name: str
    status: str  # 'healthy', 'warning', 'critical', 'error', 'offline'
    last_update: datetime
    papers_count: int
    processing_rate: float
    error_rate: float
    storage_usage_mb: int
    vector_store_status: str
    configuration_valid: bool
    active_issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['last_update'] = self.last_update.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InstanceHealthReport':
        """Create from dictionary (JSON deserialization)."""
        data['last_update'] = datetime.fromisoformat(data['last_update'])
        return cls(**data)


@dataclass
class MultiInstanceProcessingState(ProcessingState):
    """Extended processing state with instance information."""
    instance_name: str = ""
    instance_config: Optional[InstanceConfig] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = super().to_dict()
        data['instance_name'] = self.instance_name
        if self.instance_config:
            data['instance_config'] = self.instance_config.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MultiInstanceProcessingState':
        """Create from dictionary (JSON deserialization)."""
        instance_config = None
        if data.get('instance_config'):
            instance_config = InstanceConfig.from_dict(data['instance_config'])
        
        # Remove instance-specific fields before calling parent
        instance_name = data.pop('instance_name', '')
        data.pop('instance_config', None)
        
        # Create base state
        base_state = super().from_dict(data)
        
        # Create multi-instance state
        return cls(
            processor_id=base_state.processor_id,
            start_time=base_state.start_time,
            last_update=base_state.last_update,
            processed_files=base_state.processed_files,
            failed_files=base_state.failed_files,
            current_batch=base_state.current_batch,
            total_files=base_state.total_files,
            processing_stats=base_state.processing_stats,
            metadata=base_state.metadata,
            instance_name=instance_name,
            instance_config=instance_config
        )


@dataclass
class ProcessingResult:
    """Result of processing operations with success/failure tracking."""
    processed_papers: List[str] = field(default_factory=list)
    failed_papers: List[str] = field(default_factory=list)
    processing_errors: List[ProcessingError] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def success_count(self) -> int:
        """Number of successfully processed papers."""
        return len(self.processed_papers)
    
    @property
    def failure_count(self) -> int:
        """Number of failed papers."""
        return len(self.failed_papers)
    
    @property
    def total_count(self) -> int:
        """Total number of papers processed."""
        return self.success_count + self.failure_count
    
    @property
    def success_rate(self) -> float:
        """Success rate as a percentage."""
        if self.total_count == 0:
            return 0.0
        return (self.success_count / self.total_count) * 100.0
    
    @property
    def processing_duration(self) -> Optional[float]:
        """Processing duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'processed_papers': self.processed_papers,
            'failed_papers': self.failed_papers,
            'processing_errors': [error.to_dict() if hasattr(error, 'to_dict') else str(error) 
                                for error in self.processing_errors],
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'total_count': self.total_count,
            'success_rate': self.success_rate,
            'processing_duration': self.processing_duration
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingResult':
        """Create from dictionary (JSON deserialization)."""
        result = cls(
            processed_papers=data.get('processed_papers', []),
            failed_papers=data.get('failed_papers', []),
            processing_errors=data.get('processing_errors', [])
        )
        
        if data.get('start_time'):
            result.start_time = datetime.fromisoformat(data['start_time'])
        if data.get('end_time'):
            result.end_time = datetime.fromisoformat(data['end_time'])
        
        return result


# Additional Reporting and Monitoring Data Models for Task 2.3

@dataclass
class MonitoringAlert:
    """Alert model for system monitoring and notifications."""
    alert_id: str
    instance_name: str
    alert_type: str  # 'storage_warning', 'processing_error', 'performance_degradation', 'system_failure'
    severity: str  # 'info', 'warning', 'error', 'critical'
    title: str
    message: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    status: str = "active"  # 'active', 'acknowledged', 'resolved', 'suppressed'
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MonitoringAlert':
        """Create from dictionary (JSON deserialization)."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('resolved_at'):
            data['resolved_at'] = datetime.fromisoformat(data['resolved_at'])
        return cls(**data)
    
    def resolve(self) -> None:
        """Mark the alert as resolved."""
        self.resolved_at = datetime.now()
        self.status = "resolved"
    
    def acknowledge(self) -> None:
        """Mark the alert as acknowledged."""
        self.status = "acknowledged"


@dataclass
class ProcessingMetrics:
    """Detailed processing metrics for monitoring and reporting."""
    instance_name: str
    measurement_time: datetime
    papers_processed_per_hour: float
    download_speed_mbps: float
    embedding_generation_rate: float
    memory_usage_mb: int
    cpu_usage_percent: float
    disk_io_rate_mbps: float
    network_io_rate_mbps: float
    active_threads: int
    queue_size: int
    error_count_last_hour: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['measurement_time'] = self.measurement_time.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingMetrics':
        """Create from dictionary (JSON deserialization)."""
        data['measurement_time'] = datetime.fromisoformat(data['measurement_time'])
        return cls(**data)


@dataclass
class StorageBreakdown:
    """Detailed storage breakdown by data type and instance."""
    instance_name: str
    measurement_time: datetime
    pdf_files_mb: int
    processed_data_mb: int
    vector_store_mb: int
    logs_mb: int
    temp_files_mb: int
    archive_mb: int
    total_files_count: int
    oldest_file_date: Optional[datetime] = None
    newest_file_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['measurement_time'] = self.measurement_time.isoformat()
        if self.oldest_file_date:
            data['oldest_file_date'] = self.oldest_file_date.isoformat()
        if self.newest_file_date:
            data['newest_file_date'] = self.newest_file_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StorageBreakdown':
        """Create from dictionary (JSON deserialization)."""
        data['measurement_time'] = datetime.fromisoformat(data['measurement_time'])
        if data.get('oldest_file_date'):
            data['oldest_file_date'] = datetime.fromisoformat(data['oldest_file_date'])
        if data.get('newest_file_date'):
            data['newest_file_date'] = datetime.fromisoformat(data['newest_file_date'])
        return cls(**data)
    
    @property
    def total_mb(self) -> int:
        """Total storage used in MB."""
        return (self.pdf_files_mb + self.processed_data_mb + self.vector_store_mb + 
                self.logs_mb + self.temp_files_mb + self.archive_mb)


@dataclass
class ErrorAnalysis:
    """Analysis of errors for reporting and trend identification."""
    instance_name: str
    analysis_period_start: datetime
    analysis_period_end: datetime
    total_errors: int
    error_categories: Dict[str, int]  # error_type -> count
    error_trends: Dict[str, float]  # error_type -> trend_percentage
    most_common_errors: List[str]
    error_rate_by_hour: Dict[int, int]  # hour -> error_count
    resolution_suggestions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['analysis_period_start'] = self.analysis_period_start.isoformat()
        data['analysis_period_end'] = self.analysis_period_end.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorAnalysis':
        """Create from dictionary (JSON deserialization)."""
        data['analysis_period_start'] = datetime.fromisoformat(data['analysis_period_start'])
        data['analysis_period_end'] = datetime.fromisoformat(data['analysis_period_end'])
        return cls(**data)
    
    @property
    def analysis_duration_hours(self) -> float:
        """Duration of analysis period in hours."""
        return (self.analysis_period_end - self.analysis_period_start).total_seconds() / 3600
    
    @property
    def average_errors_per_hour(self) -> float:
        """Average errors per hour during analysis period."""
        if self.analysis_duration_hours == 0:
            return 0.0
        return self.total_errors / self.analysis_duration_hours


@dataclass
class ComparisonReport:
    """Comparison report between current and previous periods."""
    instance_name: str
    current_period: UpdateReport
    previous_period: Optional[UpdateReport]
    comparison_date: datetime
    papers_change: int = 0
    processing_time_change: float = 0.0
    error_rate_change: float = 0.0
    storage_change_mb: int = 0
    performance_change_percent: float = 0.0
    
    def __post_init__(self):
        """Calculate comparison metrics after initialization."""
        if self.previous_period:
            self.papers_change = (self.current_period.papers_processed - 
                                self.previous_period.papers_processed)
            self.processing_time_change = (self.current_period.processing_time_seconds - 
                                         self.previous_period.processing_time_seconds)
            
            # Calculate error rate change
            current_error_rate = (self.current_period.papers_failed / 
                                max(1, self.current_period.papers_processed + self.current_period.papers_failed))
            previous_error_rate = (self.previous_period.papers_failed / 
                                 max(1, self.previous_period.papers_processed + self.previous_period.papers_failed))
            self.error_rate_change = current_error_rate - previous_error_rate
            
            self.storage_change_mb = (self.current_period.storage_used_mb - 
                                    self.previous_period.storage_used_mb)
            
            # Calculate performance change (papers per hour)
            current_rate = (self.current_period.papers_processed / 
                          max(1, self.current_period.processing_time_seconds / 3600))
            previous_rate = (self.previous_period.papers_processed / 
                           max(1, self.previous_period.processing_time_seconds / 3600))
            if previous_rate > 0:
                self.performance_change_percent = ((current_rate - previous_rate) / previous_rate) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'instance_name': self.instance_name,
            'current_period': self.current_period.to_dict(),
            'previous_period': self.previous_period.to_dict() if self.previous_period else None,
            'comparison_date': self.comparison_date.isoformat(),
            'papers_change': self.papers_change,
            'processing_time_change': self.processing_time_change,
            'error_rate_change': self.error_rate_change,
            'storage_change_mb': self.storage_change_mb,
            'performance_change_percent': self.performance_change_percent
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComparisonReport':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            instance_name=data['instance_name'],
            current_period=UpdateReport.from_dict(data['current_period']),
            previous_period=UpdateReport.from_dict(data['previous_period']) if data.get('previous_period') else None,
            comparison_date=datetime.fromisoformat(data['comparison_date']),
            papers_change=data.get('papers_change', 0),
            processing_time_change=data.get('processing_time_change', 0.0),
            error_rate_change=data.get('error_rate_change', 0.0),
            storage_change_mb=data.get('storage_change_mb', 0),
            performance_change_percent=data.get('performance_change_percent', 0.0)
        )


@dataclass
class NotificationHistory:
    """History of sent notifications for tracking and analysis."""
    notification_id: str
    instance_name: str
    notification_type: str  # 'monthly_report', 'error_alert', 'storage_warning', 'system_health'
    recipients: List[str]
    subject: str
    sent_at: datetime
    delivery_status: str  # 'sent', 'failed', 'bounced', 'delivered', 'opened'
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['sent_at'] = self.sent_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationHistory':
        """Create from dictionary (JSON deserialization)."""
        data['sent_at'] = datetime.fromisoformat(data['sent_at'])
        return cls(**data)


@dataclass
class TrendAnalysis:
    """Trend analysis for long-term monitoring and prediction."""
    instance_name: str
    analysis_type: str  # 'processing_rate', 'error_rate', 'storage_growth', 'performance'
    time_period_days: int
    data_points: List[Dict[str, Any]]  # timestamp -> value pairs
    trend_direction: str  # 'increasing', 'decreasing', 'stable', 'volatile'
    trend_strength: float  # 0.0 to 1.0
    predicted_values: Dict[str, float]  # future_date -> predicted_value
    confidence_interval: Dict[str, tuple]  # future_date -> (lower, upper)
    analysis_date: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['analysis_date'] = self.analysis_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrendAnalysis':
        """Create from dictionary (JSON deserialization)."""
        data['analysis_date'] = datetime.fromisoformat(data['analysis_date'])
        return cls(**data)
    
    def get_trend_summary(self) -> str:
        """Get a human-readable trend summary."""
        strength_desc = "strong" if self.trend_strength > 0.7 else "moderate" if self.trend_strength > 0.4 else "weak"
        return f"{strength_desc} {self.trend_direction} trend over {self.time_period_days} days"


@dataclass
class ResourceUtilization:
    """Resource utilization metrics for system monitoring."""
    instance_name: str
    measurement_time: datetime
    cpu_usage_percent: float
    memory_usage_mb: int
    memory_total_mb: int
    disk_usage_percent: float
    disk_io_read_mbps: float
    disk_io_write_mbps: float
    network_in_mbps: float
    network_out_mbps: float
    active_processes: int
    load_average: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['measurement_time'] = self.measurement_time.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResourceUtilization':
        """Create from dictionary (JSON deserialization)."""
        data['measurement_time'] = datetime.fromisoformat(data['measurement_time'])
        return cls(**data)
    
    @property
    def memory_usage_percent(self) -> float:
        """Memory usage as percentage."""
        if self.memory_total_mb == 0:
            return 0.0
        return (self.memory_usage_mb / self.memory_total_mb) * 100.0
    
    @property
    def is_resource_constrained(self) -> bool:
        """Check if system is resource constrained."""
        return (self.cpu_usage_percent > 80 or 
                self.memory_usage_percent > 85 or 
                self.disk_usage_percent > 90)


@dataclass
class QualityMetrics:
    """Quality metrics for processed papers and system health."""
    instance_name: str
    measurement_date: datetime
    papers_with_complete_metadata: int
    papers_with_missing_metadata: int
    embedding_quality_score: float  # 0.0 to 1.0
    text_extraction_success_rate: float
    duplicate_detection_accuracy: float
    processing_consistency_score: float
    data_validation_errors: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['measurement_date'] = self.measurement_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualityMetrics':
        """Create from dictionary (JSON deserialization)."""
        data['measurement_date'] = datetime.fromisoformat(data['measurement_date'])
        return cls(**data)
    
    @property
    def total_papers(self) -> int:
        """Total papers analyzed."""
        return self.papers_with_complete_metadata + self.papers_with_missing_metadata
    
    @property
    def metadata_completeness_rate(self) -> float:
        """Metadata completeness rate as percentage."""
        if self.total_papers == 0:
            return 0.0
        return (self.papers_with_complete_metadata / self.total_papers) * 100.0
    
    @property
    def overall_quality_score(self) -> float:
        """Overall quality score combining all metrics."""
        scores = [
            self.embedding_quality_score,
            self.text_extraction_success_rate / 100.0,
            self.duplicate_detection_accuracy / 100.0,
            self.processing_consistency_score,
            self.metadata_completeness_rate / 100.0
        ]
        return sum(scores) / len(scores)