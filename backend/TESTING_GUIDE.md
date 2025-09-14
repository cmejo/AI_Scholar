# Backend Service Restoration Testing Guide

This guide covers the comprehensive testing suite implemented for the backend service restoration project.

## Overview

The testing suite includes comprehensive tests for:
- **Service Manager**: Service initialization, health monitoring, and error handling
- **Conditional Importer**: Safe imports, retry logic, caching, and error handling  
- **API Endpoints**: Functionality, validation, error handling, and performance

## Test Structure

### Test Categories

#### Unit Tests (`-m unit`)
- Test individual components in isolation
- Mock external dependencies
- Fast execution (< 1 second per test)
- High coverage of edge cases

#### Integration Tests (`-m integration`)
- Test component interactions
- Real service dependencies where possible
- Moderate execution time (1-10 seconds per test)
- End-to-end workflows

#### Performance Tests (`-m performance`)
- Load testing and benchmarking
- Concurrent request handling
- Response time validation
- Resource usage monitoring

### Test Files

```
tests/
├── test_service_manager.py              # ServiceManager unit tests
├── test_conditional_importer.py         # ConditionalImporter unit tests
├── test_service_integration.py          # Service integration tests
├── test_service_dependency_validation.py # Dependency validation tests
├── test_advanced_endpoints.py           # Endpoint functionality tests
├── test_endpoint_validation.py          # Request/response validation tests
└── test_endpoint_performance.py         # Performance and load tests
```

## Running Tests

### Quick Start

```bash
# Run all tests
python run_comprehensive_tests.py

# Run with verbose output
python run_comprehensive_tests.py --verbose

# Run with coverage reporting
python run_comprehensive_tests.py --coverage
```

### Test Categories

```bash
# Run only unit tests
python run_comprehensive_tests.py --unit

# Run only integration tests
python run_comprehensive_tests.py --integration

# Run only performance tests
python run_comprehensive_tests.py --performance
```

### Component-Specific Tests

```bash
# Run service manager tests only
python run_comprehensive_tests.py --service-manager

# Run conditional importer tests only
python run_comprehensive_tests.py --conditional-importer

# Run endpoint tests only
python run_comprehensive_tests.py --endpoints
```

### Advanced Options

```bash
# Run tests in parallel
python run_comprehensive_tests.py --parallel

# Run with coverage and parallel execution
python run_comprehensive_tests.py --coverage --parallel --verbose
```

### Direct pytest Usage

```bash
# Run specific test file
pytest tests/test_service_manager.py -v

# Run specific test class
pytest tests/test_service_manager.py::TestServiceManager -v

# Run specific test method
pytest tests/test_service_manager.py::TestServiceManager::test_service_manager_initialization -v

# Run with markers
pytest -m "unit and service_manager" -v

# Run with coverage
pytest --cov=core --cov=api --cov-report=html tests/
```

## Test Configuration

### pytest.ini Settings

The test suite uses `pytest_comprehensive.ini` for configuration:

- **Test Discovery**: Automatically finds test files matching `test_*.py`
- **Markers**: Categorizes tests by type and component
- **Timeouts**: 300-second timeout for long-running tests
- **Coverage**: Configured for core and api modules
- **Logging**: Detailed logging for debugging

### Environment Setup

Tests require the following dependencies:

```bash
pip install pytest pytest-asyncio pytest-cov pytest-xdist
```

Optional dependencies for enhanced testing:
```bash
pip install pytest-benchmark pytest-timeout pytest-mock
```

## Test Implementation Details

### Service Manager Tests

**File**: `tests/test_service_manager.py`

Tests cover:
- Service initialization and registration
- Health monitoring and caching
- Error handling and recovery
- Dependency validation
- Concurrent operations

**Key Test Classes**:
- `TestServiceManager`: Core functionality
- `TestServiceManagerIntegration`: Multi-service scenarios

### Conditional Importer Tests

**File**: `tests/test_conditional_importer.py`

Tests cover:
- Safe module imports with fallbacks
- Retry logic with exponential backoff
- Import caching and performance
- Error handling for various failure modes
- Decorator functionality

**Key Test Classes**:
- `TestConditionalImporter`: Core import functionality
- `TestConditionalImportDecorator`: Decorator usage
- `TestRequireServiceDecorator`: Service requirement decorator

### Service Integration Tests

**File**: `tests/test_service_integration.py`

Tests cover:
- Database service initialization
- Semantic search service setup
- Multi-service dependency chains
- Health check integration
- Service failure and recovery

### Dependency Validation Tests

**File**: `tests/test_service_dependency_validation.py`

Tests cover:
- Dependency resolution algorithms
- Circular dependency detection
- Missing dependency handling
- Dependency health cascading
- Complex dependency scenarios

