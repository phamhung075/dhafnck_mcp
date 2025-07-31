# Docker CLI System - Testing Guide

## Overview

This guide covers the comprehensive testing strategy for the Docker CLI System, including Test-Driven Development (TDD) practices, test infrastructure, and best practices for maintaining high-quality code.

## Test-Driven Development (TDD)

### TDD Workflow

The Docker CLI System follows a strict TDD approach:

```
1. Write Test (RED)
   └─> Test fails (no implementation)
   
2. Write Code (GREEN)
   └─> Minimal code to pass test
   
3. Refactor (REFACTOR)
   └─> Improve code quality
   └─> Tests still pass
   
4. Repeat
   └─> Next feature/test
```

### TDD Benefits

- **Design First**: Tests drive better API design
- **Confidence**: Changes don't break existing functionality
- **Documentation**: Tests serve as usage examples
- **Debugging**: Failures pinpoint exact issues
- **Coverage**: Ensures all features are tested

## Test Infrastructure

### Test Framework (`test/test_framework.sh`)

The custom test framework provides:

```bash
# Test Organization
describe "Feature Name"        # Group related tests
it "should do something"       # Individual test description

# Assertions
assert_equals               # Value equality
assert_not_equals          # Value inequality
assert_contains            # String contains substring
assert_not_contains        # String doesn't contain substring
assert_file_exists         # File existence
assert_dir_exists          # Directory existence

# Test Lifecycle
init_test_env()            # Setup test environment
cleanup_test_env()         # Cleanup after tests
run_tests()                # Execute all tests
show_test_summary()        # Display results
```

### Mock Infrastructure

#### Docker Mock System

```bash
# Mock docker command creation
create_mock_docker() {
    # Creates mock docker executable
    # Logs all calls to docker.calls
    # Routes commands to specific mocks
}

# Specific command mocks
mock_docker_compose()      # Mock docker-compose commands
mock_docker_ps()          # Mock container listings
mock_docker_exec()        # Mock container execution
mock_docker_logs()        # Mock log output
```

#### Mock Directory Structure

```
/tmp/docker-cli-test-mocks/
├── docker                 # Mock docker executable
├── docker-compose        # Mock docker-compose
├── docker.calls          # Command history
├── docker-compose.mock   # Compose behavior
├── docker-ps.mock        # PS behavior
├── docker-exec.mock      # Exec behavior
└── docker-logs.mock      # Logs behavior
```

## Test Suites

### 1. Core Commands Tests (`test_core_commands.sh`)

**Status**: ✅ 28/28 tests passing

Tests basic Docker operations:
- Service lifecycle (start/stop/restart)
- Status monitoring
- Log viewing
- Shell access
- Error handling
- Help system

Example test:
```bash
it "should start all services with 'start' command"
test_start_command() {
    # Setup
    mock_docker_compose "up -d" "Starting services..."
    
    # Execute
    output=$($DOCKER_CLI start 2>&1)
    exit_code=$?
    
    # Assert
    assert_equals 0 $exit_code "Should exit with 0"
    assert_contains "$output" "Starting DhafnckMCP services"
}
```

### 2. Database Operations Tests (`test_database_operations.sh`)

**Status**: 🚧 0/9 tests passing (not implemented)

Tests database management:
- Database initialization
- Connection testing
- Backup operations
- Restore procedures
- Migration execution
- Database shell access
- Reset functionality

Example test:
```bash
it "should initialize database"
test_db_init() {
    # Setup
    mock_docker_exec "postgres" "CREATE DATABASE"
    
    # Execute  
    output=$($DOCKER_CLI db init 2>&1)
    exit_code=$?
    
    # Assert
    assert_equals 0 $exit_code
    assert_contains "$output" "Database initialized"
}
```

### 3. Development Commands Tests (`test_development_commands.sh`)

**Status**: 🚧 0/10 tests passing (not implemented)

Tests development features:
- Environment setup
- Service building
- Test execution
- Data seeding
- Hot reload functionality

### 4. Monitoring & Health Tests (`test_monitoring_health.sh`)

**Status**: 🚧 0/9 tests passing (not implemented)

Tests system monitoring:
- Health checks
- Resource monitoring
- Performance metrics
- Diagnostic tools

### 5. Workflow Tests (`test_workflows.sh`)

**Status**: 🚧 0/9 tests passing (not implemented)

Tests automated workflows:
- Development setup
- Production deployment
- Backup/restore procedures
- System recovery

## Running Tests

### Using Make

