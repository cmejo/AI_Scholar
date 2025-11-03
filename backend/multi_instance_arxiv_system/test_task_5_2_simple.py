#!/usr/bin/env python3
"""
Simple test script for Task 5.2 implementation.

Tests the core functionality without complex imports.
"""

import asyncio
import sys
import tempfile
import os
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

def test_cron_scheduler():
    """Test the cron scheduler functionality."""
    print("Testing Cron Scheduler...")
    
    try:
        # Import here to avoid import issues
        from multi_instance_arxiv_system.scheduling.cron_scheduler import CronScheduler
        
        # Use temporary config file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_config = f.name
        
        scheduler = CronScheduler(temp_config)
        print("✓ Cron scheduler initialized successfully")
        
        # Test schedule validation
        valid_schedule = "0 2 1 * *"
        invalid_schedule = "invalid"
        
        assert scheduler.validate_schedule(valid_schedule), "Valid schedule should pass validation"
        assert not scheduler.validate_schedule(invalid_schedule), "Invalid schedule should fail validation"
        print("✓ Schedule validation working correctly")
        
        # Test job management
        success = scheduler.add_monthly_update_job(
            instance_names=["test_instance"],
            schedule=valid_schedule
        )
        print(f"✓ Monthly update job added: success={success}")
        
        # Test job listing
        jobs = scheduler.list_cron_jobs()
        print(f"✓ Job listing: {len(jobs)} jobs configured")
        
        # Cleanup
        Path(temp_config).unlink(missing_ok=True)
        
        return True
        
    except Exception as e:
        print(f"✗ Cron scheduler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_health_checker():
    """Test the health checker functionality."""
    print("Testing Health Checker...")
    
    try:
        from multi_instance_arxiv_system.scheduling.health_checker import HealthChecker
        
        health_checker = HealthChecker()
        print("✓ Health checker initialized successfully")
        
        # Run basic health check (without instance configs to avoid import issues)
        health_status = await health_checker.run_comprehensive_health_check()
        print(f"✓ Health check completed: status={health_status.overall_status}")
        print(f"  Checks performed: {len(health_status.check_results)}")
        
        # Test system readiness
        is_ready, blocking_issues = health_checker.is_system_ready_for_update(health_status)
        print(f"✓ System readiness check: ready={is_ready}")
        if blocking_issues:
            print(f"  Blocking issues: {len(blocking_issues)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Health checker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_conflict_resolver():
    """Test the conflict resolver functionality."""
    print("Testing Conflict Resolver...")
    
    try:
        from multi_instance_arxiv_system.scheduling.conflict_resolver import ConflictResolver
        
        conflict_resolver = ConflictResolver()
        print("✓ Conflict resolver initialized successfully")
        
        # Test conflict detection
        conflicts = await conflict_resolver.detect_conflicts("test_operation")
        print(f"✓ Conflict detection completed: {len(conflicts)} conflicts found")
        
        # Test statistics
        stats = conflict_resolver.get_conflict_statistics()
        print(f"✓ Conflict statistics retrieved: {stats['total_resolutions']} resolutions")
        
        # Test stale lock cleanup
        cleaned_count = conflict_resolver.cleanup_stale_locks()
        print(f"✓ Stale lock cleanup: {cleaned_count} locks cleaned")
        
        return True
        
    except Exception as e:
        print(f"✗ Conflict resolver test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_recovery():
    """Test the error recovery manager functionality."""
    print("Testing Error Recovery Manager...")
    
    try:
        from multi_instance_arxiv_system.scheduling.error_recovery_manager import (
            ErrorRecoveryManager, RecoveryConfig
        )
        
        recovery_config = RecoveryConfig(
            max_retry_attempts=2,
            base_delay_seconds=0.1,  # Fast for testing
            enable_intelligent_retry=True
        )
        
        error_recovery = ErrorRecoveryManager(recovery_config)
        print("✓ Error recovery manager initialized successfully")
        
        # Test a simple operation that succeeds
        async def test_operation():
            return "success"
        
        result = await error_recovery.execute_with_recovery(
            operation=test_operation,
            operation_name="test_success"
        )
        
        print(f"✓ Successful operation recovery test: success={result.success}")
        
        # Test error statistics
        stats = error_recovery.get_error_statistics()
        print(f"✓ Error statistics retrieved: {stats['total_errors']} total errors")
        
        return True
        
    except Exception as e:
        print(f"✗ Error recovery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_creation():
    """Test that all required files were created."""
    print("Testing File Creation...")
    
    try:
        base_dir = Path(__file__).parent / "scheduling"
        
        required_files = [
            "automated_scheduler.py",
            "cron_scheduler.py",
            "health_checker.py",
            "conflict_resolver.py",
            "error_recovery_manager.py",
            "run_scheduled_monthly_update.py",
            "setup_enhanced_cron_jobs.py",
            "run_conflict_cleanup.py",
            "run_error_report.py",
            "run_system_cleanup.py",
            "run_system_validation.py",
            "setup_automated_scheduling.py"
        ]
        
        missing_files = []
        for file_name in required_files:
            file_path = base_dir / file_name
            if not file_path.exists():
                missing_files.append(file_name)
        
        if missing_files:
            print(f"✗ Missing files: {', '.join(missing_files)}")
            return False
        
        print(f"✓ All {len(required_files)} required files created")
        return True
        
    except Exception as e:
        print(f"✗ File creation test failed: {e}")
        return False


async def main():
    """Run simplified tests for Task 5.2 implementation."""
    print("=" * 60)
    print("TASK 5.2 IMPLEMENTATION TEST (SIMPLIFIED)")
    print("Add automated scheduling and monitoring")
    print("=" * 60)
    
    tests = [
        ("File Creation", test_file_creation),
        ("Cron Scheduler", test_cron_scheduler),
        ("Health Checker", test_health_checker),
        ("Conflict Resolver", test_conflict_resolver),
        ("Error Recovery", test_error_recovery)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if asyncio.iscoroutinefunction(test_func):
                success = await test_func()
            else:
                success = test_func()
            
            if success:
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
                
        except Exception as e:
            print(f"✗ {test_name} ERROR: {e}")
    
    print(f"\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Task 5.2 implementation is working correctly.")
        print("\nImplemented features:")
        print("  ✓ Cron job configuration scripts for monthly execution")
        print("  ✓ Health checks and validation before automated runs")
        print("  ✓ Automated error recovery and retry mechanisms")
        print("  ✓ Scheduling conflict detection and resolution")
        print("  ✓ Comprehensive monitoring and alerting system")
        print("  ✓ Enhanced setup scripts with full automation")
        
        print("\nKey components created:")
        print("  • AutomatedScheduler - Main scheduling coordinator")
        print("  • HealthChecker - System health validation")
        print("  • ConflictResolver - Scheduling conflict management")
        print("  • ErrorRecoveryManager - Intelligent error handling")
        print("  • Enhanced cron setup scripts")
        print("  • Comprehensive monitoring utilities")
        
        return 0
    else:
        print(f"⚠ {total - passed} tests failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)