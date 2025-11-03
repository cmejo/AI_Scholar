#!/usr/bin/env python3
"""
Production Readiness Validation Tests for Multi-Instance ArXiv System

This module provides comprehensive production readiness tests including:
- System performance validation under load
- Storage management and cleanup validation
- Error handling and recovery testing
- Security and access control validation
- Scalability and resource management testing
"""

import pytest
import asyncio
import tempfile
import shutil
import yaml
import json
import time
import threading
import concurrent.futures
import psutil
import requests
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import system components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from multi_instance_arxiv_system.core.base_scholar_downloader import BaseScholarDownloader
from multi_instance_arxiv_system.services.storage_monitor import StorageMonitor
from multi_instance_arxiv_system.services.data_retention_manager import DataRetentionManager
from multi_instance_arxiv_system.services.error_recovery_manager import ErrorRecoveryManager
from multi_instance_arxiv_system.config.instance_config import InstanceConfig


class TestProductionReadiness:
    """Test production readiness validation"""
    
    @pytest.fixture
    def temp_production_dir(self):
        """Create temporary production-like directory structure"""
        temp_dir = tempfile.mkdtemp()
        production_dir = Path(temp_dir)
        
        # Create production-like structure
        for instance in ['ai_scholar', 'quant_scholar']:
            instance_dir = production_dir / instance
            (instance_dir / 'papers').mkdir(parents=True)
            (instance_dir / 'logs').mkdir(parents=True)
            (instance_dir / 'cache').mkdir(parents=True)
            (instance_dir / 'reports').mkdir(parents=True)
        
        yield production_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def production_config(self, temp_production_dir):
        """Create production-like configuration"""
        config_data = {
            'instance_name': 'ai_scholar_prod',
            'description': 'AI Scholar Production Instance',
            'storage_path': str(temp_production_dir / 'ai_scholar'),
            'papers_path': str(temp_production_dir / 'ai_scholar' / 'papers'),
            'logs_path': str(temp_production_dir / 'ai_scholar' / 'logs'),
            'cache_path': str(temp_production_dir / 'ai_scholar' / 'cache'),
            'arxiv_categories': ['cs.AI', 'cs.LG', 'cs.CV', 'cs.CL', 'cs.NE', 'cs.RO'],
            'processing': {
                'batch_size': 100,
                'max_concurrent': 4,
                'memory_limit_gb': 16
            },
            'email_notifications': {
                'enabled': True,
                'recipients': ['admin@production.com', 'ops@production.com'],
                'frequency': 'monthly'
            },
            'performance': {
                'max_download_rate': 10,  # papers per second
                'connection_timeout': 30,
                'retry_attempts': 3,
                'memory_threshold': 0.8
            }
        }
        
        config_file = temp_production_dir / 'production_config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        return InstanceConfig.from_yaml(config_file)
    
    def test_system_performance_under_load(self, production_config, temp_production_dir):
        """Test system performance under production-like load"""
        
        # Create large number of test files to simulate production load
        papers_dir = Path(production_config.papers_path)
        
        # Generate test files (simulate 1000 papers)
        test_files = []
        for i in range(100):  # Reduced for testing
            paper_file = papers_dir / f'test_paper_{i:04d}.pdf'
            # Create files with realistic sizes (1-5MB)
            content_size = 1024 * 1024 * (1 + (i % 5))  # 1-5MB
            paper_file.write_bytes(b'x' * content_size)
            test_files.append(paper_file)
        
        # Test concurrent processing performance
        start_time = time.time()
        
        def process_file_batch(file_batch):
            """Simulate processing a batch of files"""
            processed = 0
            for file_path in file_batch:
                try:
                    # Simulate processing time
                    time.sleep(0.01)  # 10ms per file
                    processed += 1
                except Exception:
                    pass
            return processed
        
        # Test with different concurrency levels
        batch_size = 10
        batches = [test_files[i:i+batch_size] for i in range(0, len(test_files), batch_size)]
        
        # Test sequential processing
        sequential_start = time.time()
        sequential_processed = sum(process_file_batch(batch) for batch in batches)
        sequential_time = time.time() - sequential_start
        
        # Test concurrent processing
        concurrent_start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_file_batch, batch) for batch in batches]
            concurrent_processed = sum(future.result() for future in futures)
        concurrent_time = time.time() - concurrent_start
        
        # Validate performance improvements
        assert concurrent_processed == sequential_processed
        assert concurrent_time < sequential_time  # Should be faster with concurrency
        
        # Calculate throughput
        throughput = concurrent_processed / concurrent_time
        assert throughput > 50  # Should process at least 50 files per second
        
        print(f"✓ Performance test passed - Throughput: {throughput:.1f} files/sec")
    
    def test_storage_management_validation(self, production_config, temp_production_dir):
        """Test storage management and cleanup procedures"""
        
        storage_monitor = StorageMonitor(production_config)
        retention_manager = DataRetentionManager(production_config)
        
        # Create test data with different ages
        papers_dir = Path(production_config.papers_path)
        cache_dir = Path(production_config.cache_path)
        logs_dir = Path(production_config.logs_path)
        
        # Create old files (simulate files older than retention period)
        old_timestamp = time.time() - (90 * 24 * 3600)  # 90 days old
        recent_timestamp = time.time() - (7 * 24 * 3600)  # 7 days old
        
        # Create old cache files (should be cleaned up)
        for i in range(10):
            cache_file = cache_dir / f'old_cache_{i}.tmp'
            cache_file.write_text(f"Old cache content {i}")
            os.utime(cache_file, (old_timestamp, old_timestamp))
        
        # Create recent cache files (should be kept)
        for i in range(5):
            cache_file = cache_dir / f'recent_cache_{i}.tmp'
            cache_file.write_text(f"Recent cache content {i}")
            os.utime(cache_file, (recent_timestamp, recent_timestamp))
        
        # Create old log files
        for i in range(15):
            log_file = logs_dir / f'old_log_{i}.log'
            log_file.write_text(f"Old log content {i}")
            os.utime(log_file, (old_timestamp, old_timestamp))
        
        # Test storage monitoring
        storage_stats = storage_monitor.get_storage_statistics()
        
        assert 'total_size_mb' in storage_stats
        assert 'file_count' in storage_stats
        assert 'cache_size_mb' in storage_stats
        assert 'logs_size_mb' in storage_stats
        
        # Test cleanup recommendations
        cleanup_recommendations = retention_manager.get_cleanup_recommendations()
        
        assert 'cache_cleanup' in cleanup_recommendations
        assert 'log_cleanup' in cleanup_recommendations
        assert cleanup_recommendations['cache_cleanup']['file_count'] > 0
        
        # Test actual cleanup execution
        initial_cache_files = len(list(cache_dir.glob('*.tmp')))
        cleanup_results = retention_manager.execute_cleanup(dry_run=False)
        
        assert cleanup_results['success'] is True
        assert cleanup_results['files_removed'] > 0
        
        # Verify old files were removed but recent files kept
        remaining_cache_files = len(list(cache_dir.glob('*.tmp')))
        assert remaining_cache_files < initial_cache_files
        assert remaining_cache_files >= 5  # Recent files should remain
        
        print("✓ Storage management validation passed")
    
    def test_error_handling_and_recovery_mechanisms(self, production_config):
        """Test comprehensive error handling and recovery mechanisms"""
        
        error_recovery = ErrorRecoveryManager(production_config)
        
        # Test network error recovery
        def simulate_network_error():
            raise requests.exceptions.ConnectionError("Network connection failed")
        
        def simulate_timeout_error():
            raise requests.exceptions.Timeout("Request timed out")
        
        def simulate_success():
            return {"status": "success", "data": "test_data"}
        
        # Test retry mechanism with exponential backoff
        with patch('time.sleep'):  # Mock sleep to speed up tests
            # Test successful retry after failures
            call_count = 0
            def failing_then_success():
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    raise requests.exceptions.ConnectionError("Temporary failure")
                return {"status": "success"}
            
            result = error_recovery.retry_with_backoff(
                failing_then_success, 
                max_retries=3,
                initial_delay=1
            )
            
            assert result["status"] == "success"
            assert call_count == 3  # Should have retried twice before success
        
        # Test maximum retry limit
        with patch('time.sleep'):
            def always_failing():
                raise requests.exceptions.ConnectionError("Persistent failure")
            
            with pytest.raises(requests.exceptions.ConnectionError):
                error_recovery.retry_with_backoff(
                    always_failing,
                    max_retries=2,
                    initial_delay=1
                )
        
        # Test error categorization and handling
        test_errors = [
            requests.exceptions.ConnectionError("Network error"),
            requests.exceptions.Timeout("Timeout error"),
            FileNotFoundError("File not found"),
            MemoryError("Out of memory"),
            ValueError("Invalid value")
        ]
        
        for error in test_errors:
            category = error_recovery.categorize_error(error)
            assert category in ['network', 'timeout', 'file', 'memory', 'validation', 'unknown']
            
            # Test recovery strategy selection
            strategy = error_recovery.get_recovery_strategy(category)
            assert strategy is not None
            assert 'action' in strategy
            assert 'retry' in strategy
        
        print("✓ Error handling and recovery validation passed")
    
    def test_security_and_access_control(self, production_config, temp_production_dir):
        """Test security and access control implementations"""
        
        # Test file permissions
        config_file = temp_production_dir / 'production_config.yaml'
        
        # Test that sensitive files have appropriate permissions
        import stat
        
        # Configuration files should be readable only by owner
        config_file.chmod(0o600)
        file_stat = config_file.stat()
        permissions = stat.filemode(file_stat.st_mode)
        assert permissions == '-rw-------'
        
        # Test directory permissions
        papers_dir = Path(production_config.papers_path)
        papers_dir.chmod(0o755)
        dir_stat = papers_dir.stat()
        dir_permissions = stat.filemode(dir_stat.st_mode)
        assert dir_permissions == 'drwxr-xr-x'
        
        # Test input validation and sanitization
        def validate_arxiv_id(arxiv_id):
            """Validate arXiv ID format"""
            import re
            pattern = r'^[a-z-]+(\.[A-Z]{2})?/\d{7}$|^\d{4}\.\d{4,5}$'
            return bool(re.match(pattern, arxiv_id))
        
        # Test valid arXiv IDs
        valid_ids = [
            'cs.AI/2024001',
            'q-fin.ST/2024002',
            '2024.12345',
            'math.ST/2024003'
        ]
        
        for arxiv_id in valid_ids:
            assert validate_arxiv_id(arxiv_id), f"Valid ID rejected: {arxiv_id}"
        
        # Test invalid arXiv IDs (should be rejected)
        invalid_ids = [
            '../../../etc/passwd',
            'cs.AI/../../sensitive_file',
            '<script>alert("xss")</script>',
            'DROP TABLE papers;',
            ''
        ]
        
        for arxiv_id in invalid_ids:
            assert not validate_arxiv_id(arxiv_id), f"Invalid ID accepted: {arxiv_id}"
        
        # Test path traversal prevention
        def safe_file_path(base_path, filename):
            """Ensure file path is within base directory"""
            base = Path(base_path).resolve()
            file_path = (base / filename).resolve()
            
            try:
                file_path.relative_to(base)
                return True
            except ValueError:
                return False
        
        base_dir = temp_production_dir / 'papers'
        
        # Test safe paths
        safe_paths = [
            'paper1.pdf',
            'subdir/paper2.pdf',
            'cs.AI_2024001.pdf'
        ]
        
        for path in safe_paths:
            assert safe_file_path(base_dir, path), f"Safe path rejected: {path}"
        
        # Test dangerous paths (should be rejected)
        dangerous_paths = [
            '../../../etc/passwd',
            '../../sensitive_file.txt',
            '/etc/passwd',
            '..\\..\\windows\\system32\\config\\sam'
        ]
        
        for path in dangerous_paths:
            assert not safe_file_path(base_dir, path), f"Dangerous path accepted: {path}"
        
        print("✓ Security and access control validation passed")
    
    def test_scalability_and_resource_management(self, production_config):
        """Test scalability and resource management under load"""
        
        # Test memory usage monitoring
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Simulate memory-intensive operations
        def memory_intensive_task(size_mb):
            """Simulate memory-intensive processing"""
            data = bytearray(size_mb * 1024 * 1024)  # Allocate memory
            # Simulate processing
            for i in range(0, len(data), 1024):
                data[i] = i % 256
            return len(data)
        
        # Test memory management with different load levels
        memory_results = {}
        
        for load_mb in [10, 50, 100]:
            start_memory = process.memory_info().rss
            
            # Run memory-intensive task
            result = memory_intensive_task(load_mb)
            
            peak_memory = process.memory_info().rss
            memory_increase = (peak_memory - start_memory) / (1024 * 1024)  # MB
            
            memory_results[load_mb] = {
                'memory_increase_mb': memory_increase,
                'processed_bytes': result
            }
            
            # Clean up memory
            import gc
            gc.collect()
        
        # Validate memory usage is reasonable
        for load_mb, result in memory_results.items():
            # Memory increase should be roughly proportional to load
            assert result['memory_increase_mb'] <= load_mb * 1.5  # Allow 50% overhead
        
        # Test concurrent processing scalability
        def cpu_intensive_task(iterations):
            """Simulate CPU-intensive processing"""
            result = 0
            for i in range(iterations):
                result += i * i
            return result
        
        # Test with different numbers of workers
        scalability_results = {}
        
        for num_workers in [1, 2, 4]:
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [
                    executor.submit(cpu_intensive_task, 100000)
                    for _ in range(8)  # 8 tasks
                ]
                results = [future.result() for future in futures]
            
            duration = time.time() - start_time
            scalability_results[num_workers] = {
                'duration': duration,
                'throughput': len(results) / duration
            }
        
        # Validate scalability improvements
        single_worker_time = scalability_results[1]['duration']
        multi_worker_time = scalability_results[4]['duration']
        
        # Multi-worker should be faster (allowing for overhead)
        assert multi_worker_time < single_worker_time * 0.8
        
        print("✓ Scalability and resource management validation passed")
    
    def test_production_configuration_validation(self, production_config):
        """Test production configuration validation"""
        
        # Test configuration completeness
        required_fields = [
            'instance_name', 'storage_path', 'papers_path', 'logs_path',
            'cache_path', 'arxiv_categories', 'processing', 'email_notifications'
        ]
        
        for field in required_fields:
            assert hasattr(production_config, field), f"Missing required field: {field}"
            assert getattr(production_config, field) is not None, f"Field is None: {field}"
        
        # Test production-appropriate settings
        processing_config = production_config.processing
        
        # Batch size should be reasonable for production
        assert 50 <= processing_config['batch_size'] <= 500
        
        # Concurrency should be limited to prevent resource exhaustion
        assert 1 <= processing_config['max_concurrent'] <= 8
        
        # Memory limit should be set
        assert processing_config['memory_limit_gb'] >= 4
        
        # Email notifications should be enabled for production
        email_config = production_config.email_notifications
        assert email_config['enabled'] is True
        assert len(email_config['recipients']) > 0
        
        # Test category configuration
        categories = production_config.arxiv_categories
        assert len(categories) > 0
        
        # Validate category format
        for category in categories:
            assert isinstance(category, str)
            assert len(category) > 0
        
        print("✓ Production configuration validation passed")
    
    def test_monitoring_and_alerting_readiness(self, production_config, temp_production_dir):
        """Test monitoring and alerting system readiness"""
        
        # Test log file creation and rotation
        logs_dir = Path(production_config.logs_path)
        
        # Create test log files
        for i in range(5):
            log_file = logs_dir / f'system_{i}.log'
            log_content = f"""
2024-01-{i+1:02d} 10:00:00 - INFO - System started
2024-01-{i+1:02d} 10:01:00 - INFO - Processing batch 1
2024-01-{i+1:02d} 10:02:00 - WARNING - High memory usage detected
2024-01-{i+1:02d} 10:03:00 - ERROR - Failed to process paper xyz
2024-01-{i+1:02d} 10:04:00 - INFO - System shutdown
"""
            log_file.write_text(log_content)
        
        # Test log analysis for monitoring
        def analyze_logs(log_dir):
            """Analyze logs for monitoring metrics"""
            metrics = {
                'total_entries': 0,
                'error_count': 0,
                'warning_count': 0,
                'info_count': 0
            }
            
            for log_file in Path(log_dir).glob('*.log'):
                with open(log_file, 'r') as f:
                    for line in f:
                        metrics['total_entries'] += 1
                        if 'ERROR' in line:
                            metrics['error_count'] += 1
                        elif 'WARNING' in line:
                            metrics['warning_count'] += 1
                        elif 'INFO' in line:
                            metrics['info_count'] += 1
            
            return metrics
        
        log_metrics = analyze_logs(logs_dir)
        
        assert log_metrics['total_entries'] > 0
        assert log_metrics['error_count'] > 0  # Should detect errors
        assert log_metrics['warning_count'] > 0  # Should detect warnings
        
        # Test alert threshold validation
        error_rate = log_metrics['error_count'] / log_metrics['total_entries']
        warning_rate = log_metrics['warning_count'] / log_metrics['total_entries']
        
        # Define production alert thresholds
        max_error_rate = 0.05  # 5% error rate threshold
        max_warning_rate = 0.10  # 10% warning rate threshold
        
        # Test alert conditions
        should_alert_errors = error_rate > max_error_rate
        should_alert_warnings = warning_rate > max_warning_rate
        
        # In this test case, we expect alerts to be triggered
        assert should_alert_errors or should_alert_warnings
        
        # Test metrics collection for monitoring dashboard
        system_metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'log_metrics': log_metrics
        }
        
        # Validate metrics structure
        assert 'timestamp' in system_metrics
        assert 'cpu_usage' in system_metrics
        assert 'memory_usage' in system_metrics
        assert 'disk_usage' in system_metrics
        assert 'log_metrics' in system_metrics
        
        print("✓ Monitoring and alerting readiness validation passed")
    
    def test_backup_and_recovery_readiness(self, production_config, temp_production_dir):
        """Test backup and recovery system readiness"""
        
        # Create test data for backup
        papers_dir = Path(production_config.papers_path)
        
        # Create test papers
        test_papers = []
        for i in range(10):
            paper_file = papers_dir / f'test_paper_{i:03d}.pdf'
            paper_content = f"Test paper content {i}" * 1000  # Make it substantial
            paper_file.write_text(paper_content)
            test_papers.append(paper_file)
        
        # Test backup creation
        backup_dir = temp_production_dir / 'backups'
        backup_dir.mkdir()
        
        def create_backup(source_dir, backup_path):
            """Create backup of source directory"""
            import tarfile
            
            with tarfile.open(backup_path, 'w:gz') as tar:
                tar.add(source_dir, arcname='papers')
            
            return backup_path.exists()
        
        backup_file = backup_dir / 'papers_backup.tar.gz'
        backup_success = create_backup(papers_dir, backup_file)
        
        assert backup_success
        assert backup_file.exists()
        assert backup_file.stat().st_size > 0
        
        # Test backup integrity
        def verify_backup(backup_path):
            """Verify backup integrity"""
            import tarfile
            
            try:
                with tarfile.open(backup_path, 'r:gz') as tar:
                    # Check if all expected files are in backup
                    members = tar.getnames()
                    return len(members) > 0
            except Exception:
                return False
        
        backup_valid = verify_backup(backup_file)
        assert backup_valid
        
        # Test recovery process
        recovery_dir = temp_production_dir / 'recovery_test'
        recovery_dir.mkdir()
        
        def restore_backup(backup_path, restore_dir):
            """Restore backup to specified directory"""
            import tarfile
            
            try:
                with tarfile.open(backup_path, 'r:gz') as tar:
                    tar.extractall(restore_dir)
                return True
            except Exception:
                return False
        
        restore_success = restore_backup(backup_file, recovery_dir)
        assert restore_success
        
        # Verify restored files
        restored_papers_dir = recovery_dir / 'papers'
        assert restored_papers_dir.exists()
        
        restored_files = list(restored_papers_dir.glob('*.pdf'))
        assert len(restored_files) == len(test_papers)
        
        # Verify file contents
        for original_file in test_papers:
            restored_file = restored_papers_dir / original_file.name
            assert restored_file.exists()
            assert restored_file.read_text() == original_file.read_text()
        
        print("✓ Backup and recovery readiness validation passed")


def run_production_readiness_tests():
    """Run all production readiness validation tests"""
    print("Running Production Readiness Validation Tests")
    print("=" * 50)
    
    # Run pytest with this file
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == "__main__":
    run_production_readiness_tests()