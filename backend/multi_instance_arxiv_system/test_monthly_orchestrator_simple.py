#!/usr/bin/env python3
"""
Simple test for Monthly Update Orchestrator functionality.
Tests the orchestration system without requiring actual downloads or processing.
"""

import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_orchestration_config():
    """Test OrchestrationConfig functionality."""
    try:
        from multi_instance_arxiv_system.scheduling.monthly_update_orchestrator import OrchestrationConfig
        
        logger.info("=== Testing OrchestrationConfig ===")
        
        # Test default configuration
        config = OrchestrationConfig()
        assert config.max_concurrent_instances == 2, "Default max_concurrent_instances should be 2"
        assert config.instance_timeout_hours == 12, "Default timeout should be 12 hours"
        assert config.retry_failed_instances == True, "Should retry failed instances by default"
        
        logger.info("   ✓ Default configuration created successfully")
        
        # Test custom configuration
        custom_config = OrchestrationConfig(
            max_concurrent_instances=4,
            instance_timeout_hours=6,
            retry_failed_instances=False,
            max_retry_attempts=1,
            cleanup_old_reports=False
        )
        
        assert custom_config.max_concurrent_instances == 4, "Custom max_concurrent_instances should be 4"
        assert custom_config.instance_timeout_hours == 6, "Custom timeout should be 6 hours"
        assert custom_config.retry_failed_instances == False, "Custom retry should be False"
        
        logger.info("   ✓ Custom configuration created successfully")
        
        # Test serialization
        config_dict = custom_config.to_dict()
        assert isinstance(config_dict, dict), "Should serialize to dictionary"
        assert config_dict['max_concurrent_instances'] == 4, "Serialized config should match"
        
        logger.info("   ✓ Configuration serialization works")
        
        return True
        
    except Exception as e:
        logger.error(f"OrchestrationConfig test failed: {e}")
        return False

def test_file_lock():
    """Test FileLock functionality."""
    try:
        from multi_instance_arxiv_system.scheduling.monthly_update_orchestrator import FileLock
        
        logger.info("=== Testing FileLock ===")
        
        # Create temporary lock file path
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_path = Path(temp_dir) / "test.lock"
            
            # Test lock acquisition
            lock = FileLock(str(lock_path))
            success = lock.acquire()
            assert success == True, "Should acquire lock successfully"
            assert lock.locked == True, "Lock should be marked as locked"
            
            logger.info("   ✓ Lock acquisition works")
            
            # Test lock file creation
            assert lock_path.exists(), "Lock file should exist"
            
            logger.info("   ✓ Lock file created")
            
            # Test lock release
            lock.release()
            assert lock.locked == False, "Lock should be marked as unlocked"
            assert not lock_path.exists(), "Lock file should be removed"
            
            logger.info("   ✓ Lock release works")
            
            # Test context manager
            with FileLock(str(lock_path)) as context_lock:
                assert lock_path.exists(), "Lock file should exist in context"
            
            assert not lock_path.exists(), "Lock file should be removed after context"
            
            logger.info("   ✓ Context manager works")
        
        return True
        
    except Exception as e:
        logger.error(f"FileLock test failed: {e}")
        return False

def test_orchestration_result():
    """Test OrchestrationResult functionality."""
    try:
        from multi_instance_arxiv_system.scheduling.monthly_update_orchestrator import OrchestrationResult
        
        logger.info("=== Testing OrchestrationResult ===")
        
        # Create test result
        result = OrchestrationResult(
            orchestration_id="test_orchestration_123",
            start_time=datetime.now()
        )
        
        assert result.orchestration_id == "test_orchestration_123", "Should set orchestration ID"
        assert result.start_time is not None, "Should have start time"
        assert result.end_time is None, "Should not have end time initially"
        
        logger.info("   ✓ OrchestrationResult created successfully")
        
        # Test properties before completion
        assert result.duration_seconds is None, "Duration should be None before completion"
        assert result.success_rate == 0.0, "Success rate should be 0 with no instances"
        
        logger.info("   ✓ Properties work correctly before completion")
        
        # Add some mock data
        result.failed_instances = ["instance1"]
        result.total_papers_processed = 100
        result.total_errors = 5
        
        # Complete the orchestration
        result.end_time = datetime.now()
        
        # Test properties after completion
        assert result.duration_seconds is not None, "Duration should be available after completion"
        assert result.duration_seconds >= 0, "Duration should be non-negative"
        
        logger.info("   ✓ Properties work correctly after completion")
        
        # Test serialization
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict), "Should serialize to dictionary"
        assert result_dict['orchestration_id'] == "test_orchestration_123", "Should preserve orchestration ID"
        assert result_dict['total_papers_processed'] == 100, "Should preserve paper count"
        
        logger.info("   ✓ Serialization works")
        
        return True
        
    except Exception as e:
        logger.error(f"OrchestrationResult test failed: {e}")
        return False

