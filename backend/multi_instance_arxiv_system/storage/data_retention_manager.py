#!/usr/bin/env python3
"""
Data Retention Manager for multi-instance ArXiv system.

Implements DataRetentionManager with configurable policies, automated cleanup
recommendations and execution, data archival and compression capabilities,
and storage optimization and defragmentation.
"""

import asyncio
import logging
import sys
import os
import shutil
import gzip
import tarfile
import threading
import time
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, NamedTuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import hashlib

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from .storage_monitor import StorageDataType, StorageUsage

logger = logging.getLogger(__name__)


class RetentionAction(Enum):
    """Types of retention actions."""
    DELETE = "delete"
    ARCHIVE = "archive"
    COMPRESS = "compress"
    MOVE = "move"
    KEEP = "keep"


class RetentionPriority(Enum):
    """Priority levels for retention policies."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class RetentionRule:
    """Individual retention rule."""
    name: str
    pattern: str  # File pattern (glob)
    max_age_days: int
    action: RetentionAction
    priority: RetentionPriority = RetentionPriority.NORMAL
    conditions: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    
    def matches_file(self, file_path: Path) -> bool:
        """Check if file matches this rule's pattern."""
        import fnmatch
        return fnmatch.fnmatch(str(file_path), self.pattern)
    
    def is_expired(self, file_path: Path) -> bool:
        """Check if file is expired according to this rule."""
        try:
            if not file_path.exists():
                return False
            
            file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
            return file_age.days > self.max_age_days
            
        except Exception as e:
            logger.error(f"Failed to check file age for {file_path}: {e}")
            return False


