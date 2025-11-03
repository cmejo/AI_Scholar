#!/usr/bin/env python3
"""
Test script for Task 1: Multi-Instance Infrastructure Setup

This script validates that the multi-instance infrastructure and shared components
are properly set up and working correctly.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_infrastructure_setup():
    """Test the multi-instance infrastructure setup."""
    print("=" * 60)
    print("TESTING MULTI-INSTANCE INFRASTRUCTURE SETUP")
    print("=" * 60)
    
    try:
        # Test 1: Import all main components
        print("\n1. Testing component imports...")
        
        from multi_instance_arxiv_system.shared.instance_manager import (
            InstanceManager, MultiInstanceManager
        )
        from multi_instance_arxiv_system.shared.multi_instance_state_manager import (
            MultiInstanceStateManager
        )
        from multi_instance_arxiv_system.shared.multi_instance_progress_tracker import (
            MultiInstanceProgressTracker
        )
        from multi_instance_arxiv_system.shared.multi_instance_error_handler import (
            MultiInstanceErrorHandler
        )
        from multi_instance_arxiv_system.config.instance_config_manager import (
            InstanceConfigManager
        )
        from multi_instance_arxiv_system.base.base_scholar_downloader import (
            BaseScholarDownloader
        )
        
        print("✅ All main components imported successfully")
        
        # Test 2: Create temporary directories for testing
        print("\n2. Setting up test directories...")
        
        test_base_dir = Path("/tmp/multi_instance_test")
        test_config_dir = test_base_dir / "configs"
        test_state_dir = test_base_dir / "state"
        test_error_dir = test_base_dir / "errors"
        
        # Create directories
        for directory in [test_config_dir, test_state_dir, test_error_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Test directories created at {test_base_dir}")
        
        # Test 3: Initialize MultiInstanceManager
        print("\n3. Testing MultiInstanceManager initialization...")
        
        multi_manager = MultiInstanceManager(
            base_config_dir=test_config_dir,
            base_state_dir=test_state_dir,
            base_error_dir=test_error_dir
        )
        
        print("✅ MultiInstanceManager initialized successfully")
        
        # Test 4: Register AI Scholar instance
        print("\n4. Testing AI Scholar instance registration...")
        
        ai_scholar_manager = multi_manager.register_instance("ai_scholar")
        
        if ai_scholar_manager.is_initialized:
            print("✅ AI Scholar instance registered and initialized")
            
            # Test configuration
            config = ai_scholar_manager.config
            print(f"   - Display Name: {config.display_name}")
            print(f"   - ArXiv Categories: {len(config.arxiv_categories)}")
            print(f"   - Collection Name: {config.vector_store_config.collection_name}")
        else:
            print("❌ AI Scholar instance failed to initialize")
            return False
        
        # Test 5: Register Quant Scholar instance
        print("\n5. Testing Quant Scholar instance registration...")
        
        quant_scholar_manager = multi_manager.register_instance("quant_scholar")
        
        if quant_scholar_manager.is_initialized:
            print("✅ Quant Scholar instance registered and initialized")
            
            # Test configuration
            config = quant_scholar_manager.config
            print(f"   - Display Name: {config.display_name}")
            print(f"   - ArXiv Categories: {len(config.arxiv_categories)}")
            print(f"   - Collection Name: {config.vector_store_config.collection_name}")
        else:
            print("❌ Quant Scholar instance failed to initialize")
            return False
        
        # Test 6: Test instance separation
        print("\n6. Testing instance separation...")
        
        ai_config = ai_scholar_manager.config
        quant_config = quant_scholar_manager.config
        
        # Check that instances have different configurations
        if ai_config.instance_name != quant_config.instance_name:
            print("✅ Instances have different names")
        else:
            print("❌ Instance names are not separated")
            return False
        
        if ai_config.vector_store_config.collection_name != quant_config.vector_store_config.collection_name:
            print("✅ Instances have different vector store collections")
        else:
            print("❌ Vector store collections are not separated")
            return False
        
        if ai_config.storage_paths.pdf_directory != quant_config.storage_paths.pdf_directory:
            print("✅ Instances have different storage paths")
        else:
            print("❌ Storage paths are not separated")
            return False
        
        # Test 7: Test shared components
        print("\n7. Testing shared components...")
        
        # Test state manager
        ai_state_manager = ai_scholar_manager.state_manager
        quant_state_manager = quant_scholar_manager.state_manager
        
        if ai_state_manager.instance_name != quant_state_manager.instance_name:
            print("✅ State managers are instance-specific")
        else:
            print("❌ State managers are not properly separated")
            return False
        
        # Test progress tracker
        ai_progress_tracker = ai_scholar_manager.progress_tracker
        quant_progress_tracker = quant_scholar_manager.progress_tracker
        
        if ai_progress_tracker.instance_name != quant_progress_tracker.instance_name:
            print("✅ Progress trackers are instance-specific")
        else:
            print("❌ Progress trackers are not properly separated")
            return False
        
        # Test 8: Test global summary
        print("\n8. Testing global summary...")
        
        global_summary = multi_manager.get_global_summary()
        
        if global_summary['total_instances'] == 2:
            print("✅ Global summary shows correct number of instances")
        else:
            print(f"❌ Global summary shows {global_summary['total_instances']} instances, expected 2")
            return False
        
        if 'ai_scholar' in global_summary['instances'] and 'quant_scholar' in global_summary['instances']:
            print("✅ Global summary includes both instances")
        else:
            print("❌ Global summary missing expected instances")
            return False
        
        # Test 9: Test configuration saving
        print("\n9. Testing configuration saving...")
        
        ai_config_path = test_config_dir / "ai_scholar_test.yaml"
        if ai_scholar_manager.save_configuration(ai_config_path):
            print("✅ AI Scholar configuration saved successfully")
            
            if ai_config_path.exists():
                print("✅ Configuration file created")
            else:
                print("❌ Configuration file not found")
                return False
        else:
            print("❌ Failed to save AI Scholar configuration")
            return False
        
        # Test 10: Test directory creation
        print("\n10. Testing storage directory creation...")
        
        if ai_scholar_manager.create_storage_directories():
            print("✅ AI Scholar storage directories created")
        else:
            print("❌ Failed to create AI Scholar storage directories")
            return False
        
        if quant_scholar_manager.create_storage_directories():
            print("✅ Quant Scholar storage directories created")
        else:
            print("❌ Failed to create Quant Scholar storage directories")
            return False
        
        # Test 11: Test cleanup
        print("\n11. Testing cleanup...")
        
        multi_manager.shutdown_all_instances()
        print("✅ All instances shutdown successfully")
        
        # Cleanup test directories
        import shutil
        if test_base_dir.exists():
            shutil.rmtree(test_base_dir)
            print("✅ Test directories cleaned up")
        
        print("\n" + "=" * 60)
        print("✅ ALL INFRASTRUCTURE TESTS PASSED!")
        print("✅ Task 1: Multi-Instance Infrastructure Setup - COMPLETE")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Infrastructure test failed: {e}")
        logger.exception("Infrastructure test error")
        return False


def test_yaml_configuration():
    """Test YAML configuration loading."""
    print("\n" + "=" * 60)
    print("TESTING YAML CONFIGURATION SYSTEM")
    print("=" * 60)
    
    try:
        from multi_instance_arxiv_system.config.instance_config_manager import InstanceConfigManager
        
        # Test loading existing configurations
        config_dir = Path(__file__).parent / "configs"
        
        if (config_dir / "ai_scholar.yaml").exists():
            print("\n1. Testing AI Scholar YAML configuration...")
            
            ai_config_manager = InstanceConfigManager(
                instance_name="ai_scholar",
                config_dir=config_dir
            )
            
            # Configuration is loaded automatically during initialization
            print("✅ AI Scholar YAML configuration loaded successfully")
            
            config = ai_config_manager.get_config()
            print(f"   - Instance Name: {config.get('instance_name')}")
            print(f"   - Display Name: {config.get('display_name')}")
            print(f"   - ArXiv Categories: {len(config.get('arxiv_categories', []))}")
        
        if (config_dir / "quant_scholar.yaml").exists():
            print("\n2. Testing Quant Scholar YAML configuration...")
            
            quant_config_manager = InstanceConfigManager(
                instance_name="quant_scholar",
                config_dir=config_dir
            )
            
            # Configuration is loaded automatically during initialization
            print("✅ Quant Scholar YAML configuration loaded successfully")
            
            config = quant_config_manager.get_config()
            print(f"   - Instance Name: {config.get('instance_name')}")
            print(f"   - Display Name: {config.get('display_name')}")
            print(f"   - ArXiv Categories: {len(config.get('arxiv_categories', []))}")
            print(f"   - Journal Sources: {len(config.get('journal_sources', []))}")
        
        print("\n✅ YAML CONFIGURATION TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ YAML configuration test failed: {e}")
        logger.exception("YAML configuration test error")
        return False


def main():
    """Run all infrastructure tests."""
    print("Starting Multi-Instance Infrastructure Tests...")
    print(f"Test started at: {datetime.now()}")
    
    # Run infrastructure tests
    infrastructure_success = test_infrastructure_setup()
    
    # Run YAML configuration tests
    yaml_success = test_yaml_configuration()
    
    # Overall result
    if infrastructure_success and yaml_success:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("Task 1: Multi-Instance Infrastructure Setup is COMPLETE")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Task 1: Multi-Instance Infrastructure Setup needs attention")
        return 1


if __name__ == "__main__":
    exit(main())