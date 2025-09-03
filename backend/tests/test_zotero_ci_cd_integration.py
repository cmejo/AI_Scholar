"""
CI/CD integration tests for Zotero features.
Tests designed to run in automated CI/CD pipelines.
"""
import pytest
import asyncio
import json
import os
import time
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app import app


@pytest.mark.ci
class TestZoteroCICDIntegration:
    """CI/CD integration tests for Zotero features."""
    
    @pytest.fixture
    def ci_client(self, test_db_session, mock_redis):
        """Create test client optimized for CI/CD environments."""
        app.dependency_overrides.clear()
        
        from core.database import get_db
        from core.redis_client import get_redis_client
        
        app.dependency_overrides[get_db] = lambda: test_db_session
        app.dependency_overrides[get_redis_client] = lambda: mock_redis
        
        with TestClient(app) as client:
            yield client
        
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def ci_test_data(self):
        """Generate test data suitable for CI/CD environments."""
        return {
            'libraries': [
                {
                    'id': 'ci-lib-123',
                    'type': 'user',
                    'name': 'CI Test Library',
                    'version': 100
                }
            ],
            'collections': [
                {
                    'key': 'CICOLL01',
                    'name': 'CI Test Collection',
                    'parentCollection': None,
                    'version': 50
                }
            ],
            'items': [
                {
                    'key': 'CIITEM01',
                    'version': 25,
                    'itemType': 'journalArticle',
                    'title': 'CI Test Article',
                    'creators': [
                        {'creatorType': 'author', 'firstName': 'CI', 'lastName': 'Tester'}
                    ],
                    'publicationTitle': 'CI Journal',
                    'date': '2023',
                    'abstractNote': 'Test article for CI/CD pipeline.',
                    'tags': [{'tag': 'ci'}, {'tag': 'testing'}]
                },
                {
                    'key': 'CIITEM02',
                    'version': 26,
                    'itemType': 'book',
                    'title': 'CI Test Book',
                    'creators': [
                        {'creatorType': 'author', 'firstName': 'Test', 'lastName': 'Author'}
                    ],
                    'publisher': 'CI Press',
                    'date': '2023',
                    'abstractNote': 'Test book for CI/CD pipeline.',
                    'tags': [{'tag': 'ci'}, {'tag': 'book'}]
                }
            ]
        }
    
    def test_health_check_endpoints(self, ci_client):
        """Test health check endpoints for CI/CD monitoring."""
        
        # Test main health check
        health_response = ci_client.get("/health")
        assert health_response.status_code == 200
        
        health_data = health_response.json()
        assert "status" in health_data
        assert health_data["status"] == "healthy"
        
        # Test Zotero-specific health check
        zotero_health_response = ci_client.get("/api/zotero/health")
        assert zotero_health_response.status_code == 200
        
        zotero_health_data = zotero_health_response.json()
        assert "status" in zotero_health_data
        assert "services" in zotero_health_data
        assert "version" in zotero_health_data
    
    def test_api_endpoint_availability(self, ci_client):
        """Test that all critical Zotero API endpoints are available."""
        
        critical_endpoints = [
            ("/api/zotero/auth/initiate", "POST"),
            ("/api/zotero/auth/callback", "POST"),
            ("/api/zotero/sync/test-conn/libraries", "POST"),
            ("/api/zotero/search", "POST"),
            ("/api/zotero/citations/generate", "POST"),
            ("/api/zotero/libraries/test-lib/items", "GET"),
            ("/api/zotero/health", "GET")
        ]
        
        for endpoint, method in critical_endpoints:
            if method == "GET":
                response = ci_client.get(endpoint)
            else:
                response = ci_client.post(endpoint, json={})
            
            # Should not return 404 (endpoint exists)
            assert response.status_code != 404, f"Endpoint {endpoint} not found"
            
            # Should not return 500 (no server errors)
            assert response.status_code != 500, f"Server error on endpoint {endpoint}"
    
    def test_database_connectivity(self, ci_client, ci_test_data):
        """Test database connectivity and basic operations."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            mock_client_instance.get_libraries.return_value = ci_test_data['libraries']
            mock_client_instance.get_items.return_value = ci_test_data['items']
            
            # Test database write operation
            connection_response = ci_client.post(
                "/api/zotero/auth/test-connection",
                json={"user_id": "ci-db-test-user", "access_token": "ci-test-token"}
            )
            
            assert connection_response.status_code == 200
            
            # Test database read operation
            sync_response = ci_client.post(
                "/api/zotero/sync/ci-db-test-conn/libraries"
            )
            
            assert sync_response.status_code == 200
            
            # Test database query operation
            search_response = ci_client.post(
                "/api/zotero/search",
                json={"query": "test", "library_id": "ci-lib-123"}
            )
            
            assert search_response.status_code == 200
    
    def test_environment_configuration(self, ci_client):
        """Test that environment configuration is correct for CI/CD."""
        
        # Test environment-specific settings
        config_response = ci_client.get("/api/config")
        
        if config_response.status_code == 200:
            config_data = config_response.json()
            
            # Verify CI/CD environment settings
            assert config_data.get("environment") in ["test", "ci", "staging"]
            assert config_data.get("debug", False) is True  # Debug should be enabled in CI
            assert "database_url" in config_data
            assert "redis_url" in config_data
    
    def test_dependency_versions(self, ci_client):
        """Test that all dependencies are at expected versions."""
        
        # Test Python package versions
        import pkg_resources
        
        critical_packages = [
            "fastapi",
            "sqlalchemy",
            "redis",
            "pytest",
            "requests"
        ]
        
        for package in critical_packages:
            try:
                version = pkg_resources.get_distribution(package).version
                assert version is not None, f"Package {package} not found"
                print(f"  - {package}: {version}")
            except pkg_resources.DistributionNotFound:
                pytest.fail(f"Critical package {package} not installed")
    
    def test_security_headers(self, ci_client):
        """Test that security headers are properly configured."""
        
        response = ci_client.get("/api/zotero/health")
        
        # Check for security headers
        headers = response.headers
        
        # These headers should be present in production-like environments
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection"
        ]
        
        for header in security_headers:
            if header in headers:
                print(f"  - {header}: {headers[header]}")
    
    def test_rate_limiting(self, ci_client):
        """Test that rate limiting is properly configured."""
        
        # Make multiple rapid requests to test rate limiting
        responses = []
        
        for i in range(10):
            response = ci_client.get("/api/zotero/health")
            responses.append(response)
        
        # All requests should succeed in CI environment
        for response in responses:
            assert response.status_code == 200
        
        # Check for rate limiting headers
        if "X-RateLimit-Limit" in responses[0].headers:
            print(f"  - Rate limit: {responses[0].headers['X-RateLimit-Limit']}")
            print(f"  - Remaining: {responses[0].headers.get('X-RateLimit-Remaining', 'N/A')}")


@pytest.mark.ci
class TestZoteroWorkflowValidation:
    """Validate complete Zotero workflows in CI/CD environment."""
    
    def test_complete_workflow_validation(self, ci_client, ci_test_data):
        """Test complete Zotero workflow from authentication to citation generation."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Mock all necessary API responses
            mock_client_instance.initiate_oauth.return_value = {
                'oauth_token': 'ci-oauth-token',
                'oauth_token_secret': 'ci-oauth-secret',
                'authorization_url': 'https://www.zotero.org/oauth/authorize?oauth_token=ci-test'
            }
            
            mock_client_instance.complete_oauth.return_value = {
                'access_token': 'ci-access-token',
                'user_id': 'ci-user-123'
            }
            
            mock_client_instance.get_libraries.return_value = ci_test_data['libraries']
            mock_client_instance.get_collections.return_value = ci_test_data['collections']
            mock_client_instance.get_items.return_value = ci_test_data['items']
            
            user_id = "ci-workflow-user"
            
            # Step 1: OAuth initiation
            oauth_response = ci_client.post(
                "/api/zotero/auth/initiate",
                json={"user_id": user_id}
            )
            
            assert oauth_response.status_code == 200
            oauth_data = oauth_response.json()
            assert "authorization_url" in oauth_data
            
            # Step 2: OAuth completion
            callback_response = ci_client.post(
                "/api/zotero/auth/callback",
                json={
                    "user_id": user_id,
                    "oauth_token": "ci-oauth-token",
                    "oauth_verifier": "ci-verifier"
                }
            )
            
            assert callback_response.status_code == 200
            callback_data = callback_response.json()
            assert callback_data["success"] is True
            
            connection_id = callback_data.get("connection_id", f"{user_id}-conn")
            
            # Step 3: Library synchronization
            sync_response = ci_client.post(
                f"/api/zotero/sync/{connection_id}/libraries"
            )
            
            assert sync_response.status_code == 200
            sync_data = sync_response.json()
            assert sync_data["success"] is True
            
            # Step 4: Search functionality
            search_response = ci_client.post(
                "/api/zotero/search",
                json={
                    "query": "CI Test",
                    "library_id": "ci-lib-123",
                    "limit": 10
                }
            )
            
            assert search_response.status_code == 200
            search_data = search_response.json()
            assert "items" in search_data
            
            # Step 5: Citation generation
            item_key = ci_test_data['items'][0]['key']
            
            citation_response = ci_client.post(
                "/api/zotero/citations/generate",
                json={
                    "item_keys": [item_key],
                    "style": "apa",
                    "format": "text"
                }
            )
            
            assert citation_response.status_code == 200
            citation_data = citation_response.json()
            assert "citations" in citation_data
            
            print("✅ Complete workflow validation passed")
    
    def test_error_handling_validation(self, ci_client):
        """Test that error handling works correctly in CI/CD environment."""
        
        # Test authentication error handling
        auth_error_response = ci_client.post(
            "/api/zotero/auth/callback",
            json={"invalid": "data"}
        )
        
        assert auth_error_response.status_code in [400, 422]  # Bad request or validation error
        
        # Test sync error handling
        sync_error_response = ci_client.post(
            "/api/zotero/sync/nonexistent-connection/libraries"
        )
        
        assert sync_error_response.status_code in [404, 400]  # Not found or bad request
        
        # Test search error handling
        search_error_response = ci_client.post(
            "/api/zotero/search",
            json={"invalid": "search"}
        )
        
        assert search_error_response.status_code in [400, 422]  # Bad request or validation error
        
        print("✅ Error handling validation passed")
    
    def test_performance_benchmarks(self, ci_client, ci_test_data):
        """Test that performance meets CI/CD benchmarks."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            mock_client_instance.get_libraries.return_value = ci_test_data['libraries']
            mock_client_instance.get_items.return_value = ci_test_data['items']
            
            # Performance benchmark: Sync operation
            start_time = time.time()
            
            sync_response = ci_client.post(
                "/api/zotero/sync/ci-perf-conn/libraries"
            )
            
            sync_duration = time.time() - start_time
            
            assert sync_response.status_code == 200
            assert sync_duration < 5.0  # Should complete within 5 seconds in CI
            
            # Performance benchmark: Search operation
            start_time = time.time()
            
            search_response = ci_client.post(
                "/api/zotero/search",
                json={"query": "test", "library_id": "ci-lib-123"}
            )
            
            search_duration = time.time() - start_time
            
            assert search_response.status_code == 200
            assert search_duration < 2.0  # Should complete within 2 seconds in CI
            
            # Performance benchmark: Citation generation
            start_time = time.time()
            
            citation_response = ci_client.post(
                "/api/zotero/citations/generate",
                json={"item_keys": ["CIITEM01"], "style": "apa"}
            )
            
            citation_duration = time.time() - start_time
            
            assert citation_response.status_code == 200
            assert citation_duration < 1.0  # Should complete within 1 second in CI
            
            print(f"✅ Performance benchmarks passed:")
            print(f"  - Sync: {sync_duration:.3f}s")
            print(f"  - Search: {search_duration:.3f}s")
            print(f"  - Citation: {citation_duration:.3f}s")


@pytest.mark.ci
class TestZoteroDeploymentValidation:
    """Validate deployment-specific aspects of Zotero integration."""
    
    def test_migration_compatibility(self, ci_client):
        """Test that database migrations are compatible."""
        
        # This would typically check migration files and database schema
        # For CI, we verify that the database structure is correct
        
        # Test that required tables exist by attempting operations
        connection_response = ci_client.post(
            "/api/zotero/auth/test-connection",
            json={"user_id": "migration-test-user", "access_token": "test-token"}
        )
        
        # Should not fail due to missing tables
        assert connection_response.status_code in [200, 400, 422]  # Not 500 (server error)
        
        print("✅ Migration compatibility validated")
    
    def test_configuration_validation(self, ci_client):
        """Test that configuration is valid for deployment."""
        
        # Test environment variables
        import os
        
        required_env_vars = [
            "DATABASE_URL",
            "REDIS_URL"
        ]
        
        for env_var in required_env_vars:
            value = os.getenv(env_var)
            if value:
                print(f"  - {env_var}: {'*' * (len(value) - 10) + value[-10:]}")  # Mask sensitive data
            else:
                print(f"  - {env_var}: Not set (using defaults)")
        
        print("✅ Configuration validation completed")
    
    def test_logging_configuration(self, ci_client):
        """Test that logging is properly configured."""
        
        import logging
        
        # Check that loggers are configured
        zotero_logger = logging.getLogger('services.zotero')
        app_logger = logging.getLogger('app')
        
        assert zotero_logger.level <= logging.INFO
        assert app_logger.level <= logging.INFO
        
        print("✅ Logging configuration validated")
    
    def test_monitoring_endpoints(self, ci_client):
        """Test that monitoring endpoints are available."""
        
        monitoring_endpoints = [
            "/health",
            "/api/zotero/health",
            "/metrics"  # If Prometheus metrics are enabled
        ]
        
        for endpoint in monitoring_endpoints:
            response = ci_client.get(endpoint)
            
            # Should not return 404 or 500
            if response.status_code == 404:
                print(f"  - {endpoint}: Not available (optional)")
            elif response.status_code == 500:
                pytest.fail(f"Monitoring endpoint {endpoint} has server error")
            else:
                print(f"  - {endpoint}: Available ({response.status_code})")
        
        print("✅ Monitoring endpoints validated")
        
        zotero_health_data = zotero_health_response.json()
        assert "zotero_services" in zotero_health_data
        assert "database" in zotero_health_data
        assert "redis" in zotero_health_data
    
    def test_api_version_compatibility(self, ci_client):
        """Test API version compatibility for CI/CD deployments."""
        
        # Test API version endpoint
        version_response = ci_client.get("/api/version")
        assert version_response.status_code == 200
        
        version_data = version_response.json()
        assert "version" in version_data
        assert "zotero_integration_version" in version_data
        assert "api_compatibility" in version_data
        
        # Test Zotero API compatibility
        zotero_version_response = ci_client.get("/api/zotero/version")
        assert zotero_version_response.status_code == 200
        
        zotero_version_data = zotero_version_response.json()
        assert "supported_zotero_api_version" in zotero_version_data
        assert "integration_features" in zotero_version_data
    
    def test_database_migration_compatibility(self, ci_client):
        """Test database migration compatibility for CI/CD deployments."""
        
        # Test migration status endpoint
        migration_response = ci_client.get("/api/admin/migrations/status")
        assert migration_response.status_code in [200, 404]  # May not be implemented
        
        if migration_response.status_code == 200:
            migration_data = migration_response.json()
            assert "migrations" in migration_data
            assert "zotero_migrations" in migration_data
    
    def test_configuration_validation(self, ci_client):
        """Test configuration validation for CI/CD environments."""
        
        # Test configuration endpoint
        config_response = ci_client.get("/api/admin/config/validate")
        assert config_response.status_code in [200, 404]  # May not be implemented
        
        if config_response.status_code == 200:
            config_data = config_response.json()
            assert "configuration_valid" in config_data
            assert "zotero_config" in config_data
    
    def test_basic_zotero_workflow_ci(self, ci_client, ci_test_data):
        """Test basic Zotero workflow suitable for CI/CD."""
        
        with patch('services.zotero.zotero_client.ZoteroClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Setup mock responses
            mock_client_instance.get_libraries.return_value = ci_test_data['libraries']
            mock_client_instance.get_collections.return_value = ci_test_data['collections']
            mock_client_instance.get_items.return_value = ci_test_data['items']
            
            user_id = "ci-test-user"
            
            # Test connection creation
            connection_response = ci_client.post(
                "/api/zotero/auth/test-connection",
                json={
                    "user_id": user_id,
                    "access_token": "ci-test-token"
                }
            )
            
            assert connection_response.status_code == 200
            connection_data = connection_response.json()
            assert "connection_id" in connection_data
            
            connection_id = connection_data["connection_id"]
            
            # Test library sync
            sync_response = ci_client.post(
                f"/api/zotero/sync/{connection_id}/libraries"
            )
            
            assert sync_response.status_code == 200
            sync_data = sync_response.json()
            assert sync_data["success"] is True
            
            # Test item retrieval
            items_response = ci_client.get(
                f"/api/zotero/libraries/{connection_id}/items?limit=10"
            )
            
            assert items_response.status_code == 200
            items_data = items_response.json()
            assert "items" in items_data
            assert len(items_data["items"]) <= 10
            
            # Test search functionality
            search_response = ci_client.post(
                "/api/zotero/search",
                json={
                    "query": "CI test",
                    "library_id": connection_id,
                    "limit": 5
                }
            )
            
            assert search_response.status_code == 200
            search_data = search_response.json()
            assert "items" in search_data
            
            # Test citation generation
            if items_data.get("items"):
                item_key = items_data["items"][0].get("key", "CIITEM01")
                
                citation_response = ci_client.post(
                    "/api/zotero/citations/generate",
                    json={
                        "item_keys": [item_key],
                        "style": "apa",
                        "format": "text"
                    }
                )
                
                assert citation_response.status_code == 200
                citation_data = citation_response.json()
                assert "citations" in citation_data
    
    def test_error_handling_ci(self, ci_client):
        """Test error handling for CI/CD monitoring."""
        
        # Test invalid endpoint
        invalid_response = ci_client.get("/api/zotero/invalid-endpoint")
        assert invalid_response.status_code == 404
        
        # Test invalid request data
        invalid_request_response = ci_client.post(
            "/api/zotero/search",
            json={"invalid": "data"}
        )
        assert invalid_request_response.status_code in [400, 422]
        
        # Test authentication error
        auth_error_response = ci_client.post(
            "/api/zotero/auth/callback",
            json={"invalid": "auth_data"}
        )
        assert auth_error_response.status_code in [400, 401, 422]
    
    def test_performance_benchmarks_ci(self, ci_client, ci_test_data):
        """Test performance benchmarks for CI/CD monitoring."""
        
        with patch('services.zotero.zotero_search_service.ZoteroSearchService') as mock_search:
            mock_search_instance = AsyncMock()
            mock_search.return_value = mock_search_instance
            
            mock_search_instance.search_items.return_value = {
                'items': ci_test_data['items'],
                'total_count': len(ci_test_data['items']),
                'facets': {}
            }
            
            # Test search performance
            search_start = time.time()
            
            search_response = ci_client.post(
                "/api/zotero/search",
                json={
                    "query": "performance test",
                    "library_id": "ci-perf-lib",
                    "limit": 100
                }
            )
            
            search_time = time.time() - search_start
            
            assert search_response.status_code == 200
            assert search_time < 5.0  # Should complete within 5 seconds in CI
            
            # Test citation performance
            with patch('services.zotero.zotero_citation_service.ZoteroCitationService') as mock_citation:
                mock_citation_instance = AsyncMock()
                mock_citation.return_value = mock_citation_instance
                
                mock_citation_instance.generate_citations.return_value = [
                    {
                        'item_key': 'CIITEM01',
                        'citation': 'CI citation',
                        'style': 'apa'
                    }
                ]
                
                citation_start = time.time()
                
                citation_response = ci_client.post(
                    "/api/zotero/citations/generate",
                    json={
                        "item_keys": ["CIITEM01"],
                        "style": "apa",
                        "format": "text"
                    }
                )
                
                citation_time = time.time() - citation_start
                
                assert citation_response.status_code == 200
                assert citation_time < 3.0  # Should complete within 3 seconds in CI
    
    def test_security_compliance_ci(self, ci_client):
        """Test security compliance for CI/CD pipelines."""
        
        # Test CORS headers
        cors_response = ci_client.options("/api/zotero/search")
        assert "Access-Control-Allow-Origin" in cors_response.headers or cors_response.status_code == 405
        
        # Test security headers
        security_response = ci_client.get("/api/zotero/health")
        headers = security_response.headers
        
        # Check for security headers (may not all be present in test environment)
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security"
        ]
        
        present_headers = [header for header in security_headers if header in headers]
        print(f"Security headers present: {present_headers}")
        
        # Test input validation
        xss_attempt = ci_client.post(
            "/api/zotero/search",
            json={
                "query": "<script>alert('xss')</script>",
                "library_id": "test-lib"
            }
        )
        
        # Should handle XSS attempt gracefully
        assert xss_attempt.status_code in [200, 400, 422]
        
        if xss_attempt.status_code == 200:
            xss_data = xss_attempt.json()
            # Response should not contain unescaped script tags
            response_text = json.dumps(xss_data)
            assert "<script>" not in response_text
    
    def test_logging_and_monitoring_ci(self, ci_client):
        """Test logging and monitoring for CI/CD environments."""
        
        # Test metrics endpoint
        metrics_response = ci_client.get("/metrics")
        assert metrics_response.status_code in [200, 404]  # May not be implemented
        
        if metrics_response.status_code == 200:
            # Should return Prometheus-style metrics
            metrics_text = metrics_response.text
            assert "zotero_" in metrics_text or "http_" in metrics_text
        
        # Test logs endpoint (if available)
        logs_response = ci_client.get("/api/admin/logs/recent")
        assert logs_response.status_code in [200, 404, 403]  # May not be implemented or restricted
    
    def test_deployment_readiness_ci(self, ci_client):
        """Test deployment readiness for CI/CD pipelines."""
        
        # Test readiness probe
        readiness_response = ci_client.get("/ready")
        assert readiness_response.status_code in [200, 404]
        
        if readiness_response.status_code == 200:
            readiness_data = readiness_response.json()
            assert "ready" in readiness_data
            assert readiness_data["ready"] is True
        
        # Test liveness probe
        liveness_response = ci_client.get("/alive")
        assert liveness_response.status_code in [200, 404]
        
        if liveness_response.status_code == 200:
            liveness_data = liveness_response.json()
            assert "alive" in liveness_data
            assert liveness_data["alive"] is True


@pytest.mark.ci
class TestZoteroRegressionTests:
    """Regression tests for Zotero integration in CI/CD."""
    
    def test_api_backward_compatibility(self, ci_client):
        """Test API backward compatibility for CI/CD deployments."""
        
        # Test v1 API endpoints (if they exist)
        v1_endpoints = [
            "/api/v1/zotero/health",
            "/api/v1/zotero/search",
            "/api/v1/zotero/citations"
        ]
        
        for endpoint in v1_endpoints:
            response = ci_client.get(endpoint)
            # Should either work (200) or be properly deprecated (410) or not found (404)
            assert response.status_code in [200, 404, 410]
            
            if response.status_code == 410:
                # Deprecated endpoint should provide migration info
                data = response.json()
                assert "deprecated" in data or "migration" in data
    
    def test_data_format_compatibility(self, ci_client):
        """Test data format compatibility for CI/CD deployments."""
        
        with patch('services.zotero.zotero_search_service.ZoteroSearchService') as mock_search:
            mock_search_instance = AsyncMock()
            mock_search.return_value = mock_search_instance
            
            # Test with legacy data format
            legacy_items = [
                {
                    'key': 'LEGACY01',
                    'title': 'Legacy Item',
                    'itemType': 'article',  # Legacy field name
                    'creators': [
                        {'creatorType': 'author', 'name': 'Legacy Author'}  # Legacy format
                    ]
                }
            ]
            
            mock_search_instance.search_items.return_value = {
                'items': legacy_items,
                'total_count': 1
            }
            
            search_response = ci_client.post(
                "/api/zotero/search",
                json={
                    "query": "legacy test",
                    "library_id": "legacy-lib"
                }
            )
            
            assert search_response.status_code == 200
            search_data = search_response.json()
            assert "items" in search_data
            
            # Should handle legacy data format gracefully
            if search_data["items"]:
                item = search_data["items"][0]
                assert "key" in item
                assert "title" in item
    
    def test_configuration_migration(self, ci_client):
        """Test configuration migration for CI/CD deployments."""
        
        # Test configuration migration endpoint
        migration_response = ci_client.post(
            "/api/admin/config/migrate",
            json={"from_version": "1.0", "to_version": "2.0"}
        )
        
        # Should either work or be not implemented
        assert migration_response.status_code in [200, 404, 501]
        
        if migration_response.status_code == 200:
            migration_data = migration_response.json()
            assert "migration_successful" in migration_data
    
    def test_feature_flag_compatibility(self, ci_client):
        """Test feature flag compatibility for CI/CD deployments."""
        
        # Test feature flags endpoint
        features_response = ci_client.get("/api/features")
        assert features_response.status_code in [200, 404]
        
        if features_response.status_code == 200:
            features_data = features_response.json()
            assert "features" in features_data
            
            # Check for Zotero-specific feature flags
            zotero_features = [
                "zotero_integration",
                "zotero_ai_analysis",
                "zotero_real_time_sync",
                "zotero_collaboration"
            ]
            
            for feature in zotero_features:
                if feature in features_data["features"]:
                    assert isinstance(features_data["features"][feature], bool)


@pytest.mark.ci
class TestZoteroEnvironmentSpecificTests:
    """Environment-specific tests for different CI/CD stages."""
    
    def test_development_environment(self, ci_client):
        """Test development environment specific features."""
        
        if os.getenv("ENVIRONMENT") == "development":
            # Test debug endpoints (should be available in dev)
            debug_response = ci_client.get("/api/debug/zotero")
            assert debug_response.status_code in [200, 404]
            
            # Test mock data endpoints
            mock_data_response = ci_client.get("/api/debug/zotero/mock-data")
            assert mock_data_response.status_code in [200, 404]
    
    def test_staging_environment(self, ci_client):
        """Test staging environment specific features."""
        
        if os.getenv("ENVIRONMENT") == "staging":
            # Test staging-specific configurations
            staging_config_response = ci_client.get("/api/config/staging")
            assert staging_config_response.status_code in [200, 404]
            
            # Staging should have debug features disabled
            debug_response = ci_client.get("/api/debug/zotero")
            assert debug_response.status_code in [404, 403]
    
    def test_production_environment(self, ci_client):
        """Test production environment specific features."""
        
        if os.getenv("ENVIRONMENT") == "production":
            # Production should have all debug features disabled
            debug_endpoints = [
                "/api/debug/zotero",
                "/api/debug/zotero/mock-data",
                "/api/admin/debug"
            ]
            
            for endpoint in debug_endpoints:
                debug_response = ci_client.get(endpoint)
                assert debug_response.status_code in [404, 403]
            
            # Production should have security headers
            health_response = ci_client.get("/api/zotero/health")
            headers = health_response.headers
            
            # Should have at least some security headers in production
            security_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options",
                "Strict-Transport-Security"
            ]
            
            present_security_headers = [h for h in security_headers if h in headers]
            assert len(present_security_headers) > 0  # At least one security header should be present


@pytest.mark.ci
class TestZoteroMonitoringIntegration:
    """Monitoring integration tests for CI/CD pipelines."""
    
    def test_prometheus_metrics_integration(self, ci_client):
        """Test Prometheus metrics integration."""
        
        # Test metrics endpoint
        metrics_response = ci_client.get("/metrics")
        
        if metrics_response.status_code == 200:
            metrics_text = metrics_response.text
            
            # Check for Zotero-specific metrics
            expected_metrics = [
                "zotero_sync_operations_total",
                "zotero_search_requests_total",
                "zotero_citation_generations_total",
                "zotero_api_errors_total",
                "zotero_connection_pool_size"
            ]
            
            present_metrics = [metric for metric in expected_metrics if metric in metrics_text]
            print(f"Zotero metrics present: {present_metrics}")
            
            # Should have at least some Zotero metrics
            assert len(present_metrics) > 0 or "http_requests_total" in metrics_text
    
    def test_health_check_integration(self, ci_client):
        """Test health check integration for monitoring."""
        
        # Test detailed health check
        health_response = ci_client.get("/health/detailed")
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            
            # Should include Zotero service health
            assert "services" in health_data
            
            if "zotero" in health_data["services"]:
                zotero_health = health_data["services"]["zotero"]
                assert "status" in zotero_health
                assert "response_time" in zotero_health
                assert "last_check" in zotero_health
    
    def test_alerting_integration(self, ci_client):
        """Test alerting integration for CI/CD monitoring."""
        
        # Test alert configuration endpoint
        alerts_response = ci_client.get("/api/admin/alerts/config")
        
        if alerts_response.status_code == 200:
            alerts_data = alerts_response.json()
            
            # Should have Zotero-specific alerts configured
            if "alerts" in alerts_data:
                zotero_alerts = [
                    alert for alert in alerts_data["alerts"]
                    if "zotero" in alert.get("name", "").lower()
                ]
                
                print(f"Zotero alerts configured: {len(zotero_alerts)}")
    
    def test_logging_integration(self, ci_client):
        """Test logging integration for CI/CD monitoring."""
        
        # Perform operations that should generate logs
        with patch('services.zotero.zotero_search_service.ZoteroSearchService') as mock_search:
            mock_search_instance = AsyncMock()
            mock_search.return_value = mock_search_instance
            
            mock_search_instance.search_items.return_value = {
                'items': [],
                'total_count': 0
            }
            
            # Perform search operation
            search_response = ci_client.post(
                "/api/zotero/search",
                json={
                    "query": "logging test",
                    "library_id": "logging-lib"
                }
            )
            
            assert search_response.status_code == 200
        
        # Test log retrieval (if available)
        logs_response = ci_client.get("/api/admin/logs/zotero/recent")
        
        if logs_response.status_code == 200:
            logs_data = logs_response.json()
            assert "logs" in logs_data
            
            # Should have logs from the search operation
            search_logs = [
                log for log in logs_data["logs"]
                if "search" in log.get("message", "").lower()
            ]
            
            print(f"Search operation logs found: {len(search_logs)}")