@dataclass
class RetentionPolicy:
    """Collection of retention rules for a specific context."""
    name: str
    description: str
    rules: List[RetentionRule] = field(default_factory=list)
    instance_name: Optional[str] = None
    data_type: Optional[StorageDataType] = None
    enabled: bool = True
    
    def add_rule(self, rule: RetentionRule) -> None:
        """Add a retention rule to this policy."""
        self.rules.append(rule)
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a retention rule by name."""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                return True
        return False
    
    def get_applicable_rules(self, file_path: Path) -> List[RetentionRule]:
        """Get rules that apply to the given file."""
        applicable_rules = []
        
        for rule in self.rules:
            if rule.enabled and rule.matches_file(file_path):
                applicable_rules.append(rule)
        
        # Sort by priority (highest first)
        return sorted(applicable_rules, key=lambda r: r.priority.value, reverse=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'rules': [
                {
                    'name': rule.name,
                    'pattern': rule.pattern,
                    'max_age_days': rule.max_age_days,
                    'action': rule.action.value,
                    'priority': rule.priority.value,
                    'conditions': rule.conditions,
                    'enabled': rule.enabled
                }
                for rule in self.rules
            ],
            'instance_name': self.instance_name,
            'data_type': self.data_type.value if self.data_type else None,
            'enabled': self.enabled
        }


@dataclass
class CleanupRecommendation:
    """Recommendation for cleanup action."""
    file_path: str
    action: RetentionAction
    rule_name: str
    estimated_space_savings_mb: float
    priority: RetentionPriority
    reason: str
    safe_to_execute: bool = True
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'file_path': self.file_path,
            'action': self.action.value,
            'rule_name': self.rule_name,
            'estimated_space_savings_mb': self.estimated_space_savings_mb,
            'priority': self.priority.value,
            'reason': self.reason,
            'safe_to_execute': self.safe_to_execute,
            'dependencies': self.dependencies
        }


@dataclass
class CleanupResult:
    """Result of cleanup execution."""
    total_files_processed: int
    total_space_freed_mb: float
    actions_performed: Dict[str, int]
    errors: List[str] = field(default_factory=list)
    execution_time_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'total_files_processed': self.total_files_processed,
            'total_space_freed_mb': self.total_space_freed_mb,
            'actions_performed': self.actions_performed,
            'errors': self.errors,
            'execution_time_seconds': self.execution_time_seconds
        }


class DataRetentionManager:
    """Manages data retention policies and cleanup operations."""
    
    def __init__(self, 
                 database_path: str = "/tmp/data_retention.db",
                 archive_base_path: str = "/tmp/archives"):
        """
        Initialize data retention manager.
        
        Args:
            database_path: Path to SQLite database for persistence
            archive_base_path: Base path for archived files
        """
        self.database_path = database_path
        self.archive_base_path = Path(archive_base_path)
        self.archive_base_path.mkdir(parents=True, exist_ok=True)
        
        # Retention policies
        self.policies: Dict[str, RetentionPolicy] = {}
        
        # Cleanup history
        self.cleanup_history: List[CleanupResult] = []
        
        # Initialize database
        self._init_database()
        
        # Load policies from database
        self._load_from_database()
        
        # Create default policies
        self._create_default_policies()
        
        logger.info("DataRetentionManager initialized")
    
    def _init_database(self) -> None:
        """Initialize SQLite database for retention data."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Create tables
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS retention_policies (
                        name TEXT PRIMARY KEY,
                        policy_json TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cleanup_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        result_json TEXT NOT NULL,
                        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS archived_files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        original_path TEXT NOT NULL,
                        archive_path TEXT NOT NULL,
                        archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        file_size_bytes INTEGER,
                        checksum TEXT
                    )
                ''')
                
                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cleanup_executed ON cleanup_history(executed_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_archived_original ON archived_files(original_path)')
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to initialize retention database: {e}")
            raise
    
    def _load_from_database(self) -> None:
        """Load retention policies from database."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT name, policy_json FROM retention_policies')
                for name, policy_json in cursor.fetchall():
                    try:
                        policy_data = json.loads(policy_json)
                        policy = self._policy_from_dict(policy_data)
                        self.policies[name] = policy
                    except Exception as e:
                        logger.error(f"Failed to load policy {name}: {e}")
                
                logger.info(f"Loaded {len(self.policies)} retention policies")
                
        except Exception as e:
            logger.error(f"Failed to load from retention database: {e}")
    
    def _policy_from_dict(self, data: Dict[str, Any]) -> RetentionPolicy:
        """Create RetentionPolicy from dictionary."""
        policy = RetentionPolicy(
            name=data['name'],
            description=data['description'],
            instance_name=data.get('instance_name'),
            data_type=StorageDataType(data['data_type']) if data.get('data_type') else None,
            enabled=data.get('enabled', True)
        )
        
        for rule_data in data.get('rules', []):
            rule = RetentionRule(
                name=rule_data['name'],
                pattern=rule_data['pattern'],
                max_age_days=rule_data['max_age_days'],
                action=RetentionAction(rule_data['action']),
                priority=RetentionPriority(rule_data['priority']),
                conditions=rule_data.get('conditions', {}),
                enabled=rule_data.get('enabled', True)
            )
            policy.add_rule(rule)
        
        return policy
    
    def _create_default_policies(self) -> None:
        """Create default retention policies if they don't exist."""
        default_policies = [
            {
                'name': 'temp_files_cleanup',
                'description': 'Clean up temporary files older than 7 days',
                'data_type': StorageDataType.TEMP_FILES,
                'rules': [
                    {
                        'name': 'temp_files_delete',
                        'pattern': '*.tmp',
                        'max_age_days': 7,
                        'action': RetentionAction.DELETE,
                        'priority': RetentionPriority.HIGH
                    },
                    {
                        'name': 'cache_files_delete',
                        'pattern': '*.cache',
                        'max_age_days': 14,
                        'action': RetentionAction.DELETE,
                        'priority': RetentionPriority.NORMAL
                    }
                ]
            },
            {
                'name': 'log_files_retention',
                'description': 'Archive old log files and compress recent ones',
                'data_type': StorageDataType.LOG_FILES,
                'rules': [
                    {
                        'name': 'old_logs_archive',
                        'pattern': '*.log',
                        'max_age_days': 90,
                        'action': RetentionAction.ARCHIVE,
                        'priority': RetentionPriority.NORMAL
                    },
                    {
                        'name': 'recent_logs_compress',
                        'pattern': '*.log',
                        'max_age_days': 30,
                        'action': RetentionAction.COMPRESS,
                        'priority': RetentionPriority.LOW
                    }
                ]
            },
            {
                'name': 'processed_data_retention',
                'description': 'Archive old processed data',
                'data_type': StorageDataType.PROCESSED_DATA,
                'rules': [
                    {
                        'name': 'old_processed_archive',
                        'pattern': '*.json',
                        'max_age_days': 180,
                        'action': RetentionAction.ARCHIVE,
                        'priority': RetentionPriority.LOW
                    }
                ]
            }
        ]
        
        for policy_data in default_policies:
            if policy_data['name'] not in self.policies:
                policy = RetentionPolicy(
                    name=policy_data['name'],
                    description=policy_data['description'],
                    data_type=policy_data.get('data_type')
                )
                
                for rule_data in policy_data['rules']:
                    rule = RetentionRule(
                        name=rule_data['name'],
                        pattern=rule_data['pattern'],
                        max_age_days=rule_data['max_age_days'],
                        action=rule_data['action'],
                        priority=rule_data['priority']
                    )
                    policy.add_rule(rule)
                
                self.add_policy(policy)
    
    def add_policy(self, policy: RetentionPolicy) -> bool:
        """Add a retention policy."""
        try:
            self.policies[policy.name] = policy
            
            # Save to database
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO retention_policies (name, policy_json, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (policy.name, json.dumps(policy.to_dict())))
                conn.commit()
            
            logger.info(f"Added retention policy: {policy.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add policy {policy.name}: {e}")
            return False
    
    def remove_policy(self, policy_name: str) -> bool:
        """Remove a retention policy."""
        try:
            if policy_name in self.policies:
                del self.policies[policy_name]
                
                # Remove from database
                with sqlite3.connect(self.database_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM retention_policies WHERE name = ?', (policy_name,))
                    conn.commit()
                
                logger.info(f"Removed retention policy: {policy_name}")
                return True
            else:
                logger.warning(f"Policy not found: {policy_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove policy {policy_name}: {e}")
            return False
    
    async def analyze_directory(self, 
                              directory_path: str,
                              instance_name: Optional[str] = None,
                              data_type: Optional[StorageDataType] = None) -> List[CleanupRecommendation]:
        """
        Analyze directory and generate cleanup recommendations.
        
        Args:
            directory_path: Path to analyze
            instance_name: Instance name for filtering policies
            data_type: Data type for filtering policies
            
        Returns:
            List of cleanup recommendations
        """
        recommendations = []
        
        try:
            directory = Path(directory_path)
            if not directory.exists():
                logger.warning(f"Directory does not exist: {directory_path}")
                return recommendations
            
            # Get applicable policies
            applicable_policies = [
                policy for policy in self.policies.values()
                if policy.enabled and
                (not instance_name or policy.instance_name == instance_name) and
                (not data_type or policy.data_type == data_type)
            ]
            
            logger.info(f"Analyzing {directory_path} with {len(applicable_policies)} policies")
            
            # Walk through directory
            for file_path in directory.rglob('*'):
                if not file_path.is_file():
                    continue
                
                # Check each policy
                for policy in applicable_policies:
                    rules = policy.get_applicable_rules(file_path)
                    
                    for rule in rules:
                        if rule.is_expired(file_path):
                            # Calculate space savings
                            try:
                                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                            except:
                                file_size_mb = 0.0
                            
                            recommendation = CleanupRecommendation(
                                file_path=str(file_path),
                                action=rule.action,
                                rule_name=rule.name,
                                estimated_space_savings_mb=file_size_mb,
                                priority=rule.priority,
                                reason=f"File is {(datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)).days} days old, exceeds {rule.max_age_days} day limit"
                            )
                            
                            recommendations.append(recommendation)
                            break  # Use first matching rule
            
            logger.info(f"Generated {len(recommendations)} cleanup recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to analyze directory {directory_path}: {e}")
            return recommendations
    
    async def execute_cleanup(self, 
                            recommendations: List[CleanupRecommendation],
                            dry_run: bool = True) -> CleanupResult:
        """
        Execute cleanup recommendations.
        
        Args:
            recommendations: List of cleanup recommendations to execute
            dry_run: If True, only simulate execution
            
        Returns:
            CleanupResult with execution details
        """
        start_time = time.time()
        
        result = CleanupResult(
            total_files_processed=0,
            total_space_freed_mb=0.0,
            actions_performed=defaultdict(int)
        )
        
        try:
            logger.info(f"Executing cleanup for {len(recommendations)} recommendations (dry_run={dry_run})")
            
            # Sort recommendations by priority
            sorted_recommendations = sorted(
                recommendations, 
                key=lambda r: r.priority.value, 
                reverse=True
            )
            
            for recommendation in sorted_recommendations:
                try:
                    if not recommendation.safe_to_execute:
                        logger.warning(f"Skipping unsafe recommendation: {recommendation.file_path}")
                        continue
                    
                    file_path = Path(recommendation.file_path)
                    if not file_path.exists():
                        continue
                    
                    # Execute action
                    if recommendation.action == RetentionAction.DELETE:
                        if not dry_run:
                            file_path.unlink()
                        logger.info(f"{'Would delete' if dry_run else 'Deleted'}: {file_path}")
                    
                    elif recommendation.action == RetentionAction.ARCHIVE:
                        archive_path = await self._archive_file(file_path, dry_run)
                        if archive_path:
                            logger.info(f"{'Would archive' if dry_run else 'Archived'}: {file_path} -> {archive_path}")
                    
                    elif recommendation.action == RetentionAction.COMPRESS:
                        compressed_path = await self._compress_file(file_path, dry_run)
                        if compressed_path:
                            logger.info(f"{'Would compress' if dry_run else 'Compressed'}: {file_path} -> {compressed_path}")
                    
                    # Update result
                    result.total_files_processed += 1
                    result.total_space_freed_mb += recommendation.estimated_space_savings_mb
                    result.actions_performed[recommendation.action.value] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to process {recommendation.file_path}: {e}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)
            
            result.execution_time_seconds = time.time() - start_time
            
            # Save cleanup result to history
            self.cleanup_history.append(result)
            self._save_cleanup_result(result)
            
            logger.info(f"Cleanup completed: {result.total_files_processed} files, "
                       f"{result.total_space_freed_mb:.2f}MB freed")
            
            return result
            
        except Exception as e:
            result.errors.append(f"Cleanup execution failed: {e}")
            result.execution_time_seconds = time.time() - start_time
            logger.error(f"Failed to execute cleanup: {e}")
            return result
    
    async def _archive_file(self, file_path: Path, dry_run: bool) -> Optional[str]:
        """Archive a file to the archive directory."""
        try:
            if dry_run:
                return str(self.archive_base_path / f"{file_path.name}.tar.gz")
            
            # Create archive path
            archive_date = datetime.now().strftime("%Y%m%d")
            archive_dir = self.archive_base_path / archive_date
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            archive_path = archive_dir / f"{file_path.stem}.tar.gz"
            
            # Create compressed archive
            with tarfile.open(archive_path, 'w:gz') as tar:
                tar.add(file_path, arcname=file_path.name)
            
            # Calculate checksum
            checksum = self._calculate_file_checksum(file_path)
            
            # Record in database
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO archived_files 
                    (original_path, archive_path, file_size_bytes, checksum)
                    VALUES (?, ?, ?, ?)
                ''', (
                    str(file_path),
                    str(archive_path),
                    file_path.stat().st_size,
                    checksum
                ))
                conn.commit()
            
            # Remove original file
            file_path.unlink()
            
            return str(archive_path)
            
        except Exception as e:
            logger.error(f"Failed to archive file {file_path}: {e}")
            return None
    
    async def _compress_file(self, file_path: Path, dry_run: bool) -> Optional[str]:
        """Compress a file in place."""
        try:
            compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
            
            if dry_run:
                return str(compressed_path)
            
            # Compress file
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file
            file_path.unlink()
            
            return str(compressed_path)
            
        except Exception as e:
            logger.error(f"Failed to compress file {file_path}: {e}")
            return None
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            return ""
    
    def _save_cleanup_result(self, result: CleanupResult) -> None:
        """Save cleanup result to database."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO cleanup_history (result_json)
                    VALUES (?)
                ''', (json.dumps(result.to_dict()),))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save cleanup result: {e}")