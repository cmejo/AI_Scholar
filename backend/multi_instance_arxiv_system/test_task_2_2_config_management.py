#!/usr/bin/env python3
"""
Test for Task 2.2: Instance Configuration Management functionality.

Tests the instance configuration management system including YAML loading,
validation, environment variable support, and configuration creation.
"""

import sys
import os
import tempfile
import logging
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_instance_config_manager():
    """Test InstanceConfigManager functionality."""
    try:
        from multi_instance_arxiv_system.config.instance_config_manager import InstanceConfigManager
        
        logger.info("=== Testing InstanceConfigManager ===")
        
        # Test AI Scholar configuration
        ai_config_manager = InstanceConfigManager(
            instance_name='ai_scholar',
            config_dir='backend/multi_instance_arxiv_system/configs'
        )
        
        logger.info("   ✓ AI Scholar config manager created")
        
        # Test configuration loading
        ai_instance_config = ai_config_manager.get_instance_config()
        assert ai_instance_config.instance_name == 'ai_scholar', "Should load AI Scholar config"
        assert ai_instance_config.display_name == 'AI Scholar', "Should have correct display name"
        assert len(ai_instance_config.arxiv_categories) > 0, "Should have arXiv categories"
        
        logger.info(f"   ✓ AI Scholar config loaded: {len(ai_instance_config.arxiv_categories)} categories")
        
        # Test Quant Scholar configuration
        quant_config_manager = InstanceConfigManager(
            instance_name='quant_scholar',
            config_dir='backend/multi_instance_arxiv_system/configs'
        )
        
        quant_instance_config = quant_config_manager.get_instance_config()
        assert quant_instance_config.instance_name == 'quant_scholar', "Should load Quant Scholar config"
        assert len(quant_instance_config.journal_sources) > 0, "Should have journal sources"
        
        logger.info(f"   ✓ Quant Scholar config loaded: {len(quant_instance_config.journal_sources)} journal sources")
        
        # Test configuration validation
        ai_errors = ai_config_manager.validate_instance_config()
        assert isinstance(ai_errors, list), "Should return validation errors list"
        
        quant_errors = quant_config_manager.validate_instance_config()
        assert isinstance(quant_errors, list), "Should return validation errors list"
        
        logger.info(f"   ✓ Validation completed - AI errors: {len(ai_errors)}, Quant errors: {len(quant_errors)}")
        
        return True
        
    except Exception as e:
        logger.error(f"InstanceConfigManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_instance_config_manager():
    """Test MultiInstanceConfigManager functionality."""
    try:
        from multi_instance_arxiv_system.config.instance_config_manager import MultiInstanceConfigManager
        
        logger.info("=== Testing MultiInstanceConfigManager ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "configs"
            
            # Create multi-instance manager
            multi_manager = MultiInstanceConfigManager(config_dir)
            
            logger.info("   ✓ MultiInstanceConfigManager created")
            
            # Test creating default configs
            success = multi_manager.create_default_configs()
            assert success == True, "Should create default configs successfully"
            
            logger.info("   ✓ Default configs created")
            
            # Test listing configured instances
            instances = multi_manager.list_configured_instances()
            assert 'ai_scholar' in instances, "Should list AI Scholar instance"
            assert 'quant_scholar' in instances, "Should list Quant Scholar instance"
            
            logger.info(f"   ✓ Listed instances: {instances}")
            
            # Test getting instance managers
            ai_manager = multi_manager.get_instance_manager('ai_scholar')
            assert ai_manager is not None, "Should get AI Scholar manager"
            
            quant_manager = multi_manager.get_instance_manager('quant_scholar')
            assert quant_manager is not None, "Should get Quant Scholar manager"
            
            logger.info("   ✓ Instance managers retrieved")
            
            # Test validation of all configs
            validation_results = multi_manager.validate_all_configs()
            assert isinstance(validation_results, dict), "Should return validation results dict"
            assert 'ai_scholar' in validation_results, "Should validate AI Scholar"
            assert 'quant_scholar' in validation_results, "Should validate Quant Scholar"
            
            logger.info(f"   ✓ All configs validated: {len(validation_results)} instances")
        
        return True
        
    except Exception as e:
        logger.error(f"MultiInstanceConfigManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_environment_variable_support():
    """Test environment variable override functionality."""
    try:
        from multi_instance_arxiv_system.config.instance_config_manager import InstanceConfigManager
        
        logger.info("=== Testing Environment Variable Support ===")
        
        # Set test environment variables
        test_env_vars = {
            'AI_SCHOLAR_BATCH_SIZE': '50',
            'AI_SCHOLAR_MAX_DOWNLOADS': '10',
            'AI_SCHOLAR_COLLECTION_NAME': 'test_ai_papers',
            'AI_SCHOLAR_NOTIFICATIONS_ENABLED': 'true',
            'CHROMADB_HOST': 'test-chromadb-host',
            'CHROMADB_PORT': '9999'
        }
        
        # Set environment variables
        for key, value in test_env_vars.items():
            os.environ[key] = value
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                config_dir = Path(temp_dir) / "configs"
                
                # Create config manager (will use env vars)
                config_manager = InstanceConfigManager(
                    instance_name='ai_scholar',
                    config_dir=config_dir
                )
                
                # Get configuration
                instance_config = config_manager.get_instance_config()
                
                # Verify environment variable overrides
                assert instance_config.processing_config.batch_size == 50, "Should override batch size from env var"
                assert instance_config.processing_config.max_concurrent_downloads == 10, "Should override max downloads from env var"
                assert instance_config.vector_store_config.collection_name == 'test_ai_papers', "Should override collection name from env var"
                assert instance_config.notification_config.enabled == True, "Should override notifications enabled from env var"
                assert instance_config.vector_store_config.host == 'test-chromadb-host', "Should override ChromaDB host from env var"
                assert instance_config.vector_store_config.port == 9999, "Should override ChromaDB port from env var"
                
                logger.info("   ✓ Environment variable overrides working correctly")
                
        finally:
            # Clean up environment variables
            for key in test_env_vars:
                if key in os.environ:
                    del os.environ[key]
        
        return True
        
    except Exception as e:
        logger.error(f"Environment variable test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_file_creation():
    """Test configuration file creation functionality."""
    try:
        from multi_instance_arxiv_system.config.instance_config_manager import InstanceConfigManager
        
        logger.info("=== Testing Configuration File Creation ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "configs"
            config_file = config_dir / "test_instance.yaml"
            
            # Create config manager for new instance
            config_manager = InstanceConfigManager(
                instance_name='test_instance',
                config_file=config_file,
                config_dir=config_dir
            )
            
            # Create configuration file
            success = config_manager.create_instance_config_file()
            assert success == True, "Should create config file successfully"
            assert config_file.exists(), "Config file should exist"
            
            logger.info("   ✓ Configuration file created successfully")
            
            # Test loading the created file
            new_manager = InstanceConfigManager(
                instance_name='test_instance',
                config_file=config_file,
                config_dir=config_dir
            )
            
            instance_config = new_manager.get_instance_config()
            assert instance_config.instance_name == 'test_instance', "Should load created config"
            
            logger.info("   ✓ Created configuration file loaded successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Config file creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_default_configurations():
    """Test default configuration values."""
    try:
        from multi_instance_arxiv_system.config.default_instance_configs import (
            DEFAULT_AI_SCHOLAR_CONFIG, DEFAULT_QUANT_SCHOLAR_CONFIG,
            get_categories_for_field, create_custom_instance_config
        )
        
        logger.info("=== Testing Default Configurations ===")
        
        # Test AI Scholar defaults
        ai_config = DEFAULT_AI_SCHOLAR_CONFIG
        assert ai_config['instance']['name'] == 'ai_scholar', "Should have correct AI Scholar name"
        assert len(ai_config['data_sources']['arxiv']['categories']) > 0, "Should have arXiv categories"
        assert ai_config['processing']['batch_size'] > 0, "Should have valid batch size"
        
        logger.info(f"   ✓ AI Scholar default config: {len(ai_config['data_sources']['arxiv']['categories'])} categories")
        
        # Test Quant Scholar defaults
        quant_config = DEFAULT_QUANT_SCHOLAR_CONFIG
        assert quant_config['instance']['name'] == 'quant_scholar', "Should have correct Quant Scholar name"
        assert len(quant_config['data_sources']['journals']) > 0, "Should have journal sources"
        
        logger.info(f"   ✓ Quant Scholar default config: {len(quant_config['data_sources']['journals'])} journal sources")
        
        # Test category helpers
        ai_categories = get_categories_for_field('ai_ml')
        assert len(ai_categories) > 0, "Should return AI/ML categories"
        
        physics_categories = get_categories_for_field('physics')
        assert len(physics_categories) > 0, "Should return physics categories"
        
        logger.info(f"   ✓ Category helpers: AI/ML={len(ai_categories)}, Physics={len(physics_categories)}")
        
        # Test custom config creation
        custom_config = create_custom_instance_config(
            instance_name='test_custom',
            display_name='Test Custom',
            description='Test custom instance',
            arxiv_categories=['cs.AI', 'cs.LG']
        )
        
        assert custom_config['instance']['name'] == 'test_custom', "Should create custom config"
        assert len(custom_config['data_sources']['arxiv']['categories']) == 2, "Should have specified categories"
        
        logger.info("   ✓ Custom configuration creation working")
        
        return True
        
    except Exception as e:
        logger.error(f"Default configurations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all configuration management tests."""
    logger.info("Starting Task 2.2 Instance Configuration Management Tests...")
    
    tests = [
        ("InstanceConfigManager", test_instance_config_manager),
        ("MultiInstanceConfigManager", test_multi_instance_config_manager),
        ("Environment Variable Support", test_environment_variable_support),
        ("Config File Creation", test_config_file_creation),
        ("Default Configurations", test_default_configurations)
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
        logger.info("🎉 All tests passed! Instance Configuration Management is working correctly.")
        return True
    else:
        logger.error("❌ Some tests failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)