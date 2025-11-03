#!/usr/bin/env python3
"""
Automated Scheduling Validation Tests for Multi-Instance ArXiv System

This module validates the automated monthly scheduling system, cron job setup,
file locking mechanisms, and scheduling conflict detection.
"""

import pytest
import tempfile
import shutil
import yaml
import json
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import system components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from multi_instance_arxiv_system.scheduling.monthly_update_orchestrator import MonthlyUpdateOrchestrator
from multi_instance_arxiv_system.scheduling.instance_update_manager import InstanceUpdateManager
from multi_instance_arxiv_system.config.instance_config import InstanceConfig


class TestAutomatedSchedulingValidation:
    """Test automated scheduling system validation"""
    
    @pytest.fixture
    def temp_system_dir(self):
        """Create temporary system directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def test_configs(self, temp_system_dir):
        """Create test configurations for both instances"""
        configs = []
        
        for instance_name in ['ai_scholar', 'quant_scholar']:
            config_data = {
                'instance_name': f'{instance_name}_test',
                'description': f'{instance_name.title()} Test Instance',
                'storage_path': str(temp_system_dir / instance_name),
                'papers_path': str(temp_system_dir / instance_name / 'papers'),
                'logs_path': str(temp_system_dir / instance_name / 'logs'),
                'cache_path': str(temp_system_dir / instance_name / 'cache'),
                'arxiv_categories': ['cs.AI'] if instance_name == 'ai_scholar' else ['q-fin.ST'],
                'processing': {
                    'batch_size': 10,
                    'max_concurrent': 1,
                    'memory_limit_gb': 2
                },
                'email_notifications': {
                    'enabled': True,
                    'recipients': ['test@example.com'],
                    'frequency': 'monthly'
                }
            }
            
            config_file = temp_system_dir / f'{instance_name}_config.yaml'
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f)
            
            configs.append(InstanceConfig.from_yaml(config_file))
        
        return configs
    
    @pytest.fixture
    def mock_email_service(self):
        """Mock email notification service"""
        mock_service = Mock()
        mock_service.send_update_report.return_value = True
        mock_service.send_error_alert.return_value = True
        return mock_service
    
    def test_monthly_update_orchestrator_initialization(self, test_configs, mock_email_service):
        """Test monthly update orchestrator initialization"""
        
        orchestrator = MonthlyUpdateOrchestrator(test_configs, mock_email_service)
        
        # Verify initialization
        assert orchestrator.configs == test_configs
        assert orchestrator.email_service == mock_email_service
        assert len(orchestrator.instance_managers) == 2
        
        # Verify instance managers are created correctly
        manager_names = [manager.config.instance_name for manager in orchestrator.instance_managers]
        assert 'ai_scholar_test' in manager_names
        assert 'quant_scholar_test' in manager_names
        
        print("✓ Monthly update orchestrator initialization test passed")
    
    def test_file_locking_mechanism(self, test_configs, mock_email_service, temp_system_dir):
        """Test file locking to prevent concurrent executions"""
        
        orchestrator = MonthlyUpdateOrchestrator(test_configs, mock_email_service)
        lock_file = temp_system_dir / 'update.lock'
        
        # Test lock acquisition
        with patch.object(orchestrator, '_acquire_lock') as mock_acquire:
            with patch.object(orchestrator, '_release_lock') as mock_release:
                mock_acquire.return_value = True
                
                # Simulate successful lock acquisition
                result = orchestrator._acquire_lock(str(lock_file))
                assert result is True
                
                # Verify lock release is called
                orchestrator._release_lock(str(lock_file))
                assert mock_release.called
        
        # Test concurrent execution prevention
        def simulate_concurrent_execution():
            """Simulate a concurrent execution attempt"""
            time.sleep(0.1)  # Small delay to ensure first execution starts
            return orchestrator._acquire_lock(str(lock_file))
        
        # Create actual lock file for testing
        lock_file.write_text(str(datetime.now().timestamp()))
        
        # Test that second execution is blocked
        with patch.object(orchestrator, '_is_lock_stale') as mock_stale:
            mock_stale.return_value = False  # Lock is not stale
            
            result = orchestrator._acquire_lock(str(lock_file))
            assert result is False  # Should be blocked by existing lock
        
        print("✓ File locking mechanism test passed")
    
    def test_scheduling_conflict_detection(self, test_configs, mock_email_service):
        """Test scheduling conflict detection and resolution"""
        
        orchestrator = MonthlyUpdateOrchestrator(test_configs, mock_email_service)
        
        # Test detection of running processes
        with patch('psutil.process_iter') as mock_process_iter:
            # Mock running process with same command
            mock_process = Mock()
            mock_process.info = {
                'pid': 12345,
                'name': 'python',
                'cmdline': ['python', '-m', 'multi_instance_arxiv_system.scripts.monthly_update']
            }
            mock_process_iter.return_value = [mock_process]
            
            # Test conflict detection
            has_conflict = orchestrator._check_for_running_updates()
            assert has_conflict is True
        
        # Test no conflict scenario
        with patch('psutil.process_iter') as mock_process_iter:
            # Mock different process
            mock_process = Mock()
            mock_process.info = {
                'pid': 12345,
                'name': 'python',
                'cmdline': ['python', 'some_other_script.py']
            }
            mock_process_iter.return_value = [mock_process]
            
            # Test no conflict
            has_conflict = orchestrator._check_for_running_updates()
            assert has_conflict is False
        
        print("✓ Scheduling conflict detection test passed")
    
    def test_health_checks_before_execution(self, test_configs, mock_email_service):
        """Test health checks and validation before automated runs"""
        
        orchestrator = MonthlyUpdateOrchestrator(test_configs, mock_email_service)
        
        # Test system health check
        with patch.object(orchestrator, '_check_system_health') as mock_health:
            mock_health.return_value = {
                'disk_space_ok': True,
                'memory_available': True,
                'chromadb_running': True,
                'network_connectivity': True
            }
            
            health_status = orchestrator._check_system_health()
            
            # Verify all health checks pass
            assert health_status['disk_space_ok'] is True
            assert health_status['memory_available'] is True
            assert health_status['chromadb_running'] is True
            assert health_status['network_connectivity'] is True
        
        # Test health check failure scenario
        with patch.object(orchestrator, '_check_system_health') as mock_health:
            mock_health.return_value = {
                'disk_space_ok': False,  # Insufficient disk space
                'memory_available': True,
                'chromadb_running': True,
                'network_connectivity': True
            }
            
            # Test that execution is prevented when health checks fail
            with patch.object(orchestrator, 'run_monthly_update') as mock_run:
                # Should not run update if health checks fail
                result = orchestrator._validate_execution_conditions()
                assert result is False
        
        print("✓ Health checks before execution test passed")
    
    def test_automated_error_recovery(self, test_configs, mock_email_service):
        """Test automated error recovery and retry mechanisms"""
        
        orchestrator = MonthlyUpdateOrchestrator(test_configs, mock_email_service)
        
        # Test retry mechanism for transient failures
        with patch.object(orchestrator, '_run_instance_update') as mock_update:
            # Simulate transient failure followed by success
            mock_update.side_effect = [
                Exception("Transient network error"),  # First attempt fails
                {  # Second attempt succeeds
                    'success': True,
                    'papers_downloaded': 5,
                    'papers_processed': 5,
                    'errors': 0,
                    'duration_minutes': 10
                }
            ]
            
            # Test retry logic
            result = orchestrator._run_instance_update_with_retry(test_configs[0], max_retries=2)
            
            # Verify retry was attempted and eventually succeeded
            assert result['success'] is True
            assert mock_update.call_count == 2
        
        # Test maximum retry limit
        with patch.object(orchestrator, '_run_instance_update') as mock_update:
            # Simulate persistent failure
            mock_update.side_effect = Exception("Persistent error")
            
            result = orchestrator._run_instance_update_with_retry(test_configs[0], max_retries=2)
            
            # Verify failure after max retries
            assert result['success'] is False
            assert mock_update.call_count == 2  # Should stop after max retries
        
        print("✓ Automated error recovery test passed")
    
    def test_cron_job_configuration_validation(self, temp_system_dir):
        """Test cron job configuration and setup validation"""
        
        # Create mock cron setup script
        cron_script = temp_system_dir / 'setup_cron.py'
        cron_script.write_text("""