```bash
# Run all tests
make test

# Run specific test types
make test-unit          # Unit tests only
make test-integration   # Integration tests
make test-quick        # Quick smoke tests

# Run with options
make test-verbose      # Detailed output
make test-coverage     # With coverage report

# Run specific file
make test-specific TEST_FILE=test_core_commands.sh
```

### Direct Execution

```bash
# Run all tests
bash test/run_all_tests.sh

# Run specific test file
bash test/test_core_commands.sh

# Debug mode
bash -x test/test_core_commands.sh

# With environment
DOCKER_CLI_TEST_MODE=true bash test/test_core_commands.sh
```

### Test Output

```
[0;34mTest Suite: Core Docker Commands[0m
================================
  - should start all services ... [0;32mPASS[0m
  - should stop all services ... [0;32mPASS[0m
  - should restart specific service ... [0;32mPASS[0m
  
[0;34mTest Summary[0m
================================
Total: 28
Passed: [0;32m28[0m
Failed: [0;31m0[0m
Skipped: [1;33m0[0m

[0;32mALL TESTS PASSED[0m
```

## Writing Tests

### Test Structure

```bash
#!/bin/bash
# test_new_feature.sh - Tests for new feature

# Import test framework
source "$(dirname "$0")/test_framework.sh"

# Describe test suite
describe "New Feature"

# Individual test
it "should perform expected action"
test_new_feature_action() {
    # 1. Setup - Prepare test environment
    local test_data="test input"
    mock_docker_compose "command" "expected output"
    
    # 2. Execute - Run the command
    output=$($DOCKER_CLI new-feature $test_data 2>&1)
    exit_code=$?
    
    # 3. Assert - Verify results
    assert_equals 0 $exit_code "Should succeed"
    assert_contains "$output" "Success" "Should show success"
    assert_file_exists "/tmp/output.txt" "Should create output"
}

# Run all tests
run_tests
```

### Best Practices

1. **Test Naming**
   ```bash
   # Good test names
   it "should start all services when start command is run"
   it "should show error when invalid service name provided"
   
   # Bad test names
   it "test1"
   it "works"
   ```

2. **Test Independence**
   ```bash
   # Each test should:
   - Setup its own environment
   - Not depend on other tests
   - Clean up after itself
   - Run in any order
   ```

3. **Comprehensive Assertions**
   ```bash
   # Don't just test happy path
   assert_equals 0 $exit_code
   assert_contains "$output" "expected text"
   assert_not_contains "$output" "error"
   assert_docker_compose_called_with "up -d"
   ```

4. **Mock Appropriately**
   ```bash
   # Mock external dependencies
   mock_docker_compose "ps" "container list"
   
   # Don't mock internal functions
   # Test those through integration
   ```

## Test Categories

### Unit Tests

Test individual functions in isolation:
- Single responsibility
- Mock all dependencies
- Fast execution
- High coverage

Example:
```bash
test_validate_service_name() {
    # Test just the validation function
    output=$(validate_service_name "backend")
    assert_equals 0 $? "Valid service should pass"
    
    output=$(validate_service_name "invalid")
    assert_not_equals 0 $? "Invalid service should fail"
}
```

### Integration Tests

Test module interactions:
- Multiple components
- Real dependencies where possible
- Slower but more realistic
- End-to-end scenarios

Example:
```bash
test_full_startup_sequence() {
    # Test complete startup flow
    output=$($DOCKER_CLI start 2>&1)
    assert_contains "$output" "Checking Docker"
    assert_contains "$output" "Creating network"
    assert_contains "$output" "Starting services"
    assert_contains "$output" "All services started"
}
```

### Smoke Tests

Quick validation tests:
- Critical functionality only
- Fast execution
- Run frequently
- Early warning system

```bash
# make test-quick runs smoke tests
test_cli_responds() {
    output=$($DOCKER_CLI help 2>&1)
    assert_equals 0 $?
}
```

## Debugging Tests

### Common Issues

1. **Mock Not Found**
   ```bash
   # Error: Mock docker-compose not configured
   # Fix: Ensure mock is set up before test
   mock_docker_compose "up -d" "output"
   ```

2. **Path Issues**
   ```bash
   # Error: docker-cli.sh not found
   # Fix: Check DOCKER_CLI variable
   DOCKER_CLI="./docker-cli.sh"
   ```

3. **Permission Errors**
   ```bash
   # Error: Permission denied
   # Fix: Set execute permissions
   chmod +x test/*.sh
   ```

### Debug Techniques

