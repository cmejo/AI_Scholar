"""
Integration tests for monthly update orchestration and scheduling.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import json
import sys

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.scheduling.monthly_update_orchestrator import MonthlyUpdateOrchestrator
    from multi_instance_arxiv_system.scheduling.instance_update_manager import InstanceUpdateManager
    from multi_instance_arxiv_system.core.instance_config import InstanceConfig, InstanceConfigManager
    from multi_instance_arxiv_system.models.reporting_models import UpdateReport
    from multi_instance_arxiv_system.reporting.email_notification_service import EmailNotificationService
    from multi_instance_arxiv_system.monitoring.storage_monitor import StorageMonitor
    from multi_instance_arxiv_system.error_handling.error_manager import ErrorManager
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class TestMonthlyUpdateOrchestration:
    """Integration tests for monthly update orchestration."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config_dir(self, temp_dir):
        """Create configuration directory with instance configs."""
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        
        # AI Scholar config
        ai_config = {
            'instance_name': 'ai_scholar',
            'storage_path': str(temp_dir / 'ai_scholar'),
            'arxiv_categories': ['cs.AI', 'cs.LG', 'cs.CV'],
            'max_papers_per_run': 200,
            'processing_batch_size': 20,
            'vector_store_collection': 'ai_scholar_papers',
            'email_notifications': True
        }
        
        with open(config_dir / "ai_scholar.yaml", 'w') as f:
            import yaml
            yaml.dump(ai_config, f)
        
        # Quant Scholar config
        quant_config = {
            'instance_name': 'quant_scholar',
            'storage_path': str(temp_dir / 'quant_scholar'),
            'arxiv_categories': ['q-fin.*', 'stat.AP', 'math.ST'],
            'journal_sources': ['jstatsoft', 'rjournal'],
            'max_papers_per_run': 150,
            'processing_batch_size': 15,
            'vector_store_collection': 'quant_scholar_papers',
            'email_notifications': True
        }
        
        with open(config_dir / "quant_scholar.yaml", 'w') as f:
            import yaml
            yaml.dump(quant_config, f)
        
        return config_dir
    
    @pytest.fixture
    def orchestrator(self, config_dir):
        """Create MonthlyUpdateOrchestrator instance."""
        return MonthlyUpdateOrchestrator(str(config_dir))
    
    @pytest.mark.asyncio
    async def test_single_instance_update(self, orchestrator, temp_dir):
        """Test updating a single instance."""
        
        # Mock all the components for AI Scholar
        with patch('multi_instance_arxiv_system.downloaders.ai_scholar_downloader.AIScholarDownloader') as mock_downloader_class, \
             patch('multi_instance_arxiv_system.processors.ai_scholar_processor.AIScholarProcessor') as mock_processor_class, \
             patch('multi_instance_arxiv_system.reporting.email_notification_service.EmailNotificationService') as mock_email_class, \
             patch('multi_instance_arxiv_system.monitoring.storage_monitor.StorageMonitor') as mock_storage_class:
            
            # Setup mock downloader
            mock_downloader = Mock()
            mock_downloader.download_recent_papers = AsyncMock(return_value={
                'success': True,
                'papers_downloaded': 45,
                'duplicates_skipped': 8,
                'processing_time_minutes': 25,
                'errors': []
            })
            mock_downloader.get_download_statistics = AsyncMock(return_value={
                'total_papers': 53,
                'successful_downloads': 45,
                'failed_downloads': 0,
                'success_rate': 100.0,
                'processing_time_minutes': 25
            })
            mock_downloader_class.return_value = mock_downloader
            
            # Setup mock processor
            mock_processor = Mock()
            mock_processor.process_downloaded_papers = AsyncMock(return_value={
                'success': True,
                'papers_processed': 45,
                'processing_errors': 1,
                'vector_store_updates': 44,
                'processing_time_minutes': 15
            })
            mock_processor_class.return_value = mock_processor
            
            # Setup mock email service
            mock_email = Mock()
            mock_email.send_update_notification = AsyncMock(return_value=True)
            mock_email_class.return_value = mock_email
            
            # Setup mock storage monitor
            mock_storage = Mock()
            mock_storage.get_storage_stats = AsyncMock(return_value={
                'total_size_gb': 12.5,
                'total_files': 450,
                'usage_percent': 65.0
            })
            mock_storage_class.return_value = mock_storage
            
            # Run update for AI Scholar
            result = await orchestrator.run_instance_update('ai_scholar')
            
            assert result['success'] == True
            assert result['instance_name'] == 'ai_scholar'
            assert result['papers_downloaded'] == 45
            assert result['papers_processed'] == 45
            assert result['total_errors'] == 1  # 1 processing error
            
            # Verify all components were called
            mock_downloader.download_recent_papers.assert_called_once()
            mock_processor.process_downloaded_papers.assert_called_once()
            mock_email.send_update_notification.assert_called_once()
            
            # Verify update report was generated
            assert 'update_report' in result
            update_report = result['update_report']
            assert update_report['instance_name'] == 'ai_scholar'
            assert update_report['papers_downloaded'] == 45
    
    @pytest.mark.asyncio
    async def test_multi_instance_orchestration(self, orchestrator, temp_dir):
        """Test orchestrating updates for multiple instances."""
        
        # Mock components for both instances
        with patch('multi_instance_arxiv_system.downloaders.ai_scholar_downloader.AIScholarDownloader') as mock_ai_downloader, \
             patch('multi_instance_arxiv_system.processors.ai_scholar_processor.AIScholarProcessor') as mock_ai_processor, \
             patch('multi_instance_arxiv_system.downloaders.quant_scholar_downloader.QuantScholarDownloader') as mock_quant_downloader, \
             patch('multi_instance_arxiv_system.processors.quant_scholar_processor.QuantScholarProcessor') as mock_quant_processor, \
             patch('multi_instance_arxiv_system.reporting.email_notification_service.EmailNotificationService') as mock_email_class, \
             patch('multi_instance_arxiv_system.monitoring.storage_monitor.StorageMonitor') as mock_storage_class:
            
            # Setup AI Scholar mocks
            mock_ai_dl = Mock()
            mock_ai_dl.download_recent_papers = AsyncMock(return_value={
                'success': True,
                'papers_downloaded': 30,
                'duplicates_skipped': 5
            })
            mock_ai_dl.get_download_statistics = AsyncMock(return_value={
                'successful_downloads': 30,
                'failed_downloads': 0,
                'success_rate': 100.0
            })
            mock_ai_downloader.return_value = mock_ai_dl
            
            mock_ai_proc = Mock()
            mock_ai_proc.process_downloaded_papers = AsyncMock(return_value={
                'success': True,
                'papers_processed': 30,
                'processing_errors': 0
            })
            mock_ai_processor.return_value = mock_ai_proc
            
            # Setup Quant Scholar mocks
            mock_quant_dl = Mock()
            mock_quant_dl.download_recent_papers = AsyncMock(return_value={
                'success': True,
                'arxiv_papers_downloaded': 15,
                'journal_papers_downloaded': 8,
                'total_papers_downloaded': 23,
                'duplicates_skipped': 3
            })
            mock_quant_dl.get_download_statistics = AsyncMock(return_value={
                'successful_downloads': 23,
                'failed_downloads': 1,
                'success_rate': 95.8
            })
            mock_quant_downloader.return_value = mock_quant_dl
            
            mock_quant_proc = Mock()
            mock_quant_proc.process_downloaded_papers = AsyncMock(return_value={
                'success': True,
                'papers_processed': 23,
                'processing_errors': 1
            })
            mock_quant_processor.return_value = mock_quant_proc
            
            # Setup shared mocks
            mock_email = Mock()
            mock_email.send_update_notification = AsyncMock(return_value=True)
            mock_email.send_summary_notification = AsyncMock(return_value=True)
            mock_email_class.return_value = mock_email
            
            mock_storage = Mock()
            mock_storage.get_storage_stats = AsyncMock(return_value={
                'total_size_gb': 25.0,
                'total_files': 800
            })
            mock_storage_class.return_value = mock_storage
            
            # Run updates for all instances
            results = await orchestrator.run_all_instances_update()
            
            assert len(results) == 2
            assert all(result['success'] for result in results)
            
            # Find results by instance
            ai_result = next(r for r in results if r['instance_name'] == 'ai_scholar')
            quant_result = next(r for r in results if r['instance_name'] == 'quant_scholar')
            
            # Verify AI Scholar results
            assert ai_result['papers_downloaded'] == 30
            assert ai_result['papers_processed'] == 30
            
            # Verify Quant Scholar results
            assert quant_result['papers_downloaded'] == 23
            assert quant_result['papers_processed'] == 23
            
            # Verify summary notification was sent
            mock_email.send_summary_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_with_file_locking(self, orchestrator, temp_dir):
        """Test file locking to prevent concurrent executions."""
        
        # Mock successful update
        with patch.object(orchestrator, 'run_instance_update') as mock_update:
            mock_update.return_value = {
                'success': True,
                'instance_name': 'ai_scholar',
                'papers_downloaded': 10
            }
            
            # First update should succeed
            result1 = await orchestrator.run_instance_update_with_lock('ai_scholar')
            assert result1['success'] == True
            
            # Simulate concurrent execution attempt
            with patch('fcntl.flock') as mock_flock:
                mock_flock.side_effect = BlockingIOError("Resource temporarily unavailable")
                
                result2 = await orchestrator.run_instance_update_with_lock('ai_scholar')
                assert result2['success'] == False
                assert 'already running' in result2['error'].lower()
    
    @pytest.mark.asyncio
    async def test_update_error_handling_and_recovery(self, orchestrator, temp_dir):
        """Test error handling and recovery during updates."""
        
        with patch('multi_instance_arxiv_system.downloaders.ai_scholar_downloader.AIScholarDownloader') as mock_downloader_class, \
             patch('multi_instance_arxiv_system.processors.ai_scholar_processor.AIScholarProcessor') as mock_processor_class, \
             patch('multi_instance_arxiv_system.reporting.email_notification_service.EmailNotificationService') as mock_email_class:
            
            # Setup downloader that fails
            mock_downloader = Mock()
            mock_downloader.download_recent_papers = AsyncMock(side_effect=Exception("Network timeout"))
            mock_downloader_class.return_value = mock_downloader
            
            # Setup processor (shouldn't be called)
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            
            # Setup email service
            mock_email = Mock()
            mock_email.send_error_notification = AsyncMock(return_value=True)
            mock_email_class.return_value = mock_email
            
            # Run update (should handle error gracefully)
            result = await orchestrator.run_instance_update('ai_scholar')
            
            assert result['success'] == False
            assert 'error' in result
            assert 'Network timeout' in result['error']
            
            # Verify error notification was sent
            mock_email.send_error_notification.assert_called_once()
            
            # Verify processor was not called due to download failure
            mock_processor.process_downloaded_papers.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_retry_mechanism(self, orchestrator, temp_dir):
        """Test retry mechanism for failed operations."""
        
        with patch('multi_instance_arxiv_system.downloaders.ai_scholar_downloader.AIScholarDownloader') as mock_downloader_class:
            
            # Setup downloader that fails twice then succeeds
            mock_downloader = Mock()
            mock_downloader.download_recent_papers = AsyncMock(side_effect=[
                Exception("Temporary network error"),  # First attempt fails
                Exception("Temporary network error"),  # Second attempt fails
                {  # Third attempt succeeds
                    'success': True,
                    'papers_downloaded': 20,
                    'duplicates_skipped': 2
                }
            ])
            mock_downloader.get_download_statistics = AsyncMock(return_value={
                'successful_downloads': 20,
                'failed_downloads': 0,
                'success_rate': 100.0
            })
            mock_downloader_class.return_value = mock_downloader
            
            # Configure retry settings
            orchestrator.max_retries = 3
            orchestrator.retry_delay = 0.1  # Short delay for testing
            
            # Run update with retries
            result = await orchestrator.run_instance_update_with_retry('ai_scholar')
            
            assert result['success'] == True
            assert result['papers_downloaded'] == 20
            assert result['retry_attempts'] == 2  # Failed twice before succeeding
            
            # Verify download was attempted 3 times
            assert mock_downloader.download_recent_papers.call_count == 3


