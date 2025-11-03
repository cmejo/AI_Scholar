#!/usr/bin/env python3
"""
Scalability Manager Demo Script for Multi-Instance ArXiv System.

This script demonstrates the scalability and load balancing features including:
- Configurable worker processes and thread pools
- Dynamic resource allocation based on system load
- Load balancing for concurrent operations
- Graceful degradation under high load

Usage:
    python scalability_demo.py [--instance ai_scholar|quant_scholar] [--config path/to/config.yaml]
"""

import sys
import asyncio
import argparse
import logging
import time
import random
from pathlib import Path
from typing import List, Dict, Any
import yaml

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.performance.scalability_manager import (
        ScalabilityManager, ScalabilityConfig, ScalabilityMode, ResourceAllocationStrategy
    )
    from multi_instance_arxiv_system.performance.concurrent_processor import ProcessingTask, TaskPriority
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure the multi_instance_arxiv_system package is properly installed.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScalabilityDemo:
    """Demonstration of scalability and load balancing features."""
    
    def __init__(self, instance_name: str, config_path: str):
        self.instance_name = instance_name
        self.config_path = config_path
        self.scalability_manager: ScalabilityManager = None
        self.demo_tasks: List[ProcessingTask] = []
        
        # Load configuration
        self.config = self._load_config()
        
        logger.info(f"ScalabilityDemo initialized for {instance_name}")
    
    def _load_config(self) -> ScalabilityConfig:
        """Load scalability configuration from YAML file."""
        
        try:
            with open(self.config_path, 'r') as f:
                yaml_config = yaml.safe_load(f)
            
            # Get instance-specific config
            instance_config = yaml_config.get('instances', {}).get(self.instance_name, {})
            
            # Create ScalabilityConfig object
            config = ScalabilityConfig(
                min_workers=instance_config.get('min_workers', 2),
                max_workers=instance_config.get('max_workers', 8),
                initial_workers=instance_config.get('initial_workers', 4),
                worker_scale_factor=instance_config.get('worker_scale_factor', 1.5),
                
                min_threads_per_worker=instance_config.get('min_threads_per_worker', 2),
                max_threads_per_worker=instance_config.get('max_threads_per_worker', 6),
                thread_scale_factor=instance_config.get('thread_scale_factor', 1.2),
                
                scale_up_cpu_threshold=instance_config.get('scale_up_cpu_threshold', 0.75),
                scale_up_memory_threshold=instance_config.get('scale_up_memory_threshold', 0.80),
                scale_down_cpu_threshold=instance_config.get('scale_down_cpu_threshold', 0.30),
                scale_down_memory_threshold=instance_config.get('scale_down_memory_threshold', 0.40),
                
                degradation_cpu_threshold=instance_config.get('degradation_cpu_threshold', 0.90),
                degradation_memory_threshold=instance_config.get('degradation_memory_threshold', 0.95),
                emergency_cpu_threshold=instance_config.get('emergency_cpu_threshold', 0.98),
                emergency_memory_threshold=instance_config.get('emergency_memory_threshold', 0.99),
                
                scale_check_interval=instance_config.get('scale_check_interval', 30),
                scale_up_cooldown=instance_config.get('scale_up_cooldown', 120),
                scale_down_cooldown=instance_config.get('scale_down_cooldown', 300),
                
                allocation_strategy=ResourceAllocationStrategy(
                    instance_config.get('allocation_strategy', 'dynamic')
                ),
                enable_predictive_scaling=instance_config.get('enable_predictive_scaling', True),
                enable_graceful_degradation=instance_config.get('enable_graceful_degradation', True)
            )
            
            logger.info(f"Loaded configuration for {self.instance_name}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            # Return default configuration
            return ScalabilityConfig()
    
    async def run_demo(self) -> None:
        """Run the complete scalability demonstration."""
        
        logger.info("Starting Scalability Manager Demo")
        
        # Initialize scalability manager
        self.scalability_manager = ScalabilityManager(
            instance_name=self.instance_name,
            config=self.config
        )
        
        try:
            # Start the scalability manager
            await self.scalability_manager.start()
            
            # Run demonstration scenarios
            await self._demo_normal_operations()
            await self._demo_load_balancing()
            await self._demo_dynamic_scaling()
            await self._demo_graceful_degradation()
            await self._demo_predictive_scaling()
            
            # Show final metrics
            await self._show_final_metrics()
            
        except Exception as e:
            logger.error(f"Error during demo: {e}")
        
        finally:
            # Clean up
            if self.scalability_manager:
                await self.scalability_manager.stop()
            
            logger.info("Scalability Manager Demo completed")
    
    async def _demo_normal_operations(self) -> None:
        """Demonstrate normal operations with baseline load."""
        
        logger.info("=== Demo 1: Normal Operations ===")
        
        # Create some baseline tasks
        tasks = self._create_demo_tasks(count=10, task_type="baseline", priority=TaskPriority.NORMAL)
        
        # Submit tasks
        for task in tasks:
            if self.scalability_manager.concurrent_processor:
                await self.scalability_manager.concurrent_processor.submit_task(task)
        
        # Wait for processing
        await asyncio.sleep(30)
        
        # Show metrics
        metrics = self.scalability_manager.get_scalability_metrics()
        logger.info(f"Normal operations metrics: Workers={metrics.active_workers}, "
                   f"Mode={metrics.current_mode.value}, CPU={metrics.cpu_usage_percent:.1f}%")
    
    async def _demo_load_balancing(self) -> None:
        """Demonstrate load balancing across workers."""
        
        logger.info("=== Demo 2: Load Balancing ===")
        
        # Create tasks with different priorities and types
        high_priority_tasks = self._create_demo_tasks(count=5, task_type="high_priority", priority=TaskPriority.HIGH)
        normal_tasks = self._create_demo_tasks(count=15, task_type="normal", priority=TaskPriority.NORMAL)
        low_priority_tasks = self._create_demo_tasks(count=10, task_type="low_priority", priority=TaskPriority.LOW)
        
        all_tasks = high_priority_tasks + normal_tasks + low_priority_tasks
        
        # Submit all tasks rapidly to test load balancing
        logger.info(f"Submitting {len(all_tasks)} tasks to test load balancing")
        
        for task in all_tasks:
            if self.scalability_manager.concurrent_processor:
                await self.scalability_manager.concurrent_processor.submit_task(task)
            await asyncio.sleep(0.1)  # Small delay to simulate real workload
        
        # Monitor load balancing for 60 seconds
        for i in range(6):
            await asyncio.sleep(10)
            
            if self.scalability_manager.load_balancer:
                lb_stats = self.scalability_manager.load_balancer.get_load_balancer_stats()
                logger.info(f"Load balancing status ({i*10}s): System load={lb_stats.get('system_load', 0):.2f}, "
                           f"Degraded mode={lb_stats.get('degraded_mode', False)}")
    
    async def _demo_dynamic_scaling(self) -> None:
        """Demonstrate dynamic scaling based on load."""
        
        logger.info("=== Demo 3: Dynamic Scaling ===")
        
        # Start with current worker count
        initial_workers = self.scalability_manager.current_workers
        logger.info(f"Starting dynamic scaling demo with {initial_workers} workers")
        
        # Phase 1: Gradually increase load to trigger scale-up
        logger.info("Phase 1: Increasing load to trigger scale-up")
        
        for batch in range(3):
            batch_tasks = self._create_demo_tasks(
                count=20, 
                task_type=f"scale_up_batch_{batch}", 
                priority=TaskPriority.NORMAL
            )
            
            for task in batch_tasks:
                if self.scalability_manager.concurrent_processor:
                    await self.scalability_manager.concurrent_processor.submit_task(task)
            
            await asyncio.sleep(45)  # Wait for scaling decisions
            
            metrics = self.scalability_manager.get_scalability_metrics()
            logger.info(f"After batch {batch + 1}: Workers={metrics.active_workers}, "
                       f"CPU={metrics.cpu_usage_percent:.1f}%, Mode={metrics.current_mode.value}")
        
        # Phase 2: Wait for load to decrease and trigger scale-down
        logger.info("Phase 2: Waiting for load to decrease and trigger scale-down")
        
        # Stop submitting new tasks and wait
        await asyncio.sleep(120)  # Wait for scale-down cooldown
        
        final_metrics = self.scalability_manager.get_scalability_metrics()
        logger.info(f"Final scaling state: Workers={final_metrics.active_workers}, "
                   f"CPU={final_metrics.cpu_usage_percent:.1f}%")
        
        # Show scaling history
        scaling_history = self.scalability_manager.get_scaling_history()
        logger.info(f"Scaling actions during demo: {len(scaling_history)}")
        for action in scaling_history[-3:]:  # Show last 3 actions
            logger.info(f"  {action['timestamp']}: {action['action']} "
                       f"({action['old_workers']} -> {action['new_workers']} workers)")
    
    async def _demo_graceful_degradation(self) -> None:
        """Demonstrate graceful degradation under extreme load."""
        
        logger.info("=== Demo 4: Graceful Degradation ===")
        
        # Create a very high load to trigger degradation
        logger.info("Creating extreme load to trigger graceful degradation")
        
        # Submit many CPU-intensive tasks rapidly
        extreme_load_tasks = self._create_demo_tasks(
            count=100, 
            task_type="extreme_load", 
            priority=TaskPriority.HIGH
        )
        
        # Submit tasks in rapid succession
        for task in extreme_load_tasks:
            if self.scalability_manager.concurrent_processor:
                await self.scalability_manager.concurrent_processor.submit_task(task)
            await asyncio.sleep(0.01)  # Very small delay
        
        # Monitor degradation modes
        logger.info("Monitoring degradation modes...")
        
        for i in range(12):  # Monitor for 2 minutes
            await asyncio.sleep(10)
            
            metrics = self.scalability_manager.get_scalability_metrics()
            logger.info(f"Degradation monitor ({i*10}s): Mode={metrics.current_mode.value}, "
                       f"Workers={metrics.active_workers}, CPU={metrics.cpu_usage_percent:.1f}%, "
                       f"Memory={metrics.memory_usage_percent:.1f}%")
            
            # Log mode changes
            if metrics.current_mode in [ScalabilityMode.DEGRADED, ScalabilityMode.EMERGENCY]:
                logger.warning(f"System entered {metrics.current_mode.value} mode!")
        
        # Wait for recovery
        logger.info("Waiting for system recovery...")
        await asyncio.sleep(60)
        
        recovery_metrics = self.scalability_manager.get_scalability_metrics()
        logger.info(f"Recovery status: Mode={recovery_metrics.current_mode.value}, "
                   f"Workers={recovery_metrics.active_workers}")
    
    async def _demo_predictive_scaling(self) -> None:
        """Demonstrate predictive scaling capabilities."""
        
        logger.info("=== Demo 5: Predictive Scaling ===")
        
        if not self.config.enable_predictive_scaling:
            logger.info("Predictive scaling is disabled in configuration, skipping demo")
            return
        
        # Create a predictable load pattern
        logger.info("Creating predictable load pattern for ML prediction")
        
        # Simulate a gradual increase in load over time
        for phase in range(5):
            phase_load = (phase + 1) * 10  # Increasing load
            
            phase_tasks = self._create_demo_tasks(
                count=phase_load,
                task_type=f"predictive_phase_{phase}",
                priority=TaskPriority.NORMAL
            )
            
            logger.info(f"Predictive scaling phase {phase + 1}: Submitting {phase_load} tasks")
            
            for task in phase_tasks:
                if self.scalability_manager.concurrent_processor:
                    await self.scalability_manager.concurrent_processor.submit_task(task)
            
            await asyncio.sleep(30)  # Wait between phases
            
            # Check predictions
            metrics = self.scalability_manager.get_scalability_metrics()
            logger.info(f"Phase {phase + 1} predictions: "
                       f"Predicted load 1h={metrics.predicted_load_1h:.1f}%, "
                       f"Recommended workers={metrics.recommended_workers}")
        
        logger.info("Predictive scaling demo completed")
    
    async def _show_final_metrics(self) -> None:
        """Show comprehensive final metrics."""
        
        logger.info("=== Final Metrics Summary ===")
        
        # Get comprehensive metrics
        metrics = self.scalability_manager.get_scalability_metrics()
        scaling_history = self.scalability_manager.get_scaling_history()
        exported_metrics = self.scalability_manager.export_metrics()
        
        logger.info(f"Instance: {metrics.instance_name}")
        logger.info(f"Final Mode: {metrics.current_mode.value}")
        logger.info(f"Active Workers: {metrics.active_workers}")
        logger.info(f"Thread Capacity: {metrics.total_thread_capacity}")
        logger.info(f"Active Threads: {metrics.active_threads}")
        logger.info(f"CPU Usage: {metrics.cpu_usage_percent:.1f}%")
        logger.info(f"Memory Usage: {metrics.memory_usage_percent:.1f}%")
        logger.info(f"Tasks/Second: {metrics.tasks_per_second:.2f}")
        logger.info(f"Error Rate: {metrics.error_rate_percent:.2f}%")
        logger.info(f"Scaling Actions: {len(scaling_history)}")
        logger.info(f"Degradation Events: {metrics.degradation_events}")
        
        if self.config.enable_predictive_scaling:
            logger.info(f"Predicted Load (1h): {metrics.predicted_load_1h:.1f}%")
            logger.info(f"Recommended Workers: {metrics.recommended_workers}")
        
        # Show recent scaling history
        if scaling_history:
            logger.info("Recent Scaling Actions:")
            for action in scaling_history[-5:]:  # Last 5 actions
                logger.info(f"  {action['timestamp']}: {action['action']} "
                           f"({action['old_workers']} -> {action['new_workers']} workers) "
                           f"- {action['trigger']}")
    
    def _create_demo_tasks(self, count: int, task_type: str, priority: TaskPriority) -> List[ProcessingTask]:
        """Create demo tasks for testing."""
        
        tasks = []
        
        for i in range(count):
            task = ProcessingTask(
                task_id=f"{task_type}_{i}_{int(time.time())}",
                instance_name=self.instance_name,
                task_type=task_type,
                priority=priority,
                input_data={"task_number": i, "task_type": task_type},
                processing_function=self._demo_processing_function,
                max_retries=2,
                timeout_seconds=60,
                memory_limit_mb=256
            )
            tasks.append(task)
        
        return tasks
    
    def _demo_processing_function(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Demo processing function that simulates work."""
        
        task_type = input_data.get('task_type', 'unknown')
        task_number = input_data.get('task_number', 0)
        
        # Simulate different processing times based on task type
        if 'extreme_load' in task_type:
            # CPU-intensive task
            processing_time = random.uniform(2.0, 5.0)
        elif 'high_priority' in task_type:
            # Quick task
            processing_time = random.uniform(0.5, 1.0)
        else:
            # Normal task
            processing_time = random.uniform(1.0, 3.0)
        
        # Simulate processing work
        start_time = time.time()
        while time.time() - start_time < processing_time:
            # Simulate CPU work
            _ = sum(i * i for i in range(1000))
        
        return {
            'task_type': task_type,
            'task_number': task_number,
            'processing_time': processing_time,
            'result': f"Processed {task_type} task {task_number}"
        }


async def main():
    """Main function to run the scalability demo."""
    
    parser = argparse.ArgumentParser(description='Scalability Manager Demo')
    parser.add_argument(
        '--instance',
        choices=['ai_scholar', 'quant_scholar'],
        default='ai_scholar',
        help='Instance name to demo (default: ai_scholar)'
    )
    parser.add_argument(
        '--config',
        default='backend/multi_instance_arxiv_system/configs/scalability_config.yaml',
        help='Path to scalability configuration file'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    # Run the demo
    demo = ScalabilityDemo(args.instance, str(config_path))
    
    try:
        await demo.run_demo()
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())