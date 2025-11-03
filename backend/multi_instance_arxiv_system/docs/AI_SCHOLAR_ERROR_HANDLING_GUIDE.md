# AI Scholar Error Handling and Logging Guide

## Overview

The AI Scholar Error Handling and Logging system provides comprehensive error management, recovery mechanisms, and detailed logging for the AI Scholar instance of the multi-instance ArXiv system. This system ensures robust operation, graceful error recovery, and detailed monitoring capabilities.

## Key Features

### ✅ Comprehensive Error Logging
- **Structured Error Categorization**: Errors are categorized by type (Network, PDF Processing, Vector Store, Storage, ArXiv API, etc.)
- **Severity Levels**: Critical, Error, Warning, Info levels for proper prioritization
- **Context-Rich Logging**: Each error includes detailed context information for debugging
- **Multiple Log Formats**: Standard text logs, structured JSON logs, and error-specific logs

### ✅ Error Report Generation
- **Detailed Failure Information**: Comprehensive reports with error patterns, statistics, and recommendations
- **HTML and JSON Reports**: Multiple output formats for different use cases
- **Historical Analysis**: Error trend analysis and pattern detection
- **Automated Recommendations**: System-generated suggestions for error resolution

### ✅ Graceful Processing Interruptions
- **Circuit Breaker Pattern**: Automatic service protection when error thresholds are exceeded
- **Graceful Shutdown**: Proper cleanup and state saving during interruptions
- **Resume Capability**: Ability to resume processing from the last successful state
- **Resource Management**: Proper cleanup of resources during failures

### ✅ Retry Logic with Exponential Backoff
- **Configurable Retry Strategies**: Different retry patterns for different error types
- **Exponential Backoff**: Intelligent delay increases to avoid overwhelming services
- **Jitter Support**: Random delays to prevent thundering herd problems
- **Maximum Attempt Limits**: Configurable limits to prevent infinite retries

## Architecture

### Error Handler Components

```
AIScholarErrorHandler
├── RetryStrategy (Exponential backoff configuration)
├── CircuitBreaker (Service protection)
├── ErrorCategorization (Error type classification)
├── PatternDetection (Error pattern analysis)
├── RecommendationEngine (Recovery suggestions)
└── ReportGeneration (Comprehensive reporting)
```

### Logging Components

```
AIScholarLoggerConfig
├── StructuredFormatter (JSON logging)
├── RotatingFileHandler (Log rotation)
├── OperationLogger (Context manager)
├── PerformanceMetrics (Timing and stats)
└── ProgressTracking (Operation progress)
```

## Usage Examples

### Basic Error Handler Setup

```python
from error_handling.ai_scholar_error_handler import AIScholarErrorHandler, ErrorCategory, ErrorSeverity

# Initialize error handler
error_handler = AIScholarErrorHandler(
    error_log_dir=Path("/path/to/logs"),
    instance_name="ai_scholar",
    processor_id="downloader_001"
)

# Log an error with context
error_handler.log_ai_scholar_error(
    Exception("Network timeout occurred"),
    {
        'operation': 'paper_download',
        'arxiv_id': '2301.12345',
        'attempt': 3
    },
    ErrorCategory.NETWORK,
    ErrorSeverity.ERROR
)
```

### Retry with Error Handling

```python
# Define operation to retry
async def download_paper(paper_id):
    # Download logic here
    return download_result

# Execute with retry and error handling
success, result, error = await error_handler.handle_with_retry(
    download_paper,
    ErrorCategory.DOWNLOAD,
    {'paper_id': 'arxiv:2301.12345'},
    paper_id='2301.12345'
)

if success:
    print(f"Download successful: {result}")
else:
    print(f"Download failed after retries: {error}")
```

### Logging Configuration

```python
from error_handling.logging_config import setup_ai_scholar_logging

# Setup comprehensive logging
config = setup_ai_scholar_logging(
    log_dir=Path("/path/to/logs"),
    instance_name="ai_scholar",
    log_level="INFO"
)

# Use operation logger for automatic timing
with config.create_operation_logger("paper_processing") as op_logger:
    op_logger.add_context(batch_size=100)
    op_logger.log_info("Starting paper processing")
    
    for i, paper in enumerate(papers):
        # Process paper
        op_logger.log_progress(i + 1, len(papers))
    
    op_logger.log_info("Processing completed")
```

### Error Report Generation

