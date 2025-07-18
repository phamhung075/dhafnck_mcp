"""
TDD test to reproduce and fix the AttributeError when retrieving tasks via MCP.

This test reproduces the exact scenario that causes the AttributeError:
1. Create a task with subtasks
2. Try to retrieve the task via MCP
3. Verify that the AttributeError is fixed

The error occurs when the task completion service tries to access task.subtasks
and expects it to be a list of strings (IDs), but gets Subtask objects instead.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
from fastmcp.task_management.infrastructure.repositories.orm.subtask_repository import ORMSubtaskRepository
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.entities.subtask import Subtask
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.subtask_id import SubtaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority
from fastmcp.task_management.infrastructure.database.database_config import get_session
from unittest.mock import Mock


class TestTaskRetrievalAttributeErrorFix:
    """TDD test for fixing the AttributeError when retrieving tasks with subtasks."""
    
    def test_task_repository_get_task_returns_correct_subtask_ids(self, module_test_db):
        """
        Test that reproduces the AttributeError and verifies it's fixed.
        
        The issue: When retrieving a task with subtasks, the backend returns
        Subtask objects in the subtasks field instead of string IDs.
        This causes AttributeError when the task completion service tries to
        iterate over task.subtasks expecting strings.
        """
        # Get existing git branch from database
        from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch
        session = get_session()
        try:
            git_branch = session.query(ProjectGitBranch).filter_by(name='main').first()
            git_branch_id = git_branch.id if git_branch else str(uuid4())
        finally:
            session.close()
        
        # Create repositories
        task_repo = ORMTaskRepository(git_branch_id=git_branch_id)
        subtask_repo = ORMSubtaskRepository()
        
        # Create a task
        task = task_repo.create_task(
            title="Task with Subtasks for AttributeError Test",
            description="This task reproduces the AttributeError issue",
            priority="high"
        )
        
        # Create subtasks
        subtask1 = Subtask(
            id=SubtaskId(str(uuid4())),
            title="First Subtask",
            description="First subtask description",
            parent_task_id=task.id,
            status=TaskStatus.todo(),
            priority=Priority.medium()
        )
        
        subtask2 = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Second Subtask",
            description="Second subtask description",
            parent_task_id=task.id,
            status=TaskStatus.in_progress(),
            priority=Priority.high()
        )
        
        # Save subtasks to database
        subtask_repo.save(subtask1)
        subtask_repo.save(subtask2)
        
        # NOW THE CRITICAL TEST: Retrieve the task
        # This should NOT cause AttributeError when accessing task.subtasks
        retrieved_task = task_repo.get_task(str(task.id))
        
        # Verify the task was retrieved successfully
        assert retrieved_task is not None
        assert retrieved_task.id == task.id
        assert retrieved_task.title == task.title
        
        # CRITICAL: Verify subtasks are string IDs, not Subtask objects
        assert hasattr(retrieved_task, 'subtasks')
        assert isinstance(retrieved_task.subtasks, list)
        assert len(retrieved_task.subtasks) == 2
        
        # Each subtask should be a string ID, not a Subtask object
        for subtask_id in retrieved_task.subtasks:
            assert isinstance(subtask_id, str), f"Expected string ID, got {type(subtask_id)}: {subtask_id}"
            assert len(subtask_id) > 0, f"Subtask ID should not be empty: {subtask_id}"
            # Verify it's a valid UUID string
            assert len(subtask_id) == 36, f"Expected UUID length, got {len(subtask_id)}: {subtask_id}"
            assert subtask_id.count('-') == 4, f"Expected UUID format, got: {subtask_id}"
        
        # Verify the subtask IDs match our created subtasks
        assert str(subtask1.id) in retrieved_task.subtasks
        assert str(subtask2.id) in retrieved_task.subtasks
        
        print(f"✅ Task retrieved successfully with subtask IDs: {retrieved_task.subtasks}")
        
    def test_task_serialization_with_subtasks_works(self, module_test_db):
        """Test that task.to_dict() works correctly with subtasks as string IDs."""
        # Get existing git branch from database
        from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch
        session = get_session()
        try:
            git_branch = session.query(ProjectGitBranch).filter_by(name='main').first()
            git_branch_id = git_branch.id if git_branch else str(uuid4())
        finally:
            session.close()
        
        # Create repositories
        task_repo = ORMTaskRepository(git_branch_id=git_branch_id)
        subtask_repo = ORMSubtaskRepository()
        
        # Create a task
        task = task_repo.create_task(
            title="Task for Serialization Test",
            description="This task tests serialization with subtasks",
            priority="medium"
        )
        
        # Create a subtask
        subtask = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Test Subtask",
            description="Test subtask description",
            parent_task_id=task.id,
            status=TaskStatus.todo(),
            priority=Priority.low()
        )
        
        # Save subtask to database
        subtask_repo.save(subtask)
        
        # Retrieve the task
        retrieved_task = task_repo.get_task(str(task.id))
        
        # Test serialization - this should NOT cause AttributeError
        task_dict = retrieved_task.to_dict()
        
        # Verify serialization structure
        assert 'subtasks' in task_dict
        assert isinstance(task_dict['subtasks'], list)
        assert len(task_dict['subtasks']) == 1
        assert str(subtask.id) in task_dict['subtasks']
        assert isinstance(task_dict['subtasks'][0], str)
        
        print(f"✅ Task serialization works: {task_dict['subtasks']}")
        
    def test_task_completion_service_can_handle_retrieved_task(self, module_test_db):
        """
        Test that the task completion service can work with a retrieved task.
        
        This is the key test that reproduces the AttributeError scenario.
        """
        from fastmcp.task_management.domain.services.task_completion_service import TaskCompletionService
        
        # Get existing git branch from database
        from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch
        session = get_session()
        try:
            git_branch = session.query(ProjectGitBranch).filter_by(name='main').first()
            git_branch_id = git_branch.id if git_branch else str(uuid4())
        finally:
            session.close()
        
        # Create repositories
        task_repo = ORMTaskRepository(git_branch_id=git_branch_id)
        subtask_repo = ORMSubtaskRepository()
        
        # Create a task
        task = task_repo.create_task(
            title="Task for Completion Service Test",
            description="This task tests the completion service integration",
            priority="high"
        )
        
        # Create subtasks with mixed completion status
        subtask1 = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Completed Subtask",
            description="This subtask is done",
            parent_task_id=task.id,
            status=TaskStatus.done(),
            priority=Priority.medium()
        )
        
        subtask2 = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Incomplete Subtask",
            description="This subtask is not done",
            parent_task_id=task.id,
            status=TaskStatus.todo(),
            priority=Priority.high()
        )
        
        # Save subtasks to database
        subtask_repo.save(subtask1)
        subtask_repo.save(subtask2)
        
        # Retrieve the task (this is where the AttributeError occurred)
        retrieved_task = task_repo.get_task(str(task.id))
        
        # Create completion service with mock hierarchical context service
        mock_context_service = Mock()
        mock_context_service.get_context.return_value = {
            "success": True,
            "context": {"level": "task", "context_id": str(task.id), "data": {"status": "in_progress"}}
        }
        completion_service = TaskCompletionService(subtask_repo, mock_context_service)
        
        # THIS IS THE CRITICAL TEST: This should NOT raise AttributeError
        # The completion service should be able to work with the retrieved task
        try:
            can_complete, error_message = completion_service.can_complete_task(retrieved_task)
            
            # Verify the service works correctly
            assert can_complete is False  # Should be false due to incomplete subtask
            assert error_message is not None
            assert "1 of 2 subtasks are incomplete" in error_message
            
            print(f"✅ Task completion service works correctly: {error_message}")
            
        except AttributeError as e:
            # This is the error we're trying to fix
            pytest.fail(f"AttributeError occurred when using completion service: {e}")
            
    def test_list_tasks_with_subtasks_works(self, module_test_db):
        """Test that listing tasks with subtasks works without AttributeError."""
        # Get existing git branch from database
        from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch
        session = get_session()
        try:
            git_branch = session.query(ProjectGitBranch).filter_by(name='main').first()
            git_branch_id = git_branch.id if git_branch else str(uuid4())
        finally:
            session.close()
        
        # Create repositories
        task_repo = ORMTaskRepository(git_branch_id=git_branch_id)
        subtask_repo = ORMSubtaskRepository()
        
        # Create multiple tasks with subtasks
        task1 = task_repo.create_task(
            title="First Task with Subtasks",
            description="First task for listing test",
            priority="high"
        )
        
        task2 = task_repo.create_task(
            title="Second Task with Subtasks",
            description="Second task for listing test",
            priority="medium"
        )
        
        # Create subtasks for both tasks
        subtask1 = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Task 1 Subtask",
            description="Subtask for first task",
            parent_task_id=task1.id,
            status=TaskStatus.todo(),
            priority=Priority.medium()
        )
        
        subtask2 = Subtask(
            id=SubtaskId(str(uuid4())),
            title="Task 2 Subtask",
            description="Subtask for second task",
            parent_task_id=task2.id,
            status=TaskStatus.in_progress(),
            priority=Priority.high()
        )
        
        # Save subtasks
        subtask_repo.save(subtask1)
        subtask_repo.save(subtask2)
        
        # List all tasks - this should NOT cause AttributeError
        all_tasks = task_repo.list_tasks()
        
        # Verify tasks were retrieved correctly
        assert len(all_tasks) >= 2  # At least our two tasks
        
        # Find our created tasks
        created_tasks = [t for t in all_tasks if t.id in [task1.id, task2.id]]
        assert len(created_tasks) == 2
        
        # Verify each task has correct subtasks
        for task in created_tasks:
            assert hasattr(task, 'subtasks')
            assert isinstance(task.subtasks, list)
            assert len(task.subtasks) == 1  # Each task has one subtask
            
            # Verify subtask is a string ID
            subtask_id = task.subtasks[0]
            assert isinstance(subtask_id, str)
            assert len(subtask_id) == 36  # UUID length
            
        print(f"✅ Task listing works correctly. Found {len(all_tasks)} tasks.")
        
    def test_task_without_subtasks_still_works(self, module_test_db):
        """Test that tasks without subtasks still work correctly."""
        # Get existing git branch from database
        from fastmcp.task_management.infrastructure.database.models import ProjectGitBranch
        session = get_session()
        try:
            git_branch = session.query(ProjectGitBranch).filter_by(name='main').first()
            git_branch_id = git_branch.id if git_branch else str(uuid4())
        finally:
            session.close()
        
        # Create repositories
        task_repo = ORMTaskRepository(git_branch_id=git_branch_id)
        
        # Create a task without subtasks
        task = task_repo.create_task(
            title="Task without Subtasks",
            description="This task has no subtasks",
            priority="low"
        )
        
        # Retrieve the task
        retrieved_task = task_repo.get_task(str(task.id))
        
        # Verify the task was retrieved successfully
        assert retrieved_task is not None
        assert retrieved_task.id == task.id
        assert retrieved_task.title == task.title
        
        # Verify subtasks is an empty list, not None
        assert hasattr(retrieved_task, 'subtasks')
        assert isinstance(retrieved_task.subtasks, list)
        assert len(retrieved_task.subtasks) == 0
        
        # Test serialization
        task_dict = retrieved_task.to_dict()
        assert 'subtasks' in task_dict
        assert isinstance(task_dict['subtasks'], list)
        assert len(task_dict['subtasks']) == 0
        
        print(f"✅ Task without subtasks works correctly: {task_dict['subtasks']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])