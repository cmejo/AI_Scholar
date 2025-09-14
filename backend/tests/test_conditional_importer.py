"""
Comprehensive unit tests for ConditionalImporter
Tests safe imports, retry logic, caching, and error handling
"""
import pytest
import time
import importlib
from unittest.mock import patch, MagicMock
from typing import Any

from core.conditional_importer import ConditionalImporter, conditional_import, require_service


@pytest.mark.unit
class TestConditionalImporter:
    """Test ConditionalImporter functionality"""
    
    def setup_method(self):
        """Clear caches before each test"""
        ConditionalImporter.clear_cache()
        ConditionalImporter.clear_failed_imports()
    
    def test_safe_import_success(self):
        """Test successful module import"""
        # Import a standard library module
        result = ConditionalImporter.safe_import("json")
        
        assert result is not None
        assert hasattr(result, "loads")
        assert hasattr(result, "dumps")
    
    def test_safe_import_with_attribute_success(self):
        """Test successful attribute import from module"""
        result = ConditionalImporter.safe_import("json", attribute="loads")
        
        assert result is not None
        assert callable(result)
    
    def test_safe_import_failure_with_fallback(self):
        """Test import failure with fallback value"""
        fallback_value = "fallback"
        result = ConditionalImporter.safe_import(
            "non_existent_module_12345",
            fallback=fallback_value
        )
        
        assert result == fallback_value
    
    def test_safe_import_attribute_not_found(self):
        """Test import with non-existent attribute"""
        fallback_value = "attribute_fallback"
        result = ConditionalImporter.safe_import(
            "json",
            attribute="non_existent_attribute",
            fallback=fallback_value
        )
        
        assert result == fallback_value
    
    def test_safe_import_caching(self):
        """Test import result caching"""
        module_name = "json"
        
        # First import
        result1 = ConditionalImporter.safe_import(module_name, cache=True)
        
        # Second import should use cache
        with patch('importlib.import_module') as mock_import:
            result2 = ConditionalImporter.safe_import(module_name, cache=True)
            
            # importlib should not be called due to caching
            mock_import.assert_not_called()
            assert result1 == result2
    
    def test_safe_import_no_caching(self):
        """Test import without caching"""
        module_name = "json"
        
        # Import without caching
        result1 = ConditionalImporter.safe_import(module_name, cache=False)
        
        # Second import should not use cache
        with patch('importlib.import_module') as mock_import:
            mock_import.return_value = MagicMock()
            result2 = ConditionalImporter.safe_import(module_name, cache=False)
            
            # importlib should be called
            mock_import.assert_called_once_with(module_name)
    
    def test_safe_import_failed_cache(self):
        """Test caching of failed imports"""
        module_name = "non_existent_module_12345"
        fallback = "fallback"
        
        # First failed import
        result1 = ConditionalImporter.safe_import(module_name, fallback=fallback)
        
        # Second import should use failed cache
        with patch('importlib.import_module') as mock_import:
            result2 = ConditionalImporter.safe_import(module_name, fallback=fallback)
            
            # importlib should not be called due to failed cache
            mock_import.assert_not_called()
            assert result1 == result2 == fallback
    
    def test_import_with_retry_success_first_attempt(self):
        """Test retry import succeeding on first attempt"""
        result = ConditionalImporter.import_with_retry("json", max_retries=3)
        
        assert result is not None
        assert hasattr(result, "loads")
    
    def test_import_with_retry_success_after_failures(self):
        """Test retry import succeeding after initial failures"""
        call_count = 0
        
        def mock_import(module_name):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ImportError(f"Attempt {call_count} failed")
            return MagicMock()
        
        with patch('importlib.import_module', side_effect=mock_import):
            result = ConditionalImporter.import_with_retry(
                "test_module",
                max_retries=3,
                retry_delay=0.01  # Fast retry for testing
            )
            
            assert result is not None
            assert call_count == 3
    
    def test_import_with_retry_all_attempts_fail(self):
        """Test retry import failing all attempts"""
        fallback = "retry_fallback"
        
        with patch('importlib.import_module', side_effect=ImportError("Always fails")):
            result = ConditionalImporter.import_with_retry(
                "failing_module",
                max_retries=2,
                retry_delay=0.01,
                fallback=fallback
            )
            
            assert result == fallback
    
    def test_import_with_retry_attribute_success(self):
        """Test retry import with attribute"""
        mock_module = MagicMock()
        mock_module.test_attr = "test_value"
        
        with patch('importlib.import_module', return_value=mock_module):
            result = ConditionalImporter.import_with_retry(
                "test_module",
                attribute="test_attr",
                max_retries=1
            )
            
            assert result == "test_value"
    
    def test_import_with_retry_attribute_not_found(self):
        """Test retry import with non-existent attribute"""
        mock_module = MagicMock()
        del mock_module.non_existent_attr  # Ensure attribute doesn't exist
        
        with patch('importlib.import_module', return_value=mock_module):
            result = ConditionalImporter.import_with_retry(
                "test_module",
                attribute="non_existent_attr",
                fallback="attr_fallback",
                max_retries=1
            )
            
            assert result == "attr_fallback"
    
    def test_import_service_class_success(self):
        """Test successful service class import"""
        mock_module = MagicMock()
        mock_service_class = MagicMock()
        mock_module.TestService = mock_service_class
        
        with patch('importlib.import_module', return_value=mock_module):
            result = ConditionalImporter.import_service_class(
                "services.test_service",
                "TestService"
            )
            
            assert result == mock_service_class
    
    def test_import_service_class_with_fallback(self):
        """Test service class import with fallback"""
        fallback_class = MagicMock
        
        with patch('importlib.import_module', side_effect=ImportError("Module not found")):
            result = ConditionalImporter.import_service_class(
                "services.non_existent",
                "NonExistentService",
                fallback_class=fallback_class
            )
            
            assert result == fallback_class
    
    def test_clear_cache(self):
        """Test clearing import cache"""
        # Add something to cache
        ConditionalImporter.safe_import("json", cache=True)
        assert len(ConditionalImporter._import_cache) > 0
        
        # Clear cache
        ConditionalImporter.clear_cache()
        assert len(ConditionalImporter._import_cache) == 0
    
    def test_clear_failed_imports(self):
        """Test clearing failed imports cache"""
        # Add failed import
        ConditionalImporter.safe_import("non_existent_module", fallback=None)
        assert len(ConditionalImporter._failed_imports) > 0
        
        # Clear failed imports
        ConditionalImporter.clear_failed_imports()
        assert len(ConditionalImporter._failed_imports) == 0
    
    def test_get_cache_info(self):
        """Test getting cache information"""
        # Add successful import
        ConditionalImporter.safe_import("json", cache=True)
        
        # Add failed import
        ConditionalImporter.safe_import("non_existent", fallback=None)
        
        cache_info = ConditionalImporter.get_cache_info()
        
        assert isinstance(cache_info, dict)
        assert "cached_imports" in cache_info
        assert "failed_imports" in cache_info
        assert "cache_size" in cache_info
        assert "failed_count" in cache_info
        
        assert cache_info["cache_size"] > 0
        assert cache_info["failed_count"] > 0
        assert len(cache_info["cached_imports"]) > 0
        assert len(cache_info["failed_imports"]) > 0


