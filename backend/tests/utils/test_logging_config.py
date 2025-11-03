"""Unit tests for logging configuration."""

import pytest
import logging
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from backend.rl.utils.logging_config import (
    ComponentLogger, LogLevel, StructuredFormatter,
    MultiModalLogger, PersonalizationLogger, ResearchAssistantLogger,
    PerformanceLogger, ErrorLogger, get_component_logger,
    setup_logging
)
from backend.rl.exceptions.advanced_exceptions import MultiModalProcessingError


class TestComponentLogger:
    """Test cases for ComponentLogger class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use a unique component name to avoid conflicts
        self.component_name = f"test_component_{id(self)}"
        self.logger = ComponentLogger(self.component_name, LogLevel.DEBUG)
    
    def test_component_logger_initialization(self):
        """Test component logger initialization."""
        assert self.logger.component_name == self.component_name
        assert self.logger.logger.name == f"rl.{self.component_name}"
        assert self.logger.logger.level == logging.DEBUG
    
    def test_debug_logging(self):
        """Test debug level logging."""
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.debug("Debug message", test_key="test_value")
            
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert args[0] == logging.DEBUG
            assert args[1] == "Debug message"
            assert 'extra' in kwargs
            assert kwargs['extra']['component'] == self.component_name
            assert kwargs['extra']['test_key'] == "test_value"
    
    def test_info_logging(self):
        """Test info level logging."""
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.info("Info message", operation="test_operation")
            
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert args[0] == logging.INFO
            assert args[1] == "Info message"
            assert kwargs['extra']['operation'] == "test_operation"
    
    def test_warning_logging(self):
        """Test warning level logging."""
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.warning("Warning message", severity="medium")
            
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert args[0] == logging.WARNING
            assert args[1] == "Warning message"
            assert kwargs['extra']['severity'] == "medium"
    
    def test_error_logging_without_exception(self):
        """Test error level logging without exception."""
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.error("Error message", error_code="E001")
            
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert args[0] == logging.ERROR
            assert args[1] == "Error message"
            assert kwargs['extra']['error_code'] == "E001"
    
    def test_error_logging_with_exception(self):
        """Test error level logging with exception."""
        exception = MultiModalProcessingError("Test error", processing_stage="test")
        
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.error("Error occurred", exception=exception)
            
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert args[0] == logging.ERROR
            assert args[1] == "Error occurred"
            assert kwargs['extra']['exception_type'] == "MultiModalProcessingError"
            assert kwargs['extra']['exception_message'] == "Test error"
            assert kwargs['extra']['processing_stage'] == "test"
    
    def test_critical_logging_with_exception(self):
        """Test critical level logging with exception."""
        exception = Exception("Critical error")
        
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.critical("Critical error occurred", exception=exception)
            
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert args[0] == logging.CRITICAL
            assert args[1] == "Critical error occurred"
            assert kwargs['extra']['exception_type'] == "Exception"
            assert kwargs['extra']['exception_message'] == "Critical error"
    
    def test_log_with_context(self):
        """Test logging with additional context."""
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger._log_with_context(
                logging.INFO, 
                "Test message",
                user_id="user123",
                operation="test_op",
                duration=1.5
            )
            
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert args[0] == logging.INFO
            assert args[1] == "Test message"
            assert kwargs['extra']['user_id'] == "user123"
            assert kwargs['extra']['operation'] == "test_op"
            assert kwargs['extra']['duration'] == 1.5
            assert 'timestamp' in kwargs['extra']


class TestStructuredFormatter:
    """Test cases for StructuredFormatter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = StructuredFormatter()
    
    def test_format_basic_record(self):
        """Test formatting basic log record."""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.component = "test_component"
        
        formatted = self.formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed['level'] == 'INFO'
        assert parsed['component'] == 'test_component'
        assert parsed['message'] == 'Test message'
        assert parsed['line'] == 42
        assert 'timestamp' in parsed
    
    def test_format_record_with_extra_fields(self):
        """Test formatting record with extra fields."""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="/test/path.py",
            lineno=100,
            msg="Error message",
            args=(),
            exc_info=None
        )
        record.component = "error_component"
        record.user_id = "user123"
        record.operation = "test_operation"
        record.duration = 2.5
        
        formatted = self.formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed['component'] == 'error_component'
        assert parsed['user_id'] == 'user123'
        assert parsed['operation'] == 'test_operation'
        assert parsed['duration'] == 2.5
    
    def test_format_excludes_standard_fields(self):
        """Test that standard logging fields are excluded from extra data."""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.WARNING,
            pathname="/test/path.py",
            lineno=50,
            msg="Warning message",
            args=(),
            exc_info=None
        )
        record.component = "warning_component"
        
        formatted = self.formatter.format(record)
        parsed = json.loads(formatted)
        
        # Standard fields should not appear as extra data
        assert 'name' not in parsed
        assert 'msg' not in parsed
        assert 'args' not in parsed
        assert 'pathname' not in parsed
        
        # But derived fields should be present
        assert 'level' in parsed
        assert 'message' in parsed
        assert 'line' in parsed


