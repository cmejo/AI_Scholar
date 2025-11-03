"""
Unit tests for storage monitoring and cleanup systems.
"""

import pytest
import asyncio
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json
import sys

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.monitoring.storage_monitor import StorageMonitor
    from multi_instance_arxiv_system.storage.data_retention_manager import DataRetentionManager
    from multi_instance_arxiv_system.models.monitoring_models import StorageStats
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class TestStorageMonitor:
    """Test cases for StorageMonitor."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def storage_monitor(self):
        """Create StorageMonitor instance."""
        return StorageMonitor()
    
    @pytest.fixture
    def sample_directory_structure(self, temp_dir):
        """Create sample directory structure with files."""
        # Create directories
        (temp_dir / "papers").mkdir()
        (temp_dir / "metadata").mkdir()
        (temp_dir / "logs").mkdir()
        (temp_dir / "cache").mkdir()
        
        # Create sample files with different sizes and ages
        files_to_create = [
            ("papers/paper1.pdf", 1024 * 1024, 1),  # 1MB, 1 day old
            ("papers/paper2.pdf", 2 * 1024 * 1024, 7),  # 2MB, 7 days old
            ("papers/paper3.pdf", 5 * 1024 * 1024, 30),  # 5MB, 30 days old
            ("metadata/paper1.json", 1024, 1),  # 1KB, 1 day old
            ("metadata/paper2.json", 2048, 7),  # 2KB, 7 days old
            ("logs/system.log", 10 * 1024, 1),  # 10KB, 1 day old
            ("logs/old.log", 50 * 1024, 60),  # 50KB, 60 days old
            ("cache/temp1.tmp", 100 * 1024, 1),  # 100KB, 1 day old
            ("cache/temp2.tmp", 200 * 1024, 3),  # 200KB, 3 days old
        ]
        
        for file_path, size, days_old in files_to_create:
            full_path = temp_dir / file_path
            
            # Create file with specified size
            with open(full_path, 'wb') as f:
                f.write(b'0' * size)
            
            # Set file modification time
            old_time = datetime.now() - timedelta(days=days_old)
            timestamp = old_time.timestamp()
            os.utime(full_path, (timestamp, timestamp))
        
        return temp_dir
    
    @pytest.mark.asyncio
    async def test_get_storage_stats(self, storage_monitor, sample_directory_structure):
        """Test getting storage statistics."""
        stats = await storage_monitor.get_storage_stats(str(sample_directory_structure))
        
        assert isinstance(stats, dict)
        assert 'total_size_bytes' in stats
        assert 'total_files' in stats
        assert 'directory_breakdown' in stats
        assert 'file_type_breakdown' in stats
        
        # Check that we have the expected number of files
        assert stats['total_files'] == 9
        
        # Check directory breakdown
        breakdown = stats['directory_breakdown']
        assert 'papers' in breakdown
        assert 'metadata' in breakdown
        assert 'logs' in breakdown
        assert 'cache' in breakdown
        
        # Verify papers directory has 3 files
        assert breakdown['papers']['file_count'] == 3
    
    @pytest.mark.asyncio
    async def test_calculate_directory_sizes(self, storage_monitor, sample_directory_structure):
        """Test calculating directory sizes."""
        directory_sizes = await storage_monitor._calculate_directory_sizes(sample_directory_structure)
        
        assert isinstance(directory_sizes, dict)
        assert 'papers' in directory_sizes
        assert 'metadata' in directory_sizes
        assert 'logs' in directory_sizes
        assert 'cache' in directory_sizes
        
        # Papers directory should be the largest (8MB total)
        papers_size = directory_sizes['papers']['size_bytes']
        metadata_size = directory_sizes['metadata']['size_bytes']
        
        assert papers_size > metadata_size
        assert papers_size == (1 + 2 + 5) * 1024 * 1024  # 8MB
    
    @pytest.mark.asyncio
    async def test_analyze_file_types(self, storage_monitor, sample_directory_structure):
        """Test analyzing file types."""
        file_types = await storage_monitor._analyze_file_types(sample_directory_structure)
        
        assert isinstance(file_types, dict)
        assert '.pdf' in file_types
        assert '.json' in file_types
        assert '.log' in file_types
        assert '.tmp' in file_types
        
        # Check PDF files
        pdf_stats = file_types['.pdf']
        assert pdf_stats['count'] == 3
        assert pdf_stats['total_size_bytes'] == 8 * 1024 * 1024  # 8MB
    
    @pytest.mark.asyncio
    async def test_get_disk_usage(self, storage_monitor, sample_directory_structure):
        """Test getting disk usage information."""
        disk_usage = await storage_monitor.get_disk_usage(str(sample_directory_structure))
        
        assert isinstance(disk_usage, dict)
        assert 'total_bytes' in disk_usage
        assert 'used_bytes' in disk_usage
        assert 'free_bytes' in disk_usage
        assert 'usage_percent' in disk_usage
        
        # Basic sanity checks
        assert disk_usage['total_bytes'] > 0
        assert disk_usage['free_bytes'] >= 0
        assert 0 <= disk_usage['usage_percent'] <= 100
    
    @pytest.mark.asyncio
    async def test_check_storage_thresholds(self, storage_monitor):
        """Test storage threshold checking."""
        # Mock disk usage data
        mock_usage = {
            'total_bytes': 100 * 1024 * 1024 * 1024,  # 100GB
            'used_bytes': 85 * 1024 * 1024 * 1024,   # 85GB
            'free_bytes': 15 * 1024 * 1024 * 1024,   # 15GB
            'usage_percent': 85.0
        }
        
        with patch.object(storage_monitor, 'get_disk_usage', return_value=mock_usage):
            # Test warning threshold (80%)
            result = await storage_monitor.check_storage_thresholds('/test/path', warning_threshold=80)
            
            assert result['status'] == 'warning'
            assert result['usage_percent'] == 85.0
            assert 'threshold exceeded' in result['message'].lower()
            
            # Test critical threshold (90%)
            result = await storage_monitor.check_storage_thresholds('/test/path', critical_threshold=90)
            
            assert result['status'] == 'warning'  # Below critical but above warning
            
            # Test critical threshold (80%)
            result = await storage_monitor.check_storage_thresholds('/test/path', critical_threshold=80)
            
            assert result['status'] == 'critical'
    
    @pytest.mark.asyncio
    async def test_predict_storage_growth(self, storage_monitor, sample_directory_structure):
        """Test storage growth prediction."""
        # Create historical data points
        historical_data = [
            {'timestamp': datetime.now() - timedelta(days=30), 'size_bytes': 5 * 1024 * 1024 * 1024},  # 5GB
            {'timestamp': datetime.now() - timedelta(days=20), 'size_bytes': 6 * 1024 * 1024 * 1024},  # 6GB
            {'timestamp': datetime.now() - timedelta(days=10), 'size_bytes': 7 * 1024 * 1024 * 1024},  # 7GB
            {'timestamp': datetime.now(), 'size_bytes': 8 * 1024 * 1024 * 1024},  # 8GB
        ]
        
        prediction = await storage_monitor.predict_storage_growth(historical_data, days_ahead=30)
        
        assert isinstance(prediction, dict)
        assert 'predicted_size_bytes' in prediction
        assert 'growth_rate_per_day' in prediction
        assert 'days_until_full' in prediction
        
        # Growth rate should be positive (increasing storage)
        assert prediction['growth_rate_per_day'] > 0
        
        # Predicted size should be larger than current
        current_size = historical_data[-1]['size_bytes']
        assert prediction['predicted_size_bytes'] > current_size
    
    @pytest.mark.asyncio
    async def test_generate_storage_report(self, storage_monitor, sample_directory_structure):
        """Test generating comprehensive storage report."""
        report = await storage_monitor.generate_storage_report(str(sample_directory_structure))
        
        assert isinstance(report, dict)
        assert 'timestamp' in report
        assert 'path' in report
        assert 'storage_stats' in report
        assert 'disk_usage' in report
        assert 'threshold_status' in report
        assert 'recommendations' in report
        
        # Check storage stats
        stats = report['storage_stats']
        assert stats['total_files'] == 9
        
        # Check recommendations
        recommendations = report['recommendations']
        assert isinstance(recommendations, list)


class TestDataRetentionManager:
    """Test cases for DataRetentionManager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def retention_manager(self):
        """Create DataRetentionManager instance."""
        return DataRetentionManager()
    
    @pytest.fixture
    def retention_policy(self):
        """Create sample retention policy."""
        return {
            'log_files': {
                'max_age_days': 30,
                'file_patterns': ['*.log'],
                'compress_after_days': 7
            },
            'cache_files': {
                'max_age_days': 7,
                'file_patterns': ['*.tmp', '*.cache'],
                'compress_after_days': None
            },
            'pdf_files': {
                'max_age_days': 365,
                'file_patterns': ['*.pdf'],
                'compress_after_days': 90
            }
        }
    
    @pytest.fixture
    def sample_files_for_retention(self, temp_dir):
        """Create sample files for retention testing."""
        files_to_create = [
            ("logs/recent.log", 1024, 1),  # Recent log file
            ("logs/old.log", 2048, 45),    # Old log file (should be deleted)
            ("logs/medium.log", 1024, 15), # Medium age log (should be compressed)
            ("cache/temp1.tmp", 512, 1),   # Recent cache file
            ("cache/temp2.tmp", 1024, 10), # Old cache file (should be deleted)
            ("papers/recent.pdf", 1024*1024, 30),  # Recent PDF
            ("papers/old.pdf", 2*1024*1024, 400),  # Very old PDF (should be deleted)
            ("papers/medium.pdf", 1024*1024, 120), # Medium age PDF (should be compressed)
        ]
        
        for file_path, size, days_old in files_to_create:
            full_path = temp_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create file with specified size
            with open(full_path, 'wb') as f:
                f.write(b'0' * size)
            
            # Set file modification time
            old_time = datetime.now() - timedelta(days=days_old)
            timestamp = old_time.timestamp()
            os.utime(full_path, (timestamp, timestamp))
        
        return temp_dir
    
    @pytest.mark.asyncio
    async def test_apply_retention_policy(self, retention_manager, retention_policy, sample_files_for_retention):
        """Test applying retention policy."""
        result = await retention_manager.apply_retention_policy(
            str(sample_files_for_retention), 
            retention_policy,
            dry_run=True
        )
        
        assert isinstance(result, dict)
        assert 'files_to_delete' in result
        assert 'files_to_compress' in result
        assert 'space_to_free' in result
        
        # Check that old files are marked for deletion
        files_to_delete = result['files_to_delete']
        delete_names = [Path(f['path']).name for f in files_to_delete]
        
        assert 'old.log' in delete_names  # 45 days old, exceeds 30 day limit
        assert 'temp2.tmp' in delete_names  # 10 days old, exceeds 7 day limit
        assert 'old.pdf' in delete_names  # 400 days old, exceeds 365 day limit
        
        # Check that medium-age files are marked for compression
        files_to_compress = result['files_to_compress']
        compress_names = [Path(f['path']).name for f in files_to_compress]
        
        assert 'medium.log' in compress_names  # 15 days old, should compress after 7 days
        assert 'medium.pdf' in compress_names  # 120 days old, should compress after 90 days
    
    @pytest.mark.asyncio
    async def test_delete_old_files(self, retention_manager, sample_files_for_retention):
        """Test deleting old files."""
        # Delete files older than 35 days
        cutoff_date = datetime.now() - timedelta(days=35)
        
        result = await retention_manager.delete_old_files(
            str(sample_files_for_retention),
            cutoff_date,
            file_patterns=['*.log', '*.pdf'],
            dry_run=False
        )
        
        assert isinstance(result, dict)
        assert 'deleted_files' in result
        assert 'space_freed' in result
        
        # Check that old files were actually deleted
        deleted_files = result['deleted_files']
        assert len(deleted_files) > 0
        
        # Verify files are gone
        for file_info in deleted_files:
            assert not Path(file_info['path']).exists()
    
    @pytest.mark.asyncio
    async def test_compress_files(self, retention_manager, sample_files_for_retention):
        """Test compressing files."""
        # Find files to compress (older than 10 days but newer than 35 days)
        files_to_compress = []
        
        for file_path in sample_files_for_retention.rglob('*'):
            if file_path.is_file():
                file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
                if 10 < file_age.days < 35:
                    files_to_compress.append(str(file_path))
        
        if files_to_compress:
            result = await retention_manager.compress_files(files_to_compress)
            
            assert isinstance(result, dict)
            assert 'compressed_files' in result
            assert 'space_saved' in result
            
            # Check that compressed files exist
            for original_path in files_to_compress:
                compressed_path = original_path + '.gz'
                if Path(compressed_path).exists():
                    # Original should be removed, compressed should exist
                    assert not Path(original_path).exists()
                    assert Path(compressed_path).exists()
    
    @pytest.mark.asyncio
    async def test_calculate_retention_impact(self, retention_manager, retention_policy, sample_files_for_retention):
        """Test calculating retention policy impact."""
        impact = await retention_manager.calculate_retention_impact(
            str(sample_files_for_retention),
            retention_policy
        )
        
        assert isinstance(impact, dict)
        assert 'total_files_affected' in impact
        assert 'total_space_to_free' in impact
        assert 'files_by_action' in impact
        
        # Check breakdown by action
        actions = impact['files_by_action']
        assert 'delete' in actions
        assert 'compress' in actions
        
        # Should have some files to delete and compress
        assert actions['delete']['count'] > 0
        assert actions['compress']['count'] > 0
    
    def test_validate_retention_policy(self, retention_manager):
        """Test retention policy validation."""
        # Valid policy
        valid_policy = {
            'logs': {
                'max_age_days': 30,
                'file_patterns': ['*.log'],
                'compress_after_days': 7
            }
        }
        
        assert retention_manager.validate_retention_policy(valid_policy) == True
        
        # Invalid policy (missing required fields)
        invalid_policy = {
            'logs': {
                'file_patterns': ['*.log']
                # Missing max_age_days
            }
        }
        
        assert retention_manager.validate_retention_policy(invalid_policy) == False
        
        # Invalid policy (negative values)
        negative_policy = {
            'logs': {
                'max_age_days': -5,  # Negative value
                'file_patterns': ['*.log']
            }
        }
        
        assert retention_manager.validate_retention_policy(negative_policy) == False
    
    @pytest.mark.asyncio
    async def test_generate_retention_report(self, retention_manager, retention_policy, sample_files_for_retention):
        """Test generating retention report."""
        report = await retention_manager.generate_retention_report(
            str(sample_files_for_retention),
            retention_policy
        )
        
        assert isinstance(report, dict)
        assert 'timestamp' in report
        assert 'path' in report
        assert 'policy_summary' in report
        assert 'impact_analysis' in report
        assert 'recommendations' in report
        
        # Check policy summary
        policy_summary = report['policy_summary']
        assert len(policy_summary) == len(retention_policy)
        
        # Check recommendations
        recommendations = report['recommendations']
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0


