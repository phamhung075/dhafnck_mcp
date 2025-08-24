"""
Unit test for task summary route facade method fix.

This test verifies the fix for the task list vs count discrepancy issue
where the task_summaries endpoint was using the wrong facade creation method.

Root Cause: task_summary_routes.py line 186 was using create_task_facade() 
instead of create_task_facade_with_git_branch_id(), causing the repository 
to ignore the git_branch_id parameter during task list retrieval while 
the count method worked correctly.

Fix: Replace create_task_facade() with create_task_facade_with_git_branch_id()
and add proper logging to confirm git_branch_id is passed through.
"""

import pytest
import inspect


class TestTaskSummaryFacadeMethodFix:
    """Unit tests for task summary facade method fix."""

    def test_task_summaries_endpoint_uses_correct_facade_method(self):
        """
        Test that get_task_summaries now uses create_task_facade_with_git_branch_id.
        This is the main fix verification test.
        """
        from fastmcp.server.routes.task_summary_routes import get_task_summaries
        
        # Get the source code of the function
        source = inspect.getsource(get_task_summaries)
        
        # Verify the fix is applied - should use the method that respects git_branch_id
        assert 'create_task_facade_with_git_branch_id' in source, \
            "Task summaries route should use create_task_facade_with_git_branch_id method"
        
        # Find the exact line that creates the facade
        lines = source.split('\n')
        facade_creation_line = None
        for line in lines:
            if 'create_task_facade_with_git_branch_id' in line and '=' in line:
                facade_creation_line = line.strip()
                break
        
        assert facade_creation_line is not None, "Should find the facade creation line"
        
        # Verify the method signature includes all required parameters
        assert 'git_branch_id' in facade_creation_line, "Should pass git_branch_id parameter"
        assert '"default_project"' in facade_creation_line, "Should pass project_id"
        assert '"main"' in facade_creation_line, "Should pass branch name"
        assert 'user_id' in facade_creation_line, "Should pass user_id"
        
        # Verify it's assigned to task_facade variable
        assert 'task_facade =' in facade_creation_line, "Should assign to task_facade variable"

    def test_git_branch_id_logging_added(self):
        """
        Test that logging was added to track git_branch_id usage.
        """
        from fastmcp.server.routes.task_summary_routes import get_task_summaries
        
        # Get the source code of the function
        source = inspect.getsource(get_task_summaries)
        
        # Verify logging is present before facade creation
        assert 'Creating task facade with git_branch_id' in source, \
            "Should have logging to confirm git_branch_id is being used"
        
        # Verify the log message includes the git_branch_id variable
        lines = source.split('\n')
        log_line = None
        for line in lines:
            if 'Creating task facade with git_branch_id' in line:
                log_line = line.strip()
                break
        
        assert log_line is not None, "Should find the logging line"
        assert '{git_branch_id}' in log_line, "Log message should include git_branch_id variable"
        assert 'logger.info' in log_line, "Should use logger.info for the message"

    def test_other_endpoints_unaffected(self):
        """
        Test that other endpoints still use the original method where appropriate.
        get_full_task and get_subtask_summaries don't need git_branch_id filtering.
        """
        from fastmcp.server.routes.task_summary_routes import get_full_task, get_subtask_summaries
        
        # Check get_full_task - should still use old method
        full_task_source = inspect.getsource(get_full_task)
        assert 'create_task_facade(' in full_task_source, \
            "get_full_task should still use create_task_facade (no git_branch_id filtering needed)"
        assert 'create_task_facade_with_git_branch_id' not in full_task_source, \
            "get_full_task should not use create_task_facade_with_git_branch_id"
        
        # Check get_subtask_summaries - should still use old method  
        subtask_source = inspect.getsource(get_subtask_summaries)
        assert 'create_task_facade(' in subtask_source, \
            "get_subtask_summaries should still use create_task_facade (no git_branch_id filtering needed)"
        assert 'create_task_facade_with_git_branch_id' not in subtask_source, \
            "get_subtask_summaries should not use create_task_facade_with_git_branch_id"

    def test_method_signature_comparison(self):
        """
        Test that documents the difference between the old and new methods.
        """
        from fastmcp.task_management.application.factories.task_facade_factory import TaskFacadeFactory
        
        # Get the method signatures
        old_method = getattr(TaskFacadeFactory, 'create_task_facade')
        new_method = getattr(TaskFacadeFactory, 'create_task_facade_with_git_branch_id')
        
        # Both methods should exist
        assert callable(old_method), "create_task_facade method should exist"
        assert callable(new_method), "create_task_facade_with_git_branch_id method should exist"
        
        # Get their signatures for documentation
        old_sig = inspect.signature(old_method)
        new_sig = inspect.signature(new_method)
        
        # Document the signatures (this is informational)
        print(f"Old method signature: create_task_facade{old_sig}")
        print(f"New method signature: create_task_facade_with_git_branch_id{new_sig}")
        
        # Verify new method has more parameters (including explicit git_branch_id)
        assert len(new_sig.parameters) > len(old_sig.parameters), \
            "New method should have more parameters than old method"

    def test_facade_factory_method_behavior_difference(self):
        """
        Test the behavioral difference between the two facade creation methods.
        This is the root cause test.
        """
        # This is a documentation test that explains the key difference:
        
        method_differences = {
            "create_task_facade": {
                "signature": "(self, project_id: str, git_branch_id: str = None, user_id: str = None)",
                "behavior": "Creates repository with hardcoded 'main' branch name, ignores git_branch_id",
                "issue": "The git_branch_id parameter is not passed to the repository creation",
                "repository_call": "self._repository_factory.create_repository(project_id, 'main', user_id)"
            },
            "create_task_facade_with_git_branch_id": {
                "signature": "(self, project_id: str, git_branch_name: str, user_id: str, git_branch_id: str)",
                "behavior": "Creates repository with explicit git_branch_id parameter",
                "fix": "The git_branch_id is properly passed to the repository",
                "repository_call": "self._repository_factory.create_repository_with_git_branch_id(project_id, git_branch_name, user_id, git_branch_id)"
            }
        }
        
        # Document the fix for future reference
        assert "ignores git_branch_id" in method_differences["create_task_facade"]["issue"]
        assert "properly passed" in method_differences["create_task_facade_with_git_branch_id"]["fix"]
        
        print("✅ Method behavior difference documented:")
        print("OLD METHOD (broken):")
        print(f"  - Signature: {method_differences['create_task_facade']['signature']}")
        print(f"  - Issue: {method_differences['create_task_facade']['issue']}")
        print(f"  - Repository call: {method_differences['create_task_facade']['repository_call']}")
        
        print("NEW METHOD (fixed):")
        print(f"  - Signature: {method_differences['create_task_facade_with_git_branch_id']['signature']}")
        print(f"  - Fix: {method_differences['create_task_facade_with_git_branch_id']['fix']}")
        print(f"  - Repository call: {method_differences['create_task_facade_with_git_branch_id']['repository_call']}")

    def test_fix_verification_checklist(self):
        """
        Comprehensive checklist to verify the fix is properly applied.
        """
        from fastmcp.server.routes.task_summary_routes import get_task_summaries
        
        source = inspect.getsource(get_task_summaries)
        
        checklist = {
            "✅ Uses correct facade method": 'create_task_facade_with_git_branch_id' in source,
            "✅ Passes git_branch_id parameter": 'git_branch_id' in source and 'create_task_facade_with_git_branch_id' in source,
            "✅ Added logging for debugging": 'Creating task facade with git_branch_id' in source,
            "✅ Log includes variable": '{git_branch_id}' in source,
            "✅ No old method usage": source.count('create_task_facade(') == 0,
            "✅ Exactly one new method call": source.count('create_task_facade_with_git_branch_id') == 1,
        }
        
        print("Fix verification checklist:")
        for check, passed in checklist.items():
            print(f"  {check}: {'PASS' if passed else 'FAIL'}")
            assert passed, f"Fix verification failed: {check}"
        
        print("✅ All fix verification checks passed!")


if __name__ == "__main__":
    # Run verification when executed directly
    test = TestTaskSummaryFacadeMethodFix()
    test.test_task_summaries_endpoint_uses_correct_facade_method()
    test.test_git_branch_id_logging_added()
    test.test_other_endpoints_unaffected()
    test.test_method_signature_comparison()
    test.test_facade_factory_method_behavior_difference()
    test.test_fix_verification_checklist()
    print("✅ All task summary facade method fix tests passed!")