class TestSpecializedLoggers:
    """Test cases for specialized logger classes."""
    
    def test_multimodal_logger(self):
        """Test MultiModalLogger functionality."""
        logger = MultiModalLogger()
        
        with patch.object(logger, 'info') as mock_info:
            logger.log_visual_processing(
                operation="image_analysis",
                image_info={"width": 1920, "height": 1080, "format": "PNG"},
                success=True,
                processing_time=1.5
            )
            
            mock_info.assert_called_once()
            args, kwargs = mock_info.call_args
            assert args[0] == "Visual processing: image_analysis"
            assert kwargs['operation'] == "image_analysis"
            assert kwargs['success'] is True
            assert kwargs['processing_time'] == 1.5
            assert kwargs['width'] == 1920
            assert kwargs['height'] == 1080
            assert kwargs['format'] == "PNG"
    
    def test_multimodal_logger_feature_integration(self):
        """Test MultiModalLogger feature integration logging."""
        logger = MultiModalLogger()
        
        with patch.object(logger, 'info') as mock_info:
            logger.log_feature_integration(
                text_features_count=50,
                visual_features_count=25,
                integration_method="attention_fusion",
                success=True
            )
            
            mock_info.assert_called_once()
            args, kwargs = mock_info.call_args
            assert args[0] == "Feature integration: attention_fusion"
            assert kwargs['text_features_count'] == 50
            assert kwargs['visual_features_count'] == 25
            assert kwargs['integration_method'] == "attention_fusion"
            assert kwargs['success'] is True
    
    def test_multimodal_logger_chart_analysis(self):
        """Test MultiModalLogger chart analysis logging."""
        logger = MultiModalLogger()
        
        with patch.object(logger, 'info') as mock_info:
            logger.log_chart_analysis(
                chart_type="bar_chart",
                data_points_extracted=15,
                confidence=0.85,
                success=True
            )
            
            mock_info.assert_called_once()
            args, kwargs = mock_info.call_args
            assert args[0] == "Chart analysis: bar_chart"
            assert kwargs['chart_type'] == "bar_chart"
            assert kwargs['data_points_extracted'] == 15
            assert kwargs['confidence'] == 0.85
            assert kwargs['success'] is True
    
    def test_personalization_logger(self):
        """Test PersonalizationLogger functionality."""
        logger = PersonalizationLogger()
        
        with patch.object(logger, 'info') as mock_info:
            logger.log_adaptation(
                user_id="user123",
                algorithm="deep_preference_learning",
                adaptation_type="preference_update",
                success=True,
                improvement_score=0.15
            )
            
            mock_info.assert_called_once()
            args, kwargs = mock_info.call_args
            assert args[0] == "Adaptation: deep_preference_learning - preference_update"
            assert kwargs['user_id'] == "user123"
            assert kwargs['algorithm'] == "deep_preference_learning"
            assert kwargs['adaptation_type'] == "preference_update"
            assert kwargs['success'] is True
            assert kwargs['improvement_score'] == 0.15
    
    def test_research_assistant_logger(self):
        """Test ResearchAssistantLogger functionality."""
        logger = ResearchAssistantLogger()
        
        with patch.object(logger, 'info') as mock_info:
            logger.log_workflow_optimization(
                workflow_id="workflow123",
                optimization_type="task_sequencing",
                efficiency_improvement=0.25,
                success=True
            )
            
            mock_info.assert_called_once()
            args, kwargs = mock_info.call_args
            assert args[0] == "Workflow optimization: task_sequencing"
            assert kwargs['workflow_id'] == "workflow123"
            assert kwargs['optimization_type'] == "task_sequencing"
            assert kwargs['efficiency_improvement'] == 0.25
            assert kwargs['success'] is True
    
    def test_performance_logger(self):
        """Test PerformanceLogger functionality."""
        logger = PerformanceLogger()
        
        with patch.object(logger, 'info') as mock_info:
            logger.log_processing_time(
                operation="document_analysis",
                component="multimodal_processor",
                processing_time=2.5,
                input_size=1024
            )
            
            mock_info.assert_called_once()
            args, kwargs = mock_info.call_args
            assert args[0] == "Performance: multimodal_processor - document_analysis"
            assert kwargs['operation'] == "document_analysis"
            assert kwargs['component'] == "multimodal_processor"
            assert kwargs['processing_time'] == 2.5
            assert kwargs['input_size'] == 1024
    
    def test_performance_logger_memory_usage(self):
        """Test PerformanceLogger memory usage logging."""
        logger = PerformanceLogger()
        
        with patch.object(logger, 'info') as mock_info:
            logger.log_memory_usage(
                component="feature_integrator",
                operation="cross_modal_fusion",
                memory_before=100.5,
                memory_after=150.2
            )
            
            mock_info.assert_called_once()
            args, kwargs = mock_info.call_args
            assert args[0] == "Memory usage: feature_integrator - cross_modal_fusion"
            assert kwargs['component'] == "feature_integrator"
            assert kwargs['operation'] == "cross_modal_fusion"
            assert kwargs['memory_before'] == 100.5
            assert kwargs['memory_after'] == 150.2
            assert kwargs['memory_delta'] == 49.7
    
    def test_performance_logger_throughput(self):
        """Test PerformanceLogger throughput logging."""
        logger = PerformanceLogger()
        
        with patch.object(logger, 'info') as mock_info:
            logger.log_throughput(
                component="visual_processor",
                operation="image_analysis",
                items_processed=100,
                time_elapsed=10.0
            )
            
            mock_info.assert_called_once()
            args, kwargs = mock_info.call_args
            assert args[0] == "Throughput: visual_processor - image_analysis"
            assert kwargs['component'] == "visual_processor"
            assert kwargs['operation'] == "image_analysis"
            assert kwargs['items_processed'] == 100
            assert kwargs['time_elapsed'] == 10.0
            assert kwargs['throughput'] == 10.0
    
    def test_error_logger(self):
        """Test ErrorLogger functionality."""
        logger = ErrorLogger()
        
        with patch.object(logger, 'info') as mock_info:
            logger.log_error_recovery(
                error_type="MultiModalProcessingError",
                recovery_strategy="fallback",
                recovery_success=True,
                recovery_time=0.5
            )
            
            mock_info.assert_called_once()
            args, kwargs = mock_info.call_args
            assert args[0] == "Error recovery: MultiModalProcessingError"
            assert kwargs['error_type'] == "MultiModalProcessingError"
            assert kwargs['recovery_strategy'] == "fallback"
            assert kwargs['recovery_success'] is True
            assert kwargs['recovery_time'] == 0.5


