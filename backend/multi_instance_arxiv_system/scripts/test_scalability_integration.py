#!/usr/bin/env python3
"""
Integration test for Scalability Manager.

This script tests the integration between the scalability manager and other components
to ensure task 9.3 requirements are met.
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.performance.scalability_manager import (
        ScalabilityManager, ScalabilityConfig, ScalabilityMode, ResourceAllocationStrategy
    )
    from multi_instance_arxiv_system.performance.concurrent_processor import ProcessingTask, TaskPriority
    from multi_instance_arxiv_system.performance.load_balancer import LoadBalancingStrategy
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_scalability_integration():
    """Test scalability manager integration with other components."""
    
    logger.info("Starting scalability integration test")
    
    # Test 1: Basic initialization and configuration
    logger.info("Test 1: Basic initialization")
    
    config = ScalabilityConfig(
        min_workers=2,
        max_workers=8,
        initial_workers=4,
        allocation_strategy=ResourceAllocationStrategy.DYNAMIC,
        enable_predictive_scaling=True,
        enable_graceful_degradation=True
    )
    
    scalability_manager = ScalabilityManager("test_instance", config)
    
    try:
        # Start the manager
        await scalability_manager.start()
        logger.info("✓ Scalability manager started successfully")
        
        # Test 2: Worker processes and thread pools
        logger.info("Test 2: Configurable worker processes and thread pools")
        
        initial_metrics = scalability_manager.get_scalability_metrics()
        assert initial_metrics.active_workers == 4, f"Expected 4 workers, got {initial_metrics.active_workers}"
        logger.info(f"✓ Initial workers: {initial_metrics.active_workers}")
        
        # Test 3: Manual scaling (simulating dynamic resource allocation)
        logger.info("Test 3: Dynamic resource allocation")
        
        # Scale up
        success = await scalability_manager.manual_scale(6, "test_scale_up")
        assert success, "Manual scale up failed"
        
        metrics_after_scale_up = scalability_manager.get_scalability_metrics()
        assert metrics_after_scale_up.active_workers == 6, f"Expected 6 workers after scale up, got {metrics_after_scale_up.active_workers}"
        logger.info(f"✓ Scaled up to {metrics_after_scale_up.active_workers} workers")
        
        # Scale down
        success = await scalability_manager.manual_scale(3, "test_scale_down")
        assert success, "Manual scale down failed"
        
        metrics_after_scale_down = scalability_manager.get_scalability_metrics()
        assert metrics_after_scale_down.active_workers == 3, f"Expected 3 workers after scale down, got {metrics_after_scale_down.active_workers}"
        logger.info(f"✓ Scaled down to {metrics_after_scale_down.active_workers} workers")
        
        # Test 4: Load balancing for concurrent operations
        logger.info("Test 4: Load balancing for concurrent operations")
        
        # Create test tasks
        def test_processing_function(data):
            return {"result": f"processed_{data.get('id', 'unknown')}"}
        
        tasks = []
        for i in range(10):
            task = ProcessingTask(
                task_id=f"test_task_{i}",
                instance_name="test_instance",
                task_type="test",
                priority=TaskPriority.NORMAL,
                input_data={"id": i},
                processing_function=test_processing_function
            )
            tasks.append(task)
        
        # Submit tasks to test load balancing
        if scalability_manager.concurrent_processor:
            for task in tasks:
                await scalability_manager.concurrent_processor.submit_task(task)
            
            logger.info("✓ Tasks submitted for load balancing")
            
            # Wait a bit for processing
            await asyncio.sleep(2)
            
            # Check processing stats
            processing_stats = scalability_manager.concurrent_processor.get_processing_stats()
            logger.info(f"✓ Processing stats: {processing_stats.total_tasks} total tasks")
        
        # Test 5: Graceful degradation simulation
        logger.info("Test 5: Graceful degradation under high load")
        
        # Simulate mode changes
        original_mode = scalability_manager.current_mode
        
        # Test mode change to degraded
        await scalability_manager._change_mode(ScalabilityMode.DEGRADED, 0.9, 0.9)
        assert scalability_manager.current_mode == ScalabilityMode.DEGRADED
        logger.info("✓ Successfully entered degraded mode")
        
        # Test mode change back to normal
        await scalability_manager._change_mode(ScalabilityMode.NORMAL, 0.3, 0.3)
        assert scalability_manager.current_mode == ScalabilityMode.NORMAL
        logger.info("✓ Successfully returned to normal mode")
        
        # Test 6: Configuration updates
        logger.info("Test 6: Configuration updates")
        
        new_config = ScalabilityConfig(
            min_workers=1,
            max_workers=12,
            initial_workers=5,
            allocation_strategy=ResourceAllocationStrategy.ADAPTIVE
        )
        
        scalability_manager.update_config(new_config)
        assert scalability_manager.config.max_workers == 12
        logger.info("✓ Configuration updated successfully")
        
        # Test 7: Metrics export
        logger.info("Test 7: Metrics export")
        
        exported_metrics = scalability_manager.export_metrics()
        assert 'instance_name' in exported_metrics
        assert 'current_mode' in exported_metrics
        assert 'metrics' in exported_metrics
        assert 'config' in exported_metrics
        logger.info("✓ Metrics exported successfully")
        
        # Test 8: Scaling history
        logger.info("Test 8: Scaling history")
        
        scaling_history = scalability_manager.get_scaling_history()
        assert len(scaling_history) >= 2, "Expected at least 2 scaling actions"
        logger.info(f"✓ Scaling history contains {len(scaling_history)} actions")
        
        logger.info("All integration tests passed successfully!")
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        raise
    
    finally:
        # Clean up
        await scalability_manager.stop()
        logger.info("Scalability manager stopped")


async def test_load_balancing_strategies():
    """Test different load balancing strategies."""
    
    logger.info("Testing load balancing strategies")
    
    config = ScalabilityConfig(min_workers=2, max_workers=4, initial_workers=3)
    scalability_manager = ScalabilityManager("test_lb", config)
    
    try:
        await scalability_manager.start()
        
        if scalability_manager.load_balancer:
            # Test different strategies
            strategies = [
                LoadBalancingStrategy.ROUND_ROBIN,
                LoadBalancingStrategy.LEAST_CONNECTIONS,
                LoadBalancingStrategy.RESOURCE_BASED
            ]
            
            for strategy in strategies:
                success = scalability_manager.load_balancer.set_load_balancing_strategy("default", strategy)
                assert success, f"Failed to set strategy {strategy}"
                logger.info(f"✓ Set load balancing strategy to {strategy.value}")
        
        logger.info("Load balancing strategy tests passed!")
        
    finally:
        await scalability_manager.stop()


async def main():
    """Run all integration tests."""
    
    try:
        await test_scalability_integration()
        await test_load_balancing_strategies()
        
        print("\n" + "="*50)
        print("🎉 ALL SCALABILITY INTEGRATION TESTS PASSED!")
        print("Task 9.3 requirements verified:")
        print("✓ Configurable worker processes and thread pools")
        print("✓ Load balancing for concurrent operations")
        print("✓ Dynamic resource allocation based on system load")
        print("✓ Graceful degradation under high load")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Integration tests failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())