class TestStorageStats:
    """Test cases for StorageStats model."""
    
    def test_storage_stats_creation(self):
        """Test creating StorageStats instance."""
        stats = StorageStats(
            path='/test/path',
            total_size_bytes=1024*1024*1024,  # 1GB
            total_files=100,
            directory_breakdown={
                'papers': {'size_bytes': 500*1024*1024, 'file_count': 50},
                'logs': {'size_bytes': 100*1024*1024, 'file_count': 20}
            },
            file_type_breakdown={
                '.pdf': {'size_bytes': 400*1024*1024, 'count': 40},
                '.log': {'size_bytes': 50*1024*1024, 'count': 10}
            }
        )
        
        assert stats.path == '/test/path'
        assert stats.total_size_bytes == 1024*1024*1024
        assert stats.total_files == 100
        assert 'papers' in stats.directory_breakdown
        assert '.pdf' in stats.file_type_breakdown
    
    def test_storage_stats_size_formatting(self):
        """Test storage size formatting methods."""
        stats = StorageStats(
            path='/test/path',
            total_size_bytes=1536*1024*1024,  # 1.5GB
            total_files=100
        )
        
        # Test size formatting
        formatted_size = stats.get_formatted_size()
        assert '1.5' in formatted_size
        assert 'GB' in formatted_size
        
        # Test size in different units
        size_mb = stats.get_size_in_mb()
        assert size_mb == 1536.0
        
        size_gb = stats.get_size_in_gb()
        assert size_gb == 1.5
    
    def test_storage_stats_validation(self):
        """Test StorageStats validation."""
        # Valid stats
        valid_stats = StorageStats(
            path='/valid/path',
            total_size_bytes=1024,
            total_files=10
        )
        
        assert valid_stats.validate() == True
        
        # Invalid stats (negative values)
        with pytest.raises(ValueError):
            StorageStats(
                path='/invalid/path',
                total_size_bytes=-1024,  # Negative size
                total_files=10
            )
    
    def test_storage_stats_serialization(self):
        """Test StorageStats serialization."""
        stats = StorageStats(
            path='/test/path',
            total_size_bytes=1024*1024,
            total_files=50,
            directory_breakdown={'papers': {'size_bytes': 512*1024, 'file_count': 25}}
        )
        
        stats_dict = stats.to_dict()
        
        assert stats_dict['path'] == '/test/path'
        assert stats_dict['total_size_bytes'] == 1024*1024
        assert stats_dict['total_files'] == 50
        assert 'directory_breakdown' in stats_dict
        assert 'timestamp' in stats_dict


