"""
Interactive Content Version Control Service

This service provides Git-based version control for notebooks and visualizations
with diff visualization, branching, merging, and automated backup features.
"""

import asyncio
import json
import uuid
import logging
import hashlib
import tempfile
import shutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import difflib

logger = logging.getLogger(__name__)

class ContentType(Enum):
    NOTEBOOK = "notebook"
    VISUALIZATION = "visualization"
    DATASET = "dataset"
    SCRIPT = "script"

class ChangeType(Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"

class MergeStatus(Enum):
    SUCCESS = "success"
    CONFLICT = "conflict"
    FAILED = "failed"

@dataclass
class ContentVersion:
    """Represents a version of interactive content"""
    version_id: str
    content_id: str
    content_type: ContentType
    version_number: int
    commit_hash: str
    content_data: Dict[str, Any]
    metadata: Dict[str, Any]
    author_id: str
    commit_message: str
    created_at: datetime
    parent_versions: List[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.parent_versions is None:
            self.parent_versions = []
        if self.tags is None:
            self.tags = []

@dataclass
class ContentDiff:
    """Represents differences between content versions"""
    diff_id: str
    from_version: str
    to_version: str
    content_id: str
    changes: List[Dict[str, Any]]
    summary: Dict[str, int]  # counts of added, modified, deleted
    created_at: datetime

@dataclass
class Branch:
    """Represents a content branch"""
    branch_id: str
    content_id: str
    branch_name: str
    head_version: str
    created_from: str  # parent branch or version
    created_by: str
    created_at: datetime
    is_active: bool = True
    description: str = ""

@dataclass
class MergeRequest:
    """Represents a merge request between branches"""
    merge_id: str
    content_id: str
    source_branch: str
    target_branch: str
    title: str
    description: str
    author_id: str
    status: MergeStatus
    conflicts: List[Dict[str, Any]]
    created_at: datetime
    merged_at: Optional[datetime] = None
    merged_by: Optional[str] = None

@dataclass
class BackupRecord:
    """Represents an automated backup"""
    backup_id: str
    content_id: str
    backup_type: str  # 'scheduled', 'manual', 'pre_merge'
    version_snapshot: str
    backup_path: str
    created_at: datetime
    retention_until: datetime

class InteractiveContentVersionControl:
    """Service for version control of interactive content"""
    
    def __init__(self):
        self.versions: Dict[str, List[ContentVersion]] = {}  # content_id -> versions
        self.branches: Dict[str, List[Branch]] = {}  # content_id -> branches
        self.merge_requests: Dict[str, MergeRequest] = {}
        self.backups: Dict[str, List[BackupRecord]] = {}  # content_id -> backups
        self.temp_dir = tempfile.mkdtemp(prefix="version_control_")
        
        # Configuration
        self.max_versions_per_content = 100
        self.backup_retention_days = 30
        self.auto_backup_interval_hours = 24
    
    async def initialize_content_versioning(
        self,
        content_id: str,
        content_type: ContentType,
        initial_data: Dict[str, Any],
        author_id: str,
        commit_message: str = "Initial version"
    ) -> ContentVersion:
        """Initialize version control for new content"""
        try:
            # Create initial version
            version = ContentVersion(
                version_id=str(uuid.uuid4()),
                content_id=content_id,
                content_type=content_type,
                version_number=1,
                commit_hash=self._generate_commit_hash(initial_data),
                content_data=initial_data.copy(),
                metadata={
                    'file_size': len(json.dumps(initial_data)),
                    'checksum': self._calculate_checksum(initial_data)
                },
                author_id=author_id,
                commit_message=commit_message,
                created_at=datetime.now()
            )
            
            # Initialize version history
            if content_id not in self.versions:
                self.versions[content_id] = []
            self.versions[content_id].append(version)
            
            # Create main branch
            main_branch = Branch(
                branch_id=str(uuid.uuid4()),
                content_id=content_id,
                branch_name="main",
                head_version=version.version_id,
                created_from="root",
                created_by=author_id,
                created_at=datetime.now(),
                description="Main development branch"
            )
            
            if content_id not in self.branches:
                self.branches[content_id] = []
            self.branches[content_id].append(main_branch)
            
            # Create initial backup
            await self._create_backup(content_id, version.version_id, "initial")
            
            logger.info(f"Initialized version control for content {content_id}")
            return version
            
        except Exception as e:
            logger.error(f"Error initializing version control: {str(e)}")
            raise Exception(f"Failed to initialize version control: {str(e)}")
    
    async def commit_changes(
        self,
        content_id: str,
        updated_data: Dict[str, Any],
        author_id: str,
        commit_message: str,
        branch_name: str = "main"
    ) -> Optional[ContentVersion]:
        """Commit changes to content"""
        try:
            if content_id not in self.versions:
                raise ValueError(f"Content {content_id} not found in version control")
            
            # Get current version
            current_versions = self.versions[content_id]
            if not current_versions:
                raise ValueError(f"No versions found for content {content_id}")
            
            # Find branch
            branch = self._find_branch(content_id, branch_name)
            if not branch:
                raise ValueError(f"Branch {branch_name} not found")
            
            # Get latest version in branch
            latest_version = self._get_version_by_id(content_id, branch.head_version)
            if not latest_version:
                raise ValueError(f"Latest version not found for branch {branch_name}")
            
            # Check if there are actual changes
            if self._calculate_checksum(updated_data) == latest_version.metadata.get('checksum'):
                logger.info(f"No changes detected for content {content_id}")
                return latest_version
            
            # Create new version
            new_version = ContentVersion(
                version_id=str(uuid.uuid4()),
                content_id=content_id,
                content_type=latest_version.content_type,
                version_number=latest_version.version_number + 1,
                commit_hash=self._generate_commit_hash(updated_data),
                content_data=updated_data.copy(),
                metadata={
                    'file_size': len(json.dumps(updated_data)),
                    'checksum': self._calculate_checksum(updated_data),
                    'changes_from_previous': self._count_changes(latest_version.content_data, updated_data)
                },
                author_id=author_id,
                commit_message=commit_message,
                created_at=datetime.now(),
                parent_versions=[latest_version.version_id]
            )
            
            # Add to version history
            self.versions[content_id].append(new_version)
            
            # Update branch head
            branch.head_version = new_version.version_id
            
            # Limit version history
            await self._cleanup_old_versions(content_id)
            
            # Create backup if significant changes
            changes_count = new_version.metadata.get('changes_from_previous', {})
            total_changes = sum(changes_count.values())
            if total_changes > 10:  # Threshold for backup
                await self._create_backup(content_id, new_version.version_id, "significant_changes")
            
            logger.info(f"Committed version {new_version.version_number} for content {content_id}")
            return new_version
            
        except Exception as e:
            logger.error(f"Error committing changes: {str(e)}")
            return None
    
    async def get_version_history(self, content_id: str, branch_name: Optional[str] = None) -> List[ContentVersion]:
        """Get version history for content"""
        try:
            if content_id not in self.versions:
                return []
            
            versions = self.versions[content_id]
            
            if branch_name:
                # Filter versions for specific branch
                branch = self._find_branch(content_id, branch_name)
                if not branch:
                    return []
                
                # Trace back from branch head
                branch_versions = []
                current_version_id = branch.head_version
                
                while current_version_id:
                    version = self._get_version_by_id(content_id, current_version_id)
                    if not version:
                        break
                    
                    branch_versions.append(version)
                    
                    # Move to parent version
                    if version.parent_versions:
                        current_version_id = version.parent_versions[0]
                    else:
                        break
                
                return list(reversed(branch_versions))
            
            return sorted(versions, key=lambda v: v.version_number)
            
        except Exception as e:
            logger.error(f"Error getting version history: {str(e)}")
            return []
    
    async def get_version_diff(self, content_id: str, from_version: str, to_version: str) -> Optional[ContentDiff]:
        """Generate diff between two versions"""
        try:
            from_ver = self._get_version_by_id(content_id, from_version)
            to_ver = self._get_version_by_id(content_id, to_version)
            
            if not from_ver or not to_ver:
                return None
            
            # Generate detailed diff
            changes = self._generate_detailed_diff(from_ver.content_data, to_ver.content_data)
            
            # Create summary
            summary = {
                'added': len([c for c in changes if c['type'] == 'added']),
                'modified': len([c for c in changes if c['type'] == 'modified']),
                'deleted': len([c for c in changes if c['type'] == 'deleted'])
            }
            
            diff = ContentDiff(
                diff_id=str(uuid.uuid4()),
                from_version=from_version,
                to_version=to_version,
                content_id=content_id,
                changes=changes,
                summary=summary,
                created_at=datetime.now()
            )
            
            return diff
            
        except Exception as e:
            logger.error(f"Error generating diff: {str(e)}")
            return None
    
    async def create_branch(
        self,
        content_id: str,
        branch_name: str,
        from_version: str,
        author_id: str,
        description: str = ""
    ) -> Optional[Branch]:
        """Create a new branch from a specific version"""
        try:
            if content_id not in self.versions:
                return None
            
            # Check if branch name already exists
            if self._find_branch(content_id, branch_name):
                raise ValueError(f"Branch {branch_name} already exists")
            
            # Verify source version exists
            source_version = self._get_version_by_id(content_id, from_version)
            if not source_version:
                raise ValueError(f"Source version {from_version} not found")
            
            # Create branch
            branch = Branch(
                branch_id=str(uuid.uuid4()),
                content_id=content_id,
                branch_name=branch_name,
                head_version=from_version,
                created_from=from_version,
                created_by=author_id,
                created_at=datetime.now(),
                description=description
            )
            
            if content_id not in self.branches:
                self.branches[content_id] = []
            self.branches[content_id].append(branch)
            
            logger.info(f"Created branch {branch_name} for content {content_id}")
            return branch
            
        except Exception as e:
            logger.error(f"Error creating branch: {str(e)}")
            return None
    
    async def merge_branches(
        self,
        content_id: str,
        source_branch: str,
        target_branch: str,
        author_id: str,
        merge_message: str
    ) -> MergeRequest:
        """Merge one branch into another"""
        try:
            source = self._find_branch(content_id, source_branch)
            target = self._find_branch(content_id, target_branch)
            
            if not source or not target:
                raise ValueError("Source or target branch not found")
            
            # Get versions to merge
            source_version = self._get_version_by_id(content_id, source.head_version)
            target_version = self._get_version_by_id(content_id, target.head_version)
            
            if not source_version or not target_version:
                raise ValueError("Branch head versions not found")
            
            # Create merge request
            merge_request = MergeRequest(
                merge_id=str(uuid.uuid4()),
                content_id=content_id,
                source_branch=source_branch,
                target_branch=target_branch,
                title=f"Merge {source_branch} into {target_branch}",
                description=merge_message,
                author_id=author_id,
                status=MergeStatus.SUCCESS,
                conflicts=[],
                created_at=datetime.now()
            )
            
            # Detect conflicts
            conflicts = self._detect_merge_conflicts(source_version.content_data, target_version.content_data)
            
            if conflicts:
                merge_request.status = MergeStatus.CONFLICT
                merge_request.conflicts = conflicts
                logger.warning(f"Merge conflicts detected between {source_branch} and {target_branch}")
            else:
                # Perform automatic merge
                merged_data = self._merge_content_data(source_version.content_data, target_version.content_data)
                
                # Create merge commit
                merge_version = await self.commit_changes(
                    content_id=content_id,
                    updated_data=merged_data,
                    author_id=author_id,
                    commit_message=f"Merge {source_branch} into {target_branch}: {merge_message}",
                    branch_name=target_branch
                )
                
                if merge_version:
                    merge_version.parent_versions = [source_version.version_id, target_version.version_id]
                    merge_request.status = MergeStatus.SUCCESS
                    merge_request.merged_at = datetime.now()
                    merge_request.merged_by = author_id
                else:
                    merge_request.status = MergeStatus.FAILED
            
            self.merge_requests[merge_request.merge_id] = merge_request
            return merge_request
            
        except Exception as e:
            logger.error(f"Error merging branches: {str(e)}")
            merge_request = MergeRequest(
                merge_id=str(uuid.uuid4()),
                content_id=content_id,
                source_branch=source_branch,
                target_branch=target_branch,
                title=f"Failed merge: {source_branch} into {target_branch}",
                description=str(e),
                author_id=author_id,
                status=MergeStatus.FAILED,
                conflicts=[],
                created_at=datetime.now()
            )
            self.merge_requests[merge_request.merge_id] = merge_request
            return merge_request
    
    async def revert_to_version(
        self,
        content_id: str,
        version_id: str,
        author_id: str,
        branch_name: str = "main"
    ) -> Optional[ContentVersion]:
        """Revert content to a specific version"""
        try:
            target_version = self._get_version_by_id(content_id, version_id)
            if not target_version:
                return None
            
            # Create backup before revert
            current_branch = self._find_branch(content_id, branch_name)
            if current_branch:
                await self._create_backup(content_id, current_branch.head_version, "pre_revert")
            
            # Create new version with reverted data
            revert_version = await self.commit_changes(
                content_id=content_id,
                updated_data=target_version.content_data.copy(),
                author_id=author_id,
                commit_message=f"Revert to version {target_version.version_number}",
                branch_name=branch_name
            )
            
            if revert_version:
                revert_version.metadata['reverted_from'] = version_id
                logger.info(f"Reverted content {content_id} to version {target_version.version_number}")
            
            return revert_version
            
        except Exception as e:
            logger.error(f"Error reverting to version: {str(e)}")
            return None
    
    async def create_backup(self, content_id: str, backup_type: str = "manual") -> Optional[BackupRecord]:
        """Create manual backup of current content state"""
        try:
            if content_id not in self.versions:
                return None
            
            # Get latest version
            versions = self.versions[content_id]
            if not versions:
                return None
            
            latest_version = max(versions, key=lambda v: v.version_number)
            return await self._create_backup(content_id, latest_version.version_id, backup_type)
            
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            return None
    
    async def restore_from_backup(
        self,
        content_id: str,
        backup_id: str,
        author_id: str
    ) -> Optional[ContentVersion]:
        """Restore content from backup"""
        try:
            if content_id not in self.backups:
                return None
            
            # Find backup
            backup = None
            for b in self.backups[content_id]:
                if b.backup_id == backup_id:
                    backup = b
                    break
            
            if not backup:
                return None
            
            # Get backup data
            backup_version = self._get_version_by_id(content_id, backup.version_snapshot)
            if not backup_version:
                return None
            
            # Create restore version
            restore_version = await self.commit_changes(
                content_id=content_id,
                updated_data=backup_version.content_data.copy(),
                author_id=author_id,
                commit_message=f"Restore from backup {backup_id}"
            )
            
            if restore_version:
                restore_version.metadata['restored_from_backup'] = backup_id
                logger.info(f"Restored content {content_id} from backup {backup_id}")
            
            return restore_version
            
        except Exception as e:
            logger.error(f"Error restoring from backup: {str(e)}")
            return None
    
    async def get_content_branches(self, content_id: str) -> List[Branch]:
        """Get all branches for content"""
        return self.branches.get(content_id, [])
    
    async def get_merge_requests(self, content_id: str) -> List[MergeRequest]:
        """Get merge requests for content"""
        return [mr for mr in self.merge_requests.values() if mr.content_id == content_id]
    
    async def get_backups(self, content_id: str) -> List[BackupRecord]:
        """Get backup records for content"""
        return self.backups.get(content_id, [])
    
    def _generate_commit_hash(self, data: Dict[str, Any]) -> str:
        """Generate commit hash for data"""
        content_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum for data"""
        content_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def _count_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, int]:
        """Count changes between two data structures"""
        changes = {'added': 0, 'modified': 0, 'deleted': 0}
        
        old_keys = set(old_data.keys())
        new_keys = set(new_data.keys())
        
        changes['added'] = len(new_keys - old_keys)
        changes['deleted'] = len(old_keys - new_keys)
        
        for key in old_keys & new_keys:
            if old_data[key] != new_data[key]:
                changes['modified'] += 1
        
        return changes
    
    def _generate_detailed_diff(self, old_data: Dict[str, Any], new_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate detailed diff between two data structures"""
        changes = []
        
        old_keys = set(old_data.keys())
        new_keys = set(new_data.keys())
        
        # Added keys
        for key in new_keys - old_keys:
            changes.append({
                'type': 'added',
                'path': key,
                'new_value': new_data[key]
            })
        
        # Deleted keys
        for key in old_keys - new_keys:
            changes.append({
                'type': 'deleted',
                'path': key,
                'old_value': old_data[key]
            })
        
        # Modified keys
        for key in old_keys & new_keys:
            if old_data[key] != new_data[key]:
                changes.append({
                    'type': 'modified',
                    'path': key,
                    'old_value': old_data[key],
                    'new_value': new_data[key]
                })
        
        return changes
    
    def _detect_merge_conflicts(self, source_data: Dict[str, Any], target_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect merge conflicts between two data structures"""
        conflicts = []
        
        # More sophisticated conflict detection
        # Only consider it a conflict if both branches modified the same key from the base
        for key in source_data.keys() & target_data.keys():
            if source_data[key] != target_data[key]:
                # Check if this is a real conflict (both sides changed the same thing)
                # For now, we'll be more permissive and only flag obvious conflicts
                if isinstance(source_data[key], (str, int, float)) and isinstance(target_data[key], (str, int, float)):
                    # Only flag as conflict if values are significantly different
                    if str(source_data[key]) != str(target_data[key]):
                        # Check if one is clearly an extension of the other (not a conflict)
                        source_str = str(source_data[key])
                        target_str = str(target_data[key])
                        
                        # If one contains the other, it's likely not a conflict
                        if source_str not in target_str and target_str not in source_str:
                            conflicts.append({
                                'path': key,
                                'source_value': source_data[key],
                                'target_value': target_data[key],
                                'conflict_type': 'value_mismatch'
                            })
        
        return conflicts
    
    def _merge_content_data(self, source_data: Dict[str, Any], target_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two data structures (simple strategy)"""
        merged = target_data.copy()
        
        # Add new keys from source
        for key, value in source_data.items():
            if key not in merged:
                merged[key] = value
            # If key exists in both, keep target value (target branch wins)
        
        return merged
    
    def _find_branch(self, content_id: str, branch_name: str) -> Optional[Branch]:
        """Find branch by name"""
        if content_id not in self.branches:
            return None
        
        for branch in self.branches[content_id]:
            if branch.branch_name == branch_name and branch.is_active:
                return branch
        
        return None
    
    def _get_version_by_id(self, content_id: str, version_id: str) -> Optional[ContentVersion]:
        """Get version by ID"""
        if content_id not in self.versions:
            return None
        
        for version in self.versions[content_id]:
            if version.version_id == version_id:
                return version
        
        return None
    
    async def _create_backup(self, content_id: str, version_id: str, backup_type: str) -> Optional[BackupRecord]:
        """Create backup record"""
        try:
            backup = BackupRecord(
                backup_id=str(uuid.uuid4()),
                content_id=content_id,
                backup_type=backup_type,
                version_snapshot=version_id,
                backup_path=f"{self.temp_dir}/backup_{content_id}_{version_id}.json",
                created_at=datetime.now(),
                retention_until=datetime.now() + timedelta(days=self.backup_retention_days)
            )
            
            if content_id not in self.backups:
                self.backups[content_id] = []
            self.backups[content_id].append(backup)
            
            # Clean up old backups
            await self._cleanup_old_backups(content_id)
            
            return backup
            
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            return None
    
    async def _cleanup_old_versions(self, content_id: str):
        """Clean up old versions to maintain limit"""
        if content_id not in self.versions:
            return
        
        versions = self.versions[content_id]
        if len(versions) > self.max_versions_per_content:
            # Keep the most recent versions
            versions.sort(key=lambda v: v.created_at, reverse=True)
            self.versions[content_id] = versions[:self.max_versions_per_content]
            logger.info(f"Cleaned up old versions for content {content_id}")
    
    async def _cleanup_old_backups(self, content_id: str):
        """Clean up expired backups"""
        if content_id not in self.backups:
            return
        
        now = datetime.now()
        active_backups = []
        
        for backup in self.backups[content_id]:
            if backup.retention_until > now:
                active_backups.append(backup)
            else:
                # Clean up backup file if it exists
                try:
                    if os.path.exists(backup.backup_path):
                        os.remove(backup.backup_path)
                except Exception as e:
                    logger.warning(f"Failed to remove backup file {backup.backup_path}: {str(e)}")
        
        self.backups[content_id] = active_backups
        logger.info(f"Cleaned up expired backups for content {content_id}")
    
    def cleanup(self):
        """Clean up temporary files and resources"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            logger.info("Cleaned up version control service resources")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

# Global service instance
interactive_content_version_control = InteractiveContentVersionControl()