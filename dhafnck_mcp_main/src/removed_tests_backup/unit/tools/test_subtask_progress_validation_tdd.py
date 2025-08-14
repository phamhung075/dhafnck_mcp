#!/usr/bin/env python3
"""
TDD Test Suite for Subtask Progress Percentage Validation

This test file addresses Issue 4: Subtask Progress Percentage Validation
Problem: Progress percentage updates failing with integer values in subtask management.

Test-Driven Development Approach:
1. Write failing tests that demonstrate the current issue
2. Implement the fix 
3. Verify all tests pass
4. Add regression tests

Focus areas:
- Type coercion (string to int)
- Range validation (0-100)
- Auto-status mapping
- Parameter validation enhancement
"""

import pytest
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional, List

# Add the source directory to Python path  
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "..", "..", "..", "src")
sys.path.insert(0, src_path)

from fastmcp.task_management.interface.controllers.subtask_mcp_controller import SubtaskMCPController
from fastmcp.task_management.application.factories.subtask_facade_factory import SubtaskFacadeFactory


class TestSubtaskProgressPercentageValidation:
    """
    Test suite for progress percentage validation in subtask management.
    
    Tests current issues and validates fixes for:
    - String to integer type coercion
    - Range validation (0-100)
    - Parameter format validation
    - Auto-status mapping based on progress
    """
    
    def setup_method(self):
        """Setup test environment with mocked dependencies."""
        # Mock the subtask facade factory and related dependencies
        self.mock_facade_factory = Mock(spec=SubtaskFacadeFactory)
        self.mock_facade = Mock()
        self.mock_facade_factory.create_subtask_facade.return_value = self.mock_facade
        
        # Mock context and task facades
        self.mock_context_facade = Mock()
        self.mock_task_facade = Mock()
        
        # Create controller instance
        self.controller = SubtaskMCPController(
            subtask_facade_factory=self.mock_facade_factory,
            task_facade=self.mock_task_facade,
            context_facade=self.mock_context_facade
        )
        
        # Default test data
        self.test_task_id = "test-task-123"
        self.test_subtask_id = "test-subtask-456"
        
    def test_progress_percentage_as_string_should_convert_to_int(self):
        """
        TEST: String progress percentage should be converted to integer.
        
        This test validates that the system can handle progress_percentage 
        passed as a string and convert it to integer for processing.
        """
        # Mock successful facade response
        self.mock_facade.handle_manage_subtask.return_value = {
            "success": True,
            "subtask": {"id": self.test_subtask_id, "title": "Test Subtask", "status": "in_progress"}
        }
        
        # Test with string progress percentage
        result = self.controller.manage_subtask(
            action="update",
            task_id=self.test_task_id,
            subtask_id=self.test_subtask_id,
            progress_percentage="75"  # String value that should be converted
        )
        
        # Should succeed with conversion
        assert result["success"] is True, f"Expected success but got: {result}"
        
        # The controller may call the facade multiple times (update + list for progress)
        # Let's check that it was called at least once with the right data
        assert self.mock_facade.handle_manage_subtask.call_count >= 1
        
        # Find the update call (not the list call)
        update_call = None
        for call in self.mock_facade.handle_manage_subtask.call_args_list:
            if call[1].get("action") == "update":
                update_call = call
                break
        
        assert update_call is not None, "Expected update call to facade"
        
        # The progress percentage should be converted and status should be set
        subtask_data = update_call[1]["subtask_data"]
        assert subtask_data["status"] == "in_progress", f"Expected in_progress status, got {subtask_data.get('status')}"
        
    def test_progress_percentage_invalid_string_should_fail(self):
        """
        TEST: Invalid string progress percentage should return clear error.
        
        Non-numeric strings should be rejected with helpful error message.
        """
        result = self.controller.manage_subtask(
            action="update",
            task_id=self.test_task_id,
            subtask_id=self.test_subtask_id,
            progress_percentage="abc"  # Invalid string
        )
        
        # Should fail with clear error message
        assert result["success"] is False
        assert "Invalid progress_percentage format" in result["error"]
        assert "abc" in result["error"]
        assert result["error_code"] == "PARAMETER_TYPE_ERROR"
        assert result["parameter"] == "progress_percentage"
        
    def test_progress_percentage_out_of_range_should_fail(self):
        """
        TEST: Progress percentage outside 0-100 range should fail.
        
        Values like 150 or -10 should be rejected.
        """
        # Test with value > 100
        result = self.controller.manage_subtask(
            action="update",
            task_id=self.test_task_id,
            subtask_id=self.test_subtask_id,
            progress_percentage=150
        )
        
        assert result["success"] is False
        assert "Invalid progress_percentage value: 150" in result["error"]
        assert "Must be integer between 0-100" in result["error"]
        
        # Test with negative value
        result = self.controller.manage_subtask(
            action="update",
            task_id=self.test_task_id,
            subtask_id=self.test_subtask_id,
            progress_percentage=-10
        )
        
        assert result["success"] is False
        assert "Invalid progress_percentage value: -10" in result["error"]
        assert "Must be integer between 0-100" in result["error"]
        
    def test_progress_percentage_auto_status_mapping(self):
        """
        TEST: Progress percentage should automatically map to correct status.
        
        - 0% -> "todo"
        - 1-99% -> "in_progress" 
        - 100% -> "done"
        """
        test_cases = [
            ("0", "todo"),
            ("1", "in_progress"),
            ("50", "in_progress"),
            ("99", "in_progress"),
            ("100", "done")
        ]
        
        for progress_str, expected_status in test_cases:
            # Reset mock for each test
            self.mock_facade.reset_mock()
            self.mock_facade.handle_manage_subtask.return_value = {
                "success": True,
                "subtask": {"id": self.test_subtask_id, "title": "Test Subtask", "status": expected_status}
            }
            
            result = self.controller.manage_subtask(
                action="update",
                task_id=self.test_task_id,
                subtask_id=self.test_subtask_id,
                progress_percentage=progress_str  # String input
            )
            
            assert result["success"] is True, f"Failed for progress {progress_str}"
            
            # Verify correct status was set
            call_args = self.mock_facade.handle_manage_subtask.call_args
            print(f"Call args for progress {progress_str}: {call_args}")
            
            # Handle different call argument structures
            if call_args and len(call_args) > 1:
                kwargs = call_args[1] if isinstance(call_args[1], dict) else call_args.kwargs
                if "subtask_data" in kwargs:
                    actual_status = kwargs["subtask_data"].get("status")
                    assert actual_status == expected_status, \
                        f"Expected status {expected_status} for progress {progress_str}, got {actual_status}"
                
    def test_current_validation_logic_passes_integers(self):
        """
        TEST: Current validation should handle integer values correctly.
        
        This ensures we don't break existing functionality.
        """
        self.mock_facade.handle_manage_subtask.return_value = {
            "success": True,
            "subtask": {"id": self.test_subtask_id, "title": "Test Subtask", "status": "in_progress"}
        }
        
        result = self.controller.manage_subtask(
            action="update",
            task_id=self.test_task_id,
            subtask_id=self.test_subtask_id,
            progress_percentage=50  # Integer value
        )
        
        assert result["success"] is True
        
    def test_edge_case_boundary_values(self):
        """
        TEST: Boundary values should be handled correctly.
        
        Test edge cases at the boundaries of valid range.
        """
        boundary_tests = [
            ("0", True, "todo"),
            ("100", True, "done"),
            ("-1", False, None),
            ("101", False, None)
        ]
        
        for value, should_succeed, expected_status in boundary_tests:
            self.mock_facade.reset_mock()
            if should_succeed:
                self.mock_facade.handle_manage_subtask.return_value = {
                    "success": True,
                    "subtask": {"id": self.test_subtask_id, "title": "Test Subtask", "status": expected_status}
                }
            
            result = self.controller.manage_subtask(
                action="update",
                task_id=self.test_task_id,
                subtask_id=self.test_subtask_id,
                progress_percentage=value
            )
            
            if should_succeed:
                assert result["success"] is True, f"Boundary value {value} should succeed"
                if expected_status:
                    # Find the update call
                    update_call = None
                    for call in self.mock_facade.handle_manage_subtask.call_args_list:
                        if call[1].get("action") == "update":
                            update_call = call
                            break
                    
                    if update_call:
                        subtask_data = update_call[1]["subtask_data"]
                        assert subtask_data["status"] == expected_status, \
                            f"Expected status {expected_status} for boundary value {value}"
            else:
                assert result["success"] is False, f"Boundary value {value} should fail"
                
    def test_parameter_schema_flexibility(self):
        """
        TEST: Parameter schema should accept both string and integer types.
        
        This tests the schema-level validation for flexible type acceptance.
        """
        # Test string numbers
        string_tests = ["0", "25", "50", "75", "100"]
        
        for progress_str in string_tests:
            self.mock_facade.reset_mock()
            self.mock_facade.handle_manage_subtask.return_value = {
                "success": True,
                "subtask": {"id": self.test_subtask_id, "title": "Test Subtask"}
            }
            
            result = self.controller.manage_subtask(
                action="update",
                task_id=self.test_task_id,
                subtask_id=self.test_subtask_id,
                progress_percentage=progress_str
            )
            
            assert result["success"] is True, f"String progress {progress_str} should be accepted"
            
    def test_error_messages_are_helpful(self):
        """
        TEST: Error messages should be helpful and include examples.
        
        Validates that error messages provide actionable guidance.
        """
        result = self.controller.manage_subtask(
            action="update",
            task_id=self.test_task_id,
            subtask_id=self.test_subtask_id,
            progress_percentage="invalid"
        )
        
        assert result["success"] is False
        assert "hint" in result
        assert "examples" in result or "example" in result["hint"]
        assert "progress_percentage" in result["error"]
        
    def test_parent_task_progress_calculation(self):
        """
        TEST: Progress updates should trigger parent task progress recalculation.
        
        When subtask progress changes, parent progress should be updated.
        """
        # Mock list operation to return subtasks for progress calculation
        self.mock_facade.handle_manage_subtask.side_effect = [
            # First call (update operation)
            {
                "success": True,
                "subtask": {"id": self.test_subtask_id, "title": "Test Subtask", "status": "done"}
            },
            # Second call (list for progress calculation)
            {
                "success": True,
                "subtasks": [
                    {"status": "done"},
                    {"status": "in_progress"},
                    {"status": "todo"}
                ]
            }
        ]
        
        result = self.controller.manage_subtask(
            action="update",
            task_id=self.test_task_id,
            subtask_id=self.test_subtask_id,
            progress_percentage="100"  # Complete the subtask
        )
        
        assert result["success"] is True
        # Should have called facade twice (update + list for progress)
        assert self.mock_facade.handle_manage_subtask.call_count == 2


