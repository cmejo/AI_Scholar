"""
Service dependency testing and validation
Tests dependency resolution, validation, and error handling
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from core.service_manager import ServiceManager, ServiceStatus, ServiceHealth


@pytest.mark.unit
class TestServiceDependencyValidation:
    """Test service dependency validation logic"""
    
    @pytest.fixture
    def service_manager(self):
        """Create a fresh ServiceManager instance"""
        return ServiceManager()
    
    def test_validate_dependencies_success(self, service_manager):
        """Test successful dependency validation"""
        # Add a dependency service
        dependency_service = MagicMock()
        service_manager.services["dependency"] = dependency_service
        service_manager.health_status["dependency"] = ServiceHealth(
            name="dependency",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow()
        )
        
        # Validate dependencies
        result = service_manager._validate_dependencies(["dependency"])
        
        assert result is True
    
    def test_validate_dependencies_missing(self, service_manager):
        """Test validation with missing dependencies"""
        # Try to validate non-existent dependency
        result = service_manager._validate_dependencies(["missing_dependency"])
        
        assert result is False
    
    def test_validate_dependencies_multiple_success(self, service_manager):
        """Test validation with multiple dependencies"""
        # Add multiple dependency services
        for i in range(3):
            dep_name = f"dependency_{i}"
            service_manager.services[dep_name] = MagicMock()
            service_manager.health_status[dep_name] = ServiceHealth(
                name=dep_name,
                status=ServiceStatus.HEALTHY,
                last_check=datetime.utcnow()
            )
        
        # Validate all dependencies
        result = service_manager._validate_dependencies([
            "dependency_0", "dependency_1", "dependency_2"
        ])
        
        assert result is True
    
    def test_validate_dependencies_partial_missing(self, service_manager):
        """Test validation with some missing dependencies"""
        # Add one dependency
        service_manager.services["existing"] = MagicMock()
        service_manager.health_status["existing"] = ServiceHealth(
            name="existing",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow()
        )
        
        # Validate with one existing and one missing
        result = service_manager._validate_dependencies(["existing", "missing"])
        
        assert result is False
    
    def test_validate_dependencies_empty_list(self, service_manager):
        """Test validation with empty dependency list"""
        result = service_manager._validate_dependencies([])
        
        assert result is True
    
    def test_validate_dependencies_none(self, service_manager):
        """Test validation with None dependencies"""
        result = service_manager._validate_dependencies(None)
        
        assert result is True
    
    def test_validate_dependencies_unhealthy_service(self, service_manager):
        """Test validation with unhealthy dependency"""
        # Add unhealthy dependency
        service_manager.services["unhealthy"] = MagicMock()
        service_manager.health_status["unhealthy"] = ServiceHealth(
            name="unhealthy",
            status=ServiceStatus.UNHEALTHY,
            last_check=datetime.utcnow(),
            error_message="Service is down"
        )
        
        # Validation should still pass (dependency exists, health is separate concern)
        result = service_manager._validate_dependencies(["unhealthy"])
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_dependency_health_check_cascade(self, service_manager):
        """Test dependency health check cascading"""
        # Create dependency chain: A -> B -> C
        service_c = MagicMock()
        service_c.health_check = AsyncMock(return_value={"status": "healthy"})
        
        service_b = MagicMock()
        service_b.health_check = AsyncMock(return_value={"status": "healthy"})
        
        service_a = MagicMock()
        service_a.health_check = AsyncMock(return_value={"status": "healthy"})
        
        # Initialize services with dependencies
        await service_manager.initialize_service("service_c", lambda: service_c, [])
        await service_manager.initialize_service("service_b", lambda: service_b, ["service_c"])
        await service_manager.initialize_service("service_a", lambda: service_a, ["service_b"])
        
        # Perform health check on top-level service
        result = await service_manager.perform_health_check("service_a", check_dependencies=True)
        
        assert result is True
        
        # All services should have been health checked
        service_a.health_check.assert_called_once()
        service_b.health_check.assert_called_once()
        service_c.health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_dependency_health_check_failure_cascade(self, service_manager):
        """Test dependency health check failure cascading"""
        # Create services where dependency fails
        failing_dependency = MagicMock()
        failing_dependency.health_check = AsyncMock(side_effect=Exception("Dependency failed"))
        
        dependent_service = MagicMock()
        dependent_service.health_check = AsyncMock(return_value={"status": "healthy"})
        
        # Initialize services
        await service_manager.initialize_service("failing_dep", lambda: failing_dependency, [])
        await service_manager.initialize_service("dependent", lambda: dependent_service, ["failing_dep"])
        
        # Health check dependency first
        dep_result = await service_manager.perform_health_check("failing_dep")
        assert dep_result is False
        
        # Health check dependent service
        dependent_result = await service_manager.perform_health_check("dependent")
        
        # Dependent service itself is healthy, but dependency is not
        assert dependent_result is True  # Service itself is healthy
        
        # But we can check if dependencies are healthy
        dep_health = service_manager.is_service_healthy("failing_dep")
        assert dep_health is False


@pytest.mark.unit
class TestServiceDependencyResolution:
    """Test service dependency resolution algorithms"""
    
    @pytest.fixture
    def service_manager(self):
        """Create a fresh ServiceManager instance"""
        return ServiceManager()
    
    def test_resolve_initialization_order_simple(self, service_manager):
        """Test simple dependency order resolution"""
        # Define services with dependencies: B depends on A
        service_definitions = {
            "service_a": [],
            "service_b": ["service_a"]
        }
        
        order = service_manager._resolve_initialization_order(service_definitions)
        
        assert order == ["service_a", "service_b"]
    
    def test_resolve_initialization_order_complex(self, service_manager):
        """Test complex dependency order resolution"""
        # Define services with complex dependencies
        service_definitions = {
            "service_a": [],
            "service_b": ["service_a"],
            "service_c": ["service_a"],
            "service_d": ["service_b", "service_c"],
            "service_e": ["service_d"]
        }
        
        order = service_manager._resolve_initialization_order(service_definitions)
        
        # Verify order constraints
        assert order.index("service_a") < order.index("service_b")
        assert order.index("service_a") < order.index("service_c")
        assert order.index("service_b") < order.index("service_d")
        assert order.index("service_c") < order.index("service_d")
        assert order.index("service_d") < order.index("service_e")
    
    def test_resolve_initialization_order_no_dependencies(self, service_manager):
        """Test order resolution with no dependencies"""
        service_definitions = {
            "service_a": [],
            "service_b": [],
            "service_c": []
        }
        
        order = service_manager._resolve_initialization_order(service_definitions)
        
        # All services should be in the order, exact order doesn't matter
        assert len(order) == 3
        assert set(order) == {"service_a", "service_b", "service_c"}
    
    def test_resolve_initialization_order_circular_dependency(self, service_manager):
        """Test handling of circular dependencies"""
        # Define circular dependency: A -> B -> A
        service_definitions = {
            "service_a": ["service_b"],
            "service_b": ["service_a"]
        }
        
        # Should raise an exception or handle gracefully
        with pytest.raises(ValueError, match="Circular dependency"):
            service_manager._resolve_initialization_order(service_definitions)
    
    def test_resolve_initialization_order_self_dependency(self, service_manager):
        """Test handling of self-dependency"""
        service_definitions = {
            "service_a": ["service_a"]  # Self-dependency
        }
        
        # Should raise an exception or handle gracefully
        with pytest.raises(ValueError, match="Self-dependency"):
            service_manager._resolve_initialization_order(service_definitions)
    
    def test_resolve_initialization_order_missing_dependency(self, service_manager):
        """Test handling of missing dependency in resolution"""
        service_definitions = {
            "service_a": ["missing_service"]
        }
        
        # Should raise an exception for missing dependency
        with pytest.raises(ValueError, match="Missing dependency"):
            service_manager._resolve_initialization_order(service_definitions)
    
    @pytest.mark.asyncio
    async def test_batch_service_initialization_with_order(self, service_manager):
        """Test batch service initialization with proper ordering"""
        # Create mock services
        services = {}
        for name in ["service_a", "service_b", "service_c", "service_d"]:
            service = MagicMock()
            service.health_check = AsyncMock(return_value={"status": "healthy"})
            services[name] = service
        
        # Define service dependencies
        service_definitions = {
            "service_a": [],
            "service_b": ["service_a"],
            "service_c": ["service_a"],
            "service_d": ["service_b", "service_c"]
        }
        
        # Initialize services in batch
        results = await service_manager.initialize_services_batch(service_definitions, services)
        
        # All should succeed
        assert all(results.values())
        
        # Verify initialization order was respected
        init_order = service_manager.get_initialization_order()
        assert init_order.index("service_a") < init_order.index("service_b")
        assert init_order.index("service_a") < init_order.index("service_c")
        assert init_order.index("service_b") < init_order.index("service_d")
        assert init_order.index("service_c") < init_order.index("service_d")


@pytest.mark.unit
class TestServiceDependencyErrorHandling:
    """Test error handling in service dependency management"""
    
    @pytest.fixture
    def service_manager(self):
        """Create a fresh ServiceManager instance"""
        return ServiceManager()
    
    @pytest.mark.asyncio
    async def test_dependency_initialization_failure(self, service_manager):
        """Test handling when dependency initialization fails"""
        # Create a failing dependency
        def failing_factory():
            raise Exception("Dependency initialization failed")
        
        # Try to initialize dependency
        dep_result = await service_manager.initialize_service(
            "failing_dependency",
            failing_factory,
            []
        )
        assert dep_result is False
        
        # Try to initialize service that depends on failed dependency
        dependent_service = MagicMock()
        result = await service_manager.initialize_service(
            "dependent_service",
            lambda: dependent_service,
            ["failing_dependency"]
        )
        
        assert result is False
        assert "dependent_service" not in service_manager.services
    
    @pytest.mark.asyncio
    async def test_dependency_becomes_unhealthy_after_initialization(self, service_manager):
        """Test handling when dependency becomes unhealthy after initialization"""
        # Initialize healthy dependency
        dependency = MagicMock()
        dependency.health_check = AsyncMock(return_value={"status": "healthy"})
        
        await service_manager.initialize_service("dependency", lambda: dependency, [])
        
        # Initialize dependent service
        dependent = MagicMock()
        dependent.health_check = AsyncMock(return_value={"status": "healthy"})
        
        await service_manager.initialize_service("dependent", lambda: dependent, ["dependency"])
        
        # Both should be healthy initially
        assert service_manager.is_service_healthy("dependency")
        assert service_manager.is_service_healthy("dependent")
        
        # Make dependency unhealthy
        dependency.health_check = AsyncMock(side_effect=Exception("Dependency failed"))
        
        # Perform health checks
        dep_health = await service_manager.perform_health_check("dependency")
        dependent_health = await service_manager.perform_health_check("dependent")
        
        assert dep_health is False
        assert dependent_health is True  # Dependent service itself is still healthy
    
    @pytest.mark.asyncio
    async def test_partial_dependency_failure(self, service_manager):
        """Test handling when some dependencies fail"""
        # Initialize multiple dependencies
        good_dep = MagicMock()
        good_dep.health_check = AsyncMock(return_value={"status": "healthy"})
        
        bad_dep = MagicMock()
        bad_dep.health_check = AsyncMock(side_effect=Exception("Bad dependency failed"))
        
        await service_manager.initialize_service("good_dep", lambda: good_dep, [])
        await service_manager.initialize_service("bad_dep", lambda: bad_dep, [])
        
        # Initialize service with both dependencies
        dependent = MagicMock()
        dependent.health_check = AsyncMock(return_value={"status": "healthy"})
        
        result = await service_manager.initialize_service(
            "dependent",
            lambda: dependent,
            ["good_dep", "bad_dep"]
        )
        
        assert result is True  # Should succeed if dependencies exist
        
        # Check health of all services
        good_health = await service_manager.perform_health_check("good_dep")
        bad_health = await service_manager.perform_health_check("bad_dep")
        dependent_health = await service_manager.perform_health_check("dependent")
        
        assert good_health is True
        assert bad_health is False
        assert dependent_health is True
    
    @pytest.mark.asyncio
    async def test_dependency_timeout_handling(self, service_manager):
        """Test handling of dependency timeouts"""
        # Create dependency with slow health check
        slow_dependency = MagicMock()
        
        async def slow_health_check():
            await asyncio.sleep(2.0)  # 2 second delay
            return {"status": "healthy"}
        
        slow_dependency.health_check = slow_health_check
        
        await service_manager.initialize_service("slow_dep", lambda: slow_dependency, [])
        
        # Initialize dependent service
        dependent = MagicMock()
        dependent.health_check = AsyncMock(return_value={"status": "healthy"})
        
        await service_manager.initialize_service("dependent", lambda: dependent, ["slow_dep"])
        
        # Health check with timeout
        dep_health = await service_manager.perform_health_check("slow_dep", timeout=1.0)
        dependent_health = await service_manager.perform_health_check("dependent")
        
        assert dep_health is False  # Should timeout
        assert dependent_health is True  # Dependent service itself is healthy
    
    @pytest.mark.asyncio
    async def test_dependency_recovery_notification(self, service_manager):
        """Test notification when dependencies recover"""
        # Create initially failing dependency
        dependency = MagicMock()
        call_count = 0
        
        async def recovering_health_check():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception(f"Still failing (attempt {call_count})")
            return {"status": "healthy", "recovered": True}
        
        dependency.health_check = recovering_health_check
        
        await service_manager.initialize_service("recovering_dep", lambda: dependency, [])
        
        # Initialize dependent service
        dependent = MagicMock()
        dependent.health_check = AsyncMock(return_value={"status": "healthy"})
        
        await service_manager.initialize_service("dependent", lambda: dependent, ["recovering_dep"])
        
        # Initial health checks should show dependency as unhealthy
        dep_health1 = await service_manager.perform_health_check("recovering_dep")
        dep_health2 = await service_manager.perform_health_check("recovering_dep")
        
        assert dep_health1 is False
        assert dep_health2 is False
        
        # Third health check should show recovery
        dep_health3 = await service_manager.perform_health_check("recovering_dep")
        
        assert dep_health3 is True
        assert service_manager.health_status["recovering_dep"].status == ServiceStatus.HEALTHY


@pytest.mark.integration
class TestServiceDependencyIntegration:
    """Integration tests for service dependency management"""
    
    @pytest.fixture
    def service_manager(self):
        """Create a fresh ServiceManager instance"""
        return ServiceManager()
    
    @pytest.mark.asyncio
    async def test_real_world_service_dependency_scenario(self, service_manager):
        """Test real-world service dependency scenario"""
        # Simulate typical application service dependencies:
        # Database -> (Search, Analytics) -> API Gateway
        
        # Mock database service
        with patch('services.database_service.initialize_database_service', return_value=True), \
             patch('services.database_service.get_database_service') as mock_get_db:
            
            mock_db = MagicMock()
            mock_db.health_check = AsyncMock(return_value={"status": "healthy"})
            mock_get_db.return_value = mock_db
            
            # Initialize database
            db_result = await service_manager.initialize_database_service()
            assert db_result is True
        
        # Mock search service
        with patch('core.conditional_importer.ConditionalImporter') as mock_importer:
            mock_importer.safe_import.return_value = MagicMock()
            
            search_result = await service_manager.initialize_semantic_search_service()
            assert search_result is True
        
        # Initialize analytics service (depends on database)
        analytics_service = MagicMock()
        analytics_service.health_check = AsyncMock(return_value={"status": "healthy"})
        
        analytics_result = await service_manager.initialize_service(
            "analytics",
            lambda: analytics_service,
            ["database"]
        )
        assert analytics_result is True
        
        # Initialize API gateway (depends on search and analytics)
        api_gateway = MagicMock()
        api_gateway.health_check = AsyncMock(return_value={"status": "healthy"})
        
        gateway_result = await service_manager.initialize_service(
            "api_gateway",
            lambda: api_gateway,
            ["semantic_search", "analytics"]
        )
        assert gateway_result is True
        
        # Verify all services are healthy
        all_services = ["database", "semantic_search", "analytics", "api_gateway"]
        for service_name in all_services:
            assert service_manager.is_service_healthy(service_name)
        
        # Verify dependency relationships
        assert "database" in service_manager.health_status["analytics"].dependencies
        assert "semantic_search" in service_manager.health_status["api_gateway"].dependencies
        assert "analytics" in service_manager.health_status["api_gateway"].dependencies
    
    @pytest.mark.asyncio
    async def test_service_dependency_monitoring_cycle(self, service_manager):
        """Test complete dependency monitoring cycle"""
        # Initialize services with dependencies
        base_service = MagicMock()
        base_service.health_check = AsyncMock(return_value={"status": "healthy"})
        
        dependent_service = MagicMock()
        dependent_service.health_check = AsyncMock(return_value={"status": "healthy"})
        
        await service_manager.initialize_service("base", lambda: base_service, [])
        await service_manager.initialize_service("dependent", lambda: dependent_service, ["base"])
        
        # Start monitoring
        service_manager.health_check_interval = 0.5  # 500ms for testing
        await service_manager.start_health_monitoring()
        
        # Let monitoring run for a few cycles
        await asyncio.sleep(1.5)
        
        # Make base service unhealthy
        base_service.health_check = AsyncMock(side_effect=Exception("Base service failed"))
        
        # Let monitoring detect the failure
        await asyncio.sleep(1.0)
        
        # Stop monitoring
        await service_manager.stop_health_monitoring()
        
        # Verify base service is marked as unhealthy
        assert not service_manager.is_service_healthy("base")
        
        # Dependent service should still be healthy (its own health check passes)
        assert service_manager.is_service_healthy("dependent")
        
        # But we can check dependency health separately
        base_health = service_manager.health_status["base"].status
        assert base_health == ServiceStatus.UNHEALTHY