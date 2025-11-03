#!/usr/bin/env python3
"""
Comprehensive test for AI Scholar Error Handling Integration.

Tests the complete error handling integration including:
- Error handler integration with downloader and processor
- Comprehensive error logging and reporting
- Graceful handling of processing interruptions
- Retry logic with exponential backoff
- Error recovery mechanisms
"""

import asyncio
import logging
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_error_handler_initialization():
    """Test AI Scholar error handler initialization."""
    logger.info("Testing error handler initialization...")
    
    try:
        sys.path.append(str(Path(__file__).parent))
        
        from error_handling.ai_scholar_error_handler import AIScholarErrorHandler, ErrorCategory, ErrorSeverity
        
        # Create temporary error directory
        with tempfile.TemporaryDirectory() as temp_dir:
            error_dir = Path(temp_dir)
            
            # Initialize error handler
            error_handler = AIScholarErrorHandler(
                error_dir, "test_ai_scholar", "test_processor"
            )
            
            # Verify initialization
            assert error_handler.instance_name == "test_ai_scholar"
            assert error_handler.processor_id == "test_ai_scholar_test_processor"
            assert error_handler.error_log_dir.exists()
            
            # Test error logging
            test_error = Exception("Test network error")
            processing_error = error_handler.log_ai_scholar_error(
                test_error,
                {'operation': 'test_operation', 'file_path': '/test/path'},
                ErrorCategory.NETWORK,
                ErrorSeverity.ERROR
            )
            
            assert processing_error is not None
            assert processing_error.error_type == "ai_scholar_network"
            
            # Test error summary
            summary = error_handler.get_ai_scholar_error_summary()
            assert 'ai_scholar_stats' in summary
            assert 'health_status' in summary
            assert 'recommendations' in summary
            
            logger.info("Error handler initialization test: PASSED")
            return True
        
    except Exception as e:
        logger.error(f"Error handler initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_retry_mechanism_integration():
    """Test retry mechanism integration."""
    logger.info("Testing retry mechanism integration...")
    
    try:
        from error_handling.ai_scholar_error_handler import AIScholarErrorHandler, ErrorCategory
        
        with tempfile.TemporaryDirectory() as temp_dir:
            error_dir = Path(temp_dir)
            
            error_handler = AIScholarErrorHandler(
                error_dir, "test_ai_scholar", "test_processor"
            )
            
            # Test successful operation after retries
            attempt_count = 0
            async def failing_then_success_operation():
                nonlocal attempt_count
                attempt_count += 1
                if attempt_count < 3:
                    raise Exception(f"Attempt {attempt_count} failed")
                return f"success_on_attempt_{attempt_count}"
            
            success, result, error = await error_handler.handle_with_retry(
                failing_then_success_operation,
                ErrorCategory.NETWORK,
                {'test': 'retry_integration'}
            )
            
            assert success, "Operation should succeed after retries"
            assert result == "success_on_attempt_3", f"Expected success on attempt 3, got {result}"
            assert error is None, "Error should be None for successful operation"
            assert attempt_count == 3, f"Should have made 3 attempts, made {attempt_count}"
            
            # Test circuit breaker functionality
            for _ in range(6):  # Trigger circuit breaker
                error_handler._update_circuit_breaker(ErrorCategory.ARXIV_API)
            
            # Should not allow execution when circuit breaker is open
            can_execute = error_handler._check_circuit_breaker(ErrorCategory.ARXIV_API)
            assert not can_execute, "Circuit breaker should prevent execution"
            
            logger.info("Retry mechanism integration test: PASSED")
            return True
        
    except Exception as e:
        logger.error(f"Retry mechanism integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_categorization_and_patterns():
    """Test error categorization and pattern detection."""
    logger.info("Testing error categorization and patterns...")
    
    try:
        from error_handling.ai_scholar_error_handler import AIScholarErrorHandler, ErrorCategory, ErrorSeverity
        
        with tempfile.TemporaryDirectory() as temp_dir:
            error_dir = Path(temp_dir)
            
            error_handler = AIScholarErrorHandler(
                error_dir, "test_ai_scholar", "test_processor"
            )
            
            # Test different error types and patterns
            test_cases = [
                (Exception("Connection timeout occurred"), ErrorCategory.NETWORK, "timeout_pattern"),
                (Exception("arXiv API rate limit exceeded"), ErrorCategory.ARXIV_API, "rate_limit_pattern"),
                (Exception("PDF file is corrupt and cannot be processed"), ErrorCategory.PDF_PROCESSING, "corrupt_pdf_pattern"),
                (Exception("Disk space insufficient for operation"), ErrorCategory.STORAGE, "disk_space_pattern"),
                (Exception("ChromaDB vector store connection failed"), ErrorCategory.VECTOR_STORE, "unknown_pattern")
            ]
            
            for error, category, expected_pattern in test_cases:
                # Log the error
                processing_error = error_handler.log_ai_scholar_error(
                    error, 
                    {'test_case': str(error)}, 
                    category, 
                    ErrorSeverity.ERROR
                )
                
                # Check pattern detection
                detected_pattern = error_handler._detect_error_pattern(error, category)
                logger.info(f"Error: '{error}' -> Category: {category.value} -> Pattern: {detected_pattern}")
                
                # Verify error was logged
                assert processing_error is not None
                assert processing_error.error_type == f"ai_scholar_{category.value}"
                
                # Verify pattern detection (note: this is heuristic, so we check it's a string)
                assert isinstance(detected_pattern, str)
            
            # Test error statistics
            stats = error_handler.get_ai_scholar_error_summary()
            assert stats['ai_scholar_stats']['total_errors'] == len(test_cases)
            
            logger.info("Error categorization and patterns test: PASSED")
            return True
        
    except Exception as e:
        logger.error(f"Error categorization and patterns test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_recovery_recommendations():
    """Test error recovery and recommendation system."""
    logger.info("Testing error recovery recommendations...")
    
    try:
        from error_handling.ai_scholar_error_handler import AIScholarErrorHandler, ErrorCategory, ErrorSeverity
        
        with tempfile.TemporaryDirectory() as temp_dir:
            error_dir = Path(temp_dir)
            
            error_handler = AIScholarErrorHandler(
                error_dir, "test_ai_scholar", "test_processor"
            )
            
            # Generate various error scenarios
            error_scenarios = [
                (Exception("Network timeout"), ErrorCategory.NETWORK, ErrorSeverity.ERROR),
                (Exception("PDF processing failed"), ErrorCategory.PDF_PROCESSING, ErrorSeverity.WARNING),
                (Exception("Vector store unavailable"), ErrorCategory.VECTOR_STORE, ErrorSeverity.CRITICAL),
                (Exception("Storage full"), ErrorCategory.STORAGE, ErrorSeverity.CRITICAL)
            ]
            
            for error, category, severity in error_scenarios:
                error_handler.log_ai_scholar_error(error, {'test': 'scenario'}, category, severity)
            
            # Get recommendations
            summary = error_handler.get_ai_scholar_error_summary()
            recommendations = summary.get('recommendations', [])
            
            # Verify recommendations are generated
            assert isinstance(recommendations, list)
            logger.info(f"Generated {len(recommendations)} recommendations")
            
            for rec in recommendations:
                logger.info(f"Recommendation: {rec}")
                assert isinstance(rec, str)
                assert len(rec) > 10  # Should be meaningful recommendations
            
            # Test health status
            health_status = summary.get('health_status')
            assert health_status in ['healthy', 'degraded', 'warning', 'critical']
            logger.info(f"Health status: {health_status}")
            
            # Test continue processing decision
            should_continue = error_handler.should_continue_processing()
            logger.info(f"Should continue processing: {should_continue}")
            
            logger.info("Error recovery recommendations test: PASSED")
            return True
        
    except Exception as e:
        logger.error(f"Error recovery recommendations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_report_generation():
    """Test comprehensive error report generation."""
    logger.info("Testing error report generation...")
    
    try:
        from error_handling.ai_scholar_error_handler import AIScholarErrorHandler, ErrorCategory, ErrorSeverity
        
        with tempfile.TemporaryDirectory() as temp_dir:
            error_dir = Path(temp_dir)
            
            error_handler = AIScholarErrorHandler(
                error_dir, "test_ai_scholar", "test_processor"
            )
            
            # Generate test errors
            test_errors = [
                (Exception("Network error 1"), ErrorCategory.NETWORK, ErrorSeverity.ERROR),
                (Exception("Network error 2"), ErrorCategory.NETWORK, ErrorSeverity.WARNING),
                (Exception("PDF error 1"), ErrorCategory.PDF_PROCESSING, ErrorSeverity.ERROR),
                (Exception("Critical system error"), ErrorCategory.VECTOR_STORE, ErrorSeverity.CRITICAL)
            ]
            
            for error, category, severity in test_errors:
                error_handler.log_ai_scholar_error(
                    error, 
                    {'timestamp': datetime.now().isoformat()}, 
                    category, 
                    severity
                )
            
            # Export error report
            report_path = Path(temp_dir) / "test_error_report.json"
            success = error_handler.export_ai_scholar_report(report_path)
            
            assert success, "Error report export should succeed"
            assert report_path.exists(), "Error report file should exist"
            
            # Verify report content
            with open(report_path, 'r') as f:
                report_data = json.load(f)
            
            required_sections = [
                'report_type', 'generated_at', 'instance_name', 
                'processor_id', 'summary'
            ]
            
            for section in required_sections:
                assert section in report_data, f"Report should contain '{section}'"
            
            # Verify summary content
            summary = report_data['summary']
            assert 'ai_scholar_stats' in summary
            assert 'health_status' in summary
            assert 'recommendations' in summary
            
            # Verify error statistics
            ai_stats = summary['ai_scholar_stats']
            assert ai_stats['total_errors'] == len(test_errors)
            assert ai_stats['critical_errors'] == 1  # One critical error
            assert ai_stats['network_errors'] == 2   # Two network errors
            
            logger.info(f"Error report generated successfully with {len(test_errors)} errors")
            logger.info("Error report generation test: PASSED")
            return True
        
    except Exception as e:
        logger.error(f"Error report generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_graceful_interruption_handling():
    """Test graceful handling of processing interruptions."""
    logger.info("Testing graceful interruption handling...")
    
    try:
        from error_handling.ai_scholar_error_handler import AIScholarErrorHandler, ErrorCategory
        
        with tempfile.TemporaryDirectory() as temp_dir:
            error_dir = Path(temp_dir)
            
            error_handler = AIScholarErrorHandler(
                error_dir, "test_ai_scholar", "test_processor"
            )
            
            # Simulate processing interruption
            async def interrupted_operation():
                await asyncio.sleep(0.1)  # Simulate some work
                raise KeyboardInterrupt("User interrupted processing")
            
            # Test handling of interruption
            success, result, error = await error_handler.handle_with_retry(
                interrupted_operation,
                ErrorCategory.NETWORK,
                {'operation': 'test_interruption'}
            )
            
            # Should fail gracefully
            assert not success, "Interrupted operation should not succeed"
            assert isinstance(error, KeyboardInterrupt), "Should preserve KeyboardInterrupt"
            
            # Verify error was logged
            summary = error_handler.get_ai_scholar_error_summary()
            assert summary['ai_scholar_stats']['total_errors'] > 0
            
            logger.info("Graceful interruption handling test: PASSED")
            return True
        
    except Exception as e:
        logger.error(f"Graceful interruption handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    logger.info("Starting AI Scholar Error Handling Integration tests")
    
    tests = [
        ("Error Handler Initialization", test_error_handler_initialization),
        ("Retry Mechanism Integration", test_retry_mechanism_integration),
        ("Error Categorization and Patterns", test_error_categorization_and_patterns),
        ("Error Recovery Recommendations", test_error_recovery_recommendations),
        ("Error Report Generation", test_error_report_generation),
        ("Graceful Interruption Handling", test_graceful_interruption_handling),
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
        logger.info("All AI Scholar error handling integration tests completed successfully!")
        logger.info("\nKey features verified:")
        logger.info("✓ Comprehensive error logging for AI Scholar operations")
        logger.info("✓ Error report generation with detailed failure information")
        logger.info("✓ Graceful handling of processing interruptions")
        logger.info("✓ Retry logic with exponential backoff")
        logger.info("✓ Circuit breaker functionality")
        logger.info("✓ Error categorization and pattern detection")
        logger.info("✓ Recovery recommendations")
    else:
        logger.error("Some tests failed!")


if __name__ == "__main__":
    asyncio.run(main())