#!/usr/bin/env python3
"""
Test script to verify service status monitoring functionality
"""
import asyncio
import sys
import os
import logging
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.service_manager import ServiceManager, ServiceStatus, ServiceHealth


class MockService:
    """Mock service for testing"""
    def __init__(self, name: str, should_fail: bool = False):
        self.name = name
        self.should_fail = should_fail
        self.health_check_count = 0
    
    async def health_check(self):
        """Mock health check method"""
        self.health_check_count += 1
        if self.should_fail:
            raise Exception(f"Mock service {self.name} health check failed")
        return True


class FailingService:
    """Service that fails during initialization"""
    def __init__(self):
        raise Exception("Service initialization failed")


async def test_service_monitoring():
    """Test service status monitoring functionality"""
    print("Testing Service Status Monitoring")
    print("=" * 50)
    
    # Create a new service manager for testing
    service_manager = ServiceManager()
    
    # Configure monitoring for faster testing
    service_manager.configure_health_monitoring(
        interval=5,  # 5 seconds for testing
        cache_ttl=2,  # 2 seconds cache TTL
        enabled=True
    )
    
    print("1. Testing service initialization and health tracking...")
    
    # Test successful service initialization
    mock_service_1 = MockService("test_service_1")
    success = await service_manager.initialize_service(
        "test_service_1",
        lambda: mock_service_1
    )
    print(f"   Service 1 initialization: {'SUCCESS' if success else 'FAILED'}")
    
    # Test service with dependencies
    mock_service_2 = MockService("test_service_2")
    success = await service_manager.initialize_service(
        "test_service_2",
        lambda: mock_service_2,
        dependencies=["test_service_1"]
    )
    print(f"   Service 2 initialization (with deps): {'SUCCESS' if success else 'FAILED'}")
    
    # Test failing service initialization
    success = await service_manager.initialize_service(
        "failing_service",
        FailingService
    )
    print(f"   Failing service initialization: {'FAILED' if not success else 'UNEXPECTED SUCCESS'}")
    
    print("\n2. Testing health status tracking...")
    
    # Get health status
    health_status = service_manager.get_service_health()
    print(f"   Total services tracked: {len(health_status)}")
    
    for service_name, health in health_status.items():
        print(f"   {service_name}: {health['status']} (last check: {health['last_check']})")
    
    print("\n3. Testing individual service health checks...")
    
    # Test individual health check
    health = await service_manager.check_service_health("test_service_1")
    print(f"   Service 1 health check: {health.status.value}")
    print(f"   Health check count: {mock_service_1.health_check_count}")
    
    # Test cached health check
    health_cached = await service_manager.check_service_health("test_service_1", use_cache=True)
    print(f"   Service 1 cached health check: {health_cached.status.value}")
    print(f"   Health check count (should be same): {mock_service_1.health_check_count}")
    
    print("\n4. Testing health check caching...")
    
    # Wait for cache to expire
    await asyncio.sleep(3)
    
    # Check again - should perform new health check
    health_fresh = await service_manager.check_service_health("test_service_1", use_cache=True)
    print(f"   Service 1 fresh health check: {health_fresh.status.value}")
    print(f"   Health check count (should be incremented): {mock_service_1.health_check_count}")
    
    print("\n5. Testing all services health check...")
    
    # Test all services health check
    all_health = await service_manager.check_all_services_health()
    print(f"   All services health check completed: {len(all_health)} services")
    
    for service_name, health in all_health.items():
        print(f"   {service_name}: {health.status.value}")
    
    print("\n6. Testing health monitoring status...")
    
    # Get monitoring status
    monitoring_status = service_manager.get_health_monitoring_status()
    print(f"   Monitoring enabled: {monitoring_status['monitoring_enabled']}")
    print(f"   Health check interval: {monitoring_status['health_check_interval']}s")
    print(f"   Cache TTL: {monitoring_status['cache_ttl']}s")
    print(f"   Cached services: {len(monitoring_status['cached_services'])}")
    
    print("\n7. Testing periodic health monitoring...")
    
    # Start health monitoring
    await service_manager.start_health_monitoring()
    print("   Health monitoring started")
    
    # Wait for a few monitoring cycles
    print("   Waiting for monitoring cycles...")
    await asyncio.sleep(12)  # Wait for 2+ monitoring cycles
    
    # Check health status after monitoring
    health_after_monitoring = service_manager.get_service_health()
    print("   Health status after monitoring:")
    for service_name, health in health_after_monitoring.items():
        print(f"   {service_name}: {health['status']} (last check: {health['last_check']})")
    
    # Stop health monitoring
    await service_manager.stop_health_monitoring()
    print("   Health monitoring stopped")
    
    print("\n8. Testing service with health check failures...")
    
    # Add a service that will fail health checks
    failing_health_service = MockService("failing_health_service", should_fail=True)
    success = await service_manager.initialize_service(
        "failing_health_service",
        lambda: failing_health_service
    )
    print(f"   Failing health service initialization: {'SUCCESS' if success else 'FAILED'}")
    
    # Perform health check on failing service
    health = await service_manager.check_service_health("failing_health_service")
    print(f"   Failing service health check: {health.status.value}")
    print(f"   Error message: {health.error_message}")
    
    print("\n9. Testing initialization summary...")
    
    # Get initialization summary
    summary = service_manager.get_initialization_summary()
    print(f"   Total services: {summary['total_services']}")
    print(f"   Healthy services: {summary['healthy_services']}")
    print(f"   Failed services: {summary['failed_services']}")
    print(f"   Overall health: {summary['overall_health']}")
    print(f"   Initialization order: {summary['initialization_order']}")
    
    print("\n" + "=" * 50)
    print("Service Status Monitoring Test Complete!")
    
    return True


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the test
    try:
        result = asyncio.run(test_service_monitoring())
        if result:
            print("\n✅ All service monitoring tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some service monitoring tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)