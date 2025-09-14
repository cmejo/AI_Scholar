"""
Comprehensive unit tests for ServiceManager
Tests service initialization, health monitoring, and error handling
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

from core.service_manager import ServiceManager, ServiceStatus, ServiceHealth


@pytest.mark.unit
class TestServiceManager:
    """Test ServiceManager functionality"""
    
    @pytest.fixture
    def service_manager(self):
        """Create a fresh ServiceManager instance for each test"""
        return ServiceManager()
    
    @pytest.fixture
    def mock_service(self):
        """Create a mock service for testing"""
        service = MagicMock()
        service.health_check = AsyncMock(return_value={"status": "healthy"})
        service.get_status = MagicMock(return_value={"status": "healthy"})
        return service
    
    @pytest.fixture
    def failing_service(self):
        """Create a mock service that fails initialization"""
        service = MagicMock()
        service.side_effect = Exception("Service initialization failed")
        return service
    
    def test_service_manager_initialization(self, service_manager):
        """Test ServiceManager initializes correctly"""
        assert isinstance(service_manager.services, dict)
        assert isinstance(service_manager.health_status, dict)
        assert isinstance(service_manager.initialization_order, list)
        assert len(service_manager.services) == 0
        assert len(service_manager.health_status) == 0
        assert service_manager.health_check_interval == 300
        assert service_manager.health_cache_ttl == 60
        assert service_manager.monitoring_enabled is True
    
    @pytest.mark.asyncio
    async def test_initialize_service_success(self, service_manager, mock_service):
        """Test successful service initialization"""
        service_name = "test_service"
        
        def service_factory():
            return mock_service
        
        result = await service_manager.initialize_service(
            service_name=service_name,
            service_factory=service_factory,
            dependencies=[],
            max_retries=1,
            retry_delay=0.1
        )
        
        assert result is True
        assert service_name in service_manager.services
        assert service_name in service_manager.health_status
        assert service_manager.services[service_name] == mock_service
        assert service_manager.health_status[service_name].status == ServiceStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_initialize_service_failure(self, service_manager):
        """Test service initialization failure"""
        service_name = "failing_service"
        
        def failing_factory():
            raise Exception("Service initialization failed")
        
        result = await service_manager.initialize_service(
            service_name=service_name,
            service_factory=failing_factory,
            dependencies=[],
            max_retries=1,
            retry_delay=0.1
        )
        
        assert result is False
        assert service_name not in service_manager.services
        assert service_name in service_manager.health_status
        assert service_manager.health_status[service_name].status == ServiceStatus.FAILED
        assert "Service initialization failed" in service_manager.health_status[service_name].error_message
    
    @pytest.mark.asyncio
    async def test_initialize_service_with_retries(self, service_manager):
        """Test service initialization with retry logic"""
        service_name = "retry_service"
        call_count = 0
        
        def retry_factory():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"Attempt {call_count} failed")
            return MagicMock()
        
        result = await service_manager.initialize_service(
            service_name=service_name,
            service_factory=retry_factory,
            dependencies=[],
            max_retries=3,
            retry_delay=0.1
        )
        
        assert result is True
        assert call_count == 3
        assert service_name in service_manager.services
    
    @pytest.mark.asyncio
    async def test_initialize_service_with_dependencies(self, service_manager, mock_service):
        """Test service initialization with dependencies"""
        # Initialize dependency first
        dependency_name = "dependency_service"
        await service_manager.initialize_service(
            service_name=dependency_name,
            service_factory=lambda: mock_service,
            dependencies=[]
        )
        
        # Initialize service with dependency
        service_name = "dependent_service"
        result = await service_manager.initialize_service(
            service_name=service_name,
            service_factory=lambda: mock_service,
            dependencies=[dependency_name]
        )
        
        assert result is True
        assert service_name in service_manager.services
        assert dependency_name in service_manager.health_status[service_name].dependencies
    
    @pytest.mark.asyncio
    async def test_initialize_service_missing_dependency(self, service_manager, mock_service):
        """Test service initialization with missing dependency"""
        service_name = "dependent_service"
        
        result = await service_manager.initialize_service(
            service_name=service_name,
            service_factory=lambda: mock_service,
            dependencies=["missing_dependency"]
        )
        
        assert result is False
        assert service_name not in service_manager.services
        assert service_name in service_manager.health_status
        assert service_manager.health_status[service_name].status == ServiceStatus.FAILED
    
    def test_get_service(self, service_manager, mock_service):
        """Test getting a service instance"""
        service_name = "test_service"
        service_manager.services[service_name] = mock_service
        
        retrieved_service = service_manager.get_service(service_name)
        assert retrieved_service == mock_service
        
        # Test getting non-existent service
        non_existent = service_manager.get_service("non_existent")
        assert non_existent is None
    
    def test_is_service_healthy(self, service_manager):
        """Test service health checking"""
        service_name = "test_service"
        
        # Test non-existent service
        assert service_manager.is_service_healthy(service_name) is False
        
        # Test healthy service
        service_manager.health_status[service_name] = ServiceHealth(
            name=service_name,
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow()
        )
        assert service_manager.is_service_healthy(service_name) is True
        
        # Test unhealthy service
        service_manager.health_status[service_name].status = ServiceStatus.UNHEALTHY
        assert service_manager.is_service_healthy(service_name) is False
    
    def test_get_service_health(self, service_manager):
        """Test getting service health information"""
        service_name = "test_service"
        health = ServiceHealth(
            name=service_name,
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow(),
            dependencies=["dep1", "dep2"]
        )
        service_manager.health_status[service_name] = health
        
        health_info = service_manager.get_service_health()
        
        assert isinstance(health_info, dict)
        assert service_name in health_info
        assert health_info[service_name]["status"] == "healthy"
        assert health_info[service_name]["dependencies"] == ["dep1", "dep2"]
    
    @pytest.mark.asyncio
    async def test_check_service_health(self, service_manager, mock_service):
        """Test performing health check on a service"""
        service_name = "test_service"
        service_manager.services[service_name] = mock_service
        service_manager.health_status[service_name] = ServiceHealth(
            name=service_name,
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow() - timedelta(minutes=10)  # Old check
        )
        
        # Mock health check response
        mock_service.health_check.return_value = {"status": "healthy", "details": "All good"}
        
        health = await service_manager.check_service_health(service_name)
        
        assert health.status == ServiceStatus.HEALTHY
        mock_service.health_check.assert_called_once()
        assert service_manager.health_status[service_name].status == ServiceStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_perform_health_check_failure(self, service_manager, mock_service):
        """Test health check failure handling"""
        service_name = "test_service"
        service_manager.services[service_name] = mock_service
        service_manager.health_status[service_name] = ServiceHealth(
            name=service_name,
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow()
        )
        
        # Mock health check failure
        mock_service.health_check.side_effect = Exception("Health check failed")
        
        health = await service_manager.check_service_health(service_name)
        result = health.status == ServiceStatus.HEALTHY
        
        assert result is False
        assert service_manager.health_status[service_name].status == ServiceStatus.UNHEALTHY
        assert "Health check failed" in service_manager.health_status[service_name].error_message
    
    @pytest.mark.asyncio
    async def test_perform_health_check_cached(self, service_manager, mock_service):
        """Test health check caching"""
        service_name = "test_service"
        service_manager.services[service_name] = mock_service
        
        # Set recent health check
        recent_health = ServiceHealth(
            name=service_name,
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow()
        )
        service_manager.health_status[service_name] = recent_health
        service_manager.health_cache[service_name] = (recent_health, datetime.utcnow())
        
        health = await service_manager.check_service_health(service_name, use_cache=True)
        result = health.status == ServiceStatus.HEALTHY
        
        assert result is True
        # Should not call health_check due to cache
        mock_service.health_check.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_initialize_database_service_success(self, service_manager):
        """Test successful database service initialization"""
        with patch('services.database_service.initialize_database_service') as mock_init, \
             patch('services.database_service.get_database_service') as mock_get:
            
            mock_init.return_value = True
            mock_db_service = MagicMock()
            mock_get.return_value = mock_db_service
            
            result = await service_manager.initialize_database_service()
            
            assert result is True
            mock_init.assert_called_once()
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_database_service_import_failure(self, service_manager):
        """Test database service initialization with import failure"""
        with patch('services.database_service.initialize_database_service', side_effect=ImportError("Module not found")):
            result = await service_manager.initialize_database_service()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_initialize_database_service_timeout(self, service_manager):
        """Test database service initialization timeout"""
        with patch('services.database_service.initialize_database_service') as mock_init:
            # Simulate timeout
            async def slow_init():
                await asyncio.sleep(70)  # Longer than 60s timeout
                return True
            
            mock_init.side_effect = slow_init
            
            result = await service_manager.initialize_database_service()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_initialize_semantic_search_service_success(self, service_manager):
        """Test successful semantic search service initialization"""
        with patch('core.conditional_importer.ConditionalImporter') as mock_importer:
            
            # Mock successful dependency checks and service class
            def mock_safe_import(module, **kwargs):
                if module in ["numpy", "sqlalchemy"]:
                    return MagicMock()
                elif "semantic_search_v2" in module:
                    mock_service_class = MagicMock()
                    mock_service_instance = MagicMock()
                    mock_service_class.return_value = mock_service_instance
                    return mock_service_class
                return None
            
            mock_importer.safe_import.side_effect = mock_safe_import
            
            result = await service_manager.initialize_semantic_search_service()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_initialize_semantic_search_service_missing_dependencies(self, service_manager):
        """Test semantic search service initialization with missing dependencies"""
        with patch('core.conditional_importer.ConditionalImporter') as mock_importer:
            # Mock missing numpy dependency
            mock_importer.safe_import.side_effect = lambda module, **kwargs: None if module == "numpy" else MagicMock()
            
            result = await service_manager.initialize_semantic_search_service()
            
            assert result is True  # Should fallback to mock service
            assert "semantic_search" in service_manager.services
            # Should be mock service
            service = service_manager.get_service("semantic_search")
            assert hasattr(service, 'logger')  # Mock service has logger
    
    def test_list_services(self, service_manager, mock_service):
        """Test listing all services"""
        service_manager.services["service1"] = mock_service
        service_manager.services["service2"] = mock_service
        
        services = service_manager.list_services()
        
        assert isinstance(services, list)
        assert "service1" in services
        assert "service2" in services
        assert len(services) == 2
    
    def test_get_initialization_order(self, service_manager):
        """Test getting service initialization order"""
        service_manager.initialization_order = ["service1", "service2", "service3"]
        
        order = service_manager.get_initialization_order()
        
        assert order == ["service1", "service2", "service3"]
    
    @pytest.mark.asyncio
    async def test_shutdown_service(self, service_manager, mock_service):
        """Test shutting down a service"""
        service_name = "test_service"
        service_manager.services[service_name] = mock_service
        service_manager.health_status[service_name] = ServiceHealth(
            name=service_name,
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow()
        )
        
        # Add shutdown method to mock service
        mock_service.shutdown = AsyncMock()
        
        result = await service_manager.shutdown_service(service_name)
        
        assert result is True
        assert service_name not in service_manager.services
        mock_service.shutdown.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_shutdown_all_services(self, service_manager, mock_service):
        """Test shutting down all services"""
        # Add multiple services
        for i in range(3):
            service_name = f"service_{i}"
            mock_svc = MagicMock()
            mock_svc.shutdown = AsyncMock()
            service_manager.services[service_name] = mock_svc
            service_manager.health_status[service_name] = ServiceHealth(
                name=service_name,
                status=ServiceStatus.HEALTHY,
                last_check=datetime.utcnow()
            )
        
        result = await service_manager.shutdown_all_services()
        
        assert result is True
        assert len(service_manager.services) == 0
        
        # Verify all services were shut down
        for service in service_manager.services.values():
            if hasattr(service, 'shutdown'):
                service.shutdown.assert_called_once()


@pytest.mark.unit
class TestServiceManagerIntegration:
    """Integration tests for ServiceManager with multiple services"""
    
    @pytest.fixture
    def service_manager(self):
        """Create a fresh ServiceManager instance"""
        return ServiceManager()
    
    @pytest.mark.asyncio
    async def test_multiple_service_initialization(self, service_manager):
        """Test initializing multiple services with dependencies"""
        # Create mock services
        database_service = MagicMock()
        search_service = MagicMock()
        analytics_service = MagicMock()
        
        # Initialize services in dependency order
        result1 = await service_manager.initialize_service(
            service_name="database",
            service_factory=lambda: database_service,
            dependencies=[]
        )
        
        result2 = await service_manager.initialize_service(
            service_name="search",
            service_factory=lambda: search_service,
            dependencies=["database"]
        )
        
        result3 = await service_manager.initialize_service(
            service_name="analytics",
            service_factory=lambda: analytics_service,
            dependencies=["database", "search"]
        )
        
        assert all([result1, result2, result3])
        assert len(service_manager.services) == 3
        assert service_manager.health_status["analytics"].dependencies == ["database", "search"]
    
    @pytest.mark.asyncio
    async def test_service_failure_cascade(self, service_manager):
        """Test handling of service failure cascades"""
        # Initialize base service successfully
        base_service = MagicMock()
        await service_manager.initialize_service(
            service_name="base",
            service_factory=lambda: base_service,
            dependencies=[]
        )
        
        # Try to initialize dependent service that fails
        def failing_factory():
            raise Exception("Dependent service failed")
        
        result = await service_manager.initialize_service(
            service_name="dependent",
            service_factory=failing_factory,
            dependencies=["base"]
        )
        
        assert result is False
        assert "base" in service_manager.services  # Base service should remain
        assert "dependent" not in service_manager.services
        assert service_manager.health_status["dependent"].status == ServiceStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_concurrent_service_initialization(self, service_manager):
        """Test concurrent service initialization"""
        services = {}
        for i in range(5):
            services[f"service_{i}"] = MagicMock()
        
        # Initialize services concurrently
        tasks = [
            service_manager.initialize_service(
                service_name=name,
                service_factory=lambda svc=service: svc,
                dependencies=[]
            )
            for name, service in services.items()
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert all(results)
        assert len(service_manager.services) == 5
        
        # All services should be healthy
        for name in services.keys():
            assert service_manager.is_service_healthy(name)
    
    @pytest.mark.asyncio
    async def test_health_monitoring_cycle(self, service_manager):
        """Test complete health monitoring cycle"""
        # Initialize services
        healthy_service = MagicMock()
        healthy_service.health_check = AsyncMock(return_value={"status": "healthy"})
        
        unhealthy_service = MagicMock()
        unhealthy_service.health_check = AsyncMock(side_effect=Exception("Service down"))
        
        await service_manager.initialize_service("healthy", lambda: healthy_service, [])
        await service_manager.initialize_service("unhealthy", lambda: unhealthy_service, [])
        
        # Perform health checks
        healthy_health = await service_manager.check_service_health("healthy")
        unhealthy_health = await service_manager.check_service_health("unhealthy")
        
        healthy_result = healthy_health.status == ServiceStatus.HEALTHY
        unhealthy_result = unhealthy_health.status == ServiceStatus.HEALTHY
        
        assert healthy_result is True
        assert unhealthy_result is False
        
        # Check overall health status
        health_info = service_manager.get_service_health()
        assert health_info["healthy"]["status"] == "healthy"
        assert health_info["unhealthy"]["status"] == "unhealthy"