@pytest.mark.unit
class TestConditionalImportDecorator:
    """Test conditional_import decorator"""
    
    def setup_method(self):
        """Clear caches before each test"""
        ConditionalImporter.clear_cache()
        ConditionalImporter.clear_failed_imports()
    
    def test_conditional_import_decorator_success(self):
        """Test conditional import decorator with successful import"""
        @conditional_import("json", fallback=None)
        def test_function(imported=None):
            return imported
        
        result = test_function()
        assert result is not None
        assert hasattr(result, "loads")
    
    def test_conditional_import_decorator_failure(self):
        """Test conditional import decorator with failed import"""
        fallback_value = "decorator_fallback"
        
        @conditional_import("non_existent_module", fallback=fallback_value)
        def test_function(imported=None):
            return imported
        
        result = test_function()
        assert result == fallback_value
    
    def test_conditional_import_decorator_with_attribute(self):
        """Test conditional import decorator with attribute"""
        @conditional_import("json", attribute="loads", fallback=None)
        def test_function(imported=None):
            return imported
        
        result = test_function()
        assert result is not None
        assert callable(result)
    
    def test_conditional_import_decorator_with_retry(self):
        """Test conditional import decorator with retry logic"""
        call_count = 0
        
        def mock_import(module_name):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ImportError(f"Attempt {call_count} failed")
            return MagicMock()
        
        with patch('importlib.import_module', side_effect=mock_import):
            @conditional_import(
                "test_module",
                max_retries=2,
                retry_delay=0.01,
                fallback=None
            )
            def test_function(imported=None):
                return imported
            
            result = test_function()
            assert result is not None
            assert call_count == 2
    
    def test_conditional_import_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function metadata"""
        @conditional_import("json", fallback=None)
        def test_function():
            """Test function docstring"""
            return "test"
        
        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test function docstring"


@pytest.mark.unit
class TestRequireServiceDecorator:
    """Test require_service decorator"""
    
    @pytest.fixture
    def mock_service_manager(self):
        """Mock service manager for testing"""
        with patch('core.service_manager.service_manager') as mock_sm:
            yield mock_sm
    
    @pytest.mark.asyncio
    async def test_require_service_decorator_service_available(self, mock_service_manager):
        """Test require_service decorator when service is available"""
        mock_service = MagicMock()
        mock_service_manager.is_service_healthy.return_value = True
        mock_service_manager.get_service.return_value = mock_service
        
        @require_service("test_service")
        async def test_endpoint(service=None):
            return {"service": service}
        
        result = await test_endpoint()
        
        assert result["service"] == mock_service
        mock_service_manager.is_service_healthy.assert_called_once_with("test_service")
        mock_service_manager.get_service.assert_called_once_with("test_service")
    
    @pytest.mark.asyncio
    async def test_require_service_decorator_service_unavailable_with_fallback(self, mock_service_manager):
        """Test require_service decorator when service is unavailable with fallback"""
        mock_service_manager.is_service_healthy.return_value = False
        fallback_response = {"error": "Service unavailable"}
        
        @require_service("test_service", fallback_response=fallback_response)
        async def test_endpoint(service=None):
            return {"service": service}
        
        result = await test_endpoint()
        
        assert result == fallback_response
        mock_service_manager.is_service_healthy.assert_called_once_with("test_service")
        mock_service_manager.get_service.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_require_service_decorator_service_unavailable_no_fallback(self, mock_service_manager):
        """Test require_service decorator when service is unavailable without fallback"""
        mock_service_manager.is_service_healthy.return_value = False
        
        @require_service("test_service")
        async def test_endpoint(service=None):
            return {"service": service}
        
        # Should raise HTTPException
        with pytest.raises(Exception) as exc_info:
            await test_endpoint()
        
        # Check that it's an HTTP exception with 503 status
        assert "503" in str(exc_info.value) or "Service" in str(exc_info.value)


@pytest.mark.unit
class TestConditionalImporterEdgeCases:
    """Test edge cases and error conditions"""
    
    def setup_method(self):
        """Clear caches before each test"""
        ConditionalImporter.clear_cache()
        ConditionalImporter.clear_failed_imports()
    
    def test_import_with_none_module_name(self):
        """Test import with None module name"""
        result = ConditionalImporter.safe_import(None, fallback="none_fallback")
        assert result == "none_fallback"
    
    def test_import_with_empty_module_name(self):
        """Test import with empty module name"""
        result = ConditionalImporter.safe_import("", fallback="empty_fallback")
        assert result == "empty_fallback"
    
    def test_import_with_circular_dependency(self):
        """Test handling of circular import dependencies"""
        # This is hard to test directly, but we can test that the importer
        # handles ImportError exceptions gracefully
        with patch('importlib.import_module', side_effect=ImportError("Circular import")):
            result = ConditionalImporter.safe_import(
                "circular_module",
                fallback="circular_fallback"
            )
            assert result == "circular_fallback"
    
    def test_import_with_syntax_error_in_module(self):
        """Test handling of syntax errors in imported modules"""
        with patch('importlib.import_module', side_effect=SyntaxError("Invalid syntax")):
            result = ConditionalImporter.safe_import(
                "syntax_error_module",
                fallback="syntax_fallback"
            )
            assert result == "syntax_fallback"
    
    def test_import_with_runtime_error_in_module(self):
        """Test handling of runtime errors during module initialization"""
        with patch('importlib.import_module', side_effect=RuntimeError("Runtime error")):
            result = ConditionalImporter.safe_import(
                "runtime_error_module",
                fallback="runtime_fallback"
            )
            assert result == "runtime_fallback"
    
    def test_retry_with_zero_retries(self):
        """Test retry logic with zero retries"""
        with patch('importlib.import_module', side_effect=ImportError("Always fails")):
            result = ConditionalImporter.import_with_retry(
                "failing_module",
                max_retries=0,
                fallback="zero_retry_fallback"
            )
            assert result == "zero_retry_fallback"
    
    def test_retry_with_negative_retries(self):
        """Test retry logic with negative retries"""
        with patch('importlib.import_module', side_effect=ImportError("Always fails")):
            result = ConditionalImporter.import_with_retry(
                "failing_module",
                max_retries=-1,
                fallback="negative_retry_fallback"
            )
            assert result == "negative_retry_fallback"
    
    def test_retry_with_very_short_delay(self):
        """Test retry logic with very short delay"""
        call_count = 0
        start_time = time.time()
        
        def mock_import(module_name):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ImportError(f"Attempt {call_count} failed")
            return MagicMock()
        
        with patch('importlib.import_module', side_effect=mock_import):
            result = ConditionalImporter.import_with_retry(
                "test_module",
                max_retries=3,
                retry_delay=0.001  # Very short delay
            )
            
            end_time = time.time()
            assert result is not None
            assert call_count == 3
            # Should complete quickly due to short delay
            assert (end_time - start_time) < 1.0
    
    def test_cache_key_generation(self):
        """Test cache key generation for different import scenarios"""
        # Import module only
        ConditionalImporter.safe_import("json", cache=True)
        
        # Import with attribute
        ConditionalImporter.safe_import("json", attribute="loads", cache=True)
        
        cache_info = ConditionalImporter.get_cache_info()
        cached_imports = cache_info["cached_imports"]
        
        # Should have different cache keys
        assert "json" in cached_imports
        assert "json.loads" in cached_imports
        assert len(cached_imports) >= 2
    
    def test_concurrent_imports(self):
        """Test concurrent imports of the same module"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def import_worker():
            result = ConditionalImporter.safe_import("json", cache=True)
            results.put(result)
        
        # Start multiple threads importing the same module
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=import_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All results should be the same (json module)
        import_results = []
        while not results.empty():
            import_results.append(results.get())
        
        assert len(import_results) == 5
        # All should be the same json module
        first_result = import_results[0]
        assert all(result == first_result for result in import_results)


