"""
Backup and Recovery Service for Multi-Instance Vector Store.

This module provides comprehensive backup and recovery capabilities for
vector store collections with versioning, validation, and automated scheduling.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import asyncio
import json
import shutil
import gzip
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.vector_store.multi_instance_vector_store_service import MultiInstanceVectorStoreService
    from multi_instance_arxiv_system.vector_store.collection_manager import CollectionManager
except ImportError as e:
    print(f"Import error: {e}")
    raise

logger = logging.getLogger(__name__)


class BackupType(Enum):
    """Types of backup operations."""
    FULL = "full"
    INCREMENTAL = "incremental"
    METADATA_ONLY = "metadata_only"
    EMBEDDINGS_ONLY = "embeddings_only"


class BackupStatus(Enum):
    """Backup operation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRUPTED = "corrupted"


@dataclass
class BackupMetadata:
    """Metadata for a backup."""
    
    backup_id: str
    instance_name: str
    backup_type: BackupType
    status: BackupStatus
    
    created_at: datetime
    completed_at: Optional[datetime]
    
    # Backup details
    collection_name: str
    document_count: int
    backup_size_mb: float
    
    # File information
    backup_file_path: str
    checksum: str
    compression_used: bool
    
    # Validation
    validated: bool
    validation_errors: List[str]
    
    # Recovery information
    recovery_tested: bool
    recovery_time_estimate_minutes: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['backup_type'] = self.backup_type.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupMetadata':
        """Create from dictionary (JSON deserialization)."""
        data['backup_type'] = BackupType(data['backup_type'])
        data['status'] = BackupStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return cls(**data)


@dataclass
class RecoveryResult:
    """Result of a recovery operation."""
    
    recovery_id: str
    backup_id: str
    instance_name: str
    success: bool
    
    start_time: datetime
    end_time: datetime
    
    # Recovery details
    documents_restored: int
    errors_encountered: List[str]
    warnings: List[str]
    
    # Validation results
    data_integrity_verified: bool
    collection_health_verified: bool
    
    @property
    def duration_minutes(self) -> float:
        """Duration of recovery in minutes."""
        return (self.end_time - self.start_time).total_seconds() / 60
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        data['end_time'] = self.end_time.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecoveryResult':
        """Create from dictionary (JSON deserialization)."""
        data['start_time'] = datetime.fromisoformat(data['start_time'])
        data['end_time'] = datetime.fromisoformat(data['end_time'])
        return cls(**data)