class TestInstanceUpdateManager:
    """Integration tests for InstanceUpdateManager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def ai_scholar_config(self, temp_dir):
        """Create AI Scholar configuration."""
        return InstanceConfig(
            instance_name="ai_scholar",
            storage_path=str(temp_dir / "ai_scholar"),
            arxiv_categories=["cs.AI", "cs.LG"],
            max_papers_per_run=100,
            processing_batch_size=10,
            email_notifications=True
        )
    
    @pytest.fixture
    def update_manager(self, ai_scholar_config):
        """Create InstanceUpdateManager instance."""
        return InstanceUpdateManager(ai_scholar_config)
    
    @pytest.mark.asyncio
    async def test_pre_update_validation(self, update_manager, temp_dir):
        """Test pre-update validation checks."""
        
        # Mock validation components
        with patch.object(update_manager.storage_monitor, 'check_storage_thresholds') as mock_storage_check, \
             patch.object(update_manager.error_manager, 'get_recent_errors') as mock_error_check:
            
            # Setup successful validation
            mock_storage_check.return_value = {
                'status': 'healthy',
                'usage_percent': 70.0,
                'free_space_gb': 50.0
            }
            
            mock_error_check.return_value = []  # No recent critical errors
            
            validation_result = await update_manager.run_pre_update_validation()
            
            assert validation_result['passed'] == True
            assert validation_result['storage_check']['status'] == 'healthy'
            assert len(validation_result['critical_errors']) == 0
    
    @pytest.mark.asyncio
    async def test_pre_update_validation_failure(self, update_manager, temp_dir):
        """Test pre-update validation failure scenarios."""
        
        with patch.object(update_manager.storage_monitor, 'check_storage_thresholds') as mock_storage_check, \
             patch.object(update_manager.error_manager, 'get_recent_errors') as mock_error_check:
            
            # Setup validation failure scenarios
            mock_storage_check.return_value = {
                'status': 'critical',
                'usage_percent': 95.0,
                'free_space_gb': 2.0,
                'message': 'Disk space critically low'
            }
            
            # Mock recent critical errors
            mock_critical_error = Mock()
            mock_critical_error.severity = 'critical'
            mock_critical_error.message = 'Vector store connection failed'
            mock_critical_error.timestamp = datetime.now()
            
            mock_error_check.return_value = [mock_critical_error]
            
            validation_result = await update_manager.run_pre_update_validation()
            
            assert validation_result['passed'] == False
            assert validation_result['storage_check']['status'] == 'critical'
            assert len(validation_result['critical_errors']) == 1
            assert 'blocking_issues' in validation_result
    
    @pytest.mark.asyncio
    async def test_post_update_cleanup(self, update_manager, temp_dir):
        """Test post-update cleanup operations."""
        
        # Create temporary files to clean up
        storage_path = Path(update_manager.config.storage_path)
        storage_path.mkdir(parents=True, exist_ok=True)
        
        cache_dir = storage_path / "cache"
        cache_dir.mkdir(exist_ok=True)
        
        # Create temporary files
        temp_files = [
            cache_dir / "temp1.tmp",
            cache_dir / "temp2.tmp",
            cache_dir / "download.lock"
        ]
        
        for temp_file in temp_files:
            temp_file.write_text("temporary content")
        
        # Mock storage monitoring
        with patch.object(update_manager.storage_monitor, 'get_storage_stats') as mock_storage_stats:
            mock_storage_stats.return_value = {
                'total_size_gb': 15.5,
                'total_files': 350
            }
            
            cleanup_result = await update_manager.run_post_update_cleanup()
            
            assert cleanup_result['success'] == True
            assert cleanup_result['temp_files_removed'] > 0
            
            # Verify temporary files were removed
            for temp_file in temp_files:
                assert not temp_file.exists()
    
    @pytest.mark.asyncio
    async def test_update_report_generation(self, update_manager, temp_dir):
        """Test update report generation."""
        
        # Mock update statistics
        download_stats = {
            'papers_downloaded': 25,
            'duplicates_skipped': 5,
            'processing_time_minutes': 20,
            'success_rate': 100.0
        }
        
        processing_stats = {
            'papers_processed': 25,
            'processing_errors': 1,
            'vector_store_updates': 24,
            'processing_time_minutes': 15
        }
        
        storage_stats = {
            'total_size_gb': 18.2,
            'total_files': 425,
            'usage_percent': 72.0
        }
        
        # Generate update report
        report = await update_manager.generate_update_report(
            download_stats, processing_stats, storage_stats
        )
        
        assert isinstance(report, UpdateReport)
        assert report.instance_name == 'ai_scholar'
        assert report.papers_downloaded == 25
        assert report.papers_processed == 25
        assert report.processing_errors == 1
        assert report.storage_used_gb == 18.2
        
        # Test report serialization
        report_dict = report.to_dict()
        assert report_dict['instance_name'] == 'ai_scholar'
        assert report_dict['papers_downloaded'] == 25


class TestSchedulingIntegration:
    """Integration tests for scheduling system."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_cron_job_simulation(self, temp_dir):
        """Test simulated cron job execution."""
        
        # Create mock configuration
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        
        ai_config = {
            'instance_name': 'ai_scholar',
            'storage_path': str(temp_dir / 'ai_scholar'),
            'arxiv_categories': ['cs.AI'],
            'max_papers_per_run': 50
        }
        
        with open(config_dir / "ai_scholar.yaml", 'w') as f:
            import yaml
            yaml.dump(ai_config, f)
        
        # Simulate monthly cron job execution
        orchestrator = MonthlyUpdateOrchestrator(str(config_dir))
        
        with patch('multi_instance_arxiv_system.downloaders.ai_scholar_downloader.AIScholarDownloader') as mock_downloader_class, \
             patch('multi_instance_arxiv_system.processors.ai_scholar_processor.AIScholarProcessor') as mock_processor_class, \
             patch('multi_instance_arxiv_system.reporting.email_notification_service.EmailNotificationService') as mock_email_class:
            
            # Setup mocks for successful execution
            mock_downloader = Mock()
            mock_downloader.download_recent_papers = AsyncMock(return_value={
                'success': True,
                'papers_downloaded': 15,
                'duplicates_skipped': 2
            })
            mock_downloader.get_download_statistics = AsyncMock(return_value={
                'successful_downloads': 15,
                'failed_downloads': 0,
                'success_rate': 100.0
            })
            mock_downloader_class.return_value = mock_downloader
            
            mock_processor = Mock()
            mock_processor.process_downloaded_papers = AsyncMock(return_value={
                'success': True,
                'papers_processed': 15,
                'processing_errors': 0
            })
            mock_processor_class.return_value = mock_processor
            
            mock_email = Mock()
            mock_email.send_update_notification = AsyncMock(return_value=True)
            mock_email_class.return_value = mock_email
            
            # Simulate cron execution
            start_time = datetime.now()
            result = await orchestrator.run_scheduled_update('ai_scholar')
            end_time = datetime.now()
            
            assert result['success'] == True
            assert result['instance_name'] == 'ai_scholar'
            assert result['execution_time'] is not None
            
            # Verify execution was logged
            execution_time = (end_time - start_time).total_seconds()
            assert execution_time < 60  # Should complete quickly in test
    
    @pytest.mark.asyncio
    async def test_scheduling_conflict_detection(self, temp_dir):
        """Test detection and handling of scheduling conflicts."""
        
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        
        # Create config for testing
        ai_config = {
            'instance_name': 'ai_scholar',
            'storage_path': str(temp_dir / 'ai_scholar')
        }
        
        with open(config_dir / "ai_scholar.yaml", 'w') as f:
            import yaml
            yaml.dump(ai_config, f)
        
        orchestrator = MonthlyUpdateOrchestrator(str(config_dir))
        
        # Create lock file to simulate running process
        lock_dir = temp_dir / "locks"
        lock_dir.mkdir()
        lock_file = lock_dir / "ai_scholar_update.lock"
        
        with open(lock_file, 'w') as f:
            f.write(str(12345))  # Mock PID
        
        # Mock file locking to simulate conflict
        with patch('fcntl.flock') as mock_flock:
            mock_flock.side_effect = BlockingIOError("Resource temporarily unavailable")
            
            result = await orchestrator.run_instance_update_with_lock('ai_scholar')
            
            assert result['success'] == False
            assert 'conflict' in result['error'].lower() or 'running' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_health_check_integration(self, temp_dir):
        """Test integration with health check system."""
        
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        
        orchestrator = MonthlyUpdateOrchestrator(str(config_dir))
        
        # Mock health check components
        with patch('multi_instance_arxiv_system.scripts.system_health_check.SystemHealthChecker') as mock_health_checker:
            
            mock_checker = Mock()
            mock_checker.run_comprehensive_health_check = AsyncMock(return_value={
                'overall_status': 'healthy',
                'instances': {
                    'ai_scholar': {'status': 'healthy'},
                    'quant_scholar': {'status': 'healthy'}
                },
                'system_metrics': {
                    'cpu_usage': 45.0,
                    'memory_usage': 60.0
                },
                'alerts': []
            })
            mock_health_checker.return_value = mock_checker
            
            # Run health check before updates
            health_result = await orchestrator.run_pre_update_health_check()
            
            assert health_result['overall_status'] == 'healthy'
            assert len(health_result['alerts']) == 0
            
            # Verify health check was performed
            mock_checker.run_comprehensive_health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_notification_integration(self, temp_dir):
        """Test integration with notification system."""
        
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        
        orchestrator = MonthlyUpdateOrchestrator(str(config_dir))
        
        # Mock notification service
        with patch('multi_instance_arxiv_system.reporting.email_notification_service.EmailNotificationService') as mock_email_class:
            
            mock_email = Mock()
            mock_email.send_update_notification = AsyncMock(return_value=True)
            mock_email.send_summary_notification = AsyncMock(return_value=True)
            mock_email.send_error_notification = AsyncMock(return_value=True)
            mock_email_class.return_value = mock_email
            
            # Test successful update notification
            update_report = UpdateReport(
                instance_name='ai_scholar',
                update_date=datetime.now(),
                papers_downloaded=20,
                papers_processed=19,
                processing_errors=1,
                processing_time_minutes=30,
                storage_used_gb=15.5
            )
            
            notification_result = await orchestrator.send_update_notifications(update_report)
            
            assert notification_result['success'] == True
            mock_email.send_update_notification.assert_called_once()
            
            # Test error notification
            error_info = {
                'instance_name': 'ai_scholar',
                'error_message': 'Download failed due to network timeout',
                'error_count': 1,
                'timestamp': datetime.now()
            }
            
            error_notification_result = await orchestrator.send_error_notifications(error_info)
            
            assert error_notification_result['success'] == True
            mock_email.send_error_notification.assert_called_once()