#!/usr/bin/env python3
"""
Basic test for Monthly Update Orchestrator components.
Tests individual components without complex imports.
"""

import sys
import asyncio
import logging
from pathlib import Path
import tempfile

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_basic_imports():
    """Test basic imports work."""
    try:
        logger.info("=== Testing Basic Imports ===")
        
        # Test data models import
        from multi_instance_arxiv_system.shared.multi_instance_data_models import (
            BasePaper, ArxivPaper, JournalPaper, InstanceConfig
        )
        logger.info("   ✓ Data models imported successfully")
        
        # Test orchestrator components import
        from multi_instance_arxiv_system.scheduling.monthly_update_orchestrator import (
            OrchestrationConfig, OrchestrationResult, FileLock
        )
        logger.info("   ✓ Orchestrator components imported successfully")
        
        # Test cron scheduler import
        from multi_instance_arxiv_system.scheduling.cron_scheduler import (
            CronScheduler, CronJobConfig
        )
        logger.info("   ✓ Cron scheduler imported successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Basic imports test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_orchestration_config():
    """Test OrchestrationConfig functionality."""
    try:
        from multi_instance_arxiv_system.scheduling.monthly_update_orchestrator import OrchestrationConfig
        
        logger.info("=== Testing OrchestrationConfig ===")
        
        # Test default configuration
        config = OrchestrationConfig()
        assert config.max_concurrent_instances == 2, "Default max_concurrent_instances should be 2"
        assert config.instance_timeout_hours == 12, "Default timeout should be 12 hours"
        
        logger.info("   ✓ Default configuration works")
        
        # Test custom configuration
        custom_config = OrchestrationConfig(
            max_concurrent_instances=4,
            instance_timeout_hours=6
        )
        
        assert custom_config.max_concurrent_instances == 4, "Custom max_concurrent_instances should be 4"
        assert custom_config.instance_timeout_hours == 6, "Custom timeout should be 6 hours"
        
        logger.info("   ✓ Custom configuration works")
        
        # Test serialization
        config_dict = custom_config.to_dict()
        assert isinstance(config_dict, dict), "Should serialize to dictionary"
        
        logger.info("   ✓ Configuration serialization works")
        
        return True
        
    except Exception as e:
        logger.error(f"OrchestrationConfig test failed: {e}")
        import traceback
        traceback.print_exc()
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
            
            logger.info("   ✓ Lock acquisition works")
            
            # Test lock release
            lock.release()
            assert lock.locked == False, "Lock should be marked as unlocked"
            
            logger.info("   ✓ Lock release works")
        
        return True
        
    except Exception as e:
        logger.error(f"FileLock test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cron_job_config():
    """Test CronJobConfig functionality."""
    try:
        from multi_instance_arxiv_system.scheduling.cron_scheduler import CronJobConfig
        
        logger.info("=== Testing CronJobConfig ===")
        
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
        
        # Test serialization
        job_dict = job.to_dict()
        assert isinstance(job_dict, dict), "Should serialize to dictionary"
        assert job_dict['name'] == "test_job", "Should preserve name"
        
        logger.info("   ✓ CronJobConfig serialization works")
        
        # Test deserialization
        job2 = CronJobConfig.from_dict(job_dict)
        assert job2.name == job.name, "Should deserialize correctly"
        assert job2.schedule == job.schedule, "Should preserve schedule"
        
        logger.info("   ✓ CronJobConfig deserialization works")
        
        return True
        
    except Exception as e:
        logger.error(f"CronJobConfig test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    logger.info("Starting Basic Monthly Update Orchestrator Tests...")
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("OrchestrationConfig", test_orchestration_config),
        ("FileLock", test_file_lock),
        ("CronJobConfig", test_cron_job_config)
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
        logger.info("🎉 All tests passed! Monthly Update Orchestrator components are working correctly.")
        return True
    else:
        logger.error("❌ Some tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)