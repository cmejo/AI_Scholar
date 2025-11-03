#!/usr/bin/env python3
"""
Simple test for Scheduling System functionality.
Tests the automated scheduling and monitoring components.
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

def test_health_checker():
    """Test HealthChecker functionality."""
    try:
        from multi_instance_arxiv_system.scheduling.health_checker import HealthChecker, HealthCheckResult
        
        logger.info("=== Testing HealthChecker ===")
        
        # Test health checker initialization
        health_checker = HealthChecker()
        assert health_checker is not None, "Health checker should initialize"
        assert len(health_checker.checks) > 0, "Should have health checks defined"
        
        logger.info("   ✓ HealthChecker initialized successfully")
        
        # Test health check result creation
        result = HealthCheckResult(
            check_name="test_check",
            status="healthy",
            message="Test message"
        )
        
        assert result.check_name == "test_check", "Should set check name"
        assert result.status == "healthy", "Should set status"
        
        # Test serialization
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict), "Should serialize to dictionary"
        assert result_dict['check_name'] == "test_check", "Should preserve check name"
        
        logger.info("   ✓ HealthCheckResult works correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"HealthChecker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_recovery_manager():
    """Test ErrorRecoveryManager functionality."""
    try:
        from multi_instance_arxiv_system.scheduling.error_recovery_manager import (
            ErrorRecoveryManager, RecoveryConfig, ErrorPattern, ErrorSeverity, RecoveryStrategy
        )
        
        logger.info("=== Testing ErrorRecoveryManager ===")
        
        # Test recovery config
        config = RecoveryConfig(
            max_retry_attempts=2,
            base_delay_seconds=0.1
        )
        
        assert config.max_retry_attempts == 2, "Should set retry attempts"
        assert config.base_delay_seconds == 0.1, "Should set delay"
        
        logger.info("   ✓ RecoveryConfig works correctly")
        
        # Test error recovery manager
        recovery_manager = ErrorRecoveryManager(config)
        assert recovery_manager is not None, "Should initialize"
        assert len(recovery_manager.error_patterns) > 0, "Should have error patterns"
        
        logger.info("   ✓ ErrorRecoveryManager initialized successfully")
        
        # Test error pattern matching
        pattern = ErrorPattern(
            error_type="TestError",
            error_message_pattern="test",
            severity=ErrorSeverity.LOW,
            recommended_strategy=RecoveryStrategy.IMMEDIATE_RETRY
        )
        
        test_error = Exception("This is a test error")
        matches = pattern.matches(test_error)
        assert matches == True, "Should match test error"
        
        logger.info("   ✓ Error pattern matching works")
        
        return True
        
    except Exception as e:
        logger.error(f"ErrorRecoveryManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_conflict_resolver():
    """Test ConflictResolver functionality."""
    try:
        from multi_instance_arxiv_system.scheduling.conflict_resolver import (
            ConflictResolver, ConflictInfo, ConflictType, ConflictSeverity
        )
        
        logger.info("=== Testing ConflictResolver ===")
        
        # Test with temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            resolver = ConflictResolver(lock_directory=temp_dir)
            assert resolver is not None, "Should initialize"
            assert resolver.lock_directory.exists(), "Lock directory should exist"
            
            logger.info("   ✓ ConflictResolver initialized successfully")
            
            # Test conflict info
            conflict = ConflictInfo(
                conflict_type=ConflictType.PROCESS_OVERLAP,
                severity=ConflictSeverity.MEDIUM,
                description="Test conflict"
            )
            
            assert conflict.conflict_type == ConflictType.PROCESS_OVERLAP, "Should set conflict type"
            assert conflict.severity == ConflictSeverity.MEDIUM, "Should set severity"
            
            # Test serialization
            conflict_dict = conflict.to_dict()
            assert isinstance(conflict_dict, dict), "Should serialize to dictionary"
            
            logger.info("   ✓ ConflictInfo works correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"ConflictResolver test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cron_scheduler():
    """Test CronScheduler functionality."""
    try:
        from multi_instance_arxiv_system.scheduling.cron_scheduler import CronScheduler, CronJobConfig
        
        logger.info("=== Testing CronScheduler ===")
        
        # Test with temporary config file
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "test_cron.json"
            
            scheduler = CronScheduler(str(config_file))
            assert scheduler is not None, "Should initialize"
            
            logger.info("   ✓ CronScheduler initialized successfully")
            
            # Test schedule validation
            assert scheduler.validate_schedule("0 2 1 * *") == True, "Valid schedule should pass"
            assert scheduler.validate_schedule("invalid") == False, "Invalid schedule should fail"
            
            logger.info("   ✓ Schedule validation works")
            
            # Test job configuration
            job = CronJobConfig(
                name="test_job",
                schedule="0 2 1 * *",
                command="echo test",
                description="Test job"
            )
            
            assert job.name == "test_job", "Should set job name"
            assert job.enabled == True, "Should be enabled by default"
            
            logger.info("   ✓ CronJobConfig works correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"CronScheduler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_scheduling_coordinator():
    """Test SchedulingCoordinator functionality."""
    try:
        from multi_instance_arxiv_system.scheduling.scheduling_coordinator import (
            SchedulingCoordinator, SchedulingConfig
        )
        
        logger.info("=== Testing SchedulingCoordinator ===")
        
        # Test scheduling config
        config = SchedulingConfig(
            enable_health_checks=True,
            enable_conflict_resolution=True,
            health_check_timeout_minutes=1
        )
        
        assert config.enable_health_checks == True, "Should enable health checks"
        assert config.health_check_timeout_minutes == 1, "Should set timeout"
        
        logger.info("   ✓ SchedulingConfig works correctly")
        
        # Test coordinator initialization
        coordinator = SchedulingCoordinator(scheduling_config=config)
        assert coordinator is not None, "Should initialize"
        assert coordinator.health_checker is not None, "Should have health checker"
        assert coordinator.error_recovery_manager is not None, "Should have error recovery manager"
        
        logger.info("   ✓ SchedulingCoordinator initialized successfully")
        
        # Test environment validation
        is_valid, issues = await coordinator.validate_scheduling_environment()
        logger.info(f"   Environment validation: valid={is_valid}, issues={len(issues)}")
        
        # Test statistics
        stats = coordinator.get_scheduling_statistics()
        assert isinstance(stats, dict), "Should return statistics dictionary"
        assert 'total_executions' in stats, "Should include execution count"
        
        logger.info("   ✓ Statistics and validation work")
        
        return True
        
    except Exception as e:
        logger.error(f"SchedulingCoordinator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    logger.info("Starting Scheduling System Tests...")
    
    tests = [
        ("HealthChecker", test_health_checker),
        ("ErrorRecoveryManager", test_error_recovery_manager),
        ("ConflictResolver", test_conflict_resolver),
        ("CronScheduler", test_cron_scheduler),
        ("SchedulingCoordinator", lambda: asyncio.run(test_scheduling_coordinator()))
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
        logger.info("🎉 All tests passed! Scheduling system is working correctly.")
        return True
    else:
        logger.error("❌ Some tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)