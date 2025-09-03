# Zotero Integration Testing Guide

This guide provides comprehensive information about the Zotero integration test suite, including how to run tests locally, understand test results, and contribute to the testing framework.

## Table of Contents

1. [Overview](#overview)
2. [Test Suite Structure](#test-suite-structure)
3. [Running Tests Locally](#running-tests-locally)
4. [CI/CD Integration](#cicd-integration)
5. [Test Categories](#test-categories)
6. [Performance Benchmarks](#performance-benchmarks)
7. [Troubleshooting](#troubleshooting)
8. [Contributing](#contributing)

## Overview

The Zotero integration test suite is designed to validate all aspects of the Zotero integration functionality, from basic authentication to complex AI-enhanced features. The test suite includes:

- **End-to-end workflow tests** - Complete user journeys from authentication to citation generation
- **Performance tests** - Load testing and performance validation under various conditions
- **Stress tests** - System behavior under extreme load and edge conditions
- **CI/CD tests** - Automated validation for continuous integration pipelines

## Test Suite Structure

```
backend/tests/
├── test_zotero_integration_comprehensive.py    # End-to-end integration tests
├── test_zotero_performance_comprehensive.py    # Performance and load tests
├── test_zotero_stress_comprehensive.py         # Stress tests under extreme conditions
└── test_zotero_ci_cd_integration.py           # CI/CD pipeline validation tests

backend/
├── run_zotero_integration_tests.py            # Legacy test runner
├── run_comprehensive_integration_tests.py     # New comprehensive test runner
├── pytest_integration.ini                     # Pytest configuration for integration tests
└── docs/INTEGRATION_TESTING_GUIDE.md         # This guide
```

## Running Tests Locally

### Prerequisites

1. **Python Environment**
   ```bash
   cd backend
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. **Redis Server** (for caching tests)
   ```bash
   # Using Docker
   docker run -d -p 6379:6379 redis:7-alpine
   
   # Or install locally
   sudo apt-get install redis-server  # Ubuntu/Debian
   brew install redis                  # macOS
   ```

3. **Environment Variables**
   ```bash
   export ENVIRONMENT=test
   export DATABASE_URL=sqlite:///test_zotero.db
   export REDIS_URL=redis://localhost:6379/15
   export TESTING=true
   ```

### Quick Start

Run smoke tests for quick validation:
```bash
cd backend
python run_comprehensive_integration_tests.py --smoke
```

### Test Runner Options

The comprehensive test runner provides multiple options:

```bash
# Run all tests
python run_comprehensive_integration_tests.py --all

# Run specific test suites
python run_comprehensive_integration_tests.py --integration
python run_comprehensive_integration_tests.py --performance
python run_comprehensive_integration_tests.py --stress
python run_comprehensive_integration_tests.py --ci

# Run with coverage reporting
python run_comprehensive_integration_tests.py --integration --coverage

# Run with parallel execution (not recommended for CI)
python run_comprehensive_integration_tests.py --integration --parallel --workers 4

# Verbose output for debugging
python run_comprehensive_integration_tests.py --smoke --verbose

# Keep test artifacts for analysis
python run_comprehensive_integration_tests.py --integration --keep-artifacts
```

### Direct Pytest Execution

You can also run tests directly with pytest:

```bash
# Run integration tests with custom configuration
pytest -c pytest_integration.ini tests/test_zotero_integration_comprehensive.py -v

# Run specific test class
pytest tests/test_zotero_integration_comprehensive.py::TestZoteroEndToEndWorkflows -v

# Run with markers
pytest -m "integration and not slow" -v

# Run with coverage
pytest --cov=services.zotero --cov-report=html tests/test_zotero_integration_comprehensive.py
```

## CI/CD Integration

### GitHub Actions Workflow

The test suite is integrated with GitHub Actions for automated testing:

- **Trigger Conditions:**
  - Push to main/develop branches
  - Pull requests affecting Zotero code
  - Scheduled nightly runs
  - Manual workflow dispatch

- **Test Matrix:**
  - Multiple Python versions (3.10, 3.11, 3.12)
  - Different test suites based on trigger type
  - Parallel execution for faster feedback

- **Artifact Collection:**
  - Test reports (HTML and JSON)
  - Coverage reports
  - Performance metrics
  - Failure logs and screenshots

### Local CI Simulation

Test your changes as they would run in CI:

```bash
# Simulate CI environment
export CI=true
export GITHUB_ACTIONS=true
python run_comprehensive_integration_tests.py --ci --verbose
```

## Test Categories

### 1. Integration Tests (`@pytest.mark.integration`)

**Purpose:** Validate complete end-to-end workflows

**Key Test Cases:**
- Complete OAuth authentication flow
- Library synchronization with large datasets
- Search functionality across different data types
- Citation generation in multiple formats
- AI analysis integration
- Real-time synchronization
- Collaborative features

**Performance Expectations:**
- OAuth flow: < 5 seconds
- Library sync (1000 items): < 60 seconds
- Search queries: < 2 seconds
- Citation generation (100 items): < 10 seconds

### 2. Performance Tests (`@pytest.mark.performance`)

**Purpose:** Validate system performance under load

**Key Test Cases:**
- Large library sync (10,000+ items)
- Concurrent user operations
- Search performance with massive datasets
- Bulk citation generation
- Memory usage optimization
- AI analysis performance

**Performance Benchmarks:**
- Sync rate: > 50 items/second
- Search response: < 3 seconds (10,000 items)
- Memory usage: < 1GB for 10,000 items
- Concurrent users: 10+ simultaneous operations

### 3. Stress Tests (`@pytest.mark.stress`)

**Purpose:** Test system behavior under extreme conditions

**Key Test Cases:**
- Extreme concurrent operations (50+ users)
- Sustained load over extended periods
- Memory leak detection
- Massive dataset handling (50,000+ items)
- Resource exhaustion scenarios

**Stress Thresholds:**
- Concurrent users: 50+ simultaneous
- Success rate: > 80% under extreme load
- Memory growth: < 2MB/hour sustained
- Dataset size: 50,000+ items

### 4. CI/CD Tests (`@pytest.mark.ci`)

**Purpose:** Validate deployment and configuration

**Key Test Cases:**
- Health check endpoints
- API endpoint availability
- Database connectivity
- Environment configuration
- Security headers
- Rate limiting
- Dependency versions

**CI Requirements:**
- All health checks pass
- No missing dependencies
- Proper security configuration
- Fast execution (< 20 minutes)

## Performance Benchmarks

### Sync Performance

| Dataset Size | Expected Time | Memory Usage | Items/Second |
|-------------|---------------|--------------|--------------|
| 100 items   | < 5s         | < 50MB       | > 20         |
| 1,000 items | < 30s        | < 200MB      | > 30         |
| 10,000 items| < 120s       | < 1GB        | > 50         |
| 50,000 items| < 600s       | < 3GB        | > 80         |

### Search Performance

| Dataset Size | Query Type | Expected Time | Memory Usage |
|-------------|------------|---------------|--------------|
| 1,000 items | Simple     | < 0.5s       | < 10MB       |
| 10,000 items| Simple     | < 1.5s       | < 50MB       |
| 10,000 items| Complex    | < 3.0s       | < 100MB      |
| 50,000 items| Complex    | < 5.0s       | < 200MB      |

### Citation Performance

| Item Count | Style | Expected Time | Memory Usage |
|-----------|-------|---------------|--------------|
| 10 items  | Any   | < 1s         | < 5MB        |
| 100 items | Any   | < 5s         | < 20MB       |
| 500 items | Any   | < 15s        | < 50MB       |
| 1000 items| Any   | < 30s        | < 100MB      |

## Troubleshooting

### Common Issues

#### 1. Redis Connection Errors
```
ConnectionError: Error 111 connecting to localhost:6379
```

**Solution:**
```bash
# Start Redis server
docker run -d -p 6379:6379 redis:7-alpine
# Or
sudo systemctl start redis-server
```

#### 2. Database Connection Issues
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table
```

**Solution:**
```bash
# Initialize test database
cd backend
python -c "
from core.database import engine, Base
Base.metadata.create_all(bind=engine)
"
```

#### 3. Import Errors
```
ModuleNotFoundError: No module named 'services.zotero'
```

**Solution:**
```bash
# Set PYTHONPATH
export PYTHONPATH=$PWD/backend:$PYTHONPATH
# Or run from backend directory
cd backend
python run_comprehensive_integration_tests.py --smoke
```

#### 4. Memory Issues During Large Tests
```
MemoryError: Unable to allocate array
```

**Solution:**
- Reduce test dataset size for local testing
- Increase system memory or swap
- Run tests with smaller batch sizes

#### 5. Timeout Issues
```
pytest.timeout.TimeoutExpired: Test timed out after 300 seconds
```

**Solution:**
```bash
# Increase timeout
python run_comprehensive_integration_tests.py --integration --timeout 1800
# Or run specific test
pytest tests/test_zotero_integration_comprehensive.py::specific_test --timeout=600
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Set debug environment
export LOG_LEVEL=DEBUG
export TESTING_DEBUG=true

# Run with verbose output
python run_comprehensive_integration_tests.py --smoke --verbose --keep-artifacts
```

### Performance Debugging

Profile test performance:

```bash
# Install profiling tools
pip install py-spy memory-profiler

# Profile memory usage
mprof run python run_comprehensive_integration_tests.py --performance
mprof plot

# Profile CPU usage
py-spy record -o profile.svg -- python run_comprehensive_integration_tests.py --performance
```

## Contributing

### Adding New Tests

1. **Choose the appropriate test file:**
   - `test_zotero_integration_comprehensive.py` - End-to-end workflows
   - `test_zotero_performance_comprehensive.py` - Performance tests
   - `test_zotero_stress_comprehensive.py` - Stress tests
   - `test_zotero_ci_cd_integration.py` - CI/CD validation

2. **Follow naming conventions:**
   ```python
   @pytest.mark.integration  # or performance, stress, ci
   class TestZoteroNewFeature:
       def test_new_feature_workflow(self, test_client, test_data):
           """Test description following requirements."""
           # Test implementation
   ```

3. **Include proper assertions:**
   ```python
   # Performance assertions
   assert response_time < 5.0
   assert memory_usage < 100  # MB
   
   # Functional assertions
   assert response.status_code == 200
   assert "expected_field" in response.json()
   
   # Data integrity assertions
   assert len(results) == expected_count
   assert all(item["required_field"] for item in results)
   ```

4. **Add appropriate markers:**
   ```python
   @pytest.mark.integration
   @pytest.mark.slow  # If test takes > 30 seconds
   def test_large_dataset_processing(self):
       # Test implementation
   ```

### Test Data Management

Create realistic test data:

```python
@pytest.fixture
def realistic_zotero_data(self):
    """Generate realistic test data based on actual Zotero structures."""
    return {
        'libraries': [
            {
                'id': 'test-lib-123',
                'type': 'user',
                'name': 'Test Library',
                'version': 100
            }
        ],
        'items': [
            {
                'key': 'TEST123',
                'itemType': 'journalArticle',
                'title': 'Realistic Test Article',
                'creators': [
                    {'creatorType': 'author', 'firstName': 'John', 'lastName': 'Doe'}
                ],
                'publicationTitle': 'Test Journal',
                'date': '2023',
                'abstractNote': 'This is a realistic test abstract.',
                'tags': [{'tag': 'test'}, {'tag': 'research'}]
            }
        ]
    }
```

### Performance Test Guidelines

1. **Set realistic expectations:**
   ```python
   # Good: Realistic performance expectation
   assert sync_duration < 60.0  # 1 minute for 1000 items
   
   # Bad: Unrealistic expectation
   assert sync_duration < 1.0   # 1 second for 1000 items
   ```

2. **Include resource monitoring:**
   ```python
   import psutil
   
   process = psutil.Process(os.getpid())
   memory_before = process.memory_info().rss / 1024 / 1024  # MB
   
   # Perform operation
   
   memory_after = process.memory_info().rss / 1024 / 1024  # MB
   memory_increase = memory_after - memory_before
   
   assert memory_increase < 100  # Less than 100MB increase
   ```

3. **Test with various dataset sizes:**
   ```python
   @pytest.mark.parametrize("dataset_size", [100, 1000, 5000])
   def test_sync_performance_scaling(self, dataset_size):
       # Test should scale appropriately with dataset size
   ```

### Code Review Checklist

- [ ] Tests follow naming conventions
- [ ] Appropriate markers are applied
- [ ] Performance expectations are realistic
- [ ] Error cases are handled
- [ ] Test data is realistic and comprehensive
- [ ] Documentation is updated
- [ ] CI/CD integration works correctly

## Best Practices

### Test Organization

1. **Group related tests in classes**
2. **Use descriptive test names**
3. **Include docstrings with requirement references**
4. **Organize fixtures logically**
5. **Keep tests independent and idempotent**

### Performance Testing

1. **Set realistic benchmarks based on requirements**
2. **Monitor system resources during tests**
3. **Test with various dataset sizes**
4. **Include both average and worst-case scenarios**
5. **Document performance expectations clearly**

### CI/CD Integration

1. **Keep CI tests fast and focused**
2. **Use appropriate timeouts**
3. **Generate comprehensive reports**
4. **Handle flaky tests appropriately**
5. **Provide clear failure messages**

### Debugging and Maintenance

1. **Use verbose logging for complex tests**
2. **Keep test artifacts for analysis**
3. **Regular review and update of benchmarks**
4. **Monitor test execution times**
5. **Update tests when requirements change**

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Zotero API Documentation](https://www.zotero.org/support/dev/web_api/v3/start)
- [Performance Testing Best Practices](https://martinfowler.com/articles/practical-test-pyramid.html)

## Support

For questions or issues with the test suite:

1. Check this documentation first
2. Review existing test implementations
3. Check GitHub Issues for known problems
4. Create a new issue with detailed information about the problem

---

*Last updated: January 2025*