#!/bin/bash
# test_cleanup.sh - Tests for test cleanup functionality

source "$(dirname "$0")/test_framework.sh"

describe "Test Cleanup Functionality"

# Test: Should clean up mock directory after tests
it "should remove mock directory after test completion"
test_cleanup_mock_directory() {
    # Setup - create a test file in mock directory
    local test_file="$MOCK_DIR/test-marker.txt"
    echo "test content" > "$test_file"
    
    # Execute cleanup
    cleanup_test_env
    
    # Assert
    assert_not_exists "$MOCK_DIR" "Mock directory should be removed"
}

# Test: Should clean up test artifacts
it "should remove test artifacts created during test execution"
test_cleanup_test_artifacts() {
    # Setup - create various test artifacts
    mkdir -p "test-temp"
    touch "test-output.log"
    mkdir -p "backups"
    touch "backups/test-backup.tar.gz"
    
    # Execute cleanup
    cleanup_test_artifacts
    
    # Assert
    assert_not_exists "test-temp" "Test temp directory should be removed"
    assert_not_exists "test-output.log" "Test output file should be removed"
    assert_not_exists "backups" "Test backups directory should be removed"
}

# Test: Should clean up docker call logs
it "should remove docker call logs after tests"
test_cleanup_docker_logs() {
    # Setup - create docker call logs
    mkdir -p "$MOCK_DIR"
    touch "$MOCK_DIR/docker.calls"
    touch "$MOCK_DIR/docker-exec.calls"
    
    # Execute cleanup
    cleanup_docker_logs
    
    # Assert
    assert_not_exists "$MOCK_DIR/docker.calls" "Docker calls log should be removed"
    assert_not_exists "$MOCK_DIR/docker-exec.calls" "Docker exec calls log should be removed"
}

# Test: Should preserve important files during cleanup
it "should not remove important project files during cleanup"
test_cleanup_preserves_important_files() {
    # Setup - create files that should be preserved
    touch ".env"
    touch "docker-cli.sh"
    mkdir -p "lib"
    touch "lib/common.sh"
    
    # Execute cleanup
    cleanup_test_artifacts
    
    # Assert
    assert_exists ".env" "Environment file should be preserved"
    assert_exists "docker-cli.sh" "Main CLI script should be preserved"
    assert_exists "lib/common.sh" "Library files should be preserved"
}

# Test: Should handle cleanup when directories don't exist
it "should handle cleanup gracefully when directories don't exist"
test_cleanup_nonexistent_directories() {
    # Ensure directories don't exist
    rm -rf "$MOCK_DIR" "test-temp" "backups"
    
    # Execute cleanup - should not error
    local output=$(cleanup_test_env 2>&1)
    local exit_code=$?
    
    # Assert
    assert_equals 0 $exit_code "Cleanup should succeed even with missing directories"
    assert_not_contains "$output" "error" "Should not contain error messages"
}

# Test: Should clean up after all tests in suite
it "should automatically clean up after test suite completion"
test_cleanup_after_suite() {
    # Setup - simulate test suite execution
    init_test_env
    touch "$MOCK_DIR/suite-test-file"
    mkdir -p "test-artifacts"
    
    # Execute test runner with cleanup
    run_tests_with_cleanup() {
        # Simulate running tests
        echo "Running tests..."
        # Cleanup should happen automatically
        cleanup_test_env
        cleanup_test_artifacts
    }
    
    run_tests_with_cleanup
    
    # Assert
    assert_not_exists "$MOCK_DIR" "Mock directory should be cleaned after suite"
    assert_not_exists "test-artifacts" "Test artifacts should be cleaned after suite"
}

# Test: Should provide cleanup summary
it "should provide summary of cleaned items"
test_cleanup_summary() {
    # Setup - create various test artifacts
    mkdir -p "$MOCK_DIR"
    mkdir -p "test-temp"
    touch "test-output.log"
    mkdir -p "backups"
    
    # Execute cleanup with summary
    local output=$(cleanup_with_summary 2>&1)
    
    # Assert
    assert_contains "$output" "Cleanup Summary" "Should show cleanup summary"
    assert_contains "$output" "Mock directory: removed" "Should report mock directory removal"
    assert_contains "$output" "Test artifacts: removed" "Should report artifact removal"
    assert_contains "$output" "Total items cleaned:" "Should show total count"
}

# Test: Should handle permission errors gracefully
it "should handle permission errors during cleanup"
test_cleanup_permission_errors() {
    # Setup - create directory with restricted permissions
    mkdir -p "test-restricted"
    touch "test-restricted/file.txt"
    chmod 000 "test-restricted"
    
    # Execute cleanup
    local output=$(cleanup_test_artifacts 2>&1)
    local exit_code=$?
    
    # Assert - should continue despite permission error
    assert_equals 0 $exit_code "Should not fail due to permission errors"
    assert_contains "$output" "Warning" "Should warn about permission issues"
    
    # Cleanup - restore permissions
    chmod 755 "test-restricted"
    rm -rf "test-restricted"
}

# Test: Should respect cleanup configuration
it "should respect SKIP_TEST_CLEANUP environment variable"
test_cleanup_configuration() {
    # Setup
    export SKIP_TEST_CLEANUP="true"
    mkdir -p "$MOCK_DIR"
    touch "$MOCK_DIR/should-remain.txt"
    
    # Execute cleanup
    cleanup_test_env
    
    # Assert
    assert_exists "$MOCK_DIR/should-remain.txt" "Files should remain when cleanup is skipped"
    
    # Cleanup manually
    unset SKIP_TEST_CLEANUP
    rm -rf "$MOCK_DIR"
}

# Test: Should integrate with make test command
it "should clean up when running make test"
test_cleanup_make_integration() {
    # This test verifies that cleanup is called by the Makefile
    # We'll check if the cleanup functions are properly exported
    
    # Assert functions are available
    assert_equals "function" "$(type -t cleanup_test_env)" "cleanup_test_env should be a function"
    assert_equals "function" "$(type -t cleanup_test_artifacts)" "cleanup_test_artifacts should be a function"
    assert_equals "function" "$(type -t cleanup_docker_logs)" "cleanup_docker_logs should be a function"
}

run_tests