class BackupRecoveryService:
    """
    Comprehensive backup and recovery service for multi-instance vector store.
    Provides automated backups, validation, and recovery capabilities.
    """
    
    def __init__(
        self, 
        vector_store_service: MultiInstanceVectorStoreService,
        backup_directory: str = "/tmp/vector_store_backups"
    ):
        self.vector_store_service = vector_store_service
        self.backup_directory = Path(backup_directory)
        self.backup_directory.mkdir(parents=True, exist_ok=True)
        
        # Backup tracking
        self.backup_history: List[BackupMetadata] = []
        self.recovery_history: List[RecoveryResult] = []
        
        # Configuration
        self.backup_config = {
            'auto_backup_enabled': True,
            'backup_schedule_hours': [2, 14],  # 2 AM and 2 PM
            'retention_days': 30,
            'max_backups_per_instance': 10,
            'compression_enabled': True,
            'validation_enabled': True,
            'include_embeddings': True,
            'backup_timeout_minutes': 60
        }
        
        # Load existing backup metadata
        self._load_backup_metadata()
    
    def _load_backup_metadata(self) -> None:
        """Load existing backup metadata from disk."""
        
        metadata_file = self.backup_directory / "backup_metadata.json"
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                
                self.backup_history = [
                    BackupMetadata.from_dict(backup_data) 
                    for backup_data in data.get('backups', [])
                ]
                
                self.recovery_history = [
                    RecoveryResult.from_dict(recovery_data)
                    for recovery_data in data.get('recoveries', [])
                ]
                
                logger.info(f"Loaded {len(self.backup_history)} backup records and {len(self.recovery_history)} recovery records")
                
            except Exception as e:
                logger.error(f"Error loading backup metadata: {e}")
    
    def _save_backup_metadata(self) -> None:
        """Save backup metadata to disk."""
        
        metadata_file = self.backup_directory / "backup_metadata.json"
        
        try:
            data = {
                'backups': [backup.to_dict() for backup in self.backup_history],
                'recoveries': [recovery.to_dict() for recovery in self.recovery_history],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving backup metadata: {e}")
    
    async def create_backup(
        self, 
        instance_name: str,
        backup_type: BackupType = BackupType.FULL,
        include_embeddings: bool = True,
        compress: bool = True
    ) -> BackupMetadata:
        """Create a backup for a specific instance."""
        
        logger.info(f"Creating {backup_type.value} backup for {instance_name}")
        
        # Generate backup ID
        backup_id = f"{instance_name}_{backup_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get collection information
        service = self.vector_store_service.instance_services.get(instance_name)
        if not service or not service.collection:
            raise ValueError(f"Instance {instance_name} not properly initialized")
        
        collection = service.collection
        collection_name = service.collection_name
        document_count = collection.count()
        
        # Create backup metadata
        backup_metadata = BackupMetadata(
            backup_id=backup_id,
            instance_name=instance_name,
            backup_type=backup_type,
            status=BackupStatus.PENDING,
            created_at=datetime.now(),
            completed_at=None,
            collection_name=collection_name,
            document_count=document_count,
            backup_size_mb=0.0,
            backup_file_path="",
            checksum="",
            compression_used=compress,
            validated=False,
            validation_errors=[],
            recovery_tested=False,
            recovery_time_estimate_minutes=0
        )
        
        try:
            # Update status
            backup_metadata.status = BackupStatus.IN_PROGRESS
            
            # Create backup data
            backup_data = await self._create_backup_data(
                collection, 
                backup_type, 
                include_embeddings
            )
            
            # Save backup to file
            backup_file_path = await self._save_backup_data(
                backup_data, 
                backup_id, 
                compress
            )
            
            # Calculate file size and checksum
            backup_file = Path(backup_file_path)
            backup_size_mb = backup_file.stat().st_size / (1024 * 1024)
            checksum = self._calculate_file_checksum(backup_file_path)
            
            # Update metadata
            backup_metadata.backup_file_path = backup_file_path
            backup_metadata.backup_size_mb = backup_size_mb
            backup_metadata.checksum = checksum
            backup_metadata.completed_at = datetime.now()
            backup_metadata.status = BackupStatus.COMPLETED
            
            # Validate backup if enabled
            if self.backup_config['validation_enabled']:
                validation_result = await self._validate_backup(backup_metadata)
                backup_metadata.validated = validation_result['valid']
                backup_metadata.validation_errors = validation_result['errors']
            
            # Add to history
            self.backup_history.append(backup_metadata)
            self._save_backup_metadata()
            
            # Clean up old backups
            await self._cleanup_old_backups(instance_name)
            
            logger.info(f"Backup {backup_id} completed successfully ({backup_size_mb:.1f} MB)")
            
        except Exception as e:
            logger.error(f"Backup {backup_id} failed: {e}")
            backup_metadata.status = BackupStatus.FAILED
            backup_metadata.validation_errors.append(f"Backup failed: {str(e)}")
            self.backup_history.append(backup_metadata)
            self._save_backup_metadata()
            raise
        
        return backup_metadata
    
    async def _create_backup_data(
        self, 
        collection: Any, 
        backup_type: BackupType,
        include_embeddings: bool
    ) -> Dict[str, Any]:
        """Create backup data from collection."""
        
        # Determine what to include
        include_fields = ['documents', 'metadatas', 'ids']
        if include_embeddings and backup_type != BackupType.METADATA_ONLY:
            include_fields.append('embeddings')
        
        if backup_type == BackupType.METADATA_ONLY:
            include_fields = ['metadatas', 'ids']
        elif backup_type == BackupType.EMBEDDINGS_ONLY:
            include_fields = ['embeddings', 'ids']
        
        # Get all data from collection
        all_data = collection.get(include=include_fields)
        
        # Create backup data structure
        backup_data = {
            'backup_version': '1.0',
            'backup_timestamp': datetime.now().isoformat(),
            'collection_metadata': collection.metadata,
            'document_count': collection.count(),
            'backup_type': backup_type.value,
            'include_embeddings': include_embeddings,
            'data': all_data
        }
        
        return backup_data
    
    async def _save_backup_data(
        self, 
        backup_data: Dict[str, Any], 
        backup_id: str,
        compress: bool
    ) -> str:
        """Save backup data to file."""
        
        # Create instance backup directory
        instance_dir = self.backup_directory / backup_data['data'].get('metadatas', [{}])[0].get('instance_name', 'unknown')
        instance_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine file extension
        extension = '.json.gz' if compress else '.json'
        backup_file_path = instance_dir / f"{backup_id}{extension}"
        
        # Save data
        if compress:
            with gzip.open(backup_file_path, 'wt', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2)
        else:
            with open(backup_file_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2)
        
        return str(backup_file_path)
    
    def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of a file."""
        
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    async def _validate_backup(self, backup_metadata: BackupMetadata) -> Dict[str, Any]:
        """Validate a backup file."""
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check file exists
            backup_file = Path(backup_metadata.backup_file_path)
            if not backup_file.exists():
                validation_result['valid'] = False
                validation_result['errors'].append("Backup file does not exist")
                return validation_result
            
            # Verify checksum
            current_checksum = self._calculate_file_checksum(backup_metadata.backup_file_path)
            if current_checksum != backup_metadata.checksum:
                validation_result['valid'] = False
                validation_result['errors'].append("Checksum mismatch - file may be corrupted")
                return validation_result
            
            # Load and validate backup data
            backup_data = self._load_backup_data(backup_metadata.backup_file_path)
            
            # Validate data structure
            required_fields = ['backup_version', 'backup_timestamp', 'data']
            for field in required_fields:
                if field not in backup_data:
                    validation_result['errors'].append(f"Missing required field: {field}")
            
            # Validate data content
            data = backup_data.get('data', {})
            
            if 'ids' not in data or not data['ids']:
                validation_result['errors'].append("No document IDs found in backup")
            
            if backup_metadata.backup_type != BackupType.EMBEDDINGS_ONLY:
                if 'documents' not in data or not data['documents']:
                    validation_result['errors'].append("No documents found in backup")
            
            if backup_metadata.backup_type != BackupType.METADATA_ONLY:
                if 'metadatas' not in data or not data['metadatas']:
                    validation_result['warnings'].append("No metadata found in backup")
            
            # Check document count consistency
            expected_count = backup_metadata.document_count
            actual_count = len(data.get('ids', []))
            
            if actual_count != expected_count:
                validation_result['errors'].append(
                    f"Document count mismatch: expected {expected_count}, found {actual_count}"
                )
            
            validation_result['valid'] = len(validation_result['errors']) == 0
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation failed: {str(e)}")
        
        return validation_result
    
    def _load_backup_data(self, backup_file_path: str) -> Dict[str, Any]:
        """Load backup data from file."""
        
        backup_file = Path(backup_file_path)
        
        if backup_file.suffix == '.gz':
            with gzip.open(backup_file_path, 'rt', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(backup_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    async def restore_from_backup(
        self, 
        backup_id: str,
        target_instance_name: Optional[str] = None,
        overwrite_existing: bool = False
    ) -> RecoveryResult:
        """Restore an instance from backup."""
        
        logger.info(f"Starting restore from backup {backup_id}")
        
        # Find backup metadata
        backup_metadata = None
        for backup in self.backup_history:
            if backup.backup_id == backup_id:
                backup_metadata = backup
                break
        
        if not backup_metadata:
            raise ValueError(f"Backup {backup_id} not found")
        
        # Use original instance name if target not specified
        instance_name = target_instance_name or backup_metadata.instance_name
        
        # Generate recovery ID
        recovery_id = f"recovery_{backup_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        start_time = datetime.now()
        errors = []
        warnings = []
        documents_restored = 0
        
        try:
            # Validate backup before restore
            if not backup_metadata.validated:
                validation_result = await self._validate_backup(backup_metadata)
                if not validation_result['valid']:
                    raise ValueError(f"Backup validation failed: {validation_result['errors']}")
            
            # Load backup data
            backup_data = self._load_backup_data(backup_metadata.backup_file_path)
            
            # Check if target instance exists
            if instance_name in self.vector_store_service.initialized_instances:
                if not overwrite_existing:
                    raise ValueError(f"Instance {instance_name} already exists. Use overwrite_existing=True to replace it.")
                
                # Delete existing collection
                collection_manager = CollectionManager()
                await collection_manager.initialize()
                await collection_manager.delete_instance_collection(instance_name)
                warnings.append(f"Deleted existing collection for {instance_name}")
            
            # Create new collection
            collection_manager = CollectionManager()
            await collection_manager.initialize()
            
            creation_result = await collection_manager.create_instance_collection(
                instance_name=instance_name,
                embedding_model=backup_data.get('collection_metadata', {}).get('embedding_model', 'all-MiniLM-L6-v2'),
                description=f"Restored from backup {backup_id}"
            )
            
            if not creation_result['created']:
                raise ValueError(f"Failed to create collection for {instance_name}")
            
            # Get the new collection
            collection = await collection_manager.get_instance_collection(instance_name)
            if not collection:
                raise ValueError(f"Failed to get collection for {instance_name}")
            
            # Restore data
            data = backup_data['data']
            
            if data.get('ids') and data.get('documents'):
                # Prepare data for restoration
                restore_params = {
                    'ids': data['ids'],
                    'documents': data['documents']
                }
                
                if data.get('metadatas'):
                    restore_params['metadatas'] = data['metadatas']
                
                if data.get('embeddings') and backup_metadata.backup_type != BackupType.METADATA_ONLY:
                    restore_params['embeddings'] = data['embeddings']
                
                # Add data to collection
                collection.add(**restore_params)
                documents_restored = len(data['ids'])
            
            # Verify restoration
            restored_count = collection.count()
            if restored_count != backup_metadata.document_count:
                warnings.append(
                    f"Document count mismatch after restore: expected {backup_metadata.document_count}, got {restored_count}"
                )
            
            success = True
            
        except Exception as e:
            logger.error(f"Restore from backup {backup_id} failed: {e}")
            errors.append(f"Restore failed: {str(e)}")
            success = False
        
        end_time = datetime.now()
        
        # Create recovery result
        recovery_result = RecoveryResult(
            recovery_id=recovery_id,
            backup_id=backup_id,
            instance_name=instance_name,
            success=success,
            start_time=start_time,
            end_time=end_time,
            documents_restored=documents_restored,
            errors_encountered=errors,
            warnings=warnings,
            data_integrity_verified=success and len(errors) == 0,
            collection_health_verified=success
        )
        
        # Add to history
        self.recovery_history.append(recovery_result)
        self._save_backup_metadata()
        
        logger.info(f"Restore from backup {backup_id} {'completed' if success else 'failed'}")
        return recovery_result
    
    async def _cleanup_old_backups(self, instance_name: str) -> None:
        """Clean up old backups based on retention policy."""
        
        # Get backups for this instance
        instance_backups = [
            backup for backup in self.backup_history
            if backup.instance_name == instance_name and backup.status == BackupStatus.COMPLETED
        ]
        
        # Sort by creation date (newest first)
        instance_backups.sort(key=lambda b: b.created_at, reverse=True)
        
        # Apply retention policies
        cutoff_date = datetime.now() - timedelta(days=self.backup_config['retention_days'])
        max_backups = self.backup_config['max_backups_per_instance']
        
        backups_to_delete = []
        
        # Mark old backups for deletion
        for backup in instance_backups:
            if backup.created_at < cutoff_date or len(instance_backups) > max_backups:
                backups_to_delete.append(backup)
                instance_backups.remove(backup)
        
        # Delete old backup files
        for backup in backups_to_delete:
            try:
                backup_file = Path(backup.backup_file_path)
                if backup_file.exists():
                    backup_file.unlink()
                    logger.info(f"Deleted old backup file: {backup.backup_file_path}")
                
                # Remove from history
                self.backup_history.remove(backup)
                
            except Exception as e:
                logger.error(f"Error deleting backup {backup.backup_id}: {e}")
        
        if backups_to_delete:
            self._save_backup_metadata()
    
    async def schedule_automated_backups(self) -> None:
        """Schedule automated backups for all instances."""
        
        if not self.backup_config['auto_backup_enabled']:
            return
        
        logger.info("Starting automated backup scheduler")
        
        while True:
            try:
                current_hour = datetime.now().hour
                
                if current_hour in self.backup_config['backup_schedule_hours']:
                    # Run backups for all instances
                    for instance_name in self.vector_store_service.initialized_instances:
                        try:
                            await self.create_backup(
                                instance_name=instance_name,
                                backup_type=BackupType.FULL,
                                include_embeddings=self.backup_config['include_embeddings'],
                                compress=self.backup_config['compression_enabled']
                            )
                        except Exception as e:
                            logger.error(f"Automated backup failed for {instance_name}: {e}")
                
                # Wait for next hour
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in automated backup scheduler: {e}")
                await asyncio.sleep(3600)
    
    def get_backup_history(
        self, 
        instance_name: Optional[str] = None,
        days: int = 30
    ) -> List[BackupMetadata]:
        """Get backup history with optional filtering."""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        history = [
            backup for backup in self.backup_history
            if backup.created_at >= cutoff_date
        ]
        
        if instance_name:
            history = [b for b in history if b.instance_name == instance_name]
        
        return sorted(history, key=lambda b: b.created_at, reverse=True)
    
    def get_recovery_history(
        self, 
        instance_name: Optional[str] = None,
        days: int = 30
    ) -> List[RecoveryResult]:
        """Get recovery history with optional filtering."""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        history = [
            recovery for recovery in self.recovery_history
            if recovery.start_time >= cutoff_date
        ]
        
        if instance_name:
            history = [r for r in history if r.instance_name == instance_name]
        
        return sorted(history, key=lambda r: r.start_time, reverse=True)
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get backup and recovery statistics."""
        
        total_backups = len(self.backup_history)
        successful_backups = len([b for b in self.backup_history if b.status == BackupStatus.COMPLETED])
        
        total_recoveries = len(self.recovery_history)
        successful_recoveries = len([r for r in self.recovery_history if r.success])
        
        # Calculate storage usage
        total_backup_size_mb = sum(b.backup_size_mb for b in self.backup_history if b.status == BackupStatus.COMPLETED)
        
        # Get backup frequency by instance
        instance_backup_counts = {}
        for backup in self.backup_history:
            instance = backup.instance_name
            instance_backup_counts[instance] = instance_backup_counts.get(instance, 0) + 1
        
        return {
            'total_backups': total_backups,
            'successful_backups': successful_backups,
            'backup_success_rate': successful_backups / max(1, total_backups),
            'total_recoveries': total_recoveries,
            'successful_recoveries': successful_recoveries,
            'recovery_success_rate': successful_recoveries / max(1, total_recoveries),
            'total_backup_storage_mb': total_backup_size_mb,
            'backup_counts_by_instance': instance_backup_counts,
            'auto_backup_enabled': self.backup_config['auto_backup_enabled'],
            'retention_days': self.backup_config['retention_days']
        }