```python
# Generate comprehensive error report
summary = error_handler.get_ai_scholar_error_summary()

# Export detailed report
report_path = Path("/path/to/reports/ai_scholar_errors.json")
success = error_handler.export_ai_scholar_report(report_path)

if success:
    print(f"Error report exported to {report_path}")
```

## Error Categories and Handling

### Network Errors
- **Category**: `ErrorCategory.NETWORK`
- **Common Causes**: Connection timeouts, DNS failures, network unavailability
- **Retry Strategy**: 5 attempts with 2-120 second delays
- **Recovery**: Exponential backoff with jitter

### ArXiv API Errors
- **Category**: `ErrorCategory.ARXIV_API`
- **Common Causes**: Rate limiting, API unavailability, malformed requests
- **Retry Strategy**: 3 attempts with 3-60 second delays
- **Recovery**: Longer delays for rate limiting

### PDF Processing Errors
- **Category**: `ErrorCategory.PDF_PROCESSING`
- **Common Causes**: Corrupt PDFs, parsing failures, memory issues
- **Retry Strategy**: 2 attempts with 0.5-10 second delays
- **Recovery**: Skip corrupted files, reduce batch sizes

### Vector Store Errors
- **Category**: `ErrorCategory.VECTOR_STORE`
- **Common Causes**: ChromaDB unavailability, connection failures
- **Retry Strategy**: 3 attempts with 1-30 second delays
- **Recovery**: Service health checks, connection reinitialization

### Storage Errors
- **Category**: `ErrorCategory.STORAGE`
- **Common Causes**: Disk space full, permission issues, I/O errors
- **Retry Strategy**: 2 attempts with 0.5-5 second delays
- **Recovery**: Cleanup recommendations, space monitoring

## Circuit Breaker Configuration

### Thresholds
- **Failure Threshold**: 5 consecutive failures
- **Recovery Timeout**: 5 minutes
- **States**: Closed (normal), Open (blocked), Half-Open (testing)

### Protected Services
- ArXiv API calls
- Vector store operations
- PDF processing pipeline

## Logging Configuration

### Log Files
- **Main Log**: `ai_scholar_main.log` (50MB, 5 backups)
- **Error Log**: `ai_scholar_errors.log` (20MB, 10 backups)
- **Structured Log**: `ai_scholar_structured.jsonl` (100MB, 3 backups)

### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General operational information
- **WARNING**: Warning conditions
- **ERROR**: Error conditions
- **CRITICAL**: Critical error conditions

### Structured Logging Format

```json
{
  "timestamp": "2023-10-23T17:30:00.123456",
  "level": "ERROR",
  "logger": "ai_scholar.downloader",
  "message": "Failed to download paper",
  "module": "ai_scholar_downloader",
  "function": "download_papers",
  "line": 245,
  "extra": {
    "operation": "paper_download",
    "arxiv_id": "2301.12345",
    "error_category": "network",
    "retry_count": 3
  }
}
```

## Performance Monitoring

### Metrics Collected
- **Operation Duration**: Time taken for each operation
- **Success/Failure Rates**: Success percentage by operation type
- **Error Patterns**: Frequency and distribution of error types
- **Resource Usage**: Memory and CPU utilization during operations

### Performance Logging

```python
# Automatic performance logging with operation logger
with config.create_operation_logger("batch_processing") as op_logger:
    # Operation automatically timed and logged
    process_batch(papers)

# Manual performance logging
config.log_performance_metric(
    operation="embedding_generation",
    duration_seconds=45.2,
    success=True,
    additional_metrics={
        'papers_processed': 100,
        'memory_used_mb': 512
    }
)
```

## Error Recovery Recommendations

### Automatic Recommendations
The system generates automatic recommendations based on error patterns:

- **High Network Errors**: "Implement longer delays between requests"
- **PDF Processing Failures**: "Process PDFs in smaller batches"
- **Storage Issues**: "Free up disk space or clean old files"
- **Vector Store Errors**: "Check ChromaDB service status and connection"

### Health Status Monitoring
- **Healthy**: No recent errors, all systems operational
- **Degraded**: Some errors but within acceptable limits
- **Warning**: Error rate approaching thresholds
- **Critical**: High error rate or critical system failures

## Integration with AI Scholar Components

### Downloader Integration