@pytest.mark.unit
class TestConditionalImporterPerformance:
    """Test performance characteristics of ConditionalImporter"""
    
    def setup_method(self):
        """Clear caches before each test"""
        ConditionalImporter.clear_cache()
        ConditionalImporter.clear_failed_imports()
    
    def test_cache_performance(self):
        """Test that caching improves performance"""
        module_name = "json"
        
        # Time first import (no cache)
        start_time = time.time()
        result1 = ConditionalImporter.safe_import(module_name, cache=True)
        first_import_time = time.time() - start_time
        
        # Time second import (with cache)
        start_time = time.time()
        result2 = ConditionalImporter.safe_import(module_name, cache=True)
        cached_import_time = time.time() - start_time
        
        assert result1 == result2
        # Cached import should be significantly faster
        assert cached_import_time < first_import_time
        # Cached import should be very fast (less than 1ms typically)
        assert cached_import_time < 0.001
    
    def test_failed_import_cache_performance(self):
        """Test that failed import caching improves performance"""
        module_name = "non_existent_module_12345"
        fallback = "fallback"
        
        # Time first failed import
        start_time = time.time()
        result1 = ConditionalImporter.safe_import(module_name, fallback=fallback)
        first_fail_time = time.time() - start_time
        
        # Time second failed import (should use cache)
        start_time = time.time()
        result2 = ConditionalImporter.safe_import(module_name, fallback=fallback)
        cached_fail_time = time.time() - start_time
        
        assert result1 == result2 == fallback
        # Cached failed import should be faster
        assert cached_fail_time < first_fail_time
        # Should be very fast
        assert cached_fail_time < 0.001