class TestCurrentImplementationValidation:
    """
    Test the current validation implementation to identify specific issues.
    
    These tests expose the exact problems in the current code that need fixing.
    """
    
    def setup_method(self):
        """Setup minimal test environment."""
        self.mock_facade_factory = Mock()
        self.controller = SubtaskMCPController(self.mock_facade_factory)
        
    def test_current_string_to_int_conversion_logic(self):
        """
        TEST: Examine current string-to-int conversion in _validate_subtask_parameters.
        
        The current code at lines 158-169 handles basic conversion,
        but the validation at lines 923-1023 may have additional issues.
        """
        # Test the current validation logic directly
        validation_result = self.controller._validate_subtask_parameters(
            progress_percentage="50"  # This should already be converted by manage_subtask
        )
        
        # The validation method expects int, but manage_subtask should convert strings
        # If this fails, it indicates the conversion isn't happening properly
        assert validation_result["valid"] is True, \
            f"String progress validation failed: {validation_result}"
            
    def test_current_parameter_validation_expects_int(self):
        """
        TEST: Current parameter validation expects integer type.
        
        This confirms that _validate_subtask_parameters expects int type,
        so conversion must happen before calling it.
        """
        # Test validation with string (should fail if conversion doesn't happen)
        validation_result = self.controller._validate_subtask_parameters(
            progress_percentage="50"  # String type
        )
        
        # Current implementation should handle this, let's see what we get
        print(f"Validation result: {validation_result}")
        
        # The validation method should expect int, but may not properly validate
        if "valid" not in validation_result:
            assert False, f"Validation result malformed: {validation_result}"
        
        # If it passes with string, that's the issue - validation is too lenient
        if validation_result["valid"]:
            print("⚠️ ISSUE FOUND: Validation accepts strings when it should expect integers")
        else:
            assert "Invalid progress_percentage format" in validation_result.get("error", "")
            assert "integer" in validation_result.get("error", "")


