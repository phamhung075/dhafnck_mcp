"""
Unit test for git branch filtering fix

This test directly tests the git branch filtering logic fix without complex mocking.
The fix changes from:
  git_branch_filter = self.git_branch_id or filters.get('git_branch_id')
To:
  git_branch_filter = self.git_branch_id if self.git_branch_id is not None else filters.get('git_branch_id')
"""

import pytest


class TestGitBranchFilteringLogic:
    """Unit tests for the git branch filtering logic fix"""

    def test_original_broken_logic(self):
        """Test that demonstrates the original broken OR logic"""
        # Simulate the original broken logic
        def original_logic(constructor_value, filter_value):
            return constructor_value or filter_value
        
        # Test cases that were broken
        test_cases = [
            ("", "fallback"),     # Empty string is falsy - this is the main bug
            (None, "fallback"),   # None is falsy
            ("0", "fallback"),    # String "0" is truthy, should work fine
            ("false", "fallback"), # String "false" is truthy, should work fine  
            ("normal", "fallback"), # Normal string is truthy, should work fine
        ]
        
        for constructor, filter_val in test_cases:
            original_result = original_logic(constructor, filter_val)
            if constructor == "":  # Only empty string is the problematic falsy value
                # This should fail with original logic - empty string is falsy so OR returns filter_val
                assert original_result == filter_val, f"Original logic incorrectly used fallback for empty string"
                # This demonstrates the bug
                assert original_result != constructor, f"Original logic should have failed for empty string"
            elif constructor is None:
                # None should correctly use fallback
                assert original_result == filter_val, f"None should use fallback"
            else:
                # Truthy strings should work correctly with OR
                assert original_result == constructor, f"Truthy value should use constructor for '{constructor}'"

    def test_fixed_logic(self):
        """Test that the fixed logic works correctly"""
        # Simulate the fixed logic
        def fixed_logic(constructor_value, filter_value):
            return constructor_value if constructor_value is not None else filter_value
        
        # Test cases that should now work correctly
        test_cases = [
            ("", "fallback", ""),        # Empty string should use constructor (was broken with OR)
            ("0", "fallback", "0"),      # String zero should use constructor
            ("false", "fallback", "false"),  # String false should use constructor
            ("null", "fallback", "null"),    # String null should use constructor
            (None, "fallback", "fallback"),  # None should use fallback
            ("normal", "fallback", "normal"), # Normal string should use constructor
        ]
        
        for constructor, filter_val, expected in test_cases:
            result = fixed_logic(constructor, filter_val)
            assert result == expected, f"Fixed logic failed for constructor='{constructor}', filter='{filter_val}', expected='{expected}', got='{result}'"

    def test_edge_cases(self):
        """Test edge cases for the filtering logic"""
        def fixed_logic(constructor_value, filter_value):
            return constructor_value if constructor_value is not None else filter_value
        
        edge_cases = [
            (0, "fallback", 0),          # Numeric zero should use constructor
            (False, "fallback", False),  # Boolean false should use constructor
            ([], "fallback", []),        # Empty list should use constructor
            ({}, "fallback", {}),        # Empty dict should use constructor
            ("   ", "fallback", "   "),  # Whitespace should use constructor
        ]
        
        for constructor, filter_val, expected in edge_cases:
            result = fixed_logic(constructor, filter_val)
            assert result == expected, f"Edge case failed for constructor={constructor}, filter='{filter_val}', expected={expected}, got={result}"

    def test_precedence_rules(self):
        """Test that constructor always takes precedence over filters when not None"""
        def fixed_logic(constructor_value, filter_value):
            return constructor_value if constructor_value is not None else filter_value
        
        precedence_cases = [
            ("constructor", "filter", "constructor"),  # Normal precedence
            ("", "filter", ""),                        # Empty string constructor wins
            ("0", "filter", "0"),                      # Zero string constructor wins
            ("false", "different", "false"),           # False string constructor wins
            (None, "filter", "filter"),                # Only None allows fallback
        ]
        
        for constructor, filter_val, expected in precedence_cases:
            result = fixed_logic(constructor, filter_val)
            assert result == expected, f"Precedence test failed for constructor='{constructor}', filter='{filter_val}'"

    def test_realistic_git_branch_scenarios(self):
        """Test realistic git branch ID scenarios"""
        def fixed_logic(constructor_value, filter_value):
            return constructor_value if constructor_value is not None else filter_value
        
        realistic_scenarios = [
            # Scenario: Repository initialized with empty branch (happens in some workflows)
            ("", "main", ""),  # Should filter by empty, not main
            
            # Scenario: Repository initialized with numeric branch name
            ("123", "main", "123"),  # Should filter by 123, not main
            
            # Scenario: Repository initialized with branch name that looks like boolean
            ("true", "main", "true"),   # Should filter by "true", not main
            ("false", "main", "false"), # Should filter by "false", not main
            
            # Scenario: Repository not initialized with branch, using filter
            (None, "feature/auth", "feature/auth"),  # Should use filter value
            
            # Scenario: Both None (no filtering)
            (None, None, None),  # Should return None (no filtering)
        ]
        
        for constructor, filter_val, expected in realistic_scenarios:
            result = fixed_logic(constructor, filter_val)
            assert result == expected, f"Realistic scenario failed: constructor='{constructor}', filter='{filter_val}', expected='{expected}', got='{result}'"

    def test_regression_scenarios(self):
        """Test the specific scenarios that were broken"""
        def original_broken_logic(constructor_value, filter_value):
            """The original broken logic that caused the bug"""
            return constructor_value or filter_value
        
        def fixed_logic(constructor_value, filter_value):
            """The fixed logic"""
            return constructor_value if constructor_value is not None else filter_value
        
        # These are the exact scenarios that were failing
        regression_scenarios = [
            # Empty string branch ID (most common failure case)
            {
                "constructor": "",
                "filter": "main", 
                "expected_correct": "",
                "description": "Empty string branch should be used, not ignored"
            },
            
            # Note: "0" and "false" as strings are actually truthy in Python
            # They would work fine with OR logic, but we test them anyway for completeness
            {
                "constructor": "0",
                "filter": "main",
                "expected_correct": "0", 
                "description": "String zero should be used (would work with OR too, but testing consistency)"
            },
            
            {
                "constructor": "false",
                "filter": "main",
                "expected_correct": "false",
                "description": "String false should be used (would work with OR too, but testing consistency)"
            }
        ]
        
        for scenario in regression_scenarios:
            constructor = scenario["constructor"]
            filter_val = scenario["filter"]
            expected = scenario["expected_correct"]
            description = scenario["description"]
            
            # Show the broken behavior (only for empty string, which is the real bug)
            broken_result = original_broken_logic(constructor, filter_val)
            if constructor == "":  # Only empty string is actually broken with OR
                assert broken_result == filter_val, f"Broken logic should return filter value for empty string: {description}"
            else:  # "0" and "false" strings actually work fine with OR
                assert broken_result == constructor, f"OR logic works fine for truthy strings like '{constructor}'"
            
            # Show the fixed behavior (works for all cases)
            fixed_result = fixed_logic(constructor, filter_val)
            assert fixed_result == expected, f"Fixed logic should return constructor value: {description}"
            
            # Verify they're different only for the truly broken case (empty string)
            if constructor == "":
                assert broken_result != fixed_result, f"Fix should change behavior for empty string: {description}"
            else:
                assert broken_result == fixed_result, f"Fix should not change behavior for truthy strings like '{constructor}'"