### Endpoint Tests

**File**: `tests/test_advanced_endpoints.py`

Tests cover:
- Health check endpoints
- Database endpoints
- Service-specific health checks
- Research endpoints
- Analytics endpoints
- Error handling and fallbacks

**Key Test Classes**:
- `TestHealthEndpoints`: Health check functionality
- `TestDatabaseEndpoints`: Database-related endpoints
- `TestServiceHealthEndpoints`: Individual service health
- `TestResearchEndpoints`: Research functionality
- `TestAnalyticsEndpoints`: Analytics functionality

### Endpoint Validation Tests

**File**: `tests/test_endpoint_validation.py`

Tests cover:
- Request data validation
- Response format validation
- Error response consistency
- Parameter validation
- JSON parsing and error handling

### Performance Tests

**File**: `tests/test_endpoint_performance.py`

Tests cover:
- Response time benchmarks
- Concurrent request handling
- Load testing and scalability
- Memory usage monitoring
- Throughput measurement

## Test Data and Mocking

### Mock Service Manager

Tests use a comprehensive mock service manager that simulates:
- Service registration and health tracking
- Service initialization with configurable success/failure
- Health check responses with various states
- Dependency validation

### Mock Services

Individual service mocks provide:
- Configurable health check responses
- Simulated async operations
- Error injection for testing failure scenarios
- Performance characteristics simulation

## Performance Benchmarks

### Expected Performance Metrics

| Endpoint Type | Avg Response Time | Max Response Time | Concurrent Load |
|---------------|-------------------|-------------------|-----------------|
| Health Check | < 100ms | < 500ms | 20+ concurrent |
| Search (Mock) | < 100ms | < 300ms | 15+ concurrent |
| Search (Real) | < 500ms | < 2s | 10+ concurrent |
| Analytics | < 1s | < 3s | 5+ concurrent |

### Load Testing Results

Performance tests validate:
- **Throughput**: > 10 requests/second
- **Error Rate**: < 1% under normal load
- **Memory Usage**: < 100MB increase for 100 requests
- **Scalability**: < 5x response time increase with 20x load

## Debugging Tests

### Verbose Output

```bash
python run_comprehensive_tests.py --verbose
```

### Specific Test Debugging

```bash
# Run single test with full output
pytest tests/test_service_manager.py::TestServiceManager::test_initialize_service_success -v -s

# Run with pdb debugger
pytest tests/test_service_manager.py::TestServiceManager::test_initialize_service_success --pdb
```

### Log Analysis

Tests generate detailed logs for debugging:
- Service initialization steps
- Health check results
- Error conditions and recovery
- Performance metrics

## Coverage Reports

### Generating Coverage

```bash
python run_comprehensive_tests.py --coverage
```

This generates:
- Terminal coverage summary
- HTML coverage report in `htmlcov/`
- Coverage data in `.coverage`

### Coverage Targets

| Component | Target Coverage |
|-----------|----------------|
| Service Manager | > 90% |
| Conditional Importer | > 95% |
| API Endpoints | > 85% |
| Error Handlers | > 80% |

## Continuous Integration

### GitHub Actions Integration

```yaml
name: Backend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      - name: Run comprehensive tests
        run: |
          cd backend
          python run_comprehensive_tests.py --coverage --parallel
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run tests before commit
pre-commit run --all-files
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure PYTHONPATH includes backend directory
2. **Async Test Failures**: Check pytest-asyncio installation
3. **Performance Test Timeouts**: Increase timeout in pytest.ini
4. **Mock Service Issues**: Verify mock setup in test fixtures

### Test Environment

Ensure clean test environment:
```bash
# Clear pytest cache
pytest --cache-clear

# Remove coverage data
rm -f .coverage
rm -rf htmlcov/

# Clean Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete
```

## Contributing

### Adding New Tests

1. Follow existing test patterns and naming conventions
2. Use appropriate markers (`@pytest.mark.unit`, etc.)
3. Include docstrings explaining test purpose
4. Mock external dependencies appropriately
5. Add performance benchmarks for new endpoints

### Test Review Checklist

- [ ] Tests cover happy path and error cases
- [ ] Appropriate mocking of external dependencies
- [ ] Performance tests for new endpoints
- [ ] Documentation updated
- [ ] Coverage targets maintained

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Naming**: Test names should describe what is being tested
3. **Comprehensive Mocking**: Mock all external dependencies
4. **Performance Awareness**: Include performance validations
5. **Error Coverage**: Test all error conditions
6. **Documentation**: Document complex test scenarios

## Future Enhancements

Planned improvements:
- [ ] Property-based testing with Hypothesis
- [ ] Contract testing for API endpoints
- [ ] Chaos engineering tests
- [ ] Security testing integration
- [ ] Database integration tests with test containers