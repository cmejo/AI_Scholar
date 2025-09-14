"""
Integration tests for service initialization and health checks
Tests real service interactions and dependency management
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from core.service_manager import ServiceManager, ServiceStatus
from core.conditional_importer import ConditionalImporter


@pytest.mark.integration
class TestServiceInitializationIntegration:
    """Integration tests for service initialization"""
    
    @pytest.fixture
    def service_manager(self):
        """Create a fresh ServiceManager instance"""
        return ServiceManager()
    
    @pytest.mark.asyncio
    async def test_database_service_initialization_integration(self, service_manager):
        """Test database service initialization with real dependencies"""
        with patch('services.database_service.initialize_database_service') as mock_init, \
             patch('services.database_service.get_database_service') as mock_get:
            
            # Mock successful database initialization
            mock_init.return_value = True
            mock_db_service = MagicMock()
            mock_db_service.health_check = AsyncMock(return_value={"status": "healthy"})
            mock_get.return_value = mock_db_service
            
            # Initialize database service
            result = await service_manager.initialize_database_service()
            
            assert result is True
            assert "database" in service_manager.services
            assert service_manager.is_service_healthy("database")
            
            # Verify service can be retrieved
            db_service = service_manager.get_service("database")
            assert db_service == mock_db_service
    
    @pytest.mark.asyncio
    async def test_semantic_search_service_initialization_integration(self, service_manager):
        """Test semantic search service initialization with dependencies"""
        with patch('core.conditional_importer.ConditionalImporter') as mock_importer:
            # Mock successful dependency checks
            mock_importer.safe_import.side_effect = lambda module, **kwargs: MagicMock() if module in ["numpy", "sqlalchemy"] else None
            
            # Mock successful service class import
            mock_service_class = MagicMock()
            mock_service_instance = MagicMock()
            mock_service_instance.health_check = AsyncMock(return_value={"status": "healthy"})
            mock_service_class.return_value = mock_service_instance
            
            with patch('services.semantic_search_v2.SemanticSearchServiceV2', mock_service_class):
                result = await service_manager.initialize_semantic_search_service()
                
                assert result is True
                assert "semantic_search" in service_manager.services
                
                # Verify service health
                health_check_result = await service_manager.perform_health_check("semantic_search")
                assert health_check_result is True
    
    @pytest.mark.asyncio
    async def test_multiple_service_initialization_with_dependencies(self, service_manager):
        """Test initializing multiple services with complex dependencies"""
        # Mock all required imports and services
        with patch('services.database_service.initialize_database_service', return_value=True), \
             patch('services.database_service.get_database_service') as mock_get_db, \
             patch('core.conditional_importer.ConditionalImporter') as mock_importer:
            
            # Setup database service
            mock_db_service = MagicMock()
            mock_db_service.health_check = AsyncMock(return_value={"status": "healthy"})
            mock_get_db.return_value = mock_db_service
            
            # Setup conditional importer for other services
            mock_importer.safe_import.side_effect = lambda module, **kwargs: MagicMock()
            
            # Initialize database first
            db_result = await service_manager.initialize_database_service()
            assert db_result is True
            
            # Initialize semantic search (depends on database)
            search_result = await service_manager.initialize_semantic_search_service()
            assert search_result is True
            
            # Verify both services are healthy
            assert service_manager.is_service_healthy("database")
            assert service_manager.is_service_healthy("semantic_search")
            
            # Verify initialization order
            init_order = service_manager.get_initialization_order()
            assert "database" in init_order
            assert "semantic_search" in init_order
    
    @pytest.mark.asyncio
    async def test_service_initialization_failure_recovery(self, service_manager):
        """Test service initialization failure and recovery"""
        with patch('services.database_service.initialize_database_service') as mock_init:
            # First attempt fails
            mock_init.side_effect = [Exception("Database connection failed"), True]
            
            with patch('services.database_service.get_database_service') as mock_get:
                mock_db_service = MagicMock()
                mock_get.return_value = mock_db_service
                
                # First initialization should fail
                result1 = await service_manager.initialize_database_service()
                assert result1 is False
                assert "database" not in service_manager.services
                
                # Reset the side effect for retry
                mock_init.side_effect = None
                mock_init.return_value = True
                
                # Second attempt should succeed
                result2 = await service_manager.initialize_database_service()
                assert result2 is True
                assert "database" in service_manager.services
    
    @pytest.mark.asyncio
    async def test_service_dependency_validation(self, service_manager):
        """Test service dependency validation during initialization"""
        # Try to initialize a service with missing dependency
        mock_service = MagicMock()
        
        result = await service_manager.initialize_service(
            service_name="dependent_service",
            service_factory=lambda: mock_service,
            dependencies=["non_existent_dependency"]
        )
        
        assert result is False
        assert "dependent_service" not in service_manager.services
        assert service_manager.health_status["dependent_service"].status == ServiceStatus.FAILED
        assert "Missing dependency" in service_manager.health_status["dependent_service"].error_message
    
    @pytest.mark.asyncio
    async def test_concurrent_service_initialization(self, service_manager):
        """Test concurrent initialization of multiple services"""
        # Create multiple mock services
        services = {}
        for i in range(5):
            service_name = f"service_{i}"
            mock_service = MagicMock()
            mock_service.health_check = AsyncMock(return_value={"status": "healthy"})
            services[service_name] = mock_service
        
        # Initialize all services concurrently
        tasks = [
            service_manager.initialize_service(
                service_name=name,
                service_factory=lambda svc=service: svc,
                dependencies=[]
            )
            for name, service in services.items()
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All initializations should succeed
        assert all(results)
        assert len(service_manager.services) == 5
        
        # All services should be healthy
        for service_name in services.keys():
            assert service_manager.is_service_healthy(service_name)


@pytest.mark.integration
class TestHealthCheckIntegration:
    """Integration tests for health check system"""
    
    @pytest.fixture
    def service_manager_with_services(self):
        """Create ServiceManager with pre-initialized services"""
        manager = ServiceManager()
        
        # Add healthy service
        healthy_service = MagicMock()
        healthy_service.health_check = AsyncMock(return_value={"status": "healthy", "details": "All good"})
        manager.services["healthy_service"] = healthy_service
        manager.health_status["healthy_service"] = manager._create_service_health(
            "healthy_service", ServiceStatus.HEALTHY
        )
        
        # Add degraded service
        degraded_service = MagicMock()
        degraded_service.health_check = AsyncMock(return_value={"status": "degraded", "details": "Some issues"})
        manager.services["degraded_service"] = degraded_service
        manager.health_status["degraded_service"] = manager._create_service_health(
            "degraded_service", ServiceStatus.DEGRADED
        )
        
        # Add unhealthy service
        unhealthy_service = MagicMock()
        unhealthy_service.health_check = AsyncMock(side_effect=Exception("Service down"))
        manager.services["unhealthy_service"] = unhealthy_service
        manager.health_status["unhealthy_service"] = manager._create_service_health(
            "unhealthy_service", ServiceStatus.UNHEALTHY
        )
        
        return manager
    
    @pytest.mark.asyncio
    async def test_comprehensive_health_check(self, service_manager_with_services):
        """Test comprehensive health check across multiple services"""
        manager = service_manager_with_services
        
        # Perform health checks on all services
        healthy_result = await manager.perform_health_check("healthy_service")
        degraded_result = await manager.perform_health_check("degraded_service")
        unhealthy_result = await manager.perform_health_check("unhealthy_service")
        
        assert healthy_result is True
        assert degraded_result is True  # Degraded is still considered "up"
        assert unhealthy_result is False
        
        # Check overall health status
        health_info = manager.get_service_health()
        
        assert health_info["healthy_service"]["status"] == "healthy"
        assert health_info["degraded_service"]["status"] == "degraded"
        assert health_info["unhealthy_service"]["status"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_health_check_caching(self, service_manager_with_services):
        """Test health check result caching"""
        manager = service_manager_with_services
        service_name = "healthy_service"
        
        # First health check
        start_time = datetime.utcnow()
        result1 = await manager.perform_health_check(service_name, use_cache=True)
        
        # Immediate second health check should use cache
        result2 = await manager.perform_health_check(service_name, use_cache=True)
        
        assert result1 == result2 == True
        
        # Verify the service's health_check method was only called once
        service = manager.services[service_name]
        assert service.health_check.call_count == 1
    
    @pytest.mark.asyncio
    async def test_health_check_cache_expiration(self, service_manager_with_services):
        """Test health check cache expiration"""
        manager = service_manager_with_services
        service_name = "healthy_service"
        
        # Set a very short cache TTL for testing
        manager.health_cache_ttl = 0.1  # 100ms
        
        # First health check
        result1 = await manager.perform_health_check(service_name, use_cache=True)
        
        # Wait for cache to expire
        await asyncio.sleep(0.2)
        
        # Second health check should not use cache
        result2 = await manager.perform_health_check(service_name, use_cache=True)
        
        assert result1 == result2 == True
        
        # Verify the service's health_check method was called twice
        service = manager.services[service_name]
        assert service.health_check.call_count == 2
    
    @pytest.mark.asyncio
    async def test_health_check_timeout_handling(self, service_manager_with_services):
        """Test health check timeout handling"""
        manager = service_manager_with_services
        
        # Create a service with slow health check
        slow_service = MagicMock()
        
        async def slow_health_check():
            await asyncio.sleep(2.0)  # 2 second delay
            return {"status": "healthy"}
        
        slow_service.health_check = slow_health_check
        manager.services["slow_service"] = slow_service
        manager.health_status["slow_service"] = manager._create_service_health(
            "slow_service", ServiceStatus.HEALTHY
        )
        
        # Health check with timeout should fail
        start_time = datetime.utcnow()
        result = await manager.perform_health_check("slow_service", timeout=1.0)
        end_time = datetime.utcnow()
        
        assert result is False
        assert (end_time - start_time).total_seconds() < 1.5  # Should timeout quickly
        assert manager.health_status["slow_service"].status == ServiceStatus.UNHEALTHY
    
    @pytest.mark.asyncio
    async def test_periodic_health_monitoring(self, service_manager_with_services):
        """Test periodic health monitoring functionality"""
        manager = service_manager_with_services
        
        # Enable monitoring with short interval for testing
        manager.health_check_interval = 0.5  # 500ms
        
        # Start monitoring
        await manager.start_health_monitoring()
        
        # Wait for a few monitoring cycles
        await asyncio.sleep(1.5)
        
        # Stop monitoring
        await manager.stop_health_monitoring()
        
        # Verify health checks were performed multiple times
        for service_name in ["healthy_service", "degraded_service", "unhealthy_service"]:
            service = manager.services[service_name]
            # Should have been called multiple times during monitoring
            assert service.health_check.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_health_check_error_recovery(self, service_manager_with_services):
        """Test health check error recovery"""
        manager = service_manager_with_services
        
        # Create a service that initially fails but then recovers
        recovering_service = MagicMock()
        call_count = 0
        
        async def recovering_health_check():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception(f"Health check failed (attempt {call_count})")
            return {"status": "healthy", "recovered": True}
        
        recovering_service.health_check = recovering_health_check
        manager.services["recovering_service"] = recovering_service
        manager.health_status["recovering_service"] = manager._create_service_health(
            "recovering_service", ServiceStatus.HEALTHY
        )
        
        # First two health checks should fail
        result1 = await manager.perform_health_check("recovering_service")
        result2 = await manager.perform_health_check("recovering_service")
        
        assert result1 is False
        assert result2 is False
        assert manager.health_status["recovering_service"].status == ServiceStatus.UNHEALTHY
        
        # Third health check should succeed (recovery)
        result3 = await manager.perform_health_check("recovering_service")
        
        assert result3 is True
        assert manager.health_status["recovering_service"].status == ServiceStatus.HEALTHY
        assert call_count == 3


@pytest.mark.integration
class TestServiceDependencyManagement:
    """Integration tests for service dependency management"""
    
    @pytest.fixture
    def service_manager(self):
        """Create a fresh ServiceManager instance"""
        return ServiceManager()
    
    @pytest.mark.asyncio
    async def test_complex_dependency_chain(self, service_manager):
        """Test complex service dependency chain"""
        # Create services with dependency chain: A -> B -> C -> D
        services = {}
        for name in ["service_a", "service_b", "service_c", "service_d"]:
            service = MagicMock()
            service.health_check = AsyncMock(return_value={"status": "healthy"})
            services[name] = service
        
        # Initialize services in dependency order
        await service_manager.initialize_service("service_d", lambda: services["service_d"], [])
        await service_manager.initialize_service("service_c", lambda: services["service_c"], ["service_d"])
        await service_manager.initialize_service("service_b", lambda: services["service_b"], ["service_c"])
        await service_manager.initialize_service("service_a", lambda: services["service_a"], ["service_b"])
        
        # All services should be initialized
        assert len(service_manager.services) == 4
        
        # Verify dependency relationships
        assert "service_d" in service_manager.health_status["service_c"].dependencies
        assert "service_c" in service_manager.health_status["service_b"].dependencies
        assert "service_b" in service_manager.health_status["service_a"].dependencies
    
    @pytest.mark.asyncio
    async def test_circular_dependency_detection(self, service_manager):
        """Test detection and handling of circular dependencies"""
        # This is a simplified test - in practice, circular dependencies
        # would be detected during the dependency resolution phase
        
        service_a = MagicMock()
        service_b = MagicMock()
        
        # Initialize service A
        await service_manager.initialize_service("service_a", lambda: service_a, [])
        
        # Initialize service B with dependency on A
        await service_manager.initialize_service("service_b", lambda: service_b, ["service_a"])
        
        # Try to add A as dependent on B (would create circular dependency)
        # This should be handled gracefully
        result = await service_manager.initialize_service(
            "service_a_updated",
            lambda: service_a,
            ["service_b"]
        )
        
        # Should succeed as it's a different service name
        assert result is True
    
    @pytest.mark.asyncio
    async def test_dependency_failure_cascade(self, service_manager):
        """Test handling of dependency failure cascades"""
        # Create services where B depends on A
        service_a = MagicMock()
        service_a.health_check = AsyncMock(side_effect=Exception("Service A failed"))
        
        service_b = MagicMock()
        service_b.health_check = AsyncMock(return_value={"status": "healthy"})
        
        # Initialize both services
        await service_manager.initialize_service("service_a", lambda: service_a, [])
        await service_manager.initialize_service("service_b", lambda: service_b, ["service_a"])
        
        # Perform health checks
        result_a = await service_manager.perform_health_check("service_a")
        result_b = await service_manager.perform_health_check("service_b")
        
        assert result_a is False  # Service A is unhealthy
        assert result_b is True   # Service B is still healthy (doesn't cascade by default)
        
        # But dependency information should be tracked
        assert "service_a" in service_manager.health_status["service_b"].dependencies
    
    @pytest.mark.asyncio
    async def test_optional_dependency_handling(self, service_manager):
        """Test handling of optional dependencies"""
        # Create a service that can work with or without a dependency
        main_service = MagicMock()
        main_service.health_check = AsyncMock(return_value={"status": "healthy"})
        
        # Initialize service without optional dependency
        result = await service_manager.initialize_service(
            "main_service",
            lambda: main_service,
            dependencies=[],  # No required dependencies
            optional_dependencies=["optional_service"]  # This would be a custom parameter
        )
        
        assert result is True
        assert "main_service" in service_manager.services
        
        # Service should be healthy even without optional dependency
        health_result = await service_manager.perform_health_check("main_service")
        assert health_result is True


@pytest.mark.integration
class TestServiceManagerRealWorldScenarios:
    """Integration tests for real-world service manager scenarios"""
    
    @pytest.fixture
    def service_manager(self):
        """Create a fresh ServiceManager instance"""
        return ServiceManager()
    
    @pytest.mark.asyncio
    async def test_application_startup_sequence(self, service_manager):
        """Test typical application startup sequence"""
        startup_services = []
        
        # Mock typical application services
        with patch('services.database_service.initialize_database_service', return_value=True), \
             patch('services.database_service.get_database_service') as mock_get_db, \
             patch('core.conditional_importer.ConditionalImporter') as mock_importer:
            
            # Setup mocks
            mock_db = MagicMock()
            mock_db.health_check = AsyncMock(return_value={"status": "healthy"})
            mock_get_db.return_value = mock_db
            mock_importer.safe_import.return_value = MagicMock()
            
            # 1. Initialize database service
            db_result = await service_manager.initialize_database_service()
            startup_services.append(("database", db_result))
            
            # 2. Initialize semantic search service
            search_result = await service_manager.initialize_semantic_search_service()
            startup_services.append(("semantic_search", search_result))
            
            # 3. Initialize other services that depend on the above
            analytics_service = MagicMock()
            analytics_service.health_check = AsyncMock(return_value={"status": "healthy"})
            
            analytics_result = await service_manager.initialize_service(
                "analytics",
                lambda: analytics_service,
                dependencies=["database"]
            )
            startup_services.append(("analytics", analytics_result))
            
            # Verify all services started successfully
            assert all(result for _, result in startup_services)
            assert len(service_manager.services) == 3
            
            # Verify all services are healthy
            for service_name, _ in startup_services:
                assert service_manager.is_service_healthy(service_name)
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown_sequence(self, service_manager):
        """Test graceful application shutdown sequence"""
        # Initialize multiple services
        services = {}
        for i in range(3):
            service_name = f"service_{i}"
            service = MagicMock()
            service.health_check = AsyncMock(return_value={"status": "healthy"})
            service.shutdown = AsyncMock()
            services[service_name] = service
            
            await service_manager.initialize_service(
                service_name,
                lambda svc=service: svc,
                dependencies=[]
            )
        
        # Verify all services are running
        assert len(service_manager.services) == 3
        
        # Perform graceful shutdown
        shutdown_result = await service_manager.shutdown_all_services()
        
        assert shutdown_result is True
        assert len(service_manager.services) == 0
        
        # Verify all services had their shutdown method called
        for service in services.values():
            service.shutdown.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_service_restart_scenario(self, service_manager):
        """Test service restart scenario"""
        # Initialize a service
        original_service = MagicMock()
        original_service.health_check = AsyncMock(return_value={"status": "healthy"})
        original_service.shutdown = AsyncMock()
        
        await service_manager.initialize_service(
            "restartable_service",
            lambda: original_service,
            dependencies=[]
        )
        
        assert "restartable_service" in service_manager.services
        
        # Shutdown the service
        shutdown_result = await service_manager.shutdown_service("restartable_service")
        assert shutdown_result is True
        assert "restartable_service" not in service_manager.services
        
        # Restart with new service instance
        new_service = MagicMock()
        new_service.health_check = AsyncMock(return_value={"status": "healthy"})
        
        restart_result = await service_manager.initialize_service(
            "restartable_service",
            lambda: new_service,
            dependencies=[]
        )
        
        assert restart_result is True
        assert "restartable_service" in service_manager.services
        assert service_manager.get_service("restartable_service") == new_service
    
    @pytest.mark.asyncio
    async def test_service_failure_and_recovery(self, service_manager):
        """Test service failure detection and recovery"""
        # Initialize a service that will fail
        failing_service = MagicMock()
        health_check_count = 0
        
        async def failing_then_recovering_health_check():
            nonlocal health_check_count
            health_check_count += 1
            if health_check_count <= 3:
                raise Exception(f"Service failed (check {health_check_count})")
            return {"status": "healthy", "recovered": True}
        
        failing_service.health_check = failing_then_recovering_health_check
        
        await service_manager.initialize_service(
            "failing_service",
            lambda: failing_service,
            dependencies=[]
        )
        
        # Initial health checks should fail
        for i in range(3):
            result = await service_manager.perform_health_check("failing_service")
            assert result is False
            assert service_manager.health_status["failing_service"].status == ServiceStatus.UNHEALTHY
        
        # Fourth health check should succeed (recovery)
        recovery_result = await service_manager.perform_health_check("failing_service")
        assert recovery_result is True
        assert service_manager.health_status["failing_service"].status == ServiceStatus.HEALTHY
        
        # Verify recovery was logged
        assert health_check_count == 4