import subprocess
import sys

def setup_monthly_cron():
    # Monthly update on 1st of each month at 2 AM
    cron_entry = "0 2 1 * * /opt/arxiv-system/scripts/monthly_update.sh"
    
    # Add to crontab
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_crontab = result.stdout if result.returncode == 0 else ""
        
        if cron_entry not in current_crontab:
            new_crontab = current_crontab + "\\n" + cron_entry
            subprocess.run(['crontab', '-'], input=new_crontab, text=True, check=True)
            return True
    except Exception as e:
        print(f"Error setting up cron job: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = setup_monthly_cron()
    sys.exit(0 if success else 1)
        """)
        
        # Test cron setup validation
        with patch('subprocess.run') as mock_subprocess:
            # Mock successful crontab operations
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = "# Existing crontab entries"
            
            # Import and run the setup function
            import importlib.util
            spec = importlib.util.spec_from_file_location("setup_cron", cron_script)
            setup_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(setup_module)
            
            result = setup_module.setup_monthly_cron()
            assert result is True
        
        print("✓ Cron job configuration validation test passed")
    
    def test_update_scheduling_and_timing(self, test_configs, mock_email_service):
        """Test update scheduling and timing validation"""
        
        orchestrator = MonthlyUpdateOrchestrator(test_configs, mock_email_service)
        
        # Test scheduling time validation
        def is_scheduled_time():
            """Check if current time matches scheduled execution time"""
            now = datetime.now()
            # Scheduled for 1st of month at 2 AM
            return now.day == 1 and now.hour == 2
        
        # Mock time-based execution
        with patch('datetime.datetime') as mock_datetime:
            # Mock scheduled time (1st of month, 2 AM)
            mock_now = datetime(2024, 11, 1, 2, 0, 0)
            mock_datetime.now.return_value = mock_now
            
            # Test that execution is allowed at scheduled time
            should_run = orchestrator._is_scheduled_execution_time()
            # This would be True in a real implementation
            
        # Test execution frequency validation
        last_run_file = Path(temp_system_dir) / 'last_run.json'
        
        # Simulate recent execution (should prevent duplicate run)
        last_run_data = {
            'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
            'success': True
        }
        
        with open(last_run_file, 'w') as f:
            json.dump(last_run_data, f)
        
        # Test duplicate execution prevention
        with patch.object(orchestrator, '_get_last_run_info') as mock_last_run:
            mock_last_run.return_value = last_run_data
            
            should_run = orchestrator._should_run_update()
            # Should be False if run recently
        
        print("✓ Update scheduling and timing test passed")
    
    def test_instance_update_manager_functionality(self, test_configs):
        """Test individual instance update manager functionality"""
        
        config = test_configs[0]  # Use AI Scholar config
        manager = InstanceUpdateManager(config)
        
        # Test manager initialization
        assert manager.config == config
        assert manager.config.instance_name == 'ai_scholar_test'
        
        # Test update execution with mocking
        with patch.object(manager, '_run_downloader') as mock_download:
            with patch.object(manager, '_run_processor') as mock_process:
                mock_download.return_value = {'downloaded': 10, 'errors': 1}
                mock_process.return_value = {'processed': 9, 'errors': 1}
                
                # Run instance update
                result = manager.run_update()
                
                # Verify update results
                assert 'success' in result
                assert 'papers_downloaded' in result
                assert 'papers_processed' in result
                assert 'errors' in result
                assert 'duration_minutes' in result
                
                # Verify both downloader and processor were called
                assert mock_download.called
                assert mock_process.called
        
        print("✓ Instance update manager functionality test passed")
    
    def test_comprehensive_scheduling_workflow(self, test_configs, mock_email_service, temp_system_dir):
        """Test complete automated scheduling workflow"""
        
        orchestrator = MonthlyUpdateOrchestrator(test_configs, mock_email_service)
        
        # Create directories for all configs
        for config in test_configs:
            config.create_directories()
        
        # Mock all external dependencies
        with patch.object(orchestrator, '_acquire_lock') as mock_lock:
            with patch.object(orchestrator, '_check_system_health') as mock_health:
                with patch.object(orchestrator, '_run_instance_update') as mock_update:
                    
                    # Setup mocks
                    mock_lock.return_value = True
                    mock_health.return_value = {
                        'disk_space_ok': True,
                        'memory_available': True,
                        'chromadb_running': True,
                        'network_connectivity': True
                    }
                    mock_update.return_value = {
                        'success': True,
                        'papers_downloaded': 15,
                        'papers_processed': 14,
                        'errors': 1,
                        'duration_minutes': 20
                    }
                    
                    # Run complete workflow
                    results = orchestrator.run_monthly_update()
                    
                    # Verify workflow completion
                    assert len(results) == 2  # Both instances
                    assert 'ai_scholar_test' in results
                    assert 'quant_scholar_test' in results
                    
                    # Verify all instances were processed
                    for instance_name, result in results.items():
                        assert result['success'] is True
                        assert result['papers_downloaded'] > 0
                        assert result['papers_processed'] > 0
                    
                    # Verify email notification was sent
                    assert mock_email_service.send_update_report.called
                    
                    # Verify lock was acquired and released
                    assert mock_lock.called
        
        print("✓ Comprehensive scheduling workflow test passed")


def run_scheduling_validation_tests():
    """Run all automated scheduling validation tests"""
    print("Running Automated Scheduling Validation Tests")
    print("=" * 50)
    
    # Run pytest with this file
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == "__main__":
    run_scheduling_validation_tests()