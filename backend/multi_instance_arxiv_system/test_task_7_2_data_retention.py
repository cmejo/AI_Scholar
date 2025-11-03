#!/usr/bin/env python3
"""
Test for Task 7.2: Data Retention and Cleanup System functionality.

Tests the DataRetentionManager with configurable policies, automated cleanup
recommendations and execution, data archival and compression capabilities,
and storage optimization and defragmentation.
"""

import sys
import asyncio
import tempfile
import logging
import os
import time
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_data_retention_manager_creation():
    """Test DataRetentionManager creation and initialization."""
    try:
        from multi_instance_arxiv_system.storage.data_retention_manager import (
            DataRetentionManager, RetentionPolicy, RetentionRule, 
            RetentionAction, RetentionPriority
        )
        
        logger.info("=== Testing DataRetentionManager Creation ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create data retention manager
            retention_manager = DataRetentionManager(
                database_path=os.path.join(temp_dir, "retention.db"),
                archive_base_path=os.path.join(temp_dir, "archives")
            )
            
            assert retention_manager is not None, "Should create DataRetentionManager"
            assert len(retention_manager.policies) > 0, "Should have default policies"
            
            logger.info(f"   ✓ DataRetentionManager created with {len(retention_manager.policies)} policies")
            
            # Test policy management
            test_policy = RetentionPolicy(
                name="test_policy",
                description="Test policy for unit testing"
            )
            
            test_rule = RetentionRule(
                name="test_rule",
                pattern="*.test",
                max_age_days=30,
                action=RetentionAction.DELETE,
                priority=RetentionPriority.HIGH
            )
            
            test_policy.add_rule(test_rule)
            
            # Add policy
            success = retention_manager.add_policy(test_policy)
            assert success, "Should successfully add policy"
            assert "test_policy" in retention_manager.policies, "Policy should be in manager"
            
            logger.info("   ✓ Policy management working correctly")
            
            # Test policy removal
            success = retention_manager.remove_policy("test_policy")
            assert success, "Should successfully remove policy"
            assert "test_policy" not in retention_manager.policies, "Policy should be removed"
            
            logger.info("   ✓ Policy removal working correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"DataRetentionManager creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_retention_rules_and_policies():
    """Test retention rules and policy functionality."""
    try:
        from multi_instance_arxiv_system.storage.data_retention_manager import (
            RetentionRule, RetentionPolicy, RetentionAction, RetentionPriority
        )
        
        logger.info("=== Testing Retention Rules and Policies ===")
        
        # Create test rule
        rule = RetentionRule(
            name="temp_cleanup",
            pattern="*.tmp",
            max_age_days=7,
            action=RetentionAction.DELETE,
            priority=RetentionPriority.HIGH
        )
        
        assert rule.name == "temp_cleanup", "Should set rule name"
        assert rule.pattern == "*.tmp", "Should set pattern"
        assert rule.max_age_days == 7, "Should set max age"
        assert rule.action == RetentionAction.DELETE, "Should set action"
        
        logger.info("   ✓ RetentionRule creation working correctly")
        
        # Test file matching
        test_file = Path("/tmp/test.tmp")
        assert rule.matches_file(test_file), "Should match .tmp files"
        
        non_matching_file = Path("/tmp/test.log")
        assert not rule.matches_file(non_matching_file), "Should not match .log files"
        
        logger.info("   ✓ File pattern matching working correctly")
        
        # Create test policy
        policy = RetentionPolicy(
            name="test_cleanup_policy",
            description="Policy for testing cleanup operations"
        )
        
        policy.add_rule(rule)
        assert len(policy.rules) == 1, "Should have one rule"
        
        # Test policy serialization
        policy_dict = policy.to_dict()
        assert isinstance(policy_dict, dict), "Should serialize to dictionary"
        assert policy_dict['name'] == "test_cleanup_policy", "Should preserve name"
        assert len(policy_dict['rules']) == 1, "Should preserve rules"
        
        logger.info("   ✓ Policy serialization working correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"Retention rules and policies test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_directory_analysis():
    """Test directory analysis and cleanup recommendations."""
    try:
        from multi_instance_arxiv_system.storage.data_retention_manager import (
            DataRetentionManager, RetentionPolicy, RetentionRule, 
            RetentionAction, RetentionPriority
        )
        
        logger.info("=== Testing Directory Analysis ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create retention manager
            retention_manager = DataRetentionManager(
                database_path=os.path.join(temp_dir, "retention.db"),
                archive_base_path=os.path.join(temp_dir, "archives")
            )
            
            # Create test directory structure
            test_dir = Path(temp_dir) / "test_data"
            test_dir.mkdir()
            
            # Create test files with different ages
            old_file = test_dir / "old_file.tmp"
            recent_file = test_dir / "recent_file.tmp"
            log_file = test_dir / "test.log"
            
            # Create files
            old_file.write_text("old temporary file")
            recent_file.write_text("recent temporary file")
            log_file.write_text("log file content")
            
            # Modify timestamps to simulate age
            old_time = time.time() - (10 * 24 * 60 * 60)  # 10 days ago
            recent_time = time.time() - (2 * 24 * 60 * 60)  # 2 days ago
            
            os.utime(old_file, (old_time, old_time))
            os.utime(recent_file, (recent_time, recent_time))
            
            logger.info(f"   ✓ Created test files: {len(list(test_dir.iterdir()))} files")
            
            # Add custom policy for testing
            test_policy = RetentionPolicy(
                name="test_analysis_policy",
                description="Policy for testing directory analysis"
            )
            
            # Rule to delete old temp files
            temp_rule = RetentionRule(
                name="old_temp_delete",
                pattern="*.tmp",
                max_age_days=5,
                action=RetentionAction.DELETE,
                priority=RetentionPriority.HIGH
            )
            
            test_policy.add_rule(temp_rule)
            retention_manager.add_policy(test_policy)
            
            # Analyze directory
            recommendations = await retention_manager.analyze_directory(str(test_dir))
            
            assert isinstance(recommendations, list), "Should return list of recommendations"
            logger.info(f"   ✓ Generated {len(recommendations)} cleanup recommendations")
            
            # Should recommend deleting the old temp file
            old_file_recommendations = [
                r for r in recommendations 
                if r.file_path == str(old_file)
            ]
            
            assert len(old_file_recommendations) > 0, "Should recommend cleaning old temp file"
            assert old_file_recommendations[0].action == RetentionAction.DELETE, "Should recommend deletion"
            
            logger.info("   ✓ Directory analysis working correctly")
            
            # Test recommendation details
            for rec in recommendations[:3]:  # Show first 3
                logger.info(f"     - {rec.action.value}: {Path(rec.file_path).name} ")
                logger.info(f"       ({rec.estimated_space_savings_mb:.3f}MB, {rec.priority.name})")
        
        return True
        
    except Exception as e:
        logger.error(f"Directory analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_cleanup_execution():
    """Test cleanup execution with different actions."""
    try:
        from multi_instance_arxiv_system.storage.data_retention_manager import (
            DataRetentionManager, RetentionPolicy, RetentionRule, 
            RetentionAction, RetentionPriority, CleanupRecommendation
        )
        
        logger.info("=== Testing Cleanup Execution ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create retention manager
            retention_manager = DataRetentionManager(
                database_path=os.path.join(temp_dir, "retention.db"),
                archive_base_path=os.path.join(temp_dir, "archives")
            )
            
            # Create test files
            test_dir = Path(temp_dir) / "cleanup_test"
            test_dir.mkdir()
            
            delete_file = test_dir / "delete_me.tmp"
            archive_file = test_dir / "archive_me.log"
            compress_file = test_dir / "compress_me.txt"
            
            delete_file.write_text("file to delete")
            archive_file.write_text("file to archive")
            compress_file.write_text("file to compress")
            
            logger.info(f"   ✓ Created {len(list(test_dir.iterdir()))} test files")
            
            # Create manual recommendations
            recommendations = [
                CleanupRecommendation(
                    file_path=str(delete_file),
                    action=RetentionAction.DELETE,
                    rule_name="test_delete",
                    estimated_space_savings_mb=0.001,
                    priority=RetentionPriority.HIGH,
                    reason="Test deletion"
                ),
                CleanupRecommendation(
                    file_path=str(archive_file),
                    action=RetentionAction.ARCHIVE,
                    rule_name="test_archive",
                    estimated_space_savings_mb=0.001,
                    priority=RetentionPriority.NORMAL,
                    reason="Test archival"
                ),
                CleanupRecommendation(
                    file_path=str(compress_file),
                    action=RetentionAction.COMPRESS,
                    rule_name="test_compress",
                    estimated_space_savings_mb=0.001,
                    priority=RetentionPriority.LOW,
                    reason="Test compression"
                )
            ]
            
            # Test dry run first
            dry_result = await retention_manager.execute_cleanup(recommendations, dry_run=True)
            
            assert dry_result.total_files_processed == 3, "Should process all files in dry run"
            assert len(dry_result.errors) == 0, "Should have no errors in dry run"
            assert dry_result.execution_time_seconds > 0, "Should track execution time"
            
            # Files should still exist after dry run
            assert delete_file.exists(), "File should exist after dry run"
            assert archive_file.exists(), "File should exist after dry run"
            assert compress_file.exists(), "File should exist after dry run"
            
            logger.info(f"   ✓ Dry run completed: {dry_result.total_files_processed} files processed")
            
            # Test actual execution
            actual_result = await retention_manager.execute_cleanup(recommendations, dry_run=False)
            
            assert actual_result.total_files_processed == 3, "Should process all files"
            logger.info(f"   ✓ Actual cleanup completed: {actual_result.total_files_processed} files processed")
            logger.info(f"     Space freed: {actual_result.total_space_freed_mb:.3f}MB")
            logger.info(f"     Actions: {dict(actual_result.actions_performed)}")
            
            # Verify actions were performed
            assert not delete_file.exists(), "File should be deleted"
            assert not archive_file.exists(), "File should be archived (removed from original location)"
            assert not compress_file.exists(), "File should be compressed (removed from original location)"
            
            # Check compressed file exists
            compressed_file = compress_file.with_suffix(compress_file.suffix + '.gz')
            assert compressed_file.exists(), "Compressed file should exist"
            
            logger.info("   ✓ Cleanup execution working correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"Cleanup execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_archival_and_compression():
    """Test file archival and compression functionality."""
    try:
        from multi_instance_arxiv_system.storage.data_retention_manager import (
            DataRetentionManager
        )
        
        logger.info("=== Testing Archival and Compression ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create retention manager
            retention_manager = DataRetentionManager(
                database_path=os.path.join(temp_dir, "retention.db"),
                archive_base_path=os.path.join(temp_dir, "archives")
            )
            
            # Create test file
            test_file = Path(temp_dir) / "test_archive.txt"
            test_content = "This is test content for archival testing" * 100
            test_file.write_text(test_content)
            
            original_size = test_file.stat().st_size
            logger.info(f"   ✓ Created test file: {original_size} bytes")
            
            # Test archival
            archive_path = await retention_manager._archive_file(test_file, dry_run=False)
            
            assert archive_path is not None, "Should return archive path"
            assert not test_file.exists(), "Original file should be removed"
            assert Path(archive_path).exists(), "Archive file should exist"
            
            logger.info(f"   ✓ File archived to: {Path(archive_path).name}")
            
            # Create another test file for compression
            compress_file = Path(temp_dir) / "test_compress.txt"
            compress_file.write_text(test_content)
            
            # Test compression
            compressed_path = await retention_manager._compress_file(compress_file, dry_run=False)
            
            assert compressed_path is not None, "Should return compressed path"
            assert not compress_file.exists(), "Original file should be removed"
            assert Path(compressed_path).exists(), "Compressed file should exist"
            
            # Check compression ratio
            compressed_size = Path(compressed_path).stat().st_size
            compression_ratio = compressed_size / original_size
            
            logger.info(f"   ✓ File compressed: {original_size} -> {compressed_size} bytes ")
            logger.info(f"     (ratio: {compression_ratio:.2f})")
            
            assert compression_ratio < 1.0, "Compressed file should be smaller"
        
        return True
        
    except Exception as e:
        logger.error(f"Archival and compression test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_persistence():
    """Test database persistence of policies and cleanup history."""
    try:
        from multi_instance_arxiv_system.storage.data_retention_manager import (
            DataRetentionManager, RetentionPolicy, RetentionRule, 
            RetentionAction, RetentionPriority
        )
        
        logger.info("=== Testing Database Persistence ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "persistence_test.db")
            
            # Create first manager instance
            manager1 = DataRetentionManager(
                database_path=db_path,
                archive_base_path=os.path.join(temp_dir, "archives")
            )
            
            # Add custom policy
            test_policy = RetentionPolicy(
                name="persistence_test_policy",
                description="Policy for testing persistence"
            )
            
            test_rule = RetentionRule(
                name="persistence_rule",
                pattern="*.persist",
                max_age_days=15,
                action=RetentionAction.ARCHIVE,
                priority=RetentionPriority.NORMAL
            )
            
            test_policy.add_rule(test_rule)
            success = manager1.add_policy(test_policy)
            assert success, "Should add policy successfully"
            
            initial_policy_count = len(manager1.policies)
            logger.info(f"   ✓ First manager has {initial_policy_count} policies")
            
            # Create second manager instance (should load from database)
            manager2 = DataRetentionManager(
                database_path=db_path,
                archive_base_path=os.path.join(temp_dir, "archives")
            )
            
            # Check if policy was loaded
            assert len(manager2.policies) == initial_policy_count, "Should load same number of policies"
            assert "persistence_test_policy" in manager2.policies, "Should load custom policy"
            
            loaded_policy = manager2.policies["persistence_test_policy"]
            assert loaded_policy.name == "persistence_test_policy", "Should preserve policy name"
            assert len(loaded_policy.rules) == 1, "Should preserve rules"
            assert loaded_policy.rules[0].pattern == "*.persist", "Should preserve rule details"
            
            logger.info("   ✓ Database persistence working correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"Database persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration_with_storage_monitor():
    """Test integration with storage monitoring system."""
    try:
        from multi_instance_arxiv_system.storage.data_retention_manager import (
            DataRetentionManager
        )
        from multi_instance_arxiv_system.storage.storage_monitor import (
            StorageMonitor, StorageDataType
        )
        
        logger.info("=== Testing Integration with Storage Monitor ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create storage monitor
            storage_monitor = StorageMonitor(
                database_path=os.path.join(temp_dir, "storage_monitor.db"),
                monitoring_interval=1
            )
            
            # Create retention manager
            retention_manager = DataRetentionManager(
                database_path=os.path.join(temp_dir, "integration.db"),
                archive_base_path=os.path.join(temp_dir, "archives")
            )
            
            # Create test data structure
            test_data_dir = Path(temp_dir) / "test_instance" / "processed"
            test_data_dir.mkdir(parents=True)
            
            # Create some test files
            for i in range(5):
                test_file = test_data_dir / f"processed_data_{i}.json"
                test_file.write_text(f'{{"data": "test content {i}"}}')
            
            logger.info(f"   ✓ Created test data structure with {len(list(test_data_dir.iterdir()))} files")
            
            # Get storage usage
            storage_stats = storage_monitor.get_current_stats()
            assert storage_stats is not None, "Should get storage stats"
            
            logger.info(f"   ✓ Storage stats: {storage_stats.total_storage_gb:.2f}GB total")
            
            # Analyze directory for cleanup
            recommendations = await retention_manager.analyze_directory(
                str(test_data_dir),
                data_type=StorageDataType.PROCESSED_DATA
            )
            
            logger.info(f"   ✓ Generated {len(recommendations)} recommendations for processed data")
            
            # Test that the systems work together
            assert isinstance(recommendations, list), "Should return recommendations"
            
            logger.info("   ✓ Integration with storage monitor working correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all data retention and cleanup tests."""
    logger.info("Starting Task 7.2 Data Retention and Cleanup System Tests...")
    
    tests = [
        ("DataRetentionManager Creation", test_data_retention_manager_creation),
        ("Retention Rules and Policies", test_retention_rules_and_policies),
        ("Directory Analysis", test_directory_analysis),
        ("Cleanup Execution", test_cleanup_execution),
        ("Archival and Compression", test_archival_and_compression),
        ("Database Persistence", test_database_persistence),
        ("Integration with Storage Monitor", test_integration_with_storage_monitor)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
                
            if result:
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
        logger.info("🎉 All tests passed! Data Retention and Cleanup System is working correctly.")
        return True
    else:
        logger.error("❌ Some tests failed.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)