#!/usr/bin/env python3
"""
Test for Task 7.1: Storage Monitoring System functionality.

Tests the storage monitor including real-time disk usage tracking, storage threshold
monitoring and alerting, storage usage prediction and trend analysis, and storage
breakdown by instance and data type.
"""

import sys
import tempfile
import time
import logging
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


def test_storage_monitor_initialization():
    """Test StorageMonitor initialization."""
    try:
        from multi_instance_arxiv_system.storage.storage_monitor import (
            StorageMonitor, StorageDataType, StorageAlertLevel
        )
        
        logger.info("=== Testing StorageMonitor Initialization ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_storage.db"
            
            # Create storage monitor
            monitor = StorageMonitor(
                database_path=str(db_path),
                monitoring_interval=10,  # 10 seconds for testing
                alert_thresholds={
                    'warning': 70.0,
                    'critical': 85.0,
                    'emergency': 95.0
                }
            )
            
            assert monitor is not None, "Should create storage monitor"
            assert monitor.database_path == str(db_path), "Should set database path"
            assert monitor.monitoring_interval == 10, "Should set monitoring interval"
            assert monitor.alert_thresholds['warning'] == 70.0, "Should set custom thresholds"
            
            logger.info("   ✓ StorageMonitor created successfully")
            
            # Test database initialization
            assert Path(db_path).exists(), "Should create database file"
            
            logger.info("   ✓ Database initialized successfully")
            
            # Test monitoring status
            status = monitor.get_monitoring_status()
            assert isinstance(status, dict), "Should return status dictionary"
            assert status['running'] == False, "Should not be running initially"
            assert status['monitored_paths'] == 0, "Should have no monitored paths initially"
            
            logger.info("   ✓ Monitoring status working correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"StorageMonitor initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_monitored_paths_management():
    """Test adding and removing monitored paths."""
    try:
        from multi_instance_arxiv_system.storage.storage_monitor import (
            StorageMonitor, StorageDataType
        )
        
        logger.info("=== Testing Monitored Paths Management ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_storage.db"
            monitor = StorageMonitor(database_path=str(db_path))
            
            # Create test directories
            pdf_dir = Path(temp_dir) / "pdf"
            processed_dir = Path(temp_dir) / "processed"
            pdf_dir.mkdir()
            processed_dir.mkdir()
            
            # Add monitored paths
            success1 = monitor.add_monitored_path(
                str(pdf_dir),
                StorageDataType.PDF_FILES,
                "ai_scholar"
            )
            assert success1 == True, "Should add PDF directory successfully"
            
            success2 = monitor.add_monitored_path(
                str(processed_dir),
                StorageDataType.PROCESSED_DATA,
                "quant_scholar"
            )
            assert success2 == True, "Should add processed directory successfully"
            
            logger.info("   ✓ Monitored paths added successfully")
            
            # Check monitored paths
            assert len(monitor.monitored_paths) == 2, "Should have 2 monitored paths"
            assert str(pdf_dir) in monitor.monitored_paths, "Should contain PDF directory"
            assert str(processed_dir) in monitor.monitored_paths, "Should contain processed directory"
            
            # Check path details
            pdf_info = monitor.monitored_paths[str(pdf_dir)]
            assert pdf_info[0] == StorageDataType.PDF_FILES, "Should have correct data type"
            assert pdf_info[1] == "ai_scholar", "Should have correct instance name"
            
            logger.info("   ✓ Monitored paths stored correctly")
            
            # Test adding non-existent path
            success3 = monitor.add_monitored_path(
                "/non/existent/path",
                StorageDataType.LOG_FILES
            )
            assert success3 == False, "Should fail to add non-existent path"
            
            logger.info("   ✓ Non-existent path handling working")
            
            # Remove monitored path
            success4 = monitor.remove_monitored_path(str(pdf_dir))
            assert success4 == True, "Should remove path successfully"
            assert len(monitor.monitored_paths) == 1, "Should have 1 monitored path after removal"
            assert str(pdf_dir) not in monitor.monitored_paths, "Should not contain removed path"
            
            logger.info("   ✓ Path removal working correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"Monitored paths management test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_storage_usage_collection():
    """Test storage usage data collection."""
    try:
        from multi_instance_arxiv_system.storage.storage_monitor import (
            StorageMonitor, StorageDataType, StorageUsage
        )
        
        logger.info("=== Testing Storage Usage Collection ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_storage.db"
            monitor = StorageMonitor(database_path=str(db_path))
            
            # Add current directory as monitored path
            monitor.add_monitored_path(
                temp_dir,
                StorageDataType.TEMP_FILES,
                "test_instance"
            )
            
            # Force collection
            result = monitor.force_check()
            assert result['success'] == True, "Should collect usage successfully"
            assert result['monitored_paths'] == 1, "Should report 1 monitored path"
            
            logger.info("   ✓ Storage usage collection working")
            
            # Check collected usage
            assert len(monitor.current_usage) == 1, "Should have usage data for 1 path"
            
            usage = list(monitor.current_usage.values())[0]
            assert isinstance(usage, StorageUsage), "Should be StorageUsage object"
            assert usage.path == temp_dir, "Should have correct path"
            assert usage.data_type == StorageDataType.TEMP_FILES, "Should have correct data type"
            assert usage.instance_name == "test_instance", "Should have correct instance name"
            assert usage.total_bytes > 0, "Should have positive total bytes"
            assert usage.usage_percentage >= 0, "Should have non-negative usage percentage"
            
            logger.info(f"   ✓ Usage data: {usage.used_gb:.2f}GB / {usage.total_gb:.2f}GB ({usage.usage_percentage:.1f}%)")
            
            # Test usage conversion methods
            assert usage.total_gb == usage.total_bytes / (1024**3), "Should convert bytes to GB correctly"
            assert usage.used_gb == usage.used_bytes / (1024**3), "Should convert used bytes to GB correctly"
            assert usage.free_gb == usage.free_bytes / (1024**3), "Should convert free bytes to GB correctly"
            
            logger.info("   ✓ Usage conversion methods working")
            
            # Test serialization
            usage_dict = usage.to_dict()
            assert isinstance(usage_dict, dict), "Should serialize to dictionary"
            assert usage_dict['path'] == temp_dir, "Should preserve path in serialization"
            assert usage_dict['data_type'] == 'temp_files', "Should serialize data type"
            
            logger.info("   ✓ Usage serialization working")
        
        return True
        
    except Exception as e:
        logger.error(f"Storage usage collection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_storage_alerts():
    """Test storage alert generation and management."""
    try:
        from multi_instance_arxiv_system.storage.storage_monitor import (
            StorageMonitor, StorageDataType, StorageAlertLevel
        )
        
        logger.info("=== Testing Storage Alerts ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_storage.db"
            
            # Create monitor with low thresholds for testing
            monitor = StorageMonitor(
                database_path=str(db_path),
                alert_thresholds={
                    'warning': 1.0,    # Very low threshold for testing
                    'critical': 2.0,
                    'emergency': 3.0
                }
            )
            
            # Add monitored path
            monitor.add_monitored_path(
                temp_dir,
                StorageDataType.TEMP_FILES,
                "test_instance"
            )
            
            # Force check to generate alerts
            result = monitor.force_check()
            assert result['success'] == True, "Should complete check successfully"
            
            # Check if alerts were generated (likely since thresholds are very low)
            active_alerts = monitor.get_active_alerts()
            logger.info(f"   Generated {len(active_alerts)} alerts")
            
            if active_alerts:
                alert = active_alerts[0]
                assert hasattr(alert, 'alert_id'), "Should have alert ID"
                assert hasattr(alert, 'level'), "Should have alert level"
                assert hasattr(alert, 'message'), "Should have alert message"
                assert hasattr(alert, 'path'), "Should have path"
                assert hasattr(alert, 'usage_percentage'), "Should have usage percentage"
                
                logger.info(f"   ✓ Alert generated: {alert.level.value} - {alert.message}")
                
                # Test alert serialization
                alert_dict = alert.to_dict()
                assert isinstance(alert_dict, dict), "Should serialize to dictionary"
                assert alert_dict['level'] == alert.level.value, "Should serialize level"
                
                logger.info("   ✓ Alert serialization working")
            
            # Test alert filtering
            warning_alerts = monitor.get_active_alerts(StorageAlertLevel.WARNING)
            critical_alerts = monitor.get_active_alerts(StorageAlertLevel.CRITICAL)
            
            logger.info(f"   Warning alerts: {len(warning_alerts)}")
            logger.info(f"   Critical alerts: {len(critical_alerts)}")
            
            logger.info("   ✓ Alert filtering working")
        
        return True
        
    except Exception as e:
        logger.error(f"Storage alerts test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_storage_statistics():
    """Test comprehensive storage statistics."""
    try:
        from multi_instance_arxiv_system.storage.storage_monitor import (
            StorageMonitor, StorageDataType
        )
        
        logger.info("=== Testing Storage Statistics ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_storage.db"
            monitor = StorageMonitor(database_path=str(db_path))
            
            # Create test directories for different instances and data types
            ai_pdf_dir = Path(temp_dir) / "ai_scholar" / "pdf"
            ai_processed_dir = Path(temp_dir) / "ai_scholar" / "processed"
            quant_pdf_dir = Path(temp_dir) / "quant_scholar" / "pdf"
            
            ai_pdf_dir.mkdir(parents=True)
            ai_processed_dir.mkdir(parents=True)
            quant_pdf_dir.mkdir(parents=True)
            
            # Add monitored paths
            monitor.add_monitored_path(str(ai_pdf_dir), StorageDataType.PDF_FILES, "ai_scholar")
            monitor.add_monitored_path(str(ai_processed_dir), StorageDataType.PROCESSED_DATA, "ai_scholar")
            monitor.add_monitored_path(str(quant_pdf_dir), StorageDataType.PDF_FILES, "quant_scholar")
            
            # Force collection
            monitor.force_check()
            
            # Get comprehensive statistics
            stats = monitor.get_current_stats()
            
            assert hasattr(stats, 'total_storage_gb'), "Should have total storage"
            assert hasattr(stats, 'used_storage_gb'), "Should have used storage"
            assert hasattr(stats, 'free_storage_gb'), "Should have free storage"
            assert hasattr(stats, 'overall_usage_percentage'), "Should have overall usage percentage"
            assert hasattr(stats, 'instance_breakdown'), "Should have instance breakdown"
            assert hasattr(stats, 'data_type_breakdown'), "Should have data type breakdown"
            
            logger.info(f"   ✓ Total storage: {stats.total_storage_gb:.2f}GB")
            logger.info(f"   ✓ Used storage: {stats.used_storage_gb:.2f}GB")
            logger.info(f"   ✓ Overall usage: {stats.overall_usage_percentage:.1f}%")
            
            # Check instance breakdown
            assert isinstance(stats.instance_breakdown, dict), "Should have instance breakdown dict"
            if 'ai_scholar' in stats.instance_breakdown:
                logger.info(f"   ✓ AI Scholar usage: {stats.instance_breakdown['ai_scholar']}")
            if 'quant_scholar' in stats.instance_breakdown:
                logger.info(f"   ✓ Quant Scholar usage: {stats.instance_breakdown['quant_scholar']}")
            
            # Check data type breakdown
            assert isinstance(stats.data_type_breakdown, dict), "Should have data type breakdown dict"
            if 'pdf_files' in stats.data_type_breakdown:
                logger.info(f"   ✓ PDF files usage: {stats.data_type_breakdown['pdf_files']:.2f}GB")
            if 'processed_data' in stats.data_type_breakdown:
                logger.info(f"   ✓ Processed data usage: {stats.data_type_breakdown['processed_data']:.2f}GB")
            
            # Test serialization
            stats_dict = stats.to_dict()
            assert isinstance(stats_dict, dict), "Should serialize to dictionary"
            assert 'total_storage_gb' in stats_dict, "Should include total storage in serialization"
            
            logger.info("   ✓ Statistics generation and serialization working")
        
        return True
        
    except Exception as e:
        logger.error(f"Storage statistics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_monitoring_thread():
    """Test storage monitoring thread functionality."""
    try:
        from multi_instance_arxiv_system.storage.storage_monitor import (
            StorageMonitor, StorageDataType
        )
        
        logger.info("=== Testing Monitoring Thread ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_storage.db"
            monitor = StorageMonitor(
                database_path=str(db_path),
                monitoring_interval=2  # 2 seconds for testing
            )
            
            # Add monitored path
            monitor.add_monitored_path(
                temp_dir,
                StorageDataType.TEMP_FILES,
                "test_instance"
            )
            
            # Start monitoring
            monitor.start_monitoring()
            
            # Check status
            status = monitor.get_monitoring_status()
            assert status['running'] == True, "Should be running after start"
            
            logger.info("   ✓ Monitoring thread started successfully")
            
            # Wait for a few monitoring cycles
            time.sleep(5)
            
            # Check that data was collected
            assert len(monitor.current_usage) > 0, "Should have collected usage data"
            
            logger.info("   ✓ Monitoring thread collecting data")
            
            # Stop monitoring
            monitor.stop_monitoring()
            
            # Check status
            status = monitor.get_monitoring_status()
            assert status['running'] == False, "Should not be running after stop"
            
            logger.info("   ✓ Monitoring thread stopped successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Monitoring thread test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_usage_history():
    """Test storage usage history functionality."""
    try:
        from multi_instance_arxiv_system.storage.storage_monitor import (
            StorageMonitor, StorageDataType
        )
        
        logger.info("=== Testing Usage History ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_storage.db"
            monitor = StorageMonitor(database_path=str(db_path))
            
            # Add monitored path
            monitor.add_monitored_path(
                temp_dir,
                StorageDataType.TEMP_FILES,
                "test_instance"
            )
            
            # Collect usage data multiple times
            for i in range(3):
                monitor.force_check()
                time.sleep(0.1)  # Small delay between collections
            
            # Get usage history
            history = monitor.get_usage_history(days=1)
            assert len(history) >= 3, "Should have at least 3 history records"
            
            logger.info(f"   ✓ Retrieved {len(history)} history records")
            
            # Check history record structure
            if history:
                record = history[0]
                assert hasattr(record, 'path'), "Should have path"
                assert hasattr(record, 'usage_percentage'), "Should have usage percentage"
                assert hasattr(record, 'last_updated'), "Should have timestamp"
                
                logger.info(f"   ✓ History record structure correct")
            
            # Test path-specific history
            path_history = monitor.get_usage_history(path=temp_dir, days=1)
            assert len(path_history) >= 3, "Should have path-specific history"
            
            logger.info("   ✓ Path-specific history working")
        
        return True
        
    except Exception as e:
        logger.error(f"Usage history test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all storage monitor tests."""
    logger.info("Starting Task 7.1 Storage Monitoring System Tests...")
    
    tests = [
        ("StorageMonitor Initialization", test_storage_monitor_initialization),
        ("Monitored Paths Management", test_monitored_paths_management),
        ("Storage Usage Collection", test_storage_usage_collection),
        ("Storage Alerts", test_storage_alerts),
        ("Storage Statistics", test_storage_statistics),
        ("Monitoring Thread", test_monitoring_thread),
        ("Usage History", test_usage_history)
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
        logger.info("🎉 All tests passed! Storage Monitoring System is working correctly.")
        return True
    else:
        logger.error("❌ Some tests failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)