class TestStorageIntegration:
    """Integration tests for storage monitoring and cleanup."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for integration tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_complete_storage_management_workflow(self, temp_dir):
        """Test complete storage management workflow."""
        # Create test environment
        storage_monitor = StorageMonitor()
        retention_manager = DataRetentionManager()
        
        # Create sample files
        (temp_dir / "papers").mkdir()
        (temp_dir / "logs").mkdir()
        
        # Create files of different ages
        files = [
            ("papers/recent.pdf", 1024*1024, 1),    # Recent file
            ("papers/old.pdf", 2*1024*1024, 400),   # Very old file
            ("logs/recent.log", 1024, 1),           # Recent log
            ("logs/old.log", 2048, 60),             # Old log
        ]
        
        for file_path, size, days_old in files:
            full_path = temp_dir / file_path
            with open(full_path, 'wb') as f:
                f.write(b'0' * size)
            
            old_time = datetime.now() - timedelta(days=days_old)
            timestamp = old_time.timestamp()
            os.utime(full_path, (timestamp, timestamp))
        
        # 1. Monitor storage
        initial_stats = await storage_monitor.get_storage_stats(str(temp_dir))
        assert initial_stats['total_files'] == 4
        
        # 2. Apply retention policy
        retention_policy = {
            'pdf_files': {
                'max_age_days': 365,
                'file_patterns': ['*.pdf']
            },
            'log_files': {
                'max_age_days': 30,
                'file_patterns': ['*.log']
            }
        }
        
        retention_result = await retention_manager.apply_retention_policy(
            str(temp_dir),
            retention_policy,
            dry_run=False
        )
        
        # Should delete old files
        assert len(retention_result['files_to_delete']) > 0
        
        # 3. Verify cleanup
        final_stats = await storage_monitor.get_storage_stats(str(temp_dir))
        assert final_stats['total_files'] < initial_stats['total_files']
        
        # 4. Generate report
        report = await storage_monitor.generate_storage_report(str(temp_dir))
        assert 'storage_stats' in report
        assert 'recommendations' in report
    
    @pytest.mark.asyncio
    async def test_storage_threshold_alerting(self, temp_dir):
        """Test storage threshold alerting system."""
        storage_monitor = StorageMonitor()
        
        # Mock high disk usage
        mock_usage = {
            'total_bytes': 100 * 1024 * 1024 * 1024,  # 100GB
            'used_bytes': 95 * 1024 * 1024 * 1024,    # 95GB (95% usage)
            'free_bytes': 5 * 1024 * 1024 * 1024,     # 5GB free
            'usage_percent': 95.0
        }
        
        with patch.object(storage_monitor, 'get_disk_usage', return_value=mock_usage):
            # Check thresholds
            result = await storage_monitor.check_storage_thresholds(
                str(temp_dir),
                warning_threshold=80,
                critical_threshold=90
            )
            
            # Should trigger critical alert
            assert result['status'] == 'critical'
            assert result['usage_percent'] == 95.0
            
            # Should include recommendations
            assert 'recommendations' in result
            assert len(result['recommendations']) > 0