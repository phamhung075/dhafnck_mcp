"""
Integration test for task listing git branch filtering regression fix

This test verifies the fix for the issue where falsy git_branch_id values
(like empty strings, "0", "false") were incorrectly ignored due to the
use of logical OR operator instead of proper None checking.

Root Cause: Line 795 in task_repository.py used:
  git_branch_filter = self.git_branch_id or filters.get('git_branch_id')

Fix: Changed to proper None checking:
  git_branch_filter = self.git_branch_id if self.git_branch_id is not None else filters.get('git_branch_id')
"""

import pytest
import uuid
from datetime import datetime

from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
from fastmcp.task_management.infrastructure.database.models import Task
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority


@pytest.mark.integration
class TestTaskListGitBranchFilteringRegression:
    """Integration tests for git branch filtering regression fix"""

    @pytest.fixture
    def sample_tasks(self, shared_test_db):
        """Create sample tasks across different branches"""
        tasks = []
        branch_ids = ["branch-1", "branch-2", "", "0", "false", "null"]
        
        for i, branch_id in enumerate(branch_ids):
            task = Task(
                id=str(uuid.uuid4()),
                title=f"Task {i+1}",
                description=f"Task in branch {branch_id}",
                git_branch_id=branch_id,
                status=TaskStatus.TODO.value,
                priority=Priority.MEDIUM.value,
                user_id="test-user",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            shared_test_db.add(task)
            tasks.append(task)
        
        shared_test_db.commit()
        return tasks

    def test_constructor_git_branch_id_with_normal_string(self, shared_test_db, sample_tasks):
        """Test filtering with normal string git_branch_id in constructor"""
        branch_id = "branch-1"
        
        repository = ORMTaskRepository(
            session=db_session,
            git_branch_id=branch_id,
            user_id="test-user"
        )
        
        tasks = repository.find_by_criteria({})
        
        # Should only return tasks from branch-1
        assert len(tasks) == 1
        assert tasks[0].git_branch_id == branch_id

    def test_constructor_git_branch_id_with_empty_string(self, db_session, sample_tasks):
        """Test filtering with empty string git_branch_id in constructor (falsy value)"""
        branch_id = ""
        
        repository = ORMTaskRepository(
            session=db_session,
            git_branch_id=branch_id,
            user_id="test-user"
        )
        
        tasks = repository.find_by_criteria({})
        
        # Should only return tasks with empty string branch_id
        # This was the problematic case - empty string is falsy but should still be used for filtering
        assert len(tasks) == 1
        assert tasks[0].git_branch_id == ""

    def test_constructor_git_branch_id_with_string_zero(self, db_session, sample_tasks):
        """Test filtering with string '0' git_branch_id in constructor (falsy-like value)"""
        branch_id = "0"
        
        repository = ORMTaskRepository(
            session=db_session,
            git_branch_id=branch_id,
            user_id="test-user"
        )
        
        tasks = repository.find_by_criteria({})
        
        # Should only return tasks with "0" branch_id
        assert len(tasks) == 1
        assert tasks[0].git_branch_id == "0"

    def test_constructor_git_branch_id_with_string_false(self, db_session, sample_tasks):
        """Test filtering with string 'false' git_branch_id in constructor"""
        branch_id = "false"
        
        repository = ORMTaskRepository(
            session=db_session,
            git_branch_id=branch_id,
            user_id="test-user"
        )
        
        tasks = repository.find_by_criteria({})
        
        # Should only return tasks with "false" branch_id
        assert len(tasks) == 1
        assert tasks[0].git_branch_id == "false"

    def test_constructor_precedence_over_filters(self, db_session, sample_tasks):
        """Test that constructor git_branch_id takes precedence over filters"""
        constructor_branch_id = "branch-1"
        filter_branch_id = "branch-2"
        
        repository = ORMTaskRepository(
            session=db_session,
            git_branch_id=constructor_branch_id,
            user_id="test-user"
        )
        
        # Pass different branch_id in filters - constructor should win
        tasks = repository.find_by_criteria({'git_branch_id': filter_branch_id})
        
        # Should return tasks from constructor branch, not filter branch
        assert len(tasks) == 1
        assert tasks[0].git_branch_id == constructor_branch_id

    def test_fallback_to_filters_when_constructor_none(self, db_session, sample_tasks):
        """Test fallback to filters git_branch_id when constructor is None"""
        filter_branch_id = "branch-2"
        
        repository = ORMTaskRepository(
            session=db_session,
            git_branch_id=None,  # Constructor is None
            user_id="test-user"
        )
        
        tasks = repository.find_by_criteria({'git_branch_id': filter_branch_id})
        
        # Should return tasks from filter branch
        assert len(tasks) == 1
        assert tasks[0].git_branch_id == filter_branch_id

    def test_no_filtering_when_both_none(self, db_session, sample_tasks):
        """Test no git_branch_id filtering when both constructor and filters are None"""
        repository = ORMTaskRepository(
            session=db_session,
            git_branch_id=None,
            user_id="test-user"
        )
        
        tasks = repository.find_by_criteria({})
        
        # Should return all tasks for this user (no branch filtering)
        assert len(tasks) == 6  # All sample tasks

    def test_edge_case_falsy_values_in_constructor(self, db_session, sample_tasks):
        """Test that various falsy values in constructor are handled correctly"""
        # Test empty string specifically (was the main issue)
        repository_empty = ORMTaskRepository(
            session=db_session,
            git_branch_id="",
            user_id="test-user"
        )
        
        tasks_empty = repository_empty.find_by_criteria({})
        assert len(tasks_empty) == 1
        assert tasks_empty[0].git_branch_id == ""
        
        # Test string zero
        repository_zero = ORMTaskRepository(
            session=db_session,
            git_branch_id="0",
            user_id="test-user"
        )
        
        tasks_zero = repository_zero.find_by_criteria({})
        assert len(tasks_zero) == 1
        assert tasks_zero[0].git_branch_id == "0"

    def test_mixed_filtering_scenarios(self, db_session, sample_tasks):
        """Test mixed scenarios with various filter combinations"""
        # Scenario 1: Constructor empty string + filter with normal string
        repository = ORMTaskRepository(
            session=db_session,
            git_branch_id="",  # Empty string in constructor
            user_id="test-user"
        )
        
        # Constructor should take precedence
        tasks = repository.find_by_criteria({'git_branch_id': 'branch-1'})
        assert len(tasks) == 1
        assert tasks[0].git_branch_id == ""
        
        # Scenario 2: No constructor, filter with falsy string
        repository_no_constructor = ORMTaskRepository(
            session=db_session,
            git_branch_id=None,
            user_id="test-user"
        )
        
        tasks_filter_empty = repository_no_constructor.find_by_criteria({'git_branch_id': ''})
        assert len(tasks_filter_empty) == 1
        assert tasks_filter_empty[0].git_branch_id == ""

    def test_regression_verification_before_and_after_fix(self, db_session, sample_tasks):
        """Verify that the fix resolves the specific regression issue"""
        # This test simulates the exact scenario that was broken:
        # 1. Repository created with falsy git_branch_id (empty string)
        # 2. find_by_criteria called without git_branch_id in filters
        # 3. Before fix: would return ALL tasks (no filtering)
        # 4. After fix: should return only tasks with empty string branch_id
        
        repository = ORMTaskRepository(
            session=db_session,
            git_branch_id="",  # This is the problematic falsy value
            user_id="test-user"
        )
        
        # Call find_by_criteria without any filters
        tasks = repository.find_by_criteria({})
        
        # BEFORE FIX: This would have returned all 6 tasks (no filtering)
        # AFTER FIX: This should return only 1 task (with empty string branch_id)
        assert len(tasks) == 1, f"Expected 1 task with empty branch_id, got {len(tasks)} tasks"
        assert tasks[0].git_branch_id == "", f"Expected empty string branch_id, got '{tasks[0].git_branch_id}'"
        
        # Verify this is different from the broken behavior
        all_tasks = repository.find_by_criteria({})
        repository_all = ORMTaskRepository(
            session=db_session,
            git_branch_id=None,  # No filtering
            user_id="test-user"
        )
        all_tasks_unfiltered = repository_all.find_by_criteria({})
        
        # Should be different - filtered vs unfiltered
        assert len(all_tasks) != len(all_tasks_unfiltered), "Branch filtering should make a difference"
        assert len(all_tasks_unfiltered) == 6, "Unfiltered should return all tasks"
        assert len(all_tasks) == 1, "Filtered should return only matching tasks"

    @pytest.mark.parametrize("falsy_value", ["", "0", "false", "null"])
    def test_all_falsy_string_values_regression(self, db_session, sample_tasks, falsy_value):
        """Parametrized test for all falsy string values that were problematic"""
        repository = ORMTaskRepository(
            session=db_session,
            git_branch_id=falsy_value,
            user_id="test-user"
        )
        
        tasks = repository.find_by_criteria({})
        
        # Should return exactly 1 task with the matching falsy branch_id
        assert len(tasks) == 1
        assert tasks[0].git_branch_id == falsy_value
        
        # Verify the specific task is correct
        expected_task = next((t for t in sample_tasks if t.git_branch_id == falsy_value), None)
        assert expected_task is not None, f"Sample task with branch_id '{falsy_value}' should exist"
        assert tasks[0].id == expected_task.id