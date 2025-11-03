#!/usr/bin/env python3
"""
Test script for multi-instance ArXiv system infrastructure.

This script validates that all components are properly set up and can be
imported and initialized correctly.
"""

import sys
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all components can be imported."""
    logger.info("Testing imports...")
    
    try:
        # Test shared components
        from multi_instance_arxiv_system.shared.multi_instance_data_models import (
            InstanceConfig, ArxivPaper, JournalPaper, StoragePaths
        )
        logger.info("✓ Data models imported successfully")
        
        from multi_instance_arxiv_system.shared.multi_instance_state_manager import (
            MultiInstanceStateManager, GlobalStateManager
        )
        logger.info("✓ State managers imported successfully")
        
        from multi_instance_arxiv_system.shared.multi_instance_progress_tracker import (
            MultiInstanceProgressTracker, GlobalProgressTracker
        )
        logger.info("✓ Progress trackers imported successfully")
        
        from multi_instance_arxiv_system.shared.multi_instance_error_handler import (
            MultiInstanceErrorHandler, GlobalErrorHandler
        )
        logger.info("✓ Error handlers imported successfully")
        
        from multi_instance_arxiv_system.shared.instance_manager import (
            InstanceManager, MultiInstanceManager
        )
        logger.info("✓ Instance managers imported successfully")
        
        # Test configuration components
        from multi_instance_arxiv_system.config.instance_config_manager import (
            InstanceConfigManager, MultiInstanceConfigManager
        )
        logger.info("✓ Config managers imported successfully")
        
        from multi_instance_arxiv_system.config.default_instance_configs import (
            DEFAULT_AI_SCHOLAR_CONFIG, DEFAULT_QUANT_SCHOLAR_CONFIG
        )
        logger.info("✓ Default configs imported successfully")
        
        # Test base classes
        from multi_instance_arxiv_system.base.base_scholar_downloader import BaseScholarDownloader
        from multi_instance_arxiv_system.base.base_journal_handler import BaseJournalHandler
        logger.info("✓ Base classes imported successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        return False


def test_configuration_loading():
    """Test configuration loading and validation."""
    logger.info("Testing configuration loading...")
    
    try:
        from multi_instance_arxiv_system.config.instance_config_manager import InstanceConfigManager
        
        # Test AI Scholar configuration
        config_dir = Path(__file__).parent / "configs"
        ai_config_manager = InstanceConfigManager(
            instance_name="ai_scholar",
            config_dir=config_dir
        )
        
        ai_instance_config = ai_config_manager.get_instance_config()
        logger.info(f"✓ AI Scholar config loaded: {ai_instance_config.display_name}")
        
        # Validate AI Scholar config
        ai_errors = ai_config_manager.validate_instance_config()
        if ai_errors:
            logger.warning(f"AI Scholar config validation errors: {ai_errors}")
        else:
            logger.info("✓ AI Scholar config validation passed")
        
        # Test Quant Scholar configuration
        quant_config_manager = InstanceConfigManager(
            instance_name="quant_scholar",
            config_dir=config_dir
        )
        
        quant_instance_config = quant_config_manager.get_instance_config()
        logger.info(f"✓ Quant Scholar config loaded: {quant_instance_config.display_name}")
        
        # Validate Quant Scholar config
        quant_errors = quant_config_manager.validate_instance_config()
        if quant_errors:
            logger.warning(f"Quant Scholar config validation errors: {quant_errors}")
        else:
            logger.info("✓ Quant Scholar config validation passed")
        
        return True
        
    except Exception as e:
        logger.error(f"Configuration loading failed: {e}")
        return False


def test_instance_manager():
    """Test instance manager initialization."""
    logger.info("Testing instance manager...")
    
    try:
        from multi_instance_arxiv_system.shared.instance_manager import InstanceManager
        
        # Test AI Scholar instance manager
        config_path = Path(__file__).parent / "configs" / "ai_scholar.yaml"
        ai_manager = InstanceManager(
            instance_name="ai_scholar",
            config_path=config_path
        )
        
        if ai_manager.initialize():
            logger.info("✓ AI Scholar instance manager initialized")
            
            # Test getting instance summary
            summary = ai_manager.get_instance_summary()
            logger.info(f"✓ AI Scholar summary: {summary['instance_name']}")
            
            # Test storage directory creation
            if ai_manager.create_storage_directories():
                logger.info("✓ AI Scholar storage directories created")
            else:
                logger.warning("AI Scholar storage directory creation failed")
            
            ai_manager.shutdown()
        else:
            logger.error("AI Scholar instance manager initialization failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Instance manager test failed: {e}")
        return False


def test_state_manager():
    """Test state manager functionality."""
    logger.info("Testing state manager...")
    
    try:
        from multi_instance_arxiv_system.shared.multi_instance_state_manager import (
            MultiInstanceStateManager, GlobalStateManager
        )
        from multi_instance_arxiv_system.shared.multi_instance_data_models import (
            MultiInstanceProcessingState
        )
        from datetime import datetime
        
        # Test state directory
        test_state_dir = Path("/tmp/multi_instance_test_state")
        
        # Test instance state manager
        state_manager = MultiInstanceStateManager(test_state_dir, "test_instance")
        
        # Create test state
        test_state = MultiInstanceProcessingState(
            processor_id="test_processor",
            start_time=datetime.now(),
            last_update=datetime.now(),
            instance_name="test_instance"
        )
        
        # Test save and load
        if state_manager.save_instance_state("test_processor", test_state):
            logger.info("✓ State saved successfully")
            
            loaded_state = state_manager.load_instance_state("test_processor")
            if loaded_state and loaded_state.instance_name == "test_instance":
                logger.info("✓ State loaded successfully")
            else:
                logger.error("State loading failed")
                return False
        else:
            logger.error("State saving failed")
            return False
        
        # Test global state manager
        global_manager = GlobalStateManager(test_state_dir)
        global_summary = global_manager.get_global_summary()
        logger.info(f"✓ Global state manager: {global_summary['total_instances']} instances")
        
        # Cleanup
        import shutil
        if test_state_dir.exists():
            shutil.rmtree(test_state_dir)
        
        return True
        
    except Exception as e:
        logger.error(f"State manager test failed: {e}")
        return False


def test_progress_tracker():
    """Test progress tracker functionality."""
    logger.info("Testing progress tracker...")
    
    try:
        from multi_instance_arxiv_system.shared.multi_instance_progress_tracker import (
            MultiInstanceProgressTracker, GlobalProgressTracker
        )
        
        # Test instance progress tracker
        progress_tracker = MultiInstanceProgressTracker("test_instance")
        
        # Test tracking
        progress_tracker.start_instance_tracking(100, "test_operation")
        progress_tracker.update_instance_progress(50, 2, "test_item", 1024)
        
        stats = progress_tracker.get_instance_stats()
        if stats.instance_name == "test_instance" and stats.processed_papers == 50:
            logger.info("✓ Instance progress tracker working")
        else:
            logger.error("Instance progress tracker failed")
            return False
        
        # Test global progress tracker
        global_tracker = GlobalProgressTracker()
        registered_tracker = global_tracker.register_instance("test_instance_2")
        
        global_summary = global_tracker.get_global_summary()
        if global_summary['global_stats']['total_instances'] >= 1:
            logger.info("✓ Global progress tracker working")
        else:
            logger.error("Global progress tracker failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Progress tracker test failed: {e}")
        return False


def test_error_handler():
    """Test error handler functionality."""
    logger.info("Testing error handler...")
    
    try:
        from multi_instance_arxiv_system.shared.multi_instance_error_handler import (
            MultiInstanceErrorHandler, GlobalErrorHandler
        )
        
        # Test error directory
        test_error_dir = Path("/tmp/multi_instance_test_errors")
        
        # Test instance error handler
        error_handler = MultiInstanceErrorHandler(test_error_dir, "test_instance", "test_processor")
        
        # Test error logging
        test_error = Exception("Test error")
        context = {"test_key": "test_value"}
        
        processing_error = error_handler.log_instance_error(
            test_error, context, "test_error", "error"
        )
        
        if processing_error.error_message == "Test error":
            logger.info("✓ Instance error handler working")
        else:
            logger.error("Instance error handler failed")
            return False
        
        # Test error summary
        summary = error_handler.get_instance_error_summary()
        if summary['instance_stats']['total_errors'] >= 1:
            logger.info("✓ Error summary working")
        else:
            logger.error("Error summary failed")
            return False
        
        # Test global error handler
        global_error_handler = GlobalErrorHandler(test_error_dir)
        global_summary = global_error_handler.get_global_error_summary()
        
        if 'global_stats' in global_summary:
            logger.info("✓ Global error handler working")
        else:
            logger.error("Global error handler failed")
            return False
        
        # Cleanup
        import shutil
        if test_error_dir.exists():
            shutil.rmtree(test_error_dir)
        
        return True
        
    except Exception as e:
        logger.error(f"Error handler test failed: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("Starting multi-instance ArXiv system infrastructure tests...")
    
    tests = [
        ("Imports", test_imports),
        ("Configuration Loading", test_configuration_loading),
        ("Instance Manager", test_instance_manager),
        ("State Manager", test_state_manager),
        ("Progress Tracker", test_progress_tracker),
        ("Error Handler", test_error_handler),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            if test_func():
                logger.info(f"✓ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"✗ {test_name} FAILED")
                failed += 1
        except Exception as e:
            logger.error(f"✗ {test_name} FAILED with exception: {e}")
            failed += 1
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Test Results: {passed} passed, {failed} failed")
    logger.info(f"{'='*50}")
    
    if failed == 0:
        logger.info("🎉 All tests passed! Multi-instance infrastructure is ready.")
        return 0
    else:
        logger.error(f"❌ {failed} tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())