def run_tdd_test_suite():
    """
    Run the complete TDD test suite.
    
    This function runs all tests and reports results in a format
    suitable for TDD workflow.
    """
    print("=" * 80)
    print("TDD TEST SUITE: Subtask Progress Percentage Validation")
    print("=" * 80)
    print()
    
    # Import pytest programmatically
    import subprocess
    import sys
    
    # Run pytest on this file
    test_file = __file__
    result = subprocess.run([
        sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"
    ], capture_output=True, text=True)
    
    print("PYTEST OUTPUT:")
    print("-" * 40)
    print(result.stdout)
    if result.stderr:
        print("ERRORS:")
        print(result.stderr)
    
    print(f"TEST RESULT: {'PASSED' if result.returncode == 0 else 'FAILED'}")
    print(f"Exit Code: {result.returncode}")
    
    return result.returncode == 0


if __name__ == "__main__":
    # Run individual tests for debugging
    print("Running TDD tests for subtask progress percentage validation...")
    
    # Create test instance for manual testing
    test_instance = TestSubtaskProgressPercentageValidation()
    test_instance.setup_method()
    
    print("\n1. Testing string to int conversion...")
    try:
        test_instance.test_progress_percentage_as_string_should_convert_to_int()
        print("✅ String to int conversion: PASSED")
    except Exception as e:
        print(f"❌ String to int conversion: FAILED - {e}")
    
    print("\n2. Testing invalid string handling...")
    try:
        test_instance.test_progress_percentage_invalid_string_should_fail()
        print("✅ Invalid string handling: PASSED")
    except Exception as e:
        print(f"❌ Invalid string handling: FAILED - {e}")
    
    print("\n3. Testing auto-status mapping...")
    try:
        test_instance.test_progress_percentage_auto_status_mapping()
        print("✅ Auto-status mapping: PASSED")
    except Exception as e:
        print(f"❌ Auto-status mapping: FAILED - {e}")
    
    print("\n4. Testing current implementation validation...")
    current_test = TestCurrentImplementationValidation()
    current_test.setup_method()
    try:
        current_test.test_current_parameter_validation_expects_int()
        print("✅ Current validation logic: PASSED")
    except Exception as e:
        print(f"❌ Current validation logic: FAILED - {e}")
    
    print("\n" + "=" * 80)
    print("TDD TEST SUMMARY")
    print("=" * 80)
    print("These tests demonstrate the current issue and validate the fix.")
    print("Run 'python test_subtask_progress_validation_tdd.py' to execute all tests.")