1. **Verbose Output**
   ```bash
   # Run with bash debug mode
   bash -x test/test_core_commands.sh
   
   # Add debug prints
   echo "DEBUG: output='$output'" >&2
   ```

2. **Check Mock Calls**
   ```bash
   # Examine what was called
   cat /tmp/docker-cli-test-mocks/docker.calls
   ```

3. **Isolate Tests**
   ```bash
   # Run single test function
   source test/test_framework.sh
   init_test_env
   test_specific_function
   ```

4. **Environment Issues**
   ```bash
   # Verify test mode is set
   echo "TEST_MODE: $DOCKER_CLI_TEST_MODE"
   
   # Check mock PATH
   echo "PATH: $PATH"
   which docker
   ```

## Test Coverage

### Current Coverage

```
Module                  | Tests | Passing | Coverage
------------------------|-------|---------|----------
Core Commands          | 28    | 28      | 100%
Database Operations    | 9     | 0       | 0%
Development Commands   | 10    | 0       | 0%
Monitoring & Health    | 9     | 0       | 0%
Workflows             | 9     | 0       | 0%
------------------------|-------|---------|----------
Total                  | 65    | 28      | 43%
```

### Coverage Goals

- **Minimum**: 80% coverage per module
- **Target**: 90% overall coverage
- **Critical**: 100% for core functionality

### Measuring Coverage

```bash
# Run with coverage analysis
make test-coverage

# Manual coverage check
# Count tested vs total functions
grep -c "^function\|^[a-z_]*(" lib/*.sh
grep -c "test_" test/*.sh
```

## Continuous Integration

### Pre-commit Checks

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run tests before commit
make test-quick || {
    echo "Tests failed. Commit aborted."
    exit 1
}
```

### CI Pipeline

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: make test
```

## Test Maintenance

### Adding Tests

1. **New Feature Process**
   ```bash
   # 1. Create test file
   touch test/test_new_feature.sh
   
   # 2. Write failing tests
   # 3. Run to confirm failure
   make test-specific TEST_FILE=test_new_feature.sh
   
   # 4. Implement feature
   # 5. Run tests until passing
   ```

2. **Bug Fix Process**
   ```bash
   # 1. Write test that reproduces bug
   # 2. Confirm test fails
   # 3. Fix bug
   # 4. Confirm test passes
   # 5. Run all tests to ensure no regression
   ```

### Updating Tests

- Keep tests in sync with implementation
- Update when requirements change
- Remove obsolete tests
- Refactor for clarity

### Test Reviews

Check for:
- Clear test descriptions
- Proper assertions
- Mock usage
- Cleanup procedures
- Error scenarios

## Performance Testing

### Load Testing

```bash
# Test concurrent operations
for i in {1..10}; do
    ./docker-cli.sh status &
done
wait
```

### Stress Testing

```bash
# Test resource limits
while true; do
    ./docker-cli.sh logs backend --tail 1000
done
```

### Benchmark Testing

```bash
# Measure operation time
time ./docker-cli.sh start
time ./docker-cli.sh db backup
```

## Security Testing

### Input Validation

```bash
# Test command injection
./docker-cli.sh logs "backend; rm -rf /"

# Test path traversal  
./docker-cli.sh shell "../../../etc/passwd"
```

### Permission Testing

```bash
# Test without permissions
chmod 000 docker-cli.sh
./docker-cli.sh start  # Should fail gracefully
```

## Test Reports

### Generating Reports

```bash
# Generate test report
make test > test-report.txt 2>&1

# Generate JUnit XML (with enhancement)
make test-junit > test-results.xml
```

### Report Format

```
Test Report - $(date)
====================

Environment:
- OS: Linux
- Docker: 20.10.0
- Bash: 5.0

Results:
- Total: 65 tests
- Passed: 28
- Failed: 0
- Skipped: 37
- Coverage: 43%

Details:
[Test output...]
```

## Troubleshooting Tests

### Common Problems

1. **Tests Pass Individually but Fail Together**
   - Check for shared state
   - Ensure proper cleanup
   - Look for timing issues

2. **Tests Fail in CI but Pass Locally**
   - Check environment differences
   - Verify dependencies
   - Check file permissions

3. **Flaky Tests**
   - Add wait conditions
   - Increase timeouts
   - Mock time-dependent operations

### Getting Help

1. Check test output carefully
2. Review test framework source
3. Use debug techniques
4. Ask for code review

---

*Remember: A failing test is better than no test. Write tests first, make them pass, then refactor.*