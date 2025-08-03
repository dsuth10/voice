# Testing Guide for Voice Dictation Assistant

This guide provides comprehensive information about the testing framework, how to run tests, and how to contribute to the test suite.

## Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Test Types](#test-types)
5. [Continuous Integration](#continuous-integration)
6. [Writing Tests](#writing-tests)
7. [Performance Testing](#performance-testing)
8. [Coverage Reports](#coverage-reports)
9. [Troubleshooting](#troubleshooting)

## Overview

The Voice Dictation Assistant uses a comprehensive testing framework built on pytest. The testing strategy includes:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions and workflows
- **Performance Tests**: Measure response times, memory usage, and throughput
- **Error Handling Tests**: Verify robust error recovery
- **Security Tests**: Check for vulnerabilities and best practices

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_config_manager.py   # Configuration management tests
├── test_hotkey_manager.py   # Hotkey system tests
├── test_integration_workflow.py  # End-to-end workflow tests
├── test_performance.py      # Performance benchmarks
├── test_audio_capture.py    # Audio capture tests
├── test_speech_recognition.py  # Speech recognition tests
├── test_text_formatter.py   # Text formatting tests
├── test_ai_enhancement_adapter.py  # AI processing tests
├── test_application_context.py  # Context awareness tests
└── test_user_rules_manager.py  # User rules tests
```

## Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py

# Run specific test types
python run_tests.py --type unit
python run_tests.py --type integration
python run_tests.py --type performance

# Run with coverage
python run_tests.py --type coverage
```

### Using pytest directly

```bash
# Run all tests
pytest tests/

# Run specific test types
pytest tests/ -m unit
pytest tests/ -m integration
pytest tests/ -m performance

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run in parallel
pytest tests/ -n auto

# Run with verbose output
pytest tests/ -v
```

### Advanced Options

```bash
# Include slow tests
python run_tests.py --slow

# Include performance tests
python run_tests.py --performance

# Run in parallel
python run_tests.py --parallel

# Generate HTML coverage report
python run_tests.py --html

# Verbose output
python run_tests.py --verbose

# Stop on first failure
python run_tests.py --fail-fast
```

## Test Types

### Unit Tests (`@pytest.mark.unit`)

Unit tests verify individual components in isolation using mocks for external dependencies.

**Example:**
```python
@pytest.mark.unit
def test_config_manager_initialization(self, temp_config_dir):
    """Test ConfigManager initialization with default values."""
    config_manager = ConfigManager(config_dir=temp_config_dir)
    
    assert config_manager.config_dir == temp_config_dir
    assert config_manager.config_file == os.path.join(temp_config_dir, "config.json")
```

**Best Practices:**
- Test one function/method at a time
- Use descriptive test names
- Mock external dependencies
- Test both success and failure cases
- Keep tests fast and focused

### Integration Tests (`@pytest.mark.integration`)

Integration tests verify that components work together correctly.

**Example:**
```python
@pytest.mark.integration
def test_end_to_end_dictation_workflow(self, mock_audio_data, mock_transcription_result):
    """Test the complete dictation workflow from audio capture to text insertion."""
    # Setup mocks for all components
    # Execute complete workflow
    # Verify all components were called correctly
```

**Best Practices:**
- Test complete workflows
- Mock external APIs and services
- Verify component interactions
- Test error scenarios
- Ensure realistic data flow

### Performance Tests (`@pytest.mark.performance`)

Performance tests measure response times, memory usage, and throughput.

**Example:**
```python
@pytest.mark.performance
def test_response_time_benchmark(self, mock_audio_data, performance_thresholds):
    """Test end-to-end response time performance."""
    # Run multiple iterations
    # Calculate statistics
    # Verify performance meets requirements
```

**Best Practices:**
- Run multiple iterations for statistical significance
- Measure both average and maximum times
- Monitor memory and CPU usage
- Set realistic performance thresholds
- Test under different load conditions

### Windows-Specific Tests (`@pytest.mark.windows`)

Tests that require Windows-specific functionality.

**Example:**
```python
@pytest.mark.windows
def test_windows_api_integration(self, mock_windows_api):
    """Test Windows API integration."""
    # Test Windows-specific functionality
```

## Continuous Integration

The project uses GitHub Actions for continuous integration with the following jobs:

### Test Job
- Runs on Windows with Python 3.10 and 3.11
- Executes unit, integration, and performance tests
- Generates coverage reports
- Uploads coverage to Codecov

### Lint Job
- Runs code quality checks (flake8, black, isort, mypy)
- Ensures consistent code style
- Checks for type errors

### Security Job
- Runs security scanning (bandit, safety)
- Identifies potential vulnerabilities
- Checks for known security issues

### Build Job
- Builds the package for distribution
- Creates artifacts for deployment

## Writing Tests

### Test Structure

```python
import pytest
from unittest.mock import patch, MagicMock

class TestComponentName:
    """Test cases for ComponentName class."""
    
    @pytest.mark.unit
    def test_method_name(self, fixture_name):
        """Test description."""
        # Arrange
        # Act
        # Assert
```

### Fixtures

Common fixtures are defined in `conftest.py`:

- `temp_config_dir`: Temporary directory for configuration files
- `mock_audio_data`: Mock audio data for testing
- `mock_transcription_result`: Mock transcription results
- `mock_windows_api`: Mock Windows API calls
- `performance_thresholds`: Performance thresholds for testing

### Mocking

Use mocks to isolate components and control external dependencies:

```python
@patch('external.library.Class')
def test_with_mock(self, mock_class):
    mock_instance = MagicMock()
    mock_class.return_value = mock_instance
    mock_instance.method.return_value = "expected_result"
    
    # Test implementation
    result = component.method()
    assert result == "expected_result"
    mock_instance.method.assert_called_once()
```

### Assertions

Use descriptive assertions and custom error messages:

```python
def test_validation(self):
    result = validate_input("invalid")
    assert result is False, f"Expected validation to fail for invalid input"
    
    result = validate_input("valid")
    assert result is True, f"Expected validation to pass for valid input"
```

## Performance Testing

### Response Time Testing

```python
@pytest.mark.performance
def test_response_time(self):
    start_time = time.time()
    # Execute operation
    end_time = time.time()
    
    response_time = end_time - start_time
    assert response_time < 5.0, f"Response time {response_time:.2f}s exceeds threshold"
```

### Memory Usage Testing

```python
@pytest.mark.performance
def test_memory_usage(self):
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Execute operations
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    memory_increase = final_memory - initial_memory
    assert memory_increase < 50, f"Memory increase {memory_increase:.1f}MB too high"
```

### Stress Testing

```python
@pytest.mark.performance
def test_stress_test(self):
    num_iterations = 100
    successful_operations = 0
    
    for _ in range(num_iterations):
        try:
            # Execute operation
            successful_operations += 1
        except Exception:
            continue
    
    success_rate = successful_operations / num_iterations
    assert success_rate > 0.95, f"Success rate {success_rate:.2f} too low"
```

## Coverage Reports

### Generating Coverage Reports

```bash
# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html

# Generate XML coverage report (for CI)
pytest tests/ --cov=src --cov-report=xml

# Generate terminal coverage report
pytest tests/ --cov=src --cov-report=term-missing
```

### Coverage Thresholds

The project enforces a minimum coverage threshold of 80%. Coverage reports show:

- Line coverage percentage
- Missing lines
- Branch coverage
- Function coverage

### Viewing Coverage Reports

After generating HTML coverage reports:

1. Open `htmlcov/index.html` in a web browser
2. Navigate through the source code
3. View coverage statistics for each file
4. Identify uncovered code paths

## Troubleshooting

### Common Issues

#### Test Failures

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Mock Issues**: Check mock setup and assertions
   ```python
   # Verify mock was called correctly
   mock_instance.method.assert_called_once_with(expected_args)
   ```

3. **Windows-Specific Tests**: Ensure running on Windows
   ```bash
   # Skip Windows tests on other platforms
   pytest tests/ -m "not windows"
   ```

#### Performance Test Failures

1. **Threshold Too Strict**: Adjust performance thresholds
2. **System Load**: Run tests on dedicated machine
3. **Resource Constraints**: Increase system resources

#### Coverage Issues

1. **Low Coverage**: Add tests for uncovered code paths
2. **False Negatives**: Exclude test files from coverage
3. **Missing Imports**: Check import statements

### Debugging Tests

```bash
# Run specific test with verbose output
pytest tests/test_file.py::TestClass::test_method -v -s

# Run with debugger
pytest tests/test_file.py --pdb

# Run with print statements
pytest tests/test_file.py -s
```

### Test Data

- Use realistic test data
- Include edge cases
- Test with different input sizes
- Verify output correctness

### Continuous Improvement

1. **Regular Review**: Review test coverage regularly
2. **Refactoring**: Update tests when code changes
3. **Performance**: Monitor test execution time
4. **Documentation**: Keep test documentation updated

## Contributing to Tests

### Adding New Tests

1. Create test file in `tests/` directory
2. Follow naming convention: `test_*.py`
3. Use appropriate test markers
4. Add comprehensive docstrings
5. Include both success and failure cases

### Test Guidelines

1. **Isolation**: Each test should be independent
2. **Speed**: Keep tests fast (< 1 second for unit tests)
3. **Reliability**: Tests should be deterministic
4. **Maintainability**: Use clear, readable code
5. **Coverage**: Aim for high code coverage

### Code Quality

1. **Style**: Follow PEP 8 guidelines
2. **Documentation**: Include clear docstrings
3. **Type Hints**: Use type annotations
4. **Error Handling**: Test error scenarios
5. **Edge Cases**: Include boundary conditions

## Conclusion

This testing framework ensures the Voice Dictation Assistant is reliable, performant, and maintainable. Regular testing helps catch issues early and provides confidence in the codebase.

For questions or issues with testing, please refer to the project documentation or create an issue in the repository. 