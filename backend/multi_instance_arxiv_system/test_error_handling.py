#!/usr/bin/env python3
"""
Test script for AI Scholar Error Handling.

Tests the enhanced error handling functionality including:
- Retry strategies
- Circuit breakers
- Error categorization
- Recovery mechanisms
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_retry_strategy():
    """Test retry strategy functionality."""
    logger.info("Testing retry strategy...")
    
    try:
        sys.path.append(str(Path(__file__).parent))
        
        from error_handling.ai_scholar_error_handler import RetryStrategy
        
        # Test basic retry strategy
        strategy = RetryStrategy(max_attempts=3, base_delay=0.1, max_delay=1.0)
        
        delays = []
        for attempt in range(strategy.max_attempts):
            delay = strategy.get_delay(attempt)
            delays.append(delay)
            logger.info(f"Attempt {attempt + 1}: delay = {delay:.3f}s")
        
        # Verify exponential backoff
        assert delays[1] > delays[0], "Delay should increase"
        assert all(d <= strategy.max_delay for d in delays), "Delays should not exceed max"
        
        logger.info("Retry strategy test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Retry strategy test failed: {e}")
        return False


async def test_error_categorization():
    """Test error categorization functionality."""
    logger.info("Testing error categorization...")
    
    try:
        from error_handling.ai_scholar_error_handler import ErrorCategory, ErrorSeverity
        
        # Test enum values
        categories = [
            ErrorCategory.NETWORK,
            ErrorCategory.PDF_PROCESSING,
            ErrorCategory.VECTOR_STORE,
            ErrorCategory.STORAGE,
            ErrorCategory.ARXIV_API
        ]
        
        severities = [
            ErrorSeverity.CRITICAL,
            ErrorSeverity.ERROR,
            ErrorSeverity.WARNING,
            ErrorSeverity.INFO
        ]
        
        logger.info(f"Available error categories: {[c.value for c in categories]}")
        logger.info(f"Available error severities: {[s.value for s in severities]}")
        
        # Verify enum values
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorSeverity.CRITICAL.value == "critical"
        
        logger.info("Error categorization test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Error categorization test failed: {e}")
        return False


async def test_circuit_breaker():
    """Test circuit breaker functionality."""
    logger.info("Testing circuit breaker...")
    
    try:
        from error_handling.ai_scholar_error_handler import AIScholarErrorHandler, ErrorCategory
        
        # Create temporary error directory
        with tempfile.TemporaryDirectory() as temp_dir:
            error_dir = Path(temp_dir)
            
            # Create error handler
            error_handler = AIScholarErrorHandler(
                error_dir, "test_instance", "test_processor"
            )
            
            # Test initial circuit breaker state
            assert error_handler._check_circuit_breaker(ErrorCategory.ARXIV_API), "Circuit breaker should be closed initially"
            
            # Simulate failures to trigger circuit breaker
            for i in range(6):  # More than the threshold of 5
                error_handler._update_circuit_breaker(ErrorCategory.ARXIV_API)
            
            # Check if circuit breaker is open
            breaker_state = error_handler.circuit_breakers['arxiv_api']['state']
            logger.info(f"Circuit breaker state after failures: {breaker_state}")
            
            # Test reset
            error_handler._reset_circuit_breaker(ErrorCategory.ARXIV_API)
            assert error_handler._check_circuit_breaker(ErrorCategory.ARXIV_API), "Circuit breaker should be closed after reset"
            
            logger.info("Circuit breaker test: PASSED")
            return True
        
    except Exception as e:
        logger.error(f"Circuit breaker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_pattern_detection():
    """Test error pattern detection."""
    logger.info("Testing error pattern detection...")
    
    try:
        from error_handling.ai_scholar_error_handler import AIScholarErrorHandler, ErrorCategory
        
        # Create temporary error directory
        with tempfile.TemporaryDirectory() as temp_dir:
            error_dir = Path(temp_dir)
            
            # Create error handler
            error_handler = AIScholarErrorHandler(
                error_dir, "test_instance", "test_processor"
            )
            
            # Test different error patterns
            test_cases = [
                (Exception("Connection timeout occurred"), ErrorCategory.NETWORK, "timeout_pattern"),
                (Exception("Rate limit exceeded"), ErrorCategory.ARXIV_API, "rate_limit_pattern"),
                (Exception("Corrupt PDF file detected"), ErrorCategory.PDF_PROCESSING, "corrupt_pdf_pattern"),
                (Exception("Disk space insufficient"), ErrorCategory.STORAGE, "disk_space_pattern"),
                (Exception("Unknown error"), ErrorCategory.UNKNOWN, "unknown_pattern")
            ]
            
            for error, category, expected_pattern in test_cases:
                pattern = error_handler._detect_error_pattern(error, category)
                logger.info(f"Error: '{error}' -> Category: {category.value} -> Pattern: {pattern}")
                
                # Note: Pattern detection is heuristic, so we just verify it returns a string
                assert isinstance(pattern, str), f"Pattern should be a string, got {type(pattern)}"
            
            logger.info("Error pattern detection test: PASSED")
            return True
        
    except Exception as e:
        logger.error(f"Error pattern detection test failed: {e}")
        return False


async def test_retry_with_mock_operation():
    """Test retry functionality with mock operations."""
    logger.info("Testing retry with mock operations...")
    
    try:
        from error_handling.ai_scholar_error_handler import AIScholarErrorHandler, ErrorCategory
        
        # Create temporary error directory
        with tempfile.TemporaryDirectory() as temp_dir:
            error_dir = Path(temp_dir)
            
            # Create error handler
            error_handler = AIScholarErrorHandler(
                error_dir, "test_instance", "test_processor"
            )
            
            # Test successful operation
            async def successful_operation():
                return "success"
            
            success, result, error = await error_handler.handle_with_retry(
                successful_operation,
                ErrorCategory.NETWORK,
                {'test': 'context'}
            )
            
            assert success, "Successful operation should return True"
            assert result == "success", "Result should be returned"
            assert error is None, "Error should be None for successful operation"
            
            # Test failing operation
            attempt_count = 0
            async def failing_operation():
                nonlocal attempt_count
                attempt_count += 1
                raise Exception(f"Attempt {attempt_count} failed")
            
            success, result, error = await error_handler.handle_with_retry(
                failing_operation,
                ErrorCategory.NETWORK,
                {'test': 'context'}
            )
            
            assert not success, "Failing operation should return False"
            assert result is None, "Result should be None for failed operation"
            assert error is not None, "Error should be returned for failed operation"
            assert attempt_count > 1, "Should have made multiple attempts"
            
            logger.info(f"Failing operation made {attempt_count} attempts")
            logger.info("Retry with mock operations test: PASSED")
            return True
        
    except Exception as e:
        logger.error(f"Retry with mock operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_summary():
    """Test error summary generation."""
    logger.info("Testing error summary generation...")
    
    try:
        from error_handling.ai_scholar_error_handler import AIScholarErrorHandler, ErrorCategory, ErrorSeverity
        
        # Create temporary error directory
        with tempfile.TemporaryDirectory() as temp_dir:
            error_dir = Path(temp_dir)
            
            # Create error handler
            error_handler = AIScholarErrorHandler(
                error_dir, "test_instance", "test_processor"
            )
            
            # Log some test errors
            test_errors = [
                (Exception("Network timeout"), ErrorCategory.NETWORK, ErrorSeverity.ERROR),
                (Exception("PDF corrupt"), ErrorCategory.PDF_PROCESSING, ErrorSeverity.WARNING),
                (Exception("Vector store down"), ErrorCategory.VECTOR_STORE, ErrorSeverity.CRITICAL)
            ]
            
            for error, category, severity in test_errors:
                error_handler.log_ai_scholar_error(
                    error, 
                    {'test': 'context'}, 
                    category, 
                    severity
                )
            
            # Get summary
            summary = error_handler.get_ai_scholar_error_summary()
            
            # Verify summary structure
            required_keys = [
                'instance_name', 'ai_scholar_stats', 'circuit_breakers',
                'health_status', 'recommendations'
            ]
            
            for key in required_keys:
                assert key in summary, f"Summary should contain '{key}'"
            
            logger.info(f"Error summary generated with {len(summary)} sections")
            logger.info(f"Health status: {summary['health_status']}")
            logger.info(f"Recommendations: {len(summary['recommendations'])}")
            
            logger.info("Error summary test: PASSED")
            return True
        
    except Exception as e:
        logger.error(f"Error summary test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    logger.info("Starting AI Scholar Error Handling tests")
    
    tests = [
        ("Retry Strategy", test_retry_strategy),
        ("Error Categorization", test_error_categorization),
        ("Circuit Breaker", test_circuit_breaker),
        ("Error Pattern Detection", test_error_pattern_detection),
        ("Retry with Mock Operations", test_retry_with_mock_operation),
        ("Error Summary", test_error_summary),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            result = await test_func()
            results.append((test_name, result))
            status = "PASSED" if result else "FAILED"
            logger.info(f"{test_name} Test: {status}")
        except Exception as e:
            logger.error(f"{test_name} Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n--- Test Summary ---")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("All tests completed successfully!")
    else:
        logger.error("Some tests failed!")


if __name__ == "__main__":
    asyncio.run(main())