```python
class AIScholarDownloader(BaseScholarDownloader):
    def __init__(self, config_path: str):
        super().__init__(config_path)
        
        # Initialize enhanced error handler
        self.ai_error_handler = AIScholarErrorHandler(
            error_dir, self.instance_name, self.current_processor_id
        )
    
    async def download_papers(self, papers):
        # Use error handler for retry logic
        success, result, error = await self.ai_error_handler.handle_with_retry(
            self._download_operation,
            ErrorCategory.DOWNLOAD,
            {'paper_count': len(papers)}
        )
        return result
```

### Processor Integration

```python
class AIScholarProcessor:
    def _log_processing_error(self, error, context, error_type):
        # Enhanced error logging with context
        enhanced_context = context.copy()
        enhanced_context.update({
            'instance_name': self.instance_name,
            'processor_type': 'ai_scholar_processor',
            'processed_documents_count': len(self.processed_documents)
        })
        
        logger.error(f"Processing error [{error_type}]: {error}", 
                    extra=enhanced_context)
```

## Testing and Validation

### Test Coverage
- ✅ Retry strategy logic
- ✅ Circuit breaker functionality
- ✅ Error categorization and pattern detection
- ✅ Error recovery recommendations
- ✅ Report generation
- ✅ Graceful interruption handling
- ✅ Logging configuration
- ✅ Performance metrics

### Running Tests

```bash
# Run basic error handling tests
python backend/multi_instance_arxiv_system/test_error_handling_simple.py

# Test logging configuration
python backend/multi_instance_arxiv_system/error_handling/logging_config.py
```

## Configuration Files

### Error Handler Configuration
Error handling behavior can be configured through the instance configuration:

```yaml
error_handling:
  retry_strategies:
    network:
      max_attempts: 5
      base_delay: 2.0
      max_delay: 120.0
    arxiv_api:
      max_attempts: 3
      base_delay: 3.0
      max_delay: 60.0
  
  circuit_breakers:
    failure_threshold: 5
    recovery_timeout: 300  # 5 minutes
  
  logging:
    level: "INFO"
    structured_logging: true
    log_rotation: true
```

### Logging Configuration
Logging can be configured per instance:

```yaml
logging:
  level: "INFO"
  directory: "/datapool/aischolar/logs"
  rotation:
    max_size_mb: 50
    backup_count: 5
  structured:
    enabled: true
    format: "json"
```

## Best Practices

### Error Handling
1. **Always use context**: Provide meaningful context with every error
2. **Categorize appropriately**: Use the correct error category for proper handling
3. **Set appropriate severity**: Use severity levels to prioritize error handling
4. **Monitor circuit breakers**: Check circuit breaker status before operations
5. **Handle interruptions gracefully**: Always save state before exiting

### Logging
1. **Use structured logging**: Prefer structured logs for analysis
2. **Include operation context**: Add relevant context to log entries
3. **Monitor log sizes**: Ensure log rotation is properly configured
4. **Use appropriate levels**: Don't over-log at DEBUG level in production
5. **Performance logging**: Always log operation timing and success rates

### Recovery
1. **Implement retry logic**: Use appropriate retry strategies for different operations
2. **Monitor error patterns**: Regularly review error reports and patterns
3. **Act on recommendations**: Follow system-generated recovery recommendations
4. **Plan for failures**: Design operations to be resumable after failures
5. **Test error scenarios**: Regularly test error handling and recovery mechanisms

## Troubleshooting

### Common Issues

#### High Error Rates
- Check network connectivity
- Verify service availability (ArXiv API, ChromaDB)
- Review resource usage (memory, disk space)
- Check configuration parameters

#### Circuit Breaker Activation
- Review recent error logs
- Check service health
- Wait for recovery timeout
- Manually reset if necessary

#### Log File Issues
- Verify log directory permissions
- Check disk space availability
- Review log rotation configuration
- Monitor log file sizes

### Debugging Steps
1. Check error logs for recent failures
2. Review circuit breaker status
3. Verify service connectivity
4. Check resource availability
5. Review configuration settings
6. Generate error report for analysis

## Conclusion

The AI Scholar Error Handling and Logging system provides comprehensive error management capabilities that ensure robust operation of the AI Scholar instance. With features like retry logic, circuit breakers, structured logging, and automatic recovery recommendations, the system can handle various failure scenarios gracefully while providing detailed insights for monitoring and debugging.

The system is designed to be:
- **Resilient**: Automatic recovery from transient failures
- **Observable**: Comprehensive logging and monitoring
- **Maintainable**: Clear error categorization and recommendations
- **Scalable**: Efficient handling of high-volume operations

Regular monitoring of error reports and following the system's recommendations will help maintain optimal performance and reliability of the AI Scholar instance.