class TestLoggingUtilities:
    """Test cases for logging utility functions."""
    
    def test_get_component_logger_known_component(self):
        """Test getting logger for known component."""
        logger = get_component_logger("multimodal")
        assert isinstance(logger, MultiModalLogger)
        
        logger = get_component_logger("personalization")
        assert isinstance(logger, PersonalizationLogger)
        
        logger = get_component_logger("research_assistant")
        assert isinstance(logger, ResearchAssistantLogger)
        
        logger = get_component_logger("performance")
        assert isinstance(logger, PerformanceLogger)
        
        logger = get_component_logger("errors")
        assert isinstance(logger, ErrorLogger)
    
    def test_get_component_logger_unknown_component(self):
        """Test getting logger for unknown component."""
        logger = get_component_logger("unknown_component")
        assert isinstance(logger, ComponentLogger)
        assert logger.component_name == "unknown_component"
    
    @patch('backend.rl.utils.logging_config.Path')
    def test_setup_logging(self, mock_path):
        """Test setup_logging function."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            mock_logger.handlers = []  # No existing handlers
            
            setup_logging(LogLevel.DEBUG, enable_structured_logging=True)
            
            # Verify logger configuration
            mock_get_logger.assert_called_with("rl")
            mock_logger.setLevel.assert_called_with(logging.DEBUG)
            
            # Verify directory creation
            mock_path_instance.mkdir.assert_called_with(parents=True, exist_ok=True)
            
            # Verify handlers were added
            assert mock_logger.addHandler.call_count >= 2  # At least console and file handlers


class TestLoggingIntegration:
    """Integration tests for logging system."""
    
    def test_end_to_end_logging_flow(self):
        """Test complete logging flow from component to file."""
        component_name = f"integration_test_{id(self)}"
        logger = ComponentLogger(component_name, LogLevel.DEBUG)
        
        # Test that logging doesn't raise exceptions
        logger.debug("Debug message", test_param="debug_value")
        logger.info("Info message", test_param="info_value")
        logger.warning("Warning message", test_param="warning_value")
        logger.error("Error message", test_param="error_value")
        logger.critical("Critical message", test_param="critical_value")
    
    def test_structured_logging_json_format(self):
        """Test that structured logging produces valid JSON."""
        formatter = StructuredFormatter()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message with data",
            args=(),
            exc_info=None
        )
        record.component = "test_component"
        record.user_id = "user123"
        record.processing_time = 1.5
        
        formatted = formatter.format(record)
        
        # Should be valid JSON
        parsed = json.loads(formatted)
        assert isinstance(parsed, dict)
        assert parsed['message'] == "Test message with data"
        assert parsed['component'] == "test_component"
        assert parsed['user_id'] == "user123"
        assert parsed['processing_time'] == 1.5
    
    def test_logger_hierarchy_isolation(self):
        """Test that different component loggers are isolated."""
        logger1 = ComponentLogger("component1", LogLevel.DEBUG)
        logger2 = ComponentLogger("component2", LogLevel.INFO)
        
        assert logger1.logger.name == "rl.component1"
        assert logger2.logger.name == "rl.component2"
        assert logger1.logger.level == logging.DEBUG
        assert logger2.logger.level == logging.INFO


if __name__ == "__main__":
    pytest.main([__file__])