def test_cron_scheduler():
    """Test CronScheduler functionality."""
    try:
        from multi_instance_arxiv_system.scheduling.cron_scheduler import CronScheduler, CronJobConfig
        
        logger.info("=== Testing CronScheduler ===")
        
        # Create temporary config file
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "cron_config.json"
            
            # Test scheduler creation
            scheduler = CronScheduler(str(config_file))
            assert len(scheduler.jobs) == 0, "Should start with no jobs"
            
            logger.info("   ✓ CronScheduler created successfully")
            
            # Test job creation
            job = CronJobConfig(
                name="test_job",
                schedule="0 2 1 * *",
                command="echo 'test'",
                description="Test job"
            )
            
            assert job.name == "test_job", "Should set job name"
            assert job.schedule == "0 2 1 * *", "Should set schedule"
            assert job.enabled == True, "Should be enabled by default"
            
            logger.info("   ✓ CronJobConfig created successfully")
            
            # Test schedule validation
            assert scheduler.validate_schedule("0 2 1 * *") == True, "Valid schedule should pass"
            assert scheduler.validate_schedule("invalid") == False, "Invalid schedule should fail"
            assert scheduler.validate_schedule("60 25 32 13 8") == False, "Out of range values should fail"
            
            logger.info("   ✓ Schedule validation works")
            
            # Test adding monthly update job
            success = scheduler.add_monthly_update_job(
                instance_names=["ai_scholar", "quant_scholar"],
                schedule="0 3 1 * *"
            )
            assert success == True, "Should add monthly update job successfully"
            assert len(scheduler.jobs) == 1, "Should have one job"
            
            logger.info("   ✓ Monthly update job added successfully")
            
            # Test job listing
            jobs = scheduler.list_cron_jobs()
            assert len(jobs) == 1, "Should list one job"
            assert jobs[0]['name'] == "monthly_update_all_instances", "Should have correct job name"
            
            logger.info("   ✓ Job listing works")
        
        return True
        
    except Exception as e:
        logger.error(f"CronScheduler test failed: {e}")
        return False

async def test_orchestrator_initialization():
    """Test MonthlyUpdateOrchestrator initialization."""
    try:
        from multi_instance_arxiv_system.scheduling.monthly_update_orchestrator import (
            MonthlyUpdateOrchestrator, OrchestrationConfig
        )
        
        logger.info("=== Testing MonthlyUpdateOrchestrator Initialization ===")
        
        # Test default initialization
        orchestrator = MonthlyUpdateOrchestrator()
        assert orchestrator.orchestration_config is not None, "Should have orchestration config"
        assert orchestrator.state_manager is not None, "Should have state manager"
        assert len(orchestrator.instance_managers) == 0, "Should start with no instance managers"
        
        logger.info("   ✓ Default initialization works")
        
        # Test custom config initialization
        custom_config = OrchestrationConfig(
            max_concurrent_instances=1,
            instance_timeout_hours=6
        )
        
        custom_orchestrator = MonthlyUpdateOrchestrator(orchestration_config=custom_config)
        assert custom_orchestrator.orchestration_config.max_concurrent_instances == 1, "Should use custom config"
        
        logger.info("   ✓ Custom config initialization works")
        
        # Test status methods
        status = orchestrator.get_orchestration_status()
        assert status is None, "Should return None when no orchestration is running"
        
        logger.info("   ✓ Status methods work")
        
        return True
        
    except Exception as e:
        logger.error(f"MonthlyUpdateOrchestrator initialization test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("Starting Monthly Update Orchestrator Tests...")
    
    tests = [
        ("OrchestrationConfig", test_orchestration_config),
        ("FileLock", test_file_lock),
        ("OrchestrationResult", test_orchestration_result),
        ("CronScheduler", test_cron_scheduler),
        ("Orchestrator Initialization", lambda: asyncio.run(test_orchestrator_initialization()))
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            if test_func():
                logger.info(f"✅ {test_name} Test: PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} Test: FAILED")
                failed += 1
        except Exception as e:
            logger.error(f"❌ {test_name} Test: FAILED with exception: {e}")
            failed += 1
    
    logger.info(f"\n--- Test Summary ---")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 All tests passed! Monthly Update Orchestrator is working correctly.")
        return True
    else:
        logger.error("❌ Some tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)