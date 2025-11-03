"""Unit tests for error handling infrastructure."""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from backend.rl.utils.error_handler import (
    ErrorHandler, ErrorSeverity, RecoveryStrategy,
    handle_errors, global_error_handler
)
from backend.rl.exceptions.advanced_exceptions import (
    MultiModalProcessingError, PersonalizationError,
    ResearchAssistantError, ConfigurationError
)


class TestErrorHandler:
    """Test cases for ErrorHandler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
    
    def test_error_handler_initialization(self):
        """Test error handler initialization."""
        assert self.error_handler.error_counts == {}
        assert self.error_handler.recovery_strategies == {}
        assert self.error_handler.error_patterns == {}
        assert self.error_handler.circuit_breakers == {}
    
    def test_register_recovery_strategy(self):
        """Test registering recovery strategies."""
        fallback_func = Mock()
        
        self.error_handler.register_recovery_strategy(
            MultiModalProcessingError,
            RecoveryStrategy.FALLBACK,
            fallback_function=fallback_func,
            max_retries=2,
            retry_delay=0.5
        )
        
        assert MultiModalProcessingError in self.error_handler.recovery_strategies
        strategy = self.error_handler.recovery_strategies[MultiModalProcessingError]
        assert strategy['strategy'] == RecoveryStrategy.FALLBACK
        assert strategy['fallback_function'] == fallback_func
        assert strategy['max_retries'] == 2
        assert strategy['retry_delay'] == 0.5
    
    def test_handle_error_basic(self):
        """Test basic error handling."""
        error = MultiModalProcessingError("Test error")
        context = {"test_key": "test_value"}
        
        result = self.error_handler.handle_error(error, context, "test_component")
        
        assert result['error_handled'] is True
        assert 'recovery_strategy' in result
        assert 'recovery_success' in result
        assert 'recovery_details' in result
    
    def test_error_tracking(self):
        """Test error occurrence tracking."""
        error = MultiModalProcessingError("Test error")
        error_key = "test_component:MultiModalProcessingError"
        
        # Handle error multiple times
        for i in range(3):
            self.error_handler.handle_error(error, {}, "test_component")
        
        assert error_key in self.error_handler.error_counts
        assert self.error_handler.error_counts[error_key]['count'] == 3
        assert len(self.error_handler.error_counts[error_key]['contexts']) == 3
    
    def test_get_recovery_strategy_exact_match(self):
        """Test getting recovery strategy with exact type match."""
        fallback_func = Mock()
        self.error_handler.register_recovery_strategy(
            MultiModalProcessingError,
            RecoveryStrategy.FALLBACK,
            fallback_function=fallback_func
        )
        
        strategy = self.error_handler._get_recovery_strategy(MultiModalProcessingError)
        assert strategy['strategy'] == RecoveryStrategy.FALLBACK
        assert strategy['fallback_function'] == fallback_func
    
    def test_get_recovery_strategy_inheritance(self):
        """Test getting recovery strategy with inheritance."""
        from backend.rl.exceptions.advanced_exceptions import VisualProcessingError
        
        self.error_handler.register_recovery_strategy(
            MultiModalProcessingError,
            RecoveryStrategy.FALLBACK
        )
        
        strategy = self.error_handler._get_recovery_strategy(VisualProcessingError)
        assert strategy['strategy'] == RecoveryStrategy.FALLBACK
    
    def test_get_recovery_strategy_default(self):
        """Test getting default recovery strategy."""
        strategy = self.error_handler._get_recovery_strategy(MultiModalProcessingError)
        assert strategy['strategy'] == RecoveryStrategy.FALLBACK
        
        strategy = self.error_handler._get_recovery_strategy(PersonalizationError)
        assert strategy['strategy'] == RecoveryStrategy.GRACEFUL_DEGRADATION
        
        strategy = self.error_handler._get_recovery_strategy(ResearchAssistantError)
        assert strategy['strategy'] == RecoveryStrategy.RETRY
    
    def test_retry_recovery(self):
        """Test retry recovery strategy."""
        error = ResearchAssistantError("Test error")
        recovery_info = {
            'strategy': RecoveryStrategy.RETRY,
            'max_retries': 3,
            'retry_delay': 0.1
        }
        
        result = self.error_handler._retry_recovery(error, recovery_info, {})
        
        assert result['success'] is False  # Actual retry handled by decorator
        assert result['strategy'] == 'retry'
        assert result['max_retries'] == 3
        assert result['retry_delay'] == 0.1
    
    def test_fallback_recovery_success(self):
        """Test successful fallback recovery."""
        error = MultiModalProcessingError("Test error")
        fallback_func = Mock(return_value="fallback_result")
        recovery_info = {
            'strategy': RecoveryStrategy.FALLBACK,
            'fallback_function': fallback_func
        }
        
        result = self.error_handler._fallback_recovery(error, recovery_info, {})
        
        assert result['success'] is True
        assert result['strategy'] == 'fallback'
        assert result['result'] == "fallback_result"
        fallback_func.assert_called_once()
    
    def test_fallback_recovery_failure(self):
        """Test failed fallback recovery."""
        error = MultiModalProcessingError("Test error")
        fallback_func = Mock(side_effect=Exception("Fallback failed"))
        recovery_info = {
            'strategy': RecoveryStrategy.FALLBACK,
            'fallback_function': fallback_func
        }
        
        result = self.error_handler._fallback_recovery(error, recovery_info, {})
        
        assert result['success'] is False
        assert result['strategy'] == 'fallback'
        assert 'error' in result
    
    def test_fallback_recovery_no_function(self):
        """Test fallback recovery without fallback function."""
        error = MultiModalProcessingError("Test error")
        recovery_info = {
            'strategy': RecoveryStrategy.FALLBACK,
            'fallback_function': None
        }
        
        result = self.error_handler._fallback_recovery(error, recovery_info, {})
        
        assert result['success'] is False
        assert result['strategy'] == 'fallback'
    
    def test_graceful_degradation_recovery(self):
        """Test graceful degradation recovery."""
        error = PersonalizationError("Test error")
        recovery_info = {'strategy': RecoveryStrategy.GRACEFUL_DEGRADATION}
        
        result = self.error_handler._graceful_degradation_recovery(error, recovery_info, {})
        
        assert result['success'] is True
        assert result['strategy'] == 'graceful_degradation'
    
    def test_skip_recovery(self):
        """Test skip recovery strategy."""
        error = MultiModalProcessingError("Test error")
        recovery_info = {'strategy': RecoveryStrategy.SKIP}
        
        result = self.error_handler._skip_recovery(error, recovery_info, {})
        
        assert result['success'] is True
        assert result['strategy'] == 'skip'
    
    def test_abort_recovery(self):
        """Test abort recovery strategy."""
        error = ConfigurationError("Test error")
        recovery_info = {'strategy': RecoveryStrategy.ABORT}
        
        result = self.error_handler._abort_recovery(error, recovery_info, {})
        
        assert result['success'] is False
        assert result['strategy'] == 'abort'
    
    def test_error_pattern_analysis_high_frequency(self):
        """Test high frequency error pattern detection."""
        error = MultiModalProcessingError("Test error")
        error_key = "test_component:MultiModalProcessingError"
        
        # Simulate high frequency errors
        for i in range(15):
            self.error_handler._track_error(error_key, error, {})
        
        # Check that high frequency pattern is detected
        assert error_key in self.error_handler.error_counts
        assert self.error_handler.error_counts[error_key]['count'] == 15
    
    def test_error_statistics(self):
        """Test error statistics generation."""
        # Generate some errors
        errors = [
            (MultiModalProcessingError("Error 1"), "component1"),
            (PersonalizationError("Error 2"), "component1"),
            (ResearchAssistantError("Error 3"), "component2"),
            (MultiModalProcessingError("Error 4"), "component1")
        ]
        
        for error, component in errors:
            self.error_handler.handle_error(error, {}, component)
        
        stats = self.error_handler.get_error_statistics()
        
        assert stats['total_errors'] == 4
        assert stats['unique_error_types'] == 3
        assert 'error_breakdown' in stats
        assert 'top_errors' in stats
        assert len(stats['top_errors']) > 0
    
    def test_reset_error_statistics(self):
        """Test resetting error statistics."""
        error = MultiModalProcessingError("Test error")
        self.error_handler.handle_error(error, {}, "test_component")
        
        assert len(self.error_handler.error_counts) > 0
        
        self.error_handler.reset_error_statistics()
        
        assert len(self.error_handler.error_counts) == 0


class TestErrorHandlerDecorator:
    """Test cases for error handler decorator."""
    
    def test_decorator_basic_function(self):
        """Test decorator with basic function."""
        @handle_errors(component="test_component")
        def test_function():
            raise MultiModalProcessingError("Test error")
        
        with pytest.raises(MultiModalProcessingError):
            test_function()
    
    def test_decorator_with_retry(self):
        """Test decorator with retry strategy."""
        call_count = 0
        
        @handle_errors(
            component="test_component",
            recovery_strategy=RecoveryStrategy.RETRY,
            max_retries=2,
            retry_delay=0.01
        )
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise MultiModalProcessingError("Test error")
            return "success"
        
        result = test_function()
        assert result == "success"
        assert call_count == 3
    
    def test_decorator_with_fallback(self):
        """Test decorator with fallback strategy."""
        def fallback_function(error, context):
            return "fallback_result"
        
        @handle_errors(
            component="test_component",
            recovery_strategy=RecoveryStrategy.FALLBACK,
            fallback_function=fallback_function
        )
        def test_function():
            raise MultiModalProcessingError("Test error")
        
        result = test_function()
        assert result == "fallback_result"
    
    @pytest.mark.asyncio
    async def test_decorator_async_function(self):
        """Test decorator with async function."""
        @handle_errors(component="test_component")
        async def test_async_function():
            raise PersonalizationError("Test error")
        
        with pytest.raises(PersonalizationError):
            await test_async_function()
    
    @pytest.mark.asyncio
    async def test_decorator_async_with_retry(self):
        """Test decorator with async function and retry."""
        call_count = 0
        
        @handle_errors(
            component="test_component",
            recovery_strategy=RecoveryStrategy.RETRY,
            max_retries=2,
            retry_delay=0.01
        )
        async def test_async_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ResearchAssistantError("Test error")
            return "async_success"
        
        result = await test_async_function()
        assert result == "async_success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_decorator_async_with_fallback(self):
        """Test decorator with async function and fallback."""
        async def async_fallback_function(error, context):
            return "async_fallback_result"
        
        @handle_errors(
            component="test_component",
            recovery_strategy=RecoveryStrategy.FALLBACK,
            fallback_function=async_fallback_function
        )
        async def test_async_function():
            raise MultiModalProcessingError("Test error")
        
        result = await test_async_function()
        assert result == "async_fallback_result"
    
    def test_decorator_no_logging(self):
        """Test decorator with logging disabled."""
        @handle_errors(component="test_component", log_errors=False)
        def test_function():
            raise MultiModalProcessingError("Test error")
        
        with pytest.raises(MultiModalProcessingError):
            test_function()


class TestErrorHandlerIntegration:
    """Integration tests for error handler."""
    
    def test_global_error_handler_usage(self):
        """Test using global error handler instance."""
        error = MultiModalProcessingError("Global test error")
        
        result = global_error_handler.handle_error(error, {}, "global_test")
        
        assert result['error_handled'] is True
        assert 'global_test:MultiModalProcessingError' in global_error_handler.error_counts
    
    def test_multiple_error_types(self):
        """Test handling multiple different error types."""
        errors = [
            MultiModalProcessingError("Multi-modal error"),
            PersonalizationError("Personalization error"),
            ResearchAssistantError("Research assistant error"),
            ConfigurationError("Configuration error")
        ]
        
        for error in errors:
            result = global_error_handler.handle_error(error, {}, "integration_test")
            assert result['error_handled'] is True
    
    def test_error_context_preservation(self):
        """Test that error context is preserved."""
        error = MultiModalProcessingError(
            "Test error",
            processing_stage="feature_extraction",
            visual_element_type="chart"
        )
        context = {"user_id": "test_user", "document_id": "test_doc"}
        
        result = global_error_handler.handle_error(error, context, "context_test")
        
        error_key = "context_test:MultiModalProcessingError"
        assert error_key in global_error_handler.error_counts
        
        stored_context = global_error_handler.error_counts[error_key]['contexts'][0]
        assert stored_context['context'] == context
    
    def test_recovery_strategy_inheritance(self):
        """Test recovery strategy inheritance for error subclasses."""
        from backend.rl.exceptions.advanced_exceptions import VisualProcessingError
        
        # Register strategy for parent class
        global_error_handler.register_recovery_strategy(
            MultiModalProcessingError,
            RecoveryStrategy.FALLBACK,
            max_retries=2
        )
        
        # Test with subclass
        error = VisualProcessingError("Visual processing error")
        result = global_error_handler.handle_error(error, {}, "inheritance_test")
        
        assert result['recovery_details']['strategy'] == 'fallback'


class TestErrorHandlerEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_handle_error_with_none_context(self):
        """Test handling error with None context."""
        error_handler = ErrorHandler()
        error = MultiModalProcessingError("Test error")
        
        result = error_handler.handle_error(error, None, "test_component")
        
        assert result['error_handled'] is True
    
    def test_handle_error_with_none_component(self):
        """Test handling error with None component."""
        error_handler = ErrorHandler()
        error = MultiModalProcessingError("Test error")
        
        result = error_handler.handle_error(error, {}, None)
        
        assert result['error_handled'] is True
    
    def test_context_list_truncation(self):
        """Test that context list is truncated to prevent memory bloat."""
        error_handler = ErrorHandler()
        error = MultiModalProcessingError("Test error")
        
        # Add more than 10 contexts
        for i in range(15):
            error_handler._track_error("test:MultiModalProcessingError", error, {"iteration": i})
        
        contexts = error_handler.error_counts["test:MultiModalProcessingError"]['contexts']
        assert len(contexts) == 10
        # Should keep the last 10
        assert contexts[0]['context']['iteration'] == 5
        assert contexts[-1]['context']['iteration'] == 14
    
    def test_fallback_function_exception(self):
        """Test fallback function that raises exception."""
        error_handler = ErrorHandler()
        
        def failing_fallback(error, context):
            raise Exception("Fallback failed")
        
        error_handler.register_recovery_strategy(
            MultiModalProcessingError,
            RecoveryStrategy.FALLBACK,
            fallback_function=failing_fallback
        )
        
        error = MultiModalProcessingError("Test error")
        result = error_handler.handle_error(error, {}, "test_component")
        
        assert result['recovery_details']['success'] is False
        assert 'error' in result['recovery_details']


if __name__ == "__